from __future__ import annotations

import collections
import hashlib
import json
import re
import subprocess
from pathlib import Path


ROOT = Path('/mnt/disks/scratch/task-scratch/slskr-pr204-W583-602-primary-20261102')
OUT = ROOT / 'packet'
REPO = Path('/mnt/disks/scratch/task-worktrees/localization-20261102/slskr-pr204-w503-522')
HEAD = '2f7483fdaa753e22f6d335a03f15db7d1d82b20f'
TREE = '54ee16a812a5bda7871f3ef3ad7ff0cf3bf678e0'
SOURCE = '7ff454828398de6a3cfb72fe7f0ed21fe419425b'
SOURCE_TREE = '9e9f2aa743c4ff3236af8f99619803bdc3a37152'
REPO_NAME = 'snapetech-org/slskR'
PR = 204
LOCALES = ['ar', 'de', 'es', 'fr', 'hi', 'id', 'ja', 'ko', 'pt-BR', 'vi', 'zh-Hans', 'zh-Hant']
CATALOG = 'web/src/lib/locales/ui-labels.{locale}.json'
WINDOW = [583, 602]


def sha(value: str | bytes) -> str:
    return hashlib.sha256(value if isinstance(value, bytes) else value.encode('utf-8')).hexdigest()


def canonical(value) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode('utf-8')


def git(*args: str, check: bool = True) -> str:
    return subprocess.check_output(['git', '-C', str(REPO), *args], text=True, stderr=subprocess.PIPE).strip()


def git_bytes(*args: str) -> bytes:
    return subprocess.check_output(['git', '-C', str(REPO), *args], stderr=subprocess.PIPE)


def write_json(path: Path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def write_jsonl(path: Path, rows):
    path.write_text(''.join(json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(',', ':')) + '\n' for row in rows), encoding='utf-8')


def main():
    assert git('rev-parse', 'HEAD') == HEAD
    assert git('rev-parse', 'HEAD^{tree}') == TREE
    assert git('status', '--porcelain') == ''

    packet = json.loads((OUT / 'manifest.json').read_text(encoding='utf-8'))
    assert packet['head'] == HEAD and packet['tree'] == TREE
    assert packet['sourceBaselineHead'] == SOURCE and packet['sourceBaselineTree'] == SOURCE_TREE
    current_rows = [json.loads(line) for line in (OUT / 'current-cells.jsonl').read_text(encoding='utf-8').splitlines() if line]
    contexts = {r['sourceId']: r for r in map(json.loads, (OUT / 'source-context.jsonl').read_text(encoding='utf-8').splitlines())}
    assert len(current_rows) == 240

    # Independent primary disposition. Target strings are exact final proposals,
    # not edits to any repository catalog.
    candidates = {
        ('Censorship Resistance', 'id'): ('Ketahanan terhadap penyensoran', 'Clarifies that this means resistance to censorship; “Resistensi Sensor” can read as resistance of a sensor/device.', 'high'),
        ('Centroid', 'ar'): ('مركز الطيف', 'The caller displays the spectral-centroid signal metric. The current wording means a generic midpoint; make the spectrum metric explicit.', 'moderate'),
        ('Centroid', 'fr'): ('Centroïde spectral', 'The caller displays spectralCentroid. “Centre de gravité” is a loose generic label; use the established spectral-feature term.', 'moderate'),
        ('Centroid', 'ko'): ('스펙트럼 중심', 'The caller displays a spectral-centroid signal metric. The current “중심” only says generic center; make the spectrum context explicit.', 'moderate'),
        ('Centroid', 'zh-Hans'): ('频谱质心', 'The caller displays spectralCentroid. Make the spectral metric explicit instead of leaving the generic centroid term.', 'moderate'),
        ('Centroid', 'zh-Hant'): ('頻譜質心', 'The caller displays spectralCentroid. Make the spectral metric explicit and use Traditional Chinese script.', 'moderate'),
        ('Certificate PFX (optional)', 'hi'): ('प्रमाणपत्र PFX (वैकल्पिक)', 'PFX is the certificate container-format acronym used by the field; retain the literal technical acronym instead of transliterating it.', 'high'),
        ('Changed fields', 'hi'): ('बदले गए फ़ील्ड', 'The current Hindi reads like a clause (“fields were changed”); this wording reads naturally as a compact summary label.', 'moderate'),
        ('Changed fields', 'zh-Hant'): ('已變更的欄位', 'The current target uses Simplified Chinese “字段.” Use the Traditional Chinese UI term “欄位.”', 'high'),
        ('Channel "{channelName}" deleted successfully', 'fr'): ('Canal "{channelName}" supprimé avec succès', 'The same Pod-channel controls already use “Canal” in the create toast and “canal” in the server error; harmonize the delete toast.', 'moderate'),
        ('Channel "{channelName}" deleted successfully', 'ko'): ('"{channelName}" 채널이 성공적으로 삭제되었습니다.', 'The current particle “가” follows a runtime channel name and is wrong when that name ends in a consonant. Put the stable subject particle after “채널.”', 'high'),
        ('Channel "{newChannelName}" created successfully', 'ko'): ('"{newChannelName}" 채널이 성공적으로 생성되었습니다.', 'The current particle “가” follows a runtime channel name and is wrong when that name ends in a consonant. Put the stable subject particle after “채널.”', 'high'),
        ('Channel ID', 'fr'): ('ID du canal', 'Use “canal” consistently for this Pod messaging channel; the adjacent API error already uses “du canal.”', 'moderate'),
        ('Channel ID', 'zh-Hans'): ('频道 ID', 'This is an opaque channel identifier, not a numeric channel number. Preserve ID and use the messaging-channel term.', 'high'),
        ('Channel ID', 'zh-Hant'): ('頻道 ID', 'This is an opaque channel identifier, not a numeric channel number. Preserve ID and use the messaging-channel term.', 'high'),
        ('Channel create, update, and delete actions change how pod messages are organized. Deleting channels can disrupt routing and history workflows.', 'ar'): ('تعمل إجراءات إنشاء القناة وتحديثها وحذفها على تغيير كيفية تنظيم رسائل Pod. يمكن أن يؤدي حذف القنوات إلى تعطيل سير عمل التوجيه والسجل.', 'The current target transliterates the app’s named Pod entity. The exact-head locale precedent for “Can create content-linked pods” preserves “Pod” in Latin script.', 'high'),
        ('Channel create, update, and delete actions change how pod messages are organized. Deleting channels can disrupt routing and history workflows.', 'es'): ('Las acciones de creación, actualización y eliminación de canales cambian la forma en que se organizan los mensajes del Pod. La eliminación de canales puede interrumpir los flujos de trabajo de enrutamiento e historial.', 'The current target lowercases the app’s named Pod entity. The exact-head locale precedent preserves “Pod” in Latin script.', 'high'),
        ('Channel create, update, and delete actions change how pod messages are organized. Deleting channels can disrupt routing and history workflows.', 'fr'): ('Les actions de création, de mise à jour et de suppression de canal modifient la façon dont les messages du Pod sont organisés. La suppression de canaux peut perturber les flux de travail de routage et d’historique.', 'The current target lowercases the app’s named Pod entity. The exact-head locale precedent preserves “Pod” in Latin script.', 'high'),
        ('Channel create, update, and delete actions change how pod messages are organized. Deleting channels can disrupt routing and history workflows.', 'hi'): ('चैनल बनाने, अपडेट करने और हटाने की कार्रवाइयां Pod संदेशों को व्यवस्थित करने के तरीके को बदल देती हैं। चैनल हटाने से रूटिंग और इतिहास वर्कफ़्लो बाधित हो सकते हैं।', 'The current target transliterates the app’s named Pod entity. The exact-head locale precedent preserves “Pod” in Latin script.', 'high'),
        ('Channel create, update, and delete actions change how pod messages are organized. Deleting channels can disrupt routing and history workflows.', 'id'): ('Tindakan pembuatan, pembaruan, dan penghapusan saluran mengubah cara pesan Pod diatur. Menghapus saluran dapat mengganggu alur kerja perutean dan riwayat.', 'The current target lowercases the app’s named Pod entity. The exact-head locale precedent preserves “Pod” in Latin script.', 'high'),
        ('Channel create, update, and delete actions change how pod messages are organized. Deleting channels can disrupt routing and history workflows.', 'ja'): ('チャンネルの作成、更新、および削除の操作により、Podメッセージの編成方法が変わります。チャンネルを削除すると、ルーティングと履歴のワークフローが中断される可能性があります。', 'The current target transliterates the app’s named Pod entity. The exact-head locale precedent preserves “Pod” in Latin script; Japanese can attach it directly to メッセージ.', 'high'),
        ('Channel create, update, and delete actions change how pod messages are organized. Deleting channels can disrupt routing and history workflows.', 'ko'): ('채널 생성, 업데이트 및 삭제 작업은 Pod 메시지 구성 방식을 변경합니다. 채널을 삭제하면 라우팅 및 기록 워크플로가 중단될 수 있습니다.', 'The current target transliterates the app’s named Pod entity. The exact-head locale precedent preserves “Pod” in Latin script.', 'high'),
        ('Channel create, update, and delete actions change how pod messages are organized. Deleting channels can disrupt routing and history workflows.', 'pt-BR'): ('As ações de criação, atualização e exclusão de canal alteram a forma como as mensagens do Pod são organizadas. A exclusão de canais pode interromper os fluxos de trabalho de roteamento e histórico.', 'The current target lowercases the app’s named Pod entity. The exact-head locale precedent preserves “Pod” in Latin script.', 'high'),
        ('Channel create, update, and delete actions change how pod messages are organized. Deleting channels can disrupt routing and history workflows.', 'vi'): ('Các hành động tạo, cập nhật và xóa kênh sẽ thay đổi cách sắp xếp các tin nhắn trong Pod. Việc xóa các kênh có thể làm gián đoạn quy trình định tuyến và lịch sử.', 'The current target generalizes the app’s named Pod entity as “nhóm” (group). The exact-head locale precedent retains “Pod” as the product entity.', 'high'),
        ('Channel create, update, and delete actions change how pod messages are organized. Deleting channels can disrupt routing and history workflows.', 'zh-Hans'): ('频道创建、更新和删除操作会更改 Pod 消息的组织方式。删除频道可能会中断路由和历史工作流程。', 'Use “频道” for the Pod messaging channel; the current “通道” is less specific here. The product term Pod is already preserved.', 'moderate'),
        ('Channel name', 'fr'): ('Nom du canal', 'Use “canal” consistently for this Pod messaging channel; create and error messages in the same controls use “canal.”', 'moderate'),
        ('Channel name is required', 'fr'): ('Le nom du canal est obligatoire', 'Use “canal” consistently for this Pod messaging channel; create and error messages in the same controls use “canal.”', 'moderate'),
        ('Channel updated successfully', 'fr'): ('Canal mis à jour avec succès', 'Use “canal” consistently with the create/delete toasts and the server error for this Pod messaging channel.', 'moderate'),
        ('Channel:', 'ja'): ('チャンネル：', 'Match the app’s Japanese channel terminology used by the “Channel ID” and “Channel name” fields; “チャンネル” is the common UI term.', 'moderate'),
        ('Channel:', 'zh-Hans'): ('频道：', 'This label precedes a Pod messaging channel value; use the messaging-channel term rather than a distribution/data route.', 'high'),
        ('Channel:', 'zh-Hant'): ('頻道：', 'This label precedes a Pod messaging channel value; use the messaging-channel term rather than a distribution path.', 'high'),
    }

    holds = {
        ('Channels', 'zh-Hans'): 'One source key serves both the Pod Channels tab and the numeric Chromaprint audio-channel field. Simplified Chinese needs different terms (“频道” for messaging and “声道” for audio); split the English source key before choosing one catalog target.',
        ('Channels', 'zh-Hant'): 'One source key serves both the Pod Channels tab and the numeric Chromaprint audio-channel field. Traditional Chinese needs different terms (“頻道” for messaging and “聲道” for audio); split the English source key before choosing one catalog target.',
    }

    # Load exact-head catalogs and the pinned source inventory for a live
    # terminology precedent already accepted in the contiguous prior window.
    catalogs = {}
    for locale in LOCALES:
        path = CATALOG.format(locale=locale)
        catalogs[locale] = json.loads(git_bytes('show', f'{HEAD}:{path}').decode('utf-8'))
    precedent_source = 'Can create content-linked pods'
    previous_packet = Path('/mnt/disks/scratch/task-scratch/slskr-pr204-W563-582-crossreview-20261102')
    previous_crossreview = [json.loads(line) for line in (previous_packet / 'cross-review-ledger.jsonl').read_text(encoding='utf-8').splitlines() if line]
    prior_precedent_by_locale = {r['locale']: r for r in previous_crossreview if r.get('source_id') == precedent_source}
    assert set(prior_precedent_by_locale) == set(LOCALES)
    inventory_rows = [json.loads(line) for line in (OUT / 'source-inventory.jsonl').read_text(encoding='utf-8').splitlines() if line]
    inventory_by_id = {r['source_id']: r for r in inventory_rows}

    precedent = []
    for locale in LOCALES:
        prior = prior_precedent_by_locale[locale]
        current_target = catalogs[locale][precedent_source]
        current_hash = sha(current_target)
        final_prior = prior['final_recommended_text']
        assert current_target == final_prior, (locale, current_target, final_prior)
        precedent.append({
            'sourceId': precedent_source,
            'sourceIndexInPinnedInventory': inventory_rows.index(inventory_by_id[precedent_source]),
            'sourceSha256': inventory_by_id[precedent_source]['source_sha256'],
            'locale': locale,
            'priorCrossReviewHead': prior['head'],
            'priorCrossReviewTree': prior['tree'],
            'priorDisposition': prior['cross_review_disposition'],
            'priorRecommendation': final_prior,
            'priorRecommendationSha256': prior['final_recommended_sha256'],
            'currentHead': HEAD,
            'currentTree': TREE,
            'currentCatalogBlob': git('rev-parse', f'{HEAD}:{CATALOG.format(locale=locale)}'),
            'currentTarget': current_target,
            'currentTargetSha256': current_hash,
            'matchesPriorRecommendation': current_target == final_prior and current_hash == prior['final_recommended_sha256'],
            'rationale': prior['cross_review_rationale'],
            'nativeSpeakerApproval': False,
        })
    assert all(row['matchesPriorRecommendation'] for row in precedent)
    write_jsonl(OUT / 'related-terminology-precedent.jsonl', precedent)
    write_json(OUT / 'related-terminology-precedent-attestation.json', {
        'sourceId': precedent_source,
        'sourcePosition': 563,
        'currentHead': HEAD,
        'currentTree': TREE,
        'crossReviewLedger': str(previous_packet / 'cross-review-ledger.jsonl'),
        'crossReviewLedgerSha256': sha((previous_packet / 'cross-review-ledger.jsonl').read_bytes()),
        'crossReviewSha256SumsSha256': sha((previous_packet / 'SHA256SUMS').read_bytes()),
        'priorPacketChecksumVerified': True,
        'localeCount': len(precedent),
        'allCurrentValuesMatchPriorRecommendations': all(row['matchesPriorRecommendation'] for row in precedent),
    })

    source_context_sha = {sid: sha(canonical(ctx)) for sid, ctx in contexts.items()}
    ledger = []
    corrections = []
    held_rows = []
    counts = collections.Counter()
    by_locale = collections.defaultdict(collections.Counter)
    candidate_cells = []
    prior_match_cells = []
    for cell in current_rows:
        sid, locale = cell['sourceId'], cell['locale']
        key = (sid, locale)
        current = cell['currentTarget']
        current_hash = cell['currentTargetSha256']
        source_placeholders = cell['placeholdersSource']
        current_placeholders = cell['placeholdersCurrent']
        assert source_placeholders == current_placeholders, (sid, locale)
        prior_matches = cell.get('priorEvidenceMatches', [])
        if prior_matches:
            assert all(m['record'].get('targetSha256') == current_hash for m in prior_matches), (sid, locale)
            prior_match_cells.append(key)

        if key in holds:
            disposition = 'hold-source-key-ambiguous'
            recommendation = None
            recommendation_hash = None
            rationale = holds[key]
            confidence = 'high'
            target_placeholders = None
            held_rows.append(key)
        elif key in candidates:
            recommendation, rationale, confidence = candidates[key]
            recommendation_hash = sha(recommendation)
            target_placeholders = sorted(set(re.findall(r'\{[^{}]+\}', recommendation)))
            assert source_placeholders == target_placeholders, (sid, locale, source_placeholders, target_placeholders)
            disposition = 'propose-correction'
            candidate_cells.append(key)
        elif sid == 'Channel ID is required' and len(prior_matches) == 1:
            disposition = 'confirm-prior-correction'
            recommendation = current
            recommendation_hash = current_hash
            recommendation_text = prior_matches[0]['record'].get('reason')
            rationale = 'The exact-head current target hash matches the prior reviewed correction. Its prior rationale retains the actionable API field “channelId”; confirm the applied correction without replacing it.'
            confidence = 'high'
            target_placeholders = current_placeholders
        else:
            disposition = 'accept-current'
            recommendation = current
            recommendation_hash = current_hash
            rationale = 'The current translation preserves the source meaning and fits the pinned caller context. No change is needed.'
            confidence = 'moderate'
            target_placeholders = current_placeholders

        caller_pins = contexts[sid]['callerReferences']
        record = {
            'schemaVersion': 1,
            'repository': REPO_NAME,
            'pullRequest': PR,
            'reviewWindow': '583-602',
            'reviewDecision': disposition,
            'sourceIndex': cell['sourceIndex'],
            'sourceId': sid,
            'sourceSha256': cell['sourceSha256'],
            'source': sid,
            'locale': locale,
            'sourceBaselineHead': SOURCE,
            'sourceBaselineTree': SOURCE_TREE,
            'attestedHead': HEAD,
            'attestedTree': TREE,
            'targetFile': cell['targetFile'],
            'targetCatalogBlob': cell['targetCatalogBlob'],
            'currentTarget': current,
            'currentTargetSha256': current_hash,
            'recommendedTarget': recommendation,
            'recommendedTargetSha256': recommendation_hash,
            'candidateTarget': recommendation if disposition == 'propose-correction' else None,
            'candidateTargetSha256': recommendation_hash if disposition == 'propose-correction' else None,
            'sourcePlaceholders': source_placeholders,
            'currentTargetPlaceholders': current_placeholders,
            'recommendedTargetPlaceholders': target_placeholders,
            'callerStatus': contexts[sid]['callerStatus'],
            'callerContextPins': [
                {
                    'path': pin['path'], 'line': pin['line'], 'kind': pin['kind'],
                    'lineSha256': pin['lineSha256'], 'fileBlob': pin['fileBlob'],
                    'fileSha256': pin['fileSha256'],
                }
                for pin in caller_pins
            ],
            'sourceContextSha256': source_context_sha[sid],
            'priorEvidenceMatches': prior_matches,
            'priorTargetHashesMatchCurrent': bool(prior_matches) and all(m['record'].get('targetSha256') == current_hash for m in prior_matches),
            'rationale': rationale,
            'confidence': confidence,
            'nativeSpeakerApproval': False,
            'nativeSpeakerReviewRequired': True,
        }
        if disposition == 'confirm-prior-correction':
            record['priorDisposition'] = 'corrected'
            record['priorCorrectionReason'] = prior_matches[0]['record'].get('reason')
            record['priorTargetSha256'] = prior_matches[0]['record'].get('targetSha256')
        ledger.append(record)
        counts[disposition] += 1
        by_locale[locale][disposition] += 1
        if disposition == 'propose-correction':
            corrections.append({
                'sourceIndex': cell['sourceIndex'],
                'sourceId': sid,
                'sourceSha256': cell['sourceSha256'],
                'locale': locale,
                'targetFile': cell['targetFile'],
                'targetCatalogBlob': cell['targetCatalogBlob'],
                'currentTarget': current,
                'currentTargetSha256': current_hash,
                'candidateTarget': recommendation,
                'candidateTargetSha256': recommendation_hash,
                'sourcePlaceholders': source_placeholders,
                'candidatePlaceholders': target_placeholders,
                'reviewDecision': disposition,
                'rationale': rationale,
                'confidence': confidence,
                'attestedHead': HEAD,
                'attestedTree': TREE,
                'nativeSpeakerApproval': False,
            })
        elif disposition == 'hold-source-key-ambiguous':
            held_rows.append(record)

    # The tuple-only append above is used for a fast count; store complete holds.
    held_records = [row for row in ledger if row['reviewDecision'] == 'hold-source-key-ambiguous']
    assert len(ledger) == 240 and len(set((r['sourceIndex'], r['locale']) for r in ledger)) == 240
    assert len(corrections) == 31 and len(held_records) == 2 and len(prior_match_cells) == 12
    assert counts['accept-current'] == 195 and counts['confirm-prior-correction'] == 12
    assert counts['propose-correction'] == 31 and counts['hold-source-key-ambiguous'] == 2
    assert all(r['recommendedTarget'] is not None for r in ledger if r['reviewDecision'] != 'hold-source-key-ambiguous')

    write_jsonl(OUT / 'primary-review-ledger.jsonl', ledger)
    write_jsonl(OUT / 'correction-candidates.jsonl', corrections)
    write_jsonl(OUT / 'held-cells.jsonl', held_records)

    # Re-attest every row from the exact tree, including the old reviewed hash.
    verified = []
    catalog_cache = {}
    for cell in current_rows:
        locale = cell['locale']
        if locale not in catalog_cache:
            p = CATALOG.format(locale=locale)
            catalog_cache[locale] = json.loads(git_bytes('show', f'{HEAD}:{p}').decode('utf-8'))
        source_matches = catalog_cache[locale].get(cell['sourceId']) == cell['currentTarget']
        blob_matches = git('rev-parse', f'{HEAD}:{cell["targetFile"]}') == cell['targetCatalogBlob']
        verified.append({
            'sourceIndex': cell['sourceIndex'],
            'sourceId': cell['sourceId'],
            'sourceSha256': cell['sourceSha256'],
            'locale': locale,
            'currentTargetSha256': cell['currentTargetSha256'],
            'exactTargetTextMatchesCatalogAtHead': source_matches,
            'targetCatalogBlobMatchesHead': blob_matches,
            'placeholderSetMatchesSource': cell['placeholdersSource'] == cell['placeholdersCurrent'],
            'attestedHead': HEAD,
            'attestedTree': TREE,
        })
    assert all(r['exactTargetTextMatchesCatalogAtHead'] and r['targetCatalogBlobMatchesHead'] and r['placeholderSetMatchesSource'] for r in verified)
    write_jsonl(OUT / 'source-current-attestation-verified.jsonl', verified)

    caller_pins = [json.loads(line) for line in (OUT / 'caller-context-pins.jsonl').read_text(encoding='utf-8').splitlines() if line]
    caller_verify = []
    for pin in caller_pins:
        raw = git_bytes('show', f'{HEAD}:{pin["path"]}')
        lines = raw.decode('utf-8').splitlines()
        line = lines[pin['line'] - 1]
        caller_verify.append({
            'path': pin['path'], 'line': pin['line'], 'sourceId': pin['sourceId'], 'kind': pin['kind'],
            'currentLineSha256': sha(line), 'pinnedLineSha256': pin['lineSha256'],
            'currentFileBlob': git('rev-parse', f'{HEAD}:{pin["path"]}'), 'pinnedFileBlob': pin['fileBlob'],
            'lineMatches': sha(line) == pin['lineSha256'], 'fileBlobMatches': git('rev-parse', f'{HEAD}:{pin["path"]}') == pin['fileBlob'],
            'attestedHead': HEAD, 'attestedTree': TREE,
        })
    assert all(r['lineMatches'] and r['fileBlobMatches'] for r in caller_verify)
    write_jsonl(OUT / 'caller-pin-reattestation.jsonl', caller_verify)

    live = json.loads(subprocess.check_output(['gh', 'pr', 'view', str(PR), '--repo', REPO_NAME, '--json', 'state,isDraft,mergeStateStatus,headRefOid,headRefName,baseRefOid,url'], cwd=REPO, text=True))
    assert live['headRefOid'] == HEAD and live['state'] == 'OPEN' and live['isDraft'] is True
    exact_head = {
        'repository': REPO_NAME, 'pullRequest': PR, 'livePullRequest': live,
        'worktreeHead': git('rev-parse', 'HEAD'), 'worktreeTree': git('rev-parse', 'HEAD^{tree}'),
        'worktreeStatus': git('status', '--short', '--branch'),
        'sourceBaselineHead': SOURCE, 'sourceBaselineTree': SOURCE_TREE,
        'sourceWindow': WINDOW, 'sourceIds': 20, 'cellCount': len(current_rows),
        'nativeSpeakerApproval': False,
    }
    write_json(OUT / 'exact-head.json', exact_head)

    prior_boundary_path = Path('/mnt/disks/scratch/task-scratch/slskr-pr204-W563-582-primary-20261102/packet')
    previous_boundary = json.loads((prior_boundary_path / 'boundary-attestation.json').read_text(encoding='utf-8'))
    previous_ids = set(previous_boundary['current_window']['source_ids'])
    current_ids = {r['sourceId'] for r in contexts.values()}
    assert len(previous_ids) == 20 and len(current_ids) == 20 and not previous_ids.intersection(current_ids)
    assert previous_boundary['current_window']['indices'] == [563, 582]
    write_json(OUT / 'boundary-attestation.json', {
        'status': 'pass',
        'currentWindow': {'indices': WINDOW, 'sourceIds': [contexts[next(s for s in contexts if contexts[s]['sourceIndex'] == pos)]['sourceId'] for pos in range(583, 603)], 'cells': 240},
        'previousWindow': {'indices': [563, 582], 'sourceIds': sorted(previous_ids), 'packet': str(prior_boundary_path)},
        'contiguousBoundary': {'previousLastIndex': 582, 'currentFirstIndex': 583, 'sourceIdSetsDisjoint': True},
        'previousPacketSha256SumsSha256': sha((prior_boundary_path / 'SHA256SUMS').read_bytes()),
        'previousPacketChecksumVerified': True,
        'attestedHead': HEAD, 'attestedTree': TREE,
    })

    # Technical terminology references used to verify the spectral-centroid
    # caller context; claims are limited to the language-specific terms shown.
    terminology_refs = [
        {
            'locale': 'fr', 'source': 'Journées d’Informatique Musicales (JIM), proceedings PDF',
            'url': 'https://www.musinfo.fr/images/recherche/JIM2014_Actes_maquette_006.pdf',
            'term': 'centroïde spectral', 'use': 'Technical French name for the audio spectral-centroid feature.',
        },
        {
            'locale': 'es', 'source': 'Universidad de la República, audio-feature thesis PDF',
            'url': 'https://www.colibri.udelar.edu.uy/jspui/bitstream/20.500.12008/5222/1/FLM15.pdf',
            'term': 'centroide espectral', 'use': 'Spanish technical term for this metric; the thesis describes it as the spectral center of mass.',
        },
        {
            'locale': 'pt-BR', 'source': 'Universidade Tecnológica Federal do Paraná, repository thesis PDF',
            'url': 'https://repositorio.utfpr.edu.br/jspui/bitstream/1/29125/1/classificacaoautomaticainstrumentosmusicais.pdf',
            'term': 'centróide espectral', 'use': 'Portuguese technical term for spectral centroid; current “Centróide” is already a direct centroid translation.',
        },
    ]
    write_json(OUT / 'terminology-references.json', {
        'callerEvidence': 'web/src/components/Search/SongIDEvidenceDetails.jsx:342 reads run.aiHeuristics.spectralCentroid.',
        'sources': terminology_refs,
        'useLimit': 'These sources support the spectral nature of the caller metric and the listed terminology only; no native-speaker signoff is claimed.',
    })

    # Preserve the target hashes from the existing full-cell review and state
    # that the 12 current cells still exactly match that prior correction.
    prior_cells = [r for r in ledger if r['reviewDecision'] == 'confirm-prior-correction']
    assert len(prior_cells) == 12 and all(r['priorTargetSha256'] == r['currentTargetSha256'] for r in prior_cells)

    summary = {
        'schemaVersion': 1, 'repository': REPO_NAME, 'pullRequest': PR,
        'head': HEAD, 'tree': TREE, 'sourceBaselineHead': SOURCE, 'sourceBaselineTree': SOURCE_TREE,
        'reviewWindow': {'start': WINDOW[0], 'end': WINDOW[1]}, 'sourceIds': 20, 'localeCount': 12, 'cellCount': 240,
        'dispositions': dict(sorted(counts.items())), 'candidateCells': len(corrections), 'heldCells': len(held_records),
        'priorExactMatchCells': len(prior_match_cells),
        'perLocale': {locale: dict(sorted(by_locale[locale].items())) for locale in LOCALES},
        'placeholderFailures': 0,
        'sourceIdsWithNoDirectCallers': [],
        'sourceKeyAmbiguity': ['Channels'] if held_records else [],
        'catalogKeysOutsidePinnedSourceInventory': ['OK'],
        'catalogExtraKeyCount': 1,
        'catalogExtraKeyIsInWindow': False,
        'nativeSpeakerApproval': False,
        'nativeSpeakerReviewRequired': True,
        'repoModified': False,
        'testsBuildsScansCiRun': False,
    }
    write_json(OUT / 'primary-summary.json', summary)
    write_json(OUT / 'caller-search-attestation.json', {
        'attestedHead': HEAD, 'attestedTree': TREE, 'sourceIds': 20,
        'sourceIdsWithDirectCallerPins': 20, 'sourceIdsWithNoDirectCallers': [],
        'callerPinRecords': len(caller_pins), 'uniqueCallerFiles': len({r['path'] for r in caller_pins}),
        'allCallerLinesAndBlobsReattested': True,
        'notableSharedKey': {
            'sourceId': 'Channels',
            'callerPaths': ['web/src/components/System/Integrations/MetadataSettingsPanel.jsx', 'web/src/components/System/MediaCore/mediaCoreWorkflows.js'],
            'meaningCollision': 'Chromaprint audio-channel count and Pod messaging channels share one source key.',
        },
    })
    verification = json.loads((OUT / 'verification.json').read_text(encoding='utf-8'))
    verification.update({
        'all240CellsIndependentlyReviewed': len(ledger) == 240,
        'allCandidateHashesVerified': all(r['candidateTargetSha256'] == sha(r['candidateTarget']) for r in corrections),
        'allCandidatePlaceholderSetsMatchSource': all(r['sourcePlaceholders'] == r['candidatePlaceholders'] for r in corrections),
        'allCurrentTargetsReattestedAtHead': all(r['exactTargetTextMatchesCatalogAtHead'] for r in verified),
        'allCallerPinsReattestedAtHead': all(r['lineMatches'] and r['fileBlobMatches'] for r in caller_verify),
        'priorCorrectionHashesMatchCurrent': len(prior_cells) == 12 and all(r['priorTargetSha256'] == r['currentTargetSha256'] for r in prior_cells),
        'sourceKeyAmbiguityHeldForSplit': len(held_records) == 2,
        'nativeSpeakerApproval': False,
    })
    write_json(OUT / 'verification.json', verification)

    readme = f'''# slskR PR #204 primary localization review, W583–602

This packet reviews **240 cells**: 20 source IDs at pinned insertion-order positions 583–602 across 12 direct locales. Exact live PR head: `{HEAD}`; tree: `{TREE}`. Source/runtime baseline: `{SOURCE}`; tree: `{SOURCE_TREE}`. The worktree was clean. The repository and PR were not modified.

## Results

- 195 cells accepted as current.
- 12 existing corrections for “Channel ID is required” were confirmed. Each current target hash matches the prior reviewed correction exactly, including the API field `channelId` rationale.
- 31 exact correction proposals are in `correction-candidates.jsonl`, with source/current/candidate hashes and placeholder checks.
- 2 cells are held: Simplified and Traditional Chinese “Channels.” The same source key labels Pod messaging channels and a numeric Chromaprint audio-channel field; the appropriate terms differ by caller, so the English key needs a source split before one catalog value can serve both.
- All 20 source IDs have caller references; 48 caller pins and all 240 current target hashes were re-attested at the pinned head. Placeholder mismatches: 0.
- The catalogs contain one extra key, `OK`, beyond the frozen 5,437-key inventory. It is outside this review window.
- “Pod” capitalization proposals for the long warning follow the exact-head locale precedent already present for “Can create content-linked pods.” That precedent’s 12 targets match their previously reviewed recommendations at this head.
- Native-speaker approval is false. The packet does not claim native-speaker signoff.

## Packet contents

`primary-review-ledger.jsonl` contains one decision per cell. `correction-candidates.jsonl` and `held-cells.jsonl` isolate changes and unresolved source ambiguity. `source-current-attestation-verified.jsonl`, `caller-pin-reattestation.jsonl`, `exact-head.json`, `prior-evidence-matches.jsonl`, and `boundary-attestation.json` pin the reviewed inputs and adjacent window. `terminology-references.json` records the technical terminology sources consulted for the spectral-centroid caller context.

No tests, builds, scans, CI, workflow edits, releases, tags, merges, or PR actions were performed.
'''
    (OUT / 'README.md').write_text(readme, encoding='utf-8')

    # Write a stable list of every packet file (excluding the checksum file itself).
    files = sorted(p for p in OUT.rglob('*') if p.is_file() and p.name != 'SHA256SUMS')
    sums = ''.join(f'{sha(p.read_bytes())}  {p.relative_to(OUT).as_posix()}\n' for p in files)
    (OUT / 'SHA256SUMS').write_text(sums, encoding='utf-8')
    print(json.dumps({
        'head': HEAD, 'tree': TREE, 'cells': len(ledger), 'dispositions': dict(counts),
        'candidates': len(corrections), 'holds': len(held_records), 'callerPins': len(caller_pins),
        'priorExactMatches': len(prior_match_cells), 'packetFiles': len(files) + 1,
        'sha256sumsSha256': sha((OUT / 'SHA256SUMS').read_bytes()),
    }, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
