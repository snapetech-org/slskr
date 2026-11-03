#!/usr/bin/env python3
"""Portable integrity/completeness verifier for the blind W1423-W1442 review."""
import hashlib,json,re,sys
from collections import Counter
from pathlib import Path
root=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else Path(__file__).resolve().parent
def fail(s): raise SystemExit('FAIL: '+s)
def digest(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def j(p): return json.loads(p.read_text(encoding='utf-8'))
def jl(p): return [json.loads(s) for s in p.read_text(encoding='utf-8').splitlines() if s.strip()]
def tokens(s):
 ph=re.findall(r'\{[A-Za-z][A-Za-z0-9_]*\}',s); tags=re.findall(r'<\/?[A-Za-z][^>]*>',s)
 nums=re.findall(r'(?<![A-Za-z])\d+(?:[.,]\d+)?%?(?![A-Za-z])',s); prot=[]
 for m in re.finditer(r'(?<![A-Za-z0-9])(?:[A-Z]{2,}[A-Z0-9]*|ffmpeg|Chromaprint|Soulseek|Spotify|YouTube|Pushbullet|Matrix|WebSocket|OpenAI)(?![A-Za-z0-9])',s):
  if m.group(0) not in prot: prot.append(m.group(0))
 return ph,tags,nums,prot
sums=root/'SHA256SUMS'
if not sums.is_file(): fail('SHA256SUMS missing')
listed={}
for line in sums.read_text(encoding='utf-8').splitlines():
 if not line.strip(): continue
 a=line.split('  ',1)
 if len(a)!=2: fail('malformed SHA256SUMS line')
 listed[a[1]]=a[0]
for n,h in listed.items():
 p=root/n
 if not p.is_file() or digest(p)!=h: fail('checksum mismatch: '+n)
m=j(root/'manifest.json')
for f in m['files']:
 p=root/f['path']
 if not p.is_file() or p.stat().st_size!=f['bytes'] or digest(p)!=f['sha256']: fail('manifest mismatch: '+f['path'])
 if listed.get(f['path'])!=f['sha256']: fail('manifest/SHA256SUMS mismatch: '+f['path'])
L=jl(root/'review-ledger.jsonl'); H=jl(root/'prior-hold-reattestation.jsonl'); S=j(root/'review-summary.json')
if len(L)!=240 or len({(x['position'],x['locale']) for x in L})!=240: fail('240-cell coverage mismatch')
if {x['position'] for x in L}!=set(range(1423,1443)): fail('position coverage mismatch')
v=Counter(x['verdict'] for x in L)
if v!=Counter({'accept':205,'revise':35}): fail('decision counts mismatch')
if v['accept']!=S['decisionCounts']['accept'] or v['revise']!=S['decisionCounts']['revise']: fail('summary counts mismatch')
if len(H)!=35 or not all(x['hashMatches'] and x['priorCurrentTargetSha256']==x['recomputedCurrentTargetSha256'] for x in H): fail('35 carried hold hashes mismatch')
for x in L:
 if hashlib.sha256(x['currentTarget'].encode()).hexdigest()!=x['currentTargetSha256']: fail('current target hash mismatch')
 if x['verdict']=='revise' and hashlib.sha256(x['suggestedTarget'].encode()).hexdigest()!=x['suggestedTargetSha256']: fail('suggestion hash mismatch')
 st=tokens(x['sourceKey']); tt=tokens(x['suggestedTarget'] if x['verdict']=='revise' else x['currentTarget'])
 if st[:3]!=tt[:3] or not all(t in tt[3] for t in st[3]): fail('token-preservation mismatch')
# Cross-check against exact sealed candidate-free source if the sibling is available.
base=root.parent/'slskr-pr204-w1423-1442-primary-20261103'/'candidate-free-input'
if base.is_dir():
 bi=j(base/'manifest.json')
 if digest(base/'manifest.json')!=m['candidateFreeInputManifestSha256']: fail('candidate-free manifest pin mismatch')
 source={(x['position'],x['locale']):x for x in jl(base/'current-target-cells.jsonl')}
 if len(source)!=240: fail('candidate-free source coverage mismatch')
 for x in L:
  y=source[(x['position'],x['locale'])]
  if (x['sourceKey'],x['sourceKeySha256'],x['currentTarget'],x['currentTargetSha256'])!=(y['sourceKey'],y['sourceKeySha256'],y['currentTarget'],y['currentTargetSha256']): fail('candidate-free cell mismatch')
 prior={(x['position'],x['locale']):x for x in jl(base/'prior-hold-reattestation.jsonl')}
 if len(prior)!=35: fail('candidate-free hold coverage mismatch')
 for x in H:
  y=prior[(x['position'],x['locale'])]
  if x['priorCurrentTargetSha256']!=y['priorCurrentTargetSha256'] or x['recomputedCurrentTargetSha256']!=y['currentTargetSha256']: fail('candidate-free hold hash mismatch')
 print('OK: report checksums, 240 candidate-free cells, token preservation, and 35 carried-hold hashes')
else:
 print('OK: report checksums, 240-cell coverage, token preservation, and 35 carried-hold hashes; candidate-free packet not beside report')
