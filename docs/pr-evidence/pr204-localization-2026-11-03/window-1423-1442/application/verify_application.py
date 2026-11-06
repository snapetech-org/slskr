#!/usr/bin/env python3
"""Portable exact-head verifier for the slskR W1423-W1442 application."""
from pathlib import Path
from collections import Counter
import hashlib, json, re, subprocess, sys

APP = Path(__file__).resolve().parent
WINDOW = APP.parent
REPO = APP.parents[4]
ALLOW_UNCOMMITTED = '--allow-uncommitted' in sys.argv
BASE = '7ca8589266ab4c5a925782a8726d7e57b4ed7427'
BASE_TREE = '09adcb271a2eb92770df4a20098dccc3fde2a59f'
BRANCH = 'codex/slskr-l10n-audit-20261030'


def fail(message):
    raise SystemExit('FAIL: ' + message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def readj(path):
    return json.loads(path.read_text(encoding='utf-8'))


def readjl(path):
    return [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines() if line.strip()]


def git(*args):
    return subprocess.check_output(['git', '-C', str(REPO), *args], text=True).strip()


def token_sets(value):
    placeholders = re.findall(r'\{[A-Za-z][A-Za-z0-9_]*\}', value)
    markup = re.findall(r'<\/?[A-Za-z][^>]*>', value)
    numeric = re.findall(r'(?<![A-Za-z])\d+(?:[.,]\d+)?%?(?![A-Za-z])', value)
    protected = []
    for match in re.finditer(r'(?<![A-Za-z0-9])(?:[A-Z]{2,}[A-Z0-9]*|ffmpeg|Chromaprint|Soulseek|Spotify|YouTube|Pushbullet|Matrix|WebSocket|OpenAI)(?![A-Za-z0-9])', value):
        if match.group(0) not in protected:
            protected.append(match.group(0))
    return {'placeholders': placeholders, 'markup': markup, 'numeric': numeric, 'protectedLiterals': protected}


def check_sums(folder, name='SHA256SUMS.txt', exact=False):
    checksum = folder / name
    if not checksum.is_file():
        fail(f'missing checksum list: {checksum}')
    listed = {}
    for line in checksum.read_text(encoding='utf-8').splitlines():
        if not line.strip():
            continue
        parts = line.split('  ', 1)
        if len(parts) != 2:
            fail(f'malformed checksum line: {checksum}')
        digest, rel = parts
        while rel.startswith('./'):
            rel = rel[2:]
        if rel in listed:
            fail(f'duplicate checksum entry: {rel}')
        listed[rel] = digest
    for rel, expected in listed.items():
        target = folder / rel
        if not target.is_file() or sha(target.read_bytes()) != expected:
            fail(f'checksum mismatch: {target}')
    if exact:
        actual = {p.relative_to(folder).as_posix() for p in folder.rglob('*') if p.is_file() and p != checksum}
        if set(listed) != actual:
            fail(f'checksum inventory mismatch under {folder}')


def verify_input(folder, sums, verifier):
    check_sums(folder, sums)
    run = subprocess.run([sys.executable, verifier], cwd=folder, text=True, capture_output=True)
    if run.returncode:
        fail(f'input verifier failed in {folder}: {run.stdout}{run.stderr}')


result = readj(APP / 'application-result.json')
if result['baseHead'] != BASE or result['baseTree'] != BASE_TREE:
    fail('application result does not match pinned base')
if git('rev-parse', BASE) != BASE or git('rev-parse', f'{BASE}^{{tree}}') != BASE_TREE:
    fail('base commit/tree is unavailable or changed')
head = git('rev-parse', 'HEAD')
if ALLOW_UNCOMMITTED:
    if head != BASE:
        fail('--allow-uncommitted is only valid while HEAD is the pinned base')
else:
    if head == BASE or subprocess.run(['git', '-C', str(REPO), 'merge-base', '--is-ancestor', BASE, head]).returncode != 0:
        fail('application head is not a descendant of the pinned head')
    parents = git('rev-list', '--parents', '-n', '1', 'HEAD').split()
    if len(parents) != 2 or parents[1] != BASE:
        fail('application commit is not a focused single child of the pinned head')
    if git('status', '--porcelain', '--untracked-files=all'):
        fail('worktree is not clean')
if git('branch', '--show-current') != BRANCH:
    fail('unexpected branch')

check_sums(APP, exact=True)
for folder, sums, verifier in (
    (WINDOW / 'candidate-free-input', 'SHA256SUMS.txt', 'verify-candidate-free.py'),
    (WINDOW / 'primary-review', 'SHA256SUMS.txt', 'verify_primary.py'),
    (WINDOW / 'independent-review', 'SHA256SUMS', 'verify_review.py'),
    (WINDOW / 'cross-audit', 'SHA256SUMS.txt', 'verify_cross_audit.py'),
):
    verify_input(folder, sums, verifier)

ledger = readjl(WINDOW / 'cross-audit' / 'cross-audit-ledger.jsonl')
plan = readjl(APP / 'apply-plan.jsonl')
readback = readjl(APP / 'application-readback.jsonl')
if len(ledger) != 240 or len(readback) != 240:
    fail('240-cell coverage mismatch')
counts = Counter(row['decision'] for row in ledger)
if counts != Counter({'accept-current': 201, 'correction': 38, 'refinement': 1}):
    fail(f'disposition totals mismatch: {counts}')
selected = [row for row in ledger if row['decision'] in ('correction', 'refinement')]
if len(plan) != 39 or len(selected) != 39:
    fail('selected update count mismatch')
plan_by = {(row['catalogPath'], row['sourceKey']): row for row in plan}
if len(plan_by) != 39:
    fail('duplicate application plan row')
ledger_by = {(row['catalogPath'], row['sourceKey']): row for row in ledger}
if set(plan_by) != {(row['catalogPath'], row['sourceKey']) for row in selected}:
    fail('application plan differs from selected cross-audit rows')

pins = readj(WINDOW / 'candidate-free-input' / 'catalog-file-pins.json')
invariants = readj(APP / 'catalog-invariants.json')
inv_by_path = {row['catalogPath']: row for row in invariants['catalogs']}
if len(inv_by_path) != 12 or set(inv_by_path) != {row['path'] for row in pins['localeCatalogs'].values()}:
    fail('catalog invariant coverage mismatch')

for locale, pin in pins['localeCatalogs'].items():
    path = pin['path']
    old_raw = (APP / 'before-catalogs' / Path(path).name).read_bytes()
    base_raw = subprocess.check_output(['git', '-C', str(REPO), 'show', f'{BASE}:{path}'])
    if old_raw != base_raw or sha(old_raw) != pin['sha256']:
        fail(f'baseline catalog mismatch: {path}')
    if git('rev-parse', f'{BASE}:{path}') != pin['gitBlob']:
        fail(f'baseline Git blob mismatch: {path}')
    old = json.loads(old_raw)
    new_raw = (REPO / path).read_bytes()
    new = json.loads(new_raw)
    inv = inv_by_path[path]
    order_before = sha(('\n'.join(old) + '\n').encode('utf-8'))
    order_after = sha(('\n'.join(new) + '\n').encode('utf-8'))
    if len(old) != len(new) != 5441:
        fail(f'catalog key count mismatch: {path}')
    if len(old) != 5441 or len(new) != 5441 or list(old) != list(new):
        fail(f'catalog key set/order changed: {path}')
    if order_before != order_after or order_before != pin['orderedKeySha256']:
        fail(f'catalog ordered-key hash mismatch: {path}')
    after_blob = subprocess.check_output(['git', '-C', str(REPO), 'hash-object', '--stdin'], input=new_raw).decode().strip() if ALLOW_UNCOMMITTED else git('rev-parse', f'HEAD:{path}')
    if sha(new_raw) != inv['afterSha256'] or after_blob != inv['afterGitBlob']:
        fail(f'after-catalog hash/blob mismatch: {path}')
    if inv['beforeSha256'] != pin['sha256'] or inv['beforeGitBlob'] != pin['gitBlob']:
        fail(f'invariant baseline pin mismatch: {path}')
    actual_diff = {key for key in old if old[key] != new[key]}
    expected_diff = {r['sourceKey'] for r in selected if r['catalogPath'] == path}
    if actual_diff != expected_diff or set(inv['changedSourceKeys']) != expected_diff:
        fail(f'catalog changed-value set mismatch: {path}')

for row, rb in zip(ledger, readback):
    key = (row['catalogPath'], row['sourceKey'])
    if (rb['position'], rb['locale'], rb['sourceKey'], rb['catalogPath']) != (row['position'], row['locale'], row['sourceKey'], row['catalogPath']):
        fail(f'readback row order/key mismatch: {key}')
    old = json.loads((APP / 'before-catalogs' / Path(row['catalogPath']).name).read_text(encoding='utf-8'))
    new = json.loads((REPO / row['catalogPath']).read_text(encoding='utf-8'))
    if old[row['sourceKey']] != row['currentTarget'] or sha(old[row['sourceKey']].encode('utf-8')) != row['currentTargetSha256']:
        fail(f'candidate-free current target mismatch: {key}')
    if new[row['sourceKey']] != row['selectedTarget'] or sha(new[row['sourceKey']].encode('utf-8')) != row['selectedTargetSha256']:
        fail(f'selected target mismatch: {key}')
    if rb['readbackTarget'] != row['selectedTarget'] or rb['readbackTargetSha256'] != row['selectedTargetSha256'] or rb['matches'] is not True:
        fail(f'application readback mismatch: {key}')
    if rb['disposition'] != row['decision'] or rb['tokenChecksPass'] is not True:
        fail(f'disposition/token readback mismatch: {key}')
    expected_tokens = token_sets(row['sourceKey'])
    if expected_tokens != token_sets(row['selectedTarget']) or rb['sourceTokens'] != expected_tokens or rb['selectedTokens'] != expected_tokens:
        fail(f'token/protected-literal preservation mismatch: {key}')
    if row['decision'] == 'accept-current' and (old[row['sourceKey']] != new[row['sourceKey']] or key in plan_by):
        fail(f'accept-current cell changed: {key}')
    if row['decision'] in ('correction', 'refinement'):
        p = plan_by[key]
        for field in ('selectedTarget', 'selectedTargetSha256', 'currentTargetSha256', 'decision'):
            if p[field] != row[field]:
                fail(f'plan hash/target mismatch {field}: {key}')

holds = readjl(WINDOW / 'candidate-free-input' / 'prior-hold-reattestation.jsonl')
hold_readback = readjl(APP / 'prior-hold-readback.jsonl')
if len(holds) != 35 or len(hold_readback) != 35:
    fail('carried hold count mismatch')
for hold, rb in zip(holds, hold_readback):
    after = json.loads((REPO / hold['currentCatalogPath']).read_text(encoding='utf-8'))[hold['sourceKey']]
    digest = sha(after.encode('utf-8'))
    if digest != hold['priorCurrentTargetSha256'] or digest != hold['currentTargetSha256'] or rb['preserved'] is not True or rb['readbackTargetSha256'] != digest:
        fail(f'carried hold changed: {hold["position"]}/{hold["locale"]}')

prior = readjl(WINDOW / 'candidate-free-input' / 'prior-selection-reattestation.jsonl')
selection_readback = readjl(APP / 'prior-selection-readback.jsonl')
queue = {row['position']: row for row in readjl(WINDOW / 'candidate-free-input' / 'source-queue.jsonl')}
if len(prior) != 180 or len(selection_readback) != 180:
    fail('prior selected-source count mismatch')
for old, rb in zip(prior, selection_readback):
    q = queue.get(old['position'])
    if not q or q['sourceKey'] != old['currentQueueSourceKey'] or q['sourceKeySha256'] != old['currentQueueSourceKeySha256']:
        fail(f'prior source selection drift: {old["position"]}')
    if rb['readbackSourceKey'] != q['sourceKey'] or rb['preserved'] is not True or rb['sourceKeySha256'] != q['sourceKeySha256']:
        fail(f'prior source selection readback mismatch: {old["position"]}')

if result['updates'] != 39 or result['corrections'] != 38 or result['refinements'] != 1 or result['retains'] != 201:
    fail('application result disposition totals mismatch')
if result['priorHoldsReattested'] != 35 or result['priorHoldsPreserved'] != 35 or result['priorSelectionsReattested'] != 180 or result['priorSelectionsPreserved'] != 180:
    fail('application result prior-state totals mismatch')
if result['catalogFilesChanged'] != 11 or result['tokenProtectedLiteralMismatches'] != 0:
    fail('application result catalog/token totals mismatch')

expected_catalogs = {row['catalogPath'] for row in invariants['catalogs'] if row['catalogChanged']}
window_rel = WINDOW.relative_to(REPO).as_posix()
expected_evidence = {p.relative_to(REPO).as_posix() for p in WINDOW.rglob('*') if p.is_file()}
if ALLOW_UNCOMMITTED:
    tracked_changes = set(git('diff', '--name-only', BASE).splitlines())
    untracked = set(git('ls-files', '--others', '--exclude-standard').splitlines())
    changed = tracked_changes | untracked
else:
    changed = set(git('diff', '--name-only', BASE, 'HEAD').splitlines())
if changed != expected_catalogs | expected_evidence:
    fail(f'commit file set differs from catalogs/evidence: extra={sorted(changed-(expected_catalogs|expected_evidence))[:10]} missing={sorted((expected_catalogs|expected_evidence)-changed)[:10]}')
if git('diff', '--name-only', BASE, 'HEAD', '--', '.github/workflows').strip():
    fail('workflow files changed')

print(json.dumps({'result': 'PASS', 'head': head, 'tree': git('rev-parse', 'HEAD^{tree}'),
                  'cells': 240, 'updates': 39, 'corrections': 38, 'refinements': 1, 'retains': 201,
                  'carriedHoldsPreserved': 35, 'priorSelectionsPreserved': 180,
                  'catalogsChanged': len(expected_catalogs), 'tokenProtectedLiteralMismatches': 0,
                  'fileSet': 'only 11 locale catalogs plus this evidence window', 'workflowsChanged': False, 'verificationMode': 'uncommitted preflight' if ALLOW_UNCOMMITTED else 'committed head'}, ensure_ascii=False, indent=2))
