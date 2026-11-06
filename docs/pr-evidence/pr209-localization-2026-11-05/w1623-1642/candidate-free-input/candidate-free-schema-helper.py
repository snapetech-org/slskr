#!/usr/bin/env python3
"""Pinned schema helpers for exact source, caller-context, token, and PR attestations."""
import hashlib, json, re, subprocess
from collections import Counter
from pathlib import Path
R=Path(__file__).resolve().parent
REPO=Path("/mnt/disks/scratch/task-worktrees/localization-20261104/slskr-pr209-w1583-1602-source")
PREV=Path("/home/keith/Documents/code/task-scratch/slskr-pr209-w1563-1582-primary-20261104/candidate-free-input")
APP=REPO/"docs/pr-evidence/pr209-localization-2026-11-04/window-1563-1582/application"
HEAD="e1ccc3d6509baf957f3039046e5b66dda3ae15d0"
TREE="d7c7aa967cb7faf51a8211a397859feebe8129b8"
BASE_SHA="1bbaec9fdc63a86de343e37e33bae70d44301a36"
REPO_NAME="snapetech-org/slskR"; PR=209; BRANCH="codex/slskr-l10n-audit-20261104-resync"
LOCS=["es", "zh-Hans", "hi", "de", "ja", "fr", "pt-BR", "ar", "ko", "zh-Hant", "vi", "id"]
START, END = 1583, 1602
CAT = "web/src/lib/locales"
RUNTIME = "web/src/lib/interfaceLocale.js"

def sha(x):
    if isinstance(x, str): x = x.encode()
    return hashlib.sha256(x).hexdigest()

def canon(x): return json.dumps(x, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
def wj(path, x): path.write_text(json.dumps(x, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
def wjl(path, xs): path.write_text("".join(canon(x) + "\n" for x in xs), encoding="utf-8")
def git(*args): return subprocess.check_output(["git", *args], cwd=REPO).decode().strip()
def api(endpoint): return json.loads(subprocess.check_output(["gh", "api", endpoint], text=True))
def api_rows(endpoint, expr):
    out = subprocess.check_output(["gh", "api", "--paginate", "--jq", expr, endpoint], text=True)
    return [json.loads(s) for s in out.splitlines() if s.strip()]
def remote_ref(ref):
    out = subprocess.check_output(["git", "ls-remote", "origin", ref], cwd=REPO, text=True).strip()
    return out.split()[0] if out else None

def production_path(p):
    q = "/" + p.lower()
    return p.startswith("web/src/") and p.endswith((".js", ".jsx", ".ts", ".tsx")) and not any(
        x in q for x in ("/__tests__/", ".test.", ".spec.", "storybook", "/fixtures/", "/fixture/", "/docs/")
    )

def unescape_js(s):
    out, i = [], 0
    simple = {"\\": "\\", "'": "'", '"': '"', "n": "\n", "r": "\r", "t": "\t", "b": "\b", "f": "\f", "v": "\v", "0": "\0"}
    while i < len(s):
        if s[i] != "\\": out.append(s[i]); i += 1; continue
        i += 1
        if i >= len(s): out.append("\\"); break
        ch = s[i]
        if ch in simple: out.append(simple[ch]); i += 1
        elif ch == "x" and i + 2 < len(s) and re.fullmatch(r"[0-9a-fA-F]{2}", s[i+1:i+3]):
            out.append(chr(int(s[i+1:i+3], 16))); i += 3
        elif ch == "u" and i + 1 < len(s) and s[i+1] == "{":
            j = s.find("}", i+2)
            try: out.append(chr(int(s[i+2:j], 16))); i = j + 1
            except Exception: out.extend(["\\", "u"]); i += 1
        elif ch == "u" and i + 4 < len(s) and re.fullmatch(r"[0-9a-fA-F]{4}", s[i+1:i+5]):
            out.append(chr(int(s[i+1:i+5], 16))); i += 5
        else: out.append(ch); i += 1
    return "".join(out)

def scan_quoted(text):
    block = template = False
    for ln, line in enumerate(text.splitlines(), 1):
        vals, i = [], 0
        while i < len(line):
            if template:
                if line[i] == "\\": i += 2
                elif ord(line[i]) == 96: template = False; i += 1
                else: i += 1
                continue
            if block:
                j = line.find("*/", i)
                if j < 0: break
                block = False; i = j + 2; continue
            if line.startswith("//", i): break
            if line.startswith("/*", i): block = True; i += 2; continue
            q = line[i]
            if ord(q) == 96: template = True; i += 1; continue
            if q not in ("'", '"'): i += 1; continue
            a = i + 1; i = a
            while i < len(line):
                if line[i] == "\\": i += 2
                elif line[i] == q: vals.append(unescape_js(line[a:i])); i += 1; break
                else: i += 1
        yield ln, line, vals

def toks(s):
    p = re.findall(r"\{[A-Za-z][A-Za-z0-9_]*\}", s)
    m = re.findall(r"</?[A-Za-z][^>]*>", s)
    n = re.findall(r"(?<![A-Za-z])\d+(?:[.,]\d+)?%?(?![A-Za-z])", s)
    z = []
    for x in re.findall(r"(?<![A-Za-z0-9])(?:[A-Z]{2,}[A-Z0-9]*|ffmpeg|Chromaprint|Soulseek|Spotify|YouTube|Pushbullet|Matrix|WebSocket|OpenAI)(?![A-Za-z0-9])", s):
        if x not in z: z.append(x)
    return p, m, n, z

def pr_attestation(at):
    pr = json.loads(subprocess.check_output(["gh", "pr", "view", str(PR), "--repo", REPO_NAME, "--json", "state,isDraft,headRefOid,baseRefOid,url,headRefName,baseRefName"], text=True))
    head = pr["headRefOid"]
    tree = api(f"repos/{REPO_NAME}/commits/{head}")["commit"]["tree"]["sha"]
    d = api_rows(f"repos/{REPO_NAME}/deployments?sha={head}&per_page=100", ".[] | @json")
    rd = api_rows(f"repos/{REPO_NAME}/deployments?per_page=100", ".[] | @json")
    runs = api_rows(f"repos/{REPO_NAME}/actions/runs?head_sha={head}&per_page=100", ".workflow_runs[] | @json")
    lh, lt = git("rev-parse", "HEAD"), git("rev-parse", "HEAD^{tree}")
    clean = not bool(git("status", "--porcelain"))
    branch_sha, pull_sha = remote_ref(f"refs/heads/{pr['headRefName']}"), remote_ref(f"refs/pull/{PR}/head")
    main_sha = api(f"repos/{REPO_NAME}/git/ref/heads/main")["object"]["sha"]
    out = {
        "capturedAtUtc": at, "repository": REPO_NAME, "pullRequest": PR,
        "state": pr["state"].upper(), "draft": pr["isDraft"], "head": head, "tree": tree,
        "headRef": pr["headRefName"], "branchRef": branch_sha, "pullRef": pull_sha,
        "baseRef": pr["baseRefName"], "baseSha": pr["baseRefOid"], "mainRef": main_sha,
        "localHead": lh, "localTree": lt, "localBranch": "(detached)", "localWorktreeClean": clean,
        "deploymentsForHeadCount": len(d), "deploymentsForHeadSha256": sha(canon(d)),
        "repositoryDeploymentCount": len(rd), "repositoryDeploymentsSha256": sha(canon(rd)),
        "actionsRunsForHeadCount": len(runs), "deploymentActionsIssuedByReview": 0, "url": pr["url"],
    }
    if (pr["state"].upper(), pr["isDraft"], head, tree, pr["baseRefName"], pr["baseRefOid"]) != ("OPEN", True, HEAD, TREE, "main", BASE_SHA):
        raise RuntimeError("live PR state or exact head/tree/base changed")
    if branch_sha != HEAD or pull_sha != HEAD: raise RuntimeError("remote branch/pull refs mismatch")
    if (lh, lt, clean) != (HEAD, TREE, True): raise RuntimeError("local isolated source checkout mismatch")
    return out

def contexts_for(keys):
    files = [p for p in git("ls-files", "-z").split("\0") if p and production_path(p)]
    by_key = {k: [] for k in keys}
    for p in files:
        full = REPO / p
        txt = full.read_text(encoding="utf-8")
        lines = txt.splitlines()
        blob = git("rev-parse", f"HEAD:{p}")
        fh, size = sha(full.read_bytes()), full.stat().st_size
        for ln, line, vals in scan_quoted(txt):
            counts = Counter(x for x in vals if x in by_key)
            for key, count in counts.items():
                lo, hi = max(1, ln - 4), min(len(lines), ln + 4)
                ctx = [{"line": k, "text": lines[k-1]} for k in range(lo, hi+1)]
                by_key[key].append({
                    "path": p, "line": ln, "lineText": line, "lineSha256": sha(line),
                    "literalOccurrenceCount": count, "contextStartLine": lo, "contextEndLine": hi,
                    "context": ctx, "contextSha256": sha(canon(ctx)),
                    "fileBytes": size, "fileSha256": fh, "gitBlob": blob,
                })
    rows, holds = [], []
    for pos in range(START, END+1):
        key = keys[pos-START]
        cs = sorted(by_key[key], key=lambda x:(x["path"],x["line"]))
        row = {
            "position": pos, "historicalSourceOrdinal": None, "sourceKey": key, "sourceKeySha256": sha(key),
            "callerScan": "Exact quoted JS/TS string-literal scan of tracked production web/src; tests, catalogs, docs, fixtures, Storybook, comments, and template literals excluded.",
            "productionCallerCount": len(cs), "callerOccurrenceCount": sum(c["literalOccurrenceCount"] for c in cs), "callers": cs,
        }
        row["callerContextSha256"] = sha(canon({"sourceKey":key,"callers":cs}))
        rows.append(row)
        if not cs: holds.append({"position":pos,"sourceKey":key,"sourceKeySha256":sha(key),"reason":"No exact quoted production web/src caller resolved by the pinned scan."})
    return rows, holds, len(files)

def runtime_context():
    p = REPO / RUNTIME
    lines = p.read_text(encoding="utf-8").splitlines()
    markers = ["export const INTERFACE_LANGUAGE_OPTIONS","const translationFor =","const replaceInterfaceValues =","const formatInterfaceTextForLanguage ="]
    blocks = []
    for marker in markers:
        ix = next((i for i,x in enumerate(lines) if marker in x), None)
        if ix is None: raise RuntimeError(f"missing runtime marker {marker}")
        lo, hi = max(0,ix-1), min(len(lines),ix+11)
        blocks.append({"marker":marker,"startLine":lo+1,"endLine":hi,"lines":[{"line":j+1,"text":lines[j],"lineSha256":sha(lines[j])} for j in range(lo,hi)]})
    return {
        "path":RUNTIME,"pin":{"path":RUNTIME,"byteCount":p.stat().st_size,"lineCount":len(lines),"sha256":sha(p.read_bytes()),"gitBlob":git("rev-parse",f"HEAD:{RUNTIME}")},
        "localeOptionOrder":LOCS,"lookupAndPlaceholderContext":blocks,
        "note":"Locale lookup and named-placeholder behavior are pinned to this exact source revision; caller values remain opaque."
    }

