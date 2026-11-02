from __future__ import annotations
import collections
import hashlib
import json
import re
import subprocess
from pathlib import Path


ROOT = Path('/mnt/disks/scratch/task-scratch/slskr-pr204-W583-602-primary-20261102')
OUT = ROOT / 'packet'
REPO = Path('/mnt/disks/scratch/task-worktrees/localization-20261102/slskr-pr204-w503-522')
AUDIT = Path('/mnt/disks/scratch/task-worktrees/localization-20261030/slskr-populated-catalog-review-7ff45482-20261101')
HEAD = '2f7483fdaa753e22f6d335a03f15db7d1d82b20f'
TREE = '54ee16a812a5bda7871f3ef3ad7ff0cf3bf678e0'
SOURCE = '7ff454828398de6a3cfb72fe7f0ed21fe419425b'
SOURCE_TREE = '9e9f2aa743c4ff3236af8f99619803bdc3a37152'
PR = 204
REPO_NAME = 'snapetech-org/slskR'
BRANCH = 'codex/slskr-l10n-audit-20261030'
LOCALES = ['ar', 'de', 'es', 'fr', 'hi', 'id', 'ja', 'ko', 'pt-BR', 'vi', 'zh-Hans', 'zh-Hant']
WINDOW = range(583, 603)
CATALOG = 'web/src/lib/locales/ui-labels.{locale}.json'

CONTEXT = {
    'Censorship Resistance': 'Security setting label under adversarial settings; describes resistance to censorship in the product’s transport/network behavior.',
    'Centroid': 'SongID acoustic-evidence metric label; the numeric value is spectral centroid, a signal-processing feature rather than an ordinary geometric centroid.',
    'Certificate PFX (optional)': 'Admin Policies certificate-upload field label. PFX is a certificate/key container format; retain the literal acronym.',
    'Certificate Password': 'Admin Policies field label for the password that protects the uploaded certificate/private key.',
    'Certificate Password Missing': 'Admin Policies certificate status string shown when no certificate password is configured.',
    'Certificate Password Set': 'Admin Policies certificate status string shown when a certificate password is configured.',
    'Certificate password': 'Validation/error text for the certificate password field; lowercase source variant is a separate catalog key.',
    'Change Role': 'Button in Pod Membership Management for changing a member’s role.',
    'Changed fields': 'Playlist Intake summary label before the metadata fields changed by an import/update.',
    'Channel "{channelName}" deleted successfully': 'Success toast in Pod Channel Management after a channel is deleted; {channelName} is the runtime channel name.',
    'Channel "{newChannelName}" created successfully': 'Success toast in Pod Channel Management after a channel is created; {newChannelName} is the runtime name.',
    'Channel ID': 'Field label in Quarantine Jury for a pod channel identifier.',
    'Channel ID is required': 'Server validation response for missing channelId; it is included in the app-server error allowlist and is localized by toDisplayError before Pod Channel Management shows API failures.',
    'Channel create, update, and delete actions change how pod messages are organized. Deleting channels can disrupt routing and history workflows.': 'Warning notice above Pod channel-management controls; the app’s named entity Pod is retained in the exact-head locale precedent for “Can create content-linked pods,” and channel operations affect routing/history.',
    'Channel name': 'Input label/placeholder for creating or editing a pod channel name.',
    'Channel name is required': 'Validation toast and server response when a pod-channel name is blank.',
    'Channel updated successfully': 'Success toast after updating a pod channel.',
    'Channel:': 'Inline label in Pod Message Signing details before the channel value.',
    'Channels': 'Shared key used for a Pod Channels label and for the numeric Chromaprint audio-channel setting; Chinese uses distinct terms for these meanings, so assess caller ambiguity before proposing one catalog target.',
    'Chapters': 'SongID evidence label for chapter/segment counts in an audio track’s analysis results.',
}

MANUAL_CALLERS = {
    'Channel "{channelName}" deleted successfully': [('web/src/components/System/MediaCore/PodChannelManagementPanel.jsx', 'channelName', 'handleDeleteChannel')],
    'Channel "{newChannelName}" created successfully': [('web/src/components/System/MediaCore/PodChannelManagementPanel.jsx', 'newChannelName', 'handleCreateChannel')],
}


def run(args, *, raw=False, check=True):
    result = subprocess.run(['git', '-C', str(REPO), *args], capture_output=True, check=check)
    return result.stdout if raw else result.stdout.decode('utf-8').strip()


def sha(value: str | bytes) -> str:
    return hashlib.sha256(value if isinstance(value, bytes) else value.encode('utf-8')).hexdigest()


def canon(value) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode('utf-8')


def source_text(path: str, rev: str = HEAD) -> bytes:
    return run(['show', f'{rev}:{path}'], raw=True)


def write_json(path: Path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def write_jsonl(path: Path, rows):
    path.write_text(''.join(json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(',', ':')) + '\n' for row in rows), encoding='utf-8')


def add_pin(path: str, line_no: int, kind: str, sid: str, pos: int):
    raw = source_text(path)
    lines = raw.decode('utf-8').splitlines()
    assert 1 <= line_no <= len(lines), (path, line_no)
    line = lines[line_no - 1]
    pr_oid = run(['rev-parse', f'{HEAD}:{path}'])
    base_oid = run(['rev-parse', f'{SOURCE}:{path}'], check=False)
    base_raw = source_text(path, SOURCE) if base_oid else b''
    base_lines = base_raw.decode('utf-8').splitlines() if base_raw else []
    return {
        'path': path,
        'line': line_no,
        'kind': kind,
        'lineText': line,
        'previousLine': lines[line_no - 2] if line_no > 1 else '',
        'nextLine': lines[line_no] if line_no < len(lines) else '',
        'lineSha256': sha(line),
        'fileBlob': pr_oid,
        'fileSha256': sha(raw),
        'sourceBaseBlob': base_oid or None,
        'sourceBaseFileSha256': sha(base_raw) if base_raw else None,
        'sourceBaseLineText': base_lines[line_no - 1] if len(base_lines) >= line_no else None,
        'sameLineAtSourceBaseline': bool(len(base_lines) >= line_no and base_lines[line_no - 1] == line),
        'attestedHead': HEAD,
        'attestedTree': TREE,
        'sourceId': sid,
        'sourceIdPosition': pos,
    }


def matches_for(sid: str, pos: int):
    # Exact-source search is bounded to the source/runtime directories and this one key.
    result = subprocess.run(
        ['git', '-C', str(REPO), 'grep', '-n', '-F', sid, HEAD, '--', 'web/src', 'crates/slskr-web/src', 'crates/slskr/src'],
        capture_output=True, text=True,
    )
    seen = set()
    refs = []
    tests = []
    for item in result.stdout.splitlines():
        parts = item.split(':', 3)
        if len(parts) < 4:
            continue
        _, path, line_text, text = parts
        if '/lib/locales/' in path or '/locale/' in path:
            continue
        # Retain exact quoted source literals, not substring matches against
        # identifiers such as podChannels.
        literal_patterns = [r'"' + re.escape(sid) + r'"', r"'" + re.escape(sid) + r"'"]
        if not any(re.search(pattern, text) for pattern in literal_patterns):
            continue
        try:
            line_no = int(line_text)
        except ValueError:
            continue
        key = (path, line_no)
        if key in seen:
            continue
        seen.add(key)
        if '.test.' in path or '/controller_tests/' in path:
            tests.append(add_pin(path, line_no, 'test-reference', sid, pos))
        else:
            refs.append(add_pin(path, line_no, 'source-reference', sid, pos))

    for path, token, function_name in MANUAL_CALLERS.get(sid, []):
        raw = source_text(path)
        lines = raw.decode('utf-8').splitlines()
        for i, line in enumerate(lines):
            if token in line and 'interfaceText' in line and 'toast.success' in line:
                line_no = i + 1
                key = (path, line_no)
                if key not in seen:
                    refs.append(add_pin(path, line_no, 'dynamic-localized-message-call', sid, pos))
                    seen.add(key)
    if sid == 'Channel ID is required':
        support = [
            ('web/src/lib/errors.js', 'interfaceText(output.source)', 'error-localization-helper'),
            ('web/src/components/System/MediaCore/PodChannelManagementPanel.jsx', 'toDisplayError(error_)', 'error-display-caller'),
        ]
        for path, token, kind in support:
            raw = source_text(path)
            for i, line in enumerate(raw.decode('utf-8').splitlines()):
                if token in line:
                    line_no = i + 1
                    key = (path, line_no)
                    if key not in seen:
                        refs.append(add_pin(path, line_no, kind, sid, pos))
                        seen.add(key)
    return refs, tests, result.stdout.splitlines()


def evidence_rows_for_ids(source_ids):
    # Inspect existing PR evidence only for these exact source literals and exact record fields.
    paths = run(['ls-tree', '-r', '--name-only', HEAD, 'docs/pr-evidence', 'docs/localization']).splitlines()
    candidates = [p for p in paths if p.endswith(('.json', '.jsonl'))]
    found = []
    id_set = set(source_ids)
    def walk(value, path, line_no=None):
        if isinstance(value, dict):
            sid = value.get('source_id', value.get('sourceId'))
            locale = value.get('locale')
            has_decision = any(key in value for key in ('review_decision', 'cross_review_disposition', 'disposition', 'status'))
            has_target_pin = any(key in value for key in ('target_sha256', 'targetSha256', 'current_target_sha256', 'currentTargetSha256'))
            if sid in id_set and locale in LOCALES and has_decision and has_target_pin:
                found.append({'path': path, 'line': line_no, 'sourceId': sid, 'locale': locale, 'record': value})
                return
            for child in value.values():
                walk(child, path, line_no)
        elif isinstance(value, list):
            for child in value:
                walk(child, path, line_no)
    for path in candidates:
        raw = run(['show', f'{HEAD}:{path}'], raw=True)
        if path.endswith('.jsonl'):
            for no, line in enumerate(raw.decode('utf-8').splitlines(), 1):
                if not line.strip():
                    continue
                try:
                    row = json.loads(line)
                except json.JSONDecodeError:
                    continue
                walk(row, path, no)
        else:
            try:
                walk(json.loads(raw.decode('utf-8')), path)
            except (UnicodeDecodeError, json.JSONDecodeError):
                continue
    return found


def main():
    assert run(['rev-parse', 'HEAD']) == HEAD
    assert run(['rev-parse', 'HEAD^{tree}']) == TREE
    assert run(['rev-parse', f'{SOURCE}^{{tree}}']) == SOURCE_TREE
    assert run(['merge-base', SOURCE, HEAD]) == SOURCE
    assert not run(['status', '--porcelain'])
    live = json.loads(subprocess.check_output([
        'gh', 'pr', 'view', str(PR), '--repo', REPO_NAME,
        '--json', 'state,isDraft,mergeStateStatus,headRefOid,headRefName,baseRefOid,url',
    ], cwd=REPO, text=True))
    assert live['state'] == 'OPEN' and live['isDraft'] is True and live['headRefOid'] == HEAD, live

    inventory_path = AUDIT / 'frozen-inputs/source-inventory.jsonl'
    inventory_bytes = inventory_path.read_bytes()
    inventory = [json.loads(line) for line in inventory_bytes.decode('utf-8').splitlines() if line.strip()]
    ids = [row['source_id'] for row in inventory]
    source_hashes = {row['source_id']: row['source_sha256'] for row in inventory}
    assert len(ids) == 5437 and len(set(ids)) == 5437
    selected = [(pos, ids[pos]) for pos in WINDOW]
    assert len(selected) == 20
    assert [pos for pos, _ in selected] == list(range(583, 603))
    assert all(source_hashes[sid] == sha(sid) for _, sid in selected)

    locales = {}
    catalog_info = {}
    for locale in LOCALES:
        path = CATALOG.format(locale=locale)
        raw = source_text(path)
        data = json.loads(raw.decode('utf-8'))
        # The branch contains one key outside the pinned 5,437-key source
        # inventory; preserve and account for it explicitly.
        extras = set(data) - set(ids)
        assert set(ids).issubset(data) and extras == {'OK'}, (locale, len(data), sorted(extras))
        locales[locale] = data
        catalog_info[locale] = {
            'path': path,
            'bytes': len(raw),
            'sha256': sha(raw),
            'blobOid': run(['rev-parse', f'{HEAD}:{path}']),
            'keyCount': len(data),
        }

    prior_review_path = 'docs/localization/pr204-translation-review-2026-11-01.jsonl'
    prior_review_raw = source_text(prior_review_path)

    source_contexts = []
    caller_pins = []
    current_cells = []
    review_input = []
    prior_matches = evidence_rows_for_ids([sid for _, sid in selected])
    prior_by_id = collections.defaultdict(list)
    prior_by_cell = collections.defaultdict(list)
    for match in prior_matches:
        prior_by_id[match['sourceId']].append(match)
        prior_by_cell[(match['sourceId'], match['locale'])].append(match)

    for pos, sid in selected:
        refs, tests, raw_matches = matches_for(sid, pos)
        ctx = {
            'schemaVersion': 1,
            'repository': REPO_NAME,
            'pullRequest': PR,
            'sourceBaselineHead': SOURCE,
            'sourceBaselineTree': SOURCE_TREE,
            'attestedHead': HEAD,
            'attestedTree': TREE,
            'sourceIndex': pos,
            'sourceId': sid,
            'sourceSha256': source_hashes[sid],
            'semanticContext': CONTEXT[sid],
            'callerReferences': refs,
            'testReferences': tests,
            'callerStatus': 'found' if refs else 'no-direct-caller-found',
            'existingEvidenceMatches': prior_by_id[sid],
        }
        source_contexts.append(ctx)
        caller_pins.extend(refs)
        caller_pins.extend(tests)
        for locale in LOCALES:
            target = locales[locale][sid]
            target_path = CATALOG.format(locale=locale)
            cell = {
                'sourceIndex': pos,
                'sourceId': sid,
                'sourceSha256': source_hashes[sid],
                'source': sid,
                'locale': locale,
                'targetFile': target_path,
                'targetCatalogBlob': catalog_info[locale]['blobOid'],
                'currentTarget': target,
                'currentTargetSha256': sha(target),
                'placeholdersSource': sorted(set(re.findall(r'\{[^{}]+\}', sid))),
                'placeholdersCurrent': sorted(set(re.findall(r'\{[^{}]+\}', target))),
                'callerReferences': refs,
                'contextNote': CONTEXT[sid],
                'priorEvidenceMatches': prior_by_cell[(sid, locale)],
            }
            current_cells.append(cell)
            review_input.append(cell)

    assert len(current_cells) == 240 and len(review_input) == 240
    assert len({(r['sourceIndex'], r['locale']) for r in current_cells}) == 240
    assert len(source_contexts) == 20
    assert len({(r['path'], r['line'], r['sourceId'], r['kind']) for r in caller_pins}) == len(caller_pins)

    previous = json.loads((Path('/mnt/disks/scratch/task-scratch/slskr-pr204-W563-582-primary-20261102/packet/exact-head.json')).read_text())
    previous_boundary = json.loads((Path('/mnt/disks/scratch/task-scratch/slskr-pr204-W563-582-primary-20261102/packet/boundary-attestation.json')).read_text())
    previous_window = previous_boundary.get('current_window', {}).get('indices')
    assert previous_window == [563, 582], previous_window
    assert previous['live_pr']['headRefOid'] == '7e99edecbdea10580cc5e8d198930a82f076b834'

    OUT.mkdir(parents=True, exist_ok=False)
    ROOT.mkdir(parents=True, exist_ok=True)
    (OUT / 'source-inventory.jsonl').write_bytes(inventory_bytes)
    (OUT / 'freeze-manifest.json').write_bytes((AUDIT / 'freeze-manifest.json').read_bytes())
    (OUT / 'freeze-manifest.sha256').write_bytes((AUDIT / 'freeze-manifest.sha256').read_bytes())
    write_jsonl(OUT / 'source-context.jsonl', source_contexts)
    write_jsonl(OUT / 'caller-context-pins.jsonl', caller_pins)
    write_jsonl(OUT / 'current-cells.jsonl', current_cells)
    write_jsonl(OUT / 'review-input.jsonl', review_input)
    write_jsonl(OUT / 'prior-evidence-matches.jsonl', prior_matches)
    write_jsonl(OUT / 'source-current-attestation.jsonl', [
        {
            'sourceIndex': pos,
            'sourceId': sid,
            'sourceSha256': source_hashes[sid],
            'attestedHead': HEAD,
            'attestedTree': TREE,
            'targets': [
                {
                    'locale': locale,
                    'targetFile': catalog_info[locale]['path'],
                    'targetCatalogBlob': catalog_info[locale]['blobOid'],
                    'targetCatalogSha256': catalog_info[locale]['sha256'],
                    'targetSha256': sha(locales[locale][sid]),
                    'target': locales[locale][sid],
                }
                for locale in LOCALES
            ],
        }
        for pos, sid in selected
    ])

    placeholder_failures = sum(r['placeholdersSource'] != r['placeholdersCurrent'] for r in current_cells)
    assert placeholder_failures == 0
    unique_caller_files = sorted({r['path'] for r in caller_pins})
    manifest = {
        'schemaVersion': 1,
        'repository': REPO_NAME,
        'pullRequest': PR,
        'livePullRequest': live,
        'head': HEAD,
        'tree': TREE,
        'sourceBaselineHead': SOURCE,
        'sourceBaselineTree': SOURCE_TREE,
        'branch': BRANCH,
        'baseRefOid': live['baseRefOid'],
        'sourceInventory': {
            'path': str(inventory_path),
            'sha256': sha(inventory_bytes),
            'keyCount': len(ids),
        },
        'sourceWindow': [583, 602],
        'sourceIds': 20,
        'sourceIdBoundary': {'583': selected[0][1], '602': selected[-1][1]},
        'previousWindow': {'sourceWindow': [563, 582], 'nonOverlapping': True, 'packet': '/mnt/disks/scratch/task-scratch/slskr-pr204-W563-582-primary-20261102/packet'},
        'locales': LOCALES,
        'cells': 240,
        'catalogs': catalog_info,
        'catalogKeysOutsidePinnedSourceInventory': ['OK'],
        'callerReferences': len(caller_pins),
        'uniqueCallerFiles': unique_caller_files,
        'uniqueCallerLines': len({(r['path'], r['line']) for r in caller_pins}),
        'sourceIdsWithNoDirectCallers': [r['sourceId'] for r in source_contexts if r['callerStatus'] != 'found'],
        'priorEvidenceMatches': len(prior_matches),
        'priorReviewFile': {
            'path': prior_review_path,
            'blobOid': run(['rev-parse', f'{HEAD}:{prior_review_path}']),
            'bytes': len(prior_review_raw),
            'sha256': sha(prior_review_raw),
        },
        'placeholderParityFailures': placeholder_failures,
        'nativeSpeakerApproval': False,
    }
    write_json(OUT / 'manifest.json', manifest)
    write_json(OUT / 'verification.json', {
        'exactPrHeadTree': True,
        'livePrHeadMatches': True,
        'sourceBaselineAncestor': True,
        'worktreeClean': True,
        'sourceInventoryReproduced': True,
        'selectedWindowMatches': True,
        'allPinnedSourceKeysPresentInCatalogs': True,
        'catalogExtraKeysAttestedOutsidePinnedInventory': ['OK'],
        'currentCellCount': len(current_cells),
        'sourceRowCount': len(source_contexts),
        'callerPinsReattestedAtHead': True,
        'targetCatalogBlobsReattestedAtHead': True,
        'sourceTargetPlaceholderParityFailures': placeholder_failures,
        'priorEvidenceMatches': len(prior_matches),
        'nativeSpeakerApproval': False,
    })
    print(json.dumps({
        'head': HEAD,
        'tree': TREE,
        'livePr': live,
        'sourceIds': len(source_contexts),
        'cells': len(current_cells),
        'callerReferences': len(caller_pins),
        'callerFiles': len(unique_caller_files),
        'priorEvidenceMatches': len(prior_matches),
        'noDirectCallerIds': manifest['sourceIdsWithNoDirectCallers'],
        'placeholderFailures': placeholder_failures,
    }, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
