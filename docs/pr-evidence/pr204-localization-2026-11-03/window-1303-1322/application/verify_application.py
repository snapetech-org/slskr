#!/usr/bin/env python3
import hashlib
import json
from pathlib import Path

root = Path(__file__).resolve().parents[5]
app = Path(__file__).resolve().parent
evidence = app.parent
input_dir = evidence / "candidate-free-input"

def sha(b):
    if isinstance(b, str):
        b = b.encode("utf-8")
    return hashlib.sha256(b).hexdigest()

def load(path):
    return json.loads(path.read_text(encoding="utf-8"))

def jsonl(path):
    return [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines() if x.strip()]

def ordered_hash(keys):
    return sha(json.dumps(keys, ensure_ascii=False, separators=(",", ":")))

def non_target_hash(data, changed):
    return sha(json.dumps([(k, v) for k, v in data.items() if k not in changed], ensure_ascii=False, separators=(",", ":")))

def verify_sums(directory):
    for line in (directory / "SHA256SUMS.txt").read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        expected, name = line.split(maxsplit=1)
        path = directory / name.strip().lstrip("*")
        if not path.is_file() or sha(path.read_bytes()) != expected:
            raise SystemExit(f"checksum mismatch: {path}")

for directory in [
    input_dir,
    evidence / "primary-review",
    evidence / "independent-blind-review",
    evidence / "third-party-cross-audit",
    evidence,
]:
    verify_sums(directory)

pre = load(app / "application-preflight.json")
result = load(app / "application-verification.json")
plan = jsonl(app / "application-plan.jsonl")
readback = jsonl(app / "application-readback.jsonl")
cross = jsonl(evidence / "third-party-cross-audit/cross-audit-ledger.jsonl")
structure = jsonl(input_dir / "catalog-structure.jsonl")
if pre["head"] != "f46b8b2322f4b944f39f34d5bb8d55852ba330c8" or pre["tree"] != "4eba98f951a745dac6b5332bd6796bf57c7037e2":
    raise SystemExit("preflight pin mismatch")
if len(plan) != 70 or len(readback) != 240 or len(cross) != 240 or len(structure) != 12:
    raise SystemExit("evidence row count mismatch")
by_key = {(int(x["position"]), x["locale"]): x for x in cross}
if len(by_key) != 240:
    raise SystemExit("duplicate cross-audit cell")

for row in readback:
    key = (int(row["position"]), row["locale"])
    item = by_key[key]
    value = load(root / row["catalogPath"])[row["sourceKey"]]
    if value != row["expectedTarget"] or value != item["crossAuditTarget"] or sha(value) != row["expectedTargetSha256"]:
        raise SystemExit(f"readback mismatch: {key}")
    if row["disposition"] == "hold" and row["actualTarget"] != row["preApplyTarget"]:
        raise SystemExit(f"held target changed: {key}")

for info in pre["files"]:
    path = root / info["path"]
    data = load(path)
    if len(data) != info["keyCount"] or ordered_hash(list(data)) != info["keyOrderSha256"]:
        raise SystemExit(f"catalog order mismatch: {info['path']}")
    post = next(x for x in result["files"] if x["path"] == info["path"])
    if sha(path.read_bytes()) != post["postApplyFileSha256"]:
        raise SystemExit(f"post-apply file hash mismatch: {info['path']}")
    changed = {x["sourceKey"] for x in plan if x["catalogPath"] == info["path"]}
    if non_target_hash(data, changed) != info["nonTargetEntriesSha256"]:
        raise SystemExit(f"non-target value mismatch: {info['path']}")

catalog_orders = []
for info in structure:
    data = load(root / info["path"])
    keys = list(data)
    if len(keys) != info["keyCount"] or len(keys) != 5441:
        raise SystemExit(f"catalog key count mismatch: {info['path']}")
    catalog_orders.append(keys)
if any(keys != catalog_orders[0] for keys in catalog_orders[1:]):
    raise SystemExit("locale catalogs no longer share the same key order")
if len({x["keyOrderSha256"] for x in pre["files"]}) != 1:
    raise SystemExit("pre-apply locale catalog key orders did not match")
if len({x["orderedKeySha256"] for x in structure}) != 1:
    raise SystemExit("pinned locale catalog key orders did not match")

if result["readbackMatches"] != 240 or result["selectedTargetCount"] != 70 or result["heldCellsPreserved"] is not True:
    raise SystemExit("verification summary mismatch")
print(json.dumps({
    "status": "PASS",
    "readbackCells": 240,
    "selectedTargets": 70,
    "holdsPreserved": 10,
    "catalogs": 12,
    "orderedCatalogKeyCount": 5441,
    "nestedAndApplicationChecksums": "PASS"
}, indent=2))
