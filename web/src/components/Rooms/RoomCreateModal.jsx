import LocalizedText from "../Shared/LocalizedText";
import { interfaceText, interfaceTextProps, useInterfaceLanguage } from "../../lib/interfaceLocale";


import './Rooms.css';
import { toDisplayError } from '../../lib/errors';
import { useMountedRef } from '../../lib/useMountedRef';
import React, { useRef, useState } from 'react';
import { Button, Header, Icon, Input, Modal, Radio } from 'semantic-ui-react';

const RoomCreateModal = ({ onCreateRoom, ...modalOptions }) => {
  useInterfaceLanguage();
  const [open, setOpen] = useState(false);
  const [roomName, setRoomName] = useState('');
  const [isPrivate, setIsPrivate] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const mountedRef = useMountedRef();
  const createRequestIdRef = useRef(0);
  const createInFlightRef = useRef(false);

  const handleCreate = async () => {
    if (!mountedRef.current || loading || createInFlightRef.current) return;
    const name = roomName.trim();
    if (!name) {
      setError(interfaceText("Room name cannot be empty"));
      return;
    }

    const requestId = ++createRequestIdRef.current;
    const isCurrentRequest = () =>
      mountedRef.current && createRequestIdRef.current === requestId;

    createInFlightRef.current = true;
    setLoading(true);
    setError('');

    try {
      await onCreateRoom(name, isPrivate);
      if (!isCurrentRequest()) return;
      setOpen(false);
      setRoomName('');
      setIsPrivate(false);
    } catch (error) {
      if (isCurrentRequest()) {
        setError(toDisplayError(error, 'Failed to create room'));
      }
    } finally {
      if (isCurrentRequest()) setLoading(false);
      createInFlightRef.current = false;
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter') {
      handleCreate();
    }
  };

  return (
    <Modal
      size="small"
      {...modalOptions}
      onClose={() => {
        if (!loading) {
          setOpen(false);
          setError('');
          setRoomName('');
          setIsPrivate(false);
        }
      }}
      onOpen={() => setOpen(true)}
      open={open}
      trigger={
        <Button
          color="green"
          icon
          title={interfaceText("Create New Room")}
         {...interfaceTextProps("Create New Room")}>
          <Icon name="plus" />
          <LocalizedText source={"Create Room"} /></Button>
      }
    >
      <Modal.Header>
        <Icon name="plus" />
        <LocalizedText source={"Create New Room"} /></Modal.Header>
      <Modal.Content>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <div>
            <Header as="h4"><LocalizedText source={"Room Name"} /></Header>
            <Input
              error={Boolean(error)}
              fluid
              onChange={(_, { value }) => setRoomName(value)}
              onKeyPress={handleKeyPress}
              placeholder={interfaceText("Enter room name...")}
              value={roomName}
             {...interfaceTextProps("Enter room name...")}/>
            {error && (
              <div
                style={{ color: '#db2828', fontSize: '12px', marginTop: '4px' }}
              >
                {error}
              </div>
            )}
          </div>

          <div>
            <Header as="h4"><LocalizedText source={"Room Type"} /></Header>
            <div style={{ display: 'flex', gap: '24px' }}>
              <div
                style={{ alignItems: 'center', display: 'flex', gap: '8px' }}
              >
                <Radio
                  checked={!isPrivate}
                  name="roomType"
                  onChange={() => setIsPrivate(false)}
                  value="public"
                />
                <div>
                  <strong><LocalizedText source={"Public Room"} /></strong>
                  <div className="room-create-type-description">
                    <LocalizedText source={"Anyone can join and see the room"} /></div>
                </div>
              </div>
              <div
                style={{ alignItems: 'center', display: 'flex', gap: '8px' }}
              >
                <Radio
                  checked={isPrivate}
                  name="roomType"
                  onChange={() => setIsPrivate(true)}
                  value="private"
                />
                <div>
                  <strong><LocalizedText source={"Private Room"} /></strong>
                  <div className="room-create-type-description">
                    <LocalizedText source={"Only invited members can join"} /></div>
                </div>
              </div>
            </div>
          </div>

          <div className="room-create-note">
            <Icon name="info circle" />
            <strong><LocalizedText source={"Note:"} /></strong> <LocalizedText source={"Room creation depends on server permissions. Private rooms require server operator approval."} /></div>
        </div>
      </Modal.Content>
      <Modal.Actions>
        <Button
          disabled={loading}
          onClick={() => setOpen(false)}
        >
          <LocalizedText source={"Cancel"} /></Button>
        <Button
          disabled={!roomName.trim() || loading}
          loading={loading}
          onClick={handleCreate}
          positive
        >
          <Icon name="plus" />
          <LocalizedText source={"Create Room"} /></Button>
      </Modal.Actions>
    </Modal>
  );
};

export default RoomCreateModal;
