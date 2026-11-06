#!/usr/bin/env python3
import hashlib,json,re,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; REVIEW=ROOT/"blind-review"; INPUT=ROOT/"input"/"candidate-free-input"
def sha(b): return hashlib.sha256(b).hexdigest()
def sha_text(s): return sha(s.encode("utf-8"))
def readj(p): return json.loads(p.read_text(encoding="utf-8"))
def readjl(p): return [json.loads(x) for x in p.read_text(encoding="utf-8").splitlines() if x]
def tokens(s):
 ph=re.findall(r"\{[A-Za-z][A-Za-z0-9_]*\}",s); tags=re.findall(r"<\/?[A-Za-z][^>]*>",s); nums=re.findall(r"(?<![A-Za-z])\d+(?:[.,]\d+)?%?(?![A-Za-z])",s); prot=[]
 for mt in re.finditer(r"(?<![A-Za-z0-9])(?:[A-Z]{2,}[A-Z0-9]*|ffmpeg|Chromaprint|Soulseek|Spotify|YouTube|Pushbullet|Matrix|WebSocket|OpenAI)(?![A-Za-z0-9])",s):
  if mt.group(0) not in prot: prot.append(mt.group(0))
 return {"placeholders":ph,"markupTags":tags,"numericTokens":nums,"protectedLiterals":prot}
def sums(directory,name):
 f=directory/name; entries=[]
 for line in f.read_text(encoding="utf-8").splitlines():
  digest,rel=line.split(None,1); entries.append((rel.lstrip("* "),digest))
 assert len(entries)==len({x for x,_ in entries})
 actual={p.relative_to(directory).as_posix() for p in directory.rglob("*") if p.is_file() and p!=f}
 assert {x for x,_ in entries}==actual
 for rel,d in entries: assert sha((directory/rel).read_bytes())==d,rel
 return len(entries)
root=readj(ROOT/"manifest.json"); inner=readj(REVIEW/"manifest.json"); summary=readj(REVIEW/"review-summary.json")
assert root["head"]==inner["head"]=="44b37bd94385128d5bb5287aa1545901282bdfcb" and root["tree"]==inner["tree"]=="02c3f149a079c67b010d973dd02ca15776ad1610"
assert root["independentBlindReview"] is True and root["primaryReviewAccessed"] is False and root["repositoryOrPRModified"] is False
root_count=sums(ROOT,"SHA256SUMS.txt"); inner_count=sums(REVIEW,"SHA256SUMS.txt")
subprocess.run([sys.executable,str(INPUT/"verify-candidate-free.py")],cwd=INPUT,check=True,stdout=subprocess.DEVNULL)
sums(INPUT,"SHA256SUMS.txt")
cells=readjl(INPUT/"current-target-cells.jsonl"); ledger=readjl(REVIEW/"blind-ledger.jsonl")
assert len(cells)==len(ledger)==240 and len({(r["position"],r["locale"]) for r in ledger})==240
by={(r["position"],r["locale"]):r for r in cells}; counts={}
for row in ledger:
 cur=by[(row["position"],row["locale"])]
 assert row["sourceKey"]==cur["sourceKey"] and row["sourceKeySha256"]==cur["sourceKeySha256"]
 assert row["currentTarget"]==cur["currentTarget"] and row["currentTargetSha256"]==cur["currentTargetSha256"]==sha_text(row["currentTarget"])
 assert row["selectedTargetSha256"]==sha_text(row["selectedTarget"])
 assert row["disposition"] in {"accept-current","correction","refinement","hold"}
 if row["disposition"]=="accept-current": assert row["selectedTarget"]==row["currentTarget"]
 src=tokens(row["sourceKey"]); selected=tokens(row["selectedTarget"])
 assert row["tokenChecks"]["source"]==src and row["tokenChecks"]["selectedTarget"]==selected and row["tokenChecks"]["selectedTargetAllChecksPass"] is True
 for kind in src: assert all(t in selected[kind] for t in src[kind]),(row["position"],row["locale"],kind)
 assert all(x["selectedTargetContainsExactLiteral"] for x in row["manualProtectedLiteralChecks"])
 assert row["callerCount"]==len(row["callerRefs"])>0 and row["callerDisposition"]=="caller-backed; no hold required"
 counts[row["disposition"]]=counts.get(row["disposition"],0)+1
assert counts==summary["dispositionCounts"]==root["dispositionCounts"]==inner["dispositionCounts"]=={"accept-current":190,"correction":31,"refinement":19}
assert summary["selectedTargetTokenFailures"]==root["selectedTargetTokenFailures"]==0
assert summary["baselineProtectedLiteralMismatchCount"]==root["baselineProtectedLiteralMismatchCount"]==9
holds=readjl(REVIEW/"carry-forward-hold-reattestation.jsonl")
assert len(holds)==35 and all(x["disposition"]=="hold" and x["reattestation"]=="same" and x["currentTargetSha256"]==x["priorCurrentTargetSha256"]==sha_text(x["currentTarget"]) for x in holds)
prior=readjl(REVIEW/"prior-selection-reattestation.jsonl")
assert len(prior)==200 and all(x["selectionMatchesCurrentQueue"] and x["priorSourceKey"]==x["currentQueueSourceKey"] and x["priorSourceKeySha256"]==x["currentQueueSourceKeySha256"]==sha_text(x["currentQueueSourceKey"]) for x in prior)
live=readj(REVIEW/"live-head-pin-reattestation.json")
assert live["head"]==live["branchRef"]==live["pullRef"]==root["head"] and live["tree"]==root["tree"]
assert live["state"]=="OPEN" and live["draft"] is True and live["sourcePinCount"]==29
assert live["all240CatalogTargetsReattested"] is True and live["allCallerContextFilesReattested"]==12 and live["allCallerContextLinesReattested"]>0
assert summary["carryForwardHoldsReattested"]==len(holds) and summary["carryForwardHoldFailures"]==0
assert summary["priorSelectedRowsReattested"]==len(prior) and summary["priorSelectionFailures"]==0
print(json.dumps({"result":"PASS","head":root["head"],"tree":root["tree"],"cells":len(ledger),"dispositionCounts":counts,"carryForwardHoldsReattested":len(holds),"priorSelectionsReattested":len(prior),"pinnedSourceFiles":live["sourcePinCount"],"callerContextFiles":live["allCallerContextFilesReattested"],"callerContextLines":live["allCallerContextLinesReattested"],"selectedTokenFailures":0,"baselineProtectedLiteralMismatches":9,"rootChecksumEntries":root_count,"innerChecksumEntries":inner_count},ensure_ascii=False,indent=2))
