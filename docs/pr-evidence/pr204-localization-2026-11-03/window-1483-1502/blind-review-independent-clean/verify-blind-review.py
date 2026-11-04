#!/usr/bin/env python3
import hashlib,json,re
from collections import Counter
from pathlib import Path
R=Path(__file__).resolve().parent; IN=(R.parent/'candidate-free-input')
def sha(b):return hashlib.sha256(b).hexdigest()
def hs(s):return sha(s.encode())
def j(p):return json.loads(p.read_text(encoding='utf-8'))
def jl(p):return [json.loads(s) for s in p.read_text(encoding='utf-8').splitlines() if s]
m=j(R/'manifest.json'); im=j(IN/'manifest.json')
assert m['head']==im['head'] and m['tree']==im['tree'] and m['selectedPositions']==[1483,1502] and m['cellCount']==240
assert m['candidateFreeInputManifestSha256']==sha((IN/'manifest.json').read_bytes())
sums={}
for line in (R/'SHA256SUMS.txt').read_text().splitlines():
 d,n=line.split(None,1);n=n.lstrip('* ');assert n not in sums;sums[n]=d
actual={p.name for p in R.iterdir() if p.is_file() and p.name!='SHA256SUMS.txt'}
assert set(sums)==actual and set(m['files'])==actual-{'manifest.json'}
for n,d in sums.items():assert sha((R/n).read_bytes())==d,n
for n,x in m['files'].items():
 b=(R/n).read_bytes();assert len(b)==x['byteCount'] and sha(b)==x['sha256'],n
inputs=jl(IN/'current-target-cells.jsonl'); rows=jl(R/'review-ledger.jsonl')
assert len(inputs)==len(rows)==240
assert [(x['position'],x['locale']) for x in inputs]==[(x['position'],x['locale']) for x in rows]
counts=Counter(); mismatch=Counter(); proposal_bad=0
for c,r in zip(inputs,rows):
 assert r['sourceKeySha256']==c['sourceKeySha256']==r['sourceIdSha256']
 assert r['currentTargetSha256']==c['currentTargetSha256'] and r['callerContextSha256']==c['sourceContextSha256']
 assert r['sourceKey']==c['sourceKey'] and r['currentTarget']==c['currentTarget']
 assert r['callerCount']==c['callerCount'] and hs(r['currentTarget'])==r['currentTargetSha256']
 counts[r['decision']]+=1
 for k,x in r['currentTokenChecks'].items():
  if not x['matches']:mismatch[k]+=1
 if r['decision']=='accept-current':
  assert r['suggestedTarget'] is None and r['suggestedTargetSha256'] is None and r['suggestedTokenChecks'] is None
  assert all(x['matches'] for x in r['currentTokenChecks'].values())
 else:
  assert r['decision'] in ('correction','refinement') and r['suggestedTarget']
  assert r['suggestedTargetSha256']==hs(r['suggestedTarget'])
  assert all(x['matches'] for x in r['suggestedTokenChecks'].values())
  proposal_bad+=not all(x['matches'] for x in r['suggestedTokenChecks'].values())
assert dict(counts)=={'accept-current':225,'correction':12,'refinement':3}
assert len([r for r in rows if r['suggestedTarget'] is not None])==15 and proposal_bad==0
assert mismatch==Counter({'protectedLiterals':2})
assert all(r['decision']!='hold' for r in rows)
before=j(R/'PR-attestation-before.json');after=j(R/'PR-attestation-after.json')
for x in (before,after):
 assert x['state']=='OPEN' and x['draft'] and x['head']==m['head'] and x['tree']==m['tree']
 assert x['branchRef']==x['pullRef']==m['head'] and x['deploymentsForHeadCount']==0
 assert x['repositoryDeploymentCount']==0 and x['deploymentActionsIssuedByReview']==0
for k in ('head','tree','headRef','branchRef','pullRef','baseRef','baseSha','mainRef','state','draft','deploymentsForHeadCount','deploymentsForHeadSha256','repositoryDeploymentCount','repositoryDeploymentsSha256'):assert before[k]==after[k]
print(json.dumps({'result':'PASS','head':m['head'],'tree':m['tree'],'cells':len(rows),'decisionCounts':dict(sorted(counts.items())),
 'proposalCount':15,'currentProtectedMismatchCells':2,'proposalTokenMismatches':0,'unresolvedHolds':0,
 'deploymentsBeforeAfter':[0,0],'checksumFiles':len(sums)},indent=2))

