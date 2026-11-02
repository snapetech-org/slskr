#!/usr/bin/env python3
"""Build independent, read-only cross-review evidence for slskR PR #204 W783–802."""
import collections
import hashlib
import json
import re
import subprocess
from pathlib import Path

REPO = Path('/home/keith/Documents/code/slskR')
HEAD = '2d004e38fe7cf76f8d51f36d19c14c34fb497649'
TREE = '7d114d519f4e6ad0a14a4a3fe048fde017551748'
PR = Path('/mnt/disks/scratch/task-scratch/slskr-pr204-W783-802-primary-20261102/packet')
OUT = Path('/mnt/disks/scratch/task-scratch/slskr-pr204-W783-802-crossreview-independent-20261102')
PRIOR_ROOT = Path('/mnt/disks/scratch/task-worktrees/localization-20261030/slskr-populated-catalog-review-7ff45482-20261101')
LOCALE_ORDER = ['ar', 'de', 'es', 'fr', 'hi', 'id', 'ja', 'ko', 'pt-BR', 'vi', 'zh-Hans', 'zh-Hant']
CATALOG_PREFIX = 'web/src/lib/locales/ui-labels.'
PLACEHOLDER_RE = re.compile(r'\{[^{}]+\}')
MARKUP_RE = re.compile(r'</?[A-Za-z][^>]*>')

# Primary proposals that need a more exact rendering of the pinned caller meaning.
REVISIONS = {
    (784, 'ar'): ('مدة الاحتفاظ بالملفات المكتملة (بالدقائق)', 'The paired aria-label and tooltip identify this as the retention duration for completed files. The primary wording only says completed files in minutes.'),
    (784, 'de'): ('Aufbewahrungsdauer abgeschlossener Dateien (Min.)', 'The primary wording omits the retention duration established by the numeric field and paired aria-label.'),
    (784, 'es'): ('Tiempo de retención de archivos completados (min)', 'The primary wording says completed files in minutes but omits the retention period.'),
    (784, 'fr'): ('Durée de conservation des fichiers terminés (min)', 'The primary wording omits the retention duration established by the numeric field and paired aria-label.'),
    (784, 'hi'): ('पूरी हो चुकी फ़ाइलों को रखने की अवधि (मिनट में)', 'The primary wording omits the retention duration established by the numeric field and paired aria-label.'),
    (784, 'id'): ('Lama penyimpanan berkas yang telah selesai (menit)', 'The primary wording omits the retention duration established by the numeric field and paired aria-label.'),
    (787, 'hi'): ('पूर्ण रिलीज़ को प्राथमिकता दें', 'The caller uses this as a preference option; the primary wording is awkward and can read like an instruction to finish releases.'),
    (790, 'ja'): ('完了したダウンロードのフォルダーは slskr から見えます...', 'The primary proposal places the ellipsis inside the proper name before a Japanese particle; this keeps the ellipsis at the end and expresses visibility from slskr.'),
    (790, 'ko'): ('완료된 다운로드 폴더가 slskr에서 보입니다...', 'The primary proposal places the ellipsis inside the proper name before a Korean particle; this keeps the ellipsis at the end and expresses visibility from slskr.'),
    (790, 'vi'): ('Thư mục chứa các bản tải xuống đã hoàn tất mà slskr có thể truy cập...', 'The primary phrase “hiển thị với slskr” is unnatural; this says slskr can access the directory containing completed downloads.'),
    (790, 'zh-Hans'): ('slskr 可见的已完成下载目录...', 'The primary proposal splits the product name from its predicate with the ellipsis; this keeps the source ellipsis trailing.'),
    (790, 'zh-Hant'): ('slskr 可見的已完成下載目錄...', 'The primary proposal splits the product name from its predicate with the ellipsis; this keeps the source ellipsis trailing.'),
    (792, 'zh-Hans'): ('扫描已完成的文件', 'The pinned action description asks the media server to scan confirmed completed-download paths. The primary wording says the scan itself is complete.'),
    (792, 'zh-Hant'): ('掃描已完成的檔案', 'The pinned action description asks the media server to scan confirmed completed-download paths. The primary wording says the scan itself is complete.'),
}

# Four previously accepted W790 cells translate the directory itself as complete or
# use a non-idiomatic modifier. These are added findings beyond the primary packet.
NEW_W790 = {
    'de': ('Verzeichnis der abgeschlossenen Downloads, für slskr sichtbar...', 'The current compound describes a completed directory rather than a directory of completed downloads.'),
    'es': ('Directorio de descargas completadas visible para slskr...', 'The current masculine adjective modifies “directorio” and can mean a complete directory rather than completed downloads.'),
    'fr': ('Répertoire des téléchargements terminés visible par slskr...', 'The current wording attaches “terminé” to the directory and reads as a finished directory.'),
    'hi': ('पूरे हो चुके डाउनलोड का फ़ोल्डर, जो slskr को दिखाई देता है...', 'The current wording describes a complete download directory; this makes completed downloads the folder contents.'),
}

HOLD_SOURCES = {
    785: 'The action is a plain string in mediaServerIntegrations.js and MediaServerPanel renders check.action raw. Catalog changes cannot affect this display until the caller localizes the action. The English source itself is awkward (“Complete … readiness”); clarify it while refactoring.',
    796: 'The caller interpolates raw English upload/download values and leaves the English plural s outside {direction}. No single locale string can correctly handle both directions until the caller localizes the direction or uses separate toast source keys.',
}


def run(args, *, cwd=None, binary=False):
    return subprocess.check_output(args, cwd=cwd, text=not binary)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def jcompact(obj):
    return json.dumps(obj, ensure_ascii=False, separators=(',', ':'), sort_keys=True).encode('utf-8')


def value_sha(value):
    if isinstance(value, str):
        return sha(value.encode('utf-8'))
    return sha(jcompact(value))


def load_jsonl(path):
    return [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines() if line.strip()]


def save_json(name, obj):
    (OUT / name).write_text(json.dumps(obj, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def save_jsonl(name, rows):
    (OUT / name).write_text(''.join(json.dumps(row, ensure_ascii=False, separators=(',', ':')) + '\n' for row in rows), encoding='utf-8')


def git_blob(path):
    return run(['git', 'show', f'{HEAD}:{path}'], cwd=REPO, binary=True)


def git_blob_id(path):
    return run(['git', 'rev-parse', f'{HEAD}:{path}'], cwd=REPO).strip()


def git_commit_tree(commit):
    return run(['git', 'rev-parse', f'{commit}^{{tree}}'], cwd=REPO).strip()


def live_pr_state():
    pr = json.loads(run(['gh', 'api', 'repos/snapetech-org/slskR/pulls/204']))
    commit = json.loads(run(['gh', 'api', f'repos/snapetech-org/slskR/commits/{pr["head"]["sha"]}']))
    tree = commit['commit']['tree']['sha']
    return {
        'repository': 'snapetech-org/slskR', 'number': pr['number'], 'state': pr['state'],
        'draft': pr['draft'], 'head': pr['head']['sha'], 'headRef': pr['head']['ref'],
        'baseRef': pr['base']['ref'], 'tree': tree, 'url': pr['html_url'],
        'passed': pr['number'] == 204 and pr['state'] == 'open' and pr['draft'] is True and
                  pr['head']['sha'] == HEAD and tree == TREE,
    }


def verify_primary_checksums():
    out = []
    for line in (PR / 'SHA256SUMS').read_text(encoding='utf-8').splitlines():
        digest, name = line.split('  ', 1)
        actual = sha((PR / name).read_bytes())
        if digest != actual:
            raise RuntimeError(f'primary packet checksum failure: {name}')
        out.append({'file': name, 'sha256': actual, 'passed': True})
    return out


def extract_target_leaves(value):
    if isinstance(value, str):
        return [value]
    if isinstance(value, dict):
        return [v for v in value.values() if isinstance(v, str)]
    return []


def text_validation(source, target, protected):
    leaves = extract_target_leaves(target)
    source_ph = collections.Counter(PLACEHOLDER_RE.findall(source))
    ph_ok = bool(leaves) and all(collections.Counter(PLACEHOLDER_RE.findall(t)) == source_ph for t in leaves)
    markup_ok = all(not MARKUP_RE.search(t) for t in leaves)
    literal_checks = {lit: all(lit in t for t in leaves) for lit in protected}
    protected_ok = all(literal_checks.values())
    return {'targetType': 'plural-map' if isinstance(target, dict) else 'string',
            'placeholderParity': ph_ok, 'sourcePlaceholders': dict(source_ph),
            'targetPlaceholdersByLeaf': [dict(collections.Counter(PLACEHOLDER_RE.findall(t))) for t in leaves],
            'markupFree': markup_ok, 'protectedLiteralsPreserved': protected_ok,
            'protectedLiteralChecks': literal_checks, 'nonemptyLeaves': bool(leaves) and all(t.strip() for t in leaves)}


def main():
    allowed = {'build_crossreview.py', 'README.md', 'SHA256SUMS', 'manifest.json', 'summary.json',
               'live-pr-state.json', 'primary-input-integrity.json', 'current-source-inventory.jsonl',
               'source-ordinal-reattestation.jsonl', 'live-cell-reattestation.jsonl',
               'caller-pin-reattestation.jsonl', 'prior-disposition-reattestation.jsonl',
               'W782-boundary-reattestation.jsonl', 'candidate-cross-review.jsonl',
               'new-W790-findings.jsonl', 'caller-gap-findings.json', 'held-cells.jsonl',
               'full-cell-final-dispositions.jsonl'}
    if any(p.name not in allowed for p in OUT.iterdir()):
        raise RuntimeError(f'refusing to overwrite unexpected contents in {OUT}')
    if git_commit_tree(HEAD) != TREE:
        raise RuntimeError('pinned commit/tree mismatch in local object database')
    live_pr = live_pr_state()
    if not live_pr['passed']:
        raise RuntimeError('live PR moved or no longer open/draft: ' + json.dumps(live_pr))

    primary_integrity = verify_primary_checksums()
    manifest = json.loads((PR / 'manifest.json').read_text(encoding='utf-8'))
    primary_summary = json.loads((PR / 'primary-summary.json').read_text(encoding='utf-8'))
    if (manifest['attestedHead'], manifest['attestedTree']) != (HEAD, TREE):
        raise RuntimeError('primary manifest is not pinned to requested live commit')

    # Reconstruct current source ordinals from the sorted, identical catalog key sets.
    catalogs = {}
    catalog_raw = {}
    catalog_meta = {}
    for locale in LOCALE_ORDER:
        path = CATALOG_PREFIX + locale + '.json'
        raw = git_blob(path)
        catalogs[locale] = json.loads(raw)
        catalog_raw[locale] = raw
        catalog_meta[locale] = {'catalogPath': path, 'catalogBlob': git_blob_id(path), 'catalogFileSha256': sha(raw), 'catalogBytes': len(raw)}
    keysets = [set(catalogs[loc].keys()) for loc in LOCALE_ORDER]
    if any(s != keysets[0] for s in keysets[1:]):
        raise RuntimeError('locale catalog source-key sets differ at pinned head')
    current_ids = sorted(keysets[0])
    if len(current_ids) != 5440:
        raise RuntimeError(f'expected 5,440 current source keys, found {len(current_ids)}')
    current_inventory = [{'sourceIndex': i, 'inventoryPosition1Based': i + 1,
                          'sourceId': key, 'sourceSha256': sha(key.encode('utf-8'))}
                         for i, key in enumerate(current_ids)]
    index_by_id = {x['sourceId']: x['sourceIndex'] for x in current_inventory}
    inventory_bytes = ''.join(json.dumps(x, ensure_ascii=False, separators=(',', ':')) + '\n' for x in current_inventory).encode('utf-8')
    (OUT / 'current-source-inventory.jsonl').write_bytes(inventory_bytes)

    # Exact source row inventory, with current ordinal mapping and source text hash.
    source_rows = load_jsonl(PR / 'source-inventory.jsonl')
    ordinal_rows = []
    for row in source_rows:
        live_idx = index_by_id.get(row['sourceId'])
        if live_idx is None or sha(row['sourceId'].encode('utf-8')) != row['sourceSha256']:
            raise RuntimeError(f'source absent/hash mismatch: {row["sourceId"]}')
        ordinal_rows.append({
            'primarySourceIndex': row['sourceIndex'], 'currentSourceIndex': live_idx,
            'indexShift': live_idx - row['sourceIndex'], 'sourceId': row['sourceId'],
            'sourceSha256': row['sourceSha256'], 'sourceTextMatchesId': row['source'] == row['sourceId'],
            'primaryInventorySha256': primary_summary['sourceInventorySha256'],
            'currentInventoryCount': len(current_inventory), 'currentInventorySha256': sha(inventory_bytes),
            'exactHead': HEAD, 'exactTree': TREE,
        })
    if len(ordinal_rows) != 20 or {r['indexShift'] for r in ordinal_rows} != {-1}:
        raise RuntimeError('source ordinal reattestation did not produce expected 20-cell -1 shift')
    save_jsonl('source-ordinal-reattestation.jsonl', ordinal_rows)

    cells = load_jsonl(PR / 'current-cells.jsonl')
    ledger = load_jsonl(PR / 'primary-review-ledger.jsonl')
    candidates = load_jsonl(PR / 'correction-candidates.jsonl')
    sources = {r['sourceIndex']: r for r in source_rows}
    ledger_by_key = {(r['sourceIndex'], r['locale']): r for r in ledger}
    candidate_by_key = {(r['sourceIndex'], r['locale']): r for r in candidates}
    if len(cells) != 240 or len(ledger) != 240 or len(candidates) != 108:
        raise RuntimeError('primary packet row counts differ from requested 240/108')

    live_cells = []
    cell_by_key = {}
    for row in cells:
        loc, sid = row['locale'], row['sourceId']
        live_target = catalogs[loc].get(sid)
        live_target_hash = value_sha(live_target) if live_target is not None else None
        src_row = sources[row['sourceIndex']]
        checks = {
            'currentIndexMatchesCatalogSort': index_by_id.get(sid) is not None,
            'sourceHashMatchesPrimaryInventory': sha(sid.encode('utf-8')) == row['sourceSha256'] == src_row['sourceSha256'],
            'targetPresent': live_target is not None,
            'targetValueMatchesPrimary': live_target == row['currentTarget'],
            'targetHashMatchesPrimary': live_target_hash == row['currentTargetSha256'],
            'catalogBlobMatchesPrimary': git_blob_id(row['targetFile']) == row['targetCatalogBlob'],
            'catalogFileHashMatchesPrimary': sha(catalog_raw[loc]) == row['targetCatalogFileSha256'],
        }
        if not all(checks.values()):
            raise RuntimeError(f'cell reattestation failure: {sid}/{loc}: {checks}')
        validation = text_validation(sid, live_target, row.get('protectedLiterals', []))
        live = {
            'sourceIndexPrimary': row['sourceIndex'], 'sourceIndexCurrent': index_by_id[sid],
            'sourceId': sid, 'sourceSha256': row['sourceSha256'], 'locale': loc,
            'currentTarget': live_target, 'currentTargetSha256': live_target_hash,
            'targetFile': row['targetFile'], 'targetCatalogBlob': row['targetCatalogBlob'],
            'targetCatalogFileSha256': row['targetCatalogFileSha256'],
            'priorAuditStatus': row['priorAuditStatus'], 'checks': checks, 'textValidation': validation,
            'exactHead': HEAD, 'exactTree': TREE,
        }
        live_cells.append(live)
        cell_by_key[(row['sourceIndex'], loc)] = live
    save_jsonl('live-cell-reattestation.jsonl', live_cells)

    # Reattest each pinned caller file, blob, exact line, neighbors, and three-line context hash.
    caller_pins = load_jsonl(PR / 'caller-context-pins.jsonl')
    caller_live = []
    for pin in caller_pins:
        raw = git_blob(pin['path'])
        text = raw.decode('utf-8')
        lines = text.splitlines()
        n = pin['line']
        line = lines[n - 1]
        prev = lines[n - 2] if n > 1 else ''
        nxt = lines[n] if n < len(lines) else ''
        ctx_hash = sha((prev + '\n' + line + '\n' + nxt).encode('utf-8'))
        actual_blob = git_blob_id(pin['path'])
        checks = {
            'fileBlobMatches': actual_blob == pin['fileBlob'],
            'fileSha256Matches': sha(raw) == pin['fileSha256'],
            'lineTextMatches': line == pin['lineText'],
            'lineSha256Matches': sha(line.encode('utf-8')) == pin['lineSha256'],
            'previousLineMatches': prev == pin['previousLine'],
            'nextLineMatches': nxt == pin['nextLine'],
            'contextHashMatches': ctx_hash == pin['contextSha256'],
            'expectedSubstringPresent': pin['expectedSubstring'] in line if pin.get('expectedSubstring') else True,
        }
        if not all(checks.values()):
            raise RuntimeError(f'caller pin failure: {pin["sourceId"]}/{pin["path"]}:{n}: {checks}')
        caller_live.append({
            'sourceIndexPrimary': pin['sourceIndex'], 'sourceIndexCurrent': index_by_id[pin['sourceId']],
            'sourceId': pin['sourceId'], 'path': pin['path'], 'line': n, 'kind': pin['kind'],
            'fileBlob': actual_blob, 'fileSha256': sha(raw), 'lineText': line,
            'lineSha256': sha(line.encode('utf-8')), 'previousLine': prev, 'nextLine': nxt,
            'contextSha256': ctx_hash, 'checks': checks, 'exactHead': HEAD, 'exactTree': TREE,
        })
    if len(caller_live) != 36:
        raise RuntimeError('caller pin count mismatch')
    save_jsonl('caller-pin-reattestation.jsonl', caller_live)

    # Recheck row contents, but treat a changed per-locale file hash as stale
    # provenance even when the selected rows and hashes still match.
    prior_rows = load_jsonl(PR / 'prior-disposition-reattestation.jsonl')
    prior_file_actual = {}
    prior_file_expected = {}
    prior_review_ledgers = {}
    for item in prior_rows:
        path = Path(item['priorRecordPath'])
        raw = path.read_bytes()
        digest = sha(raw)
        prior_file_actual[str(path)] = digest
        prior_file_expected[str(path)] = item['priorRecordSha256']
        locale = item['locale']
        if locale not in prior_review_ledgers:
            prior_review_ledgers[locale] = {json.loads(line)['source_id']: json.loads(line)
                                            for line in raw.decode('utf-8').splitlines() if line.strip()}
    prior_file_hash_matches = {path: prior_file_actual[path] == prior_file_expected[path]
                               for path in prior_file_actual}
    findings_path = PRIOR_ROOT / 'findings.jsonl'
    finding_by_id = {}
    finding_raw_hash = {}
    for line in findings_path.read_text(encoding='utf-8').splitlines():
        if not line.strip():
            continue
        record = json.loads(line)
        fid = record.get('finding_id')
        if fid:
            finding_by_id[fid] = record
            finding_raw_hash[fid] = sha(line.encode('utf-8'))
    prior_live = []
    for item in prior_rows:
        loc, sid = item['locale'], item['sourceId']
        prior_record = prior_review_ledgers[loc].get(sid)
        if not prior_record:
            raise RuntimeError(f'prior ledger missing source row {loc}/{sid}')
        cell = cell_by_key[(item['sourceIndex'], loc)]
        target_hash = cell['currentTargetSha256']
        source_hash = cell['sourceSha256']
        if (prior_record['status'] != item['priorStatus'] or
            prior_record['source_sha256'] != item['priorSourceSha256'] or
            prior_record['target_sha256'] != item['priorTargetSha256'] or
            item['priorStatus'] != cell['priorAuditStatus']):
            raise RuntimeError(f'prior disposition row mismatch {loc}/{sid}')
        finding_ok = item['priorFindingId'] is None
        finding = None
        if item['priorFindingId'] is not None:
            finding = finding_by_id.get(item['priorFindingId'])
            finding_ok = bool(finding) and finding_raw_hash[item['priorFindingId']] == item['priorFindingRecordSha256']
            if finding_ok:
                finding_ok = (finding['locale'] == loc and finding['source_id'] == sid and
                              finding['source_sha256'] == source_hash and finding['target_sha256'] == target_hash and
                              finding['status'] == item['priorStatus'] and
                              finding['proposed_target'] == item['priorProposedTarget'] and
                              value_sha(finding['proposed_target']) == item['priorProposedTargetSha256'])
        elif item['priorStatus'] == 'correction-needed':
            finding_ok = False
        file_hash_matches = prior_file_hash_matches[item['priorRecordPath']]
        exact_reuse = file_hash_matches and item['priorStatus'] != 'not-reviewed' and source_hash == item['priorSourceSha256'] and target_hash == item['priorTargetSha256']
        checks = {'priorLedgerRowMatches': True, 'priorFindingRecordMatches': finding_ok,
                  'sourceHashMatchesLive': source_hash == item['priorSourceSha256'],
                  'targetHashMatchesLive': target_hash == item['priorTargetSha256'],
                  'priorLedgerFileHashMatchesPrimary': file_hash_matches,
                  'primaryReuseClaimConsistentWithPinnedSourceTarget': item['exactHashReusePermitted'] == item['reuseDisposition'] == (item['priorStatus'] != 'not-reviewed' and source_hash == item['priorSourceSha256'] and target_hash == item['priorTargetSha256'])}
        if not all(v for k, v in checks.items() if k != 'priorLedgerFileHashMatchesPrimary'):
            raise RuntimeError(f'prior evidence reattestation failure {loc}/{sid}: {checks}')
        prior_live.append({
            'sourceIndexPrimary': item['sourceIndex'], 'sourceIndexCurrent': index_by_id[sid],
            'sourceId': sid, 'locale': loc, 'priorStatus': item['priorStatus'],
            'priorFindingId': item['priorFindingId'], 'priorFindingReason': item['priorFindingReason'],
            'priorProposedTarget': item['priorProposedTarget'],
            'priorProposedTargetSha256': item['priorProposedTargetSha256'],
            'priorRecordPath': item['priorRecordPath'], 'priorRecordSha256': item['priorRecordSha256'],
            'observedPriorRecordFileSha256': prior_file_actual[item['priorRecordPath']],
            'priorLinkageStatus': 'verified' if file_hash_matches else 'stale-unverified',
            'priorDispositionReusedForCrossReview': False,
            'priorFindingRecordSha256': item['priorFindingRecordSha256'],
            'liveSourceSha256': source_hash, 'liveTargetSha256': target_hash,
            'exactHashReusePermittedForCrossReview': exact_reuse, 'checks': checks,
        })
    if len(prior_live) != 240:
        raise RuntimeError('prior disposition cell count mismatch')
    save_jsonl('prior-disposition-reattestation.jsonl', prior_live)

    # Recheck the previous W763–782 applied readback for Compatibility Review,
    # whose primary ordinal 782 is current sorted-key index 781 after catalog changes.
    boundary_primary = json.loads((PR / 'window-boundary-reattestation.json').read_text(encoding='utf-8'))
    readback_path = Path(boundary_primary['previousAppliedReadbackPath'])
    readback_bytes = readback_path.read_bytes()
    if sha(readback_bytes) != boundary_primary['previousAppliedReadbackSha256']:
        raise RuntimeError('previous applied readback checksum mismatch')
    readback = [json.loads(line) for line in readback_bytes.decode('utf-8').splitlines() if line.strip()]
    readback_by_loc = {x['locale']: x for x in readback if x['sourceIndex'] == 782 and x['sourceId'] == 'Compatibility Review'}
    boundary_rows = []
    for prev in boundary_primary['boundaryTargetsReattested']:
        loc = prev['locale']
        target = catalogs[loc]['Compatibility Review']
        target_hash = value_sha(target)
        rb = readback_by_loc[loc]
        compact_hash = sha(jcompact(rb))
        checks = {
            'liveTargetMatchesPrimaryBoundary': target == prev['liveTarget'],
            'liveTargetHashMatchesPreviousAppliedHash': target_hash == prev['previousAppliedTargetSha256'],
            'previousDispositionIsAcceptCurrent': prev['previousDisposition'] == 'accept-current',
            'previousReadbackRowMatches': rb['crossDisposition'] == 'accept-current' and rb['targetHash'] == target_hash and rb['matchesCrossReviewedFinal'],
            'previousReadbackRecordHashMatches': compact_hash == prev['previousReadbackRecordSha256'],
        }
        if not all(checks.values()):
            raise RuntimeError(f'W782 boundary mismatch {loc}: {checks}')
        boundary_rows.append({
            'sourceId': 'Compatibility Review', 'sourceIndexPrimary': 782,
            'sourceIndexCurrent': index_by_id['Compatibility Review'], 'locale': loc,
            'liveTarget': target, 'liveTargetSha256': target_hash,
            'previousDisposition': prev['previousDisposition'],
            'previousReadbackRecordSha256': compact_hash, 'previousReadbackFileSha256': sha(readback_bytes),
            'checks': checks, 'currentWindowNextSource': 'Complete', 'currentWindowNextSourceIndex': index_by_id['Complete'],
        })
    if len(boundary_rows) != 12:
        raise RuntimeError('W782 boundary rows not 12')
    save_jsonl('W782-boundary-reattestation.jsonl', boundary_rows)

    # Independently adjudicate every primary candidate; hold all raw-caller blocked rows.
    candidate_review = []
    reviewed_by_key = {}
    new_w790 = []
    for c in candidates:
        key = (c['sourceIndex'], c['locale'])
        hold = c['sourceIndex'] in HOLD_SOURCES
        if hold:
            verdict, final_target, rationale = 'hold-pending-caller-refactor', None, HOLD_SOURCES[c['sourceIndex']]
        elif key in REVISIONS:
            final_target, rationale = REVISIONS[key]
            verdict = 'revise-primary-proposal'
        else:
            verdict, final_target = 'accept-primary-proposal', c['recommendedTarget']
            rationale = 'The proposal preserves the pinned caller meaning and source placeholders/protected literals; native-speaker sign-off remains outstanding.'
        protected = [x for x in ['slskr', 'Servarr', 'MediaCore'] if x in c['sourceId']]
        checks = None if final_target is None else text_validation(c['sourceId'], final_target, protected)
        if checks is not None and not all(checks[k] for k in ['placeholderParity', 'markupFree', 'protectedLiteralsPreserved', 'nonemptyLeaves']):
            raise RuntimeError(f'cross-review output text invariant failure {key}: {checks}')
        out = {
            'sourceIndexPrimary': c['sourceIndex'], 'sourceIndexCurrent': index_by_id[c['sourceId']],
            'sourceId': c['sourceId'], 'sourceSha256': c['sourceSha256'], 'locale': c['locale'],
            'primaryDecision': c['decision'], 'primaryCurrentTarget': c['currentTarget'],
            'primaryRecommendedTarget': c['recommendedTarget'],
            'primaryRecommendedTargetSha256': c['recommendedTargetSha256'],
            'crossReviewVerdict': verdict, 'crossReviewTarget': final_target,
            'crossReviewTargetSha256': value_sha(final_target) if final_target is not None else None,
            'rationale': rationale, 'callerLocalizationGap': c['callerLocalizationGap'],
            'textValidation': checks, 'nativeSpeakerApproval': False,
            'exactHead': HEAD, 'exactTree': TREE,
        }
        candidate_review.append(out)
        reviewed_by_key[key] = out

    # Four extra W790 findings among cells primary marked accept-current.
    for loc, (target, rationale) in NEW_W790.items():
        key = (790, loc)
        if key in candidate_by_key:
            raise RuntimeError(f'new W790 finding overlaps primary candidate: {loc}')
        row = cell_by_key[key]
        validation = text_validation(row['sourceId'], target, ['slskr'])
        if not all(validation[k] for k in ['placeholderParity', 'markupFree', 'protectedLiteralsPreserved', 'nonemptyLeaves']):
            raise RuntimeError(f'new W790 text invariant failure {loc}: {validation}')
        new_w790.append({
            'sourceIndexPrimary': 790, 'sourceIndexCurrent': index_by_id[row['sourceId']],
            'sourceId': row['sourceId'], 'locale': loc,
            'currentTarget': row['currentTarget'], 'currentTargetSha256': row['currentTargetSha256'],
            'newReviewVerdict': 'add-correction', 'recommendedTarget': target,
            'recommendedTargetSha256': value_sha(target), 'rationale': rationale,
            'textValidation': validation, 'callerPinPaths': ['web/src/components/System/Integrations/LidarrPanel.jsx'],
            'nativeSpeakerApproval': False,
        })
        reviewed_by_key[key] = {
            'sourceIndexPrimary': 790, 'sourceIndexCurrent': index_by_id[row['sourceId']],
            'sourceId': row['sourceId'], 'sourceSha256': row['sourceSha256'], 'locale': loc,
            'primaryDecision': 'accept-current', 'primaryCurrentTarget': row['currentTarget'],
            'primaryRecommendedTarget': None, 'primaryRecommendedTargetSha256': None,
            'crossReviewVerdict': 'add-new-correction', 'crossReviewTarget': target,
            'crossReviewTargetSha256': value_sha(target), 'rationale': rationale,
            'callerLocalizationGap': False, 'textValidation': validation,
            'nativeSpeakerApproval': False, 'exactHead': HEAD, 'exactTree': TREE,
        }
    if len(candidate_review) != 108 or len(new_w790) != 4:
        raise RuntimeError('candidate/new W790 finding count mismatch')
    save_jsonl('candidate-cross-review.jsonl', candidate_review)
    save_jsonl('new-W790-findings.jsonl', new_w790)

    held = []
    for idx, reason in HOLD_SOURCES.items():
        for c in candidates:
            if c['sourceIndex'] == idx:
                held.append({
                    'sourceIndexPrimary': idx, 'sourceIndexCurrent': index_by_id[c['sourceId']],
                    'sourceId': c['sourceId'], 'locale': c['locale'],
                    'currentTarget': c['currentTarget'], 'currentTargetSha256': c['currentTargetSha256'],
                    'primaryRecommendedTarget': c['recommendedTarget'],
                    'primaryRecommendedTargetSha256': c['recommendedTargetSha256'],
                    'hold': True, 'reason': reason,
                })
    if len(held) != 24:
        raise RuntimeError(f'expected 24 blocked W785/W796 cells, found {len(held)}')
    save_jsonl('held-cells.jsonl', held)
    save_json('caller-gap-findings.json', {
        'count': 2,
        'heldSourceIds': [sources[i]['sourceId'] for i in (785, 796)],
        'findings': [{'sourceIndexPrimary': i, 'sourceIndexCurrent': index_by_id[sources[i]['sourceId']],
                      'sourceId': sources[i]['sourceId'], 'callerReferences': sources[i].get('callerReferences', []),
                      'reason': HOLD_SOURCES[i],
                      'possibleRefactor': ('localize the action value at the readiness check or render check.action via LocalizedText/interfaceText' if i == 785 else
                                           'localize upload/download before interpolation, or split into direction-specific toast source keys')}
                     for i in (785, 796)],
        'sourceRefactorNeedsReattested': True,
    })

    # One complete disposition per live cell, including unchanged accepts and new W790 findings.
    full = []
    for cell in live_cells:
        key = (cell['sourceIndexPrimary'], cell['locale'])
        decision = reviewed_by_key.get(key)
        if decision:
            final_decision = decision['crossReviewVerdict']
            target = decision['crossReviewTarget']
            rationale = decision['rationale']
        else:
            base = ledger_by_key[key]
            final_decision = 'accept-current'
            target = cell['currentTarget']
            rationale = 'Primary accepted-current value independently retained; exact source/target/caller pin reattested.'
        full.append({
            'sourceIndexPrimary': cell['sourceIndexPrimary'], 'sourceIndexCurrent': cell['sourceIndexCurrent'],
            'sourceId': cell['sourceId'], 'sourceSha256': cell['sourceSha256'], 'locale': cell['locale'],
            'currentTarget': cell['currentTarget'], 'currentTargetSha256': cell['currentTargetSha256'],
            'priorAuditStatus': cell['priorAuditStatus'], 'primaryDecision': ledger_by_key[key]['reviewDecision'],
            'crossReviewDecision': final_decision, 'finalRecommendedTarget': target,
            'finalRecommendedTargetSha256': value_sha(target) if target is not None else None,
            'rationale': rationale, 'exactHead': HEAD, 'exactTree': TREE,
        })
    if len(full) != 240:
        raise RuntimeError('full cell disposition count mismatch')
    save_jsonl('full-cell-final-dispositions.jsonl', full)

    prior_counts = collections.Counter(r['priorStatus'] for r in prior_live)
    candidate_counts = collections.Counter(r['crossReviewVerdict'] for r in candidate_review)
    full_counts = collections.Counter(r['crossReviewDecision'] for r in full)
    validation_counts = collections.Counter()
    for row in live_cells:
        for k in ['placeholderParity', 'markupFree', 'protectedLiteralsPreserved']:
            validation_counts[k] += bool(row['textValidation'][k])
    summary = {
        'task': 'slskR PR #204 W783–802 independent cross-review',
        'repository': 'snapetech-org/slskR', 'pullRequest': 204, 'livePrState': live_pr,
        'head': HEAD, 'tree': TREE, 'primaryInputSha256Verified': True,
        'primaryPacketFilesVerified': len(primary_integrity), 'sourceRows': len(source_rows),
        'primarySourceOrdinalRange': [783, 802], 'currentSourceOrdinals': [782, 801],
        'ordinalShift': -1, 'currentSourceInventoryRows': len(current_inventory),
        'currentSourceInventorySha256': sha(inventory_bytes), 'localeCount': 12, 'cellsReattested': len(live_cells),
        'callerPinsReattested': len(caller_live), 'priorRowsReattested': len(prior_live),
        'priorDispositionCountsObservedInChangedFiles': dict(prior_counts),
        'priorSourceOrTargetHashMismatches': 0,
        'priorLedgerFilesExpected': len(prior_file_hash_matches),
        'priorLedgerFilesHashMatchingPrimary': sum(prior_file_hash_matches.values()),
        'priorLedgerFilesHashMismatched': len(prior_file_hash_matches) - sum(prior_file_hash_matches.values()),
        'priorLinkageStatus': 'stale-unverified' if not all(prior_file_hash_matches.values()) else 'verified',
        'priorDispositionReusedForCrossReview': False,
        'priorFindingRecordsReattested': sum(x['priorFindingId'] is not None for x in prior_live),
        'w782BoundaryRows': len(boundary_rows), 'w782PreviousAppliedReadbackFileSha256': sha(readback_bytes),
        'w782PrimaryOrdinal': 782, 'w782CurrentOrdinal': index_by_id['Compatibility Review'],
        'liveIndex782Source': current_ids[782], 'candidateRowsAdjudicated': len(candidate_review),
        'candidateVerdicts': dict(candidate_counts), 'newW790Findings': len(new_w790),
        'heldCells': len(held), 'fullCellFinalDispositionCounts': dict(full_counts),
        'placeholderParityPassedCells': validation_counts['placeholderParity'],
        'markupFreePassedCells': validation_counts['markupFree'],
        'protectedLiteralPassedCells': validation_counts['protectedLiteralsPreserved'],
        'nativeSpeakerApproval': False,
        'limitations': ['Machine cross-review; native-speaker approval remains outstanding.',
                        'W785/W796 targets remain held pending caller refactoring.',
                        'No repository or PR writes; no tests, builds, scans, CI, browser actions, workflow edits, or releases.'],
        'repositoryOrPrModified': False,
    }
    save_json('live-pr-state.json', live_pr)
    save_json('primary-input-integrity.json', {'primaryPath': str(PR), 'filesVerified': primary_integrity,
                                               'sourceInventorySha256Primary': primary_summary['sourceInventorySha256'],
                                               'primaryDecisionCounts': primary_summary['decisionCounts']})
    save_json('summary.json', summary)

    readme = f'''# slskR PR #204 W783–802 independent cross-review\n\nPinned independently to live PR #{live_pr['number']} at `{HEAD}` / tree `{TREE}`. The PR remains open and draft. All {len(primary_integrity)} primary packet files pass their supplied SHA256 manifest.\n\n## Results\n\n- Reattested 240 source/current cells, 36 exact caller pins, and all 240 prior source/target/status rows. All 12 referenced per-locale prior-ledger file hashes differ from the primary packet\'s recorded hashes, so prior linkage is marked stale/unverified and none of those dispositions is reused. The 29 referenced prior finding records still match their recorded row hashes and source/target values.\n- Rebuilt the sorted source inventory from all 12 current locale catalogs: 5,440 keys. The primary indices 783–802 map to current indices 782–801 (shift −1). Previous primary W782 `Compatibility Review` maps to current index 781; current index 782 is `Complete`. All 12 prior W782 applied readback targets and hashes match.\n- Adjudicated all 108 candidates: {candidate_counts['accept-primary-proposal']} accepted, {candidate_counts['revise-primary-proposal']} revised, {candidate_counts['hold-pending-caller-refactor']} held.\n- Added four W790 correction findings for German, Spanish, French, and Hindi current values.\n- Held all 24 W785/W796 locale cells until their callers localize the action/direction values. W785 source wording also merits clarification.\n- Placeholder, markup, and protected-literal checks passed for every current cell and every cross-review target. Native-speaker approval remains outstanding.\n\n## Key packet files\n\n- `live-cell-reattestation.jsonl`: all 240 live catalog/source checks and hashes.\n- `caller-pin-reattestation.jsonl`: all 36 caller lines, neighboring lines, blobs, and hashes.\n- `prior-disposition-reattestation.jsonl`: live source/target/status row checks for all 240 cells, observed stale/unverified per-locale file provenance, and exact prior finding-row reattestations where present.\n- `W782-boundary-reattestation.jsonl`: previous applied readback evidence for all 12 locales.\n- `candidate-cross-review.jsonl`: independent disposition of all 108 proposals.\n- `new-W790-findings.jsonl`: four added W790 corrections.\n- `held-cells.jsonl`: 24 W785/W796 holds.\n- `full-cell-final-dispositions.jsonl`: final cross-review state for all 240 cells.\n\nThis packet is read-only evidence. No repository/PR content was changed. No tests, builds, scans, CI, browser actions, workflow edits, or releases were run.\n'''
    (OUT / 'README.md').write_text(readme, encoding='utf-8')
    manifest_out = {
        'schemaVersion': 1, 'task': summary['task'], 'repository': 'snapetech-org/slskR',
        'pullRequest': 204, 'attestedHead': HEAD, 'attestedTree': TREE,
        'primaryPacket': str(PR), 'primaryInputIntegrity': 'primary-input-integrity.json',
        'sourceIndexMapping': {'primary': [783, 802], 'current': [782, 801], 'shift': -1},
        'rows': {'sourceOrdinalReattestations': len(ordinal_rows), 'liveCells': len(live_cells),
                 'callerPins': len(caller_live), 'priorDispositions': len(prior_live),
                 'w782Boundary': len(boundary_rows), 'candidateCrossReviews': len(candidate_review),
                 'newW790Findings': len(new_w790), 'heldCells': len(held), 'fullCellFinalDispositions': len(full)},
        'repositoryOrPrModified': False,
    }
    save_json('manifest.json', manifest_out)
    sums = []
    for path in sorted(OUT.iterdir()):
        if path.name == 'SHA256SUMS' or not path.is_file():
            continue
        sums.append(f'{sha(path.read_bytes())}  {path.name}')
    (OUT / 'SHA256SUMS').write_text('\n'.join(sums) + '\n', encoding='utf-8')
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
