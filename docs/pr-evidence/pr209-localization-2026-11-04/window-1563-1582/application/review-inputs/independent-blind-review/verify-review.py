#!/usr/bin/env python3
import hashlib, json, sys
from collections import Counter
from pathlib import Path

OUT = Path(__file__).resolve().parent
INPUT = Path('/home/keith/Documents/code/task-scratch/slskr-pr209-w1563-1582-primary-20261104/candidate-free-input')
def sha(data): return hashlib.sha256(data).hexdigest()
def load_json(path): return json.loads(path.read_text())

def fail(message):
    print(json.dumps({'result':'FAIL','reason':message}, ensure_ascii=False))
    raise SystemExit(1)

# Verify the original candidate-free input package.
input_manifest = load_json(INPUT / 'manifest.json')
input_checks = {}
for line in (INPUT / 'SHA256SUMS.txt').read_text().splitlines():
    if not line.strip(): continue
    expected, name = line.split(maxsplit=1)
    name = name.lstrip('* ')
    actual = sha((INPUT / name).read_bytes())
    if actual != expected: fail(f'input checksum mismatch: {name}')
    input_checks[name] = actual

# Verify all review rows against the pinned source-free cell inputs.
source_cells = [json.loads(x) for x in (INPUT / 'current-target-cells.jsonl').read_text().splitlines() if x.strip()]
rows = [json.loads(x) for x in (OUT / 'review-cells.jsonl').read_text().splitlines() if x.strip()]
if len(rows) != 240: fail(f'expected 240 review records, found {len(rows)}')
if len(source_cells) != 240: fail(f'expected 240 current input cells, found {len(source_cells)}')
manifest = load_json(OUT / 'review-manifest.json')
if manifest.get('head') != input_manifest.get('head') or manifest.get('tree') != input_manifest.get('tree'):
    fail('review manifest source pin mismatch')
expected = {(x['position'], x['locale']): x for x in source_cells}
seen = set()
allowed = {'accept','hold','correction','refinement'}
counts = Counter()
for row in rows:
    key = (row.get('position'), row.get('locale'))
    if key in seen: fail(f'duplicate cell {key}')
    seen.add(key)
    if key not in expected: fail(f'unexpected cell {key}')
    src = expected[key]
    for out_field, in_field in [('sourceKey','sourceKey'),('sourceKeySha256','sourceKeySha256'),('sourceContextSha256','sourceContextSha256'),('currentTarget','currentTarget'),('currentTargetSha256','currentTargetSha256'),('catalogPath','catalogPath')]:
        if row.get(out_field) != src.get(in_field): fail(f'{key}: {out_field} does not match candidate-free input')
    if sha(row['currentTarget'].encode('utf-8')) != row['currentTargetSha256']:
        fail(f'{key}: current target hash mismatch')
    if row.get('decision') not in allowed: fail(f'{key}: invalid decision')
    if not row.get('reason'): fail(f'{key}: missing reason')
    if row['decision'] in {'correction','refinement'} and not row.get('suggestedTarget'):
        fail(f'{key}: missing suggested target')
    if row['decision'] in {'accept','hold'} and row.get('suggestedTarget') is not None:
        fail(f'{key}: unexpected suggested target')
    recorded_hash = row.pop('reviewRecordSha256', None)
    canonical = json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode('utf-8')
    if recorded_hash != sha(canonical): fail(f'{key}: review record hash mismatch')
    row['reviewRecordSha256'] = recorded_hash
    counts[row['decision']] += 1
if seen != set(expected): fail('review coverage does not match exact input cell set')
if sum(counts.values()) != 240: fail('decision count mismatch')
if manifest.get('cellDecisions') != dict(sorted(counts.items())): fail('review manifest decision counts mismatch')
attestation = load_json(OUT / 'input-attestation.json')
if attestation.get('inputFilesSha256') != input_checks: fail('input attestation checksum listing mismatch')
if attestation.get('candidateFreeVerifierResult') != 'PASS': fail('candidate-free verifier result not recorded as PASS')
if attestation.get('pinnedSourceWorktree', {}).get('head') != input_manifest['head'] or attestation.get('pinnedSourceWorktree', {}).get('tree') != input_manifest['tree'] or not attestation.get('pinnedSourceWorktree', {}).get('statusClean'):
    fail('source worktree attestation mismatch')

# Verify packet file checksums (the sums file itself is intentionally self-excluding).
output_checks = {}
for line in (OUT / 'SHA256SUMS.txt').read_text().splitlines():
    if not line.strip(): continue
    expected_hash, name = line.split(maxsplit=1)
    name = name.lstrip('* ')
    actual = sha((OUT / name).read_bytes())
    if expected_hash != actual: fail(f'output checksum mismatch: {name}')
    output_checks[name] = actual
print(json.dumps({'result':'PASS','inputChecksummedFiles':len(input_checks),'reviewRecords':len(rows),'decisionCounts':dict(sorted(counts.items())),'outputChecksummedFiles':len(output_checks),'head':input_manifest['head'],'tree':input_manifest['tree']}, ensure_ascii=False, sort_keys=True))
