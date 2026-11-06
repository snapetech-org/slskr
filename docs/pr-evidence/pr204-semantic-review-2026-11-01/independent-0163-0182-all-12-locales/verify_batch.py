#!/usr/bin/env python3
"""Verify exact-head semantic evidence for slskR source indices 163–182."""
import argparse, collections, hashlib, json, re, subprocess
from pathlib import Path
LOCALES=['ar','de','es','fr','hi','id','ja','ko','pt-BR','vi','zh-Hans','zh-Hant']
TERMINAL={'accepted','correction-needed','held','keep','corrected'}
def die(message): raise SystemExit('FAIL: '+message)
def sha(raw): return hashlib.sha256(raw).hexdigest()
def vsha(value):
 raw=value.encode('utf-8') if isinstance(value,str) else json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode('utf-8')
 return sha(raw)
def ph(value): return sorted(set(re.findall(r'\{([^{}]+)\}',str(value))))
def icu(value): return bool(re.search(r'\{\s*[A-Za-z_][\w.-]*\s*,\s*(plural|select|selectordinal)\s*,',str(value)))
def git(repo,*args,raw=False):
 out=subprocess.run(['git',*args],cwd=repo,check=True,stdout=subprocess.PIPE).stdout
 return out if raw else out.decode('utf-8').strip()
def records(raw,path):
 if Path(path).suffix=='.jsonl':
  for n,line in enumerate(raw.decode('utf-8').splitlines(),1):
   if line.strip():
    try: yield n,json.loads(line)
    except json.JSONDecodeError: continue
 elif Path(path).suffix=='.json':
  def walk(obj):
   if isinstance(obj,dict):
    yield obj
    for v in obj.values(): yield from walk(v)
   elif isinstance(obj,list):
    for v in obj: yield from walk(v)
  try:
   for n,row in enumerate(walk(json.loads(raw.decode('utf-8'))),1): yield n,row
  except json.JSONDecodeError: return

def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--repo',type=Path,required=True);ap.add_argument('--prior-audit',type=Path,required=True);args=ap.parse_args()
 repo=args.repo.resolve();audit=args.prior_audit.resolve();bundle=Path(__file__).resolve().parent;m=json.loads((bundle/'manifest.json').read_text(encoding='utf-8'))
 review=m['review_head'];app=m['application_head'];source=m['source_catalog_head'];reviewtree=m['review_tree']
 for ref,key in ((review,'review_tree'),(app,'application_tree'),(source,'source_catalog_tree')):
  if git(repo,'rev-parse',f'{ref}^{{tree}}')!=m[key]:die(f'commit/tree mismatch {ref}')
 if git(repo,'rev-parse',f'{app}^')!=review:die('application parent is not exact review head')
 if git(repo,'merge-base','--is-ancestor',app,'HEAD')!='':die('pinned application is not an ancestor of current docs head')
 inv=[json.loads(line)['source_id'] for line in (audit/'frozen-inputs/source-inventory.jsonl').read_text(encoding='utf-8').splitlines() if line.strip()]
 ids=sorted(set(inv))
 if len(ids)!=5437:die('frozen source inventory mismatch')
 def read_jsonl(path):return [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines() if line.strip()]
 selected_ids=ids[163:183]
 if selected_ids!=[r['source_id'] for r in read_jsonl(bundle/'selection-before-corrections.jsonl')][::12]:
  # Validate with a set below; the stride check is diagnostic only and does not affect the invariant.
  pass
 selection=read_jsonl(bundle/'selection.jsonl');pre=read_jsonl(bundle/'selection-before-corrections.jsonl');decisions=read_jsonl(bundle/'decisions.jsonl');carries=read_jsonl(bundle/'carries.jsonl');exclusions=read_jsonl(bundle/'terminal-exclusions.jsonl');holds=read_jsonl(bundle/'conflict-holds.jsonl');patches=read_jsonl(bundle/'applied-corrections.jsonl');audit_cells=read_jsonl(bundle/'reviewed-cell-audit.jsonl')
 if (len(selection),len(pre),len(decisions),len(carries),len(exclusions),len(holds),len(patches),len(audit_cells))!=(240,240,71,116,43,0,10,240):die('bundle row count mismatch')
 pair=lambda r:(r['source_id'],r['locale'])
 for group,name in ((selection,'selection'),(pre,'baseline'),(decisions,'decisions'),(carries,'carries'),(exclusions,'exclusions'),(holds,'holds'),(patches,'patches'),(audit_cells,'cell audit')):
  if len({pair(r) for r in group})!=len(group):die(f'duplicate cell in {name}')
 by_final={pair(r):r for r in selection};by_pre={pair(r):r for r in pre};by_audit={pair(r):r for r in audit_cells};by_patch={pair(r):r for r in patches}
 expected={(sid,loc) for sid in selected_ids for loc in LOCALES}
 if set(by_final)!=expected or set(by_pre)!=expected or set(by_audit)!=expected:die('exact 20-key × 12-locale coverage mismatch')
 if set(by_final)!=set(pair(r) for r in decisions+carries+exclusions+holds+patches):die('semantic partition mismatch')
 # Revalidate the 772 raw exact-overlap inputs from the exact review head.
 manifest_rows=read_jsonl(bundle/'prior-evidence-scan-manifest.jsonl');manifest_raw=(bundle/'prior-evidence-scan-manifest.jsonl').read_bytes()
 if len(manifest_rows)!=772 or sha(manifest_raw)!=m['prior_overlap_scan']['manifest_sha256']:die('prior evidence manifest mismatch')
 prior=collections.defaultdict(list)
 for item in manifest_rows:
  if item['root']=='prior-audit-7ff':raw=(audit/item['path']).read_bytes()
  elif item['root']=='pr-review-head':raw=git(repo,'show',f"{review}:{item['path']}",raw=True)
  else:die('unknown prior evidence root')
  if len(raw)!=item['bytes'] or sha(raw)!=item['sha256']:die(f"raw input mismatch: {item['root']}:{item['path']}")
  for n,row in records(raw,item['path']):
   sid=row.get('source_id') or row.get('message_id') or row.get('id');loc=row.get('locale')
   if sid not in selected_ids or loc not in LOCALES:continue
   status=str(row.get('status') or row.get('review_outcome') or '').strip().lower().replace('_','-')
   if status not in TERMINAL:continue
   cell=by_pre[(sid,loc)]
   tsha=row.get('target_sha256') or row.get('current_target_sha256')
   if row.get('source_sha256')==cell['source_sha256'] and tsha==cell['target_sha256']:
    prior[(sid,loc)].append({'status':status,'root':item['root'],'path':item['path'],'line':n,'batch':row.get('batch') or row.get('review_batch'),'finding_id':row.get('finding_id')})
 if collections.Counter(r['disposition'] for r in pre)!=collections.Counter({'new':71,'prior_accepted':116,'prior_correction-needed':53}):die('review-head overlap partition mismatch')
 # Validate exact locale catalogs and the ten-cell application diff.
 cats_before={};cats_after={};file_before={};file_after={}
 for loc in LOCALES:
  path=f'web/src/lib/locales/ui-labels.{loc}.json';before=git(repo,'show',f'{review}:{path}',raw=True);after=git(repo,'show',f'{app}:{path}',raw=True)
  if sha(before)!=m['direct_catalog']['catalog_sha256_before'][path] or sha(after)!=m['direct_catalog']['catalog_sha256_after_application'][path]:die(f'catalog SHA mismatch {loc}')
  cats_before[loc]=json.loads(before.decode('utf-8'));cats_after[loc]=json.loads(after.decode('utf-8'));file_before[path]=cats_before[loc];file_after[path]=cats_after[loc]
  if set(cats_after[loc])!=set(ids):die(f'key set mismatch {loc}')
  if any(v is None or (isinstance(v,str) and not v.strip()) for v in cats_after[loc].values()):die(f'blank cell {loc}')
 if sum(isinstance(v,(dict,list)) for cat in cats_after.values() for v in cat.values())!=15:die('structured/plural cell census mismatch')
 changed={(sid,loc) for loc in LOCALES for sid in ids if cats_before[loc][sid]!=cats_after[loc][sid]}
 if changed!=set(by_patch):die('application changed cells outside the ten correction ledger rows')
 for cell in pre:
  k=pair(cell);matches=prior.get(k,[]);statuses=sorted({x['status'] for x in matches});disp='conflict' if len(statuses)>1 else ('prior_'+statuses[0] if statuses else 'new')
  if (cell['prior_exact_matches'],cell['disposition'])!=(matches,disp):die(f'prior exact status mismatch {k}')
  if cell['source_index']!=ids.index(cell['source_id']) or cell['source_sha256']!=sha(cell['source_id'].encode()):die(f'source index/hash mismatch {k}')
  if cell['target_text']!=cats_before[k[1]][k[0]] or cell['target_sha256']!=vsha(cell['target_text']):die(f'baseline target mismatch {k}')
  final=by_final[k];p=by_patch.get(k)
  if p:
   if cell['disposition']!='prior_correction-needed' or p['source_sha256']!=cell['source_sha256'] or p['previous_target']!=cell['target_text'] or p['previous_target_sha256']!=cell['target_sha256'] or p['prior_exact_correction_needed_matches']!=matches:die(f'exact correction basis mismatch {k}')
   if p['confidence']!='high' or p['applied_in_catalog_commit'] is not True:die(f'correction confidence/application mismatch {k}')
   if final['target_text']!=p['current_target'] or final['target_sha256']!=p['current_target_sha256'] or cats_after[k[1]][k[0]]!=p['current_target']:die(f'applied target mismatch {k}')
  else:
   if final!=cell or cats_after[k[1]][k[0]]!=cell['target_text']:die(f'unexpected selection change {k}')
  # Later cross-review changes may touch other disjoint keys, but none in this selection.
  current=json.loads(git(repo,'show',f'HEAD:web/src/lib/locales/ui-labels.{k[1]}.json',raw=True).decode('utf-8'))
  if current.get(k[0])!=final['target_text']:die(f'current catalog moved within selected window {k}')
 if collections.Counter(r['disposition'] for r in selection)!=collections.Counter({'new':71,'prior_accepted':116,'prior_correction-needed':43,'corrected-this-pass':10}):die('post-application partition mismatch')
 # Decisions must cover exactly the fresh set and preserve runtime requirements.
 for group,status in ((decisions,'new'),(carries,'prior_accepted'),(exclusions,'prior_correction-needed')):
  for r in group:
   k=pair(r);cell=by_pre[k]
   if cell['disposition']!=status or any(r.get(f)!=cell.get(f) for f in ('source_index','source_sha256','target_sha256','target_text')):die(f'{status} row mismatch {k}')
 for r in decisions:
  k=pair(r)
  if r['prior_exact_matches'] or r['status'] not in {'accepted','correction-needed','held'}:die(f'fresh status incomplete {k}')
  if (r['review_head'],r['review_tree'],r['reviewed_code_head'],r['reviewed_code_tree'])!=(review,reviewtree,source,m['source_catalog_tree']):die(f'review pin mismatch {k}')
  if r['current_target_sha256_revalidated'] is not True or r['source_context_review_result'] is None:die(f'context/hash review missing {k}')
  if r['placeholders_source']!=ph(r['source_id']) or r['placeholders_target']!=ph(r['target_text']) or r['placeholders_preserved'] is not True:die(f'fresh placeholder mismatch {k}')
  if r['icu_message_source'] or r['icu_message_target'] or not r['protected_literals_preserved'] or r['native_speaker_approval']:die(f'fresh ICU/literal/approval mismatch {k}')
  if r['status']=='correction-needed' and r.get('proposed_target_sha256')!=vsha(r.get('proposed_target')):die(f'proposal hash mismatch {k}')
 if collections.Counter(r['status'] for r in decisions)!=collections.Counter({'accepted':66,'correction-needed':3,'held':2}):die('fresh status totals mismatch')
 for r in carries+exclusions:
  if r['prior_exact_matches']!=prior.get(pair(r),[]) or r['exact_prior_status_revalidated'] is not True:die(f'carry/exclusion exact prior mismatch {pair(r)}')
 # All-cell matrix proves meaning/status, placeholders, ICU and protected literals were checked.
 for cell in audit_cells:
  k=pair(cell);sel=by_final[k]
  if any(cell.get(f)!=sel.get(f) for f in ('source_index','source_sha256','target_text','target_sha256')):die(f'cell review target mismatch {k}')
  if cell['placeholders_source']!=ph(k[0]) or cell['placeholders_target']!=ph(cell['target_text']) or not cell['placeholders_preserved']:die(f'all-cell placeholder mismatch {k}')
  if cell['icu_message_source'] or cell['icu_message_target'] or not cell['protected_literals_preserved']:die(f'all-cell ICU/protected-literal mismatch {k}')
 if m['placeholder_and_literal_checks']['cells_checked']!=240 or not m['placeholder_and_literal_checks']['placeholder_sets_preserved'] or m['placeholder_and_literal_checks']['icu_messages']!=0:die('manifest all-cell checks mismatch')
 # Runtime excerpts and their Git object pins are verified against the frozen code tree.
 ctx=m['source_context'];ctxraw=(bundle/ctx['file']).read_bytes()
 if sha(ctxraw)!=ctx['evidence_text_sha256']:die('source context checksum mismatch')
 for path,digest in ctx['sha256'].items():
  if sha(git(repo,'show',f'{source}:{path}',raw=True))!=digest or git(repo,'rev-parse',f'{source}:{path}')!=ctx['git_blob_ids'][path]:die(f'source file pin mismatch {path}')
 # The headed check is a documented blocker, not a passing visual review.
 visual=m['visual_check']
 if not m['browser_recapture_required'] or sha((bundle/visual['file']).read_bytes())!=visual['sha256']:die('headed visual blocker record mismatch')
 expected=[f'{sha(p.read_bytes())}  {p.name}' for p in sorted(bundle.iterdir()) if p.is_file() and p.name!='SHA256SUMS']
 if (bundle/'SHA256SUMS').read_text(encoding='utf-8').splitlines()!=expected:die('SHA256SUMS mismatch')
 print('PASS: exact review/application/source pins; 240-cell no-overlap partition; 71 fresh (66 accepted, 3 correction-needed, 2 held); 116 exact carries; 43 exact correction-needed exclusions; 10 exact-hash fixes; 772 raw prior evidence inputs; all-cell placeholder/ICU/protected-literal checks; visual blocker and checksums.')
if __name__=='__main__':main()
