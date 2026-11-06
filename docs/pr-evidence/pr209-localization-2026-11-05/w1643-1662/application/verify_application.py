#!/usr/bin/env python3
from __future__ import annotations
import collections, hashlib, json, subprocess, datetime
from pathlib import Path

BASE=Path('/mnt/disks/scratch/task-scratch/slskr-pr209-w1643-1662-20261105')
WORKTREE=Path('/mnt/disks/scratch/task-worktrees/localization-20261105/slskr-pr209-w1643-1662-apply')
CF=BASE/'candidate-free-input'; APP=BASE/'application'
HEAD='2d804c49879372071adf606bc2a2cf51e261fd94'; TREE='d6f5552d2400d868c2f2af98eb68caadfd4f3f66'
PR=209; REPO='snapetech-org/slskR'; BRANCH='codex/slskr-l10n-audit-20261104-resync'
def sha(b):return hashlib.sha256(b).hexdigest()
def shat(s):return sha(s.encode('utf-8'))
def jl(p):return [json.loads(x) for x in p.read_text().splitlines() if x.strip()]
def git(*args):return subprocess.check_output(['git','-C',str(WORKTREE),*args],text=True).strip()
def wjson(p,o):p.write_text(json.dumps(o,ensure_ascii=False,sort_keys=True,indent=2)+'\n')
# The worktree is expected to contain only the exact catalog edits in the apply plan.
h=git('rev-parse','HEAD'); t=git('rev-parse','HEAD^{tree}')
plan=jl(APP/'apply-plan.jsonl'); cf=jl(CF/'current-target-cells.jsonl'); readback=jl(APP/'application-readback.jsonl')
assert h==HEAD and t==TREE and len(plan)==9 and len(cf)==240 and len(readback)==240
planmap={(r['sourceKey'],r['locale']):r for r in plan}; cfmap={(r['sourceKey'],r['locale']):r for r in cf}; rbmap={(r['sourceKey'],r['locale']):r for r in readback}
assert len(planmap)==9 and len(cfmap)==240 and len(rbmap)==240
expected_paths=sorted({r['catalogPath'] for r in plan})
changed_paths=git('diff','--name-only','HEAD').splitlines()
assert sorted(changed_paths)==expected_paths, (changed_paths,expected_paths)
porcelain=subprocess.check_output(['git','-C',str(WORKTREE),'status','--porcelain=v1'],text=True).splitlines()
assert sorted([x[3:] for x in porcelain])==expected_paths and all(x[:2]==' M' for x in porcelain),porcelain
for rel in expected_paths:
 before=json.loads(subprocess.check_output(['git','-C',str(WORKTREE),'show',f'HEAD:{rel}'],text=True))
 raw=(WORKTREE/rel).read_bytes(); after=json.loads(raw)
 assert raw==(json.dumps(after,ensure_ascii=False,indent=2)+'\n').encode()
 assert list(before)==list(after)
 selected={r['sourceKey']:r for r in plan if r['catalogPath']==rel}
 changed={k for k in before if before[k]!=after[k]}
 assert changed==set(selected),(rel,changed,set(selected))
 for key,p in selected.items():
  assert shat(before[key])==p['expectedBeforeTargetSha256']
  assert after[key]==p['finalTarget'] and shat(after[key])==p['finalTargetSha256']
 for key in before:
  if key not in selected: assert before[key]==after[key],(rel,key)
for ident,c in cfmap.items():
 r=rbmap[ident]; p=planmap.get(ident)
 rel=c['catalogPath']; data=json.loads((WORKTREE/rel).read_text())
 final=data[c['sourceKey']]; digest=shat(final)
 expected=p['finalTargetSha256'] if p else c['currentTargetSha256']
 assert digest==expected==r['finalTargetSha256']
 assert r['changedByPlan']==(p is not None)
 assert r['sourceKeySha256']==c['sourceKeySha256'] and r['callerContextSha256']==c['sourceContextSha256']
 assert r['beforeTargetSha256']==c['currentTargetSha256']
 assert r['catalogPath']==rel
assert sum(1 for r in readback if r['changedByPlan'])==9
summary=json.loads((APP/'application-summary.json').read_text())
assert summary['cellsApplied']==9 and summary['readbackMatches']==240 and summary['readbackMismatches']==0
assert summary['keyOrderPreserved'] is True and summary['unselectedCatalogValuesUnchanged'] is True
assert not any(p.startswith('.github/workflows/') for p in changed_paths)
subprocess.run(['git','-C',str(WORKTREE),'diff','--check','HEAD'],check=True,stdout=subprocess.DEVNULL)
api=json.loads(subprocess.check_output(['gh','pr','view',str(PR),'--repo',REPO,'--json','state,isDraft,headRefName,headRefOid,baseRefOid'],text=True))
refs=subprocess.check_output(['git','-C',str(WORKTREE),'ls-remote','origin',f'refs/heads/{BRANCH}',f'refs/pull/{PR}/head'],text=True).strip().splitlines()
refmap={line.split('\t')[1]:line.split('\t')[0] for line in refs}
assert api.get('headRefOid')==HEAD and api.get('state')=='OPEN'
assert refmap.get(f'refs/heads/{BRANCH}')==HEAD and refmap.get(f'refs/pull/{PR}/head')==HEAD
att={'stage':'after-application-before-commit','capturedAtUtc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'localHead':h,'localTree':t,'expectedWorkingTreeChanges':expected_paths,'worktreeStatusPorcelain':porcelain,'pullRequest':api,'remoteBranch':refmap.get(f'refs/heads/{BRANCH}'),'remotePullHead':refmap.get(f'refs/pull/{PR}/head'),'matchesPinnedHeadAndExpectedChanges':True}
wjson(APP/'live-attestation-after-application.json',att)
print(json.dumps({'result':'PASS','head':h,'tree':t,'cellsReadBack':240,'targetEdits':9,'changedLocales':len(expected_paths),'expectedWorkingTreeFiles':expected_paths,'nonTargetValuesUnchanged':True,'keyOrderPreserved':True,'workflowChanges':0,'gitDiffCheck':'PASS','livePRBranchPullRefs':'PASS'},ensure_ascii=False,indent=2))
