#!/usr/bin/env python3
"""Build the independently reconciled slskR W1283–W1302 cell ledger."""

import hashlib
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = Path(__file__).resolve().parent


def read_jsonl(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


cells = read_jsonl(ROOT / "candidate-free-input/current-target-cells.jsonl")
manifest = json.loads((ROOT / "candidate-free-input/manifest.json").read_text(encoding="utf-8"))
primary = read_jsonl(ROOT / "primary-review/ledger.jsonl")
blind = read_jsonl(ROOT / "blind-review/blind-ledger.jsonl")
queue = read_jsonl(ROOT / "candidate-free-input/source-queue.jsonl")
contexts = read_jsonl(ROOT / "candidate-free-input/source-contexts.jsonl")
cell_by_key = {(row["position"], row["locale"]): row for row in cells}
primary_by_key = {(row["position"], row["locale"]): row for row in primary}
blind_by_key = {(row["position"], row["locale"]): row for row in blind}
context_by_source = {row["sourceKey"]: row for row in contexts}

RATIONALE = {
    1283: "The FTP panel says these uploads happen after completed downloads. The selected wording makes the direction and timing clear and preserves the exact FTP literal.",
    1284: "The caller labels an FTP upload toggle. The selected wording means uploads over FTP and preserves FTP as the product/protocol literal.",
    1285: "The policy toggle limits HTTP request rates. The selected targets name request-rate limiting rather than vague speed limiting and preserve HTTP.",
    1286: "The tooltip scopes HTTP request-rate limiting to API, federation, and mesh-gateway policies. The selected wording carries that scope and keeps the protected API/HTTP literals.",
    1288: "The source-feed integration imports from Last.fm feeds. The selected targets remove redundant source-feed wording or clarify the feed source while preserving Last.fm.",
    1289: "These are Lidarr integration toggles. The selected Chinese values add the normal separator around the protected brand name.",
    1290: "The caller identifies an accessible setting for auto-downloading Lidarr-created Wishlist items. The selected values preserve that this is a setting and keep Lidarr literal.",
    1291: "The caller says this setting excludes a rejected Wishlist peer and remote directory from future automatic downloads. The selected labels retain blacklist semantics and do not suggest deleting files.",
    1292: "The caller sends completed slskR download directories to Lidarr manual import. The selected wording clearly names importing completed downloads into Lidarr and preserves the Lidarr literal.",
    1293: "The caller says to delete completed files that Lidarr rejects during automatic import, with eligibility limited to direct files. The selected wording names the rejection and import context accurately.",
    1294: "The caller is an integration-settings checkbox. The selected values make Lidarr’s integration settings the object being enabled and preserve Lidarr.",
    1295: "The caller permits Lidarr to replace existing files during completed-download import. The selected wording expresses that permission clearly and preserves Lidarr.",
    1296: "The caller syncs Lidarr Wanted albums into slskR Wishlist review items. The selected values describe that setting and use locale-appropriate wording for wanted or unacquired albums.",
    1297: "The caller explains the settings for wanted-album sync and completed-download import, and says live sync occurs only after explicit Lidarr actions or configured schedulers. The selected values retain both constraints.",
    1298: "The caller is a privacy setting for Message Batching. The selected values express processing or grouping messages in batches rather than an awkward literal fragment.",
    1299: "The caller is a privacy setting for Message Padding. The selected Arabic and Indonesian values make the padding operation clear while preserving the established technical term.",
    1300: "The caller labels the Ntfy integration toggle. The selected Chinese values add spacing around the protected Ntfy brand.",
    1302: "The caller toggles obfuscated transport mode. The selected values describe concealing or obfuscating transport rather than an ambiguous opaque transport.",
}


def choose(position, method, reason):
    for row in cells:
        if row["position"] != position:
            continue
        key = (position, row["locale"])
        p = primary_by_key[key]
        b = blind_by_key[key]
        current = row["currentTarget"]
        if method == "primary":
            target = p["proposedTarget"] if p["decision"] != "accept-current" else current
        elif method == "blind":
            target = b["target"] if b["disposition"] == "propose" else (p["proposedTarget"] if p["decision"] != "accept-current" else current)
        else:
            target = current
        selected[(position, row["locale"])] = (target, reason)


selected = {}
for pos, method in (
    (1283, "primary"), (1284, "primary"), (1285, "blind"), (1286, "blind"), (1287, "current"),
    (1288, "blind"), (1289, "primary"), (1290, "primary"), (1291, "primary"), (1292, "blind"),
    (1293, "blind"), (1294, "primary"), (1295, "blind"), (1296, "primary"), (1297, "primary"),
    (1298, "blind"), (1299, "blind"), (1300, "primary"), (1301, "current"), (1302, "blind"),
):
    if pos in (1287, 1301):
        reason = "Both reviewers retain the exact current value, which is clear and preserves the product name."
    else:
        reason = RATIONALE[pos]
    choose(pos, method, reason)

# Retain the already clear German sentence while the other locales clarify upload direction.
selected[(1283, "de")] = (cell_by_key[(1283, "de")]["currentTarget"], "The current German imperative already clearly enables FTP uploads after downloads finish; retain it unchanged.")
# French keeps its established translation of mesh gateway while adding the request-rate context.
selected[(1286, "fr")] = (
    "Activez la limitation du débit des requêtes HTTP pour les règles d’API, de fédération et de passerelle maillée.",
    RATIONALE[1286] + " The French target combines the blind review’s request-rate precision with the primary review’s natural translation of mesh gateway.",
)
# The Spanish translation says imports are from Last.fm feeds.
selected[(1288, "es")] = (primary_by_key[(1288, "es")]["proposedTarget"], RATIONALE[1288] + " The primary Spanish target explicitly says imports are from Last.fm feeds.")
# Prefer primary wording for this accessible setting label.
for row in cells:
    if row["position"] == 1290 and primary_by_key[(1290, row["locale"])]["decision"] != "accept-current":
        selected[(1290, row["locale"])] = (primary_by_key[(1290, row["locale"])]["proposedTarget"], RATIONALE[1290])
# Keep the setting explicit for wanted-album sync; use clearer blind terminology in these locales.
for locale in ("zh-Hans", "ja", "fr", "ar", "zh-Hant"):
    selected[(1296, locale)] = (blind_by_key[(1296, locale)]["target"], RATIONALE[1296])
# The blind wording better distinguishes wanted/unacquired albums in these long caller-bound descriptions.
for locale in ("es", "zh-Hans", "ja", "ar", "ko", "zh-Hant"):
    selected[(1297, locale)] = (blind_by_key[(1297, locale)]["target"], RATIONALE[1297])


def normalize_refs(refs):
    fields = ("path", "line", "lineSha256", "fileSha256", "gitBlob")
    return sorted(tuple(ref.get(field) for field in fields) for ref in refs)


records = []
for row in cells:
    key = (row["position"], row["locale"])
    p = primary_by_key[key]
    b = blind_by_key[key]
    target, why = selected[key]
    allowed = {row["currentTarget"], p["proposedTarget"], b["target"]}
    if key == (1286, "fr"):
        allowed.add("Activez la limitation du débit des requêtes HTTP pour les règles d’API, de fédération et de passerelle maillée.")
    assert target in allowed, (key, target)
    assert row["sourcePlaceholders"] == p["proposedPlaceholders"] == b["targetPlaceholders"]
    assert row["sourceMarkupTags"] == p["proposedMarkupTags"] == b["targetMarkupTags"]
    assert row["sourceNumericTokens"] == p["proposedNumericTokens"] == b["targetNumericTokens"]
    assert row["placeholderSequenceMatches"] and row["markupMatches"] and row["numericTokensMatch"]
    assert all(literal in target for literal in row["sourceProtectedLiterals"]), (key, row["sourceProtectedLiterals"], target)
    assert normalize_refs(p["callerRefs"]) == normalize_refs(row["callerRefs"])
    assert normalize_refs(b["callerReferences"]) == normalize_refs(row["callerRefs"])
    source_context = context_by_source[row["sourceKey"]]
    assert source_context["callerContextSha256"] == row["sourceContextSha256"]
    assert normalize_refs(source_context["callers"]) == normalize_refs(row["callerRefs"])

    changed = target != row["currentTarget"]
    if not changed:
        disposition = "accept-current"
        why = "The exact current value is retained; no catalog change is selected."
    elif p["decision"] in ("correction", "refinement"):
        disposition = p["decision"]
    else:
        disposition = "refinement" if row["position"] in (1285, 1286, 1288, 1295, 1298, 1299) else "correction"
    records.append({
        "schemaVersion": 1,
        "artifact": "slskR PR #204 W1283-W1302 root cross-audit",
        "window": "W1283-W1302 positions 1283-1302",
        "repository": "snapetech-org/slskR",
        "pullRequest": 204,
        "head": manifest["head"],
        "tree": manifest["tree"],
        "position": row["position"],
        "historicalSourceOrdinal": row["historicalSourceOrdinal"],
        "sourceKey": row["sourceKey"],
        "sourceKeySha256": row["sourceKeySha256"],
        "locale": row["locale"],
        "catalogPath": row["catalogPath"],
        "catalogFileSha256": row["catalogFileSha256"],
        "catalogGitBlob": row["catalogGitBlob"],
        "currentTarget": row["currentTarget"],
        "currentTargetSha256": row["currentTargetSha256"],
        "sourceContextSha256": row["sourceContextSha256"],
        "callerCount": row["callerCount"],
        "callerRefs": row["callerRefs"],
        "primaryDecision": p["decision"],
        "primaryTarget": p["proposedTarget"],
        "blindDisposition": b["disposition"],
        "blindTarget": b["target"],
        "selectedTarget": target,
        "selectedTargetSha256": hashlib.sha256(target.encode("utf-8")).hexdigest(),
        "disposition": disposition,
        "rationale": why,
        "structuralEvidence": {
            "placeholdersMatchSource": True,
            "markupMatchesSource": True,
            "numericTokensMatchSource": True,
            "sourceProtectedLiterals": row["sourceProtectedLiterals"],
            "protectedLiteralsPreserved": True,
        },
    })

assert len(records) == 240
ledger = OUT / "cross-audit-ledger.jsonl"
ledger.write_text("".join(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n" for record in records), encoding="utf-8")
counts = Counter(record["disposition"] for record in records)
changes = [record for record in records if record["selectedTarget"] != record["currentTarget"]]
summary = {
    "schemaVersion": 1,
    "artifact": "slskR PR #204 W1283-W1302 root cross-audit summary",
    "window": "W1283-W1302 positions 1283-1302",
    "repository": "snapetech-org/slskR",
    "pullRequest": 204,
    "head": records[0]["head"],
    "tree": records[0]["tree"],
    "candidateFreePacketChecksumListSha256": "abbb1b89549b82072fcbf5fce3c6ae580cc5bd499b4fe5dadd5df7bd0c567f89",
    "primaryPacketChecksumListSha256": "e824b4518481fa2a4b122f3d8c425be7cb22826aa7133ac0e5ec4f1edef9f339",
    "blindPacketChecksumListSha256": "83d0867a1c615665f2c12609dd2ca525013b438497f8c8309565d0ed6f6e1178",
    "reviewedCells": len(records),
    "dispositions": dict(sorted(counts.items())),
    "selectedUpdates": len(changes),
    "updatesByPosition": dict(sorted(Counter(str(record["position"]) for record in changes).items(), key=lambda item: int(item[0]))),
    "callerResolutionHolds": sum(record["disposition"] == "hold" for record in records),
    "changedCells": [{field: record[field] for field in ("position", "locale", "sourceKey", "currentTarget", "selectedTarget", "disposition")} for record in changes],
    "rootReviewPolicy": "All 240 cells were reviewed against exact candidate-free current values, caller context, primary review, and independent blind review. All caller references are pinned. Protected literals, placeholders, markup, and numeric tokens are preserved. No native-speaker approval is claimed.",
}
(OUT / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"dispositions": summary["dispositions"], "selectedUpdates": summary["selectedUpdates"], "updatesByPosition": summary["updatesByPosition"]}, ensure_ascii=False, indent=2))
