#!/usr/bin/env python3
"""Verify slskR PR #204 exact-status conflict adjudications and final evidence scan."""
import argparse, collections, hashlib, json, re, subprocess
from pathlib import Path

LOCALES=['ar','de','es','fr','hi','id','ja','ko','pt-BR','vi','zh-Hans','zh-Hant']
TERMINAL={'accepted','correction-needed','corrected','held','keep'}
ALIASES={'source_id':['source_id','sourceId','message_id','id'],'source_sha':['source_sha256','sourceSha256'],'target_sha':['target_sha256','targetSha256','current_target_sha256'],'status':['status','disposition','review_outcome']}

def fail(s): raise SystemExit('FAIL: '+s)
def sha(b): return hashlib.sha256(b).hexdigest()
def canonical(v): return json.dumps(v,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode('utf-8')
def target_sha(v):
    return sha(v.encode('utf-8') if isinstance(v,str) else canonical(v))
def placeholders(v): return sorted(set(re.findall(r'\{([^{}]+)\}',str(v))))
def has_icu(v): return bool(re.search(r'\{[^{}]+,\s*(?:plural|select|selectordinal)\s*,',str(v),re.I))
def git(repo,*args,raw=False):
    b=subprocess.check_output(['git',*args],cwd=repo)
    return b if raw else b.decode('utf-8').strip()
def pick(d,names):
    for n in names:
        if d.get(n) is not None: return d[n]
    return None
def walk(x):
    if isinstance(x,dict):
        yield x
        for v in x.values(): yield from walk(v)
    elif isinstance(x,list):
        for v in x: yield from walk(v)
def load_jsonl(raw):
    out=[]
    for n,line in enumerate(raw.decode('utf-8').splitlines(),1):
        if not line.strip(): continue
        out.append((n,json.loads(line)))
    return out
def load_evidence_file(raw,suffix):
    if suffix=='.jsonl': return load_jsonl(raw)
    return [(n+1,row) for n,row in enumerate(walk(json.loads(raw.decode('utf-8'))))]

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--repo',type=Path,default=Path.cwd())
    ap.add_argument('--prior-audit',type=Path,required=True)
    ap.add_argument('--out',type=Path)
    args=ap.parse_args(); repo=args.repo.resolve(); prior=args.prior_audit.resolve(); bundle=Path(__file__).resolve().parent
    m=json.loads((bundle/'manifest.json').read_text(encoding='utf-8'))
    baseline=m['baseline_head']; source=m['source_head']; app=m.get('application_head')
    if not app: fail('manifest has no application_head; populate after the exact catalog commit')
    if git(repo,'rev-parse',f'{baseline}^{{tree}}')!=m['baseline_tree']: fail('baseline tree pin mismatch')
    if git(repo,'rev-parse',f'{source}^{{tree}}')!=m['source_tree']: fail('source tree pin mismatch')
    if git(repo,'rev-parse',f'{app}^{{tree}}')!=m['application_tree']: fail('application tree pin mismatch')
    if git(repo,'rev-parse',f'{app}^')!=m['application_parent_head']: fail('application parent mismatch')
    if m['application_parent_head']!=baseline: fail('catalog application did not start at reviewed baseline')

    sums={}
    for line in (bundle/'SHA256SUMS').read_text().splitlines():
        h,name=line.split('  ',1);sums[name]=h
    expected={p.name:sha(p.read_bytes()) for p in bundle.iterdir() if p.is_file() and p.name!='SHA256SUMS'}
    if sums!=expected: fail('bundle SHA256SUMS mismatch')

    prior_raw=(bundle/'prior-conflicts.json').read_bytes()
    if sha(prior_raw)!=m['prior_conflict_snapshot_sha256']: fail('prior conflict snapshot hash mismatch')
    prior_doc=json.loads(prior_raw.decode('utf-8'))
    summary_raw=(bundle/'pre-scan-summary.json').read_bytes()
    if sha(summary_raw)!=m['pre_scan_summary_sha256']: fail('pre-scan summary hash mismatch')
    scan=json.loads(summary_raw.decode('utf-8'))
    if (scan['head'],scan['head_tree'],scan['source_catalog_head'],scan['source_catalog_tree'])!=(baseline,m['baseline_tree'],source,m['source_tree']): fail('pre-scan pins differ')
    prior_conflicts=prior_doc['conflicts']
    if len(prior_conflicts)!=25 or m['baseline_conflicts']!=25: fail('baseline conflict count mismatch')

    inventory=prior/'frozen-inputs/source-inventory.jsonl'
    ids=sorted({json.loads(x)['source_id'] for x in inventory.read_text(encoding='utf-8').splitlines() if x.strip()})
    if len(ids)!=m['source_id_count']: fail('frozen source ID count mismatch')
    before={};after={};base_catalog_hashes={};app_catalog_hashes={}
    for loc in LOCALES:
        path=f'web/src/lib/locales/ui-labels.{loc}.json'
        braw=git(repo,'show',f'{baseline}:{path}',raw=True);araw=git(repo,'show',f'{app}:{path}',raw=True)
        bcat=json.loads(braw.decode('utf-8'));acat=json.loads(araw.decode('utf-8'))
        if set(bcat)!=set(ids) or set(acat)!=set(ids): fail(f'catalog keyset mismatch {loc}')
        if not all(isinstance(v,(str,dict,list)) and (not isinstance(v,str) or v.strip()) for v in acat.values()): fail(f'empty/non-string catalog cell {loc}')
        before[loc]=bcat;after[loc]=acat;base_catalog_hashes[path]=sha(braw);app_catalog_hashes[path]=sha(araw)
    if base_catalog_hashes!=m['catalog_sha256_before'] or app_catalog_hashes!=m['catalog_sha256_after']: fail('catalog file hashes differ from manifest')

    ctxraw=(bundle/'source-contexts.jsonl').read_bytes()
    if sha(ctxraw)!=m['source_context_sha256']: fail('source context hash mismatch')
    contexts={}
    for _,c in load_jsonl(ctxraw):
        raw=git(repo,'show',f'{source}:{c["path"]}',raw=True)
        if sha(raw)!=c['file_sha256'] or git(repo,'rev-parse',f'{source}:{c["path"]}')!=c['git_blob']: fail('source context file pin mismatch '+c['context_id'])
        lines=raw.decode('utf-8').splitlines(); excerpt='\n'.join(f'{i}: {lines[i-1]}' for i in range(c['line_start'],c['line_end']+1))+'\n'
        if excerpt!=c['excerpt'] or sha(excerpt.encode())!=c['excerpt_sha256']: fail('source context excerpt mismatch '+c['context_id'])
        contexts[c['context_id']]=c
    if len(contexts)!=m['source_context_count']: fail('source context count mismatch')

    fmraw=(bundle/m['prior_evidence_file_manifest']).read_bytes()
    if sha(fmraw)!=m['prior_evidence_file_manifest_sha256']: fail('prior evidence file manifest hash mismatch')
    fm={(r['root'],r['path']):r for _,r in load_jsonl(fmraw)}
    if len(fm)!=m['prior_evidence_file_manifest_count']: fail('prior evidence manifest count mismatch')
    prior_file_cache={}
    for (root,path),f in fm.items():
        if root=='prior-audit-7ff': raw=(prior/path).read_bytes()
        elif root=='pr-review-head': raw=git(repo,'show',f'{baseline}:{path}',raw=True)
        else: fail('unknown evidence root '+root)
        if len(raw)!=f['bytes'] or sha(raw)!=f['sha256']: fail('prior evidence input hash mismatch '+root+':'+path)
        prior_file_cache[(root,path)]=raw

    resolution_raw=(bundle/'conflict-resolutions.jsonl').read_bytes()
    if sha(resolution_raw)!=m['resolution_ledger_sha256']: fail('resolution ledger hash mismatch')
    resolutions=[r for _,r in load_jsonl(resolution_raw)]
    if len(resolutions)!=25 or len({(r['source_id'],r['locale']) for r in resolutions})!=25: fail('resolution row count/uniqueness mismatch')
    bycell={(r['source_id'],r['locale']):r for r in resolutions}
    expected={(x[1],x[2]):x for x in prior_conflicts}
    if set(bycell)!=set(expected): fail('resolution cells do not exactly cover baseline conflicts')
    all_diffs=set()
    for loc in LOCALES:
        all_diffs.update((sid,loc) for sid in ids if before[loc][sid]!=after[loc][sid])
    corrected={(r['source_id'],r['locale']) for r in resolutions if r['status']=='corrected'}
    if all_diffs!=corrected: fail('catalog diff includes missing or unledgered changes')
    changed_locales=sorted({loc for _,loc in all_diffs})
    if changed_locales!=m['changed_locales']: fail('changed locale set differs from manifest')
    changed_paths=git(repo,'diff','--name-only',m['application_parent_head'],app).splitlines()
    if changed_paths!=sorted(f'web/src/lib/locales/ui-labels.{loc}.json' for loc in changed_locales): fail('application commit touched unexpected paths')

    expected_outcomes=collections.Counter()
    suppress=set()
    for key,row in bycell.items():
        conflict=expected[key]; idx,sid,loc,statuses,refs=conflict
        if row['source_index']!=idx or ids[idx]!=sid: fail('source index mismatch '+str(key))
        if row['source_sha256']!=sha(sid.encode('utf-8')): fail('source hash mismatch '+str(key))
        if row['review_head']!=baseline or row['review_tree']!=m['baseline_tree'] or row['reviewed_source_head']!=source or row['reviewed_source_tree']!=m['source_tree']: fail('row pin mismatch '+str(key))
        old=before[loc][sid]; new=after[loc][sid]
        if old!=row['target_before_text'] or target_sha(old)!=row['target_before_sha256']: fail('before target hash mismatch '+str(key))
        if new!=row['target_after_text'] or target_sha(new)!=row['target_after_sha256'] or target_sha(new)!=row['target_sha256']: fail('after target hash mismatch '+str(key))
        if row['status']=='corrected' and old==new: fail('corrected row did not change catalog '+str(key))
        if row['status']!='corrected' and old!=new: fail('unchanged disposition changed catalog '+str(key))
        if placeholders(sid)!=placeholders(new) or placeholders(sid)!=row['placeholders_source'] or placeholders(new)!=row['placeholders_target']: fail('placeholder mismatch '+str(key))
        if row.get('proposed_target') is not None and placeholders(row['proposed_target'])!=placeholders(sid): fail('proposal placeholder mismatch '+str(key))
        if has_icu(sid) or has_icu(old) or has_icu(new) or has_icu(row.get('proposed_target')): fail('unexpected ICU syntax '+str(key))
        if not all(t in str(new) for t in row['protected_literals']): fail('protected literal mismatch '+str(key))
        oldrefs={(r['root'],r['path'],r['line'],r['status']) for r in refs}
        rowrefs={(r['root'],r['path'],r['line'],r['status']) for r in row['supersedes']}
        if oldrefs!=rowrefs or sorted(set(statuses))!=row['prior_statuses']: fail('superseded status refs mismatch '+str(key))
        for root,path,line,status in rowrefs:
            raw=prior_file_cache[(root,path)]
            lines=raw.decode('utf-8').splitlines()
            if not (1<=line<=len(lines)): fail('prior evidence line out of range')
            oldrec=json.loads(lines[line-1]); oldstatus=str(pick(oldrec,ALIASES['status']) or '').strip().lower().replace('_','-')
            if (pick(oldrec,ALIASES['source_id']),oldrec.get('locale'),pick(oldrec,ALIASES['source_sha']),pick(oldrec,ALIASES['target_sha']),oldstatus)!=(sid,loc,row['source_sha256'],row['target_before_sha256'],status): fail('prior exact status record mismatch '+str(key))
            suppress.add((root,path,line))
        expected_outcomes[row['status']]+=1
    if expected_outcomes!=collections.Counter({'accepted':8,'correction-needed':15,'corrected':2}) or dict(expected_outcomes)!=m['outcome_counts']: fail('final conflict dispositions mismatch')

    # Exact-current full evidence scan. Superseded rows are excluded only when a pinned resolution cites their original file and line.
    files=[]
    for path in ['findings.jsonl','carried-findings.jsonl']:
        files.append(('prior-audit-7ff',path,(prior/path).read_bytes()))
    for p in sorted((prior/'review-evidence').rglob('*')):
        if p.is_file() and p.suffix in ('.jsonl','.json'):
            files.append(('prior-audit-7ff',p.relative_to(prior).as_posix(),p.read_bytes()))
    repo_paths=git(repo,'ls-tree','-r','--name-only','HEAD','docs/pr-evidence/pr204-semantic-review-2026-11-01').splitlines()
    for path in repo_paths:
        if path.endswith(('.jsonl','.json')):
            files.append(('pr-review-head',path,git(repo,'show',f'HEAD:{path}',raw=True)))
    bycell_status=collections.defaultdict(list); file_manifest=[]
    for root,path,raw in sorted(files,key=lambda x:(x[0],x[1])):
        file_manifest.append({'root':root,'path':path,'bytes':len(raw),'sha256':sha(raw)})
        for line,rec in load_evidence_file(raw,Path(path).suffix):
            sid=pick(rec,ALIASES['source_id']);loc=rec.get('locale')
            if not isinstance(sid,str) or sid not in ids or loc not in LOCALES: continue
            status=str(pick(rec,ALIASES['status']) or '').strip().lower().replace('_','-')
            if status not in TERMINAL: continue
            cat=after[loc]
            if pick(rec,ALIASES['source_sha'])!=sha(sid.encode('utf-8')) or pick(rec,ALIASES['target_sha'])!=target_sha(cat[sid]): continue
            if (root,path,line) in suppress: continue
            bycell_status[(sid,loc)].append(status)
    counts=collections.Counter();per={l:collections.Counter() for l in LOCALES};conflicts=[];unreviewed=[]
    for loc in LOCALES:
        for sid in ids:
            sts=sorted(set(bycell_status[(sid,loc)]))
            if not sts: counts['unreviewed']+=1;per[loc]['unreviewed']+=1;unreviewed.append((ids.index(sid),sid,loc))
            elif len(sts)>1: counts['conflict']+=1;per[loc]['conflict']+=1;conflicts.append((ids.index(sid),sid,loc,sts))
            else: counts[sts[0]]+=1;per[loc][sts[0]]+=1
    if len(files)!=int(m['expected_final_evidence_file_count']): fail(f'evidence input count mismatch: {len(files)}')
    if conflicts: fail(f'{len(conflicts)} exact-current conflicts remain: {conflicts[:5]}')
    if dict(counts)!=m['expected_final_status_counts']: fail(f'final status counts mismatch: {dict(counts)}')
    if len(unreviewed)!=m['expected_final_unreviewed_cells']: fail('final unreviewed cell count mismatch')
    report={'head':git(repo,'rev-parse','HEAD'),'head_tree':git(repo,'rev-parse','HEAD^{tree}'),'application_head':app,'source_head':source,'cell_count':m['catalog_cell_count'],'evidence_files_scanned':len(files),'evidence_scan_manifest_sha256':sha(canonical(sorted(file_manifest,key=lambda r:(r['root'],r['path'])))),'unique_current_cell_status_counts':dict(sorted(counts.items())),'per_locale_exact_status_counts':{l:dict(sorted(c.items())) for l,c in per.items()},'unreviewed_cells':len(unreviewed),'unreviewed_source_index_count':len({i for i,_,_ in unreviewed}),'conflicts':conflicts,'conflict_resolution_rows':len(resolutions),'conflicts_resolved':len(suppress)}
    if args.out:
        args.out.parent.mkdir(parents=True,exist_ok=True);args.out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'result':'PASS','application_head':app,'verification_head':report['head'],'resolved_conflicts':len(resolutions),'outcomes':dict(expected_outcomes),'corrections_exact':len(all_diffs),'final_status_counts':dict(sorted(counts.items())),'unreviewed_cells':len(unreviewed),'evidence_files_scanned':len(files),'evidence_scan_manifest_sha256':report['evidence_scan_manifest_sha256']},ensure_ascii=False,indent=2))

if __name__=='__main__': main()
