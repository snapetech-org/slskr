#!/usr/bin/env python3
"""Verify slskR PR #204 W1503-W1522 independent blind review."""
import hashlib
import json
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "input" / "candidate-free-input"
OUT = ROOT / "output"
EXPECTED_HEAD = "a7d00cd97602c5910800330190817fcada008162"
EXPECTED_TREE = "2d0a051348394e809ffc3a1fdbfccd20ba8af283"
EXPECTED = {
    (1503, "de"): "Der Status der Gesundheitsprüfung der Bibliothek konnte nicht überprüft werden.",
    (1503, "fr"): "Impossible de vérifier l’état du contrôle de santé de la bibliothèque.",
    (1514, "de"): "SongID-Forensikmatrix konnte nicht kopiert werden.",
    (1514, "fr"): "Impossible de copier la matrice forensique SongID.",
    (1514, "vi"): "Không thể sao chép ma trận pháp chứng SongID.",
    (1517, "hi"): "मरम्मत कार्य नहीं बनाया जा सका।",
    (1517, "de"): "Der Reparaturauftrag konnte nicht erstellt werden.",
    (1517, "ja"): "修復ジョブを作成できませんでした。",
    (1517, "fr"): "Impossible de créer la tâche de réparation.",
    (1517, "pt-BR"): "Não foi possível criar a tarefa de reparo.",
    (1517, "ko"): "복구 작업을 만들지 못했습니다.",
}
HOLD = (1520, "ar")


def sha_bytes(raw):
    return hashlib.sha256(raw).hexdigest()


def sha_text(text):
    return sha_bytes(text.encode("utf-8"))


def canon(value):
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


def run(args, cwd):
    result = subprocess.run(args, cwd=cwd, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    if result.returncode:
        raise ValueError("command failed: " + " ".join(args) + "\n" + result.stdout)
    return result.stdout


def main():
    run([sys.executable, str(INPUT / "verify-candidate-free.py")], INPUT)
    run(["sha256sum", "-c", "SHA256SUMS.txt"], INPUT)
    manifest = json.loads((INPUT / "manifest.json").read_text(encoding="utf-8"))
    if manifest["head"] != EXPECTED_HEAD or manifest["tree"] != EXPECTED_TREE or manifest["cellCount"] != 240:
        raise ValueError("candidate-free packet pins or scope differ")
    cells = read_jsonl(INPUT / "current-target-cells.jsonl")
    contexts = {row["position"]: row for row in read_jsonl(INPUT / "source-contexts.jsonl")}
    ledger = read_jsonl(OUT / "blind-ledger.jsonl")
    key = lambda row: (row["position"], row["locale"])
    cell_map = {key(row): row for row in cells}
    review_map = {key(row): row for row in ledger}
    if len(cell_map) != 240 or len(review_map) != 240 or set(cell_map) != set(review_map):
        raise ValueError("blind ledger does not contain the exact 240 candidate-free cells")
    packet_hash = sha_bytes((INPUT / "SHA256SUMS.txt").read_bytes())
    manifest_hash = sha_bytes((INPUT / "manifest.json").read_bytes())
    counts = Counter()
    for k in sorted(cell_map):
        cell = cell_map[k]
        row = review_map[k]
        source = cell["sourceKey"]
        current = cell["currentTarget"]
        expected_tokens = tokens(source)
        actual = row["disposition"]
        if row["head"] != EXPECTED_HEAD or row["tree"] != EXPECTED_TREE:
            raise ValueError(f"review pin mismatch: {k}")
        for field, expected_value in (("sourceKey", source), ("sourceKeySha256", cell["sourceKeySha256"]), ("source", source), ("sourceSha256", cell["sourceKeySha256"]), ("locale", cell["locale"]), ("catalogPath", cell["catalogPath"]), ("catalogGitBlob", cell["catalogGitBlob"]), ("catalogFileSha256", cell["catalogFileSha256"]), ("currentTarget", current), ("currentTargetSha256", cell["currentTargetSha256"]), ("callerContextSha256", cell["sourceContextSha256"]), ("callerCount", cell["callerCount"])):
            if row[field] != expected_value:
                raise ValueError(f"candidate-free value mismatch: {k} {field}")
        context = contexts[cell["position"]]
        if row["callerRefs"] != context["callers"]:
            raise ValueError(f"caller reference mismatch: {k}")
        if row["candidateFreeInputCellSha256"] != sha_bytes(canon(cell)) or row["candidateFreePacketChecksumListSha256"] != packet_hash or row["candidateFreeManifestSha256"] != manifest_hash:
            raise ValueError(f"candidate-free evidence hash mismatch: {k}")
        if row["reviewPass"] != "independent-clean-blind" or row["nativeSpeakerApproval"] != "not claimed":
            raise ValueError(f"review provenance mismatch: {k}")

        if k in EXPECTED:
            disposition = "propose-refinement" if k[0] == 1503 else "propose-correction"
            selected = EXPECTED[k]
            if actual != disposition or row["proposedTarget"] != selected or row["reviewedTarget"] != selected:
                raise ValueError(f"proposal mismatch: {k}")
        elif k == HOLD:
            if actual != "hold" or row["proposedTarget"] is not None or row["reviewedTarget"] is not None:
                raise ValueError("held cell contains a proposed/reviewed target")
        else:
            if actual != "accept-current" or row["proposedTarget"] is not None or row["reviewedTarget"] != current:
                raise ValueError(f"unexpected proposal or disposition: {k}")

        reviewed = row["reviewedTarget"]
        reviewed_tokens = tokens(reviewed) if reviewed is not None else None
        if row["tokenIntegrity"] != {
            "placeholders": {"required": expected_tokens["placeholders"], "current": tokens(current)["placeholders"], "reviewed": reviewed_tokens["placeholders"] if reviewed_tokens else None, "currentMatches": tokens(current)["placeholders"] == expected_tokens["placeholders"], "reviewedMatches": None if reviewed_tokens is None else reviewed_tokens["placeholders"] == expected_tokens["placeholders"]},
            "markupTags": {"required": expected_tokens["markupTags"], "current": tokens(current)["markupTags"], "reviewed": reviewed_tokens["markupTags"] if reviewed_tokens else None, "currentMatches": tokens(current)["markupTags"] == expected_tokens["markupTags"], "reviewedMatches": None if reviewed_tokens is None else reviewed_tokens["markupTags"] == expected_tokens["markupTags"]},
            "numericTokens": {"required": expected_tokens["numericTokens"], "current": tokens(current)["numericTokens"], "reviewed": reviewed_tokens["numericTokens"] if reviewed_tokens else None, "currentMatches": tokens(current)["numericTokens"] == expected_tokens["numericTokens"], "reviewedMatches": None if reviewed_tokens is None else reviewed_tokens["numericTokens"] == expected_tokens["numericTokens"]},
            "protectedLiterals": {"required": expected_tokens["protectedLiterals"], "current": tokens(current)["protectedLiterals"], "reviewed": reviewed_tokens["protectedLiterals"] if reviewed_tokens else None, "currentMatches": all(x in tokens(current)["protectedLiterals"] for x in expected_tokens["protectedLiterals"]), "reviewedMatches": None if reviewed_tokens is None else all(x in reviewed_tokens["protectedLiterals"] for x in expected_tokens["protectedLiterals"])},
        }:
            raise ValueError(f"token-integrity record mismatch: {k}")
        if reviewed_tokens is not None:
            if not all(row["tokenIntegrity"][name]["reviewedMatches"] for name in row["tokenIntegrity"]):
                raise ValueError(f"reviewed target fails token integrity: {k}")
        counts[actual] += 1

    summary = json.loads((OUT / "summary.json").read_text(encoding="utf-8"))
    if summary["head"] != EXPECTED_HEAD or summary["tree"] != EXPECTED_TREE or summary["cells"] != 240 or summary["dispositions"] != dict(sorted(counts.items())):
        raise ValueError("summary does not match the reviewed ledger")
    if (OUT / "README.md").read_text(encoding="utf-8").find(EXPECTED_HEAD) < 0:
        raise ValueError("README is missing the exact head")
    print(json.dumps({"result":"PASS","head":EXPECTED_HEAD,"tree":EXPECTED_TREE,"cells":len(ledger),"dispositions":dict(sorted(counts.items())),"proposals":len(EXPECTED),"holds":1,"tokenMismatches":0,"nativeSpeakerApproval":"not claimed"},ensure_ascii=False,sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        raise SystemExit(1)
