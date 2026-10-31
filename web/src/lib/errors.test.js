import { describe, expect, it, vi } from 'vitest';
import { toDisplayError } from './errors';
import { APP_SERVER_ERROR_MESSAGES } from './serverErrorMessageAllowlist';

vi.mock('./interfaceLocale', () => ({
  interfaceText: (source) => {
    if (source === 'Search query is required') return 'Localized search query';
    if (source === 'Unsupported notification title language') {
      return 'Localized unsupported notification title language';
    }
    return source;
  },
}));

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

  it('localizes a known app-owned API error code while preserving unknown errors', () => {
    expect(
      toDisplayError({
        response: {
          data: {
            code: 'unsupported_notification_title_language',
            error: 'Unsupported notification title language',
          },
        },
      }),
    ).toBe('Localized unsupported notification title language');
    expect(
      toDisplayError({
        response: {
          data: {
            code: 'unknown_app_error',
            error: 'provider-specific error detail',
          },
        },
      }),
    ).toBe('provider-specific error detail');
  });

  it('localizes exact allowlisted server messages and preserves unknown details', () => {
    const allowedMessage = 'Search query is required';

    expect(
      toDisplayError({ response: { data: { error: allowedMessage } } }),
    ).toBe('Localized search query');
    expect(toDisplayError(new Error(allowedMessage))).toBe(
      'Localized search query',
    );

    const dynamicProviderDetail =
      'MusicBrainz lookup failed: upstream returned 503 for recording abc123';
    expect(
      toDisplayError({ response: { data: { error: dynamicProviderDetail } } }),
    ).toBe(dynamicProviderDetail);
  });

  it('preserves excluded pod errors and remote peer details verbatim', () => {
    const statusTextOnlyPodMessages = [
      'Failed to create pod',
      'Failed to delete pod',
      'Failed to get messages',
      'Failed to get pod',
      'Failed to get pod members',
      'Failed to join pod (may already be a member)',
      'Failed to list pods',
      'Failed to send message',
      'Failed to update pod',
      'Message body is required',
      'Message signature is required when PodCore.Security.SignatureMode is Enforce',
      "Mode must be 'readonly' or 'mirror'",
      'Only the designated gateway peer can modify private service policy',
      'PeerId is required',
      'Pod moderator membership is required',
      'PodId in URL must match PodId in body',
      'SenderPeerId is required',
      'SenderPeerId must match the authenticated peer identity',
      'pod revocation storage is unavailable',
    ];

    expect(APP_SERVER_ERROR_MESSAGES.size).toBe(537);
    for (const message of statusTextOnlyPodMessages) {
      expect(APP_SERVER_ERROR_MESSAGES.has(message)).toBe(false);
      expect(
        toDisplayError({ response: { data: { error: message } } }),
      ).toBe(message);
    }

    const peerMessage = 'Search query is required';
    expect(
      toDisplayError({
        isRemoteShareError: true,
        response: { data: { error: peerMessage } },
      }),
    ).toBe(peerMessage);
    expect(
      toDisplayError({
        isRemoteShareError: true,
        response: {
          data: {
            code: 'unsupported_notification_title_language',
            error: 'Unsupported notification title language',
          },
        },
      }),
    ).toBe('Unsupported notification title language');
  });

  it('does not translate allowlisted text with an unknown error code', () => {
    expect(
      toDisplayError({
        response: {
          data: {
            code: 'provider_specific_failure',
            error: 'Search query is required',
          },
        },
      }),
    ).toBe('Search query is required');
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
