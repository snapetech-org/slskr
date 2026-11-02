#!/usr/bin/env python3
"""Verify the exact-head 383–402 review, root decisions, and catalog-only application."""
import argparse, collections, hashlib, json, re, subprocess
from pathlib import Path

REVIEW_HEAD='6f8d2b252131a2b68f85d66eb5210e0b6e9f6511'
REVIEW_TREE='2fece646fa9dcb6892cad5233b7c79eb08997c24'
CATALOG_COMMIT='83aef2e22cede4041943bd0d612357e152e7a9b5'
CATALOG_TREE='927bae235b4b57ac51a64389e6becadd75b133c3'
SOURCE_HEAD='7ff454828398de6a3cfb72fe7f0ed21fe419425b'
SOURCE_TREE='9e9f2aa743c4ff3236af8f99619803bdc3a37152'
CANDIDATE_SHA='88e51551286eae1f371454f5274ac493fa8938899ddde5347a8fcaeffc6e9433'
ROOT_DECISIONS_SHA='98db66ed7e1a8154b239c1de69a2ee039c649cb15af69346db3dbb4ed1f969e4'
APPLY_PLAN_SHA='745dbdbfa8431bacd34cda6a698d5b063aa34ee6419da465e0bf870554eaff19'
LOCALES=['ar','de','es','fr','hi','id','ja','ko','pt-BR','vi','zh-Hans','zh-Hant']

def sha(raw): return hashlib.sha256(raw).hexdigest()
def read_jsonl(path): return [json.loads(x) for x in path.read_text(encoding='utf-8').splitlines() if x.strip()]
def git(repo,*args): return subprocess.check_output(['git',*args],cwd=repo,text=True).strip()
def blob(repo,commit,path): return subprocess.check_output(['git','show',f'{commit}:{path}'],cwd=repo)
def fail(condition,message):
    if not condition: raise SystemExit('FAIL: '+message)
def nonempty(value):
    if isinstance(value,str): return bool(value.strip())
    if isinstance(value,dict): return bool(value) and all(nonempty(v) for v in value.values())
    if isinstance(value,list): return bool(value) and all(nonempty(v) for v in value)
    return value is not None

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--repo',type=Path,required=True)
    parser.add_argument('--prior-audit',type=Path,required=True)
    args=parser.parse_args(); repo=args.repo.resolve(); audit=args.prior_audit.resolve()
    here=Path(__file__).resolve().parent
    fail(git(repo,'rev-parse',f'{REVIEW_HEAD}^{{tree}}')==REVIEW_TREE,'review head tree mismatch')
    fail(git(repo,'rev-parse',f'{CATALOG_COMMIT}^')==REVIEW_HEAD,'catalog commit is not a direct child of reviewed head')
    fail(git(repo,'rev-parse',f'{CATALOG_COMMIT}^{{tree}}')==CATALOG_TREE,'catalog application tree mismatch')
    fail(git(repo,'rev-parse',f'{SOURCE_HEAD}^{{tree}}')==SOURCE_TREE,'source tree mismatch')
    fail(sha((here/'candidate-corrections.jsonl').read_bytes())==CANDIDATE_SHA,'candidate ledger hash mismatch')
    fail(sha((here/'root-cross-review.jsonl').read_bytes())==ROOT_DECISIONS_SHA,'root decisions hash mismatch')
    fail(sha((here/'root-apply-plan.jsonl').read_bytes())==APPLY_PLAN_SHA,'apply plan hash mismatch')
    # Verify the final bundle checksum manifest (all files except the manifest itself).
    listed=set()
    for line in (here/'SHA256SUMS.txt').read_text(encoding='utf-8').splitlines():
        digest,name=line.split('  ',1); path=here/name
        fail(path.is_file(),f'missing checksum file: {name}')
        fail(sha(path.read_bytes())==digest,f'bundle checksum mismatch: {name}')
        listed.add(name)
    actual={p.relative_to(here).as_posix() for p in here.rglob('*') if p.is_file() and p.name!='SHA256SUMS.txt'}
    fail(actual==listed,f'bundle checksum inventory differs: missing={sorted(actual-listed)} extra={sorted(listed-actual)}')
    # Recheck baseline exact-target/source/caller pins using the frozen source audit.
    subprocess.run(['python3',str(here/'verify_candidate_preflight.py'),'--repo',str(repo),'--prior-audit',str(audit)],check=True)
    prep=json.loads((here/'prepare-summary.json').read_text(encoding='utf-8'))
    selection=read_jsonl(here/'selection.jsonl'); audit_rows=read_jsonl(here/'reviewed-cell-audit.jsonl')
    candidates=read_jsonl(here/'candidate-corrections.jsonl'); decisions=read_jsonl(here/'root-cross-review.jsonl')
    plan=read_jsonl(here/'root-apply-plan.jsonl'); applied=read_jsonl(here/'applied-corrections.jsonl')
    accepted=read_jsonl(here/'accepted-dispositions.jsonl')
    fail(prep['head']==REVIEW_HEAD and prep['head_tree']==REVIEW_TREE,'prepare head pin mismatch')
    fail(prep['source_head']==SOURCE_HEAD and prep['source_tree']==SOURCE_TREE,'prepare source pin mismatch')
    fail(len(selection)==len(audit_rows)==240,'selection/audit row count mismatch')
    fail(len(candidates)==len(decisions)==len(plan)==63,'candidate/root/plan row count mismatch')
    fail(len(applied)==55 and len(accepted)==177,'applied/accepted disposition row count mismatch')
    fail({r['source_index'] for r in selection}==set(range(383,403)),'wrong source window')
    sel_map={(r['source_index'],r['locale']):r for r in selection}
    audit_map={(r['source_index'],r['locale']):r for r in audit_rows}
    cand_map={(r['source_index'],r['locale']):r for r in candidates}
    dec_map={(r['sourceIndex'],r['locale']):r for r in decisions}
    plan_map={(r['sourceIndex'],r['locale']):r for r in plan}
    fail(all(len(x)==len(set(x)) for x in (sel_map,audit_map,cand_map,dec_map,plan_map)),'duplicate source/locale row')
    fail(set(sel_map)==set(audit_map),'selection/audit cells differ')
    fail(set(cand_map)==set(dec_map)==set(plan_map),'candidate/root/plan cells differ')
    status_counts=collections.Counter(r['decision'] for r in decisions)
    fail(status_counts=={'accept':38,'refine':17,'keep':8},f'root decision counts mismatch: {status_counts}')
    fail(sum(bool(r['apply']) for r in plan)==55,'apply plan row count mismatch')
    inventory=[json.loads(x)['source_id'] for x in (audit/'frozen-inputs/source-inventory.jsonl').read_text(encoding='utf-8').splitlines() if x.strip()]
    fail(len(inventory)==5437 and len(set(inventory))==5437,'frozen source inventory mismatch')
    for (idx,locale),row in sel_map.items():
        fail(locale in LOCALES and row['source_id']==inventory[idx],'source index mismatch')
        fail(sha(row['source_id'].encode())==row['source_sha256'],'selected source hash mismatch')
        fail(locale in LOCALES,'unexpected locale')
    base_catalogs={}; final_catalogs={}; structured=collections.Counter(); catalog_hashes={}
    for locale in LOCALES:
        path=f'web/src/lib/locales/ui-labels.{locale}.json'
        base=json.loads(blob(repo,REVIEW_HEAD,path).decode('utf-8'))
        final_raw=blob(repo,CATALOG_COMMIT,path); final=json.loads(final_raw.decode('utf-8'))
        fail(set(base)==set(inventory)==set(final),f'catalog key parity mismatch: {locale}')
        fail(all(nonempty(v) for v in final.values()),f'blank catalog value: {locale}')
        for v in final.values():
            if isinstance(v,(dict,list)): structured[locale]+=1
        base_catalogs[path]=base; final_catalogs[path]=final; catalog_hashes[path]=sha(final_raw)
        fail(sha(blob(repo,REVIEW_HEAD,path))==prep['catalog_sha256'][path],f'baseline catalog hash mismatch: {path}')
    fail(sum(structured.values())==15 and dict(structured)=={'ar':15},'structured ICU/plural inventory mismatch')
    planned={}; changed=[]
    for key,r in plan_map.items():
        path=r['catalogPath']; sid=r['sourceId']; base=base_catalogs[path][sid]; final=final_catalogs[path][sid]
        fail(base==r['currentTarget'] and sha(base.encode())==r['currentTargetSha256'],f'baseline target mismatch: {key}')
        if r['apply']:
            fail(final==r['applyTarget'] and sha(final.encode())==r['applyTargetSha256'],f'applied target mismatch: {key}')
            planned[(path,sid)]=r['applyTarget']; changed.append((path,sid))
        else:
            fail(r['decision']=='keep' and final==base,f'keep-current target changed: {key}')
    actual_changes=[]
    for path,base in base_catalogs.items():
        for sid,value in base.items():
            if final_catalogs[path][sid]!=value: actual_changes.append((path,sid))
    fail(set(actual_changes)==set(changed) and len(actual_changes)==55,'catalog diff contains unplanned cells')
    applied_map={(r['source_index'],r['locale']):r for r in applied}
    fail(len(applied_map)==55,'duplicate applied correction row')
    for key,r in plan_map.items():
        if r['apply']:
            a=applied_map.get(key); fail(a is not None,f'missing applied ledger row: {key}')
            fail(a['status']=='corrected' and a['review_outcome']=='corrected','applied terminal status missing')
            fail(a['source_id']==r['sourceId'] and a['source_sha256']==r['sourceSha256'],'applied source pin mismatch')
            fail(a['baseline_target_sha256']==r['currentTargetSha256'],'applied baseline hash mismatch')
            fail(a['final_target_sha256']==r['applyTargetSha256'] and a['applied_target']==r['applyTarget'],'applied final hash mismatch')
    accepted_map={(r['source_index'],r['locale']):r for r in accepted}
    fail(len(accepted_map)==177,'duplicate accepted row')
    for key,r in accepted_map.items():
        s=sel_map.get(key); fail(s is not None,'accepted cell outside selection')
        p=s['catalog_path']; sid=s['source_id']; value=final_catalogs[p][sid]
        fail(r['status']=='accepted' and r['review_outcome']=='accepted','accepted terminal status missing')
        fail(r['source_id']==sid and r['source_sha256']==s['source_sha256'],'accepted source mismatch')
        fail(r['target_text']==value and r['target_sha256']==sha(value.encode()),'accepted target mismatch')
    keep_rows=[r for r in decisions if r['decision']=='keep']
    fail(len(keep_rows)==8 and all(r['sourceIndex']==393 for r in keep_rows),'keep-current contextual hold mismatch')
    changed_paths=set(subprocess.check_output(['git','diff','--name-only',REVIEW_HEAD,CATALOG_COMMIT],cwd=repo,text=True).splitlines())
    expected_paths={path for path,_ in changed}
    fail(changed_paths==expected_paths and len(changed_paths)==12,'catalog commit path set mismatch')
    diff=subprocess.check_output(['git','diff','--check',REVIEW_HEAD,CATALOG_COMMIT],cwd=repo,text=True)
    fail(not diff,'git diff --check reported whitespace errors')
    print(json.dumps({'result':'PASS','catalog_commit':CATALOG_COMMIT,'catalog_tree':CATALOG_TREE,'reviewed_cells':240,'root_dispositions':dict(status_counts),'applied_corrections':55,'accepted_cells':177,'keep_current':8,'changed_catalog_files':len(changed_paths),'catalog_keys_per_locale':5437,'structured_plural_cells':dict(structured),'catalog_sha256':catalog_hashes,'git_diff_check':'passed','native_speaker_approval':False},ensure_ascii=False,indent=2))

if __name__=='__main__': main()
