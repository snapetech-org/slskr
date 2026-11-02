#!/usr/bin/env python3
"""Exact-current populated-catalog evidence scan using PR-head catalog hashes."""
import argparse,collections,hashlib,json,subprocess
from pathlib import Path
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--repo',type=Path,required=True)
parser.add_argument('--prior-audit',type=Path,required=True)
parser.add_argument('--head',required=True)
parser.add_argument('--head-tree',required=True)
parser.add_argument('--source-head',required=True)
parser.add_argument('--source-tree',required=True)
parser.add_argument('--output',type=Path,required=True)
args=parser.parse_args()
REPO=args.repo.resolve();AUDIT=args.prior_audit.resolve();OUTPUT=args.output.resolve()
HEAD=args.head;SOURCE=args.source_head
LOCALES=['ar','de','es','fr','hi','id','ja','ko','pt-BR','vi','zh-Hans','zh-Hant']
TERMINAL={'accepted','correction-needed','held','keep','corrected'}
ALIASES={'source_id':['source_id','sourceId','message_id','id'],'source_sha':['source_sha256','sourceSha256'],'target_sha':['target_sha256','current_target_sha256','reviewed_target_after_sha256','final_target_sha256','target_after_sha256','targetSha256','currentTargetSha256','reviewedTargetAfterSha256','finalTargetSha256'],'status':['status','review_outcome']}
def sha(raw):return hashlib.sha256(raw).hexdigest()
def norm(v):return str(v or '').strip().lower().replace('_','-')
def pick(d,names):
 for name in names:
  if name in d and d[name] is not None:return d[name]
 return None
def target_sha(value):
 raw=value.encode('utf-8') if isinstance(value,str) else json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode('utf-8')
 return sha(raw)
def walk(x):
 if isinstance(x,dict):
  yield x
  for v in x.values():yield from walk(v)
 elif isinstance(x,list):
  for v in x:yield from walk(v)
def nonempty(v):
 if isinstance(v,str):return bool(v.strip())
 if isinstance(v,dict):return bool(v) and all(nonempty(x) for x in v.values())
 if isinstance(v,list):return bool(v) and all(nonempty(x) for x in v)
 return False
if subprocess.check_output(['git','rev-parse',f'{HEAD}^{{tree}}'],cwd=REPO,text=True).strip()!=args.head_tree:raise SystemExit('catalog application tree pin mismatch')
if subprocess.check_output(['git','rev-parse',f'{SOURCE}^{{tree}}'],cwd=REPO,text=True).strip()!=args.source_tree:raise SystemExit('source context tree pin mismatch')
ids=sorted({json.loads(l)['source_id'] for l in (AUDIT/'frozen-inputs/source-inventory.jsonl').read_text().splitlines() if l.strip()})
if len(ids)!=5437:raise SystemExit('source-key inventory mismatch')
cells={};catalog_hashes={};structured=collections.Counter()
for loc in LOCALES:
 path=f'web/src/lib/locales/ui-labels.{loc}.json';raw=subprocess.check_output(['git','show',f'{HEAD}:{path}'],cwd=REPO);cat=json.loads(raw.decode())
 catalog_hashes[path]=sha(raw)
 if set(cat)!=set(ids):raise SystemExit(f'key mismatch in {loc}')
 for sid,value in cat.items():
  if not nonempty(value):raise SystemExit(f'blank target in {loc}:{sid}')
  if isinstance(value,(dict,list)):structured[loc]+=1
  cells[(sid,loc)]={'source_sha256':sha(sid.encode()),'target_text':value,'target_sha256':target_sha(value),'catalog_path':path}
if sum(structured.values())!=15 or dict(structured)!={'ar':15}:raise SystemExit('unexpected plural/structured inventory')
files=[AUDIT/'findings.jsonl',AUDIT/'carried-findings.jsonl']
files+=list((AUDIT/'review-evidence').rglob('*.jsonl'))+list((AUDIT/'review-evidence').rglob('*.json'))
files+=list((REPO/'docs/pr-evidence/pr204-semantic-review-2026-11-01').rglob('*.jsonl'))
files+=list((REPO/'docs/pr-evidence/pr204-semantic-review-2026-11-01').rglob('*.json'))
files=sorted({p for p in files if p.is_file()})
# A pinned conflict-resolution ledger supersedes its cited historical exact records.
resolution_path=REPO/'docs/pr-evidence/pr204-semantic-review-2026-11-01/exact-conflict-resolution-1494972d-2026-11-01/conflict-resolutions.jsonl'
resolutions=[json.loads(line) for line in resolution_path.read_text(encoding='utf-8').splitlines() if line.strip()]
suppress={(ref['root'],ref['path'],ref['line']) for row in resolutions for ref in row['supersedes']}
# An exact accepted-unchanged cross-review explicitly supersedes the older
# disposition(s) it reassessed. Require the record's source and target hashes
# to match the current catalog before suppressing its cited prior rows.
unchanged_path=REPO/'docs/pr-evidence/pr204-semantic-review-2026-11-01/independent-0323-0342-all-12-locales/accepted-unchanged.jsonl'
if unchanged_path.is_file():
 candidate_path=unchanged_path.with_name('candidate-cell-audit.jsonl')
 candidate_records=[]
 if candidate_path.is_file():
  candidate_records=[(n,json.loads(line)) for n,line in enumerate(candidate_path.read_text(encoding='utf-8').splitlines(),1) if line.strip()]
 candidate_rel=candidate_path.relative_to(REPO).as_posix()
 for row in [json.loads(line) for line in unchanged_path.read_text(encoding='utf-8').splitlines() if line.strip()]:
  sid=row.get('sourceId',row.get('source_id'));loc=row.get('locale');c=cells.get((sid,loc))
  if row.get('disposition')!='accepted-unchanged' or c is None:continue
  if row.get('sourceSha256')!=c['source_sha256'] or row.get('currentTargetSha256')!=c['target_sha256']:continue
  suppress.update((ref['root'],ref['path'],ref['line']) for ref in row.get('priorExactMatches',[]))
  # The batch's pre-cross-review candidate audit records a provisional
  # correction-needed status for this same exact cell. The accepted-unchanged
  # disposition is the final cross-reviewed status, so suppress only that
  # precisely matched candidate row.
  for line_no,candidate in candidate_records:
   if candidate.get('source_id')==sid and candidate.get('locale')==loc and candidate.get('baseline_target_sha256')==c['target_sha256'] and candidate.get('status')=='correction-needed':
    suppress.add(('pr-review-head',candidate_rel,line_no))
bycell=collections.defaultdict(list);manifest=[]
for p in files:
 raw=p.read_bytes();root='prior-audit-7ff' if AUDIT in p.parents else 'pr-review-head';base=AUDIT if root=='prior-audit-7ff' else REPO
 rel=p.relative_to(base).as_posix();manifest.append({'root':root,'path':rel,'bytes':len(raw),'sha256':sha(raw)})
 records=[]
 if p.suffix=='.jsonl':
  for n,line in enumerate(raw.decode('utf-8').splitlines(),1):
   if not line.strip():continue
   try:records.append((n,json.loads(line)))
   except json.JSONDecodeError:continue
 elif p.suffix=='.json':
  try:records=[(n+1,r) for n,r in enumerate(walk(json.loads(raw.decode('utf-8'))))]
  except json.JSONDecodeError:records=[]
 else:raise SystemExit(f'unsupported evidence file {p}')
 for n,row in records:
  if (root,rel,n) in suppress:continue
  sid=pick(row,ALIASES['source_id']);loc=row.get('locale')
  if not isinstance(sid,str) or sid not in ids or loc not in LOCALES:continue
  status=norm(pick(row,ALIASES['status']))
  if status not in TERMINAL:continue
  c=cells[(sid,loc)]
  if pick(row,ALIASES['source_sha'])!=c['source_sha256'] or pick(row,ALIASES['target_sha'])!=c['target_sha256']:continue
  bycell[(sid,loc)].append({'status':status,'root':root,'path':rel,'line':n,'batch':row.get('batch') or row.get('review_batch'),'finding_id':row.get('finding_id')})
status_counts=collections.Counter();locale_counts={l:collections.Counter() for l in LOCALES};unreviewed=[];conflicts=[]
for (sid,loc),c in cells.items():
 statuses=sorted({r['status'] for r in bycell.get((sid,loc),[])})
 if not statuses:
  status_counts['unreviewed']+=1;locale_counts[loc]['unreviewed']+=1;unreviewed.append((ids.index(sid),sid,loc,c['target_text']))
 elif len(statuses)>1:
  status_counts['conflict']+=1;locale_counts[loc]['conflict']+=1;conflicts.append((ids.index(sid),sid,loc,statuses,bycell[(sid,loc)]))
 else:
  status_counts[statuses[0]]+=1;locale_counts[loc][statuses[0]]+=1
by_index=collections.defaultdict(list)
for idx,sid,loc,target in unreviewed:by_index[idx].append({'source_id':sid,'locale':loc,'target_text':target})
scan_manifest=sorted(manifest,key=lambda r:(r['root'],r['path']))
head_tree=subprocess.check_output(['git','rev-parse',f'{HEAD}^{{tree}}'],cwd=REPO,text=True).strip()
source_tree=subprocess.check_output(['git','rev-parse',f'{SOURCE}^{{tree}}'],cwd=REPO,text=True).strip()
report={'head':HEAD,'head_tree':head_tree,'source_catalog_head':SOURCE,'source_catalog_tree':source_tree,'source_ids':len(ids),'cell_count':len(cells),
 'catalog_file_sha256':catalog_hashes,'structured_plural_cells':dict(structured),'evidence_files_scanned':len(files),
 'evidence_scan_manifest_sha256':sha(json.dumps(scan_manifest,sort_keys=True,separators=(',',':')).encode()),
 'evidence_file_manifest':scan_manifest,'unique_current_cell_status_counts':dict(sorted(status_counts.items())),
 'per_locale_exact_status_counts':{l:dict(sorted(c.items())) for l,c in locale_counts.items()},'unreviewed_source_index_count':len(by_index),
 'unreviewed_cells':len(unreviewed),'first_100_unreviewed_indices':{str(i):{'source_id':ids[i],'fresh_locale_count':len(by_index[i]),'fresh_locales':[x['locale'] for x in by_index[i]]} for i in sorted(by_index)[:100]},
 'conflicts':conflicts,'superseded_exact_records':len(suppress),'conflict_resolution_rows':len(resolutions)}
OUTPUT.parent.mkdir(parents=True,exist_ok=True);OUTPUT.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:v for k,v in report.items() if k not in ('evidence_file_manifest','first_100_unreviewed_indices','conflicts','catalog_file_sha256')},ensure_ascii=False,indent=2))
print('first unreviewed source keys:')
for i in sorted(by_index)[:30]:print(i,repr(ids[i]),len(by_index[i]),','.join(x['locale'] for x in by_index[i]))
print('conflicts',len(conflicts))
