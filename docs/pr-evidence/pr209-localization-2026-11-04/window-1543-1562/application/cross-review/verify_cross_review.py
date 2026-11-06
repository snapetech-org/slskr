#!/usr/bin/env python3
"""Verify the sealed cross-review packet and its pinned source evidence."""
import collections
import hashlib
import json
import re
import subprocess
from pathlib import Path

OUT = Path(__file__).resolve().parent
ROOT = Path('/home/keith/Documents/code/task-scratch')
INPUT = ROOT / 'slskr-pr209-w1543-1562-primary-20261104' / 'candidate-free-input'
PRIMARY = ROOT / 'slskr-pr209-w1543-1562-primary-20261104' / 'primary-review'
BLIND = ROOT / 'slskr-pr209-w1543-1562-independent-blind-review-20261104'
SOURCE = Path('/mnt/disks/scratch/task-worktrees/localization-20261104/slskr-pr209-w1543-1562-source')
HEAD = 'c15eddffec2c4c24cc091b2a6ebf0c43fa58ef1b'
TREE = '4259db991f25fbbd0200963769e62bb7e2150806'
LOCALES = ['es', 'zh-Hans', 'hi', 'de', 'ja', 'fr', 'pt-BR', 'ar', 'ko', 'zh-Hant', 'vi', 'id']


def sha(value):
    if isinstance(value, str):
        value = value.encode('utf-8')
    return hashlib.sha256(value).hexdigest()


def canon(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'))


def j(path):
    return json.loads(path.read_text(encoding='utf-8'))


def jl(path):
    return [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines() if line]


def git(*args):
    return subprocess.check_output(['git', '-C', str(SOURCE), *args], text=True).strip()


def tokens(text):
    placeholders = re.findall(r'\{[A-Za-z][A-Za-z0-9_]*\}', text)
    markup = re.findall(r'</?[A-Za-z][^>]*>', text)
    numbers = re.findall(r'(?<![A-Za-z])\d+(?:[.,]\d+)?%?(?![A-Za-z])', text)
    protected = []
    pattern = r'(?<![A-Za-z0-9])(?:[A-Z]{2,}[A-Z0-9]*|ffmpeg|Chromaprint|Soulseek|Spotify|YouTube|Pushbullet|Matrix|WebSocket|OpenAI)(?![A-Za-z0-9])'
    for value in re.findall(pattern, text):
        if value not in protected:
            protected.append(value)
    return {'placeholders': placeholders, 'markup': markup, 'numbers': numbers, 'protectedLiterals': protected}


manifest = j(OUT / 'manifest.json')
assert manifest['artifact'] == 'slskR PR #209 W1543-W1562 cross-review'
assert manifest['exactPin']['head'] == HEAD and manifest['exactPin']['tree'] == TREE
assert manifest['review']['cellCount'] == 240
assert manifest['review']['crossDispositionCounts'] == {'accept-current': 208, 'propose-correction': 27, 'hold': 5}
assert manifest['review']['primaryProposals'] == manifest['review']['primaryProposalsEndorsed'] == 21
assert manifest['review']['primaryProposalsWordingAdjusted'] == 4
assert manifest['review']['blindFindingCells'] == 22
assert manifest['review']['blindFindingCellsActioned'] == 18
assert manifest['review']['blindFindingCellsHeld'] == 4
assert manifest['liveRefChecks']['matchedExactPin'] is True
assert manifest['liveRefChecks']['prBodyOrDescriptionRequested'] is False
assert manifest['reviewerExposure']['prDescriptionOrBodyOpened'] is False
assert manifest['actions']['catalogsEdited'] is False and manifest['actions']['prOrBodyChanged'] is False

# Verify the input packet seals, including the candidate-free, primary, and blind files.
for packet in [INPUT, PRIMARY, BLIND]:
    sums = {}
    for line in (packet / 'SHA256SUMS.txt').read_text(encoding='utf-8').splitlines():
        digest, name = line.split(None, 1)
        name = name.lstrip('* ')
        assert name not in sums
        sums[name] = digest
    assert set(sums) == {p.name for p in packet.iterdir() if p.is_file() and p.name != 'SHA256SUMS.txt'}
    for name, digest in sums.items():
        assert sha((packet / name).read_bytes()) == digest, (packet.name, name)
assert sha((INPUT / 'SHA256SUMS.txt').read_bytes()) == manifest['inputs']['candidateFreeChecksumListSha256']
assert sha((PRIMARY / 'SHA256SUMS.txt').read_bytes()) == manifest['inputs']['primaryChecksumListSha256']
assert sha((BLIND / 'SHA256SUMS.txt').read_bytes()) == manifest['inputs']['blindChecksumListSha256']

# Verify the local exact-head source checkout and every saved caller hash against its file.
assert git('rev-parse', 'HEAD') == HEAD and git('rev-parse', 'HEAD^{tree}') == TREE
assert git('status', '--porcelain') == ''
contexts = jl(INPUT / 'source-contexts.jsonl')
contexts_by_pos = {x['position']: x for x in contexts}
blob_cache = {}
caller_count = 0
caller_files = set()
for item in contexts:
    assert item['callerContextSha256'] == sha(canon({'sourceKey': item['sourceKey'], 'callers': item['callers']}))
    for caller in item['callers']:
        assert caller['lineSha256'] == sha(caller['lineText'])
        assert caller['contextSha256'] == sha(canon(caller['context']))
        path = caller['path']
        full = SOURCE / path
        raw = full.read_bytes()
        assert sha(raw) == caller['fileSha256'], path
        if path not in blob_cache:
            blob_cache[path] = git('rev-parse', f'HEAD:{path}')
        assert blob_cache[path] == caller['gitBlob'], path
        lines = raw.decode('utf-8').splitlines()
        assert lines[caller['line'] - 1] == caller['lineText']
        lo, hi = caller['contextStartLine'], caller['contextEndLine']
        context = [{'line': n, 'text': lines[n - 1]} for n in range(lo, hi + 1)]
        assert context == caller['context']
        assert item['sourceKey'] in caller['lineText']
        caller_count += 1
        caller_files.add(path)
assert caller_count == manifest['sourceWorktree']['verifiedCallerReferences'] == 21
assert len(caller_files) == manifest['sourceWorktree']['verifiedCallerFiles'] == 10

# Verify catalog evidence is pinned to the exact tree.
pins = j(INPUT / 'catalog-file-pins.json')
catalogs = {}
for locale, pin in pins['localeCatalogs'].items():
    raw = (SOURCE / pin['path']).read_bytes()
    assert sha(raw) == pin['sha256']
    assert git('rev-parse', f"HEAD:{pin['path']}") == pin['gitBlob']
    catalogs[locale] = json.loads(raw.decode('utf-8'))

input_cells = jl(INPUT / 'current-target-cells.jsonl')
primary_rows = jl(PRIMARY / 'primary-ledger.jsonl')
primary_proposals = jl(PRIMARY / 'proposals.jsonl')
blind_rows = jl(BLIND / 'review-cells.jsonl')
blind_findings = j(BLIND / 'findings.json')
primary_by_key = {(x['position'], x['locale']): x for x in primary_rows}
proposal_by_key = {(x['position'], x['locale']): x for x in primary_proposals}
blind_by_key = {(x['position'], x['locale']): x for x in blind_rows}
blind_finding_ids = {}
for finding in blind_findings:
    for cell in finding['cells']:
        key = (cell['position'], cell['locale'])
        assert key not in blind_finding_ids
        blind_finding_ids[key] = finding['id']

ledger = jl(OUT / 'cross-review-ledger.jsonl')
assert len(ledger) == 240
assert [(x['position'], x['locale']) for x in ledger] == [(p, l) for p in range(1543, 1563) for l in LOCALES]
counts = collections.Counter(x['crossDisposition'] for x in ledger)
assert dict(counts) == manifest['review']['crossDispositionCounts']
for row, cell in zip(ledger, input_cells):
    key = (cell['position'], cell['locale'])
    primary = primary_by_key[key]
    blind = blind_by_key[key]
    context = contexts_by_pos[cell['position']]
    assert row['sourceKey'] == cell['sourceKey'] and row['sourceKeySha256'] == cell['sourceKeySha256']
    assert row['currentTarget'] == cell['currentTarget'] and row['currentTargetSha256'] == cell['currentTargetSha256']
    assert row['currentTargetSha256'] == sha(row['currentTarget'])
    assert row['sourceContextSha256'] == cell['sourceContextSha256'] == context['callerContextSha256']
    assert row['callerHashesVerifiedAgainstPinnedWorktree'] is True
    assert row['callerCount'] == cell['callerCount'] == len(row['callerReferences']) > 0
    assert row['primaryDisposition'] == primary['disposition']
    assert row['primarySelectedTarget'] == (proposal_by_key[key]['selectedTarget'] if key in proposal_by_key else None)
    assert row['blindFindingIds'] == blind['findingIds']
    assert row['blindFindingIds'] == ([blind_finding_ids[key]] if key in blind_finding_ids else [])
    source_tokens = tokens(row['sourceKey'])
    assert row['sourceTokens'] == source_tokens
    assert row['currentTokens'] == tokens(row['currentTarget'])
    if row['crossDisposition'] == 'hold':
        assert row['selectedTarget'] is None and row['selectedTargetSha256'] is None and row['selectedTokens'] is None
        assert row['tokenIntegrity'] is None
    else:
        selected = row['selectedTarget']
        assert isinstance(selected, str)
        assert row['selectedTargetSha256'] == sha(selected)
        selected_tokens = tokens(selected)
        assert row['selectedTokens'] == selected_tokens
        assert source_tokens['placeholders'] == selected_tokens['placeholders']
        assert source_tokens['markup'] == selected_tokens['markup']
        assert source_tokens['numbers'] == selected_tokens['numbers']
        assert all(x in selected_tokens['protectedLiterals'] for x in source_tokens['protectedLiterals'])
        assert all(row['tokenIntegrity'].values())
    assert row['primaryProposalOutcome'] == ('adjusted' if key in proposal_by_key and row['selectedTarget'] != proposal_by_key[key]['selectedTarget'] else 'endorsed') if key in proposal_by_key else row['primaryProposalOutcome'] == 'none'
    for evidence in row['catalogEvidence']:
        assert catalogs[row['locale']][evidence['key']] == evidence['translation']
        assert sha((SOURCE / evidence['path']).read_bytes()) == evidence['fileSha256']

# Verify cross-finding coverage, primary/blind reconciliation, and exact captured refs.
assert manifest['review']['crossReviewFindings'][0]['id'] == 'XR01'
assert {(x['position'], x['locale']) for x in ledger if 'XR01' in x['crossFindingIds']} == {(1548, 'ko'), (1549, 'ko')}
primary_keys = set(proposal_by_key)
blind_keys = set(blind_finding_ids)
assert (len(primary_keys & blind_keys), len(primary_keys - blind_keys), len(blind_keys - primary_keys), 240 - len(primary_keys | blind_keys)) == (12, 9, 10, 209)
primary_outcomes = collections.Counter(x['primaryProposalOutcome'] for x in ledger if x['primaryDisposition'] in ('propose-correction', 'propose-refinement'))
assert primary_outcomes == {'endorsed': 17, 'adjusted': 4}
blind_outcomes = collections.Counter(x['crossDisposition'] for x in ledger if x['blindFindingIds'])
assert blind_outcomes == {'propose-correction': 18, 'hold': 4}
metadata = j(OUT / 'live-pr-metadata.json')
assert metadata == manifest['liveRefChecks']['filteredPullRequestMetadata']
assert metadata['headRefOid'] == HEAD and metadata['baseRefOid'] == manifest['exactPin']['baseSha']
assert (OUT / 'live-branch-ref.txt').read_text().strip() == (OUT / 'live-pull-ref.txt').read_text().strip() == HEAD
assert (OUT / 'live-local-tree.txt').read_text().strip() == TREE

# Verify the sealed output file manifest and checksum list.
for name, pin in manifest['fileHashes'].items():
    raw = (OUT / name).read_bytes()
    assert len(raw) == pin['byteCount'] and sha(raw) == pin['sha256'], name
sum_rows = {}
for line in (OUT / 'SHA256SUMS.txt').read_text(encoding='utf-8').splitlines():
    digest, name = line.split(None, 1)
    assert name not in sum_rows
    sum_rows[name] = digest
assert set(sum_rows) == {p.name for p in OUT.iterdir() if p.is_file() and p.name != 'SHA256SUMS.txt'}
for name, digest in sum_rows.items():
    assert sha((OUT / name).read_bytes()) == digest, name

print(json.dumps({
    'result': 'PASS',
    'head': HEAD,
    'tree': TREE,
    'cells': len(ledger),
    'counts': dict(counts),
    'primaryProposals': dict(primary_outcomes),
    'blindFindingCells': dict(blind_outcomes),
    'primaryBlindOverlap': 12,
    'primaryOnly': 9,
    'blindOnly': 10,
    'callerReferencesVerified': caller_count,
    'callerFilesVerified': len(caller_files),
    'catalogFilesVerified': len(catalogs),
    'checksummedOutputFiles': len(sum_rows),
    'prBodyRequested': False,
}, ensure_ascii=False, indent=2))
