#!/usr/bin/env python3
"""Verify exact-head evidence for slskR lexical source indices 5420–5436."""
import argparse, collections, hashlib, json, re, subprocess, sys, unicodedata
from pathlib import Path
LOCALES=['ar','de','es','fr','hi','id','ja','ko','pt-BR','vi','zh-Hans','zh-Hant']
TERMINAL={'accepted','correction-needed','held','keep','corrected'}

def die(message): raise SystemExit('FAIL: '+message)
def sha(raw): return hashlib.sha256(raw).hexdigest()
def target_sha(value):
    raw=value.encode('utf-8') if isinstance(value,str) else json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode('utf-8')
    return sha(raw)
def placeholders(value):
    strings=[]
    def walk(x):
        if isinstance(x,str): strings.append(x)
        elif isinstance(x,dict):
            for child in x.values(): walk(child)
        elif isinstance(x,list):
            for child in x: walk(child)
    walk(value)
    return sorted(set(p for s in strings for p in re.findall(r'\{([^{}]+)\}',s)))
def git(repo,*args,raw=False):
    p=subprocess.run(['git',*args],cwd=repo,check=True,stdout=subprocess.PIPE)
    return p.stdout if raw else p.stdout.decode().strip()
def jsonl(path):
    rows=[]
    for n,line in enumerate(path.read_text(encoding='utf-8').splitlines(),1):
        if not line.strip(): continue
        try: rows.append((n,json.loads(line)))
        except json.JSONDecodeError as exc: die(f'invalid JSONL {path}:{n}: {exc}')
    return rows
def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--repo',type=Path,default=None)
    ap.add_argument('--prior-audit',type=Path,required=True)
    args=ap.parse_args()
    repo=(args.repo or Path(git(Path.cwd(),'rev-parse','--show-toplevel'))).resolve(); audit=args.prior_audit.resolve(); bundle=Path(__file__).resolve().parent
    m=json.loads((bundle/'manifest.json').read_text(encoding='utf-8')); head=m['review_head']; tree=m['review_tree']; source=m['source_catalog_head']; source_tree=m['source_catalog_tree']
    if git(repo,'rev-parse',f'{head}^{{tree}}')!=tree or git(repo,'rev-parse',f'{source}^{{tree}}')!=source_tree: die('exact commit/tree pin mismatch')
    git(repo,'cat-file','-e',f'{head}^{{commit}}'); git(repo,'cat-file','-e',f'{source}^{{commit}}')
    if any(not p.startswith('docs/') for p in git(repo,'diff','--name-only',source,head).splitlines()): die('review head contains non-doc changes after source/catalog head')
    catalogs={}; keysets={}
    for loc in LOCALES:
        path=f'web/src/lib/locales/ui-labels.{loc}.json'; raw=git(repo,'show',f'{head}:{path}',raw=True)
        if sha(raw)!=m['direct_catalog']['catalog_sha256'][path]: die(f'catalog hash mismatch: {loc}')
        catalogs[loc]=json.loads(raw); keysets[loc]=set(catalogs[loc])
    if len(set(map(frozenset,keysets.values())))!=1 or len(next(iter(keysets.values())))!=5437: die('locale key inventories differ')
    ids=sorted(next(iter(keysets.values())))
    if sum(len(c) for c in catalogs.values())!=65244: die('catalog slot count mismatch')
    selection=[r for _,r in jsonl(bundle/'selection.jsonl')]
    decisions=[r for _,r in jsonl(bundle/'decisions.jsonl')]
    carries=[r for _,r in jsonl(bundle/'carries.jsonl')]
    exclusions=[r for _,r in jsonl(bundle/'terminal-exclusions.jsonl')]
    if (len(selection),len(decisions),len(carries),len(exclusions))!=(204,6,169,29): die('window row counts mismatch')
    key=lambda r:(r['source_id'],r['locale'])
    for rows,name in [(selection,'selection'),(decisions,'decisions'),(carries,'carries'),(exclusions,'exclusions')]:
        pairs=[key(r) for r in rows]
        if len(pairs)!=len(set(pairs)): die(f'duplicate cell in {name}')
    if set(map(key,selection))!=set(map(key,decisions+carries+exclusions)): die('selection does not partition into decisions, carries, exclusions')
    source_ids=sorted({r['source_id'] for r in selection})
    if [ids.index(s) for s in source_ids]!=list(range(5420,5437)): die('selected keys are not lexical indices 5420–5436')
    for row in selection:
        sid=row['source_id']; loc=row['locale']; value=catalogs[loc].get(sid,'__MISSING__')
        if loc not in LOCALES or not row['populated'] or value=='__MISSING__': die(f'missing candidate: {loc}:{sid}')
        if value!=row['target_text'] or target_sha(value)!=row['target_sha256'] or row['source_sha256']!=sha(sid.encode()): die(f'current target/hash mismatch: {loc}:{sid}')
        if ids.index(sid)!=row['source_index']: die(f'lexical source index mismatch: {sid}')
    counts=collections.Counter(r['status'] for r in decisions); prior=collections.Counter(r['status'] for r in carries+exclusions)
    if counts!=collections.Counter({'accepted':6}) or prior!=collections.Counter({'accepted':169,'correction-needed':28,'held':1}): die(f'status counts mismatch: {dict(counts)} / {dict(prior)}')
    if any(r['source_id']!='⭐ Smart Ranking (Best Overall)' or r['status']!='accepted' or r['locale'] not in ['ar','de','es','fr','hi','id'] for r in decisions): die('unexpected new decision row')
    for row in decisions:
        if row['review_head']!=head or row['review_tree']!=tree or row['reviewed_code_head']!=source or row['reviewed_code_tree']!=source_tree: die('fresh decision head/tree pin mismatch')
        if placeholders(row['source_id'])!=placeholders(row['target_text']) or row['placeholders_source'] or row['placeholders_target']: die('fresh decision placeholder mismatch')
        if '⭐' not in row['target_text'] or row['protected_literals']!=['⭐'] or not row['protected_literals_preserved']: die('star marker not preserved')
        if row.get('proposed_target') is not None or row.get('icu_message') is not False: die('unexpected proposal or ICU message')
        if any(unicodedata.category(ch)=='Cf' for ch in row['target_text']): die('unsafe format control')

    # Context code blobs are frozen at the reviewed source/catalog head.
    c=m['source_context']
    if sha((bundle/c['file']).read_bytes())!=c['evidence_text_sha256']: die('source-context evidence hash mismatch')
    for path,digest in c['sha256'].items():
        if sha(git(repo,'show',f'{source}:{path}',raw=True))!=digest: die(f'source context hash mismatch: {path}')
        if git(repo,'rev-parse',f'{source}:{path}')!=c['git_blob_ids'][path]: die(f'source context blob mismatch: {path}')

    # Rehash every input and reconstruct exact terminal matches from the retained scan manifest.
    scan=[r for _,r in jsonl(bundle/'prior-evidence-scan-manifest.jsonl')]
    if len(scan)!=m['prior_overlap_scan']['scanned_jsonl_files']: die('prior scan input count mismatch')
    if sha((bundle/'prior-evidence-scan-manifest.jsonl').read_bytes())!=m['prior_overlap_scan']['manifest_sha256']: die('prior scan manifest checksum mismatch')
    refs=collections.defaultdict(list); prior_ids=set(source_ids)
    for entry in scan:
        root=entry['root']; rel=Path(entry['path'])
        if rel.is_absolute() or '..' in rel.parts: die('unsafe scan path')
        base=audit if root=='prior-audit-7ff' else repo if root=='pr-e05-worktree' else None
        if base is None: die(f'unknown input root: {root}')
        raw=(base/rel).read_bytes()
        if len(raw)!=entry['bytes'] or sha(raw)!=entry['sha256']: die(f'overlap input hash mismatch: {root}:{rel}')
        for n,line in enumerate(raw.decode('utf-8').splitlines(),1):
            if not line.strip(): continue
            try: r=json.loads(line)
            except json.JSONDecodeError: continue
            sid=r.get('source_id') or r.get('message_id') or r.get('id'); loc=r.get('locale')
            if sid not in prior_ids or loc not in LOCALES: continue
            status=str(r.get('status') or r.get('review_outcome') or '').strip().lower().replace('_','-')
            if status not in TERMINAL: continue
            s=next(x for x in selection if x['source_id']==sid and x['locale']==loc)
            if r.get('source_sha256')!=s['source_sha256'] or (r.get('target_sha256') or r.get('current_target_sha256'))!=s['target_sha256']: continue
            refs[(sid,loc)].append({'status':status,'batch':r.get('batch'),'finding_id':r.get('finding_id'),'root':root,'path':rel.as_posix(),'line':n})
    canonical=sha(json.dumps(sorted(scan,key=lambda x:(x['root'],x['path'])),sort_keys=True,separators=(',',':')).encode())
    if canonical!=m['prior_overlap_scan']['canonical_input_manifest_sha256']: die('canonical prior scan hash mismatch')
    for row in selection:
        actual=sorted(refs.get(key(row),[]),key=lambda x:(x['root'],x['path'],x['line'],x['status']))
        recorded=sorted(row['prior_exact_matches'],key=lambda x:(x['root'],x['path'],x['line'],x['status']))
        if actual!=recorded: die(f'prior exact references mismatch: {row["locale"]}:{row["source_id"]}')
        statuses={x['status'] for x in actual}
        if row['selection_disposition']=='fresh-decision' and statuses: die('fresh decision has terminal overlap')
        if row['selection_disposition']=='exact-accepted-carry' and statuses!={'accepted'}: die('accepted carry exact status mismatch')
        if row['selection_disposition']=='exact-terminal-exclusion' and statuses!={row['status']}: die('terminal exclusion exact status mismatch')

    sums={}
    for line in (bundle/'SHA256SUMS').read_text(encoding='utf-8').splitlines():
        match=re.fullmatch(r'([0-9a-f]{64})  (.+)',line)
        if not match: die('bad SHA256SUMS row')
        sums[match.group(2)]=match.group(1)
    expected={f.name:sha(f.read_bytes()) for f in bundle.iterdir() if f.is_file() and f.name!='SHA256SUMS'}
    if sums!=expected: die('SHA256SUMS mismatch')
    print(json.dumps({'result':'PASS','review_head':head,'review_tree':tree,'source_catalog_head':source,'source_catalog_tree':source_tree,
      'source_keys':17,'cell_slots':204,'fresh_decisions':dict(counts),'prior_exact':dict(prior),
      'final_dispositions':{'accepted':175,'correction-needed':28,'held':1},'overlap_inputs_rehashed':len(scan),'bundle_sha256s':len(sums)},ensure_ascii=False,indent=2))
if __name__=='__main__': main()
