#!/usr/bin/env python3
import hashlib,json,subprocess
from collections import Counter
from pathlib import Path
app=Path(__file__).resolve().parent
ev=app.parent
repo=Path(__file__).resolve().parents[5]
expected=('130462c56f75d3c8fc2a90663a48c0474ad1208b','47aba96d79eb57d6024fb358ee59cde931f0de3b','task/slskr-w1343-1362-20261103')
def sha(x): return hashlib.sha256(x if isinstance(x,bytes) else x.encode('utf-8')).hexdigest()
def load(p): return json.loads(p.read_text(encoding='utf-8'))
def jl(p): return [json.loads(x) for x in p.read_text(encoding='utf-8').splitlines() if x.strip()]
def git(*args): return subprocess.check_output(['git','-C',str(repo),*args],text=True).strip()
def keyhash(d): return sha('\n'.join(d.keys())+'\n')
def otherhash(d,changed): return sha(json.dumps([(k,v) for k,v in d.items() if k not in changed],ensure_ascii=False,separators=(',',':')))
head,tree,branch=git('rev-parse','HEAD'),git('show','-s','--format=%T','HEAD'),git('branch','--show-current')
if (head,tree,branch)!=expected: raise SystemExit('stale parent or unexpected work branch; refusing application')
statuses=git('status','--porcelain').splitlines()
if any(not s.startswith('?? docs/pr-evidence/pr204-localization-2026-11-03/window-1343-1362') for s in statuses): raise SystemExit('unexpected pre-existing worktree change')
plan=jl(app/'application-plan.jsonl')
ledger=jl(ev/'third-party-cross-audit/resolution-ledger.jsonl')
structure=jl(ev/'candidate-free-input/catalog-structure.jsonl')
holds=jl(ev/'candidate-free-input/prior-hold-reattestation.jsonl')
if (len(plan),len(ledger),len(structure),len(holds))!=(58,240,12,23): raise SystemExit('packet counts mismatch')
if len({(r['position'],r['locale']) for r in plan})!=58: raise SystemExit('duplicate plan cell')
cells={(int(r['position']),r['locale']):r for r in ledger}
if len(cells)!=240: raise SystemExit('duplicate cross-audit cell')
for folder in ('candidate-free-input','primary-review','independent-blind-review','third-party-cross-audit'):
    for line in (ev/folder/'SHA256SUMS.txt').read_text(encoding='utf-8').splitlines():
        if not line.strip(): continue
        digest,name=line.split(None,1); name=name.strip().lstrip('*')
        if sha((ev/folder/name).read_bytes())!=digest: raise SystemExit('packet checksum mismatch: '+folder+'/'+name)
files={}
for s in structure:
    p=s['path']; d=load(repo/p)
    if len(d)!=5441 or len(d)!=int(s['keyCount']) or keyhash(d)!=s['orderedKeySha256']: raise SystemExit('catalog shape mismatch: '+p)
    files[p]={'data':d,'before':sha((repo/p).read_bytes()),'keyhash':keyhash(d),'changed':set()}
for r in ledger:
    p,k=r['catalogPath'],r['sourceKey']; d=files[p]['data']
    if d.get(k)!=r['currentTarget'] or sha(d[k])!=r['currentTargetSha256']: raise SystemExit('input catalog does not match pinned current value')
for r in plan:
    cell=cells[(int(r['position']),r['locale'])]
    if cell['adjudicatedDisposition']!=r['selectedDisposition'] or cell['adjudicatedTarget']!=r['selectedTarget'] or cell['adjudicatedTargetSha256']!=r['selectedTargetSha256']: raise SystemExit('plan differs from cross-audit')
    p,k=r['catalogPath'],r['sourceKey']; d=files[p]['data']
    if d.get(k)!=r['currentTarget'] or sha(d[k])!=r['currentTargetSha256']: raise SystemExit('current target changed: '+str((r['position'],r['locale'])))
    if sha(r['selectedTarget'])!=r['selectedTargetSha256']: raise SystemExit('selected target hash mismatch')
    files[p]['changed'].add(k)
pre={'schemaVersion':1,'head':head,'tree':tree,'branch':branch,'files':[]}
for p,x in files.items():
    pre['files'].append({'path':p,'beforeSha256':x['before'],'keyCount':len(x['data']),'keyOrderSha256':x['keyhash'],'nonTargetEntriesSha256':otherhash(x['data'],x['changed'])})
(app/'application-preflight.json').write_text(json.dumps(pre,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
for r in plan: files[r['catalogPath']]['data'][r['sourceKey']]=r['selectedTarget']
for p,x in files.items(): (repo/p).write_text(json.dumps(x['data'],ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
read=[]
for r in ledger:
    p,k=r['catalogPath'],r['sourceKey']; actual=load(repo/p)[k]
    selected=next((x for x in plan if x['position']==r['position'] and x['locale']==r['locale']),None)
    expected_target=selected['selectedTarget'] if selected else r['adjudicatedTarget']
    if actual!=expected_target or sha(actual)!=sha(expected_target): raise SystemExit('readback mismatch: '+str((r['position'],r['locale'])))
    read.append({'position':r['position'],'locale':r['locale'],'sourceKey':k,'catalogPath':p,'adjudicatedDisposition':r['adjudicatedDisposition'],'expectedCurrentTarget':r['currentTarget'],'expectedTarget':expected_target,'actualTarget':actual,'actualTargetSha256':sha(actual),'readbackMatches':True})
(app/'application-readback.jsonl').write_text(''.join(json.dumps(x,ensure_ascii=False,sort_keys=True)+'\n' for x in read),encoding='utf-8')
for h in holds:
    actual=load(repo/h['currentCatalogPath'])[h['sourceKey']]
    if actual!=h['currentTarget'] or sha(actual)!=h['currentTargetSha256']: raise SystemExit('carry-forward hold changed')
post=[]
for p,x in files.items():
    d=load(repo/p)
    if len(d)!=len(x['data']) or keyhash(d)!=x['keyhash'] or otherhash(d,x['changed'])!=next(y['nonTargetEntriesSha256'] for y in pre['files'] if y['path']==p): raise SystemExit('catalog invariant failed: '+p)
    post.append({'path':p,'postApplyFileSha256':sha((repo/p).read_bytes()),'changedTargetCount':sum(r['catalogPath']==p for r in plan)})
counts=Counter(r['adjudicatedDisposition'] for r in ledger)
ver={'schemaVersion':1,'result':'PASS','parentHead':head,'parentTree':tree,'readbackCells':len(read),'selectedUpdates':len(plan),'corrections':counts['correction'],'refinements':counts['refinement'],'acceptCurrent':counts['accept-current'],'holds':counts['hold'],'carryForwardHolds':len(holds),'carryForwardHoldsPreserved':True,'catalogCount':len(files),'catalogKeyOrderPreserved':True,'nonTargetValuesPreserved':True,'catalogFiles':post}
(app/'application-verification.json').write_text(json.dumps(ver,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(ver,ensure_ascii=False,indent=2))
