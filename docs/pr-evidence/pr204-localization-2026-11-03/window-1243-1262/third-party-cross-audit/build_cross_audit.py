#!/usr/bin/env python3
"""Rebuild the slskR PR #204 W1243-W1262 cross-audit from sealed evidence."""
from __future__ import annotations
import collections, datetime, hashlib, json, pathlib, re, subprocess, sys

ROOT=pathlib.Path(__file__).resolve().parent
INPUT=ROOT/'input'; PRIMARY=ROOT/'primary-review'; BLIND=ROOT/'independent-blind-review'
REPO_WT=pathlib.Path('/mnt/disks/scratch/task-worktrees/localization-20261103/slskr-pr204-w1223-evidence-20261103')
HEAD='ce2e7d12f3025f0312df37527b4c270d0eb5bce5'; TREE='0ead1eb1678b4df05ca7feec9776c0319d4eefd3'
REPO='snapetech-org/slskR'; PR=204; BRANCH='codex/slskr-l10n-audit-20261030'; START=1243; END=1262

def read_json(path): return json.loads(path.read_text(encoding='utf-8'))
def read_jsonl(path): return [json.loads(l) for l in path.read_text(encoding='utf-8').splitlines() if l.strip()]
def sha_bytes(b): return hashlib.sha256(b).hexdigest()
def sha_text(s): return sha_bytes(s.encode('utf-8'))
def canonical(x): return json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':'))
def verify_checksums(directory):
    r=subprocess.run(['sha256sum','-c','SHA256SUMS.txt'],cwd=directory,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
    if r.returncode: raise SystemExit(f'checksum failure in {directory}:\n{r.stdout}')
def git(*args): return subprocess.check_output(['git','-C',str(REPO_WT),*args])
def git_bytes_at(path): return subprocess.check_output(['git','-C',str(REPO_WT),'show',f'{HEAD}:{path}'])

for d in (INPUT,PRIMARY,BLIND): verify_checksums(d)
manifest=read_json(INPUT/'manifest.json'); att=read_json(INPUT/'PR-attestation.json'); pins=read_json(INPUT/'catalog-file-pins.json')
primary_summary=read_json(PRIMARY/'summary.json'); blind_provenance=read_json(BLIND/'provenance.json')
primary=read_jsonl(PRIMARY/'ledger.jsonl'); blind=read_jsonl(BLIND/'sealed-ledger.jsonl'); cells=read_jsonl(INPUT/'current-target-cells.jsonl'); contexts=read_jsonl(INPUT/'source-contexts.jsonl'); queue=read_jsonl(INPUT/'source-queue.jsonl')
assert manifest['repository']==REPO and manifest['pullRequest']==PR and manifest['head']==HEAD and manifest['tree']==TREE
assert manifest['candidateFreeInputOnly'] is True and manifest['proposedTranslationsIncluded'] is False
assert att['headRefOid']==HEAD and att['commitApiTree']==TREE and att['remoteBranchHead']==HEAD and att['remotePullRefHead']==HEAD
assert pins['head']==HEAD and pins['tree']==TREE and pins['sourceLookupKeySetCount']==5441
assert primary_summary['head']==HEAD and primary_summary['tree']==TREE and primary_summary['cellCount']==240
assert blind_provenance['pullRequest']['headRefOid']==HEAD and blind_provenance['pullRequest']['tree']==TREE and blind_provenance['reviewType']=='independent blind semantic review' and 'did not open the primary ledger' in blind_provenance['inputPolicy'].lower()
assert manifest['selectedPositions']==[START,END] and len(cells)==240 and len(primary)==240 and len(blind)==240 and len(contexts)==20
assert len(queue)==5441 and len({(r['position'],r['locale']) for r in cells})==240

# Reattest the volatile PR and both remote refs at cross-audit time.
pr=json.loads(subprocess.check_output(['gh','api',f'repos/{REPO}/pulls/{PR}'],text=True))
assert pr['state']=='open' and pr['draft'] is True and pr['head']['sha']==HEAD and pr['head']['ref']==BRANCH
remote=subprocess.check_output(['git','ls-remote',f'https://github.com/{REPO}.git',f'refs/heads/{BRANCH}',f'refs/pull/{PR}/head'],text=True)
remote_refs={line.split('\t')[1]:line.split('\t')[0] for line in remote.splitlines()}
assert remote_refs.get(f'refs/heads/{BRANCH}')==HEAD and remote_refs.get(f'refs/pull/{PR}/head')==HEAD,remote_refs
assert git('rev-parse','HEAD').decode().strip()==HEAD and git('rev-parse','HEAD^{tree}').decode().strip()==TREE
assert not git('status','--porcelain').decode().strip(),'pinned worktree is not clean'

key=lambda r:(r['position'],r['locale'])
cur_by={key(x):x for x in cells}; p_by={key(x):x for x in primary}; b_by={key(x):x for x in blind}; ctx_by={x['position']:x for x in contexts}
queue_by={x['position']:x for x in queue}
assert all(len(m)==240 for m in (cur_by,p_by,b_by))

# Verify live catalog bytes, ordered key sets, source queue entries, exact caller lines,
# runtime lookup code, and all current target values from the exact PR commit.
locale_order=manifest['localeOrder']; catalogs={}; catalog_raw={}
for locale in locale_order:
    path=pins['localeCatalogs'][locale]['path']; raw=git_bytes_at(path)
    assert sha_bytes(raw)==pins['localeCatalogs'][locale]['sha256']
    assert git('rev-parse',f'{HEAD}:{path}').decode().strip()==pins['localeCatalogs'][locale]['gitBlob']
    catalogs[locale]=json.loads(raw.decode('utf-8')); catalog_raw[locale]=raw
assert all(list(catalogs[locale])==list(catalogs[locale_order[0]]) for locale in locale_order)
assert len(catalogs[locale_order[0]])==5441
runtime=pins['localeRuntime']; runtime_raw=git_bytes_at(runtime['path'])
assert sha_bytes(runtime_raw)==runtime['sha256'] and git('rev-parse',f"{HEAD}:{runtime['path']}").decode().strip()==runtime['gitBlob']
for pos in range(START,END+1):
    c=ctx_by[pos]
    q=queue_by[pos]
    assert q['sourceKey']==c['sourceKey'] and q['sourceKeySha256']==c['sourceKeySha256']
    assert sha_text(c['sourceKey'])==c['sourceKeySha256']
    refs=c['references']
    assert len(refs)==c['callerReferenceCount']
    for ref in refs:
        file_lines=git_bytes_at(ref['path']).decode('utf-8').splitlines()
        assert 1<=ref['line']<=len(file_lines)
        exact=file_lines[ref['line']-1]
        context_lines=ref['contextLines']
        exact_pin=next(item for item in context_lines if item['line']==ref['line'])
        assert sha_text(exact)==exact_pin['lineSha256']
        assert all(file_lines[item['line']-1]==item['text'] and sha_text(item['text'])==item['lineSha256'] for item in context_lines)
        assert sha_text('\n'.join(item['text'] for item in context_lines))==ref['contextSha256']
    for locale in locale_order:
        ccell=cur_by[(pos,locale)]
        assert ccell['sourceKey']==c['sourceKey'] and ccell['sourceKeySha256']==c['sourceKeySha256']
        assert catalogs[locale][c['sourceKey']]==ccell['currentTarget']
        assert sha_text(ccell['currentTarget'])==ccell['currentTargetSha256']
        assert ccell['catalogSha256']==sha_bytes(catalog_raw[locale])
        assert ccell['catalogGitBlob']==git('rev-parse',f"{HEAD}:{ccell['catalogPath']}").decode().strip()

# Candidate-free cross-audit overrides that address independently documented blind findings
# or strict source/runtime fidelity. No override introduces a source-incompatible token.
custom={
 (1243,'vi'):{'target':'Chạy thử (xem trước các thay đổi mà không cần áp dụng)','disposition':'refinement','rationale':'The current “Chạy khô” is a literal calque. “Chạy thử” is the clearer trial-run label while retaining the preview-without-application meaning.'},
 (1245,'zh-Hans'):{'target':None,'disposition':'refinement','replace':[('候选者','候选项')],'rationale':'The approved Discovery Inbox candidate is a content item, not a person. Use the item sense and retain the exact feature name “Discovery Inbox”.'},
 (1245,'hi'):{'target':'स्वीकृत Discovery Inbox आइटम से ड्राई-रन योजना बनाई गई। किसी भी नेटवर्क गतिविधि से पहले समीक्षा और स्पष्ट निष्पादन अभी भी आवश्यक है।','disposition':'refinement','rationale':'Preserve the exact feature name and describe its approved Discovery Inbox candidate as an item rather than a person.'},
 (1245,'zh-Hant'):{'target':None,'disposition':'refinement','replace':[('候選者','候選項')],'rationale':'The approved Discovery Inbox candidate is a content item, not a person. Use the item sense and retain the exact feature name “Discovery Inbox”.'},
 (1245,'vi'):{'target':'Kế hoạch chạy thử được tạo từ một mục ứng viên đã được phê duyệt trong Discovery Inbox. Cần xem xét và thực thi rõ ràng trước mọi hoạt động mạng.','disposition':'refinement','rationale':'Preserve the exact “Discovery Inbox” feature name and describe its candidate as an item. The required review and explicit execution before network activity remain intact.'},
 (1247,'vi'):{'target':'Số mục trùng lặp được phát hiện:','disposition':'refinement','rationale':'The caller appends a duplicate-hash count. The current “các bản sao” reads as copies; this label identifies the detected duplicate items.'},
 (1248,'vi'):{'target':'Thời lượng','disposition':'refinement','rationale':'The caller labels a measured duration statistic. “Khoảng thời gian” suggests an interval; “Thời lượng” names the time taken.'},
 (1251,'vi'):{'target':'Thời lượng:','disposition':'refinement','rationale':'The callers append either seconds or milliseconds after this generic label. “Thời lượng” names duration without adding a unit.'},
 (1258,'hi'):{'target':'कड़ियाँ','disposition':'refinement','rationale':'The exact caller displays a graph-edge count. “कड़ियाँ” names links between graph nodes; the current word can mean outer borders.'},
 (1260,'id'):{'target':'Sunting Opsi','disposition':'refinement','rationale':'Use the established Indonesian edit verb “Sunting”, matching the direct “Edit” entry in this same catalog.'},
 (1261,'id'):{'target':'Sunting catatan pengguna','disposition':'refinement','rationale':'Use the established Indonesian edit verb “Sunting”, matching the direct “Edit” entry in this same catalog.'},
 (1262,'id'):{'target':'Sunting item Daftar keinginan','disposition':'refinement','rationale':'Use the established Indonesian edit verb “Sunting” and the same catalog’s translation of “Wishlist” as “Daftar keinginan”.'},
}

placeholder_re=r'\{[A-Za-z][A-Za-z0-9_]*\}'; markup_re=r'<[^>]+>'; numeric_re=r'(?<![A-Za-z])\d+(?:[.,]\d+)*(?![A-Za-z])'; entity_re=r'&(?:#\d+|#x[0-9A-Fa-f]+|[A-Za-z][A-Za-z0-9]+);'
output=[]; final_counts=collections.Counter(); position_summary={}; mismatches=collections.Counter()
for cell_key in sorted(cur_by):
    c=cur_by[cell_key]; p=p_by[cell_key]; b=b_by[cell_key]; pos,locale=cell_key
    assert (p.get('head'),p.get('tree'),p.get('repository'),p.get('pullRequest'))==(HEAD,TREE,REPO,PR)
    assert p['sourceKey']==c['sourceKey'] and p['sourceKeySha256']==c['sourceKeySha256']
    assert p['currentTarget']==c['currentTarget'] and p['currentTargetSha256']==c['currentTargetSha256']
    assert p['catalogPath']==c['catalogPath'] and p['catalogSha256']==c['catalogSha256'] and p['catalogGitBlob']==c['catalogGitBlob']
    assert b['sourceKey']==c['sourceKey'] and b['sourceKeySha256']==c['sourceKeySha256']
    assert b['currentTarget']==c['currentTarget'] and b['currentTargetSha256']==c['currentTargetSha256']
    pdisp=p['recommendation']; bdisp={'accepted':'accept-current','held':'hold'}.get(b['disposition'],b['disposition'])
    assert pdisp in ('accept-current','correction','refinement','hold')
    if pdisp!=bdisp: mismatches['rawNormalizedDispositionMismatch']+=1
    extra=custom.get(cell_key)
    caller_hold=(c['sourceCallerCount']==0)
    if caller_hold:
        assert pos==1257 and locale in locale_order and pdisp=='hold' and b['disposition']=='held'
        final_disp='hold'; selected=None; cross_rationale='Retain the no-caller hold: the pinned exact-key scan found no caller for this catalog-only label. Primary and blind reviews agree; no translation target is selected until caller context is resolved.'
        reconciliation='Both reviews held the current value because the exact source key has zero pinned caller references.'
    elif extra:
        selected=extra['target']
        if selected is None:
            selected=c['currentTarget']
            for old,new in extra['replace']:
                assert old in selected,(cell_key,old,selected)
                selected=selected.replace(old,new)
        final_disp=extra['disposition']; cross_rationale=extra['rationale']
        reconciliation='Cross-audit incorporates the blind reviewer’s caller-specific concern, adding a supported refinement absent from the primary proposal.'
    elif pdisp in ('correction','refinement'):
        selected=p['recommendedTarget']; final_disp=pdisp
        if pos in (1252,1253,1254,1256):
            assert '(API' in c['currentTarget'] or 'campos de API' in c['currentTarget'] or 'حقول API' in c['currentTarget'] or 'trường API' in c['currentTarget'] or 'API-Felder' in c['currentTarget'] or 'champs API' in c['currentTarget'] or 'APIフィールド' in c['currentTarget'] or 'API 필드' in c['currentTarget'] or 'API 字段' in c['currentTarget'] or 'API 欄位' in c['currentTarget'] or 'API फ़ील्ड' in c['currentTarget'] or 'kolom API' in c['currentTarget']
            assert 'API' not in selected and 'API-Felder' not in selected and 'champs API' not in selected and 'campos de API' not in selected and 'حقول API' not in selected and 'trường API' not in selected and 'APIフィールド' not in selected and 'API 필드' not in selected
            cross_rationale='The pinned authored server string and browser allowlist contain only the user-facing validation sentence. The current target adds API field names absent from the source; remove that implementation-detail suffix while preserving the translated requirement and protected literal. The blind review accepted the extra hint as non-contradictory, but cross-audit keeps this message source-bound.'
            reconciliation='Primary correction selected after cross-audit; blind acceptance applied to the old current target, whose API-field suffix is not present in the pinned source/caller text.'
        elif bdisp in ('correction','refinement'):
            cross_rationale=f"Both reviews flag a wording issue in the current target. The selected primary candidate resolves it in the exact pinned caller context. {p['rationale']}"
            reconciliation='Primary candidate selected; blind independently flagged the same current-target issue.'
        else:
            cross_rationale=f"The blind review accepted the current value, but the primary candidate addresses a caller-specific terminology or grammar issue confirmed by the pinned source context. {p['rationale']}"
            reconciliation='Primary candidate selected after cross-audit; blind acceptance assessed only the old current target and did not see this candidate.'
    else:
        selected=c['currentTarget']; final_disp='accept-current'
        cross_rationale='Accept the current target. The exact caller context and source meaning support it; both reviews found no change necessary.'
        reconciliation='Primary and independent blind review agree on the current target.'

    if final_disp=='hold':
        assert selected is None
    else:
        assert isinstance(selected,str)
        if not extra and pdisp in ('correction','refinement'):
            assert selected==p['recommendedTarget']
            assert sha_text(selected)==p['recommendedTargetSha256']
        if final_disp=='accept-current': assert selected==c['currentTarget']
    source_ph=re.findall(placeholder_re,c['sourceKey']); curr_ph=re.findall(placeholder_re,c['currentTarget']); selected_ph=re.findall(placeholder_re,selected) if selected is not None else None
    source_markup=re.findall(markup_re,c['sourceKey']); curr_markup=re.findall(markup_re,c['currentTarget']); selected_markup=re.findall(markup_re,selected) if selected is not None else None
    source_nums=re.findall(numeric_re,c['sourceKey']); curr_nums=re.findall(numeric_re,c['currentTarget']); selected_nums=re.findall(numeric_re,selected) if selected is not None else None
    source_entities=re.findall(entity_re,c['sourceKey']); selected_entities=re.findall(entity_re,selected) if selected is not None else None
    assert source_ph==c['sourcePlaceholders'] and curr_ph==c['currentTargetPlaceholders']
    if selected is not None:
        assert selected_ph==source_ph,(cell_key,source_ph,selected_ph)
        assert selected_markup==source_markup,(cell_key,source_markup,selected_markup)
        assert selected_nums==source_nums,(cell_key,source_nums,selected_nums)
        assert selected_entities==source_entities,(cell_key,source_entities,selected_entities)
        assert selected==selected.strip()
    protected=list(p['protectedLiteralCheck']['requiredLiterals'])
    if pos==1245 and locale in ('hi','vi','zh-Hans','zh-Hant'): protected.append('Discovery Inbox')
    if pos==1246: protected.append('ReplayGain')
    if pos==1252: protected.append('ContentID')
    protected=sorted(set(protected))
    if selected is not None:
        assert all(lit in selected for lit in protected),(cell_key,protected,selected)
    semantic_unit=p.get('semanticUnitCheck') or {}
    unit=semantic_unit.get('unit')
    unit_markers=semantic_unit.get('acceptedLocaleMarkers',[])
    unit_pass=(unit is None) or any(marker.lower() in selected.lower() for marker in unit_markers)
    if selected is not None and unit is not None: assert unit_pass,(cell_key,unit,unit_markers,selected)
    source_context=ctx_by[pos]
    caller_refs=[]
    for ref in source_context['references']:
        line=next(x for x in ref['contextLines'] if x['line']==ref['line'])
        primary_ref=next(x for x in p['callerEvidence'] if x['path']==ref['path'] and x['line']==ref['line'] and x['contextSha256']==ref['contextSha256'])
        caller_refs.append({'path':ref['path'],'line':ref['line'],'lineText':line['text'],'lineSha256':line['lineSha256'],'contextSha256':ref['contextSha256'],'referenceScope':primary_ref['referenceScope'],'role':ref['role']})
    assert len(caller_refs)==c['sourceCallerCount']
    caller_hold_reason=p.get('callerHoldReason')
    runtime_pin=pins['localeRuntime']; q=queue_by[pos]
    queue_hash=sha_bytes(json.dumps(q,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode('utf-8'))
    row={
      'schemaVersion':1,'repository':REPO,'pullRequest':PR,'head':HEAD,'tree':TREE,'window':'W1243-W1262','position':pos,'locale':locale,
      'source':{'sourceKey':c['sourceKey'],'sha256':c['sourceKeySha256'],'queueEntrySha256':queue_hash,'selectionRule':manifest['selectionRule']},
      'currentTarget':{'text':c['currentTarget'],'sha256':c['currentTargetSha256']},
      'selectedTarget':None if selected is None else {'text':selected,'sha256':sha_text(selected)},
      'disposition':final_disp,'confidence':'high' if final_disp=='hold' or (pos in (1252,1253,1254,1256)) else ('moderate' if final_disp in ('correction','refinement') else p['confidence']),
      'rationale':None if final_disp=='hold' else (extra['rationale'] if extra else p['rationale']),
      'crossAuditRationale':cross_rationale,
      'evidence':{
        'caller':{'referenceCount':c['sourceCallerCount'],'nonTestPathReferenceCount':p['callerNonTestPathReferenceCount'],'testOnlyReferenceCount':p['callerTestOnlyReferenceCount'],'resolutionHold':bool(p.get('callerHold')),'holdReason':caller_hold_reason if caller_hold else None,'references':caller_refs,'scopeNote':'Source-context references are pinned to exact caller lines; reference-scope classification is inherited from the primary ledger and cross-checked against caller evidence.'},
        'catalog':{'path':c['catalogPath'],'currentFileSha256':c['catalogSha256'],'currentFileGitBlob':c['catalogGitBlob'],'head':HEAD,'tree':TREE},
        'localeLookupRuntime':{'path':runtime_pin['path'],'sha256':runtime_pin['sha256'],'gitBlob':runtime_pin['gitBlob'],'head':HEAD,'tree':TREE},
        'placeholders':{'sourceSequence':source_ph,'currentTargetSequence':curr_ph,'selectedTargetSequence':selected_ph,'selectedTargetPass':selected is not None and selected_ph==source_ph},
        'markupTokens':{'source':source_markup,'currentTarget':curr_markup,'selectedTarget':selected_markup,'selectedTargetPass':selected is not None and selected_markup==source_markup},
        'numericTokens':{'source':source_nums,'currentTarget':curr_nums,'selectedTarget':selected_nums,'selectedTargetPass':selected is not None and selected_nums==source_nums},
        'entityTokens':{'source':source_entities,'selectedTarget':selected_entities,'selectedTargetPass':selected is not None and selected_entities==source_entities},
        'protectedLiterals':{'required':protected,'currentTargetPreserves':all(lit in c['currentTarget'] for lit in protected),'selectedTargetPreserves':None if selected is None else all(lit in selected for lit in protected)},
        'semanticUnit':semantic_unit|{'crossAuditSelectedTargetContainsUnit':unit_pass if selected is not None and unit is not None else None}
      },
      'reviewLineage':{
        'primaryDisposition':pdisp,'primaryConfidence':p['confidence'],'primaryRecommendedTarget':p.get('recommendedTarget'),'primaryRecommendedTargetSha256':p.get('recommendedTargetSha256'),'primaryRationale':p['rationale'],
        'blindDispositionOnCurrentTarget':b['disposition'],'blindConfidence':b['confidence'],'blindRationaleOnCurrentTarget':b['rationale'],'blindSawSelectedCandidate':False,'blindReleaseApproved':False,
        'reconciliation':reconciliation
      },
      'qualifiedLocaleReviewRequiredBeforeRelease':True,'releaseApprovedByThisCrossAudit':False
    }
    output.append(row); final_counts[final_disp]+=1
    position_summary.setdefault(str(pos),{'sourceKey':c['sourceKey'],'finalDispositions':collections.Counter(),'primaryDispositions':collections.Counter(),'blindDispositions':collections.Counter(),'changedCells':0})
    ps=position_summary[str(pos)]; ps['finalDispositions'][final_disp]+=1; ps['primaryDispositions'][pdisp]+=1; ps['blindDispositions'][b['disposition']]+=1
    ps['changedCells']+=int(selected is not None and selected!=c['currentTarget'])

assert len(output)==240 and len({(x['position'],x['locale']) for x in output})==240
assert final_counts=={'accept-current':127,'correction':81,'refinement':20,'hold':12},final_counts
assert sum(1 for x in output if x['selectedTarget'] and x['selectedTarget']['text']!=x['currentTarget']['text'])==101
assert all(x['selectedTarget'] is None for x in output if x['position']==1257)
assert all(x['selectedTarget'] is not None for x in output if x['position']!=1257)

(ROOT/'cross-audit-ledger.jsonl').write_text(''.join(canonical(x)+'\n' for x in output),encoding='utf-8')
serialized={k:{'sourceKey':v['sourceKey'],'finalDispositions':dict(v['finalDispositions']),'primaryDispositions':dict(v['primaryDispositions']),'blindDispositions':dict(v['blindDispositions']),'changedCells':v['changedCells']} for k,v in position_summary.items()}
normalize_blind={'accepted':'accept-current','held':'hold'}
matrix=collections.Counter((x['reviewLineage']['primaryDisposition'],normalize_blind.get(x['reviewLineage']['blindDispositionOnCurrentTarget'],x['reviewLineage']['blindDispositionOnCurrentTarget'])) for x in output)
disagreements=[]
for x in output:
    primary_disp=x['reviewLineage']['primaryDisposition']
    blind_disp=normalize_blind.get(x['reviewLineage']['blindDispositionOnCurrentTarget'],x['reviewLineage']['blindDispositionOnCurrentTarget'])
    if primary_disp!=blind_disp:
        disagreements.append({
            'position':x['position'],'locale':x['locale'],'sourceKey':x['source']['sourceKey'],
            'primaryDisposition':primary_disp,'primaryConfidence':x['reviewLineage']['primaryConfidence'],'primaryRationale':x['reviewLineage']['primaryRationale'],'primaryCandidate':x['reviewLineage']['primaryRecommendedTarget'],'primaryCandidateSha256':x['reviewLineage']['primaryRecommendedTargetSha256'],
            'blindDisposition':x['reviewLineage']['blindDispositionOnCurrentTarget'],'blindConfidence':x['reviewLineage']['blindConfidence'],'blindRationale':x['reviewLineage']['blindRationaleOnCurrentTarget'],
            'crossAuditDisposition':x['disposition'],'selectedTarget':None if x['selectedTarget'] is None else x['selectedTarget']['text'],'selectedTargetSha256':None if x['selectedTarget'] is None else x['selectedTarget']['sha256'],'crossAuditRationale':x['crossAuditRationale'],'reconciliation':x['reviewLineage']['reconciliation']
        })
hold_rows=[{'position':x['position'],'locale':x['locale'],'sourceKey':x['source']['sourceKey'],'callerReferenceCount':x['evidence']['caller']['referenceCount'],'currentTarget':x['currentTarget']['text'],'selectedTarget':x['selectedTarget'],'primaryDisposition':x['reviewLineage']['primaryDisposition'],'blindDisposition':x['reviewLineage']['blindDispositionOnCurrentTarget'],'holdReason':x['crossAuditRationale']} for x in output if x['disposition']=='hold']
assert len(disagreements)==94 and len(hold_rows)==12
disagreement_hold={
 'schemaVersion':1,'head':HEAD,'tree':TREE,'normalizedDispositionMatrix':{f'{p} × {b}':n for (p,b),n in sorted(matrix.items())},
 'normalizedDispositionMismatchCount':len(disagreements),'disagreements':disagreements,'holds':hold_rows,
 'reconciliationNotes':[
  'The 48 API-field suffix removals at positions 1252–1254 and 1256 are primary corrections that the blind review accepted; the pinned source messages omit those API-schema details, so selected strings preserve user-facing validation requirements and ContentID where applicable.',
  'At 1243 hi and 1244 vi, primary corrections resolve dry-run meaning or terminology supported by the exact caller; at 1244 hi, the blind refinement and primary correction prefer the same selected target.',
  'The 30 primary-correction / blind-refinement mismatches are resolved from source semantics and caller composition. Dry-run choices at 1246 retain ReplayGain and pre-write preview meaning; positions 1248–1251 retain duration vs interval distinctions and seconds/minutes or unit-neutral caller composition; position 1258 uses graph-edge terminology.',
  'All 12 primary-accepted / blind-refinement disagreements receive narrow refinements for Discovery Inbox feature/item meaning (1245), duplicate-count label (1247 vi), duration wording (1248 and 1251 vi), graph links (1258 hi), or established Indonesian edit terms (1260–1262).',
  'The two primary refinements accepted by the blind review are retained: 1249 ko explicitly labels seconds and 1250 id uses the full minute unit with the unchanged {minutes} placeholder.',
  'All 12 holds are position 1257 (Ecosystem), where the exact pinned catalog key has no caller reference. Both review ledgers agree; no target is selected.'
 ]
}
(ROOT/'disagreement-and-hold-summary.json').write_text(json.dumps(disagreement_hold,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
summary={
 'schemaVersion':1,'repository':REPO,'pullRequest':PR,'head':HEAD,'tree':TREE,'window':'W1243-W1262','cellCount':240,'sourceCount':20,'localeCount':12,
 'primaryDispositionCounts':primary_summary['dispositionCounts'],'blindDispositionCounts':dict(collections.Counter(x['disposition'] for x in blind)),
 'finalDispositionCounts':dict(sorted(final_counts.items())),'selectedTargetChanges':101,'noCallerHolds':12,'noCallerHoldPosition':1257,
 'normalizedPrimaryBlindDispositionMismatches':mismatches['rawNormalizedDispositionMismatch'],
 'normalizedPrimaryBlindDispositionMatrix':{f'{p} × {b}':n for (p,b),n in sorted(matrix.items())},
 'apiFieldSuffixCorrections':48,'nonCallerRationaleAdditionsFromBlindReview':12,
 'placeholderMarkupNumericEntityProtectedLiteralUnitFailures':0,
 'orderedLocaleCatalogKeyOrderPreserved':True,'sourceQueueCount':5441,'sourceQueueOrderSha256':manifest['sourceLookupKeyOrderSha256'],
 'livePRState':pr['state'],'livePRDraft':pr['draft'],'remoteBranchHead':remote_refs[f'refs/heads/{BRANCH}'],'remotePullRefHead':remote_refs[f'refs/pull/{PR}/head'],
 'qualifiedLocaleReviewRequired':True,'nativeSpeakerApproval':False,'releaseApproved':False
}
(ROOT/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
(ROOT/'position-summary.json').write_text(json.dumps(serialized,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
attestation={
 'repository':REPO,'pullRequest':PR,'state':pr['state'],'draft':pr['draft'],'branch':BRANCH,'head':HEAD,'tree':TREE,
 'remoteBranchHead':remote_refs[f'refs/heads/{BRANCH}'],'remotePullRefHead':remote_refs[f'refs/pull/{PR}/head'],
 'localWorktree':str(REPO_WT),'localWorktreeHead':HEAD,'localWorktreeTree':TREE,'localWorktreeClean':True,
 'candidateFreeManifestSha256':sha_bytes((INPUT/'SHA256SUMS.txt').read_bytes()),'primaryManifestSha256':sha_bytes((PRIMARY/'SHA256SUMS.txt').read_bytes()),'blindManifestSha256':sha_bytes((BLIND/'SHA256SUMS.txt').read_bytes()),
 'verifiedAtUTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'reviewerType':'independent third-party cross-audit; proposals reconciled against exact caller/source pins',
 'qualifiedNativeSpeakerApproval':False,'releaseApprovedByThisCrossAudit':False,'testsBuildsScansCIWorkflowActions':False
}
(ROOT/'attestation.json').write_text(json.dumps(attestation,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

report='''# slskR PR #204 W1243–W1262 third-party cross-audit\n\n## Scope and exact pin\n\nThis cross-audit reconciles the 240 cells for 20 source keys across the 12 direct runtime locales at PR head `'''+HEAD+'''` / tree `'''+TREE+'''`. PR metadata, branch ref, pull ref, and a clean detached worktree were rechecked at cross-audit time. All three packet checksum manifests pass.\n\n## Reconciled result\n\n- Final dispositions: 127 accept-current, 81 corrections, 20 refinements, and 12 holds.\n- Selected catalog changes: 101. All 12 holds are the `Ecosystem` cells at position 1257 because the exact source-key scan finds no caller; no target is selected for them.\n- The 48 translations at positions 1252–1254 and 1256 lose parenthetical API-field lists that are absent from the pinned server string and client error allowlist. The blind review accepted these extra hints as informative; the cross-audit keeps the translated message source-bound and avoids exposing implementation detail. `ContentID` and every validation requirement remain intact.\n- The blind reviewer’s dry-run, duration, graph-edge, and Indonesian terminology findings were reconciled against the pinned caller context. The duration unit is preserved: position 1249 remains seconds, position 1250 retains `{minutes}` and minutes, and generic `Duration:` labels remain unit-neutral because callers append seconds or milliseconds.\n- Primary and blind normalized dispositions differ in 94 cells. The row-level rationale is recorded in `disagreement-and-hold-summary.json`: 48 source-bound API-suffix removals, source/caller-led dry-run and duration corrections/refinements, and narrow blind-only refinements. Both reviews agree on the 12 no-caller holds.\n- `Discovery Inbox` is preserved as the exact capitalized feature name in the affected Hindi, Chinese, and Vietnamese refinements; graph `Edges` use graph-specific terms.\n\n## Validation and limits\n\nAll 240 rows match the candidate-free source/current hashes and exact caller references. The selected targets pass placeholder, markup, numeric, entity, protected-literal, and semantic-unit checks. The 12 locale catalogs retain the same 5,441-key order. This is machine-assisted semantic review, not qualified native-speaker approval; native-speaker review remains required. Exact-head browser acceptance is also not established by this packet. No repository files, PR body, workflows, tests, builds, scans, CI, merge, release, or tag were changed or run.\n'''
(ROOT/'report.md').write_text(report,encoding='utf-8')
README='''# W1243–W1262 cross-audit evidence\n\nThis self-contained packet retains the exact candidate-free input, primary ledger, and independent blind ledger used to reconcile all 240 cells. `cross-audit-ledger.jsonl` records the final selected target, source/caller/runtime evidence, structural checks, and review lineage per locale cell.\n\n`summary.json` and `position-summary.json` give the aggregate and per-source counts; `disagreement-and-hold-summary.json` records all 94 normalized disposition mismatches and the 12 holds; `report.md` describes the principal decisions and unresolved holds. All packets are pinned to PR #204 head `'''+HEAD+'''` / tree `'''+TREE+'''`. `SHA256SUMS.txt` covers every file in this package except itself.\n\nNo native-speaker or release approval is implied.\n'''
(ROOT/'README.md').write_text(README,encoding='utf-8')
files=sorted(p for p in ROOT.rglob('*') if p.is_file() and p.name!='SHA256SUMS.txt')
(ROOT/'SHA256SUMS.txt').write_text(''.join(f'{sha_bytes(p.read_bytes())}  {p.relative_to(ROOT).as_posix()}\n' for p in files),encoding='utf-8')
print(json.dumps(summary,ensure_ascii=False,indent=2))
