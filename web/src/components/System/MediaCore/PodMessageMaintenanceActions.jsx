import LocalizedText from "../../Shared/LocalizedText";
import { interfaceText, interfaceTextProps } from "../../../lib/interfaceLocale";
import * as mediacore from '../../../lib/mediacore';
import { toDisplayError } from '../../../lib/errors';
import Button from './MediaCoreButton';
import React, { useEffect, useRef } from 'react';
import { toast } from 'react-toastify';

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

const PodMessageMaintenanceActions = ({ size = 'tiny' }) => {
  const mountedRef = useRef(true);

  useEffect(() => {
    mountedRef.current = true;
    return () => {
      mountedRef.current = false;
    };
  }, []);

  const [rebuildIndexLoading, setRebuildIndexLoading] = useMountedState(
    mountedRef,
    false,
  );
  const [vacuumLoading, setVacuumLoading] = useMountedState(mountedRef, false);

  const handleRebuildSearchIndex = async () => {
    try {
      setRebuildIndexLoading(true);
      const result = await mediacore.rebuildSearchIndex();
      toast.success(interfaceText(result ? 'Search index rebuilt successfully' : 'Search index rebuild failed'));
    } catch (error_) {
      toast.error(interfaceText('Failed to rebuild search index: {error}', { error: toDisplayError(error_) }));
    } finally {
      setRebuildIndexLoading(false);
    }
  };

  const handleVacuumDatabase = async () => {
    try {
      setVacuumLoading(true);
      const result = await mediacore.vacuumDatabase();
      toast.success(interfaceText(result ? 'Database vacuum completed successfully' : 'Database vacuum failed'));
    } catch (error_) {
      toast.error(interfaceText('Failed to vacuum database: {error}', { error: toDisplayError(error_) }));
    } finally {
      setVacuumLoading(false);
    }
  };

  return (
    <>
      <Button
        color="blue"
        loading={rebuildIndexLoading}
        onClick={handleRebuildSearchIndex}
        size={size}
      >
        <LocalizedText source={"Rebuild Search Index"} /></Button>
      <Button
        color="orange"
        loading={vacuumLoading}
        onClick={handleVacuumDatabase}
        size={size}
      >
        <LocalizedText source={"Vacuum Database"} /></Button>
    </>
  );
};

export default React.memo(PodMessageMaintenanceActions);
