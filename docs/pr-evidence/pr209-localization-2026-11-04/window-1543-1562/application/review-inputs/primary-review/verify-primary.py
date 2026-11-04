#!/usr/bin/env python3
"""Verify the primary review against its sealed candidate-free input."""
import hashlib,json,re,subprocess
from collections import Counter
from pathlib import Path
P=Path(__file__).resolve().parent
INPUT=P.parent/"candidate-free-input"
HEAD="c15eddffec2c4c24cc091b2a6ebf0c43fa58ef1b"
TREE="4259db991f25fbbd0200963769e62bb7e2150806"
LOCS=["es","zh-Hans","hi","de","ja","fr","pt-BR","ar","ko","zh-Hant","vi","id"]
def sha(x):
    if isinstance(x,str):x=x.encode()
    return hashlib.sha256(x).hexdigest()
def j(p):return json.loads(p.read_text(encoding="utf-8"))
def jl(p):return [json.loads(s) for s in p.read_text(encoding="utf-8").splitlines() if s]
def toks(s):
    p=re.findall(r"\{[A-Za-z][A-Za-z0-9_]*\}",s)
    m=re.findall(r"</?[A-Za-z][^>]*>",s)
    n=re.findall(r"(?<![A-Za-z])\d+(?:[.,]\d+)?%?(?![A-Za-z])",s)
    z=[]
    for x in re.findall(r"(?<![A-Za-z0-9])(?:[A-Z]{2,}[A-Z0-9]*|ffmpeg|Chromaprint|Soulseek|Spotify|YouTube|Pushbullet|Matrix|WebSocket|OpenAI)(?![A-Za-z0-9])",s):
        if x not in z:z.append(x)
    return p,m,n,z

subprocess.check_call(["python3",str(INPUT/"verify-candidate-free.py")])
im=j(INPUT/"manifest.json"); assert (im["head"],im["tree"])==(HEAD,TREE)
sums={}
for line in (P/"SHA256SUMS.txt").read_text(encoding="utf-8").splitlines():
    digest,name=line.split(None,1); name=name.lstrip("* "); assert name not in sums; sums[name]=digest
actual={x.name for x in P.iterdir() if x.is_file() and x.name!="SHA256SUMS.txt"}
assert set(sums)==actual
for n,d in sums.items():assert sha((P/n).read_bytes())==d,n
ledger=jl(P/"primary-ledger.jsonl"); proposals=jl(P/"proposals.jsonl"); holds=jl(P/"holds.jsonl")
cells=jl(INPUT/"current-target-cells.jsonl")
assert len(ledger)==len(cells)==240
assert [(x["position"],x["locale"]) for x in ledger]==[(x["position"],x["locale"]) for x in cells]
assert [(x["position"],x["locale"]) for x in ledger]==[(p,l) for p in range(1543,1563) for l in LOCS]
cellmap={(x["position"],x["locale"]):x for x in cells}
bykey={(x["position"],x["locale"]):x for x in ledger}
counts=Counter(x["disposition"] for x in ledger)
assert set(counts)<= {"accept-current","propose-correction","propose-refinement","text-free-hold"}
for row in ledger:
    c=cellmap[(row["position"],row["locale"])]
    assert row["sourceKeySha256"]==c["sourceKeySha256"] and row["sourceContextSha256"]==c["sourceContextSha256"]
    assert row["currentTarget"]==c["currentTarget"] and row["currentTargetSha256"]==c["currentTargetSha256"]
    assert row["currentTargetSha256"]==sha(row["currentTarget"])
    if row["disposition"]=="accept-current":
        assert row["selectedTarget"]==row["currentTarget"] and row["selectedTargetSha256"]==row["currentTargetSha256"]
    elif row["disposition"] in ("propose-correction","propose-refinement"):
        assert isinstance(row["selectedTarget"],str) and row["selectedTarget"]!=row["currentTarget"]
        assert row["selectedTargetSha256"]==sha(row["selectedTarget"])
    else:
        assert row["selectedTarget"] is None and row["selectedTargetSha256"] is None
    if row["selectedTarget"] is not None:
        st,tt=toks(row["sourceKey"]),toks(row["selectedTarget"])
        assert st[0]==tt[0] and st[1]==tt[1] and st[2]==tt[2]
        assert all(x in tt[3] for x in st[3])
proposal_keys={(x["position"],x["locale"]) for x in proposals}
expected={(x["position"],x["locale"]) for x in ledger if x["disposition"] in ("propose-correction","propose-refinement")}
assert proposal_keys==expected and len(proposals)==len(expected)
for p in proposals:
    r=bykey[(p["position"],p["locale"])]
    for key in ("sourceKeySha256","sourceContextSha256","currentTargetSha256","selectedTarget","selectedTargetSha256","disposition","reason","confidence"):
        assert p[key]==r[key],(key,p["position"],p["locale"])
hold_keys={(x["position"],x["locale"]) for x in holds}
expected_holds={(x["position"],x["locale"]) for x in ledger if x["disposition"]=="text-free-hold"}
assert hold_keys==expected_holds and len(holds)==len(expected_holds)
for h in holds:
    assert not any(k in h for k in ("sourceKey","currentTarget","selectedTarget","target","proposedTarget","text"))
s=j(P/"SUMMARY.json")
assert s["head"]==HEAD and s["tree"]==TREE and s["cellCount"]==240 and s["pullRequest"]==209
assert s["counts"]=={k:counts.get(k,0) for k in ("accept-current","propose-correction","propose-refinement","text-free-hold")}
assert s["proposalCount"]==len(proposals) and s["holdCount"]==len(holds)
assert s["candidateFreeInputChecksumListSha256"]==sha((INPUT/"SHA256SUMS.txt").read_bytes())
assert s["nativeSpeakerSignoff"] is False and s["browserReviewPerformed"] is False
print(json.dumps({"result":"PASS","head":HEAD,"tree":TREE,"cells":len(ledger),"counts":s["counts"],
 "proposals":len(proposals),"holds":len(holds),"candidateFreeInputPinned":True,
 "tokenIntegrityPreserved":True,"checksummedFiles":len(sums),"nativeSpeakerSignoff":False,"browserReviewPerformed":False},ensure_ascii=False,indent=2))
