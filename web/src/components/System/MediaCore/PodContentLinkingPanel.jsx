import LocalizedText from "../../Shared/LocalizedText";
import { interfaceText, interfaceTextProps, useInterfaceLanguage } from "../../../lib/interfaceLocale";


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

const PodContentLinkingPanel = ({ contentId, setContentId, visible = true }) => {
  useInterfaceLanguage();
  const mountedRef = useRef(true);

  useEffect(() => {
    mountedRef.current = true;
    return () => {
      mountedRef.current = false;
    };
  }, []);

  // Pod Content Linking states
  const [contentValidation, setContentValidation] = useMountedState(mountedRef, null);
  const [contentMetadata, setContentMetadata] = useMountedState(mountedRef, null);
  const [contentSearchQuery, setContentSearchQuery] = useMountedState(mountedRef, '');
  const [contentSearchResults, setContentSearchResults] = useMountedState(mountedRef, []);
  const [contentSearchError, setContentSearchError] = useMountedState(mountedRef, null);
  const [contentValidationLoading, setContentValidationLoading] =
    useMountedState(mountedRef, false);
  const [contentMetadataLoading, setContentMetadataLoading] = useMountedState(mountedRef, false);
  const [contentSearchLoading, setContentSearchLoading] = useMountedState(mountedRef, false);
  const [createPodLoading, setCreatePodLoading] = useMountedState(mountedRef, false);
  const [newPodName, setNewPodName] = useMountedState(mountedRef, '');
  const [newPodVisibility, setNewPodVisibility] = useMountedState(mountedRef, 'Unlisted');


  const handleValidateContentId = async () => {
    if (!contentId.trim()) {
      toast.error(interfaceText("Content ID is required"));
      return;
    }

    try {
      setContentValidationLoading(true);
      setContentValidation(null);
      setContentMetadata(null);
      const result = await mediacore.validateContentIdForPod(contentId.trim());
      setContentValidation(result);

      // If valid, automatically fetch metadata
      if (result.isValid) {
        await handleGetContentMetadata();
      }
    } catch (error_) {
      setContentValidation({ error: toDisplayError(error_), isValid: false });
      toast.error(`Failed to validate content ID: ${toDisplayError(error_)}`);
    } finally {
      setContentValidationLoading(false);
    }
  };

  const handleGetContentMetadata = async () => {
    if (!contentId.trim()) return;

    try {
      setContentMetadataLoading(true);
      const metadata = await mediacore.getContentMetadata(contentId.trim());
      setContentMetadata(metadata);

      // Auto-fill pod name if empty
      if (!newPodName.trim() && metadata) {
        setNewPodName(`${metadata.artist} - ${metadata.title}`);
      }
    } catch (error_) {
      toast.error(`Failed to get content metadata: ${toDisplayError(error_)}`);
      setContentMetadata(null);
    } finally {
      setContentMetadataLoading(false);
    }
  };

  const handleSearchContent = async () => {
    if (!contentSearchQuery.trim()) return;

    try {
      setContentSearchLoading(true);
      setContentSearchError(null);
      setContentSearchResults([]);
      const results = await mediacore.searchContent(
        contentSearchQuery.trim(),
        null,
        10,
      );
      setContentSearchResults(results);
    } catch (error_) {
      toast.error(`Failed to search content: ${toDisplayError(error_)}`);
      setContentSearchError(toDisplayError(error_, 'Failed to search content'));
      setContentSearchResults([]);
    } finally {
      setContentSearchLoading(false);
    }
  };

  const handleCreateContentLinkedPod = async () => {
    if (!contentId.trim()) {
      toast.error(interfaceText("Content ID is required"));
      return;
    }

    if (!newPodName.trim()) {
      toast.error(interfaceText("Pod name is required"));
      return;
    }

    if (!contentValidation?.isValid) {
      toast.error(interfaceText("Please validate the content ID first"));
      return;
    }

    try {
      setCreatePodLoading(true);
      const podRequest = {
        channels: [
          {
            channelId: 'general',
            kind: 'General',
            name: 'General',
          },
        ],

        contentId: contentId.trim(),

        externalBindings: [],
        // Auto-generate
        name: newPodName.trim(),
        podId: '',
        tags: [],
        visibility: newPodVisibility,
      };

      const createdPod = await mediacore.createContentLinkedPod(podRequest);
      toast.success(interfaceText("Pod \"{name}\" created successfully!", { "name": (createdPod.name) }));

      // Reset form
      setContentId('');
      setContentValidation(null);
      setContentMetadata(null);
      setNewPodName('');
      setContentSearchQuery('');
      setContentSearchResults([]);
    } catch (error_) {
      toast.error(`Failed to create pod: ${toDisplayError(error_)}`);
    } finally {
      setCreatePodLoading(false);
    }
  };

  const selectContentFromSearch = (contentItem) => {
    setContentId(contentItem.contentId);
    setContentSearchQuery('');
    setContentSearchResults([]);
  };


  return (
        <Grid.Column style={{ display: visible ? undefined : 'none' }} width={16}>
          <Card id="pod-content-linking" fluid>
            <Card.Content>
              <Card.Header>
                <Icon name="linkify" />
                <LocalizedText source={"Pod Content Linking"} /></Card.Header>
              <Card.Description>
                <LocalizedText source={"Create pods linked to specific content (music, videos, etc.) for focused discussions"} /></Card.Description>
              <PodWorkflowNotice title={interfaceText("Can create content-linked pods")} {...interfaceTextProps("Can create content-linked pods")}>
                <LocalizedText source={"Content search and validation are read-only. Creating a content-linked pod can publish content identifiers and pod metadata depending on visibility settings."} /></PodWorkflowNotice>
            </Card.Content>

            {/* Content Linking */}
            <Card.Content>
              <Header size="small"><LocalizedText source={"Content Search & Validation"} /></Header>

              {/* Content Search */}
              <Input
                action={
                  <Button
                    color="blue"
                    disabled={!contentSearchQuery.trim()}
                    loading={contentSearchLoading}
                    onClick={() => handleSearchContent()}
                  >
                    <LocalizedText source={"Search"} /></Button>
                }
                onChange={(e) => setContentSearchQuery(e.target.value)}
                placeholder={interfaceText("Search for content (artist, album, movie, etc.)")}
                style={{ marginBottom: '1em', width: '100%' }}
                value={contentSearchQuery}
               {...interfaceTextProps("Search for content (artist, album, movie, etc.)")}/>

              {/* Search Results */}
              {contentSearchError && (
                <Message
                  data-testid="content-search-error"
                  negative
                  size="small"
                >
                  {contentSearchError}
                </Message>
              )}

              {contentSearchResults.length > 0 && (
                <div style={{ marginBottom: '1em' }}>
                  <Header size="tiny"><LocalizedText source={"Search Results"} /></Header>
                  {contentSearchResults.map((item, index) => (
                    <Card
                      key={index}
                      onClick={() => selectContentFromSearch(item)}
                      style={{ cursor: 'pointer', marginBottom: '0.5em' }}
                    >
                      <Card.Content style={{ padding: '0.5em' }}>
                        <strong>{item.title}</strong>
                        {item.subtitle && <div>{item.subtitle}</div>}
                        <small>
                          {item.domain} • {item.type}
                        </small>
                      </Card.Content>
                    </Card>
                  ))}
                </div>
              )}

              {/* Content Validation */}
              <Input
                action={
                  <Button
                    color="green"
                    disabled={!contentId.trim()}
                    loading={contentValidationLoading}
                    onClick={() => handleValidateContentId()}
                  >
                    <LocalizedText source={"Validate"} /></Button>
                }
                onChange={(e) => setContentId(e.target.value)}
                placeholder={interfaceText("Content ID (e.g., content:audio:album:mb-release-id)")}
                style={{ marginBottom: '1em', width: '100%' }}
                value={contentId}
               {...interfaceTextProps("Content ID (e.g., content:audio:album:mb-release-id)")}/>

              {/* Validation Result */}
              {contentValidation && (
                <Message
                  negative={!contentValidation.isValid}
                  positive={contentValidation.isValid}
                  size="small"
                  style={{ marginBottom: '1em' }}
                >
                  <Message.Header>
                    {contentValidation.isValid
                      ? <LocalizedText source={"✓ Valid Content ID"} />
                      : <LocalizedText source={"✗ Invalid Content ID"} />}
                  </Message.Header>
                  {!contentValidation.isValid &&
                    contentValidation.errorMessage && (
                      <p>{contentValidation.errorMessage}</p>
                    )}
                </Message>
              )}

              {/* Content Metadata */}
              {contentMetadata && (
                <Message
                  info
                  size="small"
                  style={{ marginBottom: '1em' }}
                >
                  <Message.Header><LocalizedText source={"Content Metadata"} /></Message.Header>
                  <p>
                    <strong><LocalizedText source={"Title:"} /></strong> {contentMetadata.title}
                    <br />
                    <strong><LocalizedText source={"Artist:"} /></strong> {contentMetadata.artist}
                    <br />
                    <strong><LocalizedText source={"Type:"} /></strong> {contentMetadata.type} (
                    {contentMetadata.domain})
                  </p>
                </Message>
              )}

              {/* Pod Creation */}
              {contentValidation?.isValid && (
                <div>
                  <Header size="small"><LocalizedText source={"Create Content-Linked Pod"} /></Header>

                  <Input
                    onChange={(e) => setNewPodName(e.target.value)}
                    placeholder={interfaceText("Pod name (auto-filled from content)")}
                    style={{ marginBottom: '1em', width: '100%' }}
                    value={newPodName}
                   {...interfaceTextProps("Pod name (auto-filled from content)")}/>

                  <div style={{ marginBottom: '1em' }}>
                    <label
                      htmlFor="media-core-new-pod-visibility"
                      style={{ marginRight: '1em' }}
                    >
                      <LocalizedText source={"Visibility:"} /></label>
                    <select
                      id="media-core-new-pod-visibility"
                      onChange={(e) => setNewPodVisibility(e.target.value)}
                      value={newPodVisibility}
                    >
                      <option value="Unlisted"><LocalizedText source={"Unlisted"} /></option>
                      <option value="Listed"><LocalizedText source={"Listed"} /></option>
                      <option value="Private"><LocalizedText source={"Private"} /></option>
                    </select>
                  </div>

                  <Button
                    color="teal"
                    disabled={!newPodName.trim()}
                    loading={createPodLoading}
                    onClick={() => handleCreateContentLinkedPod()}
                  >
                    <LocalizedText source={"Create Content-Linked Pod"} /></Button>
                </div>
              )}
            </Card.Content>
          </Card>
        </Grid.Column>

  );
};

export default React.memo(PodContentLinkingPanel);
