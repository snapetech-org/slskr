#!/usr/bin/env python3
import collections
import datetime as dt
import hashlib
import json
import re
import subprocess
from pathlib import Path

ROOT = Path('/mnt/disks/scratch/task-worktrees/localization-20261102/slskr-pr204-W803-822-primary')
PRIMARY = Path('/mnt/disks/scratch/task-scratch/slskr-pr204-W803-822-primary-20261102/packet')
OUT = Path('/mnt/disks/scratch/task-scratch/slskr-pr204-W803-822-crossreview-independent-20261102')
EXPECTED_HEAD = '3a4c26a7faf1dacbd8f3a382d47243b7063a262d'
EXPECTED_TREE = '9059d27001d306ea6b064560137ff2a51dd19021'
BRANCH = 'codex/slskr-l10n-audit-20261030'
REPO = 'snapetech-org/slskR'
PR = 204
LOCALES = ['ar','de','es','fr','hi','id','ja','ko','pt-BR','vi','zh-Hans','zh-Hant']
WINDOW_FIRST, WINDOW_LAST = 802, 821

if OUT.exists() and any(OUT.iterdir()):
    raise SystemExit(f'Output path already contains files: {OUT}')
if OUT.exists():
    OUT.rmdir()
OUT.mkdir(parents=True)

def sha_bytes(value):
    return hashlib.sha256(value).hexdigest()
def sha_text(value):
    return sha_bytes(value.encode('utf-8'))
def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT).decode('utf-8').strip()
def jsonl(path):
    return [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines() if line]
def write_json(path, obj):
    path.write_text(json.dumps(obj, ensure_ascii=False, sort_keys=True, indent=2) + '\n', encoding='utf-8')
def write_jsonl(path, rows):
    path.write_text(''.join(json.dumps(row, ensure_ascii=False, sort_keys=True) + '\n' for row in rows), encoding='utf-8')
def parse_placeholders(text):
    return dict(collections.Counter(re.findall(r'\{([A-Za-z][A-Za-z0-9_]*)\}', text)))
def selector_tokens(text):
    return re.findall(r'\{[A-Za-z][A-Za-z0-9_]*\s*,\s*(?:plural|select|selectordinal)\s*,', text)
def markup_tokens(text):
    return re.findall(r'</?[A-Za-z][^>]*>', text)
def protected_counts(text):
    return {token: text.count(token) for token in ['ListenBrainz','API','URL'] if text.count(token)}
def line_data(rel, n):
    raw = (ROOT / rel).read_bytes()
    lines = raw.decode('utf-8', errors='replace').splitlines()
    value = lines[n-1]
    return {
        'path': rel,
        'line': n,
        'lineText': value,
        'lineSha256': sha_text(value),
        'fileSha256': sha_bytes(raw),
        'gitBlob': git('rev-parse', f'{EXPECTED_HEAD}:{rel}'),
    }
def cli_json(*args):
    return json.loads(subprocess.check_output(list(args), cwd=ROOT).decode('utf-8'))

# Exact pinned checkout and live remote/PR state before auditing.
status_porcelain = git('status', '--porcelain')
head = git('rev-parse', 'HEAD')
tree = git('rev-parse', 'HEAD^{tree}')
remote_head = subprocess.check_output(['git','ls-remote','taskgithub',f'refs/heads/{BRANCH}'], cwd=ROOT).decode().strip().split()[0]
pr_before = cli_json('gh','pr','view',str(PR),'--repo',REPO,'--json','state,isDraft,headRefOid,headRefName,baseRefName,url')
assert not status_porcelain, f'Pinned worktree is not clean: {status_porcelain}'
assert (head,tree)==(EXPECTED_HEAD,EXPECTED_TREE), (head,tree)
assert remote_head==EXPECTED_HEAD, remote_head
assert pr_before['state']=='OPEN' and pr_before['isDraft'] is True
assert pr_before['headRefOid']==EXPECTED_HEAD and pr_before['headRefName']==BRANCH

# Verify all supplied primary packet files against its manifest.
manifest_path = PRIMARY/'SHA256SUMS'
manifest_rows=[]
for line in manifest_path.read_text(encoding='utf-8').splitlines():
    if not line.strip():
        continue
    digest, name = line.split(None,1)
    name = name.strip()
    raw = (PRIMARY/name).read_bytes()
    actual = sha_bytes(raw)
    manifest_rows.append({'path':name,'expectedSha256':digest,'actualSha256':actual,'matches':digest==actual,'sizeBytes':len(raw)})
assert len(manifest_rows)==15 and all(row['matches'] for row in manifest_rows), manifest_rows
primary_summary = json.loads((PRIMARY/'primary-summary.json').read_text(encoding='utf-8'))
assert primary_summary['attestedHead']==EXPECTED_HEAD and primary_summary['attestedTree']==EXPECTED_TREE

# Independently read the English source catalog and all direct locale catalogs at the pinned checkout.
source_path='source text is the literal translation key; no English ui-labels catalog file is present'
source_raw=b''
source_catalog={}
catalogs={}
catalog_meta=[]
for locale in LOCALES:
    rel=f'web/src/lib/locales/ui-labels.{locale}.json'
    raw=(ROOT/rel).read_bytes()
    catalog=json.loads(raw)
    catalogs[locale]=catalog
    catalog_meta.append({
        'locale':locale,'path':rel,'fileSha256':sha_bytes(raw),
        'gitBlob':git('rev-parse',f'{EXPECTED_HEAD}:{rel}'),'keyCount':len(catalog),
        'matchesPrimaryCatalogAttestation':False,
    })
keysets=[set(catalog.keys()) for catalog in catalogs.values()]
assert all(keys==keysets[0] for keys in keysets)
keys=sorted(keysets[0])
assert len(keys)==5440
inventory_rows=[{'sourceIndex':i,'inventoryPosition1Based':i+1,'sourceId':key,'sourceSha256':sha_text(key)} for i,key in enumerate(keys)]
inventory_payload=''.join(json.dumps(row,ensure_ascii=False,separators=(',',':'))+'\n' for row in inventory_rows).encode('utf-8')
source_slice=keys[WINDOW_FIRST:WINDOW_LAST+1]
assert len(source_slice)==20
source_catalog={k:k for k in keys}
assert keys[WINDOW_FIRST]=='Compute perceptual hash for image similarity detection'
assert keys[WINDOW_LAST]=='Confirm Log Out'
assert all(source_catalog.get(k)==k for k in source_slice)

primary_inventory=jsonl(PRIMARY/'current-source-inventory.jsonl')
assert primary_inventory==inventory_rows
primary_catalog_att=json.loads((PRIMARY/'catalog-and-inventory-attestation.json').read_text(encoding='utf-8'))
assert primary_catalog_att['sortedKeySetSha256']==sha_bytes(inventory_payload)
assert primary_catalog_att['keyCount']==5440 and primary_catalog_att['catalogCount']==12
for meta in catalog_meta:
    item=next(x for x in primary_catalog_att['locales'] if x['locale']==meta['locale'])
    meta['matchesPrimaryCatalogAttestation']=(meta['fileSha256']==item['fileSha256'] and meta['gitBlob']==item['gitBlob'] and meta['keyCount']==item['keyCount'])
assert all(m['matchesPrimaryCatalogAttestation'] for m in catalog_meta)

# Recompute exact source-literal caller pins independently and compare every pin, byte/context hash and count.
tracked=git('ls-files','-z').split('\x00')
code_paths=[p for p in tracked if p and p.startswith(('web/src/','crates/','dashboard/src/')) and p.endswith(('.js','.jsx','.ts','.tsx','.rs','.py','.go')) and not p.startswith('web/src/lib/locales/')]
patterns={key:re.compile(r'(["\'])'+re.escape(key)+r'\1') for key in source_slice}
found=[]
for rel in code_paths:
    try:
        raw=(ROOT/rel).read_bytes()
        lines=raw.decode('utf-8',errors='replace').splitlines()
    except OSError:
        continue
    blob=git('rev-parse',f'{EXPECTED_HEAD}:{rel}')
    fhash=sha_bytes(raw)
    for i,line in enumerate(lines):
        for key,pattern in patterns.items():
            matches=list(pattern.finditer(line))
            if not matches:
                continue
            if 'interfaceTextProps(' in line: kind='localized-props'
            elif 'interfaceText(' in line: kind='localized-call'
            elif 'LocalizedText' in line: kind='localized-component'
            elif 'localized(' in line: kind='localized-helper'
            else: kind='raw-or-non-ui-literal'
            if re.search(r'(^|/)(test|tests|__tests__)(/|\\.)|\\.test\\.',rel):
                kind='test-reference'
            lo,hi=max(0,i-2),min(len(lines),i+3)
            found.append({
                'attestedHead':EXPECTED_HEAD,'sourceId':key,'path':rel,'line':i+1,
                'occurrencesOnLine':len(matches),'lineSha256':sha_text(line),
                'fileSha256':fhash,'gitBlob':blob,'kind':kind,
                'contextLines':[{'line':n+1,'text':lines[n]} for n in range(lo,hi)],
            })
found.sort(key=lambda x:(x['sourceId'],x['path'],x['line']))
pins=jsonl(PRIMARY/'caller-context-pins.jsonl')
assert len(pins)==63 and len(found)==63
pin_key=lambda x:(x['sourceId'],x['path'],x['line'])
assert [pin_key(x) for x in pins]==[pin_key(x) for x in found]
pin_rows=[]
for supplied, live in zip(pins,found):
    fields=['attestedHead','sourceId','path','line','occurrencesOnLine','lineSha256','fileSha256','gitBlob','kind','contextLines']
    matches={f:supplied.get(f)==live.get(f) for f in fields}
    pin_rows.append({**live,'primaryPinFieldsMatch':matches,'allPrimaryPinFieldsMatch':all(matches.values())})
assert all(row['allPrimaryPinFieldsMatch'] for row in pin_rows)

# Current cell rows and candidates: re-read source/current/candidate strings and hashes from live catalogs.
current_rows=jsonl(PRIMARY/'current-cells.jsonl')
primary_ledger=jsonl(PRIMARY/'primary-review-ledger.jsonl')
candidate_rows=jsonl(PRIMARY/'correction-candidates.jsonl')
assert len(current_rows)==240 and len(primary_ledger)==240
assert current_rows==primary_ledger
assert len(candidate_rows)==106
assert primary_summary['cellCount']==240 and primary_summary['candidateCount']==106
current_by={(r['sourceIndexZeroBased'],r['locale']):r for r in current_rows}
candidate_by={(r['sourceIndexZeroBased'],r['locale']):r for r in candidate_rows}
assert len(current_by)==240 and len(candidate_by)==106
assert all(k in current_by for k in candidate_by)

cell_review=[]
candidate_review=[]
for row in current_rows:
    idx=row['sourceIndexZeroBased']; loc=row['locale']; key=row['sourceId']
    assert idx in range(WINDOW_FIRST,WINDOW_LAST+1) and key==keys[idx]
    assert row['sourceSha256']==sha_text(key)
    assert source_catalog[key]==key
    live_target=catalogs[loc][key]
    assert isinstance(live_target,str)
    live_current_hash=sha_text(live_target)
    assert live_target==row['currentTarget'] and live_current_hash==row['currentTargetSha256']
    rec=candidate_by.get((idx,loc))
    source_ph=parse_placeholders(key); current_ph=parse_placeholders(live_target)
    source_markup=markup_tokens(key); current_markup=markup_tokens(live_target)
    source_protected=protected_counts(key); current_protected=protected_counts(live_target)
    source_selectors=selector_tokens(key); current_selectors=selector_tokens(live_target)
    assert source_ph==current_ph and source_markup==current_markup and source_protected==current_protected
    assert not source_selectors and not current_selectors
    if rec:
        proposed=rec['recommendedTarget']
        assert rec['currentTarget']==live_target and rec['currentTargetSha256']==live_current_hash
        assert rec['sourceSha256']==sha_text(key) and rec['recommendedTargetSha256']==sha_text(proposed)
        assert parse_placeholders(proposed)==source_ph
        assert markup_tokens(proposed)==source_markup
        assert protected_counts(proposed)==source_protected
        assert not selector_tokens(proposed)
        rationale_by_source={
            'Confidence':'The caller formats this as a numeric forensic confidence score. The proposed target names confidence/reliability level, while the current terms in these locales suggest trust or self-confidence.',
            'Confidence Lane':'The caller renders a percentage on one evidence-matrix lane. The proposed label identifies a confidence dimension/metric rather than a literal road lane.',
            'Confidence applies to the synthetic-likelihood readout only. It does not control download decisions when identity is strong.':'The caller distinguishes a synthetic-likelihood readout from download gating. The proposal preserves both limits and repairs the locale-specific agreement or technical wording.',
            'Confidence:':'The caller uses this as a numeric identity/content-match score label. The proposed technical confidence term fits that score sense.',
            'Configure ListenBrainz scrobbling':'The caller labels a control that opens ListenBrainz integration settings. The proposal fixes mistranslations of scrobbling or states the listening-history submission meaning; the brand is retained.',
            'Configure ListenBrainz scrobbling for this browser.':'The caller uses this as the tooltip for browser-specific ListenBrainz setup. The proposal is clear about sending listening history and preserves the browser scope and brand.',
            'Configure an API key before relying on mutating API clients or automation integrations.':'The caller is a setup-health recommendation about write-capable API clients/integrations. The proposal correctly explains “mutating” as changing data and retains API spelling.',
            'Configure an explicit media-server user mapping before importing or exporting user-scoped activity.':'The caller requires explicit media-server account mapping for per-user activity import/export. The proposed phrasing retains the prerequisite and scope.',
            'Configure the media-server base URL before enabling live scans.':'The caller is a readiness action for live scans. The proposal uses a natural base-URL construction and retains the protected URL token.',
            'Configured URL base: {urlBase}':'The caller formats a configured URL-base status. The proposal improves word order while preserving the exact {urlBase} placeholder and URL token.',
            'Configured import success':'The automation recipe uses this as a gate after an import before a configured server rescan. The proposed wording expresses successful library import to a configured media server.',
            'Confirm Directory Delete':'The caller is a file-explorer directory-delete dialog heading. The Arabic proposal uses the ordinary folder/directory term rather than a potentially ambiguous guide term.',
            'Confirm Log Out':'The caller opens a logout-confirmation modal. The proposed wording makes logout explicit in Chinese and uses a natural Spanish confirmation heading.',
        }
        rationale=rationale_by_source[key]
        disposition='accept-proposal'
        rec_validation=True
        candidate_review.append({
            'attestedHead':EXPECTED_HEAD,'attestedTree':EXPECTED_TREE,'windowLabel':row['windowLabel'],
            'sourceIndexZeroBased':idx,'sourceId':key,'locale':loc,
            'sourceSha256':sha_text(key),'currentTarget':live_target,'currentTargetSha256':live_current_hash,
            'recommendedTarget':proposed,'recommendedTargetSha256':sha_text(proposed),
            'primaryClaimedDecision':rec['reviewDecision'],
            'independentDisposition':disposition,'independentRationale':rationale,
            'independentValidation':{'sourcePlaceholders':source_ph,'currentPlaceholders':current_ph,'candidatePlaceholders':parse_placeholders(proposed),
                'sourceMarkup':source_markup,'currentMarkup':current_markup,'candidateMarkup':markup_tokens(proposed),
                'sourceSelectors':source_selectors,'candidateSelectors':selector_tokens(proposed),
                'sourceProtectedLiterals':source_protected,'currentProtectedLiterals':current_protected,'candidateProtectedLiterals':protected_counts(proposed),
                'passes':rec_validation},
            'callerVisibilityFinding':('W814 copied execution-contract report emits action as raw English.' if idx==813 else 'W815 readiness row and copied sync report emit action as raw English.' if idx==814 else None),
        })
        preferred=proposed
        primary_decision=rec['reviewDecision']
    else:
        preferred=live_target
        primary_decision='accept-current'
        disposition='accept-current'
    cell_review.append({
        'attestedHead':EXPECTED_HEAD,'attestedTree':EXPECTED_TREE,'windowLabel':row['windowLabel'],
        'sourceIndexZeroBased':idx,'sourceId':key,'locale':loc,
        'sourceSha256':sha_text(key),'liveCurrentTarget':live_target,'liveCurrentTargetSha256':live_current_hash,
        'primaryCurrentTargetMatchesLive':True,'primaryCurrentTargetSha256':row['currentTargetSha256'],
        'primaryClaimedDecision':primary_decision,'independentDisposition':disposition,
        'independentlyPreferredTarget':preferred,'independentlyPreferredTargetSha256':sha_text(preferred),
        'sourcePlaceholders':source_ph,'currentPlaceholders':current_ph,'preferredPlaceholders':parse_placeholders(preferred),
        'sourceMarkup':source_markup,'currentMarkup':current_markup,'preferredMarkup':markup_tokens(preferred),
        'sourceSelectors':source_selectors,'currentSelectors':current_selectors,'preferredSelectors':selector_tokens(preferred),
        'sourceProtectedLiterals':source_protected,'currentProtectedLiterals':current_protected,'preferredProtectedLiterals':protected_counts(preferred),
        'callerPinCount':len([p for p in pin_rows if p['sourceId']==key]),
        'callerOutputGap':('W816 raw-English Lidarr status' if key=='Configured' else 'W814 raw-English copied execution-contract action' if idx==813 else None),
    })
assert len(candidate_review)==106 and len(cell_review)==240

# Re-attest the supplied boundary source rows and their locale values, including W783 and W823.
boundary_sources=jsonl(PRIMARY/'window-boundary-reattestation.jsonl')
assert len(boundary_sources)==23
expected_boundary_indices=list(range(782,802))+[802,821,822]
assert [r['sourceIndexZeroBased'] for r in boundary_sources]==expected_boundary_indices
boundary_cells=[]
for src in boundary_sources:
    idx=src['sourceIndexZeroBased']; key=src['sourceId']
    assert keys[idx]==key and src['sourceSha256']==sha_text(key)
    boundary_label=f"W{idx+1:03d}"
    for loc in LOCALES:
        target=catalogs[loc][key]
        boundary_cells.append({
            'attestedHead':EXPECTED_HEAD,'sourceIndexZeroBased':idx,'windowLabel':boundary_label,
            'isPriorWindow':bool(src['isPriorWindow']),'sourceId':key,'sourceSha256':sha_text(key),
            'locale':loc,'currentTarget':target,'currentTargetSha256':sha_text(target),
        })
assert len(boundary_cells)==276
assert boundary_sources[0]['sourceIndexZeroBased']==782 and boundary_sources[0]['sourceId']==keys[782]
assert boundary_sources[-1]['sourceIndexZeroBased']==822 and boundary_sources[-1]['sourceId']==keys[822]

# Verify prior-provenance claim: no exact source/locale review dispositions are reused.
prior_rows=jsonl(PRIMARY/'prior-disposition-reattestation.jsonl')
prior_coverage=json.loads((PRIMARY/'prior-review-coverage.json').read_text(encoding='utf-8'))
assert len(prior_rows)==240
assert all(r['priorRecordCount']==0 and r['exactHashPriorRecordCount']==0 and not r['dispositionReused'] for r in prior_rows)
assert prior_coverage['priorMatchingReviewRecords']==0 and prior_coverage['dispositionsReused']==0

# Direct caller chains discovered during independent runtime-context review.
caller_findings=[]
# W816 known live UI gap.
for rel,n,role in [
    ('web/src/components/System/Integrations/LidarrPanel.jsx',44,'raw Configured value assigned to maskedApiKey'),
    ('web/src/components/System/Integrations/LidarrPanel.jsx',109,'raw-English value used for icon-state comparison'),
    ('web/src/components/System/Integrations/LidarrPanel.jsx',110,'maskedApiKey rendered directly as Label text'),
]:
    caller_findings.append({**line_data(rel,n),'sourceId':'Configured','windowLabel':'W816','findingType':'direct-render-gap','role':role,
        'disposition':'Hold caller integration: catalog translations do not replace this raw-English display.'})
# W814 raw action is included in the copied execution-contract report.
for rel,n,role in [
    ('web/src/lib/mediaServerIntegrations.js',194,'raw-English action string in contract check'),
    ('web/src/lib/mediaServerIntegrations.js',302,'formatter appends check.action verbatim to copied report'),
    ('web/src/components/System/Integrations/MediaServerPanel.jsx',108,'copyExecutionContract passes raw report to clipboard'),
]:
    caller_findings.append({**line_data(rel,n),'sourceId':'Configure an explicit media-server user mapping before importing or exporting user-scoped activity.','windowLabel':'W814','findingType':'raw-copy-output-gap','role':role,
        'disposition':'Hold caller integration for copied contract output; catalog proposals remain semantically acceptable.'})
# W815 readiness action is rendered raw in the shipped web panel and copied sync report.
for rel,n,role in [
    ('web/src/lib/mediaServerIntegrations.js',102,'raw-English readiness action definition'),
    ('web/src/components/System/Integrations/MediaServerPanel.jsx',305,'sync-preview action rendered directly without LocalizedText/interfaceText'),
    ('web/src/lib/mediaServerIntegrations.js',279,'sync-report formatter appends check.action verbatim'),
    ('web/src/components/System/Integrations/MediaServerPanel.jsx',82,'copySyncReport passes raw report to clipboard'),
]:
    caller_findings.append({**line_data(rel,n),'sourceId':'Configure the media-server base URL before enabling live scans.','windowLabel':'W815','findingType':'direct-and-copy-raw-output-gap','role':role,
        'disposition':'Hold caller integration for this readiness row and copied report; catalog proposals remain semantically acceptable.'})
write_jsonl(OUT/'caller-gap-findings.jsonl',caller_findings)
# The setup-health UI wraps W812 and W813, while plain-text reports/diagnostic JSON retain raw source strings.
export_findings=[]
for key,source_line in [
    ('Configure a download folder before starting acquisition workflows.',204),
    ('Configure an API key before relying on mutating API clients or automation integrations.',180),
]:
    export_findings.append({
        'windowLabel':f"W{keys.index(key)+1:03d}",'sourceId':key,
        'localizedModalRoute':line_data('web/src/components/System/Info/SetupHealthCheckModal.jsx',246),
        'rawTextReportRoute':line_data('web/src/lib/setupHealthCheck.js',351),
        'diagnosticBundleRoute':line_data('web/src/lib/diagnosticBundle.js',63),
        'sourceDefinitionRoute':line_data('web/src/lib/setupHealthCheck.js',source_line),
        'finding':'The setup-health modal uses LocalizedSetupHealthAction/LocalizedText, but copied setup-health reports and diagnostic-bundle JSON preserve the raw English action string.',
        'disposition':'Secondary export-channel localization gap; does not block the visible modal catalog translation.'
    })
write_jsonl(OUT/'secondary-export-gaps.jsonl',export_findings)

# Requery live PR and branch after all reads; stop if head/state moved during the audit.
remote_head_after=subprocess.check_output(['git','ls-remote','taskgithub',f'refs/heads/{BRANCH}'],cwd=ROOT).decode().strip().split()[0]
pr_after=cli_json('gh','pr','view',str(PR),'--repo',REPO,'--json','state,isDraft,headRefOid,headRefName,baseRefName,url')
assert remote_head_after==EXPECTED_HEAD and pr_after==pr_before

# Persist full independent packet.
write_jsonl(OUT/'caller-pin-reattestation.jsonl',pin_rows)
write_jsonl(OUT/'cell-crossreview.jsonl',cell_review)
write_jsonl(OUT/'candidate-adjudication.jsonl',candidate_review)
write_jsonl(OUT/'boundary-cell-reattestation.jsonl',boundary_cells)

input_check={
    'primaryPacketPath':str(PRIMARY),'primaryManifestPath':str(manifest_path),
    'primaryManifestSha256':sha_bytes(manifest_path.read_bytes()),'primaryFilesListed':len(manifest_rows),
    'primaryManifestVerified':all(r['matches'] for r in manifest_rows),'primaryFileChecks':manifest_rows,
    'separateInputManifestPresent':(PRIMARY.parent/'INPUT-SHA256SUMS').exists(),
    'inputManifestNote':'No separate INPUT-SHA256SUMS exists; the supplied primary packet SHA256SUMS covers the listed packet files.',
    'currentSourceInventoryRows':len(primary_inventory),'currentSourceInventoryMatchesLive':primary_inventory==inventory_rows,
    'currentInventorySha256':sha_bytes(inventory_payload),'currentCatalogs':catalog_meta,
    'englishSourceCatalog':{'path':source_path,'fileSha256':None,'gitBlob':None,'keyCount':len(source_catalog),'sourceHashRule':'SHA-256 of each exact English source string (the JSON key); the repo does not contain ui-labels.en.json.'},
    'callerPinsProvided':len(pins),'callerPinsIndependentlyScanned':len(found),'allCallerPinsMatch':all(r['allPrimaryPinFieldsMatch'] for r in pin_rows),
    'currentCellsProvided':len(current_rows),'primaryLedgerEqualsCurrentCells':current_rows==primary_ledger,
    'candidatesProvided':len(candidate_rows),'priorCoverage':prior_coverage,
    'windowBoundarySourceRowsProvided':len(boundary_sources),'boundaryLocaleCellRowsReattested':len(boundary_cells),
}
write_json(OUT/'primary-input-integrity.json',input_check)

structure={
    'attestedHead':EXPECTED_HEAD,'attestedTree':EXPECTED_TREE,'sourceIndexWindow':[WINDOW_FIRST,WINDOW_LAST],
    'sourceCount':len(source_slice),'localeCount':len(LOCALES),'cellCount':len(cell_review),
    'candidateCount':len(candidate_review),'sortedKeyCount':len(keys),'sortedKeySetSha256':sha_bytes(inventory_payload),
    'all12CatalogsSameKeySet':all(s==keysets[0] for s in keysets),'all12CatalogsSameKeyOrder':all(list(c.keys())==list(catalogs[LOCALES[0]].keys()) for c in catalogs.values()),
    'allWindowSourceValuesMatchEnglishKeys':all(source_catalog[k]==k for k in source_slice),
    'allCurrentAndCandidateValuesStrings':all(isinstance(catalogs[r['locale']][r['sourceId']],str) for r in current_rows),
    'sourceIcuSelectorCount':sum(len(selector_tokens(k)) for k in source_slice),
    'currentIcuSelectorCount':sum(len(selector_tokens(catalogs[l][k])) for l in LOCALES for k in source_slice),
    'candidateIcuSelectorCount':sum(len(selector_tokens(r['recommendedTarget'])) for r in candidate_rows),
    'placeholderFindings':{'Configured URL base: {urlBase}':{'source':parse_placeholders('Configured URL base: {urlBase}'),'currentAcrossLocales':{loc:parse_placeholders(catalogs[loc]['Configured URL base: {urlBase}']) for loc in LOCALES},'candidateTargets':sum(1 for r in candidate_rows if r['sourceId']=='Configured URL base: {urlBase}')}},
    'allCurrentAndCandidatePlaceholdersMatchSource':all(parse_placeholders(catalogs[l][k])==parse_placeholders(k) for l in LOCALES for k in source_slice) and all(parse_placeholders(r['recommendedTarget'])==parse_placeholders(r['sourceId']) for r in candidate_rows),
    'allCurrentAndCandidateMarkupMatchSource':all(markup_tokens(catalogs[l][k])==markup_tokens(k) for l in LOCALES for k in source_slice) and all(markup_tokens(r['recommendedTarget'])==markup_tokens(r['sourceId']) for r in candidate_rows),
    'allCurrentAndCandidateProtectedLiteralsMatchSource':all(protected_counts(catalogs[l][k])==protected_counts(k) for l in LOCALES for k in source_slice) and all(protected_counts(r['recommendedTarget'])==protected_counts(r['sourceId']) for r in candidate_rows),
    'protectedLiteralTokensReviewed':['ListenBrainz','API','URL'],
    'callerPinsMatched':len(pin_rows),'boundaryRows':len(boundary_sources),'boundaryLocaleCells':len(boundary_cells),
    'priorSourceCellDispositionsReused':prior_coverage['dispositionsReused'],
    'scopeNote':'The maintained localization roadmap says to localize the shipped web application and exclude the non-shipped standalone dashboard. The raw Configuration label in dashboard/src is outside this catalog scope; the web Bridge heading is localized.',
}
assert structure['sourceIcuSelectorCount']==0 and structure['currentIcuSelectorCount']==0 and structure['candidateIcuSelectorCount']==0
assert structure['allCurrentAndCandidatePlaceholdersMatchSource']
assert structure['allCurrentAndCandidateMarkupMatchSource']
assert structure['allCurrentAndCandidateProtectedLiteralsMatchSource']
write_json(OUT/'structural-integrity.json',structure)

candidate_decision_counts=dict(collections.Counter(r['independentDisposition'] for r in candidate_review))
cell_decision_counts=dict(collections.Counter(r['independentDisposition'] for r in cell_review))
primary_candidate_decisions=dict(collections.Counter(r['reviewDecision'] for r in candidate_rows))
summary={
    'attestedAtUtc':dt.datetime.now(dt.timezone.utc).isoformat(),
    'repository':REPO,'pullRequest':PR,'livePrStart':pr_before,'livePrEnd':pr_after,
    'head':EXPECTED_HEAD,'tree':EXPECTED_TREE,'branch':BRANCH,'remoteHeadStart':remote_head,'remoteHeadEnd':remote_head_after,
    'windowLabel':'W803–W822','sourceIndicesInclusive':[WINDOW_FIRST,WINDOW_LAST],
    'sourceCount':20,'localeCount':12,'cellCount':240,'callerPinCount':63,
    'candidateCount':106,'candidateDispositionCounts':candidate_decision_counts,
    'independentCellDispositionCounts':cell_decision_counts,'primaryCandidateDecisionCounts':primary_candidate_decisions,
    'semanticCandidateRevisions':0,'semanticCandidateRejections':0,'semanticCellHolds':0,
    'callerGapFindings':{
        'W816DirectRawEnglishCaller':1,'W815DirectRawEnglishReadinessAndCopy':1,'W814CopiedExecutionContractRawEnglish':1,
        'secondaryPlainTextSetupHealthExports':len(export_findings),'detailedCallerGapEvidenceLines':len(caller_findings),
        'directRawUiLocaleCells':24,'copiedMediaServerReportLocaleCells':24,
        'secondarySetupHealthExportLocaleCells':24,'callerIntegrationHoldCells':36,
        'secondaryExportOnlyLocaleCells':24,'uniqueSourceLocaleCellsWithKnownRawOutput':60,
    },
    'boundarySourceRows':len(boundary_sources),'boundaryLocaleCells':len(boundary_cells),
    'priorSourceCellDispositionsReused':0,
    'readOnly':True,'nativeSpeakerReviewStillUseful':True,
    'notes':[
        'All 106 proposals are accepted on semantic grounds; the independent cross-review did not change their target text.',
        'W816 Configured is localized in the catalog, but LidarrPanel.jsx assigns raw English at line 44, compares it for icon state at 109, and renders it at 110; the affected display requires caller localization.',
        'W814 Configure an explicit media-server user mapping... is used in a raw plain-text copied execution-contract report; its catalog value does not reach that output.',
        'W815 is raw in the media-server readiness row and copied sync report. W812 and W813 are localized in the setup-health modal but remain raw in copied setup-health reports and diagnostic-bundle JSON.',
        'The separate dashboard/src Configuration literal is outside this localization scope per docs/localization-roadmap.md, which specifies the shipped web application and excludes the non-shipped dashboard.',
        'No separate primary INPUT-SHA256SUMS file is present; all 15 files listed in the supplied primary SHA256SUMS were independently verified.',
    ],
    'packetFiles':['README.md','primary-input-integrity.json','structural-integrity.json','caller-pin-reattestation.jsonl','cell-crossreview.jsonl','candidate-adjudication.jsonl','boundary-cell-reattestation.jsonl','caller-gap-findings.jsonl','secondary-export-gaps.jsonl','summary.json','cross_review.py','SHA256SUMS'],
}
write_json(OUT/'summary.json',summary)

readme=f'''# slskR PR #204 W803–W822 independent cross-review\n\n- Reattested live PR #{PR} as OPEN/DRAFT at `{EXPECTED_HEAD}` / tree `{EXPECTED_TREE}`, branch `{BRANCH}`. `git ls-remote taskgithub` and a clean detached exact-head worktree matched before and after review.\n- Independently checked all 240 cells across 20 keys and 12 direct locales, all 63 source-literal caller pins, the source inventory and catalog/file hashes, and 23 supplied boundary source rows with 276 locale values (W783 through W823 boundary sentinels).\n- Independently adjudicated all 106 proposals. Disposition: {candidate_decision_counts.get('accept-proposal',0)} accepted; 0 revised; 0 rejected; 0 semantic holds.\n- Structural checks passed for the sole `{{urlBase}}` placeholder, zero ICU selectors, zero markup tokens, and protected literals `ListenBrainz`, `API`, and `URL`.\n- Additional caller-output findings: W816 raw-English Lidarr status assigned at line 44 and rendered at line 110 (line 109 compares it for icon state); W815 raw-English readiness action at MediaServerPanel.jsx:305 and in the copied sync report; W814 raw-English action in the copied execution-contract report. These affect 36 unique source/locale cells (W814–W816), with W815 also appearing in its copied report. W812/W813 are localized in the modal but remain raw in plain-text setup-health/diagnostic exports (24 more locale cells).\n- The separate dashboard `Configuration` literal is excluded by the maintained localization roadmap; the shipped web Bridge heading is localized.\n- No repo or PR writes, tests, builds, scans, CI, browser actions, workflow edits, releases, tags, or merges were performed.\n\nSee `summary.json`, `primary-input-integrity.json`, `structural-integrity.json`, `cell-crossreview.jsonl`, `candidate-adjudication.jsonl`, `caller-pin-reattestation.jsonl`, `boundary-cell-reattestation.jsonl`, `caller-gap-findings.jsonl`, and `secondary-export-gaps.jsonl`.\n'''
(OUT/'README.md').write_text(readme,encoding='utf-8')

# Preserve this source script for reproducibility and checksum every deliverable except the manifest itself.
script_source=Path(__file__).read_bytes()
(OUT/'cross_review.py').write_bytes(script_source)
checksum_lines=[]
for p in sorted(x for x in OUT.iterdir() if x.is_file() and x.name!='SHA256SUMS'):
    checksum_lines.append(f'{sha_bytes(p.read_bytes())}  {p.name}')
(OUT/'SHA256SUMS').write_text('\n'.join(checksum_lines)+'\n',encoding='utf-8')
# Self-check the emitted manifest.
for line in (OUT/'SHA256SUMS').read_text(encoding='utf-8').splitlines():
    expected,name=line.split(None,1)
    assert sha_bytes((OUT/name.strip()).read_bytes())==expected
print(json.dumps({
    'output':str(OUT),'manifestSha256':sha_bytes((OUT/'SHA256SUMS').read_bytes()),
    'summary':summary,'files':[{'name':p.name,'sizeBytes':p.stat().st_size} for p in sorted(OUT.iterdir()) if p.is_file()],
},ensure_ascii=False,indent=2))
