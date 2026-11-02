#!/usr/bin/env python3
"""Verify exact-hash high-confidence semantic corrections in slskR PR #204."""
import argparse
import collections
import hashlib
import json
import re
import subprocess
from pathlib import Path

BASE = 'cb1fc0c0d51ff6cf136862429530399755763bb3'
LOCALES = ['ar', 'de', 'es', 'fr', 'hi', 'id', 'ja', 'ko', 'pt-BR', 'vi', 'zh-Hans', 'zh-Hant']


def fail(message):
    raise SystemExit('FAIL: ' + message)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def git(repo, *args, raw=False):
    proc = subprocess.run(['git', *args], cwd=repo, check=True, stdout=subprocess.PIPE)
    return proc.stdout if raw else proc.stdout.decode('utf-8').strip()


def target_sha(value):
    return sha(value.encode('utf-8'))


def placeholders(value):
    return sorted(set(re.findall(r'\{([^{}]+)\}', value)))

def nonempty(value):
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, dict):
        return bool(value) and all(nonempty(child) for child in value.values())
    if isinstance(value, list):
        return bool(value) and all(nonempty(child) for child in value)
    return False


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path, default=Path.cwd())
    repo = parser.parse_args().repo.resolve()
    bundle = Path(__file__).resolve().parent
    manifest = json.loads((bundle / 'manifest.json').read_text(encoding='utf-8'))
    if git(repo, 'cat-file', '-e', f'{BASE}^{{commit}}') is None:
        fail('application parent commit missing')
    if git(repo, 'rev-parse', f'{BASE}^{{tree}}') != manifest['application_parent_tree']:
        fail('application parent tree mismatch')
    current_head = git(repo, 'rev-parse', 'HEAD')
    rows = [json.loads(line) for line in (bundle / 'applied-corrections.jsonl').read_text(encoding='utf-8').splitlines() if line.strip()]
    if len(rows) != 11 or manifest['applied_corrections'] != 11:
        fail('correction row count mismatch')
    keys = [(row['source_id'], row['locale']) for row in rows]
    if len(set(keys)) != len(keys):
        fail('duplicate corrected source/locale cell')
    if any(row.get('status') != 'corrected' or row.get('confidence') != 'high' for row in rows):
        fail('non-high-confidence or non-corrected row present')
    if manifest.get('moderate_confidence_suggestions_applied') != 0:
        fail('manifest says a moderate suggestion was applied')

    before_catalogs = {}
    after_catalogs = {}
    structured = collections.Counter()
    for locale in LOCALES:
        path = f'web/src/lib/locales/ui-labels.{locale}.json'
        before_raw = git(repo, 'show', f'{BASE}:{path}', raw=True)
        after_raw = git(repo, 'show', f'HEAD:{path}', raw=True)
        if sha(before_raw) != manifest['catalog_sha256_before'][path]:
            fail(f'before catalog hash mismatch: {locale}')
        if sha(after_raw) != manifest['catalog_sha256_after'][path]:
            fail(f'after catalog hash mismatch: {locale}')
        before_catalogs[locale] = json.loads(before_raw.decode('utf-8'))
        after_catalogs[locale] = json.loads(after_raw.decode('utf-8'))
        if set(before_catalogs[locale]) != set(after_catalogs[locale]) or len(after_catalogs[locale]) != 5437:
            fail(f'catalog key inventory changed: {locale}')
        for value in after_catalogs[locale].values():
            if isinstance(value, (dict, list)):
                structured[locale] += 1
            if not nonempty(value):
                fail(f'blank catalog value: {locale}')
    if structured != collections.Counter({'ar': 15}):
        fail(f'unexpected structured plural inventory: {dict(structured)}')

    expected = {}
    for row in rows:
        locale = row['locale']
        source_id = row['source_id']
        before = before_catalogs[locale].get(source_id)
        after = after_catalogs[locale].get(source_id)
        if before != row['previous_target'] or sha(before.encode('utf-8')) != row['previous_target_sha256']:
            fail(f'previous target hash mismatch: {locale}:{source_id}')
        if after != row['current_target'] or target_sha(after) != row['target_sha256']:
            fail(f'current target hash mismatch: {locale}:{source_id}')
        if row['source_sha256'] != sha(source_id.encode('utf-8')):
            fail(f'source hash mismatch: {locale}:{source_id}')
        if placeholders(source_id) != placeholders(before) or placeholders(source_id) != placeholders(after):
            fail(f'placeholder changed: {locale}:{source_id}')
        if row.get('application_parent_head') != BASE:
            fail(f'application parent mismatch: {locale}:{source_id}')
        ref = row['review_evidence']
        lines = (repo / ref['path']).read_text(encoding='utf-8').splitlines()
        decision = json.loads(lines[ref['line'] - 1])
        if (decision.get('status'), decision.get('confidence'), decision.get('source_id'), decision.get('locale'),
            decision.get('source_sha256'), decision.get('target_sha256'), decision.get('proposed_target')) != (
            'correction-needed', 'high', source_id, locale, row['source_sha256'], row['previous_target_sha256'], row['current_target']):
            fail(f'original high-confidence decision mismatch: {locale}:{source_id}')
        expected[(source_id, locale)] = (before, after)

    all_diffs = set()
    for locale in LOCALES:
        before, after = before_catalogs[locale], after_catalogs[locale]
        for source_id in before:
            if before[source_id] != after[source_id]:
                all_diffs.add((source_id, locale))
    if all_diffs != set(expected):
        fail('catalog changes include missing or unexpected cells')
    if manifest['catalog_values_changed_only_for_ledger_cells'] is not True:
        fail('manifest does not attest to exact-only catalog edits')

    raw_ledger = (bundle / 'applied-corrections.jsonl').read_bytes()
    if sha(raw_ledger) != manifest['correction_ledger_sha256']:
        fail('correction ledger hash mismatch')
    counts = dict(collections.Counter(row['locale'] for row in rows))
    if counts != manifest['per_locale_counts']:
        fail('per-locale correction counts mismatch')
    checksum_lines = (bundle / 'SHA256SUMS').read_text(encoding='utf-8').splitlines()
    sums = {}
    for line in checksum_lines:
        match = re.fullmatch(r'([0-9a-f]{64})  (.+)', line)
        if not match:
            fail('invalid checksum line')
        sums[match.group(2)] = match.group(1)
    expected_sums = {p.name: sha(p.read_bytes()) for p in bundle.iterdir() if p.is_file() and p.name != 'SHA256SUMS'}
    if sums != expected_sums:
        fail('bundle checksum mismatch')
    print(json.dumps({'result': 'PASS', 'application_parent_head': BASE, 'verified_current_head': current_head,
                      'corrected_cells': len(rows), 'per_locale': counts, 'changed_catalog_cells': len(all_diffs),
                      'catalogs_changed': [locale for locale in LOCALES if manifest['catalog_sha256_before'][f'web/src/lib/locales/ui-labels.{locale}.json'] != manifest['catalog_sha256_after'][f'web/src/lib/locales/ui-labels.{locale}.json']]}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
