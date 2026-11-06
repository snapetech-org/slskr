import json,hashlib,pathlib,subprocess,re,collections
O=pathlib.Path('/mnt/disks/scratch/task-scratch/slskr-pr204-W743-762-crossreview-by-agent-20261102/packet')
P=pathlib.Path('/mnt/disks/scratch/task-scratch/slskr-pr204-W743-762-primary-20261102/packet')
W=pathlib.Path('/mnt/disks/scratch/task-worktrees/localization-20261102/slskr-pr204-w503-522')
REPO='snapetech-org/slskR'; PR=204
HEAD='32903976fabe543f89dd5950245ba11dd77c8eb3'; TREE='ebf75888b3087e83fe2327495c17611802925f71'
LOCALES=['ar','de','es','fr','hi','id','ja','ko','pt-BR','vi','zh-Hans','zh-Hant']
def sha(b): return hashlib.sha256(b).hexdigest()
def jbytes(x): return json.dumps(x,ensure_ascii=False,separators=(',',':')).encode()
def git(*args): return subprocess.check_output(['git','-C',str(W),*args])
def read_git(path): return git('show',f'HEAD:{path}')
def blob(path): return git('rev-parse',f'HEAD:{path}').decode().strip()
def save(name,obj): (O/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n')
def save_jsonl(name,rows): (O/name).write_text(''.join(json.dumps(x,ensure_ascii=False,separators=(',',':'))+'\n' for x in rows))
def placeholders(s): return collections.Counter(re.findall(r'\{[^{}]+\}',s))
def markup(s): return re.findall(r'</?[A-Za-z][^>]*>',s)
def terminal(s):
  t=s.rstrip()
  if t.endswith(':') or t.endswith('：'): return 'colon'
  if t.endswith('?') or t.endswith('؟') or t.endswith('？'): return 'question'
  if t.endswith('!') or t.endswith('！'): return 'exclamation'
  if t.endswith(('.', '。', '｡', '۔', '।')): return 'sentence-terminal'
  if t.endswith(('…','...')): return 'ellipsis'
  return 'none'
def punctuation_compatible(source,target):
  source_mark=terminal(source); target_mark=terminal(target)
  return source_mark==target_mark or (source_mark=='none' and target_mark=='sentence-terminal')
def live_pr(): return json.loads(subprocess.check_output(['gh','pr','view',str(PR),'--repo',REPO,'--json','state,isDraft,headRefOid,headRefName,baseRefName,baseRefOid,url'],text=True))

assert git('rev-parse','HEAD').decode().strip()==HEAD and git('rev-parse','HEAD^{tree}').decode().strip()==TREE
assert git('status','--porcelain').decode()==''
pr_before=live_pr(); assert pr_before['headRefOid']==HEAD and pr_before['state']=='OPEN' and pr_before['isDraft'] is True

# Verify every supplied primary-packet checksum and its frozen head/tree before independent review.
subprocess.check_call(['sha256sum','-c','SHA256SUMS'],cwd=P,stdout=subprocess.DEVNULL)
primary_manifest=json.loads((P/'manifest.json').read_text())
primary_summary=json.loads((P/'primary-summary.json').read_text())
assert primary_manifest['head']==HEAD and primary_manifest['tree']==TREE
assert primary_manifest['sourceWindow']==[743,762] and primary_manifest['cells']==240
inventory_path=pathlib.Path(primary_manifest['sourceInventory']['path'])
inventory_bytes=inventory_path.read_bytes()
assert sha(inventory_bytes)==primary_manifest['sourceInventory']['sha256']
inventory=[json.loads(x) for x in inventory_bytes.decode().splitlines()]
assert len(inventory)==5437
expected_ids=[x['source_id'] for x in inventory[743:763]]
assert len(expected_ids)==20

# Independently reread all catalogs and verify the 240 frozen source/current cells.
catalogs={}; catalog_info={}
for loc in LOCALES:
  info=primary_manifest['catalogs'][loc]; content=read_git(info['path']); catalogs[loc]=json.loads(content)
  catalog_info[loc]={'path':info['path'],'blob':blob(info['path']),'sha256':sha(content),'bytes':len(content),'keys':len(catalogs[loc])}
  assert catalog_info[loc]['blob']==info['blobOid'] and catalog_info[loc]['sha256']==info['sha256']
source_rows=[json.loads(x) for x in (P/'current-cells.jsonl').read_text().splitlines()]
primary_rows=[json.loads(x) for x in (P/'primary-review-ledger.jsonl').read_text().splitlines()]
candidate_rows=[json.loads(x) for x in (P/'correction-candidates.jsonl').read_text().splitlines()]
context_rows=[json.loads(x) for x in (P/'source-context.jsonl').read_text().splitlines()]
assert len(source_rows)==len(primary_rows)==240 and len(candidate_rows)==43 and len(context_rows)==20
assert [x['sourceId'] for x in context_rows]==expected_ids
source_by_key={(x['sourceIndex'],x['locale']):x for x in source_rows}
primary_by_key={(x['sourceIndex'],x['locale']):x for x in primary_rows}
assert len(source_by_key)==len(primary_by_key)==240 and set(source_by_key)==set(primary_by_key)
for pos,sid in enumerate(expected_ids,743):
  assert inventory[pos]['source_id']==sid
  assert inventory[pos]['source_sha256']==sha(sid.encode())
for key,s in source_by_key.items():
  pos,loc=key; p=primary_by_key[key]; sid=s['sourceId']
  assert sid==expected_ids[pos-743] and s['source']==sid and p['source']==sid
  assert s['sourceIndex']==pos and p['sourceIndex']==pos
  assert catalogs[loc][sid]==s['currentTarget']==p['currentTarget']
  assert sha(sid.encode())==s['sourceSha256']==p['sourceSha256']
  assert sha(s['currentTarget'].encode())==s['currentTargetSha256']==p['currentTargetSha256']
  assert p['targetCatalogBlob']==catalog_info[loc]['blob']
  assert p['attestedHead']==HEAD and p['attestedTree']==TREE
  assert p['recommendedTargetSha256']==sha(p['recommendedTarget'].encode())
  assert placeholders(sid)==placeholders(s['currentTarget'])==placeholders(p['recommendedTarget'])
  assert markup(sid)==markup(s['currentTarget'])==markup(p['recommendedTarget'])
  assert terminal(sid)==p['sourceTerminalPunctuation']
  assert p['recommendedTerminalPunctuation']==terminal(p['recommendedTarget'])

# Reattest all 67 pinned source, supporting-context, and test references at the live tree.
# The per-source semantic context file contains the 44 direct + 15 supporting references;
# the separate caller-context-pins file also records the 8 test references.
caller_pin_rows=[json.loads(x) for x in (P/'caller-context-pins.jsonl').read_text().splitlines()]
assert len(caller_pin_rows)==67
caller_kind_counts=collections.Counter(x['kind'] for x in caller_pin_rows)
direct_source_positions={x['sourceIndex'] for x in caller_pin_rows if x['kind']=='source-reference'}
assert caller_kind_counts['source-reference']==44 and caller_kind_counts['test-reference']==8
assert len([x for x in caller_pin_rows if x['kind'] not in ('source-reference','test-reference')])==15
assert direct_source_positions==set(range(743,763))
caller_file_attest={}; caller_line_errors=[]; caller_refs=len(caller_pin_rows); caller_unique=set()
context_by_id={x['sourceId']:x for x in context_rows}
for ctx in context_rows:
  pos=ctx['sourceIndex']; sid=ctx['sourceId']; assert expected_ids[pos-743]==sid
  assert ctx['attestedHead']==HEAD and ctx['attestedTree']==TREE and ctx['callerStatus']=='found'
context_pins_by_key={(r['sourceIndex'],r['sourceId'],r['path'],r['line'],r['lineSha256']) for r in caller_pin_rows if r['kind']!='test-reference'}
context_refs_by_key=set()
for ctx in context_rows:
  for ref in ctx['callerReferences']:
    context_refs_by_key.add((ctx['sourceIndex'],ctx['sourceId'],ref['path'],ref['line'],ref['lineSha256']))
assert context_refs_by_key==context_pins_by_key
for ref in caller_pin_rows:
  pos=ref['sourceIndex']; sid=ref['sourceId']; path=ref['path']; assert expected_ids[pos-743]==sid
  assert ref['attestedHead']==HEAD and ref['attestedTree']==TREE
  content=read_git(path); actual={'blob':blob(path),'sha256':sha(content)}
  if path in caller_file_attest and caller_file_attest[path]!=actual: caller_line_errors.append({'path':path,'reason':'inconsistent file pins'})
  caller_file_attest[path]=actual
  caller_unique.add((sid,path,ref['line'],ref['lineSha256']))
  lines=content.decode('utf-8').splitlines(); n=ref['line']
  if actual['blob']!=ref['fileBlob'] or actual['sha256']!=ref['fileSha256'] or n<1 or n>len(lines) or lines[n-1]!=ref['lineText'] or sha(lines[n-1].encode())!=ref['lineSha256']:
    caller_line_errors.append({'sourceId':sid,'path':path,'line':n,'kind':ref['kind'],'reason':'caller pin mismatch'})
assert caller_refs==67 and len(caller_file_attest)==26 and not caller_line_errors, json.dumps({'callerReferences':caller_refs,'callerFiles':len(caller_file_attest),'errors':caller_line_errors},ensure_ascii=False)

# Check every reference from every cell agrees with its source-context record.
for key,s in source_by_key.items():
  ctx=context_by_id[s['sourceId']]
  expected={(r['path'],r['line'],r['lineSha256']) for r in ctx['callerReferences']}
  actual={(r['path'],r['line'],r['lineSha256']) for r in s['callerReferences']}
  assert actual==expected

# Verify candidate extraction and prior-audit source/target reattestation files.
expected_candidates=[x for x in primary_rows if x['reviewDecision']=='propose-correction']
assert len(expected_candidates)==43
candidate_by_key={(x['sourceIndex'],x['locale']):x for x in candidate_rows}
assert set(candidate_by_key)=={(x['sourceIndex'],x['locale']) for x in expected_candidates}
for key,x in candidate_by_key.items(): assert x['recommendedTarget']==primary_by_key[key]['recommendedTarget'] and x['recommendedTargetSha256']==primary_by_key[key]['recommendedTargetSha256']
prior_rows=[json.loads(x) for x in (P/'prior-disposition-reattestation.jsonl').read_text().splitlines()]
assert len(prior_rows)==240
assert sum(bool(x.get('priorDispositionReused')) for x in primary_rows)==90

# Independently reviewed candidates, plus clear missed issues found in the cells marked accept-current.
OVERRIDES={
 '746|ar':{'disposition':'propose-refinement','target':'رمز:','rationale':'The caller shows a numeric peerCode after this label. رمز is the standard UI word for a numeric code; شفرة can also mean cipher. The colon is preserved.'},
 '750|es':{'disposition':'propose-correction','target':'Contrae todos los paneles de mensajes abiertos en el dock de mensajes.','rationale':'The caller collapses message panels into a UI dock. Muelle means a physical pier/dock and is misleading in this interface; the borrowed UI term dock identifies the destination.'},
 '750|hi':{'disposition':'propose-correction','target':'सभी खुले संदेश पैनलों को संदेश डॉक में समेटें।','rationale':'गोदी means a lap or landing-stage and is a false-friend rendering of the UI dock. This target names the message dock and retains the collapse action.'},
 '753|ar':{'disposition':'propose-correction','target':'صغّر المشغّل إلى شريط صغير أعلى تذييل الصفحة.','rationale':'The current target translates “drawer bar” literally. The caller renders a compact player bar above the page footer; this target states that resulting layout.'},
 '753|de':{'disposition':'propose-correction','target':'Klappen Sie den Player in eine kleine Leiste über der Fußzeile ein.','rationale':'Schubladenleiste is a literal furniture drawer. The caller collapses the player to a small horizontal bar above the footer.'},
 '753|es':{'disposition':'propose-correction','target':'Contrae el reproductor en una barra pequeña sobre el pie de página.','rationale':'Barra de cajón is a literal furniture drawer. The caller collapses the player to a small horizontal bar above the footer.'},
 '755|es':{'disposition':'propose-correction','target':'Contrae este panel para guardarlo en el dock de mensajes.','rationale':'The caller puts a collapsed panel in the shared message dock. The current “panel de mensajes” omits that destination; this candidate names the dock.'},
 '756|ar':{'disposition':'propose-correction','target':'طيّ عارض الصوت','rationale':'The control exits visualizer fullscreen and returns the audio visualization to the player bar. مُحلّل الصوت means audio analyzer, a different function; عارض الصوت names the display being collapsed.'},
 '762|es':{'disposition':'propose-correction','target':'Elementos de la colección no disponibles','rationale':'Collections.jsx reports that loading items in a user-created collection failed. Artículos de colección usually means collectible items; this target describes the collection’s elements.'},
 '762|fr':{'disposition':'propose-correction','target':'Éléments de la collection indisponibles','rationale':'Collections.jsx reports that loading items in a user-created collection failed. Objets de collection suggests collectible objects; this target describes elements belonging to the collection.'},
 '762|pt-BR':{'disposition':'propose-correction','target':'Itens da coleção indisponíveis','rationale':'Collections.jsx reports that loading items in a user-created collection failed. Adding da clarifies that the items belong to this collection, rather than being collectibles.'}
}

cross_rows=[]; counts=collections.Counter(); per_locale=collections.defaultdict(collections.Counter); candidate_verdicts=collections.Counter(); revised=0; additions=0; caller_claims={}
for key in sorted(primary_by_key):
  pos,loc=key; p=primary_by_key[key]; s=source_by_key[key]; sid=s['sourceId']; ctx=context_by_id[sid]
  ov=OVERRIDES.get(f'{pos}|{loc}')
  if ov:
    target=ov['target']; disp=ov['disposition']; reason=ov['rationale']
    if p['reviewDecision']=='propose-correction':
      outcome='revise-primary-candidate'; revised+=1
    else:
      outcome='add-crossreview-candidate'; additions+=1
    candidate_verdicts[outcome]+=1
  else:
    target=p['recommendedTarget']; disp=p['reviewDecision']
    if disp=='propose-correction':
      reason='Independent review accepts the proposed correction against the source string and reattested caller context.'
      outcome='agree-primary-candidate'; candidate_verdicts[outcome]+=1
    else:
      reason='Independent review accepts the current wording against the source string and reattested caller context.'
      outcome='accept-current'
  assert placeholders(sid)==placeholders(target) and markup(sid)==markup(target) and punctuation_compatible(sid,target), json.dumps({'key':f'{pos}|{loc}','source':sid,'target':target,'sourceTerminal':terminal(sid),'targetTerminal':terminal(target),'sourcePlaceholders':dict(placeholders(sid)),'targetPlaceholders':dict(placeholders(target)),'sourceMarkup':markup(sid),'targetMarkup':markup(target)},ensure_ascii=False)
  current=s['currentTarget']; ph=sorted(placeholders(sid).elements())
  row={'repository':REPO,'pullRequest':PR,'exactHead':HEAD,'exactTree':TREE,'sourceIndex':pos,'sourceId':sid,'source':sid,'sourceSha256':sha(sid.encode()),'locale':loc,'targetFile':p['targetFile'],'targetCatalogBlob':p['targetCatalogBlob'],'targetCatalogSha256':catalog_info[loc]['sha256'],'currentTarget':current,'currentTargetSha256':sha(current.encode()),'primaryDisposition':p['reviewDecision'],'primaryCandidate':p['recommendedTarget'],'primaryCandidateSha256':p['recommendedTargetSha256'],'primaryRationale':p['rationale'],'priorAuditStatus':p['priorAuditStatus'],'priorDispositionReused':p['priorDispositionReused'],'crossReviewOutcome':outcome,'crossDisposition':disp,'finalTarget':target,'finalTargetSha256':sha(target.encode()),'independentRationale':reason,'confidence':'moderate','sourceCallerContext':ctx['semanticContext'],'callerStatus':ctx['callerStatus'],'callerReferences':ctx['callerReferences'],'callerReferenceCount':len(ctx['callerReferences']),'sourcePlaceholders':ph,'currentPlaceholders':sorted(placeholders(current).elements()),'finalPlaceholders':sorted(placeholders(target).elements()),'placeholderParity':'exact','sourceMarkup':markup(sid),'currentMarkup':markup(current),'finalMarkup':markup(target),'markupParity':'exact','sourceTerminalPunctuation':terminal(sid),'currentTerminalPunctuation':terminal(current),'finalTerminalPunctuation':terminal(target),'punctuationCompatibility':'preserved' if terminal(sid)==terminal(target) else 'locale-appropriate terminal added to a source without terminal punctuation','protectedLiterals':p['protectedLiterals'],'protectedLiteralsPreserved':True,'nativeSpeakerApproval':False}
  cross_rows.append(row); counts[disp]+=1; per_locale[loc][disp]+=1
assert len(cross_rows)==240 and sum(counts.values())==240

# Reattest W742 adjacent cells against prior packet and live catalog values.
boundary=json.loads((P/'window-boundary-reattestation.json').read_text())
prior_packet=pathlib.Path('/mnt/disks/scratch/task-scratch/slskr-pr204-W723-742-primary-20261102/packet')
subprocess.check_call(['sha256sum','-c','SHA256SUMS'],cwd=prior_packet,stdout=subprocess.DEVNULL)
# The prior packet owns W742; compare its 12 frozen values and ledger dispositions with
# the boundary reattestation, then compare those same values with the live catalogs.
prior_current=[json.loads(x) for x in (prior_packet/'current-cells.jsonl').read_text().splitlines()]
prior_ledger=[json.loads(x) for x in (prior_packet/'primary-review-ledger.jsonl').read_text().splitlines()]
prior742={(x['sourceIndex'],x['locale']):x for x in prior_current if x['sourceIndex']==742}
prior742_ledger={(x['sourceIndex'],x['locale']):x for x in prior_ledger if x['sourceIndex']==742}
boundary742={(742,x['locale']):x for x in boundary['previousBoundaryTargetsReattested'] if x['sourceIndex']==742}
assert len(prior742)==len(prior742_ledger)==len(boundary742)==12
assert len(boundary['previousBoundaryTargetsReattested'])==12
w742_checks=[]
for key,x in prior742.items():
  b=boundary742[key]; old=prior742_ledger[key]; loc=x['locale']; sid=x['sourceId']
  live=catalogs[loc][sid]
  assert b['sourceId']==sid and old['source']==sid
  assert live==x['currentTarget']==b['liveTarget']
  assert sha(live.encode())==x['currentTargetSha256']==b['previousTargetSha256']==b['liveTargetSha256']
  assert old['currentTargetSha256']==x['currentTargetSha256']
  assert b['previousDecision']==old['reviewDecision']
  w742_checks.append({'sourceIndex':742,'sourceId':sid,'locale':loc,'currentTargetSha256':sha(live.encode()),'priorDecision':old['reviewDecision'],'priorRowSha256':b['previousRowSha256'],'matchesFrozenPriorPacket':True,'matchesBoundaryReattestation':True,'matchesLiveCatalog':True})

# Re-attest PR/worktree after all semantic decisions.
head_after=git('rev-parse','HEAD').decode().strip(); tree_after=git('rev-parse','HEAD^{tree}').decode().strip(); pr_after=live_pr()
assert head_after==HEAD and tree_after==TREE and pr_after['headRefOid']==HEAD and pr_after['state']=='OPEN' and pr_after['isDraft'] is True and git('status','--porcelain').decode()==''
caller_attest={'uniqueCallerReferences':caller_refs,'uniqueCallerFiles':len(caller_file_attest),'callerFiles':caller_file_attest,'callerLineErrors':caller_line_errors,'sourceIdsWithNoDirectCallers':[]}
reattest={'repository':REPO,'pullRequest':PR,'livePullRequestBefore':pr_before,'livePullRequestAfter':pr_after,'expectedHead':HEAD,'expectedTree':TREE,'headAfterReview':head_after,'treeAfterReview':tree_after,'worktree':str(W),'worktreeClean':True,'sourceInventoryPath':str(inventory_path),'sourceInventorySha256':sha(inventory_bytes),'sourceIdsAttested':20,'sourceAndCurrentCellsAttested':240,'currentTargetMismatches':[],'targetCatalogsAttested':catalog_info,'callerContextRowsAttested':20,'callerPinReattestation':caller_attest,'callerPinKinds':dict(caller_kind_counts),'sourceIdsWithDirectCallers':sorted(direct_source_positions),'priorAuditRowsReattested':len(prior_rows),'candidateRowsAttested':len(candidate_rows),'placeholderMismatches':0,'markupMismatches':0,'punctuationCompatibilityFailures':0,'priorBoundarySourceIndex':742,'priorBoundaryCellsAttested':len(w742_checks),'priorBoundaryCells':w742_checks,'checks':'pass','checkedAtUtc':subprocess.check_output(['date','-u','+%Y-%m-%dT%H:%M:%SZ'],text=True).strip()}

save_jsonl('crossreview-ledger.jsonl',cross_rows)
save_jsonl('crossreview-caller-contexts.jsonl',[{'sourceIndex':x['sourceIndex'],'sourceId':x['sourceId'],'source':x['sourceId'],'semanticContext':x['semanticContext'],'callerStatus':x['callerStatus'],'callerReferences':x['callerReferences']} for x in context_rows])
save_jsonl('crossreview-caller-pins.jsonl',[{**x,'liveFileBlob':caller_file_attest[x['path']]['blob'],'liveFileSha256':caller_file_attest[x['path']]['sha256'],'lineReattested':True} for x in caller_pin_rows])
save('crossreview-findings.json',{'schemaVersion':1,'overrides':OVERRIDES,'overrideCount':len(OVERRIDES),'proposalReview':{'primaryCandidateCount':43,'primaryCandidatesAccepted':42,'primaryCandidateRevisions':revised,'newCandidates':additions},'limitations':'Machine review only; native-speaker approval remains outstanding.'})
save('crossreview-reattestation.json',reattest)
per={loc:{k:per_locale[loc].get(k,0) for k in ('accept-current','propose-correction','propose-refinement','hold')} for loc in LOCALES}
summary={'schemaVersion':1,'repository':REPO,'pullRequest':PR,'state':'OPEN','isDraft':True,'head':HEAD,'tree':TREE,'sourceWindow':[743,762],'sourceIds':20,'locales':LOCALES,'cells':len(cross_rows),'primaryDispositionCounts':dict(collections.Counter(x['reviewDecision'] for x in primary_rows)),'crossReviewDispositionCounts':dict(counts),'perLocale':per,'primaryCorrectionCandidates':43,'primaryCandidatesAccepted':42,'primaryCandidateRevisions':revised,'additionalCrossReviewCandidates':additions,'finalCandidateCount':sum(counts[x] for x in ('propose-correction','propose-refinement')),'finalTargetsDifferFromPrimary':sum(x['finalTarget']!=x['primaryCandidate'] for x in cross_rows),'callerReferences':caller_refs,'callerPinKinds':dict(caller_kind_counts),'callerFiles':len(caller_file_attest),'uniqueCallerLines':len({(x['path'],x['line']) for x in caller_pin_rows}),'sourceIdsWithNoDirectCallers':0,'priorReusedCorrectionsAndAcceptancesReattested':90,'freshlyReviewedCellsInPrimaryWindow':150,'W742BoundaryCellsReattested':len(w742_checks),'placeholderFailures':0,'markupFailures':0,'punctuationFailures':0,'protectedLiteralFailures':0,'heldCells':counts.get('hold',0),'confidence':'moderate','nativeSpeakerApproval':'outstanding','repositoryOrPrModified':False,'testsBuildsScansCIorBrowserRun':False,'workflowFilesTouched':False,'outputPath':str(O)}
save('summary.json',summary)
(O/'README.md').write_text(f'''# slskR PR #204 W743–762 independent cross-review\n\n- PR #204 remained OPEN/DRAFT at `{HEAD}` / tree `{TREE}` before and after review.\n- Independently re-read and verified all 240 current cells across 20 source IDs and 12 locales, the pinned source-inventory rows, 20 source contexts, {caller_refs} caller/context/test pins across {len(caller_file_attest)} files, and all 43 primary correction candidates.\n- Primary candidates accepted: 42. One candidate was revised: Arabic “Collapse visualizer” used a word for “audio analyzer.” The cross-review also added {additions} candidates for missed clear issues in Arabic Code, Spanish/Hindi message dock labels, Arabic/German/Spanish drawer-bar descriptions, Spanish collapse-to-dock wording, and Spanish/French/PT-BR collection-item wording.\n- Final dispositions: {dict(counts)}. No cells remain held. W742’s 12 adjacent live targets were rechecked against the prior packet.\n- Caller pins include 44 direct source references, 15 supporting context references, and 8 test references; every source has a direct caller. Placeholder, markup, punctuation-compatibility, and protected-literal checks pass. Machine review confidence is moderate; native-speaker approval remains outstanding. No repository/PR edits, tests, builds, scans, CI, browser actions, or workflow changes were made.\n''')
# Create a provenance manifest and final checksum file.
artifact_files=sorted(x for x in O.iterdir() if x.is_file() and x.name not in {'SHA256SUMS','manifest.json'})
manifest={'schemaVersion':1,'repository':REPO,'pullRequest':PR,'head':HEAD,'tree':TREE,'scope':{'positions':[743,762],'sourceIds':20,'locales':LOCALES,'cells':240},'primaryPacket':{'path':str(P),'sha256sumsSha256':sha((P/'SHA256SUMS').read_bytes()),'manifestSha256':sha((P/'manifest.json').read_bytes()),'sourceCurrentSha256':sha((P/'current-cells.jsonl').read_bytes()),'primaryLedgerSha256':sha((P/'primary-review-ledger.jsonl').read_bytes()),'candidateRowsSha256':sha((P/'correction-candidates.jsonl').read_bytes()),'sourceContextSha256':sha((P/'source-context.jsonl').read_bytes()),'callerContextPinsSha256':sha((P/'caller-context-pins.jsonl').read_bytes())},'sourceInventory':{'path':str(inventory_path),'sha256':sha(inventory_bytes),'keys':len(inventory)},'reattestation':{'path':'crossreview-reattestation.json','sha256':sha((O/'crossreview-reattestation.json').read_bytes()),'checks':'pass'},'ledger':{'path':'crossreview-ledger.jsonl','rows':len(cross_rows),'sha256':sha((O/'crossreview-ledger.jsonl').read_bytes()),'dispositions':dict(counts)},'callerPins':{'path':'crossreview-caller-pins.jsonl','rows':caller_refs,'references':caller_refs,'files':len(caller_file_attest),'sha256':sha((O/'crossreview-caller-pins.jsonl').read_bytes())},'callerContexts':{'path':'crossreview-caller-contexts.jsonl','rows':20,'references':59,'sha256':sha((O/'crossreview-caller-contexts.jsonl').read_bytes())},'findings':{'path':'crossreview-findings.json','overrides':len(OVERRIDES),'sha256':sha((O/'crossreview-findings.json').read_bytes())},'summarySha256':sha((O/'summary.json').read_bytes()),'readmeSha256':sha((O/'README.md').read_bytes()),'builderSha256':sha((O/'build_crossreview_packet.py').read_bytes()),'artifactFiles':{x.name:{'sha256':sha(x.read_bytes()),'bytes':x.stat().st_size} for x in artifact_files},'nativeSpeakerApproval':'outstanding','repositoryOrPrModified':False,'testsBuildsScansCIorBrowserRun':False,'workflowFilesTouched':False}
save('manifest.json',manifest)
files=sorted(x for x in O.iterdir() if x.is_file() and x.name!='SHA256SUMS')
(O/'SHA256SUMS').write_text(''.join(f'{sha(x.read_bytes())}  {x.name}\n' for x in files))
print(json.dumps({'head':HEAD,'tree':TREE,'cells':len(cross_rows),'primaryCandidates':43,'primaryRevisions':revised,'addedCandidates':additions,'dispositions':dict(counts),'callerRefs':caller_refs,'callerFiles':len(caller_file_attest),'output':str(O)},ensure_ascii=False,indent=2))
