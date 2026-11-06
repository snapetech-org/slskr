#!/usr/bin/env python3
"""Independent offline integrity verifier for the W1743-W1762 blind packet.

Reads only candidate-free input packets and this review packet. It does not
open a repository or use the network.
"""
import hashlib
import json
import re
from pathlib import Path

OUT=Path(__file__).resolve().parent
INPUT=Path('/mnt/disks/scratch/task-scratch/slskr-pr209-w1743-1762-20261105/candidate-free-input')
PREVIOUS=Path('/mnt/disks/scratch/task-scratch/slskr-pr209-w1723-1742-20261105/candidate-free-input')
HEAD='ccbc3dc721c1cbd225d4e512f4f0af4c80476620'
TREE='075d1b72a2fd080404ebec19d354cb863638df21'
LOCALES=['es','zh-Hans','hi','de','ja','fr','pt-BR','ar','ko','zh-Hant','vi','id']


def sha(value):
    if isinstance(value,str): value=value.encode('utf-8')
    return hashlib.sha256(value).hexdigest()


def canon(value): return json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':'))
def j(name,folder): return json.loads((folder/name).read_text(encoding='utf-8'))
def jl(name,folder): return [json.loads(line) for line in (folder/name).read_text(encoding='utf-8').splitlines() if line]


def tokens(value):
    return {'placeholders':re.findall(r'\{[A-Za-z][A-Za-z0-9_]*\}',value),
            'markupTags':re.findall(r'</?[A-Za-z][^>]*>',value),
            'numericTokens':re.findall(r'(?<![A-Za-z])\d+(?:[.,]\d+)?%?(?![A-Za-z])',value),
            'protectedLiterals':list(dict.fromkeys(re.findall(r'(?<![A-Za-z0-9])(?:[A-Z]{2,}[A-Z0-9]*|ffmpeg|Chromaprint|Soulseek|Spotify|YouTube|Pushbullet|Matrix|WebSocket|OpenAI)(?![A-Za-z0-9])',value)))}


def verify_sums(folder):
    rows={}
    for line in (folder/'SHA256SUMS.txt').read_text(encoding='utf-8').splitlines():
        if line.strip():
            digest,name=line.split(None,1); rows[name.lstrip('* ')]=digest
    actual={p.name:sha(p.read_bytes()) for p in folder.iterdir() if p.is_file() and p.name!='SHA256SUMS.txt'}
    assert rows==actual,(folder,rows,actual)
    return len(rows)

input_sum_count=verify_sums(INPUT)
output_sum_count=verify_sums(OUT)
manifest=j('manifest.json',INPUT)
assert (manifest['head'],manifest['tree'],manifest['selectedPositions'],manifest['cellCount'],manifest['localeOrder'])==(HEAD,TREE,[1743,1762],240,LOCALES)
assert manifest['callerResolutionHoldPositions']==[1754,1755]
assert manifest['callerlessTargetTextsIncluded'] is False
assert (INPUT/'source-queue.jsonl').read_bytes()==(PREVIOUS/'source-queue.jsonl').read_bytes()

review=j('review-manifest.json',OUT)
assert review['head']==HEAD and review['tree']==TREE and review['window']=='W1743-W1762'
assert review['sourceInputManifestSha256']==sha((INPUT/'manifest.json').read_bytes())
assert review['sourceInputChecksumListSha256']==sha((INPUT/'SHA256SUMS.txt').read_bytes())
assert review['candidateFreeBlindReview'] is True and review['priorProposalOrDecisionFilesRead'] is False
for name,expected in review['sourceInputFileHashes'].items():
    assert sha((INPUT/name).read_bytes())==expected

keys=(INPUT/'selected-source-keys.txt').read_text(encoding='utf-8').splitlines()
queue=jl('source-queue.jsonl',INPUT); contexts=jl('source-contexts.jsonl',INPUT); target_rows=jl('current-target-cells.jsonl',INPUT)
assert len(keys)==20 and len(queue)==5441 and len(contexts)==20 and len(target_rows)==240
assert [x['sourceKey'] for x in queue[1742:1762]]==keys
source_by={x['position']:x for x in contexts}; target_by={(x['position'],x['locale']):x for x in target_rows}
assert len(source_by)==20 and len(target_by)==240
catalog=j('catalog-file-pins.json',INPUT)['localeCatalogs']
for pos in range(1743,1763):
    source=keys[pos-1743]; context=source_by[pos]
    assert context['sourceKey']==source and context['sourceKeySha256']==sha(source)
    assert context['callerContextSha256']==sha(canon({'sourceKey':source,'callers':context['callers']}))
    assert context['productionCallerCount']==len(context['callers'])
    assert context['callerOccurrenceCount']==sum(c['literalOccurrenceCount'] for c in context['callers'])
    for c in context['callers']:
        assert c['lineSha256']==sha(c['lineText'])
        assert c['contextSha256']==sha(canon(c['context']))
    for locale in LOCALES:
        target=target_by[(pos,locale)]; pin=catalog[locale]
        assert target['sourceKey']==source and target['sourceKeySha256']==sha(source)
        assert target['sourceContextSha256']==context['callerContextSha256']
        assert target['callerCount']==context['productionCallerCount']
        assert (target['catalogPath'],target['catalogFileSha256'],target['catalogGitBlob'])==(pin['path'],pin['sha256'],pin['gitBlob'])
        if context['productionCallerCount']==0:
            assert target['targetTextIncluded'] is False and 'currentTarget' not in target
            assert len(target['currentTargetSha256'])==64
        else:
            assert target['targetTextIncluded'] is True and isinstance(target['currentTarget'],str)
            assert target['currentTargetSha256']==sha(target['currentTarget'])
            s,t=tokens(source),tokens(target['currentTarget'])
            assert target['sourcePlaceholders']==s['placeholders'] and target['sourceMarkupTags']==s['markupTags']
            assert target['sourceNumericTokens']==s['numericTokens'] and target['sourceProtectedLiterals']==s['protectedLiterals']
            assert len(target['targetTokenVariants'])==1
            v=target['targetTokenVariants'][0]
            assert v['targetStringSha256']==target['currentTargetSha256']
            assert v['targetPlaceholders']==t['placeholders'] and v['targetMarkupTags']==t['markupTags']
            assert v['targetNumericTokens']==t['numericTokens'] and v['targetProtectedLiterals']==t['protectedLiterals']
            assert v['placeholderSequenceMatches']==(s['placeholders']==t['placeholders'])
            assert v['placeholderMultisetMatches']==(sorted(s['placeholders'])==sorted(t['placeholders']))
            assert v['markupMatches']==(s['markupTags']==t['markupTags'])
            assert v['numericTokensMatch']==(s['numericTokens']==t['numericTokens'])
            assert v['protectedLiteralsMatch']==all(x in t['protectedLiterals'] for x in s['protectedLiterals'])
            assert v['protectedLiteralMismatchTokens']==[]
            if pos==1752:
                assert all(term in target['currentTarget'] for term in ('flac','mp3','wav','m4a'))
            if pos==1758:
                assert 'RustyMilk' in target['currentTarget']

# Exact 240-cell coverage, including text-free holds for callerless positions.
ledger=jl('blind-review-ledger.jsonl',OUT)
assert len(ledger)==240 and len({(x['position'],x['locale']) for x in ledger})==240
by_cell={(x['position'],x['locale']):x for x in ledger}
assert set(by_cell)==set(target_by)
counts={'accept':0,'revise':0,'hold':0}
for pos in range(1743,1763):
    source=keys[pos-1743]; context=source_by[pos]; s=tokens(source)
    pins=[{'path':c['path'],'line':c['line'],'lineSha256':c['lineSha256'],'contextSha256':c['contextSha256'],
           'fileSha256':c['fileSha256'],'gitBlob':c['gitBlob'],'literalOccurrenceCount':c['literalOccurrenceCount']} for c in context['callers']]
    for locale in LOCALES:
        cell=by_cell[(pos,locale)]; target=target_by[(pos,locale)]; counts[cell['decision']]+=1
        assert cell['position']==pos and cell['locale']==locale
        assert cell['sourceKeySha256']==context['sourceKeySha256']
        assert cell['callerContextSha256']==context['callerContextSha256']
        if context['productionCallerCount']==0:
            assert cell['decision']=='hold' and cell['targetTextIncluded'] is False and cell['callerCount']==0
            assert 'sourceKey' not in cell and 'currentTarget' not in cell and 'recommendedTarget' not in cell
            assert cell['currentTargetSha256']==target['currentTargetSha256']
            continue
        assert cell['decision'] in ('accept','revise') and cell['targetTextIncluded'] is True
        assert cell['sourceKey']==source and cell['callerPins']==pins
        assert cell['callerCount']==context['productionCallerCount'] and cell['callerOccurrenceCount']==context['callerOccurrenceCount']
        assert cell['currentTarget']==target['currentTarget'] and cell['currentTargetSha256']==sha(cell['currentTarget'])==target['currentTargetSha256']
        t=tokens(cell['currentTarget'])
        checks={'source':s,'target':t,'placeholderSequenceMatches':s['placeholders']==t['placeholders'],
                'markupMatches':s['markupTags']==t['markupTags'],'numericTokensMatch':s['numericTokens']==t['numericTokens'],
                'protectedLiteralsPreserved':all(x in t['protectedLiterals'] for x in s['protectedLiterals'])}
        assert cell['tokenCheck']==checks and all(checks[k] for k in ('placeholderSequenceMatches','markupMatches','numericTokensMatch','protectedLiteralsPreserved'))
        if pos==1752:
            assert cell['additionalExactLiteralChecks']['sourceExamples']==['flac','mp3','wav','m4a']
            assert cell['additionalExactLiteralChecks']['sourceExamplesPreserved'] is True
        if pos==1758:
            assert cell['additionalExactLiteralChecks']['brandLiteral']=='RustyMilk'
            assert cell['additionalExactLiteralChecks']['brandLiteralPreserved'] is True
        if pos in (1743,1744) and 'filename' in cell['currentTarget']:
            assert cell['additionalExactLiteralChecks']['apiFieldLiteral']=='filename'
            assert cell['additionalExactLiteralChecks']['apiFieldLiteralCasePreserved'] is True
        if cell['decision']=='revise':
            assert isinstance(cell.get('recommendedTarget'),str) and cell['recommendedTarget']
            rec=tokens(cell['recommendedTarget'])
            assert s['placeholders']==rec['placeholders'] and s['markupTags']==rec['markupTags'] and s['numericTokens']==rec['numericTokens']
            assert all(x in rec['protectedLiterals'] for x in s['protectedLiterals'])
            if pos==1758: assert 'RustyMilk' in cell['recommendedTarget']
        else:
            assert cell['decision']=='accept' and 'recommendedTarget' not in cell

assert counts==review['counts']=={'accept':203,'revise':13,'hold':24}
assert review['callerlessPositions']==[1754,1755] and review['callerlessCellCount']==24

# Active hold is copied forward with hashes only.
active=jl('preserved-active-holds.jsonl',OUT); input_active=jl('active-hold-reattestation.jsonl',INPUT)
assert len(active)==len(input_active)==1
h=active[0]; ih=input_active[0]
assert h['holdId']=='1719::id' and h['textRedacted'] is True
assert h['sourceKeySha256']==ih['sourceKeySha256'] and h['currentTargetSha256']==ih['currentTargetSha256']
assert h['currentSourceContextSha256']==ih['currentSourceContextSha256']
assert h['targetHashUnchanged'] is True and h['sourceContextUnchanged'] is True and h['textIncluded'] is False
assert not ({'sourceKey','currentTarget','sourceText','targetText'} & set(h))
print(json.dumps({'result':'PASS','inputFilesChecksummed':input_sum_count,'outputFilesChecksummed':output_sum_count,
                  'cells':len(ledger),'decisions':counts,'callerlessPositions':[1754,1755],
                  'activeHold':'1719::id hash-only','queueContinuity':'exact'},ensure_ascii=False,indent=2))
