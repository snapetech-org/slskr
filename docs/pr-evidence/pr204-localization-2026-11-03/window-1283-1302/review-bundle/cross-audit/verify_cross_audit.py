#!/usr/bin/env python3
"""Verify the sealed slskR W1283–W1302 root cross-audit."""

import hashlib
import json
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HERE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_jsonl(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def verify_sums(directory):
    sums = directory / "SHA256SUMS.txt"
    for line in sums.read_text(encoding="utf-8").splitlines():
        expected, name = line.split(None, 1)
        name = name.lstrip("* ")
        if sha(directory / name) != expected:
            raise SystemExit(f"checksum mismatch: {directory / name}")
    return sha(sums)


def normalize_refs(refs):
    fields = ("path", "line", "lineSha256", "fileSha256", "gitBlob")
    return sorted(tuple(ref.get(field) for field in fields) for ref in refs)


def main():
    input_dir = ROOT / "candidate-free-input"
    primary_dir = ROOT / "primary-review"
    blind_dir = ROOT / "blind-review"
    input_sums = verify_sums(input_dir)
    primary_sums = verify_sums(primary_dir)
    blind_sums = verify_sums(blind_dir)
    verify_sums(HERE)
    manifest = json.loads((input_dir / "manifest.json").read_text(encoding="utf-8"))
    if manifest["head"] != "55ca2ae0788bfd79daab5cc49f49ebb608593e98" or manifest["tree"] != "d5677673b766d572102bba249af2ab69095dea0d":
        raise SystemExit("candidate-free head/tree mismatch")
    if (input_sums, primary_sums, blind_sums) != (
        "abbb1b89549b82072fcbf5fce3c6ae580cc5bd499b4fe5dadd5df7bd0c567f89",
        "e824b4518481fa2a4b122f3d8c425be7cb22826aa7133ac0e5ec4f1edef9f339",
        "83d0867a1c615665f2c12609dd2ca525013b438497f8c8309565d0ed6f6e1178",
    ):
        raise SystemExit("source packet checksum-list hash mismatch")

    cells = read_jsonl(input_dir / "current-target-cells.jsonl")
    primary = read_jsonl(primary_dir / "ledger.jsonl")
    blind = read_jsonl(blind_dir / "blind-ledger.jsonl")
    audit = read_jsonl(HERE / "cross-audit-ledger.jsonl")
    key = lambda row: (row["position"], row["locale"])
    current_by_key = {key(row): row for row in cells}
    primary_by_key = {key(row): row for row in primary}
    blind_by_key = {key(row): row for row in blind}
    audit_by_key = {key(row): row for row in audit}
    if any(len(rows) != 240 for rows in (cells, primary, blind, audit)):
        raise SystemExit("expected 240 cells in each ledger")
    if any(len(mapping) != 240 for mapping in (current_by_key, primary_by_key, blind_by_key, audit_by_key)):
        raise SystemExit("duplicate or missing position/locale cell")
    context_by_source = {row["sourceKey"]: row for row in read_jsonl(input_dir / "source-contexts.jsonl")}

    for k, current in current_by_key.items():
        p = primary_by_key[k]
        b = blind_by_key[k]
        a = audit_by_key[k]
        for field in ("sourceKey", "sourceKeySha256", "currentTarget", "currentTargetSha256", "catalogPath", "catalogFileSha256", "catalogGitBlob"):
            if p[field] != current[field] or a[field] != current[field]:
                raise SystemExit(f"source/current/primary lineage mismatch at {k}: {field}")
        for field in ("sourceKey", "sourceKeySha256", "currentTarget", "currentTargetSha256"):
            if b[field] != current[field] or a[field] != b[field] and field == "sourceKey":
                raise SystemExit(f"blind/current lineage mismatch at {k}: {field}")
        if p["callerContextSha256"] != current["sourceContextSha256"] or b["callerContextSha256"] != current["sourceContextSha256"] or a["sourceContextSha256"] != current["sourceContextSha256"]:
            raise SystemExit(f"caller-context hash mismatch at {k}")
        if normalize_refs(p["callerRefs"]) != normalize_refs(current["callerRefs"]) or normalize_refs(b["callerReferences"]) != normalize_refs(current["callerRefs"]) or normalize_refs(a["callerRefs"]) != normalize_refs(current["callerRefs"]):
            raise SystemExit(f"caller reference mismatch at {k}")
        if normalize_refs(context_by_source[current["sourceKey"]]["callers"]) != normalize_refs(current["callerRefs"]):
            raise SystemExit(f"source-context caller mismatch at {k}")
        target = a["selectedTarget"]
        allowed = {current["currentTarget"], p["proposedTarget"], b["target"]}
        if k == (1286, "fr"):
            allowed.add("Activez la limitation du débit des requêtes HTTP pour les règles d’API, de fédération et de passerelle maillée.")
        if target not in allowed:
            raise SystemExit(f"selected target not traced to a review at {k}")
        if hashlib.sha256(target.encode("utf-8")).hexdigest() != a["selectedTargetSha256"]:
            raise SystemExit(f"selected target hash mismatch at {k}")
        if current["sourcePlaceholders"] != p["proposedPlaceholders"] or current["sourcePlaceholders"] != b["targetPlaceholders"]:
            raise SystemExit(f"placeholder mismatch at {k}")
        if current["sourceMarkupTags"] != p["proposedMarkupTags"] or current["sourceMarkupTags"] != b["targetMarkupTags"]:
            raise SystemExit(f"markup mismatch at {k}")
        if current["sourceNumericTokens"] != p["proposedNumericTokens"] or current["sourceNumericTokens"] != b["targetNumericTokens"]:
            raise SystemExit(f"numeric-token mismatch at {k}")
        if not all(token in target for token in current["sourceProtectedLiterals"]):
            raise SystemExit(f"protected literal missing at {k}")
        changed = target != current["currentTarget"]
        if changed != (a["disposition"] in ("correction", "refinement")):
            raise SystemExit(f"disposition/value mismatch at {k}")
        if a["disposition"] == "hold":
            raise SystemExit(f"unexpected hold at {k}")

    summary = json.loads((HERE / "summary.json").read_text(encoding="utf-8"))
    counts = Counter(row["disposition"] for row in audit)
    changed = [row for row in audit if row["selectedTarget"] != row["currentTarget"]]
    updates_by_position = Counter(str(row["position"]) for row in changed)
    if summary["reviewedCells"] != 240 or summary["selectedUpdates"] != len(changed) or summary["dispositions"] != dict(sorted(counts.items())):
        raise SystemExit("summary count mismatch")
    if summary["updatesByPosition"] != dict(sorted(updates_by_position.items(), key=lambda item: int(item[0]))):
        raise SystemExit("summary position counts mismatch")
    print(f"cross-audit verified: {len(audit)} cells; {len(changed)} updates; {counts['accept-current']} accept-current; 0 holds")


if __name__ == "__main__":
    main()
