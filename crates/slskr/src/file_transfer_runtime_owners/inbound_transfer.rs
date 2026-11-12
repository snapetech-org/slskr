use super::*;

pub(crate) async fn handle_inbound_file_transfer(
    state: &AppState,
    mut file: slskr_client::file_transfer::FileTransferConnection<TcpStream>,
    token: Option<u32>,
    peer_username: Option<&str>,
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
    let mut transfer = {
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
        if let Some(token) = token {
            Some(token)
        } else {
            let remote_token = time::timeout(
                state.config.soulseek_connection.timeout_transfer,
                file.receive_token(),
            )
            .await
            .map_err(|_| "inbound download token receive timed out".to_owned())?
            .map_err(|error| format!("inbound download token receive failed: {error}"))?;
            transfer = {
                let mut transfers = state.transfers.write().await;
                transfers
                    .claim_pending_inbound_file_transfer(
                        Some(remote_token),
                        peer_username,
                        state.config.transfer_max_active,
                        download_slots,
                    )
                    .filter(|entry| entry.direction == 0)
            }
            .ok_or_else(|| {
                format!("no accepted inbound download is pending for token {remote_token}")
            })?;
            Some(remote_token)
        }
    } else {
        None
    };

    // native profile's type-1 transfer manager sends the negotiated remote token
    // immediately after PeerInit.  The regular compatibility path retains
    // the historical local-token send behavior for clients that do not send
    // that framing on an incoming transfer socket.
    let remote_token_received = if file.is_obfuscated() && transfer.direction == 1 {
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
        let updated = apply_completed_download_permissions(state, updated).await;
        let updated = enrich_completed_audio_metadata(state, updated).await;
        persist_transfer_projection(state, &updated).await;
        issue_relay_download_tokens(state, &updated).await;
        maybe_import_lidarr_completed_download(state, &updated).await;
        maybe_upload_ftp_completed_download(state, &updated).await;
    }
    schedule_queued_uploads(state).await;
    schedule_queued_downloads(state).await;
    Ok(())
}
