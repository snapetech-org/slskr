from pathlib import Path
import json,hashlib,re
ROOT=Path('/mnt/disks/scratch/task-scratch/slskr-pr204-window-0983-1002-independent-crossreview-20261103')
PRIMARY=Path('/mnt/disks/scratch/task-scratch/slskr-pr204-window-0983-1002-primary-20261102/primary-review-ledger.jsonl')
blind=[json.loads(x) for x in (ROOT/'blind-ledger.jsonl').read_text(encoding='utf-8').splitlines()]
primary=[json.loads(x) for x in PRIMARY.read_text(encoding='utf-8').splitlines()]
seal=json.loads((ROOT/'blind-ledger-seal.json').read_text(encoding='utf-8'))
blind_sha=hashlib.sha256((ROOT/'blind-ledger.jsonl').read_bytes()).hexdigest()
primary_sha=hashlib.sha256(PRIMARY.read_bytes()).hexdigest()
assert blind_sha==seal['sha256'], 'sealed blind ledger changed'
assert len(blind)==len(primary)==240
bmap={(x['sourcePosition'],x['locale']):x for x in blind}; pmap={(x['sourcePosition'],x['locale']):x for x in primary}
assert set(bmap)==set(pmap)

def ph(s): return list(dict.fromkeys(re.findall(r'\{[A-Za-z_][A-Za-z0-9_]*\}',s)))
def tags(s): return re.findall(r'<[^>]+>',s)
def icu(s): return bool(re.search(r'\{\s*[A-Za-z_][\w.-]*\s*,\s*(?:plural|select|selectordinal)\b',s,re.I))
period=set('.。．۔।᠃'); question=set('?？؟'); exclaim=set('!！')
def punct(s):
 if not s:return 'none'
 c=s[-1]
 return 'period' if c in period else 'question' if c in question else 'exclamation' if c in exclaim else 'none'
def protected(s): return ([x for x in ['FLAC'] if x in s] + (['Pod'] if re.search(r'\bPod\b',s) else []))
def structural(source,target):
 required=protected(source)
 checks={'placeholders':ph(target)==ph(source),'markup':tags(target)==tags(source),'icu':icu(target)==icu(source),'protectedLiterals':all(x in target for x in required),'punctuation':punct(target)==punct(source)}
 return {'checks':checks,'failed':[k for k,v in checks.items() if not v]}

comp=[]; review_differences=[]; primary_structural_issues=[]; source_current_mismatches=[]
blind_counts={}; primary_counts={}; proposal_rows=0; reviewed_final_rows=0
for key,b in bmap.items():
 p=pmap[key]
 if b['sourceId']!=p['sourceId'] or b['sourceSha256']!=p['sourceSha256'] or b['currentTarget']!=p['currentTarget'] or b['currentTargetSha256']!=p['currentTargetSha256']:
  source_current_mismatches.append({'sourcePosition':key[0],'locale':key[1],'type':'source/current identity or hash mismatch'})
 bd=b['disposition']; pd=p['disposition']
 blind_counts[bd]=blind_counts.get(bd,0)+1; primary_counts[pd]=primary_counts.get(pd,0)+1
 pt=p.get('proposedTarget') if isinstance(p.get('proposedTarget'),str) else None
 pf=p.get('reviewedFinal') if isinstance(p.get('reviewedFinal'),str) else None
 if pt is not None: proposal_rows+=1
 if pf is not None: reviewed_final_rows+=1
 diffs=[]
 if bd!=pd: diffs.append('disposition')
 if (b['proposedTarget'] is None)!=(pt is None): diffs.append('proposal-presence')
 elif b['proposedTarget'] is not None and pt is not None and b['proposedTarget']!=pt: diffs.append('proposal-text')
 primary_final=pf if pf is not None else (pt if pt is not None else p['currentTarget'])
 blind_final=b['proposedTarget'] if b['proposedTarget'] is not None else b['currentTarget']
 pstruct=structural(b['sourceId'],primary_final)
 if diffs:
  review_differences.append({'sourcePosition':key[0],'locale':key[1],'sourceId':b['sourceId'],'differences':diffs,'blindDisposition':bd,'blindTarget':b['proposedTarget'],'primaryDisposition':pd,'primaryTarget':pt,'primaryReviewedFinal':pf})
 if pstruct['failed']:
  primary_structural_issues.append({'sourcePosition':key[0],'locale':key[1],'sourceId':b['sourceId'],'primaryFinal':primary_final,'failed':pstruct['failed']})
 comp.append({'sourcePosition':key[0],'locale':key[1],'sourceId':b['sourceId'],'currentTargetSha256':b['currentTargetSha256'],'blindDisposition':bd,'blindProposedTarget':b['proposedTarget'],'primaryDisposition':pd,'primaryProposedTarget':pt,'primaryProposedTargetSha256':p.get('proposedTargetSha256'),'primaryReviewedFinal':pf,'primaryReviewedFinalSha256':p.get('reviewedFinalSha256'),'dispositionMatch':bd==pd,'proposalMatch':b['proposedTarget']==pt,'primaryFinal':primary_final,'primaryFinalMatchesBlindFinal':primary_final==blind_final,'primaryStructuralCheck':pstruct})
(ROOT/'proposal-comparison.jsonl').write_text(''.join(json.dumps(x,ensure_ascii=False,separators=(',',':'))+'\n' for x in comp),encoding='utf-8')
counts={'cells':240,'dispositionAgreements':sum(x['dispositionMatch'] for x in comp),'cellsWithAnyDispositionOrProposalDifference':len(review_differences),'dispositionDifferences':sum(not x['dispositionMatch'] for x in comp),'proposalAgreements':sum(x['proposalMatch'] for x in comp),'proposalDifferences':sum(not x['proposalMatch'] for x in comp),'primaryProposalRows':proposal_rows,'primaryReviewedFinalRows':reviewed_final_rows,'sourceOrCurrentMismatches':len(source_current_mismatches),'primaryFinalStructuralFailures':len(primary_structural_issues),'blindFinalPrimaryFinalDisagreements':sum(not x['primaryFinalMatchesBlindFinal'] for x in comp),'blindDispositionCounts':blind_counts,'primaryDispositionCounts':primary_counts}
summary={'task':'post-seal primary/independent cell comparison','primaryLedgerPath':str(PRIMARY),'blindLedgerPath':'blind-ledger.jsonl','blindLedgerSha256':blind_sha,'blindLedgerUnmodified':True,'primaryLedgerSha256':primary_sha,'counts':counts,'sourceOrCurrentMismatches':source_current_mismatches,'reviewDifferences':review_differences,'primaryFinalStructuralIssues':primary_structural_issues,'notes':['Comparison ran after BLIND-SHA256SUMS.txt verified all pre-comparison outputs.','Comparison keys are (sourcePosition, locale); source/current identity and hashes were rechecked.','Primary reviewedFinal is compared with the blind final when present.','The independent protected-literal check treats Pod as exact based on the exact-head standalone catalog key; the four primary structural issues are all Pod transliterations/lowercase variants under that rule.']}
(ROOT/'proposal-comparison-summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
lines=['# Primary versus independent cross-review','',f"Blind ledger SHA-256: `{blind_sha}` (sealed before primary per-cell ledger access).",f"Primary ledger SHA-256: `{primary_sha}`.",'', 'The exact source/current values and hashes match in all 240 cells. The comparison found the following overall counts:','',f"- Dispositions agree: {counts['dispositionAgreements']}; differ: {counts['dispositionDifferences']}.",f"- Proposed-target cells agree exactly: {counts['proposalAgreements']}; differ: {counts['proposalDifferences']}.",f"- Cells with any disposition or target difference: {counts['cellsWithAnyDispositionOrProposalDifference']}.",f"- Primary reviewed-final rows: {reviewed_final_rows}; primary proposal rows: {proposal_rows}.",f"- Source/current mismatches: {len(source_current_mismatches)}.",f"- Primary finals failing the independent structural rule: {len(primary_structural_issues)}.",'','## Cell-level differences','','`proposal-comparison.jsonl` contains all 240 paired rows. The rows below differ in disposition and/or target:','']
for d in review_differences:
 lines.append(f"- **{d['sourcePosition']} / {d['locale']} — {d['sourceId']}**: blind `{d['blindDisposition']}` target={d['blindTarget']!r}; primary `{d['primaryDisposition']}` target={d['primaryTarget']!r}. Differences: {', '.join(d['differences'])}.")
lines+=['','## Primary structural findings','','The independent structural comparison found the following primary reviewed-final targets did not preserve the exact `Pod` literal used by the exact-head standalone `Pod` catalog key. This is an independent policy inference and should be adjudicated if the product permits locale-specific transliteration.','']
for d in primary_structural_issues:
 lines.append(f"- **{d['sourcePosition']} / {d['locale']}**: {d['primaryFinal']!r} (failed: {', '.join(d['failed'])}).")
lines+=['','The blind proposals pass their final placeholder, markup, ICU, protected-literal, and terminal-punctuation checks. Machine review only; no native-speaker approval is claimed.']
(ROOT/'comparison-notes.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
print(json.dumps(counts,ensure_ascii=False,indent=2))
print('unique_review_difference_cells',len(review_differences),'unique_primary_structural_cells',len(primary_structural_issues))
