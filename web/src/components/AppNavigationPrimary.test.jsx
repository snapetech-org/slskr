import '@testing-library/jest-dom';
import AppNavigationPrimary from './AppNavigationPrimary';
import UI_LABELS from '../lib/ui-labels.json';
import {
  INTERFACE_LANGUAGE_OPTIONS,
  resetInterfaceLanguage,
  setInterfaceLanguage,
} from '../lib/interfaceLocale';
import { cleanup, render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import React from 'react';
import { afterEach, describe, expect, it } from 'vitest';

afterEach(() => {
  cleanup();
  resetInterfaceLanguage();
});

describe('primary navigation language metadata', () => {
  it('keeps translated and English fallback metadata scoped to each navigation label', () => {
    setInterfaceLanguage('ar');
    const arabicIndex = INTERFACE_LANGUAGE_OPTIONS.slice(1).findIndex(
      ({ value }) => value === 'ar',
    );

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
      name: UI_LABELS['Primary navigation'][arabicIndex],
    });
    expect(navigation).toHaveAttribute('lang', 'ar');
    expect(navigation).toHaveAttribute('dir', 'rtl');
    const translatedSearch = screen.getByText(UI_LABELS.Search[arabicIndex]);
    expect(translatedSearch).toHaveAttribute('lang', 'ar');
    expect(translatedSearch).toHaveAttribute('dir', 'rtl');
    for (const fallback of ['Canary', 'Lidarr', 'Solid']) {
      expect(screen.getByText(fallback)).toHaveAttribute('lang', 'en');
      expect(screen.getByText(fallback)).toHaveAttribute('dir', 'ltr');
    }
    expect(document.documentElement.lang).toBe('en');
    expect(document.documentElement.dir).toBe('ltr');
  });

  it('localizes the More dropdown accessible name and metadata', () => {
    setInterfaceLanguage('ar');
    const arabicIndex = INTERFACE_LANGUAGE_OPTIONS.slice(1).findIndex(
      ({ value }) => value === 'ar',
    );

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
      UI_LABELS['More navigation options'][arabicIndex],
    );
    expect(moreDropdown).toHaveAttribute('lang', 'ar');
    expect(moreDropdown).toHaveAttribute('dir', 'rtl');
  });
});
