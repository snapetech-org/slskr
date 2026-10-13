import LocalizedText from "../Shared/LocalizedText";
import { interfaceText, interfaceTextProps, useInterfaceLanguage } from "../../lib/interfaceLocale";
import * as searches from '../../lib/searches';
import * as wishlistAPI from '../../lib/wishlist';
import {
  buildSimilarQueueCandidates,
  getSimilarQueueSearchQueries,
} from '../../lib/playerAutoQueue';
import { useMountedRef } from '../../lib/useMountedRef';
import { useEffect, useRef, useState } from 'react';
import {
  Button,
  Icon,
  Message,
  Modal,
  Popup,
} from 'semantic-ui-react';

const getTrackLabel = (item) =>
  item?.title || item?.fileName || item?.contentId || 'Untitled track';

const PlayerQueueModal = ({
  current,
  history,
  onClearQueue,
  onAutoQueueSimilar,
  onClose,
  onNext,
  onPrevious,
  onRemove,
  open,
  queue,
}) => {
  useInterfaceLanguage();
  const upcoming = queue.slice(1);
  const [handoffStatus, setHandoffStatus] = useState('');
  const [searchingSimilar, setSearchingSimilar] = useState(false);
  const [savingSimilarWishlist, setSavingSimilarWishlist] = useState(false);
  const mountedRef = useMountedRef();
  const openRef = useRef(open);
  const actionRequestIdRef = useRef(0);
  const actionInFlightRef = useRef(false);

  useEffect(() => {
    openRef.current = open;
    if (!open) {
      actionRequestIdRef.current += 1;
      setSearchingSimilar(false);
      setSavingSimilarWishlist(false);
    }
  }, [open]);
  const similarCandidates = buildSimilarQueueCandidates({
    current,
    history,
    queue,
  });

  const startSimilarSearches = async () => {
    if (
      !mountedRef.current ||
      !openRef.current ||
      actionInFlightRef.current
    ) {
      return;
    }
    const requestId = ++actionRequestIdRef.current;
    const isCurrentRequest = () =>
      mountedRef.current && openRef.current && actionRequestIdRef.current === requestId;
    const queries = getSimilarQueueSearchQueries(similarCandidates, { limit: 3 });
    if (queries.length === 0) {
      setHandoffStatus(interfaceText('No similar queue candidates are ready to search.'));
      return;
    }

    actionInFlightRef.current = true;
    try {
      setSearchingSimilar(true);
      const count = await searches.createBatch({ queries });
      if (!isCurrentRequest()) return;
      setHandoffStatus(interfaceText('Similar-track searches started: {count}.', { count }));
    } catch {
      if (!isCurrentRequest()) return;
      setHandoffStatus(interfaceText('Unable to start similar-track searches.'));
    } finally {
      actionInFlightRef.current = false;
      if (isCurrentRequest()) setSearchingSimilar(false);
    }
  };

  const addSimilarWishlist = async () => {
    if (
      !mountedRef.current ||
      !openRef.current ||
      actionInFlightRef.current
    ) {
      return;
    }
    const requestId = ++actionRequestIdRef.current;
    const isCurrentRequest = () =>
      mountedRef.current && openRef.current && actionRequestIdRef.current === requestId;
    const queries = getSimilarQueueSearchQueries(similarCandidates, { limit: 5 });
    if (queries.length === 0) {
      setHandoffStatus(interfaceText('No similar queue candidates are ready for Wishlist.'));
      return;
    }

    actionInFlightRef.current = true;
    try {
      setSavingSimilarWishlist(true);
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
      setHandoffStatus(interfaceText('Similar-track Wishlist seeds added: {count}.', { count: queries.length }));
    } catch {
      if (!isCurrentRequest()) return;
      setHandoffStatus(interfaceText('Unable to add similar-track seeds to Wishlist.'));
    } finally {
      actionInFlightRef.current = false;
      if (isCurrentRequest()) setSavingSimilarWishlist(false);
    }
  };

  return (
    <Modal
      className="player-browser-modal player-queue-modal"
      onClose={onClose}
      open={open}
      size="small"
    >
      <Modal.Header><LocalizedText source={"Playback Queue"} /></Modal.Header>
      <Modal.Content>
        <div className="player-queue-manager">
          <section>
            <div className="player-panel-title"><LocalizedText source={"Now Playing"} /></div>
            <div className="player-queue-manager-row player-queue-manager-current">
              <Icon name="play circle outline" />
              <div>
                <strong>{getTrackLabel(current)}</strong>
                <span>{current?.artist || 'No active playback'}</span>
              </div>
            </div>
          </section>
          <section>
            <div className="player-queue-manager-heading">
              <div className="player-panel-title"><LocalizedText source={"Upcoming"} /></div>
              <div className="player-queue-manager-actions">
                <Popup
                  content={interfaceText("Add similar recent session tracks to the upcoming queue. This only uses tracks already known to this browser session.")}
                  trigger={
                    <Button
                      data-testid="player-auto-queue-similar"
                      disabled={similarCandidates.length === 0}
                      onClick={() =>
                        onAutoQueueSimilar(
                          similarCandidates.map((candidate) => candidate.item),
                        )
                      }
                      size="mini"
                      type="button"
                    >
                      <Icon name="magic" />
                      <LocalizedText source={"Auto-fill Similar"} /></Button>
                  }
                 {...interfaceTextProps("Add similar recent session tracks to the upcoming queue. This only uses tracks already known to this browser session.")}/>
                <Popup
                  content={interfaceText("Start up to three searches from similar recent session tracks. This starts search jobs only.")}
                  trigger={
                    <Button
              data-testid="player-search-similar-candidates"
              disabled={similarCandidates.length === 0 || savingSimilarWishlist || searchingSimilar}
                      loading={searchingSimilar}
                      onClick={startSimilarSearches}
                      size="mini"
                      type="button"
                    >
                      <Icon name="search" />
                      <LocalizedText source={"Search Similar"} /></Button>
                  }
                 {...interfaceTextProps("Start up to three searches from similar recent session tracks. This starts search jobs only.")}/>
                <Popup
                  content={interfaceText("Add similar recent session tracks to Wishlist as manual requests with auto-download off.")}
                  trigger={
                    <Button
              data-testid="player-wishlist-similar-candidates"
              disabled={similarCandidates.length === 0 || savingSimilarWishlist || searchingSimilar}
                      loading={savingSimilarWishlist}
                      onClick={addSimilarWishlist}
                      size="mini"
                      type="button"
                    >
                      <Icon name="heart" />
                      <LocalizedText source={"Wishlist Similar"} /></Button>
                  }
                 {...interfaceTextProps("Add similar recent session tracks to Wishlist as manual requests with auto-download off.")}/>
                <Popup
                  content={interfaceText("Remove every upcoming item while keeping the current track playing.")}
                  trigger={
                    <Button
                      data-testid="player-clear-upcoming"
                      disabled={upcoming.length === 0}
                      onClick={onClearQueue}
                      size="mini"
                      type="button"
                    >
                      <Icon name="trash alternate outline" />
                      <LocalizedText source={"Clear Upcoming"} /></Button>
                  }
                 {...interfaceTextProps("Remove every upcoming item while keeping the current track playing.")}/>
              </div>
            </div>
            {upcoming.length > 0 ? (
              <div className="player-queue-manager-list">
                {upcoming.map((item, index) => (
                  <div
                    className="player-queue-manager-row"
                    data-testid={`player-queue-row-${item.contentId}`}
                    key={`${item.contentId}-${index}`}
                  >
                    <span className="player-queue-manager-index">{index + 1}</span>
                    <div>
                      <strong>{getTrackLabel(item)}</strong>
                      <span>{item.artist || item.album || item.contentId}</span>
                    </div>
                    <Popup
                      content={interfaceText("Remove this upcoming item from the local playback queue.")}
                      trigger={
                        <Button
                          aria-label={`Remove ${getTrackLabel(item)} from queue`}
                          data-testid={`player-remove-queue-${item.contentId}`}
                          icon
                          onClick={() => onRemove(item.contentId)}
                          size="mini"
                          type="button"
                        >
                          <Icon name="close" />
                        </Button>
                      }
                     {...interfaceTextProps("Remove this upcoming item from the local playback queue.")}/>
                  </div>
                ))}
              </div>
            ) : (
              <div className="player-queue-manager-empty">
                <LocalizedText source={"No upcoming tracks."} /></div>
            )}
          </section>
          {handoffStatus ? (
            <Message compact size="mini">
              {handoffStatus}
            </Message>
          ) : null}
          <section>
            <div className="player-panel-title"><LocalizedText source={"Recent"} /></div>
            {history.length > 0 ? (
              <div className="player-queue-manager-list">
                {history.slice(0, 5).map((item, index) => (
                  <div
                    className="player-queue-manager-row"
                    key={`${item.contentId}-${index}`}
                  >
                    <Icon name="history" />
                    <div>
                      <strong>{getTrackLabel(item)}</strong>
                      <span>{item.artist || item.album || item.contentId}</span>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="player-queue-manager-empty">
                <LocalizedText source={"No recent tracks in this session."} /></div>
            )}
          </section>
        </div>
      </Modal.Content>
      <Modal.Actions>
        <Popup
          content={interfaceText("Jump back to the previous session track, or restart the current track if there is no history.")}
          trigger={
            <Button
              data-testid="player-queue-previous"
              disabled={!current}
              onClick={onPrevious}
              type="button"
            >
              <Icon name="step backward" />
              <LocalizedText source={"Previous"} /></Button>
          }
         {...interfaceTextProps("Jump back to the previous session track, or restart the current track if there is no history.")}/>
        <Popup
          content={interfaceText("Advance to the next queued track.")}
          trigger={
            <Button
              data-testid="player-queue-next"
              disabled={queue.length < 2}
              onClick={onNext}
              type="button"
            >
              <Icon name="step forward" />
              <LocalizedText source={"Next"} /></Button>
          }
         {...interfaceTextProps("Advance to the next queued track.")}/>
        <Popup
          content={interfaceText("Close the queue manager.")}
          trigger={
            <Button
              data-testid="player-queue-close"
              onClick={onClose}
              primary
              type="button"
            >
              <Icon name="check" />
              <LocalizedText source={"Done"} /></Button>
          }
         {...interfaceTextProps("Close the queue manager.")}/>
      </Modal.Actions>
    </Modal>
  );
};

export default PlayerQueueModal;
