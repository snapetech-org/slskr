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
def git(*args):return subprocess.check_output(["git","-C",str(REPO),*args],text=True).strip()
def query():
    pr=json.loads(subprocess.check_output(["gh","api","repos/snapetech-org/slskR/pulls/204"],text=True))
    refs_raw=subprocess.check_output(["git","-C",str(REPO),"ls-remote","origin",f"refs/heads/{BRANCH}","refs/pull/204/head"],text=True)
    refs={line.split("\t",1)[1]:line.split("\t",1)[0] for line in refs_raw.splitlines() if "\t" in line}
    tree=subprocess.check_output(["gh","api",f"repos/snapetech-org/slskR/git/commits/{HEAD}","--jq",".tree.sha"],text=True).strip()
    snap={"state":pr["state"].upper(),"draft":pr["draft"],"head":pr["head"]["sha"],"branch":pr["head"]["ref"],"baseRef":pr["base"]["ref"],"baseSha":pr["base"]["sha"],"tree":tree,"refs":refs,"observedAtUtc":datetime.datetime.now(datetime.timezone.utc).isoformat()}
    if snap["state"]!="OPEN" or snap["draft"] is not True or snap["head"]!=HEAD or snap["branch"]!=BRANCH or snap["baseRef"]!="main" or snap["baseSha"]!=BASE or snap["tree"]!=TREE:
        raise SystemExit("live PR head/tree/base/state/ref mismatch")
    if refs!={f"refs/heads/{BRANCH}":HEAD,"refs/pull/204/head":HEAD}:raise SystemExit("live branch/pull refs mismatch")
    return snap
before=query()
if git("rev-parse","HEAD")!=HEAD or git("rev-parse","HEAD^{tree}")!=TREE or git("status","--porcelain"):
    raise SystemExit("source checkout drift or dirty state")
pins=json.loads((CF/"catalog-file-pins.json").read_text())
expected={}
for loc,x in pins["localeCatalogs"].items():expected[x["path"]]=(x["sha256"],x["gitBlob"],"locale-catalog")
x=pins["localeRuntime"];expected[x["path"]]=(x["sha256"],x["gitBlob"],"locale-runtime")
for path,x in pins["callerFiles"].items():expected[path]=(x["sha256"],x["gitBlob"],"production-caller")
observed={}
contents={}
for path,(sha_expected,blob_expected,kind) in sorted(expected.items()):
    raw=subprocess.check_output(["git","-C",str(REPO),"show",f"{HEAD}:{path}"])
    actual_sha=sha(raw)
    actual_blob=hashlib.sha1(b"blob "+str(len(raw)).encode("ascii")+bytes([0])+raw).hexdigest()
    if actual_sha!=sha_expected or actual_blob!=blob_expected:raise SystemExit("source pin drift "+path)
    observed[path]={"kind":kind,"sha256":actual_sha,"gitBlob":actual_blob,"bytes":len(raw)}
    if kind=="locale-catalog":contents[path]=json.loads(raw.decode("utf-8"))
cells=[json.loads(x) for x in (CF/"current-target-cells.jsonl").read_text().splitlines() if x]
for c in cells:
    path=pins["localeCatalogs"][c["locale"]]["path"]
    d=contents[path]
    if d.get(c["sourceKey"])!=c["currentTarget"] or sha(c["currentTarget"].encode("utf-8"))!=c["currentTargetSha256"]:
        raise SystemExit("catalog target drift "+str((c["position"],c["locale"])))
after=query()
record={"artifact":"slskR PR #204 W1443-W1462 final live pin recheck","repository":"snapetech-org/slskR","pullRequest":204,"branch":BRANCH,"reviewHead":HEAD,"reviewTree":TREE,"baseRef":"main","baseSha":BASE,"before":before,"after":after,"sourcePinCount":len(observed),"sourcePins":observed,"callerFiles":len(pins["callerFiles"]),"localeCatalogs":len(pins["localeCatalogs"]),"currentTargetCellsRechecked":len(cells),"allChecksPass":True}
(ROOT/"final-live-check.json").write_text(json.dumps(record,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print(json.dumps({"result":"PASS","head":HEAD,"tree":TREE,"branchAndPullRefsMatch":True,"sourcePins":len(observed),"callerFiles":len(pins["callerFiles"]),"localeCatalogs":len(pins["localeCatalogs"]),"currentTargets":len(cells)},indent=2))
