import LocalizedText from "../Shared/LocalizedText";
import { interfaceText, interfaceTextProps, useInterfaceLanguage } from "../../lib/interfaceLocale";
// <copyright file="FederatedTasteRecommendationsPanel.jsx" company="slskr Team">
// Copyright (c) slskr Team. All rights reserved.
// </copyright>

import {
  fetchTasteRecommendations,
  previewTasteRecommendationGraph,
  promoteTasteRecommendationToWishlist,
  subscribeTasteRecommendationReleaseRadar,
} from '../../lib/tasteRecommendations';
import { toDisplayError } from '../../lib/errors';
import { useMountedRef } from '../../lib/useMountedRef';
import React, { useRef, useState } from 'react';
import { toast } from 'react-toastify';
import {
  Button,
  Checkbox,
  Form,
  Header,
  Icon,
  Label,
  List,
  Message,
  Popup,
  Segment,
} from 'semantic-ui-react';

const isObject = (value) =>
  value !== null && typeof value === 'object' && !Array.isArray(value);

const asText = (value, fallback = '') =>
  typeof value === 'string' || typeof value === 'number' ? String(value) : fallback;

const asCount = (value) =>
  typeof value === 'number' && Number.isFinite(value) ? value : 0;

const getCreator = (workRef = {}) =>
  asText(workRef.creator ?? workRef.Creator);

const getTitle = (workRef = {}) =>
  asText(workRef.title ?? workRef.Title, 'Untitled recommendation');

const normalizeRecommendation = (recommendation) => {
  if (!isObject(recommendation)) {
    return null;
  }

  const workRef = isObject(recommendation.workRef)
    ? recommendation.workRef
    : isObject(recommendation.WorkRef)
      ? recommendation.WorkRef
      : {};

  return {
    ...recommendation,
    reasons: Array.isArray(recommendation.reasons)
      ? recommendation.reasons.map((reason) => asText(reason)).filter(Boolean)
      : [],
    score: asCount(recommendation.score),
    sourceActors: Array.isArray(recommendation.sourceActors)
      ? recommendation.sourceActors.map((actor) => asText(actor)).filter(Boolean)
      : [],
    trustedSourceCount: asCount(recommendation.trustedSourceCount),
    workRef,
  };
};

const normalizeSummary = (summary) => ({
  ...summary,
  candidateCount: asCount(summary.candidateCount),
  minimumTrustedSources: asCount(summary.minimumTrustedSources),
  trustedActorCount: asCount(summary.trustedActorCount),
});

const normalizeGraphPreview = (preview) => {
  if (!isObject(preview)) {
    return null;
  }

  return {
    ...preview,
    edgeCount: asCount(preview.edgeCount),
    nodeCount: asCount(preview.nodeCount),
  };
};

const responseMessage = (response, fallback) =>
  typeof response?.data?.message === 'string' && response.data.message.trim()
    ? response.data.message
    : fallback;

const FederatedTasteRecommendationsPanel = ({ disabled }) => {
  useInterfaceLanguage();
  const [error, setError] = useState('');
  const [graphPreview, setGraphPreview] = useState(null);
  const [includeSoulseekRecommendations, setIncludeSoulseekRecommendations] = useState(false);
  const [includeSourceActors, setIncludeSourceActors] = useState(false);
  const [limit, setLimit] = useState(20);
  const [loading, setLoading] = useState(false);
  const [minimumTrustedSources, setMinimumTrustedSources] = useState(2);
  const [recommendations, setRecommendations] = useState([]);
  const [status, setStatus] = useState('');
  const [summary, setSummary] = useState(null);
  const mountedRef = useMountedRef();
  const loadRequestIdRef = useRef(0);
  const actionRequestIdRef = useRef(0);
  const loadInFlightRef = useRef(false);
  const actionInFlightRef = useRef(false);
  const [actionLoading, setActionLoading] = useState(false);

  const loadRecommendations = async () => {
    if (!mountedRef.current || disabled || loadInFlightRef.current) return;
    const requestId = ++loadRequestIdRef.current;
    loadInFlightRef.current = true;
    setError('');
    setLoading(true);
    try {
      const response = await fetchTasteRecommendations({
        includeSoulseekRecommendations,
        includeSourceActors,
        limit: Number(limit) || 20,
        minimumTrustedSources: Number(minimumTrustedSources) || 2,
      });
      if (
        !mountedRef.current ||
        requestId !== loadRequestIdRef.current
      ) {
        return;
      }
      if (!isObject(response.data)) {
        throw new Error('Federated recommendations returned an invalid response');
      }
      const normalizedRecommendations = Array.isArray(response.data.recommendations)
        ? response.data.recommendations.map(normalizeRecommendation).filter(Boolean)
        : [];
      const normalizedSummary = normalizeSummary(response.data);
      setSummary(normalizedSummary);
      setRecommendations(normalizedRecommendations);
      setStatus(interfaceText('Privacy-filtered recommendations loaded: {count}.', {
        count: normalizedRecommendations.length,
      }));
    } catch (loadError) {
      if (
        mountedRef.current &&
        requestId === loadRequestIdRef.current
      ) {
        setError(
          toDisplayError(
            loadError,
            'Unable to load federated taste recommendations.',
          ),
        );
      }
    } finally {
      if (
        mountedRef.current &&
        requestId === loadRequestIdRef.current
      ) {
        setLoading(false);
      }
      loadInFlightRef.current = false;
    }
  };

  const runAction = async (operation, failureMessage) => {
    if (!mountedRef.current || disabled || actionInFlightRef.current) return;
    const requestId = ++actionRequestIdRef.current;
    actionInFlightRef.current = true;
    setActionLoading(true);
    try {
      await operation();
    } catch (actionError) {
      if (
        mountedRef.current &&
        requestId === actionRequestIdRef.current
      ) {
        toast.error(toDisplayError(actionError, failureMessage));
      }
    } finally {
      actionInFlightRef.current = false;
      if (
        mountedRef.current &&
        requestId === actionRequestIdRef.current
      ) {
        setActionLoading(false);
      }
    }
  };

  const promoteToWishlist = async (recommendation) => {
    if (!recommendation?.workRef || !isObject(recommendation.workRef)) return;
    return runAction(async () => {
      const response = await promoteTasteRecommendationToWishlist({
        note: 'Promoted from federated taste recommendation review.',
        workRef: recommendation.workRef,
      });
      if (mountedRef.current) {
        setStatus(responseMessage(
          response,
          interfaceText('Promoted {title} to Wishlist.', { title: getTitle(recommendation.workRef) }),
        ));
      }
    }, interfaceText('Unable to promote recommendation.'));
  };

  const subscribeRadar = async (recommendation) => {
    if (!recommendation?.workRef || !isObject(recommendation.workRef)) return;
    return runAction(async () => {
      const response = await subscribeTasteRecommendationReleaseRadar({
        scope: 'trusted',
        workRef: recommendation.workRef,
      });
      if (mountedRef.current) {
        setStatus(responseMessage(
          response,
          interfaceText('Subscribed {creator} to Release Radar.', { creator: getCreator(recommendation.workRef) }),
        ));
      }
    }, interfaceText('Unable to subscribe to Release Radar.'));
  };

  const previewGraph = async (recommendation) => {
    if (!recommendation?.workRef || !isObject(recommendation.workRef)) return;
    return runAction(async () => {
      const response = await previewTasteRecommendationGraph({
        workRef: recommendation.workRef,
      });
      const preview = normalizeGraphPreview(response.data);
      if (!preview) {
        throw new Error('Discovery Graph preview returned an invalid response');
      }
      if (mountedRef.current) {
        setGraphPreview(preview);
        setStatus(interfaceText('Discovery Graph previewed for {title}.', {
          title: getTitle(recommendation.workRef),
        }));
      }
    }, interfaceText('Unable to preview Discovery Graph.'));
  };

  if (disabled) {
    return (
      <Segment raised>
        <Header as="h4"><LocalizedText source={"Federated Taste Recommendations"} /></Header>
        <p><LocalizedText source={"Connect to the server to load privacy-filtered recommendations."} /></p>
      </Segment>
    );
  }

  return (
    <Segment
      loading={loading}
      raised
    >
      <Header as="h4"><LocalizedText source={"Federated Taste Recommendations"} /></Header>
      <Form>
        <Form.Group widths="equal">
          <Form.Input
            aria-label={interfaceText("Taste recommendation limit")}
            label={interfaceText("Limit")}
            min={1}
            onChange={(event) => setLimit(event.target.value)}
            type="number"
            value={limit}
           {...interfaceTextProps("Taste recommendation limit")}/>
          <Form.Input
            aria-label={interfaceText("Minimum trusted taste sources")}
            label={interfaceText("Minimum trusted sources")}
            min={1}
            onChange={(event) => setMinimumTrustedSources(event.target.value)}
            type="number"
            value={minimumTrustedSources}
           {...interfaceTextProps("Minimum trusted taste sources")}/>
          <Form.Field>
            <label><LocalizedText source={"Reveal source actors"} /></label>
            <Checkbox
              aria-label={interfaceText("Reveal federated recommendation source actors")}
              checked={includeSourceActors}
              onChange={(_event, data) => setIncludeSourceActors(data.checked)}
              toggle
             {...interfaceTextProps("Reveal federated recommendation source actors")}/>
          </Form.Field>
          <Form.Field>
            <label><LocalizedText source={"Include Soulseek native"} /></label>
            <Checkbox
              aria-label={interfaceText("Include Soulseek native recommendations")}
              checked={includeSoulseekRecommendations}
              onChange={(_event, data) => setIncludeSoulseekRecommendations(data.checked)}
              toggle
             {...interfaceTextProps("Include Soulseek native recommendations")}/>
          </Form.Field>
        </Form.Group>
        <Popup
          content={interfaceText("Load privacy-filtered recommendations from followed federated actors. Optionally include raw native Soulseek recommendation seeds.")}
          position="top center"
          trigger={
            <Button
              disabled={loading}
              loading={loading}
              onClick={loadRecommendations}
              primary
              type="button"
            >
              <Icon name="users" />
              <LocalizedText source={"Load Recommendations"} /></Button>
          }
         {...interfaceTextProps("Load privacy-filtered recommendations from followed federated actors. Optionally include raw native Soulseek recommendation seeds.")}/>
      </Form>
      {status && <Message compact size="mini">{status}</Message>}
      {error && <Message compact error size="mini">{String(error)}</Message>}
      {summary && (
        <div className="search-acquisition-profile-strip">
          <Label basic>
            <LocalizedText source={"Trusted actors"} /><Label.Detail>{summary.trustedActorCount}</Label.Detail>
          </Label>
          <Label basic>
            <LocalizedText source={"Candidates"} /><Label.Detail>{summary.candidateCount}</Label.Detail>
          </Label>
          <Label basic>
            <LocalizedText source={"Minimum sources"} /><Label.Detail>{summary.minimumTrustedSources}</Label.Detail>
          </Label>
        </div>
      )}
      {graphPreview && (
        <Message compact size="mini">
          <LocalizedText source={"Graph preview: {nodes} nodes, {edges} edges."} values={{ nodes: graphPreview.nodeCount, edges: graphPreview.edgeCount }} />
        </Message>
      )}
      <List divided relaxed>
        {recommendations.map((recommendation) => {
          const title = getTitle(recommendation.workRef);
          const creator = getCreator(recommendation.workRef);

          return (
            <List.Item key={recommendation.workRef?.id || `${creator}-${title}`}>
              <List.Icon name="user friends" />
              <List.Content>
                <List.Header>{[creator, title].filter(Boolean).join(' - ') || title}</List.Header>
                <List.Description>
                  {recommendation.trustedSourceCount} <LocalizedText source={"trusted sources · score"} />{" "}{Math.round((recommendation.score || 0) * 100)}%
                </List.Description>
                {(recommendation.reasons || []).map((reason) => (
                  <Label basic key={reason}>{reason}</Label>
                ))}
                {includeSourceActors && recommendation.sourceActors?.length > 0 && (
                  <div className="search-acquisition-profile-summary">
                    {recommendation.sourceActors.join(', ')}
                  </div>
                )}
                <Popup
                  content={interfaceText("Promote this WorkRef to Wishlist through the backend review handoff without starting a download.")}
                  position="top center"
                  trigger={
                    <Button
                      aria-label={interfaceText("Promote {title} taste recommendation to Wishlist", { "title": (title) })}
                      disabled={actionLoading}
                      onClick={() => promoteToWishlist(recommendation)}
                      size="mini"
                      type="button"
                     {...interfaceTextProps("Promote {title} taste recommendation to Wishlist")}>
                      <Icon name="heart" />
                      <LocalizedText source={"Wishlist"} /></Button>
                  }
                 {...interfaceTextProps("Promote this WorkRef to Wishlist through the backend review handoff without starting a download.")}/>
                <Popup
                  content={interfaceText("Subscribe this artist to Release Radar using trusted scope.")}
                  position="top center"
                  trigger={
                    <Button
                      aria-label={interfaceText("Subscribe {title} taste recommendation to Release Radar", { "title": (title) })}
                      disabled={actionLoading}
                      onClick={() => subscribeRadar(recommendation)}
                      size="mini"
                      type="button"
                     {...interfaceTextProps("Subscribe {title} taste recommendation to Release Radar")}>
                      <Icon name="rss" />
                      <LocalizedText source={"Radar"} /></Button>
                  }
                 {...interfaceTextProps("Subscribe this artist to Release Radar using trusted scope.")}/>
                <Popup
                  content={interfaceText("Preview nearby Discovery Graph evidence for this WorkRef.")}
                  position="top center"
                  trigger={
                    <Button
                      aria-label={interfaceText("Preview {title} taste recommendation graph", { "title": (title) })}
                      disabled={actionLoading}
                      onClick={() => previewGraph(recommendation)}
                      size="mini"
                      type="button"
                     {...interfaceTextProps("Preview {title} taste recommendation graph")}>
                      <Icon name="share alternate" />
                      <LocalizedText source={"Graph"} /></Button>
                  }
                 {...interfaceTextProps("Preview nearby Discovery Graph evidence for this WorkRef.")}/>
              </List.Content>
            </List.Item>
          );
        })}
      </List>
    </Segment>
  );
};

export default FederatedTasteRecommendationsPanel;
