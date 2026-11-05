#!/usr/bin/env python3
"""Portable offline verifier for the W1623-W1642 blind review packet."""
from __future__ import annotations
import collections, hashlib, json, re, subprocess
from pathlib import Path

OUT=Path(__file__).resolve().parent
TASK=OUT.parent
INPUT=TASK/'candidate-free-input'
HEAD='7e366cbf21ad5490bd11ef418a0f2a98b3fbd567'
TREE='801d7a037c15dcd83b3e038160054a46c9b8f03b'
LOCALES=['es','zh-Hans','hi','de','ja','fr','pt-BR','ar','ko','zh-Hant','vi','id']
PH=re.compile(r'\{[^{}]+\}')
MARKUP=re.compile(r'<[^>]+>')
NUM=re.compile(r'(?<![A-Za-z0-9])\d+(?:[.,]\d+)?(?![A-Za-z0-9])')

def sha(b): return hashlib.sha256(b).hexdigest()
def sha_text(s): return sha(s.encode('utf-8'))
def canon(o): return json.dumps(o,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode('utf-8')
def readj(p): return json.loads(p.read_text(encoding='utf-8'))
def readjl(p): return [json.loads(x) for x in p.read_text(encoding='utf-8').splitlines() if x.strip()]
def require(ok,msg):
    if not ok: raise SystemExit('FAIL: '+msg)

def verify_sums(directory):
    sums_path=directory/'SHA256SUMS.txt'
    listed={}
    for line in sums_path.read_text(encoding='utf-8').splitlines():
        if not line.strip(): continue
        h,n=line.split(None,1); n=n.lstrip('* ')
        require(n not in listed,'duplicate checksum path '+n)
        listed[n]=h
    actual={p.relative_to(directory).as_posix():sha(p.read_bytes()) for p in directory.rglob('*') if p.is_file() and p.name!='SHA256SUMS.txt'}
    require(listed==actual,'checksum set/content '+str(directory))
    return listed

input_files=verify_sums(INPUT)
output_files=verify_sums(OUT)
manifest=readj(INPUT/'manifest.json')
require(manifest['head']==HEAD and manifest['tree']==TREE,'candidate-free exact pin')
require(manifest['selectedPositions']==[1623,1642] and manifest['cellCount']==240,'candidate-free dimensions')
require(manifest['candidateFreeInputOnly'] is True and manifest['proposedTranslationsIncluded'] is False,'candidate-free scope')
att=readj(OUT/'input-attestation.json')
require(att['candidateFreeVerifierResult']=='PASS' and att['primaryReviewFilesOpened'] is False,'blind exposure / input verifier record')
require(att['candidateFreeChecksumListSha256']==sha((INPUT/'SHA256SUMS.txt').read_bytes()),'candidate-free checksum-list pin')
require(att['inputFilesSha256']==input_files,'input file hashes')
require(att['initialPRRefs']['headSha']==HEAD and att['initialPRRefs']['headTree']==TREE,'initial PR pin')
require(att['finalPRRefs']['headSha']==HEAD and att['finalPRRefs']['headTree']==TREE,'final PR pin')
require(att['initialPRRefs']['branchRefSha']==HEAD and att['initialPRRefs']['pullRefSha']==HEAD,'initial branch/pull refs')
require(att['finalPRRefs']['branchRefSha']==HEAD and att['finalPRRefs']['pullRefSha']==HEAD,'final branch/pull refs')
for ref in ('initial','final'):
    pin=att[f'{ref}PRRefs']
    stem='pr-api-before-review.json' if ref=='initial' else 'pr-api-final.json'
    refsfile='remote-refs-before-review.txt' if ref=='initial' else 'remote-refs-final.txt'
    pinbase=OUT/'attestation'
    require(pin['prApiSha256']==sha((pinbase/stem).read_bytes()),ref+' PR API seal')
    require(pin['remoteRefsSha256']==sha((pinbase/refsfile).read_bytes()),ref+' remote refs seal')
    api=readj(pinbase/stem)
    require(api['state']=='open' and api['head']['sha']==HEAD and api['head']['ref']=='codex/slskr-l10n-audit-20261104-resync',ref+' PR API identity')
    require(pin['prBodySha256']==sha((api.get('body') or '').encode()),ref+' body hash')
commit=readj(OUT/'attestation'/'head-commit-final.json')
require(commit['sha']==HEAD and commit['tree']==TREE,'final API commit tree')
repo=Path(att['pinnedSourceWorktree']['path'])
require(att['pinnedSourceWorktree']['head']==HEAD and att['pinnedSourceWorktree']['tree']==TREE and att['pinnedSourceWorktree']['statusClean'] is True,'worktree attestation')
require(subprocess.check_output(['git','-C',str(repo),'rev-parse','HEAD'],text=True).strip()==HEAD,'worktree head')
require(subprocess.check_output(['git','-C',str(repo),'rev-parse','HEAD^{tree}'],text=True).strip()==TREE,'worktree tree')
require(subprocess.check_output(['git','-C',str(repo),'status','--porcelain=v1'],text=True).strip()=='','worktree clean')

cells=readjl(INPUT/'current-target-cells.jsonl')
contexts={r['position']:r for r in readjl(INPUT/'source-contexts.jsonl')}
rows=readjl(OUT/'review-cells.jsonl')
proposals=readjl(OUT/'proposals.jsonl')
holds=readjl(OUT/'holds-hash-only.jsonl')
require(len(cells)==len(rows)==240,'240 review cell count')
require([(r['position'],r['locale']) for r in cells]==[(p,l) for p in range(1623,1643) for l in LOCALES],'candidate-free row order')
require([(r['position'],r['locale']) for r in rows]==[(r['position'],r['locale']) for r in cells],'exact review cell coverage/order')
source={(r['position'],r['locale']):r for r in cells}
require(len(source)==240,'unique candidate-free identities')
counts=collections.Counter()
proposal_ids=[]
for row in rows:
    key=(row['position'],row['locale']); src=source[key]; ctx=contexts[row['position']]
    require(row['sourceKey']==src['sourceKey']==ctx['sourceKey'],'source key '+str(key))
    require(row['sourceKeySha256']==src['sourceKeySha256']==sha_text(src['sourceKey']),'source key hash '+str(key))
    require(row['sourceContextSha256']==src['sourceContextSha256']==ctx['callerContextSha256'],'caller context hash '+str(key))
    require(row['callerCount']==src['callerCount']==ctx['productionCallerCount'],'caller count '+str(key))
    require(row['callerOccurrenceCount']==ctx['callerOccurrenceCount'],'caller occurrence count '+str(key))
    require(row['catalogPath']==src['catalogPath'] and row['catalogFileSha256']==src['catalogFileSha256'] and row['catalogGitBlob']==src['catalogGitBlob'],'catalog pin '+str(key))
    require(row['currentTarget']==src['currentTarget'] and row['currentTargetSha256']==src['currentTargetSha256'],'current target binding '+str(key))
    require(sha_text(row['currentTarget'])==row['currentTargetSha256'],'current target hash '+str(key))
    require(row['decision'] in {'accept','hold','correction','refinement'},'decision '+str(key))
    require(isinstance(row.get('reason'),str) and row['reason'].strip(),'review reason '+str(key))
    rec=row.get('reviewRecordSha256'); body={k:v for k,v in row.items() if k!='reviewRecordSha256'}
    require(rec==sha(canon(body)),'review record hash '+str(key))
    counts[row['decision']]+=1
    if row['decision'] in {'correction','refinement'}:
        target=row.get('suggestedTarget')
        require(isinstance(target,str) and target.strip(),'proposal wording '+str(key))
        require(row['suggestedTargetSha256']==sha_text(target),'proposal text hash '+str(key))
        require(PH.findall(src['sourceKey'])==PH.findall(target),'proposal placeholder parity '+str(key))
        require(MARKUP.findall(src['sourceKey'])==MARKUP.findall(target),'proposal markup parity '+str(key))
        require(NUM.findall(src['sourceKey'])==NUM.findall(target),'proposal numeric parity '+str(key))
        require(all(t in target for t in src['sourceProtectedLiterals']),'proposal protected literals '+str(key))
        proposal_ids.append(key)
    else:
        require(row.get('suggestedTarget') is None and row.get('suggestedTargetSha256') is None,'unexpected proposal '+str(key))
require(counts==collections.Counter({'accept':229,'correction':11}), 'decision dimensions '+str(dict(counts)))
require(not holds and manifest['callerResolutionHoldCount']==0,'callerless holds absent only because input has none')
require(len(proposals)==len(proposal_ids)==11,'proposal ledger count')
for p in proposals:
    key=(p['position'],p['locale'])
    row=next(r for r in rows if (r['position'],r['locale'])==key)
    require(row['decision']=='correction' and p['suggestedTarget']==row['suggestedTarget'],'proposal ledger link '+str(key))
    body={k:v for k,v in p.items() if k!='proposalRecordSha256'}
    require(p['proposalRecordSha256']==sha(canon(body)),'proposal record hash '+str(key))
summary=readj(OUT/'review-summary.json')
require(summary['exactHead']==HEAD and summary['exactTree']==TREE and summary['cellCount']==240,'review summary pin/count')
require(summary['decisionCounts']==dict(sorted(counts.items())) and summary['proposalCount']==len(proposals),'review summary decisions')
require(summary['hashOnlyHoldCount']==0 and summary['callerlessPositions']==[],'review summary hold boundary')
review_manifest=readj(OUT/'review-manifest.json')
require(review_manifest['exactHead']==HEAD and review_manifest['exactTree']==TREE and review_manifest['semanticReviewIndependent'] is True,'review manifest pin/scope')
print(json.dumps({'result':'PASS','head':HEAD,'tree':TREE,'cells':len(rows),'decisionCounts':dict(sorted(counts.items())),'proposalCount':len(proposals),'callerlessHoldCount':len(holds),'inputFilesVerified':len(input_files),'outputFilesVerified':len(output_files),'primaryReviewFilesOpened':False,'nativeSpeakerSignoff':False},ensure_ascii=False,indent=2))
