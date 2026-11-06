#!/usr/bin/env python3
import hashlib,json,re
from pathlib import Path
R=Path(__file__).resolve().parent
sha=lambda b:hashlib.sha256(b).hexdigest()
def jl(p):return [json.loads(x) for x in p.read_text(encoding="utf-8").splitlines() if x]
def tokens(s):
 return {"placeholders":re.findall(r"\{[A-Za-z][A-Za-z0-9_]*\}",s),"markupTags":re.findall(r"</?[A-Za-z][^>]*>",s),"numericTokens":re.findall(r"(?<![A-Za-z])\d+(?:[.,]\d+)?%?(?![A-Za-z])",s),"protectedLiterals":list(dict.fromkeys(m.group(0) for m in re.finditer(r"(?<![A-Za-z0-9])(?:[A-Z]{2,}[A-Z0-9]*|ffmpeg|Chromaprint|Soulseek|Spotify|YouTube|Pushbullet|Matrix|WebSocket|OpenAI)(?![A-Za-z0-9])",s)))}
m=json.loads((R/"manifest.json").read_text(encoding="utf-8")); s=json.loads((R/"summary.json").read_text(encoding="utf-8"))
assert m["repo"]=="snapetech-org/slskR" and m["pr"]==204
assert m["head"]=="727500e46852a5b6578e571781693857510943d9" and m["tree"]=="c71165c20fc6ba7d49d563898ea2ec8e1e448672"
assert m["selectedPositions"]==[1403,1422] and m["cellCount"]==240
assert m["primaryMaterialsOpened"] is False and m["reviewPacketSealStatus"]=="sealed before primary access"
att=json.loads((R/"PR-attestation.json").read_text(encoding="utf-8"))
assert att["head"]==m["head"] and att["tree"]==m["tree"] and att["state"]=="OPEN" and att["draft"] is True
entries=[]
for line in (R/"SHA256SUMS.txt").read_text(encoding="utf-8").splitlines():
 h,n=line.split("  ",1); entries.append((n,h))
assert len(entries)==len({n for n,h in entries})
assert {n for n,h in entries}=={p.name for p in R.iterdir() if p.is_file() and p.name!="SHA256SUMS.txt"}
for n,h in entries:assert sha((R/n).read_bytes())==h,n
rows=jl(R/"independent-review.jsonl"); locs=["es","zh-Hans","hi","de","ja","fr","pt-BR","ar","ko","zh-Hant","vi","id"]
assert len(rows)==240 and [(r["position"],r["locale"]) for r in rows]==[(p,l) for p in range(1403,1423) for l in locs]
assert all(r["primaryCandidateOrDecisionExposed"] is False for r in rows)
assert all(r["proposalSha256"]==sha(r["independentProposal"].encode("utf-8")) for r in rows)
counts={d:sum(r["disposition"]==d for r in rows) for d in ("retain","update","hold")}
assert counts==m["dispositionCounts"]==s["dispositions"]=={"retain":218,"update":21,"hold":1}
for r in rows:
 st=tokens(r["sourceKey"]); ct=tokens(r["currentTarget"]); pt=tokens(r["independentProposal"])
 assert st==r["sourceTokens"] and ct==r["currentTargetTokens"] and pt==r["proposalTokens"],(r["position"],r["locale"],"token data")
 assert st["placeholders"]==pt["placeholders"],(r["position"],r["locale"],"placeholder")
 assert st["markupTags"]==pt["markupTags"],(r["position"],r["locale"],"markup")
 assert [x for x in st["protectedLiterals"] if x not in pt["protectedLiterals"]]==r["protectedLiteralMismatchTokens"]==[],(r["position"],r["locale"],"protected literal")
 mismatch=st["numericTokens"]!=pt["numericTokens"]
 if mismatch:
  assert (r["position"],r["locale"]) in {(1416,"ja"),(1416,"ko")}
  assert r["numericTokenAudit"]=="source spells out three; target digit 3 is same value"
 else:assert r["numericTokenAudit"] in ("match","source spells out three; target digit 3 is same value")
 assert r["sourceKeySha256"]==sha(r["sourceKey"].encode("utf-8"))
 assert r["currentTargetSha256"]==sha(r["currentTarget"].encode("utf-8"))
 assert r["productionCallerCount"]==len(r["callerRefs"]) and r["sourceContextSha256"]
 assert r["catalogPath"].startswith("web/src/lib/locales/ui-labels.") and r["catalogFileSha256"] and r["catalogGitBlob"]
 if r["disposition"]=="retain":assert r["independentProposal"]==r["currentTarget"]
 if r["disposition"]=="hold":assert (r["position"],r["locale"])==(1420,"zh-Hant") and r["independentProposal"]==r["currentTarget"]
h=jl(R/"prior-hold-reattestation.jsonl"); p=jl(R/"prior-selection-reattestation.jsonl")
assert len(h)==35 and all(x["disposition"]=="hold" and x["reattestation"]=="same" and x["currentTarget"]==x["priorCurrentTarget"] and x["currentTargetSha256"]==x["priorCurrentTargetSha256"] for x in h)
assert len(p)==160 and all(x["selectionMatchesCurrentQueue"] and x["priorSourceKey"]==x["currentQueueSourceKey"]==x["priorSourceKey"] for x in p)
assert s["reviewedCells"]==240 and s["priorHoldsReattested"]==35 and s["changedPriorHolds"]==0 and s["priorSelectionsReattested"]==160
assert s["candidateFreeOnly"] is True and s["primaryMaterialsOpened"] is False
print(json.dumps({"result":"PASS","head":m["head"],"tree":m["tree"],"cells":len(rows),"dispositions":counts,"priorHoldsUnchanged":len(h),"priorSelectionsReattested":len(p),"numericSemanticExceptions":2,"checksumEntries":len(entries),"checksumListSha256":sha((R/"SHA256SUMS.txt").read_bytes()),"manifestSha256":sha((R/"manifest.json").read_bytes())},indent=2))
