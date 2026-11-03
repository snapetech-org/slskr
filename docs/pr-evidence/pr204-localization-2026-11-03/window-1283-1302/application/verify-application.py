#!/usr/bin/env python3
import hashlib,json,subprocess,re
from pathlib import Path
from collections import Counter

HERE=Path(__file__).resolve()
APP=HERE.parent
EVIDENCE=APP.parent
REPO=HERE.parents[5]
BUNDLE=EVIDENCE/'review-bundle'
def sha_bytes(b): return hashlib.sha256(b).hexdigest()
def sha_text(s): return sha_bytes(s.encode('utf-8'))
def readj(p): return json.loads(p.read_text(encoding='utf-8'))
def readjl(p): return [json.loads(x) for x in p.read_text(encoding='utf-8').splitlines() if x]

# Verify the embedded review packet without consulting any external proposal.
subprocess.check_call(['sha256sum','-c','ROOT-SHA256SUMS.txt'],cwd=BUNDLE,stdout=subprocess.DEVNULL)
for d in ['candidate-free-input','primary-review','blind-review','cross-audit']:
    subprocess.check_call(['sha256sum','-c','SHA256SUMS.txt'],cwd=BUNDLE/d,stdout=subprocess.DEVNULL)
manifest=readj(BUNDLE/'candidate-free-input/manifest.json')
auth=readj(BUNDLE/'application-authorization.json')
cross_summary=readj(BUNDLE/'cross-audit/summary.json')
plan=readjl(APP/'application-plan-240-cells.jsonl')
readback=readjl(APP/'readback-240-cells.jsonl')
invariants=readj(APP/'application-invariants.json')
provenance=readj(APP/'provenance.json')
bundle_validation=readj(APP/'bundle-validation.json')
assert len(plan)==len(readback)==240
assert invariants['selectedUpdates']==auth['exactSelectedTargets']==cross_summary['selectedUpdates']==145
assert invariants['acceptCurrent']==95 and invariants['holds']==0
assert invariants['parentHead']==manifest['head']=='55ca2ae0788bfd79daab5cc49f49ebb608593e98'
assert invariants['parentTree']==manifest['tree']=='d5677673b766d572102bba249af2ab69095dea0d'
assert auth['authorized'] is True
assert bundle_validation['rootSums']=='PASS'
assert bundle_validation['crossAuditVerifier']=='PASS'
assert bundle_validation['primaryVerifier']=='PASS'
assert bundle_validation['blindVerifier']=='PASS'
assert bundle_validation['candidateFreeInputSums']=='PASS'

plan_map={(r['position'],r['locale']):r for r in plan}
readback_map={(r['position'],r['locale']):r for r in readback}
assert len(plan_map)==len(readback_map)==240
assert set(plan_map)==set(readback_map)
assert len({r['sourceKey'] for r in plan})==20
assert {r['position'] for r in plan}==set(range(1283,1303))
cross_ledger=readjl(BUNDLE/'cross-audit/cross-audit-ledger.jsonl')
cross_map={(r['position'],r['locale']):r for r in cross_ledger}
assert set(cross_map)==set(plan_map)
update_count=0
accept_count=0
for key,p in plan_map.items():
    c=cross_map[key]
    assert p['sourceKey']==c['sourceKey'] and p['sourceKeySha256']==c['sourceKeySha256']
    assert p['currentTarget']==c['currentTarget'] and p['currentTargetSha256']==c['currentTargetSha256']
    assert p['selectedTarget']==c['selectedTarget'] and p['selectedTargetSha256']==c['selectedTargetSha256']
    assert p['disposition']==c['disposition'] and p['selectedUpdate']==(c['selectedTarget']!=c['currentTarget'])
    r=readback_map[key]
    assert r['sourceKey']==p['sourceKey'] and r['sourceKeySha256']==p['sourceKeySha256']
    assert r['currentTarget']==p['currentTarget'] and r['currentTargetSha256']==p['currentTargetSha256']
    assert r['selectedTarget']==p['selectedTarget'] and r['selectedTargetSha256']==p['selectedTargetSha256']
    assert r['actualTarget']==p['selectedTarget']
    assert r['actualTargetSha256']==p['selectedTargetSha256']==sha_text(r['actualTarget'])
    assert r['matchesSelectedTarget'] is True
    assert r['changedFromParent']==p['selectedUpdate']==(p['selectedTarget']!=p['currentTarget'])
    if p['selectedUpdate']: update_count+=1
    else:
        accept_count+=1
        assert p['disposition']=='accept-current'
        assert r['actualTarget']==p['currentTarget']
    assert r['structuralEvidence']==p['structuralEvidence']
assert update_count==145 and accept_count==95

# Check each full locale catalog, preserving key set/order and every non-window value.
for cat in invariants['catalogs']:
    path=REPO/cat['path']
    raw=path.read_bytes()
    assert sha_bytes(raw)==cat['afterFileSha256']
    data=json.loads(raw.decode('utf-8'))
    keys=list(data)
    assert len(keys)==cat['afterKeyCount']==5441
    key_digest=sha_bytes(('\n'.join(keys)+'\n').encode('utf-8'))
    assert key_digest==cat['beforeOrderedKeySha256']==cat['afterOrderedKeySha256']
    window_keys={r['sourceKey'] for r in plan if r['locale']==cat['locale']}
    pairs=[(k,data[k]) for k in keys if k not in window_keys]
    nonwindow=sha_bytes(json.dumps(pairs,ensure_ascii=False,separators=(',',':')).encode('utf-8'))
    assert nonwindow==cat['beforeNonWindowValuesSha256']==cat['afterNonWindowValuesSha256']
    for r in plan:
        if r['locale']==cat['locale']:
            assert data[r['sourceKey']]==r['selectedTarget']
    assert cat['beforeKeyCount']==cat['afterKeyCount']

# Historical rank-1257 Ecosystem holds must remain exact in every locale.
prev_path=REPO/'docs/pr-evidence/pr204-localization-2026-11-03/window-1243-1262/application/readback-240-cells.jsonl'
prev=[r for r in readjl(prev_path) if r['position']==1257]
assert len(prev)==12
hold_map={r['locale']:r for r in prev}
assert all(r['disposition']=='hold' and r['changedFromParent'] is False for r in prev)
for h in invariants['historicalRank1257Hold']:
    prior=hold_map[h['locale']]
    assert prior['sourceKey']=='Ecosystem'
    assert h['target']==prior['actualTarget']==prior['expectedTarget']
    assert h['targetSha256']==prior['actualSha256']==prior['expectedSha256']
    cat=next(x for x in invariants['catalogs'] if x['locale']==h['locale'])
    data=json.loads((REPO/cat['path']).read_text(encoding='utf-8'))
    assert data['Ecosystem']==h['target']
    assert sha_text(data['Ecosystem'])==h['targetSha256']

# The focused commit must contain only the 12 locale catalogs and this evidence directory.
parent=invariants['parentHead']
head=subprocess.check_output(['git','-C',str(REPO),'rev-parse','HEAD'],text=True).strip()
tree=subprocess.check_output(['git','-C',str(REPO),'rev-parse','HEAD^{tree}'],text=True).strip()
ancestor=subprocess.run(['git','-C',str(REPO),'merge-base','--is-ancestor',parent,head],check=False)
assert ancestor.returncode==0
changed=subprocess.check_output(['git','-C',str(REPO),'diff','--name-only',parent+'..'+head],text=True).splitlines()
allowed=set(invariants['catalogPaths']) | {p.relative_to(REPO).as_posix() for p in EVIDENCE.rglob('*') if p.is_file()}
assert set(changed)==allowed,(sorted(set(changed)-allowed),sorted(allowed-set(changed)))
assert not any(p.startswith('.github/workflows/') for p in changed)
status=subprocess.check_output(['git','-C',str(REPO),'status','--porcelain'],text=True)
assert status==''
print(json.dumps({'result':'PASS','head':head,'tree':tree,'parent':parent,'readbackCells':len(readback),'selectedUpdates':update_count,'acceptCurrent':accept_count,'holds':0,'preservedRank1257Holds':len(prev),'catalogs':len(invariants['catalogs']),'nonWindowValuesAndKeyOrderPreserved':True,'diffPaths':len(changed),'worktreeClean':True},indent=2))
