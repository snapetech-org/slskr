import json, pathlib, hashlib, collections, sys
base=pathlib.Path('/home/keith/Documents/code/task-scratch/slskr-pr204-w1503-primary-20261104')
inp=base/'candidate-free-input'
rows=[json.loads(l) for l in (base/'primary-ledger.jsonl').read_text().splitlines()]
manifest=json.loads((inp/'manifest.json').read_text())
expected=[json.loads(l) for l in (inp/'current-target-cells.jsonl').read_text().splitlines()]
assert len(rows)==240==len(expected)
assert len({(r['position'],r['locale']) for r in rows})==240
by={(r['position'],r['locale']):r for r in rows}
for c in expected:
 r=by[(c['position'],c['locale'])]
 assert r['sourceId']==c['sourceKeySha256'] and r['sourceKey']==c['sourceKey']
 assert r['currentTarget']==c['currentTarget']
 assert r['pins']['head']==manifest['head'] and r['pins']['tree']==manifest['tree']
 for k in ['sourceKeySha256','currentTargetSha256','sourceContextSha256','catalogPath','catalogGitBlob','catalogFileSha256']:
  assert r['pins'][k]==c[k],(r['position'],r['locale'],k)
 assert all(r['checks'].values())
 if r['disposition'] in ('correction','refinement'):
  assert r['proposedTarget'] and r['proposedTarget']!=r['currentTarget']
 else: assert r['proposedTarget'] is None
 if r['disposition']=='hold': assert not r['holdText']
assert all(r['disposition'] in ['accept-current','correction','refinement','hold'] for r in rows)
counts=collections.Counter(r['disposition'] for r in rows)
assert counts=={'accept-current':237,'refinement':2,'correction':1}
att1=json.loads((inp/'PR-attestation.json').read_text()); att2=json.loads((inp/'PR-attestation-after.json').read_text())
identity=['repository','pullRequest','state','draft','head','tree','headRef','branchRef','pullRef','baseRef','baseSha','mainRef']
assert all(att1[k]==att2[k] for k in identity)
assert att1['deploymentsForHeadCount']==att2['deploymentsForHeadCount']==0
assert att1['repositoryDeploymentCount']==att2['repositoryDeploymentCount']==0
assert att1['actionsRunsForHeadCount']==att2['actionsRunsForHeadCount']==0
print(json.dumps({'result':'PASS','rows':len(rows),'sources':len({r['sourceId'] for r in rows}),'counts':counts,'pins':'exact match','placeholder_markup_numeric_protected_checks':'240/240 pass','holdText':'empty on all holds','PR_refs_stable':True,'deployments_before_after':[0,0],'actions_runs_before_after':[0,0]},ensure_ascii=False,default=dict))
