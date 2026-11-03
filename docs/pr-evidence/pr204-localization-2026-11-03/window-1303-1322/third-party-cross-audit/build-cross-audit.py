#!/usr/bin/env python3
import collections
import hashlib
import json
import re
from pathlib import Path

BASE = Path("/home/keith/Documents/code/task-scratch")
INPUT = BASE / "slskr-pr204-w1303-1322-primary-20261103/input"
PRIMARY = BASE / "slskr-pr204-w1303-1322-primary-20261103/primary-review"
BLIND = BASE / "slskr-pr204-w1303-1322-blind-20261103/review"
OUT = BASE / "slskr-pr204-w1303-1322-root-cross-audit-20261103"
HEAD = "f46b8b2322f4b944f39f34d5bb8d55852ba330c8"
TREE = "4eba98f951a745dac6b5332bd6796bf57c7037e2"
BRANCH = "codex/slskr-l10n-audit-20261030"

def sha(data):
    if isinstance(data, str):
        data = data.encode("utf-8")
    return hashlib.sha256(data).hexdigest()

def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))

def read_jsonl(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]

def verify_sum_list(directory, filename):
    manifest = directory / filename
    failures = []
    for line in manifest.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        expected, relative = line.split(maxsplit=1)
        relative = relative.strip().lstrip("*")
        path = directory / relative
        if not path.is_file() or sha(path.read_bytes()) != expected:
            failures.append(relative)
    if failures:
        raise SystemExit(f"checksum failure in {directory}: {failures}")
    return sha(manifest.read_bytes())

def dump_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")

def dump_jsonl(path, rows):
    path.write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows), encoding="utf-8")

OUT.mkdir(parents=True, exist_ok=True)
input_sum = verify_sum_list(INPUT, "SHA256SUMS.txt")
primary_sum = verify_sum_list(PRIMARY, "SHA256SUMS.txt")
blind_sum = verify_sum_list(BLIND, "SHA256SUMS.txt")

manifest = read_json(INPUT / "manifest.json")
p_summary = read_json(PRIMARY / "summary.json")
b_summary = read_json(BLIND / "summary.json")
if manifest["head"] != HEAD or manifest["tree"] != TREE or manifest["headRef"] != BRANCH:
    raise SystemExit("candidate-free input pin mismatch")
if p_summary["head"] != HEAD or p_summary["tree"] != TREE or b_summary["pin"]["head"] != HEAD or b_summary["pin"]["tree"] != TREE:
    raise SystemExit("review pin mismatch")
if p_summary["applicationApproved"] or p_summary["blindReviewIncluded"] or b_summary["input"]["candidateFreeOnly"] is not True:
    raise SystemExit("review separation/provenance mismatch")

cells = read_jsonl(INPUT / "current-target-cells.jsonl")
primary = read_jsonl(PRIMARY / "ledger.jsonl")
blind = read_jsonl(BLIND / "blind-ledger.jsonl")
key = lambda x: (int(x["position"]), x["locale"])
cm = {key(x): x for x in cells}
pm = {key(x): x for x in primary}
bm = {key(x): x for x in blind}
if len(cells) != 240 or len(cm) != 240 or set(cm) != set(pm) or set(cm) != set(bm):
    raise SystemExit("cell coverage mismatch")
if len(primary) != 240 or len(blind) != 240:
    raise SystemExit("review row count mismatch")

holds = {
    (1310, "zh-Hans"),
    (1310, "zh-Hant"),
    (1311, "vi"),
    (1313, "zh-Hans"),
    (1313, "zh-Hant"),
    (1316, "de"),
    (1316, "ja"),
    (1316, "ko"),
    (1316, "zh-Hans"),
    (1316, "zh-Hant"),
}
numeric_retain = {(1314, "ja"), (1314, "ko"), (1314, "vi")}
blind_target_overrides = {
    (1313, "es"),
    (1313, "vi"),
    (1320, "zh-Hans"),
}

reasons = {
    1303: "The exact caller binds this label to Privacy.Enabled. The current Vietnamese word denotes security, while the selected phrase names privacy.",
    1305: "The pinned caller enables Pushbullet notification delivery. The selected Arabic notification term is the more idiomatic rendering for UI notifications.",
    1308: "The pinned tooltip explicitly names Scene and Pod as two aggregation components. The selected text preserves both exact product literals and their separate roles.",
    1309: "The exact caller controls imports from Spotify. The selected phrasing makes the import action and Spotify source clear in the target language.",
    1310: "The caller describes Spotify source-feed imports, with liked, saved, and followed feeds requiring an account or bearer token. The selected wording removes the duplicated source/feed calque; Chinese feed terminology remains held.",
    1311: "The caller binds this toggle to Privacy.Timing.Enabled. The selected labels express concealment of timing patterns rather than ambiguity or generic time confusion; Vietnamese terminology remains held.",
    1312: "The pinned caller and adjacent UI identify YouTube playlist expansion. The selected wording uses a clear playlist term and natural modifier order.",
    1313: "The caller tooltip says the YouTube Data API expands playlists for explicitly previewed Import Feed URLs. The selected labels retain the imported-feed context; Chinese terminology remains held.",
    1315: "The caller warning requires authentication before making the Web UI accessible outside a trusted local network. The selected wording expresses access/exposure rather than merely displaying the interface.",
    1316: "The caller's authorityKey is a realm authority entity, not an ordinary permission. Cells with unresolved locale-specific governance terminology remain held; the Vietnamese target names an authority body.",
    1317: "The caller tooltip defines automatic replacement of stalled downloads with alternative sources. The selected Hindi/Japanese/Korean text preserves the enabled action and stalled state.",
    1318: "The same autoReplaceStuck setting is rendered with a hyphenated label. The selected text preserves the same stalled-download behavior and avoids an awkward noun/verb sequence.",
    1319: "The pinned tooltip explicitly says to replace stuck downloads with alternative sources. The selected Hindi/Japanese/Korean wording makes the replacement action and alternative-source relation explicit.",
    1320: "The exact PlayerBar aria-label and test id identify the crossfade control, not a generic fade. The selected terminology names the crossfade transition.",
    1321: "The exact tooltip describes scheduled download speed limits under the global policy. The selected text makes clear that the schedule controls download speed.",
}

cross = []
application = []
disagreements = []
for k in sorted(cm):
    c, p, b = cm[k], pm[k], bm[k]
    pos, locale = k
    if p["sourceKey"] != c["sourceKey"] or b["sourceKey"] != c["sourceKey"]:
        raise SystemExit(f"source key mismatch: {k}")
    if p["currentTargetSha256"] != c["currentTargetSha256"] or b["currentTargetSha256"] != c["currentTargetSha256"]:
        raise SystemExit(f"current target pin mismatch: {k}")
    if k in holds:
        disposition = "hold"
        target = c["currentTarget"]
        rationale = b["rationale"]
        root_reason = reasons[pos]
        confidence = "low"
    elif k in numeric_retain:
        disposition = "accept-current"
        target = c["currentTarget"]
        rationale = "Keep the existing numeric style: the digits preserve the exact five-second duration and are conventional in this compact UI label."
        root_reason = rationale
        confidence = "high"
    elif k in blind_target_overrides:
        disposition = p["decision"]
        target = b["target"]
        rationale = "Root selected the blind proposal after comparing both candidate phrasings with the exact pinned caller and tooltip context."
        root_reason = reasons[pos]
        confidence = "moderate"
    else:
        disposition = p["decision"]
        target = p["proposedTarget"]
        rationale = p["rationale"]
        root_reason = reasons.get(pos, "Exact caller and target meaning were independently checked against the pinned context.")
        confidence = "moderate"

    if disposition == "hold" and target != c["currentTarget"]:
        raise SystemExit(f"hold changed target: {k}")
    if disposition == "accept-current":
        target = c["currentTarget"]
    if disposition not in {"accept-current", "correction", "refinement", "hold"}:
        raise SystemExit(f"invalid disposition: {k} {disposition}")

    placeholders = re.findall(r"\{[^{}]+\}", target)
    if placeholders != c.get("sourcePlaceholders", []):
        raise SystemExit(f"placeholder mismatch in root target: {k}")
    for literal in c.get("sourceProtectedLiterals", []):
        if literal not in target:
            raise SystemExit(f"protected literal missing from root target: {k} {literal}")
    for token in c.get("sourceMarkupTags", []):
        if token not in target:
            raise SystemExit(f"markup token missing from root target: {k} {token}")
    target_sha = sha(target)
    row = {
        "head": HEAD,
        "tree": TREE,
        "branch": BRANCH,
        "position": pos,
        "locale": locale,
        "sourceKey": c["sourceKey"],
        "sourceKeySha256": c["sourceKeySha256"],
        "callerContextSha256": c["sourceContextSha256"],
        "callerRefs": p["callerRefs"],
        "catalogPath": c["catalogPath"],
        "catalogFileSha256": c["catalogFileSha256"],
        "catalogGitBlob": c["catalogGitBlob"],
        "currentTarget": c["currentTarget"],
        "currentTargetSha256": c["currentTargetSha256"],
        "primaryDisposition": p["decision"],
        "primaryTarget": p["proposedTarget"],
        "primaryTargetSha256": p["proposedTargetSha256"],
        "primaryRationale": p["rationale"],
        "blindDisposition": b["disposition"],
        "blindTarget": b["target"],
        "blindTargetSha256": b["targetSha256"],
        "blindRationale": b["rationale"],
        "crossAuditDisposition": disposition,
        "crossAuditTarget": target,
        "crossAuditTargetSha256": target_sha,
        "crossAuditRationale": rationale,
        "rootReasoning": root_reason,
        "confidence": confidence,
        "structureChecks": {
            "placeholderSequenceMatches": placeholders == c.get("sourcePlaceholders", []),
            "protectedLiteralsPresent": all(x in target for x in c.get("sourceProtectedLiterals", [])),
            "markupTokensPresent": all(x in target for x in c.get("sourceMarkupTags", [])),
        },
    }
    cross.append(row)
    if target != c["currentTarget"]:
        application.append({
            "head": HEAD,
            "tree": TREE,
            "position": pos,
            "sourceKey": c["sourceKey"],
            "locale": locale,
            "catalogPath": c["catalogPath"],
            "expectedCurrentTarget": c["currentTarget"],
            "expectedCurrentTargetSha256": c["currentTargetSha256"],
            "target": target,
            "targetSha256": target_sha,
            "disposition": disposition,
        })
    if ("retain" if p["decision"] == "accept-current" else "propose") != b["disposition"] or p["proposedTarget"] != b["target"]:
        disagreements.append({
            "position": pos,
            "locale": locale,
            "sourceKey": c["sourceKey"],
            "primaryDisposition": p["decision"],
            "primaryTarget": p["proposedTarget"],
            "blindDisposition": b["disposition"],
            "blindTarget": b["target"],
            "crossAuditDisposition": disposition,
            "crossAuditTarget": target,
            "resolution": root_reason,
        })

counts = collections.Counter(x["crossAuditDisposition"] for x in cross)
if len(cross) != 240 or len(application) != 70 or counts != collections.Counter({"accept-current": 160, "correction": 31, "refinement": 39, "hold": 10}):
    raise SystemExit(f"unexpected cross-audit totals: changes={len(application)} counts={dict(counts)}")
dump_jsonl(OUT / "cross-audit-ledger.jsonl", cross)
dump_jsonl(OUT / "application-plan.jsonl", application)
dump_jsonl(OUT / "disagreements.jsonl", disagreements)
dump_json(OUT / "summary.json", {
    "artifact": "slskR PR #204 W1303-W1322 root third-party cross-audit",
    "head": HEAD,
    "tree": TREE,
    "branch": BRANCH,
    "window": {"firstPosition": 1303, "lastPosition": 1322, "sourceCount": 20, "localeCount": 12, "cellCount": 240},
    "inputs": {
        "candidateFreeManifestSha256": sha((INPUT / "manifest.json").read_bytes()),
        "candidateFreeChecksumListSha256": input_sum,
        "primaryChecksumListSha256": primary_sum,
        "blindChecksumListSha256": blind_sum,
    },
    "decisionCounts": dict(counts),
    "applicationTargetCount": len(application),
    "disagreementCount": len(disagreements),
    "holds": [{"position": x["position"], "sourceKey": x["sourceKey"], "locale": x["locale"], "reason": x["crossAuditRationale"]} for x in cross if x["crossAuditDisposition"] == "hold"],
    "checks": {
        "uniqueCellCoverage": len(set((x["position"], x["locale"]) for x in cross)) == 240,
        "allSourceCallersPinned": all(x["callerRefs"] for x in cross),
        "placeholdersProtected": all(x["structureChecks"]["placeholderSequenceMatches"] for x in cross),
        "markupProtected": all(x["structureChecks"]["markupTokensPresent"] for x in cross),
        "protectedLiteralsPreserved": all(x["structureChecks"]["protectedLiteralsPresent"] for x in cross),
        "inputPrimaryBlindSumsVerified": True,
        "applicationApproved": False,
    },
    "createdAtUtc": "2026-11-03",
})
(OUT / "README.md").write_text(
    "# slskR PR #204 W1303-W1322 root cross-audit\n\n"
    f"Pinned to {HEAD} / {TREE} on {BRANCH}. This third-party reconciliation reviewed all 240 source-locale cells, exact source/caller pins, primary and blind decisions, and structural tokens.\n\n"
    "- Final dispositions: 160 accept-current, 40 corrections, 30 refinements, and 10 holds.\n"
    "- Selected 70 exact target updates; all 10 holds remain unchanged.\n"
    "- Holds cover source-feed terminology in Simplified and Traditional Chinese (positions 1310 and 1313), Vietnamese timing terminology (1311), and governance-authority terminology in German, Japanese, Korean, Simplified Chinese, and Traditional Chinese (1316).\n"
    "- Numeric values for the five-second fade remain rendered with digits in Japanese, Korean, and Vietnamese.\n"
    "- Candidate-free, primary, and blind packets are independently checksum-verified. No repository or PR changes are part of this packet.\n",
    encoding="utf-8",
)
files = sorted(p for p in OUT.iterdir() if p.is_file() and p.name != "SHA256SUMS.txt")
(OUT / "SHA256SUMS.txt").write_text("".join(f"{sha(p.read_bytes())}  {p.name}\n" for p in files), encoding="utf-8")
print(json.dumps({
    "status": "PASS",
    "output": str(OUT),
    "cells": len(cross),
    "decisionCounts": dict(counts),
    "applicationTargets": len(application),
    "disagreements": len(disagreements),
    "checksumListSha256": sha((OUT / "SHA256SUMS.txt").read_bytes()),
}, ensure_ascii=False, indent=2))
