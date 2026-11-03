#!/usr/bin/env python3
import hashlib,json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parent

def fail(m):raise SystemExit("FAIL: "+m)
def sha(b):return hashlib.sha256(b).hexdigest()
def verify_sums():
    p=ROOT/"SHA256SUMS.txt"
    if not p.is_file():fail("missing root SHA256SUMS.txt")
    entries={}
    for line in p.read_text(encoding="utf-8").splitlines():
        if not line:continue
        if len(line)<66 or line[64:66]!="  ":fail("malformed root checksum line")
        digest=line[:64];name=line[66:].lstrip("*")
        if name in entries:fail("duplicate root checksum "+name)
        target=ROOT/name
        if not target.is_file() or sha(target.read_bytes())!=digest:fail("root checksum mismatch "+name)
        entries[name]=digest
    actual={p.relative_to(ROOT).as_posix() for p in ROOT.rglob("*") if p.is_file() and p not in {ROOT/"SHA256SUMS.txt",ROOT/"SHA256SUMS.txt.sha256"}}
    if set(entries)!=actual:fail("root checksum coverage mismatch")
    return len(entries)

def main():
    count=verify_sums()
    cf=ROOT/"candidate-free-input"
    primary=ROOT/"primary-review"
    subprocess.check_call(["python3",str(cf/"verify-candidate-free.py")],stdout=subprocess.DEVNULL)
    subprocess.check_call(["python3",str(primary/"verify_primary.py")],stdout=subprocess.DEVNULL)
    for p in cf.rglob("*"):
        if not p.is_file():continue
        rel=p.relative_to(cf)
        embedded=primary/"evidence/candidate-free-input"/rel
        if not embedded.is_file() or embedded.read_bytes()!=p.read_bytes():fail("primary embedded input differs "+str(rel))
    manifest=json.loads((ROOT/"packet-manifest.json").read_text(encoding="utf-8"))
    need={"head":"44b37bd94385128d5bb5287aa1545901282bdfcb","tree":"02c3f149a079c67b010d973dd02ca15776ad1610","window":"W1443-W1462","cellCount":240,"sourceCount":20,"localeCount":12,"decisionCounts":{"accept-current":182,"correction":46,"refinement":12},"proposalCount":58,"carriedHoldCount":35,"priorSelectionRows":200,"sourcePinCount":29,"callerReferences":27,"callerFiles":16}
    for k,v in need.items():
        if manifest.get(k)!=v:fail("packet-manifest mismatch "+k)
    live=json.loads((ROOT/"final-live-check.json").read_text(encoding="utf-8"))
    if not live.get("allChecksPass") or live.get("reviewHead")!=manifest["head"] or live.get("reviewTree")!=manifest["tree"] or live.get("sourcePinCount")!=29 or live.get("currentTargetCellsRechecked")!=240:fail("final live check mismatch")
    for stage in ("before","after"):
        o=live[stage]
        if o["state"]!="OPEN" or o["draft"] is not True or o["head"]!=manifest["head"] or o["tree"]!=manifest["tree"] or o["baseRef"]!="main" or o["baseSha"]!="2a2b188f10b9460a15bc6d5c34e406b0193d51ba":fail("live PR pin mismatch "+stage)
        if o["refs"]!={"refs/heads/codex/slskr-l10n-audit-20261030":manifest["head"],"refs/pull/204/head":manifest["head"]}:fail("live refs mismatch "+stage)
    print(json.dumps({"result":"PASS","bundleFilesChecked":count,"candidateFreeCells":240,"primaryCells":240,"decisions":manifest["decisionCounts"],"proposals":58,"sourcePins":29,"callerRefs":27,"carriedHolds":35,"priorSelections":200,"head":manifest["head"],"tree":manifest["tree"]},ensure_ascii=False,indent=2))
if __name__=="__main__":main()
