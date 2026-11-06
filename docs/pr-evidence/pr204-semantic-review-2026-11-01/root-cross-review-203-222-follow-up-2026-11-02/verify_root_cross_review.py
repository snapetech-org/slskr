#!/usr/bin/env python3
"""Verify root's 86-cell cross-review and one exact Arabic refinement."""
import argparse,collections,hashlib,json,subprocess
from pathlib import Path
LOCALES=['ar','de','es','fr','hi','id','ja','ko','pt-BR','vi','zh-Hans','zh-Hant']
ROOT_SHA='8634de78c160b0cba6f5309ff02baaa30451fff02a2272cc85dcaea676ff2d14'
PLAN_SHA='9067e22a39b6135de4f5fdb79b75e2f567c5fdad78e9c2e73a88bc1187ff01c8'
def die(m):raise SystemExit('FAIL: '+m)
def sha(raw):return hashlib.sha256(raw.encode('utf-8') if isinstance(raw,str) else raw).hexdigest()
def git(repo,*args,raw=False):
 b=subprocess.run(['git',*args],cwd=repo,check=True,stdout=subprocess.PIPE).stdout
 return b if raw else b.decode().strip()
def jrows(p):return [json.loads(x) for x in p.read_text(encoding='utf-8').splitlines() if x.strip()]
def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--repo',type=Path,required=True);ap.add_argument('--prior-audit',type=Path,required=True);args=ap.parse_args();repo=args.repo.resolve();audit=args.prior_audit.resolve();bundle=Path(__file__).resolve().parent
 ledger_raw=(bundle/'root-cross-review-86.jsonl').read_bytes();plan_raw=(bundle/'root-refinement-apply-plan.jsonl').read_bytes()
 if sha(ledger_raw)!=ROOT_SHA or sha(plan_raw)!=PLAN_SHA:die('root ledger or apply-plan checksum mismatch')
 ledger=[json.loads(x) for x in ledger_raw.decode().splitlines() if x.strip()];plan=json.loads(plan_raw.decode());follow=jrows(bundle/'refinement.jsonl')
 if len(ledger)!=86 or len(follow)!=1 or len({(r['sourceId'],r['locale']) for r in ledger})!=86:die('root review row count/uniqueness mismatch')
 disp=collections.Counter(r['disposition'] for r in ledger)
 if disp!=collections.Counter({'accepted-applied-target':85,'refined':1}):die('root review disposition mismatch')
 if plan['rootCrossReviewLedgerSha256']!=ROOT_SHA or plan['reviewedTargetHash']!=follow[0]['current_target_sha256']:die('root refinement plan provenance mismatch')
 review='6a8415d2df2f22935188992e03c4636052de2d67';review_tree='f562ac9ed6108921efbef4272973b8895bb4c22a';batch_app='cea88305885c27879ecd1569944ee86bdf78e2b2';batch_app_tree='6f2e6881ca7c463eab8e39b9ea3ec08bf929be97';reviewed_app='44333cff18f24d67e5552e3289980beca8aa996d';reviewed_app_tree='4a2886515367cd8fd1acd03fb6f3eb175d1f8500';review_code='7ff454828398de6a3cfb72fe7f0ed21fe419425b';code_tree='9e9f2aa743c4ff3236af8f99619803bdc3a37152'
 if git(repo,'rev-parse',f'{batch_app}^{{tree}}')!=batch_app_tree or git(repo,'rev-parse',f'{reviewed_app}^{{tree}}')!=reviewed_app_tree or git(repo,'rev-parse',f'{review}^{{tree}}')!=review_tree or git(repo,'rev-parse',f'{review_code}^{{tree}}')!=code_tree:die('pinned review/application/source tree mismatch')
 for r in ledger:
  if (r['livePrHeadAtReview'],r['livePrTreeAtReview'],r['appliedCommitBeforeRootRefinement'],r['appliedTreeBeforeRootRefinement'])!=(review,review_tree,reviewed_app,reviewed_app_tree):die('review/application baseline mismatch')
  if r['reviewer']!='root-independent-cross-review' or r['nativeSpeakerApproval'] is not False or r['proposalRevalidatedInContext'] is not True:die('review attestation mismatch')
  if sha(r['sourceId'])!=r['sourceHash'] or sha(r['previousTargetAtPrHead'])!=r['previousTargetHash'] or sha(r['appliedTarget'])!=r['appliedTargetHash'] or sha(r['rootReviewedTarget'])!=r['rootReviewedTargetHash']:die('root ledger content hash mismatch')
  sid=r['sourceId'];loc=r['locale'];path=f'web/src/lib/locales/ui-labels.{loc}.json'
  source_cat=json.loads(git(repo,'show',f'{review}:{path}',raw=True).decode())
  applied_cat=json.loads(git(repo,'show',f'{reviewed_app}:{path}',raw=True).decode())
  if source_cat[sid]!=r['previousTargetAtPrHead'] or applied_cat[sid]!=r['appliedTarget']:die('root ledger catalog value mismatch '+loc+':'+sid)
  if r['disposition']=='accepted-applied-target' and r['rootReviewedTarget']!=r['appliedTarget']:die('accepted row does not retain applied target')
 refined=[r for r in ledger if r['disposition']=='refined']
 if len(refined)!=1:die('single refinement row missing')
 r=refined[0];f=follow[0]
 if (r['sourceId'],r['locale'],r['previousTargetAtPrHead'],r['appliedTarget'],r['appliedTargetHash'],r['rootReviewedTarget'],r['rootReviewedTargetHash'])!=(f['source_id'],f['locale'],json.loads(git(repo,'show',f'{review}:web/src/lib/locales/ui-labels.ar.json',raw=True).decode())[f['source_id']],f['previous_target'],f['previous_target_sha256'],f['current_target'],f['current_target_sha256']):die('root refinement exact row mismatch')
 if (f['source_index'],f['source_id'],f['source_sha256'],f['review_head'],f['review_tree'],f['reviewed_application_head'],f['reviewed_application_tree'])!=(209,'Adversarial Profile',r['sourceHash'],review,review_tree,'44333cff18f24d67e5552e3289980beca8aa996d','4a2886515367cd8fd1acd03fb6f3eb175d1f8500'):die('follow-up source/review pin mismatch')
 app_commit=f['application_head'];parent=f['application_parent']
 if git(repo,'rev-parse',f'{app_commit}^{{tree}}')!=f['application_tree'] or git(repo,'rev-parse',f'{app_commit}^')!=parent or git(repo,'rev-parse',f'{parent}^{{tree}}')!=f['application_parent_tree']:die('follow-up commit/tree ancestry mismatch')
 if git(repo,'merge-base','--is-ancestor',app_commit,'HEAD')!='':die('follow-up application not in current history')
 current_path=f"web/src/lib/locales/ui-labels.{r['locale']}.json"
 current=json.loads(git(repo,'show',f"HEAD:{current_path}",raw=True).decode())
 if current[f['source_id']]!=f['current_target'] or sha(current[f['source_id']])!=f['current_target_sha256']:die('current refined value mismatch')
 before=json.loads(git(repo,'show',f"{parent}:{current_path}",raw=True).decode());after=json.loads(git(repo,'show',f"{app_commit}:{current_path}",raw=True).decode())
 if before[f['source_id']]!=f['previous_target'] or after[f['source_id']]!=f['current_target']:die('focused target diff mismatch')
 changed=[]
 for loc in LOCALES:
  p=f'web/src/lib/locales/ui-labels.{loc}.json';bcat=json.loads(git(repo,'show',f'{parent}:{p}',raw=True).decode());acat=json.loads(git(repo,'show',f'{app_commit}:{p}',raw=True).decode())
  changed.extend((sid,loc) for sid in bcat if bcat[sid]!=acat[sid])
 if changed!=[(f['source_id'],'ar')]:die('root follow-up changed cells outside exact Arabic refinement')
 original_bundle=bundle.parent/'independent-0203-0222-all-12-locales';patches=jrows(original_bundle/'applied-corrections.jsonl')
 if len(patches)!=86 or sha((original_bundle/'applied-corrections.jsonl').read_bytes())!=json.loads((original_bundle/'manifest.json').read_text())['applied_corrections_ledger_sha256']:die('original 86-row application evidence changed')
 expected=[f'{sha(p.read_bytes())}  {p.name}' for p in sorted(bundle.iterdir()) if p.is_file() and p.name!='SHA256SUMS']
 if (bundle/'SHA256SUMS').read_text(encoding='utf-8').splitlines()!=expected:die('root cross-review addendum checksums mismatch')
 print('PASS: 86 exact root cross-review rows (85 accepted, 1 refined, zero held), original 86-row ledger unchanged, and one-cell Arabic refinement verified.')
if __name__=='__main__':main()
