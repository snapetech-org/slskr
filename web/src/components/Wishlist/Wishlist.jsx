import './Wishlist.css';
import WishlistItemRow from './WishlistItemRow';
import WishlistModal from './WishlistModal';
import CsvImportModal from './CsvImportModal';
import { useMountedFlag } from './wishlistHooks';
import {
  buildWishlistRequestReviewPacket,
  buildWishlistRequestSummary,
  formatWishlistRequestReviewPacket,
  getRunnableWishlistRequests,
} from '../../lib/acquisitionRequests';
import { toDisplayError } from '../../lib/errors';
import { formatRegionalNumber, useRegionalFormat } from '../../lib/util';
import { interfaceText, useInterfaceLanguage } from '../../lib/interfaceLocale';
import * as wishlistAPI from '../../lib/wishlist';
import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { toast } from 'react-toastify';
import {
  Button,
  Checkbox,
  Form,
  Header,
  Icon,
  Label,
  Message,
  Popup,
  Segment,
  Table,
} from 'semantic-ui-react';

const Wishlist = () => {
  const { t, languageFor, directionFor } = useInterfaceLanguage();
  useRegionalFormat();
  const translateRef = useRef(t);
  translateRef.current = t;
  const localized = (source, parameters) => (
    <span lang={languageFor(source)} dir={directionFor(source)}>
      {t(source, parameters)}
    </span>
  );
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState(null);
  const [modalItem, setModalItem] = useState(null);
  const [showModal, setShowModal] = useState(false);
  const [showImportModal, setShowImportModal] = useState(false);
  const [requestCopyStatus, setRequestCopyStatus] = useState(null);
  const [bulkRunning, setBulkRunning] = useState(false);
  const [bulkFilter, setBulkFilter] = useState('');
  const [selectedIds, setSelectedIds] = useState(() => new Set());
  const mountedRef = useMountedFlag();
  const loadRequestIdRef = useRef(0);
  const operationRequestIdRef = useRef(0);
  const operationInFlightRef = useRef(false);
  const requestSummary = useMemo(
    () =>
      buildWishlistRequestSummary({
        items,
      }),
    [items],
  );
  const runnableRequests = useMemo(
    () => getRunnableWishlistRequests(items, { limit: 3 }),
    [items],
  );

  const beginOperation = () => {
    if (!mountedRef.current || operationInFlightRef.current) return false;
    operationInFlightRef.current = true;
    return true;
  };

  const finishOperation = () => {
    operationInFlightRef.current = false;
  };

  const copyRequestReviewPacket = async () => {
    const packet = buildWishlistRequestReviewPacket({
      items,
    });
    const report = formatWishlistRequestReviewPacket(packet);

    if (!navigator.clipboard?.writeText) {
      setRequestCopyStatus({ source: 'Clipboard unavailable; copy the request summary manually.' });
      return;
    }

    try {
      await navigator.clipboard.writeText(report);
      if (mountedRef.current) {
        setRequestCopyStatus({ source: 'Wishlist request review copied.' });
      }
    } catch {
      if (mountedRef.current) {
        setRequestCopyStatus({ source: 'Unable to copy Wishlist request review.' });
      }
    }
  };

  const runEnabledSearches = async () => {
    if (!beginOperation()) return;
    const requestId = ++operationRequestIdRef.current;
    setBulkRunning(true);
    const results = [];

    try {
      for (const item of runnableRequests) {
        if (
          !mountedRef.current ||
          requestId !== operationRequestIdRef.current
        ) {
          return;
        }
        try {
          const result = await wishlistAPI.runSearch(item.id);
          if (
            !mountedRef.current ||
            requestId !== operationRequestIdRef.current
          ) {
            return;
          }
          results.push({
            id: item.id,
            responseCount: result?.responseCount ?? result?.ResponseCount ?? 0,
            status: 'ran',
          });
        } catch (error) {
          if (
            !mountedRef.current ||
            requestId !== operationRequestIdRef.current
          ) {
            return;
          }
          results.push({
            error: toDisplayError(error, 'Search failed'),
            id: item.id,
            status: 'failed',
          });
        }
      }

      const ran = results.filter((result) => result.status === 'ran').length;
      const failed = results.filter((result) => result.status === 'failed').length;
      if (
        !mountedRef.current ||
        requestId !== operationRequestIdRef.current
      ) {
        return;
      }
      setRequestCopyStatus({
        source: 'Ran {completed} enabled Wishlist searches; {failed} failed.',
        parameters: {
          completed: formatRegionalNumber(ran),
          failed: formatRegionalNumber(failed),
        },
      });
      await loadItems();
    } finally {
      if (
        mountedRef.current &&
        requestId === operationRequestIdRef.current
      ) {
        setBulkRunning(false);
      }
      finishOperation();
    }
  };

  const loadItems = useCallback(async () => {
    const requestId = ++loadRequestIdRef.current;
    if (mountedRef.current) setLoadError(null);
    try {
      const data = await wishlistAPI.getAll();
      if (
        !mountedRef.current ||
        requestId !== loadRequestIdRef.current
      ) {
        return;
      }
      const nextItems = Array.isArray(data) ? data : [];
      setItems(nextItems);
      setLoadError(null);
      setSelectedIds((current) => {
        const availableIds = new Set(nextItems.map((item) => item.id));
        return new Set(
          [...current].filter((itemId) => availableIds.has(itemId)),
        );
      });
    } catch (error) {
      if (
        mountedRef.current &&
        requestId === loadRequestIdRef.current
      ) {
        console.error(error);
        setLoadError(toDisplayError(error, interfaceText('Could not load wishlist.')));
        toast.error(interfaceText('Could not load wishlist.'));
      }
    } finally {
      if (
        mountedRef.current &&
        requestId === loadRequestIdRef.current
      ) {
        setLoading(false);
      }
    }
  }, []);

  const toggleSelection = (id, selected) => {
    setSelectedIds((current) => {
      const next = new Set(current);
      if (selected) {
        next.add(id);
      } else {
        next.delete(id);
      }
      return next;
    });
  };

  const toggleAllSelections = (selected) => {
    setSelectedIds(selected ? new Set(items.map((item) => item.id)) : new Set());
  };

  const handleBulkFilter = async () => {
    const ids = [...selectedIds];
    if (ids.length === 0 || !beginOperation()) return;

    const requestId = ++operationRequestIdRef.current;
    setBulkRunning(true);
    try {
      const result = await wishlistAPI.updateFilters(ids, bulkFilter.trim());
      if (
        !mountedRef.current ||
        requestId !== operationRequestIdRef.current
      ) {
        return;
      }
      const updatedCount = result?.updatedCount ?? result?.UpdatedCount ?? ids.length;
      toast.success(translateRef.current('Updated filters for {count} item(s)', { count: formatRegionalNumber(updatedCount) }));
      setSelectedIds(new Set());
      setBulkFilter('');
      await loadItems();
    } catch (error) {
      if (
        mountedRef.current &&
        requestId === operationRequestIdRef.current
      ) {
        console.error(error);
        toast.error(translateRef.current('Could not update Wishlist filters.'));
      }
    } finally {
      if (
        mountedRef.current &&
        requestId === operationRequestIdRef.current
      ) {
        setBulkRunning(false);
      }
      finishOperation();
    }
  };

  useEffect(() => {
    void loadItems();
  }, [loadItems]);

  const handleAdd = () => {
    setModalItem(null);
    setShowModal(true);
  };

  const handleImportClick = () => {
    setShowImportModal(true);
  };

  const handleEdit = (item) => {
    setModalItem(item);
    setShowModal(true);
  };

  const handleSave = async (item) => {
    if (!beginOperation()) return;
    try {
      if (item.id) {
        await wishlistAPI.update(item.id, item);
        if (!mountedRef.current) return;
        toast.success(translateRef.current('Wishlist item updated'));
      } else {
        await wishlistAPI.create(item);
        if (!mountedRef.current) return;
        toast.success(translateRef.current('Added to wishlist'));
      }

      await loadItems();
    } finally {
      finishOperation();
    }
  };

  const handleDelete = async (id) => {
    if (!beginOperation()) return;
    const requestId = ++operationRequestIdRef.current;
    try {
      await wishlistAPI.remove(id);
      if (
        !mountedRef.current ||
        requestId !== operationRequestIdRef.current
      ) {
        return;
      }
      toast.success(translateRef.current('Wishlist item deleted'));
      await loadItems();
    } catch (error) {
      if (
        mountedRef.current &&
        requestId === operationRequestIdRef.current
      ) {
        console.error(error);
        toast.error(translateRef.current('Could not delete this Wishlist item.'));
      }
    } finally {
      finishOperation();
    }
  };

  const handleRunSearch = async (id) => {
    if (!beginOperation()) return undefined;
    try {
      const result = await wishlistAPI.runSearch(id);
      await loadItems();
      return result;
    } finally {
      finishOperation();
    }
  };

  const handleImport = async (request) => {
    if (!beginOperation()) return;
    try {
      const result = await wishlistAPI.importCsv(request);
      if (!mountedRef.current) return;
      toast.success(
          translateRef.current('Imported {created} searches; {duplicates} duplicates and {skipped} skipped.', {
            created: formatRegionalNumber(result?.createdCount ?? 0),
            duplicates: formatRegionalNumber(result?.duplicateCount ?? 0),
            skipped: formatRegionalNumber(result?.skippedCount ?? 0),
          }),
      );
      await loadItems();
    } finally {
      finishOperation();
    }
  };

  return (
    <div className="wishlist-container">
      <Segment
        className="wishlist-header"
        clearing
      >
        <Header
          as="h2"
          floated="left"
        >
          <Icon name="star" />
          <Header.Content>
            {localized('Wishlist')}
            <Header.Subheader>
              {localized('Saved searches that run automatically')}
            </Header.Subheader>
          </Header.Content>
        </Header>
        <Popup
          content={localized('Add one saved search to the Wishlist. Enabled entries run later using the normal scheduler.')}
          trigger={
            <Button
              floated="right"
              icon
              labelPosition="left"
              onClick={handleAdd}
              primary
            >
              <Icon name="plus" />
              {localized('Add Search')}
            </Button>
          }
        />
        <Popup
          content={localized('Import a playlist CSV into Wishlist searches without starting a large search burst immediately.')}
          trigger={
            <Button
              floated="right"
              icon
              labelPosition="left"
              onClick={handleImportClick}
            >
              <Icon name="file alternate outline" />
              {localized('Import CSV')}
            </Button>
          }
        />
      </Segment>

      {!loading && (
        <Segment className="wishlist-request-summary">
          <div className="wishlist-request-summary-header">
            <Header as="h3">
              <Icon name="clipboard check" />
              {localized('Request Portal Summary')}
              <Header.Subheader>
                {localized('Operator view of wanted music before acquisition jobs are wired.')}
              </Header.Subheader>
            </Header>
            <Popup
              content={localized('Copy the current Wishlist request review packet. This does not start searches, peer browsing, downloads, or automation.')}
              position="top center"
              trigger={
                <Button
                  aria-label={t('Copy Wishlist request review')}
                  lang={languageFor('Copy Wishlist request review')}
                  dir={directionFor('Copy Wishlist request review')}
                  onClick={copyRequestReviewPacket}
                  size="small"
                >
                  <Icon name="copy" />
                  {localized('Copy Review')}
                </Button>
              }
            />
            <Popup
              content={localized('Run up to three enabled Wishlist searches now through the backend. This starts search jobs only; downloads still require the normal result selection and policy.')}
              position="top center"
              trigger={
                <Button
                  aria-label={t('Run enabled Wishlist searches')}
                  lang={languageFor('Run enabled Wishlist searches')}
                  dir={directionFor('Run enabled Wishlist searches')}
                  disabled={runnableRequests.length === 0}
                  loading={bulkRunning}
                  onClick={runEnabledSearches}
                  primary
                  size="small"
                >
                  <Icon name="play" />
                  {localized('Run Enabled')}
                </Button>
              }
            />
          </div>
          <div className="wishlist-request-summary-grid">
            {/* Plain counts get a neutral pill; color is reserved for the two
                pills below that actually report a state worth noticing. */}
            <Label basic>
              {localized('Requests')}
              <Label.Detail>{formatRegionalNumber(requestSummary.total)}</Label.Detail>
            </Label>
            <Label basic>
              {localized('Enabled')}
              <Label.Detail>{formatRegionalNumber(requestSummary.enabled)}</Label.Detail>
            </Label>
            <Label basic>
              {localized('Automatic')}
              <Label.Detail>{formatRegionalNumber(requestSummary.automatic)}</Label.Detail>
            </Label>
            <Label color={requestSummary.reviewCount > 0 ? 'yellow' : 'grey'}>
              {localized('Needs Review')}
              <Label.Detail>{formatRegionalNumber(requestSummary.reviewCount)}</Label.Detail>
            </Label>
            <Label color={requestSummary.quotaStatus === 'Within quota' ? 'green' : 'orange'}>
              {localized(requestSummary.quotaStatus)}
              <Label.Detail>{localized('{count} left', { count: formatRegionalNumber(requestSummary.quotaRemaining) })}</Label.Detail>
            </Label>
          </div>
          {requestCopyStatus && (
          <Label basic lang={requestCopyStatus && languageFor(requestCopyStatus.source)} dir={requestCopyStatus && directionFor(requestCopyStatus.source)}>
              {requestCopyStatus && t(requestCopyStatus.source, requestCopyStatus.parameters)}
            </Label>
          )}
        </Segment>
      )}

      {selectedIds.size > 0 && (
        <Segment className="wishlist-bulk-actions">
          <Header as="h4">
            <Icon name="tasks" />
            {localized('Bulk actions ({count})', { count: formatRegionalNumber(selectedIds.size) })}
          </Header>
          <Form>
            <Form.Input
              aria-label={t('Bulk wishlist filter')}
              lang={languageFor('Bulk wishlist filter')}
              dir={directionFor('Bulk wishlist filter')}
              label={localized('Apply filter to selected items')}
              lang={languageFor('e.g., flac OR mp3')}
              dir={directionFor('e.g., flac OR mp3')}
              onChange={(event) => setBulkFilter(event.target.value)}
              placeholder={t('e.g., flac OR mp3')}
              value={bulkFilter}
            />
            <Button
              aria-label={t('Apply filter to selected wishlist items')}
              lang={languageFor('Apply filter to selected wishlist items')}
              dir={directionFor('Apply filter to selected wishlist items')}
              disabled={bulkRunning}
              loading={bulkRunning}
              onClick={handleBulkFilter}
              primary
            >
              <Icon name="filter" />
              {localized('Apply Filter')}
            </Button>
          </Form>
        </Segment>
      )}

      {loadError && (
        <Message
          data-testid="wishlist-load-error"
          error
        >
          <Message.Header>{localized('Wishlist unavailable')}</Message.Header>
          <p>{localized(loadError)}</p>
          <p>{localized('Previously loaded Wishlist items remain visible until the next successful refresh.')}</p>
        </Message>
      )}

      {loading ? (
        <Segment
          loading
          placeholder
        />
      ) : items.length === 0 ? (
        loadError ? null : (
          <Segment
            inverted
            placeholder
          >
            <Header
              icon
              inverted
            >
              <Icon name="star outline" />
              {localized('No wishlist items yet')}
            </Header>
            <p>
              {localized("Add searches to your wishlist and they'll run automatically.")}
            </p>
            <Button
              onClick={handleAdd}
              primary
            >
              {localized('Add Your First Search')}
            </Button>
          </Segment>
        )
      ) : (
        <Table
          celled
          striped
        >
          <Table.Header>
            <Table.Row>
              <Table.HeaderCell width={1}>
                <Checkbox
                  aria-label={t('Select all wishlist items for bulk actions')}
                  lang={languageFor('Select all wishlist items for bulk actions')}
                  dir={directionFor('Select all wishlist items for bulk actions')}
                  checked={items.length > 0 && selectedIds.size === items.length}
                  onChange={(_, { checked }) => toggleAllSelections(checked)}
                />
              </Table.HeaderCell>
              <Table.HeaderCell width={1}>{localized('Active')}</Table.HeaderCell>
              <Table.HeaderCell>{localized('Search')}</Table.HeaderCell>
              <Table.HeaderCell
                textAlign="center"
                width={1}
              >
                {localized('Auto')}
              </Table.HeaderCell>
              <Table.HeaderCell width={3}>{localized('Last Run')}</Table.HeaderCell>
              <Table.HeaderCell
                textAlign="center"
                width={1}
              >
                {localized('Matches')}
              </Table.HeaderCell>
              <Table.HeaderCell
                textAlign="center"
                width={1}
              >
                {localized('Runs')}
              </Table.HeaderCell>
              <Table.HeaderCell width={2}>{localized('Request State')}</Table.HeaderCell>
              <Table.HeaderCell width={3}>{localized('Actions')}</Table.HeaderCell>
            </Table.Row>
          </Table.Header>
          <Table.Body>
            {items.map((item) => (
              <WishlistItemRow
                item={item}
                key={item.id}
                onDelete={handleDelete}
                onEdit={handleEdit}
                onRunSearch={handleRunSearch}
                onSelect={toggleSelection}
                selected={selectedIds.has(item.id)}
              />
            ))}
          </Table.Body>
        </Table>
      )}

      {showModal && (
        <WishlistModal
          item={modalItem}
          onClose={() => setShowModal(false)}
          onSave={handleSave}
        />
      )}

      {showImportModal && (
        <CsvImportModal
          onClose={() => setShowImportModal(false)}
          onImport={handleImport}
        />
      )}
    </div>
  );
};

export default Wishlist;
