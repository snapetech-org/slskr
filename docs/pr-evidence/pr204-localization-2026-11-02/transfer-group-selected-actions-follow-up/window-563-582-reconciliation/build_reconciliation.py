#!/usr/bin/env python3
"""Build a read-only, exact-head reconciliation for slskR W563–582 locale B."""
import collections
import hashlib
import json
import re
import subprocess
from pathlib import Path

OUT = Path('/mnt/disks/scratch/task-scratch/slskr-pr204-W563-582-reconciliation-20261102')
WORKTREE = Path('/mnt/disks/scratch/task-worktrees/localization-20261102/slskr-pr204-w503-522')
PRIMARY = Path('/mnt/disks/scratch/task-scratch/slskr-pr204-W563-582-primary-20261102/packet')
XREVIEW = Path('/mnt/disks/scratch/task-scratch/slskr-pr204-W563-582-crossreview-20261102')
LIVE = 'aa106d2505de8c9ace2d7d6dbf2af9777651947d'
TREE = 'f99e717b4b77c8da098e7b8fc163926d4d32e926'
B_REVIEW_HEAD = '9d3aae249503d1732cc890a650052c85c57b2919'
B_REVIEW_TREE = 'ec98bce9f26fc3fbef2968ba3e2b737b1d7fa214'
SOURCE = '7ff454828398de6a3cfb72fe7f0ed21fe419425b'
SOURCE_TREE = '9e9f2aa743c4ff3236af8f99619803bdc3a37152'
BASE = '2a2b188f10b9460a15bc6d5c34e406b0193d51ba'
B_LOCALES = ['ja', 'ko', 'pt-BR', 'vi', 'zh-Hans', 'zh-Hant']
LOCALE_PATHS = {loc: f'web/src/lib/locales/ui-labels.{loc}.json' for loc in B_LOCALES}
CAP = 'Cap RustyMilk rendering for lower GPU load, or leave it uncapped for maximum smoothness.'
HOLD_SOURCE = 'Cancel{all}'
HOLD_LOCALES = ['ja', 'ko', 'pt-BR', 'vi', 'zh-Hans', 'zh-Hant']

def sha(data):
    return hashlib.sha256(data).hexdigest()

def git(*args):
    return subprocess.check_output(['git', '-C', str(WORKTREE), *args]).decode().strip()

def show(revision, path):
    return subprocess.check_output(['git', '-C', str(WORKTREE), 'show', f'{revision}:{path}'])

def readj(path):
    return json.loads(path.read_text(encoding='utf-8'))

def readjl(path):
    return [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines() if line]

def writej(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

def writejl(path, rows):
    path.write_text(''.join(json.dumps(r, ensure_ascii=False, separators=(',', ':')) + '\n' for r in rows), encoding='utf-8')

def verify_manifest(directory, manifest_name):
    for line in (directory / manifest_name).read_text(encoding='utf-8').splitlines():
        expected, name = line.split(None, 1)
        name = name.lstrip('* ')
        assert sha((directory / name).read_bytes()) == expected, (str(directory / manifest_name), name)

def placeholders(text):
    return sorted(set(re.findall(r'\{[^{}]+\}', text)))

def markup(text):
    return re.findall(r'</?[A-Za-z][^>]*>', text)

def protected(text):
    return {x: text.count(x) for x in ('RustyMilk', 'GPU') if text.count(x)}

assert git('rev-parse', f'{LIVE}^{{tree}}') == TREE
pr = json.loads(subprocess.check_output([
    'gh', 'pr', 'view', '--repo', 'snapetech-org/slskR', '204',
    '--json', 'state,isDraft,headRefOid,headRefName,baseRefOid'
]))
assert pr['state'] == 'OPEN' and pr['isDraft'] is True
assert pr['headRefOid'] == LIVE and pr['baseRefOid'] == BASE, pr
assert git('merge-base', LIVE, BASE) == BASE
verify_manifest(PRIMARY, 'SHA256SUMS')
verify_manifest(XREVIEW, 'SHA256SUMS')
verify_manifest(XREVIEW / 'locale-b-by-b', 'SHA256SUMS')

# The source-index order is the frozen, source-baseline inventory, not the key
# order of locale JSON files. The baseline key set and every source hash match.
inventory_path = PRIMARY / 'source-inventory.jsonl'
inventory_raw = inventory_path.read_bytes()
inventory = readjl(inventory_path)
source_ids = [r['source_id'] for r in inventory]
assert len(source_ids) == 5437 and len(set(source_ids)) == 5437
source_positions = {source_id: i for i, source_id in enumerate(source_ids)}
base_ja = json.loads(show(SOURCE, 'web/src/lib/locales/ui-labels.ja.json'))
assert set(base_ja) == set(source_ids)
for source_id, row in zip(source_ids, inventory):
    assert sha(source_id.encode('utf-8')) == row['source_sha256']

live_catalogs = {}
for locale, path in LOCALE_PATHS.items():
    raw = show(LIVE, path)
    data = json.loads(raw)
    assert set(source_ids).issubset(data)
    live_catalogs[locale] = {
        'path': path, 'data': data, 'raw': raw,
        'blob': git('rev-parse', f'{LIVE}:{path}'), 'fileSha256': sha(raw),
    }

primary_cells = {(r['source_id'], r['locale']): r for r in readjl(PRIMARY / 'current-cells.jsonl')}
primary_rows = {(r['source_id'], r['locale']): r for r in readjl(PRIMARY / 'primary-review-ledger.jsonl')}
root_rows = {(r['source_id'], r['locale']): r for r in readjl(XREVIEW / 'cross-review-ledger.jsonl')}
b_rows = {(r['sourceId'], r['locale']): r for r in readjl(XREVIEW / 'locale-b-by-b/cross-review-ledger.jsonl')}
contexts = {r['source_id']: r for r in readjl(PRIMARY / 'source-context.jsonl')}

# Four locale-B refinements and two Canonical-support live conflicts. Korean is
# both a refinement and a conflict, so it has one row with both issue labels.
decisions = {
    ('Cancelled', 'ja'): {
        'action': 'recommend-correction', 'issueTypes': ['locale-b-refinement'],
        'target': 'キャンセル済み', 'confidence': 'moderate',
        'rationale': 'These callers use the key for a completed/cancelled state in history, job status, and transfer filtering. キャンセル alone is also the Cancel action; 済み marks the terminal state.',
    },
    ('Canonical support from', 'ja'): {
        'action': 'recommend-live-target-replacement', 'issueTypes': ['canonical-support-live-conflict'],
        'target': '正規録音を支持する', 'confidence': 'moderate',
        'rationale': 'Both callers put a count of track candidates after this prefix. Those candidates support the canonical recording; 録音 names that supported audio object more precisely than the live 判定 (judgment). This is the exact target in the B packet’s accepted primary proposal.',
    },
    ('Canonical support from', 'ko'): {
        'action': 'recommend-refinement', 'issueTypes': ['locale-b-refinement', 'canonical-support-live-conflict'],
        'target': '정규 녹음을 뒷받침하는', 'confidence': 'moderate',
        'rationale': 'Both callers put a count of track candidates after this prefix. 녹음 names the canonical recording those candidates support; it is more concrete than the live 판정 (judgment) or the primary 정보 (information).',
    },
    (CAP, 'zh-Hans'): {
        'action': 'recommend-refinement', 'issueTypes': ['locale-b-refinement'],
        'target': '限制 RustyMilk 渲染以降低 GPU 负载，或不限制渲染以获得最流畅的体验。', 'confidence': 'moderate',
        'rationale': 'The current 最大平滑度 is a literal rendering of smoothness. 最流畅的体验 is more natural for this FPS-cap tooltip; the live caller is the Full/60/30/24 FPS selector.',
    },
    (CAP, 'zh-Hant'): {
        'action': 'recommend-refinement', 'issueTypes': ['locale-b-refinement'],
        'target': '限制 RustyMilk 渲染以降低 GPU 負載，或不限制渲染以獲得最流暢的體驗。', 'confidence': 'moderate',
        'rationale': 'The B refinement replaces literal 最大平滑度 with the natural gaming sense 最流暢的體驗 and is written in Traditional script; accept its exact target.',
    },
}

action_rows = []
for (source_id, locale), decision in decisions.items():
    position = source_positions[source_id]
    assert 563 <= position <= 582
    key = (source_id, locale)
    cell, primary, root_review, b_review = primary_cells[key], primary_rows[key], root_rows[key], b_rows[key]
    current = live_catalogs[locale]['data'][source_id]
    current_hash = sha(current.encode('utf-8'))
    source_hash = sha(source_id.encode('utf-8'))
    assert cell['source_index'] == primary['source_index'] == position
    assert source_hash == cell['source_sha256'] == primary['source_sha256'] == b_review['sourceSha256']
    assert b_review['observedLiveHead'] == B_REVIEW_HEAD and b_review['observedLiveTree'] == B_REVIEW_TREE
    assert current == b_review['liveHeadTarget'] and current_hash == b_review['liveHeadTargetSha256']
    assert root_review['source_index'] == position
    for candidate_text, candidate_hash in (
        (primary.get('proposed_text'), primary.get('proposed_target_sha256')),
        (root_review.get('final_recommended_text'), root_review.get('final_recommended_sha256')),
        (b_review.get('crossReviewTarget'), b_review.get('crossReviewTargetSha256')),
    ):
        if candidate_text is not None:
            assert candidate_hash == sha(candidate_text.encode('utf-8')), (key, candidate_text)
    target = decision['target']
    target_hash = sha(target.encode('utf-8'))
    assert placeholders(target) == placeholders(source_id) == placeholders(current)
    assert markup(target) == markup(source_id) == markup(current)
    assert protected(target) == protected(source_id) == protected(current)
    context = contexts[source_id]
    action_rows.append({
        'schemaVersion': 1, 'repository': 'snapetech-org/slskR', 'pullRequest': 204,
        'head': LIVE, 'tree': TREE, 'sourceHead': SOURCE, 'sourceTree': SOURCE_TREE,
        'sourceIndex': position, 'sourceId': source_id, 'locale': locale,
        'sourceSha256': source_hash, 'catalogPath': live_catalogs[locale]['path'],
        'catalogBlob': live_catalogs[locale]['blob'], 'catalogFileSha256': live_catalogs[locale]['fileSha256'],
        'frozenCurrentTarget': cell['current_text'], 'frozenCurrentTargetSha256': cell['current_target_sha256'],
        'liveCurrentTarget': current, 'liveCurrentTargetSha256': current_hash,
        'primaryDecision': primary['review_decision'], 'primaryCandidate': primary.get('proposed_text'),
        'primaryCandidateSha256': primary.get('proposed_target_sha256'),
        'firstCrossreviewDisposition': root_review['cross_review_disposition'],
        'firstCrossreviewTarget': root_review.get('final_recommended_text'),
        'firstCrossreviewTargetSha256': root_review.get('final_recommended_sha256'),
        'localeBDisposition': b_review['crossReviewDisposition'],
        'localeBObservedHead': b_review['observedLiveHead'], 'localeBObservedTree': b_review['observedLiveTree'],
        'localeBCandidate': b_review.get('crossReviewTarget'),
        'localeBCandidateSha256': b_review.get('crossReviewTargetSha256'),
        'localeBLiveComparison': b_review['liveHeadTargetComparison'],
        'recommendedAction': decision['action'], 'issueTypes': decision['issueTypes'],
        'recommendedTarget': target, 'recommendedTargetSha256': target_hash,
        'rationale': decision['rationale'], 'confidence': decision['confidence'],
        'callerContext': context['context'], 'callerStatus': context['caller_status'],
        'callerPinCount': len(context.get('localized_caller_pins', [])) + len(context.get('supporting_caller_pins', [])),
        'callerPinsReattested': True, 'placeholderParity': True, 'markupParity': True,
        'protectedLiteralParity': True, 'nativeSpeakerApproval': False,
    })

# Keep every live locale-B Cancel{all} cell held: line 102 appends literal English.
hold_rows = []
for locale in HOLD_LOCALES:
    key = (HOLD_SOURCE, locale)
    position = source_positions[HOLD_SOURCE]
    cell, primary, root_review, b_review = primary_cells[key], primary_rows[key], root_rows[key], b_rows[key]
    current = live_catalogs[locale]['data'][HOLD_SOURCE]
    current_hash = sha(current.encode('utf-8'))
    assert position == 568 and current == cell['current_text'] == b_review['liveHeadTarget']
    assert current_hash == b_review['liveHeadTargetSha256']
    assert cell['source_sha256'] == sha(HOLD_SOURCE.encode('utf-8'))
    assert b_review['crossReviewDisposition'] == 'held'
    assert placeholders(current) == placeholders(HOLD_SOURCE)
    assert markup(current) == markup(HOLD_SOURCE)
    assert protected(current) == protected(HOLD_SOURCE)
    context = contexts[HOLD_SOURCE]
    hold_rows.append({
        'schemaVersion': 1, 'repository': 'snapetech-org/slskR', 'pullRequest': 204,
        'head': LIVE, 'tree': TREE, 'sourceHead': SOURCE, 'sourceTree': SOURCE_TREE,
        'sourceIndex': position, 'sourceId': HOLD_SOURCE, 'locale': locale,
        'sourceSha256': sha(HOLD_SOURCE.encode('utf-8')),
        'catalogPath': live_catalogs[locale]['path'], 'catalogBlob': live_catalogs[locale]['blob'],
        'catalogFileSha256': live_catalogs[locale]['fileSha256'],
        'frozenCurrentTarget': cell['current_text'], 'frozenCurrentTargetSha256': cell['current_target_sha256'],
        'liveCurrentTarget': current, 'liveCurrentTargetSha256': current_hash,
        'primaryDecision': primary['review_decision'], 'firstCrossreviewDisposition': root_review['cross_review_disposition'],
        'localeBDisposition': b_review['crossReviewDisposition'],
        'localeBObservedHead': b_review['observedLiveHead'], 'localeBObservedTree': b_review['observedLiveTree'],
        'recommendedAction': 'preserve-hold', 'recommendedTarget': None, 'recommendedTargetSha256': None,
        'rationale': 'The live caller builds `all` as an empty string or the literal English suffix “ Selected” and inserts it into {all}. A catalog target alone cannot localize the full multi-selection button; retain the hold pending a separate caller fix.',
        'confidence': 'high', 'callerContext': context['context'], 'callerPinsReattested': True,
        'placeholderParity': True, 'markupParity': True, 'protectedLiteralParity': True,
        'nativeSpeakerApproval': False,
    })
action_rows.extend(hold_rows)

# Re-attest source excerpts for every affected ID at exact live commit objects.
action_ids = {sid for sid, _ in decisions} | {HOLD_SOURCE}
caller_refs = 0
caller_map = {}
for source_id in action_ids:
    context = contexts[source_id]
    for role, pins in (('localized', context.get('localized_caller_pins', [])),
                       ('supporting', context.get('supporting_caller_pins', []))):
        for pin in pins:
            caller_refs += 1
            path = pin['path']
            raw = show(LIVE, path)
            lines = raw.decode('utf-8').splitlines()
            blob = git('rev-parse', f'{LIVE}:{path}')
            assert blob == pin['pr_blob_oid'] and sha(raw) == pin['pr_file_sha256'], (source_id, path, 'caller file changed')
            excerpts = pin.get('excerpt', [])
            if not any(e['line'] == pin['occurrence_line'] for e in excerpts):
                excerpts = excerpts + [{'line': pin['occurrence_line'], 'text': pin['occurrence_text']}]
            for excerpt in excerpts:
                line_no = excerpt['line']
                assert 1 <= line_no <= len(lines) and lines[line_no - 1] == excerpt['text'], (source_id, path, line_no)
                k = (path, line_no)
                row = caller_map.setdefault(k, {
                    'schemaVersion': 1, 'head': LIVE, 'tree': TREE, 'path': path, 'line': line_no,
                    'lineText': lines[line_no - 1], 'lineSha256': sha(lines[line_no - 1].encode('utf-8')),
                    'fileBlob': blob, 'fileSha256': sha(raw), 'sourceIds': [], 'pinRoles': [],
                })
                assert row['fileBlob'] == blob and row['lineText'] == lines[line_no - 1]
                if source_id not in row['sourceIds']:
                    row['sourceIds'].append(source_id)
                if role not in row['pinRoles']:
                    row['pinRoles'].append(role)
caller_rows = sorted(caller_map.values(), key=lambda row: (row['path'], row['line']))
for row in action_rows:
    row['callerAttestationRefs'] = [f"{c['path']}:{c['line']}" for c in caller_rows if row['sourceId'] in c['sourceIds']]

assert len(action_rows) == 11 and len(hold_rows) == 6
assert sum('locale-b-refinement' in row.get('issueTypes', []) for row in action_rows) == 4
assert sum('canonical-support-live-conflict' in row.get('issueTypes', []) for row in action_rows) == 2

writejl(OUT / 'action-ledger.jsonl', action_rows)
writejl(OUT / 'caller-pin-reattestation.jsonl', caller_rows)
catalog_attestation = {
    'head': LIVE, 'tree': TREE, 'sourceHead': SOURCE, 'sourceTree': SOURCE_TREE,
    'sourceInventoryRows': len(source_ids), 'sourceInventorySha256': sha(inventory_raw),
    'sourcePositionsUseFrozenInventoryOrder': True,
    'sourceBaselineCatalogKeySetMatchesInventory': True,
    'liveCatalogs': {loc: {'path': live_catalogs[loc]['path'], 'blob': live_catalogs[loc]['blob'],
                           'fileSha256': live_catalogs[loc]['fileSha256'],
                           'keyCount': len(live_catalogs[loc]['data'])} for loc in B_LOCALES},
}
writej(OUT / 'source-catalog-attestation.json', catalog_attestation)
inputs = {
    'schemaVersion': 1, 'repository': 'snapetech-org/slskR', 'pullRequest': 204,
    'livePullRequest': pr, 'head': LIVE, 'tree': TREE, 'sourceHead': SOURCE, 'sourceTree': SOURCE_TREE,
    'localeBReviewObservedHead': B_REVIEW_HEAD, 'localeBReviewObservedTree': B_REVIEW_TREE,
    'primaryPacket': str(PRIMARY), 'primarySha256SumsSha256': sha((PRIMARY / 'SHA256SUMS').read_bytes()),
    'firstCrossreviewPacket': str(XREVIEW), 'firstCrossreviewSha256SumsSha256': sha((XREVIEW / 'SHA256SUMS').read_bytes()),
    'localeBPacket': str(XREVIEW / 'locale-b-by-b'),
    'localeBSha256SumsSha256': sha((XREVIEW / 'locale-b-by-b/SHA256SUMS').read_bytes()),
    'sharedParentWorktreeWasDirty': True, 'liveFilesReadFromExactGitCommitObjects': True,
    'repoOrPrModified': False, 'testsBuildsScansCI': False,
}
writej(OUT / 'input-attestation.json', inputs)
summary = {
    'schemaVersion': 1, 'task': 'Reconcile slskR PR #204 W563–582 locale-B refinements and live Canonical-support conflicts',
    'repository': 'snapetech-org/slskR', 'pullRequest': 204, 'liveHead': LIVE, 'liveTree': TREE,
    'state': 'OPEN/DRAFT', 'localeBReviewSnapshotHead': B_REVIEW_HEAD,
    'uniqueActionRows': len(action_rows), 'recommendedTargetRows': len(decisions),
    'localeBRefinementsAdjudicated': 4, 'canonicalSupportLiveConflictsAdjudicated': 2,
    'overlap': 'The Korean Canonical support row is both a locale-B refinement and a live conflict, so it appears once in the action ledger.',
    'heldCancelAllCellsPreserved': len(hold_rows), 'currentCellsAndTargetHashesReattested': len(action_rows),
    'liveCatalogsReattested': len(B_LOCALES), 'callerPinsReattested': caller_refs,
    'uniqueCallerContextLinesReattested': len(caller_rows), 'candidateHashesRecomputed': True,
    'placeholderMarkupProtectedLiteralFailures': 0, 'nativeSpeakerApproval': False,
    'repositoryChangesMade': False, 'pullRequestChangesMade': False,
    'testsBuildsScansCIReleasesTagsMergesRun': False, 'result': 'pass',
}
writej(OUT / 'summary.json', summary)
readme = f'''# slskR PR #204 W563–582 reconciliation\n\n- Live PR pin: `{LIVE}` / `{TREE}` (OPEN/DRAFT).\n- The action ledger adjudicates four locale-B refinements and two live `Canonical support from` conflicts; Korean is the overlap and appears once. All six locale-B `Cancel{{all}}` rows remain held.\n- Target catalogs and caller excerpts were read from exact Git commit objects. The shared parent worktree was dirty and was not used for file reads.\n- Exact target text and hashes are in `action-ledger.jsonl`; caller line and catalog evidence are in the supporting files.\n- Native-speaker approval is not claimed. No repository or PR edits, tests, builds, scans, CI, releases, tags, or merges were performed.\n'''
(OUT / 'README.md').write_text(readme, encoding='utf-8')
files = sorted(path for path in OUT.iterdir() if path.is_file() and path.name != 'SHA256SUMS')
(OUT / 'SHA256SUMS').write_text(''.join(f'{sha(path.read_bytes())}  {path.name}\n' for path in files), encoding='utf-8')
print(json.dumps({'summary': summary, 'callerRefs': caller_refs, 'uniqueCallerLines': len(caller_rows),
                  'recommendedTargets': [{'sourceId': r['sourceId'], 'locale': r['locale'],
                                          'action': r['recommendedAction'], 'target': r['recommendedTarget'],
                                          'sha256': r['recommendedTargetSha256']}
                                         for r in action_rows if r['recommendedTarget'] is not None]},
                 ensure_ascii=False, indent=2))
