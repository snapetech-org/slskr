# slskR PR #204 loading-copy interpolation cross-review

- Frozen PR head/tree: `783201d6541188ce7af5b2e5dd5572eb919e8d10` / `5cb1b2b5699336a0ca7a966391eea12a1d553017`; OPEN/DRAFT before and after; worktree clean.
- The English source `Loading native Soulseek interests for {username}.` accurately describes the active-loading state. Popup opening triggers `onOpen={this.fetchInterests}`, which sets `interestsLoading` before the API request.
- **Branch placement matters:** use the new full source in the existing `interestsLoading` branch in place of “Loading native interests”. The old “Click to load...” text is in the later `!interests` branch; replacing it there does not reliably show a loading state.
- The parent’s `username && <Popup>` guard closes the falsy-username path: without a username the interests popup is not mounted. With a truthy username, loading/error/success branches cover settled states, so returning null from the later `!interests` fallback is safe. A blank first frame remains possible if popup-open commits before the `onOpen` loading update; no persistent empty state is reachable with the guard.
- `LocalizedText` forwards `values` to `t`; `interfaceLocale` interpolates string values. Arabic translation metadata supplies `dir="rtl"`. Use display-only FSI/PDI around the placeholder; keep raw username unchanged for API and identity logic.
- Locale outcomes: 11 accept, 1 refined (Japanese spacing), 0 holds. Placeholder, exact `Soulseek` literal, and punctuation checks pass for all 12. Native-speaker review remains required.

## Final targets

| Locale | Disposition | Confidence | Final target | Rationale |
|---|---|---|---|---|
| es | accept | high | Cargando los intereses nativos de {username} en Soulseek. | Natural Spanish status wording. Keeps the established “intereses nativos” term and places the user and Soulseek relations clearly. |
| zh-Hans | accept | high | 正在加载 {username} 的 Soulseek 原生兴趣。 | Natural progressive status sentence; 原生 expresses native/platform-provided data and the possessive order is clear. |
| hi | accept | moderate | {username} की मूल Soulseek रुचियाँ लोड हो रही हैं। | Plural रुचियाँ agrees with the progressive feminine plural verb phrase; the username-first possessive order is natural. |
| de | accept | high | Native Soulseek-Interessen von {username} werden geladen. | Clear status construction and consistent with the existing catalog’s “Native Interessen werden geladen” wording. |
| ja | refine | moderate | {username} の Soulseek ネイティブな興味・関心を読み込み中です。 | Adds spacing around the Latin product name to match Japanese catalog style while retaining the standard 興味・関心 pair and progressive status form. |
| fr | accept | moderate | Chargement des centres d’intérêt natifs de {username} sur Soulseek. | A concise French loading-state label. Centres d’intérêt is idiomatic for personal interests; natifs retains the technical distinction. |
| pt-BR | accept | high | Carregando os interesses nativos de {username} no Soulseek. | Natural Brazilian Portuguese progress wording with a clear user possessive and platform location. |
| ar | accept | moderate | جارٍ تحميل اهتمامات Soulseek الأصلية للمستخدم {username}. | Appropriate Arabic loading-state construction; للمستخدم makes the username relation clear and keeps Soulseek as an exact LTR brand token. |
| ko | accept | moderate | {username}의 Soulseek 기본 관심사를 불러오는 중입니다. | Natural polite Korean progressive form and consistent with the catalog’s existing 기본 rendering of native interests. |
| zh-Hant | accept | high | 正在載入 {username} 的 Soulseek 原生興趣。 | Natural Traditional Chinese progress wording; 原生 conveys native/platform-provided data with clear possessive order. |
| vi | accept | moderate | Đang tải các sở thích gốc của {username} trên Soulseek. | Clear Vietnamese progressive status with the username as possessor and Soulseek as the platform; gốc follows existing catalog terminology. |
| id | accept | moderate | Memuat minat Soulseek asli milik {username}. | Concise Indonesian loading-state wording. asli matches the catalog’s established rendering of native interests, and milik clearly marks the user. |

## Recommended placement

```jsx
if (interestsLoading) {
  const isolatedUsername = `\u2068${username}\u2069`;
  return (
    <span>
      <Icon loading name="spinner" />{' '}
      <LocalizedText
        source="Loading native Soulseek interests for {username}."
        values={{ username: isolatedUsername }}
      />
    </span>
  );
}
```

The isolate markers belong only to the rendered placeholder. Keep the original username for the request and state comparisons. Guard the Popup with `username && (...)`, put the loading sentence in the active `interestsLoading` branch, and return null from the later `!interests` branch. A neutral fallback translation is not required unless runtime review finds a visible transition flash.

## Packet files

- `locale-assessments.jsonl`: all 12 exact final targets, dispositions, rationales, hashes, and integrity checks.
- `code-review.json`: PR/worktree attestation, caller branches and callsites, source excerpts, interpolation/RTL behavior, null-path assessment, and code recommendation.
- `SHA256SUMS.txt`: packet integrity manifest.

No repository or PR files were modified. No tests, builds, scans, CI, browser work, workflows, releases, tags, or merges were run or performed.
