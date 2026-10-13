import '@testing-library/jest-dom';
import TransferList from './TransferList';
import { resetInterfaceLanguage, setInterfaceLanguage } from '../../lib/interfaceLocale';
import React from 'react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { render, screen } from '@testing-library/react';

afterEach(() => resetInterfaceLanguage());

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
});
