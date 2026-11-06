#!/usr/bin/env python3
"""Verify a sealed slskR W1783-W1802 primary semantic review packet."""
from __future__ import annotations
import argparse, collections, hashlib, json, re, subprocess, sys
from pathlib import Path

HEAD='0264a4fcaa944fee61049efec0cf3c451416c8b9'
TREE='895e57c178d959a23aceddead27623f2dd854ba0'
OUT=Path(__file__).resolve().parent
INPUT_DEFAULT=OUT.parent/'candidate-free-input'

def sha(b): return hashlib.sha256(b).hexdigest()
def read_json(p): return json.loads(p.read_text(encoding='utf-8'))
def read_jsonl(p): return [json.loads(x) for x in p.read_text(encoding='utf-8').splitlines() if x.strip()]
def run(args,cwd=None):
    r=subprocess.run(args,cwd=cwd,text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    if r.returncode: raise RuntimeError(f'{args!r} failed: {r.stderr.strip()}')
    return r.stdout.strip()
def check_sums(path): run(['sha256sum','-c',path.name],cwd=path.parent)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--repo',type=Path)
    ap.add_argument('--candidate-free',type=Path,default=INPUT_DEFAULT)
    a=ap.parse_args(); inp=a.candidate_free.resolve()
    check_sums(inp/'SHA256SUMS.txt')
    im=read_json(inp/'manifest.json'); sm=read_json(OUT/'summary.json')
    if (im['head'],im['tree'])!=(HEAD,TREE) or (sm['head'],sm['tree'])!=(HEAD,TREE): raise ValueError('head/tree pin mismatch')
    if sm['candidateFreeChecksumListSha256']!=sha((inp/'SHA256SUMS.txt').read_bytes()): raise ValueError('candidate-free checksum-list hash mismatch')
    cells=read_jsonl(inp/'current-target-cells.jsonl')
    source_rows=read_jsonl(inp/'source-queue.jsonl')
    sources={x['position']:x for x in source_rows}
    contexts={x['position']:x for x in read_jsonl(inp/'source-contexts.jsonl')}
    if len(cells)!=240 or len({(x['position'],x['locale']) for x in cells})!=240: raise ValueError('input coverage is not exactly 240 cells')
    if sorted({x['position'] for x in cells})!=list(range(1783,1803)): raise ValueError('input position range mismatch')
    if len(contexts)!=20 or im['callerReferenceCount']!=29 or im['callerResolutionHoldCount']!=0: raise ValueError('source/caller coverage mismatch')
    ledger=read_jsonl(OUT/'primary-semantic-review-ledger.jsonl')
    if len(ledger)!=240 or len({(x['position'],x['locale']) for x in ledger})!=240: raise ValueError('ledger coverage is not exactly 240 cells')
    base={(x['position'],x['locale']):x for x in cells}; out={(x['position'],x['locale']):x for x in ledger}
    if set(base)!=set(out): raise ValueError('ledger cell keys differ from input')
    counts=collections.Counter(); before=collections.Counter(); after=collections.Counter()
    for key,b in base.items():
        e=out[key]; pos,locale=key; src=sources[pos]; ctx=contexts[pos]
        if e['sourceKey']!=src['sourceKey'] or e['sourceKeySha256']!=src['sourceKeySha256']: raise ValueError(f'source hash mismatch {key}')
        if e['currentTarget']!=b['currentTarget'] or e['currentTargetSha256']!=b['currentTargetSha256']: raise ValueError(f'current target mismatch {key}')
        if e['callerContextSha256']!=ctx['callerContextSha256'] or e['catalogPath']!=b['catalogPath'] or e['catalogFileSha256']!=b['catalogFileSha256'] or e['catalogGitBlob']!=b['catalogGitBlob']: raise ValueError(f'caller/catalog pin mismatch {key}')
        expected_refs=[{'path':c['path'],'line':c['line'],'lineText':c['lineText'],'lineSha256':c['lineSha256'],'contextStartLine':c['contextStartLine'],'contextEndLine':c['contextEndLine'],'contextSha256':c['contextSha256'],'fileSha256':c['fileSha256'],'gitBlob':c['gitBlob']} for c in ctx['callers']]
        if e['callerReferences']!=expected_refs or e['callerReferenceCount']!=ctx['callerOccurrenceCount']: raise ValueError(f'caller references mismatch {key}')
        if e.get('candidateFreeOnly') is not True or e.get('nativeSpeakerApproval') is not False: raise ValueError(f'provenance/approval label mismatch {key}')
        if sha(e['proposedTarget'].encode('utf-8'))!=e['proposedTargetSha256']: raise ValueError(f'proposal hash mismatch {key}')
        if e['disposition']=='accept_current' and e['proposedTarget']!=b['currentTarget']: raise ValueError(f'accept-current target differs {key}')
        if e['disposition'] in ('correction','refinement') and e['proposedTarget']==b['currentTarget']: raise ValueError(f'change disposition did not change target {key}')
        ph=re.findall(r'\{[A-Za-z][A-Za-z0-9_]*\}',e['proposedTarget'])
        nums=re.findall(r'\d+',e['proposedTarget'])
        markup=re.findall(r'</?[A-Za-z][^>]*>',e['proposedTarget'])
        protected=b['sourceProtectedLiterals']
        p_ok=ph==b['sourcePlaceholders'] and e['proposedPlaceholders']==ph
        n_ok=nums==b['sourceNumericTokens'] and e['proposedNumericTokens']==nums
        m_ok=markup==b['sourceMarkupTags'] and e['proposedMarkupTags']==markup
        l_ok=all(t in e['proposedTarget'] for t in protected) and e['proposedProtectedLiteralsPreserved'] is True
        if not (p_ok and n_ok and m_ok and l_ok): raise ValueError(f'proposal token mismatch {key}: {p_ok=} {n_ok=} {m_ok=} {l_ok=}')
        var=b['targetTokenVariants'][0]
        before['numeric']+=int(not var['numericTokensMatch']); before['protectedLiteral']+=int(not var['protectedLiteralsMatch']); before['placeholder']+=int(not var['placeholderSequenceMatches']); before['markup']+=int(not var['markupMatches'])
        after['numeric']+=int(not n_ok); after['protectedLiteral']+=int(not l_ok); after['placeholder']+=int(not p_ok); after['markup']+=int(not m_ok)
        counts[e['disposition']]+=1
    if before['numeric']!=1 or before['protectedLiteral']!=11 or before['placeholder'] or before['markup']: raise ValueError(f'baseline token mismatches differ: {before}')
    if any(after.values()): raise ValueError(f'proposed token mismatches remain: {after}')
    if counts['correction']+counts['refinement']!=len([e for e in ledger if e['disposition'] in ('correction','refinement')]): raise ValueError('changed-cell count mismatch')
    if sm['dispositions']!=dict(sorted(counts.items())) or sm['proposedChanges']!=counts['correction']+counts['refinement']: raise ValueError('summary disposition counts mismatch')
    # Hold and prior-window lineage must remain byte-identical and text-free.
    for name in ('active-hold-reattestation.jsonl','previous-window-readback-reattestation-hash-only.jsonl'):
        if (OUT/name).read_bytes()!=(inp/name).read_bytes(): raise ValueError(f'{name} differs from candidate-free input')
    hold=read_jsonl(OUT/'active-hold-reattestation.jsonl')
    if len(hold)!=1 or hold[0]['holdId']!='1719::id' or hold[0]['textIncluded'] is not False or hold[0]['targetHashUnchanged'] is not True or hold[0]['sourceContextUnchanged'] is not True: raise ValueError('active hold not preserved hash-only')
    previous=read_jsonl(OUT/'previous-window-readback-reattestation-hash-only.jsonl')
    if len(previous)!=240 or any(any(k in row for k in ('currentTarget','proposedTarget','targetText','translation')) for row in previous): raise ValueError('previous window is not 240-row hash-only')
    if a.repo:
        repo=a.repo.resolve(); head=run(['git','rev-parse','HEAD'],cwd=repo); tree=run(['git','rev-parse','HEAD^{tree}'],cwd=repo); status=run(['git','status','--porcelain=v1'],cwd=repo)
        if (head,tree)!=(HEAD,TREE): raise ValueError('worktree head/tree mismatch')
        if status: raise ValueError('worktree is dirty')
    print(json.dumps({'result':'PASS','head':HEAD,'tree':TREE,'cells':240,'sourceCount':20,'localeCount':12,'callerReferences':29,'dispositions':dict(sorted(counts.items())),'baselineTokenMismatches':dict(sorted(before.items())),'proposedTokenMismatches':dict(sorted(after.items())),'activeHold':'1719::id hash-only preserved','priorWindowReadbackHashes':240,'candidateFreeChecksums':'PASS','nativeSpeakerApproval':False,'worktreeCleanAndPinned':bool(a.repo)},ensure_ascii=False,indent=2))

if __name__=='__main__':
    try: main()
    except Exception as e:
        print(f'FAIL: {e}',file=sys.stderr); sys.exit(1)
