#!/usr/bin/env python3
import argparse,hashlib,json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parent; BASE=ROOT.parent
PLAN=json.loads((ROOT/"application-plan.json").read_text(encoding="utf-8"))
OUTPUT=json.loads((ROOT/"apply-output.json").read_text(encoding="utf-8"))
RECORD=json.loads((ROOT/"product-commit-record.json").read_text(encoding="utf-8"))
def sha(v): return hashlib.sha256(v if isinstance(v,bytes) else v.encode("utf-8")).hexdigest()
def rows(p): return [json.loads(s) for s in p.read_text(encoding="utf-8").splitlines() if s.strip()]
def git(repo,*args): return subprocess.check_output(["git","-C",str(repo),*args]).decode("utf-8")
parser=argparse.ArgumentParser(); parser.add_argument("--repo",type=Path,required=True); args=parser.parse_args(); repo=args.repo.resolve()
source=PLAN["sourcePin"]["head"]; product=RECORD["productCommit"]
if RECORD["parent"]!=source or git(repo,"rev-parse",f"{product}^").strip()!=source: raise SystemExit("FAIL source/product ancestry")
if git(repo,"rev-parse",f"{source}^{{tree}}").strip()!=PLAN["sourcePin"]["tree"] or git(repo,"rev-parse",f"{product}^{{tree}}").strip()!=RECORD["productTree"]: raise SystemExit("FAIL commit tree pin")
changes={(r["position"],r["locale"]):r for r in PLAN["changes"]}
final=rows(ROOT/"final-readback.jsonl"); cross=rows(BASE/"cross-review/cross-review-ledger.jsonl")
if len(final)!=240 or len(cross)!=240 or len(changes)!=13: raise SystemExit("FAIL row counts")
changed_paths={}
for path,pin in PLAN["catalogFiles"].items():
 before_raw=subprocess.check_output(["git","-C",str(repo),"show",f"{source}:{path}"])
 after_raw=subprocess.check_output(["git","-C",str(repo),"show",f"{product}:{path}"])
 before=json.loads(before_raw); after=json.loads(after_raw)
 if sha(before_raw)!=pin["catalogFileSha256"]: raise SystemExit(f"FAIL source file hash {path}")
 if len(before)!=5441 or len(after)!=5441 or list(before.keys())!=list(after.keys()) or sha("\n".join(before.keys()))!=pin["keyOrderSha256"]: raise SystemExit(f"FAIL key order {path}")
 expected=dict(before)
 for c in PLAN["changes"]:
  if c["catalogPath"]==path:
   if expected.get(c["sourceKey"])!=c["expectedCurrentTarget"] or sha(expected[c["sourceKey"]])!=c["expectedCurrentTargetSha256"]: raise SystemExit(f"FAIL current hash {c['position']}/{c['locale']}")
   expected[c["sourceKey"]]=c["finalTarget"]
 if expected!=after: raise SystemExit(f"FAIL non-target edits or selected target {path}")
 if before!=after:
  changed_paths[path]=sha(after_raw)
  if OUTPUT["catalogPostimages"].get(path)!=changed_paths[path]: raise SystemExit(f"FAIL postimage {path}")
 for r in cross:
  if r["catalogPath"]!=path: continue
  key=(r["position"],r["locale"]); c=changes.get(key); target=c["finalTarget"] if c else r["currentTarget"]
  if before.get(r["sourceKey"])!=r["currentTarget"] or sha(r["currentTarget"])!=r["currentTargetSha256"] or after.get(r["sourceKey"])!=target: raise SystemExit(f"FAIL catalog cell {key}")
if set(changed_paths)!=set(OUTPUT["catalogPostimages"]): raise SystemExit("FAIL changed catalog path set")
for a,b in zip(final,cross):
 key=(b["position"],b["locale"]); c=changes.get(key); target=c["finalTarget"] if c else b["currentTarget"]
 if (a["position"],a["locale"],a["sourceKeySha256"],a["sourceContextSha256"],a["beforeTargetSha256"])!=(b["position"],b["locale"],b["sourceKeySha256"],b["sourceContextSha256"],b["currentTargetSha256"]): raise SystemExit(f"FAIL readback binding {key}")
 if a["afterTargetSha256"]!=sha(target) or a["changed"]!=(c is not None): raise SystemExit(f"FAIL readback value {key}")
diff=set(git(repo,"diff-tree","--no-commit-id","--name-only","-r",product).splitlines())
if diff!=set(OUTPUT["catalogPostimages"]): raise SystemExit("FAIL product commit file scope")
if any(".github/workflows/" in p for p in diff): raise SystemExit("FAIL workflow edit")
if sha((ROOT/"final-readback.jsonl").read_bytes())!=OUTPUT["finalReadbackSha256"]: raise SystemExit("FAIL readback checksum")
if sum(r["changed"] for r in final)!=13 or sum(not r["changed"] for r in final)!=227: raise SystemExit("FAIL disposition counts")
print(json.dumps({"result":"PASS","sourceHead":source,"productCommit":product,"readbackCells":240,"changedCells":13,"retainedCells":227,"catalogFilesChanged":len(diff),"catalogKeysPerLocale":5441,"keyOrderUnchanged":True,"workflowChanges":0},sort_keys=True))
