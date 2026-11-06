#!/usr/bin/env python3
"""Build the sealed integrated cross-review ledger from the three pinned packets."""
from __future__ import annotations

import hashlib
import json
import re
import shutil
from collections import Counter
from pathlib import Path

OUT = Path(__file__).resolve().parent
ROOT = OUT.parent
CANDIDATE = ROOT / "candidate-free-input"
PRIMARY = ROOT / "primary-review"
BLIND = ROOT / "blind-review"
HEAD = "0264a4fcaa944fee61049efec0cf3c451416c8b9"
TREE = "895e57c178d959a23aceddead27623f2dd854ba0"
WINDOW = "W1783-W1802"

BLIND_CHOICES = {
    (1783, "vi"),
    (1791, "hi"),
    (1796, "zh-Hans"),
    (1793, "es"),
    (1793, "pt-BR"),
    (1793, "ar"),
}
HOLD_CHOICES = {(1792, "ko")}

RATIONALES = {
    (1783, "vi"): "The caller identifies this as the numeric spectralFlux metric. The blind wording is the direct technical term for spectral flux, while the primary wording paraphrases the variation; select the technical label provisionally.",
    (1784, "de"): "The pinned caller uses a filter icon and a tooltip that focuses the current result filter on the album folder name. The current German verb means visually highlighting, so the primary correction matches the action.",
    (1786, "ar"): "Both reviews reject the literal capsule rendering and retain Pod as the shared-listening product term. The caller identifies the displayed workflow as the selected pod workflow, so use the primary wording that expresses the selected state.",
    (1786, "fr"): "The caller identifies one selected pod workflow. The current French plural targeted-pods wording changes that relation; the primary correction preserves the singular selected workflow.",
    (1791, "hi"): "Both reviews reject a literal folding verb. The blind proposal explicitly says to group duplicate results, matching the action described by the source.",
    (1791, "de"): "Both reviews reject literal folding. The primary wording says to group duplicate results, which matches the source action more closely than the blind alternative meaning summarize or consolidate.",
    (1791, "ar"): "Both reviews reject literal folding. The primary wording expresses grouping duplicate results and avoids implying that the records themselves are merged.",
    (1791, "id"): "Both reviews reject literal folding. The primary wording expresses grouping duplicate results and avoids the stronger implication of merging them.",
    (1792, "es"): "Both reviews reject literal folding. The primary wording preserves the source condition of pagination support being available.",
    (1792, "hi"): "Both reviews reject literal folding. The primary wording describes pagination support and retains the source condition that the feature is available.",
    (1792, "de"): "Both reviews reject literal folding. The primary wording directly preserves the condition that page support is available.",
    (1792, "vi"): "Both reviews reject literal folding. The primary wording says the duplicates become one review row when pagination support is available, preserving the source action and condition.",
    (1792, "id"): "Both reviews reject literal folding. The primary wording says to group the likely duplicates into one review row, matching the source action.",
    (1792, "ja"): "The English source says single in words and contains no numeric token. The primary wording replaces the unmatched digit 1 with 単一 while preserving the meaning.",
    (1792, "ko"): "The primary review retains the current word, while the blind review flags a locale-specific choice between a fold/collapse term and a grouping term. The exact Korean UI term is unresolved, so hold this cell at its current hash pending locale review.",
    (1793, "es"): "The blind review identifies that the current wording omits that each rule belongs to a Wishlist item. Its proposal restores that ownership detail and matches the source.",
    (1793, "pt-BR"): "The blind review identifies that the current wording omits that each rule belongs to a Wishlist item. Its proposal restores that ownership detail and matches the source.",
    (1793, "ar"): "The blind review identifies that the current wording omits that each rule belongs to a Wishlist item. Its proposal restores that ownership detail and matches the source.",
    (1796, "ja"): "The caller is a listen-along control. The primary proposal describes listening in sync with the host, correcting the current wording that reads as tracking or pursuit.",
    (1796, "fr"): "Both reviews identify that the current French term changes a listening pod into a software module. The primary proposal preserves pod and the human host relation.",
    (1796, "vi"): "Both reviews identify that the current wording changes the human listen-along host into a server. The primary proposal preserves the human host role and Pod entity.",
    (1796, "zh-Hans"): "Both reviews reject tracking wording and use 跟随 for following playback. The caller pairs the action with a human listen-along host, so the blind proposal's 主持人 is more precise than the primary proposal's 主机.",
    (1796, "ar"): "Both reviews replace the literal capsule term with Pod and describe following the host's playback. Select the primary proposal, preserving Pod as the product entity.",
    (1799, "hi"): "The caller displays this label beside supporting evidence and pairs it with the opposing evidence label. The primary wording is a concise evidence-stance label rather than a generic preposition.",
    (1799, "ar"): "The caller displays this label beside evidence supporting the result. The primary wording directly labels what supports the result.",
    (1799, "ko"): "The caller displays this label beside supporting evidence. The primary wording makes the evidence relation explicit, which is clearer for this standalone label.",
    (1800, "hi"): "Both reviews independently propose the same Hindi action label for the administrative HTTPS checkbox. It expresses requiring HTTPS and retains the protected HTTPS literal.",
}


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def token_signature(value: str):
    placeholders = re.findall(r"\{[A-Za-z][A-Za-z0-9_]*\}", value)
    markup = re.findall(r"</?[A-Za-z][^>]*>", value)
    numbers = re.findall(r"(?<![A-Za-z])\d+(?:[.,]\d+)?%?(?![A-Za-z])", value)
    protected = []
    for item in re.findall(r"(?<![A-Za-z0-9])(?:[A-Z]{2,}[A-Z0-9]*|ffmpeg|Chromaprint|Soulseek|Spotify|YouTube|Pushbullet|Matrix|WebSocket|OpenAI)(?![A-Za-z0-9])", value):
        if item not in protected:
            protected.append(item)
    return {
        "placeholders": placeholders,
        "markupTags": markup,
        "numericTokens": numbers,
        "protectedLiterals": protected,
    }


def token_audit(source: dict, value: str):
    sig = token_signature(value)
    return {
        "placeholderSequenceMatches": sig["placeholders"] == source["sourcePlaceholders"],
        "markupMatches": sig["markupTags"] == source["sourceMarkupTags"],
        "numericTokensMatch": sig["numericTokens"] == source["sourceNumericTokens"],
        "protectedLiteralsMatch": all(x in value for x in source["sourceProtectedLiterals"]),
        "targetPlaceholders": sig["placeholders"],
        "targetMarkupTags": sig["markupTags"],
        "targetNumericTokens": sig["numericTokens"],
        "targetProtectedLiterals": sig["protectedLiterals"],
    }


def caller_pins(ctx: dict):
    return [
        {
            "path": item["path"],
            "line": item["line"],
            "lineText": item["lineText"],
            "lineSha256": item["lineSha256"],
            "contextStartLine": item["contextStartLine"],
            "contextEndLine": item["contextEndLine"],
            "contextSha256": item["contextSha256"],
            "fileSha256": item["fileSha256"],
            "gitBlob": item["gitBlob"],
            "literalOccurrenceCount": item["literalOccurrenceCount"],
        }
        for item in ctx["callers"]
    ]


def choose(pos: int, locale: str, current: dict, primary: dict, blind: dict):
    key = (pos, locale)
    current_text = current["currentTarget"]
    primary_text = primary["proposedTarget"]
    blind_text = blind.get("reviewerSuggestionUnapproved")

    if key in HOLD_CHOICES:
        return {"mode": "hold", "origin": "current", "target": current_text, "category": "hold", "rationale": RATIONALES[key], "confidence": "unknown"}

    if blind["status"] == "review":
        if key == (1800, "hi") and primary_text == blind_text:
            return {"mode": "agreement", "origin": "primary_and_blind", "target": primary_text, "category": "refinement", "rationale": RATIONALES[key], "confidence": "moderate"}
        if key in {(1786, "ar"), (1796, "ar")}:
            return {"mode": "primary", "origin": "primary", "target": primary_text, "category": "correction", "rationale": RATIONALES[key], "confidence": "moderate"}
        if key == (1796, "zh-Hans"):
            return {"mode": "blind", "origin": "blind", "target": blind_text, "category": "correction", "rationale": RATIONALES[key], "confidence": "moderate"}
        raise ValueError(f"unadjudicated blind review flag at {pos}/{locale}")

    if blind["status"] == "revise":
        if primary_text == blind_text:
            return {
                "mode": "agreement",
                "origin": "primary_and_blind",
                "target": primary_text,
                "category": "correction",
                "rationale": "The primary and blind reviews independently propose the same exact correction for the identified source/caller issue.",
                "confidence": "moderate",
            }
        if key in BLIND_CHOICES:
            return {"mode": "blind", "origin": "blind", "target": blind_text, "category": "correction", "rationale": RATIONALES[key], "confidence": "moderate"}
        if primary["disposition"] == "accept_current":
            return {
                "mode": "blind",
                "origin": "blind",
                "target": blind_text,
                "category": "correction",
                "rationale": RATIONALES.get(key, "The blind review identifies a source detail omitted by the current translation; its proposed wording restores that detail."),
                "confidence": "moderate",
            }
        return {
            "mode": "primary",
            "origin": "primary",
            "target": primary_text,
            "category": "correction",
            "rationale": RATIONALES.get(key, "Both reviews identify the same material issue; the primary proposal best preserves the source meaning in the pinned caller context."),
            "confidence": "moderate",
        }

    if blind["status"] != "retain":
        raise ValueError(f"unknown blind status at {pos}/{locale}")

    if primary["disposition"] == "correction":
        return {
            "mode": "primary",
            "origin": "primary",
            "target": primary_text,
            "category": "correction",
            "rationale": RATIONALES.get(key, "The primary review identifies a semantic or token-fidelity problem supported by the pinned source/caller evidence."),
            "confidence": "moderate",
        }

    if primary["disposition"] == "refinement":
        return {
            "mode": "current",
            "origin": "current",
            "target": current_text,
            "category": "accept_current",
            "rationale": "The blind review found no material semantic issue. The primary recommendation is a stylistic refinement, so retain the exact current target under conservative cross-review.",
            "confidence": "moderate",
        }

    return {
        "mode": "current",
        "origin": "current",
        "target": current_text,
        "category": "accept_current",
        "rationale": "Both semantic reviews retain the current translation, and the pinned source/caller and token evidence do not require a change.",
        "confidence": "moderate",
    }


def checksum_output():
    lines = []
    for path in sorted(p for p in OUT.rglob("*") if p.is_file() and p.name != "SHA256SUMS.txt"):
        lines.append(f"{sha256(path.read_bytes())}  {path.relative_to(OUT).as_posix()}")
    (OUT / "SHA256SUMS.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    if OUT.exists() and any(p.name not in {"build_integrated_cross_review.py", "verify_integrated_cross_review.py"} for p in OUT.iterdir()):
        raise SystemExit(f"refusing to overwrite generated output in directory: {OUT}")
    OUT.mkdir(parents=True, exist_ok=True)

    candidate_manifest = read_json(CANDIDATE / "manifest.json")
    primary_summary = read_json(PRIMARY / "summary.json")
    blind_manifest = read_json(BLIND / "manifest.json")
    if (candidate_manifest["head"], candidate_manifest["tree"]) != (HEAD, TREE):
        raise SystemExit("candidate-free exact-head pin mismatch")
    if (primary_summary["head"], primary_summary["tree"]) != (HEAD, TREE):
        raise SystemExit("primary exact-head pin mismatch")
    if (blind_manifest["head"], blind_manifest["tree"]) != (HEAD, TREE):
        raise SystemExit("blind exact-head pin mismatch")

    cells = read_jsonl(CANDIDATE / "current-target-cells.jsonl")
    sources = {r["position"]: r for r in read_jsonl(CANDIDATE / "source-queue.jsonl")}
    contexts = {r["position"]: r for r in read_jsonl(CANDIDATE / "source-contexts.jsonl")}
    primary_rows = {(r["position"], r["locale"]): r for r in read_jsonl(PRIMARY / "primary-semantic-review-ledger.jsonl")}
    blind_rows = {(r["position"], r["locale"]): r for r in read_jsonl(BLIND / "blind-review-ledger.jsonl")}
    keys = [(r["position"], r["locale"]) for r in cells]
    if len(cells) != 240 or len(set(keys)) != 240:
        raise SystemExit("candidate-free cell coverage is not 240 unique cells")
    if set(keys) != set(primary_rows) or set(keys) != set(blind_rows):
        raise SystemExit("primary/blind/candidate coverage differs")
    if sorted({x[0] for x in keys}) != list(range(1783, 1803)):
        raise SystemExit("window positions are not exactly W1783-W1802")
    if set(contexts) != set(range(1783, 1803)):
        raise SystemExit("source/caller context coverage differs")

    out = []
    final_counts = Counter()
    origin_counts = Counter()
    baseline_token_counts = Counter()
    selected_token_counts = Counter({"placeholder": 0, "markup": 0, "numeric": 0, "protectedLiteral": 0})
    locale_flags = []
    for current in cells:
        pos, locale = current["position"], current["locale"]
        key = (pos, locale)
        src = sources[pos]
        ctx = contexts[pos]
        primary = primary_rows[key]
        blind = blind_rows[key]

        if current["sourceKey"] != src["sourceKey"] or current["sourceKeySha256"] != src["sourceKeySha256"]:
            raise SystemExit(f"source queue mismatch at {pos}/{locale}")
        if current["sourceContextSha256"] != ctx["callerContextSha256"]:
            raise SystemExit(f"source/caller context mismatch at {pos}/{locale}")
        if primary["sourceKeySha256"] != current["sourceKeySha256"] or primary["callerContextSha256"] != current["sourceContextSha256"]:
            raise SystemExit(f"primary source/caller pin mismatch at {pos}/{locale}")
        if blind["sourceKey"] != current["sourceKey"] or blind["sourceContextSha256"] != current["sourceContextSha256"]:
            raise SystemExit(f"blind source/caller pin mismatch at {pos}/{locale}")
        if primary["currentTarget"] != current["currentTarget"] or primary["currentTargetSha256"] != current["currentTargetSha256"]:
            raise SystemExit(f"primary current-target mismatch at {pos}/{locale}")
        if blind["currentTarget"] != current["currentTarget"] or blind["currentTargetSha256"] != current["currentTargetSha256"]:
            raise SystemExit(f"blind current-target mismatch at {pos}/{locale}")
        if sha256(current["currentTarget"].encode("utf-8")) != current["currentTargetSha256"]:
            raise SystemExit(f"candidate-free current-target hash mismatch at {pos}/{locale}")
        if sha256(primary["proposedTarget"].encode("utf-8")) != primary["proposedTargetSha256"]:
            raise SystemExit(f"primary proposal hash mismatch at {pos}/{locale}")
        if primary["catalogPath"] != current["catalogPath"] or primary["catalogFileSha256"] != current["catalogFileSha256"] or primary["catalogGitBlob"] != current["catalogGitBlob"]:
            raise SystemExit(f"primary catalog pin mismatch at {pos}/{locale}")
        if primary["callerReferenceCount"] != ctx["callerOccurrenceCount"] or current["callerCount"] != ctx["productionCallerCount"]:
            raise SystemExit(f"caller count mismatch at {pos}/{locale}")

        baseline = current["targetTokenVariants"]
        if not baseline:
            raise SystemExit(f"missing current target token evidence at {pos}/{locale}")
        for variant in baseline:
            if not variant["placeholderSequenceMatches"]:
                baseline_token_counts["placeholder"] += 1
            if not variant["markupMatches"]:
                baseline_token_counts["markup"] += 1
            if not variant["numericTokensMatch"]:
                baseline_token_counts["numeric"] += 1
            if not variant["protectedLiteralsMatch"]:
                baseline_token_counts["protectedLiteral"] += 1

        selected = choose(pos, locale, current, primary, blind)
        selected_text = selected["target"]
        selected_sha = sha256(selected_text.encode("utf-8"))
        selected_audit = token_audit(current, selected_text)
        for name, key_name in [
            ("placeholder", "placeholderSequenceMatches"),
            ("markup", "markupMatches"),
            ("numeric", "numericTokensMatch"),
            ("protectedLiteral", "protectedLiteralsMatch"),
        ]:
            if not selected_audit[key_name]:
                selected_token_counts[name] += 1
        if any(not selected_audit[x] for x in ["placeholderSequenceMatches", "markupMatches", "numericTokensMatch", "protectedLiteralsMatch"]):
            raise SystemExit(f"selected target fails exact token fidelity at {pos}/{locale}")

        suggestion = blind.get("reviewerSuggestionUnapproved")
        suggestion_hash = sha256(suggestion.encode("utf-8")) if isinstance(suggestion, str) else None
        suggestion_audit = token_audit(current, suggestion) if isinstance(suggestion, str) else None
        if suggestion is not None and not isinstance(suggestion, str):
            raise SystemExit(f"blind suggestion has unexpected type at {pos}/{locale}")

        if blind["status"] == "review":
            locale_flags.append({
                "cellId": f"{pos}::{locale}",
                "blindIssueCodes": blind["issueCodes"],
                "resolution": "hold" if selected["mode"] == "hold" else "resolved_provisionally",
                "selectedTargetSha256": selected_sha,
            })

        row = {
            "window": WINDOW,
            "head": HEAD,
            "tree": TREE,
            "position": pos,
            "locale": locale,
            "source": {
                "text": current["sourceKey"],
                "sha256": current["sourceKeySha256"],
                "callerContextSha256": ctx["callerContextSha256"],
                "callerOccurrenceCount": ctx["callerOccurrenceCount"],
                "callerReferenceCount": ctx["productionCallerCount"],
                "callerReferences": caller_pins(ctx),
                "placeholders": current["sourcePlaceholders"],
                "markupTags": current["sourceMarkupTags"],
                "numericTokens": current["sourceNumericTokens"],
                "protectedLiterals": current["sourceProtectedLiterals"],
            },
            "current": {
                "text": current["currentTarget"],
                "sha256": current["currentTargetSha256"],
                "type": current["currentTargetType"],
                "catalogPath": current["catalogPath"],
                "catalogFileSha256": current["catalogFileSha256"],
                "catalogGitBlob": current["catalogGitBlob"],
                "tokenEvidence": baseline,
            },
            "reviews": {
                "primary": {
                    "disposition": primary["disposition"],
                    "proposal": primary["proposedTarget"],
                    "proposalSha256": primary["proposedTargetSha256"],
                    "rationale": primary["rationale"],
                    "confidence": primary["confidence"],
                    "tokenAudit": primary["proposedTokenAudit"],
                    "nativeSpeakerApproval": primary["nativeSpeakerApproval"],
                },
                "blind": {
                    "status": blind["status"],
                    "issueCodes": blind["issueCodes"],
                    "rationale": blind["rationale"],
                    "confidence": blind["confidence"],
                    "proposal": suggestion,
                    "proposalSha256": suggestion_hash,
                    "proposalTokenAudit": suggestion_audit,
                    "tokenChecks": blind["tokenChecks"],
                    "nativeSpeakerApproval": False,
                },
            },
            "adjudication": {
                "mode": selected["mode"],
                "targetOrigin": selected["origin"],
                "disposition": selected["category"],
                "rationale": selected["rationale"],
                "confidence": selected["confidence"],
                "selectedTarget": selected_text,
                "selectedTargetSha256": selected_sha,
                "selectedTokenAudit": selected_audit,
                "nativeSpeakerApproval": False,
            },
        }
        out.append(row)
        final_counts[selected["category"]] += 1
        origin_counts[selected["origin"]] += 1

    if len(locale_flags) != 5:
        raise SystemExit(f"expected five blind locale-review flags, got {len(locale_flags)}")
    if sum(final_counts.values()) != 240:
        raise SystemExit("integrated disposition count does not total 240")

    hold_rows = [r for r in out if r["adjudication"]["disposition"] == "hold"]
    hold_lineage = read_jsonl(CANDIDATE / "active-hold-reattestation.jsonl")
    if len(hold_lineage) != 1:
        raise SystemExit("expected exactly one carried active hash-only hold")
    active_hold = hold_lineage[0]
    if active_hold.get("holdId") != "1719::id" or active_hold.get("textIncluded") is not False:
        raise SystemExit("carried active hold is not hash-only")
    if any(k in active_hold for k in ("sourceKey", "sourceText", "currentTarget", "targetText")):
        raise SystemExit("carried active hold unexpectedly contains source/target text")
    hold_record = {
        "artifact": "integrated cross-review hold lineage",
        "head": HEAD,
        "tree": TREE,
        "carriedPriorActiveHold": active_hold,
        "newWindowHolds": [
            {
                "cellId": f'{r["position"]}::{r["locale"]}',
                "sourceKeySha256": r["source"]["sha256"],
                "sourceContextSha256": r["source"]["callerContextSha256"],
                "currentTargetSha256": r["current"]["sha256"],
                "primaryDisposition": r["reviews"]["primary"]["disposition"],
                "blindStatus": r["reviews"]["blind"]["status"],
                "blindIssueCodes": r["reviews"]["blind"]["issueCodes"],
                "selectedTargetSha256": r["adjudication"]["selectedTargetSha256"],
                "textIncluded": False,
                "rationale": r["adjudication"]["rationale"],
            }
            for r in hold_rows
        ],
    }

    boundary = next(
        r for r in read_jsonl(CANDIDATE / "source-window-boundaries.jsonl")
        if r.get("position") == 1803 and r.get("boundary") is True
    )
    if boundary["sourceKeySha256"] != "46f390c945e7ff7e760db1cc63bed9f9429afa266c56413af8628ad801008175":
        raise SystemExit("next source boundary hash mismatch")

    (OUT / "integrated-cross-ledger.jsonl").write_text(
        "".join(json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n" for row in out),
        encoding="utf-8",
    )
    shutil.copyfile(CANDIDATE / "source-contexts.jsonl", OUT / "source-caller-context-index.jsonl")
    shutil.copyfile(CANDIDATE / "active-hold-reattestation.jsonl", OUT / "active-hold-reattestation.jsonl")
    shutil.copyfile(
        CANDIDATE / "previous-window-readback-reattestation-hash-only.jsonl",
        OUT / "previous-window-readback-reattestation-hash-only.jsonl",
    )
    (OUT / "hold-lineage.json").write_text(json.dumps(hold_record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    candidate_sum_hash = sha256((CANDIDATE / "SHA256SUMS.txt").read_bytes())
    primary_sum_hash = sha256((PRIMARY / "SHA256SUMS.txt").read_bytes())
    blind_sum_hash = sha256((BLIND / "SHA256SUMS.txt").read_bytes())
    input_files = {
        "candidateFree": {
            "path": "../candidate-free-input",
            "sha256SumsFileSha256": candidate_sum_hash,
            "manifestSha256": sha256((CANDIDATE / "manifest.json").read_bytes()),
            "currentTargetCellsSha256": sha256((CANDIDATE / "current-target-cells.jsonl").read_bytes()),
            "sourceQueueSha256": sha256((CANDIDATE / "source-queue.jsonl").read_bytes()),
            "sourceContextsSha256": sha256((CANDIDATE / "source-contexts.jsonl").read_bytes()),
            "activeHoldSha256": sha256((CANDIDATE / "active-hold-reattestation.jsonl").read_bytes()),
            "previousWindowReadbackSha256": sha256((CANDIDATE / "previous-window-readback-reattestation-hash-only.jsonl").read_bytes()),
        },
        "primary": {
            "path": "../primary-review",
            "sha256SumsFileSha256": primary_sum_hash,
            "summarySha256": sha256((PRIMARY / "summary.json").read_bytes()),
            "ledgerSha256": sha256((PRIMARY / "primary-semantic-review-ledger.jsonl").read_bytes()),
        },
        "blind": {
            "path": "../blind-review",
            "sha256SumsFileSha256": blind_sum_hash,
            "manifestSha256": sha256((BLIND / "manifest.json").read_bytes()),
            "ledgerSha256": sha256((BLIND / "blind-review-ledger.jsonl").read_bytes()),
        },
    }

    manifest = {
        "artifact": "slskR PR #209 W1783-W1802 integrated cross-review ledger",
        "repository": "snapetech-org/slskR",
        "pullRequest": 209,
        "window": WINDOW,
        "head": HEAD,
        "tree": TREE,
        "inputPackets": input_files,
        "cellCount": len(out),
        "sourceCount": 20,
        "localeCount": 12,
        "callerOccurrenceCount": candidate_manifest["callerOccurrenceCount"],
        "callerReferenceCount": candidate_manifest["callerReferenceCount"],
        "dispositions": dict(sorted(final_counts.items())),
        "selectionOrigins": dict(sorted(origin_counts.items())),
        "changedTargetCount": sum(1 for r in out if r["adjudication"]["selectedTargetSha256"] != r["current"]["sha256"]),
        "baselineTokenMismatchCountsRecomputed": dict(sorted(baseline_token_counts.items())),
        "selectedTokenMismatchCounts": dict(sorted(selected_token_counts.items())),
        "localeReviewFlags": {
            "count": len(locale_flags),
            "resolvedProvisionally": sum(1 for x in locale_flags if x["resolution"] == "resolved_provisionally"),
            "held": sum(1 for x in locale_flags if x["resolution"] == "hold"),
            "cells": locale_flags,
        },
        "holdCells": [f'{r["position"]}::{r["locale"]}' for r in hold_rows],
        "carriedPriorActiveHold": {
            "holdId": active_hold["holdId"],
            "position": active_hold["position"],
            "locale": active_hold["locale"],
            "targetHashUnchanged": active_hold["targetHashUnchanged"],
            "sourceContextUnchanged": active_hold["sourceContextUnchanged"],
            "textIncluded": False,
        },
        "previousWindowReadbackCount": 240,
        "previousWindowReadbacksTextIncluded": False,
        "nextBoundary": boundary,
        "reviewConfidence": "moderate",
        "nativeSpeakerApproval": False,
        "productFilesEdited": False,
        "testsBuildsScansCiRun": False,
        "selectionPolicy": {
            "summary": "Require candidate-free source/caller/token evidence; preserve independently corroborated material corrections; retain current text when only a stylistic refinement is proposed; hold the unresolved Korean fold/group term.",
            "localeReviewFlags": {
                "resolvedProvisionally": [x["cellId"] for x in locale_flags if x["resolution"] == "resolved_provisionally"],
                "held": [x["cellId"] for x in locale_flags if x["resolution"] == "hold"],
            },
        },
        "checksumCoverage": "SHA256SUMS.txt covers every regular output file except itself.",
    }
    (OUT / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    readme = f"""# slskR PR #209 W1783-W1802 integrated cross-review

Pinned product head/tree: {HEAD} / {TREE}.

This packet integrates all 240 cells from the sealed candidate-free, primary semantic review, and blind review packets. Each cell binds the source string and caller context, current target and exact catalog pin, both review decisions and proposals, selected target text/hash, token audit, rationale, and confidence.

## Result

- 240 cells: {dict(sorted(final_counts.items()))}
- Changed targets: {manifest['changedTargetCount']}
- Five blind locale-review flags: {manifest['localeReviewFlags']['resolvedProvisionally']} resolved provisionally, {manifest['localeReviewFlags']['held']} held.
- The unresolved cell is {', '.join(manifest['holdCells'])}.
- The prior active hold 1719::id remains hash-only; its source and target text are not included.
- The predecessor window's 240 target readbacks remain hash-only and unchanged.
- No native-speaker approval is included. No product files, catalogs, PRs, tests, builds, or CI were changed or run.

## Verification

Run python3 -B verify_integrated_cross_review.py from this directory. The verifier checks all three input packet checksum lists, exact head/tree and 240-cell coverage, source/caller/current-target pins, proposal and selected-target hashes, token signatures, hold lineage, the unchanged predecessor hash-only readbacks, and this packet's checksums.

SHA256SUMS.txt lists every regular file in this packet except itself. Its SHA-256 is reported separately with the handoff.
"""
    (OUT / "README.md").write_text(readme, encoding="utf-8")
    checksum_output()
    print(json.dumps({
        "output": str(OUT),
        "cells": len(out),
        "dispositions": dict(sorted(final_counts.items())),
        "selectionOrigins": dict(sorted(origin_counts.items())),
        "changedTargetCount": manifest["changedTargetCount"],
        "localeReviewFlags": manifest["localeReviewFlags"],
        "baselineTokenMismatchCounts": dict(sorted(baseline_token_counts.items())),
        "selectedTokenMismatchCounts": dict(sorted(selected_token_counts.items())),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
