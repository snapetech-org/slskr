//! Controller full transfer start/queue-promotion contracts.
//!
//! A download is only negotiated once its entry reaches `peer_lookup`; the
//! peer-address response handler refuses every other status. These contracts
//! pin the promotion rules for downloads that clients enqueue, downloads that
//! survive a restart, and downloads the remote peer has queued on its side.

use super::*;

fn drain_commands(
    receiver: &mut tokio::sync::mpsc::Receiver<crate::SessionCommand>,
) -> Vec<String> {
    let mut usernames = Vec::new();
    while let Ok(command) = receiver.try_recv() {
        if let crate::SessionCommand::TransferPeer { username, .. } = command {
            usernames.push(username);
        }
    }
    usernames
}

async fn status_of(state: &std::sync::Arc<crate::AppState>, id: u64) -> String {
    let transfers = state.transfers.read().await;
    transfers
        .entries
        .iter()
        .find(|entry| entry.id == id)
        .map(|entry| entry.status.clone())
        .expect("transfer entry")
}

#[cfg_attr(test, tokio::test)]
#[cfg(feature = "full-controller-tests")]
pub(super) async fn transfers_route_starts_the_downloads_it_accepts() {
    let (state, mut receiver) = test_state();
    let response = crate::route_http_request(
        "POST",
        "/api/transfers",
        None,
        r#"{"username":"friend","files":[{"filename":"Music/Start.flac","size":42}]}"#,
        &state,
    )
    .await
    .expect("enqueue transfer");
    assert_eq!(response.status, "200 OK");

    assert_eq!(drain_commands(&mut receiver), vec!["friend".to_owned()]);
    let transfers = state.transfers.read().await;
    assert_eq!(transfers.entries.len(), 1);
    assert_eq!(transfers.entries[0].status, "peer_lookup");
    assert_eq!(transfers.entries[0].direction, 0);
}

#[cfg_attr(test, tokio::test)]
#[cfg(feature = "full-controller-tests")]
pub(super) async fn transfers_route_leaves_downloads_queued_when_slots_are_exhausted() {
    let (state, mut receiver) = test_state();
    state.transfer_download_settings.write().await.slots = 1;
    {
        let mut transfers = state.transfers.write().await;
        let busy = transfers.create(
            0,
            Some("busy".to_owned()),
            "Remote/Busy.flac".to_owned(),
            Some("busy".to_owned()),
            Some(1),
        );
        transfers.update_status(busy.id, "in_progress", None, None);
    }

    let response = crate::route_http_request(
        "POST",
        "/api/transfers",
        None,
        r#"{"username":"friend","files":[{"filename":"Music/Waiting.flac","size":42}]}"#,
        &state,
    )
    .await
    .expect("enqueue transfer");
    assert_eq!(response.status, "200 OK");
    assert!(drain_commands(&mut receiver).is_empty());

    let waiting_id = {
        let transfers = state.transfers.read().await;
        transfers
            .entries
            .iter()
            .find(|entry| entry.peer_username.as_deref() == Some("friend"))
            .map(|entry| entry.id)
            .expect("waiting transfer")
    };
    assert_eq!(status_of(&state, waiting_id).await, "queued");

    {
        let mut transfers = state.transfers.write().await;
        let busy_id = transfers
            .entries
            .iter()
            .find(|entry| entry.peer_username.as_deref() == Some("busy"))
            .map(|entry| entry.id)
            .expect("busy transfer");
        transfers.update_status(busy_id, "succeeded", Some(1), None);
    }
    crate::schedule_queued_downloads(&state).await;
    assert_eq!(drain_commands(&mut receiver), vec!["friend".to_owned()]);
    assert_eq!(status_of(&state, waiting_id).await, "peer_lookup");
}

#[cfg_attr(test, tokio::test)]
#[cfg(feature = "full-controller-tests")]
pub(super) async fn scheduler_promotes_downloads_restored_after_restart() {
    let (state, mut receiver) = test_state();
    let id = {
        let mut transfers = state.transfers.write().await;
        let entry = transfers.create(
            0,
            Some("friend".to_owned()),
            "Remote/Restored.flac".to_owned(),
            Some("restored".to_owned()),
            Some(4),
        );
        transfers
            .update_status(
                entry.id,
                "queued",
                None,
                Some("resumed after restart".to_owned()),
            )
            .expect("queue restored transfer")
            .id
    };

    crate::schedule_queued_downloads(&state).await;

    assert_eq!(drain_commands(&mut receiver), vec!["friend".to_owned()]);
    assert_eq!(status_of(&state, id).await, "peer_lookup");
}

#[cfg_attr(test, tokio::test)]
#[cfg(feature = "full-controller-tests")]
pub(super) async fn scheduler_promotes_reasonless_queued_downloads() {
    let (state, mut receiver) = test_state();
    let id = {
        let mut transfers = state.transfers.write().await;
        let entry = transfers.create(
            0,
            Some("friend".to_owned()),
            "Remote/Rehydrated.flac".to_owned(),
            Some("rehydrated".to_owned()),
            Some(4),
        );
        assert_eq!(entry.status, "queued");
        assert!(entry.reason.is_none());
        entry.id
    };

    crate::schedule_queued_downloads(&state).await;

    assert_eq!(drain_commands(&mut receiver), vec!["friend".to_owned()]);
    assert_eq!(status_of(&state, id).await, "peer_lookup");
}

#[cfg_attr(test, tokio::test)]
#[cfg(feature = "full-controller-tests")]
pub(super) async fn scheduler_keeps_remote_queued_downloads_waiting_on_the_peer() {
    let (state, mut receiver) = test_state();
    let id = {
        let mut transfers = state.transfers.write().await;
        let entry = transfers.create(
            0,
            Some("friend".to_owned()),
            "Remote/RemoteQueued.flac".to_owned(),
            Some("remote-queued".to_owned()),
            Some(4),
        );
        transfers
            .update_status(entry.id, "queued", None, Some("Queued".to_owned()))
            .expect("remote queue response")
            .id
    };

    crate::schedule_queued_downloads(&state).await;

    assert!(drain_commands(&mut receiver).is_empty());
    assert_eq!(status_of(&state, id).await, "queued");
}

#[cfg_attr(test, tokio::test)]
#[cfg(feature = "full-controller-tests")]
pub(super) async fn login_replay_promotes_queued_downloads() {
    let (state, mut receiver) = test_state();
    let id = {
        let mut transfers = state.transfers.write().await;
        let entry = transfers.create(
            0,
            Some("friend".to_owned()),
            "Remote/AfterLogin.flac".to_owned(),
            Some("after-login".to_owned()),
            Some(4),
        );
        entry.id
    };

    crate::session_runtime::dispatch_queued_downloads_after_login(&state).await;

    assert_eq!(drain_commands(&mut receiver), vec!["friend".to_owned()]);
    assert_eq!(status_of(&state, id).await, "peer_lookup");
}

/// The web UI enqueues downloads through `POST /transfers/downloads/{user}`
/// (`web/src/lib/transfers.js`), not through `POST /transfers`. If this route
/// leaves entries `queued` the UI shows "Queued" forever and nothing is ever
/// negotiated.
#[cfg_attr(test, tokio::test)]
#[cfg(feature = "full-controller-tests")]
pub(super) async fn user_download_route_starts_the_downloads_it_accepts() {
    let (state, mut receiver) = test_state();
    let response = crate::route_http_request(
        "POST",
        "/api/transfers/downloads/friend",
        None,
        r#"[{"filename":"Music/FromUi.flac","size":42}]"#,
        &state,
    )
    .await
    .expect("enqueue transfer");
    assert_eq!(response.status, "200 OK");

    assert_eq!(drain_commands(&mut receiver), vec!["friend".to_owned()]);
    let transfers = state.transfers.read().await;
    assert_eq!(transfers.entries.len(), 1);
    assert_eq!(transfers.entries[0].status, "peer_lookup");
    assert_eq!(transfers.entries[0].direction, 0);
}

/// The slskd-compatible mirror of the same route.
#[cfg_attr(test, tokio::test)]
#[cfg(feature = "full-controller-tests")]
pub(super) async fn versioned_user_download_route_starts_the_downloads_it_accepts() {
    let (state, mut receiver) = test_state();
    let response = crate::route_http_request(
        "POST",
        "/api/v0/transfers/downloads/friend",
        None,
        r#"[{"filename":"Music/FromUiV0.flac","size":42}]"#,
        &state,
    )
    .await
    .expect("enqueue transfer");
    assert_eq!(response.status, "200 OK");

    assert_eq!(drain_commands(&mut receiver), vec!["friend".to_owned()]);
    let transfers = state.transfers.read().await;
    assert_eq!(transfers.entries.len(), 1);
    assert_eq!(transfers.entries[0].status, "peer_lookup");
}

/// A single-transfer create is a documented staging step: it must not start
/// anything until `POST /transfers/{id}/start` asks for it.
#[cfg_attr(test, tokio::test)]
#[cfg(feature = "full-controller-tests")]
pub(super) async fn single_transfer_create_stays_staged_until_start() {
    let (state, mut receiver) = test_state();
    let response = crate::route_http_request(
        "POST",
        "/api/transfers",
        None,
        r#"{"username":"friend","filename":"Music/Staged.flac","size":42}"#,
        &state,
    )
    .await
    .expect("create transfer");
    assert_eq!(response.status, "201 Created");

    assert!(drain_commands(&mut receiver).is_empty());
    let transfers = state.transfers.read().await;
    assert_eq!(transfers.entries.len(), 1);
    assert_eq!(transfers.entries[0].status, "queued");
}

/// Uploaders only offer files after a `QueueUpload`. The downloader must accept
/// the peer's `TransferRequest { direction: 1 }`, answer `Allowed`, and leave the
/// entry waiting for the inbound file-transfer connection instead of dialing the
/// uploader itself.
#[cfg_attr(test, tokio::test)]
#[cfg(feature = "full-controller-tests")]
pub(super) async fn download_negotiation_queues_with_the_peer_and_waits_for_its_offer() {
    use crate::PeerMessage;
    use crate::ProtocolTextEncoding;
    use crate::TransferRequest;
    use crate::TransferResponse;
    use tokio::io::AsyncWriteExt as _;

    let (state, _receiver) = test_state();
    let filename = "Music/Peer Offer.flac";
    let id = {
        let mut transfers = state.transfers.write().await;
        let entry = transfers.create_with_details(
            0,
            Some("fakepeer".to_owned()),
            filename.to_owned(),
            Some("/tmp/slskr-peer-offer.flac".to_owned()),
            Some(2048),
            None,
            crate::TransferRequestDetails {
                request_id: None,
                wishlist_item_id: None,
                request_name: None,
                destination_directory: None,
                bit_rate: None,
                sample_rate: None,
                bit_depth: None,
                length_seconds: None,
                artist: None,
                album: None,
                title: None,
                track_number: None,
                year: None,
                attempts: 1,
                auto_replace_attempts: 0,
                next_attempt_at: None,
            },
        );
        transfers.update_status(entry.id, "peer_lookup", None, None);
        entry.id
    };

    let listener = tokio::net::TcpListener::bind("127.0.0.1:0").await.unwrap();
    let port = u32::from(listener.local_addr().unwrap().port());

    let expected = filename.to_owned();
    let peer = tokio::spawn(async move {
        let (mut stream, _) = listener.accept().await.unwrap();
        let init = slskr_client::io::read_init_frame(&mut stream)
            .await
            .unwrap();
        let init = slskr_client::protocol::init::InitMessage::decode(init).unwrap();
        assert!(matches!(
            init,
            slskr_client::protocol::init::InitMessage::PeerInit { .. }
        ));

        let mut connection = slskr_client::stream::PeerMessageConnection::new(stream);
        let mut queued = false;
        while !queued {
            match connection.receive().await.unwrap() {
                PeerMessage::QueueUpload { filename } => {
                    assert_eq!(filename, expected);
                    queued = true;
                }
                PeerMessage::PlaceInQueueRequest { .. } => {}
                other => panic!("unexpected peer message before QueueUpload: {other:?}"),
            }
        }
        connection
            .send(&PeerMessage::PlaceInQueueResponse {
                filename: expected.clone(),
                place: 3,
            })
            .await
            .unwrap();
        connection
            .send(&PeerMessage::TransferRequest(TransferRequest {
                direction: 1,
                token: 4242,
                filename: expected.clone(),
                filename_encoding: ProtocolTextEncoding::Utf8,
                size: Some(2048),
            }))
            .await
            .unwrap();
        loop {
            match connection.receive().await.unwrap() {
                PeerMessage::TransferResponse(TransferResponse::Allowed { token, .. }) => {
                    assert_eq!(token, 4242);
                    break;
                }
                // Sent by us right after QueueUpload, before the offer.
                PeerMessage::PlaceInQueueRequest { .. } => {}
                other => panic!("expected Allowed transfer response, got {other:?}"),
            }
        }
        connection.into_inner().shutdown().await.ok();
    });

    let address = slskr_client::protocol::server::PeerAddress {
        username: "fakepeer".to_owned(),
        ip: std::net::Ipv4Addr::LOCALHOST,
        port,
        obfuscation_type: 0,
        obfuscated_port: 0,
    };
    crate::project_peer_transfer_response(&state, &address).await;
    peer.await.unwrap();

    let transfers = state.transfers.read().await;
    let entry = transfers
        .entries
        .iter()
        .find(|entry| entry.id == id)
        .expect("transfer entry");
    assert_eq!(entry.status, "accepted");
    assert_eq!(entry.token, 4242);
    assert!(entry.reason.is_none());
}

/// Peers behind NAT publish an endpoint nobody can dial. The downloader must
/// ask the server to broker the connection so the peer dials us, then negotiate
/// `QueueUpload` over that inbound socket.
#[cfg_attr(test, tokio::test)]
#[cfg(feature = "full-controller-tests")]
pub(super) async fn download_negotiation_falls_back_to_a_server_brokered_connection() {
    use crate::PeerMessage;
    use crate::ProtocolTextEncoding;
    use crate::TransferRequest;
    use crate::TransferResponse;

    let (state, mut receiver) = test_state();
    let filename = "Music/Brokered.flac";
    let id = {
        let mut transfers = state.transfers.write().await;
        let entry = transfers.create_with_details(
            0,
            Some("fakepeer".to_owned()),
            filename.to_owned(),
            Some("/tmp/slskr-brokered.flac".to_owned()),
            Some(2048),
            None,
            crate::TransferRequestDetails {
                request_id: None,
                wishlist_item_id: None,
                request_name: None,
                destination_directory: None,
                bit_rate: None,
                sample_rate: None,
                bit_depth: None,
                length_seconds: None,
                artist: None,
                album: None,
                title: None,
                track_number: None,
                year: None,
                attempts: 1,
                auto_replace_attempts: 0,
                next_attempt_at: None,
            },
        );
        transfers.update_status(entry.id, "peer_lookup", None, None);
        entry.id
    };

    let listener = tokio::net::TcpListener::bind("127.0.0.1:0").await.unwrap();
    let listener_addr = listener.local_addr().unwrap();
    let expected = filename.to_owned();
    let peer_state = std::sync::Arc::clone(&state);
    let peer = tokio::spawn(async move {
        // Wait until the downloader registers the brokered connection and asks
        // the server for it.
        let mut token = None;
        for _ in 0..2_000 {
            if let Ok(command) = receiver.try_recv() {
                if let crate::SessionCommand::IndirectPeerMessage { token: sent, .. } = command {
                    token = Some(sent);
                    break;
                }
            }
            tokio::time::sleep(std::time::Duration::from_millis(5)).await;
        }
        let token = token.expect("indirect peer message request");
        let pending = crate::take_pending_indirect_peer_download(&peer_state, token)
            .expect("pending indirect download");
        assert_eq!(pending.transfer_id, id);

        // The peer dials the downloader and hands the socket over, exactly like
        // the listener does for an inbound `PierceFirewall` connection.
        let peer_stream = tokio::net::TcpStream::connect(listener_addr).await.unwrap();
        let (inbound, _) = listener.accept().await.unwrap();
        pending.connection.send(inbound).unwrap();

        let mut connection = slskr_client::stream::PeerMessageConnection::new(peer_stream);
        let mut queued = false;
        while !queued {
            match connection.receive().await.unwrap() {
                PeerMessage::QueueUpload { filename } => {
                    assert_eq!(filename, expected);
                    queued = true;
                }
                PeerMessage::PlaceInQueueRequest { .. } => {}
                other => panic!("unexpected peer message before QueueUpload: {other:?}"),
            }
        }
        connection
            .send(&PeerMessage::TransferRequest(TransferRequest {
                direction: 1,
                token: 5150,
                filename: expected.clone(),
                filename_encoding: ProtocolTextEncoding::Utf8,
                size: Some(2048),
            }))
            .await
            .unwrap();
        loop {
            match connection.receive().await.unwrap() {
                PeerMessage::TransferResponse(TransferResponse::Allowed { token, .. }) => {
                    assert_eq!(token, 5150);
                    break;
                }
                PeerMessage::PlaceInQueueRequest { .. } => {}
                other => panic!("expected Allowed transfer response, got {other:?}"),
            }
        }
    });

    // Port 1 on loopback refuses immediately, so the direct dial cannot work and
    // the negotiation has to fall back to the server-brokered path.
    let address = slskr_client::protocol::server::PeerAddress {
        username: "fakepeer".to_owned(),
        ip: std::net::Ipv4Addr::LOCALHOST,
        port: 1,
        obfuscation_type: 0,
        obfuscated_port: 0,
    };
    crate::project_peer_transfer_response(&state, &address).await;
    peer.await.unwrap();

    let transfers = state.transfers.read().await;
    let entry = transfers
        .entries
        .iter()
        .find(|entry| entry.id == id)
        .expect("transfer entry");
    assert_eq!(entry.status, "accepted");
    assert_eq!(entry.token, 5150);
    assert!(entry.reason.is_none());
}

/// A restarted/replaced negotiation task can leave a zero-byte `in_progress`
/// download without an owner. This sweep must release the slot, but it must not
/// touch transfers that already moved bytes or that are still inside the stall
/// window.
#[cfg_attr(test, tokio::test)]
#[cfg(feature = "full-controller-tests")]
pub(super) async fn stalled_download_sweep_releases_only_zero_byte_in_progress_entries() {
    let (state, _receiver) = test_state();
    let now = crate::unix_timestamp();
    let stall = state.config.soulseek_connection.timeout_transfer.as_secs() + 60;
    let (stalled_id, fresh_id, moved_id) = {
        let mut transfers = state.transfers.write().await;
        let stalled = transfers.create(
            0,
            Some("stalled".to_owned()),
            "Music/Stalled.flac".to_owned(),
            Some("/tmp/slskr-stalled.flac".to_owned()),
            Some(2048),
        );
        let stalled_id = stalled.id;
        transfers.update_status(stalled_id, "in_progress", None, None);

        let fresh = transfers.create(
            0,
            Some("fresh".to_owned()),
            "Music/Fresh.flac".to_owned(),
            Some("/tmp/slskr-fresh.flac".to_owned()),
            Some(2048),
        );
        let fresh_id = fresh.id;
        transfers.update_status(fresh_id, "in_progress", None, None);

        let moved = transfers.create(
            0,
            Some("moved".to_owned()),
            "Music/Moved.flac".to_owned(),
            Some("/tmp/slskr-moved.flac".to_owned()),
            Some(2048),
        );
        let moved_id = moved.id;
        transfers.update_status(moved_id, "in_progress", Some(512), None);

        for entry in transfers.entries.iter_mut() {
            match entry.id {
                id if id == stalled_id || id == moved_id => {
                    entry.updated_at = now.saturating_sub(stall);
                }
                _ => {}
            }
        }
        (stalled_id, fresh_id, moved_id)
    };

    assert_eq!(crate::expire_stalled_download_negotiations(&state).await, 1);

    let retry_attempts = state.transfer_download_settings.read().await.retry.attempts;
    {
        let transfers = state.transfers.read().await;
        let stalled = transfers
            .entries
            .iter()
            .find(|entry| entry.id == stalled_id)
            .expect("stalled entry");
        assert_eq!(stalled.status, "queued");
        assert_eq!(stalled.attempts, 2);
        assert!(stalled.next_attempt_at.is_some());
        assert_eq!(
            stalled.reason.as_deref(),
            Some("download stalled before any data arrived")
        );
        let fresh = transfers
            .entries
            .iter()
            .find(|entry| entry.id == fresh_id)
            .expect("fresh entry");
        assert_eq!(fresh.status, "in_progress");
        let moved = transfers
            .entries
            .iter()
            .find(|entry| entry.id == moved_id)
            .expect("moved entry");
        assert_eq!(moved.status, "in_progress");
    }

    // Once the configured attempts are spent the sweep records the final
    // failure instead of requeueing again.
    {
        let mut transfers = state.transfers.write().await;
        let stalled = transfers
            .entries
            .iter_mut()
            .find(|entry| entry.id == stalled_id)
            .expect("stalled entry");
        stalled.attempts = retry_attempts;
        stalled.updated_at = now.saturating_sub(stall);
        stalled.status = "accepted".to_owned();
    }
    assert_eq!(crate::expire_stalled_download_negotiations(&state).await, 1);
    let transfers = state.transfers.read().await;
    let stalled = transfers
        .entries
        .iter()
        .find(|entry| entry.id == stalled_id)
        .expect("stalled entry");
    assert_eq!(stalled.status, "failed");
}

/// Downloads without a peer or without a destination cannot be negotiated.
/// Promoting them would strand them in `peer_lookup`, which counts as active
/// and permanently consumes a download slot.
#[cfg_attr(test, tokio::test)]
#[cfg(feature = "full-controller-tests")]
pub(super) async fn scheduler_leaves_downloads_without_a_peer_or_destination_queued() {
    let (state, mut receiver) = test_state();
    let (no_peer, no_path) = {
        let mut transfers = state.transfers.write().await;
        let no_peer = transfers.create(
            0,
            None,
            "Remote/NoPeer.flac".to_owned(),
            Some("no-peer".to_owned()),
            Some(4),
        );
        let no_path = transfers.create(
            0,
            Some("friend".to_owned()),
            "Remote/NoPath.flac".to_owned(),
            None,
            Some(4),
        );
        (no_peer.id, no_path.id)
    };

    crate::schedule_queued_downloads(&state).await;

    assert!(drain_commands(&mut receiver).is_empty());
    assert_eq!(status_of(&state, no_peer).await, "queued");
    assert_eq!(status_of(&state, no_path).await, "queued");
}

/// The periodic scheduler leaves remote-queued downloads alone because the
/// peer owns that queue. A reconnect may invalidate the old `QueueUpload`, so
/// login replay re-asks once instead of waiting forever for an offer.
#[cfg_attr(test, tokio::test)]
#[cfg(feature = "full-controller-tests")]
pub(super) async fn login_replay_reasks_remote_queued_downloads() {
    let (state, mut receiver) = test_state();
    let id = {
        let mut transfers = state.transfers.write().await;
        let entry = transfers.create(
            0,
            Some("friend".to_owned()),
            "Remote/RemoteQueued.flac".to_owned(),
            Some("remote-queued".to_owned()),
            Some(4),
        );
        transfers
            .update_status(entry.id, "queued", None, Some("Queued".to_owned()))
            .expect("remote queue response")
            .id
    };

    crate::session_runtime::dispatch_queued_downloads_after_login(&state).await;

    assert_eq!(drain_commands(&mut receiver), vec!["friend".to_owned()]);
    assert_eq!(status_of(&state, id).await, "peer_lookup");
}

/// slskd's `Retry.Do` wraps the whole download, so a transfer that dies after
/// N bytes returns to the queue and resumes its `.part` file instead of being
/// marked failed.
#[cfg_attr(test, tokio::test)]
#[cfg(feature = "full-controller-tests")]
pub(super) async fn mid_transfer_failure_requeues_the_same_download() {
    let (state, _receiver) = test_state();
    let transfer = {
        let mut transfers = state.transfers.write().await;
        let entry = transfers.create(
            0,
            Some("friend".to_owned()),
            "Remote/Partial.flac".to_owned(),
            Some("partial".to_owned()),
            Some(10),
        );
        transfers
            .update_status(entry.id, "in_progress", Some(4), None)
            .expect("start download")
    };

    crate::file_transfer_runtime::finish_file_transfer(
        &state,
        &transfer,
        Err("connection reset after 4 bytes".to_owned()),
    )
    .await;

    let transfers = state.transfers.read().await;
    let entry = transfers
        .entries
        .iter()
        .find(|entry| entry.id == transfer.id)
        .expect("download entry");
    assert_eq!(entry.status, "queued");
    assert_eq!(entry.attempts, 2);
    assert!(entry.next_attempt_at.is_some());
    assert_eq!(entry.bytes_transferred, 4);
    assert_eq!(
        entry.reason.as_deref(),
        Some("connection reset after 4 bytes")
    );
}

#[cfg_attr(test, tokio::test)]
#[cfg(feature = "full-controller-tests")]
pub(super) async fn mid_transfer_failure_stays_failed_once_attempts_are_spent() {
    let (state, _receiver) = test_state();
    let attempts = state.transfer_download_settings.read().await.retry.attempts;
    let transfer = {
        let mut transfers = state.transfers.write().await;
        let entry = transfers.create(
            0,
            Some("friend".to_owned()),
            "Remote/Exhausted.flac".to_owned(),
            Some("exhausted".to_owned()),
            Some(10),
        );
        let entry = transfers
            .update_status(entry.id, "in_progress", Some(4), None)
            .expect("start download");
        transfers
            .update_retry_state(entry.id, attempts, None, "in_progress", None)
            .expect("spend attempts")
    };

    crate::file_transfer_runtime::finish_file_transfer(
        &state,
        &transfer,
        Err("connection reset after 4 bytes".to_owned()),
    )
    .await;

    let transfers = state.transfers.read().await;
    let entry = transfers
        .entries
        .iter()
        .find(|entry| entry.id == transfer.id)
        .expect("download entry");
    assert_eq!(entry.status, "failed");
    assert_eq!(entry.attempts, attempts);
    assert!(entry.next_attempt_at.is_none());
}

#[cfg_attr(test, tokio::test)]
#[cfg(feature = "full-controller-tests")]
pub(super) async fn mid_transfer_failure_keeps_cancelled_downloads_terminal() {
    let (state, _receiver) = test_state();
    let transfer = {
        let mut transfers = state.transfers.write().await;
        let entry = transfers.create(
            0,
            Some("friend".to_owned()),
            "Remote/Cancelled.flac".to_owned(),
            Some("cancelled".to_owned()),
            Some(10),
        );
        transfers
            .update_status(entry.id, "cancelled", None, None)
            .expect("cancel download")
    };

    crate::file_transfer_runtime::finish_file_transfer(
        &state,
        &transfer,
        Err("connection reset after 4 bytes".to_owned()),
    )
    .await;

    assert_eq!(status_of(&state, transfer.id).await, "cancelled");
}

/// A transfer rejected by the content-safety policy is a final verdict. Retrying
/// it would re-download the same corrupt payload.
#[cfg_attr(test, tokio::test)]
#[cfg(feature = "full-controller-tests")]
pub(super) async fn content_safety_rejection_is_not_retried() {
    let (state, _receiver) = test_state();
    let transfer = {
        let mut transfers = state.transfers.write().await;
        let entry = transfers.create(
            0,
            Some("friend".to_owned()),
            "Remote/Corrupt.flac".to_owned(),
            Some("corrupt".to_owned()),
            Some(10),
        );
        transfers
            .update_status(entry.id, "in_progress", Some(4), None)
            .expect("start download")
    };

    crate::file_transfer_runtime::finish_file_transfer(
        &state,
        &transfer,
        Err("download rejected by configured content safety policy".to_owned()),
    )
    .await;

    let transfers = state.transfers.read().await;
    let entry = transfers
        .entries
        .iter()
        .find(|entry| entry.id == transfer.id)
        .expect("download entry");
    assert_eq!(entry.status, "failed");
    assert_eq!(entry.attempts, 1);
    assert_eq!(
        entry.reason.as_deref(),
        Some("download rejected by configured content safety policy")
    );
}

/// The modern download flow needs our listener; a disabled inbound setting is
/// permanent configuration, not a transport error, so it must not burn the
/// retry budget with backoff cycles.
#[cfg_attr(test, tokio::test)]
#[cfg(feature = "full-controller-tests")]
pub(super) async fn inbound_disabled_download_fails_without_retry() {
    let (state, mut receiver) = test_state_with_env(
        MapEnv::default()
            .with("SLSKR_TRANSFER_ALLOW_INBOUND", "false")
            .with("SLSKR_TEST_USER_ENDPOINT_OVERRIDES", "friend=127.0.0.1:1"),
    );
    let id = {
        let mut transfers = state.transfers.write().await;
        transfers
            .create(
                0,
                Some("friend".to_owned()),
                "Remote/InboundDisabled.flac".to_owned(),
                Some("inbound-disabled".to_owned()),
                Some(4),
            )
            .id
    };

    crate::schedule_queued_downloads(&state).await;

    assert!(drain_commands(&mut receiver).is_empty());
    let transfers = state.transfers.read().await;
    let entry = transfers
        .entries
        .iter()
        .find(|entry| entry.id == id)
        .expect("download entry");
    assert_eq!(entry.status, "failed");
    assert_eq!(entry.attempts, 1);
    assert!(entry.next_attempt_at.is_none());
    assert!(entry
        .reason
        .as_deref()
        .is_some_and(|reason| reason.contains("inbound file transfers are disabled")));
}

/// A stall sweep can requeue a zero-byte download before its socket finally
/// errors. That late error belongs to the old attempt and must not increment
/// the fresh retry's attempt count or overwrite its backoff.
#[cfg_attr(test, tokio::test)]
#[cfg(feature = "full-controller-tests")]
pub(super) async fn late_socket_error_does_not_requeue_an_already_retried_download() {
    let (state, _receiver) = test_state();
    let transfer = {
        let mut transfers = state.transfers.write().await;
        let entry = transfers.create(
            0,
            Some("friend".to_owned()),
            "Remote/StalledThenClosed.flac".to_owned(),
            Some("stalled-then-closed".to_owned()),
            Some(10),
        );
        transfers
            .update_status(entry.id, "in_progress", None, None)
            .expect("start download")
    };
    {
        let mut transfers = state.transfers.write().await;
        transfers
            .update_retry_state(
                transfer.id,
                2,
                Some(crate::unix_timestamp().saturating_add(5)),
                "queued",
                Some("download stalled before any data arrived".to_owned()),
            )
            .expect("requeue stalled download");
    }

    crate::file_transfer_runtime::finish_file_transfer(
        &state,
        &transfer,
        Err("connection reset after 0 bytes".to_owned()),
    )
    .await;

    let transfers = state.transfers.read().await;
    let entry = transfers
        .entries
        .iter()
        .find(|entry| entry.id == transfer.id)
        .expect("download entry");
    assert_eq!(entry.status, "queued");
    assert_eq!(entry.attempts, 2);
    assert_eq!(
        entry.reason.as_deref(),
        Some("download stalled before any data arrived")
    );
}
