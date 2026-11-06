#!/usr/bin/env python3
"""Portable offline verifier for the sealed W1623-W1642 candidate-free packet."""
import collections, hashlib, json, re
from pathlib import Path
R=Path(__file__).resolve().parent
HEAD='7e366cbf21ad5490bd11ef418a0f2a98b3fbd567'; TREE='801d7a037c15dcd83b3e038160054a46c9b8f03b'
LOCS=['es','zh-Hans','hi','de','ja','fr','pt-BR','ar','ko','zh-Hant','vi','id']
sha=lambda x:hashlib.sha256(x.encode() if isinstance(x,str) else x).hexdigest()
canon=lambda x:json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':'))
def j(name): return json.loads((R/name).read_text(encoding='utf-8'))
def jl(name): return [json.loads(s) for s in (R/name).read_text(encoding='utf-8').splitlines() if s]
def check_sums():
    sums={}
    for line in (R/'SHA256SUMS.txt').read_text(encoding='utf-8').splitlines():
        digest,name=line.split(None,1); name=name.lstrip('* ')
        assert name not in sums; sums[name]=digest
    actual={p.name for p in R.iterdir() if p.is_file() and p.name!='SHA256SUMS.txt'}
    assert set(sums)==actual
    for name,digest in sums.items(): assert sha((R/name).read_bytes())==digest,name
    return sums

def token_sets(source,target):
    ph=lambda s:re.findall(r'\{[A-Za-z][A-Za-z0-9_]*\}',s)
    markup=lambda s:re.findall(r'</?[A-Za-z][^>]*>',s)
    nums=lambda s:re.findall(r'(?<![A-Za-z])\d+(?:[.,]\d+)?%?(?![A-Za-z])',s)
    protected=lambda s:list(dict.fromkeys(re.findall(r'(?<![A-Za-z0-9])(?:[A-Z]{2,}[A-Z0-9]*|ffmpeg|Chromaprint|Soulseek|Spotify|YouTube|Pushbullet|Matrix|WebSocket|OpenAI)(?![A-Za-z0-9])',s)))
    return ph(source)==ph(target) and markup(source)==markup(target) and nums(source)==nums(target) and all(x in target for x in protected(source))

m=j('manifest.json'); sums=check_sums()
assert (m['head'],m['tree'],m['selectedPositions'],m['cellCount'],m['candidateFreeInputOnly'],m['proposedTranslationsIncluded'])==(HEAD,TREE,[1623,1642],240,True,False)
assert set(m['fileHashes'])==set(sums)-{'manifest.json'}
for name,pin in m['fileHashes'].items():
    b=(R/name).read_bytes(); assert sha(b)==pin['sha256'] and len(b)==pin['byteCount'],name
queue=jl('source-queue.jsonl'); assert len(queue)==5441 and [x['position'] for x in queue]==list(range(1,5442))
keys=[x['sourceKey'] for x in queue]
assert all(x['sourceKeySha256']==sha(x['sourceKey']) for x in queue)
assert sha('\n'.join(keys)+'\n')==m['sourceLookupKeyOrderSha256']
selected=keys[1622:1642]; assert (R/'selected-source-keys.txt').read_text(encoding='utf-8').splitlines()==selected
assert [x['sourceKey'] for x in queue[1622:1642]]==selected
contexts=jl('source-contexts.jsonl'); assert len(contexts)==20 and [x['position'] for x in contexts]==list(range(1623,1643))
for c in contexts:
    assert c['sourceKey']==keys[c['position']-1] and c['sourceKeySha256']==sha(c['sourceKey'])
    assert c['productionCallerCount']==len(c['callers'])>0
    assert c['callerOccurrenceCount']==sum(x['literalOccurrenceCount'] for x in c['callers'])
    assert c['callerContextSha256']==sha(canon({'sourceKey':c['sourceKey'],'callers':c['callers']}))
    for call in c['callers']:
        assert call['lineSha256']==sha(call['lineText']) and call['contextSha256']==sha(canon(call['context']))
        assert any(x['line']==call['line'] and x['text']==call['lineText'] for x in call['context'])
cmap={x['position']:x for x in contexts}
cells=jl('current-target-cells.jsonl'); assert len(cells)==240
assert [(x['position'],x['locale']) for x in cells]==[(p,l) for p in range(1623,1643) for l in LOCS]
for x in cells:
    src=keys[x['position']-1]; ctx=cmap[x['position']]
    assert x['sourceKey']==src and x['sourceKeySha256']==sha(src)
    assert x['sourceContextSha256']==ctx['callerContextSha256'] and x['callerCount']==ctx['productionCallerCount']
    assert x['currentTargetSha256']==sha(x['currentTarget'])
    assert token_sets(src,x['currentTarget'])
    assert x['placeholderSequenceMatches'] and x['markupMatches'] and x['numericTokensMatch'] and x['protectedLiteralsMatch']
assert m['callerReferenceCount']==20 and m['callerOccurrenceCount']==20 and m['callerResolutionHoldCount']==0
assert m['mismatchCounts']=={'placeholderSequenceMismatchCount':0,'markupMismatchCount':0,'numericTokenMismatchCount':0,'protectedLiteralMismatchCount':0}

lineage_names=['prior-window-selection-hash-only.jsonl','prior-selection-hash-reattestation.jsonl','prior-hold-hash-reattestation.jsonl',
 'prior-window-1503-1522-catalog-diff-hash-only.jsonl','prior-window-1523-1542-application-hash-only.jsonl','prior-window-1543-1562-application-hash-only.jsonl',
 'prior-window-1563-1582-application-hash-only.jsonl','prior-window-1583-1602-application-hash-only.jsonl','prior-window-1603-1622-application-hash-only.jsonl',
 'prior-applied-target-hash-only.jsonl','prior-backfill-hold-hash-only.jsonl']
qhash={i:x['sourceKeySha256'] for i,x in enumerate(queue,1)}
for name in lineage_names:
    for row in jl(name):
        assert row['sourceKeyPositionMatches'] is True and qhash[row['position']]==row['sourceKeySha256']
        assert not any(k in row for k in ('sourceKey','sourceText','currentTarget','proposedTarget','selectedTarget','observedAfterTarget','lineText'))
        expected=row.get('expectedPriorTargetSha256') or row.get('priorTargetSha256') or row.get('selectedTargetSha256') or row.get('observedAfterTargetSha256')
        actual=row.get('liveCatalogTargetSha256') or row.get('liveTargetSha256')
        if expected is not None and actual is not None: assert expected==actual
priorwin=jl(lineage_names[0]); selections=jl(lineage_names[1]); holds=jl(lineage_names[2]); applied=jl(lineage_names[9]); backfill=jl(lineage_names[10])
app_windows=[jl(x) for x in lineage_names[3:9]]
assert len(priorwin)==1920 and len(selections)==380 and len(holds)==62 and len(applied)==82 and len(backfill)==10
assert all(len(x)==240 for x in app_windows)
assert all(x['liveMatchesExpectedPriorTarget'] for x in priorwin+sum(app_windows,[])+applied)
assert all(x['matchesLiveValue'] for x in holds+backfill)
assert sum(x['priorDisposition']=='applied-update' for x in app_windows[-1])==13
assert sum(x['priorDisposition']=='accept-current' for x in app_windows[-1])==227
continuity=j('prior-continuity-hash-summary.json')
assert continuity['previousWindowCells']['recordCount']==1920 and continuity['previousWindowCells']['allMatchExpectedPriorTarget'] is True
assert continuity['priorSelections']['recordCount']==380 and continuity['priorSelections']['allMatchLiveQueue'] is True
assert continuity['priorHolds']['recordCount']==62 and continuity['priorHolds']['unchangedCount']==62
assert continuity['W1603AppliedHashesMatchLiveCatalog'] is True and continuity['rawPriorTranslationsIncluded'] is False
lineage=j('source-order-lineage.json')
assert lineage['window']=='W1623-W1642' and lineage['previousWindow']=='W1603-W1622'
assert lineage['previousBoundaryPosition']==1622 and lineage['nextBoundaryPosition']==1643
assert lineage['gapPositions']==[] and lineage['overlapPositions']==[] and lineage['positionsCoveredThrough']==1642
before,after=j('PR-attestation.json'),j('PR-attestation-after.json')
for a in (before,after):
    assert a['head']==HEAD and a['tree']==TREE and a['branchRef']==HEAD and a['pullRef']==HEAD
    assert a['state']=='OPEN' and a['draft'] is True and a['baseRef']=='main'
for key in ('head','tree','headRef','branchRef','pullRef','baseRef','baseSha','state','draft','deploymentsForHeadCount','deploymentsForHeadSha256','repositoryDeploymentCount','repositoryDeploymentsSha256','actionsRunsForHeadCount'):
    assert before[key]==after[key]
print(json.dumps({'result':'PASS','offline':True,'head':HEAD,'tree':TREE,'sourceCount':20,'cells':len(cells),
 'callerReferences':m['callerReferenceCount'],'callerlessPositions':m['callerResolutionHoldPositions'],
 'priorWindowHashes':len(priorwin),'priorSelections':len(selections),'priorAppliedTargets':len(applied),'priorHolds':len(holds),
 'outputFilesVerified':len(sums),'tokenMismatchCounts':m['mismatchCounts']},ensure_ascii=False,indent=2))
