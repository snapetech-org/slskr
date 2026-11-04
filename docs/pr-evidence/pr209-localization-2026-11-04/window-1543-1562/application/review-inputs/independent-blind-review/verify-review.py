#!/usr/bin/env python3
"""Verify the sealed independent blind review and its candidate-free input pins."""
import hashlib, json
from pathlib import Path

R = Path(__file__).resolve().parent
INPUT = Path("/home/keith/Documents/code/task-scratch/slskr-pr209-w1543-1562-primary-20261104/candidate-free-input")
def sha(b): return hashlib.sha256(b).hexdigest()
def j(path): return json.loads(path.read_text(encoding="utf-8"))
def jl(path): return [json.loads(s) for s in path.read_text(encoding="utf-8").splitlines() if s]
def parse_sums(path):
    out={}
    for line in path.read_text(encoding="utf-8").splitlines():
        digest,name=line.split(None,1); name=name.lstrip("* ")
        assert name not in out
        out[name]=digest
    return out

m=j(R/"manifest.json")
assert m["artifact"]=="slskR PR #209 W1543-W1562 independent blind semantic review"
assert m["exactPin"]["head"]=="c15eddffec2c4c24cc091b2a6ebf0c43fa58ef1b"
assert m["exactPin"]["tree"]=="4259db991f25fbbd0200963769e62bb7e2150806"
assert m["review"]["reviewedCells"]==240 and m["review"]["callerlessPositions"]==[]
assert m["reviewerExposure"]["priorAppReadbackJsonlOpened"] is False
assert m["reviewerExposure"]["prDescriptionOrBodyOpened"] is False

# Recheck the candidate-free packet seal and source/cell identities.
input_sums=parse_sums(INPUT/"SHA256SUMS.txt")
assert set(input_sums)=={p.name for p in INPUT.iterdir() if p.is_file() and p.name!="SHA256SUMS.txt"}
for name,digest in input_sums.items(): assert sha((INPUT/name).read_bytes())==digest,name
im=j(INPUT/"manifest.json")
assert im["head"]==m["exactPin"]["head"] and im["tree"]==m["exactPin"]["tree"]
source_rows=jl(INPUT/"source-contexts.jsonl")
source_by_pos={x["position"]:x for x in source_rows}
input_cells=jl(INPUT/"current-target-cells.jsonl")
assert len(input_cells)==240
out_cells=jl(R/"review-cells.jsonl")
assert len(out_cells)==240
assert [(x["position"],x["locale"]) for x in out_cells]==[(x["position"],x["locale"]) for x in input_cells]
for a,b in zip(input_cells,out_cells):
    assert a["position"]==b["position"] and a["locale"]==b["locale"]
    assert a["sourceKeySha256"]==b["sourceKeySha256"]
    assert a["sourceContextSha256"]==b["sourceContextSha256"]
    assert a["currentTargetSha256"]==b["targetSha256"]
    assert a["callerCount"]>0

findings=j(R/"findings.json")
by_id={f["id"]:f for f in findings}
assert len(by_id)==len(findings)
expected={}
for f in findings:
    for c in f["cells"]:
        key=(c["position"],c["locale"])
        assert key not in expected
        expected[key]=f["id"]
for cell in out_cells:
    key=(cell["position"],cell["locale"])
    want=[expected[key]] if key in expected else []
    assert cell["findingIds"]==want
    assert cell["disposition"]==("hold" if want else "accept")
assert sum(x["disposition"]=="hold" for x in out_cells)==m["review"]["heldCells"]
assert sum(x["disposition"]=="accept" for x in out_cells)==m["review"]["acceptedCells"]
assert len(findings)==m["review"]["findingCount"]

# The live PR/head/tree/ref values in both captured checks must remain self-consistent.
for check in m["liveRefChecks"].values():
    assert check["prTuple"]==[m["exactPin"]["head"],m["exactPin"]["headRef"],m["exactPin"]["baseSha"]]
    assert check["branchSha"]==check["pullSha"]==m["exactPin"]["head"]
    assert check["commitTreeSha"]==m["exactPin"]["tree"]

# Check sealed output file hashes and conventional checksum list.
for name,digest in m["fileHashes"].items(): assert sha((R/name).read_bytes())==digest,name
output_sums=parse_sums(R/"SHA256SUMS.txt")
assert set(output_sums)=={p.name for p in R.iterdir() if p.is_file() and p.name!="SHA256SUMS.txt"}
for name,digest in output_sums.items(): assert sha((R/name).read_bytes())==digest,name
print(json.dumps({"result":"PASS","head":m["exactPin"]["head"],"tree":m["exactPin"]["tree"],
 "reviewedCells":len(out_cells),"acceptedCells":m["review"]["acceptedCells"],"heldCells":m["review"]["heldCells"],
 "findings":len(findings),"candidateFreeFilesVerified":len(input_sums),"sealedOutputFilesVerified":len(output_sums),
 "callerlessPositions":m["review"]["callerlessPositions"]},ensure_ascii=False,indent=2))
