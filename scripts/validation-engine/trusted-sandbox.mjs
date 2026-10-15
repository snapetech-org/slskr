import { closeSync, constants, fstatSync, lstatSync, openSync, readFileSync } from 'node:fs';
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
  let descriptor;
  try {
    descriptor = openSync(
      markerPath,
      constants.O_RDONLY | (constants.O_NOFOLLOW ?? 0),
    );
    const opened = fstatSync(descriptor);
    const named = lstatSync(markerPath);
    if (
      !opened.isFile() ||
      named.isSymbolicLink() ||
      named.dev !== opened.dev ||
      named.ino !== opened.ino ||
      readFileSync(descriptor, 'utf8') !== token
    ) {
      throw new Error('sandbox marker mismatch');
    }
  } catch {
    throw new Error(
      'Local test execution requires the trusted bubblewrap launcher.'
    );
  } finally {
    if (descriptor !== undefined) closeSync(descriptor);
  }
}
