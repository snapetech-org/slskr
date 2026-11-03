#!/usr/bin/env python3
from pathlib import Path
import hashlib,json,subprocess

def sha(b): return hashlib.sha256(b).hexdigest()
def git(repo,*args): return subprocess.check_output(['git','-C',str(repo),*args])
def readj(p): return json.loads(p.read_text(encoding='utf-8'))
def readjl(p): return [json.loads(x) for x in p.read_text(encoding='utf-8').splitlines() if x.strip()]
def check_sums(folder,name='SHA256SUMS.txt'):
    for line in (folder/name).read_text().splitlines():
        if not line.strip(): continue
        digest,rel=line.split(None,1); rel=rel.strip().lstrip('*')
        assert sha((folder/rel).read_bytes())==digest,(folder/rel,'checksum mismatch')

def main():
    repo=Path(__file__).resolve().parents[5]
    rel='docs/pr-evidence/pr204-localization-2026-11-03/window-1403-1422'
    window=repo/rel; app=window/'application'; result=readj(app/'application-result.json')
    base=result['baseHead']; assert git(repo,'rev-parse','HEAD').decode().strip()!=base
    assert git(repo,'rev-parse',f'{base}^{{tree}}').decode().strip()==result['baseTree']
    check_sums(window)
    for folder in ('candidate-free-input','primary-review','independent-blind-review','cross-audit'):
        check_sums(window/folder)
    changed=git(repo,'diff','--name-only',base,'HEAD').decode().splitlines()
    expected_catalogs={x['catalogPath'] for x in readj(app/'catalog-invariants.json')['catalogs']}
    expected_evidence={p.relative_to(repo).as_posix() for p in window.rglob('*') if p.is_file()}
    assert set(changed)==expected_catalogs|expected_evidence,(set(changed)-(expected_catalogs|expected_evidence))
    assert not git(repo,'diff','--name-only',base,'HEAD','--','.github/workflows').decode().strip()
    ledger=readjl(window/'cross-audit/resolution-ledger.jsonl')
    plan=readjl(app/'apply-plan.jsonl'); readback=readjl(app/'catalog-readback.jsonl')
    assert len(ledger)==len(readback)==240 and len(plan)==66
    plan_by={(r['catalogPath'],r['sourceKey']):r for r in plan}
    by_path={x['catalogPath']:x for x in readj(app/'catalog-invariants.json')['catalogs']}
    for path,inv in by_path.items():
        raw_before=git(repo,'show',f"{base}:{path}"); before=readj_bytes(raw_before)
        after=readj(repo/path)
        assert sha(raw_before)==inv['beforeSha256'] and git(repo,'rev-parse',f'{base}:{path}').decode().strip()==inv['beforeGitBlob']
        assert len(before)==len(after)==5441 and list(before)==list(after)
        assert sha(json.dumps(list(before),ensure_ascii=False,separators=(',',':')).encode())==inv['orderedKeysSha256Before']==inv['orderedKeysSha256After']
        changed_keys=[k for k in before if before[k]!=after[k]]
        assert set(changed_keys)==set(inv['changedSourceKeys'])
        assert sha((repo/path).read_bytes())==inv['afterSha256']
    for r,rb in zip(ledger,readback):
        key=(r['catalogPath'],r['sourceKey']); before=readj_bytes(git(repo,'show',f"{base}:{r['catalogPath']}")); after=readj(repo/r['catalogPath'])
        assert before[r['sourceKey']]==r['currentTarget'] and sha(before[r['sourceKey']].encode())==r['currentTargetSha256']
        assert after[r['sourceKey']]==r['selectedTarget'] and sha(after[r['sourceKey']].encode())==r['selectedTargetSha256']
        assert rb['matches'] and rb['readbackTargetSha256']==r['selectedTargetSha256']
        assert rb['disposition']==('update' if key in plan_by else 'retain')
    holds=readjl(window/'cross-audit/independent-review/prior-hold-reattestation.jsonl')
    assert len(holds)==35
    for h in holds:
        after=readj(repo/h['currentCatalogPath'])[h['sourceKey']]
        assert sha(after.encode())==h['currentTargetSha256']==h['priorCurrentTargetSha256']
    assert result['updates']==66 and result['retains']==174 and result['newHolds']==0
    assert result['priorHoldsReattested']==result['priorHoldsPreserved']==35 and result['priorSelectionsReattested']==160
    print('PASS: W1403-W1422 240-cell readback; 66 updates, 174 retains, 35 holds preserved; catalog structure and workflows unchanged')

def readj_bytes(raw): return json.loads(raw)
if __name__=='__main__': main()
