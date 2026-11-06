#!/usr/bin/env python3
from pathlib import Path
import collections,hashlib,json
E=Path(__file__).resolve().parent
BASE='281c39ec0cdb3677d7d523b7c4f0cd0d52bbf14c'
TREE='777b234b1aa3cb7a2c9fd560b2c0fecc4e7fe49d'
def rows(p): return [json.loads(x) for x in p.read_text(encoding='utf-8').splitlines() if x.strip()]
im=json.loads((E/'candidate-free-input/manifest.json').read_text())
xm=json.loads((E/'cross-audit/manifest.json').read_text())
assert (im['head'],im['tree'],im['repository'],im['pullRequest'])==(BASE,TREE,'snapetech-org/slskR',204)
assert (xm['head'],xm['tree'],xm['repository'],xm['pullRequest'])==(BASE,TREE,'snapetech-org/slskR',204)
cells=rows(E/'candidate-free-input/current-target-cells.jsonl')
audit=rows(E/'cross-audit/resolution-ledger.jsonl')
assert len(cells)==len(audit)==240
idx=lambda a:{(r['position'],r['locale']):r for r in a}
ci,ai=idx(cells),idx(audit);assert ci.keys()==ai.keys()
decisions=collections.Counter();resolutions=collections.Counter();allplan=[];updates=[]
for key in sorted(ci):
 c,a=ci[key],ai[key]
 assert a['sourceKey']==c['sourceKey'] and a['sourceKeySha256']==c['sourceKeySha256']
 assert a['currentTarget']==c['currentTarget'] and a['currentTargetSha256']==c['currentTargetSha256']
 assert a['sourceContextSha256']==c['sourceContextSha256']
 selected=a['selectedTarget'] if a['selectedTarget'] is not None else c['currentTarget']
 if a['selectedTarget'] is not None: assert a['selectedTargetSha256']==hashlib.sha256(selected.encode()).hexdigest()
 assert a['callerless']==(c['callerCount']==0)
 d=a['selectedDisposition'];decisions[d]+=1;resolutions[a['resolution']]+=1
 assert d in ('accept-current','correction','refinement','hold')
 checks=a['tokenAndRuntimeChecks']
 if d=='hold':
  assert c['position']==1376 and a['callerless'] and selected==c['currentTarget']
 else:
  assert not a['callerless']
  assert all(checks[x] for x in ['placeholdersPreserved','numericTokensPreserved','markupPreserved','protectedLiteralsPreserved','pathExamplesPreservedExactlyOnce','runtimeUsesDirectLookupAndNamedSubstitution'])
  assert checks['missingProtectedLiterals']==[]
  assert (selected==c['currentTarget'])==(d=='accept-current')
 path=c['catalogPath']
 row={'position':c['position'],'locale':c['locale'],'sourceKey':c['sourceKey'],'sourceKeySha256':c['sourceKeySha256'],'sourceContextSha256':c['sourceContextSha256'],'catalogPath':path,'catalogFileSha256':c['catalogFileSha256'],'catalogGitBlob':c['catalogGitBlob'],'catalogKeyCount':c['catalogKeyCount'],'currentTarget':c['currentTarget'],'currentTargetSha256':c['currentTargetSha256'],'selectedTarget':selected,'selectedTargetSha256':hashlib.sha256(selected.encode()).hexdigest(),'selectedDisposition':d,'resolution':a['resolution'],'callerless':a['callerless'],'callerCount':c['callerCount']}
 row['changed']=row['selectedTarget']!=row['currentTarget']
 allplan.append(row)
 if row['changed']: updates.append(row)
assert decisions==collections.Counter({'accept-current':85,'correction':27,'refinement':116,'hold':12}),decisions
assert resolutions==collections.Counter({'agreement':35,'hold-consensus':12,'primary-selected':61,'blind-selected':132}),resolutions
assert len(updates)==143
assert len({x['locale'] for x in cells})==12
assert {x['position'] for x in allplan if x['selectedDisposition']=='hold'}=={1376}
assert len({x['sourceKey'] for x in cells})==20
doc={'schemaVersion':1,'repository':'snapetech-org/slskR','pullRequest':204,'branch':'codex/slskr-l10n-audit-20261030','baseHead':BASE,'baseTree':TREE,'reviewedCells':240,'decisionCounts':dict(sorted(decisions.items())),'crossAuditResolutionCounts':dict(sorted(resolutions.items())),'changedCells':143,'changedCatalogFiles':len({x['catalogPath'] for x in updates}),'updates':updates,'allCellReadbackPlan':allplan,'priorHoldsExpected':23,'callerlessRank1376Holds':12}
(E/'apply-plan.json').write_text(json.dumps(doc,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'pass':True,'cells':240,'decisions':dict(decisions),'resolutions':dict(resolutions),'updates':143,'catalogs':doc['changedCatalogFiles'],'holds':12},indent=2))
