import collections
import datetime as dt
import hashlib
import json
import re
import subprocess
from pathlib import Path

ROOT = Path("/home/keith/Documents/code/task-worktrees/localization-20261102-slskr")
OUT = Path("/mnt/disks/scratch/task-scratch/slskr-pr204-window-0923-0942-primary-20261102")
PREV = ROOT / "docs/pr-evidence/pr204-localization-2026-11-02/window-0903-0922"
REPO = "snapetech-org/slskR"
PR = 204
BRANCH = "codex/slskr-l10n-audit-20261030"
HEAD_EXPECTED = "ca71c6c90cbe6c1fa9ef0307a57b214e61e022b5"
TREE_EXPECTED = "a35194c508f9b40f28ed75480fc20182a086c55d"
START, END = 922, 941
HOLD_INDEX = 937
LOCALES = ["ar", "de", "es", "fr", "hi", "id", "ja", "ko", "pt-BR", "vi", "zh-Hans", "zh-Hant"]
CONTEXT_TYPE = {
    922: "Player Radio and media-server copy-plan buttons",
    923: "Library Health quarantine packet action button",
    924: "generic Copy Report action used by eight production callers",
    925: "Servarr and Wishlist review action buttons",
    926: "Library Health Safe-Fix manifest action button",
    927: "Library Health replacement search-seed action button",
    928: "Servarr compatibility review action and accessible name",
    929: "SongID forensic matrix copy action and accessible name",
    930: "Wishlist request review packet button and accessible name",
    931: "Discovery Graph branch-report action and description",
    932: "local network-health report action and safety description",
    933: "manual quarantine review packet action and safety description",
    934: "read-only health report action and safety description",
    935: "Experience Settings preference review handoff description",
    936: "Library Health selected-issue action-plan description",
    937: "catalog-only browser-local support-report description with no exact caller",
    938: "Discovery Shelf policy-preview report and no-action description",
    939: "Playlist Intake tag-and-organization dry-run report description",
    940: "Library Health auto-fixable manifest action description",
    941: "Automation Center review-history accessible name",
}
PROTECTED = {928: ["Servarr"], 929: ["SongID", "JSON"], 939: ["ReplayGain"]}
PROPOSALS = {
    (922, "ar"): ("انسخ الخطة", "correction", "The two callers are copy buttons for a generated radio/search plan and a media-server readiness plan. خطة النسخ reads as a copy/backup plan; انسخ الخطة clearly asks the user to copy the plan.", "moderate"),
    (922, "fr"): ("Copier le plan", "correction", "The callers copy a generated plan. Plan de copie reads as a plan for copying; the infinitive Copier is clearer for this button.", "moderate"),
    (922, "ja"): ("プランをコピー", "correction", "The callers copy a plan. コピープラン names a copy plan; をコピー states the button action.", "moderate"),
    (923, "ja"): ("隔離パケットをコピー", "correction", "This Library Health control copies a quarantine review packet. 隔離パケットのコピー is a noun phrase for a copy; をコピー names the action.", "moderate"),
    (925, "ja"): ("レビューをコピー", "correction", "Both callers copy review material: a Servarr compatibility review and a Wishlist request review. 確認 means a check/confirmation; レビュー matches the source and neighboring review headings.", "moderate"),
    (926, "ja"): ("セーフフィックスマニフェストをコピー", "correction", "This is an action button for a Safe-Fix manifest. のコピー reads as a copy of the manifest; をコピー labels the action.", "moderate"),
    (929, "de"): ("Forensische SongID-Matrix JSON kopieren", "correction", "SongID is the exact application feature name and JSON the exact data format. The current Song-ID changes the feature token; retain SongID while keeping the German forensic-matrix wording.", "moderate"),
    (929, "hi"): ("SongID फोरेंसिक मैट्रिक्स JSON कॉपी करें", "correction", "SongID is the application feature name and JSON the exact data format. The current transliterates SongID; preserve the literal feature name in the button label.", "moderate"),
    (930, "ja"): ("ウィッシュリストのリクエストレビューをコピー", "correction", "The caller copies the current Wishlist request review packet. リクエスト確認 can mean request confirmation; リクエストレビュー retains the review meaning and the copy action.", "moderate"),
    (931, "es"): ("Copie un informe de revisión de rama con familias de nodos visibles, familias de aristas, rutas sugeridas y semillas de búsqueda cercanas.", "correction", "The caller is a Discovery Graph branch report. Sucursales suggests business branches and bordes suggests borders; rama and aristas name graph branches and edges.", "moderate"),
    (931, "fr"): ("Copiez un rapport d'examen de branche avec les familles de nœuds visibles, les familles d’arêtes, les itinéraires suggérés et les graines de recherche à proximité.", "correction", "This report describes a graph branch with node and edge families. Tronçons means segments/sections; arêtes is the graph-edge term.", "moderate"),
    (932, "hi"): ("निदान के लिए स्थानीय नेटवर्क-स्वास्थ्य रिपोर्ट की प्रतिलिपि बनाएँ। यह पीयर नोड्स को क्वेरी नहीं करता या नेटवर्क की स्थिति नहीं बदलता।", "correction", "The caller reports local mesh/DHT health, so peers are network nodes. साथियों means companions; पीयर नोड्स matches the catalog's technical network-peer wording.", "moderate"),
    (932, "vi"): ("Sao chép báo cáo tình trạng mạng cục bộ để chẩn đoán. Điều này không truy vấn các nút ngang hàng hoặc thay đổi trạng thái mạng.", "correction", "The caller reports local network health. Đồng nghiệp means colleagues; nút ngang hàng is the established Vietnamese term for network peers elsewhere in this catalog.", "moderate"),
    (933, "es"): ("Copie un paquete de revisión de cuarentena manual para problemas riesgosos seleccionados. Esto no cambia el estado de cuarentena, no mueve archivos, no envía mensajes entre pares ni modifica archivos.", "correction", "The current muta archivos is an unnatural genetics-like rendering of mutate files. The sibling read-only report uses modifica archivos for this same file-safety concept.", "moderate"),
    (933, "fr"): ("Copiez un paquet d'examen de quarantaine manuel pour les problèmes à risque sélectionnés. Cela ne modifie pas l’état de quarantaine, ne déplace pas les fichiers, n’envoie pas de messages aux pairs et ne modifie pas les fichiers.", "correction", "Mute les fichiers does not mean modify files in this tooltip. Use modifie for the final prohibition and make the coordinated no-side-effect list explicit.", "moderate"),
    (933, "hi"): ("चयनित जोखिम भरे मुद्दों के लिए मैन्युअल संगरोध समीक्षा पैकेट की प्रतिलिपि बनाएँ। यह संगरोध स्थिति को नहीं बदलता है, फ़ाइलों को स्थानांतरित नहीं करता है, नेटवर्क पीयर को संदेश नहीं भेजता है, या फ़ाइलों में बदलाव नहीं करता है।", "correction", "म्यूट means mute, not mutate files; the caller also describes a network peer packet. State that no files are changed and no network-peer messages are sent.", "moderate"),
    (933, "id"): ("Salin paket tinjauan karantina manual untuk masalah berisiko tertentu. Ini tidak mengubah status karantina, memindahkan file, mengirim pesan ke peer, atau mengubah file.", "correction", "Memutasi file is an awkward literal/noun form for this no-side-effect promise. Mengubah file clearly says the copied report does not alter files.", "moderate"),
    (933, "pt-BR"): ("Copie um pacote de revisão manual de quarentena para problemas de risco selecionados. Isso não altera o estado de quarentena, não move arquivos, não envia mensagens para pares e não altera arquivos.", "refinement", "The copy-only tooltip lists four prohibited effects. Repeating não makes the negation scope explicit for sending peer messages as well as the other effects.", "moderate"),
    (934, "fr"): ("Copiez un rapport d'intégrité en lecture seule pour un examen hors ligne. Cela ne corrige pas, ne réanalyse pas, ne met pas en quarantaine, ne recherche pas et ne modifie pas les fichiers.", "correction", "Mute les fichiers means mute rather than modify in French. Modifie preserves the source's final no-file-change guarantee.", "moderate"),
    (936, "ar"): ("انسخ خطة عمل المشكلة المحددة للمراجعة. لا ينشئ هذا مهام إصلاح، ولا يضع عمليات البحث في قائمة الانتظار، ولا يعزل الملفات أو يغيرها.", "correction", "The caller only copies the plan. State each prohibited side effect as an action; the current object list can read as creating quarantine files rather than not quarantining files.", "moderate"),
    (936, "de"): ("Kopieren Sie einen Aktionsplan für ein ausgewähltes Problem zur Überprüfung. Dadurch werden keine Korrekturjobs erstellt, keine Suchanfragen in die Warteschlange gestellt, keine Dateien unter Quarantäne gestellt und keine Dateien verändert.", "correction", "The copy-only caller must not queue searches, quarantine files, or mutate files. The current list treats those as objects that are not created; state the prohibited actions directly.", "moderate"),
    (936, "es"): ("Copie un plan de acción para el problema seleccionado para su revisión. Esto no crea trabajos de reparación, no pone búsquedas en cola, no pone archivos en cuarentena ni modifica archivos.", "correction", "Tema means topic/theme rather than selected issue, and the source promises no queued searches, file quarantine, or file mutation. Use problema and explicit action verbs.", "moderate"),
    (936, "fr"): ("Copiez un plan d'action concernant un problème sélectionné pour examen. Cela ne crée pas de tâches de correction, ne met pas de recherches en file d'attente, ne met pas de fichiers en quarantaine et ne modifie pas les fichiers.", "correction", "The current last phrase fichiers de mutation names mutation files rather than saying files are not changed. State the copy-only restrictions as actions.", "moderate"),
    (936, "hi"): ("समीक्षा के लिए चयनित समस्या की कार्य योजना कॉपी करें। यह सुधार कार्य नहीं बनाता, खोजों को कतार में नहीं डालता, फ़ाइलों को क्वारंटाइन नहीं करता और फ़ाइलों में बदलाव नहीं करता।", "correction", "The caller is a review-only action-plan copy. Make the no-job, no-queue, no-quarantine, and no-file-change limits explicit rather than listing quarantine/transformation objects.", "moderate"),
    (936, "id"): ("Salin rencana tindakan untuk masalah yang dipilih agar ditinjau. Tindakan ini tidak membuat tugas remediasi, tidak memasukkan pencarian ke antrean, tidak mengarantina file, dan tidak mengubah file.", "correction", "The source lists prohibited actions, but the current mutasi file is a noun and the other terms are objects of membuat. State the no-quarantine and no-file-change actions directly.", "moderate"),
    (936, "ja"): ("選択した問題のアクションプランをレビュー用にコピーします。これにより、修復ジョブは作成されず、検索がキューに入れられたり、ファイルが隔離されたり変更されたりすることはありません。", "correction", "The current wording says that quarantine/change objects are not created. The caller is copy-only; make clear that searches are not queued and files are not quarantined or changed.", "moderate"),
    (936, "ko"): ("검토를 위해 선택한 문제의 실행 계획을 복사합니다. 이는 복구 작업을 만들거나 검색을 대기열에 추가하거나 파일을 격리하거나 수정하지 않습니다.", "correction", "The current wording says file transformations are not generated. The source guarantees that the button does not queue searches, quarantine files, or change files.", "moderate"),
    (936, "pt-BR"): ("Copie um plano de ação para o problema selecionado para revisão. Isso não cria trabalhos de correção, não coloca buscas na fila, não coloca arquivos em quarentena nem altera arquivos.", "correction", "The current tema means topic/theme, and arquivos modificados describes modified files rather than saying files are not changed. Use problema and direct negative actions.", "moderate"),
    (936, "vi"): ("Sao chép kế hoạch hành động cho vấn đề đã chọn để xem xét. Việc này không tạo công việc khắc phục, không đưa tìm kiếm vào hàng đợi, không cách ly tệp và không thay đổi tệp.", "correction", "The current list nominalizes the quarantine and file-change actions. State that the copy-only tooltip does not queue searches, quarantine files, or change files.", "moderate"),
    (936, "zh-Hans"): ("复制选定问题的行动计划以供审查。这不会创建修复作业、将搜索加入队列、隔离文件或修改文件。", "correction", "The current 变异文件 reads as mutant files rather than a prohibition on changing files. Keep the no-side-effect list in action form.", "moderate"),
    (936, "zh-Hant"): ("複製選定問題的行動計劃以供審查。這不會建立修復作業、將搜尋加入佇列、隔離檔案或修改檔案。", "correction", "The current 變異檔案 reads as mutated files rather than a prohibition on changing files. Keep the no-side-effect list in action form.", "moderate"),
    (938, "ar"): ("انسخ تقريرًا نصيًا لمعاينة سياسة الرف الحالية للمراجعة. لا يطبق هذا أي إجراء.", "correction", "The source is a report-only preview. لا ينطبق على أي إجراء means it is not applicable to an action; لا يطبق أي إجراء means no action is applied.", "moderate"),
    (938, "fr"): ("Copiez un rapport texte de l'aperçu actuel de la politique de conservation pour examen. Cela n'applique aucune action.", "correction", "The source means that the preview does not apply/perform an action. Ne s'applique à aucune action says it is not applicable to any action.", "moderate"),
    (938, "hi"): ("समीक्षा के लिए वर्तमान शेल्फ़ नीति पूर्वावलोकन की टेक्स्ट रिपोर्ट कॉपी करें। यह कोई कार्रवाई लागू नहीं करता।", "correction", "The caller only copies a preview. The current passive phrase means no action applies to it; this wording says no action is applied.", "moderate"),
    (938, "ko"): ("검토를 위해 현재 선반 정책 미리보기 텍스트 보고서를 복사합니다. 이는 어떤 작업도 실행하지 않습니다.", "correction", "The current 적용되지 않습니다 means an action is not applicable. The copy-only tooltip says the preview performs no action.", "moderate"),
    (938, "vi"): ("Sao chép báo cáo văn bản về bản xem trước chính sách của kệ khám phá hiện tại để xem xét. Việc này không thực hiện hành động nào.", "refinement", "This feature is titled Discovery Shelf elsewhere in the same catalog as kệ khám phá; giá commonly reads as price. The caller copies a preview only, so state that no action is performed.", "moderate"),
    (938, "zh-Hans"): ("复制当前探索架策略预览的文本报告以供审阅。这不会执行任何操作。", "correction", "The source says no action is applied; 不适用 means not applicable. 执行任何操作 preserves the no-action promise.", "moderate"),
    (938, "zh-Hant"): ("複製目前探索架策略預覽的文字報告以供審閱。這不會執行任何操作。", "correction", "The source says no action is applied; 不適用 means not applicable. 執行任何操作 preserves the no-action promise.", "moderate"),
    (940, "fr"): ("Copiez un manifeste des problèmes pouvant être corrigés automatiquement pour examen. Cela ne crée pas de tâche de correction, n’exécute pas de correctifs sécurisés et ne modifie pas les fichiers.", "correction", "Auto-réparable suggests that the issue repairs itself, not that the issue can be fixed automatically. The same tooltip also used mute for file mutation; the candidate makes both meanings explicit.", "moderate"),
    (941, "ja"): ("自動化レビュー履歴をコピー", "correction", "This is an Automation Center button. のコピー names a copy of the history; をコピー names the copy action, consistent with the prior Copy History decision.", "moderate"),
    (941, "zh-Hans"): ("复制自动化审核历史记录", "correction", "自动审核 means automatic review, while the caller's section is Automation Center and the source means automation review history. 自动化审核 preserves that distinction.", "moderate"),
    (941, "zh-Hant"): ("複製自動化審查歷史記錄", "correction", "自動審核 can mean automatic review, while the source names Automation Center review history. 自動化審查 preserves the automation concept.", "moderate"),
}
ACCEPT_NOTES = {
    922: "The radio and media-server callers both copy a plan; retained forms read as a plan-copy action in their locale.",
    923: "The caller copies a manual quarantine packet; retained forms preserve the packet/action meaning.",
    924: "Eight production buttons share this generic report action; retained forms remain concise copy-report commands.",
    925: "The callers copy either compatibility-review material or Wishlist request-review material; retained forms preserve the review action.",
    926: "The caller copies a Safe-Fix manifest without running fixes; retained labels name the manifest-copy action.",
    927: "The caller copies replacement search-seed queries without opening Search; retained labels preserve the copy action.",
    928: "The caller copies a local Servarr compatibility report; Servarr remains exact in every retained translation.",
    929: "The caller copies a SongID forensic matrix; JSON and SongID are protected technical literals.",
    930: "The caller copies the current Wishlist request-review packet without starting searches or automation.",
    931: "The caller copies a Discovery Graph branch report; retained forms preserve graph-report and search-seed meanings.",
    932: "The caller copies a local network-health report; retained forms preserve the diagnostic purpose and no-network-state-change limit.",
    933: "The Library Health caller copies a manual quarantine review packet; retained forms preserve its non-mutating role.",
    934: "The Library Health caller copies a read-only report for offline review; retained forms preserve the file-safety warning.",
    935: "The Experience Settings caller copies selected preferences for implementation handoff.",
    936: "The Library Health caller copies a selected-issue action plan; retained safety wording was checked against its review-only caller.",
    937: "No exact production caller exists for this catalog-only string; all locale cells are held.",
    938: "The Player Discovery Shelf caller copies a policy preview and explicitly says it applies no action.",
    939: "The Playlist Intake caller copies the current tag/organization dry-run report; ReplayGain is an exact protected literal.",
    940: "The Library Health caller copies an auto-fixable issue manifest; the action does not execute fixes or mutate files.",
    941: "The Automation Center accessible name describes copying review history; retained forms match this action role.",
}
PLACEHOLDER = re.compile(r"\{([A-Za-z][A-Za-z0-9_]*)\}")
MARKUP = re.compile(r"</?[A-Za-z][^>]*>")
GRAPHQL = """query {
 seerr: repository(owner:"snapetech-org", name:"seerrng") { pullRequest(number:418) { number state isDraft headRefName headRefOid baseRefOid url } }
 chaptarr: repository(owner:"snapetech-org", name:"chaptarrng") { pullRequest(number:190) { number state isDraft headRefName headRefOid baseRefOid url } }
 questarr: repository(owner:"snapetech-org", name:"QuestarrNG") { pullRequest(number:155) { number state isDraft headRefName headRefOid baseRefOid url } }
 romarr: repository(owner:"snapetech-org", name:"ROMarrNG") { pullRequest(number:70) { number state isDraft headRefName headRefOid baseRefOid url } }
 slskr: repository(owner:"snapetech-org", name:"slskr") { pullRequest(number:204) { number state isDraft headRefName headRefOid baseRefOid url } }
 slskdn: repository(owner:"snapetech-org", name:"slskdN") { pullRequest(number:409) { number state isDraft headRefName headRefOid baseRefOid url } }
 torrent: repository(owner:"snapetech-org", name:"TorrentNG") { pullRequest(number:243) { number state isDraft headRefName headRefOid baseRefOid url } }
}"""

def run(args, cwd=ROOT):
    return subprocess.check_output(args, cwd=cwd, text=True, stderr=subprocess.DEVNULL).strip()

def sha(data):
    if isinstance(data, str):
        data = data.encode("utf-8")
    return hashlib.sha256(data).hexdigest()

def canonical(value):
    if isinstance(value, str):
        return value.encode("utf-8")
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")

def sha_target(value):
    return sha(canonical(value))

def text_leaves(value):
    if isinstance(value, str):
        return [value]
    if isinstance(value, dict):
        return [item for sub in value.values() for item in text_leaves(sub)]
    if isinstance(value, list):
        return [item for sub in value for item in text_leaves(sub)]
    return []

def dump_json(name, value):
    (OUT / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")

def dump_jsonl(name, rows):
    (OUT / name).write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows))

def verify_sums(folder):
    result = subprocess.run(["sha256sum", "-c", "SHA256SUMS"], cwd=folder, capture_output=True, text=True)
    return {"path": str(folder / "SHA256SUMS"), "exitCode": result.returncode,
            "verifiedFiles": len([line for line in result.stdout.splitlines() if line.endswith(": OK")]),
            "stderr": result.stderr.strip()}

def terminal(text):
    value = text.rstrip()
    return value[-1] if value and value[-1] in ".?!:：。؟！।" else ""

def punctuation_ok(source, target):
    expected = terminal(source)
    if not expected:
        return True
    allowed = {".": set(".۔。।"), "?": set("?؟？"), "!": set("!！"),
               ":": set(":：;"), "：": set(":：;")}.get(expected, {expected})
    return all(terminal(item) in allowed for item in text_leaves(target))

def formality_note(locale):
    notes = {
        "es": "Spanish tooltip descriptions use formal Copie imperatives; short action labels use infinitive Copiar.",
        "pt-BR": "Brazilian Portuguese descriptions use Copie imperatives; short action labels use infinitive Copiar.",
        "de": "German descriptions may use formal Sie imperatives; short action labels use infinitive-style verb placement.",
        "fr": "French descriptions use vous imperatives; short action labels use infinitive verbs.",
        "hi": "Hindi action wording uses respectful imperatives where the caller is a button.",
        "ja": "Japanese uses polite neutral descriptions; action labels should make copy operations explicit.",
        "ko": "Korean uses polite neutral descriptions; action labels use concise interface wording.",
        "zh-Hans": "Chinese uses neutral UI wording without person or formality marking.",
        "zh-Hant": "Chinese uses neutral UI wording without person or formality marking.",
        "ar": "Arabic uses neutral interface commands or labels without an informal second-person shift.",
        "id": "Indonesian uses neutral direct action wording without an informal second-person shift.",
        "vi": "Vietnamese uses neutral direct action wording without an informal second-person shift.",
    }
    return notes[locale]

OUT.mkdir(parents=True, exist_ok=True)
assert [x.name for x in OUT.iterdir() if x.name != "build_primary.py"] == [], f"task scratch output directory contains unexpected files: {OUT}"

# Capture all seven live PRs in one selection-time GraphQL request.
selection_time = dt.datetime.now(dt.timezone.utc).isoformat()
graphql = json.loads(run(["gh", "api", "graphql", "-f", "query=" + GRAPHQL]))
aliases = [
    ("seerr", "SeerrNG"), ("chaptarr", "chaptarrng"), ("questarr", "QuestarrNG"),
    ("romarr", "ROMarrNG"), ("slskr", "slskR"), ("slskdn", "slskdN"), ("torrent", "TorrentNG"),
]
all_prs = []
for alias, display in aliases:
    p = graphql["data"][alias]["pullRequest"]
    assert p is not None
    all_prs.append({
        "repository": display, "pullRequest": p["number"], "state": p["state"],
        "isDraft": p["isDraft"], "baseRefOid": p["baseRefOid"],
        "headRefName": p["headRefName"], "headRefOid": p["headRefOid"], "url": p["url"],
    })
selected_pr = next(p for p in all_prs if p["repository"] == "slskR")
assert (selected_pr["state"], selected_pr["isDraft"], selected_pr["headRefOid"], selected_pr["headRefName"]) == ("OPEN", True, HEAD_EXPECTED, BRANCH)

# Attest live PR, GitHub tree, remote branch, and clean local worktree.
pr_view = json.loads(run(["gh", "pr", "view", str(PR), "--repo", REPO, "--json", "state,isDraft,headRefOid,headRefName,baseRefOid,url"]))
api_tree = run(["gh", "api", f"repos/{REPO}/commits/{HEAD_EXPECTED}", "--jq", ".commit.tree.sha"])
remote_head = run(["git", "ls-remote", "taskgithub", f"refs/heads/{BRANCH}"]).split()[0]
head = run(["git", "rev-parse", "HEAD"])
tree = run(["git", "rev-parse", "HEAD^{tree}"])
branch = run(["git", "branch", "--show-current"])
worktree_status = run(["git", "status", "--porcelain"])
assert (api_tree, remote_head, head, tree, branch, worktree_status) == (TREE_EXPECTED, HEAD_EXPECTED, HEAD_EXPECTED, TREE_EXPECTED, BRANCH, "")
assert pr_view["headRefOid"] == HEAD_EXPECTED and pr_view["state"] == "OPEN" and pr_view["isDraft"] is True

# Reattest all twelve catalogs and their ordered 5,441-key inventories.
catalogs, catalog_pins = {}, []
shared_keys = None
for locale in LOCALES:
    rel = f"web/src/lib/locales/ui-labels.{locale}.json"
    raw = subprocess.check_output(["git", "show", f"HEAD:{rel}"], cwd=ROOT)
    obj = json.loads(raw)
    keys = sorted(obj)
    if shared_keys is None:
        shared_keys = keys
    assert keys == shared_keys and len(keys) == 5441
    catalogs[locale] = obj
    catalog_pins.append({
        "locale": locale, "path": rel, "blob": run(["git", "rev-parse", f"HEAD:{rel}"]),
        "fileSha256": sha(raw), "keyCount": len(keys),
        "orderedKeysetSha256": sha("\n".join(keys)),
    })
assert len(shared_keys) == 5441 and len(shared_keys[START:END + 1]) == 20

# Verify preceding-window evidence checksums and reattest all 240 final values.
prior_root_sums = verify_sums(PREV)
prior_primary_sums = verify_sums(PREV / "primary")
prior_crossreview_sums = verify_sums(PREV / "crossreview")
assert prior_root_sums["exitCode"] == prior_primary_sums["exitCode"] == prior_crossreview_sums["exitCode"] == 0
prior_manifest = json.loads((PREV / "primary" / "manifest.json").read_text())
assert prior_manifest["window"] == "W903-W922" and prior_manifest["head"] == "b1e814ef11d55fd1710d0e2522df14fee9ff0a70"
prior_primary = [json.loads(line) for line in (PREV / "primary" / "review-ledger.jsonl").read_text().splitlines() if line.strip()]
prior_cross = [json.loads(line) for line in (PREV / "crossreview" / "cross-review-ledger.jsonl").read_text().splitlines() if line.strip()]
prior_readback = [json.loads(line) for line in (PREV / "application" / "full-window-readback.jsonl").read_text().splitlines() if line.strip()]
assert len(prior_primary) == len(prior_cross) == len(prior_readback) == 240
prior_primary_by_cell = {(r["sourceIndex"], r["locale"]): r for r in prior_primary}
prior_cross_by_cell = {(r["sourceIndex"], r["locale"]): r for r in prior_cross}
prior_readback_by_cell = {(r["sourceIndex"], r["locale"]): r for r in prior_readback}
assert len(prior_primary_by_cell) == len(prior_cross_by_cell) == len(prior_readback_by_cell) == 240
prior_disposition_rows = []
for (idx, locale), rb in sorted(prior_readback_by_cell.items()):
    source = shared_keys[idx]
    current = catalogs[locale][source]
    p = prior_primary_by_cell[(idx, locale)]
    x = prior_cross_by_cell[(idx, locale)]
    assert source == rb["sourceId"] == p["sourceId"] == x["sourceId"]
    assert rb["matchesExpected"] is True
    assert rb["actualTarget"] == x["crossReviewTarget"]
    assert rb["actualTargetSha256"] == sha_target(rb["actualTarget"]) == x["crossReviewTargetSha256"]
    assert current == rb["actualTarget"] and sha_target(current) == rb["actualTargetSha256"]
    prior_disposition_rows.append({
        "previousWindow": "W903-W922", "sourceIndex": idx, "windowLabel": idx + 1,
        "sourceId": source, "locale": locale,
        "previousPrimaryDisposition": p["disposition"],
        "previousCrossReviewDisposition": x["crossReviewDisposition"],
        "previousFinalTargetSha256": rb["actualTargetSha256"],
        "currentTargetSha256": sha_target(current),
        "previousReadbackMatchesExpected": True, "matchesCurrentCatalog": True,
    })
prior_hold_rows = [r for r in prior_disposition_rows if r["previousCrossReviewDisposition"] == "hold"]
assert len(prior_disposition_rows) == 240 and len(prior_hold_rows) == 12

# Reattest W922's applied final and the W923 starting values against prior evidence.
prior_boundary_rows = [json.loads(line) for line in (PREV / "primary" / "boundary-pins.jsonl").read_text().splitlines() if line.strip()]
prior_boundary = {(r["sourceIndex"], r["locale"]): r for r in prior_boundary_rows}
assert len(prior_boundary) == 24
prior_w922 = {(r["sourceIndex"], r["locale"]): r for r in prior_readback if r["sourceIndex"] == START - 1}
assert len(prior_w922) == 12
w922_boundary_checks, w923_start_checks = [], []
for locale in LOCALES:
    w922_source = shared_keys[START - 1]
    w922_current = catalogs[locale][w922_source]
    prev_w922 = prior_w922[(START - 1, locale)]
    assert prev_w922["actualTarget"] == w922_current and prev_w922["actualTargetSha256"] == sha_target(w922_current)
    w922_boundary_checks.append({
        "sourceIndex": START - 1, "windowLabel": START, "sourceId": w922_source,
        "locale": locale, "previousDisposition": prev_w922["disposition"],
        "previousFinalTargetSha256": prev_w922["actualTargetSha256"],
        "currentTarget": w922_current, "currentTargetSha256": sha_target(w922_current),
        "matchesPriorW922FinalReadback": True,
    })
    w923_source = shared_keys[START]
    prev_w923 = prior_boundary[(START, locale)]
    w923_current = catalogs[locale][w923_source]
    assert prev_w923["sourceId"] == w923_source and prev_w923["target"] == w923_current
    assert prev_w923["targetSha256"] == sha_target(w923_current)
    w923_start_checks.append({
        "sourceIndex": START, "windowLabel": START + 1, "sourceId": w923_source,
        "locale": locale, "previousPinnedTargetSha256": prev_w923["targetSha256"],
        "currentTarget": w923_current, "currentTargetSha256": sha_target(w923_current),
        "matchesPriorW923FollowingBoundary": True,
    })

# Find exact source-string callers in tracked production JS/JSX/TS/TSX at this head.
tracked = run(["git", "ls-files", "web/src"]).splitlines()
source_files = {}
for rel in tracked:
    if not rel.endswith((".js", ".jsx", ".ts", ".tsx")) or ".test." in rel or "/__tests__/" in rel or "/test/" in rel:
        continue
    raw = (ROOT / rel).read_bytes()
    source_files[rel] = (raw, raw.decode("utf-8").splitlines())
blob_cache = {}
source_callers, caller_gaps = [], []
for index in range(START, END + 1):
    source = shared_keys[index]
    literal = re.compile(r'(["\'])' + re.escape(source) + r'\1')
    hit_count = 0
    for rel, (raw, lines) in source_files.items():
        for line_no, line in enumerate(lines, 1):
            if not literal.search(line):
                continue
            hit_count += 1
            if rel not in blob_cache:
                blob_cache[rel] = run(["git", "rev-parse", f"HEAD:{rel}"])
                assert subprocess.check_output(["git", "show", f"HEAD:{rel}"], cwd=ROOT) == raw
            lo, hi = max(1, line_no - 2), min(len(lines), line_no + 2)
            source_callers.append({
                "sourceIndex": index, "windowLabel": index + 1, "sourceId": source,
                "path": rel, "fileBlob": blob_cache[rel], "fileSha256": sha(raw),
                "line": line_no, "lineSha256": sha(line),
                "contextStartLine": lo,
                "contextLines": [{"line": n, "text": lines[n - 1]} for n in range(lo, hi + 1)],
                "surfaceLine": line.strip(),
            })
    if hit_count == 0:
        caller_gaps.append({
            "sourceIndex": index, "windowLabel": index + 1, "sourceId": source,
            "reason": "No exact source string-literal caller exists in production web/src at this head; the catalog-only entry remains held pending source/caller confirmation.",
            "targetLocales": LOCALES,
        })
assert [g["sourceIndex"] for g in caller_gaps] == [HOLD_INDEX]
assert len({p["sourceIndex"] for p in source_callers}) == 19

# Same-head lexical/context references used for term, peer, and register checks.
same_locale_examples = [
    "Copy a local network-health report for diagnostics. This does not query peers or change network state.",
    "Copy a manual quarantine review packet for selected risky issues. This does not change quarantine state, move files, send peer messages, or mutate files.",
    "Copy a read-only health report for offline review. This does not fix, rescan, quarantine, search, or mutate files.",
    "Copy an auto-fixable issue manifest for review. This does not create a remediation job, execute safe fixes, or mutate files.",
    "Copy a text report of the current shelf policy preview for review. This does not apply any action.",
    "Discovery Shelf", "Copy Report", "Copy Review", "Copy Search Seeds",
    "Copy Servarr compatibility review", "Copy SongID forensic matrix JSON",
    "Tag and organization dry run only; no tag write, cover-art write, ReplayGain run, file move, provider lookup, Soulseek search, peer browse, or download has started.",
]
term_reference_rows = []
for source in same_locale_examples:
    if source not in shared_keys:
        continue
    idx = shared_keys.index(source)
    relation = "same-head terminology or action-register comparison; not prior semantic approval"
    if source == "Discovery Shelf":
        relation = "feature-name spelling used by the shelf policy-preview caller"
    elif "ReplayGain" in source:
        relation = "exact protected algorithm spelling in the same Playlist Intake catalog"
    elif "SongID" in source or "Servarr" in source:
        relation = "exact product-name spelling in the same-head catalog"
    elif source.startswith("Copy "):
        relation = "same-locale copy-action comparison"
    for locale in LOCALES:
        target = catalogs[locale][source]
        term_reference_rows.append({
            "referenceSourceIndex": idx, "sourceId": source, "sourceSha256": sha(source),
            "locale": locale, "target": target, "targetSha256": sha_target(target),
            "relation": relation, "status": "same-head lexical/context reference only; no prior semantic approval is implied",
        })

# Review all 240 cells; record exact source/current/proposal/final hashes and parity.
review_rows, formality_rows = [], []
placeholder_mismatches, markup_mismatches, punctuation_findings = [], [], []
protected_rows, current_protected_failures, final_protected_failures = [], [], []
caller_by_index = collections.defaultdict(list)
for p in source_callers:
    caller_by_index[p["sourceIndex"]].append(f"{p['path']}:{p['line']}")
for index in range(START, END + 1):
    source = shared_keys[index]
    source_placeholders = collections.Counter(PLACEHOLDER.findall(source))
    source_markup = collections.Counter(MARKUP.findall(source))
    for locale in LOCALES:
        current = catalogs[locale][source]
        key = (index, locale)
        if index == HOLD_INDEX:
            disposition, proposal_kind, proposed = "hold", None, None
            rationale = "No exact production source-literal caller exists at this head. Preserve the current translation until the source owner confirms the description is reachable and supplies its intended UI context."
            confidence = "low"
        elif key in PROPOSALS:
            proposed, proposal_kind, rationale, confidence = PROPOSALS[key]
            disposition = proposal_kind
        else:
            proposed, proposal_kind, disposition = None, None, "accept-current"
            rationale = ACCEPT_NOTES[index] + " Current wording is adequate for this locale and UI role; no value change is recommended."
            confidence = "moderate"
        final = proposed if proposed is not None else current
        final_leaves = text_leaves(final)
        current_leaves = text_leaves(current)
        final_placeholder_bad = any(collections.Counter(PLACEHOLDER.findall(x)) != source_placeholders for x in final_leaves)
        current_placeholder_bad = any(collections.Counter(PLACEHOLDER.findall(x)) != source_placeholders for x in current_leaves)
        final_markup_bad = any(collections.Counter(MARKUP.findall(x)) != source_markup for x in final_leaves)
        current_markup_bad = any(collections.Counter(MARKUP.findall(x)) != source_markup for x in current_leaves)
        if current_placeholder_bad or final_placeholder_bad:
            placeholder_mismatches.append({
                "sourceIndex": index, "locale": locale,
                "currentMismatch": current_placeholder_bad, "finalMismatch": final_placeholder_bad,
            })
        if current_markup_bad or final_markup_bad:
            markup_mismatches.append({
                "sourceIndex": index, "locale": locale,
                "currentMismatch": current_markup_bad, "finalMismatch": final_markup_bad,
            })
        punc_ok = punctuation_ok(source, final)
        if not punc_ok:
            punctuation_findings.append({
                "sourceIndex": index, "locale": locale,
                "sourceTerminal": terminal(source),
                "currentTerminals": [terminal(x) for x in current_leaves],
                "finalTerminals": [terminal(x) for x in final_leaves],
            })
        protected = PROTECTED.get(index, [])
        current_missing = [token for token in protected if any(token not in leaf for leaf in current_leaves)]
        final_missing = [token for token in protected if any(token not in leaf for leaf in final_leaves)]
        if current_missing:
            current_protected_failures.append({"sourceIndex": index, "locale": locale, "tokens": current_missing})
        if final_missing:
            final_protected_failures.append({"sourceIndex": index, "locale": locale, "tokens": final_missing})
        protected_rows.append({
            "sourceIndex": index, "windowLabel": index + 1, "sourceId": source, "locale": locale,
            "protectedLiterals": protected, "currentTargetSha256": sha_target(current),
            "currentMissing": current_missing, "finalTargetSha256": sha_target(final),
            "finalMissing": final_missing, "finalProtectedLiteralsPreserved": not bool(final_missing),
        })
        review_rows.append({
            "sourceIndex": index, "windowLabel": index + 1, "sourceId": source,
            "sourceSha256": sha(source), "locale": locale,
            "currentTarget": current, "currentTargetSha256": sha_target(current),
            "disposition": disposition, "proposalKind": proposal_kind,
            "proposedTarget": proposed, "proposedTargetSha256": sha_target(proposed) if proposed is not None else None,
            "reviewedFinal": final, "reviewedFinalSha256": sha_target(final),
            "rationale": rationale, "confidence": confidence,
            "callerReferences": caller_by_index.get(index, []),
            "contextType": CONTEXT_TYPE[index],
            "sourcePlaceholders": sorted(source_placeholders),
            "targetPlaceholderParity": "exact" if not final_placeholder_bad else "mismatch",
            "sourceMarkup": sorted(source_markup),
            "targetMarkupParity": "exact" if not final_markup_bad else "mismatch",
            "protectedLiterals": protected,
            "protectedLiteralsPreserved": not bool(final_missing),
            "punctuationCompatible": punc_ok, "nativeSpeakerApproval": False,
        })
        formality_rows.append({
            "sourceIndex": index, "windowLabel": index + 1, "sourceId": source,
            "locale": locale, "contextType": CONTEXT_TYPE[index],
            "reviewedRegister": "context-appropriate button or description register",
            "informalSecondPersonIntroduced": False,
            "note": formality_note(locale),
        })
assert len(review_rows) == 240
assert not placeholder_mismatches, placeholder_mismatches
assert not markup_mismatches, markup_mismatches
assert not punctuation_findings, punctuation_findings
assert not final_protected_failures, final_protected_failures
assert {(r["sourceIndex"], r["locale"]) for r in current_protected_failures} == {(929, "de"), (929, "hi")}

# Exact current values at the preceding/following catalog boundaries.
boundary_rows = []
for index in (START - 1, END + 1):
    source = shared_keys[index]
    for locale in LOCALES:
        target = catalogs[locale][source]
        boundary_rows.append({
            "sourceIndex": index, "windowLabel": index + 1, "sourceId": source,
            "sourceSha256": sha(source), "locale": locale,
            "target": target, "targetSha256": sha_target(target),
        })
assert len(boundary_rows) == 24 and {r["sourceIndex"] for r in boundary_rows} == {921, 942}
source_window_rows = [
    {"sourceIndex": idx, "windowLabel": idx + 1, "sourceId": shared_keys[idx], "sourceSha256": sha(shared_keys[idx])}
    for idx in range(START - 1, END + 2)
]

# Reattest the final PR head before sealing.
final_pr = json.loads(run(["gh", "pr", "view", str(PR), "--repo", REPO, "--json", "state,isDraft,headRefOid,headRefName,baseRefOid,url"]))
final_tree = run(["gh", "api", f"repos/{REPO}/commits/{HEAD_EXPECTED}", "--jq", ".commit.tree.sha"])
final_remote = run(["git", "ls-remote", "taskgithub", f"refs/heads/{BRANCH}"]).split()[0]
final_status = run(["git", "status", "--porcelain"])
assert (final_pr["headRefOid"], final_tree, final_remote, final_status) == (HEAD_EXPECTED, TREE_EXPECTED, HEAD_EXPECTED, "")

# Write the complete primary packet under task scratch only.
dump_json("all-seven-pr-snapshots.json", {"selectedAtUtc": selection_time, "pullRequests": all_prs})
dump_json("live-head.json", {
    "repository": REPO, "pullRequest": PR, "state": pr_view["state"], "isDraft": pr_view["isDraft"],
    "url": pr_view["url"], "branch": BRANCH, "head": head, "tree": tree, "apiTree": api_tree,
    "remoteHead": remote_head, "worktreeStatus": worktree_status, "baseRefOid": pr_view["baseRefOid"],
    "selectedAtUtc": selection_time,
})
dump_json("final-live-head.json", {
    "repository": REPO, "pullRequest": PR, "state": final_pr["state"], "isDraft": final_pr["isDraft"],
    "head": final_pr["headRefOid"], "tree": final_tree, "remoteHead": final_remote,
    "worktreeStatus": final_status, "reattestedAtUtc": dt.datetime.now(dt.timezone.utc).isoformat(),
})
dump_jsonl("catalog-pins.jsonl", catalog_pins)
dump_jsonl("review-cells.jsonl", review_rows)
dump_jsonl("source-caller-pins.jsonl", source_callers)
dump_jsonl("caller-gaps.jsonl", caller_gaps)
dump_jsonl("boundary-pins.jsonl", boundary_rows)
dump_jsonl("source-window-and-boundaries.jsonl", source_window_rows)
dump_jsonl("locale-formality-checks.jsonl", formality_rows)
dump_jsonl("protected-literal-integrity.jsonl", protected_rows)
dump_jsonl("glossary-reference-pins.jsonl", term_reference_rows)
dump_jsonl("prior-disposition-reattestation.jsonl", prior_disposition_rows)
dump_json("prior-boundary-reattestation.json", {
    "previousWindow": "W903-W922", "previousHead": prior_manifest["head"], "previousTree": prior_manifest["tree"],
    "previousPacketChecksums": [prior_root_sums, prior_primary_sums, prior_crossreview_sums],
    "previousFinalReadbackCellCount": len(prior_disposition_rows),
    "previousFinalReadbackMatchesCurrent": sum(r["matchesCurrentCatalog"] for r in prior_disposition_rows),
    "previousHoldCellCount": len(prior_hold_rows),
    "previousHoldsPreserved": all(r["matchesCurrentCatalog"] for r in prior_hold_rows),
    "w922BoundaryChecks": w922_boundary_checks, "w923StartChecks": w923_start_checks,
    "allChecksPass": True,
})
counts = collections.Counter(r["disposition"] for r in review_rows)
proposal_kinds = collections.Counter(r["proposalKind"] for r in review_rows if r["proposalKind"])
proposed_changes = sum(r["proposedTarget"] is not None and sha_target(r["proposedTarget"]) != r["currentTargetSha256"] for r in review_rows)
dump_json("summary.json", {
    "repository": REPO, "pullRequest": PR, "window": "W923-W942",
    "zeroBasedSourceIndexInclusive": [START, END], "head": head, "tree": tree, "branch": BRANCH,
    "state": pr_view["state"], "isDraft": pr_view["isDraft"],
    "sourceCount": 20, "cellCount": len(review_rows),
    "counts": dict(counts), "proposalKindCounts": dict(proposal_kinds),
    "proposedValueChanges": proposed_changes, "holdCellCount": counts.get("hold", 0),
    "catalogKeyCount": len(shared_keys), "catalogsReattested": len(catalog_pins),
    "callerPins": len(source_callers), "callerFiles": len({r["path"] for r in source_callers}),
    "callerGapSources": len(caller_gaps), "callerGaps": caller_gaps,
    "placeholderMismatches": len(placeholder_mismatches), "markupMismatches": len(markup_mismatches),
    "protectedLiteralCurrentFailureCells": len(current_protected_failures),
    "protectedLiteralFinalFailureCells": len(final_protected_failures),
    "protectedLiteralCurrentFailures": current_protected_failures,
    "punctuationFindings": punctuation_findings,
    "catalogKeysetsIdentical": True, "boundarySourceIndices": [START - 1, END + 1],
    "boundarySourceIds": [shared_keys[START - 1], shared_keys[END + 1]],
    "previousWindow": "W903-W922", "previousWindowCellReadbacksReattested": len(prior_disposition_rows),
    "previousWindowReadbacksMatchingCurrent": sum(r["matchesCurrentCatalog"] for r in prior_disposition_rows),
    "previousHoldsPreserved": len(prior_hold_rows),
    "w922BoundaryAll12Match": all(r["matchesPriorW922FinalReadback"] for r in w922_boundary_checks),
    "w923StartAll12MatchPreviousPin": all(r["matchesPriorW923FollowingBoundary"] for r in w923_start_checks),
    "allSevenPullRequestsAtSelection": all_prs, "selectedAtUtc": selection_time,
    "nativeSpeakerApproval": False, "headedBrowserAcceptance": False,
    "testsBuildScansCiOrBrowserRun": False, "repositoryModified": False,
    "overallConfidence": "moderate",
    "limitations": "Static machine-assisted primary review. It does not establish native-speaker approval, browser acceptance, or runtime validation. One catalog-only source string is held across all locales for lack of an exact production caller.",
    "localeOrder": LOCALES,
})
(OUT / "terminology-sources.md").write_text("""# Terminology and caller context — W923–W942

All terminology checks use exact current-head caller context or same-catalog references; no external glossary or native-speaker authority is claimed.

- W923–W930 are concise copy controls. Caller evidence distinguishes buttons that copy plans, reports, review packets, a manifest, search seeds, a Servarr compatibility report, and the SongID forensic matrix. Same-locale copy-action values are pinned in glossary-reference-pins.jsonl.
- Servarr, SongID, JSON, and ReplayGain are treated as exact protected product or technical literals. The current German and Hindi SongID targets alter the product token; both final proposals preserve it.
- The branch report is an output of Discovery Graph. Current Spanish branch/edge terms and the French edge-family term were compared with that graph caller.
- Peer wording in the local network-health report is checked against the same catalog's network-peer translations.
- The manual quarantine, read-only health, selected-issue action-plan, shelf-policy, dry-run, and auto-fixable-manifest descriptions are attached to copy/preview callers. Their negative clauses were checked as no-side-effect guarantees.
- Discovery Shelf wording is compared with the same-head Discovery Shelf title and its policy-preview caller. The Vietnamese target currently uses giá, which can read as price; the candidate follows the existing kệ khám phá feature term.
- Source “Copy a short report of these browser-local choices to include with a support request.” has no exact source-literal production caller in web/src at this head. All twelve target cells remain held.

All judgments are machine-assisted. Native-speaker approval is false.
""")
(OUT / "README.md").write_text(f"""# slskR PR #204 primary semantic review — W923–W942

Reviewed 20 sorted source IDs × 12 direct locales (240 cells) at exact open/draft PR head {head}, tree {tree}. All twelve catalogs have the same ordered 5,441-key set and their file/blob hashes are pinned. The selection-time GraphQL snapshot covers all seven localization PRs.

Primary dispositions: {dict(counts)}. The 12 held cells are the catalog-only “Copy a short report of these browser-local choices to include with a support request.” source; no exact production source-literal caller exists at this head. The other 19 source IDs have pinned caller context.

The review proposes {proposed_changes} value changes across copy-action labels, graph terminology, network-peer wording, and side-effect guarantees. Two current protected-literal cells alter the SongID name (German Song-ID; Hindi transliteration); both final proposals preserve exact SongID and JSON. ReplayGain and Servarr are preserved. All final targets have exact placeholder and markup parity and compatible terminal punctuation.

The prior W903–W922 evidence checksums pass. All 240 previous final readbacks still match current catalogs, including the 12 held cells. W922 final values and W923 starting values match prior readbacks/pins for all twelve locales. W943 forward-boundary values are pinned.

This is a static machine-assisted primary review packet, with moderate overall confidence. It does not establish native-speaker approval, headed browser acceptance, or runtime validation. No repo files changed; no tests, builds, scans, CI jobs, or browser actions ran.

## Files

- review-cells.jsonl — all 240 source-locale decisions with source/current/proposed/final hashes.
- source-caller-pins.jsonl and caller-gaps.jsonl — exact caller/context pins and the catalog-only gap.
- catalog-pins.jsonl and protected-literal-integrity.jsonl — twelve catalog hashes and per-cell literal checks.
- boundary-pins.jsonl and prior-disposition-reattestation.jsonl — W922/W943 boundaries and previous final dispositions.
- locale-formality-checks.jsonl and glossary-reference-pins.jsonl — register and same-head terminology evidence.
- all-seven-pr-snapshots.json, live-head.json, and final-live-head.json — selection and final head attestations.
- summary.json, prior-boundary-reattestation.json, terminology-sources.md, and manifest.json — review counts, limits, and packet metadata.
- build_primary.py — reproducible packet builder.
- SHA256SUMS — checksums for packet files, including manifest.json.

Native-speaker approval is not claimed; the catalog-only caller gap remains held.
""")

# Manifest excludes itself and SHA256SUMS to avoid a hash cycle.
artifact_files = sorted(p for p in OUT.iterdir() if p.is_file() and p.name not in ("manifest.json", "SHA256SUMS"))
manifest = {
    "repository": REPO, "pullRequest": PR, "window": "W923-W942",
    "zeroBasedSourceIndexInclusive": [START, END], "head": head, "tree": tree, "branch": BRANCH,
    "artifactCountExcludingManifestAndSums": len(artifact_files),
    "artifacts": [{"path": p.name, "bytes": p.stat().st_size, "sha256": sha(p.read_bytes())} for p in artifact_files],
    "summary": {
        "cellCount": len(review_rows), "dispositionCounts": dict(counts),
        "proposalKindCounts": dict(proposal_kinds), "proposedValueChanges": proposed_changes,
        "holdCellCount": counts.get("hold", 0),
    },
}
dump_json("manifest.json", manifest)
checksum_files = sorted(p for p in OUT.rglob("*") if p.is_file() and p.name != "SHA256SUMS")
(OUT / "SHA256SUMS").write_text("".join(f"{sha(p.read_bytes())}  {p.relative_to(OUT).as_posix()}\n" for p in checksum_files))
print(json.dumps({
    "output": str(OUT), "head": head, "tree": tree, "counts": dict(counts),
    "proposalKindCounts": dict(proposal_kinds), "proposedValueChanges": proposed_changes,
    "holds": counts.get("hold", 0), "callerPins": len(source_callers),
    "catalogs": len(catalog_pins), "priorReadbacks": len(prior_disposition_rows),
    "manifestSha256": sha((OUT / "manifest.json").read_bytes()),
    "sha256SumsSha256": sha((OUT / "SHA256SUMS").read_bytes()),
}, ensure_ascii=False))
