#!/usr/bin/env python3
from __future__ import annotations
import argparse
import copy
import hashlib
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
WINDOW = HERE.parent
REPO = HERE.parents[4]
CROSS_DIR = WINDOW / "cross-review"
CROSS = CROSS_DIR / "cross-review-ledger.jsonl"
LEDGER = HERE / "root-final-review-ledger.jsonl"
PLAN = HERE / "exact-hash-apply-plan.jsonl"
TARGETS = HERE / "root-selected-targets.jsonl"
DECISIONS = HERE / "root-decisions.json"
PREFLIGHT = HERE / "preflight.json"
READBACK = HERE / "final-head-readback.jsonl"
SUMMARY = HERE / "application-summary.json"
PINNED_HEAD = "ccbc3dc721c1cbd225d4e512f4f0af4c80476620"
PINNED_TREE = "075d1b72a2fd080404ebec19d354cb863638df21"
EXPECTED_CATALOG_KEYS = 5441

def sha(value):
    if isinstance(value, str):
        data = value.encode("utf-8")
    elif isinstance(value, bytes):
        data = value
    else:
        data = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(data).hexdigest()

def read_rows(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]

def write_rows(path, values):
    path.write_text("".join(json.dumps(v, ensure_ascii=False, sort_keys=True) + "\n" for v in values), encoding="utf-8")

def git_show(path):
    return subprocess.check_output(["git", "show", f"{PINNED_HEAD}:{path}"], cwd=REPO)

def require(ok, message):
    if not ok:
        raise SystemExit(message)

def run_cross_verifier():
    result = subprocess.run([sys.executable, str(CROSS_DIR / "verify_cross_packet.py")], cwd=CROSS_DIR, capture_output=True, text=True, check=True)
    require('"result": "PASS"' in result.stdout, "cross packet verifier did not report PASS")
    return json.loads(result.stdout)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--verify-only", action="store_true")
    args = parser.parse_args()
    require(not (args.apply and args.verify_only), "choose either --apply or --verify-only")
    cross_summary = run_cross_verifier()
    cross = read_rows(CROSS)
    root = read_rows(LEDGER)
    plan = read_rows(PLAN)
    targets = read_rows(TARGETS)
    require(len(cross) == len(root) == 240, "expected 240 cross/root rows")
    require(len(plan) == len(targets) == 34, "expected 34 exact-hash changes and selected targets")
    require(len({(r["position"], r["locale"]) for r in cross}) == 240, "duplicate cross cell")
    require(len({(r["position"], r["locale"]) for r in root}) == 240, "duplicate root cell")
    cross_by_id = {(r["position"], r["locale"]): r for r in cross}
    root_by_id = {(r["position"], r["locale"]): r for r in root}
    require(set(cross_by_id) == set(root_by_id), "cross and root coverage differ")
    require(cross_summary["crossCells"] == 240, "cross verifier cell count mismatch")
    current_head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPO, text=True).strip()
    current_tree = subprocess.check_output(["git", "rev-parse", "HEAD^{tree}"], cwd=REPO, text=True).strip()
    if args.verify_only:
        ancestor = subprocess.run(["git", "merge-base", "--is-ancestor", PINNED_HEAD, "HEAD"], cwd=REPO)
        require(ancestor.returncode == 0, "pinned input head is not an ancestor of current HEAD")
    else:
        require(current_head == PINNED_HEAD and current_tree == PINNED_TREE, f"input head/tree mismatch: {current_head}/{current_tree}")
    expected_plan = []
    catalogs = {}
    for key, cross_row in cross_by_id.items():
        root_row = root_by_id[key]
        pos, locale = key
        cell = f"W1743-W1762:{pos}:{locale}"
        require(root_row["cellId"] == cell, f"cell ID mismatch at {key}")
        require(root_row["catalogPath"] == cross_row["catalogPath"], f"catalog path mismatch at {key}")
        require(root_row["crossDisposition"] == cross_row["crossDisposition"], f"cross disposition mismatch at {key}")
        if cross_row["hashOnly"]:
            require(root_row["rootDisposition"] == "hold" and root_row.get("hashOnly") is True, f"hash-only row not held at {key}")
            require("sourceKey" not in root_row and "before" not in root_row and "after" not in root_row, f"hash-only text leaked at {key}")
            require(root_row["beforeSha256"] == root_row["afterSha256"] == cross_row["currentTargetSha256"], f"hash-only hold changed at {key}")
            continue
        path = cross_row["catalogPath"]
        catalogs.setdefault(path, []).append(cross_row)
        require(root_row["sourceKey"] == cross_row["sourceKey"], f"source key mismatch at {key}")
        baseline_bytes = git_show(path)
        require(sha(baseline_bytes) == cross_row["catalogFileSha256"], f"pinned catalog hash mismatch: {path}")
        baseline = json.loads(baseline_bytes.decode("utf-8"))
        require(root_row["sourceKey"] in baseline, f"source key absent from catalog at {key}")
        before = baseline[root_row["sourceKey"]]
        require(sha(before) == cross_row["currentTargetSha256"] == root_row["beforeSha256"], f"current target hash mismatch at {key}")
        require(root_row["before"] == before, f"root before value mismatch at {key}")
        require(sha(root_row["after"]) == root_row["afterSha256"], f"root after hash mismatch at {key}")
        if root_row["rootDisposition"] in ("correction", "refinement"):
            require(root_row["after"] != before, f"selected edit is unchanged at {key}")
            if root_row["recommendationOrigin"] == "cross-review":
                require(root_row["after"] == cross_row["crossRecommendation"], f"root target differs from cross recommendation at {key}")
            elif key == (1743, "hi"):
                require(root_row["after"] == "फ़ाइल नाम आवश्यक है।", f"unexpected Hindi punctuation adjustment at {key}")
            else:
                raise SystemExit(f"unrecognized root override at {key}")
            expected_plan.append({
                "cellId": cell, "position": pos, "locale": locale, "catalogPath": path,
                "sourceKey": root_row["sourceKey"], "sourceKeySha256": cross_row["sourceKeySha256"],
                "before": before, "beforeSha256": sha(before), "after": root_row["after"],
                "afterSha256": sha(root_row["after"]), "recommendationOrigin": root_row["recommendationOrigin"],
                "selectionRationale": root_row["selectionRationale"], "confidence": root_row["confidence"],
                "catalogFileSha256Before": cross_row["catalogFileSha256"],
            })
        else:
            require(root_row["rootDisposition"] == "accept-current", f"unsupported root disposition at {key}")
            require(root_row["after"] == before and root_row["afterSha256"] == sha(before), f"accepted current target changed at {key}")
    expected_plan.sort(key=lambda row: (row["position"], row["locale"]))
    require(plan == expected_plan and targets == expected_plan, "recorded plan differs from root decisions")
    require(len(catalogs) == 12, f"expected 12 locale catalogs, got {len(catalogs)}")
    baseline_catalogs = {}
    expected_catalogs = {}
    baseline_hashes = {}
    for path, cells in catalogs.items():
        data = git_show(path)
        require(sha(data) == cells[0]["catalogFileSha256"], f"catalog checksum mismatch: {path}")
        baseline = json.loads(data.decode("utf-8"))
        require(isinstance(baseline, dict) and len(baseline) == EXPECTED_CATALOG_KEYS, f"catalog key count mismatch: {path}")
        require((json.dumps(baseline, ensure_ascii=False, indent=2) + "\n").encode("utf-8") == data, f"noncanonical catalog serialization: {path}")
        expected = copy.deepcopy(baseline)
        for edit in (item for item in expected_plan if item["catalogPath"] == path):
            require(expected.get(edit["sourceKey"]) == edit["before"], f"exact-hash guard failed at {edit['cellId']}")
            expected[edit["sourceKey"]] = edit["after"]
        baseline_catalogs[path] = baseline
        expected_catalogs[path] = expected
        baseline_hashes[path] = sha(data)
    preflight = {
        "window": "W1743-W1762", "inputHead": PINNED_HEAD, "inputTree": PINNED_TREE,
        "reviewedCells": 240, "acceptedCurrent": 182, "selectedCorrectionsAndRefinements": len(expected_plan),
        "heldUnchangedHashOnly": 24, "activeHoldIdHashOnly": "1719::id",
        "catalogsPreflighted": len(expected_catalogs), "catalogEntriesPerLocale": EXPECTED_CATALOG_KEYS,
        "catalogHashes": baseline_hashes, "all216CallerBackedCurrentValuesMatched": True,
        "all34ExactHashGuardsPassed": True, "crossAndInputPacketVerifiersPassed": True,
        "writeStartsAfterFullPreflight": True, "result": "PASS",
    }
    if args.verify_only:
        readback = []
        for path, expected in expected_catalogs.items():
            expected_bytes = (json.dumps(expected, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
            actual_bytes = (REPO / path).read_bytes()
            require(actual_bytes == expected_bytes, f"full-catalog exact-plan readback mismatch: {path}")
            actual = json.loads(actual_bytes.decode("utf-8"))
            require(list(actual) == list(baseline_catalogs[path]), f"catalog key order changed: {path}")
            for edit in (item for item in expected_plan if item["catalogPath"] == path):
                require(actual[edit["sourceKey"]] == edit["after"], f"selected target readback mismatch: {edit['cellId']}")
            for root_row in root:
                if root_row["catalogPath"] != path:
                    continue
                if root_row["hashOnly"]:
                    readback.append({
                        "cellId": root_row["cellId"], "position": root_row["position"], "locale": root_row["locale"],
                        "hashOnly": True, "expectedTargetSha256": root_row["beforeSha256"],
                        "targetTextIncluded": False, "matches": True,
                        "verificationMethod": "complete catalog equals pinned parent plus the 34 exact selected edits",
                    })
                else:
                    value = actual[root_row["sourceKey"]]
                    readback.append({
                        "cellId": root_row["cellId"], "position": root_row["position"], "locale": root_row["locale"],
                        "sourceKey": root_row["sourceKey"], "expected": root_row["after"], "actual": value,
                        "matches": value == root_row["after"], "rootDisposition": root_row["rootDisposition"],
                    })
        require(len(readback) == 240, f"unexpected readback row count: {len(readback)}")
        write_rows(READBACK, readback)
        summary = {
            **preflight, "productHead": current_head, "productTree": current_tree,
            "catalogsMatchPinnedParentPlusExactPlan": True, "nonTargetValuesAndKeyOrderPreserved": True,
            "readbackCells": len(readback), "changedCells": len(expected_plan), "unchangedCells": 206,
            "rootHindiPunctuationOverride": "फ़ाइल नाम आवश्यक है।",
            "nativeSpeakerSignoff": False, "headedBrowserAcceptance": False,
        }
        SUMMARY.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        return 0
    if not args.apply:
        for path in baseline_catalogs:
            require((REPO / path).read_bytes() == git_show(path), f"working catalog changed before preflight: {path}")
        PREFLIGHT.write_text(json.dumps(preflight, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(preflight, ensure_ascii=False, indent=2))
        print("Preflight passed; no catalogs changed. Use --apply to apply the 34 exact-hash edits.")
        return 0
    for path in baseline_catalogs:
        require((REPO / path).read_bytes() == git_show(path), f"working catalog changed before application: {path}")
    PREFLIGHT.write_text(json.dumps(preflight, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    for path, expected in expected_catalogs.items():
        if any(edit["catalogPath"] == path for edit in expected_plan):
            (REPO / path).write_text(json.dumps(expected, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(preflight, ensure_ascii=False, indent=2))
    print("Applied 34 exact-hash catalog changes; run --verify-only before committing the product milestone.")
    return 0

if __name__ == "__main__":
    main()
