# W1123-W1142 cross-audit: slskR PR #204

## Scope and pinned evidence

- 20 source IDs × 12 locale catalogs: **240 cells**.
- PR/API, branch API, and `git ls-remote` all resolve to head `dba3af4fcddf494bc0ca7da48d3f61d6f75f769c` and tree `7d83b6559bc28ee385f7da9b7c84eb46a91388f6` at 2026-11-03 06:05:54 UTC; the PR remains open and draft.
- Blind, clean-input, and primary-review checksum manifests all verify. Every clean-input file hash matches the manifest captured by the candidate-free blind review.
- All 240 source/current/catalog pins, 20 ordered source IDs, caller-context hash arrays, direct-caller flags, and caller counts match between clean input and both ledgers. The reported 64 caller references reconcile to the 20 source contexts.
- Callerless source: `Directory {directory} is locked` (12 locale cells). Its `{directory}` placeholder is retained under hold.

## Reconciliation outcomes

- 58 exact target recommendations; 20 holds; no catalog or PR changes made.
- Outcome counts: `{"HOLD_NO_DIRECT_CALLER": 12, "HOLD_TERM": 8, "KEEP_CURRENT": 162, "WIN_BLIND": 24, "WIN_CROSS_AUDIT": 3, "WIN_PRIMARY": 31}`.
- Blind/primary have 35 different effective target strings and 24 coarse keep/change/hold disagreements. The disagreement extract contains 55 rows, including cross-audit overrides and holds.

## Requested disputed recommendations

### Indonesian dimensions

- `Dimensions` → **Dimensi**; `Dimensions:` → **Dimensi:**. The pinned caller uses these for image width/height.

### “Directory is required” API-field notes

Remove the extra API-field note from all twelve current targets. The exact pinned source error is “Directory is required”; the caller path routes the backend error through the generic app-error catalog mapping, but it does not add an API-field note to the source string.

- **ar** — "المجلد مطلوب." (`244ca8c2887d2be52a5c9dd6e5d068718c36dbbd6c9ac91147d9d1b1ad344697`)
- **de** — "Das Verzeichnis ist erforderlich." (`9abcfe4af6b7f093b68619d34925407b563783ed23ae9646acc9b43d2fbdc86f`)
- **es** — "Se requiere el directorio." (`bd494a440116b3a42d1af57b02f94a2210d3c0e0fc0ec5c7f064b9d2c8732067`)
- **fr** — "Le répertoire est obligatoire." (`1379c96ad67747468ec0690a5403c1400642d20fd6406b74891427d7b0057aa0`)
- **hi** — "फ़ोल्डर आवश्यक है।" (`a9d9b1f647eeb4210e9bc10621454d05fc2d603819ff0f4850d57809e3e3335e`)
- **id** — "Direktori wajib diisi." (`045f9ae35c9398be10c19cf9d532efe9c6d555cc3c8d0369da6947d0fd0142e4`)
- **ja** — "ディレクトリが必要です。" (`4e06f5924f1703ad55d4085c2e87600fc018b9328452f07567028707f172fc91`)
- **ko** — "디렉터리가 필요합니다." (`124be21ccce3f20a13e0e872fa6603f568ee8faac26d2cb9a6098716431e6213`)
- **pt-BR** — "O diretório é obrigatório." (`b0fbcd7e2b41f9742eb2b90ae254428dd6e798b612e14eaa028ac9b60cc4f6df`)
- **vi** — "Cần có thư mục." (`a1d95684e0cc04dbb0bf74f2fe54091cd326208c0804607e7dfcf7d85de1b070`)
- **zh-Hans** — "必须提供目录。" (`ff6dd3881a73c54459aea8cc7d29ee59834bdfb4ce605ff9cbcdc6f7128d45ab`)
- **zh-Hant** — "必須提供目錄。" (`800d62a5c2af1eb406d32575323fff949d628d8b9923403b399efdd27e7d0adf`)

### Korean directory spelling and French report label

- Korean `Directory` → **디렉터리** and `Directory report` → **디렉터리 보고서**; `Directory is required` → **디렉터리가 필요합니다.**. The spelling is consistent for the pinned filesystem use, and the error target drops the unsupported suffix.
- French `Directory report` → **Rapport sur les répertoires**, for the Compatibility Dashboard report about shared filesystem directories.

### HTTPS listener and host warning

- Hindi standalone `Disable HTTPS listener` remains held. The current श्रोता means a human listener/audience; the blind लिसनर loan still needs qualified review. The Hindi safety warning sentence remains held for the same unresolved listener term, though its current sentence has the off polarity.
- Indonesian `Disable HTTPS listener` → **Nonaktifkan listener HTTPS**; warning uses **Nonaktifkan listener HTTPS. Biarkan tetap nonaktif saat mengekspos UI Web di luar localhost.**
- Vietnamese `Disable HTTPS listener` → **Tắt dịch vụ lắng nghe HTTPS**; warning uses **Tắt dịch vụ lắng nghe HTTPS. Hãy để tùy chọn này luôn tắt khi cung cấp giao diện Web bên ngoài localhost.**
- Six non-Arabic warning decisions:

- **es** — "Desactive el servicio de escucha HTTPS. Manténgalo desactivado cuando exponga la interfaz web más allá de localhost."; WIN_BLIND
- **fr** — "Désactivez le service d’écoute HTTPS. Gardez cette option désactivée lorsque vous exposez l’interface Web au-delà de localhost."; WIN_BLIND
- **hi** — HOLD: "HTTPS श्रोता को अक्षम करें। लोकलहोस्ट से परे वेब यूआई को उजागर करते समय इसे बंद रखें।"; HOLD_TERM
- **id** — "Nonaktifkan listener HTTPS. Biarkan tetap nonaktif saat mengekspos UI Web di luar localhost."; WIN_PRIMARY
- **pt-BR** — "Desative o serviço de escuta HTTPS. Mantenha-o desativado ao expor a interface Web além de localhost."; WIN_BLIND
- **vi** — "Tắt dịch vụ lắng nghe HTTPS. Hãy để tùy chọn này luôn tắt khi cung cấp giao diện Web bên ngoài localhost."; WIN_BLIND

- Arabic warning → **عطّل مستمع HTTPS. أبقه معطّلًا عند إتاحة واجهة الويب خارج localhost.** Keep the RTL ordering note for the Latin literals.
- Chinese warnings preserve their correct off instruction and include `localhost` as an exact host token in the cross-audit targets. German, Japanese, and Korean current warnings are retained; they preserve the exact host name.

### Loopback, crossfade, and authority

- French `loopback` → **Désactivez l’authentification de l’interface Web uniquement pour les déploiements loopback strictement contrôlés.**; current `bouclage` is generic loop wording.
- Vietnamese `Disable crossfade` → **Tắt hiệu ứng crossfade**. The caller documents a five-second fade between queue items and toggles `crossfadeEnabled`; native-speaker confirmation remains pending.
- Keep `Disable authority {authorityKey}` held in **de, ja, ko, vi, zh-Hans, zh-Hant**. The pinned caller confirms the dynamic authority key but does not settle the product term. All six `{authorityKey}` placeholders remain intact.

## Structural and technical-token checks

- Placeholder parity: 0 mismatches. Markup parity: 0 mismatches. Numeric source values: 0; losses: 0.
- Blind and primary proposed targets also independently pass placeholder, markup, numeric, and exact HTTPS checks.
- `HTTPS` is preserved exactly in all selected targets where it appears.
- The `loopback` concept is retained as the raw term or a locale-specific network term (Loopback, लूपबैक, ループバック, 루프백, 环回/環回). French now uses the raw network term instead of bouclage.
- The literal `localhost` is retained in recommended target strings in 11 locales; Hindi warning remains held and its current target transliterates the host name. Arabic RTL notes and all input RTL-sensitive notes are carried into the ledger.
- This is an independent machine-assisted cross-audit, not qualified native-speaker approval. No tests, builds, scans, browser review, CI, repo/worktree edits, or PR updates were run.

## Artifacts

- `cross-audit-ledger.jsonl`: all 240 cells, exact source/current/blind/primary/recommended targets and hashes, caller pins, structural checks, technical terms, and rationales.
- `disagreements.jsonl`: every row with candidate/status divergence or a cross-audit override/hold.
- `requested-disputed-recommendations.json`: concise exact recommendations for the disputed issues requested in the task.
- `technical-literal-audit.json`, `live-pr-verification.json`, `provenance-and-hashes.json`, `summary.json`, and `SHA256SUMS.txt` capture validation/provenance.
