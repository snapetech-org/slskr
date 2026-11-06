#!/usr/bin/env python3
"""Create root primary semantic review for slskR PR #209 W1603-W1622."""
import importlib.util, json, sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
P=Path(__file__).resolve().parent; ROOT=P.parent; INPUT=ROOT/'candidate-free-input'
HEAD='eeb63f1e4e21d801f4a4e0393813b6e86a1ff7c8'; TREE='590ee410666905f68f601393b64a4798b0609181'
LOCS=['es','zh-Hans','hi','de','ja','fr','pt-BR','ar','ko','zh-Hant','vi','id']; START,END=1603,1622
sys.dont_write_bytecode=True
spec=importlib.util.spec_from_file_location('schema_helper',INPUT/'candidate-free-schema-helper.py'); h=importlib.util.module_from_spec(spec); spec.loader.exec_module(h)
sha,canon=h.sha,h.canon
PROPOSALS={
 (1608,'vi'):('propose-refinement','Không thể tải các lượt truyền',
  'The current “các mục truyền” reads as transfer items. This catalog uses “lượt truyền” for completed/filtered transfers, so this more clearly names the transfer records shown on the Transfers screen.','moderate'),
 (1611,'ko'):('propose-correction','검증 통계를 불러오지 못했습니다:',
  'The caller is PodMembershipVerificationPanel and appends a caller-supplied error after this label. 검증 is the precise technical term for verification here; the trailing colon keeps the source prefix structure.','moderate'),
 (1615,'ko'):('propose-refinement','멤버십을 게시하지 못했습니다:',
  'This localized prefix is followed by membership.error in the caller. Preserve the source colon so the appended detail remains attached as intended.','high'),
 (1617,'vi'):('propose-correction','Không thể xuất bản pod:',
  'The current “nhóm” means a generic group and loses the product-domain term pod. Related Vietnamese MediaCore labels retain “pod”; this caller publishes a Pod through DHT.','moderate'),
}
RESOURCE={1603:'share contents',1604:'share groups',1605:'shared collections',1606:'shares',1607:'transfer errors',1608:'transfers',1609:'transport status',1610:'user note',1611:'verification stats',
 1612:'settings persistence',1613:'descriptor publishing',1614:'membership publishing',1615:'membership publishing details',1616:'opinion publishing',1617:'pod publishing',1618:'shadow index queries',1619:'download queueing',
 1620:'nearby Atlas searches',1621:'nearby graph searches',1622:'nearby searches'}
def wj(path,x): path.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def wjl(path,xs): path.write_text(''.join(canon(x)+'\n' for x in xs),encoding='utf-8')
def j(path): return json.loads(path.read_text(encoding='utf-8'))
def jl(path): return [json.loads(s) for s in path.read_text(encoding='utf-8').splitlines() if s]
def main():
 import subprocess
 subprocess.check_call(['python3',str(INPUT/'verify-candidate-free.py')])
 manifest=j(INPUT/'manifest.json'); assert (manifest['head'],manifest['tree'])==(HEAD,TREE)
 cells=jl(INPUT/'current-target-cells.jsonl'); contexts={x['position']:x for x in jl(INPUT/'source-contexts.jsonl')}
 rows=[]; proposals=[]; holds=[]
 for cell in cells:
  p,l=cell['position'],cell['locale']; source=cell['sourceKey']; context=contexts[p]
  if (p,l) in PROPOSALS: disp,target,reason,confidence=PROPOSALS[(p,l)]
  else:
   disp='accept-current'; target=cell['currentTarget']; confidence='moderate'
   callers=', '.join(sorted({c['path'] for c in context['callers']}))
   reason=f"The localized wording reports that {RESOURCE[p]} could not be loaded or completed, matching the exact source and production caller context ({callers})."
   if source.endswith(':'):
    reason+=' The target retains the trailing colon used before caller-supplied details.'
   if p in (1613,1614,1615,1616,1617): reason+=' The wording matches the MediaCore publishing operation and preserves product-domain meaning.'
   if p in (1620,1621,1622): reason+=' The wording preserves the distinct Atlas, graph, or generic nearby-search meaning in its caller.'
  if disp not in ('accept-current','propose-correction','propose-refinement','text-free-hold'): raise RuntimeError('invalid disposition')
  target_hash=sha(target) if target is not None else None; st=h.toks(source); tt=h.toks(target) if target is not None else ([],[],[],[])
  token_ok=(st[0]==tt[0] and st[1]==tt[1] and st[2]==tt[2] and all(x in tt[3] for x in st[3])) if target is not None else False
  if target is not None and not token_ok: raise RuntimeError(f'token integrity failed for {p}/{l}')
  row={'position':p,'locale':l,'sourceKey':source,'sourceKeySha256':cell['sourceKeySha256'],'sourceContextSha256':cell['sourceContextSha256'],'callerCount':cell['callerCount'],
   'callerPaths':sorted({c['path'] for c in context['callers']}),'currentTarget':cell['currentTarget'],'currentTargetSha256':cell['currentTargetSha256'],'disposition':disp,'selectedTarget':target,
   'selectedTargetSha256':target_hash,'reason':reason,'confidence':confidence,'placeholderSequencePreserved':target is not None and st[0]==tt[0],
   'markupPreserved':target is not None and st[1]==tt[1],'numericTokensPreserved':target is not None and st[2]==tt[2],
   'protectedLiteralsPreserved':target is not None and all(x in tt[3] for x in st[3])}
  rows.append(row)
  if disp in ('propose-correction','propose-refinement'):
   proposals.append({k:row[k] for k in ('position','locale','sourceKeySha256','sourceContextSha256','currentTargetSha256','selectedTarget','selectedTargetSha256','disposition','reason','confidence')})
  elif disp=='text-free-hold':
   holds.append({'position':p,'locale':l,'sourceKeySha256':cell['sourceKeySha256'],'sourceContextSha256':cell['sourceContextSha256'],'currentTargetSha256':cell['currentTargetSha256'],'reason':reason,'confidence':confidence})
 wjl(P/'primary-ledger.jsonl',rows); wjl(P/'proposals.jsonl',proposals); wjl(P/'holds.jsonl',holds)
 counts={d:sum(x['disposition']==d for x in rows) for d in ('accept-current','propose-correction','propose-refinement','text-free-hold')}
 summary={'artifact':'slskR PR #209 W1603-W1622 primary semantic review','repository':'snapetech-org/slskR','pullRequest':209,'head':HEAD,'tree':TREE,
  'candidateFreeInputChecksumListSha256':sha((INPUT/'SHA256SUMS.txt').read_bytes()),'sourceCount':20,'localeCount':12,'cellCount':len(rows),'counts':counts,'proposalCount':len(proposals),'holdCount':len(holds),
  'allCellRowsHaveSourceAndCurrentHashes':True,'placeholdersMarkupNumbersProtectedLiteralsReviewed':True,'nativeSpeakerSignoff':False,'browserReviewPerformed':False,'createdAtUtc':datetime.now(timezone.utc).isoformat(timespec='seconds')}
 wj(P/'SUMMARY.json',summary)
 (P/'README.md').write_text(f'''# slskR PR #209 W1603-W1622 primary review

This primary review covers all 240 locale cells from the sealed candidate-free input at {INPUT}. Input checksum-list SHA-256: {summary['candidateFreeInputChecksumListSha256']}. The pinned PR head/tree are {HEAD} / {TREE}.

The review records accept-current decisions and four cell-specific correction/refinement proposals. Counts: {counts}. Selected values preserve the source placeholder sequence, markup, numeric tokens, and protected literals.

This is a machine-assisted primary semantic review grounded in the pinned source keys, exact production callers, current catalog values, and local terminology. It does not establish qualified native-speaker signoff or exact-head browser review.
''',encoding='utf-8')
 sums=[f'{sha((P/n).read_bytes())}  {n}' for n in sorted(x.name for x in P.iterdir() if x.is_file() and x.name!='SHA256SUMS.txt')]
 (P/'SHA256SUMS.txt').write_text('\n'.join(sums)+'\n',encoding='utf-8')
 print(json.dumps(summary,ensure_ascii=False,indent=2))
if __name__=='__main__': main()
