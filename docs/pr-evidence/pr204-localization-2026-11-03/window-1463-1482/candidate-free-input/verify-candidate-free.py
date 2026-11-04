#!/usr/bin/env python3
import hashlib,json,re
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parent
HEAD='2db7fa06845d9d94a5e5da2ddb5ecfdc04100ade'
TREE='0945d38050243ed0d52aa9d923636820c66e65ba'
LOCALES=('es','zh-Hans','hi','de','ja','fr','pt-BR','ar','ko','zh-Hant','vi','id')
def sha(b): return hashlib.sha256(b).hexdigest()
def sha_text(s): return sha(s.encode('utf-8'))
def canon(x): return json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':'))
def j(name): return json.loads((ROOT/name).read_text(encoding='utf-8'))
def jl(name): return [json.loads(x) for x in (ROOT/name).read_text(encoding='utf-8').splitlines() if x]
def tokens(s):
    ph=re.findall(r'\{[A-Za-z][A-Za-z0-9_]*\}',s)
    tags=re.findall(r'<\/?[A-Za-z][^>]*>',s)
    nums=re.findall(r'(?<![A-Za-z])\d+(?:[.,]\d+)?%?(?![A-Za-z])',s)
    prot=[]
    for mt in re.finditer(r'(?<![A-Za-z0-9])(?:[A-Z]{2,}[A-Z0-9]*|ffmpeg|Chromaprint|Soulseek|Spotify|YouTube|Pushbullet|Matrix|WebSocket|OpenAI)(?![A-Za-z0-9])',s):
        if mt.group(0) not in prot: prot.append(mt.group(0))
    return ph,tags,nums,prot

def main():
    m=j('manifest.json'); att=j('PR-attestation.json'); cp=j('catalog-file-pins.json'); lin=j('source-order-lineage.json'); pin=j('source-pin-reattestation.json')
    assert m['candidateFreeInputOnly'] is True and m['proposedTranslationsIncluded'] is False
    assert m['head']==HEAD and m['tree']==TREE and m['selectedPositions']==[1463,1482]
    assert att['head']==HEAD and att['tree']==TREE and att['branchRef']==HEAD and att['pullRef']==HEAD and att['state']=='OPEN' and att['draft'] is True
    checked={}
    for line in (ROOT/'SHA256SUMS.txt').read_text(encoding='utf-8').splitlines():
        d,n=line.split(None,1); n=n.lstrip('* '); checked[n]=d
    assert checked and len(checked)==len(set(checked))
    assert set(checked)=={p.name for p in ROOT.iterdir() if p.is_file() and p.name!='SHA256SUMS.txt'}
    for name,digest in checked.items(): assert sha((ROOT/name).read_bytes())==digest,name
    for name,info in m['fileHashes'].items():
        raw=(ROOT/name).read_bytes(); assert len(raw)==info['byteCount'] and sha(raw)==info['sha256'],name
    q=jl('source-queue.jsonl'); contexts=jl('source-contexts.jsonl'); cells=jl('current-target-cells.jsonl')
    holds=jl('prior-hold-reattestation.jsonl'); selections=jl('prior-selection-reattestation.jsonl')
    callerless=jl('caller-resolution-holds.jsonl'); bounds=jl('source-window-boundaries.jsonl'); structures=jl('catalog-structure.jsonl')
    assert len(q)==5441 and [r['position'] for r in q]==list(range(1,5442))
    assert len({r['sourceKey'] for r in q})==5441
    order_sha=sha_text('\n'.join(r['sourceKey'] for r in q)+'\n')
    assert order_sha==m['sourceLookupKeyOrderSha256']==cp['sourceLookupKeyOrderSha256']
    assert sha((ROOT/'source-queue.jsonl').read_bytes())==m['sourceQueueFileSha256']==cp['sourceQueueFileSha256']
    assert cp['head']==HEAD and cp['tree']==TREE and cp['sourceLookupKeySetCount']==5441
    assert len(cp['localeCatalogs'])==12 and set(cp['localeCatalogs'])==set(LOCALES)
    assert len(structures)==12
    for s in structures:
        p=cp['localeCatalogs'][s['locale']]
        assert s['path']==p['path'] and s['sha256']==p['sha256'] and s['gitBlob']==p['gitBlob']
        assert s['keyCount']==5441 and s['orderedKeySha256']==p['orderedKeySha256']
    assert len({x['orderedKeySha256'] for x in structures})==1
    assert len(contexts)==20 and [x['position'] for x in contexts]==list(range(1463,1483))
    assert len(cells)==240 and len({(x['position'],x['locale']) for x in cells})==240
    assert [x['position'] for x in bounds]==list(range(1462,1484))
    qmap={x['position']:x for x in q}; ctxmap={x['position']:x for x in contexts}
    for idx,x in enumerate(contexts):
        qrow=qmap[x['position']]
        assert x['sourceKey']==qrow['sourceKey'] and x['sourceKeySha256']==qrow['sourceKeySha256']
        assert x['productionCallerCount']==len(x['callers'])
        assert x['callerContextSha256']==sha_text(canon({'sourceKey':x['sourceKey'],'callers':x['callers']}))
        for c in x['callers']:
            assert c['contextSha256']==sha_text(canon(c['context']))
            assert c['lineSha256']==sha_text(c['lineText'])
    mism=Counter()
    for c in cells:
        ctx=ctxmap[c['position']]; qrow=qmap[c['position']]; pinloc=cp['localeCatalogs'][c['locale']]
        assert c['sourceKey']==ctx['sourceKey']==qrow['sourceKey']
        assert c['sourceKeySha256']==qrow['sourceKeySha256']==sha_text(c['sourceKey'])
        assert c['callerCount']==ctx['productionCallerCount'] and c['sourceContextSha256']==ctx['callerContextSha256']
        assert c['callerRefs']==[{'fileSha256':x['fileSha256'],'gitBlob':x['gitBlob'],'line':x['line'],'lineSha256':x['lineSha256'],'path':x['path']} for x in ctx['callers']]
        assert c['catalogPath']==pinloc['path'] and c['catalogFileSha256']==pinloc['sha256'] and c['catalogGitBlob']==pinloc['gitBlob']
        assert c['currentTargetSha256']==sha_text(c['currentTarget'])
        sph,stags,snums,sprot=tokens(c['sourceKey']); tph,ttags,tnums,tprot=tokens(c['currentTarget'])
        bad=[t for t in sprot if t not in tprot]
        assert c['sourcePlaceholders']==sph and c['currentTargetPlaceholders']==tph and c['placeholderSequenceMatches']==(sph==tph)
        assert c['sourceMarkupTags']==stags and c['currentTargetMarkupTags']==ttags and c['markupMatches']==(stags==ttags)
        assert c['sourceNumericTokens']==snums and c['currentTargetNumericTokens']==tnums and c['numericTokensMatch']==(snums==tnums)
        assert c['sourceProtectedLiterals']==sprot and c['currentTargetProtectedLiterals']==tprot and c['protectedLiteralMismatchTokens']==bad and c['protectedLiteralsMatch']==(not bad)
        mism['placeholderSequenceMismatchCount']+=sph!=tph; mism['markupMismatchCount']+=stags!=ttags
        mism['numericTokenMismatchCount']+=snums!=tnums; mism['protectedLiteralMismatchCount']+=bool(bad)
    assert dict(mism)==m['mismatchCounts']
    assert {x['position'] for x in callerless}=={x['position'] for x in contexts if x['productionCallerCount']==0}
    assert len(selections)==220 and len({x['position'] for x in selections})==220
    assert all(x['selectionMatchesCurrentQueue'] and x['currentQueueSourceKey']==qmap[x['position']]['sourceKey'] and x['currentQueueSourceKeySha256']==qmap[x['position']]['sourceKeySha256'] for x in selections)
    assert not {x['position'] for x in selections}&set(range(1463,1483))
    assert len(holds)==35 and len({(x['position'],x['locale']) for x in holds})==35
    assert all(x['disposition']=='hold' and x['matchesPriorCurrentValue'] and x['currentTargetSha256']==x['priorCurrentTargetSha256']==sha_text(x['currentTarget']) for x in holds)
    assert m['priorSelectionReattestationCount']==220 and m['priorSelectionWindowCount']==11
    assert m['carryForwardHoldCount']==35 and m['carryForwardHoldUnchangedCount']==35 and m['carryForwardHoldChangedCount']==0
    assert m['callerResolutionHoldCount']==len(callerless) and m['cellCount']==240
    assert lin['priorSelectedSourceCount']==220 and lin['priorSelectionsAllMatchCurrentQueue'] is True
    runtime=j('localization-runtime-context.json')
    assert runtime['path']==pin['runtimePath'] and runtime['pin']['sha256']==pin['runtimeFileSha256'] and runtime['pin']['gitBlob']==pin['runtimeGitBlob']
    print(json.dumps({'result':'PASS','head':HEAD,'tree':TREE,'positions':[1463,1482],'cells':len(cells),
        'catalogs':len(structures),'sourceQueueRows':len(q),'sourceOrderSha256':order_sha,
        'selectedCallerReferences':sum(x['productionCallerCount'] for x in contexts),
        'callerlessPositions':[x['position'] for x in callerless],'priorSelectionsReattested':len(selections),
        'priorHoldsReattested':len(holds),'changedPriorHolds':sum(not x['matchesPriorCurrentValue'] for x in holds),
        'mismatchCounts':dict(mism),'checksumFiles':len(checked)},ensure_ascii=False,indent=2))
if __name__=='__main__': main()
