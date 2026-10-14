import LocalizedText from "../Shared/LocalizedText";
import { interfaceText, interfaceTextProps } from "../../lib/interfaceLocale";


import { urlBase } from '../../config';
import { toDisplayError } from '../../lib/errors';
import * as pods from '../../lib/pods';
import * as portForwarding from '../../lib/portForwarding';
import { createPollingController } from '../../lib/usePolling';
import React, { Component } from 'react';
import {
  Button,
  Card,
  Dimmer,
  Dropdown,
  Form,
  Icon,
  Input,
  Label,
  List,
  Loader,
  Message,
  Modal,
  Popup,
  Segment,
  Statistic,
  Tab,
  Table,
} from 'semantic-ui-react';

const initialState = {
  activeTab: 0,
  availablePorts: [],
  createForm: {
    destinationHost: '',
    destinationPort: '',
    localPort: '',
    serviceName: '',
  },
  creatingForwarding: false,
  error: null,
  forwardingStatus: [],
  forwardingStatusError: null,
  loading: false,
  pods: [],
  podsError: null,
  selectedPodDetail: null,
  selectedPodId: null,
  showCreateModal: false,
  stoppingForwarding: false,
  success: null,
  availablePortsError: null,
  vpnPodStatusError: null,
  vpnPodStatus: {},
};

const nonNegativeNumber = (value) => {
  const number = typeof value === 'number' ? value : Number(value);
  return Number.isFinite(number) && number >= 0 ? number : null;
};

const buildTunnelStats = (forwardingStatus) =>
  forwardingStatus.reduce((stats, forwarding) => {
    const bytesIn = nonNegativeNumber(forwarding.bytesIn);
    const bytesOut = nonNegativeNumber(forwarding.bytesOut);
    const startedAt = nonNegativeNumber(forwarding.startedAt);
    const lastActivity = nonNegativeNumber(forwarding.lastActivity);

    stats[forwarding.localPort] = {
      bytesIn,
      bytesOut,
      connections: nonNegativeNumber(forwarding.activeConnections) ?? 0,
      lastActivity,
      localPort: forwarding.localPort,
      uptime:
        startedAt === null ? null : Math.max(0, Date.now() - startedAt),
    };

    return stats;
  }, {});

class PortForwarding extends Component {
  constructor(props) {
    super(props);
    this.state = initialState;
    this.isMountedFlag = false;
    this.requestIds = {
      availablePorts: 0,
      createForwarding: 0,
      forwardingStatus: 0,
      podDetails: 0,
      pods: 0,
      vpnPodStatus: 0,
      stopForwarding: 0,
    };
    this.pollControllers = {
      status: null,
    };
    this.createInFlight = false;
    this.stopInFlight = false;
  }

  componentDidMount() {
    this.isMountedFlag = true;
    this.startPolling();
    void this.initializeComponent();
  }

  componentWillUnmount() {
    this.isMountedFlag = false;
    Object.keys(this.requestIds).forEach((key) => {
      this.requestIds[key] += 1;
    });
    this.stopPolling();
  }

  startPolling = () => {
    if (!this.pollControllers.status) {
      this.pollControllers.status = createPollingController(
        this.fetchForwardingStatus,
        5_000,
        { immediate: false },
      );
    }
  };

  stopPolling = () => {
    this.pollControllers.status?.stop();
    this.pollControllers.status = null;
  };

  initializeComponent = async () => {
    if (!this.isMountedFlag) return;
    this.setState({ error: null, loading: true });

    try {
      const podsList = await this.fetchPods();
      if (!this.isMountedFlag) return;
      await Promise.all([
        this.fetchAvailablePorts(),
        this.fetchForwardingStatus(),
        this.fetchVpnPodStatus(podsList),
      ]);
    } catch (error) {
      console.error('Failed to initialize port forwarding:', error);
      if (this.isMountedFlag) {
        this.setState({ error: toDisplayError(error, 'Failed to initialize port forwarding') });
      }
    } finally {
      if (this.isMountedFlag) this.setState({ loading: false });
    }
  };

  fetchPods = async () => {
    const requestId = ++this.requestIds.pods;
    try {
      const podsList = await pods.list();
      const normalizedPods = Array.isArray(podsList) ? podsList : [];
      if (
        this.isMountedFlag &&
        requestId === this.requestIds.pods
      ) {
        this.setState({ pods: normalizedPods, podsError: null });
      }
      return normalizedPods;
    } catch (error) {
      console.error('Failed to fetch pods:', error);
      if (
        this.isMountedFlag &&
        requestId === this.requestIds.pods
      ) {
        this.setState({
          podsError: toDisplayError(error, 'Failed to load pods'),
        });
      }
      return this.state.pods;
    }
  };

  fetchAvailablePorts = async () => {
    const requestId = ++this.requestIds.availablePorts;
    try {
      const result = await portForwarding.getAvailablePorts();
      if (
        this.isMountedFlag &&
        requestId === this.requestIds.availablePorts
      ) {
        this.setState({
          availablePorts: Array.isArray(result?.availablePorts)
            ? result.availablePorts
            : [],
          availablePortsError: null,
        });
      }
    } catch (error) {
      console.error('Failed to fetch available ports:', error);
      if (
        this.isMountedFlag &&
        requestId === this.requestIds.availablePorts
      ) {
        this.setState({
          availablePortsError: toDisplayError(
            error,
            'Failed to load available ports',
          ),
        });
      }
    }
  };

  fetchForwardingStatus = async () => {
    const requestId = ++this.requestIds.forwardingStatus;
    try {
      const status = await portForwarding.getForwardingStatus();
      const normalizedStatus = Array.isArray(status) ? status : [];
      if (
        this.isMountedFlag &&
        requestId === this.requestIds.forwardingStatus
      ) {
        this.setState({
          forwardingStatus: normalizedStatus,
          forwardingStatusError: null,
        });
      }
      return normalizedStatus;
    } catch (error) {
      console.error('Failed to fetch forwarding status:', error);
      if (
        this.isMountedFlag &&
        requestId === this.requestIds.forwardingStatus
      ) {
        this.setState({
          forwardingStatusError: toDisplayError(
            error,
            'Failed to load forwarding status',
          ),
        });
      }
      return [];
    }
  };

  fetchVpnPodStatus = async (podsList = this.state.pods) => {
    const requestId = ++this.requestIds.vpnPodStatus;
    const vpnCapablePods = podsList.filter(
      (pod) =>
        pod.capabilities?.includes('PrivateServiceGateway') ||
        pod.privateServicePolicy?.enabled === true,
    );

    const statusPromises = vpnCapablePods.map(async (pod) => {
      try {
        const detail = await pods.get(pod.podId);
        const memberCount = detail.members?.length || 0;
        const activeTunnels = nonNegativeNumber(detail.activeTunnels);
        const totalBandwidth = nonNegativeNumber(detail.totalBandwidth);

        return {
          activeTunnels,
          lastActivity: nonNegativeNumber(detail.lastActivity),
          members: memberCount,
          name: pod.name || pod.podId,
          podId: pod.podId,
          status: detail.privateServicePolicy?.enabled ? 'Active' : 'Inactive',
          totalBandwidth,
        };
      } catch (error) {
        console.error('Failed to fetch pod status', {
          error,
          podId: pod.podId,
        });
        return {
          activeTunnels: null,
          lastActivity: null,
          members: 0,
          name: pod.name || pod.podId,
          podId: pod.podId,
          status: 'Error',
          totalBandwidth: null,
        };
      }
    });

    try {
      const statusResults = await Promise.all(statusPromises);
      const status = statusResults.reduce((accumulator, stat) => {
        accumulator[stat.podId] = stat;
        return accumulator;
      }, {});

      if (
        this.isMountedFlag &&
        requestId === this.requestIds.vpnPodStatus
      ) {
        this.setState({
          vpnPodStatus: status,
          vpnPodStatusError: Object.values(status).some(
            (pod) => pod.status === 'Error',
          )
            ? 'One or more VPN pod status checks failed.'
            : null,
        });
      }
    } catch (error) {
      console.error('Failed to fetch VPN pod status:', error);
      if (
        this.isMountedFlag &&
        requestId === this.requestIds.vpnPodStatus
      ) {
        this.setState({
          vpnPodStatusError: toDisplayError(
            error,
            'Failed to load VPN pod status',
          ),
        });
      }
    }
  };

  handlePodSelection = async (podId) => {
    if (!this.isMountedFlag) return;
    const requestId = ++this.requestIds.podDetails;
    this.setState({
      loading: true,
      selectedPodDetail: null,
      selectedPodId: podId,
    });

    try {
      const podDetail = await pods.get(podId);
      if (
        this.isMountedFlag &&
        requestId === this.requestIds.podDetails
      ) {
        this.setState({ selectedPodDetail: podDetail });
      }
    } catch (error) {
      console.error('Failed to fetch pod detail:', error);
      if (
        this.isMountedFlag &&
        requestId === this.requestIds.podDetails
      ) {
        this.setState({
          error: `Failed to load pod details: ${toDisplayError(error)}`,
        });
      }
    } finally {
      if (
        this.isMountedFlag &&
        requestId === this.requestIds.podDetails
      ) {
        this.setState({ loading: false });
      }
    }
  };

  handleCreateForwarding = async () => {
    const { createForm, selectedPodId } = this.state;

    if (!selectedPodId) {
      this.setState({ error: 'Please select a pod first' });
      return;
    }

    // Validate form
    if (
      !createForm.localPort ||
      !createForm.destinationHost ||
      !createForm.destinationPort
    ) {
      this.setState({ error: 'Please fill in all required fields' });
      return;
    }

    if (this.state.creatingForwarding || this.createInFlight) return;

    const localPort = Number.parseInt(createForm.localPort, 10);
    const destinationPort = Number.parseInt(createForm.destinationPort, 10);

    if (isNaN(localPort) || localPort < 1_024 || localPort > 65_535) {
      this.setState({ error: 'Local port must be between 1024 and 65535' });
      return;
    }

    if (
      isNaN(destinationPort) ||
      destinationPort < 1 ||
      destinationPort > 65_535
    ) {
      this.setState({ error: 'Destination port must be between 1 and 65535' });
      return;
    }

    const requestId = ++this.requestIds.createForwarding;
    this.createInFlight = true;
    this.setState({ creatingForwarding: true, error: null });

    try {
      await portForwarding.startForwarding({
        destinationHost: createForm.destinationHost,
        destinationPort,
        localPort,
        podId: selectedPodId,
        serviceName: createForm.serviceName || undefined,
      });

      if (
        !this.isMountedFlag ||
        requestId !== this.requestIds.createForwarding
      ) {
        return;
      }
      // Reset form and refresh status
      this.setState({
        createForm: initialState.createForm,
        showCreateModal: false,
      });

      await Promise.all([
        this.fetchAvailablePorts(),
        this.fetchForwardingStatus(),
      ]);
    } catch (error) {
      console.error('Failed to create port forwarding:', error);
      if (
        this.isMountedFlag &&
        requestId === this.requestIds.createForwarding
      ) {
        this.setState({
          error: toDisplayError(error, 'Failed to create port forwarding'),
        });
      }
    } finally {
      if (
        this.isMountedFlag &&
        requestId === this.requestIds.createForwarding
      ) {
        this.setState({ creatingForwarding: false });
      }
      this.createInFlight = false;
    }
  };

  handleStopForwarding = async (localPort) => {
    if (
      !this.isMountedFlag ||
      this.state.stoppingForwarding ||
      this.stopInFlight
    ) return;
    const requestId = ++this.requestIds.stopForwarding;
    this.stopInFlight = true;
    this.setState({ error: null, stoppingForwarding: true, success: null });

    try {
      await portForwarding.stopForwarding(localPort);
      await Promise.all([
        this.fetchAvailablePorts(),
        this.fetchForwardingStatus(),
      ]);
      if (
        this.isMountedFlag &&
        requestId === this.requestIds.stopForwarding
      ) {
        this.setState({
          success: `Successfully stopped forwarding on port ${localPort}`,
        });
      }
    } catch (error) {
      console.error('Failed to stop port forwarding:', error);
      if (
        this.isMountedFlag &&
        requestId === this.requestIds.stopForwarding
      ) {
        this.setState({
          error: toDisplayError(error, 'Failed to stop port forwarding'),
        });
      }
    } finally {
      if (
        this.isMountedFlag &&
        requestId === this.requestIds.stopForwarding
      ) {
        this.setState({ stoppingForwarding: false });
      }
      this.stopInFlight = false;
    }
  };

  handleFormChange = (field, value) => {
    this.setState((previousState) => ({
      createForm: {
        ...previousState.createForm,
        [field]: value,
      },
    }));
  };

  render() {
    const {
      availablePorts,
      createForm,
      creatingForwarding,
      error,
      forwardingStatus,
      forwardingStatusError,
      loading,
      pods,
      podsError,
      selectedPodDetail,
      selectedPodId,
      showCreateModal,
      stoppingForwarding,
      success,
      availablePortsError,
      vpnPodStatusError,
      vpnPodStatus,
    } = this.state;

    // Filter pods that have VPN gateway capability
    const vpnCapablePods = pods.filter(
      (pod) =>
        pod.capabilities?.includes('PrivateServiceGateway') ||
        pod.privateServicePolicy?.enabled === true,
    );

    const tunnelStats = buildTunnelStats(forwardingStatus);
    const tunnelStatValues = Object.values(tunnelStats);
    const activeForwardingCount = forwardingStatus.filter(
      (forwarding) => forwarding.isActive,
    ).length;
    const totalConnections = tunnelStatValues.reduce(
      (sum, stats) => sum + stats.connections,
      0,
    );
    const byteStats = tunnelStatValues.filter(
      (stats) => stats.bytesIn !== null || stats.bytesOut !== null,
    );
    const totalBytes = byteStats.reduce(
      (sum, stats) => sum + (stats.bytesIn || 0) + (stats.bytesOut || 0),
      0,
    );
    const uptimeStats = tunnelStatValues.filter(
      (stats) => stats.uptime !== null,
    );
    const knownActiveTunnelCount = Object.values(vpnPodStatus).filter(
      (pod) => pod.activeTunnels !== null,
    ).length;
    const totalActiveTunnels = Object.values(vpnPodStatus).reduce(
      (sum, pod) => sum + (pod.activeTunnels || 0),
      0,
    );

    const panes = [
      {
        menuItem: 'Active Forwarding',
        render: () => (
          <Tab.Pane>
            {forwardingStatusError && (
              <Message
                data-testid="port-forwarding-status-error"
                error
              >
                <Message.Header><LocalizedText source={"Forwarding status unavailable"} /></Message.Header>
                <p>{forwardingStatusError}</p>
                <p><LocalizedText source={"Showing the last successfully received forwarding status."} /></p>
              </Message>
            )}
            {forwardingStatus.length === 0 ? (
              <Segment placeholder>
                <Icon name="exchange" />
                <h3>
                  {forwardingStatusError
                    ? <LocalizedText source={"Forwarding status unavailable"} />
                    : <LocalizedText source={"No active port forwarding"} />}
                </h3>
                <p>
                  {forwardingStatusError
                    ? <LocalizedText source={"The daemon did not return the current forwarding status."} />
                    : <LocalizedText source={"Start forwarding local ports to remote services through VPN tunnels."} />}
                </p>
                <Button
                  disabled={vpnCapablePods.length === 0}
                  onClick={() => this.setState({ showCreateModal: true })}
                  primary
                >
                  <LocalizedText source={"Start Forwarding"} /></Button>
              </Segment>
            ) : (
              <div>
                <div style={{ marginBottom: '20px', textAlign: 'right' }}>
                  <Button
                    disabled={vpnCapablePods.length === 0}
                    onClick={() => this.setState({ showCreateModal: true })}
                    primary
                  >
                    <Icon name="plus" />
                    <LocalizedText source={"Add Forwarding"} /></Button>
                </div>

                <Table celled>
                  <Table.Header>
                    <Table.Row>
                      <Table.HeaderCell><LocalizedText source={"Local Port"} /></Table.HeaderCell>
                      <Table.HeaderCell><LocalizedText source={"Pod"} /></Table.HeaderCell>
                      <Table.HeaderCell><LocalizedText source={"Remote Service"} /></Table.HeaderCell>
                      <Table.HeaderCell><LocalizedText source={"Status"} /></Table.HeaderCell>
                      <Table.HeaderCell><LocalizedText source={"Connections"} /></Table.HeaderCell>
                      <Table.HeaderCell><LocalizedText source={"Data Transferred"} /></Table.HeaderCell>
                      <Table.HeaderCell><LocalizedText source={"Actions"} /></Table.HeaderCell>
                    </Table.Row>
                  </Table.Header>
                  <Table.Body>
                    {forwardingStatus.map((forwarding) => (
                      <Table.Row key={forwarding.localPort}>
                        <Table.Cell>
                          <code>localhost:{forwarding.localPort}</code>
                        </Table.Cell>
                        <Table.Cell>
                          {forwarding.podId}
                          {forwarding.serviceName && (
                            <div style={{ color: 'var(--slskr-color-subtle, #666)', fontSize: '0.8em' }}>
                              <LocalizedText source={"Service:"} />{" "}{forwarding.serviceName}
                            </div>
                          )}
                        </Table.Cell>
                        <Table.Cell>
                          <code>
                            {forwarding.destinationHost}:
                            {forwarding.destinationPort}
                          </code>
                        </Table.Cell>
                        <Table.Cell>
                          <Label color={forwarding.isActive ? 'green' : 'red'}>
                            {forwarding.isActive ? <LocalizedText source={"Active"} /> : <LocalizedText source={"Inactive"} />}
                          </Label>
                        </Table.Cell>
                        <Table.Cell>{forwarding.activeConnections}</Table.Cell>
                        <Table.Cell>
                          {forwarding.bytesForwarded > 0
                            ? `${(forwarding.bytesForwarded / 1_024).toFixed(1)} KB`
                            : <LocalizedText source={"0 KB"} />}
                        </Table.Cell>
                        <Table.Cell>
                          <Popup
                            content={interfaceText("Stop port forwarding")}
                            trigger={
                              <Button
                                color="red"
                                icon="stop"
                                loading={stoppingForwarding}
                                onClick={() =>
                                  this.handleStopForwarding(
                                    forwarding.localPort,
                                  )
                                }
                                size="small"
                              />
                            }
                           {...interfaceTextProps("Stop port forwarding")}/>
                        </Table.Cell>
                      </Table.Row>
                    ))}
                  </Table.Body>
                </Table>
              </div>
            )}
          </Tab.Pane>
        ),
      },
      {
        menuItem: 'Available Ports',
        render: () => (
          <Tab.Pane>
            {availablePortsError && (
              <Message
                data-testid="available-ports-error"
                error
              >
                <Message.Header><LocalizedText source={"Available ports unavailable"} /></Message.Header>
                <p>{availablePortsError}</p>
              </Message>
            )}
            <div style={{ marginBottom: '20px' }}>
              <Statistic.Group size="small">
                <Statistic>
                  <Statistic.Value>{availablePorts.length}</Statistic.Value>
                  <Statistic.Label><LocalizedText source={"Available Ports"} /></Statistic.Label>
                </Statistic>
                <Statistic>
                  <Statistic.Value>{forwardingStatus.length}</Statistic.Value>
                  <Statistic.Label><LocalizedText source={"In Use"} /></Statistic.Label>
                </Statistic>
              </Statistic.Group>
            </div>

            <Segment>
              <p><LocalizedText source={"Available ports for forwarding (1024-65535):"} /></p>
              <div
                style={{
                  backgroundColor: 'var(--slskr-color-inset, #f8f9fa)',
                  borderRadius: '4px',
                  fontFamily: 'monospace',
                  fontSize: '12px',
                  maxHeight: '400px',
                  overflowY: 'auto',
                  padding: '10px',
                }}
              >
                {availablePorts.length > 0 ? (
                  availablePorts.slice(0, 100).join(', ') +
                  (availablePorts.length > 100
                    ? ` ... (+${availablePorts.length - 100} more)`
                    : '')
                ) : (
                  <em>
                    {availablePortsError
                      ? <LocalizedText source={"Available ports are unavailable."} />
                      : <LocalizedText source={"No ports available or still loading..."} />}
                  </em>
                )}
              </div>
            </Segment>
          </Tab.Pane>
        ),
      },
      {
        menuItem: 'Tunnel Statistics',
        render: () => (
          <Tab.Pane>
            <div style={{ marginBottom: '20px' }}>
              <Statistic.Group widths="four">
                <Statistic>
                  <Statistic.Value>{activeForwardingCount}</Statistic.Value>
                  <Statistic.Label><LocalizedText source={"Active Tunnels"} /></Statistic.Label>
                </Statistic>
                <Statistic>
                  <Statistic.Value>
                    {totalConnections}
                  </Statistic.Value>
                  <Statistic.Label><LocalizedText source={"Total Connections"} /></Statistic.Label>
                </Statistic>
                <Statistic>
                  <Statistic.Value>
                    {byteStats.length > 0
                      ? `${(totalBytes / 1_024 / 1_024).toFixed(2)} MB`
                      : interfaceText('N/A')}
                  </Statistic.Value>
                  <Statistic.Label><LocalizedText source={"Data Transferred"} /></Statistic.Label>
                </Statistic>
                <Statistic>
                  <Statistic.Value>
                    {uptimeStats.length > 0
                      ? (
                          uptimeStats.reduce(
                            (sum, stats) => sum + stats.uptime,
                            0,
                          ) /
                          uptimeStats.length /
                          1_000 /
                          60
                        ).toFixed(1)
                      : interfaceText('N/A')}{' '}
                    {uptimeStats.length > 0 && 'min'}
                  </Statistic.Value>
                  <Statistic.Label><LocalizedText source={"Avg Uptime"} /></Statistic.Label>
                </Statistic>
              </Statistic.Group>
            </div>

            <Table celled>
              <Table.Header>
                <Table.Row>
                  <Table.HeaderCell><LocalizedText source={"Local Port"} /></Table.HeaderCell>
                  <Table.HeaderCell><LocalizedText source={"Data In"} /></Table.HeaderCell>
                  <Table.HeaderCell><LocalizedText source={"Data Out"} /></Table.HeaderCell>
                  <Table.HeaderCell><LocalizedText source={"Connections"} /></Table.HeaderCell>
                  <Table.HeaderCell><LocalizedText source={"Uptime"} /></Table.HeaderCell>
                  <Table.HeaderCell><LocalizedText source={"Last Activity"} /></Table.HeaderCell>
                </Table.Row>
              </Table.Header>
              <Table.Body>
                {forwardingStatus.map((forwarding) => {
                  const stats = tunnelStats[forwarding.localPort];
                  return (
                    <Table.Row key={forwarding.localPort}>
                      <Table.Cell>
                        <code>localhost:{forwarding.localPort}</code>
                      </Table.Cell>
                      <Table.Cell>
                        {stats?.bytesIn !== null &&
                        stats?.bytesIn !== undefined
                          ? `${(stats.bytesIn / 1_024).toFixed(1)} KB`
                          : interfaceText('N/A')}
                      </Table.Cell>
                      <Table.Cell>
                        {stats?.bytesOut !== null &&
                        stats?.bytesOut !== undefined
                          ? `${(stats.bytesOut / 1_024).toFixed(1)} KB`
                          : interfaceText('N/A')}
                      </Table.Cell>
                      <Table.Cell>{stats?.connections ?? <LocalizedText source="N/A" />}</Table.Cell>
                      <Table.Cell>
                        {stats?.uptime !== null && stats?.uptime !== undefined
                          ? `${Math.floor(stats.uptime / 1_000 / 60)}m ${Math.floor((stats.uptime / 1_000) % 60)}s`
                          : interfaceText('N/A')}
                      </Table.Cell>
                      <Table.Cell>
                        {stats?.lastActivity !== null &&
                        stats?.lastActivity !== undefined
                          ? interfaceText("{seconds}s ago", { seconds: Math.max(0, Math.floor((Date.now() - stats.lastActivity) / 1_000)) })
                          : interfaceText('N/A')}
                      </Table.Cell>
                    </Table.Row>
                  );
                })}
                {forwardingStatus.length === 0 && (
                  <Table.Row>
                    <Table.Cell
                      colSpan={6}
                      textAlign="center"
                    >
                      <LocalizedText source={"No active tunnels to display statistics for"} /></Table.Cell>
                  </Table.Row>
                )}
              </Table.Body>
            </Table>
          </Tab.Pane>
        ),
      },
      {
        menuItem: 'VPN Pods',
        render: () => (
          <Tab.Pane>
            {podsError && (
              <Message
                data-testid="vpn-pods-load-error"
                error
              >
                <Message.Header><LocalizedText source={"VPN pod list unavailable"} /></Message.Header>
                <p>{podsError}</p>
              </Message>
            )}
            {vpnPodStatusError && (
              <Message
                data-testid="vpn-pod-status-error"
                warning
              >
                <Message.Header><LocalizedText source={"VPN pod status incomplete"} /></Message.Header>
                <p>{vpnPodStatusError}</p>
              </Message>
            )}
            <div style={{ marginBottom: '20px' }}>
              <Statistic.Group widths="three">
                <Statistic>
                  <Statistic.Value>
                    {Object.keys(vpnPodStatus).length}
                  </Statistic.Value>
                  <Statistic.Label><LocalizedText source={"VPN-Capable Pods"} /></Statistic.Label>
                </Statistic>
                <Statistic>
                  <Statistic.Value>
                    {Object.values(vpnPodStatus).reduce(
                      (sum, pod) => sum + pod.members,
                      0,
                    )}
                  </Statistic.Value>
                  <Statistic.Label><LocalizedText source={"Total Members"} /></Statistic.Label>
                </Statistic>
                <Statistic>
                  <Statistic.Value>
                    {knownActiveTunnelCount > 0
                      ? totalActiveTunnels
                      : interfaceText('N/A')}
                  </Statistic.Value>
                  <Statistic.Label><LocalizedText source={"Active Tunnels"} /></Statistic.Label>
                </Statistic>
              </Statistic.Group>
            </div>

            <Table celled>
              <Table.Header>
                <Table.Row>
                  <Table.HeaderCell><LocalizedText source={"Pod Name"} /></Table.HeaderCell>
                  <Table.HeaderCell><LocalizedText source={"Members"} /></Table.HeaderCell>
                  <Table.HeaderCell><LocalizedText source={"Active Tunnels"} /></Table.HeaderCell>
                  <Table.HeaderCell><LocalizedText source={"Data Transferred"} /></Table.HeaderCell>
                  <Table.HeaderCell><LocalizedText source={"Status"} /></Table.HeaderCell>
                  <Table.HeaderCell><LocalizedText source={"Last Activity"} /></Table.HeaderCell>
                </Table.Row>
              </Table.Header>
              <Table.Body>
                {Object.values(vpnPodStatus).map((pod) => (
                  <Table.Row key={pod.podId}>
                    <Table.Cell>
                      <strong>{pod.name}</strong>
                      <div style={{ color: 'var(--slskr-color-subtle, #666)', fontSize: '0.8em' }}>
                        ID: {pod.podId}
                      </div>
                    </Table.Cell>
                    <Table.Cell>{pod.members}</Table.Cell>
                    <Table.Cell>{pod.activeTunnels ?? <LocalizedText source="N/A" />}</Table.Cell>
                    <Table.Cell>
                      {pod.totalBandwidth !== null && pod.totalBandwidth > 0
                        ? `${(pod.totalBandwidth / 1_024 / 1_024).toFixed(2)} MB`
                        : pod.totalBandwidth === null
                          ? <LocalizedText source="N/A" />
                          : <LocalizedText source="0 MB" />}
                    </Table.Cell>
                    <Table.Cell>
                      <Label color={pod.status === 'Active' ? 'green' : 'grey'}>
                        <LocalizedText source={pod.status} />
                      </Label>
                    </Table.Cell>
                    <Table.Cell>
                      {pod.lastActivity === null
                        ? <LocalizedText source="N/A" />
                        : interfaceText("{seconds}s ago", { seconds: Math.max(0, Math.floor((Date.now() - pod.lastActivity) / 1_000)) })}
                    </Table.Cell>
                  </Table.Row>
                ))}
                {Object.keys(vpnPodStatus).length === 0 && (
                  <Table.Row>
                    <Table.Cell
                      colSpan={6}
                      textAlign="center"
                    >
                      <LocalizedText source={"No VPN-capable pods found"} /></Table.Cell>
                  </Table.Row>
                )}
              </Table.Body>
            </Table>
          </Tab.Pane>
        ),
      },
    ];

    return (
      <div style={{ padding: '20px' }}>
        <Dimmer active={loading}>
          <Loader />
        </Dimmer>

        <div style={{ marginBottom: '30px' }}>
          <h2><LocalizedText source={"Port Forwarding"} /></h2>
          <p>
            <LocalizedText source={"Forward local ports to remote services through secure VPN tunnels."} /></p>
        </div>

        {error && (
          <Message error>
            <Message.Header><LocalizedText source={"Error"} /></Message.Header>
            <p>{error}</p>
            <Button
              onClick={() => this.setState({ error: null })}
              size="small"
            >
              <LocalizedText source={"Dismiss"} /></Button>
          </Message>
        )}

        {success && (
          <Message success>
            <Message.Header><LocalizedText source={"Success"} /></Message.Header>
            <p>{success}</p>
            <Button
              onClick={() => this.setState({ success: null })}
              size="small"
            >
              <LocalizedText source={"Dismiss"} /></Button>
          </Message>
        )}

        {podsError ? (
          <Message
            data-testid="port-forwarding-pods-error"
            error
          >
            <Message.Header><LocalizedText source={"VPN pod list unavailable"} /></Message.Header>
            <p>{podsError}</p>
            <p><LocalizedText source={"VPN capability cannot be determined until the pod list reloads."} /></p>
          </Message>
        ) : vpnCapablePods.length === 0 && (
          <Message warning>
            <Message.Header><LocalizedText source={"No VPN-Capable Pods"} /></Message.Header>
            <p>
              <LocalizedText source={"You need at least one pod with VPN gateway capability to use port forwarding."} /></p>
            <p>
              <LocalizedText source={"Create or join a pod that has the"} />{' '}
              <code>PrivateServiceGateway</code> <LocalizedText source={"capability enabled."} /></p>
          </Message>
        )}

        <Tab
          activeIndex={this.state.activeTab}
          menu={{ pointing: true }}
          onTabChange={(_event, { activeIndex }) =>
            this.setState({ activeTab: activeIndex })
          }
          panes={panes}
          renderActiveOnly={false}
        />

        {/* Create Forwarding Modal */}
        <Modal
          onClose={() => this.setState({ showCreateModal: false })}
          open={showCreateModal}
          size="small"
        >
          <Modal.Header><LocalizedText source={"Start Port Forwarding"} /></Modal.Header>
          <Modal.Content>
            <Form>
              <Form.Field>
                <label><LocalizedText source={"VPN Pod"} /></label>
                <Dropdown
                  fluid
                  onChange={(e, { value }) => this.handlePodSelection(value)}
                  options={vpnCapablePods.map((pod) => ({
                    key: pod.podId,
                    text: pod.name || pod.podId,
                    value: pod.podId,
                  }))}
                  placeholder={interfaceText("Select a VPN-capable pod")}
                  selection
                  value={selectedPodId || ''}
                 {...interfaceTextProps("Select a VPN-capable pod")}/>
                {selectedPodDetail && (
                  <div
                    style={{
                      color: 'var(--slskr-color-subtle, #666)',
                      fontSize: '0.9em',
                      marginTop: '10px',
                    }}
                  >
                    <p>
                      <strong><LocalizedText source={"Members:"} /></strong>{' '}
                      {selectedPodDetail.members?.length || 0}
                    </p>
                    {selectedPodDetail.privateServicePolicy?.enabled && (
                      <p>
                        <strong><LocalizedText source={"VPN Gateway:"} /></strong> <LocalizedText source={"Enabled"} /></p>
                    )}
                  </div>
                )}
              </Form.Field>

              <Form.Field required>
                <label><LocalizedText source={"Local Port"} /></label>
                <Input
                  max="65535"
                  min="1024"
                  onChange={(e) =>
                    this.handleFormChange('localPort', e.target.value)
                  }
                  placeholder={interfaceText("e.g., 8080")}
                  type="number"
                  value={createForm.localPort}
                 {...interfaceTextProps("e.g., 8080")}/>
                <small style={{ color: 'var(--slskr-color-subtle, #666)' }}>
                  <LocalizedText source={"Port on your local machine (1024-65535)"} /></small>
              </Form.Field>

              <Form.Field required>
                <label><LocalizedText source={"Remote Host"} /></label>
                <Input
                  onChange={(e) =>
                    this.handleFormChange('destinationHost', e.target.value)
                  }
                  placeholder={interfaceText("e.g., database.internal.company.com")}
                  value={createForm.destinationHost}
                 {...interfaceTextProps("e.g., database.internal.company.com")}/>
                <small style={{ color: 'var(--slskr-color-subtle, #666)' }}>
                  <LocalizedText source={"Hostname or IP address of the remote service"} /></small>
              </Form.Field>

              <Form.Field required>
                <label><LocalizedText source={"Remote Port"} /></label>
                <Input
                  max="65535"
                  min="1"
                  onChange={(e) =>
                    this.handleFormChange('destinationPort', e.target.value)
                  }
                  placeholder={interfaceText("e.g., 5432")}
                  type="number"
                  value={createForm.destinationPort}
                 {...interfaceTextProps("e.g., 5432")}/>
                <small style={{ color: 'var(--slskr-color-subtle, #666)' }}>
                  <LocalizedText source={"Port number of the remote service"} /></small>
              </Form.Field>

              <Form.Field>
                <label><LocalizedText source={"Service Name (Optional)"} /></label>
                <Input
                  onChange={(e) =>
                    this.handleFormChange('serviceName', e.target.value)
                  }
                  placeholder={interfaceText("e.g., postgres-db")}
                  value={createForm.serviceName}
                 {...interfaceTextProps("e.g., postgres-db")}/>
                <small style={{ color: 'var(--slskr-color-subtle, #666)' }}>
                  <LocalizedText source={"Named service registered in the pod (for better organization)"} /></small>
              </Form.Field>
            </Form>
          </Modal.Content>
          <Modal.Actions>
            <Button onClick={() => this.setState({ showCreateModal: false })}>
              <LocalizedText source={"Cancel"} /></Button>
            <Button
              disabled={
                !selectedPodId ||
                !createForm.localPort ||
                !createForm.destinationHost ||
                !createForm.destinationPort
              }
              loading={creatingForwarding}
              onClick={this.handleCreateForwarding}
              primary
            >
              <LocalizedText source={"Start Forwarding"} /></Button>
          </Modal.Actions>
        </Modal>
      </div>
    );
  }
}

export default PortForwarding;
