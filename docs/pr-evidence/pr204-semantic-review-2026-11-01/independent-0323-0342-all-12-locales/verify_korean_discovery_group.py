#!/usr/bin/env python3
"""Verify the four exact-head Korean Discovery Inbox term rows and 48-cell context."""
import argparse,collections,hashlib,json,re,subprocess
from pathlib import Path
HERE=Path(__file__).resolve().parent
DEFAULT_REPO=Path('/mnt/disks/scratch/task-worktrees/localization-20261030/slskr-independent-review-e05f1b71-window-5400-5419-20261101')
DEFAULT_AUDIT=Path('/mnt/disks/scratch/task-worktrees/localization-20261030/slskr-populated-catalog-review-7ff45482-20261101')
LOCALES=['ar','de','es','fr','hi','id','ja','ko','pt-BR','vi','zh-Hans','zh-Hant']
IDS=['Approved in Discovery Inbox for the next acquisition step.','Rejected in Discovery Inbox and suppressed for the same evidence.','Snoozed in Discovery Inbox until later review.','Waiting in Discovery Inbox for approval or rejection.']
def fail(m):raise SystemExit('FAIL: '+m)
def sha(b):return hashlib.sha256(b).hexdigest()
def h(s):return sha(s.encode('utf-8'))
def git(repo,*a,raw=False):
 b=subprocess.check_output(['git',*a],cwd=repo);return b if raw else b.decode().strip()
def read(path):return [json.loads(x) for x in Path(path).read_text(encoding='utf-8').splitlines() if x.strip()]
def pick(r,names):
 for n in names:
  if r.get(n) is not None:return r[n]
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
    try:yield n,json.loads(line)
    except json.JSONDecodeError:continue
 elif path.endswith('.json'):
  try:yield from enumerate(walk(json.loads(raw.decode('utf-8'))),1)
  except json.JSONDecodeError:return
def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--repo',type=Path,default=DEFAULT_REPO);ap.add_argument('--prior-audit',type=Path,default=DEFAULT_AUDIT);args=ap.parse_args()
 repo=args.repo.resolve();audit=args.prior_audit.resolve();m=json.loads((HERE/'prepare-summary.json').read_text(encoding='utf-8'))
 if git(repo,'rev-parse','HEAD')!=m['head'] or git(repo,'rev-parse','HEAD^{tree}')!=m['head_tree']:fail('review PR head/tree changed')
 if git(repo,'rev-parse',m['source_head']+'^{tree}')!=m['source_tree']:fail('source commit/tree mismatch')
 inventory=(audit/'frozen-inputs/source-inventory.jsonl').read_bytes()
 if sha(inventory)!=m['frozen_source_inventory_sha256']:fail('frozen source inventory mismatch')
 ids=[json.loads(x)['source_id'] for x in inventory.decode().splitlines() if x.strip()]
 index={sid:i for i,sid in enumerate(ids)}
 if len(ids)!=5437 or ids!=sorted(ids) or any(sid not in index for sid in IDS):fail('source inventory mismatch')
 context=read(HERE/'korean-discovery-inbox-group-context-48.jsonl');candidates=read(HERE/'korean-discovery-inbox-group-candidates.jsonl')
 if len(context)!=48 or len(candidates)!=4:fail('group coverage mismatch')
 if {(x['source_id'],x['locale']) for x in context}!={(sid,loc) for sid in IDS for loc in LOCALES}:fail('48-cell group context key mismatch')
 if {x['source_id'] for x in context}!= set(IDS):fail('source ID group mismatch')
 if {x['locale'] for x in candidates}!={'ko'} or [x['source_id'] for x in candidates]!=IDS:fail('Korean group candidate order/membership mismatch')
 scan=read(HERE/'prior-evidence-scan-manifest.jsonl');exact=collections.defaultdict(list)
 if len(scan)!=m['overlap_input_count']:fail('prior evidence count mismatch')
 for item in scan:
  if item['root']=='prior-audit-7ff':raw=(audit/item['path']).read_bytes()
  elif item['root']=='pr-review-head':raw=git(repo,'show',m['head']+':'+item['path'],raw=True)
  else:fail('unknown evidence input root '+str(item['root']))
  if len(raw)!=item['bytes'] or sha(raw)!=item['sha256']:fail('prior evidence input hash mismatch '+item['path'])
  for n,r in parse(raw,item['path']):
   sid=pick(r,['source_id','sourceId','message_id','id']);loc=r.get('locale')
   st=str(pick(r,['status','review_outcome','disposition']) or '').strip().lower().replace('_','-')
   if sid in IDS and loc in LOCALES and st in {'accepted','correction-needed','held','keep','corrected'}:
    exact[(sid,loc)].append((r,st,item,n))
 for row in context:
  if row['review_head']!=m['head'] or row['review_tree']!=m['head_tree'] or row['source_catalog_head']!=m['source_head'] or row['source_catalog_tree']!=m['source_tree']:fail('context commit pin mismatch')
  if row['source_index']!=index[row['source_id']] or row['source_sha256']!=h(row['source_id']):fail('context source index/hash mismatch')
  raw=git(repo,'show',f"{m['head']}:{row['catalog_path']}",raw=True);catalog=json.loads(raw.decode('utf-8'))
  target=catalog[row['source_id']]
  if target!=row['current_target_text'] or h(target)!=row['current_target_sha256']:fail('context target mismatch '+str((row['source_id'],row['locale'])))
  matches=[]
  for r,st,item,n in exact.get((row['source_id'],row['locale']),[]):
   if pick(r,['source_sha256','sourceSha256'])==row['source_sha256'] and pick(r,['target_sha256','targetSha256','current_target_sha256'])==row['current_target_sha256']:
    matches.append({'status':st,'root':item['root'],'path':item['path'],'line':n,'batch':r.get('batch') or r.get('review_batch'),'finding_id':r.get('finding_id')})
  matches.sort(key=lambda x:(x['root'],x['path'],x['line'],x['status']))
  if matches!=row['prior_exact_matches']:fail('group exact-overlap mismatch '+str((row['source_id'],row['locale'])))
  states=sorted({x['status'] for x in matches});status='conflict' if len(states)>1 else (states[0] if states else 'unreviewed')
  if status!=row['prior_exact_status']:fail('group status mismatch '+str((row['source_id'],row['locale'])))
 for c in candidates:
  k=(c['source_id'],c['locale']);row=next(x for x in context if (x['source_id'],x['locale'])==k)
  if c['source_index']!=row['source_index'] or c['source_sha256']!=row['source_sha256'] or c['current_target_text']!=row['current_target_text'] or c['current_target_sha256']!=row['current_target_sha256'] or c['prior_exact_matches']!=row['prior_exact_matches']:fail('candidate/current exact pin mismatch '+str(k))
  if c['proposed_target']!=c['current_target_text'].replace('검색함','발견함') or c['current_target_text'].count('검색함')!=1:fail('candidate is not exact group term replacement '+str(k))
  if c['proposed_target_sha256']!=h(c['proposed_target']):fail('candidate target hash mismatch '+str(k))
  if c['context_pointer']!='web/src/lib/acquisitionRequests.js:6-46':fail('context pointer mismatch')
 by={x['source_id']:x for x in candidates}
 if by[IDS[0]]['prior_exact_status']!='correction-needed' or by[IDS[1]]['prior_exact_status']!='unreviewed' or by[IDS[2]]['prior_exact_status']!='correction-needed' or by[IDS[3]]['prior_exact_status']!='unreviewed':fail('unexpected status distribution')
 print(f'PASS: 48 exact locale-context cells, 4 Korean group candidates, 892 raw prior evidence inputs; source/current/proposed hashes and prior statuses verified at {m["head"][:12]}.')
if __name__=='__main__':main()
