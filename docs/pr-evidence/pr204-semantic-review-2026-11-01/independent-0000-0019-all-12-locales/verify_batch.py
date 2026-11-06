#!/usr/bin/env python3
"""Verify exact-head semantic-review evidence for slskR lexical indices 0–19."""
import argparse
import collections
import hashlib
import json
import re
import subprocess
import unicodedata
from pathlib import Path

LOCALES = ['ar', 'de', 'es', 'fr', 'hi', 'id', 'ja', 'ko', 'pt-BR', 'vi', 'zh-Hans', 'zh-Hant']
TERMINAL = {'accepted', 'correction-needed', 'held', 'keep', 'corrected'}
CORRECTIONS = {
    (13, 'ar'): '، الدقة=',
    (14, 'ar'): '، التحذيرات:',
    (15, 'ar'): '، أو قم بتكوين مخزن بيانات الاعتماد أو استخدم عنصر التحكم "الاتصال" في الشريط العلوي.',
    (15, 'de'): ', konfigurieren Sie einen Anmeldedatenspeicher oder verwenden Sie die Schaltfläche „Verbinden“ in der oberen Leiste.',
    (15, 'fr'): ', configurez un magasin d’identifiants ou utilisez le bouton « Connecter » dans la barre supérieure.',
    (15, 'hi'): ', एक क्रेडेंशियल स्टोर कॉन्फ़िगर करें, या शीर्ष बार में “जोड़ना” नियंत्रण का उपयोग करें।',
    (17, 'de'): ', {childDirectoryCount} Ordner',
}


def die(message):
    raise SystemExit('FAIL: ' + message)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def git(repo, *args, raw=False):
    p = subprocess.run(['git', *args], cwd=repo, check=True, stdout=subprocess.PIPE)
    return p.stdout if raw else p.stdout.decode('utf-8').strip()


def target_sha(value):
    raw = value.encode('utf-8') if isinstance(value, str) else json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(',', ':')
    ).encode('utf-8')
    return sha(raw)


def placeholders(value):
    found = []

    def walk(item):
        if isinstance(item, str):
            found.extend(re.findall(r'\{([^{}]+)\}', item))
        elif isinstance(item, dict):
            for child in item.values():
                walk(child)
        elif isinstance(item, list):
            for child in item:
                walk(child)

    walk(value)
    return sorted(set(found))


def nonempty(value):
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, dict):
        return bool(value) and all(nonempty(child) for child in value.values())
    if isinstance(value, list):
        return bool(value) and all(nonempty(child) for child in value)
    return False


def jsonl_records(raw):
    rows = []
    for n, line in enumerate(raw.decode('utf-8').splitlines(), 1):
        if not line.strip():
            continue
        try:
            rows.append((n, json.loads(line)))
        except json.JSONDecodeError:
            continue
    return rows


def walk_json(value):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from walk_json(child)
    elif isinstance(value, list):
        for child in value:
            yield from walk_json(child)


def records_for(path, raw):
    if path.suffix == '.jsonl':
        return jsonl_records(raw)
    if path.suffix == '.json':
        try:
            value = json.loads(raw.decode('utf-8'))
        except json.JSONDecodeError:
            return []
        return [(n + 1, row) for n, row in enumerate(walk_json(value))]
    die(f'unsupported evidence input extension: {path}')


def cell_key(row):
    return row['source_id'], row['locale']


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path, default=None, help='slskR worktree; defaults to this Git worktree')
    parser.add_argument('--prior-audit', type=Path, required=True,
                        help='worktree containing the pinned prior-audit-7ff evidence inputs')
    args = parser.parse_args()
    repo = (args.repo or Path(git(Path.cwd(), 'rev-parse', '--show-toplevel'))).resolve()
    audit = args.prior_audit.resolve()
    bundle = Path(__file__).resolve().parent
    manifest = json.loads((bundle / 'manifest.json').read_text(encoding='utf-8'))
    head, tree = manifest['review_head'], manifest['review_tree']
    source, source_tree = manifest['source_catalog_head'], manifest['source_catalog_tree']

    if git(repo, 'rev-parse', f'{head}^{{tree}}') != tree:
        die('review commit/tree pin mismatch')
    if git(repo, 'rev-parse', f'{source}^{{tree}}') != source_tree:
        die('source/catalog commit/tree pin mismatch')
    git(repo, 'cat-file', '-e', f'{head}^{{commit}}')
    git(repo, 'cat-file', '-e', f'{source}^{{commit}}')
    changed = git(repo, 'diff', '--name-only', source, head).splitlines()
    if any(not path.startswith('docs/') for path in changed):
        die('review head contains non-documentation changes after source/catalog head')

    catalogs, keysets = {}, {}
    structured_count, populated_count = 0, 0
    for locale in LOCALES:
        path = f'web/src/lib/locales/ui-labels.{locale}.json'
        raw = git(repo, 'show', f'{head}:{path}', raw=True)
        if sha(raw) != manifest['direct_catalog']['catalog_sha256'][path]:
            die(f'catalog file hash mismatch for {locale}')
        catalogs[locale] = json.loads(raw.decode('utf-8'))
        keysets[locale] = set(catalogs[locale])
        for value in catalogs[locale].values():
            if isinstance(value, (dict, list)):
                structured_count += 1
            if nonempty(value):
                populated_count += 1
            else:
                die(f'blank catalog value at {locale}:{value!r}')
    if len(set(map(frozenset, keysets.values()))) != 1:
        die('locale key inventories differ')
    source_ids = sorted(next(iter(keysets.values())))
    if len(source_ids) != 5437 or populated_count != 65244:
        die(f'catalog inventory/population mismatch: {len(source_ids)} keys, {populated_count} populated cells')
    if structured_count != 15:
        die(f'expected 15 structured plural cells, found {structured_count}')

    selection = [row for _, row in jsonl_records((bundle / 'selection.jsonl').read_bytes())]
    decisions = [row for _, row in jsonl_records((bundle / 'decisions.jsonl').read_bytes())]
    carries = [row for _, row in jsonl_records((bundle / 'carries.jsonl').read_bytes())]
    exclusions = [row for _, row in jsonl_records((bundle / 'terminal-exclusions.jsonl').read_bytes())]
    if (len(selection), len(decisions), len(carries), len(exclusions)) != (240, 76, 112, 52):
        die('window row counts mismatch')
    for rows, name in [(selection, 'selection'), (decisions, 'decisions'),
                       (carries, 'carries'), (exclusions, 'exclusions')]:
        keys = [cell_key(row) for row in rows]
        if len(keys) != len(set(keys)):
            die(f'duplicate cell in {name}')
    selection_keys = {cell_key(row) for row in selection}
    if selection_keys != {cell_key(row) for row in decisions + carries + exclusions}:
        die('selection does not partition into fresh decisions, accepted carries, and terminal exclusions')
    source_indices = [source_ids.index(source_id) for source_id in sorted({row['source_id'] for row in selection})]
    if source_indices != list(range(20)):
        die('selected keys are not the first 20 lexical source IDs')

    selection_by_key = {cell_key(row): row for row in selection}
    for row in selection:
        locale, sid = row['locale'], row['source_id']
        if locale not in LOCALES or not row['populated']:
            die(f'unpopulated or unsupported selection: {locale}:{sid}')
        value = catalogs[locale].get(sid, '__MISSING__')
        if value == '__MISSING__' or value != row['target_text']:
            die(f'current target differs from selected evidence: {locale}:{sid}')
        if target_sha(value) != row['target_sha256'] or row['source_sha256'] != sha(sid.encode('utf-8')):
            die(f'source/target hash mismatch: {locale}:{sid}')
        if source_ids.index(sid) != row['source_index']:
            die(f'lexical source index mismatch for {sid!r}')

    fresh_counts = collections.Counter(row['status'] for row in decisions)
    prior_counts = collections.Counter(row['status'] for row in carries + exclusions)
    expected_fresh = collections.Counter({'accepted': 69, 'correction-needed': 7})
    expected_prior = collections.Counter({'accepted': 112, 'correction-needed': 45, 'held': 7})
    if fresh_counts != expected_fresh or prior_counts != expected_prior:
        die(f'disposition totals mismatch: {dict(fresh_counts)} / {dict(prior_counts)}')

    corrections = {(row['source_index'], row['locale']): row for row in decisions
                   if row['status'] == 'correction-needed'}
    if set(corrections) != set(CORRECTIONS):
        die('fresh correction-needed cell set differs from the seven documented findings')
    for row in decisions:
        index, locale = row['source_index'], row['locale']
        if (row['review_head'], row['review_tree'], row['reviewed_code_head'], row['reviewed_code_tree']) != (head, tree, source, source_tree):
            die(f'fresh decision pin mismatch: {locale}:{row["source_id"]}')
        if not row['current_target_sha256_revalidated'] or not row['populated'] or not row['source_context_files_reviewed']:
            die(f'incomplete fresh decision record: {locale}:{row["source_id"]}')
        if row['icu_message'] is not False or row['native_speaker_approval'] is not False:
            die(f'unexpected ICU/native-speaker field: {locale}:{row["source_id"]}')
        source_ph, target_ph = placeholders(row['source_id']), placeholders(row['target_text'])
        proposal = CORRECTIONS.get((index, locale))
        if source_ph != target_ph or row['placeholders_source'] != source_ph or row['placeholders_target'] != target_ph:
            die(f'placeholder mismatch: {locale}:{row["source_id"]}')
        if row['status'] == 'correction-needed':
            if row.get('proposed_target') != proposal or placeholders(proposal) != source_ph:
                die(f'correction proposal mismatch: {locale}:{row["source_id"]}')
            if row.get('protected_literals_proposed_preserved') is not True:
                die(f'proposal does not preserve protected literals: {locale}:{row["source_id"]}')
        elif proposal is not None or row.get('proposed_target') is not None:
            die(f'unexpected proposal on accepted cell: {locale}:{row["source_id"]}')
        if row['protected_literals_preserved'] is False and (index, locale) not in {(13, 'ar'), (14, 'ar'), (15, 'ar')}:
            die(f'unexpected protected-literal loss: {locale}:{row["source_id"]}')
        if any(unicodedata.category(char) == 'Cf' for value in [row['target_text'], proposal or ''] for char in value):
            die(f'unsafe format control: {locale}:{row["source_id"]}')
        if row.get('prior_exact_matches'):
            die(f'fresh decision has exact prior refs: {locale}:{row["source_id"]}')

        # Check visible markers that should survive these source fragments.
        value = row['target_text']
        if index == 3 and '%' not in value:
            die('percentage marker missing')
        if index == 4 and ('%' not in value or '|' not in value):
            die('percentage or pipe marker missing')
        if index == 5 and ('#' not in value or '{placeInQueue}' not in value):
            die('queue-position marker/placeholder missing')
        if index == 6 and ('HTTP' not in value or '{status}' not in value or '{statusText}' not in value):
            die('HTTP marker or status placeholder missing')
        if index in {7, 10} and not (value.startswith('(') and value.endswith(')')):
            die(f'parenthetical marker missing: {locale}:{row["source_id"]}')
        if index == 8 and '=' not in value:
            die('agreement comparison marker missing')
        if index == 9 and not (value.startswith('(') and value.endswith(':')):
            die(f'threshold punctuation missing: {locale}:{row["source_id"]}')
        if index == 11 and ('{lockedDirectories}' not in value or '{lockedFiles}' not in value):
            die('locked directory/file placeholders missing')
        if index == 12 and ('{timestampSeconds}' not in value or not value.endswith('s)')):
            die('timestamp seconds marker/placeholder missing')
        if index in {13, 14, 15} and locale != 'ar' and not value.startswith(','):
            die(f'comma separator missing: {locale}:{row["source_id"]}')
        if index == 15 and locale in {'de', 'fr', 'hi'}:
            evidence = row.get('connect_label_evidence', {})
            if evidence.get('source_id') != 'Connect' or not evidence.get('target_text'):
                die(f'localized Connect label evidence missing: {locale}')
        if index == 17 and '{childDirectoryCount}' not in value:
            die('child directory count placeholder missing')
        if index == 19 and not value.startswith(('-', '–')):
            die(f'list marker missing: {locale}')

    # Verify the source callsite excerpt and every runtime file hash/blob.
    context = manifest['source_context']
    if sha((bundle / context['file']).read_bytes()) != context['evidence_text_sha256']:
        die('source context evidence hash mismatch')
    for path, digest in context['sha256'].items():
        if sha(git(repo, 'show', f'{source}:{path}', raw=True)) != digest:
            die(f'source context SHA-256 mismatch: {path}')
        if git(repo, 'rev-parse', f'{source}:{path}') != context['git_blob_ids'][path]:
            die(f'source context Git blob mismatch: {path}')

    # Rehash the complete prior input set and reconstruct every exact terminal match.
    scan = [row for _, row in jsonl_records((bundle / 'prior-evidence-scan-manifest.jsonl').read_bytes())]
    overlap = manifest['prior_overlap_scan']
    if len(scan) != 706 or len(scan) != overlap['scanned_json_evidence_files']:
        die('prior evidence input count mismatch')
    if sha((bundle / 'prior-evidence-scan-manifest.jsonl').read_bytes()) != overlap['manifest_sha256']:
        die('prior evidence manifest hash mismatch')
    canonical = sha(json.dumps(sorted(scan, key=lambda item: (item['root'], item['path'])),
                               sort_keys=True, separators=(',', ':')).encode('utf-8'))
    if canonical != overlap['canonical_input_manifest_sha256']:
        die('canonical prior input manifest hash mismatch')

    refs = collections.defaultdict(list)
    for entry in scan:
        root, rel = entry['root'], Path(entry['path'])
        if rel.is_absolute() or '..' in rel.parts:
            die('unsafe path in prior evidence manifest')
        if root == 'prior-audit-7ff':
            base = audit
        elif root == 'pr-review-head':
            base = repo
        else:
            die(f'unknown prior evidence root: {root}')
        path = base / rel
        raw = path.read_bytes()
        if len(raw) != entry['bytes'] or sha(raw) != entry['sha256']:
            die(f'prior evidence input hash mismatch: {root}:{rel.as_posix()}')
        for line_no, record in records_for(path, raw):
            sid = record.get('source_id') or record.get('message_id') or record.get('id')
            locale = record.get('locale')
            if sid not in source_ids[:20] or locale not in LOCALES:
                continue
            status = str(record.get('status') or record.get('review_outcome') or '').strip().lower().replace('_', '-')
            if status not in TERMINAL:
                continue
            selected = selection_by_key[(sid, locale)]
            target_hash = record.get('target_sha256') or record.get('current_target_sha256')
            if record.get('source_sha256') != selected['source_sha256'] or target_hash != selected['target_sha256']:
                continue
            refs[(sid, locale)].append({'status': status, 'batch': record.get('batch'),
                                        'finding_id': record.get('finding_id'), 'root': root,
                                        'path': rel.as_posix(), 'line': line_no})

    for row in selection:
        key = cell_key(row)
        actual = sorted(refs.get(key, []), key=lambda item: (item['root'], item['path'], item['line'], item['status']))
        recorded = sorted(row['prior_exact_matches'], key=lambda item: (item['root'], item['path'], item['line'], item['status']))
        if actual != recorded:
            die(f'exact prior evidence references mismatch: {row["locale"]}:{row["source_id"]}')
        statuses = {item['status'] for item in actual}
        if row['selection_disposition'] == 'fresh-decision' and statuses:
            die(f'fresh decision overlaps exact terminal evidence: {row["locale"]}:{row["source_id"]}')
        if row['selection_disposition'] == 'exact-accepted-carry' and statuses != {'accepted'}:
            die(f'accepted carry status mismatch: {row["locale"]}:{row["source_id"]}')
        if row['selection_disposition'] == 'exact-terminal-exclusion' and statuses != {row['status']}:
            die(f'terminal exclusion status mismatch: {row["locale"]}:{row["source_id"]}')

    sums = {}
    for line in (bundle / 'SHA256SUMS').read_text(encoding='utf-8').splitlines():
        match = re.fullmatch(r'([0-9a-f]{64})  (.+)', line)
        if not match:
            die('invalid SHA256SUMS row')
        sums[match.group(2)] = match.group(1)
    expected = {path.name: sha(path.read_bytes()) for path in bundle.iterdir()
                if path.is_file() and path.name != 'SHA256SUMS'}
    if sums != expected:
        die('SHA256SUMS does not match bundle files')

    final = collections.Counter(fresh_counts)
    final.update(prior_counts)
    print(json.dumps({
        'result': 'PASS', 'review_head': head, 'review_tree': tree,
        'source_catalog_head': source, 'source_catalog_tree': source_tree,
        'source_keys': 20, 'cell_slots': 240, 'populated_catalog_cells': populated_count,
        'fresh_decisions': dict(fresh_counts), 'prior_exact': dict(prior_counts),
        'final_dispositions': dict(final), 'overlap_inputs_rehashed': len(scan),
        'bundle_files_hashed': len(sums),
    }, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
