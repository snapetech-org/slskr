#!/usr/bin/env python3
"""Portable integrity verifier for the slskR W1663-W1682 blind packet."""
from pathlib import Path
import hashlib, json, re, sys

HERE = Path(__file__).resolve().parent
INPUT = HERE.parent / 'candidate-free-input'
EXPECTED_HEAD = '2ab97d1a21f7d001eb9470c76b3636f59f600609'
EXPECTED_TREE = '63097ec7c80be0bef55fb1bde5a38da7b6a59ce7'
EXPECTED_LOCALES = ['es','zh-Hans','hi','de','ja','fr','pt-BR','ar','ko','zh-Hant','vi','id']
EXPECTED_POSITIONS = list(range(1663,1683))

def fail(msg):
    raise SystemExit('FAIL: ' + msg)
def sha(data):
    return hashlib.sha256(data).hexdigest()
def load_json(path):
    try:
        return json.loads(path.read_text())
    except Exception as exc:
        fail(f'{path.name}: invalid JSON ({exc})')
def load_jsonl(path):
    try:
        return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
    except Exception as exc:
        fail(f'{path.name}: invalid JSONL ({exc})')
def parse_sums(path):
    out={}
    for line in path.read_text().splitlines():
        if not line.strip(): continue
        parts=line.split(None,1)
        if len(parts)!=2: fail(f'{path.name}: malformed checksum line')
        digest,name=parts; name=name.lstrip('* ')
        out[name]=digest
    return out
def verify_sums(root, sums_path, exclude=()):
    sums=parse_sums(sums_path)
    if not sums: fail(f'{sums_path.name}: empty checksum list')
    for name,want in sums.items():
        if name in exclude: continue
        path=root/name
        if not path.is_file(): fail(f'checksum target missing: {name}')
        if sha(path.read_bytes())!=want: fail(f'checksum mismatch: {name}')
    actual={p.name for p in root.iterdir() if p.is_file()} - set(exclude)
    named=set(sums)-set(exclude)
    if actual!=named: fail(f'checksum inventory mismatch: unlisted={sorted(actual-named)}, absent={sorted(named-actual)}')
    return len(named)

def verify_attestation(suffix):
    pr=load_json(HERE/f'pr-api-{suffix}.json')
    commit=load_json(HERE/f'head-commit-{suffix}.json')
    refs={}
    for line in (HERE/f'remote-refs-{suffix}.txt').read_text().splitlines():
        if not line.strip(): continue
        sha_,ref=line.split('\t',1); refs[ref]=sha_
    if pr.get('headRefOid')!=EXPECTED_HEAD or pr.get('headRefName')!='codex/slskr-l10n-audit-20261104-resync':
        fail(f'{suffix} PR head/ref mismatch')
    if pr.get('baseRefName')!='main': fail(f'{suffix} PR base branch mismatch')
    if commit.get('sha')!=EXPECTED_HEAD or commit.get('commit',{}).get('tree',{}).get('sha')!=EXPECTED_TREE:
        fail(f'{suffix} commit/tree mismatch')
    if refs.get('refs/heads/codex/slskr-l10n-audit-20261104-resync')!=EXPECTED_HEAD or refs.get('refs/pull/209/head')!=EXPECTED_HEAD:
        fail(f'{suffix} branch or pull ref mismatch')
    if refs.get('refs/heads/main')!=pr.get('baseRefOid'):
        fail(f'{suffix} main ref and PR base snapshot differ')
    return pr

# Verify source packet checksums and exact pin before validating ledger bindings.
verify_sums(INPUT, INPUT/'SHA256SUMS.txt', exclude=('SHA256SUMS.txt',))
cf=load_json(INPUT/'manifest.json')
if cf.get('head')!=EXPECTED_HEAD or cf.get('tree')!=EXPECTED_TREE: fail('candidate-free packet pin mismatch')
if cf.get('cellCount')!=240 or cf.get('sourceCount')!=20 or cf.get('localeOrder')!=EXPECTED_LOCALES: fail('candidate-free packet dimensions mismatch')
entry=verify_attestation('entry')
exit_=verify_attestation('exit')
if entry.get('state')!='OPEN' or not entry.get('isDraft'): fail('PR was not open/draft at review entry')

raw=(INPUT/'current-target-cells.jsonl').read_bytes().splitlines()
inputs=[json.loads(line) for line in raw]
raw_by={(d['position'],d['locale']):raw[i] for i,d in enumerate(inputs)}
source_ctx={d['position']:d for d in load_jsonl(INPUT/'source-contexts.jsonl')}
if len(source_ctx)!=20: fail('source context count mismatch')
ledger=load_jsonl(HERE/'blind-ledger.jsonl')
proposals=load_jsonl(HERE/'proposals.jsonl')
holds=load_jsonl(HERE/'holds.jsonl')
if len(ledger)!=240: fail('ledger does not contain 240 cells')
expected={(p,l) for p in EXPECTED_POSITIONS for l in EXPECTED_LOCALES}
seen=set()
changed=[]
for row in ledger:
    key=(row.get('position'),row.get('locale'))
    if key in seen: fail(f'duplicate ledger cell: {key}')
    seen.add(key)
    if key not in expected: fail(f'unexpected ledger cell: {key}')
    src=next((x for x in inputs if (x['position'],x['locale'])==key),None)
    if src is None: fail(f'candidate-free row missing: {key}')
    ctx=source_ctx[key[0]]
    if row.get('exactHead')!=EXPECTED_HEAD or row.get('exactTree')!=EXPECTED_TREE: fail(f'row pin mismatch: {key}')
    if row.get('sourceKey')!=src['sourceKey'] or row.get('sourceText')!=src['sourceKey']: fail(f'source mismatch: {key}')
    if row.get('sourceKeySha256')!=src['sourceKeySha256'] or row.get('sourceTextSha256')!=sha(src['sourceKey'].encode()): fail(f'source hash mismatch: {key}')
    if row.get('currentTarget')!=src['currentTarget'] or row.get('currentTargetSha256')!=src['currentTargetSha256']: fail(f'current target mismatch: {key}')
    if row.get('callerContextSha256')!=ctx['callerContextSha256'] or row.get('callerContextSha256')!=src['sourceContextSha256']: fail(f'caller binding mismatch: {key}')
    if row.get('candidateFreeRowSha256')!=sha(raw_by[key]): fail(f'candidate-free row hash mismatch: {key}')
    if row.get('callerCount')!=ctx.get('productionCallerCount') or row.get('callerCount',0)<1: fail(f'caller count mismatch/hold needed: {key}')
    target=row.get('recommendedTarget',row['currentTarget'])
    if row.get('decision')=='accept-current':
        if 'recommendedTarget' in row: fail(f'accepted row contains proposal: {key}')
    elif row.get('decision') in ('correction','refinement'):
        if not isinstance(row.get('recommendedTarget'),str) or row['recommendedTarget']==row['currentTarget']: fail(f'changed row lacks new target: {key}')
        if row.get('recommendedTargetSha256')!=sha(row['recommendedTarget'].encode()): fail(f'proposal hash mismatch: {key}')
        changed.append(row)
    elif row.get('decision')=='hold-hash-only':
        fail(f'hash-only hold not permitted where caller context exists: {key}')
    else: fail(f'unknown decision: {key}')
    tok=row.get('tokenIntegrity',{})
    placeholders=re.findall(r'\{[A-Za-z][A-Za-z0-9_]*\}',target)
    markup=re.findall(r'</?[A-Za-z][^>]*>',target)
    nums=re.findall(r'(?<![A-Za-z])\d+(?:[.,]\d+)?',target)
    if placeholders!=src.get('sourcePlaceholders',[]): fail(f'placeholder mismatch: {key}')
    if markup!=src.get('sourceMarkupTags',[]): fail(f'markup mismatch: {key}')
    if nums!=src.get('sourceNumericTokens',[]): fail(f'numeric token mismatch: {key}')
    if not all(x in target for x in src.get('sourceProtectedLiterals',[])): fail(f'protected literal mismatch: {key}')
    if tok.get('targetPlaceholders')!=placeholders or tok.get('targetMarkupTags')!=markup or tok.get('targetNumericTokens')!=nums or not tok.get('allPreserved'): fail(f'ledger token evidence mismatch: {key}')
if seen!=expected: fail(f'ledger coverage mismatch: missing={sorted(expected-seen)}')
if len(changed)!=8 or len(proposals)!=len(changed) or holds: fail('proposal/hold counts mismatch')
ledger_changed={(r['position'],r['locale'],r['recommendedTarget']) for r in changed}
proposal_cells={(r['position'],r['locale'],r['recommendedTarget']) for r in proposals}
if ledger_changed!=proposal_cells: fail('proposal ledger and proposal file differ')

out_count=verify_sums(HERE,HERE/'SHA256SUMS.txt',exclude=('SHA256SUMS.txt',))
print(json.dumps({'result':'PASS','head':EXPECTED_HEAD,'tree':EXPECTED_TREE,'cells':len(ledger),'proposals':len(proposals),'holds':len(holds),'candidateFreeFilesVerified':len(parse_sums(INPUT/'SHA256SUMS.txt')),'outputFilesVerified':out_count,'entryPrState':entry.get('state'),'entryDraft':entry.get('isDraft'),'exitPrState':exit_.get('state'),'exitDraft':exit_.get('isDraft'),'tokenMismatches':0},indent=2))
