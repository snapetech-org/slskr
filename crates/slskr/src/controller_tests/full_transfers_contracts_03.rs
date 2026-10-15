//! Controller full transfers contracts 03 ownership.

use super::*;

#[cfg_attr(test, tokio::test)]
#[cfg(feature = "full-controller-tests")]
pub(super) async fn transfer_start_with_peer_requests_peer_address() {
    let (state, mut receiver) = test_state();
    let path = std::env::temp_dir().join(format!(
        "slskr-transfer-start-{}-upload.bin",
        std::process::id()
    ));
    std::fs::write(&path, [1_u8, 2, 3, 4]).expect("write shared file");
    add_test_share(&state, "Remote/Song.flac", &path, 4).await;
    let created = crate::route_http_request(
        "POST",
        "/api/v0/transfers",
        None,
        "{\"direction\":1,\"peer_username\":\"friend\",\"filename\":\"Remote/Song.flac\",\"size\":4}",
        &state,
    )
    .await
    .expect("create transfer");
    assert_eq!(created.status, "201 Created");
    assert!(created.body.contains("\"token\":1"));

    let started = crate::route_http_request("POST", "/api/v0/transfers/1/start", None, "", &state)
        .await
        .expect("start transfer");

    assert_eq!(started.status, "200 OK");
    assert!(started.body.contains("\"status\":\"peer_lookup\""));
    assert_eq!(
        receiver.try_recv().expect("transfer command"),
        crate::SessionCommand::TransferPeer {
            id: 1,
            username: "friend".to_owned(),
        }
    );
    let _ = std::fs::remove_file(path);
}

#[cfg_attr(test, tokio::test)]
#[cfg(feature = "full-controller-tests")]
pub(super) async fn queued_peer_download_adopts_the_remote_upload_token() {
    let (state, _receiver) = test_state();
    let path = crate::safe_download_path(&state.config.downloads_dir, "Remote/Queued.flac")
        .expect("download path");
    let request_token = {
        let mut transfers = state.transfers.write().await;
        let entry = transfers.create(
            0,
            Some("friend".to_owned()),
            "Remote/Queued.flac".to_owned(),
            Some(path.display().to_string()),
            Some(4),
        );
        let token = entry.token;
        transfers.update_status(entry.id, "peer_lookup", None, None);
        token
    };
    let upload_token = request_token.saturating_add(76);

    let listener = tokio::net::TcpListener::bind("127.0.0.1:0")
        .await
        .expect("listener");
    let local_addr = listener.local_addr().expect("local addr");
    let server = tokio::spawn(async move {
        let (stream, _) = listener.accept().await.expect("accept");
        let mut init = slskr_client::stream::InitConnection::new(stream);
        init.receive().await.expect("init");
        let mut peer = slskr_client::stream::PeerMessageConnection::new(init.into_inner());
        assert_eq!(
            peer.receive().await.expect("download request"),
            crate::PeerMessage::TransferRequest(crate::TransferRequest {
                filename_encoding: Default::default(),
                direction: 0,
                token: request_token,
                filename: "Remote/Queued.flac".to_owned(),
                size: None,
            })
        );
        peer.send(&crate::PeerMessage::TransferResponse(
            crate::TransferResponse::Rejected {
                token: request_token,
                reason: "Queued".to_owned(),
            },
        ))
        .await
        .expect("queued response");
        peer.send(&crate::PeerMessage::TransferRequest(
            crate::TransferRequest {
                filename_encoding: Default::default(),
                direction: 1,
                token: upload_token,
                filename: "Remote/Queued.flac".to_owned(),
                size: Some(4),
            },
        ))
        .await
        .expect("upload request");
        assert_eq!(
            peer.receive().await.expect("upload acknowledgement"),
            crate::PeerMessage::TransferResponse(crate::TransferResponse::Allowed {
                token: upload_token,
                size: Some(4),
            })
        );
    });
    let address = slskr_client::protocol::server::PeerAddress {
        username: "friend".to_owned(),
        ip: "127.0.0.1".parse().unwrap(),
        port: u32::from(local_addr.port()),
        obfuscation_type: 0,
        obfuscated_port: 0,
    };

    crate::project_peer_transfer_response(&state, &address).await;
    server.await.expect("server task");

    let transfers = state.transfers.read().await;
    let record = transfers.entries.first().expect("transfer");
    assert_eq!(record.status, "accepted");
    assert_eq!(record.token, upload_token);
    assert_eq!(record.size, Some(4));
    assert_eq!(record.reason, None);
}

#[cfg_attr(test, tokio::test)]
#[cfg(feature = "full-controller-tests")]
pub(super) async fn queued_outgoing_upload_accepts_remote_download_resume_request() {
    let (state, _receiver) = test_state();
    let path = std::env::temp_dir().join(format!(
        "slskr-transfer-queued-upload-{}-resume.bin",
        std::process::id()
    ));
    std::fs::write(&path, [1_u8, 2, 3, 4]).expect("write upload file");
    add_test_share(&state, "Remote/QueuedUpload.flac", &path, 4).await;
    {
        let mut transfers = state.transfers.write().await;
        let entry = transfers.create(
            1,
            Some("friend".to_owned()),
            "Remote/QueuedUpload.flac".to_owned(),
            Some(path.display().to_string()),
            Some(4),
        );
        assert_eq!(entry.token, 1);
        transfers.update_status(entry.id, "queued", None, Some("Queued".to_owned()));
    }

    let listener = tokio::net::TcpListener::bind("127.0.0.1:0")
        .await
        .expect("listener");
    let local_addr = listener.local_addr().expect("local addr");
    let server_state = state.clone();
    let server = tokio::spawn(async move {
        let (stream, _) = listener.accept().await.expect("accept peer-message");
        crate::handle_plain_peer_messages(
            &server_state,
            slskr_client::stream::PeerMessageConnection::new(stream),
            Some("friend".to_owned()),
        )
        .await
    });

    let stream = tokio::net::TcpStream::connect(local_addr)
        .await
        .expect("connect peer-message");
    let mut peer = slskr_client::stream::PeerMessageConnection::new(stream);
    peer.send(&crate::PeerMessage::TransferRequest(
        crate::TransferRequest {
            filename_encoding: Default::default(),
            direction: 0,
            token: 77,
            filename: "Remote/QueuedUpload.flac".to_owned(),
            size: None,
        },
    ))
    .await
    .expect("send resume request");
    assert_eq!(
        peer.receive().await.expect("resume response"),
        crate::PeerMessage::TransferResponse(crate::TransferResponse::Allowed {
            token: 77,
            size: Some(4),
        })
    );
    drop(peer);
    server.await.expect("server task").expect("server result");

    let transfers = state.transfers.read().await;
    assert_eq!(transfers.entries.len(), 1);
    let record = transfers.entries.first().expect("transfer");
    assert_eq!(record.direction, 1);
    assert_eq!(record.token, 77);
    assert_eq!(record.status, "accepted");
    assert_eq!(record.size, Some(4));
    assert_eq!(record.reason, None);
    let _ = std::fs::remove_file(path);
}

#[cfg_attr(test, tokio::test)]
#[cfg(feature = "full-controller-tests")]
pub(super) async fn queued_outgoing_upload_resume_obeys_upload_slots() {
    let (state, _receiver) = test_state_with_env(MapEnv::default().with("SLSKD_UPLOAD_SLOTS", "1"));
    let path = std::env::temp_dir().join(format!(
        "slskr-transfer-queued-upload-capacity-{}-resume.bin",
        std::process::id()
    ));
    std::fs::write(&path, [1_u8, 2, 3, 4]).expect("write upload file");
    add_test_share(&state, "Remote/QueuedUpload.flac", &path, 4).await;
    {
        let mut transfers = state.transfers.write().await;
        let active = transfers.create(
            1,
            Some("busy".to_owned()),
            "Remote/Busy.flac".to_owned(),
            Some(path.display().to_string()),
            Some(4),
        );
        transfers.update_status(active.id, "in_progress", None, None);
        let queued = transfers.create(
            1,
            Some("friend".to_owned()),
            "Remote/QueuedUpload.flac".to_owned(),
            Some(path.display().to_string()),
            Some(4),
        );
        transfers.update_status(queued.id, "queued", None, Some("Queued".to_owned()));
    }

    let listener = tokio::net::TcpListener::bind("127.0.0.1:0")
        .await
        .expect("listener");
    let address = listener.local_addr().expect("local address");
    let server_state = state.clone();
    let server = tokio::spawn(async move {
        let (stream, _) = listener.accept().await.expect("accept peer-message");
        crate::handle_plain_peer_messages(
            &server_state,
            slskr_client::stream::PeerMessageConnection::new(stream),
            Some("friend".to_owned()),
        )
        .await
    });

    let stream = tokio::net::TcpStream::connect(address)
        .await
        .expect("connect peer-message");
    let mut peer = slskr_client::stream::PeerMessageConnection::new(stream);
    peer.send(&crate::PeerMessage::TransferRequest(
        crate::TransferRequest {
            filename_encoding: Default::default(),
            direction: 0,
            token: 77,
            filename: "Remote/QueuedUpload.flac".to_owned(),
            size: Some(4),
        },
    ))
    .await
    .expect("send resume request");
    assert_eq!(
        peer.receive().await.expect("resume response"),
        crate::PeerMessage::TransferResponse(crate::TransferResponse::Rejected {
            token: 77,
            reason: "Queued".to_owned(),
        })
    );
    drop(peer);
    server.await.expect("server task").expect("server result");

    let transfers = state.transfers.read().await;
    let queued = transfers
        .entries
        .iter()
        .find(|entry| entry.peer_username.as_deref() == Some("friend"))
        .expect("queued upload remains pending");
    assert_eq!(queued.status, "queued");
    assert_eq!(queued.reason.as_deref(), Some("Queued"));
    assert_ne!(queued.token, 77);
    let _ = std::fs::remove_file(path);
}

#[cfg_attr(test, tokio::test)]
#[cfg(feature = "full-controller-tests")]
pub(super) async fn queued_outgoing_upload_resume_obeys_group_slots() {
    let (state, _receiver) = test_state_with_env(MapEnv::default().with("SLSKD_UPLOAD_SLOTS", "2"));
    state
        .transfer_groups_settings
        .write()
        .await
        .default
        .upload
        .slots = 1;
    let path = std::env::temp_dir().join(format!(
        "slskr-transfer-queued-upload-group-capacity-{}-resume.bin",
        std::process::id()
    ));
    std::fs::write(&path, [1_u8, 2, 3, 4]).expect("write upload file");
    add_test_share(&state, "Remote/QueuedUpload.flac", &path, 4).await;
    {
        let mut transfers = state.transfers.write().await;
        let active = transfers.create(
            1,
            Some("busy".to_owned()),
            "Remote/Busy.flac".to_owned(),
            Some(path.display().to_string()),
            Some(4),
        );
        transfers.update_status(active.id, "in_progress", None, None);
        let queued = transfers.create(
            1,
            Some("friend".to_owned()),
            "Remote/QueuedUpload.flac".to_owned(),
            Some(path.display().to_string()),
            Some(4),
        );
        transfers.update_status(queued.id, "queued", None, Some("Queued".to_owned()));
    }

    let listener = tokio::net::TcpListener::bind("127.0.0.1:0")
        .await
        .expect("listener");
    let local_addr = listener.local_addr().expect("local addr");
    let server_state = state.clone();
    let server = tokio::spawn(async move {
        let (stream, _) = listener.accept().await.expect("accept peer-message");
        crate::handle_plain_peer_messages(
            &server_state,
            slskr_client::stream::PeerMessageConnection::new(stream),
            Some("friend".to_owned()),
        )
        .await
    });

    let stream = tokio::net::TcpStream::connect(local_addr)
        .await
        .expect("connect peer-message");
    let mut peer = slskr_client::stream::PeerMessageConnection::new(stream);
    peer.send(&crate::PeerMessage::TransferRequest(
        crate::TransferRequest {
            filename_encoding: Default::default(),
            direction: 0,
            token: 77,
            filename: "Remote/QueuedUpload.flac".to_owned(),
            size: Some(4),
        },
    ))
    .await
    .expect("send resume request");
    assert_eq!(
        peer.receive().await.expect("resume response"),
        crate::PeerMessage::TransferResponse(crate::TransferResponse::Rejected {
            token: 77,
            reason: "Queued".to_owned(),
        })
    );
    drop(peer);
    server.await.expect("server task").expect("server result");

    let transfers = state.transfers.read().await;
    let queued = transfers
        .entries
        .iter()
        .find(|entry| entry.peer_username.as_deref() == Some("friend"))
        .expect("queued upload remains pending");
    assert_eq!(queued.status, "queued");
    assert_eq!(queued.reason.as_deref(), Some("Queued"));
    assert_ne!(queued.token, 77);
    let _ = std::fs::remove_file(path);
}

#[cfg_attr(test, tokio::test)]
#[cfg(feature = "full-controller-tests")]
pub(super) async fn queued_remote_download_resume_obeys_download_slots() {
    let (state, _receiver) =
        test_state_with_env(MapEnv::default().with("SLSKD_DOWNLOAD_SLOTS", "1"));
    let download_path = crate::safe_download_path(&state.config.downloads_dir, "Remote/Busy.flac")
        .expect("download path");
    {
        let mut transfers = state.transfers.write().await;
        let active = transfers.create(
            0,
            Some("busy".to_owned()),
            "Remote/Busy.flac".to_owned(),
            Some(download_path.display().to_string()),
            Some(4),
        );
        transfers.update_status(active.id, "in_progress", None, None);
        let queued = transfers.create(
            0,
            Some("friend".to_owned()),
            "Remote/Queued.flac".to_owned(),
            Some(download_path.display().to_string()),
            Some(4),
        );
        transfers.update_status(queued.id, "queued", None, Some("Queued".to_owned()));
    }

    let listener = tokio::net::TcpListener::bind("127.0.0.1:0")
        .await
        .expect("listener");
    let address = listener.local_addr().expect("local address");
    let server_state = state.clone();
    let server = tokio::spawn(async move {
        let (stream, _) = listener.accept().await.expect("accept peer-message");
        crate::handle_plain_peer_messages(
            &server_state,
            slskr_client::stream::PeerMessageConnection::new(stream),
            Some("friend".to_owned()),
        )
        .await
    });

    let stream = tokio::net::TcpStream::connect(address)
        .await
        .expect("connect peer-message");
    let mut peer = slskr_client::stream::PeerMessageConnection::new(stream);
    peer.send(&crate::PeerMessage::TransferRequest(
        crate::TransferRequest {
            filename_encoding: Default::default(),
            direction: 1,
            token: 77,
            filename: "Remote/Queued.flac".to_owned(),
            size: Some(4),
        },
    ))
    .await
    .expect("send resume request");
    assert_eq!(
        peer.receive().await.expect("resume response"),
        crate::PeerMessage::TransferResponse(crate::TransferResponse::Rejected {
            token: 77,
            reason: "Queued".to_owned(),
        })
    );
    drop(peer);
    server.await.expect("server task").expect("server result");

    let transfers = state.transfers.read().await;
    let queued = transfers
        .entries
        .iter()
        .find(|entry| entry.peer_username.as_deref() == Some("friend"))
        .expect("queued download remains pending");
    assert_eq!(queued.status, "queued");
    assert_eq!(queued.reason.as_deref(), Some("Queued"));
    assert_ne!(queued.token, 77);
}

#[cfg_attr(test, tokio::test)]
#[cfg(feature = "full-controller-tests")]
pub(super) async fn queue_upload_and_place_in_queue_messages_drive_the_group_scheduler() {
    let (state, _receiver) = test_state_with_env(
        MapEnv::default().with("SLSKR_FROZEN_TRANSFER_UPLOAD_JSON", r#"{"slots":1}"#),
    );
    let path = std::env::temp_dir().join(format!(
        "slskr-queue-upload-message-{}.bin",
        std::process::id()
    ));
    std::fs::write(&path, [1_u8, 2, 3, 4]).unwrap();
    add_test_share(&state, "Remote/Queued.flac", &path, 4).await;
    {
        let mut transfers = state.transfers.write().await;
        let blocker = transfers.create(
            1,
            Some("busy".to_owned()),
            "Remote/Busy.flac".to_owned(),
            Some(path.display().to_string()),
            Some(4),
        );
        transfers.update_status(blocker.id, "in_progress", None, None);
    }

    let listener = tokio::net::TcpListener::bind("127.0.0.1:0").await.unwrap();
    let address = listener.local_addr().unwrap();
    let server_state = state.clone();
    let server = tokio::spawn(async move {
        let (stream, _) = listener.accept().await.unwrap();
        crate::handle_plain_peer_messages(
            &server_state,
            slskr_client::stream::PeerMessageConnection::new(stream),
            Some("friend".to_owned()),
        )
        .await
    });
    let stream = tokio::net::TcpStream::connect(address).await.unwrap();
    let mut peer = slskr_client::stream::PeerMessageConnection::new(stream);
    peer.send(&crate::PeerMessage::QueueUpload {
        filename: "Remote/Queued.flac".to_owned(),
    })
    .await
    .unwrap();
    drop(peer);
    server.await.unwrap().unwrap();

    let queued = {
        let transfers = state.transfers.read().await;
        transfers
            .entries
            .iter()
            .find(|entry| entry.peer_username.as_deref() == Some("friend"))
            .cloned()
            .unwrap()
    };
    assert_eq!(queued.status, "queued");
    assert_eq!(queued.reason.as_deref(), Some("Queued"));

    let listener = tokio::net::TcpListener::bind("127.0.0.1:0").await.unwrap();
    let address = listener.local_addr().unwrap();
    let server_state = state.clone();
    let server = tokio::spawn(async move {
        let (stream, _) = listener.accept().await.unwrap();
        crate::handle_plain_peer_messages(
            &server_state,
            slskr_client::stream::PeerMessageConnection::new(stream),
            Some("friend".to_owned()),
        )
        .await
    });
    let stream = tokio::net::TcpStream::connect(address).await.unwrap();
    let mut peer = slskr_client::stream::PeerMessageConnection::new(stream);
    peer.send(&crate::PeerMessage::PlaceInQueueRequest {
        filename: "Remote/Queued.flac".to_owned(),
    })
    .await
    .unwrap();
    assert_eq!(
        peer.receive().await.unwrap(),
        crate::PeerMessage::PlaceInQueueResponse {
            filename: "Remote/Queued.flac".to_owned(),
            // Frozen slskd's round-robin estimator reports the first file
            // in a user's local queue as zero even while another user is active.
            place: 0,
        }
    );
    drop(peer);
    server.await.unwrap().unwrap();
    let _ = std::fs::remove_file(path);
}

#[cfg_attr(test, tokio::test)]
#[cfg(feature = "full-controller-tests")]
pub(super) async fn inbound_transfer_request_serves_shared_file_over_pierce_firewall() {
    let (state, _receiver) = test_state();
    let path = std::env::temp_dir().join(format!(
        "slskr-transfer-f-{}-inbound-upload.bin",
        std::process::id()
    ));
    std::fs::write(&path, [1_u8, 2, 3, 4]).expect("write shared file");
    {
        let mut shares = state.shares.write().await;
        shares.entries.push(FileEntry {
            filename_encoding: Default::default(),
            extension_encoding: Default::default(),
            code: 1,
            filename: "Virtual/Inbound.flac".to_owned(),
            size: 4,
            extension: "flac".to_owned(),
            attributes: Vec::new(),
        });
        shares
            .local_paths
            .insert("Virtual/Inbound.flac".to_owned(), path.clone());
    }

    assert!(
        crate::find_shared_local_file(&state, r"Virtual\Inbound.flac")
            .await
            .is_some()
    );

    crate::handle_peer_message(
        &state,
        crate::PeerMessage::TransferRequest(crate::TransferRequest {
            filename_encoding: Default::default(),
            direction: 0,
            token: 7,
            filename: r"Virtual\Inbound.flac".to_owned(),
            size: None,
        }),
        None,
        |response| async move {
            assert_eq!(
                response,
                crate::PeerMessage::TransferResponse(crate::TransferResponse::Allowed {
                    token: 7,
                    size: Some(4),
                },)
            );
            Ok(())
        },
    )
    .await
    .expect("transfer request");

    let listener = tokio::net::TcpListener::bind("127.0.0.1:0")
        .await
        .expect("listener");
    let local_addr = listener.local_addr().expect("local addr");
    let inbound_state = Arc::clone(&state);
    let server = tokio::spawn(async move {
        let (stream, _) = listener.accept().await.expect("accept file-transfer");
        crate::handle_inbound_file_transfer(
            &inbound_state,
            slskr_client::file_transfer::FileTransferConnection::new(stream),
            Some(7),
        )
        .await
        .expect("serve inbound file");
    });
    let stream = tokio::net::TcpStream::connect(local_addr)
        .await
        .expect("connect file-transfer");
    let mut file = slskr_client::file_transfer::FileTransferConnection::new(stream);
    assert_eq!(file.receive_token().await.expect("token"), 7);
    file.send_offset(2).await.expect("offset");
    assert_eq!(file.read_chunk(2).await.expect("chunk"), vec![3, 4]);
    server.await.expect("server task");

    let transfers = state.transfers.read().await;
    let record = transfers.entries.first().expect("transfer");
    assert_eq!(record.status, "succeeded");
    // Progress tracks the remote position, including the resumed two-byte offset.
    assert_eq!(record.bytes_transferred, 4);
    assert_eq!(record.size, Some(4));
    let _ = std::fs::remove_file(path);
}

#[cfg_attr(test, tokio::test)]
#[cfg(feature = "full-controller-tests")]
pub(super) async fn inbound_transfer_request_rejects_when_active_limit_is_full() {
    let (state, _receiver) =
        test_state_with_env(MapEnv::default().with("SLSKR_TRANSFER_MAX_ACTIVE", "1"));
    {
        let mut transfers = state.transfers.write().await;
        let entry = transfers.create(1, None, "Remote/Busy.flac".to_owned(), None, Some(1));
        transfers.update_status(entry.id, "in_progress", None, None);
    }

    crate::handle_peer_message(
        &state,
        crate::PeerMessage::TransferRequest(crate::TransferRequest {
            filename_encoding: Default::default(),
            direction: 0,
            token: 99,
            filename: "Virtual/Test.flac".to_owned(),
            size: None,
        }),
        None,
        |response| async move {
            assert_eq!(
                response,
                crate::PeerMessage::TransferResponse(crate::TransferResponse::Rejected {
                    token: 99,
                    reason: "transfer limit reached".to_owned(),
                },)
            );
            Ok(())
        },
    )
    .await
    .expect("reject transfer request");

    let transfers = state.transfers.read().await;
    assert_eq!(transfers.entries.len(), 2);
    let rejected = transfers.entries.get(1).expect("rejection");
    assert_eq!(rejected.status, "rejected");
    assert_eq!(rejected.reason.as_deref(), Some("transfer limit reached"));
}

#[cfg_attr(test, tokio::test)]
#[cfg(feature = "full-controller-tests")]
pub(super) async fn inbound_transfer_request_rejects_when_inbound_disabled() {
    let (state, _receiver) =
        test_state_with_env(MapEnv::default().with("SLSKR_TRANSFER_ALLOW_INBOUND", "false"));

    crate::handle_peer_message(
        &state,
        crate::PeerMessage::TransferRequest(crate::TransferRequest {
            filename_encoding: Default::default(),
            direction: 0,
            token: 55,
            filename: "Virtual/Test.flac".to_owned(),
            size: None,
        }),
        None,
        |response| async move {
            assert_eq!(
                response,
                crate::PeerMessage::TransferResponse(crate::TransferResponse::Rejected {
                    token: 55,
                    reason: "inbound transfers are disabled".to_owned(),
                },)
            );
            Ok(())
        },
    )
    .await
    .expect("reject transfer request");

    let transfers = state.transfers.read().await;
    let rejected = transfers.entries.first().expect("rejection");
    assert_eq!(rejected.status, "rejected");
    assert_eq!(
        rejected.reason.as_deref(),
        Some("inbound transfers are disabled")
    );
}

#[cfg_attr(test, tokio::test)]
#[cfg(feature = "full-controller-tests")]
pub(super) async fn transfer_api_rejects_missing_filename() {
    let (state, _receiver) = test_state();

    let response = crate::route_http_request("POST", "/api/v0/transfers", None, "{}", &state)
        .await
        .expect("bad transfer");

    assert_eq!(response.status, "400 Bad Request");
    assert_eq!(response.body, "{\"error\":\"filename is required\"}");
}

#[cfg_attr(test, tokio::test)]
#[cfg(feature = "full-controller-tests")]
pub(super) async fn transfer_group_runtime_enforces_membership_limits_slots_file_types_and_speed() {
    let (state, _receiver) = test_state_with_env(
        MapEnv::default()
            .with(
                "SLSKR_FROZEN_TRANSFER_UPLOAD_JSON",
                r#"{"slots":2,"speed_limit":100,"limits":{"queued":{"files":1}}}"#,
            )
            .with(
                "SLSKR_FROZEN_TRANSFER_GROUPS_JSON",
                r#"{"user_defined":{"friends":{"upload":{"priority":5,"slots":2,"speed_limit":50,"allowed_file_types":[".flac"],"limits":{"queued":{"files":2}}},"members":["alice"]}}}"#,
            ),
    );

    assert_eq!(
        crate::file_transfer_runtime::effective_transfer_group(&state, "alice").await,
        "friends"
    );
    assert_eq!(
        crate::effective_upload_speed_limit(&state, "alice").await,
        50
    );
    assert_eq!(
        crate::effective_upload_speed_limit(&state, "stranger").await,
        100
    );
    assert_eq!(
        crate::file_transfer_runtime::inbound_upload_policy(&state, "alice", "Music/track.mp3", 10)
            .await
            .unwrap_err(),
        "File type .mp3 is not permitted."
    );

    {
        let mut transfers = state.transfers.write().await;
        let alice = transfers.create(
            1,
            Some("alice".to_owned()),
            "Music/first.flac".to_owned(),
            Some("/tmp/first.flac".to_owned()),
            Some(10),
        );
        transfers.update_status(alice.id, "in_progress", None, None);
    }
    assert_eq!(
        crate::file_transfer_runtime::inbound_upload_policy(
            &state,
            "alice",
            "Music/second.flac",
            10
        )
        .await
        .unwrap(),
        "friends"
    );

    {
        let mut transfers = state.transfers.write().await;
        let stranger = transfers.create(
            1,
            Some("stranger".to_owned()),
            "Music/first.flac".to_owned(),
            Some("/tmp/stranger.flac".to_owned()),
            Some(10),
        );
        transfers.update_status(stranger.id, "in_progress", None, None);
    }
    assert_eq!(
        crate::file_transfer_runtime::inbound_upload_policy(
            &state,
            "alice",
            "Music/third.flac",
            10
        )
        .await
        .unwrap_err(),
        "Queued"
    );
    assert_eq!(
        crate::file_transfer_runtime::inbound_upload_policy(
            &state,
            "stranger",
            "Music/second.flac",
            10
        )
        .await
        .unwrap_err(),
        "Too many files"
    );
}

#[cfg_attr(test, tokio::test)]
#[cfg(feature = "full-controller-tests")]
pub(super) async fn transfer_group_runtime_uses_frozen_limit_rejection_reasons_and_priority_resolution(
) {
    let (state, _receiver) = test_state_with_env(
        MapEnv::default()
            .with("SLSKR_CONTROLLER_PROFILE", "legacy")
            .with("SLSKR_AUTH_DISABLED", "true")
            .with(
                "SLSKR_FROZEN_TRANSFER_UPLOAD_JSON",
                r#"{"slots":10,"limits":{"daily":{"failures":1},"weekly":{"files":1,"megabytes":1}}}"#,
            )
            .with(
                "SLSKR_FROZEN_TRANSFER_GROUPS_JSON",
                r#"{"user_defined":{"lower":{"upload":{"priority":20},"members":["alice"]},"higher":{"upload":{"priority":5},"members":["alice"]}}}"#,
            ),
    );
    assert_eq!(
        crate::file_transfer_runtime::effective_transfer_group(&state, "alice").await,
        "higher"
    );

    {
        let mut transfers = state.transfers.write().await;
        let completed = transfers.create(
            1,
            Some("alice".to_owned()),
            "one.flac".to_owned(),
            Some("/tmp/one.flac".to_owned()),
            Some(10),
        );
        transfers.update_status(completed.id, "in_progress", None, None);
        transfers.update_status(completed.id, "completed", Some(10), None);
    }
    assert_eq!(
        crate::file_transfer_runtime::inbound_upload_policy(&state, "alice", "two.flac", 10)
            .await
            .unwrap_err(),
        "Too many files this week"
    );

    {
        let mut transfers = state.transfers.write().await;
        let failed = transfers.create(
            1,
            Some("bob".to_owned()),
            "failed.flac".to_owned(),
            Some("/tmp/failed.flac".to_owned()),
            Some(10),
        );
        transfers.update_status(failed.id, "in_progress", None, None);
        transfers.update_status(failed.id, "failed", None, Some("failure".to_owned()));
    }
    assert_eq!(
        crate::file_transfer_runtime::inbound_upload_policy(&state, "bob", "next.flac", 10)
            .await
            .unwrap_err(),
        "Too many failed transfers today"
    );
}

#[cfg_attr(test, tokio::test)]
#[cfg(feature = "full-controller-tests")]
pub(super) async fn transfer_group_queue_schedules_priority_slots_and_reports_frozen_positions() {
    let (state, mut receiver) = test_state_with_env(
        MapEnv::default()
            .with(
                "SLSKR_FROZEN_TRANSFER_UPLOAD_JSON",
                r#"{"slots":2}"#,
            )
            .with(
                "SLSKR_FROZEN_TRANSFER_GROUPS_JSON",
                r#"{"default":{"upload":{"priority":20,"strategy":"firstinfirstout","slots":2}},"user_defined":{"friends":{"upload":{"priority":5,"strategy":"firstinfirstout","slots":1},"members":["alice","ally"]}}}"#,
            ),
    );
    let (bob, alice, ally) = {
        let mut transfers = state.transfers.write().await;
        let mut queue = |username: &str, filename: &str| {
            let entry = transfers.create(
                1,
                Some(username.to_owned()),
                filename.to_owned(),
                Some(format!("/tmp/{filename}")),
                Some(10),
            );
            transfers
                .update_status(entry.id, "queued", None, Some("Queued".to_owned()))
                .unwrap()
        };
        (
            queue("bob", "bob.flac"),
            queue("alice", "alice.flac"),
            queue("ally", "ally.flac"),
        )
    };
    {
        let transfers = state.transfers.read().await;
        let upload = state.transfer_upload_settings.read().await;
        let groups = state.transfer_groups_settings.read().await;
        let users = state.users.read().await;
        assert_eq!(
            crate::next_queued_upload_id(
                &transfers,
                &upload,
                &groups,
                &users,
                state.config.transfer_max_active,
            ),
            Some(alice.id)
        );
    }
    crate::schedule_queued_uploads(&state).await;
    assert_eq!(
        receiver.try_recv().unwrap(),
        crate::SessionCommand::RequestPeerEndpoint("alice".to_owned())
    );
    assert_eq!(
        receiver.try_recv().unwrap(),
        crate::SessionCommand::RequestPeerEndpoint("bob".to_owned())
    );
    assert!(receiver.try_recv().is_err());
    let transfers = state.transfers.read().await;
    assert_eq!(
        transfers
            .entries
            .iter()
            .find(|entry| entry.id == alice.id)
            .unwrap()
            .status,
        "peer_lookup"
    );
    assert_eq!(
        transfers
            .entries
            .iter()
            .find(|entry| entry.id == bob.id)
            .unwrap()
            .status,
        "peer_lookup"
    );
    assert_eq!(
        transfers
            .entries
            .iter()
            .find(|entry| entry.id == ally.id)
            .unwrap()
            .status,
        "queued"
    );
    drop(transfers);

    let (round_robin, _receiver) = test_state_with_env(
        MapEnv::default()
            .with("SLSKR_FROZEN_TRANSFER_UPLOAD_JSON", r#"{"slots":1}"#)
            .with(
                "SLSKR_FROZEN_TRANSFER_GROUPS_JSON",
                r#"{"default":{"upload":{"strategy":"roundrobin","slots":1}}}"#,
            ),
    );
    {
        let mut transfers = round_robin.transfers.write().await;
        for (username, filename) in [
            ("alice", "one.flac"),
            ("alice", "two.flac"),
            ("bob", "bob.flac"),
        ] {
            let entry = transfers.create(
                1,
                Some(username.to_owned()),
                filename.to_owned(),
                Some(format!("/tmp/{filename}")),
                Some(10),
            );
            transfers.update_status(entry.id, "queued", None, Some("Queued".to_owned()));
        }
    }
    assert_eq!(
        crate::upload_queue_position(&round_robin, "alice", "two.flac").await,
        Some(2)
    );
    {
        let mut transfers = round_robin.transfers.write().await;
        let first = transfers.entries[0].id;
        transfers.update_status(first, "in_progress", None, None);
    }
    assert_eq!(
        crate::upload_queue_forecast(&round_robin, "charlie").await,
        (1, 3)
    );
}

#[cfg_attr(test, tokio::test)]
#[cfg(feature = "full-controller-tests")]
pub(super) async fn downloads_do_not_make_upload_queue_appear_free_at_the_shared_cap() {
    let (state, mut receiver) =
        test_state_with_env(MapEnv::default().with("SLSKR_TRANSFER_MAX_ACTIVE", "1"));
    let diagnostics = crate::route_http_request(
        "GET",
        "/api/transfers/uploads/diagnostics",
        None,
        "",
        &state,
    )
    .await
    .expect("upload diagnostics");
    let diagnostics: serde_json::Value =
        serde_json::from_str(&diagnostics.body).expect("diagnostics JSON");
    assert_eq!(diagnostics["uploadSlots"], 20);
    assert_eq!(diagnostics["globalTransferLimit"], 1);
    assert_eq!(diagnostics["warnings"].as_array().unwrap().len(), 1);
    let (download_id, queued_upload) = {
        let mut transfers = state.transfers.write().await;
        let download = transfers.create(
            0,
            Some("alice".to_owned()),
            "incoming.flac".to_owned(),
            None,
            Some(10),
        );
        transfers.update_status(download.id, "in_progress", None, None);
        let upload = transfers.create(
            1,
            Some("bob".to_owned()),
            "shared.flac".to_owned(),
            Some("/shares/shared.flac".to_owned()),
            Some(10),
        );
        let upload = transfers
            .update_status(upload.id, "queued", None, Some("Queued".to_owned()))
            .expect("queue upload");
        (download.id, upload)
    };

    let (slots, queue_position) = crate::upload_queue_forecast(&state, "bob").await;
    assert!(slots > 0);
    assert_eq!(queue_position, 2);
    assert_eq!(
        crate::inbound_upload_policy(&state, "charlie", "another.flac", 10)
            .await
            .unwrap_err(),
        "Queued"
    );
    crate::schedule_queued_uploads(&state).await;
    assert!(receiver.try_recv().is_err());
    assert_eq!(
        state
            .transfers
            .read()
            .await
            .entries
            .iter()
            .find(|entry| entry.id == queued_upload.id)
            .unwrap()
            .status,
        "queued"
    );

    state
        .transfers
        .write()
        .await
        .update_status(download_id, "succeeded", None, None);
    crate::schedule_queued_uploads(&state).await;
    assert_eq!(
        receiver.try_recv().unwrap(),
        crate::SessionCommand::RequestPeerEndpoint("bob".to_owned())
    );
}

#[cfg_attr(test, test)]
#[cfg(feature = "full-controller-tests")]
pub(super) fn transfer_capacity_respects_directional_and_shared_caps() {
    let mut transfers = crate::TransferQueue::new_in_memory(16);
    let download = transfers.create(
        0,
        Some("alice".to_owned()),
        "incoming.flac".to_owned(),
        None,
        Some(10),
    );
    transfers.update_status(download.id, "in_progress", None, None);

    assert!(!transfers.has_capacity_for_direction(0, 4, 1, None));
    assert!(transfers.has_capacity_for_direction(1, 4, 1, None));
    assert!(transfers.has_capacity_for_direction(0, 4, 2, Some(download.id)));

    let upload = transfers.create(
        1,
        Some("bob".to_owned()),
        "outgoing.flac".to_owned(),
        Some("/shares/outgoing.flac".to_owned()),
        Some(10),
    );
    transfers.update_status(upload.id, "accepted", None, None);

    assert!(!transfers.has_capacity_for_direction(1, 4, 1, None));
    assert!(!transfers.has_capacity_for_direction(0, 2, 4, None));
    assert!(!transfers.has_capacity_for_direction(0, 0, 4, None));
    assert!(!transfers.has_capacity_for_upload_group(4, 4, 1, None, |peer| { peer == Some("bob") }));
    assert!(
        transfers.has_capacity_for_upload_group(4, 4, 1, None, |peer| { peer == Some("alice") })
    );
}

#[cfg_attr(test, tokio::test)]
#[cfg(feature = "full-controller-tests")]
pub(super) async fn manual_upload_start_respects_transfer_group_slots() {
    let (state, _receiver) = test_state();
    state
        .transfer_groups_settings
        .write()
        .await
        .default
        .upload
        .slots = 1;
    let queued_id = {
        let mut transfers = state.transfers.write().await;
        let active = transfers.create(
            1,
            Some("busy".to_owned()),
            "Remote/Busy.flac".to_owned(),
            Some("/shares/busy.flac".to_owned()),
            Some(10),
        );
        transfers.update_status(active.id, "in_progress", None, None);
        let queued = transfers.create(
            1,
            Some("friend".to_owned()),
            "Remote/Queued.flac".to_owned(),
            Some("/shares/queued.flac".to_owned()),
            Some(10),
        );
        transfers
            .update_status(queued.id, "queued", None, Some("Queued".to_owned()))
            .unwrap()
            .id
    };

    let response = crate::route_http_request(
        "POST",
        &format!("/api/transfers/{queued_id}/start"),
        None,
        "",
        &state,
    )
    .await
    .expect("start queued upload");
    assert_eq!(response.status, "409 Conflict");
    assert!(response.body.contains("upload group slot limit reached"));
    let transfers = state.transfers.read().await;
    let queued = transfers
        .entries
        .iter()
        .find(|entry| entry.id == queued_id)
        .expect("queued transfer remains");
    assert_eq!(queued.status, "queued");
}

#[cfg_attr(test, tokio::test)]
#[cfg(feature = "full-controller-tests")]
pub(super) async fn queued_inbound_upload_is_promoted_without_a_duplicate_record() {
    let (state, _receiver) = test_state();
    let (queued, accepted, matching_records) = {
        let mut transfers = state.transfers.write().await;
        let queued = transfers.create(
            1,
            Some("alice".to_owned()),
            "track.flac".to_owned(),
            Some("/shares/track.flac".to_owned()),
            Some(10),
        );
        let queued = transfers
            .update_status(queued.id, "queued", None, Some("Queued".to_owned()))
            .expect("queued transfer");
        let accepted = transfers
            .accept_pending_inbound_upload_request("alice", "track.flac", 77, 12)
            .expect("accept queued upload");
        let matching_records = transfers
            .entries
            .iter()
            .filter(|entry| {
                entry.direction == 1
                    && entry.peer_username.as_deref() == Some("alice")
                    && entry.filename == "track.flac"
            })
            .count();
        (queued, accepted, matching_records)
    };

    assert_eq!(accepted.id, queued.id);
    assert_eq!(accepted.status, "accepted");
    assert_eq!(accepted.token, 77);
    assert_eq!(accepted.size, Some(12));
    assert_eq!(matching_records, 1);
}

#[cfg_attr(test, test)]
#[cfg(feature = "full-controller-tests")]
pub(super) fn transfer_ids_and_tokens_wrap_without_collisions() {
    let mut queue = crate::TransferQueue::new_in_memory(8);
    let first = queue.create(0, Some("peer".to_owned()), "first".to_owned(), None, None);
    assert_eq!((first.id, first.token), (1, 1));
    queue.next_id = u64::MAX;
    queue.next_token = u32::MAX;
    let maximum = queue.create(0, Some("peer".to_owned()), "max".to_owned(), None, None);
    assert_eq!((maximum.id, maximum.token), (u64::MAX, u32::MAX));
    let wrapped = queue.create(0, Some("peer".to_owned()), "wrapped".to_owned(), None, None);
    assert_eq!((wrapped.id, wrapped.token), (2, 2));
    let rejected =
        queue.record_rejected_request(0, 99, "rejected".to_owned(), None, "test".to_owned());
    assert_eq!(rejected.id, 3);
    assert_eq!(
        queue
            .entries
            .iter()
            .map(|entry| entry.id)
            .collect::<std::collections::HashSet<_>>()
            .len(),
        queue.entries.len()
    );

    let mut duplicate = wrapped.clone();
    duplicate.filename = "newest".to_owned();
    crate::write_transfer_state(&queue.state_path, &[wrapped, duplicate]).unwrap();
    let loaded = crate::load_transfer_state(&queue.state_path, 8).unwrap();
    assert_eq!(loaded.len(), 1);
    assert_eq!(loaded[0].filename, "newest");
    let _ = std::fs::remove_file(&queue.state_path);
    let _ = std::fs::remove_file(&queue.events_path);
}

#[cfg_attr(test, tokio::test)]
#[cfg(feature = "full-controller-tests")]
pub(super) async fn outbound_message_routes_reject_before_mutation_when_dispatch_is_unavailable() {
    for (path, body) in [
        (
            "/api/messages",
            r#"{"username":"friend","body":"direct message"}"#,
        ),
        (
            "/api/conversations/friend",
            r#"{"body":"conversation message"}"#,
        ),
        (
            "/api/conversations/batch",
            r#"{"usernames":["friend","peer"],"body":"batch message"}"#,
        ),
    ] {
        let (state, receiver) = test_state();
        drop(receiver);

        let response = crate::route_http_request("POST", path, None, body, &state)
            .await
            .expect("unavailable dispatch response");
        assert_eq!(response.status, "503 Service Unavailable", "{path}");
        assert!(
            response.body.contains("session manager is not running"),
            "{path}"
        );

        let messages = state.messages.read().await;
        assert!(messages.records.is_empty(), "{path}");
        assert_eq!(messages.next_id, 1, "{path}");
        drop(messages);
        assert!(
            state
                .events
                .read()
                .await
                .records
                .iter()
                .all(|event| event.kind != "message.sent"),
            "{path}"
        );
    }
}

#[cfg_attr(test, tokio::test)]
#[cfg(feature = "full-controller-tests")]
pub(super) async fn inbound_private_message_replays_update_one_record_and_retain_replay_flag() {
    use slskr_client::protocol::server::{PrivateMessage, ServerMessage};
    let (state, _receiver) = test_state();
    let listener = tokio::net::TcpListener::bind("127.0.0.1:0").await.unwrap();
    let address = listener.local_addr().unwrap();
    let client = tokio::net::TcpStream::connect(address);
    let server = listener.accept();
    let (client, server) = tokio::join!(client, server);
    let (server, _) = server.unwrap();
    let mut session = slskr_client::server::ServerSession::new(
        slskr_client::stream::ServerConnection::new(server),
    );
    let _client = slskr_client::stream::ServerConnection::new(client.unwrap());
    let message = |replayed| {
        ServerMessage::MessageUserResponse(PrivateMessage {
            id: 77,
            timestamp: 88,
            username: "peer".to_owned(),
            message: "hello".to_owned(),
            is_new: true,
            was_replayed: replayed,
        })
    };
    crate::session_runtime::project_server_message(&state, &mut session, &message(false)).await;
    crate::session_runtime::project_server_message(&state, &mut session, &message(true)).await;
    let messages = state.messages.read().await;
    assert_eq!(messages.records.len(), 1);
    assert!(messages.records[0].was_replayed);
    drop(messages);
    let response = crate::route_http_request("GET", "/api/v0/conversations/peer", None, "", &state)
        .await
        .unwrap();
    let json = serde_json::from_str::<serde_json::Value>(&response.body).unwrap();
    assert_eq!(json["messages"].as_array().unwrap().len(), 1);
    assert_eq!(json["messages"][0]["wasReplayed"], true);
}

#[cfg_attr(test, tokio::test)]
#[cfg(feature = "full-controller-tests")]
pub(super) async fn transfer_group_yaml_validation_matches_frozen_target_contracts() {
    let cases = [
        (
            "transfers:\n  upload:\n    slots: 0\n",
            "Invalid configuration:\n  Transfers:\n    Upload:\n      The field Slots must be between 1 and 2147483647.",
        ),
        (
            "transfers:\n  groups:\n    default:\n      upload:\n        priority: 0\n",
            "Invalid configuration:\n  Transfers:\n    Groups:\n      Default:\n        Upload:\n          The field Priority must be between 1 and 2147483647.",
        ),
        (
            "transfers:\n  groups:\n    default:\n      upload:\n        strategy: invalid\n",
            "Invalid configuration:\n  Transfers:\n    Groups:\n      Default:\n        Upload:\n          The Strategy field must be one of: RoundRobin, FirstInFirstOut. Case insensitive.",
        ),
        (
            "transfers:\n  groups:\n    default:\n      upload:\n        limits:\n          queued:\n            files: 0\n",
            "Invalid configuration:\n  Transfers:\n    Groups:\n      Default:\n        Upload:\n          Limits:\n            Queued:\n              The field Files must be between 1 and 2147483647.",
        ),
    ];
    for target in ["slskd", "slskdn"] {
        let (state, _receiver) = test_state_with_env(
            MapEnv::default()
                .with("SLSKR_REMOTE_CONFIGURATION", "true")
                .with("SLSKR_CONTROLLER_PROFILE", target),
        );
        for (yaml, controller_error) in cases {
            let response = crate::route_http_request(
                "POST",
                "/api/v0/options/yaml/validate",
                None,
                &serde_json::to_string(yaml).unwrap(),
                &state,
            )
            .await
            .unwrap();
            assert_eq!(response.status, "200 OK", "{target}: {yaml}");
            assert_eq!(response.content_type, "application/json; charset=utf-8");
            assert_eq!(
                serde_json::from_str::<String>(&response.body).unwrap(),
                if target == "slskd" {
                    controller_error
                } else {
                    "Invalid YAML configuration"
                },
                "{target}: {yaml}"
            );
        }

        let daily_null = crate::route_http_request(
            "POST",
            "/api/v0/options/yaml/validate",
            None,
            &serde_json::to_string("transfers:\n  upload:\n    limits:\n      daily: null\n")
                .unwrap(),
            &state,
        )
        .await
        .unwrap();
        assert_eq!(daily_null.status, "200 OK", "{target}");
        if target == "slskd" {
            assert!(daily_null.content_type.is_empty());
            assert!(daily_null.body.is_empty());
        } else {
            assert_eq!(
                serde_json::from_str::<String>(&daily_null.body).unwrap(),
                "Invalid YAML configuration"
            );
        }
    }
}

#[cfg_attr(test, tokio::test)]
#[cfg(feature = "full-controller-tests")]
pub(super) async fn transfer_download_yaml_validation_matches_frozen_target_contracts() {
    let cases = [
        (
            "transfers:\n  download:\n    slots: 0\n",
            "Invalid configuration:\n  Transfers:\n    Download:\n      The field Slots must be between 1 and 2147483647.",
        ),
        (
            "transfers:\n  download:\n    retry:\n      attempts: 0\n",
            "Invalid configuration:\n  Transfers:\n    Download:\n      Retry:\n        The field Attempts must be between 1 and 2147483647.",
        ),
        (
            "transfers:\n  download:\n    destination:\n      subdirectory: ../escape\n",
            "Invalid configuration:\n  Transfers:\n    Download:\n      Destination:\n        The Subdirectory field contains one or more unsafe path traversal segments ('.' or '..')",
        ),
    ];
    for target in ["slskd", "slskdn"] {
        let (state, _receiver) = test_state_with_env(
            MapEnv::default()
                .with("SLSKR_REMOTE_CONFIGURATION", "true")
                .with("SLSKR_CONTROLLER_PROFILE", target),
        );
        for (yaml, controller_error) in cases {
            let response = crate::route_http_request(
                "POST",
                "/api/v0/options/yaml/validate",
                None,
                &serde_json::to_string(yaml).unwrap(),
                &state,
            )
            .await
            .unwrap();
            assert_eq!(response.status, "200 OK", "{target}: {yaml}");
            if target == "slskdn" && yaml.contains("destination:") {
                assert!(response.content_type.is_empty(), "{target}: {yaml}");
                assert!(response.body.is_empty(), "{target}: {yaml}");
                continue;
            }
            assert_eq!(response.content_type, "application/json; charset=utf-8");
            assert_eq!(
                serde_json::from_str::<String>(&response.body).unwrap(),
                if target == "slskd" {
                    controller_error
                } else {
                    "Invalid YAML configuration"
                },
                "{target}: {yaml}"
            );
        }
    }
}
