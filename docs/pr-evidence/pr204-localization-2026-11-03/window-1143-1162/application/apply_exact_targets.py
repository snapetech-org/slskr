#!/usr/bin/env python3
import hashlib,json,subprocess
from pathlib import Path

OUT=Path('/mnt/disks/scratch/task-scratch/slskr-pr204-w1143-1162-application-20261103')
WT=Path('/mnt/disks/scratch/task-worktrees/localization-20261103/slskr-pr204-w1123-1142-apply')
PLAN=OUT/'apply-plan.jsonl'
PINS=Path('/mnt/disks/scratch/task-scratch/slskr-pr204-w1143-1162-primary-20261103/clean-input/catalog-file-pins.json')
EXPECTED_HEAD='20c66f7889c564fae5db1128d7dde22b512fc5be'

def sha(data): return hashlib.sha256(data).hexdigest()
def sha_text(s): return sha(s.encode('utf-8'))
def git_blob(rel): return subprocess.check_output(['git','-C',str(WT),'hash-object',rel],text=True).strip()

if subprocess.check_output(['git','-C',str(WT),'rev-parse','HEAD'],text=True).strip()!=EXPECTED_HEAD:
    raise SystemExit('HEAD moved')
if subprocess.check_output(['git','-C',str(WT),'status','--porcelain'],text=True).strip():
    raise SystemExit('worktree is dirty')
pins=json.loads(PINS.read_text())
plan=[json.loads(line) for line in PLAN.read_text().splitlines() if line]
if len(plan)!=40 or len({(r['position'],r['locale']) for r in plan})!=40:
    raise SystemExit('apply-plan coverage/uniqueness failure')
by_path={}
for row in plan:
    rel=row['path']; by_path.setdefault(rel,[]).append(row)
# Validate all 12 catalog pins before constructing any output.
before={}; objs={}; key_orders={}
for rel,pin in pins.items():
    path=WT/rel; data=path.read_bytes()
    if sha(data)!=pin['sha256'] or git_blob(rel)!=pin['gitBlob']:
        raise SystemExit(f'catalog pin changed: {rel}')
    obj=json.loads(data)
    if len(obj)!=pin['keyCount']:
        raise SystemExit(f'key count mismatch: {rel}')
    before[rel]=data; objs[rel]=obj; key_orders[rel]=list(obj)
if len({tuple(v) for v in key_orders.values()})!=1:
    raise SystemExit('catalog key order mismatch before apply')
# Build the complete result in memory, checking exact current values and unique JSON line matches.
updates={}
for rel,rows in by_path.items():
    text=before[rel].decode('utf-8')
    for row in rows:
        if sha_text(row['expectedCurrent'])!=row['expectedCurrentSha256'] or sha_text(row['finalTarget'])!=row['finalTargetSha256']:
            raise SystemExit(f'plan hash mismatch at {row["position"]}:{row["locale"]}')
        if objs[rel].get(row['sourceId'])!=row['expectedCurrent']:
            raise SystemExit(f'expected current value mismatch at {row["position"]}:{row["locale"]}')
        old=json.dumps(row['sourceId'],ensure_ascii=False)+': '+json.dumps(row['expectedCurrent'],ensure_ascii=False)
        new=json.dumps(row['sourceId'],ensure_ascii=False)+': '+json.dumps(row['finalTarget'],ensure_ascii=False)
        if text.count(old)!=1:
            raise SystemExit(f'expected one exact JSON entry for {row["position"]}:{row["locale"]}, got {text.count(old)}')
        text=text.replace(old,new,1)
        objs[rel][row['sourceId']]=row['finalTarget']
    updates[rel]=text.encode('utf-8')
# Apply to disk only after every path and target passed preflight.
for rel,data in updates.items():
    (WT/rel).write_bytes(data)
# Full readback: all 240 cells match final ledger; only exact target entries changed; key order is stable.
ratified=[json.loads(line) for line in (OUT/'ratified-ledger.jsonl').read_text().splitlines() if line]
readback=[]
for row in ratified:
    rel=next(path for path in pins if path.endswith(f'.{row["locale"]}.json'))
    obj=json.loads((WT/rel).read_text(encoding='utf-8'))
    value=obj.get(row['sourceId'])
    if value!=row['finalTarget'] or sha_text(value)!=row['finalTargetSha256']:
        raise SystemExit(f'readback mismatch at {row["position"]}:{row["locale"]}')
    readback.append({'position':row['position'],'sourceId':row['sourceId'],'locale':row['locale'],'finalTarget':value,'finalTargetSha256':sha_text(value),'disposition':row['disposition']})
for rel,pin in pins.items():
    data=(WT/rel).read_bytes(); obj=json.loads(data)
    if len(obj)!=pin['keyCount'] or list(obj)!=key_orders[rel]:
        raise SystemExit(f'ordered key or count changed: {rel}')
summary={
 'repository':'snapetech-org/slskr','pullRequest':204,'window':'W1143-W1162','baseHead':EXPECTED_HEAD,
 'appliedCells':len(plan),'readbackCells':len(readback),'readbackMismatches':0,
 'changedCatalogs':len(updates),'orderedCatalogSequencesUnchanged':True,'catalogKeysPerLocale':5441,
 'files':{rel:{'beforeSha256':sha(before[rel]),'afterSha256':sha((WT/rel).read_bytes()),'afterGitBlob':git_blob(rel)} for rel in sorted(updates)},
 'nativeSpeakerApproval':False,'browserAcceptance':False,'testsBuildsScansCI':False,'workflowsChanged':False,
}
(OUT/'readback.jsonl').write_text(''.join(json.dumps(x,ensure_ascii=False,sort_keys=True)+'\n' for x in readback),encoding='utf-8')
(OUT/'readback-summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(summary,ensure_ascii=False,indent=2))
