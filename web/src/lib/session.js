import { tokenPassthroughValue } from '../config';
import api, { getCsrfTokenFromCookieString } from './api';
import {
  clearToken,
  getToken,
  isPassthroughEnabled,
  isRememberedSession,
  isTokenRefreshable,
  setToken,
} from './token';

export const getSecurityEnabled = async () => {
  return (await api.get('/session/enabled')).data;
};

export const enablePassthrough = () => {
  console.debug(
    'enabling token passthrough.  api calls will not be authenticated',
  );
  setToken(sessionStorage, tokenPassthroughValue);
};

export const isLoggedIn = () => {
  const token = getToken();
  return (
    token !== undefined && token !== null && token !== tokenPassthroughValue
  );
};

export const isRefreshable = () => isLoggedIn() && isTokenRefreshable();

export const login = async ({ username, password, rememberMe = false }) => {
  const { token } = (
    await api.post('/session', { password, rememberMe: Boolean(rememberMe), username })
  ).data;
  clearToken();
  setToken(rememberMe ? localStorage : sessionStorage, token);
  return token;
};

export const logout = () => {
  console.debug('removing token from local and session storage');
  clearToken();
};

export const check = async () => {
  if (!isLoggedIn() && !isPassthroughEnabled()) {
    return false;
  }

  try {
    await api.get('/session');
    return true;
  } catch (error) {
    if (error.response?.status === 401) {
      console.debug('session expired; clearing stored token');
      logout();
      return false;
    }
    throw error;
  }
};

// Sliding refresh: exchange a still-valid token for a fresh one with the same
// remembered-session category. Keeps active sessions from expiring while the
// UI stays open.
export const refresh = async () => {
  if (!isLoggedIn()) {
    return undefined;
  }

  const remembered = isRememberedSession();
  const token = getToken();
  const { data } = await api.post('/session/refresh');
  if (!data?.token) {
    throw new Error('session refresh returned no token');
  }
  // Logging out (or another refresh) while this request was in flight must
  // win; never resurrect a token that the user just discarded.
  if (getToken() !== token) {
    return getToken();
  }
  clearToken();
  setToken(remembered ? localStorage : sessionStorage, data.token);
  return data.token;
};

export const authHeaders = ({ csrf = false } = {}) => {
  const token = getToken();
  const headers =
    token && token !== tokenPassthroughValue
      ? { Authorization: `Bearer ${token}` }
      : {};
  const csrfToken = csrf ? getCsrfTokenFromCookieString() : null;
  if (csrfToken) {
    headers['X-CSRF-TOKEN'] = csrfToken;
  }

  return headers;
};
