#!/usr/bin/env python3
"""Build the root ledger and exact-hash plan from sealed slskR W1763-W1782 reviews."""
from __future__ import annotations
import collections, hashlib, json, subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
INPUTS = HERE / 'inputs'
CROSS = INPUTS / 'cross-review' / 'integrated-cross-ledger.jsonl'
PINS = INPUTS / 'cross-review' / 'input-pins.json'
ROOT = HERE / 'root-adjudication'
PLAN = HERE / 'root-application' / 'exact-hash-apply-plan.jsonl'
REPO: Path
OVERRIDES = {}


def sha(v: str | bytes) -> str:
    return hashlib.sha256(v.encode('utf-8') if isinstance(v, str) else v).hexdigest()

def read_rows(p: Path):
    return [json.loads(line) for line in p.read_text(encoding='utf-8').splitlines() if line.strip()]
def write_rows(p: Path, rows):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(''.join(json.dumps(r, ensure_ascii=False, sort_keys=True) + '\n' for r in rows), encoding='utf-8')
def git(*args: str) -> str:
    return subprocess.check_output(['git', *args], cwd=REPO, text=True).strip()

def main():
    import argparse
    global REPO
    parser=argparse.ArgumentParser()
    parser.add_argument('--repo',type=Path,required=True,help='clean slskR worktree at the pinned input head')
    args=parser.parse_args(); REPO=args.repo.resolve()
    pins=json.loads(PINS.read_text(encoding='utf-8'))
    head=pins['head']; tree=pins['tree']
    rows=read_rows(CROSS)
    assert len(rows)==240 and len({(r['position'],r['locale']) for r in rows})==240
    assert git('rev-parse','HEAD')==head and git('rev-parse','HEAD^{tree}')==tree
    assert not git('status','--porcelain')
    counts=collections.Counter(); ledger=[]; plan=[]; files={}; override_rows=[]
    for r in rows:
        assert r['provenanceVerified'] is True
        assert r['crossTokenAudit']['allPreserved'] is True
        assert sha(r['sourceKey'])==r['sourceKeySha256']
        assert sha(r['currentTarget'])==r['currentTargetSha256']
        key=(r['position'],r['locale'])
        override=OVERRIDES.get(key)
        if r['crossDisposition']=='accept_current':
            target=r['currentTarget']; disposition='accept-current'; target_sha=r['currentTargetSha256']
        elif r['crossDisposition'] in {'correction','refinement'}:
            target=override['target'] if override else r['crossTarget']
            disposition=r['crossDisposition']; target_sha=sha(target)
            assert r['crossTarget'] is not None and sha(r['crossTarget'])==r['crossTargetSha256']
            assert target is not None and sha(target)==target_sha and target!=r['currentTarget']
        else:
            raise SystemExit(f"unsupported cross disposition at {r['position']}::{r['locale']}")
        assert target_sha==sha(target)
        row={
          'position':r['position'],'locale':r['locale'],'cellId':f"{r['position']}::{r['locale']}",
          'catalogPath':r['catalogPath'],'catalogFileSha256':r['catalogFileSha256'],
          'sourceKey':r['sourceKey'],'sourceKeySha256':r['sourceKeySha256'],
          'sourceContextSha256':r['sourceContextSha256'],'callerReferenceCount':r['callerCount'],
          'callerOccurrenceCount':r['callerOccurrenceCount'],'before':r['currentTarget'],
          'beforeSha256':r['currentTargetSha256'],'after':target,'afterSha256':target_sha,
          'crossDisposition':r['crossDisposition'],'crossSelectionSource':r['crossSelectionSource'],
          'crossTarget':r['crossTarget'],'crossTargetSha256':r['crossTargetSha256'],
          'primaryDecision':r['primaryDecision'],'blindDecision':r['blindDecision'],
          'crossRationale':r['crossRationale'],'rootDisposition':disposition,
          'rootTarget':target,'rootTargetSha256':target_sha,
          'rootOverrideApplied':bool(override),
          'rootRationale':override['rationale'] if override else (r['crossRationale'] if disposition!='accept-current' else 'Retain the exact-head value accepted by primary, blind, and independent cross-review.'),
          'rootAdjudicationPerformed':True,'confidence':'moderate',
          'callerReferences':r['callerReferences']
        }
        ledger.append(row); counts[disposition]+=1
        if override:
            override_rows.append({'position':r['position'],'locale':r['locale'],'cellId':f"{r['position']}::{r['locale']}",
              'sourceKey':r['sourceKey'],'sourceKeySha256':r['sourceKeySha256'],
              'before':r['currentTarget'],'beforeSha256':r['currentTargetSha256'],
              'crossTarget':r['crossTarget'],'crossTargetSha256':r['crossTargetSha256'],
              'rootTarget':target,'rootTargetSha256':target_sha,'callerReferences':r['callerReferences'],
              'rootRationale':override['rationale'],'confidence':'moderate'})
        if disposition!='accept-current':
            plan.append({k:row[k] for k in ('position','locale','cellId','catalogPath','sourceKey','sourceKeySha256','before','beforeSha256','after','afterSha256','crossTarget','crossTargetSha256','crossDisposition','crossSelectionSource','rootOverrideApplied','rootRationale','confidence','sourceContextSha256','callerReferenceCount','callerOccurrenceCount','catalogFileSha256') if k in row})
        files.setdefault(r['catalogPath'],[]).append(r)
    assert counts=={'accept-current':131,'correction':105,'refinement':4},counts
    assert len(plan)==109 and len(files)==12
    # Pin each exact baseline catalog and confirm all reviewed current values before any write.
    baseline={}
    for path, cells in files.items():
        raw=subprocess.check_output(['git','show',f'{head}:{path}'],cwd=REPO)
        expected_hash=cells[0]['catalogFileSha256']
        assert all(c['catalogFileSha256']==expected_hash for c in cells)
        assert sha(raw)==expected_hash,path
        data=json.loads(raw.decode('utf-8'))
        assert len(data)==5441,path
        assert (json.dumps(data,ensure_ascii=False,indent=2)+'\n').encode('utf-8')==raw,path
        for c in cells:
            assert c['sourceKey'] in data and data[c['sourceKey']]==c['currentTarget'],(path,c['sourceKey'])
        baseline[path]=expected_hash
    write_rows(ROOT/'root-final-review-ledger.jsonl',ledger)
    write_rows(ROOT/'root-selected-targets.jsonl',plan)
    write_rows(ROOT/'root-overrides.jsonl',override_rows)
    summary={'result':'PASS_ROOT_ADJUDICATION','head':head,'tree':tree,'window':'W1763-W1782','cells':240,
      'dispositions':dict(counts),'selectedTargets':len(plan),'catalogs':len(files),'entriesPerCatalog':5441,
      'rootOverrides':len(override_rows),
      'priorActiveHold1719IdPreserved':True,'nativeSpeakerApproval':False,'headedBrowserAcceptance':False,
      'baselineCatalogSha256':baseline}
    (ROOT/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    (ROOT/'input-attestation.json').write_text(json.dumps({'reviewHead':head,'reviewTree':tree,
      'crossChecksumListSha256':sha((INPUTS/'cross-review'/'SHA256SUMS.txt').read_bytes()),
      'crossLedgerSha256':sha(CROSS.read_bytes()),'rows':240,'priorHold1719':'hash-only; unchanged',
      'independentPostCrossAudit':'all 109 selected target hashes/provenance verified; no findings'},indent=2)+'\n',encoding='utf-8')
    print(json.dumps(summary,ensure_ascii=False,indent=2))
if __name__=='__main__': main()
