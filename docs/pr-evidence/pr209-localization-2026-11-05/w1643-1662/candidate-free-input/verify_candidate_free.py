#!/usr/bin/env python3
"""Verify the sealed candidate-free W1643-W1662 packet and hash-only history."""
from __future__ import annotations
import collections, hashlib, importlib.util, json, re, subprocess
from pathlib import Path

R=Path(__file__).resolve().parent; TASK=R.parent; REPO=TASK/'worktree'
PREV=TASK.parent/'slskr-pr209-w1623-1642-20261105'/'candidate-free-input'
APP=REPO/'docs/pr-evidence/pr209-localization-2026-11-05/w1623-1642/application'
HEAD='2d804c49879372071adf606bc2a2cf51e261fd94'; TREE='d6f5552d2400d868c2f2af98eb68caadfd4f3f66'
PREV_HEAD='7e366cbf21ad5490bd11ef418a0f2a98b3fbd567'; PREV_TREE='801d7a037c15dcd83b3e038160054a46c9b8f03b'
START,END=1643,1662; PREV_START,PREV_END=1623,1642
LOCS=['es','zh-Hans','hi','de','ja','fr','pt-BR','ar','ko','zh-Hant','vi','id']
sys_modules=__import__('sys'); sys_modules.dont_write_bytecode=True
spec=importlib.util.spec_from_file_location('schema_helper',R/'candidate-free-schema-helper.py')
h=importlib.util.module_from_spec(spec); spec.loader.exec_module(h); h.REPO=REPO; h.HEAD=HEAD; h.TREE=TREE; h.START=START; h.END=END; h.LOCS=LOCS

def sha(b):
    if isinstance(b,str): b=b.encode('utf-8')
    return hashlib.sha256(b).hexdigest()
def st(s): return sha(s.encode('utf-8'))
def canon(x): return json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':'))
def j(path): return json.loads(path.read_text(encoding='utf-8'))
def jl(path): return [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines() if line.strip()]
def require(ok,msg):
    if not ok: raise SystemExit('FAIL: '+msg)
def packet_sums(path):
    listed={}
    for line in (path/'SHA256SUMS.txt').read_text(encoding='utf-8').splitlines():
        if not line.strip(): continue
        digest,name=line.split(None,1); name=name.lstrip('* '); require(name not in listed,'duplicate checksum '+name); listed[name]=digest
    actual={p.relative_to(path).as_posix():sha(p.read_bytes()) for p in path.rglob('*') if p.is_file() and p.name!='SHA256SUMS.txt'}
    require(listed==actual,'checksum/file-set mismatch '+str(path)); return listed

def validate_context_rows(rows, queue, expected_window=None):
    qhash={i:st(k) for i,k in enumerate(queue,1)}
    for row in rows:
        pos=row['position']; key=queue[pos-1]
        require(row.get('sourceKey')==key and row.get('sourceKeySha256')==st(key),'caller source key '+str(pos))
        require(row.get('callerContextSha256')==sha(canon({'sourceKey':key,'callers':row['callers']})),'caller context hash '+str(pos))
        require(row.get('productionCallerCount')==len(row['callers']) and row.get('callerOccurrenceCount')==sum(c['literalOccurrenceCount'] for c in row['callers']),'caller counts '+str(pos))
        require(len(row['callers'])>0,'callerless text must not be present '+str(pos))
        for caller in row['callers']:
            path=REPO/caller['path']; raw=path.read_bytes(); lines=raw.decode('utf-8').splitlines()
            require(sha(raw)==caller['fileSha256'] and len(raw)==caller['fileBytes'],'caller file hash/size '+str(pos))
            require(subprocess.check_output(['git','-C',str(REPO),'rev-parse',f'HEAD:{caller["path"]}'],text=True).strip()==caller['gitBlob'],'caller git blob '+str(pos))
            require(1<=caller['line']<=len(lines) and lines[caller['line']-1]==caller['lineText'] and st(caller['lineText'])==caller['lineSha256'],'caller exact line '+str(pos))
            lo,hi=caller['contextStartLine'],caller['contextEndLine']
            expected=[{'line':n,'text':lines[n-1]} for n in range(lo,hi+1)]
            require(caller['context']==expected and sha(canon(expected))==caller['contextSha256'],'caller context lines '+str(pos))
            found=0
            for _,_,values in h.scan_quoted(caller['lineText']): found += sum(1 for v in values if v==key)
            require(found==caller['literalOccurrenceCount'],'caller literal occurrence '+str(pos))

# Verify packet inputs/output seals, including only the candidate-free input and previous application evidence.
packet_files=packet_sums(R); prev_files=packet_sums(PREV); app_files=packet_sums(APP)
manifest=j(R/'manifest.json'); prev_manifest=j(PREV/'manifest.json')
require(manifest['artifact']=='slskR PR #209 W1643-W1662 candidate-free exact-head input','artifact identity')
require(manifest['head']==HEAD and manifest['tree']==TREE and manifest['selectedPositions']==[START,END],'exact window pin')
require(manifest['candidateFreeInputOnly'] is True and manifest['proposedTranslationsIncluded'] is False,'candidate-free boundary')
require(not any('proposal' in p.name.lower() or 'review' in p.name.lower() for p in R.iterdir() if p.is_file()),'candidate-free packet contains no proposal/review artifacts')
require(manifest['fileHashes']=={p.name:{'sha256':sha(p.read_bytes()),'byteCount':p.stat().st_size} for p in sorted(R.iterdir()) if p.is_file() and p.name not in ('manifest.json','SHA256SUMS.txt')},'manifest file hashes')
require(prev_manifest['head']==PREV_HEAD and prev_manifest['tree']==PREV_TREE and prev_manifest['selectedPositions']==[PREV_START,PREV_END],'previous exact window pin')
require(set(prev_manifest['fileHashes'])==set(prev_files)-{'manifest.json'},'previous manifest file listing')
for name,pin in prev_manifest['fileHashes'].items():
    require(sha((PREV/name).read_bytes())==pin['sha256'] and (PREV/name).stat().st_size==pin['byteCount'],'previous packet file '+name)

# Verify initial and final live PR/API/branch/pull refs.
for name,api_file,refs_file,commit_file in [
 ('before','pr-api-before-extraction.json','remote-refs-before-extraction.txt','head-commit-before-extraction.json'),
 ('after','pr-api-after-extraction.json','remote-refs-after-extraction.txt','head-commit-after-extraction.json')]:
    pin=j(R/f'pin-{name}-extraction.json'); api=j(R/api_file); commit=j(R/commit_file); refs={}
    for line in (R/refs_file).read_text(encoding='utf-8').splitlines():
        digest,ref=line.split('\t'); refs[ref]=digest
    require(pin['result']=='PASS' and pin['headSha']==HEAD and pin['headTree']==TREE,'PR pin '+name)
    require(pin['headRef']=='codex/slskr-l10n-audit-20261104-resync' and pin['branchRefSha']==HEAD and pin['pullRefSha']==HEAD,'PR branch/pull '+name)
    require(api['state']=='open' and api['draft'] is True and api['head']['sha']==HEAD and api['base']['sha']=='1bbaec9fdc63a86de343e37e33bae70d44301a36','PR API state/head/base '+name)
    require(commit['sha']==HEAD and commit['tree']==TREE,'PR commit tree '+name)
    require(refs[f'refs/heads/{pin["headRef"]}']==HEAD and refs['refs/pull/209/head']==HEAD,'live remote refs '+name)
    require(pin['prApiSha256']==sha((R/api_file).read_bytes()) and pin['remoteRefsSha256']==sha((R/refs_file).read_bytes()),'PR evidence hashes '+name)
    require(pin['prBodySha256']==sha((api.get('body') or '').encode()),'PR body hash '+name)
require(j(R/'PR-attestation.json')['headSha']==HEAD and j(R/'PR-attestation-after.json')['headSha']==HEAD,'packet PR attestations')
require(j(R/'PR-attestation.json')['headTree']==TREE and j(R/'PR-attestation-after.json')['headTree']==TREE,'packet PR trees')
require(subprocess.check_output(['git','-C',str(REPO),'rev-parse','HEAD'],text=True).strip()==HEAD,'worktree HEAD')
require(subprocess.check_output(['git','-C',str(REPO),'rev-parse','HEAD^{tree}'],text=True).strip()==TREE,'worktree tree')
require(subprocess.check_output(['git','-C',str(REPO),'status','--porcelain=v1'],text=True).strip()=='','exact worktree clean')

# Verify live catalog source queue, pins, sorted selection, and new current cells.
catalogs={}; keys_by_locale=[]; catpins=j(R/'catalog-file-pins.json')['localeCatalogs']
for loc in LOCS:
    rel=f'web/src/lib/locales/ui-labels.{loc}.json'; raw=(REPO/rel).read_bytes(); data=json.loads(raw); catalogs[loc]=data; keys_by_locale.append(list(data)); pin=catpins[loc]
    require(pin['path']==rel and pin['sha256']==sha(raw) and pin['gitBlob']==subprocess.check_output(['git','-C',str(REPO),'rev-parse',f'HEAD:{rel}'],text=True).strip(),'catalog file pin '+loc)
    require(pin['orderedKeySha256']==st('\n'.join(data)+'\n') and pin['keyCount']==len(data)==5441,'catalog key order '+loc)
require(all(x==keys_by_locale[0] for x in keys_by_locale),'locale key order equality')
keys=sorted(keys_by_locale[0]); require(len(keys)==5441,'full source key count')
queue=jl(R/'source-queue.jsonl'); queue_bytes=''.join(canon(x)+'\n' for x in queue).encode('utf-8')
require(len(queue)==5441 and [x['position'] for x in queue]==list(range(1,5442)),'full queue positions')
require([x['sourceKey'] for x in queue]==keys and all(x['sourceKeySha256']==st(x['sourceKey']) for x in queue),'full queue key/hash order')
require(queue_bytes==(PREV/'source-queue.jsonl').read_bytes(),'full queue exact byte continuity')
source_order=j(R/'source-order-lineage.json')
require(sha(queue_bytes)==manifest['sourceQueueFileSha256']==source_order['completeSourceQueueSha256'],'source queue hash')
require(source_order['window']=='W1643-W1662' and source_order['selectedPositions']==list(range(START,END+1)) and source_order['positionsCoveredThrough']==END,'source order lineage')
selected=keys[START-1:END]
require((R/'selected-source-keys.txt').read_text(encoding='utf-8').splitlines()==selected,'selected source list')
boundaries=jl(R/'source-window-boundaries.jsonl')
require([x['position'] for x in boundaries]==list(range(START-1,END+2)),'window boundary positions')
require([x['sourceKey'] for x in boundaries]==keys[START-2:END+1],'window boundary source order')
require(j(R/'source-order-lineage.json')['gapPositions']==[] and j(R/'source-order-lineage.json')['overlapPositions']==[],'window continuity')
contexts=jl(R/'source-contexts.jsonl'); ctxmap={x['position']:x for x in contexts}
require(len(contexts)==20 and [x['position'] for x in contexts]==list(range(START,END+1)),'caller context rows')
validate_context_rows(contexts,keys)
require(manifest['callerReferenceCount']==sum(x['productionCallerCount'] for x in contexts),'caller reference count')
require(manifest['callerOccurrenceCount']==sum(x['callerOccurrenceCount'] for x in contexts),'caller occurrence count')
require(manifest['callerFileCount']==len({c['path'] for x in contexts for c in x['callers']}),'caller files count')
require(manifest['callerResolutionHoldCount']==0 and not jl(R/'caller-resolution-holds.jsonl'),'callerless rows')
source_pin=j(R/'source-pin-reattestation.json')
require(source_pin['head']==HEAD and source_pin['tree']==TREE and source_pin['selectedSourceCount']==20,'source pin')
require(source_pin['selectedCallerReferenceCount']==manifest['callerReferenceCount'] and source_pin['selectedCallerOccurrenceCount']==manifest['callerOccurrenceCount'] and source_pin['callerlessSelectedPositions']==[],'source caller pins')
runtime=j(R/'localization-runtime-context.json'); runtime_rel=runtime['pin']['path']; runtime_path=REPO/runtime_rel
require(runtime['pin']['sha256']==sha(runtime_path.read_bytes()) and runtime['pin']['gitBlob']==subprocess.check_output(['git','-C',str(REPO),'rev-parse',f'HEAD:{runtime_rel}'],text=True).strip(),'runtime localization pin')
cells=jl(R/'current-target-cells.jsonl')
require(len(cells)==240 and [(x['position'],x['locale']) for x in cells]==[(p,l) for p in range(START,END+1) for l in LOCS],'current cell coverage/order')
mismatch=collections.Counter()
for c in cells:
    p,loc=c['position'],c['locale']; key=keys[p-1]; ctx=ctxmap[p]; target=catalogs[loc][key]
    require(c['sourceKey']==key and c['sourceKeySha256']==st(key),'current source key '+str((p,loc)))
    require(c['sourceContextSha256']==ctx['callerContextSha256'] and c['callerCount']==ctx['productionCallerCount']>0,'current caller hash/count '+str((p,loc)))
    require(c['currentTarget']==target and c['currentTargetSha256']==st(target),'current target live catalog hash '+str((p,loc)))
    stoks,ttoks=h.toks(key),h.toks(target)
    require(c['sourcePlaceholders']==stoks[0] and c['currentTargetPlaceholders']==ttoks[0] and c['placeholderSequenceMatches']==(stoks[0]==ttoks[0]),'placeholder signature '+str((p,loc)))
    require(c['sourceMarkupTags']==stoks[1] and c['currentTargetMarkupTags']==ttoks[1] and c['markupMatches']==(stoks[1]==ttoks[1]),'markup signature '+str((p,loc)))
    require(c['sourceNumericTokens']==stoks[2] and c['currentTargetNumericTokens']==ttoks[2] and c['numericTokensMatch']==(stoks[2]==ttoks[2]),'numeric signature '+str((p,loc)))
    missing=[x for x in stoks[3] if x not in ttoks[3]]
    require(c['sourceProtectedLiterals']==stoks[3] and c['currentTargetProtectedLiterals']==ttoks[3] and c['protectedLiteralMismatchTokens']==missing and c['protectedLiteralsMatch']==(not missing),'protected literal signature '+str((p,loc)))
    mismatch['placeholderSequenceMismatchCount']+=stoks[0]!=ttoks[0]; mismatch['markupMismatchCount']+=stoks[1]!=ttoks[1]
    mismatch['numericTokenMismatchCount']+=stoks[2]!=ttoks[2]; mismatch['protectedLiteralMismatchCount']+=bool(missing)
require(dict(mismatch)==manifest['mismatchCounts'],'candidate token mismatch counts')

# Reattest the immediately prior caller contexts from the same pinned source tree.
old_contexts=jl(PREV/'source-contexts.jsonl'); validate_context_rows(old_contexts,keys)
require(len(old_contexts)==20 and [x['position'] for x in old_contexts]==list(range(PREV_START,PREV_END+1)),'previous caller context coverage')

# Reattest the W1623-W1642 application using hash-only final readback and current catalogs.
appout=j(APP/'apply-output.json'); app_product=j(APP/'product-commit-record.json'); app_rows=jl(APP/'final-readback.jsonl')
app_readback_raw=(APP/'final-readback.jsonl').read_bytes(); appsha=sha(app_readback_raw)
require(appout['result']=='PASS' and appout['finalReadbackSha256']==appsha,'prior application seal')
product=app_product['productCommit']; product_tree=app_product['productTree']
require(app_product['parent']==PREV_HEAD and subprocess.check_output(['git','-C',str(REPO),'rev-parse',product],text=True).strip()==product,'prior application commit')
require(subprocess.check_output(['git','-C',str(REPO),'rev-parse',f'{product}^{{tree}}'],text=True).strip()==product_tree,'prior product tree')
require(subprocess.call(['git','-C',str(REPO),'merge-base','--is-ancestor',product,HEAD])==0,'prior product ancestor')
commitpaths=set(subprocess.check_output(['git','-C',str(REPO),'diff-tree','--no-commit-id','--name-only','-r',product],text=True).splitlines())
require(commitpaths==set(appout['catalogPostimages']) and len(commitpaths)==10 and all(p.startswith('web/src/lib/locales/ui-labels.') and p.endswith('.json') for p in commitpaths),'prior product paths')
for p,digest in appout['catalogPostimages'].items(): require(sha((REPO/p).read_bytes())==digest,'prior catalog postimage '+p)
oldcells={(x['position'],x['locale']):x for x in jl(PREV/'current-target-cells.jsonl')}
oldctx={x['position']:x for x in old_contexts}; appmap={(x['position'],x['locale']):x for x in app_rows}
require(len(app_rows)==len(appmap)==240,'prior app readback count')
for pos in range(PREV_START,PREV_END+1):
    source=keys[pos-1]
    for loc in LOCS:
        r=appmap[(pos,loc)]; before=oldcells[(pos,loc)]['currentTargetSha256']; after=st(catalogs[loc][source])
        require(r['sourceKey']==source and r['sourceKeySha256']==st(source),'prior app source '+str((pos,loc)))
        require(r['sourceContextSha256']==oldctx[pos]['callerContextSha256'],'prior app caller '+str((pos,loc)))
        require(r['beforeTargetSha256']==before and r['afterTargetSha256']==after,'prior app target hashes '+str((pos,loc)))
        require(r['changed']==(before!=after),'prior app changed flag '+str((pos,loc)))
readback=jl(R/'prior-window-1623-1642-application-hash-only.jsonl')
require(len(readback)==240 and all('sourceKey' not in x and 'currentTarget' not in x and 'target' not in x for x in readback),'hash-only prior app lineage')
require(manifest['priorApplicationReadbackSha256']==appsha and manifest['priorProductCommit']==product and manifest['priorProductTree']==product_tree,'prior app summary pin')

# Reattest all inherited prior cells, selections, holds, and applied target hashes.
priorwin=jl(R/'prior-window-selection-hash-only.jsonl'); selections=jl(R/'prior-selection-hash-reattestation.jsonl')
holds=jl(R/'prior-hold-hash-reattestation.jsonl'); applied=jl(R/'prior-applied-target-hash-only.jsonl'); backfill=jl(R/'prior-backfill-hold-hash-only.jsonl')
require(len(priorwin)==2160 and len(selections)==400 and len(holds)==62 and len(applied)==95 and len(backfill)==10,'prior lineage counts')
require(manifest['priorWindowHashRecordCount']==len(priorwin) and manifest['priorSelectionReattestationCount']==len(selections) and manifest['carryForwardHoldCount']==len(holds) and manifest['carryForwardHoldUnchangedCount']==len(holds) and manifest['priorAppliedTargetHashCount']==len(applied),'prior manifest lineage counts')
for name in [p.name for p in R.glob('prior-*.jsonl')]:
    for row in jl(R/name):
        require(not any(k in row for k in ('sourceKey','sourceText','currentTarget','target','proposedTarget','targetText')),'prior lineage includes raw text '+name)
        pos=row.get('position')
        if row.get('sourceKeySha256') is not None: require(row.get('sourceKeyPositionMatches') is True and row['sourceKeySha256']==st(keys[pos-1]),'prior source position hash '+name)
        if row.get('matchesLiveQueue') is not None: require(row['matchesLiveQueue'] is True,'prior selection '+name)
        if row.get('expectedPriorTargetSha256') is not None:
            loc=row['locale']; actual=st(catalogs[loc][keys[pos-1]])
            require(actual==row['expectedPriorTargetSha256']==row['liveCatalogTargetSha256'] and row['liveMatchesExpectedPriorTarget'] is True,'prior target reattestation '+name)
        if row.get('matchesLiveValue') is not None:
            loc=row['locale']; actual=st(catalogs[loc][keys[pos-1]])
            require(actual==row['priorTargetSha256']==row['liveTargetSha256'] and row['matchesLiveValue'] is True,'prior hold reattestation '+name)
require(all(x['window']=='W1623-W1642' for x in readback),'prior app window label')
require(len([x for x in applied if x['window']=='W1623-W1642'])==13,'W1623 applied target hashes')
require(j(R/'prior-continuity-hash-summary.json')['previousWindowCells']['allMatchExpectedPriorTarget'] is True,'lineage summary target result')
require(j(R/'prior-continuity-hash-summary.json')['priorHolds']['unchangedCount']==62,'lineage summary hold count')
require(j(R/'prior-continuity-hash-summary.json')['priorSelections']['recordCount']==400,'lineage summary selection count')

print(json.dumps({'result':'PASS','head':HEAD,'tree':TREE,'selectedPositions':[START,END],'sourceCount':20,'cells':240,
 'callerReferences':manifest['callerReferenceCount'],'callerOccurrences':manifest['callerOccurrenceCount'],'callerFiles':manifest['callerFileCount'],
 'callerlessPositions':manifest['callerResolutionHoldPositions'],'priorWindowHashRows':len(priorwin),'priorSelections':len(selections),
 'priorAppliedTargetHashes':len(applied),'priorHolds':len(holds),'W1623AppliedCells':13,'W1623RetainedCells':227,
 'tokenMismatchCounts':dict(mismatch),'checksummedFiles':len(packet_files),'previousPacketFilesVerified':len(prev_files),'applicationFilesVerified':len(app_files)},indent=2))
