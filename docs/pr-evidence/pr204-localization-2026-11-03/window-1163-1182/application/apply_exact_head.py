#!/usr/bin/env python3
import hashlib, json, pathlib, subprocess, sys
repo=pathlib.Path(sys.argv[1]).resolve()
evidence=pathlib.Path(sys.argv[2]).resolve()
plan=[json.loads(x) for x in (evidence/"apply-plan.jsonl").read_text().splitlines()]
expected_head="9aa58492ee693d8ca0f2c027a3ee5b8438639f91"
head=subprocess.check_output(["git","rev-parse","HEAD"],cwd=repo,text=True).strip()
assert head==expected_head, (head,expected_head)
assert not subprocess.check_output(["git","status","--porcelain"],cwd=repo,text=True).strip()
paths=sorted({x["catalogPath"] for x in plan})
objects={}
for rel in paths:
    path=repo/rel
    raw=path.read_text()
    obj=json.loads(raw)
    assert raw==json.dumps(obj,ensure_ascii=False,indent=2)+"\n", f"unexpected JSON formatting: {rel}"
    objects[rel]=obj
for item in plan:
    obj=objects[item["catalogPath"]]
    old=obj[item["sourceId"]]
    assert old==item["expectedCurrent"], (item["position"],item["locale"],"current value changed")
    assert hashlib.sha256(old.encode()).hexdigest()==item["expectedCurrentSha256"]
for item in plan:
    objects[item["catalogPath"]][item["sourceId"]]=item["target"]
for rel,obj in objects.items():
    (repo/rel).write_text(json.dumps(obj,ensure_ascii=False,indent=2)+"\n")
readback=[]
for item in plan:
    value=json.loads((repo/item["catalogPath"]).read_text())[item["sourceId"]]
    assert value==item["target"]
    assert hashlib.sha256(value.encode()).hexdigest()==item["targetSha256"]
    readback.append({"catalogPath":item["catalogPath"],"locale":item["locale"],"position":item["position"],"sourceId":item["sourceId"],"target":value,"targetSha256":item["targetSha256"]})
(evidence/"application"/"readback.jsonl").write_text("".join(json.dumps(x,ensure_ascii=False,sort_keys=True)+"\n" for x in readback))
changed=subprocess.check_output(["git","diff","--name-only"],cwd=repo,text=True).splitlines()
assert sorted(changed)==paths,(changed,paths)
assert not any(x.startswith(".github/workflows/") for x in changed)
print(json.dumps({"baseHead":head,"changes":len(plan),"catalogFiles":len(paths),"changedFiles":changed,"readbackCells":len(readback)},ensure_ascii=False))
