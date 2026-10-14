import LocalizedText from "../../Shared/LocalizedText";
import { interfaceText, interfaceTextProps, useInterfaceLanguage } from "../../../lib/interfaceLocale";
import {
  buildMediaServerExecutionContract,
  buildMediaServerPathDiagnostic,
  buildMediaServerSyncPreview,
  formatMediaServerExecutionContractReport,
  formatMediaServerSyncReport,
  mediaServerAutomationContracts,
  mediaServerAdapters,
} from '../../../lib/mediaServerIntegrations';
import { useState } from 'react';
import {
  Button,
  Card,
  Checkbox,
  Header,
  Icon,
  Input,
  Label,
  Message,
  Popup,
  Segment,
  Table,
} from 'semantic-ui-react';
import { useAsyncGuard } from './integrationsShared';

const MediaServerPanel = () => {
  useInterfaceLanguage();
  const [activeAdapterId, setActiveAdapterId] = useState(mediaServerAdapters[0].id);
  const [automationEnabled, setAutomationEnabled] = useState(() =>
    mediaServerAutomationContracts.reduce(
      (accumulator, automation) => ({
        ...accumulator,
        [automation.id]:
          automation.id === 'playHistoryImport' || automation.id === 'completedScan',
      }),
      {},
    ),
  );
  const [baseUrl, setBaseUrl] = useState('');
  const [confirmationRequired, setConfirmationRequired] = useState(true);
  const [dedupeWindowHours, setDedupeWindowHours] = useState('24');
  const [localPath, setLocalPath] = useState('');
  const [rateLimitPerMinute, setRateLimitPerMinute] = useState('6');
  const [serverPath, setServerPath] = useState('');
  const [remotePathFrom, setRemotePathFrom] = useState('');
  const [remotePathTo, setRemotePathTo] = useState('');
  const [tokenConfigured, setTokenConfigured] = useState(false);
  const [userMappingConfigured, setUserMappingConfigured] = useState(false);
  const [copyStatus, setCopyStatus] = useState('');
  const asyncGuard = useAsyncGuard();
  const diagnostic = buildMediaServerPathDiagnostic({
    localPath,
    remotePathFrom,
    remotePathTo,
    serverPath,
  });
  const syncPreview = buildMediaServerSyncPreview({
    adapterId: activeAdapterId,
    baseUrl,
    localPath,
    remotePathFrom,
    remotePathTo,
    serverPath,
    tokenConfigured,
  });
  const executionContract = buildMediaServerExecutionContract({
    confirmationRequired,
    dedupeWindowHours,
    enabledAutomations: automationEnabled,
    rateLimitPerMinute,
    syncPreview,
    userMappingConfigured,
  });

  const copySyncReport = async () => {
    const requestId = asyncGuard.begin();
    if (requestId === null) return;
    const report = formatMediaServerSyncReport(syncPreview);
    if (!navigator.clipboard?.writeText) {
      if (asyncGuard.isCurrent(requestId)) {
        setCopyStatus(interfaceText('Clipboard unavailable; copy the report from the preview text.'));
      }
      asyncGuard.finish(requestId);
      return;
    }

    try {
      await navigator.clipboard.writeText(report);
      if (asyncGuard.isCurrent(requestId)) {
        setCopyStatus(interfaceText('Media-server sync review copied.'));
      }
    } catch {
      if (asyncGuard.isCurrent(requestId)) {
        setCopyStatus(interfaceText('Unable to copy media-server sync review.'));
      }
    } finally {
      asyncGuard.finish(requestId);
    }
  };

  const copyExecutionContract = async () => {
    const requestId = asyncGuard.begin();
    if (requestId === null) return;
    const report = formatMediaServerExecutionContractReport(executionContract);
    if (!navigator.clipboard?.writeText) {
      if (asyncGuard.isCurrent(requestId)) {
        setCopyStatus(interfaceText('Clipboard unavailable; copy the execution contract manually.'));
      }
      asyncGuard.finish(requestId);
      return;
    }

    try {
      await navigator.clipboard.writeText(report);
      if (asyncGuard.isCurrent(requestId)) {
        setCopyStatus(interfaceText('Media-server execution contract copied.'));
      }
    } catch {
      if (asyncGuard.isCurrent(requestId)) {
        setCopyStatus(interfaceText('Unable to copy media-server execution contract.'));
      }
    } finally {
      asyncGuard.finish(requestId);
    }
  };

  const toggleAutomation = (automationId, checked) => {
    setAutomationEnabled((current) => ({
      ...current,
      [automationId]: Boolean(checked),
    }));
  };

  return (
    <Card fluid>
      <Card.Content>
        <Card.Header>
          <Icon name="server" />
          <LocalizedText source={"Media Servers"} /></Card.Header>
        <Card.Meta>
          <LocalizedText source={"Optional Plex, Jellyfin/Emby, and Navidrome integration planning and path diagnostics."} /></Card.Meta>
      </Card.Content>
      <Card.Content>
        <Card.Group
          itemsPerRow={3}
          stackable
        >
          {mediaServerAdapters.map((adapter) => (
            <Card
              className="media-server-adapter-card"
              key={adapter.id}
            >
              <Card.Content>
                <Card.Header><LocalizedText source={adapter.label} /></Card.Header>
                <Card.Meta>
                  {adapter.requiresToken ? <LocalizedText source={"Token required"} /> : <LocalizedText source={"No token required"} />}
                </Card.Meta>
                <div className="integration-status-row">
                  {adapter.capabilities.map((capability) => (
                    <Label
                      basic
                      key={interfaceText(capability)}
                      size="tiny"
                    >
                      {interfaceText(capability)}
                    </Label>
                  ))}
                </div>
                <Popup
                  content={interfaceText("Review {label} sync readiness. This is local planning only and does not contact the media server.", { label: interfaceText(adapter.label) })}
                  position="top center"
                  trigger={
                    <Button
                      aria-label={interfaceText("Review {label} sync readiness", { label: interfaceText(adapter.label) })}
                      basic={activeAdapterId !== adapter.id}
                      color={activeAdapterId === adapter.id ? 'purple' : undefined}
                      onClick={() => setActiveAdapterId(adapter.id)}
                      size="tiny"
                     {...interfaceTextProps("Review {label} sync readiness")}>
                      <Icon name="clipboard check" />
                      <LocalizedText source={"Review"} /></Button>
                  }
                 {...interfaceTextProps("Review {label} sync readiness. This is local planning only and does not contact the media server.")}/>
              </Card.Content>
            </Card>
          ))}
        </Card.Group>

        <Segment className="integration-manual-import">
          <Header as="h4"><LocalizedText source={"Path Diagnostics"} /></Header>
          <p>
            <LocalizedText source={"Check whether a completed file path reported by slskr maps to the path a media server can scan."} /></p>
          <div className="media-server-path-grid">
            <Input
              aria-label={interfaceText("Media server base URL")}
              fluid
              label={interfaceText("Server URL")}
              onChange={(_, { value }) => setBaseUrl(value)}
              placeholder="http://media.example.invalid"
              value={baseUrl}
             {...interfaceTextProps("Media server base URL")}/>
            <Checkbox
              aria-label={interfaceText("Media server token configured")}
              checked={tokenConfigured}
              label={interfaceText("API token stored")}
              onChange={(_, { checked }) => setTokenConfigured(Boolean(checked))}
              toggle
             {...interfaceTextProps("Media server token configured")}/>
            <Input
              aria-label={interfaceText("slskr local file path")}
              fluid
              label={interfaceText("slskr path")}
              onChange={(_, { value }) => setLocalPath(value)}
              placeholder="/downloads/complete/Artist/Album/track.flac"
              value={localPath}
             {...interfaceTextProps("slskr local file path")}/>
            <Input
              aria-label={interfaceText("Media server file path")}
              fluid
              label={interfaceText("Server path")}
              onChange={(_, { value }) => setServerPath(value)}
              placeholder="/library/music/Artist/Album/track.flac"
              value={serverPath}
             {...interfaceTextProps("Media server file path")}/>
            <Input
              aria-label={interfaceText("Remote path map from")}
              fluid
              label={interfaceText("Map from")}
              onChange={(_, { value }) => setRemotePathFrom(value)}
              placeholder="/downloads/complete"
              value={remotePathFrom}
             {...interfaceTextProps("Remote path map from")}/>
            <Input
              aria-label={interfaceText("Remote path map to")}
              fluid
              label={interfaceText("Map to")}
              onChange={(_, { value }) => setRemotePathTo(value)}
              placeholder="/library/music"
              value={remotePathTo}
             {...interfaceTextProps("Remote path map to")}/>
          </div>
          <Message
            color={diagnostic.color}
            size="small"
          >
            <Message.Header><LocalizedText source={diagnostic.status} /></Message.Header>
            <p><LocalizedText source={diagnostic.message} /></p>
            {diagnostic.mappedPath && <p><LocalizedText source={"Mapped path:"} />{" "}{diagnostic.mappedPath}</p>}
          </Message>
        </Segment>

        <Segment className="media-server-sync-preview">
          <div className="integration-section-header">
            <Header as="h4">
              <Icon name="clipboard list" />
              <LocalizedText source={"Sync Review Plan"} /></Header>
            <Popup
              content={interfaceText("Copy the local media-server readiness report. This does not call Plex, Jellyfin, Emby, or Navidrome.")}
              position="top center"
              trigger={
                <Button
                  aria-label={interfaceText("Copy media-server sync review")}
                  onClick={copySyncReport}
                  size="small"
                 {...interfaceTextProps("Copy media-server sync review")}>
                  <Icon name="copy" />
                  <LocalizedText source={"Copy Plan"} /></Button>
              }
             {...interfaceTextProps("Copy the local media-server readiness report. This does not call Plex, Jellyfin, Emby, or Navidrome.")}/>
          </div>
          <div className="integration-status-row">
            <Label color={syncPreview.status === 'Ready for live adapter' ? 'green' : 'orange'}>
              <Icon
                name={
                  syncPreview.status === 'Ready for live adapter'
                    ? 'check circle'
                    : 'warning sign'
                }
              />
              <LocalizedText source={syncPreview.status} />
            </Label>
            <Label color="purple"><LocalizedText source={syncPreview.adapter.label} /></Label>
            <Label>
              {syncPreview.readyCount}/{syncPreview.total} <LocalizedText source={"checks ready"} /></Label>
          </div>
          <Table
            aria-label={interfaceText("Media server synchronization review plan")}
            celled
            compact
            tabIndex={0}
           {...interfaceTextProps("Media server synchronization review plan")}>
            <Table.Body>
              {syncPreview.checks.map((check) => (
                <Table.Row key={check.label}>
                  <Table.Cell><LocalizedText source={check.label} /></Table.Cell>
                  <Table.Cell>
                    <Label color={check.ready ? 'green' : 'orange'}>
                      {check.ready ? <LocalizedText source={"Ready"} /> : <LocalizedText source={"Todo"} />}
                    </Label>
                  </Table.Cell>
                  <Table.Cell>{check.ready ? <LocalizedText source={"No action needed."} /> : check.action}</Table.Cell>
                </Table.Row>
              ))}
            </Table.Body>
          </Table>
          {copyStatus && (
            <Message
              info
              size="small"
            >
              {copyStatus}
            </Message>
          )}
        </Segment>

        <Segment className="media-server-sync-preview">
          <div className="integration-section-header">
            <Header as="h4">
              <Icon name="tasks" />
              <LocalizedText source={"Live Execution Contracts"} /></Header>
            <Popup
              content={interfaceText("Copy the live media-server execution contract. This documents enabled automations, blockers, rate limits, dedupe, and confirmation gates without calling a media server.")}
              position="top center"
              trigger={
                <Button
                  aria-label={interfaceText("Copy media-server execution contract")}
                  onClick={copyExecutionContract}
                  size="small"
                 {...interfaceTextProps("Copy media-server execution contract")}>
                  <Icon name="copy" />
                  <LocalizedText source={"Copy Contract"} /></Button>
              }
             {...interfaceTextProps("Copy the live media-server execution contract. This documents enabled automations, blockers, rate limits, dedupe, and confirmation gates without calling a media server.")}/>
          </div>
          <div className="integration-status-row">
            <Label
              color={
                executionContract.status === 'Execution contract ready'
                  ? 'green'
                  : 'orange'
              }
            >
              <Icon
                name={
                  executionContract.status === 'Execution contract ready'
                    ? 'check circle'
                    : 'warning sign'
                }
              />
              <LocalizedText source={executionContract.status} />
            </Label>
            <Label>
              {executionContract.readyCount}/{executionContract.total} <LocalizedText source={"checks ready"} /></Label>
            <Label>
              {executionContract.enabledReadyCount}/{executionContract.enabledCount}{' '}
              <LocalizedText source={"enabled automations ready"} /></Label>
          </div>
          <div className="media-server-path-grid">
            <Checkbox
              aria-label={interfaceText("Media server user mapping configured")}
              checked={userMappingConfigured}
              label={interfaceText("User mapping configured")}
              onChange={(_, { checked }) => setUserMappingConfigured(Boolean(checked))}
              toggle
             {...interfaceTextProps("Media server user mapping configured")}/>
            <Checkbox
              aria-label={interfaceText("Require confirmation before live media-server actions")}
              checked={confirmationRequired}
              label={interfaceText("Require confirmation gates")}
              onChange={(_, { checked }) => setConfirmationRequired(Boolean(checked))}
              toggle
             {...interfaceTextProps("Require confirmation before live media-server actions")}/>
            <Input
              aria-label={interfaceText("Media server rate limit per minute")}
              fluid
              label={interfaceText("Rate limit/min")}
              min={1}
              onChange={(_, { value }) => setRateLimitPerMinute(value)}
              type="number"
              value={rateLimitPerMinute}
             {...interfaceTextProps("Media server rate limit per minute")}/>
            <Input
              aria-label={interfaceText("Media server dedupe window hours")}
              fluid
              label={interfaceText("Dedupe hours")}
              min={1}
              onChange={(_, { value }) => setDedupeWindowHours(value)}
              type="number"
              value={dedupeWindowHours}
             {...interfaceTextProps("Media server dedupe window hours")}/>
          </div>
          <Table
            aria-label={interfaceText("Media server automation execution contracts")}
            celled
            compact
            tabIndex={0}
           {...interfaceTextProps("Media server automation execution contracts")}>
            <Table.Header>
              <Table.Row>
                <Table.HeaderCell><LocalizedText source={"Automation"} /></Table.HeaderCell>
                <Table.HeaderCell><LocalizedText source={"Enabled"} /></Table.HeaderCell>
                <Table.HeaderCell><LocalizedText source={"Readiness"} /></Table.HeaderCell>
                <Table.HeaderCell><LocalizedText source={"Contract"} /></Table.HeaderCell>
              </Table.Row>
            </Table.Header>
            <Table.Body>
              {executionContract.automations.map((automation) => (
                <Table.Row key={automation.id}>
                  <Table.Cell>
                    <strong>{automation.label}</strong>
                    <div className="integration-muted-copy">
                      {automation.description}
                    </div>
                  </Table.Cell>
                  <Table.Cell>
                    <Checkbox
                      aria-label={interfaceText("Enable {label}", { "label": (automation.label) })}
                      checked={automation.enabled}
                      onChange={(_, { checked }) =>
                        toggleAutomation(automation.id, checked)
                      }
                      toggle
                     {...interfaceTextProps("Enable {label}")}/>
                  </Table.Cell>
                  <Table.Cell>
                    <Label color={automation.ready ? 'green' : 'orange'}>
                      {automation.ready ? <LocalizedText source={"Ready"} /> : <LocalizedText source={"Blocked"} />}
                    </Label>
                  </Table.Cell>
                  <Table.Cell>
                    {automation.blockedReasons.length === 0
                      ? <LocalizedText source={"All required gates are satisfied."} />
                      : automation.blockedReasons.join(' ')}
                  </Table.Cell>
                </Table.Row>
              ))}
            </Table.Body>
          </Table>
          <Message
            info
            size="small"
          >
            <LocalizedText source={"Live execution remains disabled until a backend adapter consumes this contract. The Web UI exposes every automation toggle and blocker so enablement is visible before any media-server import, scrobble, acquisition queue, scan, or file action exists."} /></Message>
        </Segment>
      </Card.Content>
    </Card>
  );
};

export default MediaServerPanel;
