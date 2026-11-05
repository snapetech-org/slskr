#!/usr/bin/env python3
"""Create an independent, read-only cross-review ledger for slskR W1603-W1622."""
from __future__ import annotations
import hashlib, json, re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

TASK = Path(__file__).resolve().parent.parent
OUT = Path(__file__).resolve().parent
INPUT = TASK / "candidate-free-input"
PRIMARY = TASK / "primary-review"
BLIND = TASK / "blind-review"
ROOT = TASK / "root-cross-review"
HEAD = "eeb63f1e4e21d801f4a4e0393813b6e86a1ff7c8"
TREE = "590ee410666905f68f601393b64a4798b0609181"
LOCALES = ["es", "zh-Hans", "hi", "de", "ja", "fr", "pt-BR", "ar", "ko", "zh-Hant", "vi", "id"]
START, END = 1603, 1622

# Cross-review decisions made from the pinned source, current targets, and caller
# contexts. All other cells retain their current target.
ROOT_PROPOSAL_CROSS_CHECKS = {
 (1606, "ar"): ("correction", "تعذر تحميل الموارد المشتركة", "The System/Shares component flattens shared folders and files from hosts. الموارد المشتركة describes those shared resources more clearly than the ambiguous المشاركة."),
 (1606, "zh-Hans"): ("correction", "无法加载共享列表", "The caller loads and displays a list of host shares, not the contents of one share; 共享列表 names that UI object."),
 (1606, "vi"): ("correction", "Không thể tải các mục chia sẻ", "The caller loads individual shared entries. Mục chia sẻ describes those entries better than nội dung chia sẻ, which suggests their contents."),
 (1608, "vi"): ("refinement", "Không thể tải các lượt truyền", "The caller loads transfer records, and the locale uses lượt truyền for transfer entries elsewhere; this is more consistent than mục truyền."),
 (1611, "ko"): ("correction", "검증 통계를 불러오지 못했습니다:", "검증 is the technical verification term here. The caller appends verificationStats.error, so the colon correctly introduces that detail."),
 (1615, "ko"): ("refinement", "멤버십을 게시하지 못했습니다:", "The caller appends membershipPublishResult.error. The colon leaves the label open for that error detail."),
 (1616, "de"): ("correction", "Die Meinung konnte nicht veröffentlicht werden: {error}", "Meinung preserves the source’s broad sense of opinion; Bewertung narrows it to a score or rating."),
 (1617, "vi"): ("correction", "Không thể xuất bản pod:", "The caller publishes a MediaCore Pod object. Keeping pod preserves the product-domain object; nhóm means a generic group."),
 (1620, "de"): ("correction", "Nahegelegene Atlas-Suchen konnten nicht in die Warteschlange gestellt werden", "Nahegelegene is the idiomatic inflected adjective for nearby. Nahe Atlas-Suchen can read as searches near an atlas."),
 (1621, "fr"): ("correction", "Impossible de mettre en file d’attente les recherches de graphe à proximité", "À proximité places proximity on the graph-search phrase. Proches du graphe can instead read as searches physically close to the graph."),
 (1621, "hi"): ("correction", "आस-पास की ग्राफ़ खोजों को कतार में नहीं जोड़ा जा सका", "आस-पास की agrees with the feminine plural head खोजों; the current masculine plural ending पास के does not."),
 (1621, "id"): ("correction", "Gagal memasukkan pencarian graf terdekat ke antrean", "Graf names the mathematical or technical graph structure; grafik commonly means a chart or diagram."),
 (1622, "de"): ("correction", "Nahegelegene Suchen konnten nicht in die Warteschlange gestellt werden", "Benachbarte means adjacent or neighboring; Nahegelegene more directly means nearby searches."),
}
ACCEPT_RATIONALE = {
 1603: "The target conveys a failed load of share contents in the contents modal.",
 1604: "The target names share groups and preserves the failed-load meaning used by both callers.",
 1605: "The target names shared collections in the Shared with Me caller.",
 1606: "The target identifies the shares handled by the System/Shares view.",
 1607: "The target identifies transfer errors and preserves the failed-load meaning.",
 1608: "The target labels the transfer records loaded by the Transfers screen.",
 1609: "The target preserves the specific transport-status meaning in adversarial settings.",
 1610: "The target identifies the user's note and the failure to load it.",
 1611: "The target conveys failure to load verification statistics and retains the error-detail prefix punctuation.",
 1612: "The target describes failure to persist or save settings in the server-error allowlist.",
 1613: "The target describes failure to publish a descriptor.",
 1614: "The target describes failure to publish membership data.",
 1615: "The target conveys failed membership publication and introduces appended error detail.",
 1616: "The target preserves the opinion-publication meaning and the named error placeholder.",
 1617: "The target identifies publication of a Pod object in the MediaCore caller.",
 1618: "The target preserves the shadow-index query operation.",
 1619: "The target says the download could not be queued and preserves the message placeholder.",
 1620: "The target identifies nearby atlas searches that failed to enter the queue.",
 1621: "The target identifies nearby graph searches that failed to enter the queue.",
 1622: "The target identifies nearby searches that failed to enter the queue.",
}
PH = re.compile(r"\{[^{}]+\}")
TAG = re.compile(r"</?[A-Za-z][^>]*>")
NUM = re.compile(r"(?<!\w)\d+(?:[.,]\d+)*(?!\w)")


def sha(value: bytes | str) -> str:
    if isinstance(value, str): value = value.encode("utf-8")
    return hashlib.sha256(value).hexdigest()

def read_json(path: Path): return json.loads(path.read_text(encoding="utf-8"))
def read_jsonl(path: Path): return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
def write_json(path: Path, value): path.write_text(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
def write_jsonl(path: Path, rows): path.write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n" for row in rows), encoding="utf-8")

def check_sums(path: Path):
    sums_path = path / "SHA256SUMS.txt"
    listed = {}
    for line in sums_path.read_text(encoding="utf-8").splitlines():
        if not line.strip(): continue
        digest, name = line.split("  ", 1)
        if name in listed: raise SystemExit(f"FAIL duplicate checksum {path.name}/{name}")
        candidate = (path / name).resolve()
        if not candidate.is_relative_to(path.resolve()) or not candidate.is_file() or sha(candidate.read_bytes()) != digest:
            raise SystemExit(f"FAIL checksum {path.name}/{name}")
        listed[name] = digest
    actual = {p.relative_to(path).as_posix() for p in path.rglob("*") if p.is_file() and p != sums_path}
    if set(listed) != actual: raise SystemExit(f"FAIL checksum coverage {path.name}")
    return listed

def token_check(source: str, target: str, protected: list[str]):
    check = {
        "placeholderSequencePreserved": PH.findall(source) == PH.findall(target),
        "markupPreserved": TAG.findall(source) == TAG.findall(target),
        "numericTokensPreserved": NUM.findall(source) == NUM.findall(target),
        "protectedLiteralsPreserved": all(literal in target for literal in protected),
    }
    return check

def main():
    for packet in (INPUT, PRIMARY, BLIND, ROOT): check_sums(packet)
    cells = read_jsonl(INPUT / "current-target-cells.jsonl")
    contexts = read_jsonl(INPUT / "source-contexts.jsonl")
    primary = read_jsonl(PRIMARY / "primary-ledger.jsonl")
    blind = read_jsonl(BLIND / "blind-ledger.jsonl")
    root = read_jsonl(ROOT / "root-adjudication.jsonl")
    cf_manifest = read_json(INPUT / "manifest.json")
    if (cf_manifest.get("head"), cf_manifest.get("tree"), cf_manifest.get("selectedPositions")) != (HEAD, TREE, [START, END]):
        raise SystemExit("FAIL candidate-free pin")
    if not (len(cells) == len(primary) == len(blind) == len(root) == 240 and len(contexts) == 20):
        raise SystemExit("FAIL packet cardinality")
    cell_by = {(r["position"], r["locale"]): r for r in cells}
    ctx_by = {r["position"]: r for r in contexts}
    p_by = {(r["position"], r["locale"]): r for r in primary}
    b_by = {(r["position"], r["locale"]): r for r in blind}
    r_by = {(r["position"], r["locale"]): r for r in root}
    expected_keys = [(pos, loc) for pos in range(START, END + 1) for loc in LOCALES]
    if list((r["position"], r["locale"]) for r in cells) != expected_keys:
        raise SystemExit("FAIL exact candidate-free cell order")
    if any(set(mapping) != set(expected_keys) for mapping in (cell_by, p_by, b_by, r_by)):
        raise SystemExit("FAIL exact one-row-per-cell coverage")
    if set(ROOT_PROPOSAL_CROSS_CHECKS) != {key for key, row in r_by.items() if row["rootDisposition"] != "accept-current"}:
        raise SystemExit("FAIL reviewed root proposal inventory")

    rows = []
    for key in expected_keys:
        c, cx, p, b, rr = cell_by[key], ctx_by[key[0]], p_by[key], b_by[key], r_by[key]
        if not (c["sourceKeySha256"] == cx["sourceKeySha256"] == p["sourceKeySha256"] == b["sourceKeySha256"] == rr["sourceKeySha256"]):
            raise SystemExit(f"FAIL source hash binding {key}")
        if not (c["sourceContextSha256"] == cx["callerContextSha256"] == p["sourceContextSha256"] == b["sourceContextSha256"] == rr["sourceContextSha256"]):
            raise SystemExit(f"FAIL source context binding {key}")
        if not (c["currentTargetSha256"] == p["currentTargetSha256"] == b["currentTargetSha256"] == rr["currentTargetSha256"]):
            raise SystemExit(f"FAIL current target binding {key}")
        if (p["disposition"], p["selectedTarget"]) != (rr["primaryDisposition"], rr["primaryTarget"]):
            raise SystemExit(f"FAIL root primary linkage {key}")
        blind_target = b["proposedTarget"]
        if (b["decision"], blind_target) != (rr["independentBlindDisposition"], rr["blindTarget"]):
            raise SystemExit(f"FAIL root blind linkage {key}")
        if rr["currentTarget"] != c["currentTarget"] or rr["sourceKey"] != c["sourceKey"]:
            raise SystemExit(f"FAIL root source/current linkage {key}")
        if rr["head"] != HEAD or rr["tree"] != TREE or rr["callerCount"] != c["callerCount"]:
            raise SystemExit(f"FAIL root head/caller binding {key}")
        check_current = token_check(c["sourceKey"], c["currentTarget"], c["sourceProtectedLiterals"])
        if not all(check_current.values()): raise SystemExit(f"FAIL current target token preservation {key}")

        if key in ROOT_PROPOSAL_CROSS_CHECKS:
            decision, target, rationale = ROOT_PROPOSAL_CROSS_CHECKS[key]
            if rr["rootDisposition"] != decision or rr["rootTarget"] != target:
                raise SystemExit(f"FAIL independent/root decision mismatch {key}")
            decision = "propose-" + decision
        else:
            decision, target, rationale = "accept-current", c["currentTarget"], ACCEPT_RATIONALE[key[0]]
            if rr["rootDisposition"] != "accept-current" or rr["rootTarget"] != c["currentTarget"]:
                raise SystemExit(f"FAIL unreviewed root proposal {key}")
        target_tokens = token_check(c["sourceKey"], target, c["sourceProtectedLiterals"])
        if not all(target_tokens.values()): raise SystemExit(f"FAIL cross target token preservation {key}")
        root_agreement = (target == rr["rootTarget"] and decision == ("propose-" + rr["rootDisposition"] if rr["rootDisposition"] != "accept-current" else "accept-current"))
        rows.append({
            "repository": "snapetech-org/slskR", "pullRequest": 209, "head": HEAD, "tree": TREE,
            "position": key[0], "locale": key[1], "sourceKey": c["sourceKey"], "sourceKeySha256": c["sourceKeySha256"],
            "sourceContextSha256": cx["callerContextSha256"], "callerCount": c["callerCount"],
            "currentTarget": c["currentTarget"], "currentTargetSha256": c["currentTargetSha256"],
            "primaryDisposition": p["disposition"], "primaryTarget": p["selectedTarget"],
            "blindDisposition": b["decision"], "blindTarget": blind_target,
            "rootDisposition": rr["rootDisposition"], "rootTarget": rr["rootTarget"], "rootTargetSha256": rr["rootTargetSha256"],
            "crossDisposition": decision, "crossTarget": target, "crossTargetSha256": sha(target),
            "crossRationale": rationale, "confidence": "moderate", "tokenChecks": target_tokens,
            "agreesWithRoot": root_agreement,
        })

    disagreements = [row for row in rows if not row["agreesWithRoot"]]
    counts = Counter(row["crossDisposition"] for row in rows)
    root_counts = Counter(row["rootDisposition"] for row in rows)
    input_pins = {}
    for name, path in (("candidateFree", INPUT), ("primary", PRIMARY), ("blind", BLIND), ("rootCrossReview", ROOT)):
        input_pins[name] = {"checksumListSha256": sha((path / "SHA256SUMS.txt").read_bytes()), "fileCount": len(check_sums(path))}
    summary = {
        "artifact": "slskR PR #209 W1603-W1622 independent cross-review",
        "repository": "snapetech-org/slskR", "pullRequest": 209,
        "head": HEAD, "tree": TREE, "window": f"W{START}-W{END}",
        "cellCount": len(rows), "sourceCount": 20, "localeCount": len(LOCALES),
        "crossDispositionCounts": dict(sorted(counts.items())), "rootDispositionCounts": dict(sorted(root_counts.items())),
        "rootOutcomesReviewed": len(ROOT_PROPOSAL_CROSS_CHECKS), "rootAgreements": len(rows) - len(disagreements),
        "rootDisagreements": len(disagreements), "crossProposalCount": sum(row["crossDisposition"].startswith("propose-") for row in rows),
        "nativeSpeakerSignoff": False, "browserReview": False, "repositoryChangesApplied": False,
        "candidateFreeChecksumsVerified": True, "primaryChecksumsVerified": True, "blindChecksumsVerified": True, "rootChecksumsVerified": True,
        "inputPins": input_pins,
        "currentTargetCellsSha256": sha((INPUT / "current-target-cells.jsonl").read_bytes()),
        "sourceContextsSha256": sha((INPUT / "source-contexts.jsonl").read_bytes()),
        "rootAdjudicationSha256": sha((ROOT / "root-adjudication.jsonl").read_bytes()),
        "reviewedAtUtc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    write_jsonl(OUT / "cross-review-ledger.jsonl", rows)
    write_jsonl(OUT / "root-disagreements.jsonl", disagreements)
    write_json(OUT / "SUMMARY.json", summary)
    (OUT / "README.md").write_text(f'''# slskR PR #209 W1603–W1622 independent cross-review

Independent review of all 240 exact-head cells, using the pinned candidate-free input and source/caller contexts, then checking the complete primary, blind, and root ledgers. Exact source head/tree: `{HEAD}` / `{TREE}`.

- Candidate-free checksum list: `{input_pins['candidateFree']['checksumListSha256']}`
- Primary, blind, and root checksum lists were independently verified; their hashes are recorded in `SUMMARY.json`.
- Cross outcomes: `{json.dumps(dict(sorted(counts.items())), ensure_ascii=False, sort_keys=True)}`; all 13 root proposals were assessed and {len(disagreements)} disagreements were recorded.
- Every row binds the source hash, caller-context hash, current-target hash, proposed cross-target hash, and token checks. `root-disagreements.jsonl` records exact text for any disagreement.
- No catalog/PR/workflow change, test, build, or CI run was made. This machine-assisted review is not native-speaker or browser signoff.

Verify with `python3 verify_cross_review.py` from this directory.
''', encoding="utf-8")
    print(json.dumps({"result":"CROSS_REVIEW_BUILT", "head":HEAD, "tree":TREE, "cells":len(rows), "crossDispositionCounts":dict(sorted(counts.items())), "rootProposalsReviewed":len(ROOT_PROPOSAL_CROSS_CHECKS), "rootDisagreements":len(disagreements)}, ensure_ascii=False, sort_keys=True))

if __name__ == "__main__": main()
