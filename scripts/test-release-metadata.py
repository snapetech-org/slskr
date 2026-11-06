#!/usr/bin/env python3
"""Exercise real metadata generation for current and legacy release tags."""
import hashlib
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import tarfile
import unittest

ROOT = Path(__file__).resolve().parent.parent
TARGETS = (
    'x86_64-unknown-linux-gnu', 'aarch64-unknown-linux-gnu',
    'x86_64-unknown-linux-musl', 'aarch64-unknown-linux-musl',
    'x86_64-apple-darwin', 'aarch64-apple-darwin', 'x86_64-pc-windows-msvc',
)


class ReleaseMetadataTests(unittest.TestCase):
    def test_publisher_accepts_tagged_calls_and_main_only_manual_retries(self):
        workflow = (ROOT / '.github/workflows/release-publish.yml').read_text()
        caller = (ROOT / '.github/workflows/release.yml').read_text()
        self.assertIn('uses: ./.github/workflows/release-publish.yml\n    with:\n      release_workflow_call: true', caller)
        self.assertIn("if: github.event_name == 'workflow_dispatch' && !inputs.release_workflow_call", workflow)
        for job in ('metadata', 'aur', 'copr', 'ppa', 'docker', 'homebrew', 'winget'):
            body = re.search(r'^  ' + job + r':\n(.*?)(?=^  [a-z]|\Z)', workflow, re.M | re.S).group(1)
            gate = re.search(r'^    if: >-\n((?:      .*\n)+)', body, re.M).group(1)
            for ref, called, action, pool, expected in (
                ('refs/tags/v9.8.7', True, 'release', 'hosted', True),
                ('refs/heads/main', False, 'release', 'hosted', True),
                ('refs/tags/v9.8.7', False, 'release', 'hosted', False),
                ('refs/heads/feature', False, 'release', 'hosted', False),
                ('refs/tags/v9.8.6', True, 'release', 'hosted', False),
                ('refs/tags/v9.8.7', True, 'test', 'hosted', False),
                ('refs/tags/v9.8.7', True, 'release', 'private', False),
            ):
                expression = gate
                for field, value in {
                    'github.event_name': 'workflow_dispatch', 'github.ref': ref,
                    'inputs.release_workflow_call': called, 'inputs.tag': 'v9.8.7',
                    'inputs.action_tag': action, 'inputs.runner_pool_tag': pool,
                    'inputs.publish_only': 'all',
                }.items():
                    expression = expression.replace(field, repr(value))
                expression = ' '.join(expression.replace('&&', ' and ').replace('||', ' or ').split())
                with self.subTest(job=job, ref=ref, called=called, action=action, pool=pool):
                    self.assertEqual(eval(expression, {'__builtins__': {},
                        'format': lambda template, value: template.format(value)}), expected)

    def test_workflow_archive_names_match_package_consumers(self):
        workflow = (ROOT / '.github/workflows/release.yml').read_text()
        value = re.search(r'^\s+SLSKR_RELEASE_VERSION:\s*(.+)$', workflow, re.M).group(1)
        archive_version = value.replace('${{ needs.version.outputs.version }}', '9.8.7')
        expected_version = subprocess.check_output(['bash', '-c',
            'source "$1"; slskr_release_version_from_tag v9.8.7', 'test',
            str(ROOT / 'packaging/scripts/release-assets.sh')], text=True).strip()
        target = 'x86_64-unknown-linux-musl'
        expected_root = f'slskr-{expected_version}-{target}'
        with tempfile.TemporaryDirectory(prefix='slskr-archive-contract-') as tmp:
            root = Path(tmp)
            (root / 'scripts').mkdir()
            shutil.copy2(ROOT / 'scripts/build-release-archive.sh', root / 'scripts')
            for name in ('README.md', 'LICENSE', 'NOTICE', 'COMPLIANCE.md',
                         'docs/slskr.config.example.toml', 'web/build/index.html',
                         'web/build/assets/app.js', f'target/{target}/release/slskr'):
                path = root / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text('archive contract fixture\n')
            (root / 'bin').mkdir()
            cargo = root / 'bin/cargo'
            cargo.write_text('#!/bin/sh\ntest "$SLSKR_APP_VERSION" = 9.8.7\n')
            cargo.chmod(0o755)
            subprocess.run(['bash', 'scripts/build-release-archive.sh', '--target', target,
                            '--skip-web-build'], cwd=root, check=True, capture_output=True,
                           env={**os.environ, 'PATH': f'{root / "bin"}:{os.environ["PATH"]}',
                                'SLSKR_RELEASE_VERSION': archive_version,
                                'SOURCE_DATE_EPOCH': '1577836800'})
            archive = root / f'target/dist/{expected_root}.tar.gz'
            self.assertTrue(archive.is_file(), 'workflow must build the filenames consumed by publishers')
            with tarfile.open(archive) as packaged:
                self.assertIn(f'{expected_root}/slskr', packaged.getnames())
            self.assertEqual(archive.with_suffix('.gz.sha256').read_text().split()[0],
                             hashlib.sha256(archive.read_bytes()).hexdigest())

    def test_tag_identity_and_portable_package_checksums(self):
        for tag in ('v9.8.7', 'release-v9.8.7'):
            with self.subTest(tag=tag), tempfile.TemporaryDirectory(prefix='slskr-release-metadata-') as tmp:
                root = Path(tmp)
                shutil.copytree(ROOT / 'packaging', root / 'packaging',
                                ignore=shutil.ignore_patterns('build', 'target', 'node_modules'))
                for name in ('flake.nix', 'slskr.xml'):
                    shutil.copy2(ROOT / name, root / name)
                unraid_template = (root / 'slskr.xml').read_bytes()
                assets = root / 'assets'
                assets.mkdir()
                hashes = {}
                for target in TARGETS:
                    content = ('fixture:' + target).encode()
                    extension = 'zip' if target.endswith('msvc') else 'tar.gz'
                    (assets / f'slskr-v9.8.7-{target}.{extension}').write_bytes(content)
                    hashes[target] = hashlib.sha256(content).hexdigest()
                subprocess.run(['bash', 'packaging/scripts/update-release-metadata.sh', tag, str(assets)],
                               cwd=root, check=True, capture_output=True)
                self.assertEqual((root / 'slskr.xml').read_bytes(), unraid_template)
                nix = (root / 'flake.nix').read_text()
                for system, target in (
                    ('x86_64-linux', 'x86_64-unknown-linux-musl'),
                    ('aarch64-linux', 'aarch64-unknown-linux-musl'),
                ):
                    source = re.search(r'"' + system + r'" = \{(.*?)\n\s*\};', nix, re.S).group(1)
                    self.assertIn(f'/releases/download/{tag}/slskr-v9.8.7-{target}.tar.gz', source)
                    self.assertIn(hashes[target], source)
                for recipe in ('PKGBUILD', 'PKGBUILD-bin'):
                    recipe_path = root / 'packaging/aur' / recipe
                    result = subprocess.check_output(['bash', '-c',
                        'source "$1"; printf "%s" "$_release_tag"', 'test', str(recipe_path)], text=True)
                    self.assertEqual(result, tag)
                formula = (root / 'packaging/homebrew/Formula/slskr.rb').read_text()
                for target in ('x86_64-unknown-linux-musl', 'aarch64-unknown-linux-musl'):
                    self.assertIn(f'/releases/download/{tag}/slskr-v9.8.7-{target}.tar.gz', formula)
                    self.assertIn(hashes[target], formula)
                    self.assertIn(f'slskr-v9.8.7-{target}.tar.gz',
                                  (root / 'packaging/rpm/slskr.spec').read_text())
                snap = (root / 'packaging/snap/snapcraft.yaml').read_text()
                self.assertIn('base: core24', snap)
                self.assertIn('platforms:', snap)
                self.assertIn("runtime-version: '25.08'",
                              (root / 'packaging/flatpak/io.github.slskd.slskr.yml').read_text())
                source_root = root / 'source' / 'Repository-Case-Independent-9.8.7'
                source_root.mkdir(parents=True)
                (source_root / 'Cargo.toml').write_text('[workspace]\n')
                result = subprocess.check_output(['bash', '-c', 'source "$1"; _source_root',
                    'test', str(root / 'packaging/aur/PKGBUILD')], text=True,
                    env={**os.environ, 'srcdir': str(source_root.parent)})
                self.assertEqual(result.strip(), str(source_root))


if __name__ == '__main__':
    unittest.main()
