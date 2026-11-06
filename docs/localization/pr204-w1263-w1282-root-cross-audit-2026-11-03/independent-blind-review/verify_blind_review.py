#!/usr/bin/env python3
import collections,hashlib,json,re,subprocess
from pathlib import Path
root=Path("/home/keith/Documents/code/task-scratch/slskr-pr204-w1263-1282-blind-20261103"); src=root/"clean-input"; out=root/"blind-review"
def H(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def R(p):return [json.loads(x) for x in p.read_text(encoding="utf-8").splitlines() if x.strip()]
s=json.loads((out/"summary.json").read_text(encoding="utf-8"))
assert H(src/"SHA256SUMS.txt")==s["candidateFreeInputChecksumListSha256"]
assert H(src/"manifest.json")==s["candidateFreeManifestJsonSha256"]
assert subprocess.run(["sha256sum","-c","SHA256SUMS.txt"],cwd=src,capture_output=True).returncode==0
a=R(out/"blind-ledger.jsonl"); b=R(src/"current-target-cells.jsonl"); by={(x["position"],x["locale"]):x for x in b}
assert len(a)==240 and len(by)==240
ph=re.compile(r"\{[A-Za-z][A-Za-z0-9_]*\}"); counts=collections.Counter()
for x in a:
 i=by[(x["position"],x["locale"])]
 assert (x["sourceKey"],x["sourceKeySha256"],x["currentTarget"],x["currentTargetSha256"])==(i["sourceKey"],i["sourceKeySha256"],i["currentTarget"],i["currentTargetSha256"])
 proposed=x["proposedTarget"] if x["proposedTarget"] is not None else x["currentTarget"]
 assert ph.findall(x["sourceKey"])==ph.findall(x["currentTarget"])==ph.findall(proposed)
 assert all(t in x["currentTarget"] and t in proposed for t in x["protectedLiterals"])
 assert x["callerReferenceCount"]>0 and x["callerPaths"]
 counts[x["verdict"]]+=1
assert counts==collections.Counter({"accept-current":183,"correction":31,"refinement":26})==collections.Counter(s["verdictCounts"])
assert not s["primaryReviewRead"] and not s["candidateFreeInputModified"] and not s["repositoryOrPRModified"]
print(json.dumps({"status":"passed","rows":len(a),"verdictCounts":dict(counts),"inputChecksumListSha256":s["candidateFreeInputChecksumListSha256"],"manifestJsonSha256":s["candidateFreeManifestJsonSha256"],"placeholdersProtectedLiteralsCallerPins":"verified"},indent=2))
