#!/usr/bin/env python3
"""Exact-hash application and full-catalog readback for slskR W1703-W1722."""

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
CROSS = WINDOW / "cross-review" / "cross-review.jsonl"
LEDGER = HERE / "root-final-review-ledger.jsonl"
PLAN = HERE / "exact-hash-apply-plan.jsonl"
TARGETS = HERE / "root-selected-targets.jsonl"
PREFLIGHT = HERE / "preflight.json"
READBACK = HERE / "final-head-readback.jsonl"
SUMMARY = HERE / "application-summary.json"
PINNED_HEAD = "91e109efba44ad9e53fe9544648a0d907a2bef77"
PINNED_TREE = "38db78228144da5fc50179addccf826662bf97de"
EXPECTED_CATALOG_KEYS = 5441


def sha(value: str | bytes | Any) -> str:
    if isinstance(value, str):
        data = value.encode("utf-8")
    elif isinstance(value, bytes):
        data = value
    else:
        data = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(data).hexdigest()


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

    cross = load_rows(CROSS)
    ledger = load_rows(LEDGER)
    plan = load_rows(PLAN)
    targets = load_rows(TARGETS)
    if len(cross) != 240 or len(ledger) != 240:
        raise SystemExit(f"expected 240 cross and root rows, got {len(cross)} and {len(ledger)}")
    if any(r["evidencePins"]["head"] != PINNED_HEAD or r["evidencePins"]["tree"] != PINNED_TREE for r in cross):
        raise SystemExit("cross packet does not match the pinned head/tree")
    if any(r["rootDisposition"] == "hold" and r["after"] != r["before"] for r in ledger):
        raise SystemExit("held cells must retain their current target")
    if sum(r["rootDisposition"] == "hold" for r in ledger) != 1:
        raise SystemExit("expected exactly one explicitly retained hold")
    if len(plan) != 69 or len(targets) != 69:
        raise SystemExit(f"expected 69 exact-hash edits and targets, got {len(plan)} and {len(targets)}")

    cross_by_id = {r["cellId"]: r for r in cross}
    ledger_by_id = {r["cellId"]: r for r in ledger}
    if len(cross_by_id) != 240 or set(cross_by_id) != set(ledger_by_id):
        raise SystemExit("cross and root ledgers do not contain the same unique cells")
    expected_plan: list[dict[str, Any]] = []
    for cell_id, row in ledger_by_id.items():
        cross_row = cross_by_id[cell_id]
        if row["sourceKey"] != cross_row["sourceKey"] or row["before"] != cross_row["currentTarget"]:
            raise SystemExit(f"root row changed the pinned source/current target at {cell_id}")
        if row["beforeSha256"] != sha(row["before"]) or row["afterSha256"] != sha(row["after"]):
            raise SystemExit(f"root row hash mismatch at {cell_id}")
        if row["crossDisposition"] != cross_row["crossDisposition"]:
            raise SystemExit(f"root row disposition mismatch at {cell_id}")
        if row["rootDisposition"] in ("correction", "refinement"):
            if row["after"] != cross_row["crossRecommendedTarget"]:
                raise SystemExit(f"root target diverges from cross-reviewed target at {cell_id}")
            expected_plan.append({
                "cellId": cell_id,
                "position": row["position"],
                "locale": row["locale"],
                "catalogPath": row["catalogPath"],
                "sourceKey": row["sourceKey"],
                "sourceKeySha256": row["sourceKeySha256"],
                "before": row["before"],
                "beforeSha256": row["beforeSha256"],
                "after": row["after"],
                "afterSha256": row["afterSha256"],
                "recommendationOrigin": row["recommendationOrigin"],
                "selectionRationale": row["selectionRationale"],
                "confidence": row["confidence"],
                "catalogFileSha256Before": cross_row["evidencePins"]["catalogFileSha256"],
            })
        elif row["rootDisposition"] == "accept-current":
            if row["after"] != row["before"]:
                raise SystemExit(f"accepted current cell was changed at {cell_id}")
        elif row["rootDisposition"] != "hold":
            raise SystemExit(f"unsupported root disposition {row['rootDisposition']} at {cell_id}")
    if plan != expected_plan or targets != expected_plan:
        raise SystemExit("recorded exact-hash plan/targets differ from root decisions")
    if not args.verify_only:
        current_head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPO, text=True).strip()
        current_tree = subprocess.check_output(["git", "rev-parse", "HEAD^{tree}"], cwd=REPO, text=True).strip()
        if current_head != PINNED_HEAD or current_tree != PINNED_TREE:
            raise SystemExit(f"pre-apply head/tree mismatch: {current_head}/{current_tree}")

    locale_rows: dict[str, list[dict[str, Any]]] = {}
    for row in cross:
        locale_rows.setdefault(row["evidencePins"]["catalogPath"], []).append(row)
    if len(locale_rows) != 12:
        raise SystemExit(f"expected 12 locale catalogs, got {len(locale_rows)}")

    expected_catalogs: dict[str, dict[str, Any]] = {}
    baseline_hashes: dict[str, str] = {}
    for path, cells in locale_rows.items():
        baseline_bytes = git_show(PINNED_HEAD, path)
        expected_sha = cells[0]["evidencePins"]["catalogFileSha256"]
        if sha(baseline_bytes) != expected_sha:
            raise SystemExit(f"pinned catalog checksum mismatch: {path}")
        baseline = json.loads(baseline_bytes.decode("utf-8"))
        if not isinstance(baseline, dict) or len(baseline) != EXPECTED_CATALOG_KEYS:
            raise SystemExit(f"unexpected catalog shape/count in {path}: {len(baseline)}")
        if (json.dumps(baseline, ensure_ascii=False, indent=2) + "\n").encode("utf-8") != baseline_bytes:
            raise SystemExit(f"catalog serialization is not canonical in {path}")
        expected = copy.deepcopy(baseline)
        for cell in cells:
            key = cell["sourceKey"]
            if key not in expected or expected[key] != cell["currentTarget"]:
                raise SystemExit(f"pinned current target mismatch at {cell['cellId']}")
        for edit in (item for item in plan if item["catalogPath"] == path):
            if expected.get(edit["sourceKey"]) != edit["before"]:
                raise SystemExit(f"exact-hash guard failed at {edit['cellId']}")
            expected[edit["sourceKey"]] = edit["after"]
        expected_catalogs[path] = expected
        baseline_hashes[path] = sha(baseline_bytes)

    preflight = {
        "window": "W1703-W1722",
        "inputHead": PINNED_HEAD,
        "inputTree": PINNED_TREE,
        "reviewedCells": 240,
        "acceptedCurrent": 170,
        "selectedCorrectionsAndRefinements": len(plan),
        "heldUnchanged": 1,
        "catalogsPreflighted": len(expected_catalogs),
        "catalogEntriesPerLocale": EXPECTED_CATALOG_KEYS,
        "catalogHashes": baseline_hashes,
        "all240CurrentValuesMatched": True,
        "all69ExactHashGuardsPassed": True,
        "writeStartedAfterFullPreflight": True,
        "result": "PASS",
    }

    if args.verify_only:
        readback_rows = []
        for path, expected in expected_catalogs.items():
            expected_bytes = (json.dumps(expected, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
            actual_bytes = (REPO / path).read_bytes()
            if actual_bytes != expected_bytes:
                raise SystemExit(f"full-catalog readback mismatch: {path}")
            for cell in locale_rows[path]:
                value = expected[cell["sourceKey"]]
                root_row = ledger_by_id[cell["cellId"]]
                if value != root_row["after"]:
                    raise SystemExit(f"readback target differs from root decision at {cell['cellId']}")
                readback_rows.append({
                    "cellId": cell["cellId"],
                    "position": cell["position"],
                    "locale": cell["locale"],
                    "sourceKey": cell["sourceKey"],
                    "expected": root_row["after"],
                    "actual": value,
                    "matches": value == root_row["after"],
                    "rootDisposition": root_row["rootDisposition"],
                })
        if len(readback_rows) != 240:
            raise SystemExit(f"unexpected readback row count: {len(readback_rows)}")
        write_rows(READBACK, readback_rows)
        summary = {
            **preflight,
            "productHead": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPO, text=True).strip(),
            "productTree": subprocess.check_output(["git", "rev-parse", "HEAD^{tree}"], cwd=REPO, text=True).strip(),
            "catalogsMatchPinnedParentPlusExactPlan": True,
            "nonTargetValuesAndKeyOrderPreserved": True,
            "readbackCells": len(readback_rows),
            "changedCells": len(plan),
            "unchangedCells": 171,
            "rootHoldCells": ["1719::id"],
        }
        SUMMARY.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        return 0

    PREFLIGHT.write_text(json.dumps(preflight, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if args.apply:
        for path, expected in expected_catalogs.items():
            (REPO / path).write_text(json.dumps(expected, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(preflight, ensure_ascii=False, indent=2))
        print("Catalogs written; commit the catalog milestone, then run --verify-only.")
        return 0
    print(json.dumps(preflight, ensure_ascii=False, indent=2))
    print("Preflight passed; no catalogs changed. Rerun with --apply to apply.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
