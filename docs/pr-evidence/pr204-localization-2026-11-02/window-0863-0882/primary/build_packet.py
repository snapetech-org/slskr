import collections, hashlib, json, re, subprocess
from pathlib import Path

ROOT = Path('/home/keith/Documents/code/task-worktrees/localization-20261102-slskr')
OUT = Path('/mnt/disks/scratch/task-scratch/slskr-pr204-window-0863-0882-primary-20261102')
REPO = 'snapetech-org/slskR'
PR = 204
BRANCH = 'codex/slskr-l10n-audit-20261030'
HEAD_EXPECTED = '72597bcf3c71f586040cd882506dff8dcbf6c804'
TREE_EXPECTED = subprocess.check_output(['git','rev-parse',f'{HEAD_EXPECTED}^{{tree}}'],cwd=ROOT,text=True).strip()
LOCALES = ['ar','de','es','fr','hi','id','ja','ko','pt-BR','vi','zh-Hans','zh-Hant']
START, END = 862, 881

PROPOSALS = {
 (862,'ar'):'شبكة منخفضة الحمل',
 (862,'de'):'Netzwerk mit geringer Auslastung',
 (862,'es'):'Red de bajo impacto',
 (862,'fr'):'Réseau à faible impact',
 (862,'hi'):'कम भार वाला नेटवर्क',
 (862,'id'):'Jaringan dengan beban rendah',
 (862,'ja'):'低負荷ネットワーク',
 (862,'ko'):'저부하 네트워크',
 (862,'pt-BR'):'Rede de baixo impacto',
 (862,'vi'):'Mạng giảm tải',
 (862,'zh-Hans'):'低负载网络',
 (862,'zh-Hant'):'低負載網路',
 (863,'ar'):'اكتشاف محدود لتجزئات الأقران خارج slskr',
 (863,'de'):'Gezielte Hash-Erkennung bei Peers außerhalb von slskr',
 (863,'es'):'Búsqueda limitada de hashes entre pares ajenos a slskr',
 (863,'fr'):'Découverte limitée des hachages auprès de pairs hors slskr',
 (863,'hi'):'slskr से बाहर के साथियों से हैश की सीमित खोज',
 (863,'id'):'Pencarian hash terbatas dari peer di luar slskr',
 (863,'ja'):'slskr 以外のピアからハッシュを限定的に検出',
 (863,'ko'):'slskr 외부 피어의 해시를 제한적으로 검색',
 (863,'pt-BR'):'Busca limitada de hashes de pares fora do slskr',
 (863,'vi'):'Phát hiện hash có giới hạn từ peer ngoài slskr',
 (863,'zh-Hans'):'有限度地发现来自 slskr 以外对等节点的哈希',
 (863,'zh-Hant'):'有限度地探索來自 slskr 以外對等節點的雜湊',
 (866,'pt-BR'):'Conteúdo',
 (869,'ar'):'شبكة علاقات المحتوى',
 (869,'de'):'Inhaltsgraph',
 (869,'es'):'Grafo de contenido',
 (869,'fr'):'Graphe de contenu',
 (869,'hi'):'सामग्री संबंध ग्राफ़',
 (869,'id'):'Graf Relasi Konten',
 (869,'pt-BR'):'Grafo de conteúdo',
 (869,'vi'):'Đồ thị quan hệ nội dung',
 (869,'zh-Hans'):'内容关系图谱',
 (869,'zh-Hant'):'內容關係圖譜',
 (870,'es'):'ID de contenido',
 (871,'es'):'ID de contenido (p. ej., content:audio:album:mb-id)',
 (871,'hi'):'सामग्री आईडी (उदाहरण: content:audio:album:mb-id)',
 (871,'id'):'ID konten (misalnya, content:audio:album:mb-id)',
 (871,'vi'):'ID nội dung (ví dụ: content:audio:album:mb-id)',
 (871,'zh-Hans'):'内容 ID（例如：content:audio:album:mb-id）',
 (871,'zh-Hant'):'內容 ID（例如：content:audio:album:mb-id）',
 (872,'es'):'ID de contenido (p. ej., content:audio:album:mb-release-id)',
 (872,'fr'):'ID de contenu (par exemple, content:audio:album:mb-release-id)',
 (872,'hi'):'सामग्री आईडी (उदाहरण: content:audio:album:mb-release-id)',
 (872,'id'):'ID konten (misalnya, content:audio:album:mb-release-id)',
 (872,'zh-Hans'):'内容 ID（例如：content:audio:album:mb-release-id）',
 (872,'zh-Hant'):'內容 ID（例如：content:audio:album:mb-release-id）',
 (875,'es'):'Asignaciones de ID de contenido y estadísticas de dominio',
 (880,'ar'):'آراء حول المحتوى',
 (880,'de'):'Meinungen zum Inhalt',
 (880,'es'):'Opiniones sobre el contenido',
 (880,'hi'):'सामग्री के बारे में राय',
 (880,'id'):'Pendapat tentang konten',
 (880,'ko'):'콘텐츠에 대한 의견',
 (880,'pt-BR'):'Opiniões sobre o conteúdo',
 (880,'vi'):'Ý kiến về nội dung',
}
RATIONALES = {
 862:'The caller labels a profile that minimizes public-network pressure and avoids aggressive retries. Use a clear low-load or low-impact label rather than a potentially political or vague sense of “conservative.”',
 863:'This is a Backfill Scheduler subtitle. “Conservative discovery” means limited/selective hash discovery from peers outside slskr; use a natural restriction term and preserve the product identifier.',
 866:'In Brazilian Portuguese, “contente” means happy; this is the Compatibility Dashboard tab for content, so use the noun “Conteúdo.”',
 869:'The caller and adjacent description explicitly identify a complete relationship graph for a ContentID. Use graph/relationship-graph terminology rather than a chart or generic diagram.',
 870:'Use the concise interface term “ID de contenido,” consistent with the technical identifier shown in the caller.',
 871:'The example is a literal Content ID syntax. Translate the explanatory label but preserve the exact token `content:audio:album:mb-id`.',
 872:'The example is a literal Content ID syntax. Translate the explanatory label but preserve the exact token `content:audio:album:mb-release-id`; keep the French label consistent with the neighboring Content ID field.',
 875:'The Spanish title should use the same concise localized term for Content ID as the adjacent field label.',
 880:'The section lists opinions about a content item. Use a natural “opinions about/on content” phrase rather than a compressed or reversed noun string.',
}

def run(args):
 return subprocess.check_output(args,cwd=ROOT,text=True).strip()
def sha(data):
 if isinstance(data,str): data=data.encode()
 return hashlib.sha256(data).hexdigest()
def jdump(path,value): path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
def jlines(path,rows): path.write_text(''.join(json.dumps(x,ensure_ascii=False,sort_keys=True)+'\n' for x in rows))

pr=json.loads(run(['gh','pr','view',str(PR),'--repo',REPO,'--json','state,isDraft,headRefOid,headRefName,baseRefOid,url']))
assert pr['state']=='OPEN' and pr['isDraft'] is True
assert pr['headRefOid']==HEAD_EXPECTED and pr['headRefName']==BRANCH
api_tree=run(['gh','api',f'repos/{REPO}/commits/{HEAD_EXPECTED}','--jq','.commit.tree.sha'])
remote=run(['git','ls-remote','taskgithub',f'refs/heads/{BRANCH}']).split()[0]
head=run(['git','rev-parse','HEAD']); tree=run(['git','rev-parse','HEAD^{tree}'])
branch=run(['git','branch','--show-current']); status=run(['git','status','--porcelain'])
assert (head,tree,branch,status,api_tree,remote)==(HEAD_EXPECTED,TREE_EXPECTED,BRANCH,'',TREE_EXPECTED,HEAD_EXPECTED)

catalogs={}; pins=[]; keyset=None
for locale in LOCALES:
 rel=f'web/src/lib/locales/ui-labels.{locale}.json'
 raw=subprocess.check_output(['git','show',f'HEAD:{rel}'],cwd=ROOT)
 obj=json.loads(raw); keys=sorted(obj)
 assert len(keys)==5441
 if keyset is None: keyset=keys
 assert keys==keyset
 catalogs[locale]=obj
 pins.append({'locale':locale,'path':rel,'blob':run(['git','rev-parse',f'HEAD:{rel}']),'fileSha256':sha(raw),'keyCount':len(obj)})
assert len(keyset)==5441
source_ids=keyset[START:END+1]
assert len(source_ids)==20
expected={862:'Conservative Network',863:'Conservative discovery of hashes from non-slskr peers',866:'Content',869:'Content Graph',870:'Content ID',871:'Content ID (e.g., content:audio:album:mb-id)',872:'Content ID (e.g., content:audio:album:mb-release-id)',874:'Content ID is required',875:'Content ID mappings and domain statistics',879:'Content Metadata',880:'Content Opinions'}
assert {i:keyset[i] for i in expected}==expected
proposal_sources={862:'Conservative Network',863:'Conservative discovery of hashes from non-slskr peers',866:'Content',869:'Content Graph',870:'Content ID',871:'Content ID (e.g., content:audio:album:mb-id)',872:'Content ID (e.g., content:audio:album:mb-release-id)',875:'Content ID mappings and domain statistics',880:'Content Opinions'}
assert all(keyset[i]==source for i,source in proposal_sources.items())
assert all(i in proposal_sources for i,_locale in PROPOSALS)
cells=[]
for index in range(START,END+1):
 source=keyset[index]
 for locale in LOCALES:
  current=catalogs[locale][source]
  proposal=PROPOSALS.get((index,locale))
  final=proposal if proposal is not None else current
  cells.append({'sourceIndex':index,'windowLabel':index+1,'sourceId':source,'sourceSha256':sha(source),'locale':locale,'currentTarget':current,'currentTargetSha256':sha(current),'disposition':'propose-correction' if proposal is not None else 'accept-current','proposedTarget':proposal,'proposedTargetSha256':sha(proposal) if proposal is not None else None,'reviewedFinal':final,'reviewedFinalSha256':sha(final),'rationale':RATIONALES.get(index,'The current value is understandable and consistent with its exact interface or validation context; protected identifiers remain intact.')})
assert len(cells)==240

# Pin only exact string-literal callers in production web source. This avoids false matches such as JSX .Content components.
tracked=run(['git','ls-files','web/src']).splitlines(); callers=[]; caller_gaps=[]
for index in range(START,END+1):
 source=keyset[index]; literal=re.compile(r'([\"\'])'+re.escape(source)+r'\1'); hits=0
 for rel in tracked:
  if not rel.endswith(('.js','.jsx','.ts','.tsx')) or '.test.' in rel or '/__tests__/' in rel or '/test/' in rel: continue
  raw=subprocess.check_output(['git','show',f'HEAD:{rel}'],cwd=ROOT,stderr=subprocess.DEVNULL)
  try: lines=raw.decode('utf-8').splitlines()
  except UnicodeDecodeError: continue
  for line_no,line in enumerate(lines,1):
   if not literal.search(line): continue
   hits+=1; start=max(1,line_no-2); end=min(len(lines),line_no+2)
   callers.append({'sourceIndex':index,'sourceId':source,'path':rel,'fileBlob':run(['git','rev-parse',f'HEAD:{rel}']),'fileSha256':sha(raw),'line':line_no,'lineSha256':sha(line),'contextStartLine':start,'contextLines':[{'line':i,'text':lines[i-1]} for i in range(start,end+1)],'surfaceLine':line.strip()})
 if hits==0: caller_gaps.append({'sourceIndex':index,'sourceId':source,'reason':'No exact source string-literal caller was found in production web/src at this PR head; review is limited to the self-contained catalog target.'})

boundaries=[]
for index in (START-1,END+1):
 source=keyset[index]
 for locale in LOCALES:
  target=catalogs[locale][source]
  boundaries.append({'sourceIndex':index,'sourceId':source,'sourceSha256':sha(source),'locale':locale,'target':target,'targetSha256':sha(target)})

placeholder=re.compile(r'\{([A-Za-z][A-Za-z0-9_]*)\}')
tag=re.compile(r'</?[A-Za-z][^>]*>')
placeholder_bad=[]; markup_bad=[]; literal_bad=[]
protected={
 863:['slskr'],
 871:['content:audio:album:mb-id'],
 872:['content:audio:album:mb-release-id'],
 873:['contentId','variantHash'],
 876:['JSON'],
}
for c in cells:
 if placeholder.findall(c['sourceId'])!=placeholder.findall(c['currentTarget']) or placeholder.findall(c['sourceId'])!=placeholder.findall(c['reviewedFinal']): placeholder_bad.append((c['sourceIndex'],c['locale']))
 if tag.findall(c['sourceId'])!=tag.findall(c['currentTarget']) or tag.findall(c['sourceId'])!=tag.findall(c['reviewedFinal']): markup_bad.append((c['sourceIndex'],c['locale']))
 for token in protected.get(c['sourceIndex'],[]):
  if token not in c['reviewedFinal']: literal_bad.append((c['sourceIndex'],c['locale'],token))
assert not placeholder_bad and not markup_bad and not literal_bad, (placeholder_bad,markup_bad,literal_bad)

jdump(OUT/'live-head.json',{'repository':REPO,'pullRequest':PR,'state':pr['state'],'isDraft':pr['isDraft'],'url':pr['url'],'branch':BRANCH,'head':head,'tree':tree,'apiTree':api_tree,'remoteHead':remote,'worktreeStatus':status,'baseRefOid':pr['baseRefOid']})
jlines(OUT/'catalog-pins.jsonl',pins); jlines(OUT/'review-ledger.jsonl',cells); jlines(OUT/'source-caller-pins.jsonl',callers); jlines(OUT/'caller-gaps.jsonl',caller_gaps); jlines(OUT/'boundary-pins.jsonl',boundaries)
jlines(OUT/'source-window-and-boundaries.jsonl',[{'sourceIndex':i,'windowLabel':i+1,'sourceId':keyset[i],'sourceSha256':sha(keyset[i])} for i in range(START-1,END+2)])
counts=collections.Counter(c['disposition'] for c in cells)
summary={'repository':REPO,'pullRequest':PR,'window':'W863-W882','zeroBasedSourceIndexInclusive':[START,END],'head':head,'tree':tree,'branch':BRANCH,'sourceCount':20,'cellCount':240,'counts':dict(counts),'candidateCorrectionCount':len(PROPOSALS),'holdCount':0,'catalogKeyCount':len(keyset),'catalogsReattested':len(catalogs),'callerFiles':len({x['path'] for x in callers}),'callerPins':len(callers),'callerGaps':caller_gaps,'placeholderMismatches':len(placeholder_bad),'markupMismatches':len(markup_bad),'protectedLiteralMismatches':len(literal_bad),'nativeSpeakerApproval':False,'headedBrowserReview':False,'testsBuildsScansCiRun':False,'repositoryModified':False,'sourceIds':source_ids,'boundarySourceIndices':[START-1,END+1],'boundarySourceIds':[keyset[START-1],keyset[END+1]],'localeOrder':LOCALES}
jdump(OUT/'summary.json',summary)
(OUT/'README.md').write_text(f'''# slskR PR #204 primary semantic review — W863–W882\n\nReviewed 20 source IDs × 12 locales (240 cells) at exact OPEN/DRAFT PR head {head}, tree {tree}. The twelve direct catalogs were reattested at 5,441 identical keys. Caller references use exact string literals from production web source; {len(callers)} line/context pins across {len({x['path'] for x in callers})} files are retained.\n\nPrimary dispositions: {dict(counts)}. The window includes corrections to the network-profile and Backfill Scheduler terms, the relationship-graph title, Brazilian Portuguese “Content,” Spanish Content ID wording, literal Content ID examples, and “Content Opinions” headings. Exact API/Content ID example tokens are retained.\n\nAll {len(cells)} targets were checked for placeholders and markup. Protected literal mismatches: {len(literal_bad)}. Boundary sources {START-1} ({keyset[START-1]}) and {END+1} ({keyset[END+1]}) are pinned.\n\nThis packet is static machine-assisted primary semantic review; it does not establish native-speaker approval or current-head headed-browser acceptance. No repository files were modified; no tests, builds, scans, or CI ran.\n''')
def dump_manifest():
 files=sorted(p for p in OUT.iterdir() if p.is_file() and p.name not in ('SHA256SUMS','manifest.json'))
 (OUT/'SHA256SUMS').write_text(''.join(f'{sha(p.read_bytes())}  {p.name}\n' for p in files))
 manifest={'repository':REPO,'pullRequest':PR,'window':'W863-W882','head':head,'tree':tree,'branch':BRANCH,'sourceCount':20,'cellCount':len(cells),'counts':dict(counts),'files':[{'path':p.name,'bytes':p.stat().st_size,'sha256':sha(p.read_bytes())} for p in files],'sha256SumsSha256':sha((OUT/'SHA256SUMS').read_bytes())}
 jdump(OUT/'manifest.json',manifest)
dump_manifest()
print(json.dumps({'output':str(OUT),'summary':summary,'manifestSha256':sha((OUT/'manifest.json').read_bytes()),'sha256SumsSha256':sha((OUT/'SHA256SUMS').read_bytes())},ensure_ascii=False))
