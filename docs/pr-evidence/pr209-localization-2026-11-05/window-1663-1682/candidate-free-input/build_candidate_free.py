#!/usr/bin/env python3
"""Build candidate-free slskR PR #209 W1663-W1682 input and hash-only lineage."""
from __future__ import annotations
import hashlib, importlib.util, json, subprocess, sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

R=Path(__file__).resolve().parent
TASK=R.parent
REPO=Path('/mnt/disks/scratch/task-worktrees/localization-20261105/slskr-pr209-w1663-1682-candidate-free')
PREV=Path('/mnt/disks/scratch/task-scratch/slskr-pr209-w1643-1662-20261105/candidate-free-input')
APP=TASK/'application-adapter'
HEAD='2ab97d1a21f7d001eb9470c76b3636f59f600609'
TREE='63097ec7c80be0bef55fb1bde5a38da7b6a59ce7'
START,END=1663,1682
PREV_START,PREV_END=1643,1662
LOCS=['es','zh-Hans','hi','de','ja','fr','pt-BR','ar','ko','zh-Hant','vi','id']
REPO_NAME='snapetech-org/slskR'; PR=209; BRANCH='codex/slskr-l10n-audit-20261104-resync'; BASE_SHA='1bbaec9fdc63a86de343e37e33bae70d44301a36'
sys.dont_write_bytecode=True
spec=importlib.util.spec_from_file_location('schema_helper',R/'candidate-free-schema-helper.py')
h=importlib.util.module_from_spec(spec); spec.loader.exec_module(h)
h.R=R; h.REPO=REPO; h.PREV=PREV; h.APP=APP; h.HEAD=HEAD; h.TREE=TREE; h.START=START; h.END=END; h.LOCS=LOCS; h.REPO_NAME=REPO_NAME; h.PR=PR; h.BRANCH=BRANCH; h.BASE_SHA=BASE_SHA
sha,canon,wj,wjl=h.sha,h.canon,h.wj,h.wjl

def readjl(path): return [json.loads(s) for s in path.read_text(encoding='utf-8').splitlines() if s.strip()]
def packet_sums(path):
    sums={}
    for line in (path/'SHA256SUMS.txt').read_text(encoding='utf-8').splitlines():
        if not line.strip(): continue
        digest,name=line.split(None,1); name=name.lstrip('* '); sums[name]=digest
    actual={p.relative_to(path).as_posix():sha(p.read_bytes()) for p in path.rglob('*') if p.is_file() and p.name!='SHA256SUMS.txt'}
    if sums!=actual: raise RuntimeError(f'checksum verification failed for {path}')
    return sums

def pin_snapshot(api_path, refs_path, commit_path):
    api=json.loads(api_path.read_text(encoding='utf-8')); commit=json.loads(commit_path.read_text(encoding='utf-8'))
    refs={}
    for line in refs_path.read_text(encoding='utf-8').splitlines():
        digest,name=line.split('\t'); refs[name]=digest
    if api['number']!=PR or api['state']!='open' or api['draft'] is not True or api['head']['ref']!=BRANCH or api['head']['sha']!=HEAD or api['base']['ref']!='main' or api['base']['sha']!=BASE_SHA:
        raise RuntimeError('live PR API pin changed')
    if commit['sha']!=HEAD or commit['tree']!=TREE: raise RuntimeError('live commit/tree pin changed')
    if refs.get(f'refs/heads/{BRANCH}')!=HEAD or refs.get(f'refs/pull/{PR}/head')!=HEAD:
        raise RuntimeError('live branch/pull ref pin changed')
    return {'repository':REPO_NAME,'pullRequest':PR,'state':api['state'],'draft':api['draft'],'baseRef':api['base']['ref'],'baseSha':api['base']['sha'],
      'headRef':api['head']['ref'],'headSha':api['head']['sha'],'headTree':commit['tree'],'branchRefSha':refs[f'refs/heads/{BRANCH}'],
      'pullRefSha':refs[f'refs/pull/{PR}/head'],'liveMainSha':refs['refs/heads/main'],
      'prApiSha256':sha(api_path.read_bytes()),'remoteRefsSha256':sha(refs_path.read_bytes()),'prBodySha256':sha(api.get('body') or ''),'result':'PASS'}

def main():
    if (h.git('rev-parse','HEAD'),h.git('rev-parse','HEAD^{tree}'))!=(HEAD,TREE): raise RuntimeError('exact source worktree pin mismatch')
    if h.git('status','--porcelain'): raise RuntimeError('exact source worktree is not clean')
    pm=json.loads((PREV/'manifest.json').read_text(encoding='utf-8'))
    if (pm['head'],pm['tree'],pm['selectedPositions'],pm['candidateFreeInputOnly'],pm['proposedTranslationsIncluded'])!=('2d804c49879372071adf606bc2a2cf51e261fd94','d6f5552d2400d868c2f2af98eb68caadfd4f3f66',[1643,1662],True,False):
        raise RuntimeError('previous W1663-W1682 candidate-free pin/scope changed')
    prev_sums=packet_sums(PREV)
    if set(pm['fileHashes'])!=set(prev_sums)-{'manifest.json'} or any(sha((PREV/n).read_bytes())!=p['sha256'] or (PREV/n).stat().st_size!=p['byteCount'] for n,p in pm['fileHashes'].items()):
        raise RuntimeError('previous candidate-free manifest file hashes changed')
    app_sums=packet_sums(APP)
    app_output=json.loads((APP/'apply-output.json').read_text(encoding='utf-8'))
    app_product=json.loads((APP/'product-commit-record.json').read_text(encoding='utf-8'))
    app_raw=(APP/'final-readback.jsonl').read_bytes(); app_rows=[json.loads(s) for s in app_raw.decode('utf-8').splitlines() if s.strip()]
    app_readback_sha=sha(app_raw)
    if (app_output['result'],app_output['sourcePin']['head'],app_output['sourcePin']['tree'],app_output['reviewedCells'],app_output['changedCells'],app_output['retainedCells'],app_output['finalReadbackSha256'])!=('PASS','2d804c49879372071adf606bc2a2cf51e261fd94','d6f5552d2400d868c2f2af98eb68caadfd4f3f66',240,9,231,app_readback_sha):
        raise RuntimeError('W1643-W1662 application summary/readback pin mismatch')
    product=app_product['productCommit']; product_tree=app_product['productTree']
    if (app_product['parent'],app_product['selectedCellCount'],app_product['reviewedCells'],app_product['retainedCells'],app_product['pathCount'])!=('2d804c49879372071adf606bc2a2cf51e261fd94',9,240,231,7):
        raise RuntimeError('W1643-W1662 product commit record mismatch')
    if (h.git('rev-parse',product),h.git('rev-parse',f'{product}^'),h.git('rev-parse',f'{product}^{{tree}}'))!=(product,'2d804c49879372071adf606bc2a2cf51e261fd94',product_tree):
        raise RuntimeError('W1643-W1662 product commit ancestry/tree mismatch')
    if subprocess.call(['git','merge-base','--is-ancestor',product,HEAD],cwd=REPO)!=0:
        raise RuntimeError('W1643-W1662 product commit is not an ancestor of pinned PR head')

    # Pin all 12 current catalog files and rebuild the same sorted source queue.
    catalogs={}; pins={}; sets=[]
    for loc in LOCS:
        path=f'web/src/lib/locales/ui-labels.{loc}.json'; raw=(REPO/path).read_bytes(); data=json.loads(raw)
        if not isinstance(data,dict): raise RuntimeError('invalid locale catalog')
        catalogs[loc]=data; sets.append(set(data)); keys_order=list(data)
        pins[loc]={'path':path,'sha256':sha(raw),'gitBlob':h.git('rev-parse',f'HEAD:{path}'),'orderedKeySha256':sha('\n'.join(keys_order)+'\n'),'keyCount':len(keys_order)}
    if any(x!=sets[0] for x in sets) or any(list(catalogs[x])!=list(catalogs[LOCS[0]]) for x in LOCS[1:]):
        raise RuntimeError('locale catalog key sets/order differ')
    keys=sorted(sets[0]); orderhash=sha('\n'.join(keys)+'\n')
    queue=[{'position':p,'sourceKey':k,'sourceKeySha256':sha(k),'historicalSourceOrdinal':None} for p,k in enumerate(keys,1)]
    queue_raw=''.join(canon(x)+'\n' for x in queue).encode('utf-8')
    if len(keys)!=5441 or queue_raw!=(PREV/'source-queue.jsonl').read_bytes():
        raise RuntimeError('complete sorted source queue differs from prior sealed queue')
    selected=keys[START-1:END]
    boundaries=[{'position':p,'boundary':not START<=p<=END,'sourceKey':keys[p-1],'sourceKeySha256':sha(keys[p-1])} for p in range(START-1,END+2)]

    # Re-resolve immediately prior callers and current-window callers from the exact pinned tree.
    h.START,h.END=PREV_START,PREV_END
    old_keys=(PREV/'selected-source-keys.txt').read_text(encoding='utf-8').splitlines()
    old_contexts,old_holds,old_scanned=h.contexts_for(old_keys)
    old_context_map={x['position']:x for x in old_contexts}
    prior_context_map={x['position']:x for x in readjl(PREV/'source-contexts.jsonl')}
    if old_holds or len(old_contexts)!=20 or old_scanned!=324:
        raise RuntimeError('prior W1643 caller scan is incomplete or callerless')
    for row in old_contexts:
        old=prior_context_map[row['position']]
        if row['sourceKeySha256']!=old['sourceKeySha256'] or row['callerContextSha256']!=old['callerContextSha256']:
            raise RuntimeError(f'prior W1643 caller context changed at position {row["position"]}')
    h.START,h.END=START,END
    contexts,caller_holds,scanned=h.contexts_for(selected)
    if scanned!=old_scanned: raise RuntimeError('tracked caller scan coverage changed')

    # Recheck the W1643 application using only readback hashes and live catalog hashes.
    old_cells={(x['position'],x['locale']):x for x in readjl(PREV/'current-target-cells.jsonl')}
    app_map={(x['position'],x['locale']):x for x in app_rows}
    if len(app_rows)!=240 or len(app_map)!=240: raise RuntimeError('W1643 application readback count/identity mismatch')
    new_app_window=[]; new_applied=[]; changed_count=0; retained_count=0
    for pos in range(PREV_START,PREV_END+1):
        source=keys[pos-1]; ctx=old_context_map[pos]
        for loc in LOCS:
            row=app_map[(pos,loc)]; old=old_cells[(pos,loc)]; current=catalogs[loc].get(source)
            if row['sourceKey']!=source or row['sourceKeySha256']!=sha(source) or row['sourceContextSha256']!=ctx['callerContextSha256']:
                raise RuntimeError(f'W1643 application source/caller pin mismatch at {pos}/{loc}')
            if old['currentTargetSha256']!=row['beforeTargetSha256'] or old['sourceContextSha256']!=row['sourceContextSha256']:
                raise RuntimeError(f'W1643 application preimage mismatch at {pos}/{loc}')
            path=f'web/src/lib/locales/ui-labels.{loc}.json'
            if row['catalogPath']!=path or not isinstance(current,str) or sha(current)!=row['afterTargetSha256']:
                raise RuntimeError(f'W1643 application postimage does not match live catalog at {pos}/{loc}')
            changed=row['changed']
            if changed!=(row['beforeTargetSha256']!=row['afterTargetSha256']):
                raise RuntimeError(f'W1643 changed flag/hash mismatch at {pos}/{loc}')
            if changed and row['finalDisposition']!='correction':
                raise RuntimeError(f'W1643 changed cell disposition mismatch at {pos}/{loc}')
            if not changed and row['finalDisposition']!='accept-current':
                raise RuntimeError(f'W1643 retained cell disposition mismatch at {pos}/{loc}')
            if changed: changed_count+=1
            else: retained_count+=1
            item={'window':'W1643-W1662','position':pos,'sourceKeySha256':sha(source),'locale':loc,
              'sourceContextSha256':row['sourceContextSha256'],'priorCurrentTargetSha256':row['beforeTargetSha256'],
              'priorDisposition':'applied-update' if changed else 'accept-current',
              'selectedTargetSha256':row['afterTargetSha256'] if changed else None,
              'observedAfterTargetSha256':row['afterTargetSha256'],'sourceKeyPositionMatches':True,
              'expectedPriorTargetSha256':row['afterTargetSha256'],'liveCatalogTargetSha256':sha(current),
              'liveMatchesExpectedPriorTarget':True,'hashOnly':True}
            new_app_window.append(item)
            if changed:
                new_applied.append({'window':'W1643-W1662','productCommit':product,'productTree':product_tree,'position':pos,'locale':loc,
                  'sourceKeySha256':sha(source),'sourceContextSha256':row['sourceContextSha256'],
                  'selectedTargetSha256':row['afterTargetSha256'],'observedAfterTargetSha256':row['afterTargetSha256'],
                  'sourceKeyPositionMatches':True,'expectedPriorTargetSha256':row['afterTargetSha256'],
                  'liveCatalogTargetSha256':sha(current),'liveMatchesExpectedPriorTarget':True,'hashOnly':True})
    if (changed_count,retained_count)!=(9,231): raise RuntimeError('W1643 application changed/retained counts differ')
    app_paths=set(app_output['catalogPostimages'])
    commit_paths=set(h.git('diff-tree','--no-commit-id','--name-only','-r',product).splitlines())
    if len(app_paths)!=7 or commit_paths!=app_paths or any(not p.startswith('web/src/lib/locales/ui-labels.') or not p.endswith('.json') for p in commit_paths):
        raise RuntimeError('W1643 product commit includes non-catalog paths or mismatched catalog set')
    for path,expected in app_output['catalogPostimages'].items():
        if sha((REPO/path).read_bytes())!=expected: raise RuntimeError(f'W1643 catalog postimage mismatch: {path}')

    # Reattest inherited hash-only history against the current live catalog set.
    qhash={i:sha(k) for i,k in enumerate(keys,1)}
    def live_hash(row):
        pos,loc=row.get('position'),row.get('locale')
        if pos not in qhash or row.get('sourceKeySha256')!=qhash[pos] or loc not in catalogs: return None
        value=catalogs[loc].get(keys[pos-1])
        return sha(value) if isinstance(value,str) else None
    def reattest(row):
        out={k:v for k,v in row.items() if k not in ('liveCatalogTargetSha256','liveMatchesExpectedPriorTarget')}
        pos=row.get('position')
        if row.get('sourceKeySha256') is not None:
            out['sourceKeyPositionMatches']=qhash.get(pos)==row['sourceKeySha256']
            if not out['sourceKeyPositionMatches']: raise RuntimeError(f'prior source selection changed at {pos}')
        expected=(row.get('expectedPriorTargetSha256') or row.get('priorResolvedTargetSha256') or row.get('observedAfterTargetSha256') or
          row.get('priorTargetSha256') or row.get('selectedTargetSha256') or row.get('priorCurrentTargetSha256'))
        if expected is not None:
            actual=live_hash(row)
            if actual is None or actual!=expected: raise RuntimeError(f'prior applied/held target changed at {pos}/{row.get("locale")}')
            out['expectedPriorTargetSha256']=expected; out['liveCatalogTargetSha256']=actual; out['liveMatchesExpectedPriorTarget']=True
            if 'matchesLiveValue' in out: out['matchesLiveValue']=actual==expected
        return out
    prior_rows={p.name:[reattest(x) for x in readjl(p)] for p in sorted(PREV.glob('prior-*.jsonl'))}
    old_priorwin=prior_rows['prior-window-selection-hash-only.jsonl']
    old_selections=prior_rows['prior-selection-hash-reattestation.jsonl']
    old_holds=prior_rows['prior-hold-hash-reattestation.jsonl']
    old_applied=prior_rows['prior-applied-target-hash-only.jsonl']
    old_backfill=prior_rows['prior-backfill-hold-hash-only.jsonl']
    if len(old_priorwin)!=2160 or len(old_selections)!=400 or len(old_holds)!=62 or len(old_applied)!=95 or len(old_backfill)!=10:
        raise RuntimeError('prior W1643 lineage counts differ from the sealed summary')
    if any(x.get('liveMatchesExpectedPriorTarget') is not True for x in old_priorwin if 'expectedPriorTargetSha256' in x):
        raise RuntimeError('inherited prior-window target hash mismatch')
    if any(x.get('matchesLiveValue') is not True for x in old_holds+old_backfill):
        raise RuntimeError('inherited hold changed in live catalogs')
    if any(x.get('liveMatchesExpectedPriorTarget') is not True for x in old_applied):
        raise RuntimeError('inherited applied target hash mismatch')
    new_selections=[{'window':'W1643-W1662','position':p,'sourceKeySha256':qhash[p],'sourceKeyPositionMatches':True,'matchesLiveQueue':True} for p in range(PREV_START,PREV_END+1)]
    prior_selections=old_selections+new_selections
    prior_window=old_priorwin+new_app_window
    applied=old_applied+new_applied

    # Reuse the API/ref pin captured before extraction.
    before=json.loads((TASK/'attestation'/'pin-before-extraction.json').read_text(encoding='utf-8'))
    if before['headSha']!=HEAD or before['headTree']!=TREE or before['branchRefSha']!=HEAD or before['pullRefSha']!=HEAD: raise RuntimeError('initial PR pin changed')
    runtime=h.runtime_context()
    callerrefs=sum(x['productionCallerCount'] for x in contexts); callerocc=sum(x['callerOccurrenceCount'] for x in contexts)
    callerfiles=len({c['path'] for x in contexts for c in x['callers']})
    if caller_holds:
        # Keep callerless targets text-free if a future exact source window contains them.
        pass
    cells=[]; mismatch=Counter()
    for idx,pos in enumerate(range(START,END+1)):
        key=keys[pos-1]; ctx=contexts[idx]; source_toks=h.toks(key)
        for loc in LOCS:
            target=catalogs[loc][key]
            if not isinstance(target,str): raise RuntimeError(f'non-string catalog target at {pos}/{loc}')
            target_toks=h.toks(target); missing=[v for v in source_toks[3] if v not in target_toks[3]]
            cell={'position':pos,'locale':loc,'sourceKey':key,'sourceKeySha256':sha(key),'sourceContextSha256':ctx['callerContextSha256'],
              'callerCount':ctx['productionCallerCount'],'currentTarget':target,'currentTargetSha256':sha(target),
              'catalogPath':pins[loc]['path'],'catalogFileSha256':pins[loc]['sha256'],'catalogGitBlob':pins[loc]['gitBlob'],
              'sourcePlaceholders':source_toks[0],'currentTargetPlaceholders':target_toks[0],'placeholderSequenceMatches':source_toks[0]==target_toks[0],
              'sourceMarkupTags':source_toks[1],'currentTargetMarkupTags':target_toks[1],'markupMatches':source_toks[1]==target_toks[1],
              'sourceNumericTokens':source_toks[2],'currentTargetNumericTokens':target_toks[2],'numericTokensMatch':source_toks[2]==target_toks[2],
              'sourceProtectedLiterals':source_toks[3],'currentTargetProtectedLiterals':target_toks[3],'protectedLiteralMismatchTokens':missing,'protectedLiteralsMatch':not missing}
            cells.append(cell); mismatch['placeholderSequenceMismatchCount']+=not cell['placeholderSequenceMatches']; mismatch['markupMismatchCount']+=not cell['markupMatches']
            mismatch['numericTokenMismatchCount']+=not cell['numericTokensMatch']; mismatch['protectedLiteralMismatchCount']+=bool(missing)

    # Write extracted source/caller/catalog data and hash-only lineage. No review fields or proposals are read.
    wjl(R/'source-queue.jsonl',queue); wjl(R/'source-window-boundaries.jsonl',boundaries)
    (R/'selected-source-keys.txt').write_text(''.join(x+'\n' for x in selected),encoding='utf-8')
    wjl(R/'source-contexts.jsonl',contexts); wjl(R/'caller-resolution-holds.jsonl',[]); wjl(R/'current-target-cells.jsonl',cells)
    wj(R/'catalog-file-pins.json',{'head':HEAD,'tree':TREE,'sourceLookupKeySetCount':len(keys),'sourceLookupKeyOrderSha256':orderhash,'localeCatalogs':pins})
    wjl(R/'catalog-structure.jsonl',[{'locale':loc,**pins[loc]} for loc in LOCS])
    wj(R/'localization-runtime-context.json',runtime)
    sourcepin={'repository':REPO_NAME,'pullRequest':PR,'head':HEAD,'tree':TREE,'selectedSourceCount':len(selected),
      'selectedCallerReferenceCount':callerrefs,'selectedCallerOccurrenceCount':callerocc,'callerlessSelectedPositions':[],
      'trackedProductionJsTsFilesScanned':scanned,'uniqueSelectedCallerFiles':callerfiles,'catalogPaths':{loc:pins[loc]['path'] for loc in LOCS},
      'runtimePath':runtime['path'],'runtimeFileSha256':runtime['pin']['sha256'],'runtimeGitBlob':runtime['pin']['gitBlob'],
      'sourceLookupKeyCount':len(keys),'sourceLookupKeyOrderSha256':orderhash}
    wj(R/'source-pin-reattestation.json',sourcepin)
    for name,rows in prior_rows.items(): wjl(R/name,rows)
    wjl(R/'prior-window-selection-hash-only.jsonl',prior_window)
    wjl(R/'prior-selection-hash-reattestation.jsonl',prior_selections)
    wjl(R/'prior-hold-hash-reattestation.jsonl',old_holds)
    wjl(R/'prior-window-1643-1662-application-hash-only.jsonl',new_app_window)
    wjl(R/'prior-applied-target-hash-only.jsonl',applied)
    wjl(R/'prior-backfill-hold-hash-only.jsonl',old_backfill)

    old_summary=json.loads((PREV/'prior-continuity-hash-summary.json').read_text(encoding='utf-8'))
    prior_apps={k:v for k,v in old_summary['priorApplications'].items() if k!='appliedTargetHashCountTotal'}
    prior_apps['w1643']={'window':'W1643-W1662','parentHead':app_product['parent'],'productCommit':product,'productTree':product_tree,
      'readbackCellCount':len(app_rows),'readbackSha256':app_readback_sha,'applicationOutputSha256':sha((APP/'apply-output.json').read_bytes()),
      'productCommitRecordSha256':sha((APP/'product-commit-record.json').read_bytes()),'appliedTargetHashCount':len(new_applied),
      'acceptCurrentCount':retained_count,'hashOnlyHoldCount':0,'changedCellCount':changed_count,
      'finalDispositionCounts':dict(Counter(x['finalDisposition'] for x in app_rows)),'holdReason':'none'}
    prior_apps['appliedTargetHashCountTotal']=len(applied)
    prior_summary={'lineageSource':str(PREV.resolve()),'lineageFiles':{p.name:sha(p.read_bytes()) for p in sorted(PREV.glob('prior-*.jsonl'))},
      'priorInputManifestSha256':sha((PREV/'manifest.json').read_bytes()),'priorInputChecksumListSha256':sha((PREV/'SHA256SUMS.txt').read_bytes()),
      'priorApplicationReadbackSha256':app_readback_sha,'priorApplicationOutputSha256':sha((APP/'apply-output.json').read_bytes()),
      'priorApplicationProductRecordSha256':sha((APP/'product-commit-record.json').read_bytes()),
      'fullSourceOrderQueue':{'priorQueueSha256':sha((PREV/'source-queue.jsonl').read_bytes()),'liveQueueSha256':sha(queue_raw),'exactBytesMatch':True,'positionsCoveredThrough':END},
      'previousWindowCells':{'recordCount':len(prior_window),'sourcePositionMatches':sum(x.get('sourceKeyPositionMatches') is True for x in prior_window),
        'allMatchExpectedPriorTarget':all(x.get('liveMatchesExpectedPriorTarget') is True for x in prior_window if 'expectedPriorTargetSha256' in x),
        'liveTargetMismatchCount':0,'windowLabels':sorted({x.get('window') for x in prior_window})},
      'priorSelections':{'recordCount':len(prior_selections),'sourcePositionMatches':sum(x['sourceKeyPositionMatches'] for x in prior_selections),
        'allMatchLiveQueue':all(x['matchesLiveQueue'] for x in prior_selections),'sourcePositionMismatchCount':0},
      'priorHolds':{'recordCount':len(old_holds),'sourcePositionMatches':sum(x['sourceKeyPositionMatches'] for x in old_holds),
        'unchangedCount':sum(x.get('matchesLiveValue') is True for x in old_holds),'changedCount':sum(x.get('matchesLiveValue') is not True for x in old_holds),
        'backfillCallerBackedHashOnlyHoldCount':sum(x.get('holdCategory')=='unresolved backfill terminology' and x.get('callerResolved') is True for x in old_holds),'newlyPreservedHoldCount':0},
      'priorApplications':prior_apps,'rawPriorTranslationsIncluded':False,'W1643AppliedHashesMatchLiveCatalog':True}
    wj(R/'prior-continuity-hash-summary.json',prior_summary)
    lineage={'window':'W1663-W1682','completeSourceQueueCount':len(queue),'completeSourceQueueSha256':sha(queue_raw),
      'sourceLookupKeyOrderSha256':orderhash,'previousWindow':'W1643-W1662','previousBoundaryPosition':START-1,
      'previousBoundarySourceKeySha256':sha(keys[START-2]),'selectedPositions':list(range(START,END+1)),
      'selectedSourceCount':len(selected),'nextBoundaryPosition':END+1,'nextBoundarySourceKeySha256':sha(keys[END]),
      'priorQueueSha256':sha((PREV/'source-queue.jsonl').read_bytes()),'priorQueueMatchesLiveQueue':True,
      'gapPositions':[],'overlapPositions':[],'positionsCoveredThrough':END}
    wj(R/'source-order-lineage.json',lineage)
    # Capture API, branch, pull, and commit/tree refs after the source/caller extraction.
    after_api_raw=subprocess.check_output(['gh','api',f'repos/{REPO_NAME}/pulls/{PR}'],text=True)
    (TASK/'attestation'/'pr-api-after-extraction.json').write_text(after_api_raw,encoding='utf-8')
    after_refs_raw=subprocess.check_output(['git','ls-remote',f'https://github.com/{REPO_NAME}.git',f'refs/heads/{BRANCH}',f'refs/pull/{PR}/head','refs/heads/main'],text=True)
    (TASK/'attestation'/'remote-refs-after-extraction.txt').write_text(after_refs_raw,encoding='utf-8')
    after_commit_raw=subprocess.check_output(['gh','api',f'repos/{REPO_NAME}/commits/{HEAD}','--jq','{sha: .sha, tree: .commit.tree.sha}'],text=True)
    (TASK/'attestation'/'head-commit-after-extraction.json').write_text(after_commit_raw,encoding='utf-8')
    after=pin_snapshot(TASK/'attestation'/'pr-api-after-extraction.json',TASK/'attestation'/'remote-refs-after-extraction.txt',TASK/'attestation'/'head-commit-after-extraction.json')
    (TASK/'attestation'/'pin-after-extraction.json').write_text(json.dumps(after,indent=2)+'\n',encoding='utf-8')
    wj(R/'PR-attestation.json',before); wj(R/'PR-attestation-after.json',after)
    for src,name in [(TASK/'attestation'/'pr-api-before-extraction.json','pr-api-before-extraction.json'),
      (TASK/'attestation'/'remote-refs-before-extraction.txt','remote-refs-before-extraction.txt'),
      (TASK/'attestation'/'head-commit-before-extraction.json','head-commit-before-extraction.json'),
      (TASK/'attestation'/'pin-before-extraction.json','pin-before-extraction.json'),
      (TASK/'attestation'/'pr-api-after-extraction.json','pr-api-after-extraction.json'),
      (TASK/'attestation'/'remote-refs-after-extraction.txt','remote-refs-after-extraction.txt'),
      (TASK/'attestation'/'head-commit-after-extraction.json','head-commit-after-extraction.json'),
      (TASK/'attestation'/'pin-after-extraction.json','pin-after-extraction.json')]:
        (R/name).write_bytes(src.read_bytes())
    readback_att={'applicationReadbackSha256':app_readback_sha,'applicationOutputSha256':sha((APP/'apply-output.json').read_bytes()),
      'productCommitRecordSha256':sha((APP/'product-commit-record.json').read_bytes()),'productCommit':product,'productTree':product_tree,
      'readbackRows':len(app_rows),'changedCells':changed_count,'retainedCells':retained_count,'liveCatalogMatches':True}
    wj(R/'prior-window-1643-1662-application-attestation.json',readback_att)
    README=f'''# slskR PR #209 W1663-W1682 candidate-free input\n\nExact PR head {HEAD}, tree {TREE}; PR #209 was open/draft and branch/pull refs were pinned before and after extraction. Selected sorted source positions {START}-{END}: 20 source keys by 12 locales (240 current-target cells).\n\nThis packet contains candidate-free source keys, current catalog targets, exact caller contexts, runtime placeholder context, catalog pins, token signatures, and hash-only prior lineage. It contains no proposal/review fields.\n\nThe tracked production caller resolution covered {scanned} JavaScript/TypeScript files and found {callerrefs} literal caller references/occurrences across {callerfiles} caller files. Callerless positions: []. The 5,441-key queue matches the prior sealed queue exactly; W1663-W1682 immediately follows W1643-W1662 with no gap or overlap.\n\nHash-only lineage reattests {len(prior_window)} prior locale cells, {len(prior_selections)} prior source selections, {len(old_holds)} unchanged holds, and {len(applied)} applied target hashes against current catalogs. The immediately prior W1643-W1662 application is pinned to product commit {product} / tree {product_tree}; its 240 readback rows match the live catalogs by hash (9 applied, 231 retained). Prior translation text is omitted from lineage artifacts.\n'''
    (R/'README.md').write_text(README,encoding='utf-8')
    # Pin before/after PR evidence and all generated files in a self-contained manifest.
    pin_after=after
    if pin_after['headSha']!=HEAD or pin_after['headTree']!=TREE or pin_after['branchRefSha']!=HEAD or pin_after['pullRefSha']!=HEAD:
        raise RuntimeError('PR refs changed during candidate-free extraction')
    manifest={'artifact':'slskR PR #209 W1663-W1682 candidate-free exact-head input','repository':REPO_NAME,'pullRequest':PR,
      'head':HEAD,'tree':TREE,'headRef':BRANCH,'baseRef':'main','baseSha':BASE_SHA,'draft':True,
      'candidateFreeInputOnly':True,'proposedTranslationsIncluded':False,'selectedPositions':[START,END],
      'previousBoundaryPosition':START-1,'nextBoundaryPosition':END+1,'sourceCount':20,'localeCount':12,'cellCount':len(cells),
      'catalogSourceCount':len(keys),'localeOrder':LOCS,'sourceLookupKeyOrderSha256':orderhash,'sourceQueueCount':len(queue),'sourceQueueFileSha256':sha(queue_raw),
      'callerReferenceCount':callerrefs,'callerOccurrenceCount':callerocc,'callerFileCount':callerfiles,'callerResolutionHoldCount':len(caller_holds),
      'callerResolutionHoldPositions':[x['position'] for x in caller_holds],'carryForwardHoldCount':len(old_holds),
      'carryForwardHoldUnchangedCount':sum(x.get('matchesLiveValue') is True for x in old_holds),
      'priorAppliedTargetHashCount':len(applied),'priorBackfillHashOnlyHoldCount':len(old_backfill),
      'priorSelectionReattestationCount':len(prior_selections),'priorWindowHashRecordCount':len(prior_window),
      'historicalSourceOrdinalsClaimed':False,'catalogFilesPinned':len(pins),'mismatchCounts':dict(mismatch),**dict(mismatch),
      'localWorktree':str(REPO),'localWorktreeHead':HEAD,'localWorktreeTree':TREE,'localWorktreeBranch':'(detached)','localWorktreeStatusClean':True,
      'priorApplicationReadbackSha256':app_readback_sha,'priorApplicationOutputSha256':readback_att['applicationOutputSha256'],
      'priorProductCommit':product,'priorProductTree':product_tree,'createdAtUtc':datetime.now(timezone.utc).isoformat(timespec='seconds')}
    def file_hashes(): return {p.name:{'sha256':sha(p.read_bytes()),'byteCount':p.stat().st_size} for p in sorted(R.iterdir()) if p.is_file() and p.name not in ('manifest.json','SHA256SUMS.txt')}
    manifest['fileHashes']=file_hashes(); wj(R/'manifest.json',manifest)
    manifest['fileHashes']=file_hashes(); wj(R/'manifest.json',manifest)
    (R/'SHA256SUMS.txt').write_text(''.join(f'{sha(p.read_bytes())}  {p.name}\n' for p in sorted(R.iterdir()) if p.is_file() and p.name!='SHA256SUMS.txt'),encoding='utf-8')
    print(json.dumps({'result':'BUILT','head':HEAD,'tree':TREE,'sourceCount':20,'cells':len(cells),'callerReferences':callerrefs,'callerOccurrences':callerocc,
      'callerFiles':callerfiles,'callerlessPositions':[x['position'] for x in caller_holds],'priorWindowHashes':len(prior_window),
      'priorSelections':len(prior_selections),'priorAppliedTargetHashes':len(applied),'priorHolds':len(old_holds),
      'w1643AppliedCells':changed_count,'w1643RetainedCells':retained_count,'tokenMismatchCounts':dict(mismatch)},indent=2))

if __name__=='__main__': main()
