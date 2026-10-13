#!/usr/bin/env python3
"""Exercise the Docker fallback's actual stdin script with offline tool doubles."""
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class AurContainerTests(unittest.TestCase):
    def run_case(self, fail=False, use_real_source=False):
        with tempfile.TemporaryDirectory(prefix='slskr-aur-container-test-') as temporary:
            root = Path(temporary)
            bin_dir = root / 'bin'
            bin_dir.mkdir()
            for name in ['bash', 'dirname', 'mktemp', 'cp', 'rm']:
                (bin_dir / name).symlink_to(Path('/usr/bin') / name)
            for name in ['pacman', 'useradd', 'chown']:
                script = bin_dir / name
                script.write_text('#!/bin/bash\nexit 0\n')
                script.chmod(0o755)
            runuser = bin_dir / 'runuser'
            runuser.write_text('''#!/usr/bin/python3
import json, os, pathlib, stat, sys
args=sys.argv[1:]
assert args[:4] == ['-u','builder','--','makepkg'], args
assert args[-2] == '-p', args
assert '--nobuild' in args and '--verifysource' not in args, 'source verification must not skip extraction/prepare'
assert pathlib.Path(args[-1]).is_file(), 'makepkg must run in the package working directory'
source=pathlib.Path(os.environ['AUR_TEST_SOURCE'])/'packaging/aur'
for fixture in source.rglob('*'):
    relative=fixture.relative_to(source)
    staged=pathlib.Path.cwd()/relative
    assert fixture.is_symlink()==staged.is_symlink(), (
        f'copy changed symlink type for {relative}'
    )
    source_mode=stat.S_IMODE(fixture.lstat().st_mode)
    staged_mode=stat.S_IMODE(staged.lstat().st_mode)
    assert source_mode==staged_mode, (
        f'copy changed POSIX mode for {relative}: '
        f'{source_mode:o} != {staged_mode:o}'
    )
with open(os.environ['AUR_TEST_LOG'],'a') as log:
 log.write(json.dumps({'kind':'makepkg','package':args[-1],'cwd':str(pathlib.Path.cwd())})+'\\n')
if os.environ['AUR_TEST_FAIL']=='1' and args[-1]=='PKGBUILD-bin': sys.exit(23)
''')
            runuser.chmod(0o755)
            docker = bin_dir / 'docker'
            docker.write_text('''#!/usr/bin/python3
import json, os, pathlib, shlex, subprocess, sys
args=sys.argv[1:]
with open(os.environ['AUR_TEST_LOG'],'a') as log:
 log.write(json.dumps({'kind':'docker','args':args})+'\\n')
if args[:2] == ['rm','--force']: sys.exit(0)
assert args[0]=='run'
cid=pathlib.Path(args[args.index('--cidfile')+1]);cid.write_text('a'*64+'\\n')
# Docker without -i succeeds with EOF: deliberately reproduce the old false pass.
if '-i' not in args and '--interactive' not in args: sys.exit(0)
script=sys.stdin.read();assert script, 'container stdin was empty'
script=script.replace('/repo/packaging/aur/.', os.environ['AUR_TEST_SOURCE']+'/packaging/aur/.')
script=script.replace(' -p /tmp ', ' -p '+shlex.quote(os.environ['AUR_TEST_CONTAINER_TMP'])+' ')
sys.exit(subprocess.run(['/bin/bash','-s','--'],input=script,text=True,cwd='/').returncode)
''')
            docker.chmod(0o755)
            log_path = root / 'calls.jsonl'
            container_tmp = root / 'container-tmp'
            container_tmp.mkdir()
            if use_real_source:
                container_source = ROOT
            else:
                container_source = root / 'container-source'
                package_source = container_source / 'packaging' / 'aur'
                package_source.mkdir(parents=True)
                for name in ['PKGBUILD', 'PKGBUILD-bin', 'slskr.service',
                             'slskr.sysusers', 'slskr.tmpfiles']:
                    (package_source / name).write_text(f'test fixture: {name}\n')
            result = subprocess.run(['/bin/bash', str(ROOT / 'scripts/check-aur-package-smoke.sh')],
                env={**os.environ, 'PATH': str(bin_dir), 'AUR_TEST_LOG': str(log_path),
                     'AUR_TEST_SOURCE': str(container_source), 'AUR_TEST_FAIL': str(int(fail)),
                     'AUR_TEST_CONTAINER_TMP': str(container_tmp),
                     'TMPDIR': str(container_tmp), 'TMP': str(container_tmp),
                     'TEMP': str(container_tmp)},
                capture_output=True, text=True, timeout=15)
            calls = [json.loads(line) for line in log_path.read_text().splitlines()]
            self.assertEqual(
                [c['package'] for c in calls if c['kind']=='makepkg'],
                ['PKGBUILD', 'PKGBUILD-bin'],
                f'container smoke did not run both package builds: exit={result.returncode}, '
                f'stdout={result.stdout!r}, stderr={result.stderr!r}, calls={calls!r}',
            )
            self.assertTrue(any(c['kind']=='docker' and c['args']==['rm','--force','a'*64] for c in calls))
            self.assertFalse(Path(next(c['args'][c['args'].index('--cidfile')+1] for c in calls if c['kind']=='docker' and c['args'][0]=='run')).parent.exists())
            return result

    def test_both_package_scripts_execute_from_their_working_directory(self):
        result = self.run_case()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('AUR package smoke passed in archlinux:base-devel', result.stdout)

    def test_repository_package_files_keep_modes_and_symlinks(self):
        result = self.run_case(use_real_source=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('AUR package smoke passed in archlinux:base-devel', result.stdout)

    def test_failed_makepkg_does_not_emit_success_and_cleans_owned_container(self):
        result = self.run_case(fail=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn('AUR package smoke passed', result.stdout)


if __name__=='__main__':
    unittest.main()
