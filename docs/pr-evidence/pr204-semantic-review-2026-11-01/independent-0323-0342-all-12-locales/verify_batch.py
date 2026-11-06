#!/usr/bin/env python3
"""Verify the 323–342 all-locale audit, exact prior overlap, review, and application."""
import argparse, collections, hashlib, json, re, subprocess
from pathlib import Path
LOCALES=['ar','de','es','fr','hi','id','ja','ko','pt-BR','vi','zh-Hans','zh-Hant']
TERMINAL={'accepted','correction-needed','held','keep','corrected'}
ALIASES={'source_id':['source_id','sourceId','message_id','id'],'source_sha':['source_sha256','sourceSha256'],'target_sha':['target_sha256','current_target_sha256'],'status':['status','review_outcome','disposition']}
def fail(m): raise SystemExit('FAIL: '+m)
def sha(raw): return hashlib.sha256(raw).hexdigest()
def vsha(v): return sha(v.encode('utf-8') if isinstance(v,str) else json.dumps(v,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode())
def readj(path): return json.loads(Path(path).read_text(encoding='utf-8'))
def readl(path): return [json.loads(x) for x in Path(path).read_text(encoding='utf-8').splitlines() if x.strip()]
def git(repo,*args,raw=False):
 b=subprocess.check_output(['git',*args],cwd=repo)
 return b if raw else b.decode().strip()
def pick(row,names):
 for n in names:
  if row.get(n) is not None:return row[n]
def norm(v): return str(v or '').strip().lower().replace('_','-')
def placeholders(v): return sorted(set(re.findall(r'\{([^{}]+)\}',str(v))))
def icu(v): return bool(re.search(r'\{\s*[A-Za-z_][\w.-]*\s*,\s*(plural|select|selectordinal)\s*,',str(v)))
def nonempty(v):
 if isinstance(v,str): return bool(v.strip())
 if isinstance(v,dict): return bool(v) and all(nonempty(x) for x in v.values())
 if isinstance(v,list): return bool(v) and all(nonempty(x) for x in v)
 return False
def walk(x):
 if isinstance(x,dict):
  yield x
  for v in x.values(): yield from walk(v)
 elif isinstance(x,list):
  for v in x: yield from walk(v)
def parse(raw,path):
 if Path(path).suffix=='.jsonl':
  for n,line in enumerate(raw.decode().splitlines(),1):
   if line.strip():
    try: yield n,json.loads(line)
    except json.JSONDecodeError: continue
 elif Path(path).suffix=='.json':
  try: yield from enumerate(walk(json.loads(raw.decode())),1)
  except json.JSONDecodeError: return
def key(r): return (r.get('source_id',r.get('sourceId')),r['locale'])
def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--repo',type=Path,required=True);ap.add_argument('--prior-audit',type=Path,required=True);a=ap.parse_args()
 repo=a.repo.resolve();audit=a.prior_audit.resolve();bundle=Path(__file__).resolve().parent;m=readj(bundle/'manifest.json')
 review=m['review_head'];app=m['application_head'];source=m['source_catalog_head'];tree=m['application_tree']
 for c,t in ((review,m['review_tree']),(app,tree),(source,m['source_catalog_tree'])):
  if git(repo,'rev-parse',f'{c}^{{tree}}')!=t:fail('commit/tree pin mismatch '+c)
 if git(repo,'rev-parse',f'{app}^')!=review or m['application_parent']!=review:fail('application is not a direct child of exact review head')
 paths={f'web/src/lib/locales/ui-labels.{l}.json' for l in LOCALES}
 changed_paths=set(git(repo,'diff','--name-only',f'{review}..{app}').splitlines())
 if changed_paths!=paths:fail('application diff is not limited to all 12 locale catalog files')
 git(repo,'diff','--check',f'{review}..{app}')
 inv_raw=(audit/'frozen-inputs/source-inventory.jsonl').read_bytes()
 if sha(inv_raw)!=m['source_inventory_sha256']:fail('source inventory hash mismatch')
 ids=[json.loads(x)['source_id'] for x in inv_raw.decode().splitlines() if x.strip()]
 if len(ids)!=5437 or ids!=sorted(ids):fail('source inventory order/count mismatch')
 start,end=m['source_index_range'];selected=ids[start:end+1]
 if (start,end)!=(323,342) or len(selected)!=20:fail('unexpected source window')
 invset=set(ids)
 before=readl(bundle/'selection-before-corrections.jsonl');final=readl(bundle/'selection.jsonl');audit_rows=readl(bundle/'reviewed-cell-audit.jsonl');decisions=readl(bundle/'decisions.jsonl');carries=readl(bundle/'carries.jsonl');unchanged=readl(bundle/'accepted-unchanged.jsonl')
 candidates=readl(bundle/'candidate-corrections.jsonl');roots=readl(bundle/'root-cross-review.jsonl');plan=readl(bundle/'root-apply-plan.jsonl');patches=readl(bundle/'applied-corrections.jsonl')
 gctx=readl(bundle/'korean-discovery-inbox-group-context-48.jsonl');gcand=readl(bundle/'korean-discovery-inbox-group-candidates.jsonl');gpatch=readl(bundle/'korean-discovery-inbox-group-applied.jsonl')
 counts=(len(before),len(final),len(audit_rows),len(decisions),len(carries),len(unchanged),len(candidates),len(roots),len(plan),len(patches),len(gctx),len(gcand),len(gpatch))
 if counts!=(240,240,240,67,128,2,46,49,47,47,48,4,4):fail('evidence row count mismatch '+repr(counts))
 for filename,expected in [('candidate-corrections.jsonl','21a0c0ca2e0025ef42475b8341c4cc375f7acfe91bb1d86c9602f9c575baf2f6'),('korean-discovery-inbox-group-candidates.jsonl','f4948754f552e395073cab20e6ec32bc6809ebf836a5a62bc50c7cc3d33186c4'),('root-cross-review.jsonl','78fd9eb826f104ed50a38b561d4f210e09091cbad6e691eab8dc55c49760f8ae'),('root-apply-plan.jsonl','f8f5bef17279617f80d21257216cf29e7b3e83c9ffd01d5d3435e43e3610e0da'),('korean-discovery-inbox-group-context-48.jsonl','3f019a82e0a6ff60912cf94cb70923c6c880c0934510e33fbf622bedeef1252a')]:
  if sha((bundle/filename).read_bytes())!=expected:fail('pinned audit input changed '+filename)
 for rows,label in ((before,'baseline'),(final,'final'),(audit_rows,'review audit'),(decisions,'fresh decisions'),(carries,'carries'),(candidates,'candidates'),(roots,'root reviews'),(plan,'plan'),(patches,'patches')):
  if len({key(r) for r in rows})!=len(rows):fail('duplicate rows in '+label)
 bmap={key(r):r for r in before};fmap={key(r):r for r in final};amap={key(r):r for r in audit_rows};dmap={key(r):r for r in decisions};cmap={key(r):r for r in carries};candmap={key(r):r for r in candidates};rmap={(r['sourceId'],r['locale']):r for r in roots};pmap={(r['sourceId'],r['locale']):r for r in plan};patchmap={key(r):r for r in patches}
 cells={(sid,l) for sid in selected for l in LOCALES}
 if set(bmap)!=cells or set(fmap)!=cells or set(amap)!=cells:fail('window does not cover 20 IDs × 12 locales')
 # Verify prior exact terminal records against the pinned raw inputs.
 scan_path=bundle/'prior-evidence-scan-manifest.jsonl';scan_raw=scan_path.read_bytes();scan=readl(scan_path)
 if len(scan)!=892 or sha(scan_raw)!=m['prior_evidence']['manifest_sha256']:fail('prior overlap input manifest mismatch')
 if sha(json.dumps(sorted(scan,key=lambda r:(r['root'],r['path'])),sort_keys=True,separators=(',',':')).encode())!=m['prior_evidence']['canonical_input_manifest_sha256'] if 'canonical_input_manifest_sha256' in m['prior_evidence'] else False: fail('canonical prior scan manifest mismatch')
 prior=collections.defaultdict(list);allprior=collections.defaultdict(list)
 for item in scan:
  if item['root']=='prior-audit-7ff':raw=(audit/item['path']).read_bytes()
  elif item['root']=='pr-review-head':raw=git(repo,'show',f"{review}:{item['path']}",raw=True)
  else:fail('unknown prior scan root')
  if len(raw)!=item['bytes'] or sha(raw)!=item['sha256']:fail('prior evidence file hash mismatch '+item['path'])
  for line,row in parse(raw,item['path']):
   sid=pick(row,ALIASES['source_id']);loc=row.get('locale')
   if not isinstance(sid,str) or sid not in invset or loc not in LOCALES:continue
   st=norm(pick(row,ALIASES['status']))
   if st not in TERMINAL:continue
   record={'status':st,'root':item['root'],'path':item['path'],'line':line,'batch':row.get('batch') or row.get('review_batch'),'finding_id':row.get('finding_id')}
   srcsha=pick(row,ALIASES['source_sha']);targetsha=pick(row,ALIASES['target_sha'])
   allprior[(sid,loc,srcsha,targetsha)].append(record)
   if sid in selected:
    b=bmap[(sid,loc)]
    if srcsha==b['source_sha256'] and targetsha==b['target_sha256']:prior[(sid,loc)].append(record)
 catbefore={};catafter={};diffcells=set();invset=set(ids)
 for loc in LOCALES:
  p=f'web/src/lib/locales/ui-labels.{loc}.json';rb=git(repo,'show',f'{review}:{p}',raw=True);ra=git(repo,'show',f'{app}:{p}',raw=True)
  if sha(rb)!=m['catalog_sha256_before'][p] or sha(ra)!=m['catalog_sha256_after'][p]:fail('catalog hash mismatch '+loc)
  cb=json.loads(rb);ca=json.loads(ra)
  if set(cb)!=invset or set(ca)!=invset:fail('catalog/source key inventory mismatch '+loc)
  if any(not nonempty(v) for v in ca.values()):fail('blank catalog target '+loc)
  if loc!='ar' and any(not isinstance(v,str) for v in ca.values()):fail('unexpected structured catalog target '+loc)
  if loc=='ar' and sum(isinstance(v,(dict,list)) for v in ca.values())!=15:fail('unexpected Arabic plural inventory')
  catbefore[loc]=cb;catafter[loc]=ca
  for sid in ids:
   if cb[sid]!=ca[sid]:diffcells.add((sid,loc))
 if diffcells!=set(pmap) or set(pmap)!=set(patchmap):fail('catalog diff cells do not exactly match root apply/patch ledger')
 if collections.Counter(r['disposition'] for r in roots)!=collections.Counter({'accepted':41,'refined':6,'accepted-unchanged':2}):fail('root cross-review disposition counts mismatch')
 if any(r.get('nativeSpeakerReview')!='not_provided' for r in roots):fail('native-speaker signoff falsely claimed')
 if len(set(pmap)&set(candmap))!=44:fail('window candidate apply count mismatch')
 for b in before:
  k=key(b);sid,loc=k;matches=prior.get(k,[]);statuses=sorted({x['status'] for x in matches});disp='conflict' if len(statuses)>1 else ('prior_'+statuses[0] if statuses else 'new')
  if b['prior_exact_matches']!=matches or b['disposition']!=disp:fail('prior exact disposition mismatch '+str(k))
  if b['source_index']!=ids.index(sid) or b['source_sha256']!=vsha(sid):fail('source index/hash mismatch '+str(k))
  old=catbefore[loc][sid];new=catafter[loc][sid]
  if old!=b['target_text'] or vsha(old)!=b['target_sha256']:fail('baseline catalog target mismatch '+str(k))
  p=pmap.get((sid,loc));patch=patchmap.get(k);root=rmap.get((sid,loc));d=dmap.get(k);c=cmap.get(k)
  if p:
   if p['expectedOldTarget']!=old or p['expectedOldTargetSha256']!=vsha(old) or p['newTarget']!=new or p['newTargetSha256']!=vsha(new):fail('plan target mismatch '+str(k))
   if patch is None or patch['baseline_target_text']!=old or patch['baseline_target_sha256']!=vsha(old) or patch['final_target']!=new or patch['final_target_sha256']!=vsha(new):fail('application patch mismatch '+str(k))
   if root is None or root['rootTarget']!=new or root['rootTargetSha256']!=vsha(new):fail('root decision mismatch '+str(k))
   expected_status='corrected'; expected_decision='corrected'
  else:
   if new!=old or patch is not None:fail('unplanned catalog change '+str(k))
   expected_status='accepted';expected_decision='accepted' if disp=='new' else ('accepted-carry' if disp=='prior_accepted' else 'accepted-after-cross-review')
   if disp not in ('new','prior_accepted','prior_correction-needed'):fail('unresolved exact conflict/hold '+str(k))
   if disp=='prior_accepted' and c is None:fail('missing accepted carry '+str(k))
  f=fmap[k];ar=amap[k]
  if f['target_text']!=new or f['target_sha256']!=vsha(new) or f['disposition']!=expected_status:fail('final selection mismatch '+str(k))
  if ar['reviewed_target_after']!=new or ar['reviewed_target_after_sha256']!=vsha(new) or ar['status']!=expected_status or ar['decision']!=expected_decision:fail('full audit status/target mismatch '+str(k))
  if ar['baseline_target_sha256']!=b['target_sha256'] or ar['source_sha256']!=b['source_sha256'] or ar['prior_exact_matches']!=matches:fail('audit baseline/source/overlap mismatch '+str(k))
  if placeholders(sid)!=placeholders(new) or ar['placeholders_target']!=placeholders(new) or not ar['placeholders_preserved']:fail('placeholder preservation mismatch '+str(k))
  if icu(sid) or icu(new) or ar['icu_message_source'] or ar['icu_message_target']:fail('unexpected ICU syntax '+str(k))
  if not ar['protected_literals_checked'] or not ar['protected_literals_final_preserved'] or ar['native_speaker_approval']:fail('protected literal or native review assertion mismatch '+str(k))
  if d is not None and (d['reviewed_target_after']!=new or d['status']!=expected_status):fail('fresh decision mismatch '+str(k))
 # Validate candidate, independent root review, and plan pins.
 gmap={(r['source_id'],r['locale']):r for r in gcand};allcand={**candmap,**gmap}
 if len(allcand)!=49:fail('main/group candidate overlap or count mismatch')
 if set(rmap)!=set(candmap)|set(gmap):fail('root candidate coverage mismatch')
 for k,root in rmap.items():
  cand=candmap.get(k) or gmap.get(k);isgroup=k not in candmap;expected_plan_sha=sha((bundle/('korean-discovery-inbox-group-candidates.jsonl' if isgroup else 'candidate-corrections.jsonl')).read_bytes())
  old=cand.get('baseline_target_text',cand.get('current_target_text'));oldsha=cand.get('baseline_target_sha256',cand.get('current_target_sha256'))
  if root['candidatePlanSha256']!=expected_plan_sha or root['currentTarget']!=old or root['currentTargetSha256']!=oldsha or root['sourceSha256']!=vsha(root['sourceId']):fail('root/candidate exact pins mismatch '+str(k))
  proposed=cand.get('proposed_target',cand.get('proposedTarget',cand.get('candidateTarget')))
  proposed_sha=cand.get('proposed_sha256',cand.get('proposed_target_sha256',cand.get('proposedTargetSha256',cand.get('candidateTargetSha256'))))
  if root['candidateTarget']!=proposed or root['candidateTargetSha256']!=proposed_sha:fail('root proposal differs from source candidate '+str(k))
  if root['rootTargetSha256']!=vsha(root['rootTarget']) or placeholders(root['sourceId'])!=placeholders(root['rootTarget']):fail('root target hash/placeholder mismatch '+str(k))
  p=pmap.get(k)
  if root['operation']=='replace_exact':
   if p is None or p['newTarget']!=root['rootTarget'] or p['expectedOldTarget']!=old or p['rootDisposition']!=root['disposition']:fail('apply-plan/root link mismatch '+str(k))
  elif root['operation']=='retain_exact':
   if p is not None or root['rootTarget']!=old:fail('invalid retain disposition '+str(k))
  else:fail('unknown root operation')
 for p in plan:
  k=(p['sourceId'],p['locale']);root=rmap[k]
  if p['sourceSha256']!=vsha(p['sourceId']) or p['rootLedgerSha256']!=sha((bundle/'root-cross-review.jsonl').read_bytes()):fail('plan source/root ledger hash mismatch '+str(k))
  if p['catalogPath']!=f"web/src/lib/locales/ui-labels.{p['locale']}.json":fail('catalog path/locale mismatch '+str(k))
 # The four-message Korean queue term was updated as one group, with 48 locale/source context cells pinned.
 sources=['Approved in Discovery Inbox for the next acquisition step.','Rejected in Discovery Inbox and suppressed for the same evidence.','Snoozed in Discovery Inbox until later review.','Waiting in Discovery Inbox for approval or rejection.']
 if {r['source_id'] for r in gctx}!=set(sources) or {r['locale'] for r in gctx}!=set(LOCALES):fail('Korean group context is incomplete')
 gm={(r['source_id'],r['locale']):r for r in gctx};gp={(r['source_id'],r['locale']):r for r in gpatch}
 if len(gm)!=48 or len(gp)!=4:fail('Korean group cell/application count mismatch')
 for cand in gcand:
  k=(cand['source_id'],cand['locale']);ctx=gm[k];old=catbefore['ko'][k[0]];new=catafter['ko'][k[0]]
  if k[1]!='ko' or cand['source_index']!=ids.index(k[0]) or ctx['current_target_text']!=old or ctx['current_target_sha256']!=vsha(old):fail('Korean group exact baseline mismatch '+str(k))
  if cand['proposed_target']!=new or cand['proposed_target_sha256']!=vsha(new) or '발견함' not in new or '검색함' in new:fail('Korean group term application mismatch '+str(k))
  if gp[k]['baseline_target_sha256']!=vsha(old) or gp[k]['final_target_sha256']!=vsha(new) or gp[k].get('status')!='corrected' or gp[k].get('target_text')!=new or gp[k].get('target_sha256')!=vsha(new):fail('Korean group applied ledger mismatch '+str(k))
 for r in gctx:
  if r['source_sha256']!=vsha(r['source_id']):fail('Korean context source hash mismatch')
  exact=allprior.get((r['source_id'],r['locale'],r['source_sha256'],r['current_target_sha256']),[])
  if r['prior_exact_matches']!=exact:fail('Korean group exact prior overlap mismatch '+str((r['source_id'],r['locale'])))
  statuses=sorted({x['status'] for x in exact});expected='conflict' if len(statuses)>1 else (statuses[0] if statuses else 'unreviewed')
  if r['prior_exact_status']!=expected:fail('Korean group prior status mismatch '+str((r['source_id'],r['locale'])))
 if any(g['prior_exact_matches']!=gm[(g['source_id'],g['locale'])]['prior_exact_matches'] or g['prior_exact_status']!=gm[(g['source_id'],g['locale'])]['prior_exact_status'] for g in gcand):fail('Korean group candidate overlap differs from full context')
 # Verify exact caller blobs against source, review and application commits.
 pins=readj(bundle/'source-pins.json')
 if pins['review_head']!=review or pins['application_head']!=app or pins['source_commit']!=source:fail('source pin commit mismatch')
 if len(pins['files'])!=18:fail('unexpected number of caller-file pins')
 for p,x in pins['files'].items():
  raw=git(repo,'show',f'{source}:{p}',raw=True)
  if sha(raw)!=x['sha256'] or git(repo,'rev-parse',f'{source}:{p}')!=x['git_blob'] or git(repo,'rev-parse',f'{review}:{p}')!=x['git_blob'] or git(repo,'rev-parse',f'{app}:{p}')!=x['git_blob']:fail('caller source/head drift '+p)
 if sha((bundle/'source-context.txt').read_bytes())!=m['source_context']['sha256']:fail('source context hash mismatch')
 if sha((bundle/'headed-visual-check.md').read_bytes())!=m['headed_visual_review']['sha256'] or m['headed_visual_review']['status']!='blocked':fail('visual review blocker record mismatch')
 if m.get('verifier_sha256')!=sha(Path(__file__).read_bytes()):fail('verifier checksum mismatch')
 if m['native_speaker_approval'] is not False or m['tests_builds_ci_workflows_releases_or_tags_run'] is not False:fail('unsupported approval/test claim in manifest')
 if collections.Counter(r['disposition'] for r in final)!=collections.Counter({'accepted':196,'corrected':44}):fail('final selection count mismatch')
 if collections.Counter(r['status'] for r in decisions)!=collections.Counter({'accepted':66,'corrected':1}):fail('fresh decision count mismatch')
 if sum(r['disposition']=='prior_correction-needed' for r in before)!=45 or sum(r['disposition']=='new' for r in before)!=67:fail('fresh/prior correction count mismatch')
 sums=[f'{sha(p.read_bytes())}  {p.name}' for p in sorted(bundle.iterdir()) if p.is_file() and p.name!='SHA256SUMS']
 if (bundle/'SHA256SUMS').read_text().splitlines()!=sums:fail('bundle checksum file mismatch')
 print('PASS: exact 2eb1 review and a65ba4 application commits/trees; 240 window cells (67 fresh: 66 accepted, 1 corrected; 128 accepted carries; 45 prior corrections reassessed); 49 root dispositions (41 accepted, 6 refined, 2 unchanged); 47 exact catalog edits including 3 coordinated Korean siblings; 892 prior evidence inputs; 18 caller pins; placeholders, ICU, protected literals, visual-check blocker, and bundle checksums verified.')
if __name__=='__main__':main()
