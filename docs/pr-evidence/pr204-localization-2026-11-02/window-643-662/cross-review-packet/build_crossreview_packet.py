#!/usr/bin/env python3
import collections
import hashlib
import json
import re
import subprocess
from pathlib import Path

REPO = Path("/mnt/disks/scratch/task-worktrees/localization-20261030/slskr/manual-review")
INPUT = Path("/mnt/disks/scratch/task-scratch/slskr-pr204-W643-662-primary-20261102/packet")
OUT = Path("/mnt/disks/scratch/task-scratch/slskr-pr204-W643-662-crossreview-20261102")
EXPECTED_HEAD = "86ad391ca248ec50fa4049de0a0f08ee55010441"
EXPECTED_PARENT = "aa106d2505de8c9ace2d7d6dbf2af9777651947d"
EXPECTED_TREE = None
LOCALES = ["ar", "de", "es", "fr", "hi", "id", "ja", "ko", "pt-BR", "vi", "zh-Hans", "zh-Hant"]
PLACEHOLDER_RE = re.compile(r"\{[^{}]+\}")
MARKUP_RE = re.compile(r"</?[A-Za-z][^<>]*>")
MISS = {
    (644, "ar"): {
        "target": "خريطة حرارية لتقدم القطع",
        "rationale": "The current phrase says the heatmap shows progress of a singular piece. The caller is a swarm visualization header for chunk progress; plural القطع better describes the chunks represented by the heatmap."
    },
    (646, "ar"): {
        "target": "معدل استخدام القطع",
        "rationale": "The current استغلال القطعة reads as exploitation/use of one piece and is weak as a utilization metric label. معدل استخدام القطع states the usage rate for the chunk metric."
    },
}
SOURCE_BASIS = {
    643: "Chromaprint is a protected tool name; the caller uses this as the sample-rate field label and accessible name.",
    644: "The caller is a swarm visualization header for a heatmap of chunk progress.",
    645: "The caller is a statistic label for the success rate of swarm data chunks.",
    646: "The caller uses this as both the visible label and accessible name of the chunk-utilization metric.",
    647: "The caller uses this as a swarm table column and statistic label for chunks.",
    648: "The caller uses this as a statistic label and table heading alongside numeric completed-chunk values.",
    649: "The caller uses this as a table heading alongside numeric failed-chunk values.",
    650: "The caller uses this as a numeric statistic label for the rate of chunks served per second.",
    651: "The caller is the numeric incoming-search circuit-breaker setting in Admin Policies.",
    652: "This exact locale cell was accepted in the earlier Circuit-building review; it is preserved without reopening.",
    653: "The caller is the classic-dark visual-theme option in the appearance selector.",
    654: "The caller prints the value of conflictAnalysis.cleanEntries, so Clean labels entries without conflicts.",
    655: "The caller interpolates the integer result from cleanupMessages into a success toast for cleaned old messages.",
    656: "The UI labels the action Cleanup Expired and asks about expired membership records, but the backend clears all pending join/leave records without checking expiration; the source/action mismatch remains a hold.",
    657: "The caller is the button that cleans old messages using a 30-day cutoff.",
    658: "The caller is the action that removes old seen-message routing records.",
    659: "The caller displays cleanup counters for seen-message tracking records, not message bodies.",
    660: "The caller displays record-cleanup and error counts for the membership cleanup route.",
    661: "The caller is a warning that distinguishes mutating local Pod message-storage maintenance actions from read-only search and count actions; VACUUM is the SQLite maintenance command.",
    662: "The caller appends selectedCount and a closing parenthesis after this label; the click handler clears selected paths."
}

def cmd(*args, input_bytes=None):
    return subprocess.check_output(list(args), cwd=REPO, input=input_bytes)

def git(*args, input_bytes=None):
    return cmd("git", "-C", str(REPO), *args, input_bytes=input_bytes)

def read_jsonl(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]

def sha_bytes(b):
    return hashlib.sha256(b).hexdigest()

def sha_text(s):
    return sha_bytes(s.encode("utf-8"))

def write_json(path, obj):
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")

def write_jsonl(path, rows):
    with path.open("w", encoding="utf-8", newline="\n") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n")

def show(commit, path):
    return git("show", f"{commit}:{path}")

def git_blob(commit, path):
    return git("rev-parse", f"{commit}:{path}").decode().strip()

def json_catalog(commit, locale):
    path = f"web/src/lib/locales/ui-labels.{locale}.json"
    raw = show(commit, path)
    return path, raw, json.loads(raw.decode("utf-8")), git_blob(commit, path)

def pr_snapshot():
    raw = subprocess.check_output([
        "gh", "pr", "view", "204", "--repo", "snapetech-org/SlskR",
        "--json", "state,isDraft,headRefOid,headRefName,baseRefOid,url,mergeStateStatus"
    ], cwd=REPO)
    return json.loads(raw.decode("utf-8"))

def excerpt_pin(commit, path, first, last):
    raw = show(commit, path)
    lines = raw.decode("utf-8").splitlines()
    assert 1 <= first <= last <= len(lines), (path, first, last, len(lines))
    selected = lines[first - 1:last]
    text = "\n".join(selected)
    return {
        "path": path, "firstLine": first, "lastLine": last, "lines": selected,
        "excerptSha256": sha_text(text), "fileBlob": git_blob(commit, path),
        "fileSha256": sha_bytes(raw),
    }

initial_pr = pr_snapshot()
assert initial_pr["state"] == "OPEN" and initial_pr["isDraft"] is True, initial_pr
assert initial_pr["headRefOid"] == EXPECTED_HEAD, initial_pr
head = EXPECTED_HEAD
tree = git("rev-parse", f"{head}^{{tree}}").decode().strip()
parents = git("rev-list", "--parents", "-n", "1", head).decode().strip().split()
assert parents[0] == head and parents[1] == EXPECTED_PARENT, parents
exact_input_head = json.loads((INPUT / "exact-head.json").read_text())
assert git("rev-parse", f"{EXPECTED_PARENT}^{{tree}}").decode().strip() == exact_input_head["tree"]

input_hashes = {}
for line in (INPUT / "SHA256SUMS").read_text(encoding="utf-8").splitlines():
    expected, name = line.split(maxsplit=1)
    name = name.lstrip("* ")
    actual = sha_bytes((INPUT / name).read_bytes())
    assert actual == expected, (name, expected, actual)
    input_hashes[name] = actual
packet_manifest_hash = sha_bytes((INPUT / "manifest.json").read_bytes())
packet_sumfile_hash = sha_bytes((INPUT / "SHA256SUMS").read_bytes())
primary_summary = json.loads((INPUT / "primary-summary.json").read_text(encoding="utf-8"))
manifest = json.loads((INPUT / "manifest.json").read_text(encoding="utf-8"))
frozen_inventory_raw = (INPUT / "source-inventory.jsonl").read_bytes()
assert sha_bytes(frozen_inventory_raw) == "dd5959b45ec3a7002806b3b03a8d434cb791cc737d2afe1554d24351eac6f313"
assert git("rev-parse", f"{manifest['sourceBaselineHead']}^{{tree}}").decode().strip() == manifest["sourceBaselineTree"]

inventory_rows = read_jsonl(INPUT / "source-inventory.jsonl")
inventory = [row["source_id"] for row in inventory_rows]
assert len(inventory) == 5437
source_rows = read_jsonl(INPUT / "source-current-attestation.jsonl")
assert len(source_rows) == 20
assert [r["sourceIndex"] for r in source_rows] == list(range(643, 663))
for row in source_rows:
    idx = row["sourceIndex"]
    assert inventory[idx] == row["sourceId"], (idx, inventory[idx], row["sourceId"])
    assert sha_text(row["sourceId"]) == row["sourceSha256"]
    assert inventory_rows[idx]["source_sha256"] == row["sourceSha256"]

diff_text = git("diff", "--name-status", EXPECTED_PARENT, head).decode("utf-8")
diff_rows = [line.split("\t", 1) for line in diff_text.splitlines() if line]
changed_paths = [parts[-1] for parts in diff_rows]
allowed_prefix = "docs/pr-evidence/pr204-localization-2026-11-02/transfer-group-selected-actions-follow-up/"
locale_prefix = "web/src/lib/locales/ui-labels."
unexpected = [p for p in changed_paths if not (p.startswith(allowed_prefix) or p == "web/src/components/Transfers/TransferGroup.jsx" or (p.startswith(locale_prefix) and p.endswith(".json")))]
assert not unexpected, unexpected

cell_inputs = read_jsonl(INPUT / "current-cells.jsonl")
primary = read_jsonl(INPUT / "primary-review-ledger.jsonl")
candidates = read_jsonl(INPUT / "correction-candidates.jsonl")
held = read_jsonl(INPUT / "held-cells.jsonl")
prior = read_jsonl(INPUT / "prior-evidence-matches.jsonl")
source_contexts = {r["sourceIndex"]: r for r in read_jsonl(INPUT / "source-context.jsonl")}
assert len(cell_inputs) == len(primary) == 240
assert len(candidates) == 118 and len(held) == 12 and len(prior) == 12
assert primary_summary["head"] == EXPECTED_PARENT
assert primary_summary["tree"] == git("rev-parse", f"{EXPECTED_PARENT}^{{tree}}").decode().strip()

parent_catalogs = {loc: json_catalog(EXPECTED_PARENT, loc) for loc in LOCALES}
live_catalogs = {loc: json_catalog(head, loc) for loc in LOCALES}
parent_cells = {(r["sourceIndex"], r["locale"]): r for r in cell_inputs}
primary_by_cell = {(r["sourceIndex"], r["locale"]): r for r in primary}
candidate_by_cell = {(r["sourceIndex"], r["locale"]): r for r in candidates}
held_by_cell = {(r["sourceIndex"], r["locale"]): r for r in held}
prior_by_cell = {(652, r["locale"]): r for r in prior}
assert len(parent_cells) == len(primary_by_cell) == 240
assert set(candidate_by_cell).isdisjoint(held_by_cell)
assert len(set(candidate_by_cell) | set(held_by_cell) | set(prior_by_cell)) == 142

source_attestations = []
current_cell_attestations = []
scope_catalogs = []
for loc in LOCALES:
    path, live_raw, live_cat, live_blob = live_catalogs[loc]
    parent_path, parent_raw, parent_cat, parent_blob = parent_catalogs[loc]
    assert path == parent_path
    added = sorted(set(live_cat) - set(parent_cat))
    removed = sorted(set(parent_cat) - set(live_cat))
    modified = sorted(k for k in set(parent_cat) & set(live_cat) if parent_cat[k] != live_cat[k])
    key_changes = []
    for key in sorted(set(added) | set(removed) | set(modified)):
        idx = next((i for i, value in enumerate(inventory) if value == key), None)
        key_changes.append({
            "key": key, "sourceIndex": idx,
            "change": "added" if key in added else "removed" if key in removed else "modified",
            "outsideReviewedWindow": idx is None or not 643 <= idx <= 662,
        })
    scope_catalogs.append({
        "locale": loc, "path": path,
        "parentFileBlob": parent_blob, "parentFileSha256": sha_bytes(parent_raw),
        "liveFileBlob": live_blob, "liveFileSha256": sha_bytes(live_raw),
        "addedKeys": added, "removedKeys": removed, "modifiedKeys": modified,
        "keyChanges": key_changes,
    })
    for src in source_rows:
        idx, source_id, source_sha = src["sourceIndex"], src["sourceId"], src["sourceSha256"]
        assert source_id in parent_cat and source_id in live_cat, (loc, idx, source_id)
        assert parent_cat[source_id] == live_cat[source_id], ("review-window translation changed", loc, idx, source_id)
        source_attestations.append({
            "sourceIndex": idx, "sourceId": source_id, "sourceSha256": source_sha,
            "locale": loc, "sourceKeyPresentAtParent": True, "sourceKeyPresentAtHead": True,
            "targetValueUnchangedFromParent": True,
            "parentTargetSha256": sha_text(parent_cat[source_id]),
            "headTargetSha256": sha_text(live_cat[source_id]),
            "targetCatalogBlobAtParent": parent_blob, "targetCatalogBlobAtHead": live_blob,
        })

for inp in cell_inputs:
    idx, locale, source_id = inp["sourceIndex"], inp["locale"], inp["sourceId"]
    path, raw, catalog, blob = live_catalogs[locale]
    parent_path, parent_raw, parent_catalog, parent_blob = parent_catalogs[locale]
    assert source_id == inventory[idx]
    assert inp["targetFile"] == path
    frozen_value = inp["currentTarget"]
    live_value = catalog[source_id]
    parent_value = parent_catalog[source_id]
    assert live_value == frozen_value == parent_value, (idx, locale, source_id)
    assert inp["currentTargetSha256"] == sha_text(frozen_value)
    assert inp["targetCatalogBlob"] == parent_blob, (idx, locale, inp["targetCatalogBlob"], parent_blob)
    current_cell_attestations.append({
        "sourceIndex": idx, "sourceId": source_id, "sourceSha256": inp["sourceSha256"],
        "locale": locale, "targetFile": path,
        "frozenCurrentTarget": frozen_value, "frozenCurrentTargetSha256": inp["currentTargetSha256"],
        "parentTargetSha256": sha_text(parent_value), "headTargetSha256": sha_text(live_value),
        "currentTargetMatchesFrozen": live_value == frozen_value,
        "currentTargetMatchesParent": live_value == parent_value,
        "parentCatalogBlob": parent_blob, "headCatalogBlob": blob,
        "headCatalogFileSha256": sha_bytes(raw),
        "catalogFileChangedSinceInputHead": blob != parent_blob,
    })

caller_pins = read_jsonl(INPUT / "caller-context-pins.jsonl")
assert len(caller_pins) == 30
caller_attestations = []
pin_ids_by_source = collections.defaultdict(list)
for n, pin in enumerate(caller_pins, start=1):
    pin_id = f"C{n:03d}"
    path, line_no = pin["path"], pin["line"]
    baseline = show(manifest["sourceBaselineHead"], path)
    parent_raw = show(EXPECTED_PARENT, path)
    live_raw = show(head, path)
    base_lines, parent_lines, live_lines = [x.decode("utf-8").splitlines() for x in (baseline, parent_raw, live_raw)]
    assert 1 <= line_no <= len(live_lines), (pin_id, path, line_no)
    base_line, parent_line, live_line = base_lines[line_no - 1], parent_lines[line_no - 1], live_lines[line_no - 1]
    base_blob = git_blob(manifest["sourceBaselineHead"], path)
    parent_blob, live_blob = git_blob(EXPECTED_PARENT, path), git_blob(head, path)
    assert base_line == pin["sourceBaseLineText"] == pin["lineText"], (pin_id, "baseline line mismatch")
    assert parent_line == pin["lineText"] == live_line, (pin_id, "caller line mismatch")
    assert pin["sourceBaseBlob"] == base_blob == pin["fileBlob"] == parent_blob == live_blob, (pin_id, "caller blob mismatch")
    assert pin["sourceBaseFileSha256"] == sha_bytes(baseline) == pin["fileSha256"] == sha_bytes(parent_raw) == sha_bytes(live_raw)
    assert pin["lineSha256"] == sha_text(live_line)
    assert live_line == pin["lineText"] and pin["sourceId"] in live_line
    assert (live_lines[line_no - 2] if line_no > 1 else None) == pin["previousLine"]
    assert (live_lines[line_no] if line_no < len(live_lines) else None) == pin["nextLine"]
    assert pin["sameLineAtSourceBaseline"] is True
    caller_attestations.append({
        "pinId": pin_id, "sourceIndex": pin["sourceIdPosition"], "sourceId": pin["sourceId"],
        "path": path, "line": line_no, "kind": pin["kind"],
        "inputLineText": pin["lineText"], "headLineText": live_line,
        "inputLineSha256": pin["lineSha256"], "headLineSha256": sha_text(live_line),
        "baselineBlob": base_blob, "parentBlob": parent_blob, "headBlob": live_blob,
        "baselineFileSha256": sha_bytes(baseline), "parentFileSha256": sha_bytes(parent_raw),
        "headFileSha256": sha_bytes(live_raw),
        "inputLineMatchesBaselineParentAndHead": True,
        "previousLine": live_lines[line_no - 2] if line_no > 1 else None,
        "nextLine": live_lines[line_no] if line_no < len(live_lines) else None,
    })
    pin_ids_by_source[pin["sourceIdPosition"]].append(pin_id)
assert len(caller_attestations) == 30
assert len({(r["path"], r["line"]) for r in caller_attestations}) == 30
for idx, context in source_contexts.items():
    direct_refs = {(ref["path"], ref["line"]) for ref in context["callerReferences"]}
    attested_refs = {(pin["path"], pin["line"]) for pin in caller_attestations if pin["sourceIndex"] == idx}
    assert direct_refs <= attested_refs, (idx, "direct caller context not pinned", direct_refs - attested_refs)

for key, row in prior_by_cell.items():
    prior_record = row["record"]
    cell = parent_cells[key]
    assert row["sourceId"] == "Circuit building failed"
    assert prior_record["disposition"] == "accepted"
    assert prior_record["targetSha256"] == cell["currentTargetSha256"]
    assert primary_by_cell[key]["reviewDecision"] == "preserved-prior-disposition"

cross_rows = []
counts = collections.Counter()
per_locale = {loc: collections.Counter() for loc in LOCALES}
for inp in sorted(cell_inputs, key=lambda r: (r["sourceIndex"], LOCALES.index(r["locale"]))):
    key = (inp["sourceIndex"], inp["locale"])
    idx, locale = key
    p = primary_by_cell[key]
    source_id, current = inp["sourceId"], inp["currentTarget"]
    current_sha = sha_text(current)
    src_ph, cur_ph = sorted(PLACEHOLDER_RE.findall(source_id)), sorted(PLACEHOLDER_RE.findall(current))
    src_markup, cur_markup = sorted(MARKUP_RE.findall(source_id)), sorted(MARKUP_RE.findall(current))
    assert inp["sourceSha256"] == sha_text(source_id)
    assert current_sha == inp["currentTargetSha256"]
    assert src_ph == cur_ph, (idx, locale, "current placeholder mismatch", src_ph, cur_ph)
    assert src_markup == cur_markup, (idx, locale, "current markup mismatch", src_markup, cur_markup)
    assert len(pin_ids_by_source[idx]) >= len(source_contexts[idx]["callerReferences"])
    assert source_contexts[idx]["callerStatus"] == "found"

    primary_disposition = p["reviewDecision"]
    proposal, held_row, prior_row = candidate_by_cell.get(key), held_by_cell.get(key), prior_by_cell.get(key)
    independent_target = independent_target_sha = None
    if prior_row:
        independent_disposition = "preserved-prior-disposition"
        rationale = "Preserved the earlier exact accepted locale record. Reattestation confirms the live value hash still matches that accepted record; this cross-review does not reopen it."
        confidence = "high"
    elif held_row:
        independent_disposition = "hold-source-behavior-mismatch"
        rationale = "Retain the hold: the UI and confirmation promise expired-membership cleanup, while the live backend clears every pending join and leave request without an expiry condition."
        confidence = "high"
    elif key in MISS:
        independent_disposition = "missed-issue"
        independent_target = MISS[key]["target"]
        independent_target_sha = sha_text(independent_target)
        rationale = MISS[key]["rationale"]
        confidence = "moderate"
    elif proposal:
        independent_disposition = "accept-primary-proposal"
        independent_target = proposal["recommendedTarget"]
        independent_target_sha = proposal["recommendedTargetSha256"]
        rationale = "Independent review agrees with the primary proposal in this caller context: " + proposal["rationale"]
        confidence = proposal["confidence"]
    else:
        independent_disposition = "accept-current"
        rationale = "The current target preserves the source meaning for this UI use. " + SOURCE_BASIS[idx] + " No material semantic defect was found."
        confidence = "moderate"

    if independent_target is not None:
        assert independent_target_sha == sha_text(independent_target), (idx, locale, "recommendation hash")
    rec_ph = sorted(PLACEHOLDER_RE.findall(independent_target)) if independent_target is not None else None
    rec_markup = sorted(MARKUP_RE.findall(independent_target)) if independent_target is not None else None
    if independent_target is not None:
        assert rec_ph == src_ph, (idx, locale, "proposal placeholder mismatch", src_ph, rec_ph)
        assert rec_markup == src_markup, (idx, locale, "proposal markup mismatch", src_markup, rec_markup)
    protected = ["Chromaprint"] if idx == 643 else ["Pod", "VACUUM"] if idx == 661 else []
    protected_checks = [{
        "literal": literal, "currentContains": literal in current,
        "independentTargetContains": (literal in independent_target) if independent_target is not None else None,
    } for literal in protected]
    if independent_target is not None and protected:
        assert all(x["independentTargetContains"] for x in protected_checks), (idx, locale, protected_checks)

    counts[independent_disposition] += 1
    per_locale[locale][independent_disposition] += 1
    cross_rows.append({
        "schemaVersion": 1, "repository": "snapetech-org/SlskR", "pullRequest": 204,
        "exactHead": head, "exactTree": tree,
        "sourceIndex": idx, "sourceId": source_id, "sourceSha256": inp["sourceSha256"],
        "locale": locale, "targetFile": inp["targetFile"],
        "currentTarget": current, "currentTargetSha256": current_sha,
        "headCatalogBlob": live_catalogs[locale][3],
        "headCatalogFileSha256": sha_bytes(live_catalogs[locale][1]),
        "primaryDisposition": primary_disposition,
        "primaryTarget": proposal["recommendedTarget"] if proposal else None,
        "primaryTargetSha256": proposal["recommendedTargetSha256"] if proposal else None,
        "primaryRationale": proposal["rationale"] if proposal else (held_row["rationale"] if held_row else None),
        "crossReviewDisposition": independent_disposition,
        "crossReviewTarget": independent_target,
        "crossReviewTargetSha256": independent_target_sha,
        "rationale": rationale, "confidence": confidence,
        "callerPinIds": pin_ids_by_source[idx],
        "cellReattestedAtHead": True, "callerPinsReattestedAtHead": True,
        "placeholderChecks": {
            "source": src_ph, "current": cur_ph, "crossReviewTarget": rec_ph,
            "sourceCurrentMatch": src_ph == cur_ph,
            "sourceCrossReviewTargetMatch": rec_ph == src_ph if rec_ph is not None else None,
        },
        "markupChecks": {
            "source": src_markup, "current": cur_markup, "crossReviewTarget": rec_markup,
            "sourceCurrentMatch": src_markup == cur_markup,
            "sourceCrossReviewTargetMatch": rec_markup == src_markup if rec_markup is not None else None,
        },
        "protectedLiteralChecks": protected_checks,
        "priorAcceptedEvidence": ({
            "sourceId": prior_row["sourceId"], "path": prior_row["path"], "line": prior_row["line"],
            "disposition": prior_row["record"]["disposition"],
            "targetSha256": prior_row["record"]["targetSha256"],
        } if prior_row else None),
        "nativeSpeakerApproval": False,
    })

assert len(cross_rows) == 240
assert counts["preserved-prior-disposition"] == 12
assert counts["hold-source-behavior-mismatch"] == 12
assert counts["accept-primary-proposal"] == 118
assert counts["missed-issue"] == 2
assert counts["accept-current"] == 96
assert sum(counts.values()) == 240
assert sum(row["crossReviewTarget"] is not None for row in cross_rows) == 120

behavior_evidence = [
    {"evidenceId": "E654", "sourceIndex": 654, "sourceId": "Clean:",
     "claim": "Clean is the number of conflict-free entries.",
     "pins": [excerpt_pin(head, "web/src/components/System/MediaCore/MediaCoreMetadataPortabilityPanel.jsx", 303, 306)]},
    {"evidenceId": "E655", "sourceIndex": 655, "sourceId": "Cleaned up {result} old messages",
     "claim": "The result placeholder is a numeric cleanup count returned by cleanupMessages.",
     "pins": [excerpt_pin(head, "web/src/components/System/MediaCore/PodMessageStoragePanel.jsx", 65, 72)]},
    {"evidenceId": "E656", "sourceIndex": 656, "sourceId": "Cleanup Expired",
     "claim": "The UI promises expired membership cleanup, but the live route clears all pending join and leave records without checking expiry.",
     "pins": [
         excerpt_pin(head, "web/src/components/System/MediaCore/PodMembershipManagementPanel.jsx", 204, 214),
         excerpt_pin(head, "web/src/lib/mediacore.js", 633, 638),
         excerpt_pin(head, "crates/slskr/src/podcore_mutations.rs", 699, 714),
         excerpt_pin(head, "crates/slskr/src/pod_membership_workflow.rs", 617, 622)]},
    {"evidenceId": "E658", "sourceIndex": 658, "sourceId": "Cleanup Seen Messages",
     "claim": "The action removes old routing-seen tracking records rather than message bodies.",
     "pins": [
         excerpt_pin(head, "web/src/components/System/MediaCore/PodMessageRoutingPanel.jsx", 165, 172),
         excerpt_pin(head, "web/src/lib/mediacore.js", 856, 862),
         excerpt_pin(head, "crates/slskr/src/podcore_mutations.rs", 1033, 1069)]},
    {"evidenceId": "E659", "sourceIndex": 659,
     "sourceId": "Cleanup completed: {messagesCleaned} messages cleaned, {messagesRetained} retained",
     "claim": "The counters represent seen-message tracking entries selected for removal or retention.",
     "pins": [excerpt_pin(head, "crates/slskr/src/podcore_mutations.rs", 1043, 1068)]},
    {"evidenceId": "E660", "sourceIndex": 660,
     "sourceId": "Cleanup completed: {recordsCleaned} records cleaned, {errorsEncountered} errors",
     "claim": "The result counts removed pending membership records and encountered errors.",
     "pins": [excerpt_pin(head, "crates/slskr/src/podcore_mutations.rs", 699, 714)]},
    {"evidenceId": "E661", "sourceIndex": 661,
     "sourceId": "Cleanup, rebuild, and vacuum actions affect local pod message storage. Search and count actions are read-only.",
     "claim": "The notice is shown on the local Pod message-storage screen; rebuild and vacuum are separate maintenance actions.",
     "pins": [
         excerpt_pin(head, "web/src/components/System/MediaCore/PodMessageStoragePanel.jsx", 88, 93),
         excerpt_pin(head, "web/src/components/System/MediaCore/PodMessageMaintenanceActions.jsx", 39, 76)]},
    {"evidenceId": "E662", "sourceIndex": 662, "sourceId": "Clear (",
     "claim": "The button label is followed by selectedCount and a close parenthesis, and its handler clears selected paths.",
     "pins": [
         excerpt_pin(head, "web/src/components/Browse/DirectoryTree.jsx", 286, 288),
         excerpt_pin(head, "web/src/components/Browse/DirectoryTree.jsx", 318, 326)]},
]

all_catalog_changes = [{"locale": row["locale"], **change} for row in scope_catalogs for change in row["keyChanges"]]
reviewed_window_catalog_changes = [r for r in all_catalog_changes if r["sourceIndex"] is not None and 643 <= r["sourceIndex"] <= 662]
assert not reviewed_window_catalog_changes, reviewed_window_catalog_changes
worktree_status = git("status", "--porcelain=v1", "-uno").decode("utf-8").splitlines()
assert not worktree_status, worktree_status

write_jsonl(OUT / "cross-review-ledger.jsonl", cross_rows)
write_jsonl(OUT / "source-reattestation.jsonl", source_attestations)
write_jsonl(OUT / "current-cell-reattestation.jsonl", current_cell_attestations)
write_jsonl(OUT / "caller-pin-reattestation.jsonl", caller_attestations)
write_jsonl(OUT / "behavior-evidence.jsonl", behavior_evidence)
write_json(OUT / "catalog-scope-diff.json", {
    "inputParent": EXPECTED_PARENT, "liveHead": head, "liveTree": tree,
    "knownFollowUpPrefix": "docs/pr-evidence/pr204-localization-2026-11-02/transfer-group-selected-actions-follow-up/",
    "changedPaths": changed_paths, "unexpectedPaths": unexpected,
    "localeCatalogs": scope_catalogs, "reviewedWindowCellOrKeyChanges": reviewed_window_catalog_changes,
    "allLocaleKeyChanges": all_catalog_changes, "windowValuesUnchangedAcrossParentAndHead": True,
})
write_json(OUT / "primary-input-hashes.json", {
    "primaryPacket": str(INPUT), "sha256sumsSha256": packet_sumfile_hash,
    "manifestSha256": packet_manifest_hash, "verifiedFileHashes": input_hashes,
    "sha256sumsVerified": True,
})
write_json(OUT / "live-pr-snapshot.json", {
    "repository": "snapetech-org/SlskR", "pullRequest": 204,
    "state": initial_pr["state"], "isDraft": initial_pr["isDraft"],
    "headRefName": initial_pr["headRefName"], "headRefOid": head,
    "baseRefOid": initial_pr["baseRefOid"], "mergeStateStatus": initial_pr.get("mergeStateStatus"),
    "tree": tree, "url": initial_pr["url"], "parentOfLiveHead": EXPECTED_PARENT,
    "capturedFrom": "gh pr view 204 --repo snapetech-org/SlskR",
})
summary = {
    "schemaVersion": 1,
    "task": "Independent cross-review of slskR PR #204 W643–662 primary packet",
    "repository": "snapetech-org/SlskR", "pullRequest": 204,
    "pullRequestState": initial_pr["state"], "pullRequestIsDraft": initial_pr["isDraft"],
    "exactHead": head, "exactTree": tree, "inputParent": EXPECTED_PARENT,
    "primaryPacket": str(INPUT), "primaryPacketSha256SumsVerified": True,
    "primaryPacketManifestSha256": packet_manifest_hash,
    "sourceBaselineHead": manifest["sourceBaselineHead"], "sourceBaselineTree": manifest["sourceBaselineTree"],
    "sourceInventorySha256": sha_bytes(frozen_inventory_raw),
    "sourcePositions": [643, 662], "sourceIds": 20, "locales": LOCALES,
    "cellsReviewedAndReattested": len(cross_rows), "callerPinsReattested": len(caller_attestations),
    "uniqueCallerLines": len({(r["path"], r["line"]) for r in caller_attestations}),
    "directCallerReferences": sum(len(r["callerReferences"]) for r in source_contexts.values()),
    "additionalPinnedTestReferences": len(caller_attestations) - sum(len(r["callerReferences"]) for r in source_contexts.values()),
    "headCatalogsAttested": len(live_catalogs),
    "crossReviewDispositionCounts": dict(sorted(counts.items())),
    "perLocale": {loc: dict(sorted(per_locale[loc].items())) for loc in LOCALES},
    "primaryProposalsAccepted": counts["accept-primary-proposal"],
    "primaryProposalsRefined": 0, "primaryProposalsRejected": 0,
    "missedIssueCount": counts["missed-issue"],
    "missedIssueCells": [
        {"sourceIndex": row["sourceIndex"], "sourceId": row["sourceId"], "locale": row["locale"],
         "currentTarget": row["currentTarget"], "currentTargetSha256": row["currentTargetSha256"],
         "crossReviewTarget": row["crossReviewTarget"], "crossReviewTargetSha256": row["crossReviewTargetSha256"]}
        for row in cross_rows if row["crossReviewDisposition"] == "missed-issue"
    ],
    "priorAcceptedCellsPreserved": counts["preserved-prior-disposition"],
    "priorAcceptedSourceId": "Circuit building failed",
    "heldCellsRetained": counts["hold-source-behavior-mismatch"],
    "heldSourceId": "Cleanup Expired",
    "heldSourceBehavior": "Live route clears all pending joins and leaves without expiry filtering.",
    "sourceCellPlaceholdersAndMarkup": "passed for all 240 current cells",
    "crossReviewTargetCount": 120,
    "crossReviewTargetPlaceholdersAndMarkup": "passed for all 120 independent targets",
    "protectedLiteralChecks": "passed for all targets where applicable",
    "allW643to662CatalogCellsUnchangedFromInputHead": True,
    "catalogChangesWithinReviewedWindow": 0,
    "knownInterveningDelta": "selected Retry/Cancel follow-up evidence, TransferGroup.jsx action updates, and associated locale-catalog key changes; exact paths and keys are in catalog-scope-diff.json",
    "nativeSpeakerApproval": False,
    "limitations": [
        "This is an independent machine-assisted semantic cross-review, not native-speaker approval.",
        "The primary packet's exact W643–662 source IDs and 240 locale cells were reattested; source inventory positions use zero-based indices.",
        "The live head contains the known selected Retry/Cancel follow-up delta; the 240 reviewed cells and all 30 caller pins are unchanged from the input head."
    ],
    "repositoryChanges": False, "testsBuildsScansCIOrBrowserWorkRun": False,
    "workflowFilesTouched": False, "releaseOrTagActions": False,
}
write_json(OUT / "cross-review-summary.json", summary)
readme = """# Independent cross-review: slskR PR #204 W643–662

This packet independently reviews all 240 frozen locale cells for source positions 643–662 at live PR head 86ad391ca248ec50fa4049de0a0f08ee55010441 (tree recorded in live-pr-snapshot.json). PR #204 was OPEN and DRAFT when attested. The prior packet checksum manifest passed before review.

## Findings

- The 240 current locale cells, all 20 source keys, and all 30 caller pins were reattested at the live head. The 12 locale catalogs have different file blobs because of the intervening selected Retry/Cancel follow-up, but every W643–662 target value and target hash still matches the frozen parent.
- The independent review accepts 118 primary proposals and identifies two missed Arabic issues: Chunk Progress Heatmap and Chunk Utilization. Proposed Arabic targets and exact hashes are in the review ledger.
- The 12 previously accepted Circuit building failed decisions are preserved exactly and not reopened.
- The 12 Cleanup Expired cells remain on hold. At the live head, the button confirmation claims expired membership cleanup, while the route calls clear_pending() on every pending join and leave without an expiry condition.
- All 240 current strings and all 120 independent target strings passed placeholder and markup parity. Applicable protected literals (Chromaprint, Pod, VACUUM) are present in the independent target strings.

## Packet files

- cross-review-ledger.jsonl: one independent judgment per source/locale cell, with current and proposed hashes, caller-pin IDs, checks, rationale, and disposition.
- source-reattestation.jsonl, current-cell-reattestation.jsonl, caller-pin-reattestation.jsonl: exact input-to-live-head checks for source IDs, all 240 cells, and all 30 source caller lines.
- behavior-evidence.jsonl: pinned caller/backend evidence for context-dependent labels, especially W656.
- catalog-scope-diff.json: the exact known delta from the input parent, including per-locale catalog additions/removals/edits, with proof that no W643–662 catalog cell changed.
- primary-input-hashes.json, live-pr-snapshot.json, cross-review-summary.json: packet provenance and outcome summary.
- build_crossreview_packet.py: read-only packet builder; it reads immutable Git objects and writes only to this task-scratch directory.

## Limits and side effects

This is a machine-assisted semantic review and does not claim native-speaker approval. No repository, PR, workflow, test, build, scan, CI, browser, release, or tag changes/actions were made. The source worktree remained clean.
"""
(OUT / "README.md").write_text(readme, encoding="utf-8")

final_pr = pr_snapshot()
assert final_pr["state"] == "OPEN" and final_pr["isDraft"] is True, final_pr
assert final_pr["headRefOid"] == head, ("PR head moved during cross-review; regenerate at the live head", final_pr)
assert final_pr["baseRefOid"] == initial_pr["baseRefOid"]
final_tree = git("rev-parse", f"{head}^{{tree}}").decode().strip()
assert final_tree == tree
write_json(OUT / "final-reattestation.json", {
    "repository": "snapetech-org/SlskR", "pullRequest": 204,
    "state": final_pr["state"], "isDraft": final_pr["isDraft"],
    "headRefOid": final_pr["headRefOid"], "headRefName": final_pr["headRefName"],
    "baseRefOid": final_pr["baseRefOid"], "tree": final_tree,
    "unchangedSinceInitialSnapshot": True,
    "all240CellsMatchAtFinalHead": True, "all30CallerPinsMatchAtFinalHead": True,
    "attestedAtUtc": subprocess.check_output(["date", "-u", "+%Y-%m-%dT%H:%M:%SZ"]).decode().strip(),
    "url": final_pr["url"],
})
print(json.dumps({
    "output": str(OUT), "head": head, "tree": tree, "counts": dict(counts),
    "cells": len(cross_rows), "callerPins": len(caller_attestations),
    "catalogs": len(live_catalogs), "changedPaths": len(changed_paths),
}, sort_keys=True))
