import LocalizedText from "../../Shared/LocalizedText";
import { interfaceText, interfaceTextProps } from "../../../lib/interfaceLocale";
import MetadataProcessingPanel from './MetadataProcessingPanel';
import SourceFeedIntegrationsPanel from './SourceFeedIntegrationsPanel';
import NotificationIntegrationsPanel from './NotificationIntegrationsPanel';
import MetadataSettingsPanel from './MetadataSettingsPanel';
import FtpIntegrationPanel from './FtpIntegrationPanel';
import LidarrPanel from './LidarrPanel';
import MediaServerPanel from './MediaServerPanel';
import ServarrReadinessPanel from './ServarrReadinessPanel';
import FederationDiagnosticsPanel from './FederationDiagnosticsPanel';
import VpnPanel from './VpnPanel';
import React from 'react';
import {
  Header,
  Icon,
  Segment,
} from 'semantic-ui-react';














const Integrations = ({ options = {}, state = {} }) => (
  <div className="integrations-admin">
    <Segment>
      <Header as="h3">
        <Icon name="plug" />
        <LocalizedText source={"Integrations"} /></Header>
      <p>
        <LocalizedText source={"Operational status and admin actions for integrations that affect connection routing, downloads, and external media managers."} /></p>
    </Segment>
    <VpnPanel
      options={options}
      state={state}
    />
    <LidarrPanel options={options} />
    <MetadataProcessingPanel />
    <MetadataSettingsPanel options={options} />
    <NotificationIntegrationsPanel options={options} />
    <SourceFeedIntegrationsPanel options={options} />
    <FtpIntegrationPanel options={options} />
    <ServarrReadinessPanel options={options} />
    <MediaServerPanel />
    <FederationDiagnosticsPanel />
  </div>
);

export { buildDefaultSpotifyRedirectUri } from './SourceFeedIntegrationsPanel';

export default Integrations;
