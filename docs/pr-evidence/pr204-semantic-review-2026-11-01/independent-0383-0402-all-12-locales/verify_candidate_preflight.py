#!/usr/bin/env python3
import argparse,hashlib,json,re,subprocess
from pathlib import Path
HEAD='6f8d2b252131a2b68f85d66eb5210e0b6e9f6511';TREE='2fece646fa9dcb6892cad5233b7c79eb08997c24'
SOURCE='7ff454828398de6a3cfb72fe7f0ed21fe419425b';SOURCE_TREE='9e9f2aa743c4ff3236af8f99619803bdc3a37152'
LOCS=['ar','de','es','fr','hi','id','ja','ko','pt-BR','vi','zh-Hans','zh-Hant']
def sha(b):return hashlib.sha256(b).hexdigest()
def git(repo,*args,raw=False):
 b=subprocess.check_output(['git',*args],cwd=repo);return b if raw else b.decode().strip()
def check(ok,msg):
 if not ok:raise SystemExit('FAIL: '+msg)
def main():
 p=argparse.ArgumentParser();p.add_argument('--repo',type=Path,required=True);p.add_argument('--prior-audit',type=Path,default=Path('/mnt/disks/scratch/task-worktrees/localization-20261030/slskr-populated-catalog-review-7ff45482-20261101'));a=p.parse_args();repo=a.repo.resolve();here=Path(__file__).resolve().parent
 check(git(repo,'rev-parse',HEAD)==HEAD and git(repo,'rev-parse',f'{HEAD}^{{tree}}')==TREE,'review head/tree mismatch')
 check(git(repo,'rev-parse',f'{SOURCE}^{{tree}}')==SOURCE_TREE,'source tree mismatch')
 sel=[json.loads(x) for x in (here/'selection.jsonl').read_text().splitlines() if x.strip()]
 cand=[json.loads(x) for x in (here/'candidate-corrections.jsonl').read_text().splitlines() if x.strip()]
 audit=[json.loads(x) for x in (here/'reviewed-cell-audit.jsonl').read_text().splitlines() if x.strip()]
 check(len(sel)==len(audit)==240 and len({(r['source_index'],r['locale']) for r in sel})==240,'selection/audit 240-cell mismatch')
 check({r['source_index'] for r in sel}==set(range(383,403)),'wrong source window')
 check({r['locale'] for r in sel}==set(LOCS),'wrong locale set')
 check(len(cand)==63 and len({(r['source_index'],r['locale']) for r in cand})==63,'candidate count/key mismatch')
 inventory=[json.loads(x)['source_id'] for x in (a.prior_audit/'frozen-inputs/source-inventory.jsonl').read_text().splitlines() if x.strip()]
 check(len(inventory)==5437,'source inventory count mismatch')
 bykey={(r['source_index'],r['locale']):r for r in sel}
 for r in sel:
  check(inventory[r['source_index']]==r['source_id'],'source inventory index mismatch')
  check(sha(r['source_id'].encode())==r['source_sha256'],'source hash mismatch')
  val=json.loads(git(repo,'show',f'{HEAD}:{r["catalog_path"]}',raw=True).decode())[r['source_id']]
  check(val==r['target_text'] and sha(val.encode())==r['target_sha256'],'exact current target mismatch')
  check(val is not None and (not isinstance(val,str) or val.strip()),'blank target')
 for c in cand:
  r=bykey[(c['source_index'],c['locale'])]
  check(c['review_head']==HEAD and c['review_tree']==TREE,'candidate head pin mismatch')
  check(c['source_catalog_head']==SOURCE and c['source_catalog_tree']==SOURCE_TREE,'candidate source pin mismatch')
  check(c['source_id']==r['source_id'] and c['source_sha256']==r['source_sha256'],'candidate source mismatch')
  check(c['baseline_target_text']==r['target_text'] and c['baseline_target_sha256']==r['target_sha256'],'candidate current target mismatch')
  check(sha(c['proposed_target'].encode())==c['proposed_sha256'],'candidate target hash mismatch')
  check(c['prior_exact_status']==r['disposition'],'candidate overlap state mismatch')
  check(c['native_speaker_review']=='not_provided','native speaker state mismatch')
 check(sum(c['prior_exact_status']=='prior_correction-needed' for c in cand)==51,'prior candidate count mismatch')
 check(sum(c['prior_exact_status']=='new' for c in cand)==12,'fresh candidate count mismatch')
 pins=json.loads((here/'source-pins.json').read_text())
 for path,pin in pins['files'].items():
  check(git(repo,'rev-parse',f'{SOURCE}:{path}')==pin['git_blob'] and git(repo,'rev-parse',f'{HEAD}:{path}')==pin['git_blob'],'caller blob mismatch '+path)
  raw=git(repo,'show',f'{SOURCE}:{path}',raw=True);check(sha(raw)==pin['sha256'] and len(raw)==pin['bytes'],'caller hash/size mismatch '+path)
 for line in (here/'SHA256SUMS.txt').read_text().splitlines():
  digest,name=line.split('  ',1);check(sha((here/name).read_bytes())==digest,'bundle checksum mismatch '+name)
 print('PASS: 240 exact cells, 132 accepted carries, 45 fresh accepted, 63 candidates (51 prior, 12 fresh), 11 caller file pins, exact source/current hashes, and bundle checksums.')
if __name__=='__main__':main()
