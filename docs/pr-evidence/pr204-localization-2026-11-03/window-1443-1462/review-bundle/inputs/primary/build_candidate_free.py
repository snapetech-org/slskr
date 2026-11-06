#!/usr/bin/env python3
import datetime,hashlib,json,re,subprocess
from collections import Counter,defaultdict
from pathlib import Path
ROOT=Path("/home/keith/Documents/code/task-scratch/slskr-pr204-w1443-1462-primary-20261103")
INP=ROOT/"candidate-free-input"
REPO=Path("/home/keith/Documents/code/task-scratch/slskr-pr204-w1443-1462-source-repo")
HEAD="44b37bd94385128d5bb5287aa1545901282bdfcb"; TREE="02c3f149a079c67b010d973dd02ca15776ad1610"
BRANCH="codex/slskr-l10n-audit-20261030"; BASE_SHA="2a2b188f10b9460a15bc6d5c34e406b0193d51ba"
LOCALES=["es","zh-Hans","hi","de","ja","fr","pt-BR","ar","ko","zh-Hant","vi","id"]
START,END=1443,1462
PREV=REPO/"docs/pr-evidence/pr204-localization-2026-11-03/window-1423-1442/candidate-free-input"

def run(*a): return subprocess.check_output(a,cwd=REPO,text=True).strip()
def sha(b): return hashlib.sha256(b).hexdigest()
def ht(s): return sha(s.encode())
def canon(x): return json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(",",":"))
def wj(p,x): p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
def wjl(p,x): p.write_text("".join(json.dumps(y,ensure_ascii=False,sort_keys=True,separators=(",",":"))+"\n" for y in x),encoding="utf-8")
def rj(p): return json.loads(p.read_text(encoding="utf-8"))
def rjl(p): return [json.loads(x) for x in p.read_text(encoding="utf-8").splitlines() if x]
def blob(p): return run("git","rev-parse",f"{HEAD}:{p}")
def orderhash(xs): return ht("\n".join(xs)+"\n")
def check_sums(folder,name="SHA256SUMS.txt"):
    for line in (folder/name).read_text().splitlines():
        d,n=line.split(None,1); n=n.lstrip("* "); assert sha((folder/n).read_bytes())==d,(folder,n)
def decode(raw):
    bt=chr(96);out=[];i=0
    simple={"n":"\n","r":"\r","t":"\t","b":"\b","f":"\f","v":"\v","0":"\0","\\":"\\","\"":"\"","'":"'"};simple[bt]=bt
    while i<len(raw):
        if raw[i]!="\\": out.append(raw[i]);i+=1;continue
        i+=1
        if i>=len(raw):break
        e=raw[i];i+=1
        if e in ("\n","\r"):
            if e=="\r" and i<len(raw) and raw[i]=="\n":i+=1
            continue
        if e in simple:out.append(simple[e]);continue
        if e=="x" and re.fullmatch(r"[0-9a-fA-F]{2}",raw[i:i+2]):out.append(chr(int(raw[i:i+2],16)));i+=2;continue
        if e=="u":
            if i<len(raw) and raw[i]=="{" and "}" in raw[i:]:
                j=raw.index("}",i);h=raw[i+1:j]
                if re.fullmatch(r"[0-9a-fA-F]{1,6}",h):out.append(chr(int(h,16)));i=j+1;continue
            if re.fullmatch(r"[0-9a-fA-F]{4}",raw[i:i+4]):out.append(chr(int(raw[i:i+4],16)));i+=4;continue
            out.append("u");continue
        out.append(e)
    return "".join(out)
def literals(s):
    i=0;n=len(s);bt=chr(96);interp="$"+chr(123)
    while i<n:
        if s.startswith("//",i):
            j=s.find("\n",i+2);i=n if j<0 else j+1;continue
        if s.startswith("/*",i):
            j=s.find("*/",i+2);i=n if j<0 else j+2;continue
        q=s[i]
        if q not in ("'",'"',bt):i+=1;continue
        start=i;i+=1;raw=[]
        while i<n:
            c=s[i]
            if c=="\\":
                if i+1<n:raw.extend((c,s[i+1]));i+=2
                else:i+=1
                continue
            if c==q:i+=1;break
            raw.append(c);i+=1
        val="".join(raw)
        if q==bt and interp in val:continue
        yield decode(val),start
def tokens(s):
    ph=re.findall(r"\{[A-Za-z][A-Za-z0-9_]*\}",s);tags=re.findall(r"</?[A-Za-z][^>]*>",s);nums=re.findall(r"(?<![A-Za-z])\d+(?:[.,]\d+)?%?(?![A-Za-z])",s)
    prot=[]
    for m in re.finditer(r"(?<![A-Za-z0-9])(?:[A-Z]{2,}[A-Z0-9]*|ffmpeg|Chromaprint|Soulseek|Spotify|YouTube|Pushbullet|Matrix|WebSocket|OpenAI)(?![A-Za-z0-9])",s):
        if m.group(0) not in prot:prot.append(m.group(0))
    return ph,tags,nums,prot
def main():
    assert run("git","rev-parse","HEAD")==HEAD and run("git","rev-parse","HEAD^{tree}")==TREE and not run("git","status","--porcelain=v1")
    rem=run("git","ls-remote","origin",f"refs/heads/{BRANCH}","refs/pull/204/head").splitlines()
    assert rem==[f"{HEAD}\trefs/heads/{BRANCH}",f"{HEAD}\trefs/pull/204/head"],rem
    pr=json.loads(run("gh","pr","view","204","--repo","snapetech-org/slskR","--json","state,isDraft,headRefName,headRefOid,baseRefName,baseRefOid,url"))
    assert pr["state"]=="OPEN" and pr["isDraft"] and pr["headRefOid"]==HEAD and pr["headRefName"]==BRANCH and pr["baseRefName"]=="main" and pr["baseRefOid"]==BASE_SHA
    att={"repository":"snapetech-org/slskR","pullRequest":204,"state":"OPEN","draft":True,"branch":BRANCH,"head":HEAD,"tree":TREE,"baseRef":"main","baseSha":BASE_SHA,"branchRef":HEAD,"pullRef":HEAD,"attestedAtUtc":datetime.datetime.now(datetime.timezone.utc).isoformat(),"method":"live gh PR fields, exact local git head/tree/status, and remote branch/pull refs"}
    wj(INP/"PR-attestation.json",att)
    check_sums(PREV)
    pm=rj(PREV/"manifest.json"); assert pm["selectedPositions"]==[1423,1442]
    oldline=rj(PREV/"source-order-lineage.json")
    priorarts=oldline["priorSelectionArtifacts"][:]
    priorarts.append({"window":"W1423-W1442","path":"docs/pr-evidence/pr204-localization-2026-11-03/window-1423-1442/candidate-free-input","head":pm["head"],"tree":pm["tree"],"manifestSha256":sha((PREV/"manifest.json").read_bytes()),"checksumListSha256":sha((PREV/"SHA256SUMS.txt").read_bytes()),"sourceQueueSha256":pm["sourceQueueFileSha256"],"sourceLookupKeyOrderSha256":pm["sourceLookupKeyOrderSha256"],"selectedPositions":pm["selectedPositions"]})
    cats={}; keys_by={}; catmeta={}
    for loc in LOCALES:
        path=f"web/src/lib/locales/ui-labels.{loc}.json";raw=(REPO/path).read_bytes();d=json.loads(raw.decode(),object_pairs_hook=dict)
        cats[loc]=(d,path);keys_by[loc]=list(d)
        catmeta[loc]={"path":path,"byteCount":len(raw),"lineCount":len(raw.splitlines()),"sha256":sha(raw),"gitBlob":blob(path),"keyCount":len(d),"orderedKeySha256":orderhash(list(d))}
    assert all(keys_by[x]==keys_by[LOCALES[0]] for x in LOCALES)
    keys=sorted(keys_by[LOCALES[0]]);assert len(keys)==5441 and len(set(keys))==5441
    sh=orderhash(keys);assert [x["sourceKey"] for x in rjl(PREV/"source-queue.jsonl")]==keys and sh==pm["sourceLookupKeyOrderSha256"]
    queue=[{"position":i+1,"sourceKey":k,"sourceKeySha256":ht(k),"historicalSourceOrdinal":None} for i,k in enumerate(keys)]
    wjl(INP/"source-queue.jsonl",queue)
    selected=queue[START-1:END];assert len(selected)==20
    (INP/"selected-source-keys.txt").write_text("".join(q["sourceKey"]+"\n" for q in selected),encoding="utf-8")
    bounds=[(START-1,"previous-boundary-W1423-W1442"),*[(p,"selected-W1443-W1462") for p in range(START,END+1)],(END+1,"next-boundary-W1443-W1462")]
    wjl(INP/"source-window-boundaries.jsonl",[{"position":p,"sourceKey":queue[p-1]["sourceKey"],"sourceKeySha256":queue[p-1]["sourceKeySha256"],"historicalSourceOrdinal":None,"role":role} for p,role in bounds])
    oldholds=rjl(PREV/"prior-hold-reattestation.jsonl")
    assert len(oldholds)==35 and all(r["reattestation"]=="same" for r in oldholds)
    needed={q["sourceKey"] for q in selected}|{r["sourceKey"] for r in oldholds}
    tracked=run("git","ls-files","-z").split("\0"); files=[]
    for rel in tracked:
        p=Path(rel)
        if not (rel.startswith("src/") or rel.startswith("web/src/")) or p.suffix.lower() not in {".js",".jsx",".ts",".tsx"}:continue
        if any(x.lower() in {"test","tests","__tests__","fixtures","storybook"} for x in p.parts) or p.name.lower().endswith((".test.js",".test.jsx",".test.ts",".test.tsx",".spec.js",".spec.jsx",".spec.ts",".spec.tsx")):continue
        files.append(rel)
    hits=defaultdict(list);filepins={}
    for rel in sorted(set(files)):
        raw=(REPO/rel).read_bytes()
        try:s=raw.decode()
        except UnicodeDecodeError:continue
        found=defaultdict(list)
        for val,offset in literals(s):
            if val in needed:found[val].append(s.count("\n",0,offset)+1)
        if not found:continue
        digest=sha(raw);gb=blob(rel);lines=s.splitlines()
        filepins[rel]={"path":rel,"byteCount":len(raw),"lineCount":len(lines),"sha256":digest,"gitBlob":gb}
        for key,lns in found.items():
            for ln,n in sorted(Counter(lns).items()):
                a=max(1,ln-4);b=min(len(lines),ln+4);context=[{"line":i,"lineSha256":ht(lines[i-1]),"text":lines[i-1]} for i in range(a,b+1)]
                hits[key].append({"path":rel,"fileSha256":digest,"gitBlob":gb,"line":ln,"lineSha256":ht(lines[ln-1]),"lineText":lines[ln-1],"literalOccurrenceCount":n,"contextStartLine":a,"contextEndLine":b,"context":context,"contextSha256":ht(canon(context))})
    for k in hits:hits[k].sort(key=lambda x:(x["path"],x["line"]))
    def context(pos,key):
        call=hits.get(key,[])
        row={"position":pos,"sourceKey":key,"sourceKeySha256":ht(key),"historicalSourceOrdinal":None,"productionCallerCount":len(call),"callerOccurrenceCount":sum(x["literalOccurrenceCount"] for x in call),"callerScan":"exact quoted JS/TS string-literal search in pinned tracked production src/ and web/src/; tests, catalogs, docs, fixtures, Storybook excluded","callers":call}
        row["callerContextSha256"]=ht(canon({"sourceKey":key,"callers":call}));return row
    contexts=[context(q["position"],q["sourceKey"]) for q in selected];wjl(INP/"source-contexts.jsonl",contexts)
    callerless=[r for r in contexts if not r["callers"]]
    wjl(INP/"caller-resolution-holds.jsonl",[{"position":r["position"],"sourceKey":r["sourceKey"],"sourceKeySha256":r["sourceKeySha256"],"reason":"No exact quoted production caller was found at the pinned head; all locale cells remain held pending caller resolution."} for r in callerless])
    runtime_path="web/src/lib/interfaceLocale.js";runtime_raw=(REPO/runtime_path).read_bytes();rt=runtime_raw.decode();rtlines=rt.splitlines()
    runtime={"path":runtime_path,"byteCount":len(runtime_raw),"lineCount":len(rtlines),"sha256":sha(runtime_raw),"gitBlob":blob(runtime_path)}
    windows=[]
    for marker in ["export const INTERFACE_LANGUAGE_OPTIONS","const translationFor =","const replaceInterfaceValues =","const formatInterfaceTextForLanguage ="]:
        found=[i for i,l in enumerate(rtlines) if marker in l]
        if found:
            i=found[0];a=max(0,i-1);b=min(len(rtlines),i+10)
            windows.append({"marker":marker,"startLine":a+1,"endLine":b,"lines":[{"line":j+1,"lineSha256":ht(rtlines[j]),"text":rtlines[j]} for j in range(a,b)]})
    wj(INP/"localization-runtime-context.json",{"path":runtime_path,"pin":runtime,"localeOptionOrder":["en",*LOCALES],"lookupAndPlaceholderContext":windows,"note":"Locale lookup uses the selected browser-local catalog, English fallback, and named placeholders; user/API values remain opaque."})
    qsha=sha((INP/"source-queue.jsonl").read_bytes())
    pins={"schemaVersion":1,"head":HEAD,"tree":TREE,"sourceLookupKeySetCount":len(keys),"sourceLookupKeyOrderSha256":sh,"sourceQueuePath":"source-queue.jsonl","sourceQueueFileSha256":qsha,"localesInRuntimeOrder":LOCALES,"localeCatalogs":catmeta,"localeRuntime":runtime,"callerFiles":filepins}
    wj(INP/"catalog-file-pins.json",pins);wjl(INP/"catalog-structure.jsonl",[catmeta[x] for x in LOCALES])
    cells=[];mismatch=Counter();ctxby={x["position"]:x for x in contexts}
    for q in selected:
        key=q["sourceKey"];ph,tag,num,prot=tokens(key);cx=ctxby[q["position"]]
        for loc in LOCALES:
            d,path=cats[loc];target=d[key];tph,ttag,tnum,tprot=tokens(target)
            row={"position":q["position"],"historicalSourceOrdinal":None,"sourceKey":key,"sourceKeySha256":q["sourceKeySha256"],"locale":loc,"catalogPath":path,"catalogFileSha256":catmeta[loc]["sha256"],"catalogGitBlob":catmeta[loc]["gitBlob"],"catalogKeyCount":len(d),"currentTarget":target,"currentTargetSha256":ht(target),"callerCount":len(cx["callers"]),"callerRefs":[{"fileSha256":x["fileSha256"],"gitBlob":x["gitBlob"],"line":x["line"],"lineSha256":x["lineSha256"],"path":x["path"]} for x in cx["callers"]],"sourceContextSha256":cx["callerContextSha256"],"sourcePlaceholders":ph,"currentTargetPlaceholders":tph,"sourceMarkupTags":tag,"currentTargetMarkupTags":ttag,"sourceNumericTokens":num,"currentTargetNumericTokens":tnum,"sourceProtectedLiterals":prot,"currentTargetProtectedLiterals":tprot,"protectedLiteralMismatchTokens":[x for x in prot if x not in tprot],"placeholderSequenceMatches":ph==tph,"markupMatches":tag==ttag,"numericTokensMatch":num==tnum,"protectedLiteralsMatch":all(x in tprot for x in prot)}
            mismatch["placeholderSequenceMismatchCount"]+=not row["placeholderSequenceMatches"];mismatch["markupMismatchCount"]+=not row["markupMatches"];mismatch["numericTokenMismatchCount"]+=not row["numericTokensMatch"];mismatch["protectedLiteralMismatchCount"]+=not row["protectedLiteralsMatch"]
            cells.append(row)
    wjl(INP/"current-target-cells.jsonl",cells)
    holds=[]
    for h in oldholds:
        loc=h["locale"];key=h["sourceKey"];pos=h["position"];target=cats[loc][0][key];cx=context(pos,key)
        holds.append({"kind":"carry-forward-hold","window":h.get("window"),"position":pos,"sourceKey":key,"sourceKeySha256":ht(key),"locale":loc,"disposition":"hold","reason":h["reason"],"priorCurrentTarget":h["currentTarget"],"priorCurrentTargetSha256":h["currentTargetSha256"],"currentTarget":target,"currentTargetSha256":ht(target),"currentCatalogPath":cats[loc][1],"currentCatalogSha256":catmeta[loc]["sha256"],"currentCatalogGitBlob":catmeta[loc]["gitBlob"],"reattestation":"same" if target==h["currentTarget"] and ht(target)==h["currentTargetSha256"] else "changed","priorCallerCount":h.get("priorCallerCount"),"currentCallerCount":len(cx["callers"]),"currentCallerContextSha256":cx["callerContextSha256"],"priorHoldEntrySha256":ht(canon(h))})
    assert len(holds)==35 and len({(x["position"],x["locale"]) for x in holds})==35
    assert all(x["reattestation"]=="same" for x in holds),[(x["position"],x["locale"]) for x in holds if x["reattestation"]!="same"]
    wjl(INP/"prior-hold-reattestation.jsonl",holds)
    prior=[];artmeta=[]
    for art in priorarts:
        folder=REPO/art["path"];check_sums(folder);mf=rj(folder/"manifest.json");qrows=rjl(folder/"source-queue.jsonl")
        assert sha((folder/"manifest.json").read_bytes())==art["manifestSha256"] and sha((folder/"SHA256SUMS.txt").read_bytes())==art["checksumListSha256"]
        assert sha((folder/"source-queue.jsonl").read_bytes())==mf["sourceQueueFileSha256"]==art["sourceQueueSha256"]
        assert mf["sourceLookupKeyOrderSha256"]==sh
        lo,hi=mf["selectedPositions"];artmeta.append({"window":art["window"],"path":art["path"],"head":mf["head"],"tree":mf["tree"],"manifestSha256":art["manifestSha256"],"checksumListSha256":art["checksumListSha256"],"sourceQueueSha256":mf["sourceQueueFileSha256"],"sourceLookupKeyOrderSha256":sh,"selectedPositions":mf["selectedPositions"]})
        for pos in range(lo,hi+1):
            a=qrows[pos-1];b=queue[pos-1]
            prior.append({"priorWindow":art["window"],"priorInputPath":art["path"],"priorHead":mf["head"],"priorTree":mf["tree"],"priorManifestSha256":art["manifestSha256"],"priorChecksumListSha256":art["checksumListSha256"],"priorSourceQueueSha256":mf["sourceQueueFileSha256"],"position":pos,"priorSourceKey":a["sourceKey"],"priorSourceKeySha256":a["sourceKeySha256"],"currentQueueSourceKey":b["sourceKey"],"currentQueueSourceKeySha256":b["sourceKeySha256"],"selectionMatchesCurrentQueue":a["sourceKey"]==b["sourceKey"] and a["sourceKeySha256"]==b["sourceKeySha256"]==ht(b["sourceKey"])})
    assert len(prior)==200 and len({x["position"] for x in prior})==200 and all(x["selectionMatchesCurrentQueue"] for x in prior)
    assert not {x["position"] for x in prior}&set(range(START,END+1))
    wjl(INP/"prior-selection-reattestation.jsonl",prior)
    qpath="docs/pr-evidence/pr204-localization-2026-11-03/window-1423-1442/candidate-free-input/source-queue.jsonl"
    assert run("git","show",f"{HEAD}:{qpath}").strip()==(INP/"source-queue.jsonl").read_text().strip()
    lineage={"selectionRule":"One-based positions in exact Unicode lexicographic order of all current English source lookup keys shared by twelve locale catalogs.","currentWindow":"W1443-W1462","currentSelectedPositions":[START,END],"previousBoundaryPosition":START-1,"nextBoundaryPosition":END+1,"previousCandidateFreeWindow":"W1423-W1442","previousCandidateFreeHead":pm["head"],"previousCandidateFreeTree":pm["tree"],"previousCandidateFreeManifestSha256":sha((PREV/"manifest.json").read_bytes()),"previousCandidateFreeChecksumListSha256":sha((PREV/"SHA256SUMS.txt").read_bytes()),"previousSourceQueueSha256":pm["sourceQueueFileSha256"],"previousWindowSelectedPositions":pm["selectedPositions"],"previousWindowNextBoundaryPosition":pm["nextBoundaryPosition"],"currentHeadCommittedSourceQueuePath":qpath,"currentHeadCommittedSourceQueueBlob":blob(qpath),"currentHeadCommittedSourceQueueMatchesCurrentQueue":True,"liveCatalogSourceKeySetCount":len(keys),"liveCatalogSourceKeyOrderSha256":sh,"liveCatalogOrderMatchesPreviousQueue":True,"priorSelectionWindowCount":len(artmeta),"priorSelectedSourceCount":len(prior),"priorSelectionsAllMatchCurrentQueue":True,"priorSelectionArtifacts":artmeta,"firstSelected":{"position":START,"sourceKey":queue[START-1]["sourceKey"],"sourceKeySha256":queue[START-1]["sourceKeySha256"],"historicalSourceOrdinal":None},"lastSelected":{"position":END,"sourceKey":queue[END-1]["sourceKey"],"sourceKeySha256":queue[END-1]["sourceKeySha256"],"historicalSourceOrdinal":None},"previousBoundary":{"position":START-1,"sourceKey":queue[START-2]["sourceKey"],"sourceKeySha256":queue[START-2]["sourceKeySha256"]},"nextBoundary":{"position":END+1,"sourceKey":queue[END]["sourceKey"],"sourceKeySha256":queue[END]["sourceKeySha256"]},"historicalSourceOrdinalsClaimed":False}
    wj(INP/"source-order-lineage.json",lineage)
    readme="""# slskR PR #204 W1443-W1462 candidate-free exact-head input

Pinned to the OPEN/DRAFT PR head and tree in PR-attestation.json. This packet contains the current 5,441-key source queue, exact production callers, twelve locale catalog/runtime hashes, and 240 current target cells for 20 sources by 12 locales. It includes no proposed translations or semantic decisions.

Selected positions are 1443-1462; position 1442 is the previous boundary and 1463 is the next boundary. Caller scanning searched exact quoted literals in tracked production JS/TS under src/ and web/src/, excluding tests, catalogs, docs, fixtures, and Storybook. Caller contexts include source line and nearby context hashes, file hashes, and Git blob IDs.

All 35 carried holds are reattested against current targets. The 200 previously selected source keys across ten windows still match their exact source queue positions. Callerless or ambiguous entries remain held.

Run python3 verify-candidate-free.py and sha256sum -c SHA256SUMS.txt from this directory.
"""
    (INP/"README.md").write_text(readme,encoding="utf-8")
    filehash={p.name:{"sha256":sha(p.read_bytes()),"byteCount":p.stat().st_size} for p in sorted(INP.iterdir()) if p.is_file() and p.name not in {"manifest.json","SHA256SUMS.txt"}}
    mm={"placeholderSequenceMismatchCount":mismatch["placeholderSequenceMismatchCount"],"markupMismatchCount":mismatch["markupMismatchCount"],"numericTokenMismatchCount":mismatch["numericTokenMismatchCount"],"protectedLiteralMismatchCount":mismatch["protectedLiteralMismatchCount"]}
    manifest={"artifact":"slskR PR #204 W1443-W1462 candidate-free exact-head input","repository":"snapetech-org/slskR","pullRequest":204,"head":HEAD,"tree":TREE,"headRef":BRANCH,"baseRef":"main","baseSha":BASE_SHA,"draft":True,"candidateFreeInputOnly":True,"proposedTranslationsIncluded":False,"selectedPositions":[START,END],"previousBoundaryPosition":START-1,"nextBoundaryPosition":END+1,"sourceCount":20,"localeCount":12,"cellCount":240,"catalogSourceCount":len(keys),"localeOrder":LOCALES,"sourceLookupKeyOrderSha256":sh,"sourceQueueFile":"source-queue.jsonl","sourceQueueFileSha256":sha((INP/"source-queue.jsonl").read_bytes()),"callerReferenceCount":sum(x["productionCallerCount"] for x in contexts),"callerOccurrenceCount":sum(x["callerOccurrenceCount"] for x in contexts),"callerFileCount":len(filepins),"callerResolutionHoldCount":len(callerless),"callerResolutionHoldPositions":[x["position"] for x in callerless],"carryForwardHoldCount":len(holds),"carryForwardHoldUnchangedCount":len(holds),"carryForwardHoldChangedCount":0,"priorSelectionReattestationCount":len(prior),"priorSelectionWindowCount":len(artmeta),"historicalSourceOrdinalsClaimed":False,"sourceOrderLineageFile":"source-order-lineage.json","localizationRuntimeContextFile":"localization-runtime-context.json","sourceQueueCount":len(queue),"catalogFilesPinned":len(catmeta),"mismatchCounts":mm,**mm,"localWorktree":str(REPO),"localWorktreeHead":HEAD,"localWorktreeTree":TREE,"localWorktreeBranch":run("git","branch","--show-current") or "detached","localWorktreeStatusClean":True,"fileHashes":filehash,"createdAtUtc":datetime.datetime.now(datetime.timezone.utc).isoformat()}
    wj(INP/"manifest.json",manifest)
    files=sorted(x for x in INP.iterdir() if x.is_file() and x.name!="SHA256SUMS.txt")
    (INP/"SHA256SUMS.txt").write_text("".join(f"{sha(p.read_bytes())}  {p.name}\n" for p in files),encoding="utf-8")
    print(json.dumps({"built":True,"output":str(INP),"head":HEAD,"tree":TREE,"positions":[START,END],"sourceKeys":[x["sourceKey"] for x in selected],"cells":len(cells),"callerlessPositions":[x["position"] for x in callerless],"carryForwardHolds":len(holds),"priorSelectionsReattested":len(prior),"catalogFilesPinned":len(catmeta),"callerFilesPinned":len(filepins),"mismatchCounts":mm},ensure_ascii=False,indent=2))
if __name__=="__main__":main()
