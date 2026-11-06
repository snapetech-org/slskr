#!/usr/bin/env python3
"""Verify exact-head slskR semantic-review evidence for source indices 303–322."""
import argparse,collections,hashlib,json,re,subprocess
from pathlib import Path
LOCALES=['ar','de','es','fr','hi','id','ja','ko','pt-BR','vi','zh-Hans','zh-Hant']
TERMINAL={'accepted','correction-needed','held','keep','corrected'}
ALIASES={'source_id':['source_id','sourceId','message_id','id'],'source_sha':['source_sha256','sourceSha256'],'target_sha':['target_sha256','targetSha256','current_target_sha256'],'status':['status','review_outcome','disposition']}
def fail(msg):raise SystemExit('FAIL: '+msg)
def sha(raw):return hashlib.sha256(raw).hexdigest()
def value_sha(v):return sha(v.encode('utf-8') if isinstance(v,str) else json.dumps(v,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode('utf-8'))
def read_jsonl(p):return [json.loads(x) for x in Path(p).read_text(encoding='utf-8').splitlines() if x.strip()]
def pick(row,names):
 for n in names:
  if row.get(n) is not None:return row[n]
def norm(v):return str(v or '').strip().lower().replace('_','-')
def placeholders(v):return sorted(set(re.findall(r'\{([^{}]+)\}',str(v))))
def icu(v):return bool(re.search(r'\{\s*[A-Za-z_][\w.-]*\s*,\s*(plural|select|selectordinal)\s*,',str(v)))
def walk(x):
 if isinstance(x,dict):
  yield x
  for v in x.values():yield from walk(v)
 elif isinstance(x,list):
  for v in x:yield from walk(v)
def parse(raw,path):
 if Path(path).suffix=='.jsonl':
  for n,line in enumerate(raw.decode('utf-8').splitlines(),1):
   if line.strip():
    try:yield n,json.loads(line)
    except json.JSONDecodeError:continue
 elif Path(path).suffix=='.json':
  try:yield from enumerate(walk(json.loads(raw.decode('utf-8'))),1)
  except json.JSONDecodeError:return
def git(repo,*a,raw=False):
 b=subprocess.check_output(['git',*a],cwd=repo)
 return b if raw else b.decode('utf-8').strip()
def key(r):return r.get('source_id',r.get('sourceId')),r['locale']
def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--repo',type=Path,required=True);ap.add_argument('--prior-audit',type=Path,required=True);args=ap.parse_args()
 repo=args.repo.resolve();audit=args.prior_audit.resolve();bundle=Path(__file__).resolve().parent
 m=json.loads((bundle/'manifest.json').read_text(encoding='utf-8'))
 review=m['review_head'];app=m['application_head'];source=m['source_catalog_head']
 for commit,tree in ((review,m['review_tree']),(app,m['application_tree']),(source,m['source_catalog_tree'])):
  if git(repo,'rev-parse',f'{commit}^{{tree}}')!=tree:fail('commit/tree mismatch '+commit)
 if git(repo,'rev-parse',f'{app}^')!=review or m['application_parent']!=review:fail('application commit is not direct child of review head')
 expected_paths={f'web/src/lib/locales/ui-labels.{loc}.json' for loc in LOCALES}
 if set(git(repo,'diff','--name-only',f'{review}..{app}').splitlines())!=expected_paths:fail('application diff is not exactly the 12 locale catalogs')
 if git(repo,'diff','--check',f'{review}..{app}') not in ('',''):fail('whitespace error in catalog application')
 inv_path=audit/'frozen-inputs/source-inventory.jsonl';inv_raw=inv_path.read_bytes()
 if sha(inv_raw)!=m['source_inventory_sha256']:fail('frozen source inventory hash mismatch')
 ids=[json.loads(x)['source_id'] for x in inv_raw.decode('utf-8').splitlines() if x.strip()]
 if len(ids)!=5437 or ids!=sorted(ids):fail('source inventory/count/order mismatch')
 selected_ids=ids[m['source_index_start']:m['source_index_end_inclusive']+1]
 if selected_ids!=m['source_ids'] or len(selected_ids)!=20:fail('source-index selection mismatch')
 before=read_jsonl(bundle/'selection-before-corrections.jsonl');final=read_jsonl(bundle/'selection.jsonl');audit_rows=read_jsonl(bundle/'reviewed-cell-audit.jsonl')
 decisions=read_jsonl(bundle/'decisions.jsonl');carries=read_jsonl(bundle/'carries.jsonl');patches=read_jsonl(bundle/'applied-corrections.jsonl')
 candidates=read_jsonl(bundle/'candidate-corrections.jsonl');roots=read_jsonl(bundle/'root-cross-review.jsonl');plan=read_jsonl(bundle/'root-apply-plan.jsonl')
 exclusions=read_jsonl(bundle/'terminal-exclusions.jsonl');recon=read_jsonl(bundle/'conflict-reconciliation.jsonl')
 groups=(before,final,audit_rows,decisions,carries,patches,candidates,roots,plan)
 labels=('baseline','final selection','full audit','fresh decisions','accepted carries','application patches','candidates','root review','root plan')
 for rows,label in zip(groups,labels):
  if len({key(r) for r in rows})!=len(rows):fail('duplicate cell in '+label)
 if tuple(map(len,groups))!=(240,240,240,80,92,77,77,77,77):fail('row count mismatch '+str(tuple(map(len,groups))))
 before_by={key(r):r for r in before};final_by={key(r):r for r in final};audit_by={key(r):r for r in audit_rows};decision_by={key(r):r for r in decisions};carry_by={key(r):r for r in carries};patch_by={key(r):r for r in patches};candidate_by={key(r):r for r in candidates};root_by={(r['sourceId'],r['locale']):r for r in roots};plan_by={(r['sourceId'],r['locale']):r for r in plan}
 cells={(sid,loc) for sid in selected_ids for loc in LOCALES}
 if set(before_by)!=cells or set(final_by)!=cells or set(audit_by)!=cells:fail('coverage is not 20 source IDs × 12 locales')
 fresh_cells={k for k,r in before_by.items() if r['disposition']=='new'}
 carry_cells={k for k,r in before_by.items() if r['disposition']=='prior_accepted'}
 if set(decision_by)!=fresh_cells:fail('fresh decision coverage mismatch')
 if set(patch_by)!=set(root_by) or set(root_by)!=set(plan_by):fail('candidate/root/plan/patch cell sets differ')
 if set(carry_by)!=(carry_cells-set(patch_by)):fail('carry coverage mismatch')
 if len(exclusions) or len(recon):fail('unexpected hold/conflict reconciliation entries')
 if collections.Counter(r['disposition'] for r in roots)!=collections.Counter({'accepted':43,'refined':34}):fail('root decision counts mismatch')
 for p,expected in [('candidate-corrections.jsonl',m['candidate_ledger_sha256']),('root-cross-review.jsonl',m['root_ledger_sha256']),('root-apply-plan.jsonl',m['root_apply_plan_sha256'])]:
  if sha((bundle/p).read_bytes())!=expected:fail('review artifact checksum mismatch '+p)
 root_summary=json.loads((bundle/'root-cross-review-summary.json').read_text(encoding='utf-8'))
 if root_summary['rootLedgerSha256']!=m['root_ledger_sha256'] or root_summary['applyPlanSha256']!=m['root_apply_plan_sha256'] or root_summary['candidatePlanSha256']!=m['candidate_ledger_sha256']:fail('root summary reference mismatch')
 scan_path=bundle/'prior-evidence-scan-manifest.jsonl';scan_raw=scan_path.read_bytes();scan=read_jsonl(scan_path)
 if len(scan)!=m['prior_overlap_scan']['input_count'] or sha(scan_raw)!=m['prior_overlap_scan']['manifest_file_sha256']:fail('prior overlap manifest count/hash mismatch')
 if sha(json.dumps(sorted(scan,key=lambda r:(r['root'],r['path'])),sort_keys=True,separators=(',',':')).encode())!=m['prior_overlap_scan']['canonical_input_manifest_sha256']:fail('canonical overlap manifest mismatch')
 prior=collections.defaultdict(list)
 for item in scan:
  if item['root']=='prior-audit-7ff':raw=(audit/item['path']).read_bytes()
  elif item['root']=='pr-review-head':raw=git(repo,'show',f"{review}:{item['path']}",raw=True)
  else:fail('unknown prior-evidence root '+str(item['root']))
  if len(raw)!=item['bytes'] or sha(raw)!=item['sha256']:fail('prior evidence input hash mismatch '+item['path'])
  for line,row in parse(raw,item['path']):
   sid=pick(row,ALIASES['source_id']);loc=row.get('locale')
   if not isinstance(sid,str) or sid not in selected_ids or loc not in LOCALES:continue
   st=norm(pick(row,ALIASES['status']))
   if st not in TERMINAL:continue
   b=before_by[(sid,loc)]
   if pick(row,ALIASES['source_sha'])==b['source_sha256'] and pick(row,ALIASES['target_sha'])==b['target_sha256']:
    prior[(sid,loc)].append({'status':st,'root':item['root'],'path':item['path'],'line':line,'batch':row.get('batch') or row.get('review_batch'),'finding_id':row.get('finding_id')})
 catalog_before={};catalog_after={};changed=set();catalog_hash_before={};catalog_hash_after={}
 for loc in LOCALES:
  p=f'web/src/lib/locales/ui-labels.{loc}.json';rb=git(repo,'show',f'{review}:{p}',raw=True);ra=git(repo,'show',f'{app}:{p}',raw=True)
  if sha(rb)!=m['catalog_sha256_before'][p] or sha(ra)!=m['catalog_sha256_after'][p]:fail('locale catalog hash mismatch '+loc)
  catalog_hash_before[p]=sha(rb);catalog_hash_after[p]=sha(ra);catalog_before[loc]=json.loads(rb.decode());catalog_after[loc]=json.loads(ra.decode())
  if set(catalog_before[loc])!=set(ids) or set(catalog_after[loc])!=set(ids):fail('catalog/source inventory mismatch '+loc)
  for sid in ids:
   old=catalog_before[loc][sid];new=catalog_after[loc][sid]
   if old!=new:changed.add((sid,loc))
   if new is None or (isinstance(new,str) and not new.strip()):fail('blank target '+str((sid,loc)))
 if changed!=set(patch_by):fail('application diff cells do not exactly match patch ledger')
 for b in before:
  k=key(b);ms=prior.get(k,[]);sts=sorted({x['status'] for x in ms});disp='conflict' if len(sts)>1 else ('prior_'+sts[0] if sts else 'new')
  if b['prior_exact_matches']!=ms or b['disposition']!=disp:fail('exact prior terminal overlap mismatch '+str(k))
  if b['source_index']!=ids.index(b['source_id']) or b['source_sha256']!=value_sha(b['source_id']):fail('source index/hash mismatch '+str(k))
  old=catalog_before[k[1]][k[0]];new=catalog_after[k[1]][k[0]]
  if old!=b['target_text'] or value_sha(old)!=b['target_sha256']:fail('baseline exact target mismatch '+str(k))
  a=audit_by[k];f=final_by[k];d=decision_by.get(k);p=plan_by.get(k);c=carry_by.get(k);patch=patch_by.get(k);root=root_by.get(k)
  if p:
   if patch is None or root is None or c is not None:fail('missing patch/root or invalid carry '+str(k))
   if p['expectedOldTarget']!=old or p['expectedOldTargetSha256']!=value_sha(old) or p['newTarget']!=new or p['newTargetSha256']!=value_sha(new):fail('plan application mismatch '+str(k))
   if patch['baseline_target_text']!=old or patch['baseline_target_sha256']!=value_sha(old) or patch['final_target']!=new or patch['final_target_sha256']!=value_sha(new):fail('application ledger text/hash mismatch '+str(k))
   if patch['root_disposition']!=root['disposition'] or patch['source_sha256']!=b['source_sha256'] or patch['prior_exact_matches']!=b['prior_exact_matches']:fail('root application/source/overlap mismatch '+str(k))
   expect_dec='corrected' if disp=='new' else ('corrected-prior' if disp=='prior_correction-needed' else 'corrected-recheck')
   expect_status='corrected'
  else:
   if new!=old or patch is not None:fail('unledgered catalog change '+str(k))
   expect_dec='accepted' if disp=='new' else 'accepted-carry';expect_status='accepted'
   if disp not in ('new','prior_accepted'):fail('unresolved correction-needed/conflict '+str(k))
  if f['target_text']!=new or f['target_sha256']!=value_sha(new) or f['decision']!=expect_dec or f['disposition']!=expect_status:fail('final selection status/target mismatch '+str(k))
  if a['target_text']!=new or a['target_sha256']!=value_sha(new) or a['status']!=expect_status or a['decision']!=expect_dec:fail('full audit status/target mismatch '+str(k))
  if a['source_sha256']!=b['source_sha256'] or a['baseline_target_sha256']!=b['target_sha256'] or a['prior_exact_matches']!=b['prior_exact_matches']:fail('audit source/baseline/overlap mismatch '+str(k))
  if placeholders(b['source_id'])!=placeholders(new) or not a['placeholders_preserved'] or a['placeholders_target']!=placeholders(new):fail('placeholder mismatch '+str(k))
  if icu(b['source_id']) or icu(new) or a['icu_message_source'] or a['icu_message_target']:fail('ICU mismatch '+str(k))
  if not a['protected_literals_checked'] or not a['protected_literals_preserved']:fail('protected literal evidence mismatch '+str(k))
  if 'RustyMilk' in b['source_id'] and 'RustyMilk' not in new:fail('RustyMilk literal lost '+str(k))
  if 'FTP' in b['source_id'] and not ('FTP' in new or (k[1]=='hi' and 'एफ़टीपी' in new)):fail('FTP literal/approved Hindi transliteration lost '+str(k))
  if '{name}' in b['source_id'] and '{name}' not in new:fail('name placeholder lost '+str(k))
  if not a['source_context_pointer'] or not a['reviewed_context'] or not a['semantic_review_result']:fail('context/review record missing '+str(k))
  if a['native_speaker_approval']:fail('native speaker approval asserted '+str(k))
  if disp=='new':
   if d is None or d['reviewed_target_after']!=new or d['status']!=expect_status:fail('fresh cell decision mismatch '+str(k))
   if d['source_sha256']!=b['source_sha256'] or d['baseline_target_sha256']!=b['target_sha256']:fail('fresh decision hash mismatch '+str(k))
  elif d is not None:fail('nonfresh cell in fresh decisions '+str(k))
  if disp=='prior_accepted' and not p:
   if c is None or c['target_text']!=new or c['target_sha256']!=value_sha(new):fail('accepted carry mismatch '+str(k))
 for cand in candidates:
  k=(cand['source_id'],cand['locale']);root=root_by.get(k);p=plan_by.get(k)
  if root is None or p is None:fail('candidate missing root/plan '+str(k))
  if root['candidateTarget']!=cand['proposed_target'] or root['candidateTargetSha256']!=cand['proposed_sha256'] or root['candidatePlanSha256']!=m['candidate_ledger_sha256']:fail('root/candidate proposal pin mismatch '+str(k))
  if root['currentTarget']!=cand['baseline_target_text'] or root['currentTargetSha256']!=cand['baseline_target_sha256'] or root['sourceSha256']!=cand['source_sha256']:fail('root baseline/source mismatch '+str(k))
  if p['rootLedgerSha256']!=m['root_ledger_sha256'] or p['newTarget']!=root['rootTarget'] or p['newTargetSha256']!=root['rootTargetSha256']:fail('root plan mismatch '+str(k))
 pins=json.loads((bundle/'source-pins.json').read_text(encoding='utf-8'))
 if pins['review_head']!=review or pins['review_tree']!=m['review_tree'] or pins['application_head']!=app or pins['application_tree']!=m['application_tree'] or pins['source_catalog_head']!=source or pins['source_catalog_tree']!=m['source_catalog_tree']:fail('source pins commit/tree mismatch')
 if pins['catalog_sha256_before']!=m['catalog_sha256_before'] or pins['catalog_sha256_after']!=m['catalog_sha256_after']:fail('source pin/catalog hash mismatch')
 if sha((bundle/'source-context.txt').read_bytes())!=m['source_context']['sha256']:fail('source context checksum mismatch')
 for path,blob in pins['git_blob_ids'].items():
  raw=git(repo,'show',f'{source}:{path}',raw=True)
  if sha(raw)!=pins['sha256'][path] or git(repo,'rev-parse',f'{source}:{path}')!=blob:fail('source caller checksum/blob mismatch '+path)
  if git(repo,'rev-parse',f'{review}:{path}')!=blob or git(repo,'rev-parse',f'{app}:{path}')!=blob:fail('source caller drift '+path)
 if len(pins['files'])!=13:fail('unexpected caller file count')
 if sha((bundle/'headed-visual-check.md').read_bytes())!=m['visual_check']['sha256'] or m['visual_check']['status']!='blocked' or not m['browser_recapture_required']:fail('headed visual evidence mismatch')
 if m['decision_counts']!={'accepted':163,'corrected':77} or m['root_disposition_counts']!={'accepted':43,'refined':34} or m['holds']!=0 or m['conflicts']!=0:fail('manifest summary mismatch')
 if m['native_speaker_approval'] or m['placeholder_and_literal_checks']!={'cells_checked':240,'placeholder_sets_preserved':True,'placeholder_cells':12,'icu_messages':0,'protected_literal_cells':48,'protected_literals_checked':True,'protected_literals_preserved':True,'protected_literals_changed':0}:fail('placeholder/literal/native-review manifest mismatch')
 expected_sums=[f'{sha(p.read_bytes())}  {p.name}' for p in sorted(bundle.iterdir()) if p.is_file() and p.name!='SHA256SUMS']
 if (bundle/'SHA256SUMS').read_text(encoding='utf-8').splitlines()!=expected_sums:fail('bundle SHA256SUMS mismatch')
 print('PASS: 240 exact cells; 80 fresh (71 accepted, 9 corrected); 92 accepted carries; 77 root-reviewed corrections (43 accepted, 34 refined); zero holds/conflicts. Verified 876 prior evidence inputs, source inventory/order, all source/current/final hashes, 13 caller files, placeholders, ICU, protected literals, exact 12-catalog-only application, blocked visual-review record, and bundle checksums.')
if __name__=='__main__':main()
