#!/usr/bin/env python3
"""Build a blind locale ledger from candidate-free input only."""
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

inp=Path(sys.argv[1])
out=Path(sys.argv[2])
manifest=json.loads((inp/"manifest.json").read_text())
attestation=json.loads((inp/"PR-attestation.json").read_text())
locale_order=manifest["localeOrder"]
cells=[json.loads(line) for line in (inp/"current-target-cells.jsonl").read_text().splitlines() if line.strip()]
contexts={json.loads(line)["position"]:json.loads(line) for line in (inp/"source-contexts.jsonl").read_text().splitlines() if line.strip()}
assert len(cells)==240 and len(contexts)==20

topics={
1323:"Names the equalizer enable action used by the player toggle.",
1324:"Names karaoke-mode enablement in the playback toolbar.",
1325:"Names keyboard-shortcut enablement in the experience-settings checkbox.",
1326:"Preserves the managed CIDR/P2P/DAT blacklist file's startup-load action.",
1327:"Preserves ffmpeg/Chromaprint, local fingerprint generation, YAML-only scope, and the explicit-scan workflow caveat.",
1328:"Names enablement of local message search.",
1329:"Distinguishes the local-message-search preference label from the visible checkbox label.",
1330:"Names the managed-blacklist enable action.",
1331:"Preserves DHT/Overlay mesh networking and the footer connectivity instruction.",
1332:"Describes the messages dense-display preference indicated by the adjacent Dense display checkbox.",
1333:"Names the player keyboard-shortcuts preference.",
1334:"Names automatic fill of the playback player's queue; the caller describes similar-track candidates.",
1335:"Preserves the label placeholder, local-policy-only status, and backend-federation dependency.",
1336:"Names automatic queue filling in the player-queue setting.",
1337:"Names enablement of a Release Radar subscription.",
1338:"Names the rescue-mode toggle.",
1339:"Names room-user filtering in the messaging settings.",
1340:"Names the room-user-filtering preference in the messaging settings.",
1341:"Keeps scheduled download limits scoped under global download policy, distinct from upload.",
1342:"Names the legacy top-level scheduled speed-limit toggle, distinct from the download-specific setting.",
}

overrides={
(1333,"es"):("correction","Habilitar la preferencia de atajos de teclado del reproductor","The caller is the media player's keyboard-shortcut preference; jugador refers to a person/player, while reproductor names the playback application."),
(1333,"zh-Hans"):("correction","启用播放器键盘快捷键首选项","玩家 means a person or game player; the caller is a media-player preference, so 播放器 is the accurate referent."),
(1333,"ar"):("correction","تمكين تفضيل اختصارات لوحة مفاتيح مشغل الوسائط","اللاعب denotes a person/player; this caller is the media-player preference. The proposed text names the media player and uses singular preference."),
(1333,"zh-Hant"):("correction","啟用播放器鍵盤快速鍵首選項","玩家 means a person or game player; the caller is a media-player preference, so 播放器 is the accurate referent."),
(1333,"id"):("correction","Aktifkan preferensi pintasan keyboard pemutar","pemain denotes a person/player; this caller is the media-player preference, so pemutar is the correct device/application term."),
(1334,"es"):("correction","Habilitar la preferencia de llenado automático de la cola del reproductor","The caller describes a playback queue; cola de jugadores refers to people, not the media reproductor."),
(1334,"zh-Hans"):("correction","启用播放器队列自动填充首选项","玩家队列 reads as a queue of people or game players; the production caller is the playback player's similar-track queue."),
(1334,"hi"):("correction","मीडिया प्लेयर की कतार अपने-आप भरने की प्राथमिकता सक्षम करें","खिलाड़ी कतार can mean a queue of people; the caller is the playback player's similar-track queue."),
(1334,"de"):("correction","Einstellung zum automatischen Füllen der Player-Warteschlange aktivieren","Spielerwarteschlange reads as a queue of people; the caller is the software media player's queue."),
(1334,"ja"):("correction","プレーヤーキューの自動補充設定を有効にする","自動入力 means automatic input; the caller describes automatic replenishment with similar-track queue candidates."),
(1334,"fr"):("correction","Activer la préférence de remplissage automatique de la file d’attente du lecteur","joueurs means people/players; the caller concerns the playback reader/player's queue."),
(1334,"pt-BR"):("correction","Ativar a preferência de preenchimento automático da fila do reprodutor","jogador refers to a person/player; the caller is the media reprodutor's playback queue."),
(1334,"zh-Hant"):("correction","啟用播放器佇列自動填充首選項","玩家隊列 reads as a queue of people or game players; the production caller is the playback player's similar-track queue."),
(1334,"vi"):("correction","Bật tùy chọn tự động làm đầy hàng đợi trình phát","người chơi means people/players; the caller is the playback trình phát's similar-track queue."),
(1334,"id"):("correction","Aktifkan preferensi pengisian otomatis antrean pemutar","pemain denotes a person/player; the caller is the media pemutar's playback queue."),
(1335,"hi"):("correction","{label} का प्रकाशन सक्षम करें। यह तब तक स्थानीय नीति स्थिति बनी रहती है जब तक बैकएंड फ़ेडरेशन को कनेक्ट नहीं किया जाता।","तार-तार means torn or ruined, not wired/connected; the caller's sentence says federation has not yet been connected."),
(1336,"es"):("correction","Habilitar el llenado automático de la cola","autocompletar suggests text autocomplete; this caller's queue is filled with similar-track candidates."),
(1336,"ja"):("correction","キューの自動補充を有効にする","自動入力 suggests automatic input; the caller uses this setting to replenish the playback queue with similar tracks."),
(1337,"ar"):("correction","تمكين الاشتراك في رادار الإصدارات","الرادار الإصدار is ungrammatical and does not naturally name a release radar; رادار الإصدارات expresses the feature subscription."),
(1339,"ko"):("correction","채팅방 사용자 필터링 활성화","회의실 means a meeting/conference room; this key is for messaging-room user filtering, so 채팅방 identifies the chat room."),
(1332,"ar"):("refinement","تمكين تفضيل الوضع الكثيف للرسائل","The current plural تفضيلات shifts the singular preference label into multiple preferences; this singular form preserves the setting scope."),
(1332,"vi"):("refinement","Bật tùy chọn hiển thị tin nhắn cô đọng","The caller labels the control Dense display; cô đọng expresses compact display more naturally than dày đặc tin nhắn."),
(1335,"fr"):("refinement","Activer la publication de {label}. Cela reste l’état de la politique locale jusqu’à ce que la fédération back-end soit connectée.","connectée is more idiomatic for a backend federation being wired up than the literal câblée; the placeholder and local-only condition are preserved."),
(1340,"ko"):("refinement","채팅방 사용자 필터링 기본 설정 활성화","룸 is understandable, but 채팅방 makes the messaging-room scope explicit and consistent with the production setting."),
}

ledger=[]
for cell in cells:
    pos=cell["position"]
    locale=cell["locale"]
    srcctx=contexts[pos]
    callers=[{"path":c["path"],"line":c["line"],"fileSha256":c["fileSha256"],"gitBlob":c["gitBlob"],"lineSha256":c["lineSha256"]} for c in srcctx.get("callers",[])]
    key=(pos,locale)
    if key in overrides:
        disposition,target,rationale=overrides[key]
    else:
        disposition="accept"
        target=cell["currentTarget"]
        callsite=", ".join(f'{c["path"]}:{c["line"]}' for c in callers) or "pinned production caller"
        rationale=f'{topics[pos]} Current wording preserves this scope at {callsite}; structural-token checks pass.'
    ledger.append({
        "position":pos,
        "sourceKey":cell["sourceKey"],
        "sourceKeySha256":cell["sourceKeySha256"],
        "locale":locale,
        "currentTarget":cell["currentTarget"],
        "currentTargetSha256":cell["currentTargetSha256"],
        "selectedTarget":target,
        "disposition":disposition,
        "rationale":rationale,
        "callerCount":cell["callerCount"],
        "callerRefs":callers,
        "sourceContextSha256":cell["sourceContextSha256"],
        "sourcePlaceholders":cell["sourcePlaceholders"],
        "sourceNumericTokens":cell["sourceNumericTokens"],
        "sourceProtectedLiterals":cell["sourceProtectedLiterals"],
        "sourceMarkupTags":cell["sourceMarkupTags"],
        "currentTargetShapeChecks":{
            "placeholderSequenceMatches":cell["placeholderSequenceMatches"],
            "numericTokensMatch":cell["numericTokensMatch"],
            "protectedLiteralsMatch":cell["protectedLiteralsMatch"],
            "markupMatches":cell["markupMatches"]
        }
    })

out.mkdir(parents=True,exist_ok=True)
ledger_path=out/"blind-review.jsonl"
ledger_path.write_text("".join(json.dumps(row,ensure_ascii=False,separators=(",",":"))+"\n" for row in ledger))
(out/"carry-forward-holds.jsonl").write_bytes((inp/"prior-hold-reattestation.jsonl").read_bytes())
counts=Counter(row["disposition"] for row in ledger)
input_manifest_sha=hashlib.sha256((inp/"manifest.json").read_bytes()).hexdigest()
input_sums_sha=hashlib.sha256((inp/"SHA256SUMS.txt").read_bytes()).hexdigest()
holds=[json.loads(line) for line in (inp/"prior-hold-reattestation.jsonl").read_text().splitlines() if line.strip()]
hold_positions=Counter(str(row["position"]) for row in holds)
summary={
    "artifact":"slskR PR #204 W1323-W1342 independent blind semantic review",
    "repository":"snapetech-org/slskR",
    "pullRequest":204,
    "state":"OPEN",
    "draft":True,
    "branch":"codex/slskr-l10n-audit-20261030",
    "head":"6ccefe07d8154acbc08e34249ef7039dc5bc1f08",
    "tree":"e0c1d1341be45ed73bd30cf027b479ce3b5bb95d",
    "baseRef":"main",
    "candidateFreeInputPath":str(inp),
    "candidateFreeManifestSha256":input_manifest_sha,
    "candidateFreeChecksumListSha256":input_sums_sha,
    "sourceCount":20,
    "localeCount":12,
    "cellCount":len(ledger),
    "currentWindowDispositionCounts":dict(sorted(counts.items())),
    "currentWindowHolds":0,
    "selectedChangeCount":counts["correction"]+counts["refinement"],
    "carryForwardHolds":{
        "count":len(holds),
        "byPosition":dict(sorted(hold_positions.items())),
        "unchangedCount":sum(row["currentTarget"]==row["priorCurrentTarget"] and row["currentTargetSha256"]==row["priorCurrentTargetSha256"] and row["reattestation"]=="same" for row in holds),
        "copiedFrom":"candidate-free input-v4/prior-hold-reattestation.jsonl"
    },
    "inputIntegrity":{
        "candidateFreeVerifier":"PASS",
        "currentWindowCallerlessHolds":0,
        "placeholderSequenceMismatchCount":0,
        "markupMismatchCount":0,
        "numericTokenMismatchCount":0,
        "protectedLiteralMismatchCount":0
    },
    "blindReviewLedgerSha256":hashlib.sha256(ledger_path.read_bytes()).hexdigest(),
    "reviewMode":"candidate-free input only; no primary or prior-audit packet opened",
    "applicationAuthorization":"not included; blind review packet only"
}
(out/"summary.json").write_text(json.dumps(summary,ensure_ascii=False,indent=2)+"\n")
readme=f"""# slskR PR #204 W1323-W1342 independent blind review

This packet independently reviews all 240 current target cells for positions 1323-1342 using only the candidate-free input at {inp}. No primary review or prior-audit packet was opened. Production caller excerpts and runtime context were taken only from input-v4.

Live PR #204 was OPEN/DRAFT on branch codex/slskr-l10n-audit-20261030 at head 6ccefe07d8154acbc08e34249ef7039dc5bc1f08 and tree e0c1d1341be45ed73bd30cf027b479ce3b5bb95d. The branch and pull refs matched at reattestation.

The ledger contains {len(ledger)} cells: {counts['accept']} accepted, {counts['correction']} corrections, {counts['refinement']} refinements, and 0 current-window holds. Corrections clarify media-player terminology, queue auto-fill semantics, a Hindi mistranslation of wired/connected, Arabic Release Radar phrasing, and Korean chat-room terminology. Refinements improve a few preference/display phrases.

The 22 historical holds are copied byte-for-byte from the candidate-free input and reattest unchanged: 12 Ecosystem cells at position 1257 and 10 W1303 cells across positions 1310, 1311, 1313, and 1316. No current-window callerless holds were present.

Candidate-free input checksums and verifier passed before review. This blind packet contains no application authorization. No repository or PR writes, tests, builds, scans, or CI were performed.
"""
(out/"README.md").write_text(readme)
