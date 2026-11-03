#!/usr/bin/env python3
"""Apply ratified slskR W1103-W1122 catalog values with exact-hash guards."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import tempfile
from pathlib import Path


ROOT = Path(subprocess.check_output(["git", "rev-parse", "--show-toplevel"], text=True).strip())
EVIDENCE = ROOT / "docs/pr-evidence/pr204-localization-2026-11-03/window-1103-1122"
INPUT = EVIDENCE / "clean-input"


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def git_blob_at_head(path: str) -> bytes:
    return subprocess.check_output(["git", "show", f"HEAD:{path}"], cwd=ROOT)


def dump_catalog(data: dict[str, str]) -> bytes:
    return (json.dumps(data, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def main() -> None:
    manifest = read_json(INPUT / "manifest.json")
    plan = read_json(EVIDENCE / "apply-plan.json")
    assert subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip() == manifest["head"]
    assert plan["head"] == manifest["head"] and plan["tree"] == manifest["tree"]
    assert plan["changeCount"] == len(plan["items"]) == 19

    ratified = [
        json.loads(line)
        for line in (EVIDENCE / "adjudication/ratified-ledger.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    approved = {
        (row["catalogFile"]["path"], row["sourceId"], row["locale"]): row
        for row in ratified
        if row["ratifiedDisposition"] == "RATIFY_PRIMARY_CANDIDATE"
    }
    assert len(approved) == 19
    for item in plan["items"]:
        row = approved[(item["catalogFile"], item["sourceId"], item["locale"])]
        assert row["callerEvidence"]["directLocalizedCaller"] is True
        assert item["currentTarget"] == row["currentTarget"]
        assert item["currentTargetSha256"] == row["currentTargetSha256"]
        assert item["target"] == row["proposedTarget"]
        assert item["targetSha256"] == row["proposedTargetSha256"]

    # Load exact baseline catalogs from the reviewed commit and ensure the live
    # worktree differs only by the planned values (also supports safe reruns).
    baseline: dict[str, dict[str, str]] = {}
    current: dict[str, dict[str, str]] = {}
    locale_paths = {}
    for path, pin in manifest["catalogPins"].items():
        locale = path.rsplit("ui-labels.", 1)[1].removesuffix(".json")
        locale_paths[locale] = path
        original_bytes = git_blob_at_head(path)
        assert sha256(original_bytes) == pin["sha256"], f"baseline hash changed: {path}"
        assert subprocess.check_output(["git", "rev-parse", f"HEAD:{path}"], cwd=ROOT, text=True).strip() == pin["gitBlob"]
        original = json.loads(original_bytes)
        live = json.loads((ROOT / path).read_text(encoding="utf-8"))
        assert list(live) == list(original), f"key order/set changed: {path}"
        baseline[path] = original
        current[path] = live

    expected_updates: dict[tuple[str, str], str] = {}
    for item in plan["items"]:
        path, key = item["catalogFile"], item["sourceId"]
        assert locale_paths[item["locale"]] == path
        before = item["currentTarget"]
        after = item["target"]
        assert sha256(before.encode("utf-8")) == item["currentTargetSha256"]
        assert sha256(after.encode("utf-8")) == item["targetSha256"]
        assert baseline[path][key] == before, f"baseline target changed: {path} {key}"
        assert current[path][key] in (before, after), f"unexpected target value: {path} {key}"
        expected_updates[(path, key)] = after

    # Verify no live worktree catalog contains any unrelated change.
    for path, live in current.items():
        original = baseline[path]
        for key in original:
            cell = (path, key)
            if cell in expected_updates:
                assert live[key] == original[key] or live[key] == expected_updates[cell], f"unplanned catalog change: {path} {key}"
            else:
                assert live[key] == original[key], f"unplanned catalog change: {path} {key}"

    updated = {path: dict(values) for path, values in current.items()}
    for (path, key), value in expected_updates.items():
        updated[path][key] = value

    cells = [
        json.loads(line)
        for line in (INPUT / "current-target-cells.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    assert len(cells) == 240
    assert len({(cell["sourceId"], cell["locale"]) for cell in cells}) == 240
    assert {cell["position"] for cell in cells} == set(range(1103, 1123))
    assert all(sum(cell["position"] == position for cell in cells) == 12 for position in range(1103, 1123))
    applied_keys = set(expected_updates)
    readback_rows = []
    mismatches = []
    for cell in cells:
        path = locale_paths[cell["locale"]]
        source = cell["sourceId"]
        assert cell["source"] == source
        assert sha256(source.encode("utf-8")) == cell["sourceSha256"]
        assert sha256(cell["currentTarget"].encode("utf-8")) == cell["currentTargetSha256"]
        assert baseline[path][source] == cell["currentTarget"], f"input target mismatch: {path} {source}"
        expected = expected_updates.get((path, source), cell["currentTarget"])
        actual = updated[path][source]
        row = {
            "sourceId": source,
            "sourceSha256": cell["sourceSha256"],
            "position": cell["position"],
            "locale": cell["locale"],
            "catalogFile": path,
            "inputCurrentTargetSha256": cell["currentTargetSha256"],
            "expected": expected,
            "expectedSha256": sha256(expected.encode("utf-8")),
            "actual": actual,
            "actualSha256": sha256(actual.encode("utf-8")),
            "changed": (path, source) in applied_keys,
        }
        readback_rows.append(row)
        if actual != expected:
            mismatches.append(row)
    assert not mismatches, json.dumps(mismatches[:3], ensure_ascii=False)

    changed_paths = sorted({path for path, _ in applied_keys})
    for path in changed_paths:
        destination = ROOT / path
        payload = dump_catalog(updated[path])
        with tempfile.NamedTemporaryFile(prefix=f".{destination.name}.w1103-1122-", dir=destination.parent, delete=False) as handle:
            temporary = Path(handle.name)
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        try:
            os.replace(temporary, destination)
        finally:
            temporary.unlink(missing_ok=True)

    catalog_summaries = {}
    for path in sorted(updated):
        live_bytes = (ROOT / path).read_bytes()
        live = json.loads(live_bytes)
        assert list(live) == list(baseline[path])
        catalog_summaries[path] = {
            "keyCount": len(live),
            "orderedKeySha256": sha256("\n".join(live).encode("utf-8")),
            "fileSha256": sha256(live_bytes),
        }

    readback = {
        "title": "Application readback: slskR PR #204 W1103-W1122",
        "repository": plan["repository"],
        "pullRequest": plan["pullRequest"],
        "baselineHead": manifest["head"],
        "window": plan["window"],
        "cellCount": len(readback_rows),
        "approvedChangeCount": len(applied_keys),
        "verifiedCellCount": len(readback_rows) - len(mismatches),
        "mismatchCount": len(mismatches),
        "changedCatalogCount": len(changed_paths),
        "catalogs": catalog_summaries,
        "rows": readback_rows,
    }
    (EVIDENCE / "readback.json").write_text(json.dumps(readback, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Applied {len(applied_keys)} exact-hash values across {len(changed_paths)} catalogs; verified {len(readback_rows)} cells.")


if __name__ == "__main__":
    main()
