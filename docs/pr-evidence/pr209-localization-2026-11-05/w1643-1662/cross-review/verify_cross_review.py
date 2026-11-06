#!/usr/bin/env python3
"""Portable verifier for the slskR W1643-W1662 cross-review packet."""
from __future__ import annotations
import argparse, hashlib, json, re, subprocess, sys
from pathlib import Path

OUT = Path(__file__).resolve().parent
HEAD = "2d804c49879372071adf606bc2a2cf51e261fd94"
TREE = "d6f5552d2400d868c2f2af98eb68caadfd4f3f66"
LOCALES = ["es", "zh-Hans", "hi", "de", "ja", "fr", "pt-BR", "ar", "ko", "zh-Hant", "vi", "id"]
FINAL = {
    (1643, "ko"): ("correction", "메타데이터를 가져오지 못했습니다:"),
    (1646, "zh-Hant"): ("refinement", "無法路由訊息。"),
    (1647, "fr"): ("refinement", "Échec du routage du message :"),
    (1647, "pt-BR"): ("refinement", "Falha ao rotear a mensagem:"),
    (1649, "hi"): ("correction", "खतरों से सुरक्षा की सेटिंग सहेजी नहीं जा सकीं"),
    (1654, "zh-Hant"): ("correction", "無法儲存來源訂閱整合設定。"),
    (1661, "ar"): ("correction", "تعذر اختيار النسخة المعيارية."),
    (1661, "ja"): ("refinement", "正準バリアントを選択できませんでした。"),
    (1661, "ko"): ("refinement", "정규 변형을 선택하지 못했습니다."),
}

def sha(data):
    if isinstance(data, str): data = data.encode("utf-8")
    return hashlib.sha256(data).hexdigest()

def readjl(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]

def require(ok, message):
    if not ok: raise RuntimeError(message)

def sums(root):
    expected = {}
    for line in (root / "SHA256SUMS.txt").read_text(encoding="utf-8").splitlines():
        if line.strip():
            digest, name = line.split(None, 1)
            expected[name.lstrip("* ")] = digest
    actual = {p.relative_to(root).as_posix(): sha(p.read_bytes()) for p in root.rglob("*") if p.is_file() and p.name != "SHA256SUMS.txt"}
    require(expected == actual, "checksum index mismatch: " + str(root))
    return len(expected)

def token_signature(text):
    placeholders = re.findall(r"\{[A-Za-z][A-Za-z0-9_]*\}", text)
    markup = re.findall(r"</?[A-Za-z][^>]*>", text)
    numeric = re.findall(r"(?<![A-Za-z])\d+(?:[.,]\d+)?%?(?![A-Za-z])", text)
    protected = []
    for value in re.findall(r"(?<![A-Za-z0-9])(?:[A-Z]{2,}[A-Z0-9]*|ffmpeg|Chromaprint|Soulseek|Spotify|YouTube|Pushbullet|Matrix|WebSocket|OpenAI)(?![A-Za-z0-9])", text):
        if value not in protected: protected.append(value)
    return {"placeholders": placeholders, "markupTags": markup, "numericTokens": numeric, "protectedLiterals": protected}

def check_live_pin(root, suffix):
    pin = json.loads((root / f"pin-{suffix}-review.json").read_text(encoding="utf-8"))
    api_path = root / f"pr-api-{suffix}-review.json"
    commit_path = root / f"head-commit-{suffix}-review.json"
    refs_path = root / f"remote-refs-{suffix}-review.txt"
    api = json.loads(api_path.read_text(encoding="utf-8"))
    commit = json.loads(commit_path.read_text(encoding="utf-8"))
    refs = {}
    for line in refs_path.read_text(encoding="utf-8").splitlines():
        digest, name = line.split("\t")
        refs[name] = digest
    require(pin.get("result") == "PASS", f"pin was not recorded PASS ({suffix})")
    require((pin.get("headSha"), pin.get("headTree"), pin.get("headRef"), pin.get("state"), pin.get("draft")) == (HEAD, TREE, "codex/slskr-l10n-audit-20261104-resync", "open", True), f"normalized PR pin mismatch ({suffix})")
    require(api.get("headRefOid") == HEAD and api.get("headRefName") == pin.get("headRef") and api.get("isDraft") is True and api.get("state", "").lower() == "open", f"raw PR API mismatch ({suffix})")
    require(api.get("baseRefName") == "main" and api.get("baseRefOid") == pin.get("baseSha") and pin.get("baseSha") == "1bbaec9fdc63a86de343e37e33bae70d44301a36", f"raw PR base mismatch ({suffix})")
    require(commit.get("sha") == HEAD and commit.get("commit", {}).get("tree", {}).get("sha") == TREE, f"raw commit/tree mismatch ({suffix})")
    require(refs.get("refs/heads/" + pin["headRef"]) == HEAD and refs.get("refs/pull/209/head") == HEAD and refs.get("refs/heads/main") == pin.get("liveMainSha"), f"raw branch/pull/main ref mismatch ({suffix})")
    require(pin.get("branchRefSha") == HEAD and pin.get("pullRefSha") == HEAD, f"normalized branch/pull ref mismatch ({suffix})")
    require(pin.get("prApiSha256") == sha(api_path.read_bytes()) and pin.get("remoteRefsSha256") == sha(refs_path.read_bytes()) and pin.get("headCommitResponseSha256") == sha(commit_path.read_bytes()), f"snapshot hash mismatch ({suffix})")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", type=Path, default=OUT.parent / "candidate-free-input")
    ap.add_argument("--primary", type=Path, default=OUT.parent / "primary-review")
    ap.add_argument("--blind", type=Path, default=OUT.parent / "blind-review")
    ap.add_argument("--worktree", type=Path, default=OUT.parent / "worktree")
    args = ap.parse_args()
    inp, primary, blind, worktree = (p.resolve() for p in (args.input, args.primary, args.blind, args.worktree))

    packet_counts = {"candidateFree": sums(inp), "primary": sums(primary), "blind": sums(blind), "crossReview": sums(OUT)}
    cross_manifest = json.loads((OUT / "manifest.json").read_text(encoding="utf-8"))
    for name, meta in cross_manifest["fileHashes"].items():
        path = OUT / name
        require(path.is_file() and sha(path.read_bytes()) == meta["sha256"] and path.stat().st_size == meta["byteCount"], "cross manifest mismatch: " + name)
    listed = set(cross_manifest["fileHashes"])
    actual = {p.relative_to(OUT).as_posix() for p in OUT.rglob("*") if p.is_file() and p.name not in {"manifest.json", "SHA256SUMS.txt"}}
    require(listed == actual, "cross-review manifest inventory mismatch")

    cfm = json.loads((inp / "manifest.json").read_text(encoding="utf-8"))
    pm = json.loads((primary / "manifest.json").read_text(encoding="utf-8"))
    bm = json.loads((blind / "manifest.json").read_text(encoding="utf-8"))
    require(cfm.get("head") == HEAD and cfm.get("tree") == TREE and cfm.get("callerResolutionHoldCount") == 0, "candidate-free pin/hold mismatch")
    require(pm.get("head") == HEAD and pm.get("tree") == TREE, "primary pin mismatch")
    require(bm.get("exactHead") == HEAD and bm.get("exactTree") == TREE, "blind pin mismatch")
    input_att = json.loads((OUT / "input-attestation.json").read_text(encoding="utf-8"))
    require(input_att.get("candidateFreeManifestSha256") == sha((inp / "manifest.json").read_bytes()), "candidate-free manifest hash mismatch")
    require(input_att.get("candidateFreeChecksumIndexSha256") == sha((inp / "SHA256SUMS.txt").read_bytes()), "candidate-free checksum index hash mismatch")
    require(input_att.get("primaryManifestSha256") == sha((primary / "manifest.json").read_bytes()), "primary manifest hash mismatch")
    require(input_att.get("primaryChecksumIndexSha256") == sha((primary / "SHA256SUMS.txt").read_bytes()), "primary checksum index hash mismatch")
    require(input_att.get("blindManifestSha256") == sha((blind / "manifest.json").read_bytes()), "blind manifest hash mismatch")
    require(input_att.get("blindChecksumIndexSha256") == sha((blind / "SHA256SUMS.txt").read_bytes()), "blind checksum index hash mismatch")
    check_live_pin(OUT / "attestation", "before")
    check_live_pin(OUT / "attestation", "after")

    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=worktree, text=True).strip()
    tree = subprocess.check_output(["git", "rev-parse", "HEAD^{tree}"], cwd=worktree, text=True).strip()
    status = subprocess.check_output(["git", "status", "--porcelain"], cwd=worktree, text=True).strip()
    require((head, tree, status) == (HEAD, TREE, ""), "pinned worktree is not clean")

    raw_lines = [line for line in (inp / "current-target-cells.jsonl").read_bytes().splitlines() if line.strip()]
    current = [json.loads(line) for line in raw_lines]
    row_hashes = {(r["position"], r["locale"]): sha(raw) for r, raw in zip(current, raw_lines)}
    contexts = {r["position"]: r for r in readjl(inp / "source-contexts.jsonl")}
    primary_rows = {(r["position"], r["locale"]): r for r in readjl(primary / "primary-ledger.jsonl")}
    primary_props = {(r["position"], r["locale"]): r for r in readjl(primary / "proposals.jsonl")}
    blind_rows = {(r["selectedPosition"], r["locale"]): r for r in readjl(blind / "ledger.jsonl")}
    blind_props = {(r["selectedPosition"], r["locale"]): r for r in readjl(blind / "proposals.jsonl")}
    ledger = readjl(OUT / "cross-ledger.jsonl")
    recommendations = readjl(OUT / "recommendations.jsonl")
    disagreements = readjl(OUT / "proposal-disagreements.jsonl")
    require((len(current), len(contexts), len(primary_rows), len(blind_rows), len(ledger), len(recommendations), len(disagreements)) == (240, 20, 240, 240, 240, 9, 7), "row coverage or proposal count mismatch")
    require((OUT / "holds-hash-only.jsonl").read_bytes() == b"" and readjl(inp / "caller-resolution-holds.jsonl") == [], "unexpected callerless holds")

    seen = set()
    for c, row in zip(current, ledger):
        pos, loc = c["position"], c["locale"]
        key = (pos, loc)
        ctx, p, b = contexts[pos], primary_rows[key], blind_rows[key]
        row_id = f"W1643-W1662:{pos}:{loc}"
        require(row["rowId"] == row_id and key not in seen, "cross ledger row identity/duplicate mismatch")
        seen.add(key)
        require(row["sourceKey"] == c["sourceKey"] == ctx["sourceKey"] and row["sourceKeySha256"] == c["sourceKeySha256"] == p["sourceKeySha256"] == sha(c["sourceKey"]), "source hash binding mismatch: " + row_id)
        require(row["candidateFreeRowSha256"] == row_hashes[key] == b["candidateFreeRowSha256"], "candidate-free row binding mismatch: " + row_id)
        require(row["currentTarget"] == c["currentTarget"] == p["currentTarget"] == b["currentTarget"] and row["currentTargetSha256"] == c["currentTargetSha256"] == p["currentTargetSha256"] == b["currentTargetSha256"] == sha(c["currentTarget"]), "current-target binding mismatch: " + row_id)
        require(row["sourceContextSha256"] == c["sourceContextSha256"] == ctx["callerContextSha256"] == p["sourceContextSha256"] == b["sourceContextSha256"], "caller-context hash mismatch: " + row_id)
        require(row["callerOccurrenceCount"] == ctx["callerOccurrenceCount"] == p["callerOccurrenceCount"] == b["callerCount"], "caller occurrence mismatch: " + row_id)
        require(row["catalogPath"] == c["catalogPath"] and row["catalogFileSha256"] == c["catalogFileSha256"] and row["catalogGitBlob"] == c["catalogGitBlob"], "catalog pin mismatch: " + row_id)
        refs = [{"path": x["path"], "line": x["line"], "lineSha256": x["lineSha256"], "contextSha256": x["contextSha256"], "literalOccurrenceCount": x["literalOccurrenceCount"]} for x in ctx["callers"]]
        require(row["callerReferences"] == refs and refs, "caller reference mismatch or empty caller: " + row_id)
        require(row["primaryReview"]["decision"] == p["decision"] and row["primaryReview"]["rationale"] == p["rationale"], "primary review binding mismatch: " + row_id)
        require(row["blindReview"]["decision"] == b["decision"] and row["blindReview"]["rationale"] == b["rationale"], "blind review binding mismatch: " + row_id)
        pp, bp = primary_props.get(key), blind_props.get(key)
        ptarget = pp["recommendedTarget"] if pp else None
        btarget = bp["recommendedTarget"] if bp else None
        require(row["primaryReview"]["recommendedTarget"] == ptarget and row["blindReview"]["recommendedTarget"] == btarget, "incoming recommendation mismatch: " + row_id)
        ptarget_hash = pp["recommendedTargetSha256"] if pp else None
        btarget_hash = bp["recommendedTargetSha256"] if bp else None
        require(row["primaryReview"]["recommendedTargetSha256"] == ptarget_hash and row["blindReview"]["recommendedTargetSha256"] == btarget_hash, "incoming recommendation hash mismatch: " + row_id)
        if pp and bp:
            require(ptarget == btarget and ptarget_hash == btarget_hash, "overlapping review targets conflict: " + row_id)
        disagreement = p["decision"] != b["decision"] or ptarget != btarget
        require(row["reviewerDisagreement"] is disagreement, "reviewer disagreement flag mismatch: " + row_id)
        final = FINAL.get(key)
        if final:
            disposition, target = final
            require(row["crossDisposition"] == disposition and row["crossRecommendedTarget"] == target and row["crossRecommendedTargetSha256"] == sha(target), "cross adjudication mismatch: " + row_id)
            require(token_signature(c["sourceKey"]) == token_signature(target) == row["crossTargetTokenSignature"], "recommended target token mismatch: " + row_id)
            require(row["applyReady"] is True, "recommended target not apply-ready: " + row_id)
        else:
            require(row["crossDisposition"] == "retain-current" and row["crossRecommendedTarget"] is None and row["crossRecommendedTargetSha256"] is None and row["applyReady"] is False, "retained row mismatch: " + row_id)
            require(row["crossTargetTokenSignature"] == token_signature(c["currentTarget"]), "retained token mismatch: " + row_id)
        source_sig = {"placeholders": c["sourcePlaceholders"], "markupTags": c["sourceMarkupTags"], "numericTokens": c["sourceNumericTokens"], "protectedLiterals": c["sourceProtectedLiterals"]}
        require(source_sig == token_signature(c["currentTarget"]) == row["sourceTokenSignature"] == row["currentTokenSignature"], "source/current token mismatch: " + row_id)
    require(len(seen) == 240, "cross-ledger coverage incomplete")
    require({(r["position"], r["locale"]) for r in recommendations} == set(FINAL), "recommendations set mismatch")
    expected_disagreements = {key for key in primary_rows if primary_rows[key]["decision"] != blind_rows[key]["decision"] or ((key in primary_props) != (key in blind_props)) or (key in primary_props and key in blind_props and primary_props[key]["recommendedTarget"] != blind_props[key]["recommendedTarget"])}
    require({(r["position"], r["locale"]) for r in disagreements} == expected_disagreements, "disagreement list coverage mismatch")
    require(len(expected_disagreements) == 7 and len(primary_props.keys() & blind_props.keys()) == 2, "reviewer overlap/disagreement count mismatch")
    rec_map = {(r["position"], r["locale"]): r for r in recommendations}
    for key, rec in rec_map.items():
        row = next(x for x in ledger if (x["position"], x["locale"]) == key)
        require(rec["recommendedTarget"] == row["crossRecommendedTarget"] and rec["recommendedTargetSha256"] == row["crossRecommendedTargetSha256"] and rec["disposition"] == row["crossDisposition"], "recommendation/ledger mismatch")
    summary = json.loads((OUT / "summary.json").read_text(encoding="utf-8"))
    require(summary.get("reviewedCellCount") == 240 and summary.get("applyReadyProposalCount") == 9 and summary.get("reviewerDisagreementCellCount") == 7 and summary.get("targetWordingConflicts") == 0, "summary counts mismatch")
    require(summary.get("crossDispositions") == {"retain-current": 231, "correction": 4, "refinement": 5}, "summary disposition mismatch")
    print(json.dumps({"result": "PASS", "head": HEAD, "tree": TREE, "cells": 240, "retainCurrent": 231, "corrections": 4, "refinements": 5, "applyReady": 9, "holds": 0, "oneSidedRecommendationDisagreements": 7, "targetWordingConflicts": 0, "inputChecksumCounts": packet_counts, "exactHeadPins": "PASS before/after", "worktree": "clean"}, indent=2))

if __name__ == "__main__":
    try: main()
    except Exception as exc:
        print(json.dumps({"result": "FAIL", "error": str(exc)}, indent=2), file=sys.stderr)
        raise SystemExit(1)
