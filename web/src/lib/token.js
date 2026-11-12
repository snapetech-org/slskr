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

// Reads the token expiry for refresh scheduling only. Signature verification
// remains the server's responsibility.
export const getTokenExpiry = () => {
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
    return typeof decoded.exp === 'number' ? decoded.exp : undefined;
  } catch {
    return undefined;
  }
};

export const getTokenRemainingMillis = () => {
  const expiry = getTokenExpiry();
  return expiry === undefined ? undefined : expiry * 1000 - Date.now();
};
