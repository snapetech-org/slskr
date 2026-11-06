#!/usr/bin/env python3
import argparse, hashlib, json, re, subprocess, sys
from pathlib import Path

HEAD='61155e37280a60d025fda50e9115a5ef2f5cd45f'
TREE='d58ce3c148365d8d4bccd997cc4e1c561d81f76e'
SOURCE='7ff454828398de6a3cfb72fe7f0ed21fe419425b'
SOURCE_TREE='9e9f2aa743c4ff3236af8f99619803bdc3a37152'
LOCALES=['ar','de','es','fr','hi','id','ja','ko','pt-BR','vi','zh-Hans','zh-Hant']

def sha(raw): return hashlib.sha256(raw).hexdigest()
def git(repo,*args,raw=False):
    b=subprocess.check_output(['git',*args],cwd=repo)
    return b if raw else b.decode().strip()
def check(ok,msg):
    if not ok: raise SystemExit('FAIL: '+msg)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--repo',required=True,type=Path)
    ap.add_argument('--prior-audit',type=Path,default=Path('/mnt/disks/scratch/task-worktrees/localization-20261030/slskr-populated-catalog-review-7ff45482-20261101'))
    args=ap.parse_args(); repo=args.repo.resolve(); here=Path(__file__).resolve().parent
    check(git(repo,'rev-parse',HEAD)==HEAD,'review commit missing')
    check(git(repo,'rev-parse',f'{HEAD}^{{tree}}')==TREE,'review tree mismatch')
    check(git(repo,'rev-parse',f'{SOURCE}^{{tree}}')==SOURCE_TREE,'source tree mismatch')
    sel=[json.loads(x) for x in (here/'selection.jsonl').read_text().splitlines() if x.strip()]
    candidates=[json.loads(x) for x in (here/'candidate-corrections.jsonl').read_text().splitlines() if x.strip()]
    decisions=[json.loads(x) for x in (here/'reviewed-cell-audit.jsonl').read_text().splitlines() if x.strip()]
    check(len(sel)==240 and len({(r['source_index'],r['locale']) for r in sel})==240,'selection not 240 unique cells')
    check(len(decisions)==240 and len({(r['source_index'],r['locale']) for r in decisions})==240,'audit not 240 unique cells')
    check({r['source_index'] for r in sel}==set(range(363,383)),'wrong source-index window')
    check({r['locale'] for r in sel}==set(LOCALES),'wrong locale set')
    check(len(candidates)==40 and len({(r['source_index'],r['locale']) for r in candidates})==40,'candidate set not 40 unique cells')
    inventory=[json.loads(x)['source_id'] for x in (args.prior_audit/'frozen-inputs/source-inventory.jsonl').read_text().splitlines() if x.strip()]
    check(len(inventory)==5437,'frozen inventory size mismatch')
    for r in sel:
        check(inventory[r['source_index']]==r['source_id'],'source inventory index mismatch')
        check(sha(r['source_id'].encode())==r['source_sha256'],'source hash mismatch')
        raw=git(repo,'show',f'{HEAD}:{r["catalog_path"]}',raw=True)
        value=json.loads(raw.decode())[r['source_id']]
        check(value==r['target_text'],'target text differs from exact review head')
        check(sha(value.encode() if isinstance(value,str) else json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode())==r['target_sha256'],'target hash mismatch')
        check(value is not None and (not isinstance(value,str) or value.strip()),'unpopulated target')
        check(not re.search(r'\{[^{}]+\}',r['source_id']),'unexpected placeholder in source key')
    bykey={(r['source_index'],r['locale']):r for r in sel}
    dbykey={(r['source_index'],r['locale']):r for r in decisions}
    check(set(bykey)==set(dbykey),'selection and decision keysets differ')
    for c in candidates:
        key=(c['source_index'],c['locale']); r=bykey.get(key)
        check(r is not None,'candidate outside selected window')
        check(c['review_head']==HEAD and c['review_tree']==TREE,'candidate review pin mismatch')
        check(c['source_catalog_head']==SOURCE and c['source_catalog_tree']==SOURCE_TREE,'candidate source pin mismatch')
        check(c['source_id']==r['source_id'] and c['source_sha256']==r['source_sha256'],'candidate source mismatch')
        check(c['catalog_path']==r['catalog_path'],'candidate catalog path mismatch')
        check(c['baseline_target_text']==r['target_text'] and c['baseline_target_sha256']==r['target_sha256'],'candidate old-target mismatch')
        check(sha(c['proposed_target'].encode())==c['proposed_sha256'],'proposed-target hash mismatch')
        check(c['proposed_target']!=c['baseline_target_text'],'candidate is a no-op')
        check(c['prior_exact_status']==r['disposition'],'candidate overlap status mismatch')
        check(c['native_speaker_review']=='not_provided','native-speaker state inflated')
        check(not re.search(r'\{[^{}]+\}',c['source_id']),'unexpected source placeholder')
        a=dbykey[key]
        check(a['decision']=='candidate-correction-pending-cross-review' and a['candidate_sha256']==c['proposed_sha256'],'cell audit candidate mismatch')
    check(sum(1 for c in candidates if c['prior_exact_status']=='prior_correction-needed')==32,'prior correction-needed count mismatch')
    check(sum(1 for c in candidates if c['prior_exact_status']=='new')==8,'fresh candidate count mismatch')
    check(sum(1 for r in decisions if r['decision']=='accepted-prior-exact-carry')==147,'accepted carry count mismatch')
    check(sum(1 for r in decisions if r['decision']=='accepted-fresh-current')==53,'fresh accepted count mismatch')
    pins=json.loads((here/'source-pins.json').read_text())
    check(pins['review_head']==HEAD and pins['review_tree']==TREE and pins['source_commit']==SOURCE and pins['source_tree']==SOURCE_TREE,'caller pin header mismatch')
    for path,pin in pins['files'].items():
        check(git(repo,'rev-parse',f'{SOURCE}:{path}')==pin['git_blob'],'source caller Git blob mismatch: '+path)
        check(git(repo,'rev-parse',f'{HEAD}:{path}')==pin['git_blob'],'review caller Git blob mismatch: '+path)
        raw=git(repo,'show',f'{SOURCE}:{path}',raw=True)
        check(sha(raw)==pin['sha256'] and len(raw)==pin['bytes'],'caller file SHA/size mismatch: '+path)
    print('PASS: 240 exact cells; 147 accepted carries, 53 fresh accepted, 40 correction candidates (32 prior, 8 fresh), 12 caller files pinned; exact head/tree/source/candidate hashes match.')
if __name__=='__main__': main()
