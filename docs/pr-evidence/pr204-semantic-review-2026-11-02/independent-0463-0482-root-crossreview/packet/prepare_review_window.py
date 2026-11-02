from __future__ import annotations
import collections, hashlib, json, re, subprocess
from pathlib import Path

ROOT = Path('/mnt/disks/scratch/task-worktrees/slskr-pr204-W463-482-20261102')
REPO = ROOT / 'worktree'
OUT = ROOT / 'packet'
AUDIT = Path('/mnt/disks/scratch/task-worktrees/localization-20261030/slskr-populated-catalog-review-7ff45482-20261101')
HEAD = '549bb55fe009246362cfd75e9f5fbfe5a66bb101'
TREE = '86f59f722e25c1a90d5bc348da68c27247088271'
SOURCE = '7ff454828398de6a3cfb72fe7f0ed21fe419425b'
SOURCE_TREE = '9e9f2aa743c4ff3236af8f99619803bdc3a37152'
LOCS = ['ar','de','es','fr','hi','id','ja','ko','pt-BR','vi','zh-Hans','zh-Hant']
WINDOW = range(463, 483)
TERMINAL = {'accepted','accept','keep','corrected','correction-needed','held','conflict','accept-as-proposed','keep-current-already-satisfied','root-confirmed-correction','source-rewrite-required'}
ALIASES_SOURCE = ['source_id','sourceId','message_id','messageId','id']
ALIASES_SOURCE_SHA = ['source_sha256','sourceSha256','sourceHash','source_hash']
ALIASES_TARGET_SHA = ['target_sha256','targetSha256','current_target_sha256','currentTargetSha256','reviewed_target_after_sha256','reviewedTargetAfterSha256','final_target_sha256','finalTargetSha256','target_after_sha256']
ALIASES_STATUS = ['status','review_outcome','disposition','rootDecision','independentDecision','reviewDecision','decision']

# Evidence-backed context corrections in addition to exact prior review proposals.
EXTRA = {
 ('Batch Descriptor Retrieval','es'): ('Recuperación de descriptores por lotes','moderate','The caller retrieves multiple content descriptors in batches; por lotes expresses the operation rather than descriptors belonging to batches.'),
 ('Batch Descriptor Retrieval','id'): ('Pengambilan deskriptor secara batch','moderate','The caller retrieves multiple content descriptors at once; secara batch clarifies that Batch describes how retrieval happens.'),
 ('Batch Descriptor Retrieval','ko'): ('콘텐츠 설명자 일괄 가져오기','moderate','The caller retrieves multiple content descriptors; 검색 means search, while the source operation and button explicitly retrieve them.'),
 ('Batch Publish Results','ar'): ('نتائج النشر على دفعات','moderate','This is the result heading for publishing multiple descriptors in batches; the current word order makes the results themselves sound like the item being published.'),
 ('Best Next Actions','es'): ('Próximas acciones recomendadas','moderate','This heading introduces ranked recommendations; the current word order is unnatural Spanish and does not read like a heading for recommended next steps.'),
}

# Exact source paths and lines read from the pinned runtime source tree.
CALLERS = {
 'Ban Member': [('web/src/components/System/MediaCore/PodMembershipManagementPanel.jsx',430)],
 'Ban Reason (optional)': [('web/src/components/System/MediaCore/PodMembershipManagementPanel.jsx',414),('web/src/components/System/MediaCore/PodMembershipManagementPanel.jsx',418)],
 'Bandwidth Limit': [('web/src/components/System/Integrations/VpnPanel.jsx',171)],
 'Banned Memberships:': [('web/src/components/System/MediaCore/PodMembershipManagementPanel.jsx',509)],
 'Banned Rejections:': [('web/src/components/System/MediaCore/PodMembershipVerificationPanel.jsx',380)],
 'Banned:': [('web/src/components/System/MediaCore/PodMembershipManagementPanel.jsx',353),('web/src/components/System/MediaCore/PodMembershipManagementPanel.jsx',398),('web/src/components/System/MediaCore/PodMembershipVerificationPanel.jsx',220)],
 'Base URL': [('web/src/components/System/Integrations/MetadataSettingsPanel.jsx',533),('web/src/components/System/Integrations/MetadataSettingsPanel.jsx',548),('web/src/components/System/Integrations/MetadataSettingsPanel.jsx',607)],
 'Base URL configured': [('web/src/components/System/Integrations/FederationDiagnosticsPanel.jsx',161),('web/src/lib/mediaServerIntegrations.js',103),('web/src/lib/servarrReadiness.js',17)],
 'Batch Descriptor Retrieval': [('web/src/components/System/MediaCore/ContentDescriptorRetrievalPanel.jsx',275)],
 'Batch Private Message': [('web/src/components/Messaging/BatchPrivateMessageModal.jsx',17)],
 'Batch Publish Descriptors': [('web/src/components/System/MediaCore/ContentDescriptorPublishingPanel.jsx',260)],
 'Batch Publish Results': [('web/src/components/System/MediaCore/ContentDescriptorPublishingPanel.jsx',292)],
 'Batch Retrieval Results': [('web/src/components/System/MediaCore/ContentDescriptorRetrievalPanel.jsx',307)],
 'Batch Window (ms)': [('web/src/components/System/Security/AdversarialSettingsView.jsx',508)],
 'Batch private message': [('web/src/components/Messaging/Messaging.jsx',783)],
 'Batch private-message body': [('web/src/components/Messaging/BatchPrivateMessageModal.jsx',30),('web/src/components/Messaging/BatchPrivateMessageModal.jsx',35)],
 'Batch private-message recipients': [('web/src/components/Messaging/BatchPrivateMessageModal.jsx',23),('web/src/components/Messaging/BatchPrivateMessageModal.jsx',28)],
 'Batch processed - click again to continue': [('web/src/components/System/Network/index.jsx',361)],
 'Best Next Actions': [('web/src/components/Search/SongIDAnalysisResults.jsx',171)],
 'Black': [('web/src/components/Users/UserNoteModal.jsx',73)],
}

CONTEXT = {
 'Ban Member':'Red action button in the Pod membership management form; invokes handleBanMember for the specified member.',
 'Ban Reason (optional)':'Label and accessible text for the optional reason input above the Pod member ban action.',
 'Bandwidth Limit':'VPN relay details row. The value immediately following is expressed in Mbit/s.',
 'Banned Memberships:':'Membership statistics count for records whose membership is marked banned.',
 'Banned Rejections:':'Verification statistics count checks rejected because is_not_banned is false; the statistic is named banned_member_rejections in the controller.',
 'Banned:':'Boolean status field for a Pod membership, rendered with Yes or No; a related Not Banned field is used for message verification.',
 'Base URL':'Form label for the base URL field in AcoustID, MusicBrainz, and Lidarr integration settings.',
 'Base URL configured':'Yes/no readiness or diagnostics label for whether the service base URL is configured.',
 'Batch Descriptor Retrieval':'Card heading. The adjacent description says to retrieve multiple content descriptors simultaneously; the button is Retrieve Batch.',
 'Batch Private Message':'Modal heading for the flow that sends one private message to multiple recipients and stores one local conversation per recipient.',
 'Batch Publish Descriptors':'Card heading. The adjacent description says to publish multiple content descriptors simultaneously.',
 'Batch Publish Results':'Results heading above total requested, successfully published, failed, and skipped counts.',
 'Batch Retrieval Results':'Results heading above requested, found, failed, and total-duration values for descriptor retrieval.',
 'Batch Window (ms)':'Numeric setting under Privacy > Message Batching, range 100–5000, stored as Privacy.Batching.BatchWindowMs.',
 'Batch private message':'Toolbar button title; its popup explains one private message sent to multiple users through the native Soulseek batch command.',
 'Batch private-message body':'aria-label for the textarea containing the single message body sent to all listed recipients; the visible label is Message.',
 'Batch private-message recipients':'aria-label for the comma-separated recipient textarea; the visible label is Recipients.',
 'Batch processed - click again to continue':'Fallback toast for a non-final history-backfill chunk; a later click continues the operation.',
 'Best Next Actions':'Heading over the ranked next-step suggestions in SongID analysis results.',
 'Black':'Standalone selectable user-note color, paired with colored swatches; not a blacklist/security state.',
}

# Context-only protected names/units. No selected source string has interpolation placeholders.
PROTECTED_CONTEXT = {
 'Ban Member':['Pod'],
 'Ban Reason (optional)':['Pod'],
 'Banned Memberships:':['Pod'],
 'Banned Rejections:':['Pod'],
 'Banned:':['Pod'],
 'Bandwidth Limit':['Mbit/s'],
 'Batch Private Message':['Soulseek'],
 'Batch private message':['Soulseek'],
 'Batch private-message body':['Soulseek'],
 'Batch private-message recipients':['Soulseek'],
 'Batch Window (ms)':['ms'],
 'Base URL':['URL'],
 'Base URL configured':['URL'],
}

SOURCE_REWRITES = {
 'Banned Rejections:':'Consider “Rejections due to banned members:” so the English label states why membership checks were rejected.',
 'Batch Private Message':'Consider “Private Message to Multiple Recipients” for the modal heading; the title describes one message sent to several users.',
 'Batch private message':'Consider “Private Message to Multiple Recipients” for the toolbar title; the tooltip describes one message sent to several users.',
 'Batch private-message body':'Consider “Private message text” or “Message text” for this accessible name; the field contains one shared message body.',
 'Batch private-message recipients':'Consider “Private message recipients” for this accessible name; the field holds the recipient list.',
 'Batch Window (ms)':'Consider “Message batching window (ms)” to make clear that this is a time interval, not a UI window or batch size.',
}


def sha(b: bytes) -> str: return hashlib.sha256(b).hexdigest()
def jcanon(o) -> bytes: return json.dumps(o,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()
def target_sha(v) -> str: return sha(v.encode('utf-8') if isinstance(v,str) else jcanon(v))
def git(*args, raw=False):
    b=subprocess.check_output(['git',*args],cwd=REPO)
    return b if raw else b.decode().strip()
def unique_source(rows): return sorted({r['source_id'] for r in rows})
def walk(o):
    if isinstance(o,dict):
        yield o
        for v in o.values(): yield from walk(v)
    elif isinstance(o,list):
        for v in o: yield from walk(v)
def first(d,names):
    for n in names:
        if d.get(n) is not None: return d[n]
def parse_evidence(raw: bytes, path: str):
    try:
        if path.endswith('.jsonl'):
            for line_no,line in enumerate(raw.decode().splitlines(),1):
                if not line.strip(): continue
                try: obj=json.loads(line)
                except json.JSONDecodeError: continue
                yield line_no,obj
        elif path.endswith('.json'):
            try: obj=json.loads(raw.decode())
            except json.JSONDecodeError: return
            for n,row in enumerate(walk(obj),1): yield n,row
    except UnicodeDecodeError:
        return

def evidence_status(row):
    v=first(row,ALIASES_STATUS)
    return str(v or '').strip().lower().replace('_','-')

def evidence_hash(row, aliases):
    value=first(row,aliases)
    if isinstance(value,str) and re.fullmatch(r'[0-9a-fA-F]{64}',value): return value.lower()
    return None

assert git('rev-parse','HEAD') == HEAD
assert git('rev-parse','HEAD^{tree}') == TREE
assert git('rev-parse',f'{SOURCE}^{{tree}}') == SOURCE_TREE
assert git('merge-base',SOURCE,HEAD) == SOURCE
assert not git('status','--porcelain')

source_inventory_path=AUDIT/'frozen-inputs/source-inventory.jsonl'
source_inventory_raw=source_inventory_path.read_bytes()
source_inventory=[json.loads(x) for x in source_inventory_raw.decode().splitlines() if x.strip()]
ids=unique_source(source_inventory)
assert len(ids)==5437
assert ids[463:483]==[
 'Ban Member','Ban Reason (optional)','Bandwidth Limit','Banned Memberships:','Banned Rejections:','Banned:','Base URL','Base URL configured','Batch Descriptor Retrieval','Batch Private Message','Batch Publish Descriptors','Batch Publish Results','Batch Retrieval Results','Batch Window (ms)','Batch private message','Batch private-message body','Batch private-message recipients','Batch processed - click again to continue','Best Next Actions','Black']

live_raw=subprocess.check_output(['gh','pr','view','204','--repo','snapetech-org/slskR','--json','state,isDraft,mergeStateStatus,mergeable,headRefOid,headRefName,baseRefOid,url'],cwd=REPO)
live=json.loads(live_raw)
assert live['state']=='OPEN' and live['isDraft'] is True and live['mergeStateStatus']=='CLEAN' and live['mergeable']=='MERGEABLE'
assert live['headRefOid']==HEAD

catalogs={}; catalog_hashes={}; catalog_info={}
for loc in LOCS:
    path=f'web/src/lib/locales/ui-labels.{loc}.json'
    raw=git('show',f'{HEAD}:{path}',raw=True)
    cat=json.loads(raw.decode())
    assert set(cat)==set(ids),(loc,len(cat),len(set(cat)^set(ids)))
    catalogs[loc]=cat; catalog_hashes[path]=sha(raw)
    catalog_info[loc]={'path':path,'bytes':len(raw),'sha256':sha(raw),'source_keys':len(cat)}

source_sha={r['source_id']:r['source_sha256'] for r in source_inventory}
current={}
for idx in WINDOW:
    sid=ids[idx]
    assert source_sha[sid]==sha(sid.encode('utf-8'))
    for loc in LOCS:
        target=catalogs[loc][sid]
        assert isinstance(target,str) and target.strip(),(sid,loc,target)
        current[(sid,loc)]={'source_index':idx,'source_id':sid,'locale':loc,'source_sha256':source_sha[sid],
                            'current_text':target,'current_target_sha256':target_sha(target),
                            'catalog_path':f'web/src/lib/locales/ui-labels.{loc}.json',
                            'placeholders':sorted(set(re.findall(r'\{[^{}]+\}',sid))),
                            'protected_literals':PROTECTED_CONTEXT.get(sid,[])}

# Freeze exact caller blobs and line excerpts from source commit 7ff4548.
source_context=[]; caller_counts=collections.Counter()
for sid in ids[463:483]:
    pins=[]
    for path,line_no in CALLERS[sid]:
        blob=git('show',f'{SOURCE}:{path}',raw=True)
        lines=blob.decode('utf-8').splitlines()
        assert 1<=line_no<=len(lines),(sid,path,line_no)
        line=lines[line_no-1]
        assert sid in line,(sid,path,line_no,line)
        lo=max(1,line_no-3); hi=min(len(lines),line_no+3)
        excerpt=[{'line':n,'text':lines[n-1]} for n in range(lo,hi+1)]
        oid=git('rev-parse',f'{SOURCE}:{path}')
        assert git('rev-parse',f'{HEAD}:{path}')==oid,(sid,path,'caller changed on PR head')
        pin={'path':path,'blob_oid':oid,'sha256':sha(blob),'occurrence_line':line_no,'occurrence_text':line,'excerpt':excerpt}
        pins.append(pin); caller_counts[path]+=1
    source_context.append({'schema_version':1,'source_head':SOURCE,'source_tree':SOURCE_TREE,'source_index':ids.index(sid),
                          'source_id':sid,'source_sha256':source_sha[sid],'context':CONTEXT[sid],
                          'protected_context_literals':PROTECTED_CONTEXT.get(sid,[]),
                          'source_rewrite_consideration':SOURCE_REWRITES.get(sid),
                          'caller_pins':pins})

# Gather prior evidence paths: frozen broader review plus all prior PR semantic evidence.
inputs=[]
for p in [AUDIT/'findings.jsonl',AUDIT/'carried-findings.jsonl']:
    if p.is_file(): inputs.append(('audit-scratch',p.relative_to(AUDIT).as_posix(),p.read_bytes()))
for p in sorted((AUDIT/'review-evidence').rglob('*')):
    if p.is_file() and p.suffix in {'.jsonl','.json'}:
        inputs.append(('audit-scratch',p.relative_to(AUDIT).as_posix(),p.read_bytes()))
repo_evidence_paths=git('ls-tree','-r','--name-only',HEAD).splitlines()
repo_evidence_paths=[p for p in repo_evidence_paths if (
    p.startswith('docs/pr-evidence/pr204-semantic-review-2026-11-01/') or
    p.startswith('docs/pr-evidence/pr204-semantic-review-2026-11-02/') or
    p in {'docs/localization/pr204-translation-review-2026-11-01.jsonl','docs/localization/pr204-translation-review-2026-11-01.manifest.json','docs/localization/pr204-regional-format-key-review-2026-11-01.json'}
) and p.endswith(('.jsonl','.json'))]
for p in sorted(repo_evidence_paths):
    inputs.append(('pr-head',p,git('show',f'{HEAD}:{p}',raw=True)))

input_manifest=[]; overlaps=collections.defaultdict(list); stale=collections.defaultdict(list)
selected=set(ids[463:483])
for root_name,path,raw in inputs:
    input_manifest.append({'root':root_name,'path':path,'bytes':len(raw),'sha256':sha(raw)})
    for line_no,row in parse_evidence(raw,path):
        sid=first(row,ALIASES_SOURCE); loc=row.get('locale')
        if not isinstance(sid,str) or sid not in selected or loc not in LOCS: continue
        cell=current[(sid,loc)]
        sh=evidence_hash(row,ALIASES_SOURCE_SHA)
        th=evidence_hash(row,ALIASES_TARGET_SHA)
        if not th:
            val=first(row,['current_target','currentTarget','currentText','target_text','current_value'])
            if isinstance(val,str): th=target_sha(val)
        rec={'root':root_name,'path':path,'line':line_no,'status':evidence_status(row) or None,
             'source_sha256':sh,'target_sha256':th,
             'confidence':row.get('confidence'),'issue_type':row.get('issue_type'),
             'finding_id':row.get('finding_id') or row.get('findingId'),
             'prior_current_text':first(row,['current_target','currentTarget','currentText','target_text','current_value']),
             'prior_proposed_text':first(row,['proposed_target','proposedTarget','proposedText','rootFinalText','independentFinalText']),
             'prior_reason':row.get('reason') or row.get('rationale') or row.get('rootRationale')}
        if th==cell['current_target_sha256'] and (not sh or sh==cell['source_sha256']):
            overlaps[(sid,loc)].append(rec)
        elif sh==cell['source_sha256']:
            stale[(sid,loc)].append(rec)
input_manifest.sort(key=lambda x:(x['root'],x['path']))
raw_exact_match_count=sum(len(v) for v in overlaps.values())
for key,records in list(overlaps.items()):
    grouped={}
    for rec in records:
        signature=(rec.get('status'),rec.get('source_sha256'),rec.get('target_sha256'),
                   rec.get('finding_id'),rec.get('prior_proposed_text'),rec.get('prior_reason'))
        if signature not in grouped:
            grouped[signature]={**rec,'evidence_refs':[]}
        grouped[signature]['evidence_refs'].append({'root':rec['root'],'path':rec['path'],'line':rec['line']})
    overlaps[key]=list(grouped.values())

# Per-cell semantic ledger. Exact prior candidates are independently confirmed where the pinned caller supports them.
ledger=[]; counts=collections.Counter(); per_locale=collections.defaultdict(collections.Counter); conflicts=[]
for idx in WINDOW:
    sid=ids[idx]
    for loc in LOCS:
        cell=current[(sid,loc)]
        exact=overlaps.get((sid,loc),[])
        corrections=[x for x in exact if evidence_status(x) in {'correction-needed','source-rewrite-required'} and x.get('prior_proposed_text') is not None]
        prior_proposals=sorted({x['prior_proposed_text'] for x in corrections})
        extra=EXTRA.get((sid,loc))
        if extra:
            proposal,confidence,rationale=extra
            decision='reopen-prior-accepted' if any(evidence_status(x) in {'accepted','accept','keep','accept-as-proposed'} for x in exact) else 'new-correction-candidate'
        elif len(prior_proposals)>1:
            proposal=None; confidence='low'; rationale='Prior exact-current evidence contains conflicting proposed targets; retain for root cross-review.'
            decision='hold-prior-conflict'
            conflicts.append({'source_index':idx,'source_id':sid,'locale':loc,'proposals':prior_proposals})
        elif prior_proposals:
            proposal=prior_proposals[0]
            confidence=max([x.get('confidence') or 'moderate' for x in corrections],key=lambda x:{'low':0,'moderate':1,'high':2}.get(x,1))
            rationale='Confirmed against the exact pinned caller context and current target. Prior exact-hash finding: '+str(next((x.get('prior_reason') for x in corrections if x.get('prior_reason')),''))
            decision='confirm-prior-correction'
        else:
            proposal=None; confidence='high'; rationale='Current wording matches the exact caller meaning; standalone punctuation, unit, and placeholder checks found no defect.'
            decision='accept-current'
        if proposal is not None:
            assert isinstance(proposal,str) and proposal.strip()
            assert sorted(set(re.findall(r'\{[^{}]+\}',proposal)))==cell['placeholders'],(sid,loc,proposal)
        row={'schema_version':1,'review_window':'463-482','pr_number':204,'pr_head':HEAD,'pr_tree':TREE,
             'source_head':SOURCE,'source_tree':SOURCE_TREE,'source_index':idx,'source_id':sid,
             'source_sha256':cell['source_sha256'],'locale':loc,'catalog_path':cell['catalog_path'],
             'current_text':cell['current_text'],'current_target_sha256':cell['current_target_sha256'],
             'placeholder_set':cell['placeholders'],'protected_literals':cell['protected_literals'],
             'prior_exact_matches':exact,'prior_source_same_target_stale_matches':stale.get((sid,loc),[]),
             'prior_proposals':prior_proposals,'review_decision':decision,'proposed_text':proposal,
             'proposed_target_sha256':target_sha(proposal) if proposal is not None else None,
             'confidence':confidence,'rationale':rationale,'native_speaker_approval':False,
             'catalog_modified':False}
        ledger.append(row); counts[decision]+=1; per_locale[loc][decision]+=1

assert len(ledger)==240 and len({(x['source_id'],x['locale']) for x in ledger})==240
assert all(len(CALLERS[sid]) for sid in ids[463:483])

# Emit packet artifacts.
(OUT/'source-inventory.jsonl').write_bytes(source_inventory_raw)
(OUT/'freeze-manifest.json').write_bytes((AUDIT/'freeze-manifest.json').read_bytes())
(OUT/'freeze-manifest.sha256').write_bytes((AUDIT/'freeze-manifest.sha256').read_bytes())
(OUT/'source-context.jsonl').write_text(''.join(json.dumps(x,ensure_ascii=False,sort_keys=True)+'\n' for x in source_context))
(OUT/'prior-evidence-scan-manifest.jsonl').write_text(''.join(json.dumps(x,ensure_ascii=False,sort_keys=True)+'\n' for x in input_manifest))
(OUT/'decision-ledger.jsonl').write_text(''.join(json.dumps(x,ensure_ascii=False,sort_keys=True)+'\n' for x in ledger))
exact_rows=[]
for row in ledger:
    for match in row['prior_exact_matches']:
        exact_rows.append({'source_index':row['source_index'],'source_id':row['source_id'],'locale':row['locale'],**match})
(OUT/'prior-exact-matches.jsonl').write_text(''.join(json.dumps(x,ensure_ascii=False,sort_keys=True)+'\n' for x in exact_rows))

runtime_diff=[p for p in git('diff','--name-only',SOURCE,HEAD,'--','web/src/components','web/src/lib').splitlines() if not p.startswith('web/src/lib/locales/')]
assert not runtime_diff,runtime_diff
summary={
 'schema_version':1,'repository':'snapetech-org/slskR','pull_request':204,
 'live_pr_state':live,'pr_head':HEAD,'pr_tree':TREE,'source_head':SOURCE,'source_tree':SOURCE_TREE,
 'branch_tree_is_source_ancestor':True,
 'source_runtime_diff_from_source_head_to_pr_head':runtime_diff,
 'source_ids':len(ids),'window_indices':[463,482],'window_source_ids':ids[463:483],
 'target_locales':LOCS,'window_cells':len(ledger),'decisions':dict(counts),
 'per_locale':{k:dict(v) for k,v in per_locale.items()},
 'correction_candidates':sum(x['proposed_text'] is not None for x in ledger),
 'prior_exact_match_cells':sum(bool(x['prior_exact_matches']) for x in ledger),
 'prior_exact_match_records':len(exact_rows),'prior_exact_match_raw_records':raw_exact_match_count,
 'prior_conflicts':conflicts,
 'prior_evidence_inputs':len(input_manifest),'prior_evidence_inputs_sha256':sha(jcanon(input_manifest)),
 'source_inventory_sha256':sha(source_inventory_raw),
 'freeze_manifest_sha256':sha((AUDIT/'freeze-manifest.json').read_bytes()),
 'freeze_manifest_declared_source_inventory_sha256':json.loads((AUDIT/'freeze-manifest.json').read_text())['source_inventory_sha256'],
 'catalogs':catalog_info,'caller_files':dict(sorted(caller_counts.items())),
 'placeholders_in_selected_source_ids':sum(bool(x['placeholder_set']) for x in ledger),
 'protected_literal_tokens_contextual_only':True,
 'native_speaker_approval':False,'catalogs_modified':False,
 'tests_builds_scans_ci_workflows_releases_tags_merges':False,
 'worktree_status':git('status','--porcelain'),
}
(OUT/'manifest.json').write_text(json.dumps(summary,ensure_ascii=False,sort_keys=True,indent=2)+'\n')
print(json.dumps({k:v for k,v in summary.items() if k not in {'window_source_ids','per_locale','catalogs','caller_files','source_component_diff_from_source_head_to_pr_head','prior_conflicts'}},ensure_ascii=False,indent=2))
print('window_source_ids:',json.dumps(summary['window_source_ids'],ensure_ascii=False))
print('extra_proposals:',len(EXTRA),'prior_exact_cells:',summary['prior_exact_match_cells'],'prior_exact_records:',len(exact_rows),'conflicts:',len(conflicts))
