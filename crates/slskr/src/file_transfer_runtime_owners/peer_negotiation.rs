use super::*;

pub(crate) async fn probe_peer_capability(
    state: &AppState,
    username: &str,
) -> Result<PeerCapabilityDescriptor, String> {
    let mesh_settings = state.advanced_networking.read().await.mesh.clone();
    if !mesh_settings.enabled
        || !mesh_settings.enable_soulseek_rendezvous
        || !mesh_settings.probe_soulseek_rendezvous_capabilities
        || !mesh_settings.enable_soulseek_capability_handshake
    {
        return Err("Soulseek mesh capability probing is disabled by configuration".to_owned());
    }
    let username = username.trim();
    if username.is_empty() {
        return Err("peer capability username is required".to_owned());
    }
    let address = request_peer_endpoint(state, username).await?;
    let nonce = uuid::Uuid::new_v4().simple().to_string();
    let hello = PeerCapabilityEnvelope::new(
        PeerCapabilityMessageType::Hello,
        nonce.clone(),
        local_capability_descriptor(state).await?,
    );
    let message = peer_capability_message(&hello)
        .map_err(|error| format!("peer capability hello failed: {error}"))?;
    let response = send_peer_message_request(state, &address, message).await?;
    let Some(mut acknowledgement) = decode_peer_capability_message(&response)
        .map_err(|error| format!("peer capability acknowledgement rejected: {error}"))?
    else {
        return Err(format!(
            "expected peer capability acknowledgement, got {}",
            peer_message_name(&response)
        ));
    };
    if acknowledgement.message_type != PeerCapabilityMessageType::Acknowledge {
        return Err("peer capability response was not an acknowledgement".to_owned());
    }
    if acknowledgement.nonce != nonce {
        return Err("peer capability acknowledgement nonce did not match".to_owned());
    }
    acknowledgement.descriptor.username = username.to_owned();
    let descriptor = acknowledgement.descriptor;
    state
        .mesh
        .write()
        .await
        .update_capability(descriptor.clone())?;
    update_listeners(state, |snapshot| {
        snapshot.last_event = Some(format!(
            "peer_capability_acknowledge:{}",
            redact_username(username)
        ));
        snapshot.last_error = None;
    })
    .await;
    Ok(descriptor)
}

pub(crate) async fn execute_accepted_file_transfer(
    state: &AppState,
    address: &PeerAddress,
    transfer: &TransferEntry,
) {
    if cancel_download_if_blocked_by_policy(state, transfer)
        .await
        .is_some()
    {
        return;
    }
    if transfer
        .local_path
        .as_deref()
        .unwrap_or_default()
        .is_empty()
    {
        return;
    }

    {
        let mut transfers = state.transfers.write().await;
        if transfers
            .entries
            .iter()
            .find(|entry| entry.id == transfer.id)
            .is_some_and(|entry| entry.status == "cancelled")
        {
            return;
        }
        transfers.update_status(transfer.id, "in_progress", None, None);
    }
    persist_transfer_durability(state).await;

    let result = if transfer.direction == 1 {
        upload_file_transfer(state, address, transfer).await
    } else {
        download_file_transfer_with_retry(state, address, transfer).await
    };
    if transfer_is_cancelled(state, transfer.id).await {
        return;
    }
    if let Err(error) = &result {
        record_expected_upload_failure(state, transfer, error).await;
    }
    let (status, bytes_transferred, size, reason) = match result {
        Ok((bytes_transferred, size)) => ("succeeded", bytes_transferred, Some(size), None),
        Err(error) => {
            if let Some(username) = transfer.peer_username.clone() {
                let indirect_pending = {
                    let mut transfers = state.transfers.write().await;
                    transfers.update_status(
                        transfer.id,
                        "indirect_pending",
                        None,
                        Some(format!("direct file-transfer failed: {error}")),
                    )
                };
                if let Some(indirect_pending) = indirect_pending {
                    persist_transfer_projection(state, &indirect_pending).await;
                }
                if let Err(error) = try_send_session_command(
                    state,
                    SessionCommand::IndirectTransfer {
                        id: transfer.id,
                        username,
                        token: transfer.token,
                    },
                ) {
                    let failed = {
                        let mut transfers = state.transfers.write().await;
                        transfers.update_status(
                            transfer.id,
                            "failed",
                            None,
                            Some(format!("indirect transfer dispatch failed: {error}")),
                        )
                    };
                    if let Some(failed) = failed {
                        persist_transfer_projection(state, &failed).await;
                    }
                    update_session(state, |snapshot| {
                        snapshot.last_error = Some(format!(
                            "indirect transfer {} dispatch failed: {error}",
                            transfer.id
                        ));
                    })
                    .await;
                }
                return;
            }
            (
                "failed",
                transfer.bytes_transferred,
                transfer.size,
                Some(error),
            )
        }
    };

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

pub(crate) async fn project_indirect_transfer_response(
    state: &AppState,
    response: &ConnectToPeerResponse,
) {
    let Ok(kind) = ConnectionKind::try_from_connection_type(&response.connection_type) else {
        return;
    };
    if kind != ConnectionKind::FileTransfer {
        return;
    }
    let transfer = {
        let transfers = state.transfers.read().await;
        transfers.pending_indirect_transfer(&response.username, response.token)
    };
    let Some(transfer) = transfer else {
        return;
    };
    let in_progress = {
        let mut transfers = state.transfers.write().await;
        if transfers
            .entries
            .iter()
            .find(|entry| entry.id == transfer.id)
            .is_some_and(|entry| entry.status == "cancelled")
        {
            return;
        }
        transfers.update_status(transfer.id, "in_progress", None, None)
    };
    if let Some(in_progress) = in_progress {
        persist_transfer_projection(state, &in_progress).await;
    }

    let result = execute_indirect_file_transfer(state, response, &transfer).await;
    if transfer_is_cancelled(state, transfer.id).await {
        return;
    }
    if let Err(error) = &result {
        record_expected_upload_failure(state, &transfer, error).await;
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
    let updated = {
        let mut transfers = state.transfers.write().await;
        transfers.update_local_execution(transfer.id, status, bytes_transferred, size, reason)
    };
    if let Some(updated) = updated {
        let updated = enrich_completed_audio_metadata(state, updated).await;
        persist_transfer_projection(state, &updated).await;
        issue_relay_download_tokens(state, &updated).await;
        maybe_import_lidarr_completed_download(state, &updated).await;
        maybe_upload_ftp_completed_download(state, &updated).await;
    }
    schedule_queued_uploads(state).await;
    schedule_queued_downloads(state).await;
}

pub(crate) async fn project_peer_transfer_response(state: &AppState, address: &PeerAddress) {
    let transfer = {
        let transfers = state.transfers.read().await;
        transfers.pending_peer_transfer(&address.username)
    };
    let Some(transfer) = transfer else {
        return;
    };
    if cancel_download_if_blocked_by_policy(state, &transfer)
        .await
        .is_some()
    {
        return;
    }
    let download_slots =
        usize::try_from(state.transfer_download_settings.read().await.slots).unwrap_or(usize::MAX);
    let transition = {
        let mut transfers = state.transfers.write().await;
        transfers.claim_pending_peer_transfer(
            transfer.id,
            state.config.transfer_max_active,
            download_slots,
        )
    };
    let Some(transition) = transition else {
        return;
    };
    persist_transfer_projection(state, &transition).await;
    if transition.status == "queued" {
        return;
    }

    if transfer.direction == 0 {
        project_peer_download_response(state, address, &transfer).await;
        return;
    }

    let result = negotiate_peer_transfer(state, address, &transfer).await;
    let (status, bytes_transferred, reason) = match result {
        Ok(PeerTransferNegotiation::Allowed { token, size }) if token == transfer.token => {
            let transferred = transfer.bytes_transferred;
            let size = size.or(transfer.size);
            let accepted = {
                let mut transfers = state.transfers.write().await;
                transfers.update_local_execution(transfer.id, "accepted", transferred, size, None)
            };
            if let Some(accepted) = accepted {
                persist_transfer_projection(state, &accepted).await;
                execute_accepted_file_transfer(state, address, &accepted).await;
            }
            return;
        }
        Ok(PeerTransferNegotiation::QueuedInbound { token, size }) => {
            let accepted_result = {
                let mut transfers = state.transfers.write().await;
                transfers.accept_queued_inbound_negotiation(transfer.id, token, size)
            };
            let accepted = match accepted_result {
                Ok(accepted) => accepted,
                Err(error) => {
                    let failed = {
                        let mut transfers = state.transfers.write().await;
                        transfers.update_status(transfer.id, "failed", None, Some(error))
                    };
                    if let Some(failed) = failed {
                        persist_transfer_projection(state, &failed).await;
                    }
                    return;
                }
            };
            if let Some(accepted) = accepted {
                persist_transfer_projection(state, &accepted).await;
            } else {
                let failed = {
                    let mut transfers = state.transfers.write().await;
                    transfers.update_status(
                        transfer.id,
                        "failed",
                        None,
                        Some("queued transfer is no longer pending".to_owned()),
                    )
                };
                if let Some(failed) = failed {
                    persist_transfer_projection(state, &failed).await;
                }
            }
            return;
        }
        Ok(PeerTransferNegotiation::Allowed { token, .. }) => (
            "failed",
            None,
            Some(format!(
                "transfer token mismatch: expected {}, received {token}",
                transfer.token
            )),
        ),
        Ok(PeerTransferNegotiation::Rejected { token, reason }) if token == transfer.token => {
            if is_remote_queue_response(&reason) {
                ("queued", None, Some(reason))
            } else {
                ("failed", None, Some(reason))
            }
        }
        Ok(PeerTransferNegotiation::Rejected { token, .. }) => (
            "failed",
            None,
            Some(format!(
                "transfer token mismatch: expected {}, received {token}",
                transfer.token
            )),
        ),
        Err(error) => ("failed", None, Some(error)),
    };

    let updated = {
        let mut transfers = state.transfers.write().await;
        let pending = transfers.entries.iter().any(|entry| {
            entry.id == transfer.id
                && entry.token == transfer.token
                && entry.status == "peer_negotiating"
        });
        if pending {
            transfers.update_status(transfer.id, status, bytes_transferred, reason)
        } else {
            None
        }
    };
    if let Some(updated) = updated {
        persist_transfer_projection(state, &updated).await;
    }
    if status != "queued" {
        schedule_queued_uploads(state).await;
    }
    schedule_queued_downloads(state).await;
}

/// Project the modern `QueueUpload` download negotiation.
///
/// Uploaders answer `QueueUpload` with `TransferRequest { direction: 1 }` and
/// then dial us. Nothing here sends `TransferRequest { direction: 0 }` or dials
/// the uploader: that legacy flow is silently ignored by current peers.
async fn project_peer_download_response(
    state: &AppState,
    address: &PeerAddress,
    transfer: &TransferEntry,
) {
    // The modern flow requires the peer to dial our listener, so a disabled
    // inbound transfer setting is permanent and must not burn the retry
    // budget on a transport classification.
    if !state.config.transfer_allow_inbound {
        fail_peer_download(
            state,
            transfer,
            "inbound file transfers are disabled, so peers cannot deliver queued downloads"
                .to_owned(),
        )
        .await;
        return;
    }
    let peer = redact_username(&address.username);
    match negotiate_peer_download(state, address, transfer).await {
        Ok(PeerDownloadNegotiation::Offer { token, size, place }) => {
            // `negotiate_peer_download` promoted the entry to `accepted` before
            // telling the peer to dial, so only the projection is left.
            let accepted = {
                let transfers = state.transfers.read().await;
                transfers
                    .entries
                    .iter()
                    .find(|entry| entry.id == transfer.id)
                    .cloned()
            };
            if let Some(accepted) = accepted {
                persist_transfer_projection(state, &accepted).await;
            }
            let place = match place {
                Some(place) => format!(", queue position {place}"),
                None => String::new(),
            };
            record_daemon_log(
                state,
                logging::LogLevel::Info,
                "transfers",
                format!(
                    "peer {peer} offered {} ({} bytes, token {token}{place}); waiting for the inbound connection",
                    transfer.filename,
                    size.or(transfer.size).unwrap_or(0)
                ),
            )
            .await;
        }
        Ok(PeerDownloadNegotiation::Queued { place }) => {
            // A slow or lost attempt must not downgrade a transfer another
            // socket already accepted; only the attempt that still owns the
            // entry may move it back to `queued`.
            if !download_negotiation_still_owned(state, transfer.id).await {
                return;
            }
            let updated = {
                let mut transfers = state.transfers.write().await;
                transfers.update_status(transfer.id, "queued", None, Some("Queued".to_owned()))
            };
            if let Some(updated) = updated {
                persist_transfer_projection(state, &updated).await;
            }
            let place = match place {
                Some(place) => format!(", queue position {place}"),
                None => String::new(),
            };
            record_daemon_log(
                state,
                logging::LogLevel::Info,
                "transfers",
                format!(
                    "peer {peer} kept {} queued{place}; waiting for the peer to offer it",
                    transfer.filename
                ),
            )
            .await;
        }
        Ok(PeerDownloadNegotiation::Rejected { reason }) => {
            if !download_negotiation_still_owned(state, transfer.id).await {
                return;
            }
            // slskd treats an explicit rejection (file not shared, denied,
            // duplicate) as final; only transport failures are retried.
            fail_peer_download(state, transfer, reason).await;
        }
        Err(error) => {
            if !download_negotiation_still_owned(state, transfer.id).await {
                return;
            }
            if requeue_peer_download(state, transfer, &error).await {
                return;
            }
            fail_peer_download(state, transfer, error).await;
        }
    }
}

/// Whether this negotiation attempt still owns the transfer entry.
///
/// Once another socket accepted the file (`accepted`/`in_progress`) a late
/// timeout or disconnect from a slower attempt must not move it back.
async fn download_negotiation_still_owned(state: &AppState, id: u64) -> bool {
    state
        .transfers
        .read()
        .await
        .entries
        .iter()
        .find(|entry| entry.id == id)
        .is_some_and(|entry| {
            matches!(
                entry.status.as_str(),
                "peer_lookup" | "peer_negotiating" | "queued"
            )
        })
}

/// Requeue a download whose attempt failed, mirroring slskd's `Retry.Do`.
///
/// slskd keeps the transfer in `Queued | Locally`, waits an exponential
/// backoff (`download.retry.delay` capped by `max_delay`), and retries the
/// same transfer until `download.retry.attempts` is exhausted. Returns `false`
/// when no attempts remain, so the caller can record the final failure.
pub(crate) async fn requeue_peer_download(
    state: &AppState,
    transfer: &TransferEntry,
    reason: &str,
) -> bool {
    let retry = state.transfer_download_settings.read().await.retry.clone();
    let attempts = transfer.attempts.max(1);
    if attempts >= retry.attempts.max(1) {
        return false;
    }
    let delay = download_retry_delay(&retry, attempts);
    let next_attempt_at = unix_timestamp().saturating_add(delay.as_secs().max(1));
    let requeued = {
        let mut transfers = state.transfers.write().await;
        // Never resurrect a transfer that another task already finished or
        // that the user cancelled while this attempt was in flight.
        if !transfers
            .entries
            .iter()
            .any(|entry| entry.id == transfer.id && !is_terminal_transfer_status(&entry.status))
        {
            return true;
        }
        transfers.update_retry_state(
            transfer.id,
            attempts.saturating_add(1),
            Some(next_attempt_at),
            "queued",
            Some(reason.to_owned()),
        )
    };
    let Some(requeued) = requeued else {
        return true;
    };
    persist_transfer_projection(state, &requeued).await;
    record_daemon_log(
        state,
        logging::LogLevel::Info,
        "transfers",
        format!(
            "download {} from {} failed: {reason}; queued for retry attempt {}/{} in {}s",
            transfer.filename,
            transfer
                .peer_username
                .as_deref()
                .map(redact_username)
                .unwrap_or_else(|| "<unknown>".to_owned()),
            attempts.saturating_add(1),
            retry.attempts.max(1),
            delay.as_secs().max(1),
        ),
    )
    .await;
    true
}

/// Fail downloads that the peer accepted but never opened a file-transfer
/// socket for.
///
/// A peer can answer `QueueUpload` with an offer, take our `Allowed`, and then
/// never dial (or dial and disappear before a byte arrives). Without this sweep
/// the entry sits in `accepted` forever and keeps a download slot, so the rest
/// of the queue never starts.
pub(crate) async fn expire_stalled_download_negotiations(state: &AppState) -> usize {
    let now = unix_timestamp();
    let stall = state
        .config
        .soulseek_connection
        .timeout_transfer
        .max(Duration::from_secs(30))
        .as_secs();
    let stalled: Vec<TransferEntry> = {
        let transfers = state.transfers.read().await;
        transfers
            .entries
            .iter()
            .filter(|entry| {
                // `in_progress` with no bytes is also a stall: a restart can
                // rehydrate a transfer whose negotiation task is gone, and a
                // retry can claim a peer address that never answers. Real
                // transfers refresh `updated_at` as chunks land; a connected
                // socket that stays silent is already bounded by the transfer
                // read timeout, so failing here is not more aggressive.
                entry.direction == 0
                    && match entry.status.as_str() {
                        "accepted" => now.saturating_sub(entry.updated_at) >= stall,
                        "in_progress" => {
                            entry.bytes_transferred == 0
                                && now.saturating_sub(entry.updated_at) >= stall
                        }
                        _ => false,
                    }
            })
            .cloned()
            .collect()
    };
    let mut expired = 0;
    for entry in stalled {
        let reason = if entry.status == "in_progress" {
            "download stalled before any data arrived"
        } else {
            "peer did not open a file-transfer connection in time"
        };
        if requeue_peer_download(state, &entry, reason).await {
            expired += 1;
            continue;
        }
        let failed = {
            let mut transfers = state.transfers.write().await;
            transfers.update_status(entry.id, "failed", None, Some(reason.to_owned()))
        };
        if let Some(failed) = failed {
            expired += 1;
            persist_transfer_projection(state, &failed).await;
            record_daemon_log(
                state,
                logging::LogLevel::Warn,
                "transfers",
                format!(
                    "download {} from {} stalled ({reason}); releasing its slot",
                    entry.filename,
                    entry
                        .peer_username
                        .as_deref()
                        .map(redact_username)
                        .unwrap_or_else(|| "<unknown>".to_owned())
                ),
            )
            .await;
        }
    }
    if expired > 0 {
        schedule_queued_downloads(state).await;
    }
    expired
}

async fn fail_peer_download(state: &AppState, transfer: &TransferEntry, reason: String) {
    let failed = {
        let mut transfers = state.transfers.write().await;
        transfers.update_status(transfer.id, "failed", None, Some(reason.clone()))
    };
    if let Some(failed) = failed {
        persist_transfer_projection(state, &failed).await;
    }
    record_daemon_log(
        state,
        logging::LogLevel::Warn,
        "transfers",
        format!(
            "download {} from {} failed during negotiation: {reason}",
            transfer.filename,
            transfer
                .peer_username
                .as_deref()
                .map(redact_username)
                .unwrap_or_else(|| "<unknown>".to_owned())
        ),
    )
    .await;
    schedule_queued_downloads(state).await;
}

pub(crate) async fn schedule_queued_downloads(state: &AppState) {
    schedule_queued_downloads_inner(state, false).await;
}

/// Re-ask peers for downloads that were waiting in their remote queue when the
/// session ended.
///
/// The periodic scheduler deliberately leaves remote-queued entries alone: the
/// peer owns the queue and will offer the file. After a reconnect the old
/// `QueueUpload` may be gone, so login replay refreshes it once instead of
/// leaving the transfer queued forever.
pub(crate) async fn resume_queued_downloads_after_login(state: &AppState) {
    schedule_queued_downloads_inner(state, true).await;
}

async fn schedule_queued_downloads_inner(state: &AppState, include_remote_queued: bool) {
    loop {
        let now = unix_timestamp();
        let download_slots = usize::try_from(state.transfer_download_settings.read().await.slots)
            .unwrap_or(usize::MAX);
        if !download_capacity_available(state, None).await {
            return;
        }
        let queued = {
            let mut transfers = state.transfers.write().await;
            let active_count = transfers.active_count_excluding(None);
            let active_downloads = transfers
                .entries
                .iter()
                .filter(|entry| entry.direction == 0 && is_active_transfer_status(&entry.status))
                .count();
            if active_count >= state.config.transfer_max_active
                || active_downloads >= download_slots
            {
                return;
            }
            let next = transfers
                .entries
                .iter()
                .filter(|entry| {
                    entry.direction == 0
                        && entry.status == "queued"
                        // Without a peer or destination there is nothing to
                        // negotiate; promoting these would strand them in
                        // `peer_lookup`, which counts as an active download.
                        && entry.peer_username.is_some()
                        && entry.local_path.is_some()
                        && (include_remote_queued
                            || !entry
                                .reason
                                .as_deref()
                                .is_some_and(is_remote_queue_response))
                        // A retry queued after a failed attempt sleeps until
                        // its backoff elapses; the periodic scheduler wakes it.
                        && entry.next_attempt_at.is_none_or(|at| at <= now)
                })
                .min_by_key(|entry| (entry.requested_at, entry.id))
                .cloned();
            next.and_then(|entry| {
                transfers.update_retry_state(entry.id, entry.attempts, None, "peer_lookup", None)
            })
        };
        let Some(queued) = queued else {
            return;
        };
        persist_transfer_projection(state, &queued).await;
        let Some(username) = queued.peer_username.as_deref() else {
            continue;
        };
        if let Some(address) = cached_peer_endpoint(state, username).await {
            Box::pin(project_peer_transfer_response(state, &address)).await;
        } else if try_send_session_command(
            state,
            SessionCommand::TransferPeer {
                id: queued.id,
                username: username.to_owned(),
            },
        )
        .is_err()
        {
            let failed = state.transfers.write().await.update_status(
                queued.id,
                "failed",
                None,
                Some("download peer lookup dispatch failed".to_owned()),
            );
            if let Some(failed) = failed {
                persist_transfer_projection(state, &failed).await;
            }
        }
    }
}
