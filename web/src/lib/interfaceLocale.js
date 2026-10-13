import React, { useCallback, useSyncExternalStore } from 'react';
import UI_LABELS from './ui-labels.json';

export const INTERFACE_LANGUAGE_OPTIONS = [
  { key: 'en', text: 'English', value: 'en' },
  { key: 'es', text: 'Español — Spanish', value: 'es' },
  { key: 'zh-Hans', text: '简体中文 — Simplified Chinese', value: 'zh-Hans' },
  { key: 'hi', text: 'हिन्दी — Hindi', value: 'hi' },
  { key: 'de', text: 'Deutsch — German', value: 'de' },
  { key: 'ja', text: '日本語 — Japanese', value: 'ja' },
  { key: 'fr', text: 'Français — French', value: 'fr' },
  { key: 'pt-BR', text: 'Português (Brasil) — Brazilian Portuguese', value: 'pt-BR' },
  { key: 'ar', text: 'العربية — Arabic', value: 'ar' },
  { key: 'ko', text: '한국어 — Korean', value: 'ko' },
  { key: 'zh-Hant', text: '繁體中文 — Traditional Chinese', value: 'zh-Hant' },
  { key: 'vi', text: 'Tiếng Việt — Vietnamese', value: 'vi' },
  { key: 'id', text: 'Bahasa Indonesia — Indonesian', value: 'id' },
];

const STORAGE_KEY = 'slskr.interface-language';
const supportedLanguages = new Set(INTERFACE_LANGUAGE_OPTIONS.map((option) => option.value));
// Catalog arrays follow this order: INTERFACE_LANGUAGE_OPTIONS without English.
const translatedLanguages = new Map(
  INTERFACE_LANGUAGE_OPTIONS.slice(1).map(({ value }, index) => [value, index]),
);
const listeners = new Set();

const translationFor = (source, language) => {
  const index = translatedLanguages.get(language);
  return index === undefined ? undefined : UI_LABELS[source]?.[index];
};

const formatInterfaceText = (source, parameters = {}) => {
  if (typeof source !== 'string') return source;
  const translated = translationFor(source, activeLanguage) || source;
  return translated.replace(/\{([a-zA-Z][a-zA-Z0-9_]*)\}/g, (placeholder, name) => {
    const value = parameters?.[name];
    return typeof value === 'string' || typeof value === 'number'
      ? String(value)
      : placeholder;
  });
};

export const interfaceText = (source, parameters = {}) =>
  formatInterfaceText(source, parameters);

export const interfaceTextProps = (source, parameters = {}) => {
  const translated = translationFor(source, activeLanguage);
  const text = formatInterfaceText(source, parameters);
  const unresolved = typeof text === 'string' && /\{[a-zA-Z][a-zA-Z0-9_]*\}/.test(text);
  const props = {
    dir: translated && activeLanguage === 'ar' ? 'rtl' : 'ltr',
    lang: translated ? activeLanguage : 'en',
  };
  if (!unresolved) {
    props['aria-label'] = text;
    props.title = text;
  }
  if (parameters && Object.keys(parameters).length > 0) props.parameters = parameters;
  return props;
};

export const getInterfaceLanguageIndex = (language) => translatedLanguages.get(language);

const browserLanguage = () => {
  if (typeof navigator === 'undefined') return 'en';
  const candidates = navigator.languages?.length ? navigator.languages : [navigator.language];
  for (const candidate of candidates) {
    const normalized = candidate.toLowerCase();
    const base = normalized.split(/[-_]/)[0];
    if (base === 'zh') return /(?:hant|tw|hk|mo)/.test(normalized) ? 'zh-Hant' : 'zh-Hans';
    if (base === 'pt') return 'pt-BR';
    if (supportedLanguages.has(base)) return base;
  }
  return 'en';
};

const readLanguage = () => {
  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    return supportedLanguages.has(stored) ? stored : browserLanguage();
  } catch {
    return browserLanguage();
  }
};

const applyDocumentLanguage = () => {
  if (typeof document === 'undefined') return;
  // Most screens remain English. Translated navigation, preference, and
  // transfer labels carry their own language and direction metadata.
  document.documentElement.lang = 'en';
  document.documentElement.dir = 'ltr';
};

let activeLanguage = readLanguage();
const notify = () => listeners.forEach((listener) => listener());

if (typeof window !== 'undefined') {
  window.addEventListener('storage', (event) => {
    if (event.key !== STORAGE_KEY && event.key !== null) return;
    activeLanguage = readLanguage();
    applyDocumentLanguage(activeLanguage);
    notify();
  });
}

export const applyInitialInterfaceLanguage = () => {
  activeLanguage = readLanguage();
  applyDocumentLanguage(activeLanguage);
};

export const setInterfaceLanguage = (language) => {
  if (!supportedLanguages.has(language)) return;
  activeLanguage = language;
  try { localStorage.setItem(STORAGE_KEY, language); } catch { /* Keep this tab usable without browser storage. */ }
  applyDocumentLanguage(language);
  notify();
};

export const resetInterfaceLanguage = () => {
  let removed = true;
  try {
    localStorage.removeItem(STORAGE_KEY);
  } catch {
    removed = false;
  }
  activeLanguage = browserLanguage();
  applyDocumentLanguage();
  notify();
  return removed;
};

export const useInterfaceLanguage = () => {
  const language = useSyncExternalStore(
    (listener) => { listeners.add(listener); return () => listeners.delete(listener); },
    () => activeLanguage,
    () => 'en',
  );
  const t = useCallback((source, parameters = {}) => {
    const translated = translationFor(source, language) || source;
    return translated.replace(/\{([a-zA-Z][a-zA-Z0-9_]*)\}/g, (placeholder, name) => {
      const value = parameters[name];
      return typeof value === 'string' || typeof value === 'number'
        ? String(value)
        : placeholder;
    });
  }, [language]);
  const languageFor = useCallback((source) => translationFor(source, language) ? language : 'en', [language]);
  const directionFor = useCallback((source) => languageFor(source) === 'ar' ? 'rtl' : 'ltr', [languageFor]);
  return { language, setLanguage: setInterfaceLanguage, t, languageFor, directionFor };
};
