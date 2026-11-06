#!/usr/bin/env python3
from pathlib import Path
from collections import Counter
import hashlib,json,re,subprocess,sys
O=Path(__file__).resolve().parent
I=O/"candidate-free-input"; BI=O/"blind-input"; P=O/"primary-review"; B=O/"blind-review"
HEAD="281c39ec0cdb3677d7d523b7c4f0cd0d52bbf14c"; TREE="777b234b1aa3cb7a2c9fd560b2c0fecc4e7fe49d"
LOCALES=["es","zh-Hans","hi","de","ja","fr","pt-BR","ar","ko","zh-Hant","vi","id"]
PROTECTED={1366:["ContentID"],1367:["Library Health"],1370:["slskr"],1372:["ID"],1375:["/music",r"C:\Music"]}
PH=re.compile(r"\{[^{}]*\}"); TAG=re.compile(r"</?[A-Za-z][^>]*>")
NUM=re.compile(r"(?<![A-Za-z])\d[\d,]*(?:\.\d+)?(?![A-Za-z])")
def sha(x): return hashlib.sha256(x if isinstance(x,bytes) else x.encode("utf-8")).hexdigest()
def j(p): return json.loads(p.read_text(encoding="utf-8"))
def jl(p): return [json.loads(x) for x in p.read_text(encoding="utf-8").splitlines() if x.strip()]
def ck(x,msg):
 if not x: raise SystemExit("FAIL: "+msg)
def run(cmd): return subprocess.run(cmd,check=True,capture_output=True,text=True).stdout
# Verify the outer checksum inventory and exact manifest file hashes.
files={p.relative_to(O).as_posix():p for p in O.rglob("*") if p.is_file() and p.relative_to(O).as_posix()!="SHA256SUMS.txt"}
sums={}
for line in (O/"SHA256SUMS.txt").read_text(encoding="utf-8").splitlines():
 d,n=line.split("  ",1); sums[n]=d
ck(set(sums)=={p.relative_to(O).as_posix() for p in O.rglob("*") if p.is_file() and p.relative_to(O).as_posix()!="SHA256SUMS.txt"},"outer checksum inventory")
for n,d in sums.items(): ck(sha((O/n).read_bytes())==d,"outer checksum "+n)
m=j(O/"manifest.json")
ck(m["head"]==HEAD and m["tree"]==TREE,"manifest head/tree")
for n,x in m["fileHashes"].items():
 ck(n in files and sha(files[n].read_bytes())==x["sha256"] and files[n].stat().st_size==x["bytes"],"manifest file pin "+n)
ck(set(m["fileHashes"])==set(files)-{"manifest.json"},"manifest file inventory")
att=j(O/"live-pr-attestation.json")
ck(att["headRefOid"]==att["liveBranchRefOid"]==att["livePullRefOid"]==HEAD and att["headTree"]==TREE and att["state"]=="OPEN","live PR attestation")
ck(att["verifiedWorktree"]["head"]==HEAD and att["verifiedWorktree"]["tree"]==TREE and att["verifiedWorktree"]["status"]=="clean","local repo status")
# Run the candidate-free, primary, and blind packet verifiers on the copied evidence.
subprocess.run([sys.executable,str(I/"verify-candidate-free.py")],check=True,capture_output=True,text=True)
subprocess.run([sys.executable,str(P/"verify-primary-ledger.py")],check=True,capture_output=True,text=True)
subprocess.run([sys.executable,str(B/"verify_blind_review.py"),"--input",str(BI)],check=True,capture_output=True,text=True)
# Verify copied evidence checksums and packet pins.
for folder,sumfile in ((I,"SHA256SUMS.txt"),(BI,"SHA256SUMS.txt"),(P,"SHA256SUMS"),(B,"SHA256SUMS.txt")):
 rows={}
 for line in (folder/sumfile).read_text(encoding="utf-8").splitlines():
  d,n=line.split("  ",1); rows[n]=d
 ck(set(rows)=={p.name for p in folder.iterdir() if p.is_file() and p.name!=sumfile},"inner checksum inventory "+folder.name)
 for n,d in rows.items(): ck(sha((folder/n).read_bytes())==d,"inner checksum "+folder.name+"/"+n)
for folder in (I,BI,P,B):
 q=j(folder/"manifest.json"); ck(q["head"]==HEAD and q["tree"]==TREE,"evidence pin "+folder.name)
cells=jl(I/"current-target-cells.jsonl"); ctxs=jl(I/"source-contexts.jsonl")
im2=j(I/"manifest.json")
input_bad={(x["position"],x["locale"]) for x in cells if not x["protectedLiteralsMatch"]}
ck_input_bad={(1372,"hi"),(1372,"ar")}
primary=jl(P/"review-ledger.jsonl"); prompts=jl(BI/"prompts.jsonl"); blind=jl(B/"sealed-translation-ledger.jsonl")
ledger=jl(O/"resolution-ledger.jsonl"); holds=jl(I/"prior-hold-reattestation.jsonl")
ck(len(cells)==len(primary)==len(prompts)==len(blind)==len(ledger)==240,"cell count")
ck(len(ctxs)==20 and len(holds)==23 and all(x["reattestation"]=="same" and x["currentTarget"]==x["priorCurrentTarget"] and x["currentTargetSha256"]==x["priorCurrentTargetSha256"] for x in holds),"prior holds")
ck([(x["position"],x["locale"]) for x in ledger]==[(x["position"],x["locale"]) for x in cells],"ledger order")
cm={(x["position"],x["locale"]):x for x in cells}; pm={(x["position"],x["locale"]):x for x in primary}
bm={(x["position"],x["locale"]):x for x in blind}; prm={(x["position"],x["locale"]):x for x in prompts}
ctx={x["position"]:x for x in ctxs}; seen=set(); resol=Counter(); disp=Counter(); agree=0; diff=0
for r in ledger:
 k=(r["position"],r["locale"]); ck(k in cm and k not in seen,"unique key "+str(k)); seen.add(k)
 c=cm[k]; p=pm[k]; b=bm[k]; prompt=prm[k]; d=b["decision"]
 ck(r["sourceKey"]==c["sourceKey"]==p["sourceKey"]==prompt["sourceKey"] and r["sourceKeySha256"]==c["sourceKeySha256"]==p["sourceKeySha256"]==prompt["sourceKeySha256"],"source lineage "+str(k))
 ck(r["currentTarget"]==c["currentTarget"] and r["currentTargetSha256"]==c["currentTargetSha256"] and p["currentTarget"]==c["currentTarget"],"current target pin "+str(k))
 ck(r["sourceContextSha256"]==c["sourceContextSha256"]==p["callerEvidence"]["callerContextSha256"]==prompt["sourceContextRef"]["sourceContextSha256"],"caller context pin "+str(k))
 pt=None if p["disposition"]=="hold" else p.get("proposedTarget",p["currentTarget"])
 bt=d.get("translation")
 ck(r["primaryTarget"]==pt and r["primaryTargetSha256"]==(sha(pt) if pt is not None else None),"primary target "+str(k))
 ck(r["blindTarget"]==bt and r["blindTargetSha256"]==(sha(bt) if bt is not None else None),"blind target "+str(k))
 ck(r["selectedTargetSha256"]==(sha(r["selectedTarget"]) if r["selectedTarget"] is not None else None),"selected hash "+str(k))
 ck(r["resolutionRationale"] and r["nativeSpeakerApproved"] is False,"rationale/claims "+str(k))
 if k[0]==1376:
  ck(r["resolution"]=="hold-consensus" and r["selectedDisposition"]=="hold" and r["selectedTarget"] is None and pt is None and bt is None and ctx[k[0]]["productionCallerCount"]==0,"callerless hold "+str(k))
 else:
  ck(r["resolution"] in ("agreement","primary-selected","blind-selected"),"resolution "+str(k))
  ck(r["selectedTarget"] is not None and r["selectedDisposition"] in ("accept-current","correction","refinement"),"selected proposal "+str(k))
  if r["resolution"]=="agreement": ck(pt==bt==r["selectedTarget"],"agreement "+str(k)); agree+=1
  elif r["resolution"]=="primary-selected": ck(r["selectedTarget"]==pt and pt!=bt,"primary selection "+str(k)); diff+=1
  else: ck(r["selectedTarget"]==bt and pt!=bt,"blind selection "+str(k)); diff+=1
  if r["selectedDisposition"]=="accept-current": ck(r["selectedTarget"]==c["currentTarget"],"accept-current "+str(k))
  else: ck(r["selectedTarget"]!=c["currentTarget"],"changed target disposition "+str(k))
 required=PROTECTED.get(k[0],[])
 ck(r["tokenAndRuntimeChecks"]["requiredProtectedLiterals"]==required,"required token list "+str(k))
 selected=r["selectedTarget"]; checks=r["tokenAndRuntimeChecks"]
 if selected is None:
  ck(checks["callerlessHoldChecksNotApplicable"] is True,"held token status "+str(k))
 else:
  ck(sorted(PH.findall(c["sourceKey"]))==sorted(PH.findall(selected)) and checks["placeholdersPreserved"],"placeholder "+str(k))
  ck(sorted(TAG.findall(c["sourceKey"]))==sorted(TAG.findall(selected)) and checks["markupPreserved"],"markup "+str(k))
  ck(NUM.findall(c["sourceKey"])==NUM.findall(selected) and checks["numericTokensPreserved"],"numeric "+str(k))
  ck(all(selected.count(t)>=c["sourceKey"].count(t) for t in required) and checks["protectedLiteralsPreserved"],"protected literal "+str(k))
  if k[0]==1375: ck(all(selected.count(t)==1 for t in required) and checks["pathExamplesPreservedExactlyOnce"],"path examples "+str(k))
  ck(checks["runtimeUsesDirectLookupAndNamedSubstitution"] and not checks["icuMessageSyntaxPresent"],"runtime "+str(k))
  disp[r["selectedDisposition"]]+=1
  ck(r["crossAuditConfidence"]=="moderate","proposal confidence "+str(k))
  ck(r["targetsAgree"]==(pt==bt),"target agreement flag "+str(k))
 if k[0]==1376: disp["hold"]+=1
 resol[r["resolution"]]+=1
ck(seen==set(cm),"ledger completeness")
ck(agree==35 and diff==193,"proposal agreement/disagreement totals")
ck(sum(1 for r in ledger if r["position"]==1376 and r["selectedDisposition"]=="hold")==12,"12 callerless holds")
ck(sum(1 for r in ledger if r["resolution"]=="blind-selected")==132,"blind adjudication count")
ck(sum(1 for r in ledger if r["resolution"]=="primary-selected")==61,"primary adjudication count")
s=j(O/"summary.json")
ck(s["cellCount"]==240 and s["primaryBlindTargetAgreementsAmongProposals"]==35 and s["primaryBlindTargetDisagreements"]==193,"summary target counts")
ck(s["callerlessCellsHeld"]==12 and s["priorCarryForwardHoldsReattestedUnchanged"]==23 and s["selectedProtectedLiteralMismatches"]==0,"summary holds/tokens")
ck(resol==Counter({"agreement":35,"hold-consensus":12,"primary-selected":61,"blind-selected":132}),"resolution counts")
ck(disp==Counter(s["selectedDispositionCounts"]),"selected disposition counts")
ck(s["blindSelectedDisagreements"]==132 and s["primarySelectedDisagreements"]==61,"selected source counts")
print(json.dumps({"pass":True,"head":HEAD,"tree":TREE,"cells":240,"targetAgreements":35,"targetDisagreementsResolved":193,"resolutionCounts":{"agreement":35,"hold-consensus":12,"primary-selected":61,"blind-selected":132},"selectedDispositions":s["selectedDispositionCounts"],"priorHoldsPreserved":23,"callerlessRank1376Holds":12,"selectedTokenMismatches":0,"outerChecksumVerifier":"PASS","candidateFreeVerifier":"PASS","primaryVerifier":"PASS","blindVerifier":"PASS"},ensure_ascii=False,indent=2))
