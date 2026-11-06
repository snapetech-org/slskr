#!/usr/bin/env python3
"""Offline verifier for the slskR PR #209 W1663-W1682 primary review packet."""
import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path

HEAD='2ab97d1a21f7d001eb9470c76b3636f59f600609'
TREE='63097ec7c80be0bef55fb1bde5a38da7b6a59ce7'
BASE='1bbaec9fdc63a86de343e37e33bae70d44301a36'
BRANCH='codex/slskr-l10n-audit-20261104-resync'
LOCALES=['es','zh-Hans','hi','de','ja','fr','pt-BR','ar','ko','zh-Hant','vi','id']


def sha(b): return hashlib.sha256(b).hexdigest()
def die(msg): raise SystemExit('FAIL: '+msg)


def sums(path):
    out={}
    for line in path.read_text(encoding='utf-8').splitlines():
        if not line.strip(): continue
        h,n=line.split(maxsplit=1); n=n.lstrip('*')
        if n in out: die(f'duplicate checksum path {n}')
        out[n]=h
    return out


def jsonl(path,keyfn):
    out={}
    for raw in path.read_bytes().splitlines():
        if not raw.strip(): continue
        row=json.loads(raw); key=keyfn(row)
        if key in out: die(f'duplicate row {key} in {path.name}')
        out[key]=(row,sha(raw))
    return out


def placeholders(s): return re.findall(r'\{[A-Za-z][A-Za-z0-9_]*\}',s)
def markup(s): return re.findall(r'</?[A-Za-z][^>]*>',s)
def numeric(s): return re.findall(r'(?<![A-Za-z])\d+(?:[.,]\d+)?%?(?![A-Za-z])',s)


def token_checks(source,target,row):
    source_protected=row.get('sourceProtectedLiterals',[])
    protected_ok=all(target.count(t)>=source.count(t) for t in source_protected)
    return {
      'placeholderSequence':placeholders(source)==placeholders(target),
      'markupTags':markup(source)==markup(target),
      'numericTokens':numeric(source)==numeric(target),
      'protectedLiterals':protected_ok,
    }


def git(repo,*args):
    return subprocess.check_output(['git','-C',str(repo),*args],text=True,stderr=subprocess.STDOUT).strip()


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--candidate-free',type=Path,help='candidate-free directory; defaults to sibling candidate-free-input')
    ap.add_argument('--repo',type=Path,help='optional local checkout for exact Git object checks')
    args=ap.parse_args()
    packet=Path(__file__).resolve().parent
    inp=(args.candidate_free or packet.parent/'candidate-free-input').resolve()
    manifest=json.loads((packet/'manifest.json').read_text(encoding='utf-8'))
    summary=json.loads((packet/'summary.json').read_text(encoding='utf-8'))
    if manifest.get('exactHead')!=HEAD or manifest.get('exactTree')!=TREE or manifest.get('baseSha')!=BASE:
        die('output manifest exact pin mismatch')
    if summary.get('exactHead')!=HEAD or summary.get('exactTree')!=TREE or summary.get('baseSha')!=BASE:
        die('summary exact pin mismatch')

    input_sums=sums(inp/'SHA256SUMS.txt')
    input_manifest=json.loads((inp/'manifest.json').read_text(encoding='utf-8'))
    if input_manifest.get('head')!=HEAD or input_manifest.get('tree')!=TREE:
        die('candidate-free exact pin mismatch')
    if set(input_sums)!=(set(input_manifest['fileHashes'])|{'manifest.json'}):
        die('candidate-free checksum inventory mismatch')
    for name,h in input_sums.items():
        p=inp/name
        if not p.is_file() or sha(p.read_bytes())!=h: die(f'candidate-free checksum mismatch: {name}')
        if name in input_manifest['fileHashes'] and input_manifest['fileHashes'][name]['sha256']!=h:
            die(f'candidate-free manifest hash mismatch: {name}')
    input_sum_sha=sha((inp/'SHA256SUMS.txt').read_bytes())
    input_manifest_sha=sha((inp/'manifest.json').read_bytes())
    if input_sum_sha!=manifest.get('candidateFreeChecksumListSha256') or input_manifest_sha!=manifest.get('candidateFreeManifestSha256'):
        die('candidate-free packet hash binding mismatch')

    queue=jsonl(inp/'source-queue.jsonl',lambda r:r['position'])
    contexts=jsonl(inp/'source-contexts.jsonl',lambda r:r['position'])
    cells=jsonl(inp/'current-target-cells.jsonl',lambda r:f"{r['position']}::{r['locale']}")
    expected={f'{p}::{loc}' for p in range(1663,1683) for loc in LOCALES}
    ledger=jsonl(packet/'ledger.jsonl',lambda r:r['cellId'])
    proposals=jsonl(packet/'proposals.jsonl',lambda r:r['cellId'])
    if len(cells)!=240 or set(cells)!=expected or set(ledger)!=expected:
        die('candidate-free / ledger scope mismatch')
    expected_proposals={k for k,(r,_) in ledger.items() if r['decision'] in ('correction','refinement')}
    if set(proposals)!=expected_proposals: die('proposal set does not match correction/refinement ledger rows')
    if (packet/'holds.jsonl').read_bytes(): die('holds.jsonl should be empty for this caller-complete review')

    counts={}; confidence={}
    for key in sorted(expected,key=lambda k:(int(k.split('::',1)[0]),LOCALES.index(k.split('::',1)[1]))):
        cell,rawsha=cells[key]; rec,_=ledger[key]
        pos=cell['position']; locale=cell['locale']; source=queue[pos][0]
        context=contexts[pos][0]
        if source['sourceKey']!=cell['sourceKey'] or source['sourceKeySha256']!=cell['sourceKeySha256']:
            die(f'source queue binding mismatch: {key}')
        if rec.get('position')!=pos or rec.get('locale')!=locale or rec.get('sourceKey')!=source['sourceKey']:
            die(f'ledger identity mismatch: {key}')
        if rec.get('sourceKeySha256')!=source['sourceKeySha256'] or rec.get('candidateFreeCellSha256')!=rawsha:
            die(f'source/candidate row hash mismatch: {key}')
        if rec.get('currentTarget')!=cell['currentTarget'] or rec.get('currentTargetSha256')!=cell['currentTargetSha256']:
            die(f'current target binding mismatch: {key}')
        if sha(cell['currentTarget'].encode())!=cell['currentTargetSha256']:
            die(f'candidate current target hash mismatch: {key}')
        if rec.get('sourceContextSha256')!=cell['sourceContextSha256'] or rec.get('sourceContextSha256')!=context['callerContextSha256']:
            die(f'caller-context binding mismatch: {key}')
        if rec.get('callerCount')!=context['callerOccurrenceCount'] or rec.get('callerPaths')!=sorted({c['path'] for c in context['callers']}):
            die(f'caller-context summary mismatch: {key}')
        if rec.get('catalogPath')!=cell['catalogPath'] or rec.get('catalogFileSha256')!=cell['catalogFileSha256'] or rec.get('catalogGitBlob')!=cell['catalogGitBlob']:
            die(f'catalog pin mismatch: {key}')
        expected_tokens={
          'placeholders':cell['sourcePlaceholders'],'markupTags':cell['sourceMarkupTags'],
          'numericTokens':cell['sourceNumericTokens'],'protectedLiterals':cell['sourceProtectedLiterals']}
        if rec.get('sourceTokens')!=expected_tokens:
            die(f'source-token inventory mismatch: {key}')
        source_text=source['sourceKey']
        target=rec.get('recommendedTarget',cell['currentTarget'])
        checks=token_checks(source_text,target,cell)
        if not all(checks.values()) or rec.get('recommendedTargetTokenChecks')!=checks:
            die(f'token mismatch in review target: {key} {checks}')
        if any(not cell.get(field) for field in ('placeholderSequenceMatches','markupMatches','numericTokensMatch','protectedLiteralsMatch')):
            die(f'candidate-free target token alert unresolved: {key}')
        if source_text.rstrip().endswith(':') and not re.search(r'[:：]\s*$',target):
            die(f'colon prefix not retained: {key}')
        if '{error}' in source_text and ('{error}' not in target or not re.search(r'[:：]\s*\{error\}$',target)):
            die(f'error placeholder or separator not retained: {key}')
        if rec['decision']=='accept-current':
            if 'recommendedTarget' in rec: die(f'accept-current record contains a proposal: {key}')
        elif rec['decision'] in ('correction','refinement'):
            if rec.get('recommendedTargetSha256')!=sha(rec['recommendedTarget'].encode()): die(f'recommended target hash mismatch: {key}')
            prop=proposals[key][0]
            if prop.get('recommendedTarget')!=rec['recommendedTarget'] or prop.get('recommendedTargetSha256')!=rec['recommendedTargetSha256']:
                die(f'proposal/ledger text mismatch: {key}')
            for f in ('sourceKeySha256','currentTargetSha256','candidateFreeCellSha256','sourceContextSha256','exactHead','exactTree'):
                if prop.get(f)!=rec.get(f): die(f'proposal binding mismatch {f}: {key}')
        else:
            die(f'unexpected decision type: {key}')
        if rec.get('exactHead')!=HEAD or rec.get('exactTree')!=TREE:
            die(f'exact pin mismatch: {key}')
        counts[rec['decision']]=counts.get(rec['decision'],0)+1
        confidence[rec['confidence']]=confidence.get(rec['confidence'],0)+1

    if counts!={'accept-current':231,'correction':3,'refinement':6}:
        die(f'decision counts mismatch: {counts}')
    if summary.get('decisionCounts')!=counts or summary.get('confidenceCounts')!=confidence:
        die('summary counts mismatch')
    if summary.get('cellCount')!=240 or summary.get('proposalCount')!=9 or summary.get('holdCount')!=0:
        die('summary scope mismatch')

    for attname in ('attestation-before.json','attestation-after.json'):
        att=json.loads((packet/attname).read_text(encoding='utf-8'))
        if att.get('head')!=HEAD or att.get('tree')!=TREE or att.get('baseSha')!=BASE:
            die(f'{attname} exact pins mismatch')
        if att.get('candidateFreeChecksumListSha256')!=input_sum_sha or att.get('candidateFreeManifestSha256')!=input_manifest_sha:
            die(f'{attname} candidate-free pin mismatch')
        refs=att.get('remoteRefs',{})
        if refs.get('refs/heads/main')!=BASE or refs.get(f'refs/heads/{BRANCH}')!=HEAD or refs.get('refs/pull/209/head')!=HEAD:
            die(f'{attname} remote refs mismatch')

    output_sums=sums(packet/'SHA256SUMS.txt')
    if set(output_sums)!=(set(manifest['files'])|{'manifest.json'}):
        die('output checksum inventory mismatch')
    for name,h in output_sums.items():
        p=packet/name
        if not p.is_file() or sha(p.read_bytes())!=h: die(f'output checksum mismatch: {name}')

    repo_result='not-requested'
    if args.repo:
        repo=args.repo.resolve()
        if git(repo,'cat-file','-t',HEAD)!='commit' or git(repo,'rev-parse',HEAD+'^{tree}')!=TREE:
            die('local exact Git commit/tree mismatch')
        for cell,_ in cells.values():
            if git(repo,'cat-file','-t',cell['catalogGitBlob'])!='blob': die(f"missing catalog blob {cell['catalogGitBlob']}")
        repo_result='PASS exact commit/tree and catalog blobs'
    print('PASS: 240 cells (20 keys × 12 locales), caller/source/current-target pins, all token checks, 9 proposals, before/after exact refs, checksums'+(f'; {repo_result}' if args.repo else ''))

if __name__=='__main__':
    try: main()
    except subprocess.CalledProcessError as exc: die(exc.output.strip() or 'Git object check failed')
