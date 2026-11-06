#!/usr/bin/env python3
"""Standalone verifier for candidate-free slskR PR #204 W1523-W1542 packet."""
import hashlib, json, re
from collections import Counter
from pathlib import Path

R=Path(__file__).resolve().parent
HEAD="f6fbf614e7e2ff869e4ca86ae96103cff604b79c"
TREE="536b0fc02a3c16fa7eb0f9d5504a4c8c91b2152d"
LOCS=["es","zh-Hans","hi","de","ja","fr","pt-BR","ar","ko","zh-Hant","vi","id"]
def sha(x):
    if isinstance(x,str): x=x.encode()
    return hashlib.sha256(x).hexdigest()
def canon(x): return json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(",",":"))
def j(n): return json.loads((R/n).read_text(encoding="utf-8"))
def jl(n): return [json.loads(s) for s in (R/n).read_text(encoding="utf-8").splitlines() if s]
def toks(s):
    p=re.findall(r"\{[A-Za-z][A-Za-z0-9_]*\}",s)
    m=re.findall(r"</?[A-Za-z][^>]*>",s)
    n=re.findall(r"(?<![A-Za-z])\d+(?:[.,]\d+)?%?(?![A-Za-z])",s)
    z=[]
    for x in re.findall(r"(?<![A-Za-z0-9])(?:[A-Z]{2,}[A-Z0-9]*|ffmpeg|Chromaprint|Soulseek|Spotify|YouTube|Pushbullet|Matrix|WebSocket|OpenAI)(?![A-Za-z0-9])",s):
        if x not in z:z.append(x)
    return p,m,n,z

m=j("manifest.json")
assert m["head"]==HEAD and m["tree"]==TREE and m["candidateFreeInputOnly"] is True and m["proposedTranslationsIncluded"] is False
assert m["selectedPositions"]==[1523,1542] and m["sourceCount"]==20 and m["localeCount"]==12 and m["cellCount"]==240
sum_rows={}
for line in (R/"SHA256SUMS.txt").read_text(encoding="utf-8").splitlines():
    digest,name=line.split(None,1); name=name.lstrip("* ")
    assert name not in sum_rows
    sum_rows[name]=digest
actual={p.name for p in R.iterdir() if p.is_file() and p.name!="SHA256SUMS.txt"}
assert set(sum_rows)==actual
assert set(m["fileHashes"])==actual-{"manifest.json"}
for name,digest in sum_rows.items(): assert sha((R/name).read_bytes())==digest,name
for name,pin in m["fileHashes"].items():
    b=(R/name).read_bytes(); assert len(b)==pin["byteCount"] and sha(b)==pin["sha256"],name
for fname in ("prior-window-selection-hash-only.jsonl","prior-selection-hash-reattestation.jsonl","prior-hold-hash-reattestation.jsonl"):
    for row in jl(fname):
        assert not any(k in row for k in ("sourceKey","currentTarget","target","crossTarget","proposedTarget","source","targetText","lineText"))
a,b=j("PR-attestation.json"),j("PR-attestation-after.json")
for x in (a,b):
    assert x["state"]=="OPEN" and x["draft"] is True and x["head"]==HEAD and x["tree"]==TREE
    assert x["branchRef"]==x["pullRef"]==HEAD and x["baseRef"]=="main"
for k in ("head","tree","headRef","branchRef","pullRef","baseRef","baseSha","state","draft","deploymentsForHeadCount","deploymentsForHeadSha256","repositoryDeploymentCount","repositoryDeploymentsSha256","actionsRunsForHeadCount"):
    assert a[k]==b[k],k
q=jl("source-queue.jsonl")
assert len(q)==5441 and [x["position"] for x in q]==list(range(1,5442))
keys=[x["sourceKey"] for x in q]
assert keys==sorted(keys) and len(set(keys))==5441
assert sha("\n".join(keys)+"\n")==m["sourceLookupKeyOrderSha256"]
assert sha((R/"source-queue.jsonl").read_bytes())==m["sourceQueueFileSha256"]
assert all(x["sourceKeySha256"]==sha(x["sourceKey"]) and x["historicalSourceOrdinal"] is None for x in q)
selected=keys[1522:1542]
assert len(selected)==20
assert (R/"selected-source-keys.txt").read_text(encoding="utf-8").splitlines()==selected
bound=jl("source-window-boundaries.jsonl")
assert [x["position"] for x in bound]==list(range(1522,1544))
assert [x["boundary"] for x in bound]==[True]+[False]*20+[True]
contexts=jl("source-contexts.jsonl")
assert [x["position"] for x in contexts]==list(range(1523,1543))
ctx={x["position"]:x for x in contexts}
for x in contexts:
    assert x["sourceKey"]==keys[x["position"]-1] and x["sourceKeySha256"]==sha(x["sourceKey"])
    assert x["productionCallerCount"]==len(x["callers"])
    assert x["callerOccurrenceCount"]==sum(c["literalOccurrenceCount"] for c in x["callers"])
    assert x["callerContextSha256"]==sha(canon({"sourceKey":x["sourceKey"],"callers":x["callers"]}))
    for c in x["callers"]:
        assert c["lineSha256"]==sha(c["lineText"])
        assert c["contextSha256"]==sha(canon(c["context"]))
        assert any(row["line"]==c["line"] and row["text"]==c["lineText"] for row in c["context"])
cells=jl("current-target-cells.jsonl")
assert len(cells)==240
assert [(x["position"],x["locale"]) for x in cells]==[(p,l) for p in range(1523,1543) for l in LOCS]
bad=Counter()
for x in cells:
    c=ctx[x["position"]]; assert x["sourceKey"]==c["sourceKey"] and x["sourceKeySha256"]==sha(x["sourceKey"])
    assert x["callerCount"]==c["productionCallerCount"] and x["sourceContextSha256"]==c["callerContextSha256"]
    assert x["currentTargetSha256"]==sha(x["currentTarget"])
    st,tt=toks(x["sourceKey"]),toks(x["currentTarget"])
    assert x["sourcePlaceholders"]==st[0] and x["currentTargetPlaceholders"]==tt[0] and x["placeholderSequenceMatches"]==(st[0]==tt[0])
    assert x["sourceMarkupTags"]==st[1] and x["currentTargetMarkupTags"]==tt[1] and x["markupMatches"]==(st[1]==tt[1])
    assert x["sourceNumericTokens"]==st[2] and x["currentTargetNumericTokens"]==tt[2] and x["numericTokensMatch"]==(st[2]==tt[2])
    missing=[z for z in st[3] if z not in tt[3]]
    assert x["sourceProtectedLiterals"]==st[3] and x["currentTargetProtectedLiterals"]==tt[3]
    assert x["protectedLiteralMismatchTokens"]==missing and x["protectedLiteralsMatch"]==(not missing)
    bad["placeholderSequenceMismatchCount"]+=st[0]!=tt[0]
    bad["markupMismatchCount"]+=st[1]!=tt[1]
    bad["numericTokenMismatchCount"]+=st[2]!=tt[2]
    bad["protectedLiteralMismatchCount"]+=bool(missing)
assert dict(bad)==m["mismatchCounts"]
for fname in ("prior-window-selection-hash-only.jsonl","prior-selection-hash-reattestation.jsonl","prior-hold-hash-reattestation.jsonl"):
    rows=jl(fname)
    assert all(x.get("sourceKeyPositionMatches") is True for x in rows)
print(json.dumps({"result":"PASS","head":HEAD,"tree":TREE,"sourceQueueRows":len(q),"sourceWindowCells":len(cells),
 "callerReferences":m["callerReferenceCount"],"callerOccurrences":m["callerOccurrenceCount"],"callerlessPositions":m["callerResolutionHoldPositions"],
 "priorWindowHashRows":m["priorWindowHashRecordCount"],"priorSelectionHashRows":m["priorSelectionReattestationCount"],
 "priorHolds":m["carryForwardHoldCount"],"tokenMismatchCounts":dict(bad),"checksummedFiles":len(sum_rows),
 "prRefsStable":True,"candidateFree":True},ensure_ascii=False,indent=2))
