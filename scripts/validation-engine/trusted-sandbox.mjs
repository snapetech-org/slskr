import { lstatSync, readFileSync } from 'node:fs';
import process from 'node:process';

const TOKEN_PATTERN = /^[a-f0-9]{64}$/u;

export function requireTrustedLocalTestSandbox({
  env = process.env,
  markerPath = '/run/validation-engine-sandbox',
} = {}) {
  if (env.GITHUB_ACTIONS === 'true') return;
  const token = env.VALIDATION_OUTER_SANDBOX_TOKEN;
  if (typeof token !== 'string' || !TOKEN_PATTERN.test(token)) {
    throw new Error(
      'Local test execution requires the trusted bubblewrap launcher.'
    );
  }
  try {
    if (!lstatSync(markerPath).isFile() || readFileSync(markerPath, 'utf8') !== token) {
      throw new Error('sandbox marker mismatch');
    }
  } catch {
    throw new Error(
      'Local test execution requires the trusted bubblewrap launcher.'
    );
  }
}
