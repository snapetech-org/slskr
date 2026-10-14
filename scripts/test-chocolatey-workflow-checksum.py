#!/usr/bin/env python3
"""Execute the actual workflow verifier against bounded checksum fixtures."""
import hashlib
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import tempfile
import textwrap
import unittest

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / '.github/workflows/publish-chocolatey.yml'
NAME = 'slskr-v0.2.40-x86_64-pc-windows-msvc.zip'
PAYLOAD = b'isolated checksum regression fixture\n'
SHA = hashlib.sha256(PAYLOAD).hexdigest()
# Hosted Linux PowerShell cold startup exceeded the old ten-second bound.
# Retain a deadline and subprocess.run's kill/wait cleanup on expiration.
POWERSHELL_TIMEOUT_SECONDS = 60


def powershell_invocation(aqua_root, executable=None):
    executable = executable or shutil.which('pwsh')
    if not executable:
        return None, None

    try:
        wrapper_lines = Path(executable).read_text().splitlines()
    except (OSError, UnicodeError):
        return [executable], None

    exports = {}
    proxy = None
    for line in wrapper_lines:
        line = line.strip()
        if line.startswith('export '):
            name, separator, value = line.removeprefix('export ').partition('=')
            if separator:
                try:
                    parsed = shlex.split(value)
                except ValueError:
                    continue
                if len(parsed) == 1:
                    exports[name] = parsed[0]
        elif line.startswith('exec '):
            try:
                command = shlex.split(line.removeprefix('exec '))
            except ValueError:
                continue
            if command and Path(command[0]).name == 'pwsh':
                proxy = command[0]

    if proxy and exports.get('AQUA_ROOT_DIR') and exports.get('AQUA_CONFIG'):
        environment = os.environ.copy()
        environment.update(exports)
        # The runner's Aqua wrapper may point at a root-owned shared cache. Call
        # its proxy directly and keep lazy installation inside this test's
        # temporary directory instead of mutating shared runner state.
        environment['AQUA_ROOT_DIR'] = str(aqua_root)
        return [proxy], environment

    return [executable], None


def verifier():
    text = WORKFLOW.read_text()
    section = text.split('      - name: Verify release asset checksum\n', 1)[1]
    section = section.split('      - name: Resolve package version\n', 1)[0]
    return textwrap.dedent(section.split('        run: |\n', 1)[1])


class PowerShellWrapperTests(unittest.TestCase):
    def test_aqua_wrapper_uses_a_private_install_root(self):
        with tempfile.TemporaryDirectory(prefix='slskr-aqua-wrapper-') as directory:
            root = Path(directory)
            wrapper = root / 'pwsh'
            shared_root = root / 'shared-aqua'
            config = root / 'aqua.yaml'
            policy = root / 'aqua-policy.yaml'
            wrapper.write_text(
                '#!/usr/bin/env bash\n'
                f'export AQUA_ROOT_DIR={shlex.quote(str(shared_root))}\n'
                f'export AQUA_CONFIG={shlex.quote(str(config))}\n'
                f'export AQUA_POLICY_CONFIG={shlex.quote(str(policy))}\n'
                f'exec {shlex.quote(str(shared_root / "bin" / "pwsh"))} "$@"\n'
            )
            private_root = root / 'aqua-root'
            command, environment = powershell_invocation(private_root, str(wrapper))

        self.assertEqual(command, [str(shared_root / 'bin' / 'pwsh')])
        self.assertEqual(environment['AQUA_ROOT_DIR'], str(private_root))
        self.assertEqual(environment['AQUA_CONFIG'], str(config))
        self.assertEqual(environment['AQUA_POLICY_CONFIG'], str(policy))


def has_runnable_powershell():
    executable = shutil.which('pwsh')
    if not executable:
        return False
    lazy_proxy = Path(executable).resolve().name == 'aqua-proxy'
    return not (os.environ.get('RUNNER_ENVIRONMENT') == 'self-hosted' and lazy_proxy)


@unittest.skipUnless(has_runnable_powershell(), 'requires runnable PowerShell; skip the shared self-hosted Aqua proxy')
class ChecksumTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.aqua_root = tempfile.TemporaryDirectory(prefix='slskr-chocolatey-aqua-')
        cls.addClassCleanup(cls.aqua_root.cleanup)
        cls.pwsh_command, cls.pwsh_environment = powershell_invocation(
            Path(cls.aqua_root.name) / 'aqua-root'
        )

    def run_fixture(self, rows, succeeds):
        with tempfile.TemporaryDirectory(prefix='slskr-chocolatey-checksum-') as directory:
            root = Path(directory)
            assets = root / 'release-assets'
            assets.mkdir()
            (assets / NAME).write_bytes(PAYLOAD)
            (assets / 'SHA256SUMS.txt').write_text(rows)
            script = root / 'verify.ps1'
            script.write_text(verifier())
            result = subprocess.run([*self.pwsh_command, '-NoLogo', '-NoProfile', '-File', str(script)],
                                    cwd=root, capture_output=True, text=True,
                                    env=self.pwsh_environment,
                                    timeout=POWERSHELL_TIMEOUT_SECONDS)
            if succeeds:
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn('Verified SHA256', result.stdout)
            else:
                self.assertNotEqual(result.returncode, 0)

    def test_plain_basename(self):
        self.run_fixture(f'{SHA}  {NAME}\n', True)

    def test_published_dot_prefix(self):
        self.run_fixture(f'{SHA}  ./{NAME}\n', True)

    def test_binary_mode_dot_prefix(self):
        self.run_fixture(f'{SHA} *./{NAME}\n', True)

    def test_missing_entry(self):
        self.run_fixture(f'{SHA}  unrelated.zip\n', False)

    def test_duplicate_aliases(self):
        self.run_fixture(f'{SHA}  {NAME}\n{SHA}  ./{NAME}\n', False)

    def test_wrong_hash(self):
        self.run_fixture(f'{"0" * 64}  ./{NAME}\n', False)

    def test_other_directory_is_rejected(self):
        self.run_fixture(f'{SHA}  elsewhere/{NAME}\n', False)

    def test_suffix_is_rejected(self):
        self.run_fixture(f'{SHA}  ./{NAME}.other\n', False)


if __name__ == '__main__':
    unittest.main()
