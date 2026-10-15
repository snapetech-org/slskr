import LocalizedText from "../../Shared/LocalizedText";
import { interfaceText, interfaceTextProps, useInterfaceLanguage } from "../../../lib/interfaceLocale";
import { formatRegionalDateTime, formatBytes, formatRegionalFixedNumber, useRegionalFormat, formatRegionalNumber } from '../../../lib/util';
// <copyright file="index.jsx" company="slskr Team">
// Copyright (c) slskr Team. All rights reserved.
// </copyright>

import * as jobsLibrary from '../../../lib/jobs';
import { toDisplayError } from '../../../lib/errors';

import { useMountedRef } from '../../../lib/useMountedRef';
import { usePolling } from '../../../lib/usePolling';
import SwarmVisualization from '../SwarmVisualization';
import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { toast } from 'react-toastify';
import {
  Button,
  Card,
  Dropdown,
  Grid,
  Header,
  Icon,
  Label,
  Loader,
  Message,
  Modal,
  Pagination,
  Progress,
  Segment,
  Statistic,
  Table,
} from 'semantic-ui-react';

const normalizedJobStatus = (job) =>
  String(job.status ?? job.state ?? '')
    .toLowerCase()
    .replaceAll(/[^a-z]/gu, '');
const ACTIVE_JOB_STATES = new Set([
  'assembling',
  'downloading',
  'inprogress',
  'pending',
  'queued',
  'running',
  'verifying',
  'verifyingfinal',
]);

const Jobs = () => {
  useInterfaceLanguage();
  useRegionalFormat();
  const [jobs, setJobs] = useState([]);
  const [swarmJobs, setSwarmJobs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [jobsError, setJobsError] = useState('');
  const [swarmLoading, setSwarmLoading] = useState(true);
  const [swarmError, setSwarmError] = useState('');
  const [selectedSwarmJobId, setSelectedSwarmJobId] = useState(null);
  const [showVisualization, setShowVisualization] = useState(false);
  const [filters, setFilters] = useState({
    sortBy: 'created_at',
    sortOrder: 'desc',
    status: null,
    type: null,
  });
  const [pagination, setPagination] = useState({
    hasMore: false,
    limit: 20,
    offset: 0,
    total: 0,
  });
  const mountedRef = useMountedRef();
  const jobsRequestIdRef = React.useRef(0);
  const swarmRequestIdRef = React.useRef(0);
  const jobsInFlightRef = React.useRef(false);

  const fetchJobs = useCallback(async () => {
    if (!mountedRef.current || jobsInFlightRef.current) return;
    const requestId = ++jobsRequestIdRef.current;
    jobsInFlightRef.current = true;
    try {
      setLoading(true);
      const response = await jobsLibrary.getJobs({
        limit: pagination.limit,
        offset: pagination.offset,
        sortBy: filters.sortBy,
        sortOrder: filters.sortOrder,
        status: filters.status || undefined,
        type: filters.type || undefined,
      });
      if (
        !mountedRef.current ||
        jobsRequestIdRef.current !== requestId
      ) {
        return;
      }
      setJobs(
        Array.isArray(response?.jobs)
          ? response.jobs.filter((job) => job && typeof job === 'object')
          : [],
      );
      setJobsError('');
      setPagination((previous) => ({
        ...previous,
        hasMore: Boolean(response?.has_more),
        total: Number.isFinite(response?.total) ? response.total : 0,
      }));
    } catch (error) {
      if (
        mountedRef.current &&
        jobsRequestIdRef.current === requestId
      ) {
        const message = toDisplayError(error, 'Failed to fetch jobs');
        setJobsError(message);
        toast.error(message);
        console.error('Failed to fetch jobs:', error);
      }
    } finally {
      if (
        mountedRef.current &&
        jobsRequestIdRef.current === requestId
      ) {
        setLoading(false);
      }
      jobsInFlightRef.current = false;
    }
  }, [filters, mountedRef, pagination.limit, pagination.offset]);

  const fetchSwarmJobs = useCallback(async () => {
    if (!mountedRef.current) return;
    const requestId = ++swarmRequestIdRef.current;
    try {
      setSwarmLoading(true);
      const jobs = await jobsLibrary.getActiveSwarmJobs();
      if (
        mountedRef.current &&
        swarmRequestIdRef.current === requestId
      ) {
        setSwarmJobs(
          Array.isArray(jobs)
            ? jobs.filter((job) => job && typeof job === 'object')
            : [],
        );
        setSwarmError('');
      }
    } catch (error) {
      if (
        mountedRef.current &&
        swarmRequestIdRef.current === requestId
      ) {
        setSwarmError(toDisplayError(error, 'Failed to fetch swarm jobs'));
        console.error('Failed to fetch swarm jobs:', error);
      }
    } finally {
      if (
        mountedRef.current &&
        swarmRequestIdRef.current === requestId
      ) {
        setSwarmLoading(false);
      }
    }
  }, [mountedRef]);

  useEffect(() => {
    void fetchJobs();
  }, [fetchJobs]);

  usePolling(fetchSwarmJobs, 5_000);

  const analytics = useMemo(() => {
    const allJobs = [...jobs, ...swarmJobs];
    const byStatus = allJobs.reduce((accumulator, job) => {
      const status = normalizedJobStatus(job) || 'unknown';
      accumulator[status] = (accumulator[status] || 0) + 1;
      return accumulator;
    }, {});

    const byType = allJobs.reduce((accumulator, job) => {
      const type = job.type || 'unknown';
      accumulator[type] = (accumulator[type] || 0) + 1;
      return accumulator;
    }, {});

    const activeCount = allJobs.filter(
      (job) => ACTIVE_JOB_STATES.has(normalizedJobStatus(job)),
    ).length;

    const completedCount = allJobs.filter(
      (job) => normalizedJobStatus(job) === 'completed',
    ).length;

    return {
      active: activeCount,
      byStatus,
      byType,
      completed: completedCount,
      total: allJobs.length,
    };
  }, [jobs, swarmJobs]);

  const handleFilterChange = (key, value) => {
    setFilters((previous) => ({ ...previous, [key]: value }));
    setPagination((previous) => ({ ...previous, offset: 0 })); // Reset to first page
  };

  const handlePageChange = (_event, { activePage }) => {
    setPagination((previous) => ({
      ...previous,
      offset: (activePage - 1) * previous.limit,
    }));
  };

  const getStatusColor = (status) => {
    switch (status?.toLowerCase()) {
      case 'running':
        return 'blue';
      case 'pending':
        return 'yellow';
      case 'completed':
        return 'green';
      case 'failed':
        return 'red';
      default:
        return 'grey';
    }
  };

  const getStatusIcon = (status) => {
    switch (status?.toLowerCase()) {
      case 'running':
        return 'spinner';
      case 'pending':
        return 'clock';
      case 'completed':
        return 'check circle';
      case 'failed':
        return 'times circle';
      default:
        return 'question circle';
    }
  };

  const formatDate = (dateString) => {
    if (!dateString) return interfaceText('N/A');
    try {
      return formatRegionalDateTime(dateString);
    } catch {
      return dateString;
    }
  };

  const totalPages = Math.ceil(pagination.total / pagination.limit);

  return (
    <div>
      {/* Analytics Overview */}
      <Segment>
        <Header as="h3">
          <Icon name="chart bar" />
          <Header.Content><LocalizedText source={"Job Analytics"} /></Header.Content>
        </Header>
        <Grid columns={4}>
          <Grid.Column>
            <Statistic>
              <Statistic.Value>{formatRegionalNumber(analytics.total)}</Statistic.Value>
              <Statistic.Label><LocalizedText source={"Total Jobs"} /></Statistic.Label>
            </Statistic>
          </Grid.Column>
          <Grid.Column>
            <Statistic>
              <Statistic.Value>
                <Icon
                  color="blue"
                  name="spinner"
                />
                {formatRegionalNumber(analytics.active)}
              </Statistic.Value>
              <Statistic.Label><LocalizedText source={"Active"} /></Statistic.Label>
            </Statistic>
          </Grid.Column>
          <Grid.Column>
            <Statistic>
              <Statistic.Value>
                <Icon
                  color="green"
                  name="check circle"
                />
                {formatRegionalNumber(analytics.completed)}
              </Statistic.Value>
              <Statistic.Label><LocalizedText source={"Completed"} /></Statistic.Label>
            </Statistic>
          </Grid.Column>
          <Grid.Column>
            <Statistic>
              <Statistic.Value>
                {Object.keys(analytics.byType).length}
              </Statistic.Value>
              <Statistic.Label><LocalizedText source={"Job Types"} /></Statistic.Label>
            </Statistic>
          </Grid.Column>
        </Grid>
      </Segment>

      {swarmError && (
        <Message negative>
          <Message.Header><LocalizedText source={"Active swarm jobs unavailable"} /></Message.Header>
          <p>{swarmError}</p>
        </Message>
      )}
      {jobsError && (
        <Message
          data-testid="jobs-load-error"
          error
        >
          <Message.Header><LocalizedText source={"Jobs unavailable"} /></Message.Header>
          <p>{jobsError}</p>
          <p><LocalizedText source={"Previously loaded jobs remain visible until the next successful refresh."} /></p>
        </Message>
      )}

      {/* Active Swarm Jobs */}
      {swarmJobs.length > 0 && (
        <Segment>
          <Header as="h3">
            <Icon name="bolt" />
            <Header.Content>
              <LocalizedText source={"Active Swarm Downloads"} /><Header.Subheader>
                <LocalizedText source={"Multi-source downloads in progress"} /></Header.Subheader>
            </Header.Content>
          </Header>
          {swarmLoading && (
            <Loader
              active
              inline="centered"
            />
          )}
          <Grid columns={2}>
            {swarmJobs.map((job) => (
              <Grid.Column key={job.jobId}>
                <Card fluid>
                  <Card.Content>
                    <Card.Header>
                      <Icon
                        color="yellow"
                        name="bolt"
                      />
                      {job.filename?.split('/').pop() ?? 'Unknown file'}
                    </Card.Header>
                    <Card.Meta>
                      {job.activeSources ?? 0} <LocalizedText source={"sources •"} />{' '}
                      {formatBytes(job.downloadedBytes ?? 0)} /{' '}
                      {formatBytes(job.totalBytes ?? 0)}
                    </Card.Meta>
                    <Progress
                      active
                      color="blue"
                      percent={job.progressPercent ?? 0}
                      progress
                      size="small"
                    />
                    {job.chunksPerSecond && (
                      <Label size="tiny">
                        <Icon name="tachometer alternate" />
                        {formatRegionalFixedNumber(job.chunksPerSecond, 1)} chunks/s
                      </Label>
                    )}
                    {job.estimatedSecondsRemaining && (
                      <Label size="tiny">
                        <Icon name="clock" />
                        {Math.round(job.estimatedSecondsRemaining)}<LocalizedText source={"s remaining"} /></Label>
                    )}
                    <div style={{ marginTop: '0.5em' }}>
                      <Button
                        compact
                        icon
                        onClick={() => {
                          setSelectedSwarmJobId(job.jobId);
                          setShowVisualization(true);
                        }}
                        size="small"
                      >
                        <Icon name="chart bar" />
                        <LocalizedText source={"View Details"} /></Button>
                    </div>
                  </Card.Content>
                </Card>
              </Grid.Column>
            ))}
          </Grid>
        </Segment>
      )}

      {/* Swarm Visualization Modal */}
      <Modal
        closeIcon
        onClose={() => {
          setShowVisualization(false);
          setSelectedSwarmJobId(null);
        }}
        open={showVisualization}
        size="large"
      >
        <Modal.Header>
          <Icon name="chart bar" />
          <LocalizedText source={"Swarm Download Visualization"} /></Modal.Header>
        <Modal.Content scrolling>
          {selectedSwarmJobId && (
            <SwarmVisualization jobId={selectedSwarmJobId} />
          )}
        </Modal.Content>
      </Modal>

      {/* Job List */}
      <Segment>
        <Header as="h3">
          <Icon name="tasks" />
          <Header.Content><LocalizedText source={"All Jobs"} /></Header.Content>
        </Header>

        {/* Filters */}
        <div style={{ display: 'flex', gap: '1em', marginBottom: '1em' }}>
          <Dropdown
            clearable
            onChange={(_e, { value }) => handleFilterChange('type', value)}
            options={[
              { key: 'discography', text: interfaceText("Discography"), value: 'discography' },
              {
                key: 'label_crate',
                text: interfaceText("Label Crate"),
                value: 'label_crate',
              },
            ]}
            placeholder={interfaceText("Filter by Type")}
            selection
            value={filters.type}
           {...interfaceTextProps("Filter by Type")}/>
          <Dropdown
            clearable
            onChange={(_e, { value }) => handleFilterChange('status', value)}
            options={[
              { key: 'pending', text: interfaceText("Pending"), value: 'pending' },
              { key: 'running', text: interfaceText("Running"), value: 'running' },
              { key: 'completed', text: interfaceText("Completed"), value: 'completed' },
              { key: 'failed', text: interfaceText("Failed"), value: 'failed' },
            ]}
            placeholder={interfaceText("Filter by Status")}
            selection
            value={filters.status}
           {...interfaceTextProps("Filter by Status")}/>
          <Dropdown
            onChange={(_e, { value }) => handleFilterChange('sortBy', value)}
            options={[
              { key: 'created_at', text: interfaceText("Created Date"), value: 'created_at' },
              { key: 'status', text: interfaceText("Status"), value: 'status' },
              { key: 'id', text: interfaceText("ID"), value: 'id' },
            ]}
            placeholder={interfaceText("Sort By")}
            selection
            value={filters.sortBy}
           {...interfaceTextProps("Sort By")}/>
          <Button
            icon
            onClick={() =>
              handleFilterChange(
                'sortOrder',
                filters.sortOrder === 'asc' ? 'desc' : 'asc',
              )
            }
            toggle
          >
            <Icon
              name={filters.sortOrder === 'asc' ? 'sort up' : 'sort down'}
            />
            {filters.sortOrder === 'asc' ? <LocalizedText source={"Ascending"} /> : <LocalizedText source={"Descending"} />}
          </Button>
          <Button
            disabled={loading}
            icon
            onClick={fetchJobs}
          >
            <Icon name="refresh" />
            <LocalizedText source={"Refresh"} /></Button>
        </div>

        {loading ? (
          <Loader
            active
            inline="centered"
          />
        ) : jobs.length === 0 ? (
          jobsError ? null : (
            <Segment placeholder>
              <Header icon>
                <Icon name="inbox" />
                <LocalizedText source={"No jobs found"} /></Header>
              <p><LocalizedText source={"No jobs match the current filters."} /></p>
            </Segment>
          )
        ) : (
          <>
            <Table celled>
              <Table.Header>
                <Table.Row>
                  <Table.HeaderCell>ID</Table.HeaderCell>
                  <Table.HeaderCell><LocalizedText source={"Type"} /></Table.HeaderCell>
                  <Table.HeaderCell><LocalizedText source={"Status"} /></Table.HeaderCell>
                  <Table.HeaderCell><LocalizedText source={"Progress"} /></Table.HeaderCell>
                  <Table.HeaderCell><LocalizedText source={"Created"} /></Table.HeaderCell>
                </Table.Row>
              </Table.Header>
              <Table.Body>
                {jobs.map((job) => (
                  <Table.Row key={job.id}>
                    <Table.Cell>
                      <code>{job.id}</code>
                    </Table.Cell>
                    <Table.Cell>
                      <Label>{job.type || 'unknown'}</Label>
                    </Table.Cell>
                    <Table.Cell>
                      <Label color={getStatusColor(job.status)}>
                        <Icon name={getStatusIcon(job.status)} />
                        {job.status || 'unknown'}
                      </Label>
                    </Table.Cell>
                    <Table.Cell>
                      {job.progress ? (
                        <div>
                          <Progress
                            color={getStatusColor(job.status)}
                            percent={
                              job.progress.releases_total > 0
                                ? (job.progress.releases_done /
                                    job.progress.releases_total) *
                                  100
                                : 0
                            }
                            progress
                            size="small"
                          />
                          <div
                            style={{ fontSize: '0.9em', marginTop: '0.25em' }}
                          >
                            {job.progress.releases_done || 0} /{' '}
                            {job.progress.releases_total || 0} <LocalizedText source={"releases"} />{job.progress.releases_failed > 0 && (
                              <Label
                                color="red"
                                size="tiny"
                              >
                                {formatRegionalNumber(job.progress.releases_failed)} <LocalizedText source={"failed"} /></Label>
                            )}
                          </div>
                        </div>
                      ) : (
                        interfaceText('N/A')
                      )}
                    </Table.Cell>
                    <Table.Cell>{formatDate(job.created_at)}</Table.Cell>
                  </Table.Row>
                ))}
              </Table.Body>
            </Table>

            {totalPages > 1 && (
              <Pagination
                activePage={
                  Math.floor(pagination.offset / pagination.limit) + 1
                }
                onPageChange={handlePageChange}
                totalPages={totalPages}
              />
            )}
          </>
        )}
      </Segment>
    </div>
  );
};

export default Jobs;
