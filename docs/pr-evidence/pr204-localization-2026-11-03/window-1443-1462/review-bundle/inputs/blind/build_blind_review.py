#!/usr/bin/env python3
import hashlib, json, re, subprocess
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
INPUT = ROOT / "input" / "candidate-free-input"
REVIEW = ROOT / "blind-review"
REPO = Path("/home/keith/Documents/code/task-scratch/slskr-pr204-w1443-1462-source-repo")
HEAD = "44b37bd94385128d5bb5287aa1545901282bdfcb"
TREE = "02c3f149a079c67b010d973dd02ca15776ad1610"
BRANCH = "codex/slskr-l10n-audit-20261030"
LOCALES = ["es","zh-Hans","hi","de","ja","fr","pt-BR","ar","ko","zh-Hant","vi","id"]

def sha(b): return hashlib.sha256(b).hexdigest()
def sha_text(s): return sha(s.encode("utf-8"))
def readj(p): return json.loads(p.read_text(encoding="utf-8"))
def readjl(p): return [json.loads(x) for x in p.read_text(encoding="utf-8").splitlines() if x]
def canon(x): return json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(",",":"))
def tokens(s):
    ph=re.findall(r"\{[A-Za-z][A-Za-z0-9_]*\}",s)
    tags=re.findall(r"<\/?[A-Za-z][^>]*>",s)
    nums=re.findall(r"(?<![A-Za-z])\d+(?:[.,]\d+)?%?(?![A-Za-z])",s)
    prot=[]
    for m in re.finditer(r"(?<![A-Za-z0-9])(?:[A-Z]{2,}[A-Z0-9]*|ffmpeg|Chromaprint|Soulseek|Spotify|YouTube|Pushbullet|Matrix|WebSocket|OpenAI)(?![A-Za-z0-9])",s):
        if m.group(0) not in prot: prot.append(m.group(0))
    return {"placeholders":ph,"markupTags":tags,"numericTokens":nums,"protectedLiterals":prot}

OVERRIDES = {
(1444,"es"):("refinement","Consentimiento explícito para publicar evidencia","The caller marks this as an approval gate and describes an explicit opt-in. This wording makes explicit consent modify the publication decision instead of the evidence itself."),
(1444,"zh-Hans"):("refinement","明确同意发布证据","The caller marks this as an approval gate and describes an explicit opt-in. The current noun stack is unnatural and can read as explicit evidence rather than explicit consent."),
(1444,"hi"):("refinement","साक्ष्य प्रकाशित करने की स्पष्ट सहमति","The caller marks this as an approval gate and describes an explicit opt-in. The current transliterated noun stack is less clear than explicit consent to publish evidence."),
(1444,"ja"):("refinement","証拠公開への明示的なオプトイン","The caller marks this as an approval gate. Reordering the phrase expresses opting in explicitly to evidence publication and reads more naturally."),
(1444,"fr"):("refinement","Consentement explicite à la publication de preuves","The caller marks this as an approval gate and describes an explicit opt-in. This avoids making explicites describe the evidence rather than the consent."),
(1444,"pt-BR"):("refinement","Consentimento explícito para publicar evidências","The caller marks this as an approval gate and describes an explicit opt-in. This makes the explicitness apply to consent, not to the evidence."),
(1444,"ar"):("refinement","موافقة صريحة على نشر الأدلة","The caller marks this as an approval gate and describes an explicit opt-in. This makes explicitness modify consent rather than evidence."),
(1444,"zh-Hant"):("refinement","明確同意發布證據","The caller marks this as an approval gate and describes an explicit opt-in. The current noun stack is unnatural and can read as explicit evidence rather than explicit consent."),
(1444,"vi"):("refinement","Đồng ý rõ ràng cho việc xuất bản bằng chứng","The caller marks this as an approval gate and describes an explicit opt-in. This makes the clear decision apply to consent rather than to the evidence."),
(1444,"id"):("refinement","Persetujuan eksplisit untuk memublikasikan bukti","The caller marks this as an approval gate and describes an explicit opt-in. This makes explicitness modify consent rather than evidence."),
(1447,"zh-Hans"):("refinement","导出 RustyMilk 波形片段","The caller passes the fragment kind wave to the RustyMilk exporter. 波形 identifies a waveform more precisely than the current 波片段."),
(1447,"zh-Hant"):("refinement","匯出 RustyMilk 波形片段","The caller passes the fragment kind wave to the RustyMilk exporter. 波形 identifies a waveform more precisely than the current 波片段."),
(1449,"ar"):("refinement","تصدير الإعداد المسبق النشط لـ RustyMilk","The caller is the action for exporting the active RustyMilk preset. The current placement of مسبقًا reads like previously; this uses the established noun phrase for a preset."),
(1452,"ar"):("refinement","تصدير نص الإعداد المسبق النشط لـ RustyMilk بعد أي تعديلات محلية.","The caller exports the active preset text after local edits. The current participle phrase is awkward; this states that the text belongs to the active preset."),
(1450,"es"):("correction","Exporte las reproducciones locales confirmadas o las valoraciones locales confirmadas al perfil del servidor de medios seleccionado.","The caller is the scrobble-and-rating export description. Clasificaciones suggests classifications or rankings; valoraciones names user ratings, and reproducciones names play events."),
(1450,"zh-Hans"):("correction","将已确认的本地播放记录或评分导回所选媒体服务器配置。","The caller is the scrobble-and-rating export description. 收视率 means audience or viewing ratings; 评分 means user ratings, while 播放记录 names local play history."),
(1450,"hi"):("correction","पुष्टि किए गए स्थानीय प्लेबैक या रेटिंग को चयनित मीडिया सर्वर प्रोफ़ाइल पर वापस निर्यात करें।","The caller is the scrobble-and-rating export description. नाटक means theatrical plays; प्लेबैक refers to local media play events."),
(1450,"fr"):("correction","Exportez les lectures locales confirmées ou les notes locales confirmées vers le profil du serveur multimédia sélectionné.","The caller is the scrobble-and-rating export description. Classements means rankings; notes is the appropriate term for user ratings."),
(1450,"pt-BR"):("correction","Exporte reproduções locais confirmadas ou avaliações locais confirmadas de volta para o perfil do servidor de mídia selecionado.","The caller is the scrobble-and-rating export description. Avaliações clearly denotes user ratings, where classificações can denote categories or classifications."),
(1450,"ar"):("correction","صدّر عمليات التشغيل المحلية المؤكدة أو التقييمات المحلية المؤكدة مرة أخرى إلى ملف تعريف خادم الوسائط المحدد.","The caller is the scrobble-and-rating export description. المسرحيات means theatrical plays; عمليات التشغيل refers to local media play events."),
(1450,"ko"):("correction","확인된 로컬 재생 기록이나 평점을 선택한 미디어 서버 프로필로 다시 내보냅니다.","The caller is the scrobble-and-rating export description. 등급 can mean a grade or content classification; 평점 is a user rating."),
(1450,"zh-Hant"):("correction","將已確認的本機播放紀錄或評分匯回所選媒體伺服器設定檔。","The caller is the scrobble-and-rating export description. 收視率 means audience or viewing ratings; 評分 means user ratings, while 播放紀錄 names local play history."),
(1450,"vi"):("correction","Xuất các lượt phát cục bộ đã xác nhận hoặc các đánh giá cục bộ đã xác nhận trở lại cấu hình máy chủ phương tiện đã chọn.","The caller is the scrobble-and-rating export description. Xếp hạng means ranking; đánh giá names user ratings."),
(1450,"id"):("correction","Ekspor pemutaran lokal yang dikonfirmasi atau penilaian lokal yang dikonfirmasi kembali ke profil server media yang dipilih.","The caller is the scrobble-and-rating export description. Peringkat means rank; penilaian names user ratings."),
(1455,"ar"):("correction","عمليات التصدير والاستيراد وحلّ التعارضات","The caller is the metadata portability statistics panel. In this data-import context, التعارضات means technical conflicts; النزاعات suggests disputes."),
(1456,"zh-Hans"):("correction","可见范围：","The caller displays Hermit, Friends only, Public, or Custom as a federation privacy scope. 接触 means contact; 可见范围 names the visibility scope."),
(1456,"hi"):("correction","दृश्यता:","The caller displays Hermit, Friends only, Public, or Custom as a federation privacy scope. खुलासा means disclosure; दृश्यता names the visibility setting."),
(1456,"de"):("correction","Sichtbarkeit:","The caller displays Hermit, Friends only, Public, or Custom as a federation privacy scope. Belichtung normally means photographic exposure; Sichtbarkeit names visibility."),
(1456,"zh-Hant"):("refinement","可見範圍：","The caller displays Hermit, Friends only, Public, or Custom as a federation privacy scope. 曝露 is understandable as exposure, but 可見範圍 identifies the setting as a visibility scope."),
(1457,"ko"):("correction","확장","The caller places Extended between Core and All releases as a discography scope. 펼친 means opened or spread; 확장 describes the expanded scope."),
(1457,"id"):("correction","Diperluas","The caller places Extended between Core and All releases as a discography scope. Diperpanjang suggests extra time or length; Diperluas describes broader scope."),
(1458,"es"):("correction","ID externo","The caller labels a field where the user enters an external identifier. The source protected literal ID is absent from the current target; retain it verbatim."),
(1458,"hi"):("correction","बाहरी ID","The caller labels a field where the user enters an external identifier. The source protected literal ID is absent from the current target; retain it verbatim."),
(1458,"ar"):("correction","ID خارجي","The caller labels a field where the user enters an external identifier. The source protected literal ID is absent from the current target; retain it verbatim."),
(1459,"hi"):("correction","हल करने के लिए बाहरी ID","The caller labels an external identifier used to look up a ContentID. The source protected literal ID is absent from the current target; retain it verbatim."),
(1459,"ar"):("correction","ID خارجي لمطابقته","The caller labels an external identifier used to look up a ContentID. The current wording loses the protected literal ID and uses an unclear pronoun; retain ID and name the matching action."),
(1460,"es"):("correction","ID externo:","The caller displays the external identifier after a successful lookup. The source protected literal ID is absent from the current target; retain it verbatim."),
(1460,"hi"):("correction","बाहरी ID:","The caller displays the external identifier after a successful lookup. The source protected literal ID is absent from the current target; retain it verbatim."),
(1460,"fr"):("correction","ID externe :","The caller displays the external identifier after a successful lookup. The source protected literal ID is absent from the current target; retain it verbatim."),
(1460,"ar"):("correction","ID خارجي:","The caller displays the external identifier after a successful lookup. The source protected literal ID is absent from the current target; retain it verbatim."),
(1461,"fr"):("correction","Les applications Servarr externes devraient utiliser une clé API à portée limitée, et non une session opérateur.","The caller gives least-privilege API-key guidance. Étendue means extended; à portée limitée conveys a key scoped to a defined permission range."),
(1461,"id"):("correction","Aplikasi Servarr eksternal sebaiknya menggunakan kunci API dengan cakupan terbatas, bukan sesi operator.","The caller gives least-privilege API-key guidance. Dicakup means covered; dengan cakupan terbatas conveys a scoped key and sebaiknya preserves should."),
(1461,"de"):("refinement","Externe Servarr-Apps sollten einen API-Schlüssel mit eingeschränktem Geltungsbereich verwenden, keine Operatorsitzung.","The caller gives least-privilege API-key guidance. Geltungsbereich is a clearer technical term for the intended API scope than bereichsbezogen."),
(1461,"es"):("refinement","Las aplicaciones externas de Servarr deberían usar una clave API de alcance limitado, no una sesión de operador.","The caller gives least-privilege API-key guidance. De alcance limitado states the restricted scope more clearly than con alcance."),
(1461,"vi"):("refinement","Các ứng dụng Servarr bên ngoài nên dùng khóa API có phạm vi giới hạn, không dùng phiên của người vận hành.","The caller gives least-privilege API-key guidance. Có phạm vi giới hạn is more idiomatic and explicit than trong phạm vi for a scoped key."),
(1462,"zh-Hans"):("correction","外部可视化器","The caller is a heading for a launcher that starts RustyMilk or another local audio visualizer. 展示台 means a display stand; 可视化器 names the software tool."),
(1462,"zh-Hant"):("correction","外部視覺化器","The caller is a heading for a launcher that starts RustyMilk or another local audio visualizer. 展示台 means a display stand; 視覺化器 names the software tool."),
(1462,"ar"):("correction","عارض مرئي خارجي","The caller is a heading for a launcher that starts RustyMilk or another local audio visualizer. متخيل means imagined; عارض مرئي names a visual display tool."),
(1462,"vi"):("correction","Trình trực quan hóa bên ngoài","The caller is a heading for a launcher that starts RustyMilk or another local audio visualizer. Trình hiển thị suggests an external display; trực quan hóa names visualization software."),
(1462,"id"):("refinement","Visualisator Eksternal","The caller is a heading for a launcher that starts RustyMilk or another local visualizer. Visualisasi names the activity; Visualisator names the tool."),
}

MEANING = {
1443:"an expiring-soon status label in the publishing panel",
1444:"an approval gate requiring explicit opt-in to evidence publication",
1445:"the metadata export action label",
1446:"an aria label for exporting a RustyMilk shape fragment",
1447:"an aria label for exporting a RustyMilk wave fragment",
1448:"the metadata export success status",
1449:"the action to export the active RustyMilk preset",
1450:"the scrobble and rating export description for a selected media-server profile",
1451:"the description of exporting ContentID metadata into a portable package",
1452:"the tooltip for exporting active RustyMilk preset text after local edits",
1453:"the tooltip for exporting a selected custom RustyMilk shape as a .shape fragment",
1454:"the tooltip for exporting a selected custom RustyMilk wave as a .wave fragment",
1455:"the metadata portability statistics description for export/import conflict handling",
1456:"the federation privacy exposure label followed by Hermit/Friends only/Public/Custom values",
1457:"the Extended option between Core and All releases in a discography scope selector",
1458:"the form label for an external identifier",
1459:"the form label for an external identifier used to find its ContentID",
1460:"the label for the external identifier after a successful lookup",
1461:"least-privilege API-key guidance for external Servarr apps",
1462:"the heading for a launcher of an external audio visualizer"}

def run(cmd,cwd=None): return subprocess.check_output(cmd,cwd=cwd,text=True).strip()
def capture_live(cells,contexts):
    pr=json.loads(run(["gh","pr","view","204","--repo","snapetech-org/slskR","--json","state,isDraft,headRefName,headRefOid,baseRefName,baseRefOid,url"]))
    head=run(["git","-C",str(REPO),"rev-parse","HEAD"]); tree=run(["git","-C",str(REPO),"rev-parse","HEAD^{tree}"])
    status=run(["git","-C",str(REPO),"status","--porcelain=v1"])
    raw=run(["git","-C",str(REPO),"ls-remote","origin",f"refs/heads/{BRANCH}","refs/pull/204/head"])
    refs={line.split("\t",1)[1]:line.split("\t",1)[0] for line in raw.splitlines()}
    catalog_pins=readj(INPUT/"catalog-file-pins.json"); wanted={}
    for entry in catalog_pins["localeCatalogs"].values(): wanted[entry["path"]]=entry
    rt=catalog_pins["localeRuntime"]; wanted[rt["path"]]=rt
    for entry in catalog_pins["callerFiles"].values(): wanted[entry["path"]]=entry
    actual={}
    for path,expected in sorted(wanted.items()):
        data=(REPO/path).read_bytes(); blob=run(["git","-C",str(REPO),"rev-parse",f"HEAD:{path}"])
        got={"path":path,"bytes":len(data),"sha256":sha(data),"gitBlob":blob}
        assert got["bytes"]==expected["byteCount"] and got["sha256"]==expected["sha256"] and got["gitBlob"]==expected["gitBlob"],path
        actual[path]=got
    catalogs={locale:readj(REPO/entry["path"]) for locale,entry in catalog_pins["localeCatalogs"].items()}
    target_hashes=[]
    for cell in cells:
        value=catalogs[cell["locale"]][cell["sourceKey"]]
        assert value==cell["currentTarget"],(cell["position"],cell["locale"])
        target_hashes.append({"position":cell["position"],"locale":cell["locale"],"sourceKeySha256":cell["sourceKeySha256"],"targetSha256":sha_text(value)})
    line_files={}; line_count=0
    for ctx in contexts:
        for caller in ctx["callers"]:
            path=caller["path"]
            if path not in line_files: line_files[path]=(REPO/path).read_text(encoding="utf-8").splitlines()
            for line in caller["context"]:
                text=line_files[path][line["line"]-1]
                assert text==line["text"] and sha_text(text)==line["lineSha256"],(path,line["line"])
                line_count+=1
    assert head==HEAD and tree==TREE and pr["state"]=="OPEN" and pr["isDraft"] is True
    assert pr["headRefName"]==BRANCH and pr["headRefOid"]==HEAD
    assert pr["baseRefOid"]==readj(INPUT/"PR-attestation.json")["baseSha"]
    assert refs=={f"refs/heads/{BRANCH}":HEAD,"refs/pull/204/head":HEAD} and not status
    return {"observedAtUtc":datetime.now(timezone.utc).isoformat(),"repository":"snapetech-org/slskR","pullRequest":204,"state":pr["state"],"draft":pr["isDraft"],"url":pr["url"],"branch":pr["headRefName"],"baseRef":pr["baseRefName"],"baseSha":pr["baseRefOid"],"head":head,"tree":tree,"branchRef":refs[f"refs/heads/{BRANCH}"],"pullRef":refs["refs/pull/204/head"],"checkoutWorktreeClean":True,"sourcePinCount":len(actual),"sourcePins":actual,"all240CatalogTargetsReattested":len(target_hashes)==240,"allCallerContextLinesReattested":line_count,"allCallerContextFilesReattested":len(line_files),"allSelectedTargetsMatchPinnedCatalogs":True,"selectedTargetHashes":target_hashes}

def write_sums(directory,output):
    output.write_text("".join(f"{sha(p.read_bytes())}  {p.relative_to(directory).as_posix()}\n" for p in sorted(x for x in directory.rglob("*") if x.is_file() and x!=output)),encoding="utf-8")

VERIFIER = r'''#!/usr/bin/env python3
import hashlib,json,re,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; REVIEW=ROOT/"blind-review"; INPUT=ROOT/"input"/"candidate-free-input"
def sha(b): return hashlib.sha256(b).hexdigest()
def sha_text(s): return sha(s.encode("utf-8"))
def readj(p): return json.loads(p.read_text(encoding="utf-8"))
def readjl(p): return [json.loads(x) for x in p.read_text(encoding="utf-8").splitlines() if x]
def tokens(s):
 ph=re.findall(r"\{[A-Za-z][A-Za-z0-9_]*\}",s); tags=re.findall(r"<\/?[A-Za-z][^>]*>",s); nums=re.findall(r"(?<![A-Za-z])\d+(?:[.,]\d+)?%?(?![A-Za-z])",s); prot=[]
 for mt in re.finditer(r"(?<![A-Za-z0-9])(?:[A-Z]{2,}[A-Z0-9]*|ffmpeg|Chromaprint|Soulseek|Spotify|YouTube|Pushbullet|Matrix|WebSocket|OpenAI)(?![A-Za-z0-9])",s):
  if mt.group(0) not in prot: prot.append(mt.group(0))
 return {"placeholders":ph,"markupTags":tags,"numericTokens":nums,"protectedLiterals":prot}
def sums(directory,name):
 f=directory/name; entries=[]
 for line in f.read_text(encoding="utf-8").splitlines():
  digest,rel=line.split(None,1); entries.append((rel.lstrip("* "),digest))
 assert len(entries)==len({x for x,_ in entries})
 actual={p.relative_to(directory).as_posix() for p in directory.rglob("*") if p.is_file() and p!=f}
 assert {x for x,_ in entries}==actual
 for rel,d in entries: assert sha((directory/rel).read_bytes())==d,rel
 return len(entries)
root=readj(ROOT/"manifest.json"); inner=readj(REVIEW/"manifest.json"); summary=readj(REVIEW/"review-summary.json")
assert root["head"]==inner["head"]=="44b37bd94385128d5bb5287aa1545901282bdfcb" and root["tree"]==inner["tree"]=="02c3f149a079c67b010d973dd02ca15776ad1610"
assert root["independentBlindReview"] is True and root["primaryReviewAccessed"] is False and root["repositoryOrPRModified"] is False
root_count=sums(ROOT,"SHA256SUMS.txt"); inner_count=sums(REVIEW,"SHA256SUMS.txt")
subprocess.run([sys.executable,str(INPUT/"verify-candidate-free.py")],cwd=INPUT,check=True,stdout=subprocess.DEVNULL)
sums(INPUT,"SHA256SUMS.txt")
cells=readjl(INPUT/"current-target-cells.jsonl"); ledger=readjl(REVIEW/"blind-ledger.jsonl")
assert len(cells)==len(ledger)==240 and len({(r["position"],r["locale"]) for r in ledger})==240
by={(r["position"],r["locale"]):r for r in cells}; counts={}
for row in ledger:
 cur=by[(row["position"],row["locale"])]
 assert row["sourceKey"]==cur["sourceKey"] and row["sourceKeySha256"]==cur["sourceKeySha256"]
 assert row["currentTarget"]==cur["currentTarget"] and row["currentTargetSha256"]==cur["currentTargetSha256"]==sha_text(row["currentTarget"])
 assert row["selectedTargetSha256"]==sha_text(row["selectedTarget"])
 assert row["disposition"] in {"accept-current","correction","refinement","hold"}
 if row["disposition"]=="accept-current": assert row["selectedTarget"]==row["currentTarget"]
 src=tokens(row["sourceKey"]); selected=tokens(row["selectedTarget"])
 assert row["tokenChecks"]["source"]==src and row["tokenChecks"]["selectedTarget"]==selected and row["tokenChecks"]["selectedTargetAllChecksPass"] is True
 for kind in src: assert all(t in selected[kind] for t in src[kind]),(row["position"],row["locale"],kind)
 assert all(x["selectedTargetContainsExactLiteral"] for x in row["manualProtectedLiteralChecks"])
 assert row["callerCount"]==len(row["callerRefs"])>0 and row["callerDisposition"]=="caller-backed; no hold required"
 counts[row["disposition"]]=counts.get(row["disposition"],0)+1
assert counts==summary["dispositionCounts"]==root["dispositionCounts"]==inner["dispositionCounts"]=={"accept-current":190,"correction":31,"refinement":19}
assert summary["selectedTargetTokenFailures"]==root["selectedTargetTokenFailures"]==0
assert summary["baselineProtectedLiteralMismatchCount"]==root["baselineProtectedLiteralMismatchCount"]==9
holds=readjl(REVIEW/"carry-forward-hold-reattestation.jsonl")
assert len(holds)==35 and all(x["disposition"]=="hold" and x["reattestation"]=="same" and x["currentTargetSha256"]==x["priorCurrentTargetSha256"]==sha_text(x["currentTarget"]) for x in holds)
prior=readjl(REVIEW/"prior-selection-reattestation.jsonl")
assert len(prior)==200 and all(x["selectionMatchesCurrentQueue"] and x["priorSourceKey"]==x["currentQueueSourceKey"] and x["priorSourceKeySha256"]==x["currentQueueSourceKeySha256"]==sha_text(x["currentQueueSourceKey"]) for x in prior)
live=readj(REVIEW/"live-head-pin-reattestation.json")
assert live["head"]==live["branchRef"]==live["pullRef"]==root["head"] and live["tree"]==root["tree"]
assert live["state"]=="OPEN" and live["draft"] is True and live["sourcePinCount"]==29
assert live["all240CatalogTargetsReattested"] is True and live["allCallerContextFilesReattested"]==12 and live["allCallerContextLinesReattested"]>0
assert summary["carryForwardHoldsReattested"]==len(holds) and summary["carryForwardHoldFailures"]==0
assert summary["priorSelectedRowsReattested"]==len(prior) and summary["priorSelectionFailures"]==0
print(json.dumps({"result":"PASS","head":root["head"],"tree":root["tree"],"cells":len(ledger),"dispositionCounts":counts,"carryForwardHoldsReattested":len(holds),"priorSelectionsReattested":len(prior),"pinnedSourceFiles":live["sourcePinCount"],"callerContextFiles":live["allCallerContextFilesReattested"],"callerContextLines":live["allCallerContextLinesReattested"],"selectedTokenFailures":0,"baselineProtectedLiteralMismatches":9,"rootChecksumEntries":root_count,"innerChecksumEntries":inner_count},ensure_ascii=False,indent=2))
'''

def build():
    REVIEW.mkdir(parents=True,exist_ok=True)
    input_manifest=readj(INPUT/"manifest.json")
    assert input_manifest["head"]==HEAD and input_manifest["tree"]==TREE
    cells=readjl(INPUT/"current-target-cells.jsonl"); contexts=readjl(INPUT/"source-contexts.jsonl")
    ctx={x["position"]:x for x in contexts}
    assert len(cells)==240 and len(contexts)==20
    ledger=[]; counts=Counter(); perpos=defaultdict(Counter); mismatch_counts=Counter(); literal_checks=0
    for c in cells:
        pos,locale=c["position"],c["locale"]; src=c["sourceKey"]; cur=c["currentTarget"]; cx=ctx[pos]
        assert locale in LOCALES and c["callerCount"]==len(cx["callers"])>0
        disposition,selected,rationale=OVERRIDES.get((pos,locale),("accept-current",cur,"The current wording faithfully conveys "+MEANING[pos]+"; the exact production caller context supports this reading, and the selected target preserves the checked tokens."))
        st,ct,xt=tokens(src),tokens(cur),tokens(selected)
        assert st=={"placeholders":c["sourcePlaceholders"],"markupTags":c["sourceMarkupTags"],"numericTokens":c["sourceNumericTokens"],"protectedLiterals":c["sourceProtectedLiterals"]}
        assert ct=={"placeholders":c["currentTargetPlaceholders"],"markupTags":c["currentTargetMarkupTags"],"numericTokens":c["currentTargetNumericTokens"],"protectedLiterals":c["currentTargetProtectedLiterals"]}
        mm={k:[t for t in st[k] if t not in xt[k]] for k in st}
        for k,v in mm.items():
            if v: mismatch_counts[k]+=1
        manual=[]
        for literal in ("RustyMilk",".shape",".wave"):
            if literal in src:
                ok=literal in selected; manual.append({"literal":literal,"selectedTargetContainsExactLiteral":ok}); literal_checks+=1; assert ok,(pos,locale,literal)
        row={"window":"W1443-W1462","position":pos,"sourceKey":src,"sourceKeySha256":c["sourceKeySha256"],"locale":locale,"catalogPath":c["catalogPath"],"catalogGitBlob":c["catalogGitBlob"],"catalogFileSha256":c["catalogFileSha256"],"callerCount":c["callerCount"],"callerRefs":c["callerRefs"],"callerContextSha256":c["sourceContextSha256"],"sourceMeaningFromCaller":MEANING[pos],"currentTarget":cur,"currentTargetSha256":c["currentTargetSha256"],"selectedTarget":selected,"selectedTargetSha256":sha_text(selected),"disposition":disposition,"rationale":rationale,"tokenChecks":{"source":st,"currentTarget":ct,"selectedTarget":xt,"selectedTargetMismatches":mm,"selectedTargetAllChecksPass":not any(mm.values())},"manualProtectedLiteralChecks":manual,"currentBaselineProtectedLiteralMismatches":c["protectedLiteralMismatchTokens"],"currentBaselineTokenChecks":{"placeholders":c["placeholderSequenceMatches"],"markupTags":c["markupMatches"],"numericTokens":c["numericTokensMatch"],"protectedLiterals":c["protectedLiteralsMatch"]},"callerDisposition":"caller-backed; no hold required","priorHoldReconciliation":"not a carried hold; current source is in this selected window","reviewMode":"independent blind review; primary ledger and summary not accessed"}
        ledger.append(row); counts[disposition]+=1; perpos[pos][disposition]+=1
    assert len(ledger)==240 and len({(x["position"],x["locale"]) for x in ledger})==240 and not mismatch_counts
    assert len(OVERRIDES)==counts["correction"]+counts["refinement"]
    (REVIEW/"blind-ledger.jsonl").write_text("".join(json.dumps(x,ensure_ascii=False,sort_keys=True)+"\n" for x in ledger),encoding="utf-8")
    prior_holds=readjl(INPUT/"prior-hold-reattestation.jsonl"); prior=readjl(INPUT/"prior-selection-reattestation.jsonl")
    assert len(prior_holds)==35 and all(x["reattestation"]=="same" and x["currentTargetSha256"]==x["priorCurrentTargetSha256"]==sha_text(x["currentTarget"]) for x in prior_holds)
    assert len(prior)==200 and all(x["selectionMatchesCurrentQueue"] for x in prior)
    (REVIEW/"carry-forward-hold-reattestation.jsonl").write_bytes((INPUT/"prior-hold-reattestation.jsonl").read_bytes())
    (REVIEW/"prior-selection-reattestation.jsonl").write_bytes((INPUT/"prior-selection-reattestation.jsonl").read_bytes())
    live=capture_live(cells,contexts)
    (REVIEW/"live-head-pin-reattestation.json").write_text(json.dumps(live,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    positions=[]
    for n in range(1443,1463):
        d={"position":n,"sourceKey":ctx[n]["sourceKey"]}; d.update(dict(perpos[n])); positions.append(d)
    summary={"artifact":"slskR PR #204 W1443-W1462 independent blind review","repository":"snapetech-org/slskR","pullRequest":204,"head":HEAD,"tree":TREE,"window":[1443,1462],"sourceCount":20,"localeCount":12,"cellCount":240,"dispositionCounts":dict(counts),"corrections":counts["correction"],"refinements":counts["refinement"],"acceptCurrent":counts["accept-current"],"holds":counts["hold"],"changedTargets":counts["correction"]+counts["refinement"],"selectedTargetTokenMismatchCounts":dict(mismatch_counts),"selectedTargetTokenFailures":0,"manualProtectedLiteralCheckCount":literal_checks,"manualProtectedLiteralFailures":0,"baselineProtectedLiteralMismatchCount":sum(bool(x["protectedLiteralMismatchTokens"]) for x in cells),"baselineProtectedLiteralMismatchCells":[{"position":x["position"],"locale":x["locale"],"sourceKey":x["sourceKey"],"missing":x["protectedLiteralMismatchTokens"]} for x in cells if x["protectedLiteralMismatchTokens"]],"baselinePlaceholderMarkupNumericMismatchCounts":{"placeholders":sum(not x["placeholderSequenceMatches"] for x in cells),"markup":sum(not x["markupMatches"] for x in cells),"numeric":sum(not x["numericTokensMatch"] for x in cells)},"callerlessCurrentPositions":[],"carryForwardHoldsReattested":len(prior_holds),"carryForwardHoldsUnchanged":35,"carryForwardHoldFailures":0,"priorSelectedRowsReattested":len(prior),"priorSelectionFailures":0,"exactCallerFilesReattested":live["allCallerContextFilesReattested"],"exactCallerContextLinesReattested":live["allCallerContextLinesReattested"],"pinnedSourceFileCount":live["sourcePinCount"],"exactBoundaryPositions":{"previous":1442,"first":1443,"last":1462,"next":1463},"nextBoundarySourceKey":readjl(INPUT/"source-window-boundaries.jsonl")[-1]["sourceKey"],"reviewScope":"Review evidence only; no repo, catalog, PR, or workflow files edited; no tests, builds, scans, or CI invoked.","positionSummary":positions}
    (REVIEW/"review-summary.json").write_text(json.dumps(summary,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    (REVIEW/"README.md").write_text("# slskR PR #204 W1443-W1462 independent blind review\n\nPinned to OPEN/DRAFT head "+HEAD+" and tree "+TREE+". This packet contains an independent per-cell ledger for 20 source strings by 12 locales (240 cells), exact caller context, current and selected target hashes, token checks, manual literal checks, and carried-hold reconciliation.\n\nThe reviewer used only the sealed candidate-free input copied under ../input/candidate-free-input/ and the exact-head source checkout. The primary review ledger and summary were not opened. The 35 carried holds remain holds and their current target hashes match the prior hashes. No current selected source is callerless.\n\nCorrections and refinements are proposals in this evidence packet only. No repository, catalog, PR, or workflow files were edited. No tests, builds, scans, or CI were run.\n\nRun python3 verify_blind_review.py from this directory or the packet root to check the evidence and checksums.\n",encoding="utf-8")
    (REVIEW/"verify_blind_review.py").write_text(VERIFIER,encoding="utf-8")
    inner_files=sorted(x for x in REVIEW.iterdir() if x.is_file() and x.name not in {"manifest.json","SHA256SUMS.txt"})
    inner={"artifact":"slskR PR #204 W1443-W1462 blind review ledger","repository":"snapetech-org/slskR","pullRequest":204,"head":HEAD,"tree":TREE,"selectedPositions":[1443,1462],"sourceCount":20,"localeCount":12,"cellCount":240,"dispositionCounts":dict(counts),"carryForwardHoldCount":35,"carryForwardHoldUnchangedCount":35,"priorSelectionReattestationCount":200,"fileHashes":{x.name:{"sha256":sha(x.read_bytes()),"byteCount":x.stat().st_size} for x in inner_files}}
    (REVIEW/"manifest.json").write_text(json.dumps(inner,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8"); write_sums(REVIEW,REVIEW/"SHA256SUMS.txt")
    (ROOT/"README.md").write_text("# slskR PR #204 W1443-W1462 blind review packet\n\nExact-head independent blind review for OPEN/DRAFT PR #204. Expected head/tree: "+HEAD+" / "+TREE+".\n\nThe per-cell ledger is in blind-review/blind-ledger.jsonl. It resolves all 240 cells, including caller-backed target corrections, refinements, exact token checks, and source literal checks. All 35 carried holds are reattested unchanged with exact target hashes; all 200 prior selected rows retain their source-order positions. The next boundary is position 1463.\n\nOnly task evidence was written here. The primary review ledger and summary were not accessed. No PR or repository files were modified, and no tests, builds, scans, CI, browser, or workflow actions were run.\n\nThe copied candidate-free packet is under input/candidate-free-input/. To verify, run python3 blind-review/verify_blind_review.py from this root.\n",encoding="utf-8")
    files=sorted(x for x in ROOT.rglob("*") if x.is_file() and x.name not in {"manifest.json","SHA256SUMS.txt"})
    rootm={"artifact":"slskR PR #204 W1443-W1462 independent blind review evidence","repository":"snapetech-org/slskR","pullRequest":204,"stateAtSeal":live["state"],"draftAtSeal":live["draft"],"head":HEAD,"tree":TREE,"branch":BRANCH,"window":{"previousBoundary":1442,"firstSelected":1443,"lastSelected":1462,"nextBoundary":1463},"sourceCount":20,"localeCount":12,"cellCount":240,"dispositionCounts":dict(counts),"corrections":counts["correction"],"refinements":counts["refinement"],"acceptCurrent":counts["accept-current"],"holds":counts["hold"],"carryForwardHoldsReattested":35,"carryForwardHoldsUnchanged":35,"priorSelectedRowsReattested":200,"selectedTargetTokenFailures":0,"baselineProtectedLiteralMismatchCount":9,"pinnedSourceFileCount":live["sourcePinCount"],"all240CatalogTargetsReattested":live["all240CatalogTargetsReattested"],"allCallerContextLinesReattested":live["allCallerContextLinesReattested"],"candidateFreeInputManifestSha256":sha((INPUT/"manifest.json").read_bytes()),"candidateFreeInputChecksumListSha256":sha((INPUT/"SHA256SUMS.txt").read_bytes()),"independentBlindReview":True,"primaryReviewAccessed":False,"repositoryOrPRModified":False,"fileHashes":{str(x.relative_to(ROOT)):{"sha256":sha(x.read_bytes()),"byteCount":x.stat().st_size} for x in files}}
    (ROOT/"manifest.json").write_text(json.dumps(rootm,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8"); write_sums(ROOT,ROOT/"SHA256SUMS.txt")
    print(json.dumps({"result":"BUILT","head":HEAD,"tree":TREE,"cellCount":240,"dispositionCounts":dict(counts),"carryForwardHoldsReattested":35,"priorSelectionsReattested":200,"pinnedSourceFiles":live["sourcePinCount"],"manualProtectedLiteralChecks":literal_checks,"rootBytes":sum(x.stat().st_size for x in ROOT.rglob("*") if x.is_file())},ensure_ascii=False,indent=2))

if __name__=="__main__": build()

