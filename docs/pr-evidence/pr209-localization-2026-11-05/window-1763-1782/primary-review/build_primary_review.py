#!/usr/bin/env python3
# Join frozen W1763-W1782 independent proposals to pinned current cells.
import collections, hashlib, json, re, shutil, subprocess
from datetime import datetime, timezone
from pathlib import Path
INPUT=Path('/mnt/disks/scratch/task-scratch/slskr-pr209-w1763-1782-candidate-free-20261105/candidate-free-input')
WORKTREE=Path('/home/keith/Documents/code/.task-worktrees/localization-20261105/slskr-w1683')
OUT=Path(__file__).resolve().parent
HEAD='5191888071f54061a6012acdedfeb518a6cb3661'; TREE='d5728c24b54a06dda432afd2ef5f378206a6cb8f'
FROZEN_PROPOSAL_SHA='142119303f5883c209772ef4103b016314ba79bf6f5227cdee7b9f5954ae33a7'
LOCALES=['es','zh-Hans','hi','de','ja','fr','pt-BR','ar','ko','zh-Hant','vi','id']
CORRECTIONS={
 1766:{'hi','de'},1767:{'hi','fr','ar'},1768:{'de','fr','ar','vi'},1770:{'hi','ko','zh-Hant'},1771:{'hi','de'},
 1772:set(LOCALES),1773:set(LOCALES),1774:set(LOCALES),1775:set(LOCALES),1776:set(LOCALES),
 1777:set(LOCALES)-{'pt-BR'},1778:{'ja','ko','zh-Hant'},1780:{'zh-Hans','ja','ar','ko','zh-Hant'},1781:set(LOCALES)
}
MEANINGS={
1763:'Button that launches an inbound-link search in the content graph.',
1764:'Search for additional files in the selected peer directory from a search result.',
1765:'Button that runs a fuzzy/similar-content search.',
1766:'Description of finding every graph item that points to one chosen ContentID.',
1767:'Placeholder asking for the ID whose inbound links will be found.',
1768:'Read-only discovery workflow that finds listed pods by metadata or registry scan.',
1769:'Retry action that seeks a different peer/source when the current peer cannot serve a file.',
1770:'Description of fuzzy matching based on perceptual hashes and text analysis.',
1771:'Description of resolving an external identifier to the application ContentID.',
1772:'Library-health scan finding duplicates, unavailable paths, missing metadata, falsely lossless files, and missing artwork.',
1773:'Audio-fingerprint length field in song-identification evidence.',
1774:'Audio-fingerprint availability status in metadata processing.',
1775:'Audio-fingerprint extraction error template; both named placeholders are substituted at runtime.',
1776:'Audio-fingerprint stored status in metadata processing.',
1777:'First input placeholder in the ContentID similarity form; neighboring labels are ContentID A/B.',
1778:'First hexadecimal hash input placeholder in the hash-similarity form.',
1779:'First text-input placeholder in the text-similarity form.',
1780:'Action button to repair selected library-health issues.',
1781:'Automation-recipe approval gate requiring user confirmation before a fix.',
1782:'In-progress status for an issue repair.'
}
def sha(b): return hashlib.sha256(b).hexdigest()
def j(path): return json.loads(path.read_text(encoding='utf-8'))
def jl(path): return [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines() if line.strip()]
def token_sig(s):
 return {'placeholders':re.findall(r'\{[A-Za-z][A-Za-z0-9_]*\}',s),'markup':re.findall(r'</?[A-Za-z][^>]*>',s),'numbers':re.findall(r'(?<![A-Za-z])\d+(?:[.,]\d+)?%?(?![A-Za-z])',s),'protected':list(dict.fromkeys(re.findall(r'(?<![A-Za-z0-9])(?:[A-Z]{2,}[A-Z0-9]*|ffmpeg|Chromaprint|Soulseek|Spotify|YouTube|Pushbullet|Matrix|WebSocket|OpenAI)(?![A-Za-z0-9])',s)))}
def manual_literals(source):
 out=[]
 if 'ContentID' in source: out.append('ContentID')
 if re.search(r'(?<![A-Za-z0-9])ID(?![A-Za-z0-9])',source): out.append('ID')
 return out
def token_audit(source,target):
 s=token_sig(source); t=token_sig(target); manual=manual_literals(source)
 return {'placeholderSequenceMatches':s['placeholders']==t['placeholders'],'markupMatches':s['markup']==t['markup'],'numericTokensMatch':s['numbers']==t['numbers'],'protectedLiteralSequenceMatches':s['protected']==t['protected'],'manualProtectedTermsRequired':manual,'manualProtectedTermsPreserved':all(re.search(r'(?<![A-Za-z0-9])'+re.escape(term)+r'(?![A-Za-z0-9])',target) for term in manual),'sourceSignature':s,'targetSignature':t}
def rationale(position,locale,decision,current,proposal):
 if decision=='correct':
  if position in (1766,1771): return 'Preserve the exact ContentID product identifier and its capitalization; the current string changes its spelling.'
  if position==1767: return 'Preserve the literal ID token; this caller uses the entered ID to find inbound links.'
  if position==1768: return {'de':'Registry scan means scanning a pod/image registry, not a registration scan.','fr':'The caller is pod discovery; “modules” changes the object being found.','ar':'The current word قرون means pods/centuries in the wrong sense; retain the technical Pod term.','vi':'The caller discovers technical pods; nhóm (“groups”) changes that object.'}[locale]
  if position==1770: return {'hi':'Perceptual hashes describe similarity hashes, not conceptual hashes.','ko':'Use the perceptual/sensory term 지각, not cognitive 인지.','zh-Hant':'Use the Traditional Chinese 雜湊 term for hashes in this technical label.'}[locale]
  if position==1772: return 'Replace literal dead-file/art calques with clear library-health terms for unavailable files and missing cover artwork; distinguish falsely lossless files.'
  if position in (1773,1774,1775,1776): return 'Pinned callers place this message in audio fingerprinting/song-identification; specify audio to avoid the human-fingerprint reading. The error template keeps both named placeholders in order.'
  if position==1777: return 'The caller labels adjacent fields ContentID A and ContentID B; preserve the exact ContentID field name.'
  if position==1778: return {'ja':'Remove the added numeric token 16; the English source contains no numeric token.','ko':'Remove the added numeric token 16; the English source contains no numeric token.','zh-Hant':'Use the established Traditional Chinese 雜湊 term; this wording describes a hexadecimal hash input.'}[locale]
  if position==1780: return {'zh-Hans':'使固定 means make stationary; this button repairs selected library-health issues.','ja':'Use the software-issue correction action rather than a physical repair reading.','ar':'Use an action label for repair; the current conjugation is not an appropriate button label.','ko':'Use the concise issue-correction action used for this repair button.','zh-Hant':'使固定 means make stationary; this button repairs selected library-health issues.'}[locale]
  if position==1781: return 'This automation field is an approval gate; wording must state that confirmation is required before the fix.'
  return 'The current wording misses the caller meaning; use the independently generated target.'
 if current==proposal: return 'Current wording matches the independent proposal and fits the pinned caller.'
 if position in (1763,1764,1765,1769): return 'Current wording is a clear action label for the pinned graph, search, or retry caller; the proposal is stylistic only.'
 if position in (1766,1767,1771): return 'Current wording conveys the graph lookup/resolution instruction and preserves its required identifier token.'
 if position==1768: return 'Current wording identifies the pod-discovery search and its lookup fields; the independent alternative is stylistic.'
 if position==1770: return 'Current wording accurately describes perceptual-hash and text-based similarity search.'
 if position==1778: return 'Current wording accurately labels the first hexadecimal hash input and preserves numeric-token rules.'
 if position==1779: return 'Current wording clearly labels the first text-string input; the proposal is a stylistic alternative.'
 if position==1780: return 'Current wording is a suitable action for repairing a selected issue.'
 if position==1782: return 'Current wording accurately reports the repair as in progress.'
 return 'Current wording is accurate in the pinned caller; keep it to avoid a style-only rewrite.'
def main():
 manifest=j(INPUT/'manifest.json'); assert (manifest['head'],manifest['tree'])==(HEAD,TREE)
 actual_head=subprocess.check_output(['git','-C',str(WORKTREE),'rev-parse','HEAD'],text=True).strip(); actual_tree=subprocess.check_output(['git','-C',str(WORKTREE),'rev-parse','HEAD^{tree}'],text=True).strip()
 assert (actual_head,actual_tree)==(HEAD,TREE) and subprocess.check_output(['git','-C',str(WORKTREE),'status','--porcelain=v1'],text=True)==''
 proposal_path=OUT/'independent-proposals.jsonl'; assert sha(proposal_path.read_bytes())==FROZEN_PROPOSAL_SHA
 proposals=jl(proposal_path); current=jl(INPUT/'current-target-cells.jsonl'); sources=jl(INPUT/'source-contexts.jsonl')
 assert len(proposals)==len(current)==240 and len(sources)==20
 proposal_by={(x['position'],x['locale']):x for x in proposals}; current_by={(x['position'],x['locale']):x for x in current}
 expected_keys=[(pos,loc) for pos in range(1763,1783) for loc in LOCALES]
 assert list((x['position'],x['locale']) for x in proposals)==expected_keys and list((x['position'],x['locale']) for x in current)==expected_keys
 decisions=[]; counts=collections.Counter(); input_token_counts=collections.Counter(); current_manual_mismatch=0; manual_only_mismatch=0; final_mismatch=0; current_mismatch_cells=0
 for pos,locale in expected_keys:
  p=proposal_by[pos,locale]; c=current_by[pos,locale]
  assert p['sourceKey']==c['sourceKey'] and p['sourceKeySha256']==c['sourceKeySha256'] and p['sourceContextSha256']==c['sourceContextSha256']
  source=p['sourceKey']; original=c['currentTarget']; proposed=p['proposedTarget']; action='correct' if locale in CORRECTIONS.get(pos,set()) else 'retain'; final=proposed if action=='correct' else original
  aud=token_audit(source,original); final_aud=token_audit(source,final); variants=c['targetTokenVariants']
  checks={'placeholderSequenceMatches':all(v['placeholderSequenceMatches'] for v in variants),'markupMatches':all(v['markupMatches'] for v in variants),'numericTokensMatch':all(v['numericTokensMatch'] for v in variants),'protectedLiteralsMatch':all(v['protectedLiteralsMatch'] for v in variants)}
  for k,v in checks.items(): input_token_counts[k]+=not v
  manual_bad=not aud['manualProtectedTermsPreserved']
  if manual_bad: current_manual_mismatch+=1
  official_bad=not all(checks.values())
  if manual_bad and not official_bad: manual_only_mismatch+=1
  current_mismatch_cells+=official_bad or manual_bad
  final_bad=not (final_aud['placeholderSequenceMatches'] and final_aud['markupMatches'] and final_aud['numericTokensMatch'] and final_aud['protectedLiteralSequenceMatches'] and final_aud['manualProtectedTermsPreserved'])
  final_mismatch+=final_bad
  if final_bad: raise SystemExit(f'final token failure at {pos}/{locale}: {final_aud}')
  if action=='correct' and final!=proposed: raise SystemExit('correction did not select independent proposal')
  if action=='retain' and final!=original: raise SystemExit('retain changed current target')
  if action=='retain' and (official_bad or manual_bad): raise SystemExit(f'unsafe retain with token mismatch at {pos}/{locale}')
  counts[action]+=1
  decisions.append({'position':pos,'sourceKey':source,'sourceKeySha256':p['sourceKeySha256'],'sourceContextSha256':p['sourceContextSha256'],'locale':locale,'catalogPath':c['catalogPath'],'catalogFileSha256':c['catalogFileSha256'],'catalogGitBlob':c['catalogGitBlob'],'callerCount':c['callerCount'],'currentTarget':original,'currentTargetSha256':c['currentTargetSha256'],'independentProposal':proposed,'independentProposalSha256':p['proposedTargetSha256'],'independentProposalLedgerSha256':FROZEN_PROPOSAL_SHA,'decision':action,'finalTarget':final,'finalTargetSha256':sha(final.encode()),'currentTokenAudit':{**checks,'manualProtectedTermsRequired':aud['manualProtectedTermsRequired'],'manualProtectedTermsPreserved':aud['manualProtectedTermsPreserved'],'targetSignature':aud['targetSignature']},'finalTokenAudit':{**final_aud,'allPreserved':not final_bad},'rationale':rationale(pos,locale,action,original,proposed),'decisionBasis':'source/callsite interpretation; independent proposal frozen before current-target comparison'})
 assert counts=={'correct':105,'retain':135} and final_mismatch==0
 source_review=[]
 for s in sources:
  source_review.append({'position':s['position'],'sourceKey':s['sourceKey'],'sourceKeySha256':s['sourceKeySha256'],'sourceContextSha256':s['callerContextSha256'],'callerOccurrenceCount':s['callerOccurrenceCount'],'meaning':MEANINGS[s['position']],'callers':[{'path':c['path'],'line':c['line'],'lineSha256':c['lineSha256'],'contextSha256':c['contextSha256']} for c in s['callers']],'manualProtectedTerms':manual_literals(s['sourceKey'])})
 hold_raw=(INPUT/'active-hold-reattestation.jsonl').read_text(encoding='utf-8'); hold_rows=[json.loads(x) for x in hold_raw.splitlines() if x.strip()]
 assert len(hold_rows)==1 and hold_rows[0]['holdId']=='1719::id' and hold_rows[0]['textIncluded'] is False
 (OUT/'hold-continuity.jsonl').write_text(json.dumps(hold_rows[0],ensure_ascii=False,separators=(',',':'))+'\n',encoding='utf-8')
 pin_file={'repository':'snapetech-org/slskR','pullRequest':209,'window':'W1763-W1782','head':HEAD,'tree':TREE,'candidateFreeInput':str(INPUT),'candidateFreeManifestSha256':sha((INPUT/'manifest.json').read_bytes()),'candidateFreeChecksumListSha256':sha((INPUT/'SHA256SUMS.txt').read_bytes()),'currentTargetCellsSha256':sha((INPUT/'current-target-cells.jsonl').read_bytes()),'sourceContextsSha256':sha((INPUT/'source-contexts.jsonl').read_bytes()),'selectedSourceKeysSha256':sha((INPUT/'selected-source-keys.txt').read_bytes()),'sourceQueueSha256':manifest['sourceQueueFileSha256'],'sourceLookupKeyOrderSha256':manifest['sourceLookupKeyOrderSha256'],'independentProposalSha256':FROZEN_PROPOSAL_SHA,'activeHoldInputSha256':sha((INPUT/'active-hold-reattestation.jsonl').read_bytes()),'worktreePath':str(WORKTREE),'worktreeStatusClean':True,'productHeadAdvanced':False}
 (OUT/'input-pins.json').write_text(json.dumps(pin_file,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 for name in ['manifest.json','SHA256SUMS.txt','selected-source-keys.txt','source-contexts.jsonl','localization-runtime-context.json','active-hold-reattestation.jsonl','source-window-boundaries.jsonl','catalog-file-pins.json','catalog-structure.jsonl']:
  shutil.copyfile(INPUT/name,OUT/('input-'+name))
 (OUT/'locale-review.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False,separators=(',',':'))+'\n' for r in decisions),encoding='utf-8')
 source_doc={'artifact':'slskR PR #209 W1763-W1782 primary semantic review','repository':'snapetech-org/slskR','pullRequest':209,'window':'W1763-W1782','head':HEAD,'tree':TREE,'sourceCount':20,'localeCount':12,'cellCount':240,'independentProposalSha256':FROZEN_PROPOSAL_SHA,'reviewerRole':'primary semantic reviewer','semanticConfidence':'moderate','localeConfidence':'moderate','nativeSpeakerApproval':False,'decisionBasis':'Pinned source and caller context; independent target proposals frozen before current catalog cells were opened. Current strings were consulted only afterward for retain/correct decisions and token audit.','sources':source_review}
 (OUT/'source-review.json').write_text(json.dumps(source_doc,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 boundaries=[json.loads(x) for x in (INPUT/'source-window-boundaries.jsonl').read_text().splitlines()]; nxt=next(x for x in boundaries if x['boundary'] and x['position']==1783)
 (OUT/'next-boundary.json').write_text(json.dumps({'nextWindowPosition':1783,'sourceKeySha256':nxt['sourceKeySha256'],'head':HEAD,'tree':TREE},indent=2)+'\n',encoding='utf-8')
 summary={'artifact':'slskR PR #209 W1763-W1782 primary review','schemaVersion':1,'head':HEAD,'tree':TREE,'window':'W1763-W1782','sourceCount':20,'localeCount':12,'cellCount':240,'actions':dict(counts),'perPositionActionCounts':{str(pos):{'correct':sum(1 for r in decisions if r['position']==pos and r['decision']=='correct'),'retain':sum(1 for r in decisions if r['position']==pos and r['decision']=='retain')} for pos in range(1763,1783)},'independentProposals':240,'independentProposalLedgerSha256':FROZEN_PROPOSAL_SHA,'candidateFreeTokenMismatchCounts':manifest['tokenMismatchCounts'],'currentTokenAudit':{'placeholderSequenceMismatchCells':input_token_counts['placeholderSequenceMatches'],'markupMismatchCells':input_token_counts['markupMatches'],'numericTokenMismatchCells':input_token_counts['numericTokensMatch'],'protectedLiteralMismatchCells':input_token_counts['protectedLiteralsMatch'],'manualProtectedTermMismatchCells':current_manual_mismatch,'manualOnlyAdditionalMismatchCells':manual_only_mismatch,'allCurrentTokenMismatchCells':current_mismatch_cells},'finalTokenMismatchCells':final_mismatch,'proposedPlaceholdersPreserved':True,'proposedMarkupPreserved':True,'proposedNumericTokensPreserved':True,'proposedProtectedLiteralsPreserved':True,'callerlessPositionsInWindow':[],'newHolds':0,'activeHoldContinuity':{'holdId':'1719::id','textIncluded':False,'targetHashUnchanged':hold_rows[0]['targetHashUnchanged'],'sourceContextUnchanged':hold_rows[0]['sourceContextUnchanged']},'nextBoundaryPosition':1783,'nextBoundarySourceKeySha256':nxt['sourceKeySha256'],'nativeSpeakerApproval':False,'testsBuildsCiRun':False,'repoEdited':False,'productHeadAdvanced':False,'createdAtUtc':datetime.now(timezone.utc).isoformat()}
 (OUT/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 readme=(f"# slskR PR #209 W1763–W1782 primary review\n\nPinned to `{HEAD}` / `{TREE}`. This packet covers 20 sources × 12 locales (240 cells).\n\n`independent-proposals.jsonl` was generated from the exact-head candidate-free source/caller context before opening current translation cells. Its frozen SHA-256 is `{FROZEN_PROPOSAL_SHA}`. The final locale ledger then compares current targets to those frozen proposals and selects either a correction or retain.\n\n## Result\n\n- Corrections: {counts['correct']}\n- Retained current targets: {counts['retain']}\n- Final placeholder, markup, number, and protected-token mismatches: {final_mismatch}\n- Corrected the candidate-free `ID` mismatches, numeric mismatches, and 15 additional exact `ContentID` mismatches.\n- The prior active hold `1719::id` is copied as a text-free hash-only reattestation. No selected-window callerless positions or new holds.\n- Next queue boundary: position 1783 (`{nxt['sourceKeySha256']}`).\n\nThe locale judgments are machine-produced semantic recommendations; no native-speaker approval is claimed. No product files were edited and no product tests, builds, or CI were run. Run `python3 -B verify_primary_review.py` and `sha256sum -c SHA256SUMS.txt` from this directory.\n")
 (OUT/'README.md').write_text(readme,encoding='utf-8')
 print(json.dumps({'result':'BUILT','output':str(OUT),'cells':len(decisions),'corrections':counts['correct'],'retains':counts['retain'],'candidateFreeCurrentMismatchCounts':manifest['tokenMismatchCounts'],'manualProtectedMismatchCells':current_manual_mismatch,'manualOnlyAdditionalMismatchCells':manual_only_mismatch,'allCurrentMismatchCells':current_mismatch_cells,'finalTokenMismatchCells':final_mismatch,'hold':'1719::id hash-only','nextBoundary':1783},ensure_ascii=False,indent=2))
if __name__=='__main__': main()
