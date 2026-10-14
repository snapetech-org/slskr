import '@testing-library/jest-dom';
import TransferList from './TransferList';
import SPANISH_LABELS from '../../lib/locales/ui-labels.es.json';
import { resetInterfaceLanguage, setInterfaceLanguage } from '../../lib/interfaceLocale';
import { setRegionalFormatPreference } from '../../lib/util';
import React from 'react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { act, render, screen } from '@testing-library/react';

beforeEach(() => {
  vi.stubGlobal('fetch', vi.fn(async () => ({
    ok: true,
    json: async () => SPANISH_LABELS,
  })));
});

afterEach(() => {
  resetInterfaceLanguage();
  setRegionalFormatPreference('system');
  vi.unstubAllGlobals();
});

describe('TransferList', () => {
  it('localizes the supported aborted state as a failure', async () => {
    await act(async () => { await setInterfaceLanguage('es'); });

    render(
      <TransferList
        directoryName="Album"
        files={[{
          direction: 'download',
          filename: 'aborted.mp3',
          id: 'aborted',
          size: 1,
          state: 'Completed, Aborted',
        }]}
        onPlaceInQueueRequested={vi.fn()}
        onRetryRequested={vi.fn()}
        onSelectionChange={vi.fn()}
      />,
    );

    expect(screen.getByText('Fallidos')).toHaveAttribute('lang', 'es');
  });

  it('translates the initializing transfer state', async () => {
    await act(async () => { await setInterfaceLanguage('es'); });

    render(
      <TransferList
        directoryName="Album"
        files={[{
          direction: 'download',
          filename: 'initializing.mp3',
          id: 'initializing',
          size: 1,
          state: 'Initializing',
        }]}
        onPlaceInQueueRequested={vi.fn()}
        onRetryRequested={vi.fn()}
        onSelectionChange={vi.fn()}
      />,
    );

    expect(screen.getByText('Iniciando')).toHaveAttribute('lang', 'es');
  });

  it('localizes the transferred-byte numerator with the regional format', () => {
    setRegionalFormatPreference('de');

    render(
      <TransferList
        directoryName="Album"
        files={[{
          bytesTransferred: 1_536,
          direction: 'download',
          filename: 'regional.mp3',
          id: 'regional',
          size: 2_048,
          state: 'InProgress',
        }]}
        onPlaceInQueueRequested={vi.fn()}
        onRetryRequested={vi.fn()}
        onSelectionChange={vi.fn()}
      />,
    );

    expect(screen.getByText('1,5 KB/2 KB')).toBeInTheDocument();
  });
});
