#!/usr/bin/env python3
"""Reconcile pinned slskR W1503-W1522 primary and clean-blind ledgers."""
from collections import Counter
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "cross-review"
PRIMARY = ROOT / "primary-review"
BLIND = ROOT / "independent-clean-blind-review" / "output"
INPUT = ROOT / "candidate-free-input"
HEAD = "a7d00cd97602c5910800330190817fcada008162"
TREE = "2d0a051348394e809ffc3a1fdbfccd20ba8af283"
LOCALES = ["es", "zh-Hans", "hi", "de", "ja", "fr", "pt-BR", "ar", "ko", "zh-Hant", "vi", "id"]

DECISIONS = {
    (1503, "de"): ("refinement", "Status des Bibliotheks-Gesundheitsscans konnte nicht überprüft werden", "root-adjudication", "The exact catalog translates Library Health Scan as Bibliotheks-Gesundheitsscan. The current wording loses that health-scan meaning; this keeps the established term and the existing concise error style."),
    (1503, "fr"): ("refinement", "Impossible de vérifier le statut de l’analyse de santé de la bibliothèque", "root-adjudication", "The exact catalog uses Analyse de l'état de la bibliothèque for Library Health Scan. This wording restores the missing health-analysis meaning while retaining the operation of checking scan status."),
    (1514, "de"): ("refinement", "SongID-Forensikmatrix konnte nicht kopiert werden", "root-adjudication", "The adjacent exact-head label Forensische SongID-Matrix JSON kopieren preserves SongID as the named feature. Use the same product spelling here and keep the forensic-matrix meaning."),
    (1514, "fr"): ("refinement", "Impossible de copier la matrice d’analyse forensique SongID", "root-adjudication", "The parallel exact-head copy label uses matrice d’analyse forensique for the forensic matrix. The current value omits forensique; this restores that meaning and preserves SongID."),
    (1514, "vi"): ("refinement", "Không thể sao chép ma trận pháp chứng SongID", "root-adjudication", "Both reviewers identify that the current analysis matrix loses the forensic meaning. This adopts their shared terminology, preserves SongID, and follows the catalog's no-terminal-period style."),
    (1517, "de"): ("correction", "Reparaturauftrag konnte nicht erstellt werden", "root-adjudication", "The caller creates a library-health fix job. Reparaturauftrag describes that repair job; Korrekturauftrag suggests a correction assignment. The catalog's error strings omit a terminal period."),
    (1517, "fr"): ("correction", "Impossible de créer la tâche de réparation", "root-adjudication", "The caller creates a library-health fix job. Tâche de réparation describes repair work; tâche de correction suggests a correction task. The catalog's error strings omit a terminal period."),
    (1517, "hi"): ("correction", "मरम्मत कार्य नहीं बनाया जा सका", "root-adjudication", "The caller creates a library-health fix job. मरम्मत कार्य describes repair work, whereas the current समाधान कार्य reads as a solution task. The catalog's error strings omit a terminal danda."),
    (1517, "ja"): ("correction", "修復ジョブを作成できませんでした", "root-adjudication", "The caller creates a library-health fix job. 修復ジョブ describes a repair job; the current 修正ジョブ can read as a correction job. The catalog's error strings omit terminal punctuation."),
    (1517, "ko"): ("correction", "복구 작업을 만들지 못했습니다", "root-adjudication", "The caller creates a library-health fix job. 복구 작업 describes a recovery or repair job; the current 수정 작업 can read as a modification task. The catalog's error strings omit terminal punctuation."),
    (1517, "pt-BR"): ("correction", "Não foi possível criar a tarefa de reparo", "root-adjudication", "The caller creates a library-health fix job. Tarefa de reparo describes repair work; tarefa de correção suggests a correction task. The catalog's error strings omit a terminal period."),
    (1520, "ar"): ("correction", "تعذر إنشاء Pod: {error}", "root-adjudication", "The exact Arabic catalog preserves Pod in sibling content-linking, membership, and channel labels. The source component creates a content-linked discussion Pod; الحاوية adds a container interpretation. Preserve the product entity and the {error} placeholder."),
}


def read_jsonl(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def sha(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


primary = read_jsonl(PRIMARY / "primary-ledger.jsonl")
blind = read_jsonl(BLIND / "blind-ledger.jsonl")
current = read_jsonl(INPUT / "current-target-cells.jsonl")
assert len(primary) == len(blind) == len(current) == 240
pmap = {(r["position"], r["locale"]): r for r in primary}
bmap = {(r["position"], r["locale"]): r for r in blind}
cmap = {(r["position"], r["locale"]): r for r in current}
assert set(pmap) == set(bmap) == set(cmap)
assert len(pmap) == 240

ledger = []
for key in sorted(pmap, key=lambda x: (x[0], LOCALES.index(x[1]))):
    p, b, c = pmap[key], bmap[key], cmap[key]
    assert p["currentTarget"] == b["currentTarget"] == c["currentTarget"]
    assert p["sourceKey"] == b["sourceKey"] == c["sourceKey"]
    assert p["pins"]["currentTargetSha256"] == b["currentTargetSha256"] == c["currentTargetSha256"]
    assert p["pins"]["sourceKeySha256"] == b["sourceKeySha256"] == c["sourceKeySha256"]
    assert p["pins"]["sourceContextSha256"] == b["callerContextSha256"]
    position, locale = key
    record = {
        "repository": "snapetech-org/slskR",
        "pullRequest": 204,
        "head": HEAD,
        "tree": TREE,
        "crossReviewer": "root",
        "position": position,
        "locale": locale,
        "sourceId": p["sourceId"],
        "sourceSha256": p["pins"]["sourceKeySha256"],
        "callerContextSha256": p["pins"]["sourceContextSha256"],
        "catalogPath": p["pins"]["catalogPath"],
        "catalogGitBlob": p["pins"]["catalogGitBlob"],
        "catalogSha256": p["pins"]["catalogFileSha256"],
        "currentTargetSha256": p["pins"]["currentTargetSha256"],
        "primaryDisposition": p["disposition"],
        "primaryProposal": p["proposedTarget"],
        "primaryRationale": p["rationale"],
        "independentBlindDisposition": b["disposition"],
        "independentBlindProposal": b["proposedTarget"],
        "independentBlindRationale": b["rationale"],
    }
    if key == (1520, "ar"):
        classification, selected, selected_from, rationale = DECISIONS[key]
        assert b["disposition"] == "hold" and p["disposition"] == "accept-current"
        record.update({
            "crossDisposition": classification,
            "action": "update",
            "selectedFrom": selected_from,
            "selectedTarget": selected,
            "selectedTargetSha256": sha(selected),
            "rationale": rationale,
        })
    elif key in DECISIONS:
        classification, selected, selected_from, rationale = DECISIONS[key]
        record.update({
            "crossDisposition": classification,
            "action": "update",
            "selectedFrom": selected_from,
            "selectedTarget": selected,
            "selectedTargetSha256": sha(selected),
            "rationale": rationale,
        })
    elif b["disposition"] == "hold":
        # Keep unresolved rows text-free, including source and target text.
        record = {
            "repository": "snapetech-org/slskR",
            "pullRequest": 204,
            "head": HEAD,
            "tree": TREE,
            "crossReviewer": "root",
            "position": position,
            "locale": locale,
            "sourceId": p["sourceId"],
            "sourceSha256": p["pins"]["sourceKeySha256"],
            "callerContextSha256": p["pins"]["sourceContextSha256"],
            "catalogPath": p["pins"]["catalogPath"],
            "catalogGitBlob": p["pins"]["catalogGitBlob"],
            "catalogSha256": p["pins"]["catalogFileSha256"],
            "currentTargetSha256": p["pins"]["currentTargetSha256"],
            "primaryDisposition": p["disposition"],
            "independentBlindDisposition": b["disposition"],
            "crossDisposition": "hold",
            "action": "hold",
            "selectedTargetSha256": None,
            "rationale": "The pinned caller does not establish the product meaning of this Arabic pod term; retain the current value without proposing target text.",
        }
    else:
        assert p["disposition"] == "accept-current" and b["disposition"] == "accept-current"
        record.update({
            "crossDisposition": "accept-current",
            "action": "no-op",
            "selectedFrom": "current",
            "currentTarget": p["currentTarget"],
            "selectedTarget": p["currentTarget"],
            "selectedTargetSha256": p["pins"]["currentTargetSha256"],
            "rationale": "Both reviews accept the current value; no selected change is needed.",
        })
    if record["crossDisposition"] != "hold":
        record["sourceText"] = p["sourceKey"]
        record["sourceTextSha256"] = p["pins"]["sourceKeySha256"]
        record["currentTarget"] = p["currentTarget"]
        if record["action"] == "no-op":
            assert record["selectedTarget"] == record["currentTarget"]
        else:
            assert record["selectedTarget"] != record["currentTarget"]
        source_placeholders = re.findall(r"\{[^{}]+\}", p["sourceKey"])
        target_placeholders = re.findall(r"\{[^{}]+\}", record["selectedTarget"])
        assert source_placeholders == target_placeholders, (key, source_placeholders, target_placeholders)
        assert re.findall(r"<[^>]+>", p["sourceKey"]) == re.findall(r"<[^>]+>", record["selectedTarget"])
    ledger.append(record)

OUT.mkdir(parents=True, exist_ok=True)
with (OUT / "root-cross-ledger.jsonl").open("w", encoding="utf-8", newline="\n") as handle:
    for row in ledger:
        handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")

counts = Counter(row["crossDisposition"] for row in ledger)
actions = Counter(row["action"] for row in ledger)
selected_from = Counter(row.get("selectedFrom", "hold") for row in ledger)
primary_proposals = sum(row["disposition"] != "accept-current" for row in primary)
blind_proposals = sum(row["disposition"].startswith("propose-") for row in blind)
proposal_union = sum(
    pmap[k]["disposition"] != "accept-current" or bmap[k]["disposition"].startswith("propose-")
    for k in pmap
)
summary = {
    "artifact": "slskR PR #204 W1503-W1522 root cross-review",
    "repository": "snapetech-org/slskR",
    "pullRequest": 204,
    "head": HEAD,
    "tree": TREE,
    "window": "W1503-W1522",
    "cells": len(ledger),
    "sourceIds": 20,
    "localeCount": 12,
    "primaryProposals": primary_proposals,
    "independentBlindProposals": blind_proposals,
    "proposalUnion": proposal_union,
    "selectedUpdates": actions["update"],
    "selectedDispositionCounts": dict(counts),
    "selectedFromCounts": dict(selected_from),
    "textFreeHolds": actions["hold"],
    "placeholderAndMarkupChecks": "PASS for every selected target",
    "primaryLedgerSha256": hashlib.sha256((PRIMARY / "primary-ledger.jsonl").read_bytes()).hexdigest(),
    "independentBlindLedgerSha256": hashlib.sha256((BLIND / "blind-ledger.jsonl").read_bytes()).hexdigest(),
    "candidateFreeManifestSha256": hashlib.sha256((INPUT / "manifest.json").read_bytes()).hexdigest(),
    "nativeSpeakerSignoff": "not claimed",
    "stateMachineValidation": "not performed",
    "exactHeadBrowserAcceptance": "not performed; exact-head deployment lookup returned zero",
    "catalogApplication": "pending",
}
write_json(OUT / "summary.json", summary)

attestation = {
    "repository": "snapetech-org/slskR",
    "pullRequest": 204,
    "state": "OPEN",
    "isDraft": True,
    "head": HEAD,
    "tree": TREE,
    "baseBranch": "main",
    "baseSha": "2a2b188f10b9460a15bc6d5c34e406b0193d51ba",
    "branch": "codex/slskr-l10n-audit-20261030",
    "exactHeadDeployments": 0,
    "actionsRunsForHead": 0,
}
write_json(OUT / "PR-attestation.json", attestation)

readme = """# slskR PR #204 W1503–W1522 root cross-review\n\nPinned head: `a7d00cd97602c5910800330190817fcada008162`\nPinned tree: `2d0a051348394e809ffc3a1fdbfccd20ba8af283`\n\nThe root cross-review reconciles 240 cells across 20 source IDs and 12 locales. It selects 12 catalog updates: 7 corrections and 5 refinements; 228 cells remain current, and the blind Arabic hold is resolved. The primary, independent clean-blind, and candidate-free inputs are separately checksummed and pinned to the same PR head.\n\nThe cross-review adopts the independent repair-job wording where the current target calls it a correction or solution task. It also uses exact-head sibling catalog terminology to refine the health-scan and SongID forensic-matrix messages. For the Arabic pod error, the pinned locale catalog consistently treats Pod as the app's content-linked discussion entity, so the catalog selects `Pod` and removes the misleading container interpretation while retaining `{error}`. Exact sibling terms, catalog blobs, file hashes, and value hashes are in adjudication-context.json.\n\nPlaceholder and markup checks pass for each selected target. No state-machine validation, browser acceptance, or qualified native-speaker approval is claimed. Exact-head GitHub deployment count is zero.\n"""
(OUT / "README.md").write_text(readme, encoding="utf-8")

term_context = {
    "repository": "snapetech-org/slskR",
    "pullRequest": 204,
    "head": HEAD,
    "tree": TREE,
    "purpose": "Exact-head sibling catalog wording used to adjudicate W1503, W1514, and W1520.",
    "catalogs": [
        {
            "locale": "de",
            "path": "web/src/lib/locales/ui-labels.de.json",
            "gitBlob": "b2db6dad028b99809b0d2dc9eb443ed75b01eaae",
            "fileSha256": "08f9e79146cb99f718cbe0d4bf1b8a3f89aa915742fdcc18f531b6ff52367fdf",
            "terms": [
                {"source": "Library Health Scan", "target": "Bibliotheks-Gesundheitsscan", "targetSha256": "1263632a3541e2f46b8bfc8ce3832d584fa359a9ebfb9786ccf52f26200b8988"},
                {"source": "Copy SongID forensic matrix JSON", "target": "Forensische SongID-Matrix JSON kopieren", "targetSha256": "1375c8a75b9be67983047dd1a093fbe154a17bf0bf525356b39d81ae7d892fb2"}
            ]
        },
        {
            "locale": "fr",
            "path": "web/src/lib/locales/ui-labels.fr.json",
            "gitBlob": "d5449bd06a0bf2d181a6f808bc2cc223c0e5eae0",
            "fileSha256": "e83512532420e600cf7db3099c0baed497cfe04894dfb49b6ce0fef514933394",
            "terms": [
                {"source": "Library Health Scan", "target": "Analyse de l'état de la bibliothèque", "targetSha256": "5ecd402585b18392945f8b72f241201c9388748dfac7ef31e6bd1c5b5c1430a6"},
                {"source": "Copy the complete forensic matrix JSON for this SongID run without changing ranking, downloads, or local files.", "target": "Copiez la matrice d’analyse forensique complète JSON pour cette exécution SongID, sans modifier le classement, les téléchargements ni les fichiers locaux.", "targetSha256": "07aa87700a860dcb50557a0a80d54b29d6c0d662620b31486d774214e79fbe90"}
            ]
        },
        {
            "locale": "ar",
            "path": "web/src/lib/locales/ui-labels.ar.json",
            "gitBlob": "24cb74a76c02dd12a5003f9d627f1a671f5e3d2f",
            "fileSha256": "35a4bf33898179e005fa07925174b1c5dfa0bf320faa295da536f2f8d57846af",
            "terms": [
                {"source": "Pod Content Linking", "target": "ربط محتوى البود", "targetSha256": "f9c590576b01d2085ce6d8c970ee841961db1ecece3f1eb6969fe8a29f6d3a36"},
                {"source": "Create Content-Linked Pod", "target": "إنشاء Pod مرتبط بالمحتوى", "targetSha256": "83f2d6bd5dd92dbec24535f63cc16d215e43f5487e0000006ee8824aa8d2c1dc"},
                {"source": "Can create content-linked pods", "target": "يمكن إنشاء Pods مرتبطة بالمحتوى", "targetSha256": "26db89c0e0b7b8957463e8445167b076e736f554a13fd3f08462162be3882681"},
                {"source": "Pod membership is required", "target": "عضوية Pod مطلوبة.", "targetSha256": "f8bd8ce91941a1d8a6974f72efbb94644d60e1b9bffcddb7b965e1b7debeddee"},
                {"source": "Failed to leave pod: {error}", "target": "تعذر مغادرة الـpod: {error}", "targetSha256": "d91581cb8656e3993d00a3fcdf96b52619e5dad6c4641353c5be3c0849cfcd82"}
            ]
        }
    ]
}
write_json(OUT / "adjudication-context.json", term_context)

