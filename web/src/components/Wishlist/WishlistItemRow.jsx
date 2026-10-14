import { formatRegionalDateTime, formatRegionalNumber, useRegionalFormat } from '../../lib/util';
import { getWishlistRequestState } from '../../lib/acquisitionRequests';
import { encodePathSegment } from '../../lib/pathEncoding';
import { useMountedFlag } from './wishlistHooks';
import { interfaceTextProps, useInterfaceLanguage } from '../../lib/interfaceLocale';
import React, { useRef, useState } from 'react';
import { Link } from 'react-router-dom';
import { toast } from 'react-toastify';
import {
  Button,
  Checkbox,
  Confirm,
  Icon,
  Label,
  Popup,
  Table,
} from 'semantic-ui-react';

const formatDate = (dateString, t) => {
  if (!dateString) return t('Never');
  const date = new Date(dateString);
  if (Number.isNaN(date.getTime())) return t('Never');
  return formatRegionalDateTime(date);
};

const WishlistItemRow = ({
  item,
  onDelete,
  onEdit,
  onRunSearch,
  onSelect,
  selected,
}) => {
  const { t, languageFor, directionFor } = useInterfaceLanguage();
  useRegionalFormat();
  const localized = (source, parameters) => (
    <span lang={languageFor(source)} dir={directionFor(source)}>{t(source, parameters)}</span>
  );
  const localizedRef = useRef(localized);
  localizedRef.current = localized;
  const [confirmDelete, setConfirmDelete] = useState(false);
  const [running, setRunning] = useState(false);
  const mountedRef = useMountedFlag();
  const requestIdRef = useRef(0);
  const inFlightRef = useRef(false);
  const requestState = getWishlistRequestState(item, []);

  const handleRunSearch = async () => {
    if (inFlightRef.current || !mountedRef.current) return;
    inFlightRef.current = true;
    const requestId = ++requestIdRef.current;
    setRunning(true);
    try {
      const result = await onRunSearch(item.id);
      if (
        mountedRef.current &&
        requestId === requestIdRef.current
      ) {
        const responseCount =
          result?.responseCount ?? result?.ResponseCount ?? 0;
        toast.success(localizedRef.current('Search completed with {count} results', { count: formatRegionalNumber(responseCount) }));
      }
    } catch (error) {
      if (
        mountedRef.current &&
        requestId === requestIdRef.current
      ) {
        console.error(error);
        toast.error(localizedRef.current('Search failed. Try again.'));
      }
    } finally {
      if (
        mountedRef.current &&
        requestId === requestIdRef.current
      ) {
        setRunning(false);
      }
      inFlightRef.current = false;
    }
  };

  return (
    <Table.Row>
      <Table.Cell>
        <Checkbox
          aria-label={t('Select {search} for bulk actions', { search: item.searchText })}
          lang={languageFor('Select {search} for bulk actions')}
          dir={directionFor('Select {search} for bulk actions')}
          checked={selected}
          onChange={(_, { checked }) => onSelect(item.id, checked)}
        />
      </Table.Cell>
      <Table.Cell>
        <Icon
          color={item.enabled ? 'green' : 'grey'}
          name={item.enabled ? 'check circle' : 'circle outline'}
        />
      </Table.Cell>
      <Table.Cell>
        <strong>{item.searchText}</strong>
        {item.filter && (
          <div className="wishlist-filter">{localized('Filter:')} {item.filter}</div>
        )}
      </Table.Cell>
      <Table.Cell textAlign="center">
        <Popup
          content={localized('Auto-download best matches')}
          trigger={
            <Icon
              color={item.autoDownload ? 'green' : 'grey'}
              name={item.autoDownload ? 'download' : 'download'}
            />
          }
        />
      </Table.Cell>
          <Table.Cell>{formatDate(item.lastSearchedAt, t)}</Table.Cell>
          <Table.Cell textAlign="center">{formatRegionalNumber(item.lastMatchCount)}</Table.Cell>
      <Table.Cell textAlign="center">{formatRegionalNumber(item.totalSearchCount)}</Table.Cell>
      <Table.Cell>
        <Popup
          content={localized(requestState.summary)}
          position="top center"
          trigger={
            <Label color={requestState.color}>
              {localized(requestState.label)}
            </Label>
          }
        />
      </Table.Cell>
      <Table.Cell>
        {item.lastSearchId && (
          <Link to={`/searches/${encodePathSegment(item.lastSearchId)}`}>
            <Button
              compact
              icon="search"
              size="tiny"
              title={t('View last search results')}
              lang={languageFor('View last search results')}
              dir={directionFor('View last search results')}
            />
          </Link>
        )}
        <Button
          compact
          disabled={running}
          icon="play"
          loading={running}
          onClick={handleRunSearch}
          primary
          size="tiny"
          title={t('Run search now')}
          lang={languageFor('Run search now')}
          dir={directionFor('Run search now')}
        />
        <Button
          compact
          icon="edit"
          onClick={() => onEdit(item)}
          size="tiny"
          title={t('Edit')}
          lang={languageFor('Edit')}
          dir={directionFor('Edit')}
        />
        <Button
          color="red"
          compact
          icon="trash"
          onClick={() => setConfirmDelete(true)}
          size="tiny"
          title={t('Delete')}
          lang={languageFor('Delete')}
          dir={directionFor('Delete')}
        />
        <Confirm
          cancelButton={{
            ...interfaceTextProps('Cancel'),
            content: localized('Cancel'),
          }}
          confirmButton={{
            ...interfaceTextProps('Delete'),
            content: localized('Delete'),
          }}
          content={localized('Delete wishlist item {search}?', { search: item.searchText })}
          header={localized('Confirm Delete')}
          onCancel={() => setConfirmDelete(false)}
          onConfirm={() => {
            setConfirmDelete(false);
            onDelete(item.id);
          }}
          open={confirmDelete}
          size="mini"
        />
      </Table.Cell>
    </Table.Row>
  );
};

export default WishlistItemRow;
