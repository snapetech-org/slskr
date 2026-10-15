import React from 'react';
import { Header, Icon, Segment } from 'semantic-ui-react';
import LocalizedText from './LocalizedText';

const PlaceholderSegment = ({
  caption,
  headingAs = 'h3',
  icon,
  size,
  ...rest
}) => {
  const className =
    size === 'small' ? 'placeholder-segment-small' : 'placeholder-segment';

  return (
    <Segment
      basic
      className={className}
      placeholder
      {...rest}
    >
      <Header
        as={headingAs}
        icon
      >
        <Icon name={icon} />
        {typeof caption === 'string' ? <LocalizedText source={caption} /> : caption}
      </Header>
    </Segment>
  );
};

export default PlaceholderSegment;
