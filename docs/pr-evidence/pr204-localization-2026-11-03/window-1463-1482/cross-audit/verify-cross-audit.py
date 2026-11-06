#!/usr/bin/env python3
import hashlib,json,re
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parent
BASE=ROOT.parent
IN=BASE/'candidate-free-input'
PRIMARY=BASE/'primary-packet'/'output'
BLIND=BASE/'blind-review-independent-clean'
def sha(b): return hashlib.sha256(b).hexdigest()
RESTRICTED={'prior-hold-reattestation.jsonl','prior-selection-reattestation.jsonl','source-order-lineage.json'}
def verify_sums(directory):
    sums={}
    for line in (directory/'SHA256SUMS.txt').read_text(encoding='utf-8').splitlines():
        expected,name=line.split(None,1); name=name.lstrip('* '); sums[name]=expected
    if directory.resolve()==IN.resolve():
        im=json.loads((IN/'manifest.json').read_text(encoding='utf-8'))
        for name,digest in sums.items():
            if name in RESTRICTED:
                assert not (IN/name).exists() and digest==im['fileHashes'][name]['sha256']
            else: assert sha((IN/name).read_bytes())==digest,(str(directory),name)
    else:
        for name,digest in sums.items(): assert sha((directory/name).read_bytes())==digest,(str(directory),name)
def jl(path): return [json.loads(s) for s in path.read_text(encoding='utf-8').splitlines() if s]
def tokens(s):
    ph=re.findall(r'\{[A-Za-z][A-Za-z0-9_]*\}',s)
    tags=re.findall(r'<\/?[A-Za-z][^>]*>',s)
    nums=re.findall(r'(?<![A-Za-z])\d+(?:[.,]\d+)?%?(?![A-Za-z])',s)
    prot=[]
    for m in re.finditer(r'(?<![A-Za-z0-9])(?:[A-Z]{2,}[A-Z0-9]*|ffmpeg|Chromaprint|Soulseek|Spotify|YouTube|Pushbullet|Matrix|WebSocket|OpenAI)(?![A-Za-z0-9])',s):
        if m.group(0) not in prot: prot.append(m.group(0))
    return {'placeholders':ph,'markupTags':tags,'numericTokens':nums,'protectedLiterals':prot}
# This hashes all candidate-free files, including restricted prior files, but never decodes/parses them.
verify_sums(IN); verify_sums(PRIMARY); verify_sums(BLIND); verify_sums(ROOT)
manifest=json.loads((IN/'manifest.json').read_text(encoding='utf-8'))
pm=json.loads((PRIMARY/'manifest.json').read_text(encoding='utf-8'))
cm=json.loads((ROOT/'manifest.json').read_text(encoding='utf-8'))
assert pm['candidateFreeInputManifestSha256']==sha((IN/'manifest.json').read_bytes())
assert cm['inputPins']['candidateFreeManifestSha256']==sha((IN/'manifest.json').read_bytes())
assert cm['inputPins']['primaryLedgerSha256']==sha((PRIMARY/'primary-ledger.jsonl').read_bytes())
assert cm['inputPins']['cleanBlindLedgerSha256']==sha((BLIND/'review-ledger.jsonl').read_bytes())
inputs=jl(IN/'current-target-cells.jsonl'); ctx={x['position']:x for x in jl(IN/'source-contexts.jsonl')}
p=jl(PRIMARY/'primary-ledger.jsonl'); b=jl(BLIND/'review-ledger.jsonl'); x=jl(ROOT/'cross-ledger.jsonl')
assert len(inputs)==len(p)==len(b)==len(x)==240
assert [(r['position'],r['locale']) for r in inputs]==[(r['position'],r['locale']) for r in p]==[(r['position'],r['locale']) for r in b]==[(r['position'],r['locale']) for r in x]
pmap={(r['position'],r['locale']):r for r in p}; bmap={(r['position'],r['locale']):r for r in b}; counts=Counter(); current_bad=Counter(); final_proposal_bad=0
for c,row in zip(inputs,x):
    key=(c['position'],c['locale']); pos,loc=key; pr=pmap[key]; br=bmap[key]; cc=ctx[pos]
    assert row['sourceKeySha256']==c['sourceKeySha256']==pr['sourceIdSha256']==br['sourceKeySha256']
    assert row['currentTargetSha256']==c['currentTargetSha256']==pr['currentTargetSha256']==br['currentTargetSha256']
    assert row['callerContextSha256']==cc['callerContextSha256']==pr['callerContextSha256']==br['callerContextSha256']
    assert row['callerCount']==cc['productionCallerCount']==pr['callerCount']==br['callerCount']
    if pos==1466:
        assert row['crossDisposition']=='hold' and pr['disposition']=='hold' and br['decision']=='hold'
        assert row['callerCount']==0 and row['currentTargetSha256']==c['currentTargetSha256']
        assert not any(k in row for k in ('sourceKey','currentTarget','crossTarget','primaryProposal','independentBlindProposal','proposalResolution'))
        assert row['protectedLiteralMismatch'] is True and len(row['missingProtectedLiteralHashes'])==1
        assert not pr['proposedTarget'] and not br['suggestedTarget']
        counts['hold']+=1
        current_bad['FAIL']+=1
        continue
    assert row['sourceKey']==c['sourceKey'] and row['currentTarget']==c['currentTarget']
    assert row['primaryDisposition']==pr['disposition'] and row['primaryProposal']==pr['proposedTarget']
    assert row['independentBlindDecision']==br['decision'] and row['independentBlindProposal']==br['suggestedTarget']
    st=tokens(c['sourceKey']); ct=tokens(c['currentTarget']); chosen=tokens(row['crossTarget'])
    missing=[t for t in st['protectedLiterals'] if t not in ct['protectedLiterals']]
    for t in missing: current_bad[t]+=1
    assert row['currentTokenChecks']['sourceTokens']==st and row['currentTokenChecks']['currentTargetTokens']==ct
    assert row['crossTargetTokenChecks']['targetTokens']==chosen
    assert row['crossTargetTokenChecks']['placeholdersMatch']==(st['placeholders']==chosen['placeholders'])
    assert row['crossTargetTokenChecks']['markupMatches']==(st['markupTags']==chosen['markupTags'])
    assert row['crossTargetTokenChecks']['numericTokensMatch']==(st['numericTokens']==chosen['numericTokens'])
    assert row['crossTargetTokenChecks']['protectedLiteralsMatch']==all(t in chosen['protectedLiterals'] for t in st['protectedLiterals'])
    final_proposal_bad+=not row['crossTargetTokenChecks']['protectedLiteralsMatch']
    candidates=[]
    if pr['proposedTarget'] is not None: candidates.append(('primary',pr['proposedTarget'],sha(pr['proposedTarget'].encode())))
    if br['suggestedTarget'] is not None: candidates.append(('independent-blind',br['suggestedTarget'],sha(br['suggestedTarget'].encode())))
    audit={(z['source'],z['target'],z['targetSha256']) for z in row['proposalResolution']}
    assert audit==set(candidates)
    selected=[z for z in row['proposalResolution'] if z['resolution']=='selected']
    if candidates: assert selected and all(z['target']==row['crossTarget'] for z in selected)
    else: assert row['crossDisposition']=='accept-current' and row['crossTarget']==c['currentTarget']
    if missing:
        assert missing==['FTP'] and row['crossDisposition'] in ('correction','refinement') and 'FTP' in row['crossTarget']
    else: assert row['crossDisposition']!='hold'
    assert sha(row['crossTarget'].encode())==row['crossTargetSha256']
    counts[row['crossDisposition']]+=1
assert dict(counts)=={'accept-current':169,'correction':29,'hold':12,'refinement':30}
assert current_bad==Counter({'FAIL':12,'FTP':16}) and final_proposal_bad==0
before=json.loads((ROOT/'PR-attestation-before.json').read_text(encoding='utf-8'))
after=json.loads((ROOT/'PR-attestation-after.json').read_text(encoding='utf-8'))
for att in (before,after):
    assert att['state']=='OPEN' and att['draft'] is True
    assert att['head']=='2db7fa06845d9d94a5e5da2ddb5ecfdc04100ade' and att['tree']=='0945d38050243ed0d52aa9d923636820c66e65ba'
    assert att['branchRef']==att['pullRef']==att['head']
    assert att['deploymentsForHeadCount']==0 and att['deploymentActionsIssuedByReview']==0
assert before['head']==after['head'] and before['tree']==after['tree'] and before['branchRef']==after['branchRef'] and before['pullRef']==after['pullRef'] and before['mainRef']==after['mainRef']
summary=json.loads((ROOT/'cross-summary.json').read_text(encoding='utf-8'))
assert summary['finalDispositionCounts']==dict(sorted(counts.items()))
assert summary['currentTokenMismatchCounts']=={'placeholder':0,'markup':0,'numeric':0,'protectedLiteral':28}
assert summary['protectedLiteralDisposition']['FTP']['count']==16 and summary['protectedLiteralDisposition']['FAIL']['count']==12
print(json.dumps({'result':'PASS','cells':240,'finalDispositionCounts':dict(sorted(counts.items())),'proposalComparison':summary['inputComparison'],
 'currentProtectedMismatches':dict(current_bad),'finalProposalProtectedMismatches':final_proposal_bad,'hashOnlyCallerlessHolds':12,
 'deploymentsBefore':before['deploymentsForHeadCount'],'deploymentsAfter':after['deploymentsForHeadCount'],'restrictedPriorContents':'hashed only; never decoded or parsed'},indent=2))
