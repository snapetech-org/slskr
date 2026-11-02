#!/usr/bin/env python3
"""Verify the eight exact-hash source-393 keep/hold dispositions."""
import argparse
import hashlib
import json
import subprocess
from pathlib import Path

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--repo", type=Path, required=True)
parser.add_argument("--prior-audit", type=Path, required=True)
args = parser.parse_args()
repo = args.repo.resolve()
audit = args.prior_audit.resolve()
bundle = Path("docs/pr-evidence/pr204-semantic-review-2026-11-01/independent-0383-0402-all-12-locales")
head = "ad7c283dfe84f31b52f5a27c363a605fe068e36c"
source_id = "Auto-Replace (automatic stuck-download replacement)"
expected = {"ar", "de", "es", "fr", "hi", "id", "zh-Hans", "zh-Hant"}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def git(*argv):
    return subprocess.check_output(["git", *argv], cwd=repo, text=True).strip()


def load_ref(ref):
    root = repo if ref["root"] == "pr-review-head" else audit
    path = (root / ref["path"]).resolve()
    if root not in path.parents:
        raise SystemExit(f"reference escapes pinned root: {ref}")
    lines = path.read_bytes().splitlines()
    if not 1 <= ref["line"] <= len(lines):
        raise SystemExit(f"reference line is missing: {ref}")
    raw = lines[ref["line"] - 1]
    if sha(raw) != ref["sha256"]:
        raise SystemExit(f"reference hash mismatch: {ref}")
    return json.loads(raw)


if git("rev-parse", f"{head}^{{tree}}") != "d0a2faeba016b57850767fe0903b67621d61bc6c":
    raise SystemExit("catalog head/tree pin mismatch")
ledger_path = repo / bundle / "held-dispositions.jsonl"
rows = [json.loads(line) for line in ledger_path.read_text(encoding="utf-8").splitlines() if line.strip()]
if len(rows) != 8 or {row["locale"] for row in rows} != expected:
    raise SystemExit("held disposition set does not match the eight root keeps")
seen = set()
prior_count = 0
for row in rows:
    cell = (row["source_id"], row["locale"])
    if cell in seen:
        raise SystemExit(f"duplicate held cell: {cell}")
    seen.add(cell)
    if (row["source_index"], row["source_id"], row["status"], row["disposition"]) != (393, source_id, "held", "held-current"):
        raise SystemExit(f"unexpected disposition: {row}")
    if row["native_speaker_approval"] is not False:
        raise SystemExit("native-speaker approval must remain false")
    if row["source_sha256"] != sha(source_id.encode("utf-8")):
        raise SystemExit(f"source hash mismatch: {cell}")
    catalog = json.loads(subprocess.check_output(["git", "show", f"{head}:{row['catalog_path']}"], cwd=repo))
    target = catalog[source_id]
    if target != row["target_text"] or sha(target.encode("utf-8")) != row["target_sha256"]:
        raise SystemExit(f"current target mismatch: {cell}")
    review_ref = {
        "root": "pr-review-head",
        "path": (bundle / "root-cross-review.jsonl").as_posix(),
        "line": row["root_cross_review_line"],
        "sha256": None,
    }
    review_path = repo / review_ref["path"]
    review_bytes = review_path.read_bytes().splitlines()[review_ref["line"] - 1]
    review_ref["sha256"] = sha(review_bytes)
    decision = load_ref(review_ref)
    if decision.get("decision") != "keep" or decision.get("locale") != row["locale"] or decision.get("sourceIndex") != 393:
        raise SystemExit(f"root disposition mismatch: {cell}")
    if decision.get("currentTargetSha256") != row["target_sha256"] or decision.get("sourceSha256") != row["source_sha256"]:
        raise SystemExit(f"root hash pin mismatch: {cell}")
    for ref in row["provisionalExactMatches"]:
        record = load_ref(ref)
        if record.get("locale") != row["locale"] or record.get("source_index", record.get("sourceIndex")) != 393:
            raise SystemExit(f"provisional row mismatch: {ref}")
    if row["locale"] in {"zh-Hans", "zh-Hant"}:
        if len(row["priorExactMatches"]) != 3:
            raise SystemExit(f"expected three prior conflict rows for {cell}")
    elif row["priorExactMatches"]:
        raise SystemExit(f"unexpected prior exact overlap for {cell}")
    for ref in row["priorExactMatches"]:
        record = load_ref(ref)
        if record.get("status") != "correction-needed" or record.get("locale") != row["locale"]:
            raise SystemExit(f"prior status mismatch: {ref}")
        if record.get("source_id", record.get("sourceId")) != source_id:
            raise SystemExit(f"prior source mismatch: {ref}")
        prior_count += 1
    if row["root_cross_review_sha256"] != sha((repo / bundle / "root-cross-review.jsonl").read_bytes()):
        raise SystemExit("root ledger file hash mismatch")

result = {
    "catalog_head": head,
    "catalog_tree": git("rev-parse", f"{head}^{{tree}}"),
    "source_id": source_id,
    "source_index": 393,
    "held_cells": len(rows),
    "held_locales": sorted(expected),
    "prior_correction_needed_rows_superseded": prior_count,
    "provisional_root_review_rows_pinned": sum(len(row["provisionalExactMatches"]) for row in rows),
    "held_ledger_sha256": sha(ledger_path.read_bytes()),
    "native_speaker_approval": False,
    "unintended_overlaps": 0,
    "all_pass": True,
}
print(json.dumps(result, ensure_ascii=False, indent=2))
