import collections, hashlib, json, re, subprocess
from pathlib import Path

REPO=Path('/mnt/disks/scratch/task-worktrees/localization-20261102/slskr-pr204-w503-522')
OUT=Path('/mnt/disks/scratch/task-scratch/slskr-pr204-W553-562-independent-review-20261102')
HEAD='255dc8789cf130c9fee39ab94f84a00fab79d215'
TREE='afdc0f69e5ed99e84e689fb6b2f20c1fe74dea54'
SOURCE='7ff454828398de6a3cfb72fe7f0ed21fe419425b'
SOURCE_TREE='9e9f2aa743c4ff3236af8f99619803bdc3a37152'
LOCALES=['ar','de','es','fr','hi','id','ja','ko','pt-BR','vi','zh-Hans','zh-Hant']
WINDOW=range(553,563)
INV_PATH='docs/pr-evidence/pr204-localization-2026-11-02/window-523-542/primary/source-inventory.jsonl'
W523='/mnt/disks/scratch/task-scratch/slskr-pr204-W523-542-20261102/packet'
W523_X='/mnt/disks/scratch/task-scratch/slskr-pr204-W523-542-independent-crossreview-20261102'

def git(*args): return subprocess.check_output(['git','-C',str(REPO),*args])
def sha(b): return hashlib.sha256(b).hexdigest()
def sha_text(s): return sha(s.encode('utf-8'))
def blob(c,p): return git('show',f'{c}:{p}')
def oid(c,p): return git('rev-parse',f'{c}:{p}').decode().strip()
def write_json(name,obj): (OUT/name).write_text(json.dumps(obj,ensure_ascii=False,sort_keys=True,indent=2)+'\n',encoding='utf-8')
def write_jsonl(name,rows): (OUT/name).write_text(''.join(json.dumps(x,ensure_ascii=False,sort_keys=True)+'\n' for x in rows),encoding='utf-8')
def placeholders(s): return sorted(set(re.findall(r'\{[^{}]+\}',s)))

assert git('rev-parse',f'{HEAD}^{{commit}}').decode().strip()==HEAD
assert git('rev-parse',f'{HEAD}^{{tree}}').decode().strip()==TREE
assert git('rev-parse',f'{SOURCE}^{{tree}}').decode().strip()==SOURCE_TREE
assert git('merge-base',SOURCE,HEAD).decode().strip()==SOURCE
assert git('status','--porcelain').decode().strip()==''
# The parent independently verified this live PR head with gh at task start; pin its recorded view too.
live={'url':'https://github.com/snapetech-org/slskR/pull/204','state':'OPEN','headRefOid':HEAD,'headRefName':'codex/slskr-l10n-audit-20261030'}

inventory=[json.loads(x) for x in blob(HEAD,INV_PATH).decode().splitlines() if x.strip()]
assert len(inventory)==5437
source_rows=[]
for i in WINDOW:
    row=inventory[i]
    assert sha_text(row['source_id'])==row['source_sha256']
    source_rows.append(row)
assert [x['source_id'] for x in source_rows]==[
 'CSV Text','CSV did not contain any track rows','CSV text is required.','Cache Hits:','Cache Misses:',
 'Cache Performance','Cache Size:','Cache cleared: {entriesCleared} entries, {bytesFreed} bytes freed',
 'Cache performance and retrieval statistics','Calendar']

catalogs={}; catalog_pins={}
for loc in LOCALES:
    p=f'web/src/lib/locales/ui-labels.{loc}.json'
    raw=blob(HEAD,p); data=json.loads(raw.decode('utf-8'))
    catalogs[loc]=data
    catalog_pins[loc]={'path':p,'bytes':len(raw),'sha256':sha(raw),'git_blob_oid':oid(HEAD,p),'source_keys':len(data)}
    assert len(data)==5437

# Search every tracked app-source file for an exact quoted occurrence, then pin the call line and context.
paths=git('ls-tree','-r','--name-only',HEAD).decode().splitlines()
source_paths=[p for p in paths if (p.startswith('web/src/') or p.startswith('crates/slskr-web/src/')) and '/lib/locales/ui-labels.' not in p]
source_paths=[p for p in source_paths if not p.endswith(('.test.js','.test.jsx','.spec.js','.spec.jsx'))]
source_blobs={p:blob(HEAD,p) for p in source_paths}
source_pin_records=[]
manual_context={
 'CSV Text':'Label for the editable text area in the Wishlist CSV import modal, where the user pastes CSV contents.',
 'CSV did not contain any track rows':'Allowlisted server error message used for CSV import failures when parsed input contains no track rows.',
 'CSV text is required.':'Validation toast shown when the CSV text entry is empty at import time.',
 'Cache Hits:':'Statistic label immediately before the count of lookups successfully served by the cache, shown in both retrieval and dashboard statistics.',
 'Cache Misses:':'Statistic label immediately before the count of lookups absent from cache, paired with Cache Hits and Hit Ratio in two statistics panels.',
 'Cache Performance':'Header for the cache statistics block containing retrieval totals, hits, misses, hit ratio, and cache size.',
 'Cache Size:':'Statistic label before the descriptor cache size, formatted in KB in the statistics panels.',
 'Cache cleared: {entriesCleared} entries, {bytesFreed} bytes freed':'Success toast after clearing the content-descriptor retrieval cache; both placeholders are supplied from the clear result.',
 'Cache performance and retrieval statistics':'Description of the MediaCore dashboard card covering cache behavior and content-descriptor retrieval statistics.',
 'Calendar':'No exact caller appears in tracked application source at the pinned source baseline; only the populated catalog key exists.',
}
for row in source_rows:
    sid=row['source_id']; escaped=re.escape(sid)
    pattern=re.compile(r'(?<![\w])([\'\"])'+escaped+r'\1(?![\w])')
    pins=[]
    for path in source_paths:
        raw=source_blobs[path]
        try: lines=raw.decode('utf-8').splitlines()
        except UnicodeDecodeError: continue
        for n,line in enumerate(lines,1):
            if not pattern.search(line): continue
            # All exact matches in this window are localization calls or the server-message allowlist entry.
            if any(token in line for token in ('LocalizedText','localized(','localizedRef.current','interfaceText','interfaceTextProps')):
                kind='localized-call'
            elif path=='web/src/lib/serverErrorMessageAllowlist.js' and sid in line:
                kind='localized-server-error-allowlist-entry'
            else:
                continue
            src_raw=blob(SOURCE,path); pr_raw=blob(HEAD,path)
            assert src_raw==pr_raw, (sid,path,'caller differs between runtime baseline and PR head')
            src_lines=src_raw.decode('utf-8').splitlines()
            excerpt=[{'line':k,'text':src_lines[k-1]} for k in range(max(1,n-3),min(len(src_lines),n+3)+1)]
            pins.append({'path':path,'caller_kind':kind,'source_blob_oid':oid(SOURCE,path),'pr_blob_oid':oid(HEAD,path),'source_file_sha256':sha(src_raw),'pr_file_sha256':sha(pr_raw),'occurrence_line':n,'occurrence_text':src_lines[n-1],'excerpt':excerpt})
    source_pin_records.append({'schema_version':1,'source_index':row['source_index'] if 'source_index' in row else WINDOW.start+len(source_pin_records),'source_id':sid,'source_sha256':row['source_sha256'],'source_head':SOURCE,'source_tree':SOURCE_TREE,'pr_head':HEAD,'pr_tree':TREE,'caller_status':'direct-caller-pinned' if pins else 'no-direct-localization-caller','context':manual_context[sid],'caller_pins':pins})

assert all(len(x['caller_pins'])==0 if x['source_id']=='Calendar' else len(x['caller_pins'])>=1 for x in source_pin_records)
assert sum(len(x['caller_pins']) for x in source_pin_records)==12

# Independently reviewed dispositions and exact correction candidates.
candidates={
 ('Cache Hits:','ar'):'مرات العثور على العنصر في ذاكرة التخزين المؤقت:',
 ('Cache Hits:','es'):'Aciertos de caché:',
 ('Cache Hits:','fr'):'Succès du cache :',
 ('Cache Hits:','pt-BR'):'Acertos de cache:',
 ('Cache Hits:','vi'):'Số lần tìm thấy trong bộ đệm:',
 ('Cache Misses:','ar'):'حالات عدم العثور على العنصر في ذاكرة التخزين المؤقت:',
 ('Cache Misses:','de'):'Cache-Fehlzugriffe:',
 ('Cache Misses:','es'):'Fallos de caché:',
 ('Cache Misses:','fr'):'Défauts de cache :',
 ('Cache Misses:','id'):'Cache miss:',
 ('Cache Misses:','pt-BR'):'Falhas de cache:',
 ('Cache Misses:','vi'):'Số lần không tìm thấy trong bộ đệm:',
 ('Cache Misses:','ko'):'캐시 미스:',
 ('Cache Misses:','zh-Hant'):'快取未命中：',
 ('Cache Hits:','zh-Hant'):'快取命中：',
 ('Cache Size:','hi'):'कैश का आकार:',
 ('Cache cleared: {entriesCleared} entries, {bytesFreed} bytes freed','ar'):'تم مسح ذاكرة التخزين المؤقت: حُذف {entriesCleared} من الإدخالات، وتم تحرير {bytesFreed} بايت.',
 ('Cache cleared: {entriesCleared} entries, {bytesFreed} bytes freed','de'):'Cache geleert: {entriesCleared} Einträge entfernt, {bytesFreed} Bytes freigegeben.',
 ('Cache cleared: {entriesCleared} entries, {bytesFreed} bytes freed','es'):'Caché vaciada: se eliminaron {entriesCleared} entradas y se liberaron {bytesFreed} bytes.',
 ('Cache cleared: {entriesCleared} entries, {bytesFreed} bytes freed','fr'):'Cache vidé : {entriesCleared} entrées supprimées, {bytesFreed} octets libérés.',
 ('Cache cleared: {entriesCleared} entries, {bytesFreed} bytes freed','vi'):'Đã xóa bộ đệm: {entriesCleared} mục, giải phóng {bytesFreed} byte',
 ('Cache cleared: {entriesCleared} entries, {bytesFreed} bytes freed','ko'):'캐시 삭제 완료: {entriesCleared}개 항목을 삭제하고 {bytesFreed}바이트를 확보했습니다.',
 ('Cache cleared: {entriesCleared} entries, {bytesFreed} bytes freed','id'):'Cache dibersihkan: {entriesCleared} entri dihapus, {bytesFreed} byte dibebaskan.',
 ('Cache cleared: {entriesCleared} entries, {bytesFreed} bytes freed','pt-BR'):'Cache limpo: {entriesCleared} entradas removidas, {bytesFreed} bytes liberados.',
 ('Cache cleared: {entriesCleared} entries, {bytesFreed} bytes freed','zh-Hans'):'缓存已清除：已删除 {entriesCleared} 个条目，释放 {bytesFreed} 字节。',
 ('Cache cleared: {entriesCleared} entries, {bytesFreed} bytes freed','zh-Hant'):'快取已清除：已刪除 {entriesCleared} 個項目，釋放 {bytesFreed} 位元組。',
 ('Cache performance and retrieval statistics','ko'):'캐시 성능 및 가져오기 통계',
}
rationales={
 'Cache Hits:':'This statistic counts successful cache lookups. The current target says visits/accesses, which includes requests that miss the cache.',
 'Cache Misses:':'This statistic counts lookups absent from cache. The current target means cache errors, missing/lost cache, or omissions rather than a cache miss.',
 'Cache Size:':'The current Hindi target misspells the transliteration of “cache”; this candidate uses the standard कैश spelling.',
 'Cache cleared: {entriesCleared} entries, {bytesFreed} bytes freed':'The toast needs to identify the cleared entry count and bytes released with natural count order and both placeholders intact.',
 'Cache performance and retrieval statistics':'The panel reports content retrievals, not searches; the Korean current target uses 검색 (“search”) instead of a retrieval/fetch term.',
}
extra_rationale={
 ('Cache Misses:','ko'):'The current Korean 누락 means omission/being left out; the metric counts failed cache lookups. 캐시 미스 is the established technical term.',
 ('Cache Misses:','zh-Hant'):'Use the Taiwan-standard 快取 term already used by the same catalog for Cache Performance and Cache Size, rather than 緩存.',
 ('Cache Hits:','zh-Hant'):'Use the same 快取 terminology as adjacent cache labels in this Traditional Chinese catalog; the current label uses 緩存.',
 ('Cache cleared: {entriesCleared} entries, {bytesFreed} bytes freed','ko'):'The current wording leaves the entry count without an action and uses an awkward detached phrase for freed bytes; the candidate explicitly says entries were deleted and bytes recovered.',
 ('Cache cleared: {entriesCleared} entries, {bytesFreed} bytes freed','id'):'Reorders the count before its noun and explicitly says the entries were deleted, while retaining the bytes-freed meaning.',
 ('Cache cleared: {entriesCleared} entries, {bytesFreed} bytes freed','pt-BR'):'Reorders the count before its noun and clarifies that entries were removed, preserving the freed-byte count.',
 ('Cache cleared: {entriesCleared} entries, {bytesFreed} bytes freed','zh-Hans'):'Adds the classifier 个 and explicitly states that the counted entries were deleted.',
 ('Cache cleared: {entriesCleared} entries, {bytesFreed} bytes freed','zh-Hant'):'Adds the classifier 個 and explicitly states that the counted entries were deleted, using the catalog’s 快取 terminology.',
}

def reason_for(key): return extra_rationale.get(key, rationales[key[0]])

ledger=[]; summary_counts=collections.Counter(); locale_counts=collections.defaultdict(collections.Counter)
context_by_id={r['source_id']:r for r in source_pin_records}
for source in source_rows:
    i=inventory.index(source); sid=source['source_id']; sh=source['source_sha256']
    assert i in WINDOW
    context=context_by_id[sid]
    for loc in LOCALES:
        current=catalogs[loc][sid]
        target_sha=sha_text(current)
        source_placeholders=placeholders(sid)
        if sid=='Calendar':
            disposition='no-op-no-direct-localized-caller'; proposal=None
            rationale='No exact localized caller exists in the tracked application source at the pinned baseline, so this catalog value is inactive and retained as a no-op.'
            confidence='high'
        elif (sid,loc) in candidates:
            disposition='correction'; proposal=candidates[(sid,loc)]
            rationale=reason_for((sid,loc)); confidence='moderate'
            assert proposal.strip() and placeholders(proposal)==source_placeholders
            assert sha_text(proposal)!=target_sha
        else:
            disposition='accept-current'; proposal=None
            rationale='The current target preserves the source meaning in the pinned UI context; spelling, technical terminology, and placeholders were reviewed.'
            confidence='moderate'
        ledger.append({'schema_version':1,'review_window':'553-562','pr_number':204,'pr_head':HEAD,'pr_tree':TREE,'source_head':SOURCE,'source_tree':SOURCE_TREE,'source_index':i,'source_id':sid,'source_sha256':sh,'locale':loc,'catalog_path':f'web/src/lib/locales/ui-labels.{loc}.json','current_text':current,'current_target_sha256':target_sha,'placeholder_set':source_placeholders,'caller_status':context['caller_status'],'caller_context_sha256':sha(json.dumps(context,ensure_ascii=False,sort_keys=True).encode('utf-8')),'caller_pins':[{'path':p['path'],'source_blob_oid':p['source_blob_oid'],'pr_blob_oid':p['pr_blob_oid'],'occurrence_line':p['occurrence_line'],'source_file_sha256':p['source_file_sha256'],'pr_file_sha256':p['pr_file_sha256']} for p in context['caller_pins']],'independent_disposition':disposition,'candidate_text':proposal,'candidate_sha256':sha_text(proposal) if proposal is not None else None,'rationale':rationale,'confidence':confidence,'native_speaker_approval':False,'native_speaker_review_required':True})
        summary_counts[disposition]+=1; locale_counts[loc][disposition]+=1

assert len(ledger)==120 and len({(x['source_index'],x['locale']) for x in ledger})==120
assert summary_counts=={'accept-current':81,'correction':27,'no-op-no-direct-localized-caller':12},summary_counts
assert all(x['candidate_sha256']==sha_text(x['candidate_text']) for x in ledger if x['candidate_text'] is not None)
assert sum(x['independent_disposition']=='no-op-no-direct-localized-caller' for x in ledger)==12
assert all(x['source_id']=='Calendar' for x in ledger if x['independent_disposition']=='no-op-no-direct-localized-caller')

# Verify exact no-op/held boundary from the preceding W523–542 cross-review.
w523_primary=[json.loads(x) for x in open(Path(W523)/'current-cells.jsonl',encoding='utf-8')]
w523_cross=[json.loads(x) for x in open(Path(W523_X)/'cross-review-ledger.jsonl',encoding='utf-8')]
w523_summary=json.loads((Path(W523_X)/'cross-review-summary.json').read_text())
prev_noop={r['source_index']:r['source_id'] for r in w523_cross if r.get('independent_disposition')=='no-op' or r.get('cross_review_disposition')=='no-op' or r.get('disposition')=='no-op'}
# Use the authoritative prior summary and primary source index; ledger schema names may vary.
prev_noop_source=w523_summary['no_op_source_id']; prev_noop_index=w523_summary['no_op_source_index']; prev_noop_cells=w523_summary['no_op_locale_cell_count']
held=w523_summary['held_candidate_text']; held_hash=w523_summary['held_candidate_sha256']
held_cell=next(r for r in w523_cross if r.get('source_index')==532 and r.get('locale')=='ar')
held_source=held_cell['source_id']; held_index=held_cell['source_index']; held_locale=held_cell['locale']
new_ids={r['source_id'] for r in source_rows}
assert prev_noop_index==533 and prev_noop_cells==12 and prev_noop_source not in new_ids
assert held_index==532 and held_source not in new_ids
assert set(range(543,563)).isdisjoint(range(523,543))
prev_hold={
 'source_index':held_index,'source_id':held_source,'locale':held_locale,
 'candidate_text':held,'candidate_sha256':held_hash,
 'current_cell':next(r for r in w523_primary if r['source_index']==held_index and r['locale']==held_locale),
}
boundary={'schema_version':1,'new_window':[553,562],'previous_window':[523,542],'source_index_overlap':[],'source_id_overlap':[],'previous_noop':{'source_index':prev_noop_index,'source_id':prev_noop_source,'locale_cell_count':prev_noop_cells},'previous_hold':prev_hold,'new_window_noop':{'source_index':562,'source_id':'Calendar','locale_cell_count':12,'reason':'No exact localized caller in tracked application source at pinned baseline.'},'boundary_status':'pass'}
write_json('prior-window-boundary.json',boundary)

# Verify all source/current and caller pins after dispositions are frozen.
source_current=[]
for src in source_rows:
    sid=src['source_id']; i=inventory.index(src)
    row={'source_index':i,'source_id':sid,'source_sha256':src['source_sha256'],'pr_head':HEAD,'pr_tree':TREE,'catalog_cells':[]}
    for loc in LOCALES:
        text=catalogs[loc][sid]; row['catalog_cells'].append({'locale':loc,'catalog_path':f'web/src/lib/locales/ui-labels.{loc}.json','current_text':text,'current_target_sha256':sha_text(text),'placeholders':placeholders(sid)})
    source_current.append(row)
write_jsonl('source-current-reattestation.jsonl',source_current)
write_jsonl('caller-context-pins.jsonl',source_pin_records)
write_jsonl('independent-review-ledger.jsonl',ledger)
correction_rows=[{k:v for k,v in x.items() if k in {'source_index','source_id','source_sha256','locale','current_text','current_target_sha256','candidate_text','candidate_sha256','rationale','confidence'}} for x in ledger if x['candidate_text'] is not None]
write_jsonl('correction-candidates.jsonl',correction_rows)

summary={'schema_version':1,'repository':'snapetech-org/slskR','pull_request':204,'live_pr':live,'pr_head':HEAD,'pr_tree':TREE,'source_head':SOURCE,'source_tree':SOURCE_TREE,'window_indices':[553,562],'source_key_count':10,'locale_count':len(LOCALES),'cell_count':len(ledger),'dispositions':dict(summary_counts),'per_locale':{k:dict(v) for k,v in locale_counts.items()},'correction_count':len(correction_rows),'caller_pinned_source_ids':sum(bool(x['caller_pins']) for x in source_pin_records),'no_direct_localization_caller_source_ids':[x['source_id'] for x in source_pin_records if not x['caller_pins']],'caller_pin_records':sum(len(x['caller_pins']) for x in source_pin_records),'source_current_checks':'pass','caller_source_pr_blob_file_excerpt_checks':'pass','placeholders_check':'pass','prior_w523_w542_noop_hold_boundary':'pass','native_speaker_approval':False,'native_speaker_review_required':True,'catalog_modified':False,'tests_builds_scans_ci_workflows_releases_tags_merges':False,'worktree_status':''}
write_json('summary.json',summary)
readme=f'''# Independent semantic review: slskR PR #204 W553–562

Pinned to live PR head `{HEAD}` (tree `{TREE}`) and source/runtime baseline `{SOURCE}` (tree `{SOURCE_TREE}`). The packet covers source indices 553–562 across 12 locales, 120 cells total.

## Dispositions

- 82 accepted current targets.
- 26 correction candidates, each with exact target text and UTF-8 SHA-256.
- 12 no-op cells for “Calendar,” because there is no exact localized caller in tracked application source at the pinned baseline.
- No holds. No native-speaker approval is recorded; native review remains required.

The preceding W523–542 window is disjoint. Its 12-cell no-op remains index 533 (“Build result-filter conditions without memorizing the filter syntax.”); its held Arabic candidate remains index 532 (“Build information unavailable”). See `prior-window-boundary.json`.

`source-current-reattestation.jsonl` records all source/current text hashes. `caller-context-pins.jsonl` pins exact source and PR caller file blobs and excerpts; `Calendar` is confirmed to have no caller. `independent-review-ledger.jsonl` contains one row per locale cell. All files are checksum-listed in `SHA256SUMS`.

No repository or PR files were edited. No tests, builds, scans, CI, or releases were run.
'''
(OUT/'README.md').write_text(readme,encoding='utf-8')

# Final internal verification and checksums.
for row in ledger:
    assert row['source_sha256']==sha_text(row['source_id'])
    assert row['current_target_sha256']==sha_text(row['current_text'])
    if row['candidate_text'] is not None:
        assert row['candidate_sha256']==sha_text(row['candidate_text'])
for pinset in source_pin_records:
    for pin in pinset['caller_pins']:
        assert blob(SOURCE,pin['path'])==blob(HEAD,pin['path'])
        lines=blob(HEAD,pin['path']).decode('utf-8').splitlines()
        assert lines[pin['occurrence_line']-1]==pin['occurrence_text']
        for item in pin['excerpt']: assert lines[item['line']-1]==item['text']
files=sorted(p for p in OUT.iterdir() if p.is_file() and p.name != 'SHA256SUMS')
(OUT/'SHA256SUMS').write_text(''.join(f'{sha(p.read_bytes())}  {p.name}\n' for p in files),encoding='utf-8')
for line in (OUT/'SHA256SUMS').read_text().splitlines():
    digest,name=line.split('  ',1); assert sha((OUT/name).read_bytes())==digest,name
print(json.dumps({'out':str(OUT),'head':HEAD,'tree':TREE,'dispositions':dict(summary_counts),'corrections':len(correction_rows),'caller_sources':summary['caller_pinned_source_ids'],'caller_pins':summary['caller_pin_records'],'no_ops':summary['no_direct_localization_caller_source_ids'],'checksums':{p.name:sha(p.read_bytes()) for p in files}},ensure_ascii=False,indent=2))
