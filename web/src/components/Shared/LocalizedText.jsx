import React from 'react';
import { useInterfaceLanguage } from '../../lib/interfaceLocale';

const LocalizedText = ({ as: Element = 'span', source, values, children, ...props }) => {
  const { directionFor, languageFor, t } = useInterfaceLanguage();
  const language = typeof source === 'string' ? languageFor(source) : undefined;
  const text = typeof source === 'string' ? t(source, values) : children;

  // English text inherits the document language and direction. Avoid adding a
  // wrapper for the default locale so ordinary phrases remain one text node.
  if (Element === 'span' && language === 'en' && Object.keys(props).length === 0) {
    return text;
  }

  return (
    <Element dir={typeof source === 'string' ? directionFor(source) : undefined}
      lang={language}
      {...props}
    >
      {text}
    </Element>
  );
};

export default LocalizedText;
