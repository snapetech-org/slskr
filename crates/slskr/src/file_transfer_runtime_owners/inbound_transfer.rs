use super::*;

/// How long an inbound download waits for an optional `FileTransferInit` token
/// when the transfer token was already negotiated in `PeerInit`.
///
/// Reference clients disagree here: Nicotine+ and SoulseekQt announce the
/// transfer token (`FileTransferInit`) on the file-transfer socket, while
/// slskd carries it in `PeerInit` and expects our offset immediately. The peer
/// that announces a token writes it in the same burst as `PeerInit`, so a short
/// grace is enough to tell the two dialects apart without stalling peers that
/// never send one. A raw socket with no negotiated token is rejected if it
/// does not provide the token frame.
pub(crate) const INBOUND_TRANSFER_TOKEN_GRACE: time::Duration = time::Duration::from_millis(1500);

pub(crate) async fn handle_inbound_file_transfer(
    state: &AppState,
    mut file: slskr_client::file_transfer::FileTransferConnection<TcpStream>,
    token: Option<u32>,
    peer_username: Option<&str>,
    source_ip: Option<std::net::IpAddr>,
) -> Result<(), String> {
    if let Some(token) = token {
        let pending = state
            .pending_backfill_transfers
            .write()
            .await
            .remove(&token);
        if let Some(pending) = pending {
            let result =
                receive_backfill_header(state, &mut file, token, pending.expected_size).await;
            let public_result = result.clone();
            let _ = pending.response.send(public_result);
            return result.map(|_| ());
        }
    }
    let download_slots =
        usize::try_from(state.transfer_download_settings.read().await.slots).unwrap_or(usize::MAX);
    let mut token = token;
    let mut pre_received_token = None;
    if token.is_none() {
        // A raw `F` connection and standard `PeerInit(token=0)` carry their
        // transfer token in the first file-transfer frame. Read it before
        // looking up a queued transfer so the token can authorize that exact
        // entry. Absence of a token never falls back to another queue token.
        let remote_token = time::timeout(INBOUND_TRANSFER_TOKEN_GRACE, file.receive_token())
            .await
            .map_err(|_| "inbound file-transfer token receive timed out".to_owned())?
            .map_err(|error| format!("inbound file-transfer token receive failed: {error}"))?;
        token = Some(remote_token);
        pre_received_token = Some(remote_token);
    }
    let candidate = state
        .transfers
        .read()
        .await
        .pending_inbound_file_transfer(token, peer_username);
    if let Some(candidate) = candidate.as_ref().filter(|entry| entry.direction == 0) {
        if let Some(source_ip) = source_ip {
            let expected_ip = if let Some(username) = candidate.peer_username.as_deref() {
                cached_peer_endpoint(state, username)
                    .await
                    .map(|address| std::net::IpAddr::V4(address.ip))
            } else {
                None
            };
            if expected_ip != Some(source_ip) {
                return Err(format!(
                    "inbound download source address does not match peer {}",
                    candidate
                        .peer_username
                        .as_deref()
                        .map(redact_username)
                        .unwrap_or_else(|| "<unknown>".to_owned())
                ));
            }
        }
    }
    let transfer = {
        let mut transfers = state.transfers.write().await;
        transfers.claim_pending_inbound_file_transfer(
            token,
            peer_username,
            state.config.transfer_max_active,
            download_slots,
        )
    }
    .ok_or_else(|| {
        token.map_or_else(
            || "no accepted inbound file transfer is pending".to_owned(),
            |token| format!("no accepted inbound file transfer is pending for token {token}"),
        )
    })?;
    let received_token = if transfer.direction == 0 {
        if let Some(remote_token) = pre_received_token {
            Some(remote_token)
        } else {
            // Some peers announce the token on this socket; peers that already
            // bound it in `PeerInit` may omit this optional frame.
            match time::timeout(INBOUND_TRANSFER_TOKEN_GRACE, file.receive_token()).await {
                Ok(Ok(remote_token)) => {
                    if let Some(expected_token) = token {
                        if remote_token != expected_token {
                            return Err(format!(
                            "inbound download token mismatch: expected {expected_token}, received {remote_token}"
                        ));
                        }
                    }
                    Some(remote_token)
                }
                Ok(Err(error)) => {
                    record_soulseek_diagnostic(
                        state,
                        logging::LogLevel::Warn,
                        "soulseek",
                        format!(
                            "inbound download {} from {} closed before its transfer token: {error}",
                            transfer.id,
                            peer_username
                                .map(redact_username)
                                .unwrap_or_else(|| "<unknown>".to_owned())
                        ),
                    )
                    .await;
                    return Err(format!(
                        "inbound download token receive failed for transfer {}: {error}",
                        transfer.id
                    ));
                }
                Err(_) if token.is_some() => Some(transfer.token),
                Err(_) => unreachable!("tokenless inbound transfers read a token before claiming"),
            }
        }
    } else {
        pre_received_token
    };

    // native profile's type-1 transfer manager sends the negotiated remote token
    // immediately after PeerInit.  The regular compatibility path retains
    // the historical local-token send behavior for clients that do not send
    // that framing on an incoming transfer socket.
    //
    // Current listeners decode the init frame and hand the payload over as a
    // plain connection, so this branch is only reachable when a caller
    // explicitly supplies an obfuscated `FileTransferConnection`.
    let remote_token_received = if pre_received_token.is_some() && transfer.direction == 1 {
        true
    } else if file.is_obfuscated() && transfer.direction == 1 {
        let remote_token = time::timeout(
            state.config.soulseek_connection.timeout_transfer,
            file.receive_token(),
        )
        .await
        .map_err(|_| "obfuscated inbound transfer token receive timed out".to_owned())?
        .map_err(|error| format!("obfuscated inbound transfer token receive failed: {error}"))?;
        if remote_token != transfer.token {
            return Err(format!(
                "obfuscated inbound transfer token mismatch: expected {}, received {remote_token}",
                transfer.token
            ));
        }
        true
    } else {
        false
    };

    let in_progress = {
        let mut transfers = state.transfers.write().await;
        transfers.update_status(transfer.id, "in_progress", None, None)
    };
    if let Some(in_progress) = in_progress {
        persist_transfer_projection(state, &in_progress).await;
    }

    let result = if transfer.direction == 0 {
        download_file_transfer_with_connection(state, &transfer, &mut file, received_token).await
    } else {
        upload_file_transfer_with_connection(state, &transfer, &mut file, !remote_token_received)
            .await
    };
    finish_file_transfer(state, &transfer, result).await;
    Ok(())
}

/// Whether this data socket still owns its transfer entry.
///
/// `handle_inbound_file_transfer` moves the entry to `in_progress` right before
/// it starts reading. Any other status means a queued retry, a newer attempt,
/// or a terminal outcome already owns the entry.
async fn download_data_socket_still_owned(state: &AppState, id: u64) -> bool {
    state
        .transfers
        .read()
        .await
        .entries
        .iter()
        .find(|entry| entry.id == id)
        .is_some_and(|entry| entry.status == "in_progress")
}

/// Project the outcome of a transfer that owns its socket.
///
/// The listener path ends here after `handle_inbound_file_transfer` reads the
/// last chunk; the outbound dial path projects through
/// `execute_accepted_file_transfer` instead.
pub(crate) async fn finish_file_transfer(
    state: &AppState,
    transfer: &TransferEntry,
    result: Result<(u64, u64), String>,
) {
    if let Err(error) = &result {
        record_expected_upload_failure(state, transfer, error).await;
    }
    // A download that loses its data socket is retried like slskd's
    // `Retry.Do`: the same entry returns to `queued` with the next attempt and
    // the incomplete `.part` file resumes. Cancellation, content-safety
    // rejection, and exhausted attempts stay terminal.
    if transfer.direction == 0 {
        if let Err(error) = &result {
            if transfer_is_cancelled(state, transfer.id).await {
                return;
            }
            // A stall sweep may have already requeued this transfer and a newer
            // attempt may own it now. A late socket error must not spend that
            // attempt's retry budget.
            if !download_data_socket_still_owned(state, transfer.id).await {
                return;
            }
            if !error.starts_with("download rejected by configured content safety policy")
                && requeue_peer_download(state, transfer, error).await
            {
                return;
            }
        }
    }
    let (status, bytes_transferred, size, reason) = match result {
        Ok((bytes_transferred, size)) => ("succeeded", bytes_transferred, Some(size), None),
        Err(error) => (
            "failed",
            transfer.bytes_transferred,
            transfer.size,
            Some(error),
        ),
    };
    if let Some(reason) = reason.as_deref() {
        record_soulseek_diagnostic(
            state,
            if transfer.direction == 0 {
                logging::LogLevel::Warn
            } else {
                logging::LogLevel::Info
            },
            "soulseek",
            format!(
                "inbound {} {} for {} ended {status}: {reason}",
                if transfer.direction == 0 {
                    "download"
                } else {
                    "upload"
                },
                transfer.id,
                transfer
                    .peer_username
                    .as_deref()
                    .map(redact_username)
                    .unwrap_or_else(|| "<unknown>".to_owned()),
            ),
        )
        .await;
    }

    let updated = {
        let mut transfers = state.transfers.write().await;
        transfers.update_local_execution(transfer.id, status, bytes_transferred, size, reason)
    };
    if let Some(updated) = updated {
        let updated = apply_completed_download_permissions(state, updated).await;
        let updated = enrich_completed_audio_metadata(state, updated).await;
        persist_transfer_projection(state, &updated).await;
        issue_relay_download_tokens(state, &updated).await;
        maybe_import_lidarr_completed_download(state, &updated).await;
        maybe_upload_ftp_completed_download(state, &updated).await;
    }
    schedule_queued_uploads(state).await;
    schedule_queued_downloads(state).await;
}
