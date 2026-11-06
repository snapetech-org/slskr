from __future__ import annotations

import hashlib
import json
import re
import subprocess
from pathlib import Path

REPO = Path('/mnt/disks/scratch/task-worktrees/localization-20261103/slskr-pr204-w1123-1142-apply')
ROOT = Path('/mnt/disks/scratch/task-scratch/slskr-pr204-w1183-1202-input-20261103')
OUT = ROOT / 'clean-input'
EXPECTED_HEAD = '8e60a51ec25967df115a3fd8c42872abbec58d8a'
EXPECTED_TREE = 'c2ec31432943730f0a8f3ee87687c46b6a4400c2'
EXPECTED_PR_BRANCH = 'codex/slskr-l10n-audit-20261030'
EXPECTED_BASE = '2a2b188f10b9460a15bc6d5c34e406b0193d51ba'
PR_NUMBER = 204


def git(*args: str) -> str:
    return subprocess.check_output(['git', *args], cwd=REPO, text=True).strip()


def raw(path: str) -> bytes:
    return subprocess.check_output(['git', 'show', f'{EXPECTED_HEAD}:{path}'], cwd=REPO)


def sha_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha_text(text: str) -> str:
    return sha_bytes(text.encode('utf-8'))


def write_json(path: Path, value) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + '\n', encoding='utf-8')


def pin(path: str) -> dict:
    data = raw(path)
    return {
        'path': path,
        'sha256': sha_bytes(data),
        'gitBlob': git('rev-parse', f'{EXPECTED_HEAD}:{path}'),
        'byteCount': len(data),
        'lineCount': data.count(b'\n'),
    }


# Re-attest PR metadata without fetching or displaying the PR body.
pr = json.loads(subprocess.check_output([
    'gh', 'api', f'repos/snapetech-org/slskR/pulls/{PR_NUMBER}',
    '--jq', '{state: .state, draft: .draft, headRef: .head.ref, head: .head.sha, baseRef: .base.ref, base: .base.sha}',
], cwd=REPO, text=True))
remote_head = git('ls-remote', 'https://github.com/snapetech-org/slskR.git', 'refs/pull/204/head').split()[0]
local_head = git('rev-parse', 'HEAD')
local_tree = git('rev-parse', 'HEAD^{tree}')
local_branch = git('branch', '--show-current')
local_status = git('status', '--porcelain')
assert pr['state'] == 'open' and pr['draft'] is True
assert pr['head'] == EXPECTED_HEAD and remote_head == EXPECTED_HEAD and local_head == EXPECTED_HEAD
assert local_tree == EXPECTED_TREE and pr['headRef'] == EXPECTED_PR_BRANCH and pr['base'] == EXPECTED_BASE
assert pr['baseRef'] == 'main' and not local_status

# The English source strings are the lookup keys in the 12 runtime locale files.
runtime_path = 'web/src/lib/interfaceLocale.js'
runtime_text = raw(runtime_path).decode('utf-8')
option_block = runtime_text.split('export const INTERFACE_LANGUAGE_OPTIONS = [', 1)[1].split('];', 1)[0]
runtime_locale_order = re.findall(r"value:\s*'([^']+)'", option_block)
assert runtime_locale_order == ['en', 'es', 'zh-Hans', 'hi', 'de', 'ja', 'fr', 'pt-BR', 'ar', 'ko', 'zh-Hant', 'vi', 'id']
locales = [language for language in runtime_locale_order if language != 'en']
catalog_paths = {language: f'web/src/lib/locales/ui-labels.{language}.json' for language in locales}
catalogs = {language: json.loads(raw(path)) for language, path in catalog_paths.items()}
keyset = set(catalogs['de'])
assert all(set(catalog) == keyset for catalog in catalogs.values())
source_keys = sorted(keyset)
assert len(source_keys) == 5441
selected = [(position, source_keys[position - 1]) for position in range(1183, 1203)]
OUT.mkdir(parents=True, exist_ok=True)
(OUT / 'selected-source-keys.txt').write_text(''.join(f'{key}\n' for _, key in selected), encoding='utf-8')

# Search exact source-key literals in product source paths only. The search is
# used only to capture direct caller context; no tests or translations are read
# as caller evidence. Exclude test files, catalogs, docs, generated/vendor data.
grep_result = subprocess.run([
    'git', 'grep', '--no-color', '-n', '-F', '-f', str(OUT / 'selected-source-keys.txt'),
    EXPECTED_HEAD, '--', 'web/src', 'src', 'crates/slskr/src',
], cwd=REPO, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
if grep_result.returncode not in (0, 1):
    raise RuntimeError(grep_result.stderr)
source_code_extensions = ('.js', '.jsx', '.ts', '.tsx', '.rs')
selected_by_text = {text: position for position, text in selected}
matches: dict[str, list[tuple[str, int, str]]] = {text: [] for _, text in selected}
for record in grep_result.stdout.splitlines():
    fields = record.split(':', 3)
    if len(fields) != 4:
        continue
    _, path, line_number, line_text = fields
    if not path.endswith(source_code_extensions):
        continue
    if '/locales/' in path or '.test.' in path or '.spec.' in path or '/__tests__/' in path or '/web_tests/' in path:
        continue
    for source_text in selected_by_text:
        start = 0
        while True:
            offset = line_text.find(source_text, start)
            if offset < 0:
                break
            if offset > 0 and line_text[offset - 1] in "'\"`" and offset + len(source_text) < len(line_text) and line_text[offset + len(source_text)] == line_text[offset - 1]:
                if source_text == 'Domain' and path == 'crates/slskr/src/config_file_parts/federation_membership.rs' and int(line_number) == 10:
                    pass
                else:
                    matches[source_text].append((path, int(line_number), line_text))
            start = offset + len(source_text)

# Playlist intake labels are stored as opaque option values and localized at
# their rendering sites through interfaceText(option.text); retain both the
# source value and the runtime-value consumer callsite.
runtime_value_consumers = {
    'Do not change cover art': ('web/src/components/PlaylistIntake/PlaylistIntake.jsx', 424),
    'Do not run ReplayGain': ('web/src/components/PlaylistIntake/PlaylistIntake.jsx', 433),
}
for source_text, (path, line_number) in runtime_value_consumers.items():
    lines = raw(path).decode('utf-8').splitlines()
    line_text = lines[line_number - 1]
    assert 'interfaceText(option.text)' in line_text
    assert source_text in selected_by_text
    matches[source_text].append((path, line_number, line_text))

caller_file_bytes: dict[str, bytes] = {}
source_context_rows = []
source_records = []
cells = []

for position, source_text in selected:
    source_hash = sha_text(source_text)
    refs = []
    for path, line_number, matched_line in sorted(set(matches[source_text])):
        lines = raw(path).decode('utf-8').splitlines()
        assert 1 <= line_number <= len(lines) and lines[line_number - 1] == matched_line
        # Preserve a compact exact-head neighborhood around each literal caller.
        start_line = max(1, line_number - 3)
        end_line = min(len(lines), line_number + 5)
        context_lines = [
            {'line': number, 'text': lines[number - 1], 'lineSha256': sha_text(lines[number - 1])}
            for number in range(start_line, end_line + 1)
        ]
        if path.endswith('serverErrorMessageAllowlist.js'):
            role = 'server-error translation allowlist'
        elif path.endswith('PlaylistIntake.jsx'):
            role = 'localized runtime-value consumer'
        elif path.startswith('crates/slskr/src/') or path.startswith('src/'):
            role = 'server-side literal caller'
        elif path.endswith('playlistIntake.js'):
            role = 'literal option value'
        else:
            role = 'UI literal caller'
        refs.append({
            'path': path,
            'line': line_number,
            'role': role,
            'matchKind': 'exact quoted source-key literal',
            'contextStartLine': start_line,
            'contextEndLine': end_line,
            'contextLines': context_lines,
            'contextSha256': sha_text('\n'.join(item['text'] for item in context_lines)),
        })
        caller_file_bytes[path] = raw(path)
    refs.sort(key=lambda item: (item['path'], item['line'], item['role']))
    source_placeholders = re.findall(r'\{[A-Za-z][A-Za-z0-9_]*\}', source_text)
    source_context_rows.append({
        'position': position,
        'sourceKey': source_text,
        'sourceKeySha256': source_hash,
        'sourcePlaceholders': source_placeholders,
        'callerReferenceCount': len(refs),
        'locations': [f"{ref['path']}:{ref['line']}" for ref in refs],
        'references': refs,
    })
    source_records.append({
        'position': position,
        'sourceKey': source_text,
        'sourceKeySha256': source_hash,
        'callerReferenceCount': len(refs),
    })
    for language in locales:
        target = catalogs[language][source_text]
        assert isinstance(target, str), (position, source_text, language, type(target).__name__)
        target_placeholders = re.findall(r'\{[A-Za-z][A-Za-z0-9_]*\}', target)
        cells.append({
            'schemaVersion': 1,
            'repository': 'snapetech-org/slskR',
            'pullRequest': PR_NUMBER,
            'window': 'W1183-W1202',
            'head': EXPECTED_HEAD,
            'tree': EXPECTED_TREE,
            'position': position,
            'sourceKey': source_text,
            'sourceKeySha256': source_hash,
            'locale': language,
            'currentTarget': target,
            'currentTargetSha256': sha_text(target),
            'catalogPath': catalog_paths[language],
            'catalogSha256': sha_bytes(raw(catalog_paths[language])),
            'catalogGitBlob': git('rev-parse', f'{EXPECTED_HEAD}:{catalog_paths[language]}'),
            'sourceCallerCount': len(refs),
            'sourcePlaceholders': source_placeholders,
            'currentTargetPlaceholders': target_placeholders,
            'placeholderTokenSequenceMatchesSource': target_placeholders == source_placeholders,
        })

assert len(cells) == 240 and len(source_context_rows) == 20
assert all(source_context_rows[index]['position'] == 1183 + index for index in range(20))
assert all(source_context_rows[index]['callerReferenceCount'] > 0 for index in range(20))

catalog_pins = {language: pin(path) | {'keyCount': len(catalogs[language])} for language, path in catalog_paths.items()}
caller_pins = {path: pin(path) for path in sorted(caller_file_bytes)}
runtime_lines = runtime_text.splitlines()
runtime_snippets = []
for marker in ('const translationFor =', 'const replaceInterfaceValues ='):
    line_number = next(index + 1 for index, line in enumerate(runtime_lines) if marker in line)
    start_line = max(1, line_number - 1)
    end_line = min(len(runtime_lines), line_number + 8)
    runtime_snippets.append({
        'marker': marker,
        'startLine': start_line,
        'endLine': end_line,
        'lines': [{'line': number, 'text': runtime_lines[number - 1], 'lineSha256': sha_text(runtime_lines[number - 1])} for number in range(start_line, end_line + 1)],
    })

source_order_sha = sha_text('\n'.join(source_keys) + '\n')
write_json(OUT / 'PR-attestation.json', {
    'repository': 'snapetech-org/slskR',
    'pullRequest': PR_NUMBER,
    'state': pr['state'],
    'draft': pr['draft'],
    'headRefName': pr['headRef'],
    'headRefOid': pr['head'],
    'remotePullRef': 'refs/pull/204/head',
    'remotePullRefHead': remote_head,
    'baseRefName': pr['baseRef'],
    'baseRefOid': pr['base'],
    'localWorktree': str(REPO),
    'localWorktreeBranch': local_branch,
    'localWorktreeHead': local_head,
    'localWorktreeTree': local_tree,
    'localWorktreeStatusClean': True,
})
write_json(OUT / 'catalog-file-pins.json', {
    'schemaVersion': 1,
    'head': EXPECTED_HEAD,
    'tree': EXPECTED_TREE,
    'localesInRuntimeOrder': locales,
    'sourceLookupKeySetCount': len(keyset),
    'sourceLookupKeyOrderSha256': source_order_sha,
    'localeCatalogs': catalog_pins,
    'localeRuntime': pin(runtime_path),
    'callerFiles': caller_pins,
})
(OUT / 'source-contexts.jsonl').write_text(''.join(json.dumps(row, ensure_ascii=False, sort_keys=True) + '\n' for row in source_context_rows), encoding='utf-8')
(OUT / 'current-target-cells.jsonl').write_text(''.join(json.dumps(row, ensure_ascii=False, sort_keys=True) + '\n' for row in cells), encoding='utf-8')
write_json(OUT / 'localization-runtime-context.json', {
    'path': runtime_path,
    'pin': pin(runtime_path),
    'localeOptionOrder': runtime_locale_order,
    'lookupAndPlaceholderContext': runtime_snippets,
    'note': 'Runtime expressions in caller context are preserved verbatim and are not evaluated or paraphrased.',
})

manifest = {
    'repository': 'snapetech-org/slskR',
    'pullRequest': PR_NUMBER,
    'head': EXPECTED_HEAD,
    'tree': EXPECTED_TREE,
    'state': pr['state'],
    'draft': pr['draft'],
    'headRef': pr['headRef'],
    'baseRef': pr['baseRef'],
    'baseSha': pr['base'],
    'remotePullRefHead': remote_head,
    'localWorktree': str(REPO),
    'localWorktreeBranch': local_branch,
    'localWorktreeHead': local_head,
    'localWorktreeTree': local_tree,
    'localWorktreeStatusClean': True,
    'window': 'W1183-W1202',
    'selectedPositions': [1183, 1202],
    'selectionRule': 'One-based positions 1183–1202 in the 5,441 unique English source lookup keys shared by the 12 runtime locale catalogs; keys are sorted lexicographically by exact Unicode string and source strings are direct catalog lookup keys.',
    'sourceRecordCount': len(source_keys),
    'sourceLookupKeyOrderSha256': source_order_sha,
    'sourceLookupKeyOrderHashFormat': 'SHA-256 of all unique source keys sorted lexicographically, one exact key per line, trailing newline.',
    'sourceCount': len(source_context_rows),
    'localeCount': len(locales),
    'localeOrder': locales,
    'cellCount': len(cells),
    'sourceIds': source_records,
    'callerFileCount': len(caller_pins),
    'callerReferenceCount': sum(row['callerReferenceCount'] for row in source_context_rows),
    'sourceContextRows': len(source_context_rows),
    'placeholderTokenSequenceMismatchCount': sum(1 for cell in cells if not cell['placeholderTokenSequenceMatchesSource']),
    'candidateFreeInputOnly': True,
    'semanticReviewIncluded': False,
    'proposedTranslationsIncluded': False,
    'nativeSpeakerApproval': False,
    'opaqueRuntimeValuesPolicy': 'Caller lines and runtime expressions are captured verbatim from pinned source files; values are not evaluated, inferred, or rewritten.',
}
write_json(OUT / 'manifest.json', manifest)

readme = f'''# slskR PR #204 W1183–W1202 candidate-free input\n\nThis packet contains 20 English source lookup keys and 240 current target cells across the 12 runtime locales. It is pinned to live open draft PR head `{EXPECTED_HEAD}` and tree `{EXPECTED_TREE}`. The PR head ref is `{pr['headRef']}`; the clean exact-head worktree branch is `{local_branch}`.\n\nThe 12 locale files have identical key sets with 5,441 source keys. Window positions are one-based in the lexicographically sorted exact source-key strings. Each source key is paired with every current locale value and SHA-256. Caller references are exact quoted source-key literals from pinned current code files, with adjacent source lines and per-file SHA-256/Git-blob pins. Direct server error callers and their client allowlist entries are both retained where present.\n\nCaller runtime expressions are captured verbatim and remain opaque. Source/current placeholder token sequences are recorded mechanically; this packet contains no semantic decisions or proposed translations. Machine review is not native-speaker approval.\n'''
(OUT / 'README.md').write_text(readme, encoding='utf-8')

sum_lines = []
for path in sorted(OUT.iterdir()):
    if path.is_file() and path.name != 'SHA256SUMS.txt':
        sum_lines.append(f'{sha_bytes(path.read_bytes())}  {path.name}')
(OUT / 'SHA256SUMS.txt').write_text('\n'.join(sum_lines) + '\n', encoding='utf-8')

print(json.dumps({
    'head': EXPECTED_HEAD,
    'tree': EXPECTED_TREE,
    'sourceCount': len(source_context_rows),
    'localeCount': len(locales),
    'cellCount': len(cells),
    'sourceKeys': source_records,
    'callerFileCount': len(caller_pins),
    'callerReferenceCount': sum(row['callerReferenceCount'] for row in source_context_rows),
    'placeholderTokenSequenceMismatchCount': manifest['placeholderTokenSequenceMismatchCount'],
    'sourceLookupKeyOrderSha256': source_order_sha,
    'output': str(OUT),
}, ensure_ascii=False, indent=2))
