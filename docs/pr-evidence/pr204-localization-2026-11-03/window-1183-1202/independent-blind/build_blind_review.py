#!/usr/bin/env python3
"""Blind semantic review of slskR PR #204 W1183-W1202 from candidate-free input only."""
from __future__ import annotations
import collections, hashlib, json, re
from pathlib import Path

ROOT=Path(__file__).resolve().parent
INPUT=ROOT/'input'
REPO='snapetech-org/slskr'; PR=204
HEAD='8e60a51ec25967df115a3fd8c42872abbec58d8a'; TREE='c2ec31432943730f0a8f3ee87687c46b6a4400c2'
BRANCH='codex/slskr-l10n-audit-20261030'; WINDOW='W1183-W1202'
LOCALES=['es','zh-Hans','hi','de','ja','fr','pt-BR','ar','ko','zh-Hant','vi','id']
PH=re.compile(r'\{[^{}]+\}'); TAG=re.compile(r'</?[A-Za-z][^>]*>'); NUM=re.compile(r'\d+')

# A candidate-free blind adjudication: key -> (decision, exact target, confidence, note).
PROPOSALS={}
def add(pos, locale, decision, target, confidence='moderate', note=''):
    PROPOSALS[(pos,locale)]=(decision,target,confidence,note)
# Rank 1183: resolve the wrong Search-vs-Discovery term and clear duration wording where current is misleading.
add(1183,'ko','correction','디스커버리 선반 만료 일수','moderate','The pinned caller places this aria-label on the numeric Discovery Shelf expiry setting. 검색 means search; the source names the Discovery Shelf.')
add(1183,'fr','refinement','Jours avant l’expiration de l’étagère Discovery','moderate','The caller uses this for an expiry-days number; the current plural étagères and Jours d’expiration are awkward for one shelf setting.')
add(1183,'vi','refinement','Số ngày trước khi các mục chưa được đánh giá hết hạn trên kệ Discovery','low','The field is a days value under “Expire unrated after”; the current wording reads more like an expiry date for the shelf itself.')
# Rank 1184: these buttons dismiss error/success messages, so “close” is the intended action.
for loc,target in {
 'es':'Cerrar','zh-Hans':'关闭','hi':'बंद करें','de':'Schließen','ja':'閉じる','fr':'Fermer',
 'pt-BR':'Fechar','ar':'إغلاق','ko':'닫기','zh-Hant':'關閉','vi':'Đóng','id':'Tutup'
}.items():
    add(1184,loc,'correction',target,'moderate','Both pinned callers render this as the action that clears an error or success message. Use the close/dismiss action, not firing or rejecting a person.')
# Rank 1188: remove additions not in the allowlisted server message while retaining exact DisplayName.
for loc,target in {
 'es':'Se requiere DisplayName.','zh-Hans':'必须提供 DisplayName。','hi':'DisplayName आवश्यक है।','de':'DisplayName ist erforderlich.',
 'ja':'DisplayNameが必要です。','pt-BR':'DisplayName é obrigatório.','ar':'مطلوب DisplayName.','ko':'DisplayName이 필요합니다.',
 'zh-Hant':'必須提供 DisplayName。','vi':'Cần có DisplayName.','id':'DisplayName wajib diisi.'
}.items():
    add(1188,loc,'correction',target,'moderate','The pinned server literal and client allowlist are exactly “DisplayName is required.” Remove the current added API-field parenthetical and preserve the exact DisplayName identifier.')
add(1189,'vi','correction','Các bồi thẩm viên bất đồng quan điểm','moderate','The caller joins the dissentingJurors list into a message header. This means dissenting individual jurors, not a dissenting jury as an institution.')
# “Distinct Users” is a unique-user metric in the pinned report tables.
add(1190,'ar','correction','المستخدمون الفريدون','moderate','This is a distinct-user count column; المتميزون means distinguished rather than unique.')
add(1190,'id','refinement','Pengguna unik','moderate','This is a distinct-user count column; unik is clearer than berbeda for a deduplicated count.')
add(1190,'ja','refinement','ユニークユーザー','moderate','The pinned table reports distinct-user counts; ユニークユーザー is the concise analytics term.')
add(1190,'ko','refinement','고유 사용자','moderate','The pinned table reports distinct-user counts; 고유 사용자 clearly means unique users.')
# “Peers” is the P2P remote-user sense in this compatibility report, not colleagues/companions.
for loc,target in {
 'es':'Pares distintos','zh-Hans':'不同的网络对等方','hi':'विशिष्ट पीयर','de':'Eindeutige Peers','ar':'نظراء فريدون',
 'ko':'고유 피어','zh-Hant':'不同的網路對等方','vi':'Các peer riêng biệt','id':'Peer unik'
}.items():
    add(1191,loc,'correction',target,'moderate','The pinned caller places this beside a distinct-user metric in the compatibility dashboard. Translate network peers/remote participants, not colleagues or companions.')
# The Domain field is a content-domain label, not a workplace/territory/specialization.
add(1194,'ar','refinement','المجال','moderate','The pinned content-registry callers use Domain for a descriptor field. المجال conveys that field/domain sense more directly than specialization.')
add(1194,'hi','correction','डोमेन','moderate','The pinned content-registry callers use Domain for a descriptor field; कार्यस्थल means workplace.')
add(1194,'vi','correction','Lĩnh vực','moderate','The pinned content-registry callers use Domain for a descriptor field; Lãnh địa means territory.')
# Search by content domain, not an Internet domain name.
add(1195,'zh-Hans','correction','按领域搜索','moderate','The pinned card says it finds ContentIDs by domain and optional type; the current 域名搜索 reads as an Internet-domain-name search.')
add(1195,'zh-Hant','correction','按領域搜尋','moderate','The pinned card says it finds ContentIDs by domain and optional type; the current 域名搜尋 reads as an Internet-domain-name search.')
add(1195,'vi','correction','Tìm kiếm theo lĩnh vực','moderate','The pinned card finds ContentIDs by content domain and optional type; tên miền suggests a DNS/Internet domain name.')
# Clean the exact allowlisted server error, remove added parentheticals, and avoid DNS “domain name” wording for this content-domain error.
for loc,target in {
 'es':'Se requiere el dominio.','zh-Hans':'必须提供领域。','hi':'डोमेन आवश्यक है।','de':'Die Domäne ist erforderlich.',
 'ja':'ドメインが必要です。','pt-BR':'O domínio é obrigatório.','ar':'المجال مطلوب.','ko':'도메인이 필요합니다.',
 'zh-Hant':'必須提供領域。','vi':'Cần có lĩnh vực.','id':'Domain wajib diisi.'
}.items():
    add(1197,loc,'correction',target,'moderate','The pinned server response and allowlist are exactly “Domain is required.” Remove added API-field notes; the endpoint uses a content-domain value rather than a DNS hostname.')
add(1199,'ar','refinement','المجال:','moderate','This labels a content-domain value in ContentID results; المجال is clearer than specialization here.')
add(1199,'vi','correction','Lĩnh vực:','moderate','This labels a content-domain value in ContentID results; Lãnh địa means territory.')
for pos in (1200,1201):
    for loc,target in {'zh-Hans':'领域' if pos==1200 else '领域:', 'zh-Hant':'領域' if pos==1200 else '領域:', 'vi':'Lĩnh vực' if pos==1200 else 'Lĩnh vực:'}.items():
        add(pos,loc,'correction',target,'moderate','The pinned MediaCore statistic is totalDomains/averageMappingsPerDomain in the content registry. Use content-domain/field wording, not Internet-domain names or territory.')
# The same Done action closes the modal in all five pinned callers.
for loc,target in {
 'es':'Cerrar','zh-Hans':'关闭','hi':'बंद करें','de':'Schließen','ja':'閉じる','fr':'Fermer',
 'pt-BR':'Fechar','ar':'إغلاق','ko':'닫기','zh-Hant':'關閉','vi':'Đóng','id':'Tutup'
}.items():
    add(1202,loc,'refinement',target,'moderate','All five pinned callers use Done as a modal-close action (shelf, integrations, queue, radio, or stats). The target names that action directly.')

HOLD_1198=('The pinned Security/Adversarial Settings caller identifies a “Domain to front through” field and mentions CDN domains, but the packet does not define the fronting mechanism or supply approved localized terminology. This security-setting phrase is unresolved; hold pending product terminology. Any later wording must preserve the exact CDN acronym.')
PROTECTED={1188:['DisplayName'],1193:['ReplayGain'],1198:['CDN']}

def sha(v): return hashlib.sha256(v if isinstance(v,bytes) else v.encode('utf-8')).hexdigest()
def readj(p): return json.loads(p.read_text(encoding='utf-8'))
def readjl(p): return [json.loads(x) for x in p.read_text(encoding='utf-8').splitlines() if x]
def writej(p,v): p.write_text(json.dumps(v,ensure_ascii=False,indent=2,sort_keys=True)+'\n',encoding='utf-8')
def writejl(p,rows): p.write_text(''.join(json.dumps(r,ensure_ascii=False,sort_keys=True)+'\n' for r in rows),encoding='utf-8')
def count_tokens(s,rx):
    d=collections.Counter(rx.findall(s)); return dict(sorted(d.items()))

# Validate candidate-free packet checksums and exact live PR pins.
verified_files=0
for line in (INPUT/'SHA256SUMS.txt').read_text(encoding='utf-8').splitlines():
    digest,rel=line.split(maxsplit=1); f=INPUT/rel.strip()
    if not f.is_file() or sha(f.read_bytes())!=digest: raise SystemExit(f'input checksum mismatch: {rel}')
    verified_files+=1
manifest=readj(INPUT/'manifest.json'); att=readj(INPUT/'PR-attestation.json'); live=readj(ROOT/'live-pr-verification.json')
if not manifest.get('candidateFreeInputOnly') or manifest.get('proposedTranslationsIncluded') is not False or manifest.get('semanticReviewIncluded') is not False: raise SystemExit('input is not candidate-free')
if str(manifest.get('repository','')).lower()!=REPO.lower() or manifest.get('pullRequest')!=PR or manifest.get('head')!=HEAD or manifest.get('tree')!=TREE: raise SystemExit('manifest exact pin mismatch')
if str(att.get('repository','')).lower()!=REPO.lower() or att.get('pullRequest')!=PR or att.get('headRefOid')!=HEAD or att.get('localWorktreeTree')!=TREE or att.get('remotePullRefHead')!=HEAD: raise SystemExit('attestation exact pin mismatch')
if live.get('state')!='OPEN' or live.get('isDraft') is not True or live.get('head')!=HEAD or live.get('tree')!=TREE or live.get('remoteBranchHead')!=HEAD or live.get('branch')!=BRANCH: raise SystemExit('live PR pin mismatch')
if manifest.get('window')!=WINDOW or manifest.get('cellCount')!=240 or manifest.get('sourceCount')!=20 or manifest.get('localeCount')!=12: raise SystemExit('window scope mismatch')

cells=readjl(INPUT/'current-target-cells.jsonl'); contexts=readjl(INPUT/'source-contexts.jsonl'); pins=readj(INPUT/'catalog-file-pins.json')
if len(cells)!=240 or len(contexts)!=20: raise SystemExit('row count mismatch')
context_by_pos={r['position']:r for r in contexts}; locale_pins=pins['localeCatalogs']; locale_order=manifest['localeOrder']
if locale_order!=LOCALES or pins['head']!=HEAD or pins['tree']!=TREE: raise SystemExit('locale or catalog manifest mismatch')
if sum(x['callerReferenceCount'] for x in contexts)!=37: raise SystemExit('pinned caller total mismatch')

# Audit known protected literals from exact source keys and current values; values are never interpolated/evaluated.
ledger=[]; holds=[]; changes_by_locale=collections.Counter(); changes_by_position=collections.Counter(); dispositions=collections.Counter()
placeholder_checks=markup_checks=numeric_checks=0; protected_current_violations=[]; protected_candidate_violations=[]
for c in sorted(cells,key=lambda x:(x['position'],LOCALES.index(x['locale']))):
    pos=c['position']; loc=c['locale']; key=(pos,loc); cx=context_by_pos[pos]; locale_pin=locale_pins[loc]
    if str(c['repository']).lower()!=REPO.lower() or c['pullRequest']!=PR or c['head']!=HEAD or c['tree']!=TREE or c['window']!=WINDOW: raise SystemExit(f'per-cell exact pin mismatch {key}')
    if c['sourceKey']!=cx['sourceKey'] or c['sourceKeySha256']!=cx['sourceKeySha256'] or sha(c['sourceKey'])!=c['sourceKeySha256']: raise SystemExit(f'source context mismatch {key}')
    if c['sourceCallerCount']!=cx['callerReferenceCount']: raise SystemExit(f'caller count mismatch {key}')
    if c['catalogPath']!=locale_pin['path'] or c['catalogSha256']!=locale_pin['sha256'] or c['catalogGitBlob']!=locale_pin['gitBlob']: raise SystemExit(f'catalog pin mismatch {key}')
    current=c['currentTarget']
    if sha(current)!=c['currentTargetSha256']: raise SystemExit(f'current target hash mismatch {key}')
    source=c['sourceKey']; source_ph=PH.findall(source); current_ph=PH.findall(current)
    source_tags=TAG.findall(source); current_tags=TAG.findall(current)
    if source_ph!=c['sourcePlaceholders'] or current_ph!=c['currentTargetPlaceholders'] or not c['placeholderTokenSequenceMatchesSource']: raise SystemExit(f'placeholder evidence mismatch {key}')
    if source_tags!=current_tags: raise SystemExit(f'source/current markup mismatch {key}')
    source_nums=NUM.findall(source); current_nums=NUM.findall(current)
    if source_nums!=current_nums: raise SystemExit(f'source/current numeric mismatch {key}')
    placeholder_checks+=1; markup_checks+=1; numeric_checks+=1
    decision,target,confidence,note=PROPOSALS.get(key,(None,None,None,None))
    if pos==1198:
        decision='hold'; target=None; confidence='low'; rationale=HOLD_1198; hold_reason=HOLD_1198
    elif decision is None:
        decision='accept-current'; target=None; confidence='moderate'; hold_reason=None
        rationale={
          1183:'The pinned caller uses this as the accessible name for the Discovery Shelf expiry-days input; current wording is adequate in this locale.',
          1185:'The pinned close icon dismisses the port migration reminder; current wording expresses dismiss/close.',
          1186:'The popup explains the reminder is dismissed until forwarded ports change; current wording preserves that condition.',
          1187:'This is the localized label for the published pod displayName value; current wording means display name.',
          1188:'The current French target is a direct server-error translation and preserves DisplayName.',
          1189:'The pinned Quarantine Jury caller uses this for dissenting jurors; current wording preserves that meaning.',
          1190:'The pinned report uses this for a distinct-user count; current wording is a clear distinct/unique-user label.',
          1191:'The pinned compatibility report uses this for distinct network peers; current wording preserves the peer sense.',
          1192:'The pinned playlist policy option means not to change the cover art; current wording preserves the policy.',
          1193:'The pinned playlist policy option means not to run ReplayGain; current wording preserves the exact product term and action.',
          1194:'The pinned content-registry controls use this as a content domain/field label; current wording is adequate in this locale.',
          1195:'The pinned ContentID card searches by content domain and optional type; current wording preserves the search purpose.',
          1196:'The pinned federation diagnostics table reports whether the federation domain is configured; current wording preserves that state.',
          1197:'The pinned server response is “Domain is required”; the current target preserves that requirement after removal of extra parentheticals.',
          1199:'The pinned ContentID result uses this as a content-domain field label; current wording preserves that sense.',
          1200:'The pinned MediaCore statistic counts content-registry domains; current wording conveys a domain total.',
          1201:'The pinned MediaCore statistics field labels content-registry domain counts; current wording conveys the field.',
          1202:'The pinned callers use this as a Done/close action in modal dialogs; current wording is a natural completion button in this locale.'
        }.get(pos,'The current value matches its pinned caller context and preserves source meaning.')
    else:
        rationale=note; hold_reason=None
    selected=target if target is not None else current
    selected_ph=PH.findall(selected); selected_tags=TAG.findall(selected); selected_nums=NUM.findall(selected)
    if selected_ph!=source_ph or selected_tags!=source_tags or selected_nums!=source_nums: raise SystemExit(f'selected structural mismatch {key}')
    protected_terms=PROTECTED.get(pos,[])
    current_literals=[]; candidate_literals=[]
    for literal in protected_terms:
        source_count=source.count(literal); cur_count=current.count(literal); sel_count=selected.count(literal)
        check={'literal':literal,'sourceCount':source_count,'currentCount':cur_count,'selectedCount':sel_count,
               'currentPreserved':cur_count==source_count,'selectedPreserved':sel_count==source_count}
        current_literals.append(check)
        if cur_count!=source_count: protected_current_violations.append({'position':pos,'locale':loc,'literal':literal,'currentCount':cur_count,'sourceCount':source_count})
        # A hold intentionally makes no candidate endorsement; only proposed targets are held to candidate preservation.
        if target is not None and sel_count!=source_count: protected_candidate_violations.append({'position':pos,'locale':loc,'literal':literal})
    if target is not None:
        if sha(target)==sha(current) and target==current: raise SystemExit(f'no-op proposal {key}')
        changes_by_locale[loc]+=1; changes_by_position[str(pos)]+=1
    if decision=='hold': holds.append({'position':pos,'locale':loc,'sourceKey':source,'currentTarget':current,'holdReason':hold_reason,
                                      'callerReferences':cx['references']})
    dispositions[decision]+=1
    row={
      'schemaVersion':1,'window':WINDOW,'position':pos,'sourceKey':source,'sourceKeySha256':c['sourceKeySha256'],
      'locale':loc,'catalogPath':c['catalogPath'],'catalogSha256':c['catalogSha256'],'catalogGitBlob':c['catalogGitBlob'],
      'currentTarget':current,'currentTargetSha256':c['currentTargetSha256'],
      'callerEvidence':{'callerReferenceCount':cx['callerReferenceCount'],'locations':cx['locations'],'references':cx['references'],
                        'callerContextSha256s':[r['contextSha256'] for r in cx['references']]},
      'decision':decision,'candidateTarget':target,'candidateTargetSha256':sha(target) if target is not None else None,
      'selectedTarget':selected,'selectedTargetSha256':sha(selected),'rationale':rationale,'confidence':confidence,
      'holdReason':hold_reason,'protectedLiteralsRequired':protected_terms,'protectedLiteralChecks':current_literals,
      'integrityChecks':{'sourceTargetHashVerified':True,'currentTargetHashVerified':True,
        'sourcePlaceholders':source_ph,'currentPlaceholders':current_ph,'selectedPlaceholders':selected_ph,'placeholderParity':source_ph==selected_ph,
        'sourceMarkupTags':source_tags,'currentMarkupTags':current_tags,'selectedMarkupTags':selected_tags,'markupParity':source_tags==selected_tags,
        'sourceNumericTokens':source_nums,'currentNumericTokens':current_nums,'selectedNumericTokens':selected_nums,'numericParity':source_nums==selected_nums,
        'runtimeValuesEvaluated':False},
      'nativeSpeakerApproved':False
    }
    ledger.append(row)

if len(ledger)!=240 or sum(1 for x in ledger if x['position']==1183)!=12 or sum(1 for x in ledger if x['position']==1202)!=12: raise SystemExit('blind ledger coverage mismatch')
if len(holds)!=12 or any(x['position']!=1198 for x in holds): raise SystemExit('unexpected hold scope')
if protected_candidate_violations: raise SystemExit('candidate protected-literal failure')
writejl(ROOT/'blind-decisions.jsonl',ledger)
writejl(ROOT/'holds.jsonl',holds)
writej(ROOT/'protected-literal-audit.json',{
 'exactProtectedTermsBySource':{'1188':['DisplayName'],'1193':['ReplayGain'],'1198':['CDN']},
 'currentValueViolations':protected_current_violations,'candidateViolations':protected_candidate_violations,
 'note':'No runtime expressions were evaluated. Current Hindi W1198 transliterates CDN as सीडीएन; W1198 is held in all locales and future candidates must preserve the exact acronym.'})
summary={
 'artifact':'slskR PR #204 independent blind semantic review W1183-W1202',
 'repository':REPO,'pullRequest':PR,'pullRequestUrl':'https://github.com/snapetech-org/slskr/pull/204',
 'state':'OPEN','isDraft':True,'branch':BRANCH,'head':HEAD,'tree':TREE,'window':WINDOW,
 'reviewMode':'independent blind; source/current and caller evidence only; primary ledger and prior targets not inspected',
 'candidateFreeManifestSha256':sha((INPUT/'manifest.json').read_bytes()),'candidateFreeChecksumListSha256':sha((INPUT/'SHA256SUMS.txt').read_bytes()),
 'verifiedInputChecksumEntries':verified_files,'sourceCount':20,'localeCount':12,'reviewedCells':240,
 'callerReferencesVerified':sum(x['callerReferenceCount'] for x in context_by_pos.values()),
 'decisionCounts':dict(sorted(dispositions.items())),'recommendedChanges':sum(changes_by_locale.values()),
 'changesByLocale':dict(changes_by_locale),'changesByPosition':dict(sorted(changes_by_position.items(),key=lambda x:int(x[0]))),
 'holdCount':len(holds),'holdsByPosition':dict(collections.Counter(str(x['position']) for x in holds)),
 'placeholderChecks':placeholder_checks,'placeholderMismatchCount':0,'markupChecks':markup_checks,'markupMismatchCount':0,
 'numericTokenChecks':numeric_checks,'numericTokenMismatchCount':0,'protectedLiteralCandidateViolations':len(protected_candidate_violations),
 'protectedLiteralCurrentViolations':len(protected_current_violations),'protectedLiteralCurrentViolationDetails':protected_current_violations,
 'rank1198Boundary':'hold all 12 locales pending product-approved domain-fronting terminology; preserve exact CDN in any future target',
 'runtimeExpressionsEvaluated':False,'nativeSpeakerApproval':False,'repositoryOrPREdited':False,
 'testsBuildsScansCIWorkflowBrowserMergeReleaseOrTagActions':False
}
writej(ROOT/'summary.json',summary)
print(json.dumps(summary,ensure_ascii=False,indent=2))
