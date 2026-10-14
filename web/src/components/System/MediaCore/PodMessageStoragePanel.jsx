import LocalizedText from "../../Shared/LocalizedText";
import { interfaceText, interfaceTextProps, useInterfaceLanguage } from "../../../lib/interfaceLocale";
import { formatRegionalDateTime, formatRegionalNumber, useRegionalFormat, formatRegionalFixedNumber } from '../../../lib/util';
import * as mediacore from '../../../lib/mediacore';
import { toDisplayError } from '../../../lib/errors';
import Button from './MediaCoreButton';
import MessageSearchPanel from './MessageSearchPanel';
import PodMessageMaintenanceActions from './PodMessageMaintenanceActions';
import PodWorkflowNotice from './PodWorkflowNotice';
import React, { useRef } from 'react';
import { toast } from 'react-toastify';
import {
  Card,
  Grid,
  Header,
  Icon,
  Message,
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

const PodMessageStoragePanel = React.memo(({ visible }) => {
  useInterfaceLanguage();
  useRegionalFormat();
  const mountedRef = useRef(true);
  React.useEffect(() => {
    mountedRef.current = true;
    return () => {
      mountedRef.current = false;
    };
  }, []);

  // Pod Message Storage states
  const [storageStats, setStorageStats] = useMountedState(mountedRef, null);
  const [storageStatsLoading, setStorageStatsLoading] = useMountedState(mountedRef, false);
  const [cleanupLoading, setCleanupLoading] = useMountedState(mountedRef, false);

  // Pod Message Storage handlers
  const handleGetStorageStats = async () => {
    try {
      setStorageStatsLoading(true);
      setStorageStats(null);
      const result = await mediacore.getMessageStorageStats();
      setStorageStats(result);
    } catch (error_) {
      setStorageStats({ error: toDisplayError(error_) });
      toast.error(`Failed to get storage stats: ${toDisplayError(error_)}`);
    } finally {
      setStorageStatsLoading(false);
    }
  };

  const handleCleanupMessages = async () => {
    try {
      setCleanupLoading(true);
      const thirtyDaysAgo = Date.now() - 30 * 24 * 60 * 60 * 1_000;
      const result = await mediacore.cleanupMessages(thirtyDaysAgo);
      toast.success(interfaceText("Cleaned up {result} old messages", { "result": (result) }));
      // Refresh stats after cleanup
      await handleGetStorageStats();
    } catch (error_) {
      toast.error(`Failed to cleanup messages: ${toDisplayError(error_)}`);
    } finally {
      setCleanupLoading(false);
    }
  };

  return (
    <>
        {/* Pod Message Storage */}
        <Grid.Column style={{ display: visible ? undefined : 'none' }} width={16}>
          <Card id="pod-message-storage" fluid>
            <Card.Content>
              <Card.Header>
                <Icon name="database" />
                <LocalizedText source={"Pod Message Storage"} /></Card.Header>
              <Card.Description>
                <LocalizedText source={"SQLite-backed message storage with full-text search and retention policies"} /></Card.Description>
              <PodWorkflowNotice title={interfaceText("Mutates local message storage")} {...interfaceTextProps("Mutates local message storage")}>
                <LocalizedText source={"Cleanup, rebuild, and vacuum actions affect local pod message storage. Search and count actions are read-only."} /></PodWorkflowNotice>
            </Card.Content>

            {/* Message Storage */}
            <Card.Content>
              <Header size="small"><LocalizedText source={"Storage Management"} /></Header>

              <div style={{ marginBottom: '1em' }}>
                <Button
                  color="teal"
                  loading={storageStatsLoading}
                  onClick={() => handleGetStorageStats()}
                  size="small"
                >
                  <LocalizedText source={"Get Storage Stats"} /></Button>

                <Button
                  color="purple"
                  loading={cleanupLoading}
                  onClick={() => handleCleanupMessages()}
                  size="small"
                >
                  <LocalizedText source={"Cleanup Old Messages (30 days)"} /></Button>

                <PodMessageMaintenanceActions size="small" />
              </div>

              {storageStats && (
                <Message
                  size="small"
                  style={{ marginBottom: '1em' }}
                >
                  <Message.Header><LocalizedText source={"Message Storage Statistics"} /></Message.Header>
                  <p>
                    <strong><LocalizedText source={"Total Messages:"} /></strong>{' '}
                    {formatRegionalNumber(storageStats.totalMessages) || 0}
                    <br />
                    <strong><LocalizedText source={"Estimated Size:"} /></strong>{' '}
                    {formatRegionalFixedNumber((storageStats.totalSizeBytes / (1_024 * 1_024)), 2)}{' '}
                    MB
                    <br />
                    <strong><LocalizedText source={"Oldest Message:"} /></strong>{' '}
                    {storageStats.oldestMessage
                      ? formatRegionalDateTime(storageStats.oldestMessage)
                      : <LocalizedText source={"None"} />}
                    <br />
                    <strong><LocalizedText source={"Newest Message:"} /></strong>{' '}
                    {storageStats.newestMessage
                      ? formatRegionalDateTime(storageStats.newestMessage)
                      : <LocalizedText source={"None"} />}
                    <br />
                    <strong><LocalizedText source={"Pods with Messages:"} /></strong>{' '}
                    {Object.keys(storageStats.messagesPerPod || {}).length}
                    <br />
                    <strong><LocalizedText source={"Active Channels:"} /></strong>{' '}
                    {Object.keys(storageStats.messagesPerChannel || {}).length}
                  </p>
                </Message>
              )}

              <MessageSearchPanel />
            </Card.Content>
          </Card>
        </Grid.Column>

    </>
  );
});

export default PodMessageStoragePanel;
