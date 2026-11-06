#!/usr/bin/env python3
import collections, hashlib, json, re, subprocess
from pathlib import Path

ROOT = Path('/mnt/disks/scratch/task-scratch')
PACKET = ROOT/'slskr-pr204-w1143-1162-primary-20261103'
BLIND = ROOT/'slskr-pr204-w1143-1162-independent-blind-20261103'
CROSS = ROOT/'slskr-pr204-w1143-1162-third-party-cross-audit-20261103'
OUT = ROOT/'slskr-pr204-w1143-1162-application-20261103'
WT = Path('/mnt/disks/scratch/task-worktrees/localization-20261103/slskr-pr204-w1123-1142-apply')

def sha(s): return hashlib.sha256(s.encode('utf-8')).hexdigest()
def read_jsonl(path): return [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines() if line]
def key(row): return (row.get('position', row.get('sourcePosition')), row['locale'])
def placeholders(s): return sorted(re.findall(r'\{[^{}]+\}', s))
def git_blob(path): return subprocess.check_output(['git','-C',str(WT),'hash-object',str(path.relative_to(WT))],text=True).strip()

inp_rows=read_jsonl(PACKET/'clean-input/current-target-cells.jsonl')
primary=read_jsonl(PACKET/'primary-review/review-decisions.jsonl')
blind=read_jsonl(BLIND/'blind-ledger.jsonl')
cross=read_jsonl(CROSS/'third-party-decisions.jsonl')
for label,rows in [('input',inp_rows),('primary',primary),('blind',blind),('cross-audit',cross)]:
    if len(rows)!=240 or len({key(r) for r in rows})!=240:
        raise SystemExit(f'{label} coverage/uniqueness failure: {len(rows)}')
idx={}
for label,rows in [('input',inp_rows),('primary',primary),('blind',blind),('cross-audit',cross)]:
    idx[label]={key(r):r for r in rows}
if any(set(idx[a])!=set(idx['input']) for a in ('primary','blind','cross-audit')):
    raise SystemExit('ledger key sets differ')
pins=json.loads((PACKET/'clean-input/catalog-file-pins.json').read_text())
manifest=json.loads((PACKET/'clean-input/manifest.json').read_text())
if manifest['head']!='20c66f7889c564fae5db1128d7dde22b512fc5be' or manifest['tree']!='85e82d73c6c191ea4875850d3c1afff7bae5c63a':
    raise SystemExit('unexpected exact-head manifest')
# Re-attest all pinned catalog files and ordered key sets before applying.
key_orders={}
for rel,pin in pins.items():
    path=WT/rel
    data=path.read_bytes()
    if hashlib.sha256(data).hexdigest()!=pin['sha256']:
        raise SystemExit(f'catalog file hash mismatch: {rel}')
    if git_blob(path)!=pin['gitBlob']:
        raise SystemExit(f'catalog Git blob mismatch: {rel}')
    obj=json.loads(data)
    if len(obj)!=pin['keyCount']:
        raise SystemExit(f'catalog key count mismatch: {rel}')
    key_orders[rel]=list(obj)
if len({tuple(v) for v in key_orders.values()})!=1:
    raise SystemExit('ordered key sequences differ at baseline')

ratified=[]
plan=[]
counts=collections.Counter()
for k in sorted(idx['input']):
    i=idx['input'][k]; p=idx['primary'][k]; b=idx['blind'][k]; c=idx['cross-audit'][k]
    if c['sourceId']!=i['sourceId'] or c['source']!=i['source'] or c['sourceSha256']!=i['sourceSha256']:
        raise SystemExit(f'source pin mismatch {k}')
    if c['currentTarget']!=i['currentTarget'] or c['currentTargetSha256']!=i['currentTargetSha256']:
        raise SystemExit(f'current target pin mismatch {k}')
    if c['callerContextSha256']!=i['callerContextSha256']:
        raise SystemExit(f'caller context mismatch {k}')
    if p.get('sourceSha256')!=i['sourceSha256'] or p.get('currentTargetSha256')!=i['currentTargetSha256']:
        raise SystemExit(f'primary pin mismatch {k}')
    if b.get('sourceSha256')!=i['sourceSha256'] or b.get('currentTargetSha256')!=i['currentTargetSha256']:
        raise SystemExit(f'blind pin mismatch {k}')
    if b.get('sourceId')!=i['sourceId'] or b.get('callerContextSha256')!=i['callerContextSha256']:
        raise SystemExit(f'blind source/caller context mismatch {k}')
    if c['checks'].get('sourceHash') is not True or c['checks'].get('currentHash') is not True or c['checks'].get('placeholderPreservation') is not True or c['checks'].get('primaryProtectedLiterals') is not True:
        raise SystemExit(f'cross-audit integrity failure {k}')
    disp=c['recommendedDisposition']
    if disp not in ('accept-current','correction','refinement','hold'):
        raise SystemExit(f'unknown disposition {disp} at {k}')
    target=c['recommendedValue'] if disp in ('correction','refinement') else i['currentTarget']
    if disp in ('correction','refinement') and (not target or target==i['currentTarget']):
        raise SystemExit(f'change disposition without a distinct target at {k}')
    if disp in ('accept-current','hold') and target!=i['currentTarget']:
        raise SystemExit(f'no-op disposition changes target at {k}')
    if placeholders(i['source'])!=placeholders(target):
        raise SystemExit(f'placeholder mismatch {k}')
    for literal in c.get('protectedLiterals',[]):
        if literal not in target:
            raise SystemExit(f'protected literal mismatch {k}: {literal!r}')
    counts[disp]+=1
    locale_path=next((rel for rel in pins if rel.endswith(f'.{i["locale"]}.json')),None)
    if not locale_path:
        raise SystemExit(f'no catalog path for {i["locale"]}')
    row={
        'position':i['position'],'sourceId':i['sourceId'],'source':i['source'],'locale':i['locale'],
        'sourceSha256':i['sourceSha256'],'currentTarget':i['currentTarget'],'currentTargetSha256':i['currentTargetSha256'],
        'callerContextSha256':i['callerContextSha256'],'directLocalizedCaller':c['directLocalizedCaller'],
        'disposition':disp,'finalTarget':target,'finalTargetSha256':sha(target),
        'rationale':c['adjudicationRationale'],'primaryDisposition':c['primaryDisposition'],
        'blindDisposition':c['blindDisposition'],'primaryCandidateTarget':c['primaryCandidateTarget'],
        'blindProposalTarget':c['blindProposalTarget'],'crossAuditChecks':c['checks'],
    }
    ratified.append(row)
    if target!=i['currentTarget']:
        plan.append({'position':i['position'],'sourceId':i['sourceId'],'locale':i['locale'],'path':locale_path,
                     'expectedCurrent':i['currentTarget'],'expectedCurrentSha256':i['currentTargetSha256'],
                     'finalTarget':target,'finalTargetSha256':sha(target),'disposition':disp,
                     'callerContextSha256':i['callerContextSha256'],'rationale':c['adjudicationRationale']})
if counts!=collections.Counter({'accept-current':186,'correction':20,'refinement':20,'hold':14}):
    raise SystemExit(f'unexpected ratified counts {counts}')
if len(plan)!=40:
    raise SystemExit(f'unexpected change count {len(plan)}')
for name,rows in [('ratified-ledger.jsonl',ratified),('apply-plan.jsonl',plan)]:
    (OUT/name).write_text(''.join(json.dumps(row,ensure_ascii=False,sort_keys=True)+'\n' for row in rows),encoding='utf-8')
summary={
 'repository':'snapetech-org/slskr','pullRequest':204,'window':'W1143-W1162',
 'baseHead':manifest['head'],'baseTree':manifest['tree'],'sourceCount':20,'localeCount':12,'cellCount':240,
 'ratifiedDispositions':dict(sorted(counts.items())),'appliedChanges':len(plan),'heldCells':counts['hold'],
 'holdPositions':sorted({r['position'] for r in ratified if r['disposition']=='hold'}),
 'catalogKeyCount':5441,'orderedCatalogSequencesUnchanged':True,'numericFiveSecondManuallyReconciled':True,
 'checksums':{
   'candidateFreeManifestSha256':hashlib.sha256((PACKET/'clean-input/manifest.json').read_bytes()).hexdigest(),
   'primaryLedgerSha256':hashlib.sha256((PACKET/'primary-review/review-decisions.jsonl').read_bytes()).hexdigest(),
   'blindLedgerSha256':hashlib.sha256((BLIND/'blind-ledger.jsonl').read_bytes()).hexdigest(),
   'thirdPartyCrossAuditSha256':hashlib.sha256((CROSS/'third-party-decisions.jsonl').read_bytes()).hexdigest(),
 },
 'nativeSpeakerApproval':False,'browserAcceptance':False,'testsBuildsScansCI':False,'workflowsChanged':False,
}
(OUT/'ratification-summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(summary,ensure_ascii=False,indent=2))
