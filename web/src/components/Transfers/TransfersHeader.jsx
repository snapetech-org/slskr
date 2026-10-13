import { isStateCancellable, isStateRetryable } from '../../lib/transfers';
import { Div, Nbsp } from '../Shared';
import ShrinkableDropdownButton from '../Shared/ShrinkableDropdownButton';
import React, { useEffect, useMemo, useState } from 'react';
import { getInterfaceLanguageIndex, useInterfaceLanguage } from '../../lib/interfaceLocale';
import transferBulkActionLabelsUrl from '../../lib/transfer-bulk-action-labels.json?url';
import { Checkbox, Icon, Popup, Segment } from 'semantic-ui-react';

const getRetryableFiles = ({ files, retryOption }) => {
  switch (retryOption) {
    case 'Errored':
      return files.filter((file) =>
        [
          'Completed, TimedOut',
          'Completed, Errored',
          'Completed, Rejected',
        ].includes(file.state),
      );
    case 'Cancelled':
      return files.filter((file) => file.state === 'Completed, Cancelled');
    case 'All':
      return files.filter((file) => isStateRetryable(file.state));
    default:
      return [];
  }
};

const getCancellableFiles = ({ cancelOption, files }) => {
  switch (cancelOption) {
    case 'All':
      return files.filter((file) => isStateCancellable(file.state));
    case 'Queued':
      return files.filter((file) =>
        ['Queued, Locally', 'Queued, Remotely'].includes(file.state),
      );
    case 'In Progress':
      return files.filter((file) => file.state === 'InProgress');
    default:
      return [];
  }
};

const getRemovableFiles = ({ files, removeOption }) => {
  switch (removeOption) {
    case 'Succeeded':
      return files.filter((file) => file.state === 'Completed, Succeeded');
    case 'Errored':
      return files.filter((file) =>
        [
          'Completed, TimedOut',
          'Completed, Errored',
          'Completed, Rejected',
        ].includes(file.state),
      );
    case 'Cancelled':
      return files.filter((file) => file.state === 'Completed, Cancelled');
    case 'Completed':
      return files.filter((file) => file.state.includes('Completed'));
    default:
      return [];
  }
};

const TransfersHeader = ({
  acceleratedEnabled = false,
  acceleratedChanging = false,
  autoReplaceEnabled = false,
  autoReplaceThreshold = 5,
  autoReplaceChanging = false,
  modeStatusError = null,
  cancelling = false,
  direction,
  onAcceleratedChange,
  onAutoReplaceChange,
  onCancelAll,
  onRemoveAll,
  onRetryAll,
  removing = false,
  retrying = false,
  server = { isConnected: true },
  transfers,
}) => {
  const { language, t, languageFor } = useInterfaceLanguage();
  const [bulkActionLabels, setBulkActionLabels] = useState(null);
  useEffect(() => {
    if (language === 'en') return;
    fetch(transferBulkActionLabelsUrl)
      .then((response) => response.json())
      .then(setBulkActionLabels)
      .catch(() => null);
  }, [language]);
  const localizedText = (source, text = t(source), localizedLanguage = languageFor(source)) => (
    <span lang={localizedLanguage} dir={localizedLanguage === 'ar' ? 'rtl' : 'ltr'}>{text}</span>
  );
  const localizedTransferLabel = (source) => {
    const languageIndex = getInterfaceLanguageIndex(language);
    const translation = languageIndex === undefined
      ? undefined
      : bulkActionLabels?.[source]?.[languageIndex];
    const labelLanguage = translation ? language : 'en';
    return { text: translation || source, language: labelLanguage };
  };
  const localizedTransferText = (source) => {
    const label = localizedTransferLabel(source);
    return localizedText(source, label.text, label.language);
  };
  const localizedAriaLabel = (source) => {
    const label = localizedTransferLabel(source);
    return {
      ariaLabel: label.text,
      ariaLabelDir: label.language === 'ar' ? 'rtl' : 'ltr',
      ariaLabelLang: label.language,
    };
  };
  const localizedBulkAction = (action, option) => {
    const source = `${action} All${option === 'All' ? '' : ` ${option}`}`;
    return localizedTransferText(source);
  };
  const [removeOption, setRemoveOption] = useState('Succeeded');
  const [cancelOption, setCancelOption] = useState('All');
  const [retryOption, setRetryOption] = useState('Errored');

  const files = useMemo(() => {
    return transfers
      .reduce((accumulator, username) => {
        const allUserFiles = username.directories.reduce(
          (directoryAccumulator, directory) => {
            return directoryAccumulator.concat(directory.files);
          },
          [],
        );

        return accumulator.concat(allUserFiles);
      }, [])
      .filter((file) => file.direction.toLowerCase() === direction);
  }, [direction, transfers]);

  const empty = files.length === 0;
  const working = retrying || cancelling || removing;

  return (
    <Segment
      className="transfers-header-segment"
      raised
    >
      <div className="transfers-segment-icon">
        <Icon
          name={direction}
          size="big"
        />
      </div>
      <Div
        className="transfers-header-buttons"
        hidden={empty}
      >
        <ShrinkableDropdownButton
          {...localizedAriaLabel('Filter retryable downloads')}
          color="green"
          disabled={working || empty || !server.isConnected}
          hidden={direction === 'upload'}
          icon="redo"
          loading={retrying}
          mediaQuery="(max-width: 715px)"
          onChange={(_, data) => setRetryOption(data.value)}
          onClick={() => onRetryAll(getRetryableFiles({ files, retryOption }))}
          options={[
            { key: 'errored', text: localizedText('Errored'), value: 'Errored' },
            { key: 'cancelled', text: localizedText('Cancelled'), value: 'Cancelled' },
            { key: 'all', text: localizedText('All'), value: 'All' },
          ]}
        >
          {localizedBulkAction('Retry', retryOption)}
        </ShrinkableDropdownButton>
        <Nbsp />
        <ShrinkableDropdownButton
          {...localizedAriaLabel('Filter downloads to cancel')}
          color="red"
          disabled={working || empty}
          icon="x"
          loading={cancelling}
          mediaQuery="(max-width: 715px)"
          onChange={(_, data) => setCancelOption(data.value)}
          onClick={() =>
            onCancelAll(getCancellableFiles({ cancelOption, files }))
          }
          options={[
            { key: 'all', text: localizedText('All'), value: 'All' },
            { key: 'queued', text: localizedText('Queued'), value: 'Queued' },
            { key: 'inProgress', text: localizedText('In Progress'), value: 'In Progress' },
          ]}
        >
          {localizedBulkAction('Cancel', cancelOption)}
        </ShrinkableDropdownButton>
        <Nbsp />
        <ShrinkableDropdownButton
          {...localizedAriaLabel('Filter downloads to remove')}
          disabled={working || empty}
          icon="trash alternate"
          loading={removing}
          mediaQuery="(max-width: 715px)"
          onChange={(_, data) => setRemoveOption(data.value)}
          onClick={() =>
            onRemoveAll(
              getRemovableFiles({ files, removeOption }),
              false,
              { useBulkClear: removeOption === 'Completed' },
            )
          }
          options={[
            { key: 'succeeded', text: localizedText('Succeeded'), value: 'Succeeded' },
            { key: 'errored', text: localizedText('Errored'), value: 'Errored' },
            { key: 'cancelled', text: localizedText('Cancelled'), value: 'Cancelled' },
            { key: 'completed', text: localizedText('Completed'), value: 'Completed' },
          ]}
        >
          {localizedBulkAction('Remove', removeOption)}
        </ShrinkableDropdownButton>
        <Nbsp />
        <Popup
          content="Allow slow or stalled downloads to use verified alternate sources. Soulseek peers use sequential failover; true multipart chunking is reserved for trusted slskr mesh peers."
          position="bottom right"
          trigger={
            <Checkbox
              checked={acceleratedEnabled}
              className="accelerated-downloads-toggle"
              disabled={
                !server.isConnected ||
                acceleratedChanging ||
                Boolean(modeStatusError)
              }
              hidden={direction === 'upload'}
              label={localizedText('Accelerated')}
              onChange={(_, data) => onAcceleratedChange?.(data.checked)}
              toggle
            />
          }
        />
        <Nbsp />
        <Popup
          content={`Automatically find and replace stuck downloads with alternative sources. Replacements must be within ${autoReplaceThreshold}% file size.`}
          position="bottom right"
          trigger={
            <Checkbox
              checked={autoReplaceEnabled}
              className="auto-replace-toggle"
              disabled={
                !server.isConnected ||
                autoReplaceChanging ||
                Boolean(modeStatusError)
              }
              hidden={direction === 'upload'}
              label={localizedText('Auto-Replace')}
              onChange={(_, data) => onAutoReplaceChange?.(data.checked)}
              toggle
            />
          }
        />
      </Div>
    </Segment>
  );
};

export default TransfersHeader;
