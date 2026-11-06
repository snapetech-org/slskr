from __future__ import annotations

import collections
import hashlib
import json
import re
import subprocess
from pathlib import Path

PARENT = Path('/mnt/disks/scratch/task-scratch/slskr-pr204-W663-682-primary-20261102/packet')
OUT = Path('/mnt/disks/scratch/task-scratch/slskr-pr204-W663-682-crossreview-agent-20261102/packet')
REPO = Path('/mnt/disks/scratch/task-worktrees/localization-20261102/slskr-pr204-w503-522')
HEAD_FROZEN = '86ad391ca248ec50fa4049de0a0f08ee55010441'
TREE_FROZEN = 'f773836319b92b6b8799cdda1695e7da09622941'
LOCALES = ['ar', 'de', 'es', 'fr', 'hi', 'id', 'ja', 'ko', 'pt-BR', 'vi', 'zh-Hans', 'zh-Hant']


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines() if line]


def write_json(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.write_text(''.join(json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(',', ':')) + '\n' for row in rows), encoding='utf-8')


def git(args: list[str]) -> bytes:
    return subprocess.check_output(['git', '-C', str(REPO), *args])


def gittext(args: list[str]) -> str:
    return git(args).decode('utf-8').strip()


def placeholders(value: str) -> list[str]:
    return sorted(re.findall(r'\{[^{}]+\}', value))


def markup(value: str) -> list[str]:
    return re.findall(r'<[^>]+>|&(?:#\d+|\w+);', value)


def normalized(value: str) -> str:
    import unicodedata
    return ''.join(ch for ch in unicodedata.normalize('NFD', value).casefold()
                   if not unicodedata.combining(ch) and not ch.isspace())


def load_manifest() -> dict:
    subprocess.check_call(['sha256sum', '-c', 'SHA256SUMS'], cwd=PARENT, stdout=subprocess.DEVNULL)
    subprocess.check_call(['sha256sum', '-c', 'freeze-manifest.sha256'], cwd=PARENT, stdout=subprocess.DEVNULL)
    return json.loads((PARENT / 'manifest.json').read_text(encoding='utf-8'))


manifest = load_manifest()
live_pr = json.loads(subprocess.check_output([
    'gh', 'pr', 'view', '204', '--repo', 'snapetech-org/slskR', '--json',
    'state,isDraft,headRefOid,headRefName,baseRefOid,url'
], cwd=REPO, text=True))
head = live_pr['headRefOid']
tree = gittext(['rev-parse', f'{head}^{{tree}}'])
if (live_pr['state'] != 'OPEN' or live_pr['isDraft'] is not True or
        gittext(['cat-file', '-t', HEAD_FROZEN]) != 'commit' or gittext(['cat-file', '-t', head]) != 'commit'):
    raise SystemExit(f'Live PR/worktree changed: {json.dumps(live_pr)} tree={tree}')
if head == HEAD_FROZEN and tree != TREE_FROZEN:
    raise SystemExit('Frozen head tree differs from the packet pin')
if head != HEAD_FROZEN:
    subprocess.check_call(['git', '-C', str(REPO), 'merge-base', '--is-ancestor', HEAD_FROZEN, head])
worktree_head = gittext(['rev-parse', 'HEAD'])
worktree_tree = gittext(['rev-parse', 'HEAD^{tree}'])
worktree_status = gittext(['status', '--porcelain'])

source_inventory = read_jsonl(PARENT / 'source-inventory.jsonl')
sources = read_jsonl(PARENT / 'source-context.jsonl')
cells = read_jsonl(PARENT / 'current-cells.jsonl')
ledger = read_jsonl(PARENT / 'primary-review-ledger.jsonl')
candidates = read_jsonl(PARENT / 'correction-candidates.jsonl')
holds = read_jsonl(PARENT / 'held-cells.jsonl')
caller_pins = read_jsonl(PARENT / 'caller-context-pins.jsonl')
attestation = read_jsonl(PARENT / 'source-current-attestation.jsonl')
if (len(sources), len(cells), len(ledger), len(candidates), len(holds), len(caller_pins)) != (20, 240, 240, 57, 24, 29):
    raise SystemExit('Primary packet scope/counts differ from the expected W663–682 inventory')
inventory_ids = [row['source_id'] for row in source_inventory]
source_ids = [row['sourceId'] for row in sorted(sources, key=lambda r: r['sourceIndex'])]
if source_ids != inventory_ids[663:683]:
    raise SystemExit('Frozen source slice does not match source inventory positions 663–682')

cell_by = {(row['sourceIndex'], row['locale']): row for row in cells}
ledger_by = {(row['sourceIndex'], row['locale']): row for row in ledger}
candidate_by = {(row['sourceIndex'], row['locale']): row for row in candidates}
hold_by = {(row['sourceIndex'], row['locale']): row for row in holds}
source_by_index = {row['sourceIndex']: row for row in sources}
attestation_by_index = {row['sourceIndex']: row for row in attestation}
if len(cell_by) != 240 or len(ledger_by) != 240 or len(candidate_by) != 57 or len(hold_by) != 24:
    raise SystemExit('Primary rows contain duplicate or missing cell keys')
if any(collections.Counter(row['locale'] for row in cell_by.values() if row['sourceIndex'] == ordinal) != collections.Counter(LOCALES)
       for ordinal in range(663, 683)):
    raise SystemExit('A source row is missing a direct locale cell')
if len(attestation) != 20:
    raise SystemExit('Source/current attestation does not have one row per source')
for row in ledger:
    key = (row['sourceIndex'], row['locale'])
    if row['attestedHead'] != HEAD_FROZEN or row['attestedTree'] != TREE_FROZEN:
        raise SystemExit(f'Primary ledger is not tied to the frozen head: {key}')
    if row['source'] != cell_by[key]['source'] or row['currentTarget'] != cell_by[key]['currentTarget']:
        raise SystemExit(f'Primary/current input row mismatch: {key}')
for key, candidate in candidate_by.items():
    row = ledger_by[key]
    if (candidate['recommendedTarget'] != row['recommendedTarget'] or
            candidate['recommendedTargetSha256'] != row['recommendedTargetSha256'] or
            sha(candidate['recommendedTarget'].encode('utf-8')) != candidate['recommendedTargetSha256']):
        raise SystemExit(f'Candidate differs from its primary ledger row: {key}')
for key, hold in hold_by.items():
    if ledger_by[key]['reviewDecision'] != 'hold-no-direct-caller' or hold['callerContextPins']:
        raise SystemExit(f'Hold row has caller context or inconsistent decision: {key}')

# Read every catalog directly from the frozen PR commit and verify the manifest
# blobs, byte hashes, exact values, and all 240 target hashes.
catalogs: dict[str, dict] = {}
catalog_pins: dict[str, dict] = {}
frozen_catalog_pins: dict[str, dict] = {}
catalog_metadata = manifest['catalogs']
for locale in LOCALES:
    path = catalog_metadata[locale]['path']
    frozen_raw = git(['show', f'{HEAD_FROZEN}:{path}'])
    frozen_oid = gittext(['rev-parse', f'{HEAD_FROZEN}:{path}'])
    if (frozen_oid != catalog_metadata[locale]['blobOid'] or sha(frozen_raw) != catalog_metadata[locale]['sha256'] or
            len(frozen_raw) != catalog_metadata[locale]['bytes']):
        raise SystemExit(f'Frozen catalog pin mismatch for {locale}: {path}')
    latest_raw = git(['show', f'{head}:{path}'])
    latest_oid = gittext(['rev-parse', f'{head}:{path}'])
    frozen_catalog_pins[locale] = {'path': path, 'blob': frozen_oid, 'sha256': sha(frozen_raw), 'bytes': len(frozen_raw)}
    catalogs[locale] = json.loads(latest_raw.decode('utf-8'))
    catalog_pins[locale] = {'path': path, 'blob': latest_oid, 'sha256': sha(latest_raw), 'bytes': len(latest_raw)}

inventory_by_id = {row['source_id']: row for row in source_inventory}
for src in sources:
    sid = src['sourceId']
    if sid not in inventory_by_id or sha(sid.encode('utf-8')) != src['sourceSha256'] or inventory_by_id[sid]['source_sha256'] != src['sourceSha256']:
        raise SystemExit(f'Source inventory hash mismatch at {src["sourceIndex"]}: {sid}')

for row in cells:
    value = catalogs[row['locale']].get(row['sourceId'])
    if value != row['currentTarget'] or sha(value.encode('utf-8')) != row['currentTargetSha256']:
        raise SystemExit(f'Current target mismatch at {row["sourceIndex"]}/{row["locale"]}')
for source_attestation in attestation:
    ordinal = source_attestation['sourceIndex']
    source_cells = [row for row in cells if row['sourceIndex'] == ordinal]
    if source_attestation['sourceId'] != source_cells[0]['sourceId'] or source_attestation['sourceSha256'] != source_cells[0]['sourceSha256']:
        raise SystemExit(f'Source/current attestation source mismatch: {ordinal}')
    attested_targets = {row['locale']: row for row in source_attestation['targets']}
    if set(attested_targets) != set(LOCALES):
        raise SystemExit(f'Source/current attestation missing a locale: {ordinal}')
    for cell in source_cells:
        target = attested_targets[cell['locale']]
        if (target['target'] != cell['currentTarget'] or target['targetSha256'] != cell['currentTargetSha256'] or
                target['targetCatalogBlob'] != cell['targetCatalogBlob']):
            raise SystemExit(f'Source/current attestation target mismatch: {(ordinal, cell["locale"])}')

# Reattest the full caller registry. Every unique pin is checked against the
# current commit, file object, file bytes, exact line and adjacent context.
unique_pins: dict[tuple[str, int, str], dict] = {}
latest_unique_pins: dict[tuple[str, int, str], dict] = {}
for pin in caller_pins:
    if pin['attestedHead'] != HEAD_FROZEN or pin['attestedTree'] != TREE_FROZEN:
        raise SystemExit(f'Caller pin is not bound to the live head: {pin}')
    key = (pin['path'], pin['line'], pin['lineSha256'])
    if key in unique_pins and unique_pins[key] != pin:
        raise SystemExit(f'Conflicting duplicate caller pin: {key}')
    unique_pins[key] = pin
for pin in unique_pins.values():
    frozen_raw = git(['show', f'{HEAD_FROZEN}:{pin["path"]}'])
    frozen_lines = frozen_raw.decode('utf-8').splitlines()
    line_no = pin['line']
    if (gittext(['rev-parse', f'{HEAD_FROZEN}:{pin["path"]}']) != pin['fileBlob'] or sha(frozen_raw) != pin['fileSha256'] or
            line_no < 1 or line_no > len(frozen_lines) or frozen_lines[line_no - 1] != pin['lineText'] or
            sha(frozen_lines[line_no - 1].encode('utf-8')) != pin['lineSha256']):
        raise SystemExit(f'Frozen caller line mismatch at {pin["path"]}:{line_no}')
    if pin.get('previousLine') is not None and (line_no < 2 or frozen_lines[line_no - 2] != pin['previousLine']):
        raise SystemExit(f'Frozen previous caller line mismatch at {pin["path"]}:{line_no}')
    if pin.get('nextLine') is not None and (line_no >= len(frozen_lines) or frozen_lines[line_no] != pin['nextLine']):
        raise SystemExit(f'Frozen next caller line mismatch at {pin["path"]}:{line_no}')
    latest_raw = git(['show', f'{head}:{pin["path"]}'])
    latest_lines = latest_raw.decode('utf-8').splitlines()
    matches = [i for i, line in enumerate(latest_lines) if line == pin['lineText'] and
               (pin.get('previousLine') is None or (i > 0 and latest_lines[i - 1] == pin['previousLine'])) and
               (pin.get('nextLine') is None or (i + 1 < len(latest_lines) and latest_lines[i + 1] == pin['nextLine']))]
    if len(matches) != 1:
        raise SystemExit(f'Caller context changed or became ambiguous at latest head: {pin["path"]}:{line_no}')
    latest_no = matches[0] + 1
    latest_unique_pins[(pin['path'], pin['line'], pin['lineSha256'])] = {
        **pin, 'attestedHead': head, 'attestedTree': tree,
        'fileBlob': gittext(['rev-parse', f'{head}:{pin["path"]}']), 'fileSha256': sha(latest_raw),
        'line': latest_no, 'lineSha256': sha(latest_lines[latest_no - 1].encode('utf-8')),
        'lineText': latest_lines[latest_no - 1]
    }

all_source_refs = [ref for src in sources for ref in src['callerReferences']]
if len(all_source_refs) != len(caller_pins):
    raise SystemExit(f'Caller reference count mismatch: source context={len(all_source_refs)} pins={len(caller_pins)}')
source_ref_keys = collections.Counter((ref['sourceId'], ref['path'], ref['line'], ref['lineSha256'], ref['fileBlob']) for ref in all_source_refs)
pin_ref_keys = collections.Counter((ref['sourceId'], ref['path'], ref['line'], ref['lineSha256'], ref['fileBlob']) for ref in caller_pins)
if source_ref_keys != pin_ref_keys:
    raise SystemExit('Caller context pin records differ from the per-source caller registry')
for src in sources:
    expected_refs = [p for p in caller_pins if p['sourceId'] == src['sourceId']]
    if src['callerStatus'] == 'no-direct-caller-found' and expected_refs:
        raise SystemExit(f'No-caller source has pins: {src["sourceId"]}')
    if src['callerStatus'] == 'found' and len(expected_refs) != len(src['callerReferences']):
        raise SystemExit(f'Caller registry source mismatch: {src["sourceId"]}')

# Established terms used to adjudicate the shelf tooltip. Values are read from
# exact source keys in the same live locale catalog, not inferred from English.
shelf_terms = {locale: catalogs[locale].get('Discovery Shelf') for locale in LOCALES}
rating_terms = {locale: catalogs[locale].get('Clear rating ({stars}/5)') for locale in LOCALES}
for locale in LOCALES:
    if not shelf_terms[locale] or not rating_terms[locale]:
        raise SystemExit(f'Established shelf/rating term missing for {locale}')

REFINEMENTS = {
    (676, 'ar'): {
        'finalTarget': 'إفراغ قائمة الانتظار القادمة',
        'rationale': 'The caller clears every upcoming queue item and keeps the current track playing. The primary wording uses قائمة التشغيل (playlist); this refinement uses قائمة الانتظار, the established Arabic term for Queue, so it cannot be confused with clearing a saved playlist.'
    }
}
CURRENT_TERM_REFINEMENTS = {
    (680, 'hi'): {
        'finalTarget': 'ब्राउज़र की स्थानीय डिस्कवरी शेल्फ़ के समीक्षा आइटम साफ़ करें। इससे फ़ाइलों या रेटिंग पर कोई प्रभाव नहीं पड़ता।',
        'rationale': 'This terminology refinement uses the same catalog’s established feature name डिस्कवरी शेल्फ instead of खोज शेल्फ़, which reads as a search shelf. It preserves browser-local scope and the no-file/no-rating assurance.'
    },
    (680, 'id'): {
        'finalTarget': 'Hapus item tinjauan dari rak penemuan lokal di browser. Ini tidak memengaruhi file atau rating.',
        'rationale': 'This wording uses rating, the same catalog’s established term for a player star rating, where peringkat suggests rank/ranking. It also makes the relationship between review items, shelf, and browser more natural.'
    },
    (680, 'pt-BR'): {
        'finalTarget': 'Limpe os itens de revisão da prateleira de descoberta local do navegador. Isso não afeta arquivos ou avaliações.',
        'rationale': 'This terminology refinement uses avaliações, matching the same catalog’s term avaliação for player star ratings. Classificações can suggest classifications rather than users’ track ratings.'
    },
    (680, 'zh-Hans'): {
        'finalTarget': '清除浏览器本地探索架中的审查项目。这不会影响文件或评分。',
        'rationale': 'This terminology refinement standardizes on 探索架 and 评分, the same catalog’s terms for Discovery Shelf and the player’s star rating. The current 发现架/评级 are understandable, but differ from those established UI terms.'
    },
    (680, 'zh-Hant'): {
        'finalTarget': '清除瀏覽器本地探索架中的審查項目。這不會影響檔案或評分。',
        'rationale': 'This terminology refinement standardizes on 探索架 and 評分, the same catalog’s terms for Discovery Shelf and the player’s star rating. The current 發現架/評級 are understandable, but differ from those established UI terms.'
    }
}

CANDIDATE_RATIONALES = {
    667: 'The pinned callers use this for a filter-reset action. The revised Japanese verb-object order is natural and describes clearing the filter.',
    668: 'The caller removes the saved ListenBrainz token. The concise German button form keeps the exact product name and clearly names that token action.',
    669: 'The caller clears local listening history. In Chinese, 清除 expresses that action; the current 清晰 describes a clear/obvious history instead.',
    671: 'The caller resets the quality-related search filters. Naming the quality filter avoids saying that quality itself is being removed.',
    672: 'The caller empties the search input/filter for the imported RustyMilk preset bank. The candidate keeps that search scope and preserves the brand without implying that preset content is deleted.',
    673: 'The caller clears the selected issues. The Hindi candidate is imperative; the current wording means a clear or obvious selection.',
    674: 'The caller empties review entries from the browser-local Discovery Shelf. The candidate uses the locale’s established Discovery Shelf term and an action verb instead of translating clear as an adjective.',
    675: 'The caller removes only the approved tag-organization snapshot while keeping the dry-run preview. The candidate denotes a stored/approved snapshot rather than a photograph or an adjective.',
    676: 'The caller removes every upcoming queue item while keeping the current track playing. This candidate names the upcoming tracks or queue action without implying that the current track is removed.',
    677: 'The caller returns to the full imported RustyMilk preset bank without deleting the playlist. The candidate describes deselecting the active local playlist, not deleting its saved contents.',
    679: 'The caller clears browse state so another username can be entered. The current German wording says to delete a search result; the candidate describes resetting the browse result.',
    680: 'The candidate preserves the browser-only scope and the explicit statement that files and ratings are unaffected. Its word choice matches the locale’s established shelf/rating terms or corrects the identified term/grammar issue.'
}

review_rows: list[dict] = []
checks: list[dict] = []
findings: list[dict] = []
for key in sorted(cell_by):
    cell = cell_by[key]
    primary = ledger_by[key]
    cand = candidate_by.get(key)
    hold = hold_by.get(key)
    ordinal, locale = key
    source = cell['source']
    current = cell['currentTarget']
    final = current
    disposition = 'accepted-current'
    rationale = 'The current target accurately communicates this short clear/reset action in its pinned caller context; it does not change the object or scope of the action.'
    candidate_outcome = 'not-applicable'

    if hold:
        disposition = 'held-no-direct-caller'
        if ordinal == 670:
            rationale = 'No direct caller is pinned at this head, so the object and context of “old” cannot be confirmed. Preserve the current target without endorsing it or guessing a correction.'
        else:
            rationale = 'No direct caller is pinned at this head, so the exact browser-local preference scope and supported-default behavior cannot be confirmed. Preserve the current target without endorsing it or guessing a correction.'
    elif cand:
        final = cand['recommendedTarget']
        disposition = 'accepted-primary-candidate'
        candidate_outcome = 'accepted-as-proposed'
        rationale = CANDIDATE_RATIONALES[ordinal]
        if key in REFINEMENTS:
            final = REFINEMENTS[key]['finalTarget']
            disposition = 'refined-primary-candidate'
            candidate_outcome = 'refined'
            rationale = REFINEMENTS[key]['rationale']
    elif key in CURRENT_TERM_REFINEMENTS:
        final = CURRENT_TERM_REFINEMENTS[key]['finalTarget']
        disposition = 'refined-current-translation'
        rationale = CURRENT_TERM_REFINEMENTS[key]['rationale']
        findings.append({
            'sourceIndex': ordinal, 'sourceId': cell['sourceId'], 'locale': locale,
            'findingType': 'current-terminology-refinement', 'source': source,
            'currentTarget': current, 'currentTargetSha256': cell['currentTargetSha256'],
            'recommendedTarget': final, 'recommendedTargetSha256': sha(final.encode('utf-8')),
            'rationale': rationale
        })
    else:
        if ordinal == 663:
            rationale = 'The caller renders this as the search-list clear-all button; the current phrase is a concise imperative and does not imply clearing unrelated application data.'
        elif ordinal in (664, 665):
            rationale = 'The caller clears the completed transfer records in the corresponding downloads/uploads table. The current wording identifies both completion and transfer direction without implying deletion of file contents.'
        elif ordinal == 666:
            rationale = 'The caller clears the content-descriptor retrieval cache; the current target directly names clearing the cache.'
        elif ordinal == 667:
            rationale = 'The callers clear a search/log/event filter. The current locale wording is an imperative reset action; the Japanese candidate is independently accepted for its more natural word order.'
        elif ordinal == 668:
            rationale = 'The caller clears the stored ListenBrainz token. The current target preserves the exact protected service name and names token removal.'
        elif ordinal == 669:
            rationale = 'The caller clears local listening history. The current target refers to local history; the Chinese candidates repair the current adjectival clear/obvious wording.'
        elif ordinal == 671:
            rationale = 'The caller resets only the quality-related search filters. Current targets identify quality criteria or the quality filter; the Spanish, Korean, and Brazilian Portuguese candidates make the filter object explicit.'
        elif ordinal == 672:
            rationale = 'The caller clears the RustyMilk preset search input without deleting presets. The current target conveys a search/filter reset in this context; the five proposed locale corrections remove a misleading “preset search” reading.'
        elif ordinal == 673:
            rationale = 'The caller clears the selected issues. Current targets name clearing a selection; the Hindi proposal repairs an adjective that means clear/obvious.'
        elif ordinal == 674:
            rationale = 'The caller empties browser-local Discovery Shelf review entries only. All 12 candidates use the established locale label for Discovery Shelf and an action verb; none suggests changing files or ratings.'
        elif ordinal == 675:
            rationale = 'The caller removes the approved metadata snapshot while keeping the preview. Current targets denote a snapshot state; the Arabic, Vietnamese, and Chinese proposals improve the object/action wording.'
        elif ordinal == 676:
            rationale = 'The caller removes every upcoming queue item while keeping the current track playing. All candidates preserve that distinction; Arabic is refined to use the established queue term rather than a playlist term.'
        elif ordinal == 677:
            rationale = 'The caller returns to the full imported preset bank and does not delete the saved playlist. All candidates describe clearing its active selection, not deleting its content.'
        elif ordinal == 678:
            rationale = 'The caller clears completed search records only. Current targets retain both “all” and “completed” and do not imply a file-system action.'
        elif ordinal == 679:
            rationale = 'The caller clears the current remote-file browse result so another username can be entered. Current targets convey clearing that result; the German proposal avoids a delete-result reading.'
        elif ordinal == 680:
            rationale = 'The caller clears browser-local shelf review items and explicitly says files and ratings are unaffected. Current targets preserve that warning; the Korean, Japanese, and Vietnamese candidates repair terminology or grammar, and five additional locale term refinements are recorded.'
        elif ordinal == 682:
            rationale = 'The callers set the current search-result filter to empty. The current target accurately names clearing the current filter.'

    src_ph = placeholders(source)
    current_ph = placeholders(current)
    final_ph = placeholders(final)
    src_markup = markup(source)
    current_markup = markup(current)
    final_markup = markup(final)
    if src_ph != current_ph or src_ph != final_ph:
        raise SystemExit(f'Placeholder mismatch {key}: {src_ph}/{current_ph}/{final_ph}')
    if src_markup != current_markup or src_markup != final_markup:
        raise SystemExit(f'Markup mismatch {key}: {src_markup}/{current_markup}/{final_markup}')
    protected = primary.get('protectedLiterals', [])
    protected_checks = []
    for literal in protected:
        ok_current = literal in current
        ok_final = literal in final
        protected_checks.append({'literal': literal, 'presentInCurrent': ok_current, 'presentInFinal': ok_final})
        if not ok_current or not ok_final:
            raise SystemExit(f'Protected literal mismatch {key}: {literal}')

    term_checks = []
    if ordinal == 674:
        canonical = shelf_terms[locale]
        # The Hindi canonical transliteration has a spelling variant with nukta.
        present = normalized(canonical) in normalized(final)
        if not present:
            raise SystemExit(f'Discovery Shelf term mismatch {key}: {canonical!r} not in {final!r}')
        term_checks.append({'termKey': 'Discovery Shelf', 'establishedLocaleTerm': canonical,
                            'presentInFinalTarget': True, 'checkMethod': 'normalized substring, including Hindi nukta normalization'})
    if ordinal == 676 and locale == 'ar':
        canonical = catalogs[locale].get('Queue')
        if not canonical or normalized(canonical) not in normalized(final):
            raise SystemExit('Arabic upcoming-queue refinement does not use the established Queue term')
        term_checks.append({'termKey': 'Queue', 'establishedLocaleTerm': canonical,
                            'presentInFinalTarget': True, 'checkMethod': 'normalized substring'})
    if ordinal == 680:
        shelf = shelf_terms[locale]
        rating_ref = rating_terms[locale]
        # The relevant finding rows adopt these exact terms. Other locale
        # translations can use grammatical variants/synonyms, as adjudicated.
        expected = {
            'hi': ('डिस्कवरी शेल्फ़', 'रेटिंग'),
            'id': ('Rak Penemuan', 'rating'),
            'pt-BR': ('prateleira de descoberta', 'avaliações'),
            'zh-Hans': ('探索架', '评分'),
            'zh-Hant': ('探索架', '評分'),
        }.get(locale)
        if expected:
            if normalized(expected[0]) not in normalized(final) or normalized(expected[1]) not in normalized(final):
                raise SystemExit(f'Established shelf/rating term missing in final target {key}')
            term_checks.append({'shelfTermKey': 'Discovery Shelf', 'establishedShelfTerm': shelf,
                                'establishedRatingReference': rating_ref, 'crossReviewTerms': list(expected),
                                'presentInFinalTarget': True})

    caller_refs = []
    for pin in cell['callerReferences']:
        ref_key = (pin['path'], pin['line'], pin['lineSha256'])
        latest_pin = latest_unique_pins[ref_key]
        caller_refs.append({'path': pin['path'], 'frozenFileBlob': pin['fileBlob'],
                            'frozenFileSha256': pin['fileSha256'], 'frozenLine': pin['line'],
                            'frozenLineSha256': pin['lineSha256'], 'fileBlob': latest_pin['fileBlob'],
                            'fileSha256': latest_pin['fileSha256'], 'line': latest_pin['line'],
                            'lineSha256': latest_pin['lineSha256'], 'lineText': latest_pin['lineText'],
                            'previousLine': latest_pin.get('previousLine'), 'nextLine': latest_pin.get('nextLine')})
    row = {
        'repository': 'snapetech-org/slskR', 'pullRequest': 204, 'exactHead': head, 'exactTree': tree,
        'primaryFrozenHead': HEAD_FROZEN, 'primaryFrozenTree': TREE_FROZEN,
        'sourceWindow': [663, 682], 'sourceIndex': ordinal, 'sourceId': cell['sourceId'], 'locale': locale,
        'source': source, 'sourceSha256': cell['sourceSha256'], 'currentTarget': current,
        'currentTargetSha256': cell['currentTargetSha256'], 'primaryDecision': primary['reviewDecision'],
        'primaryRationale': primary['rationale'], 'primaryRecommendedTarget': primary['recommendedTarget'],
        'primaryRecommendedTargetSha256': primary['recommendedTargetSha256'],
        'primaryCandidateDisposition': candidate_outcome,
        'crossReviewDisposition': disposition, 'crossReviewRationale': rationale,
        'finalTarget': final, 'finalTargetSha256': sha(final.encode('utf-8')),
        'sourcePlaceholders': src_ph, 'currentPlaceholders': current_ph, 'finalPlaceholders': final_ph,
        'placeholderCheck': 'pass', 'sourceMarkup': src_markup, 'currentMarkup': current_markup,
        'finalMarkup': final_markup, 'markupCheck': 'pass', 'protectedLiterals': protected,
        'protectedLiteralChecks': protected_checks, 'protectedLiteralCheck': 'pass',
        'localizedTermChecks': term_checks, 'callerContextPins': caller_refs,
        'targetFile': cell['targetFile'], 'frozenTargetCatalogBlob': cell['targetCatalogBlob'],
        'targetCatalogBlob': catalog_pins[locale]['blob'], 'targetCatalogSha256': catalog_pins[locale]['sha256'],
        'inputCellSha256': sha(json.dumps(cell, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode('utf-8')),
        'primaryLedgerRecordSha256': sha(json.dumps(primary, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode('utf-8')),
        'nativeSpeakerApproval': False
    }
    review_rows.append(row)
    checks.append({
        'sourceIndex': ordinal, 'sourceId': cell['sourceId'], 'locale': locale,
        'sourceSha256': cell['sourceSha256'], 'currentTargetSha256': cell['currentTargetSha256'],
        'finalTargetSha256': row['finalTargetSha256'], 'placeholderCheck': 'pass',
        'markupCheck': 'pass', 'protectedLiteralCheck': 'pass', 'protectedLiteralChecks': protected_checks,
        'localizedTermChecks': term_checks
    })

assert len(review_rows) == len(checks) == 240
cross_counts = collections.Counter(row['crossReviewDisposition'] for row in review_rows)
assert cross_counts == {
    'accepted-current': 154,
    'accepted-primary-candidate': 56,
    'refined-primary-candidate': 1,
    'refined-current-translation': 5,
    'held-no-direct-caller': 24
}, cross_counts
assert len(findings) == 5

write_jsonl(OUT / 'cross-review-cells.jsonl', review_rows)
write_jsonl(OUT / 'placeholder-markup-protected-term-checks.jsonl', checks)
write_jsonl(OUT / 'additional-findings.jsonl', findings)

primary_counts = collections.Counter(row['reviewDecision'] for row in ledger)
proposal_outcomes = collections.Counter(row['primaryCandidateDisposition'] for row in review_rows if row['primaryCandidateDisposition'] != 'not-applicable')
per_locale = {locale: dict(collections.Counter(row['crossReviewDisposition'] for row in review_rows if row['locale'] == locale)) for locale in LOCALES}
summary = {
    'schemaVersion': 1, 'repository': 'snapetech-org/slskR', 'pullRequest': 204,
    'liveState': live_pr['state'], 'isDraft': live_pr['isDraft'], 'exactHead': head, 'exactTree': tree,
    'initialRequestedHead': HEAD_FROZEN, 'initialRequestedTree': TREE_FROZEN,
    'headAdvancedDuringReview': head != HEAD_FROZEN,
    'sourceWindow': {'positions': [663, 682], 'sourceIds': 20, 'locales': LOCALES, 'cells': 240},
    'primaryPacket': str(PARENT),
    'primaryPacketSha256SumsSha256': sha((PARENT / 'SHA256SUMS').read_bytes()),
    'primaryFreezeManifestSha256': sha((PARENT / 'freeze-manifest.json').read_bytes()),
    'primaryDispositionCounts': dict(primary_counts),
    'crossReviewDispositionCounts': dict(cross_counts), 'crossReviewCountsByLocale': per_locale,
    'primaryCandidateOutcomes': {'total': sum(proposal_outcomes.values()),
        'acceptedAsProposed': proposal_outcomes['accepted-as-proposed'], 'refined': proposal_outcomes['refined'],
        'rejected': proposal_outcomes['rejected'], 'held': proposal_outcomes['held']},
    'missedCurrentIssues': 0, 'currentTranslationRefinements': len(findings), 'additionalFindings': [
        {'sourceIndex': row['sourceIndex'], 'sourceId': row['sourceId'], 'locale': row['locale'],
         'findingType': row['findingType'], 'recommendedTargetSha256': row['recommendedTargetSha256']}
        for row in findings],
    'sourceValuesReattested': len(sources), 'currentCellsReattested': len(cells),
    'cellMismatches': 0, 'callerReferenceRecordsReattested': len(caller_pins),
    'uniqueCallerLinesReattested': len(latest_unique_pins), 'uniqueCallerFiles': len({pin['path'] for pin in latest_unique_pins.values()}),
    'targetCatalogsReattested': len(catalog_pins), 'placeholderMismatches': 0, 'markupMismatches': 0,
    'protectedLiteralChecks': sum(len(row['protectedLiteralChecks']) for row in review_rows),
    'protectedLiteralMismatches': 0, 'localizedTermMismatches': 0,
    'nativeSpeakerApproval': False, 'browserReview': False, 'repositoryModifiedByReviewer': False,
    'sharedWorktreeObservedDirty': bool(worktree_status),
    'sharedWorktreeHeadAtReview': worktree_head,
    'sharedWorktreeTreeAtReview': worktree_tree,
    'testsBuildsScansCiWorkflowsReleasesTagsMerges': False, 'blockers': []
}
write_json(OUT / 'summary.json', summary)

reattestation = {
    'repository': 'snapetech-org/slskR', 'pullRequest': 204,
    'livePrState': live_pr['state'], 'isDraft': live_pr['isDraft'], 'url': live_pr['url'],
    'head': head, 'tree': tree, 'worktree': str(REPO), 'worktreeHeadAtReview': worktree_head,
    'worktreeTreeAtReview': worktree_tree, 'worktreeMatchesLivePr': worktree_head == head,
    'expectedCommitObjectPresent': True, 'worktreeClean': not bool(worktree_status),
    'worktreeDirtyObserved': bool(worktree_status),
    'worktreeReadMethod': 'all source/catalog/caller evidence read from git objects at the exact pinned commit',
    'sourceWindow': [663, 682], 'sourceIds': len(sources), 'locales': LOCALES,
    'cells': len(cells), 'primaryPacketSumsVerified': True,
    'primaryPacketSha256SumsSha256': summary['primaryPacketSha256SumsSha256'],
    'primaryFreezeManifestSha256': summary['primaryFreezeManifestSha256'],
    'sourceInventorySha256': sha((PARENT / 'source-inventory.jsonl').read_bytes()),
    'sourceContextSha256': sha((PARENT / 'source-context.jsonl').read_bytes()),
    'currentCellsSha256': sha((PARENT / 'current-cells.jsonl').read_bytes()),
    'primaryLedgerSha256': sha((PARENT / 'primary-review-ledger.jsonl').read_bytes()),
    'candidateFileSha256': sha((PARENT / 'correction-candidates.jsonl').read_bytes()),
    'holdFileSha256': sha((PARENT / 'held-cells.jsonl').read_bytes()),
    'frozenCatalogs': frozen_catalog_pins, 'catalogs': catalog_pins, 'catalogMismatches': 0,
    'sourceValuesReattested': len(sources), 'cellValuesReattested': len(cells), 'cellMismatches': 0,
    'callerReferenceRecordsReattested': len(caller_pins), 'uniqueCallerLinesReattested': len(latest_unique_pins),
    'uniqueCallerFiles': len({pin['path'] for pin in latest_unique_pins.values()}), 'callerMismatches': 0,
    'placeholdersRechecked': len(cells), 'placeholderMismatches': 0,
    'markupRechecked': len(cells), 'markupMismatches': 0,
    'protectedLiteralChecks': summary['protectedLiteralChecks'], 'protectedLiteralMismatches': 0,
    'status': 'pass', 'reattestedAtUtc': subprocess.check_output(['date', '-u', '+%Y-%m-%dT%H:%M:%SZ'], text=True).strip()
}
write_json(OUT / 'reattestation.json', reattestation)

provenance = {
    'reviewerRole': 'independent cross-reviewer',
    'reviewType': 'independent source/caller-aware adjudication of all frozen current cells, 57 primary proposals, and 24 no-caller holds',
    'exactHead': head, 'exactTree': tree, 'scope': summary['sourceWindow'],
    'inputs': ['frozen source inventory', 'source caller context', '12 exact target catalogs',
               '240 primary review rows', '57 correction/refinement proposals', '24 holds',
               'Discovery Shelf, Queue, and star-rating established locale terms'],
    'nativeSpeakerApproval': False, 'browserReview': False,
    'repositoryOrPrEdits': False, 'testsBuildsScansCiRun': False, 'workflowsTouched': False,
    'concurrentW643-662ApplicationObservedDuringReview': True,
    'worktreeWasDirtyAtFinalAttestation': bool(worktree_status)
}
write_json(OUT / 'reviewer-provenance.json', provenance)
print(json.dumps({'cells': len(review_rows), 'primaryCounts': dict(primary_counts),
    'crossReviewCounts': dict(cross_counts), 'candidateOutcomes': summary['primaryCandidateOutcomes'],
    'findings': len(findings), 'callerRecords': len(caller_pins), 'uniqueCallerLines': len(unique_pins),
    'protectedChecks': summary['protectedLiteralChecks']}, ensure_ascii=False, indent=2))
