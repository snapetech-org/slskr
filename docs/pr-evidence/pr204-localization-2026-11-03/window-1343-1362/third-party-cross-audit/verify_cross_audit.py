#!/usr/bin/env python3
import hashlib,json,re,subprocess
from pathlib import Path
OUT=Path(__file__).resolve().parent
TASK=OUT.parent/'slskr-pr204-w1343-1362-primary-20261103'
I=TASK/'input'; P=TASK/'primary-review'; B=TASK/'blind-review'; REPO=TASK/'repo'
HEAD='130462c56f75d3c8fc2a90663a48c0474ad1208b'; TREE='47aba96d79eb57d6024fb358ee59cde931f0de3b'
def sha(b): return hashlib.sha256(b).hexdigest()
def st(s): return sha(s.encode('utf-8'))
def j(p): return json.loads(p.read_text(encoding='utf-8'))
def jl(p): return [json.loads(x) for x in p.read_text(encoding='utf-8').splitlines() if x.strip()]
def check_sums(d):
    r=subprocess.run(['sha256sum','-c','SHA256SUMS.txt'],cwd=d,text=True,capture_output=True)
    assert r.returncode==0,(d,r.stdout,r.stderr)
    return r.stdout.strip().splitlines()
for d in (I,P,B): check_sums(d)
for cwd,script in ((I,'verify-candidate-free.py'),(P,'verify-primary-review.py'),(B,'verify_blind_review.py')):
    subprocess.run(['python3',str(cwd/script)],cwd=cwd,check=True,capture_output=True,text=True)
summary=j(OUT/'summary.json')
assert summary['head']==HEAD and summary['tree']==TREE
assert sha((I/'manifest.json').read_bytes())==summary['pins']['candidateFreeManifestSha256']
assert sha((I/'SHA256SUMS.txt').read_bytes())==summary['pins']['candidateFreeChecksumListSha256']
assert sha((P/'manifest.json').read_bytes())==summary['pins']['primaryManifestSha256']
assert sha((P/'SHA256SUMS.txt').read_bytes())==summary['pins']['primaryChecksumListSha256']
assert sha((B/'SHA256SUMS.txt').read_bytes())==summary['pins']['blindChecksumListSha256']
assert sha((B/'provenance.json').read_bytes())==summary['pins']['blindProvenanceSha256']
inputs={(x['position'],x['locale']):x for x in jl(I/'current-target-cells.jsonl')}
primary={(x['position'],x['locale']):x for x in jl(P/'primary-review-ledger.jsonl')}
blind={(x['position'],x['locale']):x for x in jl(B/'blind-ledger.jsonl')}
rows={(x['position'],x['locale']):x for x in jl(OUT/'resolution-ledger.jsonl')}
assert len(inputs)==len(primary)==len(blind)==len(rows)==240
assert inputs.keys()==primary.keys()==blind.keys()==rows.keys()
target_diffs=disposition_diffs=adjudicated=0
ph=re.compile(r'{[A-Za-z][A-Za-z0-9_]*}'); tags=re.compile(r'</?[A-Za-z][^>]*>'); nums=re.compile(r'(?<![A-Za-z])[0-9]+(?:[.,][0-9]+)?%?(?![A-Za-z])')
prot=re.compile(r'(?<![A-Za-z0-9])(?:[A-Z]{2,}[A-Z0-9]*|ffmpeg|Chromaprint|Soulseek|Spotify|YouTube|Pushbullet|Matrix|WebSocket|OpenAI)(?![A-Za-z0-9])')
for key,row in rows.items():
    c=inputs[key]; p=primary[key]; b=blind[key]
    assert row['sourceKey']==c['sourceKey'] and row['sourceKeySha256']==c['sourceKeySha256']
    assert row['currentTarget']==c['currentTarget'] and row['currentTargetSha256']==c['currentTargetSha256']
    assert row['primaryTarget']==p['target'] and row['primaryTargetSha256']==p['targetSha256'] and row['primaryDisposition']==p['disposition']
    assert row['blindTarget']==b['finalTarget'] and row['blindTargetSha256']==b['finalTargetSha256'] and row['blindDisposition']==b['disposition']
    td=p['target']!=b['finalTarget']; dd=p['disposition']!=b['disposition']
    assert row['targetDisagreement']==td and row['dispositionDisagreement']==dd
    target_diffs+=td; disposition_diffs+=dd
    if td or dd:
        adjudicated+=1
        assert row['decisionSource'] in {'primary-review','blind-review','current-target'}
        assert row['adjudicationRationale'].strip()
    else:
        assert row['decisionSource']=='primary+blind-consensus'
        assert row['adjudicatedTarget']==p['target'] and row['adjudicatedDisposition']==p['disposition']
    target=row['adjudicatedTarget']; source=row['sourceKey']; checks=row['tokenChecks']
    expected_ph=ph.findall(source); expected_tags=tags.findall(source); expected_nums=nums.findall(source)
    source_protected=[]
    for match in prot.finditer(source):
        if match.group(0) not in source_protected: source_protected.append(match.group(0))
    target_protected=[]
    for match in prot.finditer(target):
        if match.group(0) not in target_protected: target_protected.append(match.group(0))
    assert row['adjudicatedTargetSha256']==st(target)
    assert checks['sourcePlaceholders']==checks['targetPlaceholders']==expected_ph==ph.findall(target)
    assert checks['placeholderSequenceMatches'] is True
    assert checks['sourceMarkupTags']==checks['targetMarkupTags']==expected_tags==tags.findall(target)
    assert checks['markupMatches'] is True
    assert checks['sourceNumericTokens']==checks['targetNumericTokens']==expected_nums==nums.findall(target)
    assert checks['numericTokensMatch'] is True
    assert checks['sourceProtectedLiterals']==source_protected and checks['targetProtectedLiterals']==target_protected
    assert checks['missingProtectedLiterals']==[] and checks['protectedLiteralsMatch'] is True
    if row['adjudicatedDisposition'] in {'accept-current','hold'}: assert target==row['currentTarget']
    else: assert target!=row['currentTarget']
assert (target_diffs,disposition_diffs,adjudicated)==(57,27,57)
assert summary['comparison']['remainingTargetDisagreements']==summary['comparison']['remainingDispositionDisagreements']==0
prior=(I/'prior-hold-reattestation.jsonl').read_bytes(); copied=(OUT/'preserved-prior-holds.jsonl').read_bytes()
assert prior==copied and len([x for x in prior.splitlines() if x.strip()])==23
listed={line.split(None,1)[1].strip().lstrip('*') for line in (OUT/'SHA256SUMS.txt').read_text().splitlines() if line.strip()}
assert listed=={x.name for x in OUT.iterdir() if x.is_file() and x.name!='SHA256SUMS.txt'}
for line in (OUT/'SHA256SUMS.txt').read_text().splitlines():
    digest,name=line.split(None,1); name=name.strip().lstrip('*')
    assert sha((OUT/name).read_bytes())==digest,(name,'checksum')
assert subprocess.check_output(['git','-C',str(REPO),'rev-parse','HEAD'],text=True).strip()==HEAD
assert subprocess.check_output(['git','-C',str(REPO),'status','--short'],text=True).strip()==''
print(json.dumps({'result':'PASS','head':HEAD,'tree':TREE,'cells':len(rows),'agreedTargetAndDisposition':183,'targetDisagreementsAdjudicated':target_diffs,'dispositionDisagreementsAdjudicated':disposition_diffs,'remainingDisagreements':0,'priorHoldsPreserved':23,'candidateFreeManifestSha256':summary['pins']['candidateFreeManifestSha256'],'candidateFreeChecksumListSha256':summary['pins']['candidateFreeChecksumListSha256'],'outputChecksumListSha256':sha((OUT/'SHA256SUMS.txt').read_bytes()),'repoClean':True},ensure_ascii=False,indent=2))
