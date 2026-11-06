#!/usr/bin/env python3
import hashlib,json
from collections import Counter
from pathlib import Path
R=Path(__file__).resolve().parent; IN=(R.parents[1]/'candidate-free-input')
def sha(b):return hashlib.sha256(b).hexdigest()
def hs(s):return sha(s.encode())
def j(p):return json.loads(p.read_text(encoding='utf-8'))
def jl(p):return [json.loads(s) for s in p.read_text(encoding='utf-8').splitlines() if s]
m=j(R/'manifest.json');im=j(IN/'manifest.json')
assert m['head']==im['head'] and m['tree']==im['tree'] and m['selectedPositions']==[1483,1502]
assert m['cellCount']==240 and m['candidateFreeInputManifestSha256']==sha((IN/'manifest.json').read_bytes())
sums={}
for line in (R/'SHA256SUMS.txt').read_text().splitlines():
 d,n=line.split(None,1);n=n.lstrip('* ');assert n not in sums;sums[n]=d
actual={p.name for p in R.iterdir() if p.is_file() and p.name!='SHA256SUMS.txt'}
assert set(sums)==actual and set(m['files'])==actual-{'manifest.json'}
for n,d in sums.items():assert sha((R/n).read_bytes())==d,n
for n,x in m['files'].items():
 b=(R/n).read_bytes();assert len(b)==x['byteCount'] and sha(b)==x['sha256'],n
inputs=jl(IN/'current-target-cells.jsonl');rows=jl(R/'primary-ledger.jsonl')
assert len(inputs)==len(rows)==240 and [(x['position'],x['locale']) for x in inputs]==[(x['position'],x['locale']) for x in rows]
counts=Counter();bad=Counter()
for c,r in zip(inputs,rows):
 assert r['sourceKeySha256']==r['sourceIdSha256']==c['sourceKeySha256']
 assert r['sourceKey']==c['sourceKey'] and r['currentTarget']==c['currentTarget'] and r['currentTargetSha256']==c['currentTargetSha256']
 assert r['callerContextSha256']==c['sourceContextSha256'] and r['callerCount']==c['callerCount']
 counts[r['disposition']]+=1
 for k,v in r['currentTokenChecks'].items():
  if not v['matches']:bad[k]+=1
 if r['disposition']=='accept-current':
  assert r['proposedTarget'] is None and r['proposedTargetSha256'] is None and r['proposedTokenChecks'] is None
  assert all(v['matches'] for v in r['currentTokenChecks'].values())
 else:
  assert r['disposition'] in ('correct','refine') and r['proposedTarget']
  assert r['proposedTargetSha256']==hs(r['proposedTarget'])
  assert all(v['matches'] for v in r['proposedTokenChecks'].values())
assert dict(counts)=={'accept-current':228,'correct':12} and sum(counts.values())==240
assert len([x for x in rows if x['proposedTarget'] is not None])==12
assert bad==Counter({'protectedLiterals':2})
before=j(R/'PR-attestation-before.json');after=j(R/'PR-attestation-after.json')
for x in (before,after):
 assert x['state']=='OPEN' and x['draft'] and x['head']==m['head'] and x['tree']==m['tree']
 assert x['branchRef']==x['pullRef']==m['head'] and x['deploymentsForHeadCount']==0 and x['repositoryDeploymentCount']==0
for k in ('head','tree','headRef','branchRef','pullRef','baseRef','baseSha','mainRef','state','draft','deploymentsForHeadCount','deploymentsForHeadSha256','repositoryDeploymentCount','repositoryDeploymentsSha256'):assert before[k]==after[k]
print(json.dumps({'result':'PASS','head':m['head'],'tree':m['tree'],'cells':len(rows),'dispositions':dict(sorted(counts.items())),
 'proposalCount':12,'currentProtectedMismatchCells':2,'proposalTokenMismatches':0,'unresolvedHolds':0,
 'deploymentsBeforeAfter':[0,0],'checksumFiles':len(sums)},indent=2))

