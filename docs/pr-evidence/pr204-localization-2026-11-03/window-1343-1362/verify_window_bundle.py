#!/usr/bin/env python3
import hashlib,json,subprocess,sys
from pathlib import Path
here=Path(__file__).resolve().parent
repo=Path(__file__).resolve().parents[4]
def sha(x): return hashlib.sha256(x if isinstance(x,bytes) else x.encode('utf-8')).hexdigest()
listed=set()
for line in (here/'SHA256SUMS.txt').read_text(encoding='utf-8').splitlines():
    if not line.strip(): continue
    digest,name=line.split(None,1); name=name.strip().lstrip('*'); listed.add(name)
    path=here/name
    if not path.is_file() or sha(path.read_bytes())!=digest: raise SystemExit('window checksum mismatch: '+name)
actual={p.relative_to(here).as_posix() for p in here.rglob('*') if p.is_file() and p!=here/'SHA256SUMS.txt'}
if listed!=actual: raise SystemExit('window checksum inventory mismatch')
result=subprocess.run(['python3',str(here/'application/verify_application.py')],cwd=repo,text=True,capture_output=True)
if result.returncode: raise SystemExit(result.stdout+result.stderr)
summary=json.loads((here/'third-party-cross-audit/summary.json').read_text(encoding='utf-8'))
if summary['head']!='130462c56f75d3c8fc2a90663a48c0474ad1208b' or summary['tree']!='47aba96d79eb57d6024fb358ee59cde931f0de3b': raise SystemExit('review packet pin mismatch')
print(json.dumps({'result':'PASS','window':'W1343-W1362','crossAuditCells':summary['window']['cellCount'],'targetDisagreementsAdjudicated':summary['comparison']['targetDisagreementCount'],'dispositionDisagreementsAdjudicated':summary['comparison']['dispositionDisagreementCount'],'unresolvedDisagreements':summary['comparison']['remainingTargetDisagreements']+summary['comparison']['remainingDispositionDisagreements'],'application':json.loads(result.stdout)},ensure_ascii=False,indent=2))
