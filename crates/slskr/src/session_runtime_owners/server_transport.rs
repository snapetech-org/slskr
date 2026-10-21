use super::*;

async fn send_with_inactivity_timeout<T, E, F>(
    action: &str,
    timeout: std::time::Duration,
    future: F,
) -> Result<T, String>
where
    E: std::fmt::Display,
    F: std::future::Future<Output = Result<T, E>>,
{
    tokio::time::timeout(timeout, future)
        .await
        .map_err(|_| format!("{action} timed out after {} ms", timeout.as_millis()))?
        .map_err(|error| error.to_string())
}

pub(super) async fn send_session_ping(
    state: &AppState,
    session: &mut Option<ServerSession<TcpStream>>,
    next_ping: &mut Instant,
) {
    let Some(active_session) = session.as_mut() else {
        return;
    };

    let result = send_with_inactivity_timeout(
        "server ping",
        state.config.soulseek_connection.timeout_inactivity,
        active_session.send_ping(),
    )
    .await;
    match result {
        Ok(()) => {
            *next_ping = Instant::now() + state.config.ping_interval;
            update_session(state, |snapshot| {
                snapshot.state = "connected";
                snapshot.last_error = None;
            })
            .await;
        }
        Err(error) => {
            *session = None;
            clear_connected_server_address(state);
            reset_distributed_network(state, None).await;
            update_session(state, |snapshot| {
                snapshot.state = "error";
                snapshot.last_error = Some(format!("ping failed: {error}"));
                snapshot.supporter = None;
                snapshot.connected_at = None;
            })
            .await;
        }
    }
}

pub(super) async fn send_active_server_message(
    state: &AppState,
    session: &mut Option<ServerSession<TcpStream>>,
    message: ServerMessage,
    action: &str,
) {
    let Some(active_session) = session.as_mut() else {
        eprintln!("cannot {action}: server session is disconnected");
        update_session(state, |snapshot| {
            snapshot.state = "disconnected";
            snapshot.last_error = Some(format!("cannot {action} while disconnected"));
        })
        .await;
        return;
    };

    let result = send_with_inactivity_timeout(
        action,
        state.config.soulseek_connection.timeout_inactivity,
        active_session.send_server_message(message),
    )
    .await;
    match result {
        Ok(()) => {
            eprintln!("sent server message for {action}");
            update_session(state, |snapshot| {
                snapshot.last_error = None;
            })
            .await;
        }
        Err(error) => {
            eprintln!("failed to send server message for {action}: {error}");
            *session = None;
            clear_connected_server_address(state);
            reset_distributed_network(state, None).await;
            update_session(state, |snapshot| {
                snapshot.state = "error";
                snapshot.last_error = Some(format!("{action} failed: {error}"));
                snapshot.supporter = None;
                snapshot.connected_at = None;
            })
            .await;
            if state.config.reconnect {
                state.runtime.write().await.set_reconnect_pending(true);
                update_session(state, |snapshot| {
                    snapshot.last_error = Some(format!("{action} failed; reconnect pending"));
                })
                .await;
            }
        }
    }
}

pub(crate) fn is_remote_queue_response(reason: &str) -> bool {
    reason
        .trim()
        .trim_end_matches('.')
        .eq_ignore_ascii_case("queued")
}

pub(crate) async fn send_session_command(
    state: &AppState,
    command: SessionCommand,
) -> Result<(), String> {
    state
        .session_commands
        .try_send(command)
        .map_err(|error| match error {
            tokio::sync::mpsc::error::TrySendError::Full(_) => {
                "session command queue is full".to_owned()
            }
            tokio::sync::mpsc::error::TrySendError::Closed(_) => {
                "session manager is not running".to_owned()
            }
        })
}

pub(crate) async fn send_active_interest_command(
    state: &AppState,
    message: ServerMessage,
) -> Result<(), String> {
    if state.session.read().await.state != "connected" {
        return Err("Soulseek session is disconnected".to_owned());
    }
    send_session_command(state, SessionCommand::SendServerMessage(message)).await
}

pub(crate) fn try_send_session_command(
    state: &AppState,
    command: SessionCommand,
) -> Result<(), String> {
    state
        .session_commands
        .try_send(command)
        .map_err(|error| format!("session command queue rejected request: {error}"))
}

pub(crate) async fn update_session<F>(state: &AppState, update: F)
where
    F: FnOnce(&mut SessionSnapshot),
{
    let mut snapshot = state.session.write().await;
    let previous_error = snapshot.last_error.clone();
    update(&mut snapshot);
    if snapshot.last_error != previous_error {
        if let Some(error) = snapshot.last_error.as_deref() {
            eprintln!("[Error] session state: {error}");
        }
    }
    snapshot.updated_at = unix_timestamp();
}

pub(crate) async fn update_listeners<F>(state: &AppState, update: F)
where
    F: FnOnce(&mut ListenerSnapshot),
{
    let mut snapshot = state.listeners.write().await;
    update(&mut snapshot);
    snapshot.updated_at = unix_timestamp();
}

#[cfg(test)]
mod tests {
    use super::send_with_inactivity_timeout;

    #[tokio::test]
    async fn stalled_server_write_times_out() {
        let error = send_with_inactivity_timeout(
            "server write",
            std::time::Duration::from_millis(5),
            std::future::pending::<Result<(), &'static str>>(),
        )
        .await
        .expect_err("stalled writes must be bounded");

        assert_eq!(error, "server write timed out after 5 ms");
    }
}
