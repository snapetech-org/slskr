import React from 'react';
import { Button, Popup } from 'semantic-ui-react';
import { useInterfaceLanguage } from '../../lib/interfaceLocale';

export const LocalizedPopup = ({ content, parameters = {}, translateContent = true, textDirection, textLanguage, ...props }) => {
  const { t, languageFor, directionFor } = useInterfaceLanguage();
  const popupContent = typeof content === 'string' && translateContent
    ? <span lang={textLanguage || languageFor(content)} dir={textDirection || directionFor(content)}>{t(content, parameters)}</span>
    : content;

  return <Popup {...props} content={popupContent} />;
};

const getText = (children) => {
  if (typeof children === 'string') {
    return children;
  }

  if (Array.isArray(children)) {
    return children.filter((child) => typeof child === 'string').join(' ').trim();
  }

  return '';
};

const TooltipButton = ({
  'aria-label': ariaLabel,
  children,
  content: buttonContent,
  popupPosition = 'top center',
  parameters = {},
  dir: providedDirection,
  lang: providedLanguage,
  title,
  tooltip,
  ...props
}) => {
  const { t, languageFor, directionFor } = useInterfaceLanguage();
  const translateChildren = (value) => {
    if (typeof value === 'string') return t(value, parameters);
    if (Array.isArray(value)) return value.map(translateChildren);
    return value;
  };
  const translatedAriaLabel = typeof ariaLabel === 'string' ? t(ariaLabel, parameters) : ariaLabel;
  const translatedTitle = typeof title === 'string' ? t(title, parameters) : title;
  const translatedContent = typeof buttonContent === 'string'
    ? t(buttonContent, parameters)
    : translateChildren(buttonContent);
  const translatedChildren = translateChildren(children);
  const inferredSource = ariaLabel || title || getText(children) || getText(buttonContent) ||
    (typeof tooltip === 'string' ? tooltip : undefined);
  const inferredLabel = inferredSource ? t(inferredSource, parameters) : undefined;
  const metadataSource = ariaLabel || title || getText(children) || getText(buttonContent) ||
    (typeof tooltip === 'string' ? tooltip : undefined);
  const button = (
    <Button
      {...props}
      aria-label={translatedAriaLabel || inferredLabel}
      content={translatedContent}
      dir={providedDirection || (metadataSource ? directionFor(metadataSource) : undefined)}
      lang={providedLanguage || (metadataSource ? languageFor(metadataSource) : undefined)}
      title={translatedTitle}
    >
      {translatedChildren}
    </Button>
  );
  const content = tooltip || title || inferredSource;

  if (!content) {
    return button;
  }

  return (
    <LocalizedPopup
      content={content}
      parameters={parameters}
      position={popupPosition}
      textDirection={providedDirection}
      textLanguage={providedLanguage}
      trigger={button}
    />
  );
};

TooltipButton.Group = Button.Group;
TooltipButton.Or = Button.Or;

export default TooltipButton;
