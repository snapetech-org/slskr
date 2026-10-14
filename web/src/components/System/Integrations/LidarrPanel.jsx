import LocalizedText from "../../Shared/LocalizedText";
import { interfaceText, interfaceTextProps, useInterfaceLanguage } from "../../../lib/interfaceLocale";
import * as lidarr from '../../../lib/lidarr';
import { toDisplayError } from '../../../lib/errors';
import { useMemo, useState } from 'react';
import {
  Button,
  Card,
  Header,
  Icon,
  Input,
  Label,
  Message,
  Popup,
  Segment,
  Table,
} from 'semantic-ui-react';
import {
  boolLabel,
  getLidarrOptions,
  getOption,
  useAsyncGuard,
  valueOrDash,
} from './integrationsShared';

const LidarrPanel = ({ options }) => {
  useInterfaceLanguage();
  const lidarrOptions = getLidarrOptions(options);
  const [status, setStatus] = useState(null);
  const [wanted, setWanted] = useState([]);
  const [importHistory, setImportHistory] = useState([]);
  const [syncResult, setSyncResult] = useState(null);
  const [importDirectory, setImportDirectory] = useState('');
  const [importResult, setImportResult] = useState(null);
  const [importRetryResult, setImportRetryResult] = useState(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState('');
  const asyncGuard = useAsyncGuard();
  const enabled = getOption(lidarrOptions, 'enabled', 'Enabled');

  const maskedApiKey = useMemo(() => {
    const apiKey = getOption(lidarrOptions, 'apiKey', 'ApiKey');
    return apiKey ? 'Configured' : 'Not configured';
  }, [lidarrOptions]);

  const run = async (name, action) => {
    const requestId = asyncGuard.begin();
    if (requestId === null) return;
    setLoading(name);
    setError('');

    try {
      await action(() => asyncGuard.isCurrent(requestId));
    } catch (error) {
      if (asyncGuard.isCurrent(requestId)) {
        setError(toDisplayError(error, 'Lidarr request failed'));
      }
    } finally {
      if (asyncGuard.isCurrent(requestId)) setLoading('');
      asyncGuard.finish(requestId);
    }
  };

  const loadImportHistory = async (isCurrent = () => true) => {
    const data = await lidarr.getImportHistory({ limit: 50 });
    if (isCurrent()) {
      setImportHistory(
        Array.isArray(data)
          ? data.filter(
              (record) =>
                record && typeof record === 'object' && !Array.isArray(record),
            )
          : [],
      );
    }
  };

  const retryImport = async (historyId) => {
    await run('retry', async (isCurrent) => {
      const result = await lidarr.retryImport(historyId);
      if (isCurrent()) setImportRetryResult(result);
      await loadImportHistory(isCurrent);
    });
  };

  return (
    <Card fluid>
      <Card.Content>
        <Card.Header>
          <Icon name="music" />
          <LocalizedText source={"Lidarr"} /></Card.Header>
        <Card.Meta><LocalizedText source={"Wanted-album sync and completed-download import bridge."} /></Card.Meta>
      </Card.Content>
      <Card.Content>
        <div className="integration-status-row">
          {boolLabel(enabled)}
          {boolLabel(
            getOption(lidarrOptions, 'syncWantedToWishlist', 'SyncWantedToWishlist'),
            'Wanted Sync',
            'Wanted Sync Off',
          )}
          {boolLabel(
            getOption(lidarrOptions, 'autoImportCompleted', 'AutoImportCompleted'),
            'Auto Import',
            'Auto Import Off',
          )}
          <Label>
            <Icon name={maskedApiKey === 'Configured' ? 'key' : 'warning sign'} />
            <LocalizedText source={"API Key"} />{" "}{maskedApiKey}
          </Label>
        </div>
        <Table
          basic="very"
          compact
          definition
        >
          <Table.Body>
            <Table.Row>
              <Table.Cell>URL</Table.Cell>
              <Table.Cell>{valueOrDash(getOption(lidarrOptions, 'url', 'Url'))}</Table.Cell>
            </Table.Row>
            <Table.Row>
              <Table.Cell><LocalizedText source={"Timeout"} /></Table.Cell>
              <Table.Cell>
                {valueOrDash(getOption(lidarrOptions, 'timeoutSeconds', 'TimeoutSeconds'))}
                {<LocalizedText source={"s"} />}
              </Table.Cell>
            </Table.Row>
            <Table.Row>
              <Table.Cell><LocalizedText source={"Sync Interval"} /></Table.Cell>
              <Table.Cell>
                {valueOrDash(getOption(lidarrOptions, 'syncIntervalSeconds', 'SyncIntervalSeconds'))}
                {<LocalizedText source={"s"} />}
              </Table.Cell>
            </Table.Row>
            <Table.Row>
              <Table.Cell><LocalizedText source={"Import Mode"} /></Table.Cell>
              <Table.Cell>{valueOrDash(getOption(lidarrOptions, 'importMode', 'ImportMode'))}</Table.Cell>
            </Table.Row>
            <Table.Row>
              <Table.Cell><LocalizedText source={"Import Path Map"} /></Table.Cell>
              <Table.Cell>
                {valueOrDash(getOption(lidarrOptions, 'importPathFrom', 'ImportPathFrom'))}
                {' -> '}
                {valueOrDash(getOption(lidarrOptions, 'importPathTo', 'ImportPathTo'))}
              </Table.Cell>
            </Table.Row>
          </Table.Body>
        </Table>
        {error && (
          <Message
            negative
            size="small"
          >
            {error}
          </Message>
        )}
        <div className="integration-actions">
          <Popup
            content={interfaceText("Fetch Lidarr system status using the configured URL and API key.")}
            trigger={
              <Button
                icon
                labelPosition="left"
                loading={loading === 'status'}
                onClick={() =>
                  run('status', async (isCurrent) => {
                    const result = await lidarr.getStatus();
                    if (isCurrent()) setStatus(result);
                  })
                }
              >
                <Icon name="heartbeat" />
                <LocalizedText source={"Check Status"} /></Button>
            }
           {...interfaceTextProps("Fetch Lidarr system status using the configured URL and API key.")}/>
          <Popup
            content={interfaceText("Preview Lidarr wanted albums that can be synced into slskr Wishlist.")}
            trigger={
              <Button
                icon
                labelPosition="left"
                loading={loading === 'wanted'}
                onClick={() =>
                  run('wanted', async (isCurrent) => {
                    const result = await lidarr.getWantedMissing({ pageSize: 25 });
                    if (isCurrent()) setWanted(Array.isArray(result) ? result : []);
                  })
                }
              >
                <Icon name="list" />
                <LocalizedText source={"Load Wanted"} /></Button>
            }
           {...interfaceTextProps("Preview Lidarr wanted albums that can be synced into slskr Wishlist.")}/>
          <Popup
            content={interfaceText("Create or refresh slskr Wishlist entries from Lidarr wanted albums.")}
            trigger={
              <Button
                icon
                labelPosition="left"
                loading={loading === 'sync'}
                onClick={() =>
                  run('sync', async (isCurrent) => {
                    const result = await lidarr.syncWanted();
                    if (isCurrent()) setSyncResult(result);
                  })
                }
                primary
              >
                <Icon name="sync" />
                <LocalizedText source={"Sync Wanted"} /></Button>
            }
           {...interfaceTextProps("Create or refresh slskr Wishlist entries from Lidarr wanted albums.")}/>
          <Popup
            content={interfaceText("Load the recent completed-download import history. Failed and skipped records can be retried when the recorded source is still available.")}
            trigger={
              <Button
                icon
                labelPosition="left"
                loading={loading === 'history'}
                onClick={() => run('history', loadImportHistory)}
              >
                <Icon name="history" />
                <LocalizedText source={"Load Import History"} /></Button>
            }
           {...interfaceTextProps("Load the recent completed-download import history. Failed and skipped records can be retried when the recorded source is still available.")}/>
        </div>
        {status && (
          <Message
            positive
            size="small"
          >
            <LocalizedText source={"Lidarr responded:"} />{" "}{status.appName || status.AppName || 'Lidarr'}{' '}
            {status.version || status.Version || ''}
          </Message>
        )}
        {syncResult && (
          <Message
            info
            size="small"
          >
            <LocalizedText source={"Wanted sync:"} />{" "}{syncResult.createdCount ?? syncResult.CreatedCount ?? 0} <LocalizedText source={"created,"} />{' '}
            {syncResult.duplicateCount ?? syncResult.DuplicateCount ?? 0} <LocalizedText source={"duplicates,"} />{' '}
            {syncResult.skippedCount ?? syncResult.SkippedCount ?? 0} <LocalizedText source={"skipped."} />
          </Message>
        )}
        {wanted.length > 0 && (
          <Table
            celled
            compact
          >
            <Table.Header>
              <Table.Row>
                <Table.HeaderCell><LocalizedText source={"Artist"} /></Table.HeaderCell>
                <Table.HeaderCell><LocalizedText source={"Album"} /></Table.HeaderCell>
              </Table.Row>
            </Table.Header>
            <Table.Body>
              {wanted.slice(0, 10).map((album) => (
                <Table.Row key={album.id || album.Id || `${album.title}-${album.foreignAlbumId}`}>
                  <Table.Cell>
                    {album.artist?.artistName || album.Artist?.ArtistName || '-'}
                  </Table.Cell>
                  <Table.Cell>{album.title || album.Title || '-'}</Table.Cell>
                </Table.Row>
              ))}
            </Table.Body>
          </Table>
        )}
        {importRetryResult && (
          <Message
            info
            size="small"
          >
            {importRetryResult.commandId || importRetryResult.CommandId
              ? (() => {
                const count = importRetryResult.safeCandidateCount || importRetryResult.SafeCandidateCount || 0;
                return count === 1
                  ? interfaceText('Lidarr import retry queued: {count} file', { count })
                  : interfaceText('Lidarr import retry queued: {count} files', { count });
              })()
              : importRetryResult.skippedReason ||
                importRetryResult.SkippedReason ||
                interfaceText('Lidarr could not find a safe file to import on retry')}
          </Message>
        )}
        {importHistory.length > 0 && (
          <Segment>
            <Header as="h4">
              <Icon name="history" />
              <LocalizedText source={"Import History"} /></Header>
            <Table
              celled
              compact
            >
              <Table.Header>
                <Table.Row>
                  <Table.HeaderCell><LocalizedText source={"Status"} /></Table.HeaderCell>
                  <Table.HeaderCell><LocalizedText source={"Directory"} /></Table.HeaderCell>
                  <Table.HeaderCell><LocalizedText source={"Completed"} /></Table.HeaderCell>
                  <Table.HeaderCell><LocalizedText source={"Details"} /></Table.HeaderCell>
                  <Table.HeaderCell><LocalizedText source={"Action"} /></Table.HeaderCell>
                </Table.Row>
              </Table.Header>
              <Table.Body>
                {importHistory.map((record) => {
                  const historyId = record.id || record.Id || record.historyId;
                  const directory = record.directory || record.Directory || '-';
                  const detail =
                    record.errorMessage ||
                    record.ErrorMessage ||
                    record.skippedReason ||
                    record.SkippedReason ||
                    `${record.safeCandidateCount || record.SafeCandidateCount || 0} safe candidate(s)`;

                  return (
                    <Table.Row key={historyId || `${directory}-${record.completedAt || record.CompletedAt}`}>
                      <Table.Cell>{record.status || record.Status || '-'}</Table.Cell>
                      <Table.Cell>{directory}</Table.Cell>
                      <Table.Cell>
                        {record.completedAt || record.CompletedAt || record.startedAt || record.StartedAt || '-'}
                      </Table.Cell>
                      <Table.Cell>{detail}</Table.Cell>
                      <Table.Cell>
                        <Button
                          aria-label={interfaceText("Retry Lidarr import for {directory}", { "directory": (directory) })}
                          disabled={!historyId}
                          loading={loading === 'retry'}
                          onClick={() => retryImport(historyId)}
                          size="small"
                         {...interfaceTextProps("Retry Lidarr import for {directory}")}>
                          <LocalizedText source={"Retry"} /></Button>
                      </Table.Cell>
                    </Table.Row>
                  );
                })}
              </Table.Body>
            </Table>
          </Segment>
        )}
        <Segment className="integration-manual-import">
          <Header as="h4"><LocalizedText source={"Manual Import"} /></Header>
          <Input
            action={{
              content: interfaceText("Import"),
              disabled: !importDirectory.trim(),
              icon: 'download',
              loading: loading === 'import',
                onClick: () =>
                  run('import', async (isCurrent) => {
                    const result = await lidarr.importCompletedDirectory({
                      directory: importDirectory.trim(),
                    });
                    if (isCurrent()) setImportResult(result);
                  }),
            }}
            fluid
            onChange={(_, { value }) => setImportDirectory(value)}
            placeholder={interfaceText("Completed download directory visible to slskr...")}
            value={importDirectory}
           {...interfaceTextProps("Completed download directory visible to slskr...")}/>
          {importResult && (
            <Message
              size="small"
              warning={Boolean(importResult.skippedReason || importResult.SkippedReason)}
            >
              {importResult.skippedReason || importResult.SkippedReason
                ? interfaceText('Skipped: {reason}', {
                  reason: importResult.skippedReason || importResult.SkippedReason,
                })
                : interfaceText('Queued Lidarr command {commandId}', {
                  commandId: importResult.commandId || importResult.CommandId || '-',
                })}
            </Message>
          )}
        </Segment>
      </Card.Content>
    </Card>
  );
};

export default LidarrPanel;
