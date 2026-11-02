#!/usr/bin/env python3
"""Apply the independently cross-reviewed slskR W903-W922 catalog targets."""

from __future__ import annotations

import collections
import hashlib
import json
import re
import subprocess
from pathlib import Path


HEAD = "b1e814ef11d55fd1710d0e2522df14fee9ff0a70"
TREE = "50fef41fa1abcfcceb9a99cfd756ae014e51e286"
LOCALES = ["ar", "de", "es", "fr", "hi", "id", "ja", "ko", "pt-BR", "vi", "zh-Hans", "zh-Hant"]
CHANGED_DISPOSITIONS = {
    "accept-primary-correction",
    "accept-primary-refinement",
    "additional-correction",
}
PLACEHOLDER = re.compile(r"\{([A-Za-z][A-Za-z0-9_]*)\}")
MARKUP = re.compile(r"</?[A-Za-z][^>]*>")


EVIDENCE = Path(__file__).resolve().parents[1]
ROOT = Path(__file__).resolve().parents[5]
CATALOG_DIR = ROOT / "web/src/lib/locales"


def run(*args: str) -> str:
    return subprocess.check_output(args, cwd=ROOT, text=True).strip()


def sha_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def canonical(value: object) -> bytes:
    if isinstance(value, str):
        return value.encode("utf-8")
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def sha_target(value: object) -> str:
    return sha_bytes(canonical(value))


def leaves(value: object) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, dict):
        return [leaf for child in value.values() for leaf in leaves(child)]
    if isinstance(value, list):
        return [leaf for child in value for leaf in leaves(child)]
    return []


def preserve_object_order(expected: object, current: object) -> object:
    if isinstance(expected, dict) and isinstance(current, dict) and set(expected) == set(current):
        return {key: preserve_object_order(expected[key], current[key]) for key in current}
    if isinstance(expected, list) and isinstance(current, list) and len(expected) == len(current):
        return [preserve_object_order(new, old) for new, old in zip(expected, current)]
    return expected


def verify_checksums(folder: Path) -> None:
    sums = folder / "SHA256SUMS"
    for line in sums.read_text().splitlines():
        digest, relpath = line.split("  ", 1)
        relpath = relpath.removeprefix("./")
        path = folder / relpath
        actual = sha_bytes(path.read_bytes())
        if actual != digest:
            raise SystemExit(f"checksum mismatch: {path}")


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def write_jsonl(path: Path, rows: list[dict[str, object]]) -> None:
    path.write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows))


def main() -> None:
    if run("git", "rev-parse", "HEAD") != HEAD or run("git", "rev-parse", "HEAD^{tree}") != TREE:
        raise SystemExit("repository is not at the pinned pre-apply head/tree")

    primary = EVIDENCE / "primary"
    crossreview = EVIDENCE / "crossreview"
    application = EVIDENCE / "application"
    verify_checksums(primary)
    verify_checksums(crossreview)

    rows = [json.loads(line) for line in (crossreview / "cross-review-ledger.jsonl").read_text().splitlines()]
    if len(rows) != 240:
        raise SystemExit(f"expected 240 cross-review rows, got {len(rows)}")

    catalogs: dict[str, dict[str, object]] = {}
    key_orders: dict[str, list[str]] = {}
    catalog_paths: dict[str, Path] = {}
    for locale in LOCALES:
        path = CATALOG_DIR / f"ui-labels.{locale}.json"
        catalogs[locale] = json.loads(path.read_text())
        key_orders[locale] = list(catalogs[locale])
        catalog_paths[locale] = path
    first_order = key_orders[LOCALES[0]]
    if len(first_order) != 5441 or any(order != first_order for order in key_orders.values()):
        raise SystemExit("locale catalog key count/order mismatch before apply")

    planned: list[dict[str, object]] = []
    apply_plan: list[dict[str, object]] = []
    expected_pairs: set[tuple[str, str]] = set()
    for row in rows:
        if row["head"] != HEAD or row["tree"] != TREE:
            raise SystemExit(f"stale review pin: {row['sourceIndex']} / {row['locale']}")
        locale = str(row["locale"])
        source_id = str(row["sourceId"])
        if locale not in catalogs:
            raise SystemExit(f"unexpected locale {locale}")
        pair = (source_id, locale)
        if pair in expected_pairs:
            raise SystemExit(f"duplicate source/locale cell: {pair}")
        expected_pairs.add(pair)
        if sha_bytes(source_id.encode("utf-8")) != row["sourceSha256"]:
            raise SystemExit(f"source hash mismatch: {pair}")
        catalog = catalogs[locale]
        if source_id not in catalog:
            raise SystemExit(f"missing catalog key: {pair}")
        current = catalog[source_id]
        if current != row["currentTarget"] or sha_target(current) != row["currentTargetSha256"]:
            raise SystemExit(f"current target changed since cross-review: {pair}")
        final = preserve_object_order(row["crossReviewTarget"], current)
        if sha_target(final) != row["crossReviewTargetSha256"]:
            raise SystemExit(f"final target hash mismatch: {pair}")

        disposition = str(row["crossReviewDisposition"])
        change = disposition in CHANGED_DISPOSITIONS and final != current
        if disposition in CHANGED_DISPOSITIONS and not change:
            raise SystemExit(f"approved change is an exact no-op: {pair}")
        if disposition not in CHANGED_DISPOSITIONS and final != current:
            raise SystemExit(f"non-change disposition changes value: {pair} / {disposition}")

        source_placeholders = collections.Counter(PLACEHOLDER.findall(source_id))
        source_markup = collections.Counter(MARKUP.findall(source_id))
        for leaf in leaves(final):
            if collections.Counter(PLACEHOLDER.findall(leaf)) != source_placeholders:
                raise SystemExit(f"placeholder mismatch: {pair}")
            if collections.Counter(MARKUP.findall(leaf)) != source_markup:
                raise SystemExit(f"markup mismatch: {pair}")
            if row["sourceIndex"] == 908 and "URL" not in leaf:
                raise SystemExit(f"protected URL literal missing: {pair}")
        if row["sourceIndex"] == 915 and locale == "ar":
            if not isinstance(final, dict) or set(final) != {"zero", "one", "two", "few", "many", "other"}:
                raise SystemExit("Arabic plural categories changed")

        result = dict(row)
        result["plannedFinalTarget"] = final
        result["plannedFinalTargetSha256"] = sha_target(final)
        result["willChange"] = change
        apply_plan.append(result)
        if change:
            plan_row = {
                "window": "W903-W922",
                "head": HEAD,
                "tree": TREE,
                "sourceIndex": row["sourceIndex"],
                "sourceId": source_id,
                "locale": locale,
                "catalogPath": str(catalog_paths[locale].relative_to(ROOT)),
                "crossReviewDisposition": disposition,
                "currentTarget": current,
                "currentTargetSha256": sha_target(current),
                "finalTarget": final,
                "finalTargetSha256": sha_target(final),
                "rationale": row["crossReviewRationale"],
            }
            planned.append(plan_row)

    if len(expected_pairs) != 240 or len(planned) != 42:
        raise SystemExit(f"unexpected coverage/change count: {len(expected_pairs)} / {len(planned)}")

    write_jsonl(application / "exact-hash-apply-plan.jsonl", planned)
    write_jsonl(application / "full-window-apply-plan.jsonl", apply_plan)

    before_catalogs = {
        locale: {
            "path": str(catalog_paths[locale].relative_to(ROOT)),
            "keyCount": len(key_orders[locale]),
            "orderedKeySha256": sha_bytes("\n".join(key_orders[locale]).encode("utf-8")),
            "fileSha256": sha_bytes(catalog_paths[locale].read_bytes()),
        }
        for locale in LOCALES
    }
    preapply_pins = [
        {
            "sourceIndex": plan["sourceIndex"],
            "sourceId": plan["sourceId"],
            "locale": plan["locale"],
            "catalogPath": plan["catalogPath"],
            "beforeTarget": plan["currentTarget"],
            "beforeTargetSha256": plan["currentTargetSha256"],
            "afterTarget": plan["finalTarget"],
            "afterTargetSha256": plan["finalTargetSha256"],
        }
        for plan in planned
    ]
    write_jsonl(application / "catalog-preapply-pins.jsonl", preapply_pins)

    for plan in planned:
        locale = str(plan["locale"])
        source_id = str(plan["sourceId"])
        catalogs[locale][source_id] = plan["finalTarget"]

    for locale in LOCALES:
        catalog_paths[locale].write_text(json.dumps(catalogs[locale], ensure_ascii=False, indent=2) + "\n")

    readback: list[dict[str, object]] = []
    for row in apply_plan:
        locale = str(row["locale"])
        source_id = str(row["sourceId"])
        actual = json.loads(catalog_paths[locale].read_text())[source_id]
        expected = row["plannedFinalTarget"]
        if actual != expected or sha_target(actual) != row["plannedFinalTargetSha256"]:
            raise SystemExit(f"post-apply readback mismatch: {source_id!r} / {locale}")
        readback.append({
            "sourceIndex": row["sourceIndex"],
            "sourceId": source_id,
            "locale": locale,
            "disposition": row["crossReviewDisposition"],
            "willChange": row["willChange"],
            "actualTarget": actual,
            "actualTargetSha256": sha_target(actual),
            "matchesExpected": True,
        })
    write_jsonl(application / "full-window-readback.jsonl", readback)

    post_catalogs = {}
    for locale in LOCALES:
        reread = json.loads(catalog_paths[locale].read_text())
        after_order = list(reread)
        if after_order != key_orders[locale]:
            raise SystemExit(f"catalog keys/order changed: {locale}")
        post_catalogs[locale] = {
            "path": str(catalog_paths[locale].relative_to(ROOT)),
            "keyCount": len(after_order),
            "orderedKeySha256": sha_bytes("\n".join(after_order).encode("utf-8")),
            "fileSha256": sha_bytes(catalog_paths[locale].read_bytes()),
        }
    changed_paths = sorted(p for p in run("git", "diff", "--name-only", HEAD).splitlines() if p)
    expected_paths = sorted({str(plan["catalogPath"]) for plan in planned})
    if changed_paths != expected_paths:
        raise SystemExit(f"unexpected changed paths: {changed_paths!r} != {expected_paths!r}")

    write_json(application / "catalog-postapply-attestation.json", {
        "inputHead": HEAD,
        "inputTree": TREE,
        "localeCount": len(LOCALES),
        "catalogKeyCount": 5441,
        "before": before_catalogs,
        "after": post_catalogs,
        "changedPaths": changed_paths,
        "changedCellCount": len(planned),
        "keySetsAndOrderPreserved": True,
        "reviewCellsReadBack": len(readback),
        "allReadbacksMatch": True,
    })
    write_json(application / "apply-summary.json", {
        "repository": "snapetech-org/slskR",
        "pullRequest": 204,
        "window": "W903-W922",
        "inputHead": HEAD,
        "inputTree": TREE,
        "reviewedCells": len(rows),
        "changedCells": len(planned),
        "changedLocaleCatalogs": len(expected_paths),
        "retainedCatalogOnlyHolds": 12,
        "noOpRevisedProposal": 1,
        "fullWindowReadbacks": len(readback),
        "placeholderMarkupProtectedLiteralChecks": "passed for all 240 final targets",
        "catalogKeySetsAndOrder": "identical before and after",
        "nativeSpeakerApproval": False,
        "testsBuildScansCIOrBrowserRun": False,
    })
    print(json.dumps({"changedCells": len(planned), "changedPaths": changed_paths, "readbackCells": len(readback)}, indent=2))


if __name__ == "__main__":
    main()
