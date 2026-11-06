#!/usr/bin/env python3
"""Build the independent blind review from candidate-free input only."""
from __future__ import annotations
import hashlib, json, re
from collections import Counter
from pathlib import Path

TASK = Path(__file__).resolve().parent.parent
INPUT = TASK / 'candidate-free-input'
OUT = Path(__file__).resolve().parent
HEAD = '7e366cbf21ad5490bd11ef418a0f2a98b3fbd567'
TREE = '801d7a037c15dcd83b3e038160054a46c9b8f03b'
LOCALES = ['es','zh-Hans','hi','de','ja','fr','pt-BR','ar','ko','zh-Hant','vi','id']
PROPOSALS = {
    (1628, 'ko'): ('검색 정보를 새로 고치지 못했습니다: {error}', 'The current phrase redundantly combines “search” and “discovery”; this matches the neighboring discovery error while preserving the error placeholder.'),
    (1631, 'zh-Hant'): ('無法註冊訊息：{error}', '「登錄」means sign in/log in here; 「註冊」correctly expresses registering the message.'),
    (1633, 'vi'): ('Không thể đăng ký Pod:', 'The current wording translates the technical Pod as “group,” which changes the entity being registered.'),
    (1638, 'pt-BR'): ('Não foi possível escanear novamente os compartilhamentos', '“Verificar” means check/verify rather than scan; this wording preserves the rescan operation.'),
    (1641, 'de'): ('Fehler beim Abruf der Informationen für', 'The caller appends the username after this text; moving the failure phrase before “für” makes the combined message grammatical.'),
    (1641, 'zh-Hans'): ('获取信息失败，用户', 'The caller appends the username after this text; labeling the following name avoids the current phrase’s broken word order.'),
    (1641, 'hi'): ('जानकारी प्राप्त नहीं हो सकी, उपयोगकर्ता', 'The caller appends the username after this text; this puts the failure clause before a label for that name.'),
    (1641, 'ja'): ('情報の取得に失敗しました。対象ユーザー', 'The caller appends the username after this text; the current genitive-first fragment cannot attach naturally to the following name.'),
    (1641, 'ar'): ('تعذر استرداد المعلومات الخاصة بالمستخدم', 'The caller appends the username after this text; this expresses information for the user without leaving the preposition detached.'),
    (1641, 'ko'): ('사용자 정보를 가져오지 못했습니다. 사용자', 'The caller appends the username after this text; the current sentence ends before that name and leaves “다음에 대한” unresolved.'),
    (1641, 'zh-Hant'): ('無法取得資訊，使用者', 'The caller appends the username after this text; labeling the following name fixes the current phrase’s word order.'),
}

def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def sha_text(text: str) -> str:
    return sha(text.encode('utf-8'))

def canon(obj) -> bytes:
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode('utf-8')

def readjl(path: Path):
    return [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines() if line.strip()]

# Ensure review starts only from a sealed candidate-free input and the expected pin.
manifest = json.loads((INPUT/'manifest.json').read_text(encoding='utf-8'))
assert manifest['head'] == HEAD and manifest['tree'] == TREE
assert manifest['candidateFreeInputOnly'] is True and manifest['proposedTranslationsIncluded'] is False
sums = {}
for line in (INPUT/'SHA256SUMS.txt').read_text(encoding='utf-8').splitlines():
    if line.strip():
        digest, name = line.split(None, 1)
        sums[name.lstrip('* ')] = digest
actual = {p.name: sha(p.read_bytes()) for p in INPUT.iterdir() if p.is_file() and p.name != 'SHA256SUMS.txt'}
assert sums == actual
cells = readjl(INPUT/'current-target-cells.jsonl')
contexts = {r['position']: r for r in readjl(INPUT/'source-contexts.jsonl')}
assert len(cells) == 240 and len(contexts) == 20
assert [(r['position'], r['locale']) for r in cells] == [(p,l) for p in range(1623,1643) for l in LOCALES]

rows=[]
for c in cells:
    key=(c['position'],c['locale'])
    ctx=contexts[c['position']]
    assert c['sourceKey']==ctx['sourceKey'] and c['sourceContextSha256']==ctx['callerContextSha256']
    assert c['callerCount']==ctx['productionCallerCount'] and ctx['productionCallerCount'] > 0
    assert sha_text(c['currentTarget'])==c['currentTargetSha256']
    proposal=PROPOSALS.get(key)
    if proposal:
        decision='correction'; target, reason=proposal
        target_hash=sha_text(target)
    else:
        decision='accept'; target=None; target_hash=None
        if '{error}' in c['sourceKey']:
            reason='The wording conveys the failed operation naturally, and the {error} placeholder is retained in the caller’s error-message position.'
        elif c['sourceKey']=='Failed to retrieve information for':
            reason='The phrase can be followed by the username supplied by this caller and forms a natural user-specific message.'
        else:
            reason='The wording accurately conveys the failed action in this application error context and reads naturally for the locale.'
    row={
        'position':c['position'], 'locale':c['locale'],
        'sourceKey':c['sourceKey'], 'sourceKeySha256':c['sourceKeySha256'],
        'sourceContextSha256':c['sourceContextSha256'],
        'callerCount':c['callerCount'], 'callerOccurrenceCount':ctx['callerOccurrenceCount'],
        'catalogPath':c['catalogPath'], 'catalogFileSha256':c['catalogFileSha256'], 'catalogGitBlob':c['catalogGitBlob'],
        'currentTarget':c['currentTarget'], 'currentTargetSha256':c['currentTargetSha256'],
        'decision':decision, 'reason':reason,
        'suggestedTarget':target, 'suggestedTargetSha256':target_hash,
        'reviewConfidence':'moderate',
    }
    row['reviewRecordSha256']=sha(canon(row))
    rows.append(row)

# Separate proposal and hash-only hold ledgers are linked by cell identity.
proposals=[]
for r in rows:
    if r['decision']=='correction':
        p={k:r[k] for k in ('position','locale','sourceKeySha256','sourceContextSha256','currentTargetSha256','decision','reason','suggestedTarget','suggestedTargetSha256','reviewConfidence')}
        p['proposalRecordSha256']=sha(canon(p)); proposals.append(p)

counts=Counter(r['decision'] for r in rows)
assert counts==Counter({'accept':229,'correction':11})
input_hashes={name:actual[name] for name in sorted(actual)}
input_attestation={
    'repository':'snapetech-org/slskR','pullRequest':209,
    'exactHead':HEAD,'exactTree':TREE,
    'candidateFreeVerifierResult':'PASS','candidateFreeVerifier':'verify_candidate_free_full.py',
    'candidateFreeChecksumListSha256':sha((INPUT/'SHA256SUMS.txt').read_bytes()),
    'inputFilesSha256':input_hashes,
    'pinnedSourceWorktree':{'path':str(TASK/'worktree'),'head':HEAD,'tree':TREE,'statusClean':True},
    'initialPRRefs':json.loads((TASK/'attestation'/'pin-before-review.json').read_text(encoding='utf-8')),
    'primaryReviewFilesOpened':False,
    'browserReviewPerformed':False,'nativeSpeakerReviewPerformed':False,
    'repositoryEdits':False,'prEdits':False,'testsBuildsScansCI':False,
}
(OUT/'review-cells.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False,separators=(',',':'))+'\n' for r in rows),encoding='utf-8')
(OUT/'proposals.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False,separators=(',',':'))+'\n' for r in proposals),encoding='utf-8')
(OUT/'holds-hash-only.jsonl').write_text('',encoding='utf-8')
(OUT/'input-attestation.json').write_text(json.dumps(input_attestation,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
summary={
    'repository':'snapetech-org/slskR','pullRequest':209,'exactHead':HEAD,'exactTree':TREE,
    'window':'W1623-W1642','cellCount':len(rows),'sourceCount':20,'localeCount':12,
    'decisionCounts':dict(sorted(counts.items())),'proposalCount':len(proposals),'hashOnlyHoldCount':0,
    'callerlessPositions':[],'callerReferences':20,'callerOccurrences':20,'callerFiles':12,
    'nativeSpeakerReview':False,'browserReview':False,'primaryReviewFilesOpened':False,
    'repoEdits':False,'prEdits':False,'testsBuildsScansCi':False,
    'candidateFreeChecksumListSha256':input_attestation['candidateFreeChecksumListSha256'],
}
(OUT/'review-summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
manifest_out={
    'artifact':'slskR PR #209 W1623-W1642 independent blind review',
    'exactHead':HEAD,'exactTree':TREE,
    'candidateFreeInputChecksumListSha256':input_attestation['candidateFreeChecksumListSha256'],
    'cells':240,'sourceKeys':20,'locales':LOCALES,
    'decisionCounts':dict(sorted(counts.items())), 'proposalCount':len(proposals), 'hashOnlyHoldCount':0,
    'primaryReviewFilesOpened':False,'semanticReviewIndependent':True,
    'nativeSpeakerSignoff':False,'browserReview':False,
    'files': ['review-cells.jsonl','proposals.jsonl','holds-hash-only.jsonl','review-summary.json','input-attestation.json'],
}
(OUT/'review-manifest.json').write_text(json.dumps(manifest_out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
(OUT/'README.md').write_text('''# slskR PR #209 W1623–W1642 independent blind review\n\nThis packet independently reviews all 240 current translations at head `7e366cbf21ad5490bd11ef418a0f2a98b3fbd567` / tree `801d7a037c15dcd83b3e038160054a46c9b8f03b`. It used only the sealed candidate-free input and pinned source worktree. No primary-review files were opened.\n\n## Decisions\n\n- Accept: 229\n- Correction: 11\n- Hold: 0 (the candidate-free input has no callerless positions)\n\nEach review row binds the source key, caller-context hash, current text and hash, decision, reason, and any suggested wording. Proposed text preserves caller placeholders and protected tokens; `verify_blind_review.py` checks token parity and record hashes.\n\nThis is an AI semantic review, not native-speaker or browser signoff. No repository, PR, or workflow files were changed. No tests, builds, scans, or CI were run.\n''',encoding='utf-8')
print(json.dumps({'builtRows':len(rows),'counts':dict(sorted(counts.items())),'proposals':len(proposals),'hashOnlyHolds':0},indent=2))
