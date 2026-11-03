#!/usr/bin/env python3
from pathlib import Path
from collections import Counter
import hashlib,json,subprocess,sys
A=Path(__file__).resolve().parent; W=A.parent; R=A.parents[4]
B="44b37bd94385128d5bb5287aa1545901282bdfcb"; BT="02c3f149a079c67b010d973dd02ca15776ad1610"
C="a8df4148b178a49e21b1cb04cb16b8d8c4763c49"; CT="e840383ab2bab43c0dd094cb6fa339a116ab3b2e"
def die(x): raise SystemExit("FAIL: "+x)
def sha(x): return hashlib.sha256(x).hexdigest()
def jl(p): return [json.loads(x) for x in p.read_text().splitlines() if x.strip()]
def j(p): return json.loads(p.read_text())
def git(*x): return subprocess.check_output(["git","-C",str(R),*x],text=True).strip()
def obj(rev,p):
 try: raw=subprocess.check_output(["git","-C",str(R),"show",f"{rev}:{p}"])
 except subprocess.CalledProcessError: die("missing Git object "+p)
 return raw,json.loads(raw)
rec=j(A/"commit-record.json")
if [rec["parentHead"],rec["parentTree"],rec["catalogCommit"],rec["catalogTree"]]!=[B,BT,C,CT]: die("commit pins")
if git("rev-parse",B)!=B or git("rev-parse",f"{B}^{{tree}}")!=BT: die("parent/tree")
if git("rev-parse",C)!=C or git("rev-parse",f"{C}^{{tree}}")!=CT: die("catalog commit/tree")
if git("rev-list","--parents","-n","1",C).split()!=[C,B]: die("catalog commit parent")
if git("diff","--name-only",B,C,"--",".github/workflows").strip(): die("workflow path changed")
cross=W/"review-bundle"; sums={}
for line in (cross/"SHA256SUMS.txt").read_text().splitlines():
 if line.strip():
  h,p=line.split("  ",1); sums[p]=h
actual={x.relative_to(cross).as_posix() for x in cross.rglob("*") if x.is_file() and x.name!="SHA256SUMS.txt"}
if set(sums)!=actual: die("cross packet inventory")
for p,h in sums.items():
 if sha((cross/p).read_bytes())!=h: die("cross packet checksum "+p)
run=subprocess.run([sys.executable,str(cross/"verify_cross_audit.py")],cwd=cross,text=True,capture_output=True)
if run.returncode: die("cross verifier: "+run.stdout+run.stderr)
L=jl(cross/"cross-ledger.jsonl"); P=jl(A/"application-plan.jsonl"); Q=jl(A/"application-readback.jsonl")
if len(L)!=240 or len(Q)!=240: die("cell coverage")
counts=Counter(x["crossDisposition"] for x in L)
if counts!=Counter({"accept-current":177,"correction":50,"refinement":13}): die("dispositions")
path=lambda x:x.get("catalogPath", "web/src/lib/locales/ui-labels."+x["locale"]+".json")
key=lambda x:(path(x),x["sourceKey"])
sel=[x for x in L if x["crossDisposition"] in ("correction","refinement")]
pb={key(x):x for x in P}
if len(sel)!=63 or len(P)!=63 or set(pb)!={key(x) for x in sel}: die("selected plan")
paths={path(x) for x in sel}
changed=set(git("diff","--name-only",B,C).splitlines())
if changed!=paths: die("catalog commit file scope")
cats={}
for x in L:
 p=path(x)
 if p not in cats:
  _,o=obj(B,p); _,n=obj(C,p)
  if len(o)!=5441 or len(n)!=5441 or list(o)!=list(n): die("key order/count "+p)
  cats[p]=(o,n)
for x,q in zip(L,Q):
 k=key(x); p=path(x); o,n=cats[p]; src=x["sourceKey"]
 if o.get(src)!=x["currentTarget"] or sha(o[src].encode())!=x["currentTargetSha256"]: die("preimage "+str(k))
 if (q["position"],q["locale"],q["sourceKey"],q["catalogPath"])!=(x["position"],x["locale"],src,p): die("readback cell "+str(k))
 if q["preimageSha256"]!=x["currentTargetSha256"] or q["actualTarget"]!=n[src] or q["expectedTarget"]!=x["selectedTarget"] or q["actualTargetSha256"]!=sha(n[src].encode()) or q["expectedTargetSha256"]!=x["selectedTargetSha256"] or q["readbackMatches"] is not True: die("readback target "+str(k))
 if q["crossDisposition"]!=x["crossDisposition"]: die("readback disposition")
 if x["crossDisposition"]=="accept-current":
  if n[src]!=o[src]: die("accept-current changed")
 else:
  p=pb[k]
  if p["preimageTarget"]!=o[src] or p["preimageSha256"]!=sha(o[src].encode()) or p["selectedTarget"]!=n[src] or p["selectedTargetSha256"]!=sha(n[src].encode()): die("selected exact hash")
for p,(o,n) in cats.items():
 if {k for k in o if o[k]!=n[k]}!={x["sourceKey"] for x in sel if path(x)==p}: die("extra catalog values "+p)
H=jl(cross/"prior-hold-reattestation.jsonl")
if len(H)!=35: die("carry hold count")
for h in H:
 p=h["currentCatalogPath"]
 if p not in cats:
  _,o=obj(B,p); _,n=obj(C,p); cats[p]=(o,n)
 o,n=cats[p]; k=h["sourceKey"]
 if o.get(k)!=n.get(k) or n.get(k)!=h["currentTarget"] or sha(n[k].encode())!=h["currentTargetSha256"]: die("carried hold "+str(h["position"]))
S=jl(cross/"prior-selection-reattestation.jsonl")
if len(S)!=200 or any(x.get("selectionMatchesCurrentQueue") is not True for x in S): die("prior source selections")
v=j(A/"application-verification.json")
for k,x in {"result":"PASS","reviewedCellsReadBack":240,"selectedChangesReadBack":63,"retainedCurrentCells":177,"corrections":50,"refinements":13,"carriedHoldsPreserved":35,"priorSelectionsReattested":200,"workflowsChanged":False}.items():
 if v.get(k)!=x: die("application summary "+k)
print(json.dumps({"result":"PASS","parent":B,"parentTree":BT,"catalogCommit":C,"catalogTree":CT,"cells":240,"selected":63,"corrections":50,"refinements":13,"acceptCurrent":177,"catalogFiles":len(paths),"carriedHolds":35,"priorSelections":200,"workflowsChanged":False},indent=2))
print(run.stdout,end="")
