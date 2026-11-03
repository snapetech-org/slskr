from pathlib import Path
import collections, hashlib, json, re, subprocess

REPO=Path("/home/keith/Documents/code/task-worktrees/localization-20261102-slskr")
OUT=Path("/mnt/disks/scratch/task-scratch/slskr-pr204-window-0963-0982-primary-20261102")
HEAD="99282b2f9b904f9814f5be66d8f643175e134f8e"
TREE="ba0ba0790da40159b8d92935f0866cb6a112edce"
BRANCH="codex/slskr-l10n-audit-20261030"
LOCALES=["ar","de","es","fr","hi","id","ja","ko","pt-BR","vi","zh-Hans","zh-Hant"]
START,END=962,981
INV=REPO/"docs/pr-evidence/pr204-localization-2026-11-02/window-0803-0822/primary-packet/current-source-inventory.jsonl"
PRIOR=REPO/"docs/pr-evidence/pr204-localization-2026-11-02/window-0943-0962"
PRIOR_P=Path("/mnt/disks/scratch/task-scratch/slskr-pr204-window-0943-0962-primary-20261102")
PRIOR_X=Path("/mnt/disks/scratch/task-scratch/slskr-pr204-window-0943-0962-crossreview-20261102")
LOCALE_DIR="web/src/lib/locales"
PH=re.compile(r"\{[A-Za-z][A-Za-z0-9_]*\}")
TAG=re.compile(r"</?[A-Za-z][^>]*>")
ICU=re.compile(r"\{\s*[A-Za-z_][A-Za-z0-9_]*\s*,\s*(plural|select|selectordinal)\s*,",re.I)
TERMS=set(".?!。？！।")
COLONS=set(":：")
PROTECTED={969:["Soulseek"],972:["CSV"],977:["CSV"]}
CONTEXT={
962:"Setup Health Check modal tooltip and accessible description; copies the report for support or setup notes.",
963:"Realm Subject Index Conflicts tooltip and accessible description; disabledAuthorities is an in-browser list keyed by authorityKey, and the caller says it does not alter backend realm governance.",
964:"Download Action Preview modal tooltip and accessible description; copies the planned action summary before downloading.",
965:"Discography Coverage profile option Core, paired with Extended and All releases; value is CoreDiscography.",
966:"SongID Evidence Details scorecard label beside corpusMatchCount.",
967:"SongID Evidence Details section heading above run.corpusMatches.",
968:"Library Health issue-type label mapped from CorruptedFile and localized dynamically; a report helper also emits the same label.",
969:"No exact production source-string-literal caller in tracked web/src at this head. Runtime/composed use is not inferred.",
970:"No exact production source-string-literal caller in tracked web/src at this head. Runtime/composed use is not inferred.",
971:"Wishlist item deletion error toast.",
972:"CSV import error toast.",
973:"Ignored Wishlist folder-load error toast.",
974:"Ignored Wishlist result-load error in Search Detail.",
975:"Search-results error with retry-later fallback in Search Detail.",
976:"Wishlist load-error message and toast.",
977:"CSV file-read error toast.",
978:"Player Stats import status supplies the placeholders fileName and message.",
979:"No exact production source-string-literal caller in tracked web/src at this head. Runtime/composed use is not inferred.",
980:"Folder-restore error toast in Wishlist modal.",
981:"Wishlist item save error toast.",
}
P={}
def prop(i,l,k,t,r,c="moderate"): P[(i,l)]=(k,t,r,c)
authority={
"ar":("انسخ تقرير التعارض المرئي، بما في ذلك اختيارات تعطيل الجهات محليًا. هذا لا يغير إدارة عالم الواجهة الخلفية.","Caller stores browser-local disabled authorityKey values. Recast as disabling authorities locally and reuse same-head جهات from Disable authority; avoids the local-government reading of السلطة المحلية."),
"de":("Kopieren Sie den sichtbaren Konfliktbericht, einschließlich der Auswahl, Autoritäten lokal zu deaktivieren. Dies ändert nichts an der Backend-Realm-Governance.","Caller stores browser-local disabled authorityKey values. Recast as a local disable action to avoid örtlichen Behörden, which reads as municipal authorities; retain the technical noun for cross-review."),
"ko":("로컬에서 권한을 비활성화하는 선택을 포함하여 표시되는 충돌 보고서를 복사합니다. 백엔드 영역 거버넌스는 변경되지 않습니다.","Caller stores browser-local disabled authorityKey values. Recast as a local disable action and reuse same-head 권한 from Disable authority; avoids the local-government reading of 지역 당국."),
"vi":("Sao chép báo cáo xung đột hiển thị, bao gồm các lựa chọn vô hiệu hóa thẩm quyền ở cấp cục bộ. Điều này không thay đổi việc quản trị lĩnh vực phụ trợ.","Caller stores browser-local disabled authorityKey values. Recast as a local disable action and reuse same-head thẩm quyền; avoids the local-government reading of chính quyền địa phương."),
"zh-Hans":("复制可见的冲突报告，包括本地停用授权的选项。这不会改变后端领域治理。","Caller stores browser-local disabled authorityKey values. Recast as a local disable selection and reuse same-head 授权; avoids 地方当局's local-government reading."),
"zh-Hant":("複製可見的衝突報告，包括本機停用權限的選項。這不會改變後端領域治理。","Caller stores browser-local disabled authorityKey values. Recast as a local disable selection and reuse same-head 權限; avoids 地方當局's local-government reading."),
}
for l,(t,r) in authority.items(): prop(963,l,"refinement",t,r)
prop(964,"de","refinement","Kopieren Sie diese Aktionsübersicht, um sie vor dem Herunterladen zu überprüfen oder zu exportieren.","This is a tooltip description, not a short button label. Same-head German register notes permit formal Sie in descriptions; current Kopiere uses informal du-form. Candidate retains review and export before download.")
prop(964,"es","refinement","Copie este resumen de la acción para poder revisarlo o exportarlo antes de la descarga.","This is a tooltip description, not a short button label. Same-head Spanish register notes specify formal Copie for tooltip descriptions; current Copia is informal. Candidate retains review and export before download.")
prop(965,"es","correction","Esencial","Caller identifies a discography coverage profile (CoreDiscography) alongside Extended and All releases. Centro means a physical/geometric center, not core/essential repertoire.","high")
prop(965,"zh-Hans","refinement","核心","Discography profile option CoreDiscography, alongside Extended and All releases. 核心 makes the short profile label explicit while preserving the core meaning.")
prop(965,"zh-Hant","refinement","核心","Discography profile option CoreDiscography, alongside Extended and All releases. 核心 makes the short profile label explicit while preserving the core meaning.")
prop(966,"ar","correction","كوربوس","SongID scorecard Corpus is the matching corpus/dataset. جسد means a body; this matches the same-head Arabic Corpus Matches term.","high")
prop(966,"es","correction","Corpus","SongID scorecard Corpus is the matching corpus/dataset. Cuerpo means a body; Corpus is the technical term in the same-head Corpus Matches label.","high")
prop(966,"ko","correction","코퍼스","SongID scorecard Corpus is the matching corpus/dataset. 신체 means a body; this matches the same-head Korean Corpus Matches term.","high")
prop(966,"hi","refinement","कॉर्पस","The scorecard term is a corpus/dataset. Regularize spelling to कॉर्पस, matching same-head Hindi Corpus Matches; current spelling remains recognizable.")
prop(967,"ar","correction","مطابقات الكوربوس","The section lists corpus-match evidence. مباريات means sports matches; candidate describes corpus matches and reuses same-head كوربوس.","high")
prop(967,"id","correction","Kecocokan Korpus","The section lists corpus-match evidence. Pertandingan means sports matches; Kecocokan describes matches/correspondences and retains Korpus.","high")
prop(967,"vi","refinement","Kết quả khớp với ngữ liệu","Current heading means matching results but drops the explicit corpus reference. Candidate restores it in the SongID corpus-evidence section.")
prop(973,"es","correction","No se pudieron cargar las carpetas ignoradas de la lista de deseos.","Source identifies ignored folders in Wishlist. Current Spanish says only de la lista and omits de deseos; neighboring same-head Wishlist labels use lista de deseos.","high")
prop(973,"pt-BR","correction","Não foi possível carregar as pastas ignoradas da lista de desejos.","Source identifies ignored folders in Wishlist. Current Portuguese says only da lista and omits de desejos; neighboring same-head labels use lista de desejos.","high")
prop(973,"vi","correction","Không thể tải các thư mục đã bỏ qua của Danh sách mong muốn.","Source identifies ignored folders in Wishlist. Current Vietnamese omits Wishlist; neighboring same-head labels use Danh sách mong muốn.","high")
for l,t in {
"ar":"تعذّر تحميل نتائج قائمة الأمنيات المتجاهلة.",
"de":"Ignorierte Ergebnisse der Wunschliste konnten nicht geladen werden.",
"es":"No se pudieron cargar los resultados ignorados de la lista de deseos.",
"hi":"विशलिस्ट के अनदेखे परिणाम लोड नहीं हो सके।",
"ja":"無視したウィッシュリストの結果を読み込めませんでした。",
"ko":"무시된 위시리스트 결과를 불러오지 못했습니다.",
"pt-BR":"Não foi possível carregar os resultados ignorados da lista de desejos.",
"vi":"Không thể tải các kết quả đã bỏ qua trong Danh sách mong muốn.",
"zh-Hans":"无法加载已忽略的愿望清单结果。",
"zh-Hant":"無法載入已忽略的願望清單結果。",
}.items():
    prop(974,l,"refinement",t,"Source identifies ignored Wishlist results. Current target leaves Wishlist in English, while same-head neighboring Wishlist labels use this locale's localized feature name. Indonesian is excluded because its neighboring labels consistently retain Wishlist.")
prop(978,"hi","correction","फ़ाइल {fileName} पढ़ी नहीं जा सकी: {message}","Player Stats reports that a file could not be read. Current Hindi can read as though {fileName} is the agent that could not read; candidate states the file could not be read and preserves both placeholders.","high")
prop(978,"zh-Hans","refinement","无法读取 {fileName}：{message}","Both placeholders and meaning are present. Removing the space after a full-width colon follows Chinese punctuation spacing.")
prop(978,"zh-Hant","refinement","無法讀取 {fileName}：{message}","Both placeholders and meaning are present. Removing the space after a full-width colon follows Chinese punctuation spacing.")

def sha(b): return hashlib.sha256(b).hexdigest()
def sht(s): return sha(s.encode("utf-8"))
def jline(o): return json.dumps(o,ensure_ascii=False,sort_keys=True,separators=(",",":"))+"\n"
def jload(p): return json.loads(p.read_text(encoding="utf-8"))
def rows(p): return [json.loads(x) for x in p.read_text(encoding="utf-8").splitlines() if x]
def writej(name,o): (OUT/name).write_text(json.dumps(o,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8")
def writel(name,rs): (OUT/name).write_text("".join(jline(x) for x in rs),encoding="utf-8")
def run(args,cwd=REPO): return subprocess.run(args,cwd=cwd,text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=True)
def git(*args): return run(["git",*args]).stdout.strip()
def blob(path): return git("rev-parse",f"HEAD:{path}")
def fsha(p): return sha(p.read_bytes())
def place(s): return sorted(PH.findall(s))
def tags(s): return sorted(TAG.findall(s))
def icu(s): return bool(ICU.search(s))
def terms(s): return sum(c in TERMS for c in s)
def colons(s): return sum(c in COLONS for c in s)

# Verify local worktree, PR and official branch at the required exact pin before deriving artifacts.
head=git("rev-parse","HEAD"); tree=git("rev-parse","HEAD^{tree}"); branch=git("branch","--show-current"); status=git("status","--porcelain")
if (head,tree,branch,status)!=(HEAD,TREE,BRANCH,""): raise SystemExit(f"Local exact-head mismatch: {(head,tree,branch,status)}")
pr=json.loads(run(["gh","pr","view","204","--repo","snapetech-org/slskr","--json","state,isDraft,headRefName,headRefOid,baseRefName,baseRefOid,updatedAt,url"]).stdout)
remote=run(["git","ls-remote","taskgithub",f"refs/heads/{BRANCH}"]).stdout.strip().split()
remote_oid=remote[0] if remote else None
if pr["state"]!="OPEN" or pr["headRefName"]!=BRANCH or pr["headRefOid"]!=HEAD or remote_oid!=HEAD: raise SystemExit(f"Live pin mismatch: PR={pr}; remote={remote_oid}")
writej("live-pr-reattestation.json",{
"repository":"snapetech-org/slskR","pullRequest":204,"url":pr["url"],"state":pr["state"],"isDraft":pr["isDraft"],"updatedAt":pr["updatedAt"],
"baseRefName":pr["baseRefName"],"baseRefOid":pr["baseRefOid"],"branch":BRANCH,"expectedHead":HEAD,"localHead":head,"expectedTree":TREE,"localTree":tree,
"officialRemote":"taskgithub","officialRemoteBranchHead":remote_oid,"localWorktreeStatus":status,"localWorktreeClean":True,"allPinsMatch":True,
"noRepositoryOrPRMutation":True,"noTestsBuildsScansCIOrBrowser":True})

all_sources=rows(INV); byidx={int(x["sourceIndex"]):x for x in all_sources}
if any(i not in byidx for i in range(START,END+1)): raise SystemExit("Not a contiguous source window.")
sources=[]
for i in range(START,END+1):
    x=byidx[i]; s=x["sourceId"]
    if sht(s)!=x["sourceSha256"]: raise SystemExit(f"Source hash mismatch at {i}")
    sources.append({"sourceIndex":i,"windowLabel":i+1,"inventoryPosition1Based":x["inventoryPosition1Based"],"sourceId":s,"sourceSha256":sht(s)})
srcmap={x["sourceIndex"]:x for x in sources}

catalogs={}; cpaths={}; cpins=[]
for l in LOCALES:
    rel=f"{LOCALE_DIR}/ui-labels.{l}.json"; p=REPO/rel; raw=p.read_bytes(); doc=json.loads(raw.decode("utf-8"))
    catalogs[l]=doc; cpaths[l]=rel
    keys=list(doc)
    cpins.append({"locale":l,"path":rel,"gitBlob":blob(rel),"fileSha256":sha(raw),"bytes":len(raw),"keyCount":len(keys),
                  "orderedKeysetSha256CanonicalJsonArray":sht(json.dumps(keys,ensure_ascii=False,separators=(",",":")))})
if len({x["keyCount"] for x in cpins})!=1 or len({x["orderedKeysetSha256CanonicalJsonArray"] for x in cpins})!=1: raise SystemExit("Locale catalog key order/count mismatch.")
for x in sources:
    if any(x["sourceId"] not in catalogs[l] for l in LOCALES): raise SystemExit("Missing locale key: "+x["sourceId"])

# Exact quoted source literal scan, excluding locale catalogs and test files.
tracked=[x for x in git("ls-files","-z","--","web/src").split("\0") if x]
scan=[]
for rel in tracked:
    if "/locales/" in rel or re.search(r"(^|[./])tests?([./]|$)",rel,re.I) or re.search(r"\.test\.[^.]+$",rel,re.I): continue
    if Path(rel).suffix in {".js",".jsx",".ts",".tsx",".html",".md"}: scan.append(rel)
hits={i:[] for i in range(START,END+1)}
for x in sources:
    pat=re.compile(r"""(["'])"""+re.escape(x["sourceId"])+r"""\1""")
    for rel in scan:
        try: lines=(REPO/rel).read_text(encoding="utf-8").splitlines()
        except (UnicodeDecodeError,OSError): continue
        for n,line in enumerate(lines,1):
            if not pat.search(line) or line.strip().startswith(("//","/*","*")): continue
            kind="translation-wrapper-literal" if re.search(r"LocalizedText|interfaceText|translateRef|localizedRef|localized\(|translate\(",line) else "literal-mapping-or-call-chain"
            hits[x["sourceIndex"]].append({"path":rel,"line":n,"kind":kind,"text":line,"lines":lines})
# Corrupted File is returned by a literal issue-type map and rendered via a dynamic key.
for rel in ["web/src/components/System/LibraryHealth/index.jsx"]:
    lines=(REPO/rel).read_text(encoding="utf-8").splitlines()
    for n,line in enumerate(lines,1):
        if "LocalizedText" in line and "getIssueTypeLabel(" in line:
            hits[968].append({"path":rel,"line":n,"kind":"dynamic-localization-renderer-for-literal-label","text":line,"lines":lines})
pins=[]
for i,hs in hits.items():
    seen=set()
    for h in hs:
        k=(h["path"],h["line"],h["kind"])
        if k in seen: continue
        seen.add(k); n=h["line"]; rel=h["path"]; lines=h["lines"]; ctx=[{"line":j+1,"text":lines[j]} for j in range(max(0,n-3),min(len(lines),n+2))]
        pins.append({"sourceIndex":i,"windowLabel":i+1,"sourceId":srcmap[i]["sourceId"],"path":rel,"line":n,"kind":h["kind"],
          "surfaceLine":h["text"].strip(),"lineSha256":sht(h["text"]),"contextStartLine":ctx[0]["line"],"contextLines":ctx,
          "fileSha256":fsha(REPO/rel),"fileBlob":blob(rel)})
pins.sort(key=lambda x:(x["sourceIndex"],x["path"],x["line"]))
refs=collections.defaultdict(list)
for p in pins:
    r=f'{p["path"]}:{p["line"]}'
    if r not in refs[p["sourceIndex"]]: refs[p["sourceIndex"]].append(r)
inventory=[]
gaps=[]
for x in sources:
    i=x["sourceIndex"]; rr=refs[i]
    inventory.append({**x,"callerCount":len(rr),"callers":rr,"callerEvidenceKinds":[p["kind"] for p in pins if p["sourceIndex"]==i],"heldForNoExactCaller":not bool(rr)})
    if not rr:
        gaps.append({"sourceIndex":i,"windowLabel":i+1,"sourceId":x["sourceId"],
          "reason":"No exact production source-string-literal caller was found in tracked web/src at this head. Dynamic construction, server/API-originated strings, or another extraction limitation may still exist; the packet does not infer that the string is unused.",
          "targetLocales":LOCALES,"extractionLimitations":["Exact quoted literal scan only","Runtime-composed messages are not detected","Server/API-originated strings are not detected"]})
writel("source-inventory.jsonl",inventory); writel("caller-pins.jsonl",pins); writel("caller-gaps.jsonl",gaps); writel("catalog-pins.jsonl",cpins)

# Complete all-locale semantic and structural ledger.
ledger=[]; structural=[]
for x in sources:
    i=x["sourceIndex"]; source=x["sourceId"]; sp=place(source); sm=tags(source); literals=PROTECTED.get(i,[])
    for l in LOCALES:
        cur=catalogs[l][source]; item=P.get((i,l))
        if not refs[i]:
            d,kind,cand,reason,conf=("hold",None,None,"No exact production source-string-literal caller exists in tracked web/src at this head. Keep this locale value pending source-owner confirmation; possible dynamic/runtime use lies outside the literal audit.","low")
        elif item:
            kind,cand,reason,conf=item; d=kind
        else:
            d,kind,cand,reason,conf=("accept-current",None,None,f"The current value conveys the source in this pinned production context. {CONTEXT[i]} No material meaning or scope loss was found for this locale.","moderate")
        final=cand if cand is not None else cur
        checks=lambda v: {"placeholdersMatch":place(v)==sp,"markupMatches":tags(v)==sm,"protectedLiteralsPreserved":all(q in v for q in literals),
            "icuMatches":icu(v)==icu(source),"terminatorCountMatches":terms(v)==terms(source),"colonCountMatches":colons(v)==colons(source)}
        cc=checks(cur); fc=checks(final)
        row={"sourceIndex":i,"windowLabel":i+1,"sourceId":source,"sourceSha256":x["sourceSha256"],"locale":l,"catalogPath":cpaths[l],
          "catalogFileSha256":next(z["fileSha256"] for z in cpins if z["locale"]==l),"currentTarget":cur,"currentTargetSha256":sht(cur),
          "disposition":d,"proposalKind":kind,"proposedTarget":cand,"proposedTargetSha256":sht(cand) if cand is not None else None,
          "reviewedFinal":final,"reviewedFinalSha256":sht(final),"callerReferences":refs[i],"contextType":CONTEXT[i],
          "languageContext":"Direct locale catalog value in the pinned caller context; machine-assisted primary review, no native-speaker approval.",
          "confidence":conf,"rationale":reason,"sourcePlaceholders":sp,"currentTargetPlaceholders":place(cur),"finalTargetPlaceholders":place(final),
          "sourceMarkup":sm,"currentTargetMarkup":tags(cur),"finalTargetMarkup":tags(final),"protectedLiterals":literals,
          "currentProtectedLiteralsPreserved":cc["protectedLiteralsPreserved"],"protectedLiteralsPreserved":fc["protectedLiteralsPreserved"],
          "currentPlaceholderParity":cc["placeholdersMatch"],"targetPlaceholderParity":fc["placeholdersMatch"],
          "currentMarkupParity":cc["markupMatches"],"targetMarkupParity":fc["markupMatches"],
          "currentHasICU":icu(cur),"targetHasICU":icu(final),"icuParity":fc["icuMatches"],
          "sourceTerminalPunctuationCount":terms(source),"currentTerminalPunctuationCount":terms(cur),"finalTerminalPunctuationCount":terms(final),
          "sourceColonCount":colons(source),"currentColonCount":colons(cur),"finalColonCount":colons(final),
          "punctuationCompatible":fc["terminatorCountMatches"] and fc["colonCountMatches"],"nativeSpeakerApproval":False}
        ledger.append(row)
        structural.append({"sourceIndex":i,"windowLabel":i+1,"locale":l,"sourceId":source,"currentTarget":cur,"reviewedFinal":final,
          "sourcePlaceholders":sp,"currentPlaceholders":place(cur),"finalPlaceholders":place(final),"sourceMarkup":sm,"currentMarkup":tags(cur),"finalMarkup":tags(final),
          "protectedLiterals":literals,"checks":{"current":cc,"final":fc},"sourceHasICU":icu(source),"currentHasICU":icu(cur),"finalHasICU":icu(final)})
writel("primary-review-ledger.jsonl",ledger)
writel("manual-proposals.jsonl",[x for x in ledger if x["proposedTarget"] is not None])
writel("hold-register.jsonl",[x for x in ledger if x["disposition"]=="hold"])
writel("structural-cell-audit.jsonl",structural)

# Pin same-head glossary, adjacent terminology and established Wishlist terms; prior register note applies to tooltip descriptions.
refkeys=["Core","Extended","All releases","Corpus","Corpus Matches","Could not load wishlist.",
         "Could not delete this Wishlist item.","Could not save Wishlist item.",
         "Disable authority {authorityKey}","Enable authority {authorityKey}"]
inv_by_id={r["sourceId"]:r["sourceIndex"] for r in all_sources}
refs_out=[]
for l in LOCALES:
    for key in refkeys:
        if key in catalogs[l]:
            z=next(z for z in cpins if z["locale"]==l)
            refs_out.append({"referenceType":"same-head-catalog-term","locale":l,"sourceId":key,"sourceIndex":inv_by_id.get(key),
              "target":catalogs[l][key],"targetSha256":sht(catalogs[l][key]),"catalogPath":cpaths[l],
              "catalogSha256":z["fileSha256"],"catalogBlob":z["gitBlob"],"use":"Terminology/context only; not prior semantic approval."})
fp=REPO/"docs/pr-evidence/pr204-localization-2026-11-02/window-0923-0942/primary-packet/locale-formality-checks.jsonl"
for r in rows(fp):
    if r.get("sourceId")=="Copy Search Seeds" and r.get("locale") in {"de","es"}:
        rel=str(fp.relative_to(REPO))
        refs_out.append({"referenceType":"same-head-locale-formality-evidence","locale":r["locale"],"sourceId":r["sourceId"],
          "sourceIndex":r["sourceIndex"],"contextType":r["contextType"],"note":r["note"],"reviewedRegister":r["reviewedRegister"],
          "evidenceFile":rel,"evidenceFileSha256":fsha(fp),"evidenceFileBlob":blob(rel),
          "use":"Prior same-head register note for tooltip descriptions and button labels; not native-speaker approval."})
writel("same-head-terminology-pins.jsonl",refs_out)

# Previous W943-W962 final values and history.
prevread=rows(PRIOR/"readback.jsonl")
if len(prevread)!=240: raise SystemExit("Prior W943-W962 readback was not 240 rows.")
prevfinal=[]
for r in prevread:
    cur=catalogs[r["locale"]][r["sourceId"]]
    prevfinal.append({"sourceIndex":r["sourceIndex"],"windowLabel":r["windowLabel"],"sourceId":r["sourceId"],"locale":r["locale"],
      "priorFinalDisposition":r["finalDisposition"],"priorFinalTarget":r["finalTarget"],"priorFinalTargetSha256":r["finalTargetSha256"],
      "currentTargetSha256":sht(cur),"matchesCurrent":cur==r["finalTarget"] and sht(cur)==r["finalTargetSha256"],
      "priorHold":r["finalDisposition"]=="hold","priorCallerGap":r["callerGap"]})
writel("prior-window-final-reattestation.jsonl",prevfinal)
prevholds=[r for r in prevfinal if r["priorHold"]]
if len(prevholds)!=12 or any(r["sourceIndex"]!=943 for r in prevholds): raise SystemExit("Prior W944 hold dispositions changed.")

# Reattest previous caller pins against exact file, line, and git blob at the new head.
prevpins=rows(PRIOR/"primary-review"/"caller-pins.jsonl")
prevcall=[]
for r in prevpins:
    rel=r["path"]; n=int(r["line"]); p=REPO/rel; line=p.read_text(encoding="utf-8").splitlines()[n-1]
    prevcall.append({"path":rel,"line":n,"sourceIndex":r["sourceIndex"],"sourceId":r["sourceId"],
      "currentLineSha256":sht(line),"priorLineSha256":r["lineSha256"],"currentFileSha256":fsha(p),"priorFileSha256":r["fileSha256"],
      "currentFileBlob":blob(rel),"priorFileBlob":r["fileBlob"],
      "matches":sht(line)==r["lineSha256"] and fsha(p)==r["fileSha256"] and blob(rel)==r["fileBlob"]})
writel("prior-caller-reattestation.jsonl",prevcall)
prevbounds=rows(PRIOR/"primary-review"/"adjacent-boundary-readbacks.jsonl")
prevbound=[]
for r in prevbounds:
    cur=catalogs[r["locale"]][r["sourceId"]]
    prevbound.append({**r,"currentTargetSha256":sht(cur),"matchesCurrent":cur==r["target"] and sht(cur)==r["targetSha256"]})
writel("prior-boundary-reattestation.jsonl",prevbound)
forward=[r for r in prevbound if r["sourceIndex"]==START]
if len(forward)!=12 or any(not r["matchesCurrent"] for r in forward): raise SystemExit("Prior forward W963 boundary did not reattest.")

# Current preceding, first, and following boundary target hashes.
source982=byidx[END+1]["sourceId"]
boundaries=[]
for i,role in [(START-1,"preceding-window-end"),(START,"current-window-first-source"),(END+1,"following-window-first-source")]:
    source=byidx[i]["sourceId"]
    for l in LOCALES:
        target=catalogs[l][source]
        boundaries.append({"role":role,"sourceIndex":i,"windowLabel":i+1,"sourceId":source,"sourceSha256":sht(source),
          "locale":l,"target":target,"targetSha256":sht(target),"catalogPath":cpaths[l]})
writel("adjacent-boundary-readbacks.jsonl",boundaries)

# Prior packet sums: committed evidence, primary scratch and independent cross-review scratch.
def verify_sums(p):
    result=subprocess.run(["sha256sum","-c","SHA256SUMS"],cwd=p,text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    if result.returncode: raise SystemExit(f"Checksum failure {p}: {result.stdout}{result.stderr}")
    return {"path":str(p/"SHA256SUMS"),"verifiedEntries":sum(x.endswith(": OK") for x in result.stdout.splitlines()),
      "exitCode":result.returncode,"stdoutSha256":sha(result.stdout.encode()),"stderr":result.stderr}
prior_checks={"committedWindow":verify_sums(PRIOR),"primaryScratch":verify_sums(PRIOR_P),"crossReviewScratch":verify_sums(PRIOR_X)}
writej("input-attestation.json",{
  "exactHead":HEAD,"exactTree":TREE,"sourceInventoryPath":str(INV.relative_to(REPO)),"sourceInventoryFileSha256":fsha(INV),
  "sourceInventoryGitBlob":blob(str(INV.relative_to(REPO))),"sourceInventoryRecordCount":len(all_sources),
  "selectedSourceIndices":[START,END],"selectedSourceIdsSha256":sht("\n".join(x["sourceId"] for x in sources)),
  "previousWindow":"W943-W962","previousCommittedRootSHA256SUMS":fsha(PRIOR/"SHA256SUMS"),
  "previousPrimaryScratchSHA256SUMS":fsha(PRIOR_P/"SHA256SUMS"),"previousCrossReviewScratchSHA256SUMS":fsha(PRIOR_X/"SHA256SUMS"),
  "previousChecksumVerifications":prior_checks,"previousReadbackRows":len(prevread),
  "previousReadbackMatchesCurrent":sum(x["matchesCurrent"] for x in prevfinal),"previousW944HoldCells":len(prevholds),
  "previousCallerPins":len(prevpins),"previousCallerPinsReattested":sum(x["matches"] for x in prevcall),
  "previousBoundaryRows":len(prevbounds),"previousBoundaryRowsReattested":sum(x["matchesCurrent"] for x in prevbound)})

badcurrent=[r for r in structural if not all(r["checks"]["current"].values())]
badfinal=[r for r in structural if not all(r["checks"]["final"].values())]
if badfinal: raise SystemExit("Final structural mismatch: "+json.dumps(badfinal[:4],ensure_ascii=False))
if any(not r["matchesCurrent"] for r in prevfinal): raise SystemExit("Prior final readback mismatch.")
if any(not r["matches"] for r in prevcall): raise SystemExit("Prior caller pin mismatch.")
counts=collections.Counter(r["disposition"] for r in ledger); pcounts=collections.Counter(r["proposalKind"] for r in ledger if r["proposedTarget"] is not None)
summary={"repository":"snapetech-org/slskR","pullRequest":204,"state":pr["state"],"isDraft":pr["isDraft"],"branch":BRANCH,"head":HEAD,"tree":TREE,
"baseRefName":pr["baseRefName"],"baseRefOid":pr["baseRefOid"],"window":"W963-W982","zeroBasedSourceIndexInclusive":[START,END],
"sourceCount":20,"localeCount":12,"cellCount":len(ledger),"callerFiles":len({x["path"] for x in pins}),"callerPins":len(pins),
"callerGapSourceIds":[x["sourceId"] for x in gaps],"callerGapCount":len(gaps),"callerGapCellsHeld":len(gaps)*12,
"counts":dict(counts),"proposalKindCounts":dict(pcounts),"proposedValueChanges":sum(x["proposedTarget"] is not None for x in ledger),
"catalogsReattested":len(cpins),"catalogKeyCount":cpins[0]["keyCount"],"catalogKeysetsIdentical":True,
"priorWindow":"W943-W962","priorWindowCellReadbacksReattested":len(prevfinal),"priorWindowReadbacksMatchingCurrent":sum(x["matchesCurrent"] for x in prevfinal),
"priorWindowHoldCellsPreserved":len(prevholds),"priorCallerPinsReattested":len(prevcall),"priorCallerPinsMatching":sum(x["matches"] for x in prevcall),
"priorBoundaryRowsReattested":len(prevbound),"priorBoundaryRowsMatching":sum(x["matchesCurrent"] for x in prevbound),"adjacentBoundaryCells":len(boundaries),
"placeholderMismatches":sum(not x["checks"]["final"]["placeholdersMatch"] for x in structural),
"markupMismatches":sum(not x["checks"]["final"]["markupMatches"] for x in structural),
"icuMismatches":sum(not x["checks"]["final"]["icuMatches"] for x in structural),
"punctuationMismatches":sum(not(x["checks"]["final"]["terminatorCountMatches"] and x["checks"]["final"]["colonCountMatches"]) for x in structural),
"protectedLiteralCurrentFailureCells":sum(not x["checks"]["current"]["protectedLiteralsPreserved"] for x in structural),
"protectedLiteralFinalFailureCells":sum(not x["checks"]["final"]["protectedLiteralsPreserved"] for x in structural),
"allFinalStructuralChecksPass":not badfinal,"nativeSpeakerApproval":False,"headedBrowserAcceptance":False,
"testsBuildScansCiOrBrowserRun":False,"repositoryOrPrChanged":False,"worktreeStatusAtPin":status,"scratchPath":str(OUT)}
writej("summary.json",summary)
structural_audit={"window":"W963-W982","head":HEAD,"tree":TREE,"cellCount":len(structural),
"currentPlaceholderMismatches":[x for x in structural if not x["checks"]["current"]["placeholdersMatch"]],
"finalPlaceholderMismatches":[x for x in structural if not x["checks"]["final"]["placeholdersMatch"]],
"currentMarkupMismatches":[x for x in structural if not x["checks"]["current"]["markupMatches"]],
"finalMarkupMismatches":[x for x in structural if not x["checks"]["final"]["markupMatches"]],
"currentICUMismatches":[x for x in structural if not x["checks"]["current"]["icuMatches"]],
"finalICUMismatches":[x for x in structural if not x["checks"]["final"]["icuMatches"]],
"currentProtectedLiteralFailures":[x for x in structural if not x["checks"]["current"]["protectedLiteralsPreserved"]],
"finalProtectedLiteralFailures":[x for x in structural if not x["checks"]["final"]["protectedLiteralsPreserved"]],
"protectedLiteralPolicy":{str(k):v for k,v in PROTECTED.items()},
"punctuationAudit":"Sentence terminators and colons are counted with locale punctuation equivalents; all reviewed-final counts match source counts.",
"icuAudit":"No source in this window contains ICU plural/select syntax; every current and proposed locale value was checked.",
"result":"PASS"}
writej("structural-audit.json",structural_audit)
readme=f"""# slskR PR #204 W963-W982 primary localization review

Pinned to open draft PR #204 at head {HEAD}, tree {TREE}, branch {BRANCH}. Local worktree, official remote branch, and live PR head matched; the repository worktree was clean.

Reviewed the next contiguous 20 source IDs (zero-based indices {START}-{END}, labels W963-W982) across all 12 direct locales: 240 cells. The prior W943-W962 committed readback was reattested: all {len(prevfinal)} cells still match current catalogs; all {len(prevholds)} W944 hold cells remain unchanged. Prior caller and boundary pins were independently rechecked.

## Dispositions

- {counts['correction']} corrections
- {counts['refinement']} refinements
- {counts['accept-current']} current values retained
- {counts['hold']} cells held across {len(gaps)} exact-caller gaps

W970, W971, and W980 have no exact production source-string-literal caller in tracked web/src at this head. Each locale value is held. The audit separates these literal-map gaps from extraction limitations: dynamic construction, server/API-originated text, and runtime callers are not detected and are not assumed absent.

Structural review covers placeholders, markup, ICU forms, punctuation, and protected literals (Soulseek and CSV). This is a machine-assisted primary review, not native-speaker approval. No repository/catalog/PR edits, commits, tests, builds, scans, CI, releases, or browser work were performed.
"""
(OUT/"README.md").write_text(readme,encoding="utf-8")
artifacts=sorted(p for p in OUT.iterdir() if p.is_file() and p.name not in {"manifest.json","SHA256SUMS"})
manifest={"repository":"snapetech-org/slskR","pullRequest":204,"window":"W963-W982","head":HEAD,"tree":TREE,
"artifactCountExcludingManifestAndSums":len(artifacts),"artifacts":[{"path":p.name,"bytes":p.stat().st_size,"sha256":fsha(p)} for p in artifacts],
"summary":{"cellCount":len(ledger),"dispositionCounts":dict(counts)}}
writej("manifest.json",manifest)
sumfiles=sorted(p for p in OUT.iterdir() if p.is_file() and p.name!="SHA256SUMS")
(OUT/"SHA256SUMS").write_text("".join(f"{fsha(p)}  {p.name}\n" for p in sumfiles),encoding="utf-8")
print(json.dumps({"output":str(OUT),"counts":dict(counts),"proposalCounts":dict(pcounts),"callerGaps":[x["sourceId"] for x in gaps],
"callerPins":len(pins),"priorReadbackMatches":sum(x["matchesCurrent"] for x in prevfinal),"priorCallersMatching":sum(x["matches"] for x in prevcall),
"priorBoundariesMatching":sum(x["matchesCurrent"] for x in prevbound),"badCurrentStructural":len(badcurrent),"badFinalStructural":len(badfinal)},ensure_ascii=False,indent=2))
