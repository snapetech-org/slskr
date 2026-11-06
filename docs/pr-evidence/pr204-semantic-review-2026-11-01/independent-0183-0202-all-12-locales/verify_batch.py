#!/usr/bin/env python3
"""Verify exact-head semantic evidence for slskR source indices 183–202."""
import argparse, collections, hashlib, json, re, subprocess
from pathlib import Path
LOCALES=['ar','de','es','fr','hi','id','ja','ko','pt-BR','vi','zh-Hans','zh-Hant']
TERMINAL={'accepted','correction-needed','held','keep','corrected'}
def die(message): raise SystemExit('FAIL: '+message)
def sha(raw): return hashlib.sha256(raw).hexdigest()
def canonical(value):
 return value.encode('utf-8') if isinstance(value,str) else json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode('utf-8')
def vsha(value): return sha(canonical(value))
def flat(value):
 if isinstance(value,dict): return ' '.join(flat(v) for v in value.values())
 if isinstance(value,list): return ' '.join(flat(v) for v in value)
 return str(value)
def ph(value): return sorted(set(re.findall(r'\{([^{}]+)\}',flat(value))))
def icu(value): return bool(re.search(r'\{\s*[A-Za-z_][\w.-]*\s*,\s*(plural|select|selectordinal)\s*,',flat(value)))
def git(repo,*args,raw=False):
 out=subprocess.run(['git',*args],cwd=repo,check=True,stdout=subprocess.PIPE).stdout
 return out if raw else out.decode('utf-8').strip()
def read_jsonl(path): return [json.loads(x) for x in path.read_text(encoding='utf-8').splitlines() if x.strip()]
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
    for value in obj.values(): yield from walk(value)
   elif isinstance(obj,list):
    for value in obj: yield from walk(value)
  try:
   for n,row in enumerate(walk(json.loads(raw.decode('utf-8'))),1): yield n,row
  except json.JSONDecodeError: return

def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--repo',type=Path,required=True);ap.add_argument('--prior-audit',type=Path,required=True);args=ap.parse_args()
 repo=args.repo.resolve();audit=args.prior_audit.resolve();bundle=Path(__file__).resolve().parent;m=json.loads((bundle/'manifest.json').read_text(encoding='utf-8'))
 review=m['review_head'];app=m['application_head'];source=m['source_catalog_head']
 for ref,key in ((review,'review_tree'),(app,'application_tree'),(source,'source_catalog_tree')):
  if git(repo,'rev-parse',f'{ref}^{{tree}}')!=m[key]:die(f'commit/tree mismatch {ref}')
 if git(repo,'rev-parse',f'{app}^')!=review:die('application parent is not the exact review head')
 if git(repo,'merge-base','--is-ancestor',app,'HEAD')!='':die('pinned application is not an ancestor of current docs head')
 ids=[json.loads(x)['source_id'] for x in (audit/'frozen-inputs/source-inventory.jsonl').read_text(encoding='utf-8').splitlines() if x.strip()]
 if len(ids)!=5437 or ids!=sorted(ids):die('frozen source inventory mismatch')
 selected_ids=ids[183:203]
 if selected_ids!=m['source_ids']:die('source-index window mismatch')
 pre=read_jsonl(bundle/'selection-before-corrections.jsonl');selection=read_jsonl(bundle/'selection.jsonl');decisions=read_jsonl(bundle/'decisions.jsonl');carries=read_jsonl(bundle/'carries.jsonl');exclusions=read_jsonl(bundle/'terminal-exclusions.jsonl');holds=read_jsonl(bundle/'conflict-holds.jsonl');patches=read_jsonl(bundle/'applied-corrections.jsonl');audits=read_jsonl(bundle/'reviewed-cell-audit.jsonl')
 if (len(pre),len(selection),len(decisions),len(carries),len(exclusions),len(holds),len(patches),len(audits))!=(240,240,64,127,7,0,44,240):die('bundle row count mismatch')
 pair=lambda r:(r['source_id'],r['locale'])
 for group,name in ((pre,'baseline'),(selection,'selection'),(decisions,'decisions'),(carries,'carries'),(exclusions,'exclusions'),(holds,'holds'),(patches,'patches'),(audits,'cell audit')):
  if len({pair(x) for x in group})!=len(group):die(f'duplicate cell in {name}')
 by_pre={pair(x):x for x in pre};by_final={pair(x):x for x in selection};by_dec={pair(x):x for x in decisions};by_patch={pair(x):x for x in patches};by_audit={pair(x):x for x in audits}
 expected={(sid,loc) for sid in selected_ids for loc in LOCALES}
 if set(by_pre)!=expected or set(by_final)!=expected or set(by_audit)!=expected:die('exact 20-key × 12-locale coverage mismatch')
 if set(pair(x) for x in decisions+carries+exclusions+holds+patches)!=expected:die('review partition mismatch')
 # Revalidate all raw exact-overlap inputs at the exact review head.
 scanrows=read_jsonl(bundle/'prior-evidence-scan-manifest.jsonl');scanraw=(bundle/'prior-evidence-scan-manifest.jsonl').read_bytes()
 if len(scanrows)!=784 or sha(scanraw)!=m['prior_overlap_scan']['manifest_sha256']:die('prior evidence manifest mismatch')
 prior=collections.defaultdict(list)
 for item in scanrows:
  if item['root']=='prior-audit-7ff': raw=(audit/item['path']).read_bytes()
  elif item['root']=='pr-review-head': raw=git(repo,'show',f"{review}:{item['path']}",raw=True)
  else: die('unknown input root')
  if len(raw)!=item['bytes'] or sha(raw)!=item['sha256']:die(f"raw evidence input mismatch: {item['root']}:{item['path']}")
  for line,row in records(raw,item['path']):
   sid=row.get('source_id') or row.get('message_id') or row.get('id');loc=row.get('locale')
   if sid not in selected_ids or loc not in LOCALES:continue
   status=str(row.get('status') or row.get('review_outcome') or '').strip().lower().replace('_','-')
   if status not in TERMINAL:continue
   cell=by_pre[(sid,loc)];target_hash=row.get('target_sha256') or row.get('current_target_sha256')
   if row.get('source_sha256')==cell['source_sha256'] and target_hash==cell['target_sha256']:
    prior[(sid,loc)].append({'status':status,'root':item['root'],'path':item['path'],'line':line,'batch':row.get('batch') or row.get('review_batch'),'finding_id':row.get('finding_id')})
 if collections.Counter(x['disposition'] for x in pre)!=collections.Counter({'new':64,'prior_accepted':127,'prior_correction-needed':49}):die('review-head overlap partition mismatch')
 before_cats={};after_cats={};changed=set()
 for loc in LOCALES:
  path=f'web/src/lib/locales/ui-labels.{loc}.json';before=git(repo,'show',f'{review}:{path}',raw=True);after=git(repo,'show',f'{app}:{path}',raw=True)
  if sha(before)!=m['direct_catalog']['catalog_sha256_before'][path] or sha(after)!=m['direct_catalog']['catalog_sha256_after_application'][path]:die(f'catalog SHA mismatch {loc}')
  before_cats[loc]=json.loads(before.decode('utf-8'));after_cats[loc]=json.loads(after.decode('utf-8'))
  if set(after_cats[loc])!=set(ids):die(f'catalog keys mismatch {loc}')
  if any(v is None or (isinstance(v,str) and not v.strip()) for v in after_cats[loc].values()):die(f'blank catalog cell {loc}')
  changed.update((sid,loc) for sid in ids if before_cats[loc][sid]!=after_cats[loc][sid])
 if sum(isinstance(v,(dict,list)) for cat in after_cats.values() for v in cat.values())!=15:die('structured plural cell census mismatch')
 if changed!=set(by_patch):die('catalog application changed cells outside correction ledger')
 current={loc:json.loads(git(repo,'show',f'HEAD:web/src/lib/locales/ui-labels.{loc}.json',raw=True).decode('utf-8')) for loc in LOCALES}
 follow_dir=bundle.parent/'cross-review-183-202-follow-up-195-ptbr'
 follow_rows=read_jsonl(follow_dir/'refinement.jsonl');root_ledger=(follow_dir/'parent-cross-review-44.jsonl').read_bytes()
 if sha(root_ledger)!='540ae4de10b019726dee36779d802115bf102b5a35cec77b71eb74b876ce045b':die('parent cross-review ledger checksum mismatch')
 root_rows=read_jsonl(follow_dir/'parent-cross-review-44.jsonl')
 if len(root_rows)!=44 or len(follow_rows)!=1:die('parent cross-review/addendum row count mismatch')
 root_ref=[x for x in root_rows if x['sourceIndex']==195 and x['locale']=='pt-BR']
 if len(root_ref)!=1 or root_ref[0]['crossReviewDisposition']!='refined-and-accepted':die('unique pt-BR parent refinement missing')
 follow=follow_rows[0];follow_key=(follow['source_id'],follow['locale'])
 if follow_key!=(root_ref[0]['source'],root_ref[0]['locale']) or (follow['previous_target'],follow['previous_target_sha256'],follow['current_target'],follow['current_target_sha256'])!=(root_ref[0]['currentAppliedTarget'],root_ref[0]['expectedCurrentAppliedTargetHash'],root_ref[0]['crossReviewedTarget'],root_ref[0]['crossReviewedTargetHash']):die('parent refinement exact text/hash mismatch')
 if follow['source_sha256']!=root_ref[0]['sourceHash']:die('parent refinement source hash mismatch')
 if follow['cross_review_ledger_sha256']!=sha(root_ledger) or follow['review_baseline_head']!=root_ref[0]['currentPrHead']:die('parent refinement provenance mismatch')
 if git(repo,'rev-parse',f"{follow['application_head']}^{{tree}}")!=follow['application_tree'] or git(repo,'merge-base','--is-ancestor',follow['application_head'],'HEAD')!='':die('parent refinement application pin mismatch')
 if current[follow_key[1]].get(follow_key[0])!=follow['current_target'] or sha(current[follow_key[1]][follow_key[0]].encode('utf-8'))!=follow['current_target_sha256']:die('current parent-refined target mismatch')
 for cell in pre:
  k=pair(cell);matches=prior.get(k,[]);statuses=sorted({x['status'] for x in matches});disp='conflict' if len(statuses)>1 else ('prior_'+statuses[0] if statuses else 'new')
  if (cell['prior_exact_matches'],cell['disposition'])!=(matches,disp):die(f'exact prior status mismatch {k}')
  if cell['source_index']!=ids.index(cell['source_id']) or cell['source_sha256']!=vsha(cell['source_id']):die(f'source index/hash mismatch {k}')
  if cell['target_text']!=before_cats[k[1]][k[0]] or cell['target_sha256']!=vsha(cell['target_text']):die(f'baseline target mismatch {k}')
  final=by_final[k];patch=by_patch.get(k);target=after_cats[k[1]][k[0]]
  if patch:
   if patch['previous_target']!=cell['target_text'] or patch['previous_target_sha256']!=cell['target_sha256'] or patch['source_sha256']!=cell['source_sha256'] or patch['prior_exact_correction_needed_matches']!=matches:die(f'exact correction basis mismatch {k}')
   if patch['confidence']!='high' or patch['applied_in_catalog_commit'] is not True or patch['application_head']!=app:die(f'correction confidence/application mismatch {k}')
   if patch['current_target']!=target or patch['current_target_sha256']!=vsha(target) or final['target_text']!=target:die(f'corrected target mismatch {k}')
   if cell['disposition']=='new':
    if patch.get('fresh_review_correction') is not True:die(f'fresh correction unmarked {k}')
   elif cell['disposition']!='prior_correction-needed':die(f'correction applied outside eligible row {k}')
  else:
   if target!=cell['target_text'] or final['target_text']!=cell['target_text']:die(f'unchanged target moved {k}')
  current_target=current[k[1]].get(k[0])
  if current_target!=final['target_text']:
   if k!=follow_key or final['target_text']!=follow['previous_target'] or current_target!=follow['current_target']:die(f'current catalog differs without exact cross-review follow-up {k}')
 if collections.Counter(x['disposition'] for x in selection)!=collections.Counter({'new':62,'prior_accepted':127,'prior_correction-needed':7,'corrected-this-pass':44}):die('final selection partition mismatch')
 if collections.Counter(x['status'] for x in decisions)!=collections.Counter({'accepted':60,'correction-needed':2,'corrected':2}):die('fresh decision totals mismatch')
 # Every fresh cell has a complete context, exact pins, placeholder/ICU checks, and a disposition.
 for row in decisions:
  k=pair(row);base=by_pre[k]
  if base['disposition']!='new' or row['prior_exact_matches']:die(f'fresh cell mismatch {k}')
  if (row['review_head'],row['review_tree'],row['reviewed_code_head'],row['reviewed_code_tree'])!=(review,m['review_tree'],source,m['source_catalog_tree']):die(f'review pin mismatch {k}')
  if row['current_target_sha256_revalidated'] is not True or row['source_context_review_result'] is None:die(f'context/hash review missing {k}')
  if row['placeholders_source']!=ph(row['source_id']) or row['placeholders_target']!=ph(row['target_text']) or row['placeholders_preserved'] is not True:die(f'placeholder mismatch {k}')
  if row['icu_message_source'] or row['icu_message_target'] or not row['protected_literals_preserved'] or row['native_speaker_approval']:die(f'ICU/literal/approval mismatch {k}')
  if row['status']=='correction-needed' and row['proposed_target_sha256']!=vsha(row['proposed_target']):die(f'proposal hash mismatch {k}')
 for group,expected_status in ((carries,'prior_accepted'),(exclusions,'prior_correction-needed')):
  for row in group:
   cell=by_pre[pair(row)]
   if cell['disposition']!=expected_status or row['prior_exact_matches']!=prior.get(pair(row),[]):die(f'carry/exclusion mismatch {pair(row)}')
 for row in audits:
  k=pair(row);sel=by_final[k]
  if any(row.get(field)!=sel.get(field) for field in ('source_index','source_sha256','target_text','target_sha256')):die(f'all-cell target mismatch {k}')
  if row['placeholders_source']!=ph(row['source_id']) or row['placeholders_target']!=ph(row['target_text']) or not row['placeholders_preserved']:die(f'all-cell placeholder mismatch {k}')
  if row['icu_message_source'] or row['icu_message_target'] or not row['protected_literals_preserved']:die(f'all-cell ICU/literal mismatch {k}')
 # Source excerpts are backed by frozen Git blobs.
 ctx=m['source_context'];ctxraw=(bundle/ctx['file']).read_bytes()
 if sha(ctxraw)!=ctx['evidence_text_sha256']:die('source context checksum mismatch')
 for path,digest in ctx['sha256'].items():
  if sha(git(repo,'show',f'{source}:{path}',raw=True))!=digest or git(repo,'rev-parse',f'{source}:{path}')!=ctx['git_blob_ids'][path]:die(f'source file pin mismatch {path}')
 visual=m['visual_check'];visualraw=(bundle/visual['file']).read_bytes()
 if visual['status']!='blocked' or sha(visualraw)!=visual['sha256'] or not m['browser_recapture_required']:die('headed visual blocker mismatch')
 if m['placeholder_and_literal_checks']!={'cells_checked':240,'placeholder_sets_preserved':True,'icu_messages':0,'protected_literals_checked':True}:die('manifest placeholder/literal census mismatch')
 expected=[f'{sha(p.read_bytes())}  {p.name}' for p in sorted(bundle.iterdir()) if p.is_file() and p.name!='SHA256SUMS']
 if (bundle/'SHA256SUMS').read_text(encoding='utf-8').splitlines()!=expected:die('SHA256SUMS mismatch')
 print('PASS: exact source/review/application pins; 240-cell overlap and status partitions; 64 fresh decisions (60 accepted, 2 correction-needed, 2 corrected); 127 carries; 7 exclusions; 44 exact corrections; 784 raw prior evidence inputs; source-code pins; all-cell placeholders/ICU/protected literals; visual blocker; bundle checksums.')
if __name__=='__main__': main()
