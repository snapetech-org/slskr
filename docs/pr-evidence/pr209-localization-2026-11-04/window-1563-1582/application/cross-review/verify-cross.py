#!/usr/bin/env python3
import hashlib, json, re
from collections import Counter
from pathlib import Path

OUT=Path(__file__).resolve().parent
ROOT=Path('/home/keith/Documents/code')
INPUT=ROOT/'task-scratch/slskr-pr209-w1563-1582-primary-20261104/candidate-free-input'
PRIMARY=ROOT/'task-scratch/slskr-pr209-w1563-1582-primary-20261104/primary-review'
BLIND=ROOT/'task-scratch/slskr-pr209-w1563-1582-independent-blind-20261104'
HEAD='f42c7e4be1f2bc9d63e13607d3c311d37f83f355'
TREE='f6cb31394c01c90a784d543b8f43b04b232c8b37'
LOCS=['es','zh-Hans','hi','de','ja','fr','pt-BR','ar','ko','zh-Hant','vi','id']
def sha(x):
    if isinstance(x,str): x=x.encode('utf-8')
    return hashlib.sha256(x).hexdigest()
def canon(x): return json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':'))
def j(p): return json.loads(p.read_text(encoding='utf-8'))
def jl(p): return [(json.loads(s),sha(s)) for s in p.read_text(encoding='utf-8').splitlines() if s.strip()]
def sums(d):
    out={}
    for line in (d/'SHA256SUMS.txt').read_text(encoding='utf-8').splitlines():
        if not line.strip(): continue
        h,n=line.split(None,1); n=n.lstrip('* '); assert n not in out
        out[n]=h
    actual={p.name for p in d.iterdir() if p.is_file() and p.name!='SHA256SUMS.txt'}
    assert actual==set(out),(d,actual^set(out))
    for n,h in out.items(): assert sha((d/n).read_bytes())==h,(d,n)
    return out
def toks(s):
    p=re.findall(r'\{[A-Za-z][A-Za-z0-9_]*\}',s)
    m=re.findall(r'</?[A-Za-z][^>]*>',s)
    n=re.findall(r'(?<![A-Za-z])\d+(?:[.,]\d+)?%?(?![A-Za-z])',s)
    z=[]
    for x in re.findall(r'(?<![A-Za-z0-9])(?:[A-Z]{2,}[A-Z0-9]*|ffmpeg|Chromaprint|Soulseek|Spotify|YouTube|Pushbullet|Matrix|WebSocket|OpenAI)(?![A-Za-z0-9])',s):
        if x not in z:z.append(x)
    return {'placeholders':p,'markupTags':m,'numericTokens':n,'protectedLiterals':z}

ins=sums(INPUT); prs=sums(PRIMARY); bls=sums(BLIND)
im=j(INPUT/'manifest.json'); pm=j(PRIMARY/'SUMMARY.json'); bm=j(BLIND/'review-manifest.json'); ba=j(BLIND/'input-attestation.json')
assert im['head']==pm['head']==bm['head']==HEAD and im['tree']==pm['tree']==bm['tree']==TREE
assert sha((INPUT/'SHA256SUMS.txt').read_bytes())==pm['candidateFreeInputChecksumListSha256']==ba['inputChecksumsFileSha256']
assert ba['inputFilesSha256']==ins and ba['candidateFreeVerifierResult']=='PASS'
att=j(OUT/'input-attestation.json')
assert att['candidateFreeChecksums']==ins and att['primaryChecksums']==prs and att['blindChecksums']==bls
assert att['candidateFreeInput']['verifierResult']=='PASS' and att['primaryReview']['verifierResult']=='PASS' and att['independentBlindReview']['verifierResult']=='PASS'
assert att['candidateFreeInput']['manifestSha256']==sha((INPUT/'manifest.json').read_bytes())
assert att['primaryReview']['summarySha256']==sha((PRIMARY/'SUMMARY.json').read_bytes())
assert att['independentBlindReview']['manifestSha256']==sha((BLIND/'review-manifest.json').read_bytes())
source={r['position']:(r,h) for r,h in jl(INPUT/'source-queue.jsonl') if 1563<=r['position']<=1582}
cells={(r['position'],r['locale']):(r,h) for r,h in jl(INPUT/'current-target-cells.jsonl')}
contexts={r['position']:r for r,h in jl(INPUT/'source-contexts.jsonl')}
primary={(r['position'],r['locale']):(r,h) for r,h in jl(PRIMARY/'primary-ledger.jsonl')}
blind={(r['position'],r['locale']):(r,h) for r,h in jl(BLIND/'review-cells.jsonl')}
rows=jl(OUT/'cross-ledger.jsonl')
assert len(rows)==240 and set(cells)==set(primary)==set(blind)=={(r['position'],r['locale']) for r,h in rows}
assert [(r['position'],r['locale']) for r,h in rows]==[(p,l) for p in range(1563,1583) for l in LOCS]
for p,ctx in contexts.items():
    assert sha(canon({'sourceKey':ctx['sourceKey'],'callers':ctx['callers']}))==ctx['callerContextSha256']
    for caller in ctx['callers']:
        assert caller['lineSha256']==sha(caller['lineText'])
        assert caller['contextSha256']==sha(canon(caller['context']))
counts=Counter()
primary_proposed=set(); blind_proposed=set()
for row,rowlinehash in rows:
    key=(row['position'],row['locale']); src,shash=source[key[0]]; c,chash=cells[key]; ctx=contexts[key[0]]; pr,phash=primary[key]; br,bhash=blind[key]
    assert row['sourceKey']==src['sourceKey']==c['sourceKey']
    assert row['sourceKeySha256']==src['sourceKeySha256']==c['sourceKeySha256']==sha(src['sourceKey'])
    assert row['sourceQueueRowSha256']==shash and row['currentTargetCellRowSha256']==chash
    assert row['currentTarget']==c['currentTarget'] and row['currentTargetSha256']==c['currentTargetSha256']==sha(c['currentTarget'])
    assert row['callerContextSha256']==c['sourceContextSha256']==ctx['callerContextSha256']
    assert row['primaryReviewRowSha256']==phash and row['blindReviewRowSha256']==bhash
    assert pr['sourceKeySha256']==br['sourceKeySha256']==row['sourceKeySha256']
    assert pr['sourceContextSha256']==br['sourceContextSha256']==row['callerContextSha256']
    assert pr['currentTarget']==br['currentTarget']==row['currentTarget']
    assert pr['currentTargetSha256']==br['currentTargetSha256']==row['currentTargetSha256']
    expected_refs=[]
    if pr['disposition'] in ('propose-correction','propose-refinement'):
        primary_proposed.add(key)
        expected_refs.append({'review':'primary','decision':pr['disposition'],'reason':pr['reason'],'suggestedTarget':pr['selectedTarget'],'suggestedTargetSha256':pr['selectedTargetSha256'],'inputRowSha256':phash})
    if br['decision'] in ('correction','refinement'):
        blind_proposed.add(key)
        expected_refs.append({'review':'independent-blind','decision':br['decision'],'reason':br['reason'],'suggestedTarget':br['suggestedTarget'],'suggestedTargetSha256':sha(br['suggestedTarget']),'reviewRecordSha256':br['reviewRecordSha256'],'inputRowSha256':bhash})
    assert row['upstreamProposalRefs']==expected_refs
    saved=row.pop('crossRecordSha256'); assert saved==sha(canon(row)); row['crossRecordSha256']=saved
    st=toks(row['sourceKey']); tt=toks(row['selectedTarget']); ti=row['tokenIntegrity']
    assert ti['sourceSignature']==st and ti['selectedSignature']==tt
    assert ti['placeholdersMatch']==(st['placeholders']==tt['placeholders']) and ti['placeholdersMatch']
    assert ti['markupMatches']==(st['markupTags']==tt['markupTags']) and ti['markupMatches']
    assert ti['numericTokensMatch']==(st['numericTokens']==tt['numericTokens']) and ti['numericTokensMatch']
    assert ti['protectedLiteralsPreserved']==all(x in tt['protectedLiterals'] for x in st['protectedLiterals']) and ti['protectedLiteralsPreserved']
    if row['decision']=='accept-current':
        assert row['selectedTarget']==row['currentTarget'] and row['selectedTargetSha256']==row['currentTargetSha256']
        assert not expected_refs
    else:
        assert row['decision'] in ('propose-correction','propose-refinement') and row['selectedTargetSha256']==sha(row['selectedTarget'])
        assert any(ref['suggestedTarget']==row['selectedTarget'] for ref in expected_refs)
    if row['decision'] in ('propose-correction','propose-refinement'):
        assert row['upstreamProposalRefs']
        assert row['callerCount']==ctx['productionCallerCount'] and row['callerOccurrenceCount']==ctx['callerOccurrenceCount']
        expected_evidence=[{'path':x['path'],'line':x['line'],'lineText':x['lineText'],'lineSha256':x['lineSha256'],'context':x['context'],'contextSha256':x['contextSha256']} for x in ctx['callers']]
        assert row['callerEvidence']==expected_evidence
        assert all(x['lineSha256']==sha(x['lineText']) and x['contextSha256']==sha(canon(x['context'])) for x in row['callerEvidence'])
    counts[row['decision']]+=1
overlap=primary_proposed & blind_proposed
assert len(primary_proposed)==12 and len(blind_proposed)==18 and len(overlap)==12
assert len(primary_proposed-blind_proposed)==0 and len(blind_proposed-primary_proposed)==6
same_text_overlap=sum(primary[k][0]['selectedTarget']==blind[k][0]['suggestedTarget'] for k in overlap)
summary=j(OUT/'SUMMARY.json')
assert summary['counts']=={k:counts.get(k,0) for k in ('accept-current','propose-correction','propose-refinement','text-free-hold')}
assert counts==Counter({'accept-current':222,'propose-correction':16,'propose-refinement':2})
assert summary['cellCount']==240 and summary['head']==HEAD and summary['tree']==TREE
assert summary['proposalReconciliation']=={'primaryProposalRecordsReviewed':12,'blindProposalRecordsReviewed':18,'uniqueProposedCellsReviewed':18,'overlappingProposalCells':12,'primaryOnlyCells':0,'blindOnlyCells':6,'sameSuggestedTextOnOverlap':1,'differentSuggestedTextOnOverlap':11}
assert summary['inputChecksumListSha256']=={'candidateFree':sha((INPUT/'SHA256SUMS.txt').read_bytes()),'primary':sha((PRIMARY/'SHA256SUMS.txt').read_bytes()),'blind':sha((BLIND/'SHA256SUMS.txt').read_bytes())}
outchecks=sums(OUT)
print(json.dumps({'result':'PASS','head':HEAD,'tree':TREE,'cells':len(rows),'counts':{k:counts.get(k,0) for k in ('accept-current','propose-correction','propose-refinement','text-free-hold')},'candidateFreeChecksummedFiles':len(ins),'primaryChecksummedFiles':len(prs),'blindChecksummedFiles':len(bls),'crossChecksummedFiles':len(outchecks),'proposalOverlapCells':summary['proposalReconciliation']['overlappingProposalCells'],'sameSuggestedTextOnOverlap':summary['proposalReconciliation']['sameSuggestedTextOnOverlap'],'tokenMismatches':0},ensure_ascii=False,sort_keys=True))
