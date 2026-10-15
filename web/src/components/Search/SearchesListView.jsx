import LocalizedText from "../Shared/LocalizedText";
import { interfaceText, interfaceTextAttributes, interfaceTextProps, useInterfaceLanguage } from "../../lib/interfaceLocale";
import React, { useState } from 'react';
import { getLocalStorageItem, setLocalStorageItem } from '../../lib/storage';
import PlaceholderSegment from '../Shared/PlaceholderSegment';
import AlbumCompletionPanel from './AlbumCompletionPanel';
import ArtistReleaseRadarPanel from './ArtistReleaseRadarPanel';
import DiscographyCoveragePanel from './DiscographyCoveragePanel';
import DiscoveryGraphAtlasPanel from './DiscoveryGraphAtlasPanel';
import FederatedTasteRecommendationsPanel from './FederatedTasteRecommendationsPanel';
import SearchList from './List/SearchList';
import MusicBrainzLookup from './MusicBrainzLookup';
import SongIDPanel from './SongIDPanel';
import SoulseekDiscoveryPanel from './SoulseekDiscoveryPanel';
import {
  Button,
  Checkbox,
  Dropdown,
  Header,
  Icon,
  Input,
  Message,
  Popup,
  Segment,
} from 'semantic-ui-react';

const CollapsibleSection = ({
  children,
  defaultOpen = true,
  storageKey,
  title,
}) => {
  useInterfaceLanguage();
  const [open, setOpen] = useState(() => {
    if (!storageKey) {
      return defaultOpen;
    }

    const stored = getLocalStorageItem(storageKey);
    if (stored === null) {
      return defaultOpen;
    }

    return stored === 'open';
  });

  const toggleOpen = () => {
    setOpen((current) => {
      const next = !current;

      if (storageKey) {
        setLocalStorageItem(storageKey, next ? 'open' : 'closed');
      }

      return next;
    });
  };

  return (
    <Segment raised>
      <div
        style={{
          alignItems: 'center',
          display: 'flex',
          justifyContent: 'space-between',
          marginBottom: open ? '1em' : 0,
        }}
      >
        <Header
          as="h4"
          style={{ margin: 0 }}
        >
          {title}
        </Header>
        <Popup
          content={
            open
              ? interfaceText('Collapse the {title} panel to free up room on the page.', { title: title.toLowerCase() })
              : interfaceText('Expand the {title} panel to inspect its contents.', { title: title.toLowerCase() })
          }
          position="top center"
          trigger={
            <Button
              {...interfaceTextAttributes(open ? 'Collapse {title}' : 'Expand {title}', { title })}
              icon
              onClick={toggleOpen}
              size="mini"
            >
              <Icon name={open ? 'angle up' : 'angle down'} />
            </Button>
          }
        />
      </div>
      {open ? children : null}
    </Segment>
  );
};

const SearchesListView = ({ actions, inputRef, state }) => {
  useInterfaceLanguage();
  const {
    acquisitionProfile,
    acquisitionProfileOptions,
    connecting,
    creating,
    error,
    hasSearchData,
    initialSearchesLoaded,
    normalizedServer,
    providerPod,
    providerScene,
    removingAll,
    runtimeProfile,
    scenePodBridgeEnabled,
    searches,
  } = state;
  const {
    create,
    remove,
    removeAll,
    setProviderPod,
    setProviderScene,
    stop,
    updateAcquisitionProfile,
  } = actions;
  const connectionNotice = connecting && hasSearchData ? (
    <Message info size="small">
      <Icon loading name="circle notched" />
      <LocalizedText source={"Connecting to live search updates. Your loaded searches are available below."} /></Message>
  ) : null;

  if (runtimeProfile === 'legacy') {
    return (
      <>
        {connectionNotice}
        <Segment className="search-segment">
          <div className="search-segment-icon">
            <Icon
              name="search"
              size="big"
            />
          </div>
          <Input
            action={
              <>
                <Button
                  disabled={creating || !normalizedServer.isConnected}
                  icon="plus"
                  onClick={create}
                />
                <Button
                  disabled={creating || !normalizedServer.isConnected}
                  icon="search"
                  onClick={() => create({ navigate: true })}
                />
              </>
            }
            className="search-input"
            disabled={creating || !normalizedServer.isConnected}
            input={
              <input
                data-lpignore="true"
                placeholder={interfaceText("Connect to server to perform a search")}
                type="search"
               {...interfaceTextProps("Connect to server to perform a search")}/>
            }
            loading={creating}
            onKeyUp={(keyUpEvent) =>
              keyUpEvent.key === 'Enter' ? create() : ''
            }
            placeholder={interfaceText("Search phrase")}
            ref={inputRef}
            size="big"
           {...interfaceTextProps("Search phrase")}/>
        </Segment>
        {Object.keys(searches).length === 0 ? (
          <PlaceholderSegment
            caption="No searches to display"
            icon="search"
          />
        ) : (
          <SearchList
            connecting={connecting && !initialSearchesLoaded}
            error={hasSearchData ? undefined : error}
            onRemove={remove}
            onStop={stop}
            searches={searches}
          />
        )}
      </>
    );
  }

  return (
    <>
      {connectionNotice}
      <CollapsibleSection
        storageKey="slskr.search.section.search"
        title={interfaceText("Search")}
       {...interfaceTextProps("Search")}>
        <Segment className="search-segment">
          <div className="search-segment-icon">
            <Icon
              name="search"
              size="big"
            />
          </div>
          <Input
            action={
              <>
                <Popup
                  content={interfaceText("Queue this search without leaving the search page.")}
                  position="top center"
                  trigger={
                    <Button
                      aria-label={interfaceText("Queue search")}
                      disabled={creating || !normalizedServer.isConnected}
                      icon="plus"
                      onClick={create}
                     {...interfaceTextProps("Queue search")}/>
                  }
                 {...interfaceTextProps("Queue this search without leaving the search page.")}/>
                <Popup
                  content={interfaceText("Start this search and open its detailed results immediately.")}
                  position="top center"
                  trigger={
                    <Button
                      aria-label={interfaceText("Search and open results")}
                      disabled={creating || !normalizedServer.isConnected}
                      icon="search"
                      onClick={() => create({ navigate: true })}
                     {...interfaceTextProps("Search and open results")}/>
                  }
                 {...interfaceTextProps("Start this search and open its detailed results immediately.")}/>
              </>
            }
            className="search-input"
            disabled={creating || !normalizedServer.isConnected}
            input={
              <input
                data-lpignore="true"
                data-testid="search-input"
                placeholder={
                  normalizedServer.isConnected
                    ? 'Search phrase'
                    : 'Connect to server to perform a search'
                }
                type="search"
              />
            }
            loading={creating}
            onKeyUp={(keyUpEvent) => (keyUpEvent.key === 'Enter' ? create() : '')}
            placeholder={interfaceText("Search phrase")}
            ref={inputRef}
            size="big"
           {...interfaceTextProps("Search phrase")}/>
          {scenePodBridgeEnabled && (
            <div
              style={{
                background: 'rgba(0,0,0,0.05)',
                borderRadius: '4px',
                marginTop: '0.75em',
                padding: '0.75em',
              }}
            >
              <div
                style={{
                  alignItems: 'center',
                  display: 'flex',
                  flexWrap: 'wrap',
                  gap: '1em',
                }}
              >
                <span style={{ fontSize: '0.95em', fontWeight: 'bold' }}>
                  <LocalizedText source={"Search Sources:"} /></span>
                <Checkbox
                  checked={providerPod}
                  label={
                    <label>
                      <Icon
                        name="sitemap"
                        style={{ marginRight: '0.25em' }}
                      />
                      <LocalizedText source={"Pod/Mesh"} />
                    </label>
                  }
                  onChange={(e, { checked }) => setProviderPod(checked)}
                  toggle
                />
                <Checkbox
                  checked={providerScene}
                  label={
                    <label>
                      <Icon
                        name="globe"
                        style={{ marginRight: '0.25em' }}
                      />
                      <LocalizedText source={"Soulseek Scene"} /></label>
                  }
                  onChange={(e, { checked }) => setProviderScene(checked)}
                  toggle
                />
                {!providerPod && !providerScene && (
                  <span
                    style={{
                      color: 'orange',
                      fontSize: '0.9em',
                      fontStyle: 'italic',
                    }}
                  >
                    <Icon name="warning" /> <LocalizedText source={"At least one source must be selected"} /></span>
                )}
              </div>
            </div>
          )}
          <div className="search-acquisition-profile-strip">
            <div className="search-acquisition-profile-label">
              <Icon name={acquisitionProfile.icon} />
              <LocalizedText source={"Acquisition Profile"} /></div>
            {runtimeProfile !== 'native' && (
              <Popup
                content={interfaceText("{label}: {description}", { "label": (acquisitionProfile.label), "description": (acquisitionProfile.description) })}
                position="top center"
                trigger={
                  <Dropdown
                    aria-label={interfaceText("Acquisition profile")}
                    className="search-acquisition-profile-dropdown"
                    data-testid="acquisition-profile-select"
                    onChange={updateAcquisitionProfile}
                    options={acquisitionProfileOptions}
                    selection
                    value={acquisitionProfile.id}
                   {...interfaceTextProps("Acquisition profile")}/>
                }
               {...interfaceTextProps("{label}: {description}")}/>
            )}
            <span className="search-acquisition-profile-summary">
              {acquisitionProfile.summary}
            </span>
          </div>
        </Segment>
      </CollapsibleSection>
      <CollapsibleSection
        defaultOpen
        storageKey="slskr.search.section.searchResults"
        title={interfaceText("Search Results")}
       {...interfaceTextProps("Search Results")}>
        {Object.keys(searches).length === 0 ? (
          <PlaceholderSegment
            caption="No searches to display"
            icon="search"
          />
        ) : (
          <SearchList
            connecting={connecting && !initialSearchesLoaded}
            error={hasSearchData ? undefined : error}
            onRemove={remove}
            onRemoveAll={removeAll}
            onStop={stop}
            removingAll={removingAll}
            searches={searches}
          />
        )}
      </CollapsibleSection>
      <CollapsibleSection
        defaultOpen={false}
        storageKey="slskr.search.section.songid"
        title={interfaceText("SongID")}
       {...interfaceTextProps("SongID")}>
        <SongIDPanel disabled={!normalizedServer.isConnected} />
      </CollapsibleSection>
      <CollapsibleSection
        defaultOpen={false}
        storageKey="slskr.search.section.musicbrainz"
        title={interfaceText("MusicBrainz Lookup")}
       {...interfaceTextProps("MusicBrainz Lookup")}>
        <MusicBrainzLookup disabled={!normalizedServer.isConnected} />
      </CollapsibleSection>
      <CollapsibleSection
        defaultOpen={false}
        storageKey="slskr.search.section.discographyCoverage"
        title={interfaceText("Discography Concierge")}
       {...interfaceTextProps("Discography Concierge")}>
        <DiscographyCoveragePanel disabled={!normalizedServer.isConnected} />
      </CollapsibleSection>
      <CollapsibleSection
        defaultOpen={false}
        storageKey="slskr.search.section.artistReleaseRadar"
        title={interfaceText("Artist Release Radar")}
       {...interfaceTextProps("Artist Release Radar")}>
        <ArtistReleaseRadarPanel disabled={!normalizedServer.isConnected} />
      </CollapsibleSection>
      <CollapsibleSection
        defaultOpen={false}
        storageKey="slskr.search.section.soulseekDiscovery"
        title={interfaceText("Soulseek Discovery")}
       {...interfaceTextProps("Soulseek Discovery")}>
        <SoulseekDiscoveryPanel
          disabled={!normalizedServer.isConnected}
          onSearch={(search) => create({ navigate: true, search })}
        />
      </CollapsibleSection>
      <CollapsibleSection
        defaultOpen={false}
        storageKey="slskr.search.section.federatedTaste"
        title={interfaceText("Federated Taste")}
       {...interfaceTextProps("Federated Taste")}>
        <FederatedTasteRecommendationsPanel disabled={!normalizedServer.isConnected} />
      </CollapsibleSection>
      <CollapsibleSection
        defaultOpen={false}
        storageKey="slskr.search.section.discoveryGraphAtlas"
        title={interfaceText("Discovery Graph Atlas")}
       {...interfaceTextProps("Discovery Graph Atlas")}>
        <DiscoveryGraphAtlasPanel disabled={!normalizedServer.isConnected} />
      </CollapsibleSection>
      <CollapsibleSection
        defaultOpen={false}
        storageKey="slskr.search.section.albumCompletion"
        title={interfaceText("Album Completion")}
       {...interfaceTextProps("Album Completion")}>
        <AlbumCompletionPanel disabled={!normalizedServer.isConnected} />
      </CollapsibleSection>
    </>
  );
};

export default SearchesListView;
