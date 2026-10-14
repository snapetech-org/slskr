import LocalizedText from "../../Shared/LocalizedText";
import { interfaceText, interfaceTextProps, useInterfaceLanguage } from "../../../lib/interfaceLocale";


import { formatRegionalDateTime, useRegionalFormat, formatRegionalFixedNumber, formatRegionalNumber } from '../../../lib/util';
import * as mediacore from '../../../lib/mediacore';
import { toDisplayError } from '../../../lib/errors';
import Button from './MediaCoreButton';
import PodMessageMaintenanceActions from './PodMessageMaintenanceActions';
import PodWorkflowNotice from './PodWorkflowNotice';
import React, { useEffect, useRef } from 'react';
import { toast } from 'react-toastify';
import {
  Card,
  Form,
  Grid,
  Header,
  Icon,
  Message,
} from 'semantic-ui-react';

const useMountedState = (mountedRef, initialValue) => {
  const [value, setValue] = React.useState(initialValue);
  const setMountedValue = React.useCallback(
    (nextValue) => {
      if (mountedRef.current) {
        setValue(nextValue);
      }
    },
    [mountedRef],
  );

  return [value, setMountedValue];
};

const PodMessageRoutingPanel = ({ visible = true }) => {
  useInterfaceLanguage();
  useRegionalFormat();
  const mountedRef = useRef(true);

  useEffect(() => {
    mountedRef.current = true;
    return () => {
      mountedRef.current = false;
    };
  }, []);

  // Pod Message Routing states
  const [routeMessageData, setRouteMessageData] = useMountedState(mountedRef, '');
  const [routingMessage, setRoutingMessage] = useMountedState(mountedRef, false);
  const [routingResult, setRoutingResult] = useMountedState(mountedRef, null);
  const [routeToPeersMessage, setRouteToPeersMessage] = useMountedState(mountedRef, '');
  const [routeToPeersIds, setRouteToPeersIds] = useMountedState(mountedRef, '');
  const [routingToPeers, setRoutingToPeers] = useMountedState(mountedRef, false);
  const [routingToPeersResult, setRoutingToPeersResult] = useMountedState(mountedRef, null);
  const [routingStats, setRoutingStats] = useMountedState(mountedRef, null);
  const [loadingRoutingStats, setLoadingRoutingStats] = useMountedState(mountedRef, false);
  const [checkMessageId, setCheckMessageId] = useMountedState(mountedRef, '');
  const [checkPodId, setCheckPodId] = useMountedState(mountedRef, '');
  const [checkingMessageSeen, setCheckingMessageSeen] = useMountedState(mountedRef, false);
  const [messageSeenResult, setMessageSeenResult] = useMountedState(mountedRef, null);


  const handleRouteMessage = async () => {
    if (!routeMessageData.trim()) {
      toast.warning(interfaceText("Please enter message JSON data"));
      return;
    }

    try {
      setRoutingMessage(true);
      setRoutingResult(null);
      const message = JSON.parse(routeMessageData);
      const result = await mediacore.routePodMessage(message);
      setRoutingResult(result);
      setRouteMessageData('');
    } catch (error_) {
      setRoutingResult({ error: toDisplayError(error_) });
    } finally {
      setRoutingMessage(false);
    }
  };

  const handleRouteMessageToPeers = async () => {
    if (!routeToPeersMessage.trim() || !routeToPeersIds.trim()) {
      toast.warning(interfaceText("Please enter message JSON and target peer IDs"));
      return;
    }

    try {
      setRoutingToPeers(true);
      setRoutingToPeersResult(null);
      const message = JSON.parse(routeToPeersMessage);
      const targetPeerIds = routeToPeersIds
        .split(',')
        .map((id) => id.trim())
        .filter(Boolean);
      const result = await mediacore.routePodMessageToPeers(
        message,
        targetPeerIds,
      );
      setRoutingToPeersResult(result);
      setRouteToPeersMessage('');
      setRouteToPeersIds('');
    } catch (error_) {
      setRoutingToPeersResult({ error: toDisplayError(error_) });
    } finally {
      setRoutingToPeers(false);
    }
  };

  const handleLoadRoutingStats = async () => {
    try {
      setLoadingRoutingStats(true);
      setRoutingStats(null);
      const result = await mediacore.getPodMessageRoutingStats();
      setRoutingStats(result);
    } catch (error_) {
      setRoutingStats({ error: toDisplayError(error_) });
    } finally {
      setLoadingRoutingStats(false);
    }
  };

  const handleCheckMessageSeen = async () => {
    if (!checkMessageId.trim() || !checkPodId.trim()) {
      toast.warning(interfaceText("Please enter both message ID and pod ID"));
      return;
    }

    try {
      setCheckingMessageSeen(true);
      setMessageSeenResult(null);
      const result = await mediacore.checkMessageSeen(
        checkMessageId,
        checkPodId,
      );
      setMessageSeenResult(result);
    } catch (error_) {
      setMessageSeenResult({ error: toDisplayError(error_) });
    } finally {
      setCheckingMessageSeen(false);
    }
  };

  const handleRegisterMessageSeen = async () => {
    if (!checkMessageId.trim() || !checkPodId.trim()) {
      toast.warning(interfaceText("Please enter both message ID and pod ID"));
      return;
    }

    try {
      const result = await mediacore.registerMessageSeen(
        checkMessageId,
        checkPodId,
      );
      toast.success(
        `Message registered as seen: ${result.wasNewlyRegistered ? 'New' : 'Already known'}`,
      );
    } catch (error_) {
      toast.error(`Failed to register message: ${toDisplayError(error_)}`);
    }
  };

  const handleCleanupSeenMessages = async () => {
    try {
      const result = await mediacore.cleanupSeenMessages();
      toast.success(
        interfaceText("Cleanup completed: {messagesCleaned} messages cleaned, {messagesRetained} retained", { "messagesCleaned": (result.messagesCleaned), "messagesRetained": (result.messagesRetained) }),
      );
      // Reload stats to reflect changes
      await handleLoadRoutingStats();
    } catch (error_) {
      toast.error(`Failed to cleanup: ${toDisplayError(error_)}`);
    }
  };



  return (
        <Grid.Column style={{ display: visible ? undefined : 'none' }} width={16}>
          <Card id="pod-message-routing" fluid>
            <Card.Content>
              <Card.Header>
                <Icon name="send" />
                <LocalizedText source={"Pod Message Routing"} /></Card.Header>
              <Card.Description>
                <LocalizedText source={"Decentralized message routing via overlay network with fanout and deduplication for reliable pod communication"} /></Card.Description>
              <PodWorkflowNotice title={interfaceText("Sends pod messages")} {...interfaceTextProps("Sends pod messages")}>
                <LocalizedText source={"Routing actions can transmit message bodies and sender identifiers to selected peers or overlay routes. Use deduplication checks before resending."} /></PodWorkflowNotice>
            </Card.Content>

            {/* Manual Message Routing */}
            <Card.Content>
              <Header size="small"><LocalizedText source={"Manual Message Routing"} /></Header>
              <Form>
                <Form.TextArea
                  label={interfaceText("Pod Message JSON")}
                  onChange={(e) => setRouteMessageData(e.target.value)}
                  placeholder='{"messageId": "msg123", "channelId": "pod:artist:mb:daft-punk-hash:general", "senderPeerId": "alice", "body": "Hello pod!", "timestampUnixMs": 1703123456789, "signature": "ed25519:base64-signature"}'
                  rows={4}
                  value={routeMessageData}
                 {...interfaceTextProps("Pod Message JSON")}/>
                <Button
                  disabled={routingMessage || !routeMessageData.trim()}
                  loading={routingMessage}
                  onClick={handleRouteMessage}
                  primary
                >
                  <LocalizedText source={"Route Message"} /></Button>
              </Form>

              {routingResult && (
                <div style={{ marginTop: '1em' }}>
                  {routingResult.error ? (
                    <Message error>
                      <p><LocalizedText source={"Failed to route message:"} />{" "}{routingResult.error}</p>
                    </Message>
                  ) : (
                    <Message success>
                      <Message.Header>
                        <LocalizedText source={"Message Routed Successfully"} /></Message.Header>
                      <p>
                        <strong><LocalizedText source={"Message ID:"} /></strong> {routingResult.messageId}
                        <br />
                        <strong><LocalizedText source={"Pod ID:"} /></strong> {routingResult.podId}
                        <br />
                        <strong><LocalizedText source={"Target Peers:"} /></strong>{' '}
                        {formatRegionalNumber(routingResult.targetPeerCount)}
                        <br />
                        <strong><LocalizedText source={"Successfully Routed:"} /></strong>{' '}
                        {formatRegionalNumber(routingResult.successfullyRoutedCount)}
                        <br />
                        <strong><LocalizedText source={"Failed:"} /></strong>{' '}
                        {formatRegionalNumber(routingResult.failedRoutingCount)}
                        <br />
                        <strong><LocalizedText source={"Duration:"} /></strong>{' '}
                        {formatRegionalFixedNumber(routingResult.routingDuration?.totalMilliseconds, 0)}
                        <LocalizedText source={"ms"} /></p>
                    </Message>
                  )}
                </div>
              )}
            </Card.Content>

            <Card.Content>
              <Grid>
                <Grid.Column width={8}>
                  {/* Route to Specific Peers */}
                  <Header size="small"><LocalizedText source={"Route to Specific Peers"} /></Header>
                  <Form>
                    <Form.TextArea
                      label={interfaceText("Pod Message JSON")}
                      onChange={(e) => setRouteToPeersMessage(e.target.value)}
                      placeholder='{"messageId": "msg123", "channelId": "pod:artist:mb:daft-punk-hash:general", "senderPeerId": "alice", "body": "Direct message", "timestampUnixMs": 1703123456789, "signature": "ed25519:base64-signature"}'
                      rows={3}
                      value={routeToPeersMessage}
                     {...interfaceTextProps("Pod Message JSON")}/>
                    <Form.Input
                      label={interfaceText("Target Peer IDs (comma-separated)")}
                      onChange={(e) => setRouteToPeersIds(e.target.value)}
                      placeholder={interfaceText("bob,charlie,diana")}
                      value={routeToPeersIds}
                     {...interfaceTextProps("Target Peer IDs (comma-separated)")}/>
                    <Button
                      disabled={
                        routingToPeers ||
                        !routeToPeersMessage.trim() ||
                        !routeToPeersIds.trim()
                      }
                      fluid
                      loading={routingToPeers}
                      onClick={handleRouteMessageToPeers}
                    >
                      <LocalizedText source={"Route to Peers"} /></Button>
                  </Form>

                  {routingToPeersResult && (
                    <div style={{ marginTop: '0.5em' }}>
                      {routingToPeersResult.error ? (
                        <Message
                          error
                          size="tiny"
                        >
                          <p>{routingToPeersResult.error}</p>
                        </Message>
                      ) : (
                        <Message
                          info
                          size="tiny"
                        >
                          <p>
                            <LocalizedText source={"Routed to"} />{' '}
                            {formatRegionalNumber(routingToPeersResult.successfullyRoutedCount)}/
                            {formatRegionalNumber(routingToPeersResult.targetPeerCount)} <LocalizedText source={"peers"} /></p>
                        </Message>
                      )}
                    </div>
                  )}
                </Grid.Column>

                <Grid.Column width={8}>
                  {/* Message Deduplication */}
                  <Header size="small"><LocalizedText source={"Message Deduplication"} /></Header>
                  <Form>
                    <Form.Group widths="equal">
                      <Form.Input
                        label={interfaceText("Message ID")}
                        onChange={(e) => setCheckMessageId(e.target.value)}
                        placeholder={interfaceText("msg123")}
                        value={checkMessageId}
                       {...interfaceTextProps("Message ID")}/>
                      <Form.Input
                        label={interfaceText("Pod ID")}
                        onChange={(e) => setCheckPodId(e.target.value)}
                        placeholder="pod:artist:mb:daft-punk-hash"
                        value={checkPodId}
                       {...interfaceTextProps("Pod ID")}/>
                    </Form.Group>
                    <Button.Group fluid>
                      <Button
                        disabled={
                          checkingMessageSeen ||
                          !checkMessageId.trim() ||
                          !checkPodId.trim()
                        }
                        loading={checkingMessageSeen}
                        onClick={handleCheckMessageSeen}
                      >
                        <LocalizedText source={"Check Seen"} /></Button>
                      <Button
                        color="blue"
                        disabled={!checkMessageId.trim() || !checkPodId.trim()}
                        onClick={handleRegisterMessageSeen}
                      >
                        <LocalizedText source={"Mark Seen"} /></Button>
                    </Button.Group>
                  </Form>

                  {messageSeenResult && (
                    <div style={{ marginTop: '0.5em' }}>
                      {messageSeenResult.error ? (
                        <Message
                          error
                          size="tiny"
                        >
                          <p>{messageSeenResult.error}</p>
                        </Message>
                      ) : (
                        <Message size="tiny">
                          <p>
                            <LocalizedText source={"Message"} />{' '}
                            {messageSeenResult.isSeen
                              ? <LocalizedText source={"has been"} />
                              : <LocalizedText source={"has not been"} />}{' '}
                            <LocalizedText source={"seen in pod"} />{" "}{messageSeenResult.podId}
                          </p>
                        </Message>
                      )}
                    </div>
                  )}
                </Grid.Column>
              </Grid>
            </Card.Content>

            {/* Routing Statistics */}
            <Card.Content>
              <Button.Group fluid>
                <Button
                  disabled={loadingRoutingStats}
                  loading={loadingRoutingStats}
                  onClick={handleLoadRoutingStats}
                  primary
                >
                  <LocalizedText source={"Load Routing Stats"} /></Button>
                <Button
                  color="red"
                  onClick={handleCleanupSeenMessages}
                >
                  <LocalizedText source={"Cleanup Seen Messages"} /></Button>
              </Button.Group>

              {routingStats && !routingStats.error && (
                <div style={{ marginTop: '1em' }}>
                  <Message>
                    <Message.Header><LocalizedText source={"Message Routing Statistics"} /></Message.Header>
                    <p>
                      <strong><LocalizedText source={"Total Messages Routed:"} /></strong>{' '}
                      {routingStats.totalMessagesRouted}
                      <br />
                      <strong><LocalizedText source={"Total Routing Attempts:"} /></strong>{' '}
                      {formatRegionalNumber(routingStats.totalRoutingAttempts)}
                      <br />
                      <strong><LocalizedText source={"Successful Routes:"} /></strong>{' '}
                      {formatRegionalNumber(routingStats.successfulRoutingCount)}
                      <br />
                      <strong><LocalizedText source={"Failed Routes:"} /></strong>{' '}
                      {formatRegionalNumber(routingStats.failedRoutingCount)}
                      <br />
                      <strong><LocalizedText source={"Avg Routing Time:"} /></strong>{' '}
                      {formatRegionalFixedNumber(routingStats.averageRoutingTimeMs, 2)}<LocalizedText source={"ms"} /><br />
                      <strong><LocalizedText source={"Deduplication Items:"} /></strong>{' '}
                      {routingStats.activeDeduplicationItems}
                      <br />
                      <strong><LocalizedText source={"Bloom Filter Fill:"} /></strong>{' '}
                      {formatRegionalFixedNumber((routingStats.bloomFilterFillRatio * 100), 1)}%
                      <br />
                      <strong><LocalizedText source={"Est. False Positive:"} /></strong>{' '}
                      {formatRegionalFixedNumber((routingStats.estimatedFalsePositiveRate * 100), 4)}
                      %<br />
                      <strong><LocalizedText source={"Last Operation:"} /></strong>{' '}
                      {routingStats.lastRoutingOperation
                        ? formatRegionalDateTime(routingStats.lastRoutingOperation)
                        : <LocalizedText source={"Never"} />}
                    </p>
                  </Message>

                  <PodMessageMaintenanceActions />
                </div>
              )}

              {routingStats?.error && (
                <Message
                  error
                  style={{ marginTop: '1em' }}
                >
                  <p><LocalizedText source={"Failed to load routing stats:"} />{" "}{routingStats.error}</p>
                </Message>
              )}
            </Card.Content>
          </Card>
        </Grid.Column>

  );
};

export default React.memo(PodMessageRoutingPanel);
