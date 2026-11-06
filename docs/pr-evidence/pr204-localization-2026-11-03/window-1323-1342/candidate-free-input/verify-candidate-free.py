#!/usr/bin/env python3
import hashlib,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parent
def sha(b): return hashlib.sha256(b).hexdigest()
def sha_text(s): return sha(s.encode("utf-8"))
def canon(x): return json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(",",":"))
def readj(p): return json.loads(p.read_text(encoding="utf-8"))
def readjl(p): return [json.loads(x) for x in p.read_text(encoding="utf-8").splitlines() if x]
m=readj(ROOT/"manifest.json"); sums=(ROOT/"SHA256SUMS.txt").read_bytes()
assert m["candidateFreeInputOnly"] is True and m["proposedTranslationsIncluded"] is False
assert m["head"]=="6ccefe07d8154acbc08e34249ef7039dc5bc1f08" and m["tree"]=="e0c1d1341be45ed73bd30cf027b479ce3b5bb95d"
assert m["selectedPositions"]==[1323,1342] and m["sourceCount"]==20 and m["localeCount"]==12 and m["cellCount"]==240
entries=[]
for line in sums.decode().splitlines():
 d,n=line.split(None,1); n=n.lstrip("* "); entries.append((n,d))
assert len(entries)==len({n for n,d in entries})
assert {n for n,d in entries}=={p.name for p in ROOT.iterdir() if p.is_file() and p.name!="SHA256SUMS.txt"}
for n,d in entries: assert sha((ROOT/n).read_bytes())==d,n
for n,v in m["fileHashes"].items(): assert sha((ROOT/n).read_bytes())==v["sha256"],n
a=readj(ROOT/"PR-attestation.json")
assert a["head"]==m["head"] and a["tree"]==m["tree"] and a["branchRef"]==m["head"] and a["pullRef"]==m["head"] and a["state"]=="OPEN" and a["draft"] is True
q=readjl(ROOT/"source-queue.jsonl"); ctxs=readjl(ROOT/"source-contexts.jsonl"); cells=readjl(ROOT/"current-target-cells.jsonl"); holds=readjl(ROOT/"caller-resolution-holds.jsonl")
assert len(q)==5441 and [r["position"] for r in q]==list(range(1,5442))
assert len(ctxs)==20 and len(cells)==240 and len({(r["position"],r["locale"]) for r in cells})==240
assert [r["position"] for r in ctxs]==list(range(1323,1343))
assert [r["position"] for r in cells[::12]]==list(range(1323,1343))
assert [r["locale"] for r in cells[:12]]==m["localeOrder"]
ph=re.compile(r"\{[A-Za-z][A-Za-z0-9_]*\}"); tags=re.compile(r"<\/?[A-Za-z][^>]*>"); nums=re.compile(r"(?<![A-Za-z])\d+(?:[.,]\d+)?%?(?![A-Za-z])")
by_pos={r["position"]:r for r in ctxs}; mism={"placeholderSequenceMismatchCount":0,"markupMismatchCount":0,"numericTokenMismatchCount":0,"protectedLiteralMismatchCount":0}
for r in ctxs:
 assert r["productionCallerCount"]==len(r["callers"])
 assert r["callerContextSha256"]==sha_text(canon({"sourceKey":r["sourceKey"],"callers":r["callers"]}))
for c in cells:
 r=by_pos[c["position"]]; assert c["sourceKey"]==r["sourceKey"]==q[c["position"]-1]["sourceKey"]
 assert c["sourceKeySha256"]==sha_text(c["sourceKey"])==q[c["position"]-1]["sourceKeySha256"]
 assert c["currentTargetSha256"]==sha_text(c["currentTarget"])
 for field,pattern,matchkey in [("Placeholders",ph,"placeholderSequenceMatches"),("MarkupTags",tags,"markupMatches"),("NumericTokens",nums,"numericTokensMatch")]:
  src=pattern.findall(c["sourceKey"]); tgt=pattern.findall(c["currentTarget"])
  assert c["source"+field]==src and c["currentTarget"+field]==tgt
  good=(src==tgt); assert c[matchkey]==good
  if not good:
   key={"placeholderSequenceMatches":"placeholderSequenceMismatchCount","markupMatches":"markupMismatchCount","numericTokensMatch":"numericTokenMismatchCount"}[matchkey]; mism[key]+=1
 assert c["callerCount"]==len(r["callers"]) and c["sourceContextSha256"]==r["callerContextSha256"]
 assert c["callerRefs"]==[{"fileSha256":x["fileSha256"],"gitBlob":x["gitBlob"],"line":x["line"],"lineSha256":x["lineSha256"],"path":x["path"]} for x in r["callers"]]
 bad=[t for t in c["sourceProtectedLiterals"] if t not in c["currentTargetProtectedLiterals"]]
 assert c["protectedLiteralMismatchTokens"]==bad and c["protectedLiteralsMatch"]==(not bad)
 if bad: mism["protectedLiteralMismatchCount"]+=1
assert {r["position"] for r in holds}=={r["position"] for r in ctxs if not r["callers"]}
cf=readjl(ROOT/"prior-hold-reattestation.jsonl")
assert len(cf)==22 and sum(r["kind"]=="carry-forward-callerless-hold" for r in cf)==12 and sum(r["kind"]=="carry-forward-semantic-hold" for r in cf)==10
assert all(r["reattestation"]=="same" for r in cf)
assert mism==m["mismatchCounts"]
print(json.dumps({"result":"PASS","manifestSha256":sha((ROOT/"manifest.json").read_bytes()),"checksumListSha256":sha(sums),"sourceCount":len(ctxs),"localeCount":12,"cellCount":len(cells),"callerReferences":sum(r["productionCallerCount"] for r in ctxs),"callerlessHolds":len(holds),"carryForwardHolds":len(cf),"mismatchCounts":mism},indent=2))
