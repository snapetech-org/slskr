import {
  EXPERIENCE_PREFERENCES_STORAGE_KEY,
  readExperiencePreference,
} from './experiencePreferences';
import { getRegionalLocale } from './regionalFormat';
import { beforeEach, describe, expect, it } from 'vitest';

describe('regional format preferences', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it('uses the browser locale when the preference is unset or system', () => {
    expect(getRegionalLocale()).toBeUndefined();

    localStorage.setItem(
      EXPERIENCE_PREFERENCES_STORAGE_KEY,
      JSON.stringify({ regionalFormat: 'system' }),
    );

    expect(getRegionalLocale()).toBeUndefined();
  });

  it('uses a supported saved locale', () => {
    localStorage.setItem(
      EXPERIENCE_PREFERENCES_STORAGE_KEY,
      JSON.stringify({ regionalFormat: 'de' }),
    );

    expect(getRegionalLocale()).toBe('de');
  });

  it('falls back safely for malformed, oversized, and unsupported values', () => {
    localStorage.setItem(EXPERIENCE_PREFERENCES_STORAGE_KEY, 'not-json');
    expect(getRegionalLocale()).toBeUndefined();

    localStorage.setItem(
      EXPERIENCE_PREFERENCES_STORAGE_KEY,
      'x'.repeat(64 * 1024 + 1),
    );
    expect(getRegionalLocale()).toBeUndefined();

    localStorage.setItem(
      EXPERIENCE_PREFERENCES_STORAGE_KEY,
      JSON.stringify({ regionalFormat: 'unsupported-locale' }),
    );
    expect(getRegionalLocale()).toBeUndefined();
  });

  it('uses the fallback when a preference is missing or not a string', () => {
    localStorage.setItem(
      EXPERIENCE_PREFERENCES_STORAGE_KEY,
      JSON.stringify({ regionalFormat: 17 }),
    );

    expect(readExperiencePreference('regionalFormat', 'system')).toBe('system');
    expect(readExperiencePreference('missingPreference', 'fallback')).toBe('fallback');
  });
});
