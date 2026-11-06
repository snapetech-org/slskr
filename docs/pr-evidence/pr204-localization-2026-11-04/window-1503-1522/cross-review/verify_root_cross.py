#!/usr/bin/env python3
"""Verify the sealed root cross-ledger against its pinned review inputs."""
import hashlib
import json
from pathlib import Path
import re

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
HEAD = "a7d00cd97602c5910800330190817fcada008162"
TREE = "2d0a051348394e809ffc3a1fdbfccd20ba8af283"


def read_jsonl(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def sha(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


ledger = read_jsonl(HERE / "root-cross-ledger.jsonl")
current_rows = read_jsonl(ROOT / "candidate-free-input" / "current-target-cells.jsonl")
primary_rows = read_jsonl(ROOT / "primary-review" / "primary-ledger.jsonl")
blind_rows = read_jsonl(ROOT / "independent-clean-blind-review" / "output" / "blind-ledger.jsonl")
summary = json.loads((HERE / "summary.json").read_text(encoding="utf-8"))
context = json.loads((HERE / "adjudication-context.json").read_text(encoding="utf-8"))
assert len(ledger) == len(current_rows) == len(primary_rows) == len(blind_rows) == 240
assert summary["head"] == context["head"] == HEAD
assert summary["tree"] == context["tree"] == TREE
current = {(r["position"], r["locale"]): r for r in current_rows}
primary = {(r["position"], r["locale"]): r for r in primary_rows}
blind = {(r["position"], r["locale"]): r for r in blind_rows}
assert len(current) == 240
assert len(primary) == len(blind) == 240
assert len({(r["position"], r["locale"]) for r in ledger}) == 240

updates = 0
noops = 0
holds = 0
counts = {}
for row in ledger:
    key = (row["position"], row["locale"])
    c = current[key]
    p = primary[key]
    b = blind[key]
    assert row["head"] == HEAD and row["tree"] == TREE
    assert row["currentTargetSha256"] == c["currentTargetSha256"]
    assert row["sourceSha256"] == c["sourceKeySha256"]
    assert row["callerContextSha256"] == c["sourceContextSha256"]
    assert row["primaryDisposition"] == p["disposition"]
    assert row.get("primaryProposal") == p.get("proposedTarget")
    assert row["independentBlindDisposition"] == b["disposition"]
    assert row.get("independentBlindProposal") == b.get("proposedTarget")
    counts[row["crossDisposition"]] = counts.get(row["crossDisposition"], 0) + 1
    if row["action"] == "hold":
        holds += 1
        assert not any(k in row for k in ("sourceText", "sourceTextSha256", "currentTarget", "selectedTarget"))
        assert row["selectedTargetSha256"] is None
        continue
    assert row["sourceText"] == c["sourceKey"]
    assert row["currentTarget"] == c["currentTarget"]
    assert sha(row["selectedTarget"]) == row["selectedTargetSha256"]
    assert re.findall(r"\{[^{}]+\}", row["sourceText"]) == re.findall(r"\{[^{}]+\}", row["selectedTarget"])
    assert re.findall(r"<[^>]+>", row["sourceText"]) == re.findall(r"<[^>]+>", row["selectedTarget"])
    if row["action"] == "update":
        updates += 1
        assert row["selectedTarget"] != row["currentTarget"]
    elif row["action"] == "no-op":
        noops += 1
        assert row["selectedTarget"] == row["currentTarget"]
    else:
        raise AssertionError(f"unexpected action {row['action']}")

assert updates == summary["selectedUpdates"] == 12
assert noops == 228
assert holds == summary["textFreeHolds"] == 0
assert counts == summary["selectedDispositionCounts"]
assert counts == {"accept-current": 228, "refinement": 5, "correction": 7}

for catalog in context["catalogs"]:
    for term in catalog["terms"]:
        assert sha(term["target"]) == term["targetSha256"]

print(json.dumps({"result": "PASS", "head": HEAD, "tree": TREE, "cells": len(ledger), "primaryRows": len(primary), "blindRows": len(blind), "updates": updates, "acceptCurrent": noops, "holds": holds, "counts": counts, "termContextCatalogs": len(context["catalogs"])}))
