import LocalizedText from "../Shared/LocalizedText";
import { interfaceText, interfaceTextProps, useInterfaceLanguage } from "../../lib/interfaceLocale";
import * as listenBrainz from '../../lib/listenBrainz';
import {
  clearListeningHistory,
  exportListeningHistoryCsv,
  exportListeningHistoryJson,
  getListeningRecommendationQueries,
  getListeningRecommendationSeeds,
  getListeningStats,
  importListeningHistory,
} from '../../lib/listeningHistory';
import * as searches from '../../lib/searches';
import * as wishlistAPI from '../../lib/wishlist';
import { copyToClipboard } from '../../lib/clipboard';
import { toDisplayError } from '../../lib/errors';
import { readFileTextBounded } from '../../lib/fileReaders';
import { useMountedRef } from '../../lib/useMountedRef';
import { useCallback, useEffect, useRef, useState } from 'react';
import {
  Button,
  Icon,
  Message,
  Modal,
  Popup,
  TextArea,
} from 'semantic-ui-react';

const LocalizedListeningSeedBasis = ({ source }) => {
  const match = source.match(/^(\d+) (older|local|tagged) plays$/);
  if (match) return <LocalizedText source={`{count} ${match[2]} plays`} values={{ count: match[1] }} />;
  return <LocalizedText source={source} />;
};

const PlayerStatsModal = ({ onClose, onOpenSearch, open }) => {
  useInterfaceLanguage();
  const fileInputRef = useRef(null);
  const [rangeDays, setRangeDays] = useState(30);
  const [importText, setImportText] = useState('');
  const [importStatus, setImportStatus] = useState(null);
  const [runningSeedSearches, setRunningSeedSearches] = useState(false);
  const [scrobblingRecent, setScrobblingRecent] = useState(false);
  const [savingSeedWishlist, setSavingSeedWishlist] = useState(false);
  const [stats, setStats] = useState(() =>
    getListeningStats({ rangeDays: 30 }),
  );
  const mountedRef = useMountedRef();
  const openRef = useRef(open);
  const actionRequestIdRef = useRef(0);
  const actionInFlightRef = useRef(false);

  useEffect(() => {
    openRef.current = open;
    if (!open) {
      actionRequestIdRef.current += 1;
      setRunningSeedSearches(false);
      setScrobblingRecent(false);
      setSavingSeedWishlist(false);
    }
  }, [open]);

  const isActive = () => mountedRef.current && openRef.current;
  const recommendationSeeds = getListeningRecommendationSeeds(stats);
  const refreshStats = useCallback((nextRangeDays = rangeDays) => {
    setStats(getListeningStats({ rangeDays: nextRangeDays }));
  }, [rangeDays]);

  useEffect(() => {
    if (open) refreshStats();
  }, [open, refreshStats]);

  const clearStats = () => {
    clearListeningHistory();
    setImportStatus(null);
    refreshStats();
  };

  const updateRange = (nextRangeDays) => {
    setRangeDays(nextRangeDays);
    refreshStats(nextRangeDays);
  };

  const importHistory = () => {
    const result = importListeningHistory(importText);
    setImportStatus(
      interfaceText('{imported} rows imported; {skipped} duplicates or incomplete rows skipped.', {
        imported: result.imported,
        skipped: result.skipped,
      }),
    );
    setImportText('');
    refreshStats();
  };

  const copyHistory = async (format) => {
    const content = format === 'csv'
      ? exportListeningHistoryCsv()
      : exportListeningHistoryJson();

    try {
      const copied = await copyToClipboard(content);
      if (!mountedRef.current) return;
      setImportStatus(
        interfaceText(
          copied
            ? 'Copied {format} export for {count} plays.'
            : 'Prepared {format} export for {count} plays; clipboard is unavailable.',
          { format: format.toUpperCase(), count: stats.history.length },
        ),
      );
    } catch (error) {
      if (mountedRef.current) {
        setImportStatus(toDisplayError(
          error,
          interfaceText('Unable to copy {format} export.', { format: format.toUpperCase() }),
        ));
      }
    }
  };

  const startSeedSearches = async () => {
    if (!isActive() || actionInFlightRef.current) return;
    const requestId = ++actionRequestIdRef.current;
    const isCurrentRequest = () =>
      isActive() && actionRequestIdRef.current === requestId;
    const queries = getListeningRecommendationQueries(stats, { limit: 3 });
    if (queries.length === 0) {
      setImportStatus(interfaceText('No listening seeds are ready to search.'));
      return;
    }

    actionInFlightRef.current = true;
    try {
      setRunningSeedSearches(true);
      const count = await searches.createBatch({ queries });
      if (!isCurrentRequest()) return;
      setImportStatus(interfaceText('Listening seed searches started: {count}.', { count }));
    } catch {
      if (!isCurrentRequest()) return;
      setImportStatus(interfaceText('Unable to start listening seed searches.'));
    } finally {
      actionInFlightRef.current = false;
      if (isCurrentRequest()) setRunningSeedSearches(false);
    }
  };

  const addSeedsToWishlist = async () => {
    if (!isActive() || actionInFlightRef.current) return;
    const requestId = ++actionRequestIdRef.current;
    const isCurrentRequest = () =>
      isActive() && actionRequestIdRef.current === requestId;
    const queries = getListeningRecommendationQueries(stats, { limit: 5 });
    if (queries.length === 0) {
      setImportStatus(interfaceText('No listening seeds are ready for Wishlist.'));
      return;
    }

    actionInFlightRef.current = true;
    try {
      setSavingSeedWishlist(true);
      await queries.reduce(
        (chain, searchText) =>
          chain.then(() =>
            wishlistAPI.create({
              autoDownload: false,
              enabled: true,
              filter: '',
              maxResults: 50,
              searchText,
            }),
          ),
        Promise.resolve(),
      );
      if (!isCurrentRequest()) return;
      setImportStatus(interfaceText('Listening seeds added to Wishlist for manual acquisition: {count}.', { count: queries.length }));
    } catch {
      if (!isCurrentRequest()) return;
      setImportStatus(interfaceText('Unable to add listening seeds to Wishlist.'));
    } finally {
      actionInFlightRef.current = false;
      if (isCurrentRequest()) setSavingSeedWishlist(false);
    }
  };

  const scrobbleRecentHistory = async () => {
    if (!isActive() || actionInFlightRef.current) return;
    const requestId = ++actionRequestIdRef.current;
    const isCurrentRequest = () =>
      isActive() && actionRequestIdRef.current === requestId;
    actionInFlightRef.current = true;
    try {
      setScrobblingRecent(true);
      const result = await listenBrainz.submitListeningHistory(stats.history, {
        limit: 10,
      });
      if (!isCurrentRequest()) return;
      setImportStatus(
        result.submitted > 0
          ? interfaceText('ListenBrainz listens submitted: {count}.', { count: result.submitted })
          : interfaceText('No ListenBrainz token or eligible recent listens are available.'),
      );
    } catch {
      if (!isCurrentRequest()) return;
      setImportStatus(interfaceText('Unable to submit recent listens to ListenBrainz.'));
    } finally {
      actionInFlightRef.current = false;
      if (isCurrentRequest()) setScrobblingRecent(false);
    }
  };

  const readImportFile = (event) => {
    const file = event.target.files?.[0];
    if (!file) return;

    const requestId = ++actionRequestIdRef.current;
    const isCurrentRequest = () =>
      isActive() && actionRequestIdRef.current === requestId;

    readFileTextBounded(file).then((content) => {
      if (!isCurrentRequest()) return;
      setImportText(content);
      setImportStatus(interfaceText('Loaded {fileName} for review.', { fileName: file.name }));
    }).catch((error) => {
      if (!isCurrentRequest()) return;
      setImportStatus(interfaceText('Could not read {fileName}: {message}', {
        fileName: file.name,
        message: toDisplayError(error),
      }));
    });
    event.target.value = '';
  };

  const renderList = (items, emptyText) => (
    items.length > 0 ? (
      <div className="player-stats-list">
        {items.map((item, index) => (
          <div className="player-stats-row" key={`${item.label || item.title}-${index}`}>
            <span>{index + 1}</span>
            <strong>{item.label || item.title}</strong>
            <em>{item.plays ? <LocalizedText source={"{plays} plays"} values={{ "plays": (item.plays) }} /> : item.artist || item.album || ''}</em>
          </div>
        ))}
      </div>
    ) : (
      <div className="player-queue-manager-empty">{emptyText}</div>
    )
  );

  return (
    <Modal
      className="player-browser-modal player-stats-modal"
      onClose={onClose}
      open={open}
      size="small"
    >
      <Modal.Header><LocalizedText source={"Listening Stats"} /></Modal.Header>
      <Modal.Content>
        <div className="player-stats-summary" data-testid="player-stats-summary">
          <Icon name="bar chart" />
          <div>
            <strong>{stats.totalPlays}</strong>
            <span>
              <LocalizedText source={"local plays recorded in this browser"} />{rangeDays ? <LocalizedText source={"over {rangeDays} days"} values={{ "rangeDays": (rangeDays) }} /> : <LocalizedText source={"overall"} />}
            </span>
          </div>
        </div>
        <div className="player-stats-ranges" role="group" aria-label={interfaceText("Listening stats range")} {...interfaceTextProps("Listening stats range")}>
          {[
            { label: interfaceText("7D"), value: 7 },
            { label: interfaceText("30D"), value: 30 },
            { label: interfaceText("90D"), value: 90 },
            { label: interfaceText("All"), value: null },
          ].map((range) => (
            <Button
              active={rangeDays === range.value}
              data-testid={`player-stats-range-${range.label}`}
              key={range.label}
              onClick={() => updateRange(range.value)}
              size="mini"
              type="button"
            >
              {range.label}
            </Button>
          ))}
        </div>
        <div className="player-stats-grid">
          <section>
            <div className="player-panel-title"><LocalizedText source={"Top Artists"} /></div>
            {renderList(stats.topArtists, 'No artist plays recorded yet.')}
          </section>
          <section>
            <div className="player-panel-title"><LocalizedText source={"Top Tracks"} /></div>
            {renderList(stats.topTracks, 'No track plays recorded yet.')}
          </section>
          <section>
            <div className="player-panel-title"><LocalizedText source={"Top Genres"} /></div>
            {renderList(stats.topGenres, 'No genre metadata recorded yet.')}
          </section>
          <section>
            <div className="player-panel-title"><LocalizedText source={"Recent"} /></div>
            {renderList(stats.recent, 'No recent plays recorded yet.')}
          </section>
          <section>
            <div className="player-panel-title"><LocalizedText source={"Forgotten Favorites"} /></div>
            {renderList(
              stats.forgottenFavorites,
              'No older repeat plays outside this range yet.',
            )}
          </section>
        </div>
        <section className="player-stats-recommendations">
          <div className="player-panel-title"><LocalizedText source={"Recommendation Seeds"} /></div>
          {recommendationSeeds.length > 0 ? (
            <>
              <div className="player-stats-seed-list">
                {recommendationSeeds.map((seed) => (
                  <div className="player-stats-seed-row" key={`${seed.type}-${seed.query}`}>
                    <div>
                      <strong>{seed.label}</strong>
                      <span><LocalizedText source={seed.type} /> - <LocalizedListeningSeedBasis source={seed.basis} /></span>
                    </div>
                    <Popup
                      content={interfaceText("Open this local listening seed as a normal Search page query. Network search starts only after you choose to search.")}
                      trigger={
                        <Button
                          aria-label={interfaceText("Search {label}", { "label": (seed.label) })}
                          data-testid={`player-stats-search-seed-${seed.query}`}
                          icon
                          onClick={() => onOpenSearch(seed.query)}
                          size="mini"
                          type="button"
                         {...interfaceTextProps("Search {label}")}>
                          <Icon name="search" />
                        </Button>
                      }
                     {...interfaceTextProps("Open this local listening seed as a normal Search page query. Network search starts only after you choose to search.")}/>
                  </div>
                ))}
              </div>
              <Popup
                content={interfaceText("Start up to three live searches from the strongest listening seeds. This only starts searches; it does not browse peers, queue downloads, or mutate files.")}
                trigger={
                  <Button
                    data-testid="player-stats-start-seed-searches"
                    disabled={
                      recommendationSeeds.length === 0 ||
                      runningSeedSearches ||
                      savingSeedWishlist ||
                      scrobblingRecent
                    }
                    loading={runningSeedSearches}
                    onClick={startSeedSearches}
                    size="mini"
                    type="button"
                  >
                    <Icon name="search" />
                    <LocalizedText source={"Start Searches"} /></Button>
                }
               {...interfaceTextProps("Start up to three live searches from the strongest listening seeds. This only starts searches; it does not browse peers, queue downloads, or mutate files.")}/>
              <Popup
                content={interfaceText("Add up to five listening seeds to Wishlist as enabled manual-acquisition requests. Auto-download stays off.")}
                trigger={
                  <Button
                    data-testid="player-stats-add-seeds-to-wishlist"
                    disabled={
                      recommendationSeeds.length === 0 ||
                      runningSeedSearches ||
                      savingSeedWishlist ||
                      scrobblingRecent
                    }
                    loading={savingSeedWishlist}
                    onClick={addSeedsToWishlist}
                    size="mini"
                    type="button"
                  >
                    <Icon name="heart" />
                    <LocalizedText source={"Add Wishlist"} /></Button>
                }
               {...interfaceTextProps("Add up to five listening seeds to Wishlist as enabled manual-acquisition requests. Auto-download stays off.")}/>
            </>
          ) : (
            <div className="player-queue-manager-empty">
              <LocalizedText source={"Play more tracks locally to build recommendation seeds."} /></div>
          )}
        </section>
        <section className="player-stats-import">
          <div className="player-panel-title"><LocalizedText source={"Media Server Import"} /></div>
          <TextArea
            aria-label={interfaceText("Paste exported media server play history")}
            data-testid="player-listening-history-import-text"
            onChange={(event) => setImportText(event.target.value)}
            placeholder={interfaceText("Paste Plex, Jellyfin, Navidrome, or generic CSV/JSON play history here for local import.")}
            rows={4}
            value={importText}
           {...interfaceTextProps("Paste exported media server play history")}/>
          {importStatus ? (
            <Message compact size="mini">
              {importStatus}
            </Message>
          ) : null}
          <div className="player-stats-import-actions">
            <input
              accept=".csv,.json,.txt"
              aria-label={interfaceText("Choose media server history file")}
              data-testid="player-listening-history-file"
              onChange={readImportFile}
              ref={fileInputRef}
              type="file"
             {...interfaceTextProps("Choose media server history file")}/>
            <Popup
              content={interfaceText("Choose a local CSV or JSON export from Plex, Jellyfin, Navidrome, or another media server. The file is read in this browser only.")}
              trigger={
                <Button
                  data-testid="player-listening-history-choose-file"
                  onClick={() => fileInputRef.current?.click()}
                  size="mini"
                  type="button"
                >
                  <Icon name="folder open" />
                  <LocalizedText source={"Choose File"} /></Button>
              }
             {...interfaceTextProps("Choose a local CSV or JSON export from Plex, Jellyfin, Navidrome, or another media server. The file is read in this browser only.")}/>
            <Popup
              content={interfaceText("Import the pasted or chosen play history into browser-local listening stats with duplicate suppression.")}
              trigger={
                <Button
                  data-testid="player-listening-history-import"
                  disabled={!importText.trim()}
                  onClick={importHistory}
                  primary
                  size="mini"
                  type="button"
                >
                  <Icon name="upload" />
                  <LocalizedText source={"Import"} /></Button>
              }
             {...interfaceTextProps("Import the pasted or chosen play history into browser-local listening stats with duplicate suppression.")}/>
            <Popup
              content={interfaceText("Copy the browser-local listening history as JSON for backup or review.")}
              trigger={
                <Button
                  data-testid="player-listening-history-export-json"
                  disabled={stats.history.length === 0}
                  onClick={() => copyHistory('json')}
                  size="mini"
                  type="button"
                >
                  <Icon name="copy" />
                  JSON
                </Button>
              }
             {...interfaceTextProps("Copy the browser-local listening history as JSON for backup or review.")}/>
            <Popup
              content={interfaceText("Copy the browser-local listening history as CSV for media-server or spreadsheet review.")}
              trigger={
                <Button
                  data-testid="player-listening-history-export-csv"
                  disabled={stats.history.length === 0}
                  onClick={() => copyHistory('csv')}
                  size="mini"
                  type="button"
                >
                  <Icon name="table" />
                  CSV
                </Button>
              }
             {...interfaceTextProps("Copy the browser-local listening history as CSV for media-server or spreadsheet review.")}/>
            <Popup
              content={interfaceText("Submit up to ten recent browser-local plays to ListenBrainz using the saved token. This does not search, browse peers, download, or mutate files.")}
              trigger={
                <Button
                  data-testid="player-listening-history-scrobble-recent"
                  disabled={
                    stats.history.length === 0 ||
                    runningSeedSearches ||
                    savingSeedWishlist ||
                    scrobblingRecent
                  }
                  loading={scrobblingRecent}
                  onClick={scrobbleRecentHistory}
                  size="mini"
                  type="button"
                >
                  <Icon name="send" />
                  <LocalizedText source={"Scrobble Recent"} /></Button>
              }
             {...interfaceTextProps("Submit up to ten recent browser-local plays to ListenBrainz using the saved token. This does not search, browse peers, download, or mutate files.")}/>
          </div>
        </section>
      </Modal.Content>
      <Modal.Actions>
        <Popup
          content={interfaceText("Clear only the browser-local listening history used for this stats view.")}
          trigger={
            <Button
              data-testid="player-clear-listening-history"
              disabled={stats.totalPlays === 0}
              onClick={clearStats}
              type="button"
            >
              <Icon name="trash alternate outline" />
              <LocalizedText source={"Clear Local History"} /></Button>
          }
         {...interfaceTextProps("Clear only the browser-local listening history used for this stats view.")}/>
        <Popup
          content={interfaceText("Close listening stats.")}
          trigger={
            <Button
              data-testid="player-close-listening-stats"
              onClick={onClose}
              primary
              type="button"
            >
              <Icon name="check" />
              <LocalizedText source={"Done"} /></Button>
          }
         {...interfaceTextProps("Close listening stats.")}/>
      </Modal.Actions>
    </Modal>
  );
};

export default PlayerStatsModal;
