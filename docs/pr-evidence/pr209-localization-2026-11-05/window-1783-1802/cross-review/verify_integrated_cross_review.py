#!/usr/bin/env python3
"""Verify the integrated cross-review packet against its three sealed inputs."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import Counter
from pathlib import Path

OUT = Path(__file__).resolve().parent
ROOT = OUT.parent
DEFAULT_CANDIDATE = ROOT / "candidate-free-input"
DEFAULT_PRIMARY = ROOT / "primary-review"
DEFAULT_BLIND = ROOT / "blind-review"
HEAD = "0264a4fcaa944fee61049efec0cf3c451416c8b9"
TREE = "895e57c178d959a23aceddead27623f2dd854ba0"


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def require(condition: bool, message: str):
    if not condition:
        raise SystemExit(f"FAIL: {message}")


def checksum_entries(directory: Path):
    checksum_file = directory / "SHA256SUMS.txt"
    entries = {}
    for line in checksum_file.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        parts = line.split("  ", 1)
        require(len(parts) == 2, f"malformed checksum line in {checksum_file}")
        expected, relative = parts
        p = Path(relative)
        require(not p.is_absolute() and ".." not in p.parts, f"unsafe checksum path in {checksum_file}")
        require(relative not in entries, f"duplicate checksum path in {checksum_file}")
        entries[relative] = expected
    actual = {
        p.relative_to(directory).as_posix()
        for p in directory.rglob("*")
        if p.is_file() and p.name != "SHA256SUMS.txt"
    }
    require(actual == set(entries), f"checksum coverage differs in {directory}")
    for relative, expected in entries.items():
        require(digest((directory / relative).read_bytes()) == expected, f"checksum mismatch: {directory / relative}")
    return entries


def token_signature(value: str):
    placeholders = re.findall(r"\{[A-Za-z][A-Za-z0-9_]*\}", value)
    markup = re.findall(r"</?[A-Za-z][^>]*>", value)
    numbers = re.findall(r"(?<![A-Za-z])\d+(?:[.,]\d+)?%?(?![A-Za-z])", value)
    protected = []
    for item in re.findall(r"(?<![A-Za-z0-9])(?:[A-Z]{2,}[A-Z0-9]*|ffmpeg|Chromaprint|Soulseek|Spotify|YouTube|Pushbullet|Matrix|WebSocket|OpenAI)(?![A-Za-z0-9])", value):
        if item not in protected:
            protected.append(item)
    return placeholders, markup, numbers, protected


def token_audit(source: dict, value: str):
    placeholders, markup, numbers, protected = token_signature(value)
    return {
        "placeholderSequenceMatches": placeholders == source["sourcePlaceholders"],
        "markupMatches": markup == source["sourceMarkupTags"],
        "numericTokensMatch": numbers == source["sourceNumericTokens"],
        "protectedLiteralsMatch": all(x in value for x in source["sourceProtectedLiterals"]),
        "targetPlaceholders": placeholders,
        "targetMarkupTags": markup,
        "targetNumericTokens": numbers,
        "targetProtectedLiterals": protected,
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


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate-free", type=Path, default=DEFAULT_CANDIDATE)
    parser.add_argument("--primary", type=Path, default=DEFAULT_PRIMARY)
    parser.add_argument("--blind", type=Path, default=DEFAULT_BLIND)
    parser.add_argument("--output", type=Path, default=OUT)
    args = parser.parse_args()

    out_dir = args.output.resolve()
    manifest = read_json(out_dir / "manifest.json")
    require((manifest["head"], manifest["tree"]) == (HEAD, TREE), "integrated head/tree pin mismatch")

    input_dirs = {
        "candidateFree": args.candidate_free.resolve(),
        "primary": args.primary.resolve(),
        "blind": args.blind.resolve(),
    }
    for name, directory in input_dirs.items():
        expected = manifest["inputPackets"][name]["sha256SumsFileSha256"]
        require(digest((directory / "SHA256SUMS.txt").read_bytes()) == expected, f"{name} checksum list pin mismatch")
        checksum_entries(directory)

    candidate_manifest = read_json(input_dirs["candidateFree"] / "manifest.json")
    primary_summary = read_json(input_dirs["primary"] / "summary.json")
    blind_manifest = read_json(input_dirs["blind"] / "manifest.json")
    require((candidate_manifest["head"], candidate_manifest["tree"]) == (HEAD, TREE), "candidate-free head/tree mismatch")
    require((primary_summary["head"], primary_summary["tree"]) == (HEAD, TREE), "primary head/tree mismatch")
    require((blind_manifest["head"], blind_manifest["tree"]) == (HEAD, TREE), "blind head/tree mismatch")
    require(candidate_manifest["pullRequest"] == 209 and primary_summary["pullRequest"] == 209 and blind_manifest["pullRequest"] == 209, "PR identity mismatch")

    cf = input_dirs["candidateFree"]
    primary_dir = input_dirs["primary"]
    blind_dir = input_dirs["blind"]
    input_hash_checks = [
        (cf / "manifest.json", manifest["inputPackets"]["candidateFree"]["manifestSha256"]),
        (cf / "current-target-cells.jsonl", manifest["inputPackets"]["candidateFree"]["currentTargetCellsSha256"]),
        (cf / "source-queue.jsonl", manifest["inputPackets"]["candidateFree"]["sourceQueueSha256"]),
        (cf / "source-contexts.jsonl", manifest["inputPackets"]["candidateFree"]["sourceContextsSha256"]),
        (cf / "active-hold-reattestation.jsonl", manifest["inputPackets"]["candidateFree"]["activeHoldSha256"]),
        (cf / "previous-window-readback-reattestation-hash-only.jsonl", manifest["inputPackets"]["candidateFree"]["previousWindowReadbackSha256"]),
        (primary_dir / "summary.json", manifest["inputPackets"]["primary"]["summarySha256"]),
        (primary_dir / "primary-semantic-review-ledger.jsonl", manifest["inputPackets"]["primary"]["ledgerSha256"]),
        (blind_dir / "manifest.json", manifest["inputPackets"]["blind"]["manifestSha256"]),
        (blind_dir / "blind-review-ledger.jsonl", manifest["inputPackets"]["blind"]["ledgerSha256"]),
    ]
    for path, expected in input_hash_checks:
        require(digest(path.read_bytes()) == expected, f"input file pin mismatch: {path.name}")

    current_rows = read_jsonl(cf / "current-target-cells.jsonl")
    source_queue = {r["position"]: r for r in read_jsonl(cf / "source-queue.jsonl")}
    contexts = {r["position"]: r for r in read_jsonl(cf / "source-contexts.jsonl")}
    primary_rows = {(r["position"], r["locale"]): r for r in read_jsonl(primary_dir / "primary-semantic-review-ledger.jsonl")}
    blind_rows = {(r["position"], r["locale"]): r for r in read_jsonl(blind_dir / "blind-review-ledger.jsonl")}
    integrated = read_jsonl(out_dir / "integrated-cross-ledger.jsonl")
    current_keys = [(r["position"], r["locale"]) for r in current_rows]
    integrated_map = {(r["position"], r["locale"]): r for r in integrated}
    require(len(current_rows) == 240 and len(integrated) == 240, "cell count is not 240")
    require(len(set(current_keys)) == 240 and len(integrated_map) == 240, "duplicate cell key")
    require(set(integrated_map) == set(primary_rows) == set(blind_rows) == set(current_keys), "cell key coverage differs")
    require(sorted({p for p, _ in current_keys}) == list(range(1783, 1803)), "window positions differ")
    require(len(contexts) == 20, "source/caller context count differs")

    final_counts = Counter()
    origin_counts = Counter()
    baseline_counts = Counter()
    selected_counts = Counter({"placeholder": 0, "markup": 0, "numeric": 0, "protectedLiteral": 0})
    review_flags = []
    for current in current_rows:
        pos, locale = current["position"], current["locale"]
        key = (pos, locale)
        row = integrated_map[key]
        source = row["source"]
        current_out = row["current"]
        primary = primary_rows[key]
        blind = blind_rows[key]
        ctx = contexts[pos]

        require((row["head"], row["tree"]) == (HEAD, TREE), f"row head/tree mismatch at {pos}/{locale}")
        require(row["window"] == "W1783-W1802", f"row window mismatch at {pos}/{locale}")
        require(source["text"] == current["sourceKey"] == source_queue[pos]["sourceKey"], f"source text mismatch at {pos}/{locale}")
        require(source["sha256"] == current["sourceKeySha256"] == source_queue[pos]["sourceKeySha256"], f"source hash mismatch at {pos}/{locale}")
        require(source["callerContextSha256"] == current["sourceContextSha256"] == ctx["callerContextSha256"], f"caller context mismatch at {pos}/{locale}")
        require(source["callerReferences"] == caller_pins(ctx), f"caller reference pin mismatch at {pos}/{locale}")
        require(source["callerOccurrenceCount"] == ctx["callerOccurrenceCount"], f"caller occurrence mismatch at {pos}/{locale}")
        require(source["callerReferenceCount"] == ctx["productionCallerCount"] == current["callerCount"], f"caller reference count mismatch at {pos}/{locale}")
        require(current_out["text"] == current["currentTarget"], f"current target text mismatch at {pos}/{locale}")
        require(current_out["sha256"] == current["currentTargetSha256"] == digest(current_out["text"].encode("utf-8")), f"current target hash mismatch at {pos}/{locale}")
        require(current_out["type"] == current["currentTargetType"], f"current target type mismatch at {pos}/{locale}")
        require(current_out["catalogPath"] == current["catalogPath"], f"catalog path mismatch at {pos}/{locale}")
        require(current_out["catalogFileSha256"] == current["catalogFileSha256"], f"catalog file hash mismatch at {pos}/{locale}")
        require(current_out["catalogGitBlob"] == current["catalogGitBlob"], f"catalog blob mismatch at {pos}/{locale}")
        require(primary["currentTarget"] == current_out["text"] and primary["currentTargetSha256"] == current_out["sha256"], f"primary baseline mismatch at {pos}/{locale}")
        require(primary["sourceKeySha256"] == source["sha256"] and primary["callerContextSha256"] == source["callerContextSha256"], f"primary source/context pin mismatch at {pos}/{locale}")
        require(primary["proposedTarget"] == row["reviews"]["primary"]["proposal"], f"primary proposal mismatch at {pos}/{locale}")
        require(primary["proposedTargetSha256"] == row["reviews"]["primary"]["proposalSha256"] == digest(primary["proposedTarget"].encode("utf-8")), f"primary proposal hash mismatch at {pos}/{locale}")
        require(blind["sourceKey"] == source["text"] and blind["sourceContextSha256"] == source["callerContextSha256"], f"blind source/context pin mismatch at {pos}/{locale}")
        require(blind["status"] == row["reviews"]["blind"]["status"], f"blind status mismatch at {pos}/{locale}")
        require(blind["issueCodes"] == row["reviews"]["blind"]["issueCodes"], f"blind issue codes mismatch at {pos}/{locale}")
        suggestion = blind.get("reviewerSuggestionUnapproved")
        require(suggestion == row["reviews"]["blind"]["proposal"], f"blind proposal mismatch at {pos}/{locale}")
        expected_suggestion_hash = digest(suggestion.encode("utf-8")) if isinstance(suggestion, str) else None
        require(row["reviews"]["blind"]["proposalSha256"] == expected_suggestion_hash, f"blind proposal hash mismatch at {pos}/{locale}")
        require(row["reviews"]["primary"]["nativeSpeakerApproval"] is False and row["reviews"]["blind"]["nativeSpeakerApproval"] is False, f"native-speaker status mismatch at {pos}/{locale}")

        selected = row["adjudication"]
        require(selected["nativeSpeakerApproval"] is False, f"selected native-speaker status mismatch at {pos}/{locale}")
        require(selected["selectedTargetSha256"] == digest(selected["selectedTarget"].encode("utf-8")), f"selected target hash mismatch at {pos}/{locale}")
        if selected["targetOrigin"] == "current":
            require(selected["selectedTarget"] == current_out["text"], f"current-origin selection mismatch at {pos}/{locale}")
        elif selected["targetOrigin"] == "primary":
            require(selected["selectedTarget"] == primary["proposedTarget"], f"primary-origin selection mismatch at {pos}/{locale}")
        elif selected["targetOrigin"] == "blind":
            require(selected["selectedTarget"] == suggestion, f"blind-origin selection mismatch at {pos}/{locale}")
        elif selected["targetOrigin"] == "primary_and_blind":
            require(selected["selectedTarget"] == primary["proposedTarget"] == suggestion, f"convergent selection mismatch at {pos}/{locale}")
        else:
            raise SystemExit(f"FAIL: unknown target origin at {pos}/{locale}")

        audit = token_audit(current, selected["selectedTarget"])
        require(selected["selectedTokenAudit"] == audit, f"selected token audit mismatch at {pos}/{locale}")
        for name, key_name in [
            ("placeholder", "placeholderSequenceMatches"),
            ("markup", "markupMatches"),
            ("numeric", "numericTokensMatch"),
            ("protectedLiteral", "protectedLiteralsMatch"),
        ]:
            if not audit[key_name]:
                selected_counts[name] += 1
        require(all(audit[name] for name in ["placeholderSequenceMatches", "markupMatches", "numericTokensMatch", "protectedLiteralsMatch"]), f"selected token mismatch at {pos}/{locale}")

        for variant in current_out["tokenEvidence"]:
            if not variant["placeholderSequenceMatches"]:
                baseline_counts["placeholder"] += 1
            if not variant["markupMatches"]:
                baseline_counts["markup"] += 1
            if not variant["numericTokensMatch"]:
                baseline_counts["numeric"] += 1
            if not variant["protectedLiteralsMatch"]:
                baseline_counts["protectedLiteral"] += 1
        final_counts[selected["disposition"]] += 1
        origin_counts[selected["targetOrigin"]] += 1
        if selected["disposition"] == "hold":
            require(selected["mode"] == "hold" and selected["selectedTargetSha256"] == current_out["sha256"], f"hold did not preserve current target at {pos}/{locale}")
        if blind["status"] == "review":
            resolution = "hold" if selected["disposition"] == "hold" else "resolved_provisionally"
            review_flags.append({
                "cellId": f"{pos}::{locale}",
                "blindIssueCodes": blind["issueCodes"],
                "resolution": resolution,
                "selectedTargetSha256": selected["selectedTargetSha256"],
            })

    require(dict(sorted(final_counts.items())) == manifest["dispositions"], "final disposition counts differ from manifest")
    require(dict(sorted(origin_counts.items())) == manifest["selectionOrigins"], "selection-origin counts differ from manifest")
    require(dict(sorted(baseline_counts.items())) == manifest["baselineTokenMismatchCountsRecomputed"], "baseline token mismatch counts differ")
    require(dict(sorted(selected_counts.items())) == manifest["selectedTokenMismatchCounts"], "selected token mismatch counts differ")
    require(len(review_flags) == manifest["localeReviewFlags"]["count"] == 5, "locale-review flag count differs")
    require(review_flags == manifest["localeReviewFlags"]["cells"], "locale-review resolution list differs")
    require(manifest["localeReviewFlags"]["resolvedProvisionally"] == 4 and manifest["localeReviewFlags"]["held"] == 1, "locale-review resolution count differs")
    require(manifest["holdCells"] == ["1792::ko"], "unexpected integrated hold cells")
    changed = sum(1 for row in integrated if row["adjudication"]["selectedTargetSha256"] != row["current"]["sha256"])
    require(changed == manifest["changedTargetCount"], "changed target count differs")
    require(manifest["nativeSpeakerApproval"] is False and manifest["productFilesEdited"] is False and manifest["testsBuildsScansCiRun"] is False, "approval/work status flags differ")

    # The source/caller evidence index is copied byte-for-byte from the sealed packet.
    require((out_dir / "source-caller-context-index.jsonl").read_bytes() == (cf / "source-contexts.jsonl").read_bytes(), "source/caller context index changed")

    active_path = cf / "active-hold-reattestation.jsonl"
    active_rows = read_jsonl(active_path)
    require((out_dir / "active-hold-reattestation.jsonl").read_bytes() == active_path.read_bytes(), "active hold record changed")
    require(len(active_rows) == 1, "carried active hold count differs")
    active = active_rows[0]
    require(active["holdId"] == "1719::id" and active["textIncluded"] is False, "prior active hold is not hash-only")
    require(all(k not in active for k in ["sourceKey", "sourceText", "currentTarget", "targetText"]), "prior hold contains source or target text")
    require(active["targetHashUnchanged"] is True and active["sourceContextUnchanged"] is True, "prior active hold attestation failed")
    require(manifest["carriedPriorActiveHold"]["holdId"] == "1719::id" and manifest["carriedPriorActiveHold"]["textIncluded"] is False, "manifest active-hold summary mismatch")

    previous_path = cf / "previous-window-readback-reattestation-hash-only.jsonl"
    require((out_dir / "previous-window-readback-reattestation-hash-only.jsonl").read_bytes() == previous_path.read_bytes(), "predecessor hash-only readbacks changed")
    previous = read_jsonl(previous_path)
    require(len(previous) == 240 and all(r["targetTextIncluded"] is False for r in previous), "predecessor readbacks are not 240 hash-only rows")
    require(all("sourceKey" not in r and "currentTarget" not in r and "targetText" not in r for r in previous), "predecessor file contains source/target text")
    require(manifest["previousWindowReadbackCount"] == 240 and manifest["previousWindowReadbacksTextIncluded"] is False, "predecessor lineage manifest mismatch")

    hold_record = read_json(out_dir / "hold-lineage.json")
    require(hold_record["carriedPriorActiveHold"] == active, "hold-lineage prior record mismatch")
    hold_rows = [r for r in integrated if r["adjudication"]["disposition"] == "hold"]
    new_holds = hold_record["newWindowHolds"]
    require(len(new_holds) == len(hold_rows), "new hold lineage count mismatch")
    require([r["cellId"] for r in new_holds] == [f'{r["position"]}::{r["locale"]}' for r in hold_rows], "new hold lineage cell mismatch")
    require(all(r["textIncluded"] is False for r in new_holds), "new hold lineage unexpectedly includes text")

    boundary = next(r for r in read_jsonl(cf / "source-window-boundaries.jsonl") if r.get("position") == 1803 and r.get("boundary") is True)
    require(boundary == manifest["nextBoundary"], "next boundary differs from source packet")
    require(boundary["sourceKeySha256"] == "46f390c945e7ff7e760db1cc63bed9f9429afa266c56413af8628ad801008175", "next source hash mismatch")

    out_entries = checksum_entries(out_dir)
    print(json.dumps({
        "result": "PASS",
        "verifiedCells": len(integrated),
        "dispositions": dict(sorted(final_counts.items())),
        "changedTargets": changed,
        "localeReviewFlags": manifest["localeReviewFlags"]["count"],
        "localeReviewFlagsResolvedProvisionally": manifest["localeReviewFlags"]["resolvedProvisionally"],
        "localeReviewFlagsHeld": manifest["localeReviewFlags"]["held"],
        "carriedActiveHold": "1719::id (hash-only)",
        "nextBoundaryPosition": boundary["position"],
        "outputFilesChecksumCovered": len(out_entries),
        "outputChecksumListSha256": digest((out_dir / "SHA256SUMS.txt").read_bytes()),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
