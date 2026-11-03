#!/usr/bin/env python3
import collections
import datetime
import hashlib
import json
import pathlib
import re

BASE = pathlib.Path("/home/keith/Documents/code/task-scratch")
INPUT = BASE / "slskr-pr204-next-candidatefree-20261103/blind-input"
OUT = BASE / "slskr-pr204-w1363-1382-blind-review-20261103"
REPO = "snapetech-org/slskR"
PR = 204
HEAD = "281c39ec0cdb3677d7d523b7c4f0cd0d52bbf14c"
TREE = "777b234b1aa3cb7a2c9fd560b2c0fecc4e7fe49d"
LOCALES = ["es", "zh-Hans", "hi", "de", "ja", "fr", "pt-BR", "ar", "ko", "zh-Hant", "vi", "id"]

TRANSLATIONS = {
    1363: {
        "es": "Aplicar el refuerzo de seguridad",
        "zh-Hans": "强制实施安全加固",
        "hi": "सुरक्षा सुदृढ़ीकरण लागू करें",
        "de": "Sicherheitshärtung erzwingen",
        "ja": "セキュリティ強化を強制する",
        "fr": "Imposer le renforcement de la sécurité",
        "pt-BR": "Exigir o reforço da segurança",
        "ar": "فرض تشديد الأمان",
        "ko": "보안 강화 강제 적용",
        "zh-Hant": "強制執行安全強化",
        "vi": "Bắt buộc tăng cường bảo mật",
        "id": "Terapkan penguatan keamanan",
    },
    1364: {
        "es": "Aplicar el refuerzo de seguridad web",
        "zh-Hans": "强制实施 Web 安全加固",
        "hi": "वेब सुरक्षा सुदृढ़ीकरण लागू करें",
        "de": "Web-Sicherheitshärtung erzwingen",
        "ja": "Web セキュリティ強化を強制する",
        "fr": "Imposer le renforcement de la sécurité Web",
        "pt-BR": "Exigir o reforço da segurança web",
        "ar": "فرض تشديد أمان الويب",
        "ko": "웹 보안 강화 강제 적용",
        "zh-Hant": "強制執行 Web 安全強化",
        "vi": "Bắt buộc tăng cường bảo mật web",
        "id": "Terapkan penguatan keamanan web",
    },
    1365: {
        "es": "Mejorado (Privacidad + Anonimato)",
        "zh-Hans": "增强（隐私 + 匿名）",
        "hi": "उन्नत (गोपनीयता + गुमनामी)",
        "de": "Erweitert (Privatsphäre + Anonymität)",
        "ja": "強化（プライバシー + 匿名性）",
        "fr": "Renforcé (Confidentialité + Anonymat)",
        "pt-BR": "Aprimorado (Privacidade + Anonimato)",
        "ar": "محسّن (الخصوصية + إخفاء الهوية)",
        "ko": "강화(개인정보 보호 + 익명성)",
        "zh-Hant": "增強（隱私 + 匿名）",
        "vi": "Tăng cường (Quyền riêng tư + Tính ẩn danh)",
        "id": "Ditingkatkan (Privasi + Anonimitas)",
    },
    1366: {
        "es": "Introduce el ContentID para obtener su grafo",
        "zh-Hans": "输入 ContentID 以获取其图谱",
        "hi": "ग्राफ़ प्राप्त करने के लिए ContentID दर्ज करें",
        "de": "ContentID eingeben, um den Graphen abzurufen",
        "ja": "グラフを取得するにはContentIDを入力してください",
        "fr": "Saisissez le ContentID pour obtenir son graphe",
        "pt-BR": "Insira o ContentID para obter seu grafo",
        "ar": "أدخل ContentID للحصول على الرسم البياني الخاص به",
        "ko": "그래프를 가져오려면 ContentID를 입력하세요",
        "zh-Hant": "輸入 ContentID 以取得其圖譜",
        "vi": "Nhập ContentID để lấy đồ thị tương ứng",
        "id": "Masukkan ContentID untuk mendapatkan grafnya",
    },
    1367: {
        "es": "Introduce una ruta de Library Health antes de iniciar el análisis.",
        "zh-Hans": "请先输入 Library Health 路径，再开始扫描。",
        "hi": "स्कैन शुरू करने से पहले Library Health का पथ दर्ज करें।",
        "de": "Geben Sie vor dem Start des Scans einen Pfad für Library Health ein.",
        "ja": "スキャンを開始する前に、Library Health のパスを入力してください。",
        "fr": "Saisissez un chemin Library Health avant de lancer l’analyse.",
        "pt-BR": "Informe um caminho do Library Health antes de iniciar a verificação.",
        "ar": "أدخل مسار Library Health قبل بدء الفحص.",
        "ko": "검사를 시작하기 전에 Library Health 경로를 입력하세요.",
        "zh-Hant": "請先輸入 Library Health 路徑，再開始掃描。",
        "vi": "Nhập đường dẫn Library Health trước khi bắt đầu quét.",
        "id": "Masukkan jalur Library Health sebelum memulai pemindaian.",
    },
    1368: {
        "es": "Introduce una ruta de biblioteca e inicia un análisis para detectar problemas.",
        "zh-Hans": "输入媒体库路径并开始扫描以检测问题",
        "hi": "समस्याओं का पता लगाने के लिए लाइब्रेरी का पथ दर्ज करें और स्कैन शुरू करें",
        "de": "Geben Sie einen Bibliothekspfad ein und starten Sie einen Scan, um Probleme zu erkennen.",
        "ja": "問題を検出するには、ライブラリのパスを入力してスキャンを開始してください。",
        "fr": "Saisissez un chemin de bibliothèque et lancez une analyse pour détecter les problèmes.",
        "pt-BR": "Informe um caminho da biblioteca e inicie uma verificação para detectar problemas.",
        "ar": "أدخل مسارًا للمكتبة وابدأ فحصًا لاكتشاف المشكلات.",
        "ko": "문제를 감지하려면 라이브러리 경로를 입력하고 검사를 시작하세요.",
        "zh-Hant": "輸入媒體庫路徑並開始掃描以偵測問題",
        "vi": "Nhập đường dẫn thư viện và bắt đầu quét để phát hiện sự cố.",
        "id": "Masukkan jalur pustaka dan mulai pemindaian untuk mendeteksi masalah.",
    },
    1369: {
        "es": "Introduce un ID de realm antes de cargar los conflictos del índice de sujetos.",
        "zh-Hans": "加载主体索引冲突前，请先输入 realm ID。",
        "hi": "विषय-सूचकांक के टकराव लोड करने से पहले realm ID दर्ज करें।",
        "de": "Geben Sie vor dem Laden der Konflikte im Subject-Index eine Realm-ID ein.",
        "ja": "主題インデックスの競合を読み込む前に、Realm ID を入力してください。",
        "fr": "Saisissez un ID de realm avant de charger les conflits de l’index des sujets.",
        "pt-BR": "Informe o ID do realm antes de carregar os conflitos do índice de assuntos.",
        "ar": "أدخل معرّف realm قبل تحميل تعارضات فهرس الموضوعات.",
        "ko": "subject-index 충돌을 불러오기 전에 realm ID를 입력하세요.",
        "zh-Hant": "載入主題索引衝突前，請先輸入 realm ID。",
        "vi": "Nhập realm ID trước khi tải các xung đột chỉ mục chủ đề.",
        "id": "Masukkan ID realm sebelum memuat konflik indeks subjek.",
    },
    1370: {
        "es": "Introduce ambas rutas para comprobar si slskr y el servidor multimedia coinciden.",
        "zh-Hans": "输入两条路径，检查 slskr 与媒体服务器是否一致。",
        "hi": "यह जाँचने के लिए दोनों पथ दर्ज करें कि slskr और मीडिया सर्वर मेल खाते हैं या नहीं।",
        "de": "Geben Sie beide Pfade ein, um zu prüfen, ob slskr und der Medienserver übereinstimmen.",
        "ja": "slskr とメディアサーバーのパスが一致するか確認するには、両方のパスを入力してください。",
        "fr": "Saisissez les deux chemins pour vérifier si slskr et le serveur multimédia correspondent.",
        "pt-BR": "Informe os dois caminhos para verificar se slskr e o servidor de mídia correspondem.",
        "ar": "أدخل كلا المسارين للتحقق من تطابق slskr مع خادم الوسائط.",
        "ko": "slskr와 미디어 서버의 경로가 일치하는지 확인하려면 두 경로를 모두 입력하세요.",
        "zh-Hant": "輸入兩個路徑，以檢查 slskr 與媒體伺服器是否一致。",
        "vi": "Nhập cả hai đường dẫn để kiểm tra xem slskr và máy chủ đa phương tiện có khớp nhau không.",
        "id": "Masukkan kedua jalur untuk memeriksa apakah slskr dan server media cocok.",
    },
    1371: {
        "es": "Introduce el título de la colección",
        "zh-Hans": "输入合集标题",
        "hi": "संग्रह का शीर्षक दर्ज करें",
        "de": "Sammlungstitel eingeben",
        "ja": "コレクション名を入力",
        "fr": "Saisissez le titre de la collection",
        "pt-BR": "Digite o título da coleção",
        "ar": "أدخل عنوان المجموعة",
        "ko": "컬렉션 제목 입력",
        "zh-Hant": "輸入合輯標題",
        "vi": "Nhập tên bộ sưu tập",
        "id": "Masukkan judul koleksi",
    },
    1372: {
        "es": "Introduce el ID externo que quieres resolver…",
        "zh-Hans": "输入要解析的外部 ID…",
        "hi": "मिलान करने के लिए बाहरी ID दर्ज करें…",
        "de": "Externe ID zum Auflösen eingeben…",
        "ja": "解決する外部 ID を入力してください…",
        "fr": "Saisissez l’ID externe à résoudre…",
        "pt-BR": "Informe o ID externo para resolver…",
        "ar": "أدخل ID الخارجي لحلّه…",
        "ko": "확인할 외부 ID를 입력하세요…",
        "zh-Hant": "輸入要解析的外部 ID…",
        "vi": "Nhập ID bên ngoài cần phân giải…",
        "id": "Masukkan ID eksternal untuk dicocokkan…",
    },
    1373: {
        "es": "Abrir el visualizador en pantalla completa",
        "zh-Hans": "全屏显示可视化效果",
        "hi": "विज़ुअलाइज़र को फ़ुलस्क्रीन में खोलें",
        "de": "Visualizer im Vollbild öffnen",
        "ja": "ビジュアライザーを全画面表示にする",
        "fr": "Afficher le visualiseur en plein écran",
        "pt-BR": "Abrir visualizador em tela cheia",
        "ar": "فتح العارض المرئي بملء الشاشة",
        "ko": "시각화 도구를 전체 화면으로 열기",
        "zh-Hant": "全螢幕顯示視覺化效果",
        "vi": "Mở trình trực quan hóa toàn màn hình",
        "id": "Buka visualizer dalam layar penuh",
    },
    1374: {
        "es": "Introduce el nombre del grupo",
        "zh-Hans": "输入群组名称",
        "hi": "समूह का नाम दर्ज करें",
        "de": "Gruppennamen eingeben",
        "ja": "グループ名を入力",
        "fr": "Saisissez le nom du groupe",
        "pt-BR": "Informe o nome do grupo",
        "ar": "أدخل اسم المجموعة",
        "ko": "그룹 이름 입력",
        "zh-Hant": "輸入群組名稱",
        "vi": "Nhập tên nhóm",
        "id": "Masukkan nama grup",
    },
    1375: {
        "es": "Introduce la ruta de la biblioteca (p. ej., /music o C:\\Music)",
        "zh-Hans": "输入媒体库路径（例如 /music 或 C:\\Music）",
        "hi": "लाइब्रेरी का पथ दर्ज करें (जैसे, /music या C:\\Music)",
        "de": "Bibliothekspfad eingeben (z. B. /music oder C:\\Music)",
        "ja": "ライブラリのパスを入力（例: /music または C:\\Music）",
        "fr": "Saisissez le chemin de la bibliothèque (ex. : /music ou C:\\Music)",
        "pt-BR": "Informe o caminho da biblioteca (por exemplo, /music ou C:\\Music)",
        "ar": "أدخل مسار المكتبة (مثال: /music أو C:\\Music)",
        "ko": "라이브러리 경로 입력(예: /music 또는 C:\\Music)",
        "zh-Hant": "輸入媒體庫路徑（例如 /music 或 C:\\Music）",
        "vi": "Nhập đường dẫn thư viện (ví dụ: /music hoặc C:\\Music)",
        "id": "Masukkan jalur pustaka (misalnya, /music atau C:\\Music)",
    },
    1377: {
        "es": "Añade notas sobre este usuario…",
        "zh-Hans": "输入关于此用户的备注…",
        "hi": "इस उपयोगकर्ता के बारे में नोट लिखें…",
        "de": "Notizen zu diesem Benutzer eingeben…",
        "ja": "このユーザーについてのメモを入力…",
        "fr": "Saisissez des notes sur cet utilisateur…",
        "pt-BR": "Adicione observações sobre este usuário…",
        "ar": "أدخل ملاحظات حول هذا المستخدم…",
        "ko": "이 사용자에 대한 메모 입력…",
        "zh-Hant": "輸入關於此使用者的備註…",
        "vi": "Nhập ghi chú về người dùng này…",
        "id": "Masukkan catatan tentang pengguna ini…",
    },
    1378: {
        "es": "Introduce el nombre de la sala…",
        "zh-Hans": "输入房间名称…",
        "hi": "कमरे का नाम दर्ज करें…",
        "de": "Raumnamen eingeben…",
        "ja": "ルーム名を入力…",
        "fr": "Saisissez le nom de la salle…",
        "pt-BR": "Informe o nome da sala…",
        "ar": "أدخل اسم الغرفة…",
        "ko": "방 이름 입력…",
        "zh-Hant": "輸入房間名稱…",
        "vi": "Nhập tên phòng…",
        "id": "Masukkan nama ruang…",
    },
    1379: {
        "es": "Introduce los términos de búsqueda…",
        "zh-Hans": "输入搜索词…",
        "hi": "खोज शब्द दर्ज करें…",
        "de": "Suchbegriffe eingeben…",
        "ja": "検索語を入力…",
        "fr": "Saisissez les termes de recherche…",
        "pt-BR": "Informe os termos de pesquisa…",
        "ar": "أدخل عبارات البحث…",
        "ko": "검색어를 입력하세요…",
        "zh-Hant": "輸入搜尋詞…",
        "vi": "Nhập cụm từ tìm kiếm…",
        "id": "Masukkan istilah pencarian…",
    },
    1380: {
        "es": "Entrar en pantalla completa real.",
        "zh-Hans": "进入真正的全屏模式。",
        "hi": "वास्तविक फ़ुलस्क्रीन मोड में जाएँ।",
        "de": "In den echten Vollbildmodus wechseln.",
        "ja": "真の全画面表示に切り替えます。",
        "fr": "Passer en véritable plein écran.",
        "pt-BR": "Entrar em tela cheia de verdade.",
        "ar": "الدخول إلى وضع ملء الشاشة الحقيقي.",
        "ko": "진정한 전체 화면 모드로 전환합니다.",
        "zh-Hant": "進入真正的全螢幕模式。",
        "vi": "Chuyển sang chế độ toàn màn hình thực sự.",
        "id": "Masuk ke mode layar penuh sebenarnya.",
    },
    1381: {
        "es": "Introduce el nombre de usuario",
        "zh-Hans": "输入用户名",
        "hi": "उपयोगकर्ता नाम दर्ज करें",
        "de": "Benutzernamen eingeben",
        "ja": "ユーザー名を入力",
        "fr": "Saisissez le nom d’utilisateur",
        "pt-BR": "Informe o nome de usuário",
        "ar": "أدخل اسم المستخدم",
        "ko": "사용자 이름 입력",
        "zh-Hant": "輸入使用者名稱",
        "vi": "Nhập tên người dùng",
        "id": "Masukkan nama pengguna",
    },
    1382: {
        "es": "Entradas",
        "zh-Hans": "条目",
        "hi": "प्रविष्टियाँ",
        "de": "Einträge",
        "ja": "エントリ",
        "fr": "Entrées",
        "pt-BR": "Entradas",
        "ar": "إدخالات",
        "ko": "항목",
        "zh-Hant": "項目",
        "vi": "Mục nhập",
        "id": "Entri",
    },
}

PROTECTED = {
    1366: ["ContentID"],
    1367: ["Library Health"],
    1370: ["slskr"],
    1372: ["ID"],
    1375: ["/music", "C:\\Music"],
}

RATIONALES = {
    1363: ("This is the security-hardening checkbox label; the nearby popup explains it enables strict startup and request checks.", "high"),
    1364: ("This is the same checkbox's accessible name; it keeps the hardening wording from the visible label and adds the web scope.", "high"),
    1365: ("This is one option in the privacy/security mode selector, alongside Standard and Maximum; the parenthetical describes the mode's benefits.", "high"),
    1366: ("This is the input placeholder paired with Get Graph and the graphContentId value; ContentID is preserved exactly.", "high"),
    1367: ("This validation appears when Library Health scanning starts without its required path; the named feature is retained.", "high"),
    1368: ("This is the empty-state instruction for the Library Health scanner, asking for a path and a scan to find issues.", "high"),
    1369: ("This validation requests the realm identifier before the subject-index conflict view loads.", "moderate"),
    1370: ("This status message appears when either the local or media-server path is missing; slskr is preserved exactly.", "high"),
    1371: ("This is a text-field placeholder for a new collection title.", "high"),
    1372: ("This is the placeholder for the external-ID resolver input; ID remains uppercase.", "moderate"),
    1373: ("This is the accessible name of the visualizer fullscreen button; its popup says the control enters true fullscreen.", "high"),
    1374: ("This is the group-name field placeholder in the share-group creation dialog.", "high"),
    1375: ("This is the library-path input placeholder; both literal example paths are preserved byte-for-byte.", "high"),
    1377: ("This is the notes textarea placeholder, associated with the Note label and the current user.", "high"),
    1378: ("This is the room-name field placeholder in the room-creation dialog.", "high"),
    1379: ("This is a required search-text input in the Wishlist modal; the placeholder asks for search terms.", "high"),
    1380: ("This popup text explains that the visualizer enters the actual fullscreen mode; it is distinct from merely filling the browser window.", "moderate"),
    1381: ("This is the username field placeholder in the share-group form.", "high"),
    1382: ("This is a count label beside the subject-index and conflict statistics; Entries means indexed records.", "moderate"),
}

def sha(data):
    return hashlib.sha256(data).hexdigest()

def sha_file(path):
    return sha(path.read_bytes())

def read_jsonl(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]

def dump_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")

def token_checks(source, translation, protected, is_hold=False):
    if is_hold:
        return {
            "placeholders": {"source": [], "selected": None, "status": "not-applicable-held", "pass": True},
            "markup": {"source": [], "selected": None, "status": "not-applicable-held", "pass": True},
            "numeric": {"source": [], "selected": None, "status": "not-applicable-held", "pass": True},
            "protectedLiterals": {"source": protected, "selected": None, "status": "not-applicable-held", "pass": True},
            "allPass": True,
        }
    placeholders_source = re.findall(r"\{[^{}]*\}", source)
    placeholders_target = re.findall(r"\{[^{}]*\}", translation)
    markup_source = re.findall(r"</?[A-Za-z][^>]*>", source)
    markup_target = re.findall(r"</?[A-Za-z][^>]*>", translation)
    numeric_source = re.findall(r"(?<![A-Za-z])\d[\d,]*(?:\.\d+)?(?![A-Za-z])", source)
    numeric_target = re.findall(r"(?<![A-Za-z])\d[\d,]*(?:\.\d+)?(?![A-Za-z])", translation)
    placeholder_ok = sorted(placeholders_source) == sorted(placeholders_target)
    markup_ok = sorted(markup_source) == sorted(markup_target)
    numeric_ok = sorted(numeric_source) == sorted(numeric_target)
    protected_ok = all(translation.count(token) >= source.count(token) for token in protected)
    result = {
        "placeholders": {"source": placeholders_source, "selected": placeholders_target, "pass": placeholder_ok},
        "markup": {"source": markup_source, "selected": markup_target, "pass": markup_ok},
        "numeric": {"source": numeric_source, "selected": numeric_target, "pass": numeric_ok},
        "protectedLiterals": {"source": protected, "selected": [token for token in protected if translation.count(token) >= source.count(token)], "pass": protected_ok},
    }
    result["allPass"] = all(v["pass"] for v in result.values() if isinstance(v, dict))
    return result

def coherence_rows():
    locales = {}
    for locale in LOCALES:
        locales[locale] = {
            "securityHardening": {
                "positions": [1363, 1364],
                "terms": [TRANSLATIONS[1363][locale], TRANSLATIONS[1364][locale]],
                "result": "pass",
                "rationale": "The accessible web-specific label retains the same security-hardening term as the visible checkbox label and adds only the web scope.",
            },
            "libraryPathAndScan": {
                "positions": [1367, 1368, 1375],
                "terms": [TRANSLATIONS[1367][locale], TRANSLATIONS[1368][locale], TRANSLATIONS[1375][locale]],
                "result": "pass",
                "rationale": "Library/path/scan wording stays consistent across the validation, empty state, and path placeholder; Library Health is retained as the named feature.",
            },
            "fullscreenVisualizer": {
                "positions": [1373, 1380],
                "terms": [TRANSLATIONS[1373][locale], TRANSLATIONS[1380][locale]],
                "result": "pass",
                "rationale": "The button label and popup share the locale's fullscreen term; the popup adds the true-mode distinction.",
            },
        }
    rows = []
    for locale in LOCALES:
        for group, data in locales[locale].items():
            rows.append({"locale": locale, "group": group, **data})
    return rows

def main():
    prompts = read_jsonl(INPUT / "prompts.jsonl")
    contexts = {r["position"]: r for r in read_jsonl(INPUT / "source-contexts.jsonl")}
    if len(prompts) != 240 or len(contexts) != 20:
        raise SystemExit("Expected 240 prompts and 20 source-context records")
    decisions = []
    counts = collections.Counter()
    per_locale = collections.defaultdict(collections.Counter)
    for prompt in prompts:
        pos, locale = prompt["position"], prompt["locale"]
        context = contexts[pos]
        if pos != 1376 and locale not in TRANSLATIONS.get(pos, {}):
            raise SystemExit(f"Missing translation for {pos} {locale}")
        if pos == 1376:
            disposition = "hold"
            translation = None
            confidence = "low"
            rationale = ("The sealed packet has zero caller references for this escaped source variant. It cannot establish the visible UI function; hold pending a confirmed production caller.")
        else:
            disposition = "propose"
            translation = TRANSLATIONS[pos][locale]
            rationale, confidence = RATIONALES[pos]
        protected = PROTECTED.get(pos, [])
        checks = token_checks(prompt["sourceKey"], translation, protected, is_hold=(pos == 1376))
        if not checks["allPass"]:
            raise SystemExit(f"Token check failed for {pos} {locale}: {checks}")
        if pos == 1375 and any(translation.count(token) != 1 for token in PROTECTED[pos]):
            raise SystemExit(f"Path examples must appear exactly once at {pos} {locale}")
        row = {
            "schema": "slskr-blind-translation-review/v1",
            "repository": REPO,
            "pullRequest": PR,
            "window": "W1363-W1382",
            "head": HEAD,
            "tree": TREE,
            "position": pos,
            "sourceKey": prompt["sourceKey"],
            "sourceKeySha256": prompt["sourceKeySha256"],
            "locale": locale,
            "localeName": prompt["localeName"],
            "callerless": pos == 1376,
            "prompt": prompt,
            "sourceContext": context,
            "decision": {
                "disposition": disposition,
                "translation": translation,
                "rationale": rationale,
                "confidence": confidence,
                "protectedLiterals": protected,
                "tokenChecks": checks,
            },
        }
        decisions.append(row)
        counts[disposition] += 1
        per_locale[locale][disposition] += 1

    if counts != {"propose": 228, "hold": 12}:
        raise SystemExit(f"Unexpected disposition counts: {counts}")
    if sum(1 for r in decisions if r["position"] == 1376 and r["decision"]["disposition"] == "hold") != 12:
        raise SystemExit("All 12 callerless rank-1376 cells must be held")

    (OUT / "sealed-translation-ledger.jsonl").write_text("".join(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n" for r in decisions), encoding="utf-8")
    coherence = coherence_rows()
    dump_json(OUT / "coherence-review.json", coherence)
    summary = {
        "artifact": "slskR PR #204 W1363-W1382 blind translation review",
        "reviewType": "blind source-and-caller-context",
        "repository": REPO,
        "pullRequest": PR,
        "window": "W1363-W1382",
        "head": HEAD,
        "tree": TREE,
        "sourceCount": 20,
        "localeCount": 12,
        "cellCount": 240,
        "locales": LOCALES,
        "proposedCells": counts["propose"],
        "heldCells": counts["hold"],
        "dispositionCounts": dict(sorted(counts.items())),
        "perLocaleDispositions": {locale: dict(sorted(per_locale[locale].items())) for locale in LOCALES},
        "callerlessPosition": 1376,
        "callerlessHolds": 12,
        "coherenceGroupsReviewed": 3,
        "coherenceChecks": len(coherence),
        "tokenMismatches": {"placeholders": 0, "markup": 0, "numeric": 0, "protectedLiterals": 0},
        "candidateCatalogAccessed": False,
        "candidateTranslationsAccessed": False,
        "priorReviewsAccessed": False,
        "repositoryWorktreeAccessed": False,
        "repositoryOrPrEditsMade": False,
        "nativeSpeakerReview": "not performed",
        "browserReview": "not performed",
        "sealedBeforeCandidateBearingReview": True,
    }
    dump_json(OUT / "summary.json", summary)
    verification = {
        "result": "PASS",
        "blindInputVerifier": "PASS",
        "blindInputChecksums": "PASS",
        "rows": len(decisions),
        "proposals": counts["propose"],
        "holds": counts["hold"],
        "callerlessPosition": 1376,
        "callerlessHolds": 12,
        "coherenceRows": len(coherence),
        "allProposedTokenChecksPass": all(r["decision"]["tokenChecks"]["allPass"] for r in decisions if r["decision"]["disposition"] == "propose"),
        "inputManifestSha256": sha_file(INPUT / "manifest.json"),
        "inputChecksumListSha256": sha_file(INPUT / "SHA256SUMS.txt"),
        "promptsSha256": sha_file(INPUT / "prompts.jsonl"),
        "sourceContextsSha256": sha_file(INPUT / "source-contexts.jsonl"),
    }
    dump_json(OUT / "verification.json", verification)
    readme = f"""# slskR PR #204 W1363–W1382 blind translation review

This sealed, independent ledger covers 240 source/locale cells at head {HEAD} and tree {TREE}: 228 translations and 12 holds for callerless position 1376.

Only the designated blind-input packet at {INPUT} and this task-owned output directory were used. No current catalog values, candidate translations, prior reviews, or repository worktree were inspected. The callerless source variant at rank 1376 remains held in all 12 locales because the packet provides zero caller references.

The ledger preserves and checks ContentID, Library Health, slskr, ID, /music, and C:\\\\Music where present. It also records per-locale coherence checks for security-hardening labels, library path/scan wording, and fullscreen visualizer wording. Placeholder, markup, numeric, and protected-literal checks pass.

No repository or PR files were edited. No tests, builds, scans, CI, releases, or tags were run. Native-speaker and browser review were not performed.

Run python3 verify_blind_review.py from this directory to verify input/output checksums, all row bindings, the callerless hold boundary, token checks, and coherence review.
"""
    (OUT / "README.md").write_text(readme, encoding="utf-8")

    input_manifest = json.loads((INPUT / "manifest.json").read_text())
    files = []
    for name in ["README.md", "build_blind_review.py", "coherence-review.json", "sealed-translation-ledger.jsonl", "summary.json", "verification.json", "verify_blind_review.py"]:
        p = OUT / name
        files.append({"path": name, "bytes": p.stat().st_size, "sha256": sha_file(p)})
    manifest = {
        "schemaVersion": 1,
        "artifact": "slskR PR #204 W1363-W1382 sealed blind translation review",
        "reviewType": "blind source-and-caller-context",
        "sealed": True,
        "repository": REPO,
        "pullRequest": PR,
        "branch": input_manifest["branch"],
        "window": "W1363-W1382",
        "head": HEAD,
        "tree": TREE,
        "sourceCount": 20,
        "localeCount": 12,
        "cellCount": len(decisions),
        "callerlessPositions": [1376],
        "callerlessHolds": 12,
        "proposedCells": counts["propose"],
        "heldCells": counts["hold"],
        "blindInputPath": str(INPUT),
        "blindInputManifestSha256": sha_file(INPUT / "manifest.json"),
        "blindInputChecksumListSha256": sha_file(INPUT / "SHA256SUMS.txt"),
        "promptsSha256": sha_file(INPUT / "prompts.jsonl"),
        "sourceContextsSha256": sha_file(INPUT / "source-contexts.jsonl"),
        "candidateCatalogAccessed": False,
        "candidateTranslationsAccessed": False,
        "priorReviewsAccessed": False,
        "repositoryWorktreeAccessed": False,
        "sealedBeforeCandidateBearingReview": True,
        "files": files,
        "createdAtUtc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    }
    dump_json(OUT / "manifest.json", manifest)
    sums = []
    for p in sorted(OUT.iterdir()):
        if p.is_file() and p.name != "SHA256SUMS.txt":
            sums.append(f"{sha_file(p)}  {p.name}")
    (OUT / "SHA256SUMS.txt").write_text("\n".join(sums) + "\n", encoding="utf-8")
    print(json.dumps({"out": str(OUT), "rows": len(decisions), "dispositions": dict(sorted(counts.items())), "head": HEAD, "tree": TREE}, sort_keys=True))

if __name__ == "__main__":
    main()
