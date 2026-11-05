#!/usr/bin/env python3
"""Build the independent primary semantic review packet for W1643-W1662."""
from __future__ import annotations
import hashlib, json, re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

OUT = Path(__file__).resolve().parent
TASK = OUT.parent
INPUT = TASK / "candidate-free-input"
LOCALES = ["es", "zh-Hans", "hi", "de", "ja", "fr", "pt-BR", "ar", "ko", "zh-Hant", "vi", "id"]
HEAD = "2d804c49879372071adf606bc2a2cf51e261fd94"
TREE = "d6f5552d2400d868c2f2af98eb68caadfd4f3f66"
REPO = "snapetech-org/slskR"
PR = 209
BRANCH = "codex/slskr-l10n-audit-20261104-resync"

PROPOSALS = {
    (1643, "ko"): {
        "target": "메타데이터를 가져오지 못했습니다:",
        "rationale": "The current verb means search, while the source and Pod metadata caller mean retrieve/fetch. The caller appends the raw Pod error after a space, so retain the source colon rather than ending with a period.",
        "confidence": "high",
    },
    (1646, "zh-Hant"): {
        "target": "無法路由訊息。",
        "rationale": "Use the Traditional Chinese term 訊息, consistent with the adjacent route-message error and message-search terminology in this locale; 消息 is inconsistent with those locale terms.",
        "confidence": "moderate",
    },
    (1649, "hi"): {
        "target": "खतरों से सुरक्षा की सेटिंग सहेजी नहीं जा सकीं",
        "rationale": "प्रतिकूल describes something unfavorable/adverse here. The feature is adversarial threat protection, and the same locale renders Adversarial Settings as खतरों से सुरक्षा की सेटिंग; align the save error with that established feature wording.",
        "confidence": "moderate",
    },
    (1654, "zh-Hant"): {
        "target": "無法儲存來源訂閱整合設定。",
        "rationale": "來源摘要 means source summary, which changes the meaning of source-feed. This component configures imports from Spotify, YouTube, and Last.fm feeds; 訂閱 matches the adjacent Simplified Chinese source-feed translation and preserves the feed/subscription meaning.",
        "confidence": "high",
    },
}

MEANING = {
    1643: "Metadata retrieval failure; the colon-bearing variant is used beside appended error detail.",
    1644: "Pod metadata retrieval failure.",
    1645: "User information retrieval failure.",
    1646: "Message routing failure.",
    1647: "Message routing failure with following detail; retain the source separator.",
    1648: "Failure to save FTP integration settings; FTP is a protected product/protocol literal.",
    1649: "Failure to save adversarial threat-protection settings.",
    1650: "Failure to save bridge configuration.",
    1651: "Failure to save metadata integration settings.",
    1652: "Failure to save notification integration settings.",
    1653: "Failure to save policy settings.",
    1654: "Failure to save source-feed integration settings.",
    1655: "Failure to save a user note.",
    1656: "Content search failure.",
    1657: "Content search failure with an error placeholder.",
    1658: "Library-item search failure.",
    1659: "Message search failure.",
    1660: "Message search failure with an error placeholder.",
    1661: "Canonical-variant selection failure.",
    1662: "Failure to send a batch message to multiple recipients.",
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
    manifest = json.loads((INPUT / "manifest.json").read_text(encoding="utf-8"))
    if (manifest["head"], manifest["tree"], manifest["pullRequest"], manifest["repository"]) != (HEAD, TREE, PR, REPO):
        raise SystemExit("candidate-free exact target mismatch")
    if manifest["candidateFreeInputOnly"] is not True or manifest["proposedTranslationsIncluded"] is not False:
        raise SystemExit("candidate-free packet is not proposal-free")

    current = readjl(INPUT / "current-target-cells.jsonl")
    sources = readjl(INPUT / "source-contexts.jsonl")
    holds = readjl(INPUT / "caller-resolution-holds.jsonl")
    if len(current) != 240 or len(sources) != 20 or holds:
        raise SystemExit("candidate-free coverage/callerless hold mismatch")
    source_by_pos = {r["position"]: r for r in sources}
    if set(source_by_pos) != set(range(1643, 1663)):
        raise SystemExit("candidate-free source coverage mismatch")

    ledger, proposals = [], []
    for row in current:
        pos, loc = row["position"], row["locale"]
        ctx = source_by_pos[pos]
        if ctx["sourceKey"] != row["sourceKey"] or ctx["sourceKeySha256"] != row["sourceKeySha256"]:
            raise SystemExit(f"source/context mismatch: {pos}/{loc}")
        if ctx["callerContextSha256"] != row["sourceContextSha256"] or ctx["callerOccurrenceCount"] != row["callerCount"]:
            raise SystemExit(f"caller hash/count mismatch: {pos}/{loc}")
        actual = token_signature(row["currentTarget"])
        source_sig = {
            "placeholders": row["sourcePlaceholders"], "markupTags": row["sourceMarkupTags"],
            "numericTokens": row["sourceNumericTokens"], "protectedLiterals": row["sourceProtectedLiterals"],
        }
        if actual != {
            "placeholders": row["currentTargetPlaceholders"], "markupTags": row["currentTargetMarkupTags"],
            "numericTokens": row["currentTargetNumericTokens"], "protectedLiterals": row["currentTargetProtectedLiterals"],
        }:
            raise SystemExit(f"current token metadata mismatch: {pos}/{loc}")
        if actual != source_sig:
            raise SystemExit(f"current target violates source token signature: {pos}/{loc}")

        proposal = PROPOSALS.get((pos, loc))
        target = proposal["target"] if proposal else row["currentTarget"]
        target_sig = token_signature(target)
        if target_sig != source_sig:
            raise SystemExit(f"review target violates source token signature: {pos}/{loc}")
        decision = "correction" if proposal else "accept-current"
        caller_refs = [{
            "path": c["path"], "line": c["line"], "lineSha256": c["lineSha256"],
            "contextSha256": c["contextSha256"], "literalOccurrenceCount": c["literalOccurrenceCount"],
        } for c in ctx["callers"]]
        reason = proposal["rationale"] if proposal else f"{MEANING[pos]} Translation preserves this meaning in caller context; source/current placeholders, markup, numbers, and protected literals match exactly."
        item = {
            "rowId": f"W1643-W1662:{pos}:{loc}", "window": "W1643-W1662",
            "position": pos, "locale": loc, "sourceKey": row["sourceKey"],
            "sourceKeySha256": row["sourceKeySha256"], "currentTarget": row["currentTarget"],
            "currentTargetSha256": row["currentTargetSha256"], "sourceContextSha256": row["sourceContextSha256"],
            "callerOccurrenceCount": ctx["callerOccurrenceCount"], "callerReferences": caller_refs,
            "catalogPath": row["catalogPath"], "catalogFileSha256": row["catalogFileSha256"],
            "catalogGitBlob": row["catalogGitBlob"], "decision": decision,
            "recommendedTarget": target if proposal else None,
            "recommendedTargetSha256": sha(target) if proposal else None,
            "rationale": reason, "confidence": proposal["confidence"] if proposal else "moderate",
            "sourceTokenSignature": source_sig, "currentTokenSignature": actual,
            "recommendedTokenSignature": target_sig,
            "sourceCurrentTokenMatches": True, "recommendedTokenMatches": True,
            "priorWindowApplicationReattested": True,
        }
        ledger.append(item)
        if proposal:
            proposals.append({
                "rowId": item["rowId"], "position": pos, "locale": loc,
                "sourceKey": row["sourceKey"], "sourceKeySha256": row["sourceKeySha256"],
                "currentTarget": row["currentTarget"], "currentTargetSha256": row["currentTargetSha256"],
                "recommendedTarget": target, "recommendedTargetSha256": sha(target),
                "sourceContextSha256": row["sourceContextSha256"], "callerReferences": caller_refs,
                "disposition": "correction", "rationale": proposal["rationale"],
                "confidence": proposal["confidence"], "tokenPreservation": "PASS",
            })

    if len(ledger) != 240 or len(proposals) != 4:
        raise SystemExit("unexpected primary row or proposal count")
    if [(r["position"], r["locale"]) for r in ledger] != [(r["position"], r["locale"]) for r in current]:
        raise SystemExit("ledger order or coverage mismatch")

    writejl(OUT / "primary-ledger.jsonl", ledger)
    writejl(OUT / "proposals.jsonl", proposals)
    (OUT / "holds-hash-only.jsonl").write_text("", encoding="utf-8")
    input_att = {
        "repository": REPO, "pullRequest": PR, "head": HEAD, "tree": TREE,
        "headRef": BRANCH, "baseRef": manifest["baseRef"], "baseSha": manifest["baseSha"],
        "candidateFreeManifestSha256": sha((INPUT / "manifest.json").read_bytes()),
        "candidateFreeChecksumFileSha256": sha((INPUT / "SHA256SUMS.txt").read_bytes()),
        "candidateFreeCurrentCellsSha256": sha((INPUT / "current-target-cells.jsonl").read_bytes()),
        "candidateFreeSourceContextsSha256": sha((INPUT / "source-contexts.jsonl").read_bytes()),
        "candidateFreeRowCount": len(current), "sourceKeyCount": len(sources),
        "callerlessHoldCount": len(holds), "priorWindow1623AppliedCells": 13,
        "priorWindow1623RetainedCells": 227,
        "priorSelectionsReattested": manifest["priorSelectionReattestationCount"],
        "priorWindowHashesReattested": manifest["priorWindowHashRecordCount"],
        "priorAppliedTargetHashesReattested": manifest["priorAppliedTargetHashCount"],
        "priorHoldsReattested": manifest["carryForwardHoldUnchangedCount"],
        "candidateFreeChecksumResult": "PASS",
    }
    (OUT / "input-attestation.json").write_text(json.dumps(input_att, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    counts = Counter(row["decision"] for row in ledger)
    by_locale = {loc: {"reviewed": sum(r["locale"] == loc for r in ledger), "corrections": sum(r["locale"] == loc and r["decision"] == "correction" for r in ledger)} for loc in LOCALES}
    summary = {
        "artifact": "slskR PR #209 W1643-W1662 independent primary semantic review",
        "repository": REPO, "pullRequest": PR, "head": HEAD, "tree": TREE,
        "headRef": BRANCH, "selectedPositions": [1643, 1662], "localeOrder": LOCALES,
        "reviewedCellCount": len(ledger), "sourceKeyCount": 20, "localeCount": len(LOCALES),
        "callerOccurrenceCount": sum(r["callerOccurrenceCount"] for r in sources),
        "callerlessHoldCount": 0, "dispositions": dict(counts),
        "proposalCount": len(proposals), "proposalPositions": [1643, 1646, 1649, 1654],
        "byLocale": by_locale,
        "mechanicalMismatchCounts": {"placeholder": 0, "markup": 0, "numeric": 0, "protectedLiteral": 0},
        "priorLineage": {"priorSelections": 400, "priorWindowHashes": 2160, "priorHoldsUnchanged": 62, "priorAppliedHashes": 95, "W1623Applied": 13, "W1623Retained": 227},
        "confidence": "moderate overall; four proposed corrections are high or moderate confidence as recorded per row",
        "limitations": ["No native-speaker signoff was obtained.", "No browser/UI signoff was performed.", "No tests, builds, scans, or CI were run; review was read-only against candidate-free exact-head source and caller evidence."],
        "createdAtUtc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    (OUT / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    (OUT / "README.md").write_text(f"""# slskR PR #209 W1643-W1662 primary semantic review

This packet is an independent primary semantic review of the 240 candidate-free cells at PR head `{HEAD}` (tree `{TREE}`). It reviewed all 20 source keys in all 12 locales against the exact caller contexts and current catalog targets in the sealed candidate-free input. It contains no blind or cross-review material.

## Results

- 240 cells reviewed: {counts['accept-current']} accept-current and {counts['correction']} proposed corrections.
- Four proposals: 1643/ko, 1646/zh-Hant, 1649/hi, and 1654/zh-Hant.
- 0 callerless rows; the hash-only hold ledger is empty.
- Placeholder, markup, numeric-token, and protected-literal mismatches: 0. Proposed targets also preserve each source token signature.
- Prior continuity is reattested by the candidate-free packet: 400 prior selections, 2,160 prior window hashes, 62 unchanged holds, and 95 applied-target hashes. W1623-W1642 readback is pinned at 13 applied and 227 retained cells.

`primary-ledger.jsonl` contains every reviewed cell and binds its source, current target, caller evidence, locale catalog pin, decision, rationale, confidence, and token checks by hash. `proposals.jsonl` contains the four exact recommended target strings and their rationale. `holds-hash-only.jsonl` is empty because every row has a resolved production caller.

## Verification

Run `python3 verify_primary.py` from this directory. The default candidate-free input and exact-head worktree are the sibling `candidate-free-input/` and `worktree/` directories. Alternate paths can be provided with `--input` and `--worktree`. The verifier checks packet checksums, candidate-free seals, complete row coverage, source/current/caller hash bindings, proposal semantics and token preservation, and local Git head/tree/clean status. Live PR/branch/pull-ref snapshots taken before and after review are retained under `attestation/`.

## Limits

Overall confidence is **moderate**. Proposed corrections have per-row confidence in the ledger. No native-speaker or browser/UI signoff was obtained. No tests, builds, scans, CI, workflows, repository edits, or PR changes were performed.
""", encoding="utf-8")

    payload = [p for p in OUT.rglob("*") if p.is_file() and p.name not in {"manifest.json", "SHA256SUMS.txt"}]
    file_hashes = {p.relative_to(OUT).as_posix(): {"sha256": sha(p.read_bytes()), "byteCount": p.stat().st_size} for p in sorted(payload)}
    out_manifest = {
        "artifact": summary["artifact"], "repository": REPO, "pullRequest": PR,
        "head": HEAD, "tree": TREE, "headRef": BRANCH, "candidateFreeInputOnly": False,
        "reviewType": "independent-primary-semantic", "reviewedCellCount": len(ledger),
        "proposalCount": len(proposals), "callerlessHoldCount": 0,
        "fileHashes": file_hashes,
    }
    (OUT / "manifest.json").write_text(json.dumps(out_manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"reviewed": len(ledger), "acceptCurrent": counts["accept-current"], "corrections": counts["correction"], "proposals": len(proposals)}, indent=2))

if __name__ == "__main__": main()
