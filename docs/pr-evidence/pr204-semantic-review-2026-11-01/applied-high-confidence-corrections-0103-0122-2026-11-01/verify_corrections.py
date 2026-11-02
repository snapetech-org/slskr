#!/usr/bin/env python3
"""Verify exact-hash high-confidence corrections from slskR source indices 103–122."""
import argparse,collections,hashlib,json,re,subprocess
from pathlib import Path
LOCALES=['ar','de','es','fr','hi','id','ja','ko','pt-BR','vi','zh-Hans','zh-Hant']
def fail(msg):raise SystemExit('FAIL: '+msg)
def sha(raw):return hashlib.sha256(raw).hexdigest()
def git(repo,*args,raw=False):
 p=subprocess.run(['git',*args],cwd=repo,check=True,stdout=subprocess.PIPE)
 return p.stdout if raw else p.stdout.decode('utf8').strip()
def target_sha(value):
 raw=value.encode('utf8') if isinstance(value,str) else json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode('utf8')
 return sha(raw)
def placeholders(v):return sorted(set(re.findall(r'\{([^{}]+)\}',str(v))))
def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--repo',type=Path,default=Path.cwd());args=ap.parse_args();repo=args.repo.resolve();bundle=Path(__file__).resolve().parent
 m=json.loads((bundle/'manifest.json').read_text(encoding='utf8'))
 for name,key in [('review_head','review_tree'),('evidence_commit','evidence_tree'),('source_catalog_head','source_catalog_tree'),('application_parent_head','application_parent_tree'),('application_head','application_tree')]:
  if git(repo,'rev-parse',f'{m[name]}^{{tree}}')!=m[key]:fail(f'{name} tree mismatch')
 if git(repo,'rev-parse',f'{m["application_head"]}^')!=m['application_parent_head']:fail('application parent is not the correction commit parent')
 changed=git(repo,'diff','--name-only',m['application_parent_head'],m['application_head']).splitlines()
 if changed!=sorted(f'web/src/lib/locales/ui-labels.{l}.json' for l in m['changed_locales']):fail('application commit changed unexpected files')
 raw_ledger=(bundle/'applied-corrections.jsonl').read_bytes();rows=[json.loads(l) for l in raw_ledger.decode('utf8').splitlines() if l.strip()]
 if len(rows)!=4 or m['applied_corrections']!=4 or sha(raw_ledger)!=m['correction_ledger_sha256']:fail('ledger count/hash mismatch')
 if len({(r['source_id'],r['locale']) for r in rows})!=4 or any(r.get('status')!='corrected' or r.get('confidence')!='high' for r in rows):fail('duplicate or non-high correction')
 decision_path='docs/pr-evidence/pr204-semantic-review-2026-11-01/independent-0103-0122-all-12-locales/decisions.jsonl'
 before_cats={};after_cats={};all_diffs=set();structured=collections.Counter();source_ids=None
 for loc in LOCALES:
  path=f'web/src/lib/locales/ui-labels.{loc}.json';braw=git(repo,'show',f'{m["application_parent_head"]}:{path}',raw=True);araw=git(repo,'show',f'{m["application_head"]}:{path}',raw=True)
  if sha(braw)!=m['catalog_sha256_before'][path] or sha(araw)!=m['catalog_sha256_after'][path]:fail(f'catalog hash mismatch: {loc}')
  before=json.loads(braw.decode('utf8'));after=json.loads(araw.decode('utf8'))
  if set(before)!=set(after) or len(before)!=5437:fail(f'catalog keyset mismatch: {loc}')
  before_cats[loc]=before;after_cats[loc]=after
  if source_ids is None:source_ids=set(before)
  elif set(before)!=source_ids:fail('locale source IDs differ')
  structured[loc]+=sum(1 for v in after.values() if isinstance(v,(dict,list)))
  all_diffs.update((sid,loc) for sid in before if before[sid]!=after[sid])
 if structured!=collections.Counter({'ar':15}):fail('plural inventory mismatch')
 if all_diffs!={(r['source_id'],r['locale']) for r in rows}:fail('catalog change set differs from ledger')
 for row in rows:
  loc,sid=row['locale'],row['source_id']
  if loc not in LOCALES or sid not in source_ids:fail('invalid target cell')
  old=before_cats[loc][sid];new=after_cats[loc][sid]
  if old!=row['previous_target'] or target_sha(old)!=row['previous_target_sha256']:fail(f'old target hash mismatch {loc}:{sid}')
  if new!=row['current_target'] or target_sha(new)!=row['target_sha256']:fail(f'new target hash mismatch {loc}:{sid}')
  if row['source_sha256']!=sha(sid.encode('utf8')):fail(f'source hash mismatch {loc}:{sid}')
  if placeholders(sid)!=placeholders(old) or placeholders(sid)!=placeholders(new):fail(f'placeholder mismatch {loc}:{sid}')
  if (row['application_parent_head'],row['application_head'],row['review_head'],row['review_tree'],row['source_catalog_head'],row['source_catalog_tree'])!=(m['application_parent_head'],m['application_head'],m['review_head'],m['review_tree'],m['source_catalog_head'],m['source_catalog_tree']):fail(f'row pin mismatch {loc}:{sid}')
  ref=row['review_evidence'];lines=git(repo,'show',f'{m["evidence_commit"]}:{ref["path"]}',raw=True).decode('utf8').splitlines()
  decision=json.loads(lines[ref['line']-1])
  if (decision.get('batch'),decision.get('status'),decision.get('confidence'),decision.get('source_id'),decision.get('locale'),decision.get('source_sha256'),decision.get('target_sha256'),decision.get('proposed_target'))!=(row['review_batch'],'correction-needed','high',sid,loc,row['source_sha256'],row['previous_target_sha256'],new):fail(f'original decision mismatch {loc}:{sid}')
 if dict(collections.Counter(r['locale'] for r in rows))!=m['per_locale_counts']:fail('per-locale counts mismatch')
 if m['moderate_confidence_suggestions_applied']!=0:fail('moderate suggestion marked applied')
 sums={}
 for line in (bundle/'SHA256SUMS').read_text().splitlines():
  h,name=line.split('  ',1);sums[name]=h
 expected={p.name:sha(p.read_bytes()) for p in bundle.iterdir() if p.is_file() and p.name!='SHA256SUMS'}
 if sums!=expected:fail('SHA256SUMS mismatch')
 print(json.dumps({'result':'PASS','application_head':m['application_head'],'corrected_cells':len(rows),'per_locale':m['per_locale_counts'],'catalogs_changed':m['changed_locales'],'catalog_diffs_exact':len(all_diffs)},ensure_ascii=False,indent=2))
if __name__=='__main__':main()
