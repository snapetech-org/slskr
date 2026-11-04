#!/usr/bin/env python3
"""Verify portable slskR PR #204 W1523-W1542 cross-review bundle."""
import hashlib,json,re
from collections import Counter
from pathlib import Path
R=Path(__file__).resolve().parent
HEAD="f6fbf614e7e2ff869e4ca86ae96103cff604b79c"
TREE="536b0fc02a3c16fa7eb0f9d5504a4c8c91b2152d"
LOCS=["es","zh-Hans","hi","de","ja","fr","pt-BR","ar","ko","zh-Hant","vi","id"]
def sha(x):
 if isinstance(x,str):x=x.encode("utf-8")
 return hashlib.sha256(x).hexdigest()
def j(p):return json.loads(p.read_text(encoding="utf-8"))
def jl(p):return [json.loads(s) for s in p.read_text(encoding="utf-8").splitlines() if s]
def sums(d):
 q={}
 for line in (d/"SHA256SUMS.txt").read_text(encoding="utf-8").splitlines():
  h,n=line.split(None,1);n=n.lstrip("* ");assert n not in q;q[n]=h
 actual={p.name for p in d.iterdir() if p.is_file() and p.name!="SHA256SUMS.txt"}
 assert set(q)==actual,(d,set(q)^actual)
 for n,h in q.items():assert sha((d/n).read_bytes())==h,(d,n)
 return len(q)
def rootsums():
 q={}
 for line in (R/"SHA256SUMS.txt").read_text(encoding="utf-8").splitlines():
  h,n=line.split(None,1);n=n.lstrip("* ");assert n not in q;q[n]=h
 actual={p.relative_to(R).as_posix() for p in R.rglob("*") if p.is_file() and p.name!="SHA256SUMS.txt"}
 assert set(q)==actual,set(q)^actual
 for n,h in q.items():assert sha((R/n).read_bytes())==h,n
 return q
def index(p,fields=("position","locale")):
 out={}
 for raw in p.read_bytes().splitlines(keepends=True):
  if raw.strip():
   x=json.loads(raw);out[tuple(x[k] for k in fields)]=(x,sha(raw))
 return out
def indexpos(p):
 out={}
 for raw in p.read_bytes().splitlines(keepends=True):
  if raw.strip():
   x=json.loads(raw);out[x["position"]]=(x,sha(raw))
 return out
def toks(s):
 p=re.findall(r"\{[A-Za-z][A-Za-z0-9_]*\}",s);m=re.findall(r"</?[A-Za-z][^>]*>",s);n=re.findall(r"(?<![A-Za-z])\d+(?:[.,]\d+)?%?(?![A-Za-z])",s);z=[]
 for x in re.findall(r"(?<![A-Za-z0-9])(?:[A-Z]{2,}[A-Z0-9]*|ffmpeg|Chromaprint|Soulseek|Spotify|YouTube|Pushbullet|Matrix|WebSocket|OpenAI)(?![A-Za-z0-9])",s):
  if x not in z:z.append(x)
 return p,m,n,z
rs=rootsums();m=j(R/"cross-manifest.json");assert m["head"]==HEAD and m["tree"]==TREE
assert m["fileHashes"]=={k:v for k,v in rs.items() if k!="cross-manifest.json"}
for n,h in m["fileHashes"].items():assert sha((R/n).read_bytes())==h,n
cf=R/"inputs/candidate-free-input";pr=R/"inputs/primary-review";br=R/"inputs/blind-review"
cc,pc,bc=sums(cf),sums(pr),sums(br)
cm=j(cf/"manifest.json");ps=j(pr/"SUMMARY.json");bm=j(br/"manifest.json")
assert cm["head"]==ps["head"]==bm["head"]==HEAD and cm["tree"]==ps["tree"]==bm["tree"]==TREE
assert cm["cellCount"]==ps["cellCount"]==bm["cellCount"]==240 and cm["selectedPositions"]==[1523,1542]
prov=j(R/"provenance.json");assert prov["livePrVerification"]["result"]=="PASS" and prov["livePrVerification"]["head"]==HEAD and prov["livePrVerification"]["tree"]==TREE
for name in ("candidateFree","primary","blind"):assert prov["upstreamPackets"][name]["result"]=="PASS"
assert prov["upstreamPackets"]["candidateFree"]["checksumListSha256"]==sha((cf/"SHA256SUMS.txt").read_bytes())
assert prov["upstreamPackets"]["primary"]["checksumListSha256"]==sha((pr/"SHA256SUMS.txt").read_bytes())
assert prov["upstreamPackets"]["blind"]["checksumListSha256"]==sha((br/"SHA256SUMS.txt").read_bytes())
src=indexpos(cf/"source-queue.jsonl");ctx=indexpos(cf/"source-contexts.jsonl");cur=index(cf/"current-target-cells.jsonl");pl=index(pr/"primary-ledger.jsonl");pp=index(pr/"proposals.jsonl");bl=index(br/"review.jsonl")
ledger=jl(R/"cross-ledger.jsonl");assert len(ledger)==240
assert [(x["position"],x["locale"]) for x in ledger]==[(p,l) for p in range(1523,1543) for l in LOCS]
counts=Counter()
for x in ledger:
 k=(x["position"],x["locale"]);p=x["position"];s,shash=src[p];cctx,chash=ctx[p];c,cellhash=cur[k];a,ahash=pl[k];b,bhash=bl[k];proposal=pp.get(k)
 assert x["sourceKey"]==s["sourceKey"] and x["sourceKeySha256"]==s["sourceKeySha256"]==sha(s["sourceKey"])
 assert x["sourceContextSha256"]==cctx["callerContextSha256"]
 assert x["callerReferences"]==[{"path":q["path"],"line":q["line"]} for q in cctx["callers"]]
 assert x["candidateFreeRows"]=={"sourceQueueRowSha256":shash,"sourceContextRowSha256":chash,"currentTargetCellRowSha256":cellhash}
 assert x["currentTargetSha256"]==c["currentTargetSha256"]==sha(c["currentTarget"])
 prlink=x["proposalReconciliation"]["primary"];blink=x["proposalReconciliation"]["blind"]
 assert prlink["ledgerRowSha256"]==ahash and prlink["disposition"]==a["disposition"] and prlink["selectedTargetSha256"]==a["selectedTargetSha256"]
 assert blink["reviewRowSha256"]==bhash and blink["disposition"]==b["disposition"] and blink["proposedTargetSha256"]==sha(b["proposedTarget"])
 assert prlink["proposalRowSha256"]==(proposal[1] if proposal else None) and prlink["proposalTargetSha256"]==(proposal[0]["selectedTargetSha256"] if proposal else None)
 assert x["confidence"] in ("high","moderate","low") and x["rationale"]
 counts[x["decision"]]+=1
 if x["decision"]=="hash-only-hold":
  assert x["selectedTarget"] is None and x["selectedTargetSha256"] is None and x["selectedTargetOrigin"] is None
  assert "currentTarget" not in x and "proposedTarget" not in x and x["confidence"]=="low"
 else:
  assert x.get("currentTarget")==c["currentTarget"] and isinstance(x["selectedTarget"],str) and x["selectedTargetSha256"]==sha(x["selectedTarget"])
  st=toks(s["sourceKey"]);tt=toks(x["selectedTarget"]);assert st[:3]==tt[:3] and all(t in tt[3] for t in st[3])
  if x["decision"]=="keep-current":assert x["selectedTarget"]==c["currentTarget"] and x["selectedTargetOrigin"]=="candidate-free-input/current-target-cells.jsonl"
  else:
   assert x["decision"]=="select-primary-proposal" and proposal and x["selectedTarget"]==proposal[0]["selectedTarget"] and x["selectedTargetOrigin"]=="primary-review/proposals.jsonl"
   assert any(q["reviewer"]=="primary" and q["rowSha256"]==proposal[1] and q["targetSha256"]==proposal[0]["selectedTargetSha256"] for q in x["selectedProposalLinks"])
   if b["disposition"]=="revise" and b["proposedTarget"]==x["selectedTarget"]:
    assert any(q["reviewer"]=="blind" and q["rowSha256"]==bhash and q["targetSha256"]==sha(b["proposedTarget"]) for q in x["selectedProposalLinks"])
 agreement=x["proposalReconciliation"]["agreement"]
 if x["decision"]=="hash-only-hold":expected="proposals-diverge-held" if b["disposition"]=="revise" else "primary-proposal-unconfirmed-held"
 elif x["decision"]=="select-primary-proposal":expected=("exact-target-agreement" if sha(b["proposedTarget"])==x["selectedTargetSha256"] else "shared-revision-different-wording") if b["disposition"]=="revise" else "primary-selected-blind-accepts-current"
 else:expected="current-retained"
 assert agreement==expected,(x["position"],x["locale"],agreement,expected)
assert counts=={"keep-current":222,"select-primary-proposal":8,"hash-only-hold":10},counts
summary=j(R/"cross-summary.json");assert summary["decisionCounts"]==dict(counts) and len(summary["hashOnlyHolds"])==10 and len(summary["selectedProposalCells"])==8
lineage=prov["priorHashOnlyLineage"];expected={"prior-window-selection-hash-only.jsonl":480,"prior-selection-hash-reattestation.jsonl":260,"prior-hold-hash-reattestation.jsonl":47}
for name,count in expected.items():
 path=cf/name;rows=jl(path);assert len(rows)==count==lineage["files"][name]["rowCount"] and sha(path.read_bytes())==lineage["files"][name]["sha256"]
 assert not any(1523<=r["position"]<=1542 for r in rows)
 assert all(not any(k in r for k in ("sourceKey","currentTarget","target","crossTarget","proposedTarget","source","targetText","lineText")) for r in rows)
assert lineage["selectedWindowPositionOverlap"]==0 and lineage["rawPriorTranslationsIncluded"] is False
print(json.dumps({"result":"PASS","head":HEAD,"tree":TREE,"cells":len(ledger),"decisionCounts":dict(counts),"upstreamPacketFiles":{"candidateFree":cc,"primary":pc,"blind":bc},"rootChecksummedFiles":len(rs),"proposalLinkage":"PASS","hashOnlyHolds":10,"priorHashOnlyLineage":"PASS"},ensure_ascii=False,indent=2))
