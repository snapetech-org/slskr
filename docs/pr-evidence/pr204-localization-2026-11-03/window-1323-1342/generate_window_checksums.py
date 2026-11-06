#!/usr/bin/env python3
import hashlib
from pathlib import Path

root = Path(__file__).resolve().parent
checksum_path = root / "SHA256SUMS.txt"
files = sorted(path for path in root.rglob("*") if path.is_file() and path != checksum_path)
lines = [
    f"{hashlib.sha256(path.read_bytes()).hexdigest()}  {path.relative_to(root).as_posix()}"
    for path in files
]
checksum_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
print(f"wrote {len(lines)} evidence checksums to {checksum_path}")
