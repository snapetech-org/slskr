#!/usr/bin/env python3
import hashlib,json,re,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parent
TASK=ROOT.parent; REPO=TASK/"repo"
PREV=Path("/home/keith/Documents/code/task-scratch/slskr-pr204-w1323-1342-primary-20261103/input-v4")
HEAD="130462c56f75d3c8fc2a90663a48c0474ad1208b"; TREE="47aba96d79eb57d6024fb358ee59cde931f0de3b"
LOCALES=["es","zh-Hans","hi","de","ja","fr","pt-BR","ar","ko","zh-Hant","vi","id"]
def sha(b):return hashlib.sha256(b).hexdigest()
def st(s):return sha(s.encode("utf-8"))
def canon(x):return json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(",",":"))
def j(p):return json.loads(p.read_text(encoding="utf-8"))
def jl(p):return [json.loads(x) for x in p.read_text(encoding="utf-8").splitlines() if x.strip()]
def git(*args):return subprocess.check_output(["git","-C",str(REPO),*args])
def gt(*args):return git(*args).decode("utf-8").strip()
def gf(path):return git("show",f"{HEAD}:{path}")
def gb(path):return gt("rev-parse",f"{HEAD}:{path}")
def checks(folder,name):
 r=subprocess.run(["sha256sum","-c",name],cwd=folder,text=True,capture_output=True); assert r.returncode==0,(r.stdout,r.stderr)
checks(ROOT,"SHA256SUMS.txt"); checks(PREV,"SHA256SUMS.txt")
m=j(ROOT/"manifest.json"); att=j(ROOT/"PR-attestation.json")
assert (m["head"],m["tree"],m["selectedPositions"],m["sourceCount"],m["localeCount"],m["cellCount"])==(HEAD,TREE,[1343,1362],20,12,240)
assert (att["head"],att["tree"],att["branchRef"],att["pullRef"],att["state"],att["draft"])==(HEAD,TREE,HEAD,HEAD,"OPEN",True)
for n,v in m["fileHashes"].items():assert sha((ROOT/n).read_bytes())==v["sha256"],n
assert gt("rev-parse",f"{HEAD}^{{tree}}")==TREE==gt("rev-parse","HEAD^{tree}")
prev_m=j(PREV/"manifest.json"); prev_q=jl(PREV/"source-queue.jsonl")
q=jl(ROOT/"source-queue.jsonl"); contexts=jl(ROOT/"source-contexts.jsonl"); cells=jl(ROOT/"current-target-cells.jsonl"); holds=jl(ROOT/"caller-resolution-holds.jsonl"); prior=jl(ROOT/"prior-hold-reattestation.jsonl")
assert len(q)==len(prev_q)==5441 and q==prev_q
assert [r["position"] for r in q]==list(range(1,5442))
assert len(contexts)==20 and [r["position"] for r in contexts]==list(range(1343,1363))
assert len(cells)==240 and len({(r["position"],r["locale"]) for r in cells})==240
assert len(prior)==23 and all(r["reattestation"]=="same" and r["disposition"]=="hold" for r in prior)
lineage=j(ROOT/"source-order-lineage.json")
assert lineage["previousWindowSelectedPositions"]==[1323,1342] and lineage["previousWindowNextBoundaryPosition"]==1343
assert lineage["previousBoundary"]["position"]==1342 and lineage["firstSelected"]["position"]==1343
assert lineage["previousBoundary"]["sourceKey"]==q[1341]["sourceKey"]==prev_q[1341]["sourceKey"]
assert lineage["firstSelected"]["sourceKey"]==q[1342]["sourceKey"]==prev_q[1342]["sourceKey"]
assert lineage["nextBoundary"]["position"]==1363 and lineage["nextBoundary"]["sourceKey"]==q[1362]["sourceKey"]
queue_path=lineage["currentHeadCommittedSourceQueuePath"]
raw_q=gf(queue_path)
assert gb(queue_path)==lineage["currentHeadCommittedSourceQueueBlob"] and sha(raw_q)==lineage["currentHeadCommittedSourceQueueSha256"]
assert [json.loads(x) for x in raw_q.decode().splitlines() if x]==q
assert prev_m["sourceQueueFileSha256"]==lineage["previousSourceQueueSha256"]
assert len(contexts)==len({x["position"] for x in contexts})==20
pin=j(ROOT/"catalog-file-pins.json"); structures=jl(ROOT/"catalog-structure.jsonl")
assert pin["head"]==HEAD and pin["tree"]==TREE and pin["sourceLookupKeySetCount"]==5441
ctx={r["position"]:r for r in contexts}
cats={}; key_order=None
for loc in LOCALES:
 rec=pin["localeCatalogs"][loc]; path=rec["path"]; raw=gf(path); obj=json.loads(raw.decode(),object_pairs_hook=dict)
 assert set(obj)=={r["sourceKey"] for r in q}
 if key_order is None:key_order=list(obj)
 assert list(obj)==key_order
 cats[loc]=(path,raw,obj)
structure_map={r["locale"]:r for r in structures}
assert set(structure_map)==set(LOCALES)
source_files={}
for c in contexts:
 assert c["sourceKey"]==q[c["position"]-1]["sourceKey"] and c["sourceKeySha256"]==st(c["sourceKey"])
 assert c["productionCallerCount"]==len(c["callers"])
 assert c["callerContextSha256"]==st(canon({"sourceKey":c["sourceKey"],"callers":c["callers"]}))
 for ref in c["callers"]:
  if ref["path"] not in source_files:
   raw=gf(ref["path"]); assert sha(raw)==ref["fileSha256"] and gb(ref["path"])==ref["gitBlob"]; source_files[ref["path"]]=raw.decode().splitlines()
  lines=source_files[ref["path"]]; n=ref["line"]
  assert lines[n-1]==ref["lineText"] and st(lines[n-1])==ref["lineSha256"]
  a=max(1,n-4); b=min(len(lines),n+4)
  context=[{"line":k,"lineSha256":st(lines[k-1]),"text":lines[k-1]} for k in range(a,b+1)]
  assert context==ref["context"] and st(canon(context))==ref["contextSha256"]
assert {x["position"] for x in holds}=={x["position"] for x in contexts if not x["callers"]}
runtime=j(ROOT/"localization-runtime-context.json")
rr=gf(runtime["path"])
assert sha(rr)==runtime["pin"]["sha256"] and gb(runtime["path"])==runtime["pin"]["gitBlob"]
ph=re.compile(r"\{[A-Za-z][A-Za-z0-9_]*\}"); tags=re.compile(r"<\/?[A-Za-z][^>]*>"); nums=re.compile(r"(?<![A-Za-z])\d+(?:[.,]\d+)?%?(?![A-Za-z])")
mism={"placeholderSequenceMismatchCount":0,"markupMismatchCount":0,"numericTokenMismatchCount":0,"protectedLiteralMismatchCount":0}
for c in cells:
 path,raw,obj=cats[c["locale"]]
 assert c["catalogPath"]==path and c["catalogFileSha256"]==sha(raw) and c["catalogGitBlob"]==gb(path)
 assert c["currentTarget"]==obj[c["sourceKey"]] and c["currentTargetSha256"]==st(c["currentTarget"])
 assert c["sourceKey"]==ctx[c["position"]]["sourceKey"] and c["sourceKeySha256"]==st(c["sourceKey"])
 assert c["callerCount"]==len(ctx[c["position"]]["callers"]) and c["sourceContextSha256"]==ctx[c["position"]]["callerContextSha256"]
 assert c["callerRefs"]==[{"fileSha256":r["fileSha256"],"gitBlob":r["gitBlob"],"line":r["line"],"lineSha256":r["lineSha256"],"path":r["path"]} for r in ctx[c["position"]]["callers"]]
 assert c["sourcePlaceholders"]==ph.findall(c["sourceKey"]) and c["currentTargetPlaceholders"]==ph.findall(c["currentTarget"])
 assert c["sourceMarkupTags"]==tags.findall(c["sourceKey"]) and c["currentTargetMarkupTags"]==tags.findall(c["currentTarget"])
 assert c["sourceNumericTokens"]==nums.findall(c["sourceKey"]) and c["currentTargetNumericTokens"]==nums.findall(c["currentTarget"])
 bad=[x for x in c["sourceProtectedLiterals"] if x not in c["currentTargetProtectedLiterals"]]
 assert c["protectedLiteralMismatchTokens"]==bad and c["protectedLiteralsMatch"]==(not bad)
 mism["placeholderSequenceMismatchCount"]+=c["sourcePlaceholders"]!=c["currentTargetPlaceholders"]
 mism["markupMismatchCount"]+=c["sourceMarkupTags"]!=c["currentTargetMarkupTags"]
 mism["numericTokenMismatchCount"]+=c["sourceNumericTokens"]!=c["currentTargetNumericTokens"]
 mism["protectedLiteralMismatchCount"]+=bool(bad)
for h in prior:
 loc=h["locale"]; path,raw,obj=cats[loc]
 assert h["currentCatalogPath"]==path and h["currentCatalogSha256"]==sha(raw) and h["currentCatalogGitBlob"]==gb(path)
 assert h["currentTarget"]==obj[h["sourceKey"]] and h["currentTargetSha256"]==st(h["currentTarget"])
assert m["priorHoldReattestationCount"]==len(prior)==23 and m["priorHoldUnchangedCount"]==23
assert m["mismatchCounts"]==mism
assert len([x for x in prior if x["position"]==1335 and x["locale"]=="vi"])==1
print(json.dumps({"result":"PASS","head":HEAD,"tree":TREE,"queueCount":5441,"queueOrderSha256":lineage["liveCatalogSourceKeyOrderSha256"],"positions":[1343,1362],"cells":len(cells),"callerReferences":sum(x["productionCallerCount"] for x in contexts),"callerlessPositions":[x["position"] for x in holds],"priorHoldsReattested":len(prior),"changedPriorHolds":sum(x["reattestation"]!="same" for x in prior),"mismatchCounts":mism},ensure_ascii=False,indent=2))
