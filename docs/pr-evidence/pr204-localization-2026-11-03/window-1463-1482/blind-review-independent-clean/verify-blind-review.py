#!/usr/bin/env python3
import hashlib,json,re
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parent; INPUT=ROOT.parent/'candidate-free-input'
RESTRICTED={'prior-hold-reattestation.jsonl','prior-selection-reattestation.jsonl','source-order-lineage.json'}
def sha(b): return hashlib.sha256(b).hexdigest()
def toks(s):
    ph=re.findall(r'\{[A-Za-z][A-Za-z0-9_]*\}',s); tags=re.findall(r'<\/?[A-Za-z][^>]*>',s); nums=re.findall(r'(?<![A-Za-z])\d+(?:[.,]\d+)?%?(?![A-Za-z])',s); prot=[]
    for mt in re.finditer(r'(?<![A-Za-z0-9])(?:[A-Z]{2,}[A-Z0-9]*|ffmpeg|Chromaprint|Soulseek|Spotify|YouTube|Pushbullet|Matrix|WebSocket|OpenAI)(?![A-Za-z0-9])',s):
        if mt.group(0) not in prot: prot.append(mt.group(0))
    return ph,tags,nums,prot
def jl(p): return [json.loads(s) for s in p.read_text(encoding='utf-8').splitlines() if s]
# Verify this packet's own checksums.
sums={}
for line in (ROOT/'SHA256SUMS.txt').read_text(encoding='utf-8').splitlines():
    digest,name=line.split(None,1); name=name.lstrip('* '); assert name not in sums; sums[name]=digest
actual={p.name for p in ROOT.iterdir() if p.is_file() and p.name!='SHA256SUMS.txt'}
assert actual==set(sums)
for name,digest in sums.items(): assert sha((ROOT/name).read_bytes())==digest,name
# Verify candidate-free inputs; withheld continuity files are hash-only and are never opened.
manifest=json.loads((INPUT/'manifest.json').read_text(encoding='utf-8'))
for line in (INPUT/'SHA256SUMS.txt').read_text(encoding='utf-8').splitlines():
    digest,name=line.split(None,1); name=name.lstrip('* ')
    if name in RESTRICTED:
        assert not (INPUT/name).exists() and digest==manifest['fileHashes'][name]['sha256']
    else: assert sha((INPUT/name).read_bytes())==digest,name
contexts={x['position']:x for x in jl(INPUT/'source-contexts.jsonl')}
cells={(x['position'],x['locale']):x for x in jl(INPUT/'current-target-cells.jsonl')}
ledger=jl(ROOT/'review-ledger.jsonl'); assert len(cells)==len(ledger)==240
counts=Counter(); mismatch=Counter()
for item in ledger:
    key=(item['position'],item['locale']); src=cells[key]; ctx=contexts[key[0]]
    assert item['sourceKey']==src['sourceKey'] and item['sourceKeySha256']==src['sourceKeySha256']
    assert item['currentTarget']==src['currentTarget'] and item['currentTargetSha256']==src['currentTargetSha256']
    assert sha(item['sourceKey'].encode())==item['sourceKeySha256'] and sha(item['currentTarget'].encode())==item['currentTargetSha256']
    assert item['callerContextSha256']==ctx['callerContextSha256'] and item['callerCount']==ctx['productionCallerCount']
    ph,tags,nums,prot=toks(item['sourceKey']); tph,ttags,tnums,tprot=toks(item['currentTarget']); missing=[t for t in prot if t not in tprot]
    t=item['tokenChecks']
    assert t['placeholderSequenceMatches']==(ph==tph) and t['sourcePlaceholders']==ph and t['currentTargetPlaceholders']==tph
    assert t['markupMatches']==(tags==ttags) and t['sourceMarkupTags']==tags and t['currentTargetMarkupTags']==ttags
    assert t['numericTokensMatch']==(nums==tnums) and t['sourceNumericTokens']==nums and t['currentTargetNumericTokens']==tnums
    assert t['protectedLiteralsMatch']==(not missing) and t['sourceProtectedLiterals']==prot and t['currentTargetProtectedLiterals']==tprot and t['missingProtectedLiterals']==missing
    assert item['decision'] in {'accept-current','correction','refinement','hold'}
    if item['decision'] in {'correction','refinement'}: assert item['suggestedTarget']
    if item['decision']=='hold': assert item['suggestedTarget'] is None
    counts[item['decision']]+=1
    mismatch['placeholder']+=ph!=tph; mismatch['markup']+=tags!=ttags; mismatch['numeric']+=nums!=tnums; mismatch['protected']+=bool(missing)
assert counts==Counter({'accept-current':177,'correction':29,'refinement':22,'hold':12})
assert mismatch==Counter({'protected':28,'placeholder':0,'markup':0,'numeric':0})
assert all(x['decision']=='hold' for x in ledger if x['position']==1466)
print(json.dumps({'result':'PASS','cells':240,'decisionCounts':dict(sorted(counts.items())),'tokenMismatchCounts':dict(mismatch),'restrictedContinuity':'hash-only'},indent=2))
