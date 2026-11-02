import collections,hashlib,json,re,subprocess,os
from pathlib import Path
ROOT=Path('/mnt/disks/scratch/task-scratch/slskr-transfergroup-selected-labels-20261102')
OUT=Path('/mnt/disks/scratch/task-scratch/slskr-transfergroup-selected-labels-crossreview-by-b-20261102')
WORK=Path('/mnt/disks/scratch/task-worktrees/localization-20261102/slskr-pr204-w503-522')
HEAD='aa106d2505de8c9ace2d7d6dbf2af9777651947d'; TREE='f99e717b4b77c8da098e7b8fc163926d4d32e926'
LOCALES=['ar','de','es','fr','hi','id','ja','ko','pt-BR','vi','zh-Hans','zh-Hant']
FILES={x:f'web/src/lib/locales/ui-labels.{x}.json' for x in LOCALES}
IDS=['Retry selected','Cancel selected','Remove selected']
OLD=['Retry{all}','Cancel{all}','Remove{all}']
ACTIONS={'Retry selected':'Retry','Cancel selected':'Cancel','Remove selected':'Remove'}
PROTECTED=[]
def j(p): return json.loads(Path(p).read_text(encoding='utf8'))
def jl(p): return [json.loads(x) for x in Path(p).read_text(encoding='utf8').splitlines() if x.strip()]
def wj(p,x): Path(p).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
def wjl(p,x): Path(p).write_text(''.join(json.dumps(r,ensure_ascii=False,sort_keys=True,separators=(',',':'))+'\n' for r in x),encoding='utf8')
def hb(b): return hashlib.sha256(b).hexdigest()
def hs(s): return hb(s.encode('utf8'))
def g(*a): return subprocess.check_output(['git',*a],cwd=WORK,text=True).strip()
def gb(p): return subprocess.check_output(['git','show',f'{HEAD}:{p}'],cwd=WORK)
def placeholders(s): return sorted(set(re.findall(r'\{[A-Za-z][A-Za-z0-9_]*\}',s)))
def markup(s): return re.findall(r'</?[A-Za-z][^>]*>',s)
def pr(): return json.loads(subprocess.check_output(['gh','pr','view','204','--repo','snapetech-org/slskR','--json','state,isDraft,headRefOid']))
OUT.mkdir(parents=True,exist_ok=True)
subprocess.check_call(['sha256sum','-c','SHA256SUMS'],cwd=ROOT,stdout=subprocess.DEVNULL)
pin=pr()
assert pin=={'state':'OPEN','isDraft':True,'headRefOid':HEAD}
assert g('rev-parse','HEAD')==HEAD and g('rev-parse','HEAD^{tree}')==TREE and g('status','--porcelain')==''
rec=j(ROOT/'recommendation.json')
assert rec['livePullRequest']['head']==HEAD and rec['livePullRequest']['tree']==TREE
assert rec['livePullRequest']['state']=='OPEN' and rec['livePullRequest']['isDraft'] is True
new=jl(ROOT/'new-targets.jsonl'); retire=jl(ROOT/'retire-all-keys.jsonl')
assert len(new)==36 and len(retire)==36
assert {(r['sourceId'],r['locale']) for r in new}=={(i,l) for i in IDS for l in LOCALES}
assert {(r['sourceId'],r['locale']) for r in retire}=={(i,l) for i in OLD for l in LOCALES}
# Reattest all 12 catalogs, exact new keys, base actions, legacy entries, and the caller/source line evidence.
cats={}; rawcats={}; blobs={}
for l,p in FILES.items():
 raw=gb(p); rawcats[l]=raw; cats[l]=json.loads(raw); blobs[l]=g('rev-parse',f'{HEAD}:{p}')
 att=next(x for x in rec['catalogAttestations'] if x['locale']==l)
 assert att['path']==p and att['blob']==blobs[l] and att['fileSha256']==hb(raw)
for l in LOCALES:
 for k in IDS: assert k not in cats[l]
 for k,v in rec['existingSingleActionTranslations'][l].items(): assert cats[l][k]==v
for r in new:
 assert r['decision']=='recommend-add' and r['locale'] in LOCALES and r['sourceId'] in IDS
 assert r['sourceIdSha256']==hs(r['sourceId']) and r['targetSha256']==hs(r['target'])
 assert r['sourcePlaceholders']==[] and r['targetPlaceholders']==[] and r['sourceMarkup']==[] and r['targetMarkup']==[]
 assert r['placeholderParity'] and r['markupParity']
for r in retire:
 assert r['recommendation']=='remove-key-after-TransferGroup-source-fix'
 assert r['sourceId'] in OLD and r['locale'] in LOCALES
 assert r['sourcePlaceholders']==['{all}'] and r['targetPlaceholders']==['{all}'] and r['placeholderParity']
 assert cats[r['locale']][r['sourceId']]==r['currentTarget']
 assert hs(r['currentTarget'])==r['currentTargetSha256']
# Reattest caller evidence hashes, line text and exact source positions.
for group in ('transferGroup','interfaceLocale'):
 pinrec=rec['sourceCallerPins'][group]; p=pinrec['path']; raw=gb(p)
 assert g('rev-parse',f'{HEAD}:{p}')==pinrec['blob'] and hb(raw)==pinrec['fileSha256']
 lines=raw.decode('utf8').splitlines()
 for e in pinrec['lineEvidence']:
  assert e['path']==p and lines[e['line']-1]==e['text'] and hs(e['text'])==e['lineSha256']
# Focused key search verifies the three old IDs have only the six expected caller references.
search=subprocess.run(['rg','-n','Retry\\{all\\}|Cancel\\{all\\}|Remove\\{all\\}','web/src','--glob','!web/src/lib/locales/**'],cwd=WORK,text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
assert search.returncode==0,search.stderr
hits=search.stdout.splitlines()
assert len(hits)==6 and all(':web/src/components/Transfers/TransferGroup.jsx:' in ':'+h for h in hits),hits
for s in IDS:
 assert rec['sourceEditPlan']['newEnglishSourceIds'][IDS.index(s)]['sourceId']==s
# Cross-review decisions: accept all 36 full-action targets; retire legacy values only after the covered source rewrite.
rows=[]; counts=collections.Counter(); changed=[]; old_by={(r['sourceId'],r['locale']):r for r in retire}
new_by={(r['sourceId'],r['locale']):r for r in new}
for l in LOCALES:
 for sourceid in IDS:
  r=new_by[(sourceid,l)]
  disk=cats[l]['Remove and Delete File(s) from Disk'] if sourceid=='Remove selected' else None
  base=cats[l][ACTIONS[sourceid]]
  if sourceid=='Remove selected':
   disposition='hold'; target=None; th=None
   rationale='Hold the wording until remove semantics are clarified: the ordinary path passes remove=true, and the pinned route treats that as a request to remove the local file. The adjacent disk-delete action reaches the same file-removal condition, so the proposed from-list distinction is not established by the code path.'
   counts['held-new-target']+=1
  else:
   disposition='accept'; target=r['target']; th=r['targetSha256']
   rationale='Accepted: the complete localized action phrase fits the selected-transfer button, avoids English suffix concatenation, and matches the pinned caller.'
   counts['accepted-new-target']+=1
  row={'schemaVersion':1,'recordType':'new-selected-action-cross-review','repository':'snapetech-org/slskR','pullRequest':204,'exactHead':HEAD,'exactTree':TREE,'sourceId':sourceid,'sourceIdSha256':r['sourceIdSha256'],'locale':l,'currentCatalogKeyPresent':False,'singleActionSourceId':ACTIONS[sourceid],'singleActionTranslation':base,'targetFile':FILES[l],'targetCatalogBlob':blobs[l],'primaryDisposition':r['decision'],'primaryTarget':r['target'],'primaryTargetHash':r['targetSha256'],'crossReviewDisposition':disposition,'crossReviewTarget':target,'crossReviewTargetHash':th,'crossReviewRationale':rationale,'confidence':'moderate','sourcePlaceholders':[],'targetPlaceholders':[],'placeholderParity':True,'sourceMarkup':[],'targetMarkup':[],'markupParity':True,'removeCallerSemantics':{'handlerDefaultDeleteFile':False,'selectedRemovePassesDeleteFileFalse':True,'selectedRemovePassesRemoveTrue':True,'activeRouteDeleteFilePredicate':'remove == true || deleteFile == true','activeRouteRemovesLocalPath':True,'separateDiskDeletePassesDeleteFileTrue':True,'separateDiskDeleteTitle':disk,'semanticDistinctionConfirmed':False} if sourceid=='Remove selected' else None,'callerRefs':['web/src/components/Transfers/TransferGroup.jsx:102','web/src/components/Transfers/TransferGroup.jsx:160','web/src/components/Transfers/TransferGroup.jsx:163','web/src/components/Transfers/TransferGroup.jsx:169','web/src/components/Transfers/TransferGroup.jsx:172','web/src/components/Transfers/TransferGroup.jsx:180','web/src/components/Transfers/TransferGroup.jsx:183'],'sourceEditPlanCoverage':'Replace both content and interfaceTextProps at the corresponding old key callsites with a complete selected-action key; Remove remains held pending semantic resolution.'}
  rows.append(row)
for l in LOCALES:
 for sourceid in OLD:
  r=old_by[(sourceid,l)]
  assert sourceid in cats[l]
  if sourceid=='Remove{all}':
   disposition='hold'; rationale='Hold retirement with the Remove selected target: the source action meaning is unresolved because the normal remove path also reaches file deletion. Do not retire this key until the caller behavior/label is clarified.'; counts['held-legacy-key']+=1
  else:
   disposition='retire-after-source-rewrite'; rationale='Retire after the covered Retry/Cancel caller references are changed to complete selected-action keys. The targeted source search found no other code references; the current catalog value only interpolates the English Selected suffix.'; counts['retire-after-source-rewrite']+=1
  row={'schemaVersion':1,'recordType':'legacy-selected-action-key-cross-review','repository':'snapetech-org/slskR','pullRequest':204,'exactHead':HEAD,'exactTree':TREE,'sourceId':sourceid,'sourceIdSha256':r['sourceIdSha256'],'locale':l,'currentTarget':r['currentTarget'],'currentTargetSha256':r['currentTargetSha256'],'targetFile':FILES[l],'targetCatalogBlob':blobs[l],'primaryDisposition':r['recommendation'],'crossReviewDisposition':disposition,'crossReviewTarget':None,'crossReviewTargetHash':None,'crossReviewRationale':rationale,'confidence':'high','sourcePlaceholders':['{all}'],'currentTargetPlaceholders':['{all}'],'retirementRemovesUnusedPlaceholderKey':disposition=='retire-after-source-rewrite','callerCoverage':{'currentExactCodeReferences':6,'coveredByPlan':6,'otherCodeReferences':0,'planCallsites':['content','interfaceTextProps']},'inputAttestationMismatches':[]}
  rows.append(row)
assert len(rows)==72 and counts['accepted-new-target']==24 and counts['held-new-target']==12 and counts['retire-after-source-rewrite']==24 and counts['held-legacy-key']==12
pin2=pr()
assert pin2==pin and g('rev-parse','HEAD')==HEAD and g('rev-parse','HEAD^{tree}')==TREE and g('status','--porcelain')==''
source_plan=rec['sourceEditPlan']
semantic_evidence=[]
semantic_lines={
 'web/src/components/Transfers/TransferGroup.jsx':[61,72,182,188,189],
 'web/src/components/Transfers/Transfers.jsx':[571,575,592,594,620,621],
 'web/src/lib/transfers.js':[160,164,165,167,168],
 'crates/slskr/src/route_dispatch_group_2.rs':[10],
 'crates/slskr/src/route_dispatch_group_2_transfer_files.rs':[22,24,50,51,52]
}
for path, linenos in semantic_lines.items():
 raw=gb(path); lines=raw.decode('utf8').splitlines(); blob=g('rev-parse',f'{HEAD}:{path}')
 for line in linenos:
  assert 1<=line<=len(lines)
  semantic_evidence.append({'path':path,'fileBlob':blob,'fileSha256':hb(raw),'line':line,'lineText':lines[line-1],'lineSha256':hs(lines[line-1])})
plan_review={'schemaVersion':1,'repository':'snapetech-org/slskR','pullRequest':204,'exactHead':HEAD,'exactTree':TREE,'decision':'partial-hold','retryCancelDecision':'accept','removeDecision':'hold','rationale':'The Retry/Cancel branches preserve one-item source keys and use complete localized keys for multiple selections in both visible content and title/accessibility text. All six exact old-key references are covered and no other code reference was found. Hold the Remove branch and its old catalog-key retirement: the pinned backend treats the normal remove=true request as local-file deletion, the same condition reached by deleteFile=true, contrary to the packet assertion that the first action only removes the transfer entry.','oldKeyCallerHits':hits,'expectedOldKeyCodeReferencesAfterPlan':0,'sourceEditPlan':source_plan,'semanticEvidencePins':semantic_evidence,'removeActionSemantics':{'defaultDeleteFile':False,'transferGroupCall':'handleRemoveAll(selected)','transferGroupDefaultFlag':'deleteFile=false','transfersRemoveCall':'removeAll(selected,false)','clientApiCall':{'remove':True,'deleteFile':False},'activeRouteFileDeletePredicate':'remove == true || deleteFile == true','activeRouteDeletesLocalPathWhenPredicateTrue':True,'separateDestructiveCall':'handleRemoveAll(selected,true)','separateDestructiveTitle':'Remove and Delete File(s) from Disk','crossReviewConclusion':'The normal Remove path and separate disk-delete path both satisfy the active route file-deletion predicate; clarify/fix behavior before approving Remove labels or retiring Remove{all}.'}}
wj(OUT/'source-edit-plan-crossreview.json',plan_review)
wjl(OUT/'cross-review-ledger.jsonl',rows)
# Preserve the exact proposal inputs in this independent packet.
(OUT/'primary-new-targets.jsonl').write_bytes((ROOT/'new-targets.jsonl').read_bytes())
(OUT/'primary-retire-all-keys.jsonl').write_bytes((ROOT/'retire-all-keys.jsonl').read_bytes())
input_files=['SHA256SUMS','new-targets.jsonl','retire-all-keys.jsonl','recommendation.json']
att={'schemaVersion':1,'head':HEAD,'tree':TREE,'livePr':pin2,'worktreeClean':True,'primarySha256ChecksVerified':True,'primaryInputHashes':{f:hb((ROOT/f).read_bytes()) for f in input_files},'catalogsReattested':12,'newTargetsReattested':36,'legacyRowsReattested':36,'callerSourceLinesReattested':len(rec['sourceCallerPins']['transferGroup']['lineEvidence'])+len(rec['sourceCallerPins']['interfaceLocale']['lineEvidence']),'removeSemanticEvidenceLinesReattested':len(semantic_evidence),'oldKeyCodeReferences':6,'oldKeyReferencesOutsideTransferGroup':0,'result':'pass'}
wj(OUT/'reattestation.json',att)
summary={'schemaVersion':1,'task':'Independent cross-review of packet-only TransferGroup selected-label proposal','repository':'snapetech-org/slskR','pullRequest':204,'state':'OPEN','isDraft':True,'exactHead':HEAD,'exactTree':TREE,'newTargetRows':36,'newTargetDispositions':{'accept':24,'refine':0,'hold':12},'legacyKeyRows':36,'legacyKeyDispositions':{'retire-after-source-rewrite':24,'hold':12},'totalLedgerRows':72,'sourceEditPlanDecision':'partial-hold','currentOldKeyCodeReferences':6,'coveredOldKeyCodeReferences':6,'otherOldKeyCodeReferences':0,'removeSemanticsReviewedForAllLocales':12,'catalogMismatches':0,'callerPinMismatches':0,'targetHashMismatches':0,'placeholderOrMarkupFailures':0,'blockers':['Remove vs disk-delete caller behavior conflicts: normal remove=true also deletes the local path in the pinned active route.'],'nativeSpeakerApproval':False,'browserReview':False}
wj(OUT/'summary.json',summary)
(OUT/'README.md').write_text('slskR PR #204 TransferGroup selected-label proposal cross-review\\n\\nExact head: '+HEAD+'\\nExact tree: '+TREE+'\\n\\nReviewed all 36 selected-action targets and all 36 legacy {all} locale entries. Retry/Cancel targets are accepted (24), and their 24 legacy keys can be retired after the covered caller rewrite. Hold the 12 Remove selected targets and 12 Remove{all} retirements. The six current exact-ID callsites are covered by the plan and the targeted source search found no other code references. The normal Remove path passes remove=true; the pinned route treats remove=true OR deleteFile=true as a request to remove the local path. This conflicts with the separate disk-delete label, so the Remove branch needs behavior clarification before its labels or old keys can be approved.\\n\\nPrimary packet checksums, catalog blobs/hashes, caller lines/blobs, current legacy values, target hashes, placeholders, and markup were re-attested. No repo/PR files, tests, builds, scans, CI, workflows, or browser work were changed or run. This is machine review, not native-speaker approval.\\n',encoding='utf8')
wj(OUT/'task.json',{'repository':'snapetech-org/slskR','pullRequest':204,'head':HEAD,'tree':TREE,'newTargets':36,'legacyKeyRetirements':36,'totalRows':72,'heldRemoveTargets':12,'heldRemoveLegacyKeys':12,'ledger':'cross-review-ledger.jsonl','readOnly':True})
(OUT/'INPUT_SHA256SUMS').write_text(''.join(hb((ROOT/f).read_bytes())+'  ../slskr-transfergroup-selected-labels-20261102/'+f+'\\n' for f in input_files),encoding='utf8')
os.chdir(OUT)
files=sorted(p.relative_to(OUT).as_posix() for p in OUT.rglob('*') if p.is_file() and p.name!='SHA256SUMS')
(OUT/'SHA256SUMS').write_text(''.join(hb((OUT/f).read_bytes())+'  '+f+'\\n' for f in files),encoding='utf8')
print(json.dumps({'counts':dict(counts),'sourcePlan':'partial-hold','oldCodeReferences':len(hits),'covered':6,'other':0,'files':len(files)+1,'output':str(OUT)},ensure_ascii=False,indent=2))

