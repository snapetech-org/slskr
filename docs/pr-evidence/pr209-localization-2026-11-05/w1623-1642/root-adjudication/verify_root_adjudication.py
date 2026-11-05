#!/usr/bin/env python3
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parent; BASE=ROOT.parent
HEAD="7e366cbf21ad5490bd11ef418a0f2a98b3fbd567"; TREE="801d7a037c15dcd83b3e038160054a46c9b8f03b"
def sha(b): return hashlib.sha256(b).hexdigest()
def rows(p): return [json.loads(s) for s in p.read_text(encoding="utf-8").splitlines() if s.strip()]
summary=json.loads((ROOT/"summary.json").read_text(encoding="utf-8")); ledger=rows(ROOT/"root-disposition-ledger.jsonl"); cross=rows(BASE/"cross-review/cross-review-ledger.jsonl"); proposals={(r["position"],r["locale"]):r for r in rows(BASE/"cross-review/proposal-adjudications.jsonl")}
if summary["head"]!=HEAD or summary["tree"]!=TREE or summary["ledgerSha256"]!=sha((ROOT/"root-disposition-ledger.jsonl").read_bytes()): raise SystemExit("FAIL root packet pin")
if len(ledger)!=240 or len(cross)!=240 or len({(r["position"],r["locale"]) for r in ledger})!=240: raise SystemExit("FAIL coverage")
changes=0
for a,b in zip(ledger,cross):
 key=(a["position"],a["locale"])
 if (a["sourceKeySha256"],a["sourceContextSha256"],a["currentTargetSha256"],a["independentCrossRecordSha256"])!=(b["sourceKeySha256"],b["sourceContextSha256"],b["currentTargetSha256"],b["crossReviewRecordSha256"]): raise SystemExit(f"FAIL cross binding {key}")
 if a["finalDisposition"]=="correction":
  changes+=1; proposal=proposals.get(key)
  if proposal is None or a["finalTarget"]!=proposal["rootRecommendedTarget"] or hashlib.sha256(a["finalTarget"].encode()).hexdigest()!=a["finalTargetSha256"]: raise SystemExit(f"FAIL selected target {key}")
 elif a["finalDisposition"]!="accept-current" or a["finalTarget"] is not None: raise SystemExit(f"FAIL disposition {key}")
if changes!=13 or summary["dispositions"]!={"accept-current":227,"correction":13,"hold":0}: raise SystemExit("FAIL counts")
actual={x.relative_to(ROOT).as_posix() for x in ROOT.rglob("*") if x.is_file() and x.name!="SHA256SUMS.txt"}; listed={}
for line in (ROOT/"SHA256SUMS.txt").read_text().splitlines():
 d,n=line.split("  ",1); listed[n]=d
 if n not in actual or sha((ROOT/n).read_bytes())!=d: raise SystemExit(f"FAIL checksum {n}")
if set(listed)!=actual: raise SystemExit("FAIL checksum coverage")
print(json.dumps({"result":"PASS","head":HEAD,"tree":TREE,"cells":240,"dispositions":summary["dispositions"],"checksumFiles":len(listed)},sort_keys=True))
