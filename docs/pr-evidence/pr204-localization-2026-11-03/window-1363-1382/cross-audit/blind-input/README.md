# slskR PR #204 W1363-W1382 blind input

This packet contains 240 source-and-locale prompts for independent translation review. It is pinned to the exact PR head and tree recorded in manifest.json.

Each prompt includes the English source text, locale code and language name, source hash, caller-reference hashes, and a reference to the corresponding source/caller excerpt in source-contexts.jsonl. The callerless source at rank 1376 is represented with an empty caller-reference list and caller count zero.

The packet was built only from the sealed source-contexts.jsonl and non-translation metadata in its manifest. It contains no locale catalog values, glossary translations, candidate proposals, or review decisions.

Run python3 verify-blind-input.py and sha256sum -c SHA256SUMS.txt from this directory.
