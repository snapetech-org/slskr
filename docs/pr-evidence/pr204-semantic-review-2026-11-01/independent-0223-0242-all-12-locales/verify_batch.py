#!/usr/bin/env python3
"""Verify exact-head semantic evidence for slskR source indices 223–242."""
import argparse
import collections
import hashlib
import json
import re
import subprocess
from pathlib import Path

LOCALES = ['ar', 'de', 'es', 'fr', 'hi', 'id', 'ja', 'ko', 'pt-BR', 'vi', 'zh-Hans', 'zh-Hant']
TERMINAL = {'accepted', 'correction-needed', 'held', 'keep', 'corrected'}


def die(message):
    raise SystemExit('FAIL: ' + message)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def value_sha(value):
    raw = value.encode('utf-8') if isinstance(value, str) else json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(',', ':')
    ).encode('utf-8')
    return sha(raw)


def flat(value):
    if isinstance(value, dict):
        return ' '.join(flat(v) for v in value.values())
    if isinstance(value, list):
        return ' '.join(flat(v) for v in value)
    return str(value)


def placeholders(value):
    return sorted(set(re.findall(r'\{([^{}]+)\}', flat(value))))


def icu(value):
    return bool(re.search(r'\{\s*[A-Za-z_][\w.-]*\s*,\s*(plural|select|selectordinal)\s*,', flat(value)))


def git(repo, *args, raw=False):
    output = subprocess.run(['git', *args], cwd=repo, check=True, stdout=subprocess.PIPE).stdout
    return output if raw else output.decode('utf-8').strip()


def read_jsonl(path):
    return [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines() if line.strip()]


def walk(value):
    if isinstance(value, dict):
        yield value
        for item in value.values():
            yield from walk(item)
    elif isinstance(value, list):
        for item in value:
            yield from walk(item)


def records(raw, path):
    if Path(path).suffix == '.jsonl':
        for number, line in enumerate(raw.decode('utf-8').splitlines(), 1):
            if line.strip():
                try:
                    yield number, json.loads(line)
                except json.JSONDecodeError:
                    continue
    elif Path(path).suffix == '.json':
        try:
            for number, row in enumerate(walk(json.loads(raw.decode('utf-8'))), 1):
                yield number, row
        except json.JSONDecodeError:
            return


def pick(row, names):
    for name in names:
        if row.get(name) is not None:
            return row[name]
    return None


def normalize_status(value):
    return str(value or '').strip().lower().replace('_', '-')


def protected_literals(source_id):
    if source_id == 'Album ReplayGain after import':
        return ['ReplayGain']
    if source_id == 'Album / 01 - Artist - Title':
        return ['01', '/']
    return []


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path, required=True)
    parser.add_argument('--prior-audit', type=Path, required=True)
    args = parser.parse_args()
    repo = args.repo.resolve()
    prior_audit = args.prior_audit.resolve()
    bundle = Path(__file__).resolve().parent
    manifest = json.loads((bundle / 'manifest.json').read_text(encoding='utf-8'))
    review = manifest['review_head']
    application = manifest['application_head']
    source = manifest['source_catalog_head']

    for commit, tree_key in ((review, 'review_tree'), (application, 'application_tree'), (source, 'source_catalog_tree')):
        if git(repo, 'rev-parse', f'{commit}^{{tree}}') != manifest[tree_key]:
            die(f'commit/tree mismatch for {commit}')
    if git(repo, 'rev-parse', f'{application}^') != review:
        die('catalog application commit is not a direct child of exact review head')

    inventory = read_jsonl(prior_audit / 'frozen-inputs/source-inventory.jsonl')
    source_ids = [row['source_id'] for row in inventory]
    if len(source_ids) != 5437 or source_ids != sorted(source_ids):
        die('frozen source inventory mismatch')
    selected_ids = source_ids[223:243]
    if selected_ids != manifest['source_ids']:
        die('source-index selection mismatch')

    before = read_jsonl(bundle / 'selection-before-corrections.jsonl')
    final = read_jsonl(bundle / 'selection.jsonl')
    decisions = read_jsonl(bundle / 'decisions.jsonl')
    audits = read_jsonl(bundle / 'reviewed-cell-audit.jsonl')
    carries = read_jsonl(bundle / 'carries.jsonl')
    exclusions = read_jsonl(bundle / 'terminal-exclusions.jsonl')
    conflicts = read_jsonl(bundle / 'conflict-holds.jsonl')
    patches = read_jsonl(bundle / 'applied-corrections.jsonl')
    conflict_resolution = read_jsonl(bundle / 'conflict-reconciliation.jsonl')
    root_rows = read_jsonl(bundle / 'root-cross-review.jsonl')
    plan = read_jsonl(bundle / 'root-apply-plan.jsonl')
    candidates = read_jsonl(bundle / 'candidate-corrections.jsonl') + read_jsonl(bundle / 'candidate-supplement.jsonl')
    pair = lambda row: (row['source_id'], row['locale'])
    groups = (before, final, decisions, audits, carries, exclusions, conflicts, patches, conflict_resolution, root_rows, plan, candidates)
    names = ('baseline', 'final selection', 'fresh decisions', 'cell audit', 'carries', 'exclusions', 'conflicts', 'patches', 'conflict reconciliation', 'root review', 'root plan', 'candidates')
    for rows, name in zip(groups, names):
        if len({pair(row) for row in rows}) != len(rows):
            die(f'duplicate cell in {name}')
    if (len(before), len(final), len(decisions), len(audits), len(carries), len(exclusions), len(conflicts), len(patches), len(conflict_resolution), len(root_rows), len(plan), len(candidates)) != (240, 240, 89, 240, 132, 0, 0, 25, 1, 25, 25, 25):
        die('bundle row count mismatch')

    before_by = {pair(row): row for row in before}
    final_by = {pair(row): row for row in final}
    audit_by = {pair(row): row for row in audits}
    decision_by = {pair(row): row for row in decisions}
    patch_by = {pair(row): row for row in patches}
    root_by = {pair(row): row for row in root_rows}
    plan_by = {pair(row): row for row in plan}
    candidate_by = {pair(row): row for row in candidates}
    expected = {(source_id, locale) for source_id in selected_ids for locale in LOCALES}
    if set(before_by) != expected or set(final_by) != expected or set(audit_by) != expected:
        die('coverage is not exactly 20 source keys × 12 locales')
    if set(root_by) != set(plan_by) or set(root_by) != set(candidate_by):
        die('root review, candidate, and apply-plan key sets mismatch')
    if collections.Counter(row['disposition'] for row in root_rows) != {'accepted': 24, 'refined': 1}:
        die('root cross-review disposition totals mismatch')
    for key, root_row in root_by.items():
        candidate = candidate_by[key]
        plan_row = plan_by[key]
        if candidate['proposed_target'] != root_row['candidate_target'] or candidate['proposed_sha256'] != root_row['candidate_target_sha256']:
            die(f'candidate/root cross-review basis mismatch {key}')
        if plan_row['disposition'] != root_row['disposition'] or plan_row['final_target'] != root_row['final_target']:
            die(f'root apply plan mismatch {key}')
    if sha((bundle / 'root-cross-review.jsonl').read_bytes()) != manifest['root_cross_review_ledger_sha256']:
        die('root cross-review ledger checksum mismatch')
    if sha((bundle / 'root-apply-plan.jsonl').read_bytes()) != manifest['root_apply_plan_sha256']:
        die('root apply plan checksum mismatch')

    scan_rows = read_jsonl(bundle / 'prior-evidence-scan-manifest.jsonl')
    scan_raw = (bundle / 'prior-evidence-scan-manifest.jsonl').read_bytes()
    if len(scan_rows) != 810 or sha(scan_raw) != manifest['prior_overlap_scan']['manifest_file_sha256']:
        die('raw overlap input manifest mismatch')
    canonical = sha(json.dumps(sorted(scan_rows, key=lambda row: (row['root'], row['path'])), sort_keys=True, separators=(',', ':')).encode())
    if canonical != manifest['prior_overlap_scan']['canonical_manifest_sha256']:
        die('canonical overlap input manifest mismatch')
    prior = collections.defaultdict(list)
    for item in scan_rows:
        if item['root'] == 'prior-audit-7ff':
            raw = (prior_audit / item['path']).read_bytes()
        elif item['root'] == 'pr-review-head':
            raw = git(repo, 'show', f"{review}:{item['path']}", raw=True)
        else:
            die('unknown overlap evidence root')
        if len(raw) != item['bytes'] or sha(raw) != item['sha256']:
            die(f'raw prior evidence pin mismatch {item["root"]}:{item["path"]}')
        for line, row in records(raw, item['path']):
            source_id = pick(row, ['source_id', 'sourceId', 'message_id', 'id'])
            locale = row.get('locale')
            if not isinstance(source_id, str) or source_id not in selected_ids or locale not in LOCALES:
                continue
            status = normalize_status(pick(row, ['status', 'review_outcome', 'disposition']))
            if status not in TERMINAL:
                continue
            cell = before_by[(source_id, locale)]
            target_hash = pick(row, ['target_sha256', 'targetSha256', 'current_target_sha256'])
            if pick(row, ['source_sha256', 'sourceSha256']) == cell['source_sha256'] and target_hash == cell['target_sha256']:
                prior[(source_id, locale)].append({'status': status, 'root': item['root'], 'path': item['path'], 'line': line, 'batch': row.get('batch') or row.get('review_batch'), 'finding_id': row.get('finding_id')})

    before_catalogs = {}
    after_catalogs = {}
    changed = set()
    for locale in LOCALES:
        path = f'web/src/lib/locales/ui-labels.{locale}.json'
        raw_before = git(repo, 'show', f'{review}:{path}', raw=True)
        raw_after = git(repo, 'show', f'{application}:{path}', raw=True)
        if sha(raw_before) != manifest['catalog_sha256_before'][path] or sha(raw_after) != manifest['catalog_sha256_after'][path]:
            die(f'catalog file hash mismatch for {locale}')
        before_catalogs[locale] = json.loads(raw_before.decode('utf-8'))
        after_catalogs[locale] = json.loads(raw_after.decode('utf-8'))
        if set(before_catalogs[locale]) != set(source_ids) or set(after_catalogs[locale]) != set(source_ids):
            die(f'catalog key inventory mismatch in {locale}')
        for source_id in source_ids:
            old = before_catalogs[locale][source_id]
            new = after_catalogs[locale][source_id]
            if old != new:
                changed.add((source_id, locale))
            if new is None or (isinstance(new, str) and not new.strip()):
                die(f'blank catalog target {locale}:{source_id}')
    if changed != set(patch_by):
        die('catalog patch has unledgered/missing edits')

    for row in before:
        key = pair(row)
        current_matches = prior.get(key, [])
        statuses = sorted({item['status'] for item in current_matches})
        disposition = 'conflict' if len(statuses) > 1 else ('prior_' + statuses[0] if statuses else 'new')
        if row['prior_exact_matches'] != current_matches or row['disposition'] != disposition:
            die(f'exact overlap disposition mismatch {key}')
        if row['source_index'] != source_ids.index(row['source_id']) or row['source_sha256'] != value_sha(row['source_id']):
            die(f'source index/hash mismatch {key}')
        old = before_catalogs[key[1]][key[0]]
        new = after_catalogs[key[1]][key[0]]
        if old != row['target_text'] or value_sha(old) != row['target_sha256']:
            die(f'baseline target mismatch {key}')
        plan_row = plan_by.get(key)
        final_row = final_by[key]
        audit = audit_by[key]
        patch = patch_by.get(key)
        if plan_row:
            if patch is None or new != plan_row['final_target'] or value_sha(new) != plan_row['final_target_sha256']:
                die(f'application plan/target mismatch {key}')
            if patch['source_sha256'] != row['source_sha256'] or patch['prior_target_sha256'] != row['target_sha256'] or patch['current_target_sha256'] != value_sha(new):
                die(f'exact application basis mismatch {key}')
            if patch['application_head'] != application or patch['application_tree'] != manifest['application_tree'] or patch['application_parent'] != review:
                die(f'application commit pin mismatch {key}')
            if patch['root_disposition'] != root_by[key]['disposition'] or patch['target'] != root_by[key]['final_target']:
                die(f'root review target mismatch {key}')
            if root_by[key]['source_sha256'] != row['source_sha256'] or root_by[key]['baseline_target_sha256'] != row['target_sha256']:
                die(f'root review old/source hash mismatch {key}')
            if root_by[key]['review_head'] != review or root_by[key]['review_tree'] != manifest['review_tree']:
                die(f'root review head mismatch {key}')
            expected_status = 'corrected'
            if final_row['decision'] != ('corrected' if row['disposition'] == 'new' else 'corrected-prior-accepted' if row['disposition'] == 'prior_accepted' else 'corrected-prior'):
                die(f'final correction classification mismatch {key}')
        else:
            if new != old or final_row['decision'] != ('accepted' if row['disposition'] == 'new' else 'accepted-carry'):
                die(f'unledgered change or carry moved {key}')
            expected_status = 'accepted'
        if final_row['target_text'] != new or final_row['target_sha256'] != value_sha(new) or audit['target_text'] != new or audit['target_sha256'] != value_sha(new):
            die(f'final selection/audit value mismatch {key}')
        if final_row['status'] != expected_status or audit['status'] != expected_status:
            die(f'final terminal status mismatch {key}')
        if audit['placeholders_source'] != placeholders(row['source_id']) or audit['placeholders_target'] != placeholders(new) or not audit['placeholders_preserved']:
            die(f'placeholder preservation mismatch {key}')
        if audit['icu_message_source'] != icu(row['source_id']) or audit['icu_message_target'] != icu(new):
            die(f'ICU classification mismatch {key}')
        if audit['icu_message_source'] or audit['icu_message_target'] or not audit['protected_literals_checked'] or not audit['protected_literals_preserved']:
            die(f'ICU/protected-literal check failed {key}')
        if audit['review_head'] != review or audit['review_tree'] != manifest['review_tree'] or audit['source_catalog_head'] != source or audit['source_catalog_tree'] != manifest['source_catalog_tree']:
            die(f'review/source pin mismatch {key}')
        if not audit['reviewed_context'] or not audit['semantic_review_result']:
            die(f'semantic/context evidence missing {key}')
        if row['disposition'] == 'new':
            decision = decision_by.get(key)
            if decision is None or decision['baseline_target_text'] != old or decision['reviewed_target_after'] != new or decision['fresh_disposition'] != expected_status:
                die(f'fresh-cell decision mismatch {key}')
        if row['disposition'] == 'prior_accepted' and patch is None and final_row['decision'] != 'accepted-carry':
            die(f'accepted carry disposition mismatch {key}')
        if row['disposition'] == 'prior_correction-needed' and patch is None:
            die(f'prior correction-needed cell remains unresolved {key}')

    if {pair(row) for row in decisions} != {pair(row) for row in before if row['disposition'] == 'new'}:
        die('fresh decision membership mismatch')
    if {pair(row) for row in carries} != {pair(row) for row in before if row['disposition'] == 'prior_accepted' and pair(row) not in patch_by}:
        die('carry membership mismatch')
    if {pair(row) for row in exclusions} != {pair(row) for row in before if row['disposition'] == 'prior_correction-needed' and pair(row) not in patch_by}:
        die('terminal exclusion membership mismatch')
    if {pair(row) for row in conflicts}:
        die('unresolved conflict holds remain')
    special = ('Algorithm Accuracy:', 'pt-BR')
    resolution = conflict_resolution[0]
    if pair(resolution) != special or resolution['prior_status'] != 'prior_accepted' or resolution['current_status'] != 'corrected' or special not in patch_by:
        die('prior-accepted root reconciliation mismatch')
    if resolution['root_cross_review_sha256'] != sha((bundle / 'root-cross-review.jsonl').read_bytes()):
        die('root reconciliation ledger hash mismatch')

    source_context = manifest['source_context']
    context_raw = (bundle / source_context['file']).read_bytes()
    if sha(context_raw) != source_context['evidence_text_sha256']:
        die('source context evidence hash mismatch')
    source_pins = json.loads((bundle / 'source-pins.json').read_text(encoding='utf-8'))
    for path, digest in source_pins['sha256'].items():
        raw = git(repo, 'show', f'{source}:{path}', raw=True)
        if sha(raw) != digest or git(repo, 'rev-parse', f'{source}:{path}') != source_pins['git_blob_ids'][path]:
            die(f'source context Git pin mismatch {path}')
    visual = manifest['visual_check']
    if visual['status'] != 'blocked' or sha((bundle / visual['file']).read_bytes()) != visual['sha256'] or not manifest['browser_recapture_required']:
        die('headed visual blocker mismatch')
    if manifest['placeholder_and_literal_checks'] != {'cells_checked': 240, 'placeholder_sets_preserved': True, 'icu_messages': 0, 'protected_literals_checked': True, 'protected_literals_changed': 0}:
        die('placeholder/literal census mismatch')
    expected_sums = [f'{sha(path.read_bytes())}  {path.name}' for path in sorted(bundle.iterdir()) if path.is_file() and path.name != 'SHA256SUMS']
    if (bundle / 'SHA256SUMS').read_text(encoding='utf-8').splitlines() != expected_sums:
        die('bundle checksum list mismatch')
    print('PASS: 240 exact cells; 89 fresh (83 accepted, 6 corrected), 132 accepted carries, 18 prior corrections and 1 prior-accepted target reconciled; all 25 root-reviewed corrections applied; zero remaining holds/conflicts. Verified all 810 raw overlap inputs, exact source/current/final hashes, 17 source caller blobs, placeholders/ICU/literals, and bundle checksums.')


if __name__ == '__main__':
    main()
