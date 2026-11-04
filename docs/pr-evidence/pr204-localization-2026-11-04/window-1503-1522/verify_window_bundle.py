#!/usr/bin/env python3
"""Portable verifier for PR #204 localization window W1503-W1522."""
import hashlib, json, pathlib, subprocess, sys
ROOT=pathlib.Path(__file__).resolve().parents[4]
EVID=ROOT/'docs/pr-evidence/pr204-localization-2026-11-04/window-1503-1522'
def fail(msg):
    raise SystemExit('FAIL: '+msg)
def sha(data): return hashlib.sha256(data).hexdigest()
# Validate the original sealed packet manifest, including the primary and blind evidence.
manifest=EVID/'SHA256SUMS.txt'
for line in manifest.read_text(encoding='utf-8').splitlines():
    expected, rel=line.split('  ',1)
    p=EVID/rel
    if not p.is_file() or sha(p.read_bytes())!=expected: fail('packet checksum mismatch: '+rel)
for line in (EVID/'APPLICATION-SHA256SUMS.txt').read_text(encoding='utf-8').splitlines():
    expected, rel=line.split('  ',1)
    p=EVID/rel
    if not p.is_file() or sha(p.read_bytes())!=expected: fail('application checksum mismatch: '+rel)
ledger=[json.loads(x) for x in (EVID/'cross-review/root-cross-ledger.jsonl').read_text(encoding='utf-8').splitlines()]
readback=[json.loads(x) for x in (EVID/'application-readback.jsonl').read_text(encoding='utf-8').splitlines()]
meta=json.loads((EVID/'application-readback-metadata.json').read_text(encoding='utf-8'))
if len(ledger)!=240 or len(readback)!=240: fail('expected 240 ledger/readback cells')
if sum(r.get('action')=='update' for r in ledger)!=12: fail('expected exactly 12 updates')
if sum(r.get('action')=='no-op' for r in ledger)!=228: fail('expected 228 no-op/accept-current rows')
if meta.get('catalogCommit')!=readback[0].get('catalogCommit'): fail('metadata commit mismatch')
commit=meta['catalogCommit']
head=subprocess.check_output(['git','rev-parse',commit],cwd=ROOT,text=True).strip()
if head!=commit: fail('catalog commit is unavailable')
tree=subprocess.check_output(['git','rev-parse',commit+'^{tree}'],cwd=ROOT,text=True).strip()
if tree!=meta.get('catalogTree'): fail('catalog commit tree mismatch')
if subprocess.check_output(['git','rev-parse',commit+'^'],cwd=ROOT,text=True).strip()!=meta['reviewedParentHead']: fail('catalog commit parent differs from reviewed head')
for a,b in zip(ledger,readback):
    for key in ('position','locale','catalogPath','sourceText','action','currentTarget','currentTargetSha256','selectedTarget','selectedTargetSha256'):
        if a.get(key)!=b.get(key): fail(f'ledger/readback mismatch at {a.get("position")} {a.get("locale")}: {key}')
    expected=a['selectedTarget'] if a['action']=='update' else a['currentTarget']
    if b.get('readbackTarget')!=expected or sha(expected.encode())!=b.get('readbackTargetSha256'): fail(f'readback hash/value mismatch at {a["position"]} {a["locale"]}')
    blob=subprocess.check_output(['git','show',commit+':'+a['catalogPath']],cwd=ROOT)
    data=json.loads(blob.decode('utf-8'))
    if data.get(a['sourceText'])!=expected: fail(f'catalog mismatch at {a["position"]} {a["locale"]}')
if meta.get('cells')!=240 or meta.get('updates')!=12 or meta.get('acceptCurrent')!=228: fail('metadata counts mismatch')
print(json.dumps({'result':'PASS','catalogCommit':commit,'catalogTree':tree,'cells':240,'updates':12,'acceptCurrent':228,'holds':0},sort_keys=True))
