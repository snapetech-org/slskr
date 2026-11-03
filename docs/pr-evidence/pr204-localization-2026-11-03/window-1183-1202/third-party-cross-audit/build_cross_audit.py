#!/usr/bin/env python3
"""Third-party cross-audit for slskR PR #204 localization W1183–W1202."""
from pathlib import Path
from collections import Counter
import hashlib
import json
import re
import subprocess

ROOT = Path('/mnt/disks/scratch/task-scratch')
INPUT = ROOT / 'slskr-pr204-w1183-1202-input-20261103/clean-input'
PRIMARY_DIR = ROOT / 'slskr-pr204-w1183-1202-primary-20261103/primary-review'
PRIMARY_LEDGER = PRIMARY_DIR / 'primary-decisions.jsonl'
BLIND_DIR = ROOT / 'slskr-pr204-w1183-1202-blind-20261103'
BLIND_LEDGER = BLIND_DIR / 'blind-decisions.jsonl'
OUT = ROOT / 'slskr-pr204-w1183-1202-third-party-cross-audit-20261103'
HEAD = '8e60a51ec25967df115a3fd8c42872abbec58d8a'
TREE = 'c2ec31432943730f0a8f3ee87687c46b6a4400c2'
BRANCH = 'codex/slskr-l10n-audit-20261030'
REPO = 'snapetech-org/slskR'
LOCALES = ['es', 'zh-Hans', 'hi', 'de', 'ja', 'fr', 'pt-BR', 'ar', 'ko', 'zh-Hant', 'vi', 'id']
PH = re.compile(r'\{[A-Za-z][A-Za-z0-9_]*\}')
MARKUP = re.compile(r'</?[A-Za-z][^>]*>')
NUMBER = re.compile(r'(?<![A-Za-z])\d+(?:[.,]\d+)?%?(?![A-Za-z])')

TARGETS = {}
def set_targets(position, locales, target, disposition, rationale, winner='third-party-cross-audit'):
    for locale in locales:
        TARGETS[(position, locale)] = {
            'target': target[locale] if isinstance(target, dict) else target,
            'decision': disposition[locale] if isinstance(disposition, dict) else disposition,
            'rationale': rationale[locale] if isinstance(rationale, dict) else rationale,
            'winner': winner,
        }

ALL = set(LOCALES)

# Caller-backed changes and adjudications. Unlisted cells retain the current
# value unless both reviewers and the exact context support another disposition.
set_targets(1183, ['fr'], 'Nombre de jours avant l’expiration des éléments non évalués sur l’étagère Discovery', 'refinement',
            'The field is adjacent to “Expire unrated after.” The French candidate should name the expiry period for unrated items on the Discovery shelf, not imply that the shelf itself expires.', 'third-party-cross-audit')
set_targets(1183, ['ko'], '디스커버리 선반 만료 일수', 'correction',
            'The current term reads as a search-shelf expiration date. The pinned numeric input and Discovery-shelf context support Discovery shelf expiry days.', 'primary-and-blind-consensus')
set_targets(1183, ['vi'], 'Số ngày trước khi các mục chưa được đánh giá hết hạn trên kệ Discovery', 'correction',
            'The neighboring caller label is “Expire unrated after”; this target correctly identifies the days before unrated shelf items expire.', 'independent-blind')

set_targets(1184, ALL, {
    'es':'Cerrar','zh-Hans':'关闭','hi':'बंद करें','de':'Schließen','ja':'閉じる','fr':'Fermer',
    'pt-BR':'Fechar','ar':'إغلاق','ko':'닫기','zh-Hant':'關閉','vi':'Đóng','id':'Tutup'
}, 'correction', 'The source is the action on a port-forwarding reminder. The pinned UI caller places it on the reminder message; the current reject/fire/release meanings are wrong, and Close is an appropriate dismissal action.', 'primary-and-blind-consensus')

# Strip unsourced API-field notes while preserving the exact protected name.
set_targets(1188, ALL, {loc: None for loc in LOCALES}, 'correction',
            'Both server callers and the allowlist return only “DisplayName is required.” Remove the extra API-field parenthetical; preserve the exact DisplayName literal.', 'third-party-cross-audit')

set_targets(1189, ['vi'], 'Các bồi thẩm viên bất đồng quan điểm', 'correction',
            'The pinned Quarantine Jury caller displays aggregate.dissentingJurors. The candidate identifies jurors who dissent rather than merely different colleagues.', 'primary-and-blind-consensus')

set_targets(1190, ['ar'], 'المستخدمون الفريدون', 'correction',
            'The table columns and caller show a distinct-user count. “Unique users” avoids the current implication of distinguished users.', 'primary-and-blind-consensus')
set_targets(1190, ['id'], 'Pengguna unik', 'refinement',
            'This is an analytics column for distinct users; “unique users” is more direct than “different users.”', 'independent-blind')
set_targets(1190, ['ja'], 'ユニークユーザー', 'refinement',
            'The pinned analytics table counts distinct user identities. The standard unique-user label is more precise than “individual users.”', 'independent-blind')
set_targets(1190, ['ko'], '고유 사용자', 'refinement',
            'The pinned analytics table counts distinct user identities. “Unique users” states the metric more precisely than “individual users.”', 'independent-blind')

set_targets(1191, ['ar'], 'أقران فريدون', 'correction',
            'The UI caller labels the sum of upload/download distinctUsers as peers. Replace the current “distinguished/their peers” reading with unique network peers.', 'primary')
set_targets(1191, ['de'], 'Eindeutige Peers', 'correction',
            'The UI caller counts distinct remote users participating in transfers. “Kollegen” means colleagues; the technical loanword Peers fits the network metric.', 'primary-and-blind-consensus')
set_targets(1191, ['es'], 'Pares distintos', 'correction',
            'The current compañeros means companions/colleagues. The caller is a network-peer count; pares is the peer term in this context.', 'independent-blind')
set_targets(1191, ['zh-Hans'], '不同的网络对等方', 'correction',
            'The current 同行 suggests colleagues. The caller is a distinct-user network statistic; explicitly name network peers.', 'independent-blind')
set_targets(1191, ['hi'], 'विशिष्ट पीयर', 'correction',
            'The caller is a distinct peer/user metric, not coworkers. Preserve the established technical peer term rather than सहकर्मी.', 'primary-and-blind-consensus')
set_targets(1191, ['id'], 'Peer unik', 'correction',
            'The current rekan means colleagues. The pinned caller counts unique network peers; Peer is the appropriate technical term.', 'independent-blind')
set_targets(1191, ['ko'], '고유 피어', 'correction',
            'The current 동료 means colleagues. The caller counts network peers; use the technical peer term and distinctness.', 'independent-blind')
set_targets(1191, ['zh-Hant'], '不同的網路對等方', 'correction',
            'The current 同行 suggests colleagues. The caller is a distinct-user network statistic; explicitly name network peers.', 'independent-blind')
set_targets(1191, ['vi'], 'Các peer riêng biệt', 'correction',
            'The pinned caller sums distinct user counts for transfers. The current đồng nghiệp means colleagues; the blind candidate uses the recognizable technical peer term. Native terminology review remains advisable.', 'independent-blind')

set_targets(1194, ['ar'], 'المجال', 'correction',
            'The callers label a MediaCore content-registry/retrieval domain, not a personal specialty. المجال names the content domain.', 'primary-and-blind-consensus')
set_targets(1194, ['hi'], 'डोमेन', 'correction',
            'The MediaCore panels use Domain for a ContentID namespace. The technical transliteration is clearer than कार्यक्षेत्र (“field/work area”).', 'independent-blind')
set_targets(1194, ['vi'], 'Lĩnh vực', 'correction',
            'The current lãnh địa means territory. The MediaCore caller uses a content-registry domain; lĩnh vực is the appropriate domain/field sense.', 'primary-and-blind-consensus')

set_targets(1195, ['zh-Hans'], '按领域搜索', 'correction',
            'The card description says this searches ContentIDs by domain. 按领域搜索 makes that relation explicit and avoids the DNS-specific 域名.', 'independent-blind')
set_targets(1195, ['zh-Hant'], '按領域搜尋', 'correction',
            'The card description says this searches ContentIDs by domain. 按領域搜尋 makes that relation explicit and avoids the DNS-specific 域名.', 'independent-blind')
set_targets(1195, ['vi'], 'Tìm kiếm theo lĩnh vực', 'correction',
            'The helper text defines a content-registry search by domain. The current tên miền suggests a DNS hostname; lĩnh vực matches the content-domain meaning.', 'primary-and-blind-consensus')

# The literal error response and allowlist omit these extra API-field notes.
set_targets(1197, ['es'], 'Se requiere el dominio.', 'correction',
            'The server emits only “Domain is required.” Remove the extra API-field note; the route parameter is a MediaCore content domain.', 'independent-blind')
set_targets(1197, ['zh-Hans'], '必须提供领域。', 'correction',
            'The server emits only “Domain is required.” Remove the extra API-field note and use the content-domain sense, not a DNS domain name.', 'independent-blind')
set_targets(1197, ['hi'], 'डोमेन आवश्यक है।', 'correction',
            'The server emits only “Domain is required.” Remove the extra API-field note; the exact route parameter remains a technical domain.', 'independent-blind')
set_targets(1197, ['de'], 'Die Domäne ist erforderlich.', 'correction',
            'The server emits only “Domain is required.” Remove the unsupported API-field parenthetical.', 'independent-blind')
set_targets(1197, ['ja'], 'ドメインが必要です。', 'correction',
            'The server emits only “Domain is required.” Remove the unsupported API-field parenthetical.', 'independent-blind')
set_targets(1197, ['pt-BR'], 'O domínio é obrigatório.', 'correction',
            'The server emits only “Domain is required.” Remove the unsupported API-field parenthetical.', 'independent-blind')
set_targets(1197, ['ar'], 'المجال مطلوب.', 'correction',
            'The server emits only “Domain is required.” Remove the unsupported API-field note and use the MediaCore content-domain sense.', 'independent-blind')
set_targets(1197, ['ko'], '도메인이 필요합니다.', 'correction',
            'The server emits only “Domain is required.” Remove the unsupported API-field parenthetical.', 'independent-blind')
set_targets(1197, ['zh-Hant'], '必須提供領域。', 'correction',
            'The server emits only “Domain is required.” Remove the unsupported API-field note and use the content-domain sense rather than a DNS domain name.', 'independent-blind')
set_targets(1197, ['vi'], 'Cần có lĩnh vực.', 'correction',
            'The server emits only “Domain is required.” Remove the API-field note and avoid the DNS-specific miền for this content-registry domain.', 'independent-blind')
set_targets(1197, ['id'], 'Domain wajib diisi.', 'correction',
            'The server emits only “Domain is required.” Remove the unsupported API-field parenthetical.', 'independent-blind')

set_targets(1198, ALL, None, 'hold',
            'The pinned security-settings caller confirms a “Domain to front through” security option and CDN examples, but does not define the fronting mechanism or supply an approved localized security term. Hold all locales pending product terminology. Preserve exact CDN in any future target.', 'primary-and-blind-consensus')

set_targets(1199, ['ar'], 'المجال:', 'correction',
            'This result label is a MediaCore ContentID domain. المجال is consistent with the corrected retrieval/search labels.', 'primary-and-blind-consensus')
set_targets(1199, ['vi'], 'Lĩnh vực:', 'correction',
            'This result label is a MediaCore ContentID domain, not a geographic territory. Lĩnh vực matches the neighboring content-domain labels.', 'primary-and-blind-consensus')

set_targets(1200, ['zh-Hans'], '领域', 'correction',
            'The MediaCore dashboard counts content-registry domains; 域名 is DNS-specific. Use the same content-domain term as neighboring labels.', 'primary-and-blind-consensus')
set_targets(1200, ['zh-Hant'], '領域', 'correction',
            'The MediaCore dashboard counts content-registry domains; 網域 is DNS-specific. Use the same content-domain term as neighboring labels.', 'primary-and-blind-consensus')
set_targets(1200, ['vi'], 'Lĩnh vực', 'correction',
            'The MediaCore dashboard counts content-registry domains; tên miền suggests DNS hostnames. Use the content-domain term.', 'primary-and-blind-consensus')

set_targets(1201, ['zh-Hans'], '领域：', 'correction',
            'The MediaCore statistics panel counts content-registry domains. Use the content-domain term and preserve Chinese full-width punctuation.', 'primary')
set_targets(1201, ['zh-Hant'], '領域：', 'correction',
            'The MediaCore statistics panel counts content-registry domains. Use the content-domain term and preserve Chinese full-width punctuation.', 'primary')
set_targets(1201, ['vi'], 'Lĩnh vực:', 'correction',
            'The MediaCore statistics panel counts content-registry domains, not DNS hostnames. Use the content-domain term.', 'primary-and-blind-consensus')

set_targets(1202, ['ja'], '完了', 'correction',
            'The button is labeled Done and uses a check icon; the pinned context confirms the task is complete while the modal closes. 完了 preserves the visible “Done” meaning; 閉じる would replace it with Close.', 'primary')

def sha(data):
    if isinstance(data, str):
        data = data.encode('utf-8')
    return hashlib.sha256(data).hexdigest()

def read_jsonl(path):
    return [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines() if line.strip()]

def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

def write_jsonl(path, rows):
    path.write_text(''.join(json.dumps(row, ensure_ascii=False, separators=(',', ':')) + '\n' for row in rows), encoding='utf-8')

def verify_sums(path):
    results = []
    for line in path.read_text(encoding='utf-8').splitlines():
        if not line.strip():
            continue
        expected, relative = line.split(None, 1)
        relative = relative.strip().lstrip('*')
        actual = sha((path.parent / relative).read_bytes())
        results.append({'path': relative, 'expected': expected, 'actual': actual, 'matches': expected == actual})
    assert results and all(row['matches'] for row in results), results
    return results

def verify_live_pins():
    pr = json.loads(subprocess.check_output(
        ['gh', 'pr', 'view', '204', '--repo', REPO, '--json', 'state,isDraft,headRefName,headRefOid,baseRefName'],
        text=True,
    ))
    assert pr == {'baseRefName':'main','headRefName':BRANCH,'headRefOid':HEAD,'isDraft':True,'state':'OPEN'}, pr
    commit = json.loads(subprocess.check_output(
        ['gh', 'api', f'repos/{REPO}/git/commits/{HEAD}'], text=True,
    ))
    assert commit['sha'] == HEAD and commit['tree']['sha'] == TREE, (commit['sha'], commit['tree']['sha'])
    remote_lines = subprocess.check_output(
        ['git', 'ls-remote', f'https://github.com/{REPO}.git', f'refs/heads/{BRANCH}', 'refs/pull/204/head'],
        text=True,
    ).splitlines()
    remote = {line.split()[1]: line.split()[0] for line in remote_lines if line.split()}
    assert remote.get(f'refs/heads/{BRANCH}') == HEAD and remote.get('refs/pull/204/head') == HEAD, remote
    return {'pr':pr,'commitTree':commit['tree']['sha'],'remoteRefs':remote}

def normalized_primary(p):
    if p['disposition'] == 'hold':
        return 'hold'
    if p['disposition'] == 'accept-current':
        return 'accept-current'
    return 'proposal'

def normalized_blind(b):
    if b['decision'] == 'hold':
        return 'hold'
    if b['decision'] == 'accept-current':
        return 'accept-current'
    return 'proposal'

def occurrences(text, literal):
    return text.count(literal)

def main():
    assert not (OUT / 'cross-audit-ledger.jsonl').exists(), 'cross-audit output already exists'
    input_checks = verify_sums(INPUT / 'SHA256SUMS.txt')
    primary_checks = verify_sums(PRIMARY_DIR / 'SHA256SUMS.txt')
    blind_checks = verify_sums(BLIND_DIR / 'SHA256SUMS.txt')
    blind_input_checks = verify_sums(BLIND_DIR / 'input/SHA256SUMS.txt')
    input_manifest = json.loads((INPUT / 'manifest.json').read_text(encoding='utf-8'))
    input_attestation = json.loads((INPUT / 'PR-attestation.json').read_text(encoding='utf-8'))
    primary_summary = json.loads((PRIMARY_DIR / 'summary.json').read_text(encoding='utf-8'))
    blind_summary = json.loads((BLIND_DIR / 'summary.json').read_text(encoding='utf-8'))
    blind_live = json.loads((BLIND_DIR / 'live-pr-verification.json').read_text(encoding='utf-8'))
    assert input_manifest['head'] == HEAD and input_manifest['tree'] == TREE
    assert input_attestation['headRefOid'] == HEAD and input_attestation['localWorktreeTree'] == TREE
    assert input_attestation['remotePullRefHead'] == HEAD
    assert primary_summary['head'] == HEAD and primary_summary['tree'] == TREE
    assert blind_summary['head'] == HEAD and blind_summary['tree'] == TREE
    live = verify_live_pins()
    assert blind_live['head'] == HEAD and blind_live['tree'] == TREE and blind_live['remoteBranchHead'] == HEAD

    input_rows = read_jsonl(INPUT / 'current-target-cells.jsonl')
    contexts = read_jsonl(INPUT / 'source-contexts.jsonl')
    primary_rows = read_jsonl(PRIMARY_LEDGER)
    blind_rows = read_jsonl(BLIND_LEDGER)
    assert len(input_rows) == len(primary_rows) == len(blind_rows) == 240
    assert len(contexts) == 20 and sum(row['callerReferenceCount'] for row in contexts) == 37
    assert input_manifest['callerReferenceCount'] == 37
    assert primary_summary['callerReferenceCount'] == 37
    assert blind_summary['callerReferencesVerified'] == 37
    assert len({(row['position'], row['locale']) for row in input_rows}) == 240
    expected_keys = {(pos, locale) for pos in range(1183,1203) for locale in LOCALES}
    assert {(row['position'], row['locale']) for row in input_rows} == expected_keys

    source_context = {row['position']: row for row in contexts}
    pmap = {(row['position'], row['locale']): row for row in primary_rows}
    bmap = {(row['position'], row['locale']): row for row in blind_rows}
    assert set(pmap) == set(bmap) == expected_keys

    # The blind packet's embedded candidate-free input must match the canonical input.
    names = [line.split(None,1)[1].strip().lstrip('*') for line in (INPUT/'SHA256SUMS.txt').read_text().splitlines() if line.strip()]
    copied_input_deltas = [name for name in names if (INPUT/name).read_bytes() != (BLIND_DIR/'input'/name).read_bytes()]
    assert not copied_input_deltas, copied_input_deltas
    assert (INPUT/'SHA256SUMS.txt').read_bytes() == (BLIND_DIR/'input/SHA256SUMS.txt').read_bytes()

    audit_rows = []
    disagreements = []
    final_counts = Counter()
    primary_counts = Counter(row['disposition'] for row in primary_rows)
    blind_counts = Counter(row['decision'] for row in blind_rows)
    candidate_protected_failures = []
    current_protected_failures = []
    integrity_failures = []
    caller_reference_total = sum(row['callerReferenceCount'] for row in contexts)

    for item in input_rows:
        pos, locale = item['position'], item['locale']
        p, b = pmap[(pos,locale)], bmap[(pos,locale)]
        ctx = source_context[pos]
        refs = ctx['references']
        assert item['sourceKey'] == p['sourceKey'] == b['sourceKey'] == ctx['sourceKey']
        assert item['sourceKeySha256'] == p['sourceKeySha256'] == b['sourceKeySha256'] == ctx['sourceKeySha256']
        assert item['currentTarget'] == p['currentTarget'] == b['currentTarget']
        assert item['currentTargetSha256'] == p['currentTargetSha256'] == b['currentTargetSha256']
        assert item['catalogPath'] == b['catalogPath']
        assert item['catalogGitBlob'] == b['catalogGitBlob']
        assert item['catalogSha256'] == b['catalogSha256']
        assert p['head'] == HEAD and p['tree'] == TREE
        assert p['pullRequest'] == 204 and p['repository'] == REPO
        assert p['position'] == b['position'] == pos and p['locale'] == b['locale'] == locale

        expected_ref_pins = sorted((ref['path'],ref['line'],ref['contextSha256'],ref['role']) for ref in refs)
        primary_ref_pins = sorted((ref['path'],ref['line'],ref['contextSha256'],ref['role']) for ref in p['callerContextPins'])
        blind_ref_pins = sorted((ref['path'],ref['line'],ref['contextSha256'],ref['role']) for ref in b['callerEvidence']['references'])
        assert expected_ref_pins == primary_ref_pins == blind_ref_pins
        assert len(refs) == item['sourceCallerCount']

        source = item['sourceKey']
        current = item['currentTarget']
        primary_target = p['proposedTarget'] if p['proposedTarget'] is not None else current
        blind_target = b['selectedTarget']
        assert sha(current) == item['currentTargetSha256']
        assert sha(source) == item['sourceKeySha256']

        target_info = TARGETS.get((pos,locale))
        if pos == 1188:
            # Every current value adds an API-field parenthetical absent from the
            # exact server literal and allowlist. Strip it, including French.
            target = current.split(' (',1)[0]
            decision = 'correction'
            rationale = 'The server callers and allowlist return only “DisplayName is required.” The parenthetical is an added API-field note; remove it while retaining exact DisplayName.'
            winner = 'third-party-cross-audit'
        elif pos == 1197:
            if locale == 'fr':
                target = current
                decision = 'accept-current'
                rationale = 'French already matches the server error without an added API-field note; retain the direct validation wording.'
                winner = 'primary-and-blind-consensus'
            else:
                target_info = TARGETS[(pos,locale)]
                target, decision, rationale, winner = target_info['target'], target_info['decision'], target_info['rationale'], target_info['winner']
        elif pos == 1198:
            target = None
            decision = 'hold'
            rationale = 'Caller context identifies the security setting and CDN examples but does not define the domain-fronting mechanism or approved localized terminology. Keep the current value pending product terminology.'
            winner = 'primary-and-blind-consensus' if p['disposition']=='hold' and b['decision']=='hold' else 'third-party-cross-audit'
        elif target_info:
            target, decision, rationale, winner = target_info['target'], target_info['decision'], target_info['rationale'], target_info['winner']
        else:
            target = current
            decision = 'accept-current'
            rationale = 'The current target preserves the source meaning in the pinned caller context; neither review identifies a necessary correction.'
            winner = 'primary-and-blind-consensus' if primary_target == blind_target == current else 'primary'

        protected_required_p = p['protectedLiteralsRequired'] or []
        protected_required_b = b['protectedLiteralsRequired'] or []
        assert protected_required_p == protected_required_b
        protected_checks = []
        for literal in protected_required_p:
            source_count = occurrences(source, literal)
            current_count = occurrences(current, literal)
            p_count = occurrences(primary_target, literal)
            b_count = occurrences(blind_target, literal)
            final_count = occurrences(target, literal) if target is not None else None
            current_ok = current_count >= source_count and source_count > 0
            final_ok = (final_count is not None and final_count >= source_count) if target is not None else None
            if not current_ok:
                current_protected_failures.append({'position':pos,'locale':locale,'literal':literal,'sourceCount':source_count,'currentCount':current_count})
            if target is not None and not final_ok:
                candidate_protected_failures.append({'position':pos,'locale':locale,'literal':literal,'sourceCount':source_count,'finalCount':final_count})
            protected_checks.append({
                'literal':literal,'sourceCount':source_count,'currentCount':current_count,
                'primaryRecommendedCount':p_count,'blindSelectedCount':b_count,
                'crossAuditTargetCount':final_count,'currentPass':current_ok,'crossAuditPass':final_ok,
            })

        source_placeholders = Counter(PH.findall(source))
        current_placeholders = Counter(PH.findall(current))
        final_placeholders = Counter(PH.findall(target)) if target is not None else current_placeholders
        source_markup = Counter(MARKUP.findall(source))
        current_markup = Counter(MARKUP.findall(current))
        final_markup = Counter(MARKUP.findall(target)) if target is not None else current_markup
        source_numbers = NUMBER.findall(source)
        current_numbers = NUMBER.findall(current)
        final_numbers = NUMBER.findall(target) if target is not None else current_numbers
        placeholder_ok = source_placeholders == final_placeholders
        markup_ok = source_markup == final_markup
        numeric_ok = source_numbers == final_numbers
        if not (placeholder_ok and markup_ok and numeric_ok):
            integrity_failures.append({'position':pos,'locale':locale,'placeholderPass':placeholder_ok,'markupPass':markup_ok,'numericPass':numeric_ok})
        assert placeholder_ok and markup_ok and numeric_ok, (pos,locale)

        if pos == 1198:
            hold_reason = 'Product-approved localized terminology for the domain-fronting security feature is unavailable; exact CDN must remain unchanged in any future target.'
        else:
            hold_reason = None
        if decision == 'hold':
            assert target is None and hold_reason
        else:
            assert target is not None

        p_norm, b_norm = normalized_primary(p), normalized_blind(b)
        is_disagreement = primary_target != blind_target or p_norm != b_norm
        if is_disagreement:
            disagreements.append({
                'position':pos,'locale':locale,'sourceKey':source,'currentTarget':current,
                'primaryDisposition':p['disposition'],'primaryTarget':primary_target,
                'blindDecision':b['decision'],'blindTarget':blind_target,
                'crossAuditDecision':decision,'crossAuditTarget':target,
                'resolution': 'retained-hold' if decision == 'hold' else 'adjudicated',
                'winner':winner,'rationale':rationale,
            })

        final_counts[decision] += 1
        audit_rows.append({
            'repository':REPO,'pullRequest':204,'head':HEAD,'tree':TREE,'window':'W1183-W1202',
            'position':pos,'sourceKey':source,'sourceKeySha256':item['sourceKeySha256'],
            'locale':locale,'catalogPath':item['catalogPath'],'catalogSha256':item['catalogSha256'],
            'catalogGitBlob':item['catalogGitBlob'],'currentTarget':current,
            'currentTargetSha256':item['currentTargetSha256'],
            'callerReferenceCount':len(refs),
            'callerContextReferences':[{'path':ref['path'],'line':ref['line'],'role':ref['role'],'contextSha256':ref['contextSha256']} for ref in refs],
            'primaryDisposition':p['disposition'],'primaryProposedTarget':p['proposedTarget'],'primaryRecommendedTarget':primary_target,
            'blindDecision':b['decision'],'blindCandidateTarget':b['candidateTarget'],'blindSelectedTarget':blind_target,
            'crossAuditDecision':decision,'crossAuditTarget':target,'retainedCurrentOnHold':current if decision=='hold' else None,
            'winner':winner,'rationale':rationale,'unresolvedQuestion':hold_reason,
            'sourcePlaceholders':sorted(source_placeholders.elements()),'currentPlaceholders':sorted(current_placeholders.elements()),
            'crossAuditPlaceholders':sorted(final_placeholders.elements()),'placeholderPass':placeholder_ok,
            'sourceMarkupTags':sorted(source_markup.elements()),'currentMarkupTags':sorted(current_markup.elements()),
            'crossAuditMarkupTags':sorted(final_markup.elements()),'markupPass':markup_ok,
            'sourceNumericTokens':source_numbers,'currentNumericTokens':current_numbers,'crossAuditNumericTokens':final_numbers,'numericPass':numeric_ok,
            'protectedLiteralsRequired':protected_required_p,'protectedLiteralChecks':protected_checks,
            'primaryCallerPinsMatchInput':True,'blindCallerPinsMatchInput':True,
        })

    assert caller_reference_total == 37
    assert len(audit_rows) == 240
    assert not candidate_protected_failures
    assert not integrity_failures
    assert final_counts['hold'] == 12

    # Seal audit output; the source packets and ledgers remain unchanged.
    write_jsonl(OUT/'cross-audit-ledger.jsonl', audit_rows)
    write_jsonl(OUT/'disagreements.jsonl', disagreements)
    source_audit = []
    for context in contexts:
        source_audit.append({
            'position':context['position'],'sourceKey':context['sourceKey'],'sourceKeySha256':context['sourceKeySha256'],
            'callerReferenceCount':context['callerReferenceCount'],
            'references':[{'path':ref['path'],'line':ref['line'],'role':ref['role'],'contextSha256':ref['contextSha256']} for ref in context['references']],
            'primaryAndBlindCallerReferencesVerified':True,
        })
    write_jsonl(OUT/'caller-reference-audit.jsonl',source_audit)
    verification = {
        'candidateFreeInputChecks':input_checks,'primaryPacketChecks':primary_checks,
        'blindPacketChecks':blind_checks,'blindEmbeddedInputChecks':blind_input_checks,
        'blindEmbeddedInputByteIdentical':True,'livePRAndRemotePins':live,
        'canonicalHead':HEAD,'canonicalTree':TREE,
        'candidateFreeManifestSha256':sha((INPUT/'manifest.json').read_bytes()),
        'candidateFreeChecksumListSha256':sha((INPUT/'SHA256SUMS.txt').read_bytes()),
        'primaryLedgerSha256':sha(PRIMARY_LEDGER.read_bytes()),'blindLedgerSha256':sha(BLIND_LEDGER.read_bytes()),
        'cellCount':len(input_rows),'sourceCount':len(contexts),'callerReferenceCount':caller_reference_total,
        'allCellPinsAgree':True,'allCallerPinsAgree':True,
    }
    write_json(OUT/'input-verification.json',verification)
    summary = {
        'artifact':'slskR PR #204 third-party localization cross-audit W1183-W1202',
        'repository':REPO,'pullRequest':204,'head':HEAD,'tree':TREE,
        'reviewedCells':len(audit_rows),'sourceCount':len(contexts),'localeCount':12,
        'callerReferenceCount':caller_reference_total,
        'primaryDispositionCounts':dict(primary_counts),'blindDecisionCounts':dict(blind_counts),
        'crossAuditDispositionCounts':dict(final_counts),
        'primaryBlindDisagreementCount':len(disagreements),
        'resolvedDisagreementCount':sum(row['resolution']=='adjudicated' for row in disagreements),
        'retainedHoldDisagreementCount':sum(row['resolution']=='retained-hold' for row in disagreements),
        'unresolvedSemanticHolds':[
            {'position':1198,'sourceKey':'Domain to front through (e.g., major CDN domains). Traffic appears to connect to this domain.',
             'cells':12,'question':'Product-approved translation for the domain-fronting setting and mechanism is unavailable.'}
        ],
        'protectedLiteralAudit':{
            'requiredLiterals':{'DisplayName':12,'ReplayGain':12,'CDN':12},
            'approvedCandidateViolations':len(candidate_protected_failures),
            'existingCurrentViolations':len(current_protected_failures),
            'currentViolationDetails':current_protected_failures,
        },
        'placeholderMarkupNumericFailures':len(integrity_failures),
        'position1198HindiCurrentCDNViolation':True,
        'allInputPrimaryBlindAndLivePinsVerified':True,
        'nativeSpeakerApproval':False,
        'limitations':'Machine-assisted semantic cross-audit. Qualified native-speaker review remains outstanding; the domain-fronting terminology is held across all locales.',
        'repositoryOrPREdited':False,
        'testsBuildsScansCIWorkflowsBrowserMergeReleaseOrTagPerformed':False,
    }
    write_json(OUT/'summary.json',summary)
    readme='''# slskR PR #204 third-party cross-audit — W1183–W1202

All candidate-free, primary, blind, and blind-embedded-input checksum manifests passed. Live PR #204, its branch, pull ref, and commit tree match head `8e60a51ec25967df115a3fd8c42872abbec58d8a` and tree `c2ec31432943730f0a8f3ee87687c46b6a4400c2`. The audit checks all 240 cells and all 37 pinned caller references.

The per-cell ledger reconciles every primary and blind target. Exact `DisplayName` and `ReplayGain` are preserved. The 12 cells for the domain-fronting security hint remain held until product-approved terminology is available; Hindi's current target also fails the required exact `CDN` literal check. Placeholder, markup, and numeric checks pass for all 240 retained/recommended targets.

The ledger and disagreement file record the exact primary/blind differences and their cross-audit outcome. Native-speaker approval remains outstanding. No repository or PR files were changed, and no tests, builds, scans, CI, workflows, browser work, merge, release, or tag were performed.
'''
    (OUT/'README.md').write_text(readme,encoding='utf-8')
    files=sorted(path for path in OUT.iterdir() if path.is_file() and path.name not in ('manifest.json','SHA256SUMS.txt'))
    manifest={
        'artifact':'slskR PR #204 W1183-W1202 third-party cross-audit','sealed':True,
        'repository':REPO,'pullRequest':204,'head':HEAD,'tree':TREE,
        'rowCount':len(audit_rows),'callerReferenceCount':caller_reference_total,
        'disagreementCount':len(disagreements),'decisionCounts':dict(final_counts),
        'files':[{'name':path.name,'bytes':path.stat().st_size,'sha256':sha(path.read_bytes())} for path in files],
    }
    write_json(OUT/'manifest.json',manifest)
    files=sorted(path for path in OUT.iterdir() if path.is_file() and path.name not in ('manifest.json','SHA256SUMS.txt'))
    (OUT/'SHA256SUMS.txt').write_text(''.join(f'{sha(path.read_bytes())}  {path.name}\n' for path in files),encoding='utf-8')
    print(json.dumps(summary,ensure_ascii=False,indent=2))

if __name__=='__main__':
    main()
