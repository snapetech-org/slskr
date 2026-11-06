#!/usr/bin/env python3
"""Guarded exact-hash slskR W1763-W1782 catalog application and readback."""
from __future__ import annotations
import argparse, copy, hashlib, json, subprocess
from pathlib import Path

HERE=Path(__file__).resolve().parent
BASE=HERE.parent if HERE.name=='root-application' else HERE
REPO: Path
ROOT=BASE/'root-adjudication'
LEDGER=ROOT/'root-final-review-ledger.jsonl'
PLAN=ROOT/'root-selected-targets.jsonl'
SUMMARY=ROOT/'summary.json'
APPLY=BASE/'root-application'
PRODUCT_PIN=APPLY/'product-pin.json'
PREFLIGHT=APPLY/'preflight.json'
APPLICATION_SUMMARY=APPLY/'application-summary.json'
READBACK=APPLY/'final-head-readback.jsonl'

def sha(v): return hashlib.sha256(v.encode('utf-8') if isinstance(v,str) else v).hexdigest()
def rows(p): return [json.loads(x) for x in p.read_text(encoding='utf-8').splitlines() if x.strip()]
def write_rows(p,rs): p.parent.mkdir(parents=True,exist_ok=True); p.write_text(''.join(json.dumps(r,ensure_ascii=False,sort_keys=True)+'\n' for r in rs),encoding='utf-8')
def git(*args): return subprocess.check_output(['git',*args],cwd=REPO,text=True).strip()
def gitshow(rev,path): return subprocess.check_output(['git','show',f'{rev}:{path}'],cwd=REPO)
def main():
 global REPO
 ap=argparse.ArgumentParser(); ap.add_argument('--repo',type=Path,required=True); g=ap.add_mutually_exclusive_group(required=True); g.add_argument('--preflight',action='store_true'); g.add_argument('--apply',action='store_true'); g.add_argument('--verify-after',action='store_true'); a=ap.parse_args()
 REPO=a.repo.resolve()
 root_rows=rows(LEDGER); plan=rows(PLAN); summary=json.loads(SUMMARY.read_text(encoding='utf-8'))
 head=summary['head']; tree=summary['tree']; assert len(root_rows)==240 and len(plan)==109
 assert len({(r['position'],r['locale']) for r in root_rows})==240
 assert len({(r['position'],r['locale']) for r in plan})==109
 grouped={}
 for r in root_rows: grouped.setdefault(r['catalogPath'],[]).append(r)
 assert len(grouped)==12
 if a.preflight or a.apply:
  if git('rev-parse','HEAD')!=head or git('rev-parse','HEAD^{tree}')!=tree: raise SystemExit('input head/tree mismatch')
  if git('status','--porcelain'): raise SystemExit('worktree is not clean before catalog application')
  baseline_rev=head
 else:
  if not PRODUCT_PIN.exists(): raise SystemExit('product-pin.json missing')
  pin=json.loads(PRODUCT_PIN.read_text(encoding='utf-8')); product=pin['productCommit']
  tree_now=git('rev-parse',f'{product}^{{tree}}')
  if tree_now!=pin['productTree']: raise SystemExit('product commit tree pin mismatch')
  if subprocess.run(['git','merge-base','--is-ancestor',product,'HEAD'],cwd=REPO).returncode: raise SystemExit('product commit is not an ancestor of HEAD')
  baseline_rev=head
 expected_catalogs={}; baseline_hashes={}
 for path,cells in grouped.items():
  raw=gitshow(baseline_rev,path)
  hashes={r['catalogFileSha256'] for r in cells}
  if len(hashes)!=1 or sha(raw)!=next(iter(hashes)): raise SystemExit(f'input catalog hash mismatch: {path}')
  data=json.loads(raw.decode('utf-8'))
  if len(data)!=5441 or (json.dumps(data,ensure_ascii=False,indent=2)+'\n').encode('utf-8')!=raw: raise SystemExit(f'catalog shape/serialization mismatch: {path}')
  if list(data)!=list(json.loads(raw.decode('utf-8'))): raise SystemExit(f'catalog key order mismatch: {path}')
  expected=copy.deepcopy(data)
  for r in cells:
   if r['sourceKey'] not in data or data[r['sourceKey']]!=r['before'] or sha(data[r['sourceKey']])!=r['beforeSha256']:
    raise SystemExit(f'exact current-value guard mismatch: {path}::{r["sourceKey"]}')
  for edit in (p for p in plan if p['catalogPath']==path):
   if expected.get(edit['sourceKey'])!=edit['before'] or sha(expected[edit['sourceKey']])!=edit['beforeSha256']:
    raise SystemExit(f'exact apply guard mismatch: {path}::{edit["sourceKey"]}')
   if sha(edit['after'])!=edit['afterSha256']: raise SystemExit(f'target hash mismatch: {edit["cellId"]}')
   expected[edit['sourceKey']]=edit['after']
  expected_catalogs[path]=expected; baseline_hashes[path]=sha(raw)
 pre={'result':'PASS','window':'W1763-W1782','inputHead':head,'inputTree':tree,
   'reviewedCells':240,'selectedChanges':109,'acceptedCurrent':131,'corrections':105,'refinements':4,
   'catalogs':len(grouped),'entriesPerCatalog':5441,'allCurrentHashesMatch':True,
   'allSelectedTargetHashesMatch':True,'catalogHashes':baseline_hashes}
 if a.preflight:
  PREFLIGHT.parent.mkdir(parents=True,exist_ok=True); PREFLIGHT.write_text(json.dumps(pre,ensure_ascii=False,indent=2)+'\n',encoding='utf-8'); print(json.dumps(pre,ensure_ascii=False,indent=2)); return
 if a.apply:
  for path,data in expected_catalogs.items():
   target=REPO/path; target.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
  PREFLIGHT.write_text(json.dumps({**pre,'catalogWritesCompleted':len(expected_catalogs),'productCommitCreated':False},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
  print(json.dumps({**pre,'catalogWritesCompleted':len(expected_catalogs),'next':'commit focused catalog changes, create product-pin.json, then run --verify-after'},ensure_ascii=False,indent=2)); return
 pin=json.loads(PRODUCT_PIN.read_text(encoding='utf-8'))
 readback=[]; changed=[]
 for path,expected in expected_catalogs.items():
  product_bytes=gitshow(pin['productCommit'],path); actual=(REPO/path).read_bytes()
  if product_bytes!=actual: raise SystemExit(f'working catalog differs from pinned product commit: {path}')
  final=json.loads(actual.decode('utf-8'))
  if len(final)!=5441 or list(final)!=list(json.loads(gitshow(head,path).decode('utf-8'))): raise SystemExit(f'catalog key/order mismatch after application: {path}')
  if final!=expected: raise SystemExit(f'full catalog readback mismatch: {path}')
  for r in grouped[path]:
   got=final[r['sourceKey']]
   if got!=r['after'] or sha(got)!=r['afterSha256']: raise SystemExit(f'240-cell readback mismatch: {r["cellId"]}')
   readback.append({'cellId':r['cellId'],'position':r['position'],'locale':r['locale'],'sourceKey':r['sourceKey'],'beforeSha256':r['beforeSha256'],'after':got,'afterSha256':sha(got),'disposition':r['rootDisposition'],'matches':True})
  for r in plan:
   if r['catalogPath']==path: changed.append(r['cellId'])
 if len(readback)!=240 or len(changed)!=109: raise SystemExit('unexpected readback coverage')
 write_rows(READBACK,readback)
 report={**pre,'result':'PASS_POST_COMMIT_READBACK','productCommit':pin['productCommit'],'productTree':pin['productTree'],
  'verificationHead':git('rev-parse','HEAD'),'catalogsMatchPinnedProduct':True,'keyOrderPreserved':True,
  'readbackRows':len(readback),'changedCells':len(changed),'unchangedCells':131,'nativeSpeakerApproval':False}
 APPLICATION_SUMMARY.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 print(json.dumps(report,ensure_ascii=False,indent=2))
if __name__=='__main__': main()
