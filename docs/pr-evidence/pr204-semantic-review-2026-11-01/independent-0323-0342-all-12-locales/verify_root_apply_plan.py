#!/usr/bin/env python3
"""Verify root cross-review dispositions and exact apply plan before editing catalogs."""
import argparse,collections,hashlib,json,re,subprocess
from pathlib import Path
HERE=Path(__file__).resolve().parent
DEFAULT_REPO=Path('/mnt/disks/scratch/task-worktrees/localization-20261030/slskr-independent-review-e05f1b71-window-5400-5419-20261101')
def fail(m):raise SystemExit('FAIL: '+m)
def sha(b):return hashlib.sha256(b).hexdigest()
def h(s):return sha(s.encode('utf-8'))
def git(repo,*a,raw=False):
 b=subprocess.check_output(['git',*a],cwd=repo);return b if raw else b.decode().strip()
def read(p):return [json.loads(x) for x in Path(p).read_text(encoding='utf-8').splitlines() if x.strip()]
def placeholders(x):return sorted(set(re.findall(r'\{([^{}]+)\}',str(x))))
def icu(x):return bool(re.search(r'\{\s*[A-Za-z_][\w.-]*\s*,\s*(plural|select|selectordinal)\s*,',str(x)))
def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--repo',type=Path,default=DEFAULT_REPO);args=ap.parse_args();repo=args.repo.resolve()
 prep=json.loads((HERE/'prepare-summary.json').read_text());summary=json.loads((HERE/'root-cross-review-summary.json').read_text())
 head=prep['head'];tree=prep['head_tree'];source=prep['source_head'];source_tree=prep['source_tree']
 if git(repo,'rev-parse','HEAD')!=head or git(repo,'rev-parse','HEAD^{tree}')!=tree:fail('current review head/tree mismatch')
 if git(repo,'rev-parse',source+'^{tree}')!=source_tree:fail('source commit/tree mismatch')
 if git(repo,'status','--porcelain'):fail('worktree is not clean before application')
 main_raw=(HERE/'candidate-corrections.jsonl').read_bytes();group_raw=(HERE/'korean-discovery-inbox-group-candidates.jsonl').read_bytes()
 main_sha=sha(main_raw);group_sha=sha(group_raw)
 if main_sha!=summary['mainCandidatePlanSha256'] or group_sha!=summary['coordinatedGroupCandidatePlanSha256']:fail('candidate ledger checksum mismatch')
 if main_sha!='21a0c0ca2e0025ef42475b8341c4cc375f7acfe91bb1d86c9602f9c575baf2f6' or group_sha!='f4948754f552e395073cab20e6ec32bc6809ebf836a5a62bc50c7cc3d33186c4':fail('unexpected exact candidate pin')
 ledger_raw=(HERE/'root-cross-review.jsonl').read_bytes();plan_raw=(HERE/'root-apply-plan.jsonl').read_bytes()
 if sha(ledger_raw)!=summary['rootLedgerSha256'] or sha(plan_raw)!=summary['applyPlanSha256']:fail('root artifact checksum mismatch')
 ledger=read(HERE/'root-cross-review.jsonl');plan=read(HERE/'root-apply-plan.jsonl');candidates=read(HERE/'candidate-corrections.jsonl');group=read(HERE/'korean-discovery-inbox-group-candidates.jsonl')
 if len(ledger)!=49 or len(plan)!=47 or len(candidates)!=46 or len(group)!=4:fail('root review/apply row count mismatch')
 dispositions=collections.Counter(r['disposition'] for r in ledger)
 if dispositions!=collections.Counter({'accepted':41,'refined':6,'accepted-unchanged':2}):fail('root disposition counts mismatch')
 if any(r['nativeSpeakerReview']!='not_provided' for r in ledger):fail('native speaker approval claimed')
 cand_by={(r['source_id'],r['locale']):r for r in candidates};group_by={(r['source_id'],r['locale']):r for r in group}
 roots={(r['sourceId'],r['locale']):r for r in ledger};plans={(r['sourceId'],r['locale']):r for r in plan}
 if len(roots)!=49 or len(plans)!=47:fail('duplicate root/apply rows')
 for r in ledger:
  key=(r['sourceId'],r['locale']);cand=cand_by.get(key) or group_by.get(key)
  if cand is None:fail('root review has no exact candidate '+str(key))
  cand_sha=main_sha if cand in candidates else group_sha
  if r['candidatePlanSha256']!=cand_sha:fail('root candidate ledger pin mismatch '+str(key))
  if r['reviewHead']!=head or r['reviewTree']!=tree or r['sourceCatalogHead']!=source or r['sourceCatalogTree']!=source_tree:fail('root source/head pin mismatch '+str(key))
  current_text=cand.get('baseline_target_text',cand.get('current_target_text'))
  current_sha=cand.get('baseline_target_sha256',cand.get('current_target_sha256'))
  source_sha=cand['source_sha256']
  if r['currentTarget']!=current_text or r['currentTargetSha256']!=current_sha or r['sourceSha256']!=source_sha:fail('root baseline/source hash mismatch '+str(key))
  if r['rootTargetSha256']!=h(r['rootTarget']):fail('root target hash mismatch '+str(key))
  if placeholders(r['sourceId'])!=placeholders(r['rootTarget']):fail('root placeholder mismatch '+str(key))
  if icu(r['sourceId']) or icu(r['rootTarget']):fail('unexpected ICU syntax '+str(key))
  if r['operation']=='retain_exact':
   if r['rootTarget']!=current_text or key in plans:fail('retain operation changed target or entered apply plan '+str(key))
  elif r['operation']!='replace_exact':fail('unknown root operation '+str(key))
 for p in plan:
  key=(p['sourceId'],p['locale']);root=roots.get(key)
  if root is None or root['operation']!='replace_exact':fail('apply plan row lacks replace root disposition '+str(key))
  if p['rootLedgerSha256']!=summary['rootLedgerSha256'] or p['candidatePlanSha256']!=root['candidatePlanSha256']:fail('apply plan ledger ref mismatch '+str(key))
  if p['expectedOldTarget']!=root['currentTarget'] or p['expectedOldTargetSha256']!=root['currentTargetSha256']:fail('apply exact old target mismatch '+str(key))
  if p['newTarget']!=root['rootTarget'] or p['newTargetSha256']!=root['rootTargetSha256'] or p['rootDisposition']!=root['disposition']:fail('apply exact root target mismatch '+str(key))
  catalog=json.loads(git(repo,'show',p['reviewHead']+':'+p['catalogPath'],raw=True).decode('utf-8'))
  if catalog[p['sourceId']]!=p['expectedOldTarget'] or h(catalog[p['sourceId']])!=p['expectedOldTargetSha256']:fail('catalog current target mismatch '+str(key))
  if p['sourceSha256']!=h(p['sourceId']):fail('source ID hash mismatch '+str(key))
  if p['locale'] not in p['catalogPath']:fail('locale/catalog path mismatch '+str(key))
 paths={p['catalogPath'] for p in plan};expected={f'web/src/lib/locales/ui-labels.{loc}.json' for loc in ['ar','de','es','fr','hi','id','ja','ko','pt-BR','vi','zh-Hans','zh-Hant']}
 if not paths.issubset(expected):fail('apply plan includes non-catalog path')
 # 44 operations apply from the 46-row window ledger; the 3 sibling Korean rows are a single coherent supplement.
 main_apply=sum(r['candidateType']=='window-candidate' and r['operation']=='replace_exact' for r in plan)
 group_apply=sum(r['candidateType']=='coordinated-korean-discovery-group' for r in plan)
 if main_apply!=44 or group_apply!=3:fail('unexpected main/group operation partition')
 print(f'PASS: exact current head/tree; {len(ledger)} root-reviewed rows (38 accepted proposal, 6 refined, 2 accepted unchanged, 3 group additions included in accepted); {len(plan)} exact catalog replacements (44 window + 3 Korean siblings); source/current/new hashes, placeholders, candidate pins, and catalog paths verified.')
if __name__=='__main__':main()
