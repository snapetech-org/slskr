import LocalizedText from "../../Shared/LocalizedText";
import { interfaceText, interfaceTextProps, useInterfaceLanguage } from "../../../lib/interfaceLocale";


import './Security.css';
import * as securityApi from '../../../lib/security';
import { toDisplayError } from '../../../lib/errors';
import AdversarialSettings from './AdversarialSettings';
import { useMountedRef } from '../../../lib/useMountedRef';
import { usePolling } from '../../../lib/usePolling';
import React, { useCallback, useRef, useState } from 'react';
import {
  Button,
  Dimmer,
  Header,
  Icon,
  Loader,
  Message,
  Segment,
  Statistic,
  Tab,
} from 'semantic-ui-react';

const Security = () => {
  useInterfaceLanguage();
  const [activeIndex, setActiveIndex] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [dashboard, setDashboard] = useState(null);
  const [refreshing, setRefreshing] = useState(false);
  const mountedRef = useMountedRef();
  const requestIdRef = useRef(0);

  const fetchData = useCallback(async () => {
    if (!mountedRef.current || refreshing) return;
    const requestId = ++requestIdRef.current;
    try {
      setRefreshing(true);
      const dashboardData = await securityApi.getDashboard();
      if (
        mountedRef.current &&
        requestIdRef.current === requestId
      ) {
        setDashboard(
          dashboardData && typeof dashboardData === 'object'
            ? dashboardData
            : null,
        );
        setError(null);
      }
    } catch (fetchError) {
      if (
        mountedRef.current &&
        requestIdRef.current === requestId
      ) {
        setError(toDisplayError(fetchError, 'Failed to load security data'));
      }
    } finally {
      if (
        mountedRef.current &&
        requestIdRef.current === requestId
      ) {
        setLoading(false);
        setRefreshing(false);
      }
    }
  }, [mountedRef, refreshing]);

  usePolling(fetchData, 30_000);

  if (loading) {
    return (
      <Segment placeholder>
        <Dimmer
          active
          inverted
        >
          <Loader><LocalizedText source={"Loading Security Status..."} /></Loader>
        </Dimmer>
      </Segment>
    );
  }

  if (error && !dashboard) {
    return (
      <Message negative>
        <Message.Header><LocalizedText source={"Security Module Unavailable"} /></Message.Header>
        <p>{error}</p>
        <p><LocalizedText source={"Security features may not be enabled on this server."} /></p>
        <Button
          disabled={refreshing}
          onClick={fetchData}
          size="small"
        >
          <LocalizedText source={"Retry"} /></Button>
      </Message>
    );
  }

  const stats = dashboard || {};

  // Check if security is enabled but no data is available yet
  const hasAnyData =
    stats.networkGuardStats ||
    stats.reputationStats ||
    stats.violationStats ||
    stats.eventStats ||
    stats.paranoidStats ||
    stats.honeypotStats ||
    stats.fingerprintStats ||
    stats.canaryStats ||
    stats.entropyStats ||
    stats.consensusStats ||
    stats.verificationStats ||
    stats.disclosureStats ||
    stats.temporalStats;

  if (!hasAnyData) {
    return (
      <Message info>
        <Message.Header>
          <Icon name="info circle" />
          <LocalizedText source={"Security System Active - No Activity Yet"} /></Message.Header>
        <p>
          <LocalizedText source={"The security subsystem is running but hasn't collected data yet. This is normal for:"} /></p>
        <ul>
          <li>
            <strong><LocalizedText source={"Fresh installations"} /></strong> <LocalizedText source={"- Security features need time to observe network activity"} /></li>
          <li>
            <strong><LocalizedText source={"Standalone mode"} /></strong> <LocalizedText source={"- Most security features activate when mesh networking is enabled"} /></li>
          <li>
            <strong><LocalizedText source={"Low traffic"} /></strong> <LocalizedText source={"- Peer reputation, violation tracking, and behavioral analysis require peer interactions"} /></li>
        </ul>
        <p>
          <strong><LocalizedText source={"To activate security features:"} /></strong>
        </p>
        <ol>
          <li><LocalizedText source={"Connect to the Soulseek network (if not already connected)"} /></li>
          <li>
            <LocalizedText source={"Enable mesh networking via DHT/Overlay (check footer for connectivity)"} /></li>
          <li><LocalizedText source={"Wait for peer connections and transfer activity"} /></li>
        </ol>
        <p>
          <LocalizedText source={"Security monitoring will begin automatically once peer activity is detected. Check the"} />{" "}<strong><LocalizedText source={"Mesh"} /></strong> <LocalizedText source={"tab to verify connectivity."} /></p>
        <Button
          disabled={refreshing}
          loading={refreshing}
          onClick={fetchData}
          primary
          size="small"
        >
          <Icon name="refresh" />
          <LocalizedText source={"Refresh Status"} /></Button>
      </Message>
    );
  }

  const panes = [
    {
      menuItem: (
        <span>
          <Icon name="shield alternate" />
          <LocalizedText source={"Status"} /></span>
      ),
      render: () => (
        <Tab.Pane>
          <div className="security-dashboard">
            <div className="security-header">
              <Header as="h3">
                <Icon name="shield alternate" />
                <Header.Content>
                  <LocalizedText source={"Security Status"} /><Header.Subheader>
                    <LocalizedText source={"Real-time security monitoring"} /></Header.Subheader>
                </Header.Content>
              </Header>
              <Button
                icon="refresh"
                disabled={refreshing}
                loading={refreshing}
                onClick={fetchData}
                size="tiny"
                title={interfaceText("Refresh")}
               {...interfaceTextProps("Refresh")}/>
            </div>

            <Statistic.Group
              size="small"
              widths={4}
            >
              <Statistic color="blue">
                <Statistic.Value>
                  {stats.networkGuardStats?.globalConnections ?? 0}
                </Statistic.Value>
                <Statistic.Label><LocalizedText source={"Active Connections"} /></Statistic.Label>
              </Statistic>
              <Statistic color="teal">
                <Statistic.Value>
                  {stats.reputationStats?.totalPeers ?? 0}
                </Statistic.Value>
                <Statistic.Label><LocalizedText source={"Tracked Peers"} /></Statistic.Label>
              </Statistic>
              <Statistic color="orange">
                <Statistic.Value>
                  {stats.violationStats?.trackedIps ?? 0}
                </Statistic.Value>
                <Statistic.Label><LocalizedText source={"Tracked Violators"} /></Statistic.Label>
              </Statistic>
              <Statistic color="green">
                <Statistic.Value>
                  {stats.eventStats?.totalEvents ?? 0}
                </Statistic.Value>
                <Statistic.Label><LocalizedText source={"Security Events"} /></Statistic.Label>
              </Statistic>
            </Statistic.Group>

            <Segment>
              <Header as="h4">
                <Icon name="info circle" />
                <LocalizedText source={"Security Overview"} /></Header>
              <p>
                <strong><LocalizedText source={"Network Guard:"} /></strong> <LocalizedText source={"Rate limiting and connection caps are"} />{" "}{stats.networkGuardStats ? <LocalizedText source={"active"} /> : <LocalizedText source={"inactive"} />}.
              </p>
              <p>
                <strong><LocalizedText source={"Peer Reputation:"} /></strong>{' '}
                {stats.reputationStats?.trustedPeers ?? 0} <LocalizedText source={"trusted,"} />{' '}
                {stats.reputationStats?.untrustedPeers ?? 0} <LocalizedText source={"untrusted peers."} /></p>
              <p>
                <strong><LocalizedText source={"Violations:"} /></strong>{' '}
                {stats.violationStats?.trackedIps ?? 0} <LocalizedText source={"IPs,"} />{' '}
                {stats.violationStats?.trackedUsernames ?? 0} <LocalizedText source={"usernames tracked."} /></p>
              <p>
                <strong><LocalizedText source={"Crypto Health:"} /></strong> <LocalizedText source={"Entropy checks:"} />{' '}
                {stats.entropyStats?.checkCount ?? 0}<LocalizedText source={", Warnings:"} />{' '}
                {stats.entropyStats?.warningCount ?? 0}
              </p>
            </Segment>
          </div>
        </Tab.Pane>
      ),
    },
    {
      menuItem: (
        <span>
          <Icon name="user secret" />
          <LocalizedText source={"Adversarial"} /></span>
      ),
      render: () => (
        <Tab.Pane>
          <AdversarialSettings />
        </Tab.Pane>
      ),
    },
  ];

  return (
    <Tab
      activeIndex={activeIndex}
      onTabChange={(_event, { activeIndex: nextIndex }) =>
        setActiveIndex(nextIndex)
      }
      panes={panes}
      renderActiveOnly={false}
    />
  );
};

export default Security;
