//! OIDC login adapter for the browser's existing short-lived administrator JWT.

use std::{
    collections::HashMap,
    fmt,
    future::Future,
    net::{IpAddr, Ipv4Addr, Ipv6Addr, SocketAddr},
    pin::Pin,
    sync::Mutex,
    time::{Duration, Instant},
};

use openidconnect::{
    core::{CoreAuthenticationFlow, CoreClient, CoreProviderMetadata, CoreResponseMode},
    reqwest, AuthType, AuthorizationCode, ClientId, ClientSecret, CsrfToken, EndpointMaybeSet,
    EndpointNotSet, EndpointSet, IssuerUrl, Nonce, OAuth2TokenResponse, PkceCodeChallenge,
    PkceCodeVerifier, RedirectUrl, Scope, TokenResponse,
};
use serde::Deserialize;
use tokio::net::lookup_host;

use crate::config::ControllerOidcSettings;

const FLOW_TTL: Duration = Duration::from_secs(10 * 60);
const MAX_PENDING_FLOWS: usize = 256;
const MAX_PROVIDER_RESPONSE_BYTES: usize = 1 << 20;

type ConfiguredCoreClient = CoreClient<
    EndpointSet,
    EndpointNotSet,
    EndpointNotSet,
    EndpointNotSet,
    EndpointSet,
    EndpointMaybeSet,
>;

#[derive(Debug)]
struct OidcHttpError;

impl fmt::Display for OidcHttpError {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter.write_str("OIDC provider request failed or exceeded its size limit")
    }
}

impl std::error::Error for OidcHttpError {}

struct BoundedOidcHttpClient {
    inner: reqwest::Client,
}

impl<'a> openidconnect::AsyncHttpClient<'a> for BoundedOidcHttpClient {
    type Error = OidcHttpError;
    type Future = Pin<
        Box<
            dyn Future<Output = Result<openidconnect::http::Response<Vec<u8>>, Self::Error>>
                + Send
                + 'a,
        >,
    >;

    fn call(&'a self, request: openidconnect::http::Request<Vec<u8>>) -> Self::Future {
        Box::pin(async move {
            let (parts, body) = request.into_parts();
            let url = openidconnect::url::Url::parse(&parts.uri.to_string())
                .map_err(|_| OidcHttpError)?;
            let method = reqwest::Method::from_bytes(parts.method.as_str().as_bytes())
                .map_err(|_| OidcHttpError)?;
            let response = self
                .inner
                .request(method, url)
                .version(parts.version)
                .headers(parts.headers)
                .body(body)
                .send()
                .await
                .map_err(|_| OidcHttpError)?;
            if response
                .content_length()
                .is_some_and(|length| length > MAX_PROVIDER_RESPONSE_BYTES as u64)
            {
                return Err(OidcHttpError);
            }
            let status = response.status();
            let version = response.version();
            let headers = response.headers().clone();
            let mut stream = response;
            let mut body = Vec::new();
            while let Some(chunk) = stream.chunk().await.map_err(|_| OidcHttpError)? {
                if body.len().saturating_add(chunk.len()) > MAX_PROVIDER_RESPONSE_BYTES {
                    return Err(OidcHttpError);
                }
                body.extend_from_slice(&chunk);
            }
            let mut builder = openidconnect::http::Response::builder()
                .status(status)
                .version(version);
            if let Some(response_headers) = builder.headers_mut() {
                *response_headers = headers;
            }
            builder.body(body).map_err(|_| OidcHttpError)
        })
    }
}

struct PendingFlow {
    nonce: Nonce,
    verifier: Option<PkceCodeVerifier>,
    binding: String,
    return_to: String,
    expires_at: Instant,
}

pub(super) struct OidcLoginStart {
    pub(super) authorize_url: String,
    pub(super) state: String,
    pub(super) browser_binding: String,
}

pub(super) struct OidcIdentity {
    pub(super) email: String,
    pub(super) subject: String,
    pub(super) return_to: String,
}

pub(super) struct OidcAuth {
    settings: ControllerOidcSettings,
    pending: Mutex<HashMap<String, PendingFlow>>,
}

impl std::fmt::Debug for OidcAuth {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        formatter
            .debug_struct("OidcAuth")
            .field("enabled", &self.enabled())
            .field(
                "pending_count",
                &self.pending.lock().map(|flows| flows.len()).ok(),
            )
            .finish()
    }
}

impl OidcAuth {
    pub(super) fn new(settings: ControllerOidcSettings) -> Self {
        Self {
            settings,
            pending: Mutex::new(HashMap::new()),
        }
    }

    pub(super) fn enabled(&self) -> bool {
        !self.settings.issuer_url.is_empty()
    }

    pub(super) fn provider_hint(&self) -> &str {
        &self.settings.provider
    }

    pub(super) async fn begin(&self, next: Option<&str>) -> Result<OidcLoginStart, &'static str> {
        if !self.enabled() {
            return Err("OIDC is not configured");
        }
        let (client, _http, _) = self.provider_client().await?;
        let apple = self.is_apple_issuer();
        let (challenge, verifier) = PkceCodeChallenge::new_random_sha256();
        let request = client
            .authorize_url(
                CoreAuthenticationFlow::AuthorizationCode,
                CsrfToken::new_random,
                Nonce::new_random,
            )
            .add_scope(Scope::new("openid".to_owned()))
            .add_scope(Scope::new("email".to_owned()))
            .add_scopes(if apple {
                Vec::new()
            } else {
                vec![Scope::new("profile".to_owned())]
            });
        let (url, csrf, nonce) = if apple {
            request
                .add_extra_param("response_mode", CoreResponseMode::FormPost.as_ref())
                .url()
        } else {
            request.set_pkce_challenge(challenge).url()
        };
        let state = csrf.secret().clone();
        let browser_binding = CsrfToken::new_random().secret().clone();
        let flow = PendingFlow {
            nonce,
            verifier: (!apple).then_some(verifier),
            binding: browser_binding.clone(),
            return_to: safe_return_to(next),
            expires_at: Instant::now() + FLOW_TTL,
        };
        let mut pending = self.pending.lock().expect("OIDC flow lock poisoned");
        pending.retain(|_, flow| flow.expires_at > Instant::now());
        if pending.len() >= MAX_PENDING_FLOWS {
            return Err("too many pending OIDC flows");
        }
        pending.insert(state.clone(), flow);
        Ok(OidcLoginStart {
            authorize_url: url.to_string(),
            state,
            browser_binding,
        })
    }

    pub(super) async fn finish(
        &self,
        state: &str,
        browser_binding: &str,
        code: &str,
    ) -> Result<OidcIdentity, &'static str> {
        if state.is_empty() || state.len() > 256 || code.is_empty() || code.len() > 8_192 {
            return Err("invalid OIDC callback");
        }
        let flow = {
            let mut pending = self.pending.lock().expect("OIDC flow lock poisoned");
            let Some(flow) = pending.get(state) else {
                return Err("expired OIDC callback");
            };
            if flow.expires_at <= Instant::now() {
                pending.remove(state);
                return Err("expired OIDC callback");
            }
            if !constant_time_equal(flow.binding.as_bytes(), browser_binding.as_bytes()) {
                return Err("invalid OIDC browser binding");
            }
            pending.remove(state).expect("OIDC flow was present")
        };

        let (client, http, userinfo_endpoint) = self.provider_client().await?;
        let exchange = client.exchange_code(AuthorizationCode::new(code.to_owned()));
        let exchange = match flow.verifier {
            Some(verifier) => exchange.set_pkce_verifier(verifier),
            None => exchange,
        };
        let tokens = exchange
            .request_async(&http)
            .await
            .map_err(|_| "OIDC code exchange failed")?;
        let id_token = tokens.id_token().ok_or("provider returned no ID token")?;
        let claims = id_token
            .claims(&client.id_token_verifier(), &flow.nonce)
            .map_err(|_| "ID token validation failed")?;
        let subject = claims.subject().as_str().to_owned();
        if subject.is_empty() || subject.len() > 1_024 {
            return Err("provider subject is invalid");
        }
        let email = match (claims.email(), claims.email_verified()) {
            (Some(email), Some(true)) => email.as_str().to_owned(),
            (_, Some(false)) => return Err("provider email is unverified"),
            _ => {
                let endpoint = userinfo_endpoint
                    .as_deref()
                    .ok_or("provider returned no email or user-info endpoint")?;
                let userinfo = http
                    .request_userinfo(endpoint, tokens.access_token().secret())
                    .await
                    .map_err(|_| "provider user-info request failed")?;
                if userinfo.get("sub").and_then(serde_json::Value::as_str) != Some(&subject)
                    || !json_boolean(userinfo.get("email_verified"))
                {
                    return Err("provider user-info identity is not verified");
                }
                userinfo
                    .get("email")
                    .and_then(serde_json::Value::as_str)
                    .ok_or("provider did not return an email")?
                    .to_owned()
            }
        }
        .trim()
        .to_ascii_lowercase();
        if email.len() > 320 || !self.email_allowed(&email) {
            return Err("OIDC identity is not admitted");
        }
        Ok(OidcIdentity {
            email,
            subject,
            return_to: flow.return_to,
        })
    }

    async fn provider_client(
        &self,
    ) -> Result<(ConfiguredCoreClient, BoundedOidcHttpClient, Option<String>), &'static str> {
        let issuer = openidconnect::url::Url::parse(&self.settings.issuer_url)
            .map_err(|_| "OIDC issuer URL is invalid")?;
        if !self.settings.allow_private_issuer {
            ensure_public_target(&issuer).await?;
        }
        let inner = reqwest::ClientBuilder::new()
            .redirect(reqwest::redirect::Policy::none())
            .timeout(Duration::from_secs(15))
            .build()
            .map_err(|_| "OIDC HTTP client could not start")?;
        let http = BoundedOidcHttpClient { inner };
        let metadata = CoreProviderMetadata::discover_async(
            IssuerUrl::new(self.settings.issuer_url.clone())
                .map_err(|_| "OIDC issuer URL is invalid")?,
            &http,
        )
        .await
        .map_err(|_| "OIDC discovery failed")?;
        if metadata.issuer().as_str() != self.settings.issuer_url {
            return Err("OIDC discovery issuer mismatch");
        }
        if !self.settings.allow_private_issuer {
            let data = serde_json::to_value(&metadata)
                .map_err(|_| "OIDC metadata could not be inspected")?;
            for name in ["authorization_endpoint", "token_endpoint", "jwks_uri"] {
                let raw = data
                    .get(name)
                    .and_then(serde_json::Value::as_str)
                    .ok_or("OIDC metadata omitted a required endpoint")?;
                let endpoint = openidconnect::url::Url::parse(raw)
                    .map_err(|_| "OIDC endpoint URL is invalid")?;
                if endpoint.scheme() != "https" {
                    return Err("OIDC provider endpoints must use HTTPS");
                }
                ensure_public_target(&endpoint).await?;
            }
            if let Some(raw) = data
                .get("userinfo_endpoint")
                .and_then(serde_json::Value::as_str)
            {
                let endpoint = openidconnect::url::Url::parse(raw)
                    .map_err(|_| "OIDC endpoint URL is invalid")?;
                if endpoint.scheme() != "https" {
                    return Err("OIDC provider endpoints must use HTTPS");
                }
                ensure_public_target(&endpoint).await?;
            }
        }
        let authorization_endpoint = metadata.authorization_endpoint().clone();
        let token_endpoint = metadata
            .token_endpoint()
            .cloned()
            .ok_or("OIDC discovery omitted a token endpoint")?;
        let userinfo_endpoint = metadata
            .userinfo_endpoint()
            .map(|endpoint| endpoint.as_str().to_owned());
        let mut client = CoreClient::from_provider_metadata(
            metadata,
            ClientId::new(self.settings.client_id.clone()),
            Some(ClientSecret::new(self.settings.client_secret.clone())),
        )
        .set_auth_uri(authorization_endpoint)
        .set_token_uri(token_endpoint)
        .set_redirect_uri(
            RedirectUrl::new(self.settings.redirect_uri.clone())
                .map_err(|_| "OIDC callback URL is invalid")?,
        );
        if self.is_apple_issuer() {
            client = client.set_auth_type(AuthType::RequestBody);
        }
        Ok((client, http, userinfo_endpoint))
    }

    fn is_apple_issuer(&self) -> bool {
        self.settings.issuer_url.trim() == "https://appleid.apple.com"
    }

    fn email_allowed(&self, email: &str) -> bool {
        if self.settings.allow_any_verified_user {
            return true;
        }
        let addresses = split_allowlist(&self.settings.allowed_emails);
        let domains = split_allowlist(&self.settings.allowed_email_domains);
        let email_domain = email
            .rsplit_once('@')
            .map(|(_, domain)| domain)
            .unwrap_or_default();
        addresses.iter().any(|allowed| allowed == email)
            || domains
                .iter()
                .any(|allowed| allowed.trim_start_matches('@') == email_domain)
    }
}

impl BoundedOidcHttpClient {
    async fn request_userinfo(
        &self,
        endpoint: &str,
        access_token: &str,
    ) -> Result<serde_json::Value, OidcHttpError> {
        let request = openidconnect::http::Request::builder()
            .method("GET")
            .uri(endpoint)
            .header(
                openidconnect::http::header::AUTHORIZATION,
                format!("Bearer {access_token}"),
            )
            .body(Vec::new())
            .map_err(|_| OidcHttpError)?;
        let response = openidconnect::AsyncHttpClient::call(self, request).await?;
        if !response.status().is_success()
            || !response
                .headers()
                .get(openidconnect::http::header::CONTENT_TYPE)
                .and_then(|value| value.to_str().ok())
                .is_some_and(|value| value.to_ascii_lowercase().contains("json"))
        {
            return Err(OidcHttpError);
        }
        serde_json::from_slice(response.body()).map_err(|_| OidcHttpError)
    }
}

fn json_boolean(value: Option<&serde_json::Value>) -> bool {
    matches!(value, Some(serde_json::Value::Bool(true)))
        || matches!(value, Some(serde_json::Value::String(value)) if value == "true")
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct OidcCompletionRequest {
    state: String,
    binding: String,
    code: String,
}

pub(super) async fn start_response(
    state: &crate::app_state::AppState,
    next: Option<&str>,
) -> crate::routing::HttpResponse {
    if !state.oidc_auth.enabled() {
        return crate::routing::not_found_response();
    }
    let app_root = app_root(&state.config.controller_web.url_base);
    let default_return = app_root.clone();
    let start = match state
        .oidc_auth
        .begin(next.or(Some(default_return.as_str())))
        .await
    {
        Ok(start) => start,
        Err(_) => return login_error_response(&app_root),
    };
    let data = serde_json::json!({
        "state": start.state,
        "binding": start.browser_binding,
        "url": start.authorize_url,
    });
    let data = script_json(&data);
    start_page(&data)
}

fn start_page(data: &str) -> crate::routing::HttpResponse {
    html_response(format!(
        "<!doctype html><html lang=\"en\"><head><meta charset=\"utf-8\"><title>Signing in</title></head><body><main><h1>Signing in</h1><p role=\"status\" aria-live=\"polite\">Redirecting to your identity provider…</p></main><script>const flow={data};const prefix='slskr-oidc-flow:';for(let i=sessionStorage.length-1;i>=0;i--){{const key=sessionStorage.key(i);if(!key||!key.startsWith(prefix))continue;try{{const pending=JSON.parse(sessionStorage.getItem(key)||'null');if(!pending||pending.expiresAt<=Date.now())sessionStorage.removeItem(key)}}catch{{sessionStorage.removeItem(key)}}}}sessionStorage.setItem(prefix+flow.state,JSON.stringify({{state:flow.state,binding:flow.binding,expiresAt:Date.now()+600000}}));location.replace(flow.url);</script></body></html>"
    ))
}

pub(super) fn callback_page(
    state: &str,
    code: &str,
    error: bool,
    url_base: &str,
) -> crate::routing::HttpResponse {
    let app_root = app_root(url_base);
    if error || state.is_empty() || code.is_empty() || state.len() > 256 || code.len() > 8_192 {
        return login_error_response(&app_root);
    }
    let data = serde_json::json!({
        "state": state,
        "code": code,
    });
    let data = script_json(&data);
    let app_root = script_json(&serde_json::json!(app_root));
    html_response(format!(
        "<!doctype html><html lang=\"en\"><head><meta charset=\"utf-8\"><title>Signing in</title></head><body><main><h1>Signing in</h1><p role=\"status\" aria-live=\"polite\">Completing sign-in…</p></main><script>const callback={data};const appRoot={app_root};const target=location.pathname;history.replaceState(null,'',target);const key='slskr-oidc-flow:'+callback.state;let transaction=null;try{{transaction=JSON.parse(sessionStorage.getItem(key)||'null')}}catch{{}}sessionStorage.removeItem(key);if(!transaction||transaction.state!==callback.state||transaction.expiresAt<=Date.now()){{location.replace(appRoot+'?oidcError=1')}}else{{fetch(target,{{method:'POST',headers:{{'Content-Type':'application/json'}},credentials:'same-origin',body:JSON.stringify({{state:callback.state,code:callback.code,binding:transaction.binding}})}}).then(async response=>{{const payload=await response.json();if(!response.ok||!payload.token)throw new Error('sign-in failed');sessionStorage.setItem('slskr-token',payload.token);location.replace(payload.returnTo||appRoot)}}).catch(()=>location.replace(appRoot+'?oidcError=1'))}}</script></body></html>"
    ))
}

pub(super) async fn complete_response(
    state: &crate::app_state::AppState,
    body: &str,
) -> crate::routing::HttpResponse {
    let Ok(request) = serde_json::from_str::<OidcCompletionRequest>(body) else {
        return crate::routing::bad_request_response("invalid OIDC callback");
    };
    let identity = match state
        .oidc_auth
        .finish(&request.state, &request.binding, &request.code)
        .await
    {
        Ok(identity) => identity,
        Err(_) => return crate::routing::unauthorized_response(),
    };
    let issued = crate::utils::unix_timestamp();
    let Some((token, claims)) = crate::utils::issue_oidc_admin_jwt(
        &state.config.controller_web_jwt_key,
        state.config.controller_profile,
        state.config.controller_web_jwt_ttl_millis,
        &identity.email,
        issued,
        &state.config.controller_oidc.issuer_url,
        &identity.subject,
    ) else {
        return crate::routing::service_unavailable_response(
            "JWT signing credential is unavailable",
        );
    };
    crate::routing::HttpResponse {
        status: "200 OK",
        content_type: "application/json; charset=utf-8",
        body: serde_json::json!({
            "name": claims.name,
            "tokenType": "Bearer",
            "token": token,
            "issued": claims.iat,
            "notBefore": claims.nbf,
            "expires": claims.exp,
            "returnTo": identity.return_to,
        })
        .to_string(),
    }
}

pub(super) fn form_post_callback_page(body: &str, url_base: &str) -> crate::routing::HttpResponse {
    if body.len() > 16 * 1024 {
        return login_error_response(&app_root(url_base));
    }
    let mut state = None;
    let mut code = None;
    let mut error = false;
    for (key, value) in openidconnect::url::form_urlencoded::parse(body.as_bytes()) {
        let slot = match key.as_ref() {
            "state" => &mut state,
            "code" => &mut code,
            "error" => {
                error = true;
                continue;
            }
            _ => continue,
        };
        if slot.replace(value.into_owned()).is_some() {
            return login_error_response(&app_root(url_base));
        }
    }
    callback_page(
        state.as_deref().unwrap_or_default(),
        code.as_deref().unwrap_or_default(),
        error,
        url_base,
    )
}

fn login_error_response(app_root: &str) -> crate::routing::HttpResponse {
    let app_root = html_attribute(app_root);
    html_response(format!(
        "<!doctype html><html lang=\"en\"><head><meta charset=\"utf-8\"><title>Sign-in failed</title></head><body><main><h1>Sign-in failed</h1><p role=\"alert\" aria-live=\"assertive\">Single sign-on failed. Return to the app and try again.</p><a href=\"{app_root}\">Return to sign in</a></main></body></html>"
    ))
}

fn html_attribute(value: &str) -> String {
    value
        .replace('&', "&amp;")
        .replace('"', "&quot;")
        .replace('\'', "&#39;")
        .replace('<', "&lt;")
        .replace('>', "&gt;")
}

fn app_root(url_base: &str) -> String {
    let base = url_base.trim_end_matches('/');
    if base.is_empty() {
        "/".to_owned()
    } else {
        format!("{base}/")
    }
}

fn html_response(body: String) -> crate::routing::HttpResponse {
    crate::routing::HttpResponse {
        status: "200 OK",
        content_type: "text/html; charset=utf-8",
        body,
    }
}

fn script_json(value: &serde_json::Value) -> String {
    serde_json::to_string(value)
        .unwrap_or_else(|_| "null".to_owned())
        .replace('&', "\\u0026")
        .replace('<', "\\u003c")
        .replace('>', "\\u003e")
}

fn split_allowlist(raw: &str) -> Vec<String> {
    raw.split([',', ';', ' ', '\t', '\r', '\n'])
        .map(str::trim)
        .filter(|value| !value.is_empty())
        .map(|value| value.to_ascii_lowercase())
        .collect()
}

fn safe_return_to(raw: Option<&str>) -> String {
    let Some(value) = raw.filter(|value| value.len() <= 2_048) else {
        return "/".to_owned();
    };
    if !value.starts_with('/')
        || value.starts_with("//")
        || value.contains('\\')
        || value.chars().any(char::is_control)
    {
        return "/".to_owned();
    }
    value.to_owned()
}

fn constant_time_equal(left: &[u8], right: &[u8]) -> bool {
    use subtle::ConstantTimeEq;
    left.len() == right.len() && bool::from(left.ct_eq(right))
}

async fn ensure_public_target(url: &openidconnect::url::Url) -> Result<(), &'static str> {
    let host = url.host_str().ok_or("OIDC provider host is missing")?;
    let port = url
        .port_or_known_default()
        .ok_or("OIDC provider port is missing")?;
    let addresses = lookup_host((host, port))
        .await
        .map_err(|_| "OIDC provider host could not be resolved")?
        .collect::<Vec<SocketAddr>>();
    if addresses.is_empty() || addresses.iter().any(|address| !is_public_ip(address.ip())) {
        return Err("OIDC provider resolves to a private or reserved address");
    }
    Ok(())
}

fn is_public_ip(ip: IpAddr) -> bool {
    match ip {
        IpAddr::V4(ip) => public_ipv4(ip),
        IpAddr::V6(ip) => public_ipv6(ip),
    }
}

fn public_ipv4(ip: Ipv4Addr) -> bool {
    let [a, b, c, _] = ip.octets();
    !(ip.is_unspecified()
        || ip.is_loopback()
        || ip.is_private()
        || ip.is_link_local()
        || ip.is_broadcast()
        || ip.is_multicast()
        || a == 0
        || (a == 100 && (64..=127).contains(&b))
        || (a == 192 && b == 0 && c == 0)
        || (a == 192 && b == 0 && c == 2)
        || (a == 198 && (b == 18 || b == 19 || (b == 51 && c == 100)))
        || (a == 203 && b == 0 && c == 113)
        || a >= 224)
}

fn public_ipv6(ip: Ipv6Addr) -> bool {
    let segments = ip.segments();
    !(ip.is_unspecified()
        || ip.is_loopback()
        || ip.is_multicast()
        || (segments[0] & 0xfe00) == 0xfc00
        || (segments[0] & 0xffc0) == 0xfe80
        || (segments[0] & 0xe000) != 0x2000
        || (segments[0] == 0x2001 && segments[1] == 0x0db8))
}

#[cfg(test)]
mod tests {
    use super::{callback_page, form_post_callback_page, json_boolean, start_page};

    #[test]
    fn apple_form_post_returns_a_same_origin_completion_page() {
        let response = form_post_callback_page("state=flow-1&code=auth-code", "/slsk");
        assert_eq!(response.status, "200 OK");
        assert!(response.body.contains("flow-1") && response.body.contains("auth-code"));
        assert!(response.body.contains("sessionStorage.getItem(key)"));
        assert!(response
            .body
            .contains("key='slskr-oidc-flow:'+callback.state"));
        assert!(response.body.contains("credentials:'same-origin'"));
    }

    #[test]
    fn start_page_stores_state_per_tab_and_expires_after_ten_minutes() {
        let response = start_page(
            r#"{"state":"flow-1","binding":"browser-binding","url":"https://idp.example/authorize"}"#,
        );

        assert!(response.body.contains("slskr-oidc-flow:"));
        assert!(response.body.contains("expiresAt:Date.now()+600000"));
        assert!(response
            .body
            .contains("role=\"status\" aria-live=\"polite\""));
    }

    #[test]
    fn oidc_status_pages_have_accessible_language_and_status_landmarks() {
        let callback = callback_page("flow-1", "auth-code", false, "/slsk");
        assert!(callback.body.contains("<html lang=\"en\">"));
        assert!(callback
            .body
            .contains("role=\"status\" aria-live=\"polite\""));
    }

    #[test]
    fn apple_form_post_rejects_duplicate_callback_fields() {
        let response = form_post_callback_page("state=first&state=second&code=auth-code", "");
        assert!(response.body.contains("Sign-in failed"));
        assert!(!response.body.contains("const callback="));
    }

    #[test]
    fn apple_form_post_rejects_oversized_bodies_and_provider_errors() {
        let oversized = "x".repeat(16 * 1024 + 1);
        assert!(form_post_callback_page(&oversized, "")
            .body
            .contains("Sign-in failed"));
        assert!(
            form_post_callback_page("state=flow-1&error=access_denied", "")
                .body
                .contains("Sign-in failed")
        );
    }

    #[test]
    fn email_verified_accepts_only_true_boolean_or_string() {
        assert!(json_boolean(Some(&serde_json::json!(true))));
        assert!(json_boolean(Some(&serde_json::json!("true"))));
        assert!(!json_boolean(Some(&serde_json::json!(false))));
        assert!(!json_boolean(Some(&serde_json::json!("false"))));
        assert!(!json_boolean(Some(&serde_json::json!("yes"))));
    }
}
