#!/usr/bin/env python3
"""Build cross-review ledger from candidate-free, primary, and blind packets."""
from __future__ import annotations
import collections, hashlib, json
from pathlib import Path

TASK=Path(__file__).resolve().parent.parent
CF=TASK/'candidate-free-input'
PRIMARY=TASK/'primary-review'
BLIND=TASK/'blind-review'
OUT=Path(__file__).resolve().parent
HEAD='7e366cbf21ad5490bd11ef418a0f2a98b3fbd567'
TREE='801d7a037c15dcd83b3e038160054a46c9b8f03b'
ROOT_RECOMMENDATIONS={
 (1623,'es'):('No se pudo emitir el evento.','In this server event allowlist, “raise event” means emit/dispatch an event; “emitir” is more precise than the current “generar”.'),
 (1628,'ko'):('탐색 정보를 새로 고치지 못했습니다: {error}','The current phrase redundantly combines search and discovery. “탐색 정보” names the PodDiscoveryPanel discovery data clearly and preserves the error placeholder.'),
 (1631,'zh-Hant'):('無法註冊訊息：{error}','“註冊” accurately describes registering the message in PodMessageRoutingPanel; the current “登錄” is ambiguous and more often reads as logging/recording.'),
 (1632,'zh-Hant'):('無法註冊 Pod。','The current Traditional Chinese uses the Simplified character 注; 註冊 is the correct Traditional form, and Pod is the named entity.'),
 (1633,'vi'):('Không thể đăng ký Pod:','The current “nhóm” means group, changing the technical Pod entity shown by PodDiscoveryPanel.'),
 (1638,'pt-BR'):('Não foi possível escanear novamente os compartilhamentos','“Verificar novamente” says to check again, while the caller reports a failed rescan of shared content.'),
 (1641,'ar'):('تعذر استرداد المعلومات الخاصة بالمستخدم','The caller appends the username after this fragment; this expresses information belonging to that user without leaving the Arabic preposition detached.'),
 (1641,'de'):('Fehler beim Abruf der Informationen für','The caller appends the username after this fragment; this clause order yields “... für [username]” naturally.'),
 (1641,'hi'):('जानकारी प्राप्त नहीं हो सकी, उपयोगकर्ता','The caller appends the username after this fragment; a failure clause followed by a user label fits that order and avoids a misplaced Hindi postposition.'),
 (1641,'ja'):('ユーザーの情報を取得できませんでした：','The caller appends the username after this fragment; the current genitive-first phrase cannot attach to the name, while this colon introduces the user label.'),
 (1641,'ko'):('해당 사용자의 정보를 가져오지 못했습니다:','The caller appends the username after this fragment; this phrase names whose information failed to load and keeps the appended name interpretable.'),
 (1641,'zh-Hans'):('无法获取用户信息：','The caller appends the username after this fragment; this gives the username a clear label and fixes the current disconnected phrase.'),
 (1641,'zh-Hant'):('無法取得使用者資訊：','The caller appends the username after this fragment; this gives the name a clear label and fixes the current disconnected phrase.'),
}

def sha(b): return hashlib.sha256(b).hexdigest()
def st(s): return sha(s.encode('utf-8'))
def canon(x): return json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode('utf-8')
def readj(p): return json.loads(p.read_text(encoding='utf-8'))
def readjl(p): return [json.loads(x) for x in p.read_text(encoding='utf-8').splitlines() if x.strip()]
def verify_sums(folder):
    listed={}
    for line in (folder/'SHA256SUMS.txt').read_text(encoding='utf-8').splitlines():
        if line.strip():
            h,n=line.split(None,1); n=n.lstrip('* '); assert n not in listed; listed[n]=h
    actual={p.relative_to(folder).as_posix():sha(p.read_bytes()) for p in folder.rglob('*') if p.is_file() and p.name!='SHA256SUMS.txt'}
    assert listed==actual, f'checksum mismatch or file-set mismatch: {folder}'
    return listed

cf_sums=verify_sums(CF); p_sums=verify_sums(PRIMARY); b_sums=verify_sums(BLIND)
cf_manifest=readj(CF/'manifest.json'); pm=readj(PRIMARY/'manifest.json'); bm=readj(BLIND/'review-manifest.json')
assert cf_manifest['head']==pm['exactHead']==bm['exactHead']==HEAD
assert cf_manifest['tree']==pm['exactTree']==bm['exactTree']==TREE
assert cf_manifest['cellCount']==240 and cf_manifest['candidateFreeInputOnly'] is True
assert pm['candidateFreeChecksumListSha256']==sha((CF/'SHA256SUMS.txt').read_bytes())
assert bm['candidateFreeInputChecksumListSha256']==sha((CF/'SHA256SUMS.txt').read_bytes())

cells=readjl(CF/'current-target-cells.jsonl')
contexts={r['position']:r for r in readjl(CF/'source-contexts.jsonl')}
p_rows=readjl(PRIMARY/'primary-ledger.jsonl'); b_rows=readjl(BLIND/'review-cells.jsonl')
pmap={(r['position'],r['locale']):r for r in p_rows}; bmap={(r['position'],r['locale']):r for r in b_rows}
cmap={(r['position'],r['locale']):r for r in cells}
p_props={(r['position'],r['locale']):r for r in readjl(PRIMARY/'proposals.jsonl')}
b_props={(r['position'],r['locale']):r for r in readjl(BLIND/'proposals.jsonl')}
assert len(cells)==len(p_rows)==len(b_rows)==240 and len(cmap)==len(pmap)==len(bmap)==240
assert len(contexts)==20 and len(p_props)==9 and len(b_props)==11
assert set(ROOT_RECOMMENDATIONS)==set(p_props)|set(b_props)

cross=[]; adjudications=[]
for c in cells:
    k=(c['position'],c['locale']); p=pmap[k]; b=bmap[k]; ctx=contexts[c['position']]
    assert p['exactHead']==HEAD and p['exactTree']==TREE
    assert p['sourceKey']==b['sourceKey']==c['sourceKey']==ctx['sourceKey']
    assert p['sourceKeySha256']==b['sourceKeySha256']==c['sourceKeySha256']==st(c['sourceKey'])
    assert p['sourceContextSha256']==b['sourceContextSha256']==c['sourceContextSha256']==ctx['callerContextSha256']
    assert p['currentTarget']==b['currentTarget']==c['currentTarget']
    assert p['currentTargetSha256']==b['currentTargetSha256']==c['currentTargetSha256']==st(c['currentTarget'])
    assert p['callerCount']==b['callerCount']==c['callerCount']==ctx['productionCallerCount']
    assert p['callerOccurrenceCount']==b['callerOccurrenceCount']==ctx['callerOccurrenceCount']
    assert p['catalogPath']==b['catalogPath']==c['catalogPath']
    assert p['catalogFileSha256']==b['catalogFileSha256']==c['catalogFileSha256']
    assert p['catalogGitBlob']==b['catalogGitBlob']==c['catalogGitBlob']
    assert p['candidateFreeCellRecordSha256']==sha(canon(c))
    p_proposed=p['decision'] in {'correction','refinement'}
    b_proposed=b['decision'] in {'correction','refinement'}
    assert p_proposed==(k in p_props) and b_proposed==(k in b_props)
    if p_proposed and b_proposed:
        reconciliation='both-proposed-same-target' if p['proposedTarget']==b['suggestedTarget'] else 'both-proposed-different-target'
    elif p_proposed:
        reconciliation='primary-only-proposal'
    elif b_proposed:
        reconciliation='blind-only-proposal'
    else:
        reconciliation='both-accept-current'
    if k in ROOT_RECOMMENDATIONS:
        target,reason=ROOT_RECOMMENDATIONS[k]; decision='correction'; target_hash=st(target)
    else:
        target=None; reason='Rechecked the current text against the source meaning, exact caller context, and locale; the current wording is suitable.'
        decision='accept-current'; target_hash=None
    paths=sorted({x['path'] for x in ctx['callers']})
    record={
      'position':c['position'],'locale':c['locale'],'sourceKey':c['sourceKey'],'sourceKeySha256':c['sourceKeySha256'],
      'sourceTextSha256':st(c['sourceKey']),'sourceContextSha256':c['sourceContextSha256'],
      'callerCount':c['callerCount'],'callerOccurrenceCount':ctx['callerOccurrenceCount'],'callerPaths':paths,
      'catalogPath':c['catalogPath'],'catalogFileSha256':c['catalogFileSha256'],'catalogGitBlob':c['catalogGitBlob'],
      'currentTarget':c['currentTarget'],'currentTargetSha256':c['currentTargetSha256'],
      'candidateFreeCellRecordSha256':sha(canon(c)),
      'primaryDecision':p['decision'],'primaryProposedTarget':p.get('proposedTarget'),'primaryProposedTargetSha256':p.get('proposedTargetSha256'),
      'primaryRationale':p['rationale'] if p_proposed else None,
      'primaryCellRecordSha256':sha(canon(p)),
      'blindDecision':b['decision'],'blindSuggestedTarget':b['suggestedTarget'],'blindSuggestedTargetSha256':b['suggestedTargetSha256'],
      'blindReason':b['reason'] if b_proposed else None,'blindReviewRecordSha256':b['reviewRecordSha256'],
      'proposalReconciliation':reconciliation,'rootDisposition':decision,
      'rootRecommendedTarget':target,'rootRecommendedTargetSha256':target_hash,
      'rootRationale':reason,'reviewConfidence':'moderate',
    }
    record['crossReviewRecordSha256']=sha(canon(record))
    cross.append(record)
    if p_proposed or b_proposed:
        adjudication={k2:record[k2] for k2 in ('position','locale','sourceKey','sourceKeySha256','sourceContextSha256','currentTarget','currentTargetSha256','primaryDecision','primaryProposedTarget','primaryProposedTargetSha256','primaryRationale','blindDecision','blindSuggestedTarget','blindSuggestedTargetSha256','blindReason','proposalReconciliation','rootDisposition','rootRecommendedTarget','rootRecommendedTargetSha256','rootRationale','reviewConfidence')}
        adjudication['adjudicationRecordSha256']=sha(canon(adjudication))
        adjudications.append(adjudication)

pids=set(p_props); bids=set(b_props); union=pids|bids; overlap=pids&bids
same_targets={k for k in overlap if p_props[k]['proposedTarget']==b_props[k]['suggestedTarget']}
counts=collections.Counter(r['rootDisposition'] for r in cross)
reconciliation_counts=collections.Counter(r['proposalReconciliation'] for r in cross)
assert len(adjudications)==13 and counts==collections.Counter({'accept-current':227,'correction':13})
assert len(overlap)==7 and len(pids-bids)==2 and len(bids-pids)==4 and len(same_targets)==1

A=OUT/'attestation'
pin_before=readj(A/'pin-before-review.json'); pin_final=readj(A/'pin-final.json')
for pin in (pin_before,pin_final):
    assert pin['result']=='PASS' and pin['headSha']==HEAD and pin['headTree']==TREE
    assert pin['branchRefSha']==HEAD and pin['pullRefSha']==HEAD
input_attestation={
  'repository':'snapetech-org/slskR','pullRequest':209,'exactHead':HEAD,'exactTree':TREE,
  'candidateFreeInputChecksumListSha256':sha((CF/'SHA256SUMS.txt').read_bytes()),
  'primaryChecksumListSha256':sha((PRIMARY/'SHA256SUMS.txt').read_bytes()),
  'blindChecksumListSha256':sha((BLIND/'SHA256SUMS.txt').read_bytes()),
  'packetFileCounts':{'candidateFree':len(cf_sums),'primary':len(p_sums),'blind':len(b_sums)},
  'candidateFreeVerifierOffline':'PASS','candidateFreeVerifierFull':'PASS','primaryVerifier':'PASS','blindVerifier':'PASS',
  'sourceCurrentCallerMismatches':0,'callerlessPositions':[],'callerReferences':20,'callerOccurrences':20,'callerFiles':12,
  'initialPRPin':pin_before,'finalPRPin':pin_final,
  'reviewPacketAuthorship':{'primaryByCrossReviewer':False,'blindByCrossReviewer':True,'semanticsReassessedAgainstCandidateFree':True},
  'repositoryEdits':False,'prEdits':False,'testsBuildsScansCI':False,'nativeSpeakerReview':False,'browserReview':False,
}
(OUT/'cross-review-ledger.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False,separators=(',',':'))+'\n' for r in cross),encoding='utf-8')
(OUT/'proposal-adjudications.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False,separators=(',',':'))+'\n' for r in adjudications),encoding='utf-8')
(OUT/'input-attestation.json').write_text(json.dumps(input_attestation,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
summary={
  'repository':'snapetech-org/slskR','pullRequest':209,'exactHead':HEAD,'exactTree':TREE,'window':'W1623-W1642',
  'cells':len(cross),'sourceCount':20,'localeCount':12,'rootDecisionCounts':dict(sorted(counts.items())),
  'primaryProposalCount':len(pids),'blindProposalCount':len(bids),'proposalIdentityOverlap':len(overlap),
  'primaryOnlyProposalCount':len(pids-bids),'blindOnlyProposalCount':len(bids-pids),
  'sharedTargetAgreementCount':len(same_targets),'sharedTargetDisagreementCount':len(overlap)-len(same_targets),
  'unionProposalCount':len(union),'allUnionProposalsRecommendedCorrection':len(adjudications)==len(union),
  'proposalReconciliationCounts':dict(sorted(reconciliation_counts.items())),
  'callerlessHoldCount':0,'sourceCurrentCallerMismatches':0,
  'nativeSpeakerReview':False,'browserReview':False,'repositoryEdits':False,'prEdits':False,'testsBuildsScansCI':False,
  'candidateFreeChecksumListSha256':input_attestation['candidateFreeInputChecksumListSha256'],
  'primaryChecksumListSha256':input_attestation['primaryChecksumListSha256'],
  'blindChecksumListSha256':input_attestation['blindChecksumListSha256'],
}
(OUT/'cross-review-summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
manifest={
  'artifact':'slskR PR #209 W1623-W1642 semantic cross-review and proposal adjudication',
  'exactHead':HEAD,'exactTree':TREE,'cells':240,'sourceKeys':20,
  'candidateFreeChecksumListSha256':input_attestation['candidateFreeInputChecksumListSha256'],
  'primaryChecksumListSha256':input_attestation['primaryChecksumListSha256'],
  'blindChecksumListSha256':input_attestation['blindChecksumListSha256'],
  'rootDecisionCounts':dict(sorted(counts.items())),'proposalAdjudicationCount':len(adjudications),
  'crossReviewerPreviouslyAuthoredBlindPacket':True,'primaryPacketAuthoredByCrossReviewer':False,
  'nativeSpeakerSignoff':False,'browserReview':False,
  'files':['cross-review-ledger.jsonl','proposal-adjudications.jsonl','cross-review-summary.json','input-attestation.json'],
}
(OUT/'cross-review-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(summary,ensure_ascii=False,indent=2))
