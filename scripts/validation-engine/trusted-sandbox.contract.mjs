import assert from 'node:assert/strict';
import { mkdtempSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import path from 'node:path';
import test from 'node:test';

import { requireTrustedLocalTestSandbox } from './trusted-sandbox.mjs';

test('requires an outer sandbox marker for local test execution', (t) => {
  const directory = mkdtempSync(path.join(tmpdir(), 'trusted-sandbox-test-'));
  t.after(() => rmSync(directory, { recursive: true, force: true }));
  const markerPath = path.join(directory, 'marker');
  const token = 'a'.repeat(64);

  assert.throws(
    () => requireTrustedLocalTestSandbox({ env: {}, markerPath }),
    /trusted bubblewrap launcher/u
  );
  writeFileSync(markerPath, 'b'.repeat(64));
  assert.throws(
    () =>
      requireTrustedLocalTestSandbox({
        env: { VALIDATION_OUTER_SANDBOX_TOKEN: token },
        markerPath,
      }),
    /trusted bubblewrap launcher/u
  );
  writeFileSync(markerPath, token);
  assert.doesNotThrow(() =>
    requireTrustedLocalTestSandbox({
      env: { VALIDATION_OUTER_SANDBOX_TOKEN: token },
      markerPath,
    })
  );
  assert.doesNotThrow(() =>
    requireTrustedLocalTestSandbox({ env: { GITHUB_ACTIONS: 'true' }, markerPath })
  );
});
