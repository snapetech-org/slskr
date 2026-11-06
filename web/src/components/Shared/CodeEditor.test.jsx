import React from 'react';
import { render, screen } from '@testing-library/react';
import { EditorView } from '@codemirror/view';
import CodeEditor from './CodeEditor';

it('updates a read-only viewer without replacing its editor and destroys it on unmount', () => {
  const destroy = vi.spyOn(EditorView.prototype, 'destroy');
  const onChange = vi.fn();
  const { rerender, unmount } = render(
    <CodeEditor ariaLabel="Server options JSON" editable={false} onChange={onChange} value={'{"one":1}'} />,
  );
  const content = screen.getByLabelText('Server options JSON');
  expect(content).toHaveAttribute('aria-readonly', 'true');
  expect(content).toHaveAttribute('tabindex', '0');
  expect(content).toHaveTextContent('{"one":1}');
  rerender(<CodeEditor ariaLabel="Server options JSON" editable={false} onChange={onChange} value={'{"two":2}'} />);
  expect(screen.getByLabelText('Server options JSON')).toBe(content);
  expect(content).toHaveTextContent('{"two":2}');
  expect(onChange).not.toHaveBeenCalled();
  unmount();
  expect(destroy).toHaveBeenCalledOnce();
  destroy.mockRestore();
});

it('uses the CSP nonce for editor styles and retains wrapper language metadata', () => {
  const meta = document.createElement('meta');
  meta.name = 'csp-nonce';
  meta.content = 'viewer-test-nonce';
  document.head.append(meta);
  try {
    const { container } = render(<CodeEditor ariaLabel="JSON" editable={false} theme="dark" lang="es" dir="ltr" value="{}" />);
    expect(container.firstChild).toHaveAttribute('lang', 'es');
    expect(container.firstChild).toHaveAttribute('dir', 'ltr');
    expect(document.head.querySelector('style[nonce="viewer-test-nonce"]')).not.toBeNull();
  } finally {
    meta.remove();
  }
});
