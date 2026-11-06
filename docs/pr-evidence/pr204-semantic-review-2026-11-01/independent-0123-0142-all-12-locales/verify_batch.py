#!/usr/bin/env python3
"""Verify exact-head semantic evidence for slskR source indices 123–142."""
import argparse,collections,hashlib,json,re,subprocess
from pathlib import Path
LOCALES=['ar','de','es','fr','hi','id','ja','ko','pt-BR','vi','zh-Hans','zh-Hant']
TERMINAL={'accepted','correction-needed','held','keep','corrected'}
HIGH_CATALOG_PATHS={f'web/src/lib/locales/ui-labels.{l}.json' for l in ('ar','de','es','fr','hi')}
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
 m=json.loads((bundle/'manifest.json').read_text(encoding='utf8'));head=m['review_head'];source=m['source_catalog_head']
 if git(repo,'rev-parse',f'{head}^{{tree}}')!=m['review_tree'] or git(repo,'rev-parse',f'{source}^{{tree}}')!=m['source_catalog_tree']:die('head/tree pin mismatch')
 git(repo,'cat-file','-e',f'{head}^{{commit}}');git(repo,'cat-file','-e',f'{source}^{{commit}}')
 changed=git(repo,'diff','--name-only',source,head).splitlines()
 if any(not (p.startswith('docs/') or p in HIGH_CATALOG_PATHS) for p in changed):die('unexpected runtime/source change after pinned source head')
 if m.get('catalog_review_head')!=head or m.get('catalog_review_tree')!=m['review_tree']:die('catalog review pin mismatch')
 # Confirm every catalog change since the source snapshot is accounted for by the two prior correction ledgers.
 bundles=[
  ('docs/pr-evidence/pr204-semantic-review-2026-11-01/applied-high-confidence-corrections-2026-11-01','cb1fc0c0d51ff6cf136862429530399755763bb3','f4d295b2df50fbce0d56c7b0b94b35ea87211d36',11),
  ('docs/pr-evidence/pr204-semantic-review-2026-11-01/applied-high-confidence-corrections-0103-0122-2026-11-01','d07b19ab95a76981ed0e3e13f2fe28f997b5e23a','e3f7c25e88681c12b05390656b09e49e8ac0f116',4)]
 expected_changes=set()
 for rel,base,app,count in bundles:
  bm=json.loads(git(repo,'show',f'{head}:{rel}/manifest.json',raw=True).decode('utf8'));ledger_raw=git(repo,'show',f'{head}:{rel}/applied-corrections.jsonl',raw=True)
  if bm['applied_corrections']!=count or sha(ledger_raw)!=bm['correction_ledger_sha256']:die('prior correction ledger pin mismatch')
  if git(repo,'rev-parse',f'{base}^{{tree}}')!=bm['application_parent_tree'] or git(repo,'rev-parse',f'{app}^{{tree}}')!=bm.get('application_tree',git(repo,'rev-parse',f'{app}^{{tree}}')):die('prior correction commit/tree mismatch')
  rows=[json.loads(line) for line in ledger_raw.decode('utf8').splitlines() if line.strip()]
  if len(rows)!=count:die('prior correction row count mismatch')
  for row in rows:
   key=(row['source_id'],row['locale'])
   if key in expected_changes:die('duplicate correction across prior application bundles')
   expected_changes.add(key)
   path=f'web/src/lib/locales/ui-labels.{row["locale"]}.json';before=json.loads(git(repo,'show',f'{base}:{path}',raw=True).decode('utf8'));after=json.loads(git(repo,'show',f'{app}:{path}',raw=True).decode('utf8'))
   if before.get(row['source_id'])!=row['previous_target'] or target_sha(before[row['source_id']])!=row['previous_target_sha256'] or after.get(row['source_id'])!=row['current_target'] or target_sha(after[row['source_id']])!=row['target_sha256']:die('prior correction source/target hash mismatch')
 # Ensure the pinned current catalog differs from the source snapshot only at corrected ledger cells.
 for loc in LOCALES:
  path=f'web/src/lib/locales/ui-labels.{loc}.json';base=json.loads(git(repo,'show',f'{source}:{path}',raw=True).decode('utf8'));now=json.loads(git(repo,'show',f'{head}:{path}',raw=True).decode('utf8'))
  if {(sid,loc) for sid in base if base[sid]!=now[sid]}!={pair for pair in expected_changes if pair[1]==loc}:die(f'unledgered catalog change since source snapshot: {loc}')
 # Read the exact current catalog snapshots.
 cats={};keys=None;populated=structured=0
 for loc in LOCALES:
  path=f'web/src/lib/locales/ui-labels.{loc}.json';raw=git(repo,'show',f'{head}:{path}',raw=True)
  if sha(raw)!=m['direct_catalog']['catalog_sha256'][path]:die(f'catalog SHA mismatch: {loc}')
  cat=json.loads(raw.decode('utf8'));cats[loc]=cat
  if keys is None:keys=set(cat)
  elif set(cat)!=keys:die('catalog keysets differ')
  for v in cat.values():
   if v is None or (isinstance(v,str) and not v.strip()):die(f'blank target in {loc}')
   populated+=1;structured+=isinstance(v,(dict,list))
 if len(keys)!=5437 or populated!=65244 or structured!=15:die('catalog census mismatch')
 ids=sorted(keys);expected_ids=ids[123:143]
 def read_jsonl(name):return [r for _,r in records(bundle/name,(bundle/name).read_bytes())]
 selection=read_jsonl('selection.jsonl');decisions=read_jsonl('decisions.jsonl');carries=read_jsonl('carries.jsonl');exclusions=read_jsonl('terminal-exclusions.jsonl');holds=read_jsonl('conflict-holds.jsonl')
 if (len(selection),len(decisions),len(carries),len(exclusions),len(holds))!=(240,82,127,31,0):die('window row counts mismatch')
 key=lambda r:(r['source_id'],r['locale'])
 for rows,name in ((selection,'selection'),(decisions,'decisions'),(carries,'carries'),(exclusions,'exclusions'),(holds,'holds')):
  pairs=[key(r) for r in rows]
  if len(set(pairs))!=len(pairs):die(f'duplicate cell in {name}')
 if sorted({r['source_id'] for r in selection})!=expected_ids:die('selected IDs are not lexical indices 123–142')
 if {key(r) for r in selection}!={key(r) for r in decisions+carries+exclusions+holds}:die('decision partition mismatch')
 bysel={key(r):r for r in selection}
 for row in selection:
  sid,loc=row['source_id'],row['locale'];value=cats[loc].get(sid,'__missing__')
  if value=='__missing__' or value!=row['target_text'] or not row['populated']:die(f'current value mismatch {loc}:{sid}')
  if row['source_index']!=ids.index(sid) or row['source_sha256']!=sha(sid.encode()) or row['target_sha256']!=target_sha(value):die(f'source/target hash mismatch {loc}:{sid}')
 # Build the exact prior evidence file list at the pinned review commit, excluding this bundle.
 audit_files=[audit/'findings.jsonl',audit/'carried-findings.jsonl'];audit_files+=list((audit/'review-evidence').rglob('*.jsonl'))+list((audit/'review-evidence').rglob('*.json'));audit_files=sorted({p for p in audit_files if p.is_file()})
 paths=git(repo,'ls-tree','-r','--name-only',head,'docs/pr-evidence/pr204-semantic-review-2026-11-01').splitlines();paths=sorted(p for p in paths if p.endswith(('.jsonl','.json')))
 inputs=[]
 for p in audit_files:inputs.append(('prior-audit-7ff',p.relative_to(audit).as_posix(),p.read_bytes()))
 for rel in paths:inputs.append(('pr-review-head',rel,git(repo,'show',f'{head}:{rel}',raw=True)))
 inputs.sort(key=lambda r:(r[0],r[1]));expected_manifest=[];prior=collections.defaultdict(list)
 for root,rel,raw in inputs:
  expected_manifest.append({'root':root,'path':rel,'bytes':len(raw),'sha256':sha(raw)})
  for line,row in records(Path(rel),raw):
   sid=pick(row,'source_id','message_id','id');loc=row.get('locale')
   if sid not in expected_ids or loc not in LOCALES:continue
   status=str(pick(row,'status','review_outcome') or '').strip().lower().replace('_','-')
   if status not in TERMINAL:continue
   sel=bysel[(sid,loc)]
   if pick(row,'source_sha256')==sel['source_sha256'] and pick(row,'target_sha256','current_target_sha256')==sel['target_sha256']:
    prior[(sid,loc)].append({'status':status,'root':root,'path':rel,'line':line,'batch':row.get('batch') or row.get('review_batch'),'finding_id':row.get('finding_id')})
 recorded=read_jsonl('prior-evidence-scan-manifest.jsonl')
 if recorded!=expected_manifest or len(inputs)!=749:die('prior evidence input manifest mismatch')
 ov=m['prior_overlap_scan']
 if len(inputs)!=ov['scanned_json_evidence_files'] or sha((bundle/'prior-evidence-scan-manifest.jsonl').read_bytes())!=ov['manifest_sha256']:die('prior scan checksum/count mismatch')
 dispositions={}
 for row in selection:
  k=key(row);matches=prior.get(k,[]);statuses=sorted({r['status'] for r in matches});disp='conflict' if len(statuses)>1 else ('prior_'+statuses[0] if statuses else 'new')
  if row['prior_exact_matches']!=matches or row['disposition']!=disp:die(f'exact overlap mismatch {k}')
  dispositions[k]=disp
 if collections.Counter(dispositions.values())!=collections.Counter({'new':82,'prior_accepted':127,'prior_correction-needed':31}):die('fresh/prior partition totals mismatch')
 for row in decisions:
  k=key(row);s=bysel[k]
  if dispositions[k]!='new' or row['prior_exact_matches'] or any(row[f]!=s[f] for f in ('source_index','source_sha256','target_sha256','target_text')):die(f'fresh cell mismatch {k}')
  if (row['review_head'],row['review_tree'],row['reviewed_code_head'],row['reviewed_code_tree'])!=(head,m['review_tree'],source,m['source_catalog_tree']):die(f'review pin mismatch {k}')
  if row['status'] not in {'accepted','correction-needed'} or row['current_target_sha256_revalidated'] is not True or row['source_context_files_reviewed'] is not True:die(f'incomplete review {k}')
  if row['placeholders_source']!=ph(row['source_id']) or row['placeholders_target']!=ph(row['target_text']) or row['placeholders_preserved'] is not True:die(f'placeholder mismatch {k}')
  if row['icu_message'] is not False or row['native_speaker_approval'] is not False:die(f'ICU/native-speaker mismatch {k}')
  if row['protected_literals_preserved'] is not True:die(f'protected literal mismatch {k}')
  proposal=row.get('proposed_target')
  if proposal is None:
   if row['status']!='accepted' or row.get('issue_type') is not None:die(f'unexpected fresh finding {k}')
  elif row['status']!='correction-needed' or row['proposed_target_sha256']!=sha(proposal.encode()) or row['protected_literals_proposed_preserved'] is not True:die(f'proposal mismatch {k}')
  if row['source_id'].startswith('AcoustID') and 'AcoustID' not in row['target_text']:die(f'AcoustID protected literal lost {k}')
 for row in carries+exclusions:
  k=key(row);want='accepted' if row in carries else 'correction-needed'
  if dispositions[k]!='prior_'+want or row['status']!=want or row['prior_exact_matches']!=prior.get(k,[]):die(f'carry/exclusion mismatch {k}')
 if collections.Counter(r['status'] for r in decisions)!=collections.Counter({'accepted':80,'correction-needed':2}):die('fresh statuses mismatch')
 corrections=[{'source_index':r['source_index'],'source_id':r['source_id'],'locale':r['locale'],'current':r['target_text'],'current_sha256':r['target_sha256'],'proposal':r['proposed_target'],'proposal_sha256':r['proposed_target_sha256'],'confidence':r['confidence'],'issue_type':r['issue_type'],'applied_in_review_pass':False} for r in decisions if r['status']=='correction-needed']
 if m['correction_candidates']!=corrections or {(r['source_index'],r['locale'],r['proposed_target']) for r in decisions if r['status']=='correction-needed'}!={(137,'es','Activo'),(137,'fr','Actif')}:die('candidate set mismatch')
 ctx=m['source_context']
 if sha((bundle/ctx['file']).read_bytes())!=ctx['evidence_text_sha256']:die('source context text hash mismatch')
 for path,digest in ctx['sha256'].items():
  if sha(git(repo,'show',f'{source}:{path}',raw=True))!=digest or git(repo,'rev-parse',f'{source}:{path}')!=ctx['git_blob_ids'][path]:die(f'source code pin mismatch {path}')
 sums=(bundle/'SHA256SUMS').read_text().splitlines();expected=[f'{sha(p.read_bytes())}  {p.name}' for p in sorted(bundle.iterdir()) if p.is_file() and p.name!='SHA256SUMS']
 if sums!=expected:die('SHA256SUMS mismatch')
 print('PASS: exact source/catalog/head pins, 240-cell overlap partition, 82 fresh decisions, 127 accepted carries, 31 correction-needed exclusions, zero conflicts, 749 evidence inputs, context/placeholders/literals, and checksums')
 print('Fresh accepted: 80; moderate correction suggestions: 2 (Spanish/French Active, unapplied)')
if __name__=='__main__':main()
