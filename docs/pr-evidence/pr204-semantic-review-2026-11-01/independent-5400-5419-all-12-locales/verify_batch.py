#!/usr/bin/env python3
"""Verify the exact-head 5400–5419 semantic-review evidence bundle."""
from __future__ import annotations
import argparse
import collections
import hashlib
import json
import re
import subprocess
import sys
import unicodedata
from pathlib import Path

LOCALES = ['ar','de','es','fr','hi','id','ja','ko','pt-BR','vi','zh-Hans','zh-Hant']
TERMINAL = {'accepted','correction-needed','held','keep','corrected'}
BATCH = 'independent-5400-5419-all-12-locales'


def die(message: str) -> None:
    raise SystemExit('FAIL: ' + message)


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def ph(text: str) -> list[str]:
    return sorted(re.findall(r'\{([^{}]+)\}', text))


def git(repo: Path, *args: str, raw: bool = False):
    p = subprocess.run(['git', *args], cwd=repo, check=True, stdout=subprocess.PIPE)
    return p.stdout if raw else p.stdout.decode().strip()


def read_jsonl(path: Path):
    rows=[]
    for number,line in enumerate(path.read_text(encoding='utf-8').splitlines(),1):
        if not line.strip():
            continue
        try:
            rows.append((number,json.loads(line)))
        except json.JSONDecodeError as exc:
            die(f'invalid JSONL at {path}:{number}: {exc}')
    return rows


def main() -> None:
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--repo',type=Path,default=None,help='slskR checkout/worktree (default: git top level)')
    ap.add_argument('--prior-audit',type=Path,required=True,help='read-only frozen 7ff45482 audit archive used by the overlap scan')
    args=ap.parse_args()
    repo=(args.repo or Path(git(Path.cwd(),'rev-parse','--show-toplevel'))).resolve()
    audit=args.prior_audit.resolve()
    bundle=Path(__file__).resolve().parent
    manifest=json.loads((bundle/'manifest.json').read_text(encoding='utf-8'))
    head=manifest['review_head']; tree=manifest['review_tree']; source_head=manifest['source_catalog_head']; source_tree=manifest['source_catalog_tree']
    if git(repo,'rev-parse',f'{head}^{{tree}}') != tree: die('review head tree pin mismatch')
    if git(repo,'rev-parse',f'{source_head}^{{tree}}') != source_tree: die('source/catalog tree pin mismatch')
    git(repo,'cat-file','-e',f'{head}^{{commit}}')
    git(repo,'cat-file','-e',f'{source_head}^{{commit}}')
    changed=git(repo,'diff','--name-only',source_head,head).splitlines()
    if any(not p.startswith('docs/') for p in changed):
        die('pinned review head includes non-documentation changes beyond source/catalog head')
    # Every direct locale catalog is read from the immutable review commit.
    catalogs={}; catalog_hashes={}; blank_by_locale={}; plural_by_locale={}; keys_by_locale={}
    for locale in LOCALES:
        path=f'web/src/lib/locales/ui-labels.{locale}.json'
        raw=git(repo,'show',f'{head}:{path}',raw=True)
        catalog_hashes[path]=sha(raw)
        catalogs[locale]=json.loads(raw)
        keys_by_locale[locale]=set(catalogs[locale])
        blank_by_locale[locale]=sum(1 for v in catalogs[locale].values() if v in ('',None))
        plural_by_locale[locale]=sum(1 for v in catalogs[locale].values() if isinstance(v,dict))
        for source_id,value in catalogs[locale].items():
            if isinstance(value,dict):
                if set(value)!={'zero','one','two','few','many','other'} or not all(isinstance(x,str) and x.strip() for x in value.values()):
                    die(f'invalid structured plural-form map: {locale}:{source_id}')
            elif not isinstance(value,str) or not value.strip():
                die(f'empty or unsupported catalog value: {locale}:{source_id}')
        if sha(raw)!=manifest['direct_catalog']['catalog_sha256'][path]: die(f'catalog byte hash mismatch: {path}')
    if len(set(map(frozenset,keys_by_locale.values())))!=1: die('locale catalogs have different key sets')
    all_ids=next(iter(keys_by_locale.values()))
    if len(all_ids)!=manifest['direct_catalog']['source_ids']: die('direct catalog key count mismatch')
    total_slots=sum(len(c) for c in catalogs.values())
    total_populated=sum(sum(1 for v in c.values() if v not in ('',None)) for c in catalogs.values())
    if (total_slots,total_populated)!=(manifest['direct_catalog']['slots'],manifest['direct_catalog']['populated_cells']): die('direct catalog populated-cell census mismatch')
    blank_by_locale={k:v for k,v in blank_by_locale.items() if v}
    if blank_by_locale!=manifest['direct_catalog']['blank_locale_counts']: die(f'blank cells by locale differ: {blank_by_locale}')
    plural_by_locale={k:v for k,v in plural_by_locale.items() if v}
    if sum(plural_by_locale.values())!=manifest['direct_catalog']['structured_plural_cells'] or plural_by_locale!=manifest['direct_catalog']['structured_plural_locale_counts']:
        die(f'structured plural-form census mismatch: {plural_by_locale}')

    selection=read_jsonl(bundle/'selection.jsonl')
    decisions=read_jsonl(bundle/'decisions.jsonl')
    carries=read_jsonl(bundle/'carries.jsonl')
    exclusions=read_jsonl(bundle/'terminal-exclusions.jsonl')
    selection_rows=[r for _,r in selection]; decision_rows=[r for _,r in decisions]
    carry_rows=[r for _,r in carries]; exclusion_rows=[r for _,r in exclusions]
    if len(selection_rows)!=240 or len(decision_rows)!=96 or len(carry_rows)!=74 or len(exclusion_rows)!=70: die('selection/decision/carry/exclusion row count mismatch')
    key_order=sorted(all_ids)
    if [key_order.index(s) for s in sorted({r['source_id'] for r in selection_rows})] != list(range(5400,5420)): die('selected source IDs are not lexical indices 5400–5419')
    cell_key=lambda r:(r['source_id'],r['locale'])
    for rows,name in [(selection_rows,'selection'),(decision_rows,'decisions'),(carry_rows,'carries'),(exclusion_rows,'exclusions')]:
        keys=[cell_key(r) for r in rows]
        if len(keys)!=len(set(keys)): die(f'duplicate source/locale cell in {name}')
    if set(map(cell_key,selection_rows)) != set(map(cell_key,decision_rows+carry_rows+exclusion_rows)): die('selection rows do not partition exactly into decisions, carries, and exclusions')
    statuses=collections.Counter(); prior=collections.Counter(); per_source=collections.Counter()
    for row in selection_rows:
        sid=row['source_id']; locale=row['locale']
        if locale not in LOCALES: die(f'unknown locale: {locale}')
        if not row.get('populated') or row.get('target_text') in ('',None): die(f'candidate is blank: {locale}:{sid}')
        if row['source_sha256']!=sha(sid.encode()): die(f'source hash mismatch: {locale}:{sid}')
        value=catalogs[locale].get(sid)
        if value!=row['target_text'] or sha(str(value).encode())!=row['target_sha256']: die(f'e05 target text/hash mismatch: {locale}:{sid}')
        if row['source_index']!=key_order.index(sid): die(f'source index mismatch: {sid}')
        disposition=row['selection_disposition']
        if disposition=='fresh-decision':
            statuses[row['decision_status']]+=1; per_source[row['source_index']]+=1
        elif disposition=='exact-accepted-carry': prior['accepted']+=1
        elif disposition=='exact-terminal-exclusion': prior[row['status']]+=1
        else: die(f'unknown selection disposition: {disposition}')
    if statuses!=collections.Counter({'accepted':39,'correction-needed':33,'held':24}): die(f'fresh status counts differ: {dict(statuses)}')
    if prior!=collections.Counter({'accepted':74,'correction-needed':46,'held':24}): die(f'prior status counts differ: {dict(prior)}')
    if len(per_source)!=16 or set(per_source.values())!={6}: die('fresh decision source-key/locale cardinality differs')

    # Validate semantic fields, placeholders, protected literals, and status rows.
    for row in decision_rows:
        if row['batch']!=BATCH or row['review_head']!=head or row['review_tree']!=tree: die('fresh decision is not pinned to this batch/head/tree')
        source=row['source_id']; target=row['target_text']; proposed=row.get('proposed_target')
        if ph(source)!=ph(target) or ph(target)!=row['placeholders_target']: die(f'placeholder mismatch: {row["locale"]}:{source}')
        if proposed is not None and ph(proposed)!=ph(source): die(f'proposal placeholder mismatch: {row["locale"]}:{source}')
        if row['status']=='correction-needed' and not proposed: die(f'correction has no proposal: {row["locale"]}:{source}')
        if row['status']!='correction-needed' and proposed is not None: die(f'non-correction row has a proposal: {row["locale"]}:{source}')
        if row.get('icu_message') is not False: die('unexpected ICU record flag')
        for text in (target,proposed or ''):
            if any(unicodedata.category(ch)=='Cf' for ch in text): die(f'unsafe Unicode format control: {row["locale"]}:{source}')
        if row['source_index']==5402:
            if '→' not in source or not any(mark in target for mark in ('→','←')) or '·' not in target: die('Discovery Graph protected marker missing')
        if row['source_index']==5415 and ('·' not in target or '%' not in target): die('album-candidate protected separator/percent missing')
    for row in carry_rows+exclusion_rows:
        if row['review_head']!=head or row['review_tree']!=tree: die('prior disposition row is not pinned to this batch head/tree')

    # Verify caller context excerpts against source blobs at the frozen code head.
    source_context=manifest['source_context']
    context_raw=(bundle/source_context['file']).read_bytes()
    for path,digest in source_context['sha256'].items():
        raw=git(repo,'show',f'{source_head}:{path}',raw=True)
        if sha(raw)!=digest: die(f'context source file hash mismatch: {path}')
        if git(repo,'rev-parse',f'{source_head}:{path}')!=source_context['git_blob_ids'][path]: die(f'context source blob mismatch: {path}')
    rtl=manifest['rtl_direction_evidence']; arabic=json.loads(git(repo,'show',f'{source_head}:{rtl["catalog_path"]}',raw=True))
    if sha(rtl['target_text'].encode())!=rtl['target_sha256'] or arabic.get(rtl['source_id'])!=rtl['target_text']: die('Arabic RTL route precedent mismatch')
    # Re-run the literal search that caused contextless cells to be held.
    for sid in source_context['contextless_source_ids']:
        p=subprocess.run(['rg','-n','-F',sid,'web/src','--glob','*.jsx','--glob','*.js','--glob','*.tsx','--glob','*.ts','--glob','!**/locales/**','--glob','!**/*.test.*','--glob','!**/*.spec.*'],cwd=repo,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        if p.returncode==0: die(f'contextless source now has a runtime caller: {sid}')
        if p.returncode!=1: die(f'ripgrep context search failed for {sid}: {p.stderr.decode(errors="replace")}')

    # Rehash every exact prior-overlap input and reconstruct each cell's prior records.
    scan_rows=read_jsonl(bundle/'prior-evidence-scan-manifest.jsonl')
    if len(scan_rows)!=manifest['prior_overlap_scan']['scanned_jsonl_files']: die('prior scan manifest file count mismatch')
    if sha((bundle/'prior-evidence-scan-manifest.jsonl').read_bytes())!=manifest['prior_overlap_scan']['manifest_sha256']: die('prior scan manifest hash mismatch')
    inputs=[]
    refs=collections.defaultdict(list)
    selected_ids={r['source_id'] for r in selection_rows}
    for _,entry in scan_rows:
        root=entry['root']; rel=Path(entry['path'])
        if rel.is_absolute() or '..' in rel.parts: die('unsafe prior scan path')
        base=audit if root=='prior-audit-7ff' else repo if root=='pr-e05-worktree' else None
        if base is None: die(f'unknown prior scan root label: {root}')
        path=base/rel; raw=path.read_bytes()
        if len(raw)!=entry['bytes'] or sha(raw)!=entry['sha256']: die(f'prior overlap input hash mismatch: {root}:{rel}')
        inputs.append({'root':root,'path':rel.as_posix(),'sha256':entry['sha256'],'bytes':entry['bytes']})
        for number,line in enumerate(raw.decode('utf-8').splitlines(),1):
            if not line.strip(): continue
            try: prior_row=json.loads(line)
            except json.JSONDecodeError: continue
            sid=prior_row.get('source_id') or prior_row.get('message_id') or prior_row.get('id')
            locale=prior_row.get('locale')
            if sid not in selected_ids or locale not in LOCALES: continue
            status=str(prior_row.get('status') or prior_row.get('review_outcome') or '').strip().lower().replace('_','-')
            if status not in TERMINAL: continue
            selection_row=next(r for r in selection_rows if r['source_id']==sid and r['locale']==locale)
            if prior_row.get('source_sha256')!=selection_row['source_sha256']: continue
            target_hash=prior_row.get('target_sha256') or prior_row.get('current_target_sha256')
            if target_hash!=selection_row['target_sha256']: continue
            refs[(sid,locale)].append({'status':status,'batch':prior_row.get('batch'),'finding_id':prior_row.get('finding_id'),'root':root,'path':rel.as_posix(),'line':number})
    inputs.sort(key=lambda x:(x['root'],x['path']))
    canonical=sha(json.dumps(inputs,sort_keys=True,separators=(',',':')).encode())
    if canonical!=manifest['prior_overlap_scan']['canonical_input_manifest_sha256']: die('canonical prior scan input manifest hash mismatch')
    for row in selection_rows:
        actual=sorted(refs.get(cell_key(row),[]),key=lambda x:(x['root'],x['path'],x['line'],x.get('status','')))
        recorded=sorted(row['prior_exact_matches'],key=lambda x:(x['root'],x['path'],x['line'],x.get('status','')))
        if actual!=recorded: die(f'exact overlap references differ: {row["locale"]}:{row["source_id"]}')
        found_statuses={x['status'] for x in actual}
        disposition=row['selection_disposition']
        if disposition=='fresh-decision' and found_statuses: die(f'fresh decision overlaps terminal evidence: {row["locale"]}:{row["source_id"]}')
        if disposition=='exact-accepted-carry' and found_statuses!={'accepted'}: die('accepted carry does not have only accepted terminal matches')
        if disposition=='exact-terminal-exclusion' and found_statuses!={row['status']}: die('terminal exclusion status differs from exact prior records')

    # Verify file checksums after all bundle contents are finalized.
    sums={}
    for line in (bundle/'SHA256SUMS').read_text(encoding='utf-8').splitlines():
        match=re.fullmatch(r'([0-9a-f]{64})  (.+)',line)
        if not match: die('invalid SHA256SUMS row')
        sums[match.group(2)]=match.group(1)
    expected={p.name:sha(p.read_bytes()) for p in bundle.iterdir() if p.is_file() and p.name!='SHA256SUMS'}
    if sums!=expected: die('SHA256SUMS does not exactly cover bundle files')
    print(json.dumps({'result':'PASS','review_head':head,'review_tree':tree,'source_catalog_head':source_head,'source_catalog_tree':source_tree,
      'catalog_slots':total_slots,'populated_cells':total_populated,'fresh_decisions':dict(statuses),'prior_exact':dict(prior),
      'final_dispositions':dict(collections.Counter({k:statuses[k]+prior[k] for k in TERMINAL if statuses[k]+prior[k]})),
      'overlap_inputs_rehashed':len(inputs),'bundle_sha256s':len(sums)},ensure_ascii=False,indent=2))

if __name__=='__main__':
    main()
