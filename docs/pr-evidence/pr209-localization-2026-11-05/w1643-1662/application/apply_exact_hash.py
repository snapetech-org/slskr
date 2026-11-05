#!/usr/bin/env python3
from __future__ import annotations
import collections, hashlib, json, subprocess, datetime
from pathlib import Path

BASE=Path('/mnt/disks/scratch/task-scratch/slskr-pr209-w1643-1662-20261105')
WORKTREE=Path('/mnt/disks/scratch/task-worktrees/localization-20261105/slskr-pr209-w1643-1662-apply')
CF=BASE/'candidate-free-input'; ROOT=BASE/'root-adjudication'; APP=BASE/'application'
HEAD='2d804c49879372071adf606bc2a2cf51e261fd94'; TREE='d6f5552d2400d868c2f2af98eb68caadfd4f3f66'
PR=209; REPO='snapetech-org/slskR'; BRANCH='codex/slskr-l10n-audit-20261104-resync'
def sha(b:bytes)->str:return hashlib.sha256(b).hexdigest()
def shat(s:str)->str:return sha(s.encode('utf-8'))
def cbytes(o)->bytes:return (json.dumps(o,ensure_ascii=False,sort_keys=True,separators=(',',':'))+'\n').encode()
def wjson(path:Path,obj)->None:path.write_text(json.dumps(obj,ensure_ascii=False,sort_keys=True,indent=2)+'\n')
def readjsonl(path:Path):return [json.loads(x) for x in path.read_text().splitlines() if x.strip()]
def git(*args):return subprocess.check_output(['git','-C',str(WORKTREE),*args],text=True).strip()
def attest(stage, expected_paths=()):
 h=git('rev-parse','HEAD'); t=git('rev-parse','HEAD^{tree}')
 status=subprocess.check_output(['git','-C',str(WORKTREE),'status','--porcelain=v1'],text=True).splitlines()
 status_paths=sorted(row[3:] for row in status)
 api=json.loads(subprocess.check_output(['gh','pr','view',str(PR),'--repo',REPO,'--json','state,isDraft,headRefName,headRefOid,baseRefOid'],text=True))
 refs=subprocess.check_output(['git','-C',str(WORKTREE),'ls-remote','origin',f'refs/heads/{BRANCH}',f'refs/pull/{PR}/head'],text=True).strip().splitlines()
 refmap={line.split('\t')[1]:line.split('\t')[0] for line in refs}
 doc={'stage':stage,'capturedAtUtc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'localHead':h,'localTree':t,'worktreeStatusPorcelain':status,'expectedWorkingTreePaths':sorted(expected_paths),'pullRequest':api,'remoteBranch':refmap.get(f'refs/heads/{BRANCH}'),'remotePullHead':refmap.get(f'refs/pull/{PR}/head')}
 status_ok=status_paths==sorted(expected_paths) and all(row[:2]==' M' for row in status)
 doc['matchesPinnedHead']=h==HEAD and t==TREE and status_ok and api.get('headRefOid')==HEAD and api.get('state')=='OPEN' and refmap.get(f'refs/heads/{BRANCH}')==HEAD and refmap.get(f'refs/pull/{PR}/head')==HEAD
 if not doc['matchesPinnedHead']:raise SystemExit('FAIL live pin: '+json.dumps(doc))
 return doc

pre=attest('application-preflight')
subprocess.run(['python3',str(ROOT/'verify_root.py')],check=True,stdout=subprocess.DEVNULL)
cfrows=readjsonl(CF/'current-target-cells.jsonl')
plan=readjsonl(APP/'apply-plan.jsonl')
assert len(cfrows)==240 and len(plan)==9
cfmap={(r['sourceKey'],r['locale']):r for r in cfrows}
planmap={(r['sourceKey'],r['locale']):r for r in plan}
assert len(cfmap)==240 and len(planmap)==9
for p in plan:
 assert p['exactHead']==HEAD and p['exactTree']==TREE
 c=cfmap[(p['sourceKey'],p['locale'])]
 assert c['currentTargetSha256']==p['expectedBeforeTargetSha256']
 assert c['sourceKeySha256']==p['sourceKeySha256'] and c['sourceContextSha256']==p['sourceContextSha256']
 assert sha(p['finalTarget'].encode())==p['finalTargetSha256']
 assert p['catalogPath']==c['catalogPath']
allowed=sorted({p['catalogPath'] for p in plan})
pre_catalogs={}; before_json={}; orders={}
for rel in allowed:
 path=WORKTREE/rel; raw=path.read_bytes(); data=json.loads(raw)
 serialized=(json.dumps(data,ensure_ascii=False,indent=2)+'\n').encode()
 if serialized!=raw: raise SystemExit('FAIL refusing reformat of '+rel)
 pre_catalogs[rel]={'sha256':sha(raw),'gitBlob':git('rev-parse',f'HEAD:{rel}'),'bytes':len(raw),'keyCount':len(data),'keyOrderSha256':shat('\0'.join(data))}
 before_json[rel]=data; orders[rel]=list(data)
wjson(APP/'preflight.json',{'exactHead':HEAD,'exactTree':TREE,'candidateFreeCells':len(cfrows),'applyPlanRows':len(plan),'changedCatalogPaths':allowed,'expectedLocaleCellChanges':9,'worktreeCleanBeforeApply':True,'livePin':pre,'catalogs':pre_catalogs,'result':'PASS'})
for p in plan:
 rel=p['catalogPath']; data=before_json[rel]
 current=data[p['sourceKey']]
 assert shat(current)==p['expectedBeforeTargetSha256']
 data[p['sourceKey']]=p['finalTarget']
for rel,data in before_json.items():
 path=WORKTREE/rel
 path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')

# Independent readback over all 240 cells plus exact per-catalog comparisons to the pinned HEAD.
readback=[]; changed=collections.Counter(); locale_read=collections.Counter()
for c in cfrows:
 rel=c['catalogPath']; data=json.loads((WORKTREE/rel).read_text()); key=c['sourceKey']; loc=c['locale']
 selected=planmap.get((key,loc)); final=data[key]; final_sha=shat(final)
 expected=selected['finalTargetSha256'] if selected else c['currentTargetSha256']
 assert final_sha==expected, (key,loc,final_sha,expected)
 assert key in data
 changed_by_plan=selected is not None
 if changed_by_plan:
  assert final==selected['finalTarget']; changed[loc]+=1
 else:
  assert final_sha==c['currentTargetSha256']
 locale_read[loc]+=1
 readback.append({'window':'W1643-W1662','sourceOrdinal':c['position'],'sourceKey':key,'sourceKeySha256':c['sourceKeySha256'],'locale':loc,'catalogPath':rel,'callerContextSha256':c['sourceContextSha256'],'beforeTargetSha256':c['currentTargetSha256'],'finalTargetSha256':final_sha,'changedByPlan':changed_by_plan,'rootRowSha256':selected['rootAdjudicationRowSha256'] if selected else None,'crossReviewRowSha256':selected['crossReviewRowSha256'] if selected else None,'placeholderSequenceMatches':c['placeholderSequenceMatches'] if 'placeholderSequenceMatches' in c else True,'markupMatches':c.get('markupMatches',True),'numericTokensMatch':c.get('numericTokensMatch',True),'protectedLiteralsMatch':c.get('protectedLiteralsMatch',True)})
# Check exact pre-application HEAD values and key order for every key in changed catalogs.
file_rows={}
for rel in allowed:
 before=json.loads(subprocess.check_output(['git','-C',str(WORKTREE),'show',f'HEAD:{rel}'],text=True))
 after=json.loads((WORKTREE/rel).read_text())
 assert list(before)==list(after)==orders[rel]
 selected_keys={p['sourceKey'] for p in plan if p['catalogPath']==rel}
 assert {k for k in before if before[k]!=after[k]}==selected_keys
 file_rows[rel]={'beforeSha256':pre_catalogs[rel]['sha256'],'afterSha256':sha((WORKTREE/rel).read_bytes()),'gitBlobBefore':pre_catalogs[rel]['gitBlob'],'keyCount':len(after),'keyOrderPreserved':True,'changedKeys':sorted(selected_keys),'changedCount':len(selected_keys),'allNonTargetValuesUnchanged':True}
assert sum(changed.values())==9 and all(v==20 for v in locale_read.values())
assert len(readback)==240 and sum(1 for r in readback if r['changedByPlan'])==9
(APP/'application-readback.jsonl').write_bytes(b''.join(cbytes(r) for r in readback))
summary={'artifact':'slskR PR #209 W1643-W1662 exact-hash catalog application','exactSourceHead':HEAD,'exactSourceTree':TREE,'cellsReviewed':240,'cellsApplied':9,'readbackMatches':240,'readbackMismatches':0,'changedByLocale':dict(sorted(changed.items())),'localeCellCounts':dict(sorted(locale_read.items())),'keyOrderPreserved':True,'unselectedCatalogValuesUnchanged':True,'changedCatalogs':file_rows,'workflowFilesChanged':False,'testsBuildsScansOrCI':False,'nativeSpeakerApproval':False,'result':'PASS'}
wjson(APP/'application-summary.json',summary)
post=attest('after-application-before-commit',allowed)
wjson(APP/'live-attestation-after-application.json',post)
print(json.dumps({'result':'PASS','cells':len(readback),'applied':9,'changedByLocale':dict(changed),'catalogs':len(allowed),'keyOrderPreserved':True,'nonTargetValuesUnchanged':True,'livePinBeforeApply':pre['matchesPinnedHead'],'livePinAfterApply':post['matchesPinnedHead'],'productWorktree':str(WORKTREE)},ensure_ascii=False,indent=2))
