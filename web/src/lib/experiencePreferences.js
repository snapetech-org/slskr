import { readBoundedJson } from './persistedJson';
import { getLocalStorageItem } from './storage';

export const EXPERIENCE_PREFERENCES_STORAGE_KEY = 'slskr:experience-preferences:v1';

export const readExperiencePreference = (key, fallback = '') => {
  const preferences = readBoundedJson(
    getLocalStorageItem,
    EXPERIENCE_PREFERENCES_STORAGE_KEY,
    {},
    64 * 1024,
  );

  if (
    preferences === null ||
    typeof preferences !== 'object' ||
    Array.isArray(preferences)
  ) {
    return fallback;
  }

  const value = preferences[key];
  return typeof value === 'string' ? value : fallback;
};
