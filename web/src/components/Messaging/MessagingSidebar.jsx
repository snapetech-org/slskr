import LocalizedText from "../Shared/LocalizedText";
import { interfaceText, interfaceTextProps, useInterfaceLanguage } from "../../lib/interfaceLocale";
import React from 'react';
import RoomCreateModal from '../Rooms/RoomCreateModal';
import { channelLabel, normalizeConversationName } from './messagingWorkspaceState';
import {
  Button,
  Dropdown,
  Icon,
  Input,
  Label,
  Message,
  Popup,
  Segment,
} from 'semantic-ui-react';

const MessagingSidebar = ({ actions, state }) => {
  useInterfaceLanguage();
  const {
    availableRoomsError,
    bridgedPodNames,
    chatTarget,
    conversations,
    joinedRooms,
    roomOptions,
    roomSearchLoading,
    visiblePodChannels,
    workspaceError,
  } = state;
  const {
    deleteConversation,
    fetchAvailableRooms,
    isWorkspaceActionPending,
    joinRoom,
    leavePod,
    leaveRoom,
    openPanel,
    refreshWorkspace,
    setChatTarget,
  } = actions;

  return (
        <Segment className="messaging-sidebar">
          <div className="messaging-sidebar-header">
            <div className="messaging-sidebar-title">
              <Icon name="comments" />
              <LocalizedText source={"Messages"} /></div>
            <Popup
              content={interfaceText("Reload saved conversations and joined rooms from the daemon.")}
              trigger={
                <Button
                  aria-label={interfaceText("Refresh messages workspace")}
                  icon="refresh"
                  onClick={() => refreshWorkspace()}
                  size="mini"
                  title={interfaceText("Refresh messages workspace")}
                 {...interfaceTextProps("Refresh messages workspace")}/>
              }
             {...interfaceTextProps("Reload saved conversations and joined rooms from the daemon.")}/>
          </div>
          {workspaceError ? <Message warning>{workspaceError}</Message> : null}

          <div className="messaging-sidebar-section">
            <div className="messaging-sidebar-section-title"><LocalizedText source={"Direct Message"} /></div>
            <div className="messaging-start-row">
              <Input
                aria-label={interfaceText("Chat username")}
                fluid
                onChange={(event) => setChatTarget(event.target.value)}
                onKeyUp={(event) => {
                  if (event.key === 'Enter' && chatTarget.trim()) {
                    openPanel('chat', chatTarget);
                    setChatTarget('');
                  }
                }}
                placeholder={interfaceText("username")}
                size="small"
                value={chatTarget}
               {...interfaceTextProps("Chat username")}/>
              <Popup
                content={interfaceText("Open a direct-message panel for this user.")}
                trigger={
                  <Button
                    aria-label={interfaceText("Open direct-message panel")}
                    disabled={!chatTarget.trim()}
                    icon="comment"
                    onClick={() => {
                      openPanel('chat', chatTarget);
                      setChatTarget('');
                    }}
                    size="small"
                    title={interfaceText("Open direct-message panel")}
                   {...interfaceTextProps("Open direct-message panel")}/>
                }
               {...interfaceTextProps("Open a direct-message panel for this user.")}/>
            </div>
          </div>

          <div className="messaging-sidebar-section">
            <div className="messaging-sidebar-section-title">
              <LocalizedText source={"Saved Chats"} /><Label size="mini">{conversations.length}</Label>
            </div>
            <div className="messaging-list">
              {conversations.map((conversation) => (
                <div
                  className="messaging-list-action-row"
                  key={conversation.username}
                >
                  <Popup
                    content={interfaceText("Open this conversation as a workspace panel.")}
                    trigger={
                      <Button
                        basic
                        className="messaging-list-button"
                        compact
                        onClick={() => openPanel('chat', conversation.username)}
                        size="small"
                      >
                        <Icon name="comment alternate" />
                        {conversation.username}
                        {bridgedPodNames.has(
                          normalizeConversationName(conversation.username),
                        ) && (
                          <Label
                            size="mini"
                            title={interfaceText("Pod direct channel is folded into this saved direct message.")}
                           {...interfaceTextProps("Pod direct channel is folded into this saved direct message.")}>
                            <LocalizedText source={"pod"} /></Label>
                        )}
                        {conversation.hasUnAcknowledgedMessages && (
                          <Label
                            color="red"
                            size="mini"
                          >
                            {conversation.unAcknowledgedMessageCount}
                          </Label>
                        )}
                      </Button>
                    }
                   {...interfaceTextProps("Open this conversation as a workspace panel.")}/>
                  <Popup
                    content={interfaceText("Permanently delete this saved message thread.")}
                    trigger={
                      <Button
                        aria-label={interfaceText("Delete message thread with {username}", { "username": (conversation.username) })}
                        disabled={isWorkspaceActionPending(`chat:delete:${conversation.username}`)}
                        icon="trash alternate"
                        negative
                        onClick={() => deleteConversation(conversation.username)}
                        size="small"
                        title={interfaceText("Delete message thread with {username}", { "username": (conversation.username) })}
                       {...interfaceTextProps("Delete message thread with {username}")}/>
                    }
                   {...interfaceTextProps("Permanently delete this saved message thread.")}/>
                </div>
              ))}
            </div>
          </div>

          <div className="messaging-sidebar-section">
            <div className="messaging-sidebar-section-title"><LocalizedText source={"Join Room"} /></div>
            <div className="messaging-start-row">
              <Dropdown
                aria-label={interfaceText("Search rooms")}
                clearable
                fluid
                loading={roomSearchLoading}
                onChange={(_, { value }) => joinRoom(value)}
                onOpen={fetchAvailableRooms}
                options={roomOptions}
                placeholder={interfaceText("Search rooms")}
                search
                selection
                size="small"
               {...interfaceTextProps("Search rooms")}/>
              <RoomCreateModal onCreateRoom={(roomName) => joinRoom(roomName)} />
            </div>
            {availableRoomsError ? (
              <Message negative>{availableRoomsError}</Message>
            ) : null}
          </div>

          <div className="messaging-sidebar-section">
            <div className="messaging-sidebar-section-title">
              <LocalizedText source={"Joined Rooms"} /><Label size="mini">{joinedRooms.length}</Label>
            </div>
            <div className="messaging-list">
              {joinedRooms.map((roomName) => (
                <div
                  className="messaging-list-action-row"
                  key={roomName}
                >
                  <Popup
                    content={interfaceText("Open this room as a workspace panel.")}
                    trigger={
                      <Button
                        basic
                        className="messaging-list-button"
                        compact
                        onClick={() => openPanel('room', roomName)}
                        size="small"
                      >
                        <Icon name="comments" />
                        #{roomName}
                      </Button>
                    }
                   {...interfaceTextProps("Open this room as a workspace panel.")}/>
                  <Popup
                    content={interfaceText("Leave this room and remove it from joined rooms.")}
                    trigger={
                      <Button
                        aria-label={interfaceText("Leave room {roomName}", { "roomName": (roomName) })}
                        disabled={isWorkspaceActionPending(`room:leave:${roomName}`)}
                        icon="sign-out"
                        negative
                        onClick={() => leaveRoom(roomName)}
                        size="small"
                        title={interfaceText("Leave room {roomName}", { "roomName": (roomName) })}
                       {...interfaceTextProps("Leave room {roomName}")}/>
                    }
                   {...interfaceTextProps("Leave this room and remove it from joined rooms.")}/>
                </div>
              ))}
            </div>
          </div>

          <div className="messaging-sidebar-section">
            <div className="messaging-sidebar-section-title">
              <LocalizedText source={"Pod Channels"} /><Label size="mini">{visiblePodChannels.length}</Label>
            </div>
            <div className="messaging-list">
              {visiblePodChannels.map((channel) => (
                <div
                  className="messaging-list-action-row"
                  key={channel.target}
                >
                  <Popup
                    content={interfaceText("Open this pod channel in the unified message workspace.")}
                    trigger={
                      <Button
                        basic
                        className="messaging-list-button"
                        compact
                        onClick={() =>
                          openPanel('pod', channel.target, {
                            label: channelLabel(channel),
                          })
                        }
                        size="small"
                      >
                        <Icon name="comments outline" />
                        {channelLabel(channel)}
                      </Button>
                    }
                   {...interfaceTextProps("Open this pod channel in the unified message workspace.")}/>
                  <Popup
                    content={interfaceText("Leave this pod and remove its channels from Messages.")}
                    trigger={
                      <Button
                        aria-label={interfaceText("Leave pod {podName}", { "podName": (channel.podName) })}
                        disabled={isWorkspaceActionPending(`pod:leave:${channel.podId}`)}
                        icon="sign-out"
                        negative
                        onClick={() => leavePod(channel)}
                        size="small"
                        title={interfaceText("Leave pod {podName}", { "podName": (channel.podName) })}
                       {...interfaceTextProps("Leave pod {podName}")}/>
                    }
                   {...interfaceTextProps("Leave this pod and remove its channels from Messages.")}/>
                </div>
              ))}
            </div>
          </div>
        </Segment>
  );
};

export default MessagingSidebar;
