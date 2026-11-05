#!/usr/bin/env python3
import argparse,hashlib,json,sys
from pathlib import Path
HEAD='f04b7f965aef79552d65d40a2eeb550e5e3b9cfa';TREE='85fe880023e55e055660fd17599c291edd24a1c6'
PRIMARY={'1683::es','1683::ko','1683::vi','1684::ko','1685::zh-Hant','1686::ko','1692::de','1694::zh-Hant'}
BLIND={'1683::ko','1684::ko','1685::zh-Hant','1686::ko','1692::de'}
SELECTED={'1683::es':'No se pudo iniciar la carga retroactiva desde el historial de búsqueda.','1683::ko':'검색 기록에서 백필을 시작하지 못했습니다.','1683::vi':'Không thể bắt đầu bổ sung dữ liệu từ lịch sử tìm kiếm.','1684::ko':'포드 게시를 취소하지 못했습니다:','1685::zh-Hant':'無法取消註冊 Pod。','1686::ko':'포드 등록을 취소하지 못했습니다:','1692::de':'Die Affinitäten der Mitglieder konnten nicht aktualisiert werden: {error}','1694::zh-Hant':'無法更新 Pod 探索資訊。'}
def hb(b):return hashlib.sha256(b).hexdigest()
def hv(v):return hashlib.sha256((v.encode() if isinstance(v,str) else json.dumps(v,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode())).hexdigest()
def jl(p):return [json.loads(x) for x in p.read_text(encoding='utf-8').splitlines() if x]
def keyed(rows):
 d={}
 for x in rows:
  k=(x['position'],x['locale'])
  if k in d:raise ValueError(f'duplicate cell {k}')
  d[k]=x
 return d
def sums(d):
 for line in (d/'SHA256SUMS.txt').read_text().splitlines():
  if line.strip():
   exp,name=line.split(None,1);name=name.lstrip('* ')
   if hb((d/name).read_bytes())!=exp:raise ValueError(f'checksum mismatch {d/name}')
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--input-dir',type=Path,required=True);ap.add_argument('--primary-dir',type=Path,required=True);ap.add_argument('--blind-dir',type=Path,required=True);ap.add_argument('--output-dir',type=Path,required=True);a=ap.parse_args()
 for d in (a.input_dir,a.primary_dir,a.blind_dir,a.output_dir):sums(d)
 im=json.loads((a.input_dir/'manifest.json').read_text());pm=json.loads((a.primary_dir/'manifest.json').read_text());seal=json.loads((a.blind_dir/'seal.json').read_text())
 if (im['head'],im['tree'])!=(HEAD,TREE) or (pm['exactHead'],pm['exactTree'])!=(HEAD,TREE) or seal['sourcePin']!={'head':HEAD,'tree':TREE}:raise ValueError('source pin mismatch')
 c=jl(a.input_dir/'current-target-cells.jsonl');ctx={x['position']:x for x in jl(a.input_dir/'source-contexts.jsonl')};p=jl(a.primary_dir/'ledger.jsonl');pp=jl(a.primary_dir/'proposals.jsonl');b=jl(a.blind_dir/'ledger.jsonl');o=jl(a.output_dir/'cross-ledger.jsonl');cm,pm,bm,om=map(keyed,(c,p,b,o))
 if not(len(cm)==len(pm)==len(bm)==len(om)==240) or not(set(cm)==set(pm)==set(bm)==set(om)):raise ValueError('expected same 240 unique cell keys')
 if [(x['position'],x['locale']) for x in o]!=[(pos,loc) for pos in range(1683,1703) for loc in im['localeOrder']]:raise ValueError('ledger order mismatch')
 if {x['cellId'] for x in pp}!=PRIMARY or {f"{x['position']}::{x['locale']}" for x in b if x['decision']=='propose'}!=BLIND:raise ValueError('proposal set mismatch')
 if {x['cellId'] for x in o if x['disposition']=='select-proposal'}!=PRIMARY:raise ValueError('selected cell set mismatch')
 for k,x in cm.items():
  pr,br,cr=pm[k],bm[k],om[k];s=ctx[x['position']]
  if hv(x['sourceKey'])!=x['sourceKeySha256'] or cr['sourceKey']!=x['sourceKey'] or cr['sourceKeySha256']!=x['sourceKeySha256']:raise ValueError(f'source key mismatch {k}')
  if x['sourceContextSha256']!=s['callerContextSha256'] or cr['sourceContextSha256']!=x['sourceContextSha256']:raise ValueError(f'context mismatch {k}')
  for f in ('sourceKeySha256','sourceContextSha256','catalogPath','catalogFileSha256','catalogGitBlob','currentTargetSha256'):
   if pr[f]!=x[f] or br[f]!=x[f] or cr[f]!=x[f]:raise ValueError(f'{f} mismatch {k}')
  if pr['exactHead']!=HEAD or pr['exactTree']!=TREE or cr['candidateFreeCellSha256']!=pr['candidateFreeCellSha256']:raise ValueError(f'head/cell binding mismatch {k}')
  if hv(x['currentTarget'])!=x['currentTargetSha256'] or cr['currentTarget']!=x['currentTarget'] or cr['currentTargetSha256']!=x['currentTargetSha256']:raise ValueError(f'current target mismatch {k}')
  if hv(cr['selectedTarget'])!=cr['selectedTargetSha256']:raise ValueError(f'selected hash mismatch {k}')
  ce=[{n:y[n] for n in ('path','line','lineText','lineSha256','contextStartLine','contextEndLine','contextSha256','fileBytes','fileSha256','gitBlob','literalOccurrenceCount')} for y in s['callers']]
  if cr['callers']!=ce or cr['callerReferenceCount']!=pr['callerReferenceCount'] or cr['callerOccurrenceCount']!=pr['callerOccurrenceCount']:raise ValueError(f'caller hash/evidence mismatch {k}')
  if any(not(v['placeholderMultisetMatches'] and v['markupMatches'] and v['numericTokensMatch']) for v in x['targetTokenVariants']):raise ValueError(f'token mismatch {k}')
  if cr['cellId'] in SELECTED:
   t=SELECTED[cr['cellId']]
   if cr['disposition']!='select-proposal' or cr['selectedTarget']!=t or not all(pr['recommendedTargetTokenChecks'].values()):raise ValueError(f'proposal mismatch {cr["cellId"]}')
   if pr.get('recommendedTarget') is not None and hv(pr['recommendedTarget'])!=pr['recommendedTargetSha256']:raise ValueError(f'primary proposal hash mismatch {cr["cellId"]}')
   if cr['cellId']=='1692::de':
    if br.get('proposal')!=t or cr['selectedProposalSource']!='blind (chosen over primary wording)':raise ValueError('German proposal selection mismatch')
   else:
    if pr.get('recommendedTarget')!=t or hv(t)!=pr['recommendedTargetSha256']:raise ValueError(f'primary proposal selection mismatch {cr["cellId"]}')
    if br['decision']=='propose' and br.get('proposal')!=t:raise ValueError(f'blind proposal not selected {cr["cellId"]}')
  elif cr['disposition']!='accept-current' or cr['selectedTarget']!=x['currentTarget']:raise ValueError(f'disposition mismatch {cr["cellId"]}')
  if cr['primaryReview']['decision']!=pr['decision'] or cr['primaryReview']['rationale']!=pr['reviewRationale'] or cr['blindReview']['decision']!=br['decision'] or cr['blindReview']['rationale']!=br['rationale']:raise ValueError(f'review evidence mismatch {k}')
 seq=[v for x in c for v in x['targetTokenVariants'] if not v['placeholderSequenceMatches']];prot=[v for x in c for v in x['targetTokenVariants'] if not v['protectedLiteralsMatch']]
 if len(seq)!=12 or len(prot)!=2 or any(not(v['markupMatches'] and v['numericTokensMatch']) for x in c for v in x['targetTokenVariants']):raise ValueError('token alert totals mismatch')
 sm=json.loads((a.output_dir/'summary.json').read_text());m=json.loads((a.output_dir/'manifest.json').read_text())
 if sm['dispositionCounts']!={'accept-current':232,'select-proposal':8,'hold':0} or m['cellCount']!=240:raise ValueError('summary count mismatch')
 for n,v in m['outputFileHashes'].items():
  if hb((a.output_dir/n).read_bytes())!=v['sha256']:raise ValueError(f'output hash mismatch {n}')
 print(json.dumps({'result':'PASS','head':HEAD,'tree':TREE,'cells':240,'acceptCurrent':232,'selectedProposals':8,'primaryProposals':8,'blindProposals':5,'callerReferences':21,'callerOccurrences':21,'callerFiles':13,'placeholderOrderDifferences':12,'protectedLiteralLocalizations':2,'markupOrNumericMismatches':0},indent=2))
if __name__=='__main__':
 try:main()
 except Exception as e:print(f'FAIL: {e}',file=sys.stderr);sys.exit(1)
