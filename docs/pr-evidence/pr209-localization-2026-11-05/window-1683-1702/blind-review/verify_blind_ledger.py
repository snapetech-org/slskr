#!/usr/bin/env python3
"""Verify the blind ledger and its candidate-free source pins."""
import argparse, hashlib, json, re, sys
from pathlib import Path

EXPECTED_HEAD = 'f04b7f965aef79552d65d40a2eeb550e5e3b9cfa'
EXPECTED_TREE = '85fe880023e55e055660fd17599c291edd24a1c6'
EXPECTED_PROPOSALS = {
    (1683, 'ko'): '검색 기록에서 백필을 시작하지 못했습니다.',
    (1684, 'ko'): '포드 게시를 취소하지 못했습니다:',
    (1685, 'zh-Hant'): '無法取消註冊 Pod。',
    (1686, 'ko'): '포드 등록을 취소하지 못했습니다:',
    (1692, 'de'): 'Die Affinitäten der Mitglieder konnten nicht aktualisiert werden: {error}',
}
PLACEHOLDER_RE = re.compile(r'\{[a-zA-Z][a-zA-Z0-9_]*\}')

def digest(data): return hashlib.sha256(data).hexdigest()
def file_digest(path): return digest(path.read_bytes())
def load_json(path): return json.loads(path.read_text(encoding='utf-8'))
def load_jsonl(path): return [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines() if line]
def assert_ok(condition, message):
    if not condition: raise SystemExit('FAIL: ' + message)

def verify_sumfile(directory):
    rows = {}
    for line in (directory / 'SHA256SUMS.txt').read_text(encoding='utf-8').splitlines():
        if not line.strip(): continue
        digest_text, name = line.split(None, 1)
        name = name.strip().lstrip('*')
        assert_ok('/' not in name and name not in ('.', '..'), f'unsafe checksum path {name}')
        rows[name] = digest_text
    for name, expected in rows.items():
        path = directory / name
        assert_ok(path.is_file() and file_digest(path) == expected, f'checksum mismatch for {name}')
    return rows

parser = argparse.ArgumentParser()
parser.add_argument('--input-dir', required=True, type=Path)
parser.add_argument('--output-dir', required=True, type=Path)
args = parser.parse_args()
in_dir, out_dir = args.input_dir, args.output_dir
in_checks = verify_sumfile(in_dir)
out_checks = verify_sumfile(out_dir)
assert_ok('SHA256SUMS.txt' not in out_checks, 'checksum list must not include itself')
actual_output_names = {p.name for p in out_dir.iterdir() if p.is_file() and p.name != 'SHA256SUMS.txt'}
assert_ok(actual_output_names == set(out_checks), 'output checksum list does not cover exactly the retained files')

manifest = load_json(in_dir / 'manifest.json')
before, after = load_json(in_dir / 'attestation-before.json'), load_json(in_dir / 'attestation-after.json')
assert_ok((manifest.get('head'), manifest.get('tree')) == (EXPECTED_HEAD, EXPECTED_TREE), 'manifest pin mismatch')
assert_ok(all((x.get('headSha'), x.get('headTree')) == (EXPECTED_HEAD, EXPECTED_TREE) for x in (before, after)), 'attestation pin mismatch')
assert_ok((before.get('headSha'), before.get('headTree')) == (after.get('headSha'), after.get('headTree')), 'before/after pin drift')
source_rows = load_jsonl(in_dir / 'source-queue.jsonl')
context_rows = load_jsonl(in_dir / 'source-contexts.jsonl')
target_rows = load_jsonl(in_dir / 'current-target-cells.jsonl')
ledger = load_jsonl(out_dir / 'ledger.jsonl')
summary = load_json(out_dir / 'review-summary.json')
assert_ok(len(source_rows) == 5441 and [r['position'] for r in source_rows] == list(range(1, 5442)), 'source queue discontinuity')
assert_ok(file_digest(in_dir / 'source-queue.jsonl') == manifest['sourceQueueFileSha256'], 'source queue SHA mismatch')
assert_ok(len(context_rows) == 20 and len(target_rows) == 240 and len(ledger) == 240, 'expected 20 sources and 240 cells')
assert_ok((in_dir / 'caller-resolution-holds.jsonl').read_bytes() == b'', 'input unexpectedly has caller holds')
assert_ok((out_dir / 'holds.jsonl').read_bytes() == b'', 'output holds file is not empty')
source_by_pos = {r['position']: r for r in source_rows}
context_by_pos = {r['position']: r for r in context_rows}
target_by_cell = {(r['position'], r['locale']): r for r in target_rows}
ledger_by_cell = {(r['position'], r['locale']): r for r in ledger}
positions = list(range(1683, 1703))
locales = manifest['localeOrder']
expected_cells = {(p, l) for p in positions for l in locales}
assert_ok(set(ledger_by_cell) == expected_cells, 'ledger cells are missing, duplicated, or out of scope')
assert_ok(set(target_by_cell) == expected_cells, 'candidate-free targets are missing, duplicated, or out of scope')

seen_proposals = {}
for key in sorted(expected_cells):
    pos, locale = key
    src, ctx, source_target, row = source_by_pos[pos], context_by_pos[pos], target_by_cell[key], ledger_by_cell[key]
    assert_ok(src['sourceKey'] == ctx['sourceKey'] == row['sourceKey'] == source_target['sourceKey'], f'source mismatch {key}')
    assert_ok(src['sourceKeySha256'] == row['sourceKeySha256'] == source_target['sourceKeySha256'], f'source hash mismatch {key}')
    assert_ok(digest(src['sourceKey'].encode('utf-8')) == src['sourceKeySha256'], f'source hash cannot be recomputed {key}')
    assert_ok(row['currentTarget'] == source_target['currentTarget'], f'current translation mismatch {key}')
    assert_ok(row['currentTargetSha256'] == source_target['currentTargetSha256'], f'current target hash mismatch {key}')
    assert_ok(row['catalogPath'] == source_target['catalogPath'] and row['catalogFileSha256'] == source_target['catalogFileSha256'] and row['catalogGitBlob'] == source_target['catalogGitBlob'], f'catalog pin mismatch {key}')
    assert_ok(row['sourceContextSha256'] == ctx['callerContextSha256'] == source_target['sourceContextSha256'] and row['callerContextSha256'] == ctx['callerContextSha256'], f'caller context hash mismatch {key}')
    assert_ok(row['callers'] and row['callerCount'] == ctx['productionCallerCount'] and row['callerOccurrenceCount'] == ctx['callerOccurrenceCount'], f'caller coverage mismatch {key}')
    assert_ok(row['sourceTokens']['placeholders'] == source_target['sourcePlaceholders'] and row['sourceTokens']['protectedLiterals'] == source_target['sourceProtectedLiterals'], f'source token mismatch {key}')
    assert_ok(row['targetTokenVariants'] == source_target['targetTokenVariants'], f'target token evidence mismatch {key}')
    if row['decision'] == 'propose':
        seen_proposals[key] = row.get('proposal')
        assert_ok('proposal' in row, f'proposal missing at {key}')
        proposal_tokens = PLACEHOLDER_RE.findall(row['proposal'])
        source_tokens = PLACEHOLDER_RE.findall(src['sourceKey'])
        assert_ok(sorted(proposal_tokens) == sorted(source_tokens), f'proposal placeholder mismatch {key}')
    else:
        assert_ok(row['decision'] == 'keep' and 'proposal' not in row, f'unknown decision or stray proposal at {key}')

assert_ok(seen_proposals == EXPECTED_PROPOSALS, 'proposal set/text differs from sealed review decisions')
assert_ok(summary['decisionCounts'] == {'keep': 235, 'propose': 5, 'hold': 0}, 'summary decision counts mismatch')
assert_ok(summary['holdCount'] == 0 and summary['callerResolutionHoldsInInput'] == 0, 'hold count mismatch')
assert_ok(summary['sourcePin']['head'] == EXPECTED_HEAD and summary['sourcePin']['tree'] == EXPECTED_TREE, 'summary source pin mismatch')
assert_ok(file_digest(out_dir / 'caller-evidence.jsonl') == summary['callerEvidenceSha256'], 'caller evidence hash mismatch')
assert_ok(load_jsonl(out_dir / 'caller-evidence.jsonl') == context_rows, 'caller evidence differs from candidate-free input')
seal = load_json(out_dir / 'seal.json')
assert_ok(seal['sourcePin']['head'] == EXPECTED_HEAD and seal['sourcePin']['tree'] == EXPECTED_TREE, 'seal source pin mismatch')
assert_ok(seal['ledgerSha256'] == file_digest(out_dir / 'ledger.jsonl'), 'seal ledger hash mismatch')
assert_ok(seal['callerEvidenceSha256'] == file_digest(out_dir / 'caller-evidence.jsonl'), 'seal caller evidence hash mismatch')
assert_ok(seal['reviewSummarySha256'] == file_digest(out_dir / 'review-summary.json'), 'seal summary hash mismatch')
print(f"OK: {len(ledger)} cells; {len(seen_proposals)} proposals; 0 holds; input and output SHA256 sums verified")
