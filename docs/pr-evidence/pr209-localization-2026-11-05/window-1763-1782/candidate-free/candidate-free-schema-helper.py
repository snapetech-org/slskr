#!/usr/bin/env python3
"""Exact source and caller extraction helpers for slskR PR #209 localization review."""
import hashlib
import re
from collections import Counter
from pathlib import Path

LOCALES = ["es", "zh-Hans", "hi", "de", "ja", "fr", "pt-BR", "ar", "ko", "zh-Hant", "vi", "id"]
RUNTIME = "web/src/lib/interfaceLocale.js"


def sha(value):
    if isinstance(value, str):
        value = value.encode("utf-8")
    return hashlib.sha256(value).hexdigest()


def canon(value):
    import json
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def production_path(path):
    lower = "/" + path.lower()
    return path.startswith("web/src/") and path.endswith((".js", ".jsx", ".ts", ".tsx")) and not any(
        item in lower for item in ("/__tests__/", ".test.", ".spec.", "storybook", "/fixtures/", "/fixture/", "/docs/")
    )


def unescape_js(value):
    output, index = [], 0
    simple = {"\\": "\\", "'": "'", '"': '"', "n": "\n", "r": "\r", "t": "\t", "b": "\b", "f": "\f", "v": "\v", "0": "\0"}
    while index < len(value):
        if value[index] != "\\":
            output.append(value[index]); index += 1; continue
        index += 1
        if index >= len(value):
            output.append("\\"); break
        char = value[index]
        if char in simple:
            output.append(simple[char]); index += 1
        elif char == "x" and index + 2 < len(value) and re.fullmatch(r"[0-9a-fA-F]{2}", value[index+1:index+3]):
            output.append(chr(int(value[index+1:index+3], 16))); index += 3
        elif char == "u" and index + 1 < len(value) and value[index+1] == "{":
            close = value.find("}", index + 2)
            try:
                output.append(chr(int(value[index+2:close], 16))); index = close + 1
            except Exception:
                output.extend(["\\", "u"]); index += 1
        elif char == "u" and index + 4 < len(value) and re.fullmatch(r"[0-9a-fA-F]{4}", value[index+1:index+5]):
            output.append(chr(int(value[index+1:index+5], 16))); index += 5
        else:
            output.append(char); index += 1
    return "".join(output)


def scan_quoted(text):
    block = template = False
    for line_number, line in enumerate(text.splitlines(), 1):
        values, index = [], 0
        while index < len(line):
            if template:
                if line[index] == "\\": index += 2
                elif ord(line[index]) == 96: template = False; index += 1
                else: index += 1
                continue
            if block:
                close = line.find("*/", index)
                if close < 0: break
                block = False; index = close + 2; continue
            if line.startswith("//", index): break
            if line.startswith("/*", index): block = True; index += 2; continue
            quote = line[index]
            if ord(quote) == 96: template = True; index += 1; continue
            if quote not in ("'", '"'): index += 1; continue
            start = index + 1; index = start
            while index < len(line):
                if line[index] == "\\": index += 2
                elif line[index] == quote:
                    values.append(unescape_js(line[start:index])); index += 1; break
                else: index += 1
        yield line_number, line, values


def tokens(value):
    placeholders = re.findall(r"\{[A-Za-z][A-Za-z0-9_]*\}", value)
    markup = re.findall(r"</?[A-Za-z][^>]*>", value)
    numbers = re.findall(r"(?<![A-Za-z])\d+(?:[.,]\d+)?%?(?![A-Za-z])", value)
    protected = []
    for item in re.findall(r"(?<![A-Za-z0-9])(?:[A-Z]{2,}[A-Z0-9]*|ffmpeg|Chromaprint|Soulseek|Spotify|YouTube|Pushbullet|Matrix|WebSocket|OpenAI)(?![A-Za-z0-9])", value):
        if item not in protected: protected.append(item)
    return placeholders, markup, numbers, protected


def contexts_for(repo, keys, start, end):
    by_key = {key: [] for key in keys}
    tracked = __import__("subprocess").check_output(["git", "-C", str(repo), "ls-files", "-z"], text=True).split("\0")
    files = [path for path in tracked if path and production_path(path)]
    for relative in files:
        file_path = repo / relative
        raw = file_path.read_bytes()
        text = raw.decode("utf-8")
        lines = text.splitlines()
        blob = __import__("subprocess").check_output(["git", "-C", str(repo), "rev-parse", f"HEAD:{relative}"], text=True).strip()
        for line_number, line, values in scan_quoted(text):
            counts = Counter(value for value in values if value in by_key)
            for key, count in counts.items():
                first, last = max(1, line_number - 4), min(len(lines), line_number + 4)
                context = [{"line": number, "text": lines[number-1]} for number in range(first, last + 1)]
                by_key[key].append({
                    "path": relative, "line": line_number, "lineText": line, "lineSha256": sha(line),
                    "literalOccurrenceCount": count, "contextStartLine": first, "contextEndLine": last,
                    "context": context, "contextSha256": sha(canon(context)), "fileBytes": len(raw),
                    "fileSha256": sha(raw), "gitBlob": blob,
                })
    rows, holds = [], []
    for position in range(start, end + 1):
        key = keys[position-start]
        callers = sorted(by_key[key], key=lambda item: (item["path"], item["line"]))
        row = {"position": position, "sourceKey": key, "sourceKeySha256": sha(key),
               "callerScan": "Exact quoted JS/TS string-literal scan of tracked production web/src; tests, catalogs, docs, fixtures, Storybook, comments, and template literals excluded.",
               "productionCallerCount": len(callers), "callerOccurrenceCount": sum(item["literalOccurrenceCount"] for item in callers),
               "callers": callers}
        row["callerContextSha256"] = sha(canon({"sourceKey": key, "callers": callers}))
        rows.append(row)
        if not callers:
            holds.append({"position": position, "sourceKeySha256": sha(key),
                          "reason": "No exact quoted production web/src caller resolved by the pinned scan; target text remains hash-only."})
    return rows, holds, len(files)


def runtime_context(repo):
    import subprocess
    path = repo / RUNTIME
    lines = path.read_text(encoding="utf-8").splitlines()
    markers = ["export const INTERFACE_LANGUAGE_OPTIONS", "const translationFor =", "const replaceInterfaceValues =", "const formatInterfaceTextForLanguage ="]
    blocks = []
    for marker in markers:
        index = next((i for i, line in enumerate(lines) if marker in line), None)
        if index is None: raise RuntimeError("missing runtime marker " + marker)
        first, last = max(0, index - 1), min(len(lines), index + 11)
        blocks.append({"marker": marker, "startLine": first + 1, "endLine": last,
                       "lines": [{"line": i + 1, "text": lines[i], "lineSha256": sha(lines[i])} for i in range(first, last)]})
    return {"path": RUNTIME, "pin": {"path": RUNTIME, "byteCount": path.stat().st_size,
            "lineCount": len(lines), "sha256": sha(path.read_bytes()),
            "gitBlob": subprocess.check_output(["git", "-C", str(repo), "rev-parse", f"HEAD:{RUNTIME}"], text=True).strip()},
            "localeOptionOrder": LOCALES, "lookupAndPlaceholderContext": blocks,
            "note": "Locale lookup and named-placeholder behavior are pinned to this exact source revision; caller values remain opaque."}
