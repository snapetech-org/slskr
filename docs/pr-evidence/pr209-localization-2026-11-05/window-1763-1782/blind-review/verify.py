#!/usr/bin/env python3
from pathlib import Path
import hashlib,json,re,sys
ROOT=Path(__file__).resolve().parent
IN=Path("/mnt/disks/scratch/task-scratch/slskr-pr209-w1763-1782-candidate-free-20261105/candidate-free-input")
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def fail(x): print("FAIL:",x); sys.exit(1)
for line in (IN/"SHA256SUMS.txt").read_text().splitlines():
 d,n=line.split(None,1); n=n.strip()
 if sha(IN/n)!=d: fail("input checksum "+n)
im=json.loads((IN/"manifest.json").read_text())
if im["head"]!="5191888071f54061a6012acdedfeb518a6cb3661" or im["tree"]!="d5728c24b54a06dda432afd2ef5f378206a6cb8f": fail("input pin")
S=[json.loads(x) for x in (IN/"source-contexts.jsonl").read_text().splitlines()]; T=[json.loads(x) for x in (IN/"current-target-cells.jsonl").read_text().splitlines()]
L=[json.loads(x) for x in (ROOT/"blind-ledger.jsonl").read_text().splitlines()]
sm={x["position"]:x for x in S}; tm={(x["position"],x["locale"]):x for x in T}
if len(S)!=20 or len(T)!=240 or len(L)!=240: fail("coverage count")
if {(x["position"],x["locale"]) for x in L}!={(p,l) for p in sm for l in im["localeOrder"]}: fail("coverage or duplicate cells")
for r in L:
 s=sm[r["position"]]; t=tm[(r["position"],r["locale"])]
 for k,v in (("source_key",s["sourceKey"]),("source_key_sha256",s["sourceKeySha256"]),("source_context_sha256",s["callerContextSha256"]),("current_target",t["currentTarget"]),("current_target_sha256",t["currentTargetSha256"]),("catalog_path",t["catalogPath"]),("catalog_file_sha256",t["catalogFileSha256"]),("catalog_git_blob",t["catalogGitBlob"])):
  if r[k]!=v: fail(f"provenance {r['position']}:{r['locale']} {k}")
 if r["input_head"]!=im["head"] or r["input_tree"]!=im["tree"]: fail("row pin")
 refs={(c["path"],c["line"],c["contextSha256"],c["lineSha256"]) for c in s["callers"]}
 got={(c["path"],c["line"],c["context_sha256"],c["line_sha256"]) for c in r["caller_refs"]}
 if refs!=got: fail(f"caller pin {r['position']}:{r['locale']}")
 if (r["decision"]=="accept_current")!=(r["selected_target"]==r["current_target"]): fail("decision/selection mismatch")
 ph=re.findall(r"\{[^{}]+\}",r["selected_target"]); tags=re.findall(r"</?[A-Za-z][^>]*>",r["selected_target"]); nums=re.findall(r"(?<!\w)\d+(?:[.,]\d+)*(?!\w)",r["selected_target"])
 if ph!=t["sourcePlaceholders"] or tags!=t["sourceMarkupTags"]: fail(f"placeholder/markup {r['position']}:{r['locale']}")
 if any(x not in r["selected_target"] for x in t["sourceProtectedLiterals"]): fail(f"protected literal {r['position']}:{r['locale']}")
 delta=[x for x in nums if x not in t["sourceNumericTokens"]]
 okay=(r["position"]==1778 and r["locale"] in ("ja","ko") and delta==["16"] and bool(r["token_audit"]["numeric_explanation"]))
 if delta and not okay: fail(f"numeric delta {r['position']}:{r['locale']}")
 if r["token_audit"]["result"]!="pass": fail("cell token result")
H=json.loads((ROOT/"active-hold-reattestation.json").read_text()); hi=json.loads((IN/"active-hold-reattestation.jsonl").read_text().splitlines()[0])
if H["hold_id"]!="1719::id" or H["target_text_included"] or H["proposal"] is not None: fail("hold text/ID")
if H["current_target_sha256"]!=hi["currentTargetSha256"] or H["source_context_sha256"]!=hi["currentSourceContextSha256"] or not H["target_hash_unchanged"] or not H["source_context_unchanged"]: fail("hold continuity")
if not json.loads((ROOT/"token-audit.json").read_text())["pass"]: fail("token summary")
for line in (ROOT/"SHA256SUMS.txt").read_text().splitlines():
 d,n=line.split(None,1); n=n.strip()
 if sha(ROOT/n)!=d: fail("output checksum "+n)
print("PASS: exact input pins/checksums, 240 unique cells, caller/current/catalog provenance, 1719::id text-free hold, protected literals, placeholders, markup, numeric exception, output checksums")
