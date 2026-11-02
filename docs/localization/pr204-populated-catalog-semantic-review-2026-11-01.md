# PR #204 populated-catalog semantic review

## Latest exact-current status

- PR #204 remains open as a draft. Evidence head is `48211078d858e9dfbbc2fb2bc74d65cd54c58f0f` / tree `741d3be561eab466fcf5f79776d3e8350b2895e2`; latest catalog application is `de509ead1789fe64811b14b63e1a22c14ade6893` / tree `e50004385568ab25e9d3eb5d314654880ef6ae8f`. Source/runtime context remains `7ff454828398de6a3cfb72fe7f0ed21fe419425b` / tree `9e9f2aa743c4ff3236af8f99619803bdc3a37152`.
- Direct catalogs contain 65,244 populated cells across 12 locales. The source-linked rollout target remains 6,588 translation cells, with zero missing, null, blank, or English-identical values in the frozen source snapshot.
- Exact-current reconciliation scanned 858 evidence files and honored 97 exact supersession references across 25 conflict/status reconciliation rows. Current unique-cell statuses: **23,598 accepted, 290 corrected, 10,731 correction-needed, 289 held, zero conflicting exact statuses, and 30,336 unreviewed**. The unreviewed cells span 3,680 source IDs. Evidence-input manifest SHA-256: `f6dbcd12b6f5b0fa87af1ab8739ddafa77172e49f3d79e20c3500b8e0346a624`. Scan report SHA-256: `2deb13947e32874bb74beec652d83c42dc899fa1b5ec35935f43637859159111`.
- Per-locale unreviewed counts: ar 3,007; de 3,201; es 3,022; fr 3,075; hi 2,989; id 3,030; ja 2,002; ko 2,002; pt-BR 2,002; vi 2,002; zh-Hans 2,002; zh-Hant 2,002. The next disjoint source-key window is 283–302.
- The 6,588-cell source-linked audit remains complete. Whole-catalog semantic review continues; 30,336 cells are unreviewed and 10,731 remain correction-needed. No release or tag was cut.

The exact-current report and rerunnable scanner are in [`pr204-exact-current-scan-2026-11-01`](pr204-exact-current-scan-2026-11-01/).

## Independent semantic window: source indices 263–282

This exact-head review covers 20 source keys and all 240 populated values across twelve locales. At baseline head `5a697d84c32043b9a56ab052cdbecc8529db1ade` / tree `923a788e4c22df73380cd498b0f11ab1a182b749`, exact-hash reconciliation found 25 fresh cells, 204 accepted carries, and 11 prior correction-needed cells, with zero exact-status conflicts. Fresh review accepted 22 unchanged and identified three correction targets. All 14 candidates were independently cross-reviewed by root: eight were accepted as proposed and six refined. The 14 approved corrections were applied across eight locale catalogs; the final window contains 226 accepted and 14 corrected cells, with zero holds or unresolved conflicts.

Catalog application `de509ead1789fe64811b14b63e1a22c14ade6893` / tree `e50004385568ab25e9d3eb5d314654880ef6ae8f` is a direct child of the review head. The checksummed evidence bundle and exact verifier are in [`independent-0263-0282-all-12-locales`](../pr-evidence/pr204-semantic-review-2026-11-01/independent-0263-0282-all-12-locales/). Candidate ledger SHA-256 `8ab9e8e8c2d259cf02d985feb592641fd660df24e6a990049a1a13e8499c08ad`; root cross-review ledger `863f30995df14ad349335fa2bd143c2345d8b68e93082e8692f45786345ce5a4`; root apply plan `30e54209464ff65e7f712c51d874e4a433aa98d6f22ddef3c4c283af096c9e94`; applied-corrections ledger `f2d17f180a0cf1c372f685469d8a95178e6f621c94ec6a06e796b64f718e2c50`. The verifier passed all 240 cells, 842 raw overlap inputs, all 10 caller-file pins, exact source/old/final hashes, placeholders, ICU and protected literals, and bundle checksums.

Headed visual review remains blocked: the exact branch has no `web/node_modules`, and an isolated preview would require dependency installation/build output. No shared daemon or other worktree preview was used. Browser recapture is required when an isolated exact-head preview can be supplied. Native-speaker approval is not claimed; confidence remains moderate. No tests, builds, CI, workflow edits, releases, or tags were performed.

## Independent semantic window: source indices 243–262

This exact-head window covers 240 populated cells: 90 fresh decisions (79 accepted and 11 corrected), 78 accepted carries, and 72 prior correction-needed cells. Root independently cross-reviewed all 83 exact-hash correction candidates: 71 were accepted as proposed and 12 refined. All 83 final targets were applied; final window disposition is 157 accepted and 83 corrected, with zero holds or conflicts. The changes touch all 12 locale catalogs and preserve reviewed placeholders, ICU structure, and protected literals.

The review baseline is `b70b68e0cc297d5a0a7f7ace6a47d3c950e22470` / tree `ca40b695c4ab3a2f0485791246ecffb1c0dc249e`; catalog application is `333df9a62f1a2d54186cc966ee0658b0c5d83de7` / tree `c4d442838f1932d7d3171a95944fb4ae94d7d2d2`; source/runtime context is `7ff454828398de6a3cfb72fe7f0ed21fe419425b` / tree `9e9f2aa743c4ff3236af8f99619803bdc3a37152`. The checksummed bundle, root cross-review and apply plan, exact overlap manifest, source pins, all-cell audit, and verifier are in [`independent-0243-0262-all-12-locales`](../pr-evidence/pr204-semantic-review-2026-11-01/independent-0243-0262-all-12-locales/).

Headed visual review remains blocked because the exact worktree has no `web/node_modules`; an exact-branch preview requires dependency installation/build output. No shared preview or browser session was used. Visual recapture is still required when an isolated preview can be supplied. Native-speaker approval is not claimed; confidence remains moderate.

Machine semantic review only; no tests, builds, CI, workflow changes, releases, or tags were performed.

## Independent semantic window: source indices 183–202

This exact-head window covers 240 populated cells: 64 fresh decisions (60 accepted, two moderate correction-needed, two corrected), 127 accepted carries, seven prior correction-needed exclusions, and 44 exact-hash catalog corrections. There are no exact-status conflicts or unresolved overlaps. Fresh corrections include the Indonesian completed-action toast and Hindi caution-toast directional mark; a parent reviewer independently cross-reviewed and approved removing the same leading U+200F from Japanese and Korean. The two fresh suggestions remain unchanged: Arabic caution-toast relation wording and French queue-tooltip phrasing.

The applied changes cover queue terminology in Korean/Simplified/Traditional Chinese; smart-radio query meanings in 11 locales; listening-history recommendation tracks in 10 locales; Hindi/Vietnamese LAN peer terminology; Vietnamese Wishlist glossary; five negative-interest messages; Japanese interest and FTP-address labels; Simplified/Traditional Chinese Administrator roles; four queued-track tooltips; Indonesian completed-toast tense; and the three Japanese/Korean/Hindi leading U+200F removals. Seven older correction-needed suggestions remain explicitly excluded, listed with exact hashes and prior findings in the evidence bundle.

The review baseline is `7fb1c1973efb37609f9817a395909bf1c0602c3b` / tree `7a239122e33bf8194d9a5a110a52975a17904cfb`; catalog application is `cc55673a362e627e256dc45cd90c9fe5c28c163f` / tree `739ba38688b25d02002a6f044cb393b4996de836`. The checksummed 240-cell evidence, 784 raw overlap inputs, source pins, and independent verifier are in [`independent-0183-0202-all-12-locales`](../pr-evidence/pr204-semantic-review-2026-11-01/independent-0183-0202-all-12-locales/). The headed visual check remains blocked because the isolated worktree has no dependencies and no compatible isolated backend; the shared daemon and any build were excluded.

Machine semantic review only; no native-speaker approval is claimed.

## Window 5380–5399

The exact-head window contains 240 cells: 210 newly reviewed decisions, 26 exact accepted carries, and four exact correction-needed terminal exclusions. The 210 decisions are 143 accepted, 61 correction-needed, and six held. There are no pending exact-terminal overlaps. The six holds cover `{filtered} / {total} searches` in Japanese, Korean, Brazilian Portuguese, Vietnamese, Simplified Chinese, and Traditional Chinese because the pinned tree has no non-locale callsite to establish placement.

The semantic corrections address P2P swarm wording, listening-history plays, directory/import counts, Mesh evidence publication terminology and status, external visualizer launch phrasing, play-count grammar, and an Indonesian seconds unit. All proposed values preserve checked placeholders and protected literals.

The checksummed bundle is in [`pr-evidence/pr204-semantic-review-2026-11-01/independent-5380-5399-all-12-locales`](../pr-evidence/pr204-semantic-review-2026-11-01/independent-5380-5399-all-12-locales/). It pins the PR head/tree, current catalog hashes, source-context blobs, selection/carries/exclusions, decisions, and evidence scan. Pre-application verification confirmed all 240 target hashes against the live checkout and the pinned source-context blobs against the same tree.

- Decision accumulator SHA-256 after applying this batch: `c98b1cd429deabe19e262fef3ac6c90bab921e32115b7d941928a8c0f27778eb`.
- Findings ledger SHA-256: `2d981e8b82e9d7080c04ebd26ca2971c704d954c3b3a39ccb4aa436b211b0ccd`.
- Final evidence-scan SHA-256: `f8683d215ab40ed40e5061d7b5e5d0511b49663215cf7cef6c5fa2a3aaa21aa7`.

Machine semantic review only; these results do not establish native-speaker approval or complete browser acceptance. This window did not edit catalogs, source, workflows, or run tests, builds, or CI.

## Independent semantic window: source indices 103–122

This 20-key window contains 240 populated cells: 71 fresh decisions (64 accepted and 7 correction-needed), 117 exact accepted carries, and 52 prior correction-needed exclusions. There are no exact-status conflicts or fresh overlaps. Four high-confidence pod-action fixes were applied in German (`Accept Join`, `Accept Join Request`), French (`Accept Join`), and Spanish (`Accept Join Request`); three moderate Spanish/Hindi/Indonesian `Accept Join` proposals remain unapplied.

The review was pinned to catalog head `f4d295b2df50fbce0d56c7b0b94b35ea87211d36` / tree `332e09992fd20eb5b0183a77be627732629edca7`. Evidence is in [`independent-0103-0122-all-12-locales`](../pr-evidence/pr204-semantic-review-2026-11-01/independent-0103-0122-all-12-locales/); its manifest SHA-256 is `3ac69b2ae39f0fdc078efe115156cf3568b29d30585636ba283fd243d9c2d545`. The four corrections are recorded in [`applied-high-confidence-corrections-0103-0122-2026-11-01`](../pr-evidence/pr204-semantic-review-2026-11-01/applied-high-confidence-corrections-0103-0122-2026-11-01/); corrected-target ledger SHA-256: `6286b92785907dcddbf2a6c2e73e1208262975c1a9807c4e2f31ba60c4942728`.

## Independent semantic window: source indices 123–142

This 20-key window contains 240 populated cells: 82 fresh decisions (80 accepted and 2 moderate correction-needed suggestions), 127 exact accepted carries, and 31 prior correction-needed exclusions. There are no exact-status conflicts or fresh overlaps. The Spanish/French `Active` suggestions address singular status rows and plural count labels sharing the same source key; they remain unapplied because the source key is reused in both contexts. The acquisition-profile template preserved `{profile}` and `{description}`; no direct runtime caller for that full source key was found at the pinned source head.

The catalog review was pinned to head `365677abe637fe720608fa05e8c250ea600deea0` / tree `b2e90645ec85eb04d907845f0d048eb78bed0005`. Evidence is in [`independent-0123-0142-all-12-locales`](../pr-evidence/pr204-semantic-review-2026-11-01/independent-0123-0142-all-12-locales/); its manifest SHA-256 is `3b7f5eee7bff2edc05b1ddbe1c083c53467c0ddded93ee9fccc40e670c3026fc`. The later exact-current pass reconciled all 25 status conflicts. The remaining unreviewed source keys and correction-needed cells are still in progress.

## Independent semantic window: source indices 143–162

This window covers 20 source keys and 240 populated values. Exact-hash overlap review found 87 fresh cells (84 accepted, 3 moderate correction-needed), 103 accepted carries, and 50 prior correction-needed cells; eight of those prior correction-needed values were corrected in this pass, leaving 42 exclusions. There were no conflicts or pending exact overlaps. A second exact-context review later accepted and applied all three fresh moderate findings in `e3b1667bcec64e3b41c124e66ea6b29cc88102b9`: French `Active Swarm Downloads` → `Téléchargements multi-sources actifs`, French `Add Forwarding` → `Ajouter une redirection de port`, and Hindi `Add Item to` → `आइटम जोड़ें:`. The separate addendum carries the context and exact-cell evidence.

Eight exact-hash catalog corrections were applied: Indonesian `Add Friend from Invite`, six `Add Hated` labels (ar/de/es/fr/hi/id), and Arabic `Add Interest`. The current cell hashes were revalidated against the exact 824 baseline and the proposals against the pinned contacts and Soulseek discovery source context. The headed visual check was attempted in an isolated Agent GUI session, but the exact-branch preview could not reach an isolated compatible backend and showed a lost-connection page. The longer discovery-button labels still need a layout check; the shared daemon and stale cached binary were not used.

The catalog review baseline is `82494e758b7a78abd34812264a57a2a80bcc4c5c` / tree `ab984cf0c7043479b07264ccede7800c46d71db2`; catalog application is `f4d5d8818028162266e56d027b7966f300bb6474` / tree `c4a4f0d55c8d206d19fe7c1b15f9b661f48e82a7`. Runtime source remains `7ff454828398de6a3cfb72fe7f0ed21fe419425b` / tree `9e9f2aa743c4ff3236af8f99619803bdc3a37152`. Evidence is in [`independent-0143-0162-all-12-locales`](../pr-evidence/pr204-semantic-review-2026-11-01/independent-0143-0162-all-12-locales/); manifest SHA-256 `e32e897347d7e89eb82e5c5557fba69bbc1ebab8a69217d1d880cae442f8dc10`, applied-correction ledger `a00ef17efad6775a9fd9004249eb13e3515e5cf6307fe273f061bfc1192c32ac`, and overlap-input manifest `f7cef3f2bd91544b45694d38d325d797994de69c59945a7ceb4dbf0dbc1f5a0c`. The verifier passed; it checks all 240 cells and 763 exact prior inputs, the eight catalog changes, placeholders, ICU syntax, source-context pins, and checksums.

The exact-current scan after this batch found zero conflicts. Following the next window and three-cell cross-review, the current scan at `e3b1667b` reports 30,643 unreviewed cells across 3,737 source IDs and no newly missing or blank values. The next disjoint window is source indices 183–202. No tests, builds, CI, workflow changes, release, or tag were performed.


## Independent semantic window: source indices 163–182

This exact-head window covers 240 populated cells: 71 fresh reviews (66 accepted, 3 moderate Hindi correction-needed suggestions, 2 held generic `Add New` labels), 116 exact accepted carries, 53 prior correction-needed values, and 10 high-confidence exact-hash corrections, leaving 43 correction-needed exclusions. There are no fresh overlaps or exact-status conflicts. The holds remain because the frozen source has no caller to identify the generic object for Arabic/French `Add New`.

Ten catalog fixes correct the `Add Wishlist` action in ar/de/es/fr/hi/id and restore the Wishlist destination to `Add one saved search…` in ar/de/es/id. Three moderate Hindi suggestions concern the `Add Member to` concatenated header, a comparison-graph bridge compound, and a result-condition phrase; they remain unchanged. Placeholders, ICU structure, and protected literals were checked over all 240 cells.

The review baseline is `a4dbef9a1dda24e104bdd5f8a6315ca7d6f3d541` / tree `3a00691cd5615fafa0026457afc19af3806e5329`; the ten-cell application is `2f7794cec0592ffd1a24490a5441b3ee7d1c728d` / tree `aa0c195ecf045fef9545ddbdc7df4a0da305943b`. Exact evidence, 772 raw overlap inputs, source pins, all-cell audit, and verifier are in [`independent-0163-0182-all-12-locales`](../pr-evidence/pr204-semantic-review-2026-11-01/independent-0163-0182-all-12-locales/); the raw-input manifest SHA-256 is `54b6d650032937279c3b2c63acfb32d5f3f82b7997984ef875456b98b5cdcad2`. The headed visual review could not pass the connection overlay because an isolated source-compatible backend was unavailable; no shared daemon, tests, builds, or CI were used.

A later, disjoint cross-review corrected three earlier cells at indices 146, 155, and 161. Its exact three-cell ledger and verifier are in [`cross-review-corrections-0143-0162-2026-11-01`](../pr-evidence/pr204-semantic-review-2026-11-01/cross-review-corrections-0143-0162-2026-11-01/).
