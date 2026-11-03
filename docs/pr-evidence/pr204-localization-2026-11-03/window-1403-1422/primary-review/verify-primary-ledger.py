#!/usr/bin/env python3
import hashlib, json, re, subprocess, sys
from collections import Counter
from pathlib import Path

ROOT=Path(__file__).resolve().parent
TASK=ROOT.parent
INPUT=TASK/"candidate-free-input"
POSITIONS=list(range(1403,1423))
EXPECTED_HEAD="727500e46852a5b6578e571781693857510943d9"
EXPECTED_TREE="c71165c20fc6ba7d49d563898ea2ec8e1e448672"

def sha(b): return hashlib.sha256(b).hexdigest()
def canon(x): return json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(",",":")).encode()
def readj(p): return json.loads(p.read_text(encoding="utf-8"))
def readjl(p): return [json.loads(s) for s in p.read_text(encoding="utf-8").splitlines() if s.strip()]
def tokens(s):
    ph=re.findall(r"\{[A-Za-z][A-Za-z0-9_]*\}",s)
    tags=re.findall(r"</?[A-Za-z][^>]*>",s)
    nums=re.findall(r"(?<![A-Za-z])\d+(?:[.,]\d+)?%?(?![A-Za-z])",s)
    prot=[]
    for m in re.finditer(r"(?<![A-Za-z0-9])(?:[A-Z]{2,}[A-Z0-9]*|ffmpeg|Chromaprint|Soulseek|Spotify|YouTube|Pushbullet|Matrix|WebSocket|OpenAI)(?![A-Za-z0-9])",s):
        if m.group(0) not in prot: prot.append(m.group(0))
    return ph,tags,nums,prot
def icu(s): return bool(re.search(r"\{\s*[A-Za-z][A-Za-z0-9_]*\s*,\s*(plural|select|selectordinal)\s*,",s))

m=readj(ROOT/"manifest.json")
assert m["repository"]=="snapetech-org/slskR" and m["pullRequest"]==204
assert m["head"]==EXPECTED_HEAD and m["tree"]==EXPECTED_TREE
assert m["window"]=="W1403-W1422" and m["cellCount"]==240
assert m["sourceCount"]==20 and m["localeCount"]==12
assert m["sealed"] is True and m["reviewType"]=="primary-semantic"

ivp=subprocess.run([sys.executable,str(INPUT/"verify-candidate-free.py")],capture_output=True,text=True)
assert ivp.returncode==0,ivp.stdout+ivp.stderr
iv=json.loads(ivp.stdout)
assert iv["result"]=="PASS" and iv["head"]==EXPECTED_HEAD and iv["tree"]==EXPECTED_TREE
assert iv["positions"]==[1403,1422] and iv["cells"]==240 and iv["callerlessPositions"]==[]
assert iv["changedPriorHolds"]==0
im=readj(INPUT/"manifest.json")
assert sha((INPUT/"manifest.json").read_bytes())==m["inputManifestSha256"]==iv["manifestSha256"]
assert sha((INPUT/"SHA256SUMS.txt").read_bytes())==m["inputChecksumListSha256"]==iv["checksumListSha256"]
assert im["head"]==EXPECTED_HEAD and im["tree"]==EXPECTED_TREE
assert im["selectedPositions"]==[1403,1422] and im["candidateFreeInputOnly"] is True
assert im["proposedTranslationsIncluded"] is False
assert im["callerResolutionHoldCount"]==0 and im["carryForwardHoldChangedCount"]==0

locale_order=im["localeOrder"]
cells=readjl(INPUT/"current-target-cells.jsonl")
contexts=readjl(INPUT/"source-contexts.jsonl")
rows=readjl(ROOT/"review-ledger.jsonl")
evidence=readjl(ROOT/"source-context-evidence.jsonl")
decisions=readj(ROOT/"review-decisions.json")
assert len(cells)==len(rows)==240 and len(contexts)==len(evidence)==20
assert [r["position"] for r in contexts]==POSITIONS
assert [e["position"] for e in evidence]==POSITIONS
expected=[(p,l) for p in POSITIONS for l in locale_order]
assert [(r["position"],r["locale"]) for r in rows]==expected
cellmap={(c["position"],c["locale"]):c for c in cells}
ctxmap={c["position"]:c for c in contexts}
assert len({(d["position"],d["locale"]) for d in decisions})==len(decisions)==64
decisionmap={(d["position"],d["locale"]):d for d in decisions}
assert set(decisionmap)<=set(cellmap)
assert [(e["position"],e["evidence"]) for e in evidence]==[(c["position"],c) for c in contexts]
counts=Counter()
baseline=Counter()
reviewed=Counter()
for r in rows:
    k=(r["position"],r["locale"]); c=cellmap[k]; cx=ctxmap[r["position"]]
    d=r["disposition"]; counts[d]+=1
    assert r["sourceKey"]==c["sourceKey"] and r["sourceKeySha256"]==c["sourceKeySha256"]
    assert r["currentTarget"]==c["currentTarget"] and r["currentTargetSha256"]==c["currentTargetSha256"]
    assert sha(r["currentTarget"].encode())==r["currentTargetSha256"]
    assert r["catalog"]=={"fileSha256":c["catalogFileSha256"],"gitBlob":c["catalogGitBlob"],"keyCount":c["catalogKeyCount"],"path":c["catalogPath"]}
    ce=r["callerEvidence"]
    assert ce["callerContextSha256"]==cx["callerContextSha256"]==c["sourceContextSha256"]
    assert ce["sourceContextEvidenceSha256"]==sha(canon(cx))
    assert ce["productionCallerCount"]==cx["productionCallerCount"]==c["callerCount"]
    assert ce["callerOccurrenceCount"]==cx["callerOccurrenceCount"]
    want_callers=[{"fileSha256":q["fileSha256"],"gitBlob":q["gitBlob"],"line":q["line"],"lineSha256":q["lineSha256"],"path":q["path"]} for q in cx["callers"]]
    assert ce["callerRefs"]==want_callers==c["callerRefs"]
    assert r["checks"]["candidateFreeInputDiagnosticFlags"]=={"markupMatches":c["markupMatches"],"numericTokensMatch":c["numericTokensMatch"],"placeholderSequenceMatches":c["placeholderSequenceMatches"],"protectedLiteralsMatch":c["protectedLiteralsMatch"]}
    choice=decisionmap.get(k)
    if c["callerCount"]==0:
        assert d=="hold" and "proposedTarget" not in r
    else:
        assert d!="hold"
    if choice:
        assert d==choice["disposition"] and r.get("proposedTarget")==choice["target"]
        assert r["rationale"]==choice["rationale"] and r["confidence"]==choice["confidence"]
    else:
        assert d=="accept-current" and "proposedTarget" not in r
    target=r.get("proposedTarget",r["currentTarget"])
    sph,stags,snums,sprot=tokens(r["sourceKey"])
    tph,ttags,tnums,tprot=tokens(target)
    missing=[x for x in sprot if x not in tprot]
    assert sph==tph and stags==ttags and snums==tnums and not missing,(k,"token mismatch")
    assert icu(r["sourceKey"])==icu(target)
    q=r["checks"]
    assert q["placeholderSequencePreserved"]==(sph==tph) and q["markupPreserved"]==(stags==ttags)
    assert q["numericTokensPreserved"]==(snums==tnums) and q["protectedLiteralsPreservedInReviewedTarget"]==(not missing)
    assert q["icuSyntaxPreserved"]==(icu(r["sourceKey"])==icu(target))
    path_tokens=[x for x in ("/music","C:\\\\Music") if x in r["sourceKey"]]
    assert q["pathExampleTokens"]==path_tokens
    assert q["pathExampleTokensPreserved"]==(all(x in target for x in path_tokens) if path_tokens else None)
    baseline["placeholderSequenceMismatchCount"]+=not c["placeholderSequenceMatches"]
    baseline["markupMismatchCount"]+=not c["markupMatches"]
    baseline["numericTokenMismatchCount"]+=not c["numericTokensMatch"]
    baseline["protectedLiteralMismatchCount"]+=not c["protectedLiteralsMatch"]
    reviewed["placeholderSequenceMismatchCount"]+=sph!=tph
    reviewed["markupMismatchCount"]+=stags!=ttags
    reviewed["numericTokenMismatchCount"]+=snums!=tnums
    reviewed["protectedLiteralMismatchCount"]+=bool(missing)
assert sum(counts.values())==240 and counts["hold"]==0
assert len(decisions)==counts["correction"]+counts["refinement"]
summary=readj(ROOT/"summary.json")
assert summary["head"]==EXPECTED_HEAD and summary["tree"]==EXPECTED_TREE
assert summary["cellCount"]==240 and summary["sourceCount"]==20 and summary["localeCount"]==12
assert summary["decisionCounts"]==dict(counts)
assert summary["baselineDiagnostics"]==dict(baseline)==iv["mismatchCounts"]
assert summary["reviewedDiagnostics"]==dict(reviewed)
assert summary["holdCount"]==0 and summary["callerlessSourcePositions"]==[]
assert summary["carryForwardHoldsReattested"]==iv["priorHoldsReattested"]
assert summary["priorSelectionsReattested"]==iv["priorSelectedRowsReattested"]
assert summary["candidateFreeInputVerified"]=="PASS" and summary["runtimeAndCallerPins"]=="PASS"
assert summary["nativeSpeakerReview"]=="not performed" and summary["browserReview"]=="not performed"
assert summary["repositoryOrPRFilesEdited"] is False
assert m["decisionCounts"]==dict(counts) and m["holdCount"]==0 and m["candidateFreeInputVerifier"]=="PASS"
for name,meta in m["files"].items():
    p=ROOT/name
    assert p.is_file() and sha(p.read_bytes())==meta["sha256"] and p.stat().st_size==meta["byteCount"],(name,"manifest file mismatch")
sum_lines=(ROOT/"SHA256SUMS.txt").read_text(encoding="utf-8").splitlines()
sum_map={}
for line in sum_lines:
    h,name=line.split("  ",1); sum_map[name]=h
actual={p.name for p in ROOT.iterdir() if p.is_file()}-{"SHA256SUMS.txt"}
assert set(sum_map)==actual
for name,h in sum_map.items(): assert sha((ROOT/name).read_bytes())==h,(name,"checksum-list mismatch")
assert set(m["files"])==actual-{"manifest.json"}
print(json.dumps({"result":"PASS","head":EXPECTED_HEAD,"tree":EXPECTED_TREE,"window":"W1403-W1422","cells":len(rows),"sourceContexts":len(contexts),"decisions":len(decisions),"decisionCounts":dict(sorted(counts.items())),"confidenceCounts":dict(sorted(Counter(r["confidence"] for r in rows).items())),"callerlessPositions":iv["callerlessPositions"],"carryForwardHoldsReattested":iv["priorHoldsReattested"],"priorSelectionsReattested":iv["priorSelectedRowsReattested"],"candidateFreeVerifier":"PASS","primaryFileHashesVerified":sorted(m["files"]),"checksumListFilesVerified":len(sum_map)},ensure_ascii=False,sort_keys=True,indent=2))
