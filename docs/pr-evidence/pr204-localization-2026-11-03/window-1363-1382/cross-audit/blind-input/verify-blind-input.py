#!/usr/bin/env python3
import hashlib, json
from pathlib import Path
ROOT = Path(__file__).resolve().parent
def sha(b): return hashlib.sha256(b).hexdigest()
def sha_text(s): return sha(s.encode("utf-8"))
def canon(x): return json.dumps(x, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
def readj(p): return json.loads(p.read_text(encoding="utf-8"))
def readjl(p): return [json.loads(line) for line in p.read_text(encoding="utf-8").splitlines() if line]
FORBIDDEN_KEYS = ("target", "candidate", "proposal", "review", "disposition", "translation", "glossary")
def check_keys(value):
    if isinstance(value, dict):
        for key, child in value.items():
            low = key.lower()
            assert not any(term in low for term in FORBIDDEN_KEYS), key
            check_keys(child)
    elif isinstance(value, list):
        for child in value: check_keys(child)
m = readj(ROOT / "manifest.json")
assert m["head"] == "281c39ec0cdb3677d7d523b7c4f0cd0d52bbf14c"
assert m["tree"] == "777b234b1aa3cb7a2c9fd560b2c0fecc4e7fe49d"
assert m["positions"] == [1363, 1382] and m["promptCount"] == 240
entries = []
for line in (ROOT / "SHA256SUMS.txt").read_text(encoding="utf-8").splitlines():
    digest, name = line.split(None, 1); name = name.lstrip("* "); entries.append((name, digest))
assert len(entries) == len({name for name, _ in entries})
assert {name for name, _ in entries} == {p.name for p in ROOT.iterdir() if p.is_file() and p.name != "SHA256SUMS.txt"}
for name, digest in entries: assert sha((ROOT / name).read_bytes()) == digest, name
for name, pin in m["fileHashes"].items(): assert sha((ROOT / name).read_bytes()) == pin["sha256"], name
contexts = readjl(ROOT / "source-contexts.jsonl")
prompts = readjl(ROOT / "prompts.jsonl")
assert len(contexts) == 20 and [r["position"] for r in contexts] == list(range(1363, 1383))
assert len(prompts) == 240 and len({(r["position"], r["locale"]) for r in prompts}) == 240
locales = ["es", "zh-Hans", "hi", "de", "ja", "fr", "pt-BR", "ar", "ko", "zh-Hant", "vi", "id"]
names = {"es":"Spanish","zh-Hans":"Simplified Chinese","hi":"Hindi","de":"German","ja":"Japanese","fr":"French","pt-BR":"Brazilian Portuguese","ar":"Arabic","ko":"Korean","zh-Hant":"Traditional Chinese","vi":"Vietnamese","id":"Indonesian"}
assert m["localeOrder"] == locales and m["localeNames"] == names
assert sha((ROOT / "source-contexts.jsonl").read_bytes()) == m["sourceContextFileSha256"]
by_pos = {r["position"]: r for r in contexts}
for r in contexts:
    assert r["sourceKeySha256"] == sha_text(r["sourceKey"])
    assert r["callerContextSha256"] == sha_text(canon({"sourceKey": r["sourceKey"], "callers": r["callers"]}))
for prompt in prompts:
    r = by_pos[prompt["position"]]
    assert prompt["sourceKey"] == r["sourceKey"]
    assert prompt["sourceKeySha256"] == r["sourceKeySha256"]
    assert prompt["localeName"] == names[prompt["locale"]]
    assert prompt["sourceContextRef"] == {"file":"source-contexts.jsonl","position":r["position"],"sourceContextSha256":r["callerContextSha256"],"callerCount":r["productionCallerCount"],"callerOccurrenceCount":r["callerOccurrenceCount"]}
    expected = [{"path":c["path"],"fileSha256":c["fileSha256"],"gitBlob":c["gitBlob"],"line":c["line"],"lineSha256":c["lineSha256"],"contextStartLine":c["contextStartLine"],"contextEndLine":c["contextEndLine"],"contextSha256":c["contextSha256"],"literalOccurrenceCount":c["literalOccurrenceCount"]} for c in r["callers"]]
    assert prompt["callerRefs"] == expected
    assert prompt["taskInstruction"]
    assert set(prompt) == {"position","sourceKey","sourceKeySha256","locale","localeName","sourceContextRef","callerRefs","taskInstruction"}
assert by_pos[1376]["productionCallerCount"] == 0 and by_pos[1376]["callers"] == []
assert all((r["position"] == 1376) == (r["sourceContextRef"]["callerCount"] == 0) for r in prompts)
for name in ("manifest.json", "prompts.jsonl", "source-contexts.jsonl"):
    check_keys(readj(ROOT / name) if name == "manifest.json" else readjl(ROOT / name))
print(json.dumps({"result":"PASS","head":m["head"],"tree":m["tree"],"sourceCount":len(contexts),"localeCount":len(locales),"promptCount":len(prompts),"sourceContextSha256":m["sourceContextFileSha256"],"callerlessPositions":[p for p,r in by_pos.items() if not r["callers"]],"forbiddenFieldKeysFound":[],"manifestSha256":sha((ROOT/"manifest.json").read_bytes()),"checksumListSha256":sha((ROOT/"SHA256SUMS.txt").read_bytes())},ensure_ascii=False,indent=2))
