import { interfaceText } from './interfaceLocale';
import { isAppServerErrorMessage } from './serverErrorMessageAllowlist';

const displayErrorOutputBrand = Symbol('slskr.display-error-output');

const appOutput = (source) => Object.freeze({
  [displayErrorOutputBrand]: true,
  kind: 'app',
  source,
});

const opaqueOutput = (text) => Object.freeze({
  [displayErrorOutputBrand]: true,
  kind: 'opaque',
  text,
});

export const isDisplayErrorOutput = (value) =>
  Boolean(value && typeof value === 'object' && value[displayErrorOutputBrand] === true);

export const toDisplayErrorOutput = (error, fallback = 'Request failed') => {
  if (isDisplayErrorOutput(error)) return error;

  const value = error?.response?.data ?? error?.message ?? error;
  const preserveRemoteDetail = error?.isRemoteShareError === true;
  const fallbackOutput = () => appOutput(fallback);

  if (typeof value === 'number') return opaqueOutput(String(value));
  if (typeof value === 'string') {
    if (!value.trim()) return fallbackOutput();
    return !preserveRemoteDetail && isAppServerErrorMessage(value)
      ? appOutput(value)
      : opaqueOutput(value);
  }

  if (value && typeof value === 'object') {
    if (
      !preserveRemoteDetail &&
      value.code === 'unsupported_notification_title_language'
    ) {
      return appOutput('Unsupported notification title language');
    }

    const hasUnknownCode =
      value.code != null &&
      value.code !== 'unsupported_notification_title_language';

    for (const key of ['message', 'error', 'detail', 'title']) {
      if (typeof value[key] === 'string' && value[key].trim()) {
        return !preserveRemoteDetail &&
          !hasUnknownCode &&
          isAppServerErrorMessage(value[key])
          ? appOutput(value[key])
          : opaqueOutput(value[key]);
      }
    }

    try {
      const serialized = JSON.stringify(value);
      return opaqueOutput(typeof serialized === 'string' ? serialized : String(value));
    } catch {
      return fallbackOutput();
    }
  }

  return fallbackOutput();
};

// Keep the string helper for existing toast and interpolation callsites.
// Rendered message components should use toDisplayErrorOutput so localized
// app-authored copy and opaque server/provider details retain separate text metadata.
export const toDisplayError = (error, fallback = 'Request failed') => {
  const output = toDisplayErrorOutput(error, fallback);
  return output.kind === 'app' ? interfaceText(output.source) : output.text;
};
