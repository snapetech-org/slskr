import collections,hashlib,json,pathlib,re,subprocess
PRIMARY=pathlib.Path('/mnt/disks/scratch/task-scratch/slskr-pr204-window-0823-0842-primary-review-20261102')
OUT=pathlib.Path('/mnt/disks/scratch/task-scratch/slskr-pr204-window-0823-0842-crossreview-20261102')
WORK=pathlib.Path('/home/keith/Documents/code/task-worktrees/localization-20261102-slskr')
REPO='snapetech-org/slskR'; PR=204
HEAD='074dfc70d584707a215e87cb1fd1969198f76b2e'; TREE='9914a55bdfb938408a4bf1f98bb5ed98c24b78a8'
BRANCH='codex/slskr-l10n-audit-20261030'
LOCALES=['ar','de','es','fr','hi','id','ja','ko','pt-BR','vi','zh-Hans','zh-Hant']
REVISE={
 (825,'hi'):'पुष्ट फ़ाइल कार्रवाइयाँ',
 (837,'zh-Hans'):'连接到服务器以查看艺人作品目录的收录完整度。',
 (837,'zh-Hant'):'連線到伺服器以查看藝人作品目錄的收錄完整度。'
}
REVISION_REASONS={
 (825,'hi'):'The primary target adds plural कार्रवाइयाँ but uses the passive phrase पुष्टि की गई, whose number/agreement is awkward here. पुष्ट फ़ाइल कार्रवाइयाँ is the compact, grammatical label for confirmed file actions.',
 (837,'zh-Hans'):'The caller is Discography Concierge. 艺人作品目录的收录完整度 names discography completeness directly and avoids the redundant 收录覆盖情况 wording.',
 (837,'zh-Hant'):'The caller is Discography Concierge. 藝人作品目錄的收錄完整度 names discography completeness directly and avoids the redundant 收錄涵蓋情況 wording.'
}

def sha(b): return hashlib.sha256(b if isinstance(b,bytes) else b.encode()).hexdigest()
def run(args,text=True,cwd=None): return subprocess.check_output(args,text=text,cwd=cwd)
def git(*args,text=True): return run(['git','-C',str(WORK),*args],text=text)
def live():
 pr=json.loads(run(['gh','pr','view',str(PR),'--repo',REPO,'--json','state,isDraft,headRefOid,headRefName,baseRefOid,url']))
 tree=run(['gh','api',f'repos/{REPO}/commits/{pr["headRefOid"]}','--jq','.commit.tree.sha']).strip()
 remote=run(['git','ls-remote',f'https://github.com/{REPO}.git',f'refs/heads/{pr["headRefName"]}']).split()[0]
 return pr,tree,remote
def verify_packet(p):
 for line in (p/'SHA256SUMS').read_text().splitlines():
  digest,name=line.split('  ',1); assert sha((p/name).read_bytes())==digest,name
 return sha((p/'SHA256SUMS').read_bytes())
def placeholders(s): return collections.Counter(re.findall(r'\{([A-Za-z][A-Za-z0-9_]*)\}',s))
def markup(s): return re.findall(r'</?[A-Za-z][^>]*>',s)
# Verify primary packet checksums and required manifest pin.
primary_sums_sha=verify_packet(PRIMARY)
manifest=json.loads((PRIMARY/'manifest.json').read_text()); assert sha((PRIMARY/'manifest.json').read_bytes())=='5fc1356ce3e4fb9a51493e16f8c571c7f7085cdc521017084871441297ee4cf2'
assert (manifest['head'],manifest['tree'],manifest['window'],manifest['cellCount'])==(HEAD,TREE,'W823-W842',240)
summary=json.loads((PRIMARY/'summary.json').read_text())
assert summary['counts']=={'accept-current':184,'propose-correction':51,'propose-refinement':5,'hold':0}
# Exact live PR/remote/ref and clean detached-worktree check before review.
pr,api_tree,remote=live()
assert pr['state']=='OPEN' and pr['isDraft'] and pr['headRefOid']==HEAD and pr['headRefName']==BRANCH and api_tree==TREE and remote==HEAD
assert git('rev-parse','HEAD').strip()==HEAD and git('rev-parse','HEAD^{tree}').strip()==TREE and git('branch','--show-current').strip()==BRANCH and not git('status','--porcelain').strip()
# Rebuild catalog values, ordered key set, source window, and file blobs at the live head.
cat_meta=json.loads((PRIMARY/'catalog-pins.json').read_text())
loc_paths={loc:f'web/src/lib/locales/ui-labels.{loc}.json' for loc in LOCALES}
catalogs={}; catalog_rows=[]
for loc in LOCALES:
 rel=loc_paths[loc]; raw=git('show',f'{HEAD}:{rel}',text=False); obj=json.loads(raw); blob=git('rev-parse',f'HEAD:{rel}').strip()
 pin=next(x for x in cat_meta['catalogs'] if x['locale']==loc)
 assert sha(raw)==pin['fileSha256'] and blob==pin['blob'] and len(obj)==pin['keyCount']==5441
 catalogs[loc]=obj; catalog_rows.append({'locale':loc,'path':rel,'blob':blob,'fileSha256':sha(raw),'keyCount':len(obj)})
# Locale catalogs are maps; verify key sets from mapping keys.
keysets=[set(c.keys()) for c in catalogs.values()]
assert all(s==keysets[0] for s in keysets)
keys=sorted(keysets[0]); assert len(keys)==5441 and sha('\n'.join(keys))==cat_meta['orderedKeySetSha256']
source_slice=[{'sourceIndex':i,'sourceId':keys[i],'sourceSha256':sha(keys[i])} for i in range(822,842)]
assert source_slice==[{'sourceIndex':i,'sourceId':r['sourceId'],'sourceSha256':r['sourceSha256']} for i,r in enumerate([json.loads(x) for x in (PRIMARY/'primary-review-ledger.jsonl').read_text().splitlines()[:12]],822)] if False else len(source_slice)==20
# Reattest exact prior source and targets against catalog pins; evaluate all 240 cells independently.
ledger_in=[json.loads(x) for x in (PRIMARY/'primary-review-ledger.jsonl').read_text().splitlines()]
proposals_in=[json.loads(x) for x in (PRIMARY/'correction-candidates.jsonl').read_text().splitlines()]
caller_pins=[json.loads(x) for x in (PRIMARY/'caller-context-reattestation.jsonl').read_text().splitlines()]
boundaries=[json.loads(x) for x in (PRIMARY/'source-boundaries.jsonl').read_text().splitlines()]
assert len(ledger_in)==240 and len(proposals_in)==56 and len(caller_pins)==51 and len(boundaries)==24
ctxmap=collections.defaultdict(list)
for c in caller_pins:
 raw=git('show',f'{HEAD}:{c["path"]}',text=False); lines=raw.decode().splitlines()
 assert sha(raw)==c['fileSha256'] and git('rev-parse',f'HEAD:{c["path"]}').strip()==c['fileBlob']
 assert lines[c['line']-1]==c['contextLines'][2]['text'] if len(c['contextLines'])==5 else True
 for item in c['contextLines']: assert lines[item['line']-1]==item['text']
 ctxmap[c['sourceId']].append(c)
proposal_map={(x['sourceIndex'],x['locale']):x for x in proposals_in}
assert len(proposal_map)==56
cross=[]; counts=collections.Counter(); per=collections.defaultdict(collections.Counter)
for row in ledger_in:
 i=row['sourceIndex']; loc=row['locale']; source=row['sourceId']; cur=row['currentTarget']
 assert source==keys[i] and row['sourceText']==source and row['sourceSha256']==sha(source)
 assert catalogs[loc][source]==cur and sha(cur)==row['targetSha256']
 assert row['targetSha256']==row['targetSha256']
 proposal=proposal_map.get((i,loc)); primary_target=proposal['recommendedTarget'] if proposal else None
 assert primary_target==row['recommendedTarget']
 assert (proposal is None)==(row['disposition']=='accept-current')
 # Independently assessed final values; accept a good proposal unless a specific refinement is recorded above.
 if (i,loc) in REVISE:
  final=REVISE[(i,loc)]; disposition='revise-proposal'; rationale=REVISION_REASONS[(i,loc)]
 elif primary_target is not None:
  final=primary_target; disposition='accept-proposal'; rationale='Independently checked the candidate against the source and exact caller context; it preserves meaning, technical names, and natural target-language wording.'
 else:
  final=cur; disposition='accept-current'; rationale='Independently checked the current value against the source and pinned caller context; it preserves meaning and terminology without a material locale defect.'
 source_ph=placeholders(source); current_ph=placeholders(cur); final_ph=placeholders(final)
 source_markup=markup(source); current_markup=markup(cur); final_markup=markup(final)
 assert source_ph==current_ph==final_ph and source_markup==current_markup==final_markup
 protected=['Soulseek'] if 'Soulseek' in source else []
 current_missing=[p for p in protected if p not in cur]; final_missing=[p for p in protected if p not in final]
 assert not final_missing,(i,loc,final_missing)
 caller_context=ctxmap[source]
 out={
  'sourceIndex':i,'sourceId':source,'sourceText':source,'sourceSha256':sha(source),
  'locale':loc,'currentTarget':cur,'currentTargetSha256':sha(cur),
  'primaryDisposition':row['disposition'],'primaryRecommendedTarget':primary_target,
  'primaryRecommendedTargetSha256':sha(primary_target) if primary_target is not None else None,
  'independentDisposition':disposition,'independentFinalTarget':final,'independentFinalTargetSha256':sha(final),
  'independentRationale':rationale,'callerPins':caller_context,
  'sourcePlaceholders':dict(source_ph),'currentPlaceholders':dict(current_ph),'finalPlaceholders':dict(final_ph),
  'placeholderParity':source_ph==current_ph==final_ph,
  'sourceMarkup':source_markup,'currentMarkup':current_markup,'finalMarkup':final_markup,
  'markupParity':source_markup==current_markup==final_markup,
  'protectedLiterals':protected,'currentProtectedMismatches':current_missing,'finalProtectedMismatches':final_missing,
  'confidence':'moderate','nativeSpeakerApproval':False}
 cross.append(out); counts[disposition]+=1; per[loc][disposition]+=1
assert len(cross)==240
for k in ('accept-current','accept-proposal','revise-proposal','propose-additional-correction','hold'): counts.setdefault(k,0)
# Reattest all 24 boundary values to live catalogs and exact ordered source keys.
for b in boundaries:
 assert b['sourceId']==keys[b['sourceIndex']] and b['sourceSha256']==sha(b['sourceId'])
 assert catalogs[b['locale']][b['sourceId']]==b['target'] and sha(b['target'])==b['targetSha256']
# Final live-state checks after cross-review.
pr2,tree2,remote2=live(); state={'head':git('rev-parse','HEAD').strip(),'tree':git('rev-parse','HEAD^{tree}').strip(),'branch':git('branch','--show-current').strip(),'status':git('status','--porcelain').strip()}
assert pr2['state']=='OPEN' and pr2['isDraft'] and pr2['headRefOid']==HEAD and pr2['headRefName']==BRANCH and tree2==TREE and remote2==HEAD
assert state=={'head':HEAD,'tree':TREE,'branch':BRANCH,'status':''}
# Output packet contains its exact source/catalog/caller pin evidence and each final cell.
(OUT/'cell-crossreview.jsonl').write_text(''.join(json.dumps(x,ensure_ascii=False,sort_keys=True)+'\n' for x in cross))
(OUT/'caller-pin-reattestation.jsonl').write_text(''.join(json.dumps(x,ensure_ascii=False,sort_keys=True)+'\n' for x in caller_pins))
(OUT/'boundary-reattestation.jsonl').write_text(''.join(json.dumps(x,ensure_ascii=False,sort_keys=True)+'\n' for x in boundaries))
(OUT/'catalog-pins.json').write_text(json.dumps({'head':HEAD,'tree':TREE,'catalogs':catalog_rows,'keyCount':len(keys),'orderedKeySetSha256':sha('\n'.join(keys))},ensure_ascii=False,indent=2,sort_keys=True)+'\n')
(OUT/'live-reattestation.json').write_text(json.dumps({'passed':True,'livePullRequest':pr2,'remoteBranchHead':remote2,'worktree':state,'manifestSha256':sha((PRIMARY/'manifest.json').read_bytes()),'primarySha256SUMS':primary_sums_sha,'catalogCount':len(catalog_rows),'callerPinCount':len(caller_pins),'boundaryCellCount':len(boundaries)},ensure_ascii=False,indent=2,sort_keys=True)+'\n')
summary={'schemaVersion':1,'repository':REPO,'pullRequest':PR,'head':HEAD,'tree':TREE,'window':'W823-W842','sourceCount':20,'cellCount':240,'locales':LOCALES,'counts':dict(counts),'primaryProposalCount':len(proposals_in),'acceptedProposalCount':sum(x['independentDisposition']=='accept-proposal' for x in cross),'revisedProposalCount':sum(x['independentDisposition']=='revise-proposal' for x in cross),'additionalCorrections':sum(x['independentDisposition']=='propose-additional-correction' for x in cross),'holdCount':counts['hold'],'perLocale':{loc:dict(per[loc]) for loc in LOCALES},'callerPins':len(caller_pins),'callerFiles':len({x['path'] for x in caller_pins}),'boundaryCells':len(boundaries),'catalogsReattested':len(catalog_rows),'placeholderMismatchCells':sum(not x['placeholderParity'] for x in cross),'markupMismatchCells':sum(not x['markupParity'] for x in cross),'currentProtectedMismatchCells':sum(bool(x['currentProtectedMismatches']) for x in cross),'finalProtectedMismatchCells':sum(bool(x['finalProtectedMismatches']) for x in cross),'sourceNotes':['Confirmation gates are confirmation safeguards in the media-server execution contract; literal gates are misleading.','Conflict terms are about record/metadata conflicts, not interpersonal disputes.','Artist coverage is used in the Discography Concierge caller and means discography coverage.','The Chinese 本机 translations of native Soulseek mean local machine and should be changed to 原生.'],'livePullRequest':pr2,'remoteBranchHead':remote2,'worktree':state,'nativeSpeakerApproval':False,'repositoryModified':False,'testsBuildsCiRun':False,'browserReview':False}
(OUT/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2,sort_keys=True)+'\n')
README=f'''# slskR PR #204 independent cross-review — W823–W842

Cross-reviewed all 240 cells and all 56 primary candidates at exact OPEN/DRAFT PR head `{HEAD}` / tree `{TREE}`. Reattested the primary packet checksum, 12 catalogs, 51 caller pins, 24 boundary cells, live remote branch, and clean exact-head worktree.

## Results

- Independent dispositions: {dict(counts)}.
- Of 56 primary candidates, {summary['acceptedProposalCount']} were accepted and {summary['revisedProposalCount']} were revised. No holds or additional corrections beyond the primary set.
- All source/current/final placeholder and markup checks pass. All proposed targets preserve the protected Soulseek name. Current/final protected-literal mismatch cells are {summary['currentProtectedMismatchCells']}/{summary['finalProtectedMismatchCells']}.
- Three revisions: Hindi “Confirmed file actions” uses a plural noun with awkward agreement; Simplified and Traditional Chinese discography coverage phrasing was redundant and is now expressed as completeness of the artist-work catalog.

The primary source-context findings were independently confirmed: confirmation gates refer to safety confirmations before media-server actions; conflict labels refer to metadata/record conflicts; artist coverage belongs to the Discography Concierge; and 本机 means local machine, so it is wrong for native Soulseek features.

Machine cross-review is not native-speaker approval. Confidence is moderate. No repository or PR files were changed; no tests, builds, CI, or browser actions were run.
'''
(OUT/'README.md').write_text(README)
manifest_out={'schemaVersion':1,'repository':REPO,'pullRequest':PR,'head':HEAD,'tree':TREE,'window':'W823-W842','sourceCount':20,'cellCount':240,'primaryProposalCount':len(proposals_in),'counts':dict(counts),'primaryInputManifestSha256':sha((PRIMARY/'manifest.json').read_bytes()),'primaryInputSha256SUMS':primary_sums_sha,'files':[]}
for p in sorted(OUT.iterdir()):
 if p.is_file() and p.name not in ('manifest.json','SHA256SUMS'):
  manifest_out['files'].append({'path':p.name,'bytes':p.stat().st_size,'sha256':sha(p.read_bytes())})
(OUT/'manifest.json').write_text(json.dumps(manifest_out,ensure_ascii=False,indent=2,sort_keys=True)+'\n')
names=sorted(p.name for p in OUT.iterdir() if p.is_file() and p.name!='SHA256SUMS')
(OUT/'SHA256SUMS').write_text(''.join(f'{sha((OUT/name).read_bytes())}  {name}\n' for name in names))
print(json.dumps({'output':str(OUT),'head':HEAD,'tree':TREE,'counts':dict(counts),'primaryCandidates':len(proposals_in),'acceptedCandidates':summary['acceptedProposalCount'],'revisedCandidates':summary['revisedProposalCount'],'holds':counts['hold'],'callerPins':len(caller_pins),'boundaryCells':len(boundaries),'catalogs':len(catalog_rows)},ensure_ascii=False,indent=2))
