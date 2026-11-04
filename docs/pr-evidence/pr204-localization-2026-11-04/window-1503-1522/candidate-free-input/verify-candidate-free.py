#!/usr/bin/env python3
import hashlib,json,re
from collections import Counter
from pathlib import Path
R=Path(__file__).resolve().parent
HEAD='a7d00cd97602c5910800330190817fcada008162';TREE='2d0a051348394e809ffc3a1fdbfccd20ba8af283'
LOCS=['es','zh-Hans','hi','de','ja','fr','pt-BR','ar','ko','zh-Hant','vi','id']
def sha(b):return hashlib.sha256(b).hexdigest()
def hs(s):return sha(s.encode())
def canon(x):return json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':'))
def j(n):return json.loads((R/n).read_text(encoding='utf-8'))
def jl(n):return [json.loads(s) for s in (R/n).read_text(encoding='utf-8').splitlines() if s]
def toks(s):
 p=re.findall(r'\{[A-Za-z][A-Za-z0-9_]*\}',s);t=re.findall(r'<\/?[A-Za-z][^>]*>',s)
 n=re.findall(r'(?<![A-Za-z])\d+(?:[.,]\d+)?%?(?![A-Za-z])',s);z=[]
 for m in re.finditer(r'(?<![A-Za-z0-9])(?:[A-Z]{2,}[A-Z0-9]*|ffmpeg|Chromaprint|Soulseek|Spotify|YouTube|Pushbullet|Matrix|WebSocket|OpenAI)(?![A-Za-z0-9])',s):
  if m.group(0) not in z:z.append(m.group(0))
 return p,t,n,z
m=j('manifest.json');assert m['head']==HEAD and m['tree']==TREE and m['selectedPositions']==[1503,1522]
assert m['cellCount']==240 and m['candidateFreeInputOnly'] and not m['proposedTranslationsIncluded']
sums={}
for line in (R/'SHA256SUMS.txt').read_text().splitlines():
 d,n=line.split(None,1);n=n.lstrip('* ');assert n not in sums;sums[n]=d
actual={p.name for p in R.iterdir() if p.is_file() and p.name!='SHA256SUMS.txt'}
assert set(sums)==actual and set(m['fileHashes'])==actual-{'manifest.json'}
for n,d in sums.items():assert sha((R/n).read_bytes())==d,n
for n,x in m['fileHashes'].items():
 b=(R/n).read_bytes();assert len(b)==x['byteCount'] and sha(b)==x['sha256'],n
assert not any((R/n).exists() for n in ('prior-hold-reattestation.jsonl','prior-selection-reattestation.jsonl','source-order-lineage.json'))
a=j('PR-attestation.json');b=j('PR-attestation-after.json')
for z in (a,b):
 assert z['state']=='OPEN' and z['draft'] and z['head']==HEAD and z['tree']==TREE
 assert z['branchRef']==z['pullRef']==HEAD and z['deploymentsForHeadCount']==0 and z['repositoryDeploymentCount']==0
 assert z['actionsRunsForHeadCount']==0 and z['deploymentActionsIssuedByReview']==0
for k in ('head','tree','headRef','branchRef','pullRef','baseRef','baseSha','mainRef','state','draft','deploymentsForHeadCount','deploymentsForHeadSha256','repositoryDeploymentCount','repositoryDeploymentsSha256','actionsRunsForHeadCount'):assert a[k]==b[k],k
q=jl('source-queue.jsonl');assert len(q)==5441 and [x['position'] for x in q]==list(range(1,5442))
keys=[x['sourceKey'] for x in q];assert keys==sorted(keys) and len(set(keys))==5441
assert hs('\n'.join(keys)+'\n')==m['sourceLookupKeyOrderSha256']
assert sha((R/'source-queue.jsonl').read_bytes())==m['sourceQueueFileSha256']
qm={x['position']:x for x in q};ctx=jl('source-contexts.jsonl');assert [x['position'] for x in ctx]==list(range(1503,1523));cx={x['position']:x for x in ctx}
for x in ctx:
 assert x['sourceKey']==qm[x['position']]['sourceKey'] and x['sourceKeySha256']==hs(x['sourceKey'])
 assert x['productionCallerCount']==len(x['callers'])==x['callerOccurrenceCount']
 assert x['callerContextSha256']==hs(canon({'sourceKey':x['sourceKey'],'callers':x['callers']}))
 for c in x['callers']:assert c['contextSha256']==hs(canon(c['context'])) and c['lineSha256']==hs(c['lineText'])
cells=jl('current-target-cells.jsonl');assert len(cells)==240
assert [(x['position'],x['locale']) for x in cells]==[(p,l) for p in range(1503,1523) for l in LOCS]
bad=Counter()
for x in cells:
 c=cx[x['position']];assert x['sourceKey']==c['sourceKey'] and x['sourceKeySha256']==hs(x['sourceKey'])
 assert x['currentTargetSha256']==hs(x['currentTarget']) and x['callerCount']==c['productionCallerCount']
 assert x['sourceContextSha256']==c['callerContextSha256']
 st=toks(x['sourceKey']);tt=toks(x['currentTarget']);missing=[z for z in st[3] if z not in tt[3]]
 assert x['sourcePlaceholders']==st[0] and x['currentTargetPlaceholders']==tt[0] and x['placeholderSequenceMatches']==(st[0]==tt[0])
 assert x['sourceMarkupTags']==st[1] and x['currentTargetMarkupTags']==tt[1] and x['markupMatches']==(st[1]==tt[1])
 assert x['sourceNumericTokens']==st[2] and x['currentTargetNumericTokens']==tt[2] and x['numericTokensMatch']==(st[2]==tt[2])
 assert x['sourceProtectedLiterals']==st[3] and x['currentTargetProtectedLiterals']==tt[3]
 assert x['protectedLiteralMismatchTokens']==missing and x['protectedLiteralsMatch']==(not missing)
 bad['placeholderSequenceMismatchCount']+=st[0]!=tt[0];bad['markupMismatchCount']+=st[1]!=tt[1]
 bad['numericTokenMismatchCount']+=st[2]!=tt[2];bad['protectedLiteralMismatchCount']+=bool(missing)
assert dict(bad)==m['mismatchCounts']
prior=j('prior-continuity-hash-summary.json')
sel=jl('prior-selection-hash-reattestation.jsonl');holds=jl('prior-hold-hash-reattestation.jsonl');win=jl('prior-window-selection-hash-only.jsonl')
assert len(sel)==260 and all(x['matchesLiveQueue'] for x in sel)
assert len(holds)==47 and all(x['matchesLiveValue'] for x in holds)
assert len(win)==480 and all(x['liveMatchesPriorResolution'] for x in win)
assert prior['priorHolds']['recordCount']==prior['priorHolds']['unchangedCount']==47
assert prior['previousWindowCells']['recordCount']==480 and prior['previousWindowCells']['allMatchLiveCatalog']
for rows in (sel,holds,win):
 for x in rows:assert not any(k in x for k in ('sourceKey','currentTarget','target','crossTarget','proposedTarget','source','targetText','lineText'))
print(json.dumps({'result':'PASS','head':HEAD,'tree':TREE,'sourceQueueRows':len(q),'cells':len(cells),
 'callerReferences':m['callerReferenceCount'],'callerlessPositions':m['callerResolutionHoldPositions'],
 'priorSelectionHashes':len(sel),'priorHoldHashes':len(holds),'priorHoldsUnchanged':47,'priorWindowHashes':len(win),
 'tokenMismatchCounts':dict(bad),'checksums':len(sums),'refsStable':True,'deploymentsBeforeAfter':[0,0],
 'actionsRunsBeforeAfter':[0,0]},indent=2))

