#!/usr/bin/env python3
"""Verify exact-head semantic evidence for slskR source indices 243–262."""
import argparse
import collections
import hashlib
import json
import re
import subprocess
from pathlib import Path

LOCALES = ['ar', 'de', 'es', 'fr', 'hi', 'id', 'ja', 'ko', 'pt-BR', 'vi', 'zh-Hans', 'zh-Hant']
TERMINAL = {'accepted', 'corrected', 'correction-needed', 'held', 'keep'}
ALIASES = {
    'source_id': ['source_id', 'sourceId', 'message_id', 'id'],
    'source_sha': ['source_sha256', 'sourceSha256'],
    'target_sha': ['target_sha256', 'targetSha256', 'current_target_sha256'],
    'status': ['status', 'review_outcome', 'disposition'],
}


def die(message):
    raise SystemExit('FAIL: ' + message)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def value_sha(value):
    raw = value.encode('utf-8') if isinstance(value, str) else json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(',', ':')
    ).encode('utf-8')
    return sha(raw)


def pick(row, names):
    for name in names:
        if row.get(name) is not None:
            return row[name]
    return None


def normalize_status(value):
    return str(value or '').strip().lower().replace('_', '-')


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


def parse_evidence(raw, path):
    if Path(path).suffix == '.jsonl':
        for number, line in enumerate(raw.decode('utf-8').splitlines(), 1):
            if line.strip():
                try:
                    yield number, json.loads(line)
                except json.JSONDecodeError:
                    continue
    elif Path(path).suffix == '.json':
        try:
            yield from enumerate(walk(json.loads(raw.decode('utf-8'))), 1)
        except json.JSONDecodeError:
            return


def git(repo, *args, raw=False):
    result = subprocess.run(['git', *args], cwd=repo, check=True, stdout=subprocess.PIPE)
    return result.stdout if raw else result.stdout.decode('utf-8').strip()


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
    review_tree = manifest['review_tree']
    application_tree = manifest['application_tree']
    source_tree = manifest['source_catalog_tree']

    for commit, expected_tree in ((review, review_tree), (application, application_tree), (source, source_tree)):
        if git(repo, 'rev-parse', f'{commit}^{{tree}}') != expected_tree:
            die(f'commit/tree mismatch for {commit}')
    if git(repo, 'rev-parse', f'{application}^') != review:
        die('catalog application commit is not a direct child of exact review head')

    inventory_path = prior_audit / 'frozen-inputs/source-inventory.jsonl'
    inventory_raw = inventory_path.read_bytes()
    if sha(inventory_raw) != manifest['frozen_source_inventory_sha256']:
        die('frozen source inventory checksum mismatch')
    inventory = read_jsonl(inventory_path)
    source_ids = [row['source_id'] for row in inventory]
    if len(source_ids) != manifest['source_key_count'] or source_ids != sorted(source_ids):
        die('frozen source inventory mismatch')
    selected_ids = source_ids[manifest['source_index_start']:manifest['source_index_end_inclusive'] + 1]
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
    roots = read_jsonl(bundle / 'root-cross-review.jsonl')
    plan = read_jsonl(bundle / 'root-apply-plan.jsonl')
    candidates = read_jsonl(bundle / 'candidate-corrections.jsonl')
    recon = read_jsonl(bundle / 'conflict-reconciliation.jsonl')
    pair = lambda row: (row['source_id'], row['locale'])
    groups = (before, final, decisions, audits, carries, exclusions, conflicts, patches, roots, plan, candidates, recon)
    names = ('baseline', 'final selection', 'fresh decisions', 'cell audit', 'carries', 'exclusions', 'conflicts', 'patches', 'root review', 'root plan', 'candidates', 'conflict reconciliation')
    for rows, name in zip(groups, names):
        if len({pair(row) for row in rows}) != len(rows):
            die(f'duplicate cell in {name}')
    expected_counts = (240, 240, 90, 240, 78, 0, 0, 83, 83, 83, 83, 0)
    if tuple(map(len, groups)) != expected_counts:
        die(f'bundle row count mismatch: got {tuple(map(len, groups))}')

    before_by = {pair(row): row for row in before}
    final_by = {pair(row): row for row in final}
    audit_by = {pair(row): row for row in audits}
    decision_by = {pair(row): row for row in decisions}
    patch_by = {pair(row): row for row in patches}
    root_by = {pair(row): row for row in roots}
    plan_by = {pair(row): row for row in plan}
    candidate_by = {pair(row): row for row in candidates}
    expected = {(source_id, locale) for source_id in selected_ids for locale in LOCALES}
    if set(before_by) != expected or set(final_by) != expected or set(audit_by) != expected:
        die('coverage is not exactly 20 source keys × 12 locales')
    if set(root_by) != set(plan_by) or set(root_by) != set(candidate_by):
        die('root review, candidate, and apply-plan key sets mismatch')
    if collections.Counter(row['disposition'] for row in roots) != {'accepted-proposal': 71, 'refined': 12}:
        die('root cross-review disposition totals mismatch')
    for key, root_row in root_by.items():
        candidate = candidate_by[key]
        plan_row = plan_by[key]
        if candidate['proposed_target'] != root_row['candidate_target'] or candidate['proposed_sha256'] != root_row['candidate_target_sha256']:
            die(f'candidate/root basis mismatch {key}')
        if candidate['baseline_target_sha256'] != root_row['baseline_target_sha256'] or candidate['source_sha256'] != root_row['source_sha256']:
            die(f'candidate/root baseline pin mismatch {key}')
        if plan_row['disposition'] != root_row['disposition'] or plan_row['final_target'] != root_row['final_target'] or plan_row['final_target_sha256'] != root_row['final_target_sha256']:
            die(f'root apply plan mismatch {key}')
    if sha((bundle / 'root-cross-review.jsonl').read_bytes()) != manifest['root_cross_review_ledger_sha256']:
        die('root cross-review ledger checksum mismatch')
    if sha((bundle / 'root-apply-plan.jsonl').read_bytes()) != manifest['root_apply_plan_sha256']:
        die('root apply plan checksum mismatch')
    if sha((bundle / 'candidate-corrections.jsonl').read_bytes()) != manifest['candidate_ledger_sha256']:
        die('candidate ledger checksum mismatch')

    scan_rows = read_jsonl(bundle / 'prior-evidence-scan-manifest.jsonl')
    scan_raw = (bundle / 'prior-evidence-scan-manifest.jsonl').read_bytes()
    if len(scan_rows) != manifest['prior_overlap_scan']['input_count'] or len(scan_rows) != 826 or sha(scan_raw) != manifest['prior_overlap_scan']['manifest_file_sha256']:
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
        for line, row in parse_evidence(raw, item['path']):
            source_id = pick(row, ALIASES['source_id'])
            locale = row.get('locale')
            if not isinstance(source_id, str) or source_id not in selected_ids or locale not in LOCALES:
                continue
            status = normalize_status(pick(row, ALIASES['status']))
            if status not in TERMINAL:
                continue
            cell = before_by[(source_id, locale)]
            if pick(row, ALIASES['source_sha']) == cell['source_sha256'] and pick(row, ALIASES['target_sha']) == cell['target_sha256']:
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
        root_row = root_by.get(key)
        plan_row = plan_by.get(key)
        patch = patch_by.get(key)
        final_row = final_by[key]
        audit = audit_by[key]
        decision = decision_by.get(key)
        if plan_row:
            if patch is None or root_row is None or candidate_by.get(key) is None:
                die(f'missing reviewed application rows {key}')
            if new != plan_row['final_target'] or value_sha(new) != plan_row['final_target_sha256']:
                die(f'application plan/target mismatch {key}')
            if patch['source_sha256'] != row['source_sha256'] or patch['baseline_target_sha256'] != row['target_sha256'] or patch['current_target_sha256'] != value_sha(new):
                die(f'exact application hash basis mismatch {key}')
            if patch['application_head'] != application or patch['application_tree'] != application_tree or patch['application_parent'] != review:
                die(f'application commit pin mismatch {key}')
            if root_row['final_target'] != new or root_row['final_target_sha256'] != value_sha(new):
                die(f'root cross-review target mismatch {key}')
            if root_row['source_sha256'] != row['source_sha256'] or root_row['baseline_target_sha256'] != row['target_sha256']:
                die(f'root review old/source hash mismatch {key}')
            if root_row['review_head'] != review or root_row['review_tree'] != review_tree:
                die(f'root review head mismatch {key}')
            expected_decision = 'corrected' if row['disposition'] == 'new' else 'corrected-prior'
            expected_status = 'corrected'
            if row['disposition'] not in ('new', 'prior_correction-needed'):
                die(f'correction applied to a non-correction disposition {key}')
            if patch['root_disposition'] != root_row['disposition']:
                die(f'patch/root disposition mismatch {key}')
        else:
            if new != old:
                die(f'unledgered catalog edit {key}')
            expected_decision = 'accepted' if row['disposition'] == 'new' else 'accepted-carry'
            expected_status = 'accepted'
            if row['disposition'] not in ('new', 'prior_accepted'):
                die(f'unresolved or invalid exact status {key}')
        if final_row['decision'] != expected_decision or final_row['status'] != expected_status:
            die(f'final selection disposition mismatch {key}')
        if final_row['target_text'] != new or final_row['target_sha256'] != value_sha(new):
            die(f'final selection target mismatch {key}')
        if audit['status'] != expected_status or audit['target_text'] != new or audit['target_sha256'] != value_sha(new):
            die(f'full audit target/status mismatch {key}')
        source_placeholders = sorted(set(re.findall(r'\{([^{}]+)\}', row['source_id'])))
        target_placeholders = sorted(set(re.findall(r'\{([^{}]+)\}', new)))
        if source_placeholders != target_placeholders or audit['placeholders_source'] != source_placeholders or audit['placeholders_target'] != target_placeholders or not audit['placeholders_preserved']:
            die(f'placeholder preservation mismatch {key}')
        icu_re = r'\{\s*[A-Za-z_][\w.-]*\s*,\s*(plural|select|selectordinal)\s*,'
        source_icu = bool(re.search(icu_re, row['source_id']))
        target_icu = bool(re.search(icu_re, new))
        if audit['icu_message_source'] != source_icu or audit['icu_message_target'] != target_icu:
            die(f'ICU classification mismatch {key}')
        if source_icu or target_icu or not audit['protected_literals_checked'] or not audit['protected_literals_preserved']:
            die(f'ICU/protected-literal check failed {key}')
        if not audit['reviewed_context'] or not audit['semantic_review_result']:
            die(f'semantic/context evidence missing {key}')
        if row['disposition'] == 'new':
            if decision is None or decision['reviewed_target_after'] != new or decision['fresh_disposition'] != expected_status:
                die(f'fresh-cell decision mismatch {key}')
        elif decision is not None:
            die(f'non-fresh cell appears in fresh decisions {key}')

    if {pair(row) for row in decisions} != {pair(row) for row in before if row['disposition'] == 'new'}:
        die('fresh decision membership mismatch')
    if {pair(row) for row in carries} != {pair(row) for row in before if row['disposition'] == 'prior_accepted'}:
        die('accepted carry membership mismatch')
    if exclusions or conflicts or recon:
        die('unresolved terminal exclusions, conflicts, or reconciliation rows remain')
    if any(row['native_speaker_approval'] for row in audits) or manifest['native_speaker_approval']:
        die('native-speaker approval is incorrectly claimed')

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
    print('PASS: 240 exact cells; 90 fresh (79 accepted, 11 corrected), 78 accepted carries, 72 prior correction-needed cells corrected; 83 root-reviewed corrections applied (71 accepted proposals, 12 refined); zero holds/conflicts. Verified all 826 raw overlap inputs, exact source/current/final hashes, 14 source caller blobs, placeholders/ICU/literals, and bundle checksums.')


if __name__ == '__main__':
    main()
