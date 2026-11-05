#!/usr/bin/env python3
"""Verify the primary review ledger against its candidate-free input packet."""
import hashlib, json, subprocess, sys
from pathlib import Path
BASE=Path(__file__).resolve().parent
CF=(BASE/'../candidate-free-input').resolve()
LOCALES=['es','zh-Hans','hi','de','ja','fr','pt-BR','ar','ko','zh-Hant','vi','id']
HASH_ONLY_POSITIONS={1754,1755}

def sha(data):
    if isinstance(data,str): data=data.encode('utf-8')
    return hashlib.sha256(data).hexdigest()
def jsonl(path):
    return [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines() if line.strip()]
def require(condition,message):
    if not condition: raise ValueError(message)
def verify_sums(directory, filename):
    seen=set()
    for line in (directory/filename).read_text(encoding='utf-8').splitlines():
        expected, rel=line.split('  ',1)
        path=(directory/rel).resolve()
        require(path.parent==directory.resolve(),f'checksum path escapes packet: {rel}')
        require(path.is_file(),f'missing checksummed file: {rel}')
        require(sha(path.read_bytes())==expected,f'checksum mismatch: {rel}')
        seen.add(rel)
    return seen

def main():
    checked=verify_sums(BASE,'SHA256SUMS.txt')
    required={'README.md','manifest.json','primary-review.jsonl','active-hold-reattestation.jsonl','verify_primary_review.py'}
    require(checked==required,'checksum file coverage mismatch')
    cf_sums=verify_sums(CF,'SHA256SUMS.txt')
    require(len(cf_sums)==19,'candidate-free checksum coverage mismatch')
    result=subprocess.run([sys.executable,str(CF/'verify_candidate_free.py')],capture_output=True,text=True,check=True)
    require('"result": "PASS"' in result.stdout,'candidate-free verifier did not pass')
    manifest=json.loads((BASE/'manifest.json').read_text(encoding='utf-8'))
    require(manifest['head']=='ccbc3dc721c1cbd225d4e512f4f0af4c80476620','head pin mismatch')
    require(manifest['tree']=='075d1b72a2fd080404ebec19d354cb863638df21','tree pin mismatch')
    target_rows=jsonl(CF/'current-target-cells.jsonl')
    src_rows={x['position']:x for x in jsonl(CF/'source-contexts.jsonl')}
    cells={(x['position'],x['locale']):x for x in target_rows}
    require(len(cells)==240,'candidate-free cell count mismatch')
    records=jsonl(BASE/'primary-review.jsonl')
    require(len(records)==240,'review record count mismatch')
    require(len({(r['position'],r['locale']) for r in records})==240,'duplicate review record')
    require({r['position'] for r in records}==set(range(1743,1763)),'position coverage mismatch')
    require({r['locale'] for r in records}==set(LOCALES),'locale coverage mismatch')
    counts={k:0 for k in ('accept-current','correction','refinement','hold')}
    for r in records:
        key=(r['position'],r['locale'])
        require(key in cells,f'unknown review cell {key}')
        c=cells[key]; s=src_rows[r['position']]
        require(r['sourceKeySha256']==c['sourceKeySha256'],f'source-key hash mismatch {key}')
        require(r['currentTargetSha256']==c['currentTargetSha256'],f'target hash mismatch {key}')
        require(r['callerContextSha256']==s['callerContextSha256'],f'caller context hash mismatch {key}')
        require(r['callerCount']==s['productionCallerCount'],f'caller count mismatch {key}')
        require(r['catalogPath']==c['catalogPath'] and r['catalogFileSha256']==c['catalogFileSha256'] and r['catalogGitBlob']==c['catalogGitBlob'],f'catalog pin mismatch {key}')
        require('currentTarget' not in r and 'targetText' not in r,'current target text must not be copied')
        require(r['currentTargetTextIncluded'] is False,'current target text flag mismatch')
        require(r['reviewerRole']=='primary','reviewer role mismatch')
        counts[r['decision']]+=1
        if r['position'] in HASH_ONLY_POSITIONS:
            require(r['decision']=='hold' and r['hashOnly'] is True,'callerless cell not held hash-only')
            require(r['sourceKeyTextIncluded'] is False and 'sourceKey' not in r,'callerless source text must remain omitted')
            require('recommendedTarget' not in r and 'recommendedTargetSha256' not in r,'callerless target proposal must remain omitted')
        else:
            require(r['sourceKey']==c['sourceKey'] and r['sourceKeyTextIncluded'] is True,'source text mismatch')
            require(r['hashOnly'] is False,'caller-backed cell incorrectly marked hash-only')
            require(s['productionCallerCount']>0,'caller-backed record has no caller')
        if r['decision'] in ('correction','refinement'):
            require(isinstance(r.get('recommendedTarget'),str) and bool(r['recommendedTarget']),'recommendation missing')
            require(r.get('recommendedTargetSha256')==sha(r['recommendedTarget']),'recommendation hash mismatch')
        else:
            require('recommendedTarget' not in r and 'recommendedTargetSha256' not in r,'unexpected recommendation')
    require(counts==manifest['dispositionCounts'], 'disposition counts mismatch')
    require(counts=={'accept-current':183,'correction':7,'refinement':26,'hold':24},'unexpected disposition totals')
    hold_inputs=jsonl(CF/'active-hold-reattestation.jsonl')
    hold_outputs=jsonl(BASE/'active-hold-reattestation.jsonl')
    require(len(hold_inputs)==len(hold_outputs)==1,'active hold record count mismatch')
    src=hold_inputs[0]; out=hold_outputs[0]
    require(out['holdId']=='1719::id' and out['decision']=='hold' and out['hashOnly'] is True,'active hold identity mismatch')
    require(out['currentTargetSha256']==src['currentTargetSha256'] and out['sourceKeySha256']==src['sourceKeySha256'],'active hold hash mismatch')
    require(out['currentSourceContextSha256']==src['currentSourceContextSha256'],'active hold context hash mismatch')
    require(out['targetHashUnchanged'] is True and out['sourceContextUnchanged'] is True,'active hold continuity mismatch')
    require(out['textIncluded'] is False,'active hold text flag mismatch')
    require(not any(k in out for k in ('sourceKey','currentTarget','targetText','recommendedTarget')),'active hold text must remain omitted')
    print(json.dumps({'result':'PASS','checksummedOutputFiles':len(checked),'candidateFreeInputFiles':len(cf_sums),'reviewCells':len(records),'dispositions':counts,'callerlessHashOnlyCells':24,'activeHoldHashOnly':'1719::id'},ensure_ascii=False))

if __name__=='__main__':
    try: main()
    except Exception as exc:
        print(json.dumps({'result':'FAIL','error':str(exc)},ensure_ascii=False),file=sys.stderr)
        raise
