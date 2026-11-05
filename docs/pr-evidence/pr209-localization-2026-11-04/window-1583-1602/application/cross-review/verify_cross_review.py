#!/usr/bin/env python3
"""Verify the W1583-W1602 cross-review using only its three declared inputs."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from collections import Counter
from pathlib import Path

HEAD = "e1ccc3d6509baf957f3039046e5b66dda3ae15d0"
TREE = "d7c7aa967cb7faf51a8211a397859feebe8129b8"
LOCALES = ["es", "zh-Hans", "hi", "de", "ja", "fr", "pt-BR", "ar", "ko", "zh-Hant", "vi", "id"]
START, END = 1583, 1602
OUTPUT_FILES = {"cross-review.json", "README.md", "verify_cross_review.py"}
EXPECTED_CROSS = {
    (1585, "pt-BR"): ("propose-refinement", "Não foi possível carregar as salas em que você entrou"),
    (1590, "zh-Hant"): ("propose-correction", "無法載入網格統計資料"),
    (1592, "zh-Hant"): ("propose-refinement", "無法載入待處理的請求"),
    (1595, "vi"): ("propose-correction", "Không thể tải số liệu thống kê xuất bản của pod:"),
}
TOKEN_FIELDS = (
    "sourcePlaceholders", "currentTargetPlaceholders", "sourceMarkupTags", "currentTargetMarkupTags",
    "sourceNumericTokens", "currentTargetNumericTokens", "sourceProtectedLiterals",
    "currentTargetProtectedLiterals", "protectedLiteralMismatchTokens",
)


def sha(data: bytes | str) -> str:
    if isinstance(data, str):
        data = data.encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def sidecar(directory: Path, sidecar_name: str = "SHA256SUMS.txt") -> dict[str, str]:
    listed: dict[str, str] = {}
    for line in (directory / sidecar_name).read_text(encoding="utf-8").splitlines():
        match = re.fullmatch(r"([0-9a-f]{64})  ([A-Za-z0-9_.-]+)", line)
        if not match:
            raise ValueError(f"malformed checksum entry in {directory / sidecar_name}")
        digest, name = match.groups()
        if name in listed:
            raise ValueError(f"duplicate checksum entry: {directory / name}")
        if not (directory / name).is_file() or sha((directory / name).read_bytes()) != digest:
            raise ValueError(f"checksum mismatch or missing file: {directory / name}")
        listed[name] = digest
    return listed


def token_signature(text: str):
    placeholders = re.findall(r"\{[A-Za-z][A-Za-z0-9_]*\}", text)
    markup = re.findall(r"</?[A-Za-z][^>]*>", text)
    numbers = re.findall(r"(?<![A-Za-z])\d+(?:[.,]\d+)?%?(?![A-Za-z])", text)
    literals = []
    pattern = r"(?<![A-Za-z0-9])(?:[A-Z]{2,}[A-Z0-9]*|ffmpeg|Chromaprint|Soulseek|Spotify|YouTube|Pushbullet|Matrix|WebSocket|OpenAI)(?![A-Za-z0-9])"
    for value in re.findall(pattern, text):
        if value not in literals:
            literals.append(value)
    return placeholders, markup, numbers, literals


def fail(message: str) -> None:
    raise ValueError(message)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate-input", type=Path, required=True)
    parser.add_argument("--primary-input", type=Path, required=True)
    parser.add_argument("--blind-input", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, default=Path(__file__).resolve().parent)
    args = parser.parse_args()
    candidate_dir = args.candidate_input.resolve()
    primary_dir = args.primary_input.resolve()
    blind_dir = args.blind_input.resolve()
    output_dir = args.output_dir.resolve()

    output_sidecar = sidecar(output_dir)
    if set(output_sidecar) != OUTPUT_FILES:
        fail("output checksum list must seal exactly README, packet, and verifier")

    candidate_sidecar = sidecar(candidate_dir)
    primary_sidecar = sidecar(primary_dir)
    blind_sidecar = sidecar(blind_dir)
    if set(primary_sidecar) != {
        "README.md", "SUMMARY.json", "build_primary.py", "holds.jsonl", "primary-ledger.jsonl",
        "proposals.jsonl", "verify-primary.py",
    }:
        fail("primary checksum list has an unexpected file set")
    if set(blind_sidecar) != {"review-packet.json", "review-process-exposure.json", "verify_review.py"}:
        fail("blind checksum list has an unexpected file set")

    packet = read_json(output_dir / "cross-review.json")
    if packet.get("schema") != "slskr-pr209-independent-cross-review/v1":
        fail("unexpected cross-review schema")
    binding = packet.get("binding", {})
    manifest = read_json(candidate_dir / "manifest.json")
    if (manifest.get("head"), manifest.get("tree")) != (HEAD, TREE):
        fail("candidate-free manifest differs from the requested head/tree")
    if (binding.get("head"), binding.get("tree")) != (HEAD, TREE) or binding.get("headTreeCopiedFromCandidateFreeManifest") is not True:
        fail("cross-review head/tree binding mismatch")
    if binding.get("candidateFreeChecksumListSha256") != sha((candidate_dir / "SHA256SUMS.txt").read_bytes()):
        fail("candidate-free checksum-list digest mismatch")
    if binding.get("primaryChecksumListSha256") != sha((primary_dir / "SHA256SUMS.txt").read_bytes()):
        fail("primary checksum-list digest mismatch")
    if binding.get("blindChecksumListSha256") != sha((blind_dir / "SHA256SUMS.txt").read_bytes()):
        fail("blind checksum-list digest mismatch")

    for name, digest in manifest.get("fileHashes", {}).items():
        if candidate_sidecar.get(name) != digest.get("sha256"):
            fail(f"candidate manifest checksum does not match sidecar: {name}")
    for name in ("PR-attestation.json", "PR-attestation-after.json"):
        attestation = read_json(candidate_dir / name)
        if (attestation.get("head"), attestation.get("tree")) != (HEAD, TREE):
            fail(f"PR attestation pin mismatch: {name}")
        if attestation.get("state") != "OPEN" or attestation.get("draft") is not True:
            fail(f"PR state changed in attestation: {name}")
    before, after = (read_json(candidate_dir / n) for n in ("PR-attestation.json", "PR-attestation-after.json"))
    for key in ("head", "tree", "headRef", "branchRef", "pullRef", "baseRef", "baseSha", "state", "draft", "deploymentsForHeadCount", "deploymentsForHeadSha256", "repositoryDeploymentCount", "repositoryDeploymentsSha256", "actionsRunsForHeadCount"):
        if before.get(key) != after.get(key):
            fail(f"PR attestations disagree on {key}")

    runtime = read_json(candidate_dir / "localization-runtime-context.json")
    if runtime.get("localeOptionOrder") != LOCALES:
        fail("runtime locale order mismatch")
    if (candidate_dir / "caller-resolution-holds.jsonl").read_bytes() != b"":
        fail("candidate-free packet contains caller-resolution holds")
    queue = read_jsonl(candidate_dir / "source-queue.jsonl")
    selected = [r for r in queue if START <= r.get("position", -1) <= END]
    if len(selected) != 20 or [r["position"] for r in selected] != list(range(START, END + 1)):
        fail("source queue does not contain the exact contiguous current window")
    if len({r["sourceKey"] for r in selected}) != 20:
        fail("selected source keys are not unique")

    contexts = {r["position"]: r for r in read_jsonl(candidate_dir / "source-contexts.jsonl")}
    current_rows = read_jsonl(candidate_dir / "current-target-cells.jsonl")
    primary_rows = read_jsonl(primary_dir / "primary-ledger.jsonl")
    primary_proposals = read_jsonl(primary_dir / "proposals.jsonl")
    blind_packet = read_json(blind_dir / "review-packet.json")
    exposure = read_json(blind_dir / "review-process-exposure.json")
    if exposure != {
        "schema": "slskr-pr209-review-process-exposure/v1",
        "genericPublicSearchCount": 1,
        "searchDescription": "One generic public search about Traditional Chinese wording.",
        "searchContentIncluded": False,
        "searchContentReliedOn": False,
        "accessedPRMaterials": False,
        "accessedCandidateMaterials": False,
        "accessedPriorReviewMaterials": False,
        "proposalInfluence": False,
    }:
        fail("blind process exposure note differs from disclosed scope")
    if blind_packet.get("binding", {}).get("candidateFreeChecksumListSha256") != binding.get("candidateFreeChecksumListSha256"):
        fail("blind packet is not bound to the same candidate-free checksum list")
    if (blind_packet.get("binding", {}).get("head"), blind_packet.get("binding", {}).get("tree")) != (HEAD, TREE):
        fail("blind packet head/tree binding mismatch")

    current = {(r["position"], r["locale"]): r for r in current_rows}
    primary = {(r["position"], r["locale"]): r for r in primary_rows}
    blind = {(r["position"], r["locale"]): r for r in blind_packet.get("cells", [])}
    cross_rows = packet.get("cells", [])
    cross = {(r.get("position"), r.get("locale")): r for r in cross_rows}
    expected_pairs = {(pos, locale) for pos in range(START, END + 1) for locale in LOCALES}
    if any(len(x) != 240 or set(x) != expected_pairs for x in (current, primary, blind, cross)):
        fail("current, primary, blind, and cross packets must each cover exactly 240 unique cells")
    if len(contexts) != 20 or set(contexts) != set(range(START, END + 1)):
        fail("caller context coverage mismatch")

    catalog_pins = read_json(candidate_dir / "catalog-file-pins.json")
    if (catalog_pins.get("head"), catalog_pins.get("tree")) != (HEAD, TREE):
        fail("catalog pins are not bound to the requested head/tree")
    for locale in LOCALES:
        pin = catalog_pins.get("localeCatalogs", {}).get(locale)
        if not pin:
            fail(f"missing locale catalog pin: {locale}")

    for pos in range(START, END + 1):
        if selected[pos - START]["sourceKey"] != contexts[pos]["sourceKey"]:
            fail(f"source queue/context mismatch at {pos}")
        if contexts[pos].get("callerResolutionHold"):
            fail(f"unresolved caller context at {pos}")

    for key in sorted(expected_pairs, key=lambda x: (x[0], LOCALES.index(x[1]))):
        pos, locale = key
        c, p, b, x = current[key], primary[key], blind[key], cross[key]
        context = contexts[pos]
        if c["sourceKey"] != context["sourceKey"] or c["sourceKeySha256"] != sha(c["sourceKey"]):
            fail(f"source key/hash mismatch at {pos}/{locale}")
        if c["currentTargetSha256"] != sha(c["currentTarget"]):
            fail(f"current target hash mismatch at {pos}/{locale}")
        if c["sourceContextSha256"] != context["callerContextSha256"]:
            fail(f"caller context hash mismatch at {pos}/{locale}")
        if c["callerCount"] != context["productionCallerCount"]:
            fail(f"caller count mismatch at {pos}/{locale}")
        pin = catalog_pins["localeCatalogs"][locale]
        if c.get("catalogPath") != pin.get("path") or c.get("catalogFileSha256") != pin.get("sha256"):
            fail(f"locale catalog file pin mismatch at {pos}/{locale}")
        if p.get("sourceKey") != c["sourceKey"] or p.get("sourceKeySha256") != c["sourceKeySha256"]:
            fail(f"primary source binding mismatch at {pos}/{locale}")
        if p.get("sourceContextSha256") != c["sourceContextSha256"] or p.get("currentTarget") != c["currentTarget"] or p.get("currentTargetSha256") != c["currentTargetSha256"]:
            fail(f"primary current target/context binding mismatch at {pos}/{locale}")
        if p.get("callerCount") != c["callerCount"]:
            fail(f"primary caller count mismatch at {pos}/{locale}")
        if b.get("sourceKey") != c["sourceKey"] or b.get("sourceSha256") != c["sourceKeySha256"]:
            fail(f"blind source binding mismatch at {pos}/{locale}")
        if b.get("currentTarget") != c["currentTarget"] or b.get("currentTargetSha256") != c["currentTargetSha256"]:
            fail(f"blind current target binding mismatch at {pos}/{locale}")
        if b.get("callerContextSha256") != c["sourceContextSha256"]:
            fail(f"blind caller context mismatch at {pos}/{locale}")
        if b.get("callerOccurrenceCount") != context["callerOccurrenceCount"] or b.get("productionCallerCount") != context["productionCallerCount"]:
            fail(f"blind caller counts mismatch at {pos}/{locale}")
        refs = [{"path": r["path"], "line": r["line"]} for r in context["callers"]]
        if x.get("callerRefs") != refs:
            fail(f"cross caller references mismatch at {pos}/{locale}")
        flags = {
            "placeholderSequenceMatches": c.get("placeholderSequenceMatches"),
            "markupMatches": c.get("markupMatches"),
            "numericTokensMatch": c.get("numericTokensMatch"),
            "protectedLiteralsMatch": c.get("protectedLiteralsMatch"),
        }
        if x.get("structuralFlags") != flags or not all(flags.values()):
            fail(f"structural flags mismatch at {pos}/{locale}")
        if any(c.get(field) for field in TOKEN_FIELDS):
            fail(f"source/current protected tokens are not empty at {pos}/{locale}")
        expected = EXPECTED_CROSS.get(key)
        expected_disposition, expected_target = expected if expected else ("accept-current", c["currentTarget"])
        if x.get("crossDisposition") != expected_disposition or x.get("crossTarget") != expected_target:
            fail(f"cross decision or target mismatch at {pos}/{locale}")
        if x.get("crossTargetSha256") != sha(expected_target):
            fail(f"cross target hash mismatch at {pos}/{locale}")
        if x.get("primaryDisposition") != p.get("disposition") or x.get("primarySelectedTargetSha256") != p.get("selectedTargetSha256"):
            fail(f"primary disposition/target audit mismatch at {pos}/{locale}")
        if x.get("blindDecision") != b.get("decision") or x.get("blindRecommendedTargetSha256") != b.get("recommendedTargetSha256"):
            fail(f"blind decision/target audit mismatch at {pos}/{locale}")
        if token_signature(c["sourceKey"]) != token_signature(c["currentTarget"]) or token_signature(c["sourceKey"]) != token_signature(expected_target):
            fail(f"placeholder, markup, numeric, or protected literal mismatch at {pos}/{locale}")
        if expected and not x.get("reviewNote"):
            fail(f"proposal has no cross-review rationale at {pos}/{locale}")

    counts = Counter(r["crossDisposition"] for r in cross_rows)
    expected_counts = {"accept-current": 236, "propose-correction": 2, "propose-refinement": 2, "text-free-hold": 0}
    actual_counts = {key: counts.get(key, 0) for key in expected_counts}
    if actual_counts != expected_counts:
        fail(f"cross disposition counts mismatch: {actual_counts}")
    summary = packet.get("summary", {})
    summary_counts = {
        "acceptCurrent": actual_counts["accept-current"],
        "proposeCorrection": actual_counts["propose-correction"],
        "proposeRefinement": actual_counts["propose-refinement"],
        "textFreeHold": actual_counts["text-free-hold"],
    }
    if any(summary.get(k) != v for k, v in summary_counts.items()):
        fail("summary counts do not match per-cell decisions")

    expected_proposals = []
    for r in primary_proposals:
        expected_proposals.append(("primary", r["position"], r["locale"], r["disposition"], r["selectedTarget"], r["selectedTargetSha256"]))
    for r in blind_packet["cells"]:
        if r["decision"] in ("correction", "refinement"):
            expected_proposals.append(("blind", r["position"], r["locale"], r["decision"], r["recommendedTarget"], r["recommendedTargetSha256"]))
    actual_proposals = packet.get("proposalAudit", [])
    if len(expected_proposals) != 6 or len(actual_proposals) != len(expected_proposals):
        fail("proposal audit must account for every primary and blind proposal instance")
    expected_set = set(expected_proposals)
    actual_set = {
        (r.get("reviewerPacket"), r.get("position"), r.get("locale"), r.get("submittedDecision"), r.get("submittedTarget"), r.get("submittedTargetSha256"))
        for r in actual_proposals
    }
    if actual_set != expected_set:
        fail("proposal audit entries do not match the submitted proposal set")
    for r in actual_proposals:
        key = (r["position"], r["locale"])
        if key not in EXPECTED_CROSS or r.get("crossDisposition") != EXPECTED_CROSS[key][0] or r.get("crossTargetSha256") != sha(EXPECTED_CROSS[key][1]) or r.get("auditResult") != "endorsed-target":
            fail(f"proposal adjudication mismatch at {key}")
    if packet.get("structuralAudit", {}).get("allCurrentStructuralFlagsTrue") is not True or packet["structuralAudit"].get("allProposalStructuralSignaturesMatchSource") is not True:
        fail("structural audit summary mismatch")

    print(json.dumps({"result": "PASS", "head": HEAD, "tree": TREE, "cells": 240, "counts": expected_counts, "uniqueCrossProposals": len(EXPECTED_CROSS), "proposalAuditInstances": len(actual_proposals), "inputSealsAndBindings": "verified"}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"cross-review verification failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
