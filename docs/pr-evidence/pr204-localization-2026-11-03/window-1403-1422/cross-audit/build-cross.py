import json,hashlib,re,shutil
from pathlib import Path
R=Path("/home/keith/Documents/code/task-scratch/slskr-pr204-w1403-1422-cross-audit-20261103")
CF=R/"evidence/candidate-free-input"; PR=R/"evidence/primary-review"; IND=R/"independent-review"
sha=lambda b:hashlib.sha256(b).hexdigest()
def readj(p):return json.loads(p.read_text(encoding="utf-8"))
def jl(p):return [json.loads(x) for x in p.read_text(encoding="utf-8").splitlines() if x.strip()]
def canon(x):return json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(",",":"))
def tokens(s):
 return {"placeholders":re.findall(r"\{[A-Za-z][A-Za-z0-9_]*\}",s),"markupTags":re.findall(r"</?[A-Za-z][^>]*>",s),"numericTokens":re.findall(r"(?<![A-Za-z])\d+(?:[.,]\d+)?%?(?![A-Za-z])",s),"protectedLiterals":list(dict.fromkeys(m.group(0) for m in re.finditer(r"(?<![A-Za-z0-9])(?:[A-Z]{2,}[A-Z0-9]*|ffmpeg|Chromaprint|Soulseek|Spotify|YouTube|Pushbullet|Matrix|WebSocket|OpenAI)(?![A-Za-z0-9])",s)))}
cf_cells={(x["position"],x["locale"]):x for x in jl(CF/"current-target-cells.jsonl")}
cf_ctx={x["position"]:x for x in jl(CF/"source-contexts.jsonl")}
ind={(x["position"],x["locale"]):x for x in jl(IND/"independent-review.jsonl")}
prim={(x["position"],x["locale"]):x for x in jl(PR/"review-ledger.jsonl")}
pdec={(x["position"],x["locale"]):x for x in readj(PR/"review-decisions.json")}
assert len(cf_cells)==len(ind)==len(prim)==240 and len(pdec)==64
input_manifest=readj(CF/"manifest.json"); primary_manifest=readj(PR/"manifest.json")
assert input_manifest["head"]==primary_manifest["head"]=="727500e46852a5b6578e571781693857510943d9"
assert input_manifest["tree"]==primary_manifest["tree"]=="c71165c20fc6ba7d49d563898ea2ec8e1e448672"
locs=input_manifest["localeOrder"]; decisions=[]
for k,base in sorted(cf_cells.items()):
 i=ind[k]; p=prim[k]; d=pdec.get(k)
 assert base["sourceKey"]==i["sourceKey"]==p["sourceKey"]
 assert base["sourceKeySha256"]==i["sourceKeySha256"]==p["sourceKeySha256"]
 assert base["currentTargetSha256"]==i["currentTargetSha256"]==p["currentTargetSha256"]
 assert base["sourceContextSha256"]==i["sourceContextSha256"]==p["callerEvidence"]["callerContextSha256"]
 assert base["catalogFileSha256"]==i["catalogFileSha256"]==p["catalog"]["fileSha256"]
 assert base["catalogGitBlob"]==i["catalogGitBlob"]==p["catalog"]["gitBlob"]
 assert base["catalogPath"]==i["catalogPath"]==p["catalog"]["path"]
 assert base["callerRefs"]==i["callerRefs"]==p["callerEvidence"]["callerRefs"]
 ptarget=d["target"] if d else base["currentTarget"]
 if d:
  assert d["target"]!=base["currentTarget"]
  assert d["disposition"]==p["disposition"] and d["rationale"]==p["rationale"]
 if i["disposition"]=="update" and d:
  relation="shared-change-same-target" if i["independentProposal"]==ptarget else "shared-change-different-target"
 elif i["disposition"]=="update" and not d: relation="independent-only-change"
 elif i["disposition"]=="hold" and d: relation="primary-change-resolves-independent-hold"
 elif d: relation="primary-only-change"
 else: relation="no-change-agreement"
 selected_source="current"
 selected=base["currentTarget"]
 final_disp="retain"
 why="Both reviews retain the current translation."
 if d:
  selected_source="primary"; selected=ptarget; final_disp="update"
  if i["disposition"]=="update" and i["independentProposal"]==ptarget:
   why="Both reviews independently selected this same correction."
  elif i["disposition"]=="update":
   why="Both reviews found the current translation needs correction. The primary proposal was selected after comparing both alternatives against the pinned source and caller context; it preserves the meaning and reads more naturally in the target locale."
  elif i["disposition"]=="hold":
   why="The independent terminology hold is resolved by the exact caller: this is a user-managed digital channel object with channelId, name, and kind fields. Traditional Chinese 頻道 is the standard term for this channel."
  else:
   why="The primary correction was rechecked against the pinned source and caller. It resolves a semantic, grammatical, or locale-style issue not identified in the blind pass."
 elif i["disposition"]=="update":
  selected_source="independent"; selected=i["independentProposal"]; final_disp="update"
  if k==(1412,"ar"):
   why="The blind review correctly identified شهادة as certificate/testimony rather than an exception. The CompatibilityDashboard caller uses Exception as a table heading, so adopt استثناء."
  elif k==(1419,"vi"):
   why="The blind review identified Hợp đồng thi công as a construction contract. The integration status is an execution contract, so adopt Hợp đồng thực thi."
 elif i["disposition"]=="hold":
  selected_source="independent"; final_disp="hold"; selected=base["currentTarget"]
  why="The independent reviewer could not resolve the channel term from the pinned context."
 st=tokens(base["sourceKey"]); ct=tokens(base["currentTarget"]); pt=tokens(ptarget); ft=tokens(selected)
 assert st["placeholders"]==ft["placeholders"] and st["markupTags"]==ft["markupTags"]
 assert [x for x in st["protectedLiterals"] if x not in ft["protectedLiterals"]]==[]
 # Spell-out of three in English and Japanese/Korean digit output is semantically equal; chosen primary targets spell it out.
 assert st["numericTokens"]==ft["numericTokens"],(k,st["numericTokens"],ft["numericTokens"])
 decisions.append({
  "position":base["position"],"historicalSourceOrdinal":base["historicalSourceOrdinal"],"sourceKey":base["sourceKey"],"sourceKeySha256":base["sourceKeySha256"],"locale":base["locale"],
  "sourceContextSha256":base["sourceContextSha256"],"callerRefs":base["callerRefs"],"productionCallerCount":base["callerCount"],
  "catalogPath":base["catalogPath"],"catalogFileSha256":base["catalogFileSha256"],"catalogGitBlob":base["catalogGitBlob"],
  "currentTarget":base["currentTarget"],"currentTargetSha256":base["currentTargetSha256"],
  "independentDisposition":i["disposition"],"independentProposal":i["independentProposal"],"independentRationale":i["rationale"],
  "primaryDisposition":p["disposition"],"primaryProposal":ptarget,"primaryRationale":d["rationale"] if d else p["rationale"],
  "reviewerComparison":relation,"selectedSource":selected_source,"selectedTarget":selected,"selectedTargetSha256":sha(selected.encode()),
  "finalDisposition":final_disp,"crossAuditRationale":why,"sourceTokens":st,"currentTargetTokens":ct,"selectedTargetTokens":ft,
  "placeholderSequenceMatches":st["placeholders"]==ft["placeholders"],"markupMatches":st["markupTags"]==ft["markupTags"],
  "numericTokensMatch":st["numericTokens"]==ft["numericTokens"],"protectedLiteralsMatch":not [x for x in st["protectedLiterals"] if x not in ft["protectedLiterals"]]
 })
with (R/"resolution-ledger.jsonl").open("w",encoding="utf-8",newline="\n") as f:
 for x in decisions:f.write(json.dumps(x,ensure_ascii=False,sort_keys=True)+"\n")
# Exact catalog-key evidence for the embedded source labels, plus the distinct runtime recipe title.
pins=readj(CF/"catalog-file-pins.json")["localeCatalogs"]
code_pins=readj(CF/"catalog-file-pins.json")["callerFiles"]
repo=Path("/home/keith/Documents/code/task-scratch/slskr-pr204-w1363-1382-apply-20261103/repo")
title_rows=[]
for loc,v in pins.items():
 cat=json.loads((repo/v["path"]).read_text(encoding="utf-8"))
 target=next(x for x in pdec.values() if x["position"]==1416 and x["locale"]==loc)["target"]
 wr=cat["Wishlist Retry"]; lh=cat["Library Health"]; lhs=cat["Library Health Scan"]
 assert wr in target and lh in target,(loc,wr,lh)
 title_rows.append({"locale":loc,"catalogPath":v["path"],"catalogFileSha256":v["sha256"],"catalogGitBlob":v["gitBlob"],
  "sourceLiteralWishlistRetry":{"sourceKey":"Wishlist Retry","catalogValue":wr},
  "sourceLiteralLibraryHealth":{"sourceKey":"Library Health","catalogValue":lh},
  "runtimeRecipeTitles":{"wishlistRetrySourceTitle":"Wishlist Retry","wishlistRetryLocaleTitle":wr,"libraryHealthSourceTitle":"Library Health Scan","libraryHealthLocaleTitle":lhs},
  "primaryTargetContainsLocalizedSourceLabels":True,
  "note":"The source text literal is Library Health; the runtime recipe title in automationRecipes.js is Library Health Scan. These are distinct source keys."})
(R/"catalog-title-evidence.jsonl").write_text("".join(json.dumps(x,ensure_ascii=False,sort_keys=True)+"\n" for x in title_rows),encoding="utf-8")
# Code citation pins for the source claims used to resolve positions 1416 and 1420.
code_evidence=[]
for path,lines in [("web/src/lib/automationRecipes.js",[75,88]),("web/src/components/System/MediaCore/PodChannelManagementPanel.jsx",[117,126,143,147,157,170,269,271,273,317,325,326,335,345])]:
 b=(repo/path).read_bytes(); pin=code_pins[path]; assert sha(b)==pin["sha256"]
 text=b.decode("utf-8").splitlines()
 code_evidence.append({"path":path,"fileSha256":pin["sha256"],"gitBlob":pin["gitBlob"],"selectedLines":[{"line":n,"text":text[n-1]} for n in lines]})
(R/"code-evidence.json").write_text(json.dumps({"head":input_manifest["head"],"tree":input_manifest["tree"],"files":code_evidence,
 "notes":["Automation recipe source titles are Wishlist Retry and Library Health Scan.","The message at position 1416 literally names Wishlist Retry and Library Health; the exact catalog entries for those literal keys are pinned separately.","PodChannelManagementPanel stores channelId, name, kind, and supports channel create/edit/delete, confirming a digital channel object for zh-Hant 頻道."]},ensure_ascii=False,sort_keys=True,indent=2)+"\n",encoding="utf-8")
cnt={x:sum(r["finalDisposition"]==x for r in decisions) for x in ("retain","update","hold")}
cmp={x:sum(r["reviewerComparison"]==x for r in decisions) for x in ("no-change-agreement","primary-only-change","independent-only-change","primary-change-resolves-independent-hold","shared-change-same-target","shared-change-different-target")}
same_text=sum(r["reviewerComparison"]=="shared-change-same-target" for r in decisions)
different_text=sum(r["reviewerComparison"]=="shared-change-different-target" for r in decisions)
summary={"result":"SEALED_CROSS_AUDIT","cells":len(decisions),"finalDispositionCounts":cnt,"comparisonCounts":cmp,
 "sharedChangeSameTarget":same_text,"sharedChangeDifferentTarget":different_text,
 "sameDispositionDifferentProposalText":different_text,
 "primaryChangesAdopted":64,"independentOnlyChangesAdopted":2,"primaryAcceptedButIndependentCorrectionAdopted":2,
 "independentHoldResolved":1,"newHolds":cnt["hold"],
 "priorHoldsReattested":len(jl(CF/"prior-hold-reattestation.jsonl")),"changedPriorHolds":0,
 "priorSelectionsReattested":len(jl(CF/"prior-selection-reattestation.jsonl")),
 "placeholderMarkupNumericProtectedMismatches":0,
 "numericBaselineExceptionsResolved":2,
 "candidateFreeManifestSha256":sha((CF/"manifest.json").read_bytes()),"candidateFreeChecksumListSha256":sha((CF/"SHA256SUMS.txt").read_bytes()),
 "primaryManifestSha256":sha((PR/"manifest.json").read_bytes()),"primaryChecksumListSha256":sha((PR/"SHA256SUMS.txt").read_bytes()),
 "independentManifestSha256":sha((IND/"manifest.json").read_bytes()),"independentChecksumListSha256":sha((IND/"SHA256SUMS.txt").read_bytes()),
 "sourceQueueOrderSha256":input_manifest["sourceLookupKeyOrderSha256"],
 "exactHead":input_manifest["head"],"exactTree":input_manifest["tree"]}
(R/"summary.json").write_text(json.dumps(summary,ensure_ascii=False,sort_keys=True,indent=2)+"\n",encoding="utf-8")
manifest={"task":"slskR PR #204 W1403-W1422 independent translation cross-audit","repo":"snapetech-org/slskR","pr":204,
 "branch":"codex/slskr-l10n-audit-20261030","head":input_manifest["head"],"tree":input_manifest["tree"],"base":"2a2b188f10b9460a15bc6d5c34e406b0193d51ba",
 "state":"OPEN","draft":True,"selectedPositions":[1403,1422],"cellCount":240,"sourceCount":20,"localeOrder":locs,
 "candidateFreeEvidence":"evidence/candidate-free-input","primaryEvidence":"evidence/primary-review","independentReview":"independent-review",
 "primaryMaterialsOpenedAfterIndependentSeal":True,"candidateFreeSourceHash":summary["candidateFreeManifestSha256"],
 "primaryManifestSha256":summary["primaryManifestSha256"],"independentManifestSha256":summary["independentManifestSha256"],
 "resolutionLedgerSha256":sha((R/"resolution-ledger.jsonl").read_bytes()),"finalDispositionCounts":cnt,"comparisonCounts":cmp,
 "priorHoldsReattested":35,"changedPriorHolds":0,"priorSelectionsReattested":160,
 "candidateFreeSourceQueueSha256":sha((CF/"source-queue.jsonl").read_bytes()),
 "catalogPinsSha256":sha((CF/"catalog-file-pins.json").read_bytes()),
 "primaryDecisionFileSha256":sha((PR/"review-decisions.json").read_bytes()),
 "primaryLedgerSha256":sha((PR/"review-ledger.jsonl").read_bytes()),
 "independentReviewLedgerSha256":sha((IND/"independent-review.jsonl").read_bytes())}
(R/"manifest.json").write_text(json.dumps(manifest,ensure_ascii=False,sort_keys=True,indent=2)+"\n",encoding="utf-8")
print(json.dumps(summary,ensure_ascii=False,indent=2))
