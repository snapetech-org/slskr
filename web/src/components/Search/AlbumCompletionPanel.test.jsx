import React from 'react';
import { act, render, screen } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { setRegionalFormatPreference } from '../../lib/util';
import { fetchAlbumCompletion } from '../../lib/musicBrainz';
import AlbumCompletionPanel from './AlbumCompletionPanel';

vi.mock('../../lib/musicBrainz', () => ({
  fetchAlbumCompletion: vi.fn(),
}));

describe('AlbumCompletionPanel regional formatting', () => {
  beforeEach(() => {
    setRegionalFormatPreference('system');
    fetchAlbumCompletion.mockResolvedValue({
      data: {
        albums: [{
          completedTracks: 1_234,
          releaseId: 'release-1',
          totalTracks: 2_468,
          tracks: [{
            complete: false,
            durationMs: 184_000,
            position: 1_234,
            title: 'Example track',
          }],
        }],
      },
    });
  });

  afterEach(() => {
    setRegionalFormatPreference('system');
    vi.clearAllMocks();
  });

  it('updates visible track durations and counts after the regional choice changes', async () => {
    const { container } = render(<AlbumCompletionPanel disabled={false} />);

    await screen.findByText('Untitled album');
    expect(container.querySelector('.album-track-row .description'))
      .toHaveTextContent('03:04 min');
    expect(container.querySelector('.album-completion-meta span:last-child'))
      .toHaveTextContent('1,234/2,468');

    act(() => setRegionalFormatPreference('de'));

    expect(container.querySelector('.album-track-row .description'))
      .toHaveTextContent('03:04 min');
    expect(container.querySelector('.album-completion-meta span:last-child'))
      .toHaveTextContent('1.234/2.468');
  });
});
