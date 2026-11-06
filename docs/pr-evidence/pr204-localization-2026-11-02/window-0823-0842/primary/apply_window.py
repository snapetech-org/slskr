#!/usr/bin/env python3
import hashlib, json, re, shutil, subprocess
from collections import Counter
from pathlib import Path
ROOT=Path('/home/keith/Documents/code/task-worktrees/localization-20261102-slskr')
PRIMARY=Path('/mnt/disks/scratch/task-scratch/slskr-pr204-window-0823-0842-primary-review-20261102')
CROSS=Path('/mnt/disks/scratch/task-scratch/slskr-pr204-window-0823-0842-crossreview-20261102')
EVIDENCE=ROOT/'docs/pr-evidence/pr204-localization-2026-11-02/window-0823-0842'
HEAD='074dfc70d584707a215e87cb1fd1969198f76b2e'
TREE='9914a55bdfb938408a4bf1f98bb5ed98c24b78a8'
LOCALES=['ar','de','es','fr','hi','id','ja','ko','pt-BR','vi','zh-Hans','zh-Hant']
def sha(x): return hashlib.sha256(x if isinstance(x,bytes) else x.encode('utf-8')).hexdigest()
def git(*args): return subprocess.check_output(['git',*args],cwd=ROOT).decode().strip()
def load_pairs(p):
 def hook(pairs):
  out={}
  for k,v in pairs:
   if k in out: raise ValueError('duplicate key: '+k)
   out[k]=v
  return out
 return json.loads(p.read_text(encoding='utf-8'),object_pairs_hook=hook)
assert git('rev-parse','HEAD')==HEAD and git('rev-parse','HEAD^{tree}')==TREE
assert git('status','--porcelain=v1')==''
assert not EVIDENCE.exists()
primary=[json.loads(x) for x in (PRIMARY/'primary-review-ledger.jsonl').read_text().splitlines()]
cross=[json.loads(x) for x in (CROSS/'cell-crossreview.jsonl').read_text().splitlines()]
assert len(primary)==len(cross)==240
pmap={(r['sourceId'],r['locale']):r for r in primary}; cmap={(r['sourceId'],r['locale']):r for r in cross}
assert len(pmap)==len(cmap)==240 and pmap.keys()==cmap.keys()
primary_pins=json.loads((PRIMARY/'catalog-pins.json').read_text())['catalogs']
cross_pins=json.loads((CROSS/'catalog-pins.json').read_text())['catalogs']
assert len(primary_pins)==len(cross_pins)==12
expected={}
for pin in primary_pins:
 assert pin['keyCount']==5441
 expected[pin['path']]=pin['fileSha256']
assert {x['path']:x['fileSha256'] for x in cross_pins}==expected
catalogs={}; before_hashes={}; key_orders={}
for loc in LOCALES:
 rel=f'web/src/lib/locales/ui-labels.{loc}.json'; path=ROOT/rel; raw=path.read_bytes()
 assert sha(raw)==expected[rel], (rel,sha(raw),expected[rel])
 data=load_pairs(path); assert len(data)==5441
 catalogs[rel]=data; before_hashes[rel]=sha(raw); key_orders[rel]=list(data)
plans=[]; counts=Counter(); changed=0
for key in sorted(pmap,key=lambda x:(pmap[x]['sourceIndex'],x[1])):
 p=pmap[key]; c=cmap[key]; source=p['sourceText']; source_id=p['sourceId']; loc=p['locale']; rel=f'web/src/lib/locales/ui-labels.{loc}.json'
 assert p['head']==HEAD and p['tree']==TREE and c['sourceId']==source_id and c['sourceText']==source
 assert sha(source)==p['sourceSha256']==c['sourceSha256']
 current=p['currentTarget']; final=c['independentFinalTarget']
 assert sha(current)==c['currentTargetSha256']
 assert sha(final)==c['independentFinalTargetSha256']
 assert catalogs[rel][source_id]==current
 assert c['placeholderParity'] and c['markupParity']
 assert c['finalProtectedMismatches']==[]
 assert Counter(re.findall(r'\{([^{}]+)\}',source))==Counter(re.findall(r'\{([^{}]+)\}',final))
 assert re.findall(r'</?[A-Za-z][^>]*>',source)==re.findall(r'</?[A-Za-z][^>]*>',final)
 assert 'Soulseek' not in source or 'Soulseek' in final
 action='update' if current!=final else 'no-op'
 if action=='update': changed+=1; catalogs[rel][source_id]=final
 counts[c['independentDisposition']]+=1
 plans.append({'sourceIndex':p['sourceIndex'],'sourceId':source_id,'source':source,'sourceSha256':p['sourceSha256'],'locale':loc,'targetFile':rel,'expectedCurrent':current,'expectedCurrentSha256':sha(current),'finalTarget':final,'finalTargetSha256':sha(final),'primaryDisposition':p['disposition'],'independentDisposition':c['independentDisposition'],'rationale':c['independentRationale'],'action':action,'callerPinCount':len(c['callerPins'])})
assert changed==56, changed
EVIDENCE.mkdir(parents=True)
shutil.copytree(PRIMARY,EVIDENCE/'primary')
shutil.copytree(CROSS,EVIDENCE/'crossreview')
(EVIDENCE/'application').mkdir()
planfile=EVIDENCE/'application/exact-hash-apply-plan.jsonl'
planfile.write_text(''.join(json.dumps(x,ensure_ascii=False,sort_keys=True)+'\n' for x in plans),encoding='utf-8')
for rel,data in catalogs.items():
 raw=(json.dumps(data,ensure_ascii=False,indent=2)+'\n').encode('utf-8'); (ROOT/rel).write_bytes(raw)
readback=[]; after_hashes={}
for rel in sorted(catalogs):
 data=load_pairs(ROOT/rel); raw=(ROOT/rel).read_bytes(); after_hashes[rel]=sha(raw)
 assert len(data)==5441 and list(data)==key_orders[rel]
 for plan in [x for x in plans if x['targetFile']==rel]:
  actual=data[plan['sourceId']]
  assert actual==plan['finalTarget'] and sha(actual)==plan['finalTargetSha256']
  readback.append({'sourceIndex':plan['sourceIndex'],'sourceId':plan['sourceId'],'locale':plan['locale'],'targetFile':rel,'expectedTargetSha256':plan['finalTargetSha256'],'actualTargetSha256':sha(actual),'targetMatches':actual==plan['finalTarget'],'keyCount':len(data),'keyOrderPreserved':True})
assert len(readback)==240 and all(x['targetMatches'] for x in readback)
(EVIDENCE/'application/readback.jsonl').write_text(''.join(json.dumps(x,ensure_ascii=False,sort_keys=True)+'\n' for x in readback),encoding='utf-8')
summary={'repository':'snapetech-org/slskR','pullRequest':204,'inputHead':HEAD,'inputTree':TREE,'window':'W823-W842','sourceCount':20,'localeCount':12,'cellCount':240,'changedCells':changed,'noOpCells':240-changed,'independentDispositionCounts':dict(counts),'catalogKeyCounts':{r:len(catalogs[r]) for r in sorted(catalogs)},'catalogKeyOrderPreserved':True,'beforeCatalogHashes':before_hashes,'afterCatalogHashes':after_hashes,'all240ReadbacksMatch':True,'placeholderMarkupProtectedLiteralChecks':'all crossreview checks passed','testsBuildsScansCI':False,'nativeSpeakerApproval':False,'browserReview':False,'workflowsReleasesTagsMerges':False}
(EVIDENCE/'application/summary.json').write_text(json.dumps(summary,ensure_ascii=False,sort_keys=True,indent=2)+'\n',encoding='utf-8')
release=ROOT/'release-notes/20261102-slskr-review-window-823-842.md'
assert not release.exists()
release.write_text('''---\ncategory: fixed\naudience: users\narea: localization\naction: none\nbreaking: false\n---\nCorrected 56 slskR translations across 12 languages for confirmation safeguards, metadata conflicts, Discography Concierge coverage, and native Soulseek product terminology.\n''',encoding='utf-8')
(EVIDENCE/'README.md').write_text('''# slskR PR #204 localization review W823–W842\n\nThe primary review and independent cross-review cover 240 cells across 20 source strings and 12 direct locales. The cross-review accepted 53 candidates, revised 3, and confirmed 184 existing values. We applied 56 exact-hash changes and kept 184 current values. All twelve catalogs retain their ordered 5,441-key set; every target was re-read against the final cross-review hash.\n\nCaller context confirms that “confirmation gates” are safety confirmations before media-server actions, conflict labels concern record/metadata conflicts, artist coverage belongs to the Discography Concierge, and “native Soulseek” is a product term. See both review packets and the exact apply/readback records here.\n\nMachine-assisted review does not establish native-speaker approval. Current-head browser acceptance remains outstanding. No tests, builds, scans, CI, workflow edits, releases, tags, merges, or deployments occurred.\n''',encoding='utf-8')
entries=[]
for p in sorted(EVIDENCE.rglob('*')):
 if p.is_file() and p.name!='SHA256SUMS': entries.append(f'{sha(p.read_bytes())}  {p.relative_to(EVIDENCE).as_posix()}')
(EVIDENCE/'SHA256SUMS').write_text('\n'.join(entries)+'\n',encoding='utf-8')
print(json.dumps({'changedCells':changed,'noOpCells':240-changed,'dispositions':dict(counts),'evidence':str(EVIDENCE),'evidenceFiles':len(entries),'afterCatalogHashes':after_hashes},ensure_ascii=False,indent=2))
