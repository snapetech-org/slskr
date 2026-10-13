import LocalizedText from "../Shared/LocalizedText";
import { interfaceText, interfaceTextProps, useInterfaceLanguage } from "../../lib/interfaceLocale";
import { createListeningPartyHubConnection } from '../../lib/hubFactory';
import { toDisplayError } from '../../lib/errors';
import * as listeningParty from '../../lib/listeningParty';
import { usePlayer } from './PlayerContext';
import { usePolling } from '../../lib/usePolling';
import React, { useCallback, useEffect, useRef, useState } from 'react';
import { toast } from 'react-toastify';
import { Button, Checkbox, Icon, Label, List, Message, Popup, Segment } from 'semantic-ui-react';

const applyPartyState = (state, player) => {
  if (!state || typeof state !== 'object' || Array.isArray(state)) return;

  if (state.action === 'play' || state.action === 'seek') {
    const elapsed =
      state.action === 'play'
        ? Math.max(0, (Date.now() - state.serverTimeUnixMs) / 1000)
        : 0;
    player.playItem(
      {
        album: state.album,
        artist: state.artist || state.hostPeerId,
        contentId: state.contentId,
        streamUrl: state.streamUrl,
        title: state.title || state.contentId,
      },
      {
        positionSeconds: (state.positionSeconds || 0) + elapsed,
        replaceQueue: true,
      },
    );
  } else if (state.action === 'pause') {
    player.pause();
  } else if (state.action === 'stop') {
    player.clear();
  }
};

const PodListenAlongPanel = ({ channelId, compact = false, podId, user }) => {
  useInterfaceLanguage();
  const player = usePlayer();
  const [connected, setConnected] = useState(false);
  const [directory, setDirectory] = useState([]);
  const [following, setFollowing] = useState(false);
  const [globalRadio, setGlobalRadio] = useState(false);
  const [meshStreaming, setMeshStreaming] = useState(false);
  const [partyState, setPartyState] = useState(null);
  const [partyStateError, setPartyStateError] = useState(null);
  const [directoryError, setDirectoryError] = useState(null);
  const [publishing, setPublishing] = useState(false);
  const followingRef = useRef(false);
  const playerRef = useRef(player);
  const mountedRef = useRef(false);
  const directoryRequestIdRef = useRef(0);
  const operationRequestIdRef = useRef(0);
  const publishInFlightRef = useRef(false);

  useEffect(() => {
    mountedRef.current = true;
    return () => {
      mountedRef.current = false;
      directoryRequestIdRef.current += 1;
      operationRequestIdRef.current += 1;
    };
  }, []);

  useEffect(() => {
    followingRef.current = following;
  }, [following]);

  useEffect(() => {
    playerRef.current = player;
  }, [player]);

  useEffect(() => {
    if (!podId || !channelId) return undefined;

    let disposed = false;
    const hub = createListeningPartyHubConnection();

    hub.on('partyState', (state) => {
      if (disposed || !mountedRef.current) return;
      const nextState =
        state && typeof state === 'object' && !Array.isArray(state)
          ? state
          : null;
      setPartyState(nextState);
      setPartyStateError(null);
      if (followingRef.current) {
        playerRef.current.followParty(nextState);
        applyPartyState(nextState, playerRef.current);
      }
    });
    hub.onreconnecting(() => {
      if (!disposed && mountedRef.current) setConnected(false);
    });
    hub.onreconnected(() => {
      if (!disposed && mountedRef.current) setConnected(true);
    });
    hub.onclose(() => {
      if (!disposed && mountedRef.current) setConnected(false);
    });

    hub
      .start()
      .then(() => {
        if (disposed || !mountedRef.current) return undefined;
        return hub.invoke('JoinParty', podId, channelId);
      })
      .then(() => {
        if (!disposed && mountedRef.current) setConnected(true);
      })
      .catch(() => {
        if (!disposed && mountedRef.current) setConnected(false);
      });

    listeningParty
      .getPartyState(podId, channelId)
      .then((state) => {
        if (!disposed && mountedRef.current) {
          setPartyState(
            state && typeof state === 'object' && !Array.isArray(state)
              ? state
              : null,
          );
          setPartyStateError(null);
        }
      })
      .catch((error) => {
        if (!disposed && mountedRef.current) {
          setPartyStateError(toDisplayError(error, 'Party state unavailable'));
        }
      });

    return () => {
      disposed = true;
      operationRequestIdRef.current += 1;
      publishInFlightRef.current = false;
      if (mountedRef.current) setPublishing(false);
      hub.invoke('LeaveParty', podId, channelId).catch(() => {});
      hub.stop().catch(() => {});
    };
  }, [channelId, podId]);

  const refreshDirectory = useCallback(async () => {
    if (!mountedRef.current) return;
    const requestId = ++directoryRequestIdRef.current;
    try {
      const nextDirectory = await listeningParty.getPartyDirectory();
      if (
        mountedRef.current &&
        requestId === directoryRequestIdRef.current
      ) {
        setDirectoryError(null);
        setDirectory(
          Array.isArray(nextDirectory)
            ? nextDirectory.filter(
                (party) =>
                  party && typeof party === 'object' && !Array.isArray(party),
              )
            : [],
        );
      }
    } catch (error) {
      if (
        mountedRef.current &&
        requestId === directoryRequestIdRef.current
      ) {
        setDirectoryError(toDisplayError(error, 'Radio directory unavailable'));
      }
    }
  }, []);

  usePolling(refreshDirectory, 30_000);

  const publish = async (action) => {
    const current = player.current;
    if (
      !mountedRef.current ||
      publishInFlightRef.current ||
      (action !== 'stop' && !current?.contentId)
    ) {
      return;
    }

    const requestId = ++operationRequestIdRef.current;
    publishInFlightRef.current = true;
    setPublishing(true);
    try {
      const state = await listeningParty.publishPartyState(podId, channelId, {
        action,
        album: current?.album || '',
        allowMeshStreaming: meshStreaming,
        artist: current?.artist || user || '',
        contentId: current?.contentId || '',
        hostPeerId: user || 'local-peer',
        listed: globalRadio,
        partyId: partyState?.partyId || '',
        positionSeconds: current?.positionSeconds || 0,
        title: current?.title || current?.fileName || '',
      });
      if (
        !mountedRef.current ||
        requestId !== operationRequestIdRef.current
      ) {
        return;
      }
      setPartyState(
        state && typeof state === 'object' && !Array.isArray(state)
          ? state
          : null,
      );
      setPartyStateError(null);
      await refreshDirectory();
    } catch (error) {
      console.error('[Listen Along] Failed to publish party state:', error);
      if (
        mountedRef.current &&
        requestId === operationRequestIdRef.current
      ) {
        toast.error(toDisplayError(error, 'Broadcast failed'));
      }
    } finally {
      publishInFlightRef.current = false;
      if (
        mountedRef.current &&
        requestId === operationRequestIdRef.current
      ) {
        setPublishing(false);
      }
    }
  };

  const joinListedParty = (party) => {
    if (!mountedRef.current || !party?.contentId) return;
    try {
      const streamUrl = listeningParty.buildRadioStreamUrl(party);
      player.followParty(party);
      player.playItem(
        {
          album: party.album,
          artist: party.artist || party.hostPeerId,
          contentId: party.contentId,
          streamUrl,
          title: party.title || party.contentId,
        },
        {
          replaceQueue: true,
          streamUrl,
        },
      );
    } catch (error) {
      console.error('[Listen Along] Failed to join listed party:', error);
      toast.error(toDisplayError(error, 'Unable to join listed party'));
    }
  };

  if (compact) {
    return (
      <Segment className="pod-listen-along pod-listen-along-compact">
        {(partyStateError || directoryError) && (
          <Message
            aria-live="polite"
            content={partyStateError || directoryError}
            negative
            size="tiny"
          />
        )}
        <div className="pod-listen-along-compact-status">
          <Popup
            content={
              partyState
                ? `${partyState.hostPeerId} ${partyState.action}: ${partyState.title || partyState.contentId}`
                : 'No active room broadcast'
            }
            trigger={
              <span
                aria-label={connected ? 'Listen Along live' : 'Listen Along offline'}
                className={`pod-listen-along-orb ${connected ? 'pod-listen-along-orb-live' : ''}`}
                role="status"
                title={connected ? 'Listen Along live' : 'Listen Along offline'}
              />
            }
          />
          <span className="pod-listen-along-compact-copy">
            {partyState ? partyState.title || partyState.contentId : <LocalizedText source={"Room broadcast"} />}
          </span>
        </div>
        <div className="pod-listen-along-compact-actions">
          <Popup
            content={interfaceText("Follow this room's broadcast using your own stream access.")}
            trigger={
              <Button
                active={following}
                aria-label={interfaceText("Follow room broadcast")}
                icon
                onClick={() => {
                  const next = !following;
                  setFollowing(next);
                  if (next && partyState) {
                    player.followParty(partyState);
                    applyPartyState(partyState, player);
                  } else {
                    player.followParty(null);
                  }
                }}
                size="mini"
                title={interfaceText("Follow room broadcast")}
               {...interfaceTextProps("Follow room broadcast")}>
                <Icon name={following ? 'volume up' : 'volume off'} />
              </Button>
            }
           {...interfaceTextProps("Follow this room's broadcast using your own stream access.")}/>
          <Popup
            content={interfaceText("Broadcast your current local player track to this room.")}
            trigger={
              <Button
                aria-label={interfaceText("Broadcast current track to room")}
                disabled={publishing || !player.current}
                icon
                onClick={() => publish('play')}
                size="mini"
                title={interfaceText("Broadcast current track to room")}
               {...interfaceTextProps("Broadcast current track to room")}>
                <Icon name="bullhorn" />
              </Button>
            }
           {...interfaceTextProps("Broadcast your current local player track to this room.")}/>
          <Popup
            content={interfaceText("List this room broadcast in the mesh radio directory.")}
            trigger={
              <Button
                active={globalRadio}
                aria-label={interfaceText("List room broadcast in mesh directory")}
                icon
                onClick={() => setGlobalRadio((value) => !value)}
                size="mini"
                title={interfaceText("List room broadcast in mesh directory")}
               {...interfaceTextProps("List room broadcast in mesh directory")}>
                <Icon name="broadcast tower" />
              </Button>
            }
           {...interfaceTextProps("List this room broadcast in the mesh radio directory.")}/>
          <Popup
            content={interfaceText("Allow directory listeners to stream the current track from this node.")}
            trigger={
              <Button
                active={meshStreaming}
                aria-label={interfaceText("Allow mesh streaming for broadcast")}
                disabled={!globalRadio}
                icon
                onClick={() => setMeshStreaming((value) => !value)}
                size="mini"
                title={interfaceText("Allow mesh streaming for broadcast")}
               {...interfaceTextProps("Allow mesh streaming for broadcast")}>
                <Icon name="wifi" />
              </Button>
            }
           {...interfaceTextProps("Allow directory listeners to stream the current track from this node.")}/>
          <Popup
            content={interfaceText("Stop broadcasting listen-along metadata for this room.")}
            trigger={
              <Button
                aria-label={interfaceText("Stop room broadcast")}
                disabled={publishing}
                icon
                onClick={() => publish('stop')}
                size="mini"
                title={interfaceText("Stop room broadcast")}
               {...interfaceTextProps("Stop room broadcast")}>
                <Icon name="stop" />
              </Button>
            }
           {...interfaceTextProps("Stop broadcasting listen-along metadata for this room.")}/>
        </div>
      </Segment>
    );
  }

  return (
    <Segment className="pod-listen-along">
      {(partyStateError || directoryError) && (
        <Message
          aria-live="polite"
          content={partyStateError || directoryError}
          negative
          size="tiny"
        />
      )}
      <div className="pod-listen-along-main">
        <div>
          <strong><LocalizedText source={"Listen Along"} /></strong>
          <div className="pod-listen-along-state">
            {partyState
              ? `${partyState.hostPeerId} ${partyState.action}: ${partyState.title || partyState.contentId}`
              : <LocalizedText source={"No active party"} />}
          </div>
        </div>
        <Label color={connected ? 'green' : 'grey'}>
          {connected ? <LocalizedText source={"Live"} /> : <LocalizedText source={"Offline"} />}
        </Label>
      </div>
      <div className="pod-listen-along-toggles">
        <Popup
          content={interfaceText("List this party in the slskr mesh radio directory so nearby mesh members can discover it.")}
          trigger={
            <Checkbox
              checked={globalRadio}
              label={interfaceText("List globally")}
              onChange={(event, data) => setGlobalRadio(data.checked)}
              toggle
             {...interfaceTextProps("List globally")}/>
          }
         {...interfaceTextProps("List this party in the slskr mesh radio directory so nearby mesh members can discover it.")}/>
        <Popup
          content={interfaceText("Allow listeners who join from the directory to stream this party's current track from this slskr node.")}
          trigger={
            <Checkbox
              checked={meshStreaming}
              disabled={!globalRadio}
              label={interfaceText("Mesh streaming")}
              onChange={(event, data) => setMeshStreaming(data.checked)}
              toggle
             {...interfaceTextProps("Mesh streaming")}/>
          }
         {...interfaceTextProps("Allow listeners who join from the directory to stream this party's current track from this slskr node.")}/>
      </div>
      <Button.Group size="small">
        <Popup
          content={interfaceText("Follow this pod's host playback using your own stream access.")}
          trigger={
            <Button
              active={following}
              icon
              onClick={() => {
                const next = !following;
                setFollowing(next);
                if (next && partyState) {
                  player.followParty(partyState);
                  applyPartyState(partyState, player);
                } else {
                  player.followParty(null);
                }
              }}
            >
              <Icon name={following ? 'volume up' : 'volume off'} />
            </Button>
          }
         {...interfaceTextProps("Follow this pod's host playback using your own stream access.")}/>
        <Popup
          content={interfaceText("Publish your current local player track as the pod listen-along host.")}
          trigger={
            <Button
              disabled={publishing || !player.current}
              icon
              onClick={() => publish('play')}
            >
              <Icon name="bullhorn" />
            </Button>
          }
         {...interfaceTextProps("Publish your current local player track as the pod listen-along host.")}/>
        <Popup
          content={interfaceText("Stop hosting listen-along metadata for this pod.")}
          trigger={
            <Button
              disabled={publishing}
              icon
              onClick={() => publish('stop')}
            >
              <Icon name="stop" />
            </Button>
          }
         {...interfaceTextProps("Stop hosting listen-along metadata for this pod.")}/>
      </Button.Group>
      {directory.length > 0 && (
        <div className="pod-listen-along-directory">
          <strong><LocalizedText source={"Listed radio"} /></strong>
          <List divided relaxed>
            {directory.slice(0, 6).map((party) => (
              <List.Item key={party.partyId}>
                <List.Content floated="right">
                  <Popup
                    content={interfaceText("Join this listed radio party and stream from the host's integrated slskr endpoint when available.")}
                    trigger={
                      <Button
                        disabled={!party.allowMeshStreaming}
                        icon
                        onClick={() => joinListedParty(party)}
                        size="mini"
                      >
                        <Icon name="play" />
                      </Button>
                    }
                   {...interfaceTextProps("Join this listed radio party and stream from the host's integrated slskr endpoint when available.")}/>
                </List.Content>
                <List.Content>
                  <List.Header>{party.title || party.contentId}</List.Header>
                  <List.Description>
                    {party.hostPeerId}
                    {party.allowMeshStreaming ? <LocalizedText source={"| streamable"} /> : <LocalizedText source={"| metadata only"} />}
                  </List.Description>
                </List.Content>
              </List.Item>
            ))}
          </List>
        </div>
      )}
    </Segment>
  );
};

export default PodListenAlongPanel;
