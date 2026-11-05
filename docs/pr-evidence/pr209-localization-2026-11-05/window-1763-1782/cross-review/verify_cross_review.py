#!/usr/bin/env python3
"""Verify integrated cross-review packet against the three sealed static inputs only."""
import collections, hashlib, json, re, subprocess
from pathlib import Path
OUT=Path(__file__).resolve().parent
CF=Path('/mnt/disks/scratch/task-scratch/slskr-pr209-w1763-1782-candidate-free-20261105/candidate-free-input')
PRIMARY=Path('/mnt/disks/scratch/task-scratch/slskr-pr209-w1763-1782-primary-review-20261105/primary-review')
BLIND=Path('/mnt/disks/scratch/task-scratch/slskr-pr209-w1763-1782-blind-review-agent-20261105')
HEAD='5191888071f54061a6012acdedfeb518a6cb3661'; TREE='d5728c24b54a06dda432afd2ef5f378206a6cb8f'; REPO='snapetech-org/slskR'; PR=209
LOCALES=['es','zh-Hans','hi','de','ja','fr','pt-BR','ar','ko','zh-Hant','vi','id']
PH=re.compile(r'\{[A-Za-z][A-Za-z0-9_]*\}'); TAG=re.compile(r'</?[A-Za-z][^>]*>'); NUM=re.compile(r'(?<![A-Za-z])\d+(?:[.,]\d+)?%?(?![A-Za-z])')
PROT=re.compile(r'(?<![A-Za-z0-9])(?:[A-Z]{2,}[A-Z0-9]*|ffmpeg|Chromaprint|Soulseek|Spotify|YouTube|Pushbullet|Matrix|WebSocket|OpenAI)(?![A-Za-z0-9])')
def fail(x): raise SystemExit('FAIL: '+x)
def req(x,msg):
 if not x: fail(msg)
def sha(b): return hashlib.sha256(b).hexdigest()
def t_sha(s): return sha(s.encode('utf-8'))
def readj(p): return json.loads(p.read_text(encoding='utf-8'))
def readjl(p): return [json.loads(s) for s in p.read_text(encoding='utf-8').splitlines() if s.strip()]
def sig(s): return {'placeholders':PH.findall(s),'markup':TAG.findall(s),'numbers':NUM.findall(s),'protected':list(dict.fromkeys(PROT.findall(s)))}
def manual(s):
 out=[]
 if 'ContentID' in s: out.append('ContentID')
 if re.search(r'(?<![A-Za-z0-9])ID(?![A-Za-z0-9])',s): out.append('ID')
 return out
def audit(src,target):
 a,b=sig(src),sig(target); terms=manual(src)
 okmanual=all(re.search(r'(?<![A-Za-z0-9])'+re.escape(x)+r'(?![A-Za-z0-9])',target) for x in terms)
 return {'placeholdersMatch':a['placeholders']==b['placeholders'],'markupMatch':a['markup']==b['markup'],'numbersMatch':a['numbers']==b['numbers'],'protectedLiteralSequenceMatches':a['protected']==b['protected'],'manualProtectedTermsPreserved':okmanual,'allPreserved':a['placeholders']==b['placeholders'] and a['markup']==b['markup'] and a['numbers']==b['numbers'] and a['protected']==b['protected'] and okmanual}
def check_sums(path):
 r=subprocess.run(['sha256sum','-c','SHA256SUMS.txt'],cwd=path,text=True,capture_output=True)
 if r.returncode: fail('input checksum list failed: '+str(path)+' '+r.stdout+r.stderr)

def norm_cf(c): return (c['path'],c['line'],c['lineSha256'],c['fileSha256'],c['gitBlob'],c['contextSha256'],c['lineText'],c['contextStartLine'],c['contextEndLine'],c['literalOccurrenceCount'])
def norm_bl(c): return (c['path'],c['line'],c['line_sha256'],c['file_sha256'],c['git_blob'],c['context_sha256'],c['line_text'],c['context_start_line'],c['context_end_line'],c.get('literal_occurrence_count',1))
for x in (CF,PRIMARY,BLIND): check_sums(x)
req((PRIMARY/'input-SHA256SUMS.txt').read_bytes()==(CF/'SHA256SUMS.txt').read_bytes(),'primary candidate-free checksum pointer differs')
cfm=readj(CF/'manifest.json'); ps=readj(PRIMARY/'summary.json'); pi=readj(PRIMARY/'input-pins.json'); bm=readj(BLIND/'manifest.json')
req((cfm['repository'],cfm['pullRequest'],cfm['head'],cfm['tree'],cfm['window'])==(REPO,PR,HEAD,TREE,'W1763-W1782'),'candidate-free exact pin mismatch')
req((ps['head'],ps['tree'],ps['window'],pi['repository'],pi['pullRequest'],pi['head'],pi['tree'],pi['window'])==(HEAD,TREE,'W1763-W1782',REPO,PR,HEAD,TREE,'W1763-W1782'),'primary exact pin mismatch')
req((bm['repository'],bm['pull_request'],bm['review_head'],bm['review_tree'],bm['window'])==(REPO,PR,HEAD,TREE,'W1763-W1782'),'blind exact pin mismatch')
for fn in ('attestation-before.json','attestation-after.json'):
 a=readj(CF/fn); req((a['headSha'],a['headTree'],a['pullRequest'],a['repository'])==(HEAD,TREE,PR,REPO),'candidate-free PR attestation pin mismatch')
a=readj(CF/'attestation-before.json');b=readj(CF/'attestation-after.json')
req({k:v for k,v in a.items() if k not in ('capturedAtUtc','label')}=={k:v for k,v in b.items() if k not in ('capturedAtUtc','label')},'candidate-free before/after attestations changed')

pins=readj(OUT/'input-pins.json')
req((pins['head'],pins['tree'],pins['window'])==(HEAD,TREE,'W1763-W1782'),'cross input pin mismatch')
expected_pins={
 'candidateFree':{'checksumListSha256':sha((CF/'SHA256SUMS.txt').read_bytes()),'manifestSha256':sha((CF/'manifest.json').read_bytes()),'currentTargetCellsSha256':sha((CF/'current-target-cells.jsonl').read_bytes()),'sourceContextsSha256':sha((CF/'source-contexts.jsonl').read_bytes()),'sourceQueueSha256':sha((CF/'source-queue.jsonl').read_bytes()),'activeHoldSha256':sha((CF/'active-hold-reattestation.jsonl').read_bytes()),'beforeAttestationSha256':sha((CF/'attestation-before.json').read_bytes()),'afterAttestationSha256':sha((CF/'attestation-after.json').read_bytes())},
 'primary':{'checksumListSha256':sha((PRIMARY/'SHA256SUMS.txt').read_bytes()),'inputChecksumListSha256':sha((PRIMARY/'input-SHA256SUMS.txt').read_bytes()),'summarySha256':sha((PRIMARY/'summary.json').read_bytes()),'inputPinsSha256':sha((PRIMARY/'input-pins.json').read_bytes()),'localeReviewSha256':sha((PRIMARY/'locale-review.jsonl').read_bytes()),'frozenProposalLedgerSha256':sha((PRIMARY/'independent-proposals.jsonl').read_bytes())},
 'blind':{'checksumListSha256':sha((BLIND/'SHA256SUMS.txt').read_bytes()),'manifestSha256':sha((BLIND/'manifest.json').read_bytes()),'blindLedgerSha256':sha((BLIND/'blind-ledger.jsonl').read_bytes()),'tokenAuditSha256':sha((BLIND/'token-audit.json').read_bytes()),'activeHoldSha256':sha((BLIND/'active-hold-reattestation.json').read_bytes())}}
for role,values in expected_pins.items():
 for k,v in values.items(): req(pins[role][k]==v,f'{role} input hash mismatch: {k}')
req(pins['productWorktreeInspected'] is False and pins['rootAdjudicationInspected'] is False,'scope boundary claim mismatch')

queue=readjl(CF/'source-queue.jsonl'); sources=[r for r in queue if 1763<=r['position']<=1782]
req(len(sources)==20 and [r['position'] for r in sources]==list(range(1763,1783)),'source queue gap/overlap')
req((CF/'selected-source-keys.txt').read_text().splitlines()==[r['sourceKey'] for r in sources],'selected key sequence mismatch')
ctxrows=readjl(CF/'source-contexts.jsonl');ctx={(r['position'],r['sourceKey']):r for r in ctxrows}
req(len(ctxrows)==20 and sum(x['callerOccurrenceCount'] for x in ctxrows)==30 and sum(x['productionCallerCount'] for x in ctxrows)==30,'caller context count mismatch')

cells=readjl(CF/'current-target-cells.jsonl'); prs=readjl(PRIMARY/'locale-review.jsonl'); props=readjl(PRIMARY/'independent-proposals.jsonl');bls=readjl(BLIND/'blind-ledger.jsonl'); rows=readjl(OUT/'integrated-cross-ledger.jsonl'); disagreements=readjl(OUT/'recommendation-disagreements.jsonl')
req((len(cells),len(prs),len(props),len(bls),len(rows))==(240,240,240,240,240),'240-cell packet coverage mismatch')
key=lambda r:(r['position'],r['locale'])
cm={key(r):r for r in cells};pm={key(r):r for r in prs};pp={key(r):r for r in props};bm={(r['position'],r['locale']):r for r in bls};rm={key(r):r for r in rows}
expected={(p,l) for p in range(1763,1783) for l in LOCALES}
req(set(cm)==set(pm)==set(pp)==set(bm)==set(rm)==expected,'cell keys/locale coverage mismatch')
req(bm and bm[(1763,'es')]['locale']=='es','blind cell key order mismatch')

catalogs=readj(CF/'catalog-file-pins.json')['localeCatalogs'];structures={r['locale']:r for r in readjl(CF/'catalog-structure.jsonl')}
for k in sorted(expected,key=lambda x:(x[0],LOCALES.index(x[1]))):
 c,p,prop,b,r=cm[k],pm[k],pp[k],bm[k],rm[k]; pos,locale=k; source=c['sourceKey']; context=ctx[(pos,source)]; cat=catalogs[locale]
 req(t_sha(source)==c['sourceKeySha256'],'source key hash mismatch '+str(k))
 req(t_sha(c['currentTarget'])==c['currentTargetSha256'],'current target hash mismatch '+str(k))
 req(c['targetTextIncluded'] is True and c['currentTargetType']=='str','current target not present as a string '+str(k))
 req((c['sourceContextSha256'],c['callerCount'])==(context['callerContextSha256'],context['productionCallerCount']),'candidate-free context pin mismatch '+str(k))
 req((c['catalogPath'],c['catalogFileSha256'],c['catalogGitBlob'])==(cat['path'],cat['sha256'],cat['gitBlob']),'catalog file pin mismatch '+str(k))
 req(cat['keyCount']==5441 and structures[locale]['keyCount']==5441 and cat['orderedKeySha256']==structures[locale]['orderedKeySha256'],'catalog order/count pin mismatch '+str(k))
 req((p['sourceKey'],p['sourceKeySha256'],p['sourceContextSha256'],p['callerCount'],p['catalogPath'],p['catalogFileSha256'],p['catalogGitBlob'],p['currentTarget'],p['currentTargetSha256'])==(source,c['sourceKeySha256'],context['callerContextSha256'],c['callerCount'],c['catalogPath'],c['catalogFileSha256'],c['catalogGitBlob'],c['currentTarget'],c['currentTargetSha256']),'primary provenance mismatch '+str(k))
 req((b['source_key'],b['source_key_sha256'],b['source_context_sha256'],b['caller_reference_count'],b['catalog_path'],b['catalog_file_sha256'],b['catalog_git_blob'],b['current_target'],b['current_target_sha256'],b['input_head'],b['input_tree'])==(source,c['sourceKeySha256'],context['callerContextSha256'],c['callerCount'],c['catalogPath'],c['catalogFileSha256'],c['catalogGitBlob'],c['currentTarget'],c['currentTargetSha256'],HEAD,TREE),'blind provenance mismatch '+str(k))
 req((prop['sourceKey'],prop['sourceKeySha256'],prop['sourceContextSha256'],prop['proposedTarget'])==(source,c['sourceKeySha256'],context['callerContextSha256'],p['independentProposal']),'frozen proposal mismatch '+str(k))
 req(prop['proposedTargetSha256']==t_sha(prop['proposedTarget'])==p['independentProposalSha256'],'frozen proposal digest mismatch '+str(k))
 req(p['independentProposalLedgerSha256']==sha((PRIMARY/'independent-proposals.jsonl').read_bytes()),'proposal ledger digest pointer mismatch '+str(k))
 req(t_sha(p['finalTarget'])==p['finalTargetSha256'],'primary final target digest mismatch '+str(k))
 req(p['finalTokenAudit']['allPreserved'] is True,'primary final token audit failed '+str(k))
 req(b['token_audit']['result']=='pass' and b['selected_target']==(b['current_target'] if b['decision']=='accept_current' else b['proposal']),'blind decision/token audit mismatch '+str(k))
 req(r['provenanceVerified'] is True and (r['sourceKey'],r['sourceKeySha256'],r['sourceContextSha256'])==(source,c['sourceKeySha256'],context['callerContextSha256']),'cross provenance flag mismatch '+str(k))
\
 refs=sorted(norm_cf(x) for x in context['callers']); blind_refs=sorted(norm_bl(x) for x in b['caller_refs'])
 req(refs==blind_refs,'blind caller references differ from source context '+str(k))
 req(b['caller_reference_count']==len(context['callers'])==context['callerOccurrenceCount'],'caller reference count mismatch '+str(k))
 expected_target=p['finalTarget'] if p['decision']=='correct' else (b['selected_target'] if b['decision']=='refine' else c['currentTarget'])
 expected_action='correction' if p['decision']=='correct' else ('refinement' if b['decision']=='refine' else 'accept_current')
 req((r['crossTarget'],r['crossDisposition'])==(expected_target,expected_action),'cross action/target does not follow adjudication policy '+str(k))
 req(t_sha(r['crossTarget'])==r['crossTargetSha256'],'cross selected target digest mismatch '+str(k))
 calc=audit(source,r['crossTarget'])
 req(all(calc[f]==r['crossTokenAudit'].get(f) for f in calc) and r['crossTokenAudit'].get('source')==sig(source) and r['crossTokenAudit'].get('target')==sig(r['crossTarget']) and calc['allPreserved'],'strict cross token audit mismatch '+str(k))
 req(r['primaryDecision']==p['decision'] and r['primaryFinalTarget']==p['finalTarget'] and r['blindDecision']==b['decision'] and r['blindSelectedTarget']==b['selected_target'],'cross comparison values mismatch '+str(k))
 req(r['currentTarget']==c['currentTarget'] and r['currentTargetSha256']==c['currentTargetSha256'],'cross current target mismatch '+str(k))

# Recount current issues and selected outputs independently.
current_count=collections.Counter(); current_issue=set(); cross_count=collections.Counter(); target_agree=0; target_diff=0; p_action=collections.Counter(x['decision'] for x in prs); b_action=collections.Counter(x['decision'] for x in bls); matrix=collections.Counter(); disagreement_expected=[]
for k in sorted(expected,key=lambda x:(x[0],LOCALES.index(x[1]))):
 c,p,b,r=cm[k],pm[k],bm[k],rm[k]
 ss,ts=sig(c['sourceKey']),sig(c['currentTarget']); issues=[]
 for field in ('placeholders','markup','numbers'):
  if ss[field]!=ts[field]: current_count[field]+=1; issues.append(field)
 missing=[x for x in ss['protected'] if not re.search(r'(?<![A-Za-z0-9])'+re.escape(x)+r'(?![A-Za-z0-9])',c['currentTarget'])]
 if missing: current_count['protectedMissing']+=1; issues.append('protectedMissing')
 missing_manual=[x for x in manual(c['sourceKey']) if not re.search(r'(?<![A-Za-z0-9])'+re.escape(x)+r'(?![A-Za-z0-9])',c['currentTarget'])]
 if missing_manual: current_count['manualProtectedTermMismatchCells']+=1; issues.append('manualProtectedTermMismatch')
 if issues: current_issue.add(k)
 cross_count[r['crossDisposition']]+=1
 matrix[(p['decision'],b['decision'])]+=1
 if p['finalTarget']==b['selected_target']: target_agree+=1
 else: target_diff+=1
 compare=r['comparisonClass']
 if compare!='both_retain_or_accept_current' and (p['finalTarget']!=b['selected_target'] or p['decision']!=('retain' if b['decision']=='accept_current' else b['decision'])):
  disagreement_expected.append(r)
req(p_action=={'retain':135,'correct':105},'primary decision totals mismatch')
req(b_action=={'accept_current':156,'correct':27,'refine':57},'blind decision totals mismatch')
req(current_count['numbers']==2 and current_count['protectedMissing']==3 and current_count['manualProtectedTermMismatchCells']==18 and len(current_issue)==20,'current token issue counts mismatch')
req(cross_count=={'accept_current':131,'correction':105,'refinement':4},'cross disposition totals mismatch')
req(target_agree==166 and target_diff==74,'primary/blind target agreement totals mismatch')
req(len(disagreements)==len(disagreement_expected)==105 and disagreements==disagreement_expected,'recommendation disagreement ledger mismatch')
req(ps['finalTokenMismatchCells']==0,'primary final token mismatch count is nonzero')
req(all(r['crossTokenAudit']['allPreserved'] for r in rows),'cross token mismatch present')

# Reattest 1719::id across the three sources without emitting its target text.
h_cf=readjl(CF/'active-hold-reattestation.jsonl'); h_p=readjl(PRIMARY/'hold-continuity.jsonl'); h_b=readj(BLIND/'active-hold-reattestation.json')
req(len(h_cf)==len(h_p)==1 and h_cf==h_p,'candidate-free and primary hold rows differ')
h=h_cf[0]
req((h['holdId'],h['position'],h['locale'],h['currentTargetSha256'],h['priorCurrentTargetSha256'],h['currentHead'],h['currentTree'],h['textIncluded'])==('1719::id',1719,'id','a27ecc61d532350de5694128b36f6cf1a57939c6c9dfa7460752041df275682f','a27ecc61d532350de5694128b36f6cf1a57939c6c9dfa7460752041df275682f',HEAD,TREE,False),'active prior hold did not remain hash-only and unchanged')
req((h_b['hold_id'],h_b['position'],h_b['locale'],h_b['current_target_sha256'],h_b['prior_target_sha256'],h_b['source_key_sha256'],h_b['input_head'],h_b['input_tree'],h_b['target_hash_unchanged'],h_b['target_text_included'],h_b['proposal'])==('1719::id',1719,'id',h['currentTargetSha256'],h['priorCurrentTargetSha256'],h['sourceKeySha256'],HEAD,TREE,True,False,None),'blind active hold differs or includes text')
req((OUT/'prior-active-hold-reattestation.jsonl').read_bytes()==(CF/'active-hold-reattestation.jsonl').read_bytes(),'candidate-free hold bytes not preserved')
req((OUT/'primary-hold-continuity.jsonl').read_bytes()==(PRIMARY/'hold-continuity.jsonl').read_bytes(),'primary hold bytes not preserved')
req((OUT/'blind-active-hold-reattestation.json').read_bytes()==(BLIND/'active-hold-reattestation.json').read_bytes(),'blind hold bytes not preserved')
for path in (OUT/'prior-active-hold-reattestation.jsonl',OUT/'primary-hold-continuity.jsonl'):
 for r in readjl(path):
  req(all(k.lower() not in ('target','targettext','translation','translationtext','currenttarget') for k in r),'text field in hold evidence')

summary=readj(OUT/'cross-review-summary.json')
req((summary['repository'],summary['pullRequest'],summary['head'],summary['tree'],summary['window'],summary['selectedCells'],summary['selectedSources'],summary['callerReferences'])==(REPO,PR,HEAD,TREE,'W1763-W1782',240,20,30),'cross summary pin/count mismatch')
req(summary['crossDispositions']=={'accept_current':131,'correction':105,'refinement':4} and summary['newHolds']==0 and summary['activePriorHoldCount']==1,'cross summary disposition/hold mismatch')
req(summary['nextBoundaryPosition']==1783 and summary['nextBoundarySourceKeySha256']==readj(CF/'source-order-lineage.json')['nextBoundarySourceKeySha256'],'next-boundary mismatch')
req(summary['proposalExposureAndProvenance']['crossReviewerConsultedBothProposalSets'] is True and summary['proposalExposureAndProvenance']['liveProductWorktreeStatusVerified'] is False,'proposal exposure/worktree limitation missing')
req(pins['productWorktreeInspected'] is False and pins['rootAdjudicationInspected'] is False,'scope boundary changed')

# The output SHA list is verified after all artifacts are written.
r=subprocess.run(['sha256sum','-c','SHA256SUMS.txt'],cwd=OUT,text=True,capture_output=True)
if r.returncode: fail('output checksum list failed: '+r.stdout+r.stderr)
print(json.dumps({'result':'PASS','head':HEAD,'tree':TREE,'cells':240,'sources':20,'callerReferences':30,'perCellProvenance':'240/240','primaryBlindTargetAgreement':166,'primaryBlindTargetDisagreement':74,'recommendationDisagreementRows':105,'crossDispositions':dict(cross_count),'newHolds':0,'preservedTextFreeHold':'1719::id','currentTokenIssueCells':20,'crossTokenMismatches':0,'threeInputChecksumLists':'PASS','outputChecksumList':'PASS','productWorktreeOrRootRead':'false','nextBoundaryPosition':1783},ensure_ascii=False,indent=2))
