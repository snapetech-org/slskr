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
  resetInterfaceLanguage,
  setInterfaceLanguage,
  useInterfaceLanguage,
} from './interfaceLocale';
import { act, renderHook } from '@testing-library/react';
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
      expect(translations.every((value) => value === null || typeof value === 'string')).toBe(true);
    }
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
        const localizedLanguage = translation ? option.value : 'en';
        expect(result.current.t(source)).toBe(translation || source);
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
