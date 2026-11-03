#!/usr/bin/env python3
import hashlib,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parent
def sha(b): return hashlib.sha256(b).hexdigest()
def sha_text(s): return sha(s.encode("utf-8"))
def canon(x): return json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(",",":"))
def readj(p): return json.loads(p.read_text(encoding="utf-8"))
def readjl(p): return [json.loads(x) for x in p.read_text(encoding="utf-8").splitlines() if x]
def tokens(s):
 ph=re.findall(r"\{[A-Za-z][A-Za-z0-9_]*\}",s); tags=re.findall(r"<\/?[A-Za-z][^>]*>",s); nums=re.findall(r"(?<![A-Za-z])\d+(?:[.,]\d+)?%?(?![A-Za-z])",s)
 prot=[]
 for mt in re.finditer(r"(?<![A-Za-z0-9])(?:[A-Z]{2,}[A-Z0-9]*|ffmpeg|Chromaprint|Soulseek|Spotify|YouTube|Pushbullet|Matrix|WebSocket|OpenAI)(?![A-Za-z0-9])",s):
  if mt.group(0) not in prot: prot.append(mt.group(0))
 return ph,tags,nums,prot
m=readj(ROOT/"manifest.json"); sums=(ROOT/"SHA256SUMS.txt").read_bytes()
assert m["candidateFreeInputOnly"] is True and m["proposedTranslationsIncluded"] is False
assert m["head"]=="281c39ec0cdb3677d7d523b7c4f0cd0d52bbf14c" and m["tree"]=="777b234b1aa3cb7a2c9fd560b2c0fecc4e7fe49d"
assert m["selectedPositions"]==[1363,1382] and m["previousBoundaryPosition"]==1362 and m["nextBoundaryPosition"]==1383
assert m["sourceCount"]==20 and m["localeCount"]==12 and m["cellCount"]==240
entries=[]
for line in sums.decode().splitlines():
 d,n=line.split(None,1); n=n.lstrip("* "); entries.append((n,d))
assert len(entries)==len({n for n,d in entries})
assert {n for n,d in entries}=={p.name for p in ROOT.iterdir() if p.is_file() and p.name!="SHA256SUMS.txt"}
for n,d in entries: assert sha((ROOT/n).read_bytes())==d,n
for n,v in m["fileHashes"].items(): assert sha((ROOT/n).read_bytes())==v["sha256"],n
a=readj(ROOT/"PR-attestation.json")
assert a["head"]==m["head"] and a["tree"]==m["tree"] and a["branchRef"]==m["head"] and a["pullRef"]==m["head"] and a["state"]=="OPEN" and a["draft"] is True
q=readjl(ROOT/"source-queue.jsonl"); ctxs=readjl(ROOT/"source-contexts.jsonl"); cells=readjl(ROOT/"current-target-cells.jsonl"); holds=readjl(ROOT/"caller-resolution-holds.jsonl"); prior_holds=readjl(ROOT/"prior-hold-reattestation.jsonl"); exclusions=readjl(ROOT/"prior-selection-reattestation.jsonl")
assert len(q)==5441 and [r["position"] for r in q]==list(range(1,5442))
order_hash=sha_text("\n".join(r["sourceKey"] for r in q)+"\n")
assert order_hash==m["sourceLookupKeyOrderSha256"]
assert sha((ROOT/"source-queue.jsonl").read_bytes())==m["sourceQueueFileSha256"]
assert len(ctxs)==20 and len(cells)==240 and len({(r["position"],r["locale"]) for r in cells})==240
assert [r["position"] for r in ctxs]==list(range(1363,1383))
assert [r["position"] for r in cells[::12]]==list(range(1363,1383))
assert [r["locale"] for r in cells[:12]]==m["localeOrder"]
bounds=readjl(ROOT/"source-window-boundaries.jsonl")
assert [r["position"] for r in bounds]==[1362,*range(1363,1383),1383]
assert bounds[0]["sourceKey"]==q[1361]["sourceKey"] and bounds[-1]["sourceKey"]==q[1382]["sourceKey"]
ph_m=tag_m=num_m=prot_m=0
by_pos={r["position"]:r for r in ctxs}
for r in ctxs:
 assert r["productionCallerCount"]==len(r["callers"])
 assert r["callerContextSha256"]==sha_text(canon({"sourceKey":r["sourceKey"],"callers":r["callers"]}))
 assert r["sourceKey"]==q[r["position"]-1]["sourceKey"]
for c in cells:
 r=by_pos[c["position"]]
 assert c["sourceKey"]==r["sourceKey"]==q[c["position"]-1]["sourceKey"]
 assert c["sourceKeySha256"]==sha_text(c["sourceKey"])==q[c["position"]-1]["sourceKeySha256"]
 assert c["currentTargetSha256"]==sha_text(c["currentTarget"])
 sph,stags,snums,sprot=tokens(c["sourceKey"]); tph,ttags,tnums,tprot=tokens(c["currentTarget"])
 assert c["sourcePlaceholders"]==sph and c["currentTargetPlaceholders"]==tph and c["placeholderSequenceMatches"]==(sph==tph)
 assert c["sourceMarkupTags"]==stags and c["currentTargetMarkupTags"]==ttags and c["markupMatches"]==(stags==ttags)
 assert c["sourceNumericTokens"]==snums and c["currentTargetNumericTokens"]==tnums and c["numericTokensMatch"]==(snums==tnums)
 bad=[t for t in sprot if t not in tprot]
 assert c["sourceProtectedLiterals"]==sprot and c["currentTargetProtectedLiterals"]==tprot and c["protectedLiteralMismatchTokens"]==bad and c["protectedLiteralsMatch"]==(not bad)
 ph_m+=sph!=tph; tag_m+=stags!=ttags; num_m+=snums!=tnums; prot_m+=bool(bad)
 assert c["callerCount"]==len(r["callers"]) and c["sourceContextSha256"]==r["callerContextSha256"]
 assert c["callerRefs"]==[{"fileSha256":x["fileSha256"],"gitBlob":x["gitBlob"],"line":x["line"],"lineSha256":x["lineSha256"],"path":x["path"]} for x in r["callers"]]
assert {r["position"] for r in holds}=={r["position"] for r in ctxs if not r["callers"]}
assert len(prior_holds)==23 and len({(r["position"],r["locale"]) for r in prior_holds})==23
assert all(r["disposition"]=="hold" and r["reattestation"]=="same" and r["currentTarget"]==r["priorCurrentTarget"] and r["currentTargetSha256"]==r["priorCurrentTargetSha256"] for r in prior_holds)
assert len(exclusions)==120 and all(r["selectionMatchesCurrentQueue"] and r["priorSourceKey"]==r["currentQueueSourceKey"] and r["priorSourceKeySha256"]==r["currentQueueSourceKeySha256"]==sha_text(r["currentQueueSourceKey"]) for r in exclusions)
assert not {r["position"] for r in exclusions} & set(range(1363,1383))
lineage=readj(ROOT/"source-order-lineage.json")
assert lineage["priorSelectedSourceCount"]==len(exclusions) and lineage["priorSelectionsAllMatchCurrentQueue"] is True
assert [lineage["previousBoundary"]["position"],lineage["firstSelected"]["position"],lineage["lastSelected"]["position"],lineage["nextBoundary"]["position"]]==[1362,1363,1382,1383]
mism={"placeholderSequenceMismatchCount":ph_m,"markupMismatchCount":tag_m,"numericTokenMismatchCount":num_m,"protectedLiteralMismatchCount":prot_m}
assert mism==m["mismatchCounts"]
print(json.dumps({"result":"PASS","head":m["head"],"tree":m["tree"],"positions":[1363,1382],"cells":len(cells),"sourceQueueOrderSha256":order_hash,"callerReferences":sum(r["productionCallerCount"] for r in ctxs),"callerlessPositions":[r["position"] for r in ctxs if not r["callers"]],"priorHoldsReattested":len(prior_holds),"changedPriorHolds":0,"priorSelectedRowsReattested":len(exclusions),"mismatchCounts":mism,"manifestSha256":sha((ROOT/"manifest.json").read_bytes()),"checksumListSha256":sha(sums)},ensure_ascii=False,indent=2))
