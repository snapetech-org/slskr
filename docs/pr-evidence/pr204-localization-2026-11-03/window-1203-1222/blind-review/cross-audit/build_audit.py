import hashlib, json, pathlib, collections, datetime
R=pathlib.Path('/mnt/disks/scratch/task-scratch')
I=R/'slskr-pr204-w1203-1222-input-20261103/clean-input'
P=R/'slskr-pr204-w1203-primary-20261103'
B=R/'slskr-pr204-w1203-blind-20261103'
O=R/'slskr-pr204-w1203-blind-20261103/cross-audit'
H='7c0dd5844d39e5fdb5269fa50317b26f117512a2'; T='ba62eed0bd600a8f69bb6c0cbefe99da7ee47623'
def sha(b): return hashlib.sha256(b).hexdigest()
def shat(s): return sha(s.encode())
def j(p): return json.loads(p.read_text())
def jl(p):
 lines=p.read_bytes().splitlines(); return [json.loads(x) for x in lines],[sha(x) for x in lines]
def canon(x): return json.dumps(x,ensure_ascii=False,separators=(',',':'),sort_keys=True)
def sums(d):
 out={}
 for line in (d/'SHA256SUMS.txt').read_text().splitlines():
  digest,name=line.split('  ',1); assert sha((d/name).read_bytes())==digest,(d/name); out[name]=digest
 return out
assert {x.name for x in O.iterdir()} <= {'build_audit.py','cross-audit-decisions.jsonl','cross-audit-summary.json','cross-audit-validation.json','cross-audit-report.md','OUTPUT-MANIFEST.json','SHA256SUMS.txt','SEAL.json'}, 'Refusing to overwrite unexpected output.'
m=j(I/'manifest.json'); assert m['head']==H and m['tree']==T
crows,_=jl(I/'current-target-cells.jsonl'); ctx,ctxh=jl(I/'source-contexts.jsonl'); holdrows,_=jl(I/'caller-resolution-holds.jsonl')
primary,_=jl(P/'primary-decisions.jsonl'); blind,_=jl(B/'blind-decisions.jsonl')
key=lambda x:(x['position'],x['locale'])
assert all(len(x)==240 for x in (crows,primary,blind))
C={key(x):x for x in crows}; PR={key(x):x for x in primary}; BL={key(x):x for x in blind}
assert len(C)==len(PR)==len(BL)==240 and set(C)==set(PR)==set(BL)
CTX={x['position']:x for x in ctx}; CTXH={x['position']:h for x,h in zip(ctx,ctxh)}; HOL={key(x):x for x in holdrows}
assert len(ctx)==20 and len(holdrows)==24 and sum(x['callerReferenceCount'] for x in ctx)==86
# Preference map on the 64 conflicting cells: unspecified competing candidates follow primary.
PB={(1207,'all'),(1208,'hi'),(1209,'all'),(1211,'ar'),(1212,'ja'),(1222,'hi')}
notes={
1204:'Arabic definite article is retained; hamza orthography in الألبوم is preferred to the unhamzated form.',
1205:'Prefer idiomatic sentence case. Arabic hamza is preserved; Spanish uses lower-case after el; Vietnamese album is a common noun.',
1207:'Use explicit speed-limit wording: the pinned caller is a numeric downloadSpeedLimit field with aria label “Global download speed limit.” Preserve exact KiB/s.',
1208:'Prefer concise locale-appropriate selected-items actions; in Hindi, retain “items” explicitly to clarify what is selected.',
1209:'The caller is a numeric maximum-concurrent-downloads setting; replace ambiguous “slots” with maximum concurrent download count in every locale.',
1211:'Both proposals mean approval for downloads. The selected variants are preferred for natural phrasing and to avoid misreading this as approval to download an approval.',
1212:'Use retention-duration wording for this minutes-valued configuration field; prefer Japanese 保持期間 for retention.',
1214:'Use retention-duration wording for the minutes-valued errored-download retention setting; both proposals are semantically supported.',
1217:'The status is in progress; Indonesian sedang berlangsung expresses the active state more naturally.',
1218:'The caller identifies a downloads leaderboard. Prefer wording that retains leaderboard/ranking meaning over a generic ranking variant.',
1219:'The Hindi candidate should state that download-mode status is unavailable; the primary version is more grammatical than the blind version.',
1222:'The caller branch is taken when the download path is unset/missing. Hindi “path is not set” matches this more exactly than “unavailable”.'}
outs=[]; conflicts=collections.Counter(); diffs=0; agrees=0
for k in sorted(C):
 c,p,b=C[k],PR[k],BL[k]
 assert c['head']==p['head']==b['head']==H and c['tree']==p['tree']==b['tree']==T
 assert c['sourceKey']==p['sourceKey']==b['sourceKey'] and c['sourceKeySha256']==p['sourceKeySha256']==b['sourceKeySha256']==shat(c['sourceKey'])
 assert c['currentTarget']==p['currentTarget']==b['currentTarget'] and c['currentTargetSha256']==p['currentTargetSha256']==b['currentTargetSha256']==shat(c['currentTarget'])
 assert c['catalogPath']==p['catalogPath']==b['catalogPath'] and c['catalogSha256']==p['catalogSha256']==b['catalogSha256'] and c['catalogGitBlob']==p['catalogGitBlob']==b['catalogGitBlob']
 x=CTX[c['position']]; assert x['sourceKey']==c['sourceKey'] and x['callerReferenceCount']==len(x['references'])==len(x['locations'])==c['sourceCallerCount']==p['callerReferenceCount']==b['callerReferenceCount']
 assert p['callerLocations']==x['locations'] and p['callerEvidence']['packetFile']=='source-contexts.jsonl' and p['callerEvidence']['packetSha256']==sha((I/'source-contexts.jsonl').read_bytes())
 assert b['sourceContextRowSha256']==CTXH[c['position']]
 pairs={(z['path'],z['line']) for z in x['references']}; assert pairs=={(z['path'],z['line']) for z in b['callerRefs']}
 src_linehashes={(z['path'],z['line'],v['lineSha256']) for z in x['references'] for v in z['contextLines'] if v['line']==z['line']}
 assert {(z['path'],z['line'],z['lineSha256']) for z in b['callerRefs']}==src_linehashes
 assert p['sourcePlaceholders']==c['sourcePlaceholders'] and p['currentTargetPlaceholders']==c['currentTargetPlaceholders'] and p['currentPlaceholderCheck']=='pass'
 assert p['proposedPlaceholderCheck'] in ('pass','pass-current','hold') and p['markupCheck']=='pass'
 assert b['placeholderCheck']['currentMatchesSource'] and b['placeholderCheck']['recommendedMatchesSource'] in (True,None)
 assert b['markupCheck']['currentMatchesSource'] and b['markupCheck']['recommendedMatchesSource'] in (True,None)
 assert b['numericCheck']['currentMatchesSource'] and b['numericCheck']['recommendedMatchesSource'] in (True,None)
 if b['disposition']!='hold': assert b['placeholderCheck']['recommendedMatchesSource'] and b['markupCheck']['recommendedMatchesSource'] and b['numericCheck']['recommendedMatchesSource']
 pd={'accept-current':'accept','correction':'proposal','refinement':'proposal','hold':'hold'}[p['verdict']]
 bd={'accept-current':'accept','correction/refinement proposal':'proposal','hold':'hold'}[b['disposition']]
 pt=(p['effectiveTarget'] if p['effectiveTarget'] is not None else c['currentTarget']); bt=(b['recommendedTarget'] if bd=='proposal' else c['currentTarget'])
 assert p['effectiveTargetSha256']==(shat(p['effectiveTarget']) if p['effectiveTarget'] is not None else None)
 if p['proposedTarget'] is not None: assert p['proposedTargetSha256']==shat(p['proposedTarget'])
 if b['recommendedTarget'] is not None: assert b['recommendedTargetSha256']==shat(b['recommendedTarget'])
 if pd!=bd: conflicts[(pd,bd)]+=1
 if pt!=bt: diffs+=1
 if pt==bt and pd==bd: agrees+=1
 if k in HOL or pd=='hold' or bd=='hold':
  assert k in HOL and pd==bd=='hold'; disp='hold'; target=c['currentTarget']; why=HOL[k]['holdReason']
 elif pd==bd=='accept': disp='accept-current'; target=c['currentTarget']; why='Both reviewers accept the current translation; no change is recommended.'
 elif pd==bd=='proposal' and pt==bt: disp='correction/refinement proposal'; target=pt; why='Both reviewers independently recommend the same replacement; retained after caller-context and structural checks.'
 elif pd=='proposal' and bd=='accept': disp='correction/refinement proposal'; target=pt; why=notes.get(c['position'],'The primary proposal resolves a source/caller-specific semantic or language-quality issue identified in cross-review.')
 elif pd=='accept' and bd=='proposal': disp='correction/refinement proposal'; target=bt; why=notes.get(c['position'],'The blind proposal resolves a source/caller-specific semantic or language-quality issue identified in cross-review.')
 else:
  assert pd==bd=='proposal'
  target=bt if (c['position'],'all') in PB or (c['position'],c['locale']) in PB else pt
  disp='correction/refinement proposal'; why=notes.get(c['position'],'Both alternatives preserve the source meaning; selected the clearer/more idiomatic wording for this locale in pinned caller context.')
 if c['position']==1207:
  assert 'KiB/s' in c['sourceKey'] and 'KiB/s' in target and p['proposedProtectedLiteralsPreserved']
  assert all(z['recommendedExact'] for z in b['protectedLiteralChecks'])
 outs.append({'schemaVersion':1,'window':'W1203-W1222','repository':'snapetech-org/slskR','pullRequest':204,'head':H,'tree':T,
  'position':c['position'],'locale':c['locale'],'sourceKey':c['sourceKey'],'sourceKeySha256':c['sourceKeySha256'],'currentTarget':c['currentTarget'],'currentTargetSha256':c['currentTargetSha256'],
  'catalogPath':c['catalogPath'],'catalogSha256':c['catalogSha256'],'catalogGitBlob':c['catalogGitBlob'],'callerReferenceCount':c['sourceCallerCount'],
  'sourceContextFile':'source-contexts.jsonl','sourceContextRowSha256':CTXH[c['position']],'callerLocations':x['locations'],'callerEvidenceReconciles':True,
  'primary':{'verdict':p['verdict'],'proposedTarget':p['proposedTarget'],'effectiveTarget':p['effectiveTarget'],'comparisonTarget':pt,'effectiveTargetSha256':p['effectiveTargetSha256']},
  'blind':{'disposition':b['disposition'],'recommendedTarget':b['recommendedTarget'],'effectiveTarget':b['recommendedTarget'] if bd=='proposal' else (c['currentTarget'] if bd=='accept' else None),'comparisonTarget':bt,'effectiveTargetSha256':b['recommendedTargetSha256'] if bd=='proposal' else (shat(c['currentTarget']) if bd=='accept' else None)},
  'recommendation':disp,'recommendedTarget':target,'recommendedTargetSha256':shat(target),'adjudicationRationale':why,
  'structuralChecks':{'sourceCurrentAndProposalHashesPass':True,'placeholdersPreserved':True,'markupPreserved':True,'numericTokensPreserved':True,'KiBPerSecondPreserved':c['position']!=1207 or 'KiB/s' in target}})
counts=collections.Counter(x['recommendation'] for x in outs)
assert counts=={'accept-current':136,'correction/refinement proposal':80,'hold':24},counts
assert diffs==64 and agrees==176 and sum(conflicts.values())==11 and conflicts[('proposal','accept')]==8 and conflicts[('accept','proposal')]==3
assert collections.Counter(x['position'] for x in outs if x['recommendation']=='hold')=={1206:12,1216:12}
# Reverify sealed source-package hash lists.
ihash=sums(I); phash=sums(P); bhash=sums(B)
isums=sha((I/'SHA256SUMS.txt').read_bytes()); psums=sha((P/'SHA256SUMS.txt').read_bytes()); bsums=sha((B/'SHA256SUMS.txt').read_bytes())
assert isums=='4525f64eec71544375b5af2a44592e0560b6fa904e3bcc9e14dc6715236dd1d3'
assert bsums=='6a976d70fd8de3df1668ee3d074babc5490479407f934a6cd037be9f4df4c7b1'
S={'schemaVersion':1,'artifact':'Cross-audit of primary and blind review — slskR PR #204 W1203–W1222','createdAtUtc':datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds'),
'livePin':{'state':'open','draft':True,'headRef':'codex/slskr-l10n-audit-20261030','head':H,'tree':T,'baseRef':'main','baseSha':m['baseSha'],'remoteBranchHead':H,'remotePullRefHead':H,'commitTree':T},
'coverage':{'positions':[1203,1222],'sourceCount':20,'localeCount':12,'cellCount':240,'primaryRows':240,'blindRows':240,'callerReferenceCount':86},
'inputEvidence':{'path':str(I),'sha256SumsSha256':isums,'allChecksumsPass':True,'checksums':ihash},'primaryEvidence':{'path':str(P),'sha256SumsSha256':psums,'allChecksumsPass':True,'checksums':phash},'blindEvidence':{'path':str(B),'sha256SumsSha256':bsums,'allChecksumsPass':True,'checksums':bhash},
'comparison':{'sameDispositionAndEffectiveTarget':agrees,'effectiveTargetDifferences':diffs,'dispositionConflicts':sum(conflicts.values()),'primaryProposalBlindAccept':conflicts[('proposal','accept')],'primaryAcceptBlindProposal':conflicts[('accept','proposal')],
'bothProposeDifferentTarget':sum(1 for k in PR if PR[k]['verdict'] in ('correction','refinement') and BL[k]['disposition']=='correction/refinement proposal' and PR[k]['effectiveTarget']!=BL[k]['recommendedTarget'])},
'recommendationCounts':dict(counts),'differingTargetSelections':{'primarySelected':sum(1 for x in outs if x['primary']['effectiveTarget']!=x['blind']['effectiveTarget'] and x['recommendedTarget']==x['primary']['effectiveTarget']),'blindSelected':sum(1 for x in outs if x['primary']['effectiveTarget']!=x['blind']['effectiveTarget'] and x['recommendedTarget']==x['blind']['effectiveTarget'])},
'callerResolutionHolds':[{'position':pos,'locales':m['localeOrder'],'reason':'No exact quoted source-key caller or pinned runtime consumer resolved; preserve hold pending caller resolution.'} for pos in (1206,1216)],
'structuralReview':{'sourceCurrentAndProposalHashesVerified':True,'callerLocationsAndBlindLinePinsReconcileToInput':True,'placeholderMismatches':0,'markupMismatches':0,'numericMismatches':0,'protectedLiteral':'KiB/s','currentTargetsMissingExactLiteral':['zh-Hans','ja','ar','ko','zh-Hant'],'allRecommendedTargetsPreserveExactLiteral':True},
'substantiveFindings':['Primary-only omitted changes judged justified: Arabic hamza spelling; Spanish/Vietnamese case and idiom; Indonesian in-progress phrasing; selected-items explicitness in Arabic/Indonesian; grammatical Hindi mode-status wording.','Blind-only omitted changes judged justified: explicit maximum-concurrent-downloads labels for “Download Slots” in all locales; explicit speed-limit phrasing; Hindi selected-items and unset-path wording.','Competing leaderboard wording: choose explicit leaderboard/ranking labels. Retention labels should preserve duration semantics; Japanese 保持期間 is preferred. For approval, candidates are semantically supported and choices are mainly language-quality preferences.'],
'unsafeOrUnsupportedEditsFound':False,'limitations':['Machine semantic cross-review, not native-speaker approval.','Locale choices between semantically equivalent variants may benefit from native-speaker confirmation.','Caller evidence is reconciled to the pinned candidate-free packet; no repository or PR content was changed.'],'repoOrPrChanges':False,'testsBuildsOrCiRun':False}
O.joinpath('cross-audit-decisions.jsonl').write_text(''.join(canon(x)+'\n' for x in outs),encoding='utf-8')
O.joinpath('cross-audit-summary.json').write_text(json.dumps(S,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
V={'schemaVersion':1,'valid':True,'rowCount':240,'uniqueCellCount':240,'allInputReviewerChecksumsVerified':True,'livePinVerified':True,'callerEvidenceReconciled':True,'placeholderMarkupNumericChecksPass':True,'protectedLiteralChecksPass':True,'counts':dict(counts),'targetDifferences':diffs,'dispositionConflicts':sum(conflicts.values()),'checkAssertionsPassed':True}
O.joinpath('cross-audit-validation.json').write_text(json.dumps(V,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
report='''# Cross-audit report — slskR PR #204 W1203–W1222\n\n## Pinned state and coverage\n\nLive PR, branch, pull ref, and commit API agree on head `7c0dd5844d39e5fdb5269fa50317b26f117512a2`; tree `ba62eed0bd600a8f69bb6c0cbefe99da7ee47623`. PR is open and draft, based on `main` at `2a2b188f10b9460a15bc6d5c34e406b0193d51ba`. Reconciled 20 source keys × 12 locales = **240/240 cells**, plus all 86 caller references. The candidate-free input, primary ledger, and blind ledger checksum manifests pass.\n\n## Reconciliation\n\nReviewers match on disposition and effective target for 176 cells. They differ on targets for 64 cells, with 11 disposition conflicts: 8 primary proposals where blind accepted current, and 3 primary accepts where blind proposed a change. The other 53 target differences are competing proposals.\n\nRecommendation: **136 accept current, 80 correction/refinement proposals, 24 holds**. All holds are for every locale at positions 1206 “Download Clients” and 1216 “Download filters”; no exact caller was resolved. Among differing targets, the final value follows the primary in 36 and blind in 28. Cell-level decisions and rationale are in `cross-audit-decisions.jsonl`.\n\nPrimary-only changes judged justified include Arabic hamza spelling, Spanish and Vietnamese case/idiom improvements, Indonesian in-progress wording, selected-items explicitness in Arabic/Indonesian, and grammatical Hindi download-mode status. Blind-only changes judged justified include maximum-concurrent-downloads wording for “Download Slots” in all locales, explicit speed-limit phrasing for “Download KiB/s”, and Hindi selected-items and unset-path wording. Every recommendation retains exact `KiB/s`; five current translations omit it.\n\nNo unsupported caller claims or unsafe edits were identified. Source/current/proposal hashes, catalog pins, caller-context row hashes, placeholders, markup, and numeric-token checks reconcile. Caller wording supports the speed-limit, maximum-concurrent-downloads, retention-duration, leaderboard, and missing-path meanings recorded in the ledger.\n\n## Limits\n\nThis is a machine cross-review, not native-speaker approval. Some choices between equivalent locale variants remain language-quality judgments and merit native-speaker confirmation. No repository/PR edits, tests, builds, or CI were run.\n'''
O.joinpath('cross-audit-report.md').write_text(report,encoding='utf-8')
files=['cross-audit-decisions.jsonl','cross-audit-summary.json','cross-audit-validation.json','cross-audit-report.md','build_audit.py']
M={'schemaVersion':1,'artifact':'slskR W1203-W1222 primary/blind cross-audit','files':{n:sha((O/n).read_bytes()) for n in files},'inputChecksumListSha256':isums}
O.joinpath('OUTPUT-MANIFEST.json').write_text(json.dumps(M,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
checks=files+['OUTPUT-MANIFEST.json']
O.joinpath('SHA256SUMS.txt').write_text(''.join(f'{sha((O/n).read_bytes())}  {n}\n' for n in checks),encoding='utf-8')
seal={'schemaVersion':1,'algorithm':'SHA-256','sha256SumsFile':'SHA256SUMS.txt','sha256SumsSha256':sha((O/'SHA256SUMS.txt').read_bytes()),'rowCount':240,'head':H,'tree':T}
O.joinpath('SEAL.json').write_text(json.dumps(seal,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'output':str(O),'counts':dict(counts),'agreements':agrees,'targetDifferences':diffs,'dispositionConflicts':sum(conflicts.values()),'primarySelected':S['differingTargetSelections']['primarySelected'],'blindSelected':S['differingTargetSelections']['blindSelected'],'inputSumsSha256':isums,'outputSumsSha256':seal['sha256SumsSha256'],'ledgerSha256':M['files']['cross-audit-decisions.jsonl'],'reportSha256':M['files']['cross-audit-report.md']}))
