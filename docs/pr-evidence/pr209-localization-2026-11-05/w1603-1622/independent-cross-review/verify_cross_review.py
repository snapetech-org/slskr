#!/usr/bin/env python3
"""Portable integrity and input-binding verifier for the independent cross-review."""
from __future__ import annotations
import hashlib, json, re
from collections import Counter
from pathlib import Path

OUT = Path(__file__).resolve().parent
TASK = OUT.parent
INPUT, PRIMARY, BLIND, ROOT = (TASK / name for name in ("candidate-free-input", "primary-review", "blind-review", "root-cross-review"))
HEAD = "eeb63f1e4e21d801f4a4e0393813b6e86a1ff7c8"
TREE = "590ee410666905f68f601393b64a4798b0609181"
LOCALES = ["es", "zh-Hans", "hi", "de", "ja", "fr", "pt-BR", "ar", "ko", "zh-Hant", "vi", "id"]
START, END = 1603, 1622
PH = re.compile(r"\{[^{}]+\}")
TAG = re.compile(r"</?[A-Za-z][^>]*>")
NUM = re.compile(r"(?<!\w)\d+(?:[.,]\d+)*(?!\w)")

def fail(msg): raise SystemExit("FAIL: " + msg)
def sha(x): return hashlib.sha256(x.encode("utf-8") if isinstance(x,str) else x).hexdigest()
def read_json(p): return json.loads(p.read_text(encoding="utf-8"))
def read_jsonl(p): return [json.loads(line) for line in p.read_text(encoding="utf-8").splitlines() if line.strip()]
def tokens(source, target, protected):
    return {
        "placeholderSequencePreserved": PH.findall(source) == PH.findall(target),
        "markupPreserved": TAG.findall(source) == TAG.findall(target),
        "numericTokensPreserved": NUM.findall(source) == NUM.findall(target),
        "protectedLiteralsPreserved": all(literal in target for literal in protected),
    }
def check_sums(path):
    sums_path=path/"SHA256SUMS.txt"; listed={}
    for line in sums_path.read_text(encoding="utf-8").splitlines():
        if not line.strip(): continue
        digest,name=line.split("  ",1)
        if name in listed: fail(f"duplicate checksum {path.name}/{name}")
        file=(path/name).resolve()
        if not file.is_relative_to(path.resolve()) or not file.is_file() or sha(file.read_bytes())!=digest: fail(f"checksum {path.name}/{name}")
        listed[name]=digest
    actual={p.relative_to(path).as_posix() for p in path.rglob("*") if p.is_file() and p!=sums_path}
    if set(listed)!=actual: fail(f"checksum coverage {path.name}")
    return listed

def verify():
    outer=check_sums(OUT)
    input_sums={name:check_sums(path) for name,path in (("candidateFree",INPUT),("primary",PRIMARY),("blind",BLIND),("rootCrossReview",ROOT))}
    summary=read_json(OUT/"SUMMARY.json")
    if (summary.get("head"),summary.get("tree"),summary.get("window"),summary.get("cellCount"))!=(HEAD,TREE,"W1603-W1622",240): fail("summary pin/cardinality")
    for name,path in (("candidateFree",INPUT),("primary",PRIMARY),("blind",BLIND),("rootCrossReview",ROOT)):
        record=summary.get("inputPins",{}).get(name,{})
        if record.get("checksumListSha256")!=sha((path/"SHA256SUMS.txt").read_bytes()) or record.get("fileCount")!=len(input_sums[name]): fail("summary input pin "+name)
    cells=read_jsonl(INPUT/"current-target-cells.jsonl"); contexts=read_jsonl(INPUT/"source-contexts.jsonl")
    primary=read_jsonl(PRIMARY/"primary-ledger.jsonl"); blind=read_jsonl(BLIND/"blind-ledger.jsonl")
    root=read_jsonl(ROOT/"root-adjudication.jsonl"); rows=read_jsonl(OUT/"cross-review-ledger.jsonl")
    disagreements=read_jsonl(OUT/"root-disagreements.jsonl")
    if len(cells)!=240 or len(primary)!=240 or len(blind)!=240 or len(root)!=240 or len(rows)!=240 or len(contexts)!=20: fail("packet cardinality")
    expected=[(pos,loc) for pos in range(START,END+1) for loc in LOCALES]
    maps=[]
    for records in (cells,primary,blind,root,rows):
        mapping={(r["position"],r["locale"]):r for r in records}
        if len(mapping)!=240 or set(mapping)!=set(expected): fail("unique complete cell coverage")
        maps.append(mapping)
    cell_by,p_by,b_by,r_by,x_by=maps
    ctx_by={r["position"]:r for r in contexts}
    if len(ctx_by)!=20: fail("source-context uniqueness")
    counts=Counter(); root_counts=Counter(); observed_disagreements=[]
    for key in expected:
        c,p,b,r,x=cell_by[key],p_by[key],b_by[key],r_by[key],x_by[key]
        ctx=ctx_by[key[0]]
        if not (c["sourceKeySha256"]==p["sourceKeySha256"]==b["sourceKeySha256"]==r["sourceKeySha256"]==x["sourceKeySha256"]==ctx["sourceKeySha256"]): fail("source hash binding "+str(key))
        if not (c["sourceContextSha256"]==p["sourceContextSha256"]==b["sourceContextSha256"]==r["sourceContextSha256"]==x["sourceContextSha256"]==ctx["callerContextSha256"]): fail("caller context binding "+str(key))
        if not (c["currentTargetSha256"]==p["currentTargetSha256"]==b["currentTargetSha256"]==r["currentTargetSha256"]==x["currentTargetSha256"]): fail("current target binding "+str(key))
        if c["currentTargetSha256"]!=sha(c["currentTarget"]) or x["crossTargetSha256"]!=sha(x["crossTarget"]): fail("text hash "+str(key))
        if x["currentTarget"]!=c["currentTarget"] or x["sourceKey"]!=c["sourceKey"]: fail("review source/current binding "+str(key))
        if x["callerCount"]!=ctx["productionCallerCount"] or x["head"]!=HEAD or x["tree"]!=TREE: fail("head/caller count "+str(key))
        if (x["primaryDisposition"],x["primaryTarget"])!=(p["disposition"],p["selectedTarget"]): fail("primary linkage "+str(key))
        if (x["blindDisposition"],x["blindTarget"])!=(b["decision"],b["proposedTarget"]): fail("blind linkage "+str(key))
        if (x["rootDisposition"],x["rootTarget"],x["rootTargetSha256"])!=(r["rootDisposition"],r["rootTarget"],r["rootTargetSha256"]): fail("root linkage "+str(key))
        if x["tokenChecks"]!=tokens(c["sourceKey"],x["crossTarget"],c["sourceProtectedLiterals"]) or not all(x["tokenChecks"].values()): fail("cross target token checks "+str(key))
        if not x["crossRationale"] or x["confidence"] not in {"high","moderate","low","unknown"}: fail("rationale/confidence "+str(key))
        if x["crossDisposition"]=="accept-current":
            if x["crossTarget"]!=c["currentTarget"] or r["rootDisposition"]!="accept-current" or r["rootTarget"]!=c["currentTarget"]: fail("accept-current root decision "+str(key))
        elif x["crossDisposition"] in {"propose-correction","propose-refinement"}:
            kind=x["crossDisposition"].removeprefix("propose-")
            if r["rootDisposition"]!=kind or x["crossTarget"]!=r["rootTarget"]: fail("proposal/root decision "+str(key))
        else: fail("unknown cross disposition "+str(key))
        agreement=(x["crossTarget"]==r["rootTarget"] and ((x["crossDisposition"]=="accept-current" and r["rootDisposition"]=="accept-current") or x["crossDisposition"]=="propose-"+r["rootDisposition"]))
        if x["agreesWithRoot"] is not agreement: fail("root agreement flag "+str(key))
        counts[x["crossDisposition"]]+=1; root_counts[r["rootDisposition"]]+=1
        if not agreement: observed_disagreements.append(x)
    if disagreements!=observed_disagreements: fail("disagreement file content")
    if summary.get("crossDispositionCounts")!=dict(sorted(counts.items())) or summary.get("rootDispositionCounts")!=dict(sorted(root_counts.items())): fail("summary counts")
    if (summary.get("rootOutcomesReviewed"),summary.get("rootAgreements"),summary.get("rootDisagreements"),summary.get("crossProposalCount"))!=(13,240-len(disagreements),len(disagreements),13): fail("summary root review counts")
    if summary.get("currentTargetCellsSha256")!=sha((INPUT/"current-target-cells.jsonl").read_bytes()) or summary.get("sourceContextsSha256")!=sha((INPUT/"source-contexts.jsonl").read_bytes()) or summary.get("rootAdjudicationSha256")!=sha((ROOT/"root-adjudication.jsonl").read_bytes()): fail("summary evidence hashes")
    return {"result":"PASS","head":HEAD,"tree":TREE,"cells":len(rows),"crossDispositionCounts":dict(counts),"rootOutcomesReviewed":13,"rootAgreements":240-len(disagreements),"rootDisagreements":len(disagreements),"inputPacketsVerified":len(input_sums),"artifactFiles":len(outer)}

if __name__=="__main__": print(json.dumps(verify(),ensure_ascii=False,sort_keys=True))
