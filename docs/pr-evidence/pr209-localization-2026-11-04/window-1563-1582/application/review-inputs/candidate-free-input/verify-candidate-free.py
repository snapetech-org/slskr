#!/usr/bin/env python3
"""Standalone verifier for candidate-free slskR PR #209 W1563-W1582 packet."""
import hashlib, json, re
from collections import Counter
from pathlib import Path

R=Path(__file__).resolve().parent
HEAD="f42c7e4be1f2bc9d63e13607d3c311d37f83f355"
TREE="f6cb31394c01c90a784d543b8f43b04b232c8b37"
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
assert m["selectedPositions"]==[1563,1582] and m["sourceCount"]==20 and m["localeCount"]==12 and m["cellCount"]==240
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
for fname in ("prior-window-selection-hash-only.jsonl","prior-selection-hash-reattestation.jsonl","prior-hold-hash-reattestation.jsonl","prior-window-1503-1522-catalog-diff-hash-only.jsonl","prior-window-1523-1542-application-hash-only.jsonl","prior-window-1543-1562-application-hash-only.jsonl","prior-applied-target-hash-only.jsonl","prior-backfill-hold-hash-only.jsonl"):
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
START,END=1563,1582
selected=keys[START-1:END]
assert len(selected)==20
assert (R/"selected-source-keys.txt").read_text(encoding="utf-8").splitlines()==selected
bound=jl("source-window-boundaries.jsonl")
assert [x["position"] for x in bound]==list(range(START-1,END+2))
assert [x["boundary"] for x in bound]==[True]+[False]*(END-START+1)+[True]
contexts=jl("source-contexts.jsonl")
assert [x["position"] for x in contexts]==list(range(START,END+1))
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
assert [(x["position"],x["locale"]) for x in cells]==[(p,l) for p in range(START,END+1) for l in LOCS]
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
for fname in ("prior-window-selection-hash-only.jsonl","prior-selection-hash-reattestation.jsonl","prior-hold-hash-reattestation.jsonl","prior-window-1503-1522-catalog-diff-hash-only.jsonl","prior-window-1523-1542-application-hash-only.jsonl","prior-window-1543-1562-application-hash-only.jsonl","prior-applied-target-hash-only.jsonl","prior-backfill-hold-hash-only.jsonl"):
    rows=jl(fname)
    assert all(x.get("sourceKeyPositionMatches") is True for x in rows)
priorwin=jl("prior-window-selection-hash-only.jsonl")
priorhold=jl("prior-hold-hash-reattestation.jsonl")
priorapp1503=jl("prior-window-1503-1522-catalog-diff-hash-only.jsonl")
priorapp=jl("prior-window-1523-1542-application-hash-only.jsonl")
priorselected=jl("prior-applied-target-hash-only.jsonl")
priorbackfill=jl("prior-backfill-hold-hash-only.jsonl")
summary=j("prior-continuity-hash-summary.json")
assert len(priorwin)==m["priorWindowHashRecordCount"]==1200
assert len(priorhold)==m["carryForwardHoldCount"]==62
assert len(jl("prior-selection-hash-reattestation.jsonl"))==m["priorSelectionReattestationCount"]==320
priorapp1543=jl("prior-window-1543-1562-application-hash-only.jsonl")
assert len(priorapp1503)==240 and len(priorapp)==240 and len(priorapp1543)==240 and len(priorselected)==47 and len(priorbackfill)==10
assert m["priorAppliedTargetHashCount"]==47 and m["priorBackfillHashOnlyHoldCount"]==10
assert sum(x["priorDisposition"]=="applied-update" for x in priorapp1503)==12
assert sum(x["priorDisposition"]=="accept-current" for x in priorapp1503)==228
assert all(x["liveMatchesExpectedPriorTarget"] is True for x in priorapp1503)
assert summary["fullSourceOrderQueue"]["exactBytesMatch"] is True
assert summary["fullSourceOrderQueue"]["positionsCoveredThrough"]==1582
assert summary["previousWindowCells"]["allMatchExpectedPriorTarget"] is True
assert summary["priorHolds"]["unchangedCount"]==62 and summary["priorHolds"]["backfillCallerBackedHashOnlyHoldCount"]==10
assert {x["position"] for x in priorbackfill}=={1538,1539}
assert all(x["callerResolved"] is True and x["matchesLiveValue"] is True for x in priorbackfill)
assert all(x["selectedTargetSha256"]==x["observedAfterTargetSha256"] for x in priorselected)
assert sum(x["window"]=="W1503-W1522" for x in priorselected)==12
assert sum(x["window"]=="W1523-W1542" for x in priorselected)==8
assert sum(x["window"]=="W1543-W1562" for x in priorselected)==27
assert len([x for x in priorapp if x["priorDisposition"]=="selected-primary"])==8
assert len([x for x in priorapp if x["priorDisposition"]=="hash-only-hold"])==10
assert sum(x["priorDisposition"]=="applied-update" for x in priorapp1543)==27
assert sum(x["priorDisposition"]=="accept-current" for x in priorapp1543)==208
assert sum(x["priorDisposition"]=="hash-only-hold" for x in priorapp1543)==5
assert all(x["liveMatchesExpectedPriorTarget"] is True for x in priorapp1543)
assert all(x["liveMatchesExpectedPriorTarget"] is True for x in priorwin)
lineage=j("source-order-lineage.json")
assert lineage["completeSourceQueueSha256"]==m["sourceQueueFileSha256"]
assert lineage["priorQueueMatchesLiveQueue"] is True and lineage["gapPositions"]==[] and lineage["overlapPositions"]==[]
print(json.dumps({"result":"PASS","head":HEAD,"tree":TREE,"sourceQueueRows":len(q),"sourceWindowCells":len(cells),
 "callerReferences":m["callerReferenceCount"],"callerOccurrences":m["callerOccurrenceCount"],"callerlessPositions":m["callerResolutionHoldPositions"],
 "priorWindowHashRows":m["priorWindowHashRecordCount"],"priorSelectionHashRows":m["priorSelectionReattestationCount"],"priorAppliedTargetHashes":len(priorselected),"priorBackfillHolds":len(priorbackfill),
 "priorHolds":m["carryForwardHoldCount"],"tokenMismatchCounts":dict(bad),"checksummedFiles":len(sum_rows),
 "prRefsStable":True,"candidateFree":True},ensure_ascii=False,indent=2))
