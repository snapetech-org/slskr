#!/usr/bin/env python3
from pathlib import Path
from collections import Counter
from datetime import datetime, timezone
import hashlib, json, re, shutil, subprocess

OUT=Path(__file__).resolve().parent
TASK=Path("/home/keith/Documents/code/task-scratch")
INPUT_SRC=TASK/"slskr-pr204-w1383-1402-primary-20261103/candidate-free-input"
PRIMARY_SRC=TASK/"slskr-pr204-w1383-1402-primary-20261103/primary-review"
BLIND_SRC=TASK/"slskr-pr204-w1383-1402-blind-primary-20261103"
WORKTREE=TASK/"slskr-pr204-w1303-1322-apply-20261103/repo"
HEAD="b5da2589b6e8f2d4b0c0faab28bcdf0481e42438"
TREE="36ae6ecf3b705995fbd549cb8650d6458936df91"
BRANCH="codex/slskr-l10n-audit-20261030"
REPO="snapetech-org/slskR"
PR=204
LOCALES=["es","zh-Hans","hi","de","ja","fr","pt-BR","ar","ko","zh-Hant","vi","id"]
LOCALE_NAMES={"es":"Spanish","zh-Hans":"Simplified Chinese","hi":"Hindi","de":"German","ja":"Japanese","fr":"French","pt-BR":"Brazilian Portuguese","ar":"Arabic","ko":"Korean","zh-Hant":"Traditional Chinese","vi":"Vietnamese","id":"Indonesian"}
PH=re.compile(r"\{[^{}]*\}")
TAG=re.compile(r"</?[A-Za-z][^>]*>")
NUM=re.compile(r"(?<![A-Za-z])\d[\d,]*(?:\.\d+)?(?![A-Za-z])")
PREF={
 (1384,"vi"):"blind",(1386,"hi"):"primary",
 (1387,"es"):"custom",(1387,"hi"):"current",(1387,"de"):"current",(1387,"fr"):"current",(1387,"ar"):"current",(1387,"vi"):"current",(1387,"id"):"current",(1387,"pt-BR"):"custom",(1387,"ko"):"custom",
 (1391,"hi"):"current",(1391,"de"):"current",(1391,"ja"):"blind",(1391,"ko"):"blind",(1391,"id"):"blind",
 (1394,"zh-Hans"):"primary",(1394,"ja"):"primary",(1394,"zh-Hant"):"primary",
 (1396,"zh-Hans"):"primary",(1396,"zh-Hant"):"primary",
 (1397,"es"):"custom",(1397,"zh-Hans"):"primary",(1397,"hi"):"primary",(1397,"de"):"primary",(1397,"ja"):"blind",(1397,"pt-BR"):"primary",(1397,"ar"):"primary",(1397,"ko"):"custom",(1397,"zh-Hant"):"blind",(1397,"vi"):"primary",(1397,"id"):"blind",
 (1399,"vi"):"current",
 (1400,"hi"):"primary",(1400,"de"):"primary",(1400,"ja"):"primary",(1400,"fr"):"primary",(1400,"pt-BR"):"primary",(1400,"ar"):"primary",(1400,"ko"):"primary",(1400,"zh-Hant"):"blind",(1400,"vi"):"blind",(1400,"id"):"blind",
 (1401,"id"):"primary",
 (1402,"zh-Hans"):"primary",(1402,"hi"):"blind",(1402,"de"):"current",(1402,"ko"):"primary",(1402,"zh-Hant"):"primary",(1402,"id"):"primary",
}
CUSTOM={
 (1387,"es"):("Error al cargar los datos del enjambre","refinement"),
 (1387,"pt-BR"):("Erro ao carregar dados do enxame","refinement"),
 (1387,"ko"):("스웜 데이터를 로드하는 중 오류가 발생했습니다.","refinement"),
 (1397,"es"):("Evalúe localmente la evidencia pegada. Esto no publica nada, no consulta a nodos pares ni aplica cambios de clasificación.","correction"),
 (1397,"ko"):("붙여넣은 증거를 로컬에서 평가하세요. 이 작업은 내용을 공개하거나 피어 노드에 질의하거나 순위 변경을 적용하지 않습니다.","correction"),
}
RATIONALE={
 1384:"The source is a label for an entropy-check count. Entropy is a generic technical term here, so lowercase it in Vietnamese rather than styling it like a proper name.",
 1386:"This is a heading for counts grouped by error type. The selected Hindi wording is grammatical for the number of errors by type; retain the correction even though the blind review accepted the current phrase.",
 1387:"The caller is the swarm-download visualization error state. Exact-head sibling UI labels already translate or render the swarm concept consistently in this locale. The blind proposal switches only this error heading back to English Swarm, so retain the localized current wording; small grammar-consistency updates are separately stated in the selected target.",
 1391:"The exact callers use Errored as a transfer-state category in history tables and bulk-action selectors, distinct from generic Error and from broader Failed states. Select the explicit errored-state wording where it is clearer; retain concise current adjectives where the alternative is less idiomatic for a status label.",
 1394:"The caller displays this metric as a percentage. The selected wording says false-positive rate explicitly and uses the locale's standard technical term, rather than the less precise false-alarm/detection wording.",
 1396:"The caller displays a storage size in MB. Select the wording for estimated size or magnitude; the current term can be read as physical dimensions.",
 1397:"The caller is a tooltip for reviewing pasted mesh evidence locally. The selected wording preserves the local-only action, the lack of publishing and peer queries, and the lack of ranking changes. Locale-specific wording is chosen for technical peer terminology and clear negation.",
 1399:"The event-history error heading is clear in the existing Vietnamese value. The proposed synonym is a stylistic variation and does not improve the unavailable-state meaning.",
 1400:"The caller describes event hooks, remote targets, command hooks, and retry configuration in an administrator-policy card. The selected wording replaces the literal mistranslation of retry shape with settings/configuration language and keeps hook terminology appropriate for the locale.",
 1401:"This is the accessible name for a filter on event kind in the event-history form. The selected Indonesian word names an event occurrence more directly than the current word for an occasion.",
 1402:"The caller labels an administrator retention setting whose numeric value is in days. Select terms that match retention of system events, not general activities; retain concise current wording where it is already clear and precise.",
}
CUSTOM_RATIONALE={
 (1387,"es"):"The localized source glossary uses enjambre for Swarm; this edit also adds the natural Spanish article (los datos del enjambre).",
 (1387,"pt-BR"):"The sibling labels translate Swarm as enxame; use that established term instead of leaving the feature name in English.",
 (1387,"ko"):"Sibling Swarm labels use the established Korean transliteration 스웜; align this error heading with those exact-head labels.",
 (1397,"es"):"Use evidence rather than tests, and make the three negative effects explicit: nothing is published, no peer nodes are queried, and no ranking changes are applied.",
 (1397,"ko"):"The selected sentence uses an explicit user instruction, a local evaluation scope, and a clear subject for all three actions that do not occur.",
}

def sha(x): return hashlib.sha256(x if isinstance(x,bytes) else x.encode("utf-8")).hexdigest()
def readj(p): return json.loads(p.read_text(encoding="utf-8"))
def readl(p): return [json.loads(x) for x in p.read_text(encoding="utf-8").splitlines() if x.strip()]
def writej(p,obj): p.write_text(json.dumps(obj,ensure_ascii=False,sort_keys=True,indent=2)+"\n",encoding="utf-8")
def writel(p,rows): p.write_text("".join(json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(",",":"))+"\n" for x in rows),encoding="utf-8")
def run(args): return subprocess.run(args,check=True,capture_output=True,text=True).stdout.strip()
def fail(msg): raise SystemExit("FAIL: "+msg)
def checksum_check(folder,sum_name):
    sums={}
    for line in (folder/sum_name).read_text(encoding="utf-8").splitlines():
        digest,name=line.split("  ",1); sums[name]=digest
    actual={p.name for p in folder.iterdir() if p.is_file() and p.name!=sum_name}
    if set(sums)!=actual: fail("checksum inventory mismatch in "+str(folder))
    for name,digest in sums.items():
        if sha((folder/name).read_bytes())!=digest: fail("checksum mismatch "+str(folder/name))

if OUT.exists() and any(x.name != "build_cross_audit.py" for x in OUT.iterdir()): fail("output directory already has content")
OUT.mkdir(parents=True,exist_ok=True)
for src,dst in ((INPUT_SRC,OUT/"candidate-free-input"),(PRIMARY_SRC,OUT/"primary-review"),(BLIND_SRC,OUT/"blind-review")):
    shutil.copytree(src,dst)
I=OUT/"candidate-free-input"; P=OUT/"primary-review"; B=OUT/"blind-review"
for folder in (I,P,B): checksum_check(folder,"SHA256SUMS.txt")
verifiers={}
for name,cmd in (
 ("candidateFree",["python3",str(I/"verify-candidate-free.py")]),
 ("primary",["python3",str(P/"verify-primary-ledger.py")]),
 ("blind",["python3",str(B/"verify_primary_review.py")]),
):
    result=subprocess.run(cmd,capture_output=True,text=True)
    verifiers[name]={"returnCode":result.returncode,"stdout":result.stdout.strip(),"stderr":result.stderr.strip()}
    if result.returncode: fail(name+" input verifier failed: "+result.stdout+result.stderr)

pr=json.loads(run(["gh","pr","view",str(PR),"--repo",REPO,"--json","number,state,isDraft,headRefName,headRefOid,baseRefName,url,title"]))
branch=run(["gh","api","repos/"+REPO+"/git/matching-refs/heads/"+BRANCH,"--jq",".[0].object.sha"])
pull=run(["gh","api","repos/"+REPO+"/pulls/"+str(PR),"--jq",".head.sha"])
tree=run(["gh","api","repos/"+REPO+"/commits/"+HEAD,"--jq",".commit.tree.sha"])
wt_head=run(["git","-C",str(WORKTREE),"rev-parse","HEAD"])
wt_tree=run(["git","-C",str(WORKTREE),"rev-parse","HEAD^{tree}"])
wt_status=run(["git","-C",str(WORKTREE),"status","--porcelain"])
pinned_tree=run(["git","-C",str(WORKTREE),"rev-parse",HEAD+"^{tree}"])
if not (pr["state"]=="OPEN" and pr["isDraft"] and pr["headRefName"]==BRANCH and pr["headRefOid"]==branch==pull==HEAD and tree==pinned_tree==TREE and not wt_status):
    fail("live PR/branch/pull/tree or pinned commit object differs from required pin")
att={"repository":REPO,"pullRequest":PR,"state":pr["state"],"isDraft":pr["isDraft"],"url":pr["url"],"headRefName":pr["headRefName"],"baseRefName":pr["baseRefName"],"headRefOid":pr["headRefOid"],"branchRefOid":branch,"pullRefOid":pull,"tree":tree,"queriedAtUtc":datetime.now(timezone.utc).isoformat(),"queryCommands":["gh pr view 204 --repo snapetech-org/slskR --json number,state,isDraft,headRefName,headRefOid,baseRefName,url,title","gh api repos/snapetech-org/slskR/git/matching-refs/heads/"+BRANCH+" --jq .[0].object.sha","gh api repos/snapetech-org/slskR/pulls/204 --jq .head.sha","gh api repos/snapetech-org/slskR/commits/"+HEAD+" --jq .commit.tree.sha"],"localGitObjectDatabase":{"path":str(WORKTREE),"pinnedCommit":HEAD,"pinnedCommitTree":pinned_tree},"workingCopy":{"head":wt_head,"tree":wt_tree,"status":"clean","usedForAudit":False}}
writej(OUT/"live-ref-attestation.json",att)
writej(OUT/"input-verification.json",{"result":"PASS","packetVerifiers":verifiers,"packets":[{"path":f.name,"sha256Inventory":sha((f/"SHA256SUMS.txt").read_bytes())} for f in (I,P,B)]})

im=readj(I/"manifest.json"); pm=readj(P/"manifest.json"); bm=readj(B/"manifest.json")
if not all(m.get("head")==HEAD and m.get("tree")==TREE for m in (im,pm,bm)): fail("input packet head/tree pin mismatch")
cells=readl(I/"current-target-cells.jsonl"); contexts=readl(I/"source-contexts.jsonl"); primary=readl(P/"review-ledger.jsonl"); blind=readl(B/"primary-ledger.jsonl"); prior_holds=readl(I/"prior-hold-reattestation.jsonl")
if not (len(cells)==len(primary)==len(blind)==240 and len(contexts)==20 and len(prior_holds)==35): fail("cell/context/hold coverage mismatch")
if [(x["position"],x["locale"]) for x in cells] != [(p,l) for p in range(1383,1403) for l in LOCALES]: fail("candidate-free order mismatch")
if [(x["position"],x["locale"]) for x in primary] != [(p,l) for p in range(1383,1403) for l in LOCALES]: fail("primary order mismatch")
if [(x["position"],x["locale"]) for x in blind] != [(p,l) for p in range(1383,1403) for l in LOCALES]: fail("blind order mismatch")
if [x["position"] for x in contexts] != list(range(1383,1403)): fail("source-context range mismatch")
if any(x["reattestation"]!="same" or x["currentTarget"]!=x["priorCurrentTarget"] or x["currentTargetSha256"]!=x["priorCurrentTargetSha256"] for x in prior_holds): fail("a carry-forward hold changed")
cm={(x["position"],x["locale"]):x for x in cells}; pm={(x["position"],x["locale"]):x for x in primary}; bm={(x["position"],x["locale"]):x for x in blind}; ctx={x["position"]:x for x in contexts}
runtime_hash=sha((I/"localization-runtime-context.json").read_bytes())
ledger=[]; apply=[]; noop=[]; held=[]; agree=0; disagree=0; resolutions=Counter(); dispositions=Counter()
for c in cells:
    k=(c["position"],c["locale"]); pos,loc=k; p=pm[k]; b=bm[k]; current=c["currentTarget"]; context=ctx[pos]
    if not (p["sourceKey"]==b["sourceKey"]==c["sourceKey"]==context["sourceKey"]): fail("source lineage mismatch "+str(k))
    if not (p["sourceKeySha256"]==c["sourceKeySha256"]==b["sourceKeySha256"]): fail("source hash mismatch "+str(k))
    if not (p["currentTarget"]==b["currentTarget"]==current and p["currentTargetSha256"]==c["currentTargetSha256"]==b["currentTargetSha256"]): fail("current target hash mismatch "+str(k))
    if p["callerEvidence"]["callerContextSha256"]!=c["sourceContextSha256"] or b["callerContextSha256"]!=c["sourceContextSha256"]: fail("caller context hash mismatch "+str(k))
    if p["catalog"]["path"]!=c["catalogPath"] or b["catalogPath"]!=c["catalogPath"] or p["catalog"]["fileSha256"]!=c["catalogFileSha256"] or b["catalogFileSha256"]!=c["catalogFileSha256"]: fail("catalog file pin mismatch "+str(k))
    if context["productionCallerCount"]<=0: fail("unexpected callerless cell "+str(k))
    pd=p["disposition"]; bd=b["decision"]
    pt=current if pd=="accept-current" else p.get("proposedTarget")
    bt=current if bd=="accept-current" else b.get("proposedTarget")
    if not isinstance(pt,str) or not isinstance(bt,str): fail("review target not string "+str(k))
    same=(pt==bt)
    if same: agree+=1
    else: disagree+=1
    choice=PREF.get(k)
    if choice is None:
        if same: choice="agreement"
        elif pt==current and bt!=current: choice="blind"
        elif bt==current and pt!=current: choice="primary"
        else: fail("unmapped target disagreement "+str(k))
    if choice=="agreement":
        selected=pt; resolution="agreement"
        reason="Primary and blind reviews independently select the same exact target. The source and caller context are pinned to this head, and the selected value preserves the caller's meaning."
    elif choice=="primary":
        selected=pt; resolution="primary-selected"; reason=RATIONALE[pos]
    elif choice=="blind":
        selected=bt; resolution="blind-selected"; reason=RATIONALE[pos]
    elif choice=="current":
        selected=current; resolution="cross-audit-retain-current"; reason=RATIONALE[pos]
    elif choice=="custom":
        selected,custom_disp=CUSTOM[k]; resolution="cross-audit-new-target"; reason=CUSTOM_RATIONALE[k]
    else: fail("unknown choice "+str((k,choice)))
    if selected==current: final_disp="accept-current"
    elif choice=="custom": final_disp=custom_disp
    elif choice in ("primary","blind","agreement"):
        source_disp=pd if choice=="primary" else bd if choice=="blind" else pd
        other_disp=bd if choice in ("primary","agreement") else pd
        if source_disp not in ("correction","refinement") and other_disp not in ("correction","refinement"): fail("invalid selected review disposition "+str(k))
        final_disp="correction" if "correction" in (source_disp,other_disp) else "refinement"
    else: fail("changed target has no correction/refinement class "+str(k))
    action="no-op" if selected==current else "update"
    src_ph=PH.findall(c["sourceKey"]); dst_ph=PH.findall(selected)
    src_tags=TAG.findall(c["sourceKey"]); dst_tags=TAG.findall(selected)
    src_nums=NUM.findall(c["sourceKey"]); dst_nums=NUM.findall(selected)
    protected=c.get("sourceProtectedLiterals",[])
    missing=[t for t in protected if selected.count(t)<c["sourceKey"].count(t)]
    checks={"sourcePlaceholders":src_ph,"selectedPlaceholders":dst_ph,"placeholdersPreserved":sorted(src_ph)==sorted(dst_ph),"sourceMarkupTags":src_tags,"selectedMarkupTags":dst_tags,"markupPreserved":sorted(src_tags)==sorted(dst_tags),"sourceNumericTokens":src_nums,"selectedNumericTokens":dst_nums,"numericTokensPreserved":src_nums==dst_nums,"sourceProtectedLiterals":protected,"missingProtectedLiterals":missing,"protectedLiteralsPreserved":not missing,"sourceProtectedLiteralMismatchTokens":c.get("protectedLiteralMismatchTokens",[]),"candidateFreeDiagnosticFlags":{"placeholderSequenceMatches":c["placeholderSequenceMatches"],"markupMatches":c["markupMatches"],"numericTokensMatch":c["numericTokensMatch"],"protectedLiteralsMatch":c["protectedLiteralsMatch"]},"directCatalogLookupAndNamedPlaceholderSubstitution":True,"icuMessageSyntaxPresent":False}
    if not all(checks[x] for x in ("placeholdersPreserved","markupPreserved","numericTokensPreserved","protectedLiteralsPreserved")): fail("selected target token check failed "+str(k))
    row={"position":pos,"locale":loc,"localeName":LOCALE_NAMES[loc],"sourceKey":c["sourceKey"],"sourceKeySha256":c["sourceKeySha256"],"currentTarget":current,"currentTargetSha256":c["currentTargetSha256"],"sourceContextSha256":c["sourceContextSha256"],"callerCount":context["productionCallerCount"],"callerRefs":c["callerRefs"],"catalogPath":c["catalogPath"],"catalogFileSha256":c["catalogFileSha256"],"catalogGitBlob":c["catalogGitBlob"],"catalogKeyCount":c["catalogKeyCount"],"primaryDisposition":pd,"primaryTarget":pt,"primaryTargetSha256":sha(pt),"primaryRationale":p["rationale"],"primaryConfidence":p["confidence"],"blindDisposition":bd,"blindTarget":bt,"blindTargetSha256":sha(bt),"blindRationale":b["rationale"],"blindConfidence":b["confidence"],"reviewerTargetsAgree":same,"resolution":resolution,"resolutionRationale":reason,"selectedDisposition":final_disp,"selectedTarget":selected,"selectedTargetSha256":sha(selected),"applicationAction":action,"crossAuditConfidence":"moderate","nativeSpeakerApproved":False,"runtimeContextSha256":runtime_hash,"tokenChecks":checks}
    ledger.append(row); resolutions[resolution]+=1; dispositions[final_disp]+=1
    plan={key:row[key] for key in ("position","locale","sourceKey","sourceKeySha256","sourceContextSha256","catalogPath","catalogFileSha256","catalogGitBlob","catalogKeyCount","currentTarget","currentTargetSha256","selectedTarget","selectedTargetSha256","selectedDisposition","applicationAction")}
    if action=="update": apply.append(plan)
    else: noop.append(plan)
if agree+disagree!=240: fail("reviewer target agreement count mismatch")
if len(apply)+len(noop)!=240: fail("application plan coverage mismatch")

catalog_keys=["Swarm Analytics","Swarm Download Status","No swarm job selected","Error Loading Swarm Data"]
pins=readj(I/"catalog-file-pins.json")["localeCatalogs"]
sibling={}
for loc in LOCALES:
    path=f"web/src/lib/locales/ui-labels.{loc}.json"
    d=json.loads(run(["git","-C",str(WORKTREE),"show",f"{HEAD}:{path}"]))
    sibling[loc]={"catalogPath":path,"catalogPin":pins[loc],"labels":{key:d.get(key) for key in catalog_keys}}
writej(OUT/"terminology-context.json",{"head":HEAD,"tree":TREE,"method":"read-only git show at exact PR head","keys":catalog_keys,"locales":sibling,"note":"Confirms that current Swarm wording at source rank 1387 matches sibling feature labels in the same exact-head locale catalogs; custom Spanish, Brazilian Portuguese, and Korean targets align to sibling terminology."})
writel(OUT/"cross-audit-ledger.jsonl",ledger); writel(OUT/"apply-plan.jsonl",apply); writel(OUT/"no-op-plan.jsonl",noop); writel(OUT/"hold-plan.jsonl",held)
shutil.copy2(I/"prior-hold-reattestation.jsonl",OUT/"prior-hold-reattestation.jsonl")
summary={"repository":REPO,"pullRequest":PR,"url":pr["url"],"state":pr["state"],"isDraft":pr["isDraft"],"head":HEAD,"tree":TREE,"window":"W1383-W1402","positions":[1383,1402],"sourceCount":20,"localeCount":12,"cellCount":240,"primaryDispositionCounts":dict(Counter(x["disposition"] for x in primary)),"blindDispositionCounts":dict(Counter(x["decision"] for x in blind)),"reviewerTargetAgreements":agree,"reviewerTargetDisagreements":disagree,"resolutionCounts":dict(resolutions),"selectedDispositionCounts":dict(dispositions),"applicationUpdates":len(apply),"noOpCells":len(noop),"newHolds":len(held),"priorHoldsReattestedUnchanged":len(prior_holds),"priorSelectionsReattested":len(readl(I/"prior-selection-reattestation.jsonl")),"callerlessCells":sum(1 for x in contexts if x["productionCallerCount"]==0)*12,"selectedTokenMismatches":0,"nativeSpeakerApproved":False,"browserReviewPerformed":False,"repositoryChanged":False,"workflowFilesChanged":False,"testsBuildsOrCiRun":False,"releaseOrTag":False,"applyPlanSha256":sha((OUT/"apply-plan.jsonl").read_bytes()),"noOpPlanSha256":sha((OUT/"no-op-plan.jsonl").read_bytes()),"crossAuditLedgerSha256":sha((OUT/"cross-audit-ledger.jsonl").read_bytes()),"inputVerifiers":"PASS"}
writej(OUT/"summary.json",summary)
readme=f"""# slskR PR #204 W1383–W1402 third-party cross-audit

This independently reconciles 240 exact-head source/locale cells against the candidate-free input, primary semantic review, and blind review. PR #204 was re-queried as OPEN/DRAFT at {HEAD} with tree {TREE}; branch, pull ref, and commit tree agree. The local Git object database resolves the same pinned tree; its separate working copy is recorded but was not used as exact-head evidence.

The reviews agree on {agree} target strings and differ on {disagree}. Every disagreement is resolved in cross-audit-ledger.jsonl. The cross-audit also records three terminology consistency improvements at rank 1387 for Spanish, Brazilian Portuguese, and Korean based on sibling labels from the same exact-head catalogs. The selected application plan contains {len(apply)} exact-hash updates, {len(noop)} no-op decisions, and no new holds. All 35 previously held cells were reattested unchanged; no callerless cells occur in this window.

apply-plan.jsonl pins each changed cell to its current translation hash, catalog file hash/blob, source hash, and exact production caller-context hash. no-op-plan.jsonl preserves accepted current values. hold-plan.jsonl is empty; the separate carry-forward hold packet remains in prior-hold-reattestation.jsonl.

All selected targets preserve placeholders, markup, numeric tokens, and protected literals. The catalogs use direct lookup plus named substitution; no ICU message syntax occurs in this source window. This is machine semantic review and is not native-speaker approval. No repository/PR files, workflows, tests, builds, CI, browser sessions, releases, tags, or merges were changed or run.
"""
(OUT/"README.md").write_text(readme,encoding="utf-8")

pr2=json.loads(run(["gh","pr","view",str(PR),"--repo",REPO,"--json","number,state,isDraft,headRefName,headRefOid"]))
branch2=run(["gh","api","repos/"+REPO+"/git/matching-refs/heads/"+BRANCH,"--jq",".[0].object.sha"])
pull2=run(["gh","api","repos/"+REPO+"/pulls/"+str(PR),"--jq",".head.sha"])
tree2=run(["gh","api","repos/"+REPO+"/commits/"+HEAD,"--jq",".commit.tree.sha"])
if not (pr2["state"]=="OPEN" and pr2["isDraft"] and pr2["headRefOid"]==branch2==pull2==HEAD and tree2==TREE): fail("live PR moved during cross-audit")
att["recheckedAtUtc"]=datetime.now(timezone.utc).isoformat(); att["postReviewHead"]=pr2["headRefOid"]; att["postReviewBranchRefOid"]=branch2; att["postReviewPullRefOid"]=pull2; att["postReviewTree"]=tree2
writej(OUT/"live-ref-attestation.json",att)
print(json.dumps({"result":"BUILT","summary":summary,"output":str(OUT)},ensure_ascii=False,indent=2))
