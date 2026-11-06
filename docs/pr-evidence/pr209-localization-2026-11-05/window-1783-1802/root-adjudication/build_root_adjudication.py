#!/usr/bin/env python3
from __future__ import annotations
import collections, hashlib, json, subprocess
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE
BASE=HERE.parent
CROSS=BASE/'cross-review'
CANDIDATE=BASE/'candidate-free-input'
PRIMARY=BASE/'primary-review'
BLIND=BASE/'blind-review'

def sha(v): return hashlib.sha256(v.encode('utf-8') if isinstance(v,str) else v).hexdigest()
def read_rows(p): return [json.loads(s) for s in p.read_text(encoding='utf-8').splitlines() if s.strip()]
def write_rows(p,rs): p.parent.mkdir(parents=True,exist_ok=True); p.write_text(''.join(json.dumps(x,ensure_ascii=False,sort_keys=True)+'\n' for x in rs),encoding='utf-8')
def git(repo,*args): return subprocess.check_output(['git',*args],cwd=repo,text=True).strip()
def main():
 import argparse
 ap=argparse.ArgumentParser(); ap.add_argument('--repo',required=True,type=Path); a=ap.parse_args(); repo=a.repo.resolve()
 manifest=json.loads((CROSS/'manifest.json').read_text(encoding='utf-8'))
 head=manifest['head']; tree=manifest['tree']
 if git(repo,'rev-parse','HEAD')!=head or git(repo,'rev-parse','HEAD^{tree}')!=tree: raise SystemExit('input head/tree mismatch')
 if git(repo,'status','--porcelain'): raise SystemExit('input worktree must be clean')
 rows=read_rows(CROSS/'integrated-cross-ledger.jsonl')
 if len(rows)!=240 or len({(r['position'],r['locale']) for r in rows})!=240: raise SystemExit('unexpected review coverage')
 counts=collections.Counter(); ledger=[]; selected=[]; baseline={}; hold_ids=[]
 for r in rows:
  a=r['adjudication']; s=r['source']; c=r['current']; pr=r['reviews']['primary']; bl=r['reviews']['blind']
  if r['head']!=head or r['tree']!=tree: raise SystemExit('cell pin mismatch')
  if sha(s['text'])!=s['sha256'] or sha(c['text'])!=c['sha256']: raise SystemExit('source/current hash mismatch')
  if a['selectedTargetSha256']!=sha(a['selectedTarget']): raise SystemExit('selected target hash mismatch')
  if any(a['selectedTokenAudit'][k] is not True for k in ('markupMatches','numericTokensMatch','placeholderSequenceMatches','protectedLiteralsMatch')): raise SystemExit(f"selected token mismatch {r['position']}::{r['locale']}")
  crossdisp=a['disposition']
  if crossdisp=='accept_current': target=c['text']; disp='accept-current'; origin='current'
  elif crossdisp in ('correction','refinement'): target=a['selectedTarget']; disp=crossdisp; origin=a['targetOrigin']
  elif crossdisp=='hold': target=c['text']; disp='hold'; origin='current'; hold_ids.append(f"{r['position']}::{r['locale']}")
  else: raise SystemExit(f'unsupported disposition {crossdisp}')
  target_sha=sha(target)
  if disp!='hold' and target_sha!=a['selectedTargetSha256']: raise SystemExit(f"selection disagrees with integrated review {r['position']}::{r['locale']}")
  if disp=='hold' and target_sha!=c['sha256']: raise SystemExit('held target changed')
  if disp=='accept-current' and target!=c['text']: raise SystemExit('accept-current changed text')
  if disp in ('correction','refinement') and target==c['text']: raise SystemExit('selected edit is a no-op')
  if disp=='hold' and target!=c['text']: raise SystemExit('held text changed')
  path=c['catalogPath']; raw=subprocess.check_output(['git','show',f'{head}:{path}'],cwd=repo)
  fh=sha(raw)
  if fh!=c['catalogFileSha256']: raise SystemExit(f'catalog pin mismatch {path}')
  baseline[path]=fh
  row={
    'position':r['position'],'locale':r['locale'],'cellId':f"{r['position']}::{r['locale']}",
    'catalogPath':path,'catalogFileSha256':fh,'sourceKey':s['text'],'sourceKeySha256':s['sha256'],
    'sourceContextSha256':s.get('callerContextSha256'),'callerReferenceCount':s.get('callerReferenceCount',0),
    'callerOccurrenceCount':s.get('callerOccurrenceCount',0),'before':c['text'],'beforeSha256':c['sha256'],
    'after':target,'afterSha256':target_sha,'crossDisposition':crossdisp,
    'crossSelectionSource':a['targetOrigin'],'crossTarget':a['selectedTarget'],
    'crossTargetSha256':a['selectedTargetSha256'],'primaryDecision':pr.get('disposition',pr.get('status')),
    'blindDecision':bl.get('status'),'primaryRationale':pr.get('rationale'),
    'blindRationale':bl.get('rationale'),'crossRationale':a['rationale'],
    'rootDisposition':disp,'rootTarget':target,'rootTargetSha256':target_sha,
    'rootOverrideApplied':False,'targetOrigin':origin,'confidence':'moderate',
    'rootAdjudicationPerformed':True,'rootRationale':(
      'Keep the current Korean wording unchanged on hold pending a locale-qualified decision on fold/collapse versus grouping terminology.'
      if disp=='hold' else
      'Retain the exact-head value because the integrated review accepts it and pinned source/caller evidence supports it.'
      if disp=='accept-current' else
      'Select the cross-reviewed wording after manual review of the source, production caller context, reviewer rationales, and token audit; this is provisional pending qualified native-speaker review.'
    ),
    'selectedTokenAudit':a['selectedTokenAudit'],'callerReferences':s.get('callerReferences',[]),
    'nativeSpeakerApproval':False
  }
  ledger.append(row); counts[disp]+=1
  if disp in ('correction','refinement'):
   selected.append({k:row[k] for k in ('position','locale','cellId','catalogPath','sourceKey','sourceKeySha256','before','beforeSha256','after','afterSha256','crossTarget','crossTargetSha256','crossDisposition','crossSelectionSource','rootDisposition','targetOrigin','rootOverrideApplied','rootRationale','confidence','sourceContextSha256','callerReferenceCount','callerOccurrenceCount','catalogFileSha256')})
  data=json.loads(raw.decode('utf-8'))
  if len(data)!=5441 or (json.dumps(data,ensure_ascii=False,indent=2)+'\n').encode('utf-8')!=raw: raise SystemExit(f'catalog shape mismatch {path}')
  if data.get(s['text'])!=c['text']: raise SystemExit(f"catalog value mismatch {row['cellId']}")
 if counts!=collections.Counter({'accept-current':183,'correction':55,'refinement':1,'hold':1}): raise SystemExit(f'unexpected counts: {counts}')
 if len(selected)!=56 or hold_ids!=['1792::ko']: raise SystemExit('unexpected selected/hold coverage')
 previous=read_rows(CANDIDATE/'active-hold-reattestation.jsonl')
 if len(previous)!=1: raise SystemExit('expected one carried active hold')
 old=previous[0]
 if old.get('holdId')!='1719::id' or old.get('textIncluded') is not False or old.get('targetHashUnchanged') is not True: raise SystemExit('prior hold not hash-only and unchanged')
 write_rows(ROOT/'root-final-review-ledger.jsonl',ledger)
 write_rows(ROOT/'root-selected-targets.jsonl',selected)
 write_rows(ROOT/'root-overrides.jsonl',[])
 summary={'result':'PASS_ROOT_ADJUDICATION','head':head,'tree':tree,'window':'W1783-W1802','cells':240,
  'dispositions':dict(counts),'selectedTargets':len(selected),'catalogs':len(baseline),'entriesPerCatalog':5441,
  'rootOverrides':0,'activeHolds':2,'currentWindowHold':'1792::ko','carriedPriorActiveHold':'1719::id',
  'priorHoldTextIncluded':False,'nativeSpeakerApproval':False,'headedBrowserAcceptance':False,
  'manualReview':'All 56 selected edits were read against source and pinned caller context; four blind locale flags were resolved provisionally, and Korean 1792::ko remains on hold.',
  'baselineCatalogSha256':baseline}
 (ROOT/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 att={'reviewHead':head,'reviewTree':tree,'candidateFreeChecksumsSha256':sha((CANDIDATE/'SHA256SUMS.txt').read_bytes()),
  'primaryChecksumsSha256':sha((PRIMARY/'SHA256SUMS.txt').read_bytes()),'blindChecksumsSha256':sha((BLIND/'SHA256SUMS.txt').read_bytes()),
  'integratedCrossChecksumsSha256':sha((CROSS/'SHA256SUMS.txt').read_bytes()),
  'integratedCrossLedgerSha256':sha((CROSS/'integrated-cross-ledger.jsonl').read_bytes()),'reviewedCells':240,
  'changedTargets':56,'unresolvedHold':'1792::ko; target retained at exact input hash','priorHold':'1719::id; hash-only and unchanged',
  'reviewerApproval':'No qualified native-speaker approval; no headed-browser acceptance',
  'agentSealedPacketChecksumsSha256':{'candidateFree':'dc7a5b5d8901d1d8b5168c7da966ba3769e6377b2be383c0946c18de8e422962','primary':'f4043d4d16786166d6e0f8d74dbab8111f4bf6a09644d9fc1e1a8bd2638372','blind':'4dfd942b6367eea65d270f6d199de5194e4fd95e95bdcf91a5234ebec0e5cde2','integratedCross':'a6d7d30ac8089f01ca5597b9f6d5f016d71a794838977ec8eee338c6a621469c'},
  'committedPortablePacketChecksumsSha256':{'candidateFree':sha((CANDIDATE/'SHA256SUMS.txt').read_bytes()),'primary':sha((PRIMARY/'SHA256SUMS.txt').read_bytes()),'blind':sha((BLIND/'SHA256SUMS.txt').read_bytes()),'integratedCross':sha((CROSS/'SHA256SUMS.txt').read_bytes())},
  'portablePaths':'Packet-local verifier and builder paths resolve from committed sibling directories; predecessor candidate-free input is committed under window-1763-1782/candidate-free.'}
 (ROOT/'input-attestation.json').write_text(json.dumps(att,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 notes=['# Root adjudication — slskR PR #209 W1783–W1802','',
  f"Input head/tree: `{head}` / `{tree}`.",'',
  'I manually reviewed all 56 selected cells against the exact English source, production caller context, primary and blind rationales, and protected-token audit. The integrated review selects 55 corrections and one refinement; 183 current values are retained. The Korean `1792::ko` value remains on hold at its existing hash because the fold/collapse versus grouping term needs locale-qualified resolution. Earlier `1719::id` remains hash-only and unchanged.', '',
  'No native-speaker approval or headed-browser acceptance is claimed. All selected translations remain provisional until qualified language review.', '',
  '## Selected edits', '']
 for x in selected: notes.append(f"- `{x['cellId']}` ({x['rootDisposition']}, {x['targetOrigin']}): `{x['after']}` — {x['rootRationale']}")
 (ROOT/'root-review-notes.md').write_text('\n'.join(notes)+'\n',encoding='utf-8')
 print(json.dumps(summary,ensure_ascii=False,indent=2))
if __name__=='__main__': main()
