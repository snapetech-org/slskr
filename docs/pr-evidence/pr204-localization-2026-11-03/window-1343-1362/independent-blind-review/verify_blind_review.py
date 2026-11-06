#!/usr/bin/env python3
from pathlib import Path
from collections import Counter
import hashlib,json,re
T=Path('/home/keith/Documents/code/task-scratch/slskr-pr204-w1343-1362-primary-20261103')
I=T/'input'; OUT=T/'blind-review'
PH=re.compile(r'\{[^{}\r\n]+\}'); MK=re.compile(r'</?[A-Za-z][^<>]*?/?>'); NUM=re.compile(r'(?<!\w)[+-]?\d+(?:[.,]\d+)?%?(?!\w)')
def sha(b): return hashlib.sha256(b).hexdigest()
def st(s): return sha(s.encode('utf-8'))
def j(p): return json.loads(p.read_text(encoding='utf-8'))
def jl(p): return [json.loads(x) for x in p.read_text(encoding='utf-8').splitlines() if x.strip()]
def check_sums(d):
 for line in (d/'SHA256SUMS.txt').read_text(encoding='utf-8').splitlines():
  if line.strip():
   h,n=line.split(None,1); n=n.strip().lstrip('*'); assert sha((d/n).read_bytes())==h,(n,'checksum')
check_sums(I); check_sums(OUT)
m=j(I/'manifest.json'); s=j(OUT/'summary.json'); p=j(OUT/'provenance.json')
assert m['candidateFreeInputOnly'] is True and m['proposedTranslationsIncluded'] is False
assert m['repository']=='snapetech-org/slskR' and m['pullRequest']==204
head=m['head']; tree=m['tree']; window='W1343-W1362'
assert m['selectedPositions']==[1343,1362] and m['sourceCount']==20 and m['localeCount']==12 and m['cellCount']==240
manifest_sha=sha((I/'manifest.json').read_bytes()); sums_sha=sha((I/'SHA256SUMS.txt').read_bytes())
assert (s['head'],p['head'])==(head,head) and (s['tree'],p['tree'])==(tree,tree)
assert s['window']==p['window']==window
assert s['candidateFreeInputManifestSha256']==p['candidateFreeInputManifestSha256']==manifest_sha
assert s['candidateFreeInputChecksumListSha256']==p['candidateFreeInputChecksumListSha256']==sums_sha
assert s['candidateFreeInputOnly'] is True and p['reviewType']=='blind candidate-free semantic review'
assert s['primaryReviewReadBeforeSeal'] is False and p['primaryReviewReadBeforeSeal'] is False
assert p['repoOrPrEditsMade'] is False and s['nativeSpeakerApproval'] is False and s['exactHeadBrowserReview'] is False
assert s['allCellsIndependentlyReviewed'] is True and s['sourceCallerContextUsed'] is True
assert s['catalogSourceAdditionsNeededForThisWindow'] is False
queue={x['position']:x for x in jl(I/'source-queue.jsonl')}; callers={x['position']:x for x in jl(I/'source-contexts.jsonl')}
cells=jl(I/'current-target-cells.jsonl'); inputs={(x['position'],x['locale']):x for x in cells}
ledger=jl(OUT/'blind-ledger.jsonl'); selected=jl(OUT/'selected-direct-locale-cells.jsonl')
assert len(inputs)==len(ledger)==240 and len(queue)==5441
bykey={(x['position'],x['locale']):x for x in ledger}; assert len(bykey)==240 and set(bykey)==set(inputs)
sel={(x['position'],x['locale']):x for x in selected}; assert len(sel)==len(selected)
counts=Counter(x['disposition'] for x in ledger)
assert dict(counts)==s['dispositions'] and counts['hold']==s['holds']==0
assert len(selected)==s['proposedChanges']==counts['correction']+counts['refinement']
assert s['sourceIds']==20 and s['locales']==12 and s['cells']==240
assert s['candidateFreeBaselineMismatchCounts']==m['mismatchCounts']
for key,row in bykey.items():
 inp=inputs[key]; src=queue[key[0]]; caller=callers[key[0]]
 assert row['head']==head and row['tree']==tree and row['reviewStatus']=='blind-reviewed'
 assert row['sourceKey']==src['sourceKey']==inp['sourceKey'] and row['sourceKeySha256']==src['sourceKeySha256']==inp['sourceKeySha256']
 for field in ['currentTarget','currentTargetSha256','catalogPath','catalogGitBlob','catalogFileSha256','catalogKeyCount','sourceContextSha256','callerOccurrenceCount']:
  expected={'sourceContextSha256':caller['callerContextSha256'],'callerOccurrenceCount':caller['callerOccurrenceCount']}.get(field,inp.get(field))
  assert row[field]==expected,(key,field,row[field],expected)
 assert row['callerOccurrenceCount']==caller['productionCallerCount']>0
 assert row['callerReferences']==[{'path':c['path'],'line':c['line'],'fileSha256':c['fileSha256'],'gitBlob':c['gitBlob'],'lineSha256':c['lineSha256'],'contextSha256':c['contextSha256']} for c in caller['callers']]
 assert row['rationale'].strip() and row['confidence'] in {'high','moderate','low'}
 final=row['finalTarget']; assert row['finalTargetSha256']==st(final)
 assert PH.findall(final)==PH.findall(src['sourceKey'])==row['tokenChecks']['finalTargetPlaceholders']
 assert MK.findall(final)==MK.findall(src['sourceKey'])==row['tokenChecks']['finalTargetMarkupTags']
 assert NUM.findall(final)==NUM.findall(src['sourceKey'])==row['tokenChecks']['finalTargetNumericTokens']
 assert all(x in final for x in inp['sourceProtectedLiterals']) and row['tokenChecks']['finalTargetPreservesProtectedLiterals'] is True
 if row['disposition']=='accept-current':
  assert final==inp['currentTarget'] and key not in sel and 'proposedTarget' not in row
 else:
  assert key in sel and row['proposedTarget']==final and row['proposedTargetSha256']==st(final)
  x=sel[key]
  assert x['proposedTarget']==final and x['proposedTargetSha256']==st(final)
  assert x['rationale']==row['rationale'] and x['disposition']==row['disposition']
assert set(sel)=={k for k,v in bykey.items() if v['disposition']!='accept-current'}
assert s['proposedChangesByPosition']==dict(Counter(str(x['position']) for x in selected))
assert s['proposedChangesByLocale']==dict(Counter(x['locale'] for x in selected))
listed={line.split(None,1)[1].strip().lstrip('*') for line in (OUT/'SHA256SUMS.txt').read_text().splitlines() if line.strip()}
assert listed=={x.name for x in OUT.iterdir() if x.is_file() and x.name!='SHA256SUMS.txt'}
print(json.dumps({'result':'PASS','head':head,'tree':tree,'window':window,'cells':240,'dispositions':dict(counts),'proposedChanges':len(selected),'holds':counts['hold'],'candidateFreeInputManifestSha256':manifest_sha,'candidateFreeInputChecksumListSha256':sums_sha,'blindChecksumListSha256':sha((OUT/'SHA256SUMS.txt').read_bytes()),'primaryReviewReadBeforeSeal':False},ensure_ascii=False,indent=2))
