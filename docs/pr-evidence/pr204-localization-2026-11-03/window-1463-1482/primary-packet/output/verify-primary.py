#!/usr/bin/env python3
import hashlib,json,re
from collections import Counter
from pathlib import Path
OUT=Path(__file__).resolve().parent
IN=(OUT/'../../candidate-free-input').resolve()
EXPECTED_HEAD='2db7fa06845d9d94a5e5da2ddb5ecfdc04100ade'
EXPECTED_TREE='0945d38050243ed0d52aa9d923636820c66e65ba'
LOCALES=('es','zh-Hans','hi','de','ja','fr','pt-BR','ar','ko','zh-Hant','vi','id')
def sha(b): return hashlib.sha256(b).hexdigest()
def sha_text(s): return sha(s.encode('utf-8'))
def j(path): return json.loads(path.read_text(encoding='utf-8'))
def jl(path): return [json.loads(x) for x in path.read_text(encoding='utf-8').splitlines() if x]
def tokens(s):
    ph=re.findall(r'\{[A-Za-z][A-Za-z0-9_]*\}',s); tags=re.findall(r'<\/?[A-Za-z][^>]*>',s); nums=re.findall(r'(?<![A-Za-z])\d+(?:[.,]\d+)?%?(?![A-Za-z])',s); prot=[]
    for mt in re.finditer(r'(?<![A-Za-z0-9])(?:[A-Z]{2,}[A-Z0-9]*|ffmpeg|Chromaprint|Soulseek|Spotify|YouTube|Pushbullet|Matrix|WebSocket|OpenAI)(?![A-Za-z0-9])',s):
        if mt.group(0) not in prot: prot.append(mt.group(0))
    return {'placeholders':ph,'markupTags':tags,'numericTokens':nums,'protectedLiterals':prot}
manifest=j(OUT/'manifest.json')
assert manifest['head']==EXPECTED_HEAD and manifest['tree']==EXPECTED_TREE
assert manifest['selectedPositions']==[1463,1482] and manifest['cellCount']==240 and manifest['proposalCount']==44
assert manifest['candidateFreeInputManifestSha256']==sha((IN/'manifest.json').read_bytes())
for name,info in manifest['files'].items():
    raw=(OUT/name).read_bytes(); assert len(raw)==info['byteCount'] and sha(raw)==info['sha256'],name
sums={}
for line in (OUT/'SHA256SUMS.txt').read_text(encoding='utf-8').splitlines():
    digest,name=line.split(None,1); sums[name.lstrip('* ')]=digest
assert set(sums)=={x.name for x in OUT.iterdir() if x.is_file() and x.name!='SHA256SUMS.txt'}
for name,digest in sums.items(): assert sha((OUT/name).read_bytes())==digest,name
inputm=j(IN/'manifest.json'); assert inputm['head']==EXPECTED_HEAD and inputm['tree']==EXPECTED_TREE
cells=jl(IN/'current-target-cells.jsonl'); ctx=jl(IN/'source-contexts.jsonl'); contexts={x['position']:x for x in ctx}
rows=jl(OUT/'primary-ledger.jsonl'); assert len(rows)==240
assert [(r['position'],r['locale']) for r in rows]==[(c['position'],c['locale']) for c in cells]
counts=Counter(r['disposition'] for r in rows); assert counts==Counter({'accept-current':184,'correct':29,'refine':15,'hold':12}),counts
inputmap={(c['position'],c['locale']):c for c in cells}; proposal_count=0; proposed_bad=Counter(); current_bad=Counter()
for r in rows:
    key=(r['position'],r['locale']); c=inputmap[key]; x=contexts[r['position']]
    assert r['head']==EXPECTED_HEAD and r['tree']==EXPECTED_TREE
    assert r['sourceId']==c['sourceKey'] and r['sourceIdSha256']==c['sourceKeySha256']
    assert r['currentTarget']==c['currentTarget'] and r['currentTargetSha256']==c['currentTargetSha256']==sha_text(r['currentTarget'])
    assert r['catalogPath']==c['catalogPath'] and r['catalogFileSha256']==c['catalogFileSha256'] and r['catalogGitBlob']==c['catalogGitBlob']
    assert r['callerContextSha256']==x['callerContextSha256'] and r['callers']==x['callers']
    assert r['callerCount']==x['productionCallerCount'] and r['callerOccurrenceCount']==x['callerOccurrenceCount']
    assert r['proposedTarget'] is None if r['disposition'] in ('accept-current','hold') else r['proposedTarget'] is not None and r['proposedTarget']!=r['currentTarget']
    st=tokens(r['sourceId']); ct=tokens(r['currentTarget'])
    for keyname,actual in [('placeholders',st['placeholders']==ct['placeholders']),('markupTags',st['markupTags']==ct['markupTags']),('numericTokens',st['numericTokens']==ct['numericTokens']),('protectedLiterals',all(t in ct['protectedLiterals'] for t in st['protectedLiterals']))]:
        assert r['currentTokenChecks'][keyname]['matches']==actual
        if not actual: current_bad[keyname]+=1
    if r['disposition']=='accept-current': assert all(r['currentTokenChecks'][k]['matches'] for k in ('placeholders','markupTags','numericTokens','protectedLiterals'))
    if r['proposedTarget'] is not None:
        proposal_count+=1; pt=tokens(r['proposedTarget']); assert r['proposedTargetSha256']==sha_text(r['proposedTarget'])
        for keyname in ('placeholders','markupTags','numericTokens','protectedLiterals'):
            ok=st[keyname]==pt[keyname]
            assert r['proposedTokenChecks'][keyname]['matches']==ok and ok,(key,keyname)
    else:
        assert r['proposedTargetSha256'] is None and r['proposedTokenChecks'] is None
assert proposal_count==44
assert current_bad['protectedLiterals']==28 and current_bad['placeholders']==0 and current_bad['markupTags']==0 and current_bad['numericTokens']==0
assert all(r['disposition']=='hold' and r['proposedTarget'] is None for r in rows if r['position']==1466)
assert all(r['disposition']!='hold' for r in rows if r['position']!=1466)
assert all(r['disposition']=='accept-current' for r in rows if r['position']==1465)
print(json.dumps({'result':'PASS','head':EXPECTED_HEAD,'tree':EXPECTED_TREE,'cells':len(rows),'dispositions':dict(counts),'proposals':proposal_count,'currentProtectedMismatches':28,'proposedTokenMismatches':0,'callerlessHoldPosition':1466,'checksumFiles':len(sums)},ensure_ascii=False,indent=2))
