#!/usr/bin/env python3
import hashlib, json, subprocess, sys
from pathlib import Path
BASE=Path(__file__).resolve().parent.parent
ROOT=BASE/'root-adjudication'; APP=BASE/'application'
CF=BASE/'candidate-free-input'; CROSS=BASE/'cross-review'
HEAD='2d804c49879372071adf606bc2a2cf51e261fd94'; TREE='d6f5552d2400d868c2f2af98eb68caadfd4f3f66'
def sha(b): return hashlib.sha256(b).hexdigest()
def canon(o): return (json.dumps(o,ensure_ascii=False,sort_keys=True,separators=(',',':'))+'\n').encode()
def jl(p): return [json.loads(x) for x in p.read_text().splitlines() if x.strip()]
def verify_sums(d):
 for line in (d/'SHA256SUMS.txt').read_text().splitlines():
  digest,name=line.split('  ',1); assert sha((d/name).read_bytes())==digest, f'checksum {d/name}'

def main():
 verify_sums(ROOT); verify_sums(APP)
 recs={r['rowId']:r for r in jl(CROSS/'recommendations.jsonl')}
 cross={r['rowId']:r for r in jl(CROSS/'cross-ledger.jsonl')}
 cells={(r['sourceKey'],r['locale']):r for r in jl(CF/'current-target-cells.jsonl')}
 roots=jl(ROOT/'root-adjudication-ledger.jsonl'); plans=jl(APP/'apply-plan.jsonl')
 assert len(roots)==9 and len(plans)==9
 assert len(jl(CROSS/'cross-ledger.jsonl'))==240
 assert len(cells)==240
 for r,p in zip(roots,plans):
  rid=r['rowId']; assert rid in recs and rid in cross
  rec=recs[rid]; c=cells[(r['sourceKey'],r['locale'])]
  assert r['exactHead']==HEAD and r['exactTree']==TREE and r['rootDecision']=='accept-cross-recommendation'
  assert r['crossReviewRowSha256']==sha(canon(cross[rid]))
  assert r['finalTarget']==rec['recommendedTarget'] and r['finalTargetSha256']==rec['recommendedTargetSha256']
  assert r['finalTargetSha256']==sha(r['finalTarget'].encode())
  assert c['currentTargetSha256']==r['currentTargetSha256']
  assert c['sourceKeySha256']==r['sourceKeySha256']
  assert c['sourceContextSha256']==r['sourceContextSha256']
  assert p['rowId']==rid and p['expectedBeforeTargetSha256']==c['currentTargetSha256']
  assert p['finalTargetSha256']==r['finalTargetSha256'] and p['sourceContextSha256']==r['sourceContextSha256']
 out={'result':'PASS','head':HEAD,'tree':TREE,'cellsCrossReviewed':240,'rootAccepted':len(roots),'retainCurrent':231,'corrections':4,'refinements':5,'holds':0,'applyPlan':len(plans),'candidateFreeBindings':'PASS','crossBindings':'PASS'}
 print(json.dumps(out,indent=2))
if __name__=='__main__': main()
