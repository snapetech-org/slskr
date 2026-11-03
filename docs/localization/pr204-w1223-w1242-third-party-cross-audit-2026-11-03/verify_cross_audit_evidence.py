#!/usr/bin/env python3
"""Verify sealed slskR PR #204 W1223-W1242 cross-audit evidence and catalog readback."""
from __future__ import annotations
import argparse, collections, hashlib, json, pathlib, re, subprocess, sys

PACKAGE=pathlib.Path(__file__).resolve().parent
DEFAULT_REPO=PACKAGE.parents[2]

def sha(value:str)->str:
    return hashlib.sha256(value.encode('utf-8')).hexdigest()

def tokens(pattern:str,value:str):
    return re.findall(pattern,value)

def main()->int:
    parser=argparse.ArgumentParser()
    parser.add_argument('--repo',type=pathlib.Path,default=DEFAULT_REPO)
    args=parser.parse_args()
    repo=args.repo.resolve()
    result=subprocess.run(['sha256sum','-c','SHA256SUMS.txt'],cwd=PACKAGE,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
    if result.returncode:
        print(result.stdout,file=sys.stderr); return 1
    rows=[json.loads(x) for x in (PACKAGE/'cross-audit-ledger.jsonl').read_text(encoding='utf-8').splitlines() if x.strip()]
    summary=json.loads((PACKAGE/'summary.json').read_text(encoding='utf-8'))
    if len(rows)!=240 or summary['reviewedCellCount']!=240: raise SystemExit('cell count mismatch')
    ids={(r['position'],r['locale']) for r in rows}
    if len(ids)!=240: raise SystemExit('duplicate cell key')
    counts=collections.Counter(r['disposition'] for r in rows)
    if dict(counts)!=summary['dispositions']: raise SystemExit('disposition summary mismatch')
    changed=0; holds=0; readback=0
    catalogs={}
    for r in rows:
        source=r['source']['sourceKey']; target=r['currentTarget']['text']; locale=r['locale']
        if sha(source)!=r['source']['sourceKeySha256']: raise SystemExit(f'source hash mismatch {r["position"]}/{locale}')
        if sha(target)!=r['currentTarget']['sha256']: raise SystemExit(f'current target hash mismatch {r["position"]}/{locale}')
        rel=r['evidence']['catalog']['path']
        if locale not in catalogs:
            catalogs[locale]=json.loads((repo/rel).read_text(encoding='utf-8'))
        selected=r['selectedTarget']
        if r['disposition']=='hold':
            holds+=1
            if selected is not None or r['evidence']['caller']['referenceCount']!=0: raise SystemExit(f'held cell has caller/target {r["position"]}/{locale}')
            expected=target
        else:
            if selected is None or sha(selected['text'])!=selected['sha256']: raise SystemExit(f'selected target hash mismatch {r["position"]}/{locale}')
            expected=selected['text']
            if expected!=target: changed+=1
            protected=r['evidence']['protectedLiterals']['required']
            if any(value not in expected for value in protected): raise SystemExit(f'protected literal mismatch {r["position"]}/{locale}')
            if tokens(r'\{[A-Za-z][A-Za-z0-9_]*\}',expected)!=r['evidence']['placeholders']['sourceSequence']: raise SystemExit(f'placeholder mismatch {r["position"]}/{locale}')
            if tokens(r'<[^>]+>',expected)!=r['evidence']['markupTokens']['source']: raise SystemExit(f'markup mismatch {r["position"]}/{locale}')
            if tokens(r'\d+(?:[.,]\d+)*',expected)!=r['evidence']['numericTokens']['source']: raise SystemExit(f'numeric token mismatch {r["position"]}/{locale}')
        if catalogs[locale].get(source)!=expected: raise SystemExit(f'catalog readback mismatch {r["position"]}/{locale}')
        readback+=1
    if holds!=24 or changed!=74: raise SystemExit(f'expected 24 holds and 74 changes; got {holds}, {changed}')
    for held_pos,source in ((1227,'Download selected files'),(1234,'Downloaders')):
        held=[r for r in rows if r['position']==held_pos]
        if len(held)!=12 or any(r['source']['sourceKey']!=source or r['disposition']!='hold' for r in held): raise SystemExit(f'hold set mismatch at position {held_pos}')
    print(json.dumps({'checksumManifest':'pass','cellCount':readback,'dispositions':dict(counts),'changedTargetsReadBack':changed,'noCallerHoldsPreserved':holds},ensure_ascii=False,sort_keys=True))
    return 0

if __name__=='__main__': raise SystemExit(main())
