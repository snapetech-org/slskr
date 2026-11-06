#!/usr/bin/env python3
import hashlib,json,re
from collections import Counter
from pathlib import Path
A=Path(__file__).resolve().parent; W=A.parent; X=W/'cross-audit'; T=X; IN=W/'candidate-free-input'
def sha(b): return hashlib.sha256(b).hexdigest()
def j(p): return json.loads(p.read_text(encoding='utf-8'))
def jl(p): return [json.loads(s) for s in p.read_text(encoding='utf-8').splitlines() if s]
def tokens(s):
    ph=re.findall(r'\{[A-Za-z][A-Za-z0-9_]*\}',s); tags=re.findall(r'<\/?[A-Za-z][^>]*>',s); nums=re.findall(r'(?<![A-Za-z])\d+(?:[.,]\d+)?%?(?![A-Za-z])',s); prot=[]
    for m in re.finditer(r'(?<![A-Za-z0-9])(?:[A-Z]{2,}[A-Z0-9]*|ffmpeg|Chromaprint|Soulseek|Spotify|YouTube|Pushbullet|Matrix|WebSocket|OpenAI)(?![A-Za-z0-9])',s):
        if m.group(0) not in prot: prot.append(m.group(0))
    return {'placeholders':ph,'markupTags':tags,'numericTokens':nums,'protectedLiterals':prot}
x=jl(X/'cross-ledger.jsonl'); plan=jl(A/'application-plan.jsonl'); read=jl(A/'readback.jsonl'); sm=j(A/'application-summary.json')
cr=j(A/'commit-record.json'); cat=j(A/'catalog-commit-attestation.json'); cf=j(IN/'manifest.json'); prior=j(X/'prior-continuity-hash-summary.json')
assert len(x)==len(read)==240 and len(plan)==59
xm={(r['position'],r['locale']):r for r in x}; pm={(r['position'],r['locale']):r for r in plan}; rm={(r['position'],r['locale']):r for r in read}
assert len(xm)==240 and len(pm)==59 and len(rm)==240
counts=Counter(r['crossDisposition'] for r in x); assert counts==Counter({'accept-current':169,'correction':29,'refinement':30,'hold':12})
assert cr['reviewedHead']=='2db7fa06845d9d94a5e5da2ddb5ecfdc04100ade' and cr['reviewedTree']=='0945d38050243ed0d52aa9d923636820c66e65ba'
assert cr['catalogCommit']=='6cf5a622ba90a4f9695bcb85728db094b566f106' and cr['catalogTree']=='27fdcb332a358ff85ac6079b3c46fddaed9c9e79' and cr['catalogCommitParent']==cr['reviewedHead']
assert cr['catalogFilesChanged']==12 and cr['catalogCellUpdates']==59 and cr['workflowFilesChanged']==0
assert cr['pushed'] is False and cr['pullRequestUpdated'] is False and cr['commitCreatedByEvidenceBundle'] is False
assert cat['catalogCommit']==cr['catalogCommit'] and cat['catalogTree']==cr['catalogTree'] and cat['catalogCommitParent']==cr['catalogCommitParent']
assert len(cat['catalogs'])==12 and {q['path'] for q in cat['catalogs']}=={q['catalogPath'] for q in plan}
assert all(q['keyCount']==5441 for q in cat['catalogs']) and len({q['orderedKeySha256'] for q in cat['catalogs']})==1
updates=0
for row in x:
    k=(row['position'],row['locale']); rb=rm[k]
    assert rb['sourceKeySha256']==row['sourceKeySha256'] and rb['crossDisposition']==row['crossDisposition'] and rb['targetTextIncluded'] is False
    if row['crossDisposition']=='hold':
        assert row['position']==1466 and row['callerCount']==0
        assert not any(key in row for key in ('sourceKey','currentTarget','crossTarget','primaryProposal','independentBlindProposal'))
        assert 'sourceKey' not in rb and not rb['changed'] and rb['expectedTargetSha256']==rb['readbackTargetSha256']==row['currentTargetSha256']
        assert row['protectedLiteralMismatch'] is True
        continue
    st=tokens(row['sourceKey']); ft=tokens(row['crossTarget']); assert st==ft
    assert rb['expectedTargetSha256']==rb['readbackTargetSha256']==row['crossTargetSha256']
    changed=row['crossDisposition'] in ('correction','refinement'); assert rb['changed']==changed
    if changed:
        updates+=1; p=pm[k]
        assert p['sourceKeySha256']==row['sourceKeySha256'] and p['callerContextSha256']==row['callerContextSha256']
        assert p['preimageTargetSha256']==row['currentTargetSha256'] and p['selectedTarget']==row['crossTarget'] and p['selectedTargetSha256']==row['crossTargetSha256']
        assert tokens(p['selectedTarget'])==st
    else: assert k not in pm and row['crossDisposition']=='accept-current'
assert updates==59
assert (sm['cellsReadBack'],sm['selectedUpdates'],sm['corrections'],sm['refinements'],sm['acceptCurrent'],sm['hashOnlyHolds'],sm['unchangedValueCount'])==(240,59,29,30,169,12,65233)
assert prior['priorSelectionReattestation']['sha256']==cf['fileHashes']['prior-selection-reattestation.jsonl']['sha256']
assert prior['carriedHoldReattestation']['sha256']==cf['fileHashes']['prior-hold-reattestation.jsonl']['sha256']
assert prior['sourceOrderLineage']['sha256']==cf['fileHashes']['source-order-lineage.json']['sha256']
for name in ('PR-attestation-before.json','PR-attestation-after.json'):
    a=j(X/name); assert a['state']=='OPEN' and a['draft'] is True
    assert a['head']==cr['reviewedHead'] and a['tree']==cr['reviewedTree'] and a['branchRef']==a['pullRef']==a['head']
    assert a['deploymentsForHeadCount']==0
print(json.dumps({'result':'PASS','cells':240,'updates':updates,'dispositions':dict(counts),'hashOnlyHolds':12,'catalogFiles':12,'unchangedValues':65233,'catalogCommit':cr['catalogCommit']},indent=2))
