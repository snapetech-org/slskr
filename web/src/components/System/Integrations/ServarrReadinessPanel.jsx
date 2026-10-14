import { formatRegionalNumber, useRegionalFormat } from '../../../lib/util';
import LocalizedText from "../../Shared/LocalizedText";
import { interfaceText, interfaceTextProps, useInterfaceLanguage } from "../../../lib/interfaceLocale";
import * as lidarr from '../../../lib/lidarr';
import { toDisplayError } from '../../../lib/errors';
import { useState } from 'react';
import {
  Button,
  Card,
  Header,
  Icon,
  Label,
  Message,
  Popup,
  Table,
} from 'semantic-ui-react';
import {
  boolLabel,
  getLidarrOptions,
  getOption,
  useAsyncGuard,
} from './integrationsShared';
import {
  buildServarrCompatibilityPreview,
  buildServarrReadiness,
  formatServarrCompatibilityReport,
  summarizeServarrReadiness,
} from '../../../lib/servarrReadiness';

const ServarrReadinessPanel = ({ options }) => {
  useRegionalFormat();
  useInterfaceLanguage();
  const lidarrOptions = getLidarrOptions(options);
  const [copyStatus, setCopyStatus] = useState('');
  const [running, setRunning] = useState(false);
  const asyncGuard = useAsyncGuard();
  const checks = buildServarrReadiness({
    apiKey: getOption(lidarrOptions, 'apiKey', 'ApiKey'),
    autoImportCompleted: getOption(
      lidarrOptions,
      'autoImportCompleted',
      'AutoImportCompleted',
    ),
    enabled: getOption(lidarrOptions, 'enabled', 'Enabled'),
    importPathFrom: getOption(lidarrOptions, 'importPathFrom', 'ImportPathFrom'),
    importPathTo: getOption(lidarrOptions, 'importPathTo', 'ImportPathTo'),
    syncWantedToWishlist: getOption(
      lidarrOptions,
      'syncWantedToWishlist',
      'SyncWantedToWishlist',
    ),
    url: getOption(lidarrOptions, 'url', 'Url'),
  });
  const summary = summarizeServarrReadiness(checks);
  const compatibility = buildServarrCompatibilityPreview({
    apiKey: getOption(lidarrOptions, 'apiKey', 'ApiKey'),
    autoImportCompleted: getOption(
      lidarrOptions,
      'autoImportCompleted',
      'AutoImportCompleted',
    ),
    enabled: getOption(lidarrOptions, 'enabled', 'Enabled'),
    importMode: getOption(lidarrOptions, 'importMode', 'ImportMode') || 'copy',
    importPathFrom: getOption(lidarrOptions, 'importPathFrom', 'ImportPathFrom'),
    importPathTo: getOption(lidarrOptions, 'importPathTo', 'ImportPathTo'),
    syncWantedToWishlist: getOption(
      lidarrOptions,
      'syncWantedToWishlist',
      'SyncWantedToWishlist',
    ),
    url: getOption(lidarrOptions, 'url', 'Url'),
  });

  const copyCompatibilityReport = async () => {
    const requestId = asyncGuard.begin();
    if (requestId === null) return;
    const report = formatServarrCompatibilityReport(compatibility);
    if (!navigator.clipboard?.writeText) {
      if (asyncGuard.isCurrent(requestId)) {
        setCopyStatus(interfaceText('Clipboard unavailable; copy the Servarr review manually.'));
      }
      asyncGuard.finish(requestId);
      return;
    }

    try {
      await navigator.clipboard.writeText(report);
      if (asyncGuard.isCurrent(requestId)) {
        setCopyStatus(interfaceText('Servarr compatibility review copied.'));
      }
    } catch {
      if (asyncGuard.isCurrent(requestId)) {
        setCopyStatus(interfaceText('Unable to copy Servarr compatibility review.'));
      }
    } finally {
      asyncGuard.finish(requestId);
    }
  };

  const runReadyActions = async () => {
    const requestId = asyncGuard.begin();
    if (requestId === null) return;
    setRunning(true);
    setCopyStatus('');

    try {
      if (!compatibility.supportsWantedPull) {
        if (asyncGuard.isCurrent(requestId)) {
          setCopyStatus(interfaceText('Wanted pull is not ready; no Servarr action was run.'));
        }
        return;
      }

      const result = await lidarr.syncWanted();
      if (asyncGuard.isCurrent(requestId)) {
        setCopyStatus(interfaceText(
          'Wanted sync finished. Created: {created}; duplicates: {duplicates}; skipped: {skipped}.',
          {
            created: result.createdCount ?? result.CreatedCount ?? 0,
            duplicates: result.duplicateCount ?? result.DuplicateCount ?? 0,
            skipped: result.skippedCount ?? result.SkippedCount ?? 0,
          },
        ));
      }
    } catch (error) {
      if (asyncGuard.isCurrent(requestId)) {
        setCopyStatus(toDisplayError(error, interfaceText('Servarr action failed.')));
      }
    } finally {
      if (asyncGuard.isCurrent(requestId)) setRunning(false);
      asyncGuard.finish(requestId);
    }
  };

  return (
    <Card fluid>
      <Card.Content>
        <Card.Header>
          <Icon name="settings" />
          <LocalizedText source={"Servarr Setup"} /></Card.Header>
        <Card.Meta>
          <LocalizedText source={"Local readiness checklist for indexer/download-client style integration."} /></Card.Meta>
      </Card.Content>
      <Card.Content>
        <div className="integration-section-header">
          <Header as="h4">
            <Icon name="clipboard check" />
            <LocalizedText source={"Compatibility Review"} /></Header>
          <Popup
            content={interfaceText("Copy the local Servarr compatibility review. This does not call Lidarr, create download clients, pull wanted items, or trigger imports.")}
            position="top center"
            trigger={
              <Button
                aria-label={interfaceText("Copy Servarr compatibility review")}
                onClick={copyCompatibilityReport}
                size="small"
               {...interfaceTextProps("Copy Servarr compatibility review")}>
                <Icon name="copy" />
                <LocalizedText source={"Copy Review"} /></Button>
              }
             {...interfaceTextProps("Copy the local Servarr compatibility review. This does not call Lidarr, create download clients, pull wanted items, or trigger imports.")}/>
          <Popup
            content={interfaceText("Run ready Servarr actions now. Currently this calls the configured Lidarr wanted-sync endpoint when wanted pull is ready; imports still require an explicit directory in the Lidarr panel.")}
            position="top center"
            trigger={
              <Button
                aria-label={interfaceText("Run ready Servarr actions")}
                disabled={!compatibility.supportsWantedPull}
                loading={running}
                onClick={runReadyActions}
                primary
                size="small"
               {...interfaceTextProps("Run ready Servarr actions")}>
                <Icon name="play" />
                <LocalizedText source={"Run Ready"} /></Button>
            }
           {...interfaceTextProps("Run ready Servarr actions now. Currently this calls the configured Lidarr wanted-sync endpoint when wanted pull is ready; imports still require an explicit directory in the Lidarr panel.")}/>
        </div>
        <div className="integration-status-row">
          <Label color={summary.status === 'Ready' ? 'green' : 'orange'}>
            <Icon name={summary.status === 'Ready' ? 'check circle' : 'warning sign'} />
            <LocalizedText source={summary.status} />
          </Label>
          <Label>
            {formatRegionalNumber(summary.ready)}/{formatRegionalNumber(summary.total)} <LocalizedText source={"checks ready"} /></Label>
          <Label color={compatibility.supportsWantedPull ? 'green' : 'grey'}>
            <LocalizedText source={"Wanted Pull"} />{" "}{compatibility.supportsWantedPull ? <LocalizedText source={"Ready"} /> : <LocalizedText source={"Not Ready"} />}
          </Label>
          <Label color={compatibility.supportsCompletedImport ? 'green' : 'grey'}>
            <LocalizedText source={"Import"} />{" "}{compatibility.supportsCompletedImport ? <LocalizedText source={"Ready"} /> : <LocalizedText source={"Not Ready"} />}
          </Label>
        </div>
        <Table
          aria-label={interfaceText("Servarr integration readiness checks")}
          celled
          compact
          tabIndex={0}
         {...interfaceTextProps("Servarr integration readiness checks")}>
          <Table.Header>
            <Table.Row>
              <Table.HeaderCell><LocalizedText source={"Check"} /></Table.HeaderCell>
              <Table.HeaderCell><LocalizedText source={"Status"} /></Table.HeaderCell>
              <Table.HeaderCell><LocalizedText source={"Why it matters"} /></Table.HeaderCell>
            </Table.Row>
          </Table.Header>
          <Table.Body>
            {checks.map((check) => (
              <Table.Row key={check.id}>
                <Table.Cell><LocalizedText source={check.title} /></Table.Cell>
                <Table.Cell>
                  {boolLabel(check.ready, 'Ready', 'Needs Setup')}
                </Table.Cell>
                <Table.Cell><LocalizedText source={check.description} /></Table.Cell>
              </Table.Row>
            ))}
          </Table.Body>
        </Table>
        <Message
          info
          size="small"
        >
          <LocalizedText source={"This checklist is diagnostic only. It does not register indexers, create download clients, pull wanted items, or trigger imports."} /></Message>
        {compatibility.actions.length > 0 && (
          <Message
            size="small"
            warning
          >
            <Message.Header><LocalizedText source={"Compatibility Actions"} /></Message.Header>
            <ul>
              {compatibility.actions.map((action) => (
                <li key={action}>{action}</li>
              ))}
            </ul>
          </Message>
        )}
        {copyStatus && (
          <Message
            info
            size="small"
          >
            {copyStatus}
          </Message>
        )}
      </Card.Content>
    </Card>
  );
};

export default ServarrReadinessPanel;
