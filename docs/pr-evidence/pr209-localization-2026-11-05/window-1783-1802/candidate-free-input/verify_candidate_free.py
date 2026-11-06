#!/usr/bin/env python3
"""Offline integrity check for the W1783-W1802 candidate-free input."""
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PREVIOUS = ROOT.parent.parent / 'window-1763-1782/candidate-free'
HEAD = '0264a4fcaa944fee61049efec0cf3c451416c8b9'
TREE = '895e57c178d959a23aceddead27623f2dd854ba0'
LOCALES = ['es','zh-Hans','hi','de','ja','fr','pt-BR','ar','ko','zh-Hant','vi','id']


def sha(value):
    if isinstance(value, str): value = value.encode('utf-8')
    return hashlib.sha256(value).hexdigest()


def canon(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'))


def read_json(name): return json.loads((ROOT/name).read_text(encoding='utf-8'))
def read_jsonl(name): return [json.loads(line) for line in (ROOT/name).read_text(encoding='utf-8').splitlines() if line]


def tokens(value):
    return {'placeholders':re.findall(r'\{[A-Za-z][A-Za-z0-9_]*\}',value),
            'markupTags':re.findall(r'</?[A-Za-z][^>]*>',value),
            'numericTokens':re.findall(r'(?<![A-Za-z])\d+(?:[.,]\d+)?%?(?![A-Za-z])',value),
            'protectedLiterals':list(dict.fromkeys(re.findall(r'(?<![A-Za-z0-9])(?:[A-Z]{2,}[A-Z0-9]*|ffmpeg|Chromaprint|Soulseek|Spotify|YouTube|Pushbullet|Matrix|WebSocket|OpenAI)(?![A-Za-z0-9])',value)))}


def check_sums():
    sums={}
    for line in (ROOT/'SHA256SUMS.txt').read_text(encoding='utf-8').splitlines():
        if line.strip():
            digest,name=line.split(None,1); sums[name.lstrip('* ')]=digest
    actual={p.name:sha(p.read_bytes()) for p in ROOT.iterdir() if p.is_file() and p.name!='SHA256SUMS.txt'}
    assert sums==actual,(sums,actual)
    return len(sums)

sum_count=check_sums()
m=read_json('manifest.json')
assert (m['head'],m['tree'],m['selectedPositions'],m['sourceCount'],m['localeOrder'],m['cellCount']) == (HEAD,TREE,[1783,1802],20,LOCALES,240)
assert m['callerlessTargetTextsIncluded'] is False
before=read_json('attestation-before.json'); after=read_json('attestation-after.json')
for att in (before,after):
    assert att['headSha']==HEAD and att['headTree']==TREE and att['headRef']=='codex/slskr-l10n-audit-20261104-resync'
assert before['remoteRefs']==after['remoteRefs']
queue=read_jsonl('source-queue.jsonl'); prev_queue=(PREVIOUS/'source-queue.jsonl').read_bytes()
assert len(queue)==5441 and sha((ROOT/'source-queue.jsonl').read_bytes())==m['sourceQueueFileSha256']
assert (ROOT/'source-queue.jsonl').read_bytes()==prev_queue
keys=(ROOT/'selected-source-keys.txt').read_text(encoding='utf-8').splitlines()
assert len(keys)==20 and [x['sourceKey'] for x in queue[1782:1802]]==keys
assert [x['position'] for x in read_jsonl('source-window-boundaries.jsonl')]==list(range(1782,1804))
source_rows=read_jsonl('source-contexts.jsonl'); assert len(source_rows)==20
source_by={x['position']:x for x in source_rows}
target_rows=read_jsonl('current-target-cells.jsonl'); assert len(target_rows)==240
target_by={(x['position'],x['locale']):x for x in target_rows}; assert len(target_by)==240
catalog=read_json('catalog-file-pins.json')['localeCatalogs']
token_mismatches={'placeholderSequenceMismatchCount':0,'markupMismatchCount':0,'numericTokenMismatchCount':0,'protectedLiteralMismatchCount':0}
for pos in range(1783,1803):
    src=keys[pos-1783]; row=source_by[pos]
    assert row['sourceKey']==src and row['sourceKeySha256']==sha(src)
    assert row['callerContextSha256']==sha(canon({'sourceKey':src,'callers':row['callers']}))
    assert row['productionCallerCount']==len(row['callers'])
    assert row['callerOccurrenceCount']==sum(c['literalOccurrenceCount'] for c in row['callers'])
    for c in row['callers']:
        assert c['lineSha256']==sha(c['lineText'])
        assert c['contextSha256']==sha(canon(c['context']))
    for locale in LOCALES:
        t=target_by[(pos,locale)]; pin=catalog[locale]
        assert t['sourceKey']==src and t['sourceKeySha256']==sha(src)
        assert t['sourceContextSha256']==row['callerContextSha256']
        assert t['callerCount']==row['productionCallerCount']
        assert (t['catalogPath'],t['catalogFileSha256'],t['catalogGitBlob'])==(pin['path'],pin['sha256'],pin['gitBlob'])
        if row['productionCallerCount']==0:
            assert t['targetTextIncluded'] is False and 'currentTarget' not in t
            assert t['currentTargetType']=='str' and len(t['currentTargetSha256'])==64
        else:
            assert t['targetTextIncluded'] is True and isinstance(t['currentTarget'],str)
            assert t['currentTargetSha256']==sha(t['currentTarget'])
            st,tt=tokens(src),tokens(t['currentTarget'])
            assert t['sourcePlaceholders']==st['placeholders'] and t['sourceMarkupTags']==st['markupTags']
            assert t['sourceNumericTokens']==st['numericTokens'] and t['sourceProtectedLiterals']==st['protectedLiterals']
            assert len(t['targetTokenVariants'])==1
            v=t['targetTokenVariants'][0]
            assert v['targetStringSha256']==t['currentTargetSha256']
            assert v['targetPlaceholders']==tt['placeholders'] and v['targetMarkupTags']==tt['markupTags']
            assert v['targetNumericTokens']==tt['numericTokens'] and v['targetProtectedLiterals']==tt['protectedLiterals']
            assert v['placeholderSequenceMatches']==(st['placeholders']==tt['placeholders'])
            assert v['markupMatches']==(st['markupTags']==tt['markupTags'])
            assert v['numericTokensMatch']==(st['numericTokens']==tt['numericTokens'])
            assert v['protectedLiteralsMatch']==(not [x for x in st['protectedLiterals'] if x not in tt['protectedLiterals']])
            token_mismatches['placeholderSequenceMismatchCount'] += not v['placeholderSequenceMatches']
            token_mismatches['markupMismatchCount'] += not v['markupMatches']
            token_mismatches['numericTokenMismatchCount'] += not v['numericTokensMatch']
            token_mismatches['protectedLiteralMismatchCount'] += not v['protectedLiteralsMatch']

holds=read_jsonl('caller-resolution-holds.jsonl')
assert [x['position'] for x in holds]==[]
for hold in holds:
    assert 'sourceKey' not in hold and len(hold['sourceKeySha256'])==64
active=read_jsonl('active-hold-reattestation.jsonl'); assert len(active)==1
h=active[0]
assert h['holdId']=='1719::id' and h['currentHead']==HEAD and h['currentTree']==TREE
assert h['textIncluded'] is False and h['targetHashUnchanged'] is True and h['sourceContextUnchanged'] is True
assert not ({'sourceKey','currentTarget','sourceText','targetText'} & set(h))
lineage=read_json('source-order-lineage.json')
assert lineage['window']=='W1783-W1802' and lineage['previousWindow']=='W1763-W1782'
assert lineage['previousBoundaryPosition']==1782 and lineage['nextBoundaryPosition']==1803
assert lineage['gapPositions']==[] and lineage['overlapPositions']==[] and lineage['queueMatchesPreviousSealedQueue'] is True
assert token_mismatches==m['tokenMismatchCounts'],(token_mismatches,m['tokenMismatchCounts'])

# Verify the exact predecessor packet and reattest every one of its 240 current-target readbacks by hash.
prior_sums={}
for line in (PREVIOUS/'SHA256SUMS.txt').read_text(encoding='utf-8').splitlines():
    if line.strip():
        digest,name=line.split(None,1); prior_sums[name.lstrip('* ')]=digest
prior_actual={p.relative_to(PREVIOUS).as_posix():sha(p.read_bytes()) for p in PREVIOUS.rglob('*') if p.is_file() and p.name!='SHA256SUMS.txt'}
assert prior_sums==prior_actual
prior_manifest=json.loads((PREVIOUS/'manifest.json').read_text(encoding='utf-8'))
assert (prior_manifest['head'],prior_manifest['tree'],prior_manifest['selectedPositions'],prior_manifest['candidateFreeInputOnly'],prior_manifest['proposedTranslationsIncluded']) == ('5191888071f54061a6012acdedfeb518a6cb3661','d5728c24b54a06dda432afd2ef5f378206a6cb8f',[1763,1782],True,False)
prior_cells=[json.loads(line) for line in (PREVIOUS/'current-target-cells.jsonl').read_text(encoding='utf-8').splitlines() if line]
prior_contexts=[json.loads(line) for line in (PREVIOUS/'source-contexts.jsonl').read_text(encoding='utf-8').splitlines() if line]
assert len(prior_cells)==240 and len(prior_contexts)==20
prior_by={(x['position'],x['locale']):x for x in prior_cells}
readbacks=read_jsonl('previous-window-readback-reattestation-hash-only.jsonl')
assert len(readbacks)==240 and len({(x['position'],x['locale']) for x in readbacks})==240
prior_ctx_by={x['position']:x for x in prior_contexts}
for rb in readbacks:
    old=prior_by[(rb['position'],rb['locale'])]
    oldctx=prior_ctx_by[rb['position']]
    assert rb['sourceKeySha256']==old['sourceKeySha256']
    assert rb['priorCallerCount']==oldctx['productionCallerCount']
    assert rb['priorCallerContextSha256']==oldctx['callerContextSha256']==old['sourceContextSha256']
    assert rb['priorTargetSha256']==old['currentTargetSha256']
    if old['targetTextIncluded']:
        assert isinstance(old.get('currentTarget'),str) and sha(old['currentTarget'])==old['currentTargetSha256']
    else:
        assert 'currentTarget' not in old and old['targetTextIncluded'] is False
    assert rb['targetTextIncluded'] is False and not ({'sourceKey','currentTarget','targetText','sourceText'} & set(rb))
    assert rb['targetHashUnchanged']==(rb['priorTargetSha256']==rb['currentTargetSha256'])
    assert rb['callerContextUnchanged']==(rb['priorCallerContextSha256']==rb['currentCallerContextSha256'])
readback_counts={
 'previousWindowReadbackCount':len(readbacks),
 'previousWindowTargetHashUnchangedCount':sum(x['targetHashUnchanged'] for x in readbacks),
 'previousWindowTargetHashChangedCount':sum(not x['targetHashUnchanged'] for x in readbacks),
 'previousWindowCallerContextUnchangedCount':sum(x['callerContextUnchanged'] for x in readbacks),
 'previousWindowCallerContextChangedCount':sum(not x['callerContextUnchanged'] for x in readbacks)}
for key,value in readback_counts.items():
    assert m[key]==value and lineage[key]==value
assert m['previousWindowReadbackTextsIncluded'] is False
assert m['previousWindowReadbackCount']==240
# Remote refs in both captures must pin the PR branch/pull ref and remain stable; main is recorded separately.
for att in (before,after):
    assert att['remoteRefs']['refs/heads/codex/slskr-l10n-audit-20261104-resync']==HEAD
    assert att['remoteRefs']['refs/pull/209/head']==HEAD
    assert att['remoteMainMatchesPrBaseSha']==(att['remoteRefs'].get('refs/heads/main')==att['baseSha'])
assert before['remoteRefs']==after['remoteRefs']

print(json.dumps({'result':'PASS','checksummedFiles':sum_count,'head':HEAD,'tree':TREE,'positions':[1783,1802],
                  'cells':240,'callerlessPositions':[],'tokenMismatchCounts':token_mismatches,'callerReferences':m['callerReferenceCount'],
                  'activeHold':'1719::id hash-only'},ensure_ascii=False,indent=2))
