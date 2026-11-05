#!/usr/bin/env python3
"""Verify sealed W1583-W1602 candidate-free inputs, live pinned source, and hash-only lineage."""
import hashlib, importlib.util, json, subprocess
from collections import Counter
from pathlib import Path
R=Path(__file__).resolve().parent
REPO=Path('/mnt/disks/scratch/task-worktrees/localization-20261104/slskr-pr209-w1583-1602-source')
PREV=Path('/home/keith/Documents/code/task-scratch/slskr-pr209-w1563-1582-primary-20261104/candidate-free-input')
APP=REPO/'docs/pr-evidence/pr209-localization-2026-11-04/window-1563-1582/application'
HEAD='e1ccc3d6509baf957f3039046e5b66dda3ae15d0'; TREE='d7c7aa967cb7faf51a8211a397859feebe8129b8'
LOCS=['es','zh-Hans','hi','de','ja','fr','pt-BR','ar','ko','zh-Hant','vi','id']; START,END=1583,1602
sha=lambda x:hashlib.sha256(x.encode() if isinstance(x,str) else x).hexdigest()
canon=lambda x:json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':'))
def j(name): return json.loads((R/name).read_text(encoding='utf-8'))
def jl(name): return [json.loads(s) for s in (R/name).read_text(encoding='utf-8').splitlines() if s]
def git(*args): return subprocess.check_output(['git',*args],cwd=REPO,text=True).strip()

def verify_sums(path):
    sums={}
    for line in (path/'SHA256SUMS.txt').read_text(encoding='utf-8').splitlines():
        d,n=line.split(None,1); n=n.lstrip('* '); assert n not in sums; sums[n]=d
    actual={p.name for p in path.iterdir() if p.is_file() and p.name!='SHA256SUMS.txt'}
    assert set(sums)==actual
    for n,d in sums.items(): assert sha((path/n).read_bytes())==d,n
    return sums
m=j('manifest.json'); assert (m['head'],m['tree'],m['selectedPositions'],m['candidateFreeInputOnly'],m['proposedTranslationsIncluded'])==(HEAD,TREE,[START,END],True,False)
sums=verify_sums(R)
assert set(m['fileHashes'])==set(sums)-{'manifest.json'}
for n,pin in m['fileHashes'].items():
    b=(R/n).read_bytes(); assert len(b)==pin['byteCount'] and sha(b)==pin['sha256']
assert git('rev-parse','HEAD')==HEAD and git('rev-parse','HEAD^{tree}')==TREE and git('status','--porcelain')==''
# Candidate-free inputs must still match the exact, sorted source queue in the pinned catalogs.
LOADER=R/'candidate-free-schema-helper.py'; spec=importlib.util.spec_from_file_location('schema_helper',LOADER); h=importlib.util.module_from_spec(spec); spec.loader.exec_module(h)
h.REPO=REPO; h.START=START; h.END=END; h.LOCS=LOCS
catalogs={}; keysets=[]; catpins=j('catalog-file-pins.json')['localeCatalogs']
for loc in LOCS:
    rel=f'web/src/lib/locales/ui-labels.{loc}.json'; raw=(REPO/rel).read_bytes(); data=json.loads(raw)
    catalogs[loc]=data; keysets.append(set(data)); pin=catpins[loc]
    assert pin['path']==rel and pin['sha256']==sha(raw) and pin['gitBlob']==git('rev-parse',f'HEAD:{rel}')
assert all(x==keysets[0] for x in keysets)
keys=sorted(keysets[0]); assert len(keys)==m['catalogSourceCount']==5441
queue=jl('source-queue.jsonl'); assert len(queue)==5441 and [x['position'] for x in queue]==list(range(1,5442))
assert [x['sourceKey'] for x in queue]==keys and all(x['sourceKeySha256']==sha(x['sourceKey']) for x in queue)
assert sha((R/'source-queue.jsonl').read_bytes())==m['sourceQueueFileSha256']
assert sha('\n'.join(keys)+'\n')==m['sourceLookupKeyOrderSha256']
assert (R/'selected-source-keys.txt').read_text(encoding='utf-8').splitlines()==keys[START-1:END]
assert [x['position'] for x in jl('source-window-boundaries.jsonl')]==list(range(START-1,END+2))
assert [x['boundary'] for x in jl('source-window-boundaries.jsonl')]==[True]+[False]*20+[True]
contexts=jl('source-contexts.jsonl'); assert [x['position'] for x in contexts]==list(range(START,END+1)); ctx={x['position']:x for x in contexts}
for x in contexts:
    assert x['sourceKey']==keys[x['position']-1] and x['sourceKeySha256']==sha(x['sourceKey'])
    assert x['productionCallerCount']==len(x['callers']) and x['callerOccurrenceCount']==sum(c['literalOccurrenceCount'] for c in x['callers'])
    assert x['callerContextSha256']==sha(canon({'sourceKey':x['sourceKey'],'callers':x['callers']}))
    for c in x['callers']:
        assert c['lineSha256']==sha(c['lineText']) and c['contextSha256']==sha(canon(c['context']))
        assert any(q['line']==c['line'] and q['text']==c['lineText'] for q in c['context'])
# Re-scan production callers with the pinned helper, and compare full contexts byte-for-byte.
scan,holds,scanned=h.contexts_for(keys[START-1:END]); assert scan==contexts
sourcepin=j('source-pin-reattestation.json')
assert scanned==sourcepin['trackedProductionJsTsFilesScanned'] and holds==jl('caller-resolution-holds.jsonl')
assert sum(x['productionCallerCount'] for x in contexts)==m['callerReferenceCount']
assert sum(x['callerOccurrenceCount'] for x in contexts)==m['callerOccurrenceCount']
assert len({c['path'] for x in contexts for c in x['callers']})==m['callerFileCount']
cells=jl('current-target-cells.jsonl'); assert len(cells)==240
assert [(x['position'],x['locale']) for x in cells]==[(p,l) for p in range(START,END+1) for l in LOCS]
bad=Counter()
for x in cells:
    p,l=x['position'],x['locale']; source=keys[p-1]; target=catalogs[l][source]; c=ctx[p]
    assert x['sourceKey']==source and x['sourceKeySha256']==sha(source) and x['sourceContextSha256']==c['callerContextSha256']
    assert x['callerCount']==c['productionCallerCount'] and x['currentTarget']==target and x['currentTargetSha256']==sha(target)
    st,tt=h.toks(source),h.toks(target)
    assert x['sourcePlaceholders']==st[0] and x['currentTargetPlaceholders']==tt[0] and x['placeholderSequenceMatches']==(st[0]==tt[0])
    assert x['sourceMarkupTags']==st[1] and x['currentTargetMarkupTags']==tt[1] and x['markupMatches']==(st[1]==tt[1])
    assert x['sourceNumericTokens']==st[2] and x['currentTargetNumericTokens']==tt[2] and x['numericTokensMatch']==(st[2]==tt[2])
    missing=[z for z in st[3] if z not in tt[3]]
    assert x['sourceProtectedLiterals']==st[3] and x['currentTargetProtectedLiterals']==tt[3] and x['protectedLiteralMismatchTokens']==missing and x['protectedLiteralsMatch']==(not missing)
    bad['placeholderSequenceMismatchCount']+=st[0]!=tt[0]; bad['markupMismatchCount']+=st[1]!=tt[1]; bad['numericTokenMismatchCount']+=st[2]!=tt[2]; bad['protectedLiteralMismatchCount']+=bool(missing)
assert dict(bad)==m['mismatchCounts']
# Every prior lineage row is text-free and its saved target hash still matches the live catalog.
lineage_files=['prior-window-selection-hash-only.jsonl','prior-selection-hash-reattestation.jsonl','prior-hold-hash-reattestation.jsonl',
 'prior-window-1503-1522-catalog-diff-hash-only.jsonl','prior-window-1523-1542-application-hash-only.jsonl','prior-window-1543-1562-application-hash-only.jsonl',
 'prior-window-1563-1582-application-hash-only.jsonl','prior-applied-target-hash-only.jsonl','prior-backfill-hold-hash-only.jsonl']
for name in lineage_files:
    for row in jl(name):
        assert not any(k in row for k in ('sourceKey','currentTarget','target','crossTarget','proposedTarget','source','targetText','lineText','selectedTarget','observedAfterTarget'))
        assert row.get('sourceKeyPositionMatches') is True
        p,l=row.get('position'),row.get('locale')
        if l in catalogs:
            actual=sha(catalogs[l][keys[p-1]])
            expected=row.get('expectedPriorTargetSha256') or row.get('priorTargetSha256') or row.get('selectedTargetSha256') or row.get('observedAfterTargetSha256')
            if expected is not None: assert actual==expected,(name,p,l)
priorwin=jl(lineage_files[0]); prior_sel=jl(lineage_files[1]); prior_holds=jl(lineage_files[2]); applied=jl(lineage_files[7]); backfill=jl(lineage_files[8])
app1503,app1523,app1543,app1563=(jl(n) for n in lineage_files[3:7])
assert len(priorwin)==m['priorWindowHashRecordCount']==1440 and len(prior_sel)==m['priorSelectionReattestationCount']==340
assert len(prior_holds)==m['carryForwardHoldCount']==62 and all(x['matchesLiveValue'] for x in prior_holds)
assert len(applied)==m['priorAppliedTargetHashCount']==65 and len(backfill)==m['priorBackfillHashOnlyHoldCount']==10
assert all(len(x)==240 for x in (app1503,app1523,app1543,app1563))
assert sum(x['priorDisposition']=='applied-update' for x in app1563)==18 and sum(x['priorDisposition']=='accept-current' for x in app1563)==222
assert all(x['liveMatchesExpectedPriorTarget'] for x in priorwin+app1503+app1523+app1543+app1563)
assert all(x['matchesLiveValue'] for x in backfill)
summary=j('prior-continuity-hash-summary.json')
assert summary['rawPriorTranslationsIncluded'] is False and summary['fullSourceOrderQueue']['exactBytesMatch'] is True
assert summary['fullSourceOrderQueue']['positionsCoveredThrough']==1582
assert summary['previousWindowCells']['recordCount']==1440 and summary['previousWindowCells']['allMatchExpectedPriorTarget'] is True
assert summary['priorSelections']['recordCount']==340 and summary['priorSelections']['allMatchLiveQueue'] is True
assert summary['priorHolds']['recordCount']==62 and summary['priorHolds']['unchangedCount']==62
assert summary['W1563AppliedHashesMatchLiveCatalog'] is True
assert j('source-order-lineage.json')['gapPositions']==[] and j('source-order-lineage.json')['overlapPositions']==[]
assert j('source-order-lineage.json')['positionsCoveredThrough']==1602
# Exact PR metadata snapshots are filtered: no body is requested or stored.
for name in ('PR-attestation.json','PR-attestation-after.json'):
    a=j(name); assert a['state']=='OPEN' and a['draft'] is True and a['head']==HEAD and a['tree']==TREE
    assert a['branchRef']==a['pullRef']==HEAD and a['baseRef']=='main' and a['baseSha']=='1bbaec9fdc63a86de343e37e33bae70d44301a36'
a,b=j('PR-attestation.json'),j('PR-attestation-after.json')
for k in ('head','tree','headRef','branchRef','pullRef','baseRef','baseSha','state','draft','deploymentsForHeadCount','deploymentsForHeadSha256','repositoryDeploymentCount','repositoryDeploymentsSha256','actionsRunsForHeadCount'): assert a[k]==b[k],k
print(json.dumps({'result':'PASS','head':HEAD,'tree':TREE,'sourceQueueRows':len(queue),'sourceWindowCells':len(cells),'callerReferences':m['callerReferenceCount'],
 'callerOccurrences':m['callerOccurrenceCount'],'callerlessPositions':m['callerResolutionHoldPositions'],'priorWindowHashRows':len(priorwin),'priorSelectionHashRows':len(prior_sel),
 'priorAppliedTargetHashes':len(applied),'priorHolds':len(prior_holds),'tokenMismatchCounts':dict(bad),'checksummedFiles':len(sums),'prRefsStable':True,'candidateFree':True},ensure_ascii=False,indent=2))
