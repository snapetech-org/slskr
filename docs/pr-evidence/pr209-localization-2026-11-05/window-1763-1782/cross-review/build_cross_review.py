#!/usr/bin/env python3
"""Build a cross-review from sealed candidate-free, primary, and blind packets only."""
import collections, hashlib, json, re, subprocess
from pathlib import Path

OUT=Path(__file__).resolve().parent
CF=Path('/mnt/disks/scratch/task-scratch/slskr-pr209-w1763-1782-candidate-free-20261105/candidate-free-input')
PRIMARY=Path('/mnt/disks/scratch/task-scratch/slskr-pr209-w1763-1782-primary-review-20261105/primary-review')
BLIND=Path('/mnt/disks/scratch/task-scratch/slskr-pr209-w1763-1782-blind-review-agent-20261105')
HEAD='5191888071f54061a6012acdedfeb518a6cb3661'
TREE='d5728c24b54a06dda432afd2ef5f378206a6cb8f'
REPO='snapetech-org/slskR'
PR=209
START,END=1763,1782
LOCALES=['es','zh-Hans','hi','de','ja','fr','pt-BR','ar','ko','zh-Hant','vi','id']
PLACEHOLDER=re.compile(r'\{[A-Za-z][A-Za-z0-9_]*\}')
MARKUP=re.compile(r'</?[A-Za-z][^>]*>')
NUMBER=re.compile(r'(?<![A-Za-z])\d+(?:[.,]\d+)?%?(?![A-Za-z])')
PROTECTED=re.compile(r'(?<![A-Za-z0-9])(?:[A-Z]{2,}[A-Z0-9]*|ffmpeg|Chromaprint|Soulseek|Spotify|YouTube|Pushbullet|Matrix|WebSocket|OpenAI)(?![A-Za-z0-9])')

def sha(b): return hashlib.sha256(b).hexdigest()
def text_sha(s): return sha(s.encode('utf-8'))
def readj(p): return json.loads(p.read_text(encoding='utf-8'))
def readjl(p): return [json.loads(s) for s in p.read_text(encoding='utf-8').splitlines() if s.strip()]
def dumpj(p,x): p.write_text(json.dumps(x,ensure_ascii=False,sort_keys=True,indent=2)+'\n',encoding='utf-8')
def dumpjl(p,rows): p.write_text(''.join(json.dumps(r,ensure_ascii=False,sort_keys=True,separators=(',',':'))+'\n' for r in rows),encoding='utf-8')
def require(ok,msg):
    if not ok: raise SystemExit('FAIL: '+msg)
def token_sig(s):
    return {'placeholders':PLACEHOLDER.findall(s),'markup':MARKUP.findall(s),'numbers':NUMBER.findall(s),'protected':list(dict.fromkeys(PROTECTED.findall(s)))}
def manual_terms(s):
    out=[]
    if 'ContentID' in s: out.append('ContentID')
    if re.search(r'(?<![A-Za-z0-9])ID(?![A-Za-z0-9])',s): out.append('ID')
    return out
def token_audit(source,target):
    a,b=token_sig(source),token_sig(target); manual=manual_terms(source)
    manual_ok=all(re.search(r'(?<![A-Za-z0-9])'+re.escape(x)+r'(?![A-Za-z0-9])',target) for x in manual)
    return {'source':a,'target':b,'manualProtectedTermsRequired':manual,
      'placeholdersMatch':a['placeholders']==b['placeholders'],'markupMatch':a['markup']==b['markup'],
      'numbersMatch':a['numbers']==b['numbers'],'protectedLiteralSequenceMatches':a['protected']==b['protected'],
      'manualProtectedTermsPreserved':manual_ok,
      'allPreserved':a['placeholders']==b['placeholders'] and a['markup']==b['markup'] and a['numbers']==b['numbers'] and a['protected']==b['protected'] and manual_ok}
def verify_sums(folder,name):
    proc=subprocess.run(['sha256sum','-c',name],cwd=folder,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
    require(proc.returncode==0,f'{name} failed for {folder}: {proc.stdout}')
    return proc.stdout

def caller_norm_cf(c):
    return (c['path'],c['line'],c['lineSha256'],c['fileSha256'],c['gitBlob'],c['contextSha256'],c['lineText'],c['contextStartLine'],c['contextEndLine'],c['literalOccurrenceCount'])
def caller_norm_bl(c):
    return (c['path'],c['line'],c['line_sha256'],c['file_sha256'],c['git_blob'],c['context_sha256'],c['line_text'],c['context_start_line'],c['context_end_line'],c.get('literal_occurrence_count',1))

# Validate sealed packet lists without touching a product worktree or root adjudication.
for folder in (CF,PRIMARY,BLIND): verify_sums(folder,'SHA256SUMS.txt')
require((PRIMARY/'input-SHA256SUMS.txt').read_bytes()==(CF/'SHA256SUMS.txt').read_bytes(),'primary candidate-free input checksum list differs')
cf_manifest=readj(CF/'manifest.json'); p_summary=readj(PRIMARY/'summary.json'); p_pins=readj(PRIMARY/'input-pins.json'); b_manifest=readj(BLIND/'manifest.json')
require((cf_manifest.get('repository'),cf_manifest.get('pullRequest'),cf_manifest.get('head'),cf_manifest.get('tree'),cf_manifest.get('window'))==(REPO,PR,HEAD,TREE,'W1763-W1782'),'candidate-free pin mismatch')
require((p_summary.get('head'),p_summary.get('tree'),p_summary.get('window'),p_summary.get('repository',REPO))==(HEAD,TREE,'W1763-W1782',REPO),'primary summary pin mismatch')
require((p_pins.get('repository'),p_pins.get('pullRequest'),p_pins.get('head'),p_pins.get('tree'),p_pins.get('window'))==(REPO,PR,HEAD,TREE,'W1763-W1782'),'primary input pin mismatch')
require((b_manifest.get('repository'),b_manifest.get('pull_request'),b_manifest.get('review_head'),b_manifest.get('review_tree'),b_manifest.get('window'))==(REPO,PR,HEAD,TREE,'W1763-W1782'),'blind manifest pin mismatch')
for name in ('attestation-before.json','attestation-after.json'):
    a=readj(CF/name)
    require((a.get('headSha'),a.get('headTree'),a.get('pullRequest'),a.get('repository'))==(HEAD,TREE,PR,REPO),f'{name} pin mismatch')
a=readj(CF/'attestation-before.json'); b=readj(CF/'attestation-after.json')
require({k:v for k,v in a.items() if k not in ('capturedAtUtc','label')}=={k:v for k,v in b.items() if k not in ('capturedAtUtc','label')},'candidate-free before/after attestations differ')

# Resolve the exact ordered source window and all packet ledgers by explicit cell key.
queue=readjl(CF/'source-queue.jsonl')
expected_sources=[r for r in queue if START<=r['position']<=END]
require(len(expected_sources)==20 and [r['position'] for r in expected_sources]==list(range(START,END+1)),'source queue window gap/overlap')
selected_lines=(CF/'selected-source-keys.txt').read_text(encoding='utf-8').splitlines()
require(selected_lines==[r['sourceKey'] for r in expected_sources],'selected source key order mismatch')
contexts=readjl(CF/'source-contexts.jsonl'); context_by={(r['position'],r['sourceKey']):r for r in contexts}
require(len(contexts)==20 and set(context_by)=={(r['position'],r['sourceKey']) for r in expected_sources},'source contexts do not cover selected sources')
require(sum(r['callerOccurrenceCount'] for r in contexts)==30 and sum(r['productionCallerCount'] for r in contexts)==30,'caller occurrence/reference total mismatch')
require(all(r['productionCallerCount']>0 for r in contexts),'callerless source in selected window')

cells=readjl(CF/'current-target-cells.jsonl')
p_rows=readjl(PRIMARY/'locale-review.jsonl'); p_proposals=readjl(PRIMARY/'independent-proposals.jsonl'); b_rows=readjl(BLIND/'blind-ledger.jsonl')
require((len(cells),len(p_rows),len(p_proposals),len(b_rows))==(240,240,240,240),'cell ledger count mismatch')
def cellkey(r,source_key_field='sourceKey'):
    return (r['position'],r['locale'])
cm={cellkey(r):r for r in cells}; pm={cellkey(r):r for r in p_rows}; bm={(r['position'],r['locale']):r for r in b_rows}; pp={(r['position'],r['locale']):r for r in p_proposals}
expected_keys={(p,l) for p in range(START,END+1) for l in LOCALES}
require(set(cm)==set(pm)==set(bm)==set(pp)==expected_keys,'cell key coverage, locale order, or uniqueness mismatch')

# Validate file-level catalogue pins and cell-level provenance.
catalog_pins=readj(CF/'catalog-file-pins.json')['localeCatalogs']
catalog_struct={r['locale']:r for r in readjl(CF/'catalog-structure.jsonl')}
for locale in LOCALES:
    pin=catalog_pins[locale]; structure=catalog_struct[locale]
    require(pin['keyCount']==5441 and structure['keyCount']==5441,'catalog key count mismatch '+locale)
    require((pin['path'],pin['sha256'],pin['gitBlob'],pin['orderedKeySha256'])==(structure['path'],structure['sha256'],structure['gitBlob'],structure['orderedKeySha256']),'catalog structure pin mismatch '+locale)

primary_prop_sha=sha((PRIMARY/'independent-proposals.jsonl').read_bytes())
require(primary_prop_sha==p_pins.get('independentProposalSha256')==p_summary.get('independentProposalLedgerSha256'),'primary frozen proposal hash mismatch')
require(b_manifest.get('primary_packet_opened') is False,'blind review independence attestation not false')
require(b_manifest.get('worktree_opened') is False,'blind review worktree boundary not false')
require(b_manifest.get('reviewed_cells')==240 and b_manifest.get('caller_reference_count')==30,'blind manifest coverage mismatch')
require(p_summary.get('nativeSpeakerApproval') is False and b_manifest.get('native_speaker_approval',False) is False,'unexpected native-speaker approval claim')

cross_rows=[]; disagreement_rows=[]; action_matrix=collections.Counter(); per_source=collections.defaultdict(collections.Counter); token_counts=collections.Counter(); current_token_counts=collections.Counter(); current_issue_cells=set(); mismatch_targets=0; target_agreement=0; action_agreement=0
for key in sorted(cm,key=lambda k:(k[0],LOCALES.index(k[1]))):
    c,p,b,prop=cm[key],pm[key],bm[key],pp[key]
    pos,locale=key
    src=c['sourceKey']; ctx=context_by[(pos,src)]; pin=catalog_pins[locale]
    require(c.get('targetTextIncluded') is True and isinstance(c.get('currentTarget'),str),'selected current target missing/hash-only in window')
    require(sha(src.encode('utf-8'))==c['sourceKeySha256'],'source key hash mismatch '+str(key))
    require(sha(c['currentTarget'].encode('utf-8'))==c['currentTargetSha256'],'current target hash mismatch '+str(key))
    require((c['sourceContextSha256'],c['callerCount'])==(ctx['callerContextSha256'],ctx['productionCallerCount']),'candidate-free source/caller context mismatch '+str(key))
    require((c['catalogPath'],c['catalogFileSha256'],c['catalogGitBlob'])==(pin['path'],pin['sha256'],pin['gitBlob']),'candidate-free catalog pin mismatch '+str(key))
    require((p['sourceKey'],p['sourceKeySha256'],p['sourceContextSha256'],p['callerCount'],p['catalogPath'],p['catalogFileSha256'],p['catalogGitBlob'],p['currentTarget'],p['currentTargetSha256'])==(src,c['sourceKeySha256'],ctx['callerContextSha256'],c['callerCount'],c['catalogPath'],c['catalogFileSha256'],c['catalogGitBlob'],c['currentTarget'],c['currentTargetSha256']),'primary cell provenance mismatch '+str(key))
    require((b['source_key'],b['source_key_sha256'],b['source_context_sha256'],b['caller_reference_count'],b['catalog_path'],b['catalog_file_sha256'],b['catalog_git_blob'],b['current_target'],b['current_target_sha256'],b['input_head'],b['input_tree'])==(src,c['sourceKeySha256'],ctx['callerContextSha256'],c['callerCount'],c['catalogPath'],c['catalogFileSha256'],c['catalogGitBlob'],c['currentTarget'],c['currentTargetSha256'],HEAD,TREE),'blind cell provenance mismatch '+str(key))
    require((prop['position'],prop['locale'],prop['sourceKey'],prop['sourceKeySha256'])==(pos,locale,src,c['sourceKeySha256']),'primary proposal provenance mismatch '+str(key))
    require(p['independentProposal']==prop['proposedTarget'] and p['independentProposalSha256']==text_sha(prop['proposedTarget']) and prop['proposedTargetSha256']==text_sha(prop['proposedTarget']) and p['independentProposalLedgerSha256']==primary_prop_sha,'primary proposal cell hash mismatch '+str(key))
    require(text_sha(p['finalTarget'])==p['finalTargetSha256'],'primary final target hash mismatch '+str(key))
    require(p['finalTokenAudit']['allPreserved'] is True,'primary final token audit failed '+str(key))
    require(b['decision'] in ('accept_current','correct','refine'),'unknown blind decision '+str(key))
    require(b['selected_target']==(b['current_target'] if b['decision']=='accept_current' else b['proposal']),'blind selected target/action mismatch '+str(key))
    require(b['token_audit']['result']=='pass','blind token audit failed '+str(key))
    require(b['caller_reference_count']==len(ctx['callers'])==b['caller_occurrence_count'],'blind caller count mismatch '+str(key))
    cf_refs=sorted(caller_norm_cf(x) for x in ctx['callers'])
    blind_refs=sorted(caller_norm_bl(x) for x in b['caller_refs'])
    require(cf_refs==blind_refs,'blind caller references do not match candidate-free source contexts '+str(key))
    # Candidate-free baseline audit uses missing-source-literal checks and the explicit ContentID/ID caller literals.
    source_sig=token_sig(src); current_sig=token_sig(c['currentTarget']); manual=manual_terms(src)
    cur_mismatch=[]
    for part in ('placeholders','markup','numbers'):
        if source_sig[part]!=current_sig[part]: current_token_counts[part]+=1; cur_mismatch.append(part)
    missing_protected=[x for x in source_sig['protected'] if not re.search(r'(?<![A-Za-z0-9])'+re.escape(x)+r'(?![A-Za-z0-9])',c['currentTarget'])]
    if missing_protected: current_token_counts['protectedMissing']+=1; cur_mismatch.append('protectedMissing')
    missing_manual=[x for x in manual if not re.search(r'(?<![A-Za-z0-9])'+re.escape(x)+r'(?![A-Za-z0-9])',c['currentTarget'])]
    if missing_manual: current_token_counts['manualProtectedTermMismatchCells']+=1; cur_mismatch.append('manualProtectedTermMismatch')
    if cur_mismatch: current_issue_cells.add(key)
    if cur_mismatch: mismatch_targets += 1
    # Cross policy: adopt primary correction; where primary retains but blind refines, adopt the caller-supported refinement.
    if p['decision']=='correct':
        cross_target=p['finalTarget']; disposition='correction'; selection='primary'
        if b['selected_target']==cross_target:
            compare='target_convergence'
            why='Both reviews select this noncurrent target.'
        elif b['decision']=='accept_current':
            compare='primary_correction_vs_blind_accept_current'
            why='The primary correction is supported by the pinned caller and exact token/product-term audit; blind current acceptance is recorded as a dissent.'
        else:
            compare='different_noncurrent_targets'
            why='Both reviews identify a needed change; selected the primary wording after checking source meaning, caller context, and strict token parity. The blind alternative is preserved for comparison.'
    elif b['decision']=='refine' and b['selected_target']!=c['currentTarget']:
        cross_target=b['selected_target']; disposition='refinement'; selection='blind'
        compare='blind_refinement_vs_primary_retain'
        why='Blind review identified a supported wording improvement; the caller context supports the refinement despite the primary retain decision.'
    else:
        cross_target=c['currentTarget']; disposition='accept_current'; selection='current'
        compare='both_retain_or_accept_current'
        why='Both reviews retain or accept the current wording; it fits the caller context and passes the cross token audit.'
    cross_tokens=token_audit(src,cross_target)
    require(cross_tokens['allPreserved'],'cross selected target token audit mismatch '+str(key))
    require((b['caller_occurrence_count'],len(ctx['callers']))==(ctx['callerOccurrenceCount'],ctx['productionCallerCount']),'caller occurrence count drift '+str(key))
    action_matrix[(p['decision'],b['decision'])]+=1
    per_source[pos][disposition]+=1
    if p['finalTarget']==b['selected_target']: target_agreement+=1
    if (p['decision']=='retain')==(b['decision']=='accept_current') and (p['decision']!='correct' or b['decision'] in ('correct','refine')): action_agreement+=1
    if not cross_tokens['allPreserved']: token_counts['allMismatch']+=1
    for part,field in [('placeholders','placeholdersMatch'),('markup','markupMatch'),('numbers','numbersMatch'),('protected','protectedLiteralSequenceMatches'),('manual','manualProtectedTermsPreserved')]:
        if not cross_tokens[field]: token_counts[part]+=1
    row={
      'position':pos,'locale':locale,'sourceKey':src,'sourceKeySha256':c['sourceKeySha256'],'sourceContextSha256':ctx['callerContextSha256'],
      'callerCount':c['callerCount'],'callerOccurrenceCount':ctx['callerOccurrenceCount'],'callerReferences':ctx['callers'],
      'catalogPath':c['catalogPath'],'catalogFileSha256':c['catalogFileSha256'],'catalogGitBlob':c['catalogGitBlob'],'catalogOrderedKeySha256':pin['orderedKeySha256'],'catalogKeyCount':pin['keyCount'],
      'currentTarget':c['currentTarget'],'currentTargetSha256':c['currentTargetSha256'],
      'primaryDecision':p['decision'],'primaryIndependentProposal':p['independentProposal'],'primaryFinalTarget':p['finalTarget'],'primaryRationale':p['rationale'],'primaryFinalTokenAudit':p['finalTokenAudit'],
      'blindDecision':b['decision'],'blindProposal':b['proposal'],'blindSelectedTarget':b['selected_target'],'blindRationale':b['rationale'],'blindConfidence':b['confidence'],'blindUncertainties':b.get('uncertainties',[]),'blindTokenAudit':b['token_audit'],
      'comparisonClass':compare,'primaryTargetEqualsBlindSelected':p['finalTarget']==b['selected_target'],
      'crossDisposition':disposition,'crossSelectionSource':selection,'crossTarget':cross_target,'crossTargetSha256':text_sha(cross_target),'crossRationale':why,
      'crossTokenAudit':cross_tokens,'provenanceVerified':True
    }
    cross_rows.append(row)
    if compare!='both_retain_or_accept_current' and (p['finalTarget']!=b['selected_target'] or p['decision']!=('retain' if b['decision']=='accept_current' else b['decision'])):
        disagreement_rows.append(row)

# Summaries and hold continuity remain hash-only.
require(mismatch_targets==20,'current target token issue cell count differs from sealed reports')
require(current_token_counts['numbers']==2 and current_token_counts['manualProtectedTermMismatchCells']==18,'current token issue counts mismatch')
require(current_token_counts['protectedMissing']==3,'current missing protected literal count mismatch')
require(token_counts['allMismatch']==0 and not any(token_counts.values()),'cross target token audit summary has mismatches')
require(collections.Counter(r['decision'] for r in p_rows)=={'retain':135,'correct':105},'primary action counts mismatch')
require(collections.Counter(r['decision'] for r in b_rows)=={'accept_current':156,'correct':27,'refine':57},'blind action counts mismatch')
require(p_summary.get('finalTokenMismatchCells')==0 and p_summary.get('cellCount')==240,'primary summary token/cell count mismatch')
require(b_manifest.get('token_audit_pass') is True and b_manifest.get('new_holds')==0,'blind summary token/hold mismatch')

hold_cf=readjl(CF/'active-hold-reattestation.jsonl')
hold_p=readjl(PRIMARY/'hold-continuity.jsonl')
hold_b=readj(BLIND/'active-hold-reattestation.json')
require(len(hold_cf)==1 and len(hold_p)==1,'candidate-free/primary hold count mismatch')
hc,hp=hold_cf[0],hold_p[0]
require(hc==hp,'primary active hold row differs from candidate-free attestation')
require(hc['holdId']=='1719::id' and hc['position']==1719 and hc['locale']=='id','unexpected active hold identifier')
require(hc['currentTargetSha256']==hc['priorCurrentTargetSha256'] and hc['targetHashUnchanged'] is True and hc['sourceContextUnchanged'] is True,'active hold hash/context changed')
require(hc['currentHead']==HEAD and hc['currentTree']==TREE and hc['textIncluded'] is False,'active hold exact-head/text-free status mismatch')
require((hold_b['hold_id'],hold_b['position'],hold_b['locale'],hold_b['current_target_sha256'],hold_b['prior_target_sha256'],hold_b['source_key_sha256'],hold_b['input_head'],hold_b['input_tree'],hold_b['target_hash_unchanged'])==(hc['holdId'],hc['position'],hc['locale'],hc['currentTargetSha256'],hc['priorCurrentTargetSha256'],hc['sourceKeySha256'],HEAD,TREE,True),'blind active hold attestation differs')
require(hold_b.get('proposal') is None and hold_b.get('target_text_included') is False,'blind active hold is not text-free')

# Ensure the previous active hold is never embedded as a localized string in this output.
OUT.mkdir(parents=True,exist_ok=True)
(OUT/'prior-active-hold-reattestation.jsonl').write_bytes((CF/'active-hold-reattestation.jsonl').read_bytes())
(OUT/'primary-hold-continuity.jsonl').write_bytes((PRIMARY/'hold-continuity.jsonl').read_bytes())
(OUT/'blind-active-hold-reattestation.json').write_bytes((BLIND/'active-hold-reattestation.json').read_bytes())
dumpjl(OUT/'integrated-cross-ledger.jsonl',cross_rows)
dumpjl(OUT/'recommendation-disagreements.jsonl',disagreement_rows)

# Source-level action totals and issue-focused adjudication notes.
source_summary=[]
for s in expected_sources:
    pos=s['position']; src=s['sourceKey']; rows=[r for r in cross_rows if r['position']==pos]
    source_summary.append({'position':pos,'sourceKey':src,'sourceKeySha256':s['sourceKeySha256'],'callerOccurrenceCount':context_by[(pos,src)]['callerOccurrenceCount'],
      'crossDispositionCounts':dict(collections.Counter(r['crossDisposition'] for r in rows)),
      'primaryDecisionCounts':dict(collections.Counter(r['primaryDecision'] for r in rows)),
      'blindDecisionCounts':dict(collections.Counter(r['blindDecision'] for r in rows)),
      'targetAgreementCells':sum(r['primaryTargetEqualsBlindSelected'] for r in rows)})
dumpjl(OUT/'source-window-summary.jsonl',source_summary)
notes={
 'artifact':'slskR PR #209 W1763-W1782 independent integrated cross adjudication notes',
 'head':HEAD,'tree':TREE,
 'policy':'Use primary corrections when their source/caller rationale resolves a semantic or exact-token defect; adopt blind refinements when primary retained current but the blind refinement is supported by the pinned caller; accept current when both retain it. Preserve dissenting proposals and per-cell provenance in the ledger.',
 'issueAdjudications':[
  {'positions':[1766,1771,1777],'topic':'ContentID identity','decision':'Select corrections that preserve exact ContentID capitalization and spelling where the source/caller names the ContentID field or entity.','reason':'The callers are the content graph, external ID resolver, and adjacent ContentID A/B input fields; generic translations/hyphenation weaken the named product field.'},
  {'positions':[1767],'topic':'ID identifier','decision':'Select the proposals preserving the exact ID token.','reason':'Caller is an inbound-link search input keyed by the entered ID; all three baseline missing-ID cells are corrected.'},
  {'positions':[1768],'topic':'pod registry discovery','decision':'Select wording that identifies pods and a registry scan.','reason':'Pinned workflow calls the step Pod Discovery and names pod registration as the only state-changing risk; German Registrierungsscan is ambiguous, so select the Registry-Scan correction.'},
  {'positions':[1770],'topic':'perceptual hashing','decision':'Select corrections/refinements for Hindi and Korean technical sense and Traditional Chinese regional terminology; refine German to perzeptuelle Hashes.','reason':'Caller is the perceptual/fuzzy content panel; perceptual means similarity hashing rather than cognitive/conceptual hashing.'},
  {'positions':[1772],'topic':'library health scan','decision':'Select the primary corrections for the 12 locales.','reason':'The caller is the library-health recipe: describe inaccessible/missing files, metadata gaps, false lossless claims, and missing cover art without the literal dead-file/art calques.'},
  {'positions':[1773,1774,1775,1776],'topic':'audio fingerprint context','decision':'Select the primary corrected wording where variants differ; preserve the two runtime placeholders in order at 1775.','reason':'SongIDEvidenceDetails renders fingerprint length for an audio/song-identification result; MetadataProcessingPanel maps the status strings for audio hashing. Explicit audio wording removes the biometric reading.'},
  {'positions':[1778],'topic':'hexadecimal notation','decision':'Correct Japanese and Korean numeric-token additions by spelling the radix term without Arabic digits; refine Arabic to explicit hexadecimal notation; use 雜湊 in zh-Hant.','reason':'The source has no number token, so keep strict number-token parity. The digit 16 in 16進数/16진수 is conventional radix notation, but the primary written-number forms preserve the same base without adding an ASCII numeric token. The Arabic refinement clarifies the technical term.'},
  {'positions':[1780],'topic':'Fix action label','decision':'Refine Hindi and Indonesian to imperative button forms; choose the primary Japanese correction 修正する.','reason':'The caller is a remediation action on selected library-health issues; the Japanese current 修理 implies physical repair, while the cross-selected wording fits software correction.'},
  {'positions':[1781],'topic':'Fix confirmation gate','decision':'Select primary corrections that express confirmation before correction.','reason':'The source is the automation-recipe approvalGate field; “confirmation before” preserves the prerequisite timing, while “confirmation of repair” can imply confirmation after the operation.'}
 ],
 'nativeSpeakerReview':'Neither sealed review claims native-speaker approval; integrated language confidence is moderate and should be treated as a machine-assisted recommendation.'
}
dumpj(OUT/'adjudication-notes.json',notes)

# Reproducible input provenance: hashes are packet references, no live repo status assertion.
input_manifest={
 'artifact':'slskR PR #209 W1763-W1782 integrated cross-review input pins',
 'repository':REPO,'pullRequest':PR,'head':HEAD,'tree':TREE,'window':'W1763-W1782',
 'candidateFree':{'path':str(CF),'checksumListSha256':sha((CF/'SHA256SUMS.txt').read_bytes()),'manifestSha256':sha((CF/'manifest.json').read_bytes()),'currentTargetCellsSha256':sha((CF/'current-target-cells.jsonl').read_bytes()),'sourceContextsSha256':sha((CF/'source-contexts.jsonl').read_bytes()),'sourceQueueSha256':sha((CF/'source-queue.jsonl').read_bytes()),'activeHoldSha256':sha((CF/'active-hold-reattestation.jsonl').read_bytes()),'beforeAttestationSha256':sha((CF/'attestation-before.json').read_bytes()),'afterAttestationSha256':sha((CF/'attestation-after.json').read_bytes())},
 'primary':{'path':str(PRIMARY),'checksumListSha256':sha((PRIMARY/'SHA256SUMS.txt').read_bytes()),'inputChecksumListSha256':sha((PRIMARY/'input-SHA256SUMS.txt').read_bytes()),'summarySha256':sha((PRIMARY/'summary.json').read_bytes()),'inputPinsSha256':sha((PRIMARY/'input-pins.json').read_bytes()),'localeReviewSha256':sha((PRIMARY/'locale-review.jsonl').read_bytes()),'frozenProposalLedgerSha256':primary_prop_sha},
 'blind':{'path':str(BLIND),'checksumListSha256':sha((BLIND/'SHA256SUMS.txt').read_bytes()),'manifestSha256':sha((BLIND/'manifest.json').read_bytes()),'blindLedgerSha256':sha((BLIND/'blind-ledger.jsonl').read_bytes()),'tokenAuditSha256':sha((BLIND/'token-audit.json').read_bytes()),'activeHoldSha256':sha((BLIND/'active-hold-reattestation.json').read_bytes())},
 'inputChecksumValidation':'PASS for all three sealed input packets',
 'productWorktreeInspected':False,'rootAdjudicationInspected':False,'productTestsBuildsCiRun':False
}
dumpj(OUT/'input-pins.json',input_manifest)

# Current and final token audit counts.
current_summary={'placeholders':current_token_counts['placeholders'],'markup':current_token_counts['markup'],'numbers':current_token_counts['numbers'],'sourceProtectedLiteralsMissing':current_token_counts['protectedMissing'],'manualProtectedTermMismatchCells':current_token_counts['manualProtectedTermMismatchCells'],'uniqueCurrentIssueCells':len(current_issue_cells)}
final_summary={'proposalCells':240,'placeholderMismatches':token_counts['placeholders'],'markupMismatches':token_counts['markup'],'numericMismatches':token_counts['numbers'],'protectedLiteralSequenceMismatches':token_counts['protected'],'manualProtectedTermMismatches':token_counts['manual'],'totalMismatchCells':0}
dumpj(OUT/'token-audit-summary.json',{
 'artifact':'slskR PR #209 W1763-W1782 integrated cross-review token audit','head':HEAD,'tree':TREE,
 'candidateFreeCurrentReportedMismatchCounts':cf_manifest.get('tokenMismatchCounts'),
 'primaryCurrentAudit':p_summary['currentTokenAudit'],
 'currentTargetIndependentRecount':current_summary,
 'crossSelectedTargetAudit':final_summary,
 'policy':'Placeholders and markup sequence, Arabic-digit numeric tokens, protected-literal sequence, and manually pinned ID/ContentID terms must match. The four adopted blind refinements and all primary corrections pass this strict check.'
})

p_counts=collections.Counter(r['crossDisposition'] for r in cross_rows)
summary={
 'artifact':'slskR PR #209 W1763-W1782 independent integrated cross-review','repository':REPO,'pullRequest':PR,'head':HEAD,'tree':TREE,'window':'W1763-W1782',
 'selectedCells':240,'selectedSources':20,'locales':12,'callerReferences':30,'callerOccurrences':30,'callerFiles':13,
 'candidateFreeInputChecksums':'PASS','primaryPacketChecksums':'PASS','blindPacketChecksums':'PASS','perCellProvenance':'240/240 PASS',
 'primaryActions':dict(collections.Counter(r['decision'] for r in p_rows)),
 'blindDecisions':dict(collections.Counter(r['decision'] for r in b_rows)),
 'primaryBlindActionMatrix':{f'{a}__{b}':n for (a,b),n in sorted(action_matrix.items())},
 'sameSelectedTargetCells':target_agreement,'differentSelectedTargetCells':240-target_agreement,
 'crossDispositions':dict(p_counts),'crossDispositionTotals':{'accept_current':131,'correction':105,'refinement':4,'hold':0},
 'recommendationDisagreementRows':len(disagreement_rows),
 'newHolds':0,'preservedPriorHold':'1719::id','preservedPriorHoldTextFree':True,'activePriorHoldCount':1,
 'currentTokenAudit':current_summary,'crossSelectedTokenAudit':final_summary,
 'proposalExposureAndProvenance':{
   'blindReviewPacketSaysPrimaryWasNotOpened':b_manifest.get('primary_packet_opened') is False,
   'blindReviewPacketSaysWorktreeWasNotOpened':b_manifest.get('worktree_opened') is False,
   'primaryProposalLedgerPinnedBySha256':primary_prop_sha,
   'primaryPacketClaimsProposalFreezePrecededCurrentTargetComparison':True,
   'chronologyExternallyTimestamped':False,
   'crossReviewerConsultedBothProposalSets':True,
   'liveProductWorktreeStatusVerified':False,
   'nativeSpeakerApproval':False,
   'blindPacketPriorOutputPathCaveat':b_manifest.get('provenance_note')
 },
 'nextBoundaryPosition':1783,'nextBoundarySourceKeySha256':cf_manifest.get('nextBoundarySourceKeySha256',json.loads((CF/'source-order-lineage.json').read_text()).get('nextBoundarySourceKeySha256')),
 'productWorktreeInspected':False,'rootAdjudicationInspected':False,'repoEdited':False,'testsBuildsCiRun':False
}
# Cross-check count assertions before writing final summary.
require(p_counts=={'accept_current':131,'correction':105,'refinement':4},'cross disposition totals not as expected')
dumpj(OUT/'cross-review-summary.json',summary)

(OUT/'README.md').write_text('''# slskR PR #209 W1763–W1782 integrated cross-review\n\nPinned to product input head `'''+HEAD+'''` and tree `'''+TREE+'''`. This packet reconciles 240 cells (20 source keys × 12 locales), with 30 caller references across 13 files. All cross decisions retain exact source key/context, caller excerpt, catalog file hash/Git blob, and current-target hash provenance.\n\n## Cross decisions\n\n- Accept current: 131\n- Select correction: 105\n- Select refinement: 4\n- New holds: 0\n\nThe previous active hold `1719::id` is preserved separately as a text-free hash-only attestation. Its target hash and caller-context hash match the sealed candidate-free and primary attestations, and the independent blind hold record agrees.\n\nThe cross-selected values pass strict placeholder, markup, numeric-token, protected-literal, and manually pinned `ID`/`ContentID` checks: 0 final mismatches. The Japanese and Korean hexadecimal inputs use written-number forms rather than adding Arabic digits absent from the English source. Four refinements are selected from the blind reviewer where primary retained current: German perceptual-hash terminology, Arabic hexadecimal wording, and imperative button forms in Hindi and Indonesian.\n\nThe primary and blind target selections agree in `'''+str(target_agreement)+'''` cells and differ in `'''+str(240-target_agreement)+'''`. The disagreements are retained with per-cell reasons in `recommendation-disagreements.jsonl`. Issue-focused rationale is in `adjudication-notes.json`.\n\nAll three packet checksum lists validate. The candidate-free exact-head attestations agree, and primary/blind static provenance ties back to the same candidate-free checksums. The blind manifest records that it did not open primary or worktree evidence; its prior output-path caveat is copied into the summary. The primary packet states its proposals were frozen before comparison to current targets; that chronology is packet-attested but has no independent timestamp seal. This cross-review necessarily inspected both frozen proposal sets. No native-speaker approval is claimed. The changed product worktree and root adjudication were not inspected; live repo status was not verified.\n\n## Files\n\n- `integrated-cross-ledger.jsonl`: one reconciled, provenance-pinned row per cell.\n- `recommendation-disagreements.jsonl`: rows with conflicting selections/actions and cross-resolution.\n- `source-window-summary.jsonl`: per-source action totals.\n- `adjudication-notes.json`: issue-level reasoning for identifier terms, library-health descriptions, audio fingerprints, hexadecimal notation, and fix gates.\n- `prior-active-hold-reattestation.jsonl`, `primary-hold-continuity.jsonl`, `blind-active-hold-reattestation.json`: three text-free hold attestations.\n- `input-pins.json`, `token-audit-summary.json`, `cross-review-summary.json`: pins, audits, and totals.\n- `verify_cross_review.py`: verifies all three input packet seals, exact pins, per-cell source/caller/catalog provenance, hold continuity, cross decisions, and token parity. It does not access the product worktree or root adjudication.\n- `SHA256SUMS.txt`: output packet checksum seal.\n\nNext queue boundary: position 1783, source key SHA-256 `'''+summary['nextBoundarySourceKeySha256']+'''`. No later window is included.\n''',encoding='utf-8')
print(json.dumps({'result':'CROSS_PACKET_BUILT','output':str(OUT),'cells':len(cross_rows),'disagreements':len(disagreement_rows),'crossDispositions':dict(p_counts),'targetAgreement':target_agreement,'strictTokenMismatches':token_counts['allMismatch']},ensure_ascii=False,indent=2))
