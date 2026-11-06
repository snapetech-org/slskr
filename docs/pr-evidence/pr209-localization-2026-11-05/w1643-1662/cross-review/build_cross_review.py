#!/usr/bin/env python3
"""Build independent cross-review adjudication for slskR PR #209 W1643-W1662."""
from __future__ import annotations
import hashlib, json, re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

OUT = Path(__file__).resolve().parent
TASK = OUT.parent
INPUT = TASK / "candidate-free-input"
PRIMARY = TASK / "primary-review"
BLIND = TASK / "blind-review"
HEAD = "2d804c49879372071adf606bc2a2cf51e261fd94"
TREE = "d6f5552d2400d868c2f2af98eb68caadfd4f3f66"
REPO = "snapetech-org/slskR"
PR = 209
BRANCH = "codex/slskr-l10n-audit-20261104-resync"
LOCALES = ["es", "zh-Hans", "hi", "de", "ja", "fr", "pt-BR", "ar", "ko", "zh-Hant", "vi", "id"]

FINAL = {
    (1643, "ko"): ("correction", "메타데이터를 가져오지 못했습니다:", "The current verb means search, but this source and caller mean retrieval. The caller appends the raw Pod error, so the colon must continue the visible prefix.", "high"),
    (1646, "zh-Hant"): ("refinement", "無法路由訊息。", "消息 can mean message, but this Traditional Chinese catalog uses 訊息 in adjacent message-routing and message-search strings. The proposed term improves locale consistency without changing the basic meaning.", "moderate"),
    (1647, "fr"): ("refinement", "Échec du routage du message :", "Acheminement can mean routing or delivery, so the current wording is defensible. The exact caller is a Pod message-routing result, and the sibling route-message key uses routage; the proposal makes the technical action consistent and keeps the appended-error colon.", "moderate"),
    (1647, "pt-BR"): ("refinement", "Falha ao rotear a mensagem:", "Encaminhar can mean forwarding, while this PodMessageRoutingPanel reports a routing operation and the sibling route-message key uses rotear. The proposal aligns the specific technical action and retains the detail separator.", "moderate"),
    (1649, "hi"): ("correction", "खतरों से सुरक्षा की सेटिंग सहेजी नहीं जा सकीं", "प्रतिकूल means adverse or unfavorable in this wording. The feature is adversarial threat protection, and this same Hindi catalog renders Adversarial Settings as खतरों से सुरक्षा की सेटिंग, so the save error should use that established feature name.", "moderate"),
    (1654, "zh-Hant"): ("correction", "無法儲存來源訂閱整合設定。", "來源摘要 means source summary, not a source feed. This caller saves provider settings for Spotify, YouTube, and Last.fm feed imports; 訂閱 preserves the feed/subscription meaning and aligns with Simplified Chinese.", "high"),
    (1661, "ar"): ("correction", "تعذر اختيار النسخة المعيارية.", "The current النسخة الأساسية means basic/base version and تحديد means determine, while the source means select a canonical variant. المعيارية is a closer technical description of a canonical/standardized representative; the allowlist caller provides no narrower algorithm meaning.", "moderate"),
    (1661, "ja"): ("refinement", "正準バリアントを選択できませんでした。", "標準バリアント is understandable as a standard variant, but canonical has a precise technical equivalent 正準. The official Unicode Japanese terminology uses 正準 for Canonical; this is a terminology refinement because the allowlist caller does not expose the selection algorithm.", "moderate"),
    (1661, "ko"): ("refinement", "정규 변형을 선택하지 못했습니다.", "표준 변형 is understandable as standard variant. 정규 is also an established Korean technical equivalent for canonical form; prefer it for this technical key, while keeping moderate confidence because the allowlist caller lacks algorithm detail.", "moderate"),
}

MEANING = {
    1643: "Retrieve metadata; the colon form precedes an appended error detail.",
    1644: "Retrieve Pod metadata.",
    1645: "Retrieve user information.",
    1646: "Route a message.",
    1647: "Route a message and append the routing error detail.",
    1648: "Save FTP integration settings.",
    1649: "Save adversarial threat-protection settings.",
    1650: "Save bridge configuration.",
    1651: "Save metadata integration settings.",
    1652: "Save notification integration settings.",
    1653: "Save policy settings.",
    1654: "Save source-feed integration settings.",
    1655: "Save a user note.",
    1656: "Search content.",
    1657: "Search content and display the error placeholder.",
    1658: "Search library items.",
    1659: "Search messages.",
    1660: "Search messages and display the error placeholder.",
    1661: "Select a canonical variant.",
    1662: "Send a batch message to multiple recipients.",
}

def sha(data):
    if isinstance(data, str): data = data.encode("utf-8")
    return hashlib.sha256(data).hexdigest()

def canon(obj):
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"))

def readjl(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]

def writejl(path, rows):
    path.write_text("".join(canon(row) + "\n" for row in rows), encoding="utf-8")

def token_signature(text):
    placeholders = re.findall(r"\{[A-Za-z][A-Za-z0-9_]*\}", text)
    markup = re.findall(r"</?[A-Za-z][^>]*>", text)
    numeric = re.findall(r"(?<![A-Za-z])\d+(?:[.,]\d+)?%?(?![A-Za-z])", text)
    protected = []
    for value in re.findall(r"(?<![A-Za-z0-9])(?:[A-Z]{2,}[A-Z0-9]*|ffmpeg|Chromaprint|Soulseek|Spotify|YouTube|Pushbullet|Matrix|WebSocket|OpenAI)(?![A-Za-z0-9])", text):
        if value not in protected: protected.append(value)
    return {"placeholders": placeholders, "markupTags": markup, "numericTokens": numeric, "protectedLiterals": protected}

def main():
    cfm = json.loads((INPUT / "manifest.json").read_text(encoding="utf-8"))
    pm = json.loads((PRIMARY / "manifest.json").read_text(encoding="utf-8"))
    bm = json.loads((BLIND / "manifest.json").read_text(encoding="utf-8"))
    for m, label in ((cfm, "candidate-free"), (pm, "primary")):
        if m.get("head") != HEAD or m.get("tree") != TREE: raise SystemExit(f"{label} pin mismatch")
    if bm.get("exactHead") != HEAD or bm.get("exactTree") != TREE: raise SystemExit("blind pin mismatch")

    current_path = INPUT / "current-target-cells.jsonl"
    current_raw = current_path.read_bytes().splitlines()
    current = [json.loads(line) for line in current_raw if line.strip()]
    rowhash = { (r["position"], r["locale"]): sha(line) for r, line in zip(current, [x for x in current_raw if x.strip()]) }
    contexts = {r["position"]: r for r in readjl(INPUT / "source-contexts.jsonl")}
    primary_rows = {(r["position"], r["locale"]): r for r in readjl(PRIMARY / "primary-ledger.jsonl")}
    primary_proposals = {(r["position"], r["locale"]): r for r in readjl(PRIMARY / "proposals.jsonl")}
    blind_rows = {(r["selectedPosition"], r["locale"]): r for r in readjl(BLIND / "ledger.jsonl")}
    blind_proposals = {(r["selectedPosition"], r["locale"]): r for r in readjl(BLIND / "proposals.jsonl")}
    holds = readjl(INPUT / "caller-resolution-holds.jsonl")
    if len(current) != 240 or len(contexts) != 20 or len(primary_rows) != 240 or len(blind_rows) != 240 or holds:
        raise SystemExit("input review coverage or callerless-hold mismatch")

    ledger, final_proposals, disagreement_rows = [], [], []
    for c in current:
        pos, loc = c["position"], c["locale"]
        key = (pos, loc)
        ctx = contexts[pos]
        p = primary_rows[key]
        b = blind_rows[key]
        pp = primary_proposals.get(key)
        bp = blind_proposals.get(key)
        if c["sourceKey"] != ctx["sourceKey"] or c["sourceContextSha256"] != ctx["callerContextSha256"]:
            raise SystemExit(f"candidate-free source/context mismatch: {key}")
        if p["sourceKeySha256"] != c["sourceKeySha256"] or p["currentTargetSha256"] != c["currentTargetSha256"] or p["sourceContextSha256"] != ctx["callerContextSha256"]:
            raise SystemExit(f"primary binding mismatch: {key}")
        if b["sourceTextSha256"] != c["sourceKeySha256"] or b["currentTargetSha256"] != c["currentTargetSha256"] or b["sourceContextSha256"] != ctx["callerContextSha256"] or b["candidateFreeRowSha256"] != rowhash[key]:
            raise SystemExit(f"blind binding mismatch: {key}")
        if b["sourceText"] != c["sourceKey"] or b["currentTarget"] != c["currentTarget"] or p["currentTarget"] != c["currentTarget"]:
            raise SystemExit(f"input target/source text mismatch: {key}")
        if p["callerOccurrenceCount"] != b["callerCount"] or b["callerCount"] != ctx["callerOccurrenceCount"]:
            raise SystemExit(f"caller count mismatch: {key}")
        if not ctx["callers"]:
            raise SystemExit(f"callerless cell is not represented as a hold: {key}")
        if pp and (pp["currentTargetSha256"] != c["currentTargetSha256"] or pp["sourceContextSha256"] != ctx["callerContextSha256"]):
            raise SystemExit(f"primary proposal binding mismatch: {key}")
        if bp and (bp["currentTargetSha256"] != c["currentTargetSha256"] or bp["sourceContextSha256"] != ctx["callerContextSha256"] or bp["candidateFreeRowSha256"] != rowhash[key]):
            raise SystemExit(f"blind proposal binding mismatch: {key}")

        incoming_p = {"decision": p["decision"], "rationale": p["rationale"], "confidence": p["confidence"],
                      "recommendedTarget": pp["recommendedTarget"] if pp else None,
                      "recommendedTargetSha256": pp["recommendedTargetSha256"] if pp else None}
        incoming_b = {"decision": b["decision"], "rationale": b["rationale"], "confidence": b["confidence"],
                      "recommendedTarget": bp["recommendedTarget"] if bp else None,
                      "recommendedTargetSha256": bp["recommendedTargetSha256"] if bp else None}
        disagreement = (incoming_p["decision"] != incoming_b["decision"] or incoming_p["recommendedTarget"] != incoming_b["recommendedTarget"])
        final = FINAL.get(key)
        if final:
            disposition, target, rationale, confidence = final
            target_hash = sha(target)
            if token_signature(target) != token_signature(c["sourceKey"]):
                raise SystemExit(f"final target token signature mismatch: {key}")
            final_proposals.append({
                "rowId": f"W1643-W1662:{pos}:{loc}", "position": pos, "locale": loc,
                "sourceKey": c["sourceKey"], "sourceKeySha256": c["sourceKeySha256"],
                "currentTarget": c["currentTarget"], "currentTargetSha256": c["currentTargetSha256"],
                "recommendedTarget": target, "recommendedTargetSha256": target_hash,
                "sourceContextSha256": ctx["callerContextSha256"],
                "callerReferences": [{"path": x["path"], "line": x["line"], "lineSha256": x["lineSha256"], "contextSha256": x["contextSha256"], "literalOccurrenceCount": x["literalOccurrenceCount"]} for x in ctx["callers"]],
                "disposition": disposition, "rationale": rationale, "confidence": confidence,
                "applyReady": True, "primaryTarget": incoming_p["recommendedTarget"], "blindTarget": incoming_b["recommendedTarget"],
            })
        else:
            disposition, target, rationale, confidence, target_hash = "retain-current", None, f"{MEANING[pos]} Independent comparison of the source, exact caller context, and current localized text found the action/failure understandable with no material mistranslation. The selected row has resolved callers and passes all token checks.", "moderate", None

        if disagreement:
            disagreement_rows.append({
                "rowId": f"W1643-W1662:{pos}:{loc}", "position": pos, "locale": loc,
                "sourceKeySha256": c["sourceKeySha256"], "currentTargetSha256": c["currentTargetSha256"],
                "sourceContextSha256": ctx["callerContextSha256"],
                "primary": incoming_p, "blind": incoming_b,
                "crossDisposition": disposition, "crossRecommendedTarget": target,
                "crossRationale": rationale, "confidence": confidence,
            })

        source_sig = {"placeholders": c["sourcePlaceholders"], "markupTags": c["sourceMarkupTags"], "numericTokens": c["sourceNumericTokens"], "protectedLiterals": c["sourceProtectedLiterals"]}
        current_sig = token_signature(c["currentTarget"])
        final_target = target if target is not None else c["currentTarget"]
        final_sig = token_signature(final_target)
        if source_sig != current_sig or source_sig != final_sig:
            raise SystemExit(f"source/current/final token mismatch: {key}")
        refs = [{"path": x["path"], "line": x["line"], "lineSha256": x["lineSha256"], "contextSha256": x["contextSha256"], "literalOccurrenceCount": x["literalOccurrenceCount"]} for x in ctx["callers"]]
        ledger.append({
            "rowId": f"W1643-W1662:{pos}:{loc}", "window": "W1643-W1662",
            "position": pos, "locale": loc, "sourceKey": c["sourceKey"],
            "sourceKeySha256": c["sourceKeySha256"], "candidateFreeRowSha256": rowhash[key],
            "currentTarget": c["currentTarget"], "currentTargetSha256": c["currentTargetSha256"],
            "sourceContextSha256": ctx["callerContextSha256"], "callerOccurrenceCount": ctx["callerOccurrenceCount"],
            "callerReferences": refs, "catalogPath": c["catalogPath"],
            "catalogFileSha256": c["catalogFileSha256"], "catalogGitBlob": c["catalogGitBlob"],
            "primaryReview": incoming_p, "blindReview": incoming_b,
            "reviewerDisagreement": disagreement,
            "disagreementKind": "one-reviewer-proposed" if disagreement else ("both-proposed-same-target" if pp and bp else "both-accepted-current"),
            "crossDisposition": disposition, "crossRecommendedTarget": target,
            "crossRecommendedTargetSha256": target_hash, "crossRationale": rationale,
            "confidence": confidence, "applyReady": bool(final),
            "sourceTokenSignature": source_sig, "currentTokenSignature": current_sig,
            "crossTargetTokenSignature": final_sig, "tokenPreservation": "PASS",
            "callerlessHold": False,
        })

    if len(ledger) != 240 or len(final_proposals) != len(FINAL) or len(disagreement_rows) != 7:
        raise SystemExit("cross-review coverage, proposal union, or disagreement count mismatch")
    writejl(OUT / "cross-ledger.jsonl", ledger)
    writejl(OUT / "recommendations.jsonl", final_proposals)
    writejl(OUT / "proposal-disagreements.jsonl", disagreement_rows)
    (OUT / "holds-hash-only.jsonl").write_text("", encoding="utf-8")

    ext = {
        "capturedAtUtc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "sources": [
            {"title": "Unicode Terminology: English-Japanese", "url": "https://www.unicode.org/terminology/term_en_ja.html", "supports": "Canonical → 正準; used to assess the Japanese refinement at 1661.", "sourceType": "primary standards terminology"},
            {"title": "Korean National Institute of Korean Language term entry: 정규형", "url": "https://kli.korean.go.kr/term/trgtWord/indexTrgtWord.do?trgtWordNo=2442583", "supports": "Lists canonical form as the English equivalent of 정규형 and lists 표준형 as a synonym; supports 정규 as a technical alternative while keeping the change a moderate-confidence refinement.", "sourceType": "national terminology entry"},
        ],
        "caution": "External terminology sources inform only the canonical-variant term choices. They do not provide native-speaker or product-specific algorithm review.",
    }
    (OUT / "external-terminology-notes.json").write_text(json.dumps(ext, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    input_att = {
        "repository": REPO, "pullRequest": PR, "head": HEAD, "tree": TREE,
        "headRef": BRANCH, "baseRef": "main", "baseSha": "1bbaec9fdc63a86de343e37e33bae70d44301a36",
        "candidateFreeManifestSha256": sha((INPUT / "manifest.json").read_bytes()),
        "candidateFreeChecksumIndexSha256": sha((INPUT / "SHA256SUMS.txt").read_bytes()),
        "primaryManifestSha256": sha((PRIMARY / "manifest.json").read_bytes()),
        "primaryChecksumIndexSha256": sha((PRIMARY / "SHA256SUMS.txt").read_bytes()),
        "blindManifestSha256": sha((BLIND / "manifest.json").read_bytes()),
        "blindChecksumIndexSha256": sha((BLIND / "SHA256SUMS.txt").read_bytes()),
        "candidateFreeRows": len(current), "primaryRows": len(primary_rows), "blindRows": len(blind_rows),
        "callerlessPositions": cfm["callerResolutionHoldPositions"],
        "priorSelectionsReattested": cfm["priorSelectionReattestationCount"],
        "priorWindowHashesReattested": cfm["priorWindowHashRecordCount"],
        "priorHoldsUnchanged": cfm["carryForwardHoldUnchangedCount"],
        "priorAppliedTargetHashes": cfm["priorAppliedTargetHashCount"],
        "W1623AppliedCells": 13, "W1623RetainedCells": 227,
        "allCurrentSourceCallerBindings": "PASS",
    }
    (OUT / "input-attestation.json").write_text(json.dumps(input_att, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    verifier_results = {
        "candidateFree": {"result": "PASS", "head": HEAD, "tree": TREE, "cells": 240, "callerReferences": 21, "callerlessPositions": [], "priorWindowHashes": 2160, "priorSelections": 400, "priorHolds": 62, "priorAppliedTargetHashes": 95, "W1623AppliedCells": 13, "W1623RetainedCells": 227, "tokenMismatchCounts": {"placeholder": 0, "markup": 0, "numeric": 0, "protectedLiteral": 0}},
        "primary": {"result": "PASS", "head": HEAD, "tree": TREE, "cells": 240, "acceptCurrent": 236, "corrections": 4, "callerlessHolds": 0, "tokenPreservation": "PASS"},
        "blind": {"result": "PASS", "head": HEAD, "tree": TREE, "cells": 240, "decisions": {"accept-current": 233, "correction": 2, "refinement": 5}, "proposals": 7, "tokenSignatures": "PASS", "verifierRepoPin": "PASS with --repo exact detached worktree"},
    }
    (OUT / "packet-verifier-results.json").write_text(json.dumps(verifier_results, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    counts = Counter(r["crossDisposition"] for r in ledger)
    disagree_types = Counter(r["disagreementKind"] for r in ledger)
    summary = {
        "artifact": "slskR PR #209 W1643-W1662 independent semantic cross-review",
        "repository": REPO, "pullRequest": PR, "head": HEAD, "tree": TREE, "headRef": BRANCH,
        "selectedPositions": [1643, 1662], "sourceKeyCount": 20, "localeCount": 12,
        "reviewedCellCount": len(ledger), "callerOccurrenceCount": 21, "callerlessHoldCount": 0,
        "reviewerProposalCounts": {"primary": len(primary_proposals), "blind": len(blind_proposals), "uniqueUnion": len(final_proposals)},
        "crossDispositions": dict(counts), "applyReadyProposalCount": len(final_proposals),
        "reviewerDisagreementCellCount": len(disagreement_rows),
        "overlappingProposalCellsWithSameTarget": ["W1643-W1662:1643:ko", "W1643-W1662:1654:zh-Hant"],
        "targetWordingConflicts": 0,
        "disagreementKinds": dict(disagree_types),
        "mechanicalMismatchCounts": {"placeholder": 0, "markup": 0, "numeric": 0, "protectedLiteral": 0},
        "inputVerifierResults": {"candidateFree": "PASS", "primary": "PASS", "blind": "PASS"},
        "exactHeadAttestation": "PASS before and after cross-review; branch and pull refs both match the exact head",
        "priorLineage": {"priorSelections": 400, "priorWindowHashes": 2160, "priorHoldsUnchanged": 62, "priorAppliedTargetHashes": 95, "W1623Applied": 13, "W1623Retained": 227},
        "confidence": "moderate overall; per-cell confidence is recorded in the cross-ledger and recommendations",
        "limitations": ["No native-speaker signoff was obtained.", "No headed browser or UI display review was performed.", "No repository/catalog/PR edits, tests, builds, scans, CI, or workflows were run."],
        "createdAtUtc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    summary["disagreementKinds"].pop("both-accepted-current", None)
    (OUT / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    (OUT / "README.md").write_text(f"""# slskR PR #209 W1643-W1662 semantic cross-review

This packet independently cross-audits the candidate-free cells against both sealed review packets at PR head `{HEAD}` and tree `{TREE}`. It covers all 240 cells, all 20 source keys, all 12 locales, the source/current/caller bindings, and every proposed target. It does not modify any input packet or repository file.

## Adjudication

- All 240 cells are hash-bound to the candidate-free source, current target, caller contexts, and exact locale catalog pins.
- 231 cells retain current wording. Nine unique cells receive apply-ready recommendations: four corrections and five refinements.
- The primary and blind packets agree on the same target for 1643/ko and 1654/zh-Hant. They have seven one-sided recommendation differences; there are no conflicting target strings for a shared proposal.
- No callerless cells or cross-review holds exist.
- Source placeholders, markup, numeric tokens, and protected literals are preserved in all recommended targets.

`cross-ledger.jsonl` gives each cell's hashes, both incoming review decisions, any disagreement, and the cross-review disposition. `recommendations.jsonl` lists each apply-ready target. `proposal-disagreements.jsonl` records all seven one-sided recommendation differences. `holds-hash-only.jsonl` is empty.

The Japanese and Korean canonical-term refinements were checked against [Unicode's English-Japanese terminology](https://www.unicode.org/terminology/term_en_ja.html) and the [Korean National Institute of Korean Language term entry](https://kli.korean.go.kr/term/trgtWord/indexTrgtWord.do?trgtWordNo=2442583). The Korean entry recognizes both 정규형 and 표준형 for canonical form, so that recommendation remains a moderate-confidence refinement.

## Verification

Run `python3 verify_cross_review.py` from this directory. The defaults expect sibling `candidate-free-input/`, `primary-review/`, `blind-review/`, and `worktree/` directories. Alternate paths can be passed with `--input`, `--primary`, `--blind`, and `--worktree`. The verifier checks packet seals, exact source/current/caller hashes, candidate-free row hashes used by the blind packet, all 240 decisions, recommendation sets, token signatures, the recorded live PR pins, and the clean exact-head worktree.

The candidate-free, primary, and blind packet verifiers each passed before this cross-review. The cross-review independently pinned the live PR/API/branch/pull refs before and after review. No native-speaker or headed browser signoff is claimed. No tests, builds, scans, CI, workflows, or repository edits were performed.
""", encoding="utf-8")

    file_hashes = {p.relative_to(OUT).as_posix(): {"sha256": sha(p.read_bytes()), "byteCount": p.stat().st_size}
                   for p in sorted(OUT.rglob("*")) if p.is_file() and p.name not in {"manifest.json", "SHA256SUMS.txt"}}
    manifest = {"artifact": summary["artifact"], "repository": REPO, "pullRequest": PR,
                "head": HEAD, "tree": TREE, "headRef": BRANCH, "reviewType": "independent-semantic-cross-review",
                "reviewedCellCount": len(ledger), "proposalCount": len(final_proposals), "holdCount": 0,
                "fileHashes": file_hashes}
    (OUT / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"reviewed": len(ledger), "retainCurrent": counts["retain-current"], "corrections": counts["correction"],
                      "refinements": counts["refinement"], "applyReady": len(final_proposals), "reviewerDisagreements": len(disagreement_rows)}, indent=2))

if __name__ == "__main__": main()
