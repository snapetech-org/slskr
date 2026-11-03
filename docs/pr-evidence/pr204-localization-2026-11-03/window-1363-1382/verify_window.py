#!/usr/bin/env python3
from pathlib import Path
import collections
import hashlib
import json
import subprocess
import sys

E=Path(__file__).resolve().parent
REPO=E.parents[3]
BASE='281c39ec0cdb3677d7d523b7c4f0cd0d52bbf14c'
TREE='777b234b1aa3cb7a2c9fd560b2c0fecc4e7fe49d'
BRANCH='codex/slskr-l10n-audit-20261030'
MODES={'--precommit','--prepush','--evidence','--postpush'}
mode=sys.argv[1] if len(sys.argv)>1 else '--postpush'
assert mode in MODES,mode

def run(args,cwd=None):
 return subprocess.check_output(args,cwd=cwd or REPO,text=True).strip()

def sha(b):
 return hashlib.sha256(b).hexdigest()

def rows(path):
 return [json.loads(x) for x in path.read_text(encoding='utf-8').splitlines() if x.strip()]

def verify_sums(folder,name='SHA256SUMS.txt'):
 for line in (folder/name).read_text(encoding='utf-8').splitlines():
  if line.strip():
   digest,filename=line.split(None,1)
   filename=filename.strip().lstrip('*')
   assert sha((folder/filename).read_bytes())==digest,(folder/filename,'checksum')

def verify_root_sums():
 for line in (E/'SHA256SUMS.txt').read_text(encoding='utf-8').splitlines():
  if line.strip():
   digest,filename=line.split(None,1)
   filename=filename.strip().lstrip('*')
   assert sha((E/filename).read_bytes())==digest,(E/filename,'root checksum')

I=E/'candidate-free-input'
BI=E/'blind-input'
P=E/'primary-review'
B=E/'blind-review'
X=E/'cross-audit'
for folder in [I,BI,B,X]: verify_sums(folder)
verify_sums(P,"SHA256SUMS")
for folder,script in [(I,'verify-candidate-free.py'),(BI,'verify-blind-input.py'),(P,'verify-primary-ledger.py'),(B,'verify_blind_review.py'),(X,'verify_cross_audit.py')]:
 subprocess.run([sys.executable,script],cwd=folder,check=True,capture_output=True,text=True)
im=json.loads((I/'manifest.json').read_text())
bm=json.loads((BI/'manifest.json').read_text())
pm=json.loads((P/'manifest.json').read_text())
blm=json.loads((B/'manifest.json').read_text())
xm=json.loads((X/'manifest.json').read_text())
for m in [im,bm,pm,blm,xm]:
 assert (m['head'],m['tree'])==(BASE,TREE)
plan=json.loads((E/'apply-plan.json').read_text())
assert (plan['baseHead'],plan['baseTree'],plan['reviewedCells'])==(BASE,TREE,240)
cells=rows(I/'current-target-cells.jsonl')
audit=rows(X/'resolution-ledger.jsonl')
allplan=plan['allCellReadbackPlan']
assert len(cells)==len(audit)==len(allplan)==240
key=lambda x:(x['position'],x['locale'])
ci={key(x):x for x in cells};ai={key(x):x for x in audit};pi={key(x):x for x in allplan}
assert ci.keys()==ai.keys()==pi.keys()
decisions=collections.Counter(x['selectedDisposition'] for x in audit)
resolutions=collections.Counter(x['resolution'] for x in audit)
assert decisions==collections.Counter({'accept-current':85,'correction':27,'refinement':116,'hold':12})
assert resolutions==collections.Counter({'agreement':35,'hold-consensus':12,'primary-selected':61,'blind-selected':132})
assert len(plan['updates'])==143 and sum(x['changed'] for x in allplan)==143
assert plan['priorHoldsExpected']==23 and plan['callerlessRank1376Holds']==12
assert all(x['position']==1376 and x['selectedTarget']==x['currentTarget'] for x in allplan if x['selectedDisposition']=='hold')
for k,c in ci.items():
 a=ai[k];p=pi[k]
 assert (a['sourceKey'],a['sourceKeySha256'],a['sourceContextSha256'],a['currentTarget'],a['currentTargetSha256'])==(
  c['sourceKey'],c['sourceKeySha256'],c['sourceContextSha256'],c['currentTarget'],c['currentTargetSha256'])
 assert p['selectedTarget']==(a['selectedTarget'] if a['selectedTarget'] is not None else c['currentTarget'])
 assert p['selectedTargetSha256']==sha(p['selectedTarget'].encode())
 assert p['catalogPath']==c['catalogPath']
updates={(x['position'],x['locale']):x for x in plan['updates']}
assert updates.keys()=={k for k,x in pi.items() if x['changed']}
catalog_paths={x['catalogPath'] for x in cells}
catalogs={}
for path in catalog_paths:
 raw=subprocess.check_output(['git','show',f'{BASE}:{path}'],cwd=REPO)
 baseline=json.loads(raw.decode('utf-8'))
 assert raw.decode('utf-8')==json.dumps(baseline,ensure_ascii=False,indent=2)+'\n'
 relevant=[x for x in cells if x['catalogPath']==path]
 assert all(sha(raw)==x['catalogFileSha256'] for x in relevant)
 assert all(run(['git','rev-parse',f'{BASE}:{path}'])==x['catalogGitBlob'] for x in relevant)
 current=json.loads((REPO/path).read_text(encoding='utf-8'))
 assert list(current)==list(baseline)
 selected={x['sourceKey']:x['selectedTarget'] for x in allplan if x['catalogPath']==path and x['changed']}
 for k,v in baseline.items(): assert current[k]==selected.get(k,v),(path,k,'readback/non-target mismatch')
 catalogs[path]=(baseline,current)
for u in plan['updates']: assert catalogs[u['catalogPath']][1][u['sourceKey']]==u['selectedTarget']
prior=rows(I/'prior-hold-reattestation.jsonl')
assert len(prior)==23
for h in prior:
 value=catalogs[h['currentCatalogPath']][1][h['sourceKey']]
 assert sha(value.encode())==h['currentTargetSha256']==h['priorCurrentTargetSha256']
evidence_prefix='docs/pr-evidence/pr204-localization-2026-11-03/'
def allowed(path): return path in catalog_paths or path.startswith(evidence_prefix)
diff=set(filter(None,run(['git','diff','--name-only',BASE]).splitlines()))
assert all(allowed(p) for p in diff),sorted(diff)
assert not any(p.startswith('.github/workflows/') for p in diff)
catalog_check=subprocess.run(['git','-C',str(REPO),'diff','--check',BASE,'--',*sorted(catalog_paths)],capture_output=True,text=True)
assert catalog_check.returncode==0,catalog_check.stdout+catalog_check.stderr
status=run(['git','status','--porcelain','--untracked-files=all']).splitlines()
status_paths=[line[2:].strip() for line in status]
assert all(allowed(p) for p in status_paths),status
head=run(['git','rev-parse','HEAD']);tree=run(['git','rev-parse','HEAD^{tree}'])
pr=json.loads(run(['gh','api','repos/snapetech-org/slskR/pulls/204']))
assert (pr['state'],pr['draft'],pr['head']['ref'],pr['base']['ref'])==('open',True,BRANCH,'main')
refs_text=run(['git','ls-remote','https://github.com/snapetech-org/slskR.git',f'refs/heads/{BRANCH}','refs/pull/204/head'])
refs={line.split()[1]:line.split()[0] for line in refs_text.splitlines() if line.strip()}
remote_branch=refs[f'refs/heads/{BRANCH}'];remote_pr=refs['refs/pull/204/head']
if mode=='--precommit':
 assert head==BASE and tree==TREE
 assert pr['head']['sha']==BASE and remote_branch==remote_pr==BASE
 assert all(p in status_paths for p in {x['catalogPath'] for x in plan['updates']})
elif mode=='--prepush':
 assert run(['git','rev-parse',f'{head}^'])==BASE and not status
 assert pr['head']['sha']==BASE and remote_branch==remote_pr==BASE
elif mode=='--evidence':
 av=json.loads((E/'application-verification.json').read_text())
 assert head==av['applicationCommit'] and pr['head']['sha']==head and remote_branch==remote_pr==head
 assert all(p.startswith(evidence_prefix) for p in status_paths),status
 verify_root_sums()
else:
 assert pr['head']['sha']==head and remote_branch==remote_pr==head and not status
 verify_root_sums()
 av=json.loads((E/'application-verification.json').read_text())
 applied=av['applicationCommit']
 assert applied in run(['git','rev-list',f'{BASE}..{head}']).split()
 assert run(['git','rev-parse',f'{applied}^{{tree}}'])==av['applicationTree']
 assert av['livePullRequestHead']==applied and av['branch']==BRANCH
 assert av['catalogs']=={p:sha((REPO/p).read_bytes()) for p in sorted(catalog_paths)}
print(json.dumps({'pass':True,'mode':mode,'base':BASE,'head':head,'tree':tree,'cells':240,'decisions':dict(decisions),'crossAuditResolutions':dict(resolutions),'updates':143,'updatedCatalogFiles':len(catalog_paths),'priorHoldsPreserved':23,'callerlessRank1376Holds':12,'nonTargetChanges':0,'catalogDiffCheck':'PASS','workflowFilesTouched':False,'pr':'OPEN/DRAFT'},indent=2))
