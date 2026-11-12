use super::fixtures::*;

const ADMIN_USERNAME: &str = "admin";
const ADMIN_PASSWORD: &str = "admin-password";

fn auth_env() -> MapEnv {
    MapEnv::default()
        .with("SLSKR_AUTH_DISABLED", "false")
        .with("SLSKD_USERNAME", ADMIN_USERNAME)
        .with("SLSKD_PASSWORD", ADMIN_PASSWORD)
}

async fn login(state: &crate::AppState, body: &str) -> crate::HttpResponse {
    crate::route_dispatch::route_http_request_with_headers(
        "POST",
        "/api/v0/session",
        None,
        body,
        state,
        &crate::RequestSecurityHeaders::default(),
    )
    .await
    .expect("login route")
}

fn token_from(response: &crate::HttpResponse) -> String {
    let body: serde_json::Value = serde_json::from_str(&response.body).expect("login body");
    body["token"].as_str().expect("login token").to_owned()
}

fn claims(state: &crate::AppState, token: &str) -> crate::utils::AdminJwtClaims {
    crate::utils::verify_admin_jwt(
        &state.config.controller_web_jwt_key,
        state.config.controller_profile,
        token,
        crate::utils::unix_timestamp(),
    )
    .expect("valid session token")
}

#[tokio::test]
async fn normal_login_keeps_the_standard_lifetime() {
    let (state, _commands) = test_state_with_env(auth_env());

    let response = login(
        &state,
        r#"{"username":"admin","password":"admin-password"}"#,
    )
    .await;
    assert_eq!(response.status, "200 OK");
    let claims = claims(&state, &token_from(&response));
    assert!(!claims.remember);
    assert_eq!(
        claims.exp - claims.iat,
        state.config.controller_web_jwt_ttl_millis / 1000
    );
}

#[tokio::test]
async fn remembered_login_issues_a_long_lived_remembered_token() {
    let (state, _commands) = test_state_with_env(auth_env());

    let response = login(
        &state,
        r#"{"username":"admin","password":"admin-password","rememberMe":true}"#,
    )
    .await;
    assert_eq!(response.status, "200 OK");
    let claims = claims(&state, &token_from(&response));
    assert!(claims.remember);
    assert_eq!(
        claims.exp - claims.iat,
        state.config.controller_web_jwt_remember_ttl_millis / 1000
    );
}

#[tokio::test]
async fn session_refresh_preserves_the_remembered_category() {
    let (state, _commands) = test_state_with_env(auth_env());
    let response = login(
        &state,
        r#"{"username":"admin","password":"admin-password","rememberMe":true}"#,
    )
    .await;
    let token = token_from(&response);
    let authorization = format!("Bearer {token}");

    let refreshed = crate::route_dispatch::route_http_request_with_headers(
        "POST",
        "/api/v0/session/refresh",
        Some(authorization.as_str()),
        "",
        &state,
        &crate::RequestSecurityHeaders::default(),
    )
    .await
    .expect("refresh route");
    assert_eq!(refreshed.status, "200 OK");
    let refreshed_token = token_from(&refreshed);
    assert_ne!(refreshed_token, token);
    let claims = claims(&state, &refreshed_token);
    assert!(claims.remember);
    assert_eq!(
        claims.exp - claims.iat,
        state.config.controller_web_jwt_remember_ttl_millis / 1000
    );
}

#[tokio::test]
async fn session_refresh_requires_a_valid_bearer_token() {
    let (state, _commands) = test_state_with_env(auth_env());

    let response = crate::route_dispatch::route_http_request_with_headers(
        "POST",
        "/api/v0/session/refresh",
        None,
        "",
        &state,
        &crate::RequestSecurityHeaders::default(),
    )
    .await
    .expect("refresh route");
    assert_eq!(response.status, "401 Unauthorized");
}

#[tokio::test]
async fn session_refresh_rejects_tokens_after_a_web_auth_credential_change() {
    let (state, _commands) = test_state_with_env(auth_env());
    let response = login(
        &state,
        r#"{"username":"admin","password":"admin-password","rememberMe":true}"#,
    )
    .await;
    let token = token_from(&response);
    assert!(claims(&state, &token).auth_epoch.is_some());

    *state
        .controller_web_auth_password
        .write()
        .unwrap_or_else(std::sync::PoisonError::into_inner) = "new-password".to_owned();

    let authorization = format!("Bearer {token}");
    let rejected = crate::route_dispatch::route_http_request_with_headers(
        "POST",
        "/api/v0/session/refresh",
        Some(authorization.as_str()),
        "",
        &state,
        &crate::RequestSecurityHeaders::default(),
    )
    .await
    .expect("refresh route");
    assert_eq!(rejected.status, "401 Unauthorized");

    let response = login(
        &state,
        r#"{"username":"admin","password":"new-password","rememberMe":true}"#,
    )
    .await;
    assert_eq!(response.status, "200 OK");
    let authorization = format!("Bearer {}", token_from(&response));
    let refreshed = crate::route_dispatch::route_http_request_with_headers(
        "POST",
        "/api/v0/session/refresh",
        Some(authorization.as_str()),
        "",
        &state,
        &crate::RequestSecurityHeaders::default(),
    )
    .await
    .expect("refresh route");
    assert_eq!(refreshed.status, "200 OK");
}

#[tokio::test]
async fn session_refresh_rejects_legacy_tokens_without_a_credential_binding() {
    let (state, _commands) = test_state_with_env(auth_env());
    let (token, claims) = crate::utils::issue_admin_jwt(
        &state.config.controller_web_jwt_key,
        state.config.controller_profile,
        state.config.controller_web_jwt_ttl_millis,
        ADMIN_USERNAME,
        crate::utils::unix_timestamp(),
    )
    .expect("legacy session token");
    assert!(claims.auth_epoch.is_none());

    *state
        .controller_web_auth_password
        .write()
        .unwrap_or_else(std::sync::PoisonError::into_inner) = "new-password".to_owned();
    let authorization = format!("Bearer {token}");
    let response = crate::route_dispatch::route_http_request_with_headers(
        "POST",
        "/api/v0/session/refresh",
        Some(authorization.as_str()),
        "",
        &state,
        &crate::RequestSecurityHeaders::default(),
    )
    .await
    .expect("refresh route");

    assert_eq!(response.status, "401 Unauthorized");
}

#[tokio::test]
async fn session_refresh_rejects_oidc_tokens_without_provider_revalidation() {
    let (state, _commands) = test_state_with_env(auth_env());
    let auth_epoch = crate::utils::web_auth_epoch(
        &state.config.controller_web_jwt_key,
        ADMIN_USERNAME,
        ADMIN_PASSWORD,
    );
    let (token, _) = crate::utils::issue_oidc_admin_jwt(
        &state.config.controller_web_jwt_key,
        state.config.controller_profile,
        state.config.controller_web_jwt_ttl_millis,
        ADMIN_USERNAME,
        crate::utils::unix_timestamp(),
        "https://idp.example.invalid",
        "subject-1",
        auth_epoch,
    )
    .expect("OIDC session token");
    let authorization = format!("Bearer {token}");
    let response = crate::route_dispatch::route_http_request_with_headers(
        "POST",
        "/api/v0/session/refresh",
        Some(authorization.as_str()),
        "",
        &state,
        &crate::RequestSecurityHeaders::default(),
    )
    .await
    .expect("refresh route");

    assert_eq!(response.status, "401 Unauthorized");
}

#[tokio::test]
async fn scheduled_rotation_revocation_revokes_the_old_token() {
    let (state, _commands) = test_state_with_env(auth_env());
    let response = login(
        &state,
        r#"{"username":"admin","password":"admin-password"}"#,
    )
    .await;
    let token = token_from(&response);
    let session_claims = claims(&state, &token);

    crate::security_state::schedule_jwt_revocation(
        std::sync::Arc::clone(&state.revoked_jwts),
        session_claims.jti.clone(),
        session_claims.exp,
        0,
    );
    for _ in 0..50 {
        if state
            .revoked_jwts
            .write()
            .await
            .contains(&session_claims.jti, crate::utils::unix_timestamp())
        {
            return;
        }
        tokio::time::sleep(std::time::Duration::from_millis(10)).await;
    }
    panic!("scheduled JWT revocation did not run");
}

#[cfg(unix)]
#[test]
fn persisted_jwt_key_recovers_from_an_interrupted_write() {
    let state_dir = std::env::temp_dir().join(format!(
        "slskr-persisted-jwt-key-recovery-{}-{}",
        std::process::id(),
        std::time::SystemTime::now()
            .duration_since(std::time::UNIX_EPOCH)
            .unwrap()
            .as_nanos()
    ));
    std::fs::create_dir_all(&state_dir).expect("state dir");
    std::fs::write(state_dir.join("jwt-key"), "").expect("empty key file");

    let key = crate::config::load_or_create_persisted_controller_jwt_key(&state_dir)
        .expect("recovered key");
    assert!(key.len() >= 32);
    assert_eq!(
        std::fs::read_to_string(state_dir.join("jwt-key")).expect("persisted key"),
        key
    );

    std::fs::remove_dir_all(&state_dir).ok();
}

#[cfg(unix)]
#[test]
fn persisted_jwt_key_is_reused_and_private() {
    use std::os::unix::fs::PermissionsExt;

    let state_dir = std::env::temp_dir().join(format!(
        "slskr-persisted-jwt-key-{}-{}",
        std::process::id(),
        std::time::SystemTime::now()
            .duration_since(std::time::UNIX_EPOCH)
            .unwrap()
            .as_nanos()
    ));
    std::fs::create_dir_all(&state_dir).expect("state dir");

    let first =
        crate::config::load_or_create_persisted_controller_jwt_key(&state_dir).expect("first key");
    let second =
        crate::config::load_or_create_persisted_controller_jwt_key(&state_dir).expect("second key");
    assert_eq!(first, second);
    assert!(first.len() >= 32);

    let mode = std::fs::metadata(state_dir.join("jwt-key"))
        .expect("key metadata")
        .permissions()
        .mode()
        & 0o777;
    assert_eq!(mode, 0o600);

    std::fs::remove_dir_all(&state_dir).ok();
}
