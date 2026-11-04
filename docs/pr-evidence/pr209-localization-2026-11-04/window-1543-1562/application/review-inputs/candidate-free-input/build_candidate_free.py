#!/usr/bin/env python3
"""Build candidate-free source/caller/current-target inputs for slskR PR #209 W1543-W1562."""
import hashlib, json, re, subprocess
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

R = Path(__file__).resolve().parent
REPO = Path("/mnt/disks/scratch/task-worktrees/localization-20261104/slskr-pr209-w1543-1562-source")
PREV = Path("/home/keith/Documents/code/task-scratch/slskr-pr204-w1523-1542-primary-20261104/candidate-free-input")
APP = Path("/home/keith/Documents/code/task-scratch/slskr-pr204-w1523-1542-apply-20261104/worktree/docs/pr-evidence/pr204-semantic-review-2026-11-04/independent-1523-1542-root-application")
PREV1503 = REPO / "docs/pr-evidence/pr204-localization-2026-11-04/window-1503-1522/candidate-free-input"
APP1503_META = REPO / "docs/pr-evidence/pr204-localization-2026-11-04/window-1503-1522/application-readback-metadata.json"
PREV1503_INPUT_SUMS_SHA256 = "a599379018be2e495cd44edb33cbea6832b29afbb496d4de18b58cdb9d0d8cd1"
APP1503_META_SHA256 = "af8fac8738e8e9a77bfbc1abac5f3513b4fb4f41e3c49d8bb4cf7966857aad61"
APP1503_PRODUCT_COMMIT = "0e793dd5632b3e6d4f25f91fe5b47fc121f3f813"
APP1503_PRODUCT_TREE = "a7ad6830162f0be4298e2f8c4100e58e2590ccb9"
APP1503_PARENT_HEAD = "a7d00cd97602c5910800330190817fcada008162"
APP1503_PARENT_TREE = "2d0a051348394e809ffc3a1fdbfccd20ba8af283"
APPLICATION_REPORT_SHA256 = "39760a429a50807f836aebe37d87fd053b4be2f3c5fde7e5c9da69228bcae698"
APPLICATION_READBACK_SHA256 = "aaac86d6d749a3a7b1c3f4e25a57faca1853ec6925a5a3951cea908a19ed85f2"
APPLICATION_PLAN_SHA256 = "367c2eac7ef950e3a7a47cf7533fe0f024c7a51fc61fbbe620d5d6e78ba3c81d"
HEAD = "c15eddffec2c4c24cc091b2a6ebf0c43fa58ef1b"
TREE = "4259db991f25fbbd0200963769e62bb7e2150806"
BASE_SHA = "1bbaec9fdc63a86de343e37e33bae70d44301a36"
REPO_NAME = "snapetech-org/slskR"
PR = 209
BRANCH = "codex/slskr-l10n-audit-20261104-resync"
LOCS = ["es", "zh-Hans", "hi", "de", "ja", "fr", "pt-BR", "ar", "ko", "zh-Hant", "vi", "id"]
START, END = 1543, 1562
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

def prior_lineage(catalogs, keys):
    qhash = {i:sha(k) for i,k in enumerate(keys,1)}
    win_path, sel_path, hold_path = (PREV/x for x in ("prior-window-selection-hash-only.jsonl","prior-selection-hash-reattestation.jsonl","prior-hold-hash-reattestation.jsonl"))
    old = [[json.loads(s) for s in p.read_text(encoding="utf-8").splitlines() if s] for p in (win_path,sel_path,hold_path)]
    previous_cells={(x["position"],x["locale"]):x for x in (json.loads(s) for s in (PREV/"current-target-cells.jsonl").read_text(encoding="utf-8").splitlines() if s)}
    previous_contexts={x["position"]:x for x in (json.loads(s) for s in (PREV/"source-contexts.jsonl").read_text(encoding="utf-8").splitlines() if s)}

    # Preserve W1503-W1522 using only its candidate-free input, application metadata,
    # and exact catalog diff. Do not read its application-readback JSONL.
    if sha((PREV1503/"SHA256SUMS.txt").read_bytes()) != PREV1503_INPUT_SUMS_SHA256:
        raise RuntimeError("W1503-W1522 candidate-free input seal changed")
    if sha(APP1503_META.read_bytes()) != APP1503_META_SHA256:
        raise RuntimeError("W1503-W1522 application metadata changed")
    prev1503_manifest=json.loads((PREV1503/"manifest.json").read_text(encoding="utf-8"))
    app1503_meta=json.loads(APP1503_META.read_text(encoding="utf-8"))
    if (prev1503_manifest["head"],prev1503_manifest["tree"],prev1503_manifest["selectedPositions"],prev1503_manifest["cellCount"]) != (
        APP1503_PARENT_HEAD,APP1503_PARENT_TREE,[1503,1522],240):
        raise RuntimeError("W1503-W1522 candidate-free pin changed")
    if (app1503_meta["reviewedParentHead"],app1503_meta["reviewedParentTree"],app1503_meta["catalogCommit"],app1503_meta["catalogTree"],
        app1503_meta["cells"],app1503_meta["updates"],app1503_meta["acceptCurrent"],app1503_meta["holds"]) != (
        APP1503_PARENT_HEAD,APP1503_PARENT_TREE,APP1503_PRODUCT_COMMIT,APP1503_PRODUCT_TREE,240,12,228,0):
        raise RuntimeError("W1503-W1522 application metadata counts or commits changed")
    if sha((PREV1503/"source-queue.jsonl").read_bytes()) != sha((PREV/"source-queue.jsonl").read_bytes()):
        raise RuntimeError("W1503 source-order evidence differs from the frozen prior queue")
    if git("rev-parse",f"{APP1503_PRODUCT_COMMIT}^{{tree}}") != APP1503_PRODUCT_TREE:
        raise RuntimeError("W1503 application catalog tree changed")
    if git("rev-parse",f"{APP1503_PRODUCT_COMMIT}^") != APP1503_PARENT_HEAD:
        raise RuntimeError("W1503 application parent head changed")
    if subprocess.call(["git","merge-base","--is-ancestor",APP1503_PRODUCT_COMMIT,HEAD],cwd=REPO) != 0:
        raise RuntimeError("W1503 application commit is not an ancestor of the pinned head")
    baseline_catalogs={}; applied_catalogs={}
    for loc in LOCS:
        path=f"{CAT}/ui-labels.{loc}.json"
        baseline_catalogs[loc]=json.loads(subprocess.check_output(["git","show",f"{APP1503_PARENT_HEAD}:{path}"],cwd=REPO))
        applied_catalogs[loc]=json.loads(subprocess.check_output(["git","show",f"{APP1503_PRODUCT_COMMIT}:{path}"],cwd=REPO))
    old1503_cells={(x["position"],x["locale"]):x for x in (json.loads(s) for s in (PREV1503/"current-target-cells.jsonl").read_text(encoding="utf-8").splitlines() if s)}
    if len(old1503_cells)!=240: raise RuntimeError("W1503 candidate-free cell input is incomplete")
    app1503_rows=[]; applied1503=[]; change_count=0
    for pos in range(1503,1523):
        key=keys[pos-1]
        for loc in LOCS:
            cell=old1503_cells.get((pos,loc))
            if cell is None or cell["sourceKeySha256"]!=qhash[pos] or cell["sourceKey"]!=key:
                raise RuntimeError("W1503 candidate-free source identity changed")
            path=cell["catalogPath"]
            base_value=baseline_catalogs[loc].get(key); after_value=applied_catalogs[loc].get(key); live_value=catalogs[loc].get(key)
            if not all(isinstance(v,str) for v in (base_value,after_value,live_value)):
                raise RuntimeError("W1503 catalog source/target key missing")
            base_hash,after_hash,live_hash=sha(base_value),sha(after_value),sha(live_value)
            if base_hash!=cell["currentTargetSha256"]: raise RuntimeError("W1503 base target hash differs from candidate-free input")
            if after_hash!=live_hash: raise RuntimeError("W1503 application target differs from the pinned live catalog")
            changed=base_hash!=after_hash
            if changed: change_count+=1
            disposition="applied-update" if changed else "accept-current"
            row={"window":"W1503-W1522","position":pos,"sourceKeySha256":qhash[pos],"locale":loc,
              "priorDisposition":disposition,"priorCurrentTargetSha256":base_hash,"priorResolvedTargetSha256":after_hash,
              "selectedTargetSha256":after_hash if changed else None,"observedAfterTargetSha256":after_hash,
              "sourceContextSha256":cell["sourceContextSha256"],"hashOnlyHold":False,"sourceKeyPositionMatches":True,
              "expectedPriorTargetSha256":after_hash,"liveCatalogTargetSha256":live_hash,"liveMatchesExpectedPriorTarget":True}
            app1503_rows.append(row)
            if changed:
                applied1503.append({"window":"W1503-W1522","productCommit":APP1503_PRODUCT_COMMIT,"productTree":APP1503_PRODUCT_TREE,
                  "position":pos,"locale":loc,"sourceKeySha256":qhash[pos],"sourceContextSha256":cell["sourceContextSha256"],
                  "selectedTargetSha256":after_hash,"observedAfterTargetSha256":after_hash,"sourceKeyPositionMatches":True})
    if change_count!=12 or len(app1503_rows)!=240 or len(applied1503)!=12:
        raise RuntimeError("W1503 catalog diff does not match application metadata")

    report=json.loads((APP/"apply-readback-report.json").read_text(encoding="utf-8"))
    app_raw=(APP/"apply-readback-cells.jsonl").read_bytes()
    plan_raw=(APP/"exact-hash-apply-plan.json").read_bytes()
    report_raw=(APP/"apply-readback-report.json").read_bytes()
    if (sha(report_raw),sha(app_raw),sha(plan_raw)) != (APPLICATION_REPORT_SHA256,APPLICATION_READBACK_SHA256,APPLICATION_PLAN_SHA256):
        raise RuntimeError("W1523-W1542 application evidence root files changed")
    if (report["productCommit"],report["productTree"],report["reviewedSourcePositions"],report["reviewedCells"],report["catalogChangesApplied"],report["outcomeCounts"]) != (
        "09497027d7ca64892cf8ce3530dd5cc1fdf93c15","b4594245bbb922bbce7785c9b4efc0041a2dd5df",[1523,1542],240,8,
        {"selected-primary":8,"keep-current":222,"hash-only-hold":10}):
        raise RuntimeError("W1523-W1542 application report mismatch")
    if subprocess.call(["git","merge-base","--is-ancestor",report["productCommit"],HEAD],cwd=REPO) != 0:
        raise RuntimeError("W1523 product application is not an ancestor of the pinned head")
    app_rows=[json.loads(s) for s in app_raw.decode("utf-8").splitlines() if s]
    if len(app_rows)!=240: raise RuntimeError("W1523 application readback is incomplete")
    decisions=Counter(x["decision"] for x in app_rows)
    if decisions != Counter({"select-primary-proposal":8,"keep-current":222,"hash-only-hold":10}): raise RuntimeError("W1523 application decisions drifted")
    def live(row):
        pos, loc = row["position"], row.get("locale")
        if qhash.get(pos) != row["sourceKeySha256"] or loc not in catalogs: return None
        key=keys[pos-1]
        if key not in catalogs[loc]: return None
        return sha(catalogs[loc][key])
    win=[]
    for x in old[0]:
        lh=live(x)
        expected=x.get("priorResolvedTargetSha256") or x.get("priorCurrentTargetSha256")
        win.append({"window":x.get("window"),"position":x["position"],"sourceKeySha256":x["sourceKeySha256"],
          "sourceKeyPositionMatches":qhash.get(x["position"])==x["sourceKeySha256"],"locale":x["locale"],"priorDisposition":x.get("priorDisposition"),
          "priorCurrentTargetSha256":x.get("priorCurrentTargetSha256"),"priorResolvedTargetSha256":x.get("priorResolvedTargetSha256"),
          "expectedPriorTargetSha256":expected,"liveCatalogTargetSha256":lh,"liveMatchesExpectedPriorTarget":lh is not None and lh==expected})
    win.extend(app1503_rows)
    appended_window=[]; appended_selections=[]; appended_holds=[]; applied=[]
    for x in app_rows:
        pos,loc=x["position"],x["locale"]
        prior=previous_cells.get((pos,loc))
        if prior is None or not (1523<=pos<=1542) or loc not in LOCS: raise RuntimeError("W1523 readback position/locale mismatch")
        if x["sourceKeySha256"] != qhash[pos] or x["currentTargetSha256"] != prior["currentTargetSha256"]:
            raise RuntimeError("W1523 readback does not match its sealed source/current input")
        if not x["readbackMatches"] or x["observedAfterTargetSha256"] != x["expectedAfterTargetSha256"]:
            raise RuntimeError("W1523 readback target hash mismatch")
        is_hold=x["decision"]=="hash-only-hold"
        src=keys[pos-1]
        if is_hold:
            caller=previous_contexts.get(pos,{})
            if pos not in (1538,1539) or "backfill" not in src.lower() or caller.get("productionCallerCount",0)<1:
                raise RuntimeError("W1523 backfill hold context no longer matches its documented caller-backed scope")
            if not x["hashOnlyHold"] or x["observedAfterTargetSha256"]!=x["currentTargetSha256"]:
                raise RuntimeError("W1523 hold target was not preserved")
        elif x["hashOnlyHold"]:
            raise RuntimeError("unexpected W1523 hold flag")
        disposition={"select-primary-proposal":"selected-primary","keep-current":"keep-current","hash-only-hold":"hash-only-hold"}[x["decision"]]
        row_live=live({"position":pos,"locale":loc,"sourceKeySha256":x["sourceKeySha256"]})
        rec={"window":"W1523-W1542","position":pos,"sourceKeySha256":x["sourceKeySha256"],"locale":loc,
          "priorDisposition":disposition,"priorCurrentTargetSha256":x["currentTargetSha256"],
          "priorResolvedTargetSha256":None if is_hold else x["observedAfterTargetSha256"],
          "selectedTargetSha256":x.get("selectedTargetSha256"),"observedAfterTargetSha256":x["observedAfterTargetSha256"],
          "sourceContextSha256":x["sourceContextSha256"],"hashOnlyHold":is_hold,
          "callerResolved":not is_hold or previous_contexts[pos]["productionCallerCount"]>0,
          "sourceKeyPositionMatches":True,"expectedPriorTargetSha256":x["currentTargetSha256"] if is_hold else x["observedAfterTargetSha256"],
          "liveCatalogTargetSha256":row_live,"liveMatchesExpectedPriorTarget":row_live==(x["currentTargetSha256"] if is_hold else x["observedAfterTargetSha256"])}
        appended_window.append(rec)
        if disposition=="selected-primary":
            if x.get("selectedTargetSha256")!=x["observedAfterTargetSha256"]: raise RuntimeError("selected W1523 target hash mismatch")
            applied.append({"window":"W1523-W1542","productCommit":report["productCommit"],"productTree":report["productTree"],
              "position":pos,"locale":loc,"sourceKeySha256":x["sourceKeySha256"],"sourceContextSha256":x["sourceContextSha256"],
              "selectedTargetSha256":x["selectedTargetSha256"],"observedAfterTargetSha256":x["observedAfterTargetSha256"],"sourceKeyPositionMatches":True})
        if is_hold:
            appended_holds.append({"window":"W1523-W1542","productCommit":report["productCommit"],"position":pos,"locale":loc,
              "sourceKeySha256":x["sourceKeySha256"],"sourceContextSha256":x["sourceContextSha256"],
              "priorTargetSha256":x["observedAfterTargetSha256"],"liveTargetSha256":x["observedAfterTargetSha256"],
              "matchesLiveValue":True,"holdCategory":"unresolved backfill terminology","callerResolved":True,"sourceKeyPositionMatches":True})
    appended_window.sort(key=lambda x:(x["position"],LOCS.index(x["locale"])))
    if len(applied)!=8 or len(appended_holds)!=10: raise RuntimeError("W1523 application hash lineage count mismatch")
    win.extend(appended_window)
    sel=[]
    for x in old[1]:
        matched=qhash.get(x["position"])==x["sourceKeySha256"]
        sel.append({"window":x.get("window"),"position":x["position"],"sourceKeySha256":x["sourceKeySha256"],
          "sourceKeyPositionMatches":matched,"matchesLiveQueue":matched})
    for pos in range(1503,1523):
        sel.append({"window":"W1503-W1522","position":pos,"sourceKeySha256":qhash[pos],"sourceKeyPositionMatches":True,"matchesLiveQueue":True})
    for pos in range(1523,1543):
        sel.append({"window":"W1523-W1542","position":pos,"sourceKeySha256":qhash[pos],"sourceKeyPositionMatches":True,"matchesLiveQueue":True})
    holds=[]
    for x in old[2]:
        lh=live(x); holds.append({"window":x.get("window"),"position":x["position"],"sourceKeySha256":x["sourceKeySha256"],
          "sourceKeyPositionMatches":qhash.get(x["position"])==x["sourceKeySha256"],"locale":x["locale"],
          "priorTargetSha256":x.get("priorTargetSha256"),"liveTargetSha256":lh,"matchesLiveValue":lh is not None and lh==x.get("priorTargetSha256")})
    holds.extend(appended_holds)
    applied.extend(applied1503)
    prior_apps={
      "w1503":{"window":"W1503-W1522","parentHead":APP1503_PARENT_HEAD,"parentTree":APP1503_PARENT_TREE,
        "productCommit":APP1503_PRODUCT_COMMIT,"productTree":APP1503_PRODUCT_TREE,"metadataSha256":APP1503_META_SHA256,
        "candidateFreeChecksumListSha256":PREV1503_INPUT_SUMS_SHA256,"catalogDiffCellCount":240,"appliedTargetHashCount":len(applied1503),"acceptCurrentCount":228,"holdCount":0},
      "w1523":{"window":"W1523-W1542","productCommit":report["productCommit"],"productTree":report["productTree"],
        "readbackCellCount":len(app_rows),"readbackSha256":sha(app_raw),"applicationReportSha256":sha(report_raw),"applyPlanSha256":sha(plan_raw),
        "appliedTargetHashCount":8,"acceptCurrentCount":222,"hashOnlyHoldCount":len(appended_holds),"holdReason":"unresolved backfill terminology; production callers are present"},
      "appliedTargetHashCountTotal":len(applied),
    }
    summary={
      "lineageSource":str(PREV.resolve()),
      "lineageFiles":{p.name:sha(p.read_bytes()) for p in (win_path,sel_path,hold_path)},
      "priorInputManifestSha256":sha((PREV/"manifest.json").read_bytes()),
      "priorInputContinuitySummarySha256":sha((PREV/"prior-continuity-hash-summary.json").read_bytes()),
      "fullSourceOrderQueue":{"priorQueueSha256":sha((PREV/"source-queue.jsonl").read_bytes()),"liveQueueSha256":sha("".join(canon({"position":p,"sourceKey":k,"sourceKeySha256":sha(k),"historicalSourceOrdinal":None})+"\n" for p,k in enumerate(keys,1))),"exactBytesMatch":True,"positionsCoveredThrough":1562},
      "previousWindowCells":{"recordCount":len(win),"sourcePositionMatches":sum(x["sourceKeyPositionMatches"] for x in win),
        "allMatchExpectedPriorTarget":all(x["liveMatchesExpectedPriorTarget"] for x in win),"liveTargetMismatchCount":sum(not x["liveMatchesExpectedPriorTarget"] for x in win),
        "windowLabels":sorted({x.get("window") for x in win})},
      "priorSelections":{"recordCount":len(sel),"sourcePositionMatches":sum(x["sourceKeyPositionMatches"] for x in sel),
        "allMatchLiveQueue":all(x["matchesLiveQueue"] for x in sel),"sourcePositionMismatchCount":sum(not x["sourceKeyPositionMatches"] for x in sel)},
      "priorHolds":{"recordCount":len(holds),"sourcePositionMatches":sum(x["sourceKeyPositionMatches"] for x in holds),
        "unchangedCount":sum(x["matchesLiveValue"] for x in holds),"changedCount":sum(not x["matchesLiveValue"] for x in holds),
        "backfillCallerBackedHashOnlyHoldCount":sum(x.get("holdCategory")=="unresolved backfill terminology" and x.get("callerResolved") is True for x in holds)},
      "priorApplications":prior_apps,
      "rawPriorTranslationsIncluded":False,
    }
    return win,sel,holds,summary,app1503_rows,appended_window,applied,appended_holds

def main():
    if (git("rev-parse","HEAD"),git("rev-parse","HEAD^{tree}")) != (HEAD,TREE): raise RuntimeError("exact checkout pin mismatch")
    before=pr_attestation(datetime.now(timezone.utc).isoformat(timespec="seconds"))
    catalogs,pins,keysets={},{},[]
    for loc in LOCS:
        path=f"{CAT}/ui-labels.{loc}.json"; f=REPO/path; raw=f.read_bytes(); d=json.loads(raw)
        if not isinstance(d,dict): raise RuntimeError("bad catalog")
        catalogs[loc]=d; keysets.append(set(d))
        ks=list(d); pins[loc]={"path":path,"sha256":sha(raw),"gitBlob":git("rev-parse",f"HEAD:{path}"),"orderedKeySha256":sha("\n".join(ks)+"\n"),"keyCount":len(ks)}
    if any(s!=keysets[0] for s in keysets): raise RuntimeError("locale key sets differ")
    keys=sorted(keysets[0]); orderhash=sha("\n".join(keys)+"\n")
    if len(keys)!=5441 or keys[START-1]!="Failed to get consensus recommendations: {message}" or keys[END-1]!="Failed to leave pod: {error}": raise RuntimeError("source queue or boundary changed")
    if any(list(catalogs[l]) != list(catalogs[LOCS[0]]) for l in LOCS[1:]): raise RuntimeError("ordered locale catalog keys differ")
    prior_queue=(PREV/"source-queue.jsonl").read_bytes()
    if sha(prior_queue) != sha("".join(canon({"position":p,"sourceKey":k,"sourceKeySha256":sha(k),"historicalSourceOrdinal":None})+"\n" for p,k in enumerate(keys,1))): raise RuntimeError("frozen source queue drift")
    queue=[{"position":p,"sourceKey":k,"sourceKeySha256":sha(k),"historicalSourceOrdinal":None} for p,k in enumerate(keys,1)]
    selected=keys[START-1:END]
    boundaries=[{"position":p,"boundary":not START<=p<=END,"sourceKey":keys[p-1],"sourceKeySha256":sha(keys[p-1])} for p in range(START-1,END+2)]
    contexts,caller_holds,scanned=contexts_for(selected)
    cells=[]; mismatch=Counter()
    for pos in range(START,END+1):
        key=keys[pos-1]; context=contexts[pos-START]; st=toks(key)
        for loc in LOCS:
            target=catalogs[loc][key]
            if not isinstance(target,str): raise RuntimeError(f"non-string target {pos}/{loc}")
            tt=toks(target); missing=[x for x in st[3] if x not in tt[3]]
            cell={"position":pos,"locale":loc,"sourceKey":key,"sourceKeySha256":sha(key),"sourceContextSha256":context["callerContextSha256"],
              "callerCount":context["productionCallerCount"],"currentTarget":target,"currentTargetSha256":sha(target),
              "catalogPath":pins[loc]["path"],"catalogFileSha256":pins[loc]["sha256"],"catalogGitBlob":pins[loc]["gitBlob"],
              "sourcePlaceholders":st[0],"currentTargetPlaceholders":tt[0],"placeholderSequenceMatches":st[0]==tt[0],
              "sourceMarkupTags":st[1],"currentTargetMarkupTags":tt[1],"markupMatches":st[1]==tt[1],
              "sourceNumericTokens":st[2],"currentTargetNumericTokens":tt[2],"numericTokensMatch":st[2]==tt[2],
              "sourceProtectedLiterals":st[3],"currentTargetProtectedLiterals":tt[3],"protectedLiteralMismatchTokens":missing,"protectedLiteralsMatch":not missing}
            cells.append(cell)
            mismatch["placeholderSequenceMismatchCount"]+=not cell["placeholderSequenceMatches"]
            mismatch["markupMismatchCount"]+=not cell["markupMatches"]
            mismatch["numericTokenMismatchCount"]+=not cell["numericTokensMatch"]
            mismatch["protectedLiteralMismatchCount"]+=bool(missing)
    prior_win,prior_sel,prior_holds,prior_summary,prior_app1503,prior_app_window,prior_applied,prior_app_holds=prior_lineage(catalogs,keys)
    runtime=runtime_context()
    caller_refs=sum(x["productionCallerCount"] for x in contexts)
    caller_occ=sum(x["callerOccurrenceCount"] for x in contexts)
    caller_files=len({c["path"] for x in contexts for c in x["callers"]})
    sourcepin={"repository":REPO_NAME,"pullRequest":PR,"head":HEAD,"tree":TREE,"selectedSourceCount":len(selected),
      "selectedCallerReferenceCount":caller_refs,"selectedCallerOccurrenceCount":caller_occ,
      "callerlessSelectedPositions":[x["position"] for x in contexts if not x["productionCallerCount"]],
      "trackedProductionJsTsFilesScanned":scanned,"uniqueSelectedCallerFiles":caller_files,
      "catalogPaths":{l:pins[l]["path"] for l in LOCS},"runtimePath":RUNTIME,
      "runtimeFileSha256":runtime["pin"]["sha256"],"runtimeGitBlob":runtime["pin"]["gitBlob"],
      "sourceLookupKeyCount":len(keys),"sourceLookupKeyOrderSha256":orderhash}
    wjl(R/"source-queue.jsonl",queue); wjl(R/"source-window-boundaries.jsonl",boundaries)
    (R/"selected-source-keys.txt").write_text("".join(x+"\n" for x in selected),encoding="utf-8")
    wjl(R/"source-contexts.jsonl",contexts); wjl(R/"caller-resolution-holds.jsonl",caller_holds)
    wjl(R/"current-target-cells.jsonl",cells)
    wj(R/"catalog-file-pins.json",{"head":HEAD,"tree":TREE,"sourceLookupKeySetCount":len(keys),"sourceLookupKeyOrderSha256":orderhash,"localeCatalogs":pins})
    wjl(R/"catalog-structure.jsonl",[{"locale":l,**pins[l]} for l in LOCS])
    wj(R/"localization-runtime-context.json",runtime); wj(R/"source-pin-reattestation.json",sourcepin)
    wjl(R/"prior-window-selection-hash-only.jsonl",prior_win); wjl(R/"prior-selection-hash-reattestation.jsonl",prior_sel)
    wjl(R/"prior-hold-hash-reattestation.jsonl",prior_holds); wj(R/"prior-continuity-hash-summary.json",prior_summary)
    wjl(R/"prior-window-1503-1522-catalog-diff-hash-only.jsonl",prior_app1503)
    wjl(R/"prior-window-1523-1542-application-hash-only.jsonl",prior_app_window)
    wjl(R/"prior-applied-target-hash-only.jsonl",prior_applied)
    wjl(R/"prior-backfill-hold-hash-only.jsonl",prior_app_holds)
    wj(R/"source-order-lineage.json",{"window":"W1543-W1562","completeSourceQueueCount":len(queue),"completeSourceQueueSha256":sha((R/"source-queue.jsonl").read_bytes()),"sourceLookupKeyOrderSha256":orderhash,"previousWindow":"W1523-W1542","previousBoundaryPosition":START-1,"previousBoundarySourceKeySha256":sha(keys[START-2]),"selectedPositions":list(range(START,END+1)),"selectedSourceCount":len(selected),"nextBoundaryPosition":END+1,"nextBoundarySourceKeySha256":sha(keys[END]),"priorQueueSha256":sha(prior_queue),"priorQueueMatchesLiveQueue":True,"gapPositions":[],"overlapPositions":[],"positionsCoveredThrough":END})
    wj(R/"PR-attestation.json",before)
    wj(R/"PR-attestation-after.json",pr_attestation(datetime.now(timezone.utc).isoformat(timespec="seconds")))
    (R/"README.md").write_text(
      f"# slskR PR #209 W1543-W1562 candidate-free input\n\n"
      f"Exact PR head {HEAD}, tree {TREE}; the PR remained OPEN/DRAFT before and after extraction. "
      f"Selected sorted source positions {START}-{END}, 20 source keys by 12 locales. "
      f"This packet contains source keys, current target strings, caller contexts, integrity pins, token signatures, and hash-only prior lineage. "
      f"It contains no proposed translations or review dispositions.\n\n"
      f"Caller scan covered {scanned} tracked production JavaScript/TypeScript files under web/src and resolved "
      f"{caller_refs} references / {caller_occ} literal occurrences across {caller_files} files. "
      f"Callerless positions: {[x['position'] for x in contexts if not x['productionCallerCount']]}.\n\n"
      f"The complete 5,441-key source queue matches the preceding frozen queue byte-for-byte; positions 1543-1562 immediately follow position 1542 with no gap or overlap. "
      f"Hash-only prior lineage preserves the inherited history and adds W1503-W1522 catalog-diff hashes plus W1523-W1542 application readback hashes (20 applied target hashes, 10 unchanged backfill holds). "
      f"The 10 holds are caller-backed terminology holds, not callerless cells. No prior translation text is included.\n",
      encoding="utf-8")
    if not (R/"verify-candidate-free.py").is_file(): raise RuntimeError("write verifier before sealing")
    manifest={
      "artifact":"slskR PR #209 W1543-W1562 candidate-free exact-head input","repository":REPO_NAME,"pullRequest":PR,
      "head":HEAD,"tree":TREE,"headRef":BRANCH,"baseRef":"main","baseSha":BASE_SHA,"draft":True,
      "candidateFreeInputOnly":True,"proposedTranslationsIncluded":False,"selectedPositions":[START,END],
      "previousBoundaryPosition":START-1,"nextBoundaryPosition":END+1,"sourceCount":20,"localeCount":len(LOCS),
      "cellCount":len(cells),"catalogSourceCount":len(keys),"localeOrder":LOCS,"sourceLookupKeyOrderSha256":orderhash,
      "sourceQueueCount":len(queue),"sourceQueueFileSha256":sha((R/"source-queue.jsonl").read_bytes()),
      "callerReferenceCount":caller_refs,"callerOccurrenceCount":caller_occ,"callerFileCount":caller_files,
      "callerResolutionHoldCount":len(caller_holds),"callerResolutionHoldPositions":[x["position"] for x in caller_holds],
      "carryForwardHoldCount":prior_summary["priorHolds"]["recordCount"],"carryForwardHoldUnchangedCount":prior_summary["priorHolds"]["unchangedCount"],
      "priorAppliedTargetHashCount":prior_summary["priorApplications"]["appliedTargetHashCountTotal"],"priorBackfillHashOnlyHoldCount":prior_summary["priorApplications"]["w1523"]["hashOnlyHoldCount"],
      "priorSelectionReattestationCount":len(prior_sel),"priorWindowHashRecordCount":len(prior_win),
      "historicalSourceOrdinalsClaimed":False,"catalogFilesPinned":len(pins),"mismatchCounts":dict(mismatch),**dict(mismatch),
      "localWorktree":str(REPO),"localWorktreeHead":HEAD,"localWorktreeTree":TREE,"localWorktreeBranch":"(detached)",
      "localWorktreeStatusClean":True,"createdAtUtc":datetime.now(timezone.utc).isoformat(timespec="seconds")}
    def file_hashes(): return {p.name:{"sha256":sha(p.read_bytes()),"byteCount":p.stat().st_size} for p in sorted(R.iterdir()) if p.is_file() and p.name not in ("manifest.json","SHA256SUMS.txt")}
    manifest["fileHashes"]=file_hashes(); wj(R/"manifest.json",manifest)
    manifest["fileHashes"]=file_hashes(); wj(R/"manifest.json",manifest)
    sums=[f"{sha(p.read_bytes())}  {p.name}" for p in sorted(R.iterdir()) if p.is_file() and p.name!="SHA256SUMS.txt"]
    (R/"SHA256SUMS.txt").write_text("\n".join(sums)+"\n",encoding="utf-8")
    print(json.dumps({"result":"BUILT","head":HEAD,"tree":TREE,"sourceCount":20,"cells":len(cells),
      "callerReferences":caller_refs,"callerOccurrences":caller_occ,"callerFiles":caller_files,"callerless":[x["position"] for x in caller_holds],
      "priorWindowHashes":len(prior_win),"priorSelectionHashes":len(prior_sel),"priorAppliedTargetHashes":len(prior_applied),"priorHolds":len(prior_holds),"mismatchCounts":dict(mismatch)},indent=2))

if __name__=="__main__": main()
