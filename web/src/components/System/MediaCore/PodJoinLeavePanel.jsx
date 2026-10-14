import LocalizedText from "../../Shared/LocalizedText";
import { interfaceText, interfaceTextProps, useInterfaceLanguage } from "../../../lib/interfaceLocale";


import * as mediacore from '../../../lib/mediacore';
import { toDisplayError } from '../../../lib/errors';
import Button from './MediaCoreButton';
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

const PodJoinLeavePanel = ({ visible = true }) => {
  useInterfaceLanguage();
  const mountedRef = useRef(true);

  useEffect(() => {
    mountedRef.current = true;
    return () => {
      mountedRef.current = false;
    };
  }, []);

  // Pod Join/Leave states
  const [joinRequestData, setJoinRequestData] = useMountedState(mountedRef, '');
  const [requestingJoin, setRequestingJoin] = useMountedState(mountedRef, false);
  const [joinRequestResult, setJoinRequestResult] = useMountedState(mountedRef, null);
  const [acceptanceData, setAcceptanceData] = useMountedState(mountedRef, '');
  const [acceptingJoin, setAcceptingJoin] = useMountedState(mountedRef, false);
  const [acceptanceResult, setAcceptanceResult] = useMountedState(mountedRef, null);
  const [leaveRequestData, setLeaveRequestData] = useMountedState(mountedRef, '');
  const [requestingLeave, setRequestingLeave] = useMountedState(mountedRef, false);
  const [leaveRequestResult, setLeaveRequestResult] = useMountedState(mountedRef, null);
  const [acceptingLeave, setAcceptingLeave] = useMountedState(mountedRef, false);
  const [leaveAcceptanceResult, setLeaveAcceptanceResult] = useMountedState(mountedRef, null);
  const [pendingPodId, setPendingPodId] = useMountedState(mountedRef, '');
  const [loadingPendingRequests, setLoadingPendingRequests] = useMountedState(mountedRef, false);
  const [pendingJoinRequests, setPendingJoinRequests] = useMountedState(mountedRef, null);
  const [pendingLeaveRequests, setPendingLeaveRequests] = useMountedState(mountedRef, null);


  const handleRequestJoin = async () => {
    if (!joinRequestData.trim()) {
      toast.warning(interfaceText("Please enter join request JSON data"));
      return;
    }

    try {
      setRequestingJoin(true);
      setJoinRequestResult(null);
      const joinRequest = JSON.parse(joinRequestData);
      const result = await mediacore.requestPodJoin(joinRequest);
      setJoinRequestResult(result);
      setJoinRequestData('');
    } catch (error_) {
      setJoinRequestResult({ error: toDisplayError(error_) });
    } finally {
      setRequestingJoin(false);
    }
  };

  const handleAcceptJoin = async () => {
    if (!acceptanceData.trim()) {
      toast.warning(interfaceText("Please enter acceptance JSON data"));
      return;
    }

    try {
      setAcceptingJoin(true);
      setAcceptanceResult(null);
      const acceptance = JSON.parse(acceptanceData);
      const result = await mediacore.acceptPodJoin(acceptance);
      setAcceptanceResult(result);
      setAcceptanceData('');
    } catch (error_) {
      setAcceptanceResult({ error: toDisplayError(error_) });
    } finally {
      setAcceptingJoin(false);
    }
  };

  const handleRequestLeave = async () => {
    if (!leaveRequestData.trim()) {
      toast.warning(interfaceText("Please enter leave request JSON data"));
      return;
    }

    try {
      setRequestingLeave(true);
      setLeaveRequestResult(null);
      const leaveRequest = JSON.parse(leaveRequestData);
      const result = await mediacore.requestPodLeave(leaveRequest);
      setLeaveRequestResult(result);
      setLeaveRequestData('');
    } catch (error_) {
      setLeaveRequestResult({ error: toDisplayError(error_) });
    } finally {
      setRequestingLeave(false);
    }
  };

  const handleAcceptLeave = async () => {
    if (!acceptanceData.trim()) {
      toast.warning(interfaceText("Please enter leave acceptance JSON data"));
      return;
    }

    try {
      setAcceptingLeave(true);
      setLeaveAcceptanceResult(null);
      const acceptance = JSON.parse(acceptanceData);
      const result = await mediacore.acceptPodLeave(acceptance);
      setLeaveAcceptanceResult(result);
      setAcceptanceData('');
    } catch (error_) {
      setLeaveAcceptanceResult({ error: toDisplayError(error_) });
    } finally {
      setAcceptingLeave(false);
    }
  };

  const handleLoadPendingRequests = async () => {
    if (!pendingPodId.trim()) {
      toast.warning(interfaceText("Please enter a pod ID"));
      return;
    }

    try {
      setLoadingPendingRequests(true);
      setPendingJoinRequests(null);
      setPendingLeaveRequests(null);

      const [joinRequests, leaveRequests] = await Promise.all([
        mediacore.getPendingJoinRequests(pendingPodId),
        mediacore.getPendingLeaveRequests(pendingPodId),
      ]);

      setPendingJoinRequests(joinRequests);
      setPendingLeaveRequests(leaveRequests);
    } catch (error_) {
      setPendingJoinRequests({ error: toDisplayError(error_) });
      setPendingLeaveRequests({ error: toDisplayError(error_) });
    } finally {
      setLoadingPendingRequests(false);
    }
  };


  return (
        <Grid.Column style={{ display: visible ? undefined : 'none' }} width={16}>
          <Card id="pod-join-leave" fluid>
            <Card.Content>
              <Card.Header>
                <Icon name="user plus" />
                <LocalizedText source={"Pod Join/Leave Operations"} /></Card.Header>
              <Card.Description>
                <LocalizedText source={"Manage signed pod membership operations with Ed25519 verification and role-based approvals"} /></Card.Description>
              <PodWorkflowNotice title={interfaceText("Publishes join and leave events")} {...interfaceTextProps("Publishes join and leave events")}>
                <LocalizedText source={"Join and leave requests can expose peer IDs, requested roles, public keys, signatures, and operator-provided messages."} /></PodWorkflowNotice>
              <Message info>
                <LocalizedText source={"In Enforce mode, signatures use the"} /><code> ed25519:&lt;base64 signature&gt;</code> <LocalizedText source={"format over the canonical join payload and require a fresh one-use nonce."} /></Message>
            </Card.Content>

            {/* Join Request */}
            <Card.Content>
              <Header size="small"><LocalizedText source={"Request to Join Pod"} /></Header>
              <Form>
                <Form.TextArea
                  label={interfaceText("Join Request JSON (signed by requester)")}
                  onChange={(e) => setJoinRequestData(e.target.value)}
                  placeholder='{"podId": "pod:artist:mb:daft-punk-hash", "peerId": "alice", "requestedRole": "member", "publicKey": "base64-ed25519-public-key", "timestampUnixMs": 1703123456789, "signature": "ed25519:base64-signature", "nonce": "unique-request-nonce", "message": "Please let me join!"}'
                  rows={4}
                  value={joinRequestData}
                 {...interfaceTextProps("Join Request JSON (signed by requester)")}/>
                <Button
                  disabled={requestingJoin || !joinRequestData.trim()}
                  loading={requestingJoin}
                  onClick={handleRequestJoin}
                  primary
                >
                  <LocalizedText source={"Submit Join Request"} /></Button>
              </Form>

              {joinRequestResult && (
                <div style={{ marginTop: '1em' }}>
                  {joinRequestResult.error ? (
                    <Message error>
                      <p>
                        <LocalizedText source={"Failed to submit join request:"} />{" "}{joinRequestResult.error}
                      </p>
                    </Message>
                  ) : (
                    <Message success>
                      <Message.Header><LocalizedText source={"Join Request Submitted"} /></Message.Header>
                      <p>
                        <strong><LocalizedText source={"Pod ID:"} /></strong> {joinRequestResult.podId}
                        <br />
                        <strong><LocalizedText source={"Peer ID:"} /></strong> {joinRequestResult.peerId}
                        <br />
                        <strong><LocalizedText source={"Status:"} /></strong>{' '}
                        {joinRequestResult.success
                          ? <LocalizedText source={"Pending approval"} />
                          : <LocalizedText source={"Failed"} />}
                      </p>
                    </Message>
                  )}
                </div>
              )}
            </Card.Content>

            <Card.Content>
              <Grid>
                <Grid.Column width={8}>
                  {/* Accept Join */}
                  <Header size="small"><LocalizedText source={"Accept Join Request"} /></Header>
                  <Form>
                    <Form.TextArea
                      label={interfaceText("Acceptance JSON (signed by owner/mod)")}
                      onChange={(e) => setAcceptanceData(e.target.value)}
                      placeholder='{"podId": "pod:artist:mb:daft-punk-hash", "peerId": "alice", "acceptedRole": "member", "acceptorPeerId": "bob", "acceptorPublicKey": "base64-ed25519-public-key", "timestampUnixMs": 1703123456789, "signature": "ed25519:base64-signature", "message": "Welcome!"}'
                      rows={4}
                      value={acceptanceData}
                     {...interfaceTextProps("Acceptance JSON (signed by owner/mod)")}/>
                    <Button
                      disabled={acceptingJoin || !acceptanceData.trim()}
                      loading={acceptingJoin}
                      onClick={handleAcceptJoin}
                      positive
                    >
                      <LocalizedText source={"Accept Join"} /></Button>
                  </Form>

                  {acceptanceResult && (
                    <div style={{ marginTop: '0.5em' }}>
                      {acceptanceResult.error ? (
                        <Message
                          error
                          size="tiny"
                        >
                          <p>{acceptanceResult.error}</p>
                        </Message>
                      ) : (
                        <Message
                          size="tiny"
                          success
                        >
                          <p><LocalizedText source={"Join accepted successfully"} /></p>
                        </Message>
                      )}
                    </div>
                  )}
                </Grid.Column>

                <Grid.Column width={8}>
                  {/* Leave Request */}
                  <Header size="small"><LocalizedText source={"Request to Leave Pod"} /></Header>
                  <Form>
                    <Form.TextArea
                      label={interfaceText("Leave Request JSON (signed by member)")}
                      onChange={(e) => setLeaveRequestData(e.target.value)}
                      placeholder='{"podId": "pod:artist:mb:daft-punk-hash", "peerId": "alice", "publicKey": "base64-ed25519-public-key", "timestampUnixMs": 1703123456789, "signature": "ed25519:base64-signature", "message": "Goodbye!"}'
                      rows={4}
                      value={leaveRequestData}
                     {...interfaceTextProps("Leave Request JSON (signed by member)")}/>
                    <Button
                      disabled={requestingLeave || !leaveRequestData.trim()}
                      loading={requestingLeave}
                      onClick={handleRequestLeave}
                    >
                      <LocalizedText source={"Submit Leave Request"} /></Button>
                  </Form>

                  {leaveRequestResult && (
                    <div style={{ marginTop: '0.5em' }}>
                      {leaveRequestResult.error ? (
                        <Message
                          error
                          size="tiny"
                        >
                          <p>{leaveRequestResult.error}</p>
                        </Message>
                      ) : (
                        <Message
                          size="tiny"
                          success
                        >
                          <p><LocalizedText source={"Leave request submitted"} /></p>
                        </Message>
                      )}
                    </div>
                  )}
                </Grid.Column>
              </Grid>
            </Card.Content>

            <Card.Content>
              <Grid>
                <Grid.Column width={8}>
                  {/* Accept Leave */}
                  <Header size="small">
                    <LocalizedText source={"Accept Leave Request (Owner/Mod Only)"} /></Header>
                  <Form>
                    <Form.TextArea
                      label={interfaceText("Leave Acceptance JSON (signed by owner/mod)")}
                      onChange={(e) => setAcceptanceData(e.target.value)}
                      placeholder='{"podId": "pod:artist:mb:daft-punk-hash", "peerId": "alice", "acceptorPeerId": "bob", "acceptorPublicKey": "base64-ed25519-public-key", "timestampUnixMs": 1703123456789, "signature": "ed25519:base64-signature", "message": "Farewell!"}'
                      rows={4}
                      value={acceptanceData}
                     {...interfaceTextProps("Leave Acceptance JSON (signed by owner/mod)")}/>
                    <Button
                      disabled={acceptingLeave || !acceptanceData.trim()}
                      loading={acceptingLeave}
                      negative
                      onClick={handleAcceptLeave}
                    >
                      <LocalizedText source={"Accept Leave"} /></Button>
                  </Form>

                  {leaveAcceptanceResult && (
                    <div style={{ marginTop: '0.5em' }}>
                      {leaveAcceptanceResult.error ? (
                        <Message
                          error
                          size="tiny"
                        >
                          <p>{leaveAcceptanceResult.error}</p>
                        </Message>
                      ) : (
                        <Message
                          size="tiny"
                          success
                        >
                          <p><LocalizedText source={"Leave accepted successfully"} /></p>
                        </Message>
                      )}
                    </div>
                  )}
                </Grid.Column>

                <Grid.Column width={8}>
                  {/* Pending Requests */}
                  <Header size="small"><LocalizedText source={"View Pending Requests"} /></Header>
                  <Form>
                    <Form.Input
                      label={interfaceText("Pod ID")}
                      onChange={(e) => setPendingPodId(e.target.value)}
                      placeholder="pod:artist:mb:daft-punk-hash"
                      value={pendingPodId}
                     {...interfaceTextProps("Pod ID")}/>
                    <Button
                      disabled={loadingPendingRequests || !pendingPodId.trim()}
                      loading={loadingPendingRequests}
                      onClick={handleLoadPendingRequests}
                    >
                      <LocalizedText source={"Load Pending Requests"} /></Button>
                  </Form>

                  {pendingJoinRequests && !pendingJoinRequests.error && (
                    <div style={{ marginTop: '0.5em' }}>
                      <Message size="tiny">
                        <strong><LocalizedText source={"Join Requests:"} /></strong>{' '}
                        {pendingJoinRequests.pendingJoinRequests?.length || 0}
                      </Message>
                    </div>
                  )}

                  {pendingLeaveRequests && !pendingLeaveRequests.error && (
                    <div style={{ marginTop: '0.5em' }}>
                      <Message size="tiny">
                        <strong><LocalizedText source={"Leave Requests:"} /></strong>{' '}
                        {pendingLeaveRequests.pendingLeaveRequests?.length || 0}
                      </Message>
                    </div>
                  )}

                  {(pendingJoinRequests?.error ||
                    pendingLeaveRequests?.error) && (
                    <Message
                      error
                      size="tiny"
                      style={{ marginTop: '0.5em' }}
                    >
                      <p><LocalizedText source={"Failed to load pending requests"} /></p>
                    </Message>
                  )}
                </Grid.Column>
              </Grid>
            </Card.Content>
          </Card>
        </Grid.Column>

  );
};

export default React.memo(PodJoinLeavePanel);
