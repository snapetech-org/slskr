import UI_LABELS from './ui-labels.json';
import {
  INTERFACE_LANGUAGE_OPTIONS,
  applyInitialInterfaceLanguage,
  setInterfaceLanguage,
  useInterfaceLanguage,
} from './interfaceLocale';
import { act, renderHook } from '@testing-library/react';

const storageKey = 'slskr.interface-language';
const originalLanguages = Object.getOwnPropertyDescriptor(navigator, 'languages');

afterEach(() => {
  act(() => setInterfaceLanguage('en'));
  localStorage.removeItem(storageKey);
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
      'ko',
      'zh-Hant',
      'vi',
      'id',
    ]);

    for (const [source, translations] of Object.entries(UI_LABELS)) {
      for (const { value } of INTERFACE_LANGUAGE_OPTIONS.slice(1)) {
        expect(translations[value], `${source} (${value})`).toBeTruthy();
      }
    }
  });

  it('translates supported interface strings and sets document language and direction', () => {
    const { result } = renderHook(() => useInterfaceLanguage());

    for (const option of INTERFACE_LANGUAGE_OPTIONS) {
      act(() => result.current.setLanguage(option.value));

      expect(result.current.language).toBe(option.value);
      expect(result.current.t('Search')).toBe(
        option.value === 'en' ? 'Search' : UI_LABELS.Search[option.value],
      );
      expect(document.documentElement.lang).toBe(option.value);
      expect(document.documentElement.dir).toBe(
        option.value === 'ar' ? 'rtl' : 'ltr',
      );
      expect(localStorage.getItem(storageKey)).toBe(option.value);
    }
  });

  it('keeps English text for keys that have not been translated', () => {
    const { result } = renderHook(() => useInterfaceLanguage());

    act(() => setInterfaceLanguage('es'));

    expect(result.current.t('A future screen label')).toBe(
      'A future screen label',
    );
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
    expect(document.documentElement.lang).toBe('fr');

    localStorage.setItem(storageKey, 'de');
    applyInitialInterfaceLanguage();
    unmount();

    const restored = renderHook(() => useInterfaceLanguage());
    expect(restored.result.current.language).toBe('de');
  });
});
