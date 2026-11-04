#!/usr/bin/env python3
import hashlib,json,re
from collections import Counter
from pathlib import Path
R=Path(__file__).resolve().parent; BASE=R.parent; IN=BASE/'candidate-free-input'; P=BASE/'primary-packet'/'output'; B=BASE/'blind-review-independent-clean'
def sha(b):return hashlib.sha256(b).hexdigest()
def hs(s):return sha(s.encode())
def j(p):return json.loads(p.read_text(encoding='utf-8'))
def jl(p):return [json.loads(s) for s in p.read_text(encoding='utf-8').splitlines() if s]
def toks(s):
 x={'placeholders':re.findall(r'\{[A-Za-z][A-Za-z0-9_]*\}',s),'markupTags':re.findall(r'<\/?[A-Za-z][^>]*>',s),
 'numericTokens':re.findall(r'(?<![A-Za-z])\d+(?:[.,]\d+)?%?(?![A-Za-z])',s)}
 z=[]
 for m in re.finditer(r'(?<![A-Za-z0-9])(?:[A-Z]{2,}[A-Z0-9]*|ffmpeg|Chromaprint|Soulseek|Spotify|YouTube|Pushbullet|Matrix|WebSocket|OpenAI)(?![A-Za-z0-9])',s):
  if m.group(0) not in z:z.append(m.group(0))
 x['protectedLiterals']=z;return x
m=j(R/'manifest.json'); im=j(IN/'manifest.json'); pm=j(P/'manifest.json'); bm=j(B/'manifest.json')
assert m['head']==im['head']==pm['head']==bm['head']=='a8c2b4cf5f771f8b574001239aa9217697097d6f'
assert m['tree']==im['tree']==pm['tree']==bm['tree']=='35f48ee94ec7bcaa3b8b47869f2dd119e219ccfd'
assert m['positions']==[1483,1502] and m['cellCount']==240
assert m['inputPins']['candidateFreeManifestSha256']==sha((IN/'manifest.json').read_bytes())
assert m['inputPins']['primaryLedgerSha256']==sha((P/'primary-ledger.jsonl').read_bytes())
assert m['inputPins']['cleanBlindLedgerSha256']==sha((B/'review-ledger.jsonl').read_bytes())
sums={}
for line in (R/'SHA256SUMS.txt').read_text().splitlines():
 d,n=line.split(None,1);n=n.lstrip('* ');assert n not in sums;sums[n]=d
actual={p.name for p in R.iterdir() if p.is_file() and p.name!='SHA256SUMS.txt'}
assert set(sums)==actual and set(m['files'])==actual-{'manifest.json'}
for n,d in sums.items():assert sha((R/n).read_bytes())==d,n
for n,x in m['files'].items():
 b=(R/n).read_bytes();assert len(b)==x['byteCount'] and sha(b)==x['sha256'],n
assert m['summarySha256']==sha((R/'cross-summary.json').read_bytes())
summary=j(R/'cross-summary.json'); assert summary['cellCount']==240 and summary['unresolvedHoldCount']==0
assert summary['finalDispositionCounts']=={'accept-current':225,'correction':12,'refinement':3}
assert summary['currentTokenMismatchCounts']=={'placeholder':0,'markup':0,'numeric':0,'protectedLiteral':2}
assert summary['proposedTargetProtectedMismatchCount']==0 and summary['remainingAcceptedCurrentProtectedMismatchCount']==0
i=jl(IN/'current-target-cells.jsonl');p=jl(P/'primary-ledger.jsonl');b=jl(B/'review-ledger.jsonl');x=jl(R/'cross-ledger.jsonl')
assert len(i)==len(p)==len(b)==len(x)==240
assert [(r['position'],r['locale']) for r in i]==[(r['position'],r['locale']) for r in p]==[(r['position'],r['locale']) for r in b]==[(r['position'],r['locale']) for r in x]
counts=Counter(); cbad=Counter(); pbad=0; disagreements=0; blind_only=0
for c,pr,br,r in zip(i,p,b,x):
 key=(c['position'],c['locale'])
 assert r['sourceKeySha256']==c['sourceKeySha256']==pr['sourceIdSha256']==br['sourceIdSha256']
 assert r['currentTargetSha256']==c['currentTargetSha256']==pr['currentTargetSha256']==br['currentTargetSha256']
 assert r['callerContextSha256']==c['sourceContextSha256']==pr['callerContextSha256']==br['callerContextSha256']
 assert r['callerCount']==c['callerCount']==pr['callerCount']==br['callerCount']
 assert r['sourceKey']==c['sourceKey'] and r['currentTarget']==c['currentTarget']
 pc=pr['proposedTarget'];bc=br['suggestedTarget']
 candidates=[]
 if pc is not None:candidates.append(('primary',pc,hs(pc)))
 if bc is not None:candidates.append(('independent-clean-blind',bc,hs(bc)))
 audit={(z['source'],z['target'],z['targetSha256']) for z in r['proposalResolution']}
 assert audit==set(candidates)
 selected=[z for z in r['proposalResolution'] if z['resolution']=='selected']
 if candidates:
  assert selected and all(z['target']==r['crossTarget'] for z in selected)
  assert r['crossDisposition'] in ('correction','refinement')
 else:
  assert r['crossDisposition']=='accept-current' and r['crossTarget']==c['currentTarget']
  assert not selected
 if pc is not None and bc is not None and pc!=bc:disagreements+=1
 if pc is None and bc is not None:blind_only+=1
 assert r['crossTargetSha256']==hs(r['crossTarget'])
 st=toks(c['sourceKey']);ct=toks(c['currentTarget']);ft=toks(r['crossTarget'])
 missing=[z for z in st['protectedLiterals'] if z not in ct['protectedLiterals']]
 assert r['protectedLiteralMismatch']==bool(missing)
 assert r['missingProtectedLiteralHashes']==[hs(z) for z in missing]
 assert r['currentTokenChecks']['sourceTokens']==st and r['currentTokenChecks']['currentTargetTokens']==ct
 assert r['crossTargetTokenChecks']['targetTokens']==ft
 for nm in ('placeholders','markupTags','numericTokens'):
  assert r['crossTargetTokenChecks'][{'placeholders':'placeholdersMatch','markupTags':'markupMatches','numericTokens':'numericTokensMatch'}[nm]]==(st[nm]==ft[nm])
 assert r['crossTargetTokenChecks']['protectedLiteralsMatch']==all(z in ft['protectedLiterals'] for z in st['protectedLiterals'])
 assert all(r['crossTargetTokenChecks'][k] for k in ('placeholdersMatch','markupMatches','numericTokensMatch','protectedLiteralsMatch'))
 cbad.update(missing);pbad+=not all(r['crossTargetTokenChecks'][k] for k in ('placeholdersMatch','markupMatches','numericTokensMatch','protectedLiteralsMatch'))
 counts[r['crossDisposition']]+=1
assert dict(counts)==summary['finalDispositionCounts'] and dict(cbad)=={'FTP':2}
assert pbad==0 and disagreements==3 and blind_only==3
assert summary['inputComparison']['differentTargetProposalCount']==3
assert summary['inputComparison']['blindOnlyProposalCount']==3 and summary['inputComparison']['primaryOnlyProposalCount']==0
before=j(R/'PR-attestation-before.json');after=j(R/'PR-attestation-after.json')
for a in (before,after):
 assert a['state']=='OPEN' and a['draft'] and a['head']==m['head'] and a['tree']==m['tree']
 assert a['branchRef']==a['pullRef']==m['head'] and a['deploymentsForHeadCount']==0 and a['repositoryDeploymentCount']==0
 assert a['deploymentActionsIssuedByReview']==0
for k in ('head','tree','headRef','branchRef','pullRef','baseRef','baseSha','mainRef','state','draft','deploymentsForHeadCount','deploymentsForHeadSha256','repositoryDeploymentCount','repositoryDeploymentsSha256'):assert before[k]==after[k]
prior=j(R/'prior-continuity-hash-summary.json')
assert prior['olderCarryForwardHolds']['recordCount']==35 and prior['olderCarryForwardHolds']['unchangedCount']==35
print(json.dumps({'result':'PASS','head':m['head'],'tree':m['tree'],'cells':len(x),'finalDispositionCounts':dict(sorted(counts.items())),
 'primaryProposals':pm['proposalCount'],'blindProposals':bm['proposalCount'],'targetTextDisagreementsResolved':disagreements,
 'blindOnlyProposalsResolved':blind_only,'currentProtectedMismatches':dict(cbad),'crossTargetTokenMismatches':pbad,
 'unresolvedHolds':summary['unresolvedHoldCount'],'refsStable':True,'deploymentsBeforeAfter':[0,0],'checksumFiles':len(sums)},indent=2))

