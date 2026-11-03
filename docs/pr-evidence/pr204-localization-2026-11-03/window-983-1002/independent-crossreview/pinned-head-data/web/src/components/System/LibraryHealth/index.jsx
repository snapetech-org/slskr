import LocalizedText, { LocalizedPluralText } from "../../Shared/LocalizedText";
import { interfaceText, interfaceTextProps, useInterfaceLanguage } from "../../../lib/interfaceLocale";
import * as libraryHealth from '../../../lib/libraryHealth';
import { copyToClipboard } from '../../../lib/clipboard';
import { toDisplayError } from '../../../lib/errors';
import {
  buildLibraryHealthActionPlan,
  buildLibraryHealthQuarantinePacket,
  buildLibraryHealthReport,
  buildLibraryHealthSafeFixManifest,
  buildLibraryHealthSearchSeeds,
  getLibraryHealthReplacementSearchQueries,
  getLibraryHealthSafeFixIssueIds,
} from '../../../lib/libraryHealthReport';
import { LoaderSegment } from '../../Shared';
import { formatRegionalNumber, useRegionalFormat } from '../../../lib/util';
import * as searches from '../../../lib/searches';
import { usePolling } from '../../../lib/usePolling';
import React, { useEffect, useRef, useState } from 'react';
import {
  Button,
  Grid,
  Header,
  Icon,
  Input,
  Label,
  Loader,
  Message,
  Popup,
  Segment,
  Statistic,
  Tab,
  Table,
} from 'semantic-ui-react';

const LibraryHealth = () => {
  useInterfaceLanguage();
  useRegionalFormat();
  const [activeIndex, setActiveIndex] = useState(0);
  const [libraryPath, setLibraryPath] = useState('');
  const [scanning, setScanning] = useState(false);
  const [summary, setSummary] = useState(null);
  const [issuesByType, setIssuesByType] = useState([]);
  const [issuesByArtist, setIssuesByArtist] = useState([]);
  const [issues, setIssues] = useState([]);
  const [selectedIssues, setSelectedIssues] = useState(new Set());
  const [fixing, setFixing] = useState(false);
  const [searchingReplacements, setSearchingReplacements] = useState(false);
  const [reportMessage, setReportMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [scanId, setScanId] = useState(null);
  const scanStartedAtRef = useRef(null);
  const mountedRef = useRef(false);
  const summaryRequestIdRef = useRef(0);
  const scanRequestIdRef = useRef(0);
  const mutationRequestIdRef = useRef(0);
  const replacementRequestIdRef = useRef(0);
  const reloadTimeoutRef = useRef(null);

  useEffect(() => {
    mountedRef.current = true;

    return () => {
      mountedRef.current = false;
      summaryRequestIdRef.current += 1;
      scanRequestIdRef.current += 1;
      mutationRequestIdRef.current += 1;
      replacementRequestIdRef.current += 1;
      if (reloadTimeoutRef.current !== null) {
        clearTimeout(reloadTimeoutRef.current);
        reloadTimeoutRef.current = null;
      }
    };
  }, []);

  const loadSummary = async (path) => {
    if (!path || !mountedRef.current) return;
    const requestId = ++summaryRequestIdRef.current;

    try {
      setLoading(true);
      setError(null);
      const [summaryResp, byTypeResp, byArtistResp, issuesResp] =
        await Promise.all([
          libraryHealth.getSummary(path),
          libraryHealth.getIssuesByType(path),
          libraryHealth.getIssuesByArtist(10),
          libraryHealth.getIssues({ libraryPath: path, limit: 100 }),
        ]);
      if (!mountedRef.current || summaryRequestIdRef.current !== requestId) return;
      const summaryData = summaryResp?.data;
      const byTypeData = byTypeResp?.data;
      const byArtistData = byArtistResp?.data;
      const issuesData = issuesResp?.data;
      setSummary(
        summaryData &&
          typeof summaryData === 'object' &&
          !Array.isArray(summaryData)
          ? summaryData
          : null,
      );
      setIssuesByType(Array.isArray(byTypeData?.groups) ? byTypeData.groups : []);
      setIssuesByArtist(
        Array.isArray(byArtistData?.groups) ? byArtistData.groups : [],
      );
      setIssues(
        Array.isArray(issuesData?.issues)
          ? issuesData.issues.filter(
              (issue) =>
                issue && typeof issue === 'object' && !Array.isArray(issue),
            )
          : [],
      );
      setReportMessage('');
    } catch (error_) {
      if (!mountedRef.current || summaryRequestIdRef.current !== requestId) return;
      setError(
        toDisplayError(error_, 'Failed to load library health data'),
      );
    } finally {
      if (mountedRef.current && summaryRequestIdRef.current === requestId) {
        setLoading(false);
      }
    }
  };

  const scheduleSummaryReload = (path) => {
    if (reloadTimeoutRef.current !== null) {
      clearTimeout(reloadTimeoutRef.current);
    }
    reloadTimeoutRef.current = setTimeout(() => {
      reloadTimeoutRef.current = null;
      void loadSummary(path);
    }, 1_000);
  };

  usePolling(
    async () => {
      if (!scanId || !mountedRef.current) return;

      if (
        scanStartedAtRef.current &&
        Date.now() - scanStartedAtRef.current >= 60_000
      ) {
        if (!mountedRef.current) return;
        setScanId(null);
        scanStartedAtRef.current = null;
        setScanning(false);
        await loadSummary(libraryPath);
        return;
      }

      try {
        const statusResp = await libraryHealth.getScanStatus(scanId);
        if (
          statusResp?.data?.status === 'Completed' ||
          statusResp?.data?.status === 'Failed'
        ) {
          if (!mountedRef.current) return;
          setScanId(null);
          scanStartedAtRef.current = null;
          setScanning(false);
          await loadSummary(libraryPath);
        }
      } catch (error_) {
        if (!mountedRef.current) return;
        setError(
          toDisplayError(
            error_,
            'Failed to check library health scan status',
          ),
        );
        setScanId(null);
        scanStartedAtRef.current = null;
        setScanning(false);
      }
    },
    2_000,
    { enabled: Boolean(scanId), resetKey: scanId },
  );

  const handleStartScan = async () => {
    if (!mountedRef.current || scanning) return;
    const path = libraryPath.trim();
    if (!path) {
      setError(interfaceText("Please enter a library path"));
      return;
    }

    const requestId = ++scanRequestIdRef.current;
    try {
      setScanning(true);
      setError(null);
      const response = await libraryHealth.startScan(path);
      const startedScanId = response?.data?.scanId;
      if (!startedScanId) {
        throw new Error('Scan start returned no scan ID');
      }
      if (
        !mountedRef.current ||
        requestId !== scanRequestIdRef.current
      ) {
        return;
      }
      scanStartedAtRef.current = Date.now();
      setScanId(startedScanId);
    } catch (error_) {
      if (
        mountedRef.current &&
        requestId === scanRequestIdRef.current
      ) {
        setError(toDisplayError(error_, 'Failed to start scan'));
        setScanId(null);
        scanStartedAtRef.current = null;
        setScanning(false);
      }
    }
  };

  const getSeverityColor = (severity) => {
    switch (severity) {
      case 'Critical':
        return 'red';
      case 'High':
        return 'orange';
      case 'Medium':
        return 'yellow';
      case 'Low':
        return 'blue';
      case 'Info':
        return 'grey';
      default:
        return 'grey';
    }
  };

  const getIssueTypeLabel = (type) => {
    switch (type) {
      case 'SuspectedTranscode':
        return 'Suspected Transcode';
      case 'NonCanonicalVariant':
        return 'Non-Canonical Variant';
      case 'TrackNotInTaggedRelease':
        return 'Track Not in Tagged Release';
      case 'MissingTrackInRelease':
        return 'Missing Track in Release';
      case 'CorruptedFile':
        return 'Corrupted File';
      case 'MissingMetadata':
        return 'Missing Metadata';
      case 'MultipleVariants':
        return 'Multiple Variants';
      case 'WrongDuration':
        return 'Wrong Duration';
      default:
        return type;
    }
  };

  const handleToggleIssue = (issueId) => {
    const newSelected = new Set(selectedIssues);
    if (newSelected.has(issueId)) {
      newSelected.delete(issueId);
    } else {
      newSelected.add(issueId);
    }

    setSelectedIssues(newSelected);
  };

  const handleToggleAll = () => {
    if (selectedIssues.size === issues.length) {
      setSelectedIssues(new Set());
    } else {
      setSelectedIssues(new Set(issues.map((index) => index.issueId)));
    }
  };

  const handleFixSelected = async () => {
    if (!mountedRef.current || fixing) return;
    if (selectedIssues.size === 0) {
      setError(interfaceText("Please select issues to fix"));
      return;
    }

    const selectedIssueList = issues.filter((issue) =>
      selectedIssues.has(issue.issueId));
    const issueIds = getLibraryHealthSafeFixIssueIds(selectedIssueList);
    if (issueIds.length === 0) {
      setError(interfaceText("Select at least one auto-fixable issue."));
      return;
    }

    const requestId = ++mutationRequestIdRef.current;
    try {
      setFixing(true);
      setError(null);
      await libraryHealth.createRemediationJob(issueIds);
      if (
        !mountedRef.current ||
        requestId !== mutationRequestIdRef.current
      ) {
        return;
      }
      setSelectedIssues(new Set());
      setReportMessage(interfaceText('Remediation job queued for auto-fixable issues: {count}.', { count: issueIds.length }));
      // Reload issues after a delay
      scheduleSummaryReload(libraryPath);
    } catch (error_) {
      if (!mountedRef.current) return;
      if (
        mountedRef.current &&
        requestId === mutationRequestIdRef.current
      ) {
        setError(toDisplayError(error_, 'Failed to create fix job'));
      }
    } finally {
      if (
        mountedRef.current &&
        requestId === mutationRequestIdRef.current
      ) {
        setFixing(false);
      }
    }
  };

  const handleFixSingle = async (issueId) => {
    if (!mountedRef.current || fixing) return;
    const requestId = ++mutationRequestIdRef.current;
    try {
      setFixing(true);
      setError(null);
      await libraryHealth.createRemediationJob([issueId]);
      if (
        !mountedRef.current ||
        requestId !== mutationRequestIdRef.current
      ) {
        return;
      }
      setReportMessage(interfaceText('Remediation job queued for auto-fixable issues: {count}.', { count: 1 }));
      scheduleSummaryReload(libraryPath);
    } catch (error_) {
      if (!mountedRef.current) return;
      if (
        mountedRef.current &&
        requestId === mutationRequestIdRef.current
      ) {
        setError(toDisplayError(error_, 'Failed to create fix job'));
      }
    } finally {
      if (
        mountedRef.current &&
        requestId === mutationRequestIdRef.current
      ) {
        setFixing(false);
      }
    }
  };

  const handleCopyReport = async () => {
    const report = buildLibraryHealthReport({
      issues,
      issuesByArtist,
      issuesByType,
      libraryPath,
      summary,
    });

    try {
      const copied = await copyToClipboard(report);
      if (!mountedRef.current) return;
      setReportMessage(
        copied
          ? `Library health report copied for ${issues.length} loaded issues.`
          : `Library health report prepared for ${issues.length} loaded issues; clipboard is unavailable.`,
      );
    } catch (error_) {
      if (mountedRef.current) {
        setReportMessage(toDisplayError(error_, 'Unable to copy library health report.'));
      }
    }
  };

  const handleCopyActionPlan = async () => {
    const selectedIssueList = issues.filter((issue) =>
      selectedIssues.has(issue.issueId));
    const plan = buildLibraryHealthActionPlan({
      issues: selectedIssueList,
      libraryPath,
    });

    try {
      const copied = await copyToClipboard(plan);
      if (!mountedRef.current) return;
      setReportMessage(
        copied
          ? `Library health action plan copied for ${selectedIssueList.length} selected issues.`
          : `Library health action plan prepared for ${selectedIssueList.length} selected issues; clipboard is unavailable.`,
      );
    } catch (error_) {
      if (mountedRef.current) {
        setReportMessage(toDisplayError(error_, 'Unable to copy library health action plan.'));
      }
    }
  };

  const handleCopySafeFixManifest = async () => {
    const selectedIssueList = issues.filter((issue) =>
      selectedIssues.has(issue.issueId));
    const manifest = buildLibraryHealthSafeFixManifest({
      issues: selectedIssueList,
      libraryPath,
    });

    try {
      const copied = await copyToClipboard(manifest);
      if (!mountedRef.current) return;
      setReportMessage(
        copied
          ? `Library health safe-fix manifest copied for ${selectedIssueList.length} selected issues.`
          : `Library health safe-fix manifest prepared for ${selectedIssueList.length} selected issues; clipboard is unavailable.`,
      );
    } catch (error_) {
      if (mountedRef.current) {
        setReportMessage(toDisplayError(error_, 'Unable to copy library health safe-fix manifest.'));
      }
    }
  };

  const handleCopySearchSeeds = async () => {
    const selectedIssueList = issues.filter((issue) =>
      selectedIssues.has(issue.issueId));
    const seeds = buildLibraryHealthSearchSeeds({
      issues: selectedIssueList,
      libraryPath,
    });

    try {
      const copied = await copyToClipboard(seeds);
      if (!mountedRef.current) return;
      setReportMessage(
        copied
          ? `Library health replacement search seeds copied for ${selectedIssueList.length} selected issues.`
          : `Library health replacement search seeds prepared for ${selectedIssueList.length} selected issues; clipboard is unavailable.`,
      );
    } catch (error_) {
      if (mountedRef.current) {
        setReportMessage(toDisplayError(error_, 'Unable to copy library health replacement search seeds.'));
      }
    }
  };

  const handleCopyQuarantinePacket = async () => {
    const selectedIssueList = issues.filter((issue) =>
      selectedIssues.has(issue.issueId));
    const packet = buildLibraryHealthQuarantinePacket({
      issues: selectedIssueList,
      libraryPath,
    });

    try {
      const copied = await copyToClipboard(packet);
      if (!mountedRef.current) return;
      setReportMessage(
        copied
          ? `Library health quarantine review packet copied for ${selectedIssueList.length} selected issues.`
          : `Library health quarantine review packet prepared for ${selectedIssueList.length} selected issues; clipboard is unavailable.`,
      );
    } catch (error_) {
      if (mountedRef.current) {
        setReportMessage(toDisplayError(error_, 'Unable to copy library health quarantine review packet.'));
      }
    }
  };

  const handleRunReplacementSearches = async () => {
    if (!mountedRef.current || searchingReplacements) return;
    const selectedIssueList = issues.filter((issue) =>
      selectedIssues.has(issue.issueId));
    const queries = getLibraryHealthReplacementSearchQueries(selectedIssueList, {
      limit: 3,
    });

    if (queries.length === 0) {
      setError(interfaceText("Selected issues do not have replacement search candidates."));
      return;
    }

    const requestId = ++replacementRequestIdRef.current;
    try {
      setSearchingReplacements(true);
      setError(null);
      const count = await searches.createBatch({ queries });
      if (
        !mountedRef.current ||
        requestId !== replacementRequestIdRef.current
      ) {
        return;
      }
      const startedCount = Number.isFinite(count) ? count : queries.length;
      setReportMessage(interfaceText('Bounded replacement searches started for selected Library Health issues: {count}.', { count: startedCount }));
    } catch (error_) {
      if (
        mountedRef.current &&
        requestId === replacementRequestIdRef.current
      ) {
        setError(toDisplayError(error_, 'Failed to start replacement searches'));
      }
    } finally {
      if (
        mountedRef.current &&
        requestId === replacementRequestIdRef.current
      ) {
        setSearchingReplacements(false);
      }
    }
  };

  const OverviewPane = () => (
    <Tab.Pane>
      <Grid>
        <Grid.Row>
          <Grid.Column width={16}>
            <Segment>
              <Header as="h3">
                <Icon name="heartbeat" />
                <Header.Content>
                  <LocalizedText source={"Library Health Scanner"} /><Header.Subheader>
                    <LocalizedText source={"Detect quality issues, transcodes, and missing tracks"} /></Header.Subheader>
                </Header.Content>
              </Header>
            </Segment>
          </Grid.Column>
        </Grid.Row>

        <Grid.Row>
          <Grid.Column width={16}>
            <Segment>
              <Input
                action={
                  <Button
                    disabled={scanning || !libraryPath}
                    loading={scanning}
                    onClick={handleStartScan}
                    primary
                  >
                    <Icon name="search" />
                    {scanning ? <LocalizedText source="Scanning..." /> : <LocalizedText source={"Start Scan"} />}
                  </Button>
                }
                disabled={scanning}
                fluid
                onChange={(e) => setLibraryPath(e.target.value)}
                placeholder={interfaceText("Enter library path (e.g., /music or C:\\Music)")}
                value={libraryPath}
               {...interfaceTextProps("Enter library path (e.g., /music or C:\\Music)")}/>
            </Segment>
          </Grid.Column>
        </Grid.Row>

        {error && (
          <Grid.Row>
            <Grid.Column width={16}>
              <Message negative>
                <Icon name="warning circle" />
                {error}
              </Message>
            </Grid.Column>
          </Grid.Row>
        )}

        {loading ? (
          <Grid.Row>
            <Grid.Column width={16}>
              <LoaderSegment><LocalizedText source={"Loading library health data..."} /></LoaderSegment>
            </Grid.Column>
          </Grid.Row>
        ) : summary ? (
          <>
            <Grid.Row>
              <Grid.Column width={16}>
                <Segment>
                  <Statistic.Group widths="three">
                    <Statistic>
                      <Statistic.Value>{summary.totalIssues}</Statistic.Value>
                      <Statistic.Label><LocalizedText source={"Total Issues"} /></Statistic.Label>
                    </Statistic>
                    <Statistic color="red">
                      <Statistic.Value>{summary.issuesOpen}</Statistic.Value>
                      <Statistic.Label><LocalizedText source={"Open"} /></Statistic.Label>
                    </Statistic>
                    <Statistic color="green">
                      <Statistic.Value>
                        {formatRegionalNumber(summary.issuesResolved)}
                      </Statistic.Value>
                      <Statistic.Label><LocalizedText source={"Resolved"} /></Statistic.Label>
                    </Statistic>
                  </Statistic.Group>
                  <Popup
                    content={interfaceText("Copy a read-only health report for offline review. This does not fix, rescan, quarantine, search, or mutate files.")}
                    trigger={
                      <Button
                        data-testid="library-health-copy-report"
                        disabled={!summary}
                        onClick={handleCopyReport}
                        type="button"
                      >
                        <Icon name="copy" />
                        <LocalizedText source={"Copy Report"} /></Button>
                    }
                   {...interfaceTextProps("Copy a read-only health report for offline review. This does not fix, rescan, quarantine, search, or mutate files.")}/>
                  {reportMessage ? (
                    <Message
                      compact
                      data-testid="library-health-report-message"
                      size="mini"
                    >
                      {reportMessage}
                    </Message>
                  ) : null}
                </Segment>
              </Grid.Column>
            </Grid.Row>

            <Grid.Row>
              <Grid.Column width={8}>
                <Segment>
                  <Header as="h4"><LocalizedText source={"Issues by Type"} /></Header>
                  <Table compact>
                    <Table.Header>
                      <Table.Row>
                        <Table.HeaderCell><LocalizedText source={"Type"} /></Table.HeaderCell>
                        <Table.HeaderCell textAlign="right">
                          <LocalizedText source={"Count"} /></Table.HeaderCell>
                      </Table.Row>
                    </Table.Header>
                    <Table.Body>
                      {issuesByType.length === 0 ? (
                        <Table.Row>
                          <Table.Cell
                            colSpan={2}
                            textAlign="center"
                          >
                            <LocalizedText source={"No issues detected"} /></Table.Cell>
                        </Table.Row>
                      ) : (
                        issuesByType.map((group) => (
                          <Table.Row key={group.type}>
                            <Table.Cell>
                              <Label basic>
                                <LocalizedText source={getIssueTypeLabel(group.type)} />
                              </Label>
                            </Table.Cell>
                            <Table.Cell textAlign="right">
                              <strong>{formatRegionalNumber(group.count)}</strong>
                            </Table.Cell>
                          </Table.Row>
                        ))
                      )}
                    </Table.Body>
                  </Table>
                </Segment>
              </Grid.Column>

              <Grid.Column width={8}>
                <Segment>
                  <Header as="h4"><LocalizedText source={"Top Artists with Issues"} /></Header>
                  <Table compact>
                    <Table.Header>
                      <Table.Row>
                        <Table.HeaderCell><LocalizedText source={"Artist"} /></Table.HeaderCell>
                        <Table.HeaderCell textAlign="right">
                          <LocalizedText source={"Issues"} /></Table.HeaderCell>
                      </Table.Row>
                    </Table.Header>
                    <Table.Body>
                      {issuesByArtist.length === 0 ? (
                        <Table.Row>
                          <Table.Cell
                            colSpan={2}
                            textAlign="center"
                          >
                            <LocalizedText source={"No artist data available"} /></Table.Cell>
                        </Table.Row>
                      ) : (
                        issuesByArtist.map((group, index) => (
                          <Table.Row key={index}>
                            <Table.Cell>{group.artist}</Table.Cell>
                            <Table.Cell textAlign="right">
                              <strong>{formatRegionalNumber(group.count)}</strong>
                            </Table.Cell>
                          </Table.Row>
                        ))
                      )}
                    </Table.Body>
                  </Table>
                </Segment>
              </Grid.Column>
            </Grid.Row>
          </>
        ) : (
          <Grid.Row>
            <Grid.Column width={16}>
              <Segment placeholder>
                <Header icon>
                  <Icon name="search" />
                  <LocalizedText source={"Enter a library path and start a scan to detect issues"} /></Header>
              </Segment>
            </Grid.Column>
          </Grid.Row>
        )}
      </Grid>
    </Tab.Pane>
  );

  const IssuesPane = () => (
    <Tab.Pane>
      <Grid>
        <Grid.Row>
          <Grid.Column width={16}>
            {error && (
              <Message negative>
                <Icon name="warning circle" />
                {error}
              </Message>
            )}

            {selectedIssues.size > 0 && (
              <Segment>
                <Button
                  disabled={fixing}
                  loading={fixing}
                  onClick={handleFixSelected}
                  primary
                >
                  <Icon name="wrench" />
                  <LocalizedText source={"Fix"} />{" "}
                  <LocalizedPluralText
                    count={selectedIssues.size}
                    other="{count} Selected Issues"
                    singular="{count} Selected Issue"
                    values={{ count: formatRegionalNumber(selectedIssues.size) }}
                  />
                </Button>
                <Popup
                  content={interfaceText("Start bounded live Soulseek replacement searches for selected replacement candidates. This starts searches only; it does not browse peers, download, quarantine, or mutate files.")}
                  trigger={
                    <Button
                      data-testid="library-health-run-replacement-searches"
                      disabled={fixing || searchingReplacements}
                      loading={searchingReplacements}
                      onClick={handleRunReplacementSearches}
                      type="button"
                    >
                      <Icon name="search" />
                      <LocalizedText source={"Start Replacement Searches"} /></Button>
                  }
                 {...interfaceTextProps("Start bounded live Soulseek replacement searches for selected replacement candidates. This starts searches only; it does not browse peers, download, quarantine, or mutate files.")}/>
                <Button
                  basic
                  disabled={fixing}
                  onClick={() => setSelectedIssues(new Set())}
                >
                  <LocalizedText source={"Clear Selection"} /></Button>
                <Popup
                  content={interfaceText("Copy a selected-issue action plan for review. This does not create remediation jobs, queue searches, quarantine files, or mutate files.")}
                  trigger={
                    <Button
                      basic
                      data-testid="library-health-copy-action-plan"
                      disabled={fixing}
                      onClick={handleCopyActionPlan}
                      type="button"
                    >
                      <Icon name="copy" />
                      <LocalizedText source={"Copy Action Plan"} /></Button>
                  }
                 {...interfaceTextProps("Copy a selected-issue action plan for review. This does not create remediation jobs, queue searches, quarantine files, or mutate files.")}/>
                <Popup
                  content={interfaceText("Copy an auto-fixable issue manifest for review. This does not create a remediation job, execute safe fixes, or mutate files.")}
                  trigger={
                    <Button
                      basic
                      data-testid="library-health-copy-safe-fix-manifest"
                      disabled={fixing}
                      onClick={handleCopySafeFixManifest}
                      type="button"
                    >
                      <Icon name="check circle" />
                      <LocalizedText source={"Copy Safe-Fix Manifest"} /></Button>
                  }
                 {...interfaceTextProps("Copy an auto-fixable issue manifest for review. This does not create a remediation job, execute safe fixes, or mutate files.")}/>
                <Popup
                  content={interfaceText("Copy replacement search seed queries for selected issues. This does not open Search, contact peers, download files, or mutate files.")}
                  trigger={
                    <Button
                      basic
                      data-testid="library-health-copy-search-seeds"
                      disabled={fixing}
                      onClick={handleCopySearchSeeds}
                      type="button"
                    >
                      <Icon name="search" />
                      <LocalizedText source={"Copy Search Seeds"} /></Button>
                  }
                 {...interfaceTextProps("Copy replacement search seed queries for selected issues. This does not open Search, contact peers, download files, or mutate files.")}/>
                <Popup
                  content={interfaceText("Copy a manual quarantine review packet for selected risky issues. This does not change quarantine state, move files, send peer messages, or mutate files.")}
                  trigger={
                    <Button
                      basic
                      data-testid="library-health-copy-quarantine-packet"
                      disabled={fixing}
                      onClick={handleCopyQuarantinePacket}
                      type="button"
                    >
                      <Icon name="shield" />
                      <LocalizedText source={"Copy Quarantine Packet"} /></Button>
                  }
                 {...interfaceTextProps("Copy a manual quarantine review packet for selected risky issues. This does not change quarantine state, move files, send peer messages, or mutate files.")}/>
              </Segment>
            )}

            {loading ? (
              <LoaderSegment><LocalizedText source={"Loading issues..."} /></LoaderSegment>
            ) : issues.length === 0 ? (
              <Segment placeholder>
                <Header icon>
                  <Icon
                    color="green"
                    name="check circle"
                  />
                  <LocalizedText source={"No issues detected"} /></Header>
              </Segment>
            ) : (
              <Table
                celled
                selectable
              >
                <Table.Header>
                  <Table.Row>
                    <Table.HeaderCell collapsing>
                      <input
                        checked={
                          selectedIssues.size === issues.length &&
                          issues.length > 0
                        }
                        onChange={handleToggleAll}
                        type="checkbox"
                      />
                    </Table.HeaderCell>
                    <Table.HeaderCell><LocalizedText source={"Type"} /></Table.HeaderCell>
                    <Table.HeaderCell><LocalizedText source={"Severity"} /></Table.HeaderCell>
                    <Table.HeaderCell><LocalizedText source={"Artist"} /></Table.HeaderCell>
                    <Table.HeaderCell><LocalizedText source={"Track"} /></Table.HeaderCell>
                    <Table.HeaderCell><LocalizedText source={"Reason"} /></Table.HeaderCell>
                    <Table.HeaderCell><LocalizedText source={"Status"} /></Table.HeaderCell>
                    <Table.HeaderCell textAlign="center">
                      <LocalizedText source={"Actions"} /></Table.HeaderCell>
                  </Table.Row>
                </Table.Header>
                <Table.Body>
                  {issues.map((issue) => (
                    <Table.Row key={issue.issueId}>
                      <Table.Cell collapsing>
                        <input
                          checked={selectedIssues.has(issue.issueId)}
                          disabled={!issue.canAutoFix}
                          onChange={() => handleToggleIssue(issue.issueId)}
                          type="checkbox"
                        />
                      </Table.Cell>
                      <Table.Cell>
                        <Label
                          basic
                          size="small"
                        >
                          <LocalizedText source={getIssueTypeLabel(issue.type)} />
                        </Label>
                      </Table.Cell>
                      <Table.Cell>
                        <Label
                          color={getSeverityColor(issue.severity)}
                          size="small"
                        >
                          <LocalizedText source={issue.severity} />
                        </Label>
                      </Table.Cell>
                      <Table.Cell>{issue.artist || '-'}</Table.Cell>
                      <Table.Cell>{issue.title || '-'}</Table.Cell>
                      <Table.Cell>
                        <span title={issue.reason}>
                          {issue.reason?.length > 50
                            ? issue.reason.slice(0, 50) + '...'
                            : issue.reason}
                        </span>
                      </Table.Cell>
                      <Table.Cell>
                        <Label
                          color={
                            issue.status === 'Resolved'
                              ? 'green'
                              : issue.status === 'Fixing'
                                ? 'blue'
                                : issue.status === 'Failed'
                                  ? 'red'
                                  : 'grey'
                          }
                          size="mini"
                        >
                          <LocalizedText source={issue.status} />
                        </Label>
                      </Table.Cell>
                      <Table.Cell textAlign="center">
                        {issue.canAutoFix && issue.status === 'Detected' && (
                          <Popup
                            content={interfaceText("Queue a remediation job for this auto-fixable issue. The backend still applies its remediation safeguards.")}
                            trigger={
                              <Button
                                disabled={fixing}
                                onClick={() => handleFixSingle(issue.issueId)}
                                primary
                                size="tiny"
                              >
                                <Icon name="wrench" />
                                <LocalizedText source={"Fix"} /></Button>
                            }
                           {...interfaceTextProps("Queue a remediation job for this auto-fixable issue. The backend still applies its remediation safeguards.")}/>
                        )}
                        {issue.status === 'Fixing' && (
                          <Loader
                            active
                            inline
                            size="tiny"
                          />
                        )}
                      </Table.Cell>
                    </Table.Row>
                  ))}
                </Table.Body>
              </Table>
            )}
          </Grid.Column>
        </Grid.Row>
      </Grid>
    </Tab.Pane>
  );

  const panes = [
    {
      menuItem: {
        content: interfaceText("Overview"),
        icon: 'dashboard',
        key: 'overview',
      },
      render: () => <OverviewPane />,
    },
    {
      menuItem: {
        content: interfaceText("All Issues"),
        icon: 'warning',
        key: 'issues',
      },
      render: () => <IssuesPane />,
    },
  ];

  return (
    <div className="library-health">
      <Tab
        activeIndex={activeIndex}
        onTabChange={(_event, { activeIndex: nextIndex }) =>
          setActiveIndex(nextIndex)
        }
        panes={panes}
        renderActiveOnly={false}
      />
    </div>
  );
};

export default LibraryHealth;
