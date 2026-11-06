#!/usr/bin/env python3
import argparse, hashlib, json, re, sys
from pathlib import Path

def sha(b): return hashlib.sha256(b).hexdigest()
def load_jsonl(p): return [json.loads(x) for x in p.read_text(encoding='utf-8').splitlines() if x]
def require(ok,msg):
    if not ok: raise SystemExit('FAIL: '+msg)

a=argparse.ArgumentParser()
a.add_argument('--input',type=Path,default=Path('/home/keith/Documents/code/task-scratch/slskr-pr204-w1303-1322-primary-20261103/input'))
a.add_argument('--review',type=Path,default=Path(__file__).resolve().parent)
args=a.parse_args(); inp=args.input; out=args.review
# Verify immutable candidate-free packet hashes.
manifest=json.loads((inp/'manifest.json').read_text(encoding='utf-8'))
for line in (inp/'SHA256SUMS.txt').read_text(encoding='utf-8').splitlines():
    expected,name=line.split('  ',1)
    require(sha((inp/name).read_bytes())==expected,'candidate-free checksum '+name)
require(manifest['head']=='f46b8b2322f4b944f39f34d5bb8d55852ba330c8','manifest head')
require(manifest['tree']=='4eba98f951a745dac6b5332bd6796bf57c7037e2','manifest tree')
require(manifest['cellCount']==240 and manifest['sourceCount']==20 and manifest['localeCount']==12,'manifest dimensions')
queue=load_jsonl(inp/'source-queue.jsonl'); cells=load_jsonl(inp/'current-target-cells.jsonl'); contexts=load_jsonl(inp/'source-contexts.jsonl')
ledger=load_jsonl(out/'blind-ledger.jsonl')
require(len(ledger)==240,'ledger cell count')
q={r['position']:r for r in queue}; ctx={r['sourceKey']:r for r in contexts}
cellmap={(r['position'],r['locale']):r for r in cells}
require(len(cellmap)==240,'input unique cell count')
locale_order=manifest['localeOrder']
expected={(p,l) for p in range(1303,1323) for l in locale_order}
actual={(r['position'],r['locale']) for r in ledger}
require(actual==expected,'ledger selected coverage')
require(len(actual)==len(ledger),'ledger duplicates')
counts={'propose':0,'retain':0,'hold':0}
placeholder_re=re.compile(r'\{[A-Za-z][A-Za-z0-9_]*\}')
markup_re=re.compile(r'</?[A-Za-z][^>]*>')
accepted_digit={('ja',1314),('ko',1314),('vi',1314)}
for r in ledger:
    pos,loc=r['position'],r['locale']; cell=cellmap[pos,loc]; disposition=r['disposition']; counts[disposition]+=1
    require(r['sourceKey']==q[pos]['sourceKey']==cell['sourceKey'],'source key at '+str((pos,loc)))
    require(r['sourceKeySha256']==q[pos]['sourceKeySha256']==sha(r['sourceKey'].encode()),'source hash at '+str((pos,loc)))
    require(r['currentTarget']==cell['currentTarget'],'current target at '+str((pos,loc)))
    require(r['currentTargetSha256']==cell['currentTargetSha256']==sha(r['currentTarget'].encode()),'current target hash at '+str((pos,loc)))
    require(r['targetSha256']==sha(r['target'].encode()),'review target hash at '+str((pos,loc)))
    require(disposition in counts,'disposition at '+str((pos,loc)))
    if disposition in ('retain','hold'): require(r['target']==r['currentTarget'],'unchanged disposition target at '+str((pos,loc)))
    source_ph=placeholder_re.findall(r['sourceKey']); target_ph=placeholder_re.findall(r['target'])
    require(source_ph==target_ph,'placeholder sequence at '+str((pos,loc)))
    require(markup_re.findall(r['sourceKey'])==markup_re.findall(r['target']),'markup sequence at '+str((pos,loc)))
    source_num=cell['sourceNumericTokens']; target_num=re.findall(r'(?<![A-Za-z])\d+(?:[.,]\d+)?',r['target'])
    if (loc,pos) in accepted_digit:
        require('five-second' in r['sourceKey'] and '5' in target_num,'reviewed five-second digit equivalence at '+str((pos,loc)))
        require(disposition=='retain','numeric equivalence disposition at '+str((pos,loc)))
    else:
        require(source_num==target_num,'numeric tokens at '+str((pos,loc)))
    for lit in cell['sourceProtectedLiterals']:
        require(lit in r['target'],'protected literal '+lit+' at '+str((pos,loc)))
    c=ctx[r['sourceKey']]
    cref=r['callerContextRef']
    require(cref['callerContextSha256']==c['callerContextSha256'],'caller-context hash at '+str((pos,loc)))
    expected_refs=[{'path':x['path'],'line':x['line'],'lineSha256':x['lineSha256'],'fileSha256':x['fileSha256'],'gitBlob':x['gitBlob']} for x in c['callers']]
    require(cref['callerRefs']==expected_refs,'caller refs at '+str((pos,loc)))
require(counts=={'propose':18,'retain':212,'hold':10},'decision totals '+str(counts))
# Verify independently attested pin and summary.
att=json.loads((out/'PR-attestation-final.json').read_text(encoding='utf-8'))
require(att['head']==manifest['head'] and att['tree']==manifest['tree'],'attestation pin')
require(att['branchRef']==manifest['head'] and att['pullRef']==manifest['head'],'live refs')
summary=json.loads((out/'summary.json').read_text(encoding='utf-8'))
require(summary['counts']==counts and summary['input']['manifestSha256']==sha((inp/'manifest.json').read_bytes()),'summary values')
# Verify output checksum commitments, excluding the checksum files themselves.
for line in (out/'SHA256SUMS.txt').read_text(encoding='utf-8').splitlines():
    expected_hash,name=line.split('  ',1)
    require(sha((out/name).read_bytes())==expected_hash,'output checksum '+name)
require((out/'SHA256SUMS.sha256').read_text().strip()==sha((out/'SHA256SUMS.txt').read_bytes()),'checksum-list hash')
print(json.dumps({'status':'PASS','cells':len(ledger),'counts':counts,'packetChecksumListSha256':sha((inp/'SHA256SUMS.txt').read_bytes()),'manifestSha256':sha((inp/'manifest.json').read_bytes()),'outputChecksumListSha256':sha((out/'SHA256SUMS.txt').read_bytes()),'ledgerSha256':sha((out/'blind-ledger.jsonl').read_bytes())},indent=2))
