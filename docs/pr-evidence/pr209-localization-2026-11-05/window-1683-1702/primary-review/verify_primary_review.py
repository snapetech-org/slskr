#!/usr/bin/env python3
"""Offline verifier for the slskR PR #209 W1683-W1702 primary-review packet."""
from __future__ import annotations
import argparse, collections, json, subprocess, sys
from pathlib import Path

PACKET=Path(__file__).resolve().parent
INPUT=PACKET.parent/'candidate-free-input'
REPO_DEFAULT=Path('/home/keith/Documents/code/.task-worktrees/localization-20261105/slskr-w1683')
HEAD='f04b7f965aef79552d65d40a2eeb550e5e3b9cfa'; TREE='85fe880023e55e055660fd17599c291edd24a1c6'
BASE='1bbaec9fdc63a86de343e37e33bae70d44301a36'; BRANCH='codex/slskr-l10n-audit-20261104-resync'
START,END=1683,1702
sys.dont_write_bytecode=True
spec=__import__('importlib.util',fromlist=['spec_from_file_location']).spec_from_file_location('candidatefree_schema',INPUT/'candidate-free-schema-helper.py')
h=__import__('importlib.util',fromlist=['module_from_spec']).module_from_spec(spec); spec.loader.exec_module(h)


def fail(message): raise SystemExit('FAIL: '+message)
def sha(value): return h.sha(value)
def canon(value): return h.canon(value)
def git(repo,*args): return subprocess.check_output(['git','-C',str(repo),*args],text=True,stderr=subprocess.STDOUT).strip()
def target_hash(value): return sha(value) if isinstance(value,str) else sha(canon(value))
def target_strings(value,path='$'):
    if isinstance(value,str): return [(path,value)]
    if isinstance(value,dict): return [item for key,child in value.items() for item in target_strings(child,path+'.'+str(key))]
    if isinstance(value,list): return [item for index,child in enumerate(value) for item in target_strings(child,path+f'[{index}]')]
    return []
def read_jsonl(path): return [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines() if line.strip()]
def checksum_map(path):
    result={}
    for line in (path/'SHA256SUMS.txt').read_text(encoding='utf-8').splitlines():
        if line.strip():
            digest,name=line.split(None,1); name=name.lstrip('* ')
            if name in result: fail('duplicate checksum path '+name)
            result[name]=digest
    actual={file.relative_to(path).as_posix():sha(file.read_bytes()) for file in path.rglob('*') if file.is_file() and file.name!='SHA256SUMS.txt'}
    if result!=actual: fail('checksum file set/content mismatch at '+str(path))
    return result


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--repo',type=Path,default=REPO_DEFAULT); args=ap.parse_args(); repo=args.repo.resolve()
    packet_checks=checksum_map(PACKET); input_checks=checksum_map(INPUT)
    manifest=json.loads((PACKET/'manifest.json').read_text(encoding='utf-8'))
    input_manifest=json.loads((INPUT/'manifest.json').read_text(encoding='utf-8'))
    if (manifest.get('exactHead'),manifest.get('exactTree'),manifest.get('baseSha'),manifest.get('selectedPositions'))!=(HEAD,TREE,BASE,[START,END]): fail('review manifest exact pin/window mismatch')
    if manifest.get('candidateFreeOnly') is not True or manifest.get('blindOrCrossOutputInspected') is not False: fail('review source boundary mismatch')
    expected_file_hashes={file.name:{'sha256':sha(file.read_bytes()),'byteCount':file.stat().st_size} for file in sorted(PACKET.iterdir()) if file.is_file() and file.name not in ('manifest.json','SHA256SUMS.txt')}
    if manifest.get('files')!=expected_file_hashes: fail('primary manifest file hashes mismatch')
    input_sha=sha((INPUT/'SHA256SUMS.txt').read_bytes()); input_manifest_sha=sha((INPUT/'manifest.json').read_bytes())
    if manifest.get('candidateFreeChecksumListSha256')!=input_sha or manifest.get('candidateFreeManifestSha256')!=input_manifest_sha: fail('candidate-free packet binding mismatch')
    if input_manifest.get('head')!=HEAD or input_manifest.get('tree')!=TREE or input_manifest.get('selectedPositions')!=[START,END]: fail('candidate-free exact pin/window mismatch')
    input_file_hashes={file.name:{'sha256':sha(file.read_bytes()),'byteCount':file.stat().st_size} for file in sorted(INPUT.iterdir()) if file.is_file() and file.name not in ('manifest.json','SHA256SUMS.txt')}
    if input_manifest.get('fileHashes')!=input_file_hashes: fail('candidate-free manifest file hashes mismatch')
    if git(repo,'rev-parse','HEAD')!=HEAD or git(repo,'rev-parse','HEAD^{tree}')!=TREE or git(repo,'branch','--show-current')!=BRANCH or git(repo,'status','--porcelain=v1'): fail('local exact-head source clone mismatch')
    cells_raw=(INPUT/'current-target-cells.jsonl').read_bytes().splitlines(); candidate_cells={}; candidate_hash={}
    for raw in cells_raw:
        row=json.loads(raw); key=(row['position'],row['locale'])
        if key in candidate_cells: fail('duplicate candidate-free cell '+str(key))
        candidate_cells[key]=row; candidate_hash[key]=sha(raw)
    context_rows=read_jsonl(INPUT/'source-contexts.jsonl'); contexts={row['position']:row for row in context_rows}
    queue=read_jsonl(INPUT/'source-queue.jsonl'); queue_keys={row['position']:row for row in queue}
    locales=h.LOCALES; expected={(position,locale) for position in range(START,END+1) for locale in locales}
    if set(candidate_cells)!=expected or len(candidate_cells)!=240: fail('candidate-free cell scope mismatch')
    ledger_rows=read_jsonl(PACKET/'ledger.jsonl'); ledger={row['cellId']:row for row in ledger_rows}
    proposal_rows=read_jsonl(PACKET/'proposals.jsonl'); proposals={row['cellId']:row for row in proposal_rows}
    holds=read_jsonl(PACKET/'holds.jsonl')
    if len(ledger)!=240 or set(ledger)!={f'{p}::{l}' for p,l in expected}: fail('ledger scope mismatch')
    counts=collections.Counter(); confidence=collections.Counter(); expected_proposals=set()
    reorder_count=0; protected_count=0
    for position,locale in sorted(expected,key=lambda item:(item[0],locales.index(item[1]))):
        cell=candidate_cells[(position,locale)]; rec=ledger[f'{position}::{locale}']; queue_row=queue_keys[position]
        source=queue_row['sourceKey']; context=contexts[position]
        if rec.get('position')!=position or rec.get('locale')!=locale or rec.get('cellId')!=f'{position}::{locale}': fail('ledger identity mismatch')
        if rec.get('sourceKey')!=source or rec.get('sourceKeySha256')!=cell.get('sourceKeySha256') or rec.get('sourceKeySha256')!=sha(source): fail('source key binding mismatch')
        if rec.get('candidateFreeCellSha256')!=candidate_hash[(position,locale)]: fail('candidate-free row hash mismatch')
        if rec.get('sourceContextSha256')!=cell.get('sourceContextSha256') or rec.get('sourceContextSha256')!=context.get('callerContextSha256'): fail('source context binding mismatch')
        if rec.get('callerReferenceCount')!=context.get('productionCallerCount') or rec.get('callerOccurrenceCount')!=context.get('callerOccurrenceCount'): fail('caller count mismatch')
        if rec.get('callerPaths')!=sorted({caller['path'] for caller in context['callers']}): fail('caller path binding mismatch')
        if rec.get('currentTargetSha256')!=cell['currentTargetSha256'] or rec.get('currentTargetType')!=cell['currentTargetType']: fail('current target hash/type mismatch')
        if rec.get('catalogPath')!=cell['catalogPath'] or rec.get('catalogFileSha256')!=cell['catalogFileSha256'] or rec.get('catalogGitBlob')!=cell['catalogGitBlob']: fail('catalog pin mismatch')
        expected_tokens={'placeholders':h.tokens(source)[0],'markupTags':h.tokens(source)[1],
          'numericTokens':h.tokens(source)[2],'protectedLiterals':h.tokens(source)[3]}
        if rec.get('sourceTokens')!=expected_tokens: fail('source token signature mismatch')
        variants=cell.get('targetTokenVariants',[])
        current_multiset_matches=all(collections.Counter(row['targetPlaceholders'])==collections.Counter(expected_tokens['placeholders']) for row in variants)
        if rec.get('currentTargetPlaceholderMultisetMatches') is not current_multiset_matches: fail('placeholder multiset review mismatch')
        if bool(rec.get('currentTargetPlaceholderOrderMatches')) != all(row['targetPlaceholders']==expected_tokens['placeholders'] for row in variants): fail('placeholder order review mismatch')
        if rec.get('targetVariantPaths')!=[row['jsonPath'] for row in variants]: fail('target variant path mismatch')
        for variant in variants:
            reorder_count += variant['targetPlaceholders']!=expected_tokens['placeholders']
            protected_count += bool(variant['protectedLiteralMismatchTokens'])
        decision=rec.get('decision'); counts[decision]+=1; confidence[rec.get('confidence')]+=1
        if rec.get('exactHead')!=HEAD or rec.get('exactTree')!=TREE: fail('ledger exact source pin mismatch')
        if decision in ('correction','refinement'):
            expected_proposals.add(rec['cellId'])
            target=rec.get('recommendedTarget')
            if not isinstance(target,str) or rec.get('recommendedTargetSha256')!=sha(target): fail('proposal target hash mismatch')
            source_tokens=h.tokens(source); target_tokens=h.tokens(target)
            checks={'placeholderMultiset':collections.Counter(source_tokens[0])==collections.Counter(target_tokens[0]),
              'markupTags':source_tokens[1]==target_tokens[1],'numericTokens':source_tokens[2]==target_tokens[2],
              'protectedLiterals':all(item in target_tokens[3] for item in source_tokens[3])}
            if rec.get('recommendedTargetTokenChecks')!=checks or not all(checks.values()): fail('proposal token mismatch')
            if source.rstrip().endswith(':') and not target.rstrip().endswith((':','：')): fail('proposal removed caller prefix colon')
            prop=proposals.get(rec['cellId'])
            if prop is None: fail('proposal record missing '+rec['cellId'])
            for field in ('position','locale','sourceKeySha256','currentTargetSha256','candidateFreeCellSha256','sourceContextSha256','catalogPath','catalogFileSha256','catalogGitBlob','decision','recommendedTarget','recommendedTargetSha256','exactHead','exactTree'):
                if prop.get(field)!=rec.get(field): fail('proposal ledger binding mismatch '+field+' '+rec['cellId'])
        elif decision=='accept-current':
            if not current_multiset_matches: fail('accept-current decision with missing/duplicated source placeholder')
            if 'recommendedTarget' in rec: fail('accept-current row contains proposal')
        elif decision=='hold':
            if not any(row.get('cellId')==rec['cellId'] for row in holds): fail('hold record missing')
        else: fail('unknown decision '+str(decision))
    if set(proposals)!=expected_proposals: fail('proposal inventory does not match ledger')
    if len(holds)!=0: fail('unexpected unresolved primary holds')
    expected_counts={'accept-current':232,'correction':5,'refinement':3}
    if dict(counts)!=expected_counts: fail('decision counts mismatch '+str(counts))
    if reorder_count!=12 or protected_count!=2: fail('placeholder/protected-literal review inventory mismatch')
    summary=json.loads((PACKET/'summary.json').read_text(encoding='utf-8'))
    if summary.get('decisionCounts')!=dict(counts) or summary.get('confidenceCounts')!=dict(confidence) or summary.get('cellCount')!=240 or summary.get('proposalCount')!=8 or summary.get('holdCount')!=0: fail('summary mismatch')
    for filename in ('attestation-before.json','attestation-after.json'):
        att=json.loads((PACKET/filename).read_text(encoding='utf-8'))
        if (att.get('headSha'),att.get('headTree'),att.get('baseSha'),att.get('state'),att.get('draft'),att.get('headRef'))!=(HEAD,TREE,BASE,'OPEN',True,BRANCH): fail('live PR attestation mismatch '+filename)
        refs=att.get('remoteRefs',{})
        if refs.get(f'refs/heads/{BRANCH}')!=HEAD or refs.get('refs/pull/209/head')!=HEAD: fail('remote ref attestation mismatch '+filename)
        if att.get('candidateFreeChecksumListSha256')!=input_sha or att.get('candidateFreeManifestSha256')!=input_manifest_sha: fail('attested candidate-free hash mismatch '+filename)
        if att.get('localWorktreeClean') is not True: fail('source clone not clean in attestation '+filename)
    print(json.dumps({'result':'PASS','head':HEAD,'tree':TREE,'cells':len(ledger),'decisionCounts':dict(counts),
      'proposals':len(proposals),'holds':len(holds),'placeholderOrderDifferences':reorder_count,
      'genericIdLocalizations':protected_count,'candidateFreeChecksumFiles':len(input_checks),
      'primaryChecksumFiles':len(packet_checks)},indent=2))

if __name__=='__main__': main()
