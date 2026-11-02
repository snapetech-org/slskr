#!/usr/bin/env python3
"""Verify exact-head semantic-review evidence for slskR lexical indices 43–62."""
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
    (45, 'hi'): '24 घंटे',
    (46, 'hi'): '255, 128, 64, ... (RGBA पिक्सेल डेटा)',
    (54, 'ar'): '4 نبضات',
    (59, 'es'): '7 días',
    (62, 'ar'): '8 نبضات',
}


def die(message):
    raise SystemExit('FAIL: ' + message)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def git(repo, *args, raw=False):
    process = subprocess.run(['git', *args], cwd=repo, check=True, stdout=subprocess.PIPE)
    return process.stdout if raw else process.stdout.decode('utf-8').strip()


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
    result = []
    for line_number, line in enumerate(raw.decode('utf-8').splitlines(), 1):
        if not line.strip():
            continue
        try:
            result.append((line_number, json.loads(line)))
        except json.JSONDecodeError:
            continue
    return result


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
        return [(number + 1, row) for number, row in enumerate(walk_json(value))]
    die(f'unsupported evidence file type: {path}')


def cell_key(row):
    return row['source_id'], row['locale']


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path, default=None)
    parser.add_argument('--prior-audit', type=Path, required=True)
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
    if any(not path.startswith('docs/') for path in git(repo, 'diff', '--name-only', source, head).splitlines()):
        die('review head contains non-documentation changes after source/catalog head')

    catalogs, keysets = {}, {}
    populated = structured = 0
    for locale in LOCALES:
        path = f'web/src/lib/locales/ui-labels.{locale}.json'
        raw = git(repo, 'show', f'{head}:{path}', raw=True)
        if sha(raw) != manifest['direct_catalog']['catalog_sha256'][path]:
            die(f'catalog hash mismatch for {locale}')
        catalogs[locale] = json.loads(raw.decode('utf-8'))
        keysets[locale] = set(catalogs[locale])
        for value in catalogs[locale].values():
            if isinstance(value, (dict, list)):
                structured += 1
            if not nonempty(value):
                die(f'blank target at {locale}')
            populated += 1
    if len(set(map(frozenset, keysets.values()))) != 1 or len(next(iter(keysets.values()))) != 5437:
        die('locale source-key inventories differ')
    source_ids = sorted(next(iter(keysets.values())))
    if populated != 65244 or structured != 15:
        die(f'catalog inventory mismatch: {populated} populated / {structured} structured')

    selection = [row for _, row in jsonl_records((bundle / 'selection.jsonl').read_bytes())]
    decisions = [row for _, row in jsonl_records((bundle / 'decisions.jsonl').read_bytes())]
    carries = [row for _, row in jsonl_records((bundle / 'carries.jsonl').read_bytes())]
    exclusions = [row for _, row in jsonl_records((bundle / 'terminal-exclusions.jsonl').read_bytes())]
    if (len(selection), len(decisions), len(carries), len(exclusions)) != (240, 98, 138, 4):
        die('window row counts mismatch')
    for rows, name in [(selection, 'selection'), (decisions, 'decisions'), (carries, 'carries'), (exclusions, 'exclusions')]:
        keys = [cell_key(row) for row in rows]
        if len(keys) != len(set(keys)):
            die(f'duplicate cell in {name}')
    if {cell_key(row) for row in selection} != {cell_key(row) for row in decisions + carries + exclusions}:
        die('selection does not partition into decisions, carries, and exclusions')
    source_window = sorted({row['source_id'] for row in selection})
    if [source_ids.index(source_id) for source_id in source_window] != list(range(43, 63)):
        die('selected keys are not lexical indices 43–62')
    selection_by_key = {cell_key(row): row for row in selection}
    for row in selection:
        locale, source_id = row['locale'], row['source_id']
        if locale not in LOCALES or not row['populated']:
            die(f'unpopulated selection: {locale}:{source_id}')
        current = catalogs[locale].get(source_id, '__MISSING__')
        if current == '__MISSING__' or current != row['target_text']:
            die(f'current target mismatch: {locale}:{source_id}')
        if target_sha(current) != row['target_sha256'] or row['source_sha256'] != sha(source_id.encode('utf-8')):
            die(f'source/target hash mismatch: {locale}:{source_id}')
        if source_ids.index(source_id) != row['source_index']:
            die(f'lexical source index mismatch: {source_id!r}')

    fresh_counts = collections.Counter(row['status'] for row in decisions)
    prior_counts = collections.Counter(row['status'] for row in carries + exclusions)
    if fresh_counts != collections.Counter({'accepted': 93, 'correction-needed': 5}):
        die(f'fresh disposition totals mismatch: {dict(fresh_counts)}')
    if prior_counts != collections.Counter({'accepted': 138, 'correction-needed': 4}):
        die(f'prior disposition totals mismatch: {dict(prior_counts)}')
    expected_indices = {43,44,45,46,47,48,50,52,53,54,56,57,58,59,60,61,62}
    if {row['source_index'] for row in decisions} != expected_indices:
        die('fresh source-index set mismatch')

    corrections = {(row['source_index'], row['locale']): row for row in decisions
                   if row['status'] == 'correction-needed'}
    if set(corrections) != set(CORRECTIONS):
        die('correction candidate set mismatch')
    for row in decisions:
        index, locale, value = row['source_index'], row['locale'], row['target_text']
        if (row['review_head'], row['review_tree'], row['reviewed_code_head'], row['reviewed_code_tree']) != (head, tree, source, source_tree):
            die(f'fresh decision pin mismatch: {locale}:{row["source_id"]}')
        if not row['current_target_sha256_revalidated'] or not row['populated'] or not row['source_context_files_reviewed']:
            die(f'incomplete fresh decision: {locale}:{row["source_id"]}')
        if row['icu_message'] is not False or row['native_speaker_approval'] is not False:
            die(f'unexpected ICU/native-speaker field: {locale}:{row["source_id"]}')
        source_ph, target_ph = placeholders(row['source_id']), placeholders(value)
        if source_ph != target_ph or row['placeholders_source'] != source_ph or row['placeholders_target'] != target_ph:
            die(f'placeholder mismatch: {locale}:{row["source_id"]}')
        expected = CORRECTIONS.get((index, locale))
        if expected is None:
            if row['status'] != 'accepted' or row.get('proposed_target') is not None:
                die(f'unexpected fresh finding: {locale}:{row["source_id"]}')
        else:
            if row['status'] != 'correction-needed' or row.get('proposed_target') != expected:
                die(f'correction proposal mismatch: {locale}:{row["source_id"]}')
            if placeholders(expected) != source_ph or row.get('protected_literals_proposed_preserved') is not True:
                die(f'proposed target drops placeholder/literal: {locale}:{row["source_id"]}')
        if row['protected_literals_preserved'] is False and (index, locale) != (46, 'hi'):
            die(f'unexpected protected literal loss: {locale}:{row["source_id"]}')
        if any(unicodedata.category(char) == 'Cf' for text in [value, expected or ''] for char in text):
            die(f'unsafe format control: {locale}:{row["source_id"]}')
        if row['prior_exact_matches']:
            die(f'fresh decision has exact prior matches: {locale}:{row["source_id"]}')

        if index in {43, 48, 57} and ('FPS' not in value or not re.search(r'\b\d+ FPS\b', value)):
            die(f'FPS acronym or numeric cap missing: {locale}')
        if index in {44, 45} and '24' not in value:
            die(f'24-hour value missing: {locale}')
        if index == 46:
            if not all(part in value for part in ['255', '128', '64', '...']):
                die(f'RGBA example values missing: {locale}')
            if (locale == 'hi' and 'RGBA' in value) or (locale != 'hi' and 'RGBA' not in value):
                die(f'RGBA literal flag mismatch: {locale}')
            if locale == 'hi' and 'RGBA' not in expected:
                die('Hindi proposed target does not preserve RGBA')
        if index in {47, 54, 56, 59, 62}:
            count = {47:'3',54:'4',56:'6',59:'7',62:'8'}[index]
            if count not in value:
                die(f'count missing for source index {index}: {locale}')
        if index in {50, 52, 53} and '30' not in value:
            die(f'30-unit value missing: {locale}')
        if index in {58, 60, 61}:
            count = '60' if index == 58 else '7'
            if count not in value:
                die(f'count missing for source index {index}: {locale}')

    expected_refs = manifest['language_references']
    if len(expected_refs) != 3 or not all(item.get('url') and item.get('supports') for item in expected_refs):
        die('language-reference metadata incomplete')
    for index, locale in [(54, 'ar'), (62, 'ar')]:
        if not corrections[(index, locale)].get('language_references'):
            die('Arabic numeral decision lacks language reference')
    if not any('Larousse' in item['title'] for item in manifest['language_references']):
        die('French musical term reference missing')
    expected_candidates = []
    for (index, locale), value in CORRECTIONS.items():
        row = corrections[(index, locale)]
        expected_candidates.append({'source_index':index,'locale':locale,'current':row['target_text'],
                                    'proposal':value,'issue_type':row['issue_type']})
    if manifest['correction_candidates'] != expected_candidates:
        die('manifest correction candidate list mismatch')

    context = manifest['source_context']
    if sha((bundle / context['file']).read_bytes()) != context['evidence_text_sha256']:
        die('source context evidence hash mismatch')
    for path, digest in context['sha256'].items():
        if sha(git(repo, 'show', f'{source}:{path}', raw=True)) != digest:
            die(f'source-context SHA-256 mismatch: {path}')
        if git(repo, 'rev-parse', f'{source}:{path}') != context['git_blob_ids'][path]:
            die(f'source-context Git blob mismatch: {path}')

    scan = [row for _, row in jsonl_records((bundle / 'prior-evidence-scan-manifest.jsonl').read_bytes())]
    overlap = manifest['prior_overlap_scan']
    if len(scan) != 718 or len(scan) != overlap['scanned_json_evidence_files']:
        die('prior overlap input count mismatch')
    scan_raw = (bundle / 'prior-evidence-scan-manifest.jsonl').read_bytes()
    if sha(scan_raw) != overlap['manifest_sha256']:
        die('prior overlap manifest SHA-256 mismatch')
    canonical = sha(json.dumps(sorted(scan, key=lambda item: (item['root'], item['path'])),
                               sort_keys=True, separators=(',', ':')).encode('utf-8'))
    if canonical != overlap['canonical_input_manifest_sha256']:
        die('canonical overlap input hash mismatch')

    refs = collections.defaultdict(list)
    for entry in scan:
        root, relative = entry['root'], Path(entry['path'])
        if relative.is_absolute() or '..' in relative.parts:
            die('unsafe prior-input path')
        if root == 'prior-audit-7ff':
            base = audit
        elif root == 'pr-review-head':
            base = repo
        else:
            die(f'unknown prior evidence root: {root}')
        raw = (base / relative).read_bytes()
        if len(raw) != entry['bytes'] or sha(raw) != entry['sha256']:
            die(f'prior input hash mismatch: {root}:{relative.as_posix()}')
        for line_number, record in records_for(relative, raw):
            source_id = record.get('source_id') or record.get('message_id') or record.get('id')
            locale = record.get('locale')
            if source_id not in source_window or locale not in LOCALES:
                continue
            status = str(record.get('status') or record.get('review_outcome') or '').strip().lower().replace('_', '-')
            if status not in TERMINAL:
                continue
            selected = selection_by_key[(source_id, locale)]
            target_hash = record.get('target_sha256') or record.get('current_target_sha256')
            if record.get('source_sha256') != selected['source_sha256'] or target_hash != selected['target_sha256']:
                continue
            refs[(source_id, locale)].append({'status':status,'batch':record.get('batch'),'finding_id':record.get('finding_id'),
                'root':root,'path':relative.as_posix(),'line':line_number})

    for row in selection:
        actual = sorted(refs.get(cell_key(row), []), key=lambda item: (item['root'], item['path'], item['line'], item['status']))
        recorded = sorted(row['prior_exact_matches'], key=lambda item: (item['root'], item['path'], item['line'], item['status']))
        if actual != recorded:
            die(f'exact prior references mismatch: {row["locale"]}:{row["source_id"]}')
        statuses = {item['status'] for item in actual}
        if row['selection_disposition'] == 'fresh-decision' and statuses:
            die(f'fresh cell overlaps exact terminal evidence: {row["locale"]}:{row["source_id"]}')
        if row['selection_disposition'] == 'exact-accepted-carry' and statuses != {'accepted'}:
            die(f'accepted carry mismatch: {row["locale"]}:{row["source_id"]}')
        if row['selection_disposition'] == 'exact-terminal-exclusion' and statuses != {row['status']}:
            die(f'terminal exclusion mismatch: {row["locale"]}:{row["source_id"]}')

    sums = {}
    for line in (bundle / 'SHA256SUMS').read_text(encoding='utf-8').splitlines():
        match = re.fullmatch(r'([0-9a-f]{64})  (.+)', line)
        if not match:
            die('invalid SHA256SUMS line')
        sums[match.group(2)] = match.group(1)
    expected_sums = {path.name: sha(path.read_bytes()) for path in bundle.iterdir()
                     if path.is_file() and path.name != 'SHA256SUMS'}
    if sums != expected_sums:
        die('SHA256SUMS mismatch')

    final = collections.Counter(fresh_counts)
    final.update(prior_counts)
    print(json.dumps({'result':'PASS','review_head':head,'review_tree':tree,'source_catalog_head':source,
      'source_catalog_tree':source_tree,'source_keys':20,'cell_slots':240,'populated_catalog_cells':populated,
      'fresh_decisions':dict(fresh_counts),'prior_exact':dict(prior_counts),'final_dispositions':dict(final),
      'overlap_inputs_rehashed':len(scan),'bundle_files_hashed':len(sums)},ensure_ascii=False,indent=2))


if __name__ == '__main__':
    main()
