# Independent blind semantic review — slskR PR #209 W1543–W1562

Exact pin: `snapetech-org/slskR` PR #209, head `c15eddffec2c4c24cc091b2a6ebf0c43fa58ef1b`, tree `4259db991f25fbbd0200963769e62bb7e2150806`; base `main` at `1bbaec9fdc63a86de343e37e33bae70d44301a36`.

## Result

Reviewed all 240 cells across 20 source keys and 12 locales. Dispositions: 218 accept, 22 hold, across 20 findings. Overall confidence: moderate; findings carry their own confidence labels.

The packet verifier passed. The 5,441-key source queue and 240 selected cells are internally pinned. All 20 source keys have resolved production callers (21 literal references/occurrences total); callerless cells: 0. Placeholder sequence, markup, numeric-token, and protected-literal mismatch counts are all 0. These structural checks do not replace the semantic findings below.

Live ref checks: PR tuple `[head SHA, head ref, base SHA]` matched the packet; branch and pull refs both pointed to the head. The commit tree matched the packet, and all 12 locale catalog blobs plus the interface-locale runtime blob matched the exact tree.

## Findings

| ID | Cells | Severity / confidence | Finding |
|---|---|---|---|
| F01 | ar:1544 | major / high | The Arabic target says content data and drops the metadata distinction. Suggested action: Use an Arabic equivalent of content metadata (for example البيانات الوصفية للمحتوى) while preserving {error}. |
| F02 | es:1547 | moderate / moderate | The phrasing reads as timestamps that were seen for the last time; it is awkward and blurs last-seen timestamps. Suggested action: Use a natural Spanish phrasing for timestamps of last seen/last activity and preserve {message}. |
| F03 | fr:1547 | moderate / moderate | The phrase for the last view suggests a viewing event rather than a last-seen time and is not idiomatic here. Suggested action: Use a natural French equivalent for last-seen timestamps and preserve {message}. |
| F04 | pt-BR:1547 | moderate / moderate | The wording makes the timestamps themselves sound as if they were seen; it is clumsy and obscures the last-seen meaning. Suggested action: Use a natural Brazilian Portuguese equivalent for timestamps of last seen/last activity and preserve {message}. |
| F05 | ja:1547 | major / high | The Japanese wording means timestamps last displayed, which is different from the source's last-seen timestamps. Suggested action: Translate last seen as a person's last confirmed/online time, not the last time a timestamp was displayed; preserve {message}. |
| F06 | ko:1547 | major / high | The Korean wording means timestamps last displayed, rather than last-seen timestamps. Suggested action: Use a Korean equivalent for last-seen/last-online timestamps and preserve {message}. |
| F07 | de:1548 | major / high | The German compound means member assignments/allocations, not member affinities. Suggested action: Use a German equivalent for affinities or similarity scores between members. |
| F08 | ar:1549 | moderate / moderate | The Arabic term refers broadly to member connections/associations and is less precise than the affinity concept used in the paired key. Suggested action: Keep the affinity/similarity terminology consistent with the paired member-affinities message and preserve {message}. |
| F09 | ko:1549 | moderate / moderate | The Korean term shifts from affinity at position 1548 to intimacy/closeness here, which suggests a different interpersonal meaning. Suggested action: Reuse the same Korean affinity term used for position 1548 and preserve {message}. |
| F10 | vi:1549 | moderate / moderate | The Vietnamese wording refers to members' relationships rather than an affinity/similarity measure, and differs from the paired key. Suggested action: Use terminology aligned with the member-affinity/similarity wording at position 1548 and preserve {message}. |
| F11 | zh-Hans:1549, zh-Hant:1549 | moderate / moderate | Both Chinese variants drop the degree/affinity aspect used for position 1548, leaving a broader member-association term. Suggested action: Keep the member-affinity/relatedness term consistent with position 1548 in each script and preserve {message}. |
| F12 | zh-Hans:1550 | moderate / moderate | The Simplified Chinese wording reads as statistics about member relationships, rather than membership statistics. Suggested action: Use a term for membership or member status statistics. |
| F13 | zh-Hant:1550 | moderate / moderate | The Traditional Chinese wording reads as statistics about member relationships, rather than membership statistics. Suggested action: Use a term for membership or member status statistics. |
| F14 | zh-Hans:1551 | moderate / moderate | The Simplified Chinese wording says getting a member, which is ambiguous with retrieving a member record and does not clearly name the membership result shown by the caller. Suggested action: Use a clear term for retrieving membership/member-status information and preserve the colon. |
| F15 | zh-Hant:1551 | moderate / moderate | The Traditional Chinese wording says getting a member, which is ambiguous with retrieving a member record and does not clearly name the membership result shown by the caller. Suggested action: Use a clear term for retrieving membership/member-status information and preserve the colon. |
| F16 | ko:1551 | major / high | The Korean wording means sign-up/registration failed, while the caller renders an error from a membership result; it changes retrieval into joining/registering. Suggested action: Translate failure to retrieve membership information and preserve the colon. |
| F17 | vi:1551 | major / high | The Vietnamese wording means being unable to become a member, while the caller renders an error from a membership result; it changes retrieval into joining. Suggested action: Translate failure to retrieve membership information and preserve the colon. |
| F18 | hi:1553 | moderate / moderate | The Hindi compound for opinion statistics omits the genitive marker used naturally in the paired no-placeholder key, making the phrase awkward. Suggested action: Use राय के आँकड़े (or another natural Hindi equivalent) and preserve {message}. |
| F19 | de:1554 | major / high | The German target says ratings/reviews, while the paired placeholder message at position 1555 uses opinions; this changes the concept and is inconsistent within the same component. Suggested action: Use the same German term for opinions as position 1555. |
| F20 | de:1560, de:1561 | moderate / high | Both German translations use beitreten without the required dative article, so the construction is ungrammatical. The paired key at 1561 has the same issue. Suggested action: Use a grammatical dative construction such as Dem Raum konnte nicht beigetreten werden, preserving the error placeholder at position 1561. |

## Blind boundary

This review used only the candidate-free input packet for source keys, current targets, callers, runtime context, and integrity pins. I did not open primary-review material, any cross-review, prior application readback JSONL, or the PR description/body. The allowed packet builder/verifier files were read; no external application evidence was opened. No catalog, PR, branch, workflow, or release data was changed.

Cell-level accept/hold statuses and hashes are in `review-cells.jsonl`; finding details are in `findings.json`. The output verifier checks those records against the candidate-free packet and sealed hashes.
