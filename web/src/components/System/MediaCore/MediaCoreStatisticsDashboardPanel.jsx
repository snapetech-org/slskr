import LocalizedText from "../../Shared/LocalizedText";
import { interfaceText, interfaceTextProps } from "../../../lib/interfaceLocale";


import { formatRegionalDateTime, useRegionalFormat, formatRegionalFixedNumber, formatRegionalNumber } from '../../../lib/util';
import * as mediacore from '../../../lib/mediacore';
import { toDisplayError } from '../../../lib/errors';
import Button from './MediaCoreButton';
import React, { useEffect, useRef } from 'react';
import { toast } from 'react-toastify';
import {
  Card,
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

const MediaCoreStatisticsDashboardPanel = () => {
  useRegionalFormat();
  const mountedRef = useRef(true);

  useEffect(() => {
    mountedRef.current = true;
    return () => {
      mountedRef.current = false;
    };
  }, []);

  const [mediaCoreDashboard, setMediaCoreDashboard] = useMountedState(mountedRef, null);
  const [contentRegistryStats, setContentRegistryStats] = useMountedState(mountedRef, null);
  const [descriptorStats, setDescriptorStats] = useMountedState(mountedRef, null);
  const [fuzzyMatchingStats, setFuzzyMatchingStats] = useMountedState(mountedRef, null);
  const [ipldMappingStats, setIpldMappingStats] = useMountedState(mountedRef, null);
  const [perceptualHashingStats, setPerceptualHashingStats] = useMountedState(mountedRef, null);
  const [metadataPortabilityStats, setMetadataPortabilityStats] =
    useMountedState(mountedRef, null);
  const [contentPublishingStats, setContentPublishingStats] = useMountedState(mountedRef, null);
  const [loadingDashboard, setLoadingDashboard] = useMountedState(mountedRef, false);
  const [loadingRegistryStats, setLoadingRegistryStats] = useMountedState(mountedRef, false);
  const [loadingDescriptorStats, setLoadingDescriptorStats] = useMountedState(mountedRef, false);
  const [loadingFuzzyStats, setLoadingFuzzyStats] = useMountedState(mountedRef, false);
  const [loadingIpldStats, setLoadingIpldStats] = useMountedState(mountedRef, false);
  const [loadingPerceptualStats, setLoadingPerceptualStats] = useMountedState(mountedRef, false);
  const [loadingPortabilityStats, setLoadingPortabilityStats] = useMountedState(mountedRef, false);
  const [loadingPublishingStats, setLoadingPublishingStats] = useMountedState(mountedRef, false);


  const handleLoadMediaCoreDashboard = async () => {
    try {
      setLoadingDashboard(true);
      setMediaCoreDashboard(null);
      const result = await mediacore.getMediaCoreDashboard();
      setMediaCoreDashboard(result);
    } catch (error_) {
      setMediaCoreDashboard({ error: toDisplayError(error_) });
    } finally {
      setLoadingDashboard(false);
    }
  };

  const handleLoadContentRegistryStats = async () => {
    try {
      setLoadingRegistryStats(true);
      setContentRegistryStats(null);
      const result = await mediacore.getContentRegistryStats();
      setContentRegistryStats(result);
    } catch (error_) {
      setContentRegistryStats({ error: toDisplayError(error_) });
    } finally {
      setLoadingRegistryStats(false);
    }
  };

  const handleLoadDescriptorStats = async () => {
    try {
      setLoadingDescriptorStats(true);
      setDescriptorStats(null);
      const result = await mediacore.getDescriptorStats();
      setDescriptorStats(result);
    } catch (error_) {
      setDescriptorStats({ error: toDisplayError(error_) });
    } finally {
      setLoadingDescriptorStats(false);
    }
  };

  const handleLoadFuzzyMatchingStats = async () => {
    try {
      setLoadingFuzzyStats(true);
      setFuzzyMatchingStats(null);
      const result = await mediacore.getFuzzyMatchingStats();
      setFuzzyMatchingStats(result);
    } catch (error_) {
      setFuzzyMatchingStats({ error: toDisplayError(error_) });
    } finally {
      setLoadingFuzzyStats(false);
    }
  };

  const handleLoadIpldMappingStats = async () => {
    try {
      setLoadingIpldStats(true);
      setIpldMappingStats(null);
      const result = await mediacore.getIpldMappingStats();
      setIpldMappingStats(result);
    } catch (error_) {
      setIpldMappingStats({ error: toDisplayError(error_) });
    } finally {
      setLoadingIpldStats(false);
    }
  };

  const handleLoadPerceptualHashingStats = async () => {
    try {
      setLoadingPerceptualStats(true);
      setPerceptualHashingStats(null);
      const result = await mediacore.getPerceptualHashingStats();
      setPerceptualHashingStats(result);
    } catch (error_) {
      setPerceptualHashingStats({ error: toDisplayError(error_) });
    } finally {
      setLoadingPerceptualStats(false);
    }
  };

  const handleLoadMetadataPortabilityStats = async () => {
    try {
      setLoadingPortabilityStats(true);
      setMetadataPortabilityStats(null);
      const result = await mediacore.getMetadataPortabilityStats();
      setMetadataPortabilityStats(result);
    } catch (error_) {
      setMetadataPortabilityStats({ error: toDisplayError(error_) });
    } finally {
      setLoadingPortabilityStats(false);
    }
  };

  const handleLoadContentPublishingStats = async () => {
    try {
      setLoadingPublishingStats(true);
      setContentPublishingStats(null);
      const result = await mediacore.getContentPublishingStats();
      setContentPublishingStats(result);
    } catch (error_) {
      setContentPublishingStats({ error: toDisplayError(error_) });
    } finally {
      setLoadingPublishingStats(false);
    }
  };

  const handleResetMediaCoreStats = async () => {
    if (
      !confirm(
        'Are you sure you want to reset all MediaCore statistics? This cannot be undone.',
      )
    ) {
      return;
    }

    try {
      await mediacore.resetMediaCoreStats();
      // Clear all displayed stats
      setMediaCoreDashboard(null);
      setContentRegistryStats(null);
      setDescriptorStats(null);
      setFuzzyMatchingStats(null);
      setIpldMappingStats(null);
      setPerceptualHashingStats(null);
      setMetadataPortabilityStats(null);
      setContentPublishingStats(null);
      toast.success(interfaceText("MediaCore statistics have been reset"));
    } catch (error_) {
      toast.error(interfaceText('Failed to reset stats: {error}', { error: toDisplayError(error_) }));
    }
  };


  return (
    <>
        {/* MediaCore Statistics Dashboard */}
        <Grid.Column width={16}>
          <Card fluid>
            <Card.Content>
              <Card.Header>
                <Icon name="chart bar" />
                <LocalizedText source={"MediaCore Statistics Dashboard"} /></Card.Header>
              <Card.Description>
                <LocalizedText source={"Comprehensive overview of all MediaCore system performance and usage metrics"} /></Card.Description>
            </Card.Content>
            <Card.Content>
              <Button.Group fluid>
                <Button
                  disabled={loadingDashboard}
                  loading={loadingDashboard}
                  onClick={handleLoadMediaCoreDashboard}
                  primary
                >
                  <LocalizedText source={"Load Full Dashboard"} /></Button>
                <Button
                  color="red"
                  onClick={handleResetMediaCoreStats}
                >
                  <LocalizedText source={"Reset All Stats"} /></Button>
              </Button.Group>

              {/* Dashboard Overview */}
              {mediaCoreDashboard && !mediaCoreDashboard.error && (
                <div style={{ marginTop: '1em' }}>
                  <Message info>
                    <Message.Header><LocalizedText source={"System Overview"} /></Message.Header>
                    <p>
                      <strong><LocalizedText source={"Uptime:"} /></strong>{' '}
                      {mediaCoreDashboard.uptime
                        ? `${Math.floor(mediaCoreDashboard.uptime.totalHours)}h ${mediaCoreDashboard.uptime.minutes}m`
                        : interfaceText('N/A')}
                      <br />
                      <strong><LocalizedText source={"Last Updated:"} /></strong>{' '}
                      {mediaCoreDashboard.timestamp
                        ? formatRegionalDateTime(mediaCoreDashboard.timestamp)
                        : interfaceText('N/A')}
                    </p>
                  </Message>

                  {/* System Resources */}
                  {mediaCoreDashboard.systemResources && (
                    <Message>
                      <Message.Header><LocalizedText source={"System Resources"} /></Message.Header>
                      <p>
                        <strong><LocalizedText source={"Working Set:"} /></strong>{' '}
                        {formatRegionalFixedNumber((
                          mediaCoreDashboard.systemResources.workingSetBytes /
                          1_024 /
                          1_024
                        ), 1)}{' '}
                        MB
                        <br />
                        <strong><LocalizedText source={"Private Memory:"} /></strong>{' '}
                        {formatRegionalFixedNumber((
                          mediaCoreDashboard.systemResources
                            .privateMemoryBytes /
                          1_024 /
                          1_024
                        ), 1)}{' '}
                        MB
                        <br />
                        <strong><LocalizedText source={"GC Memory:"} /></strong>{' '}
                        {formatRegionalFixedNumber((
                          mediaCoreDashboard.systemResources
                            .gcTotalMemoryBytes /
                          1_024 /
                          1_024
                        ), 1)}{' '}
                        MB
                        <br />
                        <strong><LocalizedText source={"Thread Count:"} /></strong>{' '}
                        {formatRegionalNumber(mediaCoreDashboard.systemResources.threadCount)}
                      </p>
                    </Message>
                  )}
                </div>
              )}

              {/* Error Display */}
              {mediaCoreDashboard?.error && (
                <Message
                  error
                  style={{ marginTop: '1em' }}
                >
                  <p><LocalizedText source={"Failed to load dashboard:"} />{" "}{mediaCoreDashboard.error}</p>
                </Message>
              )}
            </Card.Content>
          </Card>
        </Grid.Column>

        {/* Content Registry Stats */}
        <Grid.Column width={8}>
          <Card fluid>
            <Card.Content>
              <Card.Header>
                <Icon name="database" />
                <LocalizedText source={"Content Registry"} /></Card.Header>
              <Card.Description>
                <LocalizedText source={"Content ID mappings and domain statistics"} /></Card.Description>
            </Card.Content>
            <Card.Content>
              <Button
                disabled={loadingRegistryStats}
                fluid
                loading={loadingRegistryStats}
                onClick={handleLoadContentRegistryStats}
              >
                <LocalizedText source={"Load Registry Stats"} /></Button>

              {contentRegistryStats && !contentRegistryStats.error && (
                <div style={{ marginTop: '1em' }}>
                  <Message success>
                    <Message.Header><LocalizedText source={"Registry Overview"} /></Message.Header>
                    <p>
                      <strong><LocalizedText source={"Total Mappings:"} /></strong>{' '}
                      {formatRegionalNumber(contentRegistryStats.totalMappings)}
                      <br />
                      <strong><LocalizedText source={"Domains:"} /></strong>{' '}
                      {formatRegionalNumber(contentRegistryStats.totalDomains)}
                      <br />
                      <strong><LocalizedText source={"Avg Mappings/Domain:"} /></strong>{' '}
                      {formatRegionalFixedNumber(contentRegistryStats.averageMappingsPerDomain, 1)}
                    </p>
                    {contentRegistryStats.mappingsByDomain &&
                      Object.keys(contentRegistryStats.mappingsByDomain)
                        .length > 0 && (
                        <div style={{ marginTop: '0.5em' }}>
                          <strong><LocalizedText source={"Mappings by Domain:"} /></strong>
                          {Object.entries(
                            contentRegistryStats.mappingsByDomain,
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
                </div>
              )}

              {contentRegistryStats?.error && (
                <Message
                  error
                  style={{ marginTop: '1em' }}
                >
                  <p>{contentRegistryStats.error}</p>
                </Message>
              )}
            </Card.Content>
          </Card>
        </Grid.Column>

        {/* Descriptor Stats */}
        <Grid.Column width={8}>
          <Card fluid>
            <Card.Content>
              <Card.Header>
                <Icon name="search" />
                <LocalizedText source={"Descriptor Retrieval"} /></Card.Header>
              <Card.Description>
                <LocalizedText source={"Cache performance and retrieval statistics"} /></Card.Description>
            </Card.Content>
            <Card.Content>
              <Button
                disabled={loadingDescriptorStats}
                fluid
                loading={loadingDescriptorStats}
                onClick={handleLoadDescriptorStats}
              >
                <LocalizedText source={"Load Descriptor Stats"} /></Button>

              {descriptorStats && !descriptorStats.error && (
                <div style={{ marginTop: '1em' }}>
                  <Message>
                    <Message.Header><LocalizedText source={"Cache Performance"} /></Message.Header>
                    <p>
                      <strong><LocalizedText source={"Total Retrievals:"} /></strong>{' '}
                      {formatRegionalNumber(descriptorStats.totalRetrievals)}
                      <br />
                      <strong><LocalizedText source={"Cache Hits:"} /></strong> {formatRegionalNumber(descriptorStats.cacheHits)}
                      <br />
                      <strong><LocalizedText source={"Cache Misses:"} /></strong>{' '}
                      {formatRegionalNumber(descriptorStats.cacheMisses)}
                      <br />
                      <strong><LocalizedText source={"Hit Ratio:"} /></strong>{' '}
                      {formatRegionalFixedNumber((descriptorStats.cacheHitRatio * 100), 1)}%<br />
                      <strong><LocalizedText source={"Avg Retrieval Time:"} /></strong>{' '}
                      {formatRegionalFixedNumber(descriptorStats.averageRetrievalTime?.totalMilliseconds, 0)}
                      <LocalizedText source={"ms"} /><br />
                      <strong><LocalizedText source={"Active Cache Entries:"} /></strong>{' '}
                      {formatRegionalNumber(descriptorStats.activeCacheEntries)}
                      <br />
                      <strong><LocalizedText source={"Cache Size:"} /></strong>{' '}
                      {formatRegionalFixedNumber((descriptorStats.cacheSizeBytes / 1_024), 1)} KB
                    </p>
                  </Message>
                </div>
              )}

              {descriptorStats?.error && (
                <Message
                  error
                  style={{ marginTop: '1em' }}
                >
                  <p>{descriptorStats.error}</p>
                </Message>
              )}
            </Card.Content>
          </Card>
        </Grid.Column>

        {/* Fuzzy Matching Stats */}
        <Grid.Column width={8}>
          <Card fluid>
            <Card.Content>
              <Card.Header>
                <Icon name="magic" />
                <LocalizedText source={"Fuzzy Matching"} /></Card.Header>
              <Card.Description>
                <LocalizedText source={"Similarity detection and accuracy metrics"} /></Card.Description>
            </Card.Content>
            <Card.Content>
              <Button
                disabled={loadingFuzzyStats}
                fluid
                loading={loadingFuzzyStats}
                onClick={handleLoadFuzzyMatchingStats}
              >
                <LocalizedText source={"Load Fuzzy Stats"} /></Button>

              {fuzzyMatchingStats && !fuzzyMatchingStats.error && (
                <div style={{ marginTop: '1em' }}>
                  <Message>
                    <Message.Header><LocalizedText source={"Matching Performance"} /></Message.Header>
                    <p>
                      <strong><LocalizedText source={"Total Matches:"} /></strong>{' '}
                      {formatRegionalNumber(fuzzyMatchingStats.totalMatches)}
                      <br />
                      <strong><LocalizedText source={"Success Rate:"} /></strong>{' '}
                      {formatRegionalFixedNumber((fuzzyMatchingStats.successRate * 100), 1)}%<br />
                      <strong><LocalizedText source={"Avg Confidence:"} /></strong>{' '}
                      {formatRegionalFixedNumber((
                        fuzzyMatchingStats.averageConfidenceScore * 100
                      ), 1)}
                      %<br />
                      <strong><LocalizedText source={"Avg Match Time:"} /></strong>{' '}
                      {formatRegionalFixedNumber(fuzzyMatchingStats.averageMatchingTime?.totalMilliseconds, 0)}
                      <LocalizedText source={"ms"} /></p>
                    {fuzzyMatchingStats.accuracyByAlgorithm &&
                      Object.keys(fuzzyMatchingStats.accuracyByAlgorithm)
                        .length > 0 && (
                        <div style={{ marginTop: '0.5em' }}>
                          <strong><LocalizedText source={"Algorithm Accuracy:"} /></strong>
                          {Object.entries(
                            fuzzyMatchingStats.accuracyByAlgorithm,
                          ).map(([algorithm, stats]) => (
                            <div
                              key={algorithm}
                              style={{ margin: '0.2em 0' }}
                            >
                              <small>
                                {algorithm}<LocalizedText source={": F1="} />{formatRegionalFixedNumber(stats.f1Score, 2)}<LocalizedText source={", Precision="} />{formatRegionalFixedNumber(stats.precision, 2)}
                              </small>
                            </div>
                          ))}
                        </div>
                      )}
                  </Message>
                </div>
              )}

              {fuzzyMatchingStats?.error && (
                <Message
                  error
                  style={{ marginTop: '1em' }}
                >
                  <p>{fuzzyMatchingStats.error}</p>
                </Message>
              )}
            </Card.Content>
          </Card>
        </Grid.Column>

        {/* Perceptual Hashing Stats */}
        <Grid.Column width={8}>
          <Card fluid>
            <Card.Content>
              <Card.Header>
                <Icon name="hashtag" />
                <LocalizedText source={"Perceptual Hashing"} /></Card.Header>
              <Card.Description>
                <LocalizedText source={"Hash computation performance and accuracy"} /></Card.Description>
            </Card.Content>
            <Card.Content>
              <Button
                disabled={loadingPerceptualStats}
                fluid
                loading={loadingPerceptualStats}
                onClick={handleLoadPerceptualHashingStats}
              >
                <LocalizedText source={"Load Hashing Stats"} /></Button>

              {perceptualHashingStats && !perceptualHashingStats.error && (
                <div style={{ marginTop: '1em' }}>
                  <Message>
                    <Message.Header><LocalizedText source={"Hashing Performance"} /></Message.Header>
                    <p>
                      <strong><LocalizedText source={"Total Hashes:"} /></strong>{' '}
                      {perceptualHashingStats.totalHashesComputed}
                      <br />
                      <strong><LocalizedText source={"Avg Computation Time:"} /></strong>{' '}
                      {formatRegionalFixedNumber(perceptualHashingStats.averageComputationTime?.totalMilliseconds, 0)}
                      <LocalizedText source={"ms"} /><br />
                      <strong><LocalizedText source={"Overall Accuracy:"} /></strong>{' '}
                      {formatRegionalFixedNumber((perceptualHashingStats.overallAccuracy * 100), 1)}
                      %<br />
                      <strong><LocalizedText source={"Duplicates Detected:"} /></strong>{' '}
                      {perceptualHashingStats.duplicateHashesDetected}
                    </p>
                    {perceptualHashingStats.statsByAlgorithm &&
                      Object.keys(perceptualHashingStats.statsByAlgorithm)
                        .length > 0 && (
                        <div style={{ marginTop: '0.5em' }}>
                          <strong><LocalizedText source={"Algorithm Breakdown:"} /></strong>
                          {Object.entries(
                            perceptualHashingStats.statsByAlgorithm,
                          ).map(([algorithm, stats]) => (
                            <div
                              key={algorithm}
                              style={{ margin: '0.2em 0' }}
                            >
                              <small>
                                {algorithm}: {stats.hashesComputed} <LocalizedText source={"hashes,"} />{' '}
                                {formatRegionalFixedNumber(stats.averageTime.totalMilliseconds, 0)}
                                <LocalizedText source={"ms avg,"} />{" "}{formatRegionalFixedNumber(stats.accuracy, 2)} <LocalizedText source={"accuracy"} /></small>
                            </div>
                          ))}
                        </div>
                      )}
                  </Message>
                </div>
              )}

              {perceptualHashingStats?.error && (
                <Message
                  error
                  style={{ marginTop: '1em' }}
                >
                  <p>{perceptualHashingStats.error}</p>
                </Message>
              )}
            </Card.Content>
          </Card>
        </Grid.Column>

        {/* IPLD Mapping Stats */}
        <Grid.Column width={8}>
          <Card fluid>
            <Card.Content>
              <Card.Header>
                <Icon name="sitemap" />
                <LocalizedText source={"IPLD Mapping"} /></Card.Header>
              <Card.Description>
                <LocalizedText source={"Graph structure and link statistics"} /></Card.Description>
            </Card.Content>
            <Card.Content>
              <Button
                disabled={loadingIpldStats}
                fluid
                loading={loadingIpldStats}
                onClick={handleLoadIpldMappingStats}
              >
                <LocalizedText source={"Load IPLD Stats"} /></Button>

              {ipldMappingStats && !ipldMappingStats.error && (
                <div style={{ marginTop: '1em' }}>
                  <Message>
                    <Message.Header><LocalizedText source={"Graph Statistics"} /></Message.Header>
                    <p>
                      <strong><LocalizedText source={"Total Links:"} /></strong>{' '}
                      {formatRegionalNumber(ipldMappingStats.totalLinks)}
                      <br />
                      <strong><LocalizedText source={"Total Nodes:"} /></strong>{' '}
                      {formatRegionalNumber(ipldMappingStats.totalNodes)}
                      <br />
                      <strong><LocalizedText source={"Total Graphs:"} /></strong>{' '}
                      {formatRegionalNumber(ipldMappingStats.totalGraphs)}
                      <br />
                      <strong><LocalizedText source={"Connectivity Ratio:"} /></strong>{' '}
                      {formatRegionalFixedNumber((ipldMappingStats.graphConnectivityRatio * 100), 1)}
                      %<br />
                      <strong><LocalizedText source={"Broken Links:"} /></strong>{' '}
                      {ipldMappingStats.brokenLinksDetected}
                      <br />
                      <strong><LocalizedText source={"Avg Traversal Time:"} /></strong>{' '}
                      {formatRegionalFixedNumber(ipldMappingStats.averageTraversalTime?.totalMilliseconds, 0)}
                      <LocalizedText source={"ms"} /></p>
                  </Message>
                </div>
              )}

              {ipldMappingStats?.error && (
                <Message
                  error
                  style={{ marginTop: '1em' }}
                >
                  <p>{ipldMappingStats.error}</p>
                </Message>
              )}
            </Card.Content>
          </Card>
        </Grid.Column>

        {/* Metadata Portability Stats */}
        <Grid.Column width={8}>
          <Card fluid>
            <Card.Content>
              <Card.Header>
                <Icon name="exchange" />
                <LocalizedText source={"Metadata Portability"} /></Card.Header>
              <Card.Description>
                <LocalizedText source={"Export/import operations and conflict resolution"} /></Card.Description>
            </Card.Content>
            <Card.Content>
              <Button
                disabled={loadingPortabilityStats}
                fluid
                loading={loadingPortabilityStats}
                onClick={handleLoadMetadataPortabilityStats}
              >
                <LocalizedText source={"Load Portability Stats"} /></Button>

              {metadataPortabilityStats && !metadataPortabilityStats.error && (
                <div style={{ marginTop: '1em' }}>
                  <Message>
                    <Message.Header><LocalizedText source={"Portability Metrics"} /></Message.Header>
                    <p>
                      <strong><LocalizedText source={"Total Exports:"} /></strong>{' '}
                      {formatRegionalNumber(metadataPortabilityStats.totalExports)}
                      <br />
                      <strong><LocalizedText source={"Total Imports:"} /></strong>{' '}
                      {formatRegionalNumber(metadataPortabilityStats.totalImports)}
                      <br />
                      <strong><LocalizedText source={"Import Success Rate:"} /></strong>{' '}
                      {formatRegionalFixedNumber((
                        metadataPortabilityStats.importSuccessRate * 100
                      ), 1)}
                      %<br />
                      <strong><LocalizedText source={"Data Transferred:"} /></strong>{' '}
                      {formatRegionalFixedNumber((
                        metadataPortabilityStats.totalDataTransferred / 1_024
                      ), 1)}{' '}
                      KB
                      <br />
                      <strong><LocalizedText source={"Avg Export Time:"} /></strong>{' '}
                      {formatRegionalFixedNumber(metadataPortabilityStats.averageExportTime?.totalMilliseconds, 0)}
                      <LocalizedText source={"ms"} /><br />
                      <strong><LocalizedText source={"Avg Import Time:"} /></strong>{' '}
                      {formatRegionalFixedNumber(metadataPortabilityStats.averageImportTime?.totalMilliseconds, 0)}
                      <LocalizedText source={"ms"} /></p>
                  </Message>
                </div>
              )}

              {metadataPortabilityStats?.error && (
                <Message
                  error
                  style={{ marginTop: '1em' }}
                >
                  <p>{metadataPortabilityStats.error}</p>
                </Message>
              )}
            </Card.Content>
          </Card>
        </Grid.Column>

        {/* Content Publishing Stats */}
        <Grid.Column width={16}>
          <Card fluid>
            <Card.Content>
              <Card.Header>
                <Icon name="cloud upload" />
                <LocalizedText source={"Content Publishing"} /></Card.Header>
              <Card.Description>
                <LocalizedText source={"DHT publishing performance and publication management"} /></Card.Description>
            </Card.Content>
            <Card.Content>
              <Button
                disabled={loadingPublishingStats}
                fluid
                loading={loadingPublishingStats}
                onClick={handleLoadContentPublishingStats}
              >
                <LocalizedText source={"Load Publishing Stats"} /></Button>

              {contentPublishingStats && !contentPublishingStats.error && (
                <div style={{ marginTop: '1em' }}>
                  <Message>
                    <Message.Header><LocalizedText source={"Publishing Overview"} /></Message.Header>
                    <p>
                      <strong><LocalizedText source={"Total Published:"} /></strong>{' '}
                      {formatRegionalNumber(contentPublishingStats.totalPublished)}
                      <br />
                      <strong><LocalizedText source={"Active Publications:"} /></strong>{' '}
                      {formatRegionalNumber(contentPublishingStats.activePublications)}
                      <br />
                      <strong><LocalizedText source={"Expired Publications:"} /></strong>{' '}
                      {formatRegionalNumber(contentPublishingStats.expiredPublications)}
                      <br />
                      <strong><LocalizedText source={"Success Rate:"} /></strong>{' '}
                      {formatRegionalFixedNumber((
                        contentPublishingStats.publicationSuccessRate * 100
                      ), 1)}
                      %<br />
                      <strong><LocalizedText source={"Republished:"} /></strong>{' '}
                      {contentPublishingStats.republishedDescriptors}
                      <br />
                      <strong><LocalizedText source={"Failed:"} /></strong>{' '}
                      {formatRegionalNumber(contentPublishingStats.failedPublications)}
                      <br />
                      <strong><LocalizedText source={"Avg Publish Time:"} /></strong>{' '}
                      {formatRegionalFixedNumber(contentPublishingStats.averagePublishTime?.totalMilliseconds, 0)}
                      <LocalizedText source={"ms"} /></p>
                    {contentPublishingStats.publicationsByDomain &&
                      Object.keys(contentPublishingStats.publicationsByDomain)
                        .length > 0 && (
                        <div style={{ marginTop: '0.5em' }}>
                          <strong><LocalizedText source={"Publications by Domain:"} /></strong>
                          {Object.entries(
                            contentPublishingStats.publicationsByDomain,
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
                </div>
              )}

              {contentPublishingStats?.error && (
                <Message
                  error
                  style={{ marginTop: '1em' }}
                >
                  <p>{contentPublishingStats.error}</p>
                </Message>
              )}
            </Card.Content>
          </Card>
        </Grid.Column>

    </>
  );
};

export default React.memo(MediaCoreStatisticsDashboardPanel);
