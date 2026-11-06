#!/usr/bin/env python3
from pathlib import Path
import datetime,hashlib,json,subprocess

ROOT=Path("/home/keith/Documents/code/task-scratch/slskr-pr204-w1443-1462-primary-20261103")
CF=ROOT/"candidate-free-input"
REPO=Path("/home/keith/Documents/code/task-scratch/slskr-pr204-w1443-1462-source-repo")
HEAD="44b37bd94385128d5bb5287aa1545901282bdfcb"
TREE="02c3f149a079c67b010d973dd02ca15776ad1610"
BRANCH="codex/slskr-l10n-audit-20261030"
BASE="2a2b188f10b9460a15bc6d5c34e406b0193d51ba"

def sha(b):return hashlib.sha256(b).hexdigest()
def git(repo,*args):return subprocess.check_output(["git","-C",str(repo),*args],text=True).strip()
def show(path):return subprocess.check_output(["git","-C",str(REPO),"show",f"{HEAD}:{path}"])
def gb(raw):return hashlib.sha1(b"blob "+str(len(raw)).encode("ascii")+bytes([0])+raw).hexdigest()

pr=json.loads(subprocess.check_output(["gh","api","repos/snapetech-org/slskR/pulls/204"],text=True))
refs_raw=subprocess.check_output(["git","-C",str(REPO),"ls-remote","origin",f"refs/heads/{BRANCH}","refs/pull/204/head"],text=True)
refs={line.split("\t",1)[1]:line.split("\t",1)[0] for line in refs_raw.splitlines() if "\t" in line}
tree=subprocess.check_output(["gh","api",f"repos/snapetech-org/slskR/git/commits/{HEAD}","--jq",".tree.sha"],text=True).strip()
if pr["state"]!="open" or pr["draft"] is not True or pr["head"]["sha"]!=HEAD or pr["head"]["ref"]!=BRANCH:
    raise SystemExit("live PR head/state/ref mismatch")
if pr["base"]["ref"]!="main" or pr["base"]["sha"]!=BASE or tree!=TREE:
    raise SystemExit("live PR base or tree mismatch")
expected={f"refs/heads/{BRANCH}":HEAD,"refs/pull/204/head":HEAD}
if refs!=expected:raise SystemExit("live branch/pull refs differ")
if git(REPO,"rev-parse","HEAD")!=HEAD or git(REPO,"rev-parse","HEAD^{tree}")!=TREE or git(REPO,"status","--porcelain"):
    raise SystemExit("local source checkout differs or is dirty")

pins=json.loads((CF/"catalog-file-pins.json").read_text())
checked={}
def attest_pin(path,expected_sha,expected_blob,kind):
    raw=show(path);actual_sha=sha(raw);actual_blob=gb(raw)
    if expected_sha and actual_sha!=expected_sha:raise SystemExit("source SHA drift: "+path)
    if expected_blob and actual_blob!=expected_blob:raise SystemExit("source Git blob drift: "+path)
    checked[path]={"kind":kind,"sha256":actual_sha,"gitBlob":actual_blob,"bytes":len(raw)}
for loc,x in pins["localeCatalogs"].items():
    attest_pin(x["path"],x["sha256"],x["gitBlob"],"locale-catalog")
attest_pin(pins["localeRuntime"]["path"],pins["localeRuntime"]["sha256"],pins["localeRuntime"]["gitBlob"],"locale-runtime")
for path,x in pins["callerFiles"].items():
    attest_pin(path,x["sha256"],x["gitBlob"],"production-caller")
# Re-read current targets from the exact pinned catalog blobs.
cats={loc:json.loads(show(x["path"]).decode("utf-8")) for loc,x in pins["localeCatalogs"].items()}
cells=[json.loads(line) for line in (CF/"current-target-cells.jsonl").read_text().splitlines() if line]
for c in cells:
    target=cats[c["locale"]][c["sourceKey"]]
    if target!=c["currentTarget"] or sha(target.encode("utf-8"))!=c["currentTargetSha256"]:
        raise SystemExit("current target drift: "+str(c["position"])+"/"+c["locale"])
before=json.loads((CF/"PR-attestation.json").read_text())
after={"repository":"snapetech-org/slskR","pullRequest":204,"state":"OPEN","draft":True,"branch":BRANCH,"head":HEAD,"tree":TREE,"baseRef":"main","baseSha":BASE,"branchRef":refs[f"refs/heads/{BRANCH}"],"pullRef":refs["refs/pull/204/head"],"observedAtUtc":datetime.datetime.now(datetime.timezone.utc).isoformat(),"checkoutHead":HEAD,"checkoutTree":TREE,"checkoutWorktreeClean":True,"beforeAttestationSha256":sha((CF/"PR-attestation.json").read_bytes()),"sourcePinCount":len(checked),"sourcePins":checked,"all240CatalogTargetsReattested":True}
(CF/"PR-attestation-after.json").write_text(json.dumps(after,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
manifest=json.loads((CF/"manifest.json").read_text())
manifest["sourcePinCountAfterReattestation"]=len(checked)
manifest["PRAttestationAfterSha256"]=sha((CF/"PR-attestation-after.json").read_bytes())
manifest["fileHashes"]={p.name:{"sha256":sha(p.read_bytes()),"byteCount":p.stat().st_size} for p in sorted(CF.iterdir()) if p.is_file() and p.name not in {"manifest.json","SHA256SUMS.txt"}}
(CF/"manifest.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
files=sorted(p for p in CF.iterdir() if p.is_file() and p.name!="SHA256SUMS.txt")
(CF/"SHA256SUMS.txt").write_text("".join(f"{sha(p.read_bytes())}  {p.name}\n" for p in files),encoding="utf-8")
print(json.dumps({"result":"PASS","head":HEAD,"tree":TREE,"liveState":"OPEN/DRAFT","branchRef":refs[f"refs/heads/{BRANCH}"],"pullRef":refs["refs/pull/204/head"],"sourcePins":len(checked),"all240TargetsReattested":len(cells),"callerContextPinCount":len(pins["callerFiles"]),"catalogFilesPinned":len(pins["localeCatalogs"])},indent=2))
