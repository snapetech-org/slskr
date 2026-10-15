import LocalizedText from "../Shared/LocalizedText";
import { interfaceText, interfaceTextAttributes, interfaceTextProps, useInterfaceLanguage } from "../../lib/interfaceLocale";
import './Messaging.css';
import * as chat from '../../lib/chat';
import {
  createMessagesHubConnection,
  createRoomsHubConnection,
} from '../../lib/hubFactory';
import { toDisplayError } from '../../lib/errors';
import {
  historyCursor,
  isAbortError,
  mergeMessageHistory,
  messageKey,
} from '../../lib/messageHistory';
import * as pods from '../../lib/pods';
import * as rooms from '../../lib/rooms';
import { getLocalStorageItem, setLocalStorageItem } from '../../lib/storage';
import { usePolling } from '../../lib/usePolling';
import ChatSession from '../Chat/ChatSession';
import PodListenAlongPanel from '../Player/PodListenAlongPanel';
import PlaceholderSegment from '../Shared/PlaceholderSegment';
import MessagingSidebar from './MessagingSidebar';
import BatchPrivateMessageModal from './BatchPrivateMessageModal';
import RoomSession from '../Rooms/RoomSession';
import UserCard from '../Shared/UserCard';
import {
  GOLD_STAR_CLUB_POD_ID,
  MAX_PANELS,
  asRecords,
  normalizePanel,
  loadPanels,
  savePanels,
  makePanel,
  encodePodTarget,
  decodePodTarget,
  channelLabel,
  normalizeConversationName,
  isPodDirectChannel,
  panelLabel,
} from './messagingWorkspaceState';
import PodChannelSession from './PodChannelSession';
import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { toast } from 'react-toastify';
import {
  Button,
  Card,
  Icon,
  Label,
  Popup,
  Segment,
} from 'semantic-ui-react';

const WORKSPACE_EVENT_REFRESH_INTERVAL_MS = 1_000;

const Messaging = ({ runtimeProfile, initialKind = 'mixed', state }) => {
  useInterfaceLanguage();
  const navigate = useNavigate();
  const [panels, setPanels] = useState(() => loadPanels());
  const [chatTarget, setChatTarget] = useState('');
  const [conversations, setConversations] = useState([]);
  const [joinedRooms, setJoinedRooms] = useState([]);
  const [podChannels, setPodChannels] = useState([]);
  const [availableRooms, setAvailableRooms] = useState([]);
  const [availableRoomsError, setAvailableRoomsError] = useState('');
  const [workspaceError, setWorkspaceError] = useState('');
  const [batchMessage, setBatchMessage] = useState('');
  const [batchModalOpen, setBatchModalOpen] = useState(false);
  const [batchSending, setBatchSending] = useState(false);
  const [batchUsernames, setBatchUsernames] = useState('');
  const [roomSearchLoading, setRoomSearchLoading] = useState(false);
  const mountedRef = useRef(false);
  const hydrateRequestIdRef = useRef(0);
  const workspaceRefreshInFlightRef = useRef(false);
  const workspaceRefreshPendingRef = useRef(false);
  const workspaceEventRefreshTimerRef = useRef(null);
  const availableRoomsRequestIdRef = useRef(0);
  const workspaceActionRequestIdRef = useRef(new Map());
  const batchRequestIdRef = useRef(0);
  const workspaceActionInFlightRef = useRef(new Set());
  const batchInFlightRef = useRef(false);
  const roomsRequestInFlightRef = useRef(false);
  const [workspaceActionKeys, setWorkspaceActionKeys] = useState([]);

  useEffect(() => {
    mountedRef.current = true;
    return () => {
      mountedRef.current = false;
      hydrateRequestIdRef.current += 1;
      workspaceRefreshInFlightRef.current = false;
      workspaceRefreshPendingRef.current = false;
      if (workspaceEventRefreshTimerRef.current !== null) {
        window.clearTimeout(workspaceEventRefreshTimerRef.current);
        workspaceEventRefreshTimerRef.current = null;
      }
      availableRoomsRequestIdRef.current += 1;
      workspaceActionRequestIdRef.current.clear();
      workspaceActionInFlightRef.current.clear();
      batchRequestIdRef.current += 1;
    };
  }, []);

  const openPanel = useCallback((type, target, metadata = {}) => {
    const trimmed = `${target || ''}`.trim();
    if (!trimmed) {
      return;
    }

    setPanels((previous) => {
      const existing = previous.find(
        (panel) => panel.type === type && panel.target === trimmed,
      );
      if (existing) {
        return previous.map((panel) =>
          panel.id === existing.id
            ? { ...panel, ...metadata, collapsed: false }
            : panel,
        );
      }

      return [
        ...previous,
        normalizePanel({
          ...makePanel(type, trimmed),
          label: metadata.label,
        }),
      ].filter(Boolean).slice(-MAX_PANELS);
    });
  }, []);

  const closePanel = useCallback((panelId) => {
    setPanels((previous) => previous.filter((panel) => panel.id !== panelId));
  }, []);

  const setPanelCollapsed = useCallback((panelId, collapsed) => {
    setPanels((previous) =>
      previous.map((panel) =>
        panel.id === panelId ? { ...panel, collapsed } : panel,
      ),
    );
  }, []);

  const hydrate = useCallback(async () => {
    const requestId = ++hydrateRequestIdRef.current;
    if (!mountedRef.current) return false;

    const [
      serverConversationsResult,
      serverJoinedRoomsResult,
      serverPodsResult,
      serverDiscoveredPodsResult,
    ] = await Promise.allSettled([
      chat.getAll(),
      rooms.getJoined(),
      pods.list(),
      runtimeProfile === 'native'
        ? pods.discoverAll(50)
        : Promise.resolve([]),
    ]);
    const failures = [];
    const resultValue = (result, label) => {
      if (result.status === 'fulfilled') return result.value;
      failures.push(`${label}: ${toDisplayError(result.reason)}`);
      return null;
    };
    const serverConversations = resultValue(
      serverConversationsResult,
      'Saved conversations',
    );
    const serverJoinedRooms = resultValue(
      serverJoinedRoomsResult,
      'Joined rooms',
    );
    const serverPods = resultValue(serverPodsResult, 'Pods');
    const serverDiscoveredPods = resultValue(
      serverDiscoveredPodsResult,
      'Pod discovery',
    );
    const conversationsList = Array.isArray(serverConversations)
      ? serverConversations
      : null;
    const joinedRoomList = Array.isArray(serverJoinedRooms)
      ? serverJoinedRooms
      : null;
    const podList = Array.isArray(serverPods)
      ? asRecords(serverPods).filter((pod) => pod.podId)
      : null;
    let podDetails = null;
    if (runtimeProfile === 'native') {
      if (Array.isArray(serverDiscoveredPods)) {
        const discovered = asRecords(serverDiscoveredPods);
        if (discovered.length > 0) {
          podDetails = discovered;
        } else if (podList) {
          podDetails = podList;
        }
      } else if (podList) {
        podDetails = podList;
      }
    } else if (podList) {
      const detailResults = await Promise.allSettled(
        podList.map((pod) => pods.get(pod.podId)),
      );
      podDetails = detailResults.map((result, index) => {
        if (result.status === 'fulfilled') return result.value;
        failures.push(
          `Pod ${podList[index].podId}: ${toDisplayError(result.reason)}`,
        );
        return podList[index];
      });
    }

    if (
      !mountedRef.current ||
      requestId !== hydrateRequestIdRef.current
    ) {
      return false;
    }

    if (conversationsList) {
      setConversations(
        conversationsList
          .filter((conversation) => typeof conversation?.username === 'string' && conversation.username.trim())
          .map((conversation) => ({
            ...conversation,
            hasUnAcknowledgedMessages: Boolean(conversation.hasUnAcknowledgedMessages),
            username: conversation.username.trim(),
          }))
          .sort((a, b) => {
            if (a.hasUnAcknowledgedMessages !== b.hasUnAcknowledgedMessages) {
              return a.hasUnAcknowledgedMessages ? -1 : 1;
            }

            return a.username.localeCompare(b.username);
          }),
      );
    }
    if (joinedRoomList) {
      setJoinedRooms(
        joinedRoomList
          .filter((roomName) => typeof roomName === 'string' && roomName.trim())
          .map((roomName) => roomName.trim())
          .sort(),
      );
    }
    if (podDetails) {
      setPodChannels(
        podDetails
          .filter((pod) => pod?.podId)
          .flatMap((pod) =>
            asRecords(pod.channels)
              .filter((channel) => channel.channelId || channel.id)
              .map((channel) => {
                const channelId = `${channel.channelId || channel.id}`;
                const podId = `${pod.podId}`;
                return {
                  channelId,
                  channelKind: `${channel.kind || channel.channelKind || ''}`,
                  channelName: `${channel.name || channel.channelName || channelId}`,
                  podId,
                  podName: `${pod.name || podId}`,
                  target: encodePodTarget(podId, channelId),
                };
              }),
          )
          .sort((a, b) => channelLabel(a).localeCompare(channelLabel(b))),
      );
    }
    if (mountedRef.current && requestId === hydrateRequestIdRef.current) {
      setWorkspaceError(
        failures.length > 0
          ? `Some messaging data could not be loaded: ${failures.join('; ')}`
          : '',
      );
    }
    return true;
  }, [runtimeProfile]);

  const refreshWorkspace = useCallback(async () => {
    if (workspaceRefreshInFlightRef.current) {
      workspaceRefreshPendingRef.current = true;
      return false;
    }

    workspaceRefreshInFlightRef.current = true;
    try {
      return await hydrate();
    } catch (error) {
      console.error('Failed to hydrate messaging workspace:', error);
      if (mountedRef.current) {
        setWorkspaceError(
          toDisplayError(error, 'Failed to hydrate messaging workspace'),
        );
      }
      return false;
    } finally {
      workspaceRefreshInFlightRef.current = false;
      if (workspaceRefreshPendingRef.current && mountedRef.current) {
        workspaceRefreshPendingRef.current = false;
        Promise.resolve().then(() => {
          if (mountedRef.current) void refreshWorkspace();
        });
      }
    }
  }, [hydrate]);

  const scheduleEventDrivenWorkspaceRefresh = useCallback(() => {
    if (
      !mountedRef.current ||
      workspaceEventRefreshTimerRef.current !== null
    ) {
      return;
    }

    const refreshWhenIdle = () => {
      if (!mountedRef.current) {
        workspaceEventRefreshTimerRef.current = null;
        return;
      }

      if (workspaceRefreshInFlightRef.current) {
        workspaceEventRefreshTimerRef.current = window.setTimeout(
          refreshWhenIdle,
          100,
        );
        return;
      }

      workspaceEventRefreshTimerRef.current = null;
      void refreshWorkspace();
    };

    workspaceEventRefreshTimerRef.current = window.setTimeout(
      refreshWhenIdle,
      WORKSPACE_EVENT_REFRESH_INTERVAL_MS,
    );
  }, [refreshWorkspace]);

  const beginWorkspaceAction = useCallback((key) => {
    if (!mountedRef.current || !key || workspaceActionInFlightRef.current.has(key)) {
      return false;
    }
    workspaceActionInFlightRef.current.add(key);
    setWorkspaceActionKeys(Array.from(workspaceActionInFlightRef.current));
    return true;
  }, []);

  const finishWorkspaceAction = useCallback((key) => {
    workspaceActionInFlightRef.current.delete(key);
    if (mountedRef.current) {
      setWorkspaceActionKeys(Array.from(workspaceActionInFlightRef.current));
    }
  }, []);

  const isWorkspaceActionPending = useCallback(
    (key) => workspaceActionKeys.includes(key),
    [workspaceActionKeys],
  );

  const savedChatNames = useMemo(
    () =>
      new Set(
        conversations.map((conversation) =>
          normalizeConversationName(conversation.username),
        ),
      ),
    [conversations],
  );

  const bridgedPodNames = useMemo(
    () =>
      new Set(
        podChannels
          .filter(
            (channel) =>
              isPodDirectChannel(channel) &&
              savedChatNames.has(normalizeConversationName(channel.podName)),
          )
          .map((channel) => normalizeConversationName(channel.podName)),
      ),
    [podChannels, savedChatNames],
  );

  const hiddenPodDirectTargets = useMemo(
    () =>
      new Set(
        podChannels
          .filter((channel) => isPodDirectChannel(channel))
          .map((channel) => channel.target),
      ),
    [podChannels],
  );

  const visiblePodChannels = useMemo(
    () =>
      podChannels.filter((channel) => !isPodDirectChannel(channel)),
    [podChannels],
  );

  usePolling(refreshWorkspace, 60_000);

  useEffect(() => {
    let disposed = false;
    const messagesHub = createMessagesHubConnection();
    const roomsHub = createRoomsHubConnection();
    const refresh = () => {
      if (disposed || !mountedRef.current) return;
      scheduleEventDrivenWorkspaceRefresh();
    };
    messagesHub.on('changed', refresh);
    roomsHub.on('changed', refresh);
    messagesHub.start().catch((error) => {
      if (!disposed) {
        console.error('Failed to start messages event feed:', error);
      }
    });
    roomsHub.start().catch((error) => {
      if (!disposed) {
        console.error('Failed to start rooms event feed:', error);
      }
    });
    return () => {
      disposed = true;
      hydrateRequestIdRef.current += 1;
      messagesHub.stop().catch(() => {});
      roomsHub.stop().catch(() => {});
    };
  }, [scheduleEventDrivenWorkspaceRefresh]);

  useEffect(() => {
    savePanels(panels);
  }, [panels]);

  useEffect(() => {
    if (hiddenPodDirectTargets.size === 0) {
      return;
    }

    setPanels((previous) =>
      previous.filter(
        (panel) =>
          !(panel.type === 'pod' && hiddenPodDirectTargets.has(panel.target)),
      ),
    );
  }, [hiddenPodDirectTargets]);

  useEffect(() => {
    if (panels.length > 0) {
      return;
    }

    if (initialKind === 'chat' && conversations[0]?.username) {
      openPanel('chat', conversations[0].username);
    }

    if (initialKind === 'room' && joinedRooms[0]) {
      openPanel('room', joinedRooms[0]);
    }

    if (initialKind === 'pod' && visiblePodChannels[0]) {
      openPanel('pod', visiblePodChannels[0].target, {
        label: channelLabel(visiblePodChannels[0]),
      });
    }
  }, [
    conversations,
    initialKind,
    joinedRooms,
    openPanel,
    panels.length,
    visiblePodChannels,
  ]);

  const fetchAvailableRooms = async () => {
    const requestId = ++availableRoomsRequestIdRef.current;
    if (!mountedRef.current || roomsRequestInFlightRef.current) return;

    roomsRequestInFlightRef.current = true;
    setRoomSearchLoading(true);
    try {
      const available = await rooms.getAvailable();
      if (
        mountedRef.current &&
        requestId === availableRoomsRequestIdRef.current
      ) {
        setAvailableRooms(
          asRecords(available)
            .filter((room) => typeof room.name === 'string' && room.name.trim())
            .map((room) => ({
              ...room,
              name: room.name.trim(),
              userCount: Number.isFinite(Number(room.userCount))
                ? Number(room.userCount)
                : 0,
            })),
        );
        setAvailableRoomsError('');
      }
    } catch (error) {
      if (
        mountedRef.current &&
        requestId === availableRoomsRequestIdRef.current
      ) {
        setAvailableRoomsError(
          toDisplayError(error, 'Failed to load available rooms'),
        );
      }
    } finally {
      if (
        mountedRef.current &&
        requestId === availableRoomsRequestIdRef.current
      ) {
        setRoomSearchLoading(false);
      }
      roomsRequestInFlightRef.current = false;
    }
  };

  const joinRoom = async (roomName) => {
    const actionKey = `room:join:${roomName}`;
    if (!roomName || !beginWorkspaceAction(actionKey)) {
      return;
    }

    const requestId = (workspaceActionRequestIdRef.current.get(actionKey) || 0) + 1;
    workspaceActionRequestIdRef.current.set(actionKey, requestId);
    try {
      await rooms.join({ roomName });
      if (!(await refreshWorkspace())) return;
      if (
        mountedRef.current &&
        requestId === workspaceActionRequestIdRef.current.get(actionKey)
      ) {
        openPanel('room', roomName);
      }
    } catch (error) {
      console.error('Failed to join room:', error);
      if (mountedRef.current) {
        toast.error(interfaceText('Failed to join room: {error}', { error: toDisplayError(error) }));
      }
    } finally {
      finishWorkspaceAction(actionKey);
    }
  };

  const leaveRoom = async (roomName) => {
    if (
      !window.confirm(
        `Leave room "${roomName}"? This exits the room and removes it from joined rooms.`,
      )
    ) {
      return;
    }
    const actionKey = `room:leave:${roomName}`;
    if (!beginWorkspaceAction(actionKey)) return;

    const requestId = (workspaceActionRequestIdRef.current.get(actionKey) || 0) + 1;
    workspaceActionRequestIdRef.current.set(actionKey, requestId);
    try {
      await rooms.leave({ roomName });
      if (!(await refreshWorkspace())) return;
      if (
        mountedRef.current &&
        requestId === workspaceActionRequestIdRef.current.get(actionKey)
      ) {
        setPanels((previous) =>
          previous.filter(
            (panel) => !(panel.type === 'room' && panel.target === roomName),
          ),
        );
      }
    } catch (error) {
      console.error('Failed to leave room:', error);
      if (mountedRef.current) {
        toast.error(interfaceText('Failed to leave room: {error}', { error: toDisplayError(error) }));
      }
    } finally {
      finishWorkspaceAction(actionKey);
    }
  };

  const deleteConversation = async (username) => {
    if (
      !window.confirm(
        `Permanently delete the saved message thread with "${username}"?`,
      )
    ) {
      return;
    }
    const actionKey = `chat:delete:${username}`;
    if (!beginWorkspaceAction(actionKey)) return;

    const requestId = (workspaceActionRequestIdRef.current.get(actionKey) || 0) + 1;
    workspaceActionRequestIdRef.current.set(actionKey, requestId);
    try {
      await chat.remove({ username });
      if (!(await refreshWorkspace())) return;
      if (
        mountedRef.current &&
        requestId === workspaceActionRequestIdRef.current.get(actionKey)
      ) {
        setPanels((previous) =>
          previous.filter(
            (panel) => !(panel.type === 'chat' && panel.target === username),
          ),
        );
      }
    } catch (error) {
      console.error('Failed to delete conversation:', error);
      if (mountedRef.current) {
        toast.error(interfaceText('Failed to delete conversation: {error}', { error: toDisplayError(error) }));
      }
    } finally {
      finishWorkspaceAction(actionKey);
    }
  };

  const leavePod = async (channel) => {
    const peerId = state?.user?.username || 'local-peer';
    const podName = channel?.podName || channel?.podId;
    if (!channel?.podId || !peerId) {
      return;
    }

    const prompt =
      channel.podId === GOLD_STAR_CLUB_POD_ID
        ? `Permanently leave ${podName}? Gold Star Club membership is irrevocable and cannot be recovered.`
        : `Leave pod "${podName}"? This exits the pod and removes its channels from Messages.`;

    if (!window.confirm(prompt)) {
      return;
    }
    const actionKey = `pod:leave:${channel.podId}`;
    if (!beginWorkspaceAction(actionKey)) return;

    const requestId = (workspaceActionRequestIdRef.current.get(actionKey) || 0) + 1;
    workspaceActionRequestIdRef.current.set(actionKey, requestId);
    try {
      await pods.leave(channel.podId, peerId);
      if (!(await refreshWorkspace())) return;
      if (
        mountedRef.current &&
        requestId === workspaceActionRequestIdRef.current.get(actionKey)
      ) {
        setPanels((previous) =>
          previous.filter((panel) => {
            if (panel.type !== 'pod') return true;
            const { podId } = decodePodTarget(panel.target);
            return podId !== channel.podId;
          }),
        );
      }
    } catch (error) {
      console.error('Failed to leave pod:', error);
      if (mountedRef.current) {
        toast.error(interfaceText('Failed to leave pod: {error}', { error: toDisplayError(error) }));
      }
    } finally {
      finishWorkspaceAction(actionKey);
    }
  };

  const sendBatchMessage = async () => {
    const usernames = batchUsernames
      .split(/[\s,;]+/)
      .map((username) => username.trim())
      .filter(Boolean);
    const message = batchMessage.trim();

    if (usernames.length === 0) {
      toast.error(interfaceText("At least one recipient is required"));
      return;
    }

    if (!message) {
      toast.error(interfaceText("Message is required"));
      return;
    }

    if (!mountedRef.current || batchInFlightRef.current) return;
    batchInFlightRef.current = true;
    const requestId = ++batchRequestIdRef.current;
    setBatchSending(true);
    try {
      await chat.sendBatch({ message, usernames });
      if (
        !mountedRef.current ||
        requestId !== batchRequestIdRef.current
      ) {
        return;
      }
      toast.success(interfaceText("Sent batch message to {size} users", { "size": (new Set(usernames.map((name) => name.toLowerCase())).size) }));
      setBatchMessage('');
      setBatchUsernames('');
      setBatchModalOpen(false);
      await refreshWorkspace();
    } catch (error) {
      if (
        mountedRef.current &&
        requestId === batchRequestIdRef.current
      ) {
        toast.error(toDisplayError(error, 'Failed to send batch message'));
      }
    } finally {
      if (
        mountedRef.current &&
        requestId === batchRequestIdRef.current
      ) {
        setBatchSending(false);
      }
      batchInFlightRef.current = false;
    }
  };

  const roomOptions = useMemo(
    () =>
      availableRooms.map((room) => ({
        description: room.isPrivate ? 'Private' : '',
        key: room.name,
        text: `${room.name} (${room.userCount} users)`,
        value: room.name,
      })),
    [availableRooms],
  );

  const openPanels = panels.filter((panel) => !panel.collapsed);
  const collapsedPanels = panels.filter((panel) => panel.collapsed);

  return (
    <div className="messaging-workspace">
      <div className="messaging-shell">
        <MessagingSidebar
          actions={{
            deleteConversation,
            fetchAvailableRooms,
            isWorkspaceActionPending,
            joinRoom,
            leavePod,
            leaveRoom,
            openPanel,
            refreshWorkspace,
            setChatTarget,
          }}
          state={{
            availableRoomsError,
            bridgedPodNames,
            chatTarget,
            conversations,
            joinedRooms,
            roomOptions,
            roomSearchLoading,
            visiblePodChannels,
            workspaceError,
          }}
        />

        <div className="messaging-main">
          <Segment className="messaging-toolbar">
            <div className="messaging-toolbar-title">
              <Icon name="window restore outline" />
              <LocalizedText source={"Workspace"} /><Label size="small">{openPanels.length} <LocalizedText source={"open"} /></Label>
            </div>
            <Popup
              content={interfaceText("Send one private message to multiple users through the native Soulseek batch command.")}
              trigger={
                <Button
                  aria-label={interfaceText("Open batch private-message dialog")}
                  icon="send"
                  onClick={() => setBatchModalOpen(true)}
                  size="small"
                  title={interfaceText("Batch private message")}
                 {...interfaceTextProps("Open batch private-message dialog")}/>
              }
             {...interfaceTextProps("Send one private message to multiple users through the native Soulseek batch command.")}/>
            <Popup
              content={interfaceText("Collapse every open message panel into the dock.")}
              trigger={
                <Button
                  aria-label={interfaceText("Collapse all message panels")}
                  disabled={openPanels.length === 0}
                  icon="window minimize outline"
                  onClick={() =>
                    setPanels((previous) =>
                      previous.map((panel) => ({ ...panel, collapsed: true })),
                    )
                  }
                  size="small"
                  title={interfaceText("Collapse all message panels")}
                 {...interfaceTextProps("Collapse all message panels")}/>
              }
             {...interfaceTextProps("Collapse every open message panel into the dock.")}/>
          </Segment>

          <BatchPrivateMessageModal
            actions={{
              sendBatchMessage,
              setBatchMessage,
              setBatchModalOpen,
              setBatchUsernames,
            }}
            state={{
              batchMessage,
              batchModalOpen,
              batchSending,
              batchUsernames,
            }}
          />

          {openPanels.length === 0 ? (
            <PlaceholderSegment
              caption="Open a saved chat, joined room, or pod channel to start a workspace panel"
              className="messaging-empty"
              icon="comments"
            />
          ) : (
            <div className="messaging-window-grid">
              {openPanels.map((panel) => {
                const panelPodChannel =
                  panel.type === 'pod'
                    ? podChannels.find(
                      (channel) => channel.target === panel.target,
                    ) || {
                      ...decodePodTarget(panel.target),
                      podName: panel.label,
                    }
                    : null;

                return (
                  <Card
                    className="messaging-window"
                    key={panel.id}
                  >
                    <Card.Content className="messaging-window-title">
                      <div className="messaging-window-heading">
                        <Icon
                          name={
                            panel.type === 'room'
                              ? 'comments'
                              : panel.type === 'pod'
                                ? 'comments outline'
                                : 'comment'
                          }
                        />
                        <span>
                          {panel.type === 'chat' ? (
                            <UserCard username={panel.target}>{panel.target}</UserCard>
                          ) : (
                            panelLabel(panel)
                          )}
                        </span>
                      </div>
                      <div className="messaging-window-actions">
                        {panel.type === 'chat' && (
                          <>
                            <Popup
                              content={interfaceText("Open this user's profile.")}
                              trigger={
                                <Button
                                  aria-label={interfaceText("Open {target} profile", { "target": (panel.target) })}
                                  icon="user"
                                  onClick={() =>
                                    navigate('/users', { state: { user: panel.target } })
                                  }
                                  size="mini"
                                  title={interfaceText("Open {target} profile", { "target": (panel.target) })}
                                 {...interfaceTextProps("Open {target} profile")}/>
                              }
                             {...interfaceTextProps("Open this user's profile.")}/>
                            <Popup
                              content={interfaceText("Permanently delete this saved message thread.")}
                              trigger={
                                <Button
                                  aria-label={interfaceText("Delete message thread with {target}", { "target": (panel.target) })}
                                  disabled={isWorkspaceActionPending(`chat:delete:${panel.target}`)}
                                  icon="trash alternate"
                                  negative
                                  onClick={() => deleteConversation(panel.target)}
                                  size="mini"
                                  title={interfaceText("Delete message thread with {target}", { "target": (panel.target) })}
                                 {...interfaceTextProps("Delete message thread with {target}")}/>
                              }
                             {...interfaceTextProps("Permanently delete this saved message thread.")}/>
                          </>
                        )}
                        {panel.type === 'room' && (
                          <Popup
                            content={interfaceText("Leave this room and remove it from joined rooms.")}
                            trigger={
                              <Button
                                aria-label={interfaceText("Leave room {target}", { "target": (panel.target) })}
                                disabled={isWorkspaceActionPending(`room:leave:${panel.target}`)}
                                icon="sign-out"
                                negative
                                onClick={() => leaveRoom(panel.target)}
                                size="mini"
                                title={interfaceText("Leave room {target}", { "target": (panel.target) })}
                               {...interfaceTextProps("Leave room {target}")}/>
                            }
                           {...interfaceTextProps("Leave this room and remove it from joined rooms.")}/>
                        )}
                        {panel.type === 'pod' && panelPodChannel && (
                          <Popup
                            content={interfaceText("Leave this pod and remove its channels from Messages.")}
                            trigger={
                              <Button
                                aria-label={interfaceText("Leave pod {podName}", { "podName": (panelPodChannel.podName) })}
                                disabled={isWorkspaceActionPending(`pod:leave:${panelPodChannel.podId}`)}
                                icon="sign-out"
                                negative
                                onClick={() => leavePod(panelPodChannel)}
                                size="mini"
                                title={interfaceText("Leave pod {podName}", { "podName": (panelPodChannel.podName) })}
                               {...interfaceTextProps("Leave pod {podName}")}/>
                            }
                           {...interfaceTextProps("Leave this pod and remove its channels from Messages.")}/>
                        )}
                        <Popup
                          content={interfaceText("Collapse this panel into the message dock.")}
                          trigger={
                            <Button
                              {...interfaceTextAttributes('Collapse {panel}', { panel: panelLabel(panel) })}
                              icon="window minimize outline"
                              onClick={() => setPanelCollapsed(panel.id, true)}
                              size="mini"
                              title={interfaceText('Collapse {panel}', { panel: panelLabel(panel) })}
                            />
                          }
                         {...interfaceTextProps("Collapse this panel into the message dock.")}/>
                        <Popup
                          content={interfaceText("Close this panel without deleting the thread or leaving anything.")}
                          trigger={
                            <Button
                              {...interfaceTextAttributes('Close {panel}', { panel: panelLabel(panel) })}
                              icon="close"
                              onClick={() => closePanel(panel.id)}
                              size="mini"
                              title={interfaceText('Close {panel}', { panel: panelLabel(panel) })}
                            />
                          }
                         {...interfaceTextProps("Close this panel without deleting the thread or leaving anything.")}/>
                      </div>
                    </Card.Content>
                    <Card.Content className="messaging-window-body">
                      {panel.type === 'chat' ? (
                        <ChatSession
                          active
                          onDelete={() => closePanel(panel.id)}
                          user={state?.user}
                          username={panel.target}
                        />
                      ) : panel.type === 'pod' ? (
                        <PodChannelSession
                          channel={panelPodChannel}
                          state={state}
                        />
                      ) : (
                        <RoomSession
                          active
                          onBrowseShares={(username) =>
                            navigate('/browse', { state: { user: username } })
                          }
                          onLeaveRoom={leaveRoom}
                          onUserProfile={(username) =>
                            navigate('/users', { state: { user: username } })
                          }
                          roomName={panel.target}
                        />
                      )}
                    </Card.Content>
                  </Card>
                );
              })}
            </div>
          )}

          {collapsedPanels.length > 0 && (
            <div className="messaging-dock">
              {collapsedPanels.map((panel) => (
                <Popup
                  content={interfaceText("Restore this message panel.")}
                  key={panel.id}
                  trigger={
                    <Button
                      basic
                      compact
                      onClick={() => setPanelCollapsed(panel.id, false)}
                      size="small"
                    >
                      <Icon name={panel.type === 'room' ? 'comments' : 'comment'} />
                      {panelLabel(panel)}
                    </Button>
                  }
                 {...interfaceTextProps("Restore this message panel.")}/>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Messaging;
