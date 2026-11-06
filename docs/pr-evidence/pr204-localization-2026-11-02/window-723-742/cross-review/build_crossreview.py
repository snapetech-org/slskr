import collections, hashlib, json, pathlib, re, shutil, subprocess, datetime

ROOT=pathlib.Path('/mnt/disks/scratch/task-scratch/slskr-pr204-W723-742-crossreview-by-root-child-20261102')
PRIMARY=pathlib.Path('/mnt/disks/scratch/task-scratch/slskr-pr204-W723-742-primary-20261102/packet')
W=pathlib.Path('/mnt/disks/scratch/task-worktrees/localization-20261102/slskr-pr204-w503-522')
REPO='snapetech-org/slskR'; PR=204
HEAD='32903976fabe543f89dd5950245ba11dd77c8eb3'; TREE='ebf75888b3087e83fe2327495c17611802925f71'
LOCALES=['ar','de','es','fr','hi','id','ja','ko','pt-BR','vi','zh-Hans','zh-Hant']

REVISE={
 (730,'vi'):('Đóng trình nhập CSV mà không thêm tìm kiếm nào vào Danh sách yêu thích.','propose-correction','The primary wording uses “Danh sách mong muốn,” while the pinned catalog’s exact Wishlist term is “Danh sách yêu thích.” This caller is the CSV importer Cancel tooltip, and the source refers to Wishlist searches.')
}
ADDITIONAL={
 (729,'ja'):('検索を開始せずにスマートラジオを閉じます。','propose-refinement','The current Japanese inserts a space inside スマート ラジオ. The catalog’s “Smart Radio Seed” term is スマートラジオシード, confirming the compact compound spelling.'),
 (730,'ar'):('إغلاق مستورد CSV دون إضافة أي عمليات بحث إلى قائمة الرغبات.','propose-refinement','The CSV Cancel tooltip refers to the Wishlist feature. Use the exact localized Wishlist label قائمة الرغبات instead of the current synonym قائمة الأمنيات.'),
 (730,'hi'):('इच्छा सूची में कोई खोज जोड़े बिना CSV आयातक बंद करें।','propose-correction','The current target transliterates Wishlist as विशलिस्ट. The pinned UI label uses इच्छा सूची; use that term for the feature in this CSV-import action.'),
 (730,'id'):('Tutup pengimpor CSV tanpa menambahkan pencarian apa pun ke Daftar keinginan.','propose-correction','The current target leaves Wishlist in English even though the pinned catalog localizes the feature as Daftar keinginan.'),
 (730,'zh-Hans'):('关闭 CSV 导入器，不向愿望单添加任何搜索。','propose-refinement','This is a Wishlist feature action. The pinned UI label is 愿望单; use it instead of the synonymous but inconsistent 愿望清单 and phrase the no-addition guarantee directly.')
}

CONTEXT={
 723:'Browse tab close-button accessible name; {label} is the selected tab title',724:'DiagnosticBundleModal close button, separate from its Copy action',725:'directory-scoped file-list close icon',726:'PlayerStatsModal Done action',727:'PlayerIntegrationsModal Done action after ListenBrainz token save',728:'SetupHealthCheckModal close button',729:'PlayerRadioModal Done action that closes Smart Radio without searching',730:'CsvImportModal Cancel action that discards the import and must not add Wishlist searches',731:'PlayerLauncher collection-picker Close action; playback continues',732:'DiagnosticBundleModal close button, distinct from Copy',733:'caller not pinned at this head; UI rendering remains unclaimed',734:'PlayerDiscoveryShelfModal Done action',735:'PlayerLauncher local-file-browser Close action; playback continues',736:'PlayerQueueModal Done action',737:'SetupHealthCheckModal close action',738:'ShareGroups Add Member Cancel action',739:'ShareGroups Create Share Group Cancel action',740:'caller not pinned at this head; UI rendering remains unclaimed',741:'Messaging close icon; closePanel only removes the panel from local UI state',742:'caller not pinned at this head; UI rendering remains unclaimed'
}

def sha(b): return hashlib.sha256(b).hexdigest()
def jbytes(x): return json.dumps(x,ensure_ascii=False,separators=(',',':')).encode()
def git(*args): return subprocess.check_output(['git','-C',str(W),*args])
def read_git(path): return git('show',f'HEAD:{path}')
def blob(path): return git('rev-parse',f'HEAD:{path}').decode().strip()
def loadjl(path): return [json.loads(line) for line in pathlib.Path(path).read_text(encoding='utf-8').splitlines() if line]
def gh_state():
    return json.loads(subprocess.check_output(['gh','pr','view',str(PR),'--repo',REPO,'--json','state,isDraft,headRefOid,headRefName,baseRefOid,url'],text=True))
def require_pin(stage):
    pr=gh_state(); h=git('rev-parse','HEAD').decode().strip(); t=git('rev-parse','HEAD^{tree}').decode().strip(); status=git('status','--porcelain').decode()
    assert h==HEAD and t==TREE,(stage,h,t)
    assert pr['headRefOid']==HEAD and pr['state']=='OPEN' and pr['isDraft'] is True,(stage,pr)
    assert status=='',(stage,'dirty worktree',status)
    return {'stage':stage,'checkedAtUtc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'livePullRequest':pr,'worktree':{'head':h,'tree':t,'status':status}}
def verify_sumfile(directory,name):
    for line in (directory/name).read_text().splitlines():
        expected,rel=line.split('  ',1)
        assert sha((directory/rel).read_bytes())==expected,(name,rel)

def placeholders(s): return sorted(set(re.findall(r'\{[^{}]+\}|%\d*\$?[sdif]|\$\{[^}]+\}',s)))
def markup(s):
    if re.fullmatch(r'<[^<>/]+>',s): return []
    return re.findall(r'</?[A-Za-z][^>]*>',s)

pre=require_pin('before-cross-review')
verify_sumfile(PRIMARY,'SHA256SUMS')
assert sha((PRIMARY/'freeze-manifest.json').read_bytes())== (PRIMARY/'freeze-manifest.sha256').read_text().split()[0]
manifest=json.loads((PRIMARY/'manifest.json').read_text()); primary_summary=json.loads((PRIMARY/'primary-summary.json').read_text())
assert manifest['head']==HEAD and manifest['tree']==TREE and primary_summary['head']==HEAD and primary_summary['tree']==TREE
assert primary_summary['sourcePositions']==[723,742] and primary_summary['sourceIds']==20 and primary_summary['cells']==240

# Reattest the exact frozen source order and source/current locale values at the live PR head.
inventory=loadjl(PRIMARY/'source-inventory.jsonl'); inv_raw=(PRIMARY/'source-inventory.jsonl').read_bytes()
assert len(inventory)==5437 and sha(inv_raw)==manifest['sourceInventory']['sha256']
source_ids=[x['source_id'] for x in inventory]
assert source_ids[723]=='Close browse tab {label}' and source_ids[742]=='Close this preview and return to the selected files without starting a transfer.'
source_att=loadjl(PRIMARY/'source-current-attestation.jsonl'); source_context=loadjl(PRIMARY/'source-context.jsonl')
current_cells=loadjl(PRIMARY/'current-cells.jsonl'); review_rows=loadjl(PRIMARY/'primary-review-ledger.jsonl')
candidate_rows=loadjl(PRIMARY/'correction-candidates.jsonl'); held_rows=loadjl(PRIMARY/'held-cells.jsonl')
assert len(source_att)==20 and len(source_context)==20 and len(current_cells)==240 and len(review_rows)==240 and len(candidate_rows)==41 and len(held_rows)==49
assert [x['sourceIndex'] for x in source_att]==list(range(723,743))

catalogs={}; cat_bytes={}; catalog_pins={}
for locale,info in manifest['catalogs'].items():
    raw=read_git(info['path']); cat_bytes[locale]=raw; catalogs[locale]=json.loads(raw)
    assert len(catalogs[locale])==5440 and blob(info['path'])==info['blobOid'] and sha(raw)==info['sha256'],locale
    catalog_pins[locale]={'path':info['path'],'blobOid':info['blobOid'],'sha256':info['sha256'],'keyCount':len(catalogs[locale])}

att_by={r['sourceId']:r for r in source_att}; context_by={r['sourceId']:r for r in source_context}
cell_by={(r['sourceIndex'],r['locale']):r for r in current_cells}
review_by={(r['sourceIndex'],r['locale']):r for r in review_rows}
candidates={(r['sourceIndex'],r['locale']):r for r in candidate_rows}
assert len(cell_by)==240 and len(review_by)==240 and len(candidates)==41
source_hashes={}
for i in range(723,743):
    sid=source_ids[i]; att=att_by[sid]; ctx=context_by[sid]
    assert att['sourceIndex']==i and att['sourceSha256']==sha(sid.encode())
    assert ctx['sourceIndex']==i and ctx['attestedHead']==HEAD and ctx['attestedTree']==TREE
    assert ctx['sourceId']==sid and not ctx['testReferences']
    source_hashes[sid]=sha(sid.encode())
    for locale in LOCALES:
        key=(i,locale); c=cell_by[key]; r=review_by[key]
        assert c['sourceIndex']==i and c['sourceId']==sid and c['source']==sid
        assert r['sourceIndex']==i and r['sourceId']==sid and r['source']==sid
        assert catalogs[locale][sid]==c['currentTarget']==r['currentTarget']
        assert c['targetCatalogBlob']==manifest['catalogs'][locale]['blobOid']
        assert c['targetFile']==manifest['catalogs'][locale]['path']
        assert r['targetCatalogBlob']==c['targetCatalogBlob'] and r['targetFile']==c['targetFile']
        assert c['currentTargetSha256']==sha(c['currentTarget'].encode())==r['currentTargetSha256']
        assert r['sourceSha256']==sha(sid.encode())

# Verify every caller/source-context pin, including all line windows and exact file blobs.
pins=loadjl(PRIMARY/'caller-context-pins.jsonl'); assert len(pins)==49
pin_files={}; pin_lines=set(); source_ref_total=0
for pin in pins:
    assert pin['attestedHead']==HEAD and pin['attestedTree']==TREE
    path=pin['path']; raw=read_git(path); lines=raw.decode('utf-8').splitlines(); line=pin['line']
    assert blob(path)==pin['fileBlob'] and sha(raw)==pin['fileSha256'],(path,'file pin')
    assert 1<=line<=len(lines) and lines[line-1]==pin['lineText'] and sha(lines[line-1].encode())==pin['lineSha256'],(pin['sourceId'],path,line)
    assert lines[line-2] if False else True
    if pin.get('previousLine') is not None: assert line>1 and lines[line-2]==pin['previousLine'],(pin['sourceId'],path,line,'previous')
    if pin.get('nextLine') is not None: assert line<len(lines) and lines[line]==pin['nextLine'],(pin['sourceId'],path,line,'next')
    pin_files[path]=1; pin_lines.add((path,line,pin['sourceId']))
    source_ref_total+=1
for ctx in source_context:
    assert ctx['attestedHead']==HEAD and ctx['attestedTree']==TREE
    for ref in ctx['callerReferences']:
        assert (ref['sourceId'],ref['path'],ref['line'],ref['lineSha256']) in {(p['sourceId'],p['path'],p['line'],p['lineSha256']) for p in pins}
no_direct=[r['sourceId'] for r in source_context if r['callerStatus']=='no-direct-caller-found']
assert no_direct==[source_ids[i] for i in (733,740,742)]
assert len(pin_files)==13 and len({(p['path'],p['line']) for p in pins})==48
assert source_ref_total==49

# Independently verify the prior W722 primary evidence from the exact current tree and current catalogs.
boundary=json.loads((PRIMARY/'boundary-reattestation.json').read_text())
assert boundary['attestedHead']==HEAD and boundary['attestedTree']==TREE
assert boundary['zeroBasedIndex722']['sourceId']==source_ids[722]=='Close'
assert boundary['zeroBasedIndex723']['sourceId']==source_ids[723]
prior_meta=boundary['previousPrimaryLedger']; prior_path=prior_meta['path']; prior_raw=read_git(prior_path)
assert blob(prior_path)==prior_meta['blobOid'] and sha(prior_raw)==prior_meta['sha256']
prior_by_locale={}
for line in prior_raw.splitlines():
    row=json.loads(line)
    if row.get('sourceIndex')==722: prior_by_locale[row['locale']]=(row,sha(line))
assert set(prior_by_locale)==set(LOCALES)
previous_rows={x['locale']:x for x in boundary['previousBoundaryRowsReattested']}
assert set(previous_rows)==set(LOCALES)
prior_caller_refs={}
prior_context_rows=[]
for locale in LOCALES:
    old,old_hash=prior_by_locale[locale]; item=previous_rows[locale]; live=catalogs[locale]['Close']
    assert item['priorRowSha256']==old_hash and old['sourceId']=='Close' and old['sourceIndex']==722
    assert item['currentCellMatchesNewCatalog'] is True
    assert item['targetState'] in ('prior-correction-current','prior-accepted-current')
    if item['targetState']=='prior-correction-current':
        assert old['recommendedTarget']==live and old['recommendedTargetSha256']==sha(live.encode()) and old['reviewDecision']=='propose-correction'
    else:
        assert old['currentTarget']==live and old['currentTargetSha256']==sha(live.encode()) and old['recommendedTarget']==live and old['recommendedTargetSha256']==sha(live.encode()) and old['reviewDecision']=='accept-current'
    verified_prior_pins=[]
    for pin in old['callerContextPins']:
        path=pin['path']; raw=read_git(path); lines=raw.decode('utf-8').splitlines(); line=pin['line']
        assert blob(path)==pin['fileBlob'] and sha(raw)==pin['fileSha256']
        assert lines[line-1] and sha(lines[line-1].encode())==pin['lineSha256'],(path,line)
        prior_caller_refs[(path,line,pin['lineSha256'])]=1
        verified_prior_pins.append(pin)
    prior_context_rows.append({'sourceIndex':722,'sourceId':'Close','locale':locale,'priorRowSha256':old_hash,
      'priorHead':old['attestedHead'],'priorTree':old['attestedTree'],'primaryDisposition':old['reviewDecision'],
      'targetState':item['targetState'],'priorCurrentTarget':old['currentTarget'],'priorCurrentTargetSha256':old['currentTargetSha256'],
      'priorRecommendedTarget':old['recommendedTarget'],'priorRecommendedTargetSha256':old['recommendedTargetSha256'],
      'liveCurrentTarget':live,'liveCurrentTargetSha256':sha(live.encode()),'currentTargetMatchesPriorDecision':True,
      'callerPinsReattestedAtHead':verified_prior_pins})
assert len(prior_caller_refs)==11 and len(prior_context_rows)==12

# Read back locale UI terms from the same pinned catalogs. These terms support candidate review for Browse,
# Wishlist, Smart Radio Seed, Collection, and Discovery Shelf.
TERM_KEYS=['Browse','Wishlist','Smart Radio Seed','Collection','Discovery Shelf']
localized_terms={locale:{key:catalogs[locale][key] for key in TERM_KEYS} for locale in LOCALES}
(ROOT/'localized-ui-terms.json').write_text(json.dumps({'head':HEAD,'tree':TREE,'sourceKeys':TERM_KEYS,'values':localized_terms},ensure_ascii=False,indent=2,sort_keys=True)+'\n',encoding='utf-8')

# Independently judge all 240 cells. Holds remain current and unclaimed; candidate revisions/additions are explicit.
review=[]; verdict_counts=collections.Counter(); final_counts=collections.Counter(); locale_counts={l:collections.Counter() for l in LOCALES}
additional=[]; revisions=[]
for i in range(723,743):
    sid=source_ids[i]; ctx=context_by[sid]; meaning=CONTEXT[i]
    for locale in LOCALES:
        key=(i,locale); p=review_by[key]; source=sid; current=p['currentTarget']; primary_disp=p['reviewDecision']; primary_reco=p['recommendedTarget'] if primary_disp=='propose-correction' else None
        if primary_disp.startswith('hold'):
            verdict='retain-hold'; final=current; final_disp=primary_disp
            if i in (733,740,742):
                rationale='Retain the no-direct-caller hold. The translation is readable, but this key has no exact rendering caller at the pinned head; do not claim that users see or invoke it.'
            elif i==741:
                rationale='Retain the source-ambiguity hold. The pinned close icon removes the panel from local UI state only; it neither deletes a thread nor leaves a room/channel. “Leaving anything” has no defined effect and must be clarified in English before these 12 locale targets are approved.'
            else:
                rationale='Retain the Vietnamese terminology hold. In this modal the label means close the diagnostic bundle; the current Đóng gói chẩn đoán can instead mean package diagnostics, and no fluent Vietnamese confirmation is available.'
            confidence='moderate'
        elif key in REVISE:
            final,final_disp,rationale=REVISE[key]; verdict='revise-primary-candidate'; confidence='moderate'
            revisions.append({'sourceIndex':i,'sourceId':sid,'locale':locale,'primaryTarget':primary_reco,'finalTarget':final,'finalDisposition':final_disp,'reason':rationale})
        elif key in ADDITIONAL:
            final,final_disp,rationale=ADDITIONAL[key]
            verdict='add-missed-correction' if final_disp=='propose-correction' else 'add-missed-refinement'
            confidence='moderate'
            additional.append({'sourceIndex':i,'sourceId':sid,'locale':locale,'currentTarget':current,'finalTarget':final,'finalDisposition':final_disp,'reason':rationale})
        elif primary_reco is not None:
            final=primary_reco; final_disp=primary_disp; verdict='accept-primary-candidate'
            rationale=f"Independent review agrees with the proposed target for the {meaning}; it retains the source action/meaning, fits the pinned caller, and preserves the exact placeholder/protected terms."
            confidence=p['confidence']
        else:
            final=current; final_disp='accept-current'; verdict='accept-current'
            rationale=f"Current target accurately conveys the source for the {meaning}; no material semantic or structural issue found in this cell."
            confidence='moderate'
        src_ph=placeholders(source); final_ph=placeholders(final)
        src_markup=markup(source); final_markup=markup(final)
        protected=p.get('protectedLiterals',[]); missing=[x for x in protected if x not in final]
        assert src_ph==final_ph,(i,locale,'placeholder mismatch',src,final)
        assert src_markup==final_markup,(i,locale,'markup mismatch',src,final)
        assert not missing,(i,locale,'protected literal mismatch',missing,final)
        assert p['currentTargetSha256']==sha(current.encode())
        if primary_reco is not None: assert p['recommendedTargetSha256']==sha(primary_reco.encode())
        callers=ctx['callerReferences']; caller_status=ctx['callerStatus']
        if i in (733,740,742): assert caller_status=='no-direct-caller-found' and not callers
        if i==741: assert caller_status=='found' and len(callers)==4
        localized_ui={}
        for term in TERM_KEYS:
            if term.lower() in source.lower(): localized_ui[term]=localized_terms[locale][term]
        verdict_counts[verdict]+=1; final_counts[final_disp]+=1; locale_counts[locale][verdict]+=1
        review.append({'repository':REPO,'pullRequest':PR,'exactHead':HEAD,'exactTree':TREE,
          'sourceIndex':i,'sourceId':sid,'source':source,'sourceSha256':sha(source.encode()),'locale':locale,
          'currentTarget':current,'currentTargetSha256':sha(current.encode()),
          'primaryDecision':primary_disp,'primaryRecommendedTarget':primary_reco,'primaryRecommendedTargetSha256':p.get('recommendedTargetSha256') if primary_reco is not None else None,
          'independentVerdict':verdict,'finalDisposition':final_disp,'finalTarget':final,'finalTargetSha256':sha(final.encode()),
          'independentRationale':rationale,'primaryRationale':p['rationale'],'confidence':confidence,
          'callerStatus':caller_status,'callerReferences':callers,
          'localizedUiTerms':localized_ui,
          'sourcePlaceholders':src_ph,'finalPlaceholders':final_ph,'placeholderParity':'exact',
          'sourceMarkup':src_markup,'finalMarkup':final_markup,'markupParity':'exact',
          'protectedLiterals':protected,'protectedLiteralsMissing':missing,'protectedLiteralParity':'exact',
          'nativeSpeakerApproval':False})
assert len(review)==240 and len({(r['sourceIndex'],r['locale']) for r in review})==240
assert verdict_counts['accept-current']==145 and verdict_counts['accept-primary-candidate']==40
assert verdict_counts['revise-primary-candidate']==1 and verdict_counts['add-missed-correction']==2 and verdict_counts['add-missed-refinement']==3 and verdict_counts['retain-hold']==49
assert final_counts['propose-correction']==43 and final_counts['propose-refinement']==3
assert sum(v for k,v in final_counts.items() if k.startswith('hold-'))==49

# Recheck exact live PR/head/tree after all cell reviews.
post=require_pin('after-cross-review')

# Copy the entire frozen primary packet into this output to preserve source, caller, and exact-current evidence.
copydir=ROOT/'primary-packet'; copydir.mkdir(exist_ok=True)
for path in PRIMARY.iterdir():
    if path.is_file(): shutil.copy2(path,copydir/path.name)
(ROOT/'cross-review-ledger.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False,sort_keys=True,separators=(',',':'))+'\n' for r in review),encoding='utf-8')
(ROOT/'additional-findings.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False,sort_keys=True,separators=(',',':'))+'\n' for r in additional),encoding='utf-8')
(ROOT/'prior-w722-context.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False,sort_keys=True,separators=(',',':'))+'\n' for r in prior_context_rows),encoding='utf-8')
(ROOT/'candidate-revisions.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False,sort_keys=True,separators=(',',':'))+'\n' for r in revisions),encoding='utf-8')
prior_attestation={'sourceIndex':722,'sourceId':'Close','priorPrimaryRowsReattested':12,'priorRecommendationsStillCurrent':12,
 'priorCallerRefsReattested':len(prior_caller_refs),'priorLedgerPath':prior_path,'priorLedgerBlob':prior_meta['blobOid'],'priorLedgerSha256':prior_meta['sha256']}
reattest={'repository':REPO,'pullRequest':PR,'expectedHead':HEAD,'expectedTree':TREE,'beforeReview':pre,'afterReview':post,
 'sourceInventoryRowsReattested':5437,'sourceIdsReattested':20,'localeCellsReattested':240,
 'sourceContextRowsReattested':20,'callerReferencesReattested':49,'callerFilesReattested':len(pin_files),'callerMismatches':0,
 'catalogsReattested':12,'priorBoundary':prior_attestation,'callerGapSourceIds':no_direct,'worktreeUnmodified':True}
(ROOT/'live-input-reattestation.json').write_text(json.dumps(reattest,ensure_ascii=False,indent=2,sort_keys=True)+'\n',encoding='utf-8')
summary={'schemaVersion':1,'repository':REPO,'pullRequest':PR,'state':'OPEN','isDraft':True,'head':HEAD,'tree':TREE,
 'sourcePositionRange':[723,742],'sourceIds':20,'locales':LOCALES,'cells':240,
 'candidateAdjudicationCounts':dict(sorted(verdict_counts.items())),
 'primaryCorrectionCandidates':41,'primaryCandidateAgreements':40,'primaryCandidateRevisions':1,
 'additionalFindings':5,'additionalCorrections':2,'additionalRefinements':3,
 'finalDispositions':dict(sorted(final_counts.items())),
 'finalCorrections':43,'finalRefinements':3,'finalHolds':49,'finalAcceptCurrent':145,
 'holds':{'noDirectCallerCells':36,'sourceAmbiguityCells':12,'localeTerminologyCells':1,
  'unclaimedSources':[source_ids[i] for i in (733,740,742)],'sourceAmbiguitySource':source_ids[741],'localeTerminologyCell':{'sourceIndex':724,'locale':'vi'}},
 'priorW722':prior_attestation,
 'callerEvidence':{'callerReferences':49,'uniqueCallerFiles':len(pin_files),'uniqueCallerLines':len({(p['path'],p['line']) for p in pins}),
  'noDirectCallerSourceIds':no_direct,'callerMismatches':0,'testReferences':0},
 'structuralChecks':{'placeholderMismatchCount':0,'markupMismatchCount':0,'protectedLiteralMismatchCount':0},
 'nativeSpeakerApproval':'outstanding','confidence':'moderate','repositoryOrPullRequestModified':False,
 'testsBuildsScansCiBrowserOrWorkflowWork':False,'outputPath':str(ROOT)}
(ROOT/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2,sort_keys=True)+'\n',encoding='utf-8')
README=f'''# slskR PR #204 W723–742 independent cross-review

- Exact live PR pin: OPEN/DRAFT at `{HEAD}` / tree `{TREE}`, rechecked before and after review.
- Scope: 20 source strings × 12 locales = 240 independently judged cells.
- The exact primary packet was copied to `primary-packet/`; its checksum manifest passes. The source inventory, 12 locale catalogs, all current cells, 49 caller pins across 13 files, and adjacent W722 boundary were reattested against the live tree.

## Review results

- 145 cells: accept current.
- 40 primary candidate targets: accept.
- 1 primary candidate target revised: W730 Vietnamese now uses the pinned `Wishlist` translation `Danh sách yêu thích`.
- 5 additional findings: W729 Japanese compound spacing; W730 Arabic, Hindi, Indonesian, and Simplified Chinese alignment with each catalog’s exact `Wishlist` term.
- Final ledger counts: 43 corrections, 3 refinements, 49 holds.
- Holds retained: 36 cells in W733/W740/W742 have no direct caller; all 12 W741 cells remain held because “leaving anything” does not describe the pinned local-state-only panel close; W724 Vietnamese remains held for fluent terminology review.
- W741’s close handler only filters the panel from local UI state. It does not delete a thread or leave a room/channel.
- W722 is adjacent and non-overlapping. Its 12 prior decisions and current targets remain present; all 11 prior caller pins still match. `prior-w722-context.jsonl` carries the exact row and caller-pin evidence.
- Placeholder, markup, and protected-literal mismatches in final targets: zero.

Confidence is moderate. Native-speaker approval remains outstanding. No repository/PR edits, tests, builds, CI, or browser actions were performed.
'''
(ROOT/'README.md').write_text(README,encoding='utf-8')
files=sorted(p for p in ROOT.rglob('*') if p.is_file() and p.resolve()!=(ROOT/'SHA256SUMS').resolve())
(ROOT/'SHA256SUMS').write_text(''.join(f'{sha(p.read_bytes())}  {p.relative_to(ROOT).as_posix()}\n' for p in files),encoding='utf-8')
print(json.dumps({'outputPath':str(ROOT),'summary':summary,'primaryPacketFilesCopied':len(list(copydir.iterdir())),'sha256sumManifest':sha((ROOT/'SHA256SUMS').read_bytes())},ensure_ascii=False,indent=2))
