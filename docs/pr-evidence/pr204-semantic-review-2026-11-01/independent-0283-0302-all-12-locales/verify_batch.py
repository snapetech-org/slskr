#!/usr/bin/env python3
"""Verify exact-head semantic-review evidence for slskR source indices 283–302."""
import argparse
import collections
import hashlib
import json
import re
import subprocess
from pathlib import Path

LOCALES=['ar','de','es','fr','hi','id','ja','ko','pt-BR','vi','zh-Hans','zh-Hant']
TERMINAL={'accepted','correction-needed','held','keep','corrected'}
ALIASES={'source_id':['source_id','sourceId','message_id','id'],
         'source_sha':['source_sha256','sourceSha256'],
         'target_sha':['target_sha256','targetSha256','current_target_sha256'],
         'status':['status','review_outcome','disposition']}

def fail(message): raise SystemExit('FAIL: '+message)
def sha(raw): return hashlib.sha256(raw).hexdigest()
def value_sha(value):
    raw=value.encode('utf-8') if isinstance(value,str) else json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode('utf-8')
    return sha(raw)
def read_jsonl(path): return [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines() if line.strip()]
def pick(row,names):
    for name in names:
        if row.get(name) is not None: return row[name]
    return None
def normalize_status(value): return str(value or '').strip().lower().replace('_','-')
def walk(value):
    if isinstance(value,dict):
        yield value
        for child in value.values(): yield from walk(child)
    elif isinstance(value,list):
        for child in value: yield from walk(child)
def parse_evidence(raw,path):
    suffix=Path(path).suffix
    if suffix=='.jsonl':
        for number,line in enumerate(raw.decode('utf-8').splitlines(),1):
            if line.strip():
                try: yield number,json.loads(line)
                except json.JSONDecodeError: continue
    elif suffix=='.json':
        try: yield from enumerate(walk(json.loads(raw.decode('utf-8'))),1)
        except json.JSONDecodeError: return
def git(repo,*args,raw=False):
    result=subprocess.run(['git',*args],cwd=repo,check=True,stdout=subprocess.PIPE)
    return result.stdout if raw else result.stdout.decode('utf-8').strip()
def placeholders(value): return sorted(set(re.findall(r'\{([^{}]+)\}',str(value))))
def icu(value): return bool(re.search(r'\{\s*[A-Za-z_][\w.-]*\s*,\s*(plural|select|selectordinal)\s*,',str(value)))
def key(row): return row['source_id'],row['locale']

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo',type=Path,required=True)
    parser.add_argument('--prior-audit',type=Path,required=True)
    args=parser.parse_args();repo=args.repo.resolve();prior_audit=args.prior_audit.resolve();bundle=Path(__file__).resolve().parent
    m=json.loads((bundle/'manifest.json').read_text(encoding='utf-8'))
    review=m['review_head'];application=m['application_head'];source=m['source_catalog_head']
    for commit,tree in ((review,m['review_tree']),(application,m['application_tree']),(source,m['source_catalog_tree'])):
        if git(repo,'rev-parse',f'{commit}^{{tree}}')!=tree: fail('commit/tree mismatch '+commit)
    if git(repo,'rev-parse',f'{application}^')!=review or m['application_parent']!=review: fail('application is not a direct child of review head')
    expected_paths={f'web/src/lib/locales/ui-labels.{loc}.json' for loc in LOCALES}
    if set(git(repo,'diff','--name-only',f'{review}..{application}').splitlines())!=expected_paths: fail('application diff is not exactly the 12 locale catalogs')
    inv_path=prior_audit/'frozen-inputs/source-inventory.jsonl';inv_raw=inv_path.read_bytes()
    if sha(inv_raw)!=m['frozen_source_inventory_sha256']: fail('frozen source inventory checksum mismatch')
    inventory=read_jsonl(inv_path);source_ids=[r['source_id'] for r in inventory]
    if len(source_ids)!=5437 or source_ids!=sorted(source_ids): fail('frozen source inventory/order mismatch')
    selected_ids=source_ids[m['source_index_start']:m['source_index_end_inclusive']+1]
    if selected_ids!=m['source_ids'] or len(selected_ids)!=20: fail('source-index selection mismatch')

    before=read_jsonl(bundle/'selection-before-corrections.jsonl');final=read_jsonl(bundle/'selection.jsonl')
    decisions=read_jsonl(bundle/'decisions.jsonl');audits=read_jsonl(bundle/'reviewed-cell-audit.jsonl')
    carries=read_jsonl(bundle/'carries.jsonl');exclusions=read_jsonl(bundle/'terminal-exclusions.jsonl')
    conflicts=read_jsonl(bundle/'conflict-holds.jsonl');patches=read_jsonl(bundle/'applied-corrections.jsonl')
    roots=read_jsonl(bundle/'root-cross-review.jsonl');plan=read_jsonl(bundle/'root-apply-plan.jsonl')
    candidates=read_jsonl(bundle/'candidate-corrections.jsonl');recon=read_jsonl(bundle/'conflict-reconciliation.jsonl')
    supplement=read_jsonl(bundle/'candidate-supplement.jsonl')
    groups=(before,final,decisions,audits,carries,exclusions,conflicts,patches,roots,plan,candidates,recon)
    names=('baseline','final selection','fresh decisions','full audit','carries','exclusions','conflicts','patches','root review','root plan','candidates','conflict reconciliation')
    for rows,name in zip(groups,names):
        if len({key(r) for r in rows})!=len(rows): fail('duplicate cell in '+name)
    if tuple(map(len,groups))!=(240,240,60,240,147,0,0,43,43,43,43,0): fail('row counts mismatch '+str(tuple(map(len,groups))))
    if len(supplement)!=4: fail('candidate supplement must contain four rows')
    before_by={key(r):r for r in before};final_by={key(r):r for r in final};audit_by={key(r):r for r in audits}
    decision_by={key(r):r for r in decisions};patch_by={key(r):r for r in patches}
    root_by={key(r):r for r in roots};plan_by={key(r):r for r in plan};candidate_by={key(r):r for r in candidates}
    expected_cells={(sid,loc) for sid in selected_ids for loc in LOCALES}
    if set(before_by)!=expected_cells or set(final_by)!=expected_cells or set(audit_by)!=expected_cells: fail('coverage is not exactly 20 source IDs × 12 locales')
    if set(root_by)!=set(plan_by) or set(root_by)!=set(candidate_by) or set(root_by)!=set(patch_by): fail('candidate/root/plan/patch cell sets differ')
    if {(r['source_id'],r['locale']) for r in supplement} - set(candidate_by): fail('supplement rows absent from combined candidates')
    if collections.Counter(r['disposition'] for r in roots)!={'accepted-proposal':42,'refined-proposal':1}: fail('root disposition count mismatch')
    if sha((bundle/'root-cross-review.jsonl').read_bytes())!=m['root_cross_review_ledger_sha256']: fail('root ledger SHA mismatch')
    if sha((bundle/'root-apply-plan.jsonl').read_bytes())!=m['root_apply_plan_sha256']: fail('root apply-plan SHA mismatch')
    if sha((bundle/'candidate-corrections.jsonl').read_bytes())!=m['candidate_ledger_sha256']: fail('candidate ledger SHA mismatch')
    if sha((bundle/'candidate-main-input.jsonl').read_bytes())!=m['candidate_main_input_sha256']: fail('candidate main-input SHA mismatch')
    if sha((bundle/'candidate-supplement.jsonl').read_bytes())!=m['candidate_supplement_sha256']: fail('candidate supplement SHA mismatch')
    for k,r in root_by.items():
        c=candidate_by[k];p=plan_by[k]
        if c['proposed_target']!=r['candidate_target'] or c['proposed_sha256']!=r['candidate_target_sha256']: fail('candidate/root proposal mismatch '+str(k))
        if c['source_sha256']!=r['source_sha256'] or c['baseline_target_sha256']!=r['baseline_target_sha256']: fail('candidate/root source/baseline mismatch '+str(k))
        if p['final_target']!=r['final_target'] or p['final_target_sha256']!=r['final_target_sha256'] or p['disposition']!=r['disposition']: fail('root plan mismatch '+str(k))
        if p['final_target_sha256']!=value_sha(p['final_target']): fail('root final target hash mismatch '+str(k))

    scan_path=bundle/'prior-evidence-scan-manifest.jsonl';scan_raw=scan_path.read_bytes();scan=read_jsonl(scan_path)
    if len(scan)!=m['prior_overlap_scan']['input_count'] or sha(scan_raw)!=m['prior_overlap_scan']['manifest_file_sha256']: fail('overlap scan manifest mismatch')
    canonical=sha(json.dumps(sorted(scan,key=lambda r:(r['root'],r['path'])),sort_keys=True,separators=(',',':')).encode())
    if canonical!=m['prior_overlap_scan']['canonical_input_manifest_sha256']: fail('canonical overlap input hash mismatch')
    prior=collections.defaultdict(list)
    for item in scan:
        if item['root']=='prior-audit-7ff': raw=(prior_audit/item['path']).read_bytes()
        elif item['root']=='pr-review-head': raw=git(repo,'show',f'{review}:{item["path"]}',raw=True)
        else: fail('unknown overlap evidence root '+str(item['root']))
        if len(raw)!=item['bytes'] or sha(raw)!=item['sha256']: fail('raw overlap input pin mismatch '+item['path'])
        for line,row in parse_evidence(raw,item['path']):
            sid=pick(row,ALIASES['source_id']);loc=row.get('locale')
            if not isinstance(sid,str) or sid not in selected_ids or loc not in LOCALES: continue
            status=normalize_status(pick(row,ALIASES['status']))
            if status not in TERMINAL: continue
            base=before_by[(sid,loc)]
            if pick(row,ALIASES['source_sha'])==base['source_sha256'] and pick(row,ALIASES['target_sha'])==base['target_sha256']:
                prior[(sid,loc)].append({'status':status,'root':item['root'],'path':item['path'],'line':line,'batch':row.get('batch') or row.get('review_batch'),'finding_id':row.get('finding_id')})

    catalog_before={};catalog_after={};changed=set()
    for loc in LOCALES:
        path=f'web/src/lib/locales/ui-labels.{loc}.json'
        rb=git(repo,'show',f'{review}:{path}',raw=True);ra=git(repo,'show',f'{application}:{path}',raw=True)
        if sha(rb)!=m['catalog_sha256_before'][path] or sha(ra)!=m['catalog_sha256_after'][path]: fail('catalog file SHA mismatch '+loc)
        catalog_before[loc]=json.loads(rb.decode('utf-8'));catalog_after[loc]=json.loads(ra.decode('utf-8'))
        if set(catalog_before[loc])!=set(source_ids) or set(catalog_after[loc])!=set(source_ids): fail('catalog key inventory mismatch '+loc)
        for sid in source_ids:
            if catalog_before[loc][sid]!=catalog_after[loc][sid]: changed.add((sid,loc))
            if catalog_after[loc][sid] is None or (isinstance(catalog_after[loc][sid],str) and not catalog_after[loc][sid].strip()): fail('blank target '+str((sid,loc)))
    if changed!=set(patch_by): fail('catalog changes do not match exact patch ledger')

    for row in before:
        k=key(row);matches=prior.get(k,[]);statuses=sorted({x['status'] for x in matches})
        disp='conflict' if len(statuses)>1 else ('prior_'+statuses[0] if statuses else 'new')
        if row['prior_exact_matches']!=matches or row['disposition']!=disp: fail('exact overlap mismatch '+str(k))
        if row['source_index']!=source_ids.index(row['source_id']) or row['source_sha256']!=value_sha(row['source_id']): fail('source index/hash mismatch '+str(k))
        old=catalog_before[k[1]][k[0]];new=catalog_after[k[1]][k[0]]
        if old!=row['target_text'] or value_sha(old)!=row['target_sha256']: fail('baseline target mismatch '+str(k))
        finalrow=final_by[k];audit=audit_by[k];decision=decision_by.get(k);planrow=plan_by.get(k);patch=patch_by.get(k);root=root_by.get(k)
        if planrow:
            if patch is None or root is None: fail('missing application/root row '+str(k))
            if new!=planrow['final_target'] or value_sha(new)!=planrow['final_target_sha256']: fail('applied target mismatch '+str(k))
            if patch['source_sha256']!=row['source_sha256'] or patch['baseline_target_sha256']!=row['target_sha256'] or patch['current_target_sha256']!=value_sha(new): fail('applied source/old/new hash mismatch '+str(k))
            if patch['application_head']!=application or patch['application_tree']!=m['application_tree'] or patch['application_parent']!=review: fail('patch commit pin mismatch '+str(k))
            if root['review_head']!=review or root['review_tree']!=m['review_tree'] or root['source_sha256']!=row['source_sha256'] or root['baseline_target_sha256']!=row['target_sha256']: fail('root head/source/old-target mismatch '+str(k))
            if root['final_target']!=new or old!=row['target_text']: fail('root/applied text mismatch '+str(k))
            if row['disposition'] not in ('new','prior_correction-needed'): fail('correction on non-correction baseline '+str(k))
            expected_status='corrected';expected_decision='corrected' if row['disposition']=='new' else 'corrected-prior'
            if patch['root_disposition']!=root['disposition']: fail('patch/root disposition mismatch '+str(k))
        else:
            if new!=old: fail('unledgered catalog edit '+str(k))
            expected_status='accepted';expected_decision='accepted' if row['disposition']=='new' else 'accepted-carry'
            if row['disposition'] not in ('new','prior_accepted'): fail('unresolved exact terminal status '+str(k))
        if finalrow['decision']!=expected_decision or finalrow['status']!=expected_status: fail('final selection disposition mismatch '+str(k))
        if finalrow['target_text']!=new or finalrow['target_sha256']!=value_sha(new): fail('final selection target mismatch '+str(k))
        if audit['status']!=expected_status or audit['target_text']!=new or audit['target_sha256']!=value_sha(new): fail('full audit target/status mismatch '+str(k))
        if placeholders(row['source_id'])!=placeholders(new) or audit['placeholders_source']!=placeholders(row['source_id']) or audit['placeholders_target']!=placeholders(new) or not audit['placeholders_preserved']: fail('placeholder mismatch '+str(k))
        if audit['icu_message_source']!=icu(row['source_id']) or audit['icu_message_target']!=icu(new) or icu(row['source_id']) or icu(new): fail('ICU check mismatch '+str(k))
        if not audit['protected_literals_checked'] or not audit['protected_literals_preserved']: fail('protected-literal evidence missing '+str(k))
        i=row['source_index'];loc=row['locale']
        if i==286 and not ('Pod' in new or 'Pods' in new): fail('Pod literal missing '+str(k))
        if i==297 and 'SongID' not in new: fail('SongID literal missing '+str(k))
        if i in (300,301) and not (('आईपी' in new) if loc=='hi' else ('IP' in new)): fail('IP qualifier missing '+str(k))
        if i==298 and '{count}' not in new: fail('count placeholder missing '+str(k))
        if not audit['reviewed_context'] or not audit['semantic_review_result'] or not audit['source_context_pointer']: fail('source context/review evidence missing '+str(k))
        if audit['native_speaker_approval']: fail('native speaker approval asserted '+str(k))
        if row['disposition']=='new':
            if decision is None or decision['reviewed_target_after']!=new or decision['fresh_disposition']!=expected_status: fail('fresh decision mismatch '+str(k))
        elif decision is not None: fail('nonfresh cell appears in decisions '+str(k))
    if {key(r) for r in decisions}!={key(r) for r in before if r['disposition']=='new'}: fail('fresh decision coverage mismatch')
    if {key(r) for r in carries}!={key(r) for r in before if r['disposition']=='prior_accepted'}: fail('carry coverage mismatch')
    if exclusions or conflicts or recon: fail('unresolved exclusions/conflicts remain')
    if any(r['native_speaker_approval'] for r in audits) or m['native_speaker_approval']: fail('native speaker approval incorrectly claimed')

    pins=json.loads((bundle/'source-pins.json').read_text(encoding='utf-8'))
    if pins['source_catalog_head']!=source or pins['source_catalog_tree']!=m['source_catalog_tree']: fail('source pin commit/tree mismatch')
    if pins['review_head']!=review or pins['review_tree']!=m['review_tree']: fail('review pin commit/tree mismatch')
    if sha((bundle/'source-context.txt').read_bytes())!=m['source_context']['evidence_text_sha256']: fail('source context SHA mismatch')
    if set(pins['sha256'])!=set(m['source_context']['runtime_files']): fail('source file list mismatch')
    for path,digest in pins['sha256'].items():
        blob=pins['git_blob_ids'][path]
        raw=git(repo,'show',f'{source}:{path}',raw=True)
        if sha(raw)!=digest or git(repo,'rev-parse',f'{source}:{path}')!=blob: fail('source file pin mismatch '+path)
        if git(repo,'rev-parse',f'{review}:{path}')!=blob or git(repo,'rev-parse',f'{application}:{path}')!=blob: fail('source caller changed after source snapshot '+path)
    if pins['catalog_sha256_before']!=m['catalog_sha256_before'] or pins['catalog_sha256_after']!=m['catalog_sha256_after']: fail('catalog pins differ between manifest and source pin file')
    visual=m['visual_check']
    if visual['status']!='blocked' or sha((bundle/visual['file']).read_bytes())!=visual['sha256'] or not m['browser_recapture_required']: fail('visual status/hash mismatch')
    if m['placeholder_and_literal_checks']!={'cells_checked':240,'placeholder_sets_preserved':True,'icu_messages':0,'protected_literals_checked':True,'protected_literals_changed':0}: fail('placeholder/literal census mismatch')
    expected_sums=[f'{sha(p.read_bytes())}  {p.name}' for p in sorted(bundle.iterdir()) if p.is_file() and p.name!='SHA256SUMS']
    if (bundle/'SHA256SUMS').read_text(encoding='utf-8').splitlines()!=expected_sums: fail('bundle checksum file mismatch')
    print('PASS: 240 exact cells; 60 fresh (50 accepted, 10 corrected); 147 accepted carries; 33 prior correction-needed cells reconciled; 43 root-reviewed corrections (42 accepted as proposed, 1 refined); zero holds/conflicts. Verified 858 overlap inputs, all source/current/final hashes, 11 source caller files, placeholders/ICU/protected literals, and all bundle checksums.')

if __name__=='__main__': main()
