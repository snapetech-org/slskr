#!/usr/bin/env python3
import collections, hashlib, json, re
from pathlib import Path

base = Path("/home/keith/Documents/code/task-scratch")
root = base / "slskr-pr204-w1303-1322-root-cross-audit-20261103"
inp = base / "slskr-pr204-w1303-1322-primary-20261103/input"
primary = base / "slskr-pr204-w1303-1322-primary-20261103/primary-review"
blind = base / "slskr-pr204-w1303-1322-blind-20261103/review"

def sha(b):
    if isinstance(b, str):
        b = b.encode("utf-8")
    return hashlib.sha256(b).hexdigest()

def jsonl(path):
    return [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines() if x.strip()]

def verify_sums(directory):
    for line in (directory / "SHA256SUMS.txt").read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        expected, name = line.split(maxsplit=1)
        name = name.strip().lstrip("*")
        path = directory / name
        if not path.is_file() or sha(path.read_bytes()) != expected:
            raise SystemExit(f"checksum mismatch: {path}")

for directory in [inp, primary, blind, root]:
    verify_sums(directory)
ledger = jsonl(root / "cross-audit-ledger.jsonl")
plan = jsonl(root / "application-plan.jsonl")
input_cells = jsonl(inp / "current-target-cells.jsonl")
cells = {(int(x["position"]), x["locale"]): x for x in input_cells}
entries = {(int(x["position"]), x["locale"]): x for x in ledger}
if len(ledger) != 240 or len(entries) != 240 or set(cells) != set(entries):
    raise SystemExit("cross-audit cell coverage mismatch")
if len(plan) != 70 or len({(x["position"], x["locale"]) for x in plan}) != 70:
    raise SystemExit("application plan coverage mismatch")
counts = collections.Counter(x["crossAuditDisposition"] for x in ledger)
if counts != collections.Counter({"accept-current":160, "correction":31, "refinement":39, "hold":10}):
    raise SystemExit(f"unexpected decision counts: {counts}")
for row in ledger:
    key = (int(row["position"]), row["locale"])
    cell = cells[key]
    if row["head"] != "f46b8b2322f4b944f39f34d5bb8d55852ba330c8" or row["tree"] != "4eba98f951a745dac6b5332bd6796bf57c7037e2":
        raise SystemExit(f"pin mismatch: {key}")
    if row["currentTargetSha256"] != cell["currentTargetSha256"] or row["sourceKey"] != cell["sourceKey"]:
        raise SystemExit(f"input pin mismatch: {key}")
    if not row["callerRefs"]:
        raise SystemExit(f"missing pinned caller: {key}")
    if row["crossAuditDisposition"] == "hold" and row["crossAuditTarget"] != cell["currentTarget"]:
        raise SystemExit(f"hold changed: {key}")
    if row["crossAuditDisposition"] == "accept-current" and row["crossAuditTarget"] != cell["currentTarget"]:
        raise SystemExit(f"accept-current changed: {key}")
    if re.findall(r"\{[^{}]+\}", row["crossAuditTarget"]) != cell.get("sourcePlaceholders", []):
        raise SystemExit(f"placeholder mismatch: {key}")
    if not all(x in row["crossAuditTarget"] for x in cell.get("sourceProtectedLiterals", [])):
        raise SystemExit(f"protected literal mismatch: {key}")
    if not all(x in row["crossAuditTarget"] for x in cell.get("sourceMarkupTags", [])):
        raise SystemExit(f"markup mismatch: {key}")
for x in plan:
    key = (int(x["position"]), x["locale"])
    row = entries[key]
    cell = cells[key]
    if x["target"] != row["crossAuditTarget"] or x["targetSha256"] != sha(x["target"]):
        raise SystemExit(f"target readback mismatch: {key}")
    if x["expectedCurrentTargetSha256"] != cell["currentTargetSha256"]:
        raise SystemExit(f"current value pin mismatch: {key}")
print(json.dumps({
    "status":"PASS",
    "cells":len(ledger),
    "applicationTargets":len(plan),
    "decisionCounts":dict(counts),
    "holdCount":counts["hold"],
    "inputPrimaryBlindAndOutputChecksums":"PASS",
    "placeholderMarkupAndProtectedLiteralChecks":"PASS",
},ensure_ascii=False,indent=2))
