#!/usr/bin/env python3
import hashlib, json, re
from pathlib import Path
from collections import Counter

ROOT = Path('/home/keith/Documents/code/task-scratch/slskr-pr204-w1283-1302-primary-20261103')
INPUT = ROOT / 'input'
OUT = ROOT / 'primary-review'
EXPECTED_MANIFEST_SHA = '6f4f7bc3ed5d3d8097916cf37aa4a2b9ee043141cd1814aa880b673c593de944'
EXPECTED_SUMS_SHA = 'abbb1b89549b82072fcbf5fce3c6ae580cc5bd499b4fe5dadd5df7bd0c567f89'
EXPECTED_HEAD = '55ca2ae0788bfd79daab5cc49f49ebb608593e98'
EXPECTED_TREE = 'd5677673b766d572102bba249af2ab69095dea0d'

def sha(b): return hashlib.sha256(b).hexdigest()
def jsonl(p): return [json.loads(x) for x in p.read_text(encoding='utf-8').splitlines() if x]

# Verify candidate-free input file digests and the two separately reported packet digests.
manifest_bytes = (INPUT/'manifest.json').read_bytes()
sums_bytes = (INPUT/'SHA256SUMS.txt').read_bytes()
assert sha(manifest_bytes) == EXPECTED_MANIFEST_SHA
assert sha(sums_bytes) == EXPECTED_SUMS_SHA
for line in sums_bytes.decode().splitlines():
    digest, name = line.split(None, 1)
    name = name.lstrip('* ')
    assert sha((INPUT/name).read_bytes()) == digest, name
manifest = json.loads(manifest_bytes)
assert manifest['candidateFreeInputOnly'] is True
assert manifest['proposedTranslationsIncluded'] is False
assert manifest['head'] == EXPECTED_HEAD and manifest['tree'] == EXPECTED_TREE

attest = json.loads((INPUT/'PR-attestation.json').read_text(encoding='utf-8'))
assert attest['head'] == EXPECTED_HEAD and attest['tree'] == EXPECTED_TREE
assert attest['branchRef'] == EXPECTED_HEAD and attest['pullRef'] == EXPECTED_HEAD
assert attest['state'] == 'OPEN' and attest['draft'] is True

queue = {r['position']:r for r in jsonl(INPUT/'source-queue.jsonl')}
cells = {(r['position'],r['locale']):r for r in jsonl(INPUT/'current-target-cells.jsonl')}
contexts = {r['position']:r for r in jsonl(INPUT/'source-contexts.jsonl')}
ledger = jsonl(OUT/'ledger.jsonl')
assert len(queue) == manifest['sourceQueueCount'] == 5441
assert len(cells) == 240
assert len(contexts) == 20
assert len(ledger) == 240
assert len({(r['position'],r['locale']) for r in ledger}) == 240
assert {r['position'] for r in ledger} == set(range(1283,1303))
assert {r['locale'] for r in ledger} == set(manifest['localeOrder'])

ph = re.compile(r'\{[A-Za-z][A-Za-z0-9_]*\}')
tags = re.compile(r'<\/?[A-Za-z][^>]*>')
nums = re.compile(r'(?<![A-Za-z])\d+(?:[.,]\d+)?%?(?![A-Za-z])')
counts = Counter()
for row in ledger:
    pos, loc = row['position'], row['locale']
    cell = cells[(pos,loc)]
    q = queue[pos]
    ctx = contexts[pos]
    assert row['sourceKey'] == q['sourceKey'] == cell['sourceKey']
    assert row['sourceKeySha256'] == q['sourceKeySha256'] == cell['sourceKeySha256']
    assert row['currentTarget'] == cell['currentTarget']
    assert row['currentTargetSha256'] == cell['currentTargetSha256']
    assert hashlib.sha256(row['currentTarget'].encode()).hexdigest() == row['currentTargetSha256']
    assert hashlib.sha256(row['proposedTarget'].encode()).hexdigest() == row['proposedTargetSha256']
    assert row['catalogPath'] == cell['catalogPath']
    assert row['catalogFileSha256'] == cell['catalogFileSha256']
    assert row['catalogGitBlob'] == cell['catalogGitBlob']
    assert row['callerCount'] == cell['callerCount'] == len(row['callerRefs'])
    assert row['callerContextSha256'] == ctx['callerContextSha256']
    expected_refs = [
        {'path':x['path'],'line':x['line'],'contextStartLine':x['contextStartLine'],'contextEndLine':x['contextEndLine'],'lineSha256':x['lineSha256'],'contextSha256':x['contextSha256'],'fileSha256':x['fileSha256'],'gitBlob':x['gitBlob']}
        for x in ctx['callers']
    ]
    assert row['callerRefs'] == expected_refs
    source = row['sourceKey']
    target = row['proposedTarget']
    checks = {
        'placeholdersMatch': ph.findall(source) == ph.findall(target),
        'markupTagsMatch': tags.findall(source) == tags.findall(target),
        'numericTokensMatch': nums.findall(source) == nums.findall(target),
        'protectedLiteralsMatch': all(token in target for token in cell['sourceProtectedLiterals']),
    }
    assert row['checks'] == checks and all(checks.values()), (pos,loc,checks)
    assert row['sourceProtectedLiterals'] == cell['sourceProtectedLiterals']
    assert row['proposedProtectedLiterals'] == [token for token in cell['sourceProtectedLiterals'] if token in target]
    assert row['decision'] in {'correction','refinement','accept-current','hold'}
    assert (row['decision']=='accept-current') == (target == row['currentTarget'])
    if row['decision'] == 'hold':
        assert target == row['currentTarget']
    assert row['inputManifestSha256'] == EXPECTED_MANIFEST_SHA
    assert row['inputChecksumListSha256'] == EXPECTED_SUMS_SHA
    counts[row['decision']] += 1

summary = json.loads((OUT/'summary.json').read_text(encoding='utf-8'))
assert summary['head'] == EXPECTED_HEAD and summary['tree'] == EXPECTED_TREE
assert summary['cellCount'] == len(ledger)
assert summary['decisionCounts'] == dict(sorted(counts.items()))
assert summary['changedCellCount'] == sum(r['proposedTarget'] != r['currentTarget'] for r in ledger)
assert summary['heldCellCount'] == counts['hold'] == 0
assert summary['placeholderMismatchCount'] == summary['markupMismatchCount'] == summary['numericTokenMismatchCount'] == summary['protectedLiteralMismatchCount'] == 0
assert summary['primaryReviewOnly'] and not summary['applicationApproved']
provenance = json.loads((OUT/'provenance.json').read_text(encoding='utf-8'))
assert provenance['candidateFreeInput']['manifestSha256'] == EXPECTED_MANIFEST_SHA
assert provenance['candidateFreeInput']['checksumListSha256'] == EXPECTED_SUMS_SHA
assert provenance['liveAttestation']['head'] == EXPECTED_HEAD
assert provenance['liveAttestation']['tree'] == EXPECTED_TREE
print(json.dumps({'result':'PASS','inputManifestSha256':EXPECTED_MANIFEST_SHA,'inputChecksumListSha256':EXPECTED_SUMS_SHA,'cellCount':len(ledger),'decisionCounts':dict(sorted(counts.items())),'holds':counts['hold'],'allStructureAndTokenChecksPassed':True},indent=2))
