#!/usr/bin/env python3
"""Portable integrity and source-binding verifier for this blind-review packet."""
from __future__ import annotations
import argparse
import collections
import hashlib
import json
import pathlib
import re
import subprocess
import sys

ROOT=pathlib.Path(__file__).resolve().parent
PACKET=ROOT.parent/'candidate-free-input'
HEAD='2d804c49879372071adf606bc2a2cf51e261fd94'
TREE='d6f5552d2400d868c2f2af98eb68caadfd4f3f66'
LOCALES=['es','zh-Hans','hi','de','ja','fr','pt-BR','ar','ko','zh-Hant','vi','id']
POSITIONS=list(range(1643,1663))

def sha(b): return hashlib.sha256(b).hexdigest()
def readj(p): return json.loads(p.read_text(encoding='utf-8'))
def jsonl(path): return [json.loads(x) for x in path.read_text(encoding='utf-8').splitlines() if x.strip()]
def token_signature(s):
    placeholders=re.findall(r'\{[A-Za-z][A-Za-z0-9_]*\}',s)
    markup=re.findall(r'</?[A-Za-z][^>]*>',s)
    numbers=re.findall(r'(?<![A-Za-z])\d+(?:[.,]\d+)?%?(?![A-Za-z])',s)
    protected=[]
    for x in re.findall(r'(?<![A-Za-z0-9])(?:[A-Z]{2,}[A-Z0-9]*|ffmpeg|Chromaprint|Soulseek|Spotify|YouTube|Pushbullet|Matrix|WebSocket|OpenAI)(?![A-Za-z0-9])',s):
        if x not in protected: protected.append(x)
    return placeholders,markup,numbers,protected

def verify_sums(directory, sumfile):
    expected={}
    for line in sumfile.read_text(encoding='utf-8').splitlines():
        if not line.strip(): continue
        h,name=line.split(None,1)
        name=name.lstrip(' *')
        expected[name]=h
    if not expected: raise ValueError(f'empty checksum index: {sumfile}')
    for name,h in expected.items():
        p=directory/name
        if not p.is_file(): raise ValueError(f'missing checksummed file: {p}')
        if sha(p.read_bytes())!=h: raise ValueError(f'checksum mismatch: {p}')
    return len(expected)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--repo',help='optional exact detached worktree for HEAD/tree/cleanliness recheck')
    args=ap.parse_args()
    inp_count=verify_sums(PACKET,PACKET/'SHA256SUMS.txt')
    out_count=verify_sums(ROOT,ROOT/'SHA256SUMS.txt')
    im=readj(PACKET/'manifest.json')
    manifest=readj(ROOT/'manifest.json')
    summary=readj(ROOT/'summary.json')
    if im.get('head')!=HEAD or im.get('tree')!=TREE: raise ValueError('candidate-free packet exact pin mismatch')
    if manifest.get('exactHead')!=HEAD or manifest.get('exactTree')!=TREE: raise ValueError('review manifest exact pin mismatch')
    if manifest.get('inputManifestSha256')!=sha((PACKET/'manifest.json').read_bytes()): raise ValueError('input manifest hash mismatch')
    if manifest.get('inputChecksumIndexSha256')!=sha((PACKET/'SHA256SUMS.txt').read_bytes()): raise ValueError('input checksum-index hash mismatch')
    rows_raw=[]
    for line in (PACKET/'current-target-cells.jsonl').read_bytes().splitlines():
        if line.strip(): rows_raw.append((json.loads(line),sha(line)))
    source_by_cell={}
    for row,rowhash in rows_raw:
        source_by_cell[(row['position'],row['locale'])]=(row,rowhash)
    contexts={x['sourceKey']:x for x in jsonl(PACKET/'source-contexts.jsonl')}
    ledger=jsonl(ROOT/'ledger.jsonl'); proposals=jsonl(ROOT/'proposals.jsonl')
    if len(rows_raw)!=240 or len(ledger)!=240: raise ValueError('expected exactly 240 input and ledger cells')
    if len(contexts)!=20: raise ValueError('expected exactly 20 source contexts')
    if len({x['cellId'] for x in ledger})!=240: raise ValueError('duplicate ledger cell')
    proposal_by_cell={x['cellId']:x for x in proposals}
    if len(proposal_by_cell)!=len(proposals): raise ValueError('duplicate proposal cell')
    decisions=collections.Counter(); seen=set(); changed=[]
    for item in ledger:
        key=(item['selectedPosition'],item['locale'])
        if key not in source_by_cell: raise ValueError(f'ledger cell not in input: {key}')
        if key in seen: raise ValueError(f'duplicate position/locale: {key}')
        seen.add(key)
        source,rowhash=source_by_cell[key]
        ctx=contexts.get(source['sourceKey'])
        if not ctx: raise ValueError('missing caller context')
        target=item.get('recommendedTarget',source['currentTarget'])
        if item['cellId']!=f"{source['sourceKey']}::{source['locale']}": raise ValueError('cellId mismatch')
        if item['sourceKey']!=source['sourceKey'] or item['locale']!=source['locale']: raise ValueError('source/locale mismatch')
        if item['exactHead']!=HEAD or item['exactTree']!=TREE: raise ValueError('row pin mismatch')
        if item['candidateFreeRowSha256']!=rowhash: raise ValueError(f'candidate row hash mismatch: {item["cellId"]}')
        if item['sourceText']!=source['sourceKey'] or item['sourceTextSha256']!=source['sourceKeySha256'] or sha(item['sourceText'].encode())!=source['sourceKeySha256']:
            raise ValueError(f'source text/hash mismatch: {item["cellId"]}')
        if item['currentTarget']!=source['currentTarget'] or item['currentTargetSha256']!=source['currentTargetSha256'] or sha(item['currentTarget'].encode())!=source['currentTargetSha256']:
            raise ValueError(f'current target/hash mismatch: {item["cellId"]}')
        if item['callerContextSha256']!=ctx['callerContextSha256'] or item['sourceContextSha256']!=source['sourceContextSha256']:
            raise ValueError(f'caller-context binding mismatch: {item["cellId"]}')
        if item['callerCount']!=source['callerCount'] or item['callerPaths']!=sorted({c['path'] for c in ctx['callers']}):
            raise ValueError(f'caller identity mismatch: {item["cellId"]}')
        if item['decision'] not in ('accept-current','correction','refinement','hold-hash-only'):
            raise ValueError(f'unknown decision: {item["decision"]}')
        if item['decision']=='accept-current' and 'recommendedTarget' in item: raise ValueError('accept-current row has recommendation')
        if item['decision'] in ('correction','refinement'):
            if 'recommendedTarget' not in item: raise ValueError('changed row lacks recommended target')
            if item.get('recommendedTargetSha256')!=sha(target.encode()): raise ValueError('recommended target hash mismatch')
            changed.append(item)
        elif item['decision']=='hold-hash-only':
            if 'recommendedTarget' in item or 'currentTarget' in item or 'sourceText' in item: raise ValueError('hash-only hold leaked text')
        if token_signature(source['sourceKey'])!=token_signature(target):
            raise ValueError(f'token signature changed: {item["cellId"]}')
        if source['sourceKey'].endswith(':') and (not target or target[-1] not in {':','：','﹕','∶'}):
            raise ValueError(f'colon continuation marker lost: {item["cellId"]}')
        if item['selectedPosition']==1644 and ('Pod' not in target):
            raise ValueError(f'Pod product term not preserved: {item["cellId"]}')
        decisions[item['decision']]+=1
    if len(seen)!=240: raise ValueError('ledger is missing cells')
    if set(proposal_by_cell)!={x['cellId'] for x in changed}: raise ValueError('proposal ledger coverage mismatch')
    for item in changed:
        proposal=proposal_by_cell[item['cellId']]
        for key in ('decision','recommendedTarget','recommendedTargetSha256','candidateFreeRowSha256','sourceTextSha256','currentTargetSha256','callerContextSha256','exactHead','exactTree'):
            if proposal.get(key)!=item.get(key): raise ValueError(f'proposal/ledger mismatch for {item["cellId"]}: {key}')
    bypos=collections.Counter(x['selectedPosition'] for x in ledger)
    bylocale=collections.Counter(x['locale'] for x in ledger)
    if set(bypos)!=set(POSITIONS) or any(n!=12 for n in bypos.values()): raise ValueError('position/locale coverage mismatch')
    if set(bylocale)!=set(LOCALES) or any(n!=20 for n in bylocale.values()): raise ValueError('locale coverage mismatch')
    if summary.get('cellCount')!=240 or summary.get('proposalCount')!=len(proposals): raise ValueError('summary counts mismatch')
    if summary.get('decisionCounts')!=dict(sorted(decisions.items())): raise ValueError('summary decision count mismatch')
    if manifest.get('ledgerSha256')!=sha((ROOT/'ledger.jsonl').read_bytes()) or manifest.get('proposalsSha256')!=sha((ROOT/'proposals.jsonl').read_bytes()):
        raise ValueError('manifest review artifact hash mismatch')
    for name in ('live-attestation-before.json','live-attestation-after.json'):
        if (ROOT/name).exists():
            a=readj(ROOT/name)
            if a.get('head')!=HEAD or a.get('tree')!=TREE or a.get('branchRefSha')!=HEAD or a.get('pullRefSha')!=HEAD or a.get('state')!='OPEN' or a.get('isDraft') is not True:
                raise ValueError(f'live PR attestation mismatch: {name}')
    repo_status='NOT_CHECKED'
    if args.repo:
        repo=pathlib.Path(args.repo)
        def git(*xs): return subprocess.check_output(['git','-C',str(repo),*xs],text=True).strip()
        if git('rev-parse','HEAD')!=HEAD or git('rev-parse','HEAD^{tree}')!=TREE or git('status','--porcelain'):
            raise ValueError('provided worktree pin/cleanliness mismatch')
        repo_status='PASS'
    print(json.dumps({'result':'PASS','cells':len(ledger),'proposals':len(proposals),'decisions':dict(sorted(decisions.items())),
      'candidateFreeInputFilesVerified':inp_count,'reviewFilesVerified':out_count,'callerBindings':'PASS','tokenSignatures':'PASS','repoPin':repo_status},sort_keys=True))

if __name__=='__main__':
    try: main()
    except Exception as e:
        print(json.dumps({'result':'FAIL','error':str(e)}),file=sys.stderr); raise
