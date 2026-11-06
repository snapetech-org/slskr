import collections
import datetime as dt
import hashlib
import json
import re
import subprocess
from pathlib import Path

ROOT = Path("/home/keith/Documents/code/task-worktrees/localization-20261102-slskr")
PRIMARY = Path("/mnt/disks/scratch/task-scratch/slskr-pr204-window-0903-0922-primary-20261102")
OUT = Path("/mnt/disks/scratch/task-scratch/slskr-pr204-window-0903-0922-crossreview-20261102")
HEAD_EXPECTED = "b1e814ef11d55fd1710d0e2522df14fee9ff0a70"
TREE_EXPECTED = "50fef41fa1abcfcceb9a99cfd756ae014e51e286"
BRANCH = "codex/slskr-l10n-audit-20261030"
LOCALES = ["ar", "de", "es", "fr", "hi", "id", "ja", "ko", "pt-BR", "vi", "zh-Hans", "zh-Hant"]
START, END = 902, 921
REPO = "snapetech-org/slskr"

def run(args, cwd=ROOT):
    return subprocess.check_output(args, cwd=cwd, text=True, stderr=subprocess.DEVNULL).strip()

def sha(data):
    if isinstance(data, str):
        data = data.encode("utf-8")
    return hashlib.sha256(data).hexdigest()

def canonical(value):
    if isinstance(value, str):
        return value.encode("utf-8")
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")

def sha_target(value):
    return sha(canonical(value))

def leaves(value):
    if isinstance(value, str):
        return [value]
    if isinstance(value, dict):
        return [text for child in value.values() for text in leaves(child)]
    if isinstance(value, list):
        return [text for child in value for text in leaves(child)]
    return []

def dump_json(name, value):
    (OUT / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")

def dump_jsonl(name, rows):
    (OUT / name).write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows))

def check_sum_file(folder):
    result = subprocess.run(["sha256sum", "-c", "SHA256SUMS"], cwd=folder, text=True, capture_output=True)
    return {"exitCode": result.returncode, "output": result.stdout.strip(), "stderr": result.stderr.strip()}

OUT.mkdir(parents=True, exist_ok=True)
expected_outputs = {
    "README.md", "cross-review-ledger.jsonl", "source-boundary-caller-checks.jsonl",
    "same-locale-register-pins.jsonl", "crossreview-findings.json", "input-attestation.json",
    "summary.json", "SHA256SUMS",
}
unexpected_outputs = [p.name for p in OUT.iterdir() if p.is_file() and p.name not in expected_outputs | {"build_crossreview.py"}]
assert not unexpected_outputs, f"unexpected files in crossreview output folder: {unexpected_outputs}"

# Live PR, Git object, branch, and clean-worktree attestation.
pr = json.loads(run(["gh", "pr", "view", "204", "--repo", REPO, "--json", "state,isDraft,headRefOid,headRefName,baseRefOid,url"]))
api_tree = run(["gh", "api", f"repos/{REPO}/commits/{HEAD_EXPECTED}", "--jq", ".commit.tree.sha"])
remote_head = run(["git", "ls-remote", "taskgithub", f"refs/heads/{BRANCH}"]).split()[0]
head = run(["git", "rev-parse", "HEAD"])
tree = run(["git", "rev-parse", "HEAD^{tree}"])
branch = run(["git", "branch", "--show-current"])
status = run(["git", "status", "--porcelain"])
assert (pr["state"], pr["isDraft"], pr["headRefOid"], pr["headRefName"]) == ("OPEN", True, HEAD_EXPECTED, BRANCH)
assert (api_tree, remote_head, head, tree, branch, status) == (TREE_EXPECTED, HEAD_EXPECTED, HEAD_EXPECTED, TREE_EXPECTED, BRANCH, "")

primary_sums = check_sum_file(PRIMARY)
assert primary_sums["exitCode"] == 0, primary_sums

# Recompute all 12 catalogs from exact Git objects and verify the same ordered key set.
catalogs = {}
catalog_attestations = []
shared_keys = None
for locale in LOCALES:
    path = f"web/src/lib/locales/ui-labels.{locale}.json"
    raw = subprocess.check_output(["git", "show", f"HEAD:{path}"], cwd=ROOT)
    obj = json.loads(raw)
    keys = sorted(obj)
    if shared_keys is None:
        shared_keys = keys
    assert keys == shared_keys
    assert len(keys) == 5441
    catalogs[locale] = obj
    catalog_attestations.append({
        "locale": locale,
        "path": path,
        "blob": run(["git", "rev-parse", f"HEAD:{path}"]),
        "fileSha256": sha(raw),
        "keyCount": len(keys),
        "orderedKeysetSha256": sha("\n".join(keys)),
    })
assert len(shared_keys) == 5441 and len(shared_keys[START:END + 1]) == 20

primary_rows = [json.loads(line) for line in (PRIMARY / "review-ledger.jsonl").read_text().splitlines() if line.strip()]
assert len(primary_rows) == 240
primary_by_cell = {(r["sourceIndex"], r["locale"]): r for r in primary_rows}
assert len(primary_by_cell) == 240

# Confirm every source and current target digest, primary proposal digest, and final digest.
for row in primary_rows:
    idx, locale, source = row["sourceIndex"], row["locale"], row["sourceId"]
    assert source == shared_keys[idx]
    assert row["sourceSha256"] == sha(source)
    current = catalogs[locale][source]
    assert current == row["currentTarget"]
    assert sha_target(current) == row["currentTargetSha256"]
    if row["proposedTarget"] is not None:
        assert sha_target(row["proposedTarget"]) == row["proposedTargetSha256"]
    assert sha_target(row["reviewedFinal"]) == row["reviewedFinalSha256"]

# Verify every exact production caller file, blob, line, line digest, and pinned context.
caller_rows = [json.loads(line) for line in (PRIMARY / "source-caller-pins.jsonl").read_text().splitlines() if line.strip()]
caller_verifications = []
for pin in caller_rows:
    raw = subprocess.check_output(["git", "show", f"HEAD:{pin['path']}"], cwd=ROOT)
    lines = raw.decode("utf-8").splitlines()
    lineno = pin["line"]
    assert run(["git", "rev-parse", f"HEAD:{pin['path']}"]) == pin["fileBlob"]
    assert sha(raw) == pin["fileSha256"]
    assert lines[lineno - 1] == pin["contextLines"][lineno - pin["contextStartLine"]]["text"]
    assert sha(lines[lineno - 1]) == pin["lineSha256"]
    assert pin["sourceId"] in lines[lineno - 1]
    lo = pin["contextStartLine"]
    assert [{"line": i, "text": lines[i - 1]} for i in range(lo, lo + len(pin["contextLines"]))] == pin["contextLines"]
    caller_verifications.append({
        "sourceIndex": pin["sourceIndex"], "windowLabel": pin["windowLabel"], "sourceId": pin["sourceId"],
        "locale": None, "path": pin["path"], "line": lineno, "fileBlob": pin["fileBlob"],
        "fileSha256": pin["fileSha256"], "lineSha256": pin["lineSha256"],
        "contextStartLine": pin["contextStartLine"], "contextLines": pin["contextLines"],
        "surfaceLine": pin["surfaceLine"], "verified": True,
    })
assert len(caller_rows) == 20

# Verify that the catalog-only source has no exact JavaScript/TypeScript production caller.
gap_source = "Control the local review panel shown with song search results."
grep = subprocess.run(["git", "grep", "-n", "-F", "-e", gap_source, "HEAD", "--", "web/src"], cwd=ROOT, text=True, capture_output=True)
assert grep.returncode in (0, 1), grep.stderr
production_exts = (".js", ".jsx", ".ts", ".tsx")
production_matches = []
for line in grep.stdout.splitlines():
    # Git grep emits HEAD:path:line:content.
    parts = line.split(":", 3)
    if len(parts) < 4:
        continue
    path = parts[1]
    if not path.endswith(production_exts) or ".test." in path or "/__tests__/" in path or "/test/" in path:
        continue
    production_matches.append(line)
assert not production_matches, production_matches

# Verify all previous/forward boundary values against current catalog objects.
boundary_rows = [json.loads(line) for line in (PRIMARY / "boundary-pins.jsonl").read_text().splitlines() if line.strip()]
assert len(boundary_rows) == 24
boundary_checks = []
for pin in boundary_rows:
    idx, locale, source = pin["sourceIndex"], pin["locale"], pin["sourceId"]
    current = catalogs[locale][source]
    assert source == shared_keys[idx]
    assert pin["sourceSha256"] == sha(source)
    assert pin["target"] == current and pin["targetSha256"] == sha_target(current)
    boundary_checks.append({
        "sourceIndex": idx, "windowLabel": pin["windowLabel"], "locale": locale,
        "sourceId": source, "sourceSha256": pin["sourceSha256"],
        "currentTarget": current, "targetSha256": pin["targetSha256"], "matchesCurrentCatalog": True,
    })
assert {r["sourceIndex"] for r in boundary_checks} == {901, 922}
prior_attestation = json.loads((PRIMARY / "prior-disposition-boundary-reattestation.json").read_text())
prior_checks = prior_attestation["previousW902FinalReadbackChecks"] + prior_attestation["newW903StartVsPreviousPinnedBoundary"]
assert len(prior_checks) == 24 and all(r.get("matchesPriorWindowFinalReadback", r.get("matchesPriorFollowingBoundary", False)) for r in prior_checks)

# Same-catalog Spanish voice references used to assess the primary register change.
register_examples = [
    "Browse available Soulseek rooms and join the selected room.",
    "Join the selected Soulseek room; its members will see this account in the participant list.",
    "Stop the selected searches that are still running.",
    "Close this preview and return to the selected files without starting a transfer.",
]
register_rows = []
for source in register_examples:
    idx = shared_keys.index(source)
    target = catalogs["es"][source]
    register_rows.append({
        "locale": "es", "sourceIndex": idx, "sourceId": source, "sourceSha256": sha(source),
        "target": target, "targetSha256": sha_target(target),
        "registerObserved": "tú affirmative/direct imperative",
    })

# Cross-review the primary proposals and the 191 primary accept-current rows.
extra_corrections = {
    (914, "de"): (
        "Export im Format {format} für {count} Wiedergabe kopiert.",
        "The source says the format export is copied for one play, but the current German makes Wiedergabe the object of kopiert. The caller selects the singular source for one history entry and copies the export string, so name the export as the copied object.",
        "moderate",
    ),
    (915, "de"): (
        "Export im Format {format} für {count} Wiedergaben kopiert.",
        "The source says the format export is copied for multiple plays, but the current German makes Wiedergaben the object of kopiert. The caller copies the export string; make Export the object and keep the play count as its qualifier.",
        "moderate",
    ),
    (912, "es"): (
        "Tiempo de espera (milisegundos)",
        "Cooldown is rendered as Período de espera in this same automation flow, while Milisegundos de enfriamiento suggests physical cooling. Use the wait-interval term and make the unit explicit.",
        "moderate",
    ),
    (912, "fr"): (
        "Délai d’attente (millisecondes)",
        "Cooldown is rendered as Délai d’attente in the paired automation label, while temps de recharge suggests recharging. Align the unit label with the wait-interval term.",
        "moderate",
    ),
    (912, "pt-BR"): (
        "Tempo de espera (milissegundos)",
        "Cooldown is rendered as Tempo de espera in the paired automation label, while resfriamento suggests physical cooling. Align the unit label and identify milliseconds as its unit.",
        "moderate",
    ),
    (912, "vi"): (
        "Thời gian chờ (mili giây)",
        "The paired automation label uses Thời gian chờ, while hồi chiêu carries a game ability/recharge sense. Align the unit label with the wait interval and state the unit.",
        "moderate",
    ),
}
revisions = {
    (903, "es"): (
        "The primary changes an existing tú imperative to formal usted. The same Spanish catalog uses tú imperatives in comparable user-facing instructions (Explora, Únete, Detén, Cierra), so retain Continúa for product voice consistency.",
        "moderate",
    ),
}
source_notes = {
    902: "The caller is the active backfill button; the retained/proposed forms are short process-continuation actions.",
    903: "The caller is progress-popup instruction copy; remaining and total counts remain explicit, and the Spanish voice decision is pinned separately.",
    904: "This is an OIDC provider button; the provider placeholder remains the named object of the continue action.",
    905: "This cadence value denotes uninterrupted or continuing operation in an automation recipe.",
    906: "This is a media-server execution-contract table heading; the retained forms function as contract nouns.",
    907: "This heading labels members who contributed opinions; the reviewed labels preserve the contribution sense and colon style.",
    908: "This VPN integration field names the control endpoint; URL is preserved as the protected literal.",
    909: "The twelve translations remain held because there is no exact production source-literal caller at this head.",
    910: "This is the Agent-mode relay connection label followed by its connection state; the German Regler term is retained as a low-confidence terminology watch.",
    911: "This recipe field is the interval between runs; correction targets were checked against its duration-bearing caller.",
    912: "This numeric integration field is a duration unit; the reviewed wording must describe milliseconds of the paired cooldown/wait interval.",
    913: "This is a clipboard-success toast for an action preview; the preview is the copied object.",
    914: "This toast follows copyToClipboard(content); the export is the copied object and play count qualifies its contents.",
    915: "This plural toast follows the same export copy path; Arabic keeps all ICU plural categories and both placeholders.",
    916: "This is a local-file table column heading and is a plural noun rather than a copy action.",
    917: "This diagnostic-bundle control performs a copy action, so action verbs are appropriate.",
    918: "This Library Health button copies a remediation plan; action wording is checked against that caller.",
    919: "This media-server control copies an execution contract, and the target remains an action label.",
    920: "This Discovery Graph control copies a branch report; both source-literal callers were pinned.",
    921: "This Automation Center button copies review history; the history itself is the object of the action.",
}
proposal_checks = {
    (902, "ar"): "The source is the active backfill button label. متابعة expresses the concise resume action; يكمل is a third-person verb.",
    (902, "de"): "Fortsetzen is a direct, standard button verb and is more suitable than colloquial Weitermachen for the pinned backfill action.",
    (902, "hi"): "The caller is an action button. जारी रखें is the polite command; जारी रखना is the dictionary infinitive.",
    (902, "id"): "Lanjutkan presents the backfill action directly; Melanjutkan is a gerund-like form.",
    (902, "ja"): "続行 is an action label for resuming the process; 続く is intransitive and does not express the button action.",
    (902, "ko"): "계속 is a concise action label; 계속하다 is the dictionary form and reads less naturally as a button.",
    (905, "ko"): "마디 없는 means jointless/seamless, which does not describe recipe cadence. 연속적 expresses continuity in this value field.",
    (906, "fr"): "The execution-contract column needs a noun. Contrat is the noun; Contracter is a verb.",
    (907, "ar"): "The heading is nominative. المساهمون agrees in case with الأعضاء, unlike the accusative/genitive المساهمين.",
    (907, "ko"): "The caller counts members who contributed opinions. 기여 means contribution; 기부 changes the meaning to donation.",
    (911, "ar"): "The current term ترطيب means moisturizing. فترة التهدئة names a cooldown interval.",
    (911, "es"): "The source is a time interval in an automation recipe. Período de espera names a duration; Enfriarse is a verb.",
    (911, "fr"): "Délai d’attente names the recipe interval; Refroidir is an infinitive verb.",
    (911, "hi"): "The source is a duration label. शांत हो जाओ is an imperative meaning calm down; कूलडाउन names the technical interval.",
    (911, "id"): "Pendinginan describes cooling. Jeda names the pause between recipe runs.",
    (911, "pt-BR"): "Tempo de espera names the run interval; Esfriar is an infinitive verb.",
    (911, "vi"): "The automation caller describes a wait interval, not a game ability. Thời gian chờ matches that role.",
    (912, "ar"): "The proposal makes the duration-to-unit relation explicit and matches the paired Arabic cooldown term.",
    (912, "de"): "Abklingzeit in Millisekunden is a clearer duration-and-unit label than the awkward compound.",
    (912, "id"): "Waktu jeda (milidetik) describes the automation pause measured in milliseconds, not milliseconds of cooling.",
    (912, "zh-Hans"): "Parentheses visibly mark 毫秒 as the unit of the cooldown duration.",
    (912, "zh-Hant"): "Parentheses visibly mark 毫秒 as the unit of the cooldown duration.",
    (915, "ar"): "The source plural sentence ends in a period. Adding terminal punctuation to all six ICU forms preserves the source sentence boundary, plural categories, and both placeholders.",
    (917, "ar"): "نسخ is an action label; ينسخ is a third-person verb.",
    (917, "de"): "Kopieren is the copy action; Kopie is a noun.",
    (917, "fr"): "Copier is the copy action; Copie is a noun.",
    (917, "hi"): "कॉपी करें is the polite button command; प्रतिलिपि is a noun.",
    (917, "id"): "Salin is the direct action label; Menyalin is a gerund.",
    (917, "pt-BR"): "Copiar is the button action; Cópia is a noun.",
    (918, "ja"): "アクションプランをコピー explicitly labels the button action; のコピー reads as a noun phrase for a copy of the plan.",
    (918, "ko"): "조치 계획 better identifies a remediation/action plan than 실천 계획 in the Library Health caller.",
    (919, "ja"): "The caller copies a live execution contract. 実行契約をコピー expresses that action; 契約書のコピー is a noun phrase.",
    (921, "ar"): "The caller copies Automation Center history. السجل identifies the log/history; التاريخ can be read as a calendar date.",
    (921, "es"): "Copiar el historial makes the history the action's object; Historial de copias reads as a history of copying.",
    (921, "ja"): "履歴をコピー labels the action; コピー履歴 names a copy history.",
    (921, "ko"): "이력을 복사 labels copying the automation history; 복사 기록 can mean a log of copy events.",
}
# Same-locale Spanish register references are a specific evidence source for this review finding.
register_pin_by_source = {
    r["sourceId"]: r for r in register_rows
}
caller_map = collections.defaultdict(list)
for n, pin in enumerate(caller_rows, 1):
    caller_map[pin["sourceIndex"]].append(n)
extra_findings = []
cross_rows = []
for ordinal, primary in enumerate(primary_rows, 1):
    key = (primary["sourceIndex"], primary["locale"])
    idx, locale = key
    current = primary["currentTarget"]
    primary_final = primary["reviewedFinal"]
    final = primary_final
    disposition = primary["disposition"]
    if key in extra_corrections:
        final, rationale, confidence = extra_corrections[key]
        cross_disposition = "additional-correction"
        extra_findings.append({
            "sourceIndex": idx, "windowLabel": idx + 1, "sourceId": primary["sourceId"], "locale": locale,
            "kind": "additional-correction", "from": current, "to": final, "confidence": confidence,
            "detail": rationale,
        })
    elif key in revisions:
        rationale, confidence = revisions[key]
        final = current
        cross_disposition = "revise-primary-proposal"
    elif disposition == "hold":
        rationale = "Keep the primary hold. The exact English source string is absent from production JS/JSX/TS/TSX callers at this head, so the intended UI role cannot be confirmed. The current translation is preserved without semantic approval."
        confidence = "low"
        cross_disposition = "hold"
    elif disposition in ("correction", "refinement"):
        cross_disposition = "accept-primary-" + disposition
        rationale = proposal_checks[key]
        confidence = primary["confidence"]
    else:
        cross_disposition = "retain-current"
        rationale = source_notes[idx] + " The current target preserves the source meaning and fits the pinned UI role; no cross-review change is recommended."
        confidence = "moderate"
        if idx == 910 and locale == "de":
            rationale += " Regler may be context-sensitive for a software relay; retain pending fluent German review because the current evidence does not establish an error."
            confidence = "low"
        if idx == 908:
            rationale += " The protected literal URL is present."
    if key in revisions:
        extra_findings.append({
            "sourceIndex": idx, "windowLabel": idx + 1, "sourceId": primary["sourceId"], "locale": locale,
            "kind": "revise-primary-proposal", "from": primary["proposedTarget"], "to": current,
            "confidence": confidence, "detail": rationale,
            "referencePins": ["same-locale-register-pins.jsonl"],
        })
    caller_refs = caller_map.get(idx, [])
    evidence = [
        f"primary-packet:review-ledger.jsonl#row={ordinal}",
        "input-attestation.json",
    ]
    if caller_refs:
        evidence.append("source-boundary-caller-checks.jsonl#sourceIndex=" + str(idx))
    if idx == 909:
        evidence.append("source-boundary-caller-checks.jsonl#catalog-only-gap")
    if key in revisions:
        evidence.append("same-locale-register-pins.jsonl")
    if key in extra_corrections:
        evidence.append("crossreview-findings.json")
    cross_rows.append({
        "head": HEAD_EXPECTED, "tree": TREE_EXPECTED,
        "sourceIndex": idx, "windowLabel": idx + 1, "sourceId": primary["sourceId"],
        "locale": locale, "sourceSha256": primary["sourceSha256"],
        "currentTarget": current, "currentTargetSha256": primary["currentTargetSha256"],
        "primaryDisposition": {
            "correction": "propose-correction", "refinement": "propose-refinement",
            "accept-current": "accept-current", "hold": "hold",
        }[disposition],
        "primaryTarget": primary_final, "primaryTargetSha256": primary["reviewedFinalSha256"],
        "primaryProposedTarget": primary["proposedTarget"],
        "primaryProposedTargetSha256": primary["proposedTargetSha256"],
        "crossReviewDisposition": cross_disposition,
        "crossReviewTarget": final, "crossReviewTargetSha256": sha_target(final),
        "crossReviewRationale": rationale, "confidence": confidence,
        "nativeSpeakerApproval": False, "evidencePins": evidence,
    })

# Recompute source placeholder/markup parity and protected literals for all cross-reviewed final targets.
placeholder_re = re.compile(r"\{([A-Za-z][A-Za-z0-9_]*)\}")
markup_re = re.compile(r"</?[A-Za-z][^>]*>")
parity_rows = []
for row in cross_rows:
    source_tokens = collections.Counter(placeholder_re.findall(row["sourceId"]))
    target_leaves = leaves(row["crossReviewTarget"])
    target_token_sets = [collections.Counter(placeholder_re.findall(leaf)) for leaf in target_leaves]
    source_markup = collections.Counter(markup_re.findall(row["sourceId"]))
    target_markup_sets = [collections.Counter(markup_re.findall(leaf)) for leaf in target_leaves]
    assert all(source_tokens == tokens for tokens in target_token_sets), (row["sourceIndex"], row["locale"], "placeholder mismatch")
    assert all(source_markup == tokens for tokens in target_markup_sets), (row["sourceIndex"], row["locale"], "markup mismatch")
    if row["sourceIndex"] == 908:
        assert all("URL" in leaf for leaf in leaves(row["crossReviewTarget"]))
    parity_rows.append({
        "sourceIndex": row["sourceIndex"], "locale": row["locale"],
        "placeholderParity": "exact", "markupParity": "exact",
        "protectedLiteralsPreserved": True if row["sourceIndex"] == 908 else None,
    })
assert len(parity_rows) == 240
arabic_plural = next(r for r in cross_rows if r["sourceIndex"] == 915 and r["locale"] == "ar")
assert set(arabic_plural["crossReviewTarget"]) == {"zero", "one", "two", "few", "many", "other"}

# Store the caller and catalog boundary checks in review-friendly form.
caller_checks = caller_verifications + [{
    "sourceIndex": 909, "windowLabel": 910, "sourceId": gap_source,
    "locale": None, "kind": "catalog-only-gap", "productionCallerMatches": production_matches,
    "verifiedNoExactProductionLiteralCaller": True,
}]
dump_jsonl("cross-review-ledger.jsonl", cross_rows)
dump_jsonl("source-boundary-caller-checks.jsonl", caller_checks + boundary_checks)
dump_jsonl("same-locale-register-pins.jsonl", register_rows)
dump_json("crossreview-findings.json", {
    "additionalCorrections": [f for f in extra_findings if f["kind"] == "additional-correction"],
    "primaryDispositionRevision": [f for f in extra_findings if f["kind"] == "revise-primary-proposal"],
    "terminologyWatch": [{
        "sourceIndex": 910, "windowLabel": 911, "sourceId": "Controller", "locale": "de",
        "currentTarget": catalogs["de"]["Controller"], "disposition": "retain-current-with-review-note",
        "confidence": "low",
        "detail": "Regler can denote a regulator/control device and may be awkward for a software relay connection label. The evidence is insufficient to prescribe a better German term, so the cell remains unchanged pending fluent review.",
    }],
    "holds": [{
        "sourceIndex": 909, "windowLabel": 910, "sourceId": gap_source,
        "locale": locale, "disposition": "hold",
        "detail": "No exact source-literal production caller is present at this head; keep the current catalog value without semantic approval.",
    } for locale in LOCALES],
})
dump_json("input-attestation.json", {
    "repository": "snapetech-org/slskR", "pullRequest": 204,
    "reviewWindow": "W903-W922", "primaryPacket": str(PRIMARY),
    "primarySumsFileSha256": sha((PRIMARY / "SHA256SUMS").read_bytes()),
    "primaryPacketChecksums": primary_sums,
    "livePullRequest": pr, "apiTree": api_tree, "remoteBranchHead": remote_head,
    "localHead": head, "localTree": tree, "branch": branch, "worktreeStatus": status,
    "catalogAttestations": catalog_attestations,
    "catalogKeyCount": len(shared_keys), "allLocaleKeysetsIdentical": True,
    "sourceCallerPinCount": len(caller_rows), "sourceCallerPinsVerified": len(caller_verifications),
    "catalogOnlyGapVerified": True, "boundaryPinCount": len(boundary_rows),
    "boundaryPinsVerified": len(boundary_checks), "previousWindowReadbacksVerified": len(prior_checks),
    "primaryCellCount": len(primary_rows), "primaryCellCurrentSourceAndTargetHashesVerified": True,
    "allInputArtifactsStayOutsideRepository": True,
    "nativeSpeakerApproval": False, "testsBuildScansCIOrBrowserRun": False,
    "attestedAtUtc": dt.datetime.now(dt.timezone.utc).isoformat(),
})

counts = collections.Counter(r["crossReviewDisposition"] for r in cross_rows)
summary = {
    "repository": "snapetech-org/slskR", "pullRequest": 204, "window": "W903-W922",
    "head": HEAD_EXPECTED, "tree": TREE_EXPECTED, "branch": BRANCH,
    "state": pr["state"], "isDraft": pr["isDraft"],
    "crossReviewedCells": len(cross_rows), "localeCount": len(LOCALES),
    "sourceCount": END - START + 1, "counts": dict(sorted(counts.items())),
    "primaryProposedCells": sum(r["primaryDisposition"].startswith("propose-") for r in cross_rows),
    "primaryProposalsAccepted": counts["accept-primary-correction"] + counts["accept-primary-refinement"],
    "primaryProposalsRevised": counts["revise-primary-proposal"],
    "primaryAcceptCurrentRetained": counts["retain-current"],
    "additionalCorrections": counts["additional-correction"],
    "primaryHoldsPreserved": counts["hold"],
    "recommendedChanges": sum(r["crossReviewTarget"] != r["currentTarget"] for r in cross_rows),
    "placeholderMismatches": 0, "markupMismatches": 0, "protectedLiteralMismatches": 0,
    "allArabicPluralCategoriesPresent": True, "arabicPluralPlaceholderParity": "exact",
    "boundaryReadbacksVerified": len(boundary_checks) + len(prior_checks),
    "callerPinsVerified": len(caller_verifications), "catalogOnlySourcesHeld": 1,
    "catalogsReattested": len(catalog_attestations), "catalogKeyCount": len(shared_keys),
    "findings": extra_findings + [{
        "kind": "terminology-watch", "sourceIndex": 910, "locale": "de",
        "detail": "Regler for software Controller is retained with low confidence pending fluent German review."
    }],
    "nativeSpeakerApproval": False, "headedBrowserAcceptance": False,
    "testsBuildScansCiOrBrowserRun": False, "repositoryModified": False,
}
assert sum(counts.values()) == 240
assert counts["hold"] == 12
assert counts["additional-correction"] == 6
assert counts["revise-primary-proposal"] == 1
assert summary["recommendedChanges"] == 42
dump_json("summary.json", summary)

readme = f"""# slskR PR #204 independent cross-review — W903–W922

This packet independently cross-reviews all 240 decisions in the primary packet at {PRIMARY}, against open draft PR #204 head {HEAD_EXPECTED} and tree {TREE_EXPECTED}. The live PR head, API tree, remote branch, local worktree, all twelve catalog objects, current-target hashes, source hashes, caller pins, and prior/forward boundary readbacks were reattested.

The ledger has one row per source-locale cell. It accepts {counts['accept-primary-correction'] + counts['accept-primary-refinement']} of the 37 primary proposals, revises the Spanish progress-instruction formality proposal to retain the existing tú voice, retains {counts['retain-current']} primary accept-current cells, adds six corrections, and preserves all twelve catalog-only holds. This yields {summary['recommendedChanges']} recommended value changes across the window.

The six additional corrections are two German copied-export toasts whose current wording makes the play count rather than the export the object, and four Spanish/French/Brazilian Portuguese/Vietnamese cooldown-unit labels that remain inconsistent with their paired wait-interval labels. The Spanish progress proposal was revised because the same catalog uses tú imperatives in comparable user instructions. German Regler for the Agent-mode software Controller remains unchanged as a low-confidence terminology watch.

The 12 translations of “Control the local review panel shown with song search results.” remain held. No exact production source-literal caller exists at this head. The Simplified and Traditional Chinese versions add “below,” which is not stated in the English source, but the missing caller prevents a safe interpretation of intended placement and control semantics.

All final targets preserve placeholders and markup; URL remains present; the Arabic plural object retains zero/one/two/few/many/other with exact placeholder parity. This is static machine-assisted review with moderate overall confidence. It is not native-speaker approval or browser acceptance. No repo files changed; no tests, builds, scans, CI jobs, or browser actions ran.

## Packet files

- cross-review-ledger.jsonl — all 240 cross-review dispositions and exact hashes.
- source-boundary-caller-checks.jsonl — caller-pin, catalog-gap, and boundary readback checks.
- same-locale-register-pins.jsonl — direct Spanish catalog examples supporting the register decision.
- crossreview-findings.json — additional corrections, proposal revision, terminology watch, and preserved holds.
- input-attestation.json — live PR, Git, catalog, primary packet, and hash verification evidence.
- summary.json — disposition counts and findings.
- build_crossreview.py — reproducible packet builder.
- SHA256SUMS — checksums for every packet file except this checksum list.

Confidence is moderate overall; the German terminology watch is low confidence. No native-speaker approval is claimed.
"""
(OUT / "README.md").write_text(readme)
# Seal every deliverable file. SHA256SUMS does not hash itself.
files = sorted(p for p in OUT.iterdir() if p.is_file() and p.name != "SHA256SUMS")
(OUT / "SHA256SUMS").write_text("".join(f"{sha(p.read_bytes())}  {p.name}\n" for p in files))
print(json.dumps({
    "out": str(OUT), "crossReviewedCells": len(cross_rows), "counts": dict(counts),
    "recommendedChanges": summary["recommendedChanges"],
    "inputChecksums": primary_sums["exitCode"], "liveHead": pr["headRefOid"],
    "catalogs": len(catalog_attestations), "callerPins": len(caller_verifications),
    "boundaryChecks": len(boundary_checks), "files": len(files) + 1,
}, ensure_ascii=False))
