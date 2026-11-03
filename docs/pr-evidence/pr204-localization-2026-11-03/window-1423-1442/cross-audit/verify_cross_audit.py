#!/usr/bin/env python3
"""Portable checksum and semantic-integrity verifier for the W1423-W1442 cross-audit."""
import hashlib,json,re,subprocess,sys
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parent
HEAD='7ca8589266ab4c5a925782a8726d7e57b4ed7427'
TREE='09adcb271a2eb92770df4a20098dccc3fde2a59f'
def fail(message): raise SystemExit('FAIL: '+message)
def sha(data): return hashlib.sha256(data).hexdigest()
def j(path): return json.loads(path.read_text(encoding='utf-8'))
def jl(path): return [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines() if line.strip()]
def tokens(value):
    placeholders=re.findall(r'\{[A-Za-z][A-Za-z0-9_]*\}',value)
    markup=re.findall(r'<\/?[A-Za-z][^>]*>',value)
    numeric=re.findall(r'(?<![A-Za-z])\d+(?:[.,]\d+)?%?(?![A-Za-z])',value)
    protected=[]
    for match in re.finditer(r'(?<![A-Za-z0-9])(?:[A-Z]{2,}[A-Z0-9]*|ffmpeg|Chromaprint|Soulseek|Spotify|YouTube|Pushbullet|Matrix|WebSocket|OpenAI)(?![A-Za-z0-9])',value):
        if match.group(0) not in protected: protected.append(match.group(0))
    return {'placeholders':placeholders,'markup':markup,'numeric':numeric,'protectedLiterals':protected}
def verify_checksums(root,checksum_name):
    checksum=root/checksum_name
    if not checksum.is_file(): fail(str(checksum)+' missing')
    listed={}
    for line in checksum.read_text(encoding='utf-8').splitlines():
        if not line.strip(): continue
        parts=line.split('  ',1)
        if len(parts)!=2 or parts[1] in listed: fail('malformed or duplicate checksum in '+str(checksum))
        listed[parts[1]]=parts[0]
    for name,expected in listed.items():
        target=root/name
        if not target.is_file() or sha(target.read_bytes())!=expected: fail('checksum mismatch: '+str(target))
    actual={path.relative_to(root).as_posix() for path in root.rglob('*') if path.is_file() and path!=checksum}
    if set(listed)!=actual: fail('checksum file set mismatch under '+str(root))
    return listed

# Verify the portable packet seal and inventory.
listed=verify_checksums(ROOT,'SHA256SUMS.txt')
manifest=j(ROOT/'manifest.json')
manifest_paths={record['path'] for record in manifest['files']}
actual_manifest_paths={path.relative_to(ROOT).as_posix() for path in ROOT.rglob('*') if path.is_file() and path not in (ROOT/'manifest.json',ROOT/'SHA256SUMS.txt')}
if manifest_paths!=actual_manifest_paths: fail('manifest file inventory mismatch')
for record in manifest['files']:
    path=ROOT/record['path']
    if not path.is_file() or path.stat().st_size!=record['bytes'] or sha(path.read_bytes())!=record['sha256'] or listed.get(record['path'])!=record['sha256']:
        fail('output manifest mismatch: '+record['path'])
if manifest['pinnedHead']!=HEAD or manifest['pinnedTree']!=TREE: fail('manifest head/tree mismatch')

# Verify the copied candidate-free, primary, and blind evidence with their supplied verifiers.
evidence=ROOT/'evidence'
primary_bundle=evidence/'slskr-pr204-w1423-1442-primary-20261103'
cf=primary_bundle/'candidate-free-input'; pr=primary_bundle/'primary-review'
br=evidence/'slskr-pr204-w1423-1442-blind-review-20261103'
for folder,script in ((cf,'verify-candidate-free.py'),(pr,'verify_primary.py'),(br,'verify_review.py')):
    run=subprocess.run([sys.executable,script],cwd=folder,text=True,capture_output=True)
    if run.returncode: fail('input packet verifier failed for '+str(folder)+': '+run.stdout+run.stderr)

# Cross-check all 240 decisions against the exact input rows and recompute hashes/tokens.
C={(x['position'],x['locale']):x for x in jl(cf/'current-target-cells.jsonl')}
P={(x['position'],x['locale']):x for x in jl(pr/'cell-review.jsonl')}
B={(x['position'],x['locale']):x for x in jl(br/'review-ledger.jsonl')}
L=jl(ROOT/'cross-audit-ledger.jsonl')
if len(L)!=240 or len({(x['position'],x['locale']) for x in L})!=240: fail('ledger does not contain 240 unique cells')
if set(C)!=set(P) or set(C)!=set(B) or {(x['position'],x['locale']) for x in L}!=set(C): fail('input/ledger coverage mismatch')
D=Counter(); R=Counter(); S=Counter(); locale_counts={}
placeholder_occurrences=markup_occurrences=numeric_occurrences=protected_occurrences=0
for row in L:
    key=(row['position'],row['locale']); current=C[key]; primary=P[key]; blind=B[key]
    if (row['sourceKey'],row['sourceKeySha256'],row['currentTarget'],row['currentTargetSha256'],row['catalogPath'],row['catalogGitBlob'],row['catalogFileSha256'])!=(current['sourceKey'],current['sourceKeySha256'],current['currentTarget'],current['currentTargetSha256'],current['catalogPath'],current['catalogGitBlob'],current['catalogFileSha256']): fail('candidate-free row mismatch '+str(key))
    if row['callerContextSha256']!=current['sourceContextSha256'] or row['callerRefs']!=current['callerRefs']: fail('caller-context pin mismatch '+str(key))
    if row['sourceKeySha256']!=sha(row['sourceKey'].encode('utf-8')) or row['currentTargetSha256']!=sha(row['currentTarget'].encode('utf-8')): fail('source/current hash mismatch '+str(key))
    if row['primaryReview']['disposition']!=primary['disposition'] or row['primaryReview']['proposedTarget']!=primary.get('proposedTarget') or row['primaryReview']['proposedTargetSha256']!=primary.get('proposedTargetSha256'): fail('primary evidence mismatch '+str(key))
    if row['blindReview']['verdict']!=blind['verdict'] or row['blindReview']['suggestedTarget']!=blind.get('suggestedTarget') or row['blindReview']['suggestedTargetSha256']!=blind.get('suggestedTargetSha256'): fail('blind evidence mismatch '+str(key))
    if row['primaryReview']['proposedTarget'] and row['primaryReview']['proposedTargetSha256']!=sha(row['primaryReview']['proposedTarget'].encode('utf-8')): fail('primary suggestion hash mismatch '+str(key))
    if row['blindReview']['suggestedTarget'] and row['blindReview']['suggestedTargetSha256']!=sha(row['blindReview']['suggestedTarget'].encode('utf-8')): fail('blind suggestion hash mismatch '+str(key))
    if row['decision'] not in ('accept-current','correction','refinement','hold'): fail('invalid decision '+str(key))
    if row['decision']=='accept-current' and row['selectedTarget']!=current['currentTarget']: fail('accept-current changed its target '+str(key))
    if row['decision'] in ('correction','refinement') and row['selectedTarget']==current['currentTarget']: fail('change disposition kept current target '+str(key))
    if row['selectedTargetSha256']!=sha(row['selectedTarget'].encode('utf-8')): fail('selected target hash mismatch '+str(key))
    source_tokens=tokens(row['sourceKey']); current_tokens=tokens(row['currentTarget']); selected_tokens=tokens(row['selectedTarget'])
    checks=row['tokenAndProtectedLiteralChecks']
    if checks['source']!=source_tokens or checks['current']!=current_tokens or checks['selected']!=selected_tokens: fail('token evidence mismatch '+str(key))
    expected_checks={name:source_tokens[name]==selected_tokens[name] for name in source_tokens}
    if checks['selectedMatchesSource']!=expected_checks or not all(expected_checks.values()) or checks['allPass'] is not True: fail('selected token/protected-literal mismatch '+str(key))
    placeholder_occurrences+=len(source_tokens['placeholders']); markup_occurrences+=len(source_tokens['markup']); numeric_occurrences+=len(source_tokens['numeric']); protected_occurrences+=len(source_tokens['protectedLiterals'])
    if primary['disposition']=='accept-current' and blind['verdict']=='accept': relation='both-accept'
    elif primary['disposition']!='accept-current' and blind['verdict']!='accept': relation='both-propose-same-target' if primary.get('proposedTarget')==blind.get('suggestedTarget') else 'both-propose-different-targets'
    elif primary['disposition']!='accept-current': relation='primary-only-proposal'
    else: relation='blind-only-proposal'
    if row['primaryBlindReconciliation']!=relation: fail('reconciliation label mismatch '+str(key))
    if row['selectedTarget']==current['currentTarget']: source='current'
    elif primary.get('proposedTarget')==row['selectedTarget'] and blind.get('suggestedTarget')==row['selectedTarget']: source='primary+blind'
    elif primary.get('proposedTarget')==row['selectedTarget']: source='primary'
    elif blind.get('suggestedTarget')==row['selectedTarget']: source='blind'
    else: source='cross-audit'
    if row['selectedFrom']!=source: fail('selected-source label mismatch '+str(key))
    if not row['rationale'].strip() or row['confidence'] not in ('high','moderate','low','unknown'): fail('rationale/confidence missing '+str(key))
    D[row['decision']]+=1; R[relation]+=1; S[source]+=1; locale_counts.setdefault(row['locale'],Counter())[row['decision']]+=1
summary=j(ROOT/'summary.json')
if {name:D.get(name,0) for name in ('accept-current','correction','refinement','hold')}!=summary['decisionCounts']: fail('decision summary count mismatch')
if dict(R)!=summary['primaryBlindReconciliationCounts']: fail('reconciliation summary count mismatch')
if dict(S)!=summary['selectedTargetSourceCounts']: fail('selected-source summary mismatch')
if sum(D.values())!=240 or sum(R.values())!=240: fail('summary totals do not equal 240')
if summary['tokenAndProtectedLiteralChecks']['cellsChecked']!=240 or summary['tokenAndProtectedLiteralChecks']['cellsPassing']!=240: fail('token check coverage mismatch')
if summary['tokenAndProtectedLiteralChecks']['placeholderSourceOccurrences']!=placeholder_occurrences or summary['tokenAndProtectedLiteralChecks']['markupSourceOccurrences']!=markup_occurrences or summary['tokenAndProtectedLiteralChecks']['numericSourceOccurrences']!=numeric_occurrences or summary['tokenAndProtectedLiteralChecks']['protectedLiteralSourceOccurrences']!=protected_occurrences: fail('token occurrence summary mismatch')
if summary['tokenAndProtectedLiteralChecks']['selectedTargetMismatchCounts']!={'placeholders':0,'markup':0,'numeric':0,'protectedLiterals':0}: fail('token mismatch summary is not zero')

# Carried holds and prior selections are copied unchanged and independently counted.
prior_cf=jl(cf/'prior-hold-reattestation.jsonl'); prior_pr=jl(pr/'prior-hold-reattestation.jsonl'); prior_bl=jl(br/'prior-hold-reattestation.jsonl')
if len(prior_cf)!=35 or len(prior_pr)!=35 or len(prior_bl)!=35: fail('carried-hold count mismatch')
def keyed(rows): return {(x['position'],x['locale']):x for x in rows}
hcf,hpr,hbl=keyed(prior_cf),keyed(prior_pr),keyed(prior_bl)
if set(hcf)!=set(hpr) or set(hcf)!=set(hbl): fail('carried-hold keys differ')
for key,x in hcf.items():
    y=hpr[key]; z=hbl[key]
    hashes={x.get('currentTargetSha256'),x.get('priorCurrentTargetSha256'),y.get('currentTargetSha256'),y.get('priorCurrentTargetSha256'),z.get('recomputedCurrentTargetSha256'),z.get('priorCurrentTargetSha256')}
    hashes.discard(None)
    if len(hashes)!=1 or x.get('reattestation')!='same' or y.get('reattestation')!='same' or z.get('reattestation')!='same' or z.get('hashMatches') is not True: fail('carried-hold hash changed '+str(key))
for folder in (cf,pr):
    selection=jl(folder/'prior-selection-reattestation.jsonl')
    if len(selection)!=180: fail('prior selection reattestation count mismatch in '+str(folder))
    if not all(x.get('selectionMatchesCurrentQueue',True) for x in selection): fail('prior selected-source row drift in '+str(folder))

# Source/catalog files must match the GitHub tree at the exact pinned commit.
drift=j(ROOT/'pinned-source-tree-check.json')
if drift['commit']!=HEAD or drift['tree']!=TREE or drift['result']!='PASS' or drift.get('missingPaths') or drift.get('mismatchedPaths') or drift['checkedPathCount']!=34: fail('pinned source/catalog tree drift')
if len(drift['paths'])!=34 or not all(x['matches'] for x in drift['paths']): fail('pinned source-tree path mismatch')
pins=j(cf/'catalog-file-pins.json'); lineage=j(cf/'source-order-lineage.json'); expected_pins={}
for locale,item in pins['localeCatalogs'].items(): expected_pins[item['path']]={'blob':item['gitBlob'],'sha256':item['sha256'],'kind':'locale-catalog','locale':locale}
for item in pins['callerFiles'].values(): expected_pins[item['path']]={'blob':item['gitBlob'],'sha256':item['sha256'],'kind':'production-caller'}
item=pins['localeRuntime']; expected_pins[item['path']]={'blob':item['gitBlob'],'sha256':item['sha256'],'kind':'locale-runtime'}
expected_pins[lineage['currentHeadCommittedSourceQueuePath']]={'blob':lineage['currentHeadCommittedSourceQueueBlob'],'sha256':None,'kind':'committed-source-queue'}
recorded={item['path']:item for item in drift['paths']}
if set(recorded)!=set(expected_pins): fail('source-tree check path set differs from candidate-free pins')
for path,pin in expected_pins.items():
 item=recorded[path]
 if item.get('expectedGitBlob')!=pin['blob'] or item.get('pinnedSha256')!=pin['sha256'] or item.get('kind')!=pin['kind'] or item.get('locale')!=pin.get('locale'): fail('source-tree check pin differs from candidate-free packet: '+path)

# Live PR state and both refs were observed before and after the audit.
att=j(ROOT/'live-pr-attestation.json')
for stage in ('observedBefore','observedAfter'):
    obs=att.get(stage)
    if not obs: fail('missing live PR observation '+stage)
    prj=obs['pr']; refs=obs['refs']; tree=obs['commitTreeApi']
    if prj['state']!='OPEN' or prj['isDraft'] is not True or prj['headRefName']!='codex/slskr-l10n-audit-20261030' or prj['headRefOid']!=HEAD: fail('PR state/head mismatch '+stage)
    if refs.get('refs/heads/codex/slskr-l10n-audit-20261030')!=HEAD or refs.get('refs/pull/204/head')!=HEAD: fail('branch/pull ref mismatch '+stage)
    if tree.get('commit')!=HEAD or tree.get('tree')!=TREE: fail('commit tree mismatch '+stage)
if not att.get('baseRefDivergenceRecorded'): fail('base-ref divergence not recorded')
print(json.dumps({'result':'PASS','cells':240,'decisionCounts':summary['decisionCounts'],'reconciliationCounts':summary['primaryBlindReconciliationCounts'],'carriedHolds':35,'priorSelections':180,'tokenAndProtectedLiteralMismatches':0,'inputPacketVerifiers':'PASS','pinnedSourceCatalogTree':'PASS (34/34)','livePRBeforeAfter':'OPEN/DRAFT at pinned head/tree'},ensure_ascii=False,indent=2))
