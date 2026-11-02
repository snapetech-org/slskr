#!/usr/bin/env python3
"""Verify the exact 343–362 all-locale semantic review and two catalog applications."""
import argparse, collections, hashlib, json, re, subprocess
from pathlib import Path
LOCALES=['ar','de','es','fr','hi','id','ja','ko','pt-BR','vi','zh-Hans','zh-Hant']
TERMINAL={'accepted','correction-needed','held','keep','corrected'}
ALIASES={'source_id':['source_id','sourceId','message_id','id'],'source_sha':['source_sha256','sourceSha256'],'target_sha':['target_sha256','current_target_sha256','reviewed_target_after_sha256','final_target_sha256','target_after_sha256','targetSha256','currentTargetSha256','reviewedTargetAfterSha256','finalTargetSha256'],'status':['status','review_outcome']}
def fail(msg): raise SystemExit('FAIL: '+msg)
def sha(raw): return hashlib.sha256(raw).hexdigest()
def vsha(v): return sha(v.encode('utf-8') if isinstance(v,str) else json.dumps(v,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode())
def readj(p): return json.loads(Path(p).read_text(encoding='utf-8'))
def readl(p): return [json.loads(x) for x in Path(p).read_text(encoding='utf-8').splitlines() if x.strip()]
def git(repo,*args,raw=False):
 b=subprocess.check_output(['git',*args],cwd=repo);return b if raw else b.decode().strip()
def pick(row,names):
 for n in names:
  if row.get(n) is not None:return row[n]
def norm(v):return str(v or '').strip().lower().replace('_','-')
def placeholders(v):return sorted(set(re.findall(r'\{([^{}]+)\}',str(v))))
def icu(v):return bool(re.search(r'\{\s*[A-Za-z_][\w.-]*\s*,\s*(plural|select|selectordinal)\s*,',str(v)))
def nonempty(v):
 if isinstance(v,str):return bool(v.strip())
 if isinstance(v,dict):return bool(v) and all(nonempty(x) for x in v.values())
 if isinstance(v,list):return bool(v) and all(nonempty(x) for x in v)
 return False
def walk(x):
 if isinstance(x,dict):
  yield x
  for v in x.values():yield from walk(v)
 elif isinstance(x,list):
  for v in x:yield from walk(v)
def parse(raw,path):
 if Path(path).suffix=='.jsonl':
  for n,line in enumerate(raw.decode().splitlines(),1):
   if line.strip():
    try:yield n,json.loads(line)
    except json.JSONDecodeError:continue
 elif Path(path).suffix=='.json':
  try:yield from enumerate(walk(json.loads(raw.decode())),1)
  except json.JSONDecodeError:return
def key(r):return (r.get('source_id',r.get('sourceId')),r['locale'])
def unique(rows,label):
 keys=[key(r) for r in rows]
 if len(set(keys))!=len(rows):fail('duplicate key in '+label)
 return {key(r):r for r in rows}
def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--repo',type=Path,required=True);ap.add_argument('--prior-audit',type=Path,required=True);a=ap.parse_args();repo=a.repo.resolve();audit=a.prior_audit.resolve();bundle=Path(__file__).resolve().parent;m=readj(bundle/'manifest.json')
 review=m['review_head'];app1,app2=m['application_heads'];source=m['source_catalog_head'];rt=m['review_tree'];t1=m['application_commits'][0]['tree'];t2=m['application_tree'];st=m['source_catalog_tree']
 for c,t in ((review,rt),(app1,t1),(app2,t2),(source,st)):
  if git(repo,'rev-parse',f'{c}^{{tree}}')!=t:fail('commit/tree pin mismatch '+c)
 if git(repo,'rev-parse',f'{app1}^')!=review or git(repo,'rev-parse',f'{app2}^')!=app1:fail('catalog application chain mismatch')
 if m['application_commits']!=[{'head':app1,'tree':t1,'parent':review,'changed_cells':16},{'head':app2,'tree':t2,'parent':app1,'changed_cells':6}]:fail('application chain manifest mismatch')
 # Frozen ordered source inventory and contiguous selection.
 inv=(bundle/'source-inventory.jsonl').read_bytes()
 if sha(inv)!=m['source_inventory']['sha256'] or sha((audit/'frozen-inputs/source-inventory.jsonl').read_bytes())!=sha(inv):fail('source inventory hash mismatch')
 ids=[json.loads(x)['source_id'] for x in inv.decode().splitlines() if x.strip()]
 if len(ids)!=5437 or ids!=sorted(ids):fail('source inventory order/count mismatch')
 start,end=m['source_index_range'];selected=ids[start:end+1]
 if (start,end)!=(343,362) or len(selected)!=20:fail('window range mismatch')
 inventory=set(ids)
 # All exact review and application evidence ledgers.
 before=readl(bundle/'selection-before-corrections.jsonl');final=readl(bundle/'selection.jsonl');audit_rows=readl(bundle/'reviewed-cell-audit.jsonl');fresh=readl(bundle/'decisions.jsonl');freshfix=readl(bundle/'fresh-correction-decisions.jsonl');carries=readl(bundle/'carries.jsonl');cand16=readl(bundle/'candidate-corrections.jsonl');cand6=readl(bundle/'candidate-supplement-artist-release-radar-six.jsonl');auditcand=readl(bundle/'candidate-cell-audit.jsonl');root16=readl(bundle/'root-cross-review.jsonl');plan16=readl(bundle/'root-apply-plan.jsonl');root6=readl(bundle/'root-radar-supplement-decisions.jsonl');plan6=readl(bundle/'root-apply-plan-radar-supplement.jsonl');patches=readl(bundle/'applied-corrections.jsonl');patch6=readl(bundle/'applied-radar-supplement.jsonl')
 if tuple(map(len,(before,final,audit_rows,fresh,freshfix,carries,cand16,cand6,auditcand,root16,plan16,root6,plan6,patches,patch6)))!=(240,240,240,30,6,188,16,6,22,16,16,6,6,22,6):fail('evidence row count mismatch')
 bm=unique(before,'baseline selection');fm=unique(final,'final selection');am=unique(audit_rows,'cell audit');dm=unique(fresh,'fresh decisions');dfm=unique(freshfix,'fresh corrections');cm=unique(carries,'accepted carries');c16m=unique(cand16,'candidate set');c6m=unique(cand6,'candidate supplement');aam=unique(auditcand,'candidate audit');r16m=unique(root16,'root review');p16m=unique(plan16,'apply plan');r6m={(r['source'],r['locale']):r for r in root6};p6m={(r['source_id'],r['locale']):r for r in plan6};patchm=unique(patches,'applied correction ledger');patch6m={(r['source_id'],r['locale']):r for r in patch6}
 cells={(sid,l) for sid in selected for l in LOCALES}
 if set(bm)!=cells or set(fm)!=cells or set(am)!=cells:fail('not exactly 20 IDs × 12 locales')
 k16=set(c16m);k6=set(c6m);allk=k16|k6
 if k16&k6 or len(allk)!=22 or set(r16m)!=k16 or set(p16m)!=k16 or set(r6m)!=k6 or set(p6m)!=k6 or set(patch6m)!=k6 or set(patchm)!=allk or set(aam)!=allk:fail('candidate/review/plan/apply coverage mismatch')
 # Rehash all previously reviewed evidence inputs to reconstruct exact overlap dispositions.
 scan=readl(bundle/'prior-evidence-scan-manifest.jsonl')
 if len(scan)!=m['prior_evidence']['input_count'] or sha((bundle/'prior-evidence-scan-manifest.jsonl').read_bytes())!=m['prior_evidence']['manifest_sha256']:fail('prior evidence input manifest mismatch')
 prior=collections.defaultdict(list)
 for item in scan:
  if item['root']=='prior-audit-7ff':raw=(audit/item['path']).read_bytes()
  elif item['root']=='pr-review-head':raw=git(repo,'show',f"{review}:{item['path']}",raw=True)
  else:fail('unknown prior evidence root')
  if len(raw)!=item['bytes'] or sha(raw)!=item['sha256']:fail('prior evidence hash mismatch '+item['path'])
  for line,row in parse(raw,item['path']):
   sid=pick(row,ALIASES['source_id']);loc=row.get('locale')
   if not isinstance(sid,str) or sid not in inventory or loc not in LOCALES:continue
   status=norm(pick(row,ALIASES['status']))
   if status not in TERMINAL:continue
   rec={'status':status,'root':item['root'],'path':item['path'],'line':line,'batch':row.get('batch') or row.get('review_batch'),'finding_id':row.get('finding_id')}
   if sid in selected and pick(row,ALIASES['source_sha'])==bm[(sid,loc)]['source_sha256'] and pick(row,ALIASES['target_sha'])==bm[(sid,loc)]['target_sha256']:prior[(sid,loc)].append(rec)
 # Verify exact catalog hashes, source inventories, and every changed cell across both application commits.
 oldcats={};newcats={};changed=set()
 for loc in LOCALES:
  path=f'web/src/lib/locales/ui-labels.{loc}.json';oldraw=git(repo,'show',f'{review}:{path}',raw=True);newraw=git(repo,'show',f'{app2}:{path}',raw=True)
  if sha(oldraw)!=m['catalog_hashes_before'][loc] or sha(newraw)!=m['catalog_hashes_after'][loc]:fail('catalog file hash mismatch '+loc)
  old=json.loads(oldraw);new=json.loads(newraw)
  if set(old)!=inventory or set(new)!=inventory:fail('catalog/source ID inventory mismatch '+loc)
  if any(not nonempty(v) for v in new.values()):fail('blank catalog value '+loc)
  if loc!='ar' and any(not isinstance(v,str) for v in new.values()):fail('structured non-Arabic catalog value '+loc)
  if loc=='ar' and sum(isinstance(v,(dict,list)) for v in new.values())!=15:fail('Arabic structured value count mismatch')
  oldcats[loc]=old;newcats[loc]=new;changed.update((sid,loc) for sid in ids if old[sid]!=new[sid])
 if changed!=allk:fail('changed catalog cells differ from the exact 22 reviewed operations')
 expected_paths={f'web/src/lib/locales/ui-labels.{loc}.json' for _,loc in allk}
 paths=set(git(repo,'diff','--name-only',f'{review}..{app2}').splitlines())
 if paths!=expected_paths:fail('changed file scope mismatch '+repr(paths^expected_paths))
 subprocess.check_call(['git','diff','--check',f'{review}..{app2}'],cwd=repo)
 # Original 16-row root packet is checksummed independently.
 root_sums={line.split()[1]:line.split()[0] for line in (bundle/'root-packet-SHA256SUMS.txt').read_text().splitlines() if line.strip()}
 for name,path in [('root-decisions.jsonl',bundle/'root-cross-review.jsonl'),('root-apply-plan.jsonl',bundle/'root-apply-plan.jsonl'),('summary.json',bundle/'root-cross-review-summary.json')]:
  if sha(path.read_bytes())!=root_sums.get(name):fail('original root packet checksum mismatch '+name)
 if sha((bundle/'candidate-corrections.jsonl').read_bytes())!='16206067e6b33036642e4e510226c8873efeb65d308feedb6c35e11facaa9263':fail('original candidate packet changed')
 if collections.Counter(r['root_disposition'] for r in root16)!=collections.Counter({'accepted':14,'refined':2}):fail('original root review decisions mismatch')
 # Supplement root packet and the post-push exact revalidation gate.
 rmeta=readj(bundle/'root-radar-supplement-checksums.json');rsummary=readj(bundle/'root-radar-supplement-summary.json');reval=readj(bundle/'post-pending-16-cell-revalidation.json')
 if sha((bundle/'candidate-supplement-artist-release-radar-six.jsonl').read_bytes())!='43d4c00728a4b0f82d462c90dee599521c20157e1b5df6412649c8132cf1833e' or rmeta['candidate_file_sha256']!=sha((bundle/'candidate-supplement-artist-release-radar-six.jsonl').read_bytes()):fail('six-cell candidate supplement hash mismatch')
 if sha((bundle/'root-radar-supplement-decisions.jsonl').read_bytes())!='d6addee4fbae79b2297d8c0ae905441f9e7ffad6cd04854bf65da3503bca8f77' or rmeta['root_decisions_sha256']!=sha((bundle/'root-radar-supplement-decisions.jsonl').read_bytes()):fail('six-cell root decision hash mismatch')
 if sha((bundle/'root-radar-supplement-summary.json').read_bytes())!='f2469cdc2720820af3be5f4dbe1bda19172341fa748c3696265d30598925e58f' or rmeta['root_summary_sha256']!=sha((bundle/'root-radar-supplement-summary.json').read_bytes()):fail('six-cell root summary hash mismatch')
 if rsummary['liveHead']!=review or rsummary['liveTree']!=rt or rsummary['candidateSupplementSha256']!=sha((bundle/'candidate-supplement-artist-release-radar-six.jsonl').read_bytes()) or rsummary['accepted']!=6 or rsummary['refined'] or rsummary['held']:fail('supplement cross-review summary mismatch')
 if reval['remote_branch_head']!=app1 or reval['live_pr']['headRefOid']!=app1 or reval['live_pr']['state']!='OPEN' or reval['live_pr']['isDraft'] is not True or not all(c['match'] for c in reval['cell_checks']):fail('post-push live exact-target gate mismatch')
 if rmeta['root_decisions_sha256']!=m['root_supplement']['review_sha256'] or rmeta['root_summary_sha256']!=m['root_supplement']['summary_sha256']:fail('manifest/supplement root hashes differ')
 if collections.Counter(r['rootDisposition'] for r in root6)!=collections.Counter({'accept':6}) or any(r['reviewedPrHead']!=review or r['reviewedPrTree']!=rt or r['reviewedSourceHead']!=source or r['reviewedSourceTree']!=st for r in root6):fail('six root dispositions/pins mismatch')
 # Verify source context and each of the 240 exact overlap/application outcomes.
 allpatch={**patchm};
 for k in allk:
  p=patchm[k]
  if k in k6 and p['status']!='corrected':fail('supplement patch status mismatch '+str(k))
 for k,b in bm.items():
  sid,loc=k;old=oldcats[loc][sid];new=newcats[loc][sid];matches=prior.get(k,[]);statuses=sorted({r['status'] for r in matches});disp='conflict' if len(statuses)>1 else ('prior_'+statuses[0] if statuses else 'new')
  if b['source_index']!=ids.index(sid) or b['source_sha256']!=vsha(sid) or b['target_text']!=old or b['target_sha256']!=vsha(old):fail('baseline source/target mismatch '+str(k))
  if b['prior_exact_matches']!=matches or b['disposition']!=disp:fail('exact prior overlap mismatch '+str(k))
  ar=am[k];f=fm[k];p=patchm.get(k);root=rootm=None;candidate=None
  if k in k16:
   root=r16m[k];plan=p16m[k];candidate=c16m[k];expected_commit=app1;expected_before=review
   if plan['review_head']!=review or plan['review_tree']!=rt or plan['apply'] is not True:fail('original plan pin mismatch '+str(k))
   if root['review_head']!=review or root['review_tree']!=rt or root['source_catalog_head']!=source or root['source_catalog_tree']!=st:fail('original root/source pin mismatch '+str(k))
   proposed=candidate['proposed_target'];proposedsha=candidate['proposed_sha256'];rootvalue=root['root_target'];rootsha=root['root_target_sha256']
   if candidate['baseline_target_text']!=old or candidate['baseline_target_sha256']!=vsha(old) or candidate['source_sha256']!=vsha(sid) or candidate['proposed_sha256']!=vsha(proposed):fail('original candidate exact hashes mismatch '+str(k))
   if root['candidate_target']!=proposed or root['candidate_target_sha256']!=proposedsha:fail('original root proposal mismatch '+str(k))
   if plan['baseline_target_text']!=old or plan['root_target']!=new or rootvalue!=new or plan['root_target_sha256']!=vsha(new):fail('original root apply target mismatch '+str(k))
   pp=patchm[k]
   if pp['catalog_before_sha256']!=m['catalog_hashes_before'][loc] or pp['catalog_after_sha256']!=sha(git(repo,'show',f'{app1}:web/src/lib/locales/ui-labels.{loc}.json',raw=True)):fail('original patch file hash mismatch '+str(k))
  elif k in k6:
   root=r6m[k];plan=p6m[k];candidate=c6m[k];expected_commit=app2;expected_before=app1
   if root['reviewedPrHead']!=review or root['reviewedPrTree']!=rt or root['reviewedSourceHead']!=source or root['reviewedSourceTree']!=st:fail('supplement root/source pin mismatch '+str(k))
   if candidate['current_target_text']!=old or candidate['current_target_sha256']!=vsha(old) or candidate['source_sha256']!=vsha(sid) or candidate['proposed_sha256']!=vsha(candidate['proposed_target']):fail('supplement candidate exact hash mismatch '+str(k))
   if root['currentTargetAtLiveHead']!=old or root['currentTargetSha256AtLiveHead']!=vsha(old) or root['proposedTarget']!=candidate['proposed_target'] or root['proposedTargetSha256']!=candidate['proposed_sha256']:fail('supplement root candidate mismatch '+str(k))
   if plan['apply_base_head']!=app1 or plan['apply_base_tree']!=t1 or plan['root_review_head']!=review or plan['root_disposition']!='accepted' or plan['baseline_target_text']!=old or plan['root_target']!=new:fail('supplement apply plan mismatch '+str(k))
   pp=patch6m[k]
   if pp['catalog_before_sha256']!=sha(git(repo,'show',f'{app1}:web/src/lib/locales/ui-labels.{loc}.json',raw=True)) or pp['catalog_after_sha256']!=m['catalog_hashes_after'][loc]:fail('supplement patch file hash mismatch '+str(k))
  else:
   if old!=new:fail('unplanned catalog change '+str(k))
  if k in allk:
   expected='corrected';decision='corrected'
   if pp['baseline_target_text']!=old or pp['baseline_target_sha256']!=vsha(old) or pp['root_target']!=new or pp['target_text']!=new or pp['target_sha256']!=vsha(new) or pp['status']!='corrected':fail('applied correction exact target mismatch '+str(k))
  else:
   expected='accepted';decision='accepted' if disp=='new' else 'accepted-carry'
   if disp not in ('new','prior_accepted'):fail('unresolved prior conflict/hold '+str(k))
  if f['target_text']!=new or f['target_sha256']!=vsha(new) or f['disposition']!=expected:fail('final selection mismatch '+str(k))
  if ar['baseline_target_text']!=old or ar['baseline_target_sha256']!=vsha(old) or ar['reviewed_target_after']!=new or ar['reviewed_target_after_sha256']!=vsha(new) or ar['status']!=expected or ar['decision']!=decision:fail('cell audit target/status mismatch '+str(k))
  if ar['prior_exact_matches']!=matches or ar['source_sha256']!=vsha(sid):fail('cell audit overlap/source mismatch '+str(k))
  if placeholders(sid)!=placeholders(new) or not ar['placeholders_preserved'] or ar['placeholders_target']!=placeholders(new):fail('placeholder mismatch '+str(k))
  if icu(sid) or icu(new) or ar['icu_message_source'] or ar['icu_message_target']:fail('unexpected ICU syntax '+str(k))
  for token in ('ContentID','MusicBrainz','ID'):
   if token in sid and token not in new:fail('protected literal lost '+str((k,token)))
  if not ar['protected_literals_checked'] or not ar['protected_literals_final_preserved'] or ar['native_speaker_approval'] is not False:fail('protected/native assertion mismatch '+str(k))
  if k in dm and (dm[k]['status']!='accepted' or dm[k]['target_text']!=new):fail('fresh accept decision mismatch '+str(k))
  if k in dfm and (dfm[k]['status']!='corrected' or dfm[k]['target_text']!=new):fail('fresh correction decision mismatch '+str(k))
  if k in cm and (cm[k]['status']!='accepted' or cm[k]['target_text']!=new):fail('accepted carry mismatch '+str(k))
 if collections.Counter(r['status'] for r in fresh)!=collections.Counter({'accepted':30}) or collections.Counter(r['status'] for r in freshfix)!=collections.Counter({'corrected':6}) or collections.Counter(r['status'] for r in carries)!=collections.Counter({'accepted':188}):fail('fresh/carry status counts mismatch')
 if collections.Counter(r['disposition'] for r in final)!=collections.Counter({'accepted':218,'corrected':22}):fail('final selection counts mismatch')
 # Rehash caller files at source, review, both applications; source context and visual blocker remain explicit.
 pins=readj(bundle/'source-pins.json')
 if pins['review_head']!=review or pins['review_tree']!=rt or pins['application_head']!=app2 or pins['application_tree']!=t2 or pins['source_commit']!=source or pins['source_tree']!=st or len(pins['files'])!=18:fail('source pin header mismatch')
 for path,x in pins['files'].items():
  raw=git(repo,'show',f'{source}:{path}',raw=True)
  if len(raw)!=x['bytes'] or sha(raw)!=x['sha256'] or git(repo,'rev-parse',f'{source}:{path}')!=x['git_blob'] or git(repo,'rev-parse',f'{review}:{path}')!=x['git_blob'] or git(repo,'rev-parse',f'{app1}:{path}')!=x['git_blob'] or git(repo,'rev-parse',f'{app2}:{path}')!=x['git_blob']:fail('source caller blob mismatch '+path)
 if sha((bundle/'source-context.txt').read_bytes())!=m['source_context']['sha256']:fail('source context hash mismatch')
 if m['native_speaker_approval'] is not False or m['tests_builds_ci_workflows_releases_or_tags_run'] is not False or m['headed_visual_review']['status']!='blocked':fail('unsupported review/build/visual assertion')
 if m['verifier_sha256']!=sha(Path(__file__).read_bytes()):fail('verifier self-hash mismatch')
 sums=[f'{sha(p.read_bytes())}  {p.name}' for p in sorted(bundle.iterdir()) if p.is_file() and p.name!='SHA256SUMS']
 if (bundle/'SHA256SUMS').read_text().splitlines()!=sums:fail('bundle checksum mismatch')
 print('PASS: exact source/review/two-application commits; 240 cells, 36 fresh (30 accepted/6 corrected), 188 carries, 22 applied corrections (20 root accepted/2 refined); 916 exact prior evidence inputs; 18 caller pins; all root packets, catalog hashes, paths, overlaps, placeholders, protected literals, ICU and bundle checksums verified. Native-speaker approval false; visual review blocked as recorded.')
if __name__=='__main__':main()
