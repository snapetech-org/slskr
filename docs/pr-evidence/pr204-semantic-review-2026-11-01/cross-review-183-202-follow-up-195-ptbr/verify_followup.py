#!/usr/bin/env python3
"""Verify parent cross-review and the one-cell pt-BR refinement."""
import argparse,collections,hashlib,json,subprocess
from pathlib import Path
LEDGER_SHA='540ae4de10b019726dee36779d802115bf102b5a35cec77b71eb74b876ce045b'
def die(m):raise SystemExit('FAIL: '+m)
def sha(b):return hashlib.sha256(b).hexdigest()
def git(repo,*args,raw=False):
 b=subprocess.run(['git',*args],cwd=repo,check=True,stdout=subprocess.PIPE).stdout
 return b if raw else b.decode().strip()
def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--repo',type=Path,required=True);args=ap.parse_args();repo=args.repo.resolve();bundle=Path(__file__).resolve().parent
 raw=(bundle/'parent-cross-review-44.jsonl').read_bytes()
 if sha(raw)!=LEDGER_SHA:die('root 44-row ledger checksum mismatch')
 rows=[json.loads(x) for x in raw.decode().splitlines() if x.strip()]
 if len(rows)!=44 or len({(r['sourceIndex'],r['locale']) for r in rows})!=44:die('root ledger row count/uniqueness mismatch')
 dispositions=collections.Counter(r['crossReviewDisposition'] for r in rows)
 if dispositions!=collections.Counter({'accepted-as-applied':43,'refined-and-accepted':1}):die('root cross-review disposition count mismatch')
 for r in rows:
  if r['currentPrHead']!='6a8415d2df2f22935188992e03c4636052de2d67' or r['currentPrTree']!='f562ac9ed6108921efbef4272973b8895bb4c22a':die('review-head pin mismatch')
  if r['reviewSourceHead']!='7ff454828398de6a3cfb72fe7f0ed21fe419425b' or r['reviewSourceTree']!='9e9f2aa743c4ff3236af8f99619803bdc3a37152':die('source-head pin mismatch')
  if r['applicationCommit']!='cc55673a362e627e256dc45cd90c9fe5c28c163f' or r['applicationTree']!='739ba38688b25d02002a6f044cb393b4996de836':die('original application pin mismatch')
 refinement=json.loads((bundle/'refinement.jsonl').read_text(encoding='utf-8'))
 cross=[r for r in rows if r['sourceIndex']==195 and r['locale']=='pt-BR']
 if len(cross)!=1:die('unique refined parent row missing')
 r=cross[0]
 if refinement['cross_review_ledger_sha256']!=LEDGER_SHA or r['crossReviewDisposition']!='refined-and-accepted':die('refinement provenance mismatch')
 for key in ('source_index','source_id','locale'):
  mapping={'source_index':'sourceIndex','source_id':'source','locale':'locale'}
  if refinement[key]!=r[mapping[key]]:die('refined source identity mismatch')
 if (refinement['source_sha256'],refinement['previous_target'],refinement['previous_target_sha256'],refinement['current_target'],refinement['current_target_sha256'])!=(r['sourceHash'],r['currentAppliedTarget'],r['expectedCurrentAppliedTargetHash'],r['crossReviewedTarget'],r['crossReviewedTargetHash']):die('refinement exact-text/hash mismatch')
 if refinement.get('status')!='corrected' or refinement.get('target_sha256')!=refinement['current_target_sha256']:die('refinement terminal status is missing or stale')
 if git(repo,'rev-parse',f"{refinement['application_head']}^{{tree}}")!=refinement['application_tree']:die('refinement tree mismatch')
 if git(repo,'rev-parse',f"{refinement['application_head']}^")!=refinement['application_parent']:die('refinement parent mismatch')
 if git(repo,'rev-parse',f"{refinement['application_parent']}^{{tree}}")!=refinement['application_parent_tree']:die('refinement parent tree mismatch')
 if git(repo,'merge-base','--is-ancestor',refinement['application_head'],'HEAD')!='':die('refinement commit is not an ancestor of current head')
 source=refinement['source_id'];loc=refinement['locale'];path=f'web/src/lib/locales/ui-labels.{loc}.json'
 old=json.loads(git(repo,'show',f"{refinement['application_parent']}:{path}",raw=True).decode())[source]
 new=json.loads(git(repo,'show',f"{refinement['application_head']}:{path}",raw=True).decode())[source]
 current=json.loads(git(repo,'show',f"HEAD:{path}",raw=True).decode())[source]
 if old!=refinement['previous_target'] or new!=refinement['current_target'] or current!=refinement['current_target']:die('refined catalog value mismatch')
 if git(repo,'show',f"{refinement['application_parent']}:{path}",raw=True)==git(repo,'show',f"{refinement['application_head']}:{path}",raw=True):die('focused application commit changed no catalog file')
 if r['source']!='Added {interest} as a hated interest.' or '{interest}' not in new:die('source placeholder mismatch')
 prior_target=r['currentAppliedTarget']
 original=json.loads(git(repo,'show',f"cc55673a362e627e256dc45cd90c9fe5c28c163f:{path}",raw=True).decode())[source]
 if original!=prior_target:die('cross-review applied target differs from pinned original app')
 original_bundle=Path(__file__).resolve().parent.parent/'independent-0183-0202-all-12-locales'
 applied=(original_bundle/'applied-corrections.jsonl').read_bytes()
 if sha(applied)!='ac21337cd22ccff47d23cb724c3fb4a7009e330144ef4697aa3a4d3cd2f05b8a':die('original 44-row application ledger changed')
 sums=[f'{sha(p.read_bytes())}  {p.name}' for p in sorted(bundle.iterdir()) if p.is_file() and p.name!='SHA256SUMS']
 if (bundle/'SHA256SUMS').read_text(encoding='utf-8').splitlines()!=sums:die('addendum checksum list mismatch')
 print('PASS: exact 44-row cross-review (43 accepted, 1 refined), unchanged historical application ledger, and exact one-cell pt-BR correction verified.')
if __name__=='__main__':main()
