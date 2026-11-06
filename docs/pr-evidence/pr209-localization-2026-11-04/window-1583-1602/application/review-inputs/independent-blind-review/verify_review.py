#!/usr/bin/env python3
"""Verify the independent blind review packet against its candidate-free inputs."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

EXPECTED_HEAD = "e1ccc3d6509baf957f3039046e5b66dda3ae15d0"
EXPECTED_TREE = "d7c7aa967cb7faf51a8211a397859feebe8129b8"
REQUIRED_INPUTS = {
    "manifest.json",
    "selected-source-keys.txt",
    "source-queue.jsonl",
    "source-contexts.jsonl",
    "caller-resolution-holds.jsonl",
    "localization-runtime-context.json",
    "current-target-cells.jsonl",
}
OUTPUT_FILES = {"review-packet.json", "verify_review.py", "review-process-exposure.json"}


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read_jsonl(path: Path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def fail(message: str) -> None:
    raise ValueError(message)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input-dir",
        type=Path,
        default=Path("/home/keith/Documents/code/task-scratch/slskr-pr209-w1583-1602-20261104/candidate-free-input"),
    )
    parser.add_argument("--output-dir", type=Path, default=Path(__file__).resolve().parent)
    args = parser.parse_args()
    input_dir = args.input_dir.resolve()
    output_dir = args.output_dir.resolve()

    packet_path = output_dir / "review-packet.json"
    sidecar_path = output_dir / "SHA256SUMS.txt"
    script_path = Path(__file__).resolve()
    if not packet_path.is_file() or not sidecar_path.is_file():
        fail("missing review packet or output SHA256SUMS.txt")

    sidecar = {}
    for line in sidecar_path.read_text(encoding="utf-8").splitlines():
        match = re.fullmatch(r"([0-9a-f]{64})  ([A-Za-z0-9_.-]+)", line)
        if not match:
            fail("malformed output SHA256SUMS.txt")
        digest, name = match.groups()
        if name in sidecar:
            fail(f"duplicate output checksum entry: {name}")
        sidecar[name] = digest
    if set(sidecar) != OUTPUT_FILES:
        fail("output SHA256SUMS.txt must seal exactly the packet and verifier")
    for name, expected in sidecar.items():
        if sha((output_dir / name).read_bytes()) != expected:
            fail(f"output checksum mismatch: {name}")
    if script_path != output_dir / "verify_review.py":
        fail("verifier is not running from the packet output directory")
    exposure = json.loads((output_dir / "review-process-exposure.json").read_text(encoding="utf-8"))
    expected_exposure = {
        "schema": "slskr-pr209-review-process-exposure/v1",
        "genericPublicSearchCount": 1,
        "searchDescription": "One generic public search about Traditional Chinese wording.",
        "searchContentIncluded": False,
        "searchContentReliedOn": False,
        "accessedPRMaterials": False,
        "accessedCandidateMaterials": False,
        "accessedPriorReviewMaterials": False,
        "proposalInfluence": False,
    }
    if exposure != expected_exposure:
        fail("review process exposure note differs from the disclosed scope")

    packet_bytes = packet_path.read_bytes()
    packet = json.loads(packet_bytes)
    if packet.get("schema") != "slskr-pr209-independent-blind-review/v1":
        fail("unexpected review packet schema")
    binding = packet.get("binding", {})
    checksum_list_path = input_dir / "SHA256SUMS.txt"
    checksum_list_bytes = checksum_list_path.read_bytes()
    if sha(checksum_list_bytes) != binding.get("candidateFreeChecksumListSha256"):
        fail("candidate-free checksum-list digest mismatch")
    listed = {}
    for line in checksum_list_bytes.decode("utf-8").splitlines():
        match = re.fullmatch(r"([0-9a-f]{64})  (.+)", line)
        if not match:
            fail("malformed candidate-free checksum list")
        digest, name = match.groups()
        if name in listed:
            fail(f"duplicate candidate-free checksum entry: {name}")
        listed[name] = digest
    input_checksums = binding.get("inputFiles", {})
    if set(input_checksums) != REQUIRED_INPUTS:
        fail("packet input checksum set does not match the permitted input set")
    for name, expected in input_checksums.items():
        path = input_dir / name
        if listed.get(name) != expected or sha(path.read_bytes()) != expected:
            fail(f"candidate-free input checksum mismatch: {name}")
    manifest = json.loads((input_dir / "manifest.json").read_text(encoding="utf-8"))
    manifest_head = manifest.get("head")
    manifest_tree = manifest.get("tree")
    if (manifest_head, manifest_tree) != (EXPECTED_HEAD, EXPECTED_TREE):
        fail("candidate-free manifest pin differs from the requested head/tree")
    if (binding.get("head"), binding.get("tree")) != (manifest_head, manifest_tree):
        fail("packet head/tree binding does not exactly match candidate-free manifest")
    if not binding.get("headTreeCopiedFromCandidateFreeManifest"):
        fail("packet must identify the candidate-free manifest as the head/tree binding source")

    selected_keys = {
        line.strip()
        for line in (input_dir / "selected-source-keys.txt").read_text(encoding="utf-8").splitlines()
        if line.strip()
    }
    queue = read_jsonl(input_dir / "source-queue.jsonl")
    window = [row for row in queue if 1583 <= row["position"] <= 1602]
    if len(window) != 20 or {row["sourceKey"] for row in window} != selected_keys:
        fail("selected-source-key/window mapping mismatch")
    contexts = {row["position"]: row for row in read_jsonl(input_dir / "source-contexts.jsonl")}
    targets = read_jsonl(input_dir / "current-target-cells.jsonl")
    runtime = json.loads((input_dir / "localization-runtime-context.json").read_text(encoding="utf-8"))
    locales = runtime.get("localeOptionOrder")
    expected_locales = ["es", "zh-Hans", "hi", "de", "ja", "fr", "pt-BR", "ar", "ko", "zh-Hant", "vi", "id"]
    if locales != expected_locales:
        fail("locale order changed from the reviewed direct-locale set")
    if (input_dir / "caller-resolution-holds.jsonl").read_bytes() != b"":
        fail("caller-resolution holds input is no longer empty")
    target_index = {(row["position"], row["locale"]): row for row in targets}
    if len(targets) != 240 or len(target_index) != 240:
        fail("candidate-free target input is not exactly 240 unique cells")

    rows = packet.get("cells", [])
    if len(rows) != 240:
        fail("packet does not contain 240 review decisions")
    row_index = {(row.get("position"), row.get("locale")): row for row in rows}
    expected_pairs = {(pos, locale) for pos in range(1583, 1603) for locale in locales}
    if len(row_index) != 240 or set(row_index) != expected_pairs:
        fail("packet coverage is incomplete or contains duplicate cells")
    context_rows = contexts
    counts = {"accept": 0, "correction": 0, "refinement": 0, "hold": 0}
    for key in sorted(expected_pairs):
        pos, locale = key
        reviewed = row_index[key]
        current = target_index[key]
        context = context_rows.get(pos)
        if context is None:
            fail(f"missing caller context at position {pos}")
        if reviewed.get("sourceKey") != current["sourceKey"]:
            fail(f"source text mismatch at {pos}/{locale}")
        if reviewed.get("sourceSha256") != current["sourceKeySha256"] or sha(reviewed["sourceKey"].encode("utf-8")) != current["sourceKeySha256"]:
            fail(f"source hash mismatch at {pos}/{locale}")
        if reviewed.get("currentTarget") != current["currentTarget"]:
            fail(f"current target text mismatch at {pos}/{locale}")
        if reviewed.get("currentTargetSha256") != current["currentTargetSha256"] or sha(reviewed["currentTarget"].encode("utf-8")) != current["currentTargetSha256"]:
            fail(f"current target hash mismatch at {pos}/{locale}")
        if reviewed.get("callerContextSha256") != context["callerContextSha256"]:
            fail(f"caller context hash mismatch at {pos}/{locale}")
        if reviewed.get("callerOccurrenceCount") != context["callerOccurrenceCount"] or reviewed.get("productionCallerCount") != context["productionCallerCount"]:
            fail(f"caller count mismatch at {pos}/{locale}")
        if current["sourceContextSha256"] != context["callerContextSha256"]:
            fail(f"current-target caller binding mismatch at {pos}/{locale}")
        structural_flags = ["placeholderSequenceMatches", "markupMatches", "numericTokensMatch", "protectedLiteralsMatch"]
        if not all(current.get(flag) is True for flag in structural_flags):
            fail(f"source/target structural mismatch at {pos}/{locale}")
        if any(current.get(name) for name in ["sourcePlaceholders", "currentTargetPlaceholders", "sourceMarkupTags", "currentTargetMarkupTags", "sourceNumericTokens", "currentTargetNumericTokens", "sourceProtectedLiterals", "currentTargetProtectedLiterals"]):
            fail(f"unexpected placeholder/markup/number/protected literal at {pos}/{locale}")
        decision = reviewed.get("decision")
        if decision not in counts:
            fail(f"invalid decision at {pos}/{locale}")
        counts[decision] += 1
        recommended = reviewed.get("recommendedTarget")
        recommended_hash = reviewed.get("recommendedTargetSha256")
        if decision in {"correction", "refinement"}:
            if not isinstance(recommended, str) or not isinstance(recommended_hash, str):
                fail(f"proposal text/hash missing at {pos}/{locale}")
            if sha(recommended.encode("utf-8")) != recommended_hash:
                fail(f"proposal hash mismatch at {pos}/{locale}")
            if not reviewed.get("rationale"):
                fail(f"proposal rationale missing at {pos}/{locale}")
        elif recommended is not None or recommended_hash is not None:
            fail(f"non-proposal decision contains a target string at {pos}/{locale}")
        if decision == "hold" and any(name in reviewed for name in ["recommendedTarget", "recommendedTargetSha256"]):
            fail(f"hold is not text-free at {pos}/{locale}")

    if packet.get("summary") != counts:
        fail("decision summary mismatch")
    structural = packet.get("structuralAudit", {})
    if structural.get("cellCount") != 240 or structural.get("allFlagsTrue") is not True:
        fail("packet structural audit summary mismatch")
    print(json.dumps({"ok": True, "cells": len(rows), "decisions": counts, "head": EXPECTED_HEAD, "tree": EXPECTED_TREE}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"verification failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
