import collections, hashlib, json, pathlib, re, subprocess

root = pathlib.Path('/mnt/disks/scratch/task-scratch/slskr-pr204-W1103-1122-primary-20261103')
base = root / 'clean-input'
out = root / 'primary-private'
out.mkdir(parents=True, exist_ok=True)
subprocess.check_call(['sha256sum', '-c', 'SHA256SUMS.txt'], cwd=base, stdout=subprocess.DEVNULL)
manifest = json.loads((base / 'manifest.json').read_text(encoding='utf-8'))
assert manifest['head'] == 'e45e6967625c5e804b688b9cb03d359ea59d000b'
assert manifest['tree'] == 'c5164178f16e0fa2f59586c9ab3685e1ac08dfa5'
assert manifest['window'] == 'W1103-W1122'
assert manifest['selectedPositions'] == [1103, 1122]
rows = [json.loads(line) for line in (base / 'current-target-cells.jsonl').read_text(encoding='utf-8').splitlines()]
context_rows = [json.loads(line) for line in (base / 'source-contexts.jsonl').read_text(encoding='utf-8').splitlines()]
contexts = {row['sourceId']: row for row in context_rows}
assert len(rows) == 240 and len(contexts) == 20
sha = lambda text: hashlib.sha256(text.encode('utf-8')).hexdigest()

# Candidate values are reviewed against the exact source, current target, and pinned caller context.
manual = {
    (1103, 'fr'): 'Décroissant',
    (1104, 'vi'): 'Mô tả',
    (1105, 'hi'): 'डिस्क्रिप्टर',
    (1105, 'vi'): 'Bộ mô tả',
    (1108, 'vi'): 'Truy xuất bộ mô tả',
    (1109, 'hi'): 'डिस्क्रिप्टर प्राप्त हुआ',
    (1109, 'ja'): '記述子を取得しました',
    (1109, 'ko'): '설명자를 가져왔습니다',
    (1109, 'zh-Hans'): '已获取描述符',
    (1109, 'zh-Hant'): '已取得描述符',
    (1109, 'id'): 'Deskriptor berhasil diambil',
    (1110, 'ar'): 'التحقق من الواصف',
    (1110, 'vi'): 'Xác minh bộ mô tả',
    (1117, 'es'): 'Las métricas detalladas de rendimiento y contribución de los pares requieren datos de seguimiento. Es posible que estos datos no estén disponibles para todas las descargas en la red de pares.',
    (1117, 'zh-Hans'): '详细的对等节点贡献和性能指标需要追踪数据。这些数据可能并非所有点对点下载都能提供。',
    (1117, 'hi'): 'विस्तृत पीयर योगदान और प्रदर्शन मेट्रिक्स के लिए ट्रेस डेटा आवश्यक है। सभी पीयर-टू-पीयर डाउनलोड के लिए यह डेटा उपलब्ध हो, यह ज़रूरी नहीं है।',
    (1117, 'ar'): 'تتطلب مساهمة الأقران التفصيلية ومقاييس الأداء بيانات التتبع. وقد لا تتوفر هذه البيانات لجميع التنزيلات عبر شبكات النظير إلى النظير.',
    (1117, 'ko'): '자세한 피어 기여 및 성능 지표에는 추적 데이터가 필요합니다. 이 데이터는 모든 스웜 다운로드에서 제공되지 않을 수 있습니다.',
    (1117, 'zh-Hant'): '詳細的對等節點貢獻和效能指標需要追蹤資料。這些資料可能並非所有點對點下載都能提供。',
    (1117, 'vi'): 'Các số liệu chi tiết về đóng góp của các nút ngang hàng và hiệu suất cần dữ liệu truy vết. Dữ liệu này có thể không có sẵn trong mọi lượt tải qua mạng ngang hàng.',
    (1117, 'id'): 'Kontribusi peer dan metrik kinerja yang terperinci memerlukan data trace. Data ini mungkin tidak tersedia untuk semua unduhan peer-to-peer.',
    (1118, 'zh-Hans'): '详情',
    (1118, 'zh-Hant'): '詳情',
    (1118, 'ko'): '세부 정보',
    (1119, 'ar'): 'اكتشاف مشكلات الجودة وعمليات تحويل الترميز والمسارات المفقودة',
    (1121, 'fr'): 'Pack de diagnostic',
    (1122, 'fr'): 'Pack de diagnostic copié',
}
annotation_positions = {1106, 1111, 1112, 1114, 1115}
annotation_re = re.compile(r'\s*\([^()]*API[^()]*\)$', re.IGNORECASE)
change_types = {
    (1103, 'fr'): 'correction',
    (1104, 'vi'): 'refinement',
    (1105, 'hi'): 'correction', (1105, 'vi'): 'correction',
    (1108, 'vi'): 'refinement',
    (1109, 'hi'): 'correction', (1109, 'ja'): 'refinement', (1109, 'ko'): 'correction',
    (1109, 'zh-Hans'): 'correction', (1109, 'zh-Hant'): 'correction', (1109, 'id'): 'correction',
    (1110, 'ar'): 'correction', (1110, 'vi'): 'correction',
    (1117, 'es'): 'refinement', (1117, 'zh-Hans'): 'correction', (1117, 'hi'): 'correction',
    (1117, 'ar'): 'refinement', (1117, 'ko'): 'correction', (1117, 'zh-Hant'): 'correction',
    (1117, 'vi'): 'correction', (1117, 'id'): 'correction',
    (1118, 'zh-Hans'): 'refinement', (1118, 'zh-Hant'): 'refinement', (1118, 'ko'): 'refinement',
    (1119, 'ar'): 'correction', (1121, 'fr'): 'refinement', (1122, 'fr'): 'refinement',
}
reason_by_position = {
    1103: 'The caller renders this in a sort-order control; French descendant means a person or thing descending from another, not descending sort order. Use the established sort-direction adjective.',
    1104: 'This is the name of an optional text field. Vietnamese Sự miêu tả is an awkward nominal phrase; Mô tả is the concise standard field label.',
    1105: 'Descriptor is a technical metadata object in the forensic matrix and Content Descriptor workflow. Hindi वर्णनकर्ता means a person who describes, and Vietnamese Mô tả collapses Descriptor into the separate Description field; use consistent technical terms.',
    1106: 'The source already preserves the exact ContentID token. The localized target appends an API-field list that is absent from the source and appears on the user-facing error path; retain only the source message.',
    1108: 'This labels descriptor retrieval statistics. Vietnamese Mô tả means description and does not identify the descriptor object; keep it distinct from the Description field.',
    1109: 'This is a success-message heading. The revised targets express successful retrieval; current Hindi is an incomplete participle, Japanese is an awkward passive label, Korean and Chinese suggest search, and Indonesian says accessed rather than retrieved.',
    1110: 'Descriptor Verification is the check of a technical descriptor object. Arabic الوصف means description, and Vietnamese Mô tả loses the distinction from Descriptor; use the same descriptor terms as adjacent labels.',
    1111: 'The localized target adds an API-field note absent from the source error. Remove that extra content from user-facing error copy.',
    1112: 'This error message is localized from the exact backend validation string. The appended destinationHost API-field note is absent from the source and unnecessary in the displayed message.',
    1113: 'Current values retain the product term Pod and correctly express the private-gateway policy; keep them.',
    1114: 'The source describes the destination path constraint. The appended destination API-field note is absent from the source; remove it while preserving the relative-path and download-root requirements.',
    1115: 'The source already gives the inclusive port bounds. The appended destinationPort API-field note is absent from the source; remove it while preserving both exact numeric limits.',
    1116: 'Detailed is the value label paired with Compact in the experience-density selector; current values express the intended display option.',
    1117: 'This is explanatory text for a peer-to-peer swarm visualization. Peer and swarm refer to network peers/downloads, not colleagues, animal herds, or generic groups; make those technical meanings clear and preserve the trace-data availability limitation.',
    1118: 'This is a table column heading. Use the conventional concise details label in Chinese and a complete “detailed information” phrase in Korean.',
    1119: 'This is the library health scanner subtitle. Arabic الرموز المحولة means converted codes and misrenders transcoding; use a phrase for transcoding operations.',
    1120: 'Detected is a status value in library-health issue records and filters. Current values preserve the detected state; retain them.',
    1121: 'This label names the diagnostics/support artifact across menu, modal, and command surfaces. French Offre groupée is an awkward calque for a software bundle; Pack de diagnostic is concise product language.',
    1122: 'This is a success toast after the diagnostic artifact is copied. Keep the same French term as the Diagnostic Bundle label.',
}

records = []
for row in rows:
    position, locale = row['position'], row['locale']
    source, current = row['source'], row['currentTarget']
    candidate = manual.get((position, locale), current)
    annotation_removed = False
    if position in annotation_positions and (position, locale) not in manual:
        candidate, count = annotation_re.subn('', current)
        annotation_removed = bool(count)
    if (position, locale) in manual:
        disposition = change_types[(position, locale)] if candidate != current else 'accept-current'
    elif annotation_removed:
        disposition = 'correction'
    else:
        disposition = 'accept-current'
    if candidate == current:
        disposition = 'accept-current'
        rationale = 'The current translation preserves the source meaning in the pinned production context; retain it.'
    elif annotation_removed:
        rationale = reason_by_position[position]
    else:
        rationale = reason_by_position[position]
    context = contexts[row['sourceId']]['references']
    context_raw = json.dumps(context, ensure_ascii=False, sort_keys=True, separators=(',', ':'))
    record = {
        'sourcePosition': position,
        'sourceId': row['sourceId'],
        'source': source,
        'locale': locale,
        'catalogPath': f'web/src/lib/locales/ui-labels.{locale}.json',
        'catalogFileSha256': manifest['catalogPins'][f'web/src/lib/locales/ui-labels.{locale}.json']['sha256'],
        'catalogGitBlob': manifest['catalogPins'][f'web/src/lib/locales/ui-labels.{locale}.json']['gitBlob'],
        'sourceSha256': row['sourceSha256'],
        'currentTarget': current,
        'currentTargetSha256': row['currentTargetSha256'],
        'candidateTarget': candidate,
        'candidateTargetSha256': sha(candidate),
        'disposition': disposition,
        'confidence': 'moderate',
        'rationale': rationale,
        'callerContextSha256': sha(context_raw),
        'callerCount': len(context),
        'callerRefs': [{'path': x['path'], 'line': x['line'], 'lineText': x['lineText'], 'fileSha256': x['fileSha256'], 'gitBlob': x['gitBlob']} for x in context],
        'sourcePlaceholders': row['placeholders'],
        'candidatePlaceholders': re.findall(r'\{([A-Za-z][A-Za-z0-9_]*)\}', candidate),
        'sourceNumericTokens': re.findall(r'\d+(?:[,.]\d+)*', source),
        'candidateNumericTokens': re.findall(r'\d+(?:[,.]\d+)*', candidate),
        'nativeSpeakerReview': False,
    }
    records.append(record)

assert len(records) == 240
assert len({(r['sourceId'], r['locale']) for r in records}) == 240
for r in records:
    assert r['sourceSha256'] == sha(r['source'])
    assert r['currentTargetSha256'] == sha(r['currentTarget'])
    assert r['candidateTargetSha256'] == sha(r['candidateTarget'])
    assert r['candidatePlaceholders'] == r['sourcePlaceholders']
    if r['candidateNumericTokens'] != r['sourceNumericTokens']:
        raise SystemExit(f"numeric token mismatch: pos={r['sourcePosition']} locale={r['locale']} source={r['source']!r} candidate={r['candidateTarget']!r} sourceTokens={r['sourceNumericTokens']} candidateTokens={r['candidateNumericTokens']}")
    for protected in ('Lidarr', 'ContentID', 'JSON', 'Pod', 'Demucs'):
        if protected in r['source']:
            assert protected in r['candidateTarget'], (r['sourcePosition'], r['locale'], protected)

counts = collections.Counter(r['disposition'] for r in records)
changes = [r for r in records if r['candidateTarget'] != r['currentTarget']]
by_locale = collections.Counter(r['locale'] for r in changes)
by_position = collections.Counter(str(r['sourcePosition']) for r in changes)
(out / 'review-decisions.jsonl').write_text(''.join(json.dumps(r, ensure_ascii=False, sort_keys=True) + '\n' for r in records), encoding='utf-8')
summary = {
    'repository': 'snapetech-org/slskr',
    'pullRequest': 204,
    'window': 'W1103-W1122',
    'inputHead': manifest['head'],
    'inputTree': manifest['tree'],
    'cleanInputManifestSha256': hashlib.sha256((base / 'manifest.json').read_bytes()).hexdigest(),
    'cleanInputChecksumListSha256': hashlib.sha256((base / 'SHA256SUMS.txt').read_bytes()).hexdigest(),
    'sourceIdOrderSha256': manifest['sourceIdOrderSha256'],
    'windowSourceSha256': manifest['windowSourceSha256'],
    'sourceCount': 20,
    'localeCount': 12,
    'cellCount': 240,
    'callerReferences': manifest['callerReferences'],
    'callerlessSourceIds': manifest['callerSourcesWithNoPinnedProductionStringReference'],
    'dispositions': dict(counts),
    'proposedChanges': len(changes),
    'changesByLocale': dict(sorted(by_locale.items())),
    'changesByPosition': dict(sorted(by_position.items(), key=lambda x: int(x[0]))),
    'sourceHashMismatches': 0,
    'currentTargetHashMismatches': 0,
    'candidateHashMismatches': 0,
    'placeholderMismatches': 0,
    'numericTokenMismatches': 0,
    'protectedLiteralMismatches': 0,
    'confidence': 'moderate',
    'nativeSpeakerReview': False,
    'independentCrossReview': False,
    'catalogsOrRepositoryChanged': False,
    'testsBuildsScansCIOrWorkflowChanges': False,
}
(out / 'summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
(out / 'README.md').write_text(f'''# Private primary semantic review — slskR PR #204 W1103-W1122

Exact clean-input pins: head {manifest['head']}, tree {manifest['tree']}, input-manifest SHA-256 {summary['cleanInputManifestSha256']}. This review covers 20 sequential source positions across 12 direct locales, 240 cells, and {manifest['callerReferences']} pinned production references. The review uses only the checksummed clean-input packet; it does not inspect or modify repository/PR content.

Dispositions: {dict(counts)}; {len(changes)} proposed target refinements/corrections. All reviewed source/current/candidate hashes, placeholder sets, numeric tokens, and protected product literals match. No catalog cells were applied. Caller context exists for every selected source ID; there are no no-caller holds in this window. This is a machine-assisted primary review, not qualified native-speaker approval or independent cross-review. Keep this packet private until the separate strict-blind review has been sealed. No tests, builds, scans, CI, workflow edits, or PR changes were made.
''', encoding='utf-8')
files = sorted(p for p in out.iterdir() if p.is_file() and p.name != 'SHA256SUMS.txt')
(out / 'SHA256SUMS.txt').write_text(''.join(f'{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.name}\n' for p in files), encoding='utf-8')
subprocess.check_call(['sha256sum', '-c', 'SHA256SUMS.txt'], cwd=out, stdout=subprocess.DEVNULL)
print(json.dumps({**summary, 'primaryLedgerSha256': hashlib.sha256((out/'review-decisions.jsonl').read_bytes()).hexdigest(), 'primaryChecksumListSha256': hashlib.sha256((out/'SHA256SUMS.txt').read_bytes()).hexdigest(), 'primaryPacketPath': str(out)}, ensure_ascii=False, indent=2))
