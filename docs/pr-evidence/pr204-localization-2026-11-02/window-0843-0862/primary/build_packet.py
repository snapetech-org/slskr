import collections, hashlib, json, re, subprocess
from pathlib import Path

ROOT = Path('/home/keith/Documents/code/task-worktrees/localization-20261102-slskr')
OUT = Path('/mnt/disks/scratch/task-scratch/slskr-pr204-window-0843-0862-primary-20261102')
REPO = 'snapetech-org/slskR'
PR = 204
BRANCH = 'codex/slskr-l10n-audit-20261030'
HEAD_EXPECTED = 'b52b7c9abd112328a70d9e811d3b6aa2d4feb8e6'
TREE_EXPECTED = 'd7a46bce75c76e3a74736b85175f7fa412324f39'
LOCALES = ['ar','de','es','fr','hi','id','ja','ko','pt-BR','vi','zh-Hans','zh-Hant']
START, END = 842, 861

PROPOSALS = {
 (842,'hi'):'कनेक्टेड क्लाइंट (',
 (843,'es'):'Clientes slskr conectados para la sincronización de hashes',
 (843,'ja'):'ハッシュ同期用の接続済み slskr クライアント',
 (843,'zh-Hans'):'用于哈希同步的已连接 slskr 客户端',
 (843,'zh-Hant'):'用於雜湊同步的已連線 slskr 用戶端',
 (844,'ar'):'الاتصال غير قائم.',
 (844,'de'):'Die Verbindung besteht nicht.',
 (844,'es'):'La conexión no está establecida.',
 (844,'fr'):'La connexion n’est pas établie.',
 (844,'hi'):'कनेक्शन स्थापित नहीं है।',
 (844,'id'):'Koneksi belum terbentuk.',
 (844,'ja'):'接続は確立されていません。',
 (844,'ko'):'연결이 설정되지 않았습니다.',
 (844,'pt-BR'):'A conexão não está estabelecida.',
 (844,'vi'):'Kết nối chưa được thiết lập.',
 (844,'zh-Hans'):'连接尚未建立。',
 (844,'zh-Hant'):'連線尚未建立。',
 (845,'ar'):'الاتصال قائم.',
 (845,'de'):'Die Verbindung besteht.',
 (845,'es'):'La conexión está establecida.',
 (845,'fr'):'La connexion est établie.',
 (845,'hi'):'कनेक्शन स्थापित है।',
 (845,'id'):'Koneksi telah terbentuk.',
 (845,'ja'):'接続が確立されています。',
 (845,'ko'):'연결이 설정되었습니다.',
 (845,'pt-BR'):'A conexão está estabelecida.',
 (845,'vi'):'Kết nối đã được thiết lập.',
 (845,'zh-Hans'):'连接已建立。',
 (845,'zh-Hant'):'連線已建立。',
 (849,'hi'):'लाइव खोज अपडेट से कनेक्ट हो रहा है। आपकी लोड की गई खोजें नीचे उपलब्ध हैं।',
 (852,'ar'):'مهلة الاتصال (مللي ثانية)',
 (852,'de'):'Verbindungszeitlimit (Millisekunden)',
 (852,'es'):'Tiempo de espera de conexión (milisegundos)',
 (852,'fr'):'Délai d’expiration de la connexion (millisecondes)',
 (852,'hi'):'कनेक्शन समय-सीमा (मिलीसेकंड)',
 (852,'id'):'Batas waktu koneksi (milidetik)',
 (852,'ja'):'接続タイムアウト（ミリ秒）',
 (852,'ko'):'연결 시간 제한(밀리초)',
 (852,'pt-BR'):'Tempo limite da conexão (milissegundos)',
 (852,'vi'):'Thời gian chờ kết nối (mili giây)',
 (852,'zh-Hans'):'连接超时时间（毫秒）',
 (852,'zh-Hant'):'連線逾時時間（毫秒）',
 (858,'hi'):'सहमति-आधारित सिफ़ारिशें',
 (861,'ar'):'الإجماع على الإجراءات المدمرة',
 (861,'de'):'Konsens für destruktive Aktionen',
 (861,'hi'):'विनाशकारी कार्रवाइयों के लिए सहमति',
 (861,'ja'):'破壊的な操作に対する合意',
 (861,'ko'):'파괴적 작업에 대한 합의',
 (861,'vi'):'Đồng thuận cho các thao tác mang tính phá hủy',
 (861,'zh-Hans'):'破坏性操作的共识',
 (861,'zh-Hant'):'破壞性操作的共識',
}
RATIONALES = {
 842:'Hindi ग्राहक means customers; this label counts software clients, so use the established transliteration क्लाइंट.',
 843:'The current wording reads as an action or imperative in these locales; recast it as a noun phrase for already connected clients used for hash synchronization.',
 844:'This is diagnostic evidence for a false Soulseek connection boolean. Translate the connection as not established instead of calling the state untrue or incorrect.',
 845:'This is diagnostic evidence for a true Soulseek connection boolean. Use the natural established-connection wording paired with the false case.',
 849:'Hindi sentence punctuation uses danda consistently.',
 852:'This is the label for an FTP connection-timeout number field. Make the unit explicit and the label natural in each locale.',
 858:'सर्वसम्मत can mean unanimous. Use recommendations based on consensus without claiming unanimity.',
 861:'This is a shared-library policy switch for archive or expiry operations. Use product-operation wording instead of language that suggests violent or destructive behavior.'
}

def run(args, cwd=ROOT, text=True):
    return subprocess.check_output(args, cwd=cwd, text=text)

def sha(data):
    if isinstance(data, str):
        data = data.encode()
    return hashlib.sha256(data).hexdigest()

def jdump(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')

def jlines(path, rows):
    path.write_text(''.join(json.dumps(x, ensure_ascii=False, sort_keys=True) + '\n' for x in rows))

pr = json.loads(run(['gh','pr','view',str(PR),'--repo',REPO,'--json','state,isDraft,headRefOid,headRefName,baseRefOid,url']))
assert pr['state'] == 'OPEN' and pr['isDraft'] is True
assert pr['headRefOid'] == HEAD_EXPECTED and pr['headRefName'] == BRANCH
tree_api = run(['gh','api',f'repos/{REPO}/commits/{pr["headRefOid"]}','--jq','.commit.tree.sha']).strip()
remote = run(['git','ls-remote','taskgithub',f'refs/heads/{BRANCH}']).split()[0]
head = run(['git','rev-parse','HEAD']).strip()
tree = run(['git','rev-parse','HEAD^{tree}']).strip()
branch = run(['git','branch','--show-current']).strip()
status = run(['git','status','--porcelain']).strip()
assert (head, tree, branch, status, tree_api, remote) == (HEAD_EXPECTED,TREE_EXPECTED,BRANCH,'',TREE_EXPECTED,HEAD_EXPECTED)

keys = None
catalogs = {}
catalog_pins = []
for locale in LOCALES:
    rel = f'web/src/lib/locales/ui-labels.{locale}.json'
    raw = subprocess.check_output(['git','show',f'HEAD:{rel}'],cwd=ROOT)
    obj = json.loads(raw)
    assert len(obj) == 5441
    this_keys = sorted(obj)
    if keys is None:
        keys = this_keys
    assert this_keys == keys
    catalogs[locale] = obj
    catalog_pins.append({'locale':locale,'path':rel,'blob':run(['git','rev-parse',f'HEAD:{rel}']).strip(),'fileSha256':sha(raw),'keyCount':len(obj)})

assert len(keys) == 5441
assert all(0 <= i < len(keys) for i in (START-1,END+1))
source_ids = keys[START:END+1]
assert len(source_ids) == 20 and source_ids[0] == 'Connected Clients (' and source_ids[-1] == 'Consensus for destructive actions'

cells = []
for index in range(START,END+1):
    source = keys[index]
    for locale in LOCALES:
        target = catalogs[locale][source]
        proposal = PROPOSALS.get((index,locale))
        final = proposal if proposal is not None else target
        cells.append({
            'sourceIndex':index,
            'sourceId':source,
            'sourceSha256':sha(source),
            'locale':locale,
            'currentTarget':target,
            'currentTargetSha256':sha(target),
            'disposition':'propose-correction' if proposal is not None else 'accept-current',
            'proposedTarget':proposal,
            'proposedTargetSha256':sha(proposal) if proposal is not None else None,
            'reviewedFinal':final,
            'reviewedFinalSha256':sha(final),
            'rationale':RATIONALES.get(index,'Current translation preserves the source meaning and product terminology in its exact caller context.')
        })
assert len(cells) == 240

# Reuse the prior independent connection-state review only for exact hash matches.
prior_path = ROOT/'docs/pr-evidence/pr204-localization-2026-11-02/connection-state-review/review-cells.jsonl'
prior = [json.loads(x) for x in prior_path.read_text().splitlines()]
prior_rows = []
for source in ('Connecting','Connection Failed'):
    matching = [r for r in prior if r['sourceKey'] == source]
    assert len(matching) == 12
    for row in matching:
        locale = row['locale']
        index = keys.index(source)
        target = catalogs[locale][source]
        assert row['crossReviewDisposition'] == 'accept'
        assert row['currentTargetSha256'] == row['recommendedTargetSha256'] == sha(target)
        prior_rows.append({'sourceIndex':index,'sourceId':source,'locale':locale,'currentTargetSha256':sha(target),'priorCrossReviewDisposition':'accept','priorEvidencePath':'docs/pr-evidence/pr204-localization-2026-11-02/connection-state-review/review-cells.jsonl','priorReviewedHead':json.loads((ROOT/'docs/pr-evidence/pr204-localization-2026-11-02/connection-state-review/review-summary.json').read_text())['pullRequest']['headRefOid']})

# Reattest all production source-code references and their surrounding context from exact HEAD blobs.
file_list = run(['git','ls-files'],text=True).splitlines()
callers = []
caller_gaps = []
for source in source_ids:
    hits = 0
    for rel in file_list:
        if not rel.startswith('web/src/') or not rel.endswith(('.js','.jsx','.ts','.tsx')):
            continue
        if '.test.' in rel or '/__tests__/' in rel or '/test/' in rel:
            continue
        raw = subprocess.check_output(['git','show',f'HEAD:{rel}'],cwd=ROOT,stderr=subprocess.DEVNULL)
        try:
            lines = raw.decode('utf-8').splitlines()
        except UnicodeDecodeError:
            continue
        for n,line in enumerate(lines,1):
            if source not in line:
                continue
            hits += 1
            start, stop = max(1,n-2), min(len(lines),n+2)
            callers.append({
                'sourceIndex':keys.index(source),'sourceId':source,'path':rel,
                'fileBlob':run(['git','rev-parse',f'HEAD:{rel}']).strip(),
                'fileSha256':sha(raw),'line':n,'lineSha256':sha(line),
                'contextStartLine':start,'contextLines':[{'line':i,'text':lines[i-1]} for i in range(start,stop+1)],
                'surfaceLine':line.strip()
            })
    if hits == 0:
        caller_gaps.append({'sourceIndex':keys.index(source),'sourceId':source,'reason':'No production caller containing this source text was found at the exact PR head; review is limited to the self-contained status label and catalog parity.'})

boundaries = []
for index in (START-1,END+1):
    source = keys[index]
    for locale in LOCALES:
        target = catalogs[locale][source]
        boundaries.append({'sourceIndex':index,'sourceId':source,'sourceSha256':sha(source),'locale':locale,'target':target,'targetSha256':sha(target)})

placeholder_re = re.compile(r'\{([A-Za-z][A-Za-z0-9_]*)\}')
tag_re = re.compile(r'</?[A-Za-z][^>]*>')
assert all(placeholder_re.findall(c['sourceId']) == placeholder_re.findall(c['currentTarget']) == placeholder_re.findall(c['reviewedFinal']) for c in cells)
assert all(tag_re.findall(c['sourceId']) == tag_re.findall(c['currentTarget']) == tag_re.findall(c['reviewedFinal']) for c in cells)
soulseek_cells = [c for c in cells if 'Soulseek' in c['sourceId']]
assert all('Soulseek' in c['currentTarget'] and 'Soulseek' in c['reviewedFinal'] for c in soulseek_cells)
assert len(PROPOSALS) == sum(c['disposition']=='propose-correction' for c in cells)

jdump(OUT/'live-head.json',{'repository':REPO,'pullRequest':PR,'state':pr['state'],'isDraft':pr['isDraft'],'url':pr['url'],'branch':BRANCH,'head':head,'tree':tree,'apiTree':tree_api,'remoteHead':remote,'worktreeStatus':status,'baseRefOid':pr['baseRefOid']})
jlines(OUT/'catalog-pins.jsonl',catalog_pins)
jlines(OUT/'review-ledger.jsonl',cells)
jlines(OUT/'source-caller-pins.jsonl',callers)
jlines(OUT/'caller-gaps.jsonl',caller_gaps)
jlines(OUT/'boundary-pins.jsonl',boundaries)
jlines(OUT/'prior-review-reattestation.jsonl',prior_rows)
source_rows = [{'sourceIndex':i,'sourceId':keys[i],'sourceSha256':sha(keys[i])} for i in range(START-1,END+2)]
jlines(OUT/'source-window-and-boundaries.jsonl',source_rows)

counts = collections.Counter(c['disposition'] for c in cells)
summary = {
 'repository':REPO,'pullRequest':PR,'window':'W843-W862','zeroBasedSourceIndexInclusive':[START,END],
 'head':head,'tree':tree,'branch':BRANCH,'sourceCount':20,'cellCount':len(cells),
 'counts':dict(counts),'correctionCandidateCount':len(PROPOSALS),'holdCount':0,
 'catalogKeyCount':len(keys),'catalogsReattested':len(catalogs),'callerFiles':len({x['path'] for x in callers}),
 'callerPins':len(callers),'callerGaps':caller_gaps,'priorReviewReusedCells':len(prior_rows),
 'placeholderMismatches':0,'markupMismatches':0,'protectedSoulseekMismatches':0,
 'nativeSpeakerApproval':False,'headedBrowserReview':False,'testsBuildsCiRun':False,
 'repositoryModified':False,
 'sourceIds':source_ids,
 'boundarySourceIndices':[START-1,END+1],
 'boundarySourceIds':[keys[START-1],keys[END+1]],
 'localeOrder':LOCALES,
}
jdump(OUT/'summary.json',summary)
readme = f'''# slskR PR #204 primary semantic review — W843–W862

Reviewed 20 source IDs × 12 locales (240 cells) at exact OPEN/DRAFT PR head {head}, tree {tree}. The 12 catalogs were reattested at 5,441 identical ordered keys. All found production caller references and context lines were pinned to exact HEAD blobs. One catalog source, Connecting to Soulseek…, has no production text caller at this exact head; its self-contained status wording is reviewed, and the gap is recorded. Boundary sources {START-1} ({keys[START-1]}) and {END+1} ({keys[END+1]}) were recorded.

Primary dispositions: {dict(counts)}. The two earlier connection-state records, Connecting and Connection Failed, were reused only where all 12 current target hashes exactly matched the prior independent review evidence; this is recorded in prior-review-reattestation.jsonl.

The candidate edits concern the Hindi software-client noun, four connected-client/hash-sync phrasings, both diagnostic connection-state sentences, Hindi sentence punctuation, explicit timeout units, Hindi consensus terminology, and destructive-operation wording. No placeholders or markup were changed; Soulseek remains verbatim.

This packet is static machine semantic review. It does not establish native-speaker approval or current-head headed-browser acceptance. No repository files were modified; no tests, builds, scans, or CI ran.
'''
(OUT/'README.md').write_text(readme)
files = sorted(p for p in OUT.iterdir() if p.is_file() and p.name not in ('SHA256SUMS','manifest.json'))
(OUT/'SHA256SUMS').write_text(''.join(f'{sha(p.read_bytes())}  {p.name}\n' for p in files))
manifest = {'repository':REPO,'pullRequest':PR,'window':'W843-W862','head':head,'tree':tree,'branch':BRANCH,'sourceCount':20,'cellCount':240,'counts':dict(counts),'files':[{'path':p.name,'bytes':p.stat().st_size,'sha256':sha(p.read_bytes())} for p in files],'sha256SumsSha256':sha((OUT/'SHA256SUMS').read_bytes())}
jdump(OUT/'manifest.json',manifest)
print(json.dumps({'out':str(OUT),'summary':summary,'sha256SumsSha256':sha((OUT/'SHA256SUMS').read_bytes())},ensure_ascii=False))
