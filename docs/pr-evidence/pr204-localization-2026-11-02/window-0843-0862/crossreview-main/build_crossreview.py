#!/usr/bin/env python3
"""Build static, read-only cross-review evidence for slskR PR #204 W843-W862."""
from __future__ import annotations
import collections, datetime, hashlib, json, pathlib, re, shutil, subprocess, socket

REPO = pathlib.Path('/home/keith/Documents/code/task-worktrees/localization-20261102-slskr')
PRIMARY = pathlib.Path('/mnt/disks/scratch/task-scratch/slskr-pr204-window-0843-0862-primary-20261102')
HIDVI = pathlib.Path('/mnt/disks/scratch/task-scratch/slskr-pr204-window-0843-0862-crossreview-hidvi-20261102')
OUT = pathlib.Path('/mnt/disks/scratch/task-scratch/slskr-pr204-window-0843-0862-crossreview-20261102')
EXPECTED_HEAD = 'b52b7c9abd112328a70d9e811d3b6aa2d4feb8e6'
EXPECTED_TREE = 'd7a46bce75c76e3a74736b85175f7fa412324f39'
BRANCH = 'codex/slskr-l10n-audit-20261030'
LOCALES = ['ar','de','es','fr','ja','ko','pt-BR','zh-Hans','zh-Hant']
ALL_LOCALES = ['ar','de','es','fr','hi','id','ja','ko','pt-BR','vi','zh-Hans','zh-Hant']
START, END = 842, 861  # zero-based positions in sorted source-key order
PR_SET = [('SeerrNG',418),('ChaptarrNG',190),('QuestarrNG',155),('ROMarrNG',70),('slskR',204),('slskdN',409),('TorrentNG',243)]
PRIOR_PATH = 'docs/pr-evidence/pr204-localization-2026-11-02/connection-state-review'
PRIOR_BASE = '9d3aae249503d1732cc890a650052c85c57b2919'
PRIOR_CAPTURE_COMMIT = 'aa106d2505de8c9ace2d7d6dbf2af9777651947d'

# Independent current-string issues found in caller context, plus one revised primary proposal.
NEW_TARGETS = {
    (842,'zh-Hans'): '连接的客户端(',
    (842,'zh-Hant'): '連接的客戶端(',
    (843,'fr'): 'Clients slskr connectés pour la synchronisation des hachages',
    (849,'ar'): 'جارٍ الاتصال بتحديثات البحث المباشر. عمليات البحث المحملة متاحة أدناه.',
    (849,'de'): 'Verbindung zu Live-Suchaktualisierungen wird hergestellt. Ihre geladenen Suchanfragen sind unten verfügbar.',
    (849,'es'): 'Conectando a las actualizaciones de búsqueda en vivo. Sus búsquedas cargadas están disponibles a continuación.',
    (849,'fr'): 'Connexion en cours aux mises à jour de recherche en direct. Vos recherches chargées sont disponibles ci-dessous.',
    (849,'ja'): 'ライブ検索の更新に接続中です。読み込んだ検索は以下で利用できます。',
    (849,'zh-Hans'): '正在连接到实时搜索更新。您加载的搜索可在下面找到。',
    (849,'zh-Hant'): '正在連線至即時搜尋更新。您載入的搜尋可在下面找到。',
}
REVISE_PRIMARY = {
    (852,'fr'): 'Délai d’attente de connexion (millisecondes)',
}
NEW_REASONS = {
    (842,'zh-Hans'): 'The caller renders this localized prefix immediately before a count and appends a hardcoded ASCII closing parenthesis. The full-width opening parenthesis currently mismatches that literal; use ASCII opening punctuation to pair with the caller suffix.',
    (842,'zh-Hant'): 'The caller renders this localized prefix immediately before a count and appends a hardcoded ASCII closing parenthesis. The full-width opening parenthesis currently mismatches that literal; use ASCII opening punctuation to pair with the caller suffix.',
    (843,'fr'): 'In the Mesh Peers subheader, this names already-connected clients used to synchronize hash values. “Du hachage” can mean the hashing process; “des hachages” identifies the values being synchronized.',
    (849,'ar'): 'The caller displays this with a loading icon while the live-search hub connection is being started. Make the first clause explicitly progressive; the existing clause reads as a noun phrase.',
    (849,'de'): 'The caller displays this with a loading icon while the live-search hub connection is being started. Make the first clause explicitly progressive; the current infinitive does not state that connection is underway.',
    (849,'es'): 'The caller displays this with a loading icon while the live-search hub connection is being started. Replace the noun phrase with an ongoing action.',
    (849,'fr'): 'The caller displays this with a loading icon while the live-search hub connection is being started. Mark the connection as in progress instead of using a bare noun phrase.',
    (849,'ja'): 'The caller displays this with a loading icon while the live-search hub connection is being started. Use 接続中 to state that the connection is in progress; 接続します reads as a future or intent.',
    (849,'zh-Hans'): 'The caller displays this with a loading icon while the live-search hub connection is being started. Add 正在 to make the ongoing connection state explicit.',
    (849,'zh-Hant'): 'The caller displays this with a loading icon while the live-search hub connection is being started. Add 正在 to make the ongoing connection state explicit.',
}
REVISE_REASONS = {
    (852,'fr'): 'The field is an FTP connection-timeout value in milliseconds. “Délai d’attente de connexion” is the established French UI phrasing for a timeout; “délai d’expiration” suggests expiry rather than waiting for the connection.',
}


def sha(data: bytes | str) -> str:
    if isinstance(data, str): data = data.encode('utf-8')
    return hashlib.sha256(data).hexdigest()

def git(args: list[str], *, text=True, check=True):
    return subprocess.run(['git', *args], cwd=REPO, text=text, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=check).stdout

def gh_json(path: str):
    return json.loads(subprocess.check_output(['gh','api',path], text=True))

def jsonl(path: pathlib.Path):
    return [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines() if line]

def write_json(path: pathlib.Path, obj):
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=True) + '\n', encoding='utf-8')

def write_jsonl(path: pathlib.Path, rows):
    path.write_text(''.join(json.dumps(x, ensure_ascii=False, sort_keys=True) + '\n' for x in rows), encoding='utf-8')

def capture_git_state(stage: str):
    status = git(['status','--porcelain','--untracked-files=all']).strip()
    state = {
        'stage': stage,
        'host': socket.gethostname().split('.')[0],
        'worktree': str(REPO),
        'branch': git(['branch','--show-current']).strip(),
        'head': git(['rev-parse','HEAD']).strip(),
        'tree': git(['rev-parse','HEAD^{tree}']).strip(),
        'statusPorcelain': status,
        'clean': not bool(status),
    }
    return state

def capture_prs(stage: str):
    rows=[]
    for name, number in PR_SET:
        repo=f'snapetech-org/{name}'
        pr=gh_json(f'repos/{repo}/pulls/{number}')
        head=pr['head']['sha']
        commit=gh_json(f'repos/{repo}/commits/{head}')
        rows.append({
            'repository':repo, 'number':number, 'stage':stage,
            'state':pr['state'], 'isDraft':pr['draft'],
            'head':head, 'tree':commit['commit']['tree']['sha'],
            'headBranch':pr['head']['ref'], 'base':pr['base']['sha'],
            'url':pr['html_url'],
        })
    return rows

def verify_sum_file(folder: pathlib.Path, sums_name='SHA256SUMS'):
    checks=[]
    for line in (folder/sums_name).read_text().splitlines():
        if not line.strip(): continue
        digest, rel=line.split('  ',1)
        actual=sha((folder/rel).read_bytes())
        checks.append({'path':str(folder/rel),'expectedSha256':digest,'actualSha256':actual,'matches':digest==actual})
    assert checks and all(x['matches'] for x in checks), checks
    return checks

def source_markers(s):
    placeholders=re.findall(r'\{[^{}]+\}', s)
    markup=re.findall(r'</?[A-Za-z][^>]*>', s)
    return {'placeholders':placeholders,'markup':markup}

OUT.mkdir(parents=True, exist_ok=True)
generated_names={'INPUT-SHA256SUMS','live-pr-heads.json','git-state-before.json','git-state-after.json','remote-branch-attestation.json','primary-input-attestation.json','catalog-reattestation.jsonl','source-window-reattestation.jsonl','caller-reattestation.jsonl','caller-gap.json','prior-review-attestation.json','prior-review-reattestation.jsonl','crossreview-ledger.jsonl','correction-candidates.jsonl','summary.json','README.md','manifest.json','SHA256SUMS'}
unknown=[p.name for p in OUT.iterdir() if p.name not in generated_names and p.name!='build_crossreview.py']
if unknown:
    raise SystemExit(f'Unknown files in task output directory; preserving them: {unknown}')
for name in generated_names:
    candidate=OUT/name
    if candidate.is_file(): candidate.unlink()
    elif candidate.exists(): raise SystemExit(f'Not removing non-file task output: {candidate}')

captured_at=datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds')
pre=capture_git_state('before')
assert pre['head']==EXPECTED_HEAD and pre['tree']==EXPECTED_TREE and pre['branch']==BRANCH and pre['clean'], pre
pr_start=capture_prs('start')
pr204=next(x for x in pr_start if x['number']==204)
assert pr204['state']=='open' and pr204['isDraft'] and pr204['head']==EXPECTED_HEAD and pr204['tree']==EXPECTED_TREE and pr204['headBranch']==BRANCH, pr204
remote_line=git(['ls-remote','taskgithub',f'refs/heads/{BRANCH}']).strip().split()
assert len(remote_line)>=2 and remote_line[0]==EXPECTED_HEAD, remote_line

# Verify input packet checksums and manifest before consuming its review rows.
primary_manifest=json.loads((PRIMARY/'manifest.json').read_text())
primary_sum_checks=verify_sum_file(PRIMARY)
assert primary_manifest['head']==EXPECTED_HEAD and primary_manifest['tree']==EXPECTED_TREE
assert sha((PRIMARY/'SHA256SUMS').read_bytes())==primary_manifest['sha256SumsSha256']
primary_ledger=jsonl(PRIMARY/'review-ledger.jsonl')
source_pins=jsonl(PRIMARY/'source-window-and-boundaries.jsonl')
caller_pins=jsonl(PRIMARY/'source-caller-pins.jsonl')
caller_gaps=jsonl(PRIMARY/'caller-gaps.jsonl')
catalog_pins=jsonl(PRIMARY/'catalog-pins.jsonl')
prior_pins=jsonl(PRIMARY/'prior-review-reattestation.jsonl')
assert len(primary_ledger)==240 and len(source_pins)==22 and len(caller_pins)==94 and len(catalog_pins)==12 and len(prior_pins)==24

# Read current exact-head catalogs via git, verify every byte hash/blob and sorted key parity.
catalogs={}; catalog_rows=[]; key_orders=[]; catalog_sha={}
for pin in catalog_pins:
    raw=git(['show',f"{EXPECTED_HEAD}:{pin['path']}"],text=False)
    data=json.loads(raw)
    keys=sorted(data)
    assert sha(raw)==pin['fileSha256'] and len(data)==pin['keyCount']==5441
    blob=subprocess.check_output(['git','hash-object','--stdin'],input=raw,cwd=REPO,text=False).decode().strip()
    assert blob==pin['blob'],(pin['locale'],blob,pin['blob'])
    catalogs[pin['locale']]=data; key_orders.append(keys); catalog_sha[pin['locale']]=sha(raw)
    catalog_rows.append({**pin,'actualFileSha256':sha(raw),'actualBlob':blob,'sortedKeyCount':len(keys),'matches':True})
assert all(keys==key_orders[0] for keys in key_orders[1:])
keys=key_orders[0]
source_by_index={p['sourceIndex']:p for p in source_pins}
assert source_by_index[841]['sourceId']=='Connected' and source_by_index[862]['sourceId']=='Conservative Network'
for i in range(842,862):
    pin=source_by_index[i]
    assert keys[i]==pin['sourceId'] and sha(pin['sourceId'])==pin['sourceSha256']
    assert all(pin['sourceId'] in catalogs[l] for l in ALL_LOCALES)

# Reattest all pinned production caller source files/lines/context against the exact PR tree.
caller_rows=[]
for c in caller_pins:
    raw=git(['show',f"{EXPECTED_HEAD}:{c['path']}"],text=False)
    lines=raw.decode('utf-8').splitlines()
    line=lines[c['line']-1]
    file_blob=subprocess.check_output(['git','hash-object','--stdin'],input=raw,cwd=REPO,text=False).decode().strip()
    context_ok=all(lines[ctx['line']-1]==ctx['text'] for ctx in c['contextLines'])
    matches=(sha(raw)==c['fileSha256'] and file_blob==c['fileBlob'] and sha(line)==c['lineSha256'] and line.strip()==c['surfaceLine'] and context_ok)
    assert matches,(c['path'],c['line'])
    caller_rows.append({
        'sourceIndex':c['sourceIndex'],'sourceId':c['sourceId'],'path':c['path'],'line':c['line'],
        'fileBlob':file_blob,'fileSha256':sha(raw),'lineSha256':sha(line),'surfaceLine':line.strip(),
        'contextLines':c['contextLines'],'matches':True,
    })
assert len(set(x['path'] for x in caller_rows))==25

# Reattest exact primary current/proposal cell hashes for all locales, then select assigned nine.
primary_by={(r['sourceIndex'],r['locale']):r for r in primary_ledger}
assert len(primary_by)==240
for r in primary_ledger:
    assert sha(r['sourceId'])==r['sourceSha256']
    assert catalogs[r['locale']][r['sourceId']]==r['currentTarget']
    assert sha(r['currentTarget'])==r['currentTargetSha256']
    assert sha(r['reviewedFinal'])==r['reviewedFinalSha256']
    if r['proposedTarget'] is not None: assert sha(r['proposedTarget'])==r['proposedTargetSha256']
assert len({(r['sourceIndex'],r['locale']) for r in primary_ledger})==240

# Reattest the two reused reviews. Their evidence artifact captures the exact dirty-tree
# catalog files against base 9d3..., and those hashes were subsequently committed in aa106d25.
prior_commit=git(['rev-parse',PRIOR_CAPTURE_COMMIT]).strip()
assert prior_commit==PRIOR_CAPTURE_COMMIT
prior_cells_raw=git(['show',f'{prior_commit}:{PRIOR_PATH}/review-cells.jsonl'],text=False)
prior_summary_raw=git(['show',f'{prior_commit}:{PRIOR_PATH}/review-summary.json'],text=False)
prior_sums_raw=git(['show',f'{prior_commit}:{PRIOR_PATH}/SHA256SUMS'],text=False)
prior_cells=[json.loads(x) for x in prior_cells_raw.decode().splitlines()]
prior_summary=json.loads(prior_summary_raw)
assert prior_summary['pullRequest']['headRefOid']==PRIOR_BASE and prior_summary['pullRequest']['state']=='OPEN' and prior_summary['pullRequest']['isDraft']
assert prior_summary['workingTreeStatusAtReview'] and len(prior_summary['catalogAttestations'])==12
prior_checks=[]
for line in prior_sums_raw.decode().splitlines():
    digest, rel=line.split('  ',1)
    raw=git(['show',f'{prior_commit}:{PRIOR_PATH}/{rel}'],text=False)
    prior_checks.append({'path':f'{PRIOR_PATH}/{rel}','expectedSha256':digest,'actualSha256':sha(raw),'matches':digest==sha(raw)})
assert all(x['matches'] for x in prior_checks)
prior_catalog_attests={x['locale']:x for x in prior_summary['catalogAttestations']}
for a in prior_catalog_attests.values():
    raw=git(['show',f'{prior_commit}:{a["path"]}'],text=False)
    assert sha(raw)==a['workingFileSha256']
prior_by={(r['sourceKey'],r['locale']):r for r in prior_cells}
prior_reattest=[]
for p in prior_pins:
    source=p['sourceId']; locale=p['locale']
    old=prior_by[(source,locale)]
    old_raw=git(['show',f'{prior_commit}:web/src/lib/locales/ui-labels.{locale}.json'],text=False)
    old_catalog=json.loads(old_raw)
    current=catalogs[locale][source]
    current_sha=sha(current)
    assert old['crossReviewDisposition']=='accept' and p['priorCrossReviewDisposition']=='accept'
    assert old['sourceSha256']==sha(source)==sha(p['sourceId'])
    assert old['currentTargetSha256']==old['recommendedTargetSha256']==p['currentTargetSha256']==current_sha
    assert old_catalog[source]==old['currentTarget']==old['recommendedTarget']
    assert sha(old_raw)==prior_catalog_attests[locale]['workingFileSha256']
    prior_reattest.append({
        'sourceIndex':p['sourceIndex'],'sourceId':source,'locale':locale,
        'sourceSha256':old['sourceSha256'],'currentTargetSha256':current_sha,
        'priorDisposition':old['crossReviewDisposition'],'priorRecommendedTargetSha256':old['recommendedTargetSha256'],
        'priorReviewBaseHead':PRIOR_BASE,'priorWorktreeSnapshotCommit':prior_commit,
        'priorCatalogSnapshotSha256':sha(old_raw),'priorReviewCellEvidenceSha256':sha(prior_cells_raw),
        'reviewedFilePath':f'{PRIOR_PATH}/review-cells.jsonl','matchesCurrent':True,
    })
assert len(prior_reattest)==24

# Create all 180 exact-hash cell dispositions, including every primary candidate.
caller_by_source=collections.defaultdict(list)
for c in caller_rows: caller_by_source[(c['sourceIndex'],c['sourceId'])].append(c)
gap_by_source={(x['sourceIndex'],x['sourceId']):x for x in caller_gaps}
prior_by_current={(x['sourceIndex'],x['locale']):x for x in prior_reattest}
cross=[]
for i in range(START,END+1):
    source=keys[i]
    for locale in LOCALES:
        p=primary_by[(i,locale)]
        current=catalogs[locale][source]
        assert current==p['currentTarget']
        primary_target=p['proposedTarget']
        key=(i,locale)
        if key in NEW_TARGETS:
            final=NEW_TARGETS[key]; action='revise-current'; disp='revise'; kind='missed-current-issue'; rationale=NEW_REASONS[key]
        elif key in REVISE_PRIMARY:
            final=REVISE_PRIMARY[key]; action='revise-primary-proposal'; disp='revise'; kind='revised-primary-proposal'; rationale=REVISE_REASONS[key]
        elif primary_target is not None:
            final=primary_target; action='accept-primary-proposal'; disp='accept'; kind='primary-proposal'; rationale=p['rationale']
        else:
            final=current; action='accept-current'; disp='accept'; kind='no-correction'; rationale='Reviewed against the exact caller/source context and neighboring terminology; the current wording is semantically suitable, with no issue found in placeholders, markup, or protected literals.'
        current_marks=source_markers(current); final_marks=source_markers(final); source_marks=source_markers(source)
        assert current_marks==source_marks and final_marks==source_marks,(i,locale,'placeholder/markup')
        protected=[term for term in ['Soulseek','slskr'] if term in source]
        for term in protected:
            assert current.count(term)==source.count(term) and final.count(term)==source.count(term),(i,locale,term)
        pins=caller_by_source.get((i,source),[])
        gap=gap_by_source.get((i,source))
        prior=prior_by_current.get((i,locale))
        if (i,locale) in [(842,'zh-Hans'),(842,'zh-Hant')]:
            assert pins and any('connectedClientCount})' in x['surfaceLine'] for x in pins)
        if i==848: assert gap and not pins
        if i in (847,851): assert prior
        cross.append({
            'sourceIndex':i,'sourceId':source,'sourceSha256':sha(source),
            'locale':locale,'catalogPath':f'web/src/lib/locales/ui-labels.{locale}.json',
            'catalogBlob':next(x['blob'] for x in catalog_pins if x['locale']==locale),
            'catalogFileSha256':catalog_sha[locale],
            'currentTarget':current,'currentTargetSha256':sha(current),
            'primaryDisposition':p['disposition'],'primaryProposedTarget':primary_target,
            'primaryProposedTargetSha256':p['proposedTargetSha256'],
            'reviewDisposition':disp,'reviewAction':action,'candidateKind':kind,
            'reviewedFinal':final,'reviewedFinalSha256':sha(final),'rationale':rationale,
            'confidence':'moderate','callerPinCount':len(pins),
            'callerPinRefs':[{'path':x['path'],'line':x['line'],'fileSha256':x['fileSha256'],'lineSha256':x['lineSha256']} for x in pins],
            'callerContextGap':gap,
            'placeholders':{'source':source_marks['placeholders'],'current':current_marks['placeholders'],'final':final_marks['placeholders'],'match':True},
            'markup':{'source':source_marks['markup'],'current':current_marks['markup'],'final':final_marks['markup'],'match':True},
            'protectedLiterals':{'expected':protected,'currentPreserved':True,'finalPreserved':True},
            'priorConnectionReview':prior,
        })
assert len(cross)==180 and len({(r['sourceIndex'],r['locale']) for r in cross})==180
counts=collections.Counter(r['reviewAction'] for r in cross)
assert counts=={'accept-current':133,'accept-primary-proposal':36,'revise-current':10,'revise-primary-proposal':1},counts
assert sum(r['primaryProposedTarget'] is not None for r in cross)==37
assert sum(r['reviewDisposition']=='revise' for r in cross)==11
assert all(r['reviewDisposition']!='hold' for r in cross)

# Dedupe and pairwise source/target safeguards for the review window.
cell_keys=[(r['sourceIndex'],r['locale']) for r in cross]
assert len(cell_keys)==len(set(cell_keys))
assert len(set((r['sourceIndex'],r['locale']) for r in cross if r['primaryProposedTarget'] is not None))==37

# Capture end state and ensure no PR or checkout drift occurred during read-only review.
pr_end=capture_prs('end')
pre_by={(x['repository'],x['number']):x for x in pr_start}
end_by={(x['repository'],x['number']):x for x in pr_end}
assert all((pre_by[k]['head'],pre_by[k]['tree'],pre_by[k]['state'],pre_by[k]['isDraft'])==(end_by[k]['head'],end_by[k]['tree'],end_by[k]['state'],end_by[k]['isDraft']) for k in pre_by)
post=capture_git_state('after')
assert post['head']==pre['head'] and post['tree']==pre['tree'] and post['branch']==pre['branch'] and post['clean'],post

# Input checksum ledger records the full primary packet and separate HI/ID/VI packet.
input_paths=[]
for file in sorted(PRIMARY.iterdir()):
    if file.is_file(): input_paths.append(file)
for file in sorted(HIDVI.iterdir()):
    if file.is_file(): input_paths.append(file)
(OUT/'INPUT-SHA256SUMS').write_text(''.join(f'{sha(f.read_bytes())}  {f}\n' for f in input_paths),encoding='utf-8')

write_json(OUT/'live-pr-heads.json',{'capturedAtUtc':captured_at,'initial':pr_start,'final':pr_end,'stableAcrossReview':True})
write_json(OUT/'git-state-before.json',pre)
write_json(OUT/'git-state-after.json',post)
write_json(OUT/'remote-branch-attestation.json',{'remote':'taskgithub','branch':BRANCH,'resolvedHead':remote_line[0],'matchesPrHead':True})
write_json(OUT/'primary-input-attestation.json',{
    'packetPath':str(PRIMARY),'manifestSha256':sha((PRIMARY/'manifest.json').read_bytes()),
    'sha256SumsSha256':sha((PRIMARY/'SHA256SUMS').read_bytes()),
    'inputFileChecks':primary_sum_checks,'reviewLedgerRowsReattested':len(primary_ledger),
    'windowSourceRowsReattested':20,'windowSortedKeyIndices':[START,END],
    'allTwelveCatalogsReattested':True,'callerPinRowsReattested':len(caller_rows),
})
write_jsonl(OUT/'catalog-reattestation.jsonl',catalog_rows)
write_jsonl(OUT/'source-window-reattestation.jsonl',[{'sourceIndex':x['sourceIndex'],'sourceId':x['sourceId'],'sourceSha256':x['sourceSha256'],'sortedKeyMatch':keys[x['sourceIndex']]==x['sourceId']} for x in source_pins])
write_jsonl(OUT/'caller-reattestation.jsonl',caller_rows)
write_json(OUT/'caller-gap.json',{'sourceIndex':848,'sourceId':'Connecting to Soulseek…','locales':LOCALES,'reason':gap_by_source[(848,'Connecting to Soulseek…')]['reason'],'reviewScope':'self-contained status text and catalog parity only'})
write_json(OUT/'prior-review-attestation.json',{
    'reviewedBaseHead':PRIOR_BASE,'reviewedPrState':'open','reviewedPrDraft':True,
    'reviewArtifactCommit':prior_commit,'reviewArtifactPath':f'{PRIOR_PATH}/review-cells.jsonl',
    'reviewArtifactSha256':sha(prior_cells_raw),'reviewSummarySha256':sha(prior_summary_raw),
    'reviewArtifactRows':len(prior_cells),'reusedSourceStates':['Connecting','Connection Failed'],
    'reusedRowsReattested':len(prior_reattest),'reusedRowsForAssignedLocales':sum(x['locale'] in LOCALES for x in prior_reattest),
    'priorSumsChecks':prior_checks,'catalogSnapshotMatchesRecordedWorkingFileHashes':True,
    'trackedBaseCatalogKeyPresenceByLocale':{locale:{key:(key in json.loads(git(['show',f'{PRIOR_BASE}:web/src/lib/locales/ui-labels.{locale}.json'],text=False))) for key in ['Connecting','Connection Failed']} for locale in ALL_LOCALES},
    'interpretation':'The prior review metadata pins base head 9d3aae but records a dirty working tree with 12 modified locale files. The review artifact committed at aa106d25 records those exact working-file SHA-256 values; they reattest to the catalog blobs at aa106d25, and all reused target hashes exactly match current b52b7c9 values. This is exact text reuse against the captured patch, not a claim that those keys were present in the tracked 9d3aae tree.'
})
write_jsonl(OUT/'prior-review-reattestation.jsonl',prior_reattest)
write_jsonl(OUT/'crossreview-ledger.jsonl',cross)
write_jsonl(OUT/'correction-candidates.jsonl',[r for r in cross if r['reviewDisposition']=='revise'])

separate_summary=json.loads((HIDVI/'summary.json').read_text())
assert separate_summary['cellsReviewed']==60 and separate_summary['exactHead']==EXPECTED_HEAD and separate_summary['exactTree']==EXPECTED_TREE
hidvi_checks=verify_sum_file(HIDVI)
summary={
    'repository':'snapetech-org/slskR','pullRequest':204,'state':'open','draft':True,
    'exactHead':EXPECTED_HEAD,'exactTree':EXPECTED_TREE,
    'window':'W843-W862','sourceIndexStart':START,'sourceIndexEnd':END,'sourceCount':20,
    'localesReviewed':LOCALES,'cellsReviewed':len(cross),'primaryCandidateCells':37,
    'primaryProposalsAccepted':counts['accept-primary-proposal'],
    'primaryProposalsRevised':counts['revise-primary-proposal'],
    'currentCellsAccepted':counts['accept-current'],'newCorrections':counts['revise-current'],
    'revisedPrimaryProposals':counts['revise-primary-proposal'],
    'holds':0,'deduplicatedCellKeys':len(set(cell_keys)),
    'callerPinsReattested':len(caller_rows),'callerFiles':len(set(x['path'] for x in caller_rows)),
    'catalogLocalesReattested':len(catalog_rows),'catalogKeysPerLocale':5441,
    'catalogSortedKeyParity':'pass','placeholderMismatches':0,'markupMismatches':0,
    'protectedLiteralMismatches':0,'priorConnectionRowsReattested':len(prior_reattest),
    'priorConnectionRowsForAssignedLocales':sum(x['locale'] in LOCALES for x in prior_reattest),
    'sourceCallerGap':{'sourceIndex':848,'sourceId':'Connecting to Soulseek…','cells':9},
    'separateHiIdViPacket':{'path':str(HIDVI),'cells':separate_summary['cellsReviewed'],'acceptCurrent':separate_summary['counts']['accept-current'],'acceptPrimaryProposal':separate_summary['counts']['accept-primary-proposal'],'newCorrections':separate_summary['newCorrections'],'holds':separate_summary['holds'],'sha256SumsVerified':all(x['matches'] for x in hidvi_checks)},
    'allSevenPrHeadsRequeried':True,'prHeadsStableAcrossReview':True,
    'worktreeCleanBeforeAndAfter':True,'repositoryModified':False,
    'testsBuildsCiBrowserRun':False,'nativeSpeakerApproval':False,'headedBrowserApproval':False,
    'confidence':'moderate; static language/context cross-review; native-speaker validation remains separate',
}
write_json(OUT/'summary.json',summary)

readme=f'''# slskR PR #204 W843–W862 independent cross-review

Reviewed {len(cross)} cells across nine locales (Arabic, German, Spanish, French, Japanese, Korean, Brazilian Portuguese, Simplified Chinese, Traditional Chinese) at OPEN/DRAFT head `{EXPECTED_HEAD}`, tree `{EXPECTED_TREE}`. Source indices {START}–{END} are zero-based positions in the lexicographically sorted source keys; the pinned boundary keys are index 841 `Connected` and index 862 `Conservative Network`.

## Dispositions

- {counts['accept-current']} exact current strings accepted.
- {counts['accept-primary-proposal']} of {sum(r['primaryProposedTarget'] is not None for r in cross)} primary proposals accepted.
- {counts['revise-primary-proposal']} primary proposal revised: French `Connection Timeout Milliseconds` uses “Délai d’attente de connexion (millisecondes)”.
- {counts['revise-current']} missed current-string issues recorded as corrections: two Chinese count-prefix parentheses that pair with the hardcoded ASCII `)`; French hash values in the Mesh Peers subheader; and seven non-progressive live-search loading messages (ar, de, es, fr, ja, zh-Hans, zh-Hant).
- Holds: 0. All 180 `(sourceIndex, locale)` cells are unique and hash-pinned.

## Reattestation

All seven GitHub PR heads were queried at start and end; all stayed stable. slskR #204 remains OPEN/DRAFT at the requested head/tree. The task checkout was clean at the exact head/tree before and after. All 12 locale catalogs have 5,441 identical sorted keys; all 94 caller pins across 25 files reattest by file blob/hash, line hash, and recorded context lines. Every primary-ledger current/proposed hash was rechecked, then the assigned 180 current values and reviewed finals were independently recorded with exact SHA-256 hashes.

The prior `Connecting` and `Connection Failed` review records reattest for all 24 locales (18 of those rows belong to this nine-locale packet). Their review summary records base head `{PRIOR_BASE}` plus a dirty worktree with 12 modified catalog files. Those recorded working-file SHA-256 values match the catalog files captured in commit `{prior_commit}`; the 24 accepted target hashes also match the current PR catalog strings exactly. The evidence packet documents this boundary rather than treating the base tree itself as containing those keys.

`Connecting to Soulseek…` has no production text caller at this head. Its nine locale cells are reviewed as self-contained status strings only, with the caller gap retained in the evidence.

A separate completed packet covers Hindi, Indonesian, and Vietnamese: `{HIDVI}`. Its checksums were verified; it reports 60 cells, 14 accepted primary proposals, 43 accepted current values, 3 new correction candidates, and no holds.

## Limits and files

This is static semantic review. It does not claim native-speaker or headed-browser approval. No repository files changed, and no tests, builds, CI, or browser work ran. `crossreview-ledger.jsonl` has one exact-hash row per cell; `correction-candidates.jsonl` lists every revised cell. Caller, catalog, source, prior-review, live-PR, and worktree attestations are separate machine-readable files.
'''
(OUT/'README.md').write_text(readme,encoding='utf-8')

# Build a deterministic output manifest and sums. Exclude the sums file from itself.
files=[]
for f in sorted(OUT.iterdir()):
    if f.is_file() and f.name not in ('SHA256SUMS','manifest.json'):
        b=f.read_bytes(); files.append({'path':f.name,'bytes':len(b),'sha256':sha(b)})
write_json(OUT/'manifest.json',{'repository':'snapetech-org/slskR','pullRequest':204,'head':EXPECTED_HEAD,'tree':EXPECTED_TREE,'window':'W843-W862','files':files})
sum_lines=[]
for f in sorted(OUT.iterdir()):
    if f.is_file() and f.name!='SHA256SUMS': sum_lines.append(f'{sha(f.read_bytes())}  {f.name}\n')
(OUT/'SHA256SUMS').write_text(''.join(sum_lines),encoding='utf-8')

# Readback/checksum audit after writing.
for line in (OUT/'SHA256SUMS').read_text().splitlines():
    digest,name=line.split('  ',1)
    assert sha((OUT/name).read_bytes())==digest,(name,digest)
ledger_readback=jsonl(OUT/'crossreview-ledger.jsonl')
assert len(ledger_readback)==180 and all(sha(x['reviewedFinal'])==x['reviewedFinalSha256'] for x in ledger_readback)
assert json.loads((OUT/'summary.json').read_text())==summary
print(json.dumps({'output':str(OUT),'cells':len(ledger_readback),'counts':dict(counts),'correctionCandidates':sum(x['reviewDisposition']=='revise' for x in cross),'sha256Sums':str(OUT/'SHA256SUMS'),'readback':'pass','before':pre,'after':post},ensure_ascii=False,indent=2))
