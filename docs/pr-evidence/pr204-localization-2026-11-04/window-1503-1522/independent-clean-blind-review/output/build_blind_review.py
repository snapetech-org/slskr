#!/usr/bin/env python3
"""Build an independent clean-blind review from the candidate-free packet only."""
import hashlib
import json
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "input" / "candidate-free-input"
OUT = ROOT / "output"

PROPOSALS = {
    (1503, "de"): ("propose-refinement", "Der Status der Gesundheitsprüfung der Bibliothek konnte nicht überprüft werden.", "The current wording omits the health-check aspect and reads as a generic library check; this restores the library health-check meaning."),
    (1503, "fr"): ("propose-refinement", "Impossible de vérifier l’état du contrôle de santé de la bibliothèque.", "The current wording omits the health-check aspect and can read as a general library analysis; this states that the library health check could not be verified."),
    (1514, "de"): ("propose-correction", "SongID-Forensikmatrix konnte nicht kopiert werden.", "The product identifier is SongID; splitting it as Song-ID changes the named tool. This keeps the identifier exact and retains the forensic-matrix meaning."),
    (1514, "fr"): ("propose-correction", "Impossible de copier la matrice forensique SongID.", "The current wording reduces forensic to general analysis; forensique preserves the source meaning and the SongID identifier."),
    (1514, "vi"): ("propose-correction", "Không thể sao chép ma trận pháp chứng SongID.", "The current wording says analysis matrix rather than forensic matrix; pháp chứng restores that distinction and preserves SongID."),
    (1517, "hi"): ("propose-correction", "मरम्मत कार्य नहीं बनाया जा सका।", "समाधान कार्य means a solution task; मरम्मत कार्य describes the repair or fix job in the pinned library-health caller."),
    (1517, "de"): ("propose-correction", "Der Reparaturauftrag konnte nicht erstellt werden.", "Korrekturauftrag suggests a correction assignment; Reparaturauftrag better matches a library-health fix job."),
    (1517, "ja"): ("propose-correction", "修復ジョブを作成できませんでした。", "修正ジョブ suggests a correction job; 修復ジョブ better conveys a repair job in the library-health context."),
    (1517, "fr"): ("propose-correction", "Impossible de créer la tâche de réparation.", "The current tâche de correction suggests a correction task; tâche de réparation better conveys the library-health fix job."),
    (1517, "pt-BR"): ("propose-correction", "Não foi possível criar a tarefa de reparo.", "The current tarefa de correção suggests a correction task; tarefa de reparo better conveys the library-health fix job."),
    (1517, "ko"): ("propose-correction", "복구 작업을 만들지 못했습니다.", "수정 작업 reads as a modification task; 복구 작업 better conveys the repair job in the library-health context."),
}

HOLD = {
    (1520, "ar"): "The caller identifies a named pod in a content-linking panel, but does not define whether this product entity is a container or another named object. The current الحاوية (pod) adds the container interpretation; hold this Arabic cell until the domain meaning is clear.",
}


def sha_bytes(raw):
    return hashlib.sha256(raw).hexdigest()


def sha_text(text):
    return sha_bytes(text.encode("utf-8"))


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def read_jsonl(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def tokens(text):
    placeholders = re.findall(r"\{[A-Za-z][A-Za-z0-9_]*\}", text)
    tags = re.findall(r"</?[A-Za-z][^>]*>", text)
    numbers = re.findall(r"(?<![A-Za-z])\d+(?:[.,]\d+)?%?(?![A-Za-z])", text)
    protected = []
    for match in re.finditer(r"(?<![A-Za-z0-9])(?:[A-Z]{2,}[A-Z0-9]*|ffmpeg|Chromaprint|Soulseek|Spotify|YouTube|Pushbullet|Matrix|WebSocket|OpenAI)(?![A-Za-z0-9])", text):
        if match.group(0) not in protected:
            protected.append(match.group(0))
    return {"placeholders": placeholders, "markupTags": tags, "numericTokens": numbers, "protectedLiterals": protected}


def rationale_for_accept():
    return "The current wording accurately conveys the source error in its pinned production context. Dynamic values, placeholders, and named product literals remain unchanged."


def main():
    cells = read_jsonl(INPUT / "current-target-cells.jsonl")
    contexts = {row["position"]: row for row in read_jsonl(INPUT / "source-contexts.jsonl")}
    manifest = json.loads((INPUT / "manifest.json").read_text(encoding="utf-8"))
    if len(cells) != 240 or manifest["cellCount"] != 240:
        raise SystemExit("candidate-free packet does not contain 240 cells")
    packet_hash = sha_bytes((INPUT / "SHA256SUMS.txt").read_bytes())
    manifest_hash = sha_bytes((INPUT / "manifest.json").read_bytes())
    ledger = []
    dispositions = Counter()
    proposed = Counter()
    for cell in cells:
        position, locale = cell["position"], cell["locale"]
        key = (position, locale)
        context = contexts[position]
        source = cell["sourceKey"]
        current = cell["currentTarget"]
        src_tokens = tokens(source)
        current_tokens = tokens(current)
        choice = PROPOSALS.get(key)
        hold = HOLD.get(key)
        if choice:
            disposition, target, rationale = choice
            reviewed = target
            confidence = "moderate"
        elif hold:
            disposition, target, reviewed = "hold", None, None
            rationale = hold
            confidence = "low"
        else:
            disposition, target, reviewed = "accept-current", None, current
            rationale = rationale_for_accept()
            confidence = "moderate"
        reviewed_tokens = tokens(reviewed) if reviewed is not None else None
        integrity = {}
        for name, required_name in (("placeholders", "placeholders"), ("markupTags", "markupTags"), ("numericTokens", "numericTokens"), ("protectedLiterals", "protectedLiterals")):
            required = src_tokens[required_name]
            current_items = current_tokens[name]
            reviewed_items = reviewed_tokens[name] if reviewed_tokens is not None else None
            current_match = current_items == required if name != "protectedLiterals" else all(x in current_items for x in required)
            reviewed_match = None if reviewed_items is None else (reviewed_items == required if name != "protectedLiterals" else all(x in reviewed_items for x in required))
            integrity[name] = {
                "required": required,
                "current": current_items,
                "reviewed": reviewed_items,
                "currentMatches": current_match,
                "reviewedMatches": reviewed_match,
            }
        row = {
            "schemaVersion": 1,
            "reviewPass": "independent-clean-blind",
            "repository": "snapetech-org/slskR",
            "pullRequest": 204,
            "head": manifest["head"],
            "tree": manifest["tree"],
            "position": position,
            "sourceKey": source,
            "sourceKeySha256": cell["sourceKeySha256"],
            "source": source,
            "sourceSha256": cell["sourceKeySha256"],
            "locale": locale,
            "catalogPath": cell["catalogPath"],
            "catalogGitBlob": cell["catalogGitBlob"],
            "catalogFileSha256": cell["catalogFileSha256"],
            "currentTarget": current,
            "currentTargetSha256": cell["currentTargetSha256"],
            "callerContextSha256": cell["sourceContextSha256"],
            "callerCount": cell["callerCount"],
            "callerRefs": context["callers"],
            "disposition": disposition,
            "proposedTarget": target,
            "reviewedTarget": reviewed,
            "reviewedTargetSha256": sha_text(reviewed) if reviewed is not None else None,
            "rationale": rationale,
            "confidence": confidence,
            "tokenIntegrity": integrity,
            "candidateFreeInputCellSha256": sha_bytes(canonical(cell)),
            "candidateFreePacketChecksumListSha256": packet_hash,
            "candidateFreeManifestSha256": manifest_hash,
            "reviewSource": "candidate-free source key, current locale value, exact pinned caller context, and localization runtime context only",
            "dynamicValueBoundary": "Named placeholders and user/API error values remain opaque and unchanged.",
            "stateMachineReview": "No state-machine behavior or state transition is inferred from this error-text review.",
            "nativeSpeakerApproval": "not claimed",
        }
        if disposition in ("propose-correction", "propose-refinement"):
            if target == current or not all(v["reviewedMatches"] is True for v in integrity.values()):
                raise SystemExit(f"invalid proposed target at {key}")
            proposed[disposition] += 1
        elif disposition == "accept-current":
            if not all(v["currentMatches"] is True for v in integrity.values()):
                raise SystemExit(f"accepted current target has token mismatch at {key}")
        elif disposition == "hold":
            if target is not None or reviewed is not None:
                raise SystemExit(f"held cell contains a target at {key}")
        ledger.append(row)
        dispositions[disposition] += 1

    if len(ledger) != 240 or sum(proposed.values()) != len(PROPOSALS) or len(HOLD) != 1:
        raise SystemExit("review is incomplete")
    OUT.mkdir(parents=True, exist_ok=True)
    ledger_path = OUT / "blind-ledger.jsonl"
    ledger_path.write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in ledger), encoding="utf-8")
    summary = {
        "artifact": "slskR PR #204 W1503-W1522 independent clean-blind semantic review",
        "repository": "snapetech-org/slskR",
        "pullRequest": 204,
        "head": manifest["head"],
        "tree": manifest["tree"],
        "window": "W1503-W1522",
        "cells": len(ledger),
        "sourceKeys": 20,
        "localeCount": 12,
        "dispositions": dict(sorted(dispositions.items())),
        "proposedTargets": sum(proposed.values()),
        "proposalCounts": dict(sorted(proposed.items())),
        "heldCells": len(HOLD),
        "heldCellsTextFree": True,
        "localeOrder": manifest["localeOrder"],
        "candidateFreePacketChecksumListSha256": packet_hash,
        "candidateFreeManifestSha256": manifest_hash,
        "nativeSpeakerApproval": "not claimed",
        "stateMachineValidation": "not performed; this review only judges fixed error text in pinned callers",
        "browserAcceptance": "not claimed",
    }
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (OUT / "README.md").write_text(
        "# slskR PR #204 W1503–W1522 independent clean-blind review\n\n"
        f"Pinned head: {manifest['head']}\nPinned tree: {manifest['tree']}\n\n"
        "The reviewer used only the verified candidate-free packet: current locale values, source keys, pinned caller contexts, and localization runtime context. No primary or cross-review material was consulted.\n\n"
        f"This review covers {len(ledger)} cells across 20 source keys and 12 locales. It records {sum(proposed.values())} proposed corrections/refinements and {len(HOLD)} semantic hold. All current and proposed token checks are included in the ledger. Dynamic error values remain opaque; this review does not validate state-machine behavior. Native-speaker signoff is not claimed.\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
