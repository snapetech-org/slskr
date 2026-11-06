#!/usr/bin/env python3
"""Exercise real metadata generation for current and legacy release tags."""
import hashlib
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parent.parent
TARGETS = (
    'x86_64-unknown-linux-gnu', 'aarch64-unknown-linux-gnu',
    'x86_64-unknown-linux-musl', 'aarch64-unknown-linux-musl',
    'x86_64-apple-darwin', 'aarch64-apple-darwin', 'x86_64-pc-windows-msvc',
)


class ReleaseMetadataTests(unittest.TestCase):
    def test_tag_identity_and_portable_package_checksums(self):
        for tag in ('v9.8.7', 'release-v9.8.7'):
            with self.subTest(tag=tag), tempfile.TemporaryDirectory(prefix='slskr-release-metadata-') as tmp:
                root = Path(tmp)
                shutil.copytree(ROOT / 'packaging', root / 'packaging',
                                ignore=shutil.ignore_patterns('build', 'target', 'node_modules'))
                for name in ('flake.nix', 'slskr.xml'):
                    shutil.copy2(ROOT / name, root / name)
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
