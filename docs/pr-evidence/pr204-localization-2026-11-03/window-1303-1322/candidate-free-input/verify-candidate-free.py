#!/usr/bin/env python3
import hashlib,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parent
def sha(b): return hashlib.sha256(b).hexdigest()
def sha_text(s): return sha(s.encode("utf-8"))
def canon(x): return json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(",",":"))
def readj(p): return json.loads(p.read_text(encoding="utf-8"))
def readjl(p): return [json.loads(x) for x in p.read_text(encoding="utf-8").splitlines() if x]
manifest_bytes=(ROOT/"manifest.json").read_bytes(); manifest=readj(ROOT/"manifest.json"); sums=(ROOT/"SHA256SUMS.txt").read_bytes()
assert manifest["candidateFreeInputOnly"] is True and manifest["proposedTranslationsIncluded"] is False
assert manifest["head"]=="f46b8b2322f4b944f39f34d5bb8d55852ba330c8" and manifest["tree"]=="4eba98f951a745dac6b5332bd6796bf57c7037e2"
assert manifest["selectedPositions"]==[1303,1322]
entries=[]
for line in sums.decode().splitlines():
 d,n=line.split(None,1); n=n.lstrip("* "); entries.append((n,d))
assert len(entries)==len({n for n,d in entries})
assert {n for n,d in entries}=={p.name for p in ROOT.iterdir() if p.is_file() and p.name!="SHA256SUMS.txt"}
for n,d in entries: assert sha((ROOT/n).read_bytes())==d,n
for n,v in manifest["fileHashes"].items(): assert sha((ROOT/n).read_bytes())==v["sha256"],n
attest=readj(ROOT/"PR-attestation.json")
assert attest["head"]==manifest["head"] and attest["tree"]==manifest["tree"] and attest["branchRef"]==manifest["head"] and attest["pullRef"]==manifest["head"]
assert attest["state"]=="OPEN" and attest["draft"] is True
queue=readjl(ROOT/"source-queue.jsonl"); contexts=readjl(ROOT/"source-contexts.jsonl"); cells=readjl(ROOT/"current-target-cells.jsonl"); holds=readjl(ROOT/"caller-resolution-holds.jsonl")
assert len(queue)==manifest["sourceQueueCount"]==5441 and [r["position"] for r in queue]==list(range(1,5442))
assert len(contexts)==manifest["sourceCount"]==20 and len(cells)==manifest["cellCount"]==240
assert len({(r["position"],r["locale"]) for r in cells})==240
assert {r["position"] for r in contexts}==set(range(1303,1323)) and {r["locale"] for r in cells}==set(manifest["localeOrder"])
assert [r["position"] for r in cells[::12]]==list(range(1303,1323))
ph=re.compile(r"\{[A-Za-z][A-Za-z0-9_]*\}"); tags=re.compile(r"<\/?[A-Za-z][^>]*>"); nums=re.compile(r"(?<![A-Za-z])\d+(?:[.,]\d+)?%?(?![A-Za-z])")
by_pos={r["position"]:r for r in contexts}
for pos,ctx in by_pos.items():
 assert ctx["callerContextSha256"]==sha_text(canon({"sourceKey":ctx["sourceKey"],"callers":ctx["callers"]}))
 assert ctx["productionCallerCount"]==len(ctx["callers"])
for c in cells:
 ctx=by_pos[c["position"]]; q=queue[c["position"]-1]
 assert c["sourceKey"]==ctx["sourceKey"]==q["sourceKey"] and c["sourceKeySha256"]==ctx["sourceKeySha256"]==q["sourceKeySha256"]
 assert sha_text(c["sourceKey"])==c["sourceKeySha256"] and sha_text(c["currentTarget"])==c["currentTargetSha256"]
 assert c["sourcePlaceholders"]==ph.findall(c["sourceKey"]) and c["currentTargetPlaceholders"]==ph.findall(c["currentTarget"])
 assert c["sourceMarkupTags"]==tags.findall(c["sourceKey"]) and c["currentTargetMarkupTags"]==tags.findall(c["currentTarget"])
 assert c["sourceNumericTokens"]==nums.findall(c["sourceKey"]) and c["currentTargetNumericTokens"]==nums.findall(c["currentTarget"])
 assert c["placeholderSequenceMatches"]==(c["sourcePlaceholders"]==c["currentTargetPlaceholders"])
 assert c["markupMatches"]==(c["sourceMarkupTags"]==c["currentTargetMarkupTags"])
 assert c["numericTokensMatch"]==(c["sourceNumericTokens"]==c["currentTargetNumericTokens"])
 assert c["sourceContextSha256"]==ctx["callerContextSha256"] and c["callerCount"]==len(ctx["callers"])
 assert c["callerRefs"]==[{"fileSha256":x["fileSha256"],"gitBlob":x["gitBlob"],"line":x["line"],"lineSha256":x["lineSha256"],"path":x["path"]} for x in ctx["callers"]]
assert {r["position"] for r in holds}=={r["position"] for r in contexts if not r["callers"]}
print(json.dumps({"result":"PASS","manifestSha256":sha(manifest_bytes),"checksumListSha256":sha(sums),"sourceCount":len(contexts),"localeCount":len(manifest["localeOrder"]),"cellCount":len(cells),"callerReferences":sum(r["productionCallerCount"] for r in contexts),"callerlessHolds":len(holds),"mismatchCounts":{k:manifest[k] for k in ["placeholderSequenceMismatchCount","markupMismatchCount","numericTokenMismatchCount","protectedLiteralMismatchCount"]}},indent=2))
