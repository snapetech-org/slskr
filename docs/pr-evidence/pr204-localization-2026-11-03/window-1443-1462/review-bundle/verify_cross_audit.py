#!/usr/bin/env python3
import argparse,hashlib,json,re,subprocess
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parent
HEAD="44b37bd94385128d5bb5287aa1545901282bdfcb";TREE="02c3f149a079c67b010d973dd02ca15776ad1610"
BRANCH="codex/slskr-l10n-audit-20261030";BASE_SHA="2a2b188f10b9460a15bc6d5c34e406b0193d51ba"
def fail(m): raise SystemExit("FAIL: "+m)
def need(ok,m):
 if not ok: fail(m)
def sha(b): return hashlib.sha256(b).hexdigest()
def shat(s): return sha(s.encode())
def canon(x): return json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(",",":"))
def rj(p): return json.loads(p.read_text(encoding="utf-8"))
def rjl(p): return [json.loads(x) for x in p.read_text(encoding="utf-8").splitlines() if x.strip()]
PH=re.compile(r"\{[A-Za-z][A-Za-z0-9_]*\}");TAG=re.compile(r"</?[A-Za-z][^>]*>")
NUM=re.compile(r"(?<![A-Za-z])\d+(?:[.,]\d+)?%?(?![A-Za-z])")
PROT=re.compile(r"(?<![A-Za-z0-9])(?:[A-Z]{2,}[A-Z0-9]*|ffmpeg|Chromaprint|Soulseek|Spotify|YouTube|Pushbullet|Matrix|WebSocket|OpenAI)(?![A-Za-z0-9])")
def tok(s): return {"placeholders":PH.findall(s),"markupTags":TAG.findall(s),"numericTokens":NUM.findall(s),"protectedLiterals":list(dict.fromkeys(m.group(0) for m in PROT.finditer(s)))}
def verify_sums(folder):
 sums=folder/"SHA256SUMS.txt";need(sums.is_file(),"missing checksum list"); entries={}
 for line in sums.read_text(encoding="utf-8").splitlines():
  if not line: continue
  need(len(line)>=66 and line[64:66]=="  ","bad checksum format")
  d=line[:64];n=line[66:].lstrip("*");need(n not in entries,"duplicate checksum "+n)
  p=folder/n;need(p.is_file() and sha(p.read_bytes())==d,"checksum mismatch "+n);entries[n]=d
 actual={p.relative_to(folder).as_posix() for p in folder.rglob("*") if p.is_file() and p.name!="SHA256SUMS.txt"}
 need(set(entries)==actual,"checksum inventory mismatch")
 return entries
def source_check(repo,pins,cells,contexts):
 repo=str(repo);h=subprocess.check_output(["git","-C",repo,"rev-parse","HEAD"],text=True).strip()
 t=subprocess.check_output(["git","-C",repo,"rev-parse","HEAD^{tree}"],text=True).strip()
 st=subprocess.check_output(["git","-C",repo,"status","--porcelain"],text=True)
 need(h==HEAD and t==TREE and not st,"source repository pin mismatch")
 expected={}
 for x in pins["localeCatalogs"].values():expected[x["path"]]=(x["sha256"],x["gitBlob"])
 x=pins["localeRuntime"];expected[x["path"]]=(x["sha256"],x["gitBlob"])
 for path,x in pins["callerFiles"].items():expected[path]=(x["sha256"],x["gitBlob"])
 need(len(expected)==29,"source pin count mismatch")
 for path,(d,b) in expected.items():
  data=subprocess.check_output(["git","-C",repo,"show",f"HEAD:{path}"])
  blob=subprocess.check_output(["git","-C",repo,"rev-parse",f"HEAD:{path}"],text=True).strip()
  need(sha(data)==d and blob==b,"source file pin mismatch "+path)
 cache={}
 for c in cells:
  if c["catalogPath"] not in cache:cache[c["catalogPath"]]=json.loads(subprocess.check_output(["git","-C",repo,"show",f"HEAD:{c['catalogPath']}"]))
  need(cache[c["catalogPath"]].get(c["sourceKey"])==c["currentTarget"],"catalog value mismatch "+str(c["position"]))
 n=0
 for cx in contexts:
  for c in cx["callers"]:
   data=subprocess.check_output(["git","-C",repo,"show",f"HEAD:{c['path']}"])
   line=data.decode().splitlines()[c["line"]-1]
   need(line==c["lineText"] and shat(line)==c["lineSha256"],"caller source mismatch "+str(cx["position"]))
   n+=1
 return {"sourceFiles":len(expected),"catalogPreimages":len(cells),"callerLines":n}
def main():
 ap=argparse.ArgumentParser();ap.add_argument("--source-repo");a=ap.parse_args()
 sums=verify_sums(ROOT);m=rj(ROOT/"manifest.json");s=rj(ROOT/"summary.json")
 need(m["head"]==HEAD and m["tree"]==TREE and m["branch"]==BRANCH and m["baseSha"]==BASE_SHA and m["cellCount"]==240,"manifest pin mismatch")
 need(m["fileHashes"]=={k:v for k,v in sums.items() if k!="manifest.json"},"manifest hashes mismatch")
 pr=ROOT/"inputs/primary";bl=ROOT/"inputs/blind"
 subprocess.check_call(["python3",str(pr/"verify_packet.py")],stdout=subprocess.DEVNULL)
 subprocess.check_call(["python3",str(bl/"blind-review/verify_blind_review.py")],stdout=subprocess.DEVNULL)
 cf=pr/"candidate-free-input";bcf=bl/"input/candidate-free-input"
 pf={x.relative_to(cf).as_posix():x.read_bytes() for x in cf.rglob("*") if x.is_file()}
 bf={x.relative_to(bcf).as_posix():x.read_bytes() for x in bcf.rglob("*") if x.is_file()}
 need(pf==bf,"candidate-free packet copies differ")
 im=rj(cf/"manifest.json");need(im["head"]==HEAD and im["tree"]==TREE and im["cellCount"]==240,"input pin mismatch")
 need(m["inputPrimaryRootSha256"]==sha((pr/"packet-manifest.json").read_bytes()),"primary packet pin mismatch")
 need(m["inputBlindRootManifestSha256"]==sha((bl/"manifest.json").read_bytes()),"blind packet pin mismatch")
 need(m["primaryRootChecksumSha256"]==sha((pr/"SHA256SUMS.txt").read_bytes()),"primary checksum pin mismatch")
 need(m["blindRootChecksumSha256"]==sha((bl/"SHA256SUMS.txt").read_bytes()),"blind checksum pin mismatch")
 need(m["candidateFreeManifestSha256"]==sha((cf/"manifest.json").read_bytes()),"candidate-free manifest pin mismatch")
 live=rj(ROOT/"live-pr-reattestation.json")
 for stage in ("observedBeforeWrite","observedDuringSeal"):
  z=live[stage];p=z["pr"]
  need(p["state"]=="OPEN" and p["isDraft"] is True and p["headRefName"]==BRANCH and p["headRefOid"]==HEAD,"live PR head/state mismatch")
  need(p["baseRefName"]=="main" and p["baseRefOid"]==BASE_SHA,"live base mismatch")
  need(z["remoteRefs"]=={f"refs/heads/{BRANCH}":HEAD,"refs/pull/204/head":HEAD} and z["remoteCommitTree"]==TREE,"live refs/tree mismatch")
  need(z["sourceCheckout"]["head"]==HEAD and z["sourceCheckout"]["tree"]==TREE and z["sourceCheckout"]["clean"],"source checkout mismatch")
 need(live["observedBeforeWrite"]["pr"]==live["observedDuringSeal"]["pr"],"PR changed during seal")
 pins=rj(cf/"catalog-file-pins.json");src=rj(ROOT/"source-pin-reattestation.json")
 need(src["result"]=="PASS" and src["head"]==HEAD and src["tree"]==TREE and src["sourceCheckoutClean"],"source reattestation record mismatch")
 need(src["pinnedFileCount"]==29 and src["currentCatalogPreimagesReattested"]==240 and src["callerLineReferencesReattested"]==27,"source reattestation counts mismatch")
 need(m["sourcePinAttestationSha256"]==sha((ROOT/"source-pin-reattestation.json").read_bytes()),"source attestation hash mismatch")
 cells=rjl(cf/"current-target-cells.jsonl");ctxs=rjl(cf/"source-contexts.jsonl")
 prows=rjl(pr/"primary-review/cell-review.jsonl");brows=rjl(bl/"blind-review/blind-ledger.jsonl");rows=rjl(ROOT/"cross-ledger.jsonl")
 need(len(cells)==len(prows)==len(brows)==len(rows)==240,"cell count mismatch")
 cm={(x["sourceKey"],x["locale"]):x for x in cells};pm={(x["sourceKey"],x["locale"]):x for x in prows};bm={(x["sourceKey"],x["locale"]):x for x in brows};xm={(x["sourceKey"],x["locale"]):x for x in rows}
 need(len(cm)==len(pm)==len(bm)==len(xm)==240,"duplicate cell")
 cx={x["position"]:x for x in ctxs}; tdiff=ddiff=anydiff=baseline=repairs=callers=0;changes=[];dc=Counter();caller_refs_seen=set()
 for k,b in cm.items():
  p=pm[k];q=bm[k];x=xm[k];pos=b["position"]
  pe=p["proposedTarget"] if p.get("proposedTarget") is not None else p["currentTarget"];be=q["selectedTarget"]
  for field in ("sourceKey","sourceKeySha256","currentTarget","currentTargetSha256","sourceContextSha256","callerCount","callerRefs"):
   need(p.get(field)==b.get(field),"primary preimage/caller mismatch "+str(k)+":"+field)
  need(q["sourceKey"]==b["sourceKey"] and q["sourceKeySha256"]==b["sourceKeySha256"] and q["currentTarget"]==b["currentTarget"] and q["currentTargetSha256"]==b["currentTargetSha256"],"blind preimage mismatch "+str(k))
  need(q["callerContextSha256"]==b["sourceContextSha256"] and q["callerRefs"]==b["callerRefs"],"blind caller mismatch "+str(k))
  need(x["sourceKey"]==b["sourceKey"] and x["sourceKeySha256"]==shat(b["sourceKey"]) and x["currentTarget"]==b["currentTarget"] and x["currentTargetSha256"]==shat(b["currentTarget"]),"cross preimage mismatch "+str(k))
  need(x["sourceContextSha256"]==b["sourceContextSha256"] and x["callerRefs"]==b["callerRefs"],"cross caller mismatch "+str(k))
  c=cx[pos];need(c["sourceKey"]==b["sourceKey"] and c["callerContextSha256"]==b["sourceContextSha256"],"caller context pin mismatch "+str(k))
  need(c["callerContextSha256"]==shat(canon({"sourceKey":c["sourceKey"],"callers":c["callers"]})),"caller context hash mismatch "+str(k))
  refs=[{"fileSha256":v["fileSha256"],"gitBlob":v["gitBlob"],"line":v["line"],"lineSha256":v["lineSha256"],"path":v["path"]} for v in c["callers"]]
  need(refs==b["callerRefs"] and b["callerCount"]==len(refs),"caller refs mismatch "+str(k));caller_refs_seen.update(json.dumps(v,sort_keys=True) for v in refs)
  need(x["primary"]["disposition"]==p["disposition"] and x["primary"]["proposedTarget"]==p.get("proposedTarget") and x["primary"]["proposedTargetSha256"]==p.get("proposedTargetSha256") and x["primary"]["candidateTarget"]==pe and x["primary"]["candidateTargetSha256"]==shat(pe) and x["primary"]["reviewReason"]==p["reviewReason"],"primary review mismatch "+str(k))
  need(x["blind"]["disposition"]==q["disposition"] and x["blind"]["selectedTarget"]==be and x["blind"]["selectedTargetSha256"]==q["selectedTargetSha256"]==shat(be) and x["blind"]["rationale"]==q["rationale"],"blind review mismatch "+str(k))
  td=pe!=be;dd=p["disposition"]!=q["disposition"];tdiff+=td;ddiff+=dd;anydiff+=td or dd
  need(x["reviewerComparison"]["targetAgreement"]==(not td) and x["reviewerComparison"]["dispositionAgreement"]==(not dd),"comparison mismatch "+str(k))
  sel=x["selectedTarget"];need(x["selectedTargetSha256"]==shat(sel),"selected hash mismatch "+str(k))
  who=x["selectedFrom"];need(who in ("primary","blind","consensus"),"invalid selection provenance "+str(k))
  if who=="primary":need(sel==pe,"primary selection mismatch "+str(k))
  elif who=="blind":need(sel==be,"blind selection mismatch "+str(k))
  else:need(sel==pe==be,"unresolved reviewer disagreement "+str(k))
  need(x["crossDisposition"] in ("accept-current","correction","refinement") and x["reconciliationReason"].strip(),"missing disposition/rationale "+str(k))
  st=tok(b["sourceKey"]);ct=tok(b["currentTarget"]);tt=tok(sel)
  need(x["tokenChecks"]=={"source":st,"current":ct,"selected":tt,"selectedChecksPass":True},"token record mismatch "+str(k))
  need(st==tt,"selected token mismatch "+str(k))
  if sel==b["currentTarget"]:need(x["crossDisposition"]=="accept-current","no-op disposition mismatch "+str(k))
  else:need(x["crossDisposition"] in ("correction","refinement"),"changed target disposition mismatch "+str(k));changes.append(x)
  if b["protectedLiteralMismatchTokens"]:
   baseline+=1;need(sel!=b["currentTarget"],"protected literal not repaired "+str(k));repairs+=1
  dc[x["crossDisposition"]]+=1
 callers=len(caller_refs_seen);need(tdiff==43 and baseline==9 and repairs==9 and callers==27,"reconciliation counts mismatch")
 holds=(ROOT/"prior-hold-reattestation.jsonl");sels=(ROOT/"prior-selection-reattestation.jsonl")
 need(holds.read_bytes()==(cf/"prior-hold-reattestation.jsonl").read_bytes() and len(rjl(holds))==35,"carried holds changed")
 need(sels.read_bytes()==(cf/"prior-selection-reattestation.jsonl").read_bytes() and len(rjl(sels))==200,"prior selections changed")
 selected=rjl(ROOT/"selected-changes.jsonl")
 wanted=[{"position":x["position"],"locale":x["locale"],"sourceKey":x["sourceKey"],"preimageSha256":x["currentTargetSha256"],"selectedTarget":x["selectedTarget"],"selectedTargetSha256":x["selectedTargetSha256"],"disposition":x["crossDisposition"]} for x in changes]
 need(selected==wanted,"selected-change list mismatch")
 need(s["crossDispositionCounts"]==dict(dc) and s["selectedChanges"]==len(changes),"summary selection counts mismatch")
 need(s["reviewerTargetDisagreements"]==tdiff and s["reviewerDispositionDisagreements"]==ddiff and s["cellsWithAnyReviewerDisagreement"]==anydiff,"summary disagreement counts mismatch")
 need(s["carriedHoldsReattestedUnchanged"]==35 and s["priorSelectionsReattested"]==200,"summary carried evidence mismatch")
 need(m["crossLedgerSha256"]==sha((ROOT/"cross-ledger.jsonl").read_bytes()) and m["selectedChangesSha256"]==sha((ROOT/"selected-changes.jsonl").read_bytes()),"ledger hashes mismatch")
 source=None
 if a.source_repo:source=source_check(a.source_repo,pins,cells,ctxs)
 print(json.dumps({"result":"PASS","head":HEAD,"tree":TREE,"cells":240,"selectedChanges":len(changes),"crossDispositions":dict(dc),
  "targetDisagreementsResolved":tdiff,"dispositionDisagreementsResolved":ddiff,"cellsWithAnyReviewerDisagreement":anydiff,
  "protectedLiteralRepairs":repairs,"carriedHolds":35,"priorSelections":200,"callerReferences":callers,
  "rootFilesChecked":len(sums),"sourceRepoReattestation":source},ensure_ascii=False,indent=2))
if __name__=="__main__":
 import argparse
 ap=argparse.ArgumentParser();ap.add_argument("--source-repo");a=ap.parse_args();main()
