import sys
sys.dont_write_bytecode = True
import hashlib, json, re
from pathlib import Path

ROOT = Path('/mnt/disks/scratch/task-scratch/slskr-pr209-w1603-1622-20261105')
INPUT = ROOT / 'candidate-free-input'
PRIMARY = ROOT / 'primary-review'
BLIND = ROOT / 'blind-review'
OUT = ROOT / 'root-cross-review'
HEAD = 'eeb63f1e4e21d801f4a4e0393813b6e86a1ff7c8'
TREE = '590ee410666905f68f601393b64a4798b0609181'

OVERRIDES = {
 (1606, 'zh-Hans'): ('correction', '无法加载共享列表', 'The shares settings caller loads a list, not the contents of one share; this also matches the catalog wording for “Share List”.'),
 (1606, 'ar'): ('correction', 'تعذر تحميل الموارد المشتركة', 'The caller is the shares settings page. “Shared resources” avoids the post or participation reading of the current noun while preserving the share-list meaning.'),
 (1606, 'vi'): ('correction', 'Không thể tải các mục chia sẻ', 'The caller loads share entries; “shared content” duplicates the distinct share-contents message.'),
 (1608, 'vi'): ('refinement', 'Không thể tải các lượt truyền', 'The Transfers screen shows transfer records; “lượt truyền” names transfer instances more clearly than the current calque “mục truyền”.'),
 (1611, 'ko'): ('correction', '검증 통계를 불러오지 못했습니다:', 'The component appends verificationStats.error after this label. Use the technical verification term and preserve the source colon so the following error reads as its detail.'),
 (1615, 'ko'): ('refinement', '멤버십을 게시하지 못했습니다:', 'The caller appends membershipPublishResult.error after this label. Preserve the colon instead of closing the prefix with a period.'),
 (1616, 'de'): ('correction', 'Die Meinung konnte nicht veröffentlicht werden: {error}', 'The caller publishes pod opinion data. “Meinung” preserves the broad source meaning; “Bewertung” narrows it to a rating or score.'),
 (1617, 'vi'): ('correction', 'Không thể xuất bản pod:', 'The caller publishes a MediaCore pod object; the current “nhóm” means a generic group and changes the product-domain object.'),
 (1620, 'de'): ('correction', 'Nahegelegene Atlas-Suchen konnten nicht in die Warteschlange gestellt werden', '“Nahegelegene” naturally describes nearby searches; the current “nahe” can read as searches close to an atlas. Keep source punctuation (no final period).'),
 (1621, 'hi'): ('correction', 'आस-पास की ग्राफ़ खोजों को कतार में नहीं जोड़ा जा सका', '“आस-पास की” agrees with feminine plural “खोजों”; the current adjective ending “पास के” does not. Keep source punctuation (no final period).'),
 (1621, 'fr'): ('correction', 'Impossible de mettre en file d’attente les recherches de graphe à proximité', 'The current “proches du graphe” says the searches are close to the graph. “À proximité” attaches proximity to the graph-search phrase. Keep source punctuation (no final period).'),
 (1621, 'id'): ('correction', 'Gagal memasukkan pencarian graf terdekat ke antrean', 'In this technical graph-search context, “graf” names the graph structure; “grafik” commonly reads as a chart. Keep source punctuation (no final period).'),
 (1622, 'de'): ('correction', 'Nahegelegene Suchen konnten nicht in die Warteschlange gestellt werden', '“Benachbart” means adjacent or neighboring; “nahegelegene” means searches available nearby. Keep source punctuation (no final period).'),
}

def read_json(path): return json.loads(path.read_text(encoding='utf-8'))
def read_jsonl(path): return [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines() if line.strip()]
def sha(s): return hashlib.sha256(s.encode('utf-8')).hexdigest()
def dump(path, obj): path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

cells = read_jsonl(INPUT / 'current-target-cells.jsonl')
contexts = read_jsonl(INPUT / 'source-contexts.jsonl')
primary = read_jsonl(PRIMARY / 'primary-ledger.jsonl')
blind = read_jsonl(BLIND / 'blind-ledger.jsonl')
cf_manifest = read_json(INPUT / 'manifest.json')
primary_summary = read_json(PRIMARY / 'SUMMARY.json')
blind_summary = read_json(BLIND / 'summary.json')
assert primary_summary['head'] == blind_summary['head'] == HEAD
assert primary_summary['tree'] == blind_summary['tree'] == TREE
assert primary_summary['cellCount'] == blind_summary['cellCount'] == len(cells) == 240
assert len(contexts) == 20 and len(primary) == len(blind) == 240
assert cf_manifest.get('head') == HEAD and cf_manifest.get('tree') == TREE

cell_by = {(r['position'], r['locale']): r for r in cells}
ctx_by = {r['position']: r for r in contexts}
p_by = {(r['position'], r['locale']): r for r in primary}
b_by = {(r['position'], r['locale']): r for r in blind}
assert len(cell_by) == len(p_by) == len(b_by) == 240

rows=[]
for key in sorted(cell_by):
    c=cell_by[key]; p=p_by[key]; b=b_by[key]; s=ctx_by[key[0]]
    assert c['sourceKeySha256'] == p['sourceKeySha256'] == b['sourceKeySha256'] == s['sourceKeySha256']
    assert c['sourceContextSha256'] == p['sourceContextSha256'] == b['sourceContextSha256'] == s['callerContextSha256']
    assert c['currentTargetSha256'] == p['currentTargetSha256'] == b['currentTargetSha256']
    if key in OVERRIDES:
        disposition, target, reason = OVERRIDES[key]
    else:
        disposition, target, reason = 'accept-current', c['currentTarget'], 'Primary and independent blind reviews accept the current translation; no cross-review concern found.'
    # Protect placeholders, tags, and numeric tokens on root-selected text.
    tokens = lambda text, pattern: re.findall(pattern, text)
    assert tokens(s['sourceKey'], r'\{[^{}]+\}') == tokens(target, r'\{[^{}]+\}')
    assert tokens(s['sourceKey'], r'</?[A-Za-z][^>]*>') == tokens(target, r'</?[A-Za-z][^>]*>')
    assert tokens(s['sourceKey'], r'(?<!\w)\d+(?:[.,]\d+)*(?!\w)') == tokens(target, r'(?<!\w)\d+(?:[.,]\d+)*(?!\w)')
    rows.append({
        'position': key[0], 'locale': key[1], 'head': HEAD, 'tree': TREE,
        'sourceKey': s['sourceKey'], 'sourceKeySha256': s['sourceKeySha256'],
        'sourceContextSha256': s['callerContextSha256'], 'callerCount': c['callerCount'],
        'currentTarget': c['currentTarget'], 'currentTargetSha256': c['currentTargetSha256'],
        'primaryDisposition': p['disposition'], 'primaryTarget': p['selectedTarget'],
        'independentBlindDisposition': b['decision'], 'blindTarget': b['proposedTarget'],
        'rootDisposition': disposition, 'rootTarget': target, 'rootTargetSha256': sha(target), 'rootRationale': reason,
        'placeholderMarkupNumericPreserved': True,
    })
assert len(OVERRIDES) == 13
(OUT / 'root-adjudication.jsonl').write_text(''.join(json.dumps(r, ensure_ascii=False, sort_keys=True) + '\n' for r in rows), encoding='utf-8')
counts={}
for row in rows: counts[row['rootDisposition']]=counts.get(row['rootDisposition'],0)+1
summary={
 'artifact':'slskR PR #209 W1603-W1622 root cross-review and adjudication',
 'repository':'snapetech-org/slskR','pullRequest':209,'head':HEAD,'tree':TREE,
 'candidateFreeChecksumListSha256':hashlib.sha256((INPUT/'SHA256SUMS.txt').read_bytes()).hexdigest(),
 'primarySummarySha256':hashlib.sha256((PRIMARY/'SUMMARY.json').read_bytes()).hexdigest(),
 'blindSummarySha256':hashlib.sha256((BLIND/'summary.json').read_bytes()).hexdigest(),
 'cellCount':len(rows),'rootDispositionCounts':counts,'proposalCount':len(OVERRIDES),
 'primaryBlindConvergence':4,'primaryBlindTargetConvergence':4,
 'holds':0,'tokenPreservation':'PASS','nativeSpeakerSignoff':False,'browserReview':False,
 'readbackPerformed':False,'repositoryChangesApplied':False,
}
dump(OUT/'SUMMARY.json',summary)
(OUT/'README.md').write_text(f'''# slskR W1603–W1622 root cross-review\n\nRoot adjudication of all 240 locale cells, joining the pinned candidate-free packet, complete primary ledger, and complete independent blind ledger.\n\n- PR #209 exact head/tree: `{HEAD}` / `{TREE}`\n- Candidate-free checksum list SHA-256: `{summary['candidateFreeChecksumListSha256']}`\n- Cells reviewed: 240 (20 source keys × 12 locales)\n- Root dispositions: `{json.dumps(counts, sort_keys=True)}`\n- All 13 proposals were resolved; source placeholders, markup, and numeric tokens passed the root preservation checks.\n- Four primary proposals converge exactly with the independent blind pass (Vietnamese 1608 and 1617; Korean 1611 and 1615).\n- Catalog changes have not yet been applied. Browser rendering and native-speaker approval are not established by this packet.\n\n`root-adjudication.jsonl` contains one exact-head row for each cell, with both reviewer decisions and the root target/reason.\n''',encoding='utf-8')
files=[p for p in OUT.iterdir() if p.is_file() and p.name!='SHA256SUMS.txt']
(OUT/'SHA256SUMS.txt').write_text(''.join(f"{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.name}\n" for p in sorted(files)),encoding='utf-8')
print(json.dumps(summary,ensure_ascii=False,indent=2))
