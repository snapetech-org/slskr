import LocalizedText from "../../Shared/LocalizedText";
import { interfaceText, interfaceTextProps, useInterfaceLanguage } from "../../../lib/interfaceLocale";


import { formatRegionalDateTime, useRegionalFormat } from '../../../lib/util';
import * as mediacore from '../../../lib/mediacore';
import { toDisplayError } from '../../../lib/errors';
import Button from './MediaCoreButton';
import PodWorkflowNotice from './PodWorkflowNotice';
import React, { useEffect, useRef } from 'react';
import { toast } from 'react-toastify';
import {
  Card,
  Form,
  Grid,
  Header,
  Icon,
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

const PodDiscoveryPanel = ({ visible = true }) => {
  useInterfaceLanguage();
  useRegionalFormat();
  const mountedRef = useRef(true);

  useEffect(() => {
    mountedRef.current = true;
    return () => {
      mountedRef.current = false;
    };
  }, []);

  // Pod Discovery states
  const [podToRegister, setPodToRegister] = useMountedState(mountedRef, '');
  const [registeringPod, setRegisteringPod] = useMountedState(mountedRef, false);
  const [podRegistrationResult, setPodRegistrationResult] = useMountedState(mountedRef, null);
  const [podToUnregister, setPodToUnregister] = useMountedState(mountedRef, '');
  const [unregisteringPod, setUnregisteringPod] = useMountedState(mountedRef, false);
  const [podUnregistrationResult, setPodUnregistrationResult] = useMountedState(mountedRef, null);
  const [discoverByName, setDiscoverByName] = useMountedState(mountedRef, '');
  const [discoveringByName, setDiscoveringByName] = useMountedState(mountedRef, false);
  const [nameDiscoveryResult, setNameDiscoveryResult] = useMountedState(mountedRef, null);
  const [discoverByTag, setDiscoverByTag] = useMountedState(mountedRef, '');
  const [discoveringByTag, setDiscoveringByTag] = useMountedState(mountedRef, false);
  const [tagDiscoveryResult, setTagDiscoveryResult] = useMountedState(mountedRef, null);
  const [discoverTags, setDiscoverTags] = useMountedState(mountedRef, '');
  const [discoveringByTags, setDiscoveringByTags] = useMountedState(mountedRef, false);
  const [tagsDiscoveryResult, setTagsDiscoveryResult] = useMountedState(mountedRef, null);
  const [discoverLimit, setDiscoverLimit] = useMountedState(mountedRef, 50);
  const [discoveringAll, setDiscoveringAll] = useMountedState(mountedRef, false);
  const [allDiscoveryResult, setAllDiscoveryResult] = useMountedState(mountedRef, null);
  const [discoverByContent, setDiscoverByContent] = useMountedState(mountedRef, '');
  const [discoveringByContent, setDiscoveringByContent] = useMountedState(mountedRef, false);
  const [contentDiscoveryResult, setContentDiscoveryResult] = useMountedState(mountedRef, null);
  const [discoveryStats, setDiscoveryStats] = useMountedState(mountedRef, null);
  const [loadingDiscoveryStats, setLoadingDiscoveryStats] = useMountedState(mountedRef, false);


  const handleRegisterPodForDiscovery = async () => {
    if (!podToRegister.trim()) {
      toast.warning(interfaceText("Please enter pod JSON data"));
      return;
    }

    try {
      setRegisteringPod(true);
      setPodRegistrationResult(null);
      const pod = JSON.parse(podToRegister);
      const result = await mediacore.registerPodForDiscovery(pod);
      setPodRegistrationResult(result);
      setPodToRegister('');
    } catch (error_) {
      setPodRegistrationResult({ error: toDisplayError(error_) });
    } finally {
      setRegisteringPod(false);
    }
  };

  const handleUnregisterPodFromDiscovery = async () => {
    if (!podToUnregister.trim()) {
      toast.warning(interfaceText("Please enter a pod ID"));
      return;
    }

    try {
      setUnregisteringPod(true);
      setPodUnregistrationResult(null);
      const result =
        await mediacore.unregisterPodFromDiscovery(podToUnregister);
      setPodUnregistrationResult(result);
      setPodToUnregister('');
    } catch (error_) {
      setPodUnregistrationResult({ error: toDisplayError(error_) });
    } finally {
      setUnregisteringPod(false);
    }
  };

  const handleDiscoverByName = async () => {
    if (!discoverByName.trim()) {
      toast.warning(interfaceText("Please enter a pod name"));
      return;
    }

    try {
      setDiscoveringByName(true);
      setNameDiscoveryResult(null);
      const result = await mediacore.discoverPodsByName(discoverByName);
      setNameDiscoveryResult(result);
    } catch (error_) {
      setNameDiscoveryResult({ error: toDisplayError(error_) });
    } finally {
      setDiscoveringByName(false);
    }
  };

  const handleDiscoverByTag = async () => {
    if (!discoverByTag.trim()) {
      toast.warning(interfaceText("Please enter a tag"));
      return;
    }

    try {
      setDiscoveringByTag(true);
      setTagDiscoveryResult(null);
      const result = await mediacore.discoverPodsByTag(discoverByTag);
      setTagDiscoveryResult(result);
    } catch (error_) {
      setTagDiscoveryResult({ error: toDisplayError(error_) });
    } finally {
      setDiscoveringByTag(false);
    }
  };

  const handleDiscoverByTags = async () => {
    if (!discoverTags.trim()) {
      toast.warning(interfaceText("Please enter tags (comma-separated)"));
      return;
    }

    try {
      setDiscoveringByTags(true);
      setTagsDiscoveryResult(null);
      const tagList = discoverTags
        .split(',')
        .map((t) => t.trim())
        .filter(Boolean);
      const result = await mediacore.discoverPodsByTags(tagList);
      setTagsDiscoveryResult(result);
    } catch (error_) {
      setTagsDiscoveryResult({ error: toDisplayError(error_) });
    } finally {
      setDiscoveringByTags(false);
    }
  };

  const handleDiscoverAll = async () => {
    try {
      setDiscoveringAll(true);
      setAllDiscoveryResult(null);
      const result = await mediacore.discoverAllPods(discoverLimit);
      setAllDiscoveryResult(result);
    } catch (error_) {
      setAllDiscoveryResult({ error: toDisplayError(error_) });
    } finally {
      setDiscoveringAll(false);
    }
  };

  const handleDiscoverByContent = async () => {
    if (!discoverByContent.trim()) {
      toast.warning(interfaceText("Please enter a content ID"));
      return;
    }

    try {
      setDiscoveringByContent(true);
      setContentDiscoveryResult(null);
      const result = await mediacore.discoverPodsByContent(discoverByContent);
      setContentDiscoveryResult(result);
    } catch (error_) {
      setContentDiscoveryResult({ error: toDisplayError(error_) });
    } finally {
      setDiscoveringByContent(false);
    }
  };

  const handleLoadDiscoveryStats = async () => {
    try {
      setLoadingDiscoveryStats(true);
      setDiscoveryStats(null);
      const result = await mediacore.getPodDiscoveryStats();
      setDiscoveryStats(result);
    } catch (error_) {
      setDiscoveryStats({ error: toDisplayError(error_) });
    } finally {
      setLoadingDiscoveryStats(false);
    }
  };

  const handleRefreshDiscovery = async () => {
    try {
      const result = await mediacore.refreshPodDiscovery();
      toast.success(
        interfaceText("Discovery refresh completed: {entriesRefreshed} refreshed, {entriesExpired} expired", { "entriesRefreshed": (result.entriesRefreshed), "entriesExpired": (result.entriesExpired) }),
      );
      // Reload stats to reflect changes
      await handleLoadDiscoveryStats();
    } catch (error_) {
      toast.error(`Failed to refresh discovery: ${toDisplayError(error_)}`);
    }
  };


  return (
        <Grid.Column style={{ display: visible ? undefined : 'none' }} width={16}>
          <Card id="pod-discovery" fluid>
            <Card.Content>
              <Card.Header>
                <Icon name="search" />
                <LocalizedText source={"Pod Discovery"} /></Card.Header>
              <Card.Description>
                <LocalizedText source={"Discover pods via DHT using name slugs, tags, and content associations"} /></Card.Description>
              <PodWorkflowNotice
                color="blue"
                icon="info circle"
                title={interfaceText("Mostly read-only discovery")}
               {...interfaceTextProps("Mostly read-only discovery")}>
                <LocalizedText source={"Search operations are read-only, but registering, updating, unregistering, or refreshing discovery data changes public pod discovery state."} /></PodWorkflowNotice>
            </Card.Content>

            {/* Pod Registration */}
            <Card.Content>
              <Header size="small"><LocalizedText source={"Register Pod for Discovery"} /></Header>
              <Form>
                <Form.TextArea
                  label={interfaceText("Pod JSON (must have Visibility: Listed)")}
                  onChange={(e) => setPodToRegister(e.target.value)}
                  placeholder='{"podId": "pod:artist:mb:daft-punk-hash", "name": "Daft Punk Fans", "visibility": "Listed", "focusContentId": "content:audio:artist:daft-punk", "tags": ["electronic", "french-house"]}'
                  rows={3}
                  value={podToRegister}
                 {...interfaceTextProps("Pod JSON (must have Visibility: Listed)")}/>
                <Button
                  disabled={registeringPod || !podToRegister.trim()}
                  loading={registeringPod}
                  onClick={handleRegisterPodForDiscovery}
                  primary
                >
                  <LocalizedText source={"Register Pod"} /></Button>
              </Form>

              {podRegistrationResult && (
                <div style={{ marginTop: '1em' }}>
                  {podRegistrationResult.error ? (
                    <Message error>
                      <p>
                        <LocalizedText source={"Failed to register pod:"} />{" "}{podRegistrationResult.error}
                      </p>
                    </Message>
                  ) : (
                    <Message success>
                      <Message.Header>
                        <LocalizedText source={"Pod Registered for Discovery"} /></Message.Header>
                      <p>
                        <strong><LocalizedText source={"Pod ID:"} /></strong> {podRegistrationResult.podId}
                        <br />
                        <strong><LocalizedText source={"Discovery Keys:"} /></strong>{' '}
                        {podRegistrationResult.discoveryKeys?.join(', ')}
                        <br />
                        <strong><LocalizedText source={"Registered:"} /></strong>{' '}
                        {formatRegionalDateTime(podRegistrationResult.registeredAt)}
                        <br />
                        <strong><LocalizedText source={"Expires:"} /></strong>{' '}
                        {formatRegionalDateTime(podRegistrationResult.expiresAt)}
                      </p>
                    </Message>
                  )}
                </div>
              )}
            </Card.Content>

            <Card.Content>
              <Header size="small"><LocalizedText source={"Unregister Pod from Discovery"} /></Header>
              <Form>
                <Form.Input
                  label={interfaceText("Pod ID")}
                  onChange={(e) => setPodToUnregister(e.target.value)}
                  placeholder="pod:artist:mb:daft-punk-hash"
                  value={podToUnregister}
                 {...interfaceTextProps("Pod ID")}/>
                <Button
                  color="red"
                  disabled={unregisteringPod || !podToUnregister.trim()}
                  loading={unregisteringPod}
                  onClick={handleUnregisterPodFromDiscovery}
                >
                  <LocalizedText source={"Unregister Pod"} /></Button>
              </Form>

              {podUnregistrationResult && (
                <div style={{ marginTop: '1em' }}>
                  {podUnregistrationResult.error ? (
                    <Message error>
                      <p>
                        <LocalizedText source={"Failed to unregister pod:"} />{' '}
                        {podUnregistrationResult.error}
                      </p>
                    </Message>
                  ) : (
                    <Message success>
                      <p><LocalizedText source={"Pod unregistered from discovery successfully"} /></p>
                    </Message>
                  )}
                </div>
              )}
            </Card.Content>

            <Card.Content>
              <Grid>
                <Grid.Column width={4}>
                  {/* Discover by Name */}
                  <Header size="small"><LocalizedText source={"By Name"} /></Header>
                  <Form>
                    <Form.Input
                      onChange={(e) => setDiscoverByName(e.target.value)}
                      placeholder="daft-punk-fans"
                      value={discoverByName}
                    />
                    <Button
                      disabled={discoveringByName || !discoverByName.trim()}
                      fluid
                      loading={discoveringByName}
                      onClick={handleDiscoverByName}
                    >
                      <LocalizedText source={"Discover"} /></Button>
                  </Form>

                  {nameDiscoveryResult && (
                    <div style={{ marginTop: '0.5em' }}>
                      {nameDiscoveryResult.error ? (
                        <Message
                          error
                          size="tiny"
                        >
                          <p>{nameDiscoveryResult.error}</p>
                        </Message>
                      ) : (
                        <Message
                          size="tiny"
                          success
                        >
                          <p><LocalizedText source={"Found"} />{" "}{nameDiscoveryResult.totalFound} <LocalizedText source={"pods"} /></p>
                        </Message>
                      )}
                    </div>
                  )}
                </Grid.Column>

                <Grid.Column width={4}>
                  {/* Discover by Tag */}
                  <Header size="small"><LocalizedText source={"By Tag"} /></Header>
                  <Form>
                    <Form.Input
                      onChange={(e) => setDiscoverByTag(e.target.value)}
                      placeholder={interfaceText("electronic")}
                      value={discoverByTag}
                     {...interfaceTextProps("electronic")}/>
                    <Button
                      disabled={discoveringByTag || !discoverByTag.trim()}
                      fluid
                      loading={discoveringByTag}
                      onClick={handleDiscoverByTag}
                    >
                      <LocalizedText source={"Discover"} /></Button>
                  </Form>

                  {tagDiscoveryResult && (
                    <div style={{ marginTop: '0.5em' }}>
                      {tagDiscoveryResult.error ? (
                        <Message
                          error
                          size="tiny"
                        >
                          <p>{tagDiscoveryResult.error}</p>
                        </Message>
                      ) : (
                        <Message
                          size="tiny"
                          success
                        >
                          <p><LocalizedText source={"Found"} />{" "}{tagDiscoveryResult.totalFound} <LocalizedText source={"pods"} /></p>
                        </Message>
                      )}
                    </div>
                  )}
                </Grid.Column>

                <Grid.Column width={4}>
                  {/* Discover by Tags */}
                  <Header size="small"><LocalizedText source={"By Tags (AND)"} /></Header>
                  <Form>
                    <Form.Input
                      onChange={(e) => setDiscoverTags(e.target.value)}
                      placeholder={interfaceText("electronic,french-house")}
                      value={discoverTags}
                     {...interfaceTextProps("electronic,french-house")}/>
                    <Button
                      disabled={discoveringByTags || !discoverTags.trim()}
                      fluid
                      loading={discoveringByTags}
                      onClick={handleDiscoverByTags}
                    >
                      <LocalizedText source={"Discover"} /></Button>
                  </Form>

                  {tagsDiscoveryResult && (
                    <div style={{ marginTop: '0.5em' }}>
                      {tagsDiscoveryResult.error ? (
                        <Message
                          error
                          size="tiny"
                        >
                          <p>{tagsDiscoveryResult.error}</p>
                        </Message>
                      ) : (
                        <Message
                          size="tiny"
                          success
                        >
                          <p><LocalizedText source={"Found"} />{" "}{tagsDiscoveryResult.totalFound} <LocalizedText source={"pods"} /></p>
                        </Message>
                      )}
                    </div>
                  )}
                </Grid.Column>

                <Grid.Column width={4}>
                  {/* Discover All */}
                  <Header size="small"><LocalizedText source={"All Pods"} /></Header>
                  <Form>
                    <Form.Input
                      label={interfaceText("Limit")}
                      max="1000"
                      min="1"
                      onChange={(e) =>
                        setDiscoverLimit(Number.parseInt(e.target.value) || 50)
                      }
                      type="number"
                      value={discoverLimit}
                     {...interfaceTextProps("Limit")}/>
                    <Button
                      disabled={discoveringAll}
                      fluid
                      loading={discoveringAll}
                      onClick={handleDiscoverAll}
                    >
                      <LocalizedText source={"Discover"} /></Button>
                  </Form>

                  {allDiscoveryResult && (
                    <div style={{ marginTop: '0.5em' }}>
                      {allDiscoveryResult.error ? (
                        <Message
                          error
                          size="tiny"
                        >
                          <p>{allDiscoveryResult.error}</p>
                        </Message>
                      ) : (
                        <Message
                          size="tiny"
                          success
                        >
                          <p><LocalizedText source={"Found"} />{" "}{allDiscoveryResult.totalFound} <LocalizedText source={"pods"} /></p>
                        </Message>
                      )}
                    </div>
                  )}
                </Grid.Column>
              </Grid>
            </Card.Content>

            <Card.Content>
              <Grid>
                <Grid.Column width={8}>
                  {/* Discover by Content */}
                  <Header size="small"><LocalizedText source={"By Content ID"} /></Header>
                  <Form>
                    <Form.Input
                      onChange={(e) => setDiscoverByContent(e.target.value)}
                      placeholder="content:audio:artist:daft-punk"
                      value={discoverByContent}
                    />
                    <Button
                      disabled={
                        discoveringByContent || !discoverByContent.trim()
                      }
                      fluid
                      loading={discoveringByContent}
                      onClick={handleDiscoverByContent}
                    >
                      <LocalizedText source={"Discover"} /></Button>
                  </Form>

                  {contentDiscoveryResult && (
                    <div style={{ marginTop: '0.5em' }}>
                      {contentDiscoveryResult.error ? (
                        <Message
                          error
                          size="tiny"
                        >
                          <p>{contentDiscoveryResult.error}</p>
                        </Message>
                      ) : (
                        <Message
                          size="tiny"
                          success
                        >
                          <p><LocalizedText source={"Found"} />{" "}{contentDiscoveryResult.totalFound} <LocalizedText source={"pods"} /></p>
                        </Message>
                      )}
                    </div>
                  )}
                </Grid.Column>

                <Grid.Column width={8}>
                  {/* Discovery Stats */}
                  <Header size="small"><LocalizedText source={"Discovery Statistics"} /></Header>
                  <Button.Group fluid>
                    <Button
                      disabled={loadingDiscoveryStats}
                      loading={loadingDiscoveryStats}
                      onClick={handleLoadDiscoveryStats}
                    >
                      <LocalizedText source={"Load Stats"} /></Button>
                    <Button
                      color="blue"
                      onClick={handleRefreshDiscovery}
                    >
                      <LocalizedText source={"Refresh"} /></Button>
                  </Button.Group>

                  {discoveryStats && !discoveryStats.error && (
                    <div style={{ marginTop: '0.5em' }}>
                      <Message size="tiny">
                        <p>
                          <strong><LocalizedText source={"Registered Pods:"} /></strong>{' '}
                          {discoveryStats.totalRegisteredPods}
                          <br />
                          <strong><LocalizedText source={"Active Entries:"} /></strong>{' '}
                          {discoveryStats.activeDiscoveryEntries}
                          <br />
                          <strong><LocalizedText source={"Expired Entries:"} /></strong>{' '}
                          {discoveryStats.expiredEntries}
                          <br />
                          <strong><LocalizedText source={"Avg Search Time:"} /></strong>{' '}
                          {discoveryStats.averageDiscoveryTime?.totalMilliseconds.toFixed(
                            0,
                          )}
                          <LocalizedText source={"ms"} /></p>
                      </Message>
                    </div>
                  )}

                  {discoveryStats?.error && (
                    <Message
                      error
                      size="tiny"
                      style={{ marginTop: '0.5em' }}
                    >
                      <p>{discoveryStats.error}</p>
                    </Message>
                  )}
                </Grid.Column>
              </Grid>
            </Card.Content>
          </Card>
        </Grid.Column>

  );
};

export default React.memo(PodDiscoveryPanel);
