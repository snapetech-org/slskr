#!/usr/bin/env python3
"""Create the primary semantic review for the sealed W1583-W1602 input."""
import hashlib, importlib.util, json, subprocess
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
P=Path(__file__).resolve().parent; ROOT=P.parent; INPUT=ROOT/'candidate-free-input'
HEAD='e1ccc3d6509baf957f3039046e5b66dda3ae15d0'; TREE='d7c7aa967cb7faf51a8211a397859feebe8129b8'
LOCS=['es','zh-Hans','hi','de','ja','fr','pt-BR','ar','ko','zh-Hant','vi','id']; START,END=1583,1602
spec=importlib.util.spec_from_file_location('schema_helper',INPUT/'candidate-free-schema-helper.py'); h=importlib.util.module_from_spec(spec); spec.loader.exec_module(h)
sha=h.sha; canon=h.canon
# Only the three reviewed cell-level changes are proposals; every other cell accepts the pinned current value.
PROPOSALS={
 (1590,'zh-Hant'):('propose-correction','無法載入網格統計資料',
  'The current 統計訊息 means statistics messages, while this caller loads the mesh statistics data. The same locale uses 統計資料 in its adjacent mesh-statistics label and in related statistics errors.','high'),
 (1592,'zh-Hant'):('propose-refinement','無法載入待處理的請求',
  '載入 is the established Traditional Chinese form throughout this catalog. The current 加載 is a Simplified-style form for this Traditional Chinese locale.','high'),
 (1595,'vi'):('propose-correction','Không thể tải số liệu thống kê xuất bản của pod:',
  'The current nhóm means a generic group. This caller reports publishing statistics for the product pod; nearby Vietnamese pod messages retain the feature term pod.','moderate'),
}
RESOURCE={1583:'forwarding status',1584:'group members',1585:'joined rooms',1586:'library health data',1587:'logs',1588:'manifest',1589:'membership statistics',1590:'mesh statistics',1591:'metrics',1592:'pending requests',1593:'pod channel messages',1594:'pod members',1595:'pod publishing statistics',1596:'pods',1597:'room',1598:'room list',1599:'routing statistics',1600:'saved conversations',1601:'searches',1602:'security data'}

def writej(path,obj): path.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def writejl(path,rows): path.write_text(''.join(canon(x)+'\n' for x in rows),encoding='utf-8')
def j(path): return json.loads(path.read_text(encoding='utf-8'))
def jl(path): return [json.loads(s) for s in path.read_text(encoding='utf-8').splitlines() if s]

def main():
 subprocess.check_call(['python3',str(INPUT/'verify-candidate-free.py')])
 manifest=j(INPUT/'manifest.json'); assert (manifest['head'],manifest['tree'])==(HEAD,TREE)
 cells=jl(INPUT/'current-target-cells.jsonl'); contexts={x['position']:x for x in jl(INPUT/'source-contexts.jsonl')}
 rows=[]; proposals=[]; holds=[]
 for cell in cells:
  p,l=cell['position'],cell['locale']; key=(p,l); source=cell['sourceKey']; context=contexts[p]
  if key in PROPOSALS:
   disp,target,reason,confidence=PROPOSALS[key]
  else:
   disp='accept-current'; target=cell['currentTarget']; confidence='moderate'
   callers=', '.join(sorted({c['path'] for c in context['callers']}))
   reason=f"The localized wording reports that {RESOURCE[p]} could not be loaded, matching the production caller's error or status context ({callers})."
   if source.endswith(':'):
    reason+=' The target retains the trailing colon used before caller-supplied details.'
   if p in (1593,1594,1595,1596):
    reason+=' The product pod term is retained or rendered consistently with this feature context.'
   if p==1590:
    reason+=' The mesh page uses this label for mesh statistics data.'
  if disp not in ('accept-current','propose-correction','propose-refinement','text-free-hold'): raise RuntimeError('invalid disposition')
  target_hash=sha(target) if target is not None else None
  st,tt=h.toks(source),h.toks(target) if target is not None else ([],[],[],[])
  token_ok=(st[0]==tt[0] and st[1]==tt[1] and st[2]==tt[2] and all(x in tt[3] for x in st[3])) if target is not None else False
  if target is not None and not token_ok: raise RuntimeError(f'token integrity failed for {p}/{l}')
  row={'position':p,'locale':l,'sourceKey':source,'sourceKeySha256':cell['sourceKeySha256'],'sourceContextSha256':cell['sourceContextSha256'],
   'callerCount':cell['callerCount'],'callerPaths':sorted({c['path'] for c in context['callers']}),'currentTarget':cell['currentTarget'],'currentTargetSha256':cell['currentTargetSha256'],
   'disposition':disp,'selectedTarget':target,'selectedTargetSha256':target_hash,'reason':reason,'confidence':confidence,
   'placeholderSequencePreserved':target is not None and st[0]==tt[0],'markupPreserved':target is not None and st[1]==tt[1],
   'numericTokensPreserved':target is not None and st[2]==tt[2],'protectedLiteralsPreserved':target is not None and all(x in tt[3] for x in st[3])}
  rows.append(row)
  if disp in ('propose-correction','propose-refinement'):
   proposals.append({k:row[k] for k in ('position','locale','sourceKeySha256','sourceContextSha256','currentTargetSha256','selectedTarget','selectedTargetSha256','disposition','reason','confidence')})
  elif disp=='text-free-hold':
   holds.append({'position':p,'locale':l,'sourceKeySha256':cell['sourceKeySha256'],'sourceContextSha256':cell['sourceContextSha256'],
    'currentTargetSha256':cell['currentTargetSha256'],'reason':reason,'confidence':confidence})
 writejl(P/'primary-ledger.jsonl',rows); writejl(P/'proposals.jsonl',proposals); writejl(P/'holds.jsonl',holds)
 counts={d:sum(x['disposition']==d for x in rows) for d in ('accept-current','propose-correction','propose-refinement','text-free-hold')}
 summary={'artifact':'slskR PR #209 W1583-W1602 primary semantic review','repository':'snapetech-org/slskR','pullRequest':209,'head':HEAD,'tree':TREE,
  'candidateFreeInputChecksumListSha256':sha((INPUT/'SHA256SUMS.txt').read_bytes()),'sourceCount':20,'localeCount':12,'cellCount':len(rows),'counts':counts,
  'proposalCount':len(proposals),'holdCount':len(holds),'allCellRowsHaveSourceAndCurrentHashes':True,'placeholdersMarkupNumbersProtectedLiteralsReviewed':True,
  'nativeSpeakerSignoff':False,'browserReviewPerformed':False,'createdAtUtc':datetime.now(timezone.utc).isoformat(timespec='seconds')}
 writej(P/'SUMMARY.json',summary)
 (P/'README.md').write_text(f'''# slskR PR #209 W1583-W1602 primary review\n\nThis packet reviews all 240 locale cells from the sealed candidate-free input at {INPUT}. Input checksum-list SHA-256: {summary['candidateFreeInputChecksumListSha256']}. The pinned PR head/tree are {HEAD} / {TREE}.\n\nThe review records accept-current decisions and three cell-specific correction/refinement proposals. Counts: {counts}. Every selected text preserves the source placeholder sequence, markup tags, numeric tokens, and protected literals.\n\nThis is a primary semantic review grounded in the pinned source keys, production caller contexts, current catalog values, and local terminology. It does not include native-speaker signoff or browser review.\n''',encoding='utf-8')
 sums=[f'{sha((P/n).read_bytes())}  {n}' for n in sorted(x.name for x in P.iterdir() if x.is_file() and x.name!='SHA256SUMS.txt')]
 (P/'SHA256SUMS.txt').write_text('\n'.join(sums)+'\n',encoding='utf-8')
 print(json.dumps(summary,ensure_ascii=False,indent=2))
if __name__=='__main__': main()
