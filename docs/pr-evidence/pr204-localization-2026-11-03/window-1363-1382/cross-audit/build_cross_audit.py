#!/usr/bin/env python3
from pathlib import Path
from collections import Counter
from datetime import datetime, timezone
import hashlib, json, re, shutil, subprocess, sys

OUT=Path(__file__).resolve().parent
TASK=Path("/home/keith/Documents/code/task-scratch")
INPUT_SRC=TASK/"slskr-pr204-next-candidatefree-20261103/candidate-free-input"
BLIND_INPUT_SRC=TASK/"slskr-pr204-next-candidatefree-20261103/blind-input"
PRIMARY_SRC=TASK/"slskr-pr204-w1363-1382-primary-review-20261103"
BLIND_SRC=TASK/"slskr-pr204-w1363-1382-blind-review-20261103"
HEAD="281c39ec0cdb3677d7d523b7c4f0cd0d52bbf14c"
TREE="777b234b1aa3cb7a2c9fd560b2c0fecc4e7fe49d"
REPO="snapetech-org/slskR"; PR=204
LOCALES=["es","zh-Hans","hi","de","ja","fr","pt-BR","ar","ko","zh-Hant","vi","id"]
BLIND_USE={
 1363:{"es","zh-Hans","hi","de","fr","pt-BR","zh-Hant","vi","id"},
 1364:{"es","zh-Hans","hi","de","fr","pt-BR","ar","vi"},
 1365:{"zh-Hans","ja","fr","ko","zh-Hant"},
 1366:{"es","hi","de","ja","fr","pt-BR","ko","vi","id"},
 1367:set(LOCALES),
 1368:{"zh-Hans","hi","ja","ko","zh-Hant"},
 1369:{"es","zh-Hans","hi","fr","pt-BR","ar","ko","zh-Hant","vi","id"},
 1370:{"zh-Hans","hi","ja","fr","pt-BR","ar","ko","zh-Hant","vi","id"},
 1371:{"es","zh-Hans","hi","de","ja","fr","pt-BR","ko","zh-Hant","vi"},
 1372:{"es","zh-Hans","hi","de","ja","fr","pt-BR","ar","zh-Hant","vi","id"},
 1373:{"es","de","ja","fr","pt-BR","ar","ko","vi","id"},
 1374:{"de","ja","fr","pt-BR","ko"},
 1375:{"zh-Hans","hi","de","ja","fr","pt-BR","ar","ko","zh-Hant","id"},
 1377:{"zh-Hans","pt-BR","zh-Hant"},
 1380:{"es","zh-Hans","hi","fr","pt-BR","ar","ko","zh-Hant","id"},
 1381:{"hi","de","ja","fr","pt-BR","ko"},
 1382:{"hi"}
}
BLIND_CORRECTIONS={
 1366:{"es","hi","de","fr","pt-BR","vi","id"},
 1367:set(LOCALES),
 1372:{"hi","ar"},
 1375:{"hi"},
 1382:{"hi"}
}
POSITION_CONTEXT={
 1363:"A checkbox label in the administrator security policy form; its adjacent popup says it enables strict startup and request hardening checks.",
 1364:"The accessible name of that same policy checkbox; the word web scopes the setting.",
 1365:"An option in the privacy/security mode selector, alongside Standard and Maximum.",
 1366:"An input placeholder paired with the Get Graph action and the graphContentId value in the content graph panel.",
 1367:"Validation copy shown when the Library Health scanner starts without its required library path.",
 1368:"The empty-state header for Library Health, instructing users to enter a library path and start a scan.",
 1369:"Validation shown before the subject-index conflict view loads, requiring a realm identifier.",
 1370:"A status message when either the local slskR path or media-server path is missing; the purpose is to compare those paths.",
 1371:"A text-field placeholder in the collection creation modal.",
 1372:"A placeholder in the external-ID resolver input. Uppercase ID is a protected technical literal.",
 1373:"The accessible name of the visualizer fullscreen button; its popup says the action enters true fullscreen.",
 1374:"A text-field placeholder in the share-group creation dialog.",
 1375:"A library-path input placeholder. The examples /music and C:\\Music must remain byte-for-byte unchanged.",
 1376:"There is no resolved production caller for this source. Keep all locales held until caller meaning is known.",
 1377:"A notes textarea placeholder attached to the current user's Note field.",
 1378:"A room-name field placeholder in the room-creation modal.",
 1379:"A required search-text placeholder in the Wishlist modal.",
 1380:"Popup text explains that the visualizer enters actual fullscreen, distinct from filling the browser window.",
 1381:"A username input placeholder in the share-group form.",
 1382:"A statistic label beside subject-index/conflict counts; Entries means indexed records."
}
BLIND_REASON={
 1363:"The blind value uses an action verb that conveys enforcing the hardening setting in a checkbox label.",
 1364:"The blind value names web scope and presents hardening as an enforced policy in the checkbox's accessible name.",
 1365:"The blind value better fits an option label and the locale's typography for the privacy/anonymity parenthetical.",
 1366:"The blind value uses graph terminology rather than a chart/diagram false friend; it also keeps ContentID in its exact technical form.",
 1367:"The blind value preserves Library Health as the named feature that owns the required path.",
 1368:"The blind value gives a direct, natural instruction for the scanner empty state.",
 1369:"The blind value preserves realm as the technical identifier used by the subject-index conflict component.",
 1370:"The blind value describes checking whether the two configured paths match, rather than saying that the server agrees.",
 1371:"The blind value is a concise field placeholder and uses the locale's natural term for a collection title.",
 1372:"The blind value reads as an input prompt for resolving an external ID and preserves uppercase ID.",
 1373:"The blind value describes opening/showing the visualizer in fullscreen as the button action.",
 1374:"The blind value is a concise group-name field placeholder.",
 1375:"The blind value is suitable for an input placeholder and preserves both path examples exactly.",
 1377:"The blind value uses a natural notes/remarks term for the user's textarea.",
 1380:"The blind value says to enter real fullscreen, matching the popup's distinction from browser-window fullscreen.",
 1381:"The blind value is concise for a username input placeholder.",
 1382:"The blind Hindi spelling is the standard form for this count label."
}
PRIMARY_REASON={
 1363:"The current wording keeps the enforce meaning without adding a second force verb or changing the policy scope.",
 1364:"The existing value is localized and clear; the rejected option adds an awkward or redundant enforcement construction in this locale.",
 1365:"The current option label already conveys the enhanced privacy/anonymity mode; the alternative is mainly a stylistic or punctuation change.",
 1366:"The Chinese wording specifies a relationship graph, which fits this graph panel more closely than a generic atlas/chart term.",
 1368:"The existing sentence is clear and maintains the established formal register; the alternative changes register without correcting the empty-state instruction.",
 1369:"The existing wording localizes the realm and subject-index concepts naturally for this locale instead of inserting an English technical phrase.",
 1370:"The existing Spanish wording is a clear formal instruction; the alternative changes register without changing what the user must compare.",
 1372:"The Korean current wording preserves the resolver action; the alternative says to check the ID, which is less specific than resolving it.",
 1373:"The Chinese wording names the fullscreen visualizer itself; the alternative describes displaying visualization effects and weakens the tool/action label.",
 1374:"The existing Spanish placeholder maintains formal address; the alternative switches to an informal imperative.",
 1375:"The existing Spanish value maintains formal address and preserves both literal path examples.",
 1377:"The existing field prompt is already clear; the alternative changes wording or ellipsis style without improving the caller-specific meaning.",
 1378:"The current room-name placeholder is clear; the alternatives are mostly register, wording, or ellipsis-style changes.",
 1379:"The current search placeholder is clear and faithful; the alternatives do not add meaning required by the Wishlist input caller.",
 1381:"The existing Spanish placeholder maintains formal address; the alternative switches to an informal imperative.",
 1382:"The selected wording is more precise for an indexed-record count than the rejected generic item wording."
}
PROTECTED_BY_POS={
 1366:["ContentID"],1367:["Library Health"],1370:["slskr"],1372:["ID"],
 1375:["/music",r"C:\Music"]
}
PH=re.compile(r"\{[^{}]*\}")
TAG=re.compile(r"</?[A-Za-z][^>]*>")
NUM=re.compile(r"(?<![A-Za-z])\d[\d,]*(?:\.\d+)?(?![A-Za-z])")
def sha(data): return hashlib.sha256(data if isinstance(data,bytes) else data.encode("utf-8")).hexdigest()
def readj(path): return json.loads(path.read_text(encoding="utf-8"))
def readl(path): return [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines() if x.strip()]
def writej(path,obj): path.write_text(json.dumps(obj,ensure_ascii=False,sort_keys=True,indent=2)+"\n",encoding="utf-8")
def writel(path,rows): path.write_text("".join(json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(",",":"))+"\n" for x in rows),encoding="utf-8")
def run(args): return subprocess.run(args,check=True,capture_output=True,text=True).stdout.strip()
def fail(msg): raise SystemExit("FAIL: "+msg)
if not all(p.exists() for p in (INPUT_SRC,BLIND_INPUT_SRC,PRIMARY_SRC,BLIND_SRC)):
    fail("pinned input or review directory missing")
for source,dest in ((INPUT_SRC,OUT/"candidate-free-input"),(BLIND_INPUT_SRC,OUT/"blind-input"),(PRIMARY_SRC,OUT/"primary-review"),(BLIND_SRC,OUT/"blind-review")):
    if not dest.exists(): shutil.copytree(source,dest)

# Re-run packet verifiers and preserve their exact outputs.
verification={}
commands=[
 ("candidateFreeInput",["python3",str(INPUT_SRC/"verify-candidate-free.py")]),
 ("primaryReview",["python3",str(PRIMARY_SRC/"verify-primary-ledger.py")]),
 ("blindReview",["python3",str(BLIND_SRC/"verify_blind_review.py"),"--input",str(BLIND_INPUT_SRC)])
]
for name,cmd in commands:
    p=subprocess.run(cmd,capture_output=True,text=True)
    verification[name]={"returnCode":p.returncode,"stdout":p.stdout.strip(),"stderr":p.stderr.strip()}
    if p.returncode: fail(name+" verifier failed: "+p.stdout+p.stderr)

im=readj(INPUT_SRC/"manifest.json")
repo_worktree=TASK/"slskr-pr204-w1343-1362-apply-20261103/repo"
wt_head=run(["git","-C",str(repo_worktree),"rev-parse","HEAD"])
wt_tree=run(["git","-C",str(repo_worktree),"rev-parse","HEAD^{tree}"])
wt_status=run(["git","-C",str(repo_worktree),"status","--porcelain"])
if wt_head!=HEAD or wt_tree!=TREE or wt_status:
    fail("pinned local worktree status/head/tree changed")
pr_view=json.loads(run(["gh","pr","view",str(PR),"--repo",REPO,"--json","number,state,headRefName,headRefOid,baseRefName,url,isDraft"]))
branch=run(["gh","api","repos/"+REPO+"/git/matching-refs/heads/"+pr_view["headRefName"],"--jq",".[0].object.sha"])
pull=run(["gh","api","repos/"+REPO+"/pulls/"+str(PR),"--jq",".head.sha"])
tree=run(["gh","api","repos/"+REPO+"/commits/"+pr_view["headRefOid"],"--jq",".commit.tree.sha"])
if pr_view["headRefOid"]!=HEAD or branch!=HEAD or pull!=HEAD or tree!=TREE:
    fail("live PR, branch, pull ref, or tree differs from the pin")
live={
 "repository":REPO,"pullRequest":PR,"state":pr_view["state"],"isDraft":pr_view["isDraft"],
 "url":pr_view["url"],"headRefName":pr_view["headRefName"],"baseRefName":pr_view["baseRefName"],
 "headRefOid":pr_view["headRefOid"],"liveBranchRefOid":branch,"livePullRefOid":pull,"headTree":tree,
 "queriedAtUtc":datetime.now(timezone.utc).isoformat(),
 "queryCommands":["gh pr view 204 --repo snapetech-org/slskR --json number,state,headRefName,headRefOid,baseRefName,url,isDraft",
                 "gh api repos/snapetech-org/slskR/git/matching-refs/heads/"+pr_view["headRefName"]+" --jq .[0].object.sha",
                 "gh api repos/snapetech-org/slskR/pulls/204 --jq .head.sha",
                 "gh api repos/snapetech-org/slskR/commits/"+HEAD+" --jq .commit.tree.sha"],
 "verifiedWorktree":{"path":str(repo_worktree),"head":wt_head,"tree":wt_tree,"status":"clean"},"candidateFreeManifestWorktreePath":im["localWorktree"],"candidateFreeManifestWorktreeCurrentlyPresent":Path(im["localWorktree"]).exists()
}
writej(OUT/"live-pr-attestation.json",live)
writej(OUT/"source-verifier-results.json",verification)

I=OUT/"candidate-free-input"; BI=OUT/"blind-input"; P=OUT/"primary-review"; B=OUT/"blind-review"
im=readj(I/"manifest.json"); bim=readj(BI/"manifest.json"); pm=readj(P/"manifest.json"); bm=readj(B/"manifest.json")
if not all((m["head"]==HEAD and m["tree"]==TREE) for m in (im,bim,pm,bm)):
    fail("evidence head/tree mismatch")
cells=readl(I/"current-target-cells.jsonl")
contexts=readl(I/"source-contexts.jsonl")
primary=readl(P/"review-ledger.jsonl")
blind=readl(B/"sealed-translation-ledger.jsonl")
prompts=readl(BI/"prompts.jsonl")
holds=readl(I/"prior-hold-reattestation.jsonl")
if not (len(cells)==len(primary)==len(blind)==len(prompts)==240 and len(contexts)==20 and len(holds)==23):
    fail("evidence coverage mismatch")
if [r["position"] for r in contexts]!=list(range(1363,1383)):
    fail("source positions mismatch")
if [(r["position"],r["locale"]) for r in cells]!=[(p,l) for p in range(1363,1383) for l in LOCALES]:
    fail("candidate-free cell order mismatch")
if [(r["position"],r["locale"]) for r in primary]!=[(p,l) for p in range(1363,1383) for l in LOCALES]:
    fail("primary cell order mismatch")
if [(r["position"],r["locale"]) for r in prompts]!=[(p,l) for p in range(1363,1383) for l in LOCALES]:
    fail("blind prompt order mismatch")
if [(r["position"],r["locale"]) for r in blind]!=[(p,l) for p in range(1363,1383) for l in LOCALES]:
    fail("blind review order mismatch")
if not all(r["reattestation"]=="same" and r["currentTarget"]==r["priorCurrentTarget"] and r["currentTargetSha256"]==r["priorCurrentTargetSha256"] for r in holds):
    fail("one or more 23 carry-forward holds changed")
if im["carryForwardHoldCount"]!=23 or im["carryForwardHoldUnchangedCount"]!=23 or im["carryForwardHoldChangedCount"]!=0:
    fail("prior hold source/position pins mismatch")
if im.get("callerResolutionHoldPositions")!=[1376]:
    fail("candidate-free callerless position mismatch")

ctx_by_pos={r["position"]:r for r in contexts}
P_by={(r["position"],r["locale"]):r for r in primary}
B_by={(r["position"],r["locale"]):r for r in blind}
PR_by={(r["position"],r["locale"]):r for r in prompts}
ledger=[]; resolutions=Counter(); final_dispositions=Counter(); disagree_by_locale=Counter(); disagree_by_pos=Counter()
input_mismatch_cells=[(r["position"],r["locale"]) for r in cells if not r["protectedLiteralsMatch"]]
target_agreements=0; target_disagreements=0
for c in cells:
    key=(c["position"],c["locale"]); pos,loc=key
    p=P_by[key]; b=B_by[key]; prompt=PR_by[key]; ctx=ctx_by_pos[pos]
    bd=b["decision"]; bt=bd.get("translation")
    if not (p["sourceKey"]==prompt["sourceKey"]==c["sourceKey"]==ctx["sourceKey"]):
        fail("source key mismatch at "+str(key))
    if not (p["sourceKeySha256"]==prompt["sourceKeySha256"]==c["sourceKeySha256"]==ctx["sourceKeySha256"]):
        fail("source hash mismatch at "+str(key))
    if not (p["locale"]==prompt["locale"]==c["locale"] and prompt["position"]==pos):
        fail("locale/position mismatch at "+str(key))
    if p["currentTarget"]!=c["currentTarget"] or p["currentTargetSha256"]!=c["currentTargetSha256"]:
        fail("current target pin mismatch at "+str(key))
    if p["callerEvidence"]["callerContextSha256"]!=c["sourceContextSha256"] or prompt["sourceContextRef"]["sourceContextSha256"]!=c["sourceContextSha256"]:
        fail("caller context pin mismatch at "+str(key))
    if len(prompt["callerRefs"])!=ctx["productionCallerCount"]:
        fail("blind caller reference count mismatch at "+str(key))
    pt=None if p["disposition"]=="hold" else p.get("proposedTarget",p["currentTarget"])
    if pos==1376:
        if p["disposition"]!="hold" or bd["disposition"]!="hold" or pt is not None or bt is not None or ctx["productionCallerCount"]!=0:
            fail("rank 1376 must remain held in both reviews")
        resolution="hold-consensus"; target_agreement=None; selected=None; disposition="hold"
        note="Both reviews hold this translation. The exact-head source packet has no production caller for rank 1376, so locale semantics cannot be resolved from the available UI context; preserve the hold across all locales."
    else:
        if p["disposition"]=="hold" or bd["disposition"]!="propose" or not isinstance(pt,str) or not isinstance(bt,str):
            fail("unexpected non-hold disposition at "+str(key))
        target_agreement=(pt==bt)
        if target_agreement:
            target_agreements+=1; resolution="agreement"; selected=pt; disposition=p["disposition"]
            note="Primary and blind reviews select the same value. "+POSITION_CONTEXT[pos]+" The common target passes the recorded token and markup checks."
        else:
            target_disagreements+=1; disagree_by_locale[loc]+=1; disagree_by_pos[pos]+=1
            if loc in BLIND_USE.get(pos,set()):
                if pt==bt: fail("blind override is not a target disagreement at "+str(key))
                resolution="blind-selected"; selected=bt
                if selected==c["currentTarget"]:
                    disposition="accept-current"
                elif loc in BLIND_CORRECTIONS.get(pos,set()):
                    disposition="correction"
                else:
                    disposition="refinement"
                note="I select the blind review's proposal. "+BLIND_REASON[pos]+" The pinned caller confirms this use: "+POSITION_CONTEXT[pos]+" The primary alternative is recorded alongside it for review."
            else:
                resolution="primary-selected"; selected=pt; disposition=p["disposition"]
                if selected==c["currentTarget"]: disposition="accept-current"
                note="I retain the primary review's value. "+PRIMARY_REASON[pos]+" The pinned caller confirms this use: "+POSITION_CONTEXT[pos]+" The blind alternative is recorded alongside it; it does not improve the meaning or fit for this caller."
    if selected is not None and disposition not in ("accept-current","correction","refinement"):
        fail("invalid selected disposition at "+str(key))
    if selected is None and disposition!="hold":
        fail("missing target is not a hold at "+str(key))
    # Candidate-free runtime is direct lookup plus named-value substitution, not ICU plural formatting.
    required=PROTECTED_BY_POS.get(pos,[])
    source_ph=PH.findall(c["sourceKey"]); selected_ph=PH.findall(selected) if selected is not None else None
    source_tag=TAG.findall(c["sourceKey"]); selected_tag=TAG.findall(selected) if selected is not None else None
    source_num=NUM.findall(c["sourceKey"]); selected_num=NUM.findall(selected) if selected is not None else None
    missing=[x for x in required if selected is not None and selected.count(x)<c["sourceKey"].count(x)]
    path_counts={x:(selected.count(x) if selected is not None else None) for x in required if pos==1375}
    tokens={
      "sourcePlaceholders":source_ph,"selectedPlaceholders":selected_ph,
      "placeholdersPreserved":selected is None or sorted(source_ph)==sorted(selected_ph),
      "sourceMarkup":source_tag,"selectedMarkup":selected_tag,
      "markupPreserved":selected is None or sorted(source_tag)==sorted(selected_tag),
      "sourceNumbers":source_num,"selectedNumbers":selected_num,
      "numericTokensPreserved":selected is None or source_num==selected_num,
      "requiredProtectedLiterals":required,"missingProtectedLiterals":missing,
      "protectedLiteralsPreserved":selected is None or not missing,
      "pathExampleOccurrenceCounts":path_counts,
      "pathExamplesPreservedExactlyOnce":(all(v==1 for v in path_counts.values()) if pos==1375 and selected is not None else (None if selected is None else True)),
      "callerlessHoldChecksNotApplicable":selected is None,
      "runtimeUsesDirectLookupAndNamedSubstitution":True,
      "icuMessageSyntaxPresent":False
    }
    if selected is not None:
        if not tokens["placeholdersPreserved"] or not tokens["markupPreserved"] or not tokens["numericTokensPreserved"] or not tokens["protectedLiteralsPreserved"] or tokens["pathExamplesPreservedExactlyOnce"] is False:
            fail("selected token/path check failed at "+str(key))
    row={
      "position":pos,"locale":loc,"localeName":b["localeName"],
      "sourceKey":c["sourceKey"],"sourceKeySha256":c["sourceKeySha256"],
      "currentTarget":c["currentTarget"],"currentTargetSha256":c["currentTargetSha256"],
      "sourceContextSha256":c["sourceContextSha256"],
      "callerless":ctx["productionCallerCount"]==0,
      "callerCount":ctx["productionCallerCount"],
      "callerReferences":prompt["callerRefs"],
      "primaryDisposition":p["disposition"],"primaryTarget":pt,
      "primaryTargetSha256":sha(pt) if pt is not None else None,
      "primaryRationale":p["rationale"],"primaryConfidence":p["confidence"],
      "primaryChecks":p["checks"],
      "blindDisposition":bd["disposition"],"blindTarget":bt,
      "blindTargetSha256":sha(bt) if bt is not None else None,
      "blindRationale":bd["rationale"],"blindConfidence":bd["confidence"],
      "blindTokenChecks":bd["tokenChecks"],
      "targetsAgree":target_agreement,
      "resolution":resolution,"resolutionRationale":note,
      "selectedDisposition":disposition,"selectedTarget":selected,
      "selectedTargetSha256":sha(selected) if selected is not None else None,
      "crossAuditConfidence":"high" if selected is None else "moderate",
      "nativeSpeakerApproved":False,"runtimeContextSha256":sha((I/"localization-runtime-context.json").read_bytes()),
      "tokenAndRuntimeChecks":tokens
    }
    ledger.append(row); resolutions[resolution]+=1; final_dispositions[disposition]+=1
if len(input_mismatch_cells)!=2 or set(input_mismatch_cells)!={(1372,"hi"),(1372,"ar")}:
    fail("expected the two known current protected-literal mismatches at rank 1372")
if target_agreements!=35 or target_disagreements!=193:
    fail("primary/blind target adjudication totals changed")
if len([r for r in ledger if r["position"]==1376 and r["selectedDisposition"]=="hold"])!=12:
    fail("all twelve rank-1376 locale cells must remain held")
if len(BLIND_USE) and sum(len(x) for x in BLIND_USE.values())!=132:
    fail("unexpected blind-selection adjudication count")
writel(OUT/"resolution-ledger.jsonl",ledger)
# Preserve a direct copy of the carry-forward hold evidence for review convenience.
shutil.copy2(I/"prior-hold-reattestation.jsonl",OUT/"prior-hold-reattestation.jsonl")
summary={
 "repository":REPO,"pullRequest":PR,"url":live["url"],"state":live["state"],"draft":live["isDraft"],
 "head":HEAD,"tree":TREE,"window":"W1363-W1382","positions":[1363,1382],
 "previousBoundaryPosition":1362,"nextBoundaryPosition":1383,
 "sourceCount":20,"localeCount":12,"cellCount":240,"proposalCells":228,"holdCells":12,
 "primaryBlindTargetAgreementsAmongProposals":target_agreements,
 "primaryBlindTargetDisagreements":target_disagreements,
 "disagreementsByLocale":{loc:disagree_by_locale[loc] for loc in LOCALES},
 "disagreementsByPosition":{str(pos):disagree_by_pos[pos] for pos in range(1363,1383)},
 "resolutionCounts":dict(resolutions),"selectedDispositionCounts":dict(final_dispositions),
 "blindSelectedDisagreements":sum(1 for r in ledger if r["resolution"]=="blind-selected"),
 "primarySelectedDisagreements":sum(1 for r in ledger if r["resolution"]=="primary-selected"),
 "callerlessPosition":1376,"callerlessCellsHeld":12,"priorCarryForwardHoldsReattestedUnchanged":23,
 "priorSelectedRowsReattested":120,"inputCurrentProtectedLiteralMismatchCells":2,
 "inputProtectedLiteralMismatchKeys":[{"position":p,"locale":l} for p,l in sorted(input_mismatch_cells)],
 "selectedPlaceholderMismatches":0,"selectedMarkupMismatches":0,"selectedNumericMismatches":0,
 "selectedProtectedLiteralMismatches":0,"selectedPathExampleMismatches":0,
 "primaryUnresolvedPathExampleMismatchCells":2,"primaryPathExampleMismatchDisposition":"both are rank-1376 callerless holds; no translation selected",
 "nativeSpeakerReviewPerformed":False,"repositoryOrPullRequestMutated":False,
 "testsBuildsOrCiRun":False,"inputVerifier":"PASS","primaryVerifier":"PASS","blindVerifier":"PASS",
 "liveHeadRequeried":True,"branchPullAndTreeAgree":True
}
writej(OUT/"summary.json",summary)
readme="""# slskR PR #204 W1363-W1382 cross-audit

This sealed package adjudicates all 240 source/locale cells against the candidate-free exact-head packet, the semantic primary review, and the independent blind translation review. The live PR, branch ref, pull ref, and tree were re-queried at head 281c39ec0cdb3677d7d523b7c4f0cd0d52bbf14c and tree 777b234b1aa3cb7a2c9fd560b2c0fecc4e7fe49d.

Among 228 proposal cells, the primary and blind targets agree on 35 and differ on 193; every difference is explicitly resolved in the ledger. All 12 cells at callerless rank 1376 remain held. The 23 carry-forward holds and 120 prior selected rows are reattested by the included input packet and remain unchanged.

The candidate-free packet reports two existing protected-literal mismatches in current catalog values (rank 1372 Hindi and Arabic). The selected values preserve uppercase ID. Both primary path-example mismatch flags belong to held rank 1376 cells; no target is selected for them. Selected proposals pass placeholder, markup, number, protected-literal, and path-example checks.

The package includes exact copies of the candidate-free input, blind-input prompts, primary review, and blind review. verify_cross_audit.py runs the copied packet verifiers and checks the cross-audit ledger, all pins, all 240 cells, the 23 carry-forward holds, and the 12 rank-1376 holds.

This is a text review without native-speaker approval. No repository or PR files were changed, and no tests, builds, CI, or releases were run.
"""
(OUT/"README.md").write_text(readme,encoding="utf-8")
verifier=r'''#!/usr/bin/env python3
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
'''
(OUT/"verify_cross_audit.py").write_text(verifier,encoding="utf-8")
(OUT/"verify_cross_audit.py").chmod(0o755)
# Build exact hashes; all nested evidence checksum files are retained and included.
file_hashes={}
for p in sorted(x for x in OUT.rglob("*") if x.is_file() and x.relative_to(OUT).as_posix() not in ("manifest.json","SHA256SUMS.txt")):
    rel=p.relative_to(OUT).as_posix()
    file_hashes[rel]={"sha256":sha(p.read_bytes()),"bytes":p.stat().st_size}
manifest={
 "schema":"slskr-cross-audit-v1","repository":REPO,"pullRequest":PR,"window":"W1363-W1382",
 "head":HEAD,"tree":TREE,"cellCount":240,"priorHoldCount":23,"callerlessPosition":1376,
 "candidateFreeManifestSha256":sha((I/"manifest.json").read_bytes()),
 "candidateFreeChecksumListSha256":sha((I/"SHA256SUMS.txt").read_bytes()),
 "blindInputManifestSha256":sha((BI/"manifest.json").read_bytes()),
 "blindInputChecksumListSha256":sha((BI/"SHA256SUMS.txt").read_bytes()),
 "primaryManifestSha256":sha((P/"manifest.json").read_bytes()),
 "primaryChecksumListSha256":sha((P/"SHA256SUMS").read_bytes()),
 "blindManifestSha256":sha((B/"manifest.json").read_bytes()),
 "blindChecksumListSha256":sha((B/"SHA256SUMS.txt").read_bytes()),
 "fileHashes":file_hashes
}
writej(OUT/"manifest.json",manifest)
all_files=sorted(p for p in OUT.rglob("*") if p.is_file() and p.relative_to(OUT).as_posix()!="SHA256SUMS.txt")
(OUT/"SHA256SUMS.txt").write_text("".join(sha(p.read_bytes())+"  "+p.relative_to(OUT).as_posix()+"\n" for p in all_files),encoding="utf-8")
print("Created",OUT)
print("Rows",len(ledger),"target differences",target_disagreements,"selected blind",sum(1 for x in ledger if x["resolution"]=="blind-selected"),"holds",len(holds))

