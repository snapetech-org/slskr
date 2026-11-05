#!/usr/bin/env python3
"""Build an independent blind semantic review from the sealed candidate-free packet only."""
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

# locale order is taken from the candidate-free manifest, never from another review.
PROPOSALS = {
    (1606, "zh-Hans"): ("无法加载共享项", "The caller is the shares settings page, so this means the share entries rather than the contents of one share. The current target duplicates the generic shared-content wording used for the earlier share-contents key.", "moderate"),
    (1606, "ar"): ("تعذر تحميل الموارد المشتركة", "In this shares-page error, المشاركات can read as participation or posts. الموارد المشتركة is the neutral meaning of the shared resources being loaded.", "moderate"),
    (1606, "vi"): ("Không thể tải các mục chia sẻ", "The caller loads the share list. The current wording says shared content, which overlaps the separate share-contents message; this names the shared items.", "moderate"),
    (1608, "vi"): ("Không thể tải các lượt truyền", "This is the Transfers page. The current phrase các mục truyền is an unnatural calque for the transfer records shown there; lượt truyền names transfer instances.", "moderate"),
    (1611, "ko"): ("검증 통계를 불러오지 못했습니다:", "The caller appends a verification error after this label, so the source's colon is meaningful. The current period closes the sentence before the appended detail; 검증 is also the direct technical term for verification.", "high"),
    (1615, "ko"): ("멤버십을 게시하지 못했습니다:", "The caller appends a membership-publish error after this text. The current period closes the sentence before that detail; retain the colon used by the source.", "high"),
    (1616, "de"): ("Die Meinung konnte nicht veröffentlicht werden: {error}", "The pod-opinions caller publishes opinion data. Bewertung narrows this to a rating or score; Meinung preserves the broader source meaning and the error placeholder.", "moderate"),
    (1617, "vi"): ("Không thể xuất bản pod:", "The caller publishes a MediaCore pod object. The current word nhóm means group and changes the object; retain the technical term pod.", "high"),
    (1620, "de"): ("Nahegelegene Atlas-Suchen konnten nicht in die Warteschlange gestellt werden.", "The current adjective nahe is awkward here and can read as spatially close to an atlas. Nahegelegene describes the nearby searches being queued.", "moderate"),
    (1621, "hi"): ("आस-पास की ग्राफ़ खोजों को कतार में नहीं जोड़ा जा सका।", "The current adjective ending पास के does not agree with feminine plural खोजों. This uses the agreeing phrase आस-पास की.", "high"),
    (1621, "fr"): ("Impossible de mettre en file d’attente les recherches de graphe à proximité.", "The current phrase proches du graphe says the searches are close to a graph. The source refers to nearby graph searches, so à proximité modifies the search type.", "moderate"),
    (1621, "id"): ("Gagal memasukkan pencarian graf terdekat ke antrean.", "In this search context, graf is the technical graph term. The current grafik usually means a chart or visual graphic, which changes the search type.", "moderate"),
    (1622, "de"): ("Nahegelegene Suchen konnten nicht in die Warteschlange gestellt werden.", "Benachbart means adjacent or neighboring, while the source means searches available nearby. Nahegelegene is the natural spatial wording here.", "moderate"),
}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def tsha(text):
    return sha(text.encode("utf-8"))


def canon(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def read_jsonl(path):
    return [json.loads(line) for line in Path(path).read_text(encoding="utf-8").splitlines() if line.strip()]


def token_signature(source, target, protected_literals):
    placeholders = lambda text: re.findall(r"\{[A-Za-z_][A-Za-z0-9_]*\}", text)
    tags = lambda text: re.findall(r"</?[A-Za-z][^>]*>", text)
    numbers = lambda text: ["".join(str(unicodedata.digit(c)) if c.isdigit() else c for c in n) for n in re.findall(r"\d+", text)]
    source_numbers = numbers(source)
    target_numbers = numbers(target)
    source_placeholders = placeholders(source)
    target_placeholders = placeholders(target)
    source_tags = tags(source)
    target_tags = tags(target)
    missing = [literal for literal in protected_literals if literal not in target]
    return {
        "placeholderSequenceMatches": source_placeholders == target_placeholders,
        "sourcePlaceholders": source_placeholders,
        "targetPlaceholders": target_placeholders,
        "markupMatches": source_tags == target_tags,
        "sourceMarkupTags": source_tags,
        "targetMarkupTags": target_tags,
        "numericTokensMatch": source_numbers == target_numbers,
        "sourceNumericTokens": source_numbers,
        "targetNumericTokens": target_numbers,
        "protectedLiteralsMatch": not missing,
        "sourceProtectedLiterals": list(protected_literals),
        "missingProtectedLiterals": missing,
    }


def verify_input():
    recorded = {}
    for line in (INPUT / "SHA256SUMS.txt").read_text(encoding="utf-8").splitlines():
        digest, name = line.split("  ", 1)
        path = INPUT / name
        if not path.is_file() or sha(path.read_bytes()) != digest:
            raise SystemExit("REFUSED: candidate-free input checksum mismatch: " + name)
        recorded[name] = digest
    actual = {p.relative_to(INPUT).as_posix() for p in INPUT.rglob("*") if p.is_file() and p.name != "SHA256SUMS.txt"}
    unlisted = actual - set(recorded)
    listed_missing = set(recorded) - actual
    allowed_cache = {name for name in unlisted if name.startswith("__pycache__/") and name.endswith(".pyc")}
    if listed_missing or unlisted != allowed_cache:
        raise SystemExit("REFUSED: candidate-free input checksum inventory mismatch")
    manifest = json.loads((INPUT / "manifest.json").read_text(encoding="utf-8"))
    if manifest.get("head") != HEAD or manifest.get("tree") != TREE or manifest.get("candidateFreeInputOnly") is not True:
        raise SystemExit("REFUSED: candidate-free input pin")
    if manifest.get("cellCount") != 240 or manifest.get("sourceCount") != 20:
        raise SystemExit("REFUSED: candidate-free input coverage")
    return manifest, sha((INPUT / "manifest.json").read_bytes()), sha((INPUT / "SHA256SUMS.txt").read_bytes()), sorted(allowed_cache)


def write_json(name, obj):
    (ROOT / name).write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_jsonl(name, rows):
    with (ROOT / name).open("w", encoding="utf-8", newline="\n") as out:
        for row in rows:
            out.write(json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n")


def main():
    input_manifest, input_manifest_sha, input_sums_sha, unlisted_cache = verify_input()
    locales = input_manifest["localeOrder"]
    if not isinstance(locales, list) or len(locales) != 12:
        raise SystemExit("REFUSED: candidate-free locale order")
    contexts = {row["position"]: row for row in read_jsonl(INPUT / "source-contexts.jsonl")}
    cells = read_jsonl(INPUT / "current-target-cells.jsonl")
    if len(contexts) != 20 or len(cells) != 240:
        raise SystemExit("REFUSED: source context/cell coverage")
    expected_order = [(pos, locale) for pos in range(1603, 1623) for locale in locales]
    if [(row["position"], row["locale"]) for row in cells] != expected_order:
        raise SystemExit("REFUSED: source/current cell order")

    ledger, proposals, holds = [], [], []
    for cell in cells:
        pos, locale = cell["position"], cell["locale"]
        ctx = contexts[pos]
        if cell["sourceKey"] != ctx["sourceKey"] or cell["sourceKeySha256"] != ctx["sourceKeySha256"]:
            raise SystemExit("REFUSED: source/context pin mismatch at " + str(pos))
        if cell["sourceContextSha256"] != ctx["callerContextSha256"]:
            raise SystemExit("REFUSED: caller context hash mismatch at " + str(pos))
        proposal = PROPOSALS.get((pos, locale))
        source = cell["sourceKey"]
        current = cell["currentTarget"]
        if cell["currentTargetSha256"] != tsha(current) or cell["sourceKeySha256"] != tsha(source):
            raise SystemExit("REFUSED: source/current hash mismatch at " + str((pos, locale)))
        if proposal:
            target, rationale, confidence = proposal
            decision = "correction"
        else:
            target, confidence = None, "moderate"
            decision = "accept-current"
            rationale = f"The current wording clearly conveys the failure to {source.removeprefix('Failed to ').removeprefix('Failed to ').removeprefix('Failed to ')} in the pinned caller context."
        target_for_tokens = target if target is not None else current
        token_evidence = token_signature(source, target_for_tokens, cell["sourceProtectedLiterals"])
        if not all(token_evidence[key] for key in ("placeholderSequenceMatches", "markupMatches", "numericTokensMatch", "protectedLiteralsMatch")):
            raise SystemExit("REFUSED: token mismatch at " + str((pos, locale)))
        row = {
            "schemaVersion": 1, "reviewPass": "independent-blind", "head": HEAD, "tree": TREE,
            "position": pos, "locale": locale,
            "sourceKey": source, "sourceKeySha256": cell["sourceKeySha256"],
            "sourceContextSha256": cell["sourceContextSha256"], "callerCount": cell["callerCount"],
            "callerOccurrenceCount": ctx["callerOccurrenceCount"],
            "callerContextSha256": ctx["callerContextSha256"],
            "callerReferencePins": [{"path": c["path"], "line": c["line"], "lineSha256": c["lineSha256"],
                                     "contextSha256": c["contextSha256"], "fileSha256": c["fileSha256"], "gitBlob": c["gitBlob"]}
                                    for c in ctx["callers"]],
            "catalogPath": cell["catalogPath"], "catalogFileSha256": cell["catalogFileSha256"],
            "catalogGitBlob": cell["catalogGitBlob"], "currentTarget": current,
            "currentTargetSha256": cell["currentTargetSha256"],
            "decision": decision, "rationale": rationale, "confidence": confidence,
            "proposedTarget": target, "proposedTargetSha256": tsha(target) if target is not None else None,
            "tokenCheck": token_evidence,
        }
        ledger.append(row)
        if proposal:
            proposals.append({"position": pos, "locale": locale, "sourceKeySha256": cell["sourceKeySha256"],
                              "sourceContextSha256": cell["sourceContextSha256"], "currentTargetSha256": cell["currentTargetSha256"],
                              "proposedTarget": target, "proposedTargetSha256": tsha(target),
                              "rationale": rationale, "confidence": confidence,
                              "tokenCheck": token_evidence})
        if decision == "hold":
            holds.append({"position": pos, "locale": locale, "sourceKeySha256": cell["sourceKeySha256"],
                          "sourceContextSha256": cell["sourceContextSha256"], "currentTargetSha256": cell["currentTargetSha256"],
                          "holdReasonCode": "INSUFFICIENT_PINNED_CONTEXT", "holdReasonSha256": tsha(rationale),
                          "sourceTextIncluded": False, "targetTextIncluded": False})

    counts = collections.Counter(row["decision"] for row in ledger)
    if counts["correction"] != len(PROPOSALS) or len(ledger) != 240:
        raise SystemExit("REFUSED: unexpected blind review coverage or proposal count")
    write_jsonl("blind-ledger.jsonl", ledger)
    write_jsonl("proposals.jsonl", proposals)
    write_jsonl("holds-hash-only.jsonl", holds)
    write_json("summary.json", {
        "artifact": "slskR PR #209 W1603-W1622 independent blind semantic review",
        "window": "W1603-W1622", "head": HEAD, "tree": TREE,
        "candidateFreeInputManifestSha256": input_manifest_sha,
        "candidateFreeInputChecksumListSha256": input_sums_sha,
        "sourceCount": 20, "localeCount": 12, "cellCount": len(ledger),
        "decisionCounts": dict(counts), "proposalCount": len(proposals), "holdCount": len(holds),
        "heldPositions": sorted({row["position"] for row in holds}),
        "allCellsReviewed": True, "candidateFreeInputOnly": True,
        "primaryReviewRead": False, "otherProposalLedgerRead": False,
        "nativeSpeakerSignoff": False, "browserReview": False,
        "tokenChecks": {"placeholderSequence": "PASS", "markup": "PASS", "numericTokens": "PASS", "protectedLiterals": "PASS"},
        "unlistedCandidateFreeCacheObserved": bool(unlisted_cache),
    })
    write_json("input-inventory-note.json", {
        "candidateFreeInputRoot": str(INPUT),
        "listedFilesVerifiedBySha256": True,
        "unlistedFiles": unlisted_cache,
        "unlistedFilesRead": False,
        "unlistedFilesChanged": False,
        "reviewUsesOnlyChecksumListedCandidateFreeFiles": True,
    })
    readme = ("# slskR PR #209 W1603-W1622 independent blind semantic review\n\n"
        "This machine review covers all 240 current-target cells for source positions 1603–1622 across the 12 locales, pinned to head `" + HEAD + "` and tree `" + TREE + "`. "
        "It uses only checksum-listed files from the candidate-free packet and its pinned source/caller contexts; no primary review or other proposal ledger was read. Unlisted files, if present, are excluded and left untouched.\n\n"
        "The review records " + str(counts["accept-current"]) + " accept-current cells, " + str(counts["correction"]) +
        " independent correction proposals, and " + str(counts["hold"]) + " holds. Placeholder, markup, numeric-token, and protected-literal checks pass for every current cell and proposal.\n\n"
        "This is machine review only. No native-speaker signoff or browser review is claimed. The review files are independent scratch evidence and do not modify the repository, catalogs, PR, or workflows.\n")
    (ROOT / "README.md").write_text(readme, encoding="utf-8")

    payloads = sorted(p.relative_to(ROOT).as_posix() for p in ROOT.rglob("*") if p.is_file() and p.name not in {"manifest.json", "SHA256SUMS.txt"})
    file_rows = [{"path": name, "sha256": sha((ROOT / name).read_bytes()), "byteCount": (ROOT / name).stat().st_size} for name in payloads]
    write_json("manifest.json", {
        "artifact": "slskR PR #209 W1603-W1622 independent blind semantic review",
        "schemaVersion": 1, "repository": "snapetech-org/slskR", "pullRequest": 209,
        "window": "W1603-W1622", "head": HEAD, "tree": TREE,
        "candidateFreeInputManifestSha256": input_manifest_sha,
        "candidateFreeInputChecksumListSha256": input_sums_sha,
        "unlistedCandidateFreeCacheObserved": bool(unlisted_cache),
        "sourceCount": 20, "localeCount": 12, "cellCount": len(ledger),
        "localeOrder": locales, "decisionCounts": dict(counts),
        "proposalCount": len(proposals), "holdCount": len(holds),
        "candidateFreeInputOnly": True, "primaryReviewRead": False,
        "otherProposalLedgerRead": False, "nativeSpeakerSignoff": False,
        "browserReview": False, "files": file_rows,
    })
    sealed = sorted(p.relative_to(ROOT).as_posix() for p in ROOT.rglob("*") if p.is_file() and p.name != "SHA256SUMS.txt")
    (ROOT / "SHA256SUMS.txt").write_text("\n".join(f"{sha((ROOT / name).read_bytes())}  {name}" for name in sealed) + "\n", encoding="utf-8")
    print(json.dumps({"result": "SEALED-INDEPENDENT-BLIND-REVIEW", "head": HEAD, "tree": TREE,
                      "cells": len(ledger), "decisions": dict(counts), "proposals": len(proposals), "holds": len(holds),
                      "inputManifestSha256": input_manifest_sha}, indent=2))


if __name__ == "__main__":
    main()
