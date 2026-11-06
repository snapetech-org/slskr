#!/usr/bin/env python3
from pathlib import Path
import hashlib,json,sys
repo=Path(sys.argv[1]).resolve()
e=repo/"docs/pr-evidence/pr204-localization-2026-11-03/window-1383-1402/application"
sha=lambda b:hashlib.sha256(b).hexdigest()
rows=[json.loads(x) for x in (e/"readback.jsonl").read_text(encoding="utf-8").splitlines() if x]
assert len(rows)==240 and all(r["matchesPlan"] for r in rows)
inv=json.loads((e/"catalog-invariants.json").read_text(encoding="utf-8"))
assert len(inv)==12 and sum(r["pluralObjectCount"] for r in inv)==15 and all(r["entryCount"]==5441 and r["orderedKeySetAndOrderPreserved"] and r["validNonemptyStringOrPluralValues"] for r in inv)
for r in rows:
 data=json.loads((repo/r["catalogPath"]).read_text(encoding="utf-8"))
 value=data[r["sourceKey"]]
 assert value==r["actualTarget"] and sha(value.encode())==r["actualTargetSha256"]
summary=json.loads((e/"application-summary.json").read_text(encoding="utf-8"))
assert summary["changedCells"]==57 and summary["newHolds"]==0 and summary["readbackMismatches"]==0
print(json.dumps({"pass":True,"cells":len(rows),"catalogs":len(inv),"updates":57,"preservedHolds":35,"arabicPluralMaps":15},indent=2))
