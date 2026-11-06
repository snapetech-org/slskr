#!/usr/bin/env python3
"""Verify the exact three-cell cross-review correction set."""
import argparse, hashlib, json, subprocess
from pathlib import Path

def die(s): raise SystemExit('FAIL: '+s)
def sha(b): return hashlib.sha256(b).hexdigest()
def git(repo,*args,raw=False):
 b=subprocess.run(['git',*args],cwd=repo,check=True,stdout=subprocess.PIPE).stdout
 return b if raw else b.decode().strip()
def main():
 ap=argparse.ArgumentParser(description=__doc__); ap.add_argument('--repo',type=Path,required=True); a=ap.parse_args(); repo=a.repo.resolve(); bundle=Path(__file__).resolve().parent
 m=json.loads((bundle/'manifest.json').read_text())
 base=m['application_parent_head']; app=m['application_head']; source=m['source_catalog_head']
 if git(repo,'rev-parse',f'{base}^{{tree}}')!=m['application_parent_tree']:die('parent tree pin mismatch')
 if git(repo,'rev-parse',f'{app}^')!=base or git(repo,'rev-parse',f'{app}^{{tree}}')!=m['application_tree']:die('application commit pin mismatch')
 if git(repo,'rev-parse',f'{source}^{{tree}}')!=m['source_catalog_tree']:die('source tree pin mismatch')
 ledger_raw=(bundle/m['ledger_file']).read_bytes()
 if sha(ledger_raw)!=m['ledger_sha256']:die('ledger SHA mismatch')
 rows=[json.loads(line) for line in ledger_raw.decode().splitlines() if line.strip()]
 if len(rows)!=3 or len({(r['source_id'],r['locale']) for r in rows})!=3:die('expected three unique correction cells')
 prev=json.loads(ledger_raw[:0] or b'{}') if False else None
 decisions_path=repo/'docs/pr-evidence/pr204-semantic-review-2026-11-01/independent-0143-0162-all-12-locales/decisions.jsonl'
 decisions=[json.loads(line) for line in decisions_path.read_text().splitlines() if line.strip()]
 for r in rows:
  if (r['application_parent_head'],r['application_parent_tree'],r['application_head'],r['application_tree'])!=(base,m['application_parent_tree'],app,m['application_tree']):die('row application pins mismatch')
  path=f"web/src/lib/locales/ui-labels.{r['locale']}.json"
  before=json.loads(git(repo,'show',f'{base}:{path}',raw=True).decode())
  after=json.loads(git(repo,'show',f'{app}:{path}',raw=True).decode())
  if sha(git(repo,'show',f'{base}:{path}',raw=True))!=r['previous_catalog_sha256']:die(f'baseline catalog hash mismatch {path}')
  if sha(git(repo,'show',f'{app}:{path}',raw=True))!=r['current_catalog_sha256']:die(f'final catalog hash mismatch {path}')
  if before.get(r['source_id'])!=r['previous_target'] or sha(r['previous_target'].encode())!=r['previous_target_sha256']:die(f'previous target/hash mismatch {r["source_id"]}/{r["locale"]}')
  if after.get(r['source_id'])!=r['current_target'] or sha(r['current_target'].encode())!=r['current_target_sha256']:die(f'current target/hash mismatch {r["source_id"]}/{r["locale"]}')
  if sha(r['source_id'].encode())!=r['source_sha256'] or not r['exact_source_and_old_target_hashes_revalidated']:die('source hash/revalidation mismatch')
  if r['confidence']!='high' or r['native_speaker_approval']:die('confidence/approval state mismatch')
  d=next((d for d in decisions if d['source_id']==r['source_id'] and d['locale']==r['locale']),None)
  if not d or d['status']!='correction-needed' or d['target_text']!=r['previous_target'] or d['target_sha256']!=r['previous_target_sha256'] or d['source_sha256']!=r['source_sha256']:die('prior semantic finding mismatch')
  if (r['review_decision_record']['path'],r['review_decision_record']['line'])!=('docs/pr-evidence/pr204-semantic-review-2026-11-01/independent-0143-0162-all-12-locales/decisions.jsonl',next(i for i,x in enumerate(decisions,1) if x is d)):die('decision reference mismatch')
 # Diff every direct locale catalog; exactly the three ledger cells may change.
 locales=['ar','de','es','fr','hi','id','ja','ko','pt-BR','vi','zh-Hans','zh-Hant'];changed=set()
 for loc in locales:
  path=f'web/src/lib/locales/ui-labels.{loc}.json'; b=json.loads(git(repo,'show',f'{base}:{path}',raw=True)); z=json.loads(git(repo,'show',f'{app}:{path}',raw=True))
  if set(b)!=set(z):die(f'key set changed: {loc}')
  changed.update((sid,loc) for sid in b if b[sid]!=z[sid])
 if changed!={(r['source_id'],r['locale']) for r in rows}:die('catalog diff has cells outside the three-row ledger')
 ctxm=json.loads((repo/'docs/pr-evidence/pr204-semantic-review-2026-11-01/independent-0143-0162-all-12-locales/manifest.json').read_text())
 ctxpath=repo/m['source_context_bundle']
 if sha(ctxpath.read_bytes())!=m['source_context_sha256'] or sha(ctxpath.read_bytes())!=ctxm['source_context']['evidence_text_sha256']:die('source context excerpt checksum mismatch')
 for path,digest in ctxm['source_context']['sha256'].items():
  if sha(git(repo,'show',f'{source}:{path}',raw=True))!=digest:die(f'source context code hash mismatch {path}')
 expected=[f'{sha(p.read_bytes())}  {p.name}' for p in sorted(bundle.iterdir()) if p.is_file() and p.name!='SHA256SUMS']
 if (bundle/'SHA256SUMS').read_text().splitlines()!=expected:die('SHA256SUMS mismatch')
 print('PASS: exact source/catalog/application pins; 3 high-confidence corrections only; old/new hashes and original findings; source-context pins; checksums.')
if __name__=='__main__':main()
