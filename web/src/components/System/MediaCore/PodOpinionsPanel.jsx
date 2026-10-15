import LocalizedText from "../../Shared/LocalizedText";
import { interfaceText, interfaceTextProps, useInterfaceLanguage } from "../../../lib/interfaceLocale";


import { formatRegionalDate, formatRegionalDateTime, useRegionalFormat, formatRegionalFixedNumber, formatRegionalNumber } from '../../../lib/util';
import * as mediacore from '../../../lib/mediacore';
import { toDisplayError } from '../../../lib/errors';
import Button from './MediaCoreButton';
import PodWorkflowNotice from './PodWorkflowNotice';
import React, { useEffect, useRef } from 'react';
import { toast } from 'react-toastify';
import {
  Card,
  Grid,
  Header,
  Icon,
  Input,
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

const opinionQueryKey = (podId, contentId) =>
  JSON.stringify([podId.trim(), contentId.trim()]);

const PodOpinionsPanel = ({ visible = true }) => {
  useInterfaceLanguage();
  useRegionalFormat();
  const mountedRef = useRef(true);

  useEffect(() => {
    mountedRef.current = true;
    return () => {
      mountedRef.current = false;
    };
  }, []);

  // Pod Opinion Management states
  const [opinionPodId, setOpinionPodId] = useMountedState(mountedRef, '');
  const [opinionContentId, setOpinionContentId] = useMountedState(mountedRef, '');
  const [opinionVariantHash, setOpinionVariantHash] = useMountedState(mountedRef, '');
  const [opinionScore, setOpinionScore] = useMountedState(mountedRef, 5);
  const [opinionNote, setOpinionNote] = useMountedState(mountedRef, '');
  const [opinions, setOpinions] = useMountedState(mountedRef, []);
  const [opinionsLoadedFor, setOpinionsLoadedFor] = useMountedState(
    mountedRef,
    null,
  );
  const [opinionsError, setOpinionsError] = useMountedState(mountedRef, null);
  const [opinionStatistics, setOpinionStatistics] = useMountedState(mountedRef, null);
  const [opinionStatisticsLoadedFor, setOpinionStatisticsLoadedFor] =
    useMountedState(mountedRef, null);
  const [opinionStatisticsError, setOpinionStatisticsError] = useMountedState(
    mountedRef,
    null,
  );
  const [publishOpinionLoading, setPublishOpinionLoading] = useMountedState(mountedRef, false);
  const [getOpinionsLoading, setGetOpinionsLoading] = useMountedState(mountedRef, false);
  const [getStatsLoading, setGetStatsLoading] = useMountedState(mountedRef, false);
  const [refreshOpinionsLoading, setRefreshOpinionsLoading] = useMountedState(mountedRef, false);

  // Pod Opinion Aggregation states
  const [aggregatedOpinions, setAggregatedOpinions] = useMountedState(mountedRef, null);
  const [aggregatedOpinionsLoadedFor, setAggregatedOpinionsLoadedFor] =
    useMountedState(mountedRef, null);
  const [aggregatedOpinionsError, setAggregatedOpinionsError] = useMountedState(
    mountedRef,
    null,
  );
  const [memberAffinities, setMemberAffinities] = useMountedState(mountedRef, {});
  const [memberAffinitiesLoadedFor, setMemberAffinitiesLoadedFor] = useMountedState(
    mountedRef,
    null,
  );
  const [memberAffinitiesError, setMemberAffinitiesError] = useMountedState(
    mountedRef,
    null,
  );
  const [consensusRecommendations, setConsensusRecommendations] = useMountedState(mountedRef, []);
  const [consensusRecommendationsLoadedFor, setConsensusRecommendationsLoadedFor] =
    useMountedState(mountedRef, null);
  const [consensusRecommendationsError, setConsensusRecommendationsError] =
    useMountedState(mountedRef, null);
  const [getAggregatedLoading, setGetAggregatedLoading] = useMountedState(mountedRef, false);
  const [getAffinitiesLoading, setGetAffinitiesLoading] = useMountedState(mountedRef, false);
  const [getRecommendationsLoading, setGetRecommendationsLoading] =
    useMountedState(mountedRef, false);
  const [updateAffinitiesLoading, setUpdateAffinitiesLoading] = useMountedState(mountedRef, false);


    const resetOpinionReadState = () => {
      setOpinionsLoadedFor(null);
      setOpinionsError(null);
      setOpinionStatisticsLoadedFor(null);
      setOpinionStatisticsError(null);
      setAggregatedOpinionsLoadedFor(null);
      setAggregatedOpinionsError(null);
      setMemberAffinitiesLoadedFor(null);
      setMemberAffinitiesError(null);
      setConsensusRecommendationsLoadedFor(null);
      setConsensusRecommendationsError(null);
    };


  const handlePublishOpinion = async () => {
    if (
      !opinionPodId.trim() ||
      !opinionContentId.trim() ||
      !opinionVariantHash.trim()
    ) {
      toast.error(interfaceText("Pod ID, Content ID, and Variant Hash are required"));
      return;
    }

    if (opinionScore < 0 || opinionScore > 10) {
      toast.error(interfaceText("Score must be between 0 and 10"));
      return;
    }

    try {
      setPublishOpinionLoading(true);
      const opinion = {
        contentId: opinionContentId.trim(),
        note: opinionNote.trim(),
        score: opinionScore,
        senderPeerId: 'current-user',
        variantHash: opinionVariantHash.trim(), // Get from session when available
      };

      await mediacore.publishOpinion(opinionPodId.trim(), opinion);
      toast.success(interfaceText("Opinion published successfully"));

      // Reset form
      setOpinionContentId('');
      setOpinionVariantHash('');
      setOpinionScore(5);
      setOpinionNote('');

      // Refresh opinions if we're viewing them
      if (opinionContentId) {
        await handleGetOpinions();
      }
    } catch (error_) {
      toast.error(interfaceText('Failed to publish opinion: {error}', { error: toDisplayError(error_) }));
    } finally {
      setPublishOpinionLoading(false);
    }
  };

  const handleGetOpinions = async () => {
    const requestedPodId = opinionPodId.trim();
    const requestedContentId = opinionContentId.trim();
    if (!requestedPodId || !requestedContentId) {
      toast.error(interfaceText("Pod ID and Content ID are required"));
      return;
    }

    try {
      setGetOpinionsLoading(true);
      setOpinionsError(null);
      const result = await mediacore.getContentOpinions(
        requestedPodId,
        requestedContentId,
      );
      if (!Array.isArray(result)) {
        throw new Error('Invalid opinions response');
      }
      setOpinions(result);
      setOpinionsLoadedFor(opinionQueryKey(requestedPodId, requestedContentId));
    } catch (error_) {
      const message = toDisplayError(error_, 'Failed to get opinions');
      setOpinionsError(message);
      toast.error(interfaceText("Failed to get opinions: {message}", { "message": (message) }));
    } finally {
      setGetOpinionsLoading(false);
    }
  };

  const handleGetOpinionStatistics = async () => {
    const requestedPodId = opinionPodId.trim();
    const requestedContentId = opinionContentId.trim();
    if (!requestedPodId || !requestedContentId) {
      toast.error(interfaceText("Pod ID and Content ID are required"));
      return;
    }

    try {
      setGetStatsLoading(true);
      setOpinionStatisticsError(null);
      const stats = await mediacore.getOpinionStatistics(
        requestedPodId,
        requestedContentId,
      );
      if (
        stats === null ||
        typeof stats !== 'object' ||
        Array.isArray(stats)
      ) {
        throw new Error('Invalid opinion statistics response');
      }
      setOpinionStatistics(stats);
      setOpinionStatisticsLoadedFor(
        opinionQueryKey(requestedPodId, requestedContentId),
      );
    } catch (error_) {
      const message = toDisplayError(
        error_,
        'Failed to get opinion statistics',
      );
      setOpinionStatisticsError(message);
      toast.error(interfaceText("Failed to get opinion statistics: {message}", { "message": (message) }));
    } finally {
      setGetStatsLoading(false);
    }
  };

  const handleRefreshOpinions = async () => {
    if (!opinionPodId.trim()) {
      toast.error(interfaceText("Pod ID is required"));
      return;
    }

    try {
      setRefreshOpinionsLoading(true);
      const result = await mediacore.refreshPodOpinions(opinionPodId.trim());
      toast.success(interfaceText("Refreshed {opinionsRefreshed} opinions", { "opinionsRefreshed": (result.opinionsRefreshed) }));

      // Refresh current view
      if (opinionContentId) {
        await Promise.all([handleGetOpinions(), handleGetOpinionStatistics()]);
      }
    } catch (error_) {
      toast.error(interfaceText('Failed to refresh opinions: {error}', { error: toDisplayError(error_) }));
    } finally {
      setRefreshOpinionsLoading(false);
    }
  };

  // Pod Opinion Aggregation handlers
  const handleGetAggregatedOpinions = async () => {
    const requestedPodId = opinionPodId.trim();
    const requestedContentId = opinionContentId.trim();
    if (!requestedPodId || !requestedContentId) {
      toast.error(interfaceText("Pod ID and Content ID are required"));
      return;
    }

    try {
      setGetAggregatedLoading(true);
      setAggregatedOpinionsError(null);
      const aggregated = await mediacore.getAggregatedOpinions(
        requestedPodId,
        requestedContentId,
      );
      if (
        aggregated === null ||
        typeof aggregated !== 'object' ||
        Array.isArray(aggregated)
      ) {
        throw new Error('Invalid aggregated opinions response');
      }
      setAggregatedOpinions(aggregated);
      setAggregatedOpinionsLoadedFor(
        opinionQueryKey(requestedPodId, requestedContentId),
      );
    } catch (error_) {
      const message = toDisplayError(
        error_,
        'Failed to get aggregated opinions',
      );
      setAggregatedOpinionsError(message);
      toast.error(interfaceText("Failed to get aggregated opinions: {message}", { "message": (message) }));
    } finally {
      setGetAggregatedLoading(false);
    }
  };

  const handleGetMemberAffinities = async () => {
    const requestedPodId = opinionPodId.trim();
    if (!requestedPodId) {
      toast.error(interfaceText("Pod ID is required"));
      return;
    }

    try {
      setGetAffinitiesLoading(true);
      setMemberAffinitiesError(null);
      const affinities = await mediacore.getMemberAffinities(
        requestedPodId,
      );
      if (
        affinities === null ||
        typeof affinities !== 'object' ||
        Array.isArray(affinities)
      ) {
        throw new Error('Invalid member affinities response');
      }
      setMemberAffinities(affinities);
      setMemberAffinitiesLoadedFor(requestedPodId);
    } catch (error_) {
      const message = toDisplayError(
        error_,
        'Failed to get member affinities',
      );
      setMemberAffinitiesError(message);
      toast.error(interfaceText("Failed to get member affinities: {message}", { "message": (message) }));
    } finally {
      setGetAffinitiesLoading(false);
    }
  };

  const handleGetConsensusRecommendations = async () => {
    const requestedPodId = opinionPodId.trim();
    const requestedContentId = opinionContentId.trim();
    if (!requestedPodId || !requestedContentId) {
      toast.error(interfaceText("Pod ID and Content ID are required"));
      return;
    }

    try {
      setGetRecommendationsLoading(true);
      setConsensusRecommendationsError(null);
      const recommendations = await mediacore.getConsensusRecommendations(
        requestedPodId,
        requestedContentId,
      );
      if (!Array.isArray(recommendations)) {
        throw new Error('Invalid consensus recommendations response');
      }
      setConsensusRecommendations(recommendations);
      setConsensusRecommendationsLoadedFor(
        opinionQueryKey(requestedPodId, requestedContentId),
      );
    } catch (error_) {
      const message = toDisplayError(
        error_,
        'Failed to get consensus recommendations',
      );
      setConsensusRecommendationsError(message);
      toast.error(interfaceText("Failed to get consensus recommendations: {message}", { "message": (message) }));
    } finally {
      setGetRecommendationsLoading(false);
    }
  };

  const handleUpdateMemberAffinities = async () => {
    if (!opinionPodId.trim()) {
      toast.error(interfaceText("Pod ID is required"));
      return;
    }

    try {
      setUpdateAffinitiesLoading(true);
      const result = await mediacore.updateMemberAffinities(
        opinionPodId.trim(),
      );
      toast.success(interfaceText("Updated affinities for {membersUpdated} members", { "membersUpdated": (result.membersUpdated) }));

      // Refresh affinities display
      await handleGetMemberAffinities();
    } catch (error_) {
      toast.error(interfaceText('Failed to update member affinities: {error}', { error: toDisplayError(error_) }));
    } finally {
      setUpdateAffinitiesLoading(false);
    }
  };


    const currentOpinionQueryKey = opinionQueryKey(
      opinionPodId,
      opinionContentId,
    );
    const hasCurrentOpinions =
      opinionsLoadedFor === currentOpinionQueryKey;
    const hasCurrentOpinionStatistics =
      opinionStatisticsLoadedFor === currentOpinionQueryKey;
    const hasCurrentAggregatedOpinions =
      aggregatedOpinionsLoadedFor === currentOpinionQueryKey;
    const hasCurrentMemberAffinities =
      memberAffinitiesLoadedFor === opinionPodId.trim();
    const hasCurrentConsensusRecommendations =
      consensusRecommendationsLoadedFor === currentOpinionQueryKey;


  return (
        <Grid.Column style={{ display: visible ? undefined : 'none' }} width={16}>
          <Card id="pod-opinion-management" fluid>
            <Card.Content>
              <Card.Header>
                <Icon name="star" />
                <LocalizedText source={"Pod Opinion Management"} /></Card.Header>
              <Card.Description>
                <LocalizedText source={"Publish and view opinions on content variants within pods for quality assessment and community feedback"} /></Card.Description>
              <PodWorkflowNotice title={interfaceText("Publishes opinion data")} {...interfaceTextProps("Publishes opinion data")}>
                <LocalizedText source={"Opinion publishing can expose peer preferences, ratings, confidence values, and content identifiers to other pod participants."} /></PodWorkflowNotice>
            </Card.Content>

            {/* Opinion Management */}
            <Card.Content>
              <Header size="small"><LocalizedText source={"Opinion Management"} /></Header>

              {/* Pod Selection */}
              <Input
                onChange={(e) => {
                  const nextPodId = e.target.value;
                  setOpinionPodId(nextPodId);
                  if (
                    opinionQueryKey(nextPodId, opinionContentId) !==
                    opinionQueryKey(opinionPodId, opinionContentId)
                  ) {
                    resetOpinionReadState();
                  }
                }}
                placeholder={interfaceText("Pod ID")}
                style={{ marginBottom: '1em', width: '100%' }}
                value={opinionPodId}
               {...interfaceTextProps("Pod ID")}/>

              <Button
                color="blue"
                disabled={!opinionPodId.trim()}
                loading={refreshOpinionsLoading}
                onClick={() => handleRefreshOpinions()}
                style={{ marginBottom: '1em' }}
              >
                <LocalizedText source={"Refresh Pod Opinions"} /></Button>

              {/* Content Opinions */}
              <Header size="tiny"><LocalizedText source={"Content Opinions"} /></Header>
              <Input
                onChange={(e) => {
                  const nextContentId = e.target.value;
                  setOpinionContentId(nextContentId);
                  if (
                    opinionQueryKey(opinionPodId, nextContentId) !==
                    opinionQueryKey(opinionPodId, opinionContentId)
                  ) {
                    resetOpinionReadState();
                  }
                }}
                placeholder={interfaceText("Content ID (e.g., content:audio:album:mb-id)")}
                style={{ marginBottom: '1em', width: '100%' }}
                value={opinionContentId}
               {...interfaceTextProps("Content ID (e.g., content:audio:album:mb-id)")}/>

              {opinionsError && (
                <Message
                  data-testid="media-core-opinions-error"
                  negative
                  size="small"
                >
                  {opinionsError}
                  {hasCurrentOpinions && opinions.length > 0 && (
                    <div><LocalizedText source={"Showing last successfully loaded opinions."} /></div>
                  )}
                </Message>
              )}

              <div style={{ marginBottom: '1em' }}>
                <Button
                  color="teal"
                  disabled={!opinionPodId.trim() || !opinionContentId.trim()}
                  loading={getOpinionsLoading}
                  onClick={() => handleGetOpinions()}
                  style={{ marginRight: '0.5em' }}
                >
                  <LocalizedText source={"Get Opinions"} /></Button>

                <Button
                  color="purple"
                  disabled={!opinionPodId.trim() || !opinionContentId.trim()}
                  loading={getStatsLoading}
                  onClick={() => handleGetOpinionStatistics()}
                >
                  <LocalizedText source={"Get Statistics"} /></Button>
              </div>

              {/* Opinion Statistics */}
              {opinionStatisticsError && (
                <Message
                  data-testid="media-core-opinion-statistics-error"
                  negative
                  size="small"
                >
                  {opinionStatisticsError}
                  {hasCurrentOpinionStatistics && opinionStatistics && (
                    <div><LocalizedText source={"Showing last successfully loaded statistics."} /></div>
                  )}
                </Message>
              )}

              {hasCurrentOpinionStatistics && opinionStatistics && (
                <Message
                  info
                  style={{ marginBottom: '1em' }}
                >
                  <Message.Header><LocalizedText source={"Opinion Statistics"} /></Message.Header>
                  <p>
                    <strong><LocalizedText source={"Total Opinions:"} /></strong>{' '}
                    {formatRegionalNumber(opinionStatistics.totalOpinions)}
                    <br />
                    <strong><LocalizedText source={"Unique Variants:"} /></strong>{' '}
                    {formatRegionalNumber(opinionStatistics.uniqueVariants)}
                    <br />
                    <strong><LocalizedText source={"Average Score:"} /></strong>{' '}
                    {formatRegionalFixedNumber(opinionStatistics.averageScore, 1)}
                    <br />
                    <strong><LocalizedText source={"Score Range:"} /></strong> {formatRegionalNumber(opinionStatistics.minScore)} -{' '}
                    {formatRegionalNumber(opinionStatistics.maxScore)}
                    <br />
                    <strong><LocalizedText source={"Last Updated:"} /></strong>{' '}
                    {formatRegionalDateTime(opinionStatistics.lastUpdated)}
                  </p>
                </Message>
              )}

              {/* Opinions List */}
              {hasCurrentOpinions && opinions.length > 0 && (
                <div style={{ marginBottom: '1em' }}>
                  <Header size="tiny"><LocalizedText source={"Opinions ("} />{opinions.length})</Header>
                  {opinions.map((opinion, index) => (
                    <Card
                      key={index}
                      style={{ marginBottom: '0.5em' }}
                    >
                      <Card.Content style={{ padding: '0.5em' }}>
                        <div
                          style={{
                            display: 'flex',
                            justifyContent: 'space-between',
                          }}
                        >
                          <div>
                            <strong><LocalizedText source={"Variant:"} /></strong>{' '}
                            {opinion.variantHash.slice(0, 8)}...
                            <br />
                            <strong><LocalizedText source={"Score:"} /></strong> {formatRegionalNumber(opinion.score)}/10
                            {opinion.note && (
                              <>
                                <br />
                                <strong><LocalizedText source={"Note:"} /></strong> {opinion.note}
                              </>
                            )}
                          </div>
                          <small>{opinion.senderPeerId}</small>
                        </div>
                      </Card.Content>
                    </Card>
                  ))}
                </div>
              )}

              {hasCurrentOpinions &&
                opinions.length === 0 &&
                opinionContentId &&
                !getOpinionsLoading &&
                !opinionsError && (
                <Message info size="small">
                  <LocalizedText source={"No opinions found for"} />{" "}{opinionContentId}.
                </Message>
              )}

              {/* Publish Opinion */}
              <Header size="small"><LocalizedText source={"Publish New Opinion"} /></Header>

              <Input
                onChange={(e) => setOpinionVariantHash(e.target.value)}
                placeholder={interfaceText("Variant Hash")}
                style={{ marginBottom: '1em', width: '100%' }}
                value={opinionVariantHash}
               {...interfaceTextProps("Variant Hash")}/>

              <div style={{ marginBottom: '1em' }}>
                <label
                  htmlFor="media-core-opinion-score"
                  style={{ marginRight: '1em' }}
                >
                  <LocalizedText source={"Score (0-10):"} /></label>
                <input
                  id="media-core-opinion-score"
                  max="10"
                  min="0"
                  onChange={(e) =>
                    setOpinionScore(Number.parseFloat(e.target.value))
                  }
                  step="0.5"
                  style={{ width: '200px' }}
                  type="range"
                  value={opinionScore}
                />
                <span style={{ marginLeft: '1em' }}>{opinionScore}/10</span>
              </div>

              <Input
                onChange={(e) => setOpinionNote(e.target.value)}
                placeholder={interfaceText("Optional note about this variant")}
                style={{ marginBottom: '1em', width: '100%' }}
                value={opinionNote}
               {...interfaceTextProps("Optional note about this variant")}/>

              <Button
                color="green"
                disabled={
                  !opinionPodId.trim() ||
                  !opinionContentId.trim() ||
                  !opinionVariantHash.trim()
                }
                loading={publishOpinionLoading}
                onClick={() => handlePublishOpinion()}
              >
                <LocalizedText source={"Publish Opinion"} /></Button>
            </Card.Content>

            {/* Opinion Aggregation */}
            <Card.Content>
              <Header size="small"><LocalizedText source={"Opinion Aggregation & Consensus"} /></Header>

              <div style={{ marginBottom: '1em' }}>
                <Button
                  color="purple"
                  disabled={!opinionPodId.trim() || !opinionContentId.trim()}
                  loading={getAggregatedLoading}
                  onClick={() => handleGetAggregatedOpinions()}
                  style={{ marginRight: '0.5em' }}
                >
                  <LocalizedText source={"Get Aggregated Opinions"} /></Button>

                <Button
                  color="blue"
                  disabled={!opinionPodId.trim()}
                  loading={getAffinitiesLoading}
                  onClick={() => handleGetMemberAffinities()}
                  style={{ marginRight: '0.5em' }}
                >
                  <LocalizedText source={"Get Member Affinities"} /></Button>

                <Button
                  color="teal"
                  disabled={!opinionPodId.trim() || !opinionContentId.trim()}
                  loading={getRecommendationsLoading}
                  onClick={() => handleGetConsensusRecommendations()}
                  style={{ marginRight: '0.5em' }}
                >
                  <LocalizedText source={"Get Recommendations"} /></Button>

                <Button
                  color="orange"
                  disabled={!opinionPodId.trim()}
                  loading={updateAffinitiesLoading}
                  onClick={() => handleUpdateMemberAffinities()}
                >
                  <LocalizedText source={"Update Affinities"} /></Button>
              </div>

              {/* Aggregated Opinions */}
              {aggregatedOpinionsError && (
                <Message
                  data-testid="media-core-aggregated-opinions-error"
                  negative
                  size="small"
                >
                  {aggregatedOpinionsError}
                  {hasCurrentAggregatedOpinions && aggregatedOpinions && (
                    <div><LocalizedText source={"Showing last successfully loaded aggregate."} /></div>
                  )}
                </Message>
              )}

              {hasCurrentAggregatedOpinions && aggregatedOpinions && (
                <div style={{ marginBottom: '1em' }}>
                  <Header size="tiny"><LocalizedText source={"Aggregated Opinion Results"} /></Header>
                  <Message info>
                    <strong><LocalizedText source={"Weighted Average:"} /></strong>{' '}
                    {formatRegionalFixedNumber(aggregatedOpinions.weightedAverageScore, 2)}/10
                    <br />
                    <strong><LocalizedText source={"Unweighted Average:"} /></strong>{' '}
                    {formatRegionalFixedNumber(aggregatedOpinions.unweightedAverageScore, 2)}/10
                    <br />
                    <strong><LocalizedText source={"Consensus Strength:"} /></strong>{' '}
                    {formatRegionalFixedNumber((aggregatedOpinions.consensusStrength * 100), 1)}%
                    <br />
                    <strong><LocalizedText source={"Total Opinions:"} /></strong>{' '}
                    {formatRegionalNumber(aggregatedOpinions.totalOpinions)}
                    <br />
                    <strong><LocalizedText source={"Unique Variants:"} /></strong>{' '}
                    {formatRegionalNumber(aggregatedOpinions.uniqueVariants)}
                    <br />
                    <strong><LocalizedText source={"Contributing Members:"} /></strong>{' '}
                    {aggregatedOpinions.contributingMembers}
                  </Message>

                  {/* Variant Breakdown */}
                  {aggregatedOpinions.variantAggregates.length > 0 && (
                    <div style={{ marginTop: '1em' }}>
                      <Header size="tiny"><LocalizedText source={"Variant Analysis"} /></Header>
                      {aggregatedOpinions.variantAggregates.map(
                        (variant, index) => (
                          <Card
                            key={index}
                            style={{ marginBottom: '0.5em' }}
                          >
                            <Card.Content style={{ padding: '0.5em' }}>
                              <div>
                                <strong><LocalizedText source={"Variant:"} /></strong>{' '}
                                {variant.variantHash.slice(0, 8)}...
                                <br />
                                <strong><LocalizedText source={"Weighted Score:"} /></strong>{' '}
                                {formatRegionalFixedNumber(variant.weightedAverageScore, 2)}/10
                                <br />
                                <strong><LocalizedText source={"Unweighted Score:"} /></strong>{' '}
                                {formatRegionalFixedNumber(variant.unweightedAverageScore, 2)}/10
                                <br />
                                <strong><LocalizedText source={"Opinions:"} /></strong>{' '}
                                {formatRegionalNumber(variant.opinionCount)}
                                <br />
                                <strong><LocalizedText source={"Agreement:"} /></strong>{' '}
                                {formatRegionalFixedNumber((
                                  1 -
                                  variant.scoreStandardDeviation / 5
                                ), 2)}{' '}
                                <LocalizedText source={"(lower std dev = higher agreement)"} /></div>
                            </Card.Content>
                          </Card>
                        ),
                      )}
                    </div>
                  )}
                </div>
              )}

              {/* Consensus Recommendations */}
              {consensusRecommendationsError && (
                <Message
                  data-testid="media-core-consensus-recommendations-error"
                  negative
                  size="small"
                >
                  {consensusRecommendationsError}
                  {hasCurrentConsensusRecommendations &&
                    consensusRecommendations.length > 0 && (
                    <div>
                      <LocalizedText source={"Showing last successfully loaded recommendations."} /></div>
                  )}
                </Message>
              )}

              {hasCurrentConsensusRecommendations &&
                consensusRecommendations.length > 0 && (
                <div style={{ marginBottom: '1em' }}>
                  <Header size="tiny"><LocalizedText source={"Consensus Recommendations"} /></Header>
                  {consensusRecommendations.map((rec, index) => (
                    <Card
                      key={index}
                      style={{
                        borderLeft:
                          rec.recommendation === 'StronglyRecommended'
                            ? '5px solid #21ba45'
                            : rec.recommendation === 'Recommended'
                              ? '5px solid #2185d0'
                              : rec.recommendation === 'Neutral'
                                ? '5px solid #fbbd08'
                                : rec.recommendation === 'NotRecommended'
                                  ? '5px solid #f2711c'
                                  : '5px solid #db2828',
                        marginBottom: '0.5em',
                      }}
                    >
                      <Card.Content style={{ padding: '0.5em' }}>
                        <div>
                          <strong><LocalizedText source={"Variant:"} /></strong>{' '}
                          {rec.variantHash.slice(0, 8)}...
                          <br />
                          <strong><LocalizedText source={"Recommendation:"} /></strong>{' '}
                          {rec.recommendation
                            .replaceAll(/([A-Z])/g, ' $1')
                            .trim()}
                          <br />
                          <strong><LocalizedText source={"Consensus Score:"} /></strong>{' '}
                          {formatRegionalFixedNumber((rec.consensusScore * 100), 1)}%<br />
                          <strong><LocalizedText source={"Reasoning:"} /></strong> {rec.reasoning}
                          <br />
                          <small>
                            <strong><LocalizedText source={"Factors:"} /></strong>{' '}
                            {rec.supportingFactors.join(', ')}
                          </small>
                        </div>
                      </Card.Content>
                    </Card>
                  ))}
                </div>
              )}

              {/* Member Affinities */}
              {memberAffinitiesError && (
                <Message
                  data-testid="media-core-member-affinities-error"
                  negative
                  size="small"
                >
                  {memberAffinitiesError}
                  {hasCurrentMemberAffinities &&
                    Object.keys(memberAffinities).length > 0 && (
                    <div><LocalizedText source={"Showing last successfully loaded affinities."} /></div>
                  )}
                </Message>
              )}

              {hasCurrentMemberAffinities &&
                Object.keys(memberAffinities).length > 0 && (
                <div style={{ marginBottom: '1em' }}>
                  <Header size="tiny">
                    <LocalizedText
                      source={"Member Affinities ({count})"}
                      values={{ count: Object.keys(memberAffinities).length }}
                    />
                  </Header>
                  {Object.entries(memberAffinities).map(
                    ([peerId, affinity], index) => (
                      <Card
                        key={index}
                        style={{ marginBottom: '0.5em' }}
                      >
                        <Card.Content style={{ padding: '0.5em' }}>
                          <div>
                            <strong><LocalizedText source={"Peer:"} /></strong> {peerId.slice(0, 8)}...
                            <br />
                            <strong><LocalizedText source={"Affinity Score:"} /></strong>{' '}
                            {formatRegionalFixedNumber((affinity.affinityScore * 100), 1)}%<br />
                            <strong><LocalizedText source={"Trust Score:"} /></strong>{' '}
                            {formatRegionalFixedNumber((affinity.trustScore * 100), 1)}%<br />
                            <strong><LocalizedText source={"Messages:"} /></strong> {formatRegionalNumber(affinity.messageCount)}
                            <br />
                            <strong><LocalizedText source={"Opinions:"} /></strong> {formatRegionalNumber(affinity.opinionCount)}
                            <br />
                            <small>
                              <LocalizedText source={"Last Activity:"} />{' '}
                              {formatRegionalDate(affinity.lastActivity)}
                            </small>
                          </div>
                        </Card.Content>
                      </Card>
                    ),
                  )}
                </div>
              )}
            </Card.Content>
          </Card>
        </Grid.Column>

  );
};

export default React.memo(PodOpinionsPanel);
