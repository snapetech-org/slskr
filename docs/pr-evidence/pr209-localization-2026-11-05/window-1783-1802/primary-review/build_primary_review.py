#!/usr/bin/env python3
"""Build the slskR W1783-W1802 primary semantic review from sealed candidate-free input."""
from __future__ import annotations
import hashlib, json, re, shutil
from collections import Counter
from pathlib import Path

OUT=Path(__file__).resolve().parent
INPUT=OUT.parent/'candidate-free-input'
HEAD='0264a4fcaa944fee61049efec0cf3c451416c8b9'
TREE='895e57c178d959a23aceddead27623f2dd854ba0'

# position, locale -> (disposition, proposal, rationale)
# Unlisted cells retain their exact current target after caller-backed review.
ALT={
 (1783,'vi'):('correction','Độ biến thiên phổ','This is the spectralFlux metric label in the SongID evidence panel. Tuôn ra means a physical gush/flow; the proposal names the spectral variation metric.'),
 (1784,'es'):('refinement','Filtrar por el álbum candidato {album}','The caller is a filter-focus button, and its pinned tooltip says it focuses the result filter on the album folder name. This makes the action clear and keeps the {album} placeholder.'),
 (1784,'de'):('correction','Nach Albumkandidat {album} filtern','The caller focuses the current result filter on the album folder name. Hervorheben means visually highlight, which is not this action.'),
 (1785,'de'):('correction','Richten Sie den aktuellen Ergebnisfilter auf den Namen dieses Albumordners aus, ohne eine weitere Suche oder einen Download zu starten.','The caller filters by the album folder name, not the album title; the current Albumnamen drops the folder distinction.'),
 (1785,'fr'):('refinement','Filtrez les résultats actuels selon le nom de ce dossier d’album sans lancer une autre recherche ni un téléchargement.','The caller describes changing the current result filter; this is more direct and idiomatic than targeting the filter.'),
 (1785,'pt-BR'):('refinement','Filtre os resultados atuais pelo nome desta pasta do álbum sem iniciar outra busca nem outro download.','The caller changes the existing result filter to the folder name; the proposal states that action directly.'),
 (1785,'hi'):('refinement','नई खोज या डाउनलोड शुरू किए बिना, इस एल्बम फ़ोल्डर के नाम से मौजूदा परिणामों को फ़िल्टर करें।','The caller filters existing results by the album-folder name. This uses natural Hindi word order and preserves both constraints.'),
 (1786,'es'):('refinement','Flujo de trabajo del pod seleccionado','The caller displays the selectedPodWorkflow label under this heading. Seleccionado conveys focused as the active selection more clearly.'),
 (1786,'zh-Hans'):('refinement','当前选定的 Pod 工作流程','The caller immediately shows the selected workflow label; 当前选定的 clarifies focused as the active selection.'),
 (1786,'ja'):('refinement','選択中の Pod ワークフロー','The caller presents the selectedPodWorkflow label below this heading. 選択中 conveys the active selection more naturally than 集中的な.'),
 (1786,'fr'):('correction','Flux de travail du pod sélectionné','The caller shows one selected pod workflow. The current plural des pods ciblés reads as workflows of multiple targeted pods.'),
 (1786,'pt-BR'):('refinement','Fluxo de trabalho do pod selecionado','The caller shows the selected pod workflow; selecionado is clearer than focado in this status heading.'),
 (1786,'ar'):('refinement','سير عمل Pod المحدد','The caller shows the active selected workflow. Keeping Pod identifies the product entity, and المحدد expresses the selected workflow.'),
 (1786,'zh-Hant'):('refinement','目前選取的 Pod 工作流程','The caller shows the selected workflow label; 目前選取的 makes the active selection clear.'),
 (1786,'vi'):('refinement','Quy trình làm việc của Pod đang được chọn','The caller shows the selected pod workflow. This preserves the Pod entity instead of recasting it as a generic group.'),
 (1786,'id'):('refinement','Alur kerja pod yang dipilih','The caller shows the selectedPodWorkflow label; yang dipilih is clearer than terfokus for the selected state.'),
 (1791,'es'):('correction','Agrupar resultados duplicados','This is the setting label for grouping duplicate search results. Doblar means physically bend/fold and is misleading here.'),
 (1791,'hi'):('correction','डुप्लिकेट परिणाम समेटें','This setting groups duplicate results. मोड़ें suggests physically bending; समेटें conveys folding/grouping results.'),
 (1791,'de'):('correction','Doppelte Ergebnisse gruppieren','The caller sets a duplicate-result grouping option; falten is a physical folding verb.'),
 (1791,'fr'):('correction','Regrouper les résultats en double','The caller sets a duplicate-result grouping option; plier is a physical folding verb.'),
 (1791,'pt-BR'):('correction','Agrupar resultados duplicados','The caller sets a duplicate-result grouping option; dobrar suggests physical folding.'),
 (1791,'ar'):('correction','تجميع النتائج المكررة','The caller sets a duplicate-result grouping option. أضعاف does not express the grouping action naturally.'),
 (1791,'vi'):('correction','Gộp kết quả trùng lặp','The caller sets a duplicate-result grouping option; gấp suggests physically folding items.'),
 (1791,'id'):('correction','Kelompokkan hasil duplikat','The caller sets a duplicate-result grouping option; lipat suggests physically folding items.'),
 (1792,'es'):('refinement','Agrupa los resultados que probablemente estén duplicados en una sola fila de revisión cuando haya compatibilidad con la paginación.','This is explanatory copy for duplicate grouping. Agrupa is clearer than doblar, and the wording describes likely duplicates and page support.'),
 (1792,'hi'):('refinement','पेजिंग समर्थन उपलब्ध होने पर संभावित डुप्लिकेट नतीजों को एक ही समीक्षा पंक्ति में समूहित करें।','The caller describes grouping probable duplicates into one review row when pagination is supported; this avoids the physical-fold sense of मोड़ें.'),
 (1792,'de'):('refinement','Fassen Sie wahrscheinlich doppelte Ergebnisse in einer einzigen Prüfzeile zusammen, sofern Seitenunterstützung verfügbar ist.','The caller describes combining likely duplicates into one review row; zusammenfassen is natural for the grouping action.'),
 (1792,'ja'):('correction','ページサポートが利用可能な場合は、重複する可能性のある結果を単一のレビュー行にまとめます。','The English source uses the word single, not a numeric token. 単一の preserves that meaning without introducing an unmatched digit.'),
 (1792,'fr'):('refinement','Regroupez les résultats susceptibles d’être des doublons dans une seule ligne de révision lorsque la pagination est prise en charge.','This is explanatory copy for grouping likely duplicates into one review row when page support is available.'),
 (1792,'pt-BR'):('correction','Agrupe os resultados que provavelmente são duplicados em uma única linha de revisão quando houver suporte a páginas.','The current contains two zero-width characters and an awkward provável duplicados phrase. This is clean Brazilian Portuguese and preserves the condition.'),
 (1792,'ar'):('refinement','اجمع النتائج التي يُحتمل تكرارها في صف مراجعة واحد عند توفر دعم الصفحات.','The caller describes grouping likely duplicates into one review row; اجمع expresses grouping more naturally than literal folding.'),
 (1792,'vi'):('correction','Gộp các kết quả có khả năng trùng lặp thành một hàng đánh giá duy nhất khi có hỗ trợ phân trang.','The caller describes grouping results into a single review row; gấp suggests physically folding items.'),
 (1792,'id'):('correction','Kelompokkan hasil yang kemungkinan duplikat ke dalam satu baris ulasan saat dukungan halaman tersedia.','The caller describes grouping likely duplicates into one review row; lipat suggests physically folding items.'),
 (1795,'vi'):('refinement','Theo dõi chương trình phát sóng của phòng','This is an accessible action label for following the room stream. The proposal supplies the natural possessive phrase của phòng.'),
 (1796,'es'):('refinement','Sigue la reproducción del host de este pod usando tu propio acceso a la transmisión.','The neighboring Spanish UI uses informal tú forms. The current Siga/su register is inconsistent with Enfoca and Abre in this window.'),
 (1796,'zh-Hans'):('refinement','使用您自己的流媒体访问权限，跟随此 Pod 主机的播放。','This is the listen-along action for a pod host; 跟随 is more natural for following playback than 跟踪, which suggests tracking.'),
 (1796,'ja'):('refinement','自分のストリームアクセスを使って、この Pod のホストの再生に合わせて聴きます。','The caller is a volume/follow playback action. 再生に合わせて聴く conveys listening along rather than tracking playback.'),
 (1796,'fr'):('correction','Suivez la lecture de l’hôte de ce pod en utilisant votre propre accès au flux.','The caller means the pod host’s playback. The current lecture hôte construction is unidiomatic; this makes the relationship explicit.'),
 (1796,'ar'):('refinement','تابع تشغيل مضيف هذا الـ Pod باستخدام وصولك الخاص إلى البث.','This is a listen-along action. The proposal keeps the Pod entity and states own access to the stream more directly.'),
 (1796,'zh-Hant'):('refinement','使用您自己的串流存取權限，跟隨此 Pod 主機的播放。','This is the listen-along action for a pod host; 跟隨 is more natural for following playback than 追蹤, which suggests tracking.'),
 (1796,'vi'):('correction','Theo dõi nội dung phát của chủ Pod này bằng quyền truy cập luồng riêng của bạn.','The caller means playback from the pod host. Máy chủ means server and nhóm means generic group, so this names the host and Pod accurately.'),
 (1797,'es'):('refinement','Sigue la transmisión de esta sala usando tu propio acceso a la transmisión.','The neighboring Spanish UI uses informal tú forms; replace the inconsistent formal Siga/su with Sigue/tu.'),
 (1799,'es'):('refinement','A favor:','The caller labels evidence supporting a SongID hypothesis, paired with evidence against; A favor is clearer than the generic Para.'),
 (1799,'zh-Hans'):('correction','支持：','The caller labels evidence supporting a SongID hypothesis. 为了 means for the purpose of, not supporting evidence.'),
 (1799,'hi'):('correction','पक्ष में:','The caller labels evidence in favor of a SongID hypothesis; पक्ष में expresses that polarity.'),
 (1799,'ja'):('correction','支持：','The caller labels supporting evidence, paired with evidence against. のために means for the sake/purpose of, not evidence in support.'),
 (1799,'pt-BR'):('refinement','A favor:','The caller labels evidence supporting a SongID hypothesis, paired with evidence against; A favor is clearer than generic Para.'),
 (1799,'ar'):('correction','ما يؤيد:','The caller labels evidence that supports a SongID hypothesis. This heading expresses what supports it, rather than an isolated preposition.'),
 (1799,'ko'):('correction','지지 근거:','The caller labels evidence supporting a SongID hypothesis. 을 위한 is an incomplete modifier phrase here.'),
 (1799,'zh-Hant'):('correction','支持：','The caller labels supporting evidence; 為了 means for the purpose of, not support.'),
 (1799,'vi'):('correction','Ủng hộ:','The caller labels evidence supporting a SongID hypothesis; Vì means because and changes the relationship.'),
 (1799,'id'):('refinement','Mendukung:','The caller labels supporting evidence paired with evidence against; Mendukung is clearer than purpose-like Untuk.'),
 (1800,'es'):('refinement','Forzar HTTPS','This is a checkbox label paired with Force HTTPS redirects. The infinitive matches that label style better than the informal imperative Fuerza.'),
 (1800,'zh-Hans'):('correction','强制 HTTPS','The caller is an admin policy checkbox that enforces HTTPS redirects. 力 is not a verb and does not express the action.'),
 (1800,'hi'):('refinement','HTTPS अनिवार्य करें','The caller is an admin policy to require HTTPS; this is clearer Hindi than transliterating Force.'),
 (1800,'de'):('refinement','HTTPS erzwingen','This is a checkbox label parallel to HTTPS-Weiterleitungen erzwingen; the infinitive is appropriate, while Erzwinge is a direct imperative.'),
 (1800,'ja'):('correction','HTTPS を強制する','The caller is an admin policy checkbox. 力 is a noun for strength and does not express enforcing HTTPS.'),
 (1800,'ar'):('correction','فرض HTTPS','The caller is an admin policy checkbox that enforces HTTPS; قوة means strength/power rather than the enforcement action.'),
 (1800,'zh-Hant'):('correction','強制 HTTPS','The caller is an admin policy checkbox; 力 is not the verb for enforcing HTTPS.'),
 (1801,'hi'):('refinement','HTTPS पर रीडायरेक्ट अनिवार्य करें','The caller forces HTTP requests to redirect to HTTPS after certificate setup; this is clearer than a transliterated Force label.'),
 (1801,'ar'):('refinement','فرض إعادة التوجيه إلى HTTPS','The caller enforces redirects to HTTPS; this is more natural than عمليات إعادة التوجيه HTTPS.'),
 (1802,'es'):('correction','Matrix forense','Matrix is a protected product term and must remain exact. The adjective follows it naturally in Spanish.'),
 (1802,'zh-Hans'):('correction','取证 Matrix','Matrix is a protected product term and must remain exact; 取证 translates the forensic qualifier.'),
 (1802,'hi'):('correction','फोरेंसिक Matrix','Matrix is a protected product term and must remain exact; फोरेंसिक translates the qualifier.'),
 (1802,'ja'):('correction','フォレンジック Matrix','Matrix is a protected product term and must remain exact; フォレンジック is the technical forensic modifier.'),
 (1802,'fr'):('correction','Matrix forensique','Matrix is a protected product term and must remain exact; forensique is the natural French modifier.'),
 (1802,'pt-BR'):('correction','Matrix Forense','Matrix is a protected product term and must remain exact; Forense translates the qualifier.'),
 (1802,'ar'):('correction','Matrix جنائية','Matrix is a protected product term and must remain exact; جنائية conveys the forensic modifier.'),
 (1802,'ko'):('correction','포렌식 Matrix','Matrix is a protected product term and must remain exact; 포렌식 translates the forensic qualifier.'),
 (1802,'zh-Hant'):('correction','鑑識 Matrix','Matrix is a protected product term and must remain exact; 鑑識 is a Traditional Chinese forensic modifier.'),
 (1802,'vi'):('correction','Matrix pháp chứng','Matrix is a protected product term and must remain exact; pháp chứng conveys the forensic qualifier.'),
 (1802,'id'):('correction','Matrix Forensik','Matrix is a protected product term and must remain exact; Forensik translates the qualifier.'),
}

def digest(b): return hashlib.sha256(b).hexdigest()
def jl(path): return [json.loads(x) for x in path.read_text(encoding='utf-8').splitlines() if x.strip()]
def main():
    m=json.loads((INPUT/'manifest.json').read_text(encoding='utf-8'))
    if (m['head'],m['tree'])!=(HEAD,TREE): raise SystemExit('input pin mismatch')
    rows=jl(INPUT/'current-target-cells.jsonl')
    sources={d['position']:d for d in jl(INPUT/'source-queue.jsonl')}
    contexts={d['position']:d for d in jl(INPUT/'source-contexts.jsonl')}
    if len(rows)!=240 or len({(r['position'],r['locale']) for r in rows})!=240: raise SystemExit('cell coverage mismatch')
    if sorted({r['position'] for r in rows})!=list(range(1783,1803)): raise SystemExit('position coverage mismatch')
    if len(sources)!=5441 or len(contexts)!=20: raise SystemExit('source or caller context coverage mismatch')
    if m['activeHoldIds']!=['1719::id'] or m['activeHoldTargetHashUnchanged'] is not True or m['activeHoldSourceContextUnchanged'] is not True: raise SystemExit('active hold attestation mismatch')
    shutil.copyfile(INPUT/'active-hold-reattestation.jsonl',OUT/'active-hold-reattestation.jsonl')
    shutil.copyfile(INPUT/'previous-window-readback-reattestation-hash-only.jsonl',OUT/'previous-window-readback-reattestation-hash-only.jsonl')
    if len(ALT)!=sum(1 for r in rows if (r['position'],r['locale']) in ALT): raise SystemExit('duplicate decision key')
    out=[]; counts=Counter(); token_before=Counter(); token_after=Counter()
    for r in rows:
        pos,locale=r['position'],r['locale']; src=sources[pos]; ctx=contexts[pos]
        if r['sourceKey']!=src['sourceKey'] or r['sourceKeySha256']!=src['sourceKeySha256']: raise SystemExit(f'source pin mismatch at {pos}/{locale}')
        if r['sourceContextSha256']!=ctx['callerContextSha256']: raise SystemExit(f'caller context pin mismatch at {pos}/{locale}')
        if not r['targetTextIncluded'] or not isinstance(r.get('currentTarget'),str): raise SystemExit(f'expected caller-backed target missing at {pos}/{locale}')
        var=r['targetTokenVariants'][0]
        if not var['numericTokensMatch']: token_before['numeric']+=1
        if not var['protectedLiteralsMatch']: token_before['protectedLiteral']+=1
        if not var['placeholderSequenceMatches']: token_before['placeholder']+=1
        if not var['markupMatches']: token_before['markup']+=1
        alt=ALT.get((pos,locale))
        if alt:
            disp,target,why=alt
        else:
            disp,target='accept_current',r['currentTarget']
            why='The current translation preserves the source meaning in its pinned caller context and is suitable UI copy for this locale; retain it.'
        proposed_ph=re.findall(r'\{[A-Za-z][A-Za-z0-9_]*\}',target)
        proposed_num=re.findall(r'\d+',target)
        source_num=r['sourceNumericTokens']
        source_ph=r['sourcePlaceholders']
        protected=r['sourceProtectedLiterals']
        proposed_markup=re.findall(r'</?[A-Za-z][^>]*>',target)
        p_ok=proposed_ph==source_ph
        n_ok=proposed_num==source_num
        m_ok=proposed_markup==r['sourceMarkupTags']
        l_ok=all(lit in target for lit in protected)
        if not (p_ok and n_ok and m_ok and l_ok): raise SystemExit(f'proposed token fidelity failed at {pos}/{locale}: placeholders={p_ok} numeric={n_ok} markup={m_ok} protected={l_ok}')
        token_after['numeric']+=int(not n_ok); token_after['protectedLiteral']+=int(not l_ok); token_after['placeholder']+=int(not p_ok); token_after['markup']+=int(not m_ok)
        refs=[{'path':c['path'],'line':c['line'],'lineText':c['lineText'],'lineSha256':c['lineSha256'],'contextStartLine':c['contextStartLine'],'contextEndLine':c['contextEndLine'],'contextSha256':c['contextSha256'],'fileSha256':c['fileSha256'],'gitBlob':c['gitBlob']} for c in ctx['callers']]
        e={
          'window':'W1783-W1802','position':pos,'locale':locale,'sourceKey':src['sourceKey'],'sourceKeySha256':src['sourceKeySha256'],
          'currentTarget':r['currentTarget'],'currentTargetSha256':r['currentTargetSha256'],'proposedTarget':target,
          'proposedTargetSha256':digest(target.encode('utf-8')),'catalogPath':r['catalogPath'],'catalogFileSha256':r['catalogFileSha256'],'catalogGitBlob':r['catalogGitBlob'],
          'callerContextSha256':ctx['callerContextSha256'],'callerReferenceCount':ctx['callerOccurrenceCount'],'callerReferences':refs,
          'sourcePlaceholders':source_ph,'proposedPlaceholders':proposed_ph,'sourceNumericTokens':source_num,'proposedNumericTokens':proposed_num,
          'sourceMarkupTags':r['sourceMarkupTags'],'proposedMarkupTags':proposed_markup,'sourceProtectedLiterals':protected,
          'proposedProtectedLiteralsPreserved':l_ok,'candidateFreeBaselineTokenAudit':var,
          'proposedTokenAudit':{'placeholderSequenceMatches':p_ok,'numericTokensMatch':n_ok,'markupMatches':m_ok,'protectedLiteralsMatch':l_ok},
          'disposition':disp,'rationale':why,'confidence':'moderate','reviewMethod':'primary machine semantic review',
          'nativeSpeakerApproval':False,'candidateFreeOnly':True
        }
        out.append(e); counts[disp]+=1
    with (OUT/'primary-semantic-review-ledger.jsonl').open('w',encoding='utf-8',newline='\n') as f:
        for e in out: f.write(json.dumps(e,ensure_ascii=False,sort_keys=True,separators=(',',':'))+'\n')
    next_boundary=[d for d in jl(INPUT/'source-window-boundaries.jsonl') if d['position']==1803][0]
    summary={
      'artifact':'slskR PR #209 W1783-W1802 primary semantic review','repository':'snapetech-org/slskR','pullRequest':209,
      'window':'W1783-W1802','head':HEAD,'tree':TREE,'candidateFreeInput':'../candidate-free-input',
      'candidateFreeChecksumListSha256':digest((INPUT/'SHA256SUMS.txt').read_bytes()),
      'cells':len(rows),'sourceCount':20,'localeCount':12,'callerReferences':m['callerReferenceCount'],'callerlessSourceCount':0,
      'dispositions':dict(sorted(counts.items())),'proposedChanges':counts['correction']+counts['refinement'],
      'baselineTokenMismatchCounts':m['tokenMismatchCounts'],'proposedTokenMismatchCounts':dict(sorted(token_after.items())),
      'protectedMatrixCellsPreserved':sum(1 for r in out if r['position']==1802 and r['proposedTokenAudit']['protectedLiteralsMatch']),
      'activeHoldReattestedHashOnly':'1719::id','activeHoldTargetHashUnchanged':True,'activeHoldSourceContextUnchanged':True,
      'previousWindowReadbackHashesCopiedUnchanged':240,'nextBoundary':next_boundary,
      'runtimeContextPath':json.loads((INPUT/'localization-runtime-context.json').read_text())['path'],
      'runtimeContextSha256':json.loads((INPUT/'localization-runtime-context.json').read_text())['pin']['sha256'],
      'reviewMethod':'Primary semantic review using candidate-free exact-head source/current/caller/runtime evidence only',
      'nativeSpeakerApproval':False,'confidence':'moderate','productWorktreeEdited':False,'catalogValuesApplied':False,'testsBuildsScansCiRun':False
    }
    (OUT/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    readme=f'''# slskR PR #209 W1783–W1802 primary semantic review\n\nPinned to PR HEAD `{HEAD}` / tree `{TREE}`. The only review input is the sealed candidate-free packet `../candidate-free-input`; its `SHA256SUMS.txt` SHA256 is `{summary['candidateFreeChecksumListSha256']}`. The packet covers 240 cells (20 source keys × 12 locales), with 29 exact caller references and no callerless source positions.\n\nThe ledger contains {counts['accept_current']} accept-current rows, {counts['correction']} corrections, and {counts['refinement']} refinements. It preserves the 1719::id active hold as hash-only and copies the previous window’s 240 hash-only readbacks unchanged. Current-target token audit flagged one Japanese numeric token and 11 protected `Matrix` literals; the proposed values resolve both, while retaining every named placeholder, markup token, number, and protected literal.\n\nThis is a primary machine semantic review only; native-speaker approval is not included. Confidence is moderate. No product files or catalogs were changed, and no tests/builds/CI were run.\n\nVerify the packet with `python3 -B verify_primary_review.py --candidate-free ../candidate-free-input`.\n'''
    (OUT/'README.md').write_text(readme,encoding='utf-8')
if __name__=='__main__': main()
