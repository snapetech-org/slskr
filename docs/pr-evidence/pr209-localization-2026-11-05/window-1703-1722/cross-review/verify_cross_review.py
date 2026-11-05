#!/usr/bin/env python3
import hashlib, json, re, subprocess, sys
from pathlib import Path

OUT = Path(__file__).resolve().parent
BASE = Path('/mnt/disks/scratch/task-scratch/slskr-pr209-w1703-1722-20261105')
CAND = BASE / 'candidate-free-input'
PRIMARY = BASE / 'primary-review'
BLIND = Path('/mnt/disks/scratch/task-scratch/slskr-pr209-w1703-1722-independent-blind-20261105')
REPO = Path('/home/keith/Documents/code/.task-worktrees/localization-20261105/slskr-w1683')
HEAD = '91e109efba44ad9e53fe9544648a0d907a2bef77'
TREE = '38db78228144da5fc50179addccf826662bf97de'
LOCALES = ['es','zh-Hans','hi','de','ja','fr','pt-BR','ar','ko','zh-Hant','vi','id']

def load_jsonl(path):
    return [json.loads(x) for x in path.read_text(encoding='utf-8').splitlines() if x.strip()]
def sha_file(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()
def checkmap():
    return {'candidate-free-verifier':'FAIL','primary-verifier':'FAIL','exact-pin':'FAIL','input-cell-pins':'FAIL',
      'canonical-240-cell-order':'FAIL','caller-contexts':'FAIL','recommendation-token-preservation':'FAIL',
      'manual-protected-literal':'FAIL','prior-holds-preserved':'FAIL','packet-checksums':'FAIL'}
checks=checkmap(); errors=[]
def mark(name, ok, detail=None):
    checks[name]='PASS' if ok else 'FAIL'
    if not ok: errors.append(detail or name)

cand_rows=load_jsonl(CAND/'current-target-cells.jsonl')
ctx_rows=load_jsonl(CAND/'source-contexts.jsonl')
p_rows=load_jsonl(PRIMARY/'ledger.jsonl')
b_rows=load_jsonl(BLIND/'blind-review.jsonl')
x_rows=load_jsonl(OUT/'cross-review.jsonl')
cand={(r['position'],r['locale']):r for r in cand_rows}
primary={(r['position'],r['locale']):r for r in p_rows}
blind={(r['position'],r['locale']):r for r in b_rows}
ctx={r['position']:r for r in ctx_rows}
out={(r['position'],r['locale']):r for r in x_rows}
expected=[(p,l) for p in range(1703,1723) for l in LOCALES]
mark('canonical-240-cell-order',len(x_rows)==240 and [(r['position'],r['locale']) for r in x_rows]==expected,'cross-review row order/count mismatch')
head=subprocess.check_output(['git','-C',str(REPO),'rev-parse','HEAD'],text=True).strip()
tree=subprocess.check_output(['git','-C',str(REPO),'rev-parse','HEAD^{tree}'],text=True).strip()
status=subprocess.check_output(['git','-C',str(REPO),'status','--porcelain'],text=True).strip()
mark('exact-pin',head==HEAD and tree==TREE and not status,'pinned worktree mismatch or dirty')
mark('input-cell-pins',len(cand)==len(primary)==len(blind)==len(out)==240 and set(cand)==set(primary)==set(blind)==set(out),'input/cross cell keys differ')
context_ok=len(ctx)==20 and sum(r['callerOccurrenceCount'] for r in ctx_rows)==30
for key,c in cand.items():
    p=primary[key]; b=blind[key]; x=out[key]
    context_ok=context_ok and p.get('sourceContextSha256')==c.get('sourceContextSha256') and b.get('sourceContextSha256')==c.get('sourceContextSha256') and x['evidencePins']['sourceContextSha256']==c.get('sourceContextSha256')
    if x['currentTarget']!=c['currentTarget'] or x['primaryRecommendedTarget']!=p.get('recommendedTarget',c['currentTarget']) or x['blindRecommendedTarget']!=b.get('recommendedTarget',c['currentTarget']):
        errors.append(f'cross row does not match input at {key}')
    if x['evidencePins']['sourceKeySha256']!=c['sourceKeySha256'] or x['evidencePins']['currentTargetSha256']!=c['currentTargetSha256'] or x['evidencePins']['catalogFileSha256']!=c['catalogFileSha256'] or x['evidencePins']['catalogGitBlob']!=c['catalogGitBlob']:
        errors.append(f'evidence pin mismatch at {key}')
mark('caller-contexts',context_ok and not any('source context' in e for e in errors),'caller context pins/count mismatch')

def placeholders(text): return re.findall(r'\{([A-Za-z][A-Za-z0-9_]*)\}',text or '')
def markup(text): return re.findall(r'</?[A-Za-z][^>]*>',text or '')
def numbers(text): return re.findall(r'\d+(?:[.,]\d+)?',text or '')
token_ok=True
for key,c in cand.items():
    x=out[key]; p=primary[key].get('recommendedTarget',c['currentTarget']); b=blind[key].get('recommendedTarget',c['currentTarget'])
    cross=x['crossRecommendedTarget'] if x['crossRecommendedTarget'] is not None else c['currentTarget']
    targets=[c['currentTarget'],p,b,cross]
    src_ph=c['sourcePlaceholders']; src_markup=c['sourceMarkupTags']; src_nums=c['sourceNumericTokens']
    if any(sorted(placeholders(t))!=sorted(src_ph) or markup(t)!=src_markup or numbers(t)!=src_nums for t in targets): token_ok=False
    if 'RustyMilk' in c['sourceKey'] and any('RustyMilk' not in t for t in targets): token_ok=False
mark('recommendation-token-preservation',token_ok,'placeholder/markup/numeric/protected signature mismatch')
brand_rows=[x for x in x_rows if x['position']==1712]
mark('manual-protected-literal',len(brand_rows)==12 and all(x['constraintChecks']['manualProtectedLiteralsPreserved'] and 'RustyMilk' in x['currentTarget'] for x in brand_rows),'RustyMilk missing')
held=(CAND/'caller-resolution-holds.jsonl').read_text().strip()=='' and (PRIMARY/'holds.jsonl').read_text().strip()=='' and json.loads((BLIND/'summary.json').read_text()).get('holdCount',0)==0
mark('prior-holds-preserved',held and [x['cellId'] for x in x_rows if x['crossDisposition']=='hold']==['1719::id'],'input hold state or cross hold mismatch')

cmds=[['python3',str(CAND/'verify_candidate_free.py'),'--repo',str(REPO)],['python3',str(PRIMARY/'verify_primary_review.py'),'--repo',str(REPO)]]
for i,cmd in enumerate(cmds):
    run=subprocess.run(cmd,capture_output=True,text=True)
    try: result=json.loads(run.stdout).get('result')
    except Exception: result='FAIL'
    name='candidate-free-verifier' if i==0 else 'primary-verifier'
    mark(name,run.returncode==0 and result=='PASS',f'{name} did not pass')

if (OUT/'SHA256SUMS.txt').exists():
    run=subprocess.run(['sha256sum','-c','SHA256SUMS.txt'],cwd=OUT,capture_output=True,text=True)
    mark('packet-checksums',run.returncode==0,'output checksum list failed')
else:
    errors.append('output checksum list missing')
result={'result':'PASS' if not errors and all(v=='PASS' for v in checks.values()) else 'FAIL','checks':checks,'errors':errors,
        'cells':len(x_rows),'rootFlags':len(load_jsonl(OUT/'root-flags.jsonl')),'head':head,'tree':tree}
print(json.dumps(result,ensure_ascii=False,indent=2))
sys.exit(0 if result['result']=='PASS' else 1)
