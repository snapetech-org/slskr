#!/usr/bin/env python3
"""Build exact-head, candidate-free lineage for slskR PR #209 W1623-W1642."""
import hashlib, importlib.util, json, subprocess, sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

R=Path(__file__).resolve().parent
REPO=Path('/mnt/disks/scratch/task-scratch/slskr-pr209-w1623-1642-20261105/worktree')
PREV=Path('/mnt/disks/scratch/task-scratch/slskr-pr209-w1603-1622-20261105/candidate-free-input')
APP=REPO/'docs/pr-evidence/pr209-localization-2026-11-05/w1603-1622/application'
HEAD='7e366cbf21ad5490bd11ef418a0f2a98b3fbd567'
TREE='801d7a037c15dcd83b3e038160054a46c9b8f03b'
START,END=1623,1642
LOCS=['es','zh-Hans','hi','de','ja','fr','pt-BR','ar','ko','zh-Hant','vi','id']
REPO_NAME='snapetech-org/slskR'; PR=209; BRANCH='codex/slskr-l10n-audit-20261104-resync'; BASE_SHA='1bbaec9fdc63a86de343e37e33bae70d44301a36'
sys.dont_write_bytecode=True
spec=importlib.util.spec_from_file_location('schema_helper',R/'candidate-free-schema-helper.py')
h=importlib.util.module_from_spec(spec); spec.loader.exec_module(h)
h.R=R; h.REPO=REPO; h.PREV=PREV; h.APP=APP; h.HEAD=HEAD; h.TREE=TREE; h.START=START; h.END=END; h.LOCS=LOCS; h.REPO_NAME=REPO_NAME; h.PR=PR; h.BRANCH=BRANCH; h.BASE_SHA=BASE_SHA
sha,canon,wj,wjl=h.sha,h.canon,h.wj,h.wjl

def readjl(path): return [json.loads(s) for s in path.read_text(encoding='utf-8').splitlines() if s]
def checksums(path):
    sums={}
    for line in (path/'SHA256SUMS.txt').read_text(encoding='utf-8').splitlines():
        d,n=line.split(None,1); sums[n.lstrip('* ')]=d
    actual={p.name for p in path.iterdir() if p.is_file() and p.name!='SHA256SUMS.txt'}
    if set(sums)!=actual or any(sha((path/n).read_bytes())!=d for n,d in sums.items()):
        raise RuntimeError(f'checksum verification failed for {path}')
    return sums

def main():
    if (h.git('rev-parse','HEAD'),h.git('rev-parse','HEAD^{tree}'))!=(HEAD,TREE): raise RuntimeError('exact source checkout pin mismatch')
    pm=json.loads((PREV/'manifest.json').read_text(encoding='utf-8'))
    if (pm['head'],pm['tree'],pm['selectedPositions'],pm['candidateFreeInputOnly'],pm['proposedTranslationsIncluded'])!=('eeb63f1e4e21d801f4a4e0393813b6e86a1ff7c8','590ee410666905f68f601393b64a4798b0609181',[1603,1622],True,False):
        raise RuntimeError('prior W1603 candidate-free packet pin changed')
    psums=checksums(PREV)
    if set(pm['fileHashes'])!=set(psums)-{'manifest.json'} or any(sha((PREV/n).read_bytes())!=p['sha256'] or (PREV/n).stat().st_size!=p['byteCount'] for n,p in pm['fileHashes'].items()):
        raise RuntimeError('prior W1603 manifest file hashes changed')
    before=h.pr_attestation(datetime.now(timezone.utc).isoformat(timespec='seconds'))

    catalogs,pins,sets={},{},[]
    for loc in LOCS:
        path=f'web/src/lib/locales/ui-labels.{loc}.json'; raw=(REPO/path).read_bytes(); data=json.loads(raw)
        if not isinstance(data,dict): raise RuntimeError('invalid locale catalog')
        catalogs[loc]=data; sets.append(set(data)); ks=list(data)
        pins[loc]={'path':path,'sha256':sha(raw),'gitBlob':h.git('rev-parse',f'HEAD:{path}'),'orderedKeySha256':sha('\n'.join(ks)+'\n'),'keyCount':len(ks)}
    if any(x!=sets[0] for x in sets) or any(list(catalogs[x])!=list(catalogs[LOCS[0]]) for x in LOCS[1:]): raise RuntimeError('locale catalog key sets/order differ')
    keys=sorted(sets[0]); orderhash=sha('\n'.join(keys)+'\n')
    queue=[{'position':p,'sourceKey':k,'sourceKeySha256':sha(k),'historicalSourceOrdinal':None} for p,k in enumerate(keys,1)]
    queue_raw=''.join(canon(x)+'\n' for x in queue).encode()
    if len(keys)!=5441 or queue_raw!=(PREV/'source-queue.jsonl').read_bytes(): raise RuntimeError('full source queue differs from prior exact queue')
    selected=keys[START-1:END]
    boundaries=[{'position':p,'boundary':not START<=p<=END,'sourceKey':keys[p-1],'sourceKeySha256':sha(keys[p-1])} for p in range(START-1,END+2)]
    contexts,caller_holds,scanned=h.contexts_for(selected)

    cells=[]; mismatch=Counter()
    for p in range(START,END+1):
        key=keys[p-1]; context=contexts[p-START]; st=h.toks(key)
        for loc in LOCS:
            target=catalogs[loc][key]
            if not isinstance(target,str): raise RuntimeError(f'non-string target at {p}/{loc}')
            tt=h.toks(target); missing=[x for x in st[3] if x not in tt[3]]
            cell={'position':p,'locale':loc,'sourceKey':key,'sourceKeySha256':sha(key),'sourceContextSha256':context['callerContextSha256'],'callerCount':context['productionCallerCount'],
              'currentTarget':target,'currentTargetSha256':sha(target),'catalogPath':pins[loc]['path'],'catalogFileSha256':pins[loc]['sha256'],'catalogGitBlob':pins[loc]['gitBlob'],
              'sourcePlaceholders':st[0],'currentTargetPlaceholders':tt[0],'placeholderSequenceMatches':st[0]==tt[0],'sourceMarkupTags':st[1],'currentTargetMarkupTags':tt[1],
              'markupMatches':st[1]==tt[1],'sourceNumericTokens':st[2],'currentTargetNumericTokens':tt[2],'numericTokensMatch':st[2]==tt[2],
              'sourceProtectedLiterals':st[3],'currentTargetProtectedLiterals':tt[3],'protectedLiteralMismatchTokens':missing,'protectedLiteralsMatch':not missing}
            cells.append(cell); mismatch['placeholderSequenceMismatchCount']+=not cell['placeholderSequenceMatches']; mismatch['markupMismatchCount']+=not cell['markupMatches']
            mismatch['numericTokenMismatchCount']+=not cell['numericTokensMatch']; mismatch['protectedLiteralMismatchCount']+=bool(missing)

    # Re-attest the previous packet's hash-only history, then append its exact 240-cell readback.
    prior_names=('prior-window-selection-hash-only.jsonl','prior-selection-hash-reattestation.jsonl','prior-hold-hash-reattestation.jsonl',
      'prior-window-1503-1522-catalog-diff-hash-only.jsonl','prior-window-1523-1542-application-hash-only.jsonl',
      'prior-window-1543-1562-application-hash-only.jsonl','prior-window-1563-1582-application-hash-only.jsonl',
      'prior-window-1583-1602-application-hash-only.jsonl','prior-applied-target-hash-only.jsonl','prior-backfill-hold-hash-only.jsonl')
    prior={n:readjl(PREV/n) for n in prior_names}
    old_cells={(x['position'],x['locale']):x for x in readjl(PREV/'current-target-cells.jsonl')}
    old_contexts={x['position']:x for x in readjl(PREV/'source-contexts.jsonl')}
    qhash={i:sha(k) for i,k in enumerate(keys,1)}
    def live(x):
        p,l=x['position'],x.get('locale')
        if qhash.get(p)!=x.get('sourceKeySha256') or l not in catalogs: return None
        value=catalogs[l].get(keys[p-1]); return sha(value) if isinstance(value,str) else None
    def reattest(x):
        expected=(x.get('expectedPriorTargetSha256') or x.get('priorResolvedTargetSha256') or x.get('observedAfterTargetSha256') or
          x.get('priorTargetSha256') or x.get('selectedTargetSha256') or x.get('priorCurrentTargetSha256'))
        actual=live(x); out={k:v for k,v in x.items() if k not in ('liveCatalogTargetSha256','liveMatchesExpectedPriorTarget')}
        if expected is not None:
            out['expectedPriorTargetSha256']=expected; out['liveCatalogTargetSha256']=actual; out['liveMatchesExpectedPriorTarget']=actual is not None and actual==expected
        if x.get('sourceKeySha256') is not None:
            out['sourceKeyPositionMatches']=qhash.get(x['position'])==x['sourceKeySha256']
        return out
    priorwin=[reattest(x) for x in prior[prior_names[0]]]
    prior_selections=[]
    for x in prior[prior_names[1]]:
        if qhash.get(x['position'])!=x['sourceKeySha256']: raise RuntimeError('inherited prior source selection changed')
        prior_selections.append({'window':x.get('window'),'position':x['position'],'sourceKeySha256':x['sourceKeySha256'],'sourceKeyPositionMatches':True,'matchesLiveQueue':True})
    prior_holds=[]
    for x in prior[prior_names[2]]:
        actual=live(x)
        if actual is None or actual!=x.get('priorTargetSha256'): raise RuntimeError('an inherited hold changed in live catalogs')
        prior_holds.append({'window':x.get('window'),'position':x['position'],'sourceKeySha256':x['sourceKeySha256'],'sourceKeyPositionMatches':True,'locale':x['locale'],
          'priorTargetSha256':x['priorTargetSha256'],'liveTargetSha256':actual,'matchesLiveValue':True,'holdCategory':x.get('holdCategory'),'callerResolved':x.get('callerResolved')})
    app_windows={}
    for n in prior_names[3:8]:
        rows=[reattest(x) for x in prior[n]]
        if any(not x.get('liveMatchesExpectedPriorTarget') for x in rows): raise RuntimeError(f'inherited lineage target mismatch in {n}')
        app_windows[n]=rows
    applied=[reattest(x) for x in prior[prior_names[8]]]
    backfill=[reattest(x) for x in prior[prior_names[9]]]
    if any(not x.get('liveMatchesExpectedPriorTarget') for x in priorwin+applied) or any(x.get('matchesLiveValue') is False for x in backfill):
        raise RuntimeError('inherited prior target/hash-only lineage no longer matches live catalogs')

    app_summary=json.loads((APP/'application-summary.json').read_text(encoding='utf-8'))
    app_raw=(APP/'readback-240-cells.jsonl').read_bytes(); app_rows=[json.loads(s) for s in app_raw.decode().splitlines() if s]
    if (app_summary.get('headBefore'),app_summary.get('treeBefore'),app_summary.get('changedCellCount'),app_summary.get('readbackCellCount'),app_summary.get('productCommit'),app_summary.get('productTree'),app_summary.get('baseHead'),app_summary.get('productCommitChangesOnlyCatalogs'))!=(
      'eeb63f1e4e21d801f4a4e0393813b6e86a1ff7c8','590ee410666905f68f601393b64a4798b0609181',13,240,'bdc831fcde86101cd949fe70bd99acd8871ace4a','c9d994368a90e82f310a3c81a6ba059567c0e3bd','eeb63f1e4e21d801f4a4e0393813b6e86a1ff7c8',True):
        raise RuntimeError('W1603 application summary changed')
    if len(app_rows)!=240 or sum(bool(x.get('changed')) for x in app_rows)!=13 or not all(x.get('matchesPlan') for x in app_rows):
        raise RuntimeError('W1603 application readback count or plan mismatch')
    expected_app_cells={(p,l) for p in range(1603,1623) for l in LOCS}
    if {(x['position'],x['locale']) for x in app_rows}!=expected_app_cells:
        raise RuntimeError('W1603 application readback cell set mismatch')
    if (h.git('rev-parse',f"{app_summary['productCommit']}^"),h.git('rev-parse',f"{app_summary['productCommit']}^{{tree}}"))!=(app_summary['baseHead'],app_summary['productTree']):
        raise RuntimeError('W1603 product commit ancestry/tree mismatch')
    if subprocess.call(['git','merge-base','--is-ancestor',app_summary['productCommit'],HEAD],cwd=REPO)!=0:
        raise RuntimeError('W1603 product commit is not an ancestor of pinned head')
    commit_paths=set(h.git('diff-tree','--no-commit-id','--name-only','-r',app_summary['productCommit']).splitlines())
    if commit_paths!=set(app_summary['changedCatalogPaths']) or any(not x.startswith('web/src/lib/locales/ui-labels.') or not x.endswith('.json') for x in commit_paths):
        raise RuntimeError('W1603 product commit contains unexpected paths')
    old_catalogs={}
    for loc in LOCS:
        path=f'web/src/lib/locales/ui-labels.{loc}.json'
        old_catalogs[loc]=json.loads(subprocess.check_output(['git','show',f"{app_summary['headBefore']}:{path}"],cwd=REPO,text=True))
    diffs={(p,l) for l in LOCS for p in old_catalogs[l] if old_catalogs[l][p]!=catalogs[l].get(p)}
    changed_rows={(x['sourceKeySha256'],x['locale']) for x in app_rows if x.get('changed')}
    expected_diffs={(sha(keys[x['position']-1]),x['locale']) for x in app_rows if x.get('changed')}
    diff_hashes={(sha(key),locale) for key,locale in diffs}
    if diff_hashes!=expected_diffs or changed_rows!=expected_diffs or len(diffs)!=13:
        raise RuntimeError('W1603 exact catalog update set does not match readback')
    appended=[]; new_applied=[]
    for x in sorted(app_rows,key=lambda row:(row['position'],LOCS.index(row['locale']))):
        p,l=x['position'],x['locale']; old=old_cells.get((p,l)); current=catalogs[l].get(keys[p-1])
        if old is None or x['sourceKeySha256']!=qhash[p] or x['sourceKeySha256']!=old['sourceKeySha256'] or x['sourceContextSha256']!=old['sourceContextSha256'] or x['currentTargetSha256']!=old['currentTargetSha256']:
            raise RuntimeError('W1603 application source/current pins do not match prior packet')
        pin=PREV/'catalog-file-pins.json'
        prior_pin=json.loads(pin.read_text(encoding='utf-8'))['localeCatalogs'][l]
        if x['sourceKey']!=keys[p-1] or x['catalogPath']!=prior_pin['path'] or x['catalogFilePreimageSha256']!=prior_pin['sha256'] or not x.get('matchesPlan'):
            raise RuntimeError('W1603 application source/catalog preimage mismatch')
        if sha(current)!=x['postimageTargetSha256'] or x['expectedTargetSha256']!=x['postimageTargetSha256']:
            raise RuntimeError('W1603 application target hash does not match pinned live catalog')
        update=bool(x['changed'])
        if update!=(x['postimageTargetSha256']!=x['currentTargetSha256']):
            raise RuntimeError('W1603 application changed flag conflicts with target hashes')
        item={'window':'W1603-W1622','position':p,'sourceKeySha256':x['sourceKeySha256'],'locale':l,
          'priorDisposition':'applied-update' if update else 'accept-current','priorCurrentTargetSha256':x['currentTargetSha256'],
          'priorResolvedTargetSha256':x['postimageTargetSha256'],'selectedTargetSha256':x['postimageTargetSha256'] if update else None,
          'observedAfterTargetSha256':x['postimageTargetSha256'],'sourceContextSha256':x['sourceContextSha256'],
          'hashOnlyHold':False,'callerResolved':old_contexts[p]['productionCallerCount']>0,
          'sourceKeyPositionMatches':True,'expectedPriorTargetSha256':x['postimageTargetSha256'],
          'liveCatalogTargetSha256':sha(current),'liveMatchesExpectedPriorTarget':True}
        appended.append(item)
        if update:
            new_applied.append({'window':'W1603-W1622','productCommit':app_summary['productCommit'],'productTree':app_summary['productTree'],
              'position':p,'locale':l,'sourceKeySha256':x['sourceKeySha256'],'sourceContextSha256':x['sourceContextSha256'],
              'selectedTargetSha256':x['postimageTargetSha256'],'observedAfterTargetSha256':x['postimageTargetSha256'],
              'sourceKeyPositionMatches':True,'expectedPriorTargetSha256':x['postimageTargetSha256'],
              'liveCatalogTargetSha256':sha(current),'liveMatchesExpectedPriorTarget':True})
    priorwin.extend(appended); applied.extend(new_applied)
    prior_selections.extend({'window':'W1603-W1622','position':p,'sourceKeySha256':qhash[p],'sourceKeyPositionMatches':True,'matchesLiveQueue':True} for p in range(1603,1623))

    runtime=h.runtime_context(); callerrefs=sum(x['productionCallerCount'] for x in contexts); callerocc=sum(x['callerOccurrenceCount'] for x in contexts)
    callerfiles=len({c['path'] for x in contexts for c in x['callers']})
    sourcepin={'repository':REPO_NAME,'pullRequest':PR,'head':HEAD,'tree':TREE,'selectedSourceCount':len(selected),'selectedCallerReferenceCount':callerrefs,
      'selectedCallerOccurrenceCount':callerocc,'callerlessSelectedPositions':[x['position'] for x in contexts if not x['productionCallerCount']],'trackedProductionJsTsFilesScanned':scanned,
      'uniqueSelectedCallerFiles':callerfiles,'catalogPaths':{l:p['path'] for l,p in pins.items()},'runtimePath':h.RUNTIME,'runtimeFileSha256':runtime['pin']['sha256'],'runtimeGitBlob':runtime['pin']['gitBlob'],
      'sourceLookupKeyCount':len(keys),'sourceLookupKeyOrderSha256':orderhash}
    wjl(R/'source-queue.jsonl',queue); wjl(R/'source-window-boundaries.jsonl',boundaries); (R/'selected-source-keys.txt').write_text(''.join(x+'\n' for x in selected),encoding='utf-8')
    wjl(R/'source-contexts.jsonl',contexts); wjl(R/'caller-resolution-holds.jsonl',caller_holds); wjl(R/'current-target-cells.jsonl',cells)
    wj(R/'catalog-file-pins.json',{'head':HEAD,'tree':TREE,'sourceLookupKeySetCount':len(keys),'sourceLookupKeyOrderSha256':orderhash,'localeCatalogs':pins})
    wjl(R/'catalog-structure.jsonl',[{'locale':l,**pins[l]} for l in LOCS]); wj(R/'localization-runtime-context.json',runtime); wj(R/'source-pin-reattestation.json',sourcepin)
    wjl(R/'prior-window-selection-hash-only.jsonl',priorwin); wjl(R/'prior-selection-hash-reattestation.jsonl',prior_selections); wjl(R/'prior-hold-hash-reattestation.jsonl',prior_holds)
    wjl(R/'prior-window-1503-1522-catalog-diff-hash-only.jsonl',app_windows[prior_names[3]])
    wjl(R/'prior-window-1523-1542-application-hash-only.jsonl',app_windows[prior_names[4]])
    wjl(R/'prior-window-1543-1562-application-hash-only.jsonl',app_windows[prior_names[5]])
    wjl(R/'prior-window-1563-1582-application-hash-only.jsonl',app_windows[prior_names[6]])
    wjl(R/'prior-window-1583-1602-application-hash-only.jsonl',app_windows[prior_names[7]])
    wjl(R/'prior-window-1603-1622-application-hash-only.jsonl',appended); wjl(R/'prior-applied-target-hash-only.jsonl',applied); wjl(R/'prior-backfill-hold-hash-only.jsonl',backfill)
    prior_apps={k:v for k,v in json.loads((PREV/'prior-continuity-hash-summary.json').read_text())['priorApplications'].items() if k!='appliedTargetHashCountTotal'}
    prior_apps['w1603']={'window':'W1603-W1622','parentHead':app_summary['baseHead'],'productCommit':app_summary['productCommit'],'productTree':app_summary['productTree'],
      'readbackCellCount':len(app_rows),'readbackSha256':sha(app_raw),'applicationSummarySha256':sha((APP/'application-summary.json').read_bytes()),'appliedTargetHashCount':len(new_applied),
      'acceptCurrentCount':sum(not x['changed'] for x in app_rows),'hashOnlyHoldCount':0,'changedCellCount':sum(bool(x['changed']) for x in app_rows),
      'rootDispositionCounts':app_summary['rootDispositionCounts'],'holdReason':'none'}
    prior_apps['appliedTargetHashCountTotal']=len(applied)
    prior_summary={'lineageSource':str(PREV.resolve()),'lineageFiles':{n:sha((PREV/n).read_bytes()) for n in prior_names},'priorInputManifestSha256':sha((PREV/'manifest.json').read_bytes()),
      'priorInputChecksumListSha256':sha((PREV/'SHA256SUMS.txt').read_bytes()),'applicationReadbackSha256':sha(app_raw),'applicationSummarySha256':sha((APP/'application-summary.json').read_bytes()),
      'fullSourceOrderQueue':{'priorQueueSha256':sha((PREV/'source-queue.jsonl').read_bytes()),'liveQueueSha256':sha(queue_raw),'exactBytesMatch':True,'positionsCoveredThrough':1622},
      'previousWindowCells':{'recordCount':len(priorwin),'sourcePositionMatches':sum(x.get('sourceKeyPositionMatches') is True for x in priorwin),'allMatchExpectedPriorTarget':all(x.get('liveMatchesExpectedPriorTarget') is True for x in priorwin),
        'liveTargetMismatchCount':sum(x.get('liveMatchesExpectedPriorTarget') is not True for x in priorwin),'windowLabels':sorted({x.get('window') for x in priorwin})},
      'priorSelections':{'recordCount':len(prior_selections),'sourcePositionMatches':sum(x['sourceKeyPositionMatches'] for x in prior_selections),'allMatchLiveQueue':all(x['matchesLiveQueue'] for x in prior_selections),'sourcePositionMismatchCount':0},
      'priorHolds':{'recordCount':len(prior_holds),'sourcePositionMatches':sum(x['sourceKeyPositionMatches'] for x in prior_holds),'unchangedCount':sum(x['matchesLiveValue'] for x in prior_holds),'changedCount':sum(not x['matchesLiveValue'] for x in prior_holds),
        'backfillCallerBackedHashOnlyHoldCount':sum(x.get('holdCategory')=='unresolved backfill terminology' and x.get('callerResolved') is True for x in prior_holds),'newlyPreservedHoldCount':0},
      'priorApplications':prior_apps,'rawPriorTranslationsIncluded':False,'W1603AppliedHashesMatchLiveCatalog':True}
    wj(R/'prior-continuity-hash-summary.json',prior_summary)
    lineage={'window':'W1623-W1642','completeSourceQueueCount':len(queue),'completeSourceQueueSha256':sha(queue_raw),'sourceLookupKeyOrderSha256':orderhash,
      'previousWindow':'W1603-W1622','previousBoundaryPosition':START-1,'previousBoundarySourceKeySha256':sha(keys[START-2]),'selectedPositions':list(range(START,END+1)),
      'selectedSourceCount':len(selected),'nextBoundaryPosition':END+1,'nextBoundarySourceKeySha256':sha(keys[END]),'priorQueueSha256':prior_summary['fullSourceOrderQueue']['priorQueueSha256'],
      'priorQueueMatchesLiveQueue':True,'gapPositions':[],'overlapPositions':[],'positionsCoveredThrough':END}
    wj(R/'source-order-lineage.json',lineage)
    wj(R/'PR-attestation.json',before); wj(R/'PR-attestation-after.json',h.pr_attestation(datetime.now(timezone.utc).isoformat(timespec='seconds')))
    (R/'README.md').write_text(f'''# slskR PR #209 W1623-W1642 candidate-free input

Exact PR head {HEAD}, tree {TREE}; PR #209 was open/draft and branch/pull refs were captured before and after extraction. Selected sorted source positions {START}-{END}: 20 source keys by 12 locales (240 current-target cells).

This packet contains source keys, current catalog targets, exact caller contexts, runtime lookup/placeholder context, integrity pins, token signatures, and hash-only prior lineage. It contains no proposed translations or review dispositions.

The production caller scan covered {scanned} tracked JavaScript/TypeScript files and found {callerrefs} caller references / {callerocc} literal occurrences in {callerfiles} files. Callerless positions: {[x['position'] for x in contexts if not x['productionCallerCount']]}. The full 5,441-key queue matches the prior sealed queue byte-for-byte; W1623-W1642 immediately follows W1603-W1622 with no gap or overlap. Hash-only lineage reattests {len(priorwin)} prior locale cells, {len(prior_selections)} source selections, {len(prior_holds)} holds, and {len(applied)} applied targets against current catalogs. Prior translation text is omitted from lineage files.
''',encoding='utf-8')
    manifest={'artifact':'slskR PR #209 W1623-W1642 candidate-free exact-head input','repository':REPO_NAME,'pullRequest':PR,'head':HEAD,'tree':TREE,'headRef':BRANCH,'baseRef':'main','baseSha':BASE_SHA,
      'draft':True,'candidateFreeInputOnly':True,'proposedTranslationsIncluded':False,'selectedPositions':[START,END],'previousBoundaryPosition':START-1,'nextBoundaryPosition':END+1,
      'sourceCount':20,'localeCount':12,'cellCount':len(cells),'catalogSourceCount':len(keys),'localeOrder':LOCS,'sourceLookupKeyOrderSha256':orderhash,'sourceQueueCount':len(queue),'sourceQueueFileSha256':sha(queue_raw),
      'callerReferenceCount':callerrefs,'callerOccurrenceCount':callerocc,'callerFileCount':callerfiles,'callerResolutionHoldCount':len(caller_holds),'callerResolutionHoldPositions':[x['position'] for x in caller_holds],
      'carryForwardHoldCount':len(prior_holds),'carryForwardHoldUnchangedCount':sum(x['matchesLiveValue'] for x in prior_holds),'priorAppliedTargetHashCount':len(applied),'priorBackfillHashOnlyHoldCount':len(backfill),
      'priorSelectionReattestationCount':len(prior_selections),'priorWindowHashRecordCount':len(priorwin),'historicalSourceOrdinalsClaimed':False,'catalogFilesPinned':len(pins),'mismatchCounts':dict(mismatch),**dict(mismatch),
      'localWorktree':str(REPO),'localWorktreeHead':HEAD,'localWorktreeTree':TREE,'localWorktreeBranch':'(detached)','localWorktreeStatusClean':True,'priorApplicationReadbackSha256':sha(app_raw),
      'priorApplicationSummarySha256':sha((APP/'application-summary.json').read_bytes()),'createdAtUtc':datetime.now(timezone.utc).isoformat(timespec='seconds')}
    manifest['fileHashes']={p.name:{'sha256':sha(p.read_bytes()),'byteCount':p.stat().st_size} for p in sorted(R.iterdir()) if p.is_file() and p.name not in ('manifest.json','SHA256SUMS.txt')}
    wj(R/'manifest.json',manifest)
    manifest['fileHashes']={p.name:{'sha256':sha(p.read_bytes()),'byteCount':p.stat().st_size} for p in sorted(R.iterdir()) if p.is_file() and p.name not in ('manifest.json','SHA256SUMS.txt')}
    wj(R/'manifest.json',manifest)
    (R/'SHA256SUMS.txt').write_text(''.join(f'{sha(p.read_bytes())}  {p.name}\n' for p in sorted(R.iterdir()) if p.is_file() and p.name!='SHA256SUMS.txt'),encoding='utf-8')
    print(json.dumps({'result':'BUILT','head':HEAD,'tree':TREE,'sourceCount':len(selected),'cells':len(cells),'callerReferences':callerrefs,'callerOccurrences':callerocc,
      'callerFiles':callerfiles,'callerless':[x['position'] for x in caller_holds],'priorWindowHashes':len(priorwin),'priorSelectionHashes':len(prior_selections),'priorAppliedTargetHashes':len(applied),
      'priorHolds':len(prior_holds),'tokenMismatchCounts':dict(mismatch)},indent=2))

if __name__=='__main__': main()
