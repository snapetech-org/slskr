#!/usr/bin/env python3
import hashlib,json,subprocess
from collections import Counter
from pathlib import Path
app=Path(__file__).resolve().parent
ev=app.parent
repo=Path(__file__).resolve().parents[5]
expected=("6ccefe07d8154acbc08e34249ef7039dc5bc1f08","e0c1d1341be45ed73bd30cf027b479ce3b5bb95d","codex/slskr-l10n-audit-20261030")
def sha(x):
    if isinstance(x,str): x=x.encode()
    return hashlib.sha256(x).hexdigest()
def load(p): return json.loads(p.read_text(encoding="utf-8"))
def jl(p): return [json.loads(x) for x in p.read_text(encoding="utf-8").splitlines() if x.strip()]
def git(*a): return subprocess.check_output(["git","-C",str(repo),*a],text=True).strip()
def keyhash(d): return sha("\n".join(d.keys())+"\n")
def otherhash(d,changed): return sha(json.dumps([(k,v) for k,v in d.items() if k not in changed],ensure_ascii=False,separators=(",",":")))
head,tree,branch=git("rev-parse","HEAD"),git("show","-s","--format=%T","HEAD"),git("branch","--show-current")
if (head,tree,branch)!=expected: raise SystemExit("stale parent; refusing application")
plan=jl(app/"application-plan.jsonl")
ledger=jl(ev/"root-cross-audit/root-cross-audit-ledger.jsonl")
structure=jl(ev/"candidate-free-input/catalog-structure.jsonl")
holds=jl(ev/"root-cross-audit/carry-forward-holds.jsonl")
if (len(plan),len(ledger),len(structure),len(holds))!=(43,240,12,22): raise SystemExit("packet counts mismatch")
if len({(r["catalogPath"],r["sourceKey"]) for r in plan})!=43: raise SystemExit("duplicate plan target")
cells={(int(r["position"]),r["locale"]):r for r in ledger}
if len(cells)!=240: raise SystemExit("duplicate ledger cell")
statuses=git("status","--porcelain").splitlines()
allow="?? docs/pr-evidence/pr204-localization-2026-11-03/window-1323-1342"
if any(not s.startswith(allow) for s in statuses): raise SystemExit("unexpected worktree change")
files={}
for s in structure:
    p=s["path"]; d=load(repo/p)
    if len(d)!=5441 or len(d)!=int(s["keyCount"]) or keyhash(d)!=s["orderedKeySha256"]: raise SystemExit("catalog shape mismatch: "+p)
    files[p]={"data":d,"before":sha((repo/p).read_bytes()),"keyhash":keyhash(d),"changed":set()}
for r in plan:
    p,k=r["catalogPath"],r["sourceKey"]; d=files[p]["data"]
    if d.get(k)!=r["currentTarget"] or sha(d[k])!=r["currentTargetSha256"]: raise SystemExit("current mismatch: "+str((r["position"],r["locale"])))
    if sha(r["selectedTarget"])!=r["selectedTargetSha256"]: raise SystemExit("selected target hash mismatch")
    files[p]["changed"].add(k)
pre={"schemaVersion":1,"head":head,"tree":tree,"branch":branch,"files":[]}
for p,x in files.items():
    pre["files"].append({"path":p,"beforeSha256":x["before"],"keyCount":len(x["data"]),"keyOrderSha256":x["keyhash"],"nonTargetEntriesSha256":otherhash(x["data"],x["changed"])})
(app/"application-preflight.json").write_text(json.dumps(pre,ensure_ascii=False,indent=2)+"\n")
for r in plan: files[r["catalogPath"]]["data"][r["sourceKey"]]=r["selectedTarget"]
for p,x in files.items(): (repo/p).write_text(json.dumps(x["data"],ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
read=[]
for r in ledger:
    actual=load(repo/r["catalogPath"])[r["sourceKey"]]
    if actual!=r["selectedTarget"] or sha(actual)!=r["selectedTargetSha256"]: raise SystemExit("readback mismatch")
    read.append({"position":r["position"],"locale":r["locale"],"sourceKey":r["sourceKey"],"catalogPath":r["catalogPath"],"rootAction":r["rootAction"],"expectedCurrentTarget":r["currentTarget"],"expectedTarget":r["selectedTarget"],"actualTarget":actual,"actualTargetSha256":sha(actual),"readbackMatches":True})
(app/"application-readback.jsonl").write_text("".join(json.dumps(x,ensure_ascii=False,sort_keys=True)+"\n" for x in read),encoding="utf-8")
for h in holds:
    value=load(repo/h["currentCatalogPath"])[h["sourceKey"]]
    if value!=h["priorCurrentTarget"] or sha(value)!=h["priorCurrentTargetSha256"]: raise SystemExit("carry-forward hold changed")
post=[]
for p,x in files.items():
    d=load(repo/p)
    if len(d)!=len(x["data"]) or keyhash(d)!=x["keyhash"] or otherhash(d,x["changed"])!=next(f["nonTargetEntriesSha256"] for f in pre["files"] if f["path"]==p): raise SystemExit("catalog invariant failed: "+p)
    post.append({"path":p,"postApplyFileSha256":sha((repo/p).read_bytes()),"changedTargetCount":sum(r["catalogPath"]==p for r in plan)})
counts=Counter(r["rootAction"] for r in ledger)
ver={"schemaVersion":1,"result":"PASS","parentHead":head,"parentTree":tree,"readbackCells":len(read),"selectedUpdates":len(plan),"retains":counts["retain"],"holds":counts["hold"],"carryForwardHolds":len(holds),"carryForwardHoldsPreserved":True,"catalogCount":len(files),"catalogKeyOrderPreserved":True,"nonTargetValuesPreserved":True,"catalogFiles":post}
(app/"application-verification.json").write_text(json.dumps(ver,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print(json.dumps(ver,ensure_ascii=False,indent=2))
