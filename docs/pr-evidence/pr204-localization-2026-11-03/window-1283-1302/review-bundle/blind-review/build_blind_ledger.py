#!/usr/bin/env python3
"""Build the independent blind ledger using only the pinned candidate-free packet."""
import hashlib, json, re
from pathlib import Path

INPUT = Path('/mnt/disks/scratch/task-scratch/slskr-pr204-w1283-1302-blind-20261103/input')
OUT = Path(__file__).resolve().parent

def sha(s): return hashlib.sha256(s.encode('utf-8')).hexdigest()
def load_jsonl(name): return [json.loads(x) for x in (INPUT / name).read_text(encoding='utf-8').splitlines()]

# Independent target proposals, keyed by selected queue position then locale.
P = {
1283: {
'es':'Habilitar las subidas por FTP después de completar las descargas',
'zh-Hans':'启用下载完成后的 FTP 上传',
'hi':'डाउनलोड पूरे होने के बाद FTP अपलोड सक्षम करें',
'ja':'ダウンロード完了後の FTP アップロードを有効にする',
'fr':'Activer les téléversements FTP après la fin des téléchargements',
'pt-BR':'Habilitar uploads via FTP após a conclusão dos downloads',
'ar':'تمكين الرفع عبر FTP بعد اكتمال التنزيلات',
'ko':'다운로드 완료 후 FTP 업로드 활성화',
'zh-Hant':'啟用下載完成後的 FTP 上傳',
'vi':'Bật tải lên qua FTP sau khi tải xuống hoàn tất',
'id':'Aktifkan unggahan melalui FTP setelah unduhan selesai',
},
1284: {
'hi':'FTP अपलोड सक्षम करें',
'fr':'Activer les téléversements FTP',
},
1285: {
'es':'Habilitar la limitación de frecuencia de las solicitudes HTTP',
'zh-Hans':'启用 HTTP 请求速率限制',
'hi':'HTTP अनुरोध दर सीमित करना सक्षम करें',
'de':'Begrenzung der HTTP-Anfragerate aktivieren',
'ja':'HTTP リクエストのレート制限を有効にする',
'fr':'Activer la limitation du débit des requêtes HTTP',
'pt-BR':'Habilitar a limitação da taxa de requisições HTTP',
'ar':'تمكين تحديد معدل طلبات HTTP',
'ko':'HTTP 요청 속도 제한 활성화',
'zh-Hant':'啟用 HTTP 請求速率限制',
'vi':'Bật giới hạn tần suất yêu cầu HTTP',
'id':'Aktifkan pembatasan laju permintaan HTTP',
},
1286: {
'es':'Habilite la limitación de frecuencia de las solicitudes HTTP para las políticas de API, federación y puerta de enlace de malla.',
'zh-Hans':'为 API、联邦和网状网关策略启用 HTTP 请求速率限制。',
'hi':'API, फ़ेडरेशन और मेश गेटवे नीतियों के लिए HTTP अनुरोध दर सीमित करना सक्षम करें।',
'de':'Aktivieren Sie die Begrenzung der HTTP-Anfragerate für API-, Föderations- und Mesh-Gateway-Richtlinien.',
'ja':'API、フェデレーション、およびメッシュゲートウェイのポリシーで、HTTP リクエストのレート制限を有効にします。',
'fr':'Activez la limitation du débit des requêtes HTTP pour les règles d’API, de fédération et de passerelle mesh.',
'pt-BR':'Ative a limitação da taxa de requisições HTTP para as políticas de API, federação e gateway de malha.',
'ar':'تمكين تحديد معدل طلبات HTTP لسياسات API والاتحاد وبوابة الشبكة المتداخلة.',
'ko':'API, 페더레이션 및 메시 게이트웨이 정책에서 HTTP 요청 속도 제한을 활성화합니다.',
'zh-Hant':'為 API、聯邦和網狀閘道政策啟用 HTTP 請求速率限制。',
'vi':'Bật giới hạn tần suất yêu cầu HTTP cho các chính sách API, liên kết và cổng lưới.',
'id':'Aktifkan pembatasan laju permintaan HTTP untuk kebijakan API, federasi, dan gateway mesh.',
},
1288: {
'es':'Habilitar las importaciones de feeds de Last.fm',
'zh-Hans':'启用 Last.fm 信息流导入',
'hi':'Last.fm फ़ीड से आयात सक्षम करें',
'de':'Importe aus Last.fm-Feeds aktivieren',
'fr':'Activer l’importation des flux Last.fm',
'pt-BR':'Habilitar importações dos feeds do Last.fm',
'ar':'تمكين الاستيراد من موجزات Last.fm',
'zh-Hant':'啟用 Last.fm 資訊流匯入',
'vi':'Bật nhập từ các nguồn cấp dữ liệu Last.fm',
'id':'Aktifkan impor dari feed Last.fm',
},
1290: {
'es':'Habilitar la descarga automática de Lidarr',
'zh-Hans':'启用 Lidarr 自动下载',
'de':'Automatischen Download in Lidarr aktivieren',
'fr':'Activer le téléchargement automatique de Lidarr',
'pt-BR':'Habilitar o download automático do Lidarr',
'ar':'تمكين التنزيل التلقائي في Lidarr',
},
1291: {
'es':'Habilitar la lista de bloqueo para las descargas rechazadas por Lidarr',
'zh-Hans':'启用 Lidarr 将被拒绝的下载加入黑名单的设置',
'hi':'Lidarr द्वारा अस्वीकृत डाउनलोड को ब्लैकलिस्ट करने की सेटिंग सक्षम करें',
'de':'Lidarr-Einstellung zum Sperren abgelehnter Downloads aktivieren',
'ja':'Lidarr で拒否されたダウンロードをブラックリストに登録する設定を有効にする',
'fr':'Activer la mise sur liste de blocage des téléchargements rejetés par Lidarr',
'pt-BR':'Habilitar a lista de bloqueio para downloads rejeitados pelo Lidarr',
'ar':'تمكين إعداد حظر التنزيلات التي يرفضها Lidarr',
'ko':'Lidarr에서 거부된 다운로드를 차단 목록에 추가하는 설정 활성화',
'zh-Hant':'啟用 Lidarr 將遭拒下載加入封鎖清單的設定',
'vi':'Bật cài đặt đưa các lượt tải xuống bị Lidarr từ chối vào danh sách chặn',
'id':'Aktifkan pengaturan untuk memasukkan unduhan yang ditolak Lidarr ke daftar blokir',
},
1292: {
'es':'Habilitar la importación de descargas completadas en Lidarr',
'zh-Hans':'启用将已完成的下载导入 Lidarr',
'hi':'Lidarr में पूरी हो चुकी डाउनलोड फ़ाइलों का आयात सक्षम करें',
'de':'Import abgeschlossener Downloads in Lidarr aktivieren',
'ja':'完了したダウンロードを Lidarr にインポートする設定を有効にする',
'fr':'Activer l’importation des téléchargements terminés dans Lidarr',
'pt-BR':'Habilitar a importação de downloads concluídos no Lidarr',
'ar':'تمكين استيراد التنزيلات المكتملة إلى Lidarr',
'ko':'완료된 다운로드를 Lidarr로 가져오기 활성화',
'zh-Hant':'啟用將已完成的下載匯入 Lidarr',
'vi':'Bật tính năng nhập các bản tải xuống đã hoàn tất vào Lidarr',
'id':'Aktifkan impor unduhan yang telah selesai ke Lidarr',
},
1293: {
'es':'Habilitar la eliminación de archivos de descargas completadas que Lidarr rechace durante la importación automática',
'zh-Hans':'启用自动导入时删除 Lidarr 拒绝的已完成文件',
'hi':'स्वचालित आयात के दौरान Lidarr द्वारा अस्वीकार की गई पूरी हो चुकी फ़ाइलों को हटाने की सेटिंग सक्षम करें',
'de':'Löschen der Dateien aus abgeschlossenen Downloads aktivieren, die Lidarr beim automatischen Import ablehnt',
'ja':'自動インポート時に Lidarr が拒否した完了済みファイルを削除する設定を有効にする',
'fr':'Activer la suppression des fichiers issus de téléchargements terminés que Lidarr rejette lors de l’importation automatique',
'pt-BR':'Habilitar a exclusão de arquivos de downloads concluídos rejeitados pelo Lidarr durante a importação automática',
'ar':'تمكين حذف الملفات المكتملة التي يرفضها Lidarr أثناء الاستيراد التلقائي',
'ko':'자동 가져오기 중 Lidarr가 거부한 완료된 파일 삭제 활성화',
'zh-Hant':'啟用在自動匯入時刪除 Lidarr 拒絕的已完成檔案',
'vi':'Bật tính năng xóa các tệp đã tải xong mà Lidarr từ chối trong quá trình nhập tự động',
'id':'Aktifkan penghapusan file unduhan yang telah selesai dan ditolak Lidarr saat impor otomatis',
},
1294: {
'es':'Habilitar la configuración de integración de Lidarr',
'de':'Lidarr-Integrationseinstellungen aktivieren',
'fr':'Activer les paramètres d’intégration de Lidarr',
},
1295: {
'es':'Permitir que Lidarr reemplace los archivos existentes',
'zh-Hans':'启用 Lidarr 在导入时替换现有文件',
'hi':'Lidarr को मौजूदा फ़ाइलें बदलने की अनुमति देने वाली सेटिंग सक्षम करें',
'de':'Lidarr das Ersetzen vorhandener Dateien erlauben',
'pt-BR':'Permitir que o Lidarr substitua arquivos existentes',
'vi':'Bật cài đặt cho phép Lidarr thay thế các tệp hiện có',
'id':'Aktifkan pengaturan agar Lidarr dapat mengganti file yang sudah ada',
},
1296: {
'es':'Habilitar la sincronización de los álbumes deseados de Lidarr',
'zh-Hans':'启用 Lidarr 待收集专辑的同步',
'hi':'Lidarr के इच्छित एल्बमों का सिंक सक्षम करें',
'de':'Synchronisierung der von Lidarr gewünschten Alben aktivieren',
'ja':'Lidarr の未入手アルバムの同期を有効にする',
'fr':'Activer la synchronisation des albums recherchés par Lidarr',
'pt-BR':'Ativar a sincronização dos álbuns desejados do Lidarr',
'ar':'تمكين مزامنة الألبومات التي يطلبها Lidarr',
'ko':'Lidarr에서 원하는 앨범 동기화 활성화',
'zh-Hant':'啟用 Lidarr 待收集專輯同步',
'vi':'Bật đồng bộ các album Lidarr muốn có',
'id':'Aktifkan sinkronisasi album yang diinginkan di Lidarr',
},
1297: {
'es':'Habilite la sincronización de los álbumes deseados de Lidarr y la importación de descargas completadas. La sincronización en vivo seguirá ejecutándose únicamente mediante acciones explícitas de Lidarr o tareas programadas configuradas.',
'zh-Hans':'启用 Lidarr 待收集专辑同步和已完成下载导入设置。实时同步仍只会通过明确触发的 Lidarr 操作或已配置的计划任务运行。',
'hi':'Lidarr के इच्छित एल्बमों का सिंक और पूरी हो चुकी डाउनलोड फ़ाइलों के आयात की सेटिंग सक्षम करें। लाइव सिंक आगे भी केवल स्पष्ट रूप से शुरू की गई Lidarr कार्रवाइयों या कॉन्फ़िगर किए गए शेड्यूलर से ही चलेगा।',
'ja':'Lidarr の未入手アルバムの同期と、完了したダウンロードのインポート設定を有効にします。ライブ同期は引き続き、明示的な Lidarr 操作または設定済みのスケジューラーからのみ実行されます。',
'fr':'Activez les paramètres de synchronisation des albums recherchés par Lidarr et d’importation des téléchargements terminés. La synchronisation en direct ne s’exécutera toujours qu’à la suite d’actions explicites de Lidarr ou de tâches planifiées configurées.',
'pt-BR':'Ative a sincronização dos álbuns desejados do Lidarr e as configurações de importação de downloads concluídos. A sincronização ao vivo continuará sendo executada somente por ações explícitas do Lidarr ou agendadores configurados.',
'ar':'تمكين مزامنة الألبومات التي يطلبها Lidarr وإعدادات استيراد التنزيلات المكتملة. ستظل المزامنة المباشرة تعمل فقط عبر إجراءات Lidarr الصريحة أو برامج الجدولة المُعَدّة.',
'ko':'Lidarr에서 원하는 앨범 동기화 및 완료된 다운로드 가져오기 설정을 활성화합니다. 실시간 동기화는 계속해서 명시적인 Lidarr 작업이나 구성된 스케줄러를 통해서만 실행됩니다.',
'zh-Hant':'啟用 Lidarr 待收集專輯同步和已完成下載匯入設定。即時同步仍只會透過明確觸發的 Lidarr 操作或已設定的排程工作執行。',
'vi':'Bật cài đặt đồng bộ các album Lidarr muốn có và nhập các bản tải xuống đã hoàn tất. Đồng bộ trực tiếp vẫn chỉ chạy khi được kích hoạt rõ ràng bằng thao tác Lidarr hoặc bởi bộ lập lịch đã cấu hình.',
'id':'Aktifkan sinkronisasi album yang diinginkan di Lidarr dan pengaturan impor unduhan yang telah selesai. Sinkronisasi langsung tetap hanya berjalan jika dipicu secara eksplisit oleh tindakan Lidarr atau penjadwal yang dikonfigurasi.',
},
1298: {
'hi':'संदेशों का बैच प्रसंस्करण सक्षम करें',
'pt-BR':'Habilitar o processamento de mensagens em lote',
'zh-Hant':'啟用訊息批次處理',
'vi':'Bật xử lý tin nhắn theo lô',
},
1299: {
'ar':'تمكين إضافة حشو إلى الرسائل',
'id':'Aktifkan padding pesan',
},
1302: {
'hi':'नेटवर्क ट्रांसपोर्ट को छिपाने की सुविधा सक्षम करें',
'ar':'تمكين تمويه النقل',
'vi':'Bật tính năng ngụy trang phương thức truyền tải',
'id':'Aktifkan transport yang disamarkan',
},
}

ROW_REASONS = {
1283:'The caller tooltip says FTP uploads occur after downloads finish. The existing wording in this locale either reverses that relationship, is ambiguous, or transliterates the protected FTP literal.',
1284:'The visible checkbox is specifically for FTP uploads; this wording corrects the locale’s download/upload mismatch or protected-literal transliteration.',
1285:'In this admin-policy checkbox, HTTP rate limiting concerns request frequency. Naming HTTP requests avoids reading the control as limiting transfer bandwidth.',
1286:'The policy tooltip identifies API, federation, and mesh-gateway policies; this wording makes the request-rate control explicit while preserving API and HTTP literals.',
1288:'The caller tooltip describes Last.fm API imports from previewed user URLs. This removes the source/feed duplication or unnatural compound while keeping Last.fm exact.',
1290:'The caller label and tooltip describe automatic downloading of Lidarr-created Wishlist items under Wishlist rules; this removes the awkward “setting” construction while retaining the control meaning.',
1291:'The caller tooltip says rejected Wishlist peers and remote directories are excluded from future automatic downloads; this makes the blacklist action grammatical and intelligible.',
1292:'The caller label says auto-import completed downloads and the tooltip says completed slskR directories are sent to Lidarr import; this identifies completed downloads as the imported item.',
1293:'The tooltip limits deletion to completed files rejected by Lidarr during automatic import; this wording restores that actor, timing, and object.',
1294:'The checkbox enables the Lidarr integration settings; this corrects missing prepositions or unnatural brand placement.',
1295:'The tooltip says Lidarr may replace existing files during completed-download import; this corrects the malformed “enable Lidarr/setting” construction.',
1296:'The caller says to sync Lidarr wanted albums into Wishlist review items; this wording identifies the wanted albums as the objects being synchronized.',
1297:'The tooltip requires wanted-album sync and completed-download import settings, with live sync limited to explicit Lidarr actions or configured schedulers; this wording preserves that constraint and fixes unnatural terminology.',
1298:'This security setting enables batching messages; the wording describes batch processing rather than merely a batch or grouped sending.',
1299:'This security setting enables message padding; the Indonesian wording uses the technical term rather than a physical cushion, and the Arabic wording expresses adding padding to messages.',
1302:'This security setting enables transport obfuscation; the wording expresses concealing/obfuscating the transport rather than ambiguity or scrambling.',
}

RETAIN_REASONS = {
1283:'The current wording correctly expresses FTP uploads following completed downloads and keeps the protected FTP literal.',
1284:'The current label clearly enables FTP uploads and preserves the protected FTP literal.',
1285:'The current wording clearly names HTTP rate limiting and retains the HTTP literal; no meaning-changing flaw is evident.',
1286:'The current tooltip preserves HTTP/API policy scope and correctly names federation and mesh-gateway policies.',
1287:'The current label clearly enables Last.fm imports and preserves the protected Last.fm name.',
1288:'The current wording is a clear, conventional rendering of Last.fm feed imports and preserves the protected Last.fm name.',
1289:'The current short label clearly enables Lidarr and preserves the protected Lidarr name.',
1290:'The current wording communicates enabling Lidarr automatic downloads; the caller tooltip supplies the Wishlist-rule scope.',
1291:'The current wording communicates Lidarr blacklisting rejected downloads; caller context clarifies that the rejected peer and directory are excluded.',
1292:'The current wording communicates the Lidarr completed-import control; caller context clarifies the completed-download and manual-import scope.',
1293:'The current wording communicates deleting downloads rejected by Lidarr; caller context clarifies automatic-import timing and eligible files.',
1294:'The current wording clearly enables Lidarr integration settings and preserves the protected Lidarr name.',
1295:'The current wording clearly describes Lidarr replacing existing files and preserves the protected Lidarr name.',
1296:'The current wording communicates enabling Lidarr wanted-album synchronization; caller context identifies the Wishlist destination.',
1297:'The current wording preserves the two settings and the explicit-action/configured-scheduler limitation.',
1298:'The current wording clearly enables message batching.',
1299:'The current wording clearly enables message padding.',
1300:'The current label clearly enables Ntfy and preserves the protected product name.',
1301:'The current wording clearly enables Ntfy notifications and preserves the protected product name.',
1302:'The current wording clearly describes obfuscated transport in this security setting.',
}

STRINGS = load_jsonl('current-target-cells.jsonl')
CONTEXTS = {r['position']:r for r in load_jsonl('source-contexts.jsonl')}
manifest = json.loads((INPUT/'manifest.json').read_text(encoding='utf-8'))
locale_order = manifest['localeOrder']
rows=[]
for item in STRINGS:
    pos=item['position']; locale=item['locale']; source=item['sourceKey']
    ctx=CONTEXTS[pos]
    proposal=P.get(pos,{}).get(locale)
    disposition='propose' if proposal is not None and proposal != item['currentTarget'] else 'retain'
    final=proposal if disposition=='propose' else item['currentTarget']
    rationale=ROW_REASONS[pos] if disposition=='propose' else RETAIN_REASONS[pos]
    confidence='high' if pos in (1283,1284,1285,1286,1288,1291,1292,1293,1298,1299,1302) and disposition=='propose' else ('moderate' if disposition=='propose' else 'high')
    refs=[]
    for caller in ctx['callers']:
        refs.append({'path':caller['path'],'line':caller['line'],'lineSha256':caller['lineSha256'],'contextSha256':caller['contextSha256'],'gitBlob':caller['gitBlob'],'fileSha256':caller['fileSha256']})
    rows.append({
      'position':pos,'sourceKey':source,'sourceKeySha256':sha(source),'locale':locale,
      'currentTarget':item['currentTarget'],'currentTargetSha256':sha(item['currentTarget']),
      'disposition':disposition,'target':final,'targetSha256':sha(final),
      'confidence':confidence,'rationale':rationale,
      'callerContextSha256':ctx['callerContextSha256'],'callerReferences':refs,
      'sourcePlaceholders':item['sourcePlaceholders'],'targetPlaceholders':re.findall(r'\{([a-zA-Z][a-zA-Z0-9_]*)\}',final),
      'sourceMarkupTags':item['sourceMarkupTags'],'targetMarkupTags':re.findall(r'<\/?[A-Za-z][^>]*>',final),
      'sourceNumericTokens':item['sourceNumericTokens'],'targetNumericTokens':re.findall(r'(?<!\w)[+-]?\d+(?:[.,]\d+)?%?(?!\w)',final),
      'sourceProtectedLiterals':item['sourceProtectedLiterals'],
      'protectedLiteralsPreserved':all(tok in final for tok in item['sourceProtectedLiterals']),
      'nativeSpeakerApproval':False,
    })
rows.sort(key=lambda r:(r['position'], locale_order.index(r['locale'])))
(OUT/'blind-ledger.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False,sort_keys=True)+'\n' for r in rows),encoding='utf-8')
counts={d:sum(r['disposition']==d for r in rows) for d in ('propose','retain')}
summary={
 'artifact':'Independent blind translation review ledger',
 'repository':'snapetech-org/slskR','pullRequest':204,
 'pinnedHead':manifest['head'],'pinnedTree':manifest['tree'],
 'candidateFreeInputPath':str(INPUT),
 'candidateFreeChecksumListSha256':hashlib.sha256((INPUT/'SHA256SUMS.txt').read_bytes()).hexdigest(),
 'candidateFreeManifestSha256':hashlib.sha256((INPUT/'manifest.json').read_bytes()).hexdigest(),
 'selectedPositions':[1283,1302],'localeOrder':locale_order,
 'expectedCells':240,'reviewedCells':len(rows),
 'proposals':counts['propose'],'retains':counts['retain'],'holds':0,
 'callerResolutionHoldCount':manifest['callerResolutionHoldCount'],
 'allCallerReferencesCarried':all(bool(r['callerReferences']) for r in rows),
 'nativeSpeakerApproval':False,
 'notes':['The exact caller/context text and pins in the candidate-free packet were the only review evidence used.','Current target values were retained except where the blind review proposes a correction or clarity improvement.','No candidate translations, primary review, PR body, tests, builds, scans, or CI were consulted/run.','Proposals remain subject to native-speaker review.'],
}
(OUT/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2,sort_keys=True)+'\n',encoding='utf-8')
