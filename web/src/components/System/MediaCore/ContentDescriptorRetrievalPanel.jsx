import LocalizedText from "../../Shared/LocalizedText";
import { interfaceText, interfaceTextProps, useInterfaceLanguage } from "../../../lib/interfaceLocale";


import { formatRegionalDateTime, formatRegionalFixedNumber, useRegionalFormat, formatRegionalNumber } from '../../../lib/util';
import * as mediacore from '../../../lib/mediacore';
import { toDisplayError } from '../../../lib/errors';
import Button from './MediaCoreButton';
import React, { useEffect, useRef } from 'react';
import { toast } from 'react-toastify';
import {
  Card,
  Checkbox,
  Dropdown,
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

const ContentDescriptorRetrievalPanel = ({ setVerificationResult }) => {
  useInterfaceLanguage();
  useRegionalFormat();
  const mountedRef = useRef(true);

  useEffect(() => {
    mountedRef.current = true;
    return () => {
      mountedRef.current = false;
    };
  }, []);

  const [retrievalResult, setRetrievalResult] = useMountedState(mountedRef, null);
  const [batchRetrievalResult, setBatchRetrievalResult] = useMountedState(mountedRef, null);
  const [queryResult, setQueryResult] = useMountedState(mountedRef, null);
  const [descriptorVerificationResult] = useMountedState(mountedRef, null);
  const [retrievalStats, setRetrievalStats] = useMountedState(mountedRef, null);
  const [retrieveContentId, setRetrieveContentId] = useMountedState(mountedRef, '');
  const [batchRetrieveContentIds, setBatchRetrieveContentIds] = useMountedState(mountedRef, '');
  const [queryDomain, setQueryDomain] = useMountedState(mountedRef, 'audio');
  const [queryType, setQueryType] = useMountedState(mountedRef, '');
  const [queryMaxResults, setQueryMaxResults] = useMountedState(mountedRef, 50);
  const [verifyDescriptor, setVerifyDescriptor] = useMountedState(mountedRef, '');
  const [bypassCache, setBypassCache] = useMountedState(mountedRef, false);
  const [retrievingDescriptor, setRetrievingDescriptor] = useMountedState(mountedRef, false);
  const [retrievingBatch, setRetrievingBatch] = useMountedState(mountedRef, false);
  const [queryingDescriptors, setQueryingDescriptors] = useMountedState(mountedRef, false);
  const [verifyingDescriptor, setVerifyingDescriptor] = useMountedState(mountedRef, false);
  const [loadingRetrievalStats, setLoadingRetrievalStats] = useMountedState(mountedRef, false);

  const handleRetrieveDescriptor = async () => {
    if (!retrieveContentId.trim()) return;

    try {
      setRetrievingDescriptor(true);
      setRetrievalResult(null);
      const result = await mediacore.retrieveContentDescriptor(
        retrieveContentId.trim(),
        bypassCache,
      );
      setRetrievalResult(result);
    } catch (error_) {
      setRetrievalResult({ error: toDisplayError(error_) });
    } finally {
      setRetrievingDescriptor(false);
    }
  };

  const handleRetrieveBatch = async () => {
    const contentIds = batchRetrieveContentIds
      .split('\n')
      .map((id) => id.trim())
      .filter(Boolean);
    if (!contentIds.length) return;

    try {
      setRetrievingBatch(true);
      setBatchRetrievalResult(null);
      const result =
        await mediacore.retrieveContentDescriptorsBatch(contentIds);
      setBatchRetrievalResult(result);
    } catch (error_) {
      setBatchRetrievalResult({ error: toDisplayError(error_) });
    } finally {
      setRetrievingBatch(false);
    }
  };

  const handleQueryDescriptors = async () => {
    if (!queryDomain.trim()) return;

    try {
      setQueryingDescriptors(true);
      setQueryResult(null);
      const result = await mediacore.queryDescriptorsByDomain(
        queryDomain.trim(),
        queryType.trim() || null,
        Number.parseInt(queryMaxResults),
      );
      setQueryResult(result);
    } catch (error_) {
      setQueryResult({ error: toDisplayError(error_) });
    } finally {
      setQueryingDescriptors(false);
    }
  };

  const handleVerifyDescriptor = async () => {
    if (!verifyDescriptor.trim()) return;

    try {
      setVerifyingDescriptor(true);
      setVerificationResult(null);

      let descriptor;
      try {
        descriptor = JSON.parse(verifyDescriptor.trim());
      } catch {
        throw new Error('Invalid JSON format for descriptor');
      }

      const result = await mediacore.verifyContentDescriptor(descriptor);
      setVerificationResult(result);
    } catch (error_) {
      setVerificationResult({ error: toDisplayError(error_) });
    } finally {
      setVerifyingDescriptor(false);
    }
  };

  const handleLoadRetrievalStats = async () => {
    try {
      setLoadingRetrievalStats(true);
      setRetrievalStats(null);
      const result = await mediacore.getRetrievalStats();
      setRetrievalStats(result);
    } catch (error_) {
      setRetrievalStats({ error: toDisplayError(error_) });
    } finally {
      setLoadingRetrievalStats(false);
    }
  };

  const handleClearRetrievalCache = async () => {
    try {
      const result = await mediacore.clearRetrievalCache();
      // Reload stats to reflect changes
      await handleLoadRetrievalStats();
      toast.success(
        interfaceText("Cache cleared: {entriesCleared} entries, {bytesFreed} bytes freed", { "entriesCleared": (result.entriesCleared), "bytesFreed": (result.bytesFreed) }),
      );
    } catch (error_) {
      toast.error(interfaceText('Failed to clear cache: {error}', { error: toDisplayError(error_) }));
    }
  };

  return (
    <>
        {/* Descriptor Retrieval */}
        <Grid.Column width={8}>
          <Card fluid>
            <Card.Content>
              <Card.Header>
                <Icon name="search" />
                <LocalizedText source={"Retrieve Content Descriptor"} /></Card.Header>
              <Card.Description>
                <LocalizedText source={"Retrieve content descriptors from the DHT by ContentID"} /></Card.Description>
            </Card.Content>
            <Card.Content>
              <Form>
                <Form.Field>
                  <label><LocalizedText source={"ContentID"} /></label>
                  <Input
                    onChange={(e) => setRetrieveContentId(e.target.value)}
                    placeholder="content:audio:track:mb-12345"
                    value={retrieveContentId}
                  />
                </Form.Field>
                <Form.Field>
                  <Checkbox
                    checked={bypassCache}
                    label={interfaceText("Bypass cache (force fresh retrieval)")}
                    onChange={(e, { checked }) => setBypassCache(checked)}
                   {...interfaceTextProps("Bypass cache (force fresh retrieval)")}/>
                </Form.Field>
                <Button
                  disabled={!retrieveContentId.trim() || retrievingDescriptor}
                  loading={retrievingDescriptor}
                  onClick={handleRetrieveDescriptor}
                  primary
                >
                  <LocalizedText source={"Retrieve Descriptor"} /></Button>
              </Form>

              {retrievalResult && (
                <div style={{ marginTop: '1em' }}>
                  {retrievalResult.error ? (
                    <Message error>
                      <p>{retrievalResult.error}</p>
                    </Message>
                  ) : !retrievalResult.found ? (
                    <Message warning>
                      <p>
                        <LocalizedText source={"Content descriptor not found for:"} />{' '}
                        {retrievalResult.contentId || retrieveContentId}
                      </p>
                    </Message>
                  ) : (
                    <Message success>
                      <Message.Header><LocalizedText source={"Descriptor Retrieved"} /></Message.Header>
                      <p>
                        <strong><LocalizedText source={"ContentID:"} /></strong>{' '}
                        {retrievalResult.descriptor?.contentId}
                        <br />
                        <strong><LocalizedText source={"From Cache:"} /></strong>{' '}
                        {retrievalResult.fromCache ? <LocalizedText source={"Yes"} /> : <LocalizedText source={"No"} />}
                        <br />
                        <strong><LocalizedText source={"Retrieved:"} /></strong>{' '}
                        {formatRegionalDateTime(retrievalResult.retrievedAt)}
                        <br />
                        <strong><LocalizedText source={"Duration:"} /></strong>{' '}
                        {formatRegionalFixedNumber(retrievalResult.retrievalDuration?.totalMilliseconds, 0)}
                        <LocalizedText source={"ms"} /><br />
                        <strong><LocalizedText source={"Verified:"} /></strong>{' '}
                        {retrievalResult.verification?.isValid ? <LocalizedText source={"Yes"} /> : <LocalizedText source={"No"} />}
                        {retrievalResult.verification?.warnings?.length > 0 && (
                          <span> <LocalizedText source={"(with warnings)"} /></span>
                        )}
                      </p>
                      <details>
                        <summary><LocalizedText source={"View Descriptor JSON"} /></summary>
                        <pre
                          style={{
                            fontSize: '0.8em',
                            maxHeight: '200px',
                            overflow: 'auto',
                          }}
                        >
                          {JSON.stringify(retrievalResult.descriptor, null, 2)}
                        </pre>
                      </details>
                    </Message>
                  )}
                </div>
              )}
            </Card.Content>
          </Card>
        </Grid.Column>

        {/* Batch Retrieval */}
        <Grid.Column width={8}>
          <Card fluid>
            <Card.Content>
              <Card.Header>
                <Icon name="list alternate" />
                <LocalizedText source={"Batch Descriptor Retrieval"} /></Card.Header>
              <Card.Description>
                <LocalizedText source={"Retrieve multiple content descriptors simultaneously"} /></Card.Description>
            </Card.Content>
            <Card.Content>
              <Form>
                <Form.Field>
                  <label><LocalizedText source={"ContentIDs (one per line)"} /></label>
                  <TextArea
                    onChange={(e) => setBatchRetrieveContentIds(e.target.value)}
                    placeholder={interfaceText("content:audio:track:mb-12345&#10;content:video:movie:imdb-tt0111161&#10;...")}
                    rows={6}
                    value={batchRetrieveContentIds}
                   {...interfaceTextProps("content:audio:track:mb-12345&#10;content:video:movie:imdb-tt0111161&#10;...")}/>
                </Form.Field>
                <Button
                  disabled={!batchRetrieveContentIds.trim() || retrievingBatch}
                  loading={retrievingBatch}
                  onClick={handleRetrieveBatch}
                  primary
                >
                  <LocalizedText source={"Retrieve Batch"} /></Button>
              </Form>

              {batchRetrievalResult && (
                <div style={{ marginTop: '1em' }}>
                  {batchRetrievalResult.error ? (
                    <Message error>
                      <p>{batchRetrievalResult.error}</p>
                    </Message>
                  ) : (
                    <Message info>
                      <Message.Header><LocalizedText source={"Batch Retrieval Results"} /></Message.Header>
                      <p>
                        <strong><LocalizedText source={"Requested:"} /></strong>{' '}
                        {formatRegionalNumber(batchRetrievalResult.requested)}
                        <br />
                        <strong><LocalizedText source={"Found:"} /></strong> {formatRegionalNumber(batchRetrievalResult.found)}
                        <br />
                        <strong><LocalizedText source={"Failed:"} /></strong> {formatRegionalNumber(batchRetrievalResult.failed)}
                        <br />
                        <strong><LocalizedText source={"Duration:"} /></strong>{' '}
                        {batchRetrievalResult.totalDuration?.totalSeconds === undefined
                          ? '—'
                          : formatRegionalFixedNumber(batchRetrievalResult.totalDuration.totalSeconds, 2)}s</p>
                    </Message>
                  )}
                </div>
              )}
            </Card.Content>
          </Card>
        </Grid.Column>

        {/* Domain Query */}
        <Grid.Column width={8}>
          <Card fluid>
            <Card.Content>
              <Card.Header>
                <Icon name="filter" />
                <LocalizedText source={"Query by Domain"} /></Card.Header>
              <Card.Description>
                <LocalizedText source={"Query content descriptors by domain and optional type"} /></Card.Description>
            </Card.Content>
            <Card.Content>
              <Form>
                <Form.Group widths="equal">
                  <Form.Field>
                    <label><LocalizedText source={"Domain"} /></label>
                    <Dropdown
                      onChange={(e, { value }) => setQueryDomain(value)}
                      options={[
                        { key: 'audio', text: interfaceText("Audio"), value: 'audio' },
                        { key: 'video', text: interfaceText("Video"), value: 'video' },
                        { key: 'image', text: interfaceText("Image"), value: 'image' },
                        { key: 'text', text: interfaceText("Text"), value: 'text' },
                        {
                          key: 'application',
                          text: interfaceText("Application"),
                          value: 'application',
                        },
                      ]}
                      selection
                      value={queryDomain}
                    />
                  </Form.Field>
                  <Form.Field>
                    <label><LocalizedText source={"Type (optional)"} /></label>
                    <Input
                      onChange={(e) => setQueryType(e.target.value)}
                      placeholder={interfaceText("track, album, movie, etc.")}
                      value={queryType}
                     {...interfaceTextProps("track, album, movie, etc.")}/>
                  </Form.Field>
                  <Form.Field>
                    <label><LocalizedText source={"Max Results"} /></label>
                    <Input
                      max="1000"
                      min="1"
                      onChange={(e) => setQueryMaxResults(e.target.value)}
                      type="number"
                      value={queryMaxResults}
                    />
                  </Form.Field>
                </Form.Group>
                <Button
                  disabled={!queryDomain.trim() || queryingDescriptors}
                  loading={queryingDescriptors}
                  onClick={handleQueryDescriptors}
                  primary
                >
                  <LocalizedText source={"Query Domain"} /></Button>
              </Form>

              {queryResult && (
                <div style={{ marginTop: '1em' }}>
                  {queryResult.error ? (
                    <Message error>
                      <p>{queryResult.error}</p>
                    </Message>
                  ) : (
                    <Message>
                      <Message.Header><LocalizedText source={"Query Results"} /></Message.Header>
                      <p>
                        <strong><LocalizedText source={"Domain:"} /></strong> {queryResult.domain}
                        {queryResult.type && (
                          <span>
                            {' '}
                            | <strong><LocalizedText source={"Type:"} /></strong> {queryResult.type}
                          </span>
                        )}
                        <br />
                        <strong><LocalizedText source={"Found:"} /></strong> {formatRegionalNumber(queryResult.totalFound)}
                        <br />
                        <strong><LocalizedText source={"Query Time:"} /></strong>{' '}
                        {formatRegionalFixedNumber(queryResult.queryDuration?.totalMilliseconds, 0)}
                        <LocalizedText source={"ms"} /><br />
                        <strong><LocalizedText source={"Has More:"} /></strong>{' '}
                        {queryResult.hasMoreResults ? <LocalizedText source={"Yes"} /> : <LocalizedText source={"No"} />}
                      </p>
                    </Message>
                  )}
                </div>
              )}
            </Card.Content>
          </Card>
        </Grid.Column>

        {/* Descriptor Verification */}
        <Grid.Column width={8}>
          <Card fluid>
            <Card.Content>
              <Card.Header>
                <Icon name="shield" />
                <LocalizedText source={"Descriptor Verification"} /></Card.Header>
              <Card.Description>
                <LocalizedText source={"Verify descriptor signature and freshness"} /></Card.Description>
            </Card.Content>
            <Card.Content>
              <Form>
                <Form.Field>
                  <label><LocalizedText source={"Descriptor JSON"} /></label>
                  <TextArea
                    onChange={(e) => setVerifyDescriptor(e.target.value)}
                    placeholder={interfaceText("Paste descriptor JSON to verify...")}
                    rows={8}
                    value={verifyDescriptor}
                   {...interfaceTextProps("Paste descriptor JSON to verify...")}/>
                </Form.Field>
                <Button
                  disabled={!verifyDescriptor.trim() || verifyingDescriptor}
                  loading={verifyingDescriptor}
                  onClick={handleVerifyDescriptor}
                  primary
                >
                  <LocalizedText source={"Verify Descriptor"} /></Button>
              </Form>

              {descriptorVerificationResult && (
                <div style={{ marginTop: '1em' }}>
                  {descriptorVerificationResult.error ? (
                    <Message error>
                      <p>{descriptorVerificationResult.error}</p>
                    </Message>
                  ) : (
                    <Message
                      success={descriptorVerificationResult.isValid}
                      warning={!descriptorVerificationResult.isValid}
                    >
                      <Message.Header>
                        <LocalizedText source={"Verification Result:"} />{' '}
                        {descriptorVerificationResult.isValid
                          ? <LocalizedText source={"Valid"} />
                          : <LocalizedText source={"Invalid"} />}
                      </Message.Header>
                      <p>
                        <strong><LocalizedText source={"Signature Valid:"} /></strong>{' '}
                        {descriptorVerificationResult.signatureValid
                          ? <LocalizedText source={"Yes"} />
                          : <LocalizedText source={"No"} />}
                        <br />
                        <strong><LocalizedText source={"Freshness Valid:"} /></strong>{' '}
                        {descriptorVerificationResult.freshnessValid
                          ? <LocalizedText source={"Yes"} />
                          : <LocalizedText source={"No"} />}
                        <br />
                        <strong><LocalizedText source={"Age:"} /></strong>{' '}
                        {formatRegionalFixedNumber(descriptorVerificationResult.age?.totalMinutes, 1)}{' '}
                        <LocalizedText source={"minutes"} /></p>
                      {descriptorVerificationResult.warnings?.length > 0 && (
                        <div>
                          <strong><LocalizedText source={"Warnings:"} /></strong>
                          <List bulleted>
                            {descriptorVerificationResult.warnings.map(
                              (warning, index) => (
                                <List.Item key={index}>{warning}</List.Item>
                              ),
                            )}
                          </List>
                        </div>
                      )}
                    </Message>
                  )}
                </div>
              )}
            </Card.Content>
          </Card>
        </Grid.Column>

        {/* Retrieval Management */}
        <Grid.Column width={16}>
          <Card fluid>
            <Card.Content>
              <Card.Header>
                <Icon name="chart line" />
                <LocalizedText source={"Retrieval Management"} /></Card.Header>
              <Card.Description>
                <LocalizedText source={"Monitor retrieval performance and manage cache"} /></Card.Description>
            </Card.Content>
            <Card.Content>
              <Button.Group fluid>
                <Button
                  disabled={loadingRetrievalStats}
                  loading={loadingRetrievalStats}
                  onClick={handleLoadRetrievalStats}
                >
                  <LocalizedText source={"Load Stats"} /></Button>
                <Button onClick={handleClearRetrievalCache}><LocalizedText source={"Clear Cache"} /></Button>
              </Button.Group>

              {/* Retrieval Stats */}
              {retrievalStats && (
                <div style={{ marginTop: '1em' }}>
                  {retrievalStats.error ? (
                    <Message error>
                      <p>{retrievalStats.error}</p>
                    </Message>
                  ) : (
                    <Message>
                      <Message.Header><LocalizedText source={"Retrieval Statistics"} /></Message.Header>
                      <p>
                        <strong><LocalizedText source={"Total Retrievals:"} /></strong>{' '}
                        {formatRegionalNumber(retrievalStats.totalRetrievals)}
                        <br />
                        <strong><LocalizedText source={"Cache Hits:"} /></strong> {formatRegionalNumber(retrievalStats.cacheHits)}
                        <br />
                        <strong><LocalizedText source={"Cache Misses:"} /></strong>{' '}
                        {formatRegionalNumber(retrievalStats.cacheMisses)}
                        <br />
                        <strong><LocalizedText source={"Hit Ratio:"} /></strong>{' '}
                        {formatRegionalFixedNumber((retrievalStats.cacheHitRatio * 100), 1)}%<br />
                        <strong><LocalizedText source={"Avg Retrieval Time:"} /></strong>{' '}
                        {formatRegionalFixedNumber(retrievalStats.averageRetrievalTime?.totalMilliseconds, 0)}
                        <LocalizedText source={"ms"} /><br />
                        <strong><LocalizedText source={"Active Cache Entries:"} /></strong>{' '}
                        {formatRegionalNumber(retrievalStats.activeCacheEntries)}
                        <br />
                        <strong><LocalizedText source={"Cache Size:"} /></strong>{' '}
                        {formatRegionalFixedNumber((retrievalStats.cacheSizeBytes / 1_024), 1)} KB
                      </p>
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

export default React.memo(ContentDescriptorRetrievalPanel);
