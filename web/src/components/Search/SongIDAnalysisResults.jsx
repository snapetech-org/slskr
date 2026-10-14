import LocalizedText from "../Shared/LocalizedText";
import { interfaceText, interfaceTextProps, useInterfaceLanguage } from "../../lib/interfaceLocale";


import React from 'react';
import DiscoveryGraphCanvas from './DiscoveryGraphCanvas';
import SongIDEvidenceDetails from './SongIDEvidenceDetails';
import {
  getStatusColor,
  getRunTitle,
  getDedupedTracks,
  getDedupedOptions,
  getDedupedPlans,
  getUniqueTopActions,
  localizeSongIdRunState,
  detailStyle,
  detailSummaryStyle,
} from './songIdPanelHelpers';
import {
  Button,
  Divider,
  Header,
  Label,
  List,
  Popup,
  Progress,
  Grid,
  Segment,
} from 'semantic-ui-react';

const SongIDAnalysisResults = ({
  actionLoading,
  copyForensicMatrix,
  copyLoading,
  disabled,
  graphData,
  graphRequest,
  handleAlbumPrepare,
  handleDiscography,
  handleGraphRecenter,
  handleMbReleaseJob,
  handleMixSearch,
  handleOptionAction,
  handlePlanAction,
  handleTrackSearch,
  handleTrackSearchBatch,
  loading,
  openDiscoveryGraph,
  run,
  source,
}) => {
  useInterfaceLanguage();
  const renderScores = (item) => (
    <div style={{ marginTop: '0.35em' }}>
      <Label size="tiny"><LocalizedText source={"Identity"} />{" "}{Math.round((item.identityScore || 0) * 100)}</Label>
      <Label size="tiny"><LocalizedText source={"Byzantine"} />{" "}{Math.round((item.byzantineScore || 0) * 100)}</Label>
      {item.canonicalScore ? (
        <Label color="teal" size="tiny">
          <LocalizedText source={"Canonical"} />{" "}{Math.round((item.canonicalScore || 0) * 100)}
        </Label>
      ) : null}
      <Label color="blue" size="tiny">
        <LocalizedText source={"Action"} />{" "}{Math.round((item.actionScore || 0) * 100)}
      </Label>
    </div>
  );

  const tracks = getDedupedTracks(run?.tracks);
  const options = getDedupedOptions(run?.options);
  const plans = getDedupedPlans(run?.plans);
  const bestTrack = tracks[0];
  const bestAlbum = Array.isArray(run?.albums) ? run.albums[0] : null;
  const bestArtist = Array.isArray(run?.artists) ? run.artists[0] : null;
  const topActions = getUniqueTopActions([
    bestTrack ? {
      label: interfaceText("Search Best Track"),
      track: bestTrack,
      type: 'track',
    } : null,
    bestAlbum ? {
      album: bestAlbum,
      label: interfaceText("Download Best Album"),
      type: 'album',
    } : null,
    bestArtist ? {
      artist: bestArtist,
      label: interfaceText("Plan Best Artist"),
      type: 'artist',
    } : null,
    ...options.slice(0, 4).map((option) => ({
      label: option.actionLabel,
      option,
      type: 'option',
    })),
    ...plans.slice(0, 4).map((plan) => ({
      label: plan.actionLabel,
      plan,
      type: 'plan',
    })),
  ].filter(Boolean), 5);

  return (
        <Grid.Column width={11}>
      {run ? (
            <Segment
              className="songid-result-panel"
              secondary
            >
          <Header as="h5" style={{ marginTop: 0 }}>
            <LocalizedText source={"Result"} /></Header>
          <div style={{ marginBottom: '1em' }}>
            <Popup
              content={interfaceText("Open the Discovery Graph for this SongID run and move sideways through nearby tracks, albums, artists, and decomposed segments.")}
              position="top center"
              trigger={
                <Button
                  onClick={() =>
                    openDiscoveryGraph({
                      scope: 'songid_run',
                      songIdRunId: run?.id,
                      title: run?.query || run?.metadata?.title,
                    })
                  }
                  size="small"
                >
                  <LocalizedText source={"Open Discovery Graph"} /></Button>
              }
             {...interfaceTextProps("Open the Discovery Graph for this SongID run and move sideways through nearby tracks, albums, artists, and decomposed segments.")}/>
          </div>
                  <Segment className="songid-result-summary">
            <Header as="h4" style={{ marginTop: 0 }}>
              {bestTrack
                ? <LocalizedText source={"{artist} - {title}"} values={{ "artist": (bestTrack.artist), "title": (bestTrack.title) }} />
                : getRunTitle(run)}
            </Header>
            <div style={{ marginBottom: '0.75em' }}>
              <Label color={getStatusColor(run.status)} size="small">
                {localizeSongIdRunState(run.status)}
              </Label>
              <Label size="small">{localizeSongIdRunState(run.currentStage || 'queued')}</Label>
              <Label size="small">{run.sourceType || interfaceText('unknown')}</Label>
              {run.workerSlot !== null && run.workerSlot !== undefined ? (
                <Label size="small"><LocalizedText source={"Worker"} />{" "}{run.workerSlot}</Label>
              ) : null}
              {run.queuePosition !== null && run.queuePosition !== undefined ? (
                <Label size="small"><LocalizedText source={"Queue"} />{" "}{run.queuePosition}</Label>
              ) : null}
            </div>
            {run.summary ? <p>{run.summary}</p> : null}
            {run.query ? (
              <p style={{ marginBottom: 0 }}>
                <strong><LocalizedText source={"Query:"} /></strong> {run.query}
              </p>
            ) : null}
          </Segment>
          <Progress
            color={run.status === 'failed' ? 'red' : 'blue'}
            percent={Math.round((run.percentComplete || 0) * 100)}
            precision={0}
            progress
            size="small"
          >
            {localizeSongIdRunState(run.currentStage || 'queued')}
          </Progress>
          {topActions.length > 0 ? (
            <>
              <Header as="h5"><LocalizedText source={"Best Next Actions"} /></Header>
              <div style={{ marginBottom: '1em' }}>
                {topActions.map((action, index) => {
                  const content = {
                    album: 'Create a single-release job from the strongest album candidate.',
                    artist: 'Create a discography job from the strongest artist candidate.',
                    option: 'Run this ranked SongID acquisition option.',
                    plan: 'Run this ranked SongID plan.',
                    track: 'Start a regular slskr search using the strongest SongID track candidate.',
                  }[action.type];
                  const onClick = () => {
                    if (action.type === 'track') {
                      return handleTrackSearch(action.track);
                    }
                    if (action.type === 'album') {
                      return handleMbReleaseJob(action.album);
                    }
                    if (action.type === 'artist') {
                      return handleDiscography(action.artist);
                    }
                    if (action.type === 'option') {
                      return handleOptionAction(action.option);
                    }

                    return handlePlanAction(action.plan);
                  };

                  return (
                    <Popup
                      key={`${action.type}-${action.label}-${index}`}
                      content={interfaceText(content)}
                      position="top center"
                        trigger={
                          <Button
                            disabled={actionLoading}
                            onClick={onClick}
                            primary={index === 0}
                          size="small"
                          style={{ marginLeft: index === 0 ? 0 : '0.5em' }}
                        >
                          {action.label}
                        </Button>
                      }
                    />
                  );
                })}
              </div>
            </>
          ) : null}
          {graphData && graphRequest?.songIdRunId === run?.id ? (
            <>
              <Divider />
              <Header as="h5"><LocalizedText source={"Mini-map"} /></Header>
              <Segment secondary>
                <DiscoveryGraphCanvas
                  graph={graphData}
                  height={220}
                  onNodeClick={handleGraphRecenter}
                  width={520}
                />
              </Segment>
            </>
          ) : null}

          {Array.isArray(run.mixGroups) && run.mixGroups.length > 0 ? (
            <>
              <Header as="h5"><LocalizedText source={"Mix Clusters"} /></Header>
              <List divided relaxed>
                {run.mixGroups.map((mix) => (
                  <List.Item key={mix.mixId}>
                    <List.Content floated="right">
                      <Popup
                        content={interfaceText("Queue the mix cluster segments as a batch of SongID searches.")}
                        position="top center"
                        trigger={
                          <Button
                            disabled={actionLoading}
                            onClick={() => handleMixSearch(mix)}
                            size="small"
                          >
                            <LocalizedText source={"Search Mix"} /></Button>
                        }
                       {...interfaceTextProps("Queue the mix cluster segments as a batch of SongID searches.")}/>
                    </List.Content>
                    <List.Content>
                      <List.Header>{mix.label}</List.Header>
                      <List.Description>
                        {mix.segmentCount} <LocalizedText source={"segments · confidence"} />{" "}{Math.round((mix.confidence || 0) * 100)}
                      </List.Description>
                      <List.Description>
                        <LocalizedText source={"Identity"} />{" "}{Math.round((mix.identityScore || 0) * 100)} <LocalizedText source={"· Byzantine"} />{" "}{Math.round((mix.byzantineScore || 0) * 100)}
                      </List.Description>
                      {mix.searchText ? (
                        <List.Description>
                          <LocalizedText source={"Query:"} />{" "}{mix.searchText}
                        </List.Description>
                      ) : null}
                    </List.Content>
                  </List.Item>
                ))}
              </List>
            </>
          ) : null}

          <SongIDEvidenceDetails
            actionLoading={actionLoading}
            copyForensicMatrix={copyForensicMatrix}
            copyLoading={copyLoading}
            handleOptionAction={handleOptionAction}
            handleTrackSearchBatch={handleTrackSearchBatch}
            options={options}
            run={run}
          />
          {plans.length > 0 ? (
            <details style={detailStyle}>
              <summary style={detailSummaryStyle}>
                <LocalizedText source={"Ranked Plans ("} />{plans.length})
              </summary>
              <List divided relaxed>
                {plans.map((plan) => (
                  <List.Item key={plan.planId}>
                    <List.Content floated="right">
                      <Popup
                        content={interfaceText("Run the highest-value SongID action path for this candidate using the current scored plan.")}
                        position="top center"
                        trigger={
                          <Button
                            disabled={actionLoading}
                            onClick={() => handlePlanAction(plan)}
                            size="small"
                          >
                            {plan.actionLabel}
                          </Button>
                        }
                       {...interfaceTextProps("Run the highest-value SongID action path for this candidate using the current scored plan.")}/>
                    </List.Content>
                    <List.Content>
                      <List.Header>
                        {plan.title}{' '}
                        {plan.duplicateCount > 1 ? (
                          <Label color="grey" size="tiny">
                            {plan.duplicateCount} <LocalizedText source={"matches"} /></Label>
                        ) : null}
                      </List.Header>
                      <List.Description>{plan.subtitle}</List.Description>
                      {renderScores(plan)}
                    </List.Content>
                  </List.Item>
                ))}
              </List>
            </details>
          ) : null}

          {tracks.length > 0 ? (
            <>
              <Header as="h5"><LocalizedText source={"Tracks"} /></Header>
              <List divided relaxed>
                {tracks.map((candidate) => (
                  <List.Item key={candidate.candidateId}>
                    <List.Content floated="right">
                      <Popup
                        content={interfaceText("Start a regular slskr search using this SongID track candidate so you can inspect sources and begin downloading.")}
                        position="top center"
                        trigger={
                          <Button
                            disabled={actionLoading}
                            onClick={() => handleTrackSearch(candidate)}
                            size="small"
                          >
                            <LocalizedText source={"Search Song"} /></Button>
                        }
                       {...interfaceTextProps("Start a regular slskr search using this SongID track candidate so you can inspect sources and begin downloading.")}/>
                      <Popup
                        content={interfaceText("Open the Discovery Graph around this track candidate and explore nearby identities, ambiguity branches, and adjacent context.")}
                        position="top center"
                        trigger={
                          <Button
                            onClick={() =>
                              openDiscoveryGraph({
                                scope: 'track',
                                songIdRunId: run?.id,
                                recordingId: candidate.recordingId,
                                title: candidate.title,
                                artist: candidate.artist,
                              })
                            }
                            size="small"
                            style={{ marginLeft: '0.5em' }}
                          >
                            <LocalizedText source={"Graph"} /></Button>
                        }
                       {...interfaceTextProps("Open the Discovery Graph around this track candidate and explore nearby identities, ambiguity branches, and adjacent context.")}/>
                    </List.Content>
                    <List.Content>
                      <List.Header>
                        {candidate.artist} - {candidate.title}{' '}
                        {candidate.isExact ? (
                          <Label color="green" size="tiny">
                            <LocalizedText source={"exact"} /></Label>
                        ) : null}
                        {candidate.duplicateCount > 1 ? (
                          <Label color="grey" size="tiny">
                            {candidate.duplicateCount} <LocalizedText source={"matches"} /></Label>
                        ) : null}
                      </List.Header>
                      <List.Description>{candidate.recordingId}</List.Description>
                      {candidate.canonicalVariantCount ? (
                        <List.Description style={{ marginTop: '0.35em' }}>
                          <LocalizedText source={"Canonical variants:"} />{" "}{candidate.canonicalVariantCount}
                          {candidate.hasLosslessCanonical ? <LocalizedText source={"· lossless available"} /> : ''}
                        </List.Description>
                      ) : null}
                      {renderScores(candidate)}
                    </List.Content>
                  </List.Item>
                ))}
              </List>
            </>
          ) : null}

          {Array.isArray(run.albums) && run.albums.length > 0 ? (
            <>
              <Header as="h5"><LocalizedText source={"Albums"} /></Header>
              <List divided relaxed>
                {run.albums.map((candidate) => (
                  <List.Item key={candidate.candidateId}>
                    <List.Content floated="right">
                      <Button.Group size="small">
                        <Popup
                          content={interfaceText("Resolve and cache this MusicBrainz release in slskr so album completion and downstream download workflows can use it.")}
                          position="top center"
                          trigger={
                            <Button
                              disabled={actionLoading}
                              onClick={() => handleAlbumPrepare(candidate)}
                            >
                              <LocalizedText source={"Prepare Album"} /></Button>
                          }
                         {...interfaceTextProps("Resolve and cache this MusicBrainz release in slskr so album completion and downstream download workflows can use it.")}/>
                        <Popup
                          content={interfaceText("Create a single-release job from this SongID album candidate so slskr can plan album acquisition directly.")}
                          position="top center"
                          trigger={
                            <Button
                              disabled={actionLoading}
                              onClick={() => handleMbReleaseJob(candidate)}
                            >
                              <LocalizedText source={"Download Album"} /></Button>
                          }
                         {...interfaceTextProps("Create a single-release job from this SongID album candidate so slskr can plan album acquisition directly.")}/>
                        <Popup
                          content={interfaceText("Open the Discovery Graph around this album candidate to explore adjacent tracks, artist context, and nearby branches.")}
                          position="top center"
                          trigger={
                            <Button
                              onClick={() =>
                                openDiscoveryGraph({
                                  scope: 'album',
                                  songIdRunId: run?.id,
                                  releaseId: candidate.releaseId,
                                  album: candidate.title,
                                  artist: candidate.artist,
                                })
                              }
                            >
                              <LocalizedText source={"Graph"} /></Button>
                          }
                         {...interfaceTextProps("Open the Discovery Graph around this album candidate to explore adjacent tracks, artist context, and nearby branches.")}/>
                      </Button.Group>
                    </List.Content>
                    <List.Content>
                      <List.Header>
                        {candidate.artist} - {candidate.title}{' '}
                        {candidate.isExact ? (
                          <Label color="green" size="tiny">
                            <LocalizedText source={"exact"} /></Label>
                        ) : null}
                      </List.Header>
                      <List.Description>
                        {candidate.trackCount} <LocalizedText source={"track(s) ·"} />{" "}{candidate.releaseId}
                      </List.Description>
                      {candidate.canonicalSupportCount ? (
                        <List.Description style={{ marginTop: '0.35em' }}>
                          <LocalizedText source={"Canonical support from"} />{" "}{candidate.canonicalSupportCount} <LocalizedText source={"track candidate(s)"} /></List.Description>
                      ) : null}
                      {renderScores(candidate)}
                    </List.Content>
                  </List.Item>
                ))}
              </List>
            </>
          ) : null}

          {Array.isArray(run.artists) && run.artists.length > 0 ? (
            <>
              <Header as="h5"><LocalizedText source={"Artists"} /></Header>
              <List divided relaxed>
                {run.artists.map((candidate) => (
                  <List.Item key={candidate.candidateId}>
                    <List.Content floated="right">
                      <Popup
                        content={interfaceText("Create a discography job from this SongID artist candidate so slskr can plan a catalog-scale acquisition workflow.")}
                        position="top center"
                        trigger={
                          <Button
                            disabled={actionLoading}
                            onClick={() => handleDiscography(candidate)}
                            size="small"
                          >
                            <LocalizedText source={"Plan Discography"} /></Button>
                        }
                       {...interfaceTextProps("Create a discography job from this SongID artist candidate so slskr can plan a catalog-scale acquisition workflow.")}/>
                      <Popup
                        content={interfaceText("Open the Discovery Graph around this artist candidate and branch into nearby artists, releases, and SongID context.")}
                        position="top center"
                        trigger={
                          <Button
                            onClick={() =>
                              openDiscoveryGraph({
                                scope: 'artist',
                                songIdRunId: run?.id,
                                artistId: candidate.artistId,
                                artist: candidate.name,
                              })
                            }
                            size="small"
                            style={{ marginLeft: '0.5em' }}
                          >
                            <LocalizedText source={"Graph"} /></Button>
                        }
                       {...interfaceTextProps("Open the Discovery Graph around this artist candidate and branch into nearby artists, releases, and SongID context.")}/>
                    </List.Content>
                    <List.Content>
                      <List.Header>{candidate.name}</List.Header>
                      <List.Description>
                        {candidate.releaseGroupCount} <LocalizedText source={"release group(s) ·"} />{' '}
                        {candidate.artistId}
                      </List.Description>
                      {candidate.canonicalSupportCount ? (
                        <List.Description style={{ marginTop: '0.35em' }}>
                          <LocalizedText source={"Canonical support from"} />{" "}{candidate.canonicalSupportCount} <LocalizedText source={"track candidate(s)"} /></List.Description>
                      ) : null}
                      {renderScores(candidate)}
                    </List.Content>
                  </List.Item>
                ))}
              </List>
            </>
          ) : null}
        </Segment>
      ) : null}
        </Grid.Column>
  );
};

export default SongIDAnalysisResults;
