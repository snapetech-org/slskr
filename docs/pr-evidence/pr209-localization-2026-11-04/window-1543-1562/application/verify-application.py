#!/usr/bin/env python3
"""Verify the PR #209 W1543-W1562 exact-hash application and evidence bundle."""
import collections
import hashlib
import json
import re
import subprocess
from pathlib import Path

R = Path(__file__).resolve().parent
REPO = R.parents[4]
HEAD = 'c15eddffec2c4c24cc091b2a6ebf0c43fa58ef1b'
TREE = '4259db991f25fbbd0200963769e62bb7e2150806'
PRODUCT = '9f158221682915a9c6c238c5e182871adbf93efd'
PRODUCT_TREE = '72c5fd0d9f69fe802e7a659e9c44d02fbc2f5eb8'
LOCALES = ['es','zh-Hans','hi','de','ja','fr','pt-BR','ar','ko','zh-Hant','vi','id']

def sha(value):
    if isinstance(value, str):
        value = value.encode('utf-8')
    return hashlib.sha256(value).hexdigest()

def j(path):
    return json.loads(path.read_text(encoding='utf-8'))

def jl(path):
    return [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines() if line]

def git(*args):
    return subprocess.check_output(['git','-C',str(REPO),*args],text=True).strip()

def git_bytes(ref, path):
    return subprocess.check_output(['git','-C',str(REPO),'show',f'{ref}:{path}'])

def tokens(text):
    placeholders=re.findall(r'\{[A-Za-z][A-Za-z0-9_]*\}',text)
    markup=re.findall(r'</?[A-Za-z][^>]*>',text)
    numbers=re.findall(r'(?<![A-Za-z])\d+(?:[.,]\d+)?%?(?![A-Za-z])',text)
    protected=[]
    pattern=r'(?<![A-Za-z0-9])(?:[A-Z]{2,}[A-Z0-9]*|ffmpeg|Chromaprint|Soulseek|Spotify|YouTube|Pushbullet|Matrix|WebSocket|OpenAI)(?![A-Za-z0-9])'
    for value in re.findall(pattern,text):
        if value not in protected: protected.append(value)
    return {'placeholders':placeholders,'markup':markup,'numbers':numbers,'protectedLiterals':protected}

def patch_value(raw, key, expected_current, selected):
    text=raw.decode('utf-8')
    key_token=json.dumps(key,ensure_ascii=False)
    pattern=re.compile(r'(?m)^(?P<indent>[ \t]*)'+re.escape(key_token)+r'(?P<after>[ \t]*:[ \t]*)')
    matches=list(pattern.finditer(text))
    assert len(matches)==1,(key,len(matches))
    start=matches[0].end()
    current,end=json.JSONDecoder().raw_decode(text,start)
    assert current==expected_current,(key,current,expected_current)
    return (text[:start]+json.dumps(selected,ensure_ascii=False)+text[end:]).encode('utf-8')

def verify_packet(directory):
    sums={}
    for line in (directory/'SHA256SUMS.txt').read_text(encoding='utf-8').splitlines():
        digest,name=line.split(None,1); name=name.lstrip('* ')
        assert name not in sums
        sums[name]=digest
    actual={p.relative_to(directory).as_posix() for p in directory.rglob('*') if p.is_file() and p.relative_to(directory).as_posix()!='SHA256SUMS.txt'}
    assert set(sums)==actual,(directory,set(sums)^actual)
    for name,digest in sums.items(): assert sha((directory/name).read_bytes())==digest,(directory,name)
    return sums

# Verify the entire evidence tree and all four nested sealed packet checksum sets.
outer_sums=verify_packet(R)
app_manifest=j(R/'application-manifest.json')
assert app_manifest['inputHead']==HEAD and app_manifest['inputTree']==TREE
assert app_manifest['productCommit']==PRODUCT and app_manifest['productTree']==PRODUCT_TREE
actual_manifest_files={p.relative_to(R).as_posix() for p in R.rglob('*') if p.is_file() and p.name not in {'SHA256SUMS.txt','application-manifest.json'}}
assert set(app_manifest['fileHashes'])==actual_manifest_files
for name,pin in app_manifest['fileHashes'].items():
    raw=(R/name).read_bytes()
    assert sha(raw)==pin['sha256'] and len(raw)==pin['byteCount'],name
cross=R/'cross-review'
review_inputs=R/'review-inputs'
cross_sums=verify_packet(cross)
input_sums={
 'candidateFree':verify_packet(review_inputs/'candidate-free-input'),
 'primary':verify_packet(review_inputs/'primary-review'),
 'independentBlind':verify_packet(review_inputs/'independent-blind-review'),
}
manifest=j(cross/'manifest.json')
assert manifest['exactPin']['head']==HEAD and manifest['exactPin']['tree']==TREE
assert manifest['review']['crossDispositionCounts']=={'accept-current':208,'propose-correction':27,'hold':5}
assert manifest['inputs']['candidateFreeChecksumListSha256']==sha((review_inputs/'candidate-free-input/SHA256SUMS.txt').read_bytes())
assert manifest['inputs']['primaryChecksumListSha256']==sha((review_inputs/'primary-review/SHA256SUMS.txt').read_bytes())
assert manifest['inputs']['blindChecksumListSha256']==sha((review_inputs/'independent-blind-review/SHA256SUMS.txt').read_bytes())
for name,pin in manifest['fileHashes'].items():
    assert sha((cross/name).read_bytes())==pin['sha256'],name

plan=j(R/'exact-hash-apply-plan.json')
report=j(R/'apply-readback-report.json')
postpins=j(R/'postimage-catalog-pins.json')
ledger=jl(cross/'cross-review-ledger.jsonl')
readback=jl(R/'apply-readback-cells.jsonl')
assert plan['inputHead']==HEAD and plan['inputTree']==TREE
assert plan['productCommit']==PRODUCT and plan['productTree']==PRODUCT_TREE
assert plan['productCommitParent']==HEAD
assert git('rev-parse',PRODUCT+'^')==HEAD and git('rev-parse',PRODUCT+'^{tree}')==PRODUCT_TREE
paths=git('diff-tree','--no-commit-id','--name-only','-r',PRODUCT).splitlines()
assert set(paths)==set(plan['productCommitPaths'])==set(report['productCommitPaths'])
assert len(paths)==11 and all(p.startswith('web/src/lib/locales/ui-labels.') for p in paths)
assert git('diff-tree','--numstat','--no-commit-id','-r',PRODUCT).splitlines()
numstat=git('diff-tree','--numstat','--no-commit-id','-r',PRODUCT).splitlines()
assert sum(int(line.split('\t')[0]) for line in numstat)==27
assert sum(int(line.split('\t')[1]) for line in numstat)==27

plan_changes={(x['position'],x['locale']):x for x in plan['selectedChanges']}
plan_accept={(x['position'],x['locale']):x for x in plan['acceptedHashOnly']}
plan_holds={(x['position'],x['locale']):x for x in plan['holdHashOnly']}
assert (len(ledger),len(readback),len(plan_changes),len(plan_accept),len(plan_holds))==(240,240,27,208,5)
assert [(x['position'],x['locale']) for x in readback]==[(x['position'],x['locale']) for x in ledger]
prepins=plan['preApplyCatalogPins']
assert set(prepins)==set(postpins) and len(prepins)==12
base_data={}; product_data={}; base_raw={}; product_raw={}
for path in sorted(prepins):
    before=git_bytes(HEAD,path); after=git_bytes(PRODUCT,path)
    base_raw[path]=before; product_raw[path]=after
    bp=prepins[path]; pp=postpins[path]
    assert sha(before)==bp['sha256'] and len(before)==bp['byteCount']
    assert sha(after)==pp['sha256'] and len(after)==pp['byteCount']
    assert git('rev-parse',f'{HEAD}:{path}')==bp['gitBlob']
    assert git('rev-parse',f'{PRODUCT}:{path}')==pp['gitBlob']
    b=json.loads(before.decode('utf-8')); a=json.loads(after.decode('utf-8'))
    base_data[path]=b; product_data[path]=a
    assert list(b.keys())==list(a.keys())
    assert len(b)==len(a)==bp['keyCount']==pp['keyCount']==5441
    order_hash=sha('\n'.join(b.keys())+'\n')
    assert order_hash==bp['orderedKeySha256']==pp['orderedKeySha256']
    assert pp['keyOrderUnchanged'] is True

# Derive the exact postimage byte streams by changing only the 27 guarded JSON value tokens.
expected_raw=dict(base_raw)
changed_pairs=set()
for row in ledger:
    key=(row['position'],row['locale']); path=f"web/src/lib/locales/ui-labels.{row['locale']}.json"
    source_key=row['sourceKey']; before=base_data[path][source_key]
    assert sha(before)==row['currentTargetSha256'] and before==row['currentTarget']
    if row['crossDisposition']=='propose-correction':
        change=plan_changes[key]
        assert change['sourceKey']==source_key and change['currentTargetSha256']==sha(before)
        assert change['selectedTarget']==row['selectedTarget'] and change['selectedTargetSha256']==sha(row['selectedTarget'])
        source_tokens=tokens(source_key); selected_tokens=tokens(change['selectedTarget'])
        assert source_tokens['placeholders']==selected_tokens['placeholders']
        assert source_tokens['markup']==selected_tokens['markup']
        assert source_tokens['numbers']==selected_tokens['numbers']
        assert all(t in selected_tokens['protectedLiterals'] for t in source_tokens['protectedLiterals'])
        expected_raw[path]=patch_value(expected_raw[path],source_key,before,change['selectedTarget'])
        changed_pairs.add((path,source_key))
        expected_after=change['selectedTarget']; decision='apply-correction'
    elif row['crossDisposition']=='accept-current':
        assert key in plan_accept and row['selectedTarget']==before and row['selectedTargetSha256']==sha(before)
        expected_after=before; decision='retain-accepted'
    else:
        assert row['crossDisposition']=='hold' and key in plan_holds and row['selectedTarget'] is None
        assert plan_holds[key]['currentTargetSha256']==sha(before)
        expected_after=before; decision='retain-hold'
    rb=readback[(row['position']-1543)*12 + ['es','zh-Hans','hi','de','ja','fr','pt-BR','ar','ko','zh-Hant','vi','id'].index(row['locale'])]
    assert rb['decision']==decision and rb['crossDisposition']==row['crossDisposition']
    assert rb['observedAfterTarget']==expected_after and rb['observedAfterTargetSha256']==sha(expected_after)
    assert rb['expectedAfterTargetSha256']==sha(expected_after) and rb['readbackMatches'] is True
assert len(changed_pairs)==27
for path in prepins:
    assert expected_raw[path]==product_raw[path],path
    selected_for_path={x['sourceKey'] for x in plan['selectedChanges'] if x['catalogPath']==path}
    for source_key in base_data[path]:
        if source_key not in selected_for_path:
            assert product_data[path][source_key]==base_data[path][source_key],(path,source_key)
        else:
            expected=next(x['selectedTarget'] for x in plan['selectedChanges'] if x['catalogPath']==path and x['sourceKey']==source_key)
            assert product_data[path][source_key]==expected,(path,source_key)

counts=collections.Counter(x['crossDisposition'] for x in ledger)
assert counts=={'accept-current':208,'propose-correction':27,'hold':5}
assert report['outcomeCounts']=={'apply-correction':27,'retain-accepted':208,'retain-hold':5}
assert report['allBaseCatalogFilesMatchedPins'] and report['allCurrentTargetGuardsMatched']
assert report['allFinalTargetsReadBack'] and report['allCatalogKeySetsUnchanged'] and report['allCatalogKeyOrdersUnchanged']
assert report['allAcceptedTargetHashesPreserved'] and report['allHoldCurrentHashesPreserved']
assert sha((R/'apply-readback-cells.jsonl').read_bytes())==report['readbackCellsSha256']
assert sha((R/'exact-hash-apply-plan.json').read_bytes())==report['applyPlanSha256']
assert sha((R/'postimage-catalog-pins.json').read_bytes())==report['postimageCatalogPinsSha256']
assert sha((cross/'SHA256SUMS.txt').read_bytes())==report['crossReviewChecksumListSha256']

# Verify exact API body-prefix evidence and the recorded summary append.
before_body=(R/'pr-before-body.txt').read_text(encoding='utf-8')
after_body=(R/'pr-after-body.txt').read_text(encoding='utf-8')
summary=(R/'pr-body-summary.md').read_text(encoding='utf-8').rstrip('\n')
att=j(R/'pr-body-update-attestation.json')
assert after_body.startswith(before_body)
separator='' if before_body.endswith('\n\n') or before_body.endswith('\r\n\r\n') else ('\r\n' if before_body.endswith('\r\n') else ('\n' if before_body.endswith('\n') else '\n\n'))
assert after_body==before_body+separator+summary+'\n'
assert sha(before_body)==att['bodyBeforeSha256'] and sha(after_body)==att['bodyAfterSha256']
assert att['exactPrefixPreserved'] and att['apiReadbackMatches'] and att['headBefore']==att['headAfter']==PRODUCT
assert j(R/'pr-before.json')['body']==before_body
assert j(R/'pr-after.json')['body']==after_body
assert report['prBodyPrefixPreserved'] and report['prBodyApiReadbackMatches']

assert report['productCommit']==PRODUCT and report['productTree']==PRODUCT_TREE and report['productCommitParent']==HEAD
assert len(report['catalogFileReports'])==12
for path, rec in report['catalogFileReports'].items():
    assert rec['baseSha256']==prepins[path]['sha256'] and rec['finalSha256']==postpins[path]['sha256']
    assert rec['baseKeyCount']==rec['finalKeyCount']==5441 and rec['keyOrderUnchanged'] and rec['keySetUnchanged']
assert manifest['review']['nativeSpeakerSignoff'] is False
assert report['nativeSpeakerSignoff'] is False and report['browserReviewPerformed'] is False
assert report['testsBuildsScansOrCiRun'] is False and report['workflowsModified'] is False

print(json.dumps({
 'result':'PASS','inputHead':HEAD,'productCommit':PRODUCT,'productTree':PRODUCT_TREE,
 'reviewedCells':len(readback),'outcomeCounts':report['outcomeCounts'],
 'catalogFilesChanged':len(paths),'catalogFilesPinned':len(prepins),
 'catalogKeyCountsAndOrder':'PASS','exactOnlyValuePatches':'PASS','readback':'PASS',
 'prBodyPrefixPreserved':True,'nestedReviewPacketsChecksummed':4,
 'checksummedEvidenceFiles':len(outer_sums),
},ensure_ascii=False,indent=2))
