#!/usr/bin/env python3
"""Verify the sealed portable W1423-W1442 review/application bundle."""
from pathlib import Path
import hashlib, json, subprocess, sys

WINDOW = Path(__file__).resolve().parent
REPO = WINDOW.parents[3]

def sha(data):
    return hashlib.sha256(data).hexdigest()

def fail(message):
    raise SystemExit('FAIL: ' + message)

checksum = WINDOW / 'SHA256SUMS.txt'
if not checksum.is_file():
    fail('missing SHA256SUMS.txt')
listed = {}
for line in checksum.read_text(encoding='utf-8').splitlines():
    if not line.strip():
        continue
    digest, rel = line.split('  ', 1)
    if rel in listed:
        fail('duplicate checksum path: ' + rel)
    listed[rel] = digest
actual = {p.relative_to(WINDOW).as_posix() for p in WINDOW.rglob('*') if p.is_file() and p != checksum}
if set(listed) != actual:
    fail('SHA256SUMS file inventory mismatch')
for rel, expected in listed.items():
    if sha((WINDOW / rel).read_bytes()) != expected:
        fail('SHA256 mismatch: ' + rel)
manifest = json.loads((WINDOW / 'manifest.json').read_text(encoding='utf-8'))
manifest_files = {row['path']: row for row in manifest['files']}
expected_paths = actual - {'manifest.json'}
if set(manifest_files) != expected_paths:
    fail('manifest inventory mismatch')
for rel, row in manifest_files.items():
    raw = (WINDOW / rel).read_bytes()
    if len(raw) != row['bytes'] or sha(raw) != row['sha256']:
        fail('manifest mismatch: ' + rel)
run = subprocess.run([sys.executable, str(WINDOW / 'application' / 'verify_application.py')] + (['--allow-uncommitted'] if '--allow-uncommitted' in sys.argv else []), cwd=REPO, text=True, capture_output=True)
if run.returncode:
    fail('application verifier failed: ' + run.stdout + run.stderr)
print(json.dumps({'result': 'PASS', 'files': len(listed), 'manifestFiles': len(manifest_files), 'applicationVerifier': 'PASS'}, indent=2))
print(run.stdout, end='')
