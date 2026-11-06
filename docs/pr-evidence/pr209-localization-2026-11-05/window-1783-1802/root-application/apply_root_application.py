#!/usr/bin/env python3
from __future__ import annotations
import argparse, copy, hashlib, json, subprocess
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parent/'root-adjudication'
LEDGER=ROOT/'root-final-review-ledger.jsonl'; PLAN=ROOT/'root-selected-targets.jsonl'; SUMMARY=ROOT/'summary.json'
def sha(v): return hashlib.sha256(v.encode('utf-8') if isinstance(v,str) else v).hexdigest()
def rows(p): return [json.loads(x) for x in p.read_text(encoding='utf-8').splitlines() if x.strip()]
def write_rows(p,rs): p.write_text(''.join(json.dumps(x,ensure_ascii=False,sort_keys=True)+'\n' for x in rs),encoding='utf-8')
def git(repo,*args): return subprocess.check_output(['git',*args],cwd=repo,text=True).strip()
def gitshow(repo,rev,path): return subprocess.check_output(['git','show',f'{rev}:{path}'],cwd=repo)
def main():
 ap=argparse.ArgumentParser(); ap.add_argument('--repo',required=True,type=Path); g=ap.add_mutually_exclusive_group(required=True); g.add_argument('--preflight',action='store_true'); g.add_argument('--apply',action='store_true'); g.add_argument('--verify-after',action='store_true'); a=ap.parse_args(); repo=a.repo.resolve()
 ledger=rows(LEDGER); plan=rows(PLAN); sm=json.loads(SUMMARY.read_text(encoding='utf-8')); head=sm['head']; tree=sm['tree']
 if len(ledger)!=240 or len(plan)!=56: raise SystemExit('unexpected ledger/plan coverage')
 grouped={}
 for r in ledger: grouped.setdefault(r['catalogPath'],[]).append(r)
 if len(grouped)!=12: raise SystemExit('expected 12 catalogs')
 if a.preflight or a.apply:
  if git(repo,'rev-parse','HEAD')!=head or git(repo,'rev-parse','HEAD^{tree}')!=tree: raise SystemExit('input head/tree mismatch')
  if git(repo,'status','--porcelain'): raise SystemExit('worktree not clean')
  rev=head
 else:
  pin=json.loads((HERE/'product-pin.json').read_text(encoding='utf-8')); product=pin['productCommit']
  if git(repo,'rev-parse',f'{product}^{{tree}}')!=pin['productTree']: raise SystemExit('product commit tree mismatch')
  if subprocess.run(['git','merge-base','--is-ancestor',product,git(repo,'rev-parse','HEAD')],cwd=repo).returncode: raise SystemExit('product commit is not an ancestor')
  rev=head
 expected={}; hashes={}
 for path,cells in grouped.items():
  raw=gitshow(repo,rev,path); expected_hashes={x['catalogFileSha256'] for x in cells}
  if len(expected_hashes)!=1 or sha(raw)!=next(iter(expected_hashes)): raise SystemExit(f'baseline hash mismatch: {path}')
  data=json.loads(raw.decode('utf-8'))
  if len(data)!=5441 or (json.dumps(data,ensure_ascii=False,indent=2)+'\n').encode('utf-8')!=raw: raise SystemExit(f'catalog shape/serialization mismatch: {path}')
  for x in cells:
   if data.get(x['sourceKey'])!=x['before'] or sha(data[x['sourceKey']])!=x['beforeSha256']: raise SystemExit(f"current hash mismatch: {x['cellId']}")
  out=copy.deepcopy(data)
  for x in (p for p in plan if p['catalogPath']==path):
   if out.get(x['sourceKey'])!=x['before'] or sha(out[x['sourceKey']])!=x['beforeSha256']: raise SystemExit(f"apply guard mismatch: {x['cellId']}")
   if sha(x['after'])!=x['afterSha256']: raise SystemExit(f"selected hash mismatch: {x['cellId']}")
   out[x['sourceKey']]=x['after']
  expected[path]=out; hashes[path]=sha(raw)
 if a.preflight:
  report={'result':'PASS','window':'W1783-W1802','inputHead':head,'inputTree':tree,'reviewedCells':240,
   'selectedChanges':56,'acceptedCurrent':183,'corrections':55,'refinements':1,'held':1,'catalogs':12,
   'entriesPerCatalog':5441,'allCurrentHashesMatch':True,'allSelectedTargetHashesMatch':True,'catalogHashes':hashes}
  (HERE/'preflight.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8'); print(json.dumps(report,ensure_ascii=False,indent=2)); return
 if a.apply:
  for path,data in expected.items(): (repo/path).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
  report={'result':'PASS','window':'W1783-W1802','inputHead':head,'inputTree':tree,'selectedChanges':56,'catalogWritesCompleted':12,'productCommitCreated':False}
  (HERE/'application-summary.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8'); print(json.dumps(report,ensure_ascii=False,indent=2)); return
 pin=json.loads((HERE/'product-pin.json').read_text(encoding='utf-8')); readback=[]
 for path,out in expected.items():
  actual=(repo/path).read_bytes()
  if actual!=gitshow(repo,pin['productCommit'],path): raise SystemExit(f'working file differs from product commit: {path}')
  final=json.loads(actual.decode('utf-8'))
  if final!=out or len(final)!=5441: raise SystemExit(f'catalog readback mismatch: {path}')
  for x in grouped[path]:
   got=final[x['sourceKey']]
   if got!=x['after'] or sha(got)!=x['afterSha256']: raise SystemExit(f"reviewed cell readback mismatch: {x['cellId']}")
   readback.append({'cellId':x['cellId'],'position':x['position'],'locale':x['locale'],'sourceKey':x['sourceKey'],'beforeSha256':x['beforeSha256'],'after':got,'afterSha256':sha(got),'disposition':x['rootDisposition'],'matches':True})
 if len(readback)!=240: raise SystemExit('unexpected readback count')
 write_rows(HERE/'final-head-readback.jsonl',readback)
 report={'result':'PASS_POST_COMMIT_READBACK','window':'W1783-W1802','inputHead':head,'inputTree':tree,
  'productCommit':pin['productCommit'],'productTree':pin['productTree'],'verificationHead':git(repo,'rev-parse','HEAD'),
  'catalogsMatchPinnedProduct':True,'keyOrderPreserved':True,'readbackRows':240,'changedCells':56,
  'unchangedCells':183,'heldCells':1,'nativeSpeakerApproval':False}
 (HERE/'application-summary.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8'); print(json.dumps(report,ensure_ascii=False,indent=2))
if __name__=='__main__': main()
