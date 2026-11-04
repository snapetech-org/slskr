#!/usr/bin/env python3
import argparse,hashlib,json,subprocess
from pathlib import Path
R=Path(__file__).resolve().parents[1]; A=R/'application'; IN=R/'candidate-free-input'; X=R/'cross-audit'
def sha(b):return hashlib.sha256(b).hexdigest()
def hs(s):return sha(s.encode())
def j(p):return json.loads(p.read_text(encoding='utf-8'))
def jl(p):return [json.loads(s) for s in p.read_text(encoding='utf-8').splitlines() if s]
def verify_repo(repo):
 git=lambda *a:subprocess.check_output(['git',*a],cwd=repo,text=True).strip()
 c=j(A/'commit-record.json');att=j(A/'catalog-commit-attestation.json');pins=j(IN/'catalog-file-pins.json')['localeCatalogs']
 commit=c['catalogCommitSha'];parent=c['catalogCommitParent']
 assert git('rev-parse',f'{commit}^')==parent
 assert git('rev-parse',f'{commit}^{{tree}}')==c['catalogCommitTree']
 assert set(git('diff-tree','--no-commit-id','--name-only','-r',commit).splitlines())==set(c['changedPaths'])
 for f in att['fileReadbackPins']:
  p=f['path'];assert git('rev-parse',f'{parent}:{p}')==f['preimageGitBlob']==pins[f['locale']]['gitBlob']
  blob=git('rev-parse',f'{commit}:{p}');assert blob==f['commitGitBlob']==git('hash-object',p)
  data=json.loads(subprocess.check_output(['git','show',f'{commit}:{p}'],cwd=repo,text=True))
  for x in jl(A/'application-plan.jsonl'):
   if x['catalogPath']==p:assert hs(data[x['sourceKey']])==x['targetSha256']
 assert not git('status','--porcelain')
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--repo');args=ap.parse_args()
 am=j(A/'manifest.json')
 sums={}
 for line in (A/'SHA256SUMS.txt').read_text().splitlines():
  d,n=line.split(None,1);n=n.lstrip('* ');assert n not in sums;sums[n]=d
 actual={p.name for p in A.iterdir() if p.is_file() and p.name!='SHA256SUMS.txt'}
 assert set(sums)==actual and set(am['files'])==actual-{'manifest.json'}
 for n,d in sums.items():assert sha((A/n).read_bytes())==d,n
 for n,x in am['files'].items():
  z=(A/n).read_bytes();assert len(z)==x['byteCount'] and sha(z)==x['sha256'],n
 c=j(A/'commit-record.json');att=j(A/'catalog-commit-attestation.json');post=j(A/'post-catalog-commit-readback.json')
 plan=jl(A/'application-plan.jsonl');read=jl(A/'readback.jsonl');files=j(A/'catalog-file-readback.json')
 cross=jl(X/'cross-ledger.jsonl');cfm=j(IN/'manifest.json')
 assert c['catalogCommitSha']=='15a3cfffc8f800f2420847e7a98e1f2e94b33819'
 assert c['catalogCommitTree']=='bad4a26bcbd81f9dccf3f779acaf05d2c1866313'
 assert c['catalogCommitParent']==cfm['head'] and c['evidenceCommitParent']==c['catalogCommitSha']
 assert len(plan)==len(read)==15 and len(files)==8
 assert c['updatedCellCount']==att['updatedCellCount']==post['cellReadbackCount']==15
 assert c['updatedCatalogFileCount']==att['updatedCatalogFileCount']==len(files)==8
 assert set(c['changedPaths'])==set(att['changedPaths'])=={x['catalogPath'] for x in files}
 xmap={(x['position'],x['locale']):x for x in cross}
 rmap={(z['position'],z['locale']):z for z in read}
 for p in plan:
  r=rmap[(p['position'],p['locale'])]
  x=xmap[(p['position'],p['locale'])]
  assert x['crossDisposition']==p['crossDisposition'] and x['crossTargetSha256']==p['targetSha256']
  assert x['currentTargetSha256']==p['currentTargetPreimageSha256']
  assert p['targetSha256']==hs(p['target']) and p['sourceKeySha256']==x['sourceKeySha256']
  assert p['catalogFilePreimageSha256']==next(z['preimageSha256'] for z in att['fileReadbackPins'] if z['path']==p['catalogPath'])
  assert r['position']==p['position'] and r['locale']==p['locale']
  assert r['preimageTargetSha256']==p['currentTargetPreimageSha256']
  assert r['targetSha256']==r['readbackTargetSha256']==p['targetSha256'] and r['readbackMatches']
 for f in att['fileReadbackPins']:
  assert f['preimageBlobMatched'] and f['commitBlobMatchedDisk']
  assert f['preimageSha256']==next(x['sha256'] for x in j(IN/'catalog-file-pins.json')['localeCatalogs'].values() if x['path']==f['path'])
  assert f['readbackSha256']==next(x['readbackFileSha256'] for x in files if x['catalogPath']==f['path'])
 assert att['allPreimageFileHashesMatched'] if 'allPreimageFileHashesMatched' in att else att['allFilePreimageHashesMatched']
 assert att['allCellTargetPreimagesMatched'] and att['allCellReadbackHashesMatched'] and att['onlyPlannedCatalogKeysChanged']
 assert post['allTargetsMatchLiveCatalog'] and post['allFilesMatchCommitTree'] and post['worktreeClean']
 assert post['allPreimageGitBlobsMatched'] and post['allCommitBlobsMatchDisk']
 if args.repo:verify_repo(Path(args.repo))
 print(json.dumps({'result':'PASS','catalogCommit':c['catalogCommitSha'],'catalogTree':c['catalogCommitTree'],
  'parent':c['catalogCommitParent'],'updatedCells':len(plan),'updatedCatalogFiles':len(files),
  'exactPreimagesAndReadbacks':'PASS','gitBlobAttestation':'PASS','repoVerification':'PASS' if args.repo else 'not requested'},indent=2))
if __name__=='__main__':main()

