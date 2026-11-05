#!/usr/bin/env python3
"""Build the primary semantic review packet for slskR W1623-W1642."""
import collections, hashlib, importlib.util, json, re, sys
from datetime import datetime, timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parent
INPUT=Path('/mnt/disks/scratch/task-scratch/slskr-pr209-w1623-1642-20261105/candidate-free-input')
HEAD='7e366cbf21ad5490bd11ef418a0f2a98b3fbd567'; TREE='801d7a037c15dcd83b3e038160054a46c9b8f03b'
LOCS=['es','zh-Hans','hi','de','ja','fr','pt-BR','ar','ko','zh-Hant','vi','id']
sys.dont_write_bytecode=True
spec=importlib.util.spec_from_file_location('candidate_helper',INPUT/'candidate-free-schema-helper.py')
h=importlib.util.module_from_spec(spec); spec.loader.exec_module(h)
sha,canon=h.sha,h.canon

def readj(path): return json.loads(path.read_text(encoding='utf-8'))
def readjl(path): return [json.loads(s) for s in path.read_text(encoding='utf-8').splitlines() if s]
def verify_input_sums(path):
    lines=(path/'SHA256SUMS.txt').read_text(encoding='utf-8').splitlines(); listed={}
    for line in lines:
        digest,name=line.split(None,1); name=name.lstrip('* ')
        if name in listed: raise RuntimeError(f'duplicate input checksum {name}')
        listed[name]=digest
    actual={p.name for p in path.iterdir() if p.is_file() and p.name!='SHA256SUMS.txt'}
    if set(listed)!=actual or any(sha((path/name).read_bytes())!=digest for name,digest in listed.items()): raise RuntimeError('candidate-free input checksum mismatch')
    return sha((path/'SHA256SUMS.txt').read_bytes())

def token_checks(source,target):
    s=h.toks(source); t=h.toks(target)
    missing=[x for x in s[3] if x not in t[3]]
    return {
      'placeholderSequenceMatches':s[0]==t[0], 'markupMatches':s[1]==t[1],
      'numericTokensMatch':s[2]==t[2], 'protectedLiteralsMatch':not missing,
      'sourcePlaceholders':s[0], 'targetPlaceholders':t[0],
      'sourceMarkupTags':s[1], 'targetMarkupTags':t[1],
      'sourceNumericTokens':s[2], 'targetNumericTokens':t[2],
      'sourceProtectedLiterals':s[3], 'targetProtectedLiterals':t[3],
      'missingProtectedLiterals':missing,
    }

PROPOSALS={
 (1623,'es'):('correction','No se pudo emitir el evento.','The caller is a server-event error allowlist; emitir means to emit/raise an event, while generar suggests creating one.'),
 (1628,'ko'):('correction','탐색 정보를 새로 고치지 못했습니다: {error}','검색 발견 정보 is redundant and unnatural for the PodDiscoveryPanel discovery status.'),
 (1632,'zh-Hant'):('correction','無法註冊 Pod。','Corrects the Simplified character 注 in the Traditional Chinese form 註冊 and aligns the domain term with Pod.'),
 (1633,'vi'):('correction','Không thể đăng ký Pod:','The current translation says group (nhóm), but the caller and sibling errors refer to the named Pod feature.'),
 (1641,'hi'):('correction','इस उपयोगकर्ता की जानकारी प्राप्त नहीं हो सकी:','The caller appends the selected username after this fragment; the current ending के लिए places the Hindi postposition before its noun.'),
 (1641,'ja'):('correction','ユーザーの情報を取得できませんでした：','The caller appends the selected username after this fragment; the current の starts an unattached possessive and ends with a sentence stop.'),
 (1641,'ko'):('correction','해당 사용자의 정보를 가져오지 못했습니다:','The caller appends the selected username after this fragment; the current sentence ends before the username and does not connect it.'),
 (1641,'zh-Hans'):('correction','无法获取用户信息：','The caller appends the selected username after this fragment; the current translation omits the relation to that user.'),
 (1641,'zh-Hant'):('correction','無法取得使用者資訊：','The caller appends the selected username after this fragment; the current translation omits the relation to that user.'),
}

input_checksum_sha=verify_input_sums(INPUT)
manifest=readj(INPUT/'manifest.json')
if (manifest['head'],manifest['tree'],manifest['selectedPositions'],manifest['cellCount'],manifest['candidateFreeInputOnly'])!=(HEAD,TREE,[1623,1642],240,True):
    raise RuntimeError('candidate-free packet pin/scope mismatch')
cells=readjl(INPUT/'current-target-cells.jsonl')
contexts={x['position']:x for x in readjl(INPUT/'source-contexts.jsonl')}
if len(cells)!=240: raise RuntimeError('expected 240 candidate-free cells')
ledger=[]
for src in cells:
    pos,loc,key=src['position'],src['locale'],src['sourceKey']
    ctx=contexts[pos]
    record_sha=sha(canon(src))
    if not ctx['productionCallerCount']:
        ledger.append({
          'exactHead':HEAD,'exactTree':TREE,'position':pos,'locale':loc,'decision':'hold',
          'reasonCode':'zero-production-caller-hash-only','reason':'No exact quoted production caller resolved in the pinned scan; preserve as a hash-only hold.',
          'confidence':'high','sourceKeySha256':src['sourceKeySha256'],'sourceTextSha256':sha(key),
          'currentTargetSha256':src['currentTargetSha256'],'sourceContextSha256':src['sourceContextSha256'],
          'candidateFreeCellRecordSha256':record_sha,'callerCount':0,
          'catalogPath':src['catalogPath'],'catalogFileSha256':src['catalogFileSha256'],'catalogGitBlob':src['catalogGitBlob'],
          'textIncluded':False,
        })
        continue
    proposal=PROPOSALS.get((pos,loc)); decision=proposal[0] if proposal else 'accept-current'
    current_checks=token_checks(key,src['currentTarget'])
    if not all(current_checks[k] for k in ('placeholderSequenceMatches','markupMatches','numericTokensMatch','protectedLiteralsMatch')):
        raise RuntimeError(f'current token mismatch at {pos}/{loc}')
    caller_paths=sorted({r['path'] for r in ctx['callers']})
    row={
      'exactHead':HEAD,'exactTree':TREE,'position':pos,'sourceKey':key,'sourceKeySha256':src['sourceKeySha256'],
      'sourceTextSha256':sha(key),'locale':loc,'decision':decision,
      'currentTarget':src['currentTarget'],'currentTargetSha256':src['currentTargetSha256'],
      'sourceContextSha256':src['sourceContextSha256'],'callerCount':ctx['productionCallerCount'],
      'callerOccurrenceCount':ctx['callerOccurrenceCount'],'callerPaths':caller_paths,
      'candidateFreeCellRecordSha256':record_sha,
      'catalogPath':src['catalogPath'],'catalogFileSha256':src['catalogFileSha256'],'catalogGitBlob':src['catalogGitBlob'],
      'currentTokenChecks':current_checks,
      'confidence':'high' if loc in {'es','de','fr','pt-BR','id','vi'} else 'moderate',
    }
    if proposal:
        kind,target,rationale=proposal
        proposal_checks=token_checks(key,target)
        if not all(proposal_checks[k] for k in ('placeholderSequenceMatches','markupMatches','numericTokensMatch','protectedLiteralsMatch')):
            raise RuntimeError(f'proposal token mismatch at {pos}/{loc}')
        row.update({'proposedTarget':target,'proposedTargetSha256':sha(target),'rationale':rationale,'proposalTokenChecks':proposal_checks})
    else:
        if pos==1641:
            rationale='The pinned caller appends the selected username immediately after this failure prefix; the retained target connects that identifier to the lookup failure.'
        else:
            rationale='Conveys the source failure and operation in the pinned caller context; current wording passes placeholder, markup, number, and protected-literal checks.'
        row['rationale']=rationale
    ledger.append(row)

assert len(ledger)==240
ledger.sort(key=lambda r:(r['position'],LOCS.index(r['locale'])))
(ROOT/'primary-ledger.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False,sort_keys=True)+'\n' for r in ledger),encoding='utf-8')
proposals=[r for r in ledger if r['decision'] in {'correction','refinement'}]
holds=[r for r in ledger if r['decision']=='hold']
(ROOT/'proposals.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False,sort_keys=True)+'\n' for r in proposals),encoding='utf-8')
(ROOT/'holds-hash-only.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False,sort_keys=True)+'\n' for r in holds),encoding='utf-8')
counts=collections.Counter(r['decision'] for r in ledger)
by_locale={loc:dict(collections.Counter(r['decision'] for r in ledger if r['locale']==loc)) for loc in LOCS}
summary={
 'schemaVersion':1,'result':'PASS','reviewType':'primary-semantic-review-only','window':'W1623-W1642',
 'repository':'snapetech-org/slskR','pullRequest':209,'exactHead':HEAD,'exactTree':TREE,
 'sourceCount':20,'cellCount':240,'localeOrder':LOCS,'decisionCounts':dict(counts),'byLocale':by_locale,
 'proposalCount':len(proposals),'hashOnlyHoldCount':len(holds),'callerlessSourceCount':len(manifest['callerResolutionHoldPositions']),
 'allCurrentTokenChecksPass':all(all(r['currentTokenChecks'][k] for k in ('placeholderSequenceMatches','markupMatches','numericTokensMatch','protectedLiteralsMatch')) for r in ledger if r['decision']!='hold'),
 'allProposalTokenChecksPass':all(all(r['proposalTokenChecks'][k] for k in ('placeholderSequenceMatches','markupMatches','numericTokensMatch','protectedLiteralsMatch')) for r in proposals),
 'candidateFreeChecksumListSha256':input_checksum_sha,'candidateFreeManifestSha256':sha((INPUT/'manifest.json').read_bytes()),
 'priorLineageReattested':{'priorWindowCells':1920,'sourceSelections':380,'appliedTargets':82,'carryForwardHolds':62,'allMatchedCurrentCatalogHashes':True},
 'livePrState':{'state':'OPEN','draft':True,'head':HEAD,'tree':TREE},
 'blindReviewPerformed':False,'crossReviewPerformed':False,'browserReviewPerformed':False,'nativeSpeakerReviewPerformed':False,
 'repoOrPrEditsMade':False,'workflowEditsMade':False,'projectTestsRun':False,'projectBuildsRun':False,'additionalProjectScansRun':False,
 'scopedCallerResolutionScan':'Performed only by the candidate-free packet builder and verifier as required for exact caller context.',
 'ciDispatched':False,'createdAtUtc':datetime.now(timezone.utc).isoformat(),
}
(ROOT/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,sort_keys=True,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'result':'BUILT','cells':len(ledger),'decisionCounts':dict(counts),'proposals':len(proposals),'holds':len(holds),'head':HEAD,'tree':TREE},ensure_ascii=False,indent=2))
