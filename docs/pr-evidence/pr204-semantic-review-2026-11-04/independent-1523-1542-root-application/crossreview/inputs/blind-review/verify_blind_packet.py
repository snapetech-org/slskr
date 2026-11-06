#!/usr/bin/env python3
"""Standalone verifier for the slskR PR #204 blind review packet."""
import hashlib, json, re
from pathlib import Path

OUT=Path(__file__).resolve().parent
INPUT=Path("/home/keith/Documents/code/task-scratch/slskr-pr204-w1523-1542-primary-20261104/candidate-free-input")
HEAD="f6fbf614e7e2ff869e4ca86ae96103cff604b79c"
TREE="536b0fc02a3c16fa7eb0f9d5504a4c8c91b2152d"
LOCS=["es","zh-Hans","hi","de","ja","fr","pt-BR","ar","ko","zh-Hant","vi","id"]
def sha(data):
    if isinstance(data,str): data=data.encode("utf-8")
    return hashlib.sha256(data).hexdigest()
def j(path): return json.loads(path.read_text(encoding="utf-8"))
def jl(path): return [json.loads(s) for s in path.read_text(encoding="utf-8").splitlines() if s]
def toks(s):
    p=re.findall(r"\{[A-Za-z][A-Za-z0-9_]*\}",s)
    m=re.findall(r"</?[A-Za-z][^>]*>",s)
    n=re.findall(r"(?<![A-Za-z])\d+(?:[.,]\d+)?%?(?![A-Za-z])",s)
    z=[]
    for x in re.findall(r"(?<![A-Za-z0-9])(?:[A-Z]{2,}[A-Z0-9]*|ffmpeg|Chromaprint|Soulseek|Spotify|YouTube|Pushbullet|Matrix|WebSocket|OpenAI)(?![A-Za-z0-9])",s):
        if x not in z: z.append(x)
    return p,m,n,z

m=j(OUT/"manifest.json")
assert m["head"]==HEAD and m["tree"]==TREE
assert m["localeOrder"]==LOCS and m["cellCount"]==240
assert m["reviewBasis"]=="sealed candidate-free input only"
assert m["reviewSha256"]==sha((OUT/"review.jsonl").read_bytes())
assert m["reviewByteCount"]==(OUT/"review.jsonl").stat().st_size

# Verify every sealed input file against its checksum file before relying on it.
sum_rows={}
for line in (INPUT/"SHA256SUMS.txt").read_text(encoding="utf-8").splitlines():
    digest,name=line.split(None,1); name=name.lstrip("* ")
    sum_rows[name]=digest
actual={p.name for p in INPUT.iterdir() if p.is_file() and p.name!="SHA256SUMS.txt"}
assert set(sum_rows)==actual
for name,digest in sum_rows.items(): assert sha((INPUT/name).read_bytes())==digest,name
im=j(INPUT/"manifest.json")
assert im["head"]==HEAD and im["tree"]==TREE
assert im["candidateFreeInputOnly"] is True and im["proposedTranslationsIncluded"] is False
assert im["selectedPositions"]==[1523,1542] and im["sourceCount"]==20
assert im["localeCount"]==12 and im["cellCount"]==240
assert im["mismatchCounts"]=={"placeholderSequenceMismatchCount":0,"markupMismatchCount":0,"numericTokenMismatchCount":0,"protectedLiteralMismatchCount":0}
assert m["inputPins"]["candidateFreeInputManifestSha256"]==sha((INPUT/"manifest.json").read_bytes())
assert m["inputPins"]["candidateFreeInputSha256SumsSha256"]==sha((INPUT/"SHA256SUMS.txt").read_bytes())
assert m["inputPins"]["currentTargetCellsSha256"]==sha((INPUT/"current-target-cells.jsonl").read_bytes())
assert m["inputPins"]["sourceContextsSha256"]==sha((INPUT/"source-contexts.jsonl").read_bytes())
assert m["inputPins"]["priorHoldHashReattestationSha256"]==sha((INPUT/"prior-hold-hash-reattestation.jsonl").read_bytes())
prior_holds=jl(INPUT/"prior-hold-hash-reattestation.jsonl")
assert len(prior_holds)==47
assert not any(1523<=r["position"]<=1542 for r in prior_holds)
assert all(not any(k in r for k in ("sourceKey","currentTarget","target","crossTarget","proposedTarget","source","targetText","lineText")) for r in prior_holds)
assert m["holdReview"]=={"callerResolutionHoldCount":0,"callerResolutionHoldPositions":[],"priorHashOnlyHoldRows":47,"priorHashOnlyHoldRowsInSelectedWindow":0}
assert m["inputPins"]["localizationRuntimeContextSha256"]==sha((INPUT/"localization-runtime-context.json").read_bytes())
src=jl(INPUT/"current-target-cells.jsonl")
contexts={x["position"]:x for x in jl(INPUT/"source-contexts.jsonl")}
rows=jl(OUT/"review.jsonl")
assert len(rows)==240
assert [(r["position"],r["locale"]) for r in rows]==[(p,l) for p in range(1523,1543) for l in LOCS]
expected={(x["position"],x["locale"]):x for x in src}
counts={"accept":0,"revise":0,"hold":0}
for r in rows:
    c=expected[(r["position"],r["locale"])]
    ctx=contexts[r["position"]]
    for k in ("sourceKey","sourceKeySha256","currentTarget","currentTargetSha256","catalogPath","catalogFileSha256","catalogGitBlob","sourceContextSha256","callerCount"):
        assert r[k]==c[k],(r["position"],r["locale"],k)
    assert r["sourceKeySha256"]==sha(r["sourceKey"])
    assert r["currentTargetSha256"]==sha(r["currentTarget"])
    assert r["sourceContextSha256"]==ctx["callerContextSha256"]
    assert r["callerCount"]==ctx["productionCallerCount"]>0
    assert r["disposition"] in counts
    counts[r["disposition"]]+=1
    assert r["confidence"] in ("high","moderate","low")
    assert r["rationale"] and r["proposedTarget"]
    source_tokens=toks(r["sourceKey"])
    current_tokens=toks(r["currentTarget"])
    proposed_tokens=toks(r["proposedTarget"])
    assert current_tokens[0]==source_tokens[0]
    assert current_tokens[1]==source_tokens[1]
    assert current_tokens[2]==source_tokens[2]
    assert all(token in current_tokens[3] for token in source_tokens[3])
    assert proposed_tokens==current_tokens
    if r["disposition"]=="accept": assert r["proposedTarget"]==r["currentTarget"]
    if r["disposition"]=="revise": assert r["proposedTarget"]!=r["currentTarget"]
    if r["disposition"]=="hold": assert r["proposedTarget"]==r["currentTarget"]
assert counts==m["counts"] and counts["hold"]==0
assert im["callerResolutionHoldCount"]==0 and im["callerResolutionHoldPositions"]==[]
# Verify this packet's own checksum list covers all output files except itself.
own={}
for line in (OUT/"SHA256SUMS.txt").read_text(encoding="utf-8").splitlines():
    digest,name=line.split(None,1); name=name.lstrip("* ")
    assert name not in own
    own[name]=digest
files={p.name for p in OUT.iterdir() if p.is_file() and p.name!="SHA256SUMS.txt"}
assert set(own)==files
for name,digest in own.items(): assert sha((OUT/name).read_bytes())==digest,name
print(json.dumps({"result":"PASS","head":HEAD,"tree":TREE,"cells":len(rows),
                  "counts":counts,"localeOrder":LOCS,
                  "inputFilesChecksummed":len(sum_rows),
                  "outputFilesChecksummed":len(own),
                  "targetHashLinkage":"PASS","placeholderMarkupNumericAndProtectedTokenSignatures":"PASS",
                  "callerlessHolds":0,"packetSha256":sha((OUT/"review.jsonl").read_bytes())},
                 ensure_ascii=False,indent=2))
