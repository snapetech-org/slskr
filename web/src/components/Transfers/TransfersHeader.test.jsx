import '@testing-library/jest-dom';
import React from 'react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { act, render, screen } from '@testing-library/react';
import TransfersHeader from './TransfersHeader';
import { resetInterfaceLanguage, setInterfaceLanguage } from '../../lib/interfaceLocale';
import transferBulkActionLabels from '../../lib/transfer-bulk-action-labels.json';

const transfers = [
  {
    username: 'alice',
    directories: [
      {
        directory: 'Album',
        files: [
          {
            direction: 'download',
            filename: 'one.mp3',
            id: '1',
            state: 'Completed, Errored',
          },
        ],
      },
    ],
  },
];

afterEach(() => {
  resetInterfaceLanguage();
  vi.unstubAllGlobals();
});

describe('TransfersHeader', () => {
  it('renders a complete localized bulk action phrase', async () => {
    setInterfaceLanguage('ar');
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: true,
      json: async () => transferBulkActionLabels,
    }));

    render(
      <TransfersHeader
        direction="download"
        onCancelAll={() => {}}
        onRemoveAll={() => {}}
        onRetryAll={() => {}}
        transfers={transfers}
      />,
    );

    await act(async () => new Promise((resolve) => setTimeout(resolve, 0)));

    const label = screen.getByText('إعادة محاولة كل عمليات النقل التي بها أخطاء');
    expect(label).toHaveAttribute('lang', 'ar');
    expect(label).toHaveAttribute('dir', 'rtl');
  });
});
