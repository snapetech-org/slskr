import React from 'react';
import LocalizedText, { LocalizedErrorOutput } from './LocalizedText';
import { isDisplayErrorOutput, toDisplayErrorOutput } from '../../lib/errors';
import { Header, Icon, Segment } from 'semantic-ui-react';

const ErrorSegment = ({ caption, error, icon = 'x', suppressPrefix = false }) => {
  const rawCaption = caption ?? error;
  const displayCaption = React.isValidElement(rawCaption)
    ? rawCaption
    : isDisplayErrorOutput(rawCaption)
      ? <LocalizedErrorOutput output={rawCaption} />
      : typeof rawCaption === 'string' || typeof rawCaption === 'number'
        ? <bdi dir="auto" lang="und">{String(rawCaption)}</bdi>
        : <LocalizedErrorOutput output={toDisplayErrorOutput(rawCaption)} />;

  return (
    <Segment
      basic
      className="error-segment"
      placeholder
    >
      <Header icon>
        <Icon
          color="red"
          name={icon}
        />
        {!suppressPrefix && <><LocalizedText source={"Error:"} />{' '}</>}
        {displayCaption}
      </Header>
    </Segment>
  );
};

export default ErrorSegment;
