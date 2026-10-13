import LocalizedText from "../../Shared/LocalizedText";
import { interfaceText, interfaceTextProps, useInterfaceLanguage } from "../../../lib/interfaceLocale";
import ErrorSegment from '../../Shared/ErrorSegment';
import Switch from '../../Shared/Switch';
import { searchDateValue } from '../../../lib/searchState';
import SearchListRow from './SearchListRow';
import React from 'react';
import { Button, Card, Icon, Loader, Popup, Table } from 'semantic-ui-react';

const SearchList = ({
  connecting = false,
  error = undefined,
  onRemove = () => {},
  onRemoveAll = () => {},
  onStop = () => {},
  removingAll = false,
  searches = {},
}) => {
  useInterfaceLanguage();
  return (
    <Card
      className="search-list-card"
      raised
    >
      <Card.Content>
        <div className="search-list-header">
          <Popup
            content={interfaceText("Clear all completed searches")}
            position="left center"
            trigger={
              <Button
                color="red"
                compact
                disabled={removingAll || Object.keys(searches).length === 0}
                icon
                labelPosition="left"
                loading={removingAll}
                onClick={onRemoveAll}
                size="small"
              >
                <Icon name="trash" />
                <LocalizedText source={"Clear All"} /></Button>
            }
           {...interfaceTextProps("Clear all completed searches")}/>
        </div>
        <div className="search-list-wrapper">
          <Switch
            connecting={
              connecting && (
                <Loader
                  active
                  inline="centered"
                  size="small"
                />
              )
            }
            error={error && <ErrorSegment caption={error} />}
          >
            <Table
              className="unstackable"
              size="large"
            >
              <Table.Header>
                <Table.Row>
                  <Table.HeaderCell className="search-list-action">
                    <Icon name="info circle" />
                  </Table.HeaderCell>
                  <Table.HeaderCell className="search-list-phrase">
                    <LocalizedText source={"Search"} /></Table.HeaderCell>
                  <Table.HeaderCell className="search-list-files">
                    <LocalizedText source={"Files"} /></Table.HeaderCell>
                  <Table.HeaderCell className="search-list-locked">
                    <LocalizedText source={"Locked"} /></Table.HeaderCell>
                  <Table.HeaderCell className="search-list-responses">
                    <LocalizedText source={"Responses"} /></Table.HeaderCell>
                  <Table.HeaderCell className="search-list-started">
                    <LocalizedText source={"Ended"} /></Table.HeaderCell>
                  <Table.HeaderCell className="search-list-action" />
                </Table.Row>
              </Table.Header>
              <Table.Body>
                {Object.values(searches)
                  .filter(Boolean)
                  .sort(
                    (a, b) =>
                      searchDateValue(b.startedAt ?? b.created_at) -
                      searchDateValue(a.startedAt ?? a.created_at),
                  )
                  .map((search) => (
                    <SearchListRow
                      key={search.id}
                      onRemove={onRemove}
                      onStop={onStop}
                      search={search}
                    />
                  ))}
              </Table.Body>
            </Table>
          </Switch>
        </div>
      </Card.Content>
    </Card>
  );
};

export default SearchList;
