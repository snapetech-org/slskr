#!/usr/bin/env python3
"""Guarded apply and full-catalog readback for slskR W1683-W1702."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
WINDOW = HERE.parent
REPO = HERE.parents[4]
CROSS = WINDOW / "cross-review" / "cross-ledger.jsonl"
PLAN = HERE / "exact-hash-apply-plan.jsonl"
LEDGER = HERE / "root-final-review-ledger.jsonl"
ROOT_DECISIONS = HERE / "root-selected-targets.jsonl"
PINS = HERE / "input-pins.json"
PREFLIGHT = HERE / "preflight.json"
SUMMARY = HERE / "application-summary.json"
READBACK = HERE / "final-head-readback.jsonl"


def sha(data: Any) -> str:
    if isinstance(data, str):
        payload = data.encode("utf-8")
    elif isinstance(data, bytes):
        payload = data
    else:
        payload = json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def load_rows(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_rows(path: Path, rows: list[dict[str, Any]]) -> None:
    path.write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows), encoding="utf-8")


def git_show(head: str, path: str) -> bytes:
    return subprocess.check_output(["git", "show", f"{head}:{path}"], cwd=REPO)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--verify-only", action="store_true")
    args = parser.parse_args()

    rows = load_rows(CROSS)
    if len(rows) != 240:
        raise SystemExit(f"expected 240 cross-review cells, got {len(rows)}")
    head, tree = rows[0]["exactHead"], rows[0]["exactTree"]
    if any(row["exactHead"] != head or row["exactTree"] != tree for row in rows):
        raise SystemExit("cross-review rows do not share one exact head/tree")
    if not args.verify_only:
        current_head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPO, text=True).strip()
        if current_head != head:
            raise SystemExit(f"pre-apply head mismatch: {current_head} != {head}")

    dispositions = {"accept-current", "select-proposal"}
    final_rows: list[dict[str, Any]] = []
    plan: list[dict[str, Any]] = []
    for row in rows:
        if row["disposition"] not in dispositions:
            raise SystemExit(f"unsupported cross disposition {row['disposition']} at {row['cellId']}")
        source = row["sourceKey"]
        current = row["currentTarget"]
        target = row["selectedTarget"] if row["disposition"] == "select-proposal" else current
        target_hash = row["selectedTargetSha256"] if row["disposition"] == "select-proposal" else sha(current)
        if sha(source) != row["sourceKeySha256"] or sha(current) != row["currentTargetSha256"] or sha(target) != target_hash:
            raise SystemExit(f"source/current/target hash mismatch at {row['cellId']}")
        root_disposition = "correction" if target != current else "accept-current"
        final = {
            "cellId": row["cellId"],
            "position": row["position"],
            "locale": row["locale"],
            "catalogPath": row["catalogPath"],
            "sourceKey": source,
            "sourceKeySha256": row["sourceKeySha256"],
            "before": current,
            "beforeSha256": row["currentTargetSha256"],
            "after": target,
            "afterSha256": sha(target),
            "disposition": root_disposition,
            "crossReviewDisposition": row["disposition"],
            "selectedProposalSource": row["selectedProposalSource"],
            "selectionRationale": row["selectionRationale"] if root_disposition == "correction" else "Independent cross-review accepted the current translation.",
            "confidence": row["confidence"],
            "callerReferenceCount": row["callerReferenceCount"],
            "callerOccurrenceCount": row["callerOccurrenceCount"],
        }
        final_rows.append(final)
        if root_disposition == "correction":
            plan.append({
                "cellId": row["cellId"],
                "position": row["position"],
                "locale": row["locale"],
                "catalogPath": row["catalogPath"],
                "sourceKey": source,
                "sourceKeySha256": row["sourceKeySha256"],
                "before": current,
                "beforeSha256": row["currentTargetSha256"],
                "after": target,
                "afterSha256": sha(target),
                "selectedProposalSource": row["selectedProposalSource"],
                "selectionRationale": row["selectionRationale"],
                "confidence": row["confidence"],
                "catalogFileSha256Before": row["catalogFileSha256"],
            })
    if len(plan) != 8 or sum(r["disposition"] == "accept-current" for r in final_rows) != 232:
        raise SystemExit(f"expected 8 corrections and 232 current accepts, got {len(plan)}")
    if len({row["cellId"] for row in plan}) != len(plan):
        raise SystemExit("duplicate edit in exact-hash plan")

    root_decisions = [{
        "cellId": r["cellId"],
        "position": r["position"],
        "locale": r["locale"],
        "sourceKey": r["sourceKey"],
        "before": r["before"],
        "after": r["after"],
        "afterSha256": r["afterSha256"],
        "selectedProposalSource": r["selectedProposalSource"],
        "rationale": r["selectionRationale"],
        "confidence": r["confidence"],
        "rootAdjudicationPerformed": True,
    } for r in plan]

    locale_paths: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        locale_paths.setdefault(row["catalogPath"], []).append(row)
    if len(locale_paths) != 12:
        raise SystemExit(f"expected 12 locale catalogs, got {len(locale_paths)}")
    expected_catalogs: dict[str, Any] = {}
    baseline_hashes: dict[str, str] = {}
    for path, cells in locale_paths.items():
        baseline_bytes = git_show(head, path)
        if sha(baseline_bytes) != cells[0]["catalogFileSha256"]:
            raise SystemExit(f"baseline catalog hash mismatch: {path}")
        baseline = json.loads(baseline_bytes.decode("utf-8"))
        if not isinstance(baseline, dict) or len(baseline) != 5441:
            raise SystemExit(f"unexpected catalog key count/shape in {path}")
        if (json.dumps(baseline, ensure_ascii=False, indent=2) + "\n").encode("utf-8") != baseline_bytes:
            raise SystemExit(f"catalog serialization differs from canonical form in {path}")
        expected = copy.deepcopy(baseline)
        for cell in cells:
            source = cell["sourceKey"]
            if source not in expected:
                raise SystemExit(f"source key missing from {path}: {source!r}")
            if expected[source] != cell["currentTarget"]:
                raise SystemExit(f"current target mismatch in {path}: {source!r}")
        for edit in (p for p in plan if p["catalogPath"] == path):
            if expected.get(edit["sourceKey"]) != edit["before"]:
                raise SystemExit(f"exact-hash guard failed in {path}: {edit['sourceKey']!r}")
            expected[edit["sourceKey"]] = edit["after"]
        expected_catalogs[path] = expected
        baseline_hashes[path] = sha(baseline_bytes)

    pins = {
        "window": "W1683-W1702",
        "remainingQueueRankRange": [1683, 1702],
        "inputHead": head,
        "inputTree": tree,
        "baseHead": rows[0]["exactHead"],
        "sourceCount": 20,
        "localeCount": 12,
        "reviewedCellCount": 240,
        "rootSelectedCorrections": len(plan),
        "acceptedCurrent": 232,
        "locales": sorted({r["locale"] for r in rows}),
    }

    if args.verify_only:
        if load_rows(PLAN) != plan or load_rows(LEDGER) != final_rows or load_rows(ROOT_DECISIONS) != root_decisions:
            raise SystemExit("recorded final decisions differ from cross-review and root adjudication")
        readback_rows = []
        for path, expected in expected_catalogs.items():
            expected_bytes = (json.dumps(expected, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
            actual_bytes = (REPO / path).read_bytes()
            if actual_bytes != expected_bytes:
                raise SystemExit(f"full-catalog readback mismatch: {path}")
            for cell in locale_paths[path]:
                value = actual_bytes and expected[cell["sourceKey"]]
                target = next((e["after"] for e in plan if e["catalogPath"] == path and e["sourceKey"] == cell["sourceKey"]), cell["currentTarget"])
                if value != target:
                    raise SystemExit(f"cell readback mismatch: {cell['cellId']}")
                readback_rows.append({
                    "cellId": cell["cellId"],
                    "position": cell["position"],
                    "locale": cell["locale"],
                    "sourceKey": cell["sourceKey"],
                    "expected": target,
                    "actual": value,
                    "matches": value == target,
                })
        if len(readback_rows) != 240:
            raise SystemExit(f"unexpected readback rows: {len(readback_rows)}")
        write_rows(READBACK, readback_rows)
        summary = {
            **pins,
            "result": "PASS",
            "productHead": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPO, text=True).strip(),
            "productTree": subprocess.check_output(["git", "rev-parse", "HEAD^{tree}"], cwd=REPO, text=True).strip(),
            "catalogsReadBack": len(expected_catalogs),
            "catalogEntriesPerLocale": 5441,
            "catalogsMatchPinnedParentPlusExactPlan": True,
            "nonTargetValuesAndKeyOrderPreserved": True,
            "readbackCells": len(readback_rows),
            "changedCells": len(plan),
            "unchangedCells": 232,
            "baselineCatalogHashes": baseline_hashes,
        }
        SUMMARY.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        return 0

    write_rows(PLAN, plan)
    write_rows(LEDGER, final_rows)
    write_rows(ROOT_DECISIONS, root_decisions)
    PINS.write_text(json.dumps(pins, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    preflight = {
        **pins,
        "result": "PASS",
        "catalogsPreflighted": len(expected_catalogs),
        "catalogHashes": baseline_hashes,
        "all240CurrentValuesMatched": True,
        "all8ExactHashGuardsPassed": True,
        "writeStartedAfterFullPreflight": True,
    }
    PREFLIGHT.write_text(json.dumps(preflight, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if args.apply:
        for path, expected in expected_catalogs.items():
            (REPO / path).write_text(json.dumps(expected, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(preflight, ensure_ascii=False, indent=2))
        print("Catalogs written; commit the catalog milestone, then rerun with --verify-only.")
        return 0
    print(json.dumps(preflight, ensure_ascii=False, indent=2))
    print("Preflight passed; no catalogs changed. Rerun with --apply to apply.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
