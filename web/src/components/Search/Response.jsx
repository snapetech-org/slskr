import LocalizedText from "../Shared/LocalizedText";
import { interfaceText, interfaceTextProps, useInterfaceLanguage } from "../../lib/interfaceLocale";
import { LocalizedPopup } from '../Shared/TooltipButton';
import * as discoveryGraph from '../../lib/discoveryGraph';
import api from '../../lib/api';
import { safeOpenBlank } from '../../lib/safeOpen';
import * as searches from '../../lib/searches';
import * as transfers from '../../lib/transfers';
import {
  buildSearchActionPreview,
  formatSearchActionPreview,
} from '../../lib/searchActionPreview';
import {
  getCommunityQualityLabel,
  getCommunityQualitySummary,
  recordCommunityQualitySignal,
} from '../../lib/communityQualitySignals';
import { getDirectoryContents, getGroup } from '../../lib/users';
import {
  buildSearchResultActionPath,
  getSearchResultItemId,
} from '../../lib/searchItemId';
import { toDisplayError } from '../../lib/errors';
import { formatBytes, formatRegionalNumber, getDirectoryName, getFileName, useRegionalFormat } from '../../lib/util';
import DiscoveryGraphModal from './DiscoveryGraphModal';
import DownloadActionPreviewModal from './DownloadActionPreviewModal';
import FileList from '../Shared/FileList';
import { LocalizedPopup as Popup } from '../Shared/TooltipButton';
import UserCard from '../Shared/UserCard';
import UserNoteModal from '../Users/UserNoteModal';
import React, { Component } from 'react';

import { Link } from 'react-router-dom';
import { toast } from 'react-toastify';
import { Button as SemanticButton, Card, Icon, Label } from 'semantic-ui-react';

const textContent = (children) => {
  if (typeof children === 'string') return children;
  if (Array.isArray(children)) return children.map(textContent).filter(Boolean).join(' ').trim();
  return '';
};

const translateChildren = (children, t, parameters) => {
  if (typeof children === 'string') return t(children, parameters);
  if (Array.isArray(children)) return children.map((child) => translateChildren(child, t, parameters));
  return children;
};

const Button = ({ children, content, title, parameters = {}, 'aria-label': ariaLabel, ...props }) => {
  const { t, languageFor, directionFor } = useInterfaceLanguage();
  const source = ariaLabel || title || (typeof content === 'string' ? content : textContent(children));
  const translatedContent = typeof content === 'string' ? t(content, parameters) : content;
  const translatedChildren = translateChildren(children, t, parameters);
  return (
    <SemanticButton
      {...props}
      aria-label={typeof ariaLabel === 'string' ? t(ariaLabel, parameters) : (source ? t(source, parameters) : undefined)}
      content={translatedContent}
      dir={source ? directionFor(source) : undefined}
      lang={source ? languageFor(source) : undefined}
      title={typeof title === 'string' ? t(title, parameters) : title}
    >
      {translatedChildren}
    </SemanticButton>
  );
};

Button.Group = SemanticButton.Group;
Button.Or = SemanticButton.Or;

const buildTree = (response) => {
  const files = [
    ...(Array.isArray(response?.files) ? response.files : []),
    ...(Array.isArray(response?.lockedFiles)
      ? response.lockedFiles.map((file) => ({ ...file, locked: true }))
      : []),
  ].filter(
    (file) =>
      file && typeof file === 'object' && typeof file.filename === 'string',
  );

  return files.reduce((dict, file) => {
    const directory = getDirectoryName(file.filename);
    const selectable = { selected: false, ...file };
    dict[directory] =
      dict[directory] === undefined
        ? [selectable]
        : dict[directory].concat(selectable);
    return dict;
  }, {});
};

const getBadgeColor = (downloadStats) => {
  if (!downloadStats) return null;
  if (downloadStats.successfulDownloads >= 5) return 'green';
  if (downloadStats.successfulDownloads >= 1) return 'blue';
  if (downloadStats.failedDownloads > downloadStats.successfulDownloads)
    return 'orange';
  return 'grey';
};

const getGroupIndicator = (group) => {
  switch (group) {
    case 'privileged':
      return { color: 'yellow', icon: 'star', tooltip: 'Privileged User' };
    case 'leechers':
      return {
        color: 'orange',
        icon: 'exclamation triangle',
        tooltip: 'Leecher (Low shares)',
      };
    case 'blacklisted':
      return { color: 'red', icon: 'ban', tooltip: 'Blacklisted User' };
    default:
      // For user-defined groups or default group, show a generic user icon
      return group && group !== 'default'
        ? { color: 'blue', icon: 'user', tooltip: 'Group: {group}', parameters: { group } }
        : null;
  }
};

const getSelectedFiles = (tree) => {
  return Object.keys(tree)
    .reduce((list, dict) => list.concat(tree[dict]), [])
    .filter((f) => f.selected);
};

const getSelectedSize = (selectedFiles) => {
  return formatBytes(
    selectedFiles.reduce((total, file) => {
      const size = Number(file?.size);
      return total + (Number.isFinite(size) && size >= 0 ? size : 0);
    }, 0),
  );
};

class Response extends Component {
  constructor(props) {
    super(props);

    this.state = {
      downloadError: '',
      downloadRequest: undefined,
      fetchingDirectoryContents: false,
      graphData: null,
      graphLoading: false,
      graphOpen: false,
      graphRequest: null,
      isFolded: this.props.isInitiallyFolded,
      previewOpen: false,
      qualitySummary: getCommunityQualitySummary(this.props.response.username),
      tree: buildTree(this.props.response),
      userGroup: null,
      userGroupLoading: false,
    };
    this.isMountedFlag = false;
    this.requestIds = {
      directory: 0,
      download: 0,
      graph: 0,
      userGroup: 0,
    };
  }

  localize = (source, parameters) => this.props.locale.t(source, parameters);

  localizedText = (source, parameters) => {
    const { languageFor, directionFor } = this.props.locale;
    return (
      <span lang={languageFor(source)} dir={directionFor(source)}>
        {this.localize(source, parameters)}
      </span>
    );
  };

  localizedError = (error, fallback) => {
    const source = toDisplayError(error, fallback);
    if (
      this.props.locale.language !== 'en' &&
      this.props.locale.languageFor(source) === 'en'
    ) {
      return this.localize(fallback);
    }
    return this.localize(source);
  };

  formatNumber = (value) => formatRegionalNumber(value);

  componentDidMount() {
    this.isMountedFlag = true;
    void this.fetchUserGroup();
  }

  componentWillUnmount() {
    this.isMountedFlag = false;
    Object.keys(this.requestIds).forEach((key) => {
      this.requestIds[key] += 1;
    });
  }

  componentDidUpdate(previousProps) {
    if (
      JSON.stringify(this.props.response) !==
      JSON.stringify(previousProps.response)
    ) {
      this.setState({ tree: buildTree(this.props.response) });
    }

    if (this.props.isInitiallyFolded !== previousProps.isInitiallyFolded) {
      this.setState({ isFolded: this.props.isInitiallyFolded });
    }

    if (this.props.response.username !== previousProps.response.username) {
      void this.fetchUserGroup();
      this.setState({
        qualitySummary: getCommunityQualitySummary(this.props.response.username),
      });
    }
  }

  fetchUserGroup = async () => {
    const { username } = this.props.response;
    const requestId = ++this.requestIds.userGroup;

    if (this.isMountedFlag && requestId === this.requestIds.userGroup) {
      this.setState({ userGroupLoading: true });
    }

    try {
      const response = await getGroup({ username });
      if (
        this.isMountedFlag &&
        requestId === this.requestIds.userGroup &&
        this.props.response.username === username
      ) {
        this.setState({ userGroup: response.data, userGroupLoading: false });
      }
    } catch (error) {
      console.debug('Failed to fetch user group for', username, error);
      if (
        this.isMountedFlag &&
        requestId === this.requestIds.userGroup &&
        this.props.response.username === username
      ) {
        this.setState({ userGroup: null, userGroupLoading: false });
      }
    }
  };

  handleFileSelectionChange = (file, state) => {
    if (!file) return;
    this.setState((previousState) => {
      const tree = Object.fromEntries(
        Object.entries(previousState.tree).map(([directory, files]) => [
          directory,
          files.map((candidate) =>
            candidate === file
              ? { ...candidate, selected: Boolean(state) }
              : candidate,
          ),
        ]),
      );
      return {
        downloadError: '',
        downloadRequest: undefined,
        tree,
      };
    });
  };

  download = (username, files) => {
    const requestId = ++this.requestIds.download;
    this.setState({ downloadRequest: 'inProgress' }, async () => {
      if (!this.isMountedFlag || requestId !== this.requestIds.download) return;
      try {
        const { response, responseIndex, searchId } = this.props;

        // Check if this is a bridged search result (has provenance) and we have searchId
        if (
          response.sourceProviders &&
          response.sourceProviders.length > 0 &&
          searchId
        ) {
          // Use new action routing endpoint for bridged searches
          // Download all selected files
          const downloadPromises = files.map(async (file) => {
            const itemId = getSearchResultItemId({
              file,
              response,
              responseIndex,
            });
            if (!itemId) {
              throw new Error(`File ${file.filename} not found in response`);
            }

            return api.post(
              buildSearchResultActionPath(searchId, itemId, 'download'),
            );
          });

          await Promise.all(downloadPromises);
        } else {
          // Use existing download method for non-bridged searches
          const requests = (files || []).map(({ filename, size }) => ({
            filename,
            size,
          }));
          await transfers.download({ files: requests, username });
        }

        if (
          this.isMountedFlag &&
          requestId === this.requestIds.download
        ) {
          this.setState({ downloadRequest: 'complete' });
        }
      } catch (error) {
        if (
          this.isMountedFlag &&
          requestId === this.requestIds.download
        ) {
          this.setState({
            downloadError: this.localizedError(error, 'Download failed'),
            downloadRequest: 'error',
          });
        }
      }
    });
  };

  getFullDirectory = async (username, directory) => {
    const requestId = ++this.requestIds.directory;
    if (!this.isMountedFlag) return;
    this.setState({ fetchingDirectoryContents: true });

    try {
      try {
        // some clients might send more than one directory in the response,
        // if the requested directory contains subdirectories. the root directory
        // is always first, and for now we'll only display the contents of that.
        const allDirectories = await getDirectoryContents({
          directory,
          username,
        });
        const theRootDirectory = allDirectories?.[0];

        // some clients might send an empty response for some reason
        if (!theRootDirectory) {
          throw new Error('No directories were included in the response');
        }

        const name =
          typeof theRootDirectory.name === 'string' &&
          theRootDirectory.name.trim()
            ? theRootDirectory.name
            : directory;
        const files = Array.isArray(theRootDirectory.files)
          ? theRootDirectory.files.filter(
              (file) =>
                file &&
                typeof file === 'object' &&
                typeof file.filename === 'string',
            )
          : [];

        // the api returns file names only, so we need to prepend the directory
        // to make it look like a search result.  we also need to preserve
        // any file selections, so check the old files and assign accordingly
        if (
          this.isMountedFlag &&
          requestId === this.requestIds.directory
        ) {
          this.setState((previousState) => {
            const oldFiles = previousState.tree[directory] || [];
            const fixedFiles = files.map((file) => {
              const filename = `${directory}\\${file.filename}`;
              return {
                ...file,
                filename,
                selected:
                  oldFiles.find((candidate) => candidate.filename === filename)
                    ?.selected ?? false,
              };
            });
            return {
              tree: {
                ...previousState.tree,
                [name]: fixedFiles,
              },
            };
          });
        }
      } catch (error) {
        throw new Error(`Failed to process directory response: ${error}`, {
          cause: error,
        });
      }
    } catch (error) {
      console.error(error);
      toast.error(this.localizedText('Failed to load directory contents'));
    } finally {
      if (
        this.isMountedFlag &&
        requestId === this.requestIds.directory
      ) {
        this.setState({ fetchingDirectoryContents: false });
      }
    }
  };

  handleToggleFolded = () => {
    this.setState((previousState) => ({ isFolded: !previousState.isFolded }));
  };

  reportSuspiciousCandidate = () => {
    const { onQualitySignalUpdate, response } = this.props;

    recordCommunityQualitySignal({
      reason: 'Reported suspicious candidate from Search review.',
      type: 'suspicious-candidate',
      username: response.username,
    });

    this.setState({
      qualitySummary: getCommunityQualitySummary(response.username),
    });

    if (onQualitySignalUpdate) {
      onQualitySignalUpdate();
    }

    toast.success(this.localizedText(
      'Added a local caution signal for {username}. Nothing was published.',
      { username: response.username },
    ));
  };

  buildFallbackGraphRequest = () => {
    const { response } = this.props;
    const firstFile = response.files?.[0] || response.lockedFiles?.[0];
    const title = firstFile ? getFileName(firstFile.filename).replace(/\.[^.]+$/u, '') : response.username;

    return {
      scope: 'songid_run',
      artist: response.username,
      title,
    };
  };

  openDiscoveryGraph = async (request) => {
    const requestId = ++this.requestIds.graph;
    if (!this.isMountedFlag) return;
    this.setState({
      graphLoading: true,
      graphOpen: true,
      graphRequest: request,
    });

    try {
      const graph = await discoveryGraph.buildDiscoveryGraph(request);
      if (this.isMountedFlag && requestId === this.requestIds.graph) {
        this.setState({ graphData: graph });
      }
    } catch (error) {
      console.error(error);
      if (this.isMountedFlag && requestId === this.requestIds.graph) {
        toast.error(this.localizedText(this.localizedError(error, 'Failed to build discovery graph')));
        this.setState({ graphOpen: false });
      }
    } finally {
      if (this.isMountedFlag && requestId === this.requestIds.graph) {
        this.setState({ graphLoading: false });
      }
    }
  };

  handleGraphCompare = async (nodeId, label) => {
    const { graphRequest } = this.state;
    if (!graphRequest || !nodeId) {
      return;
    }

    await this.openDiscoveryGraph({
      ...graphRequest,
      compareLabel: label,
      compareNodeId: nodeId,
    });
  };

  handleGraphRecenter = async (nodeId) => {
    if (!nodeId) {
      return;
    }

    const [nodeType, rawId] = nodeId.split(':');
    if (nodeType === 'artist') {
      await this.openDiscoveryGraph({ scope: 'artist', artistId: rawId });
      return;
    }

    if (nodeType === 'album' || nodeType === 'release-group') {
      await this.openDiscoveryGraph({ scope: 'album', releaseId: rawId });
      return;
    }

    if (nodeType === 'track') {
      await this.openDiscoveryGraph({ scope: 'track', recordingId: rawId });
      return;
    }

    await this.openDiscoveryGraph(this.buildFallbackGraphRequest());
  };

  handleQueueNearbyFromGraph = async (graph) => {
    const queries = (graph?.nodes || [])
      .filter((node) => node.nodeType === 'track')
      .map((node) => node.label || '')
      .filter(Boolean)
      .slice(0, 8);

    if (queries.length === 0) {
      toast.error(this.localizedText('No nearby track nodes were available to queue'));
      return;
    }

    try {
      const count = await searches.createBatch({ queries });
      toast.success(this.localizedText('Started {count} nearby graph searches', { count }));
    } catch (error) {
      console.error(error);
      toast.error(this.localizedText(this.localizedError(error, 'Failed to queue nearby graph searches')));
    }
  };

  copyPreview = async (preview) => {
    try {
      await navigator.clipboard.writeText(formatSearchActionPreview(preview));
      toast.success(this.localizedText('Copied action preview'));
    } catch (error) {
      console.error(error);
      toast.error(this.localizedText('Unable to copy action preview'));
    }
  };

  renderActionPreview = (preview, selectedSize) => (
    <DownloadActionPreviewModal
      onClose={() => this.setState({ previewOpen: false })}
      onCopy={() => this.copyPreview(preview)}
      open={this.state.previewOpen}
      preview={preview}
      selectedSize={selectedSize}
    />
  );

  renderDownloadAction = (
    selectedFiles,
    selectedSize,
    downloadRequest,
    downloadError,
  ) => {
    const noSelection = selectedFiles.length === 0;
    const { candidateRank, response } = this.props;
    const { qualitySummary } = this.state;
    const hasPodSource = response.sourceProviders?.includes('pod');
    const primarySource = response.primarySource || 'scene';
    const preview = buildSearchActionPreview({
      candidateRank,
      communityQualitySummary: response.communityQualitySummary || qualitySummary,
      files: selectedFiles,
      response,
    });

    return (
      <Card.Content extra>
        <span>
          {!noSelection && this.renderActionPreview(preview, selectedSize)}
          <Button
            basic={noSelection}
            color={noSelection ? 'grey' : 'green'}
            content={interfaceText("Download")}
            disabled={
              noSelection ||
              this.props.disabled ||
              downloadRequest === 'inProgress'
            }
            icon="download"
            label={
              noSelection
                ? undefined
                : {
                    as: 'a',
                    basic: false,
                    content: <>{this.localizedText('Files selected: {count}', { count: this.formatNumber(selectedFiles.length) })}, {selectedSize}</>,
                  }
            }
            labelPosition={noSelection ? undefined : 'right'}
            onClick={() =>
              this.download(this.props.response.username, selectedFiles)
            }
           {...interfaceTextProps("Download")}/>
          <Popup
            content={interfaceText("Preview the selected download action, route, files, size, and warnings without starting a transfer.")}
            position="top center"
            trigger={
              <Button
                basic
                content={interfaceText("Preview")}
                disabled={noSelection || downloadRequest === 'inProgress'}
                icon="clipboard list"
                onClick={() => this.setState({ previewOpen: true })}
               {...interfaceTextProps("Preview")}/>
            }
           {...interfaceTextProps("Preview the selected download action, route, files, size, and warnings without starting a transfer.")}/>
          {hasPodSource && selectedFiles.length > 0 && (
            <Popup
              content={interfaceText("Stream from Pod: {availability}.")}
              parameters={{ availability: this.localize(primarySource === 'pod' ? 'Preferred' : 'Available') }}
              position="top center"
              trigger={
                <Button
                  basic
                  color="blue"
                  content={interfaceText("Stream")}
                  disabled={
                    noSelection ||
                    this.props.disabled ||
                    downloadRequest === 'inProgress'
                  }
                  icon="play"
                  onClick={async () => {
                    // Stream first selected file
                    const firstFile = selectedFiles[0];
                    const {
                      response: responseProperty,
                      responseIndex,
                      searchId,
                    } = this.props;
                    if (!firstFile || !searchId) return;

                    try {
                      const itemId = getSearchResultItemId({
                        file: firstFile,
                        response: responseProperty,
                        responseIndex,
                      });
                      if (!itemId) return;

                      const result = await api.post(
                        buildSearchResultActionPath(searchId, itemId, 'stream'),
                      );

                      if (result.data?.stream_url) {
                        safeOpenBlank(result.data.stream_url);
                      }
                    } catch (error) {
                      toast.error(this.localizedText(this.localizedError(error, 'Stream failed')));
                    }
                  }}
                 {...interfaceTextProps("Stream")}/>
              }
             {...interfaceTextProps("Stream from Pod: {availability}.")}/>
          )}
          {downloadRequest === 'inProgress' && (
            <Icon
              aria-label={this.localize('Download in progress')}
              lang={this.props.locale.languageFor('Download in progress')}
              dir={this.props.locale.directionFor('Download in progress')}
              loading
              name="circle notch"
              size="large"
            />
          )}
          {downloadRequest === 'complete' && (
            <Icon
              aria-label={this.localize('Download complete')}
              lang={this.props.locale.languageFor('Download complete')}
              dir={this.props.locale.directionFor('Download complete')}
              color="green"
              name="checkmark"
              size="large"
            />
          )}
          {downloadRequest === 'error' && (
            <span>
              <Icon
                aria-label={this.localize('Download failed')}
                lang={this.props.locale.languageFor('Download failed')}
                dir={this.props.locale.directionFor('Download failed')}
                color="red"
                name="x"
                size="large"
              />
              <Label>
                {this.localizedText(this.localizedError(downloadError, 'Download failed'))}{' '}
                {downloadError?.status &&
                  interfaceText('(HTTP {status} {statusText})', {
                    status: downloadError.status,
                    statusText: downloadError.statusText || '',
                  })}
              </Label>
            </span>
          )}
        </span>
      </Card.Content>
    );
  };

  render() {
    const {
      downloadStats,
      isBlocked,
      onBlock,
      onNoteUpdate,
      onUnblock,
      response,
      candidateRank,
      userNote,
    } = this.props;
    const free = response.hasFreeUploadSlot;
    const { languageFor, directionFor } = this.props.locale;

    const {
      downloadError,
      downloadRequest,
      fetchingDirectoryContents,
      isFolded,
      tree,
      userGroup,
      userGroupLoading,
      graphData,
      graphLoading,
      graphOpen,
      qualitySummary,
    } = this.state;

    const selectedFiles = getSelectedFiles(tree);
    const selectedSize = getSelectedSize(selectedFiles);
    const badgeColor = getBadgeColor(downloadStats);
    const activeQualitySummary = response.communityQualitySummary || qualitySummary;
    const qualityLabel = getCommunityQualityLabel(activeQualitySummary);
    const rawUploadSpeed = response.uploadSpeed ?? response.averageSpeed;
    const uploadSpeed = Number.isFinite(rawUploadSpeed)
      ? `${formatBytes(rawUploadSpeed)}/s`
      : 'Unknown';
    const queueLength = Number.isFinite(response.queueLength)
      ? response.queueLength
      : 'Unknown';

    return (
      <>
        <Card
          className="result-card"
          raised
        >
          <Card.Content>
          <Card.Header className="result-card-header">
            <div className="result-card-identity">
              <Icon
                aria-label={this.localize(
                  isFolded ? 'Expand search results from {username}' : 'Collapse search results from {username}',
                  { username: response.username },
                )}
                className="result-card-fold"
                lang={languageFor(isFolded ? 'Expand search results from {username}' : 'Collapse search results from {username}')}
                dir={directionFor(isFolded ? 'Expand search results from {username}' : 'Collapse search results from {username}')}
                link
                name={isFolded ? 'chevron right' : 'chevron down'}
                onClick={this.handleToggleFolded}
              />
              <span
                className={`result-card-presence ${free ? 'free' : 'queued'}`}
                title={this.localize(free ? 'Free upload slot available' : 'No free upload slot')}
                lang={languageFor(free ? 'Free upload slot available' : 'No free upload slot')}
                dir={directionFor(free ? 'Free upload slot available' : 'No free upload slot')}
              />
              <Link
                className="result-card-user"
                title={this.localize('Browse files')}
                to={{
                  pathname: '/browse',
                  state: { user: response.username },
                }}
              >
                <UserCard username={response.username}>
                  {response.username}
                </UserCard>
              </Link>
              <div className="result-card-badges">
                {!userGroupLoading &&
                  userGroup &&
                  (() => {
                    const indicator = getGroupIndicator(userGroup);
                    return indicator ? (
                      <Popup
                        content={indicator.tooltip}
                        parameters={indicator.parameters}
                        position="top center"
                        trigger={
                          <Icon
                            color={indicator.color}
                            name={indicator.icon}
                            size="small"
                          />
                        }
                      />
                    ) : null;
                  })()}
                {downloadStats && (
                  <Popup
                content={interfaceText("This peer has {successful} successful downloads and {failed} failed downloads.")}
                    parameters={{ successful: downloadStats.successfulDownloads, failed: downloadStats.failedDownloads }}
                    position="top center"
                    trigger={
                      <Label
                        color={badgeColor}
                        size="tiny"
                      >
                        <Icon name="download" />
                        {this.formatNumber(downloadStats.successfulDownloads)}
                      </Label>
                    }
                   {...interfaceTextProps("This peer has {successful} successful downloads and {failed} failed downloads.")}/>
                )}
                {candidateRank?.score !== undefined && (
                  <LocalizedPopup
                    content={candidateRank.reasons?.length > 0
                      ? 'Candidate score: {score}/100. Reasons: {reasons}'
                      : 'Candidate score: {score}/100'}
                    parameters={{ score: candidateRank.score, reasons: candidateRank.reasons?.join(', ') }}
                    parameters={{ score: candidateRank.score, reasons: candidateRank.reasons?.join(', ') }}
                    position="top center"
                    trigger={
                      <Label
                        color="purple"
                        size="tiny"
                      >
                        <Icon name="star" />
                        {this.formatNumber(candidateRank.score)}
                      </Label>
                    }
                  />
                )}
                {response.duplicateGroup?.foldedCount > 0 && (
                  <Popup
                    content={interfaceText("Hidden duplicate results: {count}. Sources: {providers}. Use the Fold Duplicates search option to inspect each source.")}
                    parameters={{ count: response.duplicateGroup.foldedCount, providers: response.duplicateGroup.providers.join(', ') }}
                    position="top center"
                    trigger={
                      <Label
                        color="teal"
                        size="tiny"
                      >
                        <Icon name="clone" />
                        +{this.formatNumber(response.duplicateGroup.foldedCount)}
                      </Label>
                    }
                   {...interfaceTextProps("Hidden duplicate results: {count}. Sources: {providers}. Use the Fold Duplicates search option to inspect each source.")}/>
                )}
                {qualityLabel && (
                  <Popup
                    content={interfaceText("Local peer signals: {positive} positive; {negative} caution.")}
                    parameters={{ positive: activeQualitySummary.positive, negative: activeQualitySummary.negative }}
                    position="top center"
                    trigger={
                      <Label
                        color={qualityLabel.color}
                        size="tiny"
                      >
                        <Icon name={qualityLabel.icon} />
                        {this.localizedText(qualityLabel.text)}
                      </Label>
                    }
                   {...interfaceTextProps("Local peer signals: {positive} positive; {negative} caution.")}/>
                )}
                {userNote && (
                  <LocalizedPopup
                    content={userNote.note || 'User Note'}
                    translateContent={!userNote.note}
                    position="top center"
                    trigger={
                      <Label
                        circular
                        color={userNote.color || 'grey'}
                        empty={!userNote.icon}
                        icon={userNote.icon}
                        size="tiny"
                      />
                    }
                  />
                )}
                {response.sourceProviders &&
                  response.sourceProviders.length > 0 && (
                    <>
                      {response.sourceProviders.includes('pod') && (
                        <Popup
                          content={interfaceText("Available from Pod/Mesh network")}
                          position="top center"
                          trigger={
                            <Label
                              color="blue"
                              size="tiny"
                            >
                              POD
                            </Label>
                          }
                         {...interfaceTextProps("Available from Pod/Mesh network")}/>
                      )}
                      {response.sourceProviders.includes('scene') && (
                        <Popup
                          content={interfaceText("Available from Soulseek Scene")}
                          position="top center"
                          trigger={
                            <Label
                              color="purple"
                              size="tiny"
                            >
                              SCENE
                            </Label>
                          }
                         {...interfaceTextProps("Available from Soulseek Scene")}/>
                      )}
                      {response.sourceProviders.length > 1 && (
                        <Popup
                          content={interfaceText("Available from {providers}. Preferred: {provider}.")}
                          parameters={{ providers: 'Pod and Scene', provider: response.primarySource?.toUpperCase() || 'POD' }}
                          position="top center"
                          trigger={
                            <Label
                              color="teal"
                              size="tiny"
                            >
                              <LocalizedText source={"POD+SCENE"} /></Label>
                          }
                         {...interfaceTextProps("Available from {providers}. Preferred: {provider}.")}/>
                      )}
                    </>
                  )}
                <UserNoteModal
                  onClose={onNoteUpdate}
                  trigger={
                    <Icon
                      color="grey"
                      link
                      name="pencil alternate"
                      size="small"
                      title={this.localize('Edit User Note')}
                    />
                  }
                  username={response.username}
                />
              </div>
            </div>
            <div className="result-card-actions">
              <Popup
                content={interfaceText("Open a Discovery Graph centered on this result to explore related context.")}
                position="top center"
                trigger={
                  <Icon
                    aria-label={this.localize('Open Discovery Graph for {username}', { username: response.username })}
                    color="blue"
                    link
                    lang={languageFor('Open Discovery Graph for {username}')}
                    dir={directionFor('Open Discovery Graph for {username}')}
                    name="share alternate"
                    onClick={() => this.openDiscoveryGraph(this.buildFallbackGraphRequest())}
                  />
                }
               {...interfaceTextProps("Open a Discovery Graph centered on this result to explore related context.")}/>
              <Popup
                content={interfaceText("Open this result in atlas mode to browse a wider neighborhood with semantic zoom controls.")}
                position="top center"
                trigger={
                  <Icon
                    aria-label={this.localize('Open Discovery Graph atlas for {username}', { username: response.username })}
                    color="teal"
                    link
                    lang={languageFor('Open Discovery Graph atlas for {username}')}
                    dir={directionFor('Open Discovery Graph atlas for {username}')}
                    name="crosshairs"
                    onClick={() => this.openDiscoveryGraph(this.buildFallbackGraphRequest())}
                  />
                }
               {...interfaceTextProps("Open this result in atlas mode to browse a wider neighborhood with semantic zoom controls.")}/>
              <Popup
                content={interfaceText("Add a local caution signal for this peer/result. This only affects your browser-side review and does not publish a report.")}
                position="top center"
                trigger={
                  <Icon
                    aria-label={this.localize('Report suspicious result from {username}', { username: response.username })}
                    color="orange"
                    link
                    lang={languageFor('Report suspicious result from {username}')}
                    dir={directionFor('Report suspicious result from {username}')}
                    name="exclamation triangle"
                    onClick={this.reportSuspiciousCandidate}
                  />
                }
               {...interfaceTextProps("Add a local caution signal for this peer/result. This only affects your browser-side review and does not publish a report.")}/>
              <Popup
                content={interfaceText(isBlocked ? 'Unblock this user' : 'Block this user from search results')}
                position="top center"
                trigger={
                  <Icon
                    aria-label={this.localize(isBlocked ? 'Unblock {username}' : 'Block {username} from search results', { username: response.username })}
                    color={isBlocked ? 'orange' : 'grey'}
                    link
                    lang={languageFor(isBlocked ? 'Unblock {username}' : 'Block {username} from search results')}
                    dir={directionFor(isBlocked ? 'Unblock {username}' : 'Block {username} from search results')}
                    name={isBlocked ? 'ban' : 'user cancel'}
                    onClick={isBlocked ? onUnblock : onBlock}
                  />
                }
                {...interfaceTextProps(isBlocked ? 'Unblock this user' : 'Block this user from search results')}
              />
              <Icon
                aria-label={this.localize('Hide search result from {username}', { username: response.username })}
                className="close-button"
                color="red"
                lang={languageFor('Hide search result from {username}')}
                dir={directionFor('Hide search result from {username}')}
                link
                name="close"
                onClick={() => this.props.onHide()}
              />
            </div>
          </Card.Header>
          <Card.Meta className="result-meta">
            <span>
              {this.localizedText('Upload speed: {speed}/s. Free upload slot: {slot}. Queue length: {queue}.', {
                speed: uploadSpeed,
                slot: this.localize(free ? 'Available' : 'Unavailable'),
                queue: queueLength,
              })}
            </span>
          </Card.Meta>
          {((!isFolded && Object.keys(tree)) || []).map((directory) => (
            <FileList
              directoryName={directory}
              disabled={downloadRequest === 'inProgress'}
              files={tree[directory]}
              footer={
                <Button.Group fluid size="tiny">
                  <Button
                    disabled={fetchingDirectoryContents}
                    icon={fetchingDirectoryContents ? 'circle notch' : 'search'}
                    loading={fetchingDirectoryContents}
                    onClick={() =>
                      this.getFullDirectory(response.username, directory)
                    }
                    content={interfaceText("Find More Files")}
                   {...interfaceTextProps("Find More Files")}/>
                  {this.props.onIgnoreDirectory && (
                    <Popup
                      content={interfaceText("Hide this peer’s copy of this folder from future Wishlist searches without blocking the peer or hiding other results.")}
                      trigger={
                        <Button
                          color="red"
                          content={interfaceText("Ignore for Wishlist")}
                          icon="eye slash"
                          onClick={() =>
                            this.props.onIgnoreDirectory(directory)
                          }
                         {...interfaceTextProps("Ignore for Wishlist")}/>
                      }
                     {...interfaceTextProps("Hide this peer’s copy of this folder from future Wishlist searches without blocking the peer or hiding other results.")}/>
                  )}
                </Button.Group>
              }
              key={directory}
              locked={tree[directory].find((file) => file.locked)}
              onSelectionChange={this.handleFileSelectionChange}
            />
          ))}
          </Card.Content>
          {this.renderDownloadAction(
            selectedFiles,
            selectedSize,
            downloadRequest,
            downloadError,
          )}
        </Card>
        <DiscoveryGraphModal
          graph={graphData}
          loading={graphLoading}
          onClose={() => this.setState({ graphOpen: false })}
          onCompare={this.handleGraphCompare}
          onQueueNearby={this.handleQueueNearbyFromGraph}
          onRecenter={this.handleGraphRecenter}
          onRestoreBranch={(branch) =>
            branch?.request && this.openDiscoveryGraph(branch.request)
          }
          open={graphOpen}
        />
      </>
    );
  }
}

const ResponseWithLocale = (props) => {
  const locale = useInterfaceLanguage();
  const regionalFormat = useRegionalFormat();
  return <Response {...props} locale={locale} regionalFormat={regionalFormat} />;
};

export default ResponseWithLocale;
