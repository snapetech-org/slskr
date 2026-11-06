#!/usr/bin/env python3
"""Verify exact-head semantic-review evidence for slskR lexical indices 20–39."""
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
        return [(n + 1, row) for n, row in enumerate(walk_json(value))]
    die(f'unsupported prior evidence input type: {path}')


def key(row):
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
    changed = git(repo, 'diff', '--name-only', source, head).splitlines()
    if any(not path.startswith('docs/') for path in changed):
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
                die(f'blank target in {locale}')
            populated += 1
    if len(set(map(frozenset, keysets.values()))) != 1 or len(next(iter(keysets.values()))) != 5437:
        die('locale source-key inventories differ')
    source_ids = sorted(next(iter(keysets.values())))
    if populated != 65244 or structured != 15:
        die(f'catalog population/plural inventory mismatch: {populated} populated, {structured} structured')

    selection = [row for _, row in jsonl_records((bundle / 'selection.jsonl').read_bytes())]
    decisions = [row for _, row in jsonl_records((bundle / 'decisions.jsonl').read_bytes())]
    carries = [row for _, row in jsonl_records((bundle / 'carries.jsonl').read_bytes())]
    exclusions = [row for _, row in jsonl_records((bundle / 'terminal-exclusions.jsonl').read_bytes())]
    if (len(selection), len(decisions), len(carries), len(exclusions)) != (240, 71, 138, 31):
        die('window row counts mismatch')
    for rows, name in [(selection, 'selection'), (decisions, 'decisions'),
                       (carries, 'carries'), (exclusions, 'exclusions')]:
        pairs = [key(row) for row in rows]
        if len(pairs) != len(set(pairs)):
            die(f'duplicate current cell in {name}')
    if {key(row) for row in selection} != {key(row) for row in decisions + carries + exclusions}:
        die('selection does not partition into fresh decisions, carries, and exclusions')
    source_window = sorted({row['source_id'] for row in selection})
    if [source_ids.index(source_id) for source_id in source_window] != list(range(20, 40)):
        die('selected keys are not lexical indices 20–39')
    selection_by_key = {key(row): row for row in selection}
    for row in selection:
        locale, source_id = row['locale'], row['source_id']
        if locale not in LOCALES or not row['populated']:
            die(f'unpopulated or unsupported selection: {locale}:{source_id}')
        value = catalogs[locale].get(source_id, '__MISSING__')
        if value == '__MISSING__' or value != row['target_text']:
            die(f'current target mismatch: {locale}:{source_id}')
        if target_sha(value) != row['target_sha256'] or row['source_sha256'] != sha(source_id.encode('utf-8')):
            die(f'source/target hash mismatch: {locale}:{source_id}')
        if source_ids.index(source_id) != row['source_index']:
            die(f'lexical source index mismatch: {source_id!r}')

    fresh_counts = collections.Counter(row['status'] for row in decisions)
    prior_counts = collections.Counter(row['status'] for row in carries + exclusions)
    if fresh_counts != collections.Counter({'accepted': 71}):
        die(f'fresh status counts mismatch: {dict(fresh_counts)}')
    if prior_counts != collections.Counter({'accepted': 138, 'correction-needed': 31}):
        die(f'prior status counts mismatch: {dict(prior_counts)}')

    expected_indices = {20, 21, 22, 23, 24, 25, 26, 27, 29, 30, 35, 36, 37, 38}
    if {row['source_index'] for row in decisions} != expected_indices:
        die('fresh decision source-index set mismatch')
    for row in decisions:
        index, locale, value = row['source_index'], row['locale'], row['target_text']
        if (row['review_head'], row['review_tree'], row['reviewed_code_head'], row['reviewed_code_tree']) != (head, tree, source, source_tree):
            die(f'fresh decision pin mismatch: {locale}:{row["source_id"]}')
        if not row['current_target_sha256_revalidated'] or not row['populated'] or not row['source_context_files_reviewed']:
            die(f'incomplete fresh decision: {locale}:{row["source_id"]}')
        if row['status'] != 'accepted' or row.get('proposed_target') is not None:
            die(f'unexpected fresh disposition/proposal: {locale}:{row["source_id"]}')
        if row['icu_message'] is not False or row['native_speaker_approval'] is not False:
            die(f'unexpected ICU/native-speaker field: {locale}:{row["source_id"]}')
        source_placeholders, target_placeholders = placeholders(row['source_id']), placeholders(value)
        if (source_placeholders != target_placeholders or row['placeholders_source'] != source_placeholders
                or row['placeholders_target'] != target_placeholders or not row['placeholders_preserved']):
            die(f'placeholder mismatch: {locale}:{row["source_id"]}')
        if not row['protected_literals_preserved']:
            die(f'protected literal flagged missing: {locale}:{row["source_id"]}')
        if any(unicodedata.category(char) == 'Cf' for char in value):
            die(f'unsafe format control: {locale}:{row["source_id"]}')
        if row['prior_exact_matches']:
            die(f'fresh cell has exact prior terminal overlap: {locale}:{row["source_id"]}')

        if index in {20, 21} and not value.startswith('-'):
            die(f'security list marker missing: {locale}:{row["source_id"]}')
        if index == 22 and (not value.startswith('-> ') or '{endSeconds}' not in value or not value.endswith('s')):
            die(f'chapter-end arrow/placeholder/unit missing: {locale}')
        if index == 23 and (not value.startswith('-> ') or '{targetPort}' not in value):
            die(f'port arrow/placeholder missing: {locale}')
        if index == 24 and locale == 'de' and not all(token in value for token in ['. ', 'Alle Pod-Workflows anzeigen', 'Zurücksetzen', 'MediaCore-Pod-Oberfläche']):
            die('German MediaCore instruction is incomplete')
        if index == 25 and not value.startswith('. '):
            die(f'empty-state fragment punctuation missing: {locale}')
        if index == 26 and not value.startswith('...'):
            die(f'graph-node ellipsis missing: {locale}')
        if index == 27 and not value.startswith('0 '):
            die(f'zero-byte label lost zero: {locale}')
        if index == 29 and not all(token in value for token in ['0.1', '-0.2', '0.3', '...', '-1.0', '1.0', '(', ')']):
            die(f'audio sample/range marker missing: {locale}')
        if index == 30 and '1' not in value:
            die(f'one-hour numeric count missing: {locale}')
        if index == 35 and '15' not in value:
            die(f'15-second count missing: {locale}')
        if index == 36 and '16' not in value:
            die(f'16-beat count missing: {locale}')
        if index == 37 and '180' not in value:
            die(f'180-day count missing: {locale}')
        if index == 38 and '1' not in value:
            die(f'one-year count missing: {locale}')

    context = manifest['source_context']
    if sha((bundle / context['file']).read_bytes()) != context['evidence_text_sha256']:
        die('source context evidence text hash mismatch')
    for path, digest in context['sha256'].items():
        if sha(git(repo, 'show', f'{source}:{path}', raw=True)) != digest:
            die(f'source context file SHA-256 mismatch: {path}')
        if git(repo, 'rev-parse', f'{source}:{path}') != context['git_blob_ids'][path]:
            die(f'source context Git blob mismatch: {path}')

    scan = [row for _, row in jsonl_records((bundle / 'prior-evidence-scan-manifest.jsonl').read_bytes())]
    overlap = manifest['prior_overlap_scan']
    if len(scan) != 712 or len(scan) != overlap['scanned_json_evidence_files']:
        die('prior input manifest file count mismatch')
    scan_raw = (bundle / 'prior-evidence-scan-manifest.jsonl').read_bytes()
    if sha(scan_raw) != overlap['manifest_sha256']:
        die('prior input manifest SHA-256 mismatch')
    canonical = sha(json.dumps(sorted(scan, key=lambda item: (item['root'], item['path'])),
                               sort_keys=True, separators=(',', ':')).encode('utf-8'))
    if canonical != overlap['canonical_input_manifest_sha256']:
        die('canonical prior input manifest hash mismatch')

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
            die(f'unknown input root {root}')
        raw = (base / relative).read_bytes()
        if len(raw) != entry['bytes'] or sha(raw) != entry['sha256']:
            die(f'prior input content mismatch: {root}:{relative.as_posix()}')
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
            refs[(source_id, locale)].append({'status': status, 'batch': record.get('batch'),
                'finding_id': record.get('finding_id'), 'root': root, 'path': relative.as_posix(), 'line': line_number})

    for row in selection:
        actual = sorted(refs.get(key(row), []), key=lambda item: (item['root'], item['path'], item['line'], item['status']))
        recorded = sorted(row['prior_exact_matches'], key=lambda item: (item['root'], item['path'], item['line'], item['status']))
        if actual != recorded:
            die(f'exact prior references mismatch: {row["locale"]}:{row["source_id"]}')
        statuses = {item['status'] for item in actual}
        if row['selection_disposition'] == 'fresh-decision' and statuses:
            die(f'fresh decision overlaps terminal evidence: {row["locale"]}:{row["source_id"]}')
        if row['selection_disposition'] == 'exact-accepted-carry' and statuses != {'accepted'}:
            die(f'accepted carry status mismatch: {row["locale"]}:{row["source_id"]}')
        if row['selection_disposition'] == 'exact-terminal-exclusion' and statuses != {row['status']}:
            die(f'terminal exclusion status mismatch: {row["locale"]}:{row["source_id"]}')

    sums = {}
    for line in (bundle / 'SHA256SUMS').read_text(encoding='utf-8').splitlines():
        match = re.fullmatch(r'([0-9a-f]{64})  (.+)', line)
        if not match:
            die('invalid checksum line')
        sums[match.group(2)] = match.group(1)
    expected_sums = {path.name: sha(path.read_bytes()) for path in bundle.iterdir()
                     if path.is_file() and path.name != 'SHA256SUMS'}
    if sums != expected_sums:
        die('SHA256SUMS mismatch')

    final = collections.Counter(fresh_counts)
    final.update(prior_counts)
    print(json.dumps({'result':'PASS','review_head':head,'review_tree':tree,
      'source_catalog_head':source,'source_catalog_tree':source_tree,'source_keys':20,'cell_slots':240,
      'populated_catalog_cells':populated,'fresh_decisions':dict(fresh_counts),'prior_exact':dict(prior_counts),
      'final_dispositions':dict(final),'overlap_inputs_rehashed':len(scan),'bundle_files_hashed':len(sums)},ensure_ascii=False,indent=2))


if __name__ == '__main__':
    main()
