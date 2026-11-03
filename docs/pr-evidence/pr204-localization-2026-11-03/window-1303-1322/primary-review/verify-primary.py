#!/usr/bin/env python3
import hashlib,json,re,subprocess
from pathlib import Path
from collections import Counter
HERE=Path(__file__).resolve(); OUT=HERE.parent; TASK=OUT.parent; INPUT=TASK/"input"
EXPECTED_MANIFEST="3145ccef78adbea528fe062d053ba90067207c4c49611ba43994da78383b244c"
EXPECTED_SUMS="d30a1b2aa55a13eb0b33a116cfbf965494b675bbedf3acb9a6fbc61c53ead652"
EXPECTED_HEAD="f46b8b2322f4b944f39f34d5bb8d55852ba330c8"; EXPECTED_TREE="4eba98f951a745dac6b5332bd6796bf57c7037e2"
def sha(b): return hashlib.sha256(b).hexdigest()
def sha_text(s): return sha(s.encode("utf-8"))
def readj(p): return json.loads(p.read_text(encoding="utf-8"))
def readjl(p): return [json.loads(x) for x in p.read_text(encoding="utf-8").splitlines() if x]
subprocess.check_call(["python3",str(INPUT/"verify-candidate-free.py")],stdout=subprocess.DEVNULL)
subprocess.check_call(["sha256sum","-c","SHA256SUMS.txt"],cwd=INPUT,stdout=subprocess.DEVNULL)
ib=(INPUT/"manifest.json").read_bytes(); isum=(INPUT/"SHA256SUMS.txt").read_bytes()
assert sha(ib)==EXPECTED_MANIFEST and sha(isum)==EXPECTED_SUMS
for packet in [INPUT,OUT]:
 sums=(packet/"SHA256SUMS.txt").read_bytes()
 for line in sums.decode().splitlines():
  digest,name=line.split(None,1); name=name.lstrip("* ")
  assert sha((packet/name).read_bytes())==digest,(packet.name,name)
manifest=readj(INPUT/"manifest.json"); attest=readj(INPUT/"PR-attestation.json")
assert manifest["head"]==EXPECTED_HEAD and manifest["tree"]==EXPECTED_TREE and attest["state"]=="OPEN" and attest["draft"] is True
cells={(r["position"],r["locale"]):r for r in readjl(INPUT/"current-target-cells.jsonl")}
contexts={r["position"]:r for r in readjl(INPUT/"source-contexts.jsonl")}
queue={r["position"]:r for r in readjl(INPUT/"source-queue.jsonl")}
ledger=readjl(OUT/"ledger.jsonl")
assert len(cells)==240 and len(contexts)==20 and len(ledger)==240
assert len({(r["position"],r["locale"]) for r in ledger})==240
assert {r["position"] for r in ledger}==set(range(1303,1323))
assert {r["locale"] for r in ledger}==set(manifest["localeOrder"])
ph=re.compile(r"\{[A-Za-z][A-Za-z0-9_]*\}"); tags=re.compile(r"<\/?[A-Za-z][^>]*>"); nums=re.compile(r"(?<![A-Za-z])\d+(?:[.,]\d+)?%?(?![A-Za-z])")
counts=Counter()
for r in ledger:
 key=(r["position"],r["locale"]); cell=cells[key]; ctx=contexts[r["position"]]; q=queue[r["position"]]
 assert r["sourceKey"]==q["sourceKey"]==cell["sourceKey"] and r["sourceKeySha256"]==q["sourceKeySha256"]==cell["sourceKeySha256"]
 assert r["currentTarget"]==cell["currentTarget"] and r["currentTargetSha256"]==cell["currentTargetSha256"]==sha_text(r["currentTarget"])
 assert r["proposedTargetSha256"]==sha_text(r["proposedTarget"])
 assert r["catalogPath"]==cell["catalogPath"] and r["catalogFileSha256"]==cell["catalogFileSha256"] and r["catalogGitBlob"]==cell["catalogGitBlob"]
 assert r["callerCount"]==cell["callerCount"]==len(r["callerRefs"])
 assert r["callerContextSha256"]==ctx["callerContextSha256"]
 expected=[{"path":x["path"],"line":x["line"],"contextStartLine":x["contextStartLine"],"contextEndLine":x["contextEndLine"],"lineSha256":x["lineSha256"],"contextSha256":x["contextSha256"],"fileSha256":x["fileSha256"],"gitBlob":x["gitBlob"]} for x in ctx["callers"]]
 assert r["callerRefs"]==expected
 target=r["proposedTarget"]; source=r["sourceKey"]
 checks={"placeholdersMatch":ph.findall(source)==ph.findall(target),"markupTagsMatch":tags.findall(source)==tags.findall(target),"numericTokensMatch":nums.findall(source)==nums.findall(target),"protectedLiteralsMatch":all(t in target for t in cell["sourceProtectedLiterals"])}
 assert r["checks"]==checks and all(checks.values()),(key,checks)
 assert r["sourceProtectedLiterals"]==cell["sourceProtectedLiterals"]
 assert r["proposedProtectedLiterals"]==[t for t in cell["sourceProtectedLiterals"] if t in target]
 assert r["decision"] in {"correction","refinement","accept-current","hold"}
 assert (r["decision"]=="accept-current")== (target==r["currentTarget"])
 if r["decision"]=="hold": assert target==r["currentTarget"] and not r["callerCount"]
 else: assert r["callerCount"]>0
 assert r["rationale"].strip()
 counts[r["decision"]]+=1
summary=readj(OUT/"summary.json")
assert summary["head"]==EXPECTED_HEAD and summary["tree"]==EXPECTED_TREE
assert summary["cellCount"]==len(ledger) and summary["decisionCounts"]==dict(sorted(counts.items()))
assert summary["changedCellCount"]==sum(r["proposedTarget"]!=r["currentTarget"] for r in ledger)
assert summary["heldCellCount"]==counts["hold"]==0
assert summary["placeholderMismatchCount"]==summary["markupMismatchCount"]==summary["numericTokenMismatchCount"]==summary["protectedLiteralMismatchCount"]==0
assert summary["primaryReviewOnly"] and summary["applicationApproved"] is False and not summary["blindReviewIncluded"] and not summary["crossAuditIncluded"]
prov=readj(OUT/"provenance.json")
assert prov["candidateFreeInput"]["manifestSha256"]==EXPECTED_MANIFEST and prov["candidateFreeInput"]["checksumListSha256"]==EXPECTED_SUMS
assert prov["liveAttestation"]["head"]==EXPECTED_HEAD and prov["liveAttestation"]["tree"]==EXPECTED_TREE
print(json.dumps({"result":"PASS","inputManifestSha256":EXPECTED_MANIFEST,"inputChecksumListSha256":EXPECTED_SUMS,"primaryChecksumListSha256":sha((OUT/"SHA256SUMS.txt").read_bytes()),"cellCount":len(ledger),"decisionCounts":dict(sorted(counts.items())),"changedCells":summary["changedCellCount"],"holds":counts["hold"],"allProposedStructureChecksPassed":True},indent=2))
