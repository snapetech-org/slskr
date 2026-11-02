#!/usr/bin/env python3
"""Verify exact-head semantic evidence for slskR source indices 103–122."""
import argparse,collections,hashlib,json,re,subprocess
from pathlib import Path
LOCALES=['ar','de','es','fr','hi','id','ja','ko','pt-BR','vi','zh-Hans','zh-Hant']
TERMINAL={'accepted','correction-needed','held','keep','corrected'}
def die(msg):raise SystemExit('FAIL: '+msg)
def sha(raw):return hashlib.sha256(raw).hexdigest()
def git(repo,*args,raw=False):
 p=subprocess.run(['git',*args],cwd=repo,check=True,stdout=subprocess.PIPE)
 return p.stdout if raw else p.stdout.decode('utf8').strip()
def target_sha(value):
 raw=value.encode('utf8') if isinstance(value,str) else json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode('utf8')
 return sha(raw)
def ph(v):return sorted(set(re.findall(r'\{([^{}]+)\}',str(v))))
def records(path,raw):
 if path.suffix=='.jsonl':
  out=[]
  for n,line in enumerate(raw.decode('utf8').splitlines(),1):
   if line.strip():
    try:out.append((n,json.loads(line)))
    except json.JSONDecodeError:pass
  return out
 def walk(x):
  if isinstance(x,dict):
   yield x
   for v in x.values():yield from walk(v)
  elif isinstance(x,list):
   for v in x:yield from walk(v)
 try:return [(n+1,r) for n,r in enumerate(walk(json.loads(raw.decode('utf8'))))]
 except json.JSONDecodeError:return []
def pick(row,*names):
 for name in names:
  if row.get(name) is not None:return row[name]
 return None
def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--repo',type=Path);ap.add_argument('--prior-audit',type=Path,required=True);args=ap.parse_args()
 repo=(args.repo or Path(git(Path.cwd(),'rev-parse','--show-toplevel'))).resolve();audit=args.prior_audit.resolve();bundle=Path(__file__).resolve().parent
 manifest=json.loads((bundle/'manifest.json').read_text(encoding='utf8'));head=manifest['review_head'];source=manifest['source_catalog_head']
 if git(repo,'rev-parse',f'{head}^{{tree}}')!=manifest['review_tree']:die('review head/tree mismatch')
 if git(repo,'rev-parse',f'{source}^{{tree}}')!=manifest['source_catalog_tree']:die('source head/tree mismatch')
 git(repo,'cat-file','-e',f'{head}^{{commit}}');git(repo,'cat-file','-e',f'{source}^{{commit}}')
 changed=git(repo,'diff','--name-only',source,head).splitlines()
 allowed_catalogs={f'web/src/lib/locales/ui-labels.{loc}.json' for loc in ('ar','de','es','fr','hi')}
 if any(not (p.startswith('docs/') or p in allowed_catalogs) for p in changed):die('unexpected source/runtime change after source catalog head')
 if manifest.get('catalog_review_head')!=head or manifest.get('catalog_review_tree')!=manifest['review_tree']:die('catalog review head pin mismatch')
 # Verify that the only catalog changes since the source snapshot are the prior 11 audited corrections.
 prev_bundle=Path('docs/pr-evidence/pr204-semantic-review-2026-11-01/applied-high-confidence-corrections-2026-11-01')
 prev_manifest_raw=git(repo,'show',f'{head}:{prev_bundle.as_posix()}/manifest.json',raw=True)
 prev_manifest=json.loads(prev_manifest_raw.decode('utf8'))
 ledger_raw=git(repo,'show',f'{head}:{prev_bundle.as_posix()}/applied-corrections.jsonl',raw=True)
 if sha(ledger_raw)!=prev_manifest['correction_ledger_sha256'] or prev_manifest['applied_corrections']!=11:die('prior correction ledger pin mismatch')
 app_parent=prev_manifest['application_parent_head']
 if git(repo,'rev-parse',f'{app_parent}^{{tree}}')!=prev_manifest['application_parent_tree']:die('prior correction parent pin mismatch')
 prior_rows=[json.loads(line) for line in ledger_raw.decode('utf8').splitlines() if line.strip()]
 diffs=set()
 for loc in LOCALES:
  cp=f'web/src/lib/locales/ui-labels.{loc}.json';before_raw=git(repo,'show',f'{app_parent}:{cp}',raw=True);after_raw=git(repo,'show',f'{head}:{cp}',raw=True)
  if sha(after_raw)!=prev_manifest['catalog_sha256_after'][cp]:die(f'prior correction after-catalog hash mismatch: {loc}')
  before=json.loads(before_raw.decode('utf8'));after=json.loads(after_raw.decode('utf8'))
  if sha(before_raw)!=prev_manifest['catalog_sha256_before'][cp]:die(f'prior correction before-catalog hash mismatch: {loc}')
  for sid in before:
   if before[sid]!=after[sid]:diffs.add((sid,loc))
 if diffs!={(r['source_id'],r['locale']) for r in prior_rows}:die('catalog changes are not limited to prior exact correction ledger')
 for r in prior_rows:
  cp=f'web/src/lib/locales/ui-labels.{r["locale"]}.json';before=json.loads(git(repo,'show',f'{app_parent}:{cp}',raw=True).decode('utf8'));after=json.loads(git(repo,'show',f'{head}:{cp}',raw=True).decode('utf8'))
  if before.get(r['source_id'])!=r['previous_target'] or sha(r['previous_target'].encode('utf8'))!=r['previous_target_sha256'] or after.get(r['source_id'])!=r['current_target'] or sha(r['current_target'].encode('utf8'))!=r['target_sha256']:die('prior exact correction target mismatch')
 cats={};keys=None;structured=populated=0
 for loc in LOCALES:
  path=f'web/src/lib/locales/ui-labels.{loc}.json';raw=git(repo,'show',f'{head}:{path}',raw=True)
  if sha(raw)!=manifest['direct_catalog']['catalog_sha256'][path]:die(f'catalog hash mismatch: {loc}')
  cat=json.loads(raw.decode('utf8'));cats[loc]=cat
  if keys is None:keys=set(cat)
  elif set(cat)!=keys:die('catalog keysets differ')
  for value in cat.values():
   if value is None or (isinstance(value,str) and not value.strip()):die(f'blank target: {loc}')
   populated+=1;structured+=isinstance(value,(dict,list))
 if len(keys)!=5437 or populated!=65244 or structured!=15:die('catalog census mismatch')
 ids=sorted(keys);expected_ids=ids[103:123]
 selection=[r for _,r in records(bundle/'selection.jsonl',(bundle/'selection.jsonl').read_bytes())]
 decisions=[r for _,r in records(bundle/'decisions.jsonl',(bundle/'decisions.jsonl').read_bytes())]
 carries=[r for _,r in records(bundle/'carries.jsonl',(bundle/'carries.jsonl').read_bytes())]
 exclusions=[r for _,r in records(bundle/'terminal-exclusions.jsonl',(bundle/'terminal-exclusions.jsonl').read_bytes())]
 holds=[r for _,r in records(bundle/'conflict-holds.jsonl',(bundle/'conflict-holds.jsonl').read_bytes())]
 if (len(selection),len(decisions),len(carries),len(exclusions),len(holds))!=(240,71,117,52,0):die('row counts mismatch')
 key=lambda r:(r['source_id'],r['locale'])
 for rows,name in ((selection,'selection'),(decisions,'decisions'),(carries,'carries'),(exclusions,'exclusions'),(holds,'holds')):
  pairs=[key(r) for r in rows]
  if len(set(pairs))!=len(pairs):die(f'duplicate cell in {name}')
 selected_ids=sorted({r['source_id'] for r in selection})
 if selected_ids!=expected_ids:die('selected source IDs are not lexical indices 103–122')
 if {key(r) for r in selection}!={key(r) for r in decisions+carries+exclusions+holds}:die('decision partition mismatch')
 selection_by={key(r):r for r in selection}
 for row in selection:
  sid,loc=row['source_id'],row['locale'];value=cats[loc].get(sid,'__missing__')
  if value=='__missing__' or value!=row['target_text']:die(f'target mismatch {loc}:{sid}')
  if row['source_index']!=ids.index(sid) or row['source_sha256']!=sha(sid.encode()) or row['target_sha256']!=target_sha(value):die(f'hash/index mismatch {loc}:{sid}')
  if not row['populated']:die(f'unpopulated slot {loc}:{sid}')
 # Recreate exact prior evidence input set. PR evidence is read from the pinned review commit,
 # so this bundle cannot accidentally include itself after it is copied or committed.
 audit_files=[audit/'findings.jsonl',audit/'carried-findings.jsonl']
 audit_files += list((audit/'review-evidence').rglob('*.jsonl'))+list((audit/'review-evidence').rglob('*.json'))
 audit_files=sorted({p for p in audit_files if p.is_file()})
 evidence_paths=git(repo,'ls-tree','-r','--name-only',head,'docs/pr-evidence/pr204-semantic-review-2026-11-01').splitlines()
 evidence_paths=sorted(p for p in evidence_paths if p.endswith(('.jsonl','.json')))
 inputs=[]
 for p in audit_files:inputs.append(('prior-audit-7ff',p.relative_to(audit).as_posix(),p.read_bytes()))
 for rel in evidence_paths:inputs.append(('pr-review-head',rel,git(repo,'show',f'{head}:{rel}',raw=True)))
 inputs.sort(key=lambda item:(item[0],item[1]));expected_manifest=[];prior=collections.defaultdict(list)
 for root,rel,raw in inputs:
  expected_manifest.append({'root':root,'path':rel,'bytes':len(raw),'sha256':sha(raw)})
  suffix=Path(rel).suffix
  for line,row in records(Path(rel),raw):
   sid=pick(row,'source_id','message_id','id');loc=row.get('locale')
   if sid not in expected_ids or loc not in LOCALES:continue
   status=str(pick(row,'status','review_outcome') or '').strip().lower().replace('_','-')
   if status not in TERMINAL:continue
   ssha=pick(row,'source_sha256');tsha=pick(row,'target_sha256','current_target_sha256');sel=selection_by[(sid,loc)]
   if ssha==sel['source_sha256'] and tsha==sel['target_sha256']:
    prior[(sid,loc)].append({'status':status,'root':root,'path':rel,'line':line,'batch':row.get('batch') or row.get('review_batch'),'finding_id':row.get('finding_id')})
 expected_manifest.sort(key=lambda r:(r['root'],r['path']))
 recorded=[r for _,r in records(bundle/'prior-evidence-scan-manifest.jsonl',(bundle/'prior-evidence-scan-manifest.jsonl').read_bytes())]
 if recorded!=expected_manifest:die('prior evidence manifest differs from rehashed inputs')
 ov=manifest['prior_overlap_scan']
 if len(inputs)!=740 or len(inputs)!=ov['scanned_json_evidence_files'] or sha((bundle/'prior-evidence-scan-manifest.jsonl').read_bytes())!=ov['manifest_sha256']:die('prior scan manifest hash/count mismatch')
 # Recompute exact dispositions from current values and prior records.
 disp={}
 for row in selection:
  matches=prior.get(key(row),[]);statuses=sorted({m['status'] for m in matches})
  if len(statuses)>1:actual='conflict'
  elif statuses:actual='prior_'+statuses[0]
  else:actual='new'
  if row['prior_exact_matches']!=matches or row['disposition']!=actual:die(f'exact overlap mismatch {row["locale"]}:{row["source_id"]}')
  disp[key(row)]=actual
 if collections.Counter(disp.values())!=collections.Counter({'new':71,'prior_accepted':117,'prior_correction-needed':52}):die('fresh/prior counts mismatch')
 for row in decisions:
  k=key(row);s=selection_by[k]
  if disp[k]!='new' or row['prior_exact_matches'] or row['source_index']!=s['source_index'] or row['source_sha256']!=s['source_sha256'] or row['target_sha256']!=s['target_sha256'] or row['target_text']!=s['target_text']:die(f'fresh cell mismatch {k}')
  if (row['review_head'],row['review_tree'],row['reviewed_code_head'],row['reviewed_code_tree'])!=(head,manifest['review_tree'],source,manifest['source_catalog_tree']):die(f'pin mismatch {k}')
  if row['status'] not in {'accepted','correction-needed'} or row['current_target_sha256_revalidated'] is not True or row['source_context_files_reviewed'] is not True:die(f'incomplete review {k}')
  if row['placeholders_source']!=ph(row['source_id']) or row['placeholders_target']!=ph(row['target_text']) or row['placeholders_preserved'] is not True:die(f'placeholder mismatch {k}')
  if row['icu_message'] is not False or row['native_speaker_approval'] is not False:die(f'ICU/native speaker metadata mismatch {k}')
  if not row['protected_literals_preserved']:die(f'protected literal mismatch {k}')
  proposal=row.get('proposed_target')
  if proposal is None:
   if row['status']!='accepted' or row.get('issue_type') is not None:die(f'unexpected finding {k}')
  else:
   if row['status']!='correction-needed' or row['proposed_target_sha256']!=sha(proposal.encode()):die(f'proposal mismatch {k}')
   if row['protected_literals_proposed_preserved'] is not True or ph(proposal)!=ph(row['source_id']):die(f'proposal invariant mismatch {k}')
 for row in carries+exclusions:
  k=key(row);s=selection_by[k];want='accepted' if row in carries else 'correction-needed'
  if disp[k]!='prior_'+want or row['status']!=want or row['prior_exact_matches']!=prior.get(k,[]):die(f'carry/exclusion mismatch {k}')
 correction_candidates=manifest['correction_candidates']
 actual=[{'source_index':r['source_index'],'source_id':r['source_id'],'locale':r['locale'],'current':r['target_text'],'current_sha256':r['target_sha256'],'proposal':r['proposed_target'],'proposal_sha256':r['proposed_target_sha256'],'confidence':r['confidence'],'issue_type':r['issue_type'],'applied_in_review_pass':False} for r in decisions if r['status']=='correction-needed']
 if correction_candidates!=actual:die('correction candidates mismatch')
 high={(r['source_index'],r['locale']) for r in decisions if r['confidence']=='high' and r['status']=='correction-needed'}
 if high!={(104,'de'),(104,'fr'),(105,'de'),(105,'es')}:die('high-confidence correction set mismatch')
 context=manifest['source_context']
 if sha((bundle/context['file']).read_bytes())!=context['evidence_text_sha256']:die('context text hash mismatch')
 for path,digest in context['sha256'].items():
  if sha(git(repo,'show',f'{source}:{path}',raw=True))!=digest or git(repo,'rev-parse',f'{source}:{path}')!=context['git_blob_ids'][path]:die(f'source context pin mismatch: {path}')
 if manifest['window_accounting']['fresh_statuses']!={'accepted':64,'correction-needed':7}:die('manifest status totals mismatch')
 sums=(bundle/'SHA256SUMS').read_text(encoding='utf8').splitlines();expected=[]
 for p in sorted(bundle.iterdir()):
  if p.is_file() and p.name!='SHA256SUMS':expected.append(f'{sha(p.read_bytes())}  {p.name}')
 if sums!=expected:die('SHA256SUMS mismatch')
 print('PASS: exact source/head/tree pins, 240-cell exact-overlap partition, 71 fresh decisions, 117 carries, 52 exclusions, zero conflicts, source context, placeholders/protected literals, proposals, and checksums')
 print(f'Prior evidence inputs rehashed: {len(inputs)}; fresh accepted: 64; fresh correction-needed: 7; high-confidence proposals: {len(high)}')
if __name__=='__main__':main()
