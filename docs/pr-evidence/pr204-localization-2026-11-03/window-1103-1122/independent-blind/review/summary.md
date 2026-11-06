# Independent blind review: slskR PR #204, W1103–W1122

## Scope and provenance

- Pinned candidate head: `e45e6967625c5e804b688b9cb03d359ea59d000b`; tree: `c5164178f16e0fa2f59586c9ab3685e1ac08dfa5`.
- Input: candidate-free packet at `/mnt/disks/scratch/task-scratch/slskr-pr204-W1103-1122-blind-input-20261103/input`; packet SHA256SUMS passed before review.
- Window: 20 source IDs × 12 direct locales = **240 cells**. Source/current strings and hashes were taken from the packet; the packet’s pinned caller snippets supplied context. No proposal, primary-private, or decision files were opened, and no repository or PR files were edited.
- Each proposed-target hash is SHA-256 over the exact UTF-8 proposed string. For a hold or keep, the proposed string is the unchanged current target, with the same hash.

## Dispositions

- `KEEP_CANDIDATE`: 126 cells retain the current translation as a machine-review candidate.
- `REVISE_CANDIDATE`: 14 cells have an independently drafted wording candidate.
- `HOLD_DIRECT_CALLER_ABSENT`: 96 cells preserve current values because no direct localized caller is pinned for their source ID.
- `HOLD_TERM_REVIEW`: 4 cells preserve current values pending terminology/native review of “swarm”.

Source IDs held because no direct localized caller was pinned: `Descriptor`, `Descriptor ContentID is required`, `Descriptor is required`, `Destination host must be between 1 and 253 characters`, `Destination is not allowed by the Pod private-gateway policy`, `Destination must be relative and stay within the download root`, `Destination port must be between 1 and 65535`, `Detected`. This uses the packet’s `localizedCallPattern` evidence; it does not infer that no indirect display path exists elsewhere.

## Independent wording candidates

- **Descending / fr** → `Décroissant` — In the pinned caller this is a sort-order choice paired with “Ascending”; “décroissant” is the conventional French term for descending order, while “descendant” is ambiguous with a descendant/person.
- **Description / vi** → `Mô tả` — This is a collection form field label. “Mô tả” is the concise Vietnamese UI label; the current nominalized phrase “Sự miêu tả” is unnecessarily literal for a field.
- **Descriptor Retrieval / hi** → `डिस्क्रिप्टर पुनर्प्राप्ति` — The dashboard heading is about retrieving a technical media descriptor. The current “वर्णनकर्ता” suggests a person who describes; this aligns the term with the same catalog’s “डिस्क्रिप्टर JSON” and “डिस्क्रिप्टर” usage.
- **Descriptor Retrieval / vi** → `Truy xuất bộ mô tả` — This dashboard heading refers to retrieval of a technical descriptor. The current “mô tả” reads as the content “description”; “bộ mô tả” matches the catalog’s existing descriptor term in “Descriptor Retrieved”.
- **Descriptor Verification / ar** → `التحقق من الواصف` — The card heading is for verification of a technical descriptor. The current “الوصف” means description and does not match this catalog’s “واصف” for Descriptor.
- **Descriptor Verification / hi** → `डिस्क्रिप्टर सत्यापन` — This card heading is technical descriptor verification. The current “वर्णनकर्ता” suggests a describer; the candidate uses the same technical transliteration already used for “Descriptor JSON”.
- **Descriptor Verification / vi** → `Xác minh bộ mô tả` — This card heading verifies a technical descriptor. The current “mô tả” reads as “description”; “bộ mô tả” matches the catalog’s existing descriptor wording.
- **Detailed / ko** → `상세` — This is a standalone experience-setting option (key/value “detailed”), so the concise UI form “상세” is more natural than the modifier form “상세한” without a following noun.
- **Detailed / zh-Hans** → `详细` — This is a standalone experience-setting option (key/value “detailed”); “详细的” is a modifier form that normally expects a noun, while “详细” works as the compact option label.
- **Detailed / zh-Hant** → `詳細` — This is a standalone experience-setting option (key/value “detailed”); “詳細的” is a modifier form that normally expects a noun, while “詳細” works as the compact option label.
- **Details / zh-Hans** → `详情` — The pinned caller uses this as a table header for the Details column. “详情” is a conventional UI label for a record/details view; “细节” more often refers to particulars or minutiae.
- **Details / zh-Hant** → `詳情` — The pinned caller uses this as a table header for the Details column. “詳情” is a conventional UI label for a record/details view; “細節” more often refers to particulars or minutiae.
- **Detect quality issues, transcodes, and missing tracks / ar** → `اكتشاف مشكلات الجودة وعمليات تحويل الترميز والمسارات المفقودة` — The Library Health subheader lists quality issues, transcoding, and missing tracks. “الرموز المحولة” means converted codes/symbols, not transcoding; “عمليات تحويل الترميز” carries the intended media-processing sense.
- **Diagnostic Bundle / fr** → `Ensemble de diagnostic` — This is the button and modal heading for a copied diagnostic package. “Offre groupée” commonly suggests a bundled commercial offer; “Ensemble de diagnostic” avoids that false-friend reading and matches the toast wording already present in this catalog.

The ledger records each source, current target, proposed target, exact hashes, caller references, semantic rationale, placeholder and markup scans, protected literals, numeric tokens, and Arabic RTL notes. The packet has no template placeholders or markup in these 240 strings. Protected API identifiers and numeric bounds are checked per row; Arabic notes flag mixed-direction rendering for Latin identifiers and numbers.

## Limits

This is an independent machine review based on the supplied strings and caller snippets. It is **not qualified native-speaker approval**. Every candidate wording, including unchanged values, needs native-speaker review before release. Confidence labels describe this semantic pass only; they do not replace localization QA. No tests, builds, scans, CI dispatches, or workflow edits were run.
