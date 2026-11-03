#!/usr/bin/env python3
import hashlib,json,subprocess
from collections import Counter
from pathlib import Path
app=Path(__file__).resolve().parent
ev=app.parent
repo=Path(__file__).resolve().parents[5]
def sha(x): return hashlib.sha256(x if isinstance(x,bytes) else x.encode('utf-8')).hexdigest()
def load(p): return json.loads(p.read_text(encoding='utf-8'))
def jl(p): return [json.loads(x) for x in p.read_text(encoding='utf-8').splitlines() if x.strip()]
def git(*args): return subprocess.check_output(['git','-C',str(repo),*args],text=True).strip()
def keyhash(d): return sha('\n'.join(d.keys())+'\n')
def otherhash(d,changed): return sha(json.dumps([(k,v) for k,v in d.items() if k not in changed],ensure_ascii=False,separators=(',',':')))
def check_sums(folder):
    listed=set()
    for line in (folder/'SHA256SUMS.txt').read_text(encoding='utf-8').splitlines():
        if not line.strip(): continue
        digest,name=line.split(None,1); name=name.strip().lstrip('*'); listed.add(name)
        if not (folder/name).is_file() or sha((folder/name).read_bytes())!=digest: raise SystemExit('checksum mismatch: '+str(folder/name))
    actual={p.name for p in folder.iterdir() if p.is_file() and p.name!='SHA256SUMS.txt'}
    if listed!=actual: raise SystemExit('checksum file inventory mismatch: '+str(folder))
check_sums(app)
for name in ('candidate-free-input','primary-review','independent-blind-review','third-party-cross-audit'): check_sums(ev/name)
plan=jl(app/'application-plan.jsonl'); ledger=jl(ev/'third-party-cross-audit/resolution-ledger.jsonl')
readback=jl(app/'application-readback.jsonl'); structure=jl(ev/'candidate-free-input/catalog-structure.jsonl')
holds=jl(ev/'candidate-free-input/prior-hold-reattestation.jsonl')
pre=load(app/'application-preflight.json'); ver=load(app/'application-verification.json')
if (len(plan),len(ledger),len(readback),len(structure),len(holds))!=(58,240,240,12,23): raise SystemExit('application packet row count mismatch')
bycell={(int(r['position']),r['locale']):r for r in ledger}
if len(bycell)!=240 or len({(int(r['position']),r['locale']) for r in readback})!=240: raise SystemExit('duplicate cell')
plan_bycell={(int(r['position']),r['locale']):r for r in plan}
if len(plan_bycell)!=58: raise SystemExit('duplicate plan cell')
for r in readback:
    cell=bycell[(int(r['position']),r['locale'])]
    current=json.loads((repo/r['catalogPath']).read_text(encoding='utf-8'))[r['sourceKey']]
    if current!=r['expectedTarget'] or current!=r['actualTarget'] or sha(current)!=r['actualTargetSha256'] or current!=cell['adjudicatedTarget']: raise SystemExit('readback mismatch')
    if r['adjudicatedDisposition']!=cell['adjudicatedDisposition']: raise SystemExit('readback disposition mismatch')
for key,p in plan_bycell.items():
    cell=bycell[key]
    if cell['adjudicatedDisposition'] not in ('correction','refinement') or p['selectedTarget']!=cell['adjudicatedTarget'] or sha(p['selectedTarget'])!=p['selectedTargetSha256']: raise SystemExit('plan/cross-audit mismatch')
if {k for k,r in bycell.items() if r['adjudicatedDisposition'] in ('correction','refinement')}!=set(plan_bycell): raise SystemExit('plan omits or adds an update')
for h in holds:
    current=json.loads((repo/h['currentCatalogPath']).read_text(encoding='utf-8'))[h['sourceKey']]
    if current!=h['currentTarget'] or sha(current)!=h['currentTargetSha256']: raise SystemExit('carry-forward hold changed')
for h in holds:
    old=next(x for x in jl(ev/'third-party-cross-audit/preserved-prior-holds.jsonl') if x['locale']==h['locale'] and x['sourceKey']==h['sourceKey'])
    if old!=h: raise SystemExit('carry-forward hold evidence mismatch')
orders=[]
for info in structure:
    path=repo/info['path']; data=load(path); orders.append(list(data))
    if len(data)!=5441 or keyhash(data)!=info['orderedKeySha256']: raise SystemExit('catalog key shape mismatch: '+info['path'])
    before=next(x for x in pre['files'] if x['path']==info['path'])
    changed={r['sourceKey'] for r in plan if r['catalogPath']==info['path']}
    if otherhash(data,changed)!=before['nonTargetEntriesSha256']: raise SystemExit('non-target value changed: '+info['path'])
    after=next(x for x in ver['catalogFiles'] if x['path']==info['path'])
    if sha(path.read_bytes())!=after['postApplyFileSha256']: raise SystemExit('catalog post-apply hash mismatch: '+info['path'])
if any(x!=orders[0] for x in orders[1:]): raise SystemExit('locale key order differs')
counts=Counter(r['adjudicatedDisposition'] for r in ledger)
if counts!=Counter({'accept-current':182,'correction':54,'refinement':4}): raise SystemExit('cross-audit disposition counts mismatch')
if ver['result']!='PASS' or ver['selectedUpdates']!=58 or ver['readbackCells']!=240 or ver['carryForwardHoldsPreserved'] is not True: raise SystemExit('application summary mismatch')
changed=set(git('diff','--name-only').splitlines())
expected={r['catalogPath'] for r in plan}
if changed!=expected or any(p.startswith('.github/workflows/') for p in changed): raise SystemExit('tracked diff scope mismatch')
print(json.dumps({'result':'PASS','cells':240,'updates':58,'corrections':54,'refinements':4,'retained':182,'currentWindowHolds':0,'carryForwardHolds':23,'catalogs':12,'orderedKeysPreserved':True,'nonTargetsPreserved':True,'workflowFilesChanged':False},ensure_ascii=False,indent=2))
