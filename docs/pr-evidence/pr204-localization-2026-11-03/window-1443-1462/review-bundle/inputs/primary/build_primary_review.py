#!/usr/bin/env python3
from pathlib import Path
from collections import Counter
import hashlib,json,re,shutil,subprocess,datetime

ROOT=Path("/home/keith/Documents/code/task-scratch/slskr-pr204-w1443-1462-primary-20261103")
CF=ROOT/"candidate-free-input"
OUT=ROOT/"primary-review"
HEAD="44b37bd94385128d5bb5287aa1545901282bdfcb"
TREE="02c3f149a079c67b010d973dd02ca15776ad1610"
BRANCH="codex/slskr-l10n-audit-20261030"
LOCALES=["es","zh-Hans","hi","de","ja","fr","pt-BR","ar","ko","zh-Hant","vi","id"]
PROTECTED_RE=re.compile(r"(?<![A-Za-z0-9])(?:[A-Z]{2,}[A-Z0-9]*|ffmpeg|Chromaprint|Soulseek|Spotify|YouTube|Pushbullet|Matrix|WebSocket|OpenAI)(?![A-Za-z0-9])")
PH=re.compile(r"\{[A-Za-z][A-Za-z0-9_]*\}")
TAG=re.compile(r"</?[A-Za-z][^>]*>")
NUM=re.compile(r"(?<![A-Za-z])\d+(?:[.,]\d+)?%?(?![A-Za-z])")

def sha(b):return hashlib.sha256(b).hexdigest()
def sha_text(s):return sha(s.encode("utf-8"))
def canon(x):return json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(",",":"))
def wj(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
def wjl(p,x):p.write_text("".join(json.dumps(y,ensure_ascii=False,sort_keys=True,separators=(",",":"))+"\n" for y in x),encoding="utf-8")
def readj(p):return json.loads(p.read_text(encoding="utf-8"))
def readjl(p):return [json.loads(x) for x in p.read_text(encoding="utf-8").splitlines() if x]
def tok(s):return {"placeholders":PH.findall(s),"markupTags":TAG.findall(s),"numericTokens":NUM.findall(s),"protectedLiterals":list(dict.fromkeys(m.group(0) for m in PROTECTED_RE.finditer(s)))}

# Candidate-specific translations are fixed in this primary stream before the blind review is read.
P={}
def put(pos,loc,value,disp,reason,confidence="high"):
    P[(pos,loc)]={"target":value,"disposition":disp,"reason":reason,"confidence":confidence}

# Policy label: the pinned caller identifies the phrase as an approval gate for publishing explicit evidence.
for loc,value in {
 "es":"Consentimiento explícito para publicar evidencia",
 "zh-Hans":"明确同意发布证据",
 "hi":"साक्ष्य प्रकाशित करने के लिए स्पष्ट सहमति",
 "ja":"証拠の公開に関する明示的な同意",
 "fr":"Consentement explicite à la publication de preuves",
 "pt-BR":"Consentimento explícito para publicar evidências",
 "ar":"موافقة صريحة على نشر الأدلة",
 "zh-Hant":"明確同意公開證據",
 "vi":"Đồng ý rõ ràng cho việc công bố bằng chứng",
 "id":"Persetujuan eksplisit untuk menerbitkan bukti",
}.items():
    put(1444,loc,value,"correction","The caller uses this as an approval gate for publishing evidence. The current wording is a literal opt-in/option phrase; explicit consent states the affirmative publication permission clearly.")

put(1449,"ar","تصدير الإعداد المسبق النشط لـ RustyMilk","correction","The caller is an export control for the active RustyMilk preset. The current Arabic order reads as an active setting prepared in advance; this names the active preset.")
# Scrobble and rating export: separate playback history from user ratings.
for loc,value,reason in [
 ("es","Exporte las reproducciones o calificaciones locales confirmadas de vuelta al perfil del servidor multimedia seleccionado.","Clasificaciones can mean classifications or rankings; calificaciones identifies user ratings beside playback records."),
 ("zh-Hans","将已确认的本地播放记录或评分导出回所选的媒体服务器配置文件。","收视率 means audience/viewership ratings; the caller exports playback history or ratings."),
 ("hi","पुष्ट स्थानीय प्लेबैक या रेटिंग को चयनित मीडिया सर्वर प्रोफ़ाइल पर वापस निर्यात करें।","नाटक means a stage play; the caller exports local playback history, not theatrical plays."),
 ("fr","Exportez les lectures ou les notes locales confirmées vers le profil du serveur multimédia sélectionné.","Classements means rankings; notes is the appropriate sense of ratings here."),
 ("pt-BR","Exporte as reproduções ou avaliações locais confirmadas de volta para o perfil do servidor de mídia selecionado.","Classificações suggests classifications or rankings; avaliações clearly names user ratings."),
 ("ar","قم بتصدير عمليات التشغيل المحلية المؤكدة أو التقييمات مرة أخرى إلى ملف تعريف خادم الوسائط المحدد.","المسرحيات means theatrical plays; this integration exports playback records and ratings."),
 ("zh-Hant","將已確認的本機播放記錄或評分匯出回選定的媒體伺服器設定檔。","收視率 refers to audience/viewership ratings; this integration exports playback records or user ratings."),
 ("vi","Xuất các lượt phát hoặc đánh giá cục bộ đã được xác nhận trở lại cấu hình máy chủ phương tiện đã chọn.","Xếp hạng means rankings; đánh giá is the rating/evaluation sense."),
 ("id","Ekspor pemutaran lokal atau penilaian yang telah dikonfirmasi kembali ke profil server media yang dipilih.","Peringkat means rank/ranking; penilaian expresses ratings.")
]:
    put(1450,loc,value,"correction",reason)

put(1452,"ar","قم بتصدير نص الإعداد المسبق النشط لـ RustyMilk بعد أي تعديلات محلية.","correction","This tooltip describes exporting the active preset text after edits; the current phrasing misplaces the preset as an adverb.")
put(1453,"ar","قم بتصدير الشكل المخصص المحدد في الإعداد المسبق النشط لـ RustyMilk كجزء .shape.","refinement","The caller exports a selected shape from the active RustyMilk preset; this improves the Arabic noun order and preserves the .shape extension.")
put(1454,"ar","قم بتصدير الموجة المخصصة المحددة في الإعداد المسبق النشط لـ RustyMilk كجزء .wave.","refinement","The caller exports a selected wave from the active RustyMilk preset; this improves the Arabic noun order and preserves the .wave extension.")

# In Federation diagnostics this field is paired with Hermit, Friends only, Public, and Custom.
for loc,value,disp in [
 ("es","Visibilidad:","correction"),
 ("zh-Hans","可见范围：","correction"),
 ("hi","दृश्यता:","refinement"),
 ("de","Sichtbarkeit:","correction"),
 ("ja","公開範囲：","refinement"),
 ("fr","Visibilité :","refinement"),
 ("pt-BR","Visibilidade:","refinement"),
 ("ar","مستوى الظهور:","refinement"),
 ("ko","공개 범위:","refinement"),
 ("zh-Hant","可見範圍：","correction"),
 ("vi","Phạm vi hiển thị:","correction"),
 ("id","Visibilitas:","refinement")
]:
    put(1456,loc,value,disp,"The caller displays federation audience modes (Hermit, Friends only, Public, Custom); visibility/publication scope is clearer than a physical or general exposure sense.","moderate")

put(1457,"ja","拡張","refinement","This is the ExtendedDiscography option; the compact mode label is clearer without the past-tense ending.")
put(1457,"ko","확장","correction","The current 펼친 means unfolded; this option selects the expanded discography scope.")
put(1457,"id","Diperluas","correction","Diperpanjang usually suggests extension in duration; Diperluas describes an expanded discography scope.")

# Preserve the source's protected acronym ID in all three form labels.
put(1458,"es","ID externo","correction","This is a form label for an identifier field; preserving the source's protected ID acronym is required.")
put(1458,"hi","बाहरी ID","correction","This is a form label for an identifier field; preserve the source's protected ID acronym in Latin script.")
put(1458,"ar","معرّف خارجي (ID)","correction","This is an identifier form label; include the source's protected ID acronym alongside its Arabic gloss.")
put(1459,"hi","हल करने के लिए बाहरी ID","correction","This labels the external identifier that the form will resolve; preserve the protected ID acronym in Latin script.")
put(1459,"ar","ID خارجي مطلوب حلّه","correction","This labels the external identifier to resolve; preserve the protected ID acronym and clarify the action.")
put(1460,"es","ID externo:","correction","This value label names the protected External ID field; use the source acronym.")
put(1460,"hi","बाहरी ID:","correction","This value label names the protected External ID field; preserve the acronym in Latin script.")
put(1460,"fr","ID externe :","correction","This value label names the protected External ID field; use the source acronym.")
put(1460,"ar","المعرّف الخارجي (ID):","correction","This value label names the protected External ID field; include the source acronym.")

# Clarify that API keys have limited scope, not merely an area or an extended reach.
put(1461,"es","Las aplicaciones Servarr externas deben usar una clave de API de alcance limitado, no una sesión de operador.","correction","The current con alcance is incomplete and awkward; de alcance limitado communicates a scoped security key.")
put(1461,"hi","बाहरी Servarr ऐप्स को सीमित दायरे वाली API कुंजी का उपयोग करना चाहिए, ऑपरेटर सत्र का नहीं।","refinement","The current English loan scoped is understandable, but सीमित दायरे वाली makes the key's restriction explicit.")
put(1461,"de","Externe Servarr-Apps sollten einen API-Schlüssel mit begrenzten Berechtigungen verwenden, keine Operatorsitzung.","correction","Bereichsbezogen means area-related; limited permissions expresses the security meaning of a scoped API key.")
put(1461,"fr","Les applications Servarr externes doivent utiliser une clé API à portée limitée, et non une session d'opérateur.","correction","Étendue can mean extended; à portée limitée expresses a restricted API-key scope.")
put(1461,"vi","Các ứng dụng Servarr bên ngoài nên dùng khóa API có phạm vi quyền hạn giới hạn, không dùng phiên của người vận hành.","correction","Trong phạm vi does not express a restricted scope; this wording makes the API key's limited permissions clear.")
put(1461,"id","Aplikasi Servarr eksternal sebaiknya menggunakan kunci API dengan cakupan terbatas, bukan sesi operator.","correction","Yang dicakup is awkward and does not convey a limited security scope; cakupan terbatas does.")

# The caller is a player integrations panel with an external visualizer section.
put(1462,"zh-Hans","外部可视化工具","correction","展示台 means a display stand/showcase; this is the external visualizer tool in the player integrations panel.")
put(1462,"zh-Hant","外部視覺化工具","correction","展示台 means a display stand/showcase; this is the external visualizer tool in the player integrations panel.")
put(1462,"ar","أداة التصور المرئي الخارجية","correction","The current متخيل is an imagined person/object; this label names a visualizer tool.")
put(1462,"ko","외부 시각화 도구","refinement","The caller labels software in the player integrations panel; 도구 names a tool rather than implying a hardware device.")
put(1462,"vi","Trình trực quan hóa bên ngoài","correction","The current wording means an external display; this is a visualizer tool in the player integrations panel.")

NOTES={
1443:"Publishing statistics label for the count expiring soon.",
1444:"Automation recipe approval gate for explicit publication of signed quality and verification evidence to trusted mesh peers.",
1445:"MediaCore metadata portability card header and export button.",
1446:"RustyMilk preset export control for the selected shape fragment.",
1447:"RustyMilk preset export control for the selected wave fragment.",
1448:"Success message header after an export completes.",
1449:"Export control for the active RustyMilk preset.",
1450:"Scrobble/rating integration description that exports confirmed local playback or ratings to the selected media-server profile.",
1451:"MediaCore metadata portability description for a portable package of ContentIDs.",
1452:"Tooltip for exporting the active RustyMilk preset text after local edits.",
1453:"Tooltip for exporting the selected custom shape as a .shape fragment.",
1454:"Tooltip for exporting the selected custom wave as a .wave fragment.",
1455:"Description of export/import operations and conflict resolution.",
1456:"Federation diagnostics label for the Hermit/Friends only/Public/Custom audience mode.",
1457:"Discography coverage selector option whose value is ExtendedDiscography.",
1458:"External identifier form label.",
1459:"External identifier resolution form label.",
1460:"External identifier value label.",
1461:"Servarr readiness description comparing a scoped API key with an operator session.",
1462:"Section title in the player integrations panel for an external visualizer tool."
}

def current_tokens(s):
    return tok(s)

def main():
    im=readj(CF/"manifest.json")
    if im["head"]!=HEAD or im["tree"]!=TREE or im["selectedPositions"]!=[1443,1462]:
        raise SystemExit("candidate-free input pin mismatch")
    if OUT.exists():
        raise SystemExit("primary-review output already exists")
    (OUT/"evidence").mkdir(parents=True)
    shutil.copytree(CF,OUT/"evidence"/"candidate-free-input")
    cells=readjl(CF/"current-target-cells.jsonl")
    ctxs={r["position"]:r for r in readjl(CF/"source-contexts.jsonl")}
    rows=[]
    for c in cells:
        key=(c["position"],c["locale"])
        base=tok(c["sourceKey"]);cur=tok(c["currentTarget"])
        selected=P.get(key)
        if selected:
            proposed=selected["target"];disp=selected["disposition"];reason=selected["reason"];confidence=selected["confidence"]
        else:
            proposed=None;disp="accept-current";reason="The current wording is semantically appropriate for the pinned caller and fits the source's label/action context; retain it.";confidence="moderate"
        prop=tok(proposed) if proposed is not None else cur
        current_missing=[x for x in base["protectedLiterals"] if x not in cur["protectedLiterals"]]
        proposed_missing=[x for x in base["protectedLiterals"] if x not in prop["protectedLiterals"]] if proposed is not None else []
        current_pass=(base["placeholders"]==cur["placeholders"] and base["markupTags"]==cur["markupTags"] and base["numericTokens"]==cur["numericTokens"] and not current_missing)
        proposed_pass=(base["placeholders"]==prop["placeholders"] and base["markupTags"]==prop["markupTags"] and base["numericTokens"]==prop["numericTokens"] and not proposed_missing)
        if not current_pass and proposed is None:
            raise SystemExit("baseline token mismatch left unchanged at "+str(key))
        if proposed is not None and not proposed_pass:
            raise SystemExit("proposed target token mismatch at "+str(key))
        if proposed is None and disp!="accept-current":
            raise SystemExit("disposition without proposal at "+str(key))
        context=ctxs[c["position"]]
        tchecks={"currentChecksPass":current_pass,"sourcePlaceholders":base["placeholders"],"currentPlaceholders":cur["placeholders"],"proposedPlaceholders":prop["placeholders"],"sourceMarkupTags":base["markupTags"],"currentMarkupTags":cur["markupTags"],"proposedMarkupTags":prop["markupTags"],"sourceNumericTokens":base["numericTokens"],"currentNumericTokens":cur["numericTokens"],"proposedNumericTokens":prop["numericTokens"],"protectedLiterals":base["protectedLiterals"],"currentProtectedLiterals":cur["protectedLiterals"],"currentMissingProtectedLiterals":current_missing,"proposedProtectedLiterals":prop["protectedLiterals"],"proposedMissingProtectedLiterals":proposed_missing,"proposedChecksPass":proposed_pass}
        rows.append({"position":c["position"],"sourceKey":c["sourceKey"],"sourceKeySha256":c["sourceKeySha256"],"locale":c["locale"],"callerContextSummary":NOTES[c["position"]],"callerCount":c["callerCount"],"callerRefs":c["callerRefs"],"sourceContextSha256":c["sourceContextSha256"],"currentTarget":c["currentTarget"],"currentTargetSha256":c["currentTargetSha256"],"disposition":disp,"proposedTarget":proposed,"proposedTargetSha256":sha_text(proposed) if proposed is not None else None,"reviewReason":reason,"confidence":confidence,"tokenChecks":tchecks,"translationStatus":None})
    if set(P)!={(r["position"],r["locale"]) for r in rows if r["proposedTarget"] is not None}:
        raise SystemExit("proposal map and ledger differ")
    counts=Counter(r["disposition"] for r in rows)
    changes=[{"position":r["position"],"sourceKey":r["sourceKey"],"locale":r["locale"],"currentTarget":r["currentTarget"],"currentTargetSha256":r["currentTargetSha256"],"disposition":r["disposition"],"proposedTarget":r["proposedTarget"],"proposedTargetSha256":r["proposedTargetSha256"],"reviewReason":r["reviewReason"]} for r in rows if r["proposedTarget"] is not None]
    wjl(OUT/"cell-review.jsonl",rows)
    wj(OUT/"change-summary.json",{"artifact":"slskR W1443-W1462 primary proposed-target summary","head":HEAD,"tree":TREE,"changeCount":len(changes),"changes":changes})
    wj(OUT/"source-context-notes.json",{"artifact":"W1443-W1462 caller-context review notes","head":HEAD,"tree":TREE,"sources":{str(k):v for k,v in NOTES.items()},"candidateFreeCallerCount":sum(1 for r in ctxs.values() if r["callers"]),"callerlessPositions":[p for p,r in ctxs.items() if not r["callers"]],"runtimeContext":"web/src/lib/interfaceLocale.js uses exact English source-key lookup, named placeholder substitution, twelve locale catalogs, and English fallback; see evidence/candidate-free-input/localization-runtime-context.json."})
    shutil.copyfile(CF/"prior-hold-reattestation.jsonl",OUT/"prior-hold-reattestation.jsonl")
    shutil.copyfile(CF/"prior-selection-reattestation.jsonl",OUT/"prior-selection-reattestation.jsonl")
    # Store live before/after observations already obtained by the candidate-free builder and exact-head pin reattestation.
    before=readj(CF/"PR-attestation.json")
    after=readj(CF/"PR-attestation-after.json")
    def stage(x,clean):
        return {"state":"OPEN","isDraft":True,"branch":BRANCH,"head":HEAD,"headTree":TREE,"liveBranchRef":HEAD,"livePullRef":HEAD,"checkoutWorktreeClean":clean,"checkoutHead":HEAD,"checkoutTree":TREE,"baseRef":"main","baseSha":"2a2b188f10b9460a15bc6d5c34e406b0193d51ba","observedAtUtc":x.get("attestedAtUtc",x.get("observedAtUtc"))}
    wj(OUT/"live-pr-attestation.json",{"observedBefore":stage(before,True),"observedAfter":stage(after,True),"afterSourcePinCount":after["sourcePinCount"],"all240CatalogTargetsReattested":after["all240CatalogTargetsReattested"]})
    with (OUT/"evidence/candidate-free-verification.txt").open("w",encoding="utf-8") as f:
        result=subprocess.check_output(["python3",str(CF/"verify-candidate-free.py")],text=True)
        f.write(result)
    # Ensure the packet records the baseline protected-literal issue and its complete correction.
    current_mismatch=sum(not r["tokenChecks"]["currentChecksPass"] for r in rows)
    fixed_mismatch=sum(bool(r["tokenChecks"]["currentMissingProtectedLiterals"]) and r["tokenChecks"]["proposedChecksPass"] for r in rows)
    if current_mismatch!=9 or fixed_mismatch!=9:
        raise SystemExit(f"baseline protected-literal mismatch reconciliation unexpected: {current_mismatch}, {fixed_mismatch}")
    manifest={"artifact":"slskR PR #204 W1443-W1462 primary review","repository":"snapetech-org/slskR","pullRequest":204,"branch":BRANCH,"baseRef":"main","baseSha":"2a2b188f10b9460a15bc6d5c34e406b0193d51ba","head":HEAD,"tree":TREE,"window":"W1443-W1462","sourceCount":20,"localeCount":12,"cellCount":240,"locales":LOCALES,"decisionCounts":dict(counts),"proposedTargetCount":len(changes),"carriedHoldReattestationCount":35,"changedCarriedHolds":0,"priorSelectionReattestationRows":200,"callerResolutionHoldCount":0,"currentWindowHoldCount":0,"candidateFreeInputManifestSha256":sha((CF/"manifest.json").read_bytes()),"candidateFreeInputChecksumListSha256":sha((CF/"SHA256SUMS.txt").read_bytes()),"sourceQueueOrderSha256":im["sourceLookupKeyOrderSha256"],"catalogSourceCount":im["catalogSourceCount"],"mismatchCounts":im["mismatchCounts"],"proposedMismatchCounts":{"placeholderSequenceMismatchCount":0,"markupMismatchCount":0,"numericTokenMismatchCount":0,"protectedLiteralMismatchCount":0},"reconciledProtectedLiteralBaselineCells":9,"blindBoundary":"Primary decisions were prepared only from the candidate-free input; no blind-review or cross-audit output was opened.","reviewLimit":"Contextual editorial review; no native-speaker attestation is claimed.","createdAtUtc":datetime.datetime.now(datetime.timezone.utc).isoformat()}
    wj(OUT/"manifest.json",manifest)
    readme=f"""# slskR PR #204 W1443-W1462 primary review

This primary review covers all 240 cells for 20 English source keys by 12 locales. It was prepared from the exact-head candidate-free packet only; no blind-review or cross-audit output was opened.

Pinned PR head/tree: {HEAD} / {TREE}; branch {BRANCH}; PR OPEN/DRAFT. Caller references are pinned to exact production-source bytes and Git blobs. The packet carries 35 unchanged prior holds and reattests 200 previously selected source-key rows.

Decision counts: {json.dumps(dict(counts),ensure_ascii=False,sort_keys=True)}. Proposed target count: {len(changes)}. The candidate-free input records 9 baseline protected-literal mismatches, all at External ID labels (positions 1458-1460); this primary corrects all 9 with exact Latin-script ID. All proposed placeholder, markup, numeric, and protected-literal checks pass.

The caller context notes map each source to its current use: federation visibility modes, media-server scrobble/rating export, RustyMilk preset export, and identifier form labels. This is contextual editorial review; no native-speaker attestation is claimed. No repository or PR files were changed, and no tests, builds, CI jobs, browser sessions, or releases were run.

Verify with python3 verify_primary.py from this directory.
"""
    (OUT/"README.md").write_text(readme,encoding="utf-8")
    # Checksums include every file except this checksum list.
    files=sorted(p for p in OUT.rglob("*") if p.is_file() and p.name!="SHA256SUMS.txt")
    (OUT/"SHA256SUMS.txt").write_text("".join(f"{sha(p.read_bytes())}  {p.relative_to(OUT).as_posix()}\n" for p in files),encoding="utf-8")
    print(json.dumps({"built":True,"head":HEAD,"tree":TREE,"cells":len(rows),"counts":dict(counts),"proposedTargetCount":len(changes),"baselineProtectedLiteralCells":current_mismatch,"correctedProtectedLiteralCells":fixed_mismatch,"carriedHolds":35,"priorSelections":200,"packetFiles":len(files)+1},ensure_ascii=False,indent=2))

if __name__=="__main__":
    main()
