#!/usr/bin/env python3
from pathlib import Path
import hashlib,json,subprocess,sys
W=Path(__file__).resolve().parent; R=W.parents[4]
def die(x): raise SystemExit("FAIL: "+x)
def sha(x): return hashlib.sha256(x).hexdigest()
p=W/"SHA256SUMS.txt"; items={}
for line in p.read_text().splitlines():
 if line.strip():
  h,n=line.split("  ",1)
  if n in items: die("duplicate checksum")
  items[n]=h
actual={x.relative_to(W).as_posix() for x in W.rglob("*") if x.is_file() and x!=p}
if set(items)!=actual: die("bundle inventory")
for n,h in items.items():
 if sha((W/n).read_bytes())!=h: die("checksum "+n)
m=json.loads((W/"manifest.json").read_text()); files={x["path"]:x for x in m["files"]}
if set(files)!=actual-{"manifest.json"}: die("manifest inventory")
for n,x in files.items():
 b=(W/n).read_bytes()
 if len(b)!=x["bytes"] or sha(b)!=x["sha256"]: die("manifest "+n)
r=subprocess.run([sys.executable,str(W/"application"/"verify_application.py")],cwd=R,text=True,capture_output=True)
if r.returncode: die("application verifier: "+r.stdout+r.stderr)
print(json.dumps({"result":"PASS","files":len(items),"applicationVerifier":"PASS"},indent=2)); print(r.stdout,end="")
