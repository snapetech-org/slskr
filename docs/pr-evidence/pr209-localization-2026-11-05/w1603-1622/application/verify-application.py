#!/usr/bin/env python3
import sys
sys.dont_write_bytecode=True
import argparse,hashlib,json,re,subprocess
from pathlib import Path

APP=Path(__file__).resolve().parent
EVIDENCE=APP.parent
BASE="eeb63f1e4e21d801f4a4e0393813b6e86a1ff7c8"
PRODUCT="bdc831fcde86101cd949fe70bd99acd8871ace4a"
PRODUCT_TREE="c9d994368a90e82f310a3c81a6ba059567c0e3bd"

def sha(data): return hashlib.sha256(data).hexdigest()
def shat(text): return sha(text.encode("utf-8"))
def j(path): return json.loads(path.read_text(encoding="utf-8"))
def jl(path): return [json.loads(s) for s in path.read_text(encoding="utf-8").splitlines() if s.strip()]
def git(repo,*args): return subprocess.check_output(["git","-C",str(repo),*args],text=True).strip()
def git_bytes(repo,*args): return subprocess.check_output(["git","-C",str(repo),*args])
def tokens(text):
    return {
      "placeholders":re.findall(r"\{[A-Za-z][A-Za-z0-9_]*\}",text),
      "markup":re.findall(r"</?[A-Za-z][^>]*>",text),
      "numeric":re.findall(r"(?<![A-Za-z])\d+(?:[.,]\d+)?%?(?![A-Za-z])",text),
    }
def verify_checksums(folder):
    entries=[]
    for line in (folder/"SHA256SUMS.txt").read_text(encoding="utf-8").splitlines():
        if not line.strip(): continue
        digest,name=line.split("  ",1)
        path=folder/name
        assert path.is_file() and sha(path.read_bytes())==digest,("checksum mismatch",str(path))
        entries.append(name)
    return len(entries)

parser=argparse.ArgumentParser()
parser.add_argument("--repo",required=True)
args=parser.parse_args()
repo=Path(args.repo).resolve()
summary=j(APP/"application-summary.json")
assert summary["baseHead"]==BASE and summary["productCommit"]==PRODUCT and summary["productTree"]==PRODUCT_TREE
assert git(repo,"cat-file","-e",PRODUCT+"^{commit}")==""
assert git(repo,"rev-parse",PRODUCT+"^{tree}")==PRODUCT_TREE
assert git(repo,"rev-parse",PRODUCT+"^")==BASE
assert git(repo,"diff-tree","--no-commit-id","--name-only","-r",PRODUCT).splitlines()==summary["changedCatalogPaths"]
assert not any(path.startswith(".github/workflows/") for path in summary["changedCatalogPaths"])

cf=EVIDENCE/"candidate-free-input"
primary=EVIDENCE/"primary-review"
blind=EVIDENCE/"blind-review"
cross=EVIDENCE/"independent-cross-review"
root=EVIDENCE/"root-cross-review"
assert verify_checksums(cf)>0 and verify_checksums(primary)>0 and verify_checksums(blind)>0 and verify_checksums(cross)>0 and verify_checksums(root)>0
manifest=j(cf/"manifest.json")
assert manifest["head"]==BASE and manifest["tree"]=="590ee410666905f68f601393b64a4798b0609181"
assert verify_checksums(APP)>0
primary_summary=j(primary/"SUMMARY.json")
blind_summary=j(blind/"summary.json")
cross_summary=j(cross/"SUMMARY.json")
root_summary=j(root/"SUMMARY.json")
assert primary_summary["head"]==blind_summary["head"]==cross_summary["head"]==root_summary["head"]==BASE
assert cross_summary["rootDisagreements"]==0 and cross_summary["cellCount"]==240 and cross_summary["rootOutcomesReviewed"]==13
assert root_summary["candidateFreeChecksumListSha256"]==sha((cf/"SHA256SUMS.txt").read_bytes())
assert blind_summary["candidateFreeInputChecksumListSha256"]==sha((cf/"SHA256SUMS.txt").read_bytes())

plan=jl(APP/"application-plan.jsonl")
readback=jl(APP/"readback-240-cells.jsonl")
assert len(plan)==13 and len(readback)==240
plan_by={(r["position"],r["locale"]):r for r in plan}
read_by={(r["position"],r["locale"]):r for r in readback}
assert len(plan_by)==13 and len(read_by)==240
cells=jl(cf/"current-target-cells.jsonl")
assert len(cells)==240
cell_by={(r["position"],r["locale"]):r for r in cells}
contexts={r["position"]:r for r in jl(cf/"source-contexts.jsonl")}
assert len(contexts)==20
changed_by_path={}
for key,r in plan_by.items():
    c=cell_by[key]; rb=read_by[key]
    assert r["status"]=="APPLIED" and r["baseHead"]==BASE and r["productCommit"]==PRODUCT
    assert r["currentTargetSha256"]==shat(r["currentTarget"])
    assert r["targetSha256"]==shat(r["target"])
    assert r["catalogPath"]==c["catalogPath"] and r["sourceKey"]==c["sourceKey"]
    changed_by_path.setdefault(r["catalogPath"],{})[r["sourceKey"]]=r["target"]
    assert rb["expectedTarget"]==r["target"] and rb["postimageTarget"]==r["target"]
for key,c in cell_by.items():
    rb=read_by[key]
    path=c["catalogPath"]
    target=git_bytes(repo,"show",PRODUCT+":"+path)
    obj=json.loads(target.decode("utf-8"))
    expected=plan_by[key]["target"] if key in plan_by else c["currentTarget"]
    assert obj[c["sourceKey"]]==expected and shat(obj[c["sourceKey"]])==rb["expectedTargetSha256"]
    assert rb["matchesPlan"] is True and rb["postimageTargetSha256"]==shat(obj[c["sourceKey"]])
    assert tokens(c["sourceKey"])==tokens(obj[c["sourceKey"]])
for path,expected_changes in changed_by_path.items():
    old=json.loads(git_bytes(repo,"show",BASE+":"+path).decode("utf-8"))
    new=json.loads(git_bytes(repo,"show",PRODUCT+":"+path).decode("utf-8"))
    assert list(old)==list(new) and set(old)==set(new)
    actual={key:value for key,value in new.items() if old[key]!=value}
    assert actual==expected_changes,("unexpected value or non-target catalog change",path)
pins=j(cf/"catalog-file-pins.json")["localeCatalogs"]
key_readback=j(APP/"catalog-key-order-readback.json")
assert len(key_readback)==12
for row in key_readback:
    pin=pins[row["locale"]]
    obj=json.loads(git_bytes(repo,"show",PRODUCT+":"+pin["path"]).decode("utf-8"))
    ordered=sha(("\n".join(obj)+"\n").encode("utf-8"))
    sorted_set=sha(("\n".join(sorted(obj))+"\n").encode("utf-8"))
    assert len(obj)==5441 and ordered==pin["orderedKeySha256"]
    assert sorted_set==j(cf/"catalog-file-pins.json")["sourceLookupKeyOrderSha256"]
    assert row["postimageFileSha256"]==sha(git_bytes(repo,"show",PRODUCT+":"+pin["path"]))

print(json.dumps({
 "result":"PASS","base":BASE,"product":PRODUCT,"productTree":PRODUCT_TREE,
 "cells":240,"applied":13,"unchanged":227,"holds":0,"catalogs":8,
 "catalogKeySetsAndOrder":"PASS","nonTargetValues":"UNCHANGED",
 "placeholderMarkupNumericTokens":"PASS","evidencePackets":"PASS"
},indent=2))
