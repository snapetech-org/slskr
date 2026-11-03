from pathlib import Path
import json, hashlib, re
ROOT=Path('/mnt/disks/scratch/task-scratch/slskr-pr204-window-0983-1002-independent-crossreview-20261103')
EVIDENCE=ROOT/'evidence'; PINNED=ROOT/'pinned-head-data'
rows=[json.loads(x) for x in (EVIDENCE/'source-only-input.jsonl').read_text(encoding='utf-8').splitlines()]
pinrows=[json.loads(x) for x in (EVIDENCE/'catalog-pins.jsonl').read_text(encoding='utf-8').splitlines()]
locales=['ar','de','es','fr','hi','id','ja','ko','pt-BR','vi','zh-Hans','zh-Hant']
catalogs={p['locale']:json.loads((PINNED/p['path']).read_text(encoding='utf-8')) for p in pinrows}
overrides={}
def setc(pos,loc,disp,target,why): overrides[(pos,loc)]={'disposition':disp,'target':target,'why':why}
# Wishlist terminology refinements at the exact caller.
for loc,target in {
 'ar':'تعذر تحديث عوامل تصفية قائمة الرغبات.','hi':'इच्छा सूची के फ़िल्टर अपडेट नहीं हो सके।','id':'Tidak dapat memperbarui filter Daftar keinginan.','vi':'Không thể cập nhật bộ lọc Danh sách yêu thích.','zh-Hans':'无法更新愿望单筛选条件。'
}.items(): setc(985,loc,'refinement',target,'Use the exact-head localized Wishlist menu term consistently; the current phrase is understandable.')
# Count is a numeric table heading in the pinned callers.
for loc,target in {'de':'Anzahl','es':'Cantidad','fr':'Nombre','hi':'संख्या','id':'Jumlah','ko':'개수','pt-BR':'Quantidade','vi':'Số lượng','zh-Hans':'数量','zh-Hant':'數量'}.items():
 setc(986,loc,'correction',target,'The pinned callers use Count as a numeric table heading; the current target is a verb or infinitive rather than a quantity/count noun.')
# Rate limits in the Mesh Sync Security subheader.
for loc,target in {
 'ar':'عدادات التوقيعات والسمعة وحدود المعدل والحجر الصحي',
 'es':'Contadores de firmas, reputación, límites de frecuencia y cuarentena',
 'fr':'Compteurs de signatures, de réputation, de limites de fréquence et de quarantaine',
 'id':'Penghitung tanda tangan, reputasi, pembatasan frekuensi, dan karantina',
 'ko':'서명, 평판, 빈도 제한 및 격리 카운터',
 'pt-BR':'Contadores de assinaturas, reputação, limites de frequência e quarentena',
 'vi':'Bộ đếm chữ ký, danh tiếng, giới hạn tần suất và cách ly'
}.items(): setc(987,loc,'correction',target,'The pinned caller is a Mesh Sync Security subheader. The current wording suggests prices/fees, ratios, or throughput in this locale; the target names rate/frequency limits.')
# Cover Traffic is a noun feature header in privacy settings.
for loc,target in {
 'ar':'حركة مرور تمويهية','de':'Cover-Traffic','es':'Tráfico de cobertura','fr':'Trafic de couverture','hi':'कवर ट्रैफ़िक','id':'Lalu Lintas Penyamaran','pt-BR':'Tráfego de cobertura','vi':'Lưu lượng ngụy trang','zh-Hans':'掩护流量','zh-Hant':'掩護流量'
}.items(): setc(988,loc,'correction',target,'The pinned caller renders this as a privacy feature header. The current target is imperative/verb-like or reads as road traffic; this target is a noun phrase for cover traffic.')
setc(989,'fr','refinement','Pochette','In this playlist cover-art selector, the neighboring exact-head Cover art policy translation uses pochettes; Pochette is clearer than the broad Couverture.')
setc(991,'vi','correction','Mức độ bao phủ các tệp FLAC dùng chung','The caller renders this as progress coverage. The current phrase suggests broadcast coverage; this target states the coverage level of shared FLAC files and preserves FLAC.')
# Bare Create is a submit/action button in three pinned callers.
for loc,disp,target,why in [
 ('ar','correction','إنشاء','The current wording is a third-person verb; the pinned callers use Create as a button action.'),
 ('id','refinement','Buat','The current target is understandable but uses the meN- verb form; Buat is the concise action-button label.'),
 ('ja','refinement','作成','For a bare submit button, use the concise action label 作成 rather than dictionary-form 作成する.'),
 ('ko','refinement','만들기','The current dictionary-form verb is understandable; the button context reads more naturally as the action noun 만들기.'),
 ('vi','refinement','Tạo','The current phrase Tạo nên is understandable but adds an unnecessary nuance for a bare action button; use Tạo.'),
 ('zh-Hans','correction','创建','In the pinned software submit buttons, 创建 is the standard action; 创造 suggests inventing or making something original.'),
 ('zh-Hant','correction','建立','In the pinned software submit buttons, 建立 is the standard action; 創造 suggests inventing or making something original.')
]: setc(992,loc,disp,target,why)
# Exact-head standalone Pod label is Pod in all locales; preserve the protected product term.
for loc,target,why in [
 ('hi','कंटेंट-लिंक्ड Pod बनाएं','Keep the product term literal instead of transliterating it as पॉड.'),
 ('ja','コンテンツにリンクされた Pod の作成','Keep the product term literal instead of transliterating it as ポッド.'),
 ('ko','콘텐츠 연결 Pod 생성','Keep the product term literal instead of transliterating it as 포드.')
]: setc(994,loc,'correction',target,'The exact-head standalone Pod label remains Pod in every locale. '+why)
setc(994,'pt-BR','refinement','Criar Pod vinculado ao conteúdo','The meaning is correct; match the protected product-term casing (Pod) and use the natural contraction ao conteúdo.')
# Room labels follow exact-head Rooms terminology in each locale.
setc(998,'es','correction','Crear una nueva sala','The pinned caller creates an app chat room. The exact-head Rooms label is Salas; habitación suggests a physical room.')
setc(998,'fr','correction','Créer un nouveau salon','The pinned caller creates an app chat room. The exact-head Rooms label is Salons; pièce suggests a physical room.')
setc(998,'hi','refinement','नया रूम बनाएँ','The current कक्ष is understandable; the exact-head Rooms label uses रूम, so align the creation label with the app term.')
setc(998,'zh-Hant','correction','建立新的聊天室','The pinned caller creates an app chat room. The exact-head Rooms label is 聊天室; 房間 loses that product context.')
setc(1000,'de','correction','Raum erstellen','In the pinned caller this is a chat-room creation action. Raum schaffen means making space; Raum erstellen names the action.')
setc(1000,'es','correction','Crear una sala','The pinned caller creates an app chat room. The exact-head Rooms label is Salas; habitación suggests a physical room.')
setc(1000,'fr','correction','Créer un salon','The pinned caller creates an app chat room. The exact-head Rooms label is Salons; use the same product term rather than salle.')
setc(1000,'hi','correction','रूम बनाएँ','The pinned caller creates an app chat room. The exact-head Rooms label is रूम; जगह means place/space and loses the room meaning.')
setc(1000,'zh-Hant','correction','建立聊天室','The pinned caller creates an app chat room. The exact-head Rooms label is 聊天室; 房間 loses that product context.')
# Share Groups terminology consistency.
setc(1001,'hi','refinement','शेयर समूह बनाएँ','The exact-head Share Groups label is शेयर समूह; use the same localized feature term rather than ग्रुप.')
setc(1001,'zh-Hant','refinement','建立分享群組','The exact-head Share Groups label is 分享群組; align this creation title with that localized feature name.')
assert len(overrides)==56, len(overrides)
anchors={985:['Wishlist'],987:['Rate limits'],988:['Enable Cover Traffic'],989:['Cover art policy for {name}'],991:['FLAC'],993:['Collections'],994:['Pod'],998:['Rooms'],1000:['Rooms'],1001:['Share Groups'],1002:['Share Groups']}
def sha(s): return hashlib.sha256(s.encode('utf-8')).hexdigest()
def ph(s): return list(dict.fromkeys(re.findall(r'\{[A-Za-z_][A-Za-z0-9_]*\}',s)))
def tags(s): return re.findall(r'<[^>]+>',s)
def icu(s): return bool(re.search(r'\{\s*[A-Za-z_][\w.-]*\s*,\s*(?:plural|select|selectordinal)\b',s,re.I))
period=set('.。．۔।᠃'); question=set('?？؟'); exclaim=set('!！')
def punct(s):
 if not s:return 'none'
 c=s[-1]
 return 'period' if c in period else 'question' if c in question else 'exclamation' if c in exclaim else 'none'
def protected(source):
 result=[]
 if 'FLAC' in source: result.append('FLAC')
 if re.search(r'\bPod\b',source): result.append('Pod')
 return result
ledger=[]; struct=[]
for row in rows:
 source=row['sourceId']; pos=row['sourcePosition']
 assert sha(source)==row['sourceSha256']
 assert ph(source)==row['sourcePlaceholders'] and tags(source)==row['sourceMarkup'] and icu(source)==row['sourceHasIcu'],pos
 for c in row['currentTargets']:
  locale=c['locale']; target=catalogs[locale].get(source)
  assert target==c['target'] and sha(target)==c['targetSha256'],(pos,locale,'current drift')
  d=overrides.get((pos,locale))
  if pos in (983,984): disp='hold'; proposal=None; reason='No exact quoted production caller is pinned for this source ID; keep the cell held pending caller evidence.'
  elif d: disp=d['disposition']; proposal=d['target']; reason=d['why']
  else: disp='accept-current'; proposal=None; reason='The current translation conveys the source meaning in the pinned caller context; no material semantic issue was identified.'
  assert disp in {'accept-current','correction','refinement','hold'}
  assert (proposal is not None and proposal!=target) if disp in {'correction','refinement'} else proposal is None
  final=proposal if proposal is not None else target
  callers=[{'path':x['path'],'line':x['line'],'lineSha256':x['lineSha256'],'fileSha256':x['fileSha256'],'gitBlob':x['gitBlob']} for x in row['callers']]
  term_anchors=[]
  for key in anchors.get(pos,[]):
   if key in catalogs[locale]:
    val=catalogs[locale][key]; term_anchors.append({'sourceId':key,'target':val,'targetSha256':sha(val)})
  prot=protected(source)
  rec={'sourcePosition':pos,'sourceIndex':row['sourceIndex'],'sourceId':source,'sourceSha256':row['sourceSha256'],'locale':locale,'currentTarget':target,'currentTargetSha256':c['targetSha256'],'disposition':disp,'proposedTarget':proposal,'proposedTargetSha256':sha(proposal) if proposal is not None else None,'rationale':reason,'semanticConfidence':'moderate','callerStatus':row['callerStatus'],'callerPinCount':len(callers),'callerPinRefs':callers,'terminologyAnchors':term_anchors,'sourcePlaceholders':ph(source),'sourceMarkup':tags(source),'sourceHasIcu':icu(source),'currentPlaceholders':ph(target),'currentMarkup':tags(target),'currentHasIcu':icu(target),'finalPlaceholders':ph(final),'finalMarkup':tags(final),'finalHasIcu':icu(final),'protectedLiterals':prot,'currentPreservesProtectedLiterals':all(x in target for x in prot),'finalPreservesProtectedLiterals':all(x in final for x in prot),'sourceTerminalPunctuation':punct(source),'currentTerminalPunctuation':punct(target),'finalTerminalPunctuation':punct(final)}
  ledger.append(rec)
  checks=[]
  for name,value in [('current',target),('final',final)]:
   checks.append({'value':name,'placeholders':ph(value)==ph(source),'markup':tags(value)==tags(source),'icu':icu(value)==icu(source),'protectedLiterals':all(x in value for x in prot),'punctuation':punct(value)==punct(source)})
  struct.append({'sourcePosition':pos,'locale':locale,'sourceId':source,'currentTargetSha256':c['targetSha256'],'finalTargetSha256':sha(final),'checks':checks})
assert len(ledger)==240 and len({(x['sourcePosition'],x['locale']) for x in ledger})==240
(ROOT/'blind-ledger.jsonl').write_text(''.join(json.dumps(x,ensure_ascii=False,separators=(',',':'))+'\n' for x in ledger),encoding='utf-8')
issues=[]
for x in struct:
 for ck in x['checks']:
  failed=[k for k,v in ck.items() if k!='value' and not v]
  if failed: issues.append({'sourcePosition':x['sourcePosition'],'locale':x['locale'],'value':ck['value'],'failed':failed})
(ROOT/'blind-structural-audit.json').write_text(json.dumps({'cells':240,'perValueChecks':480,'checks':['placeholders','markup','ICU','protectedLiterals','terminalPunctuation'],'issueCount':len(issues),'issues':issues,'rows':struct,'interpretation':{'terminalPunctuation':'Source sentence-final punctuation is retained with a locale-appropriate full stop.','protectedLiterals':'FLAC is protected as an acronym. Pod is protected because the exact-head standalone catalog label Pod remains Pod in all twelve locales.','limitations':'Structural checks are deterministic. Semantic choices are machine-assisted at moderate confidence and are not native-speaker approval.'}},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
att=json.loads((EVIDENCE/'source-current-attestation.json').read_text(encoding='utf-8'))
method='''# Independent cross-review packet — PR #204, W983–W1002\n\nThis packet records a machine-assisted semantic cross-review of 240 locale cells at exact PR head `09a614a66f1104fe530773fb17c79ed6338aed02` / tree `963f283311ae39dfa5fc289386d99dcc0dac2f90`. The PR was attested open and draft. This is not native-speaker approval.\n\n## Inputs and validation\n\n- The primary packet `SHA256SUMS` and `INPUT-SHA256SUMS` passed before review. The source-only JSONL, catalog pins, selection evidence, and input attestation were copied into `evidence/`; the per-cell primary ledger was not opened before this blind ledger was sealed.\n- Exact-head GitHub API data confirmed the PR state/ref/head and commit tree. The twelve locale catalogs and pinned caller source files were downloaded from that exact commit and retained under `pinned-head-data/`.\n- `evidence/source-current-attestation.json` records twelve catalog byte/hash/blob/keyset matches, identical ordered key arrays, twenty sorted source positions, 240 source/current values and hashes, and 33 caller-pin checks. All passed with zero mismatches.\n- `blind-structural-audit.json` checks placeholders, markup, ICU patterns, protected literals, and terminal punctuation for current and final values. FLAC is protected as an acronym. Pod is protected based on the exact-head standalone catalog key `Pod`, which remains `Pod` in all twelve locales.\n\n## Review caveat\n\nBefore per-cell review, the primary packet `README.md` was opened after checksum verification. It exposed aggregate disposition counts and same-window summary claims, including the 983–984 hold status and short notes about Cover Traffic, `{name}`, and FLAC. No per-cell primary decision ledger or proposal was read before this blind ledger was sealed. The README claims were not used as cell-level evidence or to select target values. This exposure means the review is not strictly blind in process.\n\n## Decision rules\n\n- Hold both source positions 983 and 984 in every locale because the source-only input has no exact quoted production caller for either key.\n- Accept a current value when it conveys the source meaning in the pinned caller context and has no material issue.\n- Correct a target when it changes the source meaning or fails the pinned UI context; refine a target when it is understandable but conflicts with exact-head terminology or UI-action style.\n- Proposed targets exist only for correction/refinement rows. Structural checks apply to the current target and final reviewed target.\n'''
(ROOT/'blind-review-method.md').write_text(method,encoding='utf-8')
counts={}
for r in ledger: counts[r['disposition']]=counts.get(r['disposition'],0)+1
manifest={'task':'slskR PR #204 independent semantic cross-review W983-W1002','repository':'snapetech-org/slskr','pullRequest':204,'state':att['prState'],'draft':att['draft'],'headRef':att['headRef'],'head':att['headSha'],'tree':att['treeSha'],'window':{'firstPosition':983,'lastPosition':1002,'sourceCount':20,'localeCount':12,'cellCount':240},'dispositions':counts,'proposedTargets':sum(r['proposedTarget'] is not None for r in ledger),'structuralAuditIssueCount':len(issues),'sourceCurrentAttestationPass':att['exactAttestationPass'],'nativeSpeakerApproval':False,'testsBuildScansBrowserOrCI':'not run','repoOrPrEdits':'none','blindLedgerPath':'blind-ledger.jsonl','blindLedgerRows':len(ledger),'strictBlindProcess':'compromised by opening primary README.md; no per-cell proposal ledger read before sealing','semanticConfidence':'moderate','limitation':'Machine-assisted review; no native-speaker approval.'}
(ROOT/'blind-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'ledgerRows':len(ledger),'overrides':len(overrides),'dispositions':counts,'structuralIssueCount':len(issues),'attestationPass':att['exactAttestationPass']},ensure_ascii=False,indent=2))
