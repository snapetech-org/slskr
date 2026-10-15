import LocalizedText from "../Shared/LocalizedText";
import { interfaceText, interfaceTextProps } from "../../lib/interfaceLocale";
import { formatSearchActionPreview } from '../../lib/searchActionPreview';
import { formatRegionalNumber, useRegionalFormat } from '../../lib/util';
import { Button, Label, List, Modal, Popup } from 'semantic-ui-react';

const DownloadActionPreviewModal = ({
  onClose,
  onCopy,
  open,
  preview,
  selectedSize,
}) => {
  useRegionalFormat();
  return (
    <Modal
      closeIcon
      onClose={onClose}
      open={open}
      size="small"
    >
      <Modal.Header><LocalizedText source={"Download action preview"} /></Modal.Header>
      <Modal.Content>
        <List relaxed>
          <List.Item>
            <List.Header><LocalizedText source={"Source"} /></List.Header>
            <List.Description>{preview.username || 'unknown'}</List.Description>
          </List.Item>
          <List.Item>
            <List.Header><LocalizedText source={"Providers"} /></List.Header>
            <List.Description>{preview.providerLabels.join(', ')}</List.Description>
          </List.Item>
          <List.Item>
            <List.Header><LocalizedText source={"Selected files"} /></List.Header>
            <List.Description>
              {formatRegionalNumber(preview.fileCount)}{' '}
              <LocalizedText source={preview.fileCount === 1 ? "file" : "files"} />, {selectedSize}
            </List.Description>
          </List.Item>
          {preview.candidateScore !== null && (
            <List.Item>
              <List.Header><LocalizedText source={"Candidate score"} /></List.Header>
              <List.Description>{formatRegionalNumber(preview.candidateScore)}/100</List.Description>
            </List.Item>
          )}
        </List>
        {preview.warnings.length > 0 && (
          <div className="search-action-preview-warnings">
            {preview.warnings.map((warning) => (
              <Label
                color="orange"
                key={warning}
                size="small"
              >
                {warning}
              </Label>
            ))}
          </div>
        )}
        <pre className="search-action-preview-text">
          {formatSearchActionPreview(preview)}
        </pre>
      </Modal.Content>
      <Modal.Actions>
        <Popup
          content={interfaceText("Copy this planned action summary so you can review or export it before downloading.")}
          position="top center"
          trigger={
            <Button
              icon="copy"
              onClick={onCopy}
            />
          }
         {...interfaceTextProps("Copy this planned action summary so you can review or export it before downloading.")}/>
        <Button onClick={onClose}>
          <LocalizedText source={"Close"} /></Button>
      </Modal.Actions>
    </Modal>
  );
};

export default DownloadActionPreviewModal;
