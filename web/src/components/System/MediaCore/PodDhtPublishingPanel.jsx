import LocalizedText from "../../Shared/LocalizedText";
import { interfaceText, interfaceTextProps, useInterfaceLanguage } from "../../../lib/interfaceLocale";


import { formatRegionalDateTime, useRegionalFormat } from '../../../lib/util';
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
  Label,
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

const PodDhtPublishingPanel = ({ visible = true }) => {
  useInterfaceLanguage();
  useRegionalFormat();
  const mountedRef = useRef(true);

  useEffect(() => {
    mountedRef.current = true;
    return () => {
      mountedRef.current = false;
    };
  }, []);

  const [podToPublish, setPodToPublish] = useMountedState(mountedRef, '');
  const [publishingPod, setPublishingPod] = useMountedState(mountedRef, false);
  const [podPublishingResult, setPodPublishingResult] = useMountedState(mountedRef, null);
  const [podMetadataToRetrieve, setPodMetadataToRetrieve] = useMountedState(mountedRef, '');
  const [retrievingPodMetadata, setRetrievingPodMetadata] = useMountedState(mountedRef, false);
  const [podMetadataResult, setPodMetadataResult] = useMountedState(mountedRef, null);
  const [podToUnpublish, setPodToUnpublish] = useMountedState(mountedRef, '');
  const [unpublishingPod, setUnpublishingPod] = useMountedState(mountedRef, false);
  const [podUnpublishResult, setPodUnpublishResult] = useMountedState(mountedRef, null);
  const [podPublishingStats, setPodPublishingStats] = useMountedState(mountedRef, null);
  const [loadingPodStats, setLoadingPodStats] = useMountedState(mountedRef, false);

  const handlePublishPod = async () => {
    if (!podToPublish.trim()) {
      toast.warning(interfaceText("Please enter pod JSON data"));
      return;
    }

    try {
      setPublishingPod(true);
      setPodPublishingResult(null);
      const pod = JSON.parse(podToPublish);
      const result = await mediacore.publishPod(pod);
      setPodPublishingResult(result);
      setPodToPublish('');
    } catch (error_) {
      setPodPublishingResult({ error: toDisplayError(error_) });
    } finally {
      setPublishingPod(false);
    }
  };

  const handleRetrievePodMetadata = async () => {
    if (!podMetadataToRetrieve.trim()) {
      toast.warning(interfaceText("Please enter a pod ID"));
      return;
    }

    try {
      setRetrievingPodMetadata(true);
      setPodMetadataResult(null);
      const result = await mediacore.getPublishedPodMetadata(
        podMetadataToRetrieve,
      );
      setPodMetadataResult(result);
    } catch (error_) {
      setPodMetadataResult({ error: toDisplayError(error_) });
    } finally {
      setRetrievingPodMetadata(false);
    }
  };

  const handleUnpublishPod = async () => {
    if (!podToUnpublish.trim()) {
      toast.warning(interfaceText("Please enter a pod ID"));
      return;
    }

    if (
      !confirm(`Are you sure you want to unpublish pod "${podToUnpublish}"?`)
    ) {
      return;
    }

    try {
      setUnpublishingPod(true);
      setPodUnpublishResult(null);
      const result = await mediacore.unpublishPod(podToUnpublish);
      setPodUnpublishResult(result);
      setPodToUnpublish('');
    } catch (error_) {
      setPodUnpublishResult({ error: toDisplayError(error_) });
    } finally {
      setUnpublishingPod(false);
    }
  };

  const handleLoadPodPublishingStats = async () => {
    try {
      setLoadingPodStats(true);
      setPodPublishingStats(null);
      const result = await mediacore.getPodPublishingStats();
      setPodPublishingStats(result);
    } catch (error_) {
      setPodPublishingStats({ error: toDisplayError(error_) });
    } finally {
      setLoadingPodStats(false);
    }
  };

  return (
        <Grid.Column style={{ display: visible ? undefined : 'none' }} width={16}>
          <Card id="podcore-dht-publishing" fluid>
            <Card.Content>
              <Card.Header>
                <Icon name="podcast" />
                <LocalizedText source={"PodCore DHT Publishing"} /></Card.Header>
              <Card.Description>
                <LocalizedText source={"Publish and manage pod metadata on the decentralized DHT for discovery"} /></Card.Description>
              <PodWorkflowNotice title={interfaceText("Publishes pod metadata")} {...interfaceTextProps("Publishes pod metadata")}>
                <LocalizedText source={"Publishing or updating a listed pod can make pod identifiers, tags, focus content IDs, and descriptive metadata discoverable by other mesh participants."} /></PodWorkflowNotice>
            </Card.Content>

            {/* Publish Pod */}
            <Card.Content>
              <Header size="small"><LocalizedText source={"Publish Pod to DHT"} /></Header>
              <Form>
                <Form.TextArea
                  label={interfaceText("Pod JSON")}
                  onChange={(e) => setPodToPublish(e.target.value)}
                  placeholder={"{\"id\": {\"value\": \"pod:artist:mb:daft-punk-hash\"}, \"displayName\": \"Daft Punk Fans\", \"visibility\": \"Listed\", \"focusType\": \"ContentId\", \"focusContentId\": {\"domain\": \"audio\", \"type\": \"artist\", \"id\": \"daft-punk-hash\"}, \"tags\": [\"electronic\", \"french-house\"], \"createdAt\": \"2024-01-01T00:00:00Z\", \"createdBy\": \"alice\", \"metadata\": {\"description\": \"A community for Daft Punk fans\", \"memberCount\": 150}}"}
                  rows={6}
                  value={podToPublish}
                 {...interfaceTextProps("Pod JSON")} dir="ltr"/>
                <Button
                  disabled={publishingPod || !podToPublish.trim()}
                  loading={publishingPod}
                  onClick={handlePublishPod}
                  primary
                >
                  <LocalizedText source={"Publish Pod"} /></Button>
              </Form>

              {podPublishingResult && (
                <div style={{ marginTop: '1em' }}>
                  {podPublishingResult.error ? (
                    <Message error>
                      <p><LocalizedText source={"Failed to publish pod:"} />{" "}{podPublishingResult.error}</p>
                    </Message>
                  ) : (
                    <Message success>
                      <Message.Header>
                        <LocalizedText source={"Pod Published Successfully"} /></Message.Header>
                      <p>
                        <strong><LocalizedText source={"Pod ID:"} /></strong>{' '}
                        {podPublishingResult.podId?.value ||
                          podPublishingResult.podId}
                        <br />
                        <strong><LocalizedText source={"DHT Key:"} /></strong> {podPublishingResult.dhtKey}
                        <br />
                        <strong><LocalizedText source={"Published:"} /></strong>{' '}
                        {formatRegionalDateTime(podPublishingResult.publishedAt)}
                        <br />
                        <strong><LocalizedText source={"Expires:"} /></strong>{' '}
                        {formatRegionalDateTime(podPublishingResult.expiresAt)}
                      </p>
                    </Message>
                  )}
                </div>
              )}
            </Card.Content>

            <Card.Content>
              <Grid>
                <Grid.Column width={8}>
                  {/* Retrieve Pod Metadata */}
                  <Header size="small"><LocalizedText source={"Retrieve Pod Metadata"} /></Header>
                  <Form>
                    <Form.Input
                      label={interfaceText("Pod ID")}
                      onChange={(e) => setPodMetadataToRetrieve(e.target.value)}
                      placeholder="pod:artist:mb:daft-punk-hash"
                      value={podMetadataToRetrieve}
                     {...interfaceTextProps("Pod ID")}/>
                    <Button
                      disabled={
                        retrievingPodMetadata || !podMetadataToRetrieve.trim()
                      }
                      fluid
                      loading={retrievingPodMetadata}
                      onClick={handleRetrievePodMetadata}
                    >
                      <LocalizedText source={"Retrieve Metadata"} /></Button>
                  </Form>

                  {podMetadataResult && (
                    <div style={{ marginTop: '1em' }}>
                      {podMetadataResult.error ? (
                        <Message error>
                          <p>
                            <LocalizedText source={"Failed to retrieve metadata:"} />{' '}
                            {podMetadataResult.error}
                          </p>
                        </Message>
                      ) : podMetadataResult.found ? (
                        <Message success>
                          <Message.Header>
                            <LocalizedText source={"Pod Metadata Retrieved"} /></Message.Header>
                          <p>
                            <strong><LocalizedText source={"Pod ID:"} /></strong>{' '}
                            {podMetadataResult.podId?.value ||
                              podMetadataResult.podId}
                            <br />
                            <strong><LocalizedText source={"Signature Valid:"} /></strong>{' '}
                            {podMetadataResult.isValidSignature ? <LocalizedText source={"Yes"} /> : <LocalizedText source={"No"} />}
                            <br />
                            <strong><LocalizedText source={"Retrieved:"} /></strong>{' '}
                            {formatRegionalDateTime(podMetadataResult.retrievedAt)}
                            <br />
                            <strong><LocalizedText source={"Expires:"} /></strong>{' '}
                            {formatRegionalDateTime(podMetadataResult.expiresAt)}
                            <br />
                            <strong><LocalizedText source={"Display Name:"} /></strong>{' '}
                            {podMetadataResult.publishedPod?.displayName}
                            <br />
                            <strong><LocalizedText source={"Members:"} /></strong>{' '}
                            {podMetadataResult.publishedPod?.metadata
                              ?.memberCount || <LocalizedText source={"Unknown"} />}
                          </p>
                        </Message>
                      ) : (
                        <Message warning>
                          <p><LocalizedText source={"Pod not found in DHT"} /></p>
                        </Message>
                      )}
                    </div>
                  )}
                </Grid.Column>

                <Grid.Column width={8}>
                  {/* Unpublish Pod */}
                  <Header size="small"><LocalizedText source={"Unpublish Pod from DHT"} /></Header>
                  <Form>
                    <Form.Input
                      label={interfaceText("Pod ID")}
                      onChange={(e) => setPodToUnpublish(e.target.value)}
                      placeholder="pod:artist:mb:daft-punk-hash"
                      value={podToUnpublish}
                     {...interfaceTextProps("Pod ID")}/>
                    <Button
                      color="red"
                      disabled={unpublishingPod || !podToUnpublish.trim()}
                      fluid
                      loading={unpublishingPod}
                      onClick={handleUnpublishPod}
                    >
                      <LocalizedText source={"Unpublish Pod"} /></Button>
                  </Form>

                  {podUnpublishResult && (
                    <div style={{ marginTop: '1em' }}>
                      {podUnpublishResult.error ? (
                        <Message error>
                          <p>
                            <LocalizedText source={"Failed to unpublish pod:"} />{" "}{podUnpublishResult.error}
                          </p>
                        </Message>
                      ) : (
                        <Message success>
                          <p><LocalizedText source={"Pod unpublished successfully from DHT"} /></p>
                        </Message>
                      )}
                    </div>
                  )}
                </Grid.Column>
              </Grid>
            </Card.Content>

            {/* Pod Publishing Statistics */}
            <Card.Content>
              <Button.Group fluid>
                <Button
                  disabled={loadingPodStats}
                  loading={loadingPodStats}
                  onClick={handleLoadPodPublishingStats}
                  primary
                >
                  <LocalizedText source={"Load Pod Publishing Stats"} /></Button>
              </Button.Group>

              {podPublishingStats && !podPublishingStats.error && (
                <div style={{ marginTop: '1em' }}>
                  <Message>
                    <Message.Header><LocalizedText source={"Pod Publishing Statistics"} /></Message.Header>
                    <p>
                      <strong><LocalizedText source={"Total Published:"} /></strong>{' '}
                      {podPublishingStats.totalPublished}
                      <br />
                      <strong><LocalizedText source={"Active Publications:"} /></strong>{' '}
                      {podPublishingStats.activePublications}
                      <br />
                      <strong><LocalizedText source={"Expired Publications:"} /></strong>{' '}
                      {podPublishingStats.expiredPublications}
                      <br />
                      <strong><LocalizedText source={"Failed Publications:"} /></strong>{' '}
                      {podPublishingStats.failedPublications}
                      <br />
                      <strong><LocalizedText source={"Avg Publish Time:"} /></strong>{' '}
                      {podPublishingStats.averagePublishTime
                        ? `${podPublishingStats.averagePublishTime.totalMilliseconds.toFixed(0)}ms`
                        : interfaceText('N/A')}
                      <br />
                      <strong><LocalizedText source={"Last Operation:"} /></strong>{' '}
                      {podPublishingStats.lastPublishOperation
                        ? formatRegionalDateTime(podPublishingStats.lastPublishOperation)
                        : <LocalizedText source={"Never"} />}
                    </p>
                    {podPublishingStats.publicationsByVisibility &&
                      Object.keys(podPublishingStats.publicationsByVisibility)
                        .length > 0 && (
                        <div style={{ marginTop: '0.5em' }}>
                          <strong><LocalizedText source={"Publications by Visibility:"} /></strong>
                          {Object.entries(
                            podPublishingStats.publicationsByVisibility,
                          ).map(([visibility, count]) => (
                            <Label
                              key={visibility}
                              size="tiny"
                              style={{ margin: '0.1em' }}
                            >
                              {visibility}: {count}
                            </Label>
                          ))}
                        </div>
                      )}
                  </Message>
                </div>
              )}

              {podPublishingStats?.error && (
                <Message
                  error
                  style={{ marginTop: '1em' }}
                >
                  <p>
                    <LocalizedText source={"Failed to load pod publishing stats:"} />{' '}
                    {podPublishingStats.error}
                  </p>
                </Message>
              )}
            </Card.Content>
          </Card>
        </Grid.Column>

  );
};

export default React.memo(PodDhtPublishingPanel);
