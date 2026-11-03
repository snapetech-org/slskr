#!/usr/bin/env python3
import hashlib,json,pathlib,subprocess,sys
root=pathlib.Path(__file__).resolve().parents[1]
repo=root.parents[2]
app=root/'application'
def sha(b): return hashlib.sha256(b).hexdigest()
def rows(p): return [json.loads(x) for x in p.read_text(encoding='utf-8').splitlines() if x.strip()]
def check_sums(directory,name):
 for line in (directory/name).read_text().splitlines():
  if not line.strip(): continue
  digest,rel=line.split(None,1); rel=rel.lstrip('* ')
  p=directory/rel
  assert p.is_file() and sha(p.read_bytes())==digest,(p,digest)
check_sums(root,'SHA256SUMS.txt')
check_sums(root/'input','SHA256SUMS.txt')
check_sums(root/'primary-review','SHA256SUMS.txt')
check_sums(root/'independent-blind-review','BLIND-SHA256SUMS.txt')
check_sums(root/'root-cross-audit','SHA256SUMS.txt')
manifest=json.loads((root/'input/manifest.json').read_text())
pins=json.loads((root/'input/catalog-file-pins.json').read_text())['localeCatalogs']
current=rows(root/'input/current-target-cells.jsonl')
selected=rows(app/'plan-68-cells.jsonl')
readback=rows(app/'readback-240-cells.jsonl')
auth=json.loads((app/'root-application-authorization.json').read_text())
assert len(current)==240 and len(selected)==68 and len(readback)==240
assert manifest['head']==auth['head'] and manifest['commitApiTree']==auth['tree']
assert sha((root/'input/manifest.json').read_bytes())==auth['reviewedPackets']['candidateFreeManifestJsonSha256']
sel={(r['position'],r['locale']):r for r in selected}
cur={(r['position'],r['locale']):r for r in current}
rb={(r['position'],r['locale']):r for r in readback}
assert len(sel)==68 and len(cur)==240 and len(rb)==240
assert set(rb)==set(cur)
for ident,c in cur.items():
 r=rb[ident]; s=sel.get(ident); expected=s['target'] if s else c['currentTarget']
 assert r['expectedTarget']==expected and r['readbackTarget']==expected
 assert sha(expected.encode())==r['expectedTargetSha256']==r['readbackTargetSha256']
 assert r['selectedForApplication']==(s is not None)
for loc,pin in pins.items():
 p=repo/pin['path']; b=p.read_bytes(); final=json.loads(b)
 baseline_bytes=subprocess.check_output(['git','show',f"{auth['head']}:{pin['path']}"],cwd=repo)
 baseline=json.loads(baseline_bytes)
 assert list(final)==list(baseline)
 expected={s['sourceKey']:s['target'] for s in selected if s['locale']==loc}
 changed={k:v for k,v in final.items() if baseline[k]!=v}
 assert changed==expected,(loc,len(changed),len(expected))
for loc,h in json.loads((root/'primary-review/prior-hold-verification.json').read_text())['localeValuesAndHashes'].items():
 p=repo/pins[loc]['path']; value=json.loads(p.read_text())['Ecosystem']
 assert value==h['value'] and sha(value.encode())==h['sha256'],loc
assert sha((root/'primary-review/ledger.jsonl').read_bytes())==auth['reviewedPackets']['primaryLedgerSha256']
assert sha((root/'independent-blind-review/blind-ledger.jsonl').read_bytes())==auth['reviewedPackets']['blindLedgerSha256']
assert sha((root/'root-cross-audit/cross-audit-ledger.jsonl').read_bytes())==auth['reviewedPackets']['crossAuditLedgerSha256']
assert sha((root/'root-cross-audit/selected-changes.jsonl').read_bytes())==auth['selectedChangesSha256']
print('application evidence verified: 240 cells; 68 selected; 172 accept-current; 0 holds; catalogs, order, hashes, hold, and nested checksums pass')
