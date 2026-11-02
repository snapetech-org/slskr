#!/usr/bin/env python3
"""Verify the pinned 423–442 semantic review/application against catalogs and callers."""
import hashlib, json, re, subprocess
from collections import Counter
from pathlib import Path
BUNDLE=Path(__file__).resolve().parent
REPO=BUNDLE.parents[3]
BASE='98001f35f1cf33283190b96e60c3e65f01625929'
BASETREE='44280b39a053203e711d31503cf4552e23e09f8b'
SOURCE='7ff454828398de6a3cfb72fe7f0ed21fe419425b'
SOURCETREE='9e9f2aa743c4ff3236af8f99619803bdc3a37152'
LOCALES=['ar','de','es','fr','hi','id','ja','ko','pt-BR','vi','zh-Hans','zh-Hant']
def sha(b): return hashlib.sha256(b).hexdigest()
def git(*args,raw=False):
 b=subprocess.check_output(['git',*args],cwd=REPO)
 return b if raw else b.decode().strip()
def valsha(v): return sha(v.encode() if isinstance(v,str) else json.dumps(v,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode())
def populated(v):
 return (isinstance(v,str) and bool(v.strip())) or (isinstance(v,dict) and bool(v) and all(isinstance(x,str) and x.strip() for x in v.values()))
def jsonl(name): return [json.loads(x) for x in (BUNDLE/name).read_text().splitlines() if x.strip()]
assert git('rev-parse',f'{BASE}^{{tree}}')==BASETREE
assert git('rev-parse',f'{SOURCE}^{{tree}}')==SOURCETREE
inventory=[json.loads(x) for x in (BUNDLE/'source-inventory.jsonl').read_text().splitlines() if x.strip()]
ids=sorted({r['source_id'] for r in inventory})
assert len(ids)==5437
catalog_ids=list(json.loads(git('show',f'{BASE}:web/src/lib/locales/ui-labels.ar.json')).keys())
assert len(catalog_ids)==5437 and set(catalog_ids)==set(ids)
selection=jsonl('selection.jsonl'); audit=jsonl('reviewed-cell-audit.jsonl'); applied=jsonl('applied-corrections.jsonl'); accepted=jsonl('accepted-dispositions.jsonl')
root=jsonl('root-disposition-ledger.jsonl'); candidates=jsonl('candidate-plan.jsonl'); candidate_review=jsonl('candidate-review-input.jsonl'); provisional=jsonl('candidate-cell-audit.jsonl')
assert len(selection)==len(audit)==len(candidate_review)==240 and len(applied)==len(root)==len(candidates)==len(provisional)==32 and len(accepted)==208
assert sha((BUNDLE/'source-inventory.jsonl').read_bytes())=='dd5959b45ec3a7002806b3b03a8d434cb791cc737d2afe1554d24351eac6f313'
assert sha((BUNDLE/'candidate-plan.jsonl').read_bytes())=='fd70f76933cfa5d719360d07c7576f847e76c1da809ed9a8e619ef548d7d4d37'
assert sha((BUNDLE/'candidate-review-input.jsonl').read_bytes())=='c68844048a55fb0972c6b816689f0559af7408352952824e094ec5befe0f483d'
assert sha((BUNDLE/'caller-pins.json').read_bytes())=='06c1d278725685f323f24aa5c0579b31202a185c4e4b2d664dc01658ab1e9a87'
assert sha((BUNDLE/'root-disposition-ledger.jsonl').read_bytes())=='fadf1cbb42b6115dfb71ffe35d66916212c8d793527d146767ae6cfc9ff7a334'
assert sha((BUNDLE/'prior-evidence-scan-manifest.jsonl').read_bytes())=='e1f0de2401ec856cbb7869b0a706c97c2edc8d793640d7ee2b0ef332324034bf'
# Window source keys and all 240 source/current-cell pins.
bycell={(r['source_id'],r['locale']):r for r in audit}
assert len(bycell)==240
accepted_by={(r['source_id'],r['locale']):r for r in accepted}
applied_by={(r['source_id'],r['locale']):r for r in applied}
assert len(accepted_by)==208 and len(applied_by)==32 and accepted_by.keys().isdisjoint(applied_by.keys())
for k,r in accepted_by.items():
 cell=bycell[k]
 assert r['status']=='accepted' and r['target_text']==cell['final_target'] and r['target_sha256']==cell['final_target_sha256']
 assert r['source_sha256']==cell['source_sha256'] and r['review_head']==BASE and r['review_tree']==BASETREE
for k,r in applied_by.items():
 cell=bycell[k]
 assert r['status']=='corrected' and r['target_text']==cell['final_target'] and r['target_sha256']==cell['final_target_sha256']
 assert r['baseline_target_text']==cell['baseline_target'] and r['baseline_target_sha256']==cell['baseline_target_sha256']
for idx in range(423,443):
 sid=ids[idx]
 for loc in LOCALES:
  r=bycell[(sid,loc)]
  assert r['source_index']==idx and r['source_id']==sid and r['locale']==loc
  assert r['source_sha256']==sha(sid.encode()) and r['source_head']==SOURCE and r['source_tree']==SOURCETREE
  assert r['placeholder_set']==[]
  assert r['final_target'] and r['final_target_sha256']==valsha(r['final_target'])
  if sid=='Avg RTT': assert 'RTT' in r['final_target'] or (loc=='hi' and 'आरटीटी' in r['final_target'])
# Candidate and independent root disposition records are exact one-to-one.
root_by={(r['sourceId'],r['locale']):r for r in root}; cand_by={(r['source_id'],r['locale']):r for r in candidates}
assert root_by.keys()==cand_by.keys() and len(root_by)==32
for k,rr in root_by.items():
 r=bycell[k]; c=cand_by[k]
 assert rr['disposition']=='accept' and rr['nativeSpeakerApproved'] is False
 assert rr['prHead']==BASE and rr['prTree']==BASETREE and rr['sourceHead']==SOURCE and rr['sourceTree']==SOURCETREE
 assert rr['currentText']==r['baseline_target'] and rr['currentTargetSha256']==r['baseline_target_sha256']
 assert rr['finalText']==r['final_target'] and rr['finalTargetSha256']==r['final_target_sha256']
 assert rr['candidatePlanSha256']==sha((BUNDLE/'candidate-plan.jsonl').read_bytes())
 assert rr['reviewInputSha256']==sha((BUNDLE/'candidate-review-input.jsonl').read_bytes())
 assert c['current_text']==r['baseline_target'] and c['current_target_sha256']==r['baseline_target_sha256']
 assert c['proposed_text']==r['final_target'] and c['proposed_target_sha256']==r['final_target_sha256']
# Current 12 catalogs: complete parity/population and exact diff set from baseline.
loaded={}; filehashes={}; changed=[]
for loc in LOCALES:
 p=f'web/src/lib/locales/ui-labels.{loc}.json'
 raw=(REPO/p).read_bytes(); cat=json.loads(raw.decode()); filehashes[p]=sha(raw); loaded[loc]=cat
 assert len(cat)==5437 and list(cat.keys())==catalog_ids
 assert all(populated(v) for v in cat.values())
 base=json.loads(git('show',f'{BASE}:{p}'))
 assert list(base.keys())==list(cat.keys())
 changed.extend((sid,loc) for sid in ids if base[sid]!=cat[sid])
 for sid in ids[423:443]:
  r=bycell[(sid,loc)]; assert cat[sid]==r['final_target'] and valsha(cat[sid])==r['final_target_sha256']
  assert valsha(base[sid])==r['baseline_target_sha256']
  assert base[sid]==r['baseline_target']
assert set(changed)==set(root_by) and len(changed)==32
assert Counter(loc for _,loc in changed)==Counter({loc:sum(1 for r in applied if r['locale']==loc) for loc in LOCALES})
# Exact caller blob hashes and cited source lines are pinned for the full 240-cell window.
pins=json.loads((BUNDLE/'caller-pins.json').read_text())['pins']
assert pins and len(pins)==20
caller_files=set()
for sid,pins_for_key in pins.items():
 assert sid in ids[423:443] and pins_for_key
 for p in pins_for_key:
  caller_files.add(p['path'])
  blob=git('show',f'{SOURCE}:{p["path"]}',raw=True); assert sha(blob)==p['sha256']
  lines=blob.decode().splitlines()
  for occ in p['occurrences']:
   assert lines[occ['line']-1].strip()==occ['text']
   assert sid in occ['text'] and occ['text'].find(sid)>=0
# All catalog-only changes and evidence are whitespace-clean.
diffpaths=set(git('diff','--name-only',BASE).splitlines())
allowed={f'web/src/lib/locales/ui-labels.{loc}.json' for loc in LOCALES}
bundle_prefix='docs/pr-evidence/pr204-semantic-review-2026-11-01/independent-0423-0442-all-12-locales/'
scan_prefix='docs/localization/pr204-exact-current-scan-2026-11-01/'
assert all(path in allowed or path.startswith(bundle_prefix) or path.startswith(scan_prefix) for path in diffpaths)
subprocess.check_call(['git','diff','--check',BASE],cwd=REPO,stdout=subprocess.DEVNULL)
report={
 'result':'PASS','window':'423-442','prBaselineHead':BASE,'prBaselineTree':BASETREE,
 'sourceHead':SOURCE,'sourceTree':SOURCETREE,'sourceInventoryCount':len(ids),
 'reviewedCells':len(audit),'rootAcceptedCandidates':len(root),'appliedCorrections':len(applied),'acceptedUnchanged':len(accepted),
 'dispositions':dict(Counter(r['disposition'] for r in audit)),
 'changedByPriorDisposition':dict(Counter(r['prior_disposition'] for r in applied)),
 'changedCellsByLocale':dict(Counter(loc for _,loc in changed)),
 'catalogKeyOrderAndParity':'passed','catalogPopulatedCountEachLocale':5437,
 'changedCatalogs':len([loc for loc in LOCALES if any(l==loc for _,l in changed)]),
 'catalogFileSha256':filehashes,'exactTargetHashChecks':'passed','placeholderChecks':'passed',
 'protectedLiteralChecks':'passed (RTT preserved or transliterated as आरटीटी)','callerFiles':len(caller_files),
 'callerSourceLineOccurrences':sum(len(f['occurrences']) for entries in pins.values() for f in entries),
 'callerBlobHashesAndCitedLines':'passed','rootCrossReview':'32 accept, 0 refine, 0 keep, 0 hold',
 'gitDiffCheck':'passed','workflowChanges':0,'testsBuildsCIReleasesTagsRun':False,'nativeSpeakerApproved':False
}
print(json.dumps(report,ensure_ascii=False,indent=2))
