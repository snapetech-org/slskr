#!/usr/bin/env python3
"""Verify the primary semantic review packet against its sealed candidate-free input."""
import collections, hashlib, importlib.util, json, re
from pathlib import Path
ROOT=Path(__file__).resolve().parent
INPUT=Path('/mnt/disks/scratch/task-scratch/slskr-pr209-w1623-1642-20261105/candidate-free-input')
HEAD='7e366cbf21ad5490bd11ef418a0f2a98b3fbd567'; TREE='801d7a037c15dcd83b3e038160054a46c9b8f03b'
LOCS=['es','zh-Hans','hi','de','ja','fr','pt-BR','ar','ko','zh-Hant','vi','id']
sys_modules=__import__('sys'); sys_modules.dont_write_bytecode=True
spec=importlib.util.spec_from_file_location('candidate_helper',INPUT/'candidate-free-schema-helper.py'); h=importlib.util.module_from_spec(spec); spec.loader.exec_module(h)
sha,canon=h.sha,h.canon

def j(path): return json.loads(path.read_text(encoding='utf-8'))
def jl(path): return [json.loads(s) for s in path.read_text(encoding='utf-8').splitlines() if s]
def require(condition,message):
    if not condition: raise SystemExit('FAIL: '+message)
def sums(directory):
    listed={}
    for line in (directory/'SHA256SUMS.txt').read_text(encoding='utf-8').splitlines():
        digest,name=line.split(None,1); name=name.lstrip('* ')
        require(name not in listed,'duplicate checksum '+name); listed[name]=digest
    actual={p.name for p in directory.iterdir() if p.is_file() and p.name!='SHA256SUMS.txt'}
    require(set(listed)==actual,'checksum file coverage '+str(directory))
    for name,digest in listed.items(): require(sha((directory/name).read_bytes())==digest,'checksum '+name)
    return listed

def token_ok(source,target):
    st,tt=h.toks(source),h.toks(target)
    missing=[x for x in st[3] if x not in tt[3]]
    return st[0]==tt[0] and st[1]==tt[1] and st[2]==tt[2] and not missing

sums(ROOT); input_sums=sums(INPUT); input_manifest=j(INPUT/'manifest.json')
require(input_manifest['head']==HEAD and input_manifest['tree']==TREE,'candidate-free exact head/tree')
require(input_manifest['selectedPositions']==[1623,1642] and input_manifest['cellCount']==240,'candidate-free window scope')
require(input_manifest['candidateFreeInputOnly'] is True and input_manifest['proposedTranslationsIncluded'] is False,'candidate-free input type')
manifest=j(ROOT/'manifest.json'); summary=j(ROOT/'summary.json')
require(manifest['exactHead']==HEAD and manifest['exactTree']==TREE,'primary manifest pin')
require(manifest['candidateFreeChecksumListSha256']==sha((INPUT/'SHA256SUMS.txt').read_bytes()),'candidate-free checksum pin')
for name,expected in manifest['files'].items():
    require((ROOT/name).is_file() and sha((ROOT/name).read_bytes())==expected,'primary manifest file '+name)
require(summary['exactHead']==HEAD and summary['exactTree']==TREE,'summary pin')
require(summary['candidateFreeChecksumListSha256']==sha((INPUT/'SHA256SUMS.txt').read_bytes()),'summary input pin')
require(summary['blindReviewPerformed'] is False and summary['crossReviewPerformed'] is False,'review scope')
require(summary['nativeSpeakerReviewPerformed'] is False and summary['browserReviewPerformed'] is False,'review limitations')
require(summary['repoOrPrEditsMade'] is False and summary['workflowEditsMade'] is False,'edit scope')
require(summary['projectTestsRun'] is False and summary['projectBuildsRun'] is False and summary['ciDispatched'] is False,'no project tests/builds/CI')
require(input_manifest['callerResolutionHoldCount']==0,'no callerless rows in window')

cells=jl(INPUT/'current-target-cells.jsonl'); contexts={x['position']:x for x in jl(INPUT/'source-contexts.jsonl')}
ledger=jl(ROOT/'primary-ledger.jsonl'); proposals=jl(ROOT/'proposals.jsonl'); holds=jl(ROOT/'holds-hash-only.jsonl')
require(len(cells)==len(ledger)==240,'240-cell coverage')
require([(x['position'],x['locale']) for x in ledger]==[(x['position'],x['locale']) for x in cells],'ledger order')
require(len({(x['position'],x['locale']) for x in ledger})==240,'unique ledger cells')
counts=collections.Counter(x['decision'] for x in ledger)
require(dict(counts)==summary['decisionCounts'],'summary decision counts')
require(dict(counts)=={'accept-current':231,'correction':9},'review decision totals')
require(len(proposals)==9 and len(holds)==0,'proposal and hold counts')
expected_proposals=[(x['position'],x['locale']) for x in ledger if x['decision'] in {'correction','refinement'}]
require([(x['position'],x['locale']) for x in proposals]==expected_proposals,'proposal subset/order')
for src,row in zip(cells,ledger):
    cell=(src['position'],src['locale'])
    require(row['exactHead']==HEAD and row['exactTree']==TREE,'row pin '+str(cell))
    require(row['position']==src['position'] and row['locale']==src['locale'],'row identity '+str(cell))
    require(row['sourceKey']==src['sourceKey'] and row['sourceKeySha256']==src['sourceKeySha256'],'source key '+str(cell))
    require(row['sourceTextSha256']==sha(src['sourceKey']),'source hash '+str(cell))
    require(row['currentTarget']==src['currentTarget'] and row['currentTargetSha256']==src['currentTargetSha256'],'current target '+str(cell))
    require(row['sourceContextSha256']==src['sourceContextSha256'],'caller context '+str(cell))
    require(row['callerCount']==src['callerCount'] and row['callerCount']>0,'caller count '+str(cell))
    require(row['candidateFreeCellRecordSha256']==sha(canon(src)),'candidate-free row hash '+str(cell))
    require(row['catalogPath']==src['catalogPath'] and row['catalogFileSha256']==src['catalogFileSha256'] and row['catalogGitBlob']==src['catalogGitBlob'],'catalog pins '+str(cell))
    require(token_ok(src['sourceKey'],src['currentTarget']),'current token integrity '+str(cell))
    if row['decision'] in {'correction','refinement'}:
        require('proposedTarget' in row and row.get('rationale'),'proposal details '+str(cell))
        require(row['proposedTargetSha256']==sha(row['proposedTarget']),'proposal hash '+str(cell))
        require(token_ok(src['sourceKey'],row['proposedTarget']),'proposal token integrity '+str(cell))
    elif row['decision']=='accept-current':
        require('proposedTarget' not in row,'unexpected proposal '+str(cell))
    elif row['decision']=='hold':
        required_absent={'sourceKey','currentTarget','proposedTarget'}
        require(not (required_absent & set(row)),'hash-only hold text '+str(cell))
    else: raise SystemExit('FAIL: unknown decision '+str(cell))
for proposal in proposals:
    row=next(x for x in ledger if (x['position'],x['locale'])==(proposal['position'],proposal['locale']))
    require(proposal['proposedTarget']==row['proposedTarget'] and proposal['proposedTargetSha256']==row['proposedTargetSha256'],'proposal ledger parity')
    require(proposal['sourceContextSha256']==row['sourceContextSha256'],'proposal caller context')
require(all(x['decision']=='hold' and not ({'sourceKey','currentTarget','proposedTarget'} & set(x)) for x in holds),'hold artifact hash-only')
require(summary['allCurrentTokenChecksPass'] is True and summary['allProposalTokenChecksPass'] is True,'summary token checks')
require(summary['proposalCount']==9 and summary['hashOnlyHoldCount']==0,'summary counts')
print(json.dumps({'result':'PASS','head':HEAD,'tree':TREE,'cells':len(ledger),'decisions':dict(counts),'proposals':len(proposals),'hashOnlyHolds':len(holds),'candidateFreeFilesVerified':len(input_sums)},ensure_ascii=False,indent=2))
