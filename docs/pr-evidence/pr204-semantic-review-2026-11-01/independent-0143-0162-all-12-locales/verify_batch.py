#!/usr/bin/env python3
"""Verify exact-head semantic evidence for slskR source indices 143–162."""
import argparse, collections, hashlib, json, re, subprocess
from pathlib import Path
LOCALES=['ar','de','es','fr','hi','id','ja','ko','pt-BR','vi','zh-Hans','zh-Hant']
TERMINAL={'accepted','correction-needed','held','keep','corrected'}
PATCH_KEYS={(157,'id'),(158,'ar'),(158,'de'),(158,'es'),(158,'fr'),(158,'hi'),(158,'id'),(159,'ar')}
def die(msg): raise SystemExit('FAIL: '+msg)
def sha(raw): return hashlib.sha256(raw).hexdigest()
def vsha(value):
 raw=value.encode('utf-8') if isinstance(value,str) else json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode('utf-8')
 return sha(raw)
def ph(value): return sorted(set(re.findall(r'\{([^{}]+)\}',str(value))))
def git(repo,*args,raw=False):
 p=subprocess.run(['git',*args],cwd=repo,check=True,stdout=subprocess.PIPE)
 return p.stdout if raw else p.stdout.decode('utf-8').strip()
def rows_from(raw,path):
 if Path(path).suffix=='.jsonl':
  out=[]
  for n,line in enumerate(raw.decode('utf-8').splitlines(),1):
   if line.strip():
    try: out.append((n,json.loads(line)))
    except json.JSONDecodeError: pass
  return out
 def walk(obj):
  if isinstance(obj,dict):
   yield obj
   for v in obj.values(): yield from walk(v)
  elif isinstance(obj,list):
   for v in obj: yield from walk(v)
 try: return [(n+1,r) for n,r in enumerate(walk(json.loads(raw.decode('utf-8'))))]
 except json.JSONDecodeError: return []
def pick(row,*fields):
 for f in fields:
  if row.get(f) is not None:return row[f]
 return None
def read_jsonl(path):
 return [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines() if line.strip()]
def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--repo',type=Path,required=True);ap.add_argument('--prior-audit',type=Path,required=True);args=ap.parse_args()
 repo=args.repo.resolve();audit=args.prior_audit.resolve();bundle=Path(__file__).resolve().parent;m=json.loads((bundle/'manifest.json').read_text(encoding='utf-8'))
 review=m['review_head'];app=m['application_head'];source=m['source_catalog_head']
 for ref,key in ((review,'review_tree'),(app,'application_tree'),(source,'source_catalog_tree')):
  if git(repo,'rev-parse',f'{ref}^{{tree}}')!=m[key]:die(f'commit/tree mismatch {ref}')
 if git(repo,'rev-parse',f'{app}^{{commit}}')!=app or git(repo,'rev-parse',f'{source}^{{commit}}')!=source:die('missing pinned commit')
 if git(repo,'rev-parse',f'{app}^')!=review:die('application parent is not exact reviewed baseline')
 if git(repo,'rev-parse','HEAD')!=app and git(repo,'merge-base','--is-ancestor',app,'HEAD')!='':die('application commit is not ancestor of checked-out docs head')
 paths=[f'web/src/lib/locales/ui-labels.{l}.json' for l in LOCALES]
 cats_before={};cats_after={}
 for loc in LOCALES:
  path=f'web/src/lib/locales/ui-labels.{loc}.json';before_raw=git(repo,'show',f'{review}:{path}',raw=True);after_raw=git(repo,'show',f'{app}:{path}',raw=True)
  if sha(before_raw)!=m['direct_catalog']['catalog_sha256_before'][path]:die(f'baseline catalog SHA mismatch: {loc}')
  if sha(after_raw)!=m['direct_catalog']['catalog_sha256_after_application'][path]:die(f'application catalog SHA mismatch: {loc}')
  cats_before[loc]=json.loads(before_raw.decode('utf-8'));cats_after[loc]=json.loads(after_raw.decode('utf-8'))
 keyset=set(cats_after['ar']);populated=structured=0
 for loc,cat in cats_after.items():
  if set(cat)!=keyset:die('locale keysets differ')
  for val in cat.values():
   if val is None or (isinstance(val,str) and not val.strip()):die(f'blank target {loc}')
   populated+=1;structured+=isinstance(val,(dict,list))
 if (len(keyset),populated,structured)!=(5437,65244,15):die('catalog census mismatch')
 ids=sorted(keyset);expected_ids=ids[143:163]
 selection=read_jsonl(bundle/'selection.jsonl');pre=read_jsonl(bundle/'selection-before-corrections.jsonl');decisions=read_jsonl(bundle/'decisions.jsonl');carries=read_jsonl(bundle/'carries.jsonl');exclusions=read_jsonl(bundle/'terminal-exclusions.jsonl');holds=read_jsonl(bundle/'conflict-holds.jsonl');patches=read_jsonl(bundle/'applied-corrections.jsonl')
 if (len(selection),len(pre),len(decisions),len(carries),len(exclusions),len(holds),len(patches))!=(240,240,87,103,42,0,8):die('bundle row count mismatch')
 pair=lambda r:(r['source_id'],r['locale'])
 for group,name in ((selection,'selection'),(pre,'baseline selection'),(decisions,'decisions'),(carries,'carries'),(exclusions,'exclusions'),(holds,'holds'),(patches,'patches')):
  pairs=[pair(r) for r in group]
  if len(set(pairs))!=len(pairs):die(f'duplicate cell in {name}')
 if sorted({r['source_id'] for r in selection})!=expected_ids:die('source key range does not match lexical indices 143–162')
 by_final={pair(r):r for r in selection};by_pre={pair(r):r for r in pre}
 if set(by_final)!=set(by_pre):die('pre/final selected cell set differs')
 if set(by_final)!={pair(r) for r in decisions+carries+exclusions+holds+patches}:die('final decision partition mismatch')
 # Exact pre-application overlap scan from the immutable review head.
 manifest_rows=read_jsonl(bundle/'prior-evidence-scan-manifest.jsonl');manifest_bytes=(bundle/'prior-evidence-scan-manifest.jsonl').read_bytes()
 if len(manifest_rows)!=763 or sha(manifest_bytes)!=m['prior_overlap_scan']['manifest_sha256']:die('prior scan manifest checksum/count mismatch')
 prior=collections.defaultdict(list);expected_manifest=[]
 for item in manifest_rows:
  if item['root']=='prior-audit-7ff': raw=(audit/item['path']).read_bytes()
  elif item['root']=='pr-review-head': raw=git(repo,'show',f"{review}:{item['path']}",raw=True)
  else: die('unknown overlap evidence root')
  if len(raw)!=item['bytes'] or sha(raw)!=item['sha256']:die(f"prior evidence raw file mismatch: {item['root']}:{item['path']}")
  expected_manifest.append(item)
  for line_no,record in rows_from(raw,item['path']):
   sid=pick(record,'source_id','message_id','id');loc=record.get('locale')
   if sid not in expected_ids or loc not in LOCALES:continue
   status=str(pick(record,'status','review_outcome') or '').strip().lower().replace('_','-')
   if status not in TERMINAL:continue
   cell=by_pre[(sid,loc)]
   if pick(record,'source_sha256')==cell['source_sha256'] and pick(record,'target_sha256','current_target_sha256')==cell['target_sha256']:
    prior[(sid,loc)].append({'status':status,'root':item['root'],'path':item['path'],'line':line_no,'batch':record.get('batch') or record.get('review_batch'),'finding_id':record.get('finding_id')})
 if collections.Counter(r['disposition'] for r in pre)!=collections.Counter({'new':87,'prior_accepted':103,'prior_correction-needed':50}):die('baseline overlap partition mismatch')
 by_patch={pair(r):r for r in patches}
 for cell in pre:
  k=pair(cell);matches=prior.get(k,[]);statuses=sorted({r['status'] for r in matches});disp='conflict' if len(statuses)>1 else ('prior_'+statuses[0] if statuses else 'new')
  if cell['prior_exact_matches']!=matches or cell['disposition']!=disp:die(f"baseline exact overlap mismatch {k}")
  row=by_final[k]
  if (cell['source_index'],cell['source_sha256'])!=(row['source_index'],row['source_sha256']):die(f'identity mismatch {k}')
  if row['source_index']!=ids.index(row['source_id']) or row['source_sha256']!=sha(row['source_id'].encode()):die(f'source hash mismatch {k}')
  if cell['target_text']!=cats_before[k[1]][k[0]] or cell['target_sha256']!=vsha(cell['target_text']):die(f'baseline target mismatch {k}')
  if row['disposition']=='corrected-this-pass':
   if k not in by_patch:die(f'correction ledger missing {k}')
   p=by_patch[k]
   if p['previous_target']!=cell['target_text'] or p['previous_target_sha256']!=cell['target_sha256'] or p['prior_exact_correction_needed_matches']!=matches:die(f'correction baseline mismatch {k}')
   if p['source_sha256']!=cell['source_sha256'] or p['confidence']!='high' or p['applied_in_catalog_commit'] is not True:die(f'correction application evidence mismatch {k}')
   if row['pre_application_target_text']!=cell['target_text'] or row['pre_application_target_sha256']!=cell['target_sha256'] or row['target_text']!=p['current_target'] or row['target_sha256']!=p['current_target_sha256'] or row['prior_exact_matches']!=[]:die(f'final corrected selection mismatch {k}')
   if cats_after[k[1]][k[0]]!=p['current_target'] or vsha(cats_after[k[1]][k[0]])!=p['current_target_sha256']:die(f'final correction catalog mismatch {k}')
  else:
   if row!=cell:die(f'unexpected changed selection row {k}')
   if row['target_text']!=cats_after[k[1]][k[0]] or row['target_sha256']!=vsha(row['target_text']):die(f'final target mismatch {k}')
  if row['target_text']!=cats_after[k[1]][k[0]]:die(f'current catalog value mismatch {k}')
 # Exact changes from review baseline to correction application are only the 8 ledger cells.
 changed=set()
 for loc in LOCALES:
  for sid in keyset:
   if cats_before[loc].get(sid)!=cats_after[loc].get(sid):changed.add((sid,loc))
 if changed!=set(by_patch):die('application catalog diff is not exactly the 8 reviewed cells')
 if collections.Counter(r['disposition'] for r in selection)!=collections.Counter({'new':87,'prior_accepted':103,'prior_correction-needed':42,'corrected-this-pass':8}):die('final selection partition mismatch')
 for group,wanted in ((decisions,'new'),(carries,'prior_accepted'),(exclusions,'prior_correction-needed')):
  for r in group:
   k=pair(r);sel=by_final[k]
   if sel['disposition']!=wanted:die(f'wrong partition row {k}')
   if any(r.get(f)!=sel.get(f) for f in ('source_index','source_sha256','target_sha256','target_text')):die(f'row values mismatch {k}')
 for r in decisions:
  k=pair(r)
  if r['prior_exact_matches'] or r['status'] not in {'accepted','correction-needed'}:die(f'incomplete fresh disposition {k}')
  if (r['review_head'],r['review_tree'],r['reviewed_code_head'],r['reviewed_code_tree'])!=(review,m['review_tree'],source,m['source_catalog_tree']):die(f'review pin mismatch {k}')
  if r['current_target_sha256_revalidated'] is not True or r['source_context_files_reviewed'] is not True:die(f'context/hash review missing {k}')
  if r['placeholders_source']!=ph(r['source_id']) or r['placeholders_target']!=ph(r['target_text']) or r['placeholders_preserved'] is not True:die(f'placeholder mismatch {k}')
  if r['icu_message'] is not False or r['protected_literals_preserved'] is not True or r['native_speaker_approval'] is not False:die(f'ICU/literal/native review mismatch {k}')
  proposal=r.get('proposed_target')
  if proposal is None:
   if r['status']!='accepted' or r.get('issue_type') is not None:die(f'unexpected fresh correction flag {k}')
  elif r['status']!='correction-needed' or r.get('proposed_target_sha256')!=vsha(proposal):die(f'fresh proposal hash/status mismatch {k}')
 if collections.Counter(r['status'] for r in decisions)!=collections.Counter({'accepted':84,'correction-needed':3}):die('fresh status totals mismatch')
 # Exact prior status records must still classify unchanged carries and exclusions.
 for r in carries+exclusions:
  k=pair(r);want='accepted' if r in carries else 'correction-needed'
  if r['status']!=want or r['prior_exact_matches']!=prior.get(k,[]) or not r['exact_prior_status_revalidated']:die(f'prior terminal mismatch {k}')
 # The affected cells are only the three fresh moderate suggestions and no moderate proposal was applied.
 expected_props={(146,'fr','Téléchargements actifs en mode essaim'),(155,'fr','Ajouter une redirection'),(161,'hi','आइटम जोड़ें:')}
 got={(r['source_index'],r['locale'],r['proposed_target']) for r in decisions if r['status']=='correction-needed'}
 if got!=expected_props:die('fresh correction suggestion set mismatch')
 if any(r['confidence']!='high' for r in patches):die('moderate/high confidence application policy mismatch')
 # Runtime source and evidence text pins.
 ctx=m['source_context'];ctx_raw=(bundle/ctx['file']).read_bytes()
 if sha(ctx_raw)!=ctx['evidence_text_sha256']:die('source context text checksum mismatch')
 patch_raw=(bundle/'applied-corrections.jsonl').read_bytes()
 if sha(patch_raw)!=m.get('applied_correction_ledger_sha256'):die('applied-correction ledger checksum mismatch')
 expected_counts={'accepted':23251,'corrected':25,'correction-needed':10967,'held':287,'unreviewed':30714,'conflicts':0}
 if m.get('overall_exact_status_counts_after_review')!=expected_counts or m.get('unreviewed_source_id_count_after_review')!=3750:die('whole-catalog status summary mismatch')
 visual=m.get('headed_visual_check_file')
 if not visual or sha((bundle/visual).read_bytes())!=m.get('headed_visual_check_sha256') or m.get('browser_recapture_required') is not True:die('headed visual-check blocker evidence mismatch')
 for path,digest in ctx['sha256'].items():
  if sha(git(repo,'show',f'{source}:{path}',raw=True))!=digest or git(repo,'rev-parse',f'{source}:{path}')!=ctx['git_blob_ids'][path]:die(f'source code pin mismatch {path}')
 expected=[f'{sha(p.read_bytes())}  {p.name}' for p in sorted(bundle.iterdir()) if p.is_file() and p.name!='SHA256SUMS']
 if (bundle/'SHA256SUMS').read_text(encoding='utf-8').splitlines()!=expected:die('SHA256SUMS mismatch')
 print('PASS: exact source/review/application pins; catalog hashes and 8-cell-only correction diff; 240-cell no-overlap partition; 87 fresh decisions (84 accepted, 3 correction-needed); 103 accepted carries; 42 correction-needed exclusions; 8 exact-hash corrections; 763 prior evidence inputs; 0 conflict holds; placeholders/ICU/literals/context and checksums.')
if __name__=='__main__':main()
