import LocalizedText from "../../Shared/LocalizedText";
import { interfaceText, interfaceTextProps, useInterfaceLanguage } from "../../../lib/interfaceLocale";
import { formatRegionalFixedNumber, useRegionalFormat, formatRegionalNumber } from '../../../lib/util';


import * as mediacore from '../../../lib/mediacore';
import { toDisplayError } from '../../../lib/errors';
import Button from './MediaCoreButton';
import React, { useEffect, useRef } from 'react';
import { toast } from 'react-toastify';
import {
  Card,
  Form,
  Grid,
  Header,
  Icon,
  Input,
  Label,
  List,
  Message,
  TextArea,
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

const ContentDescriptorPublishingPanel = () => {
  useInterfaceLanguage();
  useRegionalFormat();
  const mountedRef = useRef(true);

  useEffect(() => {
    mountedRef.current = true;
    return () => {
      mountedRef.current = false;
    };
  }, []);

  const [publishContentId, setPublishContentId] = useMountedState(mountedRef, '');
  const [publishCodec, setPublishCodec] = useMountedState(mountedRef, 'mp3');
  const [publishSize, setPublishSize] = useMountedState(mountedRef, 1_024);
  const [batchContentIds, setBatchContentIds] = useMountedState(mountedRef, '');
  const [updateTargetId, setUpdateTargetId] = useMountedState(mountedRef, '');
  const [updateCodec, setUpdateCodec] = useMountedState(mountedRef, '');
  const [updateSize, setUpdateSize] = useMountedState(mountedRef, '');
  const [updateConfidence, setUpdateConfidence] = useMountedState(mountedRef, '');
  const [publishResult, setPublishResult] = useMountedState(mountedRef, null);
  const [batchPublishResult, setBatchPublishResult] = useMountedState(mountedRef, null);
  const [updateResult, setUpdateResult] = useMountedState(mountedRef, null);
  const [republishResult, setRepublishResult] = useMountedState(mountedRef, null);
  const [publishingStats, setPublishingStats] = useMountedState(mountedRef, null);
  const [publishingDescriptor, setPublishingDescriptor] = useMountedState(mountedRef, false);
  const [publishingBatch, setPublishingBatch] = useMountedState(mountedRef, false);
  const [updatingDescriptor, setUpdatingDescriptor] = useMountedState(mountedRef, false);
  const [republishing, setRepublishing] = useMountedState(mountedRef, false);
  const [loadingStats, setLoadingStats] = useMountedState(mountedRef, false);

  const handlePublishDescriptor = async () => {
    if (!publishContentId.trim()) return;

    try {
      setPublishingDescriptor(true);
      setPublishResult(null);

      const descriptor = {
        codec: publishCodec.trim(),
        confidence: 0.8,
        contentId: publishContentId.trim(),
        sizeBytes: Number.parseInt(publishSize),
      };

      const result = await mediacore.publishContentDescriptor(descriptor);
      setPublishResult(result);
    } catch (error_) {
      setPublishResult({ error: toDisplayError(error_) });
    } finally {
      setPublishingDescriptor(false);
    }
  };

  const handlePublishBatch = async () => {
    const contentIds = batchContentIds
      .split('\n')
      .map((id) => id.trim())
      .filter(Boolean);
    if (!contentIds.length) return;

    try {
      setPublishingBatch(true);
      setBatchPublishResult(null);

      // Create mock descriptors for each ContentID
      const descriptors = contentIds.map((contentId) => ({
        // 1MB mock
        codec: 'mock',

        confidence: 0.8,
        contentId,
        sizeBytes: 1_024 * 1_024,
      }));

      const result =
        await mediacore.publishContentDescriptorsBatch(descriptors);
      setBatchPublishResult(result);
    } catch (error_) {
      setBatchPublishResult({ error: toDisplayError(error_) });
    } finally {
      setPublishingBatch(false);
    }
  };

  const handleUpdateDescriptor = async () => {
    if (!updateTargetId.trim()) return;

    try {
      setUpdatingDescriptor(true);
      setUpdateResult(null);

      const updates = {};
      if (updateCodec.trim()) updates.newCodec = updateCodec.trim();
      if (updateSize.trim()) updates.newSizeBytes = Number.parseInt(updateSize);
      if (updateConfidence.trim())
        updates.newConfidence = Number.parseFloat(updateConfidence);

      if (Object.keys(updates).length === 0) {
        throw new Error('At least one update field is required');
      }

      const result = await mediacore.updateContentDescriptor(
        updateTargetId.trim(),
        updates,
      );
      setUpdateResult(result);
    } catch (error_) {
      setUpdateResult({ error: toDisplayError(error_) });
    } finally {
      setUpdatingDescriptor(false);
    }
  };

  const handleRepublishExpiring = async () => {
    try {
      setRepublishing(true);
      setRepublishResult(null);
      const result = await mediacore.republishExpiringDescriptors();
      setRepublishResult(result);
    } catch (error_) {
      setRepublishResult({ error: toDisplayError(error_) });
    } finally {
      setRepublishing(false);
    }
  };

  const handleLoadPublishingStats = async () => {
    try {
      setLoadingStats(true);
      setPublishingStats(null);
      const result = await mediacore.getPublishingStats();
      setPublishingStats(result);
    } catch (error_) {
      setPublishingStats({ error: toDisplayError(error_) });
    } finally {
      setLoadingStats(false);
    }
  };

  return (
    <>
        {/* Content Descriptor Publishing */}
        <Grid.Column width={8}>
          <Card fluid>
            <Card.Content>
              <Card.Header>
                <Icon name="cloud upload" />
                <LocalizedText source={"Publish Content Descriptor"} /></Card.Header>
              <Card.Description>
                <LocalizedText source={"Publish a content descriptor to the DHT with versioning support"} /></Card.Description>
            </Card.Content>
            <Card.Content>
              <Form>
                <Form.Field>
                  <label><LocalizedText source={"ContentID"} /></label>
                  <Input
                    onChange={(e) => setPublishContentId(e.target.value)}
                    placeholder="content:audio:track:mb-12345"
                    value={publishContentId}
                  />
                </Form.Field>
                <Form.Group widths="equal">
                  <Form.Field>
                    <label><LocalizedText source={"Codec"} /></label>
                    <Input
                      onChange={(e) => setPublishCodec(e.target.value)}
                      placeholder={interfaceText("mp3, flac, etc.")}
                      value={publishCodec}
                     {...interfaceTextProps("mp3, flac, etc.")}/>
                  </Form.Field>
                  <Form.Field>
                    <label><LocalizedText source={"Size (bytes)"} /></label>
                    <Input
                      onChange={(e) => setPublishSize(e.target.value)}
                      type="number"
                      value={publishSize}
                    />
                  </Form.Field>
                </Form.Group>
                <Button
                  disabled={!publishContentId.trim() || publishingDescriptor}
                  loading={publishingDescriptor}
                  onClick={handlePublishDescriptor}
                  primary
                >
                  <LocalizedText source={"Publish Descriptor"} /></Button>
              </Form>

              {publishResult && (
                <div style={{ marginTop: '1em' }}>
                  {publishResult.error ? (
                    <Message error>
                      <p>{publishResult.error}</p>
                    </Message>
                  ) : (
                    <Message success>
                      <Message.Header><LocalizedText source={"Published Successfully"} /></Message.Header>
                      <p>
                        <strong><LocalizedText source={"ContentID:"} /></strong> {publishResult.contentId}
                        <br />
                        <strong><LocalizedText source={"Version:"} /></strong> {publishResult.version}
                        <br />
                        <strong>TTL:</strong> {publishResult.ttl?.totalMinutes}{' '}
                        <LocalizedText source={"minutes"} /><br />
                        <strong><LocalizedText source={"Was Updated:"} /></strong>{' '}
                        {publishResult.wasUpdated ? <LocalizedText source={"Yes"} /> : <LocalizedText source={"No"} />}
                      </p>
                    </Message>
                  )}
                </div>
              )}
            </Card.Content>
          </Card>
        </Grid.Column>

        {/* Batch Publishing */}
        <Grid.Column width={8}>
          <Card fluid>
            <Card.Content>
              <Card.Header>
                <Icon name="list" />
                <LocalizedText source={"Batch Publish Descriptors"} /></Card.Header>
              <Card.Description>
                <LocalizedText source={"Publish multiple content descriptors simultaneously"} /></Card.Description>
            </Card.Content>
            <Card.Content>
              <Form>
                <Form.Field>
                  <label><LocalizedText source={"ContentIDs (one per line)"} /></label>
                  <TextArea
                    onChange={(e) => setBatchContentIds(e.target.value)}
                    placeholder={interfaceText("content:audio:track:mb-12345&#10;content:video:movie:imdb-tt0111161&#10;...")}
                    rows={6}
                    value={batchContentIds}
                   {...interfaceTextProps("content:audio:track:mb-12345&#10;content:video:movie:imdb-tt0111161&#10;...")}/>
                </Form.Field>
                <Button
                  disabled={!batchContentIds.trim() || publishingBatch}
                  loading={publishingBatch}
                  onClick={handlePublishBatch}
                  primary
                >
                  <LocalizedText source={"Publish Batch"} /></Button>
              </Form>

              {batchPublishResult && (
                <div style={{ marginTop: '1em' }}>
                  {batchPublishResult.error ? (
                    <Message error>
                      <p>{batchPublishResult.error}</p>
                    </Message>
                  ) : (
                    <Message info>
                      <Message.Header><LocalizedText source={"Batch Publish Results"} /></Message.Header>
                      <p>
                        <strong><LocalizedText source={"Total Requested:"} /></strong>{' '}
                        {formatRegionalNumber(batchPublishResult.totalRequested)}
                        <br />
                        <strong><LocalizedText source={"Successfully Published:"} /></strong>{' '}
                        {formatRegionalNumber(batchPublishResult.successfullyPublished)}
                        <br />
                        <strong><LocalizedText source={"Failed:"} /></strong>{' '}
                        {batchPublishResult.failedToPublish}
                        <br />
                        <strong><LocalizedText source={"Skipped:"} /></strong> {formatRegionalNumber(batchPublishResult.skipped)}
                        <br />
                        <strong><LocalizedText source={"Duration:"} /></strong>{' '}
                        {batchPublishResult.totalDuration?.totalSeconds === undefined
                          ? '—'
                          : formatRegionalFixedNumber(batchPublishResult.totalDuration.totalSeconds, 2)}s</p>
                    </Message>
                  )}
                </div>
              )}
            </Card.Content>
          </Card>
        </Grid.Column>

        {/* Descriptor Updates */}
        <Grid.Column width={8}>
          <Card fluid>
            <Card.Content>
              <Card.Header>
                <Icon name="edit" />
                <LocalizedText source={"Update Descriptor"} /></Card.Header>
              <Card.Description>
                <LocalizedText source={"Update metadata for an existing published descriptor"} /></Card.Description>
            </Card.Content>
            <Card.Content>
              <Form>
                <Form.Field>
                  <label><LocalizedText source={"Target ContentID"} /></label>
                  <Input
                    onChange={(e) => setUpdateTargetId(e.target.value)}
                    placeholder={interfaceText("ContentID to update")}
                    value={updateTargetId}
                   {...interfaceTextProps("ContentID to update")}/>
                </Form.Field>
                <Form.Group widths="equal">
                  <Form.Field>
                    <label><LocalizedText source={"New Codec"} /></label>
                    <Input
                      onChange={(e) => setUpdateCodec(e.target.value)}
                      placeholder={interfaceText("Leave empty to keep current")}
                      value={updateCodec}
                     {...interfaceTextProps("Leave empty to keep current")}/>
                  </Form.Field>
                  <Form.Field>
                    <label><LocalizedText source={"New Size (bytes)"} /></label>
                    <Input
                      onChange={(e) => setUpdateSize(e.target.value)}
                      placeholder={interfaceText("Leave empty to keep current")}
                      value={updateSize}
                     {...interfaceTextProps("Leave empty to keep current")}/>
                  </Form.Field>
                </Form.Group>
                <Form.Field>
                  <label><LocalizedText source={"New Confidence (0.0-1.0)"} /></label>
                  <Input
                    onChange={(e) => setUpdateConfidence(e.target.value)}
                    placeholder={interfaceText("Leave empty to keep current")}
                    value={updateConfidence}
                   {...interfaceTextProps("Leave empty to keep current")}/>
                </Form.Field>
                <Button
                  disabled={!updateTargetId.trim() || updatingDescriptor}
                  loading={updatingDescriptor}
                  onClick={handleUpdateDescriptor}
                  primary
                >
                  <LocalizedText source={"Update Descriptor"} /></Button>
              </Form>

              {updateResult && (
                <div style={{ marginTop: '1em' }}>
                  {updateResult.error ? (
                    <Message error>
                      <p>{updateResult.error}</p>
                    </Message>
                  ) : (
                    <Message success>
                      <Message.Header><LocalizedText source={"Update Successful"} /></Message.Header>
                      <p>
                        <strong><LocalizedText source={"ContentID:"} /></strong> {updateResult.contentId}
                        <br />
                        <strong><LocalizedText source={"Version:"} /></strong> {updateResult.previousVersion}{' '}
                        → {updateResult.newVersion}
                        <br />
                        <strong><LocalizedText source={"Updates Applied:"} /></strong>{' '}
                        {updateResult.appliedUpdates?.join(', ') || 'none'}
                      </p>
                    </Message>
                  )}
                </div>
              )}
            </Card.Content>
          </Card>
        </Grid.Column>

        {/* Publishing Management */}
        <Grid.Column width={8}>
          <Card fluid>
            <Card.Content>
              <Card.Header>
                <Icon name="cogs" />
                <LocalizedText source={"Publishing Management"} /></Card.Header>
              <Card.Description>
                <LocalizedText source={"Manage published descriptors and monitor publishing status"} /></Card.Description>
            </Card.Content>
            <Card.Content>
              <Button.Group fluid>
                <Button
                  disabled={republishing}
                  loading={republishing}
                  onClick={handleRepublishExpiring}
                >
                  <LocalizedText source={"Republish Expiring"} /></Button>
                <Button
                  disabled={loadingStats}
                  loading={loadingStats}
                  onClick={handleLoadPublishingStats}
                >
                  <LocalizedText source={"Load Stats"} /></Button>
              </Button.Group>

              {/* Republish Results */}
              {republishResult && (
                <div style={{ marginTop: '1em' }}>
                  {republishResult.error ? (
                    <Message error>
                      <p>{republishResult.error}</p>
                    </Message>
                  ) : (
                    <Message info>
                      <Message.Header><LocalizedText source={"Republish Results"} /></Message.Header>
                      <p>
                        <strong><LocalizedText source={"Checked:"} /></strong> {republishResult.totalChecked}
                        <br />
                        <strong><LocalizedText source={"Republished:"} /></strong>{' '}
                        {formatRegionalNumber(republishResult.republished)}
                        <br />
                        <strong><LocalizedText source={"Failed:"} /></strong> {formatRegionalNumber(republishResult.failed)}
                        <br />
                        <strong><LocalizedText source={"Still Valid:"} /></strong>{' '}
                        {republishResult.stillValid}
                        <br />
                        <strong><LocalizedText source={"Duration:"} /></strong>{' '}
                        {republishResult.duration?.totalSeconds === undefined
                          ? '—'
                          : formatRegionalFixedNumber(republishResult.duration.totalSeconds, 2)}s</p>
                    </Message>
                  )}
                </div>
              )}

              {/* Publishing Stats */}
              {publishingStats && (
                <div style={{ marginTop: '1em' }}>
                  {publishingStats.error ? (
                    <Message error>
                      <p>{publishingStats.error}</p>
                    </Message>
                  ) : (
                    <Message>
                      <Message.Header><LocalizedText source={"Publishing Statistics"} /></Message.Header>
                      <p>
                        <strong><LocalizedText source={"Total Published:"} /></strong>{' '}
                        {publishingStats.totalPublishedDescriptors}
                        <br />
                        <strong><LocalizedText source={"Active Publications:"} /></strong>{' '}
                        {formatRegionalNumber(publishingStats.activePublications)}
                        <br />
                        <strong><LocalizedText source={"Expiring Soon:"} /></strong>{' '}
                        {publishingStats.expiringSoon}
                        <br />
                        <strong><LocalizedText source={"Average TTL:"} /></strong>{' '}
                        {formatRegionalFixedNumber(publishingStats.averageTtlHours, 1)} <LocalizedText source={"hours"} /><br />
                        <strong><LocalizedText source={"Total Storage:"} /></strong>{' '}
                        {formatRegionalFixedNumber((
                          publishingStats.totalStorageBytes /
                          1_024 /
                          1_024
                        ), 1)}{' '}
                        MB
                      </p>
                      {publishingStats.publicationsByDomain &&
                        Object.keys(publishingStats.publicationsByDomain)
                          .length > 0 && (
                          <div style={{ marginTop: '0.5em' }}>
                            <strong><LocalizedText source={"By Domain:"} /></strong>
                            {Object.entries(
                              publishingStats.publicationsByDomain,
                            ).map(([domain, count]) => (
                              <Label
                                key={domain}
                                size="tiny"
                                style={{ margin: '0.1em' }}
                              >
                                {domain}: {count}
                              </Label>
                            ))}
                          </div>
                        )}
                    </Message>
                  )}
                </div>
              )}
            </Card.Content>
          </Card>
        </Grid.Column>

    </>
  );
};

export default React.memo(ContentDescriptorPublishingPanel);
