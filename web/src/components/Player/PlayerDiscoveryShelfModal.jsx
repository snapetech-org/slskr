import LocalizedText from "../Shared/LocalizedText";
import { interfaceText, interfaceTextProps, useInterfaceLanguage } from "../../lib/interfaceLocale";
import {
  clearDiscoveryShelf,
  exportDiscoveryShelfPolicyReport,
  getDiscoveryShelf,
  getDiscoveryShelfActionLabel,
  getDiscoveryShelfPolicyPreview,
  getDiscoveryShelfSummary,
  removeDiscoveryShelfItem,
} from '../../lib/discoveryShelf';
import { copyToClipboard } from '../../lib/clipboard';
import { toDisplayError } from '../../lib/errors';
import { useMountedRef } from '../../lib/useMountedRef';
import { useEffect, useState } from 'react';
import {
  Button,
  Checkbox,
  Icon,
  Input,
  Label,
  Message,
  Modal,
  Popup,
} from 'semantic-ui-react';

const PlayerDiscoveryShelfModal = ({ onClose, open }) => {
  useInterfaceLanguage();
  const [expiryDays, setExpiryDays] = useState(14);
  const [items, setItems] = useState(() => getDiscoveryShelf());
  const [message, setMessage] = useState('');
  const [requireConsensus, setRequireConsensus] = useState(true);
  const mountedRef = useMountedRef();
  const summary = getDiscoveryShelfSummary();
  const policyPreview = getDiscoveryShelfPolicyPreview({
    expiryDays,
    items,
    requireConsensus,
  });

  const refreshShelf = () => {
    setItems(getDiscoveryShelf());
  };

  useEffect(() => {
    if (open) {
      refreshShelf();
      setMessage('');
    }
  }, [open]);

  const previewAction = (item) => {
    setMessage(
      interfaceText("{action} prepared for {title}. No files were moved or deleted.", { action: interfaceText(getDiscoveryShelfActionLabel(item.action)), title: item.title }),
    );
  };

  const removeItem = (key) => {
    removeDiscoveryShelfItem(key);
    refreshShelf();
  };

  const clearShelf = () => {
    clearDiscoveryShelf();
    refreshShelf();
    setMessage(interfaceText("Discovery shelf cleared from this browser."));
  };

  const copyPolicyReport = async () => {
    const report = exportDiscoveryShelfPolicyReport({
      expiryDays,
      items,
      requireConsensus,
    });

    try {
      const copied = await copyToClipboard(report);
      if (!mountedRef.current) return;
      setMessage(
        copied
          ? `Policy report copied for ${items.length} shelf items.`
          : interfaceText("Policy report prepared for {length} shelf items; clipboard is unavailable.", { length: items.length }),
      );
    } catch (error) {
      if (mountedRef.current) {
        setMessage(toDisplayError(error, 'Unable to copy policy report.'));
      }
    }
  };

  return (
    <Modal
      className="player-browser-modal player-discovery-shelf-modal"
      onClose={onClose}
      open={open}
      size="small"
    >
      <Modal.Header><LocalizedText source={"Discovery Shelf"} /></Modal.Header>
      <Modal.Content>
        <div className="player-shelf-summary" data-testid="player-shelf-summary">
          <div>
            <strong>{summary.total}</strong>
            <span><LocalizedText source={"local review items"} /></span>
          </div>
          <div>
            <strong>{summary['promote-preview']}</strong>
            <span><LocalizedText source={"promote previews"} /></span>
          </div>
          <div>
            <strong>{summary['archive-preview']}</strong>
            <span><LocalizedText source={"archive previews"} /></span>
          </div>
          <div>
            <strong>{summary['expiry-watch']}</strong>
            <span><LocalizedText source={"expiry watch"} /></span>
          </div>
        </div>
        {message ? (
          <Message compact size="mini">
            {message}
          </Message>
        ) : null}
        <section className="player-shelf-policy">
          <div className="player-panel-title"><LocalizedText source={"Policy Preview"} /></div>
          <div className="player-shelf-policy-controls">
            <label htmlFor="player-shelf-expiry-days"><LocalizedText source={"Expire unrated after"} /></label>
            <Input
              aria-label={interfaceText("Discovery shelf expiry days")}
              data-testid="player-shelf-expiry-days"
              id="player-shelf-expiry-days"
              min="1"
              onChange={(event) => setExpiryDays(event.target.value)}
              size="mini"
              type="number"
              value={expiryDays}
             {...interfaceTextProps("Discovery shelf expiry days")}/>
            <Popup
              content={interfaceText("Require shared-library consensus before any destructive archive or expiry action can be applied later.")}
              trigger={
                <Checkbox
                  checked={requireConsensus}
                  data-testid="player-shelf-require-consensus"
                  label={interfaceText("Consensus for destructive actions")}
                  onChange={(_, data) => setRequireConsensus(Boolean(data.checked))}
                  toggle
                 {...interfaceTextProps("Consensus for destructive actions")}/>
              }
             {...interfaceTextProps("Require shared-library consensus before any destructive archive or expiry action can be applied later.")}/>
          </div>
          <div className="player-shelf-policy-preview" data-testid="player-shelf-policy-preview">
            <span>{policyPreview.promote} <LocalizedText source={"promote"} /></span>
            <span>{policyPreview.archive} <LocalizedText source={"archive"} /></span>
            <span>{policyPreview.expire} <LocalizedText source={"expire"} /></span>
            <span>{policyPreview.review} <LocalizedText source={"review"} /></span>
            <span>{policyPreview.blockedByConsensus} <LocalizedText source={"consensus gated"} /></span>
          </div>
          <Popup
            content={interfaceText("Copy a text report of the current shelf policy preview for review. This does not apply any action.")}
            trigger={
              <Button
                data-testid="player-shelf-copy-policy-report"
                disabled={items.length === 0}
                onClick={copyPolicyReport}
                size="mini"
                type="button"
              >
                <Icon name="copy" />
                <LocalizedText source={"Copy Report"} /></Button>
            }
           {...interfaceTextProps("Copy a text report of the current shelf policy preview for review. This does not apply any action.")}/>
        </section>
        <div className="player-shelf-list">
          {items.length > 0 ? items.map((item) => (
            <div
              className="player-shelf-row"
              data-testid={`player-shelf-row-${item.key}`}
              key={item.key}
            >
              <div className="player-shelf-rating">{item.rating || '-'}</div>
              <div className="player-shelf-track">
                <strong>{item.title}</strong>
                <span>
                  {[item.artist, item.album].filter(Boolean).join(' - ') || 'Local discovery item'}
                </span>
              </div>
              <Label size="mini">
                {interfaceText(getDiscoveryShelfActionLabel(item.action))}
              </Label>
              <Popup
                content={interfaceText("Preview the shelf action. This does not move, delete, share, download, or publish anything.")}
                trigger={
                  <Button
                    data-testid={`player-shelf-preview-${item.key}`}
                    icon
                    onClick={() => previewAction(item)}
                    size="mini"
                    type="button"
                  >
                    <Icon name="eye" />
                  </Button>
                }
               {...interfaceTextProps("Preview the shelf action. This does not move, delete, share, download, or publish anything.")}/>
              <Popup
                content={interfaceText("Remove this local review item from the browser-only shelf.")}
                trigger={
                  <Button
                    data-testid={`player-shelf-remove-${item.key}`}
                    icon
                    onClick={() => removeItem(item.key)}
                    size="mini"
                    type="button"
                  >
                    <Icon name="trash alternate outline" />
                  </Button>
                }
               {...interfaceTextProps("Remove this local review item from the browser-only shelf.")}/>
            </div>
          )) : (
            <div className="player-queue-manager-empty">
              <LocalizedText source={"Rate tracks in the player to build a local discovery review shelf."} /></div>
          )}
        </div>
      </Modal.Content>
      <Modal.Actions>
        <Popup
          content={interfaceText("Clear browser-local discovery shelf review items. This does not affect files or ratings.")}
          trigger={
            <Button
              data-testid="player-clear-discovery-shelf"
              disabled={items.length === 0}
              onClick={clearShelf}
              type="button"
            >
              <Icon name="trash" />
              <LocalizedText source={"Clear Shelf"} /></Button>
          }
         {...interfaceTextProps("Clear browser-local discovery shelf review items. This does not affect files or ratings.")}/>
        <Popup
          content={interfaceText("Close the local discovery shelf.")}
          trigger={
            <Button
              data-testid="player-close-discovery-shelf"
              onClick={onClose}
              primary
              type="button"
            >
              <Icon name="check" />
              <LocalizedText source={"Done"} /></Button>
          }
         {...interfaceTextProps("Close the local discovery shelf.")}/>
      </Modal.Actions>
    </Modal>
  );
};

export default PlayerDiscoveryShelfModal;
