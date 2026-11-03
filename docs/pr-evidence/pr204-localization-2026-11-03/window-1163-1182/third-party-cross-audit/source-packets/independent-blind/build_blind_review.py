from __future__ import annotations
import hashlib, json, re
from collections import Counter
from pathlib import Path

INPUT = Path('/mnt/disks/scratch/task-scratch/slskr-pr204-w1163-1182-clean-input-20261103/clean-input')
OUT = Path('/mnt/disks/scratch/task-scratch/slskr-pr204-w1163-1182-independent-blind-20261103')
manifest = json.loads((INPUT/'manifest.json').read_text(encoding='utf-8'))
input_sha = {line.split('  ',1)[1]:line.split('  ',1)[0] for line in (INPUT/'SHA256SUMS.txt').read_text().splitlines()}

# Independent blind decisions authored from the candidate-free source/current cells
# and their pinned caller contexts only.
CHANGES = {
(1164,'ar'):('correction-proposal','اكتشف البودات عبر DHT باستخدام معرّفات الأسماء والوسوم وروابط المحتوى','القرون تعني قرون الحيوانات (horns)، لا pod؛ هذه الصياغة تستبدلها بالبودات وتصف مدخلات الاسم والوسوم وروابط المحتوى مع إبقاء DHT حرفيًا.','moderate'),
(1164,'hi'):('correction-proposal','नाम स्लग, टैग और सामग्री के संबंधों का उपयोग करके DHT के माध्यम से पॉड खोजें','सामग्री संघों अस्वाभाविक और भ्रामक है; संबंधों सामग्री-संबंधी association का बेहतर अर्थ देता है। DHT और slug/पॉड तकनीकी शब्द बने रहते हैं।','low'),
(1164,'vi'):('correction-proposal','Khám phá các pod qua DHT bằng slug của tên, thẻ và liên kết nội dung','sên tên को शाब्दिक रूप से पढ़ने पर यह mollusk “snail/slug” की ओर जाता है; slug को तकनीकी रूप में रखना सही है। बाकी वाक्य DHT, tags और content links बताता है।','moderate'),
(1164,'zh-Hans'):('refinement-proposal','使用名称 slug、标签和内容关联通过 DHT 发现 Pod','名称别名更接近“name alias”，不表达技术 slug；候选保留 slug 和 DHT，避免把名称标识符误当作别名。','moderate'),
(1164,'zh-Hant'):('refinement-proposal','使用名稱 slug、標籤和內容關聯透過 DHT 發現 Pod','名稱別名較像 name alias，不表達技術 slug；候選保留 slug 和 DHT，避免把名稱識別碼誤作別名。','moderate'),

(1165,'ar'):('hold',None,'المكتوب الحالي بصيغة الأمر، بينما المصدر حالة «Discovered» بجوار عدد. اختيار وصف عربي مناسب يتطلب تثبيت الاسم المحذوف وصيغة العدد؛ المدخل لا يحسمهما، لذا أوقف الصياغة إلى حين مراجعة عربية بشرية.','low'),
(1165,'es'):('refinement-proposal','Descubiertos','الترجمة الحالية بالمفرد، لكن المتصل يعرض عدد العناصر المكتشفة بجوار التسمية؛ صيغة الجمع أوفق لهذا المؤشر.','moderate'),
(1165,'fr'):('refinement-proposal','Découverts','الفرنسية الحالية بالمفرد، بينما التسمية تتبعها قيمة عددية للعناصر المكتشفة؛ الجمع أوفق كعنوان لهذا المؤشر.','moderate'),
(1165,'hi'):('correction-proposal','खोजे गए','की खोज की का अर्थ है “searched for”; المصدر يصف عناصر تم العثور عليها. الصيغة المقترحة تبقي معنى الحالة المكتشفة من دون إضافة اسم غير موجود في النص.','low'),
(1165,'id'):('correction-proposal','Ditemukan','Telah menemukan تصوغ فعلًا نشطًا “has discovered” بفاعل محذوف؛ Ditemukan أنسب كحالة/تسمية للعناصر المكتشفة.','moderate'),
(1165,'ja'):('correction-proposal','検出済み','発見した عبارة ماضٍ نشطة (“discovered [something]”)؛ الصيغة المقترحة حالة موجزة “detected/discovered” تلائم التسمية العددية.','low'),
(1165,'pt-BR'):('refinement-proposal','Descobertos','الترجمة الحالية بالمفرد مع أن التسمية تعرض عدد العناصر؛ الجمع أوفق لعنوان مؤشر متعدد العناصر.','moderate'),
(1165,'zh-Hans'):('refinement-proposal','已发现','发现 وحدها اسم/فعل عام؛ 已发现 يوضح أن هذه حالة مكتملة، كما يلائم عنوان العدد.','low'),
(1165,'zh-Hant'):('refinement-proposal','已發現','發現 وحدها اسم/فعل عام；已發現更清楚地標示完成狀態，也適合作為數量標籤。','low'),

(1166,'hi'):('refinement-proposal','खोजे गए पीयरों की सूची उपलब्ध नहीं है','साथियों تعني رفقاء/companion وقد تخفي معنى peer-to-peer؛ पीयर يحفظ مصطلح الشبكة في سياق قائمة الأقران المكتشفة.','low'),
(1166,'id'):('refinement-proposal','Daftar peer yang ditemukan tidak tersedia','rekan قد تعني زميلًا بشريًا؛ peer يحافظ على معنى نظير الشبكة في قائمة مكتشفة.','moderate'),
(1166,'ja'):('refinement-proposal','検出されたピアの一覧を利用できません','ピアリスト أقل طبيعية من ピアの一覧؛候補 يوضح أن قائمة الأقران المكتشفة غير متاحة.','low'),
(1166,'pt-BR'):('correction-proposal','Lista de peers descobertos indisponível','discovered يصف peers لا القائمة؛ تصريف المكتشفة بالمفرد المؤنث يجعل المعنى “قائمة اكتُشفت”، لذا عدّلت المطابقة.','moderate'),
(1166,'vi'):('refinement-proposal','Danh sách các peer đã phát hiện không khả dụng','ngang hàng تعبير حرفي غريب هنا؛ peer يحافظ على مصطلح شبكة P2P ويجعل رسالة تعذر القائمة أوضح.','low'),
(1166,'zh-Hans'):('refinement-proposal','发现的对等节点列表不可用','对等点 حرفية وغير مألوفة لعنصر شبكة؛ 对等节点 يعبّر بوضوح أكبر عن peer node في قائمة الشبكة.','moderate'),
(1166,'zh-Hant'):('refinement-proposal','發現的對等節點列表不可用','對等點較像直譯；對等節點更清楚地表達網路 peer node。','moderate'),

(1167,'ar'):('correction-proposal','أقران slskr المكتشفون','اكتشف أقران slskr صيغة أمر (“discover peers”) وليست عنوانًا للأقران المكتشفين؛候选把 المكتشفون 与 أقران 对应，并保留 slskr。','low'),
(1167,'es'):('refinement-proposal','Pares de slskr descubiertos','الترجمة الحالية تضع slskr بعد اسم pares بصورة غير طبيعية؛ المرشح يوضح علاقة الاسم بالمنتج مع الحفاظ على المكتشفين.','moderate'),
(1167,'hi'):('correction-proposal','खोजे गए slskr पीयर्स','की खोज की वाक्यांश सक्रिय खोज बताता है لا حالة الأقران الذين تم اكتشافهم؛ الصياغة المقترحة حالة ماضية وتبقي slskr كما هو.','low'),
(1167,'id'):('correction-proposal','Peer slskr yang ditemukan','Menemukan Rekan slskr يقرأ كأن فاعلًا وجد زملاءً؛候选 يعرض الأقران المكتشفين ويحافظ على اسم slskr.','moderate'),
(1167,'ko'):('correction-proposal','발견된 slskr 피어','동료는 زميل بشري/رفيق وليس نظير شبكة؛ 피어 يحفظ peer التقني، والصفة المكتشفة تطابق عنوان الحالة.','low'),
(1167,'pt-BR'):('refinement-proposal','Pares do slskr descobertos','الصياغة الحالية Pares slskr غير طبيعية؛ do يجعل اسم المنتج يصف الأقران مع إبقاء slskr بحالته الدقيقة.','moderate'),
(1167,'vi'):('correction-proposal','Các peer slskr được phát hiện','đồng nghiệp تعني زملاء عمل، لا نظراء شبكة؛ peer يحافظ على المصطلح التقني، وđược phát hiện يطابق الحالة الماضية.','low'),
(1167,'zh-Hans'):('correction-proposal','已发现的 slskr 对等节点','同行表示同业/同事，不是网络 peer；对等节点保留网络含义并保留 slskr。','moderate'),
(1167,'zh-Hant'):('correction-proposal','已發現的 slskr 對等節點','同行表示同業/同事，不是網路 peer；對等節點保留網路含義並保留 slskr。','moderate'),

(1170,'ar'):('refinement-proposal','أطلس مخطط الاكتشاف','رسم الاكتشاف قد يعني رسمًا/رسمة؛ مخطط أوضح كاسم للـGraph في عنوان الأطلس، مع بقاء الاكتشاف قابلًا للترجمة.','low'),
(1170,'de'):('refinement-proposal','Atlas des Entdeckungsgraphen','المتن الألماني يترجم Discovery Graph إلى Entdeckungsgraph؛ إبقاء الاسم الإنجليزي في العنوان يجعل المصطلحات غير متسقة مع التسمية المحلية.','moderate'),
(1170,'hi'):('refinement-proposal','डिस्कवरी ग्राफ़ एटलस','في مواضع Graph المجاورة يستعمل الكتالوج डिस्कवरी ग्राफ़؛ المرشح يتبع هذا المصطلح بدل ترك اسم الميزة بالإنجليزية.','low'),
(1170,'id'):('refinement-proposal','Atlas Graf Penemuan','المرشح يتبع ترجمة التسمية الأساسية Graf penemuan بدل ترتيب إنجليزي غير طبيعي Atlas Discovery Graph.','moderate'),
(1170,'pt-BR'):('refinement-proposal','Atlas do grafo de descoberta','التسمية الأساسية مترجمة إلى grafo de descoberta؛ إعادة استعمالها تجعل اسم اللوحة متسقًا بدل تضمين اسم إنجليزي غير مترجم.','moderate'),
(1170,'vi'):('refinement-proposal','Tập bản đồ đồ thị khám phá','المرشح يترجم graph باللفظ التقني đồ thị، المتسق مع اسم Discovery Graph المحلي، ويتجنب خلط الاسم الإنجليزي في العنوان.','low'),
(1170,'zh-Hant'):('refinement-proposal','探索圖譜集','المسمى الأساسي في الصينية التقليدية يستخدم 探索圖；候选 يتبعه بدل إبقاء Discovery Graph إنجليزيًا داخل العنوان.','moderate'),

(1172,'fr'):('correction-proposal','Le graphe de découverte a été prévisualisé pour {title}.','Graphique de découverte en aperçu تركيب غير طبيعي ويحوّل Graph إلى chart؛ المرشح يستخدم graphe ويصرح بأن معاينة العنوان عُرضت.','moderate'),
(1172,'ko'):('correction-proposal','{title}의 탐색 그래프를 미리 보았습니다.','검색 그래프 يعني search graph لا discovery graph؛ 탐색 그래프 يطابق المصطلح المترجم في بقية الواجهة.','low'),
(1172,'pt-BR'):('correction-proposal','Prévia do grafo de descoberta exibida para {title}.','visualizado تعني viewed/visualized، لا أن المعاينة أُنشئت/عُرضت؛ المرشح يعبّر عن preview ويستخدم grafo مثل الصفحات الأخرى.','moderate'),

(1175,'fr'):('correction-proposal','Taux de découverte','Tarif تعني سعرًا/تعرفة لا معدلًا؛ سياق Statistic.Label يجعل Taux هو المقابل الدقيق لـRate.','high'),
(1176,'fr'):('refinement-proposal','Étagère Découverte','المعنى مفهوم، لكن اسم الرف الفرنسي في رسالة مسح الرف يستخدم Étagère؛ هذا التصحيح يحافظ على اللفظ ويضيف الهمزة الحادة المفقودة.','high'),
(1179,'hi'):('refinement-proposal','खोज में सावधानी','التركيب الحالي खोज सावधानी غير طبيعي؛ المرشح يعبّر بسلاسة أكبر عن الحذر في سياق ملخص تقييم الاكتشاف.','low'),
(1179,'pt-BR'):('refinement-proposal','Cautela na descoberta','Cuidado de descoberta تركيب غير مألوف؛ cautela na descoberta أوفق كتسمية بُعد تحذيري في ملخص تقييم.','moderate'),
(1179,'zh-Hans'):('hold',None,'当前“发现警告”表示 warning/警报；源标签 Discovery caution 出现在播放器评分摘要中，但数据包没有术语表说明这是提醒、风险还是谨慎偏好。保留待中文术语确认。','low'),
(1179,'zh-Hant'):('hold',None,'目前「發現警告」表示 warning/警報；來源標籤 Discovery caution 出現在播放器評分摘要中，但資料包沒有術語表說明這是提醒、風險或謹慎偏好。保留待中文術語確認。','low'),

(1180,'ar'):('hold',None,'الرسالة تتلقى رقمًا لعدد العناصر المنعشة وآخر للمنتهية صلاحيتها. صياغة العدد العربي قد تتغير حسب القيمة والنوع النحوي للمعدود، ولا يقدم السياق تنسيق جمع أو اصطلاحًا محليًا؛ يلزم تدقيق عربي بشري قبل اقتراح نص نهائي.','low'),
(1180,'es'):('correction-proposal','Actualización de descubrimiento completada: {entriesRefreshed} entradas actualizadas y {entriesExpired} entradas caducadas.','الصياغة الحالية تضع وصفين مفردين بعد عددين؛ entradas يوضح المعدود ويجعل المطابقة الإسبانية جمعًا واضحة.','moderate'),
(1180,'fr'):('correction-proposal','Actualisation de la découverte terminée : {entriesRefreshed} entrées actualisées et {entriesExpired} entrées expirées.','الأوصاف في النص الحالي مفردة وتأتي بعد أعداد؛ إضافة entrées وتطابق الجمع يجعل تقرير العدد واضحًا.','moderate'),
(1180,'hi'):('refinement-proposal','डिस्कवरी रिफ्रेश पूरा हुआ: {entriesRefreshed} प्रविष्टियाँ अपडेट हुईं, {entriesExpired} प्रविष्टियों की समय-सीमा समाप्त हुई।','النص الحالي يستخدم أفعالًا مفردة مع قيم عددية بلا معدود؛ المرشح يضيف प्रविष्टियाँ ويطابق الجمع ويبين انتهاء الصلاحية.','low'),
(1180,'ja'):('refinement-proposal','ディスカバリーの更新が完了しました：{entriesRefreshed} 件を更新し、{entriesExpired} 件の有効期限が切れました。','الأعداد الحالية تليها جملتان بلا وحدة عد؛ 件 يجعل عدد العناصر وتجديدها/انتهاءها مقروءًا في اليابانية.','low'),
(1180,'ko'):('correction-proposal','탐색 새로 고침 완료: {entriesRefreshed}개 항목을 새로 고쳤고, {entriesExpired}개 항목이 만료되었습니다.','검색 새로 고침 يترجم Discovery كأنه Search، والصياغة الحالية تسرد الأعداد من دون وحدة أو فعل؛ المرشح يستعمل 탐색 ويشرح عدد العناصر المنعشة والمنتهية.','low'),
(1180,'pt-BR'):('refinement-proposal','Atualização de descoberta concluída: {entriesRefreshed} entradas atualizadas e {entriesExpired} entradas expiradas.','الأوصاف الحالية مفردة بعد أعداد؛ إضافة entradas تجعل المعدود والمطابقة في البرتغالية أوضح.','moderate'),
(1180,'zh-Hans'):('refinement-proposal','发现刷新完成：{entriesRefreshed} 项已刷新，{entriesExpired} 项已过期','中文通常需要量词把数量和项目连接起来；项修复了数字后直接接动词/状态的断裂。','moderate'),
(1180,'zh-Hant'):('refinement-proposal','探索更新完成：{entriesRefreshed} 項已更新，{entriesExpired} 項已過期','中文通常需要量詞把數量和項目連起來；項修復了數字後直接接動詞/狀態的斷裂。','moderate'),

(1182,'ja'):('refinement-proposal','ディスカバリーシェルフがこのブラウザから消去されました。','المعنى الحالي مفهوم لكنه يمزج Discovery الإنجليزية مع シェルフ؛ المصطلح في عنوان الرف المحلي هو ディスカバリーシェルフ، و消去 يوضح تفريغه من هذا المتصفح.','low'),
(1182,'ko'):('correction-proposal','이 브라우저의 탐색 선반을 비웠습니다.','검색 라이브러리 تعني search library، لا Discovery Shelf؛ المرشح يستعمل مصطلح الاستكشاف المحلي والرف ثم فعل “clear”.','low'),
(1182,'pt-BR'):('refinement-proposal','A prateleira de descoberta foi limpa neste navegador.','Prateleira Discovery تمزج إنجليزية غير لازمة مع نص مترجم في بقية الواجهة؛ المرشح يستخدم صياغة برتغالية كاملة ويحافظ على حدث المسح المحلي.','moderate'),
}

DEFAULT_RATIONALES = {
1163:'Caller context shows this text on five localized Discover buttons; the current imperative is an appropriate action label.',
1164:'The current wording conveys discovery via DHT and the name/tag/content inputs without a material error; the exact DHT token is retained.',
1165:'The current wording works as a completed/discovered state beside the discovered-count label; no clear semantic defect found.',
1166:'The current wording states that the discovered peer list cannot be used and fits the localized error heading.',
1167:'The current wording identifies discovered slskr peers and preserves the exact lowercase project literal.',
1168:'The current noun form works as a localized label for the read-only Discovery workflow.',
1169:'The current wording names the Discovery Graph navigation/modal feature and is understandable in its pinned UI contexts.',
1170:'The current wording identifies the Discovery Graph Atlas feature; no material meaning defect found.',
1171:'The current wording accurately reports that the Discovery Graph branch report was copied.',
1172:'The current wording reports a preview for the supplied title and preserves the {title} placeholder.',
1173:'The current wording conveys that a Discovery Graph request is required in the pinned app-error path.',
1174:'The current wording accurately labels the Discovery Keys field and preserves its colon punctuation.',
1175:'The current wording represents a rate metric in the pinned network statistic label.',
1176:'The current wording names the Discovery Shelf UI feature.',
1177:'The current wording accurately labels the Discovery Statistics section.',
1178:'The current wording conveys a positive discovery boost in the dynamic player-rating summary label.',
1179:'The current wording conveys caution in the dynamic player-rating summary label; no glossary evidence resolves a more precise category term.',
1180:'The current wording reports completion and both refreshed/expired counts, preserving each named count placeholder.',
1181:'The current wording is a concise heading for discovery results.',
1182:'The current wording reports that the Discovery Shelf was cleared from the current browser and fits the pinned local-clear action.'
}

RATIONALE_OVERRIDES = {
 (1164,'ar'):'The current القرون means animal horns, not pods. The proposal uses a pod loanword and names the DHT, name-identifier, tag, and content-link inputs.',
 (1164,'hi'):'The current सामग्री संघों is an unnatural rendering of content associations. संबंधों expresses related content more clearly while retaining DHT and slug/pod terminology.',
 (1164,'vi'):'The current sên tên points to the mollusk “snail/slug,” not a technical name slug. The proposal keeps slug as a technical term and preserves the DHT/content-link meaning.',
 (1164,'zh-Hans'):'名称别名 means name alias and loses the technical slug meaning. The proposal retains slug and DHT as technical terms.',
 (1164,'zh-Hant'):'名稱別名 means name alias and loses the technical slug meaning. The proposal retains slug and DHT as technical terms.',
 (1165,'ar'):'The current Arabic is an imperative (“discover”), but the source is a completed-state label beside a count. Arabic wording depends on the implicit noun and number agreement, so hold for native review.',
 (1165,'es'):'The singular participle is awkward beside a variable count. The plural participle better fits the metric label.',
 (1165,'fr'):'The singular participle is awkward beside a variable count. The plural participle better fits the metric label.',
 (1165,'hi'):'The current phrase means “searched for,” not “discovered.” The proposal expresses a discovered state without adding an unsupported noun.',
 (1165,'id'):'Telah menemukan is an active verb with an omitted subject. Ditemukan is a better completed-state label for discovered items.',
 (1165,'ja'):'発見した is an active past-tense verb. 検出済み is a concise completed-state label suitable beside the discovered count.',
 (1165,'pt-BR'):'The singular participle is awkward beside a variable count. The plural participle better fits the metric label.',
 (1165,'zh-Hans'):'已发现 makes the completed state explicit; 发现 alone reads more like a general noun or verb.',
 (1165,'zh-Hant'):'已發現 makes the completed state explicit; 發現 alone reads more like a general noun or verb.',
 (1166,'hi'):'साथियों usually means companions and obscures the peer-to-peer context. पीयर keeps the network term explicit.',
 (1166,'id'):'Rekan can mean a human colleague. Peer keeps the network meaning explicit in this unavailable-list message.',
 (1166,'ja'):'ピアの一覧 is more natural than the compact ピアリスト and keeps the unavailable discovered-peer-list meaning.',
 (1166,'pt-BR'):'The current feminine singular descoberta makes it sound as if the list was discovered. Descobertos correctly modifies the plural peers.',
 (1166,'vi'):'Ngang hàng is an awkward literal rendering here. Peer keeps the network term clear in the unavailable-list message.',
 (1166,'zh-Hans'):'对等节点 is clearer and more idiomatic for a network peer node than the literal 对等点.',
 (1166,'zh-Hant'):'對等節點 is clearer and more idiomatic for a network peer node than the literal 對等點.',
 (1167,'ar'):'The current wording is imperative (“discover slskr peers”), not a label for peers already discovered. The proposal preserves the exact lowercase slskr literal.',
 (1167,'es'):'The current word order places slskr awkwardly after pares. The proposal makes the product relationship clearer while retaining the discovered-peer meaning.',
 (1167,'hi'):'की खोज की describes an active search rather than peers already discovered. The proposal expresses the completed state and preserves slskr.',
 (1167,'id'):'Menemukan Rekan reads as someone finding colleagues. The proposal labels the discovered slskr peers and preserves the exact product literal.',
 (1167,'ko'):'동료 means a human colleague, not a network peer. 피어 keeps the technical meaning and the proposal uses a discovered-state modifier.',
 (1167,'pt-BR'):'The current Pares slskr order is awkward. The proposal makes the product relationship clearer and preserves lowercase slskr.',
 (1167,'vi'):'Đồng nghiệp means work colleagues, not network peers. Peer keeps the technical meaning, with the discovered state stated explicitly.',
 (1167,'zh-Hans'):'同行 means a colleague or someone in the same profession, not a network peer. 对等节点 preserves the network meaning and exact slskr literal.',
 (1167,'zh-Hant'):'同行 means a colleague or someone in the same profession, not a network peer. 對等節點 preserves the network meaning and exact slskr literal.',
 (1170,'ar'):'رسم can mean a drawing; مخطط is a clearer rendering of graph in this atlas title.',
 (1170,'de'):'The base feature name is translated as Entdeckungsgraph elsewhere in this locale. The proposal keeps the Atlas title consistent with that term.',
 (1170,'hi'):'The neighboring Discovery Graph labels use डिस्कवरी ग्राफ़. The proposal reuses that established local wording in the Atlas title.',
 (1170,'id'):'The base feature label is Graf penemuan. The proposal reuses that translation and avoids the awkward English word order.',
 (1170,'pt-BR'):'The base feature label is grafo de descoberta. Reusing it makes the Atlas title consistent and fully localized.',
 (1170,'vi'):'The base feature label is translated locally. The proposal uses đồ thị khám phá consistently instead of mixing in the English feature name.',
 (1170,'zh-Hant'):'The base feature label uses 探索圖. The proposal reuses that local term rather than leaving the feature name in English.',
 (1172,'fr'):'The current phrase is unnatural and graphique means chart. The proposal uses graphe and states that the graph preview was shown for the title.',
 (1172,'ko'):'검색 그래프 means search graph, not Discovery Graph. 탐색 그래프 matches the localized feature label used elsewhere.',
 (1172,'pt-BR'):'Visualizado means viewed or visualized, not previewed. The proposal uses prévia and the established grafo de descoberta term.',
 (1175,'fr'):'Tarif means price or tariff, not rate. Taux matches the pinned statistic label.',
 (1176,'fr'):'This is an orthographic refinement: the French word étagère requires the acute accent on É, matching the other shelf message.',
 (1179,'hi'):'The current noun pairing is unnatural. The proposal expresses caution during discovery in the player-rating summary.',
 (1179,'pt-BR'):'Cuidado de descoberta is an awkward noun phrase. Cautela na descoberta reads more naturally as a rating dimension.',
 (1179,'zh-Hans'):'The current 警告 means warning. The source is a player-rating dimension, but the packet does not say whether caution means a warning, risk, or preference; hold for terminology review.',
 (1179,'zh-Hant'):'The current 警告 means warning. The source is a player-rating dimension, but the packet does not say whether caution means a warning, risk, or preference; hold for terminology review.',
 (1180,'ar'):'The message receives refreshed and expired item counts. Arabic count agreement depends on the runtime values and counted noun; hold for native review rather than guess.',
 (1180,'es'):'The current singular adjectives follow variable counts. Adding entradas clarifies the counted items and uses plural agreement.',
 (1180,'fr'):'The current singular participles follow variable counts. Adding entrées clarifies the counted items and uses plural agreement.',
 (1180,'hi'):'The current wording uses singular verbs after variable counts and omits the counted items. The proposal adds प्रविष्टियाँ and matches plural agreement.',
 (1180,'ja'):'The current counts have no counter unit. 件 makes the number of refreshed and expired entries clear in Japanese.',
 (1180,'ko'):'The current wording translates Discovery as search and lists counts without units or verbs. The proposal uses 탐색 and states the refreshed/expired item counts.',
 (1180,'pt-BR'):'The current singular adjectives follow variable counts. Adding entradas clarifies the counted items and uses plural agreement.',
 (1180,'zh-Hans'):'The classifier 项 connects each number to the counted entries and makes both status phrases read naturally.',
 (1180,'zh-Hant'):'The classifier 項 connects each number to the counted entries and makes both status phrases read naturally.',
 (1182,'ja'):'The current text mixes English Discovery with Japanese シェルフ. The proposal reuses ディスカバリーシェルフ and clearly says it was cleared from this browser.',
 (1182,'ko'):'The current phrase means search library, not Discovery Shelf. The proposal names the exploration shelf and uses a clear action verb.',
 (1182,'pt-BR'):'The current text mixes English Discovery with Portuguese. The proposal gives a complete Portuguese sentence for the local shelf-clear action.'
}

rows=[json.loads(line) for line in (INPUT/'current-target-cells.jsonl').read_text(encoding='utf-8').splitlines()]
contexts={json.loads(line)['sourceId']:json.loads(line) for line in (INPUT/'source-contexts.jsonl').read_text(encoding='utf-8').splitlines()}
assert len(rows)==240 and len(contexts)==20
ph_re=re.compile(r'\{[A-Za-z_][A-Za-z0-9_]*\}')
markup_re=re.compile(r'</?[A-Za-z][^>]*>')

def sha(s): return hashlib.sha256(s.encode('utf-8')).hexdigest()
def protected(source):
    return [t for t in ('DHT','slskr') if t in source]
def locale_confidence(locale):
    return 'low' if locale in {'ar','hi','ja','ko','vi','zh-Hans','zh-Hant'} else 'moderate'

ledger=[]
counts=Counter()
for cell in rows:
    pos=cell['position']; loc=cell['locale']; source=cell['source']; current=cell['currentTarget']
    status, proposed, rationale, confidence = CHANGES.get((pos,loc), ('accept-current',None,DEFAULT_RATIONALES[pos],locale_confidence(loc)))
    rationale = RATIONALE_OVERRIDES.get((pos,loc), rationale)
    input_placeholders=sorted(ph_re.findall(source))
    current_placeholders=sorted(ph_re.findall(current))
    target=proposed if proposed is not None else (current if status=='accept-current' else None)
    target_placeholders=sorted(ph_re.findall(target)) if target is not None else None
    protected_literals=protected(source)
    current_protected=[t for t in protected_literals if t in current]
    proposed_protected=[t for t in protected_literals if target is not None and t in target]
    rowctx=contexts[cell['sourceId']]
    assert sha(source)==cell['sourceSha256'] and sha(current)==cell['currentTargetSha256']
    assert input_placeholders==current_placeholders
    if target is not None:
        assert input_placeholders==target_placeholders, (pos,loc,input_placeholders,target_placeholders)
        assert all(t in target for t in protected_literals), (pos,loc,protected_literals,target)
        assert sorted(markup_re.findall(source))==sorted(markup_re.findall(target))
    out={
      'schemaVersion':1,'repository':manifest['repository'],'pullRequest':manifest['pullRequest'],'window':manifest['window'],'head':manifest['head'],'tree':manifest['tree'],
      'position':pos,'sourceId':cell['sourceId'],'source':source,'sourceSha256':cell['sourceSha256'],'locale':loc,
      'currentTarget':current,'currentTargetSha256':cell['currentTargetSha256'],
      'decision':status,'proposedTarget':proposed,'proposedTargetSha256':sha(proposed) if proposed is not None else None,
      'rationale':rationale,'confidence':confidence,'nativeSpeakerApproval':False,
      'sourcePlaceholders':input_placeholders,'currentPlaceholders':current_placeholders,'proposedPlaceholders':target_placeholders,
      'placeholderParity':input_placeholders==current_placeholders and (target_placeholders is None or input_placeholders==target_placeholders),
      'sourceMarkupTags':markup_re.findall(source),'currentMarkupTags':markup_re.findall(current),'proposedMarkupTags':markup_re.findall(target) if target is not None else None,
      'protectedLiteralPolicy':'Exact preservation of source occurrences of DHT and lowercase slskr; no separate term glossary was included in the candidate-free packet.',
      'sourceProtectedLiterals':protected_literals,'currentProtectedLiteralsPreserved':all(t in current for t in protected_literals),'proposedProtectedLiteralsPreserved':all(t in target for t in protected_literals) if target is not None else None,
      'callerReferenceCount':rowctx['callerReferenceCount'],'directLocalizedCaller':rowctx['directLocalizedCaller'],
      'callerEvidence':[{'path':c['path'],'line':c['line'],'matchKind':c['matchKind'],'localizedCallPattern':c['localizedCallPattern'],'contextSha256':c['contextSha256'],'lineText':c['lineText']} for c in rowctx['references']],
      'inputCurrentCellsSha256':input_sha['current-target-cells.jsonl'],'inputSourceContextsSha256':input_sha['source-contexts.jsonl'],'inputManifestSha256':input_sha['manifest.json']
    }
    ledger.append(out); counts[status]+=1
assert len(ledger)==240
assert counts['accept-current']+counts['correction-proposal']+counts['refinement-proposal']+counts['hold']==240
assert len({(x['position'],x['locale']) for x in ledger})==240

ledger_path=OUT/'blind-decisions.jsonl'
ledger_path.write_text(''.join(json.dumps(x,ensure_ascii=False,sort_keys=True)+'\n' for x in ledger),encoding='utf-8')
summary={'repository':manifest['repository'],'pullRequest':manifest['pullRequest'],'window':manifest['window'],'head':manifest['head'],'tree':manifest['tree'],'cellCount':len(ledger),'decisionCounts':dict(sorted(counts.items())),'holds':[{'position':x['position'],'sourceId':x['sourceId'],'locale':x['locale'],'rationale':x['rationale']} for x in ledger if x['decision']=='hold'],'sourceInputSha256':input_sha['current-target-cells.jsonl'],'sourceContextInputSha256':input_sha['source-contexts.jsonl'],'manifestInputSha256':input_sha['manifest.json'],'nativeSpeakerApproval':False}
(OUT/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2,sort_keys=True)+'\n',encoding='utf-8')
readme=f'''# Independent blind semantic review — slskR PR #204 W1163–W1182\n\nReviewed from the checksum-verified candidate-free input packet at `{INPUT}`. The live head/tree pins recorded in that packet are `{manifest['head']}` / `{manifest['tree']}`. This ledger covers {len(ledger)} cells: {', '.join(f'{k}={v}' for k,v in sorted(counts.items()))}.\n\n## Holds\n\n- Position 1165, `Discovered`, Arabic: the current imperative conflicts with the source state label. A safe Arabic form depends on the omitted noun and number agreement; hold for native review.\n- Position 1179, `Discovery caution`, `zh-Hans` and `zh-Hant`: the current 警告 means warning, while the rating dimension could mean caution/preference; the packet includes no glossary to settle the distinction.\n- Position 1180, discovery refresh counts, Arabic: number agreement depends on the runtime count and counted noun. Hold pending a native Arabic wording review.\n\n## Mechanical checks and limits\n\nAll 240 current cells preserve the source placeholder multiset. Every proposed value preserves the same placeholders and source markup; this window has no markup tags. When present, exact `DHT` and lowercase `slskr` literals are preserved. The candidate-free packet had no separate protected-term glossary; `DHT` and `slskr` were treated as fixed from their protocol/product use in the pinned source contexts. `Discovery Graph` and `Discovery Shelf` are treated as localizable UI feature labels.\n\nConfidence is lower for Arabic, Hindi, Japanese, Korean, Vietnamese, and Chinese idiom/register. This machine-assisted review is not native-speaker approval. No repository/PR changes or tests/builds/CI were made.\n\n## Input packet hashes\n\n- `current-target-cells.jsonl`: `{input_sha['current-target-cells.jsonl']}`\n- `source-contexts.jsonl`: `{input_sha['source-contexts.jsonl']}`\n- `manifest.json`: `{input_sha['manifest.json']}`\n- `catalog-file-pins.json`: `{input_sha['catalog-file-pins.json']}`\n\nThe complete review ledger is `blind-decisions.jsonl`; `summary.json` records counts and exact holds.\n'''
(OUT/'README.md').write_text(readme,encoding='utf-8')
# checksums include all deliverables and the reproducible builder itself.
files=[OUT/'blind-decisions.jsonl',OUT/'summary.json',OUT/'README.md',Path(__file__)]
(OUT/'SHA256SUMS.txt').write_text(''.join(f'{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.name if p.parent==OUT else "../"+p.name}\n' for p in files),encoding='utf-8')
print(json.dumps({'decisionCounts':dict(sorted(counts.items())),'holds':summary['holds'],'ledgerSha256':sha(ledger_path.read_text(encoding='utf-8')),'ledgerBytes':ledger_path.stat().st_size,'inputHashes':{k:input_sha[k] for k in ['current-target-cells.jsonl','source-contexts.jsonl','manifest.json','catalog-file-pins.json']}},ensure_ascii=False,indent=2))
