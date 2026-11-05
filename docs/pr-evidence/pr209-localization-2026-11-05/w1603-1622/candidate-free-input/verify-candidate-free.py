#!/usr/bin/env python3
"""Independently verify sealed exact-head candidate-free inputs and lineage."""
import hashlib, importlib.util, json, subprocess, sys
from collections import Counter
from pathlib import Path
R=Path(__file__).resolve().parent
REPO=Path('/mnt/disks/scratch/task-worktrees/localization-20261105/slskr-pr209-w1603-1622-pinned')
PREV=Path('/home/keith/Documents/code/task-scratch/slskr-pr209-w1583-1602-20261104/candidate-free-input')
APP=REPO/'docs/pr-evidence/pr209-localization-2026-11-04/window-1583-1602/application'
HEAD='eeb63f1e4e21d801f4a4e0393813b6e86a1ff7c8'; TREE='590ee410666905f68f601393b64a4798b0609181'
BASE='1bbaec9fdc63a86de343e37e33bae70d44301a36'; START,END=1603,1622
LOCS=['es','zh-Hans','hi','de','ja','fr','pt-BR','ar','ko','zh-Hant','vi','id']
sha=lambda x:hashlib.sha256(x.encode() if isinstance(x,str) else x).hexdigest()
canon=lambda x:json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':'))
def j(name): return json.loads((R/name).read_text(encoding='utf-8'))
def jl(name): return [json.loads(s) for s in (R/name).read_text(encoding='utf-8').splitlines() if s]
def git(*args): return subprocess.check_output(['git',*args],cwd=REPO,text=True).strip()
def check_sums(path):
    sums={}
    for line in (path/'SHA256SUMS.txt').read_text(encoding='utf-8').splitlines():
        d,n=line.split(None,1); n=n.lstrip('* '); assert n not in sums; sums[n]=d
    actual={p.name for p in path.iterdir() if p.is_file() and p.name!='SHA256SUMS.txt'}
    assert set(sums)==actual
    for n,d in sums.items(): assert sha((path/n).read_bytes())==d,n
    return sums

m=j('manifest.json'); assert (m['head'],m['tree'],m['selectedPositions'],m['candidateFreeInputOnly'],m['proposedTranslationsIncluded'])==(HEAD,TREE,[START,END],True,False)
sums=check_sums(R); assert set(m['fileHashes'])==set(sums)-{'manifest.json'}
for n,pin in m['fileHashes'].items():
    b=(R/n).read_bytes(); assert len(b)==pin['byteCount'] and sha(b)==pin['sha256']
assert git('rev-parse','HEAD')==HEAD and git('rev-parse','HEAD^{tree}')==TREE and git('status','--porcelain')==''
prev_manifest=json.loads((PREV/'manifest.json').read_text(encoding='utf-8'))
prev_sums=check_sums(PREV)
assert (prev_manifest['head'],prev_manifest['tree'],prev_manifest['selectedPositions'])==('e1ccc3d6509baf957f3039046e5b66dda3ae15d0','d7c7aa967cb7faf51a8211a397859feebe8129b8',[1583,1602])
assert set(prev_manifest['fileHashes'])==set(prev_sums)-{'manifest.json'}

sys.dont_write_bytecode=True
spec=importlib.util.spec_from_file_location('schema_helper',R/'candidate-free-schema-helper.py'); h=importlib.util.module_from_spec(spec); spec.loader.exec_module(h)
h.REPO=REPO; h.START=START; h.END=END; h.LOCS=LOCS
catalogs={}; keysets=[]; catpins=j('catalog-file-pins.json')['localeCatalogs']
for loc in LOCS:
    rel=f'web/src/lib/locales/ui-labels.{loc}.json'; raw=(REPO/rel).read_bytes(); data=json.loads(raw); catalogs[loc]=data; keysets.append(set(data)); pin=catpins[loc]
    assert pin['path']==rel and pin['sha256']==sha(raw) and pin['gitBlob']==git('rev-parse',f'HEAD:{rel}')
    assert pin['orderedKeySha256']==sha('\n'.join(data)+'\n') and pin['keyCount']==len(data)
assert all(x==keysets[0] for x in keysets)
keys=sorted(keysets[0]); assert len(keys)==m['catalogSourceCount']==5441
queue=jl('source-queue.jsonl'); assert len(queue)==5441 and [x['position'] for x in queue]==list(range(1,5442))
assert [x['sourceKey'] for x in queue]==keys and all(x['sourceKeySha256']==sha(x['sourceKey']) for x in queue)
assert (R/'source-queue.jsonl').read_bytes()==(PREV/'source-queue.jsonl').read_bytes()
assert sha((R/'source-queue.jsonl').read_bytes())==m['sourceQueueFileSha256'] and sha('\n'.join(keys)+'\n')==m['sourceLookupKeyOrderSha256']
assert (R/'selected-source-keys.txt').read_text(encoding='utf-8').splitlines()==keys[START-1:END]
boundary=jl('source-window-boundaries.jsonl'); assert [x['position'] for x in boundary]==list(range(START-1,END+2))
assert [x['boundary'] for x in boundary]==[True]+[False]*20+[True]
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

lineage_names=['prior-window-selection-hash-only.jsonl','prior-selection-hash-reattestation.jsonl','prior-hold-hash-reattestation.jsonl',
 'prior-window-1503-1522-catalog-diff-hash-only.jsonl','prior-window-1523-1542-application-hash-only.jsonl','prior-window-1543-1562-application-hash-only.jsonl',
 'prior-window-1563-1582-application-hash-only.jsonl','prior-window-1583-1602-application-hash-only.jsonl','prior-applied-target-hash-only.jsonl','prior-backfill-hold-hash-only.jsonl']
qhash={i:sha(k) for i,k in enumerate(keys,1)}
for name in lineage_names:
    for row in jl(name):
        assert not any(k in row for k in ('sourceKey','currentTarget','target','crossTarget','proposedTarget','source','targetText','lineText','selectedTarget','observedAfterTarget')),(name,row)
        assert row.get('sourceKeyPositionMatches') is True
        p,l=row.get('position'),row.get('locale'); assert qhash[p]==row['sourceKeySha256']
        if l in catalogs:
            actual=sha(catalogs[l][keys[p-1]])
            expected=row.get('expectedPriorTargetSha256') or row.get('priorTargetSha256') or row.get('selectedTargetSha256') or row.get('observedAfterTargetSha256')
            if expected is not None: assert actual==expected,(name,p,l)
priorwin=jl(lineage_names[0]); selections=jl(lineage_names[1]); priorholds=jl(lineage_names[2]); applied=jl(lineage_names[8]); backfill=jl(lineage_names[9])
app1503,app1523,app1543,app1563,app1583=(jl(n) for n in lineage_names[3:8])
assert len(priorwin)==m['priorWindowHashRecordCount']==1680 and len(selections)==m['priorSelectionReattestationCount']==360
assert len(priorholds)==m['carryForwardHoldCount']==62 and all(x['matchesLiveValue'] for x in priorholds)
assert len(applied)==m['priorAppliedTargetHashCount']==69 and len(backfill)==m['priorBackfillHashOnlyHoldCount']==10
assert all(len(x)==240 for x in (app1503,app1523,app1543,app1563,app1583))
assert sum(x['priorDisposition']=='applied-update' for x in app1583)==4 and sum(x['priorDisposition']=='accept-current' for x in app1583)==236
assert all(x['liveMatchesExpectedPriorTarget'] for x in priorwin+app1503+app1523+app1543+app1563+app1583+applied)
assert all(x.get('matchesLiveValue') is True for x in backfill)
summary=j('prior-continuity-hash-summary.json')
assert summary['rawPriorTranslationsIncluded'] is False and summary['fullSourceOrderQueue']['exactBytesMatch'] is True
assert summary['fullSourceOrderQueue']['positionsCoveredThrough']==1602
assert summary['previousWindowCells']['recordCount']==1680 and summary['previousWindowCells']['allMatchExpectedPriorTarget'] is True
assert summary['priorSelections']['recordCount']==360 and summary['priorSelections']['allMatchLiveQueue'] is True
assert summary['priorHolds']['recordCount']==62 and summary['priorHolds']['unchangedCount']==62 and summary['W1583AppliedHashesMatchLiveCatalog'] is True
assert j('source-order-lineage.json')['gapPositions']==[] and j('source-order-lineage.json')['overlapPositions']==[]
assert j('source-order-lineage.json')['positionsCoveredThrough']==1622

# Independently compare the carried-forward W1583 catalog diff with its pinned readback.
app_summary=json.loads((APP/'application-summary.json').read_text(encoding='utf-8'))
app_raw=(APP/'apply-readback-cells.jsonl').read_bytes(); app_rows=[json.loads(s) for s in app_raw.decode().splitlines() if s]
assert sha(app_raw)==m['priorApplicationReadbackSha256'] and sha((APP/'application-summary.json').read_bytes())==m['priorApplicationSummarySha256']
old_cells={(x['position'],x['locale']):x for x in [json.loads(s) for s in (PREV/'current-target-cells.jsonl').read_text().splitlines() if s]}
assert len(app_rows)==240
for i,x in enumerate(app_rows):
    p,l=x['position'],x['locale']; old=old_cells[(p,l)]; row=app1583[i]
    assert (p,l)==(1583+i//12,LOCS[i%12])
    assert row['sourceKeySha256']==x['sourceKeySha256'] and row['sourceContextSha256']==x['sourceContextSha256']
    assert row['priorCurrentTargetSha256']==x['currentTargetSha256'] and row['priorResolvedTargetSha256']==x['observedAfterTargetSha256']
    assert old['currentTargetSha256']==x['currentTargetSha256']
assert app_summary['productCommit']=='dab83932bb2b375caf3f588ac7b20b3bd835a419'

# Exact PR metadata snapshots are filtered: no body is stored in the packet.
for name in ('PR-attestation.json','PR-attestation-after.json'):
    a=j(name); assert a['state']=='OPEN' and a['draft'] is True and a['head']==HEAD and a['tree']==TREE
    assert a['branchRef']==a['pullRef']==HEAD and a['baseRef']=='main' and a['baseSha']==BASE
a,b=j('PR-attestation.json'),j('PR-attestation-after.json')
for k in ('head','tree','headRef','branchRef','pullRef','baseRef','baseSha','state','draft','deploymentsForHeadCount','deploymentsForHeadSha256','repositoryDeploymentCount','repositoryDeploymentsSha256','actionsRunsForHeadCount'): assert a[k]==b[k],k
print(json.dumps({'result':'PASS','head':HEAD,'tree':TREE,'sourceQueueRows':len(queue),'sourceWindowCells':len(cells),'callerReferences':m['callerReferenceCount'],
 'callerOccurrences':m['callerOccurrenceCount'],'callerlessPositions':m['callerResolutionHoldPositions'],'priorWindowHashRows':len(priorwin),'priorSelectionHashRows':len(selections),
 'priorAppliedTargetHashes':len(applied),'priorHolds':len(priorholds),'tokenMismatchCounts':dict(bad),'checksummedFiles':len(sums),'prRefsStable':True,'candidateFree':True},ensure_ascii=False,indent=2))
