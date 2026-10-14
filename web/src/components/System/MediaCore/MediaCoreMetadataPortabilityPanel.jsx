import LocalizedText from "../../Shared/LocalizedText";
import { interfaceText, interfaceTextProps, useInterfaceLanguage } from "../../../lib/interfaceLocale";


import * as mediacore from '../../../lib/mediacore';
import { toDisplayError } from '../../../lib/errors';
import Button from './MediaCoreButton';
import React, { useEffect, useRef } from 'react';
import {
  Card,
  Checkbox,
  Dropdown,
  Form,
  Grid,
  Icon,
  List,
  Message,
  TextArea,
} from 'semantic-ui-react';

const useMountedState = (mountedRef, initialValue) => {
  const [value, setValue] = React.useState(initialValue);
  const setMountedValue = React.useCallback(
    (nextValue) => {
      if (mountedRef.current) {
        setValue(nextValue);
      }
    },
    [mountedRef],
  );

  return [value, setMountedValue];
};

const MediaCoreMetadataPortabilityPanel = React.memo(() => {
  useInterfaceLanguage();
  const mountedRef = useRef(true);

  useEffect(() => {
    mountedRef.current = true;
    return () => {
      mountedRef.current = false;
    };
  }, []);

  const [exportContentIds, setExportContentIds] = useMountedState(mountedRef, '');
  const [includeLinks, setIncludeLinks] = useMountedState(mountedRef, true);
  const [importPackage, setImportPackage] = useMountedState(mountedRef, '');
  const [conflictStrategy, setConflictStrategy] = useMountedState(mountedRef, 'Merge');
  const [dryRun, setDryRun] = useMountedState(mountedRef, false);
  const [exportResult, setExportResult] = useMountedState(mountedRef, null);
  const [importResult, setImportResult] = useMountedState(mountedRef, null);
  const [conflictAnalysis, setConflictAnalysis] = useMountedState(mountedRef, null);
  const [availableStrategies, setAvailableStrategies] = useMountedState(mountedRef, null);
  const [exportingMetadata, setExportingMetadata] = useMountedState(mountedRef, false);
  const [importingMetadata, setImportingMetadata] = useMountedState(mountedRef, false);
  const [analyzingConflicts, setAnalyzingConflicts] = useMountedState(mountedRef, false);

  useEffect(() => {
    const loadAvailableStrategies = async () => {
      try {
        const result = await mediacore.getConflictStrategies();
        setAvailableStrategies(result);
      } catch (error_) {
        console.error('Failed to load conflict strategies:', error_);
      }
    };

    loadAvailableStrategies();
  }, [setAvailableStrategies]);

  const handleExportMetadata = async () => {
    const contentIds = exportContentIds
      .split('\n')
      .map((id) => id.trim())
      .filter(Boolean);
    if (!contentIds.length) return;

    try {
      setExportingMetadata(true);
      setExportResult(null);
      const result = await mediacore.exportMetadata(contentIds, includeLinks);
      setExportResult(result);
    } catch (error_) {
      setExportResult({ error: toDisplayError(error_) });
    } finally {
      setExportingMetadata(false);
    }
  };

  const handleImportMetadata = async () => {
    if (!importPackage.trim()) return;

    try {
      setImportingMetadata(true);
      setImportResult(null);

      let packageData;
      try {
        packageData = JSON.parse(importPackage.trim());
      } catch {
        throw new Error('Invalid JSON format for metadata package');
      }

      const result = await mediacore.importMetadata(
        packageData,
        conflictStrategy,
        dryRun,
      );
      setImportResult(result);
    } catch (error_) {
      setImportResult({ error: toDisplayError(error_) });
    } finally {
      setImportingMetadata(false);
    }
  };

  const handleAnalyzeConflicts = async () => {
    if (!importPackage.trim()) return;

    try {
      setAnalyzingConflicts(true);
      setConflictAnalysis(null);

      let packageData;
      try {
        packageData = JSON.parse(importPackage.trim());
      } catch {
        throw new Error('Invalid JSON format for metadata package');
      }

      const result = await mediacore.analyzeMetadataConflicts(packageData);
      setConflictAnalysis(result);
    } catch (error_) {
      setConflictAnalysis({ error: toDisplayError(error_) });
    } finally {
      setAnalyzingConflicts(false);
    }
  };

  return (
    <>
        {/* Metadata Portability - Export */}
        <Grid.Column width={8}>
          <Card fluid>
            <Card.Content>
              <Card.Header>
                <Icon name="download" />
                <LocalizedText source={"Export Metadata"} /></Card.Header>
              <Card.Description>
                <LocalizedText source={"Export metadata for ContentIDs to a portable package"} /></Card.Description>
            </Card.Content>
            <Card.Content>
              <Form>
                <Form.Field>
                  <label><LocalizedText source={"ContentIDs (one per line)"} /></label>
                  <TextArea
                    onChange={(e) => setExportContentIds(e.target.value)}
                    placeholder={interfaceText("content:audio:track:mb-12345&#10;content:video:movie:imdb-tt0111161&#10;...")}
                    rows={4}
                    value={exportContentIds}
                   {...interfaceTextProps("content:audio:track:mb-12345&#10;content:video:movie:imdb-tt0111161&#10;...")}/>
                </Form.Field>
                <Form.Field>
                  <Checkbox
                    checked={includeLinks}
                    label={interfaceText("Include IPLD links")}
                    onChange={(e, { checked }) => setIncludeLinks(checked)}
                   {...interfaceTextProps("Include IPLD links")}/>
                </Form.Field>
                <Button
                  disabled={!exportContentIds.trim() || exportingMetadata}
                  loading={exportingMetadata}
                  onClick={handleExportMetadata}
                  primary
                >
                  <LocalizedText source={"Export Metadata"} /></Button>
              </Form>

              {exportResult && (
                <div style={{ marginTop: '1em' }}>
                  {exportResult.error ? (
                    <Message error>
                      <p>{exportResult.error}</p>
                    </Message>
                  ) : (
                    <Message success>
                      <Message.Header><LocalizedText source={"Export Successful"} /></Message.Header>
                      <p>
                        <strong><LocalizedText source={"Version:"} /></strong> {exportResult.version}
                        <br />
                        <strong><LocalizedText source={"Entries:"} /></strong>{' '}
                        {exportResult.metadata?.totalEntries || 0}
                        <br />
                        <strong><LocalizedText source={"Links:"} /></strong>{' '}
                        {exportResult.metadata?.totalLinks || 0}
                        <br />
                        <strong><LocalizedText source={"Checksum:"} /></strong>{' '}
                        {exportResult.metadata?.checksum?.slice(0, 16)}...
                      </p>
                      <details>
                        <summary><LocalizedText source={"View Package JSON"} /></summary>
                        <pre
                          style={{
                            fontSize: '0.8em',
                            maxHeight: '200px',
                            overflow: 'auto',
                          }}
                        >
                          {JSON.stringify(exportResult, null, 2)}
                        </pre>
                      </details>
                    </Message>
                  )}
                </div>
              )}
            </Card.Content>
          </Card>
        </Grid.Column>

        {/* Metadata Portability - Import */}
        <Grid.Column width={8}>
          <Card fluid>
            <Card.Content>
              <Card.Header>
                <Icon name="upload" />
                <LocalizedText source={"Import Metadata"} /></Card.Header>
              <Card.Description>
                <LocalizedText source={"Import metadata from a portable package with conflict resolution"} /></Card.Description>
            </Card.Content>
            <Card.Content>
              <Form>
                <Form.Field>
                  <label><LocalizedText source={"Conflict Resolution Strategy"} /></label>
                  <Dropdown
                    onChange={(e, { value }) => setConflictStrategy(value)}
                    options={
                      availableStrategies?.strategies?.map((s) => ({
                        description: s.description,
                        key: s.strategy,
                        text: s.name,
                        value: s.strategy,
                      })) || []
                    }
                    selection
                    value={conflictStrategy}
                  />
                </Form.Field>
                <Form.Field>
                  <Checkbox
                    checked={dryRun}
                    label={interfaceText("Dry run (preview changes without applying)")}
                    onChange={(e, { checked }) => setDryRun(checked)}
                   {...interfaceTextProps("Dry run (preview changes without applying)")}/>
                </Form.Field>
                <Button
                  disabled={!importPackage.trim() || analyzingConflicts}
                  loading={analyzingConflicts}
                  onClick={handleAnalyzeConflicts}
                  secondary
                >
                  <LocalizedText source={"Analyze Conflicts"} /></Button>
                <Button
                  disabled={!importPackage.trim() || importingMetadata}
                  loading={importingMetadata}
                  onClick={handleImportMetadata}
                  primary
                  style={{ marginLeft: '0.5em' }}
                >
                  <LocalizedText source={"Import Metadata"} /></Button>
              </Form>

              {/* Import Package Input */}
              <Form style={{ marginTop: '1em' }}>
                <Form.Field>
                  <label><LocalizedText source={"Metadata Package (JSON)"} /></label>
                  <TextArea
                    onChange={(e) => setImportPackage(e.target.value)}
                    placeholder={interfaceText("Paste exported metadata package JSON here...")}
                    rows={6}
                    value={importPackage}
                   {...interfaceTextProps("Paste exported metadata package JSON here...")}/>
                </Form.Field>
              </Form>

              {/* Results */}
              {conflictAnalysis && (
                <div style={{ marginTop: '1em' }}>
                  {conflictAnalysis.error ? (
                    <Message error>
                      <p>{conflictAnalysis.error}</p>
                    </Message>
                  ) : (
                    <Message info>
                      <Message.Header><LocalizedText source={"Conflict Analysis"} /></Message.Header>
                      <p>
                        <strong><LocalizedText source={"Total Entries:"} /></strong>{' '}
                        {conflictAnalysis.totalEntries}
                        <br />
                        <strong><LocalizedText source={"Conflicting:"} /></strong>{' '}
                        {conflictAnalysis.conflictingEntries}
                        <br />
                        <strong><LocalizedText source={"Clean:"} /></strong> {conflictAnalysis.cleanEntries}
                        <br />
                        <strong><LocalizedText source={"Recommended Strategy:"} /></strong>{' '}
                        {Object.entries(
                          conflictAnalysis.recommendedStrategies || {},
                        ).sort(([, a], [, b]) => b - a)[0]?.[0] || interfaceText('Merge')}
                      </p>
                    </Message>
                  )}
                </div>
              )}

              {importResult && (
                <div style={{ marginTop: '1em' }}>
                  {importResult.error ? (
                    <Message error>
                      <p>{importResult.error}</p>
                    </Message>
                  ) : (
                    <Message success>
                      <Message.Header>
                        <LocalizedText source={"Import"} />{' '}
                        {importResult.success
                          ? <LocalizedText source={"Successful"} />
                          : <LocalizedText source={"Completed with Issues"} />}
                      </Message.Header>
                      <p>
                        <strong><LocalizedText source={"Processed:"} /></strong>{' '}
                        {importResult.entriesProcessed}
                        <br />
                        <strong><LocalizedText source={"Imported:"} /></strong>{' '}
                        {importResult.entriesImported}
                        <br />
                        <strong><LocalizedText source={"Skipped:"} /></strong> {importResult.entriesSkipped}
                        <br />
                        <strong><LocalizedText source={"Conflicts Resolved:"} /></strong>{' '}
                        {importResult.conflictsResolved}
                        <br />
                        <strong><LocalizedText source={"Duration:"} /></strong>{' '}
                        {importResult.duration?.TotalSeconds.toFixed(2)}<LocalizedText source={"s"} /></p>
                      {importResult.errors?.length > 0 && (
                        <details>
                          <summary>
                            <LocalizedText source={"Errors ("} />{importResult.errors.length})
                          </summary>
                          <List bulleted>
                            {importResult.errors.map((error, index) => (
                              <List.Item key={index}>{error}</List.Item>
                            ))}
                          </List>
                        </details>
                      )}
                    </Message>
                  )}
                </div>
              )}
            </Card.Content>
          </Card>
        </Grid.Column>

    </>
  );
});

export default MediaCoreMetadataPortabilityPanel;
