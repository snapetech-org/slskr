import {
  defaultHighlightStyle,
  StreamLanguage,
  syntaxHighlighting,
} from '@codemirror/language';
import { yaml } from '@codemirror/legacy-modes/mode/yaml';
import { Annotation, EditorState } from '@codemirror/state';
import { oneDark } from '@codemirror/theme-one-dark';
import { EditorView } from '@codemirror/view';
import React, { useEffect, useRef } from 'react';

// These JSON viewers disable basicSetup. Own their small CodeMirror lifecycle
// directly so autocomplete, search, lint, and command bundles are not shipped.
const externalValue = Annotation.define();

const CodeEditor = ({
  ariaLabel,
  basicSetup: _basicSetup,
  editable = true,
  onChange,
  theme,
  value = '',
  ...rest
}) => {
  const container = useRef(null);
  const editor = useRef(null);
  const changeHandler = useRef(onChange);
  changeHandler.current = onChange;

  useEffect(() => {
    const nonce = document.querySelector('meta[name="csp-nonce"]')?.getAttribute('content');
    const view = new EditorView({
      parent: container.current,
      state: EditorState.create({
        doc: value,
        extensions: [
          StreamLanguage.define(yaml),
          syntaxHighlighting(defaultHighlightStyle, { fallback: true }),
          EditorView.editable.of(editable),
          EditorState.readOnly.of(!editable),
          EditorView.contentAttributes.of({
            ...(ariaLabel ? { 'aria-label': ariaLabel } : {}),
            ...(!editable ? { 'aria-readonly': 'true', tabindex: '0' } : {}),
          }),
          ...(nonce ? [EditorView.cspNonce.of(nonce)] : []),
          ...(theme === 'dark' ? [oneDark] : []),
          EditorView.updateListener.of((update) => {
            if (update.docChanged && update.transactions.some((transaction) => !transaction.annotation(externalValue))) {
              changeHandler.current?.(update.state.doc.toString());
            }
          }),
        ],
      }),
    });
    editor.current = view;
    return () => {
      editor.current = null;
      view.destroy();
    };
    // Value updates use transactions below and retain selection and scroll.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [ariaLabel, editable, theme]);

  useEffect(() => {
    const view = editor.current;
    if (view && view.state.doc.toString() !== value) {
      view.dispatch({
        changes: { from: 0, to: view.state.doc.length, insert: value },
        annotations: externalValue.of(true),
      });
    }
  }, [value]);

  return <div ref={container} {...rest} />;
};

export default CodeEditor;
