#!/usr/bin/env python3
import hashlib,json,subprocess
from collections import Counter
from pathlib import Path
app=Path(__file__).resolve().parent
ev=app.parent
root=Path(__file__).resolve().parents[5]
def sha(x):
    if isinstance(x,str): x=x.encode()
    return hashlib.sha256(x).hexdigest()
def load(p): return json.loads(p.read_text(encoding="utf-8"))
def jl(p): return [json.loads(x) for x in p.read_text(encoding="utf-8").splitlines() if x.strip()]
def keyhash(d): return sha("\n".join(d.keys())+"\n")
def otherhash(d,changed): return sha(json.dumps([(k,v) for k,v in d.items() if k not in changed],ensure_ascii=False,separators=(",",":")))
def check_sums(d):
    for line in (d/"SHA256SUMS.txt").read_text(encoding="utf-8").splitlines():
        if not line.strip(): continue
        expected,name=line.split(maxsplit=1); path=d/name.strip().lstrip("*")
        if not path.is_file() or sha(path.read_bytes())!=expected: raise SystemExit("checksum mismatch: "+str(path))
for name in ("candidate-free-input","primary-review","independent-blind-review","root-cross-audit"): check_sums(ev/name)
plan=jl(app/"application-plan.jsonl")
ledger=jl(ev/"root-cross-audit/root-cross-audit-ledger.jsonl")
readback=jl(app/"application-readback.jsonl")
structure=jl(ev/"candidate-free-input/catalog-structure.jsonl")
pre=load(app/"application-preflight.json")
ver=load(app/"application-verification.json")
holds=jl(ev/"root-cross-audit/carry-forward-holds.jsonl")
if (len(plan),len(ledger),len(readback),len(structure),len(holds))!=(43,240,240,12,22): raise SystemExit("row count mismatch")
by_cell={(int(r["position"]),r["locale"]):r for r in ledger}
if len(by_cell)!=240 or len({(int(r["position"]),r["locale"]) for r in readback})!=240: raise SystemExit("duplicate cell")
for r in readback:
    cell=by_cell[(int(r["position"]),r["locale"])]
    actual=json.loads((root/r["catalogPath"]).read_text(encoding="utf-8"))[r["sourceKey"]]
    if actual!=r["expectedTarget"] or actual!=r["actualTarget"] or sha(actual)!=r["actualTargetSha256"] or actual!=cell["selectedTarget"]: raise SystemExit("readback mismatch")
    if r["rootAction"]!=cell["rootAction"]: raise SystemExit("disposition mismatch")
for r in plan:
    cell=by_cell[(int(r["position"]),r["locale"])]
    if cell["rootAction"]!="proposal" or r["selectedTarget"]!=cell["selectedTarget"]: raise SystemExit("plan/root mismatch")
for h in holds:
    actual=json.loads((root/h["currentCatalogPath"]).read_text(encoding="utf-8"))[h["sourceKey"]]
    if actual!=h["priorCurrentTarget"] or sha(actual)!=h["priorCurrentTargetSha256"]: raise SystemExit("carry-forward hold changed")
orders=[]
for info in structure:
    path=root/info["path"]; data=load(path); keys=list(data); orders.append(keys)
    if len(data)!=info["keyCount"] or keyhash(data)!=info["orderedKeySha256"]: raise SystemExit("catalog key order mismatch")
    before=next(x for x in pre["files"] if x["path"]==info["path"])
    changed={r["sourceKey"] for r in plan if r["catalogPath"]==info["path"]}
    if otherhash(data,changed)!=before["nonTargetEntriesSha256"]: raise SystemExit("non-target value mismatch")
    after=next(x for x in ver["catalogFiles"] if x["path"]==info["path"])
    if sha(path.read_bytes())!=after["postApplyFileSha256"]: raise SystemExit("post-apply file hash mismatch")
if any(keys!=orders[0] for keys in orders[1:]): raise SystemExit("locale key sets/order differ")
if "\u200b" in next(r for r in readback if r["position"]==1327 and r["locale"]=="ko")["actualTarget"]: raise SystemExit("Korean format controls remain")
counts=Counter(r["rootAction"] for r in ledger)
if counts!={"proposal":43,"retain":196,"hold":1}: raise SystemExit("root disposition counts mismatch")
if ver["result"]!="PASS" or ver["readbackCells"]!=240 or ver["selectedUpdates"]!=43 or ver["carryForwardHoldsPreserved"] is not True: raise SystemExit("application summary mismatch")
changed=subprocess.check_output(["git","-C",str(root),"diff","--name-only"],text=True).splitlines()
expected={r["catalogPath"] for r in plan}
if set(changed)!=expected or any(p.startswith(".github/workflows/") for p in changed): raise SystemExit("tracked diff scope mismatch")
print(json.dumps({"result":"PASS","cells":240,"updates":43,"retains":196,"currentHolds":1,"carryForwardHolds":22,"catalogs":12,"catalogOrder":"PASS","nonTargets":"PASS","workflowsChanged":False},indent=2))
