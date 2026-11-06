# slskR PR #204 localization review — W963–W982

Reviewed source positions 963–982 across all 12 direct locales: 240 cells at baseline PR head 99282b2f9b904f9814f5be66d8f643175e134f8e, tree ba0ba0790da40159b8d92935f0866cb6a112edce.

## Independent review and adjudication

The primary review recorded 170 accept-current, 10 corrections, 24 refinements, and 36 holds. The blind cross-review recorded 175 accept-current, 18 corrections, 11 refinements, and the same 36 holds. Root adjudication selected 161 accept-current, 22 corrections, 21 refinements, and 36 holds.

Applied 42 exact-hash catalog value changes across all 12 locale catalogs. All 240 final values read back with zero mismatches; the catalogs retain the same ordered 5,441-key set. The 36 holds remain at positions 970, 971, and 980 because no exact production caller was found.

## English source clarification

The source at position 964 was ambiguous. The browser-local disabledAuthorities state shows that local describes the disable choice, not the authorities. The source now reads: “Copy the visible conflict report, including which authorities you selected to disable locally. This does not change backend realm governance.” Both source callsites were updated, and the same 12 reviewed translations were rekeyed under the clarified source. Key order and catalog size remain unchanged.

The selected targets preserve all placeholders, markup, Soulseek, and CSV literals. Position 967 uses corpus/dataset meaning; position 968 is a corpus-match heading; positions 974–975 use the Wishlist context; position 979 retains both file/error placeholders.

Primary, independent cross-review, and root-adjudication folders retain their exact input pins, ledgers, rationales, and checksums. The apply plan and 240-cell post-rekey readback are at the top level.

This is machine-assisted review, not qualified native-speaker approval. Current-head browser acceptance remains outstanding. No tests, builds, scans, or CI were run; no workflow edits, merge, release, or tag occurred.
