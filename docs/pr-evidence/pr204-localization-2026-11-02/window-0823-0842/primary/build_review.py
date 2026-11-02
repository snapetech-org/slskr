import collections,hashlib,json,pathlib,re,subprocess
IN=pathlib.Path('/mnt/disks/scratch/task-scratch/slskr-pr204-window-0823-0842-primary-20261102')
OUT=pathlib.Path('/mnt/disks/scratch/task-scratch/slskr-pr204-window-0823-0842-primary-review-20261102')
WORK=pathlib.Path('/home/keith/Documents/code/task-worktrees/localization-20261102-slskr')
REPO='snapetech-org/slskR'; PR=204
HEAD='074dfc70d584707a215e87cb1fd1969198f76b2e'; TREE='9914a55bdfb938408a4bf1f98bb5ed98c24b78a8'
BRANCH='codex/slskr-l10n-audit-20261030'
LOCALES=['ar','de','es','fr','hi','id','ja','ko','pt-BR','vi','zh-Hans','zh-Hant']
START=822; END=841
C={
822:{'id':'Konfirmasi Mulai Ulang'},
824:{'ar':'التأكيد مطلوب','de':'Bestätigung erforderlich','es':'Se requiere confirmación','fr':'Confirmation requise','hi':'पुष्टि आवश्यक है','id':'Konfirmasi diperlukan','ja':'確認が必要','ko':'확인이 필요합니다','pt-BR':'Confirmação necessária','vi':'Cần xác nhận','zh-Hans':'需要确认','zh-Hant':'需要確認'},
825:{'hi':'पुष्टि की गई फ़ाइल कार्रवाइयाँ'},
826:{'ar':'تعارض','ja':'競合','ko':'충돌'},
827:{'ar':'تحليل التعارضات','hi':'विरोधाभासों का विश्लेषण','ja':'競合分析','ko':'충돌 분석'},
828:{'ar':'استراتيجية حل التعارضات','hi':'विरोधाभास सुलझाने की रणनीति','ja':'競合解決戦略','ko':'충돌 해결 전략'},
829:{'ar':'متعارضة:','es':'En conflicto:','fr':'En conflit :','ja':'競合:','ko':'충돌:'},
830:{'ar':'التعارضات','hi':'विरोधाभास','ja':'競合'},
831:{'ar':'التعارضات التي تم حلها:','hi':'सुलझाए गए विरोधाभास:'},
832:{'ar':'اتصل'},
833:{'vi':'Kết nối với Soulseek để tìm kiếm'},
834:{'ja':'検索するにはサーバーに接続してください。'},
835:{'ar':'اتصل بشبكة Soulseek إذا لم يكن الاتصال قائمًا بالفعل.','es':'Conéctese a la red Soulseek si todavía no se ha conectado.','fr':'Connectez-vous au réseau Soulseek si la connexion n’est pas déjà établie.','ja':'Soulseek ネットワークに接続してください（まだ接続していない場合）。','ko':'Soulseek 네트워크에 연결하세요(아직 연결되지 않은 경우).'},
836:{'id':'Hubungkan ke server untuk memuat rekomendasi yang disaring berdasarkan privasi.','ja':'プライバシーに配慮してフィルタリングされたおすすめを読み込むには、サーバーに接続してください。','vi':'Kết nối với máy chủ để tải các đề xuất được lọc theo quyền riêng tư.'},
837:{'ja':'アーティストのディスコグラフィー網羅状況を表示するには、サーバーに接続してください。','vi':'Kết nối với máy chủ để xem mức độ bao phủ đĩa nhạc của nghệ sĩ.','zh-Hans':'连接到服务器以查看艺人作品的收录覆盖情况。','zh-Hant':'連線到伺服器以查看藝人作品的收錄涵蓋情況。'},
839:{'ja':'Soulseek 標準の関心情報とおすすめを利用するには、サーバーに接続してください。','ko':'Soulseek 고유의 관심사와 추천 기능을 사용하려면 서버에 연결하세요.','zh-Hans':'连接到服务器以使用 Soulseek 原生的兴趣和推荐功能。','zh-Hant':'連線到伺服器以使用 Soulseek 原生的興趣與推薦功能。'},
840:{'fr':'Connectez-vous au serveur pour afficher les objectifs de l’album et suivre la progression.'},
841:{'hi':'कनेक्टेड'}
}
REFINEMENTS={(822,'id'),(829,'ar'),(833,'vi'),(840,'fr'),(841,'hi')}
WHY={
822:'Confirm Restart is a confirmation-dialog header. The Indonesian candidate uses a noun phrase, which fits a heading better than the current imperative Konfirmasikan.',
824:'The caller describes a policy safeguard that must stay enabled before downloads, scans, scrobbles, and file actions execute. The literal gate/door translations misstate this requirement; use a direct confirmation-required label.',
825:'The source is a plural label. The Hindi current target uses singular फ़ाइल कार्रवाई; the candidate marks multiple file actions.',
826:'These are data/record conflicts in the Mesh subject index and metadata portability workflow, not interpersonal disputes. The Arabic, Japanese, and Korean terms are corrected to data-conflict terminology.',
827:'Conflict Analysis summarizes conflicting metadata entries and Mesh records. The candidates avoid terms that suggest war or personal discord.',
828:'This label names a strategy for resolving metadata conflicts. The candidates use the data-conflict sense rather than a personal dispute.',
829:'This is a field label followed by a count of entries in conflict. The Spanish and French adjectives are awkward as standalone count labels; Japanese and Korean current wording is a sentence/people fighting; Arabic is refined to a clearer data-conflict term.',
830:'The label counts record conflicts in the Mesh index. The candidates avoid the interpersonal or armed-conflict sense.',
831:'This is a count label for metadata conflicts resolved by an import. The candidates use the data-conflict sense and state that the conflicts were resolved.',
832:'Connect is an action label/button in the app. The Arabic current target يتصل means “he connects,” not an action label; use the imperative اتصل.',
833:'This is an instruction to connect Soulseek before searching. The Vietnamese candidate adds the preposition with, which is the natural construction.',
834:'This appears as a search-input placeholder while no server is connected. The Japanese current target reads as a statement that the user connects and searches; the candidate is a direct instruction.',
835:'This is a setup instruction. The Arabic current wording is a noun phrase and has gendered agreement; Spanish agreement can attach to the feminine network rather than the user; French agreement points to the network; Japanese and Korean are statements rather than instructions.',
836:'This is helper text for privacy-filtered recommendations. Indonesian currently says “filtered privacy”; Japanese “filtered by privacy” is unnatural; Vietnamese “filtered privately” misses the privacy-protection sense.',
837:'The pinned caller is the Discography Concierge panel. “Artist coverage” means coverage/completeness of an artist’s discography, not broadcast or press coverage. The candidates state that context explicitly.',
839:'The caller title is Soulseek Native Discovery and the panel reads Soulseek interests. The Japanese/Korean wording is awkward or shifts native to default; 本机 in the Chinese targets means the local machine rather than native Soulseek functionality.',
840:'The French target cibles de l’album is a literal calque. objectifs de l’album is a more natural label for the album targets shown with completion status and progress.',
841:'Connected is rendered as a short state label for server/VPN connection status. Hindi कनेक्टेड avoids gender/number agreement in the current plural participle.'
}
DETAILS={
(822,'id'):'Use the nominal header form.',
(824,'ar'):'Replaces a literal gate translation with a required-confirmation label.',(824,'de'):'Replaces Bestätigungstore with the actual confirmation requirement.',(824,'es'):'Replaces puertas de confirmación with the policy meaning.',(824,'fr'):'Replaces portes de confirmation with the policy meaning.',(824,'hi'):'States that confirmation is required.',(824,'id'):'States that confirmation is required.',(824,'ja'):'States that confirmation is required.',(824,'ko'):'States that confirmation is required.',(824,'pt-BR'):'Replaces portas with the confirmation requirement.',(824,'vi'):'States that confirmation is required.',(824,'zh-Hans'):'Replaces the literal confirmation door with the requirement.',(824,'zh-Hant'):'Replaces the literal confirmation door with the requirement.',
(825,'hi'):'Uses a plural form for file actions.',
(826,'ar'):'تعارض is suitable for a data discrepancy.',(826,'ja'):'競合 is the software/data conflict term.',(826,'ko'):'충돌 is the data conflict term.',
(827,'ar'):'Uses the data-conflict term.',(827,'hi'):'Uses विरोधाभास for inconsistent records.',(827,'ja'):'Uses 競合 for data conflicts.',(827,'ko'):'Uses 충돌 for record conflicts.',
(828,'ar'):'Uses the data-conflict term.',(828,'hi'):'Names a strategy for resolving contradictory records.',(828,'ja'):'Uses the technical conflict-resolution term.',(828,'ko'):'Uses the technical conflict-resolution term.',
(829,'ar'):'Refines the adjective to the data-conflict sense.',(829,'es'):'Uses a natural count label: En conflicto.',(829,'fr'):'Uses a natural count label: En conflit.',(829,'ja'):'Uses a compact data-conflict count label.',(829,'ko'):'Replaces the current “fighting each other” phrase with a data-conflict label.',
(830,'ar'):'Uses the data-conflict plural.',(830,'hi'):'Uses the record-contradiction sense.',(830,'ja'):'Uses the data-conflict term.',(830,'ko'):'Uses the data-conflict term.',
(831,'ar'):'States that data conflicts have been resolved.',(831,'hi'):'States that record contradictions have been resolved.',
(832,'ar'):'Uses the imperative form for an action label.',(833,'vi'):'Adds the natural với preposition after Kết nối.',(834,'ja'):'Changes a declarative statement into the placeholder instruction.',
(835,'ar'):'Uses a neutral clause for the not-yet-connected condition.',(835,'es'):'Attaches the condition to the user, not to the network.',(835,'fr'):'Uses a gender-neutral established-connection clause.',(835,'ja'):'Uses a direct polite instruction.',(835,'ko'):'Uses a direct polite instruction.',
(836,'id'):'Changes filtered privacy to recommendations filtered for privacy.',(836,'ja'):'Uses natural phrasing for recommendations filtered with privacy in mind.',(836,'vi'):'Expresses filtering according to privacy protection.',
(837,'ja'):'Names discography coverage instead of an ambiguous coverage range.',(837,'vi'):'Names music/discography coverage instead of broadcast coverage.',(837,'zh-Hans'):'Names artist-work catalog coverage instead of news/report coverage.',(837,'zh-Hant'):'Names artist-work catalog coverage instead of report coverage.',
(839,'ja'):'Improves word order and identifies Soulseek’s standard interest/recommendation feature.',(839,'ko'):'Uses Soulseek-specific rather than default/basic interests.',(839,'zh-Hans'):'Changes 本机 (local machine) to 原生 (native).',(839,'zh-Hant'):'Changes 本機 (local machine) to 原生 (native).',
(840,'fr'):'Uses the natural French term objectifs for album targets.',(841,'hi'):'Avoids agreement on an unspecified status subject.'
}

def sha(b): return hashlib.sha256(b if isinstance(b,bytes) else b.encode()).hexdigest()
def run(args,text=True,cwd=None): return subprocess.check_output(args,text=text,cwd=cwd)
def git(*args,text=True): return run(['git','-C',str(WORK),*args],text=text)
def live():
 pr=json.loads(run(['gh','pr','view',str(PR),'--repo',REPO,'--json','state,isDraft,headRefOid,headRefName,baseRefOid,url']))
 tree=run(['gh','api',f'repos/{REPO}/commits/{pr["headRefOid"]}','--jq','.commit.tree.sha']).strip()
 remote=run(['git','ls-remote',f'https://github.com/{REPO}.git',f'refs/heads/{pr["headRefName"]}']).split()[0]
 return pr,tree,remote
def placeholders(s): return collections.Counter(re.findall(r'\{([A-Za-z][A-Za-z0-9_]*)\}',s))
def markup(s): return re.findall(r'</?[A-Za-z][^>]*>',s)
# Verify exact live PR, remote branch, snapshot, and clean worktree before reviewing.
head_meta=json.loads((IN/'exact-head.json').read_text())
assert (head_meta['repository'],head_meta['pullRequest'],head_meta['head'],head_meta['tree'],head_meta['branch'],head_meta['sourceIndexZeroBasedInclusive'])==(REPO,PR,HEAD,TREE,BRANCH,[822,841])
pr,api_tree,remote=live()
assert pr['state']=='OPEN' and pr['isDraft'] and pr['headRefOid']==HEAD and pr['headRefName']==BRANCH and api_tree==TREE and remote==HEAD
assert git('rev-parse','HEAD').strip()==HEAD and git('rev-parse','HEAD^{tree}').strip()==TREE and git('branch','--show-current').strip()==BRANCH and not git('status','--porcelain').strip()
# Hash all supplied input artifacts (the provided directory has no SHA256SUMS file).
input_hashes={p.name:sha(p.read_bytes()) for p in sorted(IN.iterdir()) if p.is_file()}
# Rebuild the exact ordered English key inventory and all locale catalog pins from the live tree.
cat_meta=json.loads((IN/'catalog-reattestation.json').read_text())
loc_paths={loc:f'web/src/lib/locales/ui-labels.{loc}.json' for loc in LOCALES}
catalogs={}; catalog_rows=[]
for loc in LOCALES:
 rel=loc_paths[loc]; raw=git('show',f'{HEAD}:{rel}',text=False); obj=json.loads(raw)
 blob=git('rev-parse',f'HEAD:{rel}').strip(); supplied=next(x for x in cat_meta['catalogs'] if x['locale']==loc)
 assert sha(raw)==supplied['fileSha256'] and blob==supplied['gitBlob'] and len(obj)==supplied['keyCount']==5441
 catalogs[loc]=obj; catalog_rows.append({'locale':loc,'path':rel,'blob':blob,'fileSha256':sha(raw),'keyCount':len(obj)})
keysets=[set(v) for v in catalogs.values()]; assert all(s==keysets[0] for s in keysets)
keys=sorted(keysets[0]); assert len(keys)==5441 and sha('\n'.join(keys))==cat_meta['orderedKeySetSha256']
inventory=[json.loads(x) for x in (IN/'current-source-inventory.jsonl').read_text().splitlines()]
assert len(inventory)==len(keys) and [x['sourceId'] for x in inventory]==keys
assert all(x['sourceIndex']==i and x['sourceSha256']==sha(x['sourceId']) for i,x in enumerate(inventory))
selected=keys[START:END+1]; assert len(selected)==20 and selected[0]=='Confirm Restart' and selected[-1]=='Connected'
# Reattest current-cell input exactly to catalog values and freeze source+target hashes.
input_cells=[json.loads(x) for x in (IN/'current-cells.jsonl').read_text().splitlines()]
assert len(input_cells)==240 and len({(x['sourceIndex'],x['locale']) for x in input_cells})==240
for c in input_cells:
 assert c['sourceId']==keys[c['sourceIndex']] and c['sourceSha256']==sha(c['sourceId'])
 assert catalogs[c['locale']][c['sourceId']]==c['target'] and c['targetSha256']==sha(c['target'])
 assert c['sourcePlaceholders']==dict(placeholders(c['sourceId'])) and c['targetPlaceholders']==dict(placeholders(c['target']))
# Reattest all supplied source caller line/context pins to file bytes and exact blobs.
caller_inputs=[json.loads(x) for x in (IN/'caller-context-pins.jsonl').read_text().splitlines()]
caller_rows=[]
for c in caller_inputs:
 raw=git('show',f'{HEAD}:{c["path"]}',text=False); lines=raw.decode().splitlines(); n=c['line']
 assert 1<=n<=len(lines)
 for item in c['contextLines']:
  assert lines[item['line']-1]==item['text'],(c['sourceId'],c['path'],item['line'])
 caller_rows.append({**c,'fileBlob':git('rev-parse',f'HEAD:{c["path"]}').strip(),'fileSha256':sha(raw),'callerLineSha256':sha(lines[n-1])})
# Boundary source IDs and all 12 live catalog values around the selected window.
boundaries=[]
for idx in (START-1,END+1):
 key=keys[idx]
 for loc in LOCALES:
  val=catalogs[loc][key]
  boundaries.append({'sourceIndex':idx,'sourceId':key,'sourceSha256':sha(key),'locale':loc,'target':val,'targetSha256':sha(val)})
# Review each frozen cell in its caller context. No placeholders or markup occur in this window;
# Soulseek is a protected product name and must remain verbatim wherever it appears in the source.
ctx_by=collections.defaultdict(list)
for r in caller_rows: ctx_by[r['sourceId']].append(r)
source_idx={key:i for i,key in enumerate(keys)}
ledger=[]; proposal_rows=[]; counts=collections.Counter(); per_locale=collections.defaultdict(collections.Counter)
for c in input_cells:
 i=c['sourceIndex']; loc=c['locale']; key=c['sourceId']; candidate=C.get(i,{}).get(loc)
 if candidate is not None:
  assert candidate!=c['target'],(i,loc,'candidate equals current')
 disp='accept-current'; final=c['target']; rationale='The current translation preserves the source meaning and technical terminology in the supplied caller context; no material issue was identified.'
 if candidate is not None:
  disp='propose-refinement' if (i,loc) in REFINEMENTS else 'propose-correction'; final=candidate
  rationale=WHY[i]+' '+DETAILS[(i,loc)]
 source_ph=placeholders(key); current_ph=placeholders(c['target']); final_ph=placeholders(final)
 source_tags=markup(key); current_tags=markup(c['target']); final_tags=markup(final)
 assert source_ph==current_ph==final_ph and source_tags==current_tags==final_tags
 protected=['Soulseek'] if 'Soulseek' in key else []
 current_missing=[p for p in protected if p not in c['target']]
 final_missing=[p for p in protected if p not in final]
 assert not final_missing,(i,loc,final_missing)
 row={**c,'head':HEAD,'tree':TREE,'sourceText':key,'currentTarget':c['target'],'recommendedTarget':candidate,'finalTarget':final,'recommendedTargetSha256':sha(candidate) if candidate is not None else None,'finalTargetSha256':sha(final),'disposition':disp,'rationale':rationale,'confidence':'moderate','callerContextPins':ctx_by[key],'sourcePlaceholders':dict(source_ph),'currentTargetPlaceholders':dict(current_ph),'finalTargetPlaceholders':dict(final_ph),'placeholderParity':source_ph==current_ph==final_ph,'sourceMarkup':source_tags,'currentMarkup':current_tags,'finalMarkup':final_tags,'markupParity':source_tags==current_tags==final_tags,'protectedLiterals':protected,'currentProtectedMismatches':current_missing,'finalProtectedMismatches':final_missing,'nativeSpeakerApproval':False}
 ledger.append(row); counts[disp]+=1; per_locale[loc][disp]+=1
 if candidate is not None: proposal_rows.append(row)
assert len(ledger)==240
for k in ('accept-current','propose-correction','propose-refinement','hold'): counts.setdefault(k,0)
# Exact head/ref/worktree/catalog reattestation after judgments.
pr2,tree2,remote2=live(); repo_state={'head':git('rev-parse','HEAD').strip(),'tree':git('rev-parse','HEAD^{tree}').strip(),'branch':git('branch','--show-current').strip(),'status':git('status','--porcelain').strip()}
assert pr2['state']=='OPEN' and pr2['isDraft'] and pr2['headRefOid']==HEAD and pr2['headRefName']==BRANCH and tree2==TREE and remote2==HEAD
assert repo_state=={'head':HEAD,'tree':TREE,'branch':BRANCH,'status':''}
for loc in LOCALES:
 rel=loc_paths[loc]; raw=git('show',f'{HEAD}:{rel}',text=False); assert sha(raw)==next(x['fileSha256'] for x in catalog_rows if x['locale']==loc)
(OUT/'primary-review-ledger.jsonl').write_text(''.join(json.dumps(x,ensure_ascii=False,sort_keys=True)+'\n' for x in ledger))
(OUT/'correction-candidates.jsonl').write_text(''.join(json.dumps(x,ensure_ascii=False,sort_keys=True)+'\n' for x in proposal_rows))
(OUT/'caller-context-reattestation.jsonl').write_text(''.join(json.dumps(x,ensure_ascii=False,sort_keys=True)+'\n' for x in caller_rows))
(OUT/'source-boundaries.jsonl').write_text(''.join(json.dumps(x,ensure_ascii=False,sort_keys=True)+'\n' for x in boundaries))
(OUT/'catalog-pins.json').write_text(json.dumps({'head':HEAD,'tree':TREE,'catalogs':catalog_rows,'orderedKeyCount':len(keys),'orderedKeySetSha256':sha('\n'.join(keys))},ensure_ascii=False,indent=2,sort_keys=True)+'\n')
source_slice=[{'sourceIndex':i,'sourceId':keys[i],'sourceSha256':sha(keys[i])} for i in range(START,END+1)]
summary={'schemaVersion':1,'repository':REPO,'pullRequest':PR,'head':HEAD,'tree':TREE,'branch':BRANCH,'window':'W823-W842','zeroBasedSourceIndexInclusive':[START,END],'sourceCount':20,'cellCount':240,'locales':LOCALES,'sourceIds':[x['sourceId'] for x in source_slice],'sourceWindowSha256':sha(json.dumps(source_slice,ensure_ascii=False,sort_keys=True,separators=(',',':'))),'counts':dict(counts),'proposalCount':len(proposal_rows),'holdCount':counts['hold'],'perLocale':{loc:dict(per_locale[loc]) for loc in LOCALES},'callerPinsSupplied':len(caller_rows),'callerFiles':len({x['path'] for x in caller_rows}),'placeholderMismatchCells':sum(not x['placeholderParity'] for x in ledger),'markupMismatchCells':sum(not x['markupParity'] for x in ledger),'currentProtectedMismatchCells':sum(bool(x['currentProtectedMismatches']) for x in ledger),'finalProtectedMismatchCells':sum(bool(x['finalProtectedMismatches']) for x in ledger),'catalogsReattested':len(catalog_rows),'catalogKeyCount':len(keys),'boundarySourceIndices':[START-1,END+1],'boundaryRows':len(boundaries),'livePullRequest':pr2,'remoteBranchHead':remote2,'worktree':repo_state,'sourceNotes':['Confirmation gates are policy safeguards; literal door/gate translations are misleading. Consider simplifying the English key to “Confirmation required.”','The conflicts are record/metadata conflicts, not personal or armed conflicts.','Artist coverage occurs in Discography Concierge and refers to discography coverage; avoid news/broadcast senses.','“Native Soulseek” is technical/product wording; the Chinese 本机 targets mean local machine and are inaccurate.'],'nativeSpeakerApproval':False,'repositoryModified':False,'testsBuildsCiRun':False,'browserReview':False}
(OUT/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2,sort_keys=True)+'\n')
input_manifest={'schemaVersion':1,'inputDirectory':str(IN),'files':[],'exactHead':head_meta,'livePullRequest':pr,'remoteBranchHead':remote,'worktree':repo_state}
for p in sorted(IN.iterdir()):
 if p.is_file(): input_manifest['files'].append({'path':p.name,'bytes':p.stat().st_size,'sha256':input_hashes[p.name]})
(OUT/'input-reattestation.json').write_text(json.dumps(input_manifest,ensure_ascii=False,indent=2,sort_keys=True)+'\n')
README=f'''# slskR PR #204 primary semantic review — W823–W842

Reviewed 20 source keys × 12 locales (240 cells) at OPEN/DRAFT PR head `{HEAD}` / tree `{TREE}`. API, remote branch, exact-head worktree, all 12 catalogs, 240 target values, 51 supplied caller-context pins, and both source-window boundaries were reattested. The worktree is clean.

## Review results

- Dispositions: {dict(counts)}; {len(proposal_rows)} proposed target changes and {counts['hold']} holds.
- Placeholder and markup mismatches: 0 current/final.
- Protected product-name mismatches: current {summary['currentProtectedMismatchCells']}; proposed final 0. `Soulseek` is preserved exactly.
- Caller evidence: {len(caller_rows)} supplied pins across {summary['callerFiles']} files; every line and its surrounding context matches the exact head. Catalogs have 5,441 keys and identical ordered key sets.
- Boundary indices {START-1} and {END+1} are recorded across all locales.

The important caller-specific terminology findings are: “Confirmation gates required” refers to confirmation safeguards before media-server actions; the conflict labels refer to record/metadata conflicts; artist coverage is in the Discography Concierge panel; and “native Soulseek” is a product term, where Chinese 本机 incorrectly means local machine.

`primary-review-ledger.jsonl` has one exact-hash decision per locale cell, with caller pins, placeholder/markup checks, protected literals, rationale, and final target. `correction-candidates.jsonl` contains only proposed changes. Native-speaker review remains separate; confidence is machine-assisted and moderate. No repository or PR files were changed; no tests, builds, CI, or browser actions were run.
'''
(OUT/'README.md').write_text(README)
manifest={'schemaVersion':1,'repository':REPO,'pullRequest':PR,'head':HEAD,'tree':TREE,'window':'W823-W842','sourceCount':20,'cellCount':240,'candidateCount':len(proposal_rows),'counts':dict(counts),'sourceWindowSha256':summary['sourceWindowSha256'],'inputFiles':input_manifest['files'],'files':[]}
for p in sorted(OUT.iterdir()):
 if p.is_file() and p.name not in ('manifest.json','SHA256SUMS'):
  manifest['files'].append({'path':p.name,'bytes':p.stat().st_size,'sha256':sha(p.read_bytes())})
(OUT/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2,sort_keys=True)+'\n')
names=sorted(p.name for p in OUT.iterdir() if p.is_file() and p.name!='SHA256SUMS')
(OUT/'SHA256SUMS').write_text(''.join(f'{sha((OUT/name).read_bytes())}  {name}\n' for name in names))
print(json.dumps({'output':str(OUT),'head':HEAD,'tree':TREE,'counts':dict(counts),'proposals':len(proposal_rows),'holds':counts['hold'],'callerPins':len(caller_rows),'callerFiles':summary['callerFiles'],'boundaryRows':len(boundaries),'catalogs':len(catalog_rows),'placeholderMarkupMismatches':[summary['placeholderMismatchCells'],summary['markupMismatchCells']],'protectedLiteralMismatches':[summary['currentProtectedMismatchCells'],summary['finalProtectedMismatchCells']],'cleanWorktree':True},ensure_ascii=False,indent=2))
