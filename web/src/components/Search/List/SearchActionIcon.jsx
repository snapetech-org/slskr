import { interfaceText, interfaceTextProps, useInterfaceLanguage } from "../../../lib/interfaceLocale";
import React from 'react';
import { isSearchComplete } from '../../../lib/searchState';
import { Button, Icon } from 'semantic-ui-react';

const SearchActionIcon = ({ loading, onRemove, onStop, search }) => {
  useInterfaceLanguage();
  const searchText = search.searchText ?? search.query ?? 'search';

  if (loading) {
    return (
      <Icon
        loading
        name="spinner"
        aria-label={interfaceText("Updating search: {searchText}", { "searchText": (searchText) })}
        role="status"
       {...interfaceTextProps("Updating search: {searchText}")}/>
    );
  }

  if (isSearchComplete(search)) {
    return (
      <Button
        aria-label={interfaceText("Remove search: {searchText}", { "searchText": (searchText) })}
        color="red"
        icon="trash alternate"
        onClick={() => onRemove()}
        size="small"
        title={interfaceText("Remove search: {searchText}", { "searchText": (searchText) })}
       {...interfaceTextProps("Remove search: {searchText}")}/>
    );
  }

  return (
    <Button
      aria-label={interfaceText("Stop search: {searchText}", { "searchText": (searchText) })}
      color="red"
      icon="stop circle"
      onClick={() => onStop()}
      size="small"
      title={interfaceText("Stop search: {searchText}", { "searchText": (searchText) })}
     {...interfaceTextProps("Stop search: {searchText}")}/>
  );
};

export default SearchActionIcon;
