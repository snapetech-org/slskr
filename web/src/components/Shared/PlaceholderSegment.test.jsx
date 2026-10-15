import '@testing-library/jest-dom';
import SPANISH_LABELS from '../../lib/locales/ui-labels.es.json';
import { resetInterfaceLanguage, setInterfaceLanguage } from '../../lib/interfaceLocale';
import PlaceholderSegment from './PlaceholderSegment';
import React from 'react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { act, render, screen } from '@testing-library/react';

beforeEach(() => {
  vi.stubGlobal('fetch', vi.fn(async () => ({
    ok: true,
    json: async () => SPANISH_LABELS,
  })));
});

afterEach(() => {
  act(() => resetInterfaceLanguage());
  vi.unstubAllGlobals();
});

describe('PlaceholderSegment', () => {
  it('translates string captions and marks their language', async () => {
    await act(async () => { await setInterfaceLanguage('es'); });

    render(<PlaceholderSegment caption="No messages yet" />);

    expect(screen.getByText('Aún no hay mensajes')).toHaveAttribute('lang', 'es');
  });

  it('preserves React captions supplied by callers', () => {
    render(<PlaceholderSegment caption={<span>Custom caption</span>} />);

    expect(screen.getByText('Custom caption')).toBeInTheDocument();
  });
});
