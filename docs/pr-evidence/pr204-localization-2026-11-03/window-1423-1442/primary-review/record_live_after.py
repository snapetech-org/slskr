#!/usr/bin/env python3
import json,subprocess
from pathlib import Path
root=Path(__file__).resolve().parent
repo=Path("/home/keith/Documents/code/task-scratch/slskr-pr204-w1423-1442-apply-20261103/repo")
branch="codex/slskr-l10n-audit-20261030"
def observe():
 p=json.loads(subprocess.check_output(["gh","pr","view","204","--repo","snapetech-org/slskR","--json","state,isDraft,headRefName,headRefOid,baseRefName,baseRefOid,url"],text=True))
 raw=subprocess.check_output(["git","-C",str(repo),"ls-remote","origin",f"refs/heads/{branch}","refs/pull/204/head"],text=True)
 refs={line.split("\t",1)[1]:line.split("\t",1)[0] for line in raw.splitlines()}
 return {"observedAtUtc":subprocess.check_output(["date","-u","+%Y-%m-%dT%H:%M:%SZ"],text=True).strip(),"repository":"snapetech-org/slskR","pullRequest":204,"url":p["url"],"state":p["state"],"isDraft":p["isDraft"],"branch":p["headRefName"],"head":p["headRefOid"],"baseRef":p["baseRefName"],"baseSha":p["baseRefOid"],"headTree":subprocess.check_output(["git","-C",str(repo),"rev-parse",f"{p["headRefOid"]}^{{tree}}"],text=True).strip(),"liveBranchRef":refs.get(f"refs/heads/{branch}"),"livePullRef":refs.get("refs/pull/204/head"),"checkoutPath":str(repo),"checkoutHead":subprocess.check_output(["git","-C",str(repo),"rev-parse","HEAD"],text=True).strip(),"checkoutTree":subprocess.check_output(["git","-C",str(repo),"rev-parse","HEAD^{tree}"],text=True).strip(),"checkoutWorktreeClean":not bool(subprocess.check_output(["git","-C",str(repo),"status","--porcelain=v1"],text=True))}
p=root/"live-pr-attestation.json";d=json.loads(p.read_text());d["observedAfter"]=observe();p.write_text(json.dumps(d,indent=2)+"\n")
