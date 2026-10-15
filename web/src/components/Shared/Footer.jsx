import LocalizedText, { LocalizedPluralText } from "./LocalizedText";
import { interfaceText, interfaceTextProps, useInterfaceLanguage } from "../../lib/interfaceLocale";


import './Footer.css';
import * as application from '../../lib/application';
import { toDisplayError } from '../../lib/errors';
import * as mesh from '../../lib/mesh';
import * as session from '../../lib/session';
import * as slskrAPI from '../../lib/slskr';
import { getLocalStorageItem } from '../../lib/storage';
import * as transfers from '../../lib/transfers';
import { formatRegionalCompactNumber, formatRegionalFixedNumber, formatRegionalNumber, useRegionalFormat } from '../../lib/util';
import { createPollingController } from '../../lib/usePolling';
import { urlBase } from '../../config';
import React, { Component } from 'react';
import { Icon } from 'semantic-ui-react';

const GITHUB_BASE = 'https://github.com/snapetech-org/slskr';

const formatSpeed = (bytesPerSec) => {
  if (!bytesPerSec || bytesPerSec === 0) {
    return { unit: 'B', value: formatRegionalNumber(0) };
  }

  const kb = bytesPerSec / 1_024;
  const mb = kb / 1_024;
  const gb = mb / 1_024;

  if (gb >= 1) {
    return { unit: 'G', value: formatRegionalFixedNumber(gb, gb >= 10 ? 1 : 2) };
  }

  if (mb >= 1) {
    return { unit: 'M', value: formatRegionalFixedNumber(mb, mb >= 10 ? 1 : 2) };
  }

  if (kb >= 1) {
    return { unit: 'K', value: formatRegionalFixedNumber(kb, kb >= 10 ? 1 : 2) };
  }

  return { unit: 'B', value: formatRegionalFixedNumber(bytesPerSec, 0) };
};

const formatCount = (value) => {
  if (value === undefined || value === null) return '—';
  return formatRegionalCompactNumber(value);
};

const finiteNumberOrNull = (value) => {
  const number = Number(value);
  return Number.isFinite(number) ? number : null;
};

const setFooterHeightVariable = (element) => {
  if (!element || typeof document === 'undefined') return;

  const height = Math.ceil(element.getBoundingClientRect().height);
  if (height > 0) {
    document.documentElement.style.setProperty(
      '--slskr-footer-height',
      `${height}px`,
    );
  }
};

class FooterView extends Component {
  constructor(props) {
    super(props);
    this.state = {
      buildInfo: null,
      buildInfoError: null,
      slskrStats: null,
      statsError: null,
      speeds: null,
      speedsError: null,
      stats: null,
    };
    this.footerRef = React.createRef();
    this.footerResizeObserver = null;
    this.pollController = null;
    this.isMountedFlag = false;
    this.requestIds = {
      buildInfo: 0,
      speeds: 0,
      stats: 0,
    };
  }

  componentDidMount() {
    this.isMountedFlag = true;
    this.updateFooterHeight();
    if (
      typeof window !== 'undefined' &&
      typeof window.ResizeObserver === 'function' &&
      this.footerRef.current
    ) {
      this.footerResizeObserver = new window.ResizeObserver(
        this.updateFooterHeight,
      );
      this.footerResizeObserver.observe(this.footerRef.current);
    }

    void this.fetchBuildInfo();

    if (this.props.runtimeProfile !== 'legacy' && session.isLoggedIn()) {
      this.pollController = createPollingController(
        async () => {
          await Promise.all([this.fetchStats(), this.fetchSpeeds()]);
        },
        2_000,
      );
    }
  }

  componentWillUnmount() {
    this.isMountedFlag = false;
    Object.keys(this.requestIds).forEach((key) => {
      this.requestIds[key] += 1;
    });
    this.pollController?.stop();
    this.pollController = null;
    if (this.footerResizeObserver) {
      this.footerResizeObserver.disconnect();
      this.footerResizeObserver = null;
    }
  }

  componentDidUpdate() {
    this.updateFooterHeight();
  }

  updateFooterHeight = () => {
    setFooterHeightVariable(this.footerRef.current);
  };

  fetchStats = async () => {
    if (!this.isMountedFlag || !session.isLoggedIn()) {
      return;
    }

    const requestId = ++this.requestIds.stats;
    try {
      const [transportStats, slskrStats] = await Promise.allSettled([
        mesh.getStats(),
        slskrAPI.getSlskrStats(),
      ]);

      if (this.isMountedFlag && requestId === this.requestIds.stats) {
        const nextState = {};
        const errors = [];
        if (slskrStats.status === 'fulfilled') {
          nextState.slskrStats = slskrStats.value;
        } else {
          errors.push(toDisplayError(slskrStats.reason, interfaceText('slskr telemetry unavailable')));
        }
        if (transportStats.status === 'fulfilled') {
          nextState.stats = transportStats.value;
        } else {
          errors.push(toDisplayError(transportStats.reason, interfaceText('Network telemetry unavailable')));
        }
        nextState.statsError = errors.length > 0 ? errors.join(' ') : null;
        this.setState(nextState);
      }
    } catch (error) {
      console.debug('Failed to fetch mesh stats:', error);
      if (this.isMountedFlag && requestId === this.requestIds.stats) {
        this.setState({
          statsError: toDisplayError(error, interfaceText('Network telemetry unavailable')),
        });
      }
    }
  };

  fetchSpeeds = async () => {
    if (!this.isMountedFlag || !session.isLoggedIn()) {
      return;
    }

    const requestId = ++this.requestIds.speeds;
    try {
      const speeds = await transfers.getSpeeds();
      if (this.isMountedFlag && requestId === this.requestIds.speeds) {
        this.setState({ speeds, speedsError: null });
      }
    } catch (error) {
      console.debug('Failed to fetch transfer speeds:', error);
      if (this.isMountedFlag && requestId === this.requestIds.speeds) {
        this.setState({
          speedsError: toDisplayError(error, interfaceText('Transfer speeds unavailable')),
        });
      }
    }
  };

  fetchBuildInfo = async () => {
    if (!this.isMountedFlag || this.props.runtimeProfile === 'legacy') {
      return;
    }

    const requestId = ++this.requestIds.buildInfo;
    try {
      const buildInfo = await application.getBuild({ checkForUpdates: true });
      if (this.isMountedFlag && requestId === this.requestIds.buildInfo) {
        this.setState({ buildInfo, buildInfoError: null });
      }
    } catch (error) {
      console.debug('Failed to fetch build info:', error);
      if (this.isMountedFlag && requestId === this.requestIds.buildInfo) {
        this.setState({
          buildInfoError: toDisplayError(error, interfaceText('Build information unavailable')),
        });
      }
    }
  };

  render() {
    if (this.props.runtimeProfile === 'legacy') {
      return (
        <footer
          className="slskr-footer"
          ref={this.footerRef}
        >
          <div className="slskr-footer-content">
            <a
              href="https://github.com/slskd/slskd"
              rel="noopener noreferrer"
              target="_blank"
            >
              <LocalizedText source={"slskd 0.0.0 AGPLv3"} /></a>
          </div>
        </footer>
      );
    }

    const year = new Date().getFullYear();
    const {
      buildInfo,
      buildInfoError,
      slskrStats,
      speeds,
      speedsError,
      stats,
      statsError,
    } = this.state;
    const isLoggedIn = session.isLoggedIn();

    if (!isLoggedIn && this.props.runtimeProfile !== 'native') {
      // Nothing here is real yet — no donation asks, build badge, or live
      // telemetry before someone has even signed in. Just attribution.
      return (
        <footer
          className="slskr-footer slskr-footer-minimal"
          ref={this.footerRef}
        >
          <span className="slskr-footer-copyright">
            © {year}{' '}
            <a
              href={GITHUB_BASE}
              rel="noopener noreferrer"
              target="_blank"
              title={interfaceText("slskr project")}
             {...interfaceTextProps("slskr project")}>
              <LocalizedText source={"slskr"} /></a>
          </span>
        </footer>
      );
    }

    const currentBuild = buildInfo?.current || buildInfo?.full || 'unknown';
    const fullBuild = buildInfo?.full || currentBuild;
    const latestBuild = buildInfo?.latest || '';
    const latestTag = buildInfo?.latestTag || latestBuild;
    const latestUrl = buildInfo?.latestUrl || `${GITHUB_BASE}/releases`;
    const isUpdateAvailable = buildInfo?.isUpdateAvailable === true;
    const dht = slskrStats?.dht || {};
    const hashDb = slskrStats?.hashDb || {};
    const meshStats = slskrStats?.mesh || {};
    const swarmJobs = Array.isArray(slskrStats?.swarmJobs)
      ? slskrStats.swarmJobs
      : [];
    const dhtNodes =
      finiteNumberOrNull(dht.dhtNodeCount) ?? finiteNumberOrNull(stats?.dht);
    const discoveredPeers = finiteNumberOrNull(dht.discoveredPeerCount);
    const displayedDhtPeers = discoveredPeers ?? dhtNodes;
    const meshPeers = finiteNumberOrNull(meshStats.connectedPeerCount);
    const hashCount = finiteNumberOrNull(hashDb.totalEntries);
    const seqId =
      finiteNumberOrNull(hashDb.currentSeqId) ??
      finiteNumberOrNull(meshStats.localSeqId);
    const isSyncing = Boolean(meshStats.isSyncing);
    const backfillActive = Boolean(slskrStats?.backfill?.isActive);
    const activeSwarms = swarmJobs.length;
    const karma = Number.parseInt(getLocalStorageItem('slskr-karma', '0'), 10);
    const totalSpeed = isLoggedIn && speeds ? formatSpeed(speeds.total) : null;
    const soulseekSpeed =
      isLoggedIn && speeds ? formatSpeed(speeds.soulseek) : null;
    const meshSpeed = isLoggedIn && speeds ? formatSpeed(speeds.mesh) : null;

    // Determine if stats are connected
    const isDhtConnected = isLoggedIn && displayedDhtPeers > 0;
    const isOverlayConnected = isLoggedIn && stats && stats.overlay > 0;
    const isNatResolved =
      isLoggedIn && stats && stats.natType && stats.natType !== 'Unknown';

    // Format NAT type tooltip
    const natTooltip =
      isLoggedIn && stats
        ? interfaceText('NAT Type: {natType}', {
          natType: stats.natType || interfaceText('Unknown'),
        })
        : interfaceText('NAT: Login to see stats');
    const telemetryErrors = [statsError, speedsError, buildInfoError]
      .filter(Boolean)
      .join(' ');
    const networkTooltip = isLoggedIn
      ? interfaceText('DHT peers: {dhtPeers}; DHT nodes: {dhtNodes}; mesh peers: {meshPeers}; hashes: {hashes}; seq: {seq}{errors}', {
        dhtPeers: formatCount(displayedDhtPeers),
        dhtNodes: formatCount(dhtNodes),
        meshPeers: formatCount(meshPeers),
        hashes: formatCount(hashCount),
        seq: formatCount(seqId),
        errors: telemetryErrors ? `; ${telemetryErrors}` : '',
      })
      : interfaceText('Login to see slskr network stats');

    return (
      <footer
        className="slskr-footer"
        ref={this.footerRef}
      >
        <div className="slskr-footer-content">
          <div className="slskr-footer-left">
            <div className="slskr-footer-brand">
              <a
                className="slskr-footer-github"
                href={GITHUB_BASE}
                rel="noopener noreferrer"
                target="_blank"
                title={interfaceText("Open slskr on GitHub")}
               {...interfaceTextProps("Open slskr on GitHub")}>
                <img
                  alt=""
                  aria-hidden="true"
                  src={`${urlBase}/slskr-mark.png`}
                />
                <Icon name="github" />
                <span><LocalizedText source={"GitHub"} /></span>
              </a>



              <span className="slskr-footer-copyright">
                © {year}{' '}
                <a
                  href={GITHUB_BASE}
                  rel="noopener noreferrer"
                  target="_blank"
                  title={interfaceText("slskr project")}
                 {...interfaceTextProps("slskr project")}>
                  <LocalizedText source={"slskr"} /></a>
              </span>
              <a
                className={`slskr-footer-build ${isUpdateAvailable ? 'update-available' : ''}`}
                href={isUpdateAvailable ? latestUrl : `${GITHUB_BASE}/releases`}
                rel="noopener noreferrer"
                target="_blank"
                title={
                  isUpdateAvailable
                  ? interfaceText('Running {currentBuild}; GitHub has {latestBuild}', {
                    currentBuild: fullBuild,
                    latestBuild: latestTag || latestBuild,
                  })
                    : interfaceText('Running {currentBuild}', { currentBuild: fullBuild })
                }
              >
                <Icon name={isUpdateAvailable ? 'bullhorn' : 'code branch'} />
          <span className="slskr-footer-build-label"><LocalizedText source={"Build"} /></span>
                <code>{currentBuild}</code>
                {isUpdateAvailable && (
                  <span className="slskr-footer-update-label">
                    <LocalizedText source={"update"} />{" "}{latestBuild}
                  </span>
                )}
              </a>
            </div>
          </div>

          <div className="slskr-footer-center">
            <div
              className={`slskr-footer-speeds ${isLoggedIn && speeds ? 'active' : ''}`}
              aria-label={interfaceText("Transfer speeds")}
             {...interfaceTextProps("Transfer speeds")}>
              <span className="slskr-footer-group-label"><LocalizedText source={"Speed"} /></span>
              <span
                className="slskr-footer-speed-item"
                title={
                  isLoggedIn
                    ? interfaceText('Total transfer speed (upload + download)')
                    : interfaceText('Login to see real-time speeds')
                }
              >
                <strong>T:</strong>{' '}
                <span className="speed-value">
                  {totalSpeed ? totalSpeed.value : '—'}
                </span>
                <span className="speed-unit">{totalSpeed ? totalSpeed.unit : ''}</span>
              </span>
              <span
                className="slskr-footer-speed-item"
                title={
                  isLoggedIn
                    ? interfaceText('Soulseek network speed')
                    : interfaceText('Login to see real-time speeds')
                }
              >
                <strong>S:</strong>{' '}
                <span className="speed-value">
                  {soulseekSpeed ? soulseekSpeed.value : '—'}
                </span>
                <span className="speed-unit">
                  {soulseekSpeed ? soulseekSpeed.unit : ''}
                </span>
              </span>
              <span
                className="slskr-footer-speed-item"
                title={
                  isLoggedIn
                    ? interfaceText('Mesh network speed')
                    : interfaceText('Login to see real-time speeds')
                }
              >
                <strong>M:</strong>{' '}
                <span className="speed-value">
                  {meshSpeed ? meshSpeed.value : '—'}
                </span>
                <span className="speed-unit">{meshSpeed ? meshSpeed.unit : ''}</span>
              </span>
            </div>
          </div>

          <div className="slskr-footer-right">
            <a
              className={`slskr-footer-network ${isLoggedIn && slskrStats ? 'active' : ''}`}
              href={`${urlBase}/system/network`}
              title={networkTooltip}
            >
              <span className="slskr-footer-group-label"><LocalizedText source={"Network"} /></span>
              <span className="slskr-footer-network-item">
                <Icon
                  color={displayedDhtPeers > 0 ? 'green' : 'grey'}
                  name="rss"
                />
                {formatCount(displayedDhtPeers)} <LocalizedText source={"dht"} /></span>
              <span className="slskr-footer-network-item">
                <Icon
                  color={meshPeers > 0 ? 'green' : 'grey'}
                  name="sitemap"
                />
                {formatCount(meshPeers)} <LocalizedText source={"mesh"} /></span>
              <span className="slskr-footer-network-item">
                <Icon
                  color={hashCount > 0 ? 'blue' : 'grey'}
                  name="database"
                />
                {formatCount(hashCount)} <LocalizedText source={"hashes"} /></span>
              <span
                className={`slskr-footer-network-item ${isSyncing ? 'syncing' : ''}`}
              >
                <Icon
                  color={isSyncing ? 'yellow' : 'grey'}
                  loading={isSyncing}
                  name="sync"
                />
                <LocalizedText source={"seq:"} />{seqId}
              </span>
              {activeSwarms > 0 && (
                <span className="slskr-footer-network-item active">
                  <Icon name="bolt" />
                  <LocalizedPluralText
                    count={activeSwarms}
                    other="swarms"
                    singular="swarm"
                    values={{ count: formatRegionalNumber(activeSwarms) }}
                  />
                </span>
              )}
              {backfillActive && (
                <span className="slskr-footer-network-item active">
                  <Icon
                    loading
                    name="clock"
                  />
                  <LocalizedText source={"backfill"} /></span>
              )}
              <span className="slskr-footer-network-item">
                <Icon name="trophy" />
                {karma > 0 ? '+' : ''}
                {formatRegionalNumber(karma)}
              </span>
            </a>

            <div
              className="slskr-footer-stats"
              aria-label={interfaceText("Transport health")}
              role="group"
             {...interfaceTextProps("Transport health")}>
              <Icon
                className={
                  isDhtConnected
                    ? 'slskr-footer-stat-icon connected'
                    : 'slskr-footer-stat-icon'
                }
                name="sitemap"
                title={
                  isLoggedIn && stats
                    ? interfaceText('DHT Nodes: {count}', { count: stats.dht })
                    : interfaceText('DHT: Login to see stats')
                }
              />
              <Icon
                className={
                  isNatResolved
                    ? 'slskr-footer-stat-icon connected'
                    : 'slskr-footer-stat-icon'
                }
                name="shield alternate"
                title={natTooltip}
              />
              <Icon
                className={
                  isOverlayConnected
                    ? 'slskr-footer-stat-icon connected'
                    : 'slskr-footer-stat-icon'
                }
                name="globe"
                title={
                  isLoggedIn && stats
                    ? interfaceText('Overlay Peers: {count}', { count: stats.overlay })
                    : interfaceText('Overlay: Login to see stats')
                }
              />
            </div>
          </div>
        </div>
      </footer>
    );
  }
}

const Footer = (props) => {
  useInterfaceLanguage();
  useRegionalFormat();
  return <FooterView {...props} />;
};

export default Footer;
