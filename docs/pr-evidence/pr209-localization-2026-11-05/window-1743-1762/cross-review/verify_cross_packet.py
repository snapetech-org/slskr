#!/usr/bin/env python3
"""Verify cross-review records against candidate-free, primary, and blind packets."""
import hashlib,json,subprocess,sys
from pathlib import Path
BASE=Path(__file__).resolve().parent
ROOT=BASE.parent
CF=ROOT/'candidate-free-input'
PRIMARY=ROOT/'primary-review'
BLIND=(ROOT.parent/'slskr-pr209-w1743-1762-independent-blind-20261105').resolve()
LOCALES=['es','zh-Hans','hi','de','ja','fr','pt-BR','ar','ko','zh-Hant','vi','id']

def sha(data):
 if isinstance(data,str): data=data.encode('utf-8')
 return hashlib.sha256(data).hexdigest()
def canon(value): return json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':'))
def jsonl(path): return [json.loads(x) for x in path.read_text(encoding='utf-8').splitlines() if x.strip()]
def require(condition,message):
 if not condition: raise ValueError(message)
def verify_sums(directory,filename,expected):
 seen=set()
 for line in (directory/filename).read_text(encoding='utf-8').splitlines():
  expected_hash,rel=line.split('  ',1); path=(directory/rel).resolve()
  require(path.parent==directory.resolve(),f'checksum escapes packet: {directory}/{rel}')
  require(path.is_file() and sha(path.read_bytes())==expected_hash,f'checksum mismatch: {directory}/{rel}')
  seen.add(rel)
 require(seen==set(expected),f'checksum coverage mismatch: {directory}')
def run_verifier(directory,filename):
 result=subprocess.run([sys.executable,str(directory/filename)],cwd=directory,capture_output=True,text=True,check=True)
 require('"result": "PASS"' in result.stdout,f'{filename} failed to report PASS')
 return result.stdout
def main():
 verify_sums(BASE,'SHA256SUMS.txt',{'README.md','manifest.json','cross-review-ledger.jsonl','active-hold-cross-reattestation.jsonl','verify_cross_packet.py'})
 run_verifier(CF,'verify_candidate_free.py')
 run_verifier(PRIMARY,'verify_primary_review.py')
 run_verifier(BLIND,'verify_blind_packet.py')
 m=json.loads((BASE/'manifest.json').read_text(encoding='utf-8'))
 H='ccbc3dc721c1cbd225d4e512f4f0af4c80476620';T='075d1b72a2fd080404ebec19d354cb863638df21'
 require(m['head']==H and m['tree']==T,'cross head/tree pin mismatch')
 require(json.loads((CF/'manifest.json').read_text())['head']==H,'candidate-free head mismatch')
 require(json.loads((PRIMARY/'manifest.json').read_text())['head']==H,'primary head mismatch')
 require(json.loads((BLIND/'review-manifest.json').read_text())['head']==H,'blind head mismatch')
 cells={(r['position'],r['locale']):r for r in jsonl(CF/'current-target-cells.jsonl')}
 sources={r['position']:r for r in jsonl(CF/'source-contexts.jsonl')}
 pri={(r['position'],r['locale']):r for r in jsonl(PRIMARY/'primary-review.jsonl')}
 bli={(r['position'],r['locale']):r for r in jsonl(BLIND/'blind-review-ledger.jsonl')}
 rows=jsonl(BASE/'cross-review-ledger.jsonl')
 require(len(cells)==len(pri)==len(bli)==len(rows)==240,'cell count mismatch')
 require(len({(r['position'],r['locale']) for r in rows})==240,'duplicate cross cell')
 require({r['position'] for r in rows}==set(range(1743,1763)),'position coverage mismatch')
 require({r['locale'] for r in rows}==set(LOCALES),'locale coverage mismatch')
 dispositions={}; agreements={}
 for r in rows:
  key=(r['position'],r['locale']); pos,loc=key;c=cells[key];s=sources[pos];p=pri[key];b=bli[key]
  for name,ok in (
   ('source hash',r['sourceKeySha256']==c['sourceKeySha256']),('target hash',r['currentTargetSha256']==c['currentTargetSha256']==p['currentTargetSha256']==b['currentTargetSha256']),
   ('caller context',r['callerCheck']['callerContextSha256']==s['callerContextSha256']==p['callerContextSha256']==b['callerContextSha256']),
   ('catalog path',r['catalogPath']==c['catalogPath']==p['catalogPath']==b['catalogPath']),
   ('catalog file sha',r['catalogFileSha256']==c['catalogFileSha256']==p['catalogFileSha256']==b['catalogFileSha256']),
   ('catalog blob',r['catalogGitBlob']==c['catalogGitBlob']==p['catalogGitBlob']==b['catalogGitBlob']),
   ('primary disposition',r['primaryDisposition']==p['decision']),('blind disposition',r['blindDisposition']==b['decision'])):
   require(ok,f'{name} mismatch {key}')
  require(r['currentTargetTextIncluded'] is False and 'currentTarget' not in r,'cross packet copied current target text')
  is_hash=pos in (1754,1755)
  require(r['hashOnly'] is is_hash,f'hash-only flag mismatch {key}')
  if is_hash:
   require(r['crossDisposition']=='hold' and r['agreementStatus']=='agree_hold','callerless disposition mismatch')
   require('sourceKey' not in r and r['crossRecommendationTextIncluded'] is False,'callerless strings must remain omitted')
   require(r['callerCheck']['status']=='unresolved_hash_only' and r['tokenCheck']['status']=='omitted_hash_only','callerless evidence must remain hash-only')
   require(c['targetTextIncluded'] is False and 'currentTarget' not in c,'candidate-free callerless text unexpectedly present')
  else:
   require(r['sourceKey']==c['sourceKey'],'source key mismatch')
   require(r['callerCheck']['status']=='verified' and r['callerCheck']['callerCount']==s['productionCallerCount']>0,'caller verification missing')
   require(r['callerCheck']['occurrenceCount']==s['callerOccurrenceCount'],'caller occurrence mismatch')
   require(r['callerCheck']['callerPinsSha256']==sha(canon(s['callers'])),'caller pins hash mismatch')
   variants=c['targetTokenVariants'];ta=r['tokenCheck']
   require(ta['status']=='verified' and ta['variantCount']==len(variants),'token audit count mismatch')
   require(ta['placeholderSequenceMatches']==all(x['placeholderSequenceMatches'] for x in variants),'placeholder sequence check mismatch')
   require(ta['markupMatches']==all(x['markupMatches'] for x in variants),'markup check mismatch')
   require(ta['numericTokensMatch']==all(x['numericTokensMatch'] for x in variants),'numeric token check mismatch')
   require(ta['protectedLiteralsMatch']==all(x['protectedLiteralsMatch'] for x in variants),'protected literal check mismatch')
   target_only=sorted({t for x in variants for t in x.get('targetProtectedLiterals',[]) if t not in c.get('sourceProtectedLiterals',[])})
   require(ta['targetOnlyProtectedLiterals']==target_only,'target-only literal report mismatch')
   require(ta['targetTokenVariantsSha256']==sha(canon(variants)),'target token signature hash mismatch')
   require(ta['blindTokenCheckSha256']==sha(canon(b.get('tokenCheck'))),'blind token check hash mismatch')
   require(ta['blindAdditionalLiteralChecksSha256']==sha(canon(b.get('additionalExactLiteralChecks'))),'blind literal check hash mismatch')
   require(ta['blindAdditionalLiteralChecksPreserved']==all(v is True for k,v in (b.get('additionalExactLiteralChecks') or {}).items() if k.endswith('Preserved') or k.endswith('CasePreserved')),'blind exact literal check failed')
  require(r['crossDisposition'] in ('accept-current','correction','refinement','hold'),'unknown cross disposition')
  dispositions[r['crossDisposition']]=dispositions.get(r['crossDisposition'],0)+1
  agreements[r['agreementStatus']]=agreements.get(r['agreementStatus'],0)+1
  if r['crossDisposition'] in ('correction','refinement'):
   require(isinstance(r.get('crossRecommendation'),str) and r['crossRecommendation'],'cross recommendation missing')
   require(r.get('crossRecommendationSha256')==sha(r['crossRecommendation']),'cross recommendation hash mismatch')
   source=r['recommendationResolution']
   if source=='primary': require(r['crossRecommendation']==p.get('recommendedTarget'),'primary recommendation resolution mismatch')
   elif source=='blind': require(r['crossRecommendation']==b.get('recommendedTarget'),'blind recommendation resolution mismatch')
   elif source=='same': require(p.get('recommendedTarget')==b.get('recommendedTarget')==r['crossRecommendation'],'same recommendation mismatch')
   else: require(source=='none' or source=='cross-adjudicated','unknown recommendation resolution')
  else:
   require(r['crossRecommendationTextIncluded'] is False and 'crossRecommendation' not in r,'unexpected cross recommendation')
 require(dispositions=={'accept-current':182,'correction':7,'refinement':27,'hold':24},f'cross disposition totals mismatch: {dispositions}')
 require(agreements=={'agree_accept':182,'override_blind':21,'override_primary':1,'agree_revise':12,'agree_hold':24},f'agreement totals mismatch: {agreements}')
 require(dispositions==m['crossDispositionCounts'] and agreements==m['agreementStatusCounts'],'manifest counts mismatch')
 # Continuity across candidate-free, primary, and blind packets.
 hc=jsonl(CF/'active-hold-reattestation.jsonl')[0]
 hp=jsonl(PRIMARY/'active-hold-reattestation.jsonl')[0]
 hb=jsonl(BLIND/'preserved-active-holds.jsonl')[0]
 ho=jsonl(BASE/'active-hold-cross-reattestation.jsonl')[0]
 require(all(x['holdId']=='1719::id' for x in (hc,hp,hb,ho)),'active hold ID mismatch')
 for x in (hp,hb,ho): require(x['currentTargetSha256']==hc['currentTargetSha256'],'active hold target hash mismatch')
 for x in (hp,hb,ho): require(x.get('currentSourceContextSha256')==hc['currentSourceContextSha256'],'active hold context mismatch')
 require(ho['hashOnly'] is True and ho['textIncluded'] is False,'active hold redaction mismatch')
 require(not any(k in ho for k in ('sourceKey','currentTarget','targetText','crossRecommendation')),'active hold text present')
 print(json.dumps({'result':'PASS','outputChecksummedFiles':5,'candidateFreeCells':240,'blindCells':240,'primaryCells':240,'crossCells':240,'crossDispositions':dispositions,'agreements':agreements,'callerlessHashOnlyCells':24,'activeHoldHashOnly':'1719::id'},ensure_ascii=False))
if __name__=='__main__':
 try: main()
 except Exception as exc:
  print(json.dumps({'result':'FAIL','error':str(exc)},ensure_ascii=False),file=sys.stderr)
  raise
