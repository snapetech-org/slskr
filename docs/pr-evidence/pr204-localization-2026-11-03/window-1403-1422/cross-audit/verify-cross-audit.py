#!/usr/bin/env python3
import hashlib,json,re,subprocess,sys
from pathlib import Path
R=Path(__file__).resolve().parent
sha=lambda b:hashlib.sha256(b).hexdigest()
def j(p):return json.loads(p.read_text(encoding="utf-8"))
def jl(p):return [json.loads(x) for x in p.read_text(encoding="utf-8").splitlines() if x]
def tok(s):
 return {"ph":re.findall(r"\{[A-Za-z][A-Za-z0-9_]*\}",s),"tag":re.findall(r"</?[A-Za-z][^>]*>",s),"num":re.findall(r"(?<![A-Za-z])\d+(?:[.,]\d+)?%?(?![A-Za-z])",s),"prot":list(dict.fromkeys(m.group(0) for m in re.finditer(r"(?<![A-Za-z0-9])(?:[A-Z]{2,}[A-Z0-9]*|ffmpeg|Chromaprint|Soulseek|Spotify|YouTube|Pushbullet|Matrix|WebSocket|OpenAI)(?![A-Za-z0-9])",s)))}
# Root SHA list covers every file recursively.
pairs=[]
for line in (R/"SHA256SUMS.txt").read_text().splitlines():
 h,n=line.split("  ",1); pairs.append((Path(n.removeprefix("./")),h))
assert len(pairs)==len({p for p,h in pairs})
files={p.relative_to(R) for p in R.rglob("*") if p.is_file() and p.relative_to(R)!=Path("SHA256SUMS.txt")}
assert {p for p,h in pairs}==files
for p,h in pairs:assert sha((R/p).read_bytes())==h,str(p)
m=j(R/"manifest.json");s=j(R/"summary.json")
assert (m["repo"],m["pr"],m["head"],m["tree"])==("snapetech-org/slskR",204,"727500e46852a5b6578e571781693857510943d9","c71165c20fc6ba7d49d563898ea2ec8e1e448672")
assert m["selectedPositions"]==[1403,1422] and m["cellCount"]==240
# Verify each nested packet's local file manifest.
for sub in (R/"evidence/candidate-free-input",R/"evidence/primary-review",R/"independent-review"):
 listed=[]
 for line in (sub/"SHA256SUMS.txt").read_text().splitlines():
  h,n=line.split(None,1);listed.append((Path(n.lstrip("* ")),h))
 assert {p.name for p,h in listed}=={p.name for p in sub.iterdir() if p.is_file() and p.name!="SHA256SUMS.txt"}
 for p,h in listed:assert sha((sub/p).read_bytes())==h,(sub,p)
cf=R/"evidence/candidate-free-input";pr=R/"evidence/primary-review";ir=R/"independent-review"
cm=j(cf/"manifest.json");pm=j(pr/"manifest.json");im=j(ir/"manifest.json")
assert cm["head"]==pm["head"]==im["head"]==m["head"] and cm["tree"]==pm["tree"]==im["tree"]==m["tree"]
subprocess.run([sys.executable,str(ir/"verify-independent.py")],check=True,capture_output=True,text=True)
assert im["primaryMaterialsOpened"] is False
base={(x["position"],x["locale"]):x for x in jl(cf/"current-target-cells.jsonl")}
ind={(x["position"],x["locale"]):x for x in jl(ir/"independent-review.jsonl")}
prim={(x["position"],x["locale"]):x for x in jl(pr/"review-ledger.jsonl")}
pdec={(x["position"],x["locale"]):x for x in j(pr/"review-decisions.json")}
rows=jl(R/"resolution-ledger.jsonl");locs=cm["localeOrder"]
assert len(base)==len(ind)==len(prim)==len(rows)==240 and len(pdec)==64
assert [(x["position"],x["locale"]) for x in rows]==[(p,l) for p in range(1403,1423) for l in locs]
cnt={"retain":0,"update":0,"hold":0};cmp={x:0 for x in ("no-change-agreement","primary-only-change","independent-only-change","independent-noop-agreement","primary-change-resolves-independent-hold","shared-change-same-target","shared-change-different-target")}
for r in rows:
 k=(r["position"],r["locale"]);b=base[k];i=ind[k];p=prim[k];d=pdec.get(k)
 for field,vals in (("sourceKey",(b["sourceKey"],i["sourceKey"],p["sourceKey"])),("sourceKeySha256",(b["sourceKeySha256"],i["sourceKeySha256"],p["sourceKeySha256"])),("currentTargetSha256",(b["currentTargetSha256"],i["currentTargetSha256"],p["currentTargetSha256"]))):assert len(set(vals))==1,(k,field)
 assert r["sourceContextSha256"]==b["sourceContextSha256"]==i["sourceContextSha256"]==p["callerEvidence"]["callerContextSha256"]
 assert r["callerRefs"]==b["callerRefs"]==i["callerRefs"]==p["callerEvidence"]["callerRefs"]
 assert r["catalogPath"]==b["catalogPath"]==i["catalogPath"]==p["catalog"]["path"]
 assert r["catalogFileSha256"]==b["catalogFileSha256"]==i["catalogFileSha256"]==p["catalog"]["fileSha256"]
 assert r["catalogGitBlob"]==b["catalogGitBlob"]==i["catalogGitBlob"]==p["catalog"]["gitBlob"]
 pt=d["target"] if d else b["currentTarget"];assert r["primaryProposal"]==pt
 if i["disposition"]=="update" and d:rel="shared-change-same-target" if i["independentProposal"]==pt else "shared-change-different-target"
 elif i["disposition"]=="update" and i["independentProposal"]==b["currentTarget"]:rel="independent-noop-agreement"
 elif i["disposition"]=="update":rel="independent-only-change"
 elif i["disposition"]=="hold" and d:rel="primary-change-resolves-independent-hold"
 elif d:rel="primary-only-change"
 else:rel="no-change-agreement"
 assert r["reviewerComparison"]==rel;cmp[rel]+=1
 if d:selected,src,disp=pt,"primary","update"
 elif i["disposition"]=="update" and i["independentProposal"]!=b["currentTarget"]:selected,src,disp=i["independentProposal"],"independent","update"
 elif i["disposition"]=="hold":selected,src,disp=b["currentTarget"],"independent","hold"
 else:selected,src,disp=b["currentTarget"],"current","retain"
 assert (r["selectedTarget"],r["selectedSource"],r["finalDisposition"])==(selected,src,disp)
 cnt[disp]+=1
 assert r["selectedTargetSha256"]==sha(selected.encode())
 st=tok(b["sourceKey"]);ft=tok(selected)
 assert st["ph"]==ft["ph"] and st["tag"]==ft["tag"] and st["num"]==ft["num"] and all(x in ft["prot"] for x in st["prot"])
assert cnt==s["finalDispositionCounts"]=={"retain":175,"update":65,"hold":0}
assert cmp==s["comparisonCounts"]=={"no-change-agreement":174,"primary-only-change":44,"independent-only-change":1,"independent-noop-agreement":1,"primary-change-resolves-independent-hold":1,"shared-change-same-target":8,"shared-change-different-target":11}
h=jl(cf/"prior-hold-reattestation.jsonl");prev=jl(cf/"prior-selection-reattestation.jsonl")
assert len(h)==35 and all(x["disposition"]=="hold" and x["reattestation"]=="same" and x["currentTarget"]==x["priorCurrentTarget"] and x["currentTargetSha256"]==x["priorCurrentTargetSha256"] for x in h)
assert len(prev)==160 and all(x["selectionMatchesCurrentQueue"] and x["priorSourceKey"]==x["currentQueueSourceKey"] for x in prev)
assert len(jl(R/"apply-plan.jsonl"))==65
pins=j(cf/"catalog-file-pins.json")["localeCatalogs"];titles=jl(R/"catalog-title-evidence.jsonl");assert len(titles)==12
for x in titles:
 pin=pins[x["locale"]];f=R/"evidence/pinned-catalogs"/Path(pin["path"]).name;cat=j(f)
 assert sha(f.read_bytes())==pin["sha256"]==x["catalogFileSha256"]
 assert x["sourceLiteralWishlistRetry"]["catalogValue"]==cat["Wishlist Retry"]
 assert x["sourceLiteralLibraryHealth"]["catalogValue"]==cat["Library Health"]
 assert x["runtimeRecipeTitles"]["libraryHealthLocaleTitle"]==cat["Library Health Scan"]
 row=next(y for y in rows if y["position"]==1416 and y["locale"]==x["locale"])
 assert cat["Wishlist Retry"] in row["selectedTarget"] and cat["Library Health"] in row["selectedTarget"]
cpins=j(cf/"catalog-file-pins.json")["callerFiles"];ce=j(R/"code-evidence.json")
for x in ce["files"]:
 f=R/"evidence/pinned-source"/x["path"];assert sha(f.read_bytes())==x["fileSha256"]==cpins[x["path"]]["sha256"]
 text=f.read_text().splitlines();assert all(text[y["line"]-1]==y["text"] for y in x["selectedLines"])
before=j(R/"before-live-attestation.json");after=j(R/"after-live-attestation.json")
assert m["beforeLiveAttestationSha256"]==sha((R/"before-live-attestation.json").read_bytes())
assert m["afterLiveAttestationSha256"]==sha((R/"after-live-attestation.json").read_bytes())
for a in (before,after):
 assert a["pr"]["number"]==204 and a["pr"]["state"]=="OPEN" and a["pr"]["isDraft"] is True
 assert a["pr"]["headRefOid"]==m["head"] and a["localHeadTree"]==m["tree"]
 assert a["refs"]["refs/heads/codex/slskr-l10n-audit-20261030"]==a["refs"]["refs/pull/204/head"]==m["head"]
 assert a["pr"]["baseRefOid"]==m["base"]
assert before["refs"]["refs/heads/codex/slskr-l10n-audit-20261030"]==after["refs"]["refs/heads/codex/slskr-l10n-audit-20261030"]
assert before["refs"]["refs/pull/204/head"]==after["refs"]["refs/pull/204/head"]
assert before["refs"]["refs/heads/main"]==after["refs"]["refs/heads/main"]=="32c8c40666d93690b8b1847001fd66001a4eaf99"
assert after["pr"]["baseRefOid"]!=after["refs"]["refs/heads/main"]
assert after["localStatusPorcelain"]==""
print(json.dumps({"result":"PASS","head":m["head"],"tree":m["tree"],"cells":len(rows),"finalDispositionCounts":cnt,"comparisonCounts":cmp,"priorHoldsUnchanged":len(h),"priorSelectionsReattested":len(prev),"catalogFilesRehashed":12,"sourceFilesRehashed":2,"tokenChecks":"PASS","rootChecksumEntries":len(pairs),"checksumListSha256":sha((R/"SHA256SUMS.txt").read_bytes()),"manifestSha256":sha((R/"manifest.json").read_bytes())},ensure_ascii=False,indent=2))
