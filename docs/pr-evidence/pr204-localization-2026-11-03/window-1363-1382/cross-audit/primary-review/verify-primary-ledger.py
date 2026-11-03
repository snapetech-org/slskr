#!/usr/bin/env python3
import hashlib,json
from collections import Counter
from pathlib import Path
root=Path(__file__).resolve().parent
def sha(b): return hashlib.sha256(b).hexdigest()
def canon(x): return json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()
def loadj(p): return json.loads(p.read_text(encoding='utf-8'))
def jl(p): return [json.loads(x) for x in p.read_text(encoding='utf-8').splitlines() if x.strip()]
m=loadj(root/'manifest.json'); rows=jl(root/'review-ledger.jsonl'); contexts=jl(root/'source-context-evidence.jsonl')
assert len(rows)==240 and len(contexts)==20
locs=m['localeOrder']; assert [r['position'] for r in contexts]==list(range(1363,1383))
assert [(r['position'],r['locale']) for r in rows]==[(p,l) for p in range(1363,1383) for l in locs]
ctx={r['position']:r for r in contexts}; counts=Counter(r['disposition'] for r in rows)
for c in contexts:
 assert sha(canon(c['evidence']))==c['sourceContextRecordSha256']
for r in rows:
 d=r['disposition']; assert ('proposedTarget' in r)==(d in ('correction','refinement'))
 q=r['checks']; assert q['placeholderSequencePreserved'] and q['markupPreserved'] and q['numericTokensPreserved'] and q['protectedLiteralsPreservedInReviewedTarget'] and q['icuSyntaxPreserved']
 assert q['pathExampleTokensPreserved'] is not False or r['position']==1376
 c=ctx[r['position']]
 assert c['sourceContextRecordSha256']==r['callerEvidence']['sourceContextEvidenceSha256'] and c['callerContextSha256']==r['callerEvidence']['callerContextSha256']
 assert c['evidence']['productionCallerCount']==r['callerEvidence']['productionCallerCount']
 if r['position']==1376: assert d=='hold' and c['evidence']['productionCallerCount']==0 and 'proposedTarget' not in r
 else: assert d!='hold'
assert dict(counts)=={'accept-current':203,'correction':7,'hold':12,'refinement':18},counts
for name,h in m['files'].items(): assert sha((root/name).read_bytes())==h,(name,'sha mismatch')
print(json.dumps({'result':'PASS','cells':len(rows),'sourceContexts':len(contexts),'dispositions':dict(sorted(counts.items())),'callerlessPosition1376HeldAcrossLocales':sum(r['position']==1376 and r['disposition']=='hold' for r in rows)==12,'unresolvedPathExampleMismatchCells':sum(r['checks']['pathExampleTokensPreserved'] is False for r in rows),'fileHashesVerified':sorted(m['files'])},ensure_ascii=False,sort_keys=True,indent=2))
