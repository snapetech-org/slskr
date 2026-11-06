#!/usr/bin/env python3
import argparse
import collections
import hashlib
import json
import pathlib
import re
import subprocess

DEFAULT_INPUT = pathlib.Path("/home/keith/Documents/code/task-scratch/slskr-pr204-next-candidatefree-20261103/blind-input")
OUT = pathlib.Path(__file__).resolve().parent
HEAD = "281c39ec0cdb3677d7d523b7c4f0cd0d52bbf14c"
TREE = "777b234b1aa3cb7a2c9fd560b2c0fecc4e7fe49d"
LOCALES = ["es", "zh-Hans", "hi", "de", "ja", "fr", "pt-BR", "ar", "ko", "zh-Hant", "vi", "id"]
PROTECTED = {
    1366: ["ContentID"],
    1367: ["Library Health"],
    1370: ["slskr"],
    1372: ["ID"],
    1375: ["/music", "C:\\Music"],
}

def sha(data):
    return hashlib.sha256(data).hexdigest()

def sha_file(path):
    return sha(path.read_bytes())

def read_jsonl(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]

def run(args, cwd):
    return subprocess.run(args, cwd=cwd, check=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT).stdout.strip()

def token_checks(source, translation, protected, is_hold=False):
    if is_hold:
        return {
            "placeholders": {"source": [], "selected": None, "status": "not-applicable-held", "pass": True},
            "markup": {"source": [], "selected": None, "status": "not-applicable-held", "pass": True},
            "numeric": {"source": [], "selected": None, "status": "not-applicable-held", "pass": True},
            "protectedLiterals": {"source": protected, "selected": None, "status": "not-applicable-held", "pass": True},
            "allPass": True,
        }
    placeholders_source = re.findall(r"\{[^{}]*\}", source)
    placeholders_target = re.findall(r"\{[^{}]*\}", translation)
    markup_source = re.findall(r"</?[A-Za-z][^>]*>", source)
    markup_target = re.findall(r"</?[A-Za-z][^>]*>", translation)
    numeric_source = re.findall(r"(?<![A-Za-z])\d[\d,]*(?:\.\d+)?(?![A-Za-z])", source)
    numeric_target = re.findall(r"(?<![A-Za-z])\d[\d,]*(?:\.\d+)?(?![A-Za-z])", translation)
    ph_ok = sorted(placeholders_source) == sorted(placeholders_target)
    markup_ok = sorted(markup_source) == sorted(markup_target)
    numeric_ok = sorted(numeric_source) == sorted(numeric_target)
    protected_ok = all(translation.count(token) >= source.count(token) for token in protected)
    result = {
        "placeholders": {"source": placeholders_source, "selected": placeholders_target, "pass": ph_ok},
        "markup": {"source": markup_source, "selected": markup_target, "pass": markup_ok},
        "numeric": {"source": numeric_source, "selected": numeric_target, "pass": numeric_ok},
        "protectedLiterals": {"source": protected, "selected": [token for token in protected if translation.count(token) >= source.count(token)], "pass": protected_ok},
    }
    result["allPass"] = all(v["pass"] for v in result.values() if isinstance(v, dict))
    return result

def verify(input_dir):
    manifest = json.loads((OUT / "manifest.json").read_text())
    summary = json.loads((OUT / "summary.json").read_text())
    verification = json.loads((OUT / "verification.json").read_text())
    if manifest["head"] != HEAD or manifest["tree"] != TREE:
        raise SystemExit("Output head/tree pin mismatch")
    if manifest["candidateCatalogAccessed"] or manifest["candidateTranslationsAccessed"] or manifest["priorReviewsAccessed"] or manifest["repositoryWorktreeAccessed"]:
        raise SystemExit("Blind isolation metadata mismatch")
    expected_output_files = {"README.md", "build_blind_review.py", "coherence-review.json", "sealed-translation-ledger.jsonl", "summary.json", "verification.json", "verify_blind_review.py"}
    if {x["path"] for x in manifest["files"]} != expected_output_files:
        raise SystemExit("Output manifest file list mismatch")
    for entry in manifest["files"]:
        p = OUT / entry["path"]
        if not p.is_file() or p.stat().st_size != entry["bytes"] or sha_file(p) != entry["sha256"]:
            raise SystemExit(f"Output file hash/size mismatch: {entry['path']}")
    run(["sha256sum", "-c", "SHA256SUMS.txt"], OUT)
    run(["sha256sum", "-c", "SHA256SUMS.txt"], input_dir)
    input_result = json.loads(run(["python3", "verify-blind-input.py"], input_dir))
    if input_result.get("result") != "PASS" or input_result["head"] != HEAD or input_result["tree"] != TREE or input_result["promptCount"] != 240:
        raise SystemExit("Blind input verifier failed")
    for field, path in [
        ("blindInputManifestSha256", input_dir / "manifest.json"),
        ("blindInputChecksumListSha256", input_dir / "SHA256SUMS.txt"),
        ("promptsSha256", input_dir / "prompts.jsonl"),
        ("sourceContextsSha256", input_dir / "source-contexts.jsonl"),
    ]:
        if sha_file(path) != manifest[field]:
            raise SystemExit(f"Input hash mismatch: {field}")
    prompts = read_jsonl(input_dir / "prompts.jsonl")
    contexts = {r["position"]: r for r in read_jsonl(input_dir / "source-contexts.jsonl")}
    decisions = read_jsonl(OUT / "sealed-translation-ledger.jsonl")
    if len(prompts) != 240 or len(contexts) != 20 or len(decisions) != 240:
        raise SystemExit("Expected 240 prompt/output rows and 20 context records")
    if [(r["position"], r["locale"]) for r in prompts] != [(r["position"], r["locale"]) for r in decisions]:
        raise SystemExit("Decision ledger order mismatch")
    if len({(r["position"], r["locale"]) for r in decisions}) != 240:
        raise SystemExit("Duplicate decision rows")
    disposition_counts = collections.Counter()
    per_locale = collections.defaultdict(collections.Counter)
    translation_by_key = {}
    for prompt, decision in zip(prompts, decisions):
        pos, locale = prompt["position"], prompt["locale"]
        context = contexts[pos]
        if decision["schema"] != "slskr-blind-translation-review/v1" or decision["repository"] != "snapetech-org/slskR" or decision["pullRequest"] != 204 or decision["head"] != HEAD or decision["tree"] != TREE:
            raise SystemExit("Decision provenance mismatch")
        if decision["prompt"] != prompt or decision["sourceContext"] != context:
            raise SystemExit(f"Source/caller evidence mismatch at {pos} {locale}")
        if prompt["sourceKey"] != context["sourceKey"] or prompt["sourceKeySha256"] != context["sourceKeySha256"] or prompt["sourceContextRef"]["sourceContextSha256"] != context["callerContextSha256"]:
            raise SystemExit(f"Source context pin mismatch at {pos} {locale}")
        if prompt["sourceContextRef"]["callerCount"] != context["productionCallerCount"] or len(prompt["callerRefs"]) != context["productionCallerCount"]:
            raise SystemExit(f"Caller count mismatch at {pos} {locale}")
        for ref, caller in zip(prompt["callerRefs"], context["callers"]):
            for name, value in ref.items():
                if caller.get(name) != value:
                    raise SystemExit(f"Caller reference mismatch at {pos} {locale}: {name}")
        callerless = pos == 1376
        if decision["callerless"] is not callerless:
            raise SystemExit(f"Callerless flag mismatch at {pos} {locale}")
        if callerless and (context["productionCallerCount"] != 0 or context["callers"] or prompt["callerRefs"]):
            raise SystemExit("Rank 1376 must remain callerless")
        expected = "hold" if callerless else "propose"
        d = decision["decision"]
        if d["disposition"] != expected:
            raise SystemExit(f"Unexpected proposal/hold boundary at {pos} {locale}")
        if callerless:
            if d["translation"] is not None or d["confidence"] != "low" or not d["rationale"].strip():
                raise SystemExit(f"Callerless hold is incomplete at {pos} {locale}")
        else:
            if not isinstance(d["translation"], str) or not d["translation"].strip() or not d["rationale"].strip() or d["confidence"] not in ("high", "moderate", "low"):
                raise SystemExit(f"Proposal is incomplete at {pos} {locale}")
        protected = PROTECTED.get(pos, [])
        if d["protectedLiterals"] != protected:
            raise SystemExit(f"Protected-literal list mismatch at {pos} {locale}")
        checks = token_checks(prompt["sourceKey"], d["translation"], protected, is_hold=callerless)
        if checks != d["tokenChecks"] or not checks["allPass"]:
            raise SystemExit(f"Token audit mismatch at {pos} {locale}")
        if pos == 1375 and any(d["translation"].count(token) != 1 for token in protected):
            raise SystemExit(f"Path example not preserved exactly once at {pos} {locale}")
        disposition_counts[d["disposition"]] += 1
        per_locale[locale][d["disposition"]] += 1
        translation_by_key[(pos, locale)] = d["translation"]

    if disposition_counts != {"propose": 228, "hold": 12}:
        raise SystemExit("Disposition totals mismatch")
    if any(sum(per_locale[loc].values()) != 20 or per_locale[loc]["hold"] != 1 for loc in LOCALES):
        raise SystemExit("Per-locale hold/proposal totals mismatch")

    coherence = json.loads((OUT / "coherence-review.json").read_text())
    if len(coherence) != 36:
        raise SystemExit("Expected three coherence groups for each of 12 locales")
    expected_groups = {
        "securityHardening": [1363, 1364],
        "libraryPathAndScan": [1367, 1368, 1375],
        "fullscreenVisualizer": [1373, 1380],
    }
    seen = set()
    for row in coherence:
        key = (row["locale"], row["group"])
        if row["locale"] not in LOCALES or row["group"] not in expected_groups or key in seen or row["result"] != "pass" or not row["rationale"].strip():
            raise SystemExit("Malformed coherence review row")
        positions = expected_groups[row["group"]]
        if row["positions"] != positions or row["terms"] != [translation_by_key[(pos, row["locale"])] for pos in positions]:
            raise SystemExit(f"Coherence text does not match sealed translations: {key}")
        seen.add(key)
    if len(seen) != 36:
        raise SystemExit("Missing locale coherence row")

    if summary["head"] != HEAD or summary["tree"] != TREE or summary["cellCount"] != 240 or summary["proposedCells"] != 228 or summary["heldCells"] != 12 or summary["callerlessPosition"] != 1376 or summary["callerlessHolds"] != 12:
        raise SystemExit("Summary pin/count mismatch")
    if summary["dispositionCounts"] != dict(sorted(disposition_counts.items())):
        raise SystemExit("Summary disposition mismatch")
    expected_per_locale = {loc: dict(sorted(per_locale[loc].items())) for loc in LOCALES}
    if summary["perLocaleDispositions"] != expected_per_locale:
        raise SystemExit("Per-locale summary mismatch")
    if summary["coherenceGroupsReviewed"] != 3 or summary["coherenceChecks"] != 36:
        raise SystemExit("Coherence summary mismatch")
    if summary["tokenMismatches"] != {"placeholders": 0, "markup": 0, "numeric": 0, "protectedLiterals": 0}:
        raise SystemExit("Token summary mismatch")
    if verification["result"] != "PASS" or verification["rows"] != 240 or verification["proposals"] != 228 or verification["holds"] != 12 or verification["callerlessPosition"] != 1376 or verification["callerlessHolds"] != 12 or verification["coherenceRows"] != 36 or verification["allProposedTokenChecksPass"] is not True:
        raise SystemExit("Verification summary mismatch")
    print("PASS: slskR W1363-W1382 blind ledger covers 240 cells; 228 proposals and all 12 callerless rank-1376 cells are held; exact input pins, all token checks, three per-locale coherence groups, and checksums pass.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=pathlib.Path, default=DEFAULT_INPUT)
    args = parser.parse_args()
    verify(args.input)
