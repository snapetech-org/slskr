#!/usr/bin/env python3
import hashlib, json, re
from pathlib import Path
ROOT=Path(__file__).resolve().parent
def digest(data): return hashlib.sha256(data).hexdigest()
def load_jsonl(path): return [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines() if x]
def key(r): return (r["position"],r["sourceKey"],r["locale"])
def verify_manifest(folder, manifest):
    for line in (folder/manifest).read_text(encoding="utf-8").splitlines():
        if not line.strip(): continue
        want,rel=line.split("  ",1)
        f=folder/rel
        assert f.is_file(), f"missing: {f}"
        assert digest(f.read_bytes())==want, f"checksum mismatch: {f}"
verify_manifest(ROOT/"candidate-free-input","SHA256SUMS.txt")
verify_manifest(ROOT/"primary-review","SHA256SUMS.txt")
verify_manifest(ROOT/"blind-review","BLIND-SHA256SUMS.txt")
inputs=load_jsonl(ROOT/"candidate-free-input/current-target-cells.jsonl")
primary=load_jsonl(ROOT/"primary-review/ledger.jsonl")
blind=load_jsonl(ROOT/"blind-review/blind-ledger.jsonl")
cross=load_jsonl(ROOT/"cross-audit-ledger.jsonl")
selected=load_jsonl(ROOT/"selected-changes.jsonl")
maps=[{key(x):x for x in rows} for rows in [inputs,primary,blind,cross]]
im,pm,bm,cm=maps
assert all(len(m)==240 for m in maps)
assert set(im)==set(pm)==set(bm)==set(cm)
head="4b6f9b925ac7ec1243f3003fa0792c3b50e4560e"
tree="31c708cdb279e427ddb2082e297be382209489d3"
for k,i in im.items():
    p,b,c=pm[k],bm[k],cm[k]
    assert i["head"]==p["head"]==b["head"]==c["head"]==head
    assert i["tree"]==p["tree"]==b["tree"]==c["tree"]==tree
    for row in [p,b,c]:
        assert row["currentTarget"]==i["currentTarget"]
        assert row["currentTargetSha256"]==i["currentTargetSha256"]==digest(i["currentTarget"].encode())
        assert row["sourceKey"]==i["sourceKey"]
        assert row["sourceKeySha256"]==i["sourceKeySha256"]==digest(i["sourceKey"].encode())
    assert p["placeholderCheck"]["status"]=="pass"
    assert p["markupCheck"]["status"]=="pass"
    assert p["numericCheck"]["status"]=="pass"
    assert p["technicalLiteralCheck"]["status"]=="pass"
    assert c["rootTargetSha256"]==digest(c["rootTarget"].encode())
    assert c["rootTarget"]==i["currentTarget"] or c["selectedForApplication"] is True
    tokens=re.findall(r"[{][^{}]+[}]",c["rootTarget"])
    assert tokens==i.get("sourcePlaceholders",[]), (k,tokens,i.get("sourcePlaceholders",[]))
    assert c["placeholderSequenceMatches"] is True
    for literal in (b.get("protectedLiterals") or []):
        assert literal in c["rootTarget"], (k,literal,c["rootTarget"])
expected=[c for c in cross if c["rootTarget"]!=c["currentTarget"]]
assert len(expected)==len(selected)==68
assert {(x["position"],x["sourceKey"],x["locale"],x["rootTarget"],x["rootTargetSha256"]) for x in expected} == {
    (x["position"],x["sourceKey"],x["locale"],x["target"],x["targetSha256"]) for x in selected
}
summary=json.loads((ROOT/"summary.json").read_text(encoding="utf-8"))
auth=json.loads((ROOT/"root-application-authorization.json").read_text(encoding="utf-8"))
assert summary["cellCount"]==240 and summary["selectedChangeCount"]==68 and summary["holds"]==0
assert auth["applicationApproved"] is True and auth["selectedChangeCount"]==68
assert auth["selectedChangesSha256"]==digest((ROOT/"selected-changes.jsonl").read_bytes())
assert auth["reviewedPackets"]["crossAuditLedgerSha256"]==digest((ROOT/"cross-audit-ledger.jsonl").read_bytes())
assert auth["nativeSpeakerApproval"] is False and auth["releaseApproved"] is False
print(json.dumps({"result":"PASS","cells":240,"rootDispositions":summary["rootDispositions"],"selected":68,"holds":0,"placeholderMarkupNumericTechnicalChecks":"PASS","allNestedChecksumsVerified":True},ensure_ascii=False,indent=2))
