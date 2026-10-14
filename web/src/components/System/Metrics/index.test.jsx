import '@testing-library/jest-dom';
import { getKpiMetrics } from '../../../lib/telemetry';
import Metrics from './index';
import { setRegionalFormatPreference } from '../../../lib/util';
import React from 'react';
import { act, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

vi.mock('../../../lib/telemetry', () => ({
  getKpiMetrics: vi.fn(),
}));

vi.mock('../../Shared', () => ({
  LoaderSegment: () => <div>Loading metrics...</div>,
}));

describe('Metrics', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    setRegionalFormatPreference('system');
  });

  it('retains the last successful snapshot when a refresh fails', async () => {
    getKpiMetrics
      .mockResolvedValueOnce({
        slskr_uploads_total: {
          help: 'Uploads total',
          samples: [{ value: 3 }],
          type: 'counter',
        },
      })
      .mockRejectedValueOnce(new Error('metrics service unavailable'));

    render(<Metrics />);

    expect(await screen.findByText('Uploads Total')).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: /Updated/ }));

    expect(await screen.findByTestId('metrics-load-error')).toHaveTextContent(
      'metrics service unavailable',
    );
    expect(screen.getByText('Uploads Total')).toBeInTheDocument();
    expect(screen.getAllByText('3')).not.toHaveLength(0);
    await waitFor(() => expect(getKpiMetrics).toHaveBeenCalledTimes(2));
  });

  it('formats zero byte metrics with the selected regional digits', async () => {
    act(() => setRegionalFormatPreference('ar'));
    getKpiMetrics.mockResolvedValueOnce({
      process_working_set_bytes: {
        help: 'Working set bytes',
        samples: [{ value: 0 }],
        type: 'gauge',
      },
    });

    render(<Metrics />);

    const zero = new Intl.NumberFormat('ar').format(0);
    expect(await screen.findByText(`${zero} B`)).toBeInTheDocument();
  });

  it('reformats a mounted metric when the regional preference changes', async () => {
    getKpiMetrics.mockResolvedValueOnce({
      process_working_set_bytes: {
        help: 'Working set bytes',
        samples: [{ value: 0 }],
        type: 'gauge',
      },
    });

    render(<Metrics />);
    expect(await screen.findByText('0 B')).toBeInTheDocument();

    act(() => setRegionalFormatPreference('ar'));

    const zero = new Intl.NumberFormat('ar').format(0);
    expect(await screen.findByText(`${zero} B`)).toBeInTheDocument();
  });
});
