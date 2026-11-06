#!/usr/bin/env python3
"""Verify the independent W1603-W1622 blind review against candidate-free input only."""
import collections
import hashlib
import json
import re
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent
INPUT = ROOT.parent / "candidate-free-input"
HEAD = "eeb63f1e4e21d801f4a4e0393813b6e86a1ff7c8"
TREE = "590ee410666905f68f601393b64a4798b0609181"
TEXT_KEYS = {"source", "sourceKey", "currentTarget", "target", "proposedTarget", "rationale"}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def tsha(text):
    return sha(text.encode("utf-8"))


def read_jsonl(path):
    return [json.loads(line) for line in Path(path).read_text(encoding="utf-8").splitlines() if line.strip()]


def fail(message):
    raise SystemExit("FAIL: " + message)


def check_tokens(source, target, protected_literals):
    placeholders = lambda text: re.findall(r"\{[A-Za-z_][A-Za-z0-9_]*\}", text)
    tags = lambda text: re.findall(r"</?[A-Za-z][^>]*>", text)
    numbers = lambda text: ["".join(str(unicodedata.digit(c)) if c.isdigit() else c for c in n) for n in re.findall(r"\d+", text)]
    missing = [literal for literal in protected_literals if literal not in target]
    return {
        "placeholderSequenceMatches": placeholders(source) == placeholders(target),
        "markupMatches": tags(source) == tags(target),
        "numericTokensMatch": numbers(source) == numbers(target),
        "protectedLiteralsMatch": not missing,
        "missingProtectedLiterals": missing,
    }


def verify_checksums(root, checksum_name, allow_unlisted_cache=False):
    recorded = {}
    for line in (root / checksum_name).read_text(encoding="utf-8").splitlines():
        digest, name = line.split("  ", 1)
        path = root / name
        if not path.is_file() or sha(path.read_bytes()) != digest:
            fail("checksum " + name)
        recorded[name] = digest
    actual = {p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_file() and p.name != checksum_name}
    unlisted = actual - set(recorded)
    missing = set(recorded) - actual
    allowed_cache = {name for name in unlisted if name.startswith("__pycache__/") and name.endswith(".pyc")}
    if missing or (unlisted != allowed_cache if allow_unlisted_cache else bool(unlisted)):
        fail("checksum inventory " + str(root))
    if not allow_unlisted_cache and unlisted:
        fail("unexpected unlisted files " + str(root))
    return recorded


def main():
    input_sums = verify_checksums(INPUT, "SHA256SUMS.txt", allow_unlisted_cache=True)
    input_actual = {p.relative_to(INPUT).as_posix() for p in INPUT.rglob("*") if p.is_file() and p.name != "SHA256SUMS.txt"}
    unlisted_cache = sorted(input_actual - set(input_sums))
    note = json.loads((ROOT / "input-inventory-note.json").read_text(encoding="utf-8"))
    if note.get("unlistedFiles") != unlisted_cache or note.get("unlistedFilesRead") is not False or note.get("unlistedFilesChanged") is not False:
        fail("candidate-free unlisted-cache note")
    input_manifest = json.loads((INPUT / "manifest.json").read_text(encoding="utf-8"))
    if input_manifest.get("head") != HEAD or input_manifest.get("tree") != TREE or input_manifest.get("candidateFreeInputOnly") is not True:
        fail("candidate-free pin")
    if input_manifest.get("proposedTranslationsIncluded") is not False:
        fail("candidate-free packet contains proposals")
    if set(input_manifest["fileHashes"]) != set(input_sums) - {"manifest.json"}:
        fail("candidate-free file hash inventory")

    sums = verify_checksums(ROOT, "SHA256SUMS.txt")
    manifest = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))
    if manifest.get("head") != HEAD or manifest.get("tree") != TREE or manifest.get("window") != "W1603-W1622":
        fail("blind-review pin")
    if manifest.get("candidateFreeInputOnly") is not True or manifest.get("primaryReviewRead") is not False or manifest.get("otherProposalLedgerRead") is not False:
        fail("blind-review provenance flags")
    if manifest.get("candidateFreeInputManifestSha256") != sha((INPUT / "manifest.json").read_bytes()):
        fail("candidate-free manifest binding")
    if manifest.get("candidateFreeInputChecksumListSha256") != sha((INPUT / "SHA256SUMS.txt").read_bytes()):
        fail("candidate-free checksum binding")
    if manifest.get("unlistedCandidateFreeCacheObserved") != bool(unlisted_cache):
        fail("candidate-free cache observation")
    file_rows = {row["path"]: row for row in manifest["files"]}
    actual_payloads = {p.relative_to(ROOT).as_posix() for p in ROOT.rglob("*") if p.is_file() and p.name not in {"manifest.json", "SHA256SUMS.txt"}}
    if set(file_rows) != actual_payloads:
        fail("review payload inventory")
    for name, row in file_rows.items():
        if row["sha256"] != sha((ROOT / name).read_bytes()) or row["byteCount"] != (ROOT / name).stat().st_size:
            fail("review manifest payload " + name)

    contexts = {row["position"]: row for row in read_jsonl(INPUT / "source-contexts.jsonl")}
    cells = read_jsonl(INPUT / "current-target-cells.jsonl")
    locales = input_manifest["localeOrder"]
    expected = [(position, locale) for position in range(1603, 1623) for locale in locales]
    if len(contexts) != 20 or len(cells) != 240 or [(r["position"], r["locale"]) for r in cells] != expected:
        fail("candidate-free input coverage/order")
    input_by_cell = {(row["position"], row["locale"]): row for row in cells}
    ledger = read_jsonl(ROOT / "blind-ledger.jsonl")
    proposals = read_jsonl(ROOT / "proposals.jsonl")
    holds = read_jsonl(ROOT / "holds-hash-only.jsonl")
    if len(ledger) != 240 or [(r["position"], r["locale"]) for r in ledger] != expected:
        fail("blind ledger coverage/order")
    counts = collections.Counter(row["decision"] for row in ledger)
    if len(proposals) != counts["correction"] or len(holds) != counts["hold"]:
        fail("proposal/hold counts")
    if dict(counts) != manifest.get("decisionCounts") or len(ledger) != manifest.get("cellCount"):
        fail("decision counts")
    proposal_by_cell = {(row["position"], row["locale"]): row for row in proposals}

    for row in ledger:
        key = (row["position"], row["locale"])
        cell = input_by_cell[key]
        context = contexts[row["position"]]
        for field in ("sourceKey", "sourceKeySha256", "sourceContextSha256", "callerCount", "catalogPath", "catalogFileSha256", "catalogGitBlob", "currentTarget", "currentTargetSha256"):
            if row[field] != cell[field]:
                fail("input binding " + str(key) + " " + field)
        if row["callerOccurrenceCount"] != context["callerOccurrenceCount"] or row["callerContextSha256"] != context["callerContextSha256"]:
            fail("caller context binding " + str(key))
        pins = [{"path": c["path"], "line": c["line"], "lineSha256": c["lineSha256"],
                 "contextSha256": c["contextSha256"], "fileSha256": c["fileSha256"], "gitBlob": c["gitBlob"]}
                for c in context["callers"]]
        if row["callerReferencePins"] != pins:
            fail("caller reference pins " + str(key))
        if row["head"] != HEAD or row["tree"] != TREE or row["reviewPass"] != "independent-blind":
            fail("row pin " + str(key))
        if row["sourceKeySha256"] != tsha(row["sourceKey"]) or row["currentTargetSha256"] != tsha(row["currentTarget"]):
            fail("text hash " + str(key))
        if not row["rationale"] or row["confidence"] not in {"high", "moderate", "low", "unknown"}:
            fail("rationale/confidence " + str(key))
        current = check_tokens(row["sourceKey"], row["currentTarget"], cell["sourceProtectedLiterals"])
        if not all(current[name] for name in ("placeholderSequenceMatches", "markupMatches", "numericTokensMatch", "protectedLiteralsMatch")):
            fail("current token mismatch " + str(key))
        if row["decision"] == "correction":
            target = row["proposedTarget"]
            if not target or row["proposedTargetSha256"] != tsha(target):
                fail("proposal text/hash " + str(key))
            candidate = check_tokens(row["sourceKey"], target, cell["sourceProtectedLiterals"])
            if not all(candidate[name] for name in ("placeholderSequenceMatches", "markupMatches", "numericTokensMatch", "protectedLiteralsMatch")):
                fail("proposal token mismatch " + str(key))
            p = proposal_by_cell.get(key)
            if not p or p["proposedTarget"] != target or p["proposedTargetSha256"] != row["proposedTargetSha256"] or p["rationale"] != row["rationale"]:
                fail("proposal ledger binding " + str(key))
        elif row["decision"] == "accept-current":
            if row["proposedTarget"] is not None or row["proposedTargetSha256"] is not None or key in proposal_by_cell:
                fail("accept-current contains proposal " + str(key))
        elif row["decision"] == "hold":
            if row["proposedTarget"] is not None:
                fail("hold contains proposed text " + str(key))
        else:
            fail("unknown decision " + str(key))
    for row in holds:
        if any(key in TEXT_KEYS for key in row):
            fail("text in hash-only hold")
    print(json.dumps({"result": "PASS", "head": HEAD, "tree": TREE, "reviewedCells": len(ledger),
                      "decisions": dict(counts), "proposals": len(proposals), "holds": len(holds),
                      "placeholderMarkupNumberProtectedLiteralChecks": "PASS", "checksummedFiles": len(sums)}, indent=2))


if __name__ == "__main__":
    main()
