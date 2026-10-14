import LocalizedText from "../../Shared/LocalizedText";
import { interfaceText, interfaceTextProps, useInterfaceLanguage } from "../../../lib/interfaceLocale";


import { formatRegionalDateTime, useRegionalFormat } from '../../../lib/util';
import * as mediacore from '../../../lib/mediacore';
import { toDisplayError } from '../../../lib/errors';
import Button from './MediaCoreButton';
import PodWorkflowNotice from './PodWorkflowNotice';
import React, { useRef } from 'react';
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

const PodMembershipVerificationPanel = React.memo(({
  messageToVerify,
  setMessageToVerify,
  setVerifyingMembership,
  verifyingMembership,
  visible,
}) => {
  useInterfaceLanguage();
  useRegionalFormat();
  const mountedRef = useRef(true);
  React.useEffect(() => {
    mountedRef.current = true;
    return () => {
      mountedRef.current = false;
    };
  }, []);

  // Pod Membership Verification states
  const [verifyPodId, setVerifyPodId] = useMountedState(mountedRef, '');
  const [verifyPeerId, setVerifyPeerId] = useMountedState(mountedRef, '');
  const [membershipVerificationResult, setMembershipVerificationResult] =
    useMountedState(mountedRef, null);
  const [membershipMessageToVerify, setMembershipMessageToVerify] =
    useMountedState(mountedRef, '');
  const [verifyingMessage, setVerifyingMessage] = useMountedState(mountedRef, false);
  const [messageVerificationResult, setMessageVerificationResult] =
    useMountedState(mountedRef, null);
  const [roleCheckPodId, setRoleCheckPodId] = useMountedState(mountedRef, '');
  const [roleCheckPeerId, setRoleCheckPeerId] = useMountedState(mountedRef, '');
  const [requiredRole, setRequiredRole] = useMountedState(mountedRef, 'member');
  const [checkingRole, setCheckingRole] = useMountedState(mountedRef, false);
  const [roleCheckResult, setRoleCheckResult] = useMountedState(mountedRef, null);
  const [verificationStats, setVerificationStats] = useMountedState(mountedRef, null);
  const [loadingVerificationStats, setLoadingVerificationStats] =
    useMountedState(mountedRef, false);


  // Pod Membership Verification handlers
  const handleVerifyPodMembership = async () => {
    if (!verifyPodId.trim() || !verifyPeerId.trim()) {
      toast.warning(interfaceText("Please enter both Pod ID and Peer ID"));
      return;
    }

    try {
      setVerifyingMembership(true);
      setMembershipVerificationResult(null);
      const result = await mediacore.verifyPodMembership(
        verifyPodId,
        verifyPeerId,
      );
      setMembershipVerificationResult(result);
    } catch (error_) {
      setMembershipVerificationResult({ error: toDisplayError(error_) });
    } finally {
      setVerifyingMembership(false);
    }
  };

  const handleVerifyMessage = async () => {
    if (!membershipMessageToVerify.trim()) {
      toast.warning(interfaceText("Please enter a message JSON"));
      return;
    }

    try {
      setVerifyingMessage(true);
      setMessageVerificationResult(null);
      const message = JSON.parse(membershipMessageToVerify);
      const result = await mediacore.verifyPodMessage(message);
      setMessageVerificationResult(result);
    } catch (error_) {
      setMessageVerificationResult({ error: toDisplayError(error_) });
    } finally {
      setVerifyingMessage(false);
    }
  };

  const handleCheckRole = async () => {
    if (!roleCheckPodId.trim() || !roleCheckPeerId.trim()) {
      toast.warning(interfaceText("Please enter both Pod ID and Peer ID"));
      return;
    }

    try {
      setCheckingRole(true);
      setRoleCheckResult(null);
      const hasRole = await mediacore.checkPodRole(
        roleCheckPodId,
        roleCheckPeerId,
        requiredRole,
      );
      setRoleCheckResult({ hasRole });
    } catch (error_) {
      setRoleCheckResult({ error: toDisplayError(error_) });
    } finally {
      setCheckingRole(false);
    }
  };

  const handleLoadVerificationStats = async () => {
    try {
      setLoadingVerificationStats(true);
      setVerificationStats(null);
      const result = await mediacore.getVerificationStats();
      setVerificationStats(result);
    } catch (error_) {
      setVerificationStats({ error: toDisplayError(error_) });
    } finally {
      setLoadingVerificationStats(false);
    }
  };

  return (
    <>
        {/* Pod Membership Verification */}
        <Grid.Column style={{ display: visible ? undefined : 'none' }} width={16}>
          <Card id="pod-membership-verification" fluid>
            <Card.Content>
              <Card.Header>
                <Icon name="shield" />
                <LocalizedText source={"Pod Membership Verification"} /></Card.Header>
              <Card.Description>
                <LocalizedText source={"Verify membership status, message authenticity, and role permissions for pod security"} /></Card.Description>
              <PodWorkflowNotice
                color="blue"
                icon="check circle"
                title={interfaceText("Read-only verification")}
               {...interfaceTextProps("Read-only verification")}>
                <LocalizedText source={"Verification checks should not mutate pod state, but pasted messages and membership records can still contain sensitive peer or signature data."} /></PodWorkflowNotice>
            </Card.Content>

            {/* Membership Verification */}
            <Card.Content>
              <Header size="small"><LocalizedText source={"Verify Membership Status"} /></Header>
              <Form>
                <Form.Group widths="equal">
                  <Form.Input
                    label={interfaceText("Pod ID")}
                    onChange={(e) => setVerifyPodId(e.target.value)}
                    placeholder="pod:artist:mb:daft-punk-hash"
                    value={verifyPodId}
                   {...interfaceTextProps("Pod ID")}/>
                  <Form.Input
                    label={interfaceText("Peer ID")}
                    onChange={(e) => setVerifyPeerId(e.target.value)}
                    placeholder={interfaceText("alice")}
                    value={verifyPeerId}
                   {...interfaceTextProps("Peer ID")}/>
                </Form.Group>
                <Button
                  disabled={
                    verifyingMembership ||
                    !verifyPodId.trim() ||
                    !verifyPeerId.trim()
                  }
                  fluid
                  loading={verifyingMembership}
                  onClick={handleVerifyPodMembership}
                >
                  <LocalizedText source={"Verify Membership"} /></Button>
              </Form>

              {membershipVerificationResult && (
                <div style={{ marginTop: '1em' }}>
                  {membershipVerificationResult.error ? (
                    <Message error>
                      <p>
                        <LocalizedText source={"Failed to verify membership:"} />{' '}
                        {membershipVerificationResult.error}
                      </p>
                    </Message>
                  ) : (
                    <Message success>
                      <Message.Header>
                        <LocalizedText source={"Membership Verification Result"} /></Message.Header>
                      <p>
                        <strong><LocalizedText source={"Valid Member:"} /></strong>{' '}
                        {membershipVerificationResult.isValidMember
                          ? <LocalizedText source={"Yes"} />
                          : <LocalizedText source={"No"} />}
                        <br />
                        <strong><LocalizedText source={"Role:"} /></strong>{' '}
                        {membershipVerificationResult.role || 'None'}
                        <br />
                        <strong><LocalizedText source={"Banned:"} /></strong>{' '}
                        {membershipVerificationResult.isBanned ? <LocalizedText source={"Yes"} /> : <LocalizedText source={"No"} />}
                      </p>
                    </Message>
                  )}
                </div>
              )}
            </Card.Content>

            <Card.Content>
              <Grid>
                <Grid.Column width={8}>
                  {/* Message Verification */}
                  <Header size="small"><LocalizedText source={"Verify Message Authenticity"} /></Header>
                  <Form>
                    <Form.TextArea
                      label={interfaceText("Pod Message JSON")}
                      onChange={(e) => setMessageToVerify(e.target.value)}
                      placeholder='{"messageId": "msg123", "channelId": "pod:artist:mb:daft-punk-hash:general", "senderPeerId": "alice", "body": "Hello everyone!", "timestampUnixMs": 1703123456789, "signature": "ed25519:base64-signature"}'
                      rows={4}
                      value={messageToVerify}
                     {...interfaceTextProps("Pod Message JSON")}/>
                    <Button
                      disabled={verifyingMessage || !messageToVerify.trim()}
                      fluid
                      loading={verifyingMessage}
                      onClick={handleVerifyMessage}
                    >
                      <LocalizedText source={"Verify Message"} /></Button>
                  </Form>

                  {messageVerificationResult && (
                    <div style={{ marginTop: '1em' }}>
                      {messageVerificationResult.error ? (
                        <Message error>
                          <p>
                            <LocalizedText source={"Failed to verify message:"} />{' '}
                            {messageVerificationResult.error}
                          </p>
                        </Message>
                      ) : (
                        <Message info>
                          <Message.Header>
                            <LocalizedText source={"Message Verification Result"} /></Message.Header>
                          <p>
                            <strong><LocalizedText source={"Valid:"} /></strong>{' '}
                            {messageVerificationResult.isValid ? <LocalizedText source={"Yes"} /> : <LocalizedText source={"No"} />}
                            <br />
                            <strong><LocalizedText source={"From Valid Member:"} /></strong>{' '}
                            {messageVerificationResult.isFromValidMember
                              ? <LocalizedText source={"Yes"} />
                              : <LocalizedText source={"No"} />}
                            <br />
                            <strong><LocalizedText source={"Not Banned:"} /></strong>{' '}
                            {messageVerificationResult.isNotBanned
                              ? <LocalizedText source={"Yes"} />
                              : <LocalizedText source={"No"} />}
                            <br />
                            <strong><LocalizedText source={"Valid Signature:"} /></strong>{' '}
                            {messageVerificationResult.hasValidSignature
                              ? <LocalizedText source={"Yes"} />
                              : <LocalizedText source={"No"} />}
                          </p>
                        </Message>
                      )}
                    </div>
                  )}
                </Grid.Column>

                <Grid.Column width={8}>
                  {/* Role Checking */}
                  <Header size="small"><LocalizedText source={"Check Role Permissions"} /></Header>
                  <Form>
                    <Form.Group widths="equal">
                      <Form.Input
                        label={interfaceText("Pod ID")}
                        onChange={(e) => setRoleCheckPodId(e.target.value)}
                        placeholder="pod:artist:mb:daft-punk-hash"
                        value={roleCheckPodId}
                       {...interfaceTextProps("Pod ID")}/>
                      <Form.Input
                        label={interfaceText("Peer ID")}
                        onChange={(e) => setRoleCheckPeerId(e.target.value)}
                        placeholder={interfaceText("alice")}
                        value={roleCheckPeerId}
                       {...interfaceTextProps("Peer ID")}/>
                    </Form.Group>
                    <Form.Select
                      label={interfaceText("Required Role")}
                      onChange={(e, { value }) => setRequiredRole(value)}
                      options={[
                        { key: 'member', text: interfaceText("Member"), value: 'member' },
                        { key: 'mod', text: interfaceText("Moderator"), value: 'mod' },
                        { key: 'owner', text: interfaceText("Owner"), value: 'owner' },
                      ]}
                      value={requiredRole}
                     {...interfaceTextProps("Required Role")}/>
                    <Button
                      disabled={
                        checkingRole ||
                        !roleCheckPodId.trim() ||
                        !roleCheckPeerId.trim()
                      }
                      fluid
                      loading={checkingRole}
                      onClick={handleCheckRole}
                    >
                      <LocalizedText source={"Check Role"} /></Button>
                  </Form>

                  {roleCheckResult && (
                    <div style={{ marginTop: '1em' }}>
                      {roleCheckResult.error ? (
                        <Message error>
                          <p><LocalizedText source={"Failed to check role:"} />{" "}{roleCheckResult.error}</p>
                        </Message>
                      ) : (
                        <Message>
                          <Message.Header><LocalizedText source={"Role Check Result"} /></Message.Header>
                          <p>
                            <strong><LocalizedText source={"Has Required Role ("} />{requiredRole}):</strong>{' '}
                            {roleCheckResult.hasRole ? <LocalizedText source={"Yes"} /> : <LocalizedText source={"No"} />}
                          </p>
                        </Message>
                      )}
                    </div>
                  )}
                </Grid.Column>
              </Grid>
            </Card.Content>

            {/* Verification Statistics */}
            <Card.Content>
              <Button.Group fluid>
                <Button
                  disabled={loadingVerificationStats}
                  loading={loadingVerificationStats}
                  onClick={handleLoadVerificationStats}
                  primary
                >
                  <LocalizedText source={"Load Verification Stats"} /></Button>
              </Button.Group>

              {verificationStats && !verificationStats.error && (
                <div style={{ marginTop: '1em' }}>
                  <Message>
                    <Message.Header><LocalizedText source={"Verification Statistics"} /></Message.Header>
                    <p>
                      <strong><LocalizedText source={"Total Verifications:"} /></strong>{' '}
                      {verificationStats.totalVerifications}
                      <br />
                      <strong><LocalizedText source={"Successful:"} /></strong>{' '}
                      {verificationStats.successfulVerifications}
                      <br />
                      <strong><LocalizedText source={"Failed Membership:"} /></strong>{' '}
                      {verificationStats.failedMembershipChecks}
                      <br />
                      <strong><LocalizedText source={"Failed Signatures:"} /></strong>{' '}
                      {verificationStats.failedSignatureChecks}
                      <br />
                      <strong><LocalizedText source={"Banned Rejections:"} /></strong>{' '}
                      {verificationStats.bannedMemberRejections}
                      <br />
                      <strong><LocalizedText source={"Avg Time:"} /></strong>{' '}
                      {verificationStats.averageVerificationTimeMs.toFixed(2)}<LocalizedText source={"ms"} /><br />
                      <strong><LocalizedText source={"Last Verification:"} /></strong>{' '}
                      {verificationStats.lastVerification
                        ? formatRegionalDateTime(verificationStats.lastVerification)
                        : <LocalizedText source={"Never"} />}
                    </p>
                  </Message>
                </div>
              )}

              {verificationStats?.error && (
                <Message
                  error
                  style={{ marginTop: '1em' }}
                >
                  <p>
                    <LocalizedText source={"Failed to load verification stats:"} />{" "}{verificationStats.error}
                  </p>
                </Message>
              )}
            </Card.Content>
          </Card>
        </Grid.Column>
    </>
  );
});

export default PodMembershipVerificationPanel;
