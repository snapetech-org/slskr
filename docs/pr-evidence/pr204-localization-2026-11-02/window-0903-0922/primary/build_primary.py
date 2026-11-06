import collections
import datetime as dt
import hashlib
import json
import re
import subprocess
from pathlib import Path

ROOT = Path('/home/keith/Documents/code/task-worktrees/localization-20261102-slskr')
OUT = Path('/mnt/disks/scratch/task-scratch/slskr-pr204-window-0903-0922-primary-20261102')
REPO = 'snapetech-org/slskR'
PR = 204
BRANCH = 'codex/slskr-l10n-audit-20261030'
HEAD_EXPECTED = 'b1e814ef11d55fd1710d0e2522df14fee9ff0a70'
START, END = 902, 921  # zero-based source positions; displayed as W903-W922
LOCALES = ['ar', 'de', 'es', 'fr', 'hi', 'id', 'ja', 'ko', 'pt-BR', 'vi', 'zh-Hans', 'zh-Hant']

PROPOSALS = {
    (902, 'ar'): ('متابعة', 'correction', 'This appears on the active backfill button. The current third-person verb يكمل means “he continues/completes”; use the concise action label متابعة.'),
    (902, 'de'): ('Fortsetzen', 'refinement', 'The current Weitermachen is understandable but colloquial for a primary action button; Fortsetzen is the standard concise interface action.'),
    (902, 'hi'): ('जारी रखें', 'correction', 'The current dictionary infinitive जारी रखना does not read as the formal button action. Use the polite imperative जारी रखें.'),
    (902, 'id'): ('Lanjutkan', 'correction', 'The current gerund Melanjutkan describes continuing rather than presenting the button action; Lanjutkan is the direct interface command.'),
    (902, 'ja'): ('続行', 'correction', 'The current 続く is intransitive (“continue/occur”). The button resumes a process, so 続行 is the appropriate action label.'),
    (902, 'ko'): ('계속', 'correction', 'The current dictionary form 계속하다 is not a concise action label. 계속 is the natural button label for resuming this process.'),
    (903, 'es'): ('Continúe procesando el historial de búsquedas. Quedan {remaining} de {total} búsquedas.', 'refinement', 'The popup gives an instruction and Spanish product copy uses formal/neutral address. The current Continúa is informal tú; use the formal Continúe.'),
    (905, 'ko'): ('연속적', 'correction', 'This is a cadence value. 마디 없는 means jointless/seamless rather than continuously running; 연속적 expresses a continuous cadence.'),
    (906, 'fr'): ('Contrat', 'correction', 'The table header is a noun for the media-server execution contract. Contracter is an infinitive verb (“to contract/shrink”), so use Contrat.'),
    (907, 'ar'): ('الأعضاء المساهمون:', 'correction', 'The heading names members who contributed opinions. Use the correctly agreeing nominative adjective المساهمون after الأعضاء.'),
    (907, 'ko'): ('기여 회원:', 'correction', 'The count is for members who contributed opinions; 기부 회원 means donating members. 기여 회원 preserves the contribution sense.'),
    (911, 'ar'): ('فترة التهدئة', 'correction', 'This automation label is the interval between runs. ترطيب means moisturizing/hydration, not a cooldown period.'),
    (911, 'es'): ('Período de espera', 'correction', 'This is the delay between automation runs, not the action “to cool off” expressed by Enfriarse.'),
    (911, 'fr'): ('Délai d’attente', 'correction', 'The source labels the interval before a recipe may run again; Refroidir is an infinitive verb, not that duration.'),
    (911, 'hi'): ('कूलडाउन', 'correction', 'The current शांत हो जाओ is an informal imperative meaning “calm down.” The technical label is कूलडाउन, consistent with the adjacent milliseconds setting.'),
    (911, 'id'): ('Jeda', 'correction', 'The current Pendinginan describes cooling. Jeda is the interval between automation runs and reads naturally with the displayed duration.'),
    (911, 'pt-BR'): ('Tempo de espera', 'correction', 'The source labels a delay between runs; Esfriar is an infinitive verb rather than a time interval.'),
    (911, 'vi'): ('Thời gian chờ', 'refinement', 'The value is an automation waiting interval, not a game ability. Thời gian chờ avoids the game-specific “cooldown/recharge” sense in hồi chiêu.'),
    (912, 'ar'): ('مدة التهدئة بالمللي ثانية', 'correction', 'The current phrase omits the relation between the cooldown and its unit. The proposed wording explicitly says the cooldown duration is measured in milliseconds.'),
    (912, 'de'): ('Abklingzeit in Millisekunden', 'refinement', 'The current compound is understandable but awkward as a configuration label. The proposed phrase makes the unit relation explicit.'),
    (912, 'id'): ('Waktu jeda (milidetik)', 'correction', 'Milidetik Pendinginan reads as milliseconds of cooling; identify this setting as the wait interval measured in milliseconds.'),
    (912, 'zh-Hans'): ('冷却时间（毫秒）', 'refinement', 'The current compound omits the unit boundary. Parentheses clearly mark milliseconds as the unit of the cooldown duration.'),
    (912, 'zh-Hant'): ('冷卻時間（毫秒）', 'refinement', 'The current compound omits the unit boundary. Parentheses clearly mark milliseconds as the unit of the cooldown duration.'),
    (915, 'ar'): ({
        'zero': 'تم نسخ تصدير {format} لعدد {count} من مرات التشغيل.',
        'one': 'تم نسخ تصدير {format} لعدد {count} مرة تشغيل.',
        'two': 'تم نسخ تصدير {format} لعدد {count} مرتي تشغيل.',
        'few': 'تم نسخ تصدير {format} لعدد {count} مرات تشغيل.',
        'many': 'تم نسخ تصدير {format} لعدد {count} مرة تشغيل.',
        'other': 'تم نسخ تصدير {format} لعدد {count} من مرات التشغيل.',
    }, 'refinement', 'The source plural sentence ends with terminal punctuation, but every current Arabic ICU form omits it. Add the full stop to all six forms while preserving their plural categories and both placeholders.'),
    (917, 'ar'): ('نسخ', 'correction', 'This is the action text on a Copy button. ينسخ is third-person (“he copies”); use the concise Arabic action label نسخ.'),
    (917, 'de'): ('Kopieren', 'correction', 'The current Kopie is the noun “copy,” while this is an action button. Use the verb Kopieren.'),
    (917, 'fr'): ('Copier', 'correction', 'The current Copie is a noun. This is an action button, so use the infinitive Copier, consistent with the neighboring copy actions.'),
    (917, 'hi'): ('कॉपी करें', 'correction', 'The current प्रतिलिपि is a noun. The diagnostic-bundle control is an action button; use the formal imperative कॉपी करें.'),
    (917, 'id'): ('Salin', 'correction', 'The current Menyalin is a gerund. Salin is the direct Indonesian action label used for a Copy button.'),
    (917, 'pt-BR'): ('Copiar', 'correction', 'The current Cópia is the noun “copy.” This modal control performs the copy action, so use Copiar.'),
    (918, 'ja'): ('アクションプランをコピー', 'correction', 'This is a button that copies a remediation plan. The current アクションプランのコピー reads as “a copy of an action plan”; use an explicit action.'),
    (918, 'ko'): ('조치 계획 복사', 'refinement', 'The caller copies selected-issue remediations. 조치 계획 names a corrective action plan more precisely than the current practice-plan wording 실천 계획.'),
    (919, 'ja'): ('実行契約をコピー', 'correction', 'The button copies a live media-server execution contract. The current 契約書のコピー is a noun phrase (“a copy of the contract”), not the button action.'),
    (921, 'ar'): ('نسخ السجل', 'correction', 'The caller copies automation review history. التاريخ can mean a calendar date; السجل expresses a history/log.'),
    (921, 'es'): ('Copiar el historial', 'correction', 'The current Historial de copias means a history of copy operations. This button copies the automation history itself.'),
    (921, 'ja'): ('履歴をコピー', 'correction', 'The current コピー履歴 names copy history as a noun. The button action is to copy the automation history.'),
    (921, 'ko'): ('이력을 복사', 'correction', 'The current 복사 기록 means a log of copies. The button copies the automation history, so use the explicit action 이력을 복사.'),
}

CONTEXT_TYPE = {
    902: 'backfill action button',
    903: 'backfill progress popup instruction',
    904: 'OIDC provider button',
    905: 'automation recipe cadence value',
    906: 'media-server execution table header',
    907: 'content-opinion member count label',
    908: 'VPN integration field label',
    909: 'catalog-only description; no exact production caller found',
    910: 'agent controller connection state label',
    911: 'automation cooldown label with duration',
    912: 'Pushbullet cooldown numeric field label',
    913: 'clipboard success toast',
    914: 'single-play clipboard export toast',
    915: 'plural-play clipboard export toast',
    916: 'local-file table column header',
    917: 'diagnostic bundle action button',
    918: 'Library Health action button',
    919: 'media-server execution-contract action button',
    920: 'Discovery Graph branch-report action button',
    921: 'Automation Center history action button',
}

LOCALE_LABELS = {
    'ar':'Arabic','de':'German','es':'Spanish','fr':'French','hi':'Hindi','id':'Indonesian',
    'ja':'Japanese','ko':'Korean','pt-BR':'Brazilian Portuguese','vi':'Vietnamese',
    'zh-Hans':'Simplified Chinese','zh-Hant':'Traditional Chinese',
}

PLACEHOLDER = re.compile(r'\{([A-Za-z][A-Za-z0-9_]*)\}')
MARKUP = re.compile(r'</?[A-Za-z][^>]*>')
PROTECTED = {908:['URL']}
PREVIOUS = ROOT/'docs/pr-evidence/pr204-localization-2026-11-02/window-0883-0902'


def run(args):
    return subprocess.check_output(args, cwd=ROOT, text=True).strip()


def sha_bytes(data):
    if isinstance(data, str):
        data = data.encode('utf-8')
    return hashlib.sha256(data).hexdigest()


def canonical_target(value):
    if isinstance(value, str):
        return value.encode('utf-8')
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode('utf-8')


def sha_target(value):
    return sha_bytes(canonical_target(value))


def text_leaves(value):
    if isinstance(value, str):
        return [value]
    if isinstance(value, dict):
        out=[]
        for v in value.values(): out.extend(text_leaves(v))
        return out
    if isinstance(value, list):
        out=[]
        for v in value: out.extend(text_leaves(v))
        return out
    return []


def dump_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def dump_jsonl(path, rows):
    path.write_text(''.join(json.dumps(row, ensure_ascii=False, sort_keys=True) + '\n' for row in rows))


def term_punctuation(text):
    s=text.rstrip()
    return s[-1] if s and s[-1] in '.?!:：。؟！।' else ''


def punctuation_compatible(source, target):
    expected=term_punctuation(source)
    if not expected: return True
    allowed={'.':'.۔。।', ':':':：;', '：':':：;', '?':'?؟？', '!':'!！'}[expected]
    return all((not term_punctuation(t)) or term_punctuation(t) in allowed for t in text_leaves(target)) and all(term_punctuation(t) for t in text_leaves(target))

# Exact live pull-request and worktree attestations.
pr=json.loads(run(['gh','pr','view',str(PR),'--repo',REPO,'--json','state,isDraft,headRefOid,headRefName,baseRefOid,url']))
assert pr['state']=='OPEN' and pr['isDraft'] is True
assert pr['headRefOid']==HEAD_EXPECTED and pr['headRefName']==BRANCH
api_tree=run(['gh','api',f'repos/{REPO}/commits/{HEAD_EXPECTED}','--jq','.commit.tree.sha'])
remote=run(['git','ls-remote','taskgithub',f'refs/heads/{BRANCH}']).split()[0]
head=run(['git','rev-parse','HEAD'])
tree=run(['git','rev-parse','HEAD^{tree}'])
branch=run(['git','branch','--show-current'])
status=run(['git','status','--porcelain'])
assert (head,branch,status,api_tree,remote)==(HEAD_EXPECTED,BRANCH,'',tree,HEAD_EXPECTED)

# Snapshot every localization PR at selection time; these are volatile heads.
pr_specs=[('SeerrNG',418,'seerrng'),('chaptarrng',190,'chaptarrng'),('QuestarrNG',155,'QuestarrNG'),('ROMarrNG',70,'ROMarrNG'),('slskR',204,'slskr'),('slskdN',409,'slskdN'),('TorrentNG',243,'TorrentNG')]
all_prs=[]
for display,number,repo_slug in pr_specs:
    p=json.loads(run(['gh','pr','view',str(number),'--repo',f'snapetech-org/{repo_slug}','--json','number,state,isDraft,headRefOid,headRefName,baseRefOid,url']))
    all_prs.append({'repository':display,'pullRequest':number,'baseRefOid':p['baseRefOid'],'headRefName':p['headRefName'],'headRefOid':p['headRefOid'],'isDraft':p['isDraft'],'state':p['state'],'url':p['url']})

# Reattest all direct catalogs and derive the sorted source order from the live catalog keys.
catalogs={}; catalog_pins=[]; shared_keyset=None; raw_catalogs={}
for locale in LOCALES:
    rel=f'web/src/lib/locales/ui-labels.{locale}.json'
    raw=subprocess.check_output(['git','show',f'HEAD:{rel}'],cwd=ROOT)
    obj=json.loads(raw)
    keys=sorted(obj)
    if shared_keyset is None: shared_keyset=keys
    assert keys==shared_keyset
    assert len(obj)==5441
    catalogs[locale]=obj; raw_catalogs[locale]=raw
    catalog_pins.append({'locale':locale,'path':rel,'blob':run(['git','rev-parse',f'HEAD:{rel}']),'fileSha256':sha_bytes(raw),'keyCount':len(obj),'orderedKeysetSha256':sha_bytes('\n'.join(keys))})
assert len(shared_keyset)==5441
assert len(shared_keyset[START:END+1])==20
source_ids=shared_keyset[START:END+1]

# Reattest the previous window's final W902 row and its pinned W903 starting boundary.
prior_manifest=json.loads((PREVIOUS/'primary/manifest.json').read_text())
prior_boundary_rows=[json.loads(l) for l in (PREVIOUS/'primary/boundary-pins.jsonl').read_text().splitlines() if l.strip()]
prior_boundary={ (r['sourceIndex'],r['locale']):r for r in prior_boundary_rows }
prior_readback_rows=[json.loads(l) for l in (PREVIOUS/'application/full-window-readback.jsonl').read_text().splitlines() if l.strip()]
prior_end={ (r['sourceIndex'],r['locale']):r for r in prior_readback_rows }
start_boundary_checks=[]; end_boundary_checks=[]
for locale in LOCALES:
    current_start=catalogs[locale][shared_keyset[START]]
    old_start=prior_boundary[(START,locale)]
    start_match=(old_start['sourceId']==shared_keyset[START] and old_start['target']==current_start and old_start['targetSha256']==sha_target(current_start))
    start_boundary_checks.append({'sourceIndex':START,'windowLabel':START+1,'sourceId':shared_keyset[START],'locale':locale,'priorSourceSha256':old_start['sourceSha256'],'priorTargetSha256':old_start['targetSha256'],'currentTargetSha256':sha_target(current_start),'matchesPriorFollowingBoundary':start_match})
    current_end=catalogs[locale][shared_keyset[START-1]]
    prior_applied=prior_end[(START-1,locale)]
    end_match=(prior_applied['sourceId']==shared_keyset[START-1] and prior_applied['finalTarget']==current_end and prior_applied['finalTargetSha256']==sha_target(current_end))
    end_boundary_checks.append({'sourceIndex':START-1,'windowLabel':START,'sourceId':shared_keyset[START-1],'locale':locale,'priorFinalTargetSha256':prior_applied['finalTargetSha256'],'currentTargetSha256':sha_target(current_end),'matchesPriorWindowFinalReadback':end_match})
assert all(r['matchesPriorFollowingBoundary'] for r in start_boundary_checks)
assert all(r['matchesPriorWindowFinalReadback'] for r in end_boundary_checks)
assert prior_manifest['head']=='5f295feea832b3078c52d92d9268cd6446f804a5'

# Gather exact source-literal production callers and context hashes at the current head.
tracked=run(['git','ls-files','web/src']).splitlines()
file_texts={}
for rel in tracked:
    if not rel.endswith(('.js','.jsx','.ts','.tsx')) or '.test.' in rel or '/__tests__/' in rel or '/test/' in rel:
        continue
    raw=subprocess.check_output(['git','show',f'HEAD:{rel}'],cwd=ROOT,stderr=subprocess.DEVNULL)
    try: lines=raw.decode('utf-8').splitlines()
    except UnicodeDecodeError: continue
    file_texts[rel]=(raw,lines)
source_callers=[]; caller_gaps=[]
for index in range(START,END+1):
    source=shared_keyset[index]
    literal=re.compile(r'(["\'])'+re.escape(source)+r'\1')
    hit_count=0
    for rel,(raw,lines) in file_texts.items():
        blob=run(['git','rev-parse',f'HEAD:{rel}'])
        file_sha=sha_bytes(raw)
        for line_no,line in enumerate(lines,1):
            if not literal.search(line): continue
            hit_count += 1
            lo=max(1,line_no-2); hi=min(len(lines),line_no+2)
            source_callers.append({'sourceIndex':index,'windowLabel':index+1,'sourceId':source,'path':rel,'fileBlob':blob,'fileSha256':file_sha,'line':line_no,'lineSha256':sha_bytes(line),'contextStartLine':lo,'contextLines':[{'line':i,'text':lines[i-1]} for i in range(lo,hi+1)],'surfaceLine':line.strip()})
    if hit_count==0:
        caller_gaps.append({'sourceIndex':index,'windowLabel':index+1,'sourceId':source,'reason':'No exact source string-literal caller exists in production web/src at this head; the catalog-only entry is held pending source/caller confirmation.','targetLocales':LOCALES})

# Capture all per-locale current targets and review records. Arabic ICU plural objects are hashed as canonical UTF-8 JSON.
review=[]; formality=[]; placeholder_mismatches=[]; markup_mismatches=[]; protected_mismatches=[]; punctuation_findings=[]
for index in range(START,END+1):
    source=shared_keyset[index]
    source_placeholders=sorted(PLACEHOLDER.findall(source))
    source_markup=MARKUP.findall(source)
    for locale in LOCALES:
        current=catalogs[locale][source]
        proposal=PROPOSALS.get((index,locale))
        if index==909:
            disposition='hold'; proposed=None; kind=None
            rationale='No exact production caller was found for this catalog entry. The source text does not establish whether it remains reachable or what behavior it describes, so preserve the current value until source ownership is confirmed.'
            confidence='low'
        elif proposal:
            proposed,kind,rationale=proposal
            disposition=kind
            confidence='moderate'
        else:
            proposed=None; kind=None; disposition='accept-current'
            rationale='The current target preserves the source meaning and matches the pinned caller, UI role, and locale register.'
            confidence='moderate'
        final=proposed if proposed is not None else current
        current_leaves=text_leaves(current); final_leaves=text_leaves(final)
        current_bad=(not current_leaves or any(sorted(PLACEHOLDER.findall(t))!=source_placeholders for t in current_leaves))
        final_bad=(not final_leaves or any(sorted(PLACEHOLDER.findall(t))!=source_placeholders for t in final_leaves))
        current_markup_bad=any(MARKUP.findall(t)!=source_markup for t in current_leaves)
        final_markup_bad=any(MARKUP.findall(t)!=source_markup for t in final_leaves)
        if current_bad or final_bad: placeholder_mismatches.append({'sourceIndex':index,'locale':locale,'currentMismatch':current_bad,'finalMismatch':final_bad})
        if current_markup_bad or final_markup_bad: markup_mismatches.append({'sourceIndex':index,'locale':locale,'currentMismatch':current_markup_bad,'finalMismatch':final_markup_bad})
        protected=PROTECTED.get(index,[])
        protected_missing=[token for token in protected if any(token not in t for t in final_leaves)]
        if protected_missing: protected_mismatches.append({'sourceIndex':index,'locale':locale,'tokens':protected_missing})
        p_compatible=punctuation_compatible(source,final)
        if not p_compatible: punctuation_findings.append({'sourceIndex':index,'locale':locale,'sourceTerminal':term_punctuation(source),'currentTerminal':[term_punctuation(t) for t in current_leaves],'finalTerminal':[term_punctuation(t) for t in final_leaves]})
        caller_refs=[f"{p['path']}:{p['line']}" for p in source_callers if p['sourceIndex']==index]
        review.append({'sourceIndex':index,'windowLabel':index+1,'sourceId':source,'sourceSha256':sha_bytes(source),'locale':locale,'currentTarget':current,'currentTargetSha256':sha_target(current),'disposition':disposition,'proposalKind':kind,'proposedTarget':proposed,'proposedTargetSha256':sha_target(proposed) if proposed is not None else None,'reviewedFinal':final,'reviewedFinalSha256':sha_target(final),'rationale':rationale,'confidence':confidence,'callerReferences':caller_refs,'contextType':CONTEXT_TYPE[index],'sourcePlaceholders':source_placeholders,'targetPlaceholderParity':'exact' if not final_bad else 'mismatch','sourceMarkup':source_markup,'targetMarkupParity':'exact' if not final_markup_bad else 'mismatch','protectedLiterals':protected,'protectedLiteralsPreserved':not bool(protected_missing),'punctuationCompatible':p_compatible,'nativeSpeakerApproval':False})
        formality.append({'sourceIndex':index,'sourceId':source,'locale':locale,'contextType':CONTEXT_TYPE[index],'reviewedRegister':'neutral label or context-appropriate action wording','informalSecondPersonIntroduced':False,'note':'Spanish progress instruction uses formal Continúe; Hindi actions use polite imperative; other direct actions follow established locale button conventions.' if locale in ('es','hi') else 'No informal second-person address is introduced by this label, status, toast, or action wording.'})
assert len(review)==240
assert not placeholder_mismatches, placeholder_mismatches
assert not markup_mismatches, markup_mismatches
assert not protected_mismatches, protected_mismatches
assert not punctuation_findings, punctuation_findings
assert all_prs[4]['headRefOid'] == HEAD_EXPECTED

# Boundary target pins include the preceding W902 row and the following W923 row.
boundary_pins=[]
for index in (START-1,END+1):
    source=shared_keyset[index]
    for locale in LOCALES:
        target=catalogs[locale][source]
        boundary_pins.append({'sourceIndex':index,'windowLabel':index+1,'sourceId':source,'sourceSha256':sha_bytes(source),'locale':locale,'target':target,'targetSha256':sha_target(target)})
source_window=[{'sourceIndex':i,'windowLabel':i+1,'sourceId':shared_keyset[i],'sourceSha256':sha_bytes(shared_keyset[i])} for i in range(START-1,END+2)]

# Internal terminology references are exact-head comparisons, not previous approval claims.
term_references=[]
for term,relation in [('Members','plural noun used by the contributing-member count'),('Copy Action Plan','action-verb comparison for copy controls'),('Copy Contract','action-verb comparison for copy controls'),('Copy Discovery Graph branch report','action-verb comparison for copy controls'),('Copy History','action-verb comparison for copy controls'),('Cooldown Milliseconds','unit-expression comparison for cooldown labels')]:
    if term not in shared_keyset: continue
    idx=shared_keyset.index(term)
    for locale in LOCALES:
        target=catalogs[locale][term]
        term_references.append({'referenceSourceIndex':idx,'sourceId':term,'sourceSha256':sha_bytes(term),'locale':locale,'target':target,'targetSha256':sha_target(target),'relation':relation,'status':'same-head lexical/context reference only; no prior semantic approval is implied'})

counts=collections.Counter(r['disposition'] for r in review)
proposal_kinds=collections.Counter(r['proposalKind'] for r in review if r['proposalKind'])
changed=sum(1 for r in review if r['proposedTarget'] is not None and sha_target(r['proposedTarget'])!=r['currentTargetSha256'])
summary={'repository':REPO,'pullRequest':PR,'window':'W903-W922','zeroBasedSourceIndexInclusive':[START,END],'head':head,'tree':tree,'branch':BRANCH,'state':pr['state'],'isDraft':pr['isDraft'],'sourceCount':20,'cellCount':len(review),'counts':dict(counts),'proposalKindCounts':dict(proposal_kinds),'proposedValueChanges':changed,'holdCellCount':counts.get('hold',0),'catalogKeyCount':len(shared_keyset),'catalogsReattested':len(catalogs),'callerPins':len(source_callers),'callerFiles':len({x['path'] for x in source_callers}),'callerGapSources':len(caller_gaps),'callerGaps':caller_gaps,'placeholderMismatches':len(placeholder_mismatches),'markupMismatches':len(markup_mismatches),'protectedLiteralMismatches':len(protected_mismatches),'punctuationFindings':punctuation_findings,'allArabicPluralCategoriesPresent':set(catalogs['ar'][shared_keyset[915]].keys())=={'zero','one','two','few','many','other'},'arabicPluralPlaceholderParity':'exact','catalogKeysetsIdentical':True,'sourceIds':source_ids,'boundarySourceIndices':[START-1,END+1],'boundarySourceIds':[shared_keyset[START-1],shared_keyset[END+1]],'priorBoundaryReattestation':{'priorWindow':'W883-W902','priorHead':prior_manifest['head'],'priorTree':prior_manifest['tree'],'previousW902FinalMatchesCurrent':all(r['matchesPriorWindowFinalReadback'] for r in end_boundary_checks),'W903StartMatchesPreviousFollowingBoundary':all(r['matchesPriorFollowingBoundary'] for r in start_boundary_checks)},'allSevenPullRequestsAtSelection':all_prs,'nativeSpeakerApproval':False,'headedBrowserAcceptance':False,'testsBuildScansCiOrBrowserRun':False,'repositoryModified':False,'localeOrder':LOCALES}

# Output the primary review packet.
dump_json(OUT/'live-head.json',{'repository':REPO,'pullRequest':PR,'state':pr['state'],'isDraft':pr['isDraft'],'url':pr['url'],'branch':BRANCH,'head':head,'tree':tree,'apiTree':api_tree,'remoteHead':remote,'worktreeStatus':status,'baseRefOid':pr['baseRefOid'],'selectedAtUtc':dt.datetime.now(dt.timezone.utc).isoformat()})
dump_json(OUT/'all-seven-pr-snapshots.json',{'selectedAtUtc':dt.datetime.now(dt.timezone.utc).isoformat(),'pullRequests':all_prs})
dump_jsonl(OUT/'catalog-pins.jsonl',catalog_pins)
dump_jsonl(OUT/'review-ledger.jsonl',review)
dump_jsonl(OUT/'source-caller-pins.jsonl',source_callers)
dump_jsonl(OUT/'caller-gaps.jsonl',caller_gaps)
dump_jsonl(OUT/'boundary-pins.jsonl',boundary_pins)
dump_jsonl(OUT/'source-window-and-boundaries.jsonl',source_window)
dump_jsonl(OUT/'locale-formality-checks.jsonl',formality)
dump_jsonl(OUT/'glossary-reference-pins.jsonl',term_references)
dump_json(OUT/'prior-disposition-boundary-reattestation.json',{'priorWindow':'W883-W902','priorHead':prior_manifest['head'],'priorTree':prior_manifest['tree'],'previousW902FinalReadbackChecks':end_boundary_checks,'newW903StartVsPreviousPinnedBoundary':start_boundary_checks,'allChecksPass':True})
dump_json(OUT/'summary.json',summary)
(OUT/'terminology-sources.md').write_text('''# Terminology and context references — W903–W922\n\n- `Continue` is the backfill button, while `Continue processing search history...` is its progress popup. The button action is reviewed separately from the progress instruction; the Spanish instruction keeps formal address.\n- `Continuous` is an automation recipe cadence value, not a physical or geometric continuity description.\n- `Contract` is the table column for the media-server execution contract. `Copy Contract` is the action for copying the live execution contract; adjacent descriptions explicitly call it an execution contract.\n- `Contributing Members:` is the count of members who contributed content opinions, not members who donated.\n- `Cooldown` is the minimum interval between automation recipe runs. `Cooldown Milliseconds` is the Pushbullet setting whose numeric value is measured in milliseconds. Locale strings are reviewed against those callers and the paired label.\n- `Copy`, `Copy Action Plan`, `Copy Contract`, `Copy Discovery Graph branch report`, and `Copy History` are action buttons. Same-head local entries are pinned for lexical consistency in `glossary-reference-pins.jsonl`; these references are context only and do not imply prior semantic approval.\n- Source `Control URL` uses the exact technical literal `URL`, preserved in each final value.\n- Source `Control the local review panel shown with song search results.` exists in the catalogs but has no exact production `web/src` source-literal caller at this head. All twelve locale cells are held pending source-owner/context confirmation.\n- The Arabic target for `Copied {format} export for {count} plays.` is an ICU object. It has all six categories (`zero`, `one`, `two`, `few`, `many`, `other`). Object target hashes use canonical UTF-8 JSON with sorted keys and compact separators; every leaf preserves `{format}` and `{count}`.\n\nAll review judgments are machine-assisted. No external glossary or native-speaker authority is claimed.\n''')

(OUT/'README.md').write_text(f'''# slskR PR #204 primary semantic review — W903–W922\n\nReviewed 20 sorted source IDs × 12 direct locales (240 cells) at exact open/draft PR head `{head}`, tree `{tree}`. All 12 direct locale catalogs were reattested with the same ordered 5,441-key set. The preceding W902 final readback and W903 starting-boundary values were reattested against W883–W902 evidence.\n\nPrimary dispositions: `{dict(counts)}`. Proposed value changes: {changed} ({dict(proposal_kinds)}). The 12 held cells are the catalog-only `Control the local review panel shown with song search results.` entry, which has no exact production source-literal caller at this head; the other 19 source IDs have pinned caller context.\n\nThe review covers the backfill continuation action and progress copy, automation cadence/cooldown wording, member attribution, media-server execution-contract labels, clipboard actions, and Arabic ICU plural punctuation. All 240 targets have exact placeholder and markup parity; `URL` is preserved in the VPN field label. Arabic plural categories and placeholder parity are complete.\n\nThis is a static machine-assisted primary review packet. It does not establish native-speaker approval or current-head browser acceptance. No repository files changed; no tests, builds, scans, CI jobs, or browser actions ran.\n''')

# Add compact, machine-verifiable checksums and the packet manifest.
files=sorted(p for p in OUT.iterdir() if p.is_file() and p.name not in ('SHA256SUMS','manifest.json'))
(OUT/'SHA256SUMS').write_text(''.join(f'{sha_bytes(p.read_bytes())}  {p.name}\n' for p in files))
manifest={'repository':REPO,'pullRequest':PR,'window':'W903-W922','head':head,'tree':tree,'branch':BRANCH,'sourceCount':20,'cellCount':len(review),'dispositionCounts':dict(counts),'proposalKindCounts':dict(proposal_kinds),'proposedValueChanges':changed,'heldCells':counts.get('hold',0),'files':[{'path':p.name,'bytes':p.stat().st_size,'sha256':sha_bytes(p.read_bytes())} for p in files],'sha256SumsSha256':sha_bytes((OUT/'SHA256SUMS').read_bytes())}
dump_json(OUT/'manifest.json',manifest)
print(json.dumps({'output':str(OUT),'head':head,'tree':tree,'counts':dict(counts),'proposalKindCounts':dict(proposal_kinds),'proposedValueChanges':changed,'callerPins':len(source_callers),'callerGaps':len(caller_gaps),'punctuationFindings':punctuation_findings,'manifestSha256':sha_bytes((OUT/'manifest.json').read_bytes()),'sha256SumsSha256':sha_bytes((OUT/'SHA256SUMS').read_bytes())},ensure_ascii=False))
