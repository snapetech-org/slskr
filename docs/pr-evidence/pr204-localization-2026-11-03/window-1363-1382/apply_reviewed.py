#!/usr/bin/env python3
from pathlib import Path
import collections,hashlib,json,subprocess
E=Path(__file__).resolve().parent
REPO=E.parents[3]
BASE='281c39ec0cdb3677d7d523b7c4f0cd0d52bbf14c'
TREE='777b234b1aa3cb7a2c9fd560b2c0fecc4e7fe49d'
BRANCH='codex/slskr-l10n-audit-20261030'
def run(args,cwd=None):return subprocess.check_output(args,cwd=cwd or REPO,text=True).strip()
def sha(b):return hashlib.sha256(b).hexdigest()
assert run(['git','rev-parse','HEAD'])==BASE and run(['git','rev-parse','HEAD^{tree}'])==TREE
pr=json.loads(run(['gh','api','repos/snapetech-org/slskR/pulls/204']))
assert (pr['state'],pr['draft'],pr['head']['sha'],pr['head']['ref'],pr['base']['ref'])==('open',True,BASE,BRANCH,'main')
refs=run(['git','ls-remote','https://github.com/snapetech-org/slskR.git',f'refs/heads/{BRANCH}','refs/pull/204/head'])
refmap={x.split()[1]:x.split()[0] for x in refs.splitlines()}
assert refmap=={f'refs/heads/{BRANCH}':BASE,'refs/pull/204/head':BASE}
status=run(['git','status','--porcelain','--untracked-files=all']).splitlines()
status_paths=[x[2:].strip() for x in status]
assert all(p.startswith('docs/pr-evidence/pr204-localization-2026-11-03/') for p in status_paths),status
plan=json.loads((E/'apply-plan.json').read_text())
assert plan['baseHead']==BASE and plan['baseTree']==TREE and len(plan['updates'])==143
allrows=plan['allCellReadbackPlan'];assert len(allrows)==240
catalog_paths=sorted({x['catalogPath'] for x in allrows})
before={};after={}
for path in catalog_paths:
 raw=subprocess.check_output(['git','show',f'{BASE}:{path}'],cwd=REPO)
 relevant=[x for x in allrows if x['catalogPath']==path]
 assert all(sha(raw)==x['catalogFileSha256'] for x in relevant)
 assert all(run(['git','rev-parse',f'{BASE}:{path}'])==x['catalogGitBlob'] for x in relevant)
 doc=json.loads(raw.decode('utf-8'))
 assert raw.decode('utf-8')==json.dumps(doc,ensure_ascii=False,indent=2)+'\n'
 before[path]=doc;after[path]=json.loads(raw.decode('utf-8'))
for row in allrows:
 path=row['catalogPath'];key=row['sourceKey']
 assert key in before[path]
 current=before[path][key]
 assert current==row['currentTarget'] and sha(current.encode())==row['currentTargetSha256']
 if row['changed']:after[path][key]=row['selectedTarget']
for path,data in after.items():
 changed={x['sourceKey']:x['selectedTarget'] for x in plan['updates'] if x['catalogPath']==path}
 assert list(data)==list(before[path]) and set(data)==set(before[path])
 for key,value in before[path].items():
  assert data[key]==changed.get(key,value),(path,key,'non-target or target mismatch')
 raw=json.dumps(data,ensure_ascii=False,indent=2)+'\n'
 (REPO/path).write_text(raw,encoding='utf-8')
 check=json.loads((REPO/path).read_text(encoding='utf-8'))
 assert check==data
prior=[json.loads(x) for x in (E/'candidate-free-input/prior-hold-reattestation.jsonl').read_text().splitlines() if x]
assert len(prior)==23
for h in prior:
 value=after[h['currentCatalogPath']][h['sourceKey']]
 assert sha(value.encode())==h['currentTargetSha256']==h['priorCurrentTargetSha256']
result={'schemaVersion':1,'status':'applied-uncommitted','repository':'snapetech-org/slskR','pullRequest':204,'branch':BRANCH,'reviewedBaseHead':BASE,'reviewedBaseTree':TREE,'cells':240,'decisionCounts':plan['decisionCounts'],'crossAuditResolutionCounts':plan['crossAuditResolutionCounts'],'changedCells':143,'changedCatalogFiles':len(catalog_paths),'catalogs':{p:sha((REPO/p).read_bytes()) for p in catalog_paths},'nonTargetChanges':0,'keyOrderPreserved':True,'priorHoldsPreserved':23,'callerlessRank1376Holds':12,'workflowFilesTouched':False,'testsBuildsScansCi':'not run','nativeSpeakerAndBrowserReview':'pending','mergeReleaseTag':'not performed'}
(E/'application-result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'pass':True,'cells':240,'updates':143,'catalogFiles':len(catalog_paths),'priorHoldsPreserved':23,'callerlessHolds':12,'nonTargetChanges':0},indent=2))
