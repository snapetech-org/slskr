#!/usr/bin/env python3
"""Read-only verifier for the sealed W1763-W1782 primary review packet."""
import collections, hashlib, json, re, subprocess, sys
from pathlib import Path
OUT=Path(__file__).resolve().parent
INPUT=Path('/mnt/disks/scratch/task-scratch/slskr-pr209-w1763-1782-candidate-free-20261105/candidate-free-input')
WORKTREE=Path('/home/keith/Documents/code/.task-worktrees/localization-20261105/slskr-w1683')
HEAD='5191888071f54061a6012acdedfeb518a6cb3661'; TREE='d5728c24b54a06dda432afd2ef5f378206a6cb8f'
PROPOSAL_SHA='142119303f5883c209772ef4103b016314ba79bf6f5227cdee7b9f5954ae33a7'
LOCALES=['es','zh-Hans','hi','de','ja','fr','pt-BR','ar','ko','zh-Hant','vi','id']
def fail(s): raise SystemExit('FAIL: '+s)
def sha(b): return hashlib.sha256(b).hexdigest()
def j(p): return json.loads(p.read_text(encoding='utf-8'))
def jl(p): return [json.loads(x) for x in p.read_text(encoding='utf-8').splitlines() if x.strip()]
def check_sums(root,filename='SHA256SUMS.txt'):
 listed={}
 for line in (root/filename).read_text(encoding='utf-8').splitlines():
  digest,name=line.split('  ',1)
  if name in listed or not (root/name).is_file() or sha((root/name).read_bytes())!=digest: fail(f'checksum mismatch {root}/{name}')
  listed[name]=digest
 actual={p.relative_to(root).as_posix() for p in root.rglob('*') if p.is_file() and p.name!=filename}
 if actual!=set(listed): fail(f'checksum coverage mismatch {root}')
 return listed

def token_sig(s):
 return {'placeholders':re.findall(r'\{[A-Za-z][A-Za-z0-9_]*\}',s),'markup':re.findall(r'</?[A-Za-z][^>]*>',s),'numbers':re.findall(r'(?<![A-Za-z])\d+(?:[.,]\d+)?%?(?![A-Za-z])',s),'protected':list(dict.fromkeys(re.findall(r'(?<![A-Za-z0-9])(?:[A-Z]{2,}[A-Z0-9]*|ffmpeg|Chromaprint|Soulseek|Spotify|YouTube|Pushbullet|Matrix|WebSocket|OpenAI)(?![A-Za-z0-9])',s)))}
def manual_literals(source):
 out=[]
 if 'ContentID' in source: out.append('ContentID')
 if re.search(r'(?<![A-Za-z0-9])ID(?![A-Za-z0-9])',source): out.append('ID')
 return out
def check_target(source,target):
 a=token_sig(source); b=token_sig(target)
 req=manual_literals(source)
 return a['placeholders']==b['placeholders'] and a['markup']==b['markup'] and a['numbers']==b['numbers'] and a['protected']==b['protected'] and all(re.search(r'(?<![A-Za-z0-9])'+re.escape(t)+r'(?![A-Za-z0-9])',target) for t in req)

def main():
 if subprocess.check_output(['git','-C',str(WORKTREE),'rev-parse','HEAD'],text=True).strip()!=HEAD: fail('worktree head')
 if subprocess.check_output(['git','-C',str(WORKTREE),'rev-parse','HEAD^{tree}'],text=True).strip()!=TREE: fail('worktree tree')
 if subprocess.check_output(['git','-C',str(WORKTREE),'status','--porcelain=v1'],text=True)!='': fail('worktree dirty')
 input_sums=check_sums(INPUT)
 v=subprocess.run([sys.executable,'-B',str(INPUT/'verify_candidate_free.py')],capture_output=True,text=True)
 if v.returncode: fail('candidate-free verifier: '+v.stdout+v.stderr)
 m=j(INPUT/'manifest.json')
 if (m.get('head'),m.get('tree'),m.get('selectedPositions'),m.get('cellCount'))!=(HEAD,TREE,[1763,1782],240): fail('candidate-free pin/window')
 if sha((OUT/'independent-proposals.jsonl').read_bytes())!=PROPOSAL_SHA: fail('frozen independent proposal digest')
 builder=(OUT/'build_independent_proposals.py').read_text(encoding='utf-8')
 if "INPUT/'source-contexts.jsonl'" not in builder or "INPUT/'current-target-cells.jsonl').read" in builder: fail('independent proposal source-only builder audit')
 for source_name,output_name in [('manifest.json','input-manifest.json'),('SHA256SUMS.txt','input-SHA256SUMS.txt'),('source-contexts.jsonl','input-source-contexts.jsonl'),('selected-source-keys.txt','input-selected-source-keys.txt'),('localization-runtime-context.json','input-localization-runtime-context.json'),('active-hold-reattestation.jsonl','input-active-hold-reattestation.jsonl'),('source-window-boundaries.jsonl','input-source-window-boundaries.jsonl'),('catalog-file-pins.json','input-catalog-file-pins.json'),('catalog-structure.jsonl','input-catalog-structure.jsonl')]:
  if (INPUT/source_name).read_bytes()!=(OUT/output_name).read_bytes(): fail('copied input mismatch '+source_name)
 pins=j(OUT/'input-pins.json')
 for key,value in [('head',HEAD),('tree',TREE),('candidateFreeManifestSha256',sha((INPUT/'manifest.json').read_bytes())),('candidateFreeChecksumListSha256',sha((INPUT/'SHA256SUMS.txt').read_bytes())),('currentTargetCellsSha256',sha((INPUT/'current-target-cells.jsonl').read_bytes())),('sourceContextsSha256',sha((INPUT/'source-contexts.jsonl').read_bytes())),('independentProposalSha256',PROPOSAL_SHA)]:
  if pins.get(key)!=value: fail('input pin '+key)
 proposals=jl(OUT/'independent-proposals.jsonl'); review=jl(OUT/'locale-review.jsonl'); sources=jl(INPUT/'source-contexts.jsonl'); current=jl(INPUT/'current-target-cells.jsonl')
 expected=[(pos,loc) for pos in range(1763,1783) for loc in LOCALES]
 for label,rows in [('proposal',proposals),('review',review),('candidate-free cells',current)]:
  if len(rows)!=240 or [(r['position'],r['locale']) for r in rows]!=expected: fail(label+' coverage/order')
 pby={(r['position'],r['locale']):r for r in proposals}; cby={(r['position'],r['locale']):r for r in current}
 counts=collections.Counter(); official=collections.Counter(); manual_mismatch=0; manual_only=0; union_bad=0; final_bad=0
 for r in review:
  k=(r['position'],r['locale']); p=pby[k]; c=cby[k]
  for field in ['sourceKey','sourceKeySha256','sourceContextSha256']:
   if r[field]!=p[field] or r[field]!=c[field]: fail(f'{field} join {k}')
  if r['currentTarget']!=c['currentTarget'] or r['currentTargetSha256']!=c['currentTargetSha256']: fail('current target pin '+str(k))
  if r['independentProposal']!=p['proposedTarget'] or r['independentProposalSha256']!=p['proposedTargetSha256'] or r['independentProposalLedgerSha256']!=PROPOSAL_SHA: fail('proposal join '+str(k))
  if not p.get('tokenPreserved') or not check_target(r['sourceKey'],p['proposedTarget']): fail('independent proposal token preservation '+str(k))
  if r['decision'] not in ('correct','retain'): fail('decision enum '+str(k))
  expected_final=p['proposedTarget'] if r['decision']=='correct' else c['currentTarget']
  if r['finalTarget']!=expected_final or r['finalTargetSha256']!=sha(expected_final.encode()): fail('final selection/hash '+str(k))
  if not check_target(r['sourceKey'],r['finalTarget']): fail('final token preservation '+str(k))
  counts[r['decision']]+=1
  variants=c['targetTokenVariants']
  bad={
   'placeholder':not all(v['placeholderSequenceMatches'] for v in variants),
   'markup':not all(v['markupMatches'] for v in variants),
   'numeric':not all(v['numericTokensMatch'] for v in variants),
   'protected':not all(v['protectedLiteralsMatch'] for v in variants)}
  for key,val in bad.items(): official[key]+=val
  current_manual_bad=not all(re.search(r'(?<![A-Za-z0-9])'+re.escape(t)+r'(?![A-Za-z0-9])',c['currentTarget']) for t in manual_literals(r['sourceKey']))
  manual_mismatch+=current_manual_bad
  manual_only+=current_manual_bad and not any(bad.values())
  union_bad+=any(bad.values()) or current_manual_bad
  final_bad+=not check_target(r['sourceKey'],r['finalTarget'])
 if counts!={'correct':105,'retain':135}: fail('action counts')
 if official!=collections.Counter({'numeric':2,'protected':3}): fail('source token mismatch totals '+repr(official))
 if (manual_mismatch,manual_only,union_bad,final_bad)!=(18,15,20,0): fail('manual/final token totals')
 sm=j(OUT/'summary.json')
 if sm.get('actions')!=dict(counts) or sm.get('currentTokenAudit',{}).get('allCurrentTokenMismatchCells')!=union_bad or sm.get('finalTokenMismatchCells')!=0: fail('summary totals')
 hold=jl(OUT/'hold-continuity.jsonl'); original_hold=jl(INPUT/'active-hold-reattestation.jsonl')
 if len(hold)!=1 or hold!=original_hold or hold[0].get('holdId')!='1719::id' or hold[0].get('textIncluded') is not False: fail('hash-only hold continuity')
 if any(k.lower() in ('target','currenttarget','translation','text') for k in hold[0]): fail('hold target text leakage')
 boundaries=jl(INPUT/'source-window-boundaries.jsonl'); nxt=next(x for x in boundaries if x['boundary'] and x['position']==1783)
 if j(OUT/'next-boundary.json')!={'nextWindowPosition':1783,'sourceKeySha256':nxt['sourceKeySha256'],'head':HEAD,'tree':TREE}: fail('next boundary pin')
 sr=j(OUT/'source-review.json')
 if (sr.get('head'),sr.get('tree'),sr.get('sourceCount'),sr.get('localeCount'),sr.get('cellCount'),sr.get('independentProposalSha256'))!=(HEAD,TREE,20,12,240,PROPOSAL_SHA): fail('source review summary pin')
 sums=check_sums(OUT)
 print(json.dumps({'result':'PASS','head':HEAD,'tree':TREE,'window':'W1763-W1782','cells':240,'corrections':counts['correct'],'retains':counts['retain'],'currentTokenMismatchCells':union_bad,'finalTokenMismatchCells':final_bad,'hashOnlyHold':'1719::id','nextBoundary':1783,'candidateFreeVerifier':'PASS','checksummedFiles':len(sums)},ensure_ascii=False,indent=2))
if __name__=='__main__': main()
