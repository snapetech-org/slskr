#!/usr/bin/env python3
"""Exercise real metadata generation for current and legacy release tags."""
import ast
import importlib.util
import hashlib
import io
import json
import os
from pathlib import Path
import re
import runpy
import shutil
import subprocess
import tempfile
import tarfile
import textwrap
import unittest
from unittest.mock import patch

from discord_announcement import build_payload, execute_webhook

ROOT = Path(__file__).resolve().parent.parent
TARGETS = (
    'x86_64-unknown-linux-gnu', 'aarch64-unknown-linux-gnu',
    'x86_64-unknown-linux-musl', 'aarch64-unknown-linux-musl',
    'x86_64-apple-darwin', 'aarch64-apple-darwin', 'x86_64-pc-windows-msvc',
)


def workflow_gate_value(node):
    """Interpret only the literal boolean operations used by publisher guards."""
    if isinstance(node, ast.Expression):
        return workflow_gate_value(node.body)
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.Not):
        return not workflow_gate_value(node.operand)
    if isinstance(node, ast.BoolOp):
        values = (workflow_gate_value(value) for value in node.values)
        if isinstance(node.op, ast.And):
            return all(values)
        if isinstance(node.op, ast.Or):
            return any(values)
    if isinstance(node, ast.Compare) and len(node.ops) == 1:
        left, right = workflow_gate_value(node.left), workflow_gate_value(node.comparators[0])
        if isinstance(node.ops[0], ast.Eq):
            return left == right
        if isinstance(node.ops[0], ast.NotEq):
            return left != right
    if (isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
            and node.func.id == 'format' and len(node.args) == 2 and not node.keywords):
        template, value = map(workflow_gate_value, node.args)
        return template.format(value)
    raise AssertionError(f'Unsupported workflow guard syntax: {ast.dump(node)}')


class ReleaseMetadataTests(unittest.TestCase):
    def test_recovery_metadata_records_release_tag_instead_of_current_head(self):
        workflow = (ROOT / '.github/workflows/release-publish.yml').read_text()
        step = workflow.split('      - name: Resolve version\n', 1)[1]
        script = textwrap.dedent(re.search(r'        run: \|\n((?:          .*\n|\n)+)', step).group(1))
        with tempfile.TemporaryDirectory(prefix='slskr-provenance-test-') as directory:
            fixture = Path(directory)
            def git(*args):
                return subprocess.check_output(['git', *args], cwd=fixture, text=True, stderr=subprocess.DEVNULL).strip()
            git('init', '-b', 'main')
            git('config', 'user.name', 'Release fixture')
            git('config', 'user.email', 'fixture@example.invalid')
            git('config', 'commit.gpgsign', 'false')
            git('config', 'core.hooksPath', '/dev/null')
            (fixture / 'packaging/scripts').mkdir(parents=True)
            shutil.copy2(ROOT / 'packaging/scripts/release-assets.sh', fixture / 'packaging/scripts/release-assets.sh')
            git('add', '.')
            git('commit', '-m', 'Release source')
            release_sha = git('rev-parse', 'HEAD')
            git('tag', 'v9.8.7')
            (fixture / 'retry-fix').write_text('Newer metadata recovery logic\n')
            git('add', '.')
            git('commit', '-m', 'Newer main source')
            self.assertNotEqual(git('rev-parse', 'HEAD'), release_sha)
            git('clone', '--bare', str(fixture), str(fixture / 'origin.git'))
            git('remote', 'add', 'origin', str(fixture / 'origin.git'))
            output = fixture / 'output'
            result = subprocess.run(['bash', '-c', script], cwd=fixture,
                                    env={**os.environ, 'RELEASE_TAG': 'v9.8.7', 'GITHUB_OUTPUT': str(output)},
                                    capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            values = dict(line.split('=', 1) for line in output.read_text().splitlines())
            self.assertEqual(values['release_sha'], release_sha)
            self.assertEqual(values['pkgver'], '9.8.7')

    def test_publish_steps_fail_before_work_when_credentials_are_missing(self):
        workflow = (ROOT / '.github/workflows/release-publish.yml').read_text()
        for name in ('Setup AUR SSH', 'Push slskr-bin', 'Push slskr source package',
                     'Build and upload SRPM', 'Import signing key', 'Build source package',
                     'Upload to PPA', 'Push tap'):
            with self.subTest(step=name):
                step = workflow.split(f'      - name: {name}\n', 1)[1]
                block = re.search(r'        run: \|\n((?:          .*\n|\n)+)', step).group(1)
                script = re.sub(r'\$\{\{.*?\}\}', 'v9.8.7', textwrap.dedent(block))
                # No external commands are reachable with this PATH: a missed
                # credential guard fails differently instead of publishing.
                result = subprocess.run(['/bin/bash', '-c', script],
                                        env={'PATH': '/nonexistent'}, capture_output=True, text=True)
                self.assertEqual(result.returncode, 1, result.stderr)
                self.assertIn('::error::', result.stdout)

    def test_homebrew_commit_failures_do_not_pass_as_no_changes(self):
        workflow = (ROOT / '.github/workflows/release-publish.yml').read_text()
        step = workflow.split('      - name: Push tap\n', 1)[1].split('\n  winget:', 1)[0]
        script = textwrap.dedent(step.split('        run: |\n', 1)[1])
        script = re.sub(r'\$\{\{.*?\}\}', 'v9.8.7', script)
        for diff_exit, commit_exit, push_exit, expected, committed, pushed in (
            (0, 9, 0, 0, False, True),
            (1, 0, 0, 0, True, True),
            (1, 7, 0, 7, True, False),
            (2, 0, 0, 2, False, False),
            (1, 0, 8, 8, True, True),
        ):
            with self.subTest(diff=diff_exit, commit=commit_exit, push=push_exit):
                with tempfile.TemporaryDirectory(prefix='slskr-tap-test-') as directory:
                    root = Path(directory)
                    (root / 'packaging/homebrew/Formula').mkdir(parents=True)
                    (root / 'packaging/homebrew/Formula/slskr.rb').write_text('fixture formula\n')
                    (root / 'bin').mkdir()
                    git = root / 'bin/git'
                    git.write_text('''#!/bin/sh
case "$1" in
  clone) mkdir -p tap/Formula ;;
  diff) exit "$DIFF_EXIT" ;;
  commit) touch ../committed; exit "$COMMIT_EXIT" ;;
  push) touch ../pushed; exit "$PUSH_EXIT" ;;
esac
''')
                    git.chmod(0o755)
                    env = {**os.environ, 'PATH': f"{root / 'bin'}:{os.environ['PATH']}",
                           'GH_TOKEN': 'fixture', 'DIFF_EXIT': str(diff_exit),
                           'COMMIT_EXIT': str(commit_exit), 'PUSH_EXIT': str(push_exit)}
                    result = subprocess.run(['bash', '-c', script], cwd=root, env=env,
                                            capture_output=True, text=True)
                    self.assertEqual(result.returncode, expected, result.stderr)
                    self.assertEqual((root / 'committed').exists(), committed)
                    self.assertEqual((root / 'pushed').exists(), pushed)

    def test_release_completion_rejects_skipped_and_missing_stages(self):
        spec = importlib.util.spec_from_file_location('completion', ROOT / 'scripts/check-release-completion.py')
        completion = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(completion)
        needs = {name: {'result': 'success'} for name in completion.REQUIRED}
        self.assertEqual(completion.incomplete_stages(needs), {})
        for name in completion.REQUIRED:
            for result in ('skipped', 'failure', 'cancelled'):
                with self.subTest(stage=name, result=result):
                    broken = {**needs, name: {'result': result}}
                    self.assertEqual(completion.incomplete_stages(broken), {name: result})
            missing = {key: value for key, value in needs.items() if key != name}
            self.assertEqual(completion.incomplete_stages(missing), {name: 'missing'})
        workflow = (ROOT / '.github/workflows/release.yml').read_text().split('  release-complete:\n')[1]
        self.assertIn('if: always()', workflow)
        for name in completion.REQUIRED:
            self.assertIn(name, workflow)

    def test_announcement_recovery_and_tagged_call_guards(self):
        workflow = (ROOT / '.github/workflows/announce-release.yml').read_text()
        gate = re.search(r'^    if: >-\n((?:      .*\n)+)', workflow, re.M).group(1)
        for ref, called, expected in (
            ('refs/heads/main', False, True), ('refs/tags/v9.8.7', True, True),
            ('refs/tags/v9.8.7', False, False), ('refs/heads/feature', False, False),
            ('refs/tags/v9.8.6', True, False),
        ):
            expression = gate
            for field, value in {'inputs.release_workflow_call': called,
                                 'github.ref': ref, 'inputs.tag': 'v9.8.7',
                                 'github.event_name': 'workflow_dispatch'}.items():
                expression = expression.replace(field, repr(value))
            expression = ' '.join(expression.replace('&&', ' and ').replace('||', ' or ').replace('!', ' not ').split())
            with self.subTest(ref=ref, called=called):
                self.assertEqual(workflow_gate_value(ast.parse(expression, mode='eval')), expected)
        caller = (ROOT / '.github/workflows/release.yml').read_text().split('  discord:\n', 1)[1].split('  release-complete:\n', 1)[0]
        self.assertIn('uses: ./.github/workflows/announce-release.yml', caller)
        self.assertIn('needs: [version, release]', caller)
        gate = re.search(r'^    if: >-\n((?:      .*\n)+)', caller, re.M).group(1)
        defaults = {'needs.version.result': 'success', 'needs.release.result': 'success',
                    'needs.downstream-publish.result': 'failure', 'needs.chocolatey.result': 'skipped',
                    'needs.public-publication.result': 'failure', 'github.ref': 'refs/tags/v9.8.7',
                    'inputs.tag': 'v9.8.7', 'inputs.action_tag': 'release',
                    'inputs.runner_pool_tag': 'hosted', 'always()': True, 'cancelled()': False}
        cases = [({}, True), ({'cancelled()': True}, False),
                 ({'github.ref': 'refs/heads/main'}, False),
                 ({'github.ref': 'refs/tags/v9.8.6'}, False),
                 ({'inputs.action_tag': 'validate'}, False),
                 ({'inputs.runner_pool_tag': 'other'}, False)]
        for dependency in ('version', 'release'):
            cases.extend(({f'needs.{dependency}.result': result}, False)
                         for result in ('failure', 'skipped', 'cancelled'))
        for changes, expected in cases:
            expression = gate
            for field, value in {**defaults, **changes}.items():
                expression = expression.replace(field, repr(value))
            expression = ' '.join(expression.replace('&&', ' and ').replace('||', ' or ').replace('!', ' not ').split())
            with self.subTest(changes=changes):
                self.assertEqual(workflow_gate_value(ast.parse(expression, mode='eval')), expected)
        self.assertIn('always() && !cancelled()', caller)
        self.assertIn('release_workflow_call: true', caller)

    def test_chocolatey_is_required_and_accepts_trusted_tag_calls(self):
        workflow = (ROOT / '.github/workflows/publish-chocolatey.yml').read_text()
        gate = re.search(r'^    if: >-\n((?:      .*\n)+)', workflow, re.M).group(1)
        for ref, called, expected in (
            ('refs/heads/main', False, True), ('refs/tags/v9.8.7', True, True),
            ('refs/tags/v9.8.7', False, False), ('refs/heads/feature', False, False),
            ('refs/tags/v9.8.6', True, False),
        ):
            expression = gate
            for field, value in {'inputs.release_workflow_call': called, 'github.ref': ref,
                                 'inputs.tag': 'v9.8.7', 'github.event_name': 'workflow_dispatch',
                                 'inputs.action_tag': 'release', 'inputs.runner_pool_tag': 'hosted'}.items():
                expression = expression.replace(field, repr(value))
            expression = ' '.join(expression.replace('&&', ' and ').replace('||', ' or ').replace('!', ' not ').split())
            with self.subTest(ref=ref, called=called):
                self.assertEqual(workflow_gate_value(ast.parse(expression, mode='eval')), expected)
        caller = (ROOT / '.github/workflows/release.yml').read_text().split('  chocolatey:\n')[1].split('  discord:\n')[0]
        self.assertIn('uses: ./.github/workflows/publish-chocolatey.yml', caller)
        self.assertIn('release_workflow_call: true', caller)
        self.assertIn('publish: true', caller)
        self.assertIn('chocolatey', runpy.run_path(str(ROOT / 'scripts/check-release-completion.py'))['REQUIRED'])

    def test_announcement_uses_current_published_notes_and_safe_mentions(self):
        for tag in ('v9.8.7', 'release-v9.8.7'):
            release = {'tagName': tag, 'url': f'https://github.com/owner/repo/releases/tag/{tag}',
                       'body': 'Current fixed release notes @everyone', 'publishedAt': '2026-11-07', 'isDraft': False}
            payload = build_payload(release, tag, 'owner/repo', 'https://github.com/owner/repo/actions/runs/1')
            self.assertIn(release['body'], payload['embeds'][0]['description'])
            self.assertEqual(payload['embeds'][0]['title'], 'slskr 9.8.7 is live')
            self.assertEqual(payload['allowed_mentions'], {'parse': []})
            for change in ({'isDraft': True}, {'tagName': 'v0.0.0'}, {'body': ''}):
                with self.assertRaises(ValueError):
                    build_payload({**release, **change}, tag, 'owner/repo', 'workflow')
            release['body'] = '\U0001f600' * 5000
            description = build_payload(release, tag, 'owner/repo', 'workflow')['embeds'][0]['description']
            self.assertLessEqual(len(description.encode('utf-16-le')), 7600)

    def test_discord_requires_delivery_confirmation_and_redacts_webhook_errors(self):
        webhook = 'https://discord.com/api/webhooks/123/secret-token?thread_id=456'
        payload = {'embeds': [{'url': 'https://github.com/owner/repo/releases/tag/v1.2.3'}]}
        with patch('discord_announcement.subprocess.run') as send:
            send.return_value = subprocess.CompletedProcess([], 0, '{"id":"789","channel_id":"456"}\n200')
            self.assertEqual(execute_webhook(webhook, payload)['message_id'], '789')
            self.assertIn('wait=true', send.call_args.args[0][-1])
            self.assertIn('thread_id=456', send.call_args.args[0][-1])
            self.assertEqual(json.loads(send.call_args.kwargs['input']), payload)
        with patch('discord_announcement.subprocess.run') as send:
            send.return_value = subprocess.CompletedProcess([], 0, 'secret-token\n403')
            with self.assertRaisesRegex(RuntimeError, 'HTTP 403') as raised:
                execute_webhook(webhook, payload)
            self.assertNotIn('secret-token', str(raised.exception))
        with patch('discord_announcement.subprocess.run') as send:
            send.return_value = subprocess.CompletedProcess([], 0, '{}\n200')
            with self.assertRaisesRegex(RuntimeError, 'no message confirmation'):
                execute_webhook(webhook, payload)
            send.assert_called_once()
        with patch('discord_announcement.subprocess.run', side_effect=subprocess.TimeoutExpired('curl', 35)) as send:
            with self.assertRaisesRegex(RuntimeError, 'not confirmed'):
                execute_webhook(webhook, payload)
            send.assert_called_once()

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
                    self.assertEqual(workflow_gate_value(ast.parse(expression, mode='eval')), expected)

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

    def test_release_archive_verifier_handles_many_web_assets(self):
        with tempfile.TemporaryDirectory(prefix='slskr-verifier-assets-') as tmp:
            artifact_dir = Path(tmp) / 'dist'
            artifact_dir.mkdir()
            target = 'aarch64-unknown-linux-gnu'
            root_name = f'slskr-ci-fixture-{target}'
            archive = artifact_dir / f'{root_name}.tar.gz'
            files = {
                'RUN.txt': f'slskr ci-fixture ({target})\n'.encode(),
                'README.md': b'fixture\n',
                'LICENSE': b'fixture\n',
                'NOTICE': b'fixture\n',
                'COMPLIANCE.md': b'fixture\n',
                'docs/slskr.config.example.toml': b'fixture\n',
                'slskr': b'fixture executable\n',
                'web/build/index.html': b'<html></html>\n',
                'web/build/assets/app.css': b'body {}\n',
            }
            with tarfile.open(archive, 'w:gz') as packaged:
                for name, content in files.items():
                    entry = tarfile.TarInfo(f'{root_name}/{name}')
                    entry.size = len(content)
                    packaged.addfile(entry, io.BytesIO(content))
                for index in range(2048):
                    name = f'web/build/assets/chunk-{index:04d}-' + ('x' * 48) + '.js'
                    content = b'asset\n'
                    entry = tarfile.TarInfo(f'{root_name}/{name}')
                    entry.size = len(content)
                    packaged.addfile(entry, io.BytesIO(content))

            digest = hashlib.sha256(archive.read_bytes()).hexdigest()
            archive.with_name(f'{archive.name}.sha256').write_text(f'{digest}  {archive.name}\n')
            result = subprocess.run(
                ['bash', str(ROOT / 'scripts/verify-release-artifacts.sh'), str(artifact_dir)],
                cwd=ROOT, capture_output=True, text=True,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_legacy_windows_runtime_dependencies_are_removed_for_static_releases(self):
        with tempfile.TemporaryDirectory(prefix='slskr-runtime-metadata-') as tmp:
            root = Path(tmp)
            shutil.copytree(ROOT / 'packaging', root / 'packaging', ignore=shutil.ignore_patterns('build', 'target', 'node_modules'))
            for name in ('flake.nix', 'slskr.xml'):
                shutil.copy2(ROOT / name, root / name)
            assets = root / 'assets'
            assets.mkdir()
            for version, required in (('0.2.83', True), ('0.2.84', False),
                                      ('0.2.86', False), ('0.2.87', False)):
                for target in TARGETS:
                    extension = 'zip' if target.endswith('msvc') else 'tar.gz'
                    (assets / f'slskr-v{version}-{target}.{extension}').write_bytes(b'metadata fixture')
                subprocess.run(['bash', 'packaging/scripts/update-release-metadata.sh', 'v' + version, str(assets)], cwd=root, check=True, capture_output=True)
                installer = (root / 'packaging/winget/snapetech.slskr.installer.yaml').read_text()
                nuspec = (root / 'packaging/chocolatey/slskr.nuspec').read_text()
                self.assertEqual('Microsoft.VCRedist.2015+.x64' in installer, required)
                self.assertEqual('vcredist140' in nuspec, required)
                formula = (root / 'packaging/homebrew/Formula/slskr.rb').read_text()
                self.assertIn('bin.write_exec_script libexec/"slskr"', formula)
                self.assertIn('assert_path_exists libexec/"web/build/index.html"', formula)
                self.assertEqual('  revision 1\n' in formula, version == '0.2.86')

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
