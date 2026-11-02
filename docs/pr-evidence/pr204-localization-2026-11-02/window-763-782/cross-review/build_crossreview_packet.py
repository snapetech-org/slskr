import collections
import hashlib
import json
import pathlib
import re
import subprocess

O = pathlib.Path('/mnt/disks/scratch/task-scratch/slskr-pr204-W763-782-crossreview-by-agent-20261102/packet')
P = pathlib.Path('/mnt/disks/scratch/task-scratch/slskr-pr204-W763-782-primary-20261102/packet')
P743 = pathlib.Path('/mnt/disks/scratch/task-scratch/slskr-pr204-W743-762-primary-20261102/packet')
X743 = pathlib.Path('/mnt/disks/scratch/task-scratch/slskr-pr204-W743-762-crossreview-by-agent-20261102/packet')
W = pathlib.Path('/mnt/disks/scratch/task-worktrees/localization-20261102/slskr-pr204-W743-762-apply')
REPO = 'snapetech-org/slskR'
PR = 204
HEAD = '77a1e481b475381ac45172cf7fd3f5a5c460d7c0'
TREE = 'd4dae6999b34c2060d7662caddbc348917026411'
OLD_HEAD = '32903976fabe543f89dd5950245ba11dd77c8eb3'
OLD_TREE = 'ebf75888b3087e83fe2327495c17611802925f71'
LOCALES = ['ar', 'de', 'es', 'fr', 'hi', 'id', 'ja', 'ko', 'pt-BR', 'vi', 'zh-Hans', 'zh-Hant']

def sha(data):
    if isinstance(data, str):
        data = data.encode()
    return hashlib.sha256(data).hexdigest()

def git(*args):
    return subprocess.check_output(['git', '-C', str(W), *args])

def read_git(path):
    return git('show', f'HEAD:{path}')

def blob(path):
    return git('rev-parse', f'HEAD:{path}').decode().strip()

def live_pr():
    return json.loads(subprocess.check_output(
        ['gh', 'pr', 'view', str(PR), '--repo', REPO,
         '--json', 'state,isDraft,headRefOid,headRefName,baseRefOid,url'], text=True))

def jload(path):
    return json.loads(path.read_text())

def jl(path):
    return [json.loads(line) for line in path.read_text().splitlines()]

def save(name, value):
    (O / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')

def save_jsonl(name, rows):
    (O / name).write_text(''.join(json.dumps(x, ensure_ascii=False, separators=(',', ':')) + '\n' for x in rows))

def placeholders(text):
    return collections.Counter(re.findall(r'\{[^{}]+\}', text))

def markup(text):
    return re.findall(r'</?[A-Za-z][^>]*>', text)

def terminal(text):
    s = text.rstrip()
    if s.endswith((':', '：', '﹕')):
        return 'colon'
    if s.endswith(('?', '؟', '？')):
        return 'question'
    if s.endswith(('!', '！')):
        return 'exclamation'
    if s.endswith(('.', '。', '｡', '۔', '।')):
        return 'sentence-terminal'
    if s.endswith(('…', '...')):
        return 'ellipsis'
    return 'none'

def punctuation_compatible(source, target):
    a, b = terminal(source), terminal(target)
    return a == b or (a == 'none' and b == 'sentence-terminal')

assert git('rev-parse', 'HEAD').decode().strip() == HEAD
assert git('rev-parse', 'HEAD^{tree}').decode().strip() == TREE
assert git('status', '--porcelain').decode() == ''
pr_before = live_pr()
assert pr_before['headRefOid'] == HEAD and pr_before['state'] == 'OPEN' and pr_before['isDraft'] is True

# Verify the frozen review packets before cross-reviewing their contents.
for packet in (P, P743, X743):
    subprocess.check_call(['sha256sum', '-c', 'SHA256SUMS'], cwd=packet, stdout=subprocess.DEVNULL)
pm = jload(P / 'manifest.json')
assert pm['head'] == OLD_HEAD and pm['tree'] == OLD_TREE
assert pm['sourceWindow'] == [763, 782] and pm['cells'] == 240
assert pm['livePullRequest']['headRefOid'] == OLD_HEAD
pm743 = jload(P743 / 'manifest.json')
xm743 = jload(X743 / 'manifest.json')
assert pm743['head'] == OLD_HEAD and pm743['tree'] == OLD_TREE
assert xm743['head'] == OLD_HEAD and xm743['tree'] == OLD_TREE
assert xm743['scope']['positions'] == [743, 762]

frozen_inventory_bytes = (P / 'source-inventory.jsonl').read_bytes()
inventory_path = pathlib.Path(pm['sourceInventory']['path'])
inventory_bytes = inventory_path.read_bytes()
assert sha(frozen_inventory_bytes) == pm['sourceInventory']['sha256']
assert sha(inventory_bytes) == pm['sourceInventory']['sha256']
inventory = [json.loads(line) for line in inventory_bytes.decode().splitlines()]
assert len(inventory) == 5437
source_ids = [row['source_id'] for row in inventory[763:783]]
assert len(source_ids) == 20

current_rows = jl(P / 'current-cells.jsonl')
primary_rows = jl(P / 'primary-review-ledger.jsonl')
candidate_rows = jl(P / 'correction-candidates.jsonl')
context_rows = jl(P / 'source-context.jsonl')
caller_pin_rows = jl(P / 'caller-context-pins.jsonl')
prior_reattest_rows = jl(P / 'prior-disposition-reattestation.jsonl')
prior_source_rows = jl(P / 'prior-disposition-source-records.jsonl')
assert len(current_rows) == len(primary_rows) == len(prior_reattest_rows) == len(prior_source_rows) == 240
assert len(candidate_rows) == 43 and len(context_rows) == 20 and len(caller_pin_rows) == 70
assert [r['sourceId'] for r in context_rows] == source_ids
candidate_keys = {(r['sourceIndex'], r['locale']) for r in candidate_rows}
assert len(candidate_keys) == 43

# Re-read all 12 target catalogs at the updated PR head. Current W763–782 values must still
# agree with the frozen cell values, while the catalog blobs themselves may have advanced.
catalogs = {}
catalog_info = {}
for loc in LOCALES:
    info = pm['catalogs'][loc]
    content = read_git(info['path'])
    catalogs[loc] = json.loads(content)
    catalog_info[loc] = {
        'path': info['path'], 'liveBlob': blob(info['path']), 'liveSha256': sha(content),
        'bytes': len(content), 'keys': len(catalogs[loc]),
        'frozenBlobAtPrimaryHead': info['blobOid'], 'frozenSha256AtPrimaryHead': info['sha256']
    }

current_by_key = {(r['sourceIndex'], r['locale']): r for r in current_rows}
primary_by_key = {(r['sourceIndex'], r['locale']): r for r in primary_rows}
prior_by_key = {(r['sourceIndex'], r['locale']): r for r in prior_reattest_rows}
prior_source_by_key = {(r['sourceIndex'], r['locale']): r for r in prior_source_rows}
assert len(current_by_key) == len(primary_by_key) == len(prior_by_key) == len(prior_source_by_key) == 240
assert set(current_by_key) == set(primary_by_key) == set(prior_by_key) == set(prior_source_by_key)
candidate_by_key = {(r['sourceIndex'], r['locale']): r for r in candidate_rows}
assert candidate_keys == {key for key, row in primary_by_key.items() if row['reviewDecision'] == 'propose-correction'}
for key, candidate in candidate_by_key.items():
    primary = primary_by_key[key]
    assert candidate['sourceId'] == primary['sourceId']
    assert candidate['sourceSha256'] == primary['sourceSha256']
    assert candidate['currentTarget'] == primary['currentTarget']
    assert candidate['recommendedTarget'] == primary['recommendedTarget']
    assert candidate['recommendedTargetSha256'] == primary['recommendedTargetSha256']

source_hash_mismatches = []
target_hash_mismatches = []
changed_current_cells = []
for pos, sid in enumerate(source_ids, 763):
    inv = inventory[pos]
    assert inv['source_id'] == sid and inv['source_sha256'] == sha(sid)
for key, row in current_by_key.items():
    pos, loc = key
    sid = row['sourceId']
    pri = primary_by_key[key]
    prev = prior_by_key[key]
    prev_source = prior_source_by_key[key]
    assert sid == source_ids[pos - 763] and row['source'] == sid and pri['source'] == sid
    assert sha(sid) == row['sourceSha256'] == pri['sourceSha256']
    if sha(sid) != prev['sourceSha256'] or prev['liveSourceSha256'] != sha(sid):
        source_hash_mismatches.append({'key': key, 'sourceId': sid})
    live_target = catalogs[loc][sid]
    live_target_hash = sha(live_target)
    if live_target != row['currentTarget']:
        changed_current_cells.append({'sourceIndex': pos, 'sourceId': sid, 'locale': loc,
                                      'frozenTarget': row['currentTarget'], 'liveTarget': live_target,
                                      'frozenTargetSha256': row['currentTargetSha256'],
                                      'liveTargetSha256': live_target_hash})
    if live_target_hash != row['currentTargetSha256'] or live_target_hash != pri['currentTargetSha256']:
        target_hash_mismatches.append({'key': key, 'sourceId': sid})
    assert row['targetFile'] == pm['catalogs'][loc]['path'] == pri['targetFile']
    assert sha(row['currentTarget']) == row['currentTargetSha256']
    assert sha(pri['recommendedTarget']) == pri['recommendedTargetSha256']
    assert placeholders(sid) == placeholders(live_target) == placeholders(pri['recommendedTarget'])
    assert markup(sid) == markup(live_target) == markup(pri['recommendedTarget'])
    assert punctuation_compatible(sid, pri['recommendedTarget'])
    assert prev['sourceId'] == sid and prev['sourceSha256'] == sha(sid)
    assert prev['sourceHashMatches'] is True and prev['targetHashMatches'] is True
    assert prev['priorAuditStatus'] == pri['priorAuditStatus']
    assert prev['reuseDisposition'] == pri['priorDispositionReused']
    assert prev['priorTargetSha256'] == sha(row['currentTarget'])
    assert prev_source['priorStatus'] == prev['priorAuditStatus']
    assert prev_source['priorRecord']['source_sha256'] == sha(sid)
    assert prev_source['priorRecord']['target_sha256'] == sha(row['currentTarget'])
    assert prev_source['reattestation']['liveSourceSha256'] == sha(sid)
    assert prev_source['reattestation']['liveTargetSha256'] == sha(row['currentTarget'])
assert not source_hash_mismatches and not target_hash_mismatches and not changed_current_cells

# Reattest all caller, supporting-context, and test references at the updated head.
pin_kind_counts = collections.Counter(r['kind'] for r in caller_pin_rows)
assert pin_kind_counts['source-reference'] == 43 and pin_kind_counts['test-reference'] == 12
assert sum(v for k, v in pin_kind_counts.items() if k not in ('source-reference', 'test-reference')) == 15
direct_positions = {r['sourceIndex'] for r in caller_pin_rows if r['kind'] == 'source-reference'}
assert direct_positions == set(range(763, 783)) - {768}
context_ref_set = set()
for ctx in context_rows:
    assert ctx['sourceIndex'] in range(763, 783) and ctx['sourceId'] == source_ids[ctx['sourceIndex'] - 763]
    context_ref_set.update((ctx['sourceIndex'], ctx['sourceId'], r['path'], r['line'], r['lineSha256'])
                           for r in ctx['callerReferences'])
pin_ref_set = {(r['sourceIndex'], r['sourceId'], r['path'], r['line'], r['lineSha256'])
               for r in caller_pin_rows if r['kind'] != 'test-reference'}
assert context_ref_set == pin_ref_set
caller_files = {}
caller_errors = []
pin_live_rows = []
for ref in caller_pin_rows:
    assert ref['attestedHead'] == OLD_HEAD and ref['attestedTree'] == OLD_TREE
    content = read_git(ref['path'])
    actual = {'blob': blob(ref['path']), 'sha256': sha(content)}
    if ref['path'] in caller_files and caller_files[ref['path']] != actual:
        caller_errors.append({'path': ref['path'], 'reason': 'inconsistent live file pins'})
    caller_files[ref['path']] = actual
    lines = content.decode('utf-8').splitlines()
    n = ref['line']
    if (actual['blob'] != ref['fileBlob'] or actual['sha256'] != ref['fileSha256'] or
            n < 1 or n > len(lines) or lines[n - 1] != ref['lineText'] or
            sha(lines[n - 1]) != ref['lineSha256']):
        caller_errors.append({'sourceIndex': ref['sourceIndex'], 'sourceId': ref['sourceId'],
                              'path': ref['path'], 'line': n, 'kind': ref['kind'],
                              'reason': 'caller line/blob/hash mismatch'})
    pin_live_rows.append({**ref, 'liveFileBlob': actual['blob'], 'liveFileSha256': actual['sha256'],
                          'lineReattestedAtCurrentHead': True})
assert len(caller_files) == 24 and not caller_errors

# Independently assess the candidates and the accept-current cells. Keep the source and
# caller context in every ledger row; only the three justified target revisions and one
# additional Hindi action-label refinement differ from the primary packet.
OVERRIDES = {
    '763|id': {
        'disposition': 'propose-correction',
        'target': 'Daftar berbagi koleksi tidak tersedia',
        'rationale': 'The caller shows a Shares table of collection share records with audience and permissions. “Berbagi koleksi” alone can describe the act of sharing a collection; adding “Daftar” makes clear that the share list is unavailable.'
    },
    '772|zh-Hans': {
        'disposition': 'propose-correction',
        'target': '评论 (',
        'rationale': 'The JSX immediately appends the count and an ASCII closing parenthesis. Keep the ASCII opening delimiter and the source space before it, but remove the proposed extra space after “(” so the rendered count is not separated from its opening delimiter.'
    },
    '772|zh-Hant': {
        'disposition': 'propose-correction',
        'target': '評論 (',
        'rationale': 'The JSX immediately appends the count and an ASCII closing parenthesis. Keep the ASCII opening delimiter and the source space before it, but remove the proposed extra space after “(” so the rendered count is not separated from its opening delimiter.'
    },
    '775|hi': {
        'disposition': 'propose-refinement',
        'target': 'तुलना करें',
        'rationale': 'The direct caller is a per-node comparison button. “तुलना करना” is understandable as an infinitive label, but the imperative action label “तुलना करें” matches the adjacent Hindi “Compare Pinned” button and is clearer as a button action.'
    }
}

candidate_by_key = {(r['sourceIndex'], r['locale']): r for r in candidate_rows}
assert set(candidate_by_key) == {(r['sourceIndex'], r['locale']) for r in primary_rows
                                 if r['reviewDecision'] == 'propose-correction'}
context_by_id = {r['sourceId']: r for r in context_rows}
cross_rows = []
dispositions = collections.Counter()
per_locale = collections.defaultdict(collections.Counter)
outcomes = collections.Counter()
for key in sorted(primary_by_key):
    pos, loc = key
    p = primary_by_key[key]
    c = current_by_key[key]
    sid = c['sourceId']
    ctx = context_by_id[sid]
    current = catalogs[loc][sid]
    primary_candidate = p['recommendedTarget']
    ov = OVERRIDES.get(f'{pos}|{loc}')
    if ov:
        final_target = ov['target']
        disposition = ov['disposition']
        rationale = ov['rationale']
        outcome = 'revise-primary-candidate' if p['reviewDecision'] == 'propose-correction' else 'add-crossreview-candidate'
    elif p['reviewDecision'] == 'propose-correction':
        final_target = primary_candidate
        disposition = 'propose-correction'
        rationale = 'Independent review agrees that the candidate expresses the source meaning in the pinned caller context and preserves required structure.'
        outcome = 'agree-primary-candidate'
    else:
        final_target = current
        disposition = 'accept-current'
        rationale = 'Independent review accepts the current wording for the pinned caller context; the source meaning and UI role are retained.'
        outcome = 'accept-current'
    assert placeholders(sid) == placeholders(final_target)
    assert markup(sid) == markup(final_target)
    assert punctuation_compatible(sid, final_target)
    if sid.endswith('('):
        assert final_target.endswith('(') and not final_target.endswith('( ')
    protected = p.get('protectedLiterals', [])
    assert all(lit in sid and lit in final_target for lit in protected)
    if '1G1R' in sid:
        assert '1G1R' in final_target
    assert p['sourceSha256'] == sha(sid) and p['currentTargetSha256'] == sha(current)
    assert p['recommendedTargetSha256'] == sha(primary_candidate)
    prior = prior_by_key[key]
    row = {
        'repository': REPO, 'pullRequest': PR, 'liveHead': HEAD, 'liveTree': TREE,
        'primaryPacketHead': OLD_HEAD, 'primaryPacketTree': OLD_TREE,
        'sourceIndex': pos, 'sourceId': sid, 'source': sid, 'sourceSha256': sha(sid),
        'locale': loc, 'targetFile': p['targetFile'],
        'liveCatalogBlob': catalog_info[loc]['liveBlob'], 'liveCatalogSha256': catalog_info[loc]['liveSha256'],
        'frozenPrimaryCatalogBlob': p['targetCatalogBlob'],
        'currentTarget': current, 'currentTargetSha256': sha(current),
        'frozenPrimaryTargetSha256': c['currentTargetSha256'], 'liveTargetMatchesFrozen': current == c['currentTarget'],
        'primaryDisposition': p['reviewDecision'], 'primaryCandidate': primary_candidate,
        'primaryCandidateSha256': sha(primary_candidate), 'primaryRationale': p['rationale'],
        'crossReviewOutcome': outcome, 'crossDisposition': disposition,
        'finalTarget': final_target, 'finalTargetSha256': sha(final_target),
        'independentRationale': rationale, 'confidence': 'moderate',
        'priorAuditStatus': prior['priorAuditStatus'], 'priorDispositionReused': prior['reuseDisposition'],
        'priorFindingId': prior.get('priorFindingId'), 'priorFindingSha256': prior.get('priorFindingSha256'),
        'priorRecommendedTarget': prior.get('priorRecommendedTarget'),
        'priorReason': prior.get('priorReason'), 'priorSourceSha256': prior['priorSourceSha256'],
        'priorTargetSha256': prior['priorTargetSha256'],
        'callerStatus': ctx['callerStatus'], 'standaloneReviewOnly': ctx.get('standaloneReviewOnly', False),
        'sourceCallerContext': ctx['semanticContext'],
        'callerReferences': [{'kind': r.get('kind'), 'path': r['path'], 'line': r['line'],
                              'lineSha256': r['lineSha256']} for r in ctx['callerReferences']],
        'callerReferenceCount': len(ctx['callerReferences']),
        'sourcePlaceholders': sorted(placeholders(sid).elements()),
        'currentPlaceholders': sorted(placeholders(current).elements()),
        'finalPlaceholders': sorted(placeholders(final_target).elements()), 'placeholderParity': 'exact',
        'sourceMarkup': markup(sid), 'currentMarkup': markup(current), 'finalMarkup': markup(final_target),
        'markupParity': 'exact', 'sourceTerminalPunctuation': terminal(sid),
        'currentTerminalPunctuation': terminal(current), 'finalTerminalPunctuation': terminal(final_target),
        'punctuationCompatibility': 'preserved' if terminal(sid) == terminal(final_target)
                                    else 'locale-appropriate terminal added to source without one',
        'protectedLiterals': protected, 'protectedLiteralsPreserved': True,
        'openingDelimiter': '(' if sid.endswith('(') else None,
        'openingDelimiterCompatibleWithCaller': final_target.endswith('(') if sid.endswith('(') else None,
        'nativeSpeakerApproval': False
    }
    cross_rows.append(row)
    dispositions[disposition] += 1
    per_locale[loc][disposition] += 1
    outcomes[outcome] += 1
assert len(cross_rows) == 240 and sum(dispositions.values()) == 240
assert outcomes['agree-primary-candidate'] == 40
assert outcomes['revise-primary-candidate'] == 3
assert outcomes['add-crossreview-candidate'] == 1
assert dispositions == {'accept-current': 196, 'propose-correction': 43, 'propose-refinement': 1}

# Reattest the immediate W762 boundary at the post-W723/W743 live head. The W743 cross-review
# final targets have been applied, so the live 12 locale values should match those exact
# recommended strings and hashes.
boundary = jload(P / 'window-boundary-reattestation.json')
old_boundary_rows = {(r['sourceIndex'], r['locale']): r for r in boundary['previousBoundaryTargetsReattested']}
assert len(old_boundary_rows) == 12
prev_current = jl(P743 / 'current-cells.jsonl')
prev_ledger = jl(P743 / 'primary-review-ledger.jsonl')
prev_cross = jl(X743 / 'crossreview-ledger.jsonl')
prev_current_by_key = {(r['sourceIndex'], r['locale']): r for r in prev_current}
prev_ledger_by_key = {(r['sourceIndex'], r['locale']): r for r in prev_ledger}
prev_cross_by_key = {(r['sourceIndex'], r['locale']): r for r in prev_cross}
assert len([k for k in prev_current_by_key if k[0] == 762]) == 12
boundary_checks = []
for loc in LOCALES:
    key = (762, loc)
    old_b = old_boundary_rows[key]
    old_cell = prev_current_by_key[key]
    old_decision = prev_ledger_by_key[key]
    cross = prev_cross_by_key[key]
    sid = old_cell['sourceId']
    live_target = catalogs[loc][sid]
    live_hash = sha(live_target)
    assert sid == 'Collection items unavailable' == old_b['sourceId']
    assert old_b['previousCurrentTargetSha256'] == old_cell['currentTargetSha256']
    assert old_b['previousDecision'] == old_decision['reviewDecision']
    assert cross['finalTargetSha256'] == sha(cross['finalTarget'])
    assert live_target == cross['finalTarget'] and live_hash == cross['finalTargetSha256']
    boundary_checks.append({
        'sourceIndex': 762, 'sourceId': sid, 'locale': loc,
        'preW743CommitTarget': old_cell['currentTarget'],
        'preW743CommitTargetSha256': old_cell['currentTargetSha256'],
        'preW743PrimaryDisposition': old_decision['reviewDecision'],
        'postW743CrossReviewTarget': cross['finalTarget'],
        'postW743CrossReviewDisposition': cross['crossDisposition'],
        'postW743CrossReviewTargetSha256': cross['finalTargetSha256'],
        'liveTargetAtHead': live_target, 'liveTargetSha256AtHead': live_hash,
        'liveMatchesCrossReviewFinal': True,
        'targetChangedSincePreW743Head': live_target != old_cell['currentTarget']
    })
assert sum(x['targetChangedSincePreW743Head'] for x in boundary_checks) == 7

# Check punctuation, opening delimiter, placeholder/markup parity, and protected literal
# integrity for all current and final values; 1G1R is the exact source literal in W768.
punctuation_failures = sum(not punctuation_compatible(r['source'], r['finalTarget']) for r in cross_rows)
placeholder_failures = sum(placeholders(r['source']) != placeholders(r['finalTarget']) for r in cross_rows)
markup_failures = sum(markup(r['source']) != markup(r['finalTarget']) for r in cross_rows)
protected_failures = sum(not r['protectedLiteralsPreserved'] for r in cross_rows)
delimiter_failures = sum(r['openingDelimiter'] == '(' and not r['openingDelimiterCompatibleWithCaller'] for r in cross_rows)
assert punctuation_failures == placeholder_failures == markup_failures == protected_failures == delimiter_failures == 0

# Re-query the live PR and exact tree after all semantic judgments.
head_after = git('rev-parse', 'HEAD').decode().strip()
tree_after = git('rev-parse', 'HEAD^{tree}').decode().strip()
pr_after = live_pr()
assert head_after == HEAD and tree_after == TREE
assert pr_after['headRefOid'] == HEAD and pr_after['state'] == 'OPEN' and pr_after['isDraft'] is True
assert git('status', '--porcelain').decode() == ''

prior_counts = collections.Counter(r['priorAuditStatus'] for r in prior_reattest_rows)
assert prior_counts == {'accepted': 105, 'correction-needed': 15, 'not-reviewed': 120}
prior_reused = sum(bool(r['reuseDisposition']) for r in prior_reattest_rows)
assert prior_reused == 120
caller_attestation = {
    'references': len(caller_pin_rows), 'kinds': dict(pin_kind_counts),
    'files': len(caller_files), 'uniqueLines': len({(r['path'], r['line']) for r in caller_pin_rows}),
    'filesByPath': caller_files, 'lineErrors': caller_errors,
    'sourceIdsWithNoDirectCaller': [source_ids[i - 763] for i in range(763, 783) if i not in direct_positions]
}
reattestation = {
    'repository': REPO, 'pullRequest': PR,
    'livePullRequestBefore': pr_before, 'livePullRequestAfter': pr_after,
    'oldPrimaryHead': OLD_HEAD, 'oldPrimaryTree': OLD_TREE,
    'currentLiveHead': HEAD, 'currentLiveTree': TREE,
    'headAfterReview': head_after, 'treeAfterReview': tree_after,
    'worktree': str(W), 'worktreeClean': True,
    'sourceInventoryPath': str(inventory_path), 'sourceInventorySha256': sha(inventory_bytes),
    'sourceIdsAttested': 20, 'sourceCurrentCellsAttestedAtCurrentHead': 240,
    'sourceHashMismatches': source_hash_mismatches, 'currentTargetHashMismatches': target_hash_mismatches,
    'currentTargetsChangedSincePrimaryHead': changed_current_cells,
    'targetCatalogsAtCurrentHead': catalog_info,
    'callerPinsReattested': caller_attestation,
    'priorDispositionCountsReattested': dict(prior_counts),
    'priorDispositionRowsReattested': len(prior_reattest_rows),
    'priorAcceptedAndCorrectionRowsReused': prior_reused,
    'freshNotReviewedCells': prior_counts['not-reviewed'],
    'priorSourceAndTargetMismatches': 0,
    'W762BoundaryCellsReattestedAtCurrentHead': len(boundary_checks),
    'W762BoundaryTargetsMatchingW743CrossReviewFinal': sum(x['liveMatchesCrossReviewFinal'] for x in boundary_checks),
    'W762BoundaryCells': boundary_checks,
    'placeholderFailures': placeholder_failures, 'markupFailures': markup_failures,
    'punctuationCompatibilityFailures': punctuation_failures,
    'protectedLiteralFailures': protected_failures, 'openingDelimiterFailures': delimiter_failures,
    'checks': 'pass',
    'checkedAtUtc': subprocess.check_output(['date', '-u', '+%Y-%m-%dT%H:%M:%SZ'], text=True).strip()
}

save_jsonl('crossreview-ledger.jsonl', cross_rows)
save_jsonl('crossreview-caller-contexts.jsonl', [
    {'sourceIndex': r['sourceIndex'], 'sourceId': r['sourceId'], 'source': r['sourceId'],
     'semanticContext': r['semanticContext'], 'callerStatus': r['callerStatus'],
     'standaloneReviewOnly': r.get('standaloneReviewOnly', False),
     'callerReferences': r['callerReferences']} for r in context_rows
])
save_jsonl('crossreview-caller-pins.jsonl', pin_live_rows)
save('crossreview-w762-boundary.json', {'sourceIndex': 762, 'sourceId': 'Collection items unavailable',
      'currentLiveHead': HEAD, 'currentLiveTree': TREE, 'checks': boundary_checks,
      'allTwelveMatchW743CrossReviewFinalTargets': True})
save('crossreview-findings.json', {
    'schemaVersion': 1, 'overrides': OVERRIDES,
    'primaryCandidateCount': 43, 'primaryCandidatesAccepted': 40,
    'primaryCandidateRevisions': 3, 'additionalCrossReviewCandidates': 1,
    'standaloneNoDirectCallerSource': 'Collections — full sets and 1G1R',
    'standaloneDisposition': 'Reviewed from source wording alone; all targets convey collections/full sets and preserve exact 1G1R.',
    'notes': [
        'The Indonesian primary proposal for Collection shares unavailable could describe sharing a collection; the final target says that the collection share list is unavailable.',
        'The two Chinese Comments ( proposals retained an extra space between the ASCII opening parenthesis and the appended count; the final targets remove that extra space.',
        'The Hindi Compare refinement uses a direct action label consistent with Compare Pinned.',
        'W762 live target values match all 12 final targets in the W743–762 cross-review after the intervening localization commits.'
    ],
    'nativeSpeakerApproval': 'outstanding'
})
save('crossreview-reattestation.json', reattestation)
per_locale = {loc: {k: per_locale[loc].get(k, 0) for k in ('accept-current', 'propose-correction', 'propose-refinement', 'hold')}
              for loc in LOCALES}
summary = {
    'schemaVersion': 1, 'repository': REPO, 'pullRequest': PR, 'state': 'OPEN', 'isDraft': True,
    'head': HEAD, 'tree': TREE, 'primaryPacketHead': OLD_HEAD, 'primaryPacketTree': OLD_TREE,
    'sourceWindow': [763, 782], 'sourceIds': 20, 'locales': LOCALES, 'cells': len(cross_rows),
    'primaryDispositionCounts': dict(collections.Counter(r['reviewDecision'] for r in primary_rows)),
    'crossReviewDispositionCounts': dict(dispositions), 'perLocale': per_locale,
    'primaryCorrectionCandidates': 43, 'primaryCandidatesAccepted': 40,
    'primaryCandidateRevisions': 3, 'additionalCrossReviewCandidates': 1,
    'finalCandidateCount': 44, 'finalTargetsDifferFromPrimary': 4,
    'callerReferences': len(caller_pin_rows), 'callerPinKinds': dict(pin_kind_counts),
    'callerFiles': len(caller_files), 'uniqueCallerLines': len({(r['path'], r['line']) for r in caller_pin_rows}),
    'sourceIdsWithNoDirectCaller': ['Collections — full sets and 1G1R'],
    'priorDispositionCounts': dict(prior_counts), 'priorReusedRows': prior_reused,
    'freshNotReviewedCells': prior_counts['not-reviewed'], 'priorSourceAndTargetMismatches': 0,
    'currentWindowCellDriftSincePrimaryHead': len(changed_current_cells),
    'W762BoundaryCellsReattested': len(boundary_checks),
    'W762BoundaryMatchesW743CrossReviewFinal': 12,
    'placeholderFailures': placeholder_failures, 'markupFailures': markup_failures,
    'punctuationCompatibilityFailures': punctuation_failures,
    'protectedLiteralFailures': protected_failures, 'openingDelimiterFailures': delimiter_failures,
    'heldCells': dispositions.get('hold', 0), 'confidence': 'moderate',
    'nativeSpeakerApproval': 'outstanding', 'repositoryOrPrModified': False,
    'testsBuildsScansCIorBrowserRun': False, 'workflowFilesTouched': False,
    'outputPath': str(O)
}
save('summary.json', summary)
(O / 'README.md').write_text(f'''# slskR PR #204 W763–782 independent cross-review

- The primary packet was frozen at `{OLD_HEAD}` / `{OLD_TREE}`. PR #204 is currently OPEN/DRAFT at `{HEAD}` / tree `{TREE}`; the exact current worktree was clean before and after review.
- Reattested 240 source/current-target cells across 20 IDs and 12 locales at the current head. All 240 current target strings and hashes still match the frozen primary inputs; the locale catalog blobs were re-pinned at the new head.
- Independently reviewed all 43 primary corrections and all 197 accept-current cells. Final dispositions: {dict(dispositions)}. The cross-review revises three primary targets (Indonesian Collection shares unavailable; both Chinese Comments ( labels) and adds one Hindi Compare refinement.
- Reattested {len(caller_pin_rows)} source, context, and test references across {len(caller_files)} files. Every ID except “Collections — full sets and 1G1R” has a direct caller; that label was reviewed standalone and exact `1G1R` is preserved in all 12 locales.
- Reattested all 240 prior-audit statuses and hashes: {dict(prior_counts)}. The 105 accepted and 15 correction-needed cells were reused only after exact source/target hash reattestation; the 120 not-reviewed cells remain fresh reviews.
- W762’s 12 live target values were checked against the W743–762 cross-review at the current head. All 12 match its final targets; 7 changed from the pre-commit packet boundary.
- Placeholder, markup, punctuation, protected-literal, and opening-delimiter checks pass. Confidence is moderate; native-speaker approval remains outstanding. No repository/PR edits, tests, builds, scans, CI, browser work, or workflow changes were made.
''')

artifact_files = sorted(x for x in O.iterdir() if x.is_file() and x.name not in {'SHA256SUMS', 'manifest.json'})
manifest = {
    'schemaVersion': 1, 'repository': REPO, 'pullRequest': PR,
    'liveHead': HEAD, 'liveTree': TREE, 'primaryHead': OLD_HEAD, 'primaryTree': OLD_TREE,
    'scope': {'sourcePositions': [763, 782], 'sourceIds': 20, 'locales': LOCALES, 'cells': 240},
    'primaryPacket': {
        'path': str(P), 'sha256sumsSha256': sha((P / 'SHA256SUMS').read_bytes()),
        'manifestSha256': sha((P / 'manifest.json').read_bytes()),
        'currentCellsSha256': sha((P / 'current-cells.jsonl').read_bytes()),
        'primaryLedgerSha256': sha((P / 'primary-review-ledger.jsonl').read_bytes()),
        'candidatesSha256': sha((P / 'correction-candidates.jsonl').read_bytes()),
        'sourceContextSha256': sha((P / 'source-context.jsonl').read_bytes()),
        'callerPinsSha256': sha((P / 'caller-context-pins.jsonl').read_bytes())
    },
    'previousW743Packets': {
        'primaryManifestSha256': sha((P743 / 'manifest.json').read_bytes()),
        'crossReviewManifestSha256': sha((X743 / 'manifest.json').read_bytes()),
        'crossReviewLedgerSha256': sha((X743 / 'crossreview-ledger.jsonl').read_bytes())
    },
    'sourceInventory': {'path': str(inventory_path), 'sha256': sha(inventory_bytes), 'keys': len(inventory)},
    'currentReattestation': {'path': 'crossreview-reattestation.json', 'sha256': sha((O / 'crossreview-reattestation.json').read_bytes()), 'checks': 'pass'},
    'ledger': {'path': 'crossreview-ledger.jsonl', 'rows': len(cross_rows), 'sha256': sha((O / 'crossreview-ledger.jsonl').read_bytes()), 'dispositions': dict(dispositions)},
    'callerPins': {'path': 'crossreview-caller-pins.jsonl', 'rows': len(pin_live_rows), 'sha256': sha((O / 'crossreview-caller-pins.jsonl').read_bytes())},
    'callerContexts': {'path': 'crossreview-caller-contexts.jsonl', 'rows': len(context_rows), 'sha256': sha((O / 'crossreview-caller-contexts.jsonl').read_bytes())},
    'W762Boundary': {'path': 'crossreview-w762-boundary.json', 'cells': len(boundary_checks), 'matchesFinalTargets': 12, 'sha256': sha((O / 'crossreview-w762-boundary.json').read_bytes())},
    'findingsSha256': sha((O / 'crossreview-findings.json').read_bytes()),
    'summarySha256': sha((O / 'summary.json').read_bytes()),
    'readmeSha256': sha((O / 'README.md').read_bytes()),
    'builderSha256': sha((O / 'build_crossreview_packet.py').read_bytes()),
    'artifactFiles': {x.name: {'sha256': sha(x.read_bytes()), 'bytes': x.stat().st_size} for x in artifact_files},
    'nativeSpeakerApproval': 'outstanding', 'repositoryOrPrModified': False,
    'testsBuildsScansCIorBrowserRun': False, 'workflowFilesTouched': False
}
save('manifest.json', manifest)
files = sorted(x for x in O.iterdir() if x.is_file() and x.name != 'SHA256SUMS')
(O / 'SHA256SUMS').write_text(''.join(f'{sha(x.read_bytes())}  {x.name}\n' for x in files))
print(json.dumps({'head': HEAD, 'tree': TREE, 'cells': len(cross_rows),
                  'primaryCandidates': 43, 'revised': 3, 'additional': 1,
                  'dispositions': dict(dispositions), 'callerPins': len(caller_pin_rows),
                  'priorStatuses': dict(prior_counts), 'W762Boundary': len(boundary_checks),
                  'output': str(O)}, ensure_ascii=False, indent=2))
