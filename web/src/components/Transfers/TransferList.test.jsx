import '@testing-library/jest-dom';
import TransferList from './TransferList';
import { resetInterfaceLanguage, setInterfaceLanguage } from '../../lib/interfaceLocale';
import { setRegionalFormatPreference } from '../../lib/util';
import React from 'react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { render, screen } from '@testing-library/react';

afterEach(() => {
  resetInterfaceLanguage();
  setRegionalFormatPreference('system');
});

describe('TransferList', () => {
  it('localizes the supported aborted state as a failure', () => {
    setInterfaceLanguage('es');

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

  it('translates the initializing transfer state', () => {
    setInterfaceLanguage('es');

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
