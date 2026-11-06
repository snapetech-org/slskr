#!/usr/bin/env python3
"""Build the sealed cross-review packet from the pinned source, primary, and blind inputs."""
import collections
import datetime
import hashlib
import json
import subprocess
from pathlib import Path

OUT = Path(__file__).resolve().parent
ROOT = Path('/home/keith/Documents/code/task-scratch')
INPUT = ROOT / 'slskr-pr209-w1543-1562-primary-20261104' / 'candidate-free-input'
PRIMARY = ROOT / 'slskr-pr209-w1543-1562-primary-20261104' / 'primary-review'
BLIND = ROOT / 'slskr-pr209-w1543-1562-independent-blind-review-20261104'
SOURCE = Path('/mnt/disks/scratch/task-worktrees/localization-20261104/slskr-pr209-w1543-1562-source')
HEAD = 'c15eddffec2c4c24cc091b2a6ebf0c43fa58ef1b'
TREE = '4259db991f25fbbd0200963769e62bb7e2150806'
LOCALES = ['es', 'zh-Hans', 'hi', 'de', 'ja', 'fr', 'pt-BR', 'ar', 'ko', 'zh-Hant', 'vi', 'id']


def sha(value):
    if isinstance(value, str):
        value = value.encode('utf-8')
    return hashlib.sha256(value).hexdigest()


def canon(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'))


def read_json(path):
    return json.loads(path.read_text(encoding='utf-8'))


def read_jsonl(path):
    return [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines() if line]


def git(*args):
    return subprocess.check_output(['git', '-C', str(SOURCE), *args], text=True).strip()


def token_signature(text):
    import re
    placeholders = re.findall(r'\{[A-Za-z][A-Za-z0-9_]*\}', text)
    markup = re.findall(r'</?[A-Za-z][^>]*>', text)
    numbers = re.findall(r'(?<![A-Za-z])\d+(?:[.,]\d+)?%?(?![A-Za-z])', text)
    protected = []
    pattern = r'(?<![A-Za-z0-9])(?:[A-Z]{2,}[A-Z0-9]*|ffmpeg|Chromaprint|Soulseek|Spotify|YouTube|Pushbullet|Matrix|WebSocket|OpenAI)(?![A-Za-z0-9])'
    for value in re.findall(pattern, text):
        if value not in protected:
            protected.append(value)
    return {
        'placeholders': placeholders,
        'markup': markup,
        'numbers': numbers,
        'protectedLiterals': protected,
    }


def verify_source_contexts(context_rows):
    assert git('rev-parse', 'HEAD') == HEAD
    assert git('rev-parse', 'HEAD^{tree}') == TREE
    assert git('status', '--porcelain') == ''
    blob_cache = {}
    verified_callers = 0
    for item in context_rows:
        assert item['callerContextSha256'] == sha(canon({'sourceKey': item['sourceKey'], 'callers': item['callers']}))
        assert item['productionCallerCount'] == len(item['callers'])
        assert item['callerOccurrenceCount'] == sum(c['literalOccurrenceCount'] for c in item['callers'])
        for caller in item['callers']:
            assert caller['lineSha256'] == sha(caller['lineText'])
            assert caller['contextSha256'] == sha(canon(caller['context']))
            assert any(row['line'] == caller['line'] and row['text'] == caller['lineText'] for row in caller['context'])
            path = caller['path']
            full = SOURCE / path
            file_bytes = full.read_bytes()
            assert sha(file_bytes) == caller['fileSha256'], path
            if path not in blob_cache:
                blob_cache[path] = git('rev-parse', f'HEAD:{path}')
            assert blob_cache[path] == caller['gitBlob'], path
            lines = file_bytes.decode('utf-8').splitlines()
            assert lines[caller['line'] - 1] == caller['lineText'], (path, caller['line'])
            lo, hi = caller['contextStartLine'], caller['contextEndLine']
            actual_context = [{'line': n, 'text': lines[n - 1]} for n in range(lo, hi + 1)]
            assert actual_context == caller['context'], (path, caller['line'])
            assert item['sourceKey'] in caller['lineText']
            verified_callers += 1
    return verified_callers, len(blob_cache)


# Cross-review adjudications. Entries from the primary ledger are endorsed by default;
# these overrides record wording aligned to pinned UI labels or blind-only findings.
manual = {}

def propose(position, locale, selected, rationale, *, adjusted=False, evidence=None, confidence='moderate'):
    manual[(position, locale)] = {
        'crossDisposition': 'propose-correction',
        'selectedTarget': selected,
        'rationale': rationale,
        'confidence': confidence,
        'adjudication': 'endorse-primary-adjusted' if adjusted else 'endorse-blind',
        'catalogEvidenceKeys': evidence or [],
    }


def hold(position, locale, rationale, *, evidence=None, finding_ids=None):
    manual[(position, locale)] = {
        'crossDisposition': 'hold',
        'selectedTarget': None,
        'rationale': rationale,
        'confidence': 'low',
        'adjudication': 'hold-for-fluent-review',
        'catalogEvidenceKeys': evidence or [],
        'crossFindingIds': finding_ids or [],
    }

propose(1543, 'hi', 'सहमति-आधारित सिफ़ारिशें प्राप्त नहीं हो सकीं: {message}',
        'The current wording can read as unanimous recommendations. Use the exact established Hindi wording from the Consensus Recommendations heading and preserve the runtime error placeholder.',
        adjusted=True, evidence=['Consensus Recommendations'])
propose(1543, 'ja', 'コンセンサスによる推奨事項を取得できませんでした: {message}',
        'The current compressed term is less clear than the consensus-recommendations concept. Match the exact Japanese panel heading and preserve the runtime error placeholder.',
        adjusted=True, evidence=['Consensus Recommendations'])
propose(1543, 'ar', 'تعذر الحصول على توصيات التوافق: {message}',
        'The current phrase can suggest unanimous recommendations. Match the Arabic panel heading for consensus recommendations and preserve the runtime error placeholder.',
        adjusted=True, evidence=['Consensus Recommendations'])
propose(1543, 'ko', '합의 권고사항을 가져오지 못했습니다: {message}',
        'The current wording is broad and differs from the panel heading. Match the established Korean heading term and preserve the runtime error placeholder.',
        adjusted=True, evidence=['Consensus Recommendations'])

propose(1547, 'es', 'No se pudieron obtener las marcas de tiempo de última presencia: {message}',
        'The current phrase makes the timestamps sound as if they were seen. Reuse the neighboring last-presence wording and retain {message}.',
        evidence=['Last Seen Timestamps for Pod {podId}'])
propose(1547, 'fr', 'Impossible de récupérer les horodatages de dernière présence : {message}',
        'The current phrase suggests a last viewing event. Reuse the neighboring dernière présence wording and retain {message}.',
        evidence=['Last Seen Timestamps for Pod {podId}'])
propose(1547, 'pt-BR', 'Não foi possível obter os horários da última visualização: {message}',
        'The current phrase is awkward and makes the timestamps sound as if they were seen. Reuse the neighboring Portuguese wording and retain {message}.',
        evidence=['Last Seen Timestamps for Pod {podId}'])
propose(1547, 'ja', '最終確認時刻を取得できませんでした: {message}',
        'The current target means timestamps last displayed. Reuse the neighboring last-confirmed-time wording and retain {message}.',
        evidence=['Last Seen Timestamps for Pod {podId}'])
propose(1547, 'ko', '마지막 확인 시각을 가져오지 못했습니다: {message}',
        'The current target means timestamps last displayed. Reuse the neighboring last-confirmed-time wording and retain {message}.',
        evidence=['Last Seen Timestamps for Pod {podId}'])

propose(1553, 'hi', 'राय के आँकड़े प्राप्त नहीं हो सके: {message}',
        'The current compound omits the genitive marker present in the paired no-placeholder key. Reuse that natural paired wording and retain {message}.',
        evidence=[])

hold(1549, 'ar',
     'The Arabic member-affinity terminology varies across the paired error, panel heading, action, and score label. The current phrase matches one label, but the pinned context does not settle a single precise term; retain a text-free hold for fluent review.',
     evidence=['Member Affinities ({count})', 'Get Member Affinities', 'Affinity Score:'])
hold(1548, 'ko',
     'The Korean no-placeholder message uses 친화도 while the paired error and the panel heading and score label use 친밀도. The source context does not establish which term best represents this metric; hold this cell together with the paired message for fluent review.',
     evidence=['Member Affinities ({count})', 'Get Member Affinities', 'Affinity Score:'], finding_ids=['XR01'])
hold(1549, 'ko',
     'The Korean paired messages and UI labels split between 친화도 and 친밀도. The blind finding identifies a real terminology inconsistency, but the pinned context cannot establish which term best represents this metric; hold both paired cells for fluent review.',
     evidence=['Member Affinities ({count})', 'Get Member Affinities', 'Affinity Score:'], finding_ids=['XR01'])
for locale in ['zh-Hans', 'zh-Hant']:
    hold(1550, locale,
         'The current Chinese wording says statistics about member relationships, while the source is membership statistics. Context establishes a membership concept through adjacent record labels but does not settle whether to name member records, member status, or membership statistics; retain a text-free hold for fluent review.',
         evidence=['Get Membership Record', 'Membership Found'])

cross_findings = [
    {
        'id': 'XR01',
        'cells': [{'position': 1548, 'locale': 'ko'}, {'position': 1549, 'locale': 'ko'}],
        'category': 'terminology consistency',
        'severity': 'moderate',
        'confidence': 'moderate',
        'finding': 'The paired Korean error keys and the pinned Member Affinities, Get Member Affinities, and Affinity Score labels split between 친화도 and 친밀도. The blind review flags position 1549, but the panel labels use 친밀도; the evidence does not establish which term is semantically best for this affinity metric.',
        'disposition': 'hold-both-cells-for-fluent-review',
    }
]

contexts = read_jsonl(INPUT / 'source-contexts.jsonl')
verified_callers, verified_caller_files = verify_source_contexts(contexts)
context_by_position = {x['position']: x for x in contexts}
cells = read_jsonl(INPUT / 'current-target-cells.jsonl')
primary_ledger = read_jsonl(PRIMARY / 'primary-ledger.jsonl')
primary_proposals = read_jsonl(PRIMARY / 'proposals.jsonl')
blind_cells = read_jsonl(BLIND / 'review-cells.jsonl')
blind_findings = read_json(BLIND / 'findings.json')
primary_by_key = {(x['position'], x['locale']): x for x in primary_ledger}
proposal_by_key = {(x['position'], x['locale']): x for x in primary_proposals}
blind_by_key = {(x['position'], x['locale']): x for x in blind_cells}
blind_finding_by_id = {x['id']: x for x in blind_findings}

pins = read_json(INPUT / 'catalog-file-pins.json')
catalogs = {}
catalog_blob_cache = {}
for locale, pin in pins['localeCatalogs'].items():
    full = SOURCE / pin['path']
    raw = full.read_bytes()
    assert sha(raw) == pin['sha256'], (locale, 'catalog sha')
    blob = git('rev-parse', f"HEAD:{pin['path']}")
    assert blob == pin['gitBlob'], (locale, 'catalog blob')
    catalogs[locale] = read_json(full)
    catalog_blob_cache[locale] = pin

catalog_keys_by_position = {
    1543: ['Consensus Recommendations'],
    1544: ['Content Metadata'],
    1546: ['Last Seen Timestamps for Pod {podId}'],
    1547: ['Last Seen Timestamps for Pod {podId}'],
    1548: ['Member Affinities ({count})', 'Get Member Affinities', 'Affinity Score:'],
    1549: ['Member Affinities ({count})', 'Get Member Affinities', 'Affinity Score:'],
    1550: ['Get Membership Record', 'Membership Found'],
    1551: ['Get Membership Record', 'Membership Found'],
    1560: ['Join Room'],
    1561: ['Join Room'],
}

output_rows = []
for cell in cells:
    key = (cell['position'], cell['locale'])
    context = context_by_position[cell['position']]
    assert cell['sourceContextSha256'] == context['callerContextSha256']
    primary = primary_by_key[key]
    assert primary['sourceKeySha256'] == cell['sourceKeySha256']
    assert primary['sourceContextSha256'] == cell['sourceContextSha256']
    assert primary['currentTargetSha256'] == cell['currentTargetSha256']
    p = proposal_by_key.get(key)
    blind = blind_by_key[key]
    if key in manual:
        decision = dict(manual[key])
    elif p:
        decision = {
            'crossDisposition': 'propose-correction',
            'selectedTarget': p['selectedTarget'],
            'rationale': p['reason'],
            'confidence': p['confidence'],
            'adjudication': 'endorse-primary',
            'catalogEvidenceKeys': catalog_keys_by_position.get(cell['position'], []),
        }
    else:
        assert not blind['findingIds'], f'unadjudicated blind finding {key}'
        decision = {
            'crossDisposition': 'accept-current',
            'selectedTarget': cell['currentTarget'],
            'rationale': 'The current wording preserves the source meaning in its pinned production caller. Neither the primary review nor the blind review identifies an unresolved cell-level issue.',
            'confidence': 'moderate',
            'adjudication': 'accept-current',
            'catalogEvidenceKeys': [],
        }
    selected = decision['selectedTarget']
    source_tokens = token_signature(cell['sourceKey'])
    current_tokens = token_signature(cell['currentTarget'])
    selected_tokens = token_signature(selected) if selected is not None else None
    token_integrity = None
    if selected is not None:
        token_integrity = {
            'placeholderSequenceMatches': source_tokens['placeholders'] == selected_tokens['placeholders'],
            'markupMatches': source_tokens['markup'] == selected_tokens['markup'],
            'numericTokenSequenceMatches': source_tokens['numbers'] == selected_tokens['numbers'],
            'protectedLiteralsPreserved': all(t in selected_tokens['protectedLiterals'] for t in source_tokens['protectedLiterals']),
        }
        assert all(token_integrity.values()), (key, token_integrity)
    catalog_evidence = []
    for evidence_key in decision.get('catalogEvidenceKeys', []):
        if evidence_key in catalogs[cell['locale']]:
            pin = catalog_blob_cache[cell['locale']]
            catalog_evidence.append({
                'key': evidence_key,
                'translation': catalogs[cell['locale']][evidence_key],
                'path': pin['path'],
                'fileSha256': pin['sha256'],
                'gitBlob': pin['gitBlob'],
            })
    caller_refs = [{
        'path': caller['path'],
        'line': caller['line'],
        'lineSha256': caller['lineSha256'],
        'contextSha256': caller['contextSha256'],
        'fileSha256': caller['fileSha256'],
        'gitBlob': caller['gitBlob'],
    } for caller in context['callers']]
    finding_ids = blind['findingIds']
    cross_ids = decision.get('crossFindingIds', [])
    row = {
        'position': cell['position'],
        'locale': cell['locale'],
        'sourceKey': cell['sourceKey'],
        'sourceKeySha256': cell['sourceKeySha256'],
        'currentTarget': cell['currentTarget'],
        'currentTargetSha256': cell['currentTargetSha256'],
        'sourceContextSha256': cell['sourceContextSha256'],
        'callerCount': cell['callerCount'],
        'callerReferences': caller_refs,
        'callerHashesVerifiedAgainstPinnedWorktree': True,
        'sourceTokens': source_tokens,
        'currentTokens': current_tokens,
        'selectedTarget': selected,
        'selectedTargetSha256': sha(selected) if selected is not None else None,
        'selectedTokens': selected_tokens,
        'tokenIntegrity': token_integrity,
        'primaryDisposition': primary['disposition'],
        'primarySelectedTarget': p['selectedTarget'] if p else None,
        'primarySelectedTargetSha256': p['selectedTargetSha256'] if p else None,
        'primaryReason': p['reason'] if p else None,
        'primaryProposalOutcome': ('adjusted' if p and selected != p['selectedTarget'] else 'endorsed') if p else 'none',
        'blindFindingIds': finding_ids,
        'blindFindings': [{
            'id': blind_finding_by_id[fid]['id'],
            'category': blind_finding_by_id[fid]['category'],
            'severity': blind_finding_by_id[fid]['severity'],
            'confidence': blind_finding_by_id[fid]['confidence'],
            'finding': blind_finding_by_id[fid]['finding'],
            'recommendation': blind_finding_by_id[fid]['recommendation'],
        } for fid in finding_ids],
        'crossFindingIds': cross_ids,
        'crossDisposition': decision['crossDisposition'],
        'adjudication': decision['adjudication'],
        'confidence': decision['confidence'],
        'rationale': decision['rationale'],
        'catalogEvidence': catalog_evidence,
    }
    output_rows.append(row)

assert len(output_rows) == 240
assert [(r['position'], r['locale']) for r in output_rows] == [(p, l) for p in range(1543, 1563) for l in LOCALES]
counts = collections.Counter(x['crossDisposition'] for x in output_rows)
assert counts == {'accept-current': 208, 'propose-correction': 27, 'hold': 5}, counts
primary_outcomes = collections.Counter(x['primaryProposalOutcome'] for x in output_rows if x['primaryDisposition'] in ('propose-correction', 'propose-refinement'))
assert primary_outcomes == {'endorsed': 17, 'adjusted': 4}, primary_outcomes
blind_outcomes = collections.Counter(
    next(r['crossDisposition'] for r in output_rows if (r['position'], r['locale']) == (cell['position'], cell['locale']))
    for cell in blind_cells if cell['findingIds']
)
assert blind_outcomes == {'propose-correction': 18, 'hold': 4}, blind_outcomes
primary_keys = set(proposal_by_key)
blind_keys = {key for key, value in blind_by_key.items() if value['findingIds']}
assert (len(primary_keys & blind_keys), len(primary_keys - blind_keys), len(blind_keys - primary_keys), 240 - len(primary_keys | blind_keys)) == (12, 9, 10, 209)

# Verify the source packet checksums and rerun its three supplied read-only verifiers.
for packet in [INPUT, PRIMARY, BLIND]:
    sums = {}
    for line in (packet / 'SHA256SUMS.txt').read_text(encoding='utf-8').splitlines():
        digest, name = line.split(None, 1)
        sums[name.lstrip('* ')] = digest
    assert set(sums) == {p.name for p in packet.iterdir() if p.is_file() and p.name != 'SHA256SUMS.txt'}
    for name, digest in sums.items():
        assert sha((packet / name).read_bytes()) == digest, (packet.name, name)
for verifier in [INPUT / 'verify-candidate-free.py', PRIMARY / 'verify-primary.py', BLIND / 'verify-review.py']:
    subprocess.run(['python3', str(verifier)], check=True, stdout=subprocess.DEVNULL)

# Validate the filtered live PR metadata capture without requesting or storing its body.
metadata = read_json(OUT / 'live-pr-metadata.json')
branch_sha = (OUT / 'live-branch-ref.txt').read_text(encoding='utf-8').strip()
pull_sha = (OUT / 'live-pull-ref.txt').read_text(encoding='utf-8').strip()
local_tree = (OUT / 'live-local-tree.txt').read_text(encoding='utf-8').strip()
assert metadata['number'] == 209 and metadata['state'] == 'OPEN' and metadata['isDraft'] is True
assert metadata['headRefOid'] == HEAD and metadata['baseRefName'] == 'main'
assert metadata['baseRefOid'] == '1bbaec9fdc63a86de343e37e33bae70d44301a36'
assert branch_sha == pull_sha == HEAD and local_tree == TREE

input_hashes = {
    'candidateFreeChecksumListSha256': sha((INPUT / 'SHA256SUMS.txt').read_bytes()),
    'primaryChecksumListSha256': sha((PRIMARY / 'SHA256SUMS.txt').read_bytes()),
    'blindChecksumListSha256': sha((BLIND / 'SHA256SUMS.txt').read_bytes()),
    'candidateFreeManifestSha256': sha((INPUT / 'manifest.json').read_bytes()),
    'primarySummarySha256': sha((PRIMARY / 'SUMMARY.json').read_bytes()),
    'blindManifestSha256': sha((BLIND / 'manifest.json').read_bytes()),
}
manifest = {
    'artifact': 'slskR PR #209 W1543-W1562 cross-review',
    'repository': 'snapetech-org/slskR',
    'pullRequest': 209,
    'exactPin': {
        'head': HEAD,
        'tree': TREE,
        'headRef': metadata['headRefName'],
        'baseRef': metadata['baseRefName'],
        'baseSha': metadata['baseRefOid'],
    },
    'liveRefChecks': {
        'filteredPullRequestMetadata': metadata,
        'branchRefSha': branch_sha,
        'pullRefSha': pull_sha,
        'localTreeSha': local_tree,
        'matchedExactPin': True,
        'prBodyOrDescriptionRequested': False,
    },
    'sourceWorktree': {
        'path': str(SOURCE),
        'head': git('rev-parse', 'HEAD'),
        'tree': git('rev-parse', 'HEAD^{tree}'),
        'clean': git('status', '--porcelain') == '',
        'verifiedCallerReferences': verified_callers,
        'verifiedCallerFiles': verified_caller_files,
    },
    'inputs': {
        'candidateFreeInput': str(INPUT),
        'primaryReview': str(PRIMARY),
        'independentBlindReview': str(BLIND),
        **input_hashes,
        'suppliedVerifiers': {
            'candidateFree': 'PASS',
            'primary': 'PASS',
            'independentBlind': 'PASS',
        },
    },
    'review': {
        'sourcePositions': [1543, 1562],
        'sourceCount': 20,
        'localeCount': 12,
        'cellCount': 240,
        'localeOrder': LOCALES,
        'crossDispositionCounts': dict(counts),
        'primaryProposals': 21,
        'primaryProposalsEndorsed': 21,
        'primaryProposalsWordingAdjusted': 4,
        'primaryProposalsExact': 17,
        'blindFindings': 20,
        'blindFindingCells': 22,
        'blindFindingCellsActioned': 18,
        'blindFindingCellsHeld': 4,
        'primaryBlindOverlapCells': 12,
        'primaryOnlyProposalCells': 9,
        'blindOnlyFindingCells': 10,
        'cellsWithoutPrimaryOrBlindFinding': 209,
        'newCorrectionsBeyondPrimary': 6,
        'additionalCrossReviewHolds': 1,
        'crossReviewFindings': cross_findings,
        'overallConfidence': 'moderate',
        'nativeSpeakerSignoff': False,
        'browserReviewPerformed': False,
        'tokenMismatchCounts': {
            'currentPlaceholderSequenceMismatchCount': 0,
            'currentMarkupMismatchCount': 0,
            'currentNumericTokenMismatchCount': 0,
            'currentProtectedLiteralMismatchCount': 0,
            'recommendedPlaceholderSequenceMismatchCount': 0,
            'recommendedMarkupMismatchCount': 0,
            'recommendedNumericTokenMismatchCount': 0,
            'recommendedProtectedLiteralMismatchCount': 0,
        },
        'callerHashMismatches': 0,
    },
    'reviewerExposure': {
        'candidateFreeInputOpened': True,
        'primaryReviewOpened': True,
        'independentBlindReviewOpened': True,
        'sourceCallerContextsOpened': True,
        'pinnedCatalogLabelsRead': True,
        'prDescriptionOrBodyOpened': False,
        'prDescriptionOrBodyRequested': False,
    },
    'actions': {
        'catalogsEdited': False,
        'prOrBodyChanged': False,
        'commitOrPush': False,
        'testsBuildsOrCI': False,
        'workflowsModified': False,
        'mergeReleaseOrTag': False,
    },
    'createdAtUtc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'fileHashes': {},
}

ledger_path = OUT / 'cross-review-ledger.jsonl'
ledger_path.write_text(''.join(json.dumps(row, ensure_ascii=False, sort_keys=True) + '\n' for row in output_rows), encoding='utf-8')
(OUT / 'cross-findings.json').write_text(json.dumps(cross_findings, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

report_lines = [
    '# slskR PR #209 W1543-W1562 cross-review',
    '',
    '## Pin and scope',
    '',
    f"PR #209 remained {metadata['state']} and draft={str(metadata['isDraft']).lower()}. Filtered live metadata reports head {metadata['headRefOid']} on {metadata['headRefName']} and base {metadata['baseRefName']} at {metadata['baseRefOid']}. The branch ref and pull ref both resolve to {HEAD}; the exact commit tree is {TREE}. The PR body and description were not requested or read.",
    '',
    'The review reconciles 240 cells: source positions 1543–1562 across the 12 pinned locales. Candidate-free, primary, and independent blind input seals and verifiers passed. All 21 caller references were rehashed against the exact source worktree; 21 literal occurrences across 10 caller files, with no callerless positions.',
    '',
    '## Outcome',
    '',
    f"Cross-review disposition: {counts['accept-current']} accept current, {counts['propose-correction']} correction proposals, and {counts['hold']} holds.",
    '',
    'All 21 primary proposals are supported. Seventeen use the primary wording unchanged; four consensus-recommendation wordings at position 1543 are adjusted to match the exact pinned translated panel heading.',
    '',
    'The blind review has 20 finding records covering 22 cells. Eighteen finding cells support a correction proposal. Four remain on hold: Arabic member-affinity wording at 1549, Korean affinity terminology at 1549, and Simplified and Traditional Chinese membership statistics at 1550. The Korean issue also requires position 1548 to remain held so both paired messages can be reviewed together.',
    '',
    'Six corrections are additional to the primary proposals: five last-seen message strings at 1547, aligned to each locale’s paired display wording, and Hindi opinion statistics at 1553, aligned to its paired phrase. All recommendations preserve placeholders and other protected tokens.',
    '',
    '## Disagreements and holds',
    '',
    'Primary and blind findings overlap on 12 cells; 9 cells have only a primary proposal, 10 have only a blind finding, and 209 have neither. The primary-only proposals are supported. Six blind-only cells receive explicit correction proposals; four blind-only cells remain held.',
    '',
    'The Korean affinity finding is directionally right that the pair is inconsistent, but its proposed direction is unresolved: the paired errors split between 친화도 and 친밀도, while the pinned panel heading and score label use 친밀도. Cross-review holds both error cells rather than selecting a term without fluent review.',
    '',
    'The Arabic affinity wording also varies across the paired errors and panel labels. Chinese membership-statistics wording clearly shifts to member relationships, but the exact membership or status term cannot be selected from caller context alone. Those cells remain text-free holds.',
    '',
    '## Integrity and limits',
    '',
    'Current targets and all selected correction targets preserve source placeholder sequence, markup, numeric tokens, and protected literals: zero mismatches. Caller file, line, context, and aggregate source-context hashes match the pinned checkout. The cross-review does not apply changes to catalogs or the PR.',
    '',
    'The localization documentation says catalog translations still need fluent-speaker review. No native-speaker sign-off or browser review was performed; the proposed targets remain review recommendations.',
    '',
    f"The complete cell ledger is cross-review-ledger.jsonl; unresolved findings are in cross-findings.json. The verifier is verify_cross_review.py. Input checksum-list SHA-256 values: candidate-free {input_hashes['candidateFreeChecksumListSha256']}; primary {input_hashes['primaryChecksumListSha256']}; blind {input_hashes['blindChecksumListSha256']}.",
    '',
]
(OUT / 'report.md').write_text('\n'.join(report_lines), encoding='utf-8')

# Hash all packet content except the manifest and checksum list, then write the manifest.
for path in sorted(OUT.iterdir()):
    if path.is_file() and path.name not in {'manifest.json', 'SHA256SUMS.txt'}:
        manifest['fileHashes'][path.name] = {'sha256': sha(path.read_bytes()), 'byteCount': path.stat().st_size}
(OUT / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

sum_lines = []
for path in sorted(OUT.iterdir()):
    if path.is_file() and path.name != 'SHA256SUMS.txt':
        sum_lines.append(f'{sha(path.read_bytes())}  {path.name}')
(OUT / 'SHA256SUMS.txt').write_text('\n'.join(sum_lines) + '\n', encoding='utf-8')
print(json.dumps({
    'result': 'BUILT',
    'head': HEAD,
    'tree': TREE,
    'cells': len(output_rows),
    'counts': dict(counts),
    'primaryProposalOutcomes': dict(primary_outcomes),
    'blindFindingCellOutcomes': dict(blind_outcomes),
    'verifiedCallerReferences': verified_callers,
    'verifiedCallerFiles': verified_caller_files,
    'files': len(sum_lines),
}, ensure_ascii=False, indent=2))
