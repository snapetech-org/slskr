#!/usr/bin/env python3
import hashlib,json
from pathlib import Path
W=Path(__file__).resolve().parent
IN=W/'candidate-free-input'; X=W/'cross-audit'
RESTRICTED={'prior-hold-reattestation.jsonl','prior-selection-reattestation.jsonl','source-order-lineage.json'}
def sha(b): return hashlib.sha256(b).hexdigest()
def jl(p): return [json.loads(s) for s in p.read_text(encoding='utf-8').splitlines() if s]
m=json.loads((IN/'manifest.json').read_text(encoding='utf-8'))
sums={}
for line in (IN/'SHA256SUMS.txt').read_text(encoding='utf-8').splitlines():
    digest,name=line.split(None,1); name=name.lstrip('* ')
    assert name not in sums; sums[name]=digest
assert set(m['fileHashes'])==set(sums)-{'manifest.json'}
actual={p.name for p in IN.iterdir() if p.is_file() and p.name!='SHA256SUMS.txt'}
assert actual==set(sums)-RESTRICTED
for name,digest in sums.items():
    if name in RESTRICTED:
        assert not (IN/name).exists()
        info=m['fileHashes'][name]
        assert digest==info['sha256']
    else:
        raw=(IN/name).read_bytes(); assert sha(raw)==digest,name
        if name in m['fileHashes']:
            assert len(raw)==m['fileHashes'][name]['byteCount'] and sha(raw)==m['fileHashes'][name]['sha256']
prior=json.loads((X/'prior-continuity-hash-summary.json').read_text(encoding='utf-8'))
sel=m['fileHashes']['prior-selection-reattestation.jsonl']; hold=m['fileHashes']['prior-hold-reattestation.jsonl']; lineage=m['fileHashes']['source-order-lineage.json']
assert prior['priorSelectionReattestation']['sha256']==sel['sha256'] and prior['priorSelectionReattestation']['byteCount']==sel['byteCount']
assert prior['carriedHoldReattestation']['sha256']==hold['sha256'] and prior['carriedHoldReattestation']['byteCount']==hold['byteCount']
assert prior['sourceOrderLineage']['sha256']==lineage['sha256'] and prior['sourceOrderLineage']['byteCount']==lineage['byteCount']
assert m['candidateFreeInputOnly'] is True and m['proposedTranslationsIncluded'] is False
assert m['head']=='2db7fa06845d9d94a5e5da2ddb5ecfdc04100ade' and m['tree']=='0945d38050243ed0d52aa9d923636820c66e65ba'
cells=jl(IN/'current-target-cells.jsonl'); contexts=jl(IN/'source-contexts.jsonl')
assert len(cells)==240 and len(contexts)==20 and [x['position'] for x in contexts]==list(range(1463,1483))
assert len({(x['position'],x['locale']) for x in cells})==240
for c in cells:
    assert sha(c['sourceKey'].encode())==c['sourceKeySha256'] and sha(c['currentTarget'].encode())==c['currentTargetSha256']
print(json.dumps({'result':'PASS','currentCells':240,'sourceContexts':20,'restrictedFilesOmittedHashOnly':len(RESTRICTED),'priorSelectionCount':m['priorSelectionReattestationCount'],'priorHoldCount':m['carryForwardHoldCount']},indent=2))
