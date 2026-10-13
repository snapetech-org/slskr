import UI_LABELS from './ui-labels.json';
import TRANSFER_BULK_ACTION_LABELS from './transfer-bulk-action-labels.json';
import {
  INTERFACE_LANGUAGE_OPTIONS,
  applyInitialInterfaceLanguage,
  resetInterfaceLanguage,
  setInterfaceLanguage,
  useInterfaceLanguage,
} from './interfaceLocale';
import { act, renderHook } from '@testing-library/react';

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
];
const originalLanguages = Object.getOwnPropertyDescriptor(navigator, 'languages');

afterEach(() => {
  act(() => resetInterfaceLanguage());
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

  it('translates each bulk action as a complete phrase in every supported language', () => {
    for (const source of bulkActionLabels) {
      expect(TRANSFER_BULK_ACTION_LABELS[source]).toHaveLength(INTERFACE_LANGUAGE_OPTIONS.length - 1);
      expect(TRANSFER_BULK_ACTION_LABELS[source].every((translation) => typeof translation === 'string')).toBe(true);
    }
  });

  it('translates supported interface strings without changing the mostly-English page language or direction', () => {
    const { result } = renderHook(() => useInterfaceLanguage());

    for (const option of INTERFACE_LANGUAGE_OPTIONS) {
      act(() => result.current.setLanguage(option.value));
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

  it('keeps English text for keys that have not been translated', () => {
    const { result } = renderHook(() => useInterfaceLanguage());

    act(() => setInterfaceLanguage('es'));

    expect(result.current.t('A future screen label')).toBe(
      'A future screen label',
    );
    expect(result.current.languageFor('A future screen label')).toBe('en');
    expect(result.current.directionFor('A future screen label')).toBe('ltr');

    act(() => setInterfaceLanguage('ar'));
    expect(result.current.languageFor('Search')).toBe('ar');
    expect(result.current.directionFor('Search')).toBe('rtl');
  });

  it('uses the browser language on first use and a saved choice afterward', () => {
    Object.defineProperty(navigator, 'languages', {
      configurable: true,
      value: ['fr-CA', 'en-US'],
    });
    localStorage.removeItem(storageKey);
    applyInitialInterfaceLanguage();

    const { result, unmount } = renderHook(() => useInterfaceLanguage());
    expect(result.current.language).toBe('fr');
    expect(document.documentElement.lang).toBe('en');

    localStorage.setItem(storageKey, 'de');
    applyInitialInterfaceLanguage();
    unmount();

    const restored = renderHook(() => useInterfaceLanguage());
    expect(restored.result.current.language).toBe('de');
  });

  it('resets the saved language to the browser preference', () => {
    Object.defineProperty(navigator, 'languages', {
      configurable: true,
      value: ['fr-CA', 'en-US'],
    });
    const { result } = renderHook(() => useInterfaceLanguage());
    act(() => setInterfaceLanguage('de'));

    let removed;
    act(() => { removed = resetInterfaceLanguage(); });

    expect(removed).toBe(true);
    expect(result.current.language).toBe('fr');
    expect(localStorage.getItem(storageKey)).toBeNull();
    expect(document.documentElement.lang).toBe('en');
    expect(document.documentElement.dir).toBe('ltr');
  });
});
