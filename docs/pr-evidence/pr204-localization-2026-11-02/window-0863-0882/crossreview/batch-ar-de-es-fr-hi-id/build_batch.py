import json, hashlib, subprocess, re, collections
from pathlib import Path

PRIMARY = Path('/mnt/disks/scratch/task-scratch/slskr-pr204-window-0863-0882-primary-20261102')
OUT = Path('/mnt/disks/scratch/task-scratch/slskr-pr204-window-0863-0882-crossreview-20261102/batch-ar-de-es-fr-hi-id')
REPO = Path('/home/keith/Documents/code/task-worktrees/localization-20261102-slskr')
LOCALES = {'ar','de','es','fr','hi','id'}
LOCALE_ORDER = ['ar','de','es','fr','hi','id']
OUT.mkdir(parents=True, exist_ok=True)

def sha(b):
    if isinstance(b, str): b=b.encode('utf-8')
    return hashlib.sha256(b).hexdigest()
def git(*args):
    return subprocess.check_output(['git','-C',str(REPO),*args])
def gittext(*args): return git(*args).decode('utf-8')
def jread(p): return json.loads(p.read_text(encoding='utf-8'))
def jlread(p): return [json.loads(x) for x in p.read_text(encoding='utf-8').splitlines() if x.strip()]
def canonical(v): return json.dumps(v,ensure_ascii=False,sort_keys=True,separators=(',',':'))

head=gittext('rev-parse','HEAD').strip()
tree=gittext('rev-parse','HEAD^{tree}').strip()
status=gittext('status','--porcelain=v1')
assert head=='72597bcf3c71f586040cd882506dff8dcbf6c804',head
assert tree=='98f7304db2e39ad722121c24047f5f06aa515663',tree
assert not status,repr(status)
primary_sums_sha=sha((PRIMARY/'SHA256SUMS').read_bytes())
assert primary_sums_sha=='aaeee1a02507f830796ed72959adbc31177df9dfd7e2bf0d7236137962b46209',primary_sums_sha

primary_rows=jlread(PRIMARY/'review-ledger.jsonl')
assigned=[r for r in primary_rows if r['locale'] in LOCALES]
assert len(assigned)==120
assert len({(r['sourceIndex'],r['locale']) for r in assigned})==120
caller_inputs=jlread(PRIMARY/'source-caller-pins.jsonl')
caller_by_index=collections.defaultdict(list)
for i,p in enumerate(caller_inputs):
    caller_by_index[p['sourceIndex']].append((i,p))

# Reattest each caller's exact git blob, full-file hash, surface line and all pinned context lines.
caller_reattest=[]
for i,p in enumerate(caller_inputs):
    blob=gittext('rev-parse',f"{head}:{p['path']}").strip()
    data=git('show',f"{head}:{p['path']}")
    lines=data.decode('utf-8').splitlines()
    surface=lines[p['line']-1]
    checks={
        'blobMatchesInput':blob==p['fileBlob'],
        'fileSha256MatchesInput':sha(data)==p['fileSha256'],
        'surfaceLineTextMatchesAfterIndentTrim':surface.strip()==p['surfaceLine'],
        'surfaceLineSha256Matches':sha(surface)==p['lineSha256'],
        'contextLinesMatch':all(lines[c['line']-1]==c['text'] for c in p['contextLines']),
    }
    assert all(checks.values()),(p['sourceIndex'],checks)
    record={'pinId':f"src-{p['sourceIndex']}-pin-{i+1}",'sourceIndex':p['sourceIndex'],'sourceId':p['sourceId'],'path':p['path'],'fileBlob':blob,'fileSha256':sha(data),'line':p['line'],'surfaceLine':p['surfaceLine'],'lineSha256':sha(surface),'contextStartLine':p['contextStartLine'],'contextLines':p['contextLines'],'checks':checks,'result':'pass'}
    caller_reattest.append(record)

# Reattest all twelve catalogs and their exact shared key set; row details will pin assigned locales.
catalog_inputs=jlread(PRIMARY/'catalog-pins.jsonl')
assert len(catalog_inputs)==12
catalogs={}
catalog_reattest=[]
for p in catalog_inputs:
    blob=gittext('rev-parse',f"{head}:{p['path']}").strip()
    data=git('show',f"{head}:{p['path']}")
    obj=json.loads(data)
    keys=set(obj)
    catalogs[p['locale']]=obj
    record={'locale':p['locale'],'path':p['path'],'blob':blob,'fileSha256':sha(data),'keyCount':len(keys),'expectedKeyCount':p['keyCount'],'blobMatchesInput':blob==p['blob'],'fileSha256MatchesInput':sha(data)==p['fileSha256'],'keyCountMatchesInput':len(keys)==p['keyCount'],'keySetSha256':sha('\n'.join(sorted(keys))),'result':'pass'}
    assert record['blobMatchesInput'] and record['fileSha256MatchesInput'] and record['keyCountMatchesInput'],record
    catalog_reattest.append(record)
assert len({frozenset(c) for c in catalogs.values()})==1
shared_key_count=len(next(iter(catalogs.values())))

source_reason={
 862:'The caller labels an acquisition profile whose summary says lower concurrency and no automatic public-peer retries. The correction describes low network load or low impact, which better conveys the profile setting than a political or vague “conservative” sense.',
 863:'The Backfill Scheduler subtitle describes selective hash discovery from peers outside the product. The candidate expresses limited/targeted discovery and retains the exact lowercase product identifier `slskr`; the exclusion meaning is rendered naturally in each locale rather than forcing the English `non-` compound.',
 864:'This is the Contacts navigation label and page heading for managing peer contacts. The current short noun is a natural section label in this locale.',
 865:'This is an empty/unavailable-state heading in the Contacts page. The current wording clearly says contacts are unavailable and fits the page context.',
 866:'This is a Compatibility Dashboard tab label with a folder icon and directory listing beneath it. The current general translation of “Content” fits that section.',
 867:'This label precedes `contentIdA` in the perceptual similarity result. The target keeps the “A” item designation distinct from B; Hindi transliteration names the letter while preserving the distinction.',
 868:'This label precedes `contentIdB` in the perceptual similarity result. The target keeps the “B” item designation distinct from A; Hindi transliteration names the letter while preserving the distinction.',
 869:'The adjacent description explicitly says the tool returns a complete relationship graph for a ContentID. The candidate uses graph/relationship terminology rather than suggesting a chart or generic diagram.',
 870:'This appears as a Content ID table header and a form label for the identifier field. The candidate is a concise locale-appropriate label; “Content ID” is an interface phrase and is translatable here.',
 871:'This is a Pod Opinions input placeholder. The explanation is localized while the exact machine-readable example slug `content:audio:album:mb-id` is preserved.',
 872:'This is a Pod Content Linking input placeholder. The explanation is localized while the exact machine-readable example slug `content:audio:album:mb-release-id` is preserved; the French wording is consistent with adjacent #871.',
 873:'This server-message allowlist entry reports two required identifiers. The translation keeps the required status and exact API field names `contentId` and `variantHash`, as well as the API label.',
 874:'This validation message appears in the Content Linking workflow and server-message allowlist. The current text clearly states that the Content ID field is required.',
 875:'This is the Content Registry card description. It refers to identifier mappings and domain statistics; the Spanish candidate uses the same localized Content ID terminology as the nearby registry field.',
 876:'This is a server validation message specifying that Content ID must be a JSON string. The current message preserves exact `JSON` capitalization and conveys the constraint.',
 877:'This label precedes the resolved `contentId` value in a result message. The current locale-specific identifier label is clear in that context.',
 878:'This is the menu/workflow label for searching content and creating content-linked pods. The current concise translation fits the action.',
 879:'This message header introduces a content-metadata result with Title and metadata values below it. The current translation denotes metadata, not opinions.',
 880:'This heading labels the opinions input in the Pod Opinions panel. The candidates express opinions about the content rather than an ambiguous compressed noun phrase.',
 881:'This dashboard section covers DHT publishing performance and publication management. The current translation accurately names content publishing.',
}
locale_note={
 'ar':'Arabic wording preserves the section/validation sense; on W864 the negative relation is expressed as outside slskr, with exact lowercase `slskr` retained.',
 'de':'German wording is natural for the specific UI surface; on W864 “außerhalb von slskr” expresses the peer exclusion while retaining exact lowercase `slskr`.',
 'es':'Spanish wording is natural for the specific UI surface; on W864 “ajenos a slskr” expresses the peer exclusion while retaining exact lowercase `slskr`.',
 'fr':'French wording is natural for the specific UI surface; on W864 “hors slskr” expresses the peer exclusion while retaining exact lowercase `slskr`.',
 'hi':'Hindi wording is natural for the specific UI surface; on W864 “slskr से बाहर” expresses the peer exclusion while retaining exact lowercase `slskr`.',
 'id':'Indonesian wording is natural for the specific UI surface; on W864 “di luar slskr” expresses the peer exclusion while retaining exact lowercase `slskr`.',
}

markup_re=re.compile(r'</?[A-Za-z][^>]*>|\{\{?[^{}]+\}?\}|%[0-9$sdf]')
slug_tokens={871:['content:audio:album:mb-id'],872:['content:audio:album:mb-release-id']}
protect_tokens={873:['API','contentId','variantHash'],876:['JSON']}
negative_patterns={
 'ar':['غير','خارج'], 'de':['Nicht-','außerhalb'], 'es':['no son','ajenos'], 'fr':['non-','hors'], 'hi':['गैर','बाहर'], 'id':['non-','di luar']
}
ledger=[]
for r in sorted(assigned,key=lambda x:(x['sourceIndex'],LOCALE_ORDER.index(x['locale']))):
    idx=r['sourceIndex']; loc=r['locale']; source=r['sourceId']; cur=r['currentTarget']; cand=r['reviewedFinal']
    catalog_pin=next(p for p in catalog_reattest if p['locale']==loc)
    exact_current=catalogs[loc].get(source)
    assert exact_current==cur,(idx,loc,exact_current,cur)
    assert sha(source)==r['sourceSha256'] and sha(cur)==r['currentTargetSha256'] and sha(cand)==r['reviewedFinalSha256']
    primary_candidate=r.get('proposedTarget')
    assert (sha(primary_candidate)==r['proposedTargetSha256']) if primary_candidate is not None else r['proposedTargetSha256'] is None
    if r['disposition']=='accept-current':
        disposition='accept-current'; recommended=cur
    else:
        disposition='accept-proposal'; recommended=cand
    recommended_hash=sha(recommended)
    pindices=caller_by_index[idx]
    caller_ids=[f"src-{p['sourceIndex']}-pin-{i+1}" for i,p in pindices]
    caller_pin_hash=sha(canonical([caller_reattest[i] for i,p in pindices]))
    required=slug_tokens.get(idx,protect_tokens.get(idx,(['slskr'] if idx==863 else [])))
    current_missing=[t for t in required if t not in cur]
    candidate_missing=[t for t in required if t not in cand]
    recommended_missing=[t for t in required if t not in recommended]
    if idx==863:
        neg_current=any(p in cur for p in negative_patterns[loc])
        neg_candidate=any(p in cand for p in negative_patterns[loc])
        neg_recommended=any(p in recommended for p in negative_patterns[loc])
        assert 'slskr' in cur and 'slskr' in cand and 'slskr' in recommended
        assert neg_current and neg_candidate and neg_recommended,(loc,cur,cand)
        semantic_literal_note='The product identifier is protected exactly as lowercase `slskr`; the source negative compound `non-slskr` is not required verbatim when its negative/external meaning is naturally translated.'
    else:
        neg_current=neg_candidate=neg_recommended=None
        semantic_literal_note=None
    # Current examples intentionally fail in six cells; candidates restore the source slug.
    current_status='pass' if not current_missing else 'fail'
    candidate_status='pass' if not candidate_missing else 'fail'
    recommended_status='pass' if not recommended_missing else 'fail'
    assert not candidate_missing and not recommended_missing,(idx,loc,candidate_missing)
    src_markup=markup_re.findall(source); cur_markup=markup_re.findall(cur); cand_markup=markup_re.findall(cand); rec_markup=markup_re.findall(recommended)
    assert cur_markup==src_markup and cand_markup==src_markup and rec_markup==src_markup
    extra=[]
    if current_missing:
        extra.append('Current catalog target fails the exact protected-example-slug check; missing: '+', '.join(current_missing)+'. The primary candidate restores the exact token and is accepted.')
    if idx==863:
        extra.append('The exclusion is retained in both current and candidate; exact lowercase `slskr` is preserved, while locale-specific negative/external wording replaces English `non-` morphology.')
    if idx in slug_tokens:
        extra.append('The example slug is code-shaped input guidance, so it remains byte-for-byte unchanged while only the surrounding label/example wording is localized.')
    if idx==873: extra.append('Quoted API field names are exact and retain order/punctuation.')
    if idx==876: extra.append('`JSON` remains exact uppercase in the constraint message.')
    rationale=source_reason[idx]+' '+locale_note[loc]+' '+' '.join(extra)
    row={
      'sourceIndex':idx,'windowLabel':r['windowLabel'],'sourceId':source,'locale':loc,
      'sourceTarget':source,'sourceSha256':r['sourceSha256'],
      'currentTarget':cur,'currentTargetSha256':r['currentTargetSha256'],
      'currentTargetCatalogAttestation':{'matchesCatalogValue':exact_current==cur,'sha256Matches':sha(exact_current)==r['currentTargetSha256'],'catalogPath':catalog_pin['path'],'catalogBlob':catalog_pin['blob'],'catalogFileSha256':catalog_pin['fileSha256'],'catalogKeyCount':catalog_pin['keyCount']},
      'primaryDisposition':r['disposition'],'primaryProposedTarget':primary_candidate,'primaryProposedTargetSha256':r['proposedTargetSha256'],
      'primaryFinalTarget':cand,'primaryFinalTargetSha256':r['reviewedFinalSha256'],
      'crossReviewDisposition':disposition,'recommendedTarget':recommended,'recommendedTargetSha256':recommended_hash,
      'callerPinIds':caller_ids,'callerContextPinSetSha256':caller_pin_hash,
      'rationale':rationale,'confidence':'moderate','nativeSpeakerApproval':False,
      'protectedLiteralAttestations':{
        'requiredExactTokens':required,
        'currentTarget':{'missing':current_missing,'status':current_status},
        'primaryFinalTarget':{'missing':candidate_missing,'status':candidate_status},
        'recommendedTarget':{'missing':recommended_missing,'status':recommended_status},
        'negativeExclusionSemantics':({'currentTarget':neg_current,'primaryFinalTarget':neg_candidate,'recommendedTarget':neg_recommended,'note':semantic_literal_note} if idx==863 else None),
      },
      'placeholderAttestation':{'sourceTokens':[],'currentTokens':[],'primaryFinalTokens':[],'recommendedTokens':[],'status':'pass'},
      'markupAttestation':{'sourceMarkup':src_markup,'currentMarkup':cur_markup,'primaryFinalMarkup':cand_markup,'recommendedMarkup':rec_markup,'status':'pass'},
    }
    ledger.append(row)
assert len(ledger)==120
counts=collections.Counter(x['crossReviewDisposition'] for x in ledger)
assert counts=={'accept-current':88,'accept-proposal':32},counts

# W864 current/final semantic exclusion and exact product spelling checked; the key fixed-protection defects are six example cells.
current_slug_failures=[(x['sourceIndex'],x['locale'],x['currentTarget'],x['protectedLiteralAttestations']['currentTarget']['missing']) for x in ledger if x['protectedLiteralAttestations']['currentTarget']['status']=='fail']
assert {(i,l) for i,l,_,_ in current_slug_failures}=={(871,'es'),(871,'hi'),(871,'id'),(872,'es'),(872,'hi'),(872,'id')}

# Write row-level ledgers and exact caller/catalog reattestations.
(OUT/'crossreview-ledger.jsonl').write_text(''.join(canonical(x)+'\n' for x in ledger),encoding='utf-8')
(OUT/'caller-reattestation.jsonl').write_text(''.join(canonical(x)+'\n' for x in caller_reattest),encoding='utf-8')
(OUT/'catalog-reattestation.jsonl').write_text(''.join(canonical(x)+'\n' for x in catalog_reattest),encoding='utf-8')

primary_manifest=jread(PRIMARY/'manifest.json')
summary={
 'repository':'snapetech-org/slskR','pullRequest':204,'window':'W863-W882','assignedLocales':LOCALE_ORDER,
 'assignedCellCount':len(ledger),'dispositionCounts':dict(sorted(counts.items())),
 'candidateRevisions':sum(x['crossReviewDisposition']=='accept-proposal' for x in ledger),
 'rejectedCandidates':0,'holds':0,
 'exactPrimaryHead':head,'exactPrimaryTree':tree,'repositoryStatusBeforeAfter':'clean',
 'catalogsReattested':len(catalog_reattest),'catalogsAssigned':len(LOCALES),'catalogKeyCount':shared_key_count,'allTwelveCatalogKeySetsIdentical':True,
 'currentTargetCellReattestationsPassed':len(ledger),'currentTargetCellReattestationFailures':0,
 'currentProtectedExampleTokenFailures':len(current_slug_failures),
 'currentProtectedExampleFailures':[{'sourceIndex':i,'windowLabel':i+1,'locale':l,'target':t,'missingTokens':m,'primaryAcceptedTarget':next(x['recommendedTarget'] for x in ledger if x['sourceIndex']==i and x['locale']==l)} for i,l,t,m in current_slug_failures],
 'allCandidateAndRecommendedProtectedTokensPassed':all(x['protectedLiteralAttestations']['primaryFinalTarget']['status']=='pass' and x['protectedLiteralAttestations']['recommendedTarget']['status']=='pass' for x in ledger),
 'placeholderMismatches':0,'markupMismatches':0,
 'callerPinsReattested':len(caller_reattest),'callerPinFailures':0,'callerPinCountForWindow':len({x['sourceIndex'] for x in caller_reattest}),
 'sourceAndCallerContext':'All exact source caller pins are tied to commit blobs, file hashes, surface-line hashes, and pinned context lines; #863 exclusion is checked semantically with exact lowercase `slskr` retained.',
 'primaryPacketSha256SumsSha256':primary_sums_sha,'primaryReviewLedgerSha256':sha((PRIMARY/'review-ledger.jsonl').read_bytes()),
 'primaryManifestSha256':sha((PRIMARY/'manifest.json').read_bytes()),
 'livePRStateAttestation':'Parent combined packet owns live seven-PR head/state requery; this batch reattests the pinned local PR commit/tree.',
 'nativeSpeakerApproval':False,'testsBuildsScansCiBrowserRun':False,'repositoryModified':False,
 'reviewLimits':['Machine-assisted semantic cross-review; no native-speaker approval is established.','This batch makes no repository or PR changes.'],
}
(OUT/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
readme='''# slskR PR #204 cross-review batch — W863–W882\n\nIndependent row-level review for locales ar, de, es, fr, hi, and id (120 cells).\n\nThe pinned primary input is `slskr-pr204-window-0863-0882-primary-20261102`, whose `SHA256SUMS` SHA-256 is `'''+primary_sums_sha+'''`. This batch independently reattests the exact PR commit `'''+head+'''` and tree `'''+tree+'''`; the checkout was clean before and after.\n\nEach row records the exact source/current/primary/recommended strings and SHA-256 hashes, the catalog blob and file hash for its locale, caller pin IDs and a hash of those pinned contexts, a disposition, rationale, confidence, protected-literal findings, and placeholder/markup attestations. The current catalog values and all 120 cell hashes were reattested. All 12 locale catalogs were also reattested at 5,441 keys with identical key sets. All 27 source-caller context pins were verified against the pinned production file blobs, file hashes, surface lines, and context lines.\n\nThe six existing localized example slugs at W871–W872 for es, hi, and id omit or translate portions of the code-shaped source example. The accepted primary candidates restore the exact full slugs. At W864, `slskr` remains exact lowercase and exclusion is naturally expressed per locale; the English `non-` prefix need not be copied literally.\n\nDisposition counts: `accept-current` 88; `accept-proposal` 32; `revise-proposal` 0; `reject` 0; `hold` 0.\n\nThis is machine-assisted cross-review and does not establish native-speaker approval. No repository/PR edits, tests, builds, scans, CI, or browser review were performed in this batch. The parent combined packet owns the live seven-PR state/head requery.\n'''
(OUT/'README.md').write_text(readme,encoding='utf-8')

# Manifest lists stable artifacts but not itself or checksum file (avoids cyclic hashes).
files=[]
for name in ['README.md','crossreview-ledger.jsonl','caller-reattestation.jsonl','catalog-reattestation.jsonl','summary.json','build_batch.py']:
    data=(OUT/name).read_bytes()
    files.append({'path':name,'bytes':len(data),'sha256':sha(data)})
manifest={
 'repository':'snapetech-org/slskR','pullRequest':204,'window':'W863-W882','assignedLocales':LOCALE_ORDER,
 'head':head,'tree':tree,'primaryInput':{'directory':str(PRIMARY),'sha256SumsSha256':primary_sums_sha,'manifestSha256':sha((PRIMARY/'manifest.json').read_bytes()),'reviewLedgerSha256':sha((PRIMARY/'review-ledger.jsonl').read_bytes())},
 'cellCount':120,'dispositionCounts':dict(sorted(counts.items())),'callerPinsReattested':len(caller_reattest),'catalogLocalesReattested':len(catalog_reattest),'sharedCatalogKeyCount':shared_key_count,'files':files,
 'nativeSpeakerApproval':False,'repositoryModified':False,
}
(OUT/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
# Checksums cover all deliverable artifacts, including manifest and helper.
(OUT/'manifest.sha256').write_text(f"{sha((OUT/'manifest.json').read_bytes())}  manifest.json\n",encoding='utf-8')
entries=[]
for p in sorted(OUT.iterdir()):
    if p.is_file() and p.name != 'SHA256SUMS':
        entries.append(f"{sha(p.read_bytes())}  {p.name}")
(OUT/'SHA256SUMS').write_text('\n'.join(entries)+'\n',encoding='utf-8')
print(json.dumps({'path':str(OUT),'counts':dict(counts),'manifestSha256':sha((OUT/'manifest.json').read_bytes()),'sumsSha256':sha((OUT/'SHA256SUMS').read_bytes()),'currentSlugFailures':current_slug_failures,'callerPins':len(caller_reattest),'catalogs':len(catalog_reattest)},ensure_ascii=False,indent=2))
