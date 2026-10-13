import { REGIONAL_FORMAT_OPTIONS } from './regionalFormat';
import {
  EXPERIENCE_PREFERENCES_STORAGE_KEY,
  formatRegionalCompactDateTime,
  formatRegionalDate,
  formatRegionalDateTime,
  formatRegionalNumber,
  formatRegionalTime,
  getRegionalLocale,
} from './util';
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

  it('ignores non-object preference data and non-string settings', () => {
    localStorage.setItem(EXPERIENCE_PREFERENCES_STORAGE_KEY, JSON.stringify(['de']));
    expect(getRegionalLocale()).toBeUndefined();

    localStorage.setItem(
      EXPERIENCE_PREFERENCES_STORAGE_KEY,
      JSON.stringify({ regionalFormat: 17 }),
    );
    expect(getRegionalLocale()).toBeUndefined();
  });
  it('formats numbers and dates with the selected locale', () => {
    localStorage.setItem(
      EXPERIENCE_PREFERENCES_STORAGE_KEY,
      JSON.stringify({ regionalFormat: 'de' }),
    );
    const timestamp = '2026-01-02T15:04:05Z';
    const date = new Date(timestamp);

    expect(formatRegionalNumber(1234567.89)).toBe(
      (1234567.89).toLocaleString('de'),
    );
    expect(formatRegionalDateTime(timestamp)).toBe(date.toLocaleString('de'));
    expect(formatRegionalDate(timestamp)).toBe(date.toLocaleDateString('de'));
    expect(formatRegionalTime(timestamp)).toBe(date.toLocaleTimeString('de'));
    expect(formatRegionalCompactDateTime(date)).toBe(
      new Intl.DateTimeFormat('de', {
        day: 'numeric',
        hour: 'numeric',
        minute: '2-digit',
        month: 'numeric',
      }).format(date),
    );
  });

  it('accepts each listed locale option', () => {
    for (const { value } of REGIONAL_FORMAT_OPTIONS) {
      localStorage.setItem(
        EXPERIENCE_PREFERENCES_STORAGE_KEY,
        JSON.stringify({ regionalFormat: value }),
      );
      expect(getRegionalLocale()).toBe(value === 'system' ? undefined : value);
    }
  });
});
