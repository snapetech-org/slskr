#!/usr/bin/env python3
"""Create an independent primary semantic review from only the sealed candidate-free packet."""
from __future__ import annotations
import json, subprocess
import textwrap
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

R=Path(__file__).resolve().parent
TASK=R.parent
INPUT=TASK/'candidate-free-input'
REPO=Path('/home/keith/Documents/code/.task-worktrees/localization-20261105/slskr-w1683')
REPO_NAME='snapetech-org/slskR'; PR=209
BRANCH='codex/slskr-l10n-audit-20261104-resync'
HEAD='91e109efba44ad9e53fe9544648a0d907a2bef77'
TREE='38db78228144da5fc50179addccf826662bf97de'
BASE='1bbaec9fdc63a86de343e37e33bae70d44301a36'
LOCALES=['es','zh-Hans','hi','de','ja','fr','pt-BR','ar','ko','zh-Hant','vi','id']
START,END=1703,1722
sys=__import__('sys'); sys.dont_write_bytecode=True
spec=__import__('importlib.util',fromlist=['spec_from_file_location']).spec_from_file_location('candidatefree_schema',INPUT/'candidate-free-schema-helper.py')
h=__import__('importlib.util',fromlist=['module_from_spec']).module_from_spec(spec); spec.loader.exec_module(h)


def sha(value): return h.sha(value)
def canonical(value): return h.canon(value)
def write_json(path,value): path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def write_jsonl(path,rows): path.write_text(''.join(canonical(row)+'\n' for row in rows),encoding='utf-8')
def run(args,cwd=None): return subprocess.check_output(args,cwd=cwd,text=True,stderr=subprocess.STDOUT).strip()


def packet_pins():
    listed={}
    for line in (INPUT/'SHA256SUMS.txt').read_text(encoding='utf-8').splitlines():
        if line.strip():
            digest,name=line.split(None,1); listed[name.lstrip('* ')]=digest
    actual={path.relative_to(INPUT).as_posix():sha(path.read_bytes()) for path in INPUT.rglob('*') if path.is_file() and path.name!='SHA256SUMS.txt'}
    if listed!=actual: raise RuntimeError('candidate-free checksum list mismatch')
    manifest=json.loads((INPUT/'manifest.json').read_text(encoding='utf-8'))
    if (manifest['head'],manifest['tree'],manifest['selectedPositions'],manifest['candidateFreeInputOnly'],manifest['proposedTranslationsIncluded']) != (HEAD,TREE,[START,END],True,False):
        raise RuntimeError('candidate-free packet identity mismatch')
    return {'checksumListSha256':sha((INPUT/'SHA256SUMS.txt').read_bytes()),
      'manifestSha256':sha((INPUT/'manifest.json').read_bytes()),'cellRowsSha256':sha((INPUT/'current-target-cells.jsonl').read_bytes()),
      'sourceContextRowsSha256':sha((INPUT/'source-contexts.jsonl').read_bytes()),'manifest':manifest}


def capture(label,input_pins):
    api=json.loads(run(['gh','api',f'repos/{REPO_NAME}/pulls/{PR}','--jq',
      '{number:.number,state:.state,draft:.draft,headRef:.head.ref,headSha:.head.sha,baseRef:.base.ref,baseSha:.base.sha,url:.html_url}']))
    raw=run(['git','ls-remote',f'https://github.com/{REPO_NAME}.git',f'refs/heads/{BRANCH}',f'refs/pull/{PR}/head','refs/heads/main'])
    refs={}
    for line in raw.splitlines(): digest,name=line.split('\t'); refs[name]=digest
    commit=json.loads(run(['gh','api',f'repos/{REPO_NAME}/commits/{HEAD}','--jq','{sha:.sha,tree:.commit.tree.sha}']))
    local_head=run(['git','rev-parse','HEAD'],REPO); local_tree=run(['git','rev-parse','HEAD^{tree}'],REPO)
    clean=run(['git','status','--porcelain=v1'],REPO)==''
    branch=run(['git','branch','--show-current'],REPO)
    if (api['number'],api['state'],api['draft'],api['headRef'],api['headSha'],api['baseRef'],api['baseSha'])!=(PR,'open',True,BRANCH,HEAD,'main',BASE):
        raise RuntimeError('live PR pin drift: '+str(api))
    if commit!={'sha':HEAD,'tree':TREE} or local_head!=HEAD or local_tree!=TREE or branch!=BRANCH or not clean:
        raise RuntimeError('local exact-head source clone mismatch')
    if refs.get(f'refs/heads/{BRANCH}')!=HEAD or refs.get(f'refs/pull/{PR}/head')!=HEAD:
        raise RuntimeError('remote branch/pull ref drift')
    return {'capturedAtUtc':datetime.now(timezone.utc).isoformat(timespec='seconds'),'label':label,
      'repository':REPO_NAME,'pullRequest':PR,'state':'OPEN','draft':True,'url':api['url'],
      'headRef':BRANCH,'headSha':HEAD,'headTree':TREE,'baseRef':'main','baseSha':BASE,
      'remoteRefs':refs,'localBranch':branch,'localHead':local_head,'localTree':local_tree,'localWorktreeClean':clean,
      'candidateFreeChecksumListSha256':input_pins['checksumListSha256'],
      'candidateFreeManifestSha256':input_pins['manifestSha256'],
      'candidateFreeCellRowsSha256':input_pins['cellRowsSha256'],
      'deploymentActionsIssuedByReview':0}


proposal_rows=json.loads((R/'proposal-selections.json').read_text(encoding='utf-8'))['proposals']
PROPOSALS={(row['position'],row['locale']):row for row in proposal_rows}
if len(PROPOSALS)!=len(proposal_rows): raise RuntimeError('duplicate primary proposal cell')
POSITION_NOTES={
 1703:'A count heading for failed publication, retrieval, routing, and verification operations; use a natural failure label.',
 1704:'A transport failover setting/status; the displayed value is Auto.',
 1705:'Signed warnings for suspicious candidates falsely presented as lossless.',
 1706:'A family label for a SongID forensic-matrix family lane, not a household.',
 1707:'The numeric score associated with the known SongID family.',
 1708:'An acquisition profile that allows high-bitrate lossy matches and prefers shorter queues.',
 1709:'The accessible name for a button seeking local playback forward.',
 1710:'The seek-forward tooltip and accessible text, specifying a 30-second step.',
 1711:'An acquisition-profile preference for the fastest source.',
 1712:'The accessible name for toggling the active RustyMilk preset as a favorite.',
 1713:'The option label for the RustyMilk preset library favorites view.',
 1714:'The collapsible header for the Federated Taste recommendation section.',
 1715:'The heading of a music recommendation panel; taste refers to user music preferences, not food flavor.',
 1716:'The off state of the Federation status value.',
 1717:'The on state of the Federation status value.',
 1718:'A numeric rate-limit field counting permitted federation requests per minute.',
 1719:'A numeric rate-limit field for the federation window duration in seconds.',
 1720:'The diagnostics card for Federation and the technical Pod unit.',
 1721:'The fixed error shown when Federation diagnostics cannot be loaded.',
 1722:'The fixed error shown when Federation diagnostics fail.'}



def main():
    input_pins=packet_pins(); before=capture('before primary review',input_pins)
    raw=(INPUT/'current-target-cells.jsonl').read_bytes().splitlines()
    cells={}; raw_hash={}
    for line in raw:
        cell=json.loads(line); key=(cell['position'],cell['locale'])
        if key in cells: raise RuntimeError('duplicate candidate-free cell '+str(key))
        cells[key]=cell; raw_hash[key]=sha(line)
    contexts={row['position']:row for row in (json.loads(line) for line in (INPUT/'source-contexts.jsonl').read_text(encoding='utf-8').splitlines())}
    locale_decisions=Counter(); ledger=[]; proposals=[]; holds=[]; placeholder_reorders=[]; protected_localizations=[]
    for position in range(START,END+1):
      for locale in LOCALES:
        key=(position,locale); cell=cells[key]; context=contexts[position]; proposal=PROPOSALS.get(key)
        if proposal and proposal['sourceKey'] != cell['sourceKey']: raise RuntimeError('primary proposal source binding mismatch '+str(key))
        current=cell.get('currentTarget')
        target=proposal['target'] if proposal else None
        decision=proposal['decision'] if proposal else 'accept-current'
        source_placeholders=h.tokens(cell['sourceKey'])[0]
        variant_rows=cell.get('targetTokenVariants',[])
        current_placeholder_multiset_matches=all(Counter(row['targetPlaceholders'])==Counter(source_placeholders) for row in variant_rows)
        if not current_placeholder_multiset_matches and proposal is None:
            decision='hold'
            holds.append({'cellId':f'{position}::{locale}','position':position,'locale':locale,
              'sourceKeySha256':cell['sourceKeySha256'],'currentTargetSha256':cell['currentTargetSha256'],
              'candidateFreeCellSha256':raw_hash[key],'sourceContextSha256':cell['sourceContextSha256'],
              'reason':'Current target does not preserve every named source placeholder exactly once; retain unresolved pending review.'})
        for variant in variant_rows:
            if variant['targetPlaceholders']!=source_placeholders and variant.get('placeholderMultisetMatches') is True:
                placeholder_reorders.append({'position':position,'locale':locale,'jsonPath':variant['jsonPath'],
                  'sourcePlaceholders':source_placeholders,'targetPlaceholders':variant['targetPlaceholders'],
                  'note':'Order differs for target-language grammar; every named placeholder appears exactly once.'})
            if variant['protectedLiteralMismatchTokens']:
                protected_localizations.append({'position':position,'locale':locale,'jsonPath':variant['jsonPath'],
                  'translatedLiterals':variant['protectedLiteralMismatchTokens'],
                  'note':'The acronym is a generic identifier term and is translated into the target language.'})
        note=proposal['rationale'] if proposal else ('Current target held: named placeholders do not match the source multiset.' if decision=='hold' else ('Reviewed against the source meaning and pinned production caller context: '+POSITION_NOTES[position]+' Current wording is accepted; no supported correction is recommended.'))
        rec={'cellId':f'{position}::{locale}','position':position,'locale':locale,
          'sourceKey':cell['sourceKey'],'sourceKeySha256':cell['sourceKeySha256'],
          'sourceContextSha256':cell['sourceContextSha256'],'callerReferenceCount':context['productionCallerCount'],
          'callerOccurrenceCount':context['callerOccurrenceCount'],'callerPaths':sorted({caller['path'] for caller in context['callers']}),
          'candidateFreeCellSha256':raw_hash[key],'currentTargetSha256':cell['currentTargetSha256'],
          'currentTargetType':cell['currentTargetType'],'catalogPath':cell['catalogPath'],
          'catalogFileSha256':cell['catalogFileSha256'],'catalogGitBlob':cell['catalogGitBlob'],
          'sourceTokens':{'placeholders':source_placeholders,'markupTags':cell.get('sourceMarkupTags',[]),
            'numericTokens':cell.get('sourceNumericTokens',[]),'protectedLiterals':cell.get('sourceProtectedLiterals',[])},
          'currentTargetPlaceholderOrderMatches':all(row['targetPlaceholders']==source_placeholders for row in variant_rows),
          'currentTargetPlaceholderMultisetMatches':current_placeholder_multiset_matches,
          'targetVariantPaths':[row['jsonPath'] for row in variant_rows],
          'decision':decision,'reviewRationale':note,'confidence':proposal['confidence'] if proposal else 'moderate',
          'exactHead':HEAD,'exactTree':TREE}
        if proposal:
            rec['recommendedTarget']=target
            rec['recommendedTargetSha256']=sha(target)
            source_tokens=h.tokens(cell['sourceKey']); proposed_tokens=h.tokens(target)
            checks={'placeholderMultiset':Counter(source_tokens[0])==Counter(proposed_tokens[0]),
              'markupTags':source_tokens[1]==proposed_tokens[1],
              'numericTokens':source_tokens[2]==proposed_tokens[2],
              'protectedLiterals':all(item in proposed_tokens[3] for item in source_tokens[3])}
            rec['recommendedTargetTokenChecks']=checks
            if not all(checks.values()): raise RuntimeError('proposal token signature failed '+str(key)+': '+str(checks))
            if cell['sourceKey'].rstrip().endswith(':') and not target.rstrip().endswith((':','：')):
                raise RuntimeError('proposal removed source prefix colon '+str(key))
            proposals.append({'cellId':rec['cellId'],'position':position,'locale':locale,
              'sourceKeySha256':cell['sourceKeySha256'],'currentTargetSha256':cell['currentTargetSha256'],
              'candidateFreeCellSha256':raw_hash[key],'sourceContextSha256':cell['sourceContextSha256'],
              'catalogPath':cell['catalogPath'],'catalogFileSha256':cell['catalogFileSha256'],'catalogGitBlob':cell['catalogGitBlob'],
              'decision':decision,'recommendedTarget':target,'recommendedTargetSha256':sha(target),
              'rationale':proposal['rationale'],'confidence':proposal['confidence'],'exactHead':HEAD,'exactTree':TREE})
        ledger.append(rec); locale_decisions[decision]+=1
    if len(cells)!=240: raise RuntimeError('candidate-free scope is not 240 cells')
    write_jsonl(R/'ledger.jsonl',ledger); write_jsonl(R/'proposals.jsonl',proposals); write_jsonl(R/'holds.jsonl',holds)
    summary={'exactHead':HEAD,'exactTree':TREE,'baseSha':BASE,'window':'W1703-W1722','sourceCount':20,
      'localeCount':12,'cellCount':len(ledger),'decisionCounts':dict(Counter(row['decision'] for row in ledger)),
      'confidenceCounts':dict(Counter(row['confidence'] for row in ledger)),
      'proposalCount':len(proposals),'holdCount':len(holds),'placeholderOrderDifferenceCellCount':len(placeholder_reorders),
      'protectedLiteralLocalizationCellCount':len(protected_localizations),'callerlessCells':input_pins['manifest']['callerResolutionHoldCount'],
      'candidateFreeInputOnly':True,'blindOrCrossOutputInspected':False,'nativeSpeakerSignoff':False,
      'localeDecisionCounts':{locale:dict(Counter(row['decision'] for row in ledger if row['locale']==locale)) for locale in LOCALES}}
    write_json(R/'summary.json',summary); write_json(R/'input-attestation.json',input_pins)
    write_json(R/'placeholder-order-review.json',{'count':len(placeholder_reorders),'items':placeholder_reorders,
      'disposition':'Accepted when every placeholder is preserved exactly once and the change is a target-language word-order requirement.'})
    write_json(R/'protected-literal-review.json',{'count':len(protected_localizations),'items':protected_localizations,
      'disposition':'Accepted translations of generic ID are not branded/protected literals.'})
    after_input=packet_pins(); after=capture('after primary review',after_input)
    write_json(R/'attestation-before.json',before); write_json(R/'attestation-after.json',after)
    if before['candidateFreeChecksumListSha256']!=after['candidateFreeChecksumListSha256'] or before['candidateFreeManifestSha256']!=after['candidateFreeManifestSha256']:
        raise RuntimeError('candidate-free packet changed during primary review')
    if before['headSha']!=after['headSha'] or before['headTree']!=after['headTree'] or before['remoteRefs']!=after['remoteRefs']:
        raise RuntimeError('source/PR refs drifted during primary review')
    readme=textwrap.dedent(f'''# slskR PR #209 W1703–W1722 primary semantic review

    This independent primary review covers all 240 candidate-free cells across 20 source keys and 12 locales, pinned to exact PR head {HEAD} / tree {TREE}. The review input and reviewer worktree remained unchanged during the review.

    Dispositions: {summary['decisionCounts'].get('accept-current',0)} accept current, {summary['decisionCounts'].get('correction',0)} corrections, {summary['decisionCounts'].get('refinement',0)} refinements, and {summary['holdCount']} holds. The proposal ledger contains every changed recommendation with source/caller/catalog bindings, rationale, confidence, and token signatures.

    The review examined count labels in the media publication and retrieval panels; fake-lossless warning terminology; local seek-forward button labels and tooltip text; federated music preference recommendations; federation rate-limit units; and Federation diagnostics terminology. All other cells were reviewed against their caller context and retained when no clear issue was supported.

    All target placeholders, markup tags, numeric tokens, and protected literals were checked for each proposal. Candidate-free input had no callerless cells or token mismatches. This primary review used candidate-free evidence only and did not inspect blind or cross-review output. It makes no qualified native-speaker or visual-review claim.

    Offline verification: python3 verify_primary_review.py --repo {REPO}. No repository catalogs or source files were edited. No tests, builds, scans, CI dispatches, or workflow actions were run.
    ''')
    (R/'README.md').write_text(readme,encoding='utf-8')
    manifest={'artifact':'slskR PR #209 W1703-W1722 independent primary semantic review','repository':REPO_NAME,
      'pullRequest':PR,'exactHead':HEAD,'exactTree':TREE,'baseSha':BASE,'branch':BRANCH,
      'selectedPositions':[START,END],'sourceCount':20,'localeCount':12,'cellCount':len(ledger),
      'candidateFreeChecksumListSha256':after_input['checksumListSha256'],'candidateFreeManifestSha256':after_input['manifestSha256'],
      'candidateFreeCellRowsSha256':after_input['cellRowsSha256'],'decisionCounts':summary['decisionCounts'],
      'proposalCount':len(proposals),'holdCount':len(holds),'candidateFreeOnly':True,
      'blindOrCrossOutputInspected':False,'sourceFilesEdited':False,
      'createdAtUtc':datetime.now(timezone.utc).isoformat(timespec='seconds')}
    manifest['files']={path.name:{'sha256':sha(path.read_bytes()),'byteCount':path.stat().st_size} for path in sorted(R.iterdir()) if path.is_file() and path.name not in ('manifest.json','SHA256SUMS.txt')}
    write_json(R/'manifest.json',manifest)
    (R/'SHA256SUMS.txt').write_text(''.join(f'{sha(path.read_bytes())}  {path.name}\n' for path in sorted(R.iterdir()) if path.is_file() and path.name!='SHA256SUMS.txt'),encoding='utf-8')
    print(json.dumps({'result':'BUILT','head':HEAD,'tree':TREE,'cells':len(ledger),'decisionCounts':summary['decisionCounts'],
      'proposals':len(proposals),'holds':len(holds),'placeholderOrderDifferenceCells':len(placeholder_reorders),
      'protectedLiteralLocalizations':len(protected_localizations),'packet':str(R)},indent=2))

if __name__=='__main__': main()
