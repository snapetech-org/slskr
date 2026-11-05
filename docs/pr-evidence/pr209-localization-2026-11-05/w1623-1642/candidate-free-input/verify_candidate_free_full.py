#!/usr/bin/env python3
"""Independently verify the W1623-W1642 candidate-free packet and lineage."""
import hashlib, importlib.util, json, subprocess, sys
from collections import Counter
from pathlib import Path
R=Path(__file__).resolve().parent
REPO=Path('/mnt/disks/scratch/task-scratch/slskr-pr209-w1623-1642-20261105/worktree')
PREV=Path('/mnt/disks/scratch/task-scratch/slskr-pr209-w1603-1622-20261105/candidate-free-input')
APP=REPO/'docs/pr-evidence/pr209-localization-2026-11-05/w1603-1622/application'
HEAD='7e366cbf21ad5490bd11ef418a0f2a98b3fbd567'; TREE='801d7a037c15dcd83b3e038160054a46c9b8f03b'
BASE='1bbaec9fdc63a86de343e37e33bae70d44301a36'; START,END=1623,1642
LOCS=['es','zh-Hans','hi','de','ja','fr','pt-BR','ar','ko','zh-Hant','vi','id']
sha=lambda x:hashlib.sha256(x.encode() if isinstance(x,str) else x).hexdigest()
canon=lambda x:json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':'))
def j(name): return json.loads((R/name).read_text(encoding='utf-8'))
def jl(name): return [json.loads(s) for s in (R/name).read_text(encoding='utf-8').splitlines() if s]
def jl_from_path(path): return [json.loads(s) for s in path.read_text(encoding='utf-8').splitlines() if s]
def git(*args): return subprocess.check_output(['git',*args],cwd=REPO,text=True).strip()
def check_sums(path):
    sums={}
    for line in (path/'SHA256SUMS.txt').read_text(encoding='utf-8').splitlines():
        digest,name=line.split(None,1); name=name.lstrip('* '); assert name not in sums; sums[name]=digest
    actual={p.name for p in path.iterdir() if p.is_file() and p.name!='SHA256SUMS.txt'}
    assert set(sums)==actual, (path, set(sums)^actual)
    for name,digest in sums.items(): assert sha((path/name).read_bytes())==digest, (path,name)
    return sums

m=j('manifest.json')
assert (m['head'],m['tree'],m['selectedPositions'],m['candidateFreeInputOnly'],m['proposedTranslationsIncluded'])==(HEAD,TREE,[START,END],True,False)
sums=check_sums(R); assert set(m['fileHashes'])==set(sums)-{'manifest.json'}
for name,pin in m['fileHashes'].items():
    blob=(R/name).read_bytes(); assert len(blob)==pin['byteCount'] and sha(blob)==pin['sha256'],name
assert git('rev-parse','HEAD')==HEAD and git('rev-parse','HEAD^{tree}')==TREE and git('status','--porcelain')==''
prev_manifest=json.loads((PREV/'manifest.json').read_text(encoding='utf-8')); prev_sums=check_sums(PREV)
assert (prev_manifest['head'],prev_manifest['tree'],prev_manifest['selectedPositions'],prev_manifest['candidateFreeInputOnly'],prev_manifest['proposedTranslationsIncluded'])==('eeb63f1e4e21d801f4a4e0393813b6e86a1ff7c8','590ee410666905f68f601393b64a4798b0609181',[1603,1622],True,False)
assert set(prev_manifest['fileHashes'])==set(prev_sums)-{'manifest.json'}
for name,pin in prev_manifest['fileHashes'].items(): assert sha((PREV/name).read_bytes())==pin['sha256'] and (PREV/name).stat().st_size==pin['byteCount']

sys.dont_write_bytecode=True
spec=importlib.util.spec_from_file_location('schema_helper',R/'candidate-free-schema-helper.py'); h=importlib.util.module_from_spec(spec); spec.loader.exec_module(h)
h.REPO=REPO; h.START=START; h.END=END; h.LOCS=LOCS
catalogs={}; keysets=[]; catpins=j('catalog-file-pins.json')['localeCatalogs']
for loc in LOCS:
    rel=f'web/src/lib/locales/ui-labels.{loc}.json'; raw=(REPO/rel).read_bytes(); data=json.loads(raw); catalogs[loc]=data; keysets.append(set(data)); pin=catpins[loc]
    assert pin['path']==rel and pin['sha256']==sha(raw) and pin['gitBlob']==git('rev-parse',f'HEAD:{rel}')
    assert pin['orderedKeySha256']==sha('\n'.join(data)+'\n') and pin['keyCount']==len(data)
assert all(s==keysets[0] for s in keysets)
keys=sorted(keysets[0]); assert len(keys)==m['catalogSourceCount']==5441
queue=jl('source-queue.jsonl'); assert len(queue)==5441 and [x['position'] for x in queue]==list(range(1,5442))
assert [x['sourceKey'] for x in queue]==keys and all(x['sourceKeySha256']==sha(x['sourceKey']) for x in queue)
assert (R/'source-queue.jsonl').read_bytes()==(PREV/'source-queue.jsonl').read_bytes()
assert sha((R/'source-queue.jsonl').read_bytes())==m['sourceQueueFileSha256'] and sha('\n'.join(keys)+'\n')==m['sourceLookupKeyOrderSha256']
assert (R/'selected-source-keys.txt').read_text(encoding='utf-8').splitlines()==keys[START-1:END]
assert [(i+1,keys[i]) for i in range(START-1,END)]==[(r['position'],r['sourceKey']) for r in queue[START-1:END]]
boundaries=jl('source-window-boundaries.jsonl'); assert [x['position'] for x in boundaries]==list(range(START-1,END+2))
assert [x['boundary'] for x in boundaries]==[True]+[False]*20+[True]
assert j('source-order-lineage.json')['previousWindow']=='W1603-W1622'
assert j('source-order-lineage.json')['gapPositions']==[] and j('source-order-lineage.json')['overlapPositions']==[]
assert j('source-order-lineage.json')['positionsCoveredThrough']==END

contexts=jl('source-contexts.jsonl'); assert [x['position'] for x in contexts]==list(range(START,END+1)); ctx={x['position']:x for x in contexts}
for x in contexts:
    assert x['sourceKey']==keys[x['position']-1] and x['sourceKeySha256']==sha(x['sourceKey'])
    assert x['productionCallerCount']==len(x['callers']) and x['callerOccurrenceCount']==sum(c['literalOccurrenceCount'] for c in x['callers'])
    assert x['callerContextSha256']==sha(canon({'sourceKey':x['sourceKey'],'callers':x['callers']}))
    for c in x['callers']:
        assert c['lineSha256']==sha(c['lineText']) and c['contextSha256']==sha(canon(c['context']))
        assert any(q['line']==c['line'] and q['text']==c['lineText'] for q in c['context'])
scan,holds,scanned=h.contexts_for(keys[START-1:END]); assert scan==contexts and holds==jl('caller-resolution-holds.jsonl')
assert scanned==j('source-pin-reattestation.json')['trackedProductionJsTsFilesScanned']
assert sum(x['productionCallerCount'] for x in contexts)==m['callerReferenceCount']
assert sum(x['callerOccurrenceCount'] for x in contexts)==m['callerOccurrenceCount']
assert len({c['path'] for x in contexts for c in x['callers']})==m['callerFileCount']
assert [x['position'] for x in holds]==m['callerResolutionHoldPositions']

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
assert dict(bad)==m['mismatchCounts'] and all(v==0 for v in bad.values())

# Reattest all earlier hash-only selected cells, source positions, holds, and applied targets.
lineage_names=['prior-window-selection-hash-only.jsonl','prior-selection-hash-reattestation.jsonl','prior-hold-hash-reattestation.jsonl',
 'prior-window-1503-1522-catalog-diff-hash-only.jsonl','prior-window-1523-1542-application-hash-only.jsonl','prior-window-1543-1562-application-hash-only.jsonl',
 'prior-window-1563-1582-application-hash-only.jsonl','prior-window-1583-1602-application-hash-only.jsonl','prior-window-1603-1622-application-hash-only.jsonl',
 'prior-applied-target-hash-only.jsonl','prior-backfill-hold-hash-only.jsonl']
qhash={i:sha(k) for i,k in enumerate(keys,1)}
for name in lineage_names:
    for row in jl(name):
        assert not any(k in row for k in ('sourceKey','currentTarget','target','crossTarget','proposedTarget','source','targetText','lineText','selectedTarget','observedAfterTarget')),(name,row)
        assert row.get('sourceKeyPositionMatches') is True
        p,loc=row.get('position'),row.get('locale'); assert qhash[p]==row['sourceKeySha256']
        if loc in catalogs:
            actual=sha(catalogs[loc][keys[p-1]])
            expected=row.get('expectedPriorTargetSha256') or row.get('priorTargetSha256') or row.get('selectedTargetSha256') or row.get('observedAfterTargetSha256')
            if expected is not None: assert actual==expected,(name,p,loc)
priorwin=jl(lineage_names[0]); selections=jl(lineage_names[1]); priorholds=jl(lineage_names[2])
app1503,app1523,app1543,app1563,app1583,app1603=(jl(n) for n in lineage_names[3:9])
applied=jl(lineage_names[9]); backfill=jl(lineage_names[10])
assert len(priorwin)==m['priorWindowHashRecordCount']==1920
assert len(selections)==m['priorSelectionReattestationCount']==380
assert len(priorholds)==m['carryForwardHoldCount']==62 and all(x['matchesLiveValue'] for x in priorholds)
assert len(applied)==m['priorAppliedTargetHashCount']==82 and len(backfill)==m['priorBackfillHashOnlyHoldCount']==10
assert all(len(x)==240 for x in (app1503,app1523,app1543,app1563,app1583,app1603))
assert sum(x['priorDisposition']=='applied-update' for x in app1603)==13
assert sum(x['priorDisposition']=='accept-current' for x in app1603)==227
assert all(x['liveMatchesExpectedPriorTarget'] for x in priorwin+app1503+app1523+app1543+app1563+app1583+app1603+applied)
assert all(x.get('matchesLiveValue') is True for x in backfill)
summary=j('prior-continuity-hash-summary.json')
assert summary['rawPriorTranslationsIncluded'] is False and summary['fullSourceOrderQueue']['exactBytesMatch'] is True
assert summary['fullSourceOrderQueue']['positionsCoveredThrough']==1622
assert summary['previousWindowCells']['recordCount']==1920 and summary['previousWindowCells']['allMatchExpectedPriorTarget'] is True
assert summary['priorSelections']['recordCount']==380 and summary['priorSelections']['allMatchLiveQueue'] is True
assert summary['priorHolds']['recordCount']==62 and summary['priorHolds']['unchangedCount']==62
assert summary['W1603AppliedHashesMatchLiveCatalog'] is True

# Independently recheck the immediately prior W1603-W1622 application using hashes only in emitted lineage.
app_sums=check_sums(APP)
app_summary=json.loads((APP/'application-summary.json').read_text(encoding='utf-8'))
app_raw=(APP/'readback-240-cells.jsonl').read_bytes(); app_rows=[json.loads(s) for s in app_raw.decode().splitlines() if s]
assert sha(app_raw)==m['priorApplicationReadbackSha256'] and sha((APP/'application-summary.json').read_bytes())==m['priorApplicationSummarySha256']
assert (app_summary['productCommit'],app_summary['productTree'],app_summary['changedCellCount'],app_summary['readbackCellCount'])==('bdc831fcde86101cd949fe70bd99acd8871ace4a','c9d994368a90e82f310a3c81a6ba059567c0e3bd',13,240)
assert git('rev-parse',f"{app_summary['productCommit']}^")==app_summary['baseHead']
assert git('rev-parse',f"{app_summary['productCommit']}^{{tree}}")==app_summary['productTree']
assert subprocess.call(['git','merge-base','--is-ancestor',app_summary['productCommit'],HEAD],cwd=REPO)==0
app_map={(r['position'],r['locale']):r for r in app_rows}; assert len(app_map)==240
assert [(x['position'],x['locale']) for x in app1603]==[(p,l) for p in range(1603,1623) for l in LOCS]
prev_cells={(x['position'],x['locale']):x for x in jl_from_path(PREV/'current-target-cells.jsonl')}
for key,row in app_map.items():
    lineage=next(x for x in app1603 if (x['position'],x['locale'])==key)
    p,loc=key; old=prev_cells[key]; actual=sha(catalogs[loc][keys[p-1]])
    assert row['sourceKeySha256']==old['sourceKeySha256']==lineage['sourceKeySha256']
    assert row['currentTargetSha256']==old['currentTargetSha256']==lineage['priorCurrentTargetSha256']
    assert row['postimageTargetSha256']==actual==lineage['liveCatalogTargetSha256']
    assert row['postimageTargetSha256']==lineage['expectedPriorTargetSha256']
    assert row['sourceContextSha256']==lineage['sourceContextSha256']
    assert bool(row['changed'])==(row['currentTargetSha256']!=row['postimageTargetSha256'])
assert sum(bool(r['changed']) for r in app_rows)==13

# The attestation files contain only filtered pins and no PR body content.
for name in ('PR-attestation.json','PR-attestation-after.json'):
    a=j(name); assert a['state']=='OPEN' and a['draft'] is True and a['head']==HEAD and a['tree']==TREE
    assert a['branchRef']==a['pullRef']==HEAD and a['baseRef']=='main' and a['baseSha']==BASE
before,after=j('PR-attestation.json'),j('PR-attestation-after.json')
for k in ('head','tree','headRef','branchRef','pullRef','baseRef','baseSha','state','draft','deploymentsForHeadCount','deploymentsForHeadSha256','repositoryDeploymentCount','repositoryDeploymentsSha256','actionsRunsForHeadCount'):
    assert before[k]==after[k],k
assert m['candidateFreeInputOnly'] is True and m['proposedTranslationsIncluded'] is False
print(json.dumps({'result':'PASS','head':HEAD,'tree':TREE,'sourceQueueRows':len(queue),'sourceWindowCells':len(cells),
 'callerReferences':m['callerReferenceCount'],'callerOccurrences':m['callerOccurrenceCount'],'callerlessPositions':m['callerResolutionHoldPositions'],
 'priorWindowHashRows':len(priorwin),'priorSelectionHashRows':len(selections),'priorAppliedTargetHashes':len(applied),
 'priorHolds':len(priorholds),'priorAppW1603ChangedCells':13,'tokenMismatchCounts':dict(bad),'checksummedFiles':len(sums),
 'priorPacketFilesVerified':len(prev_sums),'priorApplicationFilesVerified':len(app_sums),'prRefsStable':True,'candidateFreeOnly':True},ensure_ascii=False,indent=2))

def jl_from_path(path):
    return [json.loads(s) for s in path.read_text(encoding='utf-8').splitlines() if s]
