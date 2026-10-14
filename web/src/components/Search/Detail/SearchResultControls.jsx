import { interfaceText, interfaceTextProps, useInterfaceLanguage } from "../../../lib/interfaceLocale";
import React from 'react';
import { formatRegionalNumber, useRegionalFormat } from '../../../lib/util';

import SearchFilterModal from './SearchFilterModal';
import {
  Button,
  Checkbox,
  Dropdown,
  Header,
  Icon,
  Input,
  Label,
  List,
  Popup,
  Segment,
} from 'semantic-ui-react';

const sortDropdownOptions = [
  {
    key: 'smart',
    get text() { return interfaceText("⭐ Smart Ranking (Best Overall)"); },
    value: 'smart',
  },
  {
    key: 'uploadSpeed',
    get text() { return interfaceText("Upload Speed (Fastest to Slowest)"); },
    value: 'uploadSpeed',
  },
  {
    key: 'queueLength',
    get text() { return interfaceText("Queue Depth (Least to Most)"); },
    value: 'queueLength',
  },
  {
    key: 'fileCount',
    get text() { return interfaceText("File Count (Most to Least)"); },
    value: 'fileCount',
  },
];

const SearchResultControls = ({ actions, state }) => {
  useRegionalFormat();
  const { t, languageFor, directionFor } = useInterfaceLanguage();
  const localized = (source, parameters) => (
    <span lang={languageFor(source)} dir={directionFor(source)}>{t(source, parameters)}</span>
  );
  const {
    albumCandidates,
    blockedUsers,
    deduplicatedResults,
    foldDuplicateResults,
    foldResults,
    hasSavedDefault,
    hideBlockedUsers,
    hideLocked,
    hideNoFreeSlots,
    loaded,
    pageSize,
    resultFilters,
    resultSort,
    savedFilters,
    search,
  } = state;
  const {
    clearSavedDefault,
    deleteNamedFilter,
    focusAlbumCandidate,
    handleFoldDuplicateResultsChange,
    handlePageSizeChange,
    loadNamedFilter,
    saveAlbumCandidateRule,
    saveAsDefault,
    saveNamedFilter,
    setFoldResults,
    setHideBlockedUsers,
    setHideLocked,
    setHideNoFreeSlots,
    setResultFilters,
    setResultSort,
  } = actions;

  return (
    <>
        {loaded && (
          <Segment
            className="search-options"
            raised
          >
            <Dropdown
              aria-label={t('Sort search results')}
              lang={languageFor('Sort search results')}
              dir={directionFor('Sort search results')}
              button
              className="search-options-sort icon"
              floating
              icon="sort"
              labeled
              onChange={(_event, { value }) => setResultSort(value)}
              options={sortDropdownOptions.map((option) => ({ ...option, text: localized(option.text) }))}
              text={
                localized((sortDropdownOptions.find((o) => o.value === resultSort) ??
                  sortDropdownOptions[0]).text)
              }
            />
            <Dropdown
              aria-label={t('Results per page')}
              lang={languageFor('Results per page')}
              dir={directionFor('Results per page')}
              button
              className="search-options-pagesize"
              floating
              onChange={(_event, { value }) => handlePageSizeChange(value)}
              options={[
                { key: '10', text: localized('{count} per page', { count: formatRegionalNumber(10) }), value: 10 },
                { key: '25', text: localized('{count} per page', { count: formatRegionalNumber(25) }), value: 25 },
                { key: '50', text: localized('{count} per page', { count: formatRegionalNumber(50) }), value: 50 },
                { key: '100', text: localized('{count} per page', { count: formatRegionalNumber(100) }), value: 100 },
                { key: 'all', text: localized('Show All'), value: 999_999 },
              ]}
              style={{ marginLeft: '0.5em' }}
              text={pageSize >= 999_999 ? localized('Show All') : localized('{count} per page', { count: formatRegionalNumber(pageSize) })}
            />
            <div className="search-option-toggles">
              <Checkbox
                checked={hideLocked}
                className="search-options-hide-locked"
                label={localized('Hide Locked Results')}
                onChange={() => setHideLocked(!hideLocked)}
                toggle
              />
              <Checkbox
                checked={hideNoFreeSlots}
                className="search-options-hide-no-slots"
                label={localized('Hide Results with No Free Slots')}
                onChange={() => setHideNoFreeSlots(!hideNoFreeSlots)}
                toggle
              />
              <Checkbox
                checked={hideBlockedUsers}
                className="search-options-hide-blocked"
                label={localized('Hide Blocked Users ({count})', { count: formatRegionalNumber(blockedUsers.length) })}
                onChange={() => setHideBlockedUsers(!hideBlockedUsers)}
                toggle
              />
              <Checkbox
                checked={foldResults}
                className="search-options-fold-results"
                label={localized('Fold Results')}
                onChange={() => setFoldResults(!foldResults)}
                toggle
              />
              <Popup
                content={localized('Fold duplicate file candidates that appear from multiple providers or peers, keeping the highest-ranked visible result and showing the folded sources as metadata.')}
                position="top center"
                trigger={
                  <Checkbox
                    checked={foldDuplicateResults}
                    className="search-options-fold-duplicates"
                    label={deduplicatedResults.foldedCount > 0
                      ? localized('Fold Duplicates ({count})', { count: formatRegionalNumber(deduplicatedResults.foldedCount) })
                      : localized('Fold Duplicates')}
                    onChange={handleFoldDuplicateResultsChange}
                    toggle
                  />
                }
              />
            </div>
            <div
              className="search-wishlist-ignore-guidance"
              role="note"
            >
              <Icon name={search.wishlistItemId ? 'ban' : 'info circle'} />
              {search.wishlistItemId
                ? localized('Wishlist search: use “Ignore for Wishlist” below a result folder to hide that peer and folder from future runs of this wishlist item.')
                : localized('Folder ignores are available only for wishlist searches because each rule belongs to one wishlist item. Open a result from Wishlist history to use them.')}
            </div>
            <Input
              action={
                <Button.Group>
                  {savedFilters.length > 0 && (
                    <Dropdown
                      button
                      className="icon"
                      floating
                      icon="bookmark"
                      onChange={(_event, { value }) => loadNamedFilter(value)}
                      options={savedFilters.map((filter) => ({
                        key: filter.name,
                        text: filter.name,
                        value: filter.name,
                      }))}
                      aria-label={t('Load saved filter')}
                      lang={languageFor('Load saved filter')}
                      dir={directionFor('Load saved filter')}
                      title={t('Load saved filter')}
                    />
                  )}
                  {Boolean(resultFilters) && (
                    <Button
                      color="red"
                      icon="x"
                      onClick={() => setResultFilters('')}
                      aria-label={t('Clear current filter')}
                      lang={languageFor('Clear current filter')}
                      dir={directionFor('Clear current filter')}
                      title={t('Clear current filter')}
                    />
                  )}
                  {Boolean(resultFilters) && (
                    <Button
                      color="teal"
                      icon="bookmark"
                      onClick={saveNamedFilter}
                      aria-label={t('Save named filter')}
                      lang={languageFor('Save named filter')}
                      dir={directionFor('Save named filter')}
                      title={t('Save named filter')}
                    />
                  )}
                  {savedFilters.some((filter) => filter.value === resultFilters) && (
                    <Button
                      color="orange"
                      icon="minus circle"
                      onClick={deleteNamedFilter}
                      aria-label={t('Delete matching saved filter')}
                      lang={languageFor('Delete matching saved filter')}
                      dir={directionFor('Delete matching saved filter')}
                      title={t('Delete matching saved filter')}
                    />
                  )}
                  <Button
                    color="blue"
                    icon="save"
                    onClick={saveAsDefault}
                    aria-label={t('Save as default filter')}
                    lang={languageFor('Save as default filter')}
                    dir={directionFor('Save as default filter')}
                    title={t('Save as default filter')}
                  />
                  {hasSavedDefault && (
                    <Button
                      color="orange"
                      icon="trash"
                      onClick={clearSavedDefault}
                      aria-label={t('Clear saved default filter')}
                      lang={languageFor('Clear saved default filter')}
                      dir={directionFor('Clear saved default filter')}
                      title={t('Clear saved default filter')}
                    />
                  )}
                  <SearchFilterModal
                    filterString={resultFilters}
                    onChange={setResultFilters}
                    trigger={
                      <Button
                        icon
                        aria-label={t('Advanced Filters')}
                        lang={languageFor('Advanced Filters')}
                        dir={directionFor('Advanced Filters')}
                        title={t('Advanced Filters')}
                      >
                        <Icon name="sliders horizontal" />
                      </Button>
                    }
                  />
                </Button.Group>
              }
              className="search-filter"
              label={{ content: localized('Filter'), icon: 'filter' }}
              onChange={(_event, data) => setResultFilters(data.value)}
              placeholder={interfaceText("lackluster container -bothersome iscbr|isvbr islossless|islossy minbr:320 minfilesize:100mb maxfilesize:2gb minfilesinfolder:8 minlength:5000")}
              value={resultFilters}
             {...interfaceTextProps("lackluster container -bothersome iscbr|isvbr islossless|islossy minbr:320 minfilesize:100mb maxfilesize:2gb minfilesinfolder:8 minlength:5000")}/>
          </Segment>
        )}
        {loaded && albumCandidates.length > 0 && (
          <Segment
            className="search-album-picker-segment"
            raised
          >
            <Header as="h4" lang={languageFor('Album candidates')} dir={directionFor('Album candidates')}>
              {t('Album candidates')}
              <Label
                color="blue"
                size="mini"
              >
                {albumCandidates.length}
              </Label>
            </Header>
            <List
              className="search-album-candidate-list"
              divided
              relaxed
            >
              {albumCandidates.map((candidate) => (
                <List.Item
                  className="search-album-candidate"
                  key={candidate.key}
                >
                  <List.Content floated="right">
                    <Popup
                      content={localized('Save this visible album review as a browser-local rule preview for similar future searches. This does not alter download behavior or contact peers.')}
                      position="top center"
                      trigger={
                        <Button
                          aria-label={t('Save album rule for {album}', { album: candidate.albumTitle })}
                          lang={languageFor('Save album rule for {album}')}
                          dir={directionFor('Save album rule for {album}')}
                          icon="bookmark outline"
                          onClick={() => saveAlbumCandidateRule(candidate)}
                          size="mini"
                        />
                      }
                    />
                    <Popup
                      content={localized('Focus the current result filter on this album folder name without starting another search or download.')}
                      position="top center"
                      trigger={
                        <Button
                          aria-label={t('Focus album candidate {album}', { album: candidate.albumTitle })}
                          lang={languageFor('Focus album candidate {album}')}
                          dir={directionFor('Focus album candidate {album}')}
                          icon="filter"
                          onClick={() => focusAlbumCandidate(candidate)}
                          size="mini"
                        />
                      }
                    />
                  </List.Content>
                  <List.Content>
                    <List.Header>
                      {candidate.albumTitle}
                      <Label
                        color="purple"
                        size="tiny"
                      >
                        {candidate.score}/100
                      </Label>
                    </List.Header>
                    <List.Description>
                {t('{tracks} of {expected} visible tracks · {sources} sources · {percent}%', {
                  tracks: formatRegionalNumber(candidate.trackCount),
                  expected: formatRegionalNumber(candidate.expectedTrackCount),
                  sources: formatRegionalNumber(candidate.sourceCount),
                  percent: formatRegionalNumber(Math.round(candidate.completenessRatio * 100)),
                })}
                    </List.Description>
                    <div className="search-album-candidate-review">
                      <span>
                    {localized('Formats:')}{' '}
                        {candidate.formatMix
                          .map((item) => `${item.format} ${item.count}`)
                          .join(', ')}
                      </span>
                      {candidate.missingTrackNumbers.length > 0 && (
                        <span>
                    {localized('Missing:')}{' '}
                          {candidate.missingTrackNumbers.slice(0, 8).join(', ')}
                        </span>
                      )}
                      {candidate.durationVarianceSeconds > 0 && (
                        <span>
                    {t('Duration spread: {minutes} min', { minutes: formatRegionalNumber(Math.round(candidate.durationVarianceSeconds / 60)) })}
                        </span>
                      )}
                      {candidate.substitutionOptions.length > 0 && (
                        <span>
                    {localized('Substitutions:')}{' '}
                          {candidate.substitutionOptions
                            .map(
                              (option) =>
                          t('track {number} ({count} options)', {
                            number: formatRegionalNumber(option.trackNumber),
                            count: formatRegionalNumber(option.optionCount),
                          }),
                            )
                            .join(', ')}
                        </span>
                      )}
                    </div>
                    {candidate.substitutionOptions.length > 0 && (
                      <div className="search-album-candidate-substitutions">
                        {candidate.substitutionOptions.slice(0, 4).map((option) => (
                          <Popup
                          content={localized('Manual review options from {sources} in {formats}. This only describes visible alternatives; it does not select or download them.', {
                            sources: option.sources.join(', '),
                            formats: option.formats.join(', '),
                          })}
                            key={option.trackNumber}
                            position="top center"
                            trigger={
                              <Label
                                color="teal"
                                size="tiny"
                              >
                                <Icon name="exchange" />
                              {t('Track {number}: {count} options', {
                                number: formatRegionalNumber(option.trackNumber),
                                count: formatRegionalNumber(option.optionCount),
                              })}
                              </Label>
                            }
                          />
                        ))}
                      </div>
                    )}
                    <div className="search-album-candidate-labels">
                      {candidate.reasons.map((reason) => (
                        <Label
                          key={reason}
                          size="tiny"
                        >
                          {reason}
                        </Label>
                      ))}
                      {candidate.warnings.map((warning) => (
                        <Popup
                          content={localized('This is a local confidence warning from visible search result metadata only; it does not reject the candidate or contact peers.')}
                          key={warning}
                          position="top center"
                          trigger={
                            <Label
                              color="yellow"
                              size="tiny"
                            >
                              <Icon name="warning sign" />
                              {warning}
                            </Label>
                          }
                        />
                      ))}
                    </div>
                    <div className="search-album-candidate-paths">
                      {candidate.directories.join(' | ')}
                    </div>
                  </List.Content>
                </List.Item>
              ))}
            </List>
          </Segment>
        )}

    </>
  );
};

export default SearchResultControls;
