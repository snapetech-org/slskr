#!/usr/bin/env python3
from collections import Counter
from pathlib import Path
import hashlib
import json
import re
import sys

INPUT = Path("/home/keith/Documents/code/task-scratch/slskr-pr204-w1383-1402-primary-20261103/candidate-free-input")
OUT = Path(__file__).resolve().parent
HEAD = "b5da2589b6e8f2d4b0c0faab28bcdf0481e42438"
TREE = "36ae6ecf3b705995fbd549cb8650d6458936df91"
BRANCH = "codex/slskr-l10n-audit-20261030"
BASE_SHA = "2a2b188f10b9460a15bc6d5c34e406b0193d51ba"
WINDOW = "W1383-W1402"
POSITIONS = list(range(1383, 1403))
LOCALE_ORDER = ["es", "zh-Hans", "hi", "de", "ja", "fr", "pt-BR", "ar", "ko", "zh-Hant", "vi", "id"]
PLACEHOLDER = re.compile(r"\{[A-Za-z][A-Za-z0-9_]*\}")
NUMBER = re.compile(r"\d+(?:[.,]\d+)*")
MARKUP = re.compile(r"</?[A-Za-z][^>]*>")

ACCEPT_RATIONALES = {
    1383: "The caller shows the count in export metadata; the current label accurately names the number of entries.",
    1384: "The security panel uses this label for its entropy-check count; the current wording preserves the technical meaning.",
    1385: "The current generic error heading is suitable for its repeated error banners and the log-level filter.",
    1386: "The compatibility dashboard chart groups error counts by type; the current title is clear.",
    1387: "The current translation preserves Swarm as the feature name and identifies its data-loading failure.",
    1388: "The compatibility dashboard uses this as the error-count report label; the current wording is clear.",
    1389: "The caller labels the compatibility error-history chart; the current wording conveys that history.",
    1390: "The current translation preserves the error prefix and its colon before the dynamic error text.",
    1391: "The current value communicates the errored state in its transfer and retention callers.",
    1392: "The current plural noun is suitable for the compatibility dashboard's Errors tab.",
    1393: "The current opening parenthesis pairs with the caller's appended count and closing parenthesis.",
    1394: "A revised proposal is recorded because this caller displays a false-positive rate as a percentage.",
    1395: "The current label accurately introduces the estimated impact percentage in the Swarm recommendation.",
    1396: "The current label accurately describes the estimated storage size shown in MB.",
    1397: "A revised proposal is recorded where the local-only and peer-query meaning needs clearer wording.",
    1398: "The current label accurately names the form's event-history filters.",
    1399: "The current heading clearly reports that event history is unavailable.",
    1400: "A revised proposal is recorded because literal translations of retry shape are unclear in this settings-card description.",
    1401: "The current label accurately names the event-kind filter.",
    1402: "The current label clearly names the event-retention duration in days.",
}

def sha(data):
    return hashlib.sha256(data).hexdigest()

def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")

def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))

def read_jsonl(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]

def verify_input():
    sums = {}
    for line in (INPUT / "SHA256SUMS.txt").read_text(encoding="utf-8").splitlines():
        digest, name = line.split(None, 1)
        name = name.strip()
        if name in sums:
            raise SystemExit("duplicate candidate-free input checksum")
        sums[name] = digest
    packet = read_json(INPUT / "manifest.json")
    required = set(packet["fileHashes"]) | {"manifest.json"}
    if set(sums) != required:
        raise SystemExit("candidate-free packet checksum inventory mismatch")
    for name, digest in sums.items():
        path = INPUT / name
        if not path.is_file() or sha(path.read_bytes()) != digest:
            raise SystemExit(f"candidate-free input checksum failure: {name}")
    att = read_json(INPUT / "PR-attestation.json")
    expected_att = {
        "repository": "snapetech-org/slskR", "pullRequest": 204, "state": "OPEN",
        "draft": True, "branch": BRANCH, "head": HEAD, "tree": TREE,
        "baseRef": "main", "baseSha": BASE_SHA,
    }
    for key, value in expected_att.items():
        if att.get(key) != value:
            raise SystemExit(f"candidate-free PR attestation mismatch: {key}")
    if (packet["repository"], packet["pullRequest"], packet["head"], packet["tree"],
        packet["headRef"], packet["baseRef"], packet["baseSha"]) != (
        "snapetech-org/slskR", 204, HEAD, TREE, BRANCH, "main", BASE_SHA
    ):
        raise SystemExit("candidate-free exact-head/tree/window binding mismatch")
    if (packet["selectedPositions"], packet["sourceCount"], packet["localeCount"],
        packet["cellCount"], packet["callerResolutionHoldCount"]) != (
        [1383, 1402], 20, 12, 240, 0
    ):
        raise SystemExit("candidate-free window inventory mismatch")
    if packet["callerlessPositions"] if "callerlessPositions" in packet else []:
        raise SystemExit("candidate-free input reports callerless selected positions")
    current = read_jsonl(INPUT / "current-target-cells.jsonl")
    contexts = read_jsonl(INPUT / "source-contexts.jsonl")
    if len(current) != 240 or len(contexts) != 20:
        raise SystemExit("candidate-free source/cell count mismatch")
    cells = {(r["position"], r["locale"]): r for r in current}
    by_pos = {r["position"]: r for r in contexts}
    expected_cells = {(p, l) for p in POSITIONS for l in packet["localeOrder"]}
    if set(cells) != expected_cells or set(by_pos) != set(POSITIONS):
        raise SystemExit("candidate-free cell inventory is not contiguous")
    for pos in POSITIONS:
        ctx = by_pos[pos]
        if ctx["productionCallerCount"] < 1 or not ctx["callers"]:
            raise SystemExit(f"selected source lacks a pinned production caller: {pos}")
        for locale in packet["localeOrder"]:
            cell = cells[(pos, locale)]
            if (cell["sourceKey"], cell["sourceKeySha256"], cell["sourceContextSha256"]) != (
                ctx["sourceKey"], ctx["sourceKeySha256"], ctx["callerContextSha256"]
            ):
                raise SystemExit(f"cell/source/caller pin mismatch: {pos}/{locale}")
            if cell["callerCount"] != ctx["productionCallerCount"]:
                raise SystemExit(f"caller count mismatch: {pos}/{locale}")
            if any(not cell[k] for k in ("placeholderSequenceMatches", "markupMatches",
                                         "numericTokensMatch", "protectedLiteralsMatch")):
                raise SystemExit(f"candidate-free baseline token mismatch: {pos}/{locale}")
            if sha(cell["currentTarget"].encode("utf-8")) != cell["currentTargetSha256"]:
                raise SystemExit(f"current target hash mismatch: {pos}/{locale}")
    prior_holds = read_jsonl(INPUT / "prior-hold-reattestation.jsonl")
    if len(prior_holds) != 35 or any(
        r["reattestation"] != "same" or r["currentTarget"] != r["priorCurrentTarget"]
        or r["currentTargetSha256"] != r["priorCurrentTargetSha256"]
        for r in prior_holds
    ):
        raise SystemExit("predecessor hold preservation check failed")
    prior_selection = read_jsonl(INPUT / "prior-selection-reattestation.jsonl")
    if len(prior_selection) != 140:
        raise SystemExit("predecessor selection reattestation count mismatch")
    return packet, cells, by_pos, sums, prior_holds, prior_selection

def token_checks(cell, reviewed):
    source = cell["sourceKey"]
    ph_source = PLACEHOLDER.findall(source)
    ph_reviewed = PLACEHOLDER.findall(reviewed)
    num_source = NUMBER.findall(source)
    num_reviewed = NUMBER.findall(reviewed)
    markup_source = MARKUP.findall(source)
    markup_reviewed = MARKUP.findall(reviewed)
    protected = cell["sourceProtectedLiterals"]
    return {
        "placeholderSequencePreserved": ph_source == ph_reviewed == cell["sourcePlaceholders"],
        "numericTokensPreserved": num_source == num_reviewed == cell["sourceNumericTokens"],
        "markupPreserved": markup_source == markup_reviewed == cell["sourceMarkupTags"],
        "protectedLiteralsPreserved": all(source.count(x) == reviewed.count(x) for x in protected),
    }

def make_ledger(packet, cells, contexts, decisions):
    if len(decisions) != 58:
        raise SystemExit("primary decision inventory must contain 58 explicit review proposals")
    expected_review_keys = {
        (pos, loc) for pos in POSITIONS for loc in packet["localeOrder"]
    }
    if not set(cells) == expected_review_keys:
        raise SystemExit("primary ledger cell inventory mismatch")
    allowed = {(pos, locale) for pos in POSITIONS for locale in packet["localeOrder"]}
    decision_keys = set()
    for key in decisions:
        pos_text, locale = key.split("|", 1)
        cell_key = (int(pos_text), locale)
        if cell_key not in allowed or cell_key in decision_keys:
            raise SystemExit(f"invalid/duplicate explicit decision: {key}")
        decision_keys.add(cell_key)
    rows = []
    technical = Counter()
    for pos in POSITIONS:
        ctx = contexts[pos]
        for locale in packet["localeOrder"]:
            cell = cells[(pos, locale)]
            key = f"{pos}|{locale}"
            explicit = decisions.get(key)
            if explicit:
                decision = explicit["disposition"]
                proposed = explicit["proposal"]
                rationale = explicit["rationale"]
                confidence = explicit["confidence"]
                if decision not in ("correction", "refinement") or not proposed:
                    raise SystemExit(f"invalid explicit proposal disposition at {key}")
                reviewed = proposed
            else:
                decision = "accept-current"
                proposed = None
                rationale = ACCEPT_RATIONALES[pos]
                confidence = "moderate"
                reviewed = cell["currentTarget"]
            checks = token_checks(cell, reviewed)
            if not all(checks.values()):
                raise SystemExit(f"reviewed token check failed at {key}: {checks}")
            technical.update({k: 0 if v else 1 for k, v in checks.items()})
            caller_refs = cell["callerRefs"]
            rows.append({
                "schemaVersion": 1,
                "repository": "snapetech-org/slskR",
                "pullRequest": 204,
                "window": WINDOW,
                "head": HEAD,
                "tree": TREE,
                "position": pos,
                "historicalSourceOrdinal": cell["historicalSourceOrdinal"],
                "sourceKey": cell["sourceKey"],
                "sourceKeySha256": cell["sourceKeySha256"],
                "locale": locale,
                "currentTarget": cell["currentTarget"],
                "currentTargetSha256": cell["currentTargetSha256"],
                "catalogPath": cell["catalogPath"],
                "catalogGitBlob": cell["catalogGitBlob"],
                "catalogFileSha256": cell["catalogFileSha256"],
                "catalogKeyCount": cell["catalogKeyCount"],
                "callerContextSha256": cell["sourceContextSha256"],
                "callerCount": cell["callerCount"],
                "callerRefs": caller_refs,
                "callerContextConfidence": "high",
                "decision": decision,
                "proposedTarget": proposed,
                "reviewedTargetSha256": sha(reviewed.encode("utf-8")),
                "confidence": confidence,
                "rationale": rationale,
                "technicalChecks": checks,
            })
    if len(rows) != 240 or len({(x["position"], x["locale"]) for x in rows}) != 240:
        raise SystemExit("primary review is not a complete 240-cell ledger")
    if Counter(x["decision"] for x in rows) != Counter({
        "accept-current": 182, "correction": 46, "refinement": 12
    }):
        raise SystemExit("unexpected primary decision counts")
    if technical != Counter({
        "placeholderSequencePreserved": 0, "numericTokensPreserved": 0,
        "markupPreserved": 0, "protectedLiteralsPreserved": 0
    }):
        raise SystemExit("unexpected primary token-check totals")
    return rows, technical

def make_manifest(packet, input_sums, prior_holds, prior_selection, rows, technical, ledger_bytes, decision_bytes, live):
    counts = Counter(x["decision"] for x in rows)
    per_locale = {
        locale: dict(sorted(Counter(x["decision"] for x in rows if x["locale"] == locale).items()))
        for locale in packet["localeOrder"]
    }
    return {
        "schemaVersion": 1,
        "artifact": "slskR PR #204 W1383-W1402 primary localization review",
        "repository": "snapetech-org/slskR",
        "pullRequest": 204,
        "window": WINDOW,
        "range": [1383, 1402],
        "head": HEAD,
        "tree": TREE,
        "branch": BRANCH,
        "baseRef": "main",
        "baseSha": BASE_SHA,
        "liveRefAttestation": live,
        "inputPins": {
            "candidateFreeInputOnly": True,
            "candidateFreeManifestSha256": sha((INPUT / "manifest.json").read_bytes()),
            "candidateFreeChecksumListSha256": sha((INPUT / "SHA256SUMS.txt").read_bytes()),
            "sourceQueueSha256": packet["sourceQueueFileSha256"],
            "sourceLookupKeyOrderSha256": packet["sourceLookupKeyOrderSha256"],
            "currentTargetCellsSha256": input_sums["current-target-cells.jsonl"],
            "sourceContextsSha256": input_sums["source-contexts.jsonl"],
            "localizationRuntimeContextSha256": input_sums["localization-runtime-context.json"],
            "inputPacketHashes": input_sums,
        },
        "review": {
            "cells": len(rows),
            "sourceCount": 20,
            "localeCount": 12,
            "localeOrder": packet["localeOrder"],
            "callerReferences": packet["callerReferenceCount"],
            "callerOccurrences": packet["callerOccurrenceCount"],
            "callerlessPositions": [],
            "decisionCounts": dict(sorted(counts.items())),
            "decisionCountsByLocale": per_locale,
            "confidenceCounts": dict(sorted(Counter(x["confidence"] for x in rows).items())),
            "callerContextConfidenceCounts": dict(sorted(Counter(x["callerContextConfidence"] for x in rows).items())),
            "proposalCount": sum(x["proposedTarget"] is not None for x in rows),
            "holdCount": counts.get("hold", 0),
            "tokenCheckFailures": dict(sorted(technical.items())),
        },
        "priorPreservation": {
            "holdsReattested": len(prior_holds),
            "changedPriorHolds": 0,
            "priorHoldReattestationSha256": input_sums["prior-hold-reattestation.jsonl"],
            "selectedRowsReattested": len(prior_selection),
            "priorSelectionReattestationSha256": input_sums["prior-selection-reattestation.jsonl"],
        },
        "nativeSpeakerReview": "not performed; no native-speaker approval claimed",
        "applicationStatus": "review evidence only; no repository/catalog/PR mutation",
        "activity": {
            "repositoryFilesOpened": 0,
            "primaryLedgerOrProposalValuesFromOtherReviewersOpened": 0,
            "testsBuildsCI": "not run",
            "browserReview": "not performed",
            "releaseOrTag": "not performed",
        },
        "sealedLedger": {
            "path": "primary-ledger.jsonl",
            "byteCount": len(ledger_bytes),
            "sha256": sha(ledger_bytes),
            "orderedCellIdsSha256": sha(canonical([f'{x["position"]}:{x["locale"]}' for x in rows])),
        },
        "reviewDecisionsSha256": sha(decision_bytes),
        "liveRefAttestationSha256": sha((OUT / "live-ref-attestation.json").read_bytes()),
    }

def verify():
    packet, cells, contexts, input_sums, prior_holds, prior_selection = verify_input()
    live = read_json(OUT / "live-ref-attestation.json")
    if (live.get("repository"), live.get("pullRequest"), live.get("state"), live.get("draft"),
        live.get("headRef"), live.get("headSha"), live.get("branchRefSha"), live.get("tree"),
        live.get("baseRef"), live.get("baseSha")) != (
        "snapetech-org/slskr", 204, "open", True, BRANCH, HEAD, HEAD, TREE, "main", BASE_SHA
    ):
        raise SystemExit("live PR/branch/tree attestation mismatch")
    decisions_path = OUT / "review-decisions.json"
    decision_bytes = decisions_path.read_bytes()
    decisions = json.loads(decision_bytes.decode("utf-8"))
    rows, technical = make_ledger(packet, cells, contexts, decisions)
    expected_bytes = b"".join(canonical(x) + b"\n" for x in rows)
    ledger_path = OUT / "primary-ledger.jsonl"
    ledger_bytes = ledger_path.read_bytes()
    if ledger_bytes != expected_bytes:
        raise SystemExit("sealed primary ledger differs from verified input/decisions")
    manifest = read_json(OUT / "manifest.json")
    expected_manifest = make_manifest(packet, input_sums, prior_holds, prior_selection, rows, technical,
                                      ledger_bytes, decision_bytes, live)
    if manifest != expected_manifest:
        raise SystemExit("primary manifest does not match recomputed review evidence")
    sums = {}
    for line in (OUT / "SHA256SUMS.txt").read_text(encoding="utf-8").splitlines():
        digest, name = line.split(None, 1)
        name = name.strip()
        if name in sums:
            raise SystemExit("duplicate output checksum entry")
        sums[name] = digest
    required = {"README.md", "manifest.json", "primary-ledger.jsonl",
                "review-decisions.json", "live-ref-attestation.json", Path(__file__).name}
    if set(sums) != required:
        raise SystemExit("output checksum inventory mismatch")
    for name, digest in sums.items():
        if sha((OUT / name).read_bytes()) != digest:
            raise SystemExit(f"primary output checksum failure: {name}")
    print(json.dumps({
        "pass": True,
        "verifier": "candidate-free input checksums, live PR/branch/tree pins, 240 caller-bound decisions, token checks, prior holds, and sealed outputs",
        "head": HEAD, "tree": TREE, "cells": len(rows),
        "decisions": dict(sorted(Counter(x["decision"] for x in rows).items())),
        "proposals": sum(x["proposedTarget"] is not None for x in rows),
        "callerless": 0, "priorHoldsReattested": len(prior_holds),
        "priorHoldsChanged": 0, "priorSelectionsReattested": len(prior_selection),
        "tokenCheckFailures": dict(sorted(technical.items())),
        "ledgerSha256": manifest["sealedLedger"]["sha256"],
        "outputBytes": sum((OUT / name).stat().st_size for name in required | {"SHA256SUMS.txt"}),
    }, ensure_ascii=False, indent=2))

def build():
    if (OUT / "manifest.json").exists() or (OUT / "primary-ledger.jsonl").exists():
        raise SystemExit("Refusing to overwrite sealed primary review output")
    packet, cells, contexts, input_sums, prior_holds, prior_selection = verify_input()
    live = read_json(OUT / "live-ref-attestation.json")
    decisions_path = OUT / "review-decisions.json"
    decision_bytes = decisions_path.read_bytes()
    decisions = json.loads(decision_bytes.decode("utf-8"))
    rows, technical = make_ledger(packet, cells, contexts, decisions)
    ledger_bytes = b"".join(canonical(x) + b"\n" for x in rows)
    (OUT / "primary-ledger.jsonl").write_bytes(ledger_bytes)
    manifest = make_manifest(packet, input_sums, prior_holds, prior_selection, rows, technical,
                             ledger_bytes, decision_bytes, live)
    (OUT / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    readme = """# slskR PR #204 W1383-W1402 primary localization review

This sealed review covers 240 current target cells across 20 source keys and 12 locales at exact head b5da2589b6e8f2d4b0c0faab28bcdf0481e42438 and tree 36ae6ecf3b705995fbd549cb8650d6458936df91.

The input was limited to the specified candidate-free packet. It contains source keys, current targets, exact production caller contexts, locale catalog hashes, and runtime lookup context; no prior primary ledger or prior proposal values were opened. Live PR metadata, the branch ref, and the commit tree were independently re-attested before review. The packet checksum inventory and its verifier passed.

The review records 182 accept-current cells, 46 corrections, 12 refinements, and no holds. All 49 caller references are pinned; no selected cell is callerless. Placeholder, numeric, markup, and protected-literal checks pass for current and reviewed values.

All 35 predecessor holds were reattested unchanged, and the 140 previously selected rows remain reattested. Caller/context binding is high confidence. Translation judgments are machine-assisted at moderate confidence; qualified native-speaker review has not been performed.

No repository, catalog, or PR files were changed. No tests, builds, CI, browser review, releases, or tags were run.
"""
    (OUT / "README.md").write_text(readme, encoding="utf-8")
    files = ["README.md", "manifest.json", "primary-ledger.jsonl",
             "review-decisions.json", "live-ref-attestation.json", Path(__file__).name]
    (OUT / "SHA256SUMS.txt").write_text(
        "".join(f"{sha((OUT / name).read_bytes())}  {name}\n" for name in sorted(files)),
        encoding="utf-8",
    )
    verify()

if __name__ == "__main__":
    if sys.argv[1:] == ["--build"]:
        build()
    elif sys.argv[1:] in ([], ["--verify"]):
        verify()
    else:
        raise SystemExit("Usage: verify_primary_review.py [--build|--verify]")
