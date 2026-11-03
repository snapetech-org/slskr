#!/usr/bin/env python3
import hashlib,json,re,subprocess
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parent

def fail(msg): raise SystemExit("FAIL: "+msg)
def need(ok,msg):
    if not ok: fail(msg)
def sha(b): return hashlib.sha256(b).hexdigest()
def sha_text(s): return sha(s.encode("utf-8"))
def readj(p): return json.loads(p.read_text(encoding="utf-8"))
def readjl(p): return [json.loads(x) for x in p.read_text(encoding="utf-8").splitlines() if x.strip()]
def verify_sums(folder):
    sums=folder/"SHA256SUMS.txt"
    need(sums.is_file(),"missing checksum list "+str(sums))
    entries={}
    for line in sums.read_text(encoding="utf-8").splitlines():
        if not line: continue
        need(len(line)>=66 and line[64:66]=="  ","malformed checksum line")
        digest=line[:64]; name=line[66:].lstrip("*")
        need(name not in entries,"duplicate checksum entry "+name)
        path=folder/name
        need(path.is_file() and sha(path.read_bytes())==digest,"checksum mismatch "+name)
        entries[name]=digest
    actual={p.relative_to(folder).as_posix() for p in folder.rglob("*") if p.is_file() and p.name!="SHA256SUMS.txt"}
    need(set(entries)==actual,"checksum coverage mismatch for "+str(folder))
    return len(entries)
PH=re.compile(r"\{[A-Za-z][A-Za-z0-9_]*\}")
TAG=re.compile(r"</?[A-Za-z][^>]*>")
NUM=re.compile(r"(?<![A-Za-z])\d+(?:[.,]\d+)?%?(?![A-Za-z])")
PROT=re.compile(r"(?<![A-Za-z0-9])(?:[A-Z]{2,}[A-Z0-9]*|ffmpeg|Chromaprint|Soulseek|Spotify|YouTube|Pushbullet|Matrix|WebSocket|OpenAI)(?![A-Za-z0-9])")
def tok(s):
    return {"placeholders":PH.findall(s),"markupTags":TAG.findall(s),"numericTokens":NUM.findall(s),"protectedLiterals":list(dict.fromkeys(m.group(0) for m in PROT.finditer(s)))}

def main():
    packet_files=verify_sums(ROOT)
    cf=ROOT/"evidence/candidate-free-input"
    cf_files=verify_sums(cf)
    im=readj(cf/"manifest.json");m=readj(ROOT/"manifest.json")
    head="44b37bd94385128d5bb5287aa1545901282bdfcb";tree="02c3f149a079c67b010d973dd02ca15776ad1610"
    need(im["head"]==m["head"]==head,"exact PR head mismatch")
    need(im["tree"]==m["tree"]==tree,"exact tree mismatch")
    need(im["selectedPositions"]==[1443,1462] and m["window"]=="W1443-W1462","window selection mismatch")
    need(im["candidateFreeInputOnly"] is True and im["proposedTranslationsIncluded"] is False,"candidate-free boundary mismatch")
    need(m["candidateFreeInputManifestSha256"]==sha((cf/"manifest.json").read_bytes()),"candidate-free manifest pin mismatch")
    need(m["candidateFreeInputChecksumListSha256"]==sha((cf/"SHA256SUMS.txt").read_bytes()),"candidate-free checksum-list pin mismatch")
    need(m["branch"]==im["headRef"]=="codex/slskr-l10n-audit-20261030","branch pin mismatch")
    need(m["baseRef"]==im["baseRef"]=="main" and m["baseSha"]==im["baseSha"]=="2a2b188f10b9460a15bc6d5c34e406b0193d51ba","base-ref pin mismatch")
    # Re-run the exact-input portable verifier embedded with the candidate-free packet.
    subprocess.check_call(["python3",str(cf/"verify-candidate-free.py")],stdout=subprocess.DEVNULL)
    att=readj(cf/"PR-attestation.json"); after=readj(cf/"PR-attestation-after.json")
    need(att["head"]==head and att["tree"]==tree and att["state"]=="OPEN" and att["draft"] is True,"before live attestation mismatch")
    need(att["branchRef"]==head and att["pullRef"]==head,"before refs mismatch")
    need(after["head"]==head and after["tree"]==tree and after["state"]=="OPEN" and after["draft"] is True,"after live attestation mismatch")
    need(after["branchRef"]==head and after["pullRef"]==head and after["sourcePinCount"]==29 and after["all240CatalogTargetsReattested"] is True,"after refs/source-pin attestation mismatch")
    pins=readj(cf/"catalog-file-pins.json")
    expected={}
    for loc,x in pins["localeCatalogs"].items(): expected[x["path"]]=(x["sha256"],x["gitBlob"],"locale-catalog")
    x=pins["localeRuntime"];expected[x["path"]]=(x["sha256"],x["gitBlob"],"locale-runtime")
    for path,x in pins["callerFiles"].items(): expected[path]=(x["sha256"],x["gitBlob"],"production-caller")
    observed=after.get("sourcePins",{})
    need(set(observed)==set(expected),"source-pin path coverage mismatch")
    for path,(digest,blob,kind) in expected.items():
        item=observed[path]
        need((item.get("sha256"),item.get("gitBlob"),item.get("kind"))==(digest,blob,kind),"source/catalog pin mismatch "+path)
    live=readj(ROOT/"live-pr-attestation.json")
    for stage in ("observedBefore","observedAfter"):
        o=live[stage]
        need(o["state"]=="OPEN" and o["isDraft"] is True and o["branch"]==m["branch"] and o["head"]==head and o["headTree"]==tree and o["liveBranchRef"]==head and o["livePullRef"]==head and o["checkoutWorktreeClean"] is True and o["checkoutHead"]==head and o["checkoutTree"]==tree,"live pin mismatch "+stage)
    base_rows={(r["position"],r["locale"]):r for r in readjl(cf/"current-target-cells.jsonl")}
    rows=readjl(ROOT/"cell-review.jsonl")
    need(len(base_rows)==len(rows)==240,"240-cell coverage mismatch")
    need(len({(r["position"],r["locale"]) for r in rows})==240,"duplicate review cell")
    counts=Counter();changed=[]
    for d in rows:
        k=(d["position"],d["locale"]);need(k in base_rows,"unexpected cell "+str(k));b=base_rows[k]
        for a,z in [("sourceKey","sourceKey"),("sourceKeySha256","sourceKeySha256"),("currentTarget","currentTarget"),("currentTargetSha256","currentTargetSha256"),("sourceContextSha256","sourceContextSha256"),("callerCount","callerCount"),("callerRefs","callerRefs")]:
            need(d.get(a)==b.get(z),a+" mismatch "+str(k))
        need(d["sourceKeySha256"]==sha_text(d["sourceKey"]),"source hash mismatch "+str(k))
        need(d["currentTargetSha256"]==sha_text(d["currentTarget"]),"current hash mismatch "+str(k))
        need(d["callerCount"]==len(d["callerRefs"]),"caller count mismatch "+str(k))
        need(isinstance(d.get("reviewReason"),str) and d["reviewReason"].strip(),"missing rationale "+str(k))
        need(d.get("confidence") in ("high","moderate","low"),"confidence missing "+str(k))
        source=tok(d["sourceKey"]);current=tok(d["currentTarget"]);tc=d["tokenChecks"]
        cur_missing=[x for x in source["protectedLiterals"] if x not in current["protectedLiterals"]]
        need(tc["sourcePlaceholders"]==source["placeholders"] and tc["currentPlaceholders"]==current["placeholders"],"current placeholder record mismatch "+str(k))
        need(tc["sourceMarkupTags"]==source["markupTags"] and tc["currentMarkupTags"]==current["markupTags"],"current markup record mismatch "+str(k))
        need(tc["sourceNumericTokens"]==source["numericTokens"] and tc["currentNumericTokens"]==current["numericTokens"],"current numeric record mismatch "+str(k))
        need(tc["protectedLiterals"]==source["protectedLiterals"] and tc["currentProtectedLiterals"]==current["protectedLiterals"] and tc["currentMissingProtectedLiterals"]==cur_missing,"current protected-literal record mismatch "+str(k))
        current_pass=(source["placeholders"]==current["placeholders"] and source["markupTags"]==current["markupTags"] and source["numericTokens"]==current["numericTokens"] and not cur_missing)
        need(tc["currentChecksPass"]==current_pass,"current check status mismatch "+str(k))
        disp=d["disposition"];counts[disp]+=1
        need(disp in ("accept-current","correction","refinement","hold"),"invalid disposition "+str(k))
        proposed=d.get("proposedTarget")
        if proposed is None:
            need(d.get("proposedTargetSha256") is None and disp in ("accept-current","hold"),"missing-target disposition mismatch "+str(k))
            need(current_pass,"current token mismatch cannot be accepted/held without explicit evidence "+str(k))
            need(tc["proposedChecksPass"] is True and tc["proposedMissingProtectedLiterals"]==[],"no-op token record mismatch "+str(k))
        else:
            need(disp in ("correction","refinement"),"proposal has invalid disposition "+str(k))
            need(d["proposedTargetSha256"]==sha_text(proposed),"proposal hash mismatch "+str(k))
            pt=tok(proposed);missing=[x for x in source["protectedLiterals"] if x not in pt["protectedLiterals"]]
            need(tc["proposedPlaceholders"]==pt["placeholders"] and source["placeholders"]==pt["placeholders"],"proposal placeholders mismatch "+str(k))
            need(tc["proposedMarkupTags"]==pt["markupTags"] and source["markupTags"]==pt["markupTags"],"proposal markup mismatch "+str(k))
            need(tc["proposedNumericTokens"]==pt["numericTokens"] and source["numericTokens"]==pt["numericTokens"],"proposal numeric mismatch "+str(k))
            need(tc["proposedProtectedLiterals"]==pt["protectedLiterals"] and tc["proposedMissingProtectedLiterals"]==missing and not missing,"proposal protected literals mismatch "+str(k))
            need(tc["proposedChecksPass"] is True,"proposal check status mismatch "+str(k))
            if cur_missing:
                need(proposed is not None,"baseline protected literal left unresolved "+str(k))
            changed.append(d)
    need(counts==m["decisionCounts"],"decision counts mismatch")
    need(len(changed)==m["proposedTargetCount"],"proposal count mismatch")
    need(counts["hold"]==m["currentWindowHoldCount"]==0,"unexpected current holds")
    need(m["callerResolutionHoldCount"]==0,"unexpected caller-resolution holds")
    need(sum(not r["tokenChecks"]["currentChecksPass"] for r in rows)==m["reconciledProtectedLiteralBaselineCells"]==9,"baseline protected literal count mismatch")
    need(sum(bool(r["tokenChecks"]["currentMissingProtectedLiterals"]) and r["tokenChecks"]["proposedChecksPass"] for r in rows)==9,"baseline protected literal reconciliation count mismatch")
    summary=readj(ROOT/"change-summary.json")
    want=[(d["position"],d["locale"],d["currentTargetSha256"],d["proposedTargetSha256"]) for d in changed]
    got=[(d["position"],d["locale"],d["currentTargetSha256"],d["proposedTargetSha256"]) for d in summary["changes"]]
    need(summary["changeCount"]==len(changed) and got==want,"change summary exact targets mismatch")
    notes=readj(ROOT/"source-context-notes.json")
    need(notes["head"]==head and notes["tree"]==tree and notes["callerlessPositions"]==[],"source-context notes pin mismatch")
    need(len(notes["sources"])==20,"source-context note coverage mismatch")
    for d in rows:
        need(d["callerContextSummary"]==notes["sources"][str(d["position"])],"source-context rationale mismatch")
    for name,count in [("prior-hold-reattestation.jsonl",35),("prior-selection-reattestation.jsonl",200)]:
        a=(ROOT/name).read_bytes();b=(cf/name).read_bytes()
        need(a==b,"carried evidence copy mismatch "+name)
        prior=[json.loads(x) for x in a.decode("utf-8").splitlines() if x]
        need(len(prior)==count,"carried evidence count mismatch "+name)
        if name.startswith("prior-hold"):
            need(all(x["reattestation"]=="same" and x["currentTargetSha256"]==x["priorCurrentTargetSha256"] for x in prior),"carried hold changed")
        else:
            need(all(x["selectionMatchesCurrentQueue"] for x in prior),"prior selection changed")
    # Count and compare the candidate-free baseline mismatch records against the ledger.
    baseline=im["mismatchCounts"]
    need(baseline["placeholderSequenceMismatchCount"]==0 and baseline["markupMismatchCount"]==0 and baseline["numericTokenMismatchCount"]==0 and baseline["protectedLiteralMismatchCount"]==9,"baseline token mismatch counts differ")
    print(json.dumps({"result":"PASS","head":head,"tree":tree,"cells":len(rows),"decisionCounts":dict(counts),"proposals":len(changed),"candidateFreeFilesChecked":cf_files,"primaryFilesChecked":packet_files,"sourcePinsReattested":after["sourcePinCount"],"callerReferences":im["callerReferenceCount"],"carriedHolds":35,"priorSelections":200,"baselineProtectedLiteralCells":9,"protectedLiteralCorrections":9},ensure_ascii=False,indent=2))

if __name__=="__main__":
    main()
