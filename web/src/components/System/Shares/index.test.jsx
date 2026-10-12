import '@testing-library/jest-dom';
import React from 'react';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { vi } from 'vitest';
import Shares from './index';

const { cancel, getAll, getState, rescan } = vi.hoisted(() => ({
  cancel: vi.fn(),
  getAll: vi.fn(),
  getState: vi.fn(),
  rescan: vi.fn(),
}));

vi.mock('../../../lib/shares', () => ({ cancel, getAll, rescan }));
vi.mock('../../../lib/application', () => ({ getState }));
vi.mock('../../../lib/errors', () => ({
  toDisplayError: (error, fallback) => error?.message ?? fallback,
}));
vi.mock('react-toastify', () => ({ toast: { error: vi.fn() } }));
vi.mock('semantic-ui-react', () => ({ Divider: () => <hr /> }));
vi.mock('../../Shared', () => ({
  LoaderSegment: ({ children }) => <div>{children}</div>,
  ShrinkableButton: ({ children, ...props }) => <button {...props}>{children}</button>,
  Switch: ({ children, loading, scanning, filling, empty }) =>
    loading || scanning || filling || empty || children,
}));
vi.mock('./ContentsModal', () => ({ default: () => null }));
vi.mock('./ExclusionTable', () => ({ default: () => null }));
vi.mock('./ShareTable', () => ({ default: () => null }));

describe('Shares scan progress', () => {
  beforeEach(() => {
    cancel.mockReset();
    getAll.mockReset().mockResolvedValue({});
    getState.mockReset().mockResolvedValue({
      shares: {
        directories: 0,
        files: 0,
        scanEntries: 1_234,
        scanPending: false,
        scanning: true,
      },
    });
    rescan.mockReset().mockResolvedValue({});
  });

  it('polls and renders the live entry count even when the supplied state is stale', async () => {
    const view = render(
      <Shares
        state={{
          directories: 2,
          files: 8,
          scanEntries: 0,
          scanPending: false,
          scanning: false,
        }}
      />,
    );

    fireEvent.click(await screen.findByRole('button', { name: 'Rescan Shares' }));

    await waitFor(() => {
      expect(getState).toHaveBeenCalled();
      expect(screen.getByText('Visited 1,234 filesystem entries')).toBeInTheDocument();
    });
    expect(screen.getByText('Scanning shares')).toBeInTheDocument();

    view.rerender(
      <Shares
        state={{
          directories: 2,
          files: 8,
          scanEntries: 0,
          scanPending: false,
          scanning: true,
        }}
      />,
    );
    expect(screen.getByText('Visited 1,234 filesystem entries')).toBeInTheDocument();
  });
});
