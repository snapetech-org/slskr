#!/usr/bin/env python3
"""Verify the sealed W1643-W1662 primary review packet without modifying inputs."""
from __future__ import annotations
import argparse, hashlib, json, re, subprocess, sys
from pathlib import Path

OUT = Path(__file__).resolve().parent
HEAD = "2d804c49879372071adf606bc2a2cf51e261fd94"
TREE = "d6f5552d2400d868c2f2af98eb68caadfd4f3f66"
LOCALES = ["es", "zh-Hans", "hi", "de", "ja", "fr", "pt-BR", "ar", "ko", "zh-Hant", "vi", "id"]
PROPOSAL_KEYS = {(1643, "ko"), (1646, "zh-Hant"), (1649, "hi"), (1654, "zh-Hant")}

def sha(data):
    if isinstance(data, str): data = data.encode("utf-8")
    return hashlib.sha256(data).hexdigest()

def readjl(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]

def require(ok, message):
    if not ok: raise RuntimeError(message)

def verify_sums(root):
    sums = {}
    for line in (root / "SHA256SUMS.txt").read_text(encoding="utf-8").splitlines():
        if not line.strip(): continue
        digest, name = line.split(None, 1)
        sums[name.lstrip("* ")] = digest
    actual = {p.relative_to(root).as_posix(): sha(p.read_bytes()) for p in root.rglob("*") if p.is_file() and p.name != "SHA256SUMS.txt"}
    require(sums == actual, "SHA256SUMS.txt does not match the packet files")
    return len(sums)

def token_signature(text):
    placeholders = re.findall(r"\{[A-Za-z][A-Za-z0-9_]*\}", text)
    markup = re.findall(r"</?[A-Za-z][^>]*>", text)
    numeric = re.findall(r"(?<![A-Za-z])\d+(?:[.,]\d+)?%?(?![A-Za-z])", text)
    protected = []
    for value in re.findall(r"(?<![A-Za-z0-9])(?:[A-Z]{2,}[A-Z0-9]*|ffmpeg|Chromaprint|Soulseek|Spotify|YouTube|Pushbullet|Matrix|WebSocket|OpenAI)(?![A-Za-z0-9])", text):
        if value not in protected: protected.append(value)
    return {"placeholders": placeholders, "markupTags": markup, "numericTokens": numeric, "protectedLiterals": protected}

def verify_pin(path):
    pin = json.loads(path.read_text(encoding="utf-8"))
    require((pin.get("state"), pin.get("draft"), pin.get("headSha"), pin.get("headTree")) == ("open", True, HEAD, TREE), f"PR pin changed in {path.name}")
    require(pin.get("headRef") == "codex/slskr-l10n-audit-20261104-resync", f"PR branch changed in {path.name}")
    require(pin.get("branchRefSha") == HEAD and pin.get("pullRefSha") == HEAD, f"branch/pull refs changed in {path.name}")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=OUT.parent / "candidate-free-input")
    parser.add_argument("--worktree", type=Path, default=OUT.parent / "worktree")
    args = parser.parse_args()
    input_dir, worktree = args.input.resolve(), args.worktree.resolve()

    checksum_count = verify_sums(OUT)
    manifest = json.loads((OUT / "manifest.json").read_text(encoding="utf-8"))
    for name, meta in manifest["fileHashes"].items():
        path = OUT / name
        require(path.is_file() and sha(path.read_bytes()) == meta["sha256"] and path.stat().st_size == meta["byteCount"], "manifest file hash mismatch: " + name)
    listed = set(manifest["fileHashes"])
    actual_payload = {p.relative_to(OUT).as_posix() for p in OUT.rglob("*") if p.is_file() and p.name not in {"manifest.json", "SHA256SUMS.txt"}}
    require(listed == actual_payload, "manifest file inventory mismatch")

    cf_count = verify_sums(input_dir)
    cf = json.loads((input_dir / "manifest.json").read_text(encoding="utf-8"))
    require(cf.get("candidateFreeInputOnly") is True and cf.get("proposedTranslationsIncluded") is False, "candidate-free source is not proposal-free")
    require((cf.get("head"), cf.get("tree"), cf.get("selectedPositions")) == (HEAD, TREE, [1643, 1662]), "candidate-free exact-head/window mismatch")
    require(sha((input_dir / "manifest.json").read_bytes()) == json.loads((OUT / "input-attestation.json").read_text(encoding="utf-8"))["candidateFreeManifestSha256"], "candidate-free manifest attestation mismatch")
    verify_pin(OUT / "attestation" / "pin-before-review.json")
    verify_pin(OUT / "attestation" / "pin-after-review.json")

    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=worktree, text=True).strip()
    tree = subprocess.check_output(["git", "rev-parse", "HEAD^{tree}"], cwd=worktree, text=True).strip()
    status = subprocess.check_output(["git", "status", "--porcelain"], cwd=worktree, text=True).strip()
    require((head, tree, status) == (HEAD, TREE, ""), "exact detached worktree is not at the clean pinned head")

    current = readjl(input_dir / "current-target-cells.jsonl")
    sources = readjl(input_dir / "source-contexts.jsonl")
    holds = readjl(input_dir / "caller-resolution-holds.jsonl")
    ledger = readjl(OUT / "primary-ledger.jsonl")
    proposals = readjl(OUT / "proposals.jsonl")
    require((len(current), len(sources), len(ledger), len(proposals), len(holds)) == (240, 20, 240, 4, 0), "row/proposal/callerless coverage mismatch")
    require((OUT / "holds-hash-only.jsonl").read_bytes() == b"", "hash-only hold ledger must be empty for this window")
    source_by_pos = {r["position"]: r for r in sources}
    proposal_by_id = {r["rowId"]: r for r in proposals}
    require(len(proposal_by_id) == 4, "proposal row IDs are not unique")
    seen = set()
    accept_count = 0
    for c, row in zip(current, ledger):
        pos, loc = c["position"], c["locale"]
        row_id = f"W1643-W1662:{pos}:{loc}"
        require(row["rowId"] == row_id and row["position"] == pos and row["locale"] == loc, "ledger order/identity mismatch")
        require(loc in LOCALES and (pos, loc) not in seen, "duplicate or unknown cell")
        seen.add((pos, loc))
        ctx = source_by_pos[pos]
        require(row["sourceKey"] == c["sourceKey"] == ctx["sourceKey"], "source text mismatch: " + row_id)
        require(row["sourceKeySha256"] == c["sourceKeySha256"] == ctx["sourceKeySha256"] == sha(c["sourceKey"]), "source hash mismatch: " + row_id)
        require(row["currentTarget"] == c["currentTarget"] and row["currentTargetSha256"] == c["currentTargetSha256"] == sha(c["currentTarget"]), "current target hash mismatch: " + row_id)
        require(row["sourceContextSha256"] == c["sourceContextSha256"] == ctx["callerContextSha256"], "caller context hash mismatch: " + row_id)
        require(row["callerOccurrenceCount"] == ctx["callerOccurrenceCount"] == c["callerCount"], "caller count mismatch: " + row_id)
        refs = [{"path": x["path"], "line": x["line"], "lineSha256": x["lineSha256"], "contextSha256": x["contextSha256"], "literalOccurrenceCount": x["literalOccurrenceCount"]} for x in ctx["callers"]]
        require(row["callerReferences"] == refs, "caller references mismatch: " + row_id)
        require(row["catalogPath"] == c["catalogPath"] and row["catalogFileSha256"] == c["catalogFileSha256"] and row["catalogGitBlob"] == c["catalogGitBlob"], "catalog pin mismatch: " + row_id)
        source_sig = {"placeholders": c["sourcePlaceholders"], "markupTags": c["sourceMarkupTags"], "numericTokens": c["sourceNumericTokens"], "protectedLiterals": c["sourceProtectedLiterals"]}
        cur_sig = token_signature(c["currentTarget"])
        require(source_sig == cur_sig == row["sourceTokenSignature"] == row["currentTokenSignature"], "current token mismatch: " + row_id)
        if (pos, loc) in PROPOSAL_KEYS:
            p = proposal_by_id.get(row_id)
            require(p is not None and row["decision"] == "correction", "missing correction: " + row_id)
            target = p["recommendedTarget"]
            require(row["recommendedTarget"] == target and row["recommendedTargetSha256"] == p["recommendedTargetSha256"] == sha(target), "proposal target mismatch: " + row_id)
            require(p["currentTarget"] == c["currentTarget"] and p["currentTargetSha256"] == c["currentTargetSha256"], "proposal current target mismatch: " + row_id)
            require(p["sourceContextSha256"] == row["sourceContextSha256"] and p["callerReferences"] == refs, "proposal caller binding mismatch: " + row_id)
            require(token_signature(target) == source_sig == row["recommendedTokenSignature"], "proposal token preservation mismatch: " + row_id)
        else:
            require(row["decision"] == "accept-current" and row["recommendedTarget"] is None and row["recommendedTargetSha256"] is None, "unexpected proposal: " + row_id)
            require(row["recommendedTokenSignature"] == cur_sig, "accepted target token mismatch: " + row_id)
            accept_count += 1
        require(row["priorWindowApplicationReattested"] is True, "prior lineage reattestation missing: " + row_id)
    require(seen == {(p, loc) for p in range(1643, 1663) for loc in LOCALES}, "cell coverage incomplete")
    require(set(proposal_by_id) == {f"W1643-W1662:{p}:{loc}" for p, loc in PROPOSAL_KEYS}, "proposal set mismatch")
    summary = json.loads((OUT / "summary.json").read_text(encoding="utf-8"))
    require(summary.get("reviewedCellCount") == 240 and summary.get("proposalCount") == 4 and summary.get("dispositions") == {"accept-current": 236, "correction": 4}, "summary count mismatch")
    print(json.dumps({"result": "PASS", "head": HEAD, "tree": TREE, "cells": len(ledger), "acceptCurrent": accept_count, "corrections": len(proposals), "callerlessHolds": len(holds), "candidateFreeChecksumFiles": cf_count, "primaryChecksumFiles": checksum_count, "tokenPreservation": "PASS", "exactWorktree": "PASS", "beforeAfterLivePRPins": "PASS"}, indent=2))

if __name__ == "__main__":
    try: main()
    except Exception as exc:
        print(json.dumps({"result": "FAIL", "error": str(exc)}, indent=2), file=sys.stderr)
        raise SystemExit(1)
