import { afterEach, describe, expect, it } from 'vitest';
import {
  clearToken,
  getTokenExpiry,
  getTokenRemainingMillis,
  isTokenRefreshable,
  setToken,
} from './token';

const tokenWithClaims = (claims) => {
  const header = btoa(JSON.stringify({ alg: 'HS256', typ: 'JWT' }));
  const payload = btoa(JSON.stringify(claims))
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
    setToken(sessionStorage, tokenWithClaims({ exp: 1234 }));

    expect(getTokenExpiry()).toBe(1234);
  });

  it('returns undefined for missing or malformed tokens', () => {
    expect(getTokenExpiry()).toBeUndefined();

    setToken(sessionStorage, 'not-a-jwt');

    expect(getTokenExpiry()).toBeUndefined();
  });

  it('reports the remaining lifetime in milliseconds', () => {
    const exp = Math.floor(Date.now() / 1000) + 60;
    setToken(sessionStorage, tokenWithClaims({ exp }));

    const remaining = getTokenRemainingMillis();

    expect(remaining).toBeGreaterThan(58_000);
    expect(remaining).toBeLessThanOrEqual(60_000);
  });

  it('only schedules refresh for locally authenticated tokens with an epoch', () => {
    setToken(
      sessionStorage,
      tokenWithClaims({ auth_epoch: 42, exp: 1234 }),
    );
    expect(isTokenRefreshable()).toBe(true);

    setToken(sessionStorage, tokenWithClaims({ exp: 1234 }));
    expect(isTokenRefreshable()).toBe(false);

    setToken(
      sessionStorage,
      tokenWithClaims({ auth_epoch: 42, exp: 1234, oidc_issuer: 'idp' }),
    );
    expect(isTokenRefreshable()).toBe(false);
  });
});
