import '@testing-library/jest-dom';
import AppNavigationPrimary from './AppNavigationPrimary';
import UI_LABELS from '../lib/ui-labels.json';
import { resetInterfaceLanguage, setInterfaceLanguage } from '../lib/interfaceLocale';
import { cleanup, render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import React from 'react';
import { afterEach, describe, expect, it } from 'vitest';

afterEach(() => {
  cleanup();
  resetInterfaceLanguage();
});

describe('primary navigation language metadata', () => {
  it('keeps Arabic direction and language scoped to the translated navigation', () => {
    setInterfaceLanguage('ar');

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

    const navigation = screen.getByRole('navigation', {
      name: UI_LABELS['Primary navigation'].ar,
    });
    expect(navigation).toHaveAttribute('lang', 'ar');
    expect(navigation).toHaveAttribute('dir', 'rtl');
    expect(screen.getByText(UI_LABELS.Search.ar)).toBeInTheDocument();
    expect(document.documentElement.lang).toBe('en');
    expect(document.documentElement.dir).toBe('ltr');
  });
});
