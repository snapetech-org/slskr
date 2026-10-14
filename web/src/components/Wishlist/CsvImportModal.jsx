import { readFileTextBounded } from '../../lib/fileReaders';
import { useMountedFlag } from './wishlistHooks';
import { useInterfaceLanguage } from '../../lib/interfaceLocale';
import React, { useRef, useState } from 'react';
import { toast } from 'react-toastify';
import { Button, Checkbox, Form, Icon, Modal, Popup } from 'semantic-ui-react';

const CsvImportModal = ({ onClose, onImport }) => {
  const { t, languageFor, directionFor } = useInterfaceLanguage();
  const localized = (source) => (
    <span lang={languageFor(source)} dir={directionFor(source)}>{t(source)}</span>
  );
  const localizedRef = useRef(localized);
  localizedRef.current = localized;
  const [csvText, setCsvText] = useState('');
  const [filter, setFilter] = useState('');
  const [enabled, setEnabled] = useState(true);
  const [autoDownload, setAutoDownload] = useState(false);
  const [includeAlbum, setIncludeAlbum] = useState(false);
  const [maxResults, setMaxResults] = useState(100);
  const [importing, setImporting] = useState(false);
  const mountedRef = useMountedFlag();
  const operationRequestIdRef = useRef(0);
  const importInFlightRef = useRef(false);

  const handleFile = async (event) => {
    const file = event.target.files?.[0];
    if (!file) return;
    try {
      const text = await readFileTextBounded(file, 768 * 1024);
      if (mountedRef.current) {
        setCsvText(text);
      }
    } catch (error) {
      if (mountedRef.current) {
        console.error(error);
        toast.error(localizedRef.current('Could not read the CSV file.'));
      }
    }
  };

  const handleImport = async () => {
    if (!csvText.trim()) {
      toast.error(localizedRef.current('CSV text is required.'));
      return;
    }
    if (importInFlightRef.current || !mountedRef.current) return;
    importInFlightRef.current = true;

    const requestId = ++operationRequestIdRef.current;
    setImporting(true);
    try {
      await onImport({
        autoDownload,
        csvText,
        enabled,
        filter: filter.trim() || undefined,
        includeAlbum,
        maxResults,
      });
      if (
        !mountedRef.current ||
        requestId !== operationRequestIdRef.current
      ) {
        return;
      }
      onClose();
    } catch (error) {
      if (
        mountedRef.current &&
        requestId === operationRequestIdRef.current
      ) {
        console.error(error);
        toast.error(localizedRef.current('Could not import the CSV.'));
      }
    } finally {
      if (
        mountedRef.current &&
        requestId === operationRequestIdRef.current
      ) {
        setImporting(false);
      }
      importInFlightRef.current = false;
    }
  };

  return (
    <Modal
      onClose={onClose}
      open
      size="small"
    >
      <Modal.Header>
        <Icon name="file alternate outline" />
        {localized('Import CSV Playlist')}
      </Modal.Header>
      <Modal.Content>
        <Form>
          <Form.Input
            accept=".csv,text/csv"
            label={localized('CSV File')}
            onChange={handleFile}
            type="file"
          />
          <Form.TextArea
            dir={directionFor('Track name,Artist name,Album name')}
            lang={languageFor('Track name,Artist name,Album name')}
            label={localized('CSV Text')}
            onChange={(event) => setCsvText(event.target.value)}
            placeholder={t('Track name,Artist name,Album name')}
            rows={8}
            value={csvText}
          />
          <Form.Input
            dir={directionFor('e.g., flac OR mp3')}
            lang={languageFor('e.g., flac OR mp3')}
            label={localized('Filter (optional)')}
            onChange={(event) => setFilter(event.target.value)}
            placeholder={t('e.g., flac OR mp3')}
            value={filter}
          />
          <Form.Input
            dir={directionFor('Max Results')}
            lang={languageFor('Max Results')}
            label={localized('Max Results')}
            max={1_000}
            min={1}
            onChange={(event) =>
              setMaxResults(Number.parseInt(event.target.value, 10) || 100)
            }
            type="number"
            value={maxResults}
          />
          <Form.Group widths="equal">
            <Form.Field>
              <Checkbox
                checked={enabled}
                dir={directionFor('Enabled')}
                lang={languageFor('Enabled')}
                label={localized('Enabled')}
                onChange={(_, data) => setEnabled(data.checked)}
                toggle
              />
            </Form.Field>
            <Form.Field>
              <Checkbox
                checked={autoDownload}
                dir={directionFor('Auto-download matches')}
                lang={languageFor('Auto-download matches')}
                label={localized('Auto-download matches')}
                onChange={(_, data) => setAutoDownload(data.checked)}
                toggle
              />
            </Form.Field>
            <Form.Field>
              <Checkbox
                checked={includeAlbum}
                dir={directionFor('Include album')}
                lang={languageFor('Include album')}
                label={localized('Include album')}
                onChange={(_, data) => setIncludeAlbum(data.checked)}
                toggle
              />
            </Form.Field>
          </Form.Group>
        </Form>
      </Modal.Content>
      <Modal.Actions>
        <Popup
          content={localized('Close the CSV importer without adding any wishlist searches.')}
          trigger={<Button onClick={onClose}>{localized('Cancel')}</Button>}
        />
        <Popup
          content={localized('Create wishlist searches from the parsed CSV rows using the selected options.')}
          trigger={
            <Button
              disabled={importing}
              loading={importing}
              onClick={handleImport}
              primary
            >
              {localized('Import')}
            </Button>
          }
        />
      </Modal.Actions>
    </Modal>
  );
};

export default CsvImportModal;
