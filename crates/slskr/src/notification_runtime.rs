use super::*;

#[derive(Clone, Copy)]
enum NotificationTitleKind {
    PrivateMessage,
    RoomMention,
}

fn interpolate_notification_title(
    template: &str,
    language: &str,
    username: &str,
    room: &str,
) -> String {
    let mut rendered = String::with_capacity(template.len() + username.len() + room.len());
    let mut remaining = template;
    loop {
        let Some(opening) = remaining.find('{') else {
            rendered.push_str(remaining);
            break;
        };
        rendered.push_str(&remaining[..opening]);
        let placeholder_start = &remaining[opening..];
        let Some(closing) = placeholder_start.find('}') else {
            rendered.push_str(placeholder_start);
            break;
        };
        let (placeholder, tail) = placeholder_start.split_at(closing + 1);
        let value = match placeholder {
            "{username}" => Some(username),
            "{room}" => Some(room),
            _ => None,
        };
        if let Some(value) = value {
            if language == "ar" {
                rendered.push('\u{2068}');
                rendered.push_str(value);
                rendered.push('\u{2069}');
            } else {
                rendered.push_str(value);
            }
        } else {
            rendered.push_str(placeholder);
        }
        remaining = tail;
    }
    rendered
}

fn notification_title(
    language: &str,
    kind: NotificationTitleKind,
    username: &str,
    room: &str,
) -> String {
    static CATALOG: std::sync::OnceLock<serde_json::Value> = std::sync::OnceLock::new();
    let catalog = CATALOG.get_or_init(|| {
        serde_json::from_str(include_str!("../data/notification-titles.json"))
            .expect("notification title catalog must be valid JSON")
    });
    let (catalog_key, source) = match kind {
        NotificationTitleKind::PrivateMessage => {
            ("privateMessage", "Private Message from {username}")
        }
        NotificationTitleKind::RoomMention => {
            ("roomMention", "Room Mention by {username} in {room}")
        }
    };
    let localized_language = if catalog.get(language).is_some() {
        language
    } else {
        "en"
    };
    let template = catalog
        .get(localized_language)
        .and_then(|locale| locale.get(catalog_key))
        .and_then(serde_json::Value::as_str)
        .unwrap_or(source);
    interpolate_notification_title(template, localized_language, username, room)
}

async fn send_ntfy_notification(
    options: &config::NtfyIntegrationSettings,
    title: &str,
    body: &str,
) -> Result<(), String> {
    let resolved = validate_integration_base_url(&options.url)?;
    send_ntfy_notification_to(options, title, body, &options.url, &resolved).await
}

pub(super) async fn send_ntfy_notification_to(
    options: &config::NtfyIntegrationSettings,
    title: &str,
    body: &str,
    endpoint: &str,
    resolved: &ResolvedIntegrationTarget,
) -> Result<(), String> {
    let client = reqwest::Client::builder()
        .timeout(Duration::from_secs(30))
        .redirect(reqwest::redirect::Policy::none())
        .no_proxy()
        .resolve_to_addrs(&resolved.host, &resolved.addrs)
        .build()
        .map_err(|error| format!("failed to build Ntfy client: {error}"))?;
    let mut request = client
        .post(endpoint)
        .header("Title", format!("{}: {title}", options.notification_prefix))
        .header("Content-Type", "text/plain; charset=utf-8")
        .body(body.to_owned());
    if !options.access_token.trim().is_empty() {
        request = request.bearer_auth(&options.access_token);
    }
    let response = request
        .send()
        .await
        .map_err(|error| format!("Ntfy request failed: {error}"))?;
    if !response.status().is_success() {
        return Err(format!("Ntfy returned HTTP {}", response.status()));
    }
    Ok(())
}

pub(super) async fn send_pushover_notification(
    options: &config::PushoverIntegrationSettings,
    title: &str,
    body: &str,
    endpoint: &str,
) -> Result<(), String> {
    let prefixed_title = format!("{}: {title}", options.notification_prefix);
    let response = reqwest::Client::builder()
        .timeout(Duration::from_secs(30))
        .redirect(reqwest::redirect::Policy::none())
        .build()
        .map_err(|error| format!("failed to build Pushover client: {error}"))?
        .post(endpoint)
        .form(&[
            ("token", options.token.as_str()),
            ("user", options.user_key.as_str()),
            ("title", prefixed_title.as_str()),
            ("message", body),
        ])
        .send()
        .await
        .map_err(|error| format!("Pushover request failed: {error}"))?;
    if !response.status().is_success() {
        return Err(format!("Pushover returned HTTP {}", response.status()));
    }
    Ok(())
}

pub(super) async fn send_pushbullet_notification(
    options: &config::PushbulletIntegrationSettings,
    title: &str,
    body: &str,
    endpoint: &str,
) -> Result<(), String> {
    let client = reqwest::Client::builder()
        .timeout(Duration::from_secs(30))
        .redirect(reqwest::redirect::Policy::none())
        .build()
        .map_err(|error| format!("failed to build Pushbullet client: {error}"))?;
    let payload = serde_json::json!({"title": format!("{} {title}", options.notification_prefix), "body": body, "type": "note"});
    let attempts = options.retry_attempts.max(1);
    let mut last_error = String::new();
    for _ in 0..attempts {
        match client
            .post(endpoint)
            .header("Access-Token", &options.access_token)
            .header("User-Agent", format!("slskR v{APP_VERSION}"))
            .json(&payload)
            .send()
            .await
        {
            Ok(response) if response.status().is_success() => return Ok(()),
            Ok(response) => last_error = format!("Pushbullet returned HTTP {}", response.status()),
            Err(error) => last_error = format!("Pushbullet request failed: {error}"),
        }
    }
    Err(last_error)
}

pub(super) async fn send_private_message_notifications(
    state: &AppState,
    username: &str,
    message: &str,
) {
    let key = format!("notification:pm:{username}");
    if !state
        .private_message_auto_responses
        .write()
        .await
        .should_respond(&key, unix_timestamp(), 30)
    {
        return;
    }
    let integrations = state.integration_settings.read().await.clone();
    let title = notification_title(
        &integrations.notification_language,
        NotificationTitleKind::PrivateMessage,
        username,
        "",
    );
    if integrations.pushbullet.enabled && integrations.pushbullet.notify_on_private_message {
        if integrations.pushbullet.cooldown_time < 0 {
            record_daemon_log(
                state,
                logging::LogLevel::Warn,
                "pushbullet",
                "Pushbullet cooldown is negative".to_owned(),
            )
            .await;
            return;
        }
        let cooldown = u64::try_from(integrations.pushbullet.cooldown_time)
            .unwrap_or_default()
            .saturating_add(999)
            / 1_000;
        let push_key = format!("pushbullet:pm:{username}");
        if state
            .private_message_auto_responses
            .write()
            .await
            .should_respond(&push_key, unix_timestamp(), cooldown)
        {
            if let Err(error) = send_pushbullet_notification(
                &integrations.pushbullet,
                &title,
                message,
                "https://api.pushbullet.com/v2/pushes",
            )
            .await
            {
                record_daemon_log(state, logging::LogLevel::Warn, "pushbullet", error).await;
            }
        }
    }
    if integrations.ntfy.enabled && integrations.ntfy.notify_on_private_message {
        if let Err(error) = send_ntfy_notification(&integrations.ntfy, &title, message).await {
            record_daemon_log(state, logging::LogLevel::Error, "ntfy", error).await;
        }
    }
    if integrations.pushover.enabled && integrations.pushover.notify_on_private_message {
        if let Err(error) = send_pushover_notification(
            &integrations.pushover,
            &title,
            message,
            "https://api.pushover.net/1/messages.json",
        )
        .await
        {
            record_daemon_log(state, logging::LogLevel::Error, "pushover", error).await;
        }
    }
}

pub(super) async fn send_room_mention_notifications(
    state: &AppState,
    room: &str,
    username: &str,
    message: &str,
) {
    let key = format!("notification:room:{room}:{username}");
    if !state
        .private_message_auto_responses
        .write()
        .await
        .should_respond(&key, unix_timestamp(), 30)
    {
        return;
    }
    let integrations = state.integration_settings.read().await.clone();
    let title = notification_title(
        &integrations.notification_language,
        NotificationTitleKind::RoomMention,
        username,
        room,
    );
    if integrations.pushbullet.enabled && integrations.pushbullet.notify_on_room_mention {
        if integrations.pushbullet.cooldown_time < 0 {
            record_daemon_log(
                state,
                logging::LogLevel::Warn,
                "pushbullet",
                "Pushbullet cooldown is negative".to_owned(),
            )
            .await;
            return;
        }
        let cooldown = u64::try_from(integrations.pushbullet.cooldown_time)
            .unwrap_or_default()
            .saturating_add(999)
            / 1_000;
        let push_key = format!("pushbullet:room:{room}");
        if state
            .private_message_auto_responses
            .write()
            .await
            .should_respond(&push_key, unix_timestamp(), cooldown)
        {
            if let Err(error) = send_pushbullet_notification(
                &integrations.pushbullet,
                &title,
                message,
                "https://api.pushbullet.com/v2/pushes",
            )
            .await
            {
                record_daemon_log(state, logging::LogLevel::Warn, "pushbullet", error).await;
            }
        }
    }
    if integrations.ntfy.enabled && integrations.ntfy.notify_on_room_mention {
        if let Err(error) = send_ntfy_notification(&integrations.ntfy, &title, message).await {
            record_daemon_log(state, logging::LogLevel::Error, "ntfy", error).await;
        }
    }
    if integrations.pushover.enabled && integrations.pushover.notify_on_room_mention {
        if let Err(error) = send_pushover_notification(
            &integrations.pushover,
            &title,
            message,
            "https://api.pushover.net/1/messages.json",
        )
        .await
        {
            record_daemon_log(state, logging::LogLevel::Error, "pushover", error).await;
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn notification_titles_use_selected_locale_and_preserve_opaque_values() {
        assert_eq!(
            notification_title("en", NotificationTitleKind::PrivateMessage, "peer/name", "",),
            "Private Message from peer/name"
        );
        assert_eq!(
            notification_title(
                "es",
                NotificationTitleKind::RoomMention,
                "peer/name",
                "room:one",
            ),
            "Mención de peer/name en room:one"
        );
        assert_eq!(
            notification_title("ar", NotificationTitleKind::PrivateMessage, "peer/name", "",),
            "رسالة خاصة من \u{2068}peer/name\u{2069}"
        );
        assert_eq!(
            notification_title(
                "unknown",
                NotificationTitleKind::RoomMention,
                "peer/name",
                "room:one",
            ),
            "Room Mention by peer/name in room:one"
        );
    }

    #[test]
    fn notification_titles_do_not_reprocess_placeholder_like_user_data() {
        let username = "peer{room}";
        let room = "Mix{username}";
        assert_eq!(
            notification_title("en", NotificationTitleKind::PrivateMessage, username, "",),
            "Private Message from peer{room}"
        );
        assert_eq!(
            notification_title("en", NotificationTitleKind::RoomMention, username, room,),
            "Room Mention by peer{room} in Mix{username}"
        );
        assert_eq!(
            notification_title("ar", NotificationTitleKind::RoomMention, username, room,),
            "أشار إليك \u{2068}peer{room}\u{2069} في \u{2068}Mix{username}\u{2069}"
        );
    }

    #[test]
    fn notification_title_catalog_matches_the_web_locale_catalogs() {
        let title_catalog: serde_json::Value =
            serde_json::from_str(include_str!("../data/notification-titles.json")).unwrap();
        for language in crate::config::SUPPORTED_NOTIFICATION_LANGUAGES {
            if *language == "en" {
                assert_eq!(
                    title_catalog["en"]["privateMessage"],
                    "Private Message from {username}"
                );
                assert_eq!(
                    title_catalog["en"]["roomMention"],
                    "Room Mention by {username} in {room}"
                );
                continue;
            }
            let path = std::path::Path::new(env!("CARGO_MANIFEST_DIR"))
                .join("../../web/src/lib/locales")
                .join(format!("ui-labels.{language}.json"));
            let web_catalog: serde_json::Value = serde_json::from_str(
                &std::fs::read_to_string(path).expect("web locale catalog must exist"),
            )
            .expect("web locale catalog must be valid JSON");
            assert_eq!(
                title_catalog[language]["privateMessage"],
                web_catalog["Private Message from {username}"],
                "{language} private-message title"
            );
            assert_eq!(
                title_catalog[language]["roomMention"],
                web_catalog["Room Mention by {username} in {room}"],
                "{language} room-mention title"
            );
        }
    }
}
