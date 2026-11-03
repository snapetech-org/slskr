#!/usr/bin/env python3
from pathlib import Path
from collections import Counter
import hashlib,json,re

O=Path(__file__).resolve().parent
HEAD="b5da2589b6e8f2d4b0c0faab28bcdf0481e42438"
TREE="36ae6ecf3b705995fbd549cb8650d6458936df91"
LOCALES=["es","zh-Hans","hi","de","ja","fr","pt-BR","ar","ko","zh-Hant","vi","id"]
PH=re.compile(r"\{[^{}]*\}")
TAG=re.compile(r"</?[A-Za-z][^>]*>")
NUM=re.compile(r"(?<![A-Za-z])\d[\d,]*(?:\.\d+)?(?![A-Za-z])")

def sha(x): return hashlib.sha256(x if isinstance(x,bytes) else x.encode("utf-8")).hexdigest()
def j(p): return json.loads(p.read_text(encoding="utf-8"))
def jl(p): return [json.loads(x) for x in p.read_text(encoding="utf-8").splitlines() if x.strip()]
def ck(v,m):
    if not v: raise SystemExit("FAIL: "+m)
def checksum(folder,name):
    sums={}
    for line in (folder/name).read_text(encoding="utf-8").splitlines():
        d,n=line.split("  ",1); sums[n]=d
    actual={p.name for p in folder.iterdir() if p.is_file() and p.name!=name}
    ck(set(sums)==actual,"checksum inventory "+str(folder))
    for n,d in sums.items(): ck(sha((folder/n).read_bytes())==d,"checksum "+str(folder/n))
for d,n in ((O/"candidate-free-input","SHA256SUMS.txt"),(O/"primary-review","SHA256SUMS.txt"),(O/"blind-review","SHA256SUMS.txt")):
    checksum(d,n)
# Verify the outer exact file inventory and manifest pins.
allfiles={p.relative_to(O).as_posix():p for p in O.rglob("*") if p.is_file()}
ck("SHA256SUMS.txt" in allfiles and "manifest.json" in allfiles,"outer manifest files")
sums={}
for line in (O/"SHA256SUMS.txt").read_text(encoding="utf-8").splitlines():
    d,n=line.split("  ",1); sums[n]=d
ck(set(sums)==set(allfiles)-{"SHA256SUMS.txt"},"outer checksum inventory")
for n,d in sums.items(): ck(sha(allfiles[n].read_bytes())==d,"outer checksum "+n)
m=j(O/"manifest.json")
ck(m["head"]==HEAD and m["tree"]==TREE,"outer manifest head/tree")
expected_files=set(allfiles)-{"manifest.json","SHA256SUMS.txt"}
ck(set(m["fileHashes"])==expected_files,"manifest file inventory")
for n,x in m["fileHashes"].items():
    ck(x["sha256"]==sha(allfiles[n].read_bytes()) and x["bytes"]==allfiles[n].stat().st_size,"manifest file pin "+n)

att=j(O/"live-ref-attestation.json")
ck(att["state"]=="OPEN" and att["isDraft"] is True,"PR open draft")
ck(att["headRefOid"]==att["branchRefOid"]==att["pullRefOid"]==HEAD and att["tree"]==TREE,"live exact-head attestation")
ck(att["postReviewHead"]==att["postReviewBranchRefOid"]==att["postReviewPullRefOid"]==HEAD and att["postReviewTree"]==TREE,"post-review exact-head attestation")
ck(att["localGitObjectDatabase"]["pinnedCommit"]==HEAD and att["localGitObjectDatabase"]["pinnedCommitTree"]==TREE,"local object tree attestation")
ck(att["workingCopy"]["usedForAudit"] is False,"working copy provenance")

I=O/"candidate-free-input"; P=O/"primary-review"; B=O/"blind-review"
for f in (I,P,B):
    z=j(f/"manifest.json")
    ck(z["head"]==HEAD and z["tree"]==TREE,"input head/tree "+f.name)
cells=jl(I/"current-target-cells.jsonl"); primary=jl(P/"review-ledger.jsonl"); blind=jl(B/"primary-ledger.jsonl")
ctx=jl(I/"source-contexts.jsonl"); ledger=jl(O/"cross-audit-ledger.jsonl")
apply=jl(O/"apply-plan.jsonl"); noop=jl(O/"no-op-plan.jsonl"); holds=jl(O/"hold-plan.jsonl")
prior=jl(I/"prior-hold-reattestation.jsonl"); preserved=jl(O/"prior-hold-reattestation.jsonl")
ck(len(cells)==len(primary)==len(blind)==len(ledger)==240,"240-cell coverage")
ck(len(ctx)==20 and len(prior)==len(preserved)==35,"source and carry-forward hold counts")
ck(all(a==b for a,b in zip(prior,preserved)),"carry-forward holds preserved byte-semantically")
expected=[(p,l) for p in range(1383,1403) for l in LOCALES]
keys=lambda rows:[(x["position"],x["locale"]) for x in rows]
ck(keys(cells)==keys(primary)==keys(blind)==keys(ledger)==expected,"exact cell order")
cm={(x["position"],x["locale"]):x for x in cells}
pm={(x["position"],x["locale"]):x for x in primary}
bm={(x["position"],x["locale"]):x for x in blind}
context={x["position"]:x for x in ctx}
updates=[]; noops=[]; dispositions=Counter(); resolutions=Counter(); disagreements=0; agreements=0
for r in ledger:
    k=(r["position"],r["locale"]); c=cm[k]; p=pm[k]; b=bm[k]
    ck(r["callerCount"]>0 and context[k[0]]["productionCallerCount"]>0,"caller-bound cell "+str(k))
    ck(r["sourceKey"]==c["sourceKey"]==p["sourceKey"]==b["sourceKey"],"source key "+str(k))
    ck(r["sourceKeySha256"]==c["sourceKeySha256"]==p["sourceKeySha256"]==b["sourceKeySha256"],"source hash "+str(k))
    ck(r["sourceContextSha256"]==c["sourceContextSha256"]==p["callerEvidence"]["callerContextSha256"]==b["callerContextSha256"],"caller context "+str(k))
    ck(r["currentTarget"]==c["currentTarget"]==p["currentTarget"]==b["currentTarget"],"current value "+str(k))
    ck(r["currentTargetSha256"]==c["currentTargetSha256"]==p["currentTargetSha256"]==b["currentTargetSha256"],"current value hash "+str(k))
    ck(r["catalogPath"]==c["catalogPath"]==p["catalog"]["path"]==b["catalogPath"],"catalog path "+str(k))
    ck(r["catalogFileSha256"]==c["catalogFileSha256"]==p["catalog"]["fileSha256"]==b["catalogFileSha256"],"catalog hash "+str(k))
    ptarget=c["currentTarget"] if p["disposition"]=="accept-current" else p["proposedTarget"]
    btarget=c["currentTarget"] if b["decision"]=="accept-current" else b["proposedTarget"]
    ck(r["primaryTarget"]==ptarget and r["blindTarget"]==btarget,"reviewer target provenance "+str(k))
    ck(r["primaryTargetSha256"]==sha(ptarget) and r["blindTargetSha256"]==sha(btarget),"reviewer target hashes "+str(k))
    ck(r["selectedTarget"] is not None and r["selectedTargetSha256"]==sha(r["selectedTarget"]),"selected target hash "+str(k))
    ck(r["selectedDisposition"] in ("accept-current","correction","refinement"),"selected disposition "+str(k))
    ck(r["applicationAction"]==("no-op" if r["selectedTarget"]==c["currentTarget"] else "update"),"application action "+str(k))
    ck(r["resolutionRationale"] and r["crossAuditConfidence"]=="moderate" and r["nativeSpeakerApproved"] is False,"review claims/rationale "+str(k))
    checks=r["tokenChecks"]
    ck(checks["placeholdersPreserved"] and sorted(PH.findall(c["sourceKey"]))==sorted(PH.findall(r["selectedTarget"])),"placeholder tokens "+str(k))
    ck(checks["markupPreserved"] and sorted(TAG.findall(c["sourceKey"]))==sorted(TAG.findall(r["selectedTarget"])),"markup tokens "+str(k))
    ck(checks["numericTokensPreserved"] and NUM.findall(c["sourceKey"])==NUM.findall(r["selectedTarget"]),"numeric tokens "+str(k))
    ck(checks["protectedLiteralsPreserved"] and not checks["missingProtectedLiterals"],"protected literals "+str(k))
    ck(checks["directCatalogLookupAndNamedPlaceholderSubstitution"] and not checks["icuMessageSyntaxPresent"],"runtime/ICU note "+str(k))
    same=ptarget==btarget
    ck(r["reviewerTargetsAgree"]==same,"review agreement flag "+str(k))
    if same: agreements+=1
    else: disagreements+=1
    if r["applicationAction"]=="update": updates.append(r)
    else: noops.append(r)
    resolutions[r["resolution"]]+=1; dispositions[r["selectedDisposition"]]+=1
ck(agreements==192 and disagreements==48,"review target agreement totals")
ck(len(updates)==57 and len(noops)==183 and len(holds)==0,"update/no-op/new-hold counts")
ck([x["position"] for x in updates]==[x["position"] for x in apply],"apply position list")
ck([(x["position"],x["locale"]) for x in updates]==[(x["position"],x["locale"]) for x in apply],"apply plan keys")
ck([(x["position"],x["locale"]) for x in noops]==[(x["position"],x["locale"]) for x in noop],"no-op plan keys")
fields=("position","locale","sourceKey","sourceKeySha256","sourceContextSha256","catalogPath","catalogFileSha256","catalogGitBlob","catalogKeyCount","currentTarget","currentTargetSha256","selectedTarget","selectedTargetSha256","selectedDisposition","applicationAction")
for rows,plan in ((updates,apply),(noops,noop)):
    for r,p in zip(rows,plan):
        ck(all(r[k]==p[k] for k in fields),"application plan exact fields "+str((r["position"],r["locale"])))
s=j(O/"summary.json")
ck(s["head"]==HEAD and s["tree"]==TREE and s["cellCount"]==240,"summary pins")
ck(s["reviewerTargetAgreements"]==agreements and s["reviewerTargetDisagreements"]==disagreements,"summary review counts")
ck(s["applicationUpdates"]==len(apply) and s["noOpCells"]==len(noop) and s["newHolds"]==0,"summary plan counts")
ck(s["priorHoldsReattestedUnchanged"]==35 and s["priorSelectionsReattested"]==140,"summary carry-forward counts")
ck(s["nativeSpeakerApproved"] is False and s["browserReviewPerformed"] is False,"summary acceptance status")
ck(s["repositoryChanged"] is False and s["workflowFilesChanged"] is False and s["testsBuildsOrCiRun"] is False and s["releaseOrTag"] is False,"summary scope")
ck(s["applyPlanSha256"]==sha((O/"apply-plan.jsonl").read_bytes()),"apply-plan SHA")
ck(s["noOpPlanSha256"]==sha((O/"no-op-plan.jsonl").read_bytes()),"no-op-plan SHA")
ck(s["crossAuditLedgerSha256"]==sha((O/"cross-audit-ledger.jsonl").read_bytes()),"cross-audit ledger SHA")
tc=j(O/"terminology-context.json")
ck(tc["head"]==HEAD and tc["tree"]==TREE and set(tc["locales"])==set(LOCALES),"terminology context pins/locales")
for loc in LOCALES:
    pin=tc["locales"][loc]["catalogPin"]
    manifest_pin=j(I/"catalog-file-pins.json")["localeCatalogs"][loc]
    ck(pin==manifest_pin,"terminology catalog pin "+loc)
print(json.dumps({"pass":True,"head":HEAD,"tree":TREE,"cells":240,"reviewerAgreements":agreements,"reviewerDisagreementsResolved":disagreements,"updates":len(apply),"noOps":len(noop),"newHolds":0,"priorHoldsPreserved":35,"selectedDispositionCounts":dict(dispositions),"nativeSpeakerApproved":False},ensure_ascii=False,indent=2))
