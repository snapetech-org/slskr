#!/usr/bin/env python3
"""Verify the exact source/cell decisions and catalog-only application for window 403–422."""
import argparse, collections, hashlib, json, re, subprocess
from pathlib import Path
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--repo',type=Path,default=Path.cwd())
args=parser.parse_args();repo=args.repo.resolve();bundle=Path(__file__).resolve().parent
BASE='087ea7ca6fed28c59dabe9639d8984ea8f061aa1'
COMMIT='ad7c283dfe84f31b52f5a27c363a605fe068e36c'
SOURCE='7ff454828398de6a3cfb72fe7f0ed21fe419425b'
LOCS=['ar','de','es','fr','hi','id','ja','ko','pt-BR','vi','zh-Hans','zh-Hant']
def git(*args,raw=False):
 b=subprocess.check_output(['git',*args],cwd=repo)
 return b if raw else b.decode().strip()
def sha(b):return hashlib.sha256(b).hexdigest()
def text_sha(s):return sha(s.encode('utf-8'))
def lines(name):return [json.loads(s) for s in (bundle/name).read_text(encoding='utf-8').splitlines() if s.strip()]
if git('rev-parse',f'{COMMIT}^')!=BASE:raise SystemExit('catalog commit is not a direct child of the reviewed baseline')
if git('rev-parse',f'{COMMIT}^{{tree}}')!='d0a2faeba016b57850767fe0903b67621d61bc6c':raise SystemExit('catalog tree pin mismatch')
if git('rev-parse',f'{SOURCE}^{{tree}}')!='9e9f2aa743c4ff3236af8f99619803bdc3a37152':raise SystemExit('source context tree pin mismatch')
review=lines('reviewed-cell-audit.jsonl');applied=lines('applied-corrections.jsonl');accepted=lines('accepted-dispositions.jsonl')
rootplan=lines('root-candidate-plan-403-422.jsonl');reconciled=lines('reconciled-decision-ledger-403-422.jsonl');applyplan=lines('reconciled-apply-plan-403-422.jsonl');independent=lines('independent-full-crossreview/decision-ledger.jsonl')
if (len(review),len(applied),len(accepted),len(rootplan),len(reconciled),len(applyplan),len(independent))!=(240,55,185,56,56,55,56):
 raise SystemExit('unexpected evidence row counts')
review_keys={(r['source_index'],r['locale']) for r in review}
if len(review_keys)!=240:raise SystemExit('duplicate reviewed source/locale cells')
for rows,name in ((applied,'applied'),(accepted,'accepted')):
 if len({(r['source_index'],r['locale']) for r in rows})!=len(rows):raise SystemExit(f'duplicate {name} rows')
locale_keys={};file_hashes={};changed_paths=git('diff','--name-only',f'{BASE}..{COMMIT}').splitlines()
expected_paths=sorted({r['catalog_path'] for r in review})
if sorted(changed_paths)!=expected_paths or len(changed_paths)!=12:raise SystemExit('catalog diff path set mismatch')
before={};after={}
for loc in LOCS:
 path=f'web/src/lib/locales/ui-labels.{loc}.json'
 before[loc]=json.loads(git('show',f'{BASE}:{path}',raw=True).decode('utf-8'))
 raw=git('show',f'{COMMIT}:{path}',raw=True);after[loc]=json.loads(raw.decode('utf-8'));file_hashes[path]=sha(raw)
 if len(before[loc])!=5437 or len(after[loc])!=5437 or list(before[loc])!=list(after[loc]):raise SystemExit(f'catalog key count/order mismatch {loc}')
 if any(v is None or (isinstance(v,str) and not v.strip()) for v in after[loc].values()):raise SystemExit(f'blank catalog target {loc}')
locale_changed={}
for loc in LOCS:
 path=f'web/src/lib/locales/ui-labels.{loc}.json'
 expected_changed={r['source_id'] for r in applied if r['locale']==loc}
 actual_changed={k for k in before[loc] if before[loc][k]!=after[loc][k]}
 if actual_changed!=expected_changed:raise SystemExit(f'changed cell set mismatch {loc}: {actual_changed ^ expected_changed}')
 locale_changed[loc]=len(actual_changed)
source_pins={};status=collections.Counter();per_locale={loc:collections.Counter() for loc in LOCS}
for r in review:
 loc=r['locale'];sid=r['source_id']
 if text_sha(sid)!=r['source_sha256']:raise SystemExit(f'source id hash mismatch {loc}:{sid}')
 if before[loc].get(sid)!=r['current_target_text'] or text_sha(r['current_target_text'])!=r['current_target_sha256']:raise SystemExit(f'baseline target mismatch {loc}:{sid}')
 if after[loc].get(sid)!=r['final_target_text'] or text_sha(r['final_target_text'])!=r['final_target_sha256']:raise SystemExit(f'final target mismatch {loc}:{sid}')
 if sorted(re.findall(r'\{[^{}]+\}',r['current_target_text']))!=sorted(re.findall(r'\{[^{}]+\}',r['final_target_text'])):raise SystemExit(f'placeholder mismatch {loc}:{sid}')
 for caller in r['source_callers']:
  raw=git('show',f"{SOURCE}:{caller['path']}",raw=True)
  if sha(raw)!=caller['sha256']:raise SystemExit(f'caller blob mismatch {caller["path"]}')
  blob_lines=raw.decode('utf-8').splitlines()
  for ref in caller['lines']:
   if blob_lines[ref['line']-1]!=ref['text']:raise SystemExit(f'caller line mismatch {caller["path"]}:{ref["line"]}')
  source_pins[caller['path']]=caller['sha256']
 decision=r['decision'];status[decision]+=1;per_locale[loc][decision]+=1
if status!=collections.Counter({'accepted-carry':115,'accepted-fresh':69,'accepted-current':1,'corrected':55}):raise SystemExit(f'final disposition mismatch: {status}')
for r in applied:
 loc=r['locale'];sid=r['source_id']
 if before[loc][sid]!=r['baseline_target_text'] or after[loc][sid]!=r['final_target_text']:raise SystemExit(f'applied ledger text mismatch {loc}:{sid}')
 if text_sha(r['baseline_target_text'])!=r['baseline_target_sha256'] or text_sha(r['final_target_text'])!=r['final_target_sha256']:raise SystemExit(f'applied ledger hash mismatch {loc}:{sid}')
 if r['status']!='corrected' or r['target_sha256']!=r['final_target_sha256']:raise SystemExit(f'applied ledger terminal status mismatch {loc}:{sid}')
for r in accepted:
 if r['status']!='accepted' or text_sha(r['target_text'])!=r['target_sha256']:raise SystemExit('accepted ledger target mismatch')
if not any(r['locale']=='pt-BR' and r['source_id']=='Available ports for forwarding (1024-65535):' for r in accepted):raise SystemExit('pt-BR accepted unchanged decision missing')
if len(lines('accepted-unchanged.jsonl'))!=1:raise SystemExit('accepted unchanged supersession missing')
counts=collections.Counter(r['resolution'] for r in reconciled)
if counts!=collections.Counter({'accept':52,'root-refine':1,'independent-refine':2,'keep-current':1}):raise SystemExit(f'reconciled decision count mismatch: {counts}')
subprocess.check_call(['git','diff','--check',f'{BASE}..{COMMIT}'],cwd=repo)
print(json.dumps({'baseline_head':BASE,'catalog_commit':COMMIT,'catalog_tree':git('rev-parse',f'{COMMIT}^{{tree}}'),'source_head':SOURCE,'source_tree':git('rev-parse',f'{SOURCE}^{{tree}}'),'reviewed_cells':len(review),'candidate_cells':len(rootplan),'accepted_dispositions':len(accepted),'applied_changes':len(applied),'disposition_counts':dict(status),'root_reconciled_candidate_counts':dict(counts),'caller_file_pins':len(source_pins),'caller_files':source_pins,'catalog_key_count_each_locale':5437,'locale_changed_cell_counts':locale_changed,'catalog_file_sha256_after':file_hashes,'git_diff_check':'passed','native_speaker_approved':False,'tests_builds_ci_run':False,'all_pass':True},ensure_ascii=False,indent=2))
