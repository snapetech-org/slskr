import { interfaceText } from './interfaceLocale';

export const toDisplayError = (error, fallback = 'Request failed') => {
  const value = error?.response?.data ?? error?.message ?? error;

  if (typeof value === 'number') return String(value);
  if (typeof value === 'string') return value.trim() ? value : interfaceText(fallback);

  if (value && typeof value === 'object') {
    for (const key of ['message', 'error', 'detail', 'title']) {
      if (typeof value[key] === 'string' && value[key].trim()) return value[key];
    }

    try {
      return JSON.stringify(value);
    } catch {
      return interfaceText(fallback);
    }
  }

  return interfaceText(fallback);
};
