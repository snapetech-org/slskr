#!/usr/bin/env python3
import argparse, collections, hashlib, json, subprocess
from pathlib import Path

HEAD='6f8d2b252131a2b68f85d66eb5210e0b6e9f6511'
TREE='2fece646fa9dcb6892cad5233b7c79eb08997c24'
PLAN_SHA='745dbdbfa8431bacd34cda6a698d5b063aa34ee6419da465e0bf870554eaff19'

def sha(data): return hashlib.sha256(data).hexdigest()
def git(repo,*args): return subprocess.check_output(['git',*args],cwd=repo,text=True).strip()
def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--repo',type=Path,required=True)
    ap.add_argument('--plan',type=Path,default=Path(__file__).with_name('root-apply-plan.jsonl'))
    ap.add_argument('--summary',type=Path,default=Path(__file__).with_name('apply-summary.json'))
    ap.add_argument('--ledger',type=Path,default=Path(__file__).with_name('applied-corrections.jsonl'))
    a=ap.parse_args(); repo=a.repo.resolve()
    assert git(repo,'rev-parse','HEAD')==HEAD
    assert git(repo,'rev-parse',f'{HEAD}^{{tree}}')==TREE
    assert not git(repo,'status','--porcelain')
    plan_raw=a.plan.read_bytes(); assert sha(plan_raw)==PLAN_SHA
    plan=[json.loads(line) for line in plan_raw.decode().splitlines() if line.strip()]
    assert len(plan)==63
    pins=json.loads(Path(__file__).with_name('prepare-summary.json').read_text(encoding='utf-8'))['catalog_sha256']
    catalogs={}; before_hashes={}; after_hashes={}; changed={}
    for path,expected in pins.items():
        raw=(repo/path).read_bytes(); assert sha(raw)==expected,(path,sha(raw),expected)
        data=json.loads(raw.decode('utf-8')); catalogs[path]=data; before_hashes[path]=sha(raw)
    seen=set(); application=[]
    for row in plan:
        key=(row['sourceIndex'],row['locale']); assert key not in seen; seen.add(key)
        path=row['catalogPath']; catalog=catalogs[path]; sid=row['sourceId']
        assert sid in catalog
        current=catalog[sid]
        assert current==row['currentTarget']
        assert sha(current.encode('utf-8'))==row['currentTargetSha256']
        assert sha(sid.encode('utf-8'))==row['sourceSha256']
        if not row['apply']:
            assert row['decision']=='keep' and row['applyTarget']==current
            continue
        assert row['decision'] in {'accept','refine'}
        target=row['applyTarget']
        assert isinstance(target,str) and target.strip()
        assert sha(target.encode('utf-8'))==row['applyTargetSha256']
        catalog[sid]=target
        application.append({'application':'slskR','window':'383-402','source_index':row['sourceIndex'],'source_id':sid,'source_sha256':row['sourceSha256'],'locale':row['locale'],'catalog_path':path,'review_head':HEAD,'review_tree':TREE,'source_head':row['sourceCatalogHead'],'source_tree':row['sourceCatalogTree'],'baseline_target_text':current,'baseline_target_sha256':row['currentTargetSha256'],'review_disposition':row['decision'],'proposed_target':row['candidateTarget'],'proposed_target_sha256':row['candidateTargetSha256'],'applied_target':target,'applied_target_sha256':row['applyTargetSha256'],'status':'corrected','review_outcome':'corrected','final_target_text':target,'final_target_sha256':row['applyTargetSha256'],'root_reason':row['reason'],'root_native_speaker_approval':False})
        changed[path]=True
    assert len(application)==55 and len(seen)==63
    for path in changed:
        raw=(json.dumps(catalogs[path],ensure_ascii=False,indent=2)+'\n').encode('utf-8')
        (repo/path).write_bytes(raw); after_hashes[path]=sha(raw)
    for path in pins:
        if path not in after_hashes: after_hashes[path]=before_hashes[path]
    a.ledger.write_text(''.join(json.dumps(r,ensure_ascii=False,sort_keys=True)+'\n' for r in application),encoding='utf-8')
    counts=collections.Counter(r['review_disposition'] for r in application)
    summary={'review_head':HEAD,'review_tree':TREE,'source_head':'7ff454828398de6a3cfb72fe7f0ed21fe419425b','source_tree':'9e9f2aa743c4ff3236af8f99619803bdc3a37152','candidate_sha256':'88e51551286eae1f371454f5274ac493fa8938899ddde5347a8fcaeffc6e9433','root_decisions_sha256':'98db66ed7e1a8154b239c1de69a2ee039c649cb15af69346db3dbb4ed1f969e4','root_apply_plan_sha256':PLAN_SHA,'total_reviewed_cells':240,'root_dispositions':{'accept':38,'refine':17,'keep':8},'applied_cells':len(application),'changed_catalog_files':len(changed),'changed_paths':sorted(changed),'applied_disposition_counts':dict(sorted(counts.items())),'pre_catalog_sha256':before_hashes,'post_catalog_sha256':after_hashes,'applied_ledger_sha256':sha(a.ledger.read_bytes()),'native_speaker_approval':False}
    a.summary.write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(summary,ensure_ascii=False,indent=2))

if __name__=='__main__': main()
