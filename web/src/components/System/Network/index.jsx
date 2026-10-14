import LocalizedText from "../../Shared/LocalizedText";
import { interfaceText, interfaceTextProps, useInterfaceLanguage } from "../../../lib/interfaceLocale";


import * as slskrAPI from '../../../lib/slskr';
import { toDisplayError } from '../../../lib/errors';
import {
  buildNetworkHealthScore,
  formatNetworkHealthReport,
} from '../../../lib/networkHealthScore';
import { getLocalStorageItem, setLocalStorageItem } from '../../../lib/storage';
import { formatBytesFixed as formatRegionalBytes, formatRegionalCompactNumber, useRegionalFormat, formatRegionalNumber } from '../../../lib/util';
import { useMountedRef } from '../../../lib/useMountedRef';
import { usePolling } from '../../../lib/usePolling';
import { LoaderSegment, ShrinkableButton } from '../../Shared';
import NetworkDetails from './NetworkDetails';
import React, { useCallback, useRef, useState } from 'react';
import { toast } from 'react-toastify';
import {
  Button,
  Card,
  Divider,
  Grid,
  Header,
  Icon,
  Label,
  List,
  Message,
  Popup,
  Progress,
  Segment,
  Statistic,
  Table,
} from 'semantic-ui-react';

const DHT_EXPOSURE_CONSENT_KEY = 'slskr:ui:dht-public-exposure:consent-v1';

const formatBytes = (bytes) => {
  if (bytes === 0 || bytes === undefined || bytes === null) {
    return formatRegionalBytes(0, 1);
  }
  return formatRegionalBytes(Number(bytes), 1);
};

const formatNumber = (value) => {
  if (value === undefined || value === null) return formatRegionalCompactNumber(0);
  return formatRegionalCompactNumber(value);
};

const normalizePeerRecords = (value) => {
  const peers = Array.isArray(value)
    ? value
    : value && typeof value === 'object' && Array.isArray(value.peers)
      ? value.peers
      : [];

  return peers.filter(
    (peer) => peer && typeof peer === 'object' && !Array.isArray(peer),
  );
};

const isRecord = (value) =>
  value !== null && typeof value === 'object' && !Array.isArray(value);

const StatCard = ({ color, icon, inverted = false, label, subLabel, value }) => (
  <Card raised={inverted}>
    <Card.Content>
      <Card.Header style={inverted ? { color: 'rgba(255, 255, 255, 0.92)' } : undefined}>
        <Icon
          color={color}
          name={icon}
        />{' '}
        {value}
      </Card.Header>
      <Card.Meta style={inverted ? { color: 'rgba(255, 255, 255, 0.7)' } : undefined}>
        {label}
      </Card.Meta>
      {subLabel && (
        <Card.Description
          style={inverted ? { color: 'rgba(255, 255, 255, 0.82)' } : undefined}
        >
          {subLabel}
        </Card.Description>
      )}
    </Card.Content>
  </Card>
);

const getServerStateText = (server = {}) =>
  server.state ||
  server.State ||
  (server.isConnected || server.connected ? 'Connected' : 'Disconnected');

const getCredentialSourceLabel = (server = {}, options = {}) => {
  const source = server.credentialSource || server.CredentialSource;
  if (source && source !== 'none') return source;
  if (server.credentialsConfigured || options.credentials_configured) return 'config';
  if (server.runtimeCredentialsConfigured) return 'runtime';
  return 'not configured';
};

const getStatusColor = (server = {}) => {
  if (server.isConnected || server.connected) return 'green';
  if (server.isConnecting || server.isLoggingIn || server.isTransitioning) return 'yellow';
  if (server.lastError) return 'red';
  return 'grey';
};

const SoulseekSessionStatus = ({ options = {}, state = {} }) => {
  useInterfaceLanguage();
  const server = state.server || {};
  const listeners = state.listeners || {};
  const statusText = getServerStateText(server);
  const credentialSource = getCredentialSourceLabel(server, options);
  const autoConnect = options.auto_connect ?? options.autoConnect;
  const reconnect = options.reconnect;

  return (
    <Segment className="network-health-panel">
      <div className="network-health-head">
        <Header as="h4">
          <Icon name="plug" />
          <Header.Content>
            <LocalizedText source={"Soulseek Session"} /><Header.Subheader>
              <LocalizedText source={"Login, credential source, and listener state for the public Soulseek network"} /></Header.Subheader>
          </Header.Content>
        </Header>
        <Label color={getStatusColor(server)}>
          <LocalizedText source={statusText} />
        </Label>
      </div>
      <Label.Group>
        <Label color={credentialSource === 'not configured' ? 'red' : 'blue'}>
          <LocalizedText source={"credentials"} /><Label.Detail><LocalizedText source={credentialSource} /></Label.Detail>
        </Label>
        <Label color={autoConnect ? 'green' : 'grey'}>
          <LocalizedText source="auto-connect" />
          <Label.Detail>{autoConnect ? <LocalizedText source={"on"} /> : <LocalizedText source={"off"} />}</Label.Detail>
        </Label>
        <Label color={reconnect ? 'green' : 'grey'}>
          <LocalizedText source={"reconnect"} /><Label.Detail>{reconnect ? <LocalizedText source={"on"} /> : <LocalizedText source={"off"} />}</Label.Detail>
        </Label>
        <Label color="teal">
          <LocalizedText source={"server"} /><Label.Detail>{server.address || server.ipEndPoint || options.server_address || <LocalizedText source="unset" />}</Label.Detail>
        </Label>
        <Label color="teal">
          <LocalizedText source={"listen"} /><Label.Detail>{options.listen_port ?? <LocalizedText source="unset" />}</Label.Detail>
        </Label>
        <Label color="teal">
          <LocalizedText source={"advertised"} /><Label.Detail>{options.advertised_port ?? options.listen_port ?? <LocalizedText source="unset" />}</Label.Detail>
        </Label>
      </Label.Group>
      {(listeners.regularLocalAddr || listeners.regular_local_addr ||
        listeners.obfuscatedLocalAddr || listeners.obfuscated_local_addr ||
        listeners.lastError || listeners.last_error) && (
        <Label.Group>
          <Label color="blue">
            <LocalizedText source={"listener"} /><Label.Detail>
              {listeners.regularLocalAddr || listeners.regular_local_addr || <LocalizedText source="not bound" />}
            </Label.Detail>
          </Label>
          <Label color="purple">
            <LocalizedText source={"obfuscated"} /><Label.Detail>
              {listeners.obfuscatedLocalAddr || listeners.obfuscated_local_addr || <LocalizedText source="not bound" />}
            </Label.Detail>
          </Label>
        </Label.Group>
      )}
      {server.lastError && (
        <Message
          className="network-diagnostic-message"
          negative
        >
          <Message.Header><LocalizedText source={"Soulseek connection failed"} /></Message.Header>
          <p>{server.lastError}</p>
        </Message>
      )}
      {(listeners.lastError || listeners.last_error) && (
        <Message
          className="network-diagnostic-message"
          warning
        >
          <Message.Header><LocalizedText source={"Listener warning"} /></Message.Header>
          <p>{listeners.lastError || listeners.last_error}</p>
        </Message>
      )}
      {credentialSource === 'not configured' && (
        <Message
          className="network-diagnostic-message"
          warning
        >
          <Message.Header><LocalizedText source={"Soulseek credentials are not configured"} /></Message.Header>
          <p>
            <LocalizedText source={"Set"} />{" "}<code>SLSK_USERNAME</code> <LocalizedText source={"and"} />{" "}<code>SLSK_PASSWORD</code><LocalizedText source={", configure a credential store, or use the Connect control in the top bar."} /></p>
        </Message>
      )}
    </Segment>
  );
};

// eslint-disable-next-line complexity
const LocalizedNetworkFindingSummary = ({ source }) => {
  const securityMatch = source.match(/^(\d+) mesh security signal(s?) visible$/);
  if (securityMatch) return <LocalizedText source={securityMatch[2] ? "{count} mesh security signals visible" : "{count} mesh security signal visible"} values={{ count: securityMatch[1] }} />;
  const backfillMatch = source.match(/^(\d+) pending backfill candidates$/);
  if (backfillMatch) return <LocalizedText source="{count} pending backfill candidates" values={{ count: backfillMatch[1] }} />;
  return <LocalizedText source={source} />;
};

const Network = ({ options = {}, state = {}, theme }) => {
  useInterfaceLanguage();
  useRegionalFormat();
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState(null);
  const [statsError, setStatsError] = useState(null);
  const [meshPeers, setMeshPeers] = useState([]);
  const [discoveredPeers, setDiscoveredPeers] = useState([]);
  const [meshPeersError, setMeshPeersError] = useState(null);
  const [discoveredPeersError, setDiscoveredPeersError] = useState(null);
  const [syncing, setSyncing] = useState({});
  const [backfilling, setBackfilling] = useState(false);
  const [backfillProgress, setBackfillProgress] = useState(null);
  const [dhtExposureAcknowledged, setDhtExposureAcknowledged] = useState(() => {
    return getLocalStorageItem(DHT_EXPOSURE_CONSENT_KEY) === 'acknowledged';
  });
  const mountedRef = useMountedRef();
  const fetchRequestIdRef = useRef(0);
  const syncRequestIdsRef = useRef({});
  const backfillRequestIdRef = useRef(0);

  const fetchData = useCallback(async () => {
    if (!mountedRef.current) return;
    const requestId = ++fetchRequestIdRef.current;
    try {
      const [statsResult, peersResult, discoveredResult] = await Promise.allSettled([
        slskrAPI.getSlskrStats(),
        slskrAPI.getMeshPeers(),
        slskrAPI.getDiscoveredPeers(),
      ]);

      if (
        mountedRef.current &&
        requestId === fetchRequestIdRef.current
      ) {
        if (statsResult.status === 'fulfilled' && isRecord(statsResult.value)) {
          setStats(statsResult.value);
          setStatsError(null);
        } else {
          setStatsError(
            statsResult.status === 'rejected'
              ? toDisplayError(statsResult.reason, 'Network statistics unavailable')
              : 'Network statistics response was invalid',
          );
        }

        if (peersResult.status === 'fulfilled') {
          setMeshPeers(normalizePeerRecords(peersResult.value));
          setMeshPeersError(null);
        } else {
          setMeshPeersError(
            toDisplayError(peersResult.reason, 'Mesh peer list unavailable'),
          );
        }
        if (discoveredResult.status === 'fulfilled') {
          setDiscoveredPeers(normalizePeerRecords(discoveredResult.value));
          setDiscoveredPeersError(null);
        } else {
          setDiscoveredPeersError(
            toDisplayError(
              discoveredResult.reason,
              'Discovered peer list unavailable',
            ),
          );
        }
      }
    } catch (error) {
      console.error('Failed to fetch network stats:', error);
      if (mountedRef.current && requestId === fetchRequestIdRef.current) {
        setStatsError(toDisplayError(error, 'Network statistics unavailable'));
      }
    } finally {
      if (
        mountedRef.current &&
        requestId === fetchRequestIdRef.current
      ) {
        setLoading(false);
      }
    }
  }, [mountedRef]);

  usePolling(fetchData, 5_000);

  const dismissDhtExposureConsent = () => {
    setLocalStorageItem(DHT_EXPOSURE_CONSENT_KEY, 'acknowledged');
    setDhtExposureAcknowledged(true);
  };

  const handleSync = async (username) => {
    if (!mountedRef.current || syncRequestIdsRef.current[username]) return;
    const requestId = (syncRequestIdsRef.current[username] || 0) + 1;
    syncRequestIdsRef.current[username] = requestId;
    setSyncing((previous) => ({ ...previous, [username]: true }));
    try {
      const result = await slskrAPI.triggerMeshSync(username);
      if (result?.success === false || result?.error) {
        throw new Error(toDisplayError(result, 'Failed to sync with peer'));
      }
      if (
        mountedRef.current &&
        syncRequestIdsRef.current[username] === requestId
      ) {
        toast.success(interfaceText("Sync initiated with {username}", { "username": (username) }));
      }
    } catch (error) {
      if (
        mountedRef.current &&
        syncRequestIdsRef.current[username] === requestId
      ) {
        toast.error(toDisplayError(error, `Failed to sync with ${username}`));
      }
    } finally {
      if (
        mountedRef.current &&
        syncRequestIdsRef.current[username] === requestId
      ) {
        setSyncing((previous) => ({ ...previous, [username]: false }));
        delete syncRequestIdsRef.current[username];
      }
    }
  };

  const handleBackfillFromHistory = async (reset = false) => {
    if (!mountedRef.current || backfilling) return;
    const requestId = ++backfillRequestIdRef.current;
    setBackfilling(true);
    try {
      const result = await slskrAPI.backfillFromSearchHistory({
        batchSize: 50,
        reset,
      });

      if (
        !mountedRef.current ||
        requestId !== backfillRequestIdRef.current
      ) {
        return;
      }

      if (result?.error) {
        toast.error(interfaceText("Backfill failed: {error}", { "error": (result.error) }));
        setBackfillProgress(null);
      } else {
        setBackfillProgress(
          result && typeof result === 'object' ? result : null,
        );

        if (result?.complete) {
          toast.success(result.message || 'Backfill complete!');
        } else {
          toast.info(
            result.message || 'Batch processed - click again to continue',
          );
        }

        void fetchData(); // Refresh stats
      }
    } catch {
      if (
        mountedRef.current &&
        requestId === backfillRequestIdRef.current
      ) {
        toast.error(interfaceText("Failed to trigger backfill from search history"));
        setBackfillProgress(null);
      }
    } finally {
      if (
        mountedRef.current &&
        requestId === backfillRequestIdRef.current
      ) {
        setBackfilling(false);
      }
    }
  };

  const { backfill, capabilities, hashDb, mesh, swarmJobs } = stats || {};
  const hasStats = stats !== null;
  const hashDbSizeBytes = hashDb?.dbSizeBytes;
  const hasHashDbSize =
    hashDbSizeBytes !== undefined &&
    hashDbSizeBytes !== null &&
    Number.isFinite(Number(hashDbSizeBytes));
  const obfuscation = capabilities?.obfuscation;
  const darkTheme = theme === 'dark';
  const dhtIsLanOnly = stats?.dht?.isLanOnly ?? stats?.dht?.lanOnly ?? false;
  const dhtIsRunning = stats?.dht?.isDhtRunning ?? false;
  const dhtNodeCount = stats?.dht?.dhtNodeCount ?? 0;
  const dhtDiscoveredPeerCount =
    stats?.dht?.discoveredPeerCount ?? stats?.dht?.totalPeersDiscovered ?? 0;
  const dhtActiveMeshCount = stats?.dht?.activeMeshConnections ?? 0;
  const observedMeshPeerCount = Math.max(
    meshPeers.length,
    mesh?.connectedPeerCount ?? 0,
    dhtActiveMeshCount,
  );
  const observedDiscoveredPeerCount = Math.max(
    discoveredPeers.length,
    dhtDiscoveredPeerCount,
  );
  const shouldExplainLanOnlyDht =
    dhtIsLanOnly &&
    dhtIsRunning &&
    dhtNodeCount === 0 &&
    observedMeshPeerCount === 0 &&
    observedDiscoveredPeerCount === 0;
  const shouldWarnAboutConnectivity =
    !shouldExplainLanOnlyDht &&
    dhtIsRunning &&
    dhtNodeCount === 0 &&
    observedMeshPeerCount === 0 &&
    observedDiscoveredPeerCount === 0;
  const shouldShowDhtExposureNotice =
    (stats?.dht?.isEnabled ?? false) &&
    !dhtIsLanOnly &&
    dhtIsRunning &&
    !dhtExposureAcknowledged;
  const networkHealth = hasStats
    ? buildNetworkHealthScore({
        discoveredPeers,
        meshPeers,
        stats,
      })
    : null;

  const copyNetworkHealthReport = async () => {
    if (!mountedRef.current) return;
    if (!networkHealth) {
      toast.info(interfaceText("Network health is unavailable until network statistics load"));
      return;
    }
    const report = formatNetworkHealthReport(networkHealth);
    if (navigator.clipboard?.writeText) {
      try {
        await navigator.clipboard.writeText(report);
        toast.success(interfaceText("Network health report copied"));
      } catch {
        toast.error(interfaceText("Unable to copy network health report"));
      }
      return;
    }

    toast.info(interfaceText("Clipboard unavailable; select the report text manually"));
  };

  if (loading) {
    return <LoaderSegment />;
  }

  return (
    <div className="network-dashboard">
      <SoulseekSessionStatus
        options={options}
        state={state}
      />
      {statsError && (
        <Message
          className="network-diagnostic-message"
          negative
        >
          <Message.Header><LocalizedText source={"Network telemetry unavailable"} /></Message.Header>
          <p>{statsError}</p>
          <p>
            {hasStats
              ? <LocalizedText source={"Showing the last successful network snapshot until the next poll succeeds."} />
              : <LocalizedText source={"Network health and counters will remain unavailable until the daemon responds."} />}
          </p>
        </Message>
      )}
      {meshPeersError && (
        <Message
          data-testid="mesh-peers-load-error"
          className="network-diagnostic-message"
          warning
        >
          <Message.Header><LocalizedText source={"Mesh peer list unavailable"} /></Message.Header>
          <p>{meshPeersError}</p>
          <p><LocalizedText source={"Existing peer data is retained until the next successful poll."} /></p>
        </Message>
      )}
      {discoveredPeersError && (
        <Message
          data-testid="discovered-peers-load-error"
          className="network-diagnostic-message"
          warning
        >
          <Message.Header><LocalizedText source={"Discovered peer list unavailable"} /></Message.Header>
          <p>{discoveredPeersError}</p>
          <p><LocalizedText source={"Existing peer data is retained until the next successful poll."} /></p>
        </Message>
      )}
      {shouldExplainLanOnlyDht && (
        <Message
          className="network-diagnostic-message"
          info
        >
          <Message.Header><LocalizedText source={"LAN-only DHT is isolated"} /></Message.Header>
          <p>
            <LocalizedText source={"DHT rendezvous is running with"} />{" "}<code>dhtRendezvous.lanOnly: true</code><LocalizedText source={", so slskr intentionally skips the public BitTorrent DHT bootstrap routers. Seeing"} />{" "}<code>0</code> <LocalizedText source={"DHT nodes and"} />{" "}<code>0</code> <LocalizedText source={"discovered peers can be expected in this privacy mode even when the overlay and DHT ports are open."} /></p>
          <p>
            <LocalizedText source={"To discover public slskr peers through DHT rendezvous, set"} /><code> dhtRendezvous.lanOnly: false</code> <LocalizedText source={"and restart. Keep LAN-only enabled if you want discovery limited to local or already-known private peers."} /></p>
        </Message>
      )}
      {shouldWarnAboutConnectivity && (
        <Message
          className="network-diagnostic-message"
          warning
        >
          <Message.Header><LocalizedText source={"Connectivity diagnostics"} /></Message.Header>
          <p>
            <LocalizedText source={"slskr is not seeing reachable peers yet. If you can log into the Soulseek server but uploads, downloads, and peer counts stay at zero, verify that your configured Soulseek listen port is reachable from other peers. The default is"} />{" "}<code>50300/tcp</code>.
          </p>
          <p>
            <LocalizedText source={"Check local firewall rules, router/NAT forwarding, container port publishing, and any reverse-proxy setup that might expose the Web UI but not the Soulseek listen port."} /></p>
        </Message>
      )}
      {shouldShowDhtExposureNotice && (
        <Message
          className="network-diagnostic-message"
          info
          onDismiss={dismissDhtExposureConsent}
        >
          <Message.Header><LocalizedText source={"Public DHT exposure notice"} /></Message.Header>
          <p>
            <LocalizedText source={"DHT rendezvous is enabled and this node can publish its public endpoint into the public BitTorrent DHT. This is expected when public rendezvous is enabled; this notice is only here so operators are aware that other slskr peers can discover the node for mesh sync."} /></p>
          <p>
            <LocalizedText source={"If you want to keep mesh discovery confined to trusted local peers, set"} />{" "}<code>dht.lan_only=true</code> <LocalizedText source={"in configuration before long-term operation."} /></p>
        </Message>
      )}

      {/* Header Stats */}
      <Card.Group
        itemsPerRow={4}
        stackable
      >
        <StatCard
          color="blue"
          icon="sitemap"
          inverted={darkTheme}
          label={interfaceText("Mesh Peers")}
          subLabel={<LocalizedText source={"slskr clients connected"} />}
          value={hasStats ? formatNumber(mesh?.connectedPeerCount ?? meshPeers.length) : '—'}
         {...interfaceTextProps("Mesh Peers")}/>
        <StatCard
          color="green"
          icon="database"
          inverted={darkTheme}
          label={interfaceText("Hash Entries")}
          subLabel={
            hasStats && hasHashDbSize
              ? <>{formatBytes(hashDbSizeBytes)} <LocalizedText source={"on disk"} /></>
              : <LocalizedText source={"Local database"} />
          }
          value={hasStats ? formatNumber(hashDb?.totalEntries ?? 0) : '—'}
         {...interfaceTextProps("Hash Entries")}/>
        <StatCard
          color="purple"
          icon="sync"
          inverted={darkTheme}
          label={interfaceText("Sequence ID")}
          subLabel={<LocalizedText source={"Mesh sync position"} />}
          value={hasStats ? hashDb?.currentSeqId ?? mesh?.localSeqId ?? 0 : '—'}
         {...interfaceTextProps("Sequence ID")}/>
        <StatCard
          color="orange"
          icon="bolt"
          inverted={darkTheme}
          label={interfaceText("Active Swarms")}
          subLabel={<LocalizedText source={"Multi-source downloads"} />}
          value={hasStats ? formatNumber(swarmJobs?.length ?? 0) : '—'}
         {...interfaceTextProps("Active Swarms")}/>
      </Card.Group>

      <Divider />

      <Segment className="network-health-panel">
        <div className="network-health-head">
          <Header as="h4">
            <Icon name="heartbeat" />
            <Header.Content>
              <LocalizedText source={"Network Health"} /><Header.Subheader>
                <LocalizedText source={"Local readiness score from already-loaded mesh, DHT, HashDb, and security counters"} /></Header.Subheader>
            </Header.Content>
          </Header>
          <Popup
            content={interfaceText("Copy a local network-health report for diagnostics. This does not query peers or change network state.")}
            position="top center"
            trigger={
              <Button
                aria-label={interfaceText("Copy network health report")}
                onClick={copyNetworkHealthReport}
                size="small"
               {...interfaceTextProps("Copy network health report")}>
                <Icon name="copy" />
                <LocalizedText source={"Copy Report"} /></Button>
            }
           {...interfaceTextProps("Copy a local network-health report for diagnostics. This does not query peers or change network state.")}/>
        </div>
        {networkHealth ? (
          <>
            <div className="network-health-score-row">
              <Progress
                color={
                  networkHealth.score >= 85
                    ? 'green'
                    : networkHealth.score >= 65
                      ? 'yellow'
                      : 'red'
                }
                percent={formatRegionalNumber(networkHealth.score)}
                progress
              >
                <LocalizedText source={networkHealth.label} />
              </Progress>
              {/* These four are inputs to the score above, not states of their
                  own — one neutral pill style, not four unrelated hues. */}
              <Label basic>
                <LocalizedText source={"Mesh"} /><Label.Detail>{formatNumber(networkHealth.inputs.meshCount)}</Label.Detail>
              </Label>
              <Label basic>
                <LocalizedText source={"Discovered"} /><Label.Detail>{formatNumber(networkHealth.inputs.discoveredCount)}</Label.Detail>
              </Label>
              <Label basic>
                DHT
                <Label.Detail>{formatNumber(networkHealth.inputs.dhtNodes)}</Label.Detail>
              </Label>
              <Label
                basic={networkHealth.inputs.securityWarningCount === 0}
                color={networkHealth.inputs.securityWarningCount > 0 ? 'orange' : undefined}
              >
                <LocalizedText source={"Security"} /><Label.Detail>{formatNumber(networkHealth.inputs.securityWarningCount)}</Label.Detail>
              </Label>
            </div>
            {networkHealth.findings.length > 0 ? (
              <List
                divided
                relaxed
              >
                {networkHealth.findings.map((finding) => (
                  <List.Item key={`${finding.area}-${finding.summary}`}>
                    <List.Icon
                      color={
                        finding.severity === 'fail'
                          ? 'red'
                          : finding.severity === 'warn'
                            ? 'yellow'
                            : 'blue'
                      }
                      name={
                        finding.severity === 'fail'
                          ? 'warning sign'
                          : finding.severity === 'warn'
                            ? 'exclamation triangle'
                            : 'info circle'
                      }
                      verticalAlign="middle"
                    />
                    <List.Content>
                      <List.Header>
                        <LocalizedText source={finding.area} />: <LocalizedNetworkFindingSummary source={finding.summary} />
                      </List.Header>
                      <List.Description><LocalizedText source={finding.action} /></List.Description>
                    </List.Content>
                  </List.Item>
                ))}
              </List>
            ) : (
              <Message
                className="network-diagnostic-message"
                positive
              >
                <Message.Header><LocalizedText source={"No local network-health findings"} /></Message.Header>
                <p>
                  <LocalizedText source={"Mesh, DHT, HashDb, and security counters look healthy from the already-loaded dashboard data."} /></p>
              </Message>
            )}
          </>
        ) : (
          <Message
            className="network-diagnostic-message"
            warning
          >
            <Message.Header><LocalizedText source={"Network health unavailable"} /></Message.Header>
            <p><LocalizedText source={"There is no successful network snapshot to score yet."} /></p>
          </Message>
        )}
      </Segment>

      {/* Our Capabilities */}
      <Segment>
        <Header as="h4">
          <Icon name="id card" />
          <Header.Content>
            <LocalizedText source={"Our Capabilities"} /><Header.Subheader>
              <LocalizedText source={"What we advertise to other slskr peers"} /></Header.Subheader>
          </Header.Content>
        </Header>

        <Label.Group>
          <Label color="blue">
            <Icon name="code branch" />
            {hasStats ? capabilities?.version ?? 'unknown' : '—'}
          </Label>
          {hasStats ? (
            capabilities?.features?.map((feature) => (
              <Label
                color="teal"
                key={feature}
              >
                <Icon name="check" />
                {feature}
              </Label>
            )) ?? (
              <>
                <Label color="teal">
                  <Icon name="check" />
                  multi_source
                </Label>
                <Label color="teal">
                  <Icon name="check" />
                  hash_db
                </Label>
                <Label color="teal">
                  <Icon name="check" />
                  mesh_sync
                </Label>
              </>
            )
          ) : (
            <Label color="grey"><LocalizedText source={"Capabilities unavailable"} /></Label>
          )}
        </Label.Group>
        {obfuscation && (
          <Message
            info={!obfuscation.enabled}
            warning={obfuscation.enabled && !obfuscation.runtimeSupported}
            positive={obfuscation.enabled && obfuscation.runtimeSupported}
          >
            <Message.Header><LocalizedText source={"Soulseek Type-1 Obfuscation"} /></Message.Header>
            <p>{obfuscation.summary}</p>
            <Label.Group>
              <Label color={obfuscation.enabled ? 'teal' : 'grey'}>
                {obfuscation.enabled ? <LocalizedText source={"enabled"} /> : <LocalizedText source={"disabled"} />}
              </Label>
              <Label color="blue"><LocalizedText source={"mode:"} />{" "}{obfuscation.mode}</Label>
              <Label color="blue"><LocalizedText source={"type:"} />{" "}{obfuscation.type}</Label>
              <Label color="blue">
                <LocalizedText source={"streams:"} />{" "}{(obfuscation.supportedConnectionTypes ?? []).join(', ') || interfaceText('unset')}
              </Label>
              <Label color="blue">
                <LocalizedText source={"obfuscated port:"} />{" "}{obfuscation.effectiveListenPort ?? interfaceText('unset')}
              </Label>
              <Label color={obfuscation.advertiseRegularPort ? 'green' : 'grey'}>
                <LocalizedText source={"regular fallback:"} />{' '}
                {obfuscation.advertiseRegularPort ? <LocalizedText source={"advertised"} /> : <LocalizedText source={"off"} />}
              </Label>
              <Label color={obfuscation.runtimeSupported ? 'green' : 'orange'}>
                <LocalizedText source={"runtime:"} />{" "}{obfuscation.runtimeState}
              </Label>
            </Label.Group>
          </Message>
        )}
      </Segment>

      <NetworkDetails
        actions={{
          handleBackfillFromHistory,
          handleSync,
        }}
        data={{
          backfill,
          backfillProgress,
          backfilling,
          darkTheme,
          discoveredPeers,
          discoveredPeersError,
          formatBytes,
          formatNumber,
          hasStats,
          hashDb,
          mesh,
          meshPeers,
          meshPeersError,
          swarmJobs,
          syncing,
        }}
      />
    </div>
  );
};

export default Network;
