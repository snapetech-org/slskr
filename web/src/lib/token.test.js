import { afterEach, describe, expect, it } from 'vitest';
import {
  clearToken,
  getTokenExpiry,
  getTokenRemainingMillis,
  setToken,
} from './token';

const tokenWithExpiry = (exp) => {
  const header = btoa(JSON.stringify({ alg: 'HS256', typ: 'JWT' }));
  const payload = btoa(JSON.stringify({ exp }))
    .replace(/\+/g, '-')
    .replace(/\//g, '_')
    .replace(/=+$/, '');
  return `${header}.${payload}.signature`;
};

describe('token expiry helpers', () => {
  afterEach(() => {
    clearToken();
  });

  it('reads exp from a stored token', () => {
    setToken(sessionStorage, tokenWithExpiry(1234));

    expect(getTokenExpiry()).toBe(1234);
  });

  it('returns undefined for missing or malformed tokens', () => {
    expect(getTokenExpiry()).toBeUndefined();

    setToken(sessionStorage, 'not-a-jwt');

    expect(getTokenExpiry()).toBeUndefined();
  });

  it('reports the remaining lifetime in milliseconds', () => {
    const exp = Math.floor(Date.now() / 1000) + 60;
    setToken(sessionStorage, tokenWithExpiry(exp));

    const remaining = getTokenRemainingMillis();

    expect(remaining).toBeGreaterThan(58_000);
    expect(remaining).toBeLessThanOrEqual(60_000);
  });
});
