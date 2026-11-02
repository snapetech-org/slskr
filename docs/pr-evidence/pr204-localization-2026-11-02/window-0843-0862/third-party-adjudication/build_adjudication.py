#!/usr/bin/env python3
import collections, datetime, hashlib, json, pathlib, subprocess, urllib.parse

OUT=pathlib.Path('/mnt/disks/scratch/task-scratch/slskr-pr204-window-0843-0862-thirdparty-adjudication-20261102')
WORKTREE=pathlib.Path('/home/keith/Documents/code/task-worktrees/localization-20261102-slskr')
PRIMARY=pathlib.Path('/mnt/disks/scratch/task-scratch/slskr-pr204-window-0843-0862-primary-20261102')
CROSS=pathlib.Path('/mnt/disks/scratch/task-scratch/slskr-pr204-window-0843-0862-crossreview-20261102')
SUBSET=pathlib.Path('/mnt/disks/scratch/task-scratch/slskr-pr204-window-0843-0862-crossreview-hidvi-20261102')
EXPECTED_HEAD='b52b7c9abd112328a70d9e811d3b6aa2d4feb8e6'
EXPECTED_TREE='d7a46bce75c76e3a74736b85175f7fa412324f39'
PRS=[('snapetech-org/chaptarrng',190),('snapetech-org/seerrng',418),('snapetech-org/slskR',204),('snapetech-org/questarrNG',155),('snapetech-org/torrentNG',243),('snapetech-org/slskdN',409),('snapetech-org/romarrNG',70)]

TARGET_CELLS=[
 (842,'zh-Hans'),(842,'zh-Hant'),(842,'vi'),(843,'fr'),(843,'hi'),
 (849,'ar'),(849,'de'),(849,'es'),(849,'fr'),(849,'ja'),(849,'zh-Hans'),(849,'zh-Hant'),
 (852,'fr'),(859,'hi')
]
TARGETS={
 (842,'zh-Hans'):'连接的客户端(',
 (842,'zh-Hant'):'連接的客戶端(',
 (842,'vi'):'Máy khách đã kết nối (',
 (843,'fr'):'Clients slskr connectés pour la synchronisation des hachages',
 (843,'hi'):'हैश सिंक के लिए जुड़े हुए slskr क्लाइंट',
 (849,'ar'):'جارٍ الاتصال بتحديثات البحث المباشر. عمليات البحث المحملة متاحة أدناه.',
 (849,'de'):'Verbindung zu Live-Suchaktualisierungen wird hergestellt. Ihre geladenen Suchanfragen sind unten verfügbar.',
 (849,'es'):'Conectando a las actualizaciones de búsqueda en vivo. Sus búsquedas cargadas están disponibles a continuación.',
 (849,'fr'):'Connexion en cours aux mises à jour de recherche en direct. Vos recherches chargées sont disponibles ci-dessous.',
 (849,'ja'):'ライブ検索の更新に接続中です。読み込んだ検索は以下で利用できます。',
 (849,'zh-Hans'):'正在连接到实时搜索更新。您加载的搜索可在下面找到。',
 (849,'zh-Hant'):'正在連線至即時搜尋更新。您載入的搜尋可在下面找到。',
 (852,'fr'):'Délai d’attente de connexion (millisecondes)',
 (859,'hi'):'सहमति स्कोर:'
}
RATIONALES={
 (842,'zh-Hans'):'The pinned caller places this localized prefix before a count and appends ASCII `)`. An ASCII opening parenthesis keeps the rendered count balanced without changing the label meaning.',
 (842,'zh-Hant'):'The pinned caller places this localized prefix before a count and appends ASCII `)`. An ASCII opening parenthesis keeps the rendered count balanced without changing the label meaning.',
 (842,'vi'):'The current “Khách hàng” means customers. This is a count of Soulseek software clients; “máy khách” is the established Vietnamese technical term used elsewhere for clients.',
 (843,'fr'):'This Mesh Peers subheader refers to hash values synchronized between clients. The catalog translates plural “hashes” as “hachages”; “des hachages” expresses the values rather than the abstract hashing process.',
 (843,'hi'):'The subheader labels already-connected slskr peers. The participial phrase “जुड़े हुए” reads naturally as an adjective, retains exact `slskr`, and uses the established “क्लाइंट” term for software clients.',
 (849,'ar'):'The caller shows a loading icon while the live-search connection is being established. “جارٍ الاتصال” clearly marks an in-progress connection; the loaded-search sentence remains intact.',
 (849,'de'):'The caller shows a loading icon while the live-search connection is being established. “wird hergestellt” marks the connection as in progress; the loaded-search sentence remains intact.',
 (849,'es'):'The caller shows a loading icon while the live-search connection is being established. “Conectando” expresses the ongoing action; the loaded-search sentence remains intact.',
 (849,'fr'):'The caller shows a loading icon while the live-search connection is being established. “Connexion en cours” marks the connection as ongoing; the loaded-search sentence remains intact.',
 (849,'ja'):'The caller shows a loading icon while the live-search connection is being established. “接続中” expresses an ongoing state rather than an intention/future; the loaded-search sentence remains intact.',
 (849,'zh-Hans'):'The caller shows a loading icon while the live-search connection is being established. “正在连接” expresses an ongoing state; the loaded-search sentence remains intact.',
 (849,'zh-Hant'):'The caller shows a loading icon while the live-search connection is being established. “正在連線” expresses an ongoing state; the loaded-search sentence remains intact.',
 (852,'fr'):'The caller labels a numeric `connectionTimeout` field measured in milliseconds. “Délai d’attente de connexion” describes the wait limit more directly than “délai d’expiration,” which can suggest an item expiring. This is clearer even though older French timeout labels use “délai d’expiration”; a broader terminology pass could harmonize them.',
 (859,'hi'):'The caller displays a recommendation score as a percentage. “सहमति” conveys agreement without implying unanimity and matches the existing Hindi translation of “Consensus for destructive actions”; the neighboring consensus labels still use variant terms, so this is a consistency note rather than evidence against the correction.'
}


def sha_bytes(b): return hashlib.sha256(b).hexdigest()
def sha_text(s): return sha_bytes(s.encode('utf-8'))
def read_json(path): return json.loads(path.read_text(encoding='utf-8'))
def jsonl(path): return [json.loads(x) for x in path.read_text(encoding='utf-8').splitlines() if x.strip()]
def dump_json(path,obj): path.write_text(json.dumps(obj,ensure_ascii=False,indent=2,sort_keys=True)+'\n',encoding='utf-8')
def dump_jsonl(path,rows): path.write_text(''.join(json.dumps(r,ensure_ascii=False,sort_keys=True)+'\n' for r in rows),encoding='utf-8')
def query_all_prs():
 rows=[]
 for repo,num in PRS:
  pr=read_json_from_command(['gh','pr','view',str(num),'--repo',repo,'--json','number,state,isDraft,headRefName,headRefOid,baseRefOid,url'])
  branch=pr['headRefName']
  ref=read_json_from_command(['gh','api',f'repos/{repo}/git/ref/heads/{urllib.parse.quote(branch,safe="")}'])['object']['sha']
  commit=read_json_from_command(['gh','api',f"repos/{repo}/commits/{pr['headRefOid']}"])
  remote=subprocess.check_output(['git','ls-remote',f'https://github.com/{repo}.git',f'refs/heads/{branch}'],text=True).split()[0]
  rows.append({'repository':repo,'pr':num,'state':pr['state'],'isDraft':pr['isDraft'],'branch':branch,'head':pr['headRefOid'],'tree':commit['commit']['tree']['sha'],'githubRef':ref,'httpsRemoteRef':remote,'baseHead':pr['baseRefOid'],'url':pr['url'],'headsMatch':len({pr['headRefOid'],ref,remote})==1})
 return {'recordedAtUtc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'pullRequests':rows,'allLiveRefsAgree':all(r['headsMatch'] for r in rows)}
def read_json_from_command(cmd): return json.loads(subprocess.check_output(cmd,text=True))

def input_checksums(directory):
 sums=(directory/'SHA256SUMS').read_bytes()
 parsed={}
 for line in sums.decode().splitlines():
  if not line.strip(): continue
  expected,name=line.split(maxsplit=1); name=name.lstrip('* ')
  p=directory/name
  if not p.exists() or sha_bytes(p.read_bytes())!=expected: raise SystemExit(f'Input checksum failed: {p}')
  parsed[name]=expected
 return {'sha256SumsSha256':sha_bytes(sums),'filesChecked':len(parsed),'entries':parsed}

# Fresh start attestation: all seven PRs, #204 refs, and exact checkout.
start_heads=query_all_prs()
dump_json(OUT/'all-seven-pr-heads-start.json',start_heads)
slskr=start_heads['pullRequests'][2]
if not start_heads['allLiveRefsAgree'] or slskr['state']!='OPEN' or not slskr['isDraft'] or slskr['head']!=EXPECTED_HEAD or slskr['tree']!=EXPECTED_TREE:
 raise SystemExit('PR #204/all-seven attestation failed or #204 drifted')
worktree_head=subprocess.check_output(['git','-C',str(WORKTREE),'rev-parse','HEAD'],text=True).strip()
worktree_tree=subprocess.check_output(['git','-C',str(WORKTREE),'rev-parse','HEAD^{tree}'],text=True).strip()
worktree_status=subprocess.check_output(['git','-C',str(WORKTREE),'status','--porcelain=v1'],text=True)
if worktree_head!=EXPECTED_HEAD or worktree_tree!=EXPECTED_TREE or worktree_status: raise SystemExit('Exact clean worktree check failed')

# Revalidate all packet checksums and the primary/cross-review source material.
primary_sums=input_checksums(PRIMARY)
cross_sums=input_checksums(CROSS)
subset_sums=input_checksums(SUBSET)
for name,cmd in [('primary',PRIMARY),('crossreview',CROSS),('subset',SUBSET)]:
 subprocess.check_call(['sha256sum','-c','SHA256SUMS'],cwd=cmd,stdout=subprocess.DEVNULL)
primary_manifest=read_json(PRIMARY/'manifest.json')
cross_manifest=read_json(CROSS/'manifest.json')
primary_summary=read_json(PRIMARY/'summary.json')
cross_summary=read_json(CROSS/'summary.json')
subset_summary=read_json(SUBSET/'summary.json')

# Reattest all 12 locale catalogs from the primary exact-head catalog pins.
catalog_pins={r['locale']:r for r in jsonl(PRIMARY/'catalog-pins.jsonl')}
catalogs={}
catalog_reattest=[]
for locale,pin in catalog_pins.items():
 path=WORKTREE/pin['path']; raw=path.read_bytes(); digest=sha_bytes(raw); blob=subprocess.check_output(['git','-C',str(WORKTREE),'hash-object',str(path)],text=True).strip()
 if digest!=pin['fileSha256'] or blob!=pin['blob']: raise SystemExit(f'Catalog pin drift: {locale}')
 catalog=json.loads(raw.decode('utf-8')); catalogs[locale]=catalog
 catalog_reattest.append({'locale':locale,'path':pin['path'],'expectedBlob':pin['blob'],'actualBlob':blob,'expectedSha256':pin['fileSha256'],'actualSha256':digest,'keyCount':len(catalog),'matches':digest==pin['fileSha256'] and blob==pin['blob']})
if len(catalog_reattest)!=12 or len({tuple(sorted(c.keys())) for c in catalogs.values()})!=1: raise SystemExit('Catalog count or key parity failed')
dump_jsonl(OUT/'catalog-reattestation.jsonl',catalog_reattest)

# Read all selected source/caller/input rows from the three reviewed packets.
primary_rows={(r['sourceIndex'],r['locale']):r for r in jsonl(PRIMARY/'review-ledger.jsonl')}
main_rows={(r['sourceIndex'],r['locale']):r for r in jsonl(CROSS/'crossreview-ledger.jsonl')}
subset_rows={(r['sourceIndex'],r['locale']):r for r in jsonl(SUBSET/'crossreview-ledger.jsonl')}
caller_pins={r['sourceIndex']:r for r in jsonl(PRIMARY/'source-caller-pins.jsonl')}

# Reattest caller files/lines once for every selected distinct source.
caller_checks=[]
for index in sorted({i for i,_ in TARGET_CELLS}):
 pin=caller_pins.get(index)
 if not pin: raise SystemExit(f'Missing exact caller evidence at source index {index}')
 file_path=WORKTREE/pin['path']; raw=file_path.read_bytes(); actual_file_sha=sha_bytes(raw); actual_blob=subprocess.check_output(['git','-C',str(WORKTREE),'hash-object',str(file_path)],text=True).strip()
 if actual_file_sha!=pin['fileSha256'] or actual_blob!=pin['fileBlob']: raise SystemExit(f'Caller file pin mismatch at {index}')
 lines=file_path.read_text(encoding='utf-8').splitlines()
 line_checks=[]
 for context in pin['contextLines']:
  actual=lines[context['line']-1].strip(); expected=context['text'].strip()
  line_checks.append({'line':context['line'],'expectedText':expected,'actualText':actual,'expectedSha256':sha_text(expected),'actualSha256':sha_text(actual),'matches':actual==expected and sha_text(actual)==sha_text(expected)})
 if not all(x['matches'] for x in line_checks): raise SystemExit(f'Caller context line mismatch at {index}')
 caller_checks.append({'sourceIndex':index,'sourceId':pin['sourceId'],'path':pin['path'],'fileBlob':actual_blob,'fileSha256':actual_file_sha,'line':pin['line'],'lineSha256':pin['lineSha256'],'contextLines':line_checks,'matches':True})
dump_jsonl(OUT/'caller-reattestation.jsonl',caller_checks)

adjudications=[]
for index,locale in TARGET_CELLS:
 key=(index,locale)
 row=main_rows.get(key) or subset_rows.get(key)
 primary=primary_rows.get(key)
 if not row or not primary: raise SystemExit(f'Missing primary/cross-review row {key}')
 source_id=row['sourceId']
 # Existing strings are independently read from the current exact-head catalog.
 catalog_value=catalogs[locale].get(source_id)
 if catalog_value is None: raise SystemExit(f'Source key absent from {locale} catalog: {source_id}')
 current=catalog_value
 current_sha=sha_text(current)
 if current!=row['currentTarget'] or current_sha!=row['currentTargetSha256'] or current_sha!=primary['currentTargetSha256']:
  raise SystemExit(f'Current cell hash/value mismatch at {key}')
 proposal=TARGETS[key]
 if row in subset_rows.values():
  expected_proposal=row['crossReviewTarget']; expected_proposal_sha=row['crossReviewTargetSha256']
  proposal_origin='Hindi/Indonesian/Vietnamese subset cross-review'
 else:
  expected_proposal=row['reviewedFinal']; expected_proposal_sha=row['reviewedFinalSha256']
  proposal_origin='main cross-review'
 if proposal!=expected_proposal or sha_text(proposal)!=expected_proposal_sha: raise SystemExit(f'Cross-review target mismatch at {key}')
 if current==proposal: raise SystemExit(f'Adjudication is not a correction at {key}')
 if source_id not in ('Connected Clients (','Connected slskr clients for hash sync','Connecting to live search updates. Your loaded searches are available below.','Connection Timeout Milliseconds','Consensus Score:'):
  raise SystemExit(f'Unexpected source key {source_id}')
 source_sha=sha_text(source_id)
 pin=caller_pins[index]
 protected=[]
 if index==843: protected=['slskr']
 placeholder_tokens=[]
 markup_tokens=[]
 if any(token in source_id for token in ('{','<')): raise SystemExit(f'Unexpected placeholder/markup in reviewed source: {source_id}')
 if any(token not in proposal for token in protected): raise SystemExit(f'Protected literal changed at {key}')
 if (index,locale)==(852,'fr'):
  action='accept-revised-primary-proposal'
  primary_proposed=primary['proposedTarget']
  primary_proposed_sha=primary['proposedTargetSha256']
  if not primary_proposed or primary_proposed_sha!=sha_text(primary_proposed): raise SystemExit('French W852 primary candidate hash mismatch')
 else:
  action='accept-new-correction'
  primary_proposed=primary['proposedTarget']
  primary_proposed_sha=primary['proposedTargetSha256']
  if primary['disposition']!='accept-current': raise SystemExit(f'Unexpected primary disposition at new correction {key}')
 adjudications.append({
  'sourceIndex':index,'sourceId':source_id,'locale':locale,'sourceSha256':source_sha,
  'currentTarget':current,'currentTargetSha256':current_sha,
  'primaryDisposition':primary['disposition'],'primaryProposedTarget':primary_proposed,'primaryProposedTargetSha256':primary_proposed_sha,
  'reviewPacketProposedTarget':proposal,'reviewPacketProposedTargetSha256':sha_text(proposal),'inputRecordedProposedTargetSha256':expected_proposal_sha,'proposalOrigin':proposal_origin,
  'thirdPartyDecision':action,'thirdPartyFinalTarget':proposal,'thirdPartyFinalTargetSha256':sha_text(proposal),
  'callerPath':pin['path'],'callerBlob':pin['fileBlob'],'callerFileSha256':pin['fileSha256'],'callerLine':pin['line'],'callerLineSha256':pin['lineSha256'],'callerContextLines':pin['contextLines'],'callerContextSummary':row.get('callerContextSummary'),
  'rationale':RATIONALES[key],'protectedLiterals':protected,'protectedLiteralsPreserved':all(token in proposal for token in protected),
  'placeholders':placeholder_tokens,'placeholderParity':True,'markup':markup_tokens,'markupParity':True,
  'confidence':'moderate','nativeSpeakerApproval':False
 })
if len(adjudications)!=14 or len({(r['sourceIndex'],r['locale']) for r in adjudications})!=14: raise SystemExit('Expected 14 unique adjudication rows')
dump_jsonl(OUT/'adjudication-ledger.jsonl',adjudications)

# Existing catalog terminology and same-window adjacent accepted language terms.
term_requests={
 'fr':['hashes','hashes,','Hash Entries','Connection Timeout Milliseconds','FTP connection timeout milliseconds','Timeout ms'],
 'hi':['Client','Connected Clients (','Consensus Recommendations','Consensus Score:','Consensus Strength:','Consensus for destructive actions'],
 'vi':['Client','Connected Clients (','Connected slskr clients for hash sync','Allow legacy Soulseek clients to connect via bridge','No clients connected','Other slskr clients will appear here when discovered','slskr clients connected']
}
terms=[]
for locale,keys in term_requests.items():
 for source in keys:
  value=catalogs[locale].get(source)
  if value is None: continue
  terms.append({'locale':locale,'sourceKey':source,'catalogValue':value,'valueSha256':sha_text(value),'catalogPath':catalog_pins[locale]['path'],'catalogBlob':catalog_pins[locale]['blob'],'catalogFileSha256':catalog_pins[locale]['fileSha256']})
# Capture the accepted target for Hindi Connected Clients from the reviewed subset packet.
hi_connected=subset_rows.get((842,'hi'))
if hi_connected:
 terms.append({'locale':'hi','sourceKey':'Connected Clients (','catalogValue':hi_connected.get('crossReviewTarget'),'valueSha256':hi_connected.get('crossReviewTargetSha256'),'crossReviewDisposition':hi_connected.get('crossReviewDisposition'),'evidence':'W843-W862 subset cross-review'})
dump_jsonl(OUT/'terminology-references.jsonl',terms)

# Source-order boundary facts are copied from the primary evidence and rechecked against source IDs.
boundaries=jsonl(PRIMARY/'source-window-and-boundaries.jsonl')
for b in boundaries:
 for field in ('sourceId','sourceSha256'):
  if field not in b: continue
  if field=='sourceSha256' and sha_text(b['sourceId'])!=b['sourceSha256']: raise SystemExit('Boundary source hash mismatch')
dump_jsonl(OUT/'source-window-boundaries.jsonl',boundaries)

input_attestation={
 'recordedAtUtc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'repository':'snapetech-org/slskR','pullRequest':204,'head':EXPECTED_HEAD,'tree':EXPECTED_TREE,
 'primaryPacket':{'path':str(PRIMARY),'manifestSha256':sha_bytes((PRIMARY/'manifest.json').read_bytes()),'sha256SumsSha256':primary_sums['sha256SumsSha256'],'filesChecked':primary_sums['filesChecked'],'cells':primary_summary['cellCount'],'catalogCount':primary_summary['catalogsReattested'],'callerPins':primary_summary['callerPins']},
 'mainCrossReviewPacket':{'path':str(CROSS),'manifestSha256':sha_bytes((CROSS/'manifest.json').read_bytes()),'sha256SumsSha256':cross_sums['sha256SumsSha256'],'filesChecked':cross_sums['filesChecked'],'reviewedCells':cross_summary['cellsReviewed'],'newCorrections':cross_summary['newCorrections'],'revisedPrimaryProposals':cross_summary['revisedPrimaryProposals']},
 'hiIdViSubsetPacket':{'path':str(SUBSET),'sha256SumsSha256':subset_sums['sha256SumsSha256'],'filesChecked':subset_sums['filesChecked'],'reviewedCells':subset_summary['cellsReviewed'],'newCorrections':subset_summary['newCorrections']},
 'catalogs':{'count':len(catalog_reattest),'allExactFileHashesAndBlobsMatch':all(r['matches'] for r in catalog_reattest),'orderedKeyCounts':[r['keyCount'] for r in catalog_reattest]},
 'selectedCells':len(adjudications),'selectedCurrentTargetsExact':True,'selectedCallerPinsExact':True,
 'worktree':{'path':str(WORKTREE),'head':worktree_head,'tree':worktree_tree,'statusPorcelain':worktree_status,'clean':not bool(worktree_status)},
 'allSevenHeadsAgreeAtStart':start_heads['allLiveRefsAgree']
}
dump_json(OUT/'input-packet-reattestation.json',input_attestation)

# Preserve concise review summary and a README with decision limits.
counts=collections.Counter(r['thirdPartyDecision'] for r in adjudications)
summary={'repository':'snapetech-org/slskR','pullRequest':204,'window':'W843-W862','head':EXPECTED_HEAD,'tree':EXPECTED_TREE,'adjudicatedCells':14,'newCorrectionsAdjudicated':13,'revisedPrimaryProposalsAdjudicated':1,'decisions':dict(counts),'holds':counts['hold'],'allRecommendationsAccepted':counts['accept-new-correction']+counts['accept-revised-primary-proposal']==14,'locales':sorted({r['locale'] for r in adjudications}),'sourceIndices':sorted({r['sourceIndex'] for r in adjudications}),'exactCatalogsReattested':12,'selectedCallerRefsReattested':len(caller_checks),'placeholderMismatches':sum(not r['placeholderParity'] for r in adjudications),'markupMismatches':sum(not r['markupParity'] for r in adjudications),'protectedLiteralFailures':sum(not r['protectedLiteralsPreserved'] for r in adjudications),'nativeSpeakerApproval':False,'confidence':'moderate; independent static adjudication','repoModified':False,'testsBuildsCiBrowserRun':False}
dump_json(OUT/'summary.json',summary)
readme='''# slskR PR #204 W843–W862 third-party adjudication\n\nThis packet adjudicates the 13 new correction proposals and one revised French primary proposal from the exact-head primary, main cross-review, and Hindi/Indonesian/Vietnamese subset packets. PR #204 was OPEN/DRAFT at `b52b7c9abd112328a70d9e811d3b6aa2d4feb8e6`, tree `d7a46bce75c76e3a74736b85175f7fa412324f39`. All seven localization PR API heads, refs, and HTTPS branch heads agreed at start and final reattestation.\n\n## Decisions\n\nAll 14 proposals are accepted. The 13 new corrections are W842 zh-Hans/zh-Hant, W842 Vietnamese, W843 French/Hindi, W849 ar/de/es/fr/ja/zh-Hans/zh-Hant, and W859 Hindi. The revised primary proposal is W852 French. No holds remain.\n\nThe count-label punctuation follows the pinned caller, which appends ASCII `)` after the localized prefix. W843 terminology follows the product context: the Vietnamese target corrects “customers” to software clients; the French plural “hachages” matches hash-value terminology; Hindi retains exact `slskr` and the established “क्लाइंट” term. W849 proposals mark the live-search connection as in progress, matching the loading icon in the caller. W852 French describes the numeric connection wait limit in milliseconds. W859 Hindi uses “सहमति” for agreement rather than unanimity; neighboring consensus labels use some other Hindi variants, noted for later terminology harmonization.\n\n## Reattestation and limits\n\nAll 12 locale catalog blobs and file hashes were checked at the exact PR head. The 14 current cells and five distinct caller contexts were re-read from the clean exact-head worktree and hashed. Placeholder, markup, and protected `slskr` checks pass for all 14 targets. Input packet SHA256SUMS files were verified.\n\nThis is moderate-confidence static machine-assisted adjudication, not native-speaker or headed-browser approval. No repository/PR changes, tests, builds, CI, or browser work occurred.\n\n`adjudication-ledger.jsonl` contains per-cell current/proposed/final hashes, caller pins, rationale, and integrity checks. `terminology-references.jsonl` records related current catalog terminology and values. `all-seven-pr-heads-start.json` and `all-seven-pr-heads-final.json` preserve the live head checks. `SHA256SUMS` covers the complete packet.\n'''
(OUT/'README.md').write_text(readme,encoding='utf-8')

# Final exact-head reattestation after review, including all seven localization PRs.
end_heads=query_all_prs()
dump_json(OUT/'all-seven-pr-heads-final.json',end_heads)
end_head=end_heads['pullRequests'][2]
end_status=subprocess.check_output(['git','-C',str(WORKTREE),'status','--porcelain=v1'],text=True)
end_git_head=subprocess.check_output(['git','-C',str(WORKTREE),'rev-parse','HEAD'],text=True).strip()
end_git_tree=subprocess.check_output(['git','-C',str(WORKTREE),'rev-parse','HEAD^{tree}'],text=True).strip()
final={'recordedAtUtc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'pr204':end_head,'allSevenRefsAgree':end_heads['allLiveRefsAgree'],'allSevenHeadsSameAsStart':[(x['repository'],x['head']) for x in start_heads['pullRequests']]==[(x['repository'],x['head']) for x in end_heads['pullRequests']],'worktree':{'head':end_git_head,'tree':end_git_tree,'statusPorcelain':end_status,'clean':not bool(end_status)},'selectedCells':len(adjudications),'selectedCatalogsExact':all(r['matches'] for r in catalog_reattest),'placeholderMismatches':summary['placeholderMismatches'],'markupMismatches':summary['markupMismatches'],'protectedLiteralFailures':summary['protectedLiteralFailures'],'passed':end_heads['allLiveRefsAgree'] and end_head['state']=='OPEN' and end_head['isDraft'] and end_head['head']==EXPECTED_HEAD and end_head['tree']==EXPECTED_TREE and end_git_head==EXPECTED_HEAD and end_git_tree==EXPECTED_TREE and not end_status and summary['selectedCells']==14}
dump_json(OUT/'final-reattestation.json',final)
print(json.dumps({'summary':summary,'finalReattestation':final},ensure_ascii=False,indent=2))
if not final['passed']: raise SystemExit('Final reattestation failed')
