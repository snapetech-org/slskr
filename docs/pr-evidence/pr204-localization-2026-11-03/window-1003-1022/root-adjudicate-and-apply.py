#!/usr/bin/env python3
"""Adjudicate and apply slskR PR #204 localization window W1003-W1022."""
from __future__ import annotations
import hashlib
import json
import shutil
import subprocess
from collections import Counter
from pathlib import Path

WORKTREE = Path('/mnt/disks/scratch/task-worktrees/localization-20261103/slskr-pr204-w983-apply')
PRIMARY = Path('/mnt/disks/scratch/task-scratch/slskr-pr204-w1003-1022-primary-20261103')
BLIND = Path('/mnt/disks/scratch/task-scratch/slskr-pr204-w1003-1022-blind-20261103')
EVIDENCE = WORKTREE / 'docs/pr-evidence/pr204-localization-2026-11-03/window-1003-1022'
EXPECTED_HEAD = '4193d79547018a561e9d5acacdb0ac0850f6f346'
EXPECTED_TREE = 'da7d72c82203781fc14d99e8dd85cc1b30c10164'
REPOS = 'snapetech-org/slskR#204'


def run(*args: str) -> str:
    return subprocess.run(args, check=True, text=True, capture_output=True).stdout.strip()


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def verify_manifest(folder: Path, name: str) -> dict[str, str]:
    verified = {}
    for line in (folder / name).read_text().splitlines():
        if not line.strip():
            continue
        expected, rel = line.split(maxsplit=1)
        rel = rel.strip().lstrip('*')
        actual = sha((folder / rel).read_bytes())
        if actual != expected:
            raise SystemExit(f'checksum mismatch: {folder / rel}')
        verified[rel] = actual
    return verified


def blob_at(rev: str, path: str) -> bytes:
    return subprocess.run(['git', '-C', str(WORKTREE), 'show', f'{rev}:{path}'],
                          check=True, capture_output=True).stdout


def main() -> None:
    head = run('git', '-C', str(WORKTREE), 'rev-parse', 'HEAD')
    tree = run('git', '-C', str(WORKTREE), 'rev-parse', 'HEAD^{tree}')
    if (head, tree) != (EXPECTED_HEAD, EXPECTED_TREE):
        raise SystemExit(f'worktree moved: {head}/{tree}')
    dirty = run('git', '-C', str(WORKTREE), 'status', '--porcelain')
    if dirty:
        raise SystemExit(f'worktree not clean before apply: {dirty}')
    primary_hashes = verify_manifest(PRIMARY, 'SHA256SUMS')
    blind_hashes = verify_manifest(BLIND, 'SHA256SUMS.txt')

    primary = [json.loads(line) for line in (PRIMARY / 'primary-review-ledger.jsonl').read_text().splitlines()]
    blind = [json.loads(line) for line in (BLIND / 'cell-review-ledger.jsonl').read_text().splitlines()]
    if len(primary) != 240 or len(blind) != 240:
        raise SystemExit('expected 240 primary and 240 blind cells')
    blind_by = {(r['ordinal'], r['locale']): r for r in blind}
    if len(blind_by) != 240:
        raise SystemExit('duplicate/missing blind cell key')

    # Re-attest the exact source and current targets for every cell.
    for r in primary:
        k = (r['sourcePosition'], r['locale'])
        b = blind_by.get(k)
        if b is None or b['source'] != r['sourceId'] or b['current_target'] != r['currentTarget']:
            raise SystemExit(f'blind input mismatch: {k}')
        if r['sourceSha256'] != sha(r['sourceId'].encode()) or r['currentTargetSha256'] != sha(r['currentTarget'].encode()):
            raise SystemExit(f'primary source/current hash mismatch: {k}')
        if r['currentTargetSha256'] != sha(b['current_target'].encode()):
            raise SystemExit(f'blind current hash mismatch: {k}')

    # Re-attest the catalog bytes and Git blobs pinned by the primary packet.
    catalog_pins = {}
    for r in primary:
        path = r['catalogPath']
        file_bytes = blob_at(EXPECTED_HEAD, path)
        blob = run('git', '-C', str(WORKTREE), 'rev-parse', f'{EXPECTED_HEAD}:{path}')
        if sha(file_bytes) != r['catalogFileSha256'] or blob != r['catalogGitBlob']:
            raise SystemExit(f'catalog pin mismatch: {path}')
        catalog_pins[path] = {'sha256': sha(file_bytes), 'gitBlob': blob}

    # Re-attest exact production caller file and line pins from source-only input.
    source_rows = [json.loads(line) for line in (PRIMARY / 'source-only-input.jsonl').read_text().splitlines()]
    caller_pins = {}
    for src in source_rows:
        for caller in src.get('callers', []):
            path = caller['file']
            file_bytes = blob_at(EXPECTED_HEAD, path)
            if sha(file_bytes) != caller['fileSha256']:
                raise SystemExit(f'caller file hash mismatch: {path}')
            lines = file_bytes.decode('utf-8').splitlines()
            line_no = caller['line']
            if not (1 <= line_no <= len(lines)):
                raise SystemExit(f'caller line out of range: {path}:{line_no}')
            actual_line = lines[line_no - 1]
            if actual_line.strip() != caller['lineText'] or sha(actual_line.encode()) != caller['lineSha256']:
                raise SystemExit(f'caller line mismatch: {path}:{line_no}')
            caller_pins[f'{path}:{line_no}'] = caller['lineSha256']

    # Root adjudication is exact-hash based. All 22 independent holds are resolved
    # only with source and caller context: 12 remain held; 10 proposals are accepted.
    manual_notes = {
        1007: ('The exact SongID analysis caller describes an album candidate and album acquisition; nearby UI says “Download Album”. '
               'The proposals say one album release/job and avoid the music-single reading. Accept the primary proposals for this source.'),
        1010: ('Hold all locales. The caller concatenates a localized sentence fragment, raw code literal PrivateServiceGateway, '
               'and separately localized suffix; the resulting complete grammar cannot be reliably adjudicated as locale cells alone.'),
        1012: ('The exact caller is in the “Pod Content Linking” feature card and is followed by PodWorkflowNotice. '
               'Pod is the product term; French “modules” is the semantic error. Accept the primary Pod wording.'),
        1019: ('The display callsites are table headers over createdAt timestamps; acquisition-plan results also use Created as a status. '
               'The Arabic, Hindi, and Vietnamese passive-completed forms preserve the shared “Created” label in both contexts.'),
    }
    root_rows = []
    plan = []
    for r in primary:
        b = blind_by[(r['sourcePosition'], r['locale'])]
        pos, locale = r['sourcePosition'], r['locale']
        pdis = r['disposition']
        bdec = b['decision']
        if bdec not in {'pass', 'hold'}:
            raise SystemExit(f'unknown blind decision: {bdec}')
        if bdec == 'hold' and pos not in manual_notes:
            raise SystemExit(f'unadjudicated independent hold: {pos}/{locale}')
        if bdec == 'hold' and pos == 1010:
            root_disposition, final = 'hold', r['currentTarget']
            reason = manual_notes[pos]
        else:
            root_disposition = pdis
            final = r['reviewedFinal'] if pdis in {'correction', 'refinement'} else r['currentTarget']
            reason = manual_notes.get(pos) if bdec == 'hold' else (
                'Independent blind review passed this cell; retain the primary exact-hash disposition.'
                if bdec == 'pass' and pdis != 'accept-current' else
                'Primary and independent blind review both accept the current wording.'
            )
        if root_disposition in {'correction', 'refinement'}:
            if not final or final == r['currentTarget']:
                raise SystemExit(f'non-change adjudication: {pos}/{locale}')
            if not r['proposedPlaceholderParity'] or not r['finalMarkupParity'] or not r['icuParity'] or not r['finalProtectedLiteralsPreserved']:
                raise SystemExit(f'structural guard failed: {pos}/{locale}')
            plan.append({
                'sourcePosition': pos, 'sourceId': r['sourceId'], 'locale': locale,
                'catalogPath': r['catalogPath'], 'expectedCurrentSha256': r['currentTargetSha256'],
                'finalTarget': final, 'finalTargetSha256': sha(final.encode()),
                'rootDisposition': root_disposition, 'primaryDisposition': pdis,
                'blindDecision': bdec, 'rationale': reason,
            })
        else:
            if final != r['currentTarget']:
                raise SystemExit(f'hold/accept-current changed target: {pos}/{locale}')
        root_rows.append({
            **r,
            'independentBlindDecision': bdec,
            'independentBlindRationale': b['rationale'],
            'rootDisposition': root_disposition,
            'rootFinal': final,
            'rootFinalSha256': sha(final.encode()),
            'rootAdjudicationRationale': reason,
            'qualifiedNativeSpeakerApproval': False,
        })

    if Counter(r['rootDisposition'] for r in root_rows) != Counter({'accept-current': 143, 'correction': 39, 'refinement': 46, 'hold': 12}):
        raise SystemExit('root disposition totals differ from adjudicated window')
    if len(plan) != 85:
        raise SystemExit(f'expected 85 approved changes, got {len(plan)}')
    if sum(b['decision'] == 'hold' for b in blind) != 22:
        raise SystemExit('independent hold count changed')

    # Check all mutable cells against original bytes before writing any catalog.
    before = {}
    parsed = {}
    for path, pin in catalog_pins.items():
        file_path = WORKTREE / path
        data = file_path.read_bytes()
        if sha(data) != pin['sha256']:
            raise SystemExit(f'working catalog changed since pin: {path}')
        obj = json.loads(data)
        before[path] = list(obj.keys())
        parsed[path] = obj
    for item in plan:
        obj = parsed[item['catalogPath']]
        old = next(r['currentTarget'] for r in primary if r['sourcePosition'] == item['sourcePosition'] and r['locale'] == item['locale'])
        if obj.get(item['sourceId']) != old:
            raise SystemExit(f'catalog value mismatch before apply: {item["sourcePosition"]}/{item["locale"]}')

    # Retain source packets in the PR and write root evidence before application.
    if EVIDENCE.exists():
        raise SystemExit(f'evidence destination already exists: {EVIDENCE}')
    (EVIDENCE / 'primary').mkdir(parents=True)
    (EVIDENCE / 'independent-review').mkdir()
    shutil.copytree(PRIMARY, EVIDENCE / 'primary', dirs_exist_ok=True)
    shutil.copytree(BLIND, EVIDENCE / 'independent-review', dirs_exist_ok=True)
    with (EVIDENCE / 'root-adjudication.jsonl').open('w', encoding='utf-8', newline='\n') as f:
        for row in root_rows:
            f.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + '\n')
    with (EVIDENCE / 'apply-plan.jsonl').open('w', encoding='utf-8', newline='\n') as f:
        for row in plan:
            f.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + '\n')

    # Apply reviewed exact-hash cell changes, preserving catalog key order.
    for item in plan:
        parsed[item['catalogPath']][item['sourceId']] = item['finalTarget']
    for path, obj in parsed.items():
        if list(obj.keys()) != before[path]:
            raise SystemExit(f'catalog key order changed: {path}')
        (WORKTREE / path).write_text(json.dumps(obj, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

    # Re-read all cells, all 12 ordered key sets, placeholder/literal integrity.
    after_catalogs = {}
    for path in catalog_pins:
        after_catalogs[path] = json.loads((WORKTREE / path).read_text())
        if list(after_catalogs[path].keys()) != before[path]:
            raise SystemExit(f'catalog key order changed after readback: {path}')
    first_keys = next(iter(after_catalogs.values())).keys()
    if any(list(obj.keys()) != list(first_keys) for obj in after_catalogs.values()):
        raise SystemExit('locale catalogs no longer have identical ordered keys')
    if len(first_keys) != 5441:
        raise SystemExit(f'unexpected catalog key count: {len(first_keys)}')
    for row in root_rows:
        path = row['catalogPath']
        actual = after_catalogs[path].get(row['sourceId'])
        if actual != row['rootFinal'] or sha(actual.encode()) != row['rootFinalSha256']:
            raise SystemExit(f'final readback mismatch: {row["sourcePosition"]}/{row["locale"]}')
    for item in plan:
        if after_catalogs[item['catalogPath']][item['sourceId']] != item['finalTarget']:
            raise SystemExit(f'applied target mismatch: {item["sourcePosition"]}/{item["locale"]}')

    readback = {
        'repository': REPOS,
        'baseHead': EXPECTED_HEAD,
        'baseTree': EXPECTED_TREE,
        'window': 'W1003-W1022',
        'reviewedCells': len(root_rows),
        'changedCells': len(plan),
        'unchangedAcceptedOrHeldCells': len(root_rows) - len(plan),
        'rootDispositionCounts': dict(Counter(r['rootDisposition'] for r in root_rows)),
        'blindDecisionCounts': dict(Counter(r['independentBlindDecision'] for r in root_rows)),
        'orderedCatalogKeyCountPerLocale': len(first_keys),
        'localeCount': len(after_catalogs),
        'orderedCatalogKeysSha256': sha(('\n'.join(first_keys) + '\n').encode()),
        'catalogPinsAtBase': catalog_pins,
        'callerFileAndLinePinsVerified': len(caller_pins),
        'blindHoldAdjudications': {
            'accepted': ['1007/de', '1007/id', '1007/ja', '1007/vi', '1007/zh-Hans', '1007/zh-Hant', '1012/fr', '1019/ar', '1019/hi', '1019/vi'],
            'retainedAsHolds': [f'1010/{locale}' for locale in sorted({r['locale'] for r in root_rows if r['sourcePosition'] == 1010})],
        },
        'allFinalCellValuesReadBack': True,
        'placeholderMarkupIcuProtectedLiteralChecks': 'all approved targets passed pinned structural checks',
        'nativeSpeakerApproval': 'not established',
        'readbackCatalogFileSha256': {path: sha((WORKTREE / path).read_bytes()) for path in sorted(after_catalogs)},
    }
    (EVIDENCE / 'apply-readback.json').write_text(json.dumps(readback, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    summary = {
        'repository': REPOS,
        'window': 'W1003-W1022',
        'baseHead': EXPECTED_HEAD,
        'baseTree': EXPECTED_TREE,
        'reviewCounts': {'cells': 240, 'primary': {'accept-current': 143, 'correction': 39, 'refinement': 46, 'hold': 12}, 'independentBlind': {'pass': 218, 'hold': 22}, 'root': dict(Counter(r['rootDisposition'] for r in root_rows))},
        'approvedCatalogChanges': 85,
        'callerlessOrCompositionHold': 'source position 1010 in all 12 locales',
        'primaryPacketSha256': sha((PRIMARY / 'SHA256SUMS').read_bytes()),
        'independentPacketSha256': sha((BLIND / 'SHA256SUMS.txt').read_bytes()),
        'catalogKeyCount': len(first_keys),
        'catalogsHaveIdenticalOrderedKeys': True,
        'nativeSpeakerApproval': 'not established',
        'browserReview': 'current-head browser review remains a separate gate',
        'noTestsBuildsOrCI': True,
    }
    (EVIDENCE / 'root-summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    readme = f'''# slskR PR #204 W1003–W1022 localization review\n\nThe exact review base is `{EXPECTED_HEAD}` with tree `{EXPECTED_TREE}`. The source packet and independent blind packet both verify their checksums and contain the same 240 source/locale cells with matching source and current-target hashes.\n\nPrimary dispositions: 143 accept-current, 39 corrections, 46 refinements, and 12 holds. The independent blind review records 218 passes and 22 holds. Root adjudication accepts ten blind holds based on the pinned caller context and retains twelve holds at source position 1010, where the localized fragment is concatenated around the raw `PrivateServiceGateway` literal and a separately localized suffix.\n\nAt position 1007, the exact caller is the SongID album-candidate flow and the nearby control is “Download Album”; the selected wording means a job for one album release and avoids the music-single reading. At position 1012, the exact caller is in the “Pod Content Linking” feature and uses the product term Pod; French “modules” was corrected. At position 1019, the exact callers show a Created column over `createdAt` values as well as a Created acquisition-plan status; Arabic, Hindi, and Vietnamese passive-completed forms preserve the shared label.\n\nThe 85 accepted changes were applied to the 12 locale JSON catalogs. Each catalog retains its original key order; all 12 catalogs have the same ordered 5,441-key set. Every reviewed cell was read back. Placeholder, markup, ICU, and protected-literal checks passed for approved targets.\n\nPrimary and independent evidence are retained under `primary/` and `independent-review/`. Root dispositions are in `root-adjudication.jsonl`; the exact-hash mutation list is in `apply-plan.jsonl`; readback is in `apply-readback.json`. The `EVIDENCE-SHA256SUMS.txt` manifest covers this evidence tree except itself.\n\nNo qualified native-speaker approval is claimed. This packet does not establish current-head browser acceptance. No tests, builds, CI, workflow edits, merges, releases, or tags were performed.\n'''
    (EVIDENCE / 'README.md').write_text(readme, encoding='utf-8')

    # Copy the exact script into the retained packet and seal all evidence files.
    shutil.copy2(Path(__file__), EVIDENCE / 'root-adjudicate-and-apply.py')
    manifest_lines = []
    for path in sorted(p for p in EVIDENCE.rglob('*') if p.is_file() and p.name != 'EVIDENCE-SHA256SUMS.txt'):
        rel = path.relative_to(EVIDENCE).as_posix()
        manifest_lines.append(f'{sha(path.read_bytes())}  {rel}')
    (EVIDENCE / 'EVIDENCE-SHA256SUMS.txt').write_text('\n'.join(manifest_lines) + '\n', encoding='utf-8')
    print(json.dumps({'evidence': str(EVIDENCE), 'reviewedCells': len(root_rows), 'approvedChanges': len(plan),
                      'rootCounts': dict(Counter(r['rootDisposition'] for r in root_rows)),
                      'blindCounts': dict(Counter(r['independentBlindDecision'] for r in root_rows)),
                      'catalogKeysPerLocale': len(first_keys), 'callerPinsVerified': len(caller_pins),
                      'evidenceFileCount': len(manifest_lines), 'evidenceBytes': sum(p.stat().st_size for p in EVIDENCE.rglob('*') if p.is_file())}, ensure_ascii=False))

if __name__ == '__main__':
    main()
