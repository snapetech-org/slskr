#!/usr/bin/env python3
"""Verify the exact 363–382 review, root cross-review, and catalog application."""
import argparse, collections, hashlib, json, subprocess
from pathlib import Path

BASE='61155e37280a60d025fda50e9115a5ef2f5cd45f'
BASE_TREE='d58ce3c148365d8d4bccd997cc4e1c561d81f76e'
APP='267269fc7179e9445efae7ab2ed66ac95fce9a5e'
APP_TREE='9f17ede96f077d66dfcfbe4ba7766dbf35f750db'
SOURCE='7ff454828398de6a3cfb72fe7f0ed21fe419425b'
SOURCE_TREE='9e9f2aa743c4ff3236af8f99619803bdc3a37152'
CANDIDATE_SHA='ba33bee8a5196ee9f570caed213b9df84ff15acec21bbf482de0752400f468ce'
ROOT_SHA='2eff0b89297490fe1a2409ecb593e558f4bbd4344a1dfb1710bf252769892fbf'
PLAN_SHA='8dc30c6e0f772b1fc06aac1dced9806fdc6efe4b481dd19563584371a9afa9ff'
APPLIED_SHA='f3ec3caea024f0e2fbb01ce839b295917f9fa6eaaed43e9bf78b5a16ac2acf49'
LOCALES=['ar','de','es','fr','hi','id','ja','ko','pt-BR','vi','zh-Hans','zh-Hant']

def sha(b): return hashlib.sha256(b).hexdigest()
def git(repo,*args,raw=False):
    b=subprocess.check_output(['git',*args],cwd=repo)
    return b if raw else b.decode().strip()
def check(ok,msg):
    if not ok: raise SystemExit('FAIL: '+msg)
def lines(path): return [json.loads(x) for x in path.read_text(encoding='utf-8').splitlines() if x.strip()]

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--repo',required=True,type=Path)
    ap.add_argument('--prior-audit',required=True,type=Path)
    a=ap.parse_args(); repo=a.repo.resolve(); bundle=Path(__file__).resolve().parent
    check(git(repo,'rev-parse',f'{BASE}^{{tree}}')==BASE_TREE,'base tree pin mismatch')
    check(git(repo,'rev-parse',APP)==APP and git(repo,'rev-parse',f'{APP}^{{tree}}')==APP_TREE,'application commit/tree mismatch')
    check(git(repo,'rev-parse',f'{APP}^')==BASE,'catalog commit is not a direct child of exact review head')
    check(git(repo,'rev-parse',f'{SOURCE}^{{tree}}')==SOURCE_TREE,'source tree pin mismatch')
    subprocess.check_call(['git','diff','--check',BASE,APP],cwd=repo)
    expected_paths={f'web/src/lib/locales/ui-labels.{l}.json' for l in LOCALES}
    changed=set(git(repo,'diff','--name-only',BASE,APP).splitlines())
    check(changed==expected_paths,'catalog commit path set differs from 12 locale files')
    for name,expected in [('candidate-corrections.jsonl',CANDIDATE_SHA),('root-cross-review.jsonl',ROOT_SHA),('root-apply-plan.jsonl',PLAN_SHA),('applied-corrections.jsonl',APPLIED_SHA)]:
        check(sha((bundle/name).read_bytes())==expected,f'{name} SHA mismatch')
    selection=lines(bundle/'selection.jsonl'); cand=lines(bundle/'candidate-corrections.jsonl')
    root=lines(bundle/'root-cross-review.jsonl'); plan=lines(bundle/'root-apply-plan.jsonl')
    applied=lines(bundle/'applied-corrections.jsonl'); audit=lines(bundle/'reviewed-cell-audit.jsonl')
    check(len(selection)==240 and len(audit)==240,'240-cell review ledger count mismatch')
    check(len(cand)==40 and len(root)==40 and len(plan)==40 and len(applied)==40,'40-cell candidate/root/apply ledger count mismatch')
    inventory=[json.loads(x)['source_id'] for x in (a.prior_audit/'frozen-inputs/source-inventory.jsonl').read_text().splitlines() if x.strip()]
    check(len(inventory)==5437,'source inventory size mismatch')
    check(len({(x['source_index'],x['locale']) for x in selection})==240,'duplicate selected cell')
    check({x['source_index'] for x in selection}==set(range(363,383)),'wrong window indices')
    check({x['locale'] for x in selection}==set(LOCALES),'wrong locale set')
    base_by={(x['source_index'],x['locale']):x for x in selection}
    plan_by={(x['source_index'],x['locale']):x for x in plan}
    applied_by={(x['source_index'],x['locale']):x for x in applied}
    root_by={(x['sourceIndex'],x['locale']):x for x in root}
    candidate_by={(x['source_index'],x['locale']):x for x in cand}
    audit_by={(x['source_index'],x['locale']):x for x in audit}
    check(len(plan_by)==len(applied_by)==len(root_by)==len(candidate_by)==40,'duplicate/missing exact-cell ledger key')
    for x in selection:
        k=(x['source_index'],x['locale']); sid=x['source_id']; loc=x['locale']; rel=x['catalog_path']
        check(inventory[x['source_index']]==sid,'source inventory index mismatch')
        check(sha(sid.encode())==x['source_sha256'],'source ID hash mismatch')
        basecat=json.loads(git(repo,'show',f'{BASE}:{rel}',raw=True).decode())
        check(basecat.get(sid)==x['target_text'],'selection baseline value mismatch')
        check(sha(x['target_text'].encode())==x['target_sha256'],'selection baseline target hash mismatch')
        finalcat=json.loads(git(repo,'show',f'{APP}:{rel}',raw=True).decode())
        check(set(basecat)==set(finalcat),'catalog keyset mismatch')
        check(all(v is not None and (not isinstance(v,str) or v.strip()) for v in finalcat.values()),'catalog contains blank value')
        changed_keys={key for key in basecat if basecat[key]!=finalcat[key]}
        planned_keys={p['source_id'] for p in plan if p['catalog_path']==rel}
        check(changed_keys==planned_keys,'unplanned/missing catalog target change: '+loc)
        arow=audit_by[k]
        check(arow['source_id']==sid and arow['source_sha256']==x['source_sha256'],'cell audit source mismatch')
        if k in plan_by:
            p=plan_by[k]; r=root_by[k]; c=candidate_by[k]; appliedrow=applied_by[k]
            check(r['decision']=='accept' and r['nativeSpeakerApproval'] is False,'root disposition/native status mismatch')
            check(r['candidatePacketSha256']==CANDIDATE_SHA,'root candidate packet pin mismatch')
            check(c['source_id']==sid and c['baseline_target_sha256']==x['target_sha256'],'candidate baseline mismatch')
            check(p['old_target_text']==x['target_text'] and p['old_target_sha256']==x['target_sha256'],'apply plan baseline mismatch')
            final=p['final_target']; final_sha=sha(final.encode())
            check(finalcat[sid]==final and p['final_target_sha256']==final_sha,'final catalog value/hash mismatch')
            check(appliedrow['target_text']==final and appliedrow['target_sha256']==final_sha and appliedrow['status']=='corrected','applied ledger mismatch')
            check(arow['status']=='corrected' and arow['target_sha256']==final_sha,'cell audit corrected state mismatch')
        else:
            check(finalcat[sid]==x['target_text'],'unplanned target value change')
            check(arow['status']=='accepted' and arow['target_sha256']==x['target_sha256'],'accepted decision ledger mismatch')
    pins=json.loads((bundle/'source-pins.json').read_text())
    for path,pin in pins['files'].items():
        check(git(repo,'rev-parse',f'{SOURCE}:{path}')==pin['git_blob'],'source caller blob mismatch '+path)
        check(git(repo,'rev-parse',f'{BASE}:{path}')==pin['git_blob'],'base caller blob mismatch '+path)
        raw=git(repo,'show',f'{SOURCE}:{path}',raw=True)
        check(sha(raw)==pin['sha256'] and len(raw)==pin['bytes'],'caller file SHA/size mismatch '+path)
    # Validate checksums for every bundle payload other than the checksum file itself.
    for line in (bundle/'SHA256SUMS.txt').read_text().splitlines():
        digest,name=line.split('  ',1)
        check(sha((bundle/name).read_bytes())==digest,'bundle checksum mismatch '+name)
    print('PASS: exact parent/application hashes; 240 source-linked decisions; 40 accepted root corrections; only 40 planned targets changed; all 12 catalog schemas and population; 12 source callers; git diff --check and bundle checksums.')
if __name__=='__main__': main()
