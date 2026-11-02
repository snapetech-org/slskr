#!/usr/bin/env python3
"""Verify exact-head semantic review evidence for slskR source indices 263–282."""
import argparse
import collections
import hashlib
import json
import re
import subprocess
from pathlib import Path

LOCALES=['ar','de','es','fr','hi','id','ja','ko','pt-BR','vi','zh-Hans','zh-Hant']
TERMINAL={'accepted','corrected','correction-needed','held','keep'}
ALIASES={
 'source_id':['source_id','sourceId','message_id','id'],
 'source_sha':['source_sha256','sourceSha256'],
 'target_sha':['target_sha256','targetSha256','current_target_sha256'],
 'status':['status','review_outcome','disposition'],
}

def fail(message): raise SystemExit('FAIL: '+message)
def sha(raw): return hashlib.sha256(raw).hexdigest()
def value_sha(value):
 raw=value.encode('utf-8') if isinstance(value,str) else json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode('utf-8')
 return sha(raw)
def read_jsonl(path): return [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines() if line.strip()]
def pick(row,names):
 for name in names:
  if row.get(name) is not None: return row[name]
 return None
def normalize_status(value): return str(value or '').strip().lower().replace('_','-')
def walk(value):
 if isinstance(value,dict):
  yield value
  for child in value.values(): yield from walk(child)
 elif isinstance(value,list):
  for child in value: yield from walk(child)
def parse_evidence(raw,path):
 if Path(path).suffix=='.jsonl':
  for number,line in enumerate(raw.decode('utf-8').splitlines(),1):
   if line.strip():
    try: yield number,json.loads(line)
    except json.JSONDecodeError: continue
 elif Path(path).suffix=='.json':
  try: yield from enumerate(walk(json.loads(raw.decode('utf-8'))),1)
  except json.JSONDecodeError: return
def git(repo,*args,raw=False):
 result=subprocess.run(['git',*args],cwd=repo,check=True,stdout=subprocess.PIPE)
 return result.stdout if raw else result.stdout.decode('utf-8').strip()
def placeholders(value): return sorted(set(re.findall(r'\{([^{}]+)\}',str(value))))
def icu(value): return bool(re.search(r'\{\s*[A-Za-z_][\w.-]*\s*,\s*(plural|select|selectordinal)\s*,',str(value)))
def pair(row): return row['source_id'],row['locale']

def main():
 parser=argparse.ArgumentParser(description=__doc__)
 parser.add_argument('--repo',type=Path,required=True)
 parser.add_argument('--prior-audit',type=Path,required=True)
 args=parser.parse_args();repo=args.repo.resolve();prior_audit=args.prior_audit.resolve();bundle=Path(__file__).resolve().parent
 m=json.loads((bundle/'manifest.json').read_text(encoding='utf-8'))
 review=m['review_head'];application=m['application_head'];source=m['source_catalog_head']
 for commit,tree in ((review,m['review_tree']),(application,m['application_tree']),(source,m['source_catalog_tree'])):
  if git(repo,'rev-parse',f'{commit}^{{tree}}')!=tree: fail(f'commit/tree mismatch {commit}')
 if git(repo,'rev-parse',f'{application}^')!=review or m['application_parent']!=review: fail('application is not a direct child of review head')
 inventory_path=prior_audit/'frozen-inputs/source-inventory.jsonl';inventory_raw=inventory_path.read_bytes()
 if sha(inventory_raw)!=m['frozen_source_inventory_sha256']: fail('frozen source inventory checksum mismatch')
 inventory=read_jsonl(inventory_path);source_ids=[r['source_id'] for r in inventory]
 if len(source_ids)!=m['source_key_count'] or source_ids!=sorted(source_ids): fail('source inventory/order mismatch')
 selected_ids=source_ids[m['source_index_start']:m['source_index_end_inclusive']+1]
 if selected_ids!=m['source_ids'] or len(selected_ids)!=20: fail('source-index selection mismatch')

 before=read_jsonl(bundle/'selection-before-corrections.jsonl');final=read_jsonl(bundle/'selection.jsonl')
 decisions=read_jsonl(bundle/'decisions.jsonl');audits=read_jsonl(bundle/'reviewed-cell-audit.jsonl')
 carries=read_jsonl(bundle/'carries.jsonl');exclusions=read_jsonl(bundle/'terminal-exclusions.jsonl')
 conflicts=read_jsonl(bundle/'conflict-holds.jsonl');patches=read_jsonl(bundle/'applied-corrections.jsonl')
 roots=read_jsonl(bundle/'root-cross-review.jsonl');plan=read_jsonl(bundle/'root-apply-plan.jsonl')
 candidates=read_jsonl(bundle/'candidate-corrections.jsonl');recon=read_jsonl(bundle/'conflict-reconciliation.jsonl')
 groups=(before,final,decisions,audits,carries,exclusions,conflicts,patches,roots,plan,candidates,recon)
 names=('baseline','final selection','fresh decisions','full audit','carries','exclusions','conflicts','patches','root review','root plan','candidates','conflict reconciliation')
 for rows,name in zip(groups,names):
  if len({pair(r) for r in rows})!=len(rows): fail(f'duplicate cell in {name}')
 expected=(240,240,25,240,204,0,0,14,14,14,14,0)
 if tuple(map(len,groups))!=expected: fail(f'row counts mismatch: {tuple(map(len,groups))}')
 base_by={pair(r):r for r in before};final_by={pair(r):r for r in final};audit_by={pair(r):r for r in audits}
 decision_by={pair(r):r for r in decisions};patch_by={pair(r):r for r in patches}
 root_by={pair(r):r for r in roots};plan_by={pair(r):r for r in plan};candidate_by={pair(r):r for r in candidates}
 expected_cells={(sid,loc) for sid in selected_ids for loc in LOCALES}
 if set(base_by)!=expected_cells or set(final_by)!=expected_cells or set(audit_by)!=expected_cells: fail('coverage is not exactly 20 keys × 12 locales')
 if set(root_by)!=set(plan_by) or set(root_by)!=set(candidate_by) or set(root_by)!=set(patch_by): fail('candidate/root/plan/patch key sets differ')
 if collections.Counter(r['disposition'] for r in roots)!={'accepted-proposal':8,'refined':6}: fail('root disposition count mismatch')
 if sha((bundle/'root-cross-review.jsonl').read_bytes())!=m['root_cross_review_ledger_sha256']: fail('root ledger SHA mismatch')
 if sha((bundle/'root-apply-plan.jsonl').read_bytes())!=m['root_apply_plan_sha256']: fail('root plan SHA mismatch')
 if sha((bundle/'candidate-corrections.jsonl').read_bytes())!=m['candidate_ledger_sha256']: fail('candidate ledger SHA mismatch')
 for key,r in root_by.items():
  c=candidate_by[key];p=plan_by[key]
  if c['proposed_target']!=r['candidate_target'] or c['proposed_sha256']!=r['candidate_target_sha256']: fail(f'candidate/root mismatch {key}')
  if c['source_sha256']!=r['source_sha256'] or c['baseline_target_sha256']!=r['baseline_target_sha256']: fail(f'candidate/root source/baseline mismatch {key}')
  if p['final_target']!=r['final_target'] or p['final_target_sha256']!=r['final_target_sha256'] or p['disposition']!=r['disposition']: fail(f'root plan mismatch {key}')
  if p['final_target_sha256']!=value_sha(p['final_target']): fail(f'root final target hash mismatch {key}')

 scan_path=bundle/'prior-evidence-scan-manifest.jsonl';scan_raw=scan_path.read_bytes();scan=read_jsonl(scan_path)
 if len(scan)!=m['prior_overlap_scan']['input_count'] or sha(scan_raw)!=m['prior_overlap_scan']['manifest_file_sha256']: fail('overlap input manifest mismatch')
 canonical=sha(json.dumps(sorted(scan,key=lambda r:(r['root'],r['path'])),sort_keys=True,separators=(',',':')).encode())
 if canonical!=m['prior_overlap_scan']['canonical_input_manifest_sha256']: fail('canonical overlap manifest mismatch')
 prior=collections.defaultdict(list)
 for item in scan:
  if item['root']=='prior-audit-7ff': raw=(prior_audit/item['path']).read_bytes()
  elif item['root']=='pr-review-head': raw=git(repo,'show',f'{review}:{item["path"]}',raw=True)
  else: fail('unknown overlap evidence root '+str(item['root']))
  if len(raw)!=item['bytes'] or sha(raw)!=item['sha256']: fail('raw overlap pin mismatch '+item['path'])
  for line,row in parse_evidence(raw,item['path']):
   sid=pick(row,ALIASES['source_id']);loc=row.get('locale')
   if not isinstance(sid,str) or sid not in selected_ids or loc not in LOCALES: continue
   status=normalize_status(pick(row,ALIASES['status']))
   if status not in TERMINAL: continue
   cell=base_by[(sid,loc)]
   if pick(row,ALIASES['source_sha'])==cell['source_sha256'] and pick(row,ALIASES['target_sha'])==cell['target_sha256']:
    prior[(sid,loc)].append({'status':status,'root':item['root'],'path':item['path'],'line':line,
      'batch':row.get('batch') or row.get('review_batch'),'finding_id':row.get('finding_id')})

 before_catalogs={};after_catalogs={};changed=set()
 for loc in LOCALES:
  path=f'web/src/lib/locales/ui-labels.{loc}.json'
  raw_before=git(repo,'show',f'{review}:{path}',raw=True);raw_after=git(repo,'show',f'{application}:{path}',raw=True)
  if sha(raw_before)!=m['catalog_sha256_before'][path] or sha(raw_after)!=m['catalog_sha256_after'][path]: fail('catalog file hash mismatch '+loc)
  before_catalogs[loc]=json.loads(raw_before.decode());after_catalogs[loc]=json.loads(raw_after.decode())
  if set(before_catalogs[loc])!=set(source_ids) or set(after_catalogs[loc])!=set(source_ids): fail('catalog key inventory mismatch '+loc)
  for sid in source_ids:
   old=before_catalogs[loc][sid];new=after_catalogs[loc][sid]
   if old!=new: changed.add((sid,loc))
   if new is None or isinstance(new,str) and not new.strip(): fail('blank target '+str((sid,loc)))
 if changed!=set(patch_by): fail('catalog edits do not match exact correction ledger')

 for row in before:
  key=pair(row);matches=prior.get(key,[]);statuses=sorted({x['status'] for x in matches})
  disp='conflict' if len(statuses)>1 else ('prior_'+statuses[0] if statuses else 'new')
  if row['prior_exact_matches']!=matches or row['disposition']!=disp: fail('exact overlap mismatch '+str(key))
  if row['source_index']!=source_ids.index(row['source_id']) or row['source_sha256']!=value_sha(row['source_id']): fail('source index/hash mismatch '+str(key))
  old=before_catalogs[key[1]][key[0]];new=after_catalogs[key[1]][key[0]]
  if old!=row['target_text'] or value_sha(old)!=row['target_sha256']: fail('baseline target mismatch '+str(key))
  finalrow=final_by[key];audit=audit_by[key];decision=decision_by.get(key);planrow=plan_by.get(key);patch=patch_by.get(key)
  root=root_by.get(key)
  if planrow:
   if patch is None or root is None: fail('missing application/root record '+str(key))
   if new!=planrow['final_target'] or value_sha(new)!=planrow['final_target_sha256']: fail('applied final target mismatch '+str(key))
   if patch['source_sha256']!=row['source_sha256'] or patch['baseline_target_sha256']!=row['target_sha256'] or patch['current_target_sha256']!=value_sha(new): fail('application source/old/new hash mismatch '+str(key))
   if patch['application_head']!=application or patch['application_tree']!=m['application_tree'] or patch['application_parent']!=review: fail('application commit pin mismatch '+str(key))
   if root['review_head']!=review or root['review_tree']!=m['review_tree'] or root['source_sha256']!=row['source_sha256'] or root['baseline_target_sha256']!=row['target_sha256']: fail('root head/source/old hash mismatch '+str(key))
   if old!=row['target_text'] or root['final_target']!=new: fail('root text/application mismatch '+str(key))
   if row['disposition'] not in ('new','prior_correction-needed'): fail('correction applied to noncorrection row '+str(key))
   expected_status='corrected';expected_decision='corrected' if row['disposition']=='new' else 'corrected-prior'
   if patch['root_disposition']!=root['disposition']: fail('patch/root disposition mismatch '+str(key))
  else:
   if new!=old: fail('unledgered catalog edit '+str(key))
   expected_status='accepted';expected_decision='accepted' if row['disposition']=='new' else 'accepted-carry'
   if row['disposition'] not in ('new','prior_accepted'): fail('unresolved exact terminal status '+str(key))
  if finalrow['decision']!=expected_decision or finalrow['status']!=expected_status: fail('final selection status mismatch '+str(key))
  if finalrow['target_text']!=new or finalrow['target_sha256']!=value_sha(new): fail('final target mismatch '+str(key))
  if audit['status']!=expected_status or audit['target_text']!=new or audit['target_sha256']!=value_sha(new): fail('audit target/status mismatch '+str(key))
  if placeholders(row['source_id'])!=placeholders(new) or audit['placeholders_source']!=placeholders(row['source_id']) or audit['placeholders_target']!=placeholders(new) or not audit['placeholders_preserved']: fail('placeholder mismatch '+str(key))
  if audit['icu_message_source']!=icu(row['source_id']) or audit['icu_message_target']!=icu(new) or icu(row['source_id']) or icu(new): fail('ICU check mismatch '+str(key))
  if not audit['protected_literals_checked'] or not audit['protected_literals_preserved']: fail('protected literal evidence missing '+str(key))
  if row['source_index']==263:
   if (key[1]=='hi' and 'सीआईडीआर' not in new) or (key[1]!='hi' and 'CIDR' not in new): fail('CIDR technical term missing '+str(key))
  if row['source_index']==264 and ('Soulseek' not in new or 'slskr' not in new): fail('protected product terms missing '+str(key))
  if row['source_index']==270 and 'API' not in new: fail('API protected literal missing '+str(key))
  if row['source_index']==274 and 'Pod' not in new: fail('Pod protected literal missing '+str(key))
  if not audit['reviewed_context'] or not audit['semantic_review_result']: fail('semantic/context evidence missing '+str(key))
  if row['disposition']=='new':
   if decision is None or decision['reviewed_target_after']!=new or decision['fresh_disposition']!=expected_status: fail('fresh decision mismatch '+str(key))
  elif decision is not None: fail('nonfresh cell in decisions '+str(key))

 if {pair(r) for r in decisions}!={pair(r) for r in before if r['disposition']=='new'}: fail('fresh decision membership mismatch')
 if {pair(r) for r in carries}!={pair(r) for r in before if r['disposition']=='prior_accepted'}: fail('carry membership mismatch')
 if exclusions or conflicts or recon: fail('unresolved exclusions/conflicts remain')
 if any(r['native_speaker_approval'] for r in audits) or m['native_speaker_approval']: fail('native speaker approval incorrectly claimed')

 pins=json.loads((bundle/'source-pins.json').read_text(encoding='utf-8'));context=m['source_context'];raw_context=(bundle/context['file']).read_bytes()
 if sha(raw_context)!=context['evidence_text_sha256']: fail('source context hash mismatch')
 if set(pins['sha256'])!=set(context['runtime_files']): fail('source context file list mismatch')
 for path,digest in pins['sha256'].items():
  raw=git(repo,'show',f'{source}:{path}',raw=True)
  if sha(raw)!=digest or git(repo,'rev-parse',f'{source}:{path}')!=pins['git_blob_ids'][path]: fail('source file pin mismatch '+path)
  if git(repo,'rev-parse',f'{review}:{path}')!=pins['git_blob_ids'][path]: fail('review-head caller file differs '+path)
 visual=m['visual_check']
 if visual['status']!='blocked' or sha((bundle/visual['file']).read_bytes())!=visual['sha256'] or not m['browser_recapture_required']: fail('visual status/hash mismatch')
 if m['placeholder_and_literal_checks']!={'cells_checked':240,'placeholder_sets_preserved':True,'icu_messages':0,'protected_literals_checked':True,'protected_literals_changed':0}: fail('placeholder/literal census mismatch')
 expected_sums=[f'{sha(p.read_bytes())}  {p.name}' for p in sorted(bundle.iterdir()) if p.is_file() and p.name!='SHA256SUMS']
 if (bundle/'SHA256SUMS').read_text(encoding='utf-8').splitlines()!=expected_sums: fail('bundle SHA256SUMS mismatch')
 print('PASS: 240 exact cells; 25 fresh (22 accepted, 3 corrected), 204 accepted carries, 11 prior correction-needed cells corrected; 14 root-reviewed corrections (8 accepted as proposed, 6 refined); zero holds/conflicts. Verified all exact overlap inputs, source/current/final hashes, 10 source caller blobs, placeholders/ICU/protected literals, and bundle checksums.')

if __name__=='__main__': main()
