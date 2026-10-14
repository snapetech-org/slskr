import LocalizedText from "../Shared/LocalizedText";
import { interfaceText, interfaceTextProps, useInterfaceLanguage } from "../../lib/interfaceLocale";
import React from 'react';
import { Button, Dropdown, Form, Message, Modal } from 'semantic-ui-react';

const CollectionAddItemModal = ({ actions, state }) => {
  useInterfaceLanguage();
  const { addItemModalOpen, addingItem, itemSearchLoading, itemSearchQuery, itemSearchResults, selectedCollection } = state;
  const { onAddItem, onClose, onSearchInputChange, onSearchResultChange } = actions;

  return (
          <Modal
            onClose={onClose}
            open={addItemModalOpen}
          >
            <Modal.Header><LocalizedText source={"Add Item to"} />{" "}{selectedCollection?.title}</Modal.Header>
            <Modal.Content>
              <Form>
                <Form.Field>
                  <label htmlFor="collection-item-search">
                    <LocalizedText source={"Search for item"} /></label>
                  <Form.Input
                    data-testid="collection-item-search-input"
                    id="collection-item-search"
                    label={interfaceText("Search for item")}
                    loading={itemSearchLoading}
                    onChange={onSearchInputChange}
                    placeholder={interfaceText("Search by filename (e.g., sintel, aria, treasure)...")}
                    value={itemSearchQuery}
                   {...interfaceTextProps("Search for item")}/>
                </Form.Field>
                {itemSearchResults.length > 0 && (
                  <Form.Field>
                    <label htmlFor="collection-item-results">
                      <LocalizedText source={"Search Results"} /></label>
                    <Dropdown
                      data-testid="collection-item-results"
                      fluid
                      id="collection-item-results"
                      onChange={onSearchResultChange}
                      options={itemSearchResults.map((item, index) => ({
                        key: item.contentId || index,
                        text: `${item.fileName || item.path} (${item.mediaKind || 'File'})`,
                        value: item.contentId,
                      }))}
                      placeholder={interfaceText("Select an item from search results")}
                      search
                      selection
                     {...interfaceTextProps("Select an item from search results")}/>
                  </Form.Field>
                )}
                {itemSearchQuery &&
                  itemSearchResults.length === 0 &&
                  !itemSearchLoading && (
                    <Message info>
                      <LocalizedText source={"No results found. You can still add the search query as a content ID."} /></Message>
                  )}
              </Form>
            </Modal.Content>
            <Modal.Actions>
              <Button
                onClick={onClose}
              >
                <LocalizedText source={"Cancel"} /></Button>
              <Button
                data-testid="collection-add-item-submit"
                disabled={!itemSearchQuery.trim() || addingItem}
                loading={addingItem}
                onClick={onAddItem}
                primary
              >
                <LocalizedText source={"Add Item"} /></Button>
            </Modal.Actions>
          </Modal>
  );
};

export default CollectionAddItemModal;
