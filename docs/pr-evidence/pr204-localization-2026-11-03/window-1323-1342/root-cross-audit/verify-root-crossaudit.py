#!/usr/bin/env python3
"""Verify the root cross-audit against the exact sealed review packets."""
import hashlib
import json
import re
import subprocess
from collections import Counter
from pathlib import Path

out=Path(__file__).resolve().parent
inp=Path("/home/keith/Documents/code/task-scratch/slskr-pr204-w1323-1342-primary-20261103/input-v4")
pdir=Path("/home/keith/Documents/code/task-scratch/slskr-pr204-w1323-1342-primary-20261103/primary-review-v2")
bdir=Path("/home/keith/Documents/code/task-scratch/slskr-pr204-w1323-1342-independent-blind-20261103")
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
summary=json.loads((out/"summary.json").read_text())
att=json.loads((inp/"PR-attestation.json").read_text())
assert att["head"]==summary["head"] and att["tree"]==summary["tree"]
assert summary["packetPins"]["candidateFreeManifestSha256"]==sha(inp/"manifest.json")
assert summary["packetPins"]["candidateFreeChecksumListSha256"]==sha(inp/"SHA256SUMS.txt")
assert summary["packetPins"]["primarySummarySha256"]==sha(pdir/"summary.json")
assert summary["packetPins"]["primaryChecksumListSha256"]==sha(pdir/"SHA256SUMS.txt")
assert summary["packetPins"]["blindSummarySha256"]==sha(bdir/"summary.json")
assert summary["packetPins"]["blindChecksumListSha256"]==sha(bdir/"SHA256SUMS.txt")
cells=[json.loads(s) for s in (inp/"current-target-cells.jsonl").read_text().splitlines() if s.strip()]
ledger=[json.loads(s) for s in (out/"root-cross-audit-ledger.jsonl").read_text().splitlines() if s.strip()]
plan=[json.loads(s) for s in (out/"proposal-only-apply-plan.jsonl").read_text().splitlines() if s.strip()]
holds=(inp/"prior-hold-reattestation.jsonl").read_bytes()
assert (out/"carry-forward-holds.jsonl").read_bytes()==holds
cmap={(r["position"],r["locale"]):r for r in cells}
assert len(cells)==len(ledger)==240
lmap={(r["position"],r["locale"]):r for r in ledger}
assert len(lmap)==240 and set(lmap)==set(cmap)
ph=re.compile(r"\{[a-zA-Z][a-zA-Z0-9_]*\}")
tag=re.compile(r"</?[A-Za-z][^>]*>")
for key,row in lmap.items():
    c=cmap[key]
    assert row["sourceKey"]==c["sourceKey"] and row["sourceKeySha256"]==c["sourceKeySha256"]
    assert row["currentTarget"]==c["currentTarget"] and row["currentTargetSha256"]==c["currentTargetSha256"]
    assert row["sourceContextSha256"]==c["sourceContextSha256"]
    assert [m.group(0) for m in ph.finditer(row["selectedTarget"])]==c["sourcePlaceholders"]
    assert all(t in row["selectedTarget"] for t in c["sourceProtectedLiterals"])
    assert all(t in row["selectedTarget"] for t in c["sourceNumericTokens"])
    assert [m.group(0) for m in tag.finditer(row["selectedTarget"])]==c["sourceMarkupTags"]
    assert row["selectedTargetSha256"]==hashlib.sha256(row["selectedTarget"].encode()).hexdigest()
assert len(plan)==43
expected={(r["position"],r["locale"]):r for r in plan}
assert set(expected)=={k for k,r in lmap.items() if r["selectedTarget"]!=r["currentTarget"]}
for k,r in expected.items():
    assert r["selectedTarget"]==lmap[k]["selectedTarget"]
prior=[json.loads(s) for s in holds.decode().splitlines() if s.strip()]
assert len(prior)==22
assert all(r["reattestation"]=="same" and r["currentTarget"]==r["priorCurrentTarget"] and r["currentTargetSha256"]==r["priorCurrentTargetSha256"] for r in prior)
assert Counter(r["position"] for r in prior)==Counter({1257:12,1310:2,1311:1,1313:2,1316:5})
assert sum(r["rootAction"]=="hold" for r in ledger)==1
assert sum(r["rootAction"]=="retain" for r in ledger)==196
assert sum(r["rootAction"]=="proposal" for r in ledger)==43
assert len([1 for r in ledger if r["primaryDisposition"]=="hold"])==1
assert (out/"disagreement-resolutions.jsonl").exists()
for folder,verifier in ((inp,"verify-candidate-free.py"),(pdir,"verify-primary-review.py"),(bdir,"verify-blind-review.py")):
    subprocess.run(["python3",str(folder/verifier)],check=True,stdout=subprocess.DEVNULL)
subprocess.run(["sha256sum","-c","SHA256SUMS.txt"],cwd=out,check=True,stdout=subprocess.DEVNULL)
print(json.dumps({"result":"PASS","cells":len(ledger),"proposalOnlyChanges":len(plan),"retains":196,"holds":1,"carryForwardHolds":len(prior),"carryForwardUnchanged":True}))
