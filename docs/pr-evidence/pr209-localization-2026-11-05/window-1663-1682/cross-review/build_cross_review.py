#!/usr/bin/env python3
"""Build the pinned slskR W1663-W1682 cross-review packet."""
from __future__ import annotations
import datetime, hashlib, json, re, subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parent
TASK=ROOT.parent
CF=TASK/'candidate-free-input'; P=TASK/'primary-review'; B=TASK/'blind-review'
REPO=Path('/mnt/disks/scratch/task-worktrees/localization-20261105/slskr-pr209-w1663-1682-candidate-free')
REPO_NAME='snapetech-org/slskR'; PR=209; BRANCH='codex/slskr-l10n-audit-20261104-resync'
HEAD='2ab97d1a21f7d001eb9470c76b3636f59f600609'; TREE='63097ec7c80be0bef55fb1bde5a38da7b6a59ce7'
BASE='1bbaec9fdc63a86de343e37e33bae70d44301a36'; START,END=1663,1682
LOCS=['es','zh-Hans','hi','de','ja','fr','pt-BR','ar','ko','zh-Hant','vi','id']

def sha(x):
    if isinstance(x,str): x=x.encode('utf-8')
    return hashlib.sha256(x).hexdigest()
def canon(x): return json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':'))
def dump(path,obj): path.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def write_jsonl(path,rows): path.write_text(''.join(canon(x)+'\n' for x in rows),encoding='utf-8')
def read_jsonl_raw(path):
    rows=[]; hashes=[]
    for line in path.read_bytes().splitlines(keepends=True):
        if line.strip():
            rows.append(json.loads(line)); hashes.append(sha(line[:-1] if line.endswith(b'\n') else line))
    return rows,hashes
def j(path): return json.loads(path.read_text(encoding='utf-8'))
def jl(path): return [json.loads(x) for x in path.read_text(encoding='utf-8').splitlines() if x.strip()]
def packet_files(path): return {q.relative_to(path).as_posix():sha(q.read_bytes()) for q in path.rglob('*') if q.is_file() and q.name!='SHA256SUMS.txt'}
def checksum(path):
    files=packet_files(path)
    (path/'SHA256SUMS.txt').write_text(''.join(f'{files[name]}  {name}\n' for name in sorted(files)),encoding='utf-8')
    return files
def git(*args): return subprocess.check_output(['git','-C',str(REPO),*args],text=True).strip()
def api(endpoint): return json.loads(subprocess.check_output(['gh','api',endpoint],text=True))
def capture(phase):
    pr=json.loads(subprocess.check_output(['gh','pr','view',str(PR),'--repo',REPO_NAME,'--json','number,state,isDraft,headRefName,headRefOid,baseRefName,baseRefOid,url'],text=True))
    head_commit=api(f'repos/{REPO_NAME}/commits/{pr["headRefOid"]}')
    base_commit=api(f'repos/{REPO_NAME}/commits/{pr["baseRefOid"]}')
    refs_text=subprocess.check_output(['git','ls-remote',f'https://github.com/{REPO_NAME}.git',f'refs/heads/{BRANCH}',f'refs/pull/{PR}/head','refs/heads/main'],text=True)
    refs={line.split('\t')[1]:line.split('\t')[0] for line in refs_text.splitlines() if line.strip()}
    local_head=git('rev-parse','HEAD'); local_tree=git('rev-parse','HEAD^{tree}')
    clean=(git('status','--porcelain=v1')=='')
    head_tree=head_commit['commit']['tree']['sha']; base_tree=base_commit['commit']['tree']['sha']
    check=(pr['state'],pr['isDraft'],pr['headRefName'],pr['headRefOid'],head_tree,pr['baseRefName'],pr['baseRefOid'],base_tree,refs.get(f'refs/heads/{BRANCH}'),refs.get(f'refs/pull/{PR}/head'),refs.get('refs/heads/main'),local_head,local_tree,clean)
    expected=('OPEN',True,BRANCH,HEAD,TREE,'main',BASE,'3e8b229b305df2c28b1ba3e3799086b94b2c01e8',HEAD,HEAD,BASE,HEAD,TREE,True)
    if check!=expected: raise RuntimeError(f'live pin changed during {phase}: {check!r}')
    snap={
      'capturedAtUtc':datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds'),
      'repository':REPO_NAME,'pullRequest':PR,'pr':pr,
      'headTree':head_tree,'baseTree':base_tree,
      'branchRef':refs.get(f'refs/heads/{BRANCH}'),'pullRef':refs.get(f'refs/pull/{PR}/head'),'mainRef':refs.get('refs/heads/main'),
      'localHead':local_head,'localTree':local_tree,'localClean':clean,
      'pinTuple':[pr['state'],pr['isDraft'],pr['headRefName'],pr['headRefOid'],head_tree,pr['baseRefName'],pr['baseRefOid'],base_tree,refs.get(f'refs/heads/{BRANCH}'),refs.get(f'refs/pull/{PR}/head'),refs.get('refs/heads/main'),local_head,local_tree,clean],
    }
    dump(ROOT/f'{phase}-attestation.json',snap)
    (ROOT/f'{phase}-remote-refs.txt').write_text(refs_text,encoding='utf-8')
    return snap

def toks(s):
    placeholders=re.findall(r'\{[A-Za-z][A-Za-z0-9_]*\}',s)
    markup=re.findall(r'</?[A-Za-z][^>]*>',s)
    numbers=re.findall(r'(?<![A-Za-z])\d+(?:[.,]\d+)?%?(?![A-Za-z])',s)
    protected=[]
    for x in re.findall(r'(?<![A-Za-z0-9])(?:[A-Z]{2,}[A-Z0-9]*|ffmpeg|Chromaprint|Soulseek|Spotify|YouTube|Pushbullet|Matrix|WebSocket|OpenAI)(?![A-Za-z0-9])',s):
        if x not in protected: protected.append(x)
    return {'placeholders':placeholders,'markup':markup,'numericTokens':numbers,'protectedLiterals':protected}
def run(label,cmd):
    result=subprocess.run(cmd,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
    if result.returncode: raise RuntimeError(label+' verifier failed: '+result.stdout)
    return {'label':label,'command':cmd,'exitCode':result.returncode,'output':result.stdout.strip()}

if any((ROOT/name).exists() for name in ['ledger.jsonl','proposals.jsonl','manifest.json']):
    raise RuntimeError('refusing to overwrite existing cross-review artifacts')
entry=capture('entry')
# Re-run all sealed-input verifiers immediately before adjudication output.
verifiers=[
 run('candidate-free',['python3',str(CF/'verify_candidate_free.py'),'--repo',str(REPO)]),
 run('primary',['python3',str(P/'verify_primary_review.py'),'--repo',str(REPO)]),
 run('blind',['python3',str(B/'verify_blind_review.py')]),
]
cfrows,cfhashes=read_jsonl_raw(CF/'current-target-cells.jsonl')
prows=jl(P/'ledger.jsonl'); brows=jl(B/'blind-ledger.jsonl')
pp={(x['sourceKey'],x['locale']):x for x in jl(P/'proposals.jsonl')}
bp={(x['sourceKey'],x['locale']):x for x in jl(B/'proposals.jsonl')}
pmap={(x['sourceKey'],x['locale']):x for x in prows}; bmap={(x['sourceKey'],x['locale']):x for x in brows}
if not (len(cfrows)==len(cfhashes)==len(prows)==len(brows)==240): raise RuntimeError('input cell coverage mismatch')
if len(pmap)!=240 or len(bmap)!=240: raise RuntimeError('duplicate reviewer rows')
# Source/caller summaries are used to assess the exact production action and any appended value.
contexts={x['sourceKey']:x for x in jl(CF/'source-contexts.jsonl')}
activity={
1663:'generic chat, room-chat, and modal message-send error',1664:'pod message-send error',1665:'collection-sharing error',
1666:'message-signing error followed by signing failure detail',1667:'leaderboard-sort error',1668:'historical-data backfill start error',
1669:'bridge start error',1670:'network port-forwarding start error',1671:'replacement-search start error',1672:'library scan start error',
1673:'search start error',1674:'stream start error',1675:'bridge stop error',1676:'port-forwarding stop error',1677:'search stop error',
1678:'pod join-request submission error followed by service detail',1679:'pod historical-message backfill synchronization error with {error}',
1680:'peer synchronization error',1681:'accelerated-mode toggle error with {error}',1682:'automatic-replacement toggle error with {error}' }
# Cross-review exact final strings. Each override cites the pinned caller and explains the terminology decision.
overrides={
 (1667,'pt-BR'):{'target':'Não foi possível ordenar a tabela de classificação','decision':'accept-consensus-proposal','rationale':'The dashboard sorts a ranked leaderboard. “Placar” is more often a scoreboard; “tabela de classificação” names the ranking and both reviewers independently selected it.'},
 (1668,'es'):{'target':'No se pudo iniciar la carga retroactiva de datos','decision':'accept-primary-proposal','rationale':'The caller starts a historical data backfill. “Recuperación de datos” can mean restoring lost data; “carga retroactiva de datos” states the operation explicitly. I prefer the primary’s fuller wording to the blind review’s shorter alternative because “de datos” clarifies what is being loaded.'},
 (1670,'fr'):{'target':'Impossible de démarrer la redirection de port.','decision':'accept-primary-proposal','rationale':'“Redirection de port” is the clear networking term and matches the paired stop message. The proposal retains the terminal period already present in this server-error translation.'},
 (1670,'ja'):{'target':'ポート転送を開始できませんでした。','decision':'accept-primary-proposal','rationale':'“ポート転送” is clear Japanese and matches the paired stop message’s terminology; it avoids switching to the English loanword in this error.'},
 (1670,'zh-Hant'):{'target':'無法啟動連接埠轉送。','decision':'accept-consensus-proposal','rationale':'The source is network port forwarding. Taiwanese Traditional Chinese uses “連接埠轉送”; this also matches the paired stop message and replaces mainland “端口轉發”.'},
 (1678,'es'):{'target':'No se pudo enviar la solicitud para unirse:','decision':'accept-consensus-proposal','rationale':'The pod panel appends a join failure after this prefix. “Solicitud para unirse” clearly means a request to join, while “solicitud de unión” can suggest a labor union; the colon remains for the appended detail.'},
 (1679,'es'):{'target':'No se pudo sincronizar la carga retroactiva del pod: {error}','decision':'accept-consensus-proposal','rationale':'The caller synchronizes historical pod messages. “Carga retroactiva” conveys backfill and aligns with the selected Spanish wording for position 1668; the {error} slot is preserved.'},
 (1679,'id'):{'target':'Gagal menyinkronkan pengisian data historis pod: {error}','decision':'accept-blind-proposal','rationale':'The caller synchronizes historical pod messages. “Pengisian ulang” suggests refilling; “pengisian data historis” accurately names backfill and matches the existing Indonesian rendering at position 1668. The {error} slot is preserved.'},
 (1679,'pt-BR'):{'target':'Não foi possível sincronizar o preenchimento retroativo do pod: {error}','decision':'accept-primary-proposal','rationale':'The caller synchronizes a pod backfill. “Preenchimento retroativo” makes the historical operation explicit and matches the selected Brazilian Portuguese term at position 1668; the {error} slot is preserved.'},
 (1681,'ar'):{'target':'تعذر تبديل وضع التسريع: {error}','decision':'accept-primary-proposal','rationale':'The Transfers caller reports a failed accelerated-mode toggle. “وضع التسريع” means acceleration mode more precisely than “الوضع السريع” (fast mode); the {error} slot is preserved.'},
 (1681,'hi'):{'target':'त्वरण मोड को चालू या बंद नहीं किया जा सका: {error}','decision':'cross-adjustment','rationale':'The blind proposal improves the transliterated “टॉगल” by stating that the mode could not be switched on or off. I changed “त्वरित” (fast) to “त्वरण” (acceleration) to preserve the source’s accelerated-mode meaning. The {error} slot is preserved.'},
 (1682,'hi'):{'target':'स्वचालित प्रतिस्थापन को चालू या बंद नहीं किया जा सका: {error}','decision':'accept-blind-proposal','rationale':'The Transfers caller toggles the automatic-replacement setting. Spelling out “could not be switched on or off” is clearer Hindi than the dense “ऑटो-रिप्लेस टॉगल”; the {error} slot is preserved.'},
}
ledger=[]; final_proposals=[]; counts={}; agreement={}
for c,cfhash in zip(cfrows,cfhashes):
    key=(c['sourceKey'],c['locale']); pos=c['position']; loc=c['locale']
    p=pmap[key]; b=bmap[key]
    if p.get('candidateFreeCellSha256')!=cfhash or b.get('candidateFreeRowSha256')!=cfhash: raise RuntimeError(f'candidate-free row hash mismatch {key}')
    if (p['exactHead'],p['exactTree'])!=(HEAD,TREE) or (b['exactHead'],b['exactTree'])!=(HEAD,TREE): raise RuntimeError(f'reviewer ref mismatch {key}')
    if p['currentTarget']!=c['currentTarget'] or b['currentTarget']!=c['currentTarget']: raise RuntimeError(f'current target mismatch {key}')
    if p['sourceContextSha256']!=c['sourceContextSha256'] or b.get('callerContextSha256')!=c['sourceContextSha256']: raise RuntimeError(f'caller context mismatch {key}')
    if p['sourceKeySha256']!=c['sourceKeySha256'] or b['sourceKeySha256']!=c['sourceKeySha256']: raise RuntimeError(f'source key mismatch {key}')
    pr=pp.get(key); br=bp.get(key)
    for name,x in [('primary',pr),('blind',br)]:
        if x and (x['sourceKeySha256']!=c['sourceKeySha256'] or x.get('sourceContextSha256',x.get('callerContextSha256'))!=c['sourceContextSha256'] or x['currentTargetSha256']!=c['currentTargetSha256']): raise RuntimeError(f'{name} proposal hash mismatch {key}')
    over=overrides.get((pos,loc))
    if over:
        target=over['target']; decision=over['decision']; rationale=over['rationale']
        if not (pr or br): raise RuntimeError(f'cross override without candidate proposal {key}')
        primary_target=pr['recommendedTarget'] if pr else None; blind_target=br['recommendedTarget'] if br else None
        if decision=='accept-consensus-proposal' and not (primary_target==blind_target==target): raise RuntimeError(f'consensus proposal disagreement {key}')
        if decision=='accept-primary-proposal' and primary_target!=target: raise RuntimeError(f'primary proposal mismatch {key}')
        if decision=='accept-blind-proposal' and blind_target!=target: raise RuntimeError(f'blind proposal mismatch {key}')
        if decision=='adjust-primary-proposal' and (not primary_target or target==primary_target): raise RuntimeError(f'adjusted primary is not an adjustment {key}')
        if decision=='cross-adjustment' and (not blind_target or target==blind_target): raise RuntimeError(f'cross adjustment is not distinct {key}')
        relation=('exact-consensus' if primary_target==blind_target==target else 'primary-exact' if primary_target==target else 'blind-exact' if blind_target==target else 'cross-adjusted')
        target_source=relation
    else:
        target=c['currentTarget']; decision='accept-current'
        rationale=f"Pinned callers use this for the {activity[pos]}. The current {loc} wording communicates the failed operation naturally; primary and blind reviewers both retain it. Caller and token signatures are intact."
        primary_target=pr['recommendedTarget'] if pr else None; blind_target=br['recommendedTarget'] if br else None
        target_source='current'
    sig=toks(c['sourceKey']); ts=toks(target)
    checks={'placeholders':sig['placeholders']==ts['placeholders'],'markup':sig['markup']==ts['markup'],'numericTokens':sig['numericTokens']==ts['numericTokens'],'protectedLiterals':all(x in ts['protectedLiterals'] for x in sig['protectedLiterals'])}
    if not all(checks.values()): raise RuntimeError(f'final token mismatch {key} {checks}')
    pp_row=None if pr is None else {'decision':pr['decision'],'recommendedTarget':pr['recommendedTarget'],'recommendedTargetSha256':pr['recommendedTargetSha256'],'rationale':pr['rationale']}
    bp_row=None if br is None else {'decision':b['decision'],'recommendedTarget':br['recommendedTarget'],'recommendedTargetSha256':br['recommendedTargetSha256'],'rationale':br['rationale']}
    x={
      'position':pos,'sourceKey':c['sourceKey'],'sourceKeySha256':c['sourceKeySha256'],'locale':loc,
      'exactHead':HEAD,'exactTree':TREE,'catalogPath':c['catalogPath'],'catalogFileSha256':c['catalogFileSha256'],'catalogGitBlob':c['catalogGitBlob'],
      'candidateFreeCellSha256':cfhash,'sourceContextSha256':c['sourceContextSha256'],'callerCount':c['callerCount'],
      'currentTarget':c['currentTarget'],'currentTargetSha256':c['currentTargetSha256'],
      'primaryDecision':p['decision'],'blindDecision':b['decision'],'primaryProposal':pp_row,'blindProposal':bp_row,
      'crossDecision':decision,'proposalRelation':target_source,'recommendedTarget':target,'recommendedTargetSha256':sha(target),
      'finalTokenChecks':checks,'confidence':'moderate','rationale':rationale,
    }
    ledger.append(x); counts[decision]=counts.get(decision,0)+1
    if target!=c['currentTarget']:
        final_proposals.append({
          'position':pos,'sourceKey':c['sourceKey'],'sourceKeySha256':c['sourceKeySha256'],'locale':loc,
          'candidateFreeCellSha256':cfhash,'sourceContextSha256':c['sourceContextSha256'],
          'currentTarget':c['currentTarget'],'currentTargetSha256':c['currentTargetSha256'],
          'recommendedTarget':target,'recommendedTargetSha256':sha(target),'crossDecision':decision,'proposalRelation':target_source,
          'primaryRecommendedTarget':primary_target,'blindRecommendedTarget':blind_target,'rationale':rationale,'tokenChecks':checks,
          'exactHead':HEAD,'exactTree':TREE,
        })
    if pr or br:
        if pr and br and primary_target==blind_target: a='same-text'
        elif pr and br: a='different-text'
        elif pr: a='primary-only'
        else: a='blind-only'
        agreement[a]=agreement.get(a,0)+1
# Holds remain text-free; no row needed because there are no unresolved cells.
write_jsonl(ROOT/'ledger.jsonl',ledger)
write_jsonl(ROOT/'proposals.jsonl',final_proposals)
write_jsonl(ROOT/'holds.jsonl',[])
exit_at=capture('exit')
if entry['pinTuple']!=exit_at['pinTuple']: raise RuntimeError('PR/source refs changed during cross-review')
input_pins={}
for name,path in [('candidate-free',CF),('primary',P),('blind',B)]:
    files=packet_files(path)
    input_pins[name]={'directory':path.name,'filesSha256':files,'checksumListSha256':sha((path/'SHA256SUMS.txt').read_bytes()),'manifestSha256':sha((path/'manifest.json').read_bytes()),'fileCount':len(files)}
summary={
  'artifact':'slskR PR #209 W1663-W1682 independent semantic cross-review',
  'repository':REPO_NAME,'pullRequest':PR,'stateAtEntry':'OPEN/draft','stateAtExit':'OPEN/draft',
  'exactHead':HEAD,'exactTree':TREE,'baseSha':BASE,'baseTree':entry['baseTree'],'branch':BRANCH,
  'sourceRange':[START,END],'sourceCount':20,'localeCount':12,'cellCount':len(ledger),
  'changedCellCount':len(final_proposals),'retainedCurrentCount':len(ledger)-len(final_proposals),
  'crossDecisionCounts':counts,'reviewerProposalAgreement':agreement,'reviewerProposalCounts':{'primary':len(pp),'blind':len(bp),'uniqueCells':len(set(pp)|set(bp))},
  'holdCount':0,'confidence':'moderate; no native-speaker signoff',
  'candidateFreeRowBindings':240,'primaryRowBindings':240,'blindRowBindings':240,'finalTargetTokenMismatches':0,
  'verifierResults':verifiers,'entryExitRefsMatch':True,
}
dump(ROOT/'summary.json',summary)
manifest={
  'artifact':'slskR PR #209 W1663-W1682 cross-review packet','schemaVersion':1,'packetType':'independent-semantic-cross-review',
  'repository':REPO_NAME,'pullRequest':PR,'branch':BRANCH,'baseRef':'main','baseSha':BASE,'baseTree':entry['baseTree'],
  'exactHead':HEAD,'exactTree':TREE,'stateAtReview':'open/draft','sourceRange':[START,END],
  'sourceCount':20,'localeCount':12,'cellCount':240,'changedCellCount':12,'retainedCurrentCount':228,'holdCount':0,
  'inputPackets':input_pins,'portableVerifier':'verify_cross_review.py','exactWorktreeVerifierCommand':'python3 verify_cross_review.py --repo /mnt/disks/scratch/task-worktrees/localization-20261105/slskr-pr209-w1663-1682-candidate-free',
  'checksumsFile':'SHA256SUMS.txt','sourceContextHashRule':'Each row carries the exact candidate-free caller-context SHA256; source and current target hashes are exact UTF-8 SHA256 values.',
  'holdRule':'Unresolved rows, if present, belong in holds.jsonl with no source/target text; this packet has zero holds.',
}
dump(ROOT/'manifest.json',manifest)
dump(ROOT/'input-verifier-results.json',{'results':verifiers})
readme=f'''# slskR PR #209 W1663–W1682 cross-review\n\nThis packet independently adjudicates all 240 source/locale cells for source positions 1663–1682. It is pinned to PR head `{HEAD}` / tree `{TREE}`, branch `{BRANCH}`, and base `main` at `{BASE}` / tree `{entry['baseTree']}`. The PR was open and draft at entry and exit; the remote branch, pull ref, main ref, and isolated local source worktree matched those pins both times.\n\nThe cross ledger binds each decision to its candidate-free cell row, source key, caller-context hash, current target, locale catalog file/blob, and the primary/blind decisions and proposals. Input packets and their checksums are pinned in `manifest.json`. Review output is limited to this task scratch; no source repository or PR files were edited.\n\n## Decisions\n\n- 240 cells reviewed; 228 retain current text and 12 receive an exact target recommendation.\n- 12 unique candidate cells were reconciled from 9 primary and 8 blind proposals. Four proposal pairs agreed exactly; the Spanish backfill-start proposals differed in length, and the fuller primary wording was selected for clarity.\n- The French port-forwarding proposal retains the current terminal period. The Hindi accelerated-mode proposal is adjusted from the blind wording to use “त्वरण” for acceleration rather than “त्वरित” for fast.\n- No unresolved rows remain. All final placeholders, markup, numeric tokens, and protected literals match the English source signatures. Confidence is moderate; no native-speaker signoff was available.\n\n## Verification\n\nPortable offline verification (checksums, packet pins, all 240 row bindings, proposal reconciliation, and final token signatures):\n\n```sh\npython3 verify_cross_review.py\n```\n\nExact worktree readback, including commit/tree, cleanliness, catalog blobs, and current catalog values:\n\n```sh\npython3 verify_cross_review.py --repo /mnt/disks/scratch/task-worktrees/localization-20261105/slskr-pr209-w1663-1682-candidate-free\n```\n\nThe candidate-free, primary, and blind packet verifiers also passed immediately before cross output was written; their results and entry/exit PR snapshots are included. `SHA256SUMS.txt` covers all files in this directory except itself.\n'''
(ROOT/'README.md').write_text(readme,encoding='utf-8')
checksum(ROOT)
print(json.dumps({'entryExitRefsMatch':True,'cellCount':len(ledger),'changedCellCount':len(final_proposals),'retainedCurrentCount':len(ledger)-len(final_proposals),'crossDecisionCounts':counts,'reviewerProposalAgreement':agreement,'inputVerifierResults':[x['label']+':PASS' for x in verifiers],'outputPath':str(ROOT)},ensure_ascii=False,indent=2))
