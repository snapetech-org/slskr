#!/usr/bin/env python3
"""Verify W1583-W1602 primary review against the sealed candidate-free input."""
import hashlib,json,re,subprocess
from collections import Counter
from pathlib import Path
P=Path(__file__).resolve().parent; INPUT=P.parent/'candidate-free-input'
HEAD='e1ccc3d6509baf957f3039046e5b66dda3ae15d0'; TREE='d7c7aa967cb7faf51a8211a397859feebe8129b8'
LOCS=['es','zh-Hans','hi','de','ja','fr','pt-BR','ar','ko','zh-Hant','vi','id']; START,END=1583,1602
sha=lambda x:hashlib.sha256(x.encode() if isinstance(x,str) else x).hexdigest()
def j(path): return json.loads(path.read_text(encoding='utf-8'))
def jl(path): return [json.loads(s) for s in path.read_text(encoding='utf-8').splitlines() if s]
def toks(s):
 p=re.findall(r'\{[A-Za-z][A-Za-z0-9_]*\}',s); m=re.findall(r'</?[A-Za-z][^>]*>',s); n=re.findall(r'(?<![A-Za-z])\d+(?:[.,]\d+)?%?(?![A-Za-z])',s); z=[]
 for x in re.findall(r'(?<![A-Za-z0-9])(?:[A-Z]{2,}[A-Z0-9]*|ffmpeg|Chromaprint|Soulseek|Spotify|YouTube|Pushbullet|Matrix|WebSocket|OpenAI)(?![A-Za-z0-9])',s):
  if x not in z:z.append(x)
 return p,m,n,z
subprocess.check_call(['python3',str(INPUT/'verify-candidate-free.py')])
im=j(INPUT/'manifest.json'); assert (im['head'],im['tree'])==(HEAD,TREE)
sums={}
for line in (P/'SHA256SUMS.txt').read_text(encoding='utf-8').splitlines():
 d,n=line.split(None,1); n=n.lstrip('* '); assert n not in sums; sums[n]=d
actual={x.name for x in P.iterdir() if x.is_file() and x.name!='SHA256SUMS.txt'}; assert set(sums)==actual
for n,d in sums.items(): assert sha((P/n).read_bytes())==d,n
ledger=jl(P/'primary-ledger.jsonl'); proposals=jl(P/'proposals.jsonl'); holds=jl(P/'holds.jsonl'); cells=jl(INPUT/'current-target-cells.jsonl')
assert len(ledger)==len(cells)==240
assert [(x['position'],x['locale']) for x in ledger]==[(p,l) for p in range(START,END+1) for l in LOCS]
cellmap={(x['position'],x['locale']):x for x in cells}; bykey={(x['position'],x['locale']):x for x in ledger}; counts=Counter(x['disposition'] for x in ledger)
assert set(counts)<={'accept-current','propose-correction','propose-refinement','text-free-hold'}
for row in ledger:
 c=cellmap[(row['position'],row['locale'])]; assert row['sourceKeySha256']==c['sourceKeySha256'] and row['sourceContextSha256']==c['sourceContextSha256']
 assert row['sourceKey']==c['sourceKey'] and row['currentTarget']==c['currentTarget'] and row['currentTargetSha256']==c['currentTargetSha256']==sha(row['currentTarget'])
 assert row['callerCount']==c['callerCount'] and isinstance(row['reason'],str) and row['reason'] and row['confidence'] in ('high','moderate','low','unknown')
 if row['disposition']=='accept-current': assert row['selectedTarget']==row['currentTarget'] and row['selectedTargetSha256']==row['currentTargetSha256']
 elif row['disposition'] in ('propose-correction','propose-refinement'): assert isinstance(row['selectedTarget'],str) and row['selectedTarget']!=row['currentTarget'] and row['selectedTargetSha256']==sha(row['selectedTarget'])
 else: assert row['selectedTarget'] is None and row['selectedTargetSha256'] is None
 if row['selectedTarget'] is not None:
  st,tt=toks(row['sourceKey']),toks(row['selectedTarget'])
  assert st[0]==tt[0] and st[1]==tt[1] and st[2]==tt[2] and all(x in tt[3] for x in st[3])
  assert row['placeholderSequencePreserved'] and row['markupPreserved'] and row['numericTokensPreserved'] and row['protectedLiteralsPreserved']
proposal_keys={(x['position'],x['locale']) for x in proposals}; expected={(x['position'],x['locale']) for x in ledger if x['disposition'] in ('propose-correction','propose-refinement')}
assert proposal_keys==expected and len(proposals)==len(expected)
for p in proposals:
 r=bykey[(p['position'],p['locale'])]
 for k in ('sourceKeySha256','sourceContextSha256','currentTargetSha256','selectedTarget','selectedTargetSha256','disposition','reason','confidence'): assert p[k]==r[k]
holdkeys={(x['position'],x['locale']) for x in holds}; expectedholds={(x['position'],x['locale']) for x in ledger if x['disposition']=='text-free-hold'}
assert holdkeys==expectedholds and len(holds)==len(expectedholds)
for h in holds: assert not any(k in h for k in ('sourceKey','currentTarget','selectedTarget','target','proposedTarget','text'))
s=j(P/'SUMMARY.json'); assert (s['head'],s['tree'],s['cellCount'],s['pullRequest'])==(HEAD,TREE,240,209)
assert s['counts']=={k:counts.get(k,0) for k in ('accept-current','propose-correction','propose-refinement','text-free-hold')}
assert s['proposalCount']==len(proposals) and s['holdCount']==len(holds) and s['candidateFreeInputChecksumListSha256']==sha((INPUT/'SHA256SUMS.txt').read_bytes())
assert s['nativeSpeakerSignoff'] is False and s['browserReviewPerformed'] is False
assert {(x['position'],x['locale']) for x in proposals}=={(1590,'zh-Hant'),(1592,'zh-Hant'),(1595,'vi')}
print(json.dumps({'result':'PASS','head':HEAD,'tree':TREE,'cells':len(ledger),'counts':s['counts'],'proposals':len(proposals),'holds':len(holds),
 'candidateFreeInputPinned':True,'tokenIntegrityPreserved':True,'checksummedFiles':len(sums),'nativeSpeakerSignoff':False,'browserReviewPerformed':False},ensure_ascii=False,indent=2))
