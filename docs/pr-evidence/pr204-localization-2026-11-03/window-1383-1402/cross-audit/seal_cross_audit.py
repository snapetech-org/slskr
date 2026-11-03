#!/usr/bin/env python3
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json

O=Path(__file__).resolve().parent
def sha(b): return hashlib.sha256(b).hexdigest()
files=sorted(p for p in O.rglob("*") if p.is_file() and p.relative_to(O).as_posix() not in {"manifest.json","SHA256SUMS.txt"})
manifest={
 "schemaVersion":1,
 "repository":"snapetech-org/slskR",
 "pullRequest":204,
 "window":"W1383-W1402",
 "head":"b5da2589b6e8f2d4b0c0faab28bcdf0481e42438",
 "tree":"36ae6ecf3b705995fbd549cb8650d6458936df91",
 "createdAtUtc":datetime.now(timezone.utc).isoformat(),
 "fileHashes":{p.relative_to(O).as_posix():{"sha256":sha(p.read_bytes()),"bytes":p.stat().st_size} for p in files}
}
(O/"manifest.json").write_text(json.dumps(manifest,ensure_ascii=False,sort_keys=True,indent=2)+"\n",encoding="utf-8")
files=sorted(p for p in O.rglob("*") if p.is_file() and p.relative_to(O).as_posix()!="SHA256SUMS.txt")
(O/"SHA256SUMS.txt").write_text("".join(f"{sha(p.read_bytes())}  {p.relative_to(O).as_posix()}\n" for p in files),encoding="utf-8")
print(json.dumps({"manifestFiles":len(manifest["fileHashes"]),"checksumFiles":len(files),"manifestSha256":sha((O/"manifest.json").read_bytes()),"checksumListSha256":sha((O/"SHA256SUMS.txt").read_bytes())},indent=2))
