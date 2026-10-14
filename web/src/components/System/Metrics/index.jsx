import LocalizedText from "../../Shared/LocalizedText";
import { interfaceText, interfaceTextProps, useInterfaceLanguage } from "../../../lib/interfaceLocale";
import {
  formatBytesFixed,
  formatRegionalCompactNumber,
  formatRegionalTime,
  useRegionalFormat,
} from '../../../lib/util';
import { getKpiMetrics } from '../../../lib/telemetry';
import { toDisplayError } from '../../../lib/errors';
import { LoaderSegment } from '../../Shared';
import { useMountedRef } from '../../../lib/useMountedRef';
import React, { useCallback, useEffect, useRef, useState } from 'react';
import {
  Divider,
  Button,
  Grid,
  Header,
  Icon,
  Message,
  Segment,
  Statistic,
  Table,
} from 'semantic-ui-react';

const formatBytes = (bytes) => {
  const numericBytes = Number(bytes);
  if (!Number.isFinite(numericBytes) || numericBytes <= 0) {
    return formatBytesFixed(0, 1);
  }
  return formatBytesFixed(numericBytes, 1);
};

const formatNumber = (value) => {
  if (value === undefined || value === null) return '—';
  return formatRegionalCompactNumber(value, { smallMaximumFractionDigits: 2 });
};

// Extract the first sample value from a metric, or null
const sampleValue = (metric) => {
  if (!metric) return null;
  if (Array.isArray(metric.samples) && metric.samples.length > 0) {
    return metric.samples[0]?.value ?? null;
  }
  return null;
};

const KPI_GROUPS = [
  {
    key: 'transfers',
    get title() { return interfaceText("Transfers"); },
    icon: 'exchange',
    metrics: [
      { key: 'slskr_uploads_total', get label() { return interfaceText("Uploads Total"); }, format: formatNumber },
      { key: 'slskr_downloads_total', get label() { return interfaceText("Downloads Total"); }, format: formatNumber },
      { key: 'slskr_uploads_active', get label() { return interfaceText("Uploads Active"); }, format: formatNumber },
      { key: 'slskr_downloads_active', get label() { return interfaceText("Downloads Active"); }, format: formatNumber },
      { key: 'slskr_uploads_queued', get label() { return interfaceText("Uploads Queued"); }, format: formatNumber },
      { key: 'slskr_downloads_queued', get label() { return interfaceText("Downloads Queued"); }, format: formatNumber },
    ],
  },
  {
    key: 'search',
    get title() { return interfaceText("Search"); },
    icon: 'search',
    metrics: [
      { key: 'slskr_searches_incoming_requests_total', get label() { return interfaceText("Incoming Requests"); }, format: formatNumber },
      { key: 'slskr_searches_incoming_requests_dropped_total', get label() { return interfaceText("Dropped Requests"); }, format: formatNumber },
      { key: 'slskr_searches_outgoing_total', get label() { return interfaceText("Outgoing Searches"); }, format: formatNumber },
    ],
  },
  {
    key: 'process',
    get title() { return interfaceText("Process"); },
    icon: 'microchip',
    metrics: [
      { key: 'process_working_set_bytes', get label() { return interfaceText("Working Set"); }, format: formatBytes },
      { key: 'dotnet_total_memory_bytes', get label() { return interfaceText("Managed Memory"); }, format: formatBytes },
      { key: 'process_cpu_seconds_total', get label() { return interfaceText("CPU Seconds"); }, format: formatNumber },
    ],
  },
  {
    key: 'network',
    get title() { return interfaceText("Network"); },
    icon: 'wifi',
    metrics: [
      { key: 'microsoft_aspnetcore_server_kestrel_current_connections', get label() { return interfaceText("Kestrel Connections"); }, format: formatNumber },
      { key: 'system_net_sockets_connections_established_total', get label() { return interfaceText("Sockets Established"); }, format: formatNumber },
    ],
  },
];

const MetricGroup = ({ group, metrics }) => {
  useInterfaceLanguage();
  const normalizedMetrics = metrics && typeof metrics === 'object' ? metrics : {};
  const items = group.metrics
    .map(({ key, label, format }) => ({
      label,
      value: sampleValue(normalizedMetrics[key]),
      format,
    }))
    .filter(({ value }) => value !== null);

  if (items.length === 0) return null;

  return (
    <Segment>
      <Header size="small">
        <Icon name={group.icon} />
        {group.title}
      </Header>
      <Statistic.Group size="mini">
        {items.map(({ label, value, format }) => (
          <Statistic key={label}>
            <Statistic.Value>{format(value)}</Statistic.Value>
            <Statistic.Label>{label}</Statistic.Label>
          </Statistic>
        ))}
      </Statistic.Group>
    </Segment>
  );
};

const SlskrMetricsTable = ({ metrics }) => {
  useInterfaceLanguage();
  const slskrMetrics = Object.entries(
    metrics && typeof metrics === 'object' ? metrics : {},
  )
    .filter(([key]) => key.startsWith('slskr_'))
    .sort(([a], [b]) => a.localeCompare(b));

  if (slskrMetrics.length === 0) return null;

  return (
    <Segment>
      <Header size="small">
        <Icon name="table" />
        <LocalizedText source={"All slskr Metrics"} /></Header>
      <Table
        compact
        size="small"
        striped
      >
        <Table.Header>
          <Table.Row>
            <Table.HeaderCell><LocalizedText source={"Metric"} /></Table.HeaderCell>
            <Table.HeaderCell><LocalizedText source={"Type"} /></Table.HeaderCell>
            <Table.HeaderCell><LocalizedText source={"Value"} /></Table.HeaderCell>
            <Table.HeaderCell><LocalizedText source={"Help"} /></Table.HeaderCell>
          </Table.Row>
        </Table.Header>
        <Table.Body>
          {slskrMetrics.map(([key, metric]) => (
            <Table.Row key={key}>
              <Table.Cell>
                <code style={{ fontSize: '0.85em' }}>{key}</code>
              </Table.Cell>
              <Table.Cell>{metric.type}</Table.Cell>
              <Table.Cell>{formatNumber(sampleValue(metric))}</Table.Cell>
              <Table.Cell style={{ color: 'grey', fontSize: '0.9em' }}>{metric.help}</Table.Cell>
            </Table.Row>
          ))}
        </Table.Body>
      </Table>
    </Segment>
  );
};

const Metrics = () => {
  useInterfaceLanguage();
  useRegionalFormat();
  const [metrics, setMetrics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [lastUpdated, setLastUpdated] = useState(null);
  const mountedRef = useMountedRef();
  const requestIdRef = useRef(0);
  const inFlightRef = useRef(false);

  const fetchMetrics = useCallback(async () => {
    if (!mountedRef.current || inFlightRef.current) return;
    const requestId = ++requestIdRef.current;
    inFlightRef.current = true;
    setLoading(true);
    setError(null);
    try {
      const data = await getKpiMetrics();
      if (
        !mountedRef.current ||
        requestIdRef.current !== requestId
      ) {
        return;
      }
      setMetrics(data && typeof data === 'object' ? data : {});
      setLastUpdated(new Date());
    } catch (err) {
      if (
        mountedRef.current &&
        requestIdRef.current === requestId
      ) {
        setError(toDisplayError(err, 'Failed to load metrics'));
      }
    } finally {
      if (
        mountedRef.current &&
        requestIdRef.current === requestId
      ) {
        setLoading(false);
      }
      inFlightRef.current = false;
    }
  }, [mountedRef]);

  useEffect(() => {
    void fetchMetrics();
  }, [fetchMetrics]);

  if (loading && !metrics) return <LoaderSegment />;

  if (error && !metrics) {
    return (
      <Message
        error
        header={interfaceText("Failed to load metrics")}
        content={error}
       {...interfaceTextProps("Failed to load metrics")}/>
    );
  }

  return (
    <div>
      {error && (
        <Message
          data-testid="metrics-load-error"
          error
        >
          <Message.Header><LocalizedText source={"Metrics refresh failed"} /></Message.Header>
          <p>{error}</p>
          <p><LocalizedText source={"Showing the last successfully loaded metrics snapshot."} /></p>
        </Message>
      )}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1em' }}>
        <Header size="medium">
          <Icon name="chart bar" />
          <LocalizedText source={"Prometheus Metrics"} /></Header>
        <Button
          basic
          onClick={fetchMetrics}
          size="small"
          type="button"
        >
          <Icon name="refresh" />
          {lastUpdated
            ? <LocalizedText source={"Updated {timestamp}"} values={{ "timestamp": formatRegionalTime(lastUpdated) }} />
            : <LocalizedText source={"Refresh"} />}
        </Button>
      </div>

      <Grid stackable>
        {KPI_GROUPS.map((group) => (
          <Grid.Column key={group.key} width={8}>
            <MetricGroup
              group={group}
              metrics={metrics}
            />
          </Grid.Column>
        ))}
      </Grid>

      <Divider />

      <SlskrMetricsTable metrics={metrics} />
    </div>
  );
};

export default Metrics;
