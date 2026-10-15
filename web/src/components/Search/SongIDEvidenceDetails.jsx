import LocalizedText from "../Shared/LocalizedText";
import { interfaceText, interfaceTextProps, useInterfaceLanguage } from "../../lib/interfaceLocale";
import { LocalizedPopup } from '../Shared/TooltipButton';
import { formatRegionalNumber, useRegionalFormat } from '../../lib/util';


import React from 'react';
import {
  Button,
  Header,
  Label,
  List,
  Popup,
} from 'semantic-ui-react';
import {
  detailStyle,
  detailSummaryStyle,
  formatPercent,
  getIdentityVerdictColor,
  getSyntheticVerdictColor,
  hasScorecardSignal,
} from './songIdPanelHelpers';

const localizeKnownValue = (value, labels) => (
  Object.prototype.hasOwnProperty.call(labels, value)
    ? interfaceText(labels[value])
    : value
);

const identityVerdictLabels = {
  candidate_identity: 'Candidate identity',
  candidate_match_found: 'Candidate match found',
  matched: 'Matched',
  needs_manual_review: 'Needs manual review',
  recognized_cataloged_track: 'Recognized catalog track',
  strong_identity: 'Strong identity',
  unclassified: 'Unclassified',
  weak_identity: 'Weak identity',
};

const syntheticVerdictLabels = {
  insufficient_evidence: 'Insufficient evidence',
  low_signal: 'Low signal',
  moderate_suspicion: 'Moderate suspicion',
  mixed_or_inconclusive: 'Mixed or inconclusive',
  strong_suspicion: 'Strong suspicion',
  unlikely: 'Unlikely',
};

const SongIDEvidenceDetails = ({
  actionLoading,
  copyForensicMatrix,
  copyLoading,
  handleOptionAction,
  handleTrackSearchBatch,
  options,
  run,
}) => {
  useInterfaceLanguage();
  useRegionalFormat();
  const formatPercent = (value) =>
    formatRegionalNumber(Math.round((Number(value) || 0) * 100));
  const renderOptionScores = (item) => (
    <div style={{ marginTop: '0.35em' }}>
      <Label color="blue" size="tiny">
        <LocalizedText source={"Overall"} />{" "}{formatPercent(item.overallScore)}
      </Label>
      <Label size="tiny"><LocalizedText source={"Quality"} />{" "}{formatPercent(item.qualityScore)}</Label>
      <Label size="tiny"><LocalizedText source={"Byzantine"} />{" "}{formatPercent(item.byzantineScore)}</Label>
      <Label size="tiny"><LocalizedText source={"Ready"} />{" "}{formatPercent(item.readinessScore)}</Label>
    </div>
  );

  const renderSyntheticPopupContent = () => {
    if (!run?.forensicMatrix) {
      return run?.syntheticAssessment?.summary || interfaceText('No synthetic detail available.');
    }

    const matrix = run.forensicMatrix;
    return (
      <div style={{ maxWidth: 360 }}>
        <div>
          <LocalizedText source={"Synthetic score"} />{" "}{matrix.syntheticScore || 0} <LocalizedText source={"· confidence"} />{' '}
          {matrix.confidenceScore || 0} <LocalizedText source={"· family"} />{" "}{matrix.familyLabel || interfaceText('none')}
        </div>
        {Array.isArray(matrix.topEvidenceFor) && matrix.topEvidenceFor.length > 0 ? (
          <div style={{ marginTop: '0.5em' }}>
            <LocalizedText source={"For:"} />{" "}{matrix.topEvidenceFor.slice(0, 3).join(' | ')}
          </div>
        ) : null}
        {Array.isArray(matrix.topEvidenceAgainst) &&
        matrix.topEvidenceAgainst.length > 0 ? (
          <div style={{ marginTop: '0.5em' }}>
            <LocalizedText source={"Against:"} />{" "}{matrix.topEvidenceAgainst.slice(0, 3).join(' | ')}
          </div>
        ) : null}
        {Array.isArray(matrix.notes) && matrix.notes.length > 0 ? (
          <div style={{ marginTop: '0.5em' }}>
            <LocalizedText source={"Notes:"} />{" "}{matrix.notes.slice(0, 4).join(' | ')}
          </div>
        ) : null}
      </div>
    );
  };

  const renderLane = (label, lane) => {
    if (!lane) {
      return null;
    }

    const metricSummary = Object.entries(lane.metrics || {})
      .slice(0, 5)
      .map(([key, value]) => `${key}: ${value}`)
      .join(' | ');

    return (
      <Popup
        key={label}
        content={
          <div style={{ maxWidth: 360 }}>
            <div>{lane.summary || interfaceText('No lane summary.')}</div>
            {metricSummary ? (
              <div style={{ marginTop: '0.5em' }}>{metricSummary}</div>
            ) : null}
          </div>
        }
        position="top left"
        trigger={
          <Label size="tiny">
            <LocalizedText source={label} /> {formatPercent(lane.score)}
          </Label>
        }
      />
    );
  };

  const identityVerdict = run?.identityAssessment?.verdict || run?.assessment?.verdict;
  const identityConfidence = (run?.identityAssessment?.confidence ?? run?.assessment?.confidence) || 0;
  const identitySummary = run?.identityAssessment?.summary || run?.assessment?.summary;
  const showIdentity = Boolean(identitySummary || identityConfidence > 0 || (identityVerdict && identityVerdict !== 'unclassified'));
  const showSynthetic = Boolean(
    run?.syntheticAssessment?.summary ||
    (run?.syntheticAssessment?.verdict && run.syntheticAssessment.verdict !== 'insufficient_evidence') ||
    run?.forensicMatrix?.familyLabel ||
    hasScorecardSignal(run?.scorecard),
  );

  return (
    <>
          {showIdentity ? (
            <>
              <Header as="h5"><LocalizedText source={"Identity"} /></Header>
              <p>
                <strong><LocalizedText source={"Verdict:"} /></strong>{' '}
                <Label
                  color={getIdentityVerdictColor(identityVerdict)}
                  size="tiny"
                >
                  {identityVerdict
                    ? localizeKnownValue(identityVerdict, identityVerdictLabels)
                    : interfaceText('unclassified')}
                </Label>
                <br />
                <strong><LocalizedText source={"Confidence:"} /></strong> {formatPercent(identityConfidence)}
                <br />
                <strong><LocalizedText source={"Reasoning:"} /></strong> {identitySummary || interfaceText('None')}
              </p>
            </>
          ) : null}

          {showSynthetic ? (
            <>
              <Header as="h5"><LocalizedText source={"Synthetic Signals"} /></Header>
              <div style={{ marginBottom: '1em' }}>
                <Popup
                  content={renderSyntheticPopupContent()}
                  position="top left"
                  trigger={
                    <Label
                      color={getSyntheticVerdictColor(
                        run.syntheticAssessment?.verdict,
                      )}
                      size="tiny"
                    >
                      <LocalizedText source={"Synthetic"} />{" "}{run.syntheticAssessment?.verdict
                        ? localizeKnownValue(run.syntheticAssessment.verdict, syntheticVerdictLabels)
                        : interfaceText('unknown')}
                    </Label>
                  }
                />
                <Popup
                  content={interfaceText("Confidence applies to the synthetic-likelihood readout only. It does not control download decisions when identity is strong.")}
                  position="top left"
                  trigger={
                    <Label size="tiny">
                      <LocalizedText source={"Confidence"} />{' '}
                      {formatRegionalNumber(run.forensicMatrix?.confidenceScore ||
                        run.syntheticAssessment?.confidence) || interfaceText('low')}
                    </Label>
                  }
                 {...interfaceTextProps("Confidence applies to the synthetic-likelihood readout only. It does not control download decisions when identity is strong.")}/>
                {run.forensicMatrix?.familyLabel ? (
                  <LocalizedPopup
                    content="Known-family score {score}. This is a hint lane, not a download-control signal."
                    parameters={{ score: run.forensicMatrix.knownFamilyScore || 0 }}
                    position="top left"
                    trigger={
                      <Label size="tiny">
                        <LocalizedText source={"Family"} />{" "}{run.forensicMatrix.familyLabel}
                      </Label>
                    }
                  />
                ) : null}
                {run.forensicMatrix?.qualityClass ? (
                  <Label size="tiny">
                    <LocalizedText source={"Quality"} />{" "}{run.forensicMatrix.qualityClass}
                  </Label>
                ) : null}
                {run.forensicMatrix?.perturbationStability !== undefined ? (
                  <Label size="tiny">
                    <LocalizedText source={"Stability"} />{' '}
                    {formatPercent(run.forensicMatrix.perturbationStability)}
                  </Label>
                ) : null}
              </div>
              {run.syntheticAssessment?.summary ? (
                <p style={{ marginTop: 0 }}>
                  {run.syntheticAssessment.summary}
                </p>
              ) : null}
              <div style={{ marginBottom: '1em' }}>
                {renderLane('Provenance', run.forensicMatrix?.provenanceLane)}
                {renderLane('Spectral', run.forensicMatrix?.spectralArtifactLane)}
                {renderLane('Descriptor', run.forensicMatrix?.descriptorPriorsLane)}
                {renderLane('Lyrics', run.forensicMatrix?.lyricsSpeechLane)}
                {renderLane('Structure', run.forensicMatrix?.structuralLane)}
                {renderLane('Family', run.forensicMatrix?.generatorFamilyLane)}
              </div>
            </>
          ) : null}

          {hasScorecardSignal(run.scorecard) ? (
            <details style={detailStyle}>
              <summary style={detailSummaryStyle}><LocalizedText source={"Scorecard"} /></summary>
              <div style={{ marginBottom: '1em' }}>
                <Label size="tiny"><LocalizedText source={"Audio"} />{" "}{run.scorecard.analysisAudioSource || interfaceText('none')}</Label>
                <Label size="tiny"><LocalizedText source={"Clips"} />{" "}{formatRegionalNumber(run.scorecard.clipCount || 0)}</Label>
                <Label size="tiny"><LocalizedText source={"AcoustID"} />{" "}{formatRegionalNumber(run.scorecard.acoustIdHitCount || 0)}</Label>
                <Label size="tiny"><LocalizedText source={"AcoustID Raw"} />{" "}{formatRegionalNumber(run.scorecard.rawAcoustIdHitCount || 0)}</Label>
                <Label size="tiny"><LocalizedText source={"SongRec"} />{" "}{formatRegionalNumber(run.scorecard.songRecHitCount || 0)}</Label>
                <Label size="tiny"><LocalizedText source={"SongRec Distinct"} />{" "}{formatRegionalNumber(run.scorecard.songRecDistinctMatchCount || 0)}</Label>
                <Label size="tiny"><LocalizedText source={"Transcript"} />{" "}{formatRegionalNumber(run.scorecard.transcriptCount || 0)}</Label>
                <Label size="tiny">OCR {formatRegionalNumber(run.scorecard.ocrCount || 0)}</Label>
                <Label size="tiny"><LocalizedText source={"Comments"} />{" "}{formatRegionalNumber(run.scorecard.commentFindingCount || 0)}</Label>
                <Label size="tiny"><LocalizedText source={"Timestamps"} />{" "}{formatRegionalNumber(run.scorecard.timestampHintCount || 0)}</Label>
                <Label size="tiny"><LocalizedText source={"Chapters"} />{" "}{formatRegionalNumber(run.scorecard.chapterHintCount || 0)}</Label>
                <Label size="tiny"><LocalizedText source={"Playlist Requests"} />{" "}{formatRegionalNumber(run.scorecard.playlistRequestCount || 0)}</Label>
                <Label size="tiny"><LocalizedText source={"AI Mentions"} />{" "}{formatRegionalNumber(run.scorecard.aiCommentMentionCount || 0)}</Label>
                <Label size="tiny"><LocalizedText source={"Panako"} />{" "}{formatRegionalNumber(run.scorecard.panakoHitCount || 0)}</Label>
                <Label size="tiny"><LocalizedText source={"Audfprint"} />{" "}{formatRegionalNumber(run.scorecard.audfprintHitCount || 0)}</Label>
                <Label size="tiny"><LocalizedText source={"Corpus"} />{" "}{formatRegionalNumber(run.scorecard.corpusMatchCount || 0)}</Label>
                <Label size="tiny">
                  <LocalizedText source={"Provenance"} />{" "}{formatRegionalNumber(run.scorecard.provenanceSignalCount || 0)}
                </Label>
                <Label size="tiny">
                  <LocalizedText source={"AI Heuristics"} />{" "}{formatRegionalNumber(run.scorecard.aiArtifactClipCount || 0)}
                </Label>
              </div>
              {Array.isArray(run.scorecard.embeddedMetadataKeys) &&
              run.scorecard.embeddedMetadataKeys.length > 0 ? (
                <div style={{ marginBottom: '1em' }}>
                  <strong><LocalizedText source={"Metadata Keys:"} /></strong>{' '}
                  {run.scorecard.embeddedMetadataKeys.join(', ')}
                </div>
              ) : null}
              {Array.isArray(run.scorecard.provenanceSignals) &&
              run.scorecard.provenanceSignals.length > 0 ? (
                <div style={{ marginBottom: '1em' }}>
                  <strong><LocalizedText source={"Provenance Signals:"} /></strong>{' '}
                  {run.scorecard.provenanceSignals.join(', ')}
                </div>
              ) : null}
            </details>
          ) : null}

          {run.fullSourceFingerprint ? (
            <details style={detailStyle}>
              <summary style={detailSummaryStyle}><LocalizedText source={"Full-Source Fingerprint"} /></summary>
              <p>
                <strong><LocalizedText source={"Duration:"} /></strong>{' '}
                {formatRegionalNumber(Math.round(run.fullSourceFingerprint.durationSeconds || 0))} s<br />
                <strong><LocalizedText source={"Fingerprint Length:"} /></strong>{' '}
                {formatRegionalNumber(run.fullSourceFingerprint.fingerprintLength || 0)}
                <br />
                <strong><LocalizedText source={"Path:"} /></strong> {run.fullSourceFingerprint.path}
              </p>
            </details>
          ) : null}

          {run.provenance && run.provenance.signalCount > 0 ? (
            <>
              <Header as="h5"><LocalizedText source={"Provenance"} /></Header>
              <div style={{ marginBottom: '0.75em' }}>
                <Label size="tiny">
                  <LocalizedText source={"Tool"} />{" "}{run.provenance.toolAvailable ? <LocalizedText source={"available"} /> : <LocalizedText source={"unavailable"} />}
                </Label>
                <Label size="tiny">
                  <LocalizedText source={"Manifest"} />{" "}{run.provenance.manifestHint ? <LocalizedText source={"hinted"} /> : <LocalizedText source={"none"} />}
                </Label>
                <Label size="tiny">
                  <LocalizedText source={"Validation"} />{" "}{run.provenance.validationState || interfaceText('unknown')}
                </Label>
                {run.provenance.verified ? (
                  <Label color="green" size="tiny">
                    <LocalizedText source={"verified"} /></Label>
                ) : null}
              </div>
              <List bulleted>
                {(run.provenance.signals || []).map((signal) => (
                  <List.Item key={signal}>{signal}</List.Item>
                ))}
              </List>
            </>
          ) : null}

          {run.aiHeuristics ? (
            <details style={detailStyle}>
              <summary style={detailSummaryStyle}><LocalizedText source={"AI Audio Heuristics"} /></summary>
              <div style={{ marginBottom: '1em' }}>
                <Label size="tiny">
                  <LocalizedText source={"Score"} />{" "}{formatPercent(run.aiHeuristics.artifactScore)}
                </Label>
                <Label size="tiny">{run.aiHeuristics.artifactLabel || interfaceText('unknown')}</Label>
                <Label size="tiny">
                  <LocalizedText source={"Peaks"} />{" "}{formatRegionalNumber(run.aiHeuristics.peakCount || 0)}
                </Label>
                <Label size="tiny">
                  <LocalizedText source={"Periodicity"} />{' '}
                  {formatPercent(run.aiHeuristics.periodicityStrength)}
                </Label>
                <Label size="tiny">
                  <LocalizedText source={"Centroid"} />{" "}{formatRegionalNumber(Math.round(run.aiHeuristics.spectralCentroid || 0))}
                </Label>
                <Label size="tiny">
                  <LocalizedText source={"Flux"} />{" "}{formatRegionalNumber(Math.round((run.aiHeuristics.spectralFlux || 0) * 1000))}
                </Label>
                <Label size="tiny">
                  <LocalizedText source={"Pitch"} />{" "}{formatPercent(run.aiHeuristics.pitchSalience)}
                </Label>
              </div>
            </details>
          ) : null}

          {Array.isArray(run.perturbations) && run.perturbations.length > 0 ? (
            <details style={detailStyle}>
              <summary style={detailSummaryStyle}>
                <LocalizedText source={"Perturbation Stability ("} />{formatRegionalNumber(run.perturbations.length)})
              </summary>
              <List divided relaxed>
                {run.perturbations.map((item) => (
                  <List.Item key={item.perturbationId}>
                    <List.Content>
                      <List.Header>{item.label}</List.Header>
                      <List.Description>
                        <LocalizedText source={"Delta"} />{" "}{formatPercent(item.baselineDelta)}
                      </List.Description>
                      {item.heuristics ? (
                        <List.Description style={{ marginTop: '0.35em' }}>
                          <LocalizedText source={"Score"} />{" "}{formatPercent(item.heuristics.artifactScore)} ·
                          {` `}<LocalizedText source={"Label"} />{" "}{item.heuristics.artifactLabel || interfaceText('unknown')}
                        </List.Description>
                      ) : null}
                    </List.Content>
                  </List.Item>
                ))}
              </List>
            </details>
          ) : null}

          {Array.isArray(run.corpusMatches) && run.corpusMatches.length > 0 ? (
            <>
              <Header as="h5"><LocalizedText source={"Corpus Matches"} /></Header>
              <List divided relaxed>
                {run.corpusMatches.map((match) => (
                  <List.Item key={match.matchId}>
                    <List.Content>
                      <List.Header>{match.label || match.source}</List.Header>
                      <List.Description>
                        <LocalizedText source={"Similarity"} />{" "}{formatPercent(match.similarityScore)}
                      </List.Description>
                      {match.artist || match.title ? (
                        <List.Description style={{ marginTop: '0.35em' }}>
                          {[match.artist, match.title].filter(Boolean).join(' - ')}
                        </List.Description>
                      ) : null}
                      {match.recordingId ? (
                        <List.Description style={{ marginTop: '0.35em' }}>
                          <LocalizedText source={"Recording:"} />{" "}{match.recordingId}
                        </List.Description>
                      ) : null}
                    </List.Content>
                  </List.Item>
                ))}
              </List>
            </>
          ) : null}

          {Array.isArray(run.stems) && run.stems.length > 0 ? (
            <>
              <Header as="h5"><LocalizedText source={"Demucs Stems"} /></Header>
              <List bulleted>
                {run.stems.map((stem) => (
                  <List.Item key={stem.artifactId}>
                    {stem.label}: {stem.path}
                  </List.Item>
                ))}
              </List>
            </>
          ) : null}

          {Array.isArray(run.evidence) && run.evidence.length > 0 ? (
            <details style={detailStyle}>
              <summary style={detailSummaryStyle}>
                <LocalizedText source={"Evidence ("} />{formatRegionalNumber(run.evidence.length)})
              </summary>
              <List bulleted>
                {run.evidence.map((item) => (
                  <List.Item key={item}>{item}</List.Item>
                ))}
              </List>
            </details>
          ) : null}

          {Array.isArray(run.segments) && run.segments.length > 0 ? (
            <>
              <Header as="h5"><LocalizedText source={"Segment Decomposition"} /></Header>
              <List divided relaxed>
                {run.segments.map((segment) => (
                  <List.Item key={segment.segmentId}>
                    <List.Content>
                      <List.Header>
                        {segment.label}{' '}
                        <Label size="tiny">
                          {formatPercent(segment.confidence)}%
                        </Label>
                      </List.Header>
                      <List.Description>
                        {segment.decompositionLabel || segment.sourceLabel}
                      </List.Description>
                      <List.Description style={{ marginTop: '0.35em' }}>
                        <LocalizedText source={"Search:"} />{" "}<code>{segment.query}</code>
                      </List.Description>
                      {Array.isArray(segment.candidates) &&
                      segment.candidates.length > 0 ? (
                        <List.Description style={{ marginTop: '0.5em' }}>
                          {segment.candidates.map((candidate) => (
                            <Label key={candidate.candidateId} size="tiny">
                              {candidate.artist} - {candidate.title}
                            </Label>
                          ))}
                        </List.Description>
                      ) : null}
                      <div style={{ marginTop: '0.5em' }}>
                        {Array.isArray(segment.options) &&
                        segment.options.length > 0 ? (
                          <Popup
                            content={interfaceText("Run the best segment-level SongID action for this decomposed portion of the source.")}
                            position="top center"
                            trigger={
                              <Button
                                disabled={actionLoading}
                                onClick={() => handleOptionAction(segment.options[0])}
                                size="mini"
                              >
                                {segment.options[0].actionLabel}
                              </Button>
                            }
                           {...interfaceTextProps("Run the best segment-level SongID action for this decomposed portion of the source.")}/>
                        ) : (
                          <Popup
                            content={interfaceText("Search this decomposed segment directly when SongID found a plausible chapter or timestamp clue.")}
                            position="top center"
                            trigger={
                              <Button
                                disabled={actionLoading}
                                onClick={() =>
                                  handleTrackSearchBatch([segment.query])
                                }
                                size="mini"
                              >
                                <LocalizedText source={"Search Segment"} /></Button>
                            }
                           {...interfaceTextProps("Search this decomposed segment directly when SongID found a plausible chapter or timestamp clue.")}/>
                        )}
                      </div>
                    </List.Content>
                  </List.Item>
                ))}
              </List>
            </>
          ) : null}

          {options.length > 0 ? (
            <details style={detailStyle}>
              <summary style={detailSummaryStyle}>
                <LocalizedText source={"Ranked Download Options ("} />{formatRegionalNumber(options.length)})
              </summary>
              <List divided relaxed>
                {options.map((option) => (
                  <List.Item key={option.optionId}>
                    <List.Content floated="right">
                      <Popup
                        content={interfaceText("Run this SongID acquisition option using the scored track, album, or discography path shown here.")}
                        position="top center"
                        trigger={
                          <Button
                            disabled={actionLoading}
                            onClick={() => handleOptionAction(option)}
                            size="small"
                          >
                            {option.actionLabel}
                          </Button>
                        }
                       {...interfaceTextProps("Run this SongID acquisition option using the scored track, album, or discography path shown here.")}/>
                    </List.Content>
                    <List.Content>
                      <List.Header>
                        {option.title}{' '}
                        <Label size="tiny">{option.scope}</Label>
                        <Label size="tiny">{option.mode}</Label>
                        {option.duplicateCount > 1 ? (
                          <Label color="grey" size="tiny">
                            {formatRegionalNumber(option.duplicateCount)} <LocalizedText source={"matches"} /></Label>
                        ) : null}
                      </List.Header>
                      <List.Description>{option.description}</List.Description>
                      {option.searchText ? (
                        <List.Description style={{ marginTop: '0.35em' }}>
                          <LocalizedText source={"Search:"} />{" "}<code>{option.searchText}</code>
                        </List.Description>
                      ) : null}
                      {Array.isArray(option.searchTexts) &&
                      option.searchTexts.length > 0 ? (
                        <List.Description style={{ marginTop: '0.35em' }}>
                          <LocalizedText source={"Searches:"} />{" "}<code>{option.searchTexts.join(' | ')}</code>
                        </List.Description>
                      ) : null}
                      {option.profile ? (
                        <List.Description style={{ marginTop: '0.35em' }}>
                          <LocalizedText source={"Profile:"} />{" "}{option.profile}
                        </List.Description>
                      ) : null}
                      {renderOptionScores(option)}
                    </List.Content>
                  </List.Item>
                ))}
              </List>
            </details>
          ) : null}

          {Array.isArray(run.clips) && run.clips.length > 0 ? (
            <details style={detailStyle}>
              <summary style={detailSummaryStyle}>
                <LocalizedText source={"Clip Findings ("} />{formatRegionalNumber(run.clips.length)})
              </summary>
              <List divided relaxed>
                {run.clips.map((clip) => (
                  <List.Item key={clip.clipId}>
                    <List.Content>
                      <List.Header>
                        {clip.profile} @ {formatRegionalNumber(clip.startSeconds)}s</List.Header>
                      <List.Description>
                        <LocalizedText source={"Duration:"} /> {formatRegionalNumber(clip.durationSeconds)}s</List.Description>
                      {clip.acoustId ? (
                        <List.Description style={{ marginTop: '0.35em' }}>
                          <LocalizedText source={"AcoustID:"} />{" "}{clip.acoustId.artist} - {clip.acoustId.title}
                        </List.Description>
                      ) : null}
                      {clip.songRec ? (
                        <List.Description style={{ marginTop: '0.35em' }}>
                          <LocalizedText source={"SongRec:"} />{" "}{clip.songRec.artist} - {clip.songRec.title}
                        </List.Description>
                      ) : null}
                      {clip.panako ? (
                        <List.Description style={{ marginTop: '0.35em' }}>
                          <LocalizedText source={"Panako:"} />{" "}{clip.panako.title || clip.panako.sourcePath}
                        </List.Description>
                      ) : null}
                      {clip.audfprint ? (
                        <List.Description style={{ marginTop: '0.35em' }}>
                          <LocalizedText source={"Audfprint:"} />{" "}{clip.audfprint.title}
                        </List.Description>
                      ) : null}
                      {clip.aiHeuristics ? (
                        <List.Description style={{ marginTop: '0.35em' }}>
                          <LocalizedText source={"AI Heuristics:"} />{" "}{clip.aiHeuristics.artifactLabel} (
                          {formatPercent(clip.aiHeuristics.artifactScore)})
                        </List.Description>
                      ) : null}
                    </List.Content>
                  </List.Item>
                ))}
              </List>
            </details>
          ) : null}

          {Array.isArray(run.transcripts) && run.transcripts.length > 0 ? (
            <details style={detailStyle}>
              <summary style={detailSummaryStyle}>
                <LocalizedText source={"Transcripts ("} />{formatRegionalNumber(run.transcripts.length)})
              </summary>
              <List divided relaxed>
                {run.transcripts.map((transcript) => (
                  <List.Item key={transcript.transcriptId}>
                    <List.Content>
                      <List.Header>{transcript.source}</List.Header>
                      <List.Description>{transcript.text}</List.Description>
                      <List.Description style={{ marginTop: '0.35em' }}>
                        <LocalizedText source={"Segments:"} />{" "}{formatRegionalNumber(transcript.segmentCount || 0)} <LocalizedText source={"· Language:"} />{' '}
                        {transcript.language || interfaceText('unknown')} <LocalizedText source={"· Excerpt:"} />{' '}
                        {formatRegionalNumber(transcript.excerptStartSeconds || 0)}s /{' '}
                        {formatRegionalNumber(transcript.excerptDurationSeconds || 0)}s</List.Description>
                      {Array.isArray(transcript.musicBrainzQueries) &&
                      transcript.musicBrainzQueries.length > 0 ? (
                        <List.Description style={{ marginTop: '0.35em' }}>
                          <LocalizedText source={"Queries:"} />{" "}{transcript.musicBrainzQueries.join(' | ')}
                        </List.Description>
                      ) : null}
                    </List.Content>
                  </List.Item>
                ))}
              </List>
            </details>
          ) : null}

          {Array.isArray(run.ocr) && run.ocr.length > 0 ? (
            <details style={detailStyle}>
              <summary style={detailSummaryStyle}><LocalizedText source={"OCR ("} />{formatRegionalNumber(run.ocr.length)})</summary>
              <List bulleted>
                {run.ocr.map((item) => (
                  <List.Item key={item.ocrId}>
                    {item.timestampSeconds}s: {item.text}
                  </List.Item>
                ))}
              </List>
            </details>
          ) : null}

          {Array.isArray(run.comments) && run.comments.length > 0 ? (
            <details style={detailStyle}>
              <summary style={detailSummaryStyle}>
                <LocalizedText source={"Comments ("} />{formatRegionalNumber(run.comments.length)})
              </summary>
              <List bulleted>
                {run.comments.map((comment) => (
                  <List.Item key={comment.commentId}>
                    {comment.author ? <LocalizedText source={"{author}:"} values={{ "author": (comment.author) }} /> : ''}
                    {comment.text}
                    {comment.timestampSeconds !== null &&
                    comment.timestampSeconds !== undefined
                      ? <LocalizedText source={"({timestampSeconds}s)"} values={{ "timestampSeconds": (comment.timestampSeconds) }} />
                      : ''}
                  </List.Item>
                ))}
              </List>
            </details>
          ) : null}

          {Array.isArray(run.chapters) && run.chapters.length > 0 ? (
            <>
              <Header as="h5"><LocalizedText source={"Chapters"} /></Header>
              <List bulleted>
                {run.chapters.map((chapter) => (
                  <List.Item key={chapter.chapterId}>
                    {formatRegionalNumber(chapter.startSeconds)}s: {chapter.title || interfaceText('untitled chapter')}
                    {chapter.endSeconds !== null &&
                    chapter.endSeconds !== undefined
                      ? <LocalizedText source={"-> {endSeconds}s"} values={{ "endSeconds": (chapter.endSeconds) }} />
                      : ''}
                  </List.Item>
                ))}
              </List>
            </>
          ) : null}

          {run.forensicMatrix ? (
            <details style={detailStyle}>
              <summary style={detailSummaryStyle}><LocalizedText source={"Forensic Matrix"} /></summary>
              <div style={{ marginBottom: '1em' }}>
                <Popup
                  content={interfaceText("Copy the complete forensic matrix JSON for this SongID run without changing ranking, downloads, or local files.")}
                  position="top left"
                  trigger={
                    <Button
                      aria-label={interfaceText("Copy SongID forensic matrix JSON")}
                      disabled={copyLoading}
                      icon="copy"
                      loading={copyLoading}
                      onClick={copyForensicMatrix}
                      size="mini"
                     {...interfaceTextProps("Copy SongID forensic matrix JSON")}/>
                  }
                 {...interfaceTextProps("Copy the complete forensic matrix JSON for this SongID run without changing ranking, downloads, or local files.")}/>
              </div>
              <div style={{ marginBottom: '1em' }}>
                <Label size="tiny"><LocalizedText source={"Identity"} />{" "}{run.forensicMatrix.identityScore || 0}</Label>
                <Label size="tiny">
                  <LocalizedText source={"Synthetic"} />{" "}{run.forensicMatrix.syntheticScore || 0}
                </Label>
                <Label size="tiny">
                  <LocalizedText source={"Confidence"} />{" "}{run.forensicMatrix.confidenceScore || 0}
                </Label>
                <Label size="tiny">
                  <LocalizedText source={"Family Score"} />{" "}{run.forensicMatrix.knownFamilyScore || 0}
                </Label>
              </div>
              <div style={{ marginBottom: '1em' }}>
                {run.forensicMatrix.identityLane ? (
                  <Popup
                    content={run.forensicMatrix.identityLane.summary}
                    position="top left"
                    trigger={
                      <Label size="tiny">
                        <LocalizedText source={"Identity Lane"} />{" "}{formatPercent(run.forensicMatrix.identityLane.score)}
                      </Label>
                    }
                  />
                ) : null}
                {run.forensicMatrix.confidenceLane ? (
                  <Popup
                    content={run.forensicMatrix.confidenceLane.summary}
                    position="top left"
                    trigger={
                      <Label size="tiny">
                        <LocalizedText source={"Confidence Lane"} />{" "}{formatPercent(run.forensicMatrix.confidenceLane.score)}
                      </Label>
                    }
                  />
                ) : null}
                {run.forensicMatrix.spectralArtifactLane ? (
                  <Popup
                    content={run.forensicMatrix.spectralArtifactLane.summary}
                    position="top left"
                    trigger={
                      <Label size="tiny">
                        <LocalizedText source={"Spectral"} />{" "}{formatPercent(run.forensicMatrix.spectralArtifactLane.score)}
                      </Label>
                    }
                  />
                ) : null}
                {run.forensicMatrix.lyricsSpeechLane ? (
                  <Popup
                    content={run.forensicMatrix.lyricsSpeechLane.summary}
                    position="top left"
                    trigger={
                      <Label size="tiny">
                        <LocalizedText source={"Lyrics"} />{" "}{formatPercent(run.forensicMatrix.lyricsSpeechLane.score)}
                      </Label>
                    }
                  />
                ) : null}
                {run.forensicMatrix.structuralLane ? (
                  <Popup
                    content={run.forensicMatrix.structuralLane.summary}
                    position="top left"
                    trigger={
                      <Label size="tiny">
                        <LocalizedText source={"Structure"} />{" "}{formatPercent(run.forensicMatrix.structuralLane.score)}
                      </Label>
                    }
                  />
                ) : null}
                {run.forensicMatrix.provenanceLane ? (
                  <Popup
                    content={run.forensicMatrix.provenanceLane.summary}
                    position="top left"
                    trigger={
                      <Label size="tiny">
                        <LocalizedText source={"Provenance"} />{" "}{formatPercent(run.forensicMatrix.provenanceLane.score)}
                      </Label>
                    }
                  />
                ) : null}
              </div>
              {Array.isArray(run.forensicMatrix.topEvidenceFor) &&
              run.forensicMatrix.topEvidenceFor.length > 0 ? (
                <div style={{ marginBottom: '0.75em' }}>
                  <strong><LocalizedText source={"For:"} /></strong> {run.forensicMatrix.topEvidenceFor.join(' | ')}
                </div>
              ) : null}
              {Array.isArray(run.forensicMatrix.topEvidenceAgainst) &&
              run.forensicMatrix.topEvidenceAgainst.length > 0 ? (
                <div style={{ marginBottom: '0.75em' }}>
                  <strong><LocalizedText source={"Against:"} /></strong>{' '}
                  {run.forensicMatrix.topEvidenceAgainst.join(' | ')}
                </div>
              ) : null}
              {Array.isArray(run.forensicMatrix.notes) &&
              run.forensicMatrix.notes.length > 0 ? (
                <div style={{ marginBottom: '0.75em' }}>
                  <strong><LocalizedText source={"Notes:"} /></strong> {run.forensicMatrix.notes.join(' | ')}
                </div>
              ) : null}
            </details>
          ) : null}

    </>
  );
};

export default SongIDEvidenceDetails;
