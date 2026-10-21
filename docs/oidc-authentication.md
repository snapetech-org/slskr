# OIDC authentication

slskR can use an OpenID Connect provider for browser sign-in while retaining
its existing API-token and local authentication paths. OIDC is disabled unless
all four core settings are present.

## Configure the provider

Set these environment variables on the controller:

| Variable | Purpose |
| --- | --- |
| `SLSKR_OIDC_ISSUER_URL` | Exact issuer URL published by the provider. |
| `SLSKR_OIDC_CLIENT_ID` | Confidential web client ID. |
| `SLSKR_OIDC_CLIENT_SECRET` | Client secret. |
| `SLSKR_OIDC_REDIRECT_URI` | HTTPS callback registered at the provider. |
| `SLSKR_OIDC_PROVIDER` | Optional login-branding hint: `google`, `microsoft-entra`, `okta`, `auth0`, `keycloak`, `authentik`, `zitadel`, `amazon-cognito`, `gitlab`, `fusionauth`, `onelogin`, `pingone`, `jumpcloud`,
or `apple-sign-in`. Defaults to generic. |
| `SLSKR_OIDC_ALLOWED_EMAILS` | Optional exact verified-email allowlist, comma/space/semicolon separated. |
| `SLSKR_OIDC_ALLOWED_EMAIL_DOMAINS` | Optional exact email-domain allowlist. |
| `SLSKR_OIDC_ALLOW_ANY_VERIFIED_USER` | Set to `true` to admit any provider-verified email. Defaults to `false`. |
| `SLSKR_OIDC_ALLOW_PRIVATE_ISSUER` | Set to `true` only for an explicitly trusted private provider; permits HTTP issuers and private endpoint addresses. Defaults to `false`. |

The callback path is `/api/v0/session/oidc/callback` at the root URL. If
`web.url_base` is configured, include that base path before the callback path.
For example, `web.url_base = "/slsk"` requires
`https://slsk.example.test/slsk/api/v0/session/oidc/callback`.

Admission requires at least one exact email, one exact domain, or the explicit
allow-any setting. An empty policy denies everyone. The provider must return a
verified email claim either in the ID token or from UserInfo with a matching
subject. Provider groups do not grant application roles; admitted identities
receive the controller's existing administrator session. OIDC identity is
recorded by the exact `(issuer, subject)` pair, and accounts are not linked by
email.

Ordinary providers use authorization code with PKCE S256; Apple uses its
documented form-post flow without PKCE. All flows use one-time state and nonce,
server
side code exchange, and the existing short-lived administrator JWT. Configure
the provider and callback on HTTPS. Local/API-token authentication remains
available as the recovery path.

The private-issuer option is for deliberate self-hosted deployments. When it
is disabled, discovery and provider endpoints must use HTTPS and resolve only
to public addresses. DNS is checked before requests; operators should use a
stable provider hostname and trusted network configuration.

The provider hint changes only the button label, bundled local logo, and
official provider setup link. It does not select an issuer or relax OIDC
validation. Unknown values fall back to generic OIDC.

### Sign in with Apple

Set the issuer to exactly `https://appleid.apple.com`, use the Apple Services ID
as the client ID, and put the signed client-secret JWT in
`SLSKR_OIDC_CLIENT_SECRET`. Register the exact HTTPS callback shown above with
Apple. The adapter requests only `openid email`, uses `response_mode=form_post`,
and omits PKCE for Apple's documented web flow. Apple email verification may
arrive as a boolean or a JSON string; only `true` is admitted. Rotate the JWT
before its six-month maximum expiry. See Apple's [environment setup](https://developer.apple.com/documentation/signinwithapple/configuring-your-environment-for-sign-in-with-apple)
and [web authorization flow](https://developer.apple.com/documentation/signinwithapple/incorporating-sign-in-with-apple-into-other-platforms).

See the [shared cross-project OIDC contract](https://github.com/snapetech-org/seerrng/blob/main/docs/maintainers/oidc-cross-project-template.md)
for the common flow, identity-admission, and security behavior.
