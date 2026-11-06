# slskR Chinese Full preset label correction

This exact-hash follow-up corrects the Chinese `Full` quality-preset label at source inventory index 1823. Pinned caller context shows the selector value maps to uncapped rendering, and the adjacent tooltip says that `Full` leaves rendering uncapped. The previous zh-Hans `满的` and zh-Hant `滿的` labels mean “full/filled”; the corrected labels are `不设上限` and `不設上限`.

The change is pinned to input head `c0255ca319b9d5b3bba06980fc97ddb72072f759` / tree `0773b762a309cad8e102e7b159eeef00a0eaf1d9`. Exact source, caller files, current catalog blobs, current target hashes, and recommended target hashes were checked before applying. Both targets were read back afterward. The two locale files retain 5,438 keys, and all twelve locale catalogs retain identical key sets.

The issue was identified in independent cross-review of W603–622; the root review confirmed the selector/caller semantics before applying the two proposals. Qualified native-speaker review remains outstanding. No tests, builds, scans, CI jobs, source changes, workflow changes, releases, tags, or merges were made. The original cross-review packet is preserved as `crossreview-README.md`, `crossreview-SHA256SUMS`, and `full-preset-followup-evidence.json`.
