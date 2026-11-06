#!/usr/bin/env python3
"""Apply only cross-reviewed slskR W1663-W1682 target values."""
import argparse,hashlib,json,os,subprocess,tempfile
from pathlib import Path

def sha(b): return hashlib.sha256(b).hexdigest()
def textsha(s): return sha(s.encode("utf-8"))
def keyorder(keys): return sha((json.dumps(keys,ensure_ascii=False,separators=(",",":"))+"\n").encode("utf-8"))
def git(repo,*args): return subprocess.check_output(["git","-C",str(repo),*args],text=True).strip()
def fail(s): raise SystemExit("FAIL: "+s)
def main():
 ap=argparse.ArgumentParser();ap.add_argument("--repo",type=Path,required=True);ap.add_argument("--plan",type=Path,required=True);ap.add_argument("--output",type=Path,required=True);a=ap.parse_args()
 repo=a.repo.resolve();plan=json.loads(a.plan.read_text(encoding="utf-8"));pin=plan["sourcePin"]
 if git(repo,"rev-parse","HEAD")!=pin["head"] or git(repo,"rev-parse","HEAD^{tree}")!=pin["tree"]: fail("exact input HEAD/tree mismatch")
 if git(repo,"status","--porcelain=v1","--untracked-files=no"): fail("tracked worktree not clean before apply")
 docs={};raws={}
 for rec in plan["catalogs"]:
  path=rec["path"];raw=(repo/path).read_bytes();doc=json.loads(raw)
  if sha(raw)!=rec["preimageSha256"]: fail("catalog preimage mismatch: "+path)
  if len(doc)!=rec["entryCount"] or keyorder(list(doc))!=rec["keyOrderSha256"]: fail("catalog shape/order mismatch: "+path)
  if raw!=(json.dumps(doc,ensure_ascii=False,indent=2)+"\n").encode("utf-8"): fail("unexpected catalog serialization: "+path)
  docs[path]=doc;raws[path]=raw
 before={path:json.loads(raw) for path,raw in raws.items()}
 seen=set()
 for cell in plan["changes"]:
  key=(cell["sourceKey"],cell["locale"])
  if key in seen: fail("duplicate selected cell")
  seen.add(key);path=cell["catalogPath"]
  if path not in docs: fail("un-pinned catalog path: "+path)
  if textsha(cell["sourceKey"])!=cell["sourceKeySha256"]: fail("source key hash mismatch: "+repr(key))
  doc=docs[path]
  if cell["sourceKey"] not in doc or doc[cell["sourceKey"]]!=cell["currentTarget"] or textsha(doc[cell["sourceKey"]])!=cell["currentTargetSha256"]: fail("target preimage mismatch: "+repr(key))
  if textsha(cell["finalTarget"])!=cell["finalTargetSha256"]: fail("target postimage hash mismatch: "+repr(key))
  doc[cell["sourceKey"]]=cell["finalTarget"]
 if len(seen)!=12: fail("selected cell count mismatch")
 outputs={}
 for path,doc in docs.items():
  expected=json.loads(raws[path])
  for cell in plan["changes"]:
   if cell["catalogPath"]==path: expected[cell["sourceKey"]]=cell["finalTarget"]
  if doc!=expected or list(doc)!=list(before[path]): fail("unexpected catalog mutation/order change: "+path)
  if doc!=before[path]: outputs[path]=(json.dumps(doc,ensure_ascii=False,indent=2)+"\n").encode("utf-8")
 if len(outputs)!=8: fail("changed catalog count mismatch")
 for path,data in outputs.items():
  target=repo/path;tmp=None
  try:
   with tempfile.NamedTemporaryFile(prefix=".w1663-1682-",suffix=".tmp",dir=target.parent,delete=False) as f:
    f.write(data);f.flush();os.fsync(f.fileno());tmp=f.name
   os.replace(tmp,target)
  finally:
   if tmp and os.path.exists(tmp): os.unlink(tmp)
  if target.read_bytes()!=data: fail("postimage readback mismatch: "+path)
 changed=git(repo,"diff","--name-only").splitlines()
 if changed!=sorted(outputs): fail("tracked changes differ from approved catalogs: "+repr(changed))
 result={"result":"PASS","sourcePin":pin,"selectedCells":len(seen),"changedCatalogs":len(outputs),"changedPaths":sorted(outputs),"catalogPreimageSha256":{p:sha(raws[p]) for p in sorted(raws)},"catalogPostimageSha256":{p:sha((repo/p).read_bytes()) for p in sorted(outputs)},"keyCounts":{p:len(docs[p]) for p in sorted(docs)},"keyOrderChanged":False,"workflowChanges":False}
 a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
 print(json.dumps(result,ensure_ascii=False,sort_keys=True))
if __name__=="__main__":main()
