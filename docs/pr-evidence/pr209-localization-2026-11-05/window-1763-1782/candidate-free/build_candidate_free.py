#!/usr/bin/env python3
"""Build the candidate-free W1763-W1782 review input at one exact PR head."""
from __future__ import annotations
import importlib.util, json, subprocess
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

R = Path(__file__).resolve().parent
TASK = R.parent
REPO = Path('/home/keith/Documents/code/.task-worktrees/localization-20261105/slskr-w1683')
PREV = Path('/home/keith/Documents/code/.task-worktrees/localization-20261105/slskr-w1683/docs/pr-evidence/pr209-localization-2026-11-05/window-1743-1762/candidate-free-input')
REPO_NAME = 'snapetech-org/slskR'; PR = 209
BRANCH = 'codex/slskr-l10n-audit-20261104-resync'
HEAD = '5191888071f54061a6012acdedfeb518a6cb3661'
TREE = 'd5728c24b54a06dda432afd2ef5f378206a6cb8f'
BASE = '1bbaec9fdc63a86de343e37e33bae70d44301a36'
START, END = 1763, 1782
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
      'baseRef':api['baseRef'],'baseSha':api['baseSha'],'remoteRefs':refs,
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
    if (manifest.get('head'),manifest.get('tree'),manifest.get('selectedPositions'),manifest.get('candidateFreeInputOnly'),manifest.get('proposedTranslationsIncluded')) != ('ccbc3dc721c1cbd225d4e512f4f0af4c80476620','075d1b72a2fd080404ebec19d354cb863638df21',[1743,1762],True,False):
        raise RuntimeError('previous candidate-free packet identity/scope mismatch')
    return manifest, sha((PREV/'source-queue.jsonl').read_bytes()), sha((PREV/'manifest.json').read_bytes()), sha((PREV/'SHA256SUMS.txt').read_bytes())


def main():
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
    if (prior_active_hold.get('holdId'),prior_active_hold.get('currentHead'),prior_active_hold.get('currentTree'),prior_active_hold.get('textIncluded')) != ('1719::id','ccbc3dc721c1cbd225d4e512f4f0af4c80476620','075d1b72a2fd080404ebec19d354cb863638df21',False):
        raise RuntimeError('prior active hold is not pinned hash-only to W1743 input head/tree')
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
    if hold_context.get('callerContextSha256')!=prior_active_hold.get('priorSourceContextSha256'):
        raise RuntimeError('active hold caller context changed since prior packet')
    active_hold={
      'holdId':'1719::id','position':hold_position,'locale':'id','decision':'preserved_active_hold',
      'previousWindow':'W1743-W1762','priorHead':prior_active_hold['currentHead'],'priorTree':prior_active_hold['currentTree'],
      'currentHead':HEAD,'currentTree':TREE,'sourceKeySha256':sha(hold_key),
      'catalogPath':pins['id']['path'],'catalogFileSha256':pins['id']['sha256'],'catalogGitBlob':pins['id']['gitBlob'],
      'currentCallerCount':hold_context['productionCallerCount'],'currentSourceContextSha256':hold_context['callerContextSha256'],
      'currentTargetSha256':held_hash,'priorCurrentTargetSha256':prior_active_hold['currentTargetSha256'],
      'targetHashUnchanged':True,'sourceContextUnchanged':True,'textIncluded':False,
      'priorCellRecordSha256':prior_active_hold['priorCellRecordSha256'],
      'priorPacketManifestSha256':prior_active_hold['priorPacketManifestSha256'],
      'priorPacketChecksumsSha256':prior_active_hold['priorPacketChecksumsSha256'],
      'rationale':'Reattested the active hold at the current exact head; source context and target hash match the immediately preceding sealed packet; target text remains hash-only.'
    }
    contexts,holds,scanned=h.contexts_for(REPO,selected,START,END)
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
    lineage={'window':'W1763-W1782','selectedPositions':list(range(START,END+1)),'previousWindow':'W1743-W1762',
      'previousWindowHead':prior_manifest['head'],'previousWindowTree':prior_manifest['tree'],
      'previousQueueSha256':prior_queue_sha,'previousManifestSha256':prior_manifest_sha,
      'previousChecksumListSha256':prior_sums_sha,'fullSourceQueueCount':len(queue),'fullSourceQueueSha256':sha(queue_bytes),
      'sourceLookupKeyOrderSha256':order_sha,'queueMatchesPreviousSealedQueue':True,
      'previousBoundaryPosition':START-1,'previousBoundarySourceKeySha256':sha(keys[START-2]),'activeHoldId':'1719::id','activeHoldTargetHashUnchanged':active_hold['targetHashUnchanged'],'activeHoldSourceContextUnchanged':active_hold['sourceContextUnchanged'],
      'nextBoundaryPosition':END+1,'nextBoundarySourceKeySha256':sha(keys[END]),
      'gapPositions':[],'overlapPositions':[],'positionsCoveredThrough':END}
    write_json(R/'source-order-lineage.json',lineage)
    write_json(R/'attestation-before.json',before)
    after=capture('after extraction')
    write_json(R/'attestation-after.json',after)
    if before['headSha'] != after['headSha'] or before['headTree'] != after['headTree'] or before['remoteRefs'] != after['remoteRefs']:
        raise RuntimeError('source/PR refs drifted during extraction')
    readme=f'''# slskR PR #209 W1763–W1782 candidate-free input

Pinned to open draft PR #209 at `{HEAD}` / tree `{TREE}`, branch `{BRANCH}`, base `main` at `{BASE}`. Before and after extraction, the local clone, branch ref, pull ref, PR head, and tree matched these pins. See `attestation-before.json` and `attestation-after.json`.

This packet covers sorted source positions {START}–{END}: 20 keys × 12 locales = 240 cells. The complete 5,441-key queue matches the prior sealed W1723–W1742 candidate-free queue by exact bytes; this window follows it with no gap or overlap.

Active hold continuity: `1719::id` is preserved as hash-only; target hash unchanged={active_hold['targetHashUnchanged']}, caller-context hash unchanged={active_hold['sourceContextUnchanged']}. See `active-hold-reattestation.jsonl`.

The exact quoted-literal scan covered {scanned} tracked production JavaScript/TypeScript files and found {caller_refs} caller references / {caller_occ} occurrences in {caller_files} caller files. Callerless source positions: {callerless_positions or 'none'}. **Every target for a callerless position is hash-only:** its string is omitted from `current-target-cells.jsonl`, its target SHA-256 is retained, and the position is recorded in `caller-resolution-holds.jsonl`. These rows are holds, not reviewable translation proposals.

For caller-backed cells, the packet records current target text, target hash, exact catalog path/file SHA/Git blob, placeholder/markup/numeric/protected-literal signatures, and a pinned caller-context SHA. Caller contexts contain source lines ±4 lines plus file byte count, file SHA-256, and Git blob. `localization-runtime-context.json` pins locale lookup and placeholder-formatting context to the same exact source tree. No review decisions or candidate proposals are included.

Offline integrity check: `python3 verify_candidate_free.py`. It checks the candidate-free input checksums, exact window coverage, catalog/source/caller pins, and hash-only active hold. It makes no network requests.
'''
    (R/'README.md').write_text(readme,encoding='utf-8')
    manifest={'artifact':'slskR PR #209 W1763-W1782 candidate-free exact-head input','repository':REPO_NAME,'pullRequest':PR,
      'head':HEAD,'tree':TREE,'headRef':BRANCH,'baseRef':'main','baseSha':BASE,'draft':True,
      'candidateFreeInputOnly':True,'proposedTranslationsIncluded':False,'selectedPositions':[START,END],
      'sourceCount':len(selected),'localeCount':len(LOCALES),'cellCount':len(cells),'catalogSourceCount':len(keys),
      'localeOrder':LOCALES,'sourceLookupKeyOrderSha256':order_sha,'sourceQueueCount':len(queue),'sourceQueueFileSha256':sha(queue_bytes),
      'callerReferenceCount':caller_refs,'callerOccurrenceCount':caller_occ,'callerFileCount':caller_files,
      'trackedProductionJsTsFilesScanned':scanned,'uniqueSelectedCallerFiles':caller_files,
      'callerResolutionHoldCount':len(holds),'callerResolutionHoldPositions':callerless_positions,
      'callerlessTargetTextsIncluded':False,'activeHoldReattestationCount':1,'activeHoldIds':['1719::id'],'activeHoldTargetHashUnchanged':active_hold['targetHashUnchanged'],'activeHoldSourceContextUnchanged':active_hold['sourceContextUnchanged'],'tokenMismatchCounts':dict(mismatch),
      'catalogFilesPinned':len(pins),'previousWindow':'W1743-W1762','previousQueueSha256':prior_queue_sha,
      'previousQueueMatchesLiveQueue':True,'historicalSourceOrdinalsClaimed':False,
      'localWorktree':str(REPO),'localWorktreeHead':HEAD,'localWorktreeTree':TREE,'localWorktreeBranch':BRANCH,
      'localWorktreeStatusClean':True,'beforeAfterRefsStable':True,
      'createdAtUtc':datetime.now(timezone.utc).isoformat(timespec='seconds'),'window':'W1763-W1782'}
    manifest['fileHashes']={p.name:{'sha256':sha(p.read_bytes()),'byteCount':p.stat().st_size} for p in sorted(R.iterdir()) if p.is_file() and p.name not in ('manifest.json','SHA256SUMS.txt')}
    write_json(R/'manifest.json',manifest)
    (R/'SHA256SUMS.txt').write_text(''.join(f'{sha(path.read_bytes())}  {path.name}\n' for path in sorted(R.iterdir()) if path.is_file() and path.name!='SHA256SUMS.txt'),encoding='utf-8')
    print(json.dumps({'result':'BUILT','head':HEAD,'tree':TREE,'selectedPositions':[START,END],'sourceCount':len(selected),
      'cells':len(cells),'callerReferences':caller_refs,'callerOccurrences':caller_occ,'callerFiles':caller_files,
      'callerlessPositions':callerless_positions,'scannedProductionFiles':scanned,'activeHoldId':'1719::id','activeHoldTargetHashUnchanged':active_hold['targetHashUnchanged'],'activeHoldSourceContextUnchanged':active_hold['sourceContextUnchanged'],'tokenMismatchCounts':dict(mismatch),
      'packet':str(R)},indent=2))

if __name__ == '__main__': main()
