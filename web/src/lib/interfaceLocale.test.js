import LOCALE_0 from './locales/ui-labels.es.json';
import LOCALE_1 from './locales/ui-labels.zh-Hans.json';
import LOCALE_2 from './locales/ui-labels.hi.json';
import LOCALE_3 from './locales/ui-labels.de.json';
import LOCALE_4 from './locales/ui-labels.ja.json';
import LOCALE_5 from './locales/ui-labels.fr.json';
import LOCALE_6 from './locales/ui-labels.pt-BR.json';
import LOCALE_7 from './locales/ui-labels.ar.json';
import LOCALE_8 from './locales/ui-labels.ko.json';
import LOCALE_9 from './locales/ui-labels.zh-Hant.json';
import LOCALE_10 from './locales/ui-labels.vi.json';
import LOCALE_11 from './locales/ui-labels.id.json';
import { beforeEach, vi } from 'vitest';
import TRANSFER_BULK_ACTION_LABELS from './transfer-bulk-action-labels.json';
import {
  INTERFACE_LANGUAGE_OPTIONS,
  applyInitialInterfaceLanguage,
  interfaceTextProps,
  interfaceTextPlural,
  resetInterfaceLanguage,
  setInterfaceLanguage,
  useInterfaceLanguage,
} from './interfaceLocale';
import { parse } from '@babel/parser';
import { act, renderHook } from '@testing-library/react';
import fs from 'node:fs';
import path from 'node:path';
import { toDisplayError } from './errors';
const localeCatalogs = {
  'es': LOCALE_0,
  'zh-Hans': LOCALE_1,
  'hi': LOCALE_2,
  'de': LOCALE_3,
  'ja': LOCALE_4,
  'fr': LOCALE_5,
  'pt-BR': LOCALE_6,
  'ar': LOCALE_7,
  'ko': LOCALE_8,
  'zh-Hant': LOCALE_9,
  'vi': LOCALE_10,
  'id': LOCALE_11,
};
const UI_LABELS = Object.fromEntries(Object.keys(LOCALE_0).map((source) => [
  source, Object.values(localeCatalogs).map((locale) => locale[source]),
]));
const translationForms = (translation) => (
  typeof translation === 'string'
    ? [translation]
    : translation && typeof translation === 'object'
      ? Object.values(translation)
      : []
);
const defaultTranslation = (translation) => (
  typeof translation === 'string' ? translation : translation?.other
);

const storageKey = 'slskr.interface-language';
const bulkActionLabels = [
  'Retry All',
  'Retry All Errored',
  'Retry All Cancelled',
  'Cancel All',
  'Cancel All Queued',
  'Cancel All In Progress',
  'Remove All Succeeded',
  'Remove All Errored',
  'Remove All Cancelled',
  'Remove All Completed',
  'Filter retryable downloads',
  'Filter downloads to cancel',
  'Filter downloads to remove',
];
const originalLanguages = Object.getOwnPropertyDescriptor(navigator, 'languages');
const untranslatedTechnicalExamples = new Set([
  // These values are protocol/event examples, not app-owned prose.
  'PrivateMessageReceived&#10;DownloadFileComplete',
  'content:audio:track:mb-12345&#10;content:video:movie:imdb-tt0111161&#10;...',
]);
// The PR adds catalog coverage in these modules; untouched source modules
// remain in the broader localization audit tracked by docs/localization-roadmap.md.
const localizationAuditFiles = new Set([
  'components/App.jsx',
  'components/Browse/Directory.jsx',
  'components/Chat/Chat.jsx',
  'components/Chat/ChatSession.jsx',
  'components/Messaging/Messaging.jsx',
  'components/Messaging/PodChannelSession.jsx',
  'components/Player/Equalizer.jsx',
  'components/Player/PlayerLauncher.jsx',
  'components/Player/PlayerStatsModal.jsx',
  'components/Player/PlayerVisualTiles.jsx',
  'components/Player/PodListenAlongPanel.jsx',
  'components/Player/VisualizerOverlayControls.jsx',
  'components/Rooms/RoomSession.jsx',
  'components/Rooms/Rooms.jsx',
  'components/Shared/Footer.jsx',
  'components/Search/AlbumCompletionPanel.jsx',
  'components/Search/DiscographyCoveragePanel.jsx',
  'components/Search/DownloadActionPreviewModal.jsx',
  'components/Search/MusicBrainzLookup.jsx',
  'components/Search/Searches.jsx',
  'components/Search/SongIDPanel.jsx',
  'components/System/Integrations/LidarrPanel.jsx',
  'components/System/LibraryHealth/index.jsx',
  'components/System/MediaCore/ContentDescriptorRetrievalPanel.jsx',
  'components/System/MediaCore/MediaCoreStatisticsDashboardPanel.jsx',
  'components/System/MediaCore/MessageSearchPanel.jsx',
  'components/System/MediaCore/PodChannelManagementPanel.jsx',
  'components/System/MediaCore/PodContentLinkingPanel.jsx',
  'components/System/MediaCore/PodDiscoveryPanel.jsx',
  'components/System/MediaCore/PodMembershipManagementPanel.jsx',
  'components/System/MediaCore/PodMessageBackfillPanel.jsx',
  'components/System/MediaCore/PodMessageMaintenanceActions.jsx',
  'components/System/MediaCore/PodMessageRoutingPanel.jsx',
  'components/System/MediaCore/PodMessageStoragePanel.jsx',
  'components/System/MediaCore/PodOpinionsPanel.jsx',
  'components/System/Mesh/MeshEvidencePolicy.jsx',
  'components/System/Network/index.jsx',
  'components/System/SwarmAnalytics/index.jsx',
  'components/Transfers/Transfers.jsx',
]);

const localizationSourceReferences = () => {
  const sourceRoot = path.resolve(process.cwd(), 'src');
  const files = [];
  const visitDirectory = (directory) => {
    for (const entry of fs.readdirSync(directory, { withFileTypes: true })) {
      const fullPath = path.join(directory, entry.name);
      if (entry.isDirectory()) {
        visitDirectory(fullPath);
      } else if (/\.(?:js|jsx)$/.test(entry.name) && !entry.name.includes('.test.')) {
        files.push(fullPath);
      }
    }
  };
  visitDirectory(sourceRoot);

  const references = [];
  const collectStaticTexts = (node) => {
    if (!node) return [];
    if (node.type === 'StringLiteral') return [node.value];
    if (node.type === 'TemplateLiteral' && node.expressions.length === 0) {
      return [node.quasis[0]?.value.cooked || ''];
    }
    if (node.type === 'ConditionalExpression') {
      return [...collectStaticTexts(node.consequent), ...collectStaticTexts(node.alternate)];
    }
    if (node.type === 'LogicalExpression') return collectStaticTexts(node.right);
    if (node.type === 'ParenthesizedExpression' || node.type === 'TSAsExpression') {
      return collectStaticTexts(node.expression);
    }
    return [];
  };
  for (const file of files) {
    const source = fs.readFileSync(file, 'utf8');
    const ast = parse(source, { sourceType: 'unambiguous', plugins: ['jsx'] });
    const relativeFile = path.relative(sourceRoot, file);
    const sourceValues = new Map();
    const visitSourceValues = (node) => {
      if (!node || typeof node !== 'object') return;
      if (node.type === 'FunctionDeclaration' && node.id?.name) {
        const returned = [];
        const visitFunctionBody = (child, isRoot = false) => {
          if (!child || typeof child !== 'object') return;
          if (!isRoot && ['FunctionDeclaration', 'FunctionExpression', 'ArrowFunctionExpression'].includes(child.type)) return;
          if (child.type === 'ReturnStatement') returned.push(...collectStaticTexts(child.argument));
          for (const value of Object.values(child)) {
            if (Array.isArray(value)) value.forEach((item) => visitFunctionBody(item));
            else if (value && typeof value === 'object') visitFunctionBody(value);
          }
        };
        visitFunctionBody(node.body, true);
        sourceValues.set(node.id.name, returned);
      }
      if (node.type === 'VariableDeclarator' && node.id.type === 'Identifier' && node.init) {
        if (['ArrowFunctionExpression', 'FunctionExpression'].includes(node.init.type)) {
          const returned = node.init.body.type === 'BlockStatement'
            ? []
            : collectStaticTexts(node.init.body);
          if (node.init.body.type === 'BlockStatement') {
            const visitFunctionBody = (child, isRoot = false) => {
              if (!child || typeof child !== 'object') return;
              if (!isRoot && ['FunctionDeclaration', 'FunctionExpression', 'ArrowFunctionExpression'].includes(child.type)) return;
              if (child.type === 'ReturnStatement') returned.push(...collectStaticTexts(child.argument));
              for (const value of Object.values(child)) {
                if (Array.isArray(value)) value.forEach((item) => visitFunctionBody(item));
                else if (value && typeof value === 'object') visitFunctionBody(value);
              }
            };
            visitFunctionBody(node.init.body, true);
          }
          sourceValues.set(node.id.name, returned);
        } else {
          const values = collectStaticTexts(node.init);
          if (values.length) sourceValues.set(node.id.name, values);
        }
      }
      for (const [key, value] of Object.entries(node)) {
        if (['loc', 'start', 'end', 'leadingComments', 'trailingComments', 'innerComments'].includes(key)) continue;
        if (Array.isArray(value)) value.forEach(visitSourceValues);
        else if (value && typeof value === 'object') visitSourceValues(value);
      }
    };
    visitSourceValues(ast);
    const collectLocalizedSourceTexts = (node) => {
      const staticTexts = collectStaticTexts(node);
      if (staticTexts.length) return staticTexts;
      if (node?.type === 'Identifier') return sourceValues.get(node.name) || [];
      if (node?.type === 'CallExpression' && node.callee.type === 'Identifier') return sourceValues.get(node.callee.name) || [];
      return [];
    };
    const walk = (node) => {
      if (!node || typeof node !== 'object') return;

      if (
        node.type === 'VariableDeclarator' &&
        node.id.type === 'Identifier' &&
        node.id.name === 'toDisplayError' &&
        node.init?.params?.[1]?.type === 'AssignmentPattern'
      ) {
        for (const text of collectStaticTexts(node.init.params[1].right)) {
          if (text) references.push({ file: relativeFile, line: node.init.params[1].loc.start.line, source: text });
        }
      }

      if (
        node.type === 'CallExpression' &&
        node.callee.type === 'Identifier' &&
        ['interfaceText', 'interfaceTextProps', 'interfaceTextPlural', 't', 'tp'].includes(node.callee.name)
      ) {
        const sourceArgumentCount = ['interfaceTextPlural', 'tp'].includes(node.callee.name) ? 2 : 1;
        for (const argument of node.arguments.slice(0, sourceArgumentCount)) {
          for (const text of collectStaticTexts(argument)) {
            if (text) references.push({ file: relativeFile, line: node.loc.start.line, source: text });
          }
        }
      }

      if (
        node.type === 'CallExpression' &&
        node.callee.type === 'Identifier' &&
        node.callee.name === 'toDisplayError' &&
        node.arguments[1]
      ) {
        for (const text of collectStaticTexts(node.arguments[1])) {
          if (text) references.push({ file: relativeFile, line: node.loc.start.line, source: text });
        }
      }

      if (node.type === 'JSXOpeningElement') {
        const componentName = node.name.name;
        const attributesByComponent = {
          LocalizedText: ['source'],
          LocalizedPopup: ['content'],
          LocalizedPluralText: ['singular', 'other'],
          TooltipButton: ['aria-label', 'title', 'content', 'tooltip'],
        };
        for (const attribute of node.attributes) {
          if (
            attribute.type !== 'JSXAttribute' ||
            !attributesByComponent[componentName]?.includes(attribute.name.name)
          ) continue;
          const valueNode = attribute.value?.type === 'JSXExpressionContainer'
            ? attribute.value.expression
            : attribute.value?.type === 'StringLiteral'
              ? { type: 'StringLiteral', value: attribute.value.value }
              : undefined;
          for (const text of collectLocalizedSourceTexts(valueNode)) {
            if (text) references.push({ file: relativeFile, line: attribute.loc.start.line, source: text });
          }
        }
      }

      for (const [key, value] of Object.entries(node)) {
        if (['loc', 'start', 'end', 'leadingComments', 'trailingComments', 'innerComments'].includes(key)) continue;
        if (Array.isArray(value)) value.forEach(walk);
        else if (value && typeof value === 'object') walk(value);
      }
    };
    walk(ast);
  }

  return references;
};

beforeEach(() => {
  vi.stubGlobal('fetch', vi.fn(async (url) => {
    const language = String(url).match(/ui-labels\.([^.]+)\.json/)?.[1];
    const locale = localeCatalogs[language];
    return { ok: Boolean(locale), status: locale ? 200 : 404, json: async () => locale };
  }));
});

afterEach(() => {
  act(() => resetInterfaceLanguage());
  vi.unstubAllGlobals();
  if (originalLanguages) {
    Object.defineProperty(navigator, 'languages', originalLanguages);
  }
});

describe('interface language', () => {
  it('offers only locales with completed interface support', () => {
    expect(INTERFACE_LANGUAGE_OPTIONS.map((option) => option.value)).toEqual([
      'en',
      'es',
      'zh-Hans',
      'hi',
      'de',
      'ja',
      'fr',
      'pt-BR',
      'ar',
      'ko',
      'zh-Hant',
      'vi',
      'id',
    ]);

    for (const [source, translations] of Object.entries(UI_LABELS)) {
      expect(translations).toHaveLength(INTERFACE_LANGUAGE_OPTIONS.length - 1);
      expect(translations.every((value) => (
        value === null || typeof value === 'string' ||
        (value && typeof value === 'object' && !Array.isArray(value) && typeof value.other === 'string')
      ))).toBe(true);
    }
  });

  it('keeps locale catalogs in key and placeholder parity with the source catalog', () => {
    const sourceKeys = Object.keys(LOCALE_0).sort();
    const placeholders = (text) => [...text.matchAll(/\{([a-zA-Z][a-zA-Z0-9_]*)\}/g)]
      .map((match) => match[1])
      .sort();

    for (const [language, catalog] of Object.entries(localeCatalogs)) {
      expect(Object.keys(catalog).sort(), `${language} catalog keys`).toEqual(sourceKeys);

      for (const [source, translation] of Object.entries(catalog)) {
        for (const form of translationForms(translation)) {
          expect(placeholders(form), `${language}: ${source}`).toEqual(placeholders(source));
        }
      }
    }
  });

  it('uses oscilloscope terminology and distinguishes Chinese DHT peers from nodes', () => {
    const expectedScopes = {
      es: 'osciloscopio',
      'zh-Hans': '示波器',
      hi: 'ऑसिलोस्कोप',
      de: 'Oszilloskop',
      ja: 'オシロスコープ',
      fr: 'oscilloscope',
      'pt-BR': 'osciloscópio',
      ar: 'راسم الإشارة',
      ko: '오실로스코프',
      'zh-Hant': '示波器',
      vi: 'máy hiện sóng',
      id: 'osiloskop',
    };
    const dhtSummary = 'DHT peers: {dhtPeers}; DHT nodes: {dhtNodes}; mesh peers: {meshPeers}; hashes: {hashes}; seq: {seq}{errors}';

    for (const [language, expected] of Object.entries(expectedScopes)) {
      const catalog = localeCatalogs[language];
      expect(catalog['signal scope']).toBe(expected);
      expect(catalog['Show signal scope in this box.']).not.toMatch(/signal range|信号范围|訊號範圍|نطاق الإشارة|phạm vi tín hiệu|cakupan sinyal/iu);
    }
    expect(localeCatalogs['zh-Hans'][dhtSummary]).toContain('DHT 对等端: {dhtPeers}; DHT 节点: {dhtNodes}');
    expect(localeCatalogs['zh-Hant'][dhtSummary]).toContain('DHT 對等端: {dhtPeers}; DHT 節點: {dhtNodes}');
    expect(localeCatalogs['zh-Hant']['Message {channel}']).toBe('傳送訊息到頻道 {channel}');
  });

  it('keeps static app-owned localization callsites in every locale catalog', () => {
    const sourceKeys = new Set(Object.keys(LOCALE_0));
    const missing = localizationSourceReferences()
      .filter(({ file, source }) => (
        localizationAuditFiles.has(file) &&
        !sourceKeys.has(source) &&
        !untranslatedTechnicalExamples.has(source)
      ))
      .map(({ file, line, source }) => `${file}:${line}: ${JSON.stringify(source)}`);

    expect(missing).toEqual([]);
  });

  it('translates transfer actions and filter names in every supported language', () => {
    for (const source of bulkActionLabels) {
      expect(TRANSFER_BULK_ACTION_LABELS[source]).toHaveLength(INTERFACE_LANGUAGE_OPTIONS.length - 1);
      expect(TRANSFER_BULK_ACTION_LABELS[source].every((translation) => typeof translation === 'string')).toBe(true);
    }
  });

  it('translates supported interface strings without changing the mostly-English page language or direction', async () => {
    const { result } = renderHook(() => useInterfaceLanguage());

    for (const option of INTERFACE_LANGUAGE_OPTIONS) {
      await act(async () => { await result.current.setLanguage(option.value); });
      const translationIndex = INTERFACE_LANGUAGE_OPTIONS.slice(1).findIndex(
        (item) => item.value === option.value,
      );

      expect(result.current.language).toBe(option.value);
      for (const [source, translations] of Object.entries(UI_LABELS)) {
        const translation = option.value === 'en' ? null : translations[translationIndex];
        const translatedText = defaultTranslation(translation);
        const localizedLanguage = translatedText && translatedText !== source ? option.value : 'en';
        expect(result.current.t(source)).toBe(translatedText || source);
        expect(result.current.languageFor(source)).toBe(localizedLanguage);
        expect(result.current.directionFor(source)).toBe(
          localizedLanguage === 'ar' ? 'rtl' : 'ltr',
        );
      }
      expect(document.documentElement.lang).toBe('en');
      expect(document.documentElement.dir).toBe('ltr');
      expect(localStorage.getItem(storageKey)).toBe(option.value);
    }
  });

  it('keeps English text for keys that have not been translated', async () => {
    const { result } = renderHook(() => useInterfaceLanguage());

    await act(async () => { await setInterfaceLanguage('es'); });

    expect(result.current.t('A future screen label')).toBe(
      'A future screen label',
    );
    expect(result.current.languageFor('A future screen label')).toBe('en');
    expect(result.current.directionFor('A future screen label')).toBe('ltr');

    await act(async () => { await setInterfaceLanguage('ar'); });
    expect(result.current.languageFor('Search')).toBe('ar');
    expect(result.current.directionFor('Search')).toBe('rtl');
  });

  it('uses Arabic plural categories for visible counts', async () => {
    const arabicPluralSources = [
      'Failed to {action} {count} transfers. First error: {label}: {message}',
      'Last {count} hours',
      '{count} Selected Issues',
      'Lidarr import retry queued: {count} files',
      '{count} files',
      '{count} swarms',
      'swarms',
      'fingerprint matches',
      'Added {count} missing tracks to Wishlist',
      '· {count} verified matches',
      'Cleared {count} searches',
      'Copied {format} export for {count} plays.',
      'Prepared {format} export for {count} plays; clipboard is unavailable.',
    ];
    const requiredCategories = ['zero', 'one', 'two', 'few', 'many', 'other'].sort();
    await act(async () => { await setInterfaceLanguage('ar'); });

    for (const source of arabicPluralSources) {
      expect(Object.keys(LOCALE_7[source] || {}).sort()).toEqual(requiredCategories);
    }

    const cases = [
      [0, '0 ملف'],
      [1, '1 ملف'],
      [2, '2 ملفان'],
      [3, '3 ملفات'],
      [11, '11 ملفًا'],
      [100, '100 ملف'],
    ];

    for (const [count, expected] of cases) {
      expect(interfaceTextPlural('{count} file', '{count} files', count)).toBe(expected);
    }
  });

  it('localizes only the fixed error fallback and preserves server error detail', async () => {
    await act(async () => { await setInterfaceLanguage('es'); });

    expect(toDisplayError(null, 'Failed to load saved conversations'))
      .toBe('No se pudieron cargar las conversaciones guardadas');
    expect(toDisplayError({ response: { data: { message: 'raw backend message' } } }, 'Failed to load saved conversations'))
      .toBe('raw backend message');
  });

  it('keeps same-as-source values tagged as English and left-to-right', async () => {
    await act(async () => { await setInterfaceLanguage('ar'); });

    expect(interfaceTextProps('slskr')).toMatchObject({
      dir: 'ltr',
      lang: 'en',
      'aria-label': 'slskr',
      title: 'slskr',
    });
  });

  it('uses the browser language on first use and a saved choice afterward', async () => {
    Object.defineProperty(navigator, 'languages', {
      configurable: true,
      value: ['fr-CA', 'en-US'],
    });
    localStorage.removeItem(storageKey);
    await act(async () => { await applyInitialInterfaceLanguage(); });

    const { result, unmount } = renderHook(() => useInterfaceLanguage());
    expect(result.current.language).toBe('fr');
    expect(document.documentElement.lang).toBe('en');

    localStorage.setItem(storageKey, 'de');
    await act(async () => { await applyInitialInterfaceLanguage(); });
    unmount();

    const restored = renderHook(() => useInterfaceLanguage());
    expect(restored.result.current.language).toBe('de');
  });

  it('resets the saved language to the browser preference', async () => {
    Object.defineProperty(navigator, 'languages', {
      configurable: true,
      value: ['fr-CA', 'en-US'],
    });
    const { result } = renderHook(() => useInterfaceLanguage());
    await act(async () => { await setInterfaceLanguage('de'); });

    let removed;
    act(() => { removed = resetInterfaceLanguage(); });

    expect(removed).toBe(true);
    expect(result.current.language).toBe('fr');
    expect(localStorage.getItem(storageKey)).toBeNull();
    expect(document.documentElement.lang).toBe('en');
    expect(document.documentElement.dir).toBe('ltr');
  });
});
