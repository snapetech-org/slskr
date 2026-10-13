import '@testing-library/jest-dom';
import { createLogsHubConnection } from '../../../lib/hubFactory';
import { getLogs, updateLogLevel } from '../../../lib/options';
import Logs, { formatLogTimestamp } from './index';
import { setRegionalFormatPreference } from '../../../lib/util';
import { cleanup, render, screen } from '@testing-library/react';
import React from 'react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

vi.mock('../../../lib/hubFactory', () => ({
  createLogsHubConnection: vi.fn(),
}));

vi.mock('../../../lib/options', () => ({
  getLogs: vi.fn(),
  updateLogLevel: vi.fn(),
}));

describe('Logs', () => {
  beforeEach(() => {
    localStorage.clear();
    setRegionalFormatPreference('system');
    getLogs.mockRejectedValue({
      response: { data: { message: 'Log endpoint unavailable' } },
    });
    updateLogLevel.mockResolvedValue({ level: 'Information' });
    createLogsHubConnection.mockReturnValue({
      on: vi.fn(),
      onclose: vi.fn(),
      onreconnected: vi.fn(),
      onreconnecting: vi.fn(),
      start: vi.fn().mockResolvedValue(undefined),
      stop: vi.fn(),
    });
  });

  afterEach(() => {
    cleanup();
    setRegionalFormatPreference('system');
    localStorage.clear();
    vi.clearAllMocks();
  });

  it('surfaces initial log-load failures instead of showing an empty success state', async () => {
    render(<Logs />);

    expect(await screen.findByTestId('logs-error')).toHaveTextContent(
      'Log endpoint unavailable',
    );
    expect(screen.getByText('No logs are available from the server')).toBeInTheDocument();
    expect(screen.queryByText('No logs match the selected filter')).not.toBeInTheDocument();
  });

  it('formats log timestamps with the selected regional time and seconds', () => {
    localStorage.setItem(
      'slskr:experience-preferences:v1',
      JSON.stringify({ regionalFormat: 'de' }),
    );
    setRegionalFormatPreference('de');
    const timestamp = Date.UTC(2026, 9, 13, 12, 34, 56);
    const date = new Date(timestamp);

    expect(formatLogTimestamp(timestamp)).toBe(
      new Intl.DateTimeFormat('de', {
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
      }).format(date),
    );
  });
});
