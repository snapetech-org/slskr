#!/usr/bin/env python3
import hashlib,json,re
from collections import Counter
from pathlib import Path
R=Path(__file__).resolve().parent
HEAD='a8c2b4cf5f771f8b574001239aa9217697097d6f'
TREE='35f48ee94ec7bcaa3b8b47869f2dd119e219ccfd'
LOCS=['es','zh-Hans','hi','de','ja','fr','pt-BR','ar','ko','zh-Hant','vi','id']
def sha(b): return hashlib.sha256(b).hexdigest()
def hs(s): return sha(s.encode())
def canon(x): return json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':'))
def j(n): return json.loads((R/n).read_text(encoding='utf-8'))
def jl(n): return [json.loads(s) for s in (R/n).read_text(encoding='utf-8').splitlines() if s]
def tokens(s):
 p=re.findall(r'\{[A-Za-z][A-Za-z0-9_]*\}',s); t=re.findall(r'<\/?[A-Za-z][^>]*>',s)
 n=re.findall(r'(?<![A-Za-z])\d+(?:[.,]\d+)?%?(?![A-Za-z])',s); z=[]
 for m in re.finditer(r'(?<![A-Za-z0-9])(?:[A-Z]{2,}[A-Z0-9]*|ffmpeg|Chromaprint|Soulseek|Spotify|YouTube|Pushbullet|Matrix|WebSocket|OpenAI)(?![A-Za-z0-9])',s):
  if m.group(0) not in z:z.append(m.group(0))
 return p,t,n,z
m=j('manifest.json')
assert m['head']==HEAD and m['tree']==TREE and m['selectedPositions']==[1483,1502]
assert m['cellCount']==240 and m['candidateFreeInputOnly'] and not m['proposedTranslationsIncluded']
sums={}
for line in (R/'SHA256SUMS.txt').read_text().splitlines():
 d,n=line.split(None,1); n=n.lstrip('* '); assert n not in sums;sums[n]=d
actual={p.name for p in R.iterdir() if p.is_file() and p.name!='SHA256SUMS.txt'}
assert set(sums)==actual
for n,d in sums.items(): assert sha((R/n).read_bytes())==d,n
assert set(m['fileHashes'])==actual-{'manifest.json'}
for n,x in m['fileHashes'].items():
 b=(R/n).read_bytes();assert len(b)==x['byteCount'] and sha(b)==x['sha256'],n
assert not any((R/n).exists() for n in ('prior-hold-reattestation.jsonl','prior-selection-reattestation.jsonl','source-order-lineage.json'))
a=j('PR-attestation.json'); b=j('PR-attestation-after.json')
for q in (a,b):
 assert q['state']=='OPEN' and q['draft'] is True and q['head']==HEAD and q['tree']==TREE
 assert q['branchRef']==q['pullRef']==HEAD and q['deploymentsForHeadCount']==0 and q['repositoryDeploymentCount']==0
 assert q['deploymentActionsIssuedByReview']==0
for k in ('head','tree','headRef','branchRef','pullRef','baseRef','baseSha','mainRef','state','draft','deploymentsForHeadCount','deploymentsForHeadSha256','repositoryDeploymentCount','repositoryDeploymentsSha256'):
 assert a[k]==b[k],k
q=jl('source-queue.jsonl'); assert len(q)==5441
keys=[x['sourceKey'] for x in q]; assert keys==sorted(keys) and len(set(keys))==len(keys)
assert [x['position'] for x in q]==list(range(1,5442))
assert hs('\n'.join(keys)+'\n')==m['sourceLookupKeyOrderSha256']
assert sha((R/'source-queue.jsonl').read_bytes())==m['sourceQueueFileSha256']
qm={x['position']:x for x in q}; ctx=jl('source-contexts.jsonl'); assert [x['position'] for x in ctx]==list(range(1483,1503))
cx={x['position']:x for x in ctx}
for x in ctx:
 assert x['sourceKey']==qm[x['position']]['sourceKey'] and x['sourceKeySha256']==hs(x['sourceKey'])
 assert x['productionCallerCount']==len(x['callers'])==x['callerOccurrenceCount']
 assert x['callerContextSha256']==hs(canon({'sourceKey':x['sourceKey'],'callers':x['callers']}))
 for c in x['callers']:
  assert c['contextSha256']==hs(canon(c['context'])) and c['lineSha256']==hs(c['lineText'])
  assert sum(1 for z in c['context'] if z['line']==c['line'] and z['text']==c['lineText'])==1
cells=jl('current-target-cells.jsonl'); assert len(cells)==240
expected=[(p,l) for p in range(1483,1503) for l in LOCS]
assert [(x['position'],x['locale']) for x in cells]==expected
bad=Counter()
for x in cells:
 c=cx[x['position']]; assert x['sourceKey']==c['sourceKey'] and x['sourceKeySha256']==hs(x['sourceKey'])
 assert x['currentTargetSha256']==hs(x['currentTarget'])
 assert x['callerCount']==c['productionCallerCount'] and x['sourceContextSha256']==c['callerContextSha256']
 st=tokens(x['sourceKey']); tt=tokens(x['currentTarget'])
 assert x['sourcePlaceholders']==st[0] and x['currentTargetPlaceholders']==tt[0] and x['placeholderSequenceMatches']==(st[0]==tt[0])
 assert x['sourceMarkupTags']==st[1] and x['currentTargetMarkupTags']==tt[1] and x['markupMatches']==(st[1]==tt[1])
 assert x['sourceNumericTokens']==st[2] and x['currentTargetNumericTokens']==tt[2] and x['numericTokensMatch']==(st[2]==tt[2])
 missing=[t for t in st[3] if t not in tt[3]]
 assert x['sourceProtectedLiterals']==st[3] and x['currentTargetProtectedLiterals']==tt[3]
 assert x['protectedLiteralMismatchTokens']==missing and x['protectedLiteralsMatch']==(not missing)
 bad['placeholderSequenceMismatchCount']+=st[0]!=tt[0]
 bad['markupMismatchCount']+=st[1]!=tt[1];bad['numericTokenMismatchCount']+=st[2]!=tt[2];bad['protectedLiteralMismatchCount']+=bool(missing)
assert dict(bad)==m['mismatchCounts']
prior=j('prior-continuity-hash-summary.json')
assert prior['olderPriorSelectionReattestation']['recordCount']==prior['olderPriorSelectionReattestation']['matchesLiveQueueCount']==220
assert prior['olderCarryForwardHolds']['recordCount']==prior['olderCarryForwardHolds']['unchangedCount']==35
assert prior['previousWindow']['cellCount']==prior['previousWindow']['hashOnlyCellRecordCount']==240
for name,rows in [('prior-selection-hash-reattestation.jsonl',jl('prior-selection-hash-reattestation.jsonl')),
 ('prior-hold-hash-reattestation.jsonl',jl('prior-hold-hash-reattestation.jsonl')),
 ('prior-window-selection-hash-only.jsonl',jl('prior-window-selection-hash-only.jsonl'))]:
 for row in rows:
  assert not any(k in row for k in ('sourceKey','currentTarget','target','crossTarget','proposedTarget','lineText'))
  assert not any(k in row for k in ('source','proposal'))
assert all(x['matchesLiveQueue'] for x in jl('prior-selection-hash-reattestation.jsonl'))
assert all(x['matchesLiveValue'] for x in jl('prior-hold-hash-reattestation.jsonl'))
assert all(x['liveMatchesPriorResolution'] for x in jl('prior-window-selection-hash-only.jsonl'))
print(json.dumps({'result':'PASS','head':HEAD,'tree':TREE,'sourceQueueRows':len(q),'cells':len(cells),
 'callerReferences':m['callerReferenceCount'],'callerlessPositions':m['callerResolutionHoldPositions'],
 'priorSelectionHashes':220,'unchangedPriorHoldHashes':35,'priorWindowHashRows':240,
 'tokenMismatchCounts':dict(bad),'checksumFiles':len(sums),'refsStable':True,'deploymentsBeforeAfter':[0,0]},indent=2))

