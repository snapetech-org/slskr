#!/usr/bin/env python3
"""Portable offline verifier for the slskR W1623-W1642 cross-review packet."""
from __future__ import annotations
import collections, hashlib, json, re, subprocess
from pathlib import Path

OUT=Path(__file__).resolve().parent
TASK=OUT.parent
CF=TASK/'candidate-free-input'; PRIMARY=TASK/'primary-review'; BLIND=TASK/'blind-review'
HEAD='7e366cbf21ad5490bd11ef418a0f2a98b3fbd567'; TREE='801d7a037c15dcd83b3e038160054a46c9b8f03b'
LOCALES=['es','zh-Hans','hi','de','ja','fr','pt-BR','ar','ko','zh-Hant','vi','id']
PH=re.compile(r'\{[^{}]+\}'); MARKUP=re.compile(r'<[^>]+>'); NUM=re.compile(r'(?<![A-Za-z0-9])\d+(?:[.,]\d+)?(?![A-Za-z0-9])')

def sha(data): return hashlib.sha256(data).hexdigest()
def shat(text): return sha(text.encode('utf-8'))
def canon(obj): return json.dumps(obj,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode('utf-8')
def readj(p): return json.loads(p.read_text(encoding='utf-8'))
def readjl(p): return [json.loads(line) for line in p.read_text(encoding='utf-8').splitlines() if line.strip()]
def require(ok,msg):
    if not ok: raise SystemExit('FAIL: '+msg)
def verify_packet(folder):
    path=folder/'SHA256SUMS.txt'; listed={}
    for line in path.read_text(encoding='utf-8').splitlines():
        if not line.strip(): continue
        h,n=line.split(None,1); n=n.lstrip('* ')
        require(n not in listed,'duplicate checksum '+n); listed[n]=h
    actual={p.relative_to(folder).as_posix():sha(p.read_bytes()) for p in folder.rglob('*') if p.is_file() and p.name!='SHA256SUMS.txt'}
    require(listed==actual,'packet checksum coverage/content '+str(folder))
    return listed,sha(path.read_bytes())

cf_files,cf_sums_sha=verify_packet(CF)
p_files,p_sums_sha=verify_packet(PRIMARY)
b_files,b_sums_sha=verify_packet(BLIND)
out_files,out_sums_sha=verify_packet(OUT)
att=readj(OUT/'input-attestation.json')
cfm=readj(CF/'manifest.json'); pm=readj(PRIMARY/'manifest.json'); bm=readj(BLIND/'review-manifest.json')
require(cfm['head']==pm['exactHead']==bm['exactHead']==HEAD,'candidate/primary/blind head')
require(cfm['tree']==pm['exactTree']==bm['exactTree']==TREE,'candidate/primary/blind tree')
require(cfm['selectedPositions']==[1623,1642] and cfm['cellCount']==240,'candidate-free scope')
require(att['exactHead']==HEAD and att['exactTree']==TREE,'cross input attestation pin')
require(att['candidateFreeInputChecksumListSha256']==cf_sums_sha,'candidate-free input checksum pin')
require(att['primaryChecksumListSha256']==p_sums_sha and att['blindChecksumListSha256']==b_sums_sha,'review input checksum pins')
require(att['packetFileCounts']=={'candidateFree':len(cf_files),'primary':len(p_files),'blind':len(b_files)},'input packet file counts')
require(att['candidateFreeVerifierOffline']=='PASS' and att['candidateFreeVerifierFull']=='PASS' and att['primaryVerifier']=='PASS' and att['blindVerifier']=='PASS','input verifier records')
require(att['sourceCurrentCallerMismatches']==0 and att['callerlessPositions']==[],'source/caller mismatch attestation')

# Validate exact live PR evidence before and after the semantic review.
for stage in ('initialPRPin','finalPRPin'):
    pin=att[stage]; suffix='before-review' if stage=='initialPRPin' else 'final'
    require(pin['result']=='PASS' and pin['state']=='open','PR state '+stage)
    require(pin['headSha']==HEAD and pin['headTree']==TREE,'PR head/tree '+stage)
    require(pin['branchRefSha']==HEAD and pin['pullRefSha']==HEAD,'branch/pull refs '+stage)
    api_path=OUT/'attestation'/('pr-api-before-review.json' if suffix=='before-review' else 'pr-api-final.json')
    refs_path=OUT/'attestation'/('remote-refs-before-review.txt' if suffix=='before-review' else 'remote-refs-final.txt')
    require(pin['prApiSha256']==sha(api_path.read_bytes()),'PR API file hash '+stage)
    require(pin['remoteRefsSha256']==sha(refs_path.read_bytes()),'remote refs file hash '+stage)
    api=readj(api_path)
    require(api['number']==209 and api['state']=='open' and api['head']['ref']=='codex/slskr-l10n-audit-20261104-resync','PR API identity '+stage)
    require(api['head']['sha']==HEAD and api['base']['ref']=='main','PR API branch/base '+stage)
    require(pin['prBodySha256']==shat(api.get('body') or ''),'PR body hash '+stage)
    refs={}
    for line in refs_path.read_text(encoding='utf-8').splitlines():
        h,name=line.split('\t');refs[name]=h
    require(refs['refs/heads/codex/slskr-l10n-audit-20261104-resync']==HEAD and refs['refs/pull/209/head']==HEAD,'remote ref evidence '+stage)
commit=readj(OUT/'attestation'/'head-commit-final.json')
require(commit['sha']==HEAD and commit['tree']==TREE,'final commit/tree API')
repo=Path(att['pinnedSourceWorktree']['path'])
require(att['pinnedSourceWorktree']['head']==HEAD and att['pinnedSourceWorktree']['tree']==TREE and att['pinnedSourceWorktree']['statusClean'] is True,'worktree attestation')
require(subprocess.check_output(['git','-C',str(repo),'rev-parse','HEAD'],text=True).strip()==HEAD,'worktree HEAD')
require(subprocess.check_output(['git','-C',str(repo),'rev-parse','HEAD^{tree}'],text=True).strip()==TREE,'worktree tree')
require(subprocess.check_output(['git','-C',str(repo),'status','--porcelain=v1'],text=True).strip()=='','worktree clean')

cells=readjl(CF/'current-target-cells.jsonl'); contexts={x['position']:x for x in readjl(CF/'source-contexts.jsonl')}
primary=readjl(PRIMARY/'primary-ledger.jsonl'); blind=readjl(BLIND/'review-cells.jsonl'); cross=readjl(OUT/'cross-review-ledger.jsonl'); adjud=readjl(OUT/'proposal-adjudications.jsonl')
require(len(cells)==len(primary)==len(blind)==len(cross)==240,'240-cell packet counts')
require([(x['position'],x['locale']) for x in cells]==[(p,l) for p in range(1623,1643) for l in LOCALES],'candidate-free ordering')
key=lambda r:(r['position'],r['locale'])
cm={key(r):r for r in cells}; pmr={key(r):r for r in primary}; bmr={key(r):r for r in blind}; xmr={key(r):r for r in cross}
require(len(cm)==len(pmr)==len(bmr)==len(xmr)==240,'unique identities')
pp={key(r):r for r in readjl(PRIMARY/'proposals.jsonl')}; bp={key(r):r for r in readjl(BLIND/'proposals.jsonl')}
require(len(pp)==9 and len(bp)==11,'input proposal counts')
counts=collections.Counter(); recon=collections.Counter(); proposal_ids=set()
for k,c in cm.items():
    p=pmr[k]; b=bmr[k]; x=xmr[k]; ctx=contexts[c['position']]
    require(p['exactHead']==HEAD and p['exactTree']==TREE,'primary row pin '+str(k))
    require(p['candidateFreeCellRecordSha256']==sha(canon(c)),'primary candidate-free row hash '+str(k))
    for r,label in ((p,'primary'),(b,'blind'),(x,'cross')):
        require(r['sourceKey']==c['sourceKey']==ctx['sourceKey'],'source key '+label+' '+str(k))
        require(r['sourceKeySha256']==c['sourceKeySha256']==shat(c['sourceKey']),'source key hash '+label+' '+str(k))
        require(r['currentTarget']==c['currentTarget'] and r['currentTargetSha256']==c['currentTargetSha256']==shat(c['currentTarget']),'current text/hash '+label+' '+str(k))
        require(r['sourceContextSha256']==c['sourceContextSha256']==ctx['callerContextSha256'],'caller context '+label+' '+str(k))
        require(r['callerCount']==c['callerCount']==ctx['productionCallerCount'],'caller count '+label+' '+str(k))
        require(r['catalogPath']==c['catalogPath'] and r['catalogFileSha256']==c['catalogFileSha256'] and r['catalogGitBlob']==c['catalogGitBlob'],'catalog pins '+label+' '+str(k))
    require(x['sourceTextSha256']==shat(c['sourceKey']) and x['callerOccurrenceCount']==ctx['callerOccurrenceCount'],'cross source/caller '+str(k))
    if p['decision'] in {'correction','refinement'}: require(p['proposedTarget']==pp[k]['proposedTarget'],'primary proposal linkage '+str(k))
    if b['decision'] in {'correction','refinement'}: require(b['suggestedTarget']==bp[k]['suggestedTarget'],'blind proposal linkage '+str(k))
    p_has=p['decision'] in {'correction','refinement'}; b_has=b['decision'] in {'correction','refinement'}
    expected_recon=('both-proposed-same-target' if p['proposedTarget']==b['suggestedTarget'] else 'both-proposed-different-target') if p_has and b_has else ('primary-only-proposal' if p_has else ('blind-only-proposal' if b_has else 'both-accept-current'))
    require(x['proposalReconciliation']==expected_recon,'proposal reconciliation '+str(k))
    require(x['rootDisposition'] in {'accept-current','correction','refinement'},'root disposition '+str(k))
    require(isinstance(x['rootRationale'],str) and x['rootRationale'].strip(),'root rationale '+str(k))
    if x['rootDisposition'] in {'correction','refinement'}:
        target=x['rootRecommendedTarget'];require(isinstance(target,str) and target.strip(),'root target '+str(k))
        require(x['rootRecommendedTargetSha256']==shat(target),'root target hash '+str(k))
        require(PH.findall(c['sourceKey'])==PH.findall(target),'placeholder parity '+str(k))
        require(MARKUP.findall(c['sourceKey'])==MARKUP.findall(target),'markup parity '+str(k))
        require(NUM.findall(c['sourceKey'])==NUM.findall(target),'numeric parity '+str(k))
        require(all(t in target for t in c['sourceProtectedLiterals']),'protected literals '+str(k))
        proposal_ids.add(k)
    else: require(x['rootRecommendedTarget'] is None and x['rootRecommendedTargetSha256'] is None,'unexpected root target '+str(k))
    record_hash=x.get('crossReviewRecordSha256');body={n:v for n,v in x.items() if n!='crossReviewRecordSha256'}
    require(record_hash==sha(canon(body)),'cross row record hash '+str(k))
    counts[x['rootDisposition']]+=1;recon[x['proposalReconciliation']]+=1
expected_union=set(pp)|set(bp)
require(proposal_ids==expected_union and len(adjud)==13,'adjudication union coverage')
am={key(r):r for r in adjud};require(set(am)==expected_union,'adjudication identities')
for k,r in am.items():
    x=xmr[k];require(r['rootRecommendedTarget']==x['rootRecommendedTarget'] and r['rootDisposition']==x['rootDisposition'],'adjudication link '+str(k))
    body={n:v for n,v in r.items() if n!='adjudicationRecordSha256'}
    require(r['adjudicationRecordSha256']==sha(canon(body)),'adjudication hash '+str(k))
overlap=set(pp)&set(bp); same={k for k in overlap if pp[k]['proposedTarget']==bp[k]['suggestedTarget']}
require(len(overlap)==7 and len(set(pp)-set(bp))==2 and len(set(bp)-set(pp))==4 and len(same)==1,'proposal set/wording reconciliation counts')
require(counts==collections.Counter({'accept-current':227,'correction':13}),'root decision counts')
summary=readj(OUT/'cross-review-summary.json')
require(summary['rootDecisionCounts']==dict(sorted(counts.items())) and summary['proposalReconciliationCounts']==dict(sorted(recon.items())),'summary counts')
require(summary['proposalIdentityOverlap']==7 and summary['primaryOnlyProposalCount']==2 and summary['blindOnlyProposalCount']==4 and summary['sharedTargetAgreementCount']==1 and summary['sharedTargetDisagreementCount']==6,'summary proposal reconciliation')
manifest=readj(OUT/'cross-review-manifest.json')
require(manifest['exactHead']==HEAD and manifest['exactTree']==TREE and manifest['proposalAdjudicationCount']==13,'cross manifest pin/count')
require(manifest['crossReviewerPreviouslyAuthoredBlindPacket'] is True and manifest['primaryPacketAuthoredByCrossReviewer'] is False,'cross reviewer disclosure')
print(json.dumps({'result':'PASS','head':HEAD,'tree':TREE,'cells':len(cross),'rootDecisions':dict(sorted(counts.items())),'primaryProposals':len(pp),'blindProposals':len(bp),'proposalUnionAdjudicated':len(proposal_ids),'proposalIdentityOverlap':len(overlap),'primaryOnly':len(set(pp)-set(bp)),'blindOnly':len(set(bp)-set(pp)),'sharedTargetAgreement':len(same),'sharedTargetDisagreement':len(overlap)-len(same),'candidateFreeFilesVerified':len(cf_files),'primaryFilesVerified':len(p_files),'blindFilesVerified':len(b_files),'crossFilesVerified':len(out_files),'sourceCurrentCallerMismatches':0,'callerlessHolds':0},ensure_ascii=False,indent=2))
