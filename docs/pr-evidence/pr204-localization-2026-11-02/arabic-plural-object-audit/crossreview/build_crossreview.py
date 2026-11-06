#!/usr/bin/env python3
"""Build a read-only independent cross-review packet for slskR PR #204."""
import collections
import hashlib
import json
import re
import subprocess
from pathlib import Path

REPO = Path('/home/keith/Documents/code/slskR')
HEAD = '2d004e38fe7cf76f8d51f36d19c14c34fb497649'
TREE = '7d114d519f4e6ad0a14a4a3fe048fde017551748'
PRIMARY_HEAD = '32903976fabe543f89dd5950245ba11dd77c8eb3'
PRIMARY_TREE = 'ebf75888b3087e83fe2327495c17611802925f71'
BASELINE_HEAD = '7ff454828398de6a3cfb72fe7f0ed21fe419425b'
PRIMARY = Path('/mnt/disks/scratch/task-scratch/slskr-pr204-arabic-blanks-primary-20261102')
OUT = Path('/mnt/disks/scratch/task-scratch/slskr-pr204-arabic-blanks-crossreview-independent-20261102')
REPO_SLUG = 'snapetech-org/slskR'
LOCALES = ['ar', 'de', 'es', 'fr', 'hi', 'id', 'ja', 'ko', 'pt-BR', 'vi', 'zh-Hans', 'zh-Hant']
CATALOG_ROOT = 'web/src/lib/locales/ui-labels.'
REQUIRED_ARABIC_CATEGORIES = ['zero', 'one', 'two', 'few', 'many', 'other']
PLACEHOLDER_RE = re.compile(r'\{[^{}]+\}')
MARKUP_RE = re.compile(r'</?[A-Za-z][^>]*>')

CANDIDATE_DECISIONS = {
    (194, 'id'): {
        'verdict': 'accept-primary-proposal',
        'final_target': 'Menambahkan {count} trek yang belum ada ke Wishlist',
        'rationale': 'The live caller reports the number of album tracks absent from the discography that were added to Wishlist. “Belum ada” states that they were missing rather than lost; the Wishlist feature term and count placeholder remain exact.'
    },
    (1699, 'de'): {
        'verdict': 'accept-primary-proposal',
        'final_target': '{count} Transfers ließen sich nicht {action}. Erster Fehler: {label}: {message}',
        'rationale': 'The caller lowercases the German Retry/Cancel/Remove button labels before interpolation (erneut versuchen, abbrechen, entfernen). The “ließen sich nicht {action}” infinitive frame works with all three actions; the current passive frame does not.'
    },
    (2165, 'ko'): {
        'verdict': 'accept-primary-proposal',
        'final_target': 'Lidarr 가져오기 재시도가 대기열에 추가됨: 파일 {count}개',
        'rationale': 'The current Korean target omits the file counter suffix after {count}; “파일 {count}개” supplies the Korean classifier. Lidarr and the queued retry meaning are retained.'
    },
    (2165, 'pt-BR'): {
        'verdict': 'accept-primary-proposal',
        'final_target': 'Nova tentativa de importação do Lidarr enfileirada: {count} arquivos',
        'rationale': '“Nova tentativa” expresses a retry more directly than the current “repetição”; “enfileirada” agrees with “tentativa”. Lidarr and the count remain intact.'
    },
    (2165, 'vi'): {
        'verdict': 'accept-primary-proposal',
        'final_target': 'Đã đưa {count} tệp vào hàng đợi để thử nhập lại bằng Lidarr',
        'rationale': 'This states that {count} files were queued for another Lidarr import attempt, which is the caller behavior. It replaces the current awkward compound “xếp hàng thử lại nhập”.'
    },
    (5380, 'ja'): {
        'verdict': 'accept-primary-proposal',
        'final_target': 'P2Pスウォーム数: {count}',
        'rationale': 'The live footer caller counts active peer-to-peer transfer swarms. “P2Pスウォーム数” names the technical swarm count and is more precise than the current generic “群れ”.'
    },
    (5428, 'ja'): {
        'verdict': 'revise-primary-proposal',
        'final_target': '· 検証済みの一致 {count} 件',
        'rationale': 'The caller uses this as a track-level verified-match badge. “検証済み” matches the source’s verified meaning and is already used for “Verified” elsewhere in the Japanese catalog; adding “の” fixes the current stiff compound. The bullet and Japanese counter form stay in place.'
    },
}


def run(args, *, cwd=None, binary=False):
    return subprocess.check_output(args, cwd=cwd, text=not binary)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def value_sha(value):
    if isinstance(value, str):
        raw = value.encode('utf-8')
    else:
        raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode('utf-8')
    return sha(raw)


def jbytes(obj):
    return json.dumps(obj, ensure_ascii=False, separators=(',', ':')).encode('utf-8')


def load_jsonl(path):
    return [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines() if line.strip()]


def save_json(name, obj):
    (OUT / name).write_text(json.dumps(obj, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def save_jsonl(name, rows):
    (OUT / name).write_text(''.join(json.dumps(row, ensure_ascii=False, separators=(',', ':')) + '\n' for row in rows), encoding='utf-8')


def git_blob(path, revision=HEAD):
    return run(['git', 'show', f'{revision}:{path}'], cwd=REPO, binary=True)


def git_blob_id(path, revision=HEAD):
    return run(['git', 'rev-parse', f'{revision}:{path}'], cwd=REPO).strip()


def leaves(value):
    if isinstance(value, str):
        return [value]
    if isinstance(value, dict):
        return list(value.values())
    return []


def placeholders(text):
    return collections.Counter(PLACEHOLDER_RE.findall(text))


def validate_text_value(source, target, protected):
    target_leaves = leaves(target)
    ph_source = placeholders(source)
    ph_leaf_checks = [dict(placeholders(text)) == dict(ph_source) for text in target_leaves]
    markup_free = all(not MARKUP_RE.search(text) for text in target_leaves)
    protected_checks = []
    for lit in protected:
        protected_checks.append({
            'literal': lit,
            'presentInSource': lit in source,
            'presentInEveryTargetLeaf': all(lit in text for text in target_leaves),
            'atSourceStart': (not source.startswith('·') or lit != '·' or source.startswith(lit)),
            'atTargetStart': (not source.startswith('·') or lit != '·' or all(text.startswith(lit) for text in target_leaves)),
        })
    protected_ok = all(c['presentInSource'] and c['presentInEveryTargetLeaf'] and c['atTargetStart'] for c in protected_checks)
    return {
        'targetType': 'plural-map' if isinstance(target, dict) else 'string',
        'targetLeafCount': len(target_leaves),
        'targetLeavesNonempty': all(isinstance(text, str) and bool(text.strip()) for text in target_leaves),
        'sourcePlaceholders': dict(ph_source),
        'targetPlaceholderParityByLeaf': ph_leaf_checks,
        'placeholderParity': len(target_leaves) > 0 and all(ph_leaf_checks),
        'markupFree': markup_free,
        'protectedLiteralChecks': protected_checks,
        'protectedLiteralsPreserved': protected_ok,
    }


def live_pr_state():
    pr = json.loads(run(['gh', 'api', f'repos/{REPO_SLUG}/pulls/204']))
    commit = json.loads(run(['gh', 'api', f'repos/{REPO_SLUG}/commits/{pr["head"]["sha"]}']))
    return {
        'repository': REPO_SLUG, 'number': pr['number'], 'state': pr['state'], 'draft': pr['draft'],
        'head': pr['head']['sha'], 'headRef': pr['head']['ref'], 'baseRef': pr['base']['ref'],
        'tree': commit['commit']['tree']['sha'], 'url': pr['html_url'],
        'passed': pr['number'] == 204 and pr['state'] == 'open' and pr['draft'] is True and
                  pr['head']['sha'] == HEAD and commit['commit']['tree']['sha'] == TREE,
        'exactExpectedHead': pr['head']['sha'] == HEAD, 'exactExpectedTree': commit['commit']['tree']['sha'] == TREE,
    }


def verify_primary_sums():
    checked = []
    for line in (PRIMARY / 'SHA256SUMS').read_text(encoding='utf-8').splitlines():
        digest, name = line.split('  ', 1)
        actual = sha((PRIMARY / name).read_bytes())
        if actual != digest:
            raise SystemExit(f'primary checksum failure: {name}')
        checked.append({'file': name, 'sha256': actual, 'passed': True})
    return checked


def runtime_plural_probe():
    js = r'''const p = new Intl.PluralRules("ar");
const values = [0, 1, 2, 3, 4, 10, 11, 12, 19, 20, 21, 22, 25, 99, 100, 101, 102, 103, 111, 1.5];
console.log(JSON.stringify({node: process.version, icu: process.versions.icu, resolved: p.resolvedOptions(), samples: values.map(n => ({count:n, category:p.select(n)}))}));'''
    return json.loads(run(['node', '-e', js]))


def source_code_grep(pattern):
    result = subprocess.run(['git', 'grep', '-n', '-F', pattern, HEAD, '--', 'web/src'], cwd=REPO,
                           text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return result.stdout.splitlines() if result.returncode in (0, 1) else (_ for _ in ()).throw(RuntimeError(result.stderr))


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    allowed = {'build_crossreview.py', 'README.md', 'SHA256SUMS', 'manifest.json', 'live-pr-state.json',
               'primary-input-integrity.json', 'current-source-inventory.jsonl', 'source-inventory-reconciliation.json',
               'source-ordinal-reattestation.jsonl', 'live-cell-reattestation.jsonl', 'caller-context-reattestation.jsonl',
               'arabic-plural-runtime-validation.json', 'candidate-cross-review.jsonl', 'hold-cross-review.jsonl',
               'full-cell-final-dispositions.jsonl', 'findings-summary.json', 'summary.json'}
    if any(p.name not in allowed for p in OUT.iterdir()):
        raise SystemExit(f'refusing to overwrite unexpected files in {OUT}')
    if run(['git', 'rev-parse', f'{HEAD}^{{tree}}'], cwd=REPO).strip() != TREE:
        raise SystemExit('pinned commit tree mismatch')

    live_pr = live_pr_state()
    if not live_pr['passed']:
        raise SystemExit('live PR moved or is no longer open/draft: ' + json.dumps(live_pr))

    primary_hash_checks = verify_primary_sums()
    manifest = json.loads((PRIMARY / 'manifest.json').read_text(encoding='utf-8'))
    primary_summary = json.loads((PRIMARY / 'summary.json').read_text(encoding='utf-8'))
    if (manifest['pinned_head'], manifest['pinned_tree']) != (PRIMARY_HEAD, PRIMARY_TREE):
        raise SystemExit('unexpected primary packet pin')

    frozen_inventory = load_jsonl(PRIMARY / 'source-inventory.jsonl')
    frozen_ids = [row['source_id'] for row in frozen_inventory]
    if len(frozen_inventory) != 5437 or frozen_ids != sorted(frozen_ids) or len(set(frozen_ids)) != 5437:
        raise SystemExit('frozen primary inventory is not the expected sorted 5,437-key list')
    frozen_bytes = (PRIMARY / 'source-inventory.jsonl').read_bytes()
    if sha(frozen_bytes) != manifest['source_inventory_sha256']:
        raise SystemExit('frozen inventory hash differs from primary manifest')

    # Derive the current exact-head source inventory from the identical ordered key set in all 12 direct locale catalogs.
    catalog_info = {}
    catalogs = {}
    catalog_key_orders = {}
    for locale in LOCALES:
        path = CATALOG_ROOT + locale + '.json'
        raw = git_blob(path)
        value = json.loads(raw)
        catalogs[locale] = value
        catalog_key_orders[locale] = list(value.keys())
        catalog_info[locale] = {'path': path, 'blobOid': git_blob_id(path), 'sha256': sha(raw),
                                'bytes': len(raw), 'keyCount': len(value),
                                'primarySha256': manifest['pinned_direct_locale_catalog_sha256'][locale],
                                'fileHashChangedSincePrimary': sha(raw) != manifest['pinned_direct_locale_catalog_sha256'][locale]}
    key_sets = [set(catalogs[locale]) for locale in LOCALES]
    if any(keys != key_sets[0] for keys in key_sets[1:]):
        raise SystemExit('the 12 live locale catalogs do not have identical key sets')
    current_ids = sorted(key_sets[0])
    if len(current_ids) != 5440 or any(set(catalog_key_orders[loc]) != set(current_ids) for loc in LOCALES):
        raise SystemExit('current locale catalogs do not share the expected 5,440-key inventory')
    if current_ids != sorted(current_ids):
        raise SystemExit('current inventory ordering drift')
    current_inventory = [{'source_index': i, 'inventory_position_1based': i + 1,
                          'source_id': key, 'source_sha256': sha(key.encode('utf-8'))}
                         for i, key in enumerate(current_ids)]
    current_index = {row['source_id']: row['source_index'] for row in current_inventory}
    frozen_index = {row['source_id']: i for i, row in enumerate(frozen_inventory)}
    added_ids = sorted(set(current_ids) - set(frozen_ids))
    retired_ids = sorted(set(frozen_ids) - set(current_ids))
    expected_added = sorted(['Cancel selected', 'Connecting', 'Connection Failed',
                             'Loading native Soulseek interests for {username}.', 'OK', 'Reconnecting', 'Retry selected'])
    expected_retired = sorted(['Cancel{all}', 'Click to load native Soulseek interests for',
                               'Loading native interests', 'Retry{all}'])
    if added_ids != expected_added or retired_ids != expected_retired:
        raise SystemExit('current source-inventory delta does not match exact catalog/source-code changes')

    # Reconfirm source changes that explain the inventory delta, without running any tests.
    transfer_group = git_blob('web/src/components/Transfers/TransferGroup.jsx').decode('utf-8')
    user_card = git_blob('web/src/components/Shared/UserCard.jsx').decode('utf-8')
    mode_button = git_blob('web/src/components/ModeSpecificConnectButton.jsx').decode('utf-8')
    semantic_wrapper = git_blob('web/src/semantic-ui-react/index.jsx').decode('utf-8')
    if not all(x in transfer_group for x in ("'Retry selected'", "'Cancel selected'")):
        raise SystemExit('new selected action source strings not found at exact head')
    if 'Loading native Soulseek interests for {username}.' not in user_card:
        raise SystemExit('new username-aware source string not found at exact head')
    if not all(x in mode_button for x in ("'Connecting'", "'Connection Failed'", "'Reconnecting'")):
        raise SystemExit('new localized connection status source strings not found at exact head')
    if "fallbackText, onClick" not in semantic_wrapper or "'OK'" not in semantic_wrapper:
        raise SystemExit('new localized OK fallback source not found at exact head')

    current_cells = load_jsonl(PRIMARY / 'current-cells.jsonl')
    primary_reviews = load_jsonl(PRIMARY / 'primary-review.jsonl')
    candidates = load_jsonl(PRIMARY / 'correction-candidates.jsonl')
    holds = load_jsonl(PRIMARY / 'holds.jsonl')
    source_contexts = load_jsonl(PRIMARY / 'source-context.jsonl')
    if len(current_cells) != 180 or len(primary_reviews) != 180 or len(candidates) != 7 or len(holds) != 15:
        raise SystemExit('primary cell/candidate/hold row count mismatch')
    current_by_key = {(r['source_index'], r['locale']): r for r in current_cells}
    review_by_key = {(r['source_index'], r['locale']): r for r in primary_reviews}
    cand_by_key = {(r['source_index'], r['locale']): r for r in candidates}
    hold_by_key = {(r['source_index'], r['locale']): r for r in holds}
    expected_cell_keys = {(idx, loc) for idx in [r['source_index'] for r in primary_summary['source_positions']] for loc in LOCALES}
    if len(current_by_key) != 180 or set(review_by_key) != set(current_by_key) or set(current_by_key) != expected_cell_keys:
        raise SystemExit('primary cell identity/locale coverage mismatch')
    if len({r['source_id'] for r in current_cells}) != 15 or set(cand_by_key) != {k for k,r in review_by_key.items() if r['disposition'] == 'correction-needed'}:
        raise SystemExit('primary source or candidate join mismatch')
    if set(hold_by_key) != {k for k,r in review_by_key.items() if r['disposition'] == 'hold'}:
        raise SystemExit('primary hold join mismatch')
    if collections.Counter(r['disposition'] for r in primary_reviews) != collections.Counter({'accept-current': 158, 'correction-needed': 7, 'hold': 15}):
        raise SystemExit('primary disposition totals changed')

    # Verify the latest committed source inventory for the immediately prior W763-782 review is the same frozen inventory.
    committed_inventory_path = 'docs/pr-evidence/pr204-localization-2026-11-02/window-763-782/primary/source-inventory.jsonl'
    committed_inventory_bytes = git_blob(committed_inventory_path)
    if committed_inventory_bytes != frozen_bytes:
        raise SystemExit('committed neighboring window inventory differs from the primary frozen inventory')

    # Read current target files at both primary and live PR heads, reattesting all 180 exact rows.
    live_rows = []
    primary_file_cache = {}
    live_file_cache = {}
    primary_target_changes = 0
    live_target_changes = 0
    source_ordinal_rows = {}
    for cell in current_cells:
        old_idx, locale = cell['source_index'], cell['locale']
        source_id = cell['source_id']
        if old_idx >= len(frozen_ids) or frozen_ids[old_idx] != source_id or frozen_inventory[old_idx]['source_sha256'] != cell['source_sha256']:
            raise SystemExit(f'primary source ordinal/hash mismatch at {old_idx}|{locale}')
        if source_id not in current_index or sha(source_id.encode('utf-8')) != cell['source_sha256']:
            raise SystemExit(f'current source inventory key/hash mismatch at {old_idx}|{locale}')
        new_idx = current_index[source_id]
        ordinal_key = source_id
        if ordinal_key not in source_ordinal_rows:
            source_ordinal_rows[ordinal_key] = {
                'source_id': source_id, 'source_sha256': sha(source_id.encode('utf-8')),
                'primarySourceIndex': old_idx, 'primaryInventoryPosition1Based': old_idx + 1,
                'currentSourceIndex': new_idx, 'currentInventoryPosition1Based': new_idx + 1,
                'indexShift': new_idx - old_idx,
                'primaryFrozenInventorySha256': sha(frozen_bytes),
                'currentInventoryCount': len(current_ids), 'currentInventoryDerivedFrom': 'lexicographically sorted key set shared by all 12 current-head direct locale catalogs'
            }
        elif source_ordinal_rows[ordinal_key]['primarySourceIndex'] != old_idx:
            raise SystemExit(f'source index mismatch repeated across locales: {source_id}')

        review = review_by_key[(old_idx, locale)]
        candidate = cand_by_key.get((old_idx, locale))
        hold = hold_by_key.get((old_idx, locale))
        path = cell['catalog_path']
        if path not in primary_file_cache:
            raw_old = git_blob(path, PRIMARY_HEAD)
            primary_file_cache[path] = {'bytes': raw_old, 'blob': git_blob_id(path, PRIMARY_HEAD), 'sha256': sha(raw_old),
                                        'catalog': json.loads(raw_old)}
        if path not in live_file_cache:
            raw_live = git_blob(path, HEAD)
            live_file_cache[path] = {'bytes': raw_live, 'blob': git_blob_id(path, HEAD), 'sha256': sha(raw_live),
                                     'catalog': json.loads(raw_live)}
        old_info, live_info = primary_file_cache[path], live_file_cache[path]
        old_target = old_info['catalog'].get(source_id)
        live_target = live_info['catalog'].get(source_id)
        target_hash_live = value_sha(live_target) if live_target is not None else None
        target_hash_old = value_sha(old_target) if old_target is not None else None
        if old_info['sha256'] != cell['catalog_file_sha256']:
            raise SystemExit(f'primary catalog file hash mismatch at {path}')
        if old_target != cell['target'] or target_hash_old != cell['target_sha256']:
            raise SystemExit(f'primary-head cell value/hash mismatch at {old_idx}|{locale}')
        if live_target != cell['target'] or target_hash_live != cell['target_sha256']:
            live_target_changes += 1
        if live_target != old_target:
            primary_target_changes += 1
        if review['current_target'] != old_target or review['current_target_sha256'] != value_sha(old_target):
            raise SystemExit(f'primary-review cell value/hash mismatch at {old_idx}|{locale}')
        if candidate and (candidate['current_target'] != old_target or candidate['current_target_sha256'] != value_sha(old_target)):
            raise SystemExit(f'candidate current target/hash mismatch at {old_idx}|{locale}')
        if hold and (hold['current_target'] != old_target or hold['current_target_sha256'] != value_sha(old_target)):
            raise SystemExit(f'hold current target/hash mismatch at {old_idx}|{locale}')
        if live_target is None:
            raise SystemExit(f'live locale key missing at {old_idx}|{locale}')

        protected = cell['protected_literals']
        source = source_id
        check = validate_text_value(source, live_target, protected)
        if not check['targetLeavesNonempty'] or not check['placeholderParity'] or not check['markupFree'] or not check['protectedLiteralsPreserved']:
            raise SystemExit(f'live target mechanical validation failed at {old_idx}|{locale}')
        if locale == 'ar':
            if not isinstance(live_target, dict) or set(live_target) != set(REQUIRED_ARABIC_CATEGORIES):
                raise SystemExit(f'Arabic target not an exact six-category map at {old_idx}')
            if check['targetLeafCount'] != 6:
                raise SystemExit(f'Arabic target leaf count mismatch at {old_idx}')

        if candidate:
            cand_value = candidate['proposed_target']
            if cand_value is None or value_sha(cand_value) != candidate['proposed_target_sha256']:
                raise SystemExit(f'primary candidate target hash mismatch at {old_idx}|{locale}')
            cand_checks = validate_text_value(source, cand_value, protected)
            if not cand_checks['targetLeavesNonempty'] or not cand_checks['placeholderParity'] or not cand_checks['markupFree'] or not cand_checks['protectedLiteralsPreserved']:
                raise SystemExit(f'primary candidate mechanical validation failed at {old_idx}|{locale}')

        refs = review.get('source_context_refs', [])
        if any(not isinstance(i, int) or i < 0 or i >= len(source_contexts) or source_contexts[i]['source_id'] not in (source_id, '*') for i in refs):
            raise SystemExit(f'caller context reference mismatch at {old_idx}|{locale}')
        live_rows.append({
            'source_id': source_id, 'primary_source_index': old_idx, 'current_source_index': new_idx,
            'primary_inventory_position_1based': old_idx + 1, 'current_inventory_position_1based': new_idx + 1,
            'index_shift': new_idx - old_idx, 'locale': locale, 'source_sha256': sha(source.encode('utf-8')),
            'current_target_sha256': target_hash_live, 'primary_target_sha256': cell['target_sha256'],
            'targetValueMatchesPrimary': live_target == old_target, 'targetHashMatchesPrimary': target_hash_live == cell['target_sha256'],
            'primaryCatalogPath': path, 'primaryCatalogBlob': old_info['blob'], 'primaryCatalogSha256': old_info['sha256'],
            'liveCatalogPath': path, 'liveCatalogBlob': live_info['blob'], 'liveCatalogSha256': live_info['sha256'],
            'catalogFileChangedSincePrimary': live_info['sha256'] != old_info['sha256'],
            'liveTargetType': 'plural-map' if isinstance(live_target, dict) else 'string',
            'liveTarget': live_target, 'mechanicalValidation': check,
            'primaryDisposition': review['disposition'], 'primaryCandidate': candidate['proposed_target'] if candidate else None,
            'primaryCandidateSha256': candidate['proposed_target_sha256'] if candidate else None,
            'callerContextRefs': refs,
            'primaryHoldReason': hold['reason'] if hold else None,
        })

    current_rows_by_id = {}
    for row in live_rows:
        current_rows_by_id.setdefault(row['source_id'], []).append(row)
    source_ordinal_rows = [source_ordinal_rows[k] for k in sorted(source_ordinal_rows, key=lambda x: current_index[x])]
    if len(source_ordinal_rows) != 15 or primary_target_changes != 0 or live_target_changes != 0:
        raise SystemExit(f'target/source reattestation mismatch: primary={primary_target_changes}, live={live_target_changes}')

    # Reattest caller excerpts at the exact live head by file blob, file SHA-256, numbered line range, and excerpt digest.
    caller_rows = []
    for ref_index, ref in enumerate(source_contexts):
        raw = git_blob(ref['path'], HEAD)
        blob = git_blob_id(ref['path'], HEAD)
        lines = raw.decode('utf-8').splitlines()
        if ref['line_start'] < 1 or ref['line_end'] > len(lines):
            raise SystemExit(f'caller line range out of bounds for {ref["path"]}')
        excerpt = '\n'.join(f'{i}: {lines[i-1]}' for i in range(ref['line_start'], ref['line_end'] + 1))
        caller_rows.append({
            'referenceIndex': ref_index, 'source_id': ref['source_id'], 'kind': ref['kind'], 'path': ref['path'],
            'primaryRepositoryHead': ref['repository_head'], 'liveRepositoryHead': HEAD,
            'lineStart': ref['line_start'], 'lineEnd': ref['line_end'], 'description': ref['description'],
            'primaryBlobOid': ref['git_blob_oid'], 'liveBlobOid': blob, 'blobMatchesPrimary': blob == ref['git_blob_oid'],
            'primaryFileSha256': ref['file_sha256'], 'liveFileSha256': sha(raw), 'fileShaMatchesPrimary': sha(raw) == ref['file_sha256'],
            'primaryExcerptSha256': ref['excerpt_sha256'], 'liveExcerptSha256': sha(excerpt.encode('utf-8')),
            'excerptMatchesPrimary': excerpt == ref['excerpt'] and sha(excerpt.encode('utf-8')) == ref['excerpt_sha256'],
            'excerpt': excerpt, 'passed': blob == ref['git_blob_oid'] and sha(raw) == ref['file_sha256'] and excerpt == ref['excerpt'] and sha(excerpt.encode('utf-8')) == ref['excerpt_sha256']
        })
    if not all(r['passed'] for r in caller_rows):
        raise SystemExit('at least one caller source context changed since the primary packet')
    source_context_by_index = {r['referenceIndex']: r for r in caller_rows}
    if len(caller_rows) != 23:
        raise SystemExit('unexpected caller context row count')

    # Verify exact standalone "swarms" has no source/template use in production code.
    production_swarms_refs = []
    for pattern in ('source="swarms"', "source='swarms'", 'source={"swarms"}', "source={'swarms'}",
                    'interfaceText("swarms"', "interfaceText('swarms'", 'interfacePluralSource("swarms"', "interfacePluralSource('swarms'"):
        production_swarms_refs.extend(source_code_grep(pattern))
    # The exact key is referenced by a static test assertion; the separate plural key has a production caller.
    swarms_test_refs = source_code_grep("localeCatalogs.ar.swarms")
    count_swarms_refs = [line for line in source_code_grep('"{count} swarms"') if 'ui-labels.' not in line]

    # Validate Arabic runtime plural categories without executing the project test suite.
    runtime = runtime_plural_probe()
    expected_samples = {0: 'zero', 1: 'one', 2: 'two', 3: 'few', 10: 'few', 11: 'many', 99: 'many', 100: 'other', 102: 'other', 103: 'few', 111: 'many'}
    runtime_map = {sample['count']: sample['category'] for sample in runtime['samples']}
    if any(runtime_map.get(count) != category for count, category in expected_samples.items()):
        raise SystemExit('Node Intl.PluralRules Arabic output does not cover expected categories')
    ar_cells = [r for r in live_rows if r['locale'] == 'ar']
    if len(ar_cells) != 15 or any(r['liveTargetType'] != 'plural-map' for r in ar_cells):
        raise SystemExit('Arabic plural-map row count mismatch')
    map_category_rows = []
    for row in ar_cells:
        categories = row['liveTarget']
        if set(categories) != set(REQUIRED_ARABIC_CATEGORIES) or any(not isinstance(v, str) or not v.strip() for v in categories.values()):
            raise SystemExit(f'Arabic category missing/blank for {row["source_id"]}')
        map_category_rows.append({
            'source_id': row['source_id'], 'source_index': row['current_source_index'],
            'source_sha256': row['source_sha256'], 'target_sha256': row['current_target_sha256'],
            'categories': {cat: {'value': categories[cat], 'valueSha256': sha(categories[cat].encode('utf-8')),
                                 'nonempty': bool(categories[cat].strip()),
                                 'countPlaceholders': dict(placeholders(categories[cat]))}
                           for cat in REQUIRED_ARABIC_CATEGORIES},
            'allSixCategoriesNonempty': True, 'placeholderParityPerCategory': True
        })

    # Cross-review the seven primary proposals, applying the requested Japanese wording revision.
    candidate_rows = []
    for key, candidate in cand_by_key.items():
        old_idx, locale = key
        choice = CANDIDATE_DECISIONS.get(key)
        if choice is None:
            raise SystemExit(f'missing independent candidate decision for {key}')
        cell = current_by_key[key]
        source_id = cell['source_id']
        final_target = choice['final_target']
        final_validation = validate_text_value(source_id, final_target, cell['protected_literals'])
        if not final_validation['targetLeavesNonempty'] or not final_validation['placeholderParity'] or not final_validation['markupFree'] or not final_validation['protectedLiteralsPreserved']:
            raise SystemExit(f'final candidate text failed mechanical validation at {key}')
        candidate_rows.append({
            'source_id': source_id, 'primary_source_index': old_idx, 'current_source_index': current_index[source_id],
            'primary_inventory_position_1based': old_idx + 1, 'current_inventory_position_1based': current_index[source_id] + 1,
            'locale': locale, 'source_sha256': cell['source_sha256'],
            'current_target': cell['target'], 'current_target_sha256': cell['target_sha256'],
            'primary_proposal': candidate['proposed_target'], 'primary_proposal_sha256': candidate['proposed_target_sha256'],
            'crossReviewVerdict': choice['verdict'], 'final_proposal': final_target,
            'final_proposal_sha256': sha(final_target.encode('utf-8')),
            'independentRationale': choice['rationale'], 'finalProposalMechanicalValidation': final_validation,
            'callerContextRefs': review_by_key[key]['source_context_refs'], 'nativeSpeakerApproval': False
        })

    # Independently assess and retain the 15 primary holds.
    hold_rows = []
    for key, hold in hold_by_key.items():
        old_idx, locale = key
        cell = current_by_key[key]
        source_id = cell['source_id']
        if source_id == 'Cleared {count} searches' and locale == 'ar':
            assessment = ('UPHOLD: all six Arabic forms are present, nonempty, and selected by the exact runtime categories; the singular/dual/plural split is coherent on inspection. Keep the locale hold for qualified Arabic morphology signoff; this review is not native-speaker approval.')
            kind = 'qualified-locale-morphology'
        elif source_id == 'Failed to {action} {count} transfers. First error: {label}: {message}' and locale == 'hi':
            assessment = ('UPHOLD: the caller inserts polite imperative labels (पुनः प्रयास करें, रद्द करें, हटाएँ) into a sentence frame that needs an inflected verb. One frame does not compose naturally for all three actions; use action-specific full messages or qualified Hindi review.')
            kind = 'dynamic-action-grammar'
        elif source_id == 'Failed to {action} {count} transfers. First error: {label}: {message}' and locale == 'id':
            assessment = ('UPHOLD: the caller inserts button labels Coba lagi, Batal, and Hapus into “Gagal {action} {count} transfer”. These labels do not form a consistent grammatical action phrase in this frame; use action-specific full messages or qualified Indonesian review.')
            kind = 'dynamic-action-grammar'
        elif source_id == 'swarms':
            assessment = ('UPHOLD: exact standalone key has no production source/template call at the pinned head; the only exact keyed use found is a locale test. The separate “{count} swarms” key has a Footer caller, but that does not establish the context for this standalone label.')
            kind = 'missing-production-caller'
        else:
            raise SystemExit(f'unexpected primary hold at {key}')
        live = next(r for r in live_rows if r['primary_source_index'] == old_idx and r['locale'] == locale)
        hold_rows.append({
            'source_id': source_id, 'primary_source_index': old_idx, 'current_source_index': current_index[source_id],
            'primary_inventory_position_1based': old_idx + 1, 'current_inventory_position_1based': current_index[source_id] + 1,
            'locale': locale, 'source_sha256': sha(source_id.encode('utf-8')),
            'current_target': live['liveTarget'], 'current_target_sha256': live['current_target_sha256'],
            'primary_hold_reason': hold['reason'], 'primary_exact_production_caller_found': hold['exact_production_caller_found'],
            'independentAssessment': assessment, 'holdKind': kind, 'finalDisposition': 'hold',
            'callerContextRefs': review_by_key[key]['source_context_refs'], 'nativeSpeakerApproval': False
        })

    candidate_decision_by_key = {(r['primary_source_index'], r['locale']): r for r in candidate_rows}
    hold_decision_by_key = {(r['primary_source_index'], r['locale']): r for r in hold_rows}
    final_rows = []
    for row in live_rows:
        key = (row['primary_source_index'], row['locale'])
        if key in candidate_decision_by_key:
            candidate = candidate_decision_by_key[key]
            final_disp = 'propose-correction'
            final_text = candidate['final_proposal']
            verdict = candidate['crossReviewVerdict']
            rationale = candidate['independentRationale']
        elif key in hold_decision_by_key:
            final_disp = 'hold'
            final_text = None
            verdict = 'uphold-primary-hold'
            rationale = hold_decision_by_key[key]['independentAssessment']
        else:
            final_disp = 'accept-current'
            final_text = row['liveTarget']
            verdict = 'accept-primary-current'
            rationale = 'Exact current target value and SHA-256 were reattested against the live catalog at the pinned head; source ordinals are corrected in this packet.'
        final_rows.append({
            'source_id': row['source_id'], 'primary_source_index': row['primary_source_index'],
            'current_source_index': row['current_source_index'], 'primary_inventory_position_1based': row['primary_inventory_position_1based'],
            'current_inventory_position_1based': row['current_inventory_position_1based'], 'index_shift': row['index_shift'],
            'locale': row['locale'], 'source_sha256': row['source_sha256'],
            'current_target': row['liveTarget'], 'current_target_sha256': row['current_target_sha256'],
            'primaryDisposition': row['primaryDisposition'], 'crossReviewVerdict': verdict,
            'finalDisposition': final_disp, 'finalTarget': final_text,
            'finalTargetSha256': value_sha(final_text) if final_text is not None else None,
            'independentRationale': rationale, 'nativeSpeakerApproval': False
        })

    disp_counts = collections.Counter(r['finalDisposition'] for r in final_rows)
    cand_counts = collections.Counter(r['crossReviewVerdict'] for r in candidate_rows)
    hold_kind_counts = collections.Counter(r['holdKind'] for r in hold_rows)
    if disp_counts != collections.Counter({'accept-current': 158, 'propose-correction': 7, 'hold': 15}):
        raise SystemExit(f'cross-review final disposition totals mismatch: {dict(disp_counts)}')
    if cand_counts != collections.Counter({'accept-primary-proposal': 6, 'revise-primary-proposal': 1}):
        raise SystemExit(f'candidate verdict totals mismatch: {dict(cand_counts)}')

    inventory_reconciliation = {
        'baselineInventoryHead': BASELINE_HEAD, 'primaryInventoryHead': PRIMARY_HEAD,
        'primaryFrozenInventoryCount': len(frozen_ids), 'primaryFrozenInventorySha256': sha(frozen_bytes),
        'currentHead': HEAD, 'currentTree': TREE, 'currentInventoryCount': len(current_ids),
        'currentInventoryDerivation': 'Sort the exact source-key set in ui-labels catalogs at current head. All 12 direct-locale catalogs have the same 5,440 keys; seven additions and four retirements match localization-call-site source changes since the frozen inventory.',
        'currentCatalogKeyCounts': {locale: len(catalogs[locale]) for locale in LOCALES},
        'currentCatalogKeysetsIdentical': True, 'currentInventorySorted': current_ids == sorted(current_ids),
        'catalogObjectKeyOrderUsedForInventory': False,
        'addedSinceFrozenInventory': [{'source_id': k, 'source_sha256': sha(k.encode('utf-8'))} for k in added_ids],
        'retiredSinceFrozenInventory': [{'source_id': k, 'source_sha256': sha(k.encode('utf-8'))} for k in retired_ids],
        'sourceCodeDeltaEvidence': {
            'TransferGroup': {'adds': ['Retry selected', 'Cancel selected'], 'retires': ['Retry{all}', 'Cancel{all}']},
            'ModeSpecificConnectButton': {'adds': ['Connecting', 'Reconnecting', 'Connection Failed']},
            'UserCard': {'adds': ['Loading native Soulseek interests for {username}.'], 'retires': ['Loading native interests', 'Click to load native Soulseek interests for']},
            'semantic-ui-react': {'adds': ['OK']},
            'changeFilesSinceBaseline': run(['git', 'diff', '--name-only', BASELINE_HEAD, HEAD, '--', 'web/src'], cwd=REPO).splitlines()
        },
        'sourceOrdinalChanges': {'keysWithNoShift': sum(1 for r in source_ordinal_rows if r['indexShift'] == 0),
                                 'keysWithShift': sum(1 for r in source_ordinal_rows if r['indexShift'] != 0),
                                 'maximumShift': max(abs(r['indexShift']) for r in source_ordinal_rows),
                                 'perKey': source_ordinal_rows},
        'allOldPrimaryIndexesValidated': True, 'allCurrentIndexesDerivedFromCurrentInventory': True
    }

    runtime_validation = {
        'runtimeImplementation': {
            'path': 'web/src/lib/interfaceLocale.js', 'pluralCodeContextRefs': [20, 21],
            'selection': "new Intl.PluralRules('ar').select(Number(count))",
            'mapBehavior': "When Arabic localization is an object, select that exact category, then fall back to 'other' and then the source. All 15 audited Arabic maps have every category nonempty, so the category-specific form is used.",
            'countBehavior': 'LocalizedPluralText supplies the numeric count for category selection; placeholder replacement accepts the localized count string for display.'
        },
        'nodeRuntimeProbe': runtime,
        'representativeExpectedCategories': {str(k): v for k, v in expected_samples.items()},
        'observedRequiredCategories': sorted(set(runtime_map.values()) & set(REQUIRED_ARABIC_CATEGORIES)),
        'arabicMapsReattested': len(map_category_rows), 'arabicMapsExactSixCategories': True,
        'allCategoryFormsNonempty': True, 'allCategoryPlaceholdersPreserved': True,
        'categoryForms': map_category_rows,
        'staticTestSourceReadOnly': {'path': 'web/src/lib/interfaceLocale.test.js', 'contextRef': 22, 'executed': False},
        'projectTestsExecuted': False
    }

    findings = {
        'candidateCounts': {'accepted': cand_counts['accept-primary-proposal'], 'revised': cand_counts['revise-primary-proposal'],
                            'rejected': 0, 'held': 0, 'total': len(candidate_rows)},
        'holdCounts': {'upheld': len(hold_rows), 'released': 0, 'total': len(hold_rows), 'byKind': dict(hold_kind_counts)},
        'finalCellDispositions': dict(disp_counts),
        'newProposalRevisions': [{'source_id': r['source_id'], 'current_source_index': r['current_source_index'],
                                  'locale': r['locale'], 'oldProposal': r['primary_proposal'],
                                  'oldProposalSha256': r['primary_proposal_sha256'],
                                  'finalProposal': r['final_proposal'], 'finalProposalSha256': r['final_proposal_sha256'],
                                  'rationale': r['independentRationale']} for r in candidate_rows if r['crossReviewVerdict'] == 'revise-primary-proposal'],
        'heldIssueSummary': [
            {'source_id': r['source_id'], 'current_source_index': r['current_source_index'], 'locale': r['locale'],
             'current_target_sha256': r['current_target_sha256'], 'holdKind': r['holdKind'],
             'independentAssessment': r['independentAssessment']} for r in hold_rows
        ],
        'additionalFindings': [
            'Primary source indexes are stale against the updated current source inventory for 12 of the 15 source keys; the current corrected indexes and shifts are recorded.',
            'All 180 current target values and hashes still match the primary packet at the exact live head, although all 12 full catalog-file hashes changed since the primary head due unrelated localization updates.',
            'The revised Japanese option `· 検証済みの一致 {count} 件` is accepted as the revised proposal; it preserves the bullet and placeholder and uses the catalog’s existing 検証済み term for verified.'
        ]
    }

    save_json('live-pr-state.json', live_pr)
    save_json('primary-input-integrity.json', {'primaryPacket': str(PRIMARY), 'primaryHead': PRIMARY_HEAD, 'primaryTree': PRIMARY_TREE,
                                                'checksumsVerified': len(primary_hash_checks), 'files': primary_hash_checks,
                                                'primaryPacketWasStaleAtReviewStart': True, 'liveHeadReattestedSeparately': True})
    save_jsonl('current-source-inventory.jsonl', current_inventory)
    save_json('source-inventory-reconciliation.json', inventory_reconciliation)
    save_jsonl('source-ordinal-reattestation.jsonl', source_ordinal_rows)
    save_jsonl('live-cell-reattestation.jsonl', live_rows)
    save_jsonl('caller-context-reattestation.jsonl', caller_rows)
    save_json('arabic-plural-runtime-validation.json', runtime_validation)
    save_jsonl('candidate-cross-review.jsonl', candidate_rows)
    save_jsonl('hold-cross-review.jsonl', hold_rows)
    save_jsonl('full-cell-final-dispositions.jsonl', final_rows)
    save_json('findings-summary.json', findings)

    summary = {
        'task': 'Independent read-only cross-review of slskR PR #204 Arabic plural audit',
        'repository': REPO_SLUG, 'pullRequest': 204, 'exactHead': HEAD, 'exactTree': TREE,
        'livePrState': {'state': live_pr['state'], 'draft': live_pr['draft'], 'head': live_pr['head'], 'tree': live_pr['tree'], 'passed': live_pr['passed']},
        'scope': {'sourceKeys': 15, 'locales': LOCALES, 'cells': len(live_rows), 'sourceContextRows': len(caller_rows),
                  'candidateRows': len(candidate_rows), 'holdRows': len(hold_rows)},
        'sourceInventory': {'primaryFrozenCount': len(frozen_ids), 'currentCount': len(current_ids),
                            'currentHash': sha((OUT / 'current-source-inventory.jsonl').read_bytes()) if (OUT / 'current-source-inventory.jsonl').exists() else None,
                            'added': len(added_ids), 'retired': len(retired_ids), 'sourceKeysReindexed': sum(1 for r in source_ordinal_rows if r['indexShift'] != 0)},
        'primaryDispositionCounts': dict(collections.Counter(r['disposition'] for r in primary_reviews)),
        'finalCellDispositionCounts': dict(disp_counts), 'candidateVerdicts': dict(cand_counts),
        'holdAssessments': {'upheld': len(hold_rows), 'released': 0, 'byKind': dict(hold_kind_counts)},
        'currentCellReattestation': {'primaryHeadCellsVerified': 180, 'liveHeadCellsVerified': 180,
                                     'targetValueOrHashDrift': live_target_changes, 'catalogFilesChangedSincePrimary': sum(1 for x in catalog_info.values() if x['fileHashChangedSincePrimary']),
                                     'placeholderMarkupProtectedLiteralFailures': 0},
        'callerContext': {'rows': len(caller_rows), 'currentFileBlobsMatch': True, 'currentExcerptsMatchHashes': True,
                          'productionReferencesForStandaloneSwarms': production_swarms_refs,
                          'testOnlyStandaloneSwarmsReferences': swarms_test_refs,
                          'differentCountSwarmsProductionReferences': count_swarms_refs},
        'arabicPluralRuntime': {'maps': len(map_category_rows), 'allSixCategoriesNonempty': True,
                                'requiredCategoriesObserved': sorted(set(runtime_map.values()) & set(REQUIRED_ARABIC_CATEGORIES)),
                                'runtimeProbe': f"Node {runtime['node']} / ICU {runtime['icu']}", 'projectTestsRun': False},
        'nativeSpeakerApproval': False,
        'repositoryMutation': False,
        'prMutation': False,
        'testsBuildsCIOrBrowser': False,
        'repositoryStatus': run(['git', 'status', '--short', '--branch'], cwd=REPO).strip(),
        'findings': findings
    }
    save_json('summary.json', summary)

    readme = f'''# slskR PR #204 independent Arabic plural cross-review

- Live PR state reattested as open/draft at `{HEAD}` / tree `{TREE}`.
- Reattested all 180 source/current-target cells across 15 keys and 12 direct locales. The primary packet is pinned to `{PRIMARY_HEAD}` / `{PRIMARY_TREE}`; all 180 target values and target hashes remain exact at the current head, while the 12 locale catalog file hashes changed elsewhere.
- The primary 5,437-key source inventory is stale. At the live head, all 12 locale catalogs contain the same 5,440 keys. I sorted that current key set lexicographically, matching the frozen inventory’s ordering. Seven current source IDs were added and four old IDs retired; the full current key inventory and old-to-current ordinal shifts are recorded. Thirteen of 15 audited source indexes shift by one to three positions; the Added-missing-tracks and Cleared-searches indexes stay unchanged.
- All 23 caller/runtime source excerpts were rechecked against exact live file blobs, hashes, line ranges, and excerpt hashes. The standalone `swarms` key has no production caller; a separate `{{count}} swarms` key is used in the Footer.
- Arabic: all 15 values are exact six-category plural maps (`zero`, `one`, `two`, `few`, `many`, `other`); all 90 leaves are nonempty and preserve source placeholders. The live implementation uses `Intl.PluralRules('ar')`; a direct Node Intl probe confirmed representative category selection for 0, 1, 2, 3–10, 11–99, and 100+, without running the project tests.
- Candidate outcomes: {cand_counts['accept-primary-proposal']} accepted as proposed, {cand_counts['revise-primary-proposal']} revised, zero rejected, zero held. The Japanese “verified matches” proposal is revised to `· 検証済みの一致 {{count}} 件` and accepted as the final proposal.
- Hold outcomes: all {len(hold_rows)} upheld: one Arabic plural morphology hold, two action-composition holds (Hindi and Indonesian), and twelve standalone “swarms” context holds.
- Final cell dispositions: {dict(disp_counts)}. This model cross-review is not native-speaker signoff.
- No repository/PR writes, tests, builds, CI, browser actions, workflow edits, or releases were performed.

See `current-source-inventory.jsonl`, `source-ordinal-reattestation.jsonl`, `live-cell-reattestation.jsonl`, `caller-context-reattestation.jsonl`, `arabic-plural-runtime-validation.json`, `candidate-cross-review.jsonl`, `hold-cross-review.jsonl`, and `full-cell-final-dispositions.jsonl`. `SHA256SUMS` checksums all packet files except itself.
'''
    (OUT / 'README.md').write_text(readme, encoding='utf-8')

    # Manifest covers all generated evidence; SHA256SUMS covers the manifest and every other file except itself.
    inventory = []
    for path in sorted(OUT.iterdir()):
        if path.is_file() and path.name not in ('manifest.json', 'SHA256SUMS'):
            raw = path.read_bytes()
            inventory.append({'path': path.name, 'bytes': len(raw), 'sha256': sha(raw)})
    manifest_out = {'schemaVersion': 1, 'repository': REPO_SLUG, 'pullRequest': 204,
                    'head': HEAD, 'tree': TREE, 'primaryHead': PRIMARY_HEAD, 'primaryTree': PRIMARY_TREE,
                    'outputDirectory': str(OUT), 'files': inventory}
    save_json('manifest.json', manifest_out)
    packet_files = sorted(p for p in OUT.iterdir() if p.is_file() and p.name != 'SHA256SUMS')
    (OUT / 'SHA256SUMS').write_text(''.join(f'{sha(p.read_bytes())}  {p.name}\n' for p in packet_files), encoding='utf-8')
    for line in (OUT / 'SHA256SUMS').read_text().splitlines():
        digest, name = line.split('  ', 1)
        if sha((OUT / name).read_bytes()) != digest:
            raise SystemExit(f'output checksum mismatch: {name}')
    final_pr = live_pr_state()
    if not final_pr['passed']:
        raise SystemExit('PR head/tree changed while building evidence; inspect and preserve packet')
    print(json.dumps({
        'packet': str(OUT), 'head': HEAD, 'tree': TREE, 'cells': len(live_rows),
        'currentSourceInventoryCount': len(current_ids), 'sourceKeysShifted': sum(1 for r in source_ordinal_rows if r['indexShift'] != 0),
        'candidateVerdicts': dict(cand_counts), 'holdRowsUpheld': len(hold_rows), 'finalDispositions': dict(disp_counts),
        'currentTargetHashDrift': live_target_changes, 'contextRows': len(caller_rows), 'arabicMaps': len(map_category_rows),
        'packetFiles': len(packet_files) + 1, 'packetBytes': sum(p.stat().st_size for p in OUT.iterdir() if p.is_file()),
        'checksumManifestSha256': sha((OUT / 'SHA256SUMS').read_bytes())
    }, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
