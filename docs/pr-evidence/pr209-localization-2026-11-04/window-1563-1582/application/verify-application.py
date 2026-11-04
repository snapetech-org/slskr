#!/usr/bin/env python3
"""Verify the W1563-W1582 exact-hash product application and evidence packet."""
import argparse
import collections
import hashlib
import json
import re
import subprocess
from pathlib import Path

R = Path(__file__).resolve().parent
REPO = Path(subprocess.check_output(['git', '-C', str(R), 'rev-parse', '--show-toplevel'], text=True).strip())
HEAD = 'f42c7e4be1f2bc9d63e13607d3c311d37f83f355'
TREE = 'f6cb31394c01c90a784d543b8f43b04b232c8b37'
PRODUCT = '62e74939e7b8145055dbd77d83d2b5c3804d3b0b'
PRODUCT_TREE = '9103c0870dc73bdf15737bcdecd522ba511bee5f'
BRANCH = 'codex/slskr-l10n-audit-20261104-resync'
LOCALES = ['es','zh-Hans','hi','de','ja','fr','pt-BR','ar','ko','zh-Hant','vi','id']

def sha(data):
    if isinstance(data, str):
        data = data.encode('utf-8')
    return hashlib.sha256(data).hexdigest()

def canon(obj):
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(',', ':'))

def j(path):
    return json.loads(path.read_text(encoding='utf-8'))

def jl(path):
    return [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines() if line.strip()]

def git(*args):
    return subprocess.check_output(['git', '-C', str(REPO), *args], text=True).strip()

def git_bytes(ref, path):
    return subprocess.check_output(['git', '-C', str(REPO), 'show', f'{ref}:{path}'])

def verify_packet(folder):
    sums = {}
    for line in (folder / 'SHA256SUMS.txt').read_text(encoding='utf-8').splitlines():
        if not line.strip():
            continue
        digest, name = line.split(None, 1)
        name = name.lstrip('* ')
        assert name not in sums
        sums[name] = digest
    actual = {p.relative_to(folder).as_posix() for p in folder.rglob('*')
              if p.is_file() and p != folder / 'SHA256SUMS.txt'}
    assert actual == set(sums), (folder, actual ^ set(sums))
    for name, digest in sums.items():
        assert sha((folder / name).read_bytes()) == digest, (folder, name)
    return sums

def tokens(text):
    placeholders = re.findall(r'\{[A-Za-z][A-Za-z0-9_]*\}', text)
    markup = re.findall(r'</?[A-Za-z][^>]*>', text)
    numbers = re.findall(r'(?<![A-Za-z])\d+(?:[.,]\d+)?%?(?![A-Za-z])', text)
    pattern = r'(?<![A-Za-z0-9])(?:[A-Z]{2,}[A-Z0-9]*|ffmpeg|Chromaprint|Soulseek|Spotify|YouTube|Pushbullet|Matrix|WebSocket|OpenAI)(?![A-Za-z0-9])'
    protected = list(dict.fromkeys(re.findall(pattern, text)))
    return {'placeholders': placeholders, 'markup': markup, 'numbers': numbers, 'protectedLiterals': protected}

def patch_value(raw, key, expected, selected):
    text = raw.decode('utf-8')
    key_token = json.dumps(key, ensure_ascii=False)
    pattern = re.compile(r'(?m)^(?P<indent>[ \t]*)' + re.escape(key_token) + r'(?P<after>[ \t]*:[ \t]*)')
    matches = list(pattern.finditer(text))
    assert len(matches) == 1, (key, len(matches))
    start = matches[0].end()
    current, end = json.JSONDecoder().raw_decode(text, start)
    assert current == expected, (key, current, expected)
    return (text[:start] + json.dumps(selected, ensure_ascii=False) + text[end:]).encode('utf-8')

parser = argparse.ArgumentParser()
parser.add_argument('--precommit', action='store_true', help='verify packet and product before the evidence commit')
args = parser.parse_args()

outer_sums = verify_packet(R)
manifest = j(R / 'application-manifest.json')
file_set = {p.relative_to(R).as_posix() for p in R.rglob('*') if p.is_file()
            and p not in {R / 'SHA256SUMS.txt', R / 'application-manifest.json'}}
assert set(manifest['fileHashes']) == file_set
for name, pin in manifest['fileHashes'].items():
    raw = (R / name).read_bytes()
    assert sha(raw) == pin['sha256'] and len(raw) == pin['byteCount'], name

INPUTS = R / 'review-inputs'
CF = INPUTS / 'candidate-free-input'
PRIMARY = INPUTS / 'primary-review'
BLIND = INPUTS / 'independent-blind-review'
ROOT = INPUTS / 'root-adjudication'
CROSS = R / 'cross-review'
packet_sums = {
    'candidateFree': verify_packet(CF),
    'primary': verify_packet(PRIMARY),
    'independentBlind': verify_packet(BLIND),
    'crossReview': verify_packet(CROSS),
    'rootAdjudication': verify_packet(ROOT),
}
im = j(CF / 'manifest.json')
pm = j(PRIMARY / 'SUMMARY.json')
bm = j(BLIND / 'review-manifest.json')
cross_summary = j(CROSS / 'SUMMARY.json')
root_doc = j(ROOT / 'root-adjudication.json')
assert (im['head'], im['tree']) == (HEAD, TREE)
assert (pm['head'], pm['tree']) == (HEAD, TREE)
assert (bm['head'], bm['tree']) == (HEAD, TREE)
assert (cross_summary['head'], cross_summary['tree']) == (HEAD, TREE)
assert pm['candidateFreeInputChecksumListSha256'] == sha((CF / 'SHA256SUMS.txt').read_bytes())
blind_att = j(BLIND / 'input-attestation.json')
assert blind_att['inputChecksumsFileSha256'] == sha((CF / 'SHA256SUMS.txt').read_bytes())
assert blind_att['inputFilesSha256'] == packet_sums['candidateFree']
assert root_doc['exactHead'] == HEAD and root_doc['exactTree'] == TREE
assert root_doc['sealedCrossPacketModified'] is False

plan = j(R / 'exact-hash-apply-plan.json')
report = j(R / 'apply-readback-report.json')
postpins = j(R / 'postimage-catalog-pins.json')
candidate_cells = jl(CF / 'current-target-cells.jsonl')
cross_rows = jl(CROSS / 'cross-ledger.jsonl')
readback = jl(R / 'apply-readback-cells.jsonl')
assert plan['inputHead'] == report['inputHead'] == HEAD
assert plan['inputTree'] == report['inputTree'] == TREE
assert plan['productCommit'] == report['productCommit'] == PRODUCT
assert plan['productCommitParent'] == report['productCommitParent'] == HEAD
assert git('rev-parse', PRODUCT + '^') == HEAD
assert git('rev-parse', PRODUCT + '^{tree}') == PRODUCT_TREE
if not args.precommit:
    assert git('rev-parse', 'HEAD^') == PRODUCT
assert len(candidate_cells) == len(cross_rows) == len(readback) == 240

cell_by = {(r['position'], r['locale']): r for r in candidate_cells}
cross_by = {(r['position'], r['locale']): r for r in cross_rows}
read_by = {(r['position'], r['locale']): r for r in readback}
selected = {(r['position'], r['locale']): r for r in plan['selectedChanges']}
accepted = {(r['position'], r['locale']): r for r in plan['acceptedHashOnly']}
root_by = {(r['position'], r['locale']): r for r in root_doc['rows']}
assert len(cell_by) == len(cross_by) == len(read_by) == 240
assert len(selected) == 18 and len(accepted) == 222 and not plan['holdHashOnly']
assert set(root_by) == {(1569, 'hi'), (1570, 'hi'), (1570, 'es')}
assert set(selected) | set(accepted) == set(cell_by)
assert set(selected).isdisjoint(accepted)

catalog_meta = j(CF / 'catalog-file-pins.json')['localeCatalogs']
prepins = plan['preApplyCatalogPins']
assert set(prepins) == {r['path'] for r in catalog_meta.values()}
assert set(postpins['catalogFiles']) == set(prepins) and len(prepins) == 12
base_data = {}
final_data = {}
expected_raw = {}
base_raw = {}
final_raw = {}
for locale, pin in catalog_meta.items():
    path = pin['path']
    before = git_bytes(HEAD, path)
    after = git_bytes(PRODUCT, path)
    pre = prepins[path]
    post = postpins['catalogFiles'][path]
    assert sha(before) == pin['sha256'] == pre['sha256']
    assert git('rev-parse', f'{HEAD}:{path}') == pin['gitBlob'] == pre['gitBlob']
    assert len(before) == pre['byteCount']
    assert sha(after) == post['sha256'] and len(after) == post['byteCount']
    assert git('rev-parse', f'{PRODUCT}:{path}') == post['gitBlob']
    b = json.loads(before.decode('utf-8'))
    a = json.loads(after.decode('utf-8'))
    assert len(b) == len(a) == pin['keyCount'] == post['keyCount'] == 5441
    assert list(b.keys()) == list(a.keys())
    order_hash = sha('\n'.join(b.keys()) + '\n')
    assert order_hash == pin['orderedKeySha256'] == post['orderedKeySha256']
    assert post['keySetUnchanged'] and post['keyOrderUnchanged']
    base_data[locale] = b
    final_data[locale] = a
    base_raw[path] = before
    final_raw[path] = after
    expected_raw[path] = before

for root_row in root_doc['rows']:
    key = (root_row['position'], root_row['locale'])
    cross_row = cross_by[key]
    assert root_row['sourceKeySha256'] == cross_row['sourceKeySha256']
    assert root_row['currentTargetSha256'] == cross_row['currentTargetSha256']
    assert root_row['crossRecordSha256'] == cross_row['crossRecordSha256']
    assert sha(root_row['rootTarget']) == root_row['rootTargetSha256']
    assert root_row['crossSelectedTarget'] == cross_row['selectedTarget']
    assert root_row['crossSelectedTargetSha256'] == cross_row['selectedTargetSha256']

changed_pairs = set()
for key, row in selected.items():
    cross_row = cross_by[key]
    cell = cell_by[key]
    assert row['sourceKey'] == cell['sourceKey'] == cross_row['sourceKey']
    assert row['sourceKeySha256'] == cell['sourceKeySha256'] == cross_row['sourceKeySha256'] == sha(row['sourceKey'])
    assert row['currentTargetSha256'] == cell['currentTargetSha256'] == cross_row['currentTargetSha256'] == sha(row['currentTarget'])
    assert row['currentTarget'] == cell['currentTarget'] == cross_row['currentTarget']
    assert row['crossLedgerRowSha256'] == cross_row['crossRecordSha256']
    if key in root_by:
        root_row = root_by[key]
        assert row['selectionOrigin'] == 'root-adjudication'
        assert row['selectedTarget'] == root_row['rootTarget']
        assert row['selectedTargetSha256'] == root_row['rootTargetSha256']
    else:
        assert row['selectionOrigin'] == 'cross-review'
        assert row['selectedTarget'] == cross_row['selectedTarget']
        assert row['selectedTargetSha256'] == cross_row['selectedTargetSha256']
    source_tokens = tokens(row['sourceKey'])
    target_tokens = tokens(row['selectedTarget'])
    assert source_tokens['placeholders'] == target_tokens['placeholders']
    assert source_tokens['markup'] == target_tokens['markup']
    assert source_tokens['numbers'] == target_tokens['numbers']
    assert all(t in target_tokens['protectedLiterals'] for t in source_tokens['protectedLiterals'])
    path = row['catalogPath']
    assert path == catalog_meta[row['locale']]['path']
    expected_raw[path] = patch_value(expected_raw[path], row['sourceKey'], row['currentTarget'], row['selectedTarget'])
    changed_pairs.add((row['locale'], row['sourceKey']))
assert len(changed_pairs) == 18

expected_decisions = collections.Counter()
for cell in candidate_cells:
    key = (cell['position'], cell['locale'])
    cross_row = cross_by[key]
    rb = read_by[key]
    path = catalog_meta[cell['locale']]['path']
    current = base_data[cell['locale']][cell['sourceKey']]
    final = final_data[cell['locale']][cell['sourceKey']]
    assert current == cell['currentTarget'] and sha(current) == cell['currentTargetSha256']
    assert rb['sourceKey'] == cell['sourceKey'] and rb['sourceKeySha256'] == cell['sourceKeySha256']
    assert rb['sourceContextSha256'] == cell['sourceContextSha256']
    assert rb['catalogPath'] == path and rb['currentTargetSha256'] == sha(current)
    assert rb['observedAfterTarget'] == final and rb['observedAfterTargetSha256'] == sha(final)
    assert rb['readbackMatches'] is True and rb['crossLedgerRowSha256'] == cross_row['crossRecordSha256']
    if key in selected:
        sel = selected[key]
        assert final == sel['selectedTarget'] and sha(final) == sel['selectedTargetSha256']
        decision = 'apply-refinement' if sel['crossDisposition'] == 'propose-refinement' else 'apply-correction'
        assert rb['decision'] == decision and rb['selectionOrigin'] == sel['selectionOrigin']
        if key in root_by:
            assert rb['rootAdjudicationTargetSha256'] == root_by[key]['rootTargetSha256']
        expected_decisions[decision] += 1
    else:
        assert key in accepted and cross_row['decision'] == 'accept-current'
        assert rb['decision'] == 'retain-accepted' and rb['selectionOrigin'] == 'cross-review-accept-current'
        assert final == current and accepted[key]['currentTargetSha256'] == sha(current)
        expected_decisions['retain-accepted'] += 1
assert expected_decisions == {'apply-correction': 16, 'apply-refinement': 2, 'retain-accepted': 222}
assert all(expected_raw[path] == final_raw[path] for path in expected_raw)

product_paths = git('diff-tree', '--no-commit-id', '--name-only', '-r', PRODUCT).splitlines()
assert set(product_paths) == set(prepins) and len(product_paths) == 12
numstat = git('diff-tree', '--numstat', '--no-commit-id', '-r', PRODUCT).splitlines()
assert sum(int(x.split('\t')[0]) for x in numstat) == 18
assert sum(int(x.split('\t')[1]) for x in numstat) == 18
assert set(report['productCommitPaths']) == set(product_paths)
assert report['outcomeCounts'] == {'apply-correction': 16, 'apply-refinement': 2, 'retain-accepted': 222, 'retain-hold': 0}
assert report['readbackCellCount'] == 240 and report['catalogChangesApplied'] == 18
assert report['rootAdjudicatedOverrides']['count'] == 3
assert report['allBaseCatalogFilesMatchedPins'] and report['allCurrentTargetGuardsMatched']
assert report['allFinalTargetsReadBack'] and report['allCatalogKeySetsUnchanged'] and report['allCatalogKeyOrdersUnchanged']
assert report['allAcceptedTargetHashesPreserved'] and report['testsBuildsScansOrCiRun'] is False
assert report['workflowsModified'] is False and report['nativeSpeakerSignoff'] is False and report['browserReviewPerformed'] is False

before_body = (R / 'pr-before-body.txt').read_text(encoding='utf-8')
after_body = (R / 'pr-after-body.txt').read_text(encoding='utf-8')
summary = (R / 'pr-body-summary.md').read_text(encoding='utf-8')
separator = '' if before_body.endswith('\n\n') or before_body.endswith('\r\n\r\n') else ('\r\n' if before_body.endswith('\r\n') else ('\n' if before_body.endswith('\n') else '\n\n'))
body_att = j(R / 'pr-body-update-attestation.json')
assert after_body.startswith(before_body)
assert after_body == before_body + separator + summary + '\n'
assert sha(summary) == body_att['appendedSummarySha256']
assert sha(before_body) == body_att['bodyBeforeSha256'] == report['prBeforeBodySha256']
assert sha(after_body) == body_att['bodyAfterSha256'] == report['prAfterBodySha256']
assert body_att['exactPrefixPreserved'] and body_att['apiReadbackMatches']
assert j(R / 'pr-before.json')['body'] == before_body
pr_after = j(R / 'pr-after.json')
assert pr_after['body'] == after_body and pr_after['head']['sha'] == PRODUCT
assert pr_after['state'] == 'open' and pr_after['draft'] is True
assert report['prBodyPrefixPreserved'] and report['prBodyApiReadbackMatches']
push = j(R / 'product-push-attestation.json')
assert push['branchRemoteSha'] == push['pullRefSha'] == PRODUCT
assert len(push['remoteBlobShaReadback']) == 12 and push['testsBuildsScansCiRun'] is False
pre = j(R / 'pre-apply-attestation.json')
assert pre['exactInputHead'] == HEAD and pre['exactInputTree'] == TREE
assert pre['localStatusPorcelain'] == '' and pre['all240CurrentTargetGuardsMatched']

assert sha((R / 'apply-readback-cells.jsonl').read_bytes()) == report['readbackCellsSha256']
assert sha((R / 'exact-hash-apply-plan.json').read_bytes()) == report['applyPlanSha256']
assert sha((R / 'postimage-catalog-pins.json').read_bytes()) == report['postimageCatalogPinsSha256']
assert sha((CROSS / 'SHA256SUMS.txt').read_bytes()) == report['crossReviewChecksumListSha256']

if not args.precommit:
    evidence_commit = git('rev-parse', 'HEAD')
    assert git('rev-parse', evidence_commit + '^') == PRODUCT
    committed = set(git('diff-tree', '--no-commit-id', '--name-only', '-r', evidence_commit).splitlines())
    app_prefix = R.relative_to(REPO).as_posix() + '/'
    expected = {app_prefix + p.relative_to(R).as_posix() for p in R.rglob('*') if p.is_file()}
    assert committed == expected, (committed ^ expected)
    assert git('status', '--porcelain') == ''

print(json.dumps({'result':'PASS','inputHead':HEAD,'productCommit':PRODUCT,'productTree':PRODUCT_TREE,
 'reviewedCells':240,'outcomeCounts':report['outcomeCounts'],'catalogFilesChanged':12,
 'nestedPacketFiles':sum(len(s) + 1 for s in packet_sums.values()),'rootAdjudications':3,
 'prBodyPrefixPreserved':True,'prBodyApiReadbackMatches':True,
 'evidenceCommitVerified':not args.precommit,'checksummedEvidenceFiles':len(outer_sums)},ensure_ascii=False,indent=2))
