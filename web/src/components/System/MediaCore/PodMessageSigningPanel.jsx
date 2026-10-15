import LocalizedText from "../../Shared/LocalizedText";
import { interfaceText, interfaceTextProps, useInterfaceLanguage } from "../../../lib/interfaceLocale";


import * as mediacore from '../../../lib/mediacore';
import { toDisplayError } from '../../../lib/errors';
import Button from './MediaCoreButton';
import PodWorkflowNotice from './PodWorkflowNotice';
import React, { useEffect, useRef } from 'react';
import { formatRegionalFixedNumber, useRegionalFormat, formatRegionalNumber } from '../../../lib/util';
import { toast } from 'react-toastify';
import { Card, Form, Grid, Header, Icon, Message } from 'semantic-ui-react';

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

const PodMessageSigningPanel = ({
  messageToVerify,
  setMessageToVerify,
  setVerificationResult,
  verificationResult,
  visible = true,
}) => {
  useInterfaceLanguage();
  useRegionalFormat();
  const mountedRef = useRef(true);

  useEffect(() => {
    mountedRef.current = true;
    return () => {
      mountedRef.current = false;
    };
  }, []);

  const [messageToSign, setMessageToSign] = useMountedState(mountedRef, '');
  const [privateKeyForSigning, setPrivateKeyForSigning] = useMountedState(mountedRef, '');
  const [signingMessage, setSigningMessage] = useMountedState(mountedRef, false);
  const [signedMessageResult, setSignedMessageResult] = useMountedState(mountedRef, null);
  const [verifyingSignature, setVerifyingSignature] = useMountedState(mountedRef, false);
  const [generatingKeyPair, setGeneratingKeyPair] = useMountedState(mountedRef, false);
  const [generatedKeyPair, setGeneratedKeyPair] = useMountedState(mountedRef, null);
  const [signingStats, setSigningStats] = useMountedState(mountedRef, null);
  const [loadingSigningStats, setLoadingSigningStats] = useMountedState(mountedRef, false);

  const handleSignMessage = async () => {
    if (!messageToSign.trim() || !privateKeyForSigning.trim()) {
      toast.warning(interfaceText("Please enter message JSON and private key"));
      return;
    }

    try {
      setSigningMessage(true);
      setSignedMessageResult(null);
      const message = JSON.parse(messageToSign);
      const result = await mediacore.signPodMessage(
        message,
        privateKeyForSigning,
      );
      setSignedMessageResult(result);
      setMessageToSign('');
    } catch (error_) {
      setSignedMessageResult({ error: toDisplayError(error_) });
    } finally {
      setSigningMessage(false);
    }
  };

  const handleVerifySignature = async () => {
    if (!messageToVerify.trim()) {
      toast.warning(interfaceText("Please enter message JSON to verify"));
      return;
    }

    try {
      setVerifyingSignature(true);
      setVerificationResult(null);
      const message = JSON.parse(messageToVerify);
      const result = await mediacore.verifyPodMessageSignature(message);
      setVerificationResult(result);
    } catch (error_) {
      setVerificationResult({ error: toDisplayError(error_) });
    } finally {
      setVerifyingSignature(false);
    }
  };

  const handleGenerateKeyPair = async () => {
    try {
      setGeneratingKeyPair(true);
      setGeneratedKeyPair(null);
      const result = await mediacore.generateMessageKeyPair();
      setGeneratedKeyPair(result);
    } catch (error_) {
      setGeneratedKeyPair({ error: toDisplayError(error_) });
    } finally {
      setGeneratingKeyPair(false);
    }
  };

  const handleLoadSigningStats = async () => {
    try {
      setLoadingSigningStats(true);
      setSigningStats(null);
      const result = await mediacore.getMessageSigningStats();
      setSigningStats(result);
    } catch (error_) {
      setSigningStats({ error: toDisplayError(error_) });
    } finally {
      setLoadingSigningStats(false);
    }
  };

  return (
        <Grid.Column style={{ display: visible ? undefined : 'none' }} width={16}>
          <Card id="pod-message-signing" fluid>
            <Card.Content>
              <Card.Header>
                <Icon name="key" />
                <LocalizedText source={"Pod Message Signing"} /></Card.Header>
              <Card.Description>
                <LocalizedText source={"Cryptographic signing and verification of pod messages for authenticity and integrity"} /></Card.Description>
              <PodWorkflowNotice title={interfaceText("Handles key material")} {...interfaceTextProps("Handles key material")}>
                <LocalizedText source={"Signing and key generation workflows may expose private keys or signed payloads in the browser. Treat pasted keys and generated output as sensitive."} /></PodWorkflowNotice>
            </Card.Content>

            {/* Message Signing */}
            <Card.Content>
              <Header size="small"><LocalizedText source={"Sign Pod Message"} /></Header>
              <Form>
                <Form.TextArea
                  label={interfaceText("Pod Message JSON")}
                  onChange={(e) => setMessageToSign(e.target.value)}
                  placeholder='{"messageId": "msg123", "channelId": "pod:artist:mb:daft-punk-hash:general", "senderPeerId": "alice", "body": "Hello pod!", "timestampUnixMs": 1703123456789}'
                  rows={3}
                  value={messageToSign}
                 {...interfaceTextProps("Pod Message JSON")}/>
                <Form.Input
                  label={interfaceText("Private Key")}
                  onChange={(e) => setPrivateKeyForSigning(e.target.value)}
                  placeholder={interfaceText("base64-encoded private key")}
                  type="password"
                  value={privateKeyForSigning}
                 {...interfaceTextProps("Private Key")}/>
                <Button
                  disabled={
                    signingMessage ||
                    !messageToSign.trim() ||
                    !privateKeyForSigning.trim()
                  }
                  loading={signingMessage}
                  onClick={handleSignMessage}
                  primary
                >
                  <LocalizedText source={"Sign Message"} /></Button>
              </Form>

              {signedMessageResult && (
                <div style={{ marginTop: '1em' }}>
                  {signedMessageResult.error ? (
                    <Message error>
                      <p><LocalizedText source={"Failed to sign message:"} />{" "}{signedMessageResult.error}</p>
                    </Message>
                  ) : (
                    <Message success>
                      <Message.Header>
                        <LocalizedText source={"Message Signed Successfully"} /></Message.Header>
                      <p>
                        <strong><LocalizedText source={"Message ID:"} /></strong>{' '}
                        {signedMessageResult.messageId}
                        <br />
                        <strong><LocalizedText source={"Channel:"} /></strong>{' '}
                        {signedMessageResult.channelId}
                        <br />
                        <strong><LocalizedText source={"Signature:"} /></strong>{' '}
                        {signedMessageResult.signature?.slice(0, 50)}...
                      </p>
                    </Message>
                  )}
                </div>
              )}
            </Card.Content>

            <Card.Content>
              <Grid>
                <Grid.Column width={8}>
                  {/* Signature Verification */}
                  <Header size="small"><LocalizedText source={"Verify Message Signature"} /></Header>
                  <Form>
                    <Form.TextArea
                      label={interfaceText("Pod Message JSON (with signature)")}
                      onChange={(e) => setMessageToVerify(e.target.value)}
                      placeholder='{"messageId": "msg123", "channelId": "pod:artist:mb:daft-punk-hash:general", "senderPeerId": "alice", "body": "Hello pod!", "timestampUnixMs": 1703123456789, "signature": "ed25519:base64-signature"}'
                      rows={4}
                      value={messageToVerify}
                     {...interfaceTextProps("Pod Message JSON (with signature)")}/>
                    <Button
                      disabled={verifyingSignature || !messageToVerify.trim()}
                      fluid
                      loading={verifyingSignature}
                      onClick={handleVerifySignature}
                    >
                      <LocalizedText source={"Verify Signature"} /></Button>
                  </Form>

                  {verificationResult && (
                    <div style={{ marginTop: '0.5em' }}>
                      {verificationResult.error ? (
                        <Message
                          error
                          size="tiny"
                        >
                          <p>{verificationResult.error}</p>
                        </Message>
                      ) : (
                        <Message size="tiny">
                          <p>
                            <LocalizedText source={"Message"} />{" "}{verificationResult.messageId}<LocalizedText source={": Signature is"} />{' '}
                            {verificationResult.isValid ? interfaceText('Valid') : interfaceText('Invalid')}
                          </p>
                        </Message>
                      )}
                    </div>
                  )}
                </Grid.Column>

                <Grid.Column width={8}>
                  {/* Key Pair Generation */}
                  <Header size="small"><LocalizedText source={"Generate Key Pair"} /></Header>
                  <Form>
                    <Button
                      disabled={generatingKeyPair}
                      fluid
                      loading={generatingKeyPair}
                      onClick={handleGenerateKeyPair}
                    >
                      <LocalizedText source={"Generate New Key Pair"} /></Button>
                  </Form>

                  {generatedKeyPair && (
                    <div style={{ marginTop: '0.5em' }}>
                      {generatedKeyPair.error ? (
                        <Message
                          error
                          size="tiny"
                        >
                          <p>{generatedKeyPair.error}</p>
                        </Message>
                      ) : (
                        <Message
                          size="tiny"
                          success
                        >
                          <Message.Header><LocalizedText source={"Key Pair Generated"} /></Message.Header>
                          <p>
                            <strong><LocalizedText source={"Public Key:"} /></strong>{' '}
                            {generatedKeyPair.publicKey?.slice(0, 30)}...
                            <br />
                            <strong><LocalizedText source={"Private Key:"} /></strong>{' '}
                            {generatedKeyPair.privateKey?.slice(0, 30)}...
                            <br />
                            <em><LocalizedText source={"⚠️ Keep private key secure!"} /></em>
                          </p>
                        </Message>
                      )}
                    </div>
                  )}

                  {/* Signing Statistics */}
                  <Header
                    size="small"
                    style={{ marginTop: '1em' }}
                  >
                    <LocalizedText source={"Signing Statistics"} /></Header>
                  <Button.Group fluid>
                    <Button
                      disabled={loadingSigningStats}
                      loading={loadingSigningStats}
                      onClick={handleLoadSigningStats}
                    >
                      <LocalizedText source={"Load Stats"} /></Button>
                  </Button.Group>

                  {signingStats && !signingStats.error && (
                    <div style={{ marginTop: '0.5em' }}>
                      <Message size="tiny">
                        <p>
                          <strong><LocalizedText source={"Signatures Created:"} /></strong>{' '}
                          {signingStats.totalSignaturesCreated}
                          <br />
                          <strong><LocalizedText source={"Signatures Verified:"} /></strong>{' '}
                          {signingStats.totalSignaturesVerified}
                          <br />
                          <strong><LocalizedText source={"Successful:"} /></strong>{' '}
                          {formatRegionalNumber(signingStats.successfulVerifications)}
                          <br />
                          <strong><LocalizedText source={"Failed:"} /></strong>{' '}
                          {formatRegionalNumber(signingStats.failedVerifications)}
                          <br />
                          <strong><LocalizedText source={"Avg Sign Time:"} /></strong>{' '}
                          {formatRegionalFixedNumber(signingStats.averageSigningTimeMs, 2)}<LocalizedText source={"ms"} /><br />
                          <strong><LocalizedText source={"Avg Verify Time:"} /></strong>{' '}
                          {formatRegionalFixedNumber(signingStats.averageVerificationTimeMs, 2)}<LocalizedText source={"ms"} /></p>
                      </Message>
                    </div>
                  )}

                  {signingStats?.error && (
                    <Message
                      error
                      size="tiny"
                      style={{ marginTop: '0.5em' }}
                    >
                      <p>{signingStats.error}</p>
                    </Message>
                  )}
                </Grid.Column>
              </Grid>
            </Card.Content>
          </Card>
        </Grid.Column>

    );
};

export default React.memo(PodMessageSigningPanel);
