import React, { useCallback, useSyncExternalStore } from 'react';
import localeUrl0 from './locales/ui-labels.es.json?url';
import localeUrl1 from './locales/ui-labels.zh-Hans.json?url';
import localeUrl2 from './locales/ui-labels.hi.json?url';
import localeUrl3 from './locales/ui-labels.de.json?url';
import localeUrl4 from './locales/ui-labels.ja.json?url';
import localeUrl5 from './locales/ui-labels.fr.json?url';
import localeUrl6 from './locales/ui-labels.pt-BR.json?url';
import localeUrl7 from './locales/ui-labels.ar.json?url';
import localeUrl8 from './locales/ui-labels.ko.json?url';
import localeUrl9 from './locales/ui-labels.zh-Hant.json?url';
import localeUrl10 from './locales/ui-labels.vi.json?url';
import localeUrl11 from './locales/ui-labels.id.json?url';
import { urlBase } from '../config';

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
const localeAssetUrls = {
  es: localeUrl0,
  'zh-Hans': localeUrl1,
  hi: localeUrl2,
  de: localeUrl3,
  ja: localeUrl4,
  fr: localeUrl5,
  'pt-BR': localeUrl6,
  ar: localeUrl7,
  ko: localeUrl8,
  'zh-Hant': localeUrl9,
  vi: localeUrl10,
  id: localeUrl11,
};
const listeners = new Set();
const localeCatalogs = new Map();
const pendingCatalogs = new Map();
let catalogRevision = 0;
let activeLanguage;
let languageRequest = 0;

const notify = () => listeners.forEach((listener) => listener());
const translationFor = (source, language) => localeCatalogs.get(language)?.[source];

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

export const getInterfaceLanguageIndex = (language) => {
  const index = INTERFACE_LANGUAGE_OPTIONS.slice(1).findIndex((option) => option.value === language);
  return index < 0 ? undefined : index;
};

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

const resolveLocaleUrl = (assetUrl) => {
  if (assetUrl.startsWith('/')) return assetUrl;
  if (typeof window === 'undefined') return assetUrl;
  const basePath = String(urlBase || '') + '/';
  return new URL(assetUrl, window.location.origin + basePath).toString();
};

const loadCatalog = (language) => {
  if (localeCatalogs.has(language)) return Promise.resolve(localeCatalogs.get(language));
  if (pendingCatalogs.has(language)) return pendingCatalogs.get(language);
  const assetUrl = localeAssetUrls[language];
  if (!assetUrl) return Promise.resolve(null);

  const request = (async () => {
    try {
      const response = await fetch(resolveLocaleUrl(assetUrl), { credentials: 'same-origin' });
      if (!response.ok) throw new Error('Locale catalog request failed: ' + response.status);
      const catalog = await response.json();
      if (!catalog || typeof catalog !== 'object' || Array.isArray(catalog)) {
        throw new Error('Locale catalog response must be an object');
      }
      localeCatalogs.set(language, catalog);
      return catalog;
    } finally {
      pendingCatalogs.delete(language);
    }
  })();
  pendingCatalogs.set(language, request);
  return request;
};

const loadSelectedCatalog = (language) => {
  const request = ++languageRequest;
  if (language === 'en') return Promise.resolve();
  return loadCatalog(language).then(
    () => {
      if (request === languageRequest && activeLanguage === language) {
        catalogRevision += 1;
        notify();
      }
    },
    () => {
      if (request === languageRequest && activeLanguage === language) {
        catalogRevision += 1;
        notify();
      }
    },
  );
};

const subscribe = (listener) => {
  listeners.add(listener);
  return () => listeners.delete(listener);
};
const snapshot = () => String(activeLanguage) + ':' + catalogRevision;

activeLanguage = readLanguage();

if (typeof window !== 'undefined') {
  window.addEventListener('storage', (event) => {
    if (event.key !== STORAGE_KEY && event.key !== null) return;
    activeLanguage = readLanguage();
    applyDocumentLanguage();
    notify();
    void loadSelectedCatalog(activeLanguage);
  });
}

export const applyInitialInterfaceLanguage = () => {
  activeLanguage = readLanguage();
  applyDocumentLanguage();
  notify();
  return loadSelectedCatalog(activeLanguage);
};

export const setInterfaceLanguage = (language) => {
  if (!supportedLanguages.has(language)) return Promise.resolve();
  activeLanguage = language;
  try { localStorage.setItem(STORAGE_KEY, language); } catch { /* Keep this tab usable without browser storage. */ }
  applyDocumentLanguage();
  notify();
  return loadSelectedCatalog(language);
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
  void loadSelectedCatalog(activeLanguage);
  return removed;
};

export const useInterfaceLanguage = () => {
  const state = useSyncExternalStore(subscribe, snapshot, () => 'en:0');
  const [language, revision] = state.split(':');
  const t = useCallback((source, parameters = {}) => {
    const translated = translationFor(source, language) || source;
    return translated.replace(/\{([a-zA-Z][a-zA-Z0-9_]*)\}/g, (placeholder, name) => {
      const value = parameters[name];
      return typeof value === 'string' || typeof value === 'number'
        ? String(value)
        : placeholder;
    });
  }, [language, revision]);
  const languageFor = useCallback(
    (source) => translationFor(source, language) ? language : 'en',
    [language, revision],
  );
  const directionFor = useCallback((source) => languageFor(source) === 'ar' ? 'rtl' : 'ltr', [languageFor]);
  return { language, setLanguage: setInterfaceLanguage, t, languageFor, directionFor };
};
