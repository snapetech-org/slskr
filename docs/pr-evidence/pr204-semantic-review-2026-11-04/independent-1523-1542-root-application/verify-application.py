#!/usr/bin/env python3
"""Verify slskR PR #204 W1523-W1542 review application and readback evidence."""
import hashlib,json,subprocess
from collections import Counter
from pathlib import Path
R=Path(__file__).resolve().parent
REPO=R.parents[3]
HEAD="f6fbf614e7e2ff869e4ca86ae96103cff604b79c"
TREE="536b0fc02a3c16fa7eb0f9d5504a4c8c91b2152d"
def sha(x):
 if isinstance(x,str):x=x.encode("utf-8")
 return hashlib.sha256(x).hexdigest()
def j(p):return json.loads(p.read_text(encoding="utf-8"))
def jl(p):return [json.loads(s) for s in p.read_text(encoding="utf-8").splitlines() if s]
def cmd(*args):return subprocess.check_output(args,text=True).strip()
sums={}
for line in (R/"SHA256SUMS.txt").read_text(encoding="utf-8").splitlines():
 h,n=line.split(None,1);n=n.lstrip("* ");assert n not in sums;sums[n]=h
actual={p.relative_to(R).as_posix() for p in R.rglob("*") if p.is_file() and p.relative_to(R).as_posix()!="SHA256SUMS.txt"}
assert set(sums)==actual,set(sums)^actual
for n,h in sums.items():assert sha((R/n).read_bytes())==h,n
subprocess.run(["python3",str(R/"crossreview/verify_cross_bundle.py")],check=True,capture_output=True,text=True)
cf=R/"crossreview/inputs/candidate-free-input";ledger=jl(R/"crossreview/cross-ledger.jsonl");current=jl(cf/"current-target-cells.jsonl");bycell={(x["position"],x["locale"]):x for x in current}
report=j(R/"apply-readback-report.json");plan=j(R/"exact-hash-apply-plan.json");rows=jl(R/"apply-readback-cells.jsonl")
assert report["inputHead"]==HEAD and report["inputTree"]==TREE
assert report["productCommitParent"]==HEAD and cmd("git","-C",str(REPO),"rev-parse",report["productCommit"])==report["productCommit"]
assert cmd("git","-C",str(REPO),"rev-parse",report["productCommit"]+"^{tree}")==report["productTree"]
assert cmd("git","-C",str(REPO),"rev-parse",report["productCommit"]+"^")==HEAD
paths=set(cmd("git","-C",str(REPO),"diff-tree","--no-commit-id","--name-only","-r",report["productCommit"]).splitlines())
assert paths==set(report["productCommitPaths"]) and len(paths)==5 and all(p.startswith("web/src/lib/locales/ui-labels.") for p in paths)
subprocess.run(["git","-C",str(REPO),"diff","--check",HEAD,report["productCommit"]],check=True,capture_output=True,text=True)
assert len(ledger)==len(rows)==240 and [(x["position"],x["locale"]) for x in rows]==[(x["position"],x["locale"]) for x in ledger]
assert sha((R/"apply-readback-cells.jsonl").read_bytes())==report["readbackCellsSha256"]
assert sha((R/"exact-hash-apply-plan.json").read_bytes())==report["applyPlanSha256"]
assert sha((R/"crossreview/SHA256SUMS.txt").read_bytes())==report["crossBundleChecksumListSha256"]
base_cache={};post_cache={};changed={};counts=Counter();pins=j(cf/"catalog-file-pins.json")
for x,r in zip(ledger,rows):
 k=(x["position"],x["locale"]);c=bycell[k];path=c["catalogPath"];source=x["sourceKey"]
 assert r["sourceKeySha256"]==x["sourceKeySha256"] and r["sourceContextSha256"]==x["sourceContextSha256"] and r["decision"]==x["decision"]
 assert r["catalogPath"]==path and r["currentTargetSha256"]==c["currentTargetSha256"]
 if path not in base_cache:
  raw=subprocess.check_output(["git","-C",str(REPO),"show",f"{HEAD}:{path}"]);base_cache[path]=json.loads(raw);post_cache[path]=json.loads((REPO/path).read_text(encoding="utf-8"))
  assert sha(raw)==pins["localeCatalogs"][c["locale"]]["sha256"]
  assert set(base_cache[path])==set(post_cache[path])
 before=base_cache[path][source];actual_target=post_cache[path][source]
 assert before==c["currentTarget"] and sha(before)==c["currentTargetSha256"]
 if x["decision"]=="hash-only-hold":
  expected=before;assert x["selectedTarget"] is None and "currentTarget" not in x
  assert r["hashOnlyHold"] is True and "selectedTargetSha256" not in r
 else:
  expected=x["selectedTarget"];assert r["hashOnlyHold"] is False and r["selectedTargetSha256"]==x["selectedTargetSha256"]
 assert actual_target==expected and r["expectedAfterTargetSha256"]==sha(expected)==r["observedAfterTargetSha256"] and r["readbackMatches"] is True
 if before!=actual_target:changed.setdefault(path,set()).add(source)
 counts[x["decision"]]+=1
assert counts=={"keep-current":222,"select-primary-proposal":8,"hash-only-hold":10}
assert report["outcomeCounts"]=={"selected-primary":8,"keep-current":222,"hash-only-hold":10}
assert report["allBaseCatalogFilesMatchedPins"] and report["allBaseCurrentTargetsMatched"] and report["allFinalTargetsReadBack"] and report["allCatalogKeySetsUnchanged"] and report["allHoldCurrentHashesPreserved"]
assert len(plan["selectedChanges"])==8 and len(plan["hashOnlyHolds"])==10
expected_selected={(x["position"],x["locale"]) for x in ledger if x["decision"]=="select-primary-proposal"}
assert {(x["position"],x["locale"]) for x in plan["selectedChanges"]}==expected_selected
for a in plan["selectedChanges"]:
 x=next(y for y in ledger if y["position"]==a["position"] and y["locale"]==a["locale"])
 assert a["selectedTarget"]==x["selectedTarget"] and a["selectedTargetSha256"]==x["selectedTargetSha256"] and a["catalogPath"]==bycell[(a["position"],a["locale"])]["catalogPath"]
expected_changed={(bycell[(x["position"],x["locale"])]["catalogPath"],x["sourceKey"]) for x in ledger if x["decision"]=="select-primary-proposal"}
assert {(p,k) for p,keys in changed.items() for k in keys}==expected_changed
assert len(report["catalogFileReports"])==12
for path,rec in report["catalogFileReports"].items():
 assert sha((REPO/path).read_bytes())==rec["finalSha256"] and len(post_cache[path])==rec["finalKeyCount"]==rec["baseKeyCount"]==5441
 assert rec["keySetUnchanged"] is True and cmd("git","-C",str(REPO),"hash-object",path)==rec["finalGitBlob"]
print(json.dumps({"result":"PASS","head":HEAD,"productCommit":report["productCommit"],"productTree":report["productTree"],"reviewedCells":240,"decisionCounts":dict(counts),"catalogFilesChanged":len(paths),"readback":"PASS","catalogKeySets":"PASS","diffCheck":"PASS","nestedCrossBundle":"PASS","evidenceChecksummedFiles":len(sums)},ensure_ascii=False,indent=2))
