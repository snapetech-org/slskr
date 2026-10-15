import LocalizedText from "../Shared/LocalizedText";
import { interfaceText, interfaceTextProps, useInterfaceLanguage } from "../../lib/interfaceLocale";
import * as discoveryGraph from '../../lib/discoveryGraph';
import { useMountedRef } from '../../lib/useMountedRef';
import * as searches from '../../lib/searches';
import { toDisplayError } from '../../lib/errors';
import { formatRegionalFixedNumber, formatRegionalNumber, useRegionalFormat } from '../../lib/util';
import { resolveTarget } from '../../lib/musicBrainz';
import React, { useMemo, useRef, useState } from 'react';
import { toast } from 'react-toastify';
import {
  Button,
  Form,
  Header,
  Input,
  List,
  Popup,
  Segment,
} from 'semantic-ui-react';
import DiscoveryGraphModal from './DiscoveryGraphModal';

const isObject = (value) =>
  value !== null && typeof value === 'object' && !Array.isArray(value);

const normalizeResolvedTarget = (data) => {
  if (!isObject(data)) {
    return null;
  }

  if (isObject(data.album)) {
    return {
      album: {
        ...data.album,
        artist: typeof data.album.artist === 'string' ? data.album.artist : '',
        title: typeof data.album.title === 'string' && data.album.title ? data.album.title : null,
        tracks: Array.isArray(data.album.tracks)
          ? data.album.tracks.filter((track) => isObject(track))
          : [],
      },
    };
  }

  if (isObject(data.track)) {
    return {
      track: {
        ...data.track,
        artist: typeof data.track.artist === 'string' ? data.track.artist : '',
        title: typeof data.track.title === 'string' && data.track.title ? data.track.title : null,
        duration: typeof data.track.duration === 'number' ? data.track.duration : 0,
      },
    };
  }

  return null;
};

const MusicBrainzLookup = ({ disabled }) => {
  useInterfaceLanguage();
  const regionalFormat = useRegionalFormat();
  const [releaseInput, setReleaseInput] = useState('');
  const [recordingInput, setRecordingInput] = useState('');
  const [discogsInput, setDiscogsInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [target, setTarget] = useState(null);
  const [graphLoading, setGraphLoading] = useState(false);
  const [graphOpen, setGraphOpen] = useState(false);
  const [graphData, setGraphData] = useState(null);
  const [graphRequest, setGraphRequest] = useState(null);
  const mountedRef = useMountedRef();
  const lookupRequestIdRef = useRef(0);
  const graphRequestIdRef = useRef(0);
  const queueInFlightRef = useRef(false);
  const [queueLoading, setQueueLoading] = useState(false);

  const openDiscoveryGraph = async (request) => {
    if (!mountedRef.current || disabled || graphLoading) return;
    const requestId = ++graphRequestIdRef.current;
    setGraphLoading(true);
    setGraphOpen(true);
    setGraphData(null);
    setGraphRequest(request);

    try {
      const graph = await discoveryGraph.buildDiscoveryGraph(request);
      if (
        !mountedRef.current ||
        requestId !== graphRequestIdRef.current
      ) {
        return;
      }
      setGraphData(graph);
    } catch (error) {
      console.error(error);
      if (
        mountedRef.current &&
        requestId === graphRequestIdRef.current
      ) {
        toast.error(toDisplayError(error, 'Failed to build discovery graph'));
        setGraphOpen(false);
      }
    } finally {
      if (
        mountedRef.current &&
        requestId === graphRequestIdRef.current
      ) {
        setGraphLoading(false);
      }
    }
  };

  const handleLookup = async () => {
    if (!mountedRef.current || disabled || loading) return;
    const payload = {
      discogsReleaseId: typeof discogsInput === 'string' ? discogsInput.trim() || undefined : undefined,
      recordingId: typeof recordingInput === 'string' ? recordingInput.trim() || undefined : undefined,
      releaseId: typeof releaseInput === 'string' ? releaseInput.trim() || undefined : undefined,
    };
    if (!payload.releaseId && !payload.recordingId && !payload.discogsReleaseId) {
      toast.error(interfaceText("Provide at least one MusicBrainz or Discogs identifier"));
      return;
    }

    const requestId = ++lookupRequestIdRef.current;
    setLoading(true);

    try {
      const response = await resolveTarget(payload);
      const resolvedTarget = normalizeResolvedTarget(response.data);
      if (!resolvedTarget) {
        throw new Error('MusicBrainz target response did not include a target');
      }

      if (
        !mountedRef.current ||
        requestId !== lookupRequestIdRef.current
      ) {
        return;
      }
      setTarget(resolvedTarget);

      toast.success(resolvedTarget.album
        ? interfaceText('Loaded album {title}', { title: resolvedTarget.album.title })
        : interfaceText('Loaded track {title}', { title: resolvedTarget.track?.title || '' }));
    } catch (error) {
      console.error(error);
      if (
        mountedRef.current &&
        requestId === lookupRequestIdRef.current
      ) {
        toast.error(toDisplayError(error, 'Failed to resolve target'));
      }
    } finally {
      if (
        mountedRef.current &&
        requestId === lookupRequestIdRef.current
      ) {
        setLoading(false);
      }
    }
  };

  const summary = useMemo(() => {
    if (!target) {
      return null;
    }

    if (target.album) {
      return (
        <List>
          <List.Item>
            <List.Header><LocalizedText source={"Album"} /></List.Header>
            <List.Description>
              {target.album.title || <LocalizedText source={"Untitled album"} />} · {target.album.artist} ·{' '}
              {formatRegionalNumber(target.album.tracks?.length ?? 0)} <LocalizedText source={"tracks"} /></List.Description>
          </List.Item>
        </List>
      );
    }

    if (target.track) {
      return (
        <List>
          <List.Item>
            <List.Header><LocalizedText source={"Track"} /></List.Header>
            <List.Description>
              {target.track.title || <LocalizedText source={"Untitled track"} />} · {target.track.artist} ·{' '}
              {target.track.duration
                ? `${formatRegionalFixedNumber(target.track.duration / 60_000, 2)} min`
                : <LocalizedText source={"unknown length"} />}
            </List.Description>
          </List.Item>
        </List>
      );
    }

    return null;
  }, [regionalFormat, target]);

  const handleOpenGraph = async () => {
    if (target?.album?.musicBrainzReleaseId) {
      await openDiscoveryGraph({
        scope: 'album',
        releaseId: target.album.musicBrainzReleaseId,
        album: target.album.title || interfaceText('Untitled album'),
        artist: target.album.artist,
      });
      return;
    }

    if (target?.track?.musicBrainzRecordingId) {
      await openDiscoveryGraph({
        scope: 'track',
        recordingId: target.track.musicBrainzRecordingId,
        title: target.track.title || interfaceText('Untitled track'),
        artist: target.track.artist,
      });
    }
  };

  const handleGraphRecenter = async (nodeId) => {
    if (!nodeId) {
      return;
    }

    const [nodeType, rawId] = nodeId.split(':');
    if (nodeType === 'artist') {
      await openDiscoveryGraph({ scope: 'artist', artistId: rawId });
      return;
    }

    if (nodeType === 'album' || nodeType === 'release-group') {
      await openDiscoveryGraph({ scope: 'album', releaseId: rawId });
      return;
    }

    if (nodeType === 'track') {
      await openDiscoveryGraph({ scope: 'track', recordingId: rawId });
    }
  };

  const handleGraphCompare = async (nodeId, label) => {
    if (!graphRequest || !nodeId) {
      return;
    }

    await openDiscoveryGraph({
      ...graphRequest,
      compareLabel: label,
      compareNodeId: nodeId,
    });
  };

  const handleQueueNearby = async (graph) => {
    if (!mountedRef.current || disabled || queueInFlightRef.current) return;
    const queries = (Array.isArray(graph?.nodes) ? graph.nodes : [])
      .filter((node) => isObject(node) && node.nodeType === 'track')
      .map((node) => (typeof node.label === 'string' ? node.label.trim() : ''))
      .filter(Boolean)
      .slice(0, 8);

    if (queries.length === 0) {
      toast.error(interfaceText("No nearby track nodes were available to queue"));
      return;
    }

    queueInFlightRef.current = true;
    setQueueLoading(true);
    try {
      const count = await searches.createBatch({ queries });
      if (mountedRef.current) {
        const startedCount = typeof count === 'number'
          ? count
          : typeof count?.count === 'number'
            ? count.count
            : queries.length;
        toast.success(interfaceText("Started {startedCount} nearby graph searches", { "startedCount": (startedCount) }));
      }
    } catch (error) {
      console.error(error);
      if (mountedRef.current) {
        toast.error(toDisplayError(error, 'Failed to queue nearby searches'));
      }
    } finally {
      queueInFlightRef.current = false;
      if (mountedRef.current) setQueueLoading(false);
    }
  };

  return (
    <>
      <Segment
        className="musicbrainz-lookup-segment"
        raised
      >
        <Header as="h4"><LocalizedText source={"MusicBrainz / Discogs Lookup"} /></Header>
        <Form>
          <Form.Field>
            <Input
              disabled={disabled || loading}
              label={interfaceText("MusicBrainz Release ID")}
              onChange={(event) => setReleaseInput(event.target.value)}
              placeholder={interfaceText("e.g. 1c3b3668-...")}
              value={releaseInput}
             {...interfaceTextProps("MusicBrainz Release ID")}/>
          </Form.Field>
          <Form.Field>
            <Input
              disabled={disabled || loading}
              label={interfaceText("MusicBrainz Recording ID")}
              onChange={(event) => setRecordingInput(event.target.value)}
              placeholder={interfaceText("e.g. 8af4c1b9-...")}
              value={recordingInput}
             {...interfaceTextProps("MusicBrainz Recording ID")}/>
          </Form.Field>
          <Form.Field>
            <Input
              disabled={disabled || loading}
              label={interfaceText("Discogs Release/Master ID")}
              onChange={(event) => setDiscogsInput(event.target.value)}
              placeholder={interfaceText("e.g. 123456")}
              value={discogsInput}
             {...interfaceTextProps("Discogs Release/Master ID")}/>
          </Form.Field>
          <Popup
            content={interfaceText("Resolve a canonical MusicBrainz or Discogs target when you already know an identifier and want exact metadata.")}
            position="top center"
            trigger={
              <Button
                disabled={disabled || loading}
                loading={loading}
                onClick={handleLookup}
                primary
              >
                <LocalizedText source={"Resolve target"} /></Button>
            }
           {...interfaceTextProps("Resolve a canonical MusicBrainz or Discogs target when you already know an identifier and want exact metadata.")}/>
          <Popup
            content={interfaceText("Open the Discovery Graph around the resolved MusicBrainz target to branch into nearby releases, tracks, and artists.")}
            position="top center"
            trigger={
            <Button
                disabled={!target || graphLoading}
                onClick={handleOpenGraph}
                style={{ marginLeft: '0.5em' }}
              >
                <LocalizedText source={"Graph"} /></Button>
            }
           {...interfaceTextProps("Open the Discovery Graph around the resolved MusicBrainz target to branch into nearby releases, tracks, and artists.")}/>
          <Popup
            content={interfaceText("Open the same canonical target as a wider atlas-style discovery surface for neighborhood browsing.")}
            position="top center"
            trigger={
            <Button
                disabled={!target || graphLoading}
                onClick={handleOpenGraph}
                style={{ marginLeft: '0.5em' }}
              >
                <LocalizedText source={"Atlas"} /></Button>
            }
           {...interfaceTextProps("Open the same canonical target as a wider atlas-style discovery surface for neighborhood browsing.")}/>
        </Form>
        {summary}
      </Segment>
      <DiscoveryGraphModal
        graph={graphData}
        loading={graphLoading}
        onClose={() => {
          graphRequestIdRef.current += 1;
          setGraphOpen(false);
          setGraphLoading(false);
        }}
        onCompare={handleGraphCompare}
        onQueueNearby={handleQueueNearby}
        onRecenter={handleGraphRecenter}
        onRestoreBranch={(branch) => branch?.request && openDiscoveryGraph(branch.request)}
        open={graphOpen}
      />
    </>
  );
};

export default MusicBrainzLookup;
