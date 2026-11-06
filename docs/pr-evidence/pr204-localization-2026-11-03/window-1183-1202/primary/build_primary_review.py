from __future__ import annotations

import collections
import hashlib
import json
import re
from pathlib import Path

ROOT = Path('/mnt/disks/scratch/task-scratch/slskr-pr204-w1183-1202-primary-20261103')
INPUT = Path('/mnt/disks/scratch/task-scratch/slskr-pr204-w1183-1202-input-20261103/clean-input')
OUT = ROOT / 'primary-review'


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def write_json(path: Path, value) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + '\n', encoding='utf-8')


def read_jsonl(path: Path):
    return [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines() if line]


PROTECTED = {
    1188: ['DisplayName'],
    1193: ['ReplayGain'],
    1198: ['CDN'],
}

# (source position, locale): (exact candidate, proposal class, rationale, confidence)
PROPOSALS = {
    (1183, 'fr'): ('Nombre de jours avant expiration de l’étagère Discovery', 'refinement', 'This is a numeric `expiryDays` field. The current plural phrasing is awkward; the proposal states that the value is the number of days before the Discovery shelf expires.', 'moderate'),
    (1183, 'ko'): ('디스커버리 선반 만료 일수', 'correction', 'The caller binds this label to a numeric days value. The current wording says “search shelf expiry date”; this preserves Discovery and expresses an expiry-day count.', 'moderate'),
    (1183, 'vi'): ('Số ngày đến khi kệ Discovery hết hạn', 'correction', 'The caller binds this label to a numeric days value. The current translation says an expiry day/date, rather than the number of days until expiry.', 'moderate'),

    (1184, 'es'): ('Cerrar', 'correction', 'Both callers clear an error or success message when this button is clicked. “Despedir” suggests dismissing a person; “Cerrar” matches the close action.', 'high'),
    (1184, 'zh-Hans'): ('关闭', 'correction', 'Both callers clear an error or success message when this button is clicked. “解雇” means firing someone; “关闭” matches the close action.', 'high'),
    (1184, 'hi'): ('बंद करें', 'correction', 'The callers clear the displayed error or success message. The current wording means reject/refuse; this is the close action.', 'moderate'),
    (1184, 'de'): ('Schließen', 'correction', 'The callers clear the displayed error or success message. “Zurückweisen” means reject; “Schließen” matches the close action.', 'high'),
    (1184, 'ja'): ('閉じる', 'correction', 'The callers clear the displayed error or success message. “却下する” means reject a proposal; “閉じる” matches the close action.', 'high'),
    (1184, 'fr'): ('Fermer', 'correction', 'The callers clear the displayed error or success message. “Rejeter” means reject; “Fermer” matches the close action.', 'high'),
    (1184, 'pt-BR'): ('Fechar', 'correction', 'The callers clear the displayed error or success message. “Liberar” means release/free; “Fechar” matches the close action.', 'high'),
    (1184, 'ar'): ('إغلاق', 'correction', 'The callers clear the displayed error or success message. “رفض” means rejection; “إغلاق” matches the close action.', 'moderate'),
    (1184, 'ko'): ('닫기', 'correction', 'The callers clear the displayed error or success message. “해고하다” means fire someone; “닫기” matches the close action.', 'high'),
    (1184, 'zh-Hant'): ('關閉', 'correction', 'The callers clear the displayed error or success message. “解僱” means firing someone; “關閉” matches the close action.', 'high'),
    (1184, 'vi'): ('Đóng', 'correction', 'The callers clear the displayed error or success message. “Miễn nhiệm” means removing someone from an office; “Đóng” matches the close action.', 'moderate'),
    (1184, 'id'): ('Tutup', 'correction', 'The callers clear the displayed error or success message. “Membubarkan” means disband/dissolve; “Tutup” matches the close action.', 'moderate'),

    (1189, 'vi'): ('Các bồi thẩm viên bất đồng quan điểm', 'correction', 'The caller uses this as the heading for a joined list of `dissentingJurors`. The current wording names a dissenting jury panel, rather than the dissenting jurors.', 'moderate'),
    (1190, 'ar'): ('المستخدمون الفريدون', 'correction', 'This is a count heading for distinct users. “المتميزون” can read as distinguished users; “الفريدون” expresses unique users.', 'moderate'),

    (1191, 'es'): ('Pares únicos', 'correction', 'The caller is a transfer-compatibility statistic built from distinct-user counts. “Compañeros” suggests companions/colleagues; “pares” preserves the network-peer sense.', 'moderate'),
    (1191, 'de'): ('Eindeutige Peers', 'correction', 'The caller is a transfer-compatibility statistic built from distinct-user counts. “Kollegen” means colleagues; the technical loan “Peers” preserves the network-peer sense.', 'moderate'),
    (1191, 'hi'): ('विशिष्ट पीयर', 'correction', 'The caller is a transfer-compatibility statistic built from distinct-user counts. “सहकर्मी” means colleague; the technical term “पीयर” preserves the network-peer sense.', 'low'),
    (1191, 'ar'): ('أقران فريدون', 'correction', 'The caller is a transfer-compatibility statistic built from distinct-user counts. The current phrase can read as “their distinguished peers”; this says unique peers.', 'moderate'),
    (1191, 'ko'): ('서로 다른 피어', 'correction', 'The caller is a transfer-compatibility statistic built from distinct-user counts. “동료” means colleague; “피어” preserves the network-peer sense.', 'moderate'),
    (1191, 'zh-Hans'): ('不同的对等方', 'refinement', 'The caller is a transfer-compatibility statistic built from distinct-user counts. “同行” can read as professional colleagues; “对等方” identifies peers in the network context.', 'moderate'),
    (1191, 'zh-Hant'): ('不同的對等方', 'refinement', 'The caller is a transfer-compatibility statistic built from distinct-user counts. “同行” can read as professional colleagues; “對等方” identifies peers in the network context.', 'moderate'),
    (1191, 'id'): ('Peer yang unik', 'correction', 'The caller is a transfer-compatibility statistic built from distinct-user counts. “Rekan” suggests colleagues/associates; “peer” retains the network term.', 'moderate'),

    (1194, 'ar'): ('المجال', 'correction', 'The callers use this for content domains such as audio, video, and image. “اختصاص” suggests a specialty; “المجال” expresses the domain/category.', 'moderate'),
    (1194, 'vi'): ('Lĩnh vực', 'correction', 'The callers use this for content domains such as audio, video, and image. “Lãnh địa” means territory; “Lĩnh vực” expresses a domain or field.', 'moderate'),

    (1195, 'zh-Hans'): ('领域搜索', 'correction', 'The caller’s card describes finding ContentIDs by domains such as audio, video, and image. “域名搜索” implies DNS/domain-name search; “领域搜索” fits content domains.', 'moderate'),
    (1195, 'zh-Hant'): ('領域搜尋', 'correction', 'The caller’s card describes finding ContentIDs by domains such as audio, video, and image. “域名搜尋” implies DNS/domain-name search; “領域搜尋” fits content domains.', 'moderate'),
    (1195, 'vi'): ('Tìm kiếm theo lĩnh vực', 'correction', 'The caller’s card searches content domains such as audio, video, and image. “Tên miền” means an Internet domain name; this expresses search by content field/domain.', 'moderate'),

    (1199, 'ar'): ('المجال:', 'correction', 'The caller displays this label before a runtime content-domain value. The current “اختصاص” suggests a specialty; “المجال” fits the audio/video/image category context.', 'moderate'),
    (1199, 'vi'): ('Lĩnh vực:', 'correction', 'The caller displays this label before an opaque runtime content-domain value. “Lãnh địa” means territory; “Lĩnh vực” fits the content field/domain.', 'moderate'),

    (1200, 'zh-Hans'): ('领域', 'correction', 'The caller labels a count of MediaCore content domains, whose examples are audio, video, and image. “域名” implies DNS names; “领域” fits these categories.', 'moderate'),
    (1200, 'zh-Hant'): ('領域', 'correction', 'The caller labels a count of MediaCore content domains, whose examples are audio, video, and image. “網域” implies network domains; “領域” fits these categories.', 'moderate'),
    (1200, 'vi'): ('Lĩnh vực', 'correction', 'The caller labels a count of MediaCore content domains, whose examples are audio, video, and image. “Tên miền” implies DNS names; “Lĩnh vực” fits these categories.', 'moderate'),

    (1201, 'zh-Hans'): ('领域：', 'correction', 'The caller labels the total count of MediaCore content domains, whose examples are audio, video, and image. “域名” implies DNS names; “领域” fits these categories.', 'moderate'),
    (1201, 'zh-Hant'): ('領域：', 'correction', 'The caller labels the total count of MediaCore content domains, whose examples are audio, video, and image. “域名” implies DNS names; “領域” fits these categories.', 'moderate'),
    (1201, 'vi'): ('Lĩnh vực:', 'correction', 'The caller labels the total count of MediaCore content domains, whose examples are audio, video, and image. “Tên miền” implies DNS names; “Lĩnh vực” fits these categories.', 'moderate'),

    (1202, 'ja'): ('完了', 'refinement', 'All five callers use this as a button that closes or finishes a modal, not as a label for an ending. “完了” is the conventional concise UI action.', 'moderate'),
}

HOLD_KEYS = {(1188, locale) for locale in ['es', 'zh-Hans', 'hi', 'de', 'ja', 'fr', 'pt-BR', 'ar', 'ko', 'zh-Hant', 'vi', 'id']}
HOLD_KEYS |= {(1197, locale) for locale in ['es', 'zh-Hans', 'hi', 'de', 'ja', 'pt-BR', 'ar', 'ko', 'zh-Hant', 'vi', 'id']}
HOLD_KEYS |= {(1198, locale) for locale in ['es', 'hi', 'de', 'ja', 'fr', 'pt-BR', 'ar', 'ko', 'vi', 'id']}
HOLD_KEYS.add((1191, 'vi'))

HOLD_RATIONALES = {
    1188: 'The server callers return only `DisplayName is required.` The targets append an API-field parenthetical naming `displayName`; although the packet contains a `publishedPod.displayName` response property elsewhere, it does not establish that this added note belongs in the localized validation error or names the input field. Preserve the exact `DisplayName` literal and hold the added wording until its error-message contract is confirmed.',
    1191: 'The caller shows this as a transfer-compatibility statistic whose value is computed from `distinctUsers`. The current Vietnamese says colleagues; the packet does not establish the product’s preferred Vietnamese term for network peers. Hold rather than choose an unverified term.',
    1197: 'The server caller checks an empty `/domain/` path segment and returns only `Domain is required`. Most targets append an “API fields: domain” note; the packet does not establish that this extra explanatory phrase belongs in the localized error or that a path parameter should be described as a field. Hold the added wording. The French cell has no appended note and remains reviewable.',
    1198: 'This is a security setting for a domain to front through; the hint says traffic appears to connect to the selected domain and gives CDN examples. The current phrasings include literal front-through constructions or wording about transmitting/advancing that does not establish a reliable locale-specific term for domain fronting. Hold these cells rather than invent technical terminology. The Hindi cell also renders `CDN` in Devanagari rather than preserving the acronym.',
}

CONTEXT_RATIONALE = {
    1183: 'The exact caller binds this label to the numeric `expiryDays` input.',
    1184: 'The exact callers clear an error or success message on click.',
    1185: 'The exact caller uses this as the title/accessible label of the port-migration reminder close button.',
    1186: 'The exact caller uses this as the popup explanation for dismissing the port-migration reminder until forwarded ports change.',
    1187: 'The exact caller places this label before the published pod display-name value.',
    1188: 'The exact server callers return this validation error and the client allowlist routes it through translated error handling.',
    1189: 'The exact caller uses this as the heading for a joined list of dissenting jurors.',
    1190: 'The exact callers use this as a table heading for distinct-user counts.',
    1191: 'The exact caller uses this as a transfer-compatibility statistic label; its value comes from distinct-user counters.',
    1192: 'The exact source value is a playlist cover-art policy option; the UI passes its text through `interfaceText(option.text)` while keeping the option value separate.',
    1193: 'The exact source value is a ReplayGain policy option; the UI passes its text through `interfaceText(option.text)` while keeping the option value separate.',
    1194: 'The exact callers use this for content domains such as audio, video, and image.',
    1195: 'The exact caller labels a search panel that finds ContentIDs by content domain and optional type.',
    1196: 'The exact caller uses this as a federation status row with a boolean Yes/No value.',
    1197: 'The exact server caller rejects an empty `domain` path segment and the client allowlist routes the error through translated handling.',
    1198: 'The exact caller uses this as help text for a security setting; the wording refers to a domain that traffic appears to connect to.',
    1199: 'The exact callers place this label before opaque `queryResult.domain` or `validatedContent.domain` values.',
    1200: 'The exact caller labels a count of MediaCore content domains.',
    1201: 'The exact caller labels a total count of MediaCore content domains.',
    1202: 'All five exact callers use this as the button action for closing or finishing a modal.',
}


def literal_checks(required, text):
    return [{'literal': literal, 'presentExactly': literal in text} for literal in required]


input_sum_bytes = (INPUT / 'SHA256SUMS.txt').read_bytes()
input_sum_text = input_sum_bytes.decode('utf-8')
input_hashes = {}
for line in input_sum_text.splitlines():
    digest, name = line.split('  ', 1)
    input_hashes[name] = digest
for name, digest in input_hashes.items():
    assert sha((INPUT / name).read_bytes()) == digest, name
input_manifest = json.loads((INPUT / 'manifest.json').read_text(encoding='utf-8'))
cells = read_jsonl(INPUT / 'current-target-cells.jsonl')
contexts = {row['position']: row for row in read_jsonl(INPUT / 'source-contexts.jsonl')}
assert len(cells) == 240 and len(contexts) == 20
assert sum(row['callerReferenceCount'] for row in contexts.values()) == 37
assert input_manifest['head'] == '8e60a51ec25967df115a3fd8c42872abbec58d8a'
assert input_manifest['tree'] == 'c2ec31432943730f0a8f3ee87687c46b6a4400c2'

rows = []
for cell in cells:
    position = cell['position']
    locale = cell['locale']
    key = (position, locale)
    source = cell['sourceKey']
    current = cell['currentTarget']
    expected_placeholders = re.findall(r'\{[A-Za-z][A-Za-z0-9_]*\}', source)
    current_placeholders = re.findall(r'\{[A-Za-z][A-Za-z0-9_]*\}', current)
    required_literals = PROTECTED.get(position, [])

    if key in HOLD_KEYS:
        disposition = 'hold'
        proposal = None
        proposal_type = None
        rationale = HOLD_RATIONALES[position]
        confidence = 'low' if position in {1188, 1197} else 'moderate'
    elif key in PROPOSALS:
        proposal, proposal_type, rationale, confidence = PROPOSALS[key]
        disposition = 'correction/refinement proposal'
    else:
        disposition = 'accept-current'
        proposal = None
        proposal_type = None
        rationale = CONTEXT_RATIONALE[position] + ' The current wording preserves the source meaning and any protected literal; I found no clear semantic defect.'
        confidence = 'low' if locale in {'ar', 'hi', 'id', 'ko', 'vi', 'zh-Hans', 'zh-Hant'} else 'moderate'

    review_target = proposal if proposal is not None else current
    review_placeholders = re.findall(r'\{[A-Za-z][A-Za-z0-9_]*\}', review_target)
    proposal_required_literals = literal_checks(required_literals, review_target)
    context_refs = contexts[position]['references']
    hold_evidence = None
    if disposition == 'hold':
        hold_evidence = {
            'sourceCallerReferences': [{'path': ref['path'], 'line': ref['line'], 'role': ref['role']} for ref in context_refs],
            'unresolvedQuestion': {
                1188: 'whether the added API-field note is part of the intended localized validation error',
                1191: 'which Vietnamese term is preferred for a network peer in this statistic',
                1197: 'whether the added API-field note belongs in the error and how to describe a route path parameter',
                1198: 'which locale-specific term is approved for domain fronting',
            }[position],
        }
    rows.append({
        'schemaVersion': 1,
        'repository': 'snapetech-org/slskR',
        'pullRequest': 204,
        'window': 'W1183-W1202',
        'head': cell['head'],
        'tree': cell['tree'],
        'position': position,
        'sourceKey': source,
        'sourceKeySha256': cell['sourceKeySha256'],
        'locale': locale,
        'currentTarget': current,
        'currentTargetSha256': cell['currentTargetSha256'],
        'disposition': disposition,
        'proposalType': proposal_type,
        'proposedTarget': proposal,
        'proposedTargetSha256': sha(proposal.encode('utf-8')) if proposal is not None else None,
        'rationale': rationale,
        'confidence': confidence,
        'callerContextPins': [{'path': ref['path'], 'line': ref['line'], 'role': ref['role'], 'contextSha256': ref['contextSha256']} for ref in context_refs],
        'callerContextReviewed': True,
        'opaqueCallerExpressionsPreservedVerbatim': True,
        'placeholderChecks': {
            'sourceTokens': expected_placeholders,
            'currentTargetTokens': current_placeholders,
            'currentTargetMatchesSource': collections.Counter(expected_placeholders) == collections.Counter(current_placeholders),
            'reviewTargetTokens': review_placeholders,
            'reviewTargetMatchesSource': collections.Counter(expected_placeholders) == collections.Counter(review_placeholders),
        },
        'protectedLiteralsRequired': required_literals,
        'currentTargetProtectedLiteralChecks': literal_checks(required_literals, current),
        'reviewTargetProtectedLiteralChecks': proposal_required_literals,
        'holdEvidence': hold_evidence,
    })

assert len(rows) == 240
assert len({(row['sourceKey'], row['locale']) for row in rows}) == 240
assert set((row['position'], row['locale']) for row in rows if row['disposition'] == 'correction/refinement proposal') == set(PROPOSALS)
assert set((row['position'], row['locale']) for row in rows if row['disposition'] == 'hold') == HOLD_KEYS
assert all(row['placeholderChecks']['currentTargetMatchesSource'] for row in rows)
assert all(row['placeholderChecks']['reviewTargetMatchesSource'] for row in rows)
assert all(all(check['presentExactly'] for check in row['reviewTargetProtectedLiteralChecks']) for row in rows if row['proposedTarget'] is not None)

counts = collections.Counter(row['disposition'] for row in rows)
proposal_classes = collections.Counter(row['proposalType'] for row in rows if row['proposalType'])
proposal_rows = [{k: row[k] for k in ['position', 'sourceKey', 'locale', 'currentTarget', 'proposedTarget', 'proposalType', 'rationale', 'confidence']} for row in rows if row['proposedTarget'] is not None]
hold_rows = [{k: row[k] for k in ['position', 'sourceKey', 'locale', 'currentTarget', 'rationale', 'confidence', 'holdEvidence']} for row in rows if row['disposition'] == 'hold']

summary = {
    'schemaVersion': 1,
    'reviewType': 'primary semantic review',
    'repository': 'snapetech-org/slskR',
    'pullRequest': 204,
    'window': 'W1183-W1202',
    'head': input_manifest['head'],
    'tree': input_manifest['tree'],
    'inputPacket': str(INPUT),
    'inputChecksumListSha256': sha(input_sum_bytes),
    'inputFiles': input_hashes,
    'sourceCount': 20,
    'localeCount': 12,
    'cellCount': len(rows),
    'callerReferenceCount': input_manifest['callerReferenceCount'],
    'callerFileCount': input_manifest['callerFileCount'],
    'placeholderMismatchCount': 0,
    'protectedLiteralChecks': sum(len(row['protectedLiteralsRequired']) for row in rows),
    'protectedLiteralMismatchCount': sum(1 for row in rows for check in row['reviewTargetProtectedLiteralChecks'] if not check['presentExactly']),
    'dispositionCounts': dict(counts),
    'proposalClassCounts': dict(proposal_classes),
    'proposalCount': len(proposal_rows),
    'proposals': proposal_rows,
    'holdCount': len(hold_rows),
    'holds': hold_rows,
    'nativeSpeakerApproval': False,
    'limitations': [
        'Machine review is not native-speaker approval.',
        'Position 1188 is held because the targets append an API-field note whose relationship to the validation error is not established by the pinned callers.',
        'Position 1197 is held for locales with an added API-field note because the exact caller is a route path parameter and the packet does not establish that extra wording as part of the localized error.',
        'Position 1198 is held in ten locales because the packet does not establish a reliable localized term for the specialized domain-fronting setting; Simplified and Traditional Chinese “前置域” are accepted as direct equivalents.',
        'Vietnamese position 1191 is held because the packet does not establish the product’s preferred term for network peers.',
    ],
}

OUT.mkdir(parents=True, exist_ok=True)
(OUT / 'primary-decisions.jsonl').write_text(''.join(json.dumps(row, ensure_ascii=False, sort_keys=True) + '\n' for row in rows), encoding='utf-8')
write_json(OUT / 'summary.json', summary)
readme = f'''# slskR PR #204 W1183–W1202 primary semantic review\n\nThis ledger covers all {len(rows)} current translation cells across 20 source keys and 12 locales, pinned to head `{summary['head']}` and tree `{summary['tree']}`. It uses only the checksummed candidate-free packet at `{INPUT}`; that packet’s checksum-list SHA-256 is `{summary['inputChecksumListSha256']}`.\n\nEach decision records the exact current value, disposition, rationale, confidence, caller-context hashes, placeholder checks, and protected-literal checks. Caller expressions remain opaque and unchanged. Holds preserve uncertainty where API-field notes or specialized terminology cannot be supported by the pinned context.\n\nThis is machine review, not native-speaker approval. No repository or PR files were changed, and no tests, builds, scans, or CI were run.\n'''
(OUT / 'README.md').write_text(readme, encoding='utf-8')
checks = []
for path in sorted(OUT.iterdir()):
    if path.is_file() and path.name != 'SHA256SUMS.txt':
        checks.append(f'{sha(path.read_bytes())}  {path.name}')
(OUT / 'SHA256SUMS.txt').write_text('\n'.join(checks) + '\n', encoding='utf-8')
print(json.dumps({
    'head': summary['head'],
    'tree': summary['tree'],
    'cells': len(rows),
    'dispositions': dict(counts),
    'proposalClasses': dict(proposal_classes),
    'protectedLiteralMismatchCount': summary['protectedLiteralMismatchCount'],
    'output': str(OUT),
}, ensure_ascii=False, indent=2))
