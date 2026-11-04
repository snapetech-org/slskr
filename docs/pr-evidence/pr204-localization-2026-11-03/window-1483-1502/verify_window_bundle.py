#!/usr/bin/env python3
import hashlib,json,subprocess,sys
from pathlib import Path
R=Path(__file__).resolve().parent
def sha(b):return hashlib.sha256(b).hexdigest()
def j(p):return json.loads(p.read_text(encoding='utf-8'))
def run(label,script):
 q=subprocess.run([sys.executable,str(script)],cwd=script.parent,text=True,capture_output=True)
 if q.returncode:raise SystemExit('FAIL: '+label+' verifier\n'+q.stdout+q.stderr)
 return 'PASS'
m=j(R/'manifest.json')
sums={}
for line in (R/'SHA256SUMS.txt').read_text(encoding='utf-8').splitlines():
 d,n=line.split(None,1);n=n.lstrip('* ');assert n not in sums;sums[n]=d
actual={p.relative_to(R).as_posix() for p in R.rglob('*') if p.is_file() and p.relative_to(R).as_posix()!='SHA256SUMS.txt'}
assert set(sums)==actual
for n,d in sums.items():assert sha((R/n).read_bytes())==d,n
assert set(m['files'])==actual-{'manifest.json'}
for n,x in m['files'].items():
 b=(R/n).read_bytes();assert len(b)==x['byteCount'] and sha(b)==x['sha256'],n
cf=R/'candidate-free-input'; primary=R/'primary-packet'/'output'; blind=R/'blind-review-independent-clean'; cross=R/'cross-audit'; app=R/'application'
steps=[('candidateFree',cf/'verify-candidate-free.py'),('primary',primary/'verify-primary.py'),
 ('cleanIndependentBlind',blind/'verify-blind-review.py'),('crossAudit',cross/'verify-cross-audit.py'),('application',app/'verify_application.py')]
results={name:run(name,path) for name,path in steps}
im=j(cf/'manifest.json'); cm=j(cross/'cross-summary.json'); am=j(app/'commit-record.json')
assert m['head']==im['head']=='a8c2b4cf5f771f8b574001239aa9217697097d6f'
assert m['tree']==im['tree']=='35f48ee94ec7bcaa3b8b47869f2dd119e219ccfd'
assert m['selectedPositions']==[1483,1502] and m['cellCount']==240
assert m['finalDispositionCounts']=={'accept-current':225,'correction':12,'refinement':3}
assert cm['finalDispositionCounts']==m['finalDispositionCounts']
assert m['catalogCommitSha']==am['catalogCommitSha']=='15a3cfffc8f800f2420847e7a98e1f2e94b33819'
assert m['catalogCommitParent']==am['catalogCommitParent']==im['head']
assert am['updatedCellCount']==15 and am['updatedCatalogFileCount']==8
assert cm['unresolvedHoldCount']==0 and cm['proposedTargetProtectedMismatchCount']==0
assert m['priorContinuityPolicy']=='hash-only'
for name in ('prior-hold-reattestation.jsonl','prior-selection-reattestation.jsonl','source-order-lineage.json'):
 assert not (cf/name).exists()
assert not (R/'blind-review').exists()
print(json.dumps({'result':'PASS','rootFiles':len(sums),'positions':[1483,1502],'cells':240,
 'finalDispositionCounts':m['finalDispositionCounts'],'catalogCommit':m['catalogCommitSha'],
 'nestedVerifiers':results,'priorContinuity':'hash-only','checksumEntries':len(sums)},indent=2))

