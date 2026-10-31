import { interfaceText } from './interfaceLocale';
import { isAppServerErrorMessage } from './serverErrorMessageAllowlist';

export const toDisplayError = (error, fallback = 'Request failed') => {
  const value = error?.response?.data ?? error?.message ?? error;
  const preserveRemoteDetail = error?.isRemoteShareError === true;

  if (typeof value === 'number') return String(value);
  if (typeof value === 'string') {
    if (!value.trim()) return interfaceText(fallback);
    return !preserveRemoteDetail && isAppServerErrorMessage(value)
      ? interfaceText(value)
      : value;
  }

  if (value && typeof value === 'object') {
    if (
      !preserveRemoteDetail &&
      value.code === 'unsupported_notification_title_language'
    ) {
      return interfaceText('Unsupported notification title language');
    }

    const hasUnknownCode =
      value.code != null &&
      value.code !== 'unsupported_notification_title_language';

    for (const key of ['message', 'error', 'detail', 'title']) {
      if (typeof value[key] === 'string' && value[key].trim()) {
        return !preserveRemoteDetail &&
          !hasUnknownCode &&
          isAppServerErrorMessage(value[key])
          ? interfaceText(value[key])
          : value[key];
      }
    }

    try {
      return JSON.stringify(value);
    } catch {
      return interfaceText(fallback);
    }
  }

  return interfaceText(fallback);
};
