#!/usr/bin/env python3
from pathlib import Path
import hashlib,json,subprocess,sys
W=Path(__file__).resolve().parent
def sha(b): return hashlib.sha256(b).hexdigest()
sums={}
for line in (W/'SHA256SUMS.txt').read_text(encoding='utf-8').splitlines():
    digest,name=line.split(None,1); name=name.lstrip('* ')
    if name in sums: raise SystemExit('FAIL: duplicate checksum '+name)
    sums[name]=digest
actual={p.relative_to(W).as_posix() for p in W.rglob('*') if p.is_file() and p.relative_to(W).as_posix()!='SHA256SUMS.txt'}
if set(sums)!=actual: raise SystemExit('FAIL: root checksum inventory')
for name,digest in sums.items():
    if sha((W/name).read_bytes())!=digest: raise SystemExit('FAIL: checksum '+name)
m=json.loads((W/'manifest.json').read_text(encoding='utf-8')); listed={x['path']:x for x in m['files']}
if set(listed)!=actual-{'manifest.json'}: raise SystemExit('FAIL: root manifest inventory')
for name,info in listed.items():
    raw=(W/name).read_bytes()
    if len(raw)!=info['byteCount'] or sha(raw)!=info['sha256']: raise SystemExit('FAIL: manifest entry '+name)
steps=[('candidateFreeHashOnly',W/'verify-candidate-free-hash-only.py'),('primary',W/'primary-packet'/'output'/'verify-primary.py'),
 ('cleanIndependentBlind',W/'blind-review-independent-clean'/'verify-blind-review.py'),('crossAudit',W/'cross-audit'/'verify-cross-audit.py'),('application',W/'application'/'verify_application.py')]
results={}
for label,script in steps:
    run=subprocess.run([sys.executable,str(script)],cwd=script.parent,text=True,capture_output=True)
    if run.returncode: raise SystemExit('FAIL: '+label+' verifier\n'+run.stdout+run.stderr)
    results[label]='PASS'
print(json.dumps({'result':'PASS','rootFiles':len(sums),'nestedVerifiers':results},indent=2))
