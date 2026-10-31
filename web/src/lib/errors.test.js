import { describe, expect, it } from 'vitest';
import { toDisplayError } from './errors';

describe('toDisplayError', () => {
  it.each(['', ' ', '\n\t'])('uses the app fallback for blank server detail %j', (detail) => {
    expect(toDisplayError({ response: { data: detail } }, 'Unavailable')).toBe('Unavailable');
  });

  it('preserves numeric and nonempty server detail exactly', () => {
    expect(toDisplayError({ response: { data: 0 } })).toBe('0');
    expect(toDisplayError({ response: { data: '  raw detail  ' } })).toBe('  raw detail  ');
  });

  it('prefers a structured API error message', () => {
    expect(toDisplayError({ response: { data: { error: 'validation failed' } } })).toBe(
      'validation failed',
    );
  });

  it('serializes structured errors without exposing an object to React', () => {
    expect(toDisplayError({ response: { data: { code: 'invalid' } } })).toBe(
      '{"code":"invalid"}',
    );
  });

  it('uses a fallback for empty or non-displayable errors', () => {
    expect(toDisplayError(null, 'Unavailable')).toBe('Unavailable');
  });
});
