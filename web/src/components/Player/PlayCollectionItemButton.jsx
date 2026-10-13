import { interfaceText, interfaceTextProps, useInterfaceLanguage } from "../../lib/interfaceLocale";
import { usePlayer } from './PlayerContext';
import React from 'react';
import { Button, Icon, Popup } from 'semantic-ui-react';

const PlayCollectionItemButton = ({ item, size = 'small' }) => {
  useInterfaceLanguage();
  const { playItem } = usePlayer();

  return (
    <Popup
      content={interfaceText("Play this item through the local stream endpoint and update your now-playing status.")}
      trigger={
        <Button
          data-testid="player-play-item"
          icon
          onClick={() => playItem(item, { replaceQueue: true })}
          size={size}
        >
          <Icon name="play" />
        </Button>
      }
     {...interfaceTextProps("Play this item through the local stream endpoint and update your now-playing status.")}/>
  );
};

export default PlayCollectionItemButton;

