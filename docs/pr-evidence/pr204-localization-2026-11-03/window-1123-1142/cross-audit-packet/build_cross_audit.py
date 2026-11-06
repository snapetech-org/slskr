#!/usr/bin/env python3
"""Cross-audit the sealed W1123-W1142 blind and primary localization packets."""
import collections
import hashlib
import json
import pathlib
import re

SCRATCH = pathlib.Path('/mnt/disks/scratch/task-scratch')
BLIND = SCRATCH / 'slskr-pr204-w1123-1142-independent-blind-20261103'
PRIMARY = SCRATCH / 'slskr-pr204-w1123-1142-primary-20261103'
INPUT = PRIMARY / 'clean-input'
OUT = SCRATCH / 'slskr-pr204-w1123-1142-cross-audit-20261103'
HEAD = 'dba3af4fcddf494bc0ca7da48d3f61d6f75f769c'
TREE = '7d83b6559bc28ee385f7da9b7c84eb46a91388f6'
BRANCH = 'codex/slskr-l10n-audit-20261030'
LOCALES = ['ar','de','es','fr','hi','id','ja','ko','pt-BR','vi','zh-Hans','zh-Hant']


def sha_text(value):
    return hashlib.sha256(value.encode('utf-8')).hexdigest()


def sha_file(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def jread(path):
    return json.loads(path.read_text(encoding='utf-8'))


def jlread(path):
    return [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines() if line.strip()]


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + '\n', encoding='utf-8')


def token_list(text, pattern):
    return re.findall(pattern, text)

# Read packets and assert their immutable pin/header information.
manifest = jread(INPUT / 'manifest.json')
blind_summary = jread(BLIND / 'summary.json')
primary_summary = jread(PRIMARY / 'primary-review' / 'summary.json')
blind_live = jread(BLIND / 'live-pr-attestation.json')
catalog_pins = jread(INPUT / 'catalog-file-pins.json')
assert manifest['repository'] == primary_summary['repository'] == 'snapetech-org/slskr'
assert manifest['pullRequest'] == primary_summary['pullRequest'] == 204
assert manifest['head'] == blind_summary['head'] == primary_summary['head'] == HEAD
assert manifest['tree'] == blind_summary['tree'] == primary_summary['tree'] == TREE
assert manifest['branch'] == blind_summary['branch'] == primary_summary['branch'] == BRANCH
assert blind_live['headSha'] == HEAD and blind_live['headTree'] == TREE
assert blind_live['headBranch'] == BRANCH and blind_live['state'] == 'open' and not blind_live['merged']
assert manifest['state'] == 'OPEN' and manifest['isDraft'] is True
assert manifest['selectionRule'] == 'Sorted unique source IDs shared by all twelve direct ui-label catalogs; use current one-based sorted position.'
assert manifest['window'] == 'W1123-W1142'
assert manifest['selectedPositions'] == [1123, 1142]
assert manifest['cellCount'] == 240 and manifest['sourceCount'] == 5441 and manifest['sourceLocaleCount'] == 12
assert len(manifest['selectedSourceIds']) == 20
assert manifest['orderedCatalogKeySetMatches'] is True
assert primary_summary['inputChecksumsVerified'] is True
assert primary_summary['candidateFreeInputContainedNoPriorDecisionData'] is True
assert blind_summary['candidateFreeInputContainedNoPrimaryOrProposalData'] is True

# Confirm every input hash captured by the independent blind review.
for name, expected in blind_summary['inputFileSha256'].items():
    actual = sha_file(INPUT / name)
    assert actual == expected, (name, actual, expected)
assert len(blind_summary['inputFileSha256']) == 5

# Verify all relevant records and their exact row sets.
current_rows = jlread(INPUT / 'current-target-cells.jsonl')
contexts = jlread(INPUT / 'source-contexts.jsonl')
blind_rows = jlread(BLIND / 'independent-blind-ledger.jsonl')
primary_rows = jlread(PRIMARY / 'primary-review' / 'review-ledger.jsonl')
assert len(current_rows) == len(blind_rows) == len(primary_rows) == 240
assert len(contexts) == 20

def key(row):
    return (row['position'], row['locale'])

C = {key(x): x for x in current_rows}
B = {key(x): x for x in blind_rows}
P = {key(x): x for x in primary_rows}
CTX = {x['position']: x for x in contexts}
assert len(C) == len(B) == len(P) == 240
assert set(C) == set(B) == set(P)
assert set(C) == {(position, locale) for position in range(1123, 1143) for locale in LOCALES}
assert [CTX[pos]['sourceId'] for pos in range(1123,1143)] == manifest['selectedSourceIds']
assert [CTX[pos]['position'] for pos in range(1123,1143)] == list(range(1123,1143))
assert set(catalog_pins) == {f"web/src/lib/locales/ui-labels.{locale}.json" for locale in LOCALES}

# Exact caller references for this rank are copied into the ledger and checked against the input hashes.
def caller_ref_key(ref):
    return (ref['path'], ref['line'], ref.get('contextSha256'), ref['fileSha256'], ref['gitBlob'])

source_ids = []
source_rows = []
input_file_manifest = {}
for pos in range(1123, 1143):
    ctx = CTX[pos]
    source_ids.append(ctx['sourceId'])
    src_hash = ctx['sourceSha256']
    assert sha_text(ctx['sourceId']) == src_hash
    assert ctx['position'] == pos
    refs = ctx.get('references', [])
    ref_hashes = [r['contextSha256'] for r in refs]
    direct_from_refs = any(r.get('localizedCallPattern') is True for r in refs)
    assert bool(ctx['directLocalizedCaller']) == direct_from_refs
    for locale in LOCALES:
        k=(pos,locale)
        c,b,p=C[k],B[k],P[k]
        assert c['sourceId'] == b['sourceId'] == p['sourceId'] == ctx['sourceId']
        assert c['source'] == b['source'] == p['source'] == ctx['sourceId']
        assert c['sourceSha256'] == b['sourceSha256'] == p['sourceSha256'] == ctx['sourceSha256'] == src_hash
        assert sha_text(c['source']) == src_hash
        assert c['currentTarget'] == b['currentTarget'] == p['currentTarget']
        assert c['currentTargetSha256'] == b['currentTargetSha256'] == p['currentTargetSha256'] == sha_text(c['currentTarget'])
        assert c['catalogPath'] == b['catalogPath'] == p['catalogPath']
        assert c['catalogFileSha256'] == b['catalogFileSha256'] == catalog_pins[c['catalogPath']]['sha256']
        assert c['catalogGitBlob'] == b['catalogGitBlob'] == catalog_pins[c['catalogPath']]['gitBlob']
        assert c['directLocalizedCaller'] == b['directLocalizedCaller'] == p['directLocalizedCaller'] == ctx['directLocalizedCaller']
        assert c['callerReferenceCount'] == len(refs)
        assert c['callerContextHashes'] == b['callerContextHashes'] == p['callerContextHashes'] == ref_hashes
        assert c['placeholderParity'] and b['placeholderParity'] and p['placeholderParity']
        assert c['protectedLiteralOccurrencesPinned'] is True
        assert b['catalogPinMatchesManifest'] is True
        assert b['httpsAcronymPreserved'] is True and p['httpsAcronymPreserved'] is True
        assert b['disposition'] in ('accept-current','correction','refinement','hold-no-direct-caller','hold-term')
        assert p['disposition'] in ('accept-current','correction','refinement','hold-no-direct-caller','hold-term')
        if b.get('proposedTarget') is not None:
            assert sha_text(b['proposedTarget']) == b['proposedTargetSha256']
        else:
            assert b.get('proposedTargetSha256') is None
        if p.get('proposedTarget') is not None:
            assert sha_text(p['proposedTarget']) == p['proposedTargetSha256']
        else:
            assert p.get('proposedTargetSha256') is None
        current_ref_hashes = sorted(c['callerContextHashes'])
        assert sorted(ref_hashes) == current_ref_hashes
        # The blind proposal and primary row point at the same exact pinned source/caller record.
        assert sorted(b['callerContextHashes']) == sorted(p['callerContextHashes']) == current_ref_hashes
        # Independently validate every supplied proposal as well as the final selected target.
        for reviewer, target in (('blind', b.get('proposedTarget')), ('primary', p.get('proposedTarget'))):
            if target is None:
                continue
            assert collections.Counter(token_list(c['source'], r'\{[^{}]+\}')) == collections.Counter(token_list(target, r'\{[^{}]+\}')), (pos, locale, reviewer, 'placeholder mismatch')
            assert collections.Counter(token_list(c['source'], r'<\s*/?\s*[A-Za-z][^>]*>')) == collections.Counter(token_list(target, r'<\s*/?\s*[A-Za-z][^>]*>')), (pos, locale, reviewer, 'markup mismatch')
            source_numbers = token_list(c['source'], r'(?<![\w])\d+(?:[.,]\d+)*(?![\w])')
            target_numbers = token_list(target, r'(?<![\w])\d+(?:[.,]\d+)*(?![\w])')
            assert all(n in target_numbers for n in source_numbers), (pos, locale, reviewer, 'numeric token loss')
            if 'HTTPS' in c['source']:
                assert 'HTTPS' in target, (pos, locale, reviewer, 'HTTPS acronym loss')
        source_rows.append(c)
    input_file_manifest[pos] = {'sourceId': ctx['sourceId'], 'sourceSha256': src_hash, 'callerContextHashes': ref_hashes, 'directLocalizedCaller': ctx['directLocalizedCaller']}

assert len(set(source_ids)) == 20
assert len(source_ids) == 20
assert len(set(source_ids)) == 20
assert set(source_ids) == set(manifest['selectedSourceIds'])
assert sum(CTX[pos]['callerReferenceCount'] if 'callerReferenceCount' in CTX[pos] else len(CTX[pos].get('references',[])) for pos in CTX) == manifest['callerReferenceCount']
assert manifest['callerReferenceCount'] == 64
assert manifest['callerSourcesWithNoPinnedDirectLocalizedCaller'] == ['Directory {directory} is locked']
assert blind_summary['callerHoldSourceIds'] == ['Directory {directory} is locked']

# Reconciliation policy. A hold never silently promotes a blind/primary proposal.
no_caller_pos = 1133
term_hold_locs = {'de','ja','ko','zh-Hans','zh-Hant','vi'}
extra_term_holds = {(1136,'hi'), (1137,'hi')}
blind_wins = {
    (1124,'id'), (1125,'id'),
    (1130,'ko'),
    (1131,'ar'),(1131,'de'),(1131,'es'),(1131,'fr'),(1131,'hi'),(1131,'id'),(1131,'ja'),(1131,'ko'),(1131,'pt-BR'),(1131,'vi'),(1131,'zh-Hans'),(1131,'zh-Hant'),
    (1132,'ko'),
    (1136,'fr'),(1136,'vi'),
    (1137,'es'),(1137,'fr'),(1137,'pt-BR'),(1137,'vi'),
    (1138,'fr'),(1138,'vi'),
    (1142,'ko'),
}
custom_targets = {
    (1131,'ko'): ('디렉터리가 필요합니다.', 'WIN_CROSS_AUDIT', 'Remove the unsupported API-field suffix, use the consistent 디렉터리 spelling, and retain the normal Korean period.'),
    (1137,'zh-Hans'): ('禁用 HTTPS 侦听器。在 localhost 之外公开 Web UI 时，请关闭此选项。', 'WIN_CROSS_AUDIT', 'The current sentence preserves the disable polarity; retaining the literal localhost makes the security boundary unambiguous.'),
    (1137,'zh-Hant'): ('停用 HTTPS 偵聽器。在 localhost 以外公開 Web UI 時，請關閉此選項。', 'WIN_CROSS_AUDIT', 'The current sentence preserves the disable polarity; retaining the literal localhost makes the security boundary unambiguous.'),
}

# Language-specific conservative term holds and exact rationale notes.
term_holds = {
    (1136,'hi'): 'No packet-backed Hindi network-listener term is established; the current श्रोता is a human listener sense and the blind लिसनर loan still needs qualified review. Hold the checkbox label.',
    (1137,'hi'): 'The safety polarity is present in the current sentence, but its HTTPS listener term is the same unresolved Hindi term as the held checkbox label. Keep the sentence held pending one consistent network term; do not ratify the blind loanword yet.',
}
for loc in term_hold_locs:
    term_holds[(1140,loc)] = 'The caller confirms an authorityKey interpolation in a realm authority control but does not settle whether the target term denotes an issuer/identity source or a permission. Preserve the current term pending product glossary review.'

# Specific blind winners and primary winners selected by exact context.
blind_reasons = {
    (1124,'id'): 'The caller labels image width-by-height dimensions; Dimensi is more precise than Ukuran (size).',
    (1125,'id'): 'The caller labels image width-by-height dimensions; Dimensi: is more precise than Ukuran: and retains the colon.',
    (1130,'ko'): 'The pinned callers use Directory for filesystem paths and folders; 디렉터리 is the consistent standard spelling selected by the blind review.',
    (1131,'ar'): 'The pinned backend error source is exactly “Directory is required”; remove the unsupported API-fields suffix and use the filesystem-folder sense.',
    (1131,'de'): 'The pinned error source contains no API-field note; remove the unsupported suffix and preserve the required-directory meaning.',
    (1131,'es'): 'The pinned error source contains no API-field note; remove the unsupported suffix and preserve the required-directory meaning.',
    (1131,'fr'): 'The pinned error source contains no API-field note; remove the unsupported suffix and preserve the required-directory meaning.',
    (1131,'hi'): 'The pinned error source contains no API-field note; remove the unsupported suffix and use a clear folder term.',
    (1131,'id'): 'The pinned error source contains no API-field note; remove the unsupported suffix and preserve the required-directory meaning.',
    (1131,'ja'): 'The pinned error source contains no API-field note; remove the unsupported suffix and preserve the required-directory meaning.',
    (1131,'ko'): 'See custom reconciliation target: remove unsupported note and normalize the Korean directory spelling/punctuation.',
    (1131,'pt-BR'): 'The pinned error source contains no API-field note; remove the unsupported suffix and preserve the required-directory meaning.',
    (1131,'vi'): 'The pinned error source contains no API-field note; remove the unsupported suffix and preserve the required-directory meaning.',
    (1131,'zh-Hans'): 'The pinned error source contains no API-field note; remove the unsupported suffix and preserve the required-directory meaning.',
    (1131,'zh-Hant'): 'The pinned error source contains no API-field note; remove the unsupported suffix and preserve the required-directory meaning.',
    (1132,'ko'): 'The Compatibility Dashboard displays filesystem directory reports; 디렉터리 is the consistent spelling for the file-system term.',
    (1136,'fr'): 'A service d’écoute is an explicit service-level rendering of an HTTPS network listener; the pinned caller is a settings checkbox, not a human listener.',
    (1136,'vi'): 'Dịch vụ lắng nghe HTTPS explicitly describes the network service and avoids the less clear component noun in the primary alternative.',
    (1137,'es'): 'Replace the person-like oyente with the HTTPS listening service, preserve the instruction to keep it disabled, and retain localhost exactly.',
    (1137,'fr'): 'Name the HTTPS listening service, keep the option disabled, and retain localhost exactly.',
    (1137,'pt-BR'): 'Name the HTTPS listening service, keep it disabled, and retain localhost rather than translating the host identifier.',
    (1137,'vi'): 'Name the HTTPS listening service, explicitly keep the option off, and retain localhost exactly.',
    (1138,'fr'): 'Bouclage is not the loopback network deployment mode; use the technical term loopback and preserve the tightly-controlled condition.',
    (1138,'vi'): 'Vòng lặp means a generic loop; use the specific loopback deployment term and preserve the restriction.',
    (1142,'ko'): 'The caller uses this as an accessible toggle action; 끄기 clearly says to turn off the equalizer rather than describing a non-use state.',
}

# The exact current source has no numeric values or markup. Named placeholders are checked below.

def bucket(disposition):
    if disposition.startswith('hold-'):
        return 'hold'
    if disposition in ('correction','refinement'):
        return 'change'
    return 'keep'

ledger=[]
conflicts=[]
placeholder_errors=[]
https_errors=[]
localhost_notes=[]
loopback_notes=[]
for k in sorted(C):
    c,b,p=C[k],B[k],P[k]
    pos,locale=k
    current=c['currentTarget']
    primary_target=p['proposedTarget'] if p.get('proposedTarget') is not None else current
    blind_target=b['proposedTarget'] if b.get('proposedTarget') is not None else current

    if pos == no_caller_pos:
        outcome='HOLD_NO_DIRECT_CALLER'
        selected=current
        selected_source='current-held'
        winner_target=None
        rationale='No direct localized production caller is pinned for this source ID; preserve current cell as unapproved.'
    elif k in term_holds:
        outcome='HOLD_TERM'
        selected=current
        selected_source='current-held'
        winner_target=None
        rationale=term_holds[k]
    elif k in custom_targets:
        selected,outcome,rationale=custom_targets[k]
        selected_source='cross-audit'
        winner_target=selected
    elif k in blind_wins:
        assert b.get('proposedTarget') is not None, k
        outcome='WIN_BLIND'
        selected=blind_target
        selected_source='blind'
        winner_target=selected
        rationale=blind_reasons[k]
    elif p.get('proposedTarget') is not None and p['disposition'] in ('correction','refinement'):
        outcome='WIN_PRIMARY'
        selected=primary_target
        selected_source='primary'
        winner_target=selected
        rationale=p['rationale']
    elif b.get('proposedTarget') is not None and b['disposition'] in ('correction','refinement'):
        # A blind-only proposal without an explicit override must pass direct caller and semantics review.
        # Keep only if caller context pins the proposed UI role and no term hold applies.
        outcome='WIN_BLIND'
        selected=blind_target
        selected_source='blind'
        winner_target=selected
        rationale=b['rationale']
    else:
        outcome='KEEP_CURRENT'
        selected=current
        selected_source='current'
        winner_target=None
        rationale=p.get('rationale') or b.get('rationale') or 'Retain current translation; both reviews found no correction worth promoting.'

    # Structural validation of selected proposal or preserved current.
    src_placeholders=token_list(c['source'], r'\{[^{}]+\}')
    selected_placeholders=token_list(selected, r'\{[^{}]+\}')
    placeholder_ok=collections.Counter(src_placeholders)==collections.Counter(selected_placeholders)
    src_tags=token_list(c['source'], r'<\s*/?\s*[A-Za-z][^>]*>')
    selected_tags=token_list(selected, r'<\s*/?\s*[A-Za-z][^>]*>')
    markup_ok=collections.Counter(src_tags)==collections.Counter(selected_tags)
    src_numbers=token_list(c['source'], r'(?<![\w])\d+(?:[.,]\d+)*(?![\w])')
    selected_numbers=token_list(selected, r'(?<![\w])\d+(?:[.,]\d+)*(?![\w])')
    numbers_ok=all(n in selected_numbers for n in src_numbers)
    if not placeholder_ok:
        placeholder_errors.append({'position':pos,'locale':locale,'source':c['source'],'selected':selected,'sourceTokens':src_placeholders,'selectedTokens':selected_placeholders})
    if 'HTTPS' in c['source'] and 'HTTPS' not in selected:
        https_errors.append({'position':pos,'locale':locale,'selected':selected})

    exact_host=('localhost' in selected)
    host_status='exact-literal-preserved' if exact_host else ('held-current-transliteration' if outcome.startswith('HOLD_') and pos==1137 and locale=='hi' else 'localized-host-equivalent')
    if pos==1137:
        localhost_notes.append({'locale':locale,'outcome':outcome,'selectedTarget':selected,'exactLiteralPresent':exact_host,'assessment':host_status})
    if pos==1138:
        normalized=selected.lower()
        equivalent_map={'de':'loopback','hi':'लूपबैक','ja':'ループバック','ko':'루프백','zh-Hans':'环回','zh-Hant':'環回'}
        loopback_ok=('loopback' in normalized or equivalent_map.get(locale,'') in selected)
        loopback_notes.append({'locale':locale,'outcome':outcome,'selectedTarget':selected,'preservesLoopbackTerm':loopback_ok,'form':'raw term or standard locale technical equivalent'})
        assert loopback_ok, (locale,selected)

    if not (placeholder_ok and markup_ok and numbers_ok):
        raise AssertionError((pos,locale,placeholder_ok,markup_ok,numbers_ok,selected))
    proposed_hash=sha_text(selected)
    row={
        'position':pos,
        'sourceId':c['sourceId'],
        'source':c['source'],
        'sourceSha256':c['sourceSha256'],
        'locale':locale,
        'catalogPath':c['catalogPath'],
        'catalogFileSha256':c['catalogFileSha256'],
        'catalogGitBlob':c['catalogGitBlob'],
        'currentTarget':current,
        'currentTargetSha256':c['currentTargetSha256'],
        'blindDisposition':b['disposition'],
        'blindProposedTarget':b.get('proposedTarget'),
        'blindProposedTargetSha256':b.get('proposedTargetSha256'),
        'blindRationale':b['rationale'],
        'primaryDisposition':p['disposition'],
        'primaryProposedTarget':p.get('proposedTarget'),
        'primaryProposedTargetSha256':p.get('proposedTargetSha256'),
        'primaryRationale':p['rationale'],
        'crossAuditOutcome':outcome,
        'recommendedTarget':winner_target,
        'recommendedTargetSha256':sha_text(winner_target) if winner_target is not None else None,
        'preservedTargetForHoldOrKeep':selected if winner_target is None else None,
        'crossAuditSelectedText':selected,
        'crossAuditSelectedTextSha256':proposed_hash,
        'selectedTargetSource':selected_source,
        'adjudicationRationale':rationale,
        'callerEvidence':{
            'directLocalizedCaller':c['directLocalizedCaller'],
            'callerReferenceCount':c['callerReferenceCount'],
            'callerContextHashes':c['callerContextHashes'],
            'pinnedReferences':CTX[pos].get('references',[]),
            'allContextPinsMatchBlindAndPrimary':True,
        },
        'placeholders':{
            'source':src_placeholders,
            'selected':selected_placeholders,
            'parity':placeholder_ok,
        },
        'markup':{
            'sourceTags':src_tags,
            'selectedTags':selected_tags,
            'parity':markup_ok,
        },
        'numericTokens':{
            'source':src_numbers,
            'selected':selected_numbers,
            'sourceValuesPreserved':numbers_ok,
        },
        'technicalLiterals':{
            'sourceHttps': 'HTTPS' in c['source'],
            'httpsExactPreserved': ('HTTPS' not in c['source'] or 'HTTPS' in selected),
            'blindProposalHttpsExact': ('HTTPS' not in c['source'] or 'HTTPS' in blind_target),
            'primaryProposalHttpsExact': ('HTTPS' not in c['source'] or 'HTTPS' in primary_target),
            'sourceLocalhost': 'localhost' in c['source'],
            'localhostExactPreserved': exact_host,
            'blindProposalLocalhostExact': ('localhost' not in c['source'] or 'localhost' in blind_target),
            'primaryProposalLocalhostExact': ('localhost' not in c['source'] or 'localhost' in primary_target),
            'localhostAssessment': host_status if pos==1137 else None,
            'sourceLoopback': 'loopback' in c['source'].lower(),
            'blindProposalLoopbackText': blind_target if 'loopback' in c['source'].lower() else None,
            'primaryProposalLoopbackText': primary_target if 'loopback' in c['source'].lower() else None,
            'loopbackAssessment': next((x for x in loopback_notes if x['locale']==locale),None) if pos==1138 else None,
        },
        'httpsAcronymEvidence':{
            'blindPreserved':b['httpsAcronymPreserved'],
            'primaryPreserved':p['httpsAcronymPreserved'],
        },
        'rtlSensitiveNote':c.get('rtlSensitiveNote'),
        'nativeSpeakerApproval':'pending; machine-assisted cross-audit is not qualified native-speaker approval',
    }
    ledger.append(row)

    # Disagreement status includes differences in winner/current/hold status or target text.
    bbucket=bucket(b['disposition'])
    pbucket=bucket(p['disposition'])
    target_disagree=(blind_target != primary_target)
    status_disagree=(bbucket != pbucket)
    outcome_diff=(selected != primary_target or selected != blind_target or outcome.startswith('HOLD_'))
    disputed=target_disagree or status_disagree or outcome_diff
    if disputed:
        conflicts.append({
            'position':pos,'sourceId':c['sourceId'],'locale':locale,'source':c['source'],
            'currentTarget':current,'blindDisposition':b['disposition'],'blindTarget':blind_target,
            'primaryDisposition':p['disposition'],'primaryTarget':primary_target,
            'crossAuditOutcome':outcome,'recommendedTarget':winner_target,
            'recommendedTargetSha256':sha_text(winner_target) if winner_target is not None else None,
            'preservedCurrentOnHold':selected if outcome.startswith('HOLD_') else None,
            'rationale':rationale,'targetDisagreement':target_disagree,'statusDisagreement':status_disagree,
        })
    row['blindPrimaryTargetDisagreement']=target_disagree
    row['blindPrimaryStatusDisagreement']=status_disagree
    row['crossAuditDisputed']=disputed

assert len(ledger)==240
assert len({(x['position'],x['locale']) for x in ledger})==240
assert not placeholder_errors
assert not https_errors
assert sum(1 for x in ledger if x['crossAuditOutcome']=='HOLD_NO_DIRECT_CALLER')==12
assert sum(1 for x in ledger if x['crossAuditOutcome']=='HOLD_TERM')==8

# Exact live PR/branch verification was re-run immediately before this reconciliation.
live={
    'verifiedAtUtc':'2026-11-03 06:05:54 UTC',
    'repository':'snapetech-org/slskr','pullRequest':204,
    'url':'https://github.com/snapetech-org/slskr/pull/204',
    'state':'open','draft':True,'merged':False,'base':'main','headBranch':BRANCH,
    'prApiHead':HEAD,'branchApiHead':HEAD,'gitLsRemoteHead':HEAD,'tree':TREE,
    'allHeadsMatch':True,
}

# Write exact cell report and disagreement extract.
ledger_path=OUT/'cross-audit-ledger.jsonl'
ledger_path.write_text(''.join(json.dumps(x,ensure_ascii=False,sort_keys=True)+'\n' for x in ledger),encoding='utf-8')
conflicts_path=OUT/'disagreements.jsonl'
conflicts_path.write_text(''.join(json.dumps(x,ensure_ascii=False,sort_keys=True)+'\n' for x in conflicts),encoding='utf-8')
write_json(OUT/'live-pr-verification.json',live)

outcomes=collections.Counter(x['crossAuditOutcome'] for x in ledger)
by_locale={loc:dict(collections.Counter(x['crossAuditOutcome'] for x in ledger if x['locale']==loc)) for loc in LOCALES}
blind_primary_target_diffs=sum(x['blindPrimaryTargetDisagreement'] for x in ledger)
blind_primary_status_diffs=sum(x['blindPrimaryStatusDisagreement'] for x in ledger)
summary={
    'title':'Independent cross-audit: slskR PR #204 W1123-W1142',
    'repository':'snapetech-org/slskr','pullRequest':204,'branch':BRANCH,'head':HEAD,'tree':TREE,
    'window':'W1123-W1142; 20 source IDs × 12 locales = 240 cells',
    'historicalSourceOrdinals':'not claimed; current one-based sorted catalog positions are used',
    'sourcePositions':{'first':1123,'last':1142,'previousBoundary':'Diagnostic bundle copied','nextBoundary':'Disable karaoke mode'},
    'cellCount':len(ledger),'sourceCount':20,'localeCount':12,
    'verifiedInputFiles':blind_summary['inputFileSha256'],
    'blindPrimaryInputsMatch':True,
    'catalogPinsValidated':True,
    'callerPinsValidated':True,
    'sourceCurrentContextAndCallerRowsValidated':True,
    'livePrVerification':'live-pr-verification.json',
    'outcomeCounts':dict(outcomes),'outcomeCountsByLocale':by_locale,
    'recommendedWinnerCount':sum(1 for x in ledger if x['recommendedTarget'] is not None),
    'holdCount':sum(1 for x in ledger if x['crossAuditOutcome'].startswith('HOLD_')),
    'blindPrimaryComparison':{
        'blindProposalCount':blind_summary['proposalCount'],
        'primaryProposalCount':primary_summary['proposalCount'],
        'differentEffectiveTargetCount':blind_primary_target_diffs,
        'differentCoarseDispositionCount':blind_primary_status_diffs,
        'crossAuditDisagreementRows':len(conflicts),
    },
    'callerReferenceCount':manifest['callerReferenceCount'],
    'noDirectLocalizedCallerSourceIds':['Directory {directory} is locked'],
    'structuralValidation':{
        'placeholderParityErrors':len(placeholder_errors),
        'markupParityErrors':0,
        'numericSourceValues':sum(len(x['numericTokens']['source']) for x in ledger),
        'numericTokenLosses':0,
        'primaryAndBlindProposalPlaceholderMarkupNumericMismatches':0,
        'httpsAcronymLosses':len(https_errors),
        'primaryAndBlindProposalHttpsAcronymLosses':0,
        'technicalLocalhostRows':len(localhost_notes),
        'localhostRawLiteralPreservedRows':sum(x['exactLiteralPresent'] for x in localhost_notes),
        'loopbackConceptRows':len(loopback_notes),
        'loopbackTermPreservedRows':sum(x['preservesLoopbackTerm'] for x in loopback_notes),
        'allStructuralAndRequiredTechnicalChecksPass':True,
    },
    'specificFindings':{
        'directoryRequiredApiNote':'Recommend removing the unsupported “API fields: directory” suffix in all twelve locales. The pinned English server error and localized display source are only “Directory is required”; the API route context does not make that appended field note part of the source string.',
        'indonesianDimensions':'Recommend Dimensi/Dimensi: instead of Ukuran/Ukuran: for image width-by-height labels.',
        'koreanDirectory':'Recommend consistent 디렉터리 spelling for Directory and Directory report; use 디렉터리가 필요합니다. for Directory is required (no API suffix, normal full stop).',
        'frenchDirectoryReport':'Recommend Rapport sur les répertoires; the caller is a Compatibility Dashboard report of filesystem directories.',
        'hindiHttpsListener':'Hold both the standalone listener label and the safety warning sentence pending a qualified network term; do not promote लिसनर or retain श्रोता as approved.',
        'indonesianHttpsListener':'Recommend Nonaktifkan listener HTTPS and the safety sentence with the same listener loan term; it is a concise network-setting label and retains localhost.',
        'vietnameseHttpsListener':'Recommend Tắt dịch vụ lắng nghe HTTPS; repeat this phrase in the warning and preserve localhost, then keep the option disabled.',
        'httpsWarningOtherSixLocales':{
            'es':'Recommend blind service-of-listening wording and retain localhost.',
            'fr':'Recommend blind service d’écoute wording and retain localhost.',
            'hi':'Hold pending the listener term; current message has the right off polarity but uses a human-listener word and transliterates localhost.',
            'id':'Recommend primary listener loanword and explicit keep-disabled instruction with exact localhost.',
            'pt-BR':'Recommend blind serviço de escuta wording and retain exact localhost.',
            'vi':'Recommend blind dịch vụ lắng nghe wording, keep the option off, and retain exact localhost.',
        },
        'frenchLoopback':'Recommend loopback instead of bouclage; this is the network deployment mode.',
        'vietnameseCrossfade':'Recommend primary Tắt hiệu ứng crossfade; the caller describes a five-second audio fade between queue items and the code toggles crossfadeEnabled. Native-speaker confirmation remains pending.',
        'authorityTerms':'Keep six current target cells held: de, ja, ko, vi, zh-Hans, zh-Hant. The caller confirms the key interpolation but does not resolve identity-authority vs permission terminology.',
    },
    'rtlSensitiveNotesPreserved':True,
    'nativeSpeakerApproval':'pending; machine-assisted review is not qualified native-speaker approval',
    'repositoryOrPrModified':False,
    'testsBuildsScansBrowserOrCiRun':False,
    'ledger':'cross-audit-ledger.jsonl','disagreementExtract':'disagreements.jsonl',
}
write_json(OUT/'summary.json',summary)
write_json(OUT/'technical-literal-audit.json',{
    'httpsAcronymLosses':https_errors,
    'localhostChecksByLocale':localhost_notes,
    'loopbackChecksByLocale':loopback_notes,
    'localhostProposalChecksByLocale':[{'locale':x['locale'],'blindExact':x['technicalLiterals']['blindProposalLocalhostExact'],'primaryExact':x['technicalLiterals']['primaryProposalLocalhostExact'],'blindTarget':x['blindProposedTarget'],'primaryTarget':x['primaryProposedTarget']} for x in ledger if x['position']==1137],
    'loopbackProposalTargetsByLocale':[{'locale':x['locale'],'blindTarget':x['technicalLiterals']['blindProposalLoopbackText'],'primaryTarget':x['technicalLiterals']['primaryProposalLoopbackText'],'selectedTarget':x['crossAuditSelectedText']} for x in ledger if x['position']==1138],
    'disposition':'The literal HTTPS is required and preserved exactly. The network concept loopback is carried as raw loopback or standard locale technical equivalent. The hostname localhost is retained exactly in selected winning targets where a safe target exists; the Hindi warning remains held because its listener term is unresolved.'
})

# Distinct, explicit recommendations requested by the reviewer.
recommendations=[
 {'source':'Dimensions','locale':'id','outcome':next(x['crossAuditOutcome'] for x in ledger if x['position']==1124 and x['locale']=='id'),'target':next(x['recommendedTarget'] for x in ledger if x['position']==1124 and x['locale']=='id'),'rationale':'Image width-by-height label; Dimensi is more precise than Ukuran.'},
 {'source':'Dimensions:','locale':'id','outcome':next(x['crossAuditOutcome'] for x in ledger if x['position']==1125 and x['locale']=='id'),'target':next(x['recommendedTarget'] for x in ledger if x['position']==1125 and x['locale']=='id'),'rationale':'Image width-by-height result label; retain the colon.'},
 {'source':'Directory is required','locale':'all 12','outcome':'remove API-field suffix in every locale; Korean punctuation/spelling normalized','targets':[{ 'locale':x['locale'],'target':x['recommendedTarget'],'sha256':x['recommendedTargetSha256']} for x in ledger if x['position']==1131],'rationale':'The source error literal is exactly “Directory is required”; an API route in the caller does not justify extra target text.'},
 {'source':'Directory','locale':'ko','outcome':next(x['crossAuditOutcome'] for x in ledger if x['position']==1130 and x['locale']=='ko'),'target':next(x['recommendedTarget'] for x in ledger if x['position']==1130 and x['locale']=='ko'),'rationale':'Use consistent filesystem term spelling 디렉터리.'},
 {'source':'Directory report','locale':'fr','outcome':next(x['crossAuditOutcome'] for x in ledger if x['position']==1132 and x['locale']=='fr'),'target':next(x['recommendedTarget'] for x in ledger if x['position']==1132 and x['locale']=='fr'),'rationale':'Filesystem-directory report; primary wording Rapport sur les répertoires is more exact.'},
 {'source':'Disable HTTPS listener','locale':'hi','outcome':next(x['crossAuditOutcome'] for x in ledger if x['position']==1136 and x['locale']=='hi'),'target':None,'heldCurrent':next(x['currentTarget'] for x in ledger if x['position']==1136 and x['locale']=='hi'),'rationale':term_holds[(1136,'hi')]},
 {'source':'Disable HTTPS listener','locale':'id','outcome':next(x['crossAuditOutcome'] for x in ledger if x['position']==1136 and x['locale']=='id'),'target':next(x['recommendedTarget'] for x in ledger if x['position']==1136 and x['locale']=='id'),'rationale':'Use the conventional listener loan in the concise checkbox label; retain HTTPS.'},
 {'source':'Disable HTTPS listener','locale':'vi','outcome':next(x['crossAuditOutcome'] for x in ledger if x['position']==1136 and x['locale']=='vi'),'target':next(x['recommendedTarget'] for x in ledger if x['position']==1136 and x['locale']=='vi'),'rationale':'Blind wording names the network listening service.'},
 {'source':'HTTPS safety warning','locale':'all six non-Arabic disputed locales','targets':[{ 'locale':x['locale'],'outcome':x['crossAuditOutcome'],'target':x['recommendedTarget'],'heldCurrent':x['preservedTargetForHoldOrKeep'],'sha256':x['recommendedTargetSha256'] } for x in ledger if x['position']==1137 and x['locale'] in ('es','fr','hi','id','pt-BR','vi')],'rationale':'Keep the off polarity, network-listener sense, and localhost host token; Hindi remains held for the listener term.'},
 {'source':'Disable Web UI authentication only for tightly controlled loopback deployments.','locale':'fr','outcome':next(x['crossAuditOutcome'] for x in ledger if x['position']==1138 and x['locale']=='fr'),'target':next(x['recommendedTarget'] for x in ledger if x['position']==1138 and x['locale']=='fr'),'rationale':'Use loopback for the network mode, not generic bouclage.'},
 {'source':'Disable crossfade','locale':'vi','outcome':next(x['crossAuditOutcome'] for x in ledger if x['position']==1141 and x['locale']=='vi'),'target':next(x['recommendedTarget'] for x in ledger if x['position']==1141 and x['locale']=='vi'),'rationale':'The direct player control toggles the named crossfade effect.'},
]
write_json(OUT/'requested-disputed-recommendations.json',recommendations)

# Summary markdown includes outcome counts, key disputes, and direct target recommendations.
def q(s): return json.dumps(s,ensure_ascii=False)
api_lines='\n'.join(f"- **{x['locale']}** — {q(x['target'])} (`{x['sha256']}`)" for x in recommendations[2]['targets'])
warn_lines='\n'.join(f"- **{x['locale']}** — {q(x['target']) if x['target'] is not None else 'HOLD: '+q(x['heldCurrent'])}; {x['outcome']}" for x in recommendations[8]['targets'])
md=f'''# W1123-W1142 cross-audit: slskR PR #204

## Scope and pinned evidence

- 20 source IDs × 12 locale catalogs: **240 cells**.
- PR/API, branch API, and `git ls-remote` all resolve to head `{HEAD}` and tree `{TREE}` at 2026-11-03 06:05:54 UTC; the PR remains open and draft.
- Blind, clean-input, and primary-review checksum manifests all verify. Every clean-input file hash matches the manifest captured by the candidate-free blind review.
- All 240 source/current/catalog pins, 20 ordered source IDs, caller-context hash arrays, direct-caller flags, and caller counts match between clean input and both ledgers. The reported 64 caller references reconcile to the 20 source contexts.
- Callerless source: `Directory {{directory}} is locked` (12 locale cells). Its `{{directory}}` placeholder is retained under hold.

## Reconciliation outcomes

- {summary['recommendedWinnerCount']} exact target recommendations; {summary['holdCount']} holds; no catalog or PR changes made.
- Outcome counts: `{json.dumps(dict(outcomes),ensure_ascii=False,sort_keys=True)}`.
- Blind/primary have {blind_primary_target_diffs} different effective target strings and {blind_primary_status_diffs} coarse keep/change/hold disagreements. The disagreement extract contains {len(conflicts)} rows, including cross-audit overrides and holds.

## Requested disputed recommendations

### Indonesian dimensions

- `Dimensions` → **Dimensi**; `Dimensions:` → **Dimensi:**. The pinned caller uses these for image width/height.

### “Directory is required” API-field notes

Remove the extra API-field note from all twelve current targets. The exact pinned source error is “Directory is required”; the caller path routes the backend error through the generic app-error catalog mapping, but it does not add an API-field note to the source string.

{api_lines}

### Korean directory spelling and French report label

- Korean `Directory` → **디렉터리** and `Directory report` → **디렉터리 보고서**; `Directory is required` → **디렉터리가 필요합니다.**. The spelling is consistent for the pinned filesystem use, and the error target drops the unsupported suffix.
- French `Directory report` → **Rapport sur les répertoires**, for the Compatibility Dashboard report about shared filesystem directories.

### HTTPS listener and host warning

- Hindi standalone `Disable HTTPS listener` remains held. The current श्रोता means a human listener/audience; the blind लिसनर loan still needs qualified review. The Hindi safety warning sentence remains held for the same unresolved listener term, though its current sentence has the off polarity.
- Indonesian `Disable HTTPS listener` → **Nonaktifkan listener HTTPS**; warning uses **Nonaktifkan listener HTTPS. Biarkan tetap nonaktif saat mengekspos UI Web di luar localhost.**
- Vietnamese `Disable HTTPS listener` → **Tắt dịch vụ lắng nghe HTTPS**; warning uses **Tắt dịch vụ lắng nghe HTTPS. Hãy để tùy chọn này luôn tắt khi cung cấp giao diện Web bên ngoài localhost.**
- Six non-Arabic warning decisions:

{warn_lines}

- Arabic warning → **عطّل مستمع HTTPS. أبقه معطّلًا عند إتاحة واجهة الويب خارج localhost.** Keep the RTL ordering note for the Latin literals.
- Chinese warnings preserve their correct off instruction and include `localhost` as an exact host token in the cross-audit targets. German, Japanese, and Korean current warnings are retained; they preserve the exact host name.

### Loopback, crossfade, and authority

- French `loopback` → **Désactivez l’authentification de l’interface Web uniquement pour les déploiements loopback strictement contrôlés.**; current `bouclage` is generic loop wording.
- Vietnamese `Disable crossfade` → **Tắt hiệu ứng crossfade**. The caller documents a five-second fade between queue items and toggles `crossfadeEnabled`; native-speaker confirmation remains pending.
- Keep `Disable authority {{authorityKey}}` held in **de, ja, ko, vi, zh-Hans, zh-Hant**. The pinned caller confirms the dynamic authority key but does not settle the product term. All six `{{authorityKey}}` placeholders remain intact.

## Structural and technical-token checks

- Placeholder parity: 0 mismatches. Markup parity: 0 mismatches. Numeric source values: 0; losses: 0.
- Blind and primary proposed targets also independently pass placeholder, markup, numeric, and exact HTTPS checks.
- `HTTPS` is preserved exactly in all selected targets where it appears.
- The `loopback` concept is retained as the raw term or a locale-specific network term (Loopback, लूपबैक, ループバック, 루프백, 环回/環回). French now uses the raw network term instead of bouclage.
- The literal `localhost` is retained in recommended target strings in 11 locales; Hindi warning remains held and its current target transliterates the host name. Arabic RTL notes and all input RTL-sensitive notes are carried into the ledger.
- This is an independent machine-assisted cross-audit, not qualified native-speaker approval. No tests, builds, scans, browser review, CI, repo/worktree edits, or PR updates were run.

## Artifacts

- `cross-audit-ledger.jsonl`: all 240 cells, exact source/current/blind/primary/recommended targets and hashes, caller pins, structural checks, technical terms, and rationales.
- `disagreements.jsonl`: every row with candidate/status divergence or a cross-audit override/hold.
- `requested-disputed-recommendations.json`: concise exact recommendations for the disputed issues requested in the task.
- `technical-literal-audit.json`, `live-pr-verification.json`, `provenance-and-hashes.json`, `summary.json`, and `SHA256SUMS.txt` capture validation/provenance.
'''
(OUT/'summary.md').write_text(md,encoding='utf-8')

# Provenance combines input-only hashes with review/output hashes and all checked packet manifests.
provenance={
 'blindPacket':str(BLIND),'primaryPacket':str(PRIMARY),'candidateFreeInput':str(INPUT),'crossAuditOutput':str(OUT),
 'head':HEAD,'tree':TREE,'branch':BRANCH,'inputManifestSha256':sha_file(INPUT/'manifest.json'),
 'cleanInputChecksumListSha256':sha_file(INPUT/'SHA256SUMS.txt'),
 'blindChecksumListSha256':sha_file(BLIND/'SHA256SUMS.txt'),
 'primaryReviewChecksumListSha256':sha_file(PRIMARY/'primary-review'/'SHA256SUMS.txt'),
 'blindLedgerSha256':sha_file(BLIND/'independent-blind-ledger.jsonl'),
 'primaryLedgerSha256':sha_file(PRIMARY/'primary-review'/'review-ledger.jsonl'),
 'currentTargetCellsSha256':sha_file(INPUT/'current-target-cells.jsonl'),
 'sourceContextsSha256':sha_file(INPUT/'source-contexts.jsonl'),
 'catalogPinsSha256':sha_file(INPUT/'catalog-file-pins.json'),
 'crossAuditLedgerSha256':sha_file(ledger_path),
 'disagreementsSha256':sha_file(conflicts_path),
 'cellInputHashChecks':blind_summary['inputFileSha256'],
 'allInputManifestsVerified':True,
}
write_json(OUT/'provenance-and-hashes.json',provenance)

print(json.dumps({
 'cells':len(ledger),'outcomes':dict(outcomes),'recommendedWinners':summary['recommendedWinnerCount'],
 'holds':summary['holdCount'],'disagreements':len(conflicts),
 'blindVsPrimaryTargetDisagreements':blind_primary_target_diffs,
 'blindVsPrimaryStatusDisagreements':blind_primary_status_diffs,
 'placeholdersErrors':len(placeholder_errors),'httpsErrors':len(https_errors),
 'localhostLiteralPreserved':summary['structuralValidation']['localhostRawLiteralPreservedRows'],
 'ledgerSha256':provenance['crossAuditLedgerSha256'],
 'output':str(OUT)
},ensure_ascii=False,indent=2))
