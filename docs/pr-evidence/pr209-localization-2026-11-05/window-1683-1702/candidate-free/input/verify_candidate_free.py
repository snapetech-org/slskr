#!/usr/bin/env python3
"""Offline verifier for the sealed slskR PR #209 W1683-W1702 input."""
from __future__ import annotations
import argparse, collections, json, subprocess, sys
from pathlib import Path

PACKET=Path(__file__).resolve().parent
REPO_DEFAULT=Path('/home/keith/Documents/code/.task-worktrees/localization-20261105/slskr-w1683')
PREV_REL='docs/pr-evidence/pr209-localization-2026-11-05/window-1663-1682/candidate-free-input'
HEAD='f04b7f965aef79552d65d40a2eeb550e5e3b9cfa'; TREE='85fe880023e55e055660fd17599c291edd24a1c6'
BASE='1bbaec9fdc63a86de343e37e33bae70d44301a36'; BRANCH='codex/slskr-l10n-audit-20261104-resync'
START,END=1683,1702
sys.dont_write_bytecode=True
spec=__import__('importlib.util',fromlist=['spec_from_file_location']).spec_from_file_location('schema',PACKET/'candidate-free-schema-helper.py')
h=__import__('importlib.util',fromlist=['module_from_spec']).module_from_spec(spec); spec.loader.exec_module(h)


def fail(message): raise SystemExit('FAIL: '+message)
def run(repo,*args): return subprocess.check_output(['git','-C',str(repo),*args],text=True,stderr=subprocess.STDOUT).strip()
def jsonl(path): return [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines() if line.strip()]
def canon(value): return h.canon(value)
def sha(value): return h.sha(value)
def target_hash(value): return sha(value) if isinstance(value,str) else sha(canon(value))
def target_strings(value,path='$'):
    if isinstance(value,str): return [(path,value)]
    if isinstance(value,dict): return [item for key,child in value.items() for item in target_strings(child,path+'.'+str(key))]
    if isinstance(value,list): return [item for index,child in enumerate(value) for item in target_strings(child,path+f'[{index}]')]
    return []


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--repo',type=Path,default=REPO_DEFAULT); args=ap.parse_args()
    repo=args.repo.resolve(); manifest=json.loads((PACKET/'manifest.json').read_text(encoding='utf-8'))
    listed={}
    for line in (PACKET/'SHA256SUMS.txt').read_text(encoding='utf-8').splitlines():
        if line.strip():
            digest,name=line.split(None,1); name=name.lstrip('* ')
            if name in listed: fail('duplicate checksum '+name)
            listed[name]=digest
    actual={path.relative_to(PACKET).as_posix():sha(path.read_bytes()) for path in PACKET.rglob('*') if path.is_file() and path.name!='SHA256SUMS.txt'}
    if listed != actual: fail('checksum list does not match packet files')
    file_hashes={path.name:{'sha256':sha(path.read_bytes()),'byteCount':path.stat().st_size} for path in sorted(PACKET.iterdir()) if path.is_file() and path.name not in ('manifest.json','SHA256SUMS.txt')}
    if manifest.get('fileHashes') != file_hashes: fail('manifest file hashes do not match')
    if (manifest.get('head'),manifest.get('tree'),manifest.get('baseSha'),manifest.get('selectedPositions'),manifest.get('candidateFreeInputOnly'),manifest.get('proposedTranslationsIncluded')) != (HEAD,TREE,BASE,[START,END],True,False): fail('manifest exact pin or scope mismatch')
    if manifest.get('callerlessTargetTextsIncluded') is not False: fail('callerless target privacy flag mismatch')
    if run(repo,'rev-parse','HEAD') != HEAD or run(repo,'rev-parse','HEAD^{tree}') != TREE: fail('local source checkout exact commit/tree mismatch')
    if run(repo,'branch','--show-current') != BRANCH or run(repo,'status','--porcelain=v1'): fail('local source checkout branch/cleanliness mismatch')
    prev=repo/PREV_REL; prev_manifest=json.loads((prev/'manifest.json').read_text(encoding='utf-8'))
    prev_sums={}
    for line in (prev/'SHA256SUMS.txt').read_text(encoding='utf-8').splitlines():
        if line.strip():
            digest,name=line.split(None,1); prev_sums[name.lstrip('* ')]=digest
    prev_actual={path.relative_to(prev).as_posix():sha(path.read_bytes()) for path in prev.rglob('*') if path.is_file() and path.name!='SHA256SUMS.txt'}
    if prev_sums != prev_actual: fail('previous sealed candidate-free checksum mismatch')
    if sha((prev/'source-queue.jsonl').read_bytes()) != manifest['previousQueueSha256']: fail('previous queue pin mismatch')
    queue_rows=jsonl(PACKET/'source-queue.jsonl'); keys=[row['sourceKey'] for row in queue_rows]
    if len(keys)!=5441 or [row['position'] for row in queue_rows]!=list(range(1,5442)) or keys!=sorted(keys): fail('queue order/count mismatch')
    queue_raw=''.join(canon(row)+'\n' for row in queue_rows).encode('utf-8')
    if sha(queue_raw)!=manifest['sourceQueueFileSha256'] or queue_raw!=(prev/'source-queue.jsonl').read_bytes(): fail('queue bytes/hash continuity mismatch')
    locs=h.LOCALES; catalogs={}; pins=json.loads((PACKET/'catalog-file-pins.json').read_text(encoding='utf-8'))['localeCatalogs']
    for locale in locs:
        rel=f'web/src/lib/locales/ui-labels.{locale}.json'; raw=(repo/rel).read_bytes(); data=json.loads(raw); catalogs[locale]=data
        pin=pins[locale]
        if pin['path']!=rel or pin['sha256']!=sha(raw) or pin['gitBlob']!=run(repo,'rev-parse',f'HEAD:{rel}'): fail('catalog exact pin mismatch '+locale)
        if pin['orderedKeySha256']!=sha('\n'.join(data)+'\n') or pin['keyCount']!=len(data) or len(data)!=5441: fail('catalog key order/count '+locale)
    if any(list(catalogs[locale])!=list(catalogs[locs[0]]) for locale in locs[1:]): fail('catalog key order differs by locale')
    if keys!=sorted(catalogs[locs[0]]) or sha('\n'.join(keys)+'\n')!=manifest['sourceLookupKeyOrderSha256']: fail('catalog/source queue mismatch')
    selected=keys[START-1:END]
    if (PACKET/'selected-source-keys.txt').read_text(encoding='utf-8').splitlines()!=selected: fail('selected source key list mismatch')
    boundaries=jsonl(PACKET/'source-window-boundaries.jsonl')
    if [row['position'] for row in boundaries]!=list(range(START-1,END+2)) or [row['sourceKeySha256'] for row in boundaries]!=[sha(keys[pos-1]) for pos in range(START-1,END+2)]: fail('window boundary continuity mismatch')
    lineage=json.loads((PACKET/'source-order-lineage.json').read_text(encoding='utf-8'))
    if lineage.get('window')!='W1683-W1702' or lineage.get('selectedPositions')!=list(range(START,END+1)) or lineage.get('gapPositions')!=[] or lineage.get('overlapPositions')!=[] or lineage.get('queueMatchesPreviousSealedQueue') is not True: fail('source order lineage mismatch')
    expected_contexts,expected_holds,scanned=h.contexts_for(repo,selected,START,END)
    contexts=jsonl(PACKET/'source-contexts.jsonl')
    if contexts!=expected_contexts: fail('exact caller context scan mismatch')
    if jsonl(PACKET/'caller-resolution-holds.jsonl')!=expected_holds: fail('callerless hold list mismatch')
    if len(contexts)!=20 or scanned!=manifest['trackedProductionJsTsFilesScanned']: fail('caller context coverage mismatch')
    if sum(row['productionCallerCount'] for row in contexts)!=manifest['callerReferenceCount']: fail('caller reference count mismatch')
    if sum(row['callerOccurrenceCount'] for row in contexts)!=manifest['callerOccurrenceCount']: fail('caller occurrence count mismatch')
    if len({caller['path'] for row in contexts for caller in row['callers']})!=manifest['callerFileCount']: fail('caller file count mismatch')
    source_pin=json.loads((PACKET/'source-pin-reattestation.json').read_text(encoding='utf-8'))
    if source_pin.get('head')!=HEAD or source_pin.get('tree')!=TREE or source_pin.get('selectedSourceCount')!=20 or source_pin.get('callerlessSelectedPositions')!=[row['position'] for row in expected_holds]: fail('source pin reattestation mismatch')
    structures=jsonl(PACKET/'catalog-structure.jsonl')
    if structures!=[{'locale':locale,**pins[locale]} for locale in locs]: fail('catalog structure index mismatch')
    runtime=json.loads((PACKET/'localization-runtime-context.json').read_text(encoding='utf-8'))
    runtime_path=repo/runtime['pin']['path']
    if runtime['pin']['sha256']!=sha(runtime_path.read_bytes()) or runtime['pin']['gitBlob']!=run(repo,'rev-parse',f"HEAD:{runtime['pin']['path']}"): fail('runtime exact pin mismatch')
    cells=jsonl(PACKET/'current-target-cells.jsonl')
    if len(cells)!=240 or [(row['position'],row['locale']) for row in cells]!=[(pos,locale) for pos in range(START,END+1) for locale in locs]: fail('cell coverage/order mismatch')
    mismatch={key:0 for key in ('placeholderSequenceMismatchCount','markupMismatchCount','numericTokenMismatchCount','protectedLiteralMismatchCount')}
    context_by_pos={row['position']:row for row in contexts}
    for cell in cells:
        pos,locale=cell['position'],cell['locale']; key=keys[pos-1]; ctx=context_by_pos[pos]; value=catalogs[locale][key]
        if cell['sourceKey']!=key or cell['sourceKeySha256']!=sha(key): fail('cell source pin mismatch')
        if cell['sourceContextSha256']!=ctx['callerContextSha256'] or cell['callerCount']!=ctx['productionCallerCount']: fail('cell caller pin mismatch')
        if cell['catalogFileSha256']!=pins[locale]['sha256'] or cell['catalogGitBlob']!=pins[locale]['gitBlob']: fail('cell catalog pin mismatch')
        if cell['currentTargetSha256']!=target_hash(value) or cell['currentTargetType']!=type(value).__name__: fail('cell target hash/type mismatch')
        included=ctx['productionCallerCount']>0
        if cell['targetTextIncluded'] is not included: fail('target text inclusion flag mismatch')
        if included:
            if cell.get('currentTarget')!=value: fail('candidate-free target does not match catalog')
            source_tokens=h.tokens(key); variants=[]
            for path,target in target_strings(value):
                tokens=h.tokens(target); missing=[token for token in source_tokens[3] if token not in tokens[3]]
                variant={'jsonPath':path,'targetStringSha256':sha(target),'targetPlaceholders':tokens[0],
                  'placeholderSequenceMatches':source_tokens[0]==tokens[0],'targetMarkupTags':tokens[1],
                  'placeholderMultisetMatches':collections.Counter(source_tokens[0])==collections.Counter(tokens[0]),
                  'markupMatches':source_tokens[1]==tokens[1],'targetNumericTokens':tokens[2],
                  'numericTokensMatch':source_tokens[2]==tokens[2],'targetProtectedLiterals':tokens[3],
                  'protectedLiteralMismatchTokens':missing,'protectedLiteralsMatch':not missing}
                variants.append(variant)
                mismatch['placeholderSequenceMismatchCount']+=not variant['placeholderSequenceMatches']
                mismatch['markupMismatchCount']+=not variant['markupMatches']
                mismatch['numericTokenMismatchCount']+=not variant['numericTokensMatch']
                mismatch['protectedLiteralMismatchCount']+=bool(missing)
            if cell.get('targetTokenVariants')!=variants: fail('candidate token signatures mismatch')
        else:
            if 'currentTarget' in cell or 'targetTokenVariants' in cell: fail('callerless target text/signatures must be omitted')
    if dict(mismatch)!=manifest['tokenMismatchCounts']: fail('token alert summary mismatch')
    for name in ('attestation-before.json','attestation-after.json'):
        att=json.loads((PACKET/name).read_text(encoding='utf-8'))
        if (att.get('headSha'),att.get('headTree'),att.get('baseSha'),att.get('state'),att.get('draft'),att.get('headRef'))!=(HEAD,TREE,BASE,'OPEN',True,BRANCH): fail('saved PR exact pin '+name)
        if att.get('remoteRefs',{}).get(f'refs/heads/{BRANCH}')!=HEAD or att.get('remoteRefs',{}).get('refs/pull/209/head')!=HEAD: fail('saved remote refs '+name)
        if not att.get('localWorktreeClean'): fail('saved worktree dirty '+name)
    print(json.dumps({'result':'PASS','head':HEAD,'tree':TREE,'positions':[START,END],'cells':len(cells),
      'sourceCount':20,'localeCount':12,'callerReferences':manifest['callerReferenceCount'],
      'callerOccurrences':manifest['callerOccurrenceCount'],'callerFiles':manifest['callerFileCount'],
      'callerlessPositions':manifest['callerResolutionHoldPositions'],'tokenMismatchCounts':dict(mismatch),
      'checksumFiles':len(listed),'priorQueueContinuity':'PASS'},indent=2))

if __name__=='__main__': main()
