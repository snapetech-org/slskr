from __future__ import annotations

import collections
import hashlib
import json
import subprocess
from pathlib import Path


EVIDENCE = Path(__file__).resolve().parents[1]
REPO = Path(__file__).resolve().parents[5]
PRIMARY = EVIDENCE / "primary"
CROSS = EVIDENCE / "crossreview"
HEAD = "72597bcf3c71f586040cd882506dff8dcbf6c804"
TREE = "98f7304db2e39ad722121c24047f5f06aa515663"
LOCALES = ["ar", "de", "es", "fr", "hi", "id", "ja", "ko", "pt-BR", "vi", "zh-Hans", "zh-Hant"]


def sha(data: bytes | str) -> str:
    return hashlib.sha256(data.encode("utf-8") if isinstance(data, str) else data).hexdigest()


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=REPO, text=True).strip()


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows), encoding="utf-8")


def verify_manifest(directory: Path, expected_sums_sha: str) -> int:
    sums = (directory / "SHA256SUMS").read_bytes()
    assert sha(sums) == expected_sums_sha
    count = 0
    for line in sums.decode("utf-8").splitlines():
        if not line.strip():
            continue
        digest, name = line.split("  ", 1)
        assert sha((directory / name).read_bytes()) == digest, (directory, name)
        count += 1
    return count


assert git("rev-parse", "HEAD") == HEAD
assert git("rev-parse", "HEAD^{tree}") == TREE
status = git("status", "--short").splitlines()
assert all(line.startswith("?? docs/pr-evidence/pr204-localization-2026-11-02/window-0863-0882/") for line in status), status

primary_file_count = verify_manifest(PRIMARY, "aaeee1a02507f830796ed72959adbc31177df9dfd7e2bf0d7236137962b46209")
cross_file_count = verify_manifest(CROSS, "a347cfd9b3ebbc0920051b0c655703f49e48ea322fe3d2d51bb8a02e2999af1f")
primary_summary = json.loads((PRIMARY / "summary.json").read_text(encoding="utf-8"))
cross_summary = json.loads((CROSS / "summary.json").read_text(encoding="utf-8"))
assert primary_summary["head"] == HEAD and primary_summary["tree"] == TREE
assert cross_summary["primaryHead"] == HEAD and cross_summary["primaryTree"] == TREE

live = json.loads((CROSS / "live-prs-before-apply.json").read_text(encoding="utf-8"))
assert len(live["pullRequests"]) == 7 and live["phase"] == "before-apply"
slskr_pr = next(row for row in live["pullRequests"] if row["number"] == 204)
assert slskr_pr["repository"].lower() == "snapetech-org/slskr"
assert slskr_pr["state"] == "OPEN" and slskr_pr["isDraft"] is True
assert slskr_pr["headRefOid"] == HEAD and slskr_pr["remoteBranchOid"] == HEAD and slskr_pr["tree"] == TREE

primary = read_jsonl(PRIMARY / "review-ledger.jsonl")
cross = read_jsonl(CROSS / "crossreview-ledger.jsonl")
assert len(primary) == len(cross) == 240
pmap = {(row["sourceIndex"], row["locale"]): row for row in primary}
assert len(pmap) == 240
dispositions = collections.Counter(row["crossReviewDisposition"] for row in cross)
assert dispositions == {"accept-current": 172, "accept-proposal": 56, "revise-proposal": 12}

pin_rows = read_jsonl(CROSS / "caller-pin-reattestation.jsonl")
assert len(pin_rows) == 27
for pin in pin_rows:
    blob = git("rev-parse", f"{HEAD}:{pin['path']}")
    raw = subprocess.check_output(["git", "show", f"{HEAD}:{pin['path']}"], cwd=REPO)
    assert blob == pin["fileBlob"] and sha(raw) == pin["fileSha256"]
    line = raw.decode("utf-8").splitlines()[pin["line"] - 1]
    assert line.strip() == pin["surfaceLine"] and sha(line) == pin["lineSha256"]
    assert pin["independentReattestation"] == "pass"

catalog_paths = {locale: REPO / f"web/src/lib/locales/ui-labels.{locale}.json" for locale in LOCALES}
catalogs: dict[str, dict] = {}
preapply = []
for locale, path in catalog_paths.items():
    raw = path.read_bytes()
    catalog = json.loads(raw)
    assert raw == (json.dumps(catalog, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    assert len(catalog) == 5441
    catalogs[locale] = catalog
    preapply.append({
        "locale": locale,
        "path": str(path.relative_to(REPO)),
        "keyCount": len(catalog),
        "fileSha256": sha(raw),
        "gitBlobOid": git("rev-parse", f"{HEAD}:{path.relative_to(REPO)}"),
        "orderedKeysSha256": sha("\n".join(catalog)),
        "keySetSha256": sha("\n".join(sorted(catalog))),
    })
assert len({row["keySetSha256"] for row in preapply}) == 1
write_jsonl(EVIDENCE / "apply" / "catalog-preapply-pins.jsonl", preapply)

plan = []
for row in cross:
    key = (row["sourceIndex"], row["locale"])
    primary_row = pmap[key]
    sid = row["sourceId"]
    assert primary_row["sourceId"] == sid
    assert primary_row["currentTarget"] == row["currentTarget"]
    assert primary_row["currentTargetSha256"] == row["currentTargetSha256"]
    assert primary_row["sourceSha256"] == row["sourceSha256"] == sha(sid)
    current = catalogs[row["locale"]][sid]
    assert current == row["currentTarget"] and sha(current) == row["currentTargetSha256"]
    final = row["reviewedFinal"]
    assert sha(final) == row["reviewedFinalSha256"]
    if row["crossReviewDisposition"] == "accept-current":
        assert final == current
    elif row["crossReviewDisposition"] == "accept-proposal":
        assert final == primary_row["proposedTarget"] == primary_row["reviewedFinal"]
    else:
        assert row["crossReviewDisposition"] == "revise-proposal"
        assert row["primaryProposal"] == primary_row["proposedTarget"]
    assert row["placeholderCheck"] == "pass" and row["markupCheck"] == "pass"
    for token in row.get("protectedLiteralCheck", {}).get("requiredTokens", []):
        assert token in final, (key, token)
    plan.append({
        "window": "W863-W882",
        "sourceIndex": row["sourceIndex"],
        "sourceId": sid,
        "sourceSha256": row["sourceSha256"],
        "locale": row["locale"],
        "path": str(catalog_paths[row["locale"]].relative_to(REPO)),
        "currentTarget": current,
        "currentTargetSha256": row["currentTargetSha256"],
        "primaryDisposition": row["primaryDisposition"],
        "primaryProposal": primary_row["proposedTarget"],
        "crossReviewDisposition": row["crossReviewDisposition"],
        "crossReviewReason": row["reason"],
        "finalTarget": final,
        "finalTargetSha256": row["reviewedFinalSha256"],
        "changed": final != current,
    })

changed = [row for row in plan if row["changed"]]
assert len(plan) == 240 and len(changed) == 67
write_jsonl(EVIDENCE / "apply" / "apply-plan.jsonl", plan)

for row in changed:
    catalogs[row["locale"]][row["sourceId"]] = row["finalTarget"]

for locale, path in catalog_paths.items():
    before_keys = [row for row in json.loads(path.read_text(encoding="utf-8"))]
    assert before_keys == list(catalogs[locale])
    path.write_text(json.dumps(catalogs[locale], ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

readback = []
for row in plan:
    actual = json.loads(catalog_paths[row["locale"]].read_text(encoding="utf-8"))[row["sourceId"]]
    assert actual == row["finalTarget"] and sha(actual) == row["finalTargetSha256"]
    readback.append({**row, "readbackTarget": actual, "readbackTargetSha256": sha(actual), "readbackMatches": True})
write_jsonl(EVIDENCE / "apply" / "apply-readback.jsonl", readback)

postapply = []
for locale, path in catalog_paths.items():
    raw = path.read_bytes()
    catalog = json.loads(raw)
    postapply.append({
        "locale": locale,
        "path": str(path.relative_to(REPO)),
        "keyCount": len(catalog),
        "fileSha256": sha(raw),
        "gitBlobOid": git("hash-object", str(path.relative_to(REPO))),
        "orderedKeysSha256": sha("\n".join(catalog)),
        "keySetSha256": sha("\n".join(sorted(catalog))),
    })
    assert len(catalog) == 5441 and list(catalog) == list(json.loads(path.read_text(encoding="utf-8")))
assert len({row["keySetSha256"] for row in postapply}) == 1
assert all(pre["orderedKeysSha256"] == post["orderedKeysSha256"] for pre, post in zip(preapply, postapply))

summary = {
    "result": "APPLIED_AND_READ_BACK",
    "repository": "snapetech-org/slskR",
    "pullRequest": 204,
    "inputHead": HEAD,
    "inputTree": TREE,
    "window": "W863-W882",
    "sourceIndexRangeInclusive": [862, 881],
    "sourceCount": 20,
    "cellsReviewed": len(plan),
    "locales": len(LOCALES),
    "catalogKeyCount": 5441,
    "catalogValuesChanged": len(changed),
    "perLocaleChangedCells": dict(sorted(collections.Counter(row["locale"] for row in changed).items())),
    "dispositions": dict(sorted(dispositions.items())),
    "primaryCandidates": 57,
    "primaryProposalsAccepted": 56,
    "primaryProposalsRevised": 1,
    "independentCurrentValueCorrections": 11,
    "revisedFinalCellsEqualToCurrent": sum(row["crossReviewDisposition"] == "revise-proposal" and not row["changed"] for row in plan),
    "holds": 0,
    "callerPinsReattested": len(pin_rows),
    "callerReferences": 27,
    "placeholderAndMarkupChecks": "all pass",
    "protectedLiteralMismatches": 0,
    "allTargetsReadBack": len(readback) == 240 and all(row["readbackMatches"] for row in readback),
    "catalogKeySetsPreserved": len({row["keySetSha256"] for row in postapply}) == 1,
    "perCatalogKeyOrderAndSerializationPreserved": all(pre["orderedKeysSha256"] == post["orderedKeysSha256"] for pre, post in zip(preapply, postapply)),
    "primaryPacketChecksummedFiles": primary_file_count,
    "crossReviewPacketChecksummedFiles": cross_file_count,
    "nativeSpeakerApproval": False,
    "headedBrowserReview": False,
    "testsBuildsScansCiRun": False,
    "workflowFilesTouched": False,
    "mergeReleaseOrTag": False,
}
write_json(EVIDENCE / "apply" / "apply-summary.json", summary)
write_json(EVIDENCE / "apply" / "catalog-postapply-attestation.json", {
    "repository": "snapetech-org/slskR",
    "pullRequest": 204,
    "inputHead": HEAD,
    "inputTree": TREE,
    "catalogs": postapply,
    "allCatalogsHave5441Keys": all(row["keyCount"] == 5441 for row in postapply),
    "catalogKeySetParity": len({row["keySetSha256"] for row in postapply}) == 1,
    "perCatalogOrderPreserved": all(pre["orderedKeysSha256"] == post["orderedKeysSha256"] for pre, post in zip(preapply, postapply)),
})
print(json.dumps(summary, ensure_ascii=False, indent=2))
