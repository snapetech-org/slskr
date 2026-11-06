#!/usr/bin/env python3
"""Verify a blind-review packet against its candidate-free input."""
import hashlib
import json
import re
import subprocess
from collections import Counter
from pathlib import Path

out=Path(__file__).resolve().parent
inp=Path("/home/keith/Documents/code/task-scratch/slskr-pr204-w1323-1342-primary-20261103/input-v4")
summary=json.loads((out/"summary.json").read_text())
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
assert summary["candidateFreeManifestSha256"]==sha(inp/"manifest.json")
assert summary["candidateFreeChecksumListSha256"]==sha(inp/"SHA256SUMS.txt")
cells=[json.loads(s) for s in (inp/"current-target-cells.jsonl").read_text().splitlines() if s.strip()]
ledger=[json.loads(s) for s in (out/"blind-review.jsonl").read_text().splitlines() if s.strip()]
assert len(cells)==240 and len(ledger)==240
cellmap={(r["position"],r["locale"]):r for r in cells}
ledgerkeys=[(r["position"],r["locale"]) for r in ledger]
assert len(set(ledgerkeys))==240 and set(ledgerkeys)==set(cellmap)
ph=re.compile(r"\{[a-zA-Z][a-zA-Z0-9_]*\}")
tag=re.compile(r"</?[A-Za-z][^>]*>")
for row in ledger:
    source=cellmap[(row["position"],row["locale"])]
    assert row["sourceKey"]==source["sourceKey"]
    assert row["sourceKeySha256"]==source["sourceKeySha256"]
    assert row["currentTarget"]==source["currentTarget"]
    assert row["currentTargetSha256"]==source["currentTargetSha256"]
    assert row["sourceContextSha256"]==source["sourceContextSha256"]
    target=row["selectedTarget"]
    assert [m.group(0) for m in ph.finditer(target)]==source["sourcePlaceholders"]
    assert all(token in target for token in source["sourceProtectedLiterals"])
    assert all(token in target for token in source["sourceNumericTokens"])
    assert [m.group(0) for m in tag.finditer(target)]==source["sourceMarkupTags"]
    if row["disposition"]=="accept":
        assert target==source["currentTarget"]
    else:
        assert target!=source["currentTarget"]
counts=Counter(r["disposition"] for r in ledger)
assert dict(sorted(counts.items()))==summary["currentWindowDispositionCounts"]
assert counts["correction"]==20 and counts["refinement"]==4 and counts["accept"]==216
prior=(inp/"prior-hold-reattestation.jsonl").read_bytes()
assert (out/"carry-forward-holds.jsonl").read_bytes()==prior
holds=[json.loads(s) for s in prior.decode().splitlines() if s.strip()]
assert len(holds)==22
assert all(r["reattestation"]=="same" and r["currentTarget"]==r["priorCurrentTarget"] and r["currentTargetSha256"]==r["priorCurrentTargetSha256"] for r in holds)
assert Counter(r["position"] for r in holds)==Counter({1257:12,1310:2,1311:1,1313:2,1316:5})
assert summary["currentWindowHolds"]==0
subprocess.run(["sha256sum","-c","SHA256SUMS.txt"],cwd=out,check=True,stdout=subprocess.DEVNULL)
print(json.dumps({"result":"PASS","cells":len(ledger),"counts":dict(sorted(counts.items())),"carryForwardHolds":len(holds),"carryForwardUnchanged":True,"proposalTokenChecks":"PASS"}))
