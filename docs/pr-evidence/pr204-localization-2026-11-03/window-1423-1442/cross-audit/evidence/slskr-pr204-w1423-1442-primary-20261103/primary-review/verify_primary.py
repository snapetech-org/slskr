#!/usr/bin/env python3
import hashlib,json,re,sys
from pathlib import Path
root=Path(__file__).resolve().parent

def sha(b):return hashlib.sha256(b).hexdigest()
def check(ok,msg):
 if not ok:raise SystemExit('FAIL '+msg)
# Packet checksum manifest.
listed={}
for line in (root/'SHA256SUMS.txt').read_text().splitlines():
 if not line.strip():continue
 digest,name=line.split('  ',1);listed[name]=digest;p=root/name
 check(p.is_file() and sha(p.read_bytes())==digest,'checksum '+name)
check('SHA256SUMS.txt' not in listed,'checksum file self-hash')
cf=root/'evidence'/'candidate-free-input'
# Embedded input checksum validation.
for line in (cf/'SHA256SUMS.txt').read_text().splitlines():
 digest,name=line.split('  ',1);p=cf/name
 check(p.is_file() and sha(p.read_bytes())==digest,'candidate-free checksum '+name)
im=json.loads((cf/'manifest.json').read_text());m=json.loads((root/'manifest.json').read_text())
check(m['head']==im['head']=='7ca8589266ab4c5a925782a8726d7e57b4ed7427','head pin')
check(m['tree']==im['tree']=='09adcb271a2eb92770df4a20098dccc3fde2a59f','tree pin')
check(m['branch']==im['headRef']=='codex/slskr-l10n-audit-20261030','branch pin')
check(im['candidateFreeInputOnly'] and not im['proposedTranslationsIncluded'],'candidate-free boundary')
base={}
for line in (cf/'current-target-cells.jsonl').read_text().splitlines():
 d=json.loads(line);base[(d['position'],d['locale'])]=d
ledger=[json.loads(s) for s in (root/'cell-review.jsonl').read_text().splitlines()]
check(len(base)==len(ledger)==240,'cell count')
seen=set();counts={}
for d in ledger:
 k=(d['position'],d['locale']);check(k not in seen and k in base,'cell identity '+str(k));seen.add(k);b=base[k]
 for a,z in [('sourceKey','sourceKey'),('sourceKeySha256','sourceKeySha256'),('currentTarget','currentTarget'),('currentTargetSha256','currentTargetSha256'),('sourceContextSha256','sourceContextSha256'),('callerCount','callerCount'),('callerRefs','callerRefs')]:check(d[a]==b[z],a+' mismatch '+str(k))
 check(sha(d['currentTarget'].encode())==d['currentTargetSha256'],'current hash '+str(k))
 check(d['callerCount']>0,'callerless cell '+str(k))
 disp=d['disposition'];counts[disp]=counts.get(disp,0)+1;check(disp in ('accept-current','correction','refinement','hold'),'disposition '+str(k))
 t=d['tokenChecks'];
 check(t['currentChecksPass'],'current token checks '+str(k))
 check(sorted(t['sourcePlaceholders'])==sorted(t['currentPlaceholders']),'current placeholders '+str(k))
 check(sorted(t['sourceMarkupTags'])==sorted(t['currentMarkupTags']),'current markup '+str(k))
 check(sorted(t['sourceNumericTokens'])==sorted(t['currentNumericTokens']),'current numeric '+str(k))
 check(not t['currentMissingProtectedLiterals'],'current protected literals '+str(k))
 if d['proposedTarget'] is None:
  check(d['proposedTargetSha256'] is None and disp=='accept-current','no proposal '+str(k))
 else:
  check(disp in ('correction','refinement') and sha(d['proposedTarget'].encode())==d['proposedTargetSha256'],'proposal hash '+str(k))
  check(sorted(t['sourcePlaceholders'])==sorted(t['proposedPlaceholders']),'proposal placeholders '+str(k))
  check(sorted(t['sourceMarkupTags'])==sorted(t['proposedMarkupTags']),'proposal markup '+str(k))
  check(sorted(t['sourceNumericTokens'])==sorted(t['proposedNumericTokens']),'proposal numeric '+str(k))
  check(not t['proposedMissingProtectedLiterals'],'proposal protected literals '+str(k))
check(seen==set(base),'coverage')
check(counts==m['decisionCounts'],'decision counts')
changes=[d for d in ledger if d['proposedTarget'] is not None]
summary=json.loads((root/'change-summary.json').read_text())
check(len(changes)==summary['changeCount']==m['proposedTargetCount'],'change summary count')
check([(d['position'],d['locale'],d['currentTargetSha256'],d['proposedTargetSha256']) for d in summary['changes']]==[(d['position'],d['locale'],d['currentTargetSha256'],d['proposedTargetSha256']) for d in changes],'change summary exact hashes')
# Carried holds and prior selections are byte-for-byte copies of candidate-free evidence.
for name,count in [('prior-hold-reattestation.jsonl',35),('prior-selection-reattestation.jsonl',180)]:
 a=(root/name).read_bytes();b=(cf/name).read_bytes();check(a==b,'evidence copy '+name)
 rows=[json.loads(x) for x in a.decode().splitlines()];check(len(rows)==count,'evidence rows '+name)
 if name.startswith('prior-hold'):
  check(all(r['reattestation']=='same' and r['currentTargetSha256']==r['priorCurrentTargetSha256'] for r in rows),'carried hold hashes')
# Runtime/source evidence remains exact.
check((root/'source-context-notes.json').is_file(),'source context notes')
att=json.loads((root/'live-pr-attestation.json').read_text())
for stage in ('observedBefore','observedAfter'):
 o=att[stage];check(isinstance(o,dict),'live refs '+stage)
 check(o['state']=='OPEN' and o['isDraft'] is True and o['branch']==m['branch'] and o['head']==m['head'] and o['headTree']==m['tree'] and o['liveBranchRef']==m['head'] and o['livePullRef']==m['head'] and o['checkoutWorktreeClean'] and o['checkoutHead']==m['head'] and o['checkoutTree']==m['tree'],'live pin '+stage)
print('PASS primary W1423-W1442: 240 exact-hash cells; decisions '+json.dumps(counts,sort_keys=True)+'; 35 carried holds and 180 prior selection rows reattested; source callers and placeholder/markup/numeric/protected-literal checks pass; live PR OPEN/DRAFT refs pinned before/after.')
