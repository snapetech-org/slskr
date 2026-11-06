#!/usr/bin/env python3
"""Build sealed candidate-free input for slskR PR #209 W1583-W1602."""
import hashlib, importlib.util, json, subprocess
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

R=Path(__file__).resolve().parent
REPO=Path('/mnt/disks/scratch/task-worktrees/localization-20261104/slskr-pr209-w1583-1602-source')
PREV=Path('/home/keith/Documents/code/task-scratch/slskr-pr209-w1563-1582-primary-20261104/candidate-free-input')
APP=REPO/'docs/pr-evidence/pr209-localization-2026-11-04/window-1563-1582/application'
HEAD='e1ccc3d6509baf957f3039046e5b66dda3ae15d0'
TREE='d7c7aa967cb7faf51a8211a397859feebe8129b8'
START,END=1583,1602
LOCS=['es','zh-Hans','hi','de','ja','fr','pt-BR','ar','ko','zh-Hant','vi','id']
REPO_NAME='snapetech-org/slskR'; PR=209; BRANCH='codex/slskr-l10n-audit-20261104-resync'; BASE_SHA='1bbaec9fdc63a86de343e37e33bae70d44301a36'
helper_path=R/'candidate-free-schema-helper.py'
spec=importlib.util.spec_from_file_location('schema_helper',helper_path)
h=importlib.util.module_from_spec(spec); spec.loader.exec_module(h)
h.R=R; h.REPO=REPO; h.PREV=PREV; h.APP=APP; h.HEAD=HEAD; h.TREE=TREE; h.START=START; h.END=END; h.LOCS=LOCS; h.REPO_NAME=REPO_NAME; h.PR=PR; h.BRANCH=BRANCH; h.BASE_SHA=BASE_SHA
sha,canon,wj,wjl=h.sha,h.canon,h.wj,h.wjl

def prior_lineage(catalogs,keys):
    qhash={i:sha(k) for i,k in enumerate(keys,1)}
    names=('prior-window-selection-hash-only.jsonl','prior-selection-hash-reattestation.jsonl','prior-hold-hash-reattestation.jsonl',
      'prior-window-1503-1522-catalog-diff-hash-only.jsonl','prior-window-1523-1542-application-hash-only.jsonl',
      'prior-window-1543-1562-application-hash-only.jsonl','prior-applied-target-hash-only.jsonl','prior-backfill-hold-hash-only.jsonl')
    pm=json.loads((PREV/'manifest.json').read_text(encoding='utf-8'))
    if (pm['head'],pm['tree'],pm['selectedPositions'])!=('f42c7e4be1f2bc9d63e13607d3c311d37f83f355','f6cb31394c01c90a784d543b8f43b04b232c8b37',[1563,1582]):
        raise RuntimeError('prior W1563 candidate-free packet pin changed')
    psums={}
    for line in (PREV/'SHA256SUMS.txt').read_text(encoding='utf-8').splitlines():
        d,n=line.split(None,1); psums[n.lstrip('* ')]=d
    pactual={x.name for x in PREV.iterdir() if x.is_file() and x.name!='SHA256SUMS.txt'}
    if set(psums)!=pactual or any(sha((PREV/n).read_bytes())!=d for n,d in psums.items()): raise RuntimeError('prior W1563 candidate-free checksums failed')
    old={n:[json.loads(s) for s in (PREV/n).read_text(encoding='utf-8').splitlines() if s] for n in names}
    oldwin,oldsel,oldholds=(old[names[i]] for i in range(3))
    old1503,old1523,old1543,oldapplied,oldbackfill=(old[n] for n in names[3:])
    sm=json.loads((PREV/'prior-continuity-hash-summary.json').read_text(encoding='utf-8'))
    oldcells={(x['position'],x['locale']):x for x in (json.loads(s) for s in (PREV/'current-target-cells.jsonl').read_text(encoding='utf-8').splitlines() if s)}
    oldctx={x['position']:x for x in (json.loads(s) for s in (PREV/'source-contexts.jsonl').read_text(encoding='utf-8').splitlines() if s)}
    queue=''.join(canon({'position':i,'sourceKey':k,'sourceKeySha256':sha(k),'historicalSourceOrdinal':None})+'\n' for i,k in enumerate(keys,1)).encode()
    oldqueue=(PREV/'source-queue.jsonl').read_bytes()
    if queue!=oldqueue: raise RuntimeError('source queue differs from prior sealed full queue')
    if (len(oldwin),len(oldsel),len(oldholds),len(old1503),len(old1523),len(old1543),len(oldapplied),len(oldbackfill))!=(1200,320,62,240,240,240,47,10):
        raise RuntimeError('prior W1563 lineage row counts changed')
    if sm['priorHolds']['recordCount']!=62 or sm['priorHolds']['unchangedCount']!=62: raise RuntimeError('prior hold ledger changed')
    def live(x):
        p,l=x['position'],x.get('locale')
        if qhash.get(p)!=x['sourceKeySha256'] or l not in catalogs: return None
        v=catalogs[l].get(keys[p-1]); return sha(v) if isinstance(v,str) else None
    def reattest(x):
        expected=x.get('expectedPriorTargetSha256') or x.get('priorResolvedTargetSha256') or x.get('observedAfterTargetSha256') or x.get('priorCurrentTargetSha256')
        actual=live(x); out={k:v for k,v in x.items() if k not in ('liveCatalogTargetSha256','liveMatchesExpectedPriorTarget')}
        out['expectedPriorTargetSha256']=expected; out['liveCatalogTargetSha256']=actual; out['liveMatchesExpectedPriorTarget']=actual is not None and actual==expected
        return out
    win=[reattest(x) for x in oldwin]
    if any(not x['liveMatchesExpectedPriorTarget'] for x in win): raise RuntimeError('an inherited prior-window target hash is stale')
    sel=[]
    for x in oldsel:
        ok=qhash.get(x['position'])==x['sourceKeySha256']
        if not ok: raise RuntimeError('an inherited source selection hash is stale')
        sel.append({'window':x.get('window'),'position':x['position'],'sourceKeySha256':x['sourceKeySha256'],'sourceKeyPositionMatches':True,'matchesLiveQueue':True})
    holds=[]
    for x in oldholds:
        actual=live(x); ok=actual is not None and actual==x.get('priorTargetSha256')
        if not ok: raise RuntimeError('an inherited review hold changed')
        holds.append({'window':x.get('window'),'position':x['position'],'sourceKeySha256':x['sourceKeySha256'],'sourceKeyPositionMatches':True,'locale':x['locale'],
          'priorTargetSha256':x.get('priorTargetSha256'),'liveTargetSha256':actual,'matchesLiveValue':True,'holdCategory':x.get('holdCategory'),'callerResolved':x.get('callerResolved')})
    apps={}
    for window,rows in (('W1503-W1522',old1503),('W1523-W1542',old1523),('W1543-W1562',old1543)):
        rows2=[reattest(x) for x in rows]
        if any(not x['liveMatchesExpectedPriorTarget'] for x in rows2): raise RuntimeError(f'{window} target hash no longer matches live catalog')
        apps[window]=rows2
    applied=[]
    for x in oldapplied:
        actual=live(x); expected=x.get('selectedTargetSha256') or x.get('observedAfterTargetSha256')
        if actual is None or actual!=expected: raise RuntimeError('an applied target hash is stale')
        applied.append({k:v for k,v in x.items() if k not in ('sourceKey','currentTarget','selectedTarget','observedAfterTarget','target')})
    report_path=APP/'apply-readback-report.json'; rows_path=APP/'apply-readback-cells.jsonl'
    report_raw,rows_raw=report_path.read_bytes(),rows_path.read_bytes(); report=json.loads(report_raw)
    rows=[json.loads(s) for s in rows_raw.decode('utf-8').splitlines() if s]
    report_sha,rows_sha=sha(report_raw),sha(rows_raw)
    if (report_sha,rows_sha)!=('d15957bb55f751384f27c0da5af663f540df9b4700b4f2f2325dda5e89bbd57f','1033b835394637d4045817bb46c7ecf1464948a580dcf4dd5d437706eda64c08'):
        raise RuntimeError('W1563 application report or readback bytes changed')
    if (report.get('inputHead'),report.get('inputTree'),report.get('productCommitParent'),report.get('productCommit'),report.get('productTree'),report.get('reviewedSourcePositions'),report.get('reviewedCells'),report.get('catalogChangesApplied'),report.get('outcomeCounts'))!=(
      'f42c7e4be1f2bc9d63e13607d3c311d37f83f355','f6cb31394c01c90a784d543b8f43b04b232c8b37','f42c7e4be1f2bc9d63e13607d3c311d37f83f355',
      '62e74939e7b8145055dbd77d83d2b5c3804d3b0b','9103c0870dc73bdf15737bcdecd522ba511bee5f',[1563,1582],240,18,
      {'apply-correction':16,'apply-refinement':2,'retain-accepted':222,'retain-hold':0}): raise RuntimeError('W1563 application report pins or counts changed')
    if (h.git('rev-parse',f"{report['productCommit']}^{{tree}}"),h.git('rev-parse',f"{report['productCommit']}^"))!=(report['productTree'],report['productCommitParent']): raise RuntimeError('prior product commit ancestry mismatch')
    if subprocess.call(['git','merge-base','--is-ancestor',report['productCommit'],HEAD],cwd=REPO)!=0: raise RuntimeError('prior product commit is not an ancestor of pinned head')
    if (h.git('rev-parse',f'HEAD:{report_path.relative_to(REPO).as_posix()}'),h.git('rev-parse',f'HEAD:{rows_path.relative_to(REPO).as_posix()}'))!=('cd9c15db581094723b06fbf2a3d5e1bd5a3abfc7','fce2912cafbbd7667a1ad5a60234969719e0fd27'):
        raise RuntimeError('prior application readback Git blobs changed')
    if len(rows)!=240: raise RuntimeError('prior application readback cell count changed')
    decisions=Counter(x['decision'] for x in rows)
    if decisions!=Counter({'retain-accepted':222,'apply-correction':16,'apply-refinement':2}): raise RuntimeError('prior application decisions changed')
    appended=[]; new_applied=[]
    for i,x in enumerate(rows):
        p,l=x['position'],x['locale']
        if (p,l)!=(1563+i//12,LOCS[i%12]): raise RuntimeError('prior application readback order changed')
        oldcell=oldcells.get((p,l))
        if oldcell is None or x['sourceKeySha256']!=qhash[p] or x['sourceKeySha256']!=oldcell['sourceKeySha256'] or x['sourceContextSha256']!=oldcell['sourceContextSha256'] or x['currentTargetSha256']!=oldcell['currentTargetSha256']:
            raise RuntimeError('prior application readback source/current pins mismatch')
        if not x.get('readbackMatches') or x['observedAfterTargetSha256']!=x['expectedAfterTargetSha256'] or sha(x['observedAfterTarget'])!=x['observedAfterTargetSha256']:
            raise RuntimeError('prior application after-target hash mismatch')
        if x['catalogPath']!=oldcell['catalogPath']: raise RuntimeError('prior application catalog path changed')
        update=x['decision'] in ('apply-correction','apply-refinement')
        if (x['decision']=='retain-accepted' and x['expectedAfterTargetSha256']!=x['currentTargetSha256']) or (update and x['expectedAfterTargetSha256']==x['currentTargetSha256']):
            raise RuntimeError('prior application disposition and target hash conflict')
        actual=live(x)
        if actual!=x['observedAfterTargetSha256']: raise RuntimeError('prior application result differs from live catalog')
        item={'window':'W1563-W1582','position':p,'sourceKeySha256':x['sourceKeySha256'],'locale':l,'priorDisposition':'applied-update' if update else 'accept-current',
          'priorCurrentTargetSha256':x['currentTargetSha256'],'priorResolvedTargetSha256':x['observedAfterTargetSha256'],
          'selectedTargetSha256':x['expectedAfterTargetSha256'] if update else None,'observedAfterTargetSha256':x['observedAfterTargetSha256'],
          'sourceContextSha256':x['sourceContextSha256'],'hashOnlyHold':False,'callerResolved':oldctx[p]['productionCallerCount']>0,
          'sourceKeyPositionMatches':True,'expectedPriorTargetSha256':x['observedAfterTargetSha256'],'liveCatalogTargetSha256':actual,'liveMatchesExpectedPriorTarget':True}
        appended.append(item)
        if update: new_applied.append({'window':'W1563-W1582','productCommit':report['productCommit'],'productTree':report['productTree'],'position':p,'locale':l,
          'sourceKeySha256':x['sourceKeySha256'],'sourceContextSha256':x['sourceContextSha256'],'selectedTargetSha256':x['expectedAfterTargetSha256'],
          'observedAfterTargetSha256':x['observedAfterTargetSha256'],'sourceKeyPositionMatches':True})
    if (len(appended),len(new_applied))!=(240,18): raise RuntimeError('prior application hash lineage totals mismatch')
    win.extend(appended)
    sel.extend({'window':'W1563-W1582','position':p,'sourceKeySha256':qhash[p],'sourceKeyPositionMatches':True,'matchesLiveQueue':True} for p in range(1563,1583))
    applied.extend(new_applied)
    prior_apps={'w1503':sm['priorApplications']['w1503'],'w1523':sm['priorApplications']['w1523'],'w1543':sm['priorApplications']['w1543'],
      'w1563':{'window':'W1563-W1582','parentHead':report['productCommitParent'],'productCommit':report['productCommit'],'productTree':report['productTree'],
        'readbackCellCount':len(rows),'readbackSha256':rows_sha,'applicationReportSha256':report_sha,'appliedTargetHashCount':18,'acceptCurrentCount':222,'hashOnlyHoldCount':0,
        'decisionCounts':dict(decisions),'holdReason':'none'},'appliedTargetHashCountTotal':len(applied)}
    summary={'lineageSource':str(PREV.resolve()),'lineageFiles':{n:sha((PREV/n).read_bytes()) for n in names},'priorInputManifestSha256':sha((PREV/'manifest.json').read_bytes()),
      'priorInputChecksumListSha256':sha((PREV/'SHA256SUMS.txt').read_bytes()),'applicationReadbackSha256':rows_sha,'applicationReportSha256':report_sha,
      'fullSourceOrderQueue':{'priorQueueSha256':sha(oldqueue),'liveQueueSha256':sha(queue),'exactBytesMatch':True,'positionsCoveredThrough':1582},
      'previousWindowCells':{'recordCount':len(win),'sourcePositionMatches':sum(x['sourceKeyPositionMatches'] for x in win),'allMatchExpectedPriorTarget':all(x['liveMatchesExpectedPriorTarget'] for x in win),
        'liveTargetMismatchCount':sum(not x['liveMatchesExpectedPriorTarget'] for x in win),'windowLabels':sorted({x.get('window') for x in win})},
      'priorSelections':{'recordCount':len(sel),'sourcePositionMatches':sum(x['sourceKeyPositionMatches'] for x in sel),'allMatchLiveQueue':all(x['matchesLiveQueue'] for x in sel),
        'sourcePositionMismatchCount':sum(not x['sourceKeyPositionMatches'] for x in sel)},
      'priorHolds':{'recordCount':len(holds),'sourcePositionMatches':sum(x['sourceKeyPositionMatches'] for x in holds),'unchangedCount':sum(x['matchesLiveValue'] for x in holds),
        'changedCount':sum(not x['matchesLiveValue'] for x in holds),'backfillCallerBackedHashOnlyHoldCount':sum(x.get('holdCategory')=='unresolved backfill terminology' and x.get('callerResolved') is True for x in holds),
        'newlyPreservedHoldCount':0},'priorApplications':prior_apps,'rawPriorTranslationsIncluded':False,'W1563AppliedHashesMatchLiveCatalog':True}
    return win,sel,holds,summary,apps['W1503-W1522'],apps['W1523-W1542'],apps['W1543-W1562'],appended,applied,oldbackfill

def main():
    if (h.git('rev-parse','HEAD'),h.git('rev-parse','HEAD^{tree}'))!=(HEAD,TREE): raise RuntimeError('exact source checkout pin mismatch')
    before=h.pr_attestation(datetime.now(timezone.utc).isoformat(timespec='seconds'))
    catalogs,pins,sets={},{},[]
    for loc in LOCS:
        path=f'web/src/lib/locales/ui-labels.{loc}.json'; f=REPO/path; raw=f.read_bytes(); data=json.loads(raw)
        if not isinstance(data,dict): raise RuntimeError('invalid catalog')
        catalogs[loc]=data; sets.append(set(data)); ks=list(data)
        pins[loc]={'path':path,'sha256':sha(raw),'gitBlob':h.git('rev-parse',f'HEAD:{path}'),'orderedKeySha256':sha('\n'.join(ks)+'\n'),'keyCount':len(ks)}
    if any(x!=sets[0] for x in sets) or any(list(catalogs[x])!=list(catalogs[LOCS[0]]) for x in LOCS[1:]): raise RuntimeError('locale catalog key sets/order differ')
    keys=sorted(sets[0]); orderhash=sha('\n'.join(keys)+'\n')
    if len(keys)!=5441 or keys[START-1]!='Failed to load forwarding status' or keys[END-1]!='Failed to load security data': raise RuntimeError('source queue or selected boundaries changed')
    queue=[{'position':p,'sourceKey':k,'sourceKeySha256':sha(k),'historicalSourceOrdinal':None} for p,k in enumerate(keys,1)]
    selected=keys[START-1:END]; boundaries=[{'position':p,'boundary':not START<=p<=END,'sourceKey':keys[p-1],'sourceKeySha256':sha(keys[p-1])} for p in range(START-1,END+2)]
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
    priorwin,priorsel,priorholds,prior_summary,app1503,app1523,app1543,app1563,applied,backfill=prior_lineage(catalogs,keys)
    runtime=h.runtime_context(); callerrefs=sum(x['productionCallerCount'] for x in contexts); callerocc=sum(x['callerOccurrenceCount'] for x in contexts)
    callerfiles=len({c['path'] for x in contexts for c in x['callers']})
    sourcepin={'repository':REPO_NAME,'pullRequest':PR,'head':HEAD,'tree':TREE,'selectedSourceCount':len(selected),'selectedCallerReferenceCount':callerrefs,
      'selectedCallerOccurrenceCount':callerocc,'callerlessSelectedPositions':[x['position'] for x in contexts if not x['productionCallerCount']],
      'trackedProductionJsTsFilesScanned':scanned,'uniqueSelectedCallerFiles':callerfiles,'catalogPaths':{l:p['path'] for l,p in pins.items()},
      'runtimePath':h.RUNTIME,'runtimeFileSha256':runtime['pin']['sha256'],'runtimeGitBlob':runtime['pin']['gitBlob'],'sourceLookupKeyCount':len(keys),'sourceLookupKeyOrderSha256':orderhash}
    wjl(R/'source-queue.jsonl',queue); wjl(R/'source-window-boundaries.jsonl',boundaries)
    (R/'selected-source-keys.txt').write_text(''.join(x+'\n' for x in selected),encoding='utf-8')
    wjl(R/'source-contexts.jsonl',contexts); wjl(R/'caller-resolution-holds.jsonl',caller_holds); wjl(R/'current-target-cells.jsonl',cells)
    wj(R/'catalog-file-pins.json',{'head':HEAD,'tree':TREE,'sourceLookupKeySetCount':len(keys),'sourceLookupKeyOrderSha256':orderhash,'localeCatalogs':pins})
    wjl(R/'catalog-structure.jsonl',[{'locale':l,**pins[l]} for l in LOCS]); wj(R/'localization-runtime-context.json',runtime); wj(R/'source-pin-reattestation.json',sourcepin)
    wjl(R/'prior-window-selection-hash-only.jsonl',priorwin); wjl(R/'prior-selection-hash-reattestation.jsonl',priorsel); wjl(R/'prior-hold-hash-reattestation.jsonl',priorholds)
    wj(R/'prior-continuity-hash-summary.json',prior_summary)
    wjl(R/'prior-window-1503-1522-catalog-diff-hash-only.jsonl',app1503); wjl(R/'prior-window-1523-1542-application-hash-only.jsonl',app1523)
    wjl(R/'prior-window-1543-1562-application-hash-only.jsonl',app1543); wjl(R/'prior-window-1563-1582-application-hash-only.jsonl',app1563)
    wjl(R/'prior-applied-target-hash-only.jsonl',applied); wjl(R/'prior-backfill-hold-hash-only.jsonl',backfill)
    wj(R/'source-order-lineage.json',{'window':'W1583-W1602','completeSourceQueueCount':len(queue),'completeSourceQueueSha256':sha((R/'source-queue.jsonl').read_bytes()),
      'sourceLookupKeyOrderSha256':orderhash,'previousWindow':'W1563-W1582','previousBoundaryPosition':START-1,'previousBoundarySourceKeySha256':sha(keys[START-2]),
      'selectedPositions':list(range(START,END+1)),'selectedSourceCount':len(selected),'nextBoundaryPosition':END+1,'nextBoundarySourceKeySha256':sha(keys[END]),
      'priorQueueSha256':prior_summary['fullSourceOrderQueue']['priorQueueSha256'],'priorQueueMatchesLiveQueue':True,'gapPositions':[],'overlapPositions':[],'positionsCoveredThrough':END})
    wj(R/'PR-attestation.json',before); wj(R/'PR-attestation-after.json',h.pr_attestation(datetime.now(timezone.utc).isoformat(timespec='seconds')))
    (R/'README.md').write_text(f'''# slskR PR #209 W1583-W1602 candidate-free input\n\nExact PR head {HEAD}, tree {TREE}; PR open/draft state and branch/pull refs were captured before and after extraction. Selected sorted source positions {START}-{END}: 20 source keys by 12 locales (240 current-target cells).\n\nThis packet contains source keys, current catalog targets, exact caller contexts, runtime lookup/placeholder context, integrity pins, token signatures, and hash-only prior lineage. It contains no proposed translations or review dispositions.\n\nThe production caller scan covered {scanned} tracked JavaScript/TypeScript files and found {callerrefs} caller references / {callerocc} literal occurrences in {callerfiles} files. Callerless positions: {[x['position'] for x in contexts if not x['productionCallerCount']]}. The complete 5,441-key queue matches the prior frozen queue byte-for-byte; W1583-W1602 immediately follows W1563-W1582 with no gap or overlap. Hash-only lineage reattests {len(priorwin)} prior locale cells, {len(priorsel)} source selections, {len(priorholds)} holds, and {len(applied)} applied targets against current catalogs. Prior translation text is not included in lineage files.\n''',encoding='utf-8')
    manifest={'artifact':'slskR PR #209 W1583-W1602 candidate-free exact-head input','repository':REPO_NAME,'pullRequest':PR,'head':HEAD,'tree':TREE,'headRef':BRANCH,'baseRef':'main','baseSha':BASE_SHA,
      'draft':True,'candidateFreeInputOnly':True,'proposedTranslationsIncluded':False,'selectedPositions':[START,END],'previousBoundaryPosition':START-1,'nextBoundaryPosition':END+1,
      'sourceCount':20,'localeCount':12,'cellCount':len(cells),'catalogSourceCount':len(keys),'localeOrder':LOCS,'sourceLookupKeyOrderSha256':orderhash,'sourceQueueCount':len(queue),
      'sourceQueueFileSha256':sha((R/'source-queue.jsonl').read_bytes()),'callerReferenceCount':callerrefs,'callerOccurrenceCount':callerocc,'callerFileCount':callerfiles,
      'callerResolutionHoldCount':len(caller_holds),'callerResolutionHoldPositions':[x['position'] for x in caller_holds],'carryForwardHoldCount':len(priorholds),
      'carryForwardHoldUnchangedCount':sum(x['matchesLiveValue'] for x in priorholds),'priorAppliedTargetHashCount':len(applied),'priorBackfillHashOnlyHoldCount':len(backfill),
      'priorSelectionReattestationCount':len(priorsel),'priorWindowHashRecordCount':len(priorwin),'historicalSourceOrdinalsClaimed':False,'catalogFilesPinned':len(pins),
      'mismatchCounts':dict(mismatch),**dict(mismatch),'localWorktree':str(REPO),'localWorktreeHead':HEAD,'localWorktreeTree':TREE,'localWorktreeBranch':'(detached)',
      'localWorktreeStatusClean':True,'priorApplicationReadbackSha256':prior_summary['applicationReadbackSha256'],'priorApplicationReportSha256':prior_summary['applicationReportSha256'],
      'createdAtUtc':datetime.now(timezone.utc).isoformat(timespec='seconds')}
    manifest['fileHashes']={p.name:{'sha256':sha(p.read_bytes()),'byteCount':p.stat().st_size} for p in sorted(R.iterdir()) if p.is_file() and p.name not in ('manifest.json','SHA256SUMS.txt')}
    wj(R/'manifest.json',manifest)
    manifest['fileHashes']={p.name:{'sha256':sha(p.read_bytes()),'byteCount':p.stat().st_size} for p in sorted(R.iterdir()) if p.is_file() and p.name not in ('manifest.json','SHA256SUMS.txt')}
    wj(R/'manifest.json',manifest)
    sums=[f'{sha(p.read_bytes())}  {p.name}' for p in sorted(R.iterdir()) if p.is_file() and p.name!='SHA256SUMS.txt']
    (R/'SHA256SUMS.txt').write_text('\n'.join(sums)+'\n',encoding='utf-8')
    print(json.dumps({'result':'BUILT','head':HEAD,'tree':TREE,'sourceCount':len(selected),'cells':len(cells),'callerReferences':callerrefs,'callerOccurrences':callerocc,
      'callerFiles':callerfiles,'callerless':[x['position'] for x in caller_holds],'priorWindowHashes':len(priorwin),'priorSelectionHashes':len(priorsel),
      'priorAppliedTargetHashes':len(applied),'priorHolds':len(priorholds),'tokenMismatchCounts':dict(mismatch)},indent=2))

if __name__=='__main__': main()
