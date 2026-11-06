#!/usr/bin/env python3
"""Verify the 240-cell slskR readback and unchanged catalog shape."""
import argparse,hashlib,json,subprocess
from pathlib import Path

def sha(b): return hashlib.sha256(b).hexdigest()
def textsha(s): return sha(s.encode("utf-8"))
def keyorder(keys): return sha((json.dumps(keys,ensure_ascii=False,separators=(",",":"))+"\n").encode("utf-8"))
def git(repo,*args): return subprocess.check_output(["git","-C",str(repo),*args])
def rows(p): return [json.loads(s) for s in Path(p).read_text(encoding="utf-8").splitlines() if s.strip()]
def main():
 ap=argparse.ArgumentParser();ap.add_argument("--repo",type=Path,required=True);ap.add_argument("--plan",type=Path,required=True);ap.add_argument("--cross-ledger",type=Path,required=True);ap.add_argument("--root-ledger",type=Path,required=True);ap.add_argument("--output",type=Path,required=True);a=ap.parse_args()
 repo=a.repo.resolve();plan=json.loads(a.plan.read_text(encoding="utf-8"));pin=plan["sourcePin"]
 if git(repo,"rev-parse","HEAD").decode().strip()!=pin["head"] or git(repo,"rev-parse","HEAD^{tree}").decode().strip()!=pin["tree"]: raise SystemExit("exact source pin changed before readback")
 changes={(r["sourceKey"],r["locale"]):r for r in plan["changes"]};cross=rows(a.cross_ledger);rootledger=rows(a.root_ledger)
 if len(cross)!=240 or len(rootledger)!=240: raise SystemExit("240-cell review coverage mismatch")
 readback=[];changed_paths=[];file_counts={}
 for rec in plan["catalogs"]:
  path=rec["path"];raw=git(repo,"show",f"{pin['head']}:{path}");before=json.loads(raw);after=json.loads((repo/path).read_text(encoding="utf-8"))
  if len(before)!=rec["entryCount"] or len(after)!=rec["entryCount"] or list(before)!=list(after) or keyorder(list(after))!=rec["keyOrderSha256"]: raise SystemExit("catalog structure/order mismatch: "+path)
  expected_file={}
  for item in plan["changes"]:
   if item["catalogPath"]==path: expected_file[item["sourceKey"]]=item
  for key in before:
   expected=expected_file.get(key)
   if expected:
    if before[key]!=expected["currentTarget"] or after[key]!=expected["finalTarget"] or textsha(after[key])!=expected["finalTargetSha256"]: raise SystemExit(f"target readback mismatch: {path}/{key}")
   elif before[key]!=after[key]: raise SystemExit(f"non-target catalog value changed: {path}/{key}")
  if before!=after: changed_paths.append(path)
  file_counts[path]=len(after)
 for c in cross:
  key=(c["sourceKey"],c["locale"]);actual=json.loads((repo/c["catalogPath"]).read_text(encoding="utf-8"))[c["sourceKey"]]
  target=changes.get(key);expected_hash=target["finalTargetSha256"] if target else c["currentTargetSha256"]
  if textsha(actual)!=expected_hash: raise SystemExit(f"240-cell hash readback mismatch: {key}")
  readback.append({"position":c["position"],"sourceKeySha256":c["sourceKeySha256"],"locale":c["locale"],"expectedTargetSha256":expected_hash,"actualTargetSha256":textsha(actual),"rootDisposition":"apply-selected" if target else "retain-current"})
 if len(changed_paths)!=8 or len(changes)!=12: raise SystemExit("application delta count mismatch")
 result={"result":"PASS","sourcePin":pin,"readbackCells":len(readback),"appliedCells":len(changes),"retainedCells":228,"holds":0,"changedCatalogs":len(changed_paths),"changedPaths":sorted(changed_paths),"entryCounts":file_counts,"catalogKeyOrderChanged":False,"workflowChanges":False,"readback":readback}
 a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
 print(json.dumps({k:v for k,v in result.items() if k!="readback"},ensure_ascii=False,indent=2))
if __name__=="__main__":main()
