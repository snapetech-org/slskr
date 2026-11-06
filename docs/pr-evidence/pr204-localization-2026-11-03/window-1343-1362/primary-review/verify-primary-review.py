#!/usr/bin/env python3
import hashlib,json,re,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parent; TASK=ROOT.parent; INPUT=TASK/"input"; REPO=TASK/"repo"
HEAD="130462c56f75d3c8fc2a90663a48c0474ad1208b"; TREE="47aba96d79eb57d6024fb358ee59cde931f0de3b"
IM="d11af73c2178f0789b5429ece69811719e7d50b54bbcef08c93fda352376834e"; IS="7a77ceaae645ea04165ba88924ce6bed87d7650c52d7d91ef9e3f98b386327b3"
def sha(b):return hashlib.sha256(b).hexdigest()
def st(s):return sha(s.encode("utf-8"))
def j(p):return json.loads(p.read_text(encoding="utf-8"))
def jl(p):return [json.loads(x) for x in p.read_text(encoding="utf-8").splitlines() if x.strip()]
def git(*a):return subprocess.check_output(["git","-C",str(REPO),*a])
def gt(*a):return git(*a).decode().strip()
def checks(d,n):
 r=subprocess.run(["sha256sum","-c",n],cwd=d,text=True,capture_output=True);assert r.returncode==0,(r.stdout,r.stderr)
def tok(s):
 ph=re.findall(r"{[A-Za-z][A-Za-z0-9_]*}",s); tags=re.findall(r"</?[A-Za-z][^>]*>",s); nums=re.findall(r"(?<![A-Za-z])[0-9]+(?:[.,][0-9]+)?%?(?![A-Za-z])",s); prot=[]
 for m in re.finditer(r"(?<![A-Za-z0-9])(?:[A-Z]{2,}[A-Z0-9]*|ffmpeg|Chromaprint|Soulseek|Spotify|YouTube|Pushbullet|Matrix|WebSocket|OpenAI)(?![A-Za-z0-9])",s):
  if m.group(0) not in prot:prot.append(m.group(0))
 return ph,tags,nums,prot
checks(INPUT,"SHA256SUMS.txt");checks(ROOT,"SHA256SUMS.txt")
assert sha((INPUT/"manifest.json").read_bytes())==IM and sha((INPUT/"SHA256SUMS.txt").read_bytes())==IS
subprocess.run(["python3",str(INPUT/"verify-candidate-free.py")],check=True,capture_output=True,text=True)
m=j(ROOT/"manifest.json"); s=j(ROOT/"summary.json"); p=j(ROOT/"provenance.json")
assert (m["head"],m["tree"],m["selectedPositions"],m["sourceCount"],m["localeCount"],m["cellCount"])==(HEAD,TREE,[1343,1362],20,12,240)
assert (p["head"],p["tree"],p["candidateFreeManifestSha256"],p["candidateFreeChecksumListSha256"],p["blindReviewMaterialsRead"],p["repositoryOrPRModified"])==(HEAD,TREE,IM,IS,False,False)
for n,v in m["fileHashes"].items():assert sha((ROOT/n).read_bytes())==v["sha256"],n
assert gt("rev-parse",f"{HEAD}^{{tree}}")==TREE==gt("rev-parse","HEAD^{tree}")
cells={(r["position"],r["locale"]):r for r in jl(INPUT/"current-target-cells.jsonl")}
contexts={r["position"]:r for r in jl(INPUT/"source-contexts.jsonl")}
rows=jl(ROOT/"primary-review-ledger.jsonl");assert len(rows)==240 and len(cells)==240
counts={k:0 for k in ["correction","refinement","accept-current","hold"]}
for r in rows:
 k=(r["position"],r["locale"]);c=cells[k];a=tok(c["sourceKey"]);b=tok(r["target"])
 assert r["head"]==HEAD and r["tree"]==TREE and r["sourceKey"]==c["sourceKey"] and r["sourceKeySha256"]==st(c["sourceKey"])
 assert r["currentTarget"]==c["currentTarget"] and r["currentTargetSha256"]==st(c["currentTarget"]) and r["targetSha256"]==st(r["target"])
 assert (r["catalogPath"],r["catalogFileSha256"],r["catalogGitBlob"],r["callerRefs"],r["sourceContextSha256"])==(c["catalogPath"],c["catalogFileSha256"],c["catalogGitBlob"],c["callerRefs"],c["sourceContextSha256"])
 assert r["callerCount"]==len(contexts[r["position"]]["callers"])
 if r["disposition"] in {"accept-current","hold"}:assert r["target"]==r["currentTarget"]
 else:assert r["target"]!=r["currentTarget"] and r["rationale"]
 if r["disposition"]=="hold":assert r["callerCount"]==0
 assert r["disposition"] in counts and r["confidence"] in {"high","moderate","low"}
 assert (r["sourcePlaceholders"],r["targetPlaceholders"])==(a[0],b[0]) and a[0]==b[0]
 assert (r["sourceMarkupTags"],r["targetMarkupTags"])==(a[1],b[1]) and a[1]==b[1]
 assert (r["sourceNumericTokens"],r["targetNumericTokens"])==(a[2],b[2]) and a[2]==b[2]
 bad=[x for x in a[3] if x not in b[3]]
 assert r["sourceProtectedLiterals"]==a[3] and r["targetProtectedLiterals"]==b[3] and not bad
 assert all(r[x] for x in ["placeholderSequenceMatches","markupMatches","numericTokensMatch","protectedLiteralsMatch"])
 counts[r["disposition"]]+=1
assert counts==s["countsByDisposition"] and sum(counts.values())==240
assert counts["correction"]+counts["refinement"]==s["selectedChanges"]==57 and counts["hold"]==s["countsByDisposition"]["hold"]==0
assert s["priorHoldsPreserved"]==23 and s["blindReviewMaterialsRead"] is False
assert all(r["callerCount"]>0 for r in rows)
print(json.dumps({"result":"PASS","head":HEAD,"tree":TREE,"cells":len(rows),"counts":counts,"candidateFreeManifestSha256":IM,"candidateFreeChecksumListSha256":IS,"structuralMismatches":0,"carryForwardHolds":23},ensure_ascii=False,indent=2))
