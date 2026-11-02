#!/usr/bin/env python3
"""Verify exact-head evidence for slskR source indices 63–82."""
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
    (65, 'fr'): ': F1=',
    (66, 'hi'): ': हस्ताक्षर की स्थिति',
    (70, 'hi'): '; गवाहों की संख्या',
    (79, 'de'): 'ALLES STANDARDMÄSSIG DEAKTIVIERT',
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
    die(f'unsupported prior input type: {path}')


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
    if any(not path.startswith('docs/') for path in git(repo, 'diff', '--name-only', source, head).splitlines()):
        die('review head contains non-documentation changes after source/catalog head')

    catalogs, keysets = {}, {}
    populated = structured = 0
    for locale in LOCALES:
        path = f'web/src/lib/locales/ui-labels.{locale}.json'
        raw = git(repo, 'show', f'{head}:{path}', raw=True)
        if sha(raw) != manifest['direct_catalog']['catalog_sha256'][path]:
            die(f'catalog SHA-256 mismatch: {locale}')
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
        die('catalog population or structured-value count mismatch')

    selection = [row for _, row in jsonl_records((bundle / 'selection.jsonl').read_bytes())]
    decisions = [row for _, row in jsonl_records((bundle / 'decisions.jsonl').read_bytes())]
    carries = [row for _, row in jsonl_records((bundle / 'carries.jsonl').read_bytes())]
    exclusions = [row for _, row in jsonl_records((bundle / 'terminal-exclusions.jsonl').read_bytes())]
    conflict_holds = [row for _, row in jsonl_records((bundle / 'conflict-holds.jsonl').read_bytes())]
    if (len(selection), len(decisions), len(carries), len(exclusions), len(conflict_holds)) != (240, 83, 138, 14, 5):
        die('window row counts mismatch')
    for rows, name in [(selection,'selection'),(decisions,'decisions'),(carries,'carries'),
                       (exclusions,'exclusions'),(conflict_holds,'conflict holds')]:
        pairs = [key(row) for row in rows]
        if len(pairs) != len(set(pairs)):
            die(f'duplicate cell in {name}')
    expected_partition = decisions + carries + exclusions + conflict_holds
    if {key(row) for row in selection} != {key(row) for row in expected_partition}:
        die('selection does not partition into decisions, carries, exclusions, and conflict holds')
    source_window = sorted({row['source_id'] for row in selection})
    if [source_ids.index(source_id) for source_id in source_window] != list(range(63, 83)):
        die('selected keys are not lexical indices 63–82')
    selection_by_key = {key(row): row for row in selection}
    for row in selection:
        locale, source_id = row['locale'], row['source_id']
        if locale not in LOCALES or not row['populated']:
            die(f'unpopulated selection: {locale}:{source_id}')
        value = catalogs[locale].get(source_id, '__MISSING__')
        if value == '__MISSING__' or value != row['target_text']:
            die(f'current target mismatch: {locale}:{source_id}')
        if target_sha(value) != row['target_sha256'] or row['source_sha256'] != sha(source_id.encode('utf-8')):
            die(f'source/target hash mismatch: {locale}:{source_id}')
        if source_ids.index(source_id) != row['source_index']:
            die(f'lexical source index mismatch: {source_id!r}')

    fresh_counts = collections.Counter(row['status'] for row in decisions)
    prior_counts = collections.Counter(row['status'] for row in carries + exclusions)
    if fresh_counts != collections.Counter({'accepted':79,'correction-needed':4}):
        die(f'fresh status mismatch: {dict(fresh_counts)}')
    if prior_counts != collections.Counter({'accepted':138,'correction-needed':14}):
        die(f'prior status mismatch: {dict(prior_counts)}')
    expected_fresh_indices = {63,64,65,66,67,68,70,73,75,76,77,78,79,80,81}
    if {row['source_index'] for row in decisions} != expected_fresh_indices:
        die('fresh source index set mismatch')
    corrections = {(row['source_index'],row['locale']):row for row in decisions if row['status']=='correction-needed'}
    if set(corrections) != set(CORRECTIONS):
        die('correction candidate set mismatch')

    for row in decisions:
        index, locale, value = row['source_index'], row['locale'], row['target_text']
        if (row['review_head'],row['review_tree'],row['reviewed_code_head'],row['reviewed_code_tree']) != (head,tree,source,source_tree):
            die(f'fresh decision pin mismatch: {locale}:{row["source_id"]}')
        if not row['current_target_sha256_revalidated'] or not row['populated'] or not row['source_context_files_reviewed']:
            die(f'incomplete decision: {locale}:{row["source_id"]}')
        if row['icu_message'] is not False or row['native_speaker_approval'] is not False:
            die(f'unexpected ICU/native-speaker metadata: {locale}:{row["source_id"]}')
        source_ph,target_ph=placeholders(row['source_id']),placeholders(value)
        if source_ph!=target_ph or row['placeholders_source']!=source_ph or row['placeholders_target']!=target_ph:
            die(f'placeholder mismatch: {locale}:{row["source_id"]}')
        proposal=CORRECTIONS.get((index,locale))
        if proposal is None:
            if row['status']!='accepted' or row.get('proposed_target') is not None:
                die(f'unexpected fresh finding: {locale}:{row["source_id"]}')
        else:
            if row['status']!='correction-needed' or row.get('proposed_target')!=proposal:
                die(f'correction proposal mismatch: {locale}:{row["source_id"]}')
            if placeholders(proposal)!=source_ph or row.get('protected_literals_proposed_preserved') is not True:
                die(f'proposal loses placeholder or protected literal: {locale}:{row["source_id"]}')
        if row['protected_literals_preserved'] is False and (index,locale)!=(65,'fr'):
            die(f'unexpected protected literal/punctuation flag: {locale}:{row["source_id"]}')
        if any(unicodedata.category(char)=='Cf' for text in [value,proposal or ''] for char in text):
            die(f'unsafe format control: {locale}:{row["source_id"]}')
        if row['prior_exact_matches']:
            die(f'fresh decision overlaps exact prior status: {locale}:{row["source_id"]}')
        if index in {63,64} and '90' not in value:
            die(f'90-day count missing: {locale}')
        if index==65 and ('F1' not in value or '=' not in value):
            die(f'F1/equal marker missing: {locale}')
        if index==66 and ':' not in value:
            die(f'signature prefix punctuation missing: {locale}')
        if index in {67,68,70} and ';' not in value:
            die(f'mesh-evidence semicolon missing: {locale}:{row["source_id"]}')
        if index==73 and not value:
            die('acquisition failure summary is empty')
        if index in {75,76,77,78} and not any(token in value for token in ['AI','IA','KI','AI','एआई','الذكاء الاصطناعي','人工智慧','人工智能','AI']):
            die(f'AI marker/category missing: {locale}:{row["source_id"]}')
        if index==79 and locale=='de' and 'ß' not in value:
            die('German current uppercase sharp-s finding is missing')
        if index==80 and locale=='hi':
            evidence=row.get('related_label_evidence',{})
            if evidence.get('source_id')!='API key CIDR allowlist' or not evidence.get('target_text'):
                die('Hindi related CIDR-label consistency evidence missing')
        if index==81 and 'API' not in value and locale not in {'ar','hi'}:
            die(f'API identifier missing: {locale}')

    if corrections[(66,'hi')].get('following_value_evidence',{}).get('target_values') != {'Valid':'वैध','Invalid':'अमान्य'}:
        die('Hindi signature-value context evidence mismatch')
    language_refs=manifest['language_references']
    if len(language_refs)!=1 or not language_refs[0].get('url') or not corrections[(79,'de')].get('language_references'):
        die('German language-reference record missing')
    expected_candidates=[]
    for (index,locale),proposal in CORRECTIONS.items():
        row=corrections[(index,locale)]
        expected_candidates.append({'source_index':index,'locale':locale,'current':row['target_text'],'proposal':proposal,'issue_type':row['issue_type']})
    if manifest['correction_candidates']!=expected_candidates:
        die('manifest correction candidate list mismatch')

    expected_conflicts={(68,'ko'),(68,'vi'),(68,'zh-Hans'),(68,'zh-Hant'),(71,'ja')}
    if {(r['source_index'],r['locale']) for r in conflict_holds}!=expected_conflicts:
        die('conflict-hold cell set mismatch')
    for row in conflict_holds:
        if 'status' in row or len(row['conflicting_terminal_statuses'])<2:
            die('conflict hold incorrectly assigns a final status')
        if row['selection_disposition']!='conflict-hold':
            die('conflict hold selection disposition mismatch')

    context=manifest['source_context']
    if sha((bundle/context['file']).read_bytes())!=context['evidence_text_sha256']:
        die('source context evidence hash mismatch')
    for path,digest in context['sha256'].items():
        if sha(git(repo,'show',f'{source}:{path}',raw=True))!=digest:
            die(f'source context SHA-256 mismatch: {path}')
        if git(repo,'rev-parse',f'{source}:{path}')!=context['git_blob_ids'][path]:
            die(f'source context Git blob mismatch: {path}')

    scan=[row for _,row in jsonl_records((bundle/'prior-evidence-scan-manifest.jsonl').read_bytes())]
    overlap=manifest['prior_overlap_scan']
    if len(scan)!=724 or len(scan)!=overlap['scanned_json_evidence_files']:
        die('prior evidence scan count mismatch')
    scan_raw=(bundle/'prior-evidence-scan-manifest.jsonl').read_bytes()
    if sha(scan_raw)!=overlap['manifest_sha256']:
        die('prior evidence scan manifest hash mismatch')
    canonical=sha(json.dumps(sorted(scan,key=lambda item:(item['root'],item['path'])),sort_keys=True,separators=(',',':')).encode('utf-8'))
    if canonical!=overlap['canonical_input_manifest_sha256']:
        die('canonical input manifest hash mismatch')
    refs=collections.defaultdict(list)
    for entry in scan:
        root,relative=entry['root'],Path(entry['path'])
        if relative.is_absolute() or '..' in relative.parts:die('unsafe prior evidence path')
        if root=='prior-audit-7ff':base=audit
        elif root=='pr-review-head':base=repo
        else:die(f'unknown prior evidence root: {root}')
        raw=(base/relative).read_bytes()
        if len(raw)!=entry['bytes'] or sha(raw)!=entry['sha256']:
            die(f'prior evidence hash mismatch: {root}:{relative.as_posix()}')
        for line_number,record in records_for(relative,raw):
            source_id=record.get('source_id') or record.get('message_id') or record.get('id');locale=record.get('locale')
            if source_id not in source_window or locale not in LOCALES:continue
            status=str(record.get('status') or record.get('review_outcome') or '').strip().lower().replace('_','-')
            if status not in TERMINAL:continue
            selected=selection_by_key[(source_id,locale)]
            target_hash=record.get('target_sha256') or record.get('current_target_sha256')
            if record.get('source_sha256')!=selected['source_sha256'] or target_hash!=selected['target_sha256']:continue
            refs[(source_id,locale)].append({'status':status,'batch':record.get('batch'),'finding_id':record.get('finding_id'),
              'root':root,'path':relative.as_posix(),'line':line_number})
    for row in selection:
        actual=sorted(refs.get(key(row),[]),key=lambda item:(item['root'],item['path'],item['line'],item['status']))
        recorded=sorted(row['prior_exact_matches'],key=lambda item:(item['root'],item['path'],item['line'],item['status']))
        if actual!=recorded:die(f'exact prior evidence reference mismatch: {row["locale"]}:{row["source_id"]}')
        statuses={item['status'] for item in actual}
        disposition=row['selection_disposition']
        if disposition=='fresh-decision' and statuses:die('fresh decision has prior terminal overlap')
        if disposition=='exact-accepted-carry' and statuses!={'accepted'}:die('accepted carry status mismatch')
        if disposition=='exact-terminal-exclusion' and statuses!={row['status']}:die('terminal exclusion status mismatch')
        if disposition=='conflict-hold' and statuses!=set(row['conflicting_terminal_statuses']):die('conflict-hold terminal statuses mismatch')

    sums={}
    for line in (bundle/'SHA256SUMS').read_text(encoding='utf-8').splitlines():
        match=re.fullmatch(r'([0-9a-f]{64})  (.+)',line)
        if not match:die('invalid SHA256SUMS line')
        sums[match.group(2)]=match.group(1)
    expected_sums={path.name:sha(path.read_bytes()) for path in bundle.iterdir() if path.is_file() and path.name!='SHA256SUMS'}
    if sums!=expected_sums:die('SHA256SUMS mismatch')

    final=collections.Counter(fresh_counts);final.update(prior_counts)
    print(json.dumps({'result':'PASS','review_head':head,'review_tree':tree,'source_catalog_head':source,'source_catalog_tree':source_tree,
      'source_keys':20,'cell_slots':240,'populated_catalog_cells':populated,'fresh_decisions':dict(fresh_counts),
      'prior_unconflicted':dict(prior_counts),'unresolved_conflict_holds':len(conflict_holds),
      'final_unconflicted_dispositions':dict(final),'overlap_inputs_rehashed':len(scan),'bundle_files_hashed':len(sums)},ensure_ascii=False,indent=2))


if __name__=='__main__':
    main()
