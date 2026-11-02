#!/usr/bin/env python3
"""Verify original translation target hashes against later exact corrections."""
import argparse
import collections
import hashlib
import json
import subprocess
from pathlib import Path

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--repo", type=Path, required=True)
parser.add_argument("--head", default="ad7c283dfe84f31b52f5a27c363a605fe068e36c")
parser.add_argument("--write-evidence", action="store_true", help="write deterministic reconciliation JSONL and summary")
args = parser.parse_args()
repo = args.repo.resolve()
head = args.head
expected_tree = "d0a2faeba016b57850767fe0903b67621d61bc6c"
locales = ["ar", "de", "es", "fr", "hi", "id", "ja", "ko", "pt-BR", "vi", "zh-Hans", "zh-Hant"]
source_manifest_path = Path("docs/localization/pr204-pending-translation-cells-9c6dcb22.jsonl")
review_ledger_path = Path("docs/localization/pr204-translation-review-2026-11-01.jsonl")
bundle = Path("docs/localization/pr204-translation-target-reconciliation-2026-11-02")
changed_path = bundle / "changed-target-supersessions.jsonl"
summary_path = bundle / "reconciliation-summary.json"


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def value_sha(value):
    raw = value.encode("utf-8") if isinstance(value, str) else json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return sha(raw)


def git(*argv):
    return subprocess.check_output(["git", *argv], cwd=repo, text=True).strip()


def read_jsonl(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


if git("rev-parse", f"{head}^{{tree}}") != expected_tree:
    raise SystemExit("catalog commit/tree pin mismatch")
source_manifest = repo / source_manifest_path
review_ledger = repo / review_ledger_path
if sha(source_manifest.read_bytes()) != "027ba04ae68b21057b305650cc3523108686114fd16964f88ef31b12e89be835":
    raise SystemExit("source manifest hash mismatch")
if sha(review_ledger.read_bytes()) != "27ab430e61b7cb5628150121afc1b565e38af9cd2dc2608d3aebd65fce99220e":
    raise SystemExit("historical translation review ledger hash mismatch")

manifest_rows = read_jsonl(source_manifest)
target_sources = [row for row in manifest_rows if row.get("recordType") == "targetSource"]
target_cells = {(row["sourceId"], locale): row for row in target_sources for locale in row["targetLocales"]}
if len(target_sources) != 549 or len(target_cells) != 6588:
    raise SystemExit("source-linked target inventory count mismatch")
translation_rows = [row for row in read_jsonl(review_ledger) if row.get("recordType") == "reviewedTranslationCell"]
if len(translation_rows) != 6552 or len({(row["sourceId"], row["locale"]) for row in translation_rows}) != 6552:
    raise SystemExit("historical translation ledger cell count/uniqueness mismatch")
if not {(row["sourceId"], row["locale"]) for row in translation_rows} <= set(target_cells):
    raise SystemExit("translation ledger contains a cell outside the pinned source manifest")

catalogs = {}
catalog_hashes = {}
for locale in locales:
    path = f"web/src/lib/locales/ui-labels.{locale}.json"
    raw = subprocess.check_output(["git", "show", f"{head}:{path}"], cwd=repo)
    catalog_hashes[path] = sha(raw)
    catalogs[locale] = json.loads(raw.decode("utf-8"))

apply_files = sorted((repo / "docs/pr-evidence/pr204-semantic-review-2026-11-01").rglob("applied-corrections.jsonl"))
evidence_by_cell = collections.defaultdict(list)
for path in apply_files:
    rel = path.relative_to(repo).as_posix()
    for line_no, raw in enumerate(path.read_bytes().splitlines(), 1):
        if not raw.strip():
            continue
        try:
            record = json.loads(raw)
        except json.JSONDecodeError:
            continue
        sid = record.get("source_id", record.get("sourceId"))
        locale = record.get("locale")
        if not isinstance(sid, str) or locale not in locales:
            continue
        evidence_by_cell[(sid, locale)].append((rel, line_no, record, sha(raw)))

changed = []
matched_original_hashes = 0
enum_cells = 0
for (sid, locale), source_record in target_cells.items():
    target = catalogs[locale].get(sid)
    if not isinstance(target, str) or not target.strip():
        raise SystemExit(f"missing/blank current target: {locale}:{sid}")
    if target.strip() == sid.strip():
        raise SystemExit(f"current target is source-identical: {locale}:{sid}")
    current_hash = value_sha(target)
    if source_record["sourceSha256"] != value_sha(sid):
        raise SystemExit(f"source id hash mismatch: {locale}:{sid}")
    if source_record["category"] == "new-source-id-required-by-enum-label":
        enum_cells += 1

for row in translation_rows:
    sid = row["sourceId"]
    locale = row["locale"]
    if row["sourceSha256"] != value_sha(sid):
        raise SystemExit(f"historical source hash mismatch: {locale}:{sid}")
    current = catalogs[locale][sid]
    current_hash = value_sha(current)
    if row["targetSha256"] == current_hash:
        matched_original_hashes += 1
        continue
    exact_matches = []
    for rel, line_no, record, line_sha in evidence_by_cell[(sid, locale)]:
        old_hash = record.get("baseline_target_sha256", record.get("old_target_sha256", record.get("previous_target_sha256", record.get("current_target_sha256"))))
        final_hash = record.get("applied_target_sha256", record.get("final_target_sha256", record.get("target_sha256")))
        source_hash = record.get("source_sha256", record.get("sourceSha256"))
        if old_hash == row["targetSha256"] and final_hash == current_hash and source_hash == row["sourceSha256"]:
            exact_matches.append({
                "root": "pr-review-head",
                "path": rel,
                "line": line_no,
                "line_sha256": line_sha,
                "review_head": record.get("review_head"),
                "application_head": record.get("application_head"),
                "window": record.get("window"),
            })
    if len(exact_matches) != 1:
        raise SystemExit(f"expected one exact applied-correction record for {locale}:{sid}, found {len(exact_matches)}")
    changed.append({
        "recordType": "translation-target-supersession",
        "sourceIndex": row["sourceIndex"],
        "sourceId": sid,
        "locale": locale,
        "sourceSha256": row["sourceSha256"],
        "historicalTranslationTargetSha256": row["targetSha256"],
        "currentTargetSha256": current_hash,
        "currentTarget": current,
        "semanticCorrectionEvidence": exact_matches[0],
        "nativeSpeakerApproval": False,
    })

if enum_cells != 36 or matched_original_hashes != 6524 or len(changed) != 28:
    raise SystemExit(f"unexpected reconciliation counts: enum={enum_cells}, unchanged={matched_original_hashes}, superseded={len(changed)}")
changed.sort(key=lambda row: (row["sourceIndex"], row["locale"]))
summary = {
    "catalogHead": head,
    "catalogTree": expected_tree,
    "sourceSetPath": source_manifest_path.as_posix(),
    "sourceSetSha256": sha(source_manifest.read_bytes()),
    "historicalTranslationReviewLedgerPath": review_ledger_path.as_posix(),
    "historicalTranslationReviewLedgerSha256": sha(review_ledger.read_bytes()),
    "sourceIdCount": len(target_sources),
    "translationTargetCellCount": len(target_cells),
    "historicalTranslationReviewCells": len(translation_rows),
    "historicalTargetHashesStillCurrent": matched_original_hashes,
    "historicalTargetHashesSupersededByExactSemanticCorrections": len(changed),
    "enumDisplayCellsOutsideTranslationReviewLedger": enum_cells,
    "currentTargetsMissingOrBlank": 0,
    "currentTargetsSourceIdentical": 0,
    "unmatchedSupersededTargets": 0,
    "catalogFileSha256": catalog_hashes,
    "supersessionLedgerSha256": sha((json.dumps(changed, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")),
    "nativeSpeakerApproval": False,
    "allPass": True,
}
changed_bytes = "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in changed).encode("utf-8")
summary["supersessionLedgerSha256"] = sha(changed_bytes)
if args.write_evidence:
    changed_path.write_bytes(changed_bytes)
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
else:
    if not changed_path.is_file() or changed_path.read_bytes() != changed_bytes:
        raise SystemExit("saved supersession ledger differs from recomputed exact rows; rerun with --write-evidence")
    saved_summary = json.loads(summary_path.read_text(encoding="utf-8"))
    if saved_summary != summary:
        raise SystemExit("saved reconciliation summary differs from recomputed values")
print(json.dumps(summary, ensure_ascii=False, indent=2))
