import LocalizedText from "../Shared/LocalizedText";
import { interfaceText, interfaceTextProps, useInterfaceLanguage } from "../../lib/interfaceLocale";
import React from 'react';
import { Button, Dropdown, Form, Modal } from 'semantic-ui-react';

const CreateCollectionModal = ({ actions, state, typeOptions }) => {
  useInterfaceLanguage();
  const { creatingCollection, createModalOpen, newCollectionDescription, newCollectionTitle, newCollectionType } = state;
  const { onClose, onCreate, onDescriptionChange, onTitleChange, onTypeChange } = actions;

  return (
          <Modal
            onClose={onClose}
            open={createModalOpen}
          >
            <Modal.Header><LocalizedText source={"Create Collection"} /></Modal.Header>
            <Modal.Content>
              <Form>
                <Form.Field>
                  <label htmlFor="collection-type"><LocalizedText source={"Type"} /></label>
                  <Dropdown
                    data-testid="collections-type-select"
                    id="collection-type"
                    onChange={onTypeChange}
                    options={typeOptions}
                    selection
                    value={newCollectionType}
                  />
                </Form.Field>
                <Form.Input
                  data-testid="collections-title-input"
                  label={interfaceText("Title")}
                  onChange={onTitleChange}
                  placeholder={interfaceText("Enter collection title")}
                  value={newCollectionTitle}
                 {...interfaceTextProps("Title")}/>
                <Form.TextArea
                  label={interfaceText("Description")}
                  onChange={onDescriptionChange}
                  placeholder={interfaceText("Optional description")}
                  value={newCollectionDescription}
                 {...interfaceTextProps("Description")}/>
              </Form>
            </Modal.Content>
            <Modal.Actions>
              <Button
                onClick={onClose}
              >
                <LocalizedText source={"Cancel"} /></Button>
              <Button
                data-testid="collections-create-submit"
                disabled={!newCollectionTitle.trim() || creatingCollection}
                loading={creatingCollection}
                onClick={onCreate}
                primary
              >
                <LocalizedText source={"Create"} /></Button>
            </Modal.Actions>
          </Modal>
  );
};

export default CreateCollectionModal;
