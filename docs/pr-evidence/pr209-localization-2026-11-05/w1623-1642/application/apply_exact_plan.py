#!/usr/bin/env python3
from pathlib import Path
import hashlib,json,subprocess
BASE=Path('/mnt/disks/scratch/task-scratch/slskr-pr209-w1623-1642-20261105')
REPO=BASE/'worktree'; OUT=BASE/'application'; PLAN=json.loads((OUT/'application-plan.json').read_text(encoding='utf-8'))
def sha(v): return hashlib.sha256(v if isinstance(v,bytes) else v.encode('utf-8')).hexdigest()
def git(*args): return subprocess.check_output(['git','-C',str(REPO),*args],text=True).strip()
head=PLAN['sourcePin']['head']; tree=PLAN['sourcePin']['tree']
if git('rev-parse','HEAD')!=head or git('rev-parse','HEAD^{tree}')!=tree: raise SystemExit('FAIL exact source head/tree')
if git('status','--porcelain=v1','--untracked-files=all'): raise SystemExit('FAIL source worktree not clean')
for path,pin in PLAN['catalogFiles'].items():
 raw=subprocess.check_output(['git','-C',str(REPO),'show',f'{head}:{path}'])
 if sha(raw)!=pin['catalogFileSha256'] or git('rev-parse',f'{head}:{path}')!=pin['catalogGitBlob']: raise SystemExit(f'FAIL exact catalog pin {path}')
 catalogs={}; raw_before={}
for path in PLAN['catalogFiles']:
 raw=subprocess.check_output(['git','-C',str(REPO),'show',f'{head}:{path}'])
 obj=json.loads(raw)
 if list(obj).__len__()!=PLAN['catalogFiles'][path]['keyCount'] or sha('\n'.join(obj.keys()))!=PLAN['catalogFiles'][path]['keyOrderSha256']: raise SystemExit(f'FAIL key order {path}')
 catalogs[path]=obj; raw_before[path]=raw
for c in PLAN['changes']:
 obj=catalogs[c['catalogPath']]; key=c['sourceKey']
 if key not in obj or sha(key)!=c['sourceKeySha256']: raise SystemExit('FAIL source key')
 if obj[key]!=c['expectedCurrentTarget'] or sha(obj[key])!=c['expectedCurrentTargetSha256']: raise SystemExit(f'FAIL exact current target {c["position"]}/{c["locale"]}')
 if sha(c['finalTarget'])!=c['finalTargetSha256']: raise SystemExit('FAIL final target hash')
 obj[key]=c['finalTarget']
outputs={p:(json.dumps(o,ensure_ascii=False,indent=2)+'\n').encode('utf-8') for p,o in catalogs.items()}
for p in outputs:
 if list(json.loads(raw_before[p]).keys()) != list(json.loads(outputs[p]).keys()): raise SystemExit(f'FAIL key order changed {p}')
for p,raw in outputs.items():
 if raw!=raw_before[p]:
  path=REPO/p; path.write_bytes(raw)
changes={(r['position'],r['locale']):r for r in PLAN['changes']}
cross=[json.loads(s) for s in (BASE/'cross-review/cross-review-ledger.jsonl').read_text(encoding='utf-8').splitlines() if s.strip()]
readback=[]
for r in cross:
 key=(r['position'],r['locale']); path=r['catalogPath']; after=catalogs[path][r['sourceKey']]
 c=changes.get(key); expected=c['finalTarget'] if c else r['currentTarget']
 if after!=expected: raise SystemExit(f'FAIL readback {key}')
 readback.append({'position':r['position'],'locale':r['locale'],'catalogPath':path,'sourceKey':r['sourceKey'],'sourceKeySha256':r['sourceKeySha256'],'sourceContextSha256':r['sourceContextSha256'],'beforeTargetSha256':r['currentTargetSha256'],'afterTargetSha256':sha(after),'changed':c is not None,'finalDisposition':'correction' if c else 'accept-current'})
if len(readback)!=240 or sum(r['changed'] for r in readback)!=13: raise SystemExit('FAIL readback coverage')
(OUT/'final-readback.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False,sort_keys=True,separators=(',',':'))+'\n' for r in readback),encoding='utf-8')
output={'result':'PASS','sourcePin':PLAN['sourcePin'],'reviewedCells':240,'changedCells':13,'retainedCells':227,'catalogFilesChanged':sum(outputs[p]!=raw_before[p] for p in outputs),'catalogMessageKeys':{p:PLAN['catalogFiles'][p]['keyCount'] for p in outputs},'keyOrderUnchanged':True,'translationStatusChanges':0,'translationReviewMetadataChanges':0,'workflowChanges':0,'testsBuildsScansCi':False,'finalReadbackSha256':sha((OUT/'final-readback.jsonl').read_bytes()),'catalogPostimages':{p:sha(raw) for p,raw in outputs.items() if raw!=raw_before[p]}}
(OUT/'apply-output.json').write_text(json.dumps(output,ensure_ascii=False,sort_keys=True,indent=2)+'\n',encoding='utf-8')
print(json.dumps(output,ensure_ascii=False,sort_keys=True))
