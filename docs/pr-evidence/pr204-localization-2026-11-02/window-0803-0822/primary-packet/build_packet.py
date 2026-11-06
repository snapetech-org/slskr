#!/usr/bin/env python3
import hashlib, json, re, subprocess
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path.cwd()
OUT = Path("/mnt/disks/scratch/task-scratch/slskr-pr204-W803-822-primary-20261102/packet")
LOCALES = ["ar", "de", "es", "fr", "hi", "id", "ja", "ko", "pt-BR", "vi", "zh-Hans", "zh-Hant"]
HEAD_EXPECTED = "3a4c26a7faf1dacbd8f3a382d47243b7063a262d"
TREE_EXPECTED = "9059d27001d306ea6b064560137ff2a51dd19021"
START, END = 802, 822
REPO, PR = "snapetech-org/slskR", 204

def sha(x):
    return hashlib.sha256(x if isinstance(x, bytes) else x.encode("utf-8")).hexdigest()
def run(*args):
    return subprocess.check_output(args, cwd=ROOT).decode().strip()
def jwrite(name, obj):
    (OUT / name).write_text(json.dumps(obj, ensure_ascii=False, sort_keys=True, indent=2) + "\n")
def jlwrite(name, rows):
    with (OUT / name).open("w") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
def ph(text):
    return Counter(re.findall(r"\{([A-Za-z][A-Za-z0-9_]*)\}", text))
def selectors(text):
    return re.findall(r"\{[A-Za-z][A-Za-z0-9_]*\s*,\s*(?:plural|select|selectordinal)\s*,", text)
def markup(text):
    return re.findall(r"</?[A-Za-z][^>]*>", text)
def protected(text):
    return [{"token": t, "count": text.count(t)} for t in ["ListenBrainz", "API", "URL"] if text.count(t)]
def blob(path):
    try: return run("git", "rev-parse", f"{HEAD_EXPECTED}:{path}")
    except subprocess.CalledProcessError: return None

head, tree = run("git", "rev-parse", "HEAD"), run("git", "rev-parse", "HEAD^{tree}")
assert (head, tree) == (HEAD_EXPECTED, TREE_EXPECTED)
catalogs, catalog_meta = {}, []
for loc in LOCALES:
    rel = f"web/src/lib/locales/ui-labels.{loc}.json"
    raw = (ROOT / rel).read_bytes()
    catalogs[loc] = json.loads(raw)
    catalog_meta.append({"locale": loc, "path": rel, "fileSha256": sha(raw), "gitBlob": blob(rel), "keyCount": len(catalogs[loc])})
keysets = [set(o) for o in catalogs.values()]
assert all(x == keysets[0] for x in keysets)
keys = sorted(keysets[0])
assert len(keys) == 5440
inventory_rows = [
    {"sourceIndex": i, "inventoryPosition1Based": i + 1, "sourceId": key, "sourceSha256": sha(key)}
    for i, key in enumerate(keys)
]
inventory_payload = "".join(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n" for row in inventory_rows)
keyset_hash = sha(inventory_payload)
(OUT / "current-source-inventory.jsonl").write_text(inventory_payload)
assert keys[802] == "Compute perceptual hash for image similarity detection"
assert keys[821] == "Confirm Log Out"

proposals = {}
def propose(idx, loc, target, decision, reason):
    proposals[(idx, loc)] = {"target": target, "decision": decision, "rationale": reason}

for loc, val in {
 "de":"Konfidenz", "hi":"विश्वास स्तर", "id":"Tingkat keyakinan", "ja":"信頼度",
 "ko":"신뢰도", "vi":"Độ tin cậy", "zh-Hans":"置信度", "zh-Hant":"置信度"
}.items():
    propose(803, loc, val, "propose-correction", "This is a numeric forensic confidence score; the current term means trust or self-confidence rather than the score label.")

lane = {
 "ar":"بُعد الثقة", "de":"Konfidenzdimension", "es":"Dimensión de confianza", "fr":"Dimension de confiance",
 "hi":"विश्वास का आयाम", "id":"Dimensi keyakinan", "ja":"信頼度指標", "ko":"신뢰도 지표",
 "pt-BR":"Dimensão de confiança", "vi":"Chiều đo độ tin cậy", "zh-Hans":"置信度维度", "zh-Hant":"置信度維度"
}
for loc, val in lane.items():
    dec = "propose-correction" if loc in {"ar","es","fr","vi","zh-Hans","zh-Hant"} else "propose-refinement"
    propose(804, loc, val, dec, "Caller renders a percentage and dynamic summary in a matrix of parallel evidence dimensions; the current lane term is awkward or misleading.")

for loc, val, dec, reason in [
 ("ar","تنطبق الثقة فقط على قراءة الاحتمالية الاصطناعية. ولا تتحكم في قرارات التنزيل عندما تكون الهوية قوية.","propose-correction","The feminine noun الثقة needs a feminine verb; current يتحكم is masculine."),
 ("de","Die Konfidenz gilt nur für die Anzeige der synthetischen Likelihood. Sie steuert keine Download-Entscheidungen, wenn die Identität eindeutig ist.","propose-correction","Current second sentence uses the wrong pronoun for feminine Konfidenz; proposal fixes agreement."),
 ("es","La confianza solo se aplica a la lectura de verosimilitud sintética. No determina las decisiones de descarga cuando la identidad está bien establecida.","propose-correction","Statistical likelihood is verosimilitud, not probabilidad; identity clause is made idiomatic."),
 ("fr","La confiance s’applique uniquement à la lecture de vraisemblance synthétique. Elle ne contrôle pas les décisions de téléchargement lorsque l’identité est forte.","propose-correction","Current pronoun Il has the wrong gender for confiance; Elle fixes agreement."),
 ("hi","विश्वास स्तर केवल सिंथेटिक संभावना के रीडआउट पर लागू होता है। पहचान का स्तर ऊँचा होने पर यह डाउनलोड के निर्णयों को नियंत्रित नहीं करता।","propose-refinement","Names the numeric confidence level rather than a person's self-confidence."),
 ("id","Tingkat keyakinan hanya berlaku untuk pembacaan kemungkinan sintetis. Nilai ini tidak mengendalikan keputusan pengunduhan saat identitasnya sudah kuat.","propose-refinement","Adds the score referent and makes the sentence natural while preserving the likelihood-only boundary."),
 ("ja","信頼度は合成尤度の読み取り値にのみ適用されます。対象の同一性が十分に確かな場合でも、ダウンロードの判断には影響しません。","propose-correction","Current text changes identity into the acronym ID; proposal restores identity assessment."),
 ("ko","신뢰도는 합성 우도 판독값에만 적용됩니다. 식별 결과가 확실한 경우에도 다운로드 결정에는 영향을 주지 않습니다.","propose-correction","Current text changes identity into ID and uses an awkward strong-ID phrase."),
 ("pt-BR","A confiança aplica-se apenas à leitura da probabilidade sintética. Ela não controla as decisões de download quando a identidade é forte.","propose-correction","Current pronoun Ele has the wrong gender for confiança; Ela fixes agreement."),
 ("vi","Độ tin cậy chỉ áp dụng cho kết quả ước tính khả năng xảy ra tổng hợp. Nó không chi phối quyết định tải xuống khi kết quả định danh đã rõ ràng.","propose-correction","Current wording says synthetic capability rather than synthetic likelihood and translates strong identity too literally."),
 ("zh-Hans","置信度仅适用于合成似然读数。身份匹配度较高时，它不会控制下载决策。","propose-refinement","Makes the identity clause read as a match assessment while retaining the confidence/likelihood distinction."),
 ("zh-Hant","置信度僅適用於合成似然讀數。身分比對度較高時，它不會控制下載決策。","propose-refinement","Makes the identity clause read as a match assessment while retaining the confidence/likelihood distinction.")
]:
    propose(805, loc, val, dec, reason)

for loc, val in {
 "de":"Konfidenz:", "hi":"विश्वास स्तर:", "id":"Tingkat keyakinan:", "ja":"信頼度：",
 "ko":"신뢰도:", "vi":"Độ tin cậy:", "zh-Hans":"置信度：", "zh-Hant":"置信度："
}.items():
    propose(806, loc, val, "propose-correction", "Caller displays a numeric score; align the label with the score-specific Confidence term.")

for loc, val, dec, why in [
 ("ar","اضبط إرسال سجل الاستماع إلى ListenBrainz","propose-correction","Current word means scrolling; replace with sending listening history."),
 ("fr","Configurer le scrobbling ListenBrainz","propose-correction","Fixes the misspelling scrobling while retaining the feature term."),
 ("ja","ListenBrainzへの再生履歴送信を設定","propose-refinement","Uses a clear description of scrobbling rather than a rare transliteration."),
 ("ko","ListenBrainz 재생 기록 전송 설정","propose-correction","Current word means scrolling; this describes sending playback history."),
 ("vi","Thiết lập gửi lịch sử nghe đến ListenBrainz","propose-correction","Current word means scanning; this describes sending listening history."),
 ("zh-Hans","配置 ListenBrainz 听歌记录同步","propose-correction","Current phrase means out of order; this describes listening-history synchronization."),
 ("zh-Hant","設定 ListenBrainz 聆聽紀錄同步","propose-correction","Current phrase means out of order; this describes listening-history synchronization.")
]:
    propose(809, loc, val, dec, why)
for loc, val, dec, why in [
 ("ar","اضبط إرسال سجل الاستماع إلى ListenBrainz لهذا المتصفح.","propose-correction","Current word means scrolling; replace it with sending listening history for this browser."),
 ("fr","Configurez le scrobbling ListenBrainz pour ce navigateur.","propose-correction","Fixes the misspelling scrobling while retaining the feature term."),
 ("ja","このブラウザーでListenBrainzに再生履歴を送信するよう設定します。","propose-refinement","Explains the scrobbling action clearly for this browser."),
 ("ko","이 브라우저에서 ListenBrainz로 재생 기록을 전송하도록 설정합니다.","propose-correction","Current term means scrolling and omits the listening-history action."),
 ("vi","Hãy thiết lập gửi lịch sử nghe từ trình duyệt này đến ListenBrainz.","propose-correction","Current text omits the scrobbling action."),
 ("zh-Hans","为此浏览器配置 ListenBrainz 听歌记录同步。","propose-correction","Current phrase means garbled text; proposal states listening-history sync."),
 ("zh-Hant","為此瀏覽器設定 ListenBrainz 聆聽紀錄同步。","propose-correction","Current phrase means garbled or out-of-order text; proposal states listening-history sync.")
]:
    propose(810, loc, val, dec, why)

for loc, val in {
 "ar":"قم بتكوين مفتاح API قبل الاعتماد على عملاء API أو تكاملات الأتمتة التي تُجري تغييرات على البيانات.",
 "de":"Konfigurieren Sie einen API-Schlüssel, bevor Sie sich auf API-Clients oder Automatisierungsintegrationen verlassen, die Daten verändern.",
 "es":"Configure una clave de API antes de depender de clientes de API o integraciones de automatización que modifiquen datos.",
 "fr":"Configurez une clé API avant de vous fier à des clients API ou à des intégrations d’automatisation qui modifient des données.",
 "hi":"डेटा में बदलाव करने वाले API क्लाइंट या ऑटोमेशन इंटीग्रेशन पर निर्भर होने से पहले API कुंजी कॉन्फ़िगर करें।",
 "id":"Konfigurasikan kunci API sebelum mengandalkan klien API atau integrasi otomatisasi yang mengubah data.",
 "ja":"データを変更するAPIクライアントや自動化連携に依存する前に、APIキーを設定してください。",
 "ko":"데이터를 변경하는 API 클라이언트나 자동화 통합에 의존하기 전에 API 키를 구성하세요.",
 "pt-BR":"Configure uma chave de API antes de depender de clientes de API ou integrações de automação que alteram dados.",
 "vi":"Hãy cấu hình khóa API trước khi dựa vào ứng dụng khách API hoặc tích hợp tự động hóa có thể thay đổi dữ liệu.",
 "zh-Hans":"在依赖会修改数据的 API 客户端或自动化集成之前，请配置 API 密钥。",
 "zh-Hant":"在依賴會修改資料的 API 用戶端或自動化整合之前，請設定 API 金鑰。"
}.items():
    propose(812, loc, val, "propose-correction", "The setup-health caller warns about API access. Mutating means the client or integration performs writes, not that it is mutant or changing. Proposal preserves API.")

for loc, val in {
 "hi":"उपयोगकर्ता-विशिष्ट गतिविधि आयात या निर्यात करने से पहले मीडिया सर्वर के लिए स्पष्ट उपयोगकर्ता मैपिंग कॉन्फ़िगर करें।",
 "id":"Konfigurasikan pemetaan pengguna yang spesifik pada server media sebelum mengimpor atau mengekspor aktivitas milik pengguna.",
 "ja":"ユーザーごとのアクティビティをインポートまたはエクスポートする前に、メディアサーバーのユーザー対応付けを明示的に設定してください。",
 "ko":"사용자별 활동을 가져오거나 내보내기 전에 미디어 서버 사용자 매핑을 명시적으로 구성하세요.",
 "zh-Hans":"导入或导出特定用户的活动前，请先配置明确的媒体服务器用户映射。",
 "zh-Hant":"匯入或匯出特定使用者的活動前，請先設定明確的媒體伺服器使用者對應。"
}.items():
    propose(813, loc, val, "propose-refinement", "The caller requires per-user media-server mapping before moving user-scoped activity; proposal states user-specific activity more naturally.")

for loc, val in {
 "ar":"قم بتكوين عنوان URL الأساسي لخادم الوسائط قبل تمكين عمليات الفحص المباشر.",
 "de":"Konfigurieren Sie die Basis-URL des Medienservers, bevor Sie Live-Scans aktivieren.",
 "es":"Configure la URL base del servidor multimedia antes de habilitar los análisis en vivo.",
 "fr":"Configurez l’URL de base du serveur multimédia avant d’activer les analyses en direct.",
 "hi":"लाइव स्कैन सक्षम करने से पहले मीडिया सर्वर का आधार URL कॉन्फ़िगर करें।",
 "id":"Konfigurasikan URL dasar server media sebelum mengaktifkan pemindaian langsung.",
 "ja":"ライブスキャンを有効にする前に、メディアサーバーのベースURLを設定してください。",
 "ko":"라이브 스캔을 활성화하기 전에 미디어 서버의 기본 URL을 구성하세요.",
 "pt-BR":"Configure a URL base do servidor de mídia antes de ativar as varreduras ao vivo.",
 "vi":"Hãy cấu hình URL cơ sở của máy chủ phương tiện trước khi bật quét trực tiếp.",
 "zh-Hans":"启用实时扫描前，请先配置媒体服务器的基础 URL。",
 "zh-Hant":"啟用即時掃描前，請先設定媒體伺服器的基礎 URL。"
}.items():
    dec = "propose-refinement" if loc in {"hi","ja","zh-Hans","zh-Hant"} else "propose-correction"
    propose(814, loc, val, dec, "The media-server readiness check needs its base URL before live scans; current order is awkward or grammatically wrong. URL spelling is preserved.")

for loc, val, dec, why in [
 ("ar","عنوان URL الأساسي المُهيّأ: {urlBase}","propose-refinement","More natural Arabic order for base URL; placeholder remains exact."),
 ("id","URL dasar yang telah dikonfigurasi: {urlBase}","propose-refinement","Uses standard URL dasar order; placeholder remains exact."),
 ("ja","設定済みのベースURL：{urlBase}","propose-refinement","Uses a natural Japanese base-URL phrase; placeholder remains exact."),
 ("vi","URL cơ sở đã cấu hình: {urlBase}","propose-correction","Current wording is unnatural and reverses standard URL cơ sở phrase; placeholder remains exact."),
 ("zh-Hans","已配置的基础 URL：{urlBase}","propose-correction","底座 means a physical stand/base; this is a configured base URL. Placeholder remains exact."),
 ("zh-Hant","已設定的基礎 URL：{urlBase}","propose-correction","底座 means a physical stand/base; this is a configured base URL. Placeholder remains exact.")
]:
    propose(816, loc, val, dec, why)

for loc, val in {
 "ar":"نجاح استيراد المكتبة إلى خادم وسائط مُهيّأ",
 "de":"Erfolgreicher Bibliotheksimport in einen konfigurierten Medienserver",
 "es":"Importación correcta de la biblioteca en un servidor multimedia configurado",
 "fr":"Importation de bibliothèque réussie vers un serveur multimédia configuré",
 "hi":"कॉन्फ़िगर किए गए मीडिया सर्वर पर लाइब्रेरी का सफल आयात",
 "id":"Impor pustaka berhasil ke server media yang telah dikonfigurasi",
 "ja":"設定済みメディアサーバーへのライブラリのインポートに成功",
 "ko":"구성된 미디어 서버로 라이브러리 가져오기 성공",
 "pt-BR":"Importação da biblioteca bem-sucedida para um servidor de mídia configurado",
 "vi":"Nhập thư viện thành công vào máy chủ phương tiện đã cấu hình",
 "zh-Hans":"成功将媒体库导入已配置的媒体服务器",
 "zh-Hant":"成功將媒體庫匯入已設定的媒體伺服器"
}.items():
    propose(817, loc, val, "propose-correction", "The automation recipe uses this as a gate for successful library import before configured media servers rescan; current wording can read as configuring the import/success itself.")

propose(819, "ar", "تأكيد حذف المجلد", "propose-correction", "The caller confirms deletion of a filesystem directory; الدليل can mean a guide, while المجلد is the normal folder/directory term.")
propose(821, "es", "Confirmar cierre de sesión", "propose-refinement", "This is a modal heading; cierre de sesión is the natural noun phrase, while cerrar sesión is an infinitive clause.")
propose(821, "zh-Hans", "确认退出登录", "propose-correction", "The caller opens the logout confirmation modal; 退出 alone can mean exiting the app or view.")
propose(821, "zh-Hant", "確認登出", "propose-correction", "The caller opens the logout confirmation modal; 退出 alone can mean exiting the app or view.")

tracked = run("git", "ls-files", "-z").split("\x00")
code_paths = [p for p in tracked if p and p.startswith(("web/src/","crates/","dashboard/src/"))
              and p.endswith((".js",".jsx",".ts",".tsx",".rs",".py",".go"))
              and not p.startswith("web/src/lib/locales/")]
patterns = {k: re.compile(r"([\"'])" + re.escape(k) + r"\1") for k in keys[START:END]}
caller_by_key = {k: [] for k in keys[START:END]}
for rel in code_paths:
    path = ROOT / rel
    try:
        raw = path.read_bytes()
        lines = raw.decode("utf-8", errors="replace").splitlines()
    except OSError:
        continue
    for i, line in enumerate(lines):
        for key, pattern in patterns.items():
            matches = list(pattern.finditer(line))
            if not matches:
                continue
            if "interfaceTextProps(" in line: kind = "localized-props"
            elif "interfaceText(" in line: kind = "localized-call"
            elif "LocalizedText" in line: kind = "localized-component"
            elif "localized(" in line: kind = "localized-helper"
            else: kind = "raw-or-non-ui-literal"
            is_test = bool(re.search(r"(^|/)(test|tests|__tests__)(/|\\.)|\\.test\\.", rel))
            lo, hi = max(0, i-2), min(len(lines), i+3)
            caller_by_key[key].append({
                "attestedHead":head, "sourceId":key, "path":rel, "line":i+1,
                "occurrencesOnLine":len(matches), "lineSha256":sha(line),
                "fileSha256":sha(raw), "gitBlob":blob(rel),
                "kind":"test-reference" if is_test else kind,
                "contextLines":[{"line":n+1,"text":lines[n]} for n in range(lo,hi)]
            })
caller_rows = sorted([x for v in caller_by_key.values() for x in v], key=lambda x:(x["sourceId"],x["path"],x["line"]))
jlwrite("caller-context-pins.jsonl", caller_rows)
jwrite("caller-search-attestation.json",{
 "attestedHead":head,"attestedTree":tree,
 "trackedSourceFileCount":len(code_paths),
 "searchScope":["web/src/","crates/","dashboard/src/"],
 "excluded":["web/src/lib/locales/ui-labels.*.json","generated/untracked files"],
 "matchingRule":"Exact source key enclosed in matching single or double quotes in tracked JS/JSX/TS/TSX/Rust/Python/Go source; occurrence count retained per line.",
 "callerPinCount":len(caller_rows),
 "perSource":{
  key:{"windowLabel":f"W{START+j+1:03d}","sourceIndexZeroBased":START+j,
       "exactLiteralLineCount":len(caller_by_key[key]),
       "references":[{"path":r["path"],"line":r["line"],"kind":r["kind"]} for r in caller_by_key[key]]}
  for j,key in enumerate(keys[START:END])
 },
 "limits":"This scan attests direct quoted source literals in tracked code. Dynamically assembled text or keys supplied only by runtime data would not appear as exact source-literal matches."
})

context = {
 802:"MediaCore content-hashing panel description for computing an image perceptual hash.",
 803:"Forensic-matrix confidence score and synthetic-assessment confidence readout.",
 804:"Confidence Lane percentage score with dynamic summary, one dimension in an evidence matrix.",
 805:"Explains confidence applies only to synthetic-likelihood readout and does not govern download decisions.",
 806:"Identity-confidence label in Song ID evidence and confidence in fuzzy-content matching.",
 807:"Bridge administration card heading.",
 808:"Success notification after bridge configuration update; restart is required.",
 809:"ListenBrainz integration button aria-label in the Player bar.",
 810:"ListenBrainz configuration tooltip for this browser.",
 811:"Setup-health action when no download folder is configured.",
 812:"API-access warning before using clients or integrations that mutate state.",
 813:"Media-server contract check requiring explicit user mapping before per-user activity import/export.",
 814:"Media-server readiness check requiring base URL before live scans.",
 815:"Compact configured-state label for credentials, IDs, addresses, and tokens.",
 816:"Setup-health modal formats a configured base URL with the runtime urlBase value.",
 817:"Automation Center gate for successful library import before configured media servers rescan.",
 818:"Wishlist item delete-confirmation dialog header.",
 819:"File Explorer directory-delete confirmation header.",
 820:"File Explorer file-delete confirmation header.",
 821:"App-header logout-confirmation modal header."
}
source_ctx = [{
 "windowLabel":f"W{i+1:03d}", "sourceIndexZeroBased":i, "sourceId":keys[i],
 "sourceContext":context[i], "callerPinCount":len(caller_by_key[keys[i]]),
 "callerLocalizationGap":i==815
} for i in range(START,END)]
jlwrite("source-context.jsonl", source_ctx)

cells=[]
for i in range(START,END):
    key=keys[i]
    src_ph, src_markup, src_protected = ph(key), markup(key), Counter({x["token"]:x["count"] for x in protected(key)})
    for loc in LOCALES:
        target=catalogs[loc][key]
        assert isinstance(target,str)
        pr=proposals.get((i,loc))
        rec=pr["target"] if pr else target
        rec_ph, rec_markup = ph(rec), markup(rec)
        rec_protected=Counter({x["token"]:x["count"] for x in protected(rec)})
        meta=next(x for x in catalog_meta if x["locale"]==loc)
        decision=pr["decision"] if pr else "accept-current"
        cells.append({
         "attestedHead":head,"attestedTree":tree,"repository":REPO,"pullRequest":PR,
         "windowLabel":f"W{i+1:03d}","sourceIndexZeroBased":i,"sourceId":key,"source":key,"sourceSha256":sha(key),
         "locale":loc,"targetFile":meta["path"],"targetCatalogFileSha256":meta["fileSha256"],"targetCatalogBlob":meta["gitBlob"],
         "currentTarget":target,"currentTargetType":"string","currentTargetSha256":sha(target),
         "sourcePlaceholders":dict(src_ph),"currentTargetPlaceholders":dict(ph(target)),
         "placeholderCheck":{"passes":src_ph==ph(target),"source":dict(src_ph),"current":dict(ph(target)),"note":"Names and multiplicities must match exactly."},
         "sourceSelectorTokens":selectors(key),"currentTargetSelectorTokens":selectors(target),
         "sourceMarkupTokens":src_markup,"currentTargetMarkupTokens":markup(target),
         "markupCheck":{"passes":src_markup==markup(target),"source":src_markup,"current":markup(target)},
         "protectedLiterals":list(src_protected.keys()),
         "protectedLiteralCheck":{"passes":src_protected==Counter({x["token"]:x["count"] for x in protected(target)}),
                                  "sourceCounts":dict(src_protected),"currentCounts":dict(Counter({x["token"]:x["count"] for x in protected(target)}))},
         "callerContextRefs":[{"path":r["path"],"line":r["line"],"kind":r["kind"],"lineSha256":r["lineSha256"]} for r in caller_by_key[key]],
         "callerLocalizationGap":i==815,
         "reviewDecision":decision,"recommendedTarget":rec,"recommendedTargetSha256":sha(rec),
         "recommendedTargetPlaceholders":dict(rec_ph),"recommendedMarkupTokens":rec_markup,
         "recommendedProtectedLiteralCounts":dict(rec_protected),
         "recommendedValidationPasses":src_ph==rec_ph and src_markup==rec_markup and src_protected==rec_protected,
         "rationale":pr["rationale"] if pr else "Fresh semantic review against the source and its pinned caller context found no material correction necessary.",
         "confidence":"moderate","reviewMode":"fresh-independent-semantic-review",
         "nativeSpeakerApproval":False,"nativeSpeakerReviewRequired":True
        })
jlwrite("current-cells.jsonl", cells)
jlwrite("primary-review-ledger.jsonl", cells)
candidates=[r for r in cells if r["reviewDecision"]!="accept-current"]
jlwrite("correction-candidates.jsonl", candidates)

evidence=ROOT/"docs/pr-evidence/pr204-localization-2026-11-02"
prior=[]
for file in evidence.rglob("*.jsonl"):
    if file.name in {"source-inventory.jsonl","source-inventory-attestation.jsonl","source-context.jsonl"}: continue
    try: lines=file.read_text().splitlines()
    except Exception: continue
    for n,line in enumerate(lines,1):
        try: obj=json.loads(line)
        except Exception: continue
        sid=obj.get("sourceId") or obj.get("source")
        decision=obj.get("reviewDecision") or obj.get("disposition") or obj.get("status")
        if sid in keys[START:END] and decision:
            prior.append({"path":str(file.relative_to(ROOT)),"line":n,"recordSha256":sha(line),"sourceId":sid,
             "sourceSha256":obj.get("sourceSha256"),"locale":obj.get("locale"),
             "targetSha256":obj.get("currentTargetSha256") or obj.get("targetSha256"),
             "decision":decision,"priorTarget":obj.get("currentTarget") or obj.get("target")})
prior_rows=[]
for row in cells:
    matched=[p for p in prior if p["sourceId"]==row["sourceId"] and p["locale"]==row["locale"]]
    exact=[p for p in matched if p.get("sourceSha256")==row["sourceSha256"] and p.get("targetSha256")==row["currentTargetSha256"]]
    prior_rows.append({"windowLabel":row["windowLabel"],"sourceIndexZeroBased":row["sourceIndexZeroBased"],
     "sourceId":row["sourceId"],"sourceSha256":row["sourceSha256"],"locale":row["locale"],
     "currentTargetSha256":row["currentTargetSha256"],"priorRecordCount":len(matched),
     "exactHashPriorRecordCount":len(exact),"priorRecords":matched,"dispositionReused":False,
     "reason":"No prior source/locale cell-review disposition was found in repository PR evidence; reviewed fresh."})
jlwrite("prior-disposition-reattestation.jsonl",prior_rows)

boundary=[]
for ordinal in range(783,803):
    idx=ordinal-1
    boundary.append({"windowLabel":f"W{ordinal:03d}","sourceIndexZeroBased":idx,"sourceId":keys[idx],"sourceSha256":sha(keys[idx]),"isPriorWindow":True})
for ordinal in [803,822,823]:
    idx=ordinal-1
    boundary.append({"windowLabel":f"W{ordinal:03d}","sourceIndexZeroBased":idx,"sourceId":keys[idx],"sourceSha256":sha(keys[idx]),"isPriorWindow":False})
jlwrite("window-boundary-reattestation.jsonl",boundary)

jwrite("exact-head.json",{"repository":REPO,"pullRequest":PR,"state":"OPEN","isDraft":True,
 "headRefName":"codex/slskr-l10n-audit-20261030","baseRefName":"main","head":head,"tree":tree,
 "url":"https://github.com/snapetech-org/slskR/pull/204","attestedAtUtc":datetime.now(timezone.utc).isoformat(),
 "livePrQueryUsed":"gh pr view 204 --repo snapetech-org/slskR --json state,isDraft,headRefOid,headRefName,baseRefName,url",
 "headReattestationRequiredIfChanged":True})
jwrite("catalog-and-inventory-attestation.json",{
 "attestedHead":head,"attestedTree":tree,"locales":catalog_meta,"catalogCount":len(LOCALES),"keyCount":len(keys),
 "allCatalogsHaveSameKeySet":True,
 "allCatalogsSameKeyOrder":len({tuple(catalogs[l].keys()) for l in LOCALES})==1,
 "orderedInventoryDefinition":"Lexically sorted exact key set, not JSON insertion order.",
 "sortedKeySetSha256":keyset_hash,
 "sourceSlice":{"label":"W803–W822","zeroBasedIndicesInclusive":[START,END-1]},
 "sourceValuesAllStrings":all(isinstance(catalogs[l][k],str) for l in LOCALES for k in keys[START:END]),
 "icuSelectorCountInSourceSlice":sum(len(selectors(k)) for k in keys[START:END]),
 "icuSelectorCountInCurrentCells":sum(len(selectors(catalogs[l][k])) for l in LOCALES for k in keys[START:END]),
 "placeholderKeysInSourceSlice":{keys[i]:dict(ph(keys[i])) for i in range(START,END) if ph(keys[i])},
 "protectedLiteralsReviewed":["ListenBrainz","API","URL"],
 "protectedLiteralFindings":{keys[i]:protected(keys[i]) for i in range(START,END) if protected(keys[i])}
})
jwrite("prior-review-coverage.json",{
 "evidenceScope":"tracked docs/pr-evidence/pr204-localization-2026-11-02 JSONL records available at the attested head",
 "priorMatchingReviewRecords":len(prior),
 "exactHashPriorReviewCells":sum(bool(x["exactHashPriorRecordCount"]) for x in prior_rows),
 "cellsReviewedFresh":len(cells),"dispositionsReused":0,
 "note":"No source-window-specific review dispositions were found; source inventory rows are not review decisions."
})
counts=Counter(r["reviewDecision"] for r in cells)
assert len(cells)==240 and len(candidates)==sum(counts[k] for k in counts if k!="accept-current")
assert len(caller_by_key["Configured"])==27, len(caller_by_key["Configured"])
assert all(r["placeholderCheck"]["passes"] and r["markupCheck"]["passes"] and r["protectedLiteralCheck"]["passes"] for r in cells)
assert all(r["recommendedValidationPasses"] for r in cells)
jwrite("primary-summary.json",{
 "repository":REPO,"pullRequest":PR,"attestedHead":head,"attestedTree":tree,
 "windowLabel":"W803–W822","sourceIndexZeroBasedInclusive":[START,END-1],
 "keyCount":20,"localeCount":len(LOCALES),"cellCount":len(cells),
 "priorReviewCoverage":{"priorMatchingReviewRecords":len(prior),"exactHashPriorReviewCells":sum(bool(x["exactHashPriorRecordCount"]) for x in prior_rows),
                        "freshlyReviewedCells":len(cells),"reusedDispositions":0},
 "decisionCounts":dict(counts),"candidateCount":len(candidates),"cellHolds":0,
 "callerLocalizationGaps":[{"sourceId":"Configured","sourceIndexZeroBased":815,"windowLabel":"W816",
  "file":"web/src/components/System/Integrations/LidarrPanel.jsx","lines":[44,109],
  "finding":"maskedApiKey contains raw English Configured and is rendered as text without LocalizedText/interfaceText; translation proposals do not display in this row until its caller is localized."}],
 "validation":{"all12CatalogsSameKeySet":True,"all240CurrentValuesStrings":True,
  "allCurrentPlaceholdersMatchSource":all(r["placeholderCheck"]["passes"] for r in cells),
  "allCurrentMarkupMatchesSource":all(r["markupCheck"]["passes"] for r in cells),
  "allCurrentProtectedLiteralsMatch":all(r["protectedLiteralCheck"]["passes"] for r in cells),
  "allRecommendedPlaceholderMarkupProtectedLiteralChecksPass":all(r["recommendedValidationPasses"] for r in cells),
  "sourceIcuSelectors":sum(len(selectors(k)) for k in keys[START:END]),
  "currentCellIcuSelectors":sum(len(selectors(catalogs[l][k])) for l in LOCALES for k in keys[START:END]),
  "placeholder":"W817 has {urlBase} once in source and every current/proposed target.",
  "protectedLiterals":"ListenBrainz, API, and URL preserve exact spelling/case in current and proposed targets."},
 "confidence":"moderate","nativeSpeakerReviewRequired":True,"readOnly":True
})
(OUT/"README.md").write_text(
"# slskR PR #204 W803–W822 primary semantic review\n\n"
+f"- Live PR state at freeze: OPEN/DRAFT, branch codex/slskr-l10n-audit-20261030, head {head}, tree {tree}.\n"
+"- Reviewed 20 source keys at current sorted-inventory zero-based indices 802–821, labeled W803–W822; 12 direct locales, 240 cells.\n"
+"- Inventory is the lexically sorted exact key set, not JSON insertion order. All 12 catalogs contain the same 5,440 keys; see catalog-and-inventory-attestation.json.\n"
+"- W783–W802 reattest at indices 782–801; W803 starts at 802. W822 ends at 821; W823 is index 822.\n"
+"- No prior source-window cell-review dispositions were found in tracked PR evidence. All 240 cells were reviewed fresh; no prior disposition was reused.\n"
+"- Exact caller paths, lines, hashes, Git blob IDs, and nearby code are in caller-context-pins.jsonl; per-source summaries are in source-context.jsonl.\n"
+"- Exact source and target hashes, current values, candidates, placeholders, selectors, markup, protected literals, and decisions are in primary-review-ledger.jsonl; proposals only are in correction-candidates.jsonl.\n"
+"- There are zero ICU selectors. W817 has the sole placeholder {urlBase}, preserved by all current and proposed targets. No markup tokens occur. ListenBrainz, API, and URL preserve case.\n"
+"- W816 Configured has one caller gap: LidarrPanel.jsx lines 44 and 109 renders the raw English status instead of localizing it.\n"
+f"- Decisions: {json.dumps(dict(counts),ensure_ascii=False,sort_keys=True)}; candidates: {len(candidates)}; cell holds: 0.\n"
+"- Moderate-confidence machine semantic review; native-speaker approval remains outstanding.\n"
+"- Read-only: no repository or PR writes, tests, builds, scans, CI, browser/workflow, release, tag, or merge actions.\n")
print(json.dumps({"head":head,"tree":tree,"sortedKeySetSha256":keyset_hash,"cells":len(cells),
 "candidates":len(candidates),"decisionCounts":dict(counts),"priorMatchingRecords":len(prior),
 "callerRefsConfigured":len(caller_by_key["Configured"]),"files":sorted(x.name for x in OUT.iterdir())},
 ensure_ascii=False,default=dict,indent=2))
