import { tokenKey, tokenPassthroughValue } from '../config';
import {
  getLocalStorageItem,
  getSessionStorageItem,
  removeLocalStorageItem,
  removeSessionStorageItem,
  setStorageItem,
} from './storage';

// Remembered sessions live in localStorage so they survive closing the
// browser and restarting the daemon. Normal sessions stay in sessionStorage so
// closing the browser tab ends them.
export const getRememberedToken = () => getLocalStorageItem(tokenKey);
export const getToken = () =>
  getSessionStorageItem(tokenKey) ?? getRememberedToken();
export const isRememberedSession = () => {
  const token = getToken();
  return token !== undefined && token !== null && token === getRememberedToken();
};
export const setToken = (storage, token) => setStorageItem(storage, tokenKey, token);
export const clearToken = () => {
  removeLocalStorageItem(tokenKey);
  removeSessionStorageItem(tokenKey);
};

export const isPassthroughEnabled = () => getToken() === tokenPassthroughValue;

// Reads token claims for scheduling only. Signature verification remains the
// server's responsibility.
const getTokenClaims = () => {
  const token = getToken();
  if (!token || token === tokenPassthroughValue) return undefined;
  const payload = token.split('.')[1];
  if (!payload) return undefined;
  try {
    const normalized = payload.replace(/-/g, '+').replace(/_/g, '/');
    const padded = normalized.padEnd(
      Math.ceil(normalized.length / 4) * 4,
      '=',
    );
    const decoded = JSON.parse(atob(padded));
    return decoded && typeof decoded === 'object' ? decoded : undefined;
  } catch {
    return undefined;
  }
};

export const isTokenRefreshable = () => {
  const claims = getTokenClaims();
  return (
    claims !== undefined &&
    typeof claims.auth_epoch === 'number' &&
    !claims.oidc_issuer &&
    !claims.oidc_subject
  );
};

export const getTokenExpiry = () => {
  const expiry = getTokenClaims()?.exp;
  return typeof expiry === 'number' ? expiry : undefined;
};

export const getTokenRemainingMillis = () => {
  const expiry = getTokenExpiry();
  return expiry === undefined ? undefined : expiry * 1000 - Date.now();
};
