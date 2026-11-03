#!/usr/bin/env python3
import hashlib,json,re,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent
INP=ROOT.parent/"input-v4"
def sha(b): return hashlib.sha256(b).hexdigest()
def sha_text(s): return sha(s.encode("utf-8"))
def readj(p): return json.loads(p.read_text(encoding="utf-8"))
def readjl(p): return [json.loads(x) for x in p.read_text(encoding="utf-8").splitlines() if x]
proc=subprocess.run([sys.executable,str(INP/"verify-candidate-free.py")],capture_output=True,text=True,check=True)
m=readj(INP/"manifest.json"); s=readj(ROOT/"summary.json"); ledger=readjl(ROOT/"review-ledger.jsonl"); terms=readjl(ROOT/"terminology-context.jsonl")
input_cells=readjl(INP/"current-target-cells.jsonl"); input_by_key={(r["position"],r["locale"]):r for r in input_cells}
pins=readj(INP/"catalog-file-pins.json")
assert m["head"]==s["pin"]["head"]=="6ccefe07d8154acbc08e34249ef7039dc5bc1f08"
assert m["tree"]==s["pin"]["tree"]=="e0c1d1341be45ed73bd30cf027b479ce3b5bb95d"
assert len(ledger)==240 and len({(r["position"],r["locale"]) for r in ledger})==240
assert s["candidateFreeInput"]["manifestSha256"]==sha((INP/"manifest.json").read_bytes())
assert s["candidateFreeInput"]["checksumListSha256"]==sha((INP/"SHA256SUMS.txt").read_bytes())
assert all(r["confidence"] in {"high","moderate","low","unknown"} for r in ledger)
assert all(r["targetSha256"]==sha_text(r["target"]) for r in ledger)
assert all(r["currentTargetSha256"]==sha_text(r["currentTarget"]) for r in ledger)
assert all(r["disposition"] in {"propose","retain","hold"} for r in ledger)
assert all(r["target"]==r["currentTarget"] for r in ledger if r["disposition"] in {"retain","hold"})
assert all(r["proposedTarget"] is None and r["proposedTargetSha256"] is None for r in ledger if r["disposition"]=="hold")
assert all(r["proposedTarget"]==r["target"] and r["proposedTargetSha256"]==r["targetSha256"] for r in ledger if r["disposition"]=="propose")
assert all(r["structuralChecks"]=={"placeholdersPreserved":True,"markupPreserved":True,"numericTokensPreserved":True,"protectedLiteralsPreserved":True} for r in ledger)
ph=re.compile(r"\{[A-Za-z][A-Za-z0-9_]*\}"); tags=re.compile(r"<\/?[A-Za-z][^>]*>"); nums=re.compile(r"(?<![A-Za-z])\d+(?:[.,]\d+)?%?(?![A-Za-z])")
for r in ledger:
 key=(r["position"],r["locale"]); ic=input_by_key[key]
 assert r["sourceKey"]==ic["sourceKey"] and r["sourceKeySha256"]==ic["sourceKeySha256"]
 assert r["currentTarget"]==ic["currentTarget"] and r["currentTargetSha256"]==ic["currentTargetSha256"]
 assert r["catalogPath"]==ic["catalogPath"] and r["catalogFileSha256"]==ic["catalogFileSha256"] and r["catalogGitBlob"]==ic["catalogGitBlob"]
 assert r["callerContextSha256"]==ic["sourceContextSha256"] and r["callerCount"]==ic["callerCount"] and r["callerRefs"]==ic["callerRefs"]
 assert r["sourceTokens"]=={"placeholders":ic["sourcePlaceholders"],"markupTags":ic["sourceMarkupTags"],"numericTokens":ic["sourceNumericTokens"],"protectedLiterals":ic["sourceProtectedLiterals"]}
 src=r["sourceTokens"]; tgt=r["targetTokens"]
 assert src["placeholders"]==ph.findall(r["target"])
 assert src["markupTags"]==tags.findall(r["target"])
 assert src["numericTokens"]==nums.findall(r["target"])
 assert all(t in tgt["protectedLiterals"] for t in src["protectedLiterals"])
term_ids={t["referenceId"] for t in terms}
for r in ledger:
 assert len(r["callerRefs"])==r["callerCount"]>0
 assert r["callerContextSha256"]
 assert all(ref in term_ids for ref in r["terminologyReferences"])
for t in terms:
 assert t["head"]==m["head"] and t["tree"]==m["tree"]
 assert t["catalogFileSha256"]==pins["localeCatalogs"][t["locale"]]["sha256"]
 assert t["catalogGitBlob"]==pins["localeCatalogs"][t["locale"]]["gitBlob"]
 assert t["currentTargetSha256"]==sha_text(t["currentTarget"])
assert len(terms)==36 and len({t["referenceId"] for t in terms})==36
counts={d:sum(r["disposition"]==d for r in ledger) for d in ["propose","retain","hold"]}
assert counts==s["counts"] and sum(counts.values())==240
assert counts["hold"]==1 and s["callerlessHolds"]==0
assert s["structuralMismatchCounts"]=={"placeholderMismatchCount":0,"markupMismatchCount":0,"numericTokenMismatchCount":0,"protectedLiteralMismatchCount":0}
entries=[]
for line in (ROOT/"SHA256SUMS.txt").read_text().splitlines():
 d,n=line.split(None,1); n=n.lstrip("* "); entries.append((n,d))
assert len(entries)==len({n for n,d in entries})
assert {n for n,d in entries}=={p.name for p in ROOT.iterdir() if p.is_file() and p.name!="SHA256SUMS.txt"}
for n,d in entries: assert sha((ROOT/n).read_bytes())==d,n
print(json.dumps({"result":"PASS","candidateFreeVerifier":"PASS","ledgerCells":len(ledger),"counts":counts,"structuralMismatchCounts":s["structuralMismatchCounts"],"terminologyReferenceRows":len(terms),"summarySha256":sha((ROOT/"summary.json").read_bytes()),"checksumListSha256":sha((ROOT/"SHA256SUMS.txt").read_bytes())},indent=2))
