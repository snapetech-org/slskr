#!/usr/bin/env python3
"""Verify source-index 323–342 exact-head selection and candidate preflight."""
import argparse, collections, hashlib, json, re, subprocess
from pathlib import Path
HERE=Path(__file__).resolve().parent
REPO=Path('/mnt/disks/scratch/task-worktrees/localization-20261030/slskr-independent-review-e05f1b71-window-5400-5419-20261101')
AUDIT=Path('/mnt/disks/scratch/task-worktrees/localization-20261030/slskr-populated-catalog-review-7ff45482-20261101')
LOCALES=['ar','de','es','fr','hi','id','ja','ko','pt-BR','vi','zh-Hans','zh-Hant']
TERMINAL={'accepted','correction-needed','held','keep','corrected'}
def fail(msg): raise SystemExit('FAIL: '+msg)
def sha(b): return hashlib.sha256(b).hexdigest()
def value_sha(v): return sha(v.encode('utf-8') if isinstance(v,str) else json.dumps(v,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode())
def git(*args,raw=False):
 b=subprocess.check_output(['git',*args],cwd=REPO)
 return b if raw else b.decode('utf-8').strip()
def read_jsonl(path): return [json.loads(line) for line in Path(path).read_text(encoding='utf-8').splitlines() if line.strip()]
def placeholders(v): return sorted(set(re.findall(r'\{([^{}]+)\}',str(v))))
def icu(v): return bool(re.search(r'\{\s*[A-Za-z_][\w.-]*\s*,\s*(plural|select|selectordinal)\s*,',str(v)))
def pick(r,names):
 for n in names:
  if r.get(n) is not None:return r[n]
def norm(v): return str(v or '').strip().lower().replace('_','-')
def walk(v):
 if isinstance(v,dict):
  yield v
  for x in v.values():yield from walk(x)
 elif isinstance(v,list):
  for x in v:yield from walk(x)
def parse(raw,path):
 if path.endswith('.jsonl'):
  for n,line in enumerate(raw.decode('utf-8').splitlines(),1):
   if line.strip():
    try: yield n,json.loads(line)
    except json.JSONDecodeError: continue
 elif path.endswith('.json'):
  try: yield from enumerate(walk(json.loads(raw.decode('utf-8'))),1)
  except json.JSONDecodeError: return

def main():
 global REPO, AUDIT
 ap=argparse.ArgumentParser(description=__doc__)
 ap.add_argument('--repo',type=Path,default=REPO)
 ap.add_argument('--prior-audit',type=Path,default=AUDIT)
 args=ap.parse_args()
 REPO=args.repo.resolve();AUDIT=args.prior_audit.resolve()
 m=json.loads((HERE/'prepare-summary.json').read_text(encoding='utf-8'))
 if git('rev-parse','HEAD')!=m['head'] or git('rev-parse','HEAD^{tree}')!=m['head_tree']:fail('live review head/tree changed')
 if git('rev-parse',m['source_head']+'^{tree}')!=m['source_tree']:fail('source code commit/tree mismatch')
 inventory=(AUDIT/'frozen-inputs/source-inventory.jsonl').read_bytes()
 if sha(inventory)!=m['frozen_source_inventory_sha256']:fail('source inventory checksum mismatch')
 ids=[json.loads(x)['source_id'] for x in inventory.decode('utf-8').splitlines() if x.strip()]
 if len(ids)!=5437 or ids!=sorted(ids):fail('source inventory size/order mismatch')
 selection=read_jsonl(HERE/'selection.jsonl')
 if len(selection)!=240 or len({(r['source_id'],r['locale']) for r in selection})!=240:fail('selection coverage/count mismatch')
 selected_ids=[]
 for r in sorted(selection,key=lambda x:(x['source_index'],LOCALES.index(x['locale']))):
  if r['source_id'] not in selected_ids:selected_ids.append(r['source_id'])
 if selected_ids!=ids[323:343]:fail('selection source index range mismatch')
 if m['selected_source_indices']!=[323,342] or m['selected_source_ids']!=selected_ids:fail('selection manifest mismatch')
 if m['counts']!={'new':67,'prior_accepted':128,'prior_correction-needed':45}:fail('overlap counts mismatch')
 # Verify the complete raw prior-evidence corpus and exact terminal overlaps.
 scan=read_jsonl(HERE/'prior-evidence-scan-manifest.jsonl')
 if len(scan)!=m['overlap_input_count']:fail('prior input count mismatch')
 if sha(json.dumps(scan,sort_keys=True,separators=(',',':')).encode())!=m['overlap_manifest_sha256']:fail('prior overlap manifest canonical hash mismatch')
 exact=collections.defaultdict(list)
 for item in scan:
  if item['root']=='prior-audit-7ff':raw=(AUDIT/item['path']).read_bytes()
  elif item['root']=='pr-review-head':raw=git('show',m['head']+':'+item['path'],raw=True)
  else:fail('unknown prior evidence root '+str(item['root']))
  if len(raw)!=item['bytes'] or sha(raw)!=item['sha256']:fail('prior raw input mismatch '+item['path'])
  for n,row in parse(raw,item['path']):
   sid=pick(row,['source_id','sourceId','message_id','id']);loc=row.get('locale')
   if not isinstance(sid,str) or loc not in LOCALES:continue
   st=norm(pick(row,['status','review_outcome','disposition']))
   if st not in TERMINAL:continue
   exact[(sid,loc)].append((item,n,row,st))
 for r in selection:
  matches=[]
  for item,n,row,st in exact.get((r['source_id'],r['locale']),[]):
   if pick(row,['source_sha256','sourceSha256'])!=r['source_sha256'] or pick(row,['target_sha256','targetSha256','current_target_sha256'])!=r['target_sha256']:continue
   matches.append({'status':st,'root':item['root'],'path':item['path'],'line':n,'batch':row.get('batch') or row.get('review_batch'),'finding_id':row.get('finding_id')})
  matches.sort(key=lambda x:(x['root'],x['path'],x['line'],x['status']))
  if matches!=r['prior_exact_matches']:fail('exact terminal overlap mismatch '+str((r['source_index'],r['locale'])))
  if r['source_sha256']!=value_sha(r['source_id']):fail('source hash mismatch '+str((r['source_index'],r['locale'])))
  if not isinstance(r['target_text'],str) or not r['target_text'].strip():fail('blank/current value not string '+str((r['source_index'],r['locale'])))
 # All 12 pinned catalog files and selected current values are exact at review head.
 for loc in LOCALES:
  path=f'web/src/lib/locales/ui-labels.{loc}.json';raw=git('show',m['head']+':'+path,raw=True)
  if sha(raw)!=m['catalog_sha256'][path]:fail('catalog file hash mismatch '+loc)
  cat=json.loads(raw.decode('utf-8'))
  for r in (x for x in selection if x['locale']==loc):
   if cat.get(r['source_id'])!=r['target_text'] or value_sha(cat[r['source_id']])!=r['target_sha256']:fail('catalog target mismatch '+str((r['source_index'],loc)))
 # Caller file pins must match both immutable source context and exact PR head.
 pins=json.loads((HERE/'source-pins.json').read_text(encoding='utf-8'))
 if pins['source_commit']!=m['source_head'] or git('rev-parse',m['source_head']+'^{tree}')!=pins['source_tree']:fail('source-pins commit/tree mismatch')
 for path,p in pins['files'].items():
  raw=git('show',m['source_head']+':'+path,raw=True)
  if len(raw)!=p['bytes'] or sha(raw)!=p['sha256'] or git('rev-parse',m['source_head']+':'+path)!=p['git_blob']:fail('caller source pin mismatch '+path)
  if git('rev-parse',m['head']+':'+path)!=p['git_blob']:fail('caller differs at PR head '+path)
 context=(HERE/'source-context.txt').read_bytes()
 review_summary=json.loads((HERE/'review-summary.json').read_text(encoding='utf-8'))
 if sha(context)!=review_summary['source_context_sha256']:fail('source context hash mismatch')
 # Candidate rows must map 1:1 to current exact cells and preserve source placeholders/literals.
 candidates=read_jsonl(HERE/'candidate-corrections.jsonl');by={(r['source_id'],r['locale']):r for r in selection}
 if len(candidates)!=46 or len({(r['source_id'],r['locale']) for r in candidates})!=46:fail('candidate count/uniqueness mismatch')
 for c in candidates:
  k=(c['source_id'],c['locale']);s=by.get(k)
  if s is None:fail('candidate outside selected window '+str(k))
  if c['review_head']!=m['head'] or c['review_tree']!=m['head_tree'] or c['source_catalog_head']!=m['source_head'] or c['source_catalog_tree']!=m['source_tree']:fail('candidate commit/tree pin mismatch '+str(k))
  if c['baseline_target_text']!=s['target_text'] or c['baseline_target_sha256']!=s['target_sha256'] or c['source_sha256']!=s['source_sha256']:fail('candidate baseline/source mismatch '+str(k))
  if c['proposed_sha256']!=value_sha(c['proposed_target']):fail('candidate final proposal hash mismatch '+str(k))
  if c['prior_exact_status']!=s['disposition'] or c['prior_exact_matches']!=s['prior_exact_matches']:fail('candidate prior status mismatch '+str(k))
  if placeholders(c['source_id'])!=placeholders(c['proposed_target']):fail('candidate placeholder mismatch '+str(k))
  if icu(c['source_id']) or icu(c['proposed_target']):fail('unexpected ICU syntax '+str(k))
  if not c['rationale'] or not c['source_context_pointer']:fail('candidate rationale/context missing '+str(k))
  if 'CSV' in c['source_id']:
   if 'CSV' not in c['proposed_target']:fail('CSV format literal not preserved '+str(k))
   token={'ar':'بفاصلة','de':'Komma','es':'comas','fr':'virgule','hi':'अल्पविराम','id':'koma','ja':'カンマ','ko':'쉼표','pt-BR':'vírgula','vi':'dấu phẩy','zh-Hans':'逗号','zh-Hant':'逗號'}[c['locale']]
   if token not in c['proposed_target']:fail('CSV field separator not preserved '+str(k))
 # Every cell has explicit review context and placeholder/ICU results.
 audits=read_jsonl(HERE/'reviewed-cell-audit.jsonl');decisions=read_jsonl(HERE/'decisions.jsonl');carries=read_jsonl(HERE/'carries.jsonl')
 if len(audits)!=240 or len(decisions)!=67 or len(carries)!=128:fail('review ledger counts mismatch')
 cand_keys={(x['source_id'],x['locale']) for x in candidates}
 audit_by={(x['source_id'],x['locale']):x for x in audits}
 for a in audits:
  if a['source_sha256']!=value_sha(a['source_id']) or a['baseline_target_sha256']!=value_sha(a['baseline_target_text']):fail('audit source/target hash mismatch')
  if not a['reviewed_context'] or not a['source_context_pointer'] or not a['semantic_review_result']:fail('audit context/result missing')
  if placeholders(a['source_id'])!=placeholders(a['reviewed_target_after']) or not a['placeholders_preserved']:fail('audit placeholder mismatch')
  if icu(a['source_id']) or icu(a['reviewed_target_after']) or a['icu_message_source'] or a['icu_message_target']:fail('unexpected ICU cell')
  if a['native_speaker_approval'] is not False:fail('native speaker approval must remain false')
  if a['candidate_target']:
   c=next((x for x in candidates if x['source_id']==a['source_id'] and x['locale']==a['locale']),None)
   if c is None or c['proposed_target']!=a['candidate_target'] or c['proposed_sha256']!=a['candidate_target_sha256']:fail('candidate audit mismatch')
  elif (a['source_id'],a['locale']) in cand_keys:fail('candidate is missing from cell audit')
 if sum(a['status']=='accepted' for a in audits)!=194 or sum(a['status']=='correction-needed' for a in audits)!=46:fail('first-pass disposition count mismatch')
 # Check manifest declared raw evidence roots, all tracked output SHA sums, and candidate hash pin.
 summary=json.loads((HERE/'review-summary.json').read_text(encoding='utf-8'))
 if summary['review_head']!=m['head'] or summary['window_cells']!=240 or summary['candidate_count']!=46:fail('review summary mismatch')
 print(f'PASS: exact PR head/tree {m["head"][:12]}/{m["head_tree"][:12]}; source {m["source_head"][:12]}/{m["source_tree"][:12]}; 240 cells, 67 fresh (66 accepted, 1 candidate), 128 accepted carries, 45 exact correction-needed overlaps, 0 conflicts; 46 exact candidate rows; {len(scan)} raw prior evidence inputs; 12 catalogs and {len(pins["files"])} caller files rehashed; source/current/proposed hashes, placeholders, CSV literal, and ICU checks pass.')
if __name__=='__main__': main()
