#!/usr/bin/env python3
"""Build the candidate-free W1783-W1802 input at one exact PR head."""
from __future__ import annotations
import argparse, importlib.util, json, subprocess
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

R = Path(__file__).resolve().parent
TASK = R.parent
REPO: Path
PREV: Path
REPO_NAME = 'snapetech-org/slskR'; PR = 209
BRANCH = 'codex/slskr-l10n-audit-20261104-resync'
HEAD = '0264a4fcaa944fee61049efec0cf3c451416c8b9'
TREE = '895e57c178d959a23aceddead27623f2dd854ba0'
BASE = '1bbaec9fdc63a86de343e37e33bae70d44301a36'
START, END = 1783, 1802
LOCALES = ['es','zh-Hans','hi','de','ja','fr','pt-BR','ar','ko','zh-Hant','vi','id']
sys_path = str(R)
import sys
sys.dont_write_bytecode = True
spec = importlib.util.spec_from_file_location('candidate_free_schema', R / 'candidate-free-schema-helper.py')
h = importlib.util.module_from_spec(spec); spec.loader.exec_module(h)


def sha(value): return h.sha(value)
def canonical(value): return h.canon(value)
def write_json(path, value): path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
def write_jsonl(path, rows): path.write_text(''.join(canonical(row) + '\n' for row in rows), encoding='utf-8')


def run(args, cwd=None): return subprocess.check_output(args, cwd=cwd, text=True, stderr=subprocess.STDOUT).strip()


def capture(label):
    api = json.loads(run(['gh','api',f'repos/{REPO_NAME}/pulls/{PR}','--jq',
        '{number:.number,state:.state,draft:.draft,headRef:.head.ref,headSha:.head.sha,baseRef:.base.ref,baseSha:.base.sha,url:.html_url}']))
    refs_raw = run(['git','ls-remote',f'https://github.com/{REPO_NAME}.git',
        f'refs/heads/{BRANCH}',f'refs/pull/{PR}/head','refs/heads/main'])
    refs = {}
    for line in refs_raw.splitlines():
        digest, name = line.split('\t'); refs[name] = digest
    commit = json.loads(run(['gh','api',f'repos/{REPO_NAME}/commits/{HEAD}','--jq','{sha:.sha,tree:.commit.tree.sha}']))
    local_head = run(['git','rev-parse','HEAD'],REPO)
    local_tree = run(['git','rev-parse','HEAD^{tree}'],REPO)
    clean = run(['git','status','--porcelain=v1'],REPO) == ''
    branch = run(['git','branch','--show-current'],REPO)
    snapshot = {
      'capturedAtUtc':datetime.now(timezone.utc).isoformat(timespec='seconds'), 'label':label,
      'repository':REPO_NAME,'pullRequest':PR,'state':api['state'].upper(),'draft':api['draft'],'url':api['url'],
      'headRef':api['headRef'],'headSha':api['headSha'],'headTree':commit['tree'],
      'baseRef':api['baseRef'],'baseSha':api['baseSha'],'remoteRefs':refs,'remoteMainMatchesPrBaseSha':refs.get('refs/heads/main')==api['baseSha'],
      'localBranch':branch,'localHead':local_head,'localTree':local_tree,'localWorktreeClean':clean,
      'deploymentActionsIssuedByReview':0,
    }
    expected_refs = {f'refs/heads/{BRANCH}':HEAD,f'refs/pull/{PR}/head':HEAD}
    if (api['number'],api['state'],api['draft'],api['headRef'],api['headSha'],api['baseRef'],api['baseSha']) != (PR,'open',True,BRANCH,HEAD,'main',BASE):
        raise RuntimeError(f'{label}: live PR state/ref/base drift: {api}')
    if commit != {'sha':HEAD,'tree':TREE} or local_head != HEAD or local_tree != TREE or branch != BRANCH or not clean:
        raise RuntimeError(f'{label}: source clone pin/cleanliness mismatch')
    if any(refs.get(name) != digest for name,digest in expected_refs.items()):
        raise RuntimeError(f'{label}: remote branch or pull ref drift')
    return snapshot


def verify_prior_packet():
    manifest=json.loads((PREV/'manifest.json').read_text(encoding='utf-8'))
    sums={}
    for line in (PREV/'SHA256SUMS.txt').read_text(encoding='utf-8').splitlines():
        if line.strip():
            digest,name=line.split(None,1); sums[name.lstrip('* ')]=digest
    actual={p.relative_to(PREV).as_posix():sha(p.read_bytes()) for p in PREV.rglob('*') if p.is_file() and p.name!='SHA256SUMS.txt'}
    if sums != actual: raise RuntimeError('previous sealed candidate-free packet checksum mismatch')
    if (manifest.get('head'),manifest.get('tree'),manifest.get('selectedPositions'),manifest.get('candidateFreeInputOnly'),manifest.get('proposedTranslationsIncluded')) != ('5191888071f54061a6012acdedfeb518a6cb3661','d5728c24b54a06dda432afd2ef5f378206a6cb8f',[1763,1782],True,False):
        raise RuntimeError('previous candidate-free packet identity/scope mismatch')
    return manifest, sha((PREV/'source-queue.jsonl').read_bytes()), sha((PREV/'manifest.json').read_bytes()), sha((PREV/'SHA256SUMS.txt').read_bytes())


def main():
    global REPO, PREV
    parser=argparse.ArgumentParser(description='Build candidate-free evidence from an exact-head slskR worktree.')
    parser.add_argument('--repo',type=Path,required=True,help='clean worktree pinned to the input PR head')
    parser.add_argument('--previous',type=Path,default=R.parent.parent/'window-1763-1782/candidate-free',help='sealed preceding candidate-free packet')
    args=parser.parse_args(); REPO=args.repo.resolve(); PREV=args.previous.resolve()
    if R.resolve() != Path(__file__).resolve().parent: raise RuntimeError('unexpected packet path')
    before=capture('before extraction')
    prior_manifest,prior_queue_sha,prior_manifest_sha,prior_sums_sha=verify_prior_packet()
    catalogs={}; pins={}; key_orders=[]
    for locale in LOCALES:
        relative=f'web/src/lib/locales/ui-labels.{locale}.json'
        raw=(REPO/relative).read_bytes(); data=json.loads(raw)
        if not isinstance(data,dict) or not all(isinstance(key,str) for key in data):
            raise RuntimeError('locale catalog must map string keys to JSON values: '+locale)
        catalogs[locale]=data; key_orders.append(list(data))
        pins[locale]={'path':relative,'sha256':sha(raw),'gitBlob':run(['git','rev-parse',f'HEAD:{relative}'],REPO),
          'orderedKeySha256':sha('\n'.join(data)+'\n'),'keyCount':len(data)}
    if any(keys != key_orders[0] for keys in key_orders[1:]): raise RuntimeError('catalog key order differs across locales')
    keys=sorted(key_orders[0]); order_sha=sha('\n'.join(keys)+'\n')
    if len(keys) != 5441: raise RuntimeError('source key count drift: '+str(len(keys)))
    queue=[{'position':position,'sourceKey':key,'sourceKeySha256':sha(key),'historicalSourceOrdinal':None} for position,key in enumerate(keys,1)]
    queue_bytes=''.join(canonical(row)+'\n' for row in queue).encode('utf-8')
    if queue_bytes != (PREV/'source-queue.jsonl').read_bytes(): raise RuntimeError('full sorted source queue does not match previous sealed packet')
    selected=keys[START-1:END]
    # Carry forward the exact-head active-hold attestation from the immediately previous candidate-free packet.
    # The hold's source and target strings are never read into this review packet.
    active_rows=[json.loads(line) for line in (PREV/'active-hold-reattestation.jsonl').read_text(encoding='utf-8').splitlines() if line.strip()]
    if len(active_rows)!=1: raise RuntimeError('expected exactly one prior active-hold attestation')
    prior_active_hold=active_rows[0]
    if (prior_active_hold.get('holdId'),prior_active_hold.get('currentHead'),prior_active_hold.get('currentTree'),prior_active_hold.get('textIncluded')) != ('1719::id','5191888071f54061a6012acdedfeb518a6cb3661','d5728c24b54a06dda432afd2ef5f378206a6cb8f',False):
        raise RuntimeError('prior active hold is not pinned hash-only to W1763 input head/tree')
    if prior_active_hold.get('targetHashUnchanged') is not True or prior_active_hold.get('sourceContextUnchanged') is not True:
        raise RuntimeError('prior active hold continuity is not confirmed')
    hold_position=1719
    hold_key=keys[hold_position-1]
    hold_contexts,_,_=h.contexts_for(REPO,[hold_key],hold_position,hold_position)
    if len(hold_contexts)!=1:
        raise RuntimeError('could not reattest the active hold source context')
    hold_context=hold_contexts[0]
    held_value=catalogs['id'][hold_key]
    held_hash=sha(held_value) if isinstance(held_value,str) else sha(canonical(held_value))
    if held_hash!=prior_active_hold.get('currentTargetSha256'):
        raise RuntimeError('active hold target hash changed since prior packet')
    if hold_context.get('callerContextSha256')!=prior_active_hold.get('currentSourceContextSha256'):
        raise RuntimeError('active hold caller context changed since prior packet')
    active_hold={
      'holdId':'1719::id','position':hold_position,'locale':'id','decision':'preserved_active_hold',
      'previousWindow':'W1763-W1782','priorHead':prior_active_hold['currentHead'],'priorTree':prior_active_hold['currentTree'],
      'currentHead':HEAD,'currentTree':TREE,'sourceKeySha256':sha(hold_key),
      'catalogPath':pins['id']['path'],'catalogFileSha256':pins['id']['sha256'],'catalogGitBlob':pins['id']['gitBlob'],
      'currentCallerCount':hold_context['productionCallerCount'],'priorSourceContextSha256':prior_active_hold['currentSourceContextSha256'],'currentSourceContextSha256':hold_context['callerContextSha256'],
      'currentTargetSha256':held_hash,'priorCurrentTargetSha256':prior_active_hold['currentTargetSha256'],
      'targetHashUnchanged':True,'sourceContextUnchanged':True,'textIncluded':False,
      'priorCellRecordSha256':prior_active_hold['priorCellRecordSha256'],
      'priorPacketManifestSha256':prior_active_hold['priorPacketManifestSha256'],
      'priorPacketChecksumsSha256':prior_active_hold['priorPacketChecksumsSha256'],
      'rationale':'Reattested the active hold at the current exact head; source context and target hash match the immediately preceding sealed packet; target text remains hash-only.'
    }
    contexts,holds,scanned=h.contexts_for(REPO,selected,START,END)
    # Reattest the immediately preceding 240 product target readbacks at this exact head.
    # Store only hashes and counts in this lineage file; target strings stay in their sealed predecessor packet.
    prev_start,prev_end=1763,1782
    prior_cells=[json.loads(line) for line in (PREV/'current-target-cells.jsonl').read_text(encoding='utf-8').splitlines() if line.strip()]
    prior_contexts=[json.loads(line) for line in (PREV/'source-contexts.jsonl').read_text(encoding='utf-8').splitlines() if line.strip()]
    if len(prior_cells)!=240 or len(prior_contexts)!=20:
        raise RuntimeError('previous W1763-W1782 packet does not contain the expected 240 readbacks / 20 source rows')
    prior_keys=[row['sourceKey'] for row in sorted(prior_contexts,key=lambda item:item['position'])]
    prior_ctx_now,prior_holds_now,prior_scanned=h.contexts_for(REPO,prior_keys,prev_start,prev_end)
    prior_ctx_by={row['position']:row for row in prior_ctx_now}
    prior_ctx_old_by={row['position']:row for row in prior_contexts}
    prior_cell_by={(row['position'],row['locale']):row for row in prior_cells}
    if len(prior_cell_by)!=240:
        raise RuntimeError('previous readback packet has duplicate or missing position/locale cells')
    prior_readbacks=[]
    prior_target_unchanged=prior_target_changed=prior_context_unchanged=prior_context_changed=0
    for prior_position in range(prev_start,prev_end+1):
        prior_key=prior_keys[prior_position-prev_start]
        old_ctx=prior_ctx_old_by[prior_position]; now_ctx=prior_ctx_by[prior_position]
        if old_ctx['sourceKey']!=prior_key or now_ctx['sourceKey']!=prior_key:
            raise RuntimeError('previous-window source key/order changed during readback reattestation')
        for prior_locale in LOCALES:
            old_cell=prior_cell_by[(prior_position,prior_locale)]
            if old_cell['sourceKeySha256']!=sha(prior_key) or old_cell['sourceContextSha256']!=old_ctx['callerContextSha256']:
                raise RuntimeError('previous readback source/context pins do not match its sealed source rows')
            if old_cell['targetTextIncluded']:
                if not isinstance(old_cell.get('currentTarget'),str) or sha(old_cell['currentTarget'])!=old_cell['currentTargetSha256']:
                    raise RuntimeError('previous target readback does not match its own target hash')
            elif 'currentTarget' in old_cell or old_cell.get('currentTargetType')!='str':
                raise RuntimeError('previous callerless readback is not hash-only')
            live_value=catalogs[prior_locale][prior_key]
            live_hash=sha(live_value) if isinstance(live_value,str) else sha(canonical(live_value))
            live_target_type=type(live_value).__name__
            prior_target_same=live_hash==old_cell['currentTargetSha256']
            prior_context_same=now_ctx['callerContextSha256']==old_ctx['callerContextSha256']
            prior_target_unchanged += prior_target_same
            prior_target_changed += not prior_target_same
            prior_context_unchanged += prior_context_same
            prior_context_changed += not prior_context_same
            prior_readbacks.append({
              'position':prior_position,'locale':prior_locale,'sourceKeySha256':sha(prior_key),
              'priorCallerCount':old_ctx['productionCallerCount'],'currentCallerCount':now_ctx['productionCallerCount'],
              'priorCallerContextSha256':old_ctx['callerContextSha256'],'currentCallerContextSha256':now_ctx['callerContextSha256'],
              'callerContextUnchanged':prior_context_same,'priorTargetSha256':old_cell['currentTargetSha256'],
              'currentTargetSha256':live_hash,'targetType':live_target_type,'targetHashUnchanged':prior_target_same,
              'priorCatalogFileSha256':old_cell['catalogFileSha256'],'currentCatalogFileSha256':pins[prior_locale]['sha256'],
              'targetTextIncluded':False
            })
    context_by_position={row['position']:row for row in contexts}
    runtime=h.runtime_context(REPO)
    boundaries=[{'position':position,'boundary':not START<=position<=END,'sourceKeySha256':sha(keys[position-1])} for position in range(START-1,END+2)]
    cells=[]; mismatch=Counter(); caller_refs=sum(row['productionCallerCount'] for row in contexts)
    caller_occ=sum(row['callerOccurrenceCount'] for row in contexts); caller_files=len({c['path'] for row in contexts for c in row['callers']})
    callerless_positions=[row['position'] for row in holds]
    def target_strings(value, path='$'):
        if isinstance(value,str): return [(path,value)]
        if isinstance(value,dict):
            return [item for key,child in value.items() for item in target_strings(child,path+'.'+str(key))]
        if isinstance(value,list):
            return [item for index,child in enumerate(value) for item in target_strings(child,path+f'[{index}]')]
        return []
    for position,key in zip(range(START,END+1),selected):
        ctx=context_by_position[position]; source_tokens=h.tokens(key)
        for locale in LOCALES:
            target=catalogs[locale][key]
            target_hash=sha(target) if isinstance(target,str) else sha(canonical(target))
            cell={'position':position,'locale':locale,'sourceKey':key,'sourceKeySha256':sha(key),
              'sourceContextSha256':ctx['callerContextSha256'],'callerCount':ctx['productionCallerCount'],
              'catalogPath':pins[locale]['path'],'catalogFileSha256':pins[locale]['sha256'],'catalogGitBlob':pins[locale]['gitBlob'],
              'currentTargetSha256':target_hash,'currentTargetType':type(target).__name__,
              'targetTextIncluded':ctx['productionCallerCount']>0}
            if ctx['productionCallerCount']>0:
                cell['currentTarget']=target
                variants=[]
                for json_path,target_text in target_strings(target):
                    target_tokens=h.tokens(target_text)
                    missing=[token for token in source_tokens[3] if token not in target_tokens[3]]
                    variant={'jsonPath':json_path,'targetStringSha256':sha(target_text),
                      'targetPlaceholders':target_tokens[0],'placeholderSequenceMatches':source_tokens[0]==target_tokens[0],
                      'placeholderMultisetMatches':Counter(source_tokens[0])==Counter(target_tokens[0]),
                      'targetMarkupTags':target_tokens[1],'markupMatches':source_tokens[1]==target_tokens[1],
                      'targetNumericTokens':target_tokens[2],'numericTokensMatch':source_tokens[2]==target_tokens[2],
                      'targetProtectedLiterals':target_tokens[3],'protectedLiteralMismatchTokens':missing,
                      'protectedLiteralsMatch':not missing}
                    variants.append(variant)
                    mismatch['placeholderSequenceMismatchCount'] += not variant['placeholderSequenceMatches']
                    mismatch['markupMismatchCount'] += not variant['markupMatches']
                    mismatch['numericTokenMismatchCount'] += not variant['numericTokensMatch']
                    mismatch['protectedLiteralMismatchCount'] += bool(missing)
                cell.update({'sourcePlaceholders':source_tokens[0],'sourceMarkupTags':source_tokens[1],
                  'sourceNumericTokens':source_tokens[2],'sourceProtectedLiterals':source_tokens[3],
                  'targetTokenVariants':variants})
            else:
                cell.update({'targetTextDisposition':'hash-only callerless hold'})
            cells.append(cell)
    write_jsonl(R/'source-queue.jsonl',queue)
    write_jsonl(R/'source-window-boundaries.jsonl',boundaries)
    (R/'selected-source-keys.txt').write_text(''.join(key+'\n' for key in selected),encoding='utf-8')
    write_jsonl(R/'source-contexts.jsonl',contexts)
    write_jsonl(R/'caller-resolution-holds.jsonl',holds)
    write_jsonl(R/'active-hold-reattestation.jsonl',[active_hold])
    write_jsonl(R/'current-target-cells.jsonl',cells)
    write_jsonl(R/'previous-window-readback-reattestation-hash-only.jsonl',prior_readbacks)
    write_json(R/'catalog-file-pins.json',{'head':HEAD,'tree':TREE,'sourceLookupKeySetCount':len(keys),'sourceLookupKeyOrderSha256':order_sha,'localeCatalogs':pins})
    write_jsonl(R/'catalog-structure.jsonl',[{'locale':locale,**pins[locale]} for locale in LOCALES])
    write_json(R/'localization-runtime-context.json',runtime)
    source_pin={'repository':REPO_NAME,'pullRequest':PR,'head':HEAD,'tree':TREE,'selectedSourceCount':len(selected),
      'selectedCallerReferenceCount':caller_refs,'selectedCallerOccurrenceCount':caller_occ,'callerlessSelectedPositions':callerless_positions,
      'trackedProductionJsTsFilesScanned':scanned,'uniqueSelectedCallerFiles':caller_files,
      'catalogPaths':{locale:pins[locale]['path'] for locale in LOCALES},'runtimePath':runtime['path'],
      'runtimeFileSha256':runtime['pin']['sha256'],'runtimeGitBlob':runtime['pin']['gitBlob'],
      'sourceLookupKeyCount':len(keys),'sourceLookupKeyOrderSha256':order_sha}
    write_json(R/'source-pin-reattestation.json',source_pin)
    lineage={'window':'W1783-W1802','selectedPositions':list(range(START,END+1)),'previousWindow':'W1763-W1782',
      'previousWindowHead':prior_manifest['head'],'previousWindowTree':prior_manifest['tree'],
      'previousQueueSha256':prior_queue_sha,'previousManifestSha256':prior_manifest_sha,
      'previousChecksumListSha256':prior_sums_sha,'fullSourceQueueCount':len(queue),'fullSourceQueueSha256':sha(queue_bytes),
      'sourceLookupKeyOrderSha256':order_sha,'queueMatchesPreviousSealedQueue':True,
      'previousBoundaryPosition':START-1,'previousBoundarySourceKeySha256':sha(keys[START-2]),'activeHoldId':'1719::id','activeHoldTargetHashUnchanged':active_hold['targetHashUnchanged'],'activeHoldSourceContextUnchanged':active_hold['sourceContextUnchanged'],
      'nextBoundaryPosition':END+1,'nextBoundarySourceKeySha256':sha(keys[END]),
      'gapPositions':[],'overlapPositions':[],'positionsCoveredThrough':END,
      'previousWindowReadbackCount':len(prior_readbacks),'previousWindowTargetHashUnchangedCount':prior_target_unchanged,
      'previousWindowTargetHashChangedCount':prior_target_changed,'previousWindowCallerContextUnchangedCount':prior_context_unchanged,
      'previousWindowCallerContextChangedCount':prior_context_changed,'previousWindowReadbackFile':'previous-window-readback-reattestation-hash-only.jsonl'}
    write_json(R/'source-order-lineage.json',lineage)
    write_json(R/'attestation-before.json',before)
    after=capture('after extraction')
    write_json(R/'attestation-after.json',after)
    if before['headSha'] != after['headSha'] or before['headTree'] != after['headTree'] or before['remoteRefs'] != after['remoteRefs']:
        raise RuntimeError('source/PR refs drifted during extraction')
    readme=f'''# slskR PR #209 W1783–W1802 candidate-free input

Pinned to open draft PR #209 at `{HEAD}` / tree `{TREE}`, branch `{BRANCH}`, base `main` at `{BASE}`. Before and after extraction, the local clone, branch ref, pull ref, PR head, and tree matched these pins. The live remote main SHA is captured separately because it differs from the PR API base SHA; this does not alter the pinned PR head or its reported base. See `attestation-before.json` and `attestation-after.json`.

This packet covers sorted source positions {START}–{END}: 20 keys × 12 locales = 240 cells. The complete 5,441-key source queue matches the prior sealed W1763–W1782 candidate-free queue by exact bytes; this window follows it with no gap or overlap.

Active hold continuity: `1719::id` is preserved as hash-only; target hash unchanged={active_hold['targetHashUnchanged']}, caller-context hash unchanged={active_hold['sourceContextUnchanged']}. See `active-hold-reattestation.jsonl`.

The exact quoted-literal scan covered {scanned} tracked production JavaScript/TypeScript files and found {caller_refs} caller references / {caller_occ} occurrences in {caller_files} caller files. Callerless source positions: {callerless_positions or 'none'}. **Every target for a callerless position is hash-only:** its string is omitted from `current-target-cells.jsonl`, its target SHA-256 is retained, and the position is recorded in `caller-resolution-holds.jsonl`. These rows are holds, not reviewable translation proposals.

The prior W1763–W1782 packet’s 240 target readbacks are reattested at this head by hash only in previous-window-readback-reattestation-hash-only.jsonl; no prior or current target strings are copied into that lineage file. For caller-backed cells in this window, the packet records current target text, target hash, exact catalog path/file SHA/Git blob, placeholder/markup/numeric/protected-literal signatures, and a pinned caller-context SHA. Caller contexts contain source lines ±4 lines plus file byte count, file SHA-256, and Git blob. `localization-runtime-context.json` pins locale lookup and placeholder-formatting context to the same exact source tree. No review decisions or candidate proposals are included.

Offline integrity check: `python3 verify_candidate_free.py`. It checks the candidate-free input checksums, exact window coverage, catalog/source/caller pins, and hash-only active hold. It makes no network requests.
'''
    (R/'README.md').write_text(readme,encoding='utf-8')
    manifest={'artifact':'slskR PR #209 W1783-W1802 candidate-free exact-head input','repository':REPO_NAME,'pullRequest':PR,
      'head':HEAD,'tree':TREE,'headRef':BRANCH,'baseRef':'main','baseSha':BASE,'draft':True,
      'candidateFreeInputOnly':True,'proposedTranslationsIncluded':False,'selectedPositions':[START,END],
      'sourceCount':len(selected),'localeCount':len(LOCALES),'cellCount':len(cells),'catalogSourceCount':len(keys),
      'localeOrder':LOCALES,'sourceLookupKeyOrderSha256':order_sha,'sourceQueueCount':len(queue),'sourceQueueFileSha256':sha(queue_bytes),
      'callerReferenceCount':caller_refs,'callerOccurrenceCount':caller_occ,'callerFileCount':caller_files,
      'trackedProductionJsTsFilesScanned':scanned,'uniqueSelectedCallerFiles':caller_files,
      'callerResolutionHoldCount':len(holds),'callerResolutionHoldPositions':callerless_positions,
      'callerlessTargetTextsIncluded':False,'activeHoldReattestationCount':1,'activeHoldIds':['1719::id'],'activeHoldTargetHashUnchanged':active_hold['targetHashUnchanged'],'activeHoldSourceContextUnchanged':active_hold['sourceContextUnchanged'],'tokenMismatchCounts':dict(mismatch),
      'catalogFilesPinned':len(pins),'previousWindow':'W1763-W1782','previousQueueSha256':prior_queue_sha,
      'previousQueueMatchesLiveQueue':True,'historicalSourceOrdinalsClaimed':False,
      'localWorktreeHead':HEAD,'localWorktreeTree':TREE,'localWorktreeBranch':BRANCH,
      'localWorktreeStatusClean':True,'beforeAfterRefsStable':True,
      'previousWindowReadbackCount':len(prior_readbacks),'previousWindowTargetHashUnchangedCount':prior_target_unchanged,
      'previousWindowTargetHashChangedCount':prior_target_changed,'previousWindowCallerContextUnchangedCount':prior_context_unchanged,
      'previousWindowCallerContextChangedCount':prior_context_changed,'previousWindowReadbackTextsIncluded':False,
      'createdAtUtc':datetime.now(timezone.utc).isoformat(timespec='seconds'),'window':'W1783-W1802'}
    manifest['fileHashes']={p.name:{'sha256':sha(p.read_bytes()),'byteCount':p.stat().st_size} for p in sorted(R.iterdir()) if p.is_file() and p.name not in ('manifest.json','SHA256SUMS.txt')}
    write_json(R/'manifest.json',manifest)
    (R/'SHA256SUMS.txt').write_text(''.join(f'{sha(path.read_bytes())}  {path.name}\n' for path in sorted(R.iterdir()) if path.is_file() and path.name!='SHA256SUMS.txt'),encoding='utf-8')
    print(json.dumps({'result':'BUILT','head':HEAD,'tree':TREE,'selectedPositions':[START,END],'sourceCount':len(selected),
      'cells':len(cells),'callerReferences':caller_refs,'callerOccurrences':caller_occ,'callerFiles':caller_files,
      'callerlessPositions':callerless_positions,'scannedProductionFiles':scanned,'activeHoldId':'1719::id','activeHoldTargetHashUnchanged':active_hold['targetHashUnchanged'],'activeHoldSourceContextUnchanged':active_hold['sourceContextUnchanged'],'tokenMismatchCounts':dict(mismatch),
      'packet':str(R)},indent=2))

if __name__ == '__main__': main()
