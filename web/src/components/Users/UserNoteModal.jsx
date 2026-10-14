import LocalizedText from "../Shared/LocalizedText";
import { interfaceText, interfaceTextProps, useInterfaceLanguage } from "../../lib/interfaceLocale";
import * as userNotes from '../../lib/userNotes';
import { toDisplayError } from '../../lib/errors';
import { useMountedRef } from '../../lib/useMountedRef';
import React, { useEffect, useState } from 'react';
import { Button, Form, Header, Icon, Message, Modal } from 'semantic-ui-react';

const colors = [
  { icon: 'circle outline', get text() { return interfaceText("None"); }, value: null },
  {
    label: { circular: true, color: 'red', empty: true },
    get text() { return interfaceText("Red"); },
    value: 'red',
  },
  {
    label: { circular: true, color: 'orange', empty: true },
    get text() { return interfaceText("Orange"); },
    value: 'orange',
  },
  {
    label: { circular: true, color: 'yellow', empty: true },
    get text() { return interfaceText("Yellow"); },
    value: 'yellow',
  },
  {
    label: { circular: true, color: 'olive', empty: true },
    get text() { return interfaceText("Olive"); },
    value: 'olive',
  },
  {
    label: { circular: true, color: 'green', empty: true },
    get text() { return interfaceText("Green"); },
    value: 'green',
  },
  {
    label: { circular: true, color: 'teal', empty: true },
    get text() { return interfaceText("Teal"); },
    value: 'teal',
  },
  {
    label: { circular: true, color: 'blue', empty: true },
    get text() { return interfaceText("Blue"); },
    value: 'blue',
  },
  {
    label: { circular: true, color: 'violet', empty: true },
    get text() { return interfaceText("Violet"); },
    value: 'violet',
  },
  {
    label: { circular: true, color: 'purple', empty: true },
    get text() { return interfaceText("Purple"); },
    value: 'purple',
  },
  {
    label: { circular: true, color: 'pink', empty: true },
    get text() { return interfaceText("Pink"); },
    value: 'pink',
  },
  {
    label: { circular: true, color: 'brown', empty: true },
    get text() { return interfaceText("Brown"); },
    value: 'brown',
  },
  {
    label: { circular: true, color: 'grey', empty: true },
    get text() { return interfaceText("Grey"); },
    value: 'grey',
  },
  {
    label: { circular: true, color: 'black', empty: true },
    get text() { return interfaceText("Black"); },
    value: 'black',
  },
];

const UserNoteModal = ({ onClose, trigger, username }) => {
  useInterfaceLanguage();
  const [open, setOpen] = useState(false);
  const [note, setNote] = useState('');
  const [color, setColor] = useState(null);
  const [isHighPriority, setIsHighPriority] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const mountedRef = useMountedRef();
  const requestIdRef = React.useRef(0);
  const saveInFlightRef = React.useRef(false);

  useEffect(() => {
    const requestId = ++requestIdRef.current;
    const fetchNote = async () => {
      if (!username || !open || !mountedRef.current) return;

      setLoading(true);
      setError('');
      try {
        const response = await userNotes.getNote({ username });
        if (
          !mountedRef.current ||
          requestIdRef.current !== requestId
        ) {
          return;
        }
        if (
          response.data &&
          typeof response.data === 'object' &&
          !Array.isArray(response.data)
        ) {
          setNote(
            typeof response.data.note === 'string' ? response.data.note : '',
          );
          setColor(
            typeof response.data.color === 'string'
              ? response.data.color
              : null,
          );
          setIsHighPriority(response.data.isHighPriority === true);
        } else {
          // Reset if no note exists
          setNote('');
          setColor(null);
          setIsHighPriority(false);
        }
      } catch (error) {
        if (
          !mountedRef.current ||
          requestIdRef.current !== requestId
        ) {
          return;
        }
        if (error.response && error.response.status === 404) {
          setNote('');
          setColor(null);
          setIsHighPriority(false);
        } else {
          console.error('Failed to fetch user note', error);
          setError(toDisplayError(error, 'Failed to load user note'));
        }
      } finally {
        if (
          mountedRef.current &&
          requestIdRef.current === requestId
        ) {
          setLoading(false);
        }
      }
    };

    void fetchNote();

    return () => {
      requestIdRef.current += 1;
    };
  }, [mountedRef, open, username]);

  const handleClose = () => {
    setOpen(false);
    if (onClose) onClose();
  };

  const handleSave = async () => {
    if (
      !mountedRef.current ||
      loading ||
      saveInFlightRef.current ||
      !username
    ) {
      return;
    }
    saveInFlightRef.current = true;
    const requestId = ++requestIdRef.current;
    const isCurrentRequest = () =>
      mountedRef.current && requestIdRef.current === requestId;
    setLoading(true);
    setError('');
    try {
      await userNotes.setNote({
        color,
        isHighPriority,
        note,
        username,
      });
      if (isCurrentRequest()) handleClose();
    } catch (error) {
      if (isCurrentRequest()) {
        console.error('Failed to save user note', error);
        setError(toDisplayError(error, 'Failed to save user note'));
      }
    } finally {
      saveInFlightRef.current = false;
      if (isCurrentRequest()) setLoading(false);
    }
  };

  return (
    <Modal
      onClose={handleClose}
      onOpen={() => setOpen(true)}
      open={open}
      size="tiny"
      trigger={trigger}
    >
      <Header>
        <Icon name="sticky note outline" />
        <Modal.Content><LocalizedText source={"User Note:"} />{" "}{username}</Modal.Content>
      </Header>
      <Modal.Content>
        <Form loading={loading}>
          <Form.Dropdown
            fluid
            label={interfaceText("Color Rating")}
            onChange={(_, { value }) => setColor(value)}
            options={colors}
            placeholder={interfaceText("Select Color")}
            selection
            value={color}
           {...interfaceTextProps("Color Rating")}/>
          <Form.TextArea
            label={interfaceText("Note")}
            onChange={(event) => setNote(event.target.value)}
            placeholder={interfaceText("Enter notes about this user...")}
            rows={5}
            value={note}
           {...interfaceTextProps("Note")}/>
          <Form.Checkbox
            checked={isHighPriority}
            label={interfaceText("High Priority (Warning)")}
            onChange={(_, { checked }) => setIsHighPriority(checked)}
           {...interfaceTextProps("High Priority (Warning)")}/>
        </Form>
        {error ? <Message negative>{error}</Message> : null}
      </Modal.Content>
      <Modal.Actions>
        <Button onClick={handleClose}><LocalizedText source={"Cancel"} /></Button>
        <Button
          disabled={loading}
          onClick={handleSave}
          primary
        >
          <LocalizedText source={"Save"} /></Button>
      </Modal.Actions>
    </Modal>
  );
};

export default UserNoteModal;
