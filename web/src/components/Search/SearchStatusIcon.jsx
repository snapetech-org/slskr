import LocalizedText from '../Shared/LocalizedText';
import { getSearchStateKind } from '../../lib/searchState';
import React from 'react';
import { Icon, Popup } from 'semantic-ui-react';

const getIcon = ({ state, status, ...props }) => {
  switch (getSearchStateKind({ state, status })) {
    case 'active':
      if (
        ['none', 'queued', 'requested'].includes(
          String(state ?? status ?? '').trim().toLowerCase(),
        )
      ) {
        return (
          <Icon
            name="time"
            {...props}
          />
        );
      }
      return (
        <Icon
          color="green"
          loading
          name="circle notch"
          {...props}
        />
      );
    case 'completed':
      return (
        <Icon
          color="green"
          name="check"
          {...props}
        />
      );
    case 'cancelled':
      return (
        <Icon
          color="green"
          name="stop circle"
          {...props}
        />
      );
    case 'failed':
      return (
        <Icon
          color="red"
          name="x"
          {...props}
        />
      );
    default:
      return (
        <Icon
          color="yellow"
          name="question circle"
          {...props}
        />
      );
  }
};

const getSearchStatusLabel = ({ state, status }) => {
  const raw = status ?? state ?? 'Unknown';
  const normalized = String(state ?? status ?? '').trim().toLowerCase();
  switch (getSearchStateKind({ state, status })) {
    case 'active':
      return ['none', 'queued', 'requested'].includes(normalized) ? 'Queued' : 'In Progress';
    case 'completed': return 'Completed';
    case 'cancelled': return 'Cancelled';
    case 'failed': return 'Failed';
    default: return raw;
  }
};

const SearchStatusIcon = ({ state, status, ...props }) => (
  <Popup
    content={<LocalizedText source={getSearchStatusLabel({ state, status })} />}
    trigger={getIcon({ state, status, ...props })}
  />
);

export default SearchStatusIcon;
