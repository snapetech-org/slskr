import { getOidcProviderPresentation } from './oidcProvider';

describe('getOidcProviderPresentation', () => {
  it('returns the branded setup guide for a known provider', () => {
    expect(getOidcProviderPresentation(' Keycloak ')).toMatchObject({
      label: 'Keycloak',
      icon: 'keycloak',
      setupUrl: 'https://www.keycloak.org/docs/latest/server_admin/',
    });
  });

  it('uses the Apple mark and setup guide for the Apple-specific adapter', () => {
    expect(getOidcProviderPresentation('apple-sign-in')).toMatchObject({
      label: 'Apple',
      icon: 'apple',
      setupUrl: 'https://developer.apple.com/documentation/signinwithapple/configuring-your-environment-for-sign-in-with-apple',
    });
  });

  it.each([
      ['fusionauth', 'FusionAuth', 'fusionauth', 'https://fusionauth.io/docs/lifecycle/authenticate-users/oauth/'],
      ['onelogin', 'OneLogin', 'onelogin', 'https://developers.onelogin.com/docs/openid-connect/connect-to-onelogin/'],
      ['pingone', 'PingOne', 'pingone', 'https://docs.pingidentity.com/pingone/applications/p1_edit_application_oidc.html'],
      ['jumpcloud', 'JumpCloud', 'jumpcloud', 'https://jumpcloud.com/support/sso-with-oidc']
  ])('returns branded provider presentation for %s', (id, label, icon, setupUrl) => {
    expect(getOidcProviderPresentation(id)).toMatchObject({ label, icon, setupUrl });
  });

  it('uses generic branding for unknown and prototype property names', () => {
    expect(getOidcProviderPresentation('constructor').icon).toBe('generic');
    expect(getOidcProviderPresentation('<script>').label).toBe('identity provider');
  });
});
