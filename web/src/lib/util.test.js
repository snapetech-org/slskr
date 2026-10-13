import * as utils from './util';
import { act, renderHook } from '@testing-library/react';

const regionalPreferencesKey = 'slskr:experience-preferences:v1';

describe('formatBytesAsUnit', () => {
  it('converts bytes to specified unit', () => {
    expect(utils.formatBytesAsUnit(1_234_567, 'MB', 2)).toBe(1.18);
  });
});

describe('dashboard formatting helpers', () => {
  it('formats speeds and queue waits like slskd', () => {
    expect(utils.formatSpeed(1_024)).toBe('1 KB/s');
    expect(utils.formatWait(30)).toBe('30s');
    expect(utils.formatWait(90)).toBe('1.5m');
  });

  it('truncates long diagnostic text with an ellipsis', () => {
    expect(utils.truncate('abcdefgh', 5)).toBe('abcde...');
  });
});

describe('regional number formatting', () => {
  beforeEach(() => {
    localStorage.setItem(regionalPreferencesKey, JSON.stringify({ regionalFormat: 'de' }));
    utils.setRegionalFormatPreference('de');
  });

  afterEach(() => {
    utils.setRegionalFormatPreference('system');
    localStorage.removeItem(regionalPreferencesKey);
  });

  it('localizes common byte, speed, wait, and count formatting', () => {
    expect(utils.formatBytes(1_536)).toBe('1,5 KB');
    expect(utils.formatBytesFixed(1_024)).toBe('1,0 KB');
    expect(utils.formatSpeed(1_536)).toBe('1,5 KB/s');
    expect(utils.formatWait(90)).toBe('1,5m');
    expect(utils.formatRegionalNumber(1_234.5)).toBe('1.234,5');
    expect(utils.formatRegionalCompactNumber(1_234)).toBe(
      new Intl.NumberFormat('de', {
        notation: 'compact',
        maximumFractionDigits: 1,
      }).format(1_234),
    );
  });

  it('uses locale-native compact digits, suffixes, and magnitude boundaries', () => {
    for (const [locale, value] of [
      ['ar', 1_234_567],
      ['ja', 12_345],
      ['zh-CN', 12_345],
    ]) {
      utils.setRegionalFormatPreference(locale);
      expect(utils.formatRegionalCompactNumber(value)).toBe(
        new Intl.NumberFormat(locale, {
          notation: 'compact',
          maximumFractionDigits: 1,
        }).format(value),
      );
    }

    utils.setRegionalFormatPreference('ar');
    expect(utils.formatRegionalCompactNumber(1_234_567)).not.toMatch(/[KM]/u);
    utils.setRegionalFormatPreference('ja');
    expect(utils.formatRegionalCompactNumber(12_345)).toContain('万');
  });

  it('localizes zero byte, speed, and wait values with Arabic digits', () => {
    utils.setRegionalFormatPreference('ar');
    const zero = new Intl.NumberFormat('ar').format(0);

    expect(utils.formatBytes(0)).toBe(`${zero} B`);
    expect(utils.formatBytesFixed(0)).toBe(`${zero} B`);
    expect(utils.formatSpeed(0)).toBe(`${zero} B/s`);
    expect(utils.formatWait(0)).toBe(`${zero}s`);
  });

  it('formats regional time with an explicit seconds field', () => {
    const date = new Date('2026-10-13T12:34:56Z');
    const options = { hour: '2-digit', minute: '2-digit', second: '2-digit' };
    expect(utils.formatRegionalTime(date, options)).toBe(
      new Intl.DateTimeFormat('de', options).format(date),
    );
  });

  it('notifies open views when the selected regional format changes', () => {
    const { result } = renderHook(() => utils.useRegionalFormat());

    act(() => utils.setRegionalFormatPreference('fr'));

    expect(result.current).toBe('fr');
  });
});
