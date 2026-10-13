import '@testing-library/jest-dom';
import ExperienceSettings from './index';
import { REGIONAL_FORMAT_OPTIONS } from '../../../lib/regionalFormat';
import {
  INTERFACE_LANGUAGE_OPTIONS,
  resetInterfaceLanguage,
  setInterfaceLanguage,
} from '../../../lib/interfaceLocale';
import { setRegionalFormatPreference } from '../../../lib/util';
import React from 'react';
import { fireEvent, render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const storageKey = 'slskr:experience-preferences:v1';

describe('ExperienceSettings', () => {
  beforeEach(() => {
    localStorage.clear();
    resetInterfaceLanguage();
    setRegionalFormatPreference('system');
    Object.assign(navigator, {
      clipboard: {
        writeText: vi.fn().mockResolvedValue(undefined),
      },
    });
  });

  it('surfaces Search, Player, and Messages preferences', () => {
    render(<ExperienceSettings />);

    expect(screen.getByText('Search')).toBeInTheDocument();
    expect(screen.queryByText('Discovery Inbox')).not.toBeInTheDocument();
    expect(screen.getByText('Player')).toBeInTheDocument();
    expect(screen.getByText('Messages')).toBeInTheDocument();
    expect(
      screen.getByLabelText('Enable search duplicate folding preference'),
    ).toBeChecked();
    expect(screen.getByLabelText('Show unread message badges preference')).toBeChecked();
  });

  it('saves local preferences without a backend call', () => {
    render(<ExperienceSettings />);

    fireEvent.click(screen.getByLabelText('Enable search duplicate folding preference'));
    fireEvent.click(screen.getByLabelText('Enable player queue auto-fill preference'));
    fireEvent.click(screen.getByRole('button', { name: 'Save Local Preferences' }));

    const saved = JSON.parse(localStorage.getItem(storageKey));
    expect(saved.searchDuplicateFolding).toBe(false);
    expect(saved.playerQueueAutoFill).toBe(true);
    expect(
      screen.getByText('Experience preferences saved locally in this browser.'),
    ).toBeInTheDocument();
  });

  it('keeps the regional selector in sync with changes from another tab', () => {
    render(<ExperienceSettings />);

    localStorage.setItem(storageKey, JSON.stringify({ regionalFormat: 'de' }));
    fireEvent(
      window,
      new StorageEvent('storage', {
        key: storageKey,
        newValue: JSON.stringify({ regionalFormat: 'de' }),
      }),
    );

    expect(screen.getByRole('combobox', { name: 'Regional format' })).toHaveTextContent(
      'Deutsch — German',
    );

    fireEvent.click(screen.getByLabelText('Enable search duplicate folding preference'));
    fireEvent.click(screen.getByRole('button', { name: 'Save Local Preferences' }));

    expect(JSON.parse(localStorage.getItem(storageKey)).regionalFormat).toBe('de');
  });

  it('copies a preference report', () => {
    render(<ExperienceSettings />);

    fireEvent.click(screen.getByRole('button', { name: 'Copy Report' }));

    expect(navigator.clipboard.writeText).toHaveBeenCalledWith(
      expect.stringContaining('slskr experience preferences'),
    );
    expect(navigator.clipboard.writeText).toHaveBeenCalledWith(
      expect.stringContaining('Messages:'),
    );
  });

  it('resets the browser-local interface language with the other preferences', () => {
    setInterfaceLanguage('de');
    render(<ExperienceSettings />);

    fireEvent.click(screen.getByRole('button', { name: 'Reset' }));

    expect(localStorage.getItem('slskr.interface-language')).toBeNull();
    expect(document.documentElement.lang).toBe('en');
    expect(
      screen.getByText('Experience preferences reset to defaults.'),
    ).toBeInTheDocument();
  });

  it('uses each language option’s own pronunciation and text direction', () => {
    setInterfaceLanguage('ar');
    render(<ExperienceSettings />);

    const languageSelect = screen.getAllByRole('combobox')[0];
    expect(languageSelect).not.toHaveAttribute('lang');
    expect(languageSelect).not.toHaveAttribute('dir');
    fireEvent.click(languageSelect);

    for (const option of INTERFACE_LANGUAGE_OPTIONS) {
      const optionLabel = screen.getByRole('option', { name: option.text }).querySelector('span');
      expect(optionLabel).not.toBeNull();
      expect(optionLabel).toHaveAttribute('lang', option.value);
      expect(optionLabel).toHaveAttribute('dir', option.value === 'ar' ? 'rtl' : 'ltr');
    }
  });

  it('uses each regional-format option’s own pronunciation and text direction', () => {
    setInterfaceLanguage('ar');
    render(<ExperienceSettings />);

    const regionalSelect = screen.getAllByRole('combobox')[1];
    expect(regionalSelect).not.toHaveAttribute('lang');
    expect(regionalSelect).not.toHaveAttribute('dir');
    fireEvent.click(regionalSelect);

    for (const option of REGIONAL_FORMAT_OPTIONS) {
      const optionLabel = screen.getByRole('option', { name: option.text }).querySelector('span');
      expect(optionLabel).not.toBeNull();
      expect(optionLabel).toHaveAttribute('lang', option.value === 'system' ? 'en' : option.value);
      expect(optionLabel).toHaveAttribute('dir', option.value === 'ar' ? 'rtl' : 'ltr');
    }
  });
});
