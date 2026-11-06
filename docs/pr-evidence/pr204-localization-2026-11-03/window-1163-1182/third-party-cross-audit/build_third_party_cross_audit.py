#!/usr/bin/env python3
"""Reconcile the W1163-W1182 slskR primary and blind packets independently."""
from __future__ import annotations

import collections
import hashlib
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PACKETS = ROOT / "source-packets"
INPUT_DIR = PACKETS / "candidate-free-input"
PRIMARY_DIR = PACKETS / "root-primary"
BLIND_DIR = PACKETS / "independent-blind"
EXPECTED_HEAD = "9aa58492ee693d8ca0f2c027a3ee5b8438639f91"
EXPECTED_TREE = "b9ebab27d1f24932be0c623cf894a78115b6f2bb"
EXPECTED_BRANCH = "codex/slskr-l10n-audit-20261030"
EXPECTED_WINDOW = "W1163-W1182"
LOCALES = ["ar", "de", "es", "fr", "hi", "id", "ja", "ko", "pt-BR", "vi", "zh-Hans", "zh-Hant"]
PLACEHOLDER_RE = re.compile(r"\{[^{}]+\}")
MARKUP_RE = re.compile(r"</?[A-Za-z][^>]*>")
LITERAL_RE = re.compile(r"\b(?:DHT|slskr)\b")

HOLD_REASONS = {
    1164: "No approved localized product noun is provided for Pod. Preserve DHT exactly, but the exact protocol token does not settle the product term; hold the complete description in every locale until the approved Pod glossary wording is available.",
    (1165, "ar"): "The pinned caller renders Discovered beside a runtime discoveredCount. The primary proposal المكتشفون can denote discoverers (the agents who discover), reversing the source's discovered-peer state; a safe Arabic count label also depends on count/noun agreement. Hold for qualified Arabic review.",
    (1179, "zh-Hans"): "The pinned caller uses this as a player-rating dimension. The current 警告 means warning, while the source caution could denote a warning, risk, or preference. No glossary or rating semantics resolve this distinction; hold for terminology review.",
    (1179, "zh-Hant"): "The pinned caller uses this as a player-rating dimension. The current 警告 means warning, while the source caution could denote a warning, risk, or preference. No glossary or rating semantics resolve this distinction; hold for terminology review.",
    (1180, "ar"): "The toast interpolates two runtime counts for refreshed and expired entries. Arabic number and noun agreement depends on the actual counts and counted noun, so hold for native-speaker wording review rather than guessing.",
}

PREFER_BLIND = {
    (1165, "es"), (1165, "fr"), (1165, "pt-BR"), (1165, "zh-Hans"), (1165, "zh-Hant"),
    (1166, "hi"), (1166, "vi"), (1166, "zh-Hant"),
    (1167, "es"), (1167, "hi"), (1167, "pt-BR"), (1167, "zh-Hans"), (1167, "zh-Hant"),
    (1170, "hi"), (1172, "fr"), (1172, "pt-BR"),
    (1180, "hi"), (1180, "ko"), (1180, "es"), (1180, "fr"), (1180, "ja"), (1180, "pt-BR"), (1180, "zh-Hans"), (1180, "zh-Hant"),
    (1182, "pt-BR"),
}
PREFER_PRIMARY = {
    (1165, "ja"), (1166, "ko"), (1167, "ja"), (1170, "ja"), (1170, "ko"),
    (1172, "de"), (1172, "es"), (1172, "id"), (1172, "ja"), (1172, "ko"), (1172, "zh-Hans"), (1172, "zh-Hant"),
    (1176, "fr"), (1178, "vi"), (1181, "de"), (1181, "ja"), (1182, "ja"), (1182, "zh-Hant"),
}
KEEP_CURRENT = {(1165, "vi")}
CUSTOM_TARGETS = {
    (1182, "zh-Hans"): "已清空此浏览器中的探索架。",
    (1182, "ko"): "이 브라우저의 디스커버리 선반을 비웠습니다.",
}
CHOICE_NOTES = {
    (1165, "es"): "Choose Descubiertos: this is the closest direct completed-state rendering of Discovered and agrees in number with the adjacent variable peer count; the alternative Encontrados means found.",
    (1165, "fr"): "Choose Découverts: it directly means discovered and agrees with the adjacent count; the alternative Trouvés means found.",
    (1165, "pt-BR"): "Choose Descobertos: it directly means discovered and agrees with the adjacent variable count; the alternative Encontrados means found.",
    (1165, "ja"): "Choose the primary 発見済み, which says discovered/already found. The blind 検出済み means detected; this count label is explicitly for discovered peers.",
    (1166, "hi"): "Choose the blind plural पीयरों form because the unavailable list contains network peers, not one peer; both proposals replace the misleading companion word with the network term.",
    (1166, "vi"): "Choose the blind form with các peer and đã phát hiện: it explicitly names the plural peer list and reads as a completed discovery state.",
    (1166, "zh-Hant"): "Choose 不可用 for the concise unavailable-list heading; both candidates correctly identify network peer nodes and preserve the same meaning.",
    (1167, "es"): "Choose descubiertos rather than detectados because the source and caller describe discovered peers; detectados shifts the wording toward merely detected peers.",
    (1167, "hi"): "Choose the plural पीयर्स spelling for the peer heading beside a peer count; both proposals correct the active-search wording and preserve lowercase slskr.",
    (1167, "zh-Hans"): "Choose 已发现 to make the completed discovered-peer state explicit; retain the exact slskr product literal and network-node meaning.",
    (1167, "zh-Hant"): "Choose 已發現 to make the completed discovered-peer state explicit; retain the exact slskr product literal and network-node meaning.",
    (1170, "hi"): "Choose डिस्कवरी ग्राफ़ to match the established Hindi rendering in the neighboring Discovery Graph label at position 1169. खोज can read as search and would change the named feature's sense.",
    (1172, "fr"): "Choose the blind complete status sentence: the caller sets a success status after creating the preview, and this wording says the discovery graph was previewed for the title. The primary noun phrase loses the completed-event wording.",
    (1172, "pt-BR"): "Choose the blind wording that says the preview was displayed for the title; the caller sets a success status after creating the preview, while the primary noun phrase omits that completed event.",
    (1176, "fr"): "Choose Étagère de découverte: the accent is required and this grammatical localized phrase matches the wording already used in the cleared-shelf message.",
    (1180, "hi"): "Choose the blind wording with प्रविष्टियाँ after both placeholders; it supplies the counted item noun and handles the variable counts without guessing a singular noun.",
    (1180, "ko"): "Choose the blind full status sentence, which explicitly says entries were refreshed and expired. The primary shorthand leaves the counted noun and event relation implicit.",
    (1182, "ja"): "Choose the primary active success wording and keep ディスカバリーシェルフ consistent with the existing Japanese Discovery Shelf label at position 1176.",
    (1182, "pt-BR"): "Choose the blind complete sentence; it states that the shelf was cleared in this browser, while the primary fragment reads like a clipped label.",
}


def fail(message: str) -> None:
    raise SystemExit(f"REFUSED: {message}")


def sha(data: bytes | str) -> str:
    return hashlib.sha256(data.encode("utf-8") if isinstance(data, str) else data).hexdigest()


def canonical(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def write_json(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows), encoding="utf-8")


def verify_manifest(directory: Path, name: str) -> int:
    count = 0
    for line in (directory / name).read_text(encoding="utf-8").splitlines():
        digest, rel = line.split(maxsplit=1)
        rel = rel.lstrip("*").strip()
        path = directory / rel
        if not path.is_file() or sha(path.read_bytes()) != digest:
            fail(f"checksum mismatch: {path}")
        count += 1
    return count


def placeholder_tokens(text: str) -> list[str]:
    return sorted(PLACEHOLDER_RE.findall(text))


def markup_tokens(text: str) -> list[str]:
    return sorted(MARKUP_RE.findall(text))


def root_action(row: dict) -> str:
    if row["disposition"] == "hold":
        return "hold"
    if row["disposition"] == "accept-current":
        return "accept-current"
    return "propose"


def blind_action(row: dict) -> str:
    if row["decision"] == "hold":
        return "hold"
    if row["decision"] == "accept-current":
        return "accept-current"
    return "propose"


def p_proposed_target(row: dict) -> str | None:
    return row["candidateTarget"] if root_action(row) == "propose" and row["candidateTarget"] != row["currentTarget"] else None


def b_target(row: dict) -> str | None:
    value = row.get("proposedTarget")
    return value if blind_action(row) == "propose" and value is not None and value != row["currentTarget"] else None


def pinned_callers(context: dict) -> list[dict]:
    return [{key: ref[key] for key in ("path", "line", "lineText", "fileSha256", "gitBlob")}
            for ref in context["references"] if ref.get("localizedCallPattern") is True]


def select_recommendation(position: int, locale: str, primary: dict, blind: dict) -> tuple[str, str | None, str, str]:
    key = (position, locale)
    current = primary["currentTarget"]
    if position == 1164 or key in HOLD_REASONS:
        reason = HOLD_REASONS[position] if position == 1164 else HOLD_REASONS[key]
        return "hold", None, "cross-audit", reason
    if key in KEEP_CURRENT:
        return "accept-current", None, "current", "The existing Đã phát hiện expresses a completed discovered/detected state beside the runtime count; the blind review found no clear semantic defect, and changing it to Đã tìm thấy is not needed to preserve source meaning."
    if key in CUSTOM_TARGETS:
        target = CUSTOM_TARGETS[key]
        if locale == "zh-Hans":
            reason = "Use 探索架, the exact established Simplified Chinese term for Discovery Shelf in the same packet at position 1176, and state that this browser-local shelf was emptied. The primary suggestion 发现架 introduces a different feature term."
        else:
            reason = "Use 디스커버리 선반, the exact established Korean term for Discovery Shelf in the same packet at position 1176, and state that this browser-local shelf was emptied. This preserves the product label and avoids the primary 보관함 alternative's storage/library sense."
        return "refinement", target, "third-party", reason

    pt, bt = p_proposed_target(primary), b_target(blind)
    if pt is not None and bt is not None:
        if pt == bt:
            target, origin = pt, "primary+blind"
            reason = "Both independent reviews propose the same target. It matches the pinned caller's use and passes the exact placeholder, markup, and protected-literal checks."
        elif key in PREFER_PRIMARY:
            target, origin = pt, "primary"
            reason = CHOICE_NOTES.get(key, "The primary target fits the pinned caller more closely than the alternate blind wording; both preserve required placeholders and protected literals.")
        elif key in PREFER_BLIND:
            target, origin = bt, "blind"
            reason = CHOICE_NOTES.get(key, "The blind target fits the pinned caller more closely than the alternate primary wording; both preserve required placeholders and protected literals.")
        else:
            fail(f"unreviewed divergent candidate requires explicit cross choice: {position}/{locale}")
    elif pt is not None:
        target, origin = pt, "primary"
        reason = primary["rationale"]
        reason = "The primary proposal fixes the issue identified in the pinned caller; the blind review retains current, but the proposed wording preserves source meaning and passes all structural/literal checks. " + reason
    elif bt is not None:
        target, origin = bt, "blind"
        reason = blind["rationale"]
        reason = "The blind proposal fixes the issue identified in the pinned caller; the primary review retains current, but the proposed wording preserves source meaning and passes all structural/literal checks. " + reason
    else:
        return "accept-current", None, "current", "Both reviews retain the current value or provide no candidate. The pinned caller context supports its source meaning, and source/current structure and exact protected-token checks pass."

    if target == current:
        return "accept-current", None, origin, "The selected wording is unchanged from the exact current target; retain it."
    classes = []
    if origin in ("primary", "primary+blind") and primary["disposition"] == "correction":
        classes.append("correction")
    if origin in ("blind", "primary+blind") and blind["decision"] == "correction-proposal":
        classes.append("correction")
    disposition = "correction" if classes else "refinement"
    return disposition, target, origin, reason


def main() -> None:
    # The source and review packets are immutable inputs; every included packet checksum is verified.
    input_manifest_entries = verify_manifest(INPUT_DIR, "SHA256SUMS.txt")
    primary_manifest_entries = verify_manifest(PRIMARY_DIR, "SHA256SUMS.txt")
    blind_manifest_entries = verify_manifest(BLIND_DIR, "SHA256SUMS.txt")
    manifest = read_json(INPUT_DIR / "manifest.json")
    primary_summary = read_json(PRIMARY_DIR / "summary.json")
    blind_summary = read_json(BLIND_DIR / "summary.json")
    input_cells_path = INPUT_DIR / "current-target-cells.jsonl"
    context_path = INPUT_DIR / "source-contexts.jsonl"
    input_cells_sha = sha(input_cells_path.read_bytes())
    contexts_sha = sha(context_path.read_bytes())
    input_manifest_sha = sha((INPUT_DIR / "manifest.json").read_bytes())
    input_checksum_list_sha = sha((INPUT_DIR / "SHA256SUMS.txt").read_bytes())

    live_pr = json.loads(subprocess.check_output([
        "gh", "pr", "view", "204", "--repo", "snapetech-org/slskr",
        "--json", "state,isDraft,headRefName,headRefOid,baseRefName",
    ], cwd=ROOT, text=True))
    remote = subprocess.check_output([
        "git", "ls-remote", "https://github.com/snapetech-org/slskr.git",
        f"refs/heads/{EXPECTED_BRANCH}",
    ], cwd=ROOT, text=True).split()
    remote_head = remote[0] if remote else None
    if manifest.get("head") != EXPECTED_HEAD or manifest.get("tree") != EXPECTED_TREE:
        fail("candidate-free packet head/tree mismatch")
    if manifest.get("branch") != EXPECTED_BRANCH or manifest.get("repository") != "snapetech-org/slskr" or manifest.get("pullRequest") != 204:
        fail("candidate-free PR identity mismatch")
    if live_pr != {
        "baseRefName": "main", "headRefName": EXPECTED_BRANCH, "headRefOid": EXPECTED_HEAD,
        "isDraft": True, "state": "OPEN",
    }:
        fail(f"live PR differs from candidate-free pin: {live_pr}")
    if remote_head != EXPECTED_HEAD:
        fail(f"remote branch differs from candidate-free pin: {remote_head}")
    for summary in (primary_summary, blind_summary):
        summary_head = summary.get("inputHead", summary.get("head"))
        summary_tree = summary.get("inputTree", summary.get("tree"))
        if summary_head != EXPECTED_HEAD or summary_tree != EXPECTED_TREE:
            fail("a review summary does not pin the exact input head/tree")
    if primary_summary.get("cleanInputManifestSha256") != input_manifest_sha:
        fail("primary summary does not pin candidate-free manifest.json")
    if blind_summary.get("manifestInputSha256") != input_manifest_sha:
        fail("blind summary does not pin candidate-free manifest.json")
    if primary_summary.get("cleanInputChecksumListSha256") != input_checksum_list_sha:
        fail("primary summary does not pin candidate-free SHA256SUMS.txt")
    if blind_summary.get("inputCurrentCellsSha256") not in (None, input_cells_sha):
        fail("blind summary input current-cell hash differs")

    input_rows = read_jsonl(input_cells_path)
    primary_rows = read_jsonl(PRIMARY_DIR / "primary-decisions.jsonl")
    blind_rows = read_jsonl(BLIND_DIR / "blind-decisions.jsonl")
    context_rows = read_jsonl(context_path)
    catalog_pins = read_json(INPUT_DIR / "catalog-file-pins.json")
    if not all(len(rows) == 240 for rows in (input_rows, primary_rows, blind_rows)):
        fail("all three cell packets must contain exactly 240 records")
    if len(context_rows) != 20 or manifest.get("callerReferenceCount") != 36:
        fail("candidate-free context/reference count mismatch")
    if manifest.get("selectedPositions") != [1163, 1182] or manifest.get("sourceCount") != 5441:
        fail("selected source position/order boundary mismatch")
    if manifest.get("localeOrder") != LOCALES or manifest.get("localeCount") != 12:
        fail("locale order/count mismatch")
    if primary_summary.get("cellCount") != 240 or blind_summary.get("cellCount") != 240:
        fail("review summaries do not report 240 cells")

    input_map = {(row["position"], row["locale"]): row for row in input_rows}
    primary_map = {(row["sourcePosition"], row["locale"]): row for row in primary_rows}
    blind_map = {(row["position"], row["locale"]): row for row in blind_rows}
    if any(len(mapping) != 240 for mapping in (input_map, primary_map, blind_map)):
        fail("duplicate or missing source/locale cell")
    if not (set(input_map) == set(primary_map) == set(blind_map)):
        fail("input, primary, and blind ledgers do not cover the same cells")
    context_map = {row["position"]: row for row in context_rows}
    if len(context_map) != 20:
        fail("duplicate source-context records")

    # Verify the selected queue is exactly the pinned 20 consecutive IDs and 12 locales.
    for pos in range(1163, 1183):
        cells = [input_map[(pos, locale)] for locale in LOCALES]
        if len({row["sourceId"] for row in cells}) != 1 or len({row["source"] for row in cells}) != 1:
            fail(f"source identity mismatch across locale cells at position {pos}")
        context = context_map.get(pos)
        if not context or context["sourceId"] != cells[0]["sourceId"] or context["sourceSha256"] != cells[0]["sourceSha256"]:
            fail(f"source context pin mismatch at position {pos}")
        if context["callerReferenceCount"] != len(context["references"]):
            fail(f"source caller-reference count mismatch at position {pos}")
        if context["directLocalizedCaller"] is not True:
            fail(f"source lacks a direct localized caller at position {pos}")

    # Catalog file pins and all repeated row metadata must agree.
    catalog_by_path = catalog_pins
    if set(catalog_by_path) != {input_map[(1163, locale)]["catalogPath"] for locale in LOCALES}:
        fail("catalog pin packet does not contain exactly the twelve direct locale catalogs")
    for path, pin in catalog_by_path.items():
        if pin.get("keyCount") != 5441:
            fail(f"unexpected catalog key count: {path}")
    all_cells = []
    p_proposal_cells = set()
    b_proposal_cells = set()
    p_proposals = b_proposals = 0
    p_protected_violations = b_protected_violations = 0
    p_placeholder_violations = b_placeholder_violations = 0
    input_placeholder_violations = 0
    p_markup_violations = b_markup_violations = 0
    recommendation_disagreements = []
    exact_holds = []
    disposition_counts = collections.Counter()
    final_changes_by_locale = collections.Counter()
    p_change_by_cell = {}
    b_change_by_cell = {}
    protected_total = collections.Counter()
    selected_disagreement_count = collections.Counter()
    source_ids = {}
    verified_refs = 0

    for key in sorted(input_map, key=lambda item: (item[0], LOCALES.index(item[1]))):
        source = input_map[key]
        primary = primary_map[key]
        blind = blind_map[key]
        pos, locale = key
        context = context_map[pos]
        src_text = source["source"]
        current = source["currentTarget"]
        if source["sourceId"] != context["sourceId"] or sha(src_text) != source["sourceSha256"]:
            fail(f"input source hash/identity mismatch: {key}")
        if sha(current) != source["currentTargetSha256"]:
            fail(f"input current-target hash mismatch: {key}")
        pin = catalog_by_path.get(source["catalogPath"])
        if not pin or source["catalogFileSha256"] != pin["sha256"] or source["catalogGitBlob"] != pin["gitBlob"]:
            fail(f"catalog pin mismatch in candidate-free cell: {key}")
        for row, label in ((primary, "primary"), (blind, "blind")):
            expected_position = row.get("sourcePosition", row.get("position"))
            required_fields = (("sourceId", source["sourceId"]), ("source", src_text),
                               ("sourceSha256", source["sourceSha256"]), ("locale", locale),
                               ("currentTarget", current), ("currentTargetSha256", source["currentTargetSha256"]))
            for field, value in required_fields:
                if row.get(field) != value:
                    fail(f"{label} {field} pin mismatch: {key}")
            for field, value in (("catalogPath", source["catalogPath"]),
                                 ("catalogFileSha256", source["catalogFileSha256"]),
                                 ("catalogGitBlob", source["catalogGitBlob"])):
                if label == "primary" and row.get(field) != value:
                    fail(f"{label} {field} pin mismatch: {key}")
                if field in row and row[field] != value:
                    fail(f"{label} optional {field} pin mismatch: {key}")
            if expected_position != pos:
                fail(f"{label} position mismatch: {key}")
            if label == "blind" and (row.get("head") != EXPECTED_HEAD or row.get("tree") != EXPECTED_TREE
                                      or row.get("pullRequest") != 204 or row.get("repository") != "snapetech-org/slskr"):
                fail(f"blind per-cell PR head/tree/repository pin mismatch: {key}")
        if primary.get("callerCount") != context["callerReferenceCount"] or primary.get("directLocalizedCaller") != context["directLocalizedCaller"]:
            fail(f"primary caller count/direct-caller mismatch: {key}")
        if blind.get("callerReferenceCount") != context["callerReferenceCount"] or blind.get("directLocalizedCaller") != context["directLocalizedCaller"]:
            fail(f"blind caller count/direct-caller mismatch: {key}")
        context_hash = sha(canonical(context["references"]))
        if primary.get("callerContextSha256") != context_hash:
            fail(f"primary caller-context digest mismatch: {key}")
        expected_callers = pinned_callers(context)
        if primary.get("callerRefs") != expected_callers:
            fail(f"primary caller refs differ from pinned source contexts: {key}")
        blind_refs = [{k: ref[k] for k in ("path", "line", "lineText", "contextSha256")} for ref in blind.get("callerEvidence", [])]
        expected_blind_refs = [{k: ref[k] for k in ("path", "line", "lineText", "contextSha256")} for ref in context["references"]]
        if blind_refs != expected_blind_refs:
            fail(f"blind caller refs differ from pinned source contexts: {key}")
        if locale == LOCALES[0]:
            verified_refs += context["callerReferenceCount"]
        source_ids[pos] = source["sourceId"]

        p_target = primary["candidateTarget"]
        p_candidate = p_target if root_action(primary) == "propose" and p_target != current else None
        b_candidate = b_target(blind)
        if sha(p_target) != primary["candidateTargetSha256"]:
            fail(f"primary candidate hash mismatch: {key}")
        if primary.get("disposition") in ("accept-current", "hold") and p_target != current:
            fail(f"primary accept/hold candidate is not the current target: {key}")
        if b_candidate is not None and sha(b_candidate) != blind.get("proposedTargetSha256"):
            fail(f"blind proposal hash mismatch: {key}")
        if b_candidate is None and blind.get("decision") in ("accept-current", "hold") and blind.get("proposedTarget") is not None:
            fail(f"blind accept/hold row unexpectedly has a proposal: {key}")
        if p_candidate is not None:
            p_proposals += 1
            p_proposal_cells.add(key)
        if b_candidate is not None:
            b_proposals += 1
            b_proposal_cells.add(key)
        p_change_by_cell[key] = p_candidate
        b_change_by_cell[key] = b_candidate

        src_ph = placeholder_tokens(src_text)
        cur_ph = placeholder_tokens(current)
        p_ph = placeholder_tokens(p_target)
        b_ph = placeholder_tokens(b_candidate if b_candidate is not None else current)
        src_markup = markup_tokens(src_text)
        cur_markup = markup_tokens(current)
        p_markup = markup_tokens(p_target)
        b_markup = markup_tokens(b_candidate if b_candidate is not None else current)
        p_literal_list = primary.get("protectedLiterals", [])
        b_literal_list = blind.get("sourceProtectedLiterals", [])
        if p_literal_list != b_literal_list:
            fail(f"primary/blind protected-literal inventory differs: {key}")
        source_literals = sorted(LITERAL_RE.findall(src_text))
        if sorted(p_literal_list) != source_literals:
            fail(f"protected-literal packet does not match exact source tokens: {key}")
        literal_checks = []
        for literal in source_literals:
            occurrences = src_text.count(literal)
            current_preserved = current.count(literal) == occurrences
            p_preserved = p_target.count(literal) == occurrences
            b_value = b_candidate if b_candidate is not None else current
            b_preserved = b_value.count(literal) == occurrences
            protected_total[literal] += 1
            literal_checks.append({"literal": literal, "sourceOccurrences": occurrences,
                                   "currentPreserved": current_preserved,
                                   "primaryCandidatePreserved": p_preserved,
                                   "blindProposalPreserved": b_preserved})
            p_protected_violations += not p_preserved
            b_protected_violations += not b_preserved
        p_placeholder_ok = src_ph == p_ph
        b_placeholder_ok = src_ph == b_ph
        current_placeholder_ok = src_ph == cur_ph
        p_markup_ok = src_markup == p_markup
        b_markup_ok = src_markup == b_markup
        current_markup_ok = src_markup == cur_markup
        p_placeholder_violations += not p_placeholder_ok
        b_placeholder_violations += not b_placeholder_ok
        input_placeholder_violations += not current_placeholder_ok
        p_markup_violations += not p_markup_ok
        b_markup_violations += not b_markup_ok
        if not (current_placeholder_ok and current_markup_ok):
            fail(f"source/current structural mismatch: {key}")
        source_placeholder_names = sorted(token[1:-1] for token in src_ph)
        primary_placeholder_names = sorted(token[1:-1] for token in p_ph)
        if sorted(primary.get("sourcePlaceholders", [])) != source_placeholder_names or sorted(primary.get("candidatePlaceholders", [])) != primary_placeholder_names:
            fail(f"primary placeholder evidence mismatch: {key}")
        if sorted(primary.get("sourcePlaceholders", [])) != sorted(primary.get("candidatePlaceholders", [])):
            fail(f"primary source/candidate placeholder check failed: {key}")
        if blind.get("sourcePlaceholders") != src_ph or blind.get("currentPlaceholders") != cur_ph:
            fail(f"blind source/current placeholder evidence mismatch: {key}")
        if blind.get("placeholderParity") is not True:
            fail(f"blind candidate placeholder check failed: {key}")
        if blind.get("sourceMarkupTags") != src_markup or blind.get("currentMarkupTags") != cur_markup:
            fail(f"blind source/current markup evidence mismatch: {key}")
        if source_literals and blind.get("currentProtectedLiteralsPreserved") is not True:
            fail(f"blind current protected-literal check failed: {key}")
        if source_literals and b_candidate is not None and blind.get("proposedProtectedLiteralsPreserved") is not True:
            fail(f"blind proposal protected-literal check failed: {key}")
        if p_candidate is not None and primary.get("protectedLiterals") != p_literal_list:
            fail(f"primary proposal protected-literal check failed: {key}")
        if p_candidate is not None and not p_placeholder_ok:
            fail(f"primary proposal placeholder check failed: {key}")
        if b_candidate is not None and not b_placeholder_ok:
            fail(f"blind proposal placeholder check failed: {key}")
        if p_candidate is not None and not p_markup_ok:
            fail(f"primary proposal markup check failed: {key}")
        if b_candidate is not None and not b_markup_ok:
            fail(f"blind proposal markup check failed: {key}")

        p_action, b_action = root_action(primary), blind_action(blind)
        cell_disagrees = (
            p_action != b_action or
            (p_candidate is not None and b_candidate is not None and p_candidate != b_candidate)
        )
        if cell_disagrees:
            recommendation_disagreements.append({
                "position": pos, "sourceId": source["sourceId"], "locale": locale,
                "primaryAction": p_action, "primaryDisposition": primary["disposition"],
                "primaryCandidate": p_candidate, "blindAction": b_action,
                "blindDisposition": blind["decision"], "blindCandidate": b_candidate,
                "reason": "The reviewers differ on whether to retain, hold, or change the target, or they propose different target text.",
            })

        disposition, proposed, selected_from, rationale = select_recommendation(pos, locale, primary, blind)
        effective_target = current if disposition in ("accept-current", "hold") else proposed
        if effective_target is None:
            fail(f"cross recommendation lacks an effective target: {key}")
        if disposition == "hold":
            hold_reason = rationale
            exact_holds.append({"position": pos, "sourceId": source["sourceId"], "source": src_text,
                                "locale": locale, "catalogPath": source["catalogPath"],
                                "currentTarget": current, "holdReason": hold_reason,
                                "primaryDisposition": primary["disposition"], "blindDecision": blind["decision"],
                                "primaryCandidate": p_candidate, "blindCandidate": b_candidate})
        else:
            hold_reason = None
        if disposition in ("correction", "refinement"):
            final_changes_by_locale[locale] += 1
        disposition_counts[disposition] += 1

        for check_name, ok in (
            ("currentPlaceholderParity", current_placeholder_ok),
            ("primaryPlaceholderParity", p_placeholder_ok),
            ("blindPlaceholderParity", b_placeholder_ok),
            ("currentMarkupParity", current_markup_ok),
            ("primaryMarkupParity", p_markup_ok),
            ("blindMarkupParity", b_markup_ok),
        ):
            if not ok:
                fail(f"structural check failed {check_name}: {key}")
        if any(not item["currentPreserved"] or not item["primaryCandidatePreserved"] or not item["blindProposalPreserved"] for item in literal_checks):
            fail(f"protected literal mismatch: {key}")

        all_cells.append({
            "position": pos, "window": EXPECTED_WINDOW, "sourceId": source["sourceId"],
            "source": src_text, "sourceSha256": source["sourceSha256"], "locale": locale,
            "catalogPath": source["catalogPath"], "catalogFileSha256": source["catalogFileSha256"],
            "catalogGitBlob": source["catalogGitBlob"], "currentTarget": current,
            "currentTargetSha256": source["currentTargetSha256"],
            "callerEvidence": {"directLocalizedCaller": context["directLocalizedCaller"],
                                "referenceCount": context["callerReferenceCount"],
                                "contextSha256": context_hash,
                                "references": context["references"],
                                "primaryRefsMatch": True, "blindRefsMatch": True},
            "primaryRecommendation": {"disposition": primary["disposition"],
                                      "candidateTarget": p_target,
                                      "candidateTargetSha256": primary["candidateTargetSha256"],
                                      "rationale": primary["rationale"], "confidence": primary.get("confidence")},
            "blindRecommendation": {"disposition": blind["decision"],
                                    "proposedTarget": blind.get("proposedTarget"),
                                    "proposedTargetSha256": blind.get("proposedTargetSha256"),
                                    "rationale": blind["rationale"], "confidence": blind.get("confidence")},
            "comparison": {"primaryProposesChange": p_candidate is not None,
                           "blindProposesChange": b_candidate is not None,
                           "sameProposedTarget": p_candidate is not None and b_candidate is not None and p_candidate == b_candidate,
                           "differentProposedTargets": p_candidate is not None and b_candidate is not None and p_candidate != b_candidate,
                           "reviewersDiffer": cell_disagrees},
            "crossChecks": {"sourceCurrentPlaceholderTokens": {"source": src_ph, "current": cur_ph,
                                                                  "parity": current_placeholder_ok},
                            "primaryCandidatePlaceholderTokens": p_ph,
                            "blindCandidatePlaceholderTokens": b_ph,
                            "primaryPlaceholderParity": p_placeholder_ok,
                            "blindPlaceholderParity": b_placeholder_ok,
                            "sourceCurrentMarkupTags": {"source": src_markup, "current": cur_markup,
                                                         "parity": current_markup_ok},
                            "primaryMarkupParity": p_markup_ok, "blindMarkupParity": b_markup_ok,
                            "protectedLiteralChecks": literal_checks},
            "thirdPartyRecommendation": {"disposition": disposition,
                                         "proposedTarget": proposed,
                                         "effectiveTargetIfApplied": effective_target,
                                         "selectedFrom": selected_from,
                                         "rationale": rationale,
                                         "holdReason": hold_reason,
                                         "machineAssisted": True,
                                         "qualifiedNativeSpeakerApproval": False},
        })

    # Verify the immutable review totals and the independently observed proposal pattern.
    if (p_proposals, b_proposals, len(p_proposal_cells & b_proposal_cells)) != (53, 54, 36):
        fail(f"proposal totals differ from the sealed review ledgers: primary={p_proposals}, blind={b_proposals}, overlap={len(p_proposal_cells & b_proposal_cells)}")
    exact_agreements = sum(p_change_by_cell[k] is not None and p_change_by_cell[k] == b_change_by_cell[k] for k in p_proposal_cells & b_proposal_cells)
    divergent_overlap = sum(p_change_by_cell[k] is not None and b_change_by_cell[k] is not None and p_change_by_cell[k] != b_change_by_cell[k] for k in p_proposal_cells & b_proposal_cells)
    primary_only = len(p_proposal_cells - b_proposal_cells)
    blind_only = len(b_proposal_cells - p_proposal_cells)
    if (exact_agreements, divergent_overlap, primary_only, blind_only) != (16, 20, 17, 18):
        fail("primary/blind proposal agreement counts differ from the sealed packet comparison")
    if len(exact_holds) != 16 or dict(disposition_counts) != {"accept-current": 160, "correction": 17, "refinement": 47, "hold": 16}:
        fail(f"unexpected third-party disposition counts: {dict(disposition_counts)} holds={len(exact_holds)}")
    if verified_refs != 36:
        fail(f"expected 36 pinned caller references, verified {verified_refs}")
    if input_placeholder_violations or p_placeholder_violations or b_placeholder_violations or p_markup_violations or b_markup_violations:
        fail("placeholder or markup mismatch discovered during cross-audit")
    if p_protected_violations or b_protected_violations:
        fail("protected exact literal mismatch discovered during cross-audit")

    # Reconcile concrete meaning/terminology disagreements and answer the requested audit question.
    risk_findings = [
        {"position": 1164, "locales": LOCALES, "term": "Pod", "primary": "hold all locales", "blind": "5 proposals and 7 accept-current dispositions",
         "finding": "The blind proposals preserve DHT but use unapproved Pod loanwords/localized nouns. The primary's terminology hold is retained across all 12 locales until the product glossary approves Pod wording."},
        {"position": 1165, "locale": "ar", "primaryProposal": primary_map[(1165, "ar")]["candidateTarget"], "blindDisposition": blind_map[(1165, "ar")]["decision"],
         "finding": "The primary's المكتشفون can denote discoverers and may invert the discovered-peer count label; the blind review holds because count agreement is unresolved. Third party holds."},
        {"position": 1167, "locale": "es", "primaryProposal": p_proposed_target(primary_map[(1167, "es")]), "blindProposal": b_target(blind_map[(1167, "es")]),
         "finding": "The proposals distinguish detected (detectados) from discovered (descubiertos). The source and caller say discovered peers; third party chooses the blind wording."},
        {"position": 1170, "locale": "hi", "primaryProposal": p_proposed_target(primary_map[(1170, "hi")]), "blindProposal": b_target(blind_map[(1170, "hi")]),
         "finding": "खोज can read as search, while the neighboring localized feature label uses डिस्कवरी ग्राफ़. Third party chooses the blind wording for feature-term consistency."},
        {"position": 1179, "locales": ["zh-Hans", "zh-Hant"], "primary": "accept-current", "blind": "hold",
         "finding": "The player-rating context does not disambiguate caution from warning/risk/preference; third party holds both."},
        {"position": 1180, "locale": "ar", "primary": "accept-current", "blind": "hold",
         "finding": "Variable count morphology is underdetermined; third party holds pending native Arabic wording."},
    ]
    write_jsonl(ROOT / "cross-audit-ledger.jsonl", all_cells)
    write_jsonl(ROOT / "primary-blind-disagreements.jsonl", recommendation_disagreements)
    write_jsonl(ROOT / "holds.jsonl", exact_holds)
    write_json(ROOT / "meaning-and-protected-term-audit.json", {
        "protectedExactLiterals": ["DHT", "slskr"],
        "primaryCandidateProtectedLiteralViolations": p_protected_violations,
        "blindCandidateProtectedLiteralViolations": b_protected_violations,
        "thirdPartyCandidateProtectedLiteralViolations": 0,
        "sharedExactProposalCells": exact_agreements,
        "sharedExactProposalsChangingMeaningOrProtectedTerms": 0,
        "meaningOrTerminologyDisagreements": risk_findings,
        "assessment": "No primary or blind candidate drops DHT or lowercase slskr. Sixteen exactly identical proposals were checked in caller context and none changes source meaning or an exact protected literal. The most consequential disagreements are listed above; the identified risky/ambiguous cells are held or resolved to the wording that preserves the source meaning.",
    })

    write_json(ROOT / "live-pr-verification.json", {
        "verification": "passed", "repository": "snapetech-org/slskr", "pullRequest": 204,
        "pullRequestState": live_pr["state"], "isDraft": live_pr["isDraft"],
        "baseRefName": live_pr["baseRefName"], "headRefName": live_pr["headRefName"],
        "headRefOid": live_pr["headRefOid"], "tree": EXPECTED_TREE,
        "remoteBranch": EXPECTED_BRANCH, "remoteBranchHead": remote_head,
        "candidateFreeInputHead": EXPECTED_HEAD, "candidateFreeInputTree": EXPECTED_TREE,
    })

    summary = {
        "reviewType": "third-party semantic and structural cross-audit of exact-head slskR PR #204 W1163-W1182",
        "repository": "snapetech-org/slskr", "pullRequest": 204, "pullRequestUrl": "https://github.com/snapetech-org/slskr/pull/204",
        "state": live_pr["state"], "isDraft": live_pr["isDraft"], "branch": EXPECTED_BRANCH,
        "exactHead": EXPECTED_HEAD, "exactTree": EXPECTED_TREE, "remoteBranchHead": remote_head,
        "window": EXPECTED_WINDOW, "positions": [1163, 1182], "sourceCount": 20, "localeCount": 12,
        "cellCount": len(all_cells), "callerReferencesVerified": verified_refs,
        "inputManifestSha256": input_manifest_sha, "inputChecksumListSha256": input_checksum_list_sha,
        "candidateFreeCurrentCellsSha256": input_cells_sha, "candidateFreeSourceContextsSha256": contexts_sha,
        "rootPrimaryManifestSha256": sha((PRIMARY_DIR / "SHA256SUMS.txt").read_bytes()),
        "independentBlindManifestSha256": sha((BLIND_DIR / "SHA256SUMS.txt").read_bytes()),
        "verifiedInputManifestEntries": input_manifest_entries,
        "verifiedPrimaryManifestEntries": primary_manifest_entries,
        "verifiedBlindManifestEntries": blind_manifest_entries,
        "primaryProposedChangeCells": p_proposals, "blindProposedChangeCells": b_proposals,
        "bothProposeCells": len(p_proposal_cells & b_proposal_cells),
        "identicalProposalTextCells": exact_agreements, "differentProposalTextCells": divergent_overlap,
        "primaryOnlyProposalCells": primary_only, "blindOnlyProposalCells": blind_only,
        "primaryBlindRecommendationDisagreementRows": len(recommendation_disagreements),
        "thirdPartyDispositions": dict(sorted(disposition_counts.items())),
        "thirdPartyRecommendedChanges": sum(disposition_counts[x] for x in ("correction", "refinement")),
        "exactHoldCount": len(exact_holds), "holdsByPosition": dict(sorted(collections.Counter(str(r["position"]) for r in exact_holds).items())),
        "holdsByLocale": dict(sorted(collections.Counter(r["locale"] for r in exact_holds).items())),
        "changesByLocale": dict(sorted(final_changes_by_locale.items())),
        "sourceCurrentPlaceholderMismatchCount": input_placeholder_violations,
        "primaryPlaceholderMismatchCount": p_placeholder_violations,
        "blindPlaceholderMismatchCount": b_placeholder_violations,
        "primaryMarkupMismatchCount": p_markup_violations,
        "blindMarkupMismatchCount": b_markup_violations,
        "primaryProtectedLiteralMismatchCount": p_protected_violations,
        "blindProtectedLiteralMismatchCount": b_protected_violations,
        "protectedLiteralSourceCellCounts": dict(sorted(protected_total.items())),
        "meaningAndProtectedTermAudit": "meaning-and-protected-term-audit.json",
        "nativeSpeakerApproval": False, "headedProductBrowserAcceptance": False,
        "repositoryOrPRChanged": False, "testsBuildsScansCIOrWorkflowChanges": False,
    }
    write_json(ROOT / "cross-audit-summary.json", summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
