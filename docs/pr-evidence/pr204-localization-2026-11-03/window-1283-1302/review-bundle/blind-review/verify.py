#!/usr/bin/env python3
"""Verify blind-ledger coverage and invariants against candidate-free input only."""
import hashlib, json, re, sys
from pathlib import Path

INPUT=Path('/mnt/disks/scratch/task-scratch/slskr-pr204-w1283-1302-blind-20261103/input')
OUT=Path(__file__).resolve().parent

def fail(msg):
    print('FAIL:',msg); sys.exit(1)
def sha_bytes(b): return hashlib.sha256(b).hexdigest()
def sha_text(s): return sha_bytes(s.encode('utf-8'))
def jsonl(path): return [json.loads(x) for x in path.read_text(encoding='utf-8').splitlines()]

manifest=json.loads((INPUT/'manifest.json').read_text(encoding='utf-8'))
if manifest['head']!='55ca2ae0788bfd79daab5cc49f49ebb608593e98' or manifest['tree']!='d5677673b766d572102bba249af2ab69095dea0d': fail('head/tree pin')
if sha_bytes((INPUT/'SHA256SUMS.txt').read_bytes())!='abbb1b89549b82072fcbf5fce3c6ae580cc5bd499b4fe5dadd5df7bd0c567f89': fail('candidate-free packet checksum-list digest')
for name,entry in manifest['fileHashes'].items():
    if sha_bytes((INPUT/name).read_bytes()) != entry['sha256']: fail('input file hash: '+name)
for line in (INPUT/'SHA256SUMS.txt').read_text(encoding='utf-8').splitlines():
    digest, name = line.split(None, 1)
    name=name.lstrip('* ')
    if sha_bytes((INPUT/name).read_bytes()) != digest: fail('input checksum-list entry: '+name)
queue=jsonl(INPUT/'source-queue.jsonl')
if len(queue)!=manifest['catalogSourceCount']: fail('source queue key count')
keys=[r['sourceKey'] for r in queue]
if len(set(keys))!=len(keys) or keys!=sorted(keys): fail('source queue uniqueness/order')
if sha_bytes(('\n'.join(keys)+'\n').encode('utf-8'))!=manifest['sourceLookupKeyOrderSha256']: fail('source queue order digest')
if [r['sourceKey'] for r in queue[1282:1302]] != (INPUT/'selected-source-keys.txt').read_text(encoding='utf-8').splitlines(): fail('selected source key list')
if any(queue[i]['position']!=i+1 for i in range(len(queue))): fail('source queue position sequence')
for cell in queue[1282:1302]:
    if cell['sourceKeySha256']!=sha_text(cell['sourceKey']): fail('source queue key hash')
pins=json.loads((INPUT/'catalog-file-pins.json').read_text(encoding='utf-8'))
structure=jsonl(INPUT/'catalog-structure.jsonl')
by_locale={r['locale']:r for r in structure}
if len(by_locale)!=12 or set(by_locale)!=set(manifest['localeOrder']): fail('catalog locale coverage')
for locale, pin in pins['localeCatalogs'].items():
    cat=by_locale.get(locale)
    if cat is None or cat['keyCount']!=len(keys): fail('catalog key count: '+locale)
    for field in ('path','byteCount','lineCount','keyCount','sha256','gitBlob','orderedKeySha256'):
        if cat[field]!=pin[field]: fail('catalog structure pin '+locale+': '+field)
if len({r['orderedKeySha256'] for r in structure})!=1: fail('catalogs do not share one key order')
lineage=json.loads((INPUT/'source-order-lineage.json').read_text(encoding='utf-8'))
if lineage['liveCatalogSourceKeyOrderSha256']!=manifest['sourceLookupKeyOrderSha256'] or not lineage['liveCatalogOrderMatchesPreviousCandidateFreeQueue']: fail('source-order lineage pin')

curr=jsonl(INPUT/'current-target-cells.jsonl')
ctx={r['position']:r for r in jsonl(INPUT/'source-contexts.jsonl')}
ledger=jsonl(OUT/'blind-ledger.jsonl')
if len(ledger)!=240 or len(curr)!=240: fail('cell count')
locale_order=manifest['localeOrder']
expected=[(p,l) for p in range(1283,1303) for l in locale_order]
actual=[(r['position'],r['locale']) for r in ledger]
if actual!=expected: fail('coverage/order or duplicate cell')
base={(r['position'],r['locale']):r for r in curr}
for row in ledger:
    key=(row['position'],row['locale']); old=base[key]
    if row['sourceKey']!=old['sourceKey'] or row['sourceKeySha256']!=sha_text(old['sourceKey']): fail(f'source pin: {key}')
    if row['currentTarget']!=old['currentTarget'] or row['currentTargetSha256']!=sha_text(old['currentTarget']): fail(f'current target pin: {key}')
    if row['targetSha256']!=sha_text(row['target']): fail(f'target hash: {key}')
    if row['disposition'] not in ('retain','propose'): fail(f'disposition: {key}')
    if row['disposition']=='retain' and row['target']!=row['currentTarget']: fail(f'retain changed value: {key}')
    if row['disposition']=='propose' and row['target']==row['currentTarget']: fail(f'empty proposal: {key}')
    if not row['rationale'] or row['confidence'] not in ('high','moderate','low'): fail(f'rationale/confidence: {key}')
    if row['sourcePlaceholders']!=old['sourcePlaceholders'] or row['targetPlaceholders']!=re.findall(r'\{([a-zA-Z][a-zA-Z0-9_]*)\}',row['target']): fail(f'placeholder evidence: {key}')
    if row['sourcePlaceholders']!=row['targetPlaceholders']: fail(f'placeholder mismatch: {key}')
    if row['sourceMarkupTags']!=old['sourceMarkupTags'] or row['targetMarkupTags']!=re.findall(r'<\/?[A-Za-z][^>]*>',row['target']): fail(f'markup evidence: {key}')
    if row['sourceMarkupTags']!=row['targetMarkupTags']: fail(f'markup mismatch: {key}')
    if row['sourceNumericTokens']!=old['sourceNumericTokens'] or row['targetNumericTokens']!=re.findall(r'(?<!\w)[+-]?\d+(?:[.,]\d+)?%?(?!\w)',row['target']): fail(f'numeric evidence: {key}')
    if row['sourceNumericTokens']!=row['targetNumericTokens']: fail(f'numeric-token mismatch: {key}')
    if row['sourceProtectedLiterals']!=old['sourceProtectedLiterals']: fail(f'protected literal source evidence: {key}')
    if not all(tok in row['target'] for tok in row['sourceProtectedLiterals']): fail(f'protected literal lost: {key}')
    if row['callerContextSha256']!=ctx[row['position']]['callerContextSha256']: fail(f'caller context hash: {key}')
    refs=[{'path':c['path'],'line':c['line'],'lineSha256':c['lineSha256'],'contextSha256':c['contextSha256'],'gitBlob':c['gitBlob'],'fileSha256':c['fileSha256']} for c in ctx[row['position']]['callers']]
    if row['callerReferences']!=refs: fail(f'caller references: {key}')
    if row['nativeSpeakerApproval'] is not False: fail(f'native-speaker status: {key}')
    if row['sourceKey'] in ('Enable FTP completed-download uploads','Enable FTP uploads') and row['locale']=='hi' and 'FTP' not in row['target']: fail('FTP literal correction')
counts={d:sum(r['disposition']==d for r in ledger) for d in ('propose','retain')}
if counts!={'propose':132,'retain':108}: fail(f'disposition counts {counts}')
if json.loads((INPUT/'caller-resolution-holds.jsonl').read_text(encoding='utf-8') or '[]')!=[]: fail('unexpected caller hold')
summary=json.loads((OUT/'summary.json').read_text(encoding='utf-8'))
if summary['reviewedCells']!=240 or summary['proposals']!=counts['propose'] or summary['retains']!=counts['retain'] or summary['holds']!=0: fail('summary counts')
if summary['candidateFreeChecksumListSha256']!=sha_bytes((INPUT/'SHA256SUMS.txt').read_bytes()): fail('summary input checksum')
print(json.dumps({'status':'PASS','cells':len(ledger),'proposals':counts['propose'],'retains':counts['retain'],'holds':0,'candidateFreeChecksumListSha256':summary['candidateFreeChecksumListSha256'],'head':manifest['head'],'tree':manifest['tree']},sort_keys=True))
