# Primary versus independent cross-review

Blind ledger SHA-256: `9c4b196efb93ac708f2bc2d346dce5fa504ca073844cec95ea4df6807c83d362` (sealed before primary per-cell ledger access).
Primary ledger SHA-256: `28b2a31cd39a3216836b7a2fe7ac3781daefd3e89d60613596aa34a20ef96088`.

The exact source/current values and hashes match in all 240 cells. The comparison found the following overall counts:

- Dispositions agree: 216; differ: 24.
- Proposed-target cells agree exactly: 209; differ: 31.
- Cells with any disposition or target difference: 34.
- Primary reviewed-final rows: 216; primary proposal rows: 51.
- Source/current mismatches: 0.
- Primary finals failing the independent structural rule: 4.

## Cell-level differences

`proposal-comparison.jsonl` contains all 240 paired rows. The rows below differ in disposition and/or target:

- **985 / ar — Could not update Wishlist filters.**: blind `refinement` target='تعذر تحديث عوامل تصفية قائمة الرغبات.'; primary `accept-current` target=None. Differences: disposition, proposal-presence.
- **985 / hi — Could not update Wishlist filters.**: blind `refinement` target='इच्छा सूची के फ़िल्टर अपडेट नहीं हो सके।'; primary `accept-current` target=None. Differences: disposition, proposal-presence.
- **985 / id — Could not update Wishlist filters.**: blind `refinement` target='Tidak dapat memperbarui filter Daftar keinginan.'; primary `accept-current` target=None. Differences: disposition, proposal-presence.
- **985 / vi — Could not update Wishlist filters.**: blind `refinement` target='Không thể cập nhật bộ lọc Danh sách yêu thích.'; primary `accept-current` target=None. Differences: disposition, proposal-presence.
- **985 / zh-Hans — Could not update Wishlist filters.**: blind `refinement` target='无法更新愿望单筛选条件。'; primary `accept-current` target=None. Differences: disposition, proposal-presence.
- **986 / ko — Count**: blind `correction` target='개수'; primary `correction` target='건수'. Differences: proposal-text.
- **987 / fr — Counters for signatures, reputation, rate limits, and quarantine**: blind `correction` target='Compteurs de signatures, de réputation, de limites de fréquence et de quarantaine'; primary `accept-current` target=None. Differences: disposition, proposal-presence.
- **987 / id — Counters for signatures, reputation, rate limits, and quarantine**: blind `correction` target='Penghitung tanda tangan, reputasi, pembatasan frekuensi, dan karantina'; primary `correction` target='Penghitung tanda tangan, reputasi, batas frekuensi, dan karantina'. Differences: proposal-text.
- **988 / de — Cover Traffic**: blind `correction` target='Cover-Traffic'; primary `correction` target='Tarnverkehr'. Differences: proposal-text.
- **988 / hi — Cover Traffic**: blind `correction` target='कवर ट्रैफ़िक'; primary `correction` target='छद्म ट्रैफ़िक'. Differences: proposal-text.
- **989 / fr — Cover art**: blind `refinement` target='Pochette'; primary `correction` target='Pochette'. Differences: disposition.
- **989 / zh-Hans — Cover art**: blind `accept-current` target=None; primary `correction` target='封面图'. Differences: disposition, proposal-presence.
- **989 / zh-Hant — Cover art**: blind `accept-current` target=None; primary `correction` target='封面圖'. Differences: disposition, proposal-presence.
- **990 / zh-Hans — Cover art policy for {name}**: blind `accept-current` target=None; primary `refinement` target='{name} 的封面图策略'. Differences: disposition, proposal-presence.
- **990 / zh-Hant — Cover art policy for {name}**: blind `accept-current` target=None; primary `refinement` target='{name} 的封面圖策略'. Differences: disposition, proposal-presence.
- **991 / vi — Coverage of shared FLACs**: blind `correction` target='Mức độ bao phủ các tệp FLAC dùng chung'; primary `correction` target='Mức độ bao phủ các tệp FLAC được chia sẻ'. Differences: proposal-text.
- **992 / vi — Create**: blind `refinement` target='Tạo'; primary `correction` target='Tạo'. Differences: disposition.
- **994 / hi — Create Content-Linked Pod**: blind `correction` target='कंटेंट-लिंक्ड Pod बनाएं'; primary `accept-current` target=None. Differences: disposition, proposal-presence.
- **994 / ja — Create Content-Linked Pod**: blind `correction` target='コンテンツにリンクされた Pod の作成'; primary `accept-current` target=None. Differences: disposition, proposal-presence.
- **994 / ko — Create Content-Linked Pod**: blind `correction` target='콘텐츠 연결 Pod 생성'; primary `accept-current` target=None. Differences: disposition, proposal-presence.
- **994 / pt-BR — Create Content-Linked Pod**: blind `refinement` target='Criar Pod vinculado ao conteúdo'; primary `accept-current` target=None. Differences: disposition, proposal-presence.
- **994 / zh-Hans — Create Content-Linked Pod**: blind `accept-current` target=None; primary `refinement` target='创建与内容关联的 Pod'. Differences: disposition, proposal-presence.
- **994 / zh-Hant — Create Content-Linked Pod**: blind `accept-current` target=None; primary `refinement` target='建立與內容連結的 Pod'. Differences: disposition, proposal-presence.
- **995 / hi — Create Group**: blind `accept-current` target=None; primary `refinement` target='समूह बनाएँ'. Differences: disposition, proposal-presence.
- **998 / es — Create New Room**: blind `correction` target='Crear una nueva sala'; primary `correction` target='Crear nueva sala'. Differences: proposal-text.
- **998 / hi — Create New Room**: blind `refinement` target='नया रूम बनाएँ'; primary `refinement` target='नया कमरा बनाएँ'. Differences: proposal-text.
- **998 / zh-Hant — Create New Room**: blind `correction` target='建立新的聊天室'; primary `accept-current` target=None. Differences: disposition, proposal-presence.
- **1000 / de — Create Room**: blind `correction` target='Raum erstellen'; primary `refinement` target='Raum erstellen'. Differences: disposition.
- **1000 / es — Create Room**: blind `correction` target='Crear una sala'; primary `correction` target='Crear sala'. Differences: proposal-text.
- **1000 / hi — Create Room**: blind `correction` target='रूम बनाएँ'; primary `correction` target='कमरा बनाएँ'. Differences: proposal-text.
- **1000 / zh-Hant — Create Room**: blind `correction` target='建立聊天室'; primary `accept-current` target=None. Differences: disposition, proposal-presence.
- **1001 / es — Create Share Group**: blind `accept-current` target=None; primary `correction` target='Crear grupo para compartir'. Differences: disposition, proposal-presence.
- **1001 / hi — Create Share Group**: blind `refinement` target='शेयर समूह बनाएँ'; primary `refinement` target='साझा समूह बनाएँ'. Differences: proposal-text.
- **1001 / zh-Hant — Create Share Group**: blind `refinement` target='建立分享群組'; primary `accept-current` target=None. Differences: disposition, proposal-presence.

## Primary structural findings

The independent structural comparison found the following primary reviewed-final targets did not preserve the exact `Pod` literal used by the exact-head standalone `Pod` catalog key. This is an independent policy inference and should be adjudicated if the product permits locale-specific transliteration.

- **994 / hi**: 'कंटेंट-लिंक्ड पॉड बनाएं' (failed: protectedLiterals).
- **994 / ja**: 'コンテンツにリンクされたポッドの作成' (failed: protectedLiterals).
- **994 / ko**: '콘텐츠 연결 포드 생성' (failed: protectedLiterals).
- **994 / pt-BR**: 'Criar pod vinculado a conteúdo' (failed: protectedLiterals).

The blind proposals pass their final placeholder, markup, ICU, protected-literal, and terminal-punctuation checks. Machine review only; no native-speaker approval is claimed.
