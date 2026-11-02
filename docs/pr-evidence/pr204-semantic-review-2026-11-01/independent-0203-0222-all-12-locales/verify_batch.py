#!/usr/bin/env python3
"""Verify exact-head semantic evidence for slskR source indices 203–222."""
import argparse, collections, hashlib, json, re, subprocess
from pathlib import Path
LOCALES=['ar','de','es','fr','hi','id','ja','ko','pt-BR','vi','zh-Hans','zh-Hant']
TERMINAL={'accepted','correction-needed','held','keep','corrected'}
def die(msg): raise SystemExit('FAIL: '+msg)
def sha(raw):return hashlib.sha256(raw).hexdigest()
def vsha(value):
 raw=value.encode('utf-8') if isinstance(value,str) else json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode('utf-8')
 return sha(raw)
def flat(value):
 if isinstance(value,dict):return ' '.join(flat(v) for v in value.values())
 if isinstance(value,list):return ' '.join(flat(v) for v in value)
 return str(value)
def ph(value):return sorted(set(re.findall(r'\{([^{}]+)\}',flat(value))))
def icu(value):return bool(re.search(r'\{\s*[A-Za-z_][\w.-]*\s*,\s*(plural|select|selectordinal)\s*,',flat(value)))
def git(repo,*args,raw=False):
 out=subprocess.run(['git',*args],cwd=repo,check=True,stdout=subprocess.PIPE).stdout
 return out if raw else out.decode('utf-8').strip()
def read_jsonl(path):return [json.loads(x) for x in path.read_text(encoding='utf-8').splitlines() if x.strip()]
def walk(x):
 if isinstance(x,dict):
  yield x
  for v in x.values():yield from walk(v)
 elif isinstance(x,list):
  for v in x:yield from walk(v)
def records(raw,path):
 if Path(path).suffix=='.jsonl':
  for n,line in enumerate(raw.decode('utf-8').splitlines(),1):
   if line.strip():
    try:yield n,json.loads(line)
    except json.JSONDecodeError:continue
 elif Path(path).suffix=='.json':
  try:
   for n,row in enumerate(walk(json.loads(raw.decode('utf-8'))),1):yield n,row
  except json.JSONDecodeError:return
def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--repo',type=Path,required=True);ap.add_argument('--prior-audit',type=Path,required=True);args=ap.parse_args()
 repo=args.repo.resolve();audit=args.prior_audit.resolve();bundle=Path(__file__).resolve().parent;m=json.loads((bundle/'manifest.json').read_text(encoding='utf-8'))
 review=m['review_head'];app=m['application_head'];source=m['source_catalog_head']
 for ref,key in ((review,'review_tree'),(app,'application_tree'),(source,'source_catalog_tree')):
  if git(repo,'rev-parse',f'{ref}^{{tree}}')!=m[key]:die(f'commit/tree mismatch: {ref}')
 if git(repo,'rev-parse',f'{app}^')!=review or m['application_parent']!=review:die('application commit is not a direct child of review head')
 if git(repo,'merge-base','--is-ancestor',app,'HEAD')!='':die('pinned application is not an ancestor of docs head')
 inv=read_jsonl(audit/'frozen-inputs/source-inventory.jsonl');ids=[r['source_id'] for r in inv]
 if len(ids)!=5437 or ids!=sorted(ids):die('frozen source inventory mismatch')
 selected_ids=ids[203:223]
 if selected_ids!=m['source_ids']:die('source-index window mismatch')
 pre=read_jsonl(bundle/'selection-before-corrections.jsonl');final=read_jsonl(bundle/'selection.jsonl');fresh=read_jsonl(bundle/'decisions.jsonl');carries=read_jsonl(bundle/'carries.jsonl');exclusions=read_jsonl(bundle/'terminal-exclusions.jsonl');holds=read_jsonl(bundle/'conflict-holds.jsonl');patches=read_jsonl(bundle/'applied-corrections.jsonl');audits=read_jsonl(bundle/'reviewed-cell-audit.jsonl')
 if (len(pre),len(final),len(fresh),len(carries),len(exclusions),len(holds),len(patches),len(audits))!=(240,240,39,104,12,0,86,240):die('bundle row count mismatch')
 pair=lambda r:(r['source_id'],r['locale'])
 for group,name in ((pre,'baseline'),(final,'selection'),(fresh,'fresh decisions'),(carries,'carries'),(exclusions,'exclusions'),(holds,'conflicts'),(patches,'patches'),(audits,'cell audit')):
  if len({pair(r) for r in group})!=len(group):die(f'duplicate row in {name}')
 bypre={pair(r):r for r in pre};byfinal={pair(r):r for r in final};byaudit={pair(r):r for r in audits};byfresh={pair(r):r for r in fresh};bypatch={pair(r):r for r in patches}
 expected={(sid,loc) for sid in selected_ids for loc in LOCALES}
 if set(bypre)!=expected or set(byfinal)!=expected or set(byaudit)!=expected:die('exact 20-source × 12-locale coverage mismatch')
 if set(byfresh)!= {(k[0],k[1]) for k in expected if bypre[k]['disposition']=='new'}:die('fresh decision set mismatch')
 if collections.Counter(r['disposition'] for r in pre)!=collections.Counter({'new':39,'prior_accepted':104,'prior_correction-needed':97}):die('review-head overlap partition mismatch')
 # Validate every raw file used to compute exact current overlap.
 scanrows=read_jsonl(bundle/'prior-evidence-scan-manifest.jsonl');scanraw=(bundle/'prior-evidence-scan-manifest.jsonl').read_bytes()
 if len(scanrows)!=794 or sha(scanraw)!=m['prior_overlap_scan']['manifest_file_sha256']:die('raw overlap-input manifest hash mismatch')
 canon=sha(json.dumps(sorted(scanrows,key=lambda x:(x['root'],x['path'])),sort_keys=True,separators=(',',':')).encode())
 if canon!=m['prior_overlap_scan']['canonical_manifest_sha256']:die('canonical overlap-input manifest mismatch')
 prior=collections.defaultdict(list)
 for item in scanrows:
  if item['root']=='prior-audit-7ff':raw=(audit/item['path']).read_bytes()
  elif item['root']=='pr-review-head':raw=git(repo,'show',f"{review}:{item['path']}",raw=True)
  else:die('unknown evidence root')
  if len(raw)!=item['bytes'] or sha(raw)!=item['sha256']:die('raw evidence pin mismatch: '+item['root']+':'+item['path'])
  for line,row in records(raw,item['path']):
   sid=row.get('source_id') or row.get('message_id') or row.get('id');loc=row.get('locale')
   if not isinstance(sid,str) or loc not in LOCALES or sid not in selected_ids:continue
   status=str(row.get('status') or row.get('review_outcome') or '').strip().lower().replace('_','-')
   if status not in TERMINAL:continue
   cell=bypre[(sid,loc)];target_sha=row.get('target_sha256') or row.get('current_target_sha256')
   if row.get('source_sha256')==cell['source_sha256'] and target_sha==cell['target_sha256']:
    prior[(sid,loc)].append({'status':status,'root':item['root'],'path':item['path'],'line':line,'batch':row.get('batch') or row.get('review_batch'),'finding_id':row.get('finding_id')})
 # Compare exact statuses and targets at both pinned catalog commits.
 changed=set();before_cats={};after_cats={}
 for loc in LOCALES:
  path=f'web/src/lib/locales/ui-labels.{loc}.json';before=git(repo,'show',f'{review}:{path}',raw=True);after=git(repo,'show',f'{app}:{path}',raw=True)
  if sha(before)!=m['catalog_sha256_before'][path] or sha(after)!=m['catalog_sha256_after'][path]:die('raw catalog pin mismatch '+loc)
  before_cats[loc]=json.loads(before.decode());after_cats[loc]=json.loads(after.decode())
  if set(before_cats[loc])!=set(ids) or set(after_cats[loc])!=set(ids):die('catalog key inventory mismatch '+loc)
  for sid in ids:
   if before_cats[loc][sid]!=after_cats[loc][sid]:changed.add((sid,loc))
   value=after_cats[loc][sid]
   if value is None or (isinstance(value,str) and not value.strip()):die('blank catalog value '+loc+':'+sid)
 if changed!=set(bypatch):die('application contains unledgered or missing catalog edits')
 if collections.Counter(r['decision'] for r in final)!=collections.Counter({'accepted':38,'corrected':1,'corrected-prior':85,'accepted-carry':104,'held-correction-needed':12}):die('final decision partition mismatch')
 if collections.Counter(r['fresh_disposition'] for r in fresh)!=collections.Counter({'accepted':38,'corrected':1}):die('fresh decision totals mismatch')
 if sum(r['source_index'] in range(207,216) and r['locale'] in {'ar','de','es','fr','hi','id','vi'} for r in patches)!=62:die('adversarial contextual correction count mismatch')
 for cell in pre:
  k=pair(cell);matches=prior.get(k,[]);statuses=sorted({r['status'] for r in matches});disp='conflict' if len(statuses)>1 else ('prior_'+statuses[0] if statuses else 'new')
  if (cell['prior_exact_matches'],cell['disposition'])!=(matches,disp):die('exact overlap mismatch '+repr(k))
  if cell['source_index']!=ids.index(cell['source_id']) or cell['source_sha256']!=vsha(cell['source_id']):die('source index/hash mismatch '+repr(k))
  if cell['target_text']!=before_cats[k[1]][k[0]] or cell['target_sha256']!=vsha(cell['target_text']):die('baseline target mismatch '+repr(k))
  new=byfinal[k];auditrow=byaudit[k];patch=bypatch.get(k);target=after_cats[k[1]][k[0]]
  expected_status='corrected' if patch else 'accepted' if cell['disposition'] in ('new','prior_accepted') else 'correction-needed'
  if new['status']!=expected_status or auditrow['status']!=expected_status:die('terminal review status mismatch '+repr(k))
  if patch:
   if patch['source_sha256']!=cell['source_sha256'] or patch['previous_target']!=cell['target_text'] or patch['previous_target_sha256']!=cell['target_sha256'] or patch['prior_exact_correction_needed_matches']!=matches:die('correction exact-hash basis mismatch '+repr(k))
   if patch['confidence']!='high' or patch['applied_in_catalog_commit'] is not True or patch['application_head']!=app or patch['application_tree']!=m['application_tree']:die('correction not exact/high-confidence/application-pinned '+repr(k))
   if patch['current_target']!=target or patch['current_target_sha256']!=vsha(target) or patch.get('target_sha256')!=vsha(target) or patch.get('status')!='corrected':die('correction value/hash/status mismatch '+repr(k))
   if cell['disposition']=='new' and patch.get('fresh_review_correction') is not True:die('fresh correction not marked '+repr(k))
   if cell['disposition']=='prior_correction-needed' and patch.get('fresh_review_correction') is True:die('prior correction misclassified '+repr(k))
   if cell['disposition'] not in ('new','prior_correction-needed'):die('correction applied outside eligible status '+repr(k))
  elif target!=cell['target_text']:die('unledgered target change '+repr(k))
  if new['target_text']!=target or new['target_sha256']!=vsha(target) or new['baseline_target_text']!=cell['target_text']:die('final selection mismatch '+repr(k))
  if auditrow['target_text']!=target or auditrow['target_sha256']!=vsha(target):die('cell audit value/hash mismatch '+repr(k))
  if auditrow['placeholders_source']!=ph(cell['source_id']) or auditrow['placeholders_target']!=ph(target) or not auditrow['placeholders_preserved']:die('placeholder preservation mismatch '+repr(k))
  if auditrow['icu_message_source']!=icu(cell['source_id']) or auditrow['icu_message_target']!=icu(target):die('ICU classification mismatch '+repr(k))
  if auditrow['icu_message_source'] or auditrow['icu_message_target'] or not auditrow['protected_literals_checked'] or not auditrow['protected_literals_preserved']:die('ICU/protected-literal check failed '+repr(k))
  if auditrow['review_head']!=review or auditrow['review_tree']!=m['review_tree'] or auditrow['source_catalog_head']!=source or auditrow['source_catalog_tree']!=m['source_catalog_tree']:die('review pin mismatch '+repr(k))
  if not auditrow['reviewed_context'] or not auditrow['semantic_review_result']:die('semantic context/review missing '+repr(k))
  if cell['disposition']=='new':
   d=byfresh[k]
   if d['source_sha256']!=cell['source_sha256'] or d['reviewed_target_before']!=cell['target_text'] or d['reviewed_target_after']!=target:die('fresh decision exact value mismatch '+repr(k))
   if d['current_target_sha256_revalidated'] is not True or d['source_context_review_result']!=auditrow['reviewed_context']:die('fresh decision context/hash gap '+repr(k))
  if cell['disposition']=='prior_accepted' and (target!=cell['target_text'] or new['decision']!='accepted-carry'):die('accepted carry moved '+repr(k))
  if cell['disposition']=='prior_correction-needed' and not patch and (target!=cell['target_text'] or new['decision']!='held-correction-needed'):die('held exact target moved '+repr(k))
 # Verify the carry and hold files are exactly their selected partitions.
 if {pair(r) for r in carries}!={pair(r) for r in pre if r['disposition']=='prior_accepted'}:die('carry membership mismatch')
 if {pair(r) for r in exclusions}!={pair(r) for r in pre if r['disposition']=='prior_correction-needed' and pair(r) not in bypatch}:die('exclusion membership mismatch')
 for row in carries+exclusions:
  if row['prior_exact_matches']!=prior.get(pair(row),[]):die('carry/exclusion prior evidence mismatch '+repr(pair(row)))
 # Source-context snippets are pinned to exact Git blobs and hashes.
 ctx=m['source_context'];ctxraw=(bundle/ctx['file']).read_bytes()
 if sha(ctxraw)!=ctx['evidence_text_sha256']:die('context evidence text hash mismatch')
 for path,digest in ctx['sha256'].items():
  if sha(git(repo,'show',f'{source}:{path}',raw=True))!=digest or git(repo,'rev-parse',f'{source}:{path}')!=ctx['git_blob_ids'][path]:die('source file pin mismatch '+path)
 vis=m['visual_check'];visraw=(bundle/vis['file']).read_bytes()
 if vis['status']!='blocked' or sha(visraw)!=vis['sha256'] or not m['browser_recapture_required']:die('headed visual blocker evidence mismatch')
 if m['placeholder_and_literal_checks']!={'cells_checked':240,'placeholder_sets_preserved':True,'icu_messages':0,'protected_literals_checked':True,'protected_literals_changed':0}:die('placeholder/literal census mismatch')
 sums=[f'{sha(p.read_bytes())}  {p.name}' for p in sorted(bundle.iterdir()) if p.is_file() and p.name!='SHA256SUMS']
 if (bundle/'SHA256SUMS').read_text(encoding='utf-8').splitlines()!=sums:die('bundle checksum list mismatch')
 print('PASS: 240 exact cells; 39 fresh (38 accepted, 1 corrected), 104 accepted carries, 85 exact prior corrections plus 1 fresh correction, 12 exact prior holds, zero conflicts; all 794 raw overlap inputs, source blobs, catalogs, hashes, placeholders/ICU/literals, and bundle checksums verified.')
if __name__=='__main__':main()
