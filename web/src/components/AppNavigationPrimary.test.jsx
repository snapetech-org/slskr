import '@testing-library/jest-dom';
import AppNavigationPrimary from './AppNavigationPrimary';
import ARABIC_LABELS from '../lib/locales/ui-labels.ar.json';
import {
  resetInterfaceLanguage,
  setInterfaceLanguage,
} from '../lib/interfaceLocale';
import { act, cleanup, render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import React from 'react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

beforeEach(() => {
  vi.stubGlobal('fetch', vi.fn(async () => ({
    ok: true,
    json: async () => ARABIC_LABELS,
  })));
});

afterEach(() => {
  cleanup();
  resetInterfaceLanguage();
  vi.unstubAllGlobals();
});

describe('primary navigation language metadata', () => {
  it('keeps translated and English fallback metadata scoped to each navigation label', async () => {
    await act(async () => { await setInterfaceLanguage('ar'); });

    render(
      <MemoryRouter>
        <AppNavigationPrimary
          isAgent={false}
          isLegacyProfile={false}
          isNativeProfile={true}
          navActivity={{ chat: false, rooms: false }}
          version={{ isCanary: true }}
        />
      </MemoryRouter>,
    );

    const navigation = screen.getByRole('navigation', {
      name: ARABIC_LABELS['Primary navigation'],
    });
    expect(navigation).toHaveAttribute('lang', 'ar');
    expect(navigation).not.toHaveAttribute('dir', 'rtl');
    expect(navigation).toHaveAttribute(
      'aria-labelledby',
      'primary-navigation-label',
    );
    const accessibleLabel = document.getElementById('primary-navigation-label');
    expect(accessibleLabel).toHaveTextContent(
      ARABIC_LABELS['Primary navigation'],
    );
    expect(accessibleLabel).toHaveAttribute('lang', 'ar');
    expect(accessibleLabel).toHaveAttribute('dir', 'rtl');
    const translatedSearch = screen.getByText(ARABIC_LABELS.Search);
    expect(translatedSearch).toHaveAttribute('lang', 'ar');
    expect(translatedSearch).toHaveAttribute('dir', 'rtl');
    for (const fallback of ['Canary', 'Lidarr', 'Solid']) {
      expect(screen.getByText(fallback)).toHaveAttribute('lang', 'en');
      expect(screen.getByText(fallback)).toHaveAttribute('dir', 'ltr');
    }
    expect(document.documentElement.lang).toBe('en');
    expect(document.documentElement.dir).toBe('ltr');
  });

  it('localizes the More dropdown accessible name and metadata', async () => {
    await act(async () => { await setInterfaceLanguage('ar'); });

    render(
      <MemoryRouter>
        <AppNavigationPrimary
          isAgent={false}
          isLegacyProfile={false}
          isNativeProfile={false}
          navActivity={{ chat: false, rooms: false }}
          version={{ isCanary: false }}
        />
      </MemoryRouter>,
    );

    const moreDropdown = screen.getByTestId('nav-more');
    expect(moreDropdown).toHaveAttribute(
      'aria-label',
      ARABIC_LABELS['More navigation options'],
    );
    expect(moreDropdown).toHaveAttribute('lang', 'ar');
    expect(moreDropdown).toHaveAttribute('dir', 'rtl');
  });
});
