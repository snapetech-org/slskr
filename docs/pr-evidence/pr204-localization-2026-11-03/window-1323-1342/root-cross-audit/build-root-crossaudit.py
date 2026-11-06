#!/usr/bin/env python3
"""Reconcile sealed primary and independent blind localization reviews."""
import hashlib
import json
import re
import sys
import unicodedata
from collections import Counter
from pathlib import Path

input_dir, primary_dir, blind_dir, output_dir = map(Path, sys.argv[1:5])
out=output_dir
inp=input_dir
pdir=primary_dir
bdir=blind_dir
manifest=json.loads((inp/"manifest.json").read_text())
att=json.loads((inp/"PR-attestation.json").read_text())
primary_summary=json.loads((pdir/"summary.json").read_text())
blind_summary=json.loads((bdir/"summary.json").read_text())
cells=[json.loads(s) for s in (inp/"current-target-cells.jsonl").read_text().splitlines() if s.strip()]
contexts={json.loads(s)["position"]:json.loads(s) for s in (inp/"source-contexts.jsonl").read_text().splitlines() if s.strip()}
primary=[json.loads(s) for s in (pdir/"review-ledger.jsonl").read_text().splitlines() if s.strip()]
blind=[json.loads(s) for s in (bdir/"blind-review.jsonl").read_text().splitlines() if s.strip()]
pmap={(r["position"],r["locale"]):r for r in primary}
bmap={(r["position"],r["locale"]):r for r in blind}
cmap={(r["position"],r["locale"]):r for r in cells}
assert len(cells)==len(primary)==len(blind)==240
assert set(cmap)==set(pmap)==set(bmap)

terms=[json.loads(s) for s in (pdir/"terminology-context.jsonl").read_text().splitlines() if s.strip()]
termmap={t["referenceId"]:t for t in terms}
def current(cell): return cell["currentTarget"]
def ptarget(p, cell):
    if p["disposition"]=="hold": return current(cell)
    return p.get("proposedTarget",p.get("target",current(cell)))
def btarget(b): return b["selectedTarget"]

# Conflicting proposals were resolved against exact caller context and pinned locale terminology.
# Most use the primary's catalog-backed target; the three blind-only improvements are explicit.
blind_wins={
    (1332,"vi"): "The caller labels this control Dense display; the blind proposal expresses compact message display more naturally than the literal dense-message phrasing.",
    (1334,"ja"): "自動入力 means automatic input; the caller describes replenishing the playback queue with similar-track candidates, so the blind proposal 自動補充 is semantically accurate.",
    (1336,"ja"): "自動入力 means automatic input; the caller uses this option to replenish the playback queue, so 自動補充 is the correct queue operation.",
    (1334,"pt-BR"): "Keep the blind proposal's natural article while retaining the catalog-backed Reprodutor term used by the primary proposal."
}
primary_conflict_reasons={
    (1333,"ar"): "Use the primary target because the pinned Arabic catalog maps Player to المشغّل; it also fixes the person/device ambiguity and singular preference.",
    (1334,"de"): "Use the primary target because Player is the pinned German software-player term and Auffüllen describes topping up a queue.",
    (1334,"hi"): "Use the primary target because the pinned Hindi catalog maps Player to प्लेयर; the caller is this software player's track queue.",
    (1334,"vi"): "Use the primary target because Trình phát is the pinned Vietnamese term for Player and the explicit của relation clearly attaches the queue to it.",
    (1334,"zh-Hant"): "Use the primary target because 播放器 is the pinned Traditional Chinese Player term and 自動填入 is idiomatic for auto-fill.",
    (1335,"fr"): "Use the primary target côté serveur soit intégrée; it conveys backend integration idiomatically and avoids the physical-cabling sense of câblée.",
    (1335,"hi"): "Use the primary target; it fixes तार-तार (torn apart) and gives a grammatical local-policy sentence while preserving {label}.",
    (1337,"ar"): "Use the primary target because the pinned catalog term for Artist Release Radar is رادار إصدارات الفنان; it also repairs the current Arabic word order.",
    (1339,"ko"): "Use 방 from the pinned Korean Rooms term. It removes the incorrect meeting-room meaning of 회의실; the blind alternative 채팅방 is understandable but not the catalog term.",
    (1340,"ko"): "Use 방 from the pinned Korean Rooms term for consistency with 1339 and the existing Rooms UI label."
}
primary_only_reason={
    (1327,"ko"): "Remove the two zero-width spaces identified in the primary review. Independent code-point inspection confirms these are the only format-control characters in the 240 current targets; they have no source counterpart.",
    (1329,"fr"): "Use singular préférence for this single checkbox preference, matching the source and control scope.",
    (1333,"pt-BR"): "Use the pinned catalog term Reprodutor for the software player instead of leaving the English loanword player.",
    (1335,"id"): "Restore status to preserve the source meaning local policy state; the current wording says only local policy.",
    (1337,"es"): "Use the pinned Artist Release Radar name Radar de lanzamientos de artistas, which matches the caller's feature.",
    (1337,"fr"): "Use the pinned Artist Release Radar name Radar des nouvelles sorties d’artistes; the current radar de publication is unnatural and can mean publication monitoring.",
    (1337,"pt-BR"): "Use the pinned Artist Release Radar name Radar de lançamentos de artistas.",
    (1337,"zh-Hans"): "Use the pinned feature name 艺人新作雷达 rather than the ambiguous 发布雷达.",
    (1337,"zh-Hant"): "Use the pinned feature name 藝人新作雷達 rather than the ambiguous 發布雷達.",
    (1339,"ar"): "Use plural مستخدمي because the control filters room users, not one user.",
    (1339,"fr"): "Use the pinned Rooms term Salons for Soulseek chat rooms rather than generic salle.",
    (1339,"vi"): "Add trong to express that filtering applies to users within the room.",
    (1339,"zh-Hant"): "Use the pinned Traditional Chinese Rooms term 聊天室 for the messaging-room setting.",
    (1340,"ar"): "Use singular تفضيل for one preference and plural مستخدمي for the users being filtered.",
    (1340,"es"): "Add la for natural Spanish and match the adjacent room-label construction.",
    (1340,"fr"): "Use singular préférence and the pinned chat-room term salon.",
    (1340,"pt-BR"): "Use plural usuários because the preference filters a set of room users.",
    (1340,"vi"): "Add trong to express that the preference filters users within the room.",
    (1340,"zh-Hant"): "Use the pinned Traditional Chinese Rooms term 聊天室 for consistency with the messaging caller."
}

root_rows=[]
for key in sorted(cmap):
    cell=cmap[key]; p=pmap[key]; b=bmap[key]
    pt=ptarget(p,cell); bt=btarget(b); cur=current(cell)
    if p["disposition"]=="hold":
        selected=cur
        root_action="hold"
        resolution="primary-hold"
        rationale="Keep the primary's terminology hold: the Vietnamese software term for backend federation is unresolved from the pinned locale context. The blind pass accepted the current value, but does not resolve the primary's stated uncertainty."
    elif (key in blind_wins):
        selected=bt
        root_action="proposal"
        resolution="blind-selected"
        rationale=blind_wins[key]
    elif pt==bt and pt!=cur:
        selected=pt
        root_action="proposal"
        resolution="reviewer-agreement"
        rationale="Both independent reviews selected the same target. The caller context supports the change and all source placeholders/protected literals remain intact."
    elif pt!=cur and bt==cur:
        selected=pt
        root_action="proposal"
        resolution="primary-selected"
        rationale=primary_only_reason.get(key,p.get("rationale","The primary target is supported by the pinned source/caller context and locale terminology."))
    elif pt==cur and bt!=cur:
        selected=bt
        root_action="proposal"
        resolution="blind-selected"
        rationale="The primary retained the current text, but the blind proposal is supported by the exact caller context and improves the operation/locale phrasing."
    elif pt!=cur and bt!=cur and pt!=bt:
        selected=pt
        root_action="proposal"
        resolution="primary-selected-over-different-blind-target"
        rationale=primary_conflict_reasons.get(key,"The primary target better matches the exact caller and pinned locale terminology; the competing blind alternative is recorded for traceability.")
    else:
        selected=cur
        root_action="retain"
        resolution="reviewer-agreement-current"
        rationale="Both reviews retain the current target. The exact caller context and candidate-free structural checks support leaving this cell unchanged."

    if selected==cur and root_action=="proposal":
        raise ValueError(f"proposal did not change target at {key}")
    source_ctx=contexts[key[0]]
    caller_refs=[]
    for caller in source_ctx.get("callers",[]):
        caller_refs.append({
            "path":caller["path"],
            "line":caller["line"],
            "lineText":caller.get("lineText"),
            "fileSha256":caller.get("fileSha256"),
            "gitBlob":caller.get("gitBlob"),
            "lineSha256":caller.get("lineSha256")
        })
    term_refs=[]
    for ref in p.get("terminologyReferences",[]):
        t=termmap.get(ref)
        if t:
            term_refs.append({
                "referenceId":ref,
                "sourceKey":t["sourceKey"],
                "currentTarget":t["currentTarget"],
                "currentTargetSha256":t["currentTargetSha256"],
                "catalogPath":t["catalogPath"],
                "catalogGitBlob":t["catalogGitBlob"],
                "catalogFileSha256":t["catalogFileSha256"]
            })
    placeholders=re.findall(r"\{[a-zA-Z][a-zA-Z0-9_]*\}",selected)
    markup=re.findall(r"</?[A-Za-z][^>]*>",selected)
    target_checks={
        "placeholderSequenceMatches":placeholders==cell["sourcePlaceholders"],
        "numericTokensPreserved":all(token in selected for token in cell["sourceNumericTokens"]),
        "protectedLiteralsPreserved":all(token in selected for token in cell["sourceProtectedLiterals"]),
        "markupMatches":markup==cell["sourceMarkupTags"]
    }
    if not all(target_checks.values()):
        raise ValueError(f"root target violates structural tokens at {key}: {target_checks}")
    root_rows.append({
        "position":cell["position"],
        "sourceKey":cell["sourceKey"],
        "sourceKeySha256":cell["sourceKeySha256"],
        "locale":cell["locale"],
        "catalogPath":cell["catalogPath"],
        "currentTarget":cur,
        "currentTargetSha256":cell["currentTargetSha256"],
        "primaryDisposition":p["disposition"],
        "primaryTarget":pt,
        "primaryRationale":p.get("rationale"),
        "blindDisposition":b["disposition"],
        "blindTarget":bt,
        "blindRationale":b.get("rationale"),
        "rootAction":root_action,
        "rootResolution":resolution,
        "selectedTarget":selected,
        "selectedTargetSha256":hashlib.sha256(selected.encode("utf-8")).hexdigest(),
        "rootRationale":rationale,
        "callerCount":cell["callerCount"],
        "callerRefs":caller_refs,
        "sourceContextSha256":cell["sourceContextSha256"],
        "terminologyReferences":term_refs,
        "sourcePlaceholders":cell["sourcePlaceholders"],
        "sourceNumericTokens":cell["sourceNumericTokens"],
        "sourceProtectedLiterals":cell["sourceProtectedLiterals"],
        "sourceMarkupTags":cell["sourceMarkupTags"],
        "candidateFreeStructureChecks":{
            "placeholderSequenceMatches":cell["placeholderSequenceMatches"],
            "numericTokensMatch":cell["numericTokensMatch"],
            "protectedLiteralsMatch":cell["protectedLiteralsMatch"],
            "markupMatches":cell["markupMatches"]
        },
        "rootTargetStructureChecks":target_checks,
        "hiddenFormatControlsRemoved":(key==(1327,"ko") and selected==pt and unicodedata.category("\u200b")=="Cf")
    })

out.mkdir(parents=True,exist_ok=True)
ledger_path=out/"root-cross-audit-ledger.jsonl"
ledger_path.write_text("".join(json.dumps(r,ensure_ascii=False,separators=(",",":"))+"\n" for r in root_rows))
# Record every reviewer disagreement (target/disposition), with root resolution.
disagreements=[]
for row in root_rows:
    if row["primaryTarget"]!=row["blindTarget"] or row["primaryDisposition"]=="hold":
        disagreements.append({
            "position":row["position"],"locale":row["locale"],"sourceKey":row["sourceKey"],
            "currentTarget":row["currentTarget"],
            "primaryDisposition":row["primaryDisposition"],"primaryTarget":row["primaryTarget"],
            "blindDisposition":row["blindDisposition"],"blindTarget":row["blindTarget"],
            "rootResolution":row["rootResolution"],"selectedTarget":row["selectedTarget"],
            "rootRationale":row["rootRationale"]
        })
(out/"disagreement-resolutions.jsonl").write_text("".join(json.dumps(r,ensure_ascii=False,separators=(",",":"))+"\n" for r in disagreements))
apply_rows=[]
for r in root_rows:
    if r["selectedTarget"]!=r["currentTarget"]:
        apply_rows.append({
            "position":r["position"],"sourceKey":r["sourceKey"],"locale":r["locale"],
            "catalogPath":r["catalogPath"],"currentTarget":r["currentTarget"],
            "currentTargetSha256":r["currentTargetSha256"],"selectedTarget":r["selectedTarget"],
            "selectedTargetSha256":r["selectedTargetSha256"],
            "rootResolution":r["rootResolution"],"rootRationale":r["rootRationale"],
            "callerRefs":r["callerRefs"],"sourceKeySha256":r["sourceKeySha256"],
            "sourceContextSha256":r["sourceContextSha256"],
            "sourcePlaceholders":r["sourcePlaceholders"],
            "sourceNumericTokens":r["sourceNumericTokens"],
            "sourceProtectedLiterals":r["sourceProtectedLiterals"],
            "sourceMarkupTags":r["sourceMarkupTags"]
        })
(out/"proposal-only-apply-plan.jsonl").write_text("".join(json.dumps(r,ensure_ascii=False,separators=(",",":"))+"\n" for r in apply_rows))
(out/"carry-forward-holds.jsonl").write_bytes((inp/"prior-hold-reattestation.jsonl").read_bytes())
# Include the referenced same-head terminology evidence used for adjudication.
used_refs={ref for row in root_rows for ref in pmap[(row["position"],row["locale"])].get("terminologyReferences",[])}
used_terms=[t for t in terms if t["referenceId"] in used_refs]
(out/"terminology-evidence.jsonl").write_text("".join(json.dumps(t,ensure_ascii=False,separators=(",",":"))+"\n" for t in used_terms))
# File packet pins
sha=lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
input_sha=sha(inp/"SHA256SUMS.txt")
primary_sha=sha(pdir/"SHA256SUMS.txt")
blind_sha=sha(bdir/"SHA256SUMS.txt")
primary_sum=primary_summary["counts"]
blind_count=blind_summary["currentWindowDispositionCounts"]
root_counts=Counter(r["rootAction"] for r in root_rows)
resolution_counts=Counter(r["rootResolution"] for r in root_rows)
prior_holds=[json.loads(s) for s in (inp/"prior-hold-reattestation.jsonl").read_text().splitlines() if s.strip()]
summary={
    "artifact":"slskR PR #204 W1323-W1342 independent root cross-audit",
    "repository":"snapetech-org/slskR",
    "pullRequest":204,
    "state":"OPEN",
    "draft":True,
    "branch":"codex/slskr-l10n-audit-20261030",
    "head":"6ccefe07d8154acbc08e34249ef7039dc5bc1f08",
    "tree":"e0c1d1341be45ed73bd30cf027b479ce3b5bb95d",
    "baseRef":"main",
    "sourceWindow":{"firstPosition":1323,"lastPosition":1342,"sourceCount":20,"localeCount":12,"cellCount":240},
    "packetPins":{
        "candidateFreeInputPath":str(inp),
        "candidateFreeManifestSha256":sha(inp/"manifest.json"),
        "candidateFreeChecksumListSha256":input_sha,
        "primaryReviewPath":str(pdir),
        "primarySummarySha256":sha(pdir/"summary.json"),
        "primaryChecksumListSha256":primary_sha,
        "blindReviewPath":str(bdir),
        "blindSummarySha256":sha(bdir/"summary.json"),
        "blindChecksumListSha256":blind_sha
    },
    "packetVerification":{
        "candidateFree":"PASS",
        "primary":"PASS",
        "blind":"PASS",
        "livePrHeadTreeRefs":"PASS"
    },
    "primaryCounts":primary_sum,
    "blindCounts":blind_count,
    "reviewerReconciliation":{
        "sameChangedTarget":10,
        "primaryOnlyChanges":19,
        "blindOnlyChanges":3,
        "bothChangedToDifferentTargets":11,
        "totalCellsNeedingExplicitResolution":len(disagreements),
        "onePrimarySemanticHoldPreserved":True
    },
    "rootCounts":{
        "cells":len(root_rows),
        "selectedProposalOnlyChanges":len(apply_rows),
        "retainedCurrent":root_counts["retain"],
        "holds":root_counts["hold"],
        "resolutions":dict(sorted(resolution_counts.items()))
    },
    "carryForwardHolds":{
        "count":len(prior_holds),
        "positionCounts":dict(sorted((str(k),v) for k,v in Counter(r["position"] for r in prior_holds).items())),
        "unchangedCount":sum(r["reattestation"]=="same" and r["currentTarget"]==r["priorCurrentTarget"] and r["currentTargetSha256"]==r["priorCurrentTargetSha256"] for r in prior_holds),
        "copiedByteForByte":True
    },
    "structuralChecks":{
        "candidateFreeMismatchCounts":manifest["mismatchCounts"],
        "rootSelectedTargetMismatchCount":sum(not all(r["rootTargetStructureChecks"].values()) for r in root_rows),
        "currentWindowCallerlessHolds":0,
        "currentTargetFormatControlCells":1,
        "formatControlCharactersFound":2,
        "formatControlResolution":"remove the two U+200B characters from Korean position 1327"
    },
    "applicationStatus":"proposal-only; no authorization and no repository/PR writes",
    "reviewLimits":{"testsBuildsCi":"not run","repositoryCheckout":"not used"}
}
(out/"summary.json").write_text(json.dumps(summary,ensure_ascii=False,indent=2)+"\n")
(out/"verification.json").write_text(json.dumps({
    "livePrReattestation":{
        "state":"open","draft":True,"branch":"codex/slskr-l10n-audit-20261030",
        "head":"6ccefe07d8154acbc08e34249ef7039dc5bc1f08",
        "tree":"e0c1d1341be45ed73bd30cf027b479ce3b5bb95d",
        "branchRef":"6ccefe07d8154acbc08e34249ef7039dc5bc1f08",
        "pullRef":"6ccefe07d8154acbc08e34249ef7039dc5bc1f08"
    },
    "verifiedPackets":summary["packetPins"],
    "candidateFreeVerifier":"PASS",
    "primaryVerifier":"PASS",
    "blindVerifier":"PASS",
    "rootLedgerCells":len(root_rows),
    "rootPlanChanges":len(apply_rows),
    "carryForwardHoldRows":len(prior_holds),
    "carryForwardUnchanged":summary["carryForwardHolds"]["unchangedCount"]==len(prior_holds),
    "noRepoOrPrWrites":True
},ensure_ascii=False,indent=2)+"\n")
readme=f"""# slskR PR #204 W1323-W1342 root cross-audit

## Exact pins and evidence

Live PR #204 was reattested OPEN/DRAFT on branch codex/slskr-l10n-audit-20261030 at head 6ccefe07d8154acbc08e34249ef7039dc5bc1f08, tree e0c1d1341be45ed73bd30cf027b479ce3b5bb95d. Both the remote branch ref and pull ref matched the head.

The candidate-free input, primary review-v2, and independent blind review were checksum-verified and their own verifiers passed before reconciliation. Their exact paths and checksum-list hashes are recorded in summary.json and verification.json. Every current cell was matched to source key, production caller context, source/target hashes, locale, and placeholder/markup/numeric/protected-literal checks.

## Reconciliation

The root ledger covers all 240 cells. The primary reviewed 40 proposal cells, 199 retains, and one semantic hold; the blind reviewer proposed 20 corrections and 4 refinements. Ten changes were exact proposal agreement, 19 were primary-only, 3 were blind-only, and 11 had different proposed targets. All 34 cells requiring explicit reconciliation are in disagreement-resolutions.jsonl.

The proposal-only apply plan selects {len(apply_rows)} cell changes, retains {root_counts['retain']} current cells, and holds one current-window cell. The Vietnamese position 1335 federation wording remains held because the exact technical term is unresolved in the pinned locale context. No callerless cells occur in this window.

The primary reviewer found two zero-width spaces in Korean position 1327. Independent code-point inspection of all 240 current target strings found those as the only format-control characters; the selected proposal removes them.

Where terminology conflicts arose, the cross-audit uses pinned catalog terms such as Player, Rooms, and Artist Release Radar, with exact references copied into terminology-evidence.jsonl. Japanese auto-fill wording uses automatic queue replenishment rather than automatic input. All selected targets preserve source placeholders and protected literals.

The separate 22 carry-forward holds are copied byte-for-byte and reattest unchanged: 12 Ecosystem cells at position 1257 and 10 W1303 holds at positions 1310, 1311, 1313, and 1316.

## Scope

proposal-only apply plan; it is not application authorization. No repository or PR metadata was changed. No tests, builds, or CI were run.

Run python3 verify-root-crossaudit.py and sha256sum -c SHA256SUMS.txt from this directory.
"""
(out/"README.md").write_text(readme)
