#!/usr/bin/env python3
"""Portable verifier for the sealed slskR W1663-W1682 cross-review."""
from __future__ import annotations
import argparse, hashlib, json, re, subprocess, sys
from pathlib import Path
R=Path(__file__).resolve().parent
TASK=R.parent
CF=TASK/'candidate-free-input'
P=TASK/'primary-review'
B=TASK/'blind-review'
HEAD='2ab97d1a21f7d001eb9470c76b3636f59f600609'
TREE='63097ec7c80be0bef55fb1bde5a38da7b6a59ce7'
BASE='1bbaec9fdc63a86de343e37e33bae70d44301a36'
BRANCH='codex/slskr-l10n-audit-20261104-resync'
LOCS=['es','zh-Hans','hi','de','ja','fr','pt-BR','ar','ko','zh-Hant','vi','id']
START,END=1663,1682

def sha(x):
    if isinstance(x,str): x=x.encode('utf-8')
    return hashlib.sha256(x).hexdigest()
def canon(x): return json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':'))
def require(ok,msg):
    if not ok: raise SystemExit('FAIL: '+msg)
def jsonl_raw(path):
    raw=path.read_bytes().splitlines(keepends=True)
    rows=[]; hashes=[]
    for line in raw:
        if line.strip():
            rows.append(json.loads(line))
            hashes.append(sha(line[:-1] if line.endswith(b'\n') else line))
    return rows,hashes
def jsonl(path): return jsonl_raw(path)[0]
def j(path): return json.loads(path.read_text(encoding='utf-8'))
def packet_sums(path):
    sums={}
    for line in (path/'SHA256SUMS.txt').read_text(encoding='utf-8').splitlines():
        if line.strip():
            digest,name=line.split(None,1); name=name.lstrip('* ')
            require(name not in sums,'duplicate checksum '+name+' in '+str(path)); sums[name]=digest
    actual={p.relative_to(path).as_posix():sha(p.read_bytes()) for p in path.rglob('*') if p.is_file() and p.name!='SHA256SUMS.txt'}
    require(sums==actual,'checksum/file set mismatch '+str(path))
    return sums
def toks(s):
    placeholders=re.findall(r'\{[A-Za-z][A-Za-z0-9_]*\}',s)
    markup=re.findall(r'</?[A-Za-z][^>]*>',s)
    numbers=re.findall(r'(?<![A-Za-z])\d+(?:[.,]\d+)?%?(?![A-Za-z])',s)
    protected=[]
    for x in re.findall(r'(?<![A-Za-z0-9])(?:[A-Z]{2,}[A-Z0-9]*|ffmpeg|Chromaprint|Soulseek|Spotify|YouTube|Pushbullet|Matrix|WebSocket|OpenAI)(?![A-Za-z0-9])',s):
        if x not in protected: protected.append(x)
    return {'placeholders':placeholders,'markup':markup,'numericTokens':numbers,'protectedLiterals':protected}
def proposal_map(path):
    rows=jsonl(path)
    return {(x['sourceKey'],x['locale']):x for x in rows}
def verify_packet_pin(name,path,manifest,pin):
    sums=packet_sums(path)
    require(sums==pin['filesSha256'],'input files differ from sealed '+name+' pins')
    require(sha((path/'SHA256SUMS.txt').read_bytes())==pin['checksumListSha256'],'input checksum-list hash '+name)
    require(sha((path/'manifest.json').read_bytes())==pin['manifestSha256'],'input manifest hash '+name)
    return sums

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--repo',type=Path,help='optional exact pinned worktree for live catalog/object readback')
    args=ap.parse_args()
    output_files=packet_sums(R)
    m=j(R/'manifest.json')
    require(m['exactHead']==HEAD and m['exactTree']==TREE and m['baseSha']==BASE and m['branch']==BRANCH,'manifest exact refs')
    require(m['sourceRange']==[START,END] and m['cellCount']==240,'manifest scope')
    pins=m['inputPackets']
    for name,path in [('candidate-free',CF),('primary',P),('blind',B)]:
        require(name in pins,'missing input pin '+name)
        verify_packet_pin(name,path,None,pins[name])
    cfm=j(CF/'manifest.json'); pm=j(P/'manifest.json'); bm=j(B/'manifest.json')
    require(cfm['head']==HEAD and cfm['tree']==TREE and cfm['baseSha']==BASE,'candidate-free pins')
    require(pm['exactHead']==HEAD and pm['exactTree']==TREE and bm['exactHead']==HEAD and bm['exactTree']==TREE,'reviewer refs')
    cfc,cfhashes=jsonl_raw(CF/'current-target-cells.jsonl')
    pledger=jsonl(P/'ledger.jsonl'); bledger=jsonl(B/'blind-ledger.jsonl')
    pp=proposal_map(P/'proposals.jsonl'); bp=proposal_map(B/'proposals.jsonl')
    cross,cross_hashes=jsonl_raw(R/'ledger.jsonl'); proposals=jsonl(R/'proposals.jsonl'); holds=jsonl(R/'holds.jsonl')
    require(len(cfc)==len(pledger)==len(bledger)==len(cross)==240,'240-row coverage')
    require(len(holds)==0,'cross-review holds must be empty for this result')
    keys=[(x['sourceKey'],x['locale']) for x in cfc]
    require(len(set(keys))==240,'candidate-free duplicate cell')
    expected=[(key,loc) for key in dict.fromkeys(x['sourceKey'] for x in cfc) for loc in LOCS]
    require(keys==expected,'candidate-free cell order/coverage')
    pmap={(x['sourceKey'],x['locale']):x for x in pledger}
    bmap={(x['sourceKey'],x['locale']):x for x in bledger}
    cmap={(x['sourceKey'],x['locale']):x for x in cross}
    require(len(pmap)==len(bmap)==len(cmap)==240,'duplicate reviewer/cross cell')
    proposed={(x['sourceKey'],x['locale']):x for x in proposals}
    require(len(proposed)==len(proposals),'duplicate final proposal')
    changed=[]
    final_counts={}
    for c,cfrowhash in zip(cfc,cfhashes):
        key=(c['sourceKey'],c['locale']); p=pmap[key]; b=bmap[key]; x=cmap[key]
        require(p['candidateFreeCellSha256']==cfrowhash and b['candidateFreeRowSha256']==cfrowhash,'candidate-free row hash '+str(key))
        for row,label in ((p,'primary'),(b,'blind')):
            require(row['exactHead']==HEAD and row['exactTree']==TREE,'reviewer pin '+label+str(key))
            require(row['sourceKey']==c['sourceKey'] and row['sourceKeySha256']==sha(c['sourceKey']),'reviewer source '+label+str(key))
            require(row['currentTarget']==c['currentTarget'] and row['currentTargetSha256']==c['currentTargetSha256'],'reviewer current target '+label+str(key))
            context=row.get('sourceContextSha256',row.get('callerContextSha256'))
            require(context==c['sourceContextSha256'],'reviewer caller hash '+label+str(key))
        require(p['catalogFileSha256']==c['catalogFileSha256'] and p['catalogGitBlob']==c['catalogGitBlob'] and p['catalogPath']==c['catalogPath'],'primary catalog pin '+str(key))
        require(x['candidateFreeCellSha256']==cfrowhash and x['sourceContextSha256']==c['sourceContextSha256'],'cross candidate/caller hash '+str(key))
        require(x['exactHead']==HEAD and x['exactTree']==TREE,'cross exact ref '+str(key))
        require(x['sourceKey']==c['sourceKey'] and x['sourceKeySha256']==sha(c['sourceKey']),'cross source key '+str(key))
        require(x['currentTarget']==c['currentTarget'] and x['currentTargetSha256']==c['currentTargetSha256'],'cross current target '+str(key))
        require(x['locale']==c['locale'] and x['position']==c['position'],'cross coordinates '+str(key))
        require(x['primaryDecision']==p['decision'] and x['blindDecision']==b['decision'],'cross source decisions '+str(key))
        for origin,pm_,candidate_map in [('primary',pp,p),('blind',bp,b)]:
            prop=pm_.get(key)
            claimed=x[origin+'Proposal']
            if prop is None:
                require(claimed is None,'unexpected attached proposal '+origin+str(key))
            else:
                require(claimed is not None,'missing attached proposal '+origin+str(key))
                require(claimed['recommendedTarget']==prop['recommendedTarget'] and claimed['recommendedTargetSha256']==prop['recommendedTargetSha256'],'attached proposal text/hash '+origin+str(key))
                require(prop['sourceKeySha256']==c['sourceKeySha256'] and prop.get('sourceContextSha256',prop.get('callerContextSha256'))==c['sourceContextSha256'] and prop['currentTargetSha256']==c['currentTargetSha256'],'proposal pins '+origin+str(key))
        final=x['recommendedTarget']; final_hash=sha(final)
        require(x['recommendedTargetSha256']==final_hash,'final target hash '+str(key))
        sig=toks(c['sourceKey']); fsig=toks(final)
        check={'placeholders':sig['placeholders']==fsig['placeholders'],'markup':sig['markup']==fsig['markup'],'numericTokens':sig['numericTokens']==fsig['numericTokens'],'protectedLiterals':all(z in fsig['protectedLiterals'] for z in sig['protectedLiterals'])}
        require(all(check.values()),'final token integrity '+str(key))
        require(x['finalTokenChecks']==check,'recorded final token checks '+str(key))
        require(x['currentTargetSha256']==c['currentTargetSha256'],'source target hash '+str(key))
        if final!=c['currentTarget']:
            changed.append(key)
            require(key in proposed,'missing final proposal '+str(key))
            q=proposed[key]
            require(q['recommendedTarget']==final and q['recommendedTargetSha256']==final_hash,'proposal ledger target '+str(key))
            require(q['candidateFreeCellSha256']==cfrowhash and q['sourceContextSha256']==c['sourceContextSha256'],'proposal ledger pins '+str(key))
        else:
            require(key not in proposed,'unchanged cell in proposal ledger '+str(key))
        final_counts[x['crossDecision']]=final_counts.get(x['crossDecision'],0)+1
    require(len(changed)==len(proposals)==12,'final changed/proposal count')
    require(set(cmap)==set((x['sourceKey'],x['locale']) for x in cross),'cross key set')
    summ=j(R/'summary.json')
    require(summ['cellCount']==240 and summ['changedCellCount']==12 and summ['retainedCurrentCount']==228,'summary counts')
    require(summ['crossDecisionCounts']==final_counts,'summary decision counts')
    for phase in ('entry','exit'):
        at=j(R/f'{phase}-attestation.json')
        require(at['pr']['state']=='OPEN' and at['pr']['isDraft'] is True,'live PR status '+phase)
        require(at['pr']['headRefOid']==HEAD and at['pr']['baseRefOid']==BASE and at['pr']['headRefName']==BRANCH and at['pr']['baseRefName']=='main','PR API refs '+phase)
        require(at['headTree']==TREE and at['baseTree']==m['baseTree'],'API tree refs '+phase)
        require(at['branchRef']==HEAD and at['pullRef']==HEAD and at['mainRef']==BASE,'remote refs '+phase)
        require(at['localHead']==HEAD and at['localTree']==TREE and at['localClean'] is True,'local exact source '+phase)
    require(j(R/'entry-attestation.json')['pinTuple']==j(R/'exit-attestation.json')['pinTuple'],'entry/exit ref stability')
    if args.repo:
        repo=args.repo.resolve()
        def git(*cmd): return subprocess.check_output(['git','-C',str(repo),*cmd],text=True).strip()
        require(git('rev-parse','HEAD')==HEAD and git('rev-parse','HEAD^{tree}')==TREE,'exact worktree head/tree')
        require(not git('status','--porcelain=v1'),'exact worktree is dirty')
        catalogs={}
        for loc in LOCS:
            path=f'web/src/lib/locales/ui-labels.{loc}.json'
            data=json.loads((repo/path).read_text(encoding='utf-8'))
            blob=git('rev-parse',f'HEAD:{path}')
            require(blob==cfc[(LOCS.index(loc))]['catalogGitBlob'],'catalog blob '+loc)
            catalogs[loc]=data
        for c in cfc:
            require(catalogs[c['locale']][c['sourceKey']]==c['currentTarget'],'live catalog target '+str((c['position'],c['locale'])))
        exact=True
    else: exact=False
    print(json.dumps({'result':'PASS','head':HEAD,'tree':TREE,'cells':240,'changedCells':len(changed),'retainedCurrent':240-len(changed),'proposals':len(proposals),'holds':len(holds),'crossDecisionCounts':final_counts,'candidateFreeRowsBound':240,'primaryRowsBound':240,'blindRowsBound':240,'outputFilesChecksummed':len(output_files),'exactWorktreeReadback':exact},ensure_ascii=False,indent=2))
if __name__=='__main__': main()
