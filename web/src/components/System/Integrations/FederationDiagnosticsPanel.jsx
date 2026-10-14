import LocalizedText from "../../Shared/LocalizedText";
import { interfaceText, interfaceTextProps } from "../../../lib/interfaceLocale";


import * as federationDiagnostics from '../../../lib/federationDiagnostics';
import { toDisplayError } from '../../../lib/errors';
import { useEffect, useState } from 'react';
import {
  Card,
  Header,
  Icon,
  Label,
  Message,
  Table,
} from 'semantic-ui-react';
import {
  boolLabel,
  getOption,
  useAsyncGuard,
  valueOrDash,
} from './integrationsShared';

const FederationDiagnosticsPanel = () => {
  const [diagnostics, setDiagnostics] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const asyncGuard = useAsyncGuard();

  useEffect(() => {
    const requestId = asyncGuard.begin();
    if (requestId === null) return undefined;

    const loadDiagnostics = async () => {
      try {
        setLoading(true);
        setError(null);
        const response = await federationDiagnostics.getDiagnostics();
        if (asyncGuard.isCurrent(requestId)) {
          const data = response?.data;
          setDiagnostics(
            data && typeof data === 'object' && !Array.isArray(data)
              ? data
              : {},
          );
        }
      } catch (error_) {
        if (asyncGuard.isCurrent(requestId)) {
          setError(toDisplayError(error_, 'Federation diagnostics failed'));
        }
      } finally {
        if (asyncGuard.isCurrent(requestId)) setLoading(false);
        asyncGuard.finish(requestId);
      }
    };

    void loadDiagnostics();
    return undefined;
  }, [asyncGuard]);

  const federation = diagnostics?.federation || {};
  const publishing = diagnostics?.publishing || {};
  const pods = diagnostics?.pods || {};
  const mesh = diagnostics?.mesh || {};
  const warnings = diagnostics?.warnings || [];

  return (
    <Card fluid>
      <Card.Content>
        <Card.Header>
          <Icon name="share alternate" />
          <LocalizedText source={"Federation and Pod Diagnostics"} /></Card.Header>
        <Card.Meta>
          <LocalizedText source={"Read-only posture for ActivityPub, pod signing, and mesh-adjacent publishing."} /></Card.Meta>
      </Card.Content>
      <Card.Content>
        {error && (
          <Message
            negative
            size="small"
          >
            <LocalizedText source={"Federation diagnostics could not be loaded."} /></Message>
        )}
        <div className="integration-status-row">
          {boolLabel(federation.enabled, 'Federation On', 'Federation Off')}
          <Label>
            <Icon name="privacy" />
            <LocalizedText source={"Exposure:"} />{" "}{valueOrDash(federation.exposure)}
          </Label>
          {boolLabel(publishing.enabled, 'Publishing On', 'Publishing Off')}
          {boolLabel(
            federation.verifySignatures,
            'HTTP Signatures On',
            'HTTP Signatures Off',
          )}
        </div>
        <Table
          compact
          definition
          size="small"
        >
          <Table.Body>
            <Table.Row>
              <Table.Cell><LocalizedText source={"Domain configured"} /></Table.Cell>
              <Table.Cell>{federation.domainConfigured ? <LocalizedText source={"Yes"} /> : <LocalizedText source={"No"} />}</Table.Cell>
            </Table.Row>
            <Table.Row>
              <Table.Cell><LocalizedText source={"Base URL configured"} /></Table.Cell>
              <Table.Cell>{federation.baseUrlConfigured ? <LocalizedText source={"Yes"} /> : <LocalizedText source={"No"} />}</Table.Cell>
            </Table.Row>
            <Table.Row>
              <Table.Cell><LocalizedText source={"Publishable domains"} /></Table.Cell>
              <Table.Cell>{publishing.publishableDomains?.join(', ') || '-'}</Table.Cell>
            </Table.Row>
            <Table.Row>
              <Table.Cell><LocalizedText source={"Publishing visibility"} /></Table.Cell>
              <Table.Cell>{valueOrDash(publishing.defaultVisibility)}</Table.Cell>
            </Table.Row>
            <Table.Row>
              <Table.Cell><LocalizedText source={"Pod join signatures"} /></Table.Cell>
              <Table.Cell>{valueOrDash(pods.joinSignatureMode)}</Table.Cell>
            </Table.Row>
            <Table.Row>
              <Table.Cell><LocalizedText source={"Pod message signatures"} /></Table.Cell>
              <Table.Cell>{valueOrDash(pods.messageSignatureMode)}</Table.Cell>
            </Table.Row>
            <Table.Row>
              <Table.Cell><LocalizedText source={"Mesh self peer ID"} /></Table.Cell>
              <Table.Cell>{mesh.selfPeerIdConfigured ? <LocalizedText source={"Configured"} /> : <LocalizedText source={"Missing"} />}</Table.Cell>
            </Table.Row>
            <Table.Row>
              <Table.Cell><LocalizedText source={"Soulseek rendezvous"} /></Table.Cell>
              <Table.Cell>{mesh.slskrendezvousEnabled ? <LocalizedText source={"Enabled"} /> : <LocalizedText source={"Disabled"} />}</Table.Cell>
            </Table.Row>
          </Table.Body>
        </Table>
        {warnings.length > 0 && (
          <Message
            size="small"
            warning
          >
            <Message.Header><LocalizedText source={"Federation posture warnings"} /></Message.Header>
            <Message.List items={warnings} />
          </Message>
        )}
        {!loading && warnings.length === 0 && diagnostics && (
          <Message
            positive
            size="small"
          >
            <LocalizedText source={"No federation or pod signing posture warnings were reported."} /></Message>
        )}
      </Card.Content>
    </Card>
  );
};

export default FederationDiagnosticsPanel;
