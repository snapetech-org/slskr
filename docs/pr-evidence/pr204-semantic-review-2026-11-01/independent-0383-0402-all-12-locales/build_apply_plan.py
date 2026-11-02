#!/usr/bin/env python3
import argparse, collections, hashlib, json
from pathlib import Path

def sha(data):
    return hashlib.sha256(data).hexdigest()

def read_jsonl(path):
    return [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines() if line.strip()]

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--candidate',type=Path,default=Path(__file__).with_name('candidate-corrections.jsonl'))
    ap.add_argument('--decisions',type=Path,default=Path(__file__).with_name('root-decisions.jsonl'))
    ap.add_argument('--plan',type=Path,default=Path(__file__).with_name('root-apply-plan.jsonl'))
    ap.add_argument('--summary',type=Path,default=Path(__file__).with_name('root-apply-plan-summary.json'))
    a=ap.parse_args()
    candidate_sha=sha(a.candidate.read_bytes())
    candidates=read_jsonl(a.candidate); decisions=read_jsonl(a.decisions)
    assert len(candidates)==63 and len(decisions)==63
    c_map={(r['source_index'],r['locale']):r for r in candidates}
    d_map={(r['sourceIndex'],r['locale']):r for r in decisions}
    assert len(c_map)==len(candidates) and len(d_map)==len(decisions)
    assert set(c_map)==set(d_map)
    plans=[]; counts=collections.Counter(); locales=collections.defaultdict(collections.Counter)
    for key,c in sorted(c_map.items()):
        d=d_map[key]
        assert d['candidatePacketSha256']==candidate_sha
        for d_key,c_key in [('reviewHead','review_head'),('reviewTree','review_tree'),('sourceCatalogHead','source_catalog_head'),('sourceCatalogTree','source_catalog_tree'),('sourceId','source_id'),('sourceSha256','source_sha256'),('catalogPath','catalog_path'),('sourceContextPointer','source_context_pointer'),('sourceIndex','source_index'),('currentTarget','baseline_target_text'),('currentTargetSha256','baseline_target_sha256'),('candidateTarget','proposed_target'),('candidateTargetSha256','proposed_sha256')]:
            assert d[d_key]==c[c_key],(key,d_key)
        assert d['reviewer']=='independent-root-cross-review'
        assert d['nativeSpeakerApproval'] is False
        assert sha(d['sourceId'].encode())==d['sourceSha256']
        assert sha(d['currentTarget'].encode())==d['currentTargetSha256']
        assert sha(d['candidateTarget'].encode())==d['candidateTargetSha256']
        assert d['decision'] in {'accept','refine','keep'}
        final=d['finalTarget']
        assert isinstance(final,str) and final
        assert sha(final.encode())==d['finalTargetSha256'] if 'finalTargetSha256' in d else True
        if d['decision']=='accept': assert final==d['candidateTarget']
        elif d['decision']=='refine': assert final!=d['candidateTarget']
        else: assert final==d['currentTarget']
        apply=d['decision'] in {'accept','refine'}
        plan=dict(d)
        plan['apply']=apply
        plan['applyTarget']=final
        plan['applyTargetSha256']=sha(final.encode())
        plans.append(plan); counts[d['decision']]+=1; locales[d['locale']][d['decision']]+=1
    assert dict(counts)=={'accept':38,'refine':17,'keep':8},counts
    assert sum(counts[x] for x in ('accept','refine'))==55
    a.plan.write_text(''.join(json.dumps(r,ensure_ascii=False,sort_keys=True)+'\n' for r in plans),encoding='utf-8')
    summary={'schemaVersion':1,'candidatePacketSha256':candidate_sha,'rootDecisionsSha256':sha(a.decisions.read_bytes()),'rows':len(plans),'decisionCounts':dict(sorted(counts.items())),'applyCount':55,'keepCount':8,'perLocale':{k:dict(sorted(v.items())) for k,v in sorted(locales.items())},'planSha256':sha(a.plan.read_bytes()),'nativeSpeakerApproval':False}
    a.summary.write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(summary,ensure_ascii=False,indent=2))

if __name__=='__main__': main()
