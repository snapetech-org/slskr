import LocalizedText from "../Shared/LocalizedText";
import { interfaceText, interfaceTextProps, useInterfaceLanguage } from "../../lib/interfaceLocale";
import React from 'react';
import { Button, Form, Icon, Message, Modal } from 'semantic-ui-react';

const BatchPrivateMessageModal = ({ actions, state }) => {
  useInterfaceLanguage();
  const { batchMessage, batchModalOpen, batchSending, batchUsernames } = state;
  const { sendBatchMessage, setBatchMessage, setBatchModalOpen, setBatchUsernames } = actions;

  return (
          <Modal
            onClose={() => setBatchModalOpen(false)}
            open={batchModalOpen}
            size="small"
          >
            <Modal.Header><LocalizedText source={"Batch Private Message"} /></Modal.Header>
            <Modal.Content>
              <Message info>
                <LocalizedText source={"Sends through Soulseek's multi-recipient private-message command and stores one local conversation per recipient."} /></Message>
              <Form>
                <Form.TextArea
                  aria-label={interfaceText("Batch private-message recipients")}
                  label={interfaceText("Recipients")}
                  onChange={(event) => setBatchUsernames(event.target.value)}
                  placeholder={interfaceText("alice, bob, carol")}
                  value={batchUsernames}
                 {...interfaceTextProps("Batch private-message recipients")}/>
                <Form.TextArea
                  aria-label={interfaceText("Batch private-message body")}
                  label={interfaceText("Message")}
                  onChange={(event) => setBatchMessage(event.target.value)}
                  placeholder={interfaceText("Message")}
                  value={batchMessage}
                 {...interfaceTextProps("Batch private-message body")}/>
              </Form>
            </Modal.Content>
            <Modal.Actions>
              <Button onClick={() => setBatchModalOpen(false)}>
                <LocalizedText source={"Cancel"} /></Button>
              <Button
                disabled={
                  batchSending ||
                  !batchMessage.trim() ||
                  !batchUsernames.trim()
                }
                loading={batchSending}
                onClick={sendBatchMessage}
                primary
              >
                <Icon name="send" />
                <LocalizedText source={"Send"} /></Button>
            </Modal.Actions>
          </Modal>
  );
};

export default BatchPrivateMessageModal;
