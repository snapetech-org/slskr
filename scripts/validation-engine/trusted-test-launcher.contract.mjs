// Copyright (c) snapetech and SeerrNG contributors.
import assert from 'node:assert/strict';
import { execFileSync, spawnSync } from 'node:child_process';
import {
  existsSync,
  mkdirSync,
  mkdtempSync,
  readFileSync,
  rmSync,
  symlinkSync,
  writeFileSync,
} from 'node:fs';
import { once } from 'node:events';
import { createServer } from 'node:net';
import { tmpdir } from 'node:os';
import path from 'node:path';
import test from 'node:test';
import { fileURLToPath } from 'node:url';
import {
  HOST_PATHS_TO_HIDE,
  hostPathsToHide,
  isSensitiveCandidatePath,
  sandboxMountOperations,
} from './trusted-test-sandbox-policy.mjs';

const launcher = fileURLToPath(
  new URL(
    './trusted-test-launcher.mjs',
    import.meta.url
  )
);
for (const hostPath of ['/etc', '/opt', '/srv', '/usr/local'])
  assert.ok(
    HOST_PATHS_TO_HIDE.includes(hostPath),
    `the sandbox must hide host path ${hostPath}`
  );
const bwrap = ['/usr/bin/bwrap', '/bin/bwrap'].find(existsSync);
const sandboxAvailable = (() => {
  if (process.platform !== 'linux' || !bwrap) return false;
  return (
    spawnSync(
      bwrap,
      [
        '--die-with-parent',
        '--unshare-user',
        '--ro-bind',
        '/',
        '/',
        '--',
        '/bin/true',
      ],
      { stdio: 'ignore' }
    ).status === 0
  );
})();

test('preserves tracked source files named token while excluding credential config files', () => {
  assert.equal(isSensitiveCandidatePath('web/src/lib/token.js'), false);
  assert.equal(isSensitiveCandidatePath('client-go/auth/client.go'), false);
  assert.equal(isSensitiveCandidatePath('client-python/auth/__init__.py'), false);
  assert.equal(isSensitiveCandidatePath('client-go/auth/api-key.go'), true);
  assert.equal(isSensitiveCandidatePath('client-python/auth/client-secret.py'), true);
  assert.equal(isSensitiveCandidatePath('vendor/mainline/src/rpc/server/tokens.rs'), false);
  assert.equal(isSensitiveCandidatePath('src/authentication.ts'), false);
  assert.equal(isSensitiveCandidatePath('src/auth.ts'), false);
  assert.equal(isSensitiveCandidatePath('src/token.ts'), true);
  assert.equal(isSensitiveCandidatePath('src/auth.rs'), true);
  assert.equal(isSensitiveCandidatePath('src/credentials.py'), true);
  assert.equal(isSensitiveCandidatePath('src/secrets.js'), true);
  assert.equal(isSensitiveCandidatePath('ops/production-auth.json'), true);
  assert.equal(isSensitiveCandidatePath('token.production.env'), true);
  assert.equal(isSensitiveCandidatePath('credentials.prod.toml'), true);
  assert.equal(isSensitiveCandidatePath('secrets-production.yaml'), true);
  assert.equal(isSensitiveCandidatePath('token.uat.json'), true);
  assert.equal(isSensitiveCandidatePath('credentials.preprod.toml'), true);
  assert.equal(isSensitiveCandidatePath('secrets-sandbox.yaml'), true);
  assert.equal(isSensitiveCandidatePath('ops/secrets-production/value.json'), true);
  assert.equal(isSensitiveCandidatePath('ops/credentials.prod/value.json'), true);
  assert.equal(isSensitiveCandidatePath('ops/token.uat/value.json'), true);
  assert.equal(isSensitiveCandidatePath('ops/credentials.sandbox/value.json'), true);
  assert.equal(isSensitiveCandidatePath('web/src/designTokens.ts'), false);
  assert.equal(isSensitiveCandidatePath('src/cancellationToken.ts'), false);
  assert.equal(isSensitiveCandidatePath('scripts/check-browser-token-persistence.sh'), false);
  assert.equal(isSensitiveCandidatePath('scripts/check-secret-scanning.sh'), false);
  assert.equal(isSensitiveCandidatePath('scripts/check-web-auth-credentials-differential.sh'), false);
  assert.equal(isSensitiveCandidatePath('release-notes/20261013-validation-snapshot-credential-filter.md'), false);
  assert.equal(isSensitiveCandidatePath('release-notes/20261013-validation-snapshot-credentials.md'), false);
  assert.equal(
    isSensitiveCandidatePath('crates/slskr/src/private_gateway_owners/peer_authentication.rs'),
    false,
  );
  assert.equal(
    isSensitiveCandidatePath('crates/slskr/data/peer-controller-auth-policy.json'),
    false,
  );
  assert.equal(isSensitiveCandidatePath('src/client-secret.ts'), true);
  assert.equal(isSensitiveCandidatePath('packages/app/api-key.js'), true);
  assert.equal(isSensitiveCandidatePath('src/access-token.ts'), true);
  assert.equal(isSensitiveCandidatePath('ops/secrets/production.ts'), true);
  assert.equal(isSensitiveCandidatePath('src/credentials/TokenStore.ts'), false);
  assert.equal(isSensitiveCandidatePath('auth'), true);
  assert.equal(isSensitiveCandidatePath('nested/tokens'), true);
  assert.equal(isSensitiveCandidatePath('credentials'), true);
  assert.equal(isSensitiveCandidatePath('secrets'), true);
  assert.equal(isSensitiveCandidatePath('nested/secrets.env'), true);
  assert.equal(isSensitiveCandidatePath('auth.json'), true);
  assert.equal(isSensitiveCandidatePath('nested/config/secrets.yaml'), true);
  assert.equal(isSensitiveCandidatePath('.env.local'), true);
  assert.equal(isSensitiveCandidatePath('.token'), true);
  assert.equal(isSensitiveCandidatePath('.auth'), true);
  assert.equal(isSensitiveCandidatePath('.credentials'), true);
  assert.equal(isSensitiveCandidatePath('.secrets'), true);
  assert.equal(isSensitiveCandidatePath('packages/auth/.token'), true);
  assert.equal(isSensitiveCandidatePath('tokens.env'), true);
  assert.equal(isSensitiveCandidatePath('tokens.env.local'), true);
  assert.equal(isSensitiveCandidatePath('secrets.env.production'), true);
  assert.equal(isSensitiveCandidatePath('tokens.env.example'), false);
  assert.equal(isSensitiveCandidatePath('nested/credentials/private-key'), true);
  assert.equal(isSensitiveCandidatePath('nested/credentials/private-key.ts'), true);
  assert.equal(isSensitiveCandidatePath('api-key.json'), true);
  assert.equal(isSensitiveCandidatePath('.private-key.ts'), true);
  assert.equal(isSensitiveCandidatePath('access-token.json'), true);
  assert.equal(isSensitiveCandidatePath('refresh_token.yaml'), true);
  assert.equal(isSensitiveCandidatePath('client-secret.ts'), true);
  assert.equal(isSensitiveCandidatePath('production-api-key.json'), true);
  assert.equal(isSensitiveCandidatePath('production-token.json'), true);
  assert.equal(isSensitiveCandidatePath('github-secrets.yaml'), true);
  assert.equal(isSensitiveCandidatePath('acme-credentials.toml'), true);
  assert.equal(isSensitiveCandidatePath('api.key.json'), true);
  assert.equal(isSensitiveCandidatePath('production.private.key.json'), true);
  assert.equal(isSensitiveCandidatePath('github.access.token.ts'), true);
  assert.equal(isSensitiveCandidatePath('src/apiKey.ts'), true);
  assert.equal(isSensitiveCandidatePath('src/apiKeys.js'), true);
  assert.equal(isSensitiveCandidatePath('src/productionApiKey.ts'), true);
  assert.equal(isSensitiveCandidatePath('src/productionToken.ts'), true);
  assert.equal(isSensitiveCandidatePath('src/productionPrivateKey.ts'), true);
  assert.equal(isSensitiveCandidatePath('githubAccessToken.js'), true);
  assert.equal(isSensitiveCandidatePath('productionAPIKey.ts'), true);
  assert.equal(isSensitiveCandidatePath('src/github-access-token.ts'), true);
  assert.equal(isSensitiveCandidatePath('src/myToken.ts'), false);
  assert.equal(isSensitiveCandidatePath('ops/acme-client-secret.env'), true);
  assert.equal(isSensitiveCandidatePath('src/mytoken.ts'), false);
  assert.equal(isSensitiveCandidatePath('src/tokens/index.ts'), false);
  assert.equal(isSensitiveCandidatePath('nested/credentials/TokenStore.ts'), true);
  assert.equal(isSensitiveCandidatePath('dashboard/src/pages/ApiKeys.tsx'), false);
  assert.equal(isSensitiveCandidatePath('dashboard/src/pages/ApiKeys.jsx'), true);
  assert.equal(isSensitiveCandidatePath('dashboard/src/pages/apiKeys.tsx'), true);
  assert.equal(isSensitiveCandidatePath('web/src/lib/ApiKeys.tsx'), true);
  assert.equal(isSensitiveCandidatePath('ops/production-secrets/value.json'), true);
  assert.equal(isSensitiveCandidatePath('ops/github-tokens/value.json'), true);
  assert.equal(isSensitiveCandidatePath('auth-service/src/index.js'), false);
  assert.equal(isSensitiveCandidatePath('token-parser/src/index.js'), false);
  assert.equal(isSensitiveCandidatePath('secrets-manager/src/index.js'), false);
  assert.equal(isSensitiveCandidatePath('src/production-secrets/schema.ts'), false);
  assert.equal(isSensitiveCandidatePath('packages/auth/package.json'), false);
  assert.equal(isSensitiveCandidatePath('src/tokens/schema.json'), false);
  assert.equal(isSensitiveCandidatePath('packages/auth/scripts/setup.sh'), false);
});

test('opens required host sources before masking their parent directories', () => {
  const hiddenDirectories = hostPathsToHide('/home/runner/work/slskr')
    .filter((directory) => ['/home', '/tmp', '/usr/local', '/mnt'].includes(directory));
  const operations = sandboxMountOperations({
    workspace: '/home/runner/work/slskr',
    runDirectory: '/home/runner/work/_temp/validation-run',
    externalMounts: [['/usr/local/bin/node', '/mnt/run-data/dependencies/0']],
    dependencyMounts: [['/home/runner/work/slskr/web/node_modules/react', '/mnt/workspace/web/node_modules/react']],
    hiddenDirectories,
    guestWorkspace: '/mnt/workspace',
    guestRun: '/mnt/run-data',
    markerFile: '/home/runner/work/_temp/validation-run/sandbox-marker',
    guestMarker: '/run/validation-engine-sandbox',
  });
  const finalHostMask = Math.max(...operations
    .map((operation, index) => operation.hostMask ? index : -1));
  const descriptorBinds = operations.filter((operation) =>
    operation.type === 'bind-fd' || operation.type === 'ro-bind-fd');

  assert.equal(operations.filter((operation) => operation.hostMask).length, hiddenDirectories.length);
  assert.ok(descriptorBinds.length > 0);
  assert.ok(operations.indexOf(descriptorBinds[0]) > finalHostMask);
  assert.deepEqual(
    descriptorBinds.map(({ type, source, target }) => ({ type, source, target })),
    [
      { type: 'bind-fd', source: '/home/runner/work/slskr', target: '/mnt/workspace' },
      { type: 'bind-fd', source: '/home/runner/work/_temp/validation-run', target: '/mnt/run-data' },
      { type: 'ro-bind-fd', source: '/usr/local/bin/node', target: '/mnt/run-data/dependencies/0' },
      { type: 'ro-bind-fd', source: '/home/runner/work/slskr/web/node_modules/react', target: '/mnt/workspace/web/node_modules/react' },
      { type: 'ro-bind-fd', source: '/home/runner/work/_temp/validation-run/sandbox-marker', target: '/run/validation-engine-sandbox' },
    ]
  );
});

test(
  'trusted launcher contains import-time candidate code before it runs',
  { skip: !sandboxAvailable && 'bubblewrap user namespaces are unavailable' },
  async (t) => {
    const parent = mkdtempSync(
      path.join(tmpdir(), 'trusted-validation-launcher-')
    );
    const source = path.join(parent, 'candidate');
    const hostFile = path.join(parent, 'host-canary.txt');
    const browserCache = path.join(parent, 'playwright-cache');
    const outsideDependencies = path.join(parent, 'outside-dependencies');
    const hostSocket = path.join(parent, 'host-canary.sock');
    const candidateWrite = path.join(source, 'launcher-write-canary.txt');
    mkdirSync(path.join(source, 'bin'), { recursive: true });
    mkdirSync(browserCache, { recursive: true });
    mkdirSync(outsideDependencies, { recursive: true });
    const tcpServer = createServer();
    tcpServer.listen(0, '127.0.0.1');
    await once(tcpServer, 'listening');
    const socketServer = createServer();
    socketServer.listen(hostSocket);
    await once(socketServer, 'listening');
    t.after(async () => {
      if (tcpServer.listening)
        await new Promise((resolve) => tcpServer.close(resolve));
      if (socketServer.listening)
        await new Promise((resolve) => socketServer.close(resolve));
      rmSync(parent, { recursive: true, force: true });
    });
    mkdirSync(path.join(source, 'nested/config'), { recursive: true });
    mkdirSync(path.join(source, 'src'), { recursive: true });
    mkdirSync(path.join(source, 'packages/app'), { recursive: true });
    mkdirSync(path.join(source, 'ops/secrets'), { recursive: true });
    mkdirSync(path.join(source, 'ops/production-secrets'), { recursive: true });
    mkdirSync(path.join(source, 'ops/secrets-production'), { recursive: true });
    mkdirSync(path.join(source, 'ops/credentials.prod'), { recursive: true });
    mkdirSync(path.join(source, 'ops/token.uat'), { recursive: true });
    mkdirSync(path.join(source, 'ops/credentials.sandbox'), { recursive: true });
    mkdirSync(path.join(source, 'ops/github-tokens'), { recursive: true });
    mkdirSync(path.join(source, 'auth-service/src'), { recursive: true });
    mkdirSync(path.join(source, 'token-parser/src'), { recursive: true });
    mkdirSync(path.join(source, 'secrets-manager/src'), { recursive: true });
    mkdirSync(path.join(source, 'src/production-secrets'), { recursive: true });
    mkdirSync(path.join(source, 'client-go/auth'), { recursive: true });
    mkdirSync(path.join(source, 'client-python/auth'), { recursive: true });
    mkdirSync(path.join(source, 'web/src/lib'), { recursive: true });
    mkdirSync(path.join(source, 'dashboard/src/pages'), { recursive: true });
    mkdirSync(path.join(source, 'vendor/mainline/src/rpc/server'), { recursive: true });
    mkdirSync(path.join(source, 'scripts'), { recursive: true });
    mkdirSync(path.join(source, 'release-notes'), { recursive: true });
    mkdirSync(path.join(source, 'crates/slskr/src/private_gateway_owners'), { recursive: true });
    mkdirSync(path.join(source, 'crates/slskr/data'), { recursive: true });
    writeFileSync(path.join(source, 'web/src/lib/token.js'), 'export const token = "source code";\n');
    writeFileSync(path.join(source, 'client-go/auth/client.go'), 'package auth\nfunc Client() {}\n');
    writeFileSync(path.join(source, 'client-python/auth/__init__.py'), 'def login(): return None\n');
    writeFileSync(path.join(source, 'client-go/auth/api-key.go'), 'package auth\nconst APIKey = "hidden"\n');
    writeFileSync(path.join(source, 'client-python/auth/client-secret.py'), 'CLIENT_SECRET = "hidden"\n');
    writeFileSync(
      path.join(source, 'dashboard/src/pages/ApiKeys.tsx'),
      'export default function ApiKeys() { return null; }\n',
    );
    writeFileSync(
      path.join(source, 'dashboard/src/pages/apiKeys.tsx'),
      'export const apiKeys = "credential canary";\n',
    );
    writeFileSync(
      path.join(source, 'dashboard/src/pages/ApiKeys.jsx'),
      'export const API_KEYS_CANARY = "hidden";\n',
    );
    writeFileSync(
      path.join(source, 'web/src/lib/ApiKeys.tsx'),
      'export const API_KEYS_CANARY = "hidden";\n',
    );
    writeFileSync(path.join(source, 'src/apiKey.ts'), 'export const API_KEY_CANARY = "hidden";\n');
    writeFileSync(path.join(source, 'src/apiKeys.js'), 'export const API_KEYS_CANARY = "hidden";\n');
    writeFileSync(path.join(source, 'src/productionApiKey.ts'), 'export const API_KEY_CANARY = "hidden";\n');
    writeFileSync(path.join(source, 'src/productionPrivateKey.ts'), 'export const PRIVATE_KEY_CANARY = "hidden";\n');
    writeFileSync(path.join(source, 'src/productionToken.ts'), 'export const TOKEN_CANARY = "hidden";\n');
    writeFileSync(path.join(source, 'src/token.ts'), 'export const TOKEN_CANARY = "hidden";\n');
    writeFileSync(path.join(source, 'src/auth.rs'), 'const TOKEN_CANARY: &str = "hidden";\n');
    writeFileSync(path.join(source, 'src/credentials.py'), 'TOKEN_CANARY = "hidden"\n');
    writeFileSync(path.join(source, 'src/secrets.js'), 'export const TOKEN_CANARY = "hidden";\n');
    writeFileSync(path.join(source, 'ops/production-auth.json'), '{"token":"hidden"}\n');
    writeFileSync(path.join(source, 'token.production.env'), 'TOKEN_CANARY=hidden\n');
    writeFileSync(path.join(source, 'credentials.prod.toml'), 'TOKEN_CANARY="hidden"\n');
    writeFileSync(path.join(source, 'secrets-production.yaml'), 'token: hidden\n');
    writeFileSync(path.join(source, 'token.uat.json'), '{"token":"hidden"}\n');
    writeFileSync(path.join(source, 'credentials.preprod.toml'), 'TOKEN_CANARY="hidden"\n');
    writeFileSync(path.join(source, 'secrets-sandbox.yaml'), 'token: hidden\n');
    writeFileSync(path.join(source, 'ops/secrets-production/value.json'), '{"token":"hidden"}\n');
    writeFileSync(path.join(source, 'ops/credentials.prod/value.json'), '{"token":"hidden"}\n');
    writeFileSync(path.join(source, 'ops/token.uat/value.json'), '{"token":"hidden"}\n');
    writeFileSync(path.join(source, 'ops/credentials.sandbox/value.json'), '{"token":"hidden"}\n');
    writeFileSync(path.join(source, 'web/src/designTokens.ts'), 'export const designTokens = {};\n');
    writeFileSync(path.join(source, 'src/cancellationToken.ts'), 'export const cancellationToken = {};\n');
    writeFileSync(path.join(source, 'scripts/check-browser-token-persistence.sh'), '#!/bin/sh\nexit 0\n');
    writeFileSync(path.join(source, 'scripts/check-secret-scanning.sh'), '#!/bin/sh\nexit 0\n');
    writeFileSync(path.join(source, 'scripts/check-web-auth-credentials-differential.sh'), '#!/bin/sh\nexit 0\n');
    writeFileSync(path.join(source, 'release-notes/20261013-validation-snapshot-credential-filter.md'), 'Validation snapshots filter secrets safely.\n');
    writeFileSync(path.join(source, 'release-notes/20261013-validation-snapshot-credentials.md'), 'Credential matching avoids checker files.\n');
    writeFileSync(
      path.join(source, 'crates/slskr/src/private_gateway_owners/peer_authentication.rs'),
      'pub fn peer_authentication() {}\n',
    );
    writeFileSync(
      path.join(source, 'crates/slskr/data/peer-controller-auth-policy.json'),
      '{"policy":"source metadata"}\n',
    );
    writeFileSync(path.join(source, 'githubAccessToken.js'), 'export const TOKEN_CANARY = "hidden";\n');
    writeFileSync(path.join(source, 'productionAPIKey.ts'), 'export const API_KEY_CANARY = "hidden";\n');
    writeFileSync(path.join(source, 'api.key.json'), '{"api_key":"hidden"}');
    writeFileSync(path.join(source, 'production.private.key.json'), '{"private_key":"hidden"}');
    writeFileSync(path.join(source, 'github.access.token.ts'), 'export const TOKEN_CANARY = "hidden";\n');
    writeFileSync(path.join(source, 'vendor/mainline/src/rpc/server/tokens.rs'), 'pub fn tokens() {}\n');
    writeFileSync(hostFile, 'host canary stays unchanged');
    writeFileSync(path.join(browserCache, 'browser-canary.txt'), 'read-only browser');
    writeFileSync(path.join(source, '.gitignore'), 'node_modules/\n');
    writeFileSync(path.join(source, '.env'), 'PRIVATE_ENV_CANARY=hidden\n');
    writeFileSync(path.join(source, 'production-api-key.json'), '{"api_key":"hidden"}');
    writeFileSync(path.join(source, 'production-token.json'), '{"token":"hidden"}');
    writeFileSync(path.join(source, 'github-secrets.yaml'), 'token: hidden\n');
    writeFileSync(path.join(source, 'acme-credentials.toml'), 'token="hidden"\n');
    writeFileSync(path.join(source, 'auth-service/src/index.js'), 'export const service = true;\n');
    writeFileSync(path.join(source, 'token-parser/src/index.js'), 'export const parser = true;\n');
    writeFileSync(path.join(source, 'secrets-manager/src/index.js'), 'export const manager = true;\n');
    writeFileSync(path.join(source, 'config.json'), '{"private":true}\n');
    writeFileSync(
      path.join(source, 'nested/.env.local'),
      'NESTED_ENV_CANARY=hidden\n'
    );
    writeFileSync(
      path.join(source, 'nested/config/secrets.json'),
      '{"secret":"hidden"}\n'
    );
    writeFileSync(path.join(source, 'auth.json'), '{"token":"private"}\n');
    writeFileSync(path.join(source, 'token.json'), '{"token":"private"}\n');
    writeFileSync(path.join(source, 'tokens.env'), 'PRIVATE_TOKENS_CANARY=hidden\n');
    writeFileSync(path.join(source, 'tokens.env.local'), 'SUFFIXED_TOKEN_CANARY=hidden\n');
    writeFileSync(path.join(source, 'secrets.env.production'), 'SUFFIXED_SECRET_CANARY=hidden\n');
    writeFileSync(path.join(source, 'tokens.env.example'), 'EXAMPLE_TOKEN_TEMPLATE=visible\n');
    mkdirSync(path.join(source, 'nested/credentials'), { recursive: true });
    writeFileSync(path.join(source, 'nested/credentials/private-key'), 'private credential\n');
    writeFileSync(path.join(source, '.token'), 'DOT_TOKEN_CANARY=hidden\n');
    writeFileSync(path.join(source, '.auth'), 'DOT_AUTH_CANARY=hidden\n');
    writeFileSync(path.join(source, '.credentials'), 'DOT_CREDENTIALS_CANARY=hidden\n');
    writeFileSync(path.join(source, '.secrets'), 'DOT_SECRETS_CANARY=hidden\n');
    writeFileSync(path.join(source, 'api-key.json'), '{"api_key":"hidden"}\\n');
    writeFileSync(path.join(source, 'access-token.json'), '{"access_token":"hidden"}\\n');
    writeFileSync(path.join(source, 'refresh_token.yaml'), 'refresh_token: hidden\\n');
    writeFileSync(path.join(source, 'client-secret.ts'), 'CLIENT_SECRET_CANARY=hidden\\n');
    writeFileSync(path.join(source, 'src/client-secret.ts'), 'SOURCE_CLIENT_SECRET_CANARY=hidden\\n');
    writeFileSync(path.join(source, 'src/github-access-token.ts'), 'GITHUB_ACCESS_TOKEN_CANARY=hidden');
    writeFileSync(path.join(source, 'src/mytoken.ts'), 'export const mytoken = "ordinary source";');
    writeFileSync(path.join(source, 'src/myToken.ts'), 'export const myToken = "ordinary source";');
    writeFileSync(path.join(source, 'ops/production-secrets/value.json'), '{"secret":"hidden"}');
    writeFileSync(path.join(source, 'ops/github-tokens/value.json'), '{"token":"hidden"}');
    writeFileSync(path.join(source, 'src/production-secrets/schema.ts'), 'export const schema = "source asset";');
    writeFileSync(path.join(source, 'packages/app/api-key.js'), 'export const API_KEY_CANARY = "hidden";\\n');
    writeFileSync(path.join(source, 'ops/secrets/production.ts'), 'export const TOKEN_CANARY = "hidden";\\n');
    writeFileSync(path.join(source, 'ops/acme-client-secret.env'), 'ACME_SECRET_CANARY=hidden');
    writeFileSync(path.join(source, '.private-key.ts'), 'PRIVATE_KEY_CANARY=hidden\\n');
    writeFileSync(path.join(source, 'nested/credentials/TokenStore.ts'), 'export const source = "nested credential source";\\n');
    mkdirSync(path.join(source, 'packages/auth/scripts'), { recursive: true });
    writeFileSync(
      path.join(source, 'packages/auth/package.json'),
      '{"name":"fixture-auth-package","type":"module"}\n',
    );
    writeFileSync(
      path.join(source, 'packages/auth/scripts/setup.sh'),
      '#!/bin/sh\nprintf "auth package asset\\n"\n',
    );
    mkdirSync(path.join(source, 'src/tokens'), { recursive: true });
    writeFileSync(path.join(source, 'src/tokens/index.ts'), 'export const source = "token directory source";\n');
    writeFileSync(
      path.join(source, 'src/tokens/schema.json'),
      '{"schema":"token asset"}\n',
    );
    mkdirSync(path.join(source, 'src/tokens/fixtures'), { recursive: true });
    writeFileSync(
      path.join(source, 'src/tokens/fixtures/sample.json'),
      '{"fixture":"token asset"}\n',
    );
    mkdirSync(path.join(source, 'src/tokens/templates'), { recursive: true });
    writeFileSync(
      path.join(source, 'src/tokens/templates/config.hbs'),
      'token template asset\n',
    );
    writeFileSync(path.join(source, 'credentials'), 'private credential\n');
    mkdirSync(path.join(source, 'node_modules'), { recursive: true });
    writeFileSync(
      path.join(source, 'node_modules/marker.txt'),
      'read-only dependency'
    );
    mkdirSync(path.join(source, 'node_modules/fixture-dependency'));
    writeFileSync(
      path.join(source, 'node_modules/fixture-dependency/package.json'),
      '{"name":"fixture-dependency","type":"module","exports":"./index.js"}\n'
    );
    writeFileSync(
      path.join(source, 'node_modules/fixture-dependency/index.js'),
      'export default "sibling dependency resolved";\n'
    );
    writeFileSync(
      path.join(source, 'bin/run-local-validation.mjs'),
      `import assert from 'node:assert/strict';
import { existsSync, readFileSync, writeFileSync } from 'node:fs';
import net from 'node:net';
import path from 'node:path';
import fixtureDependency from 'fixture-dependency';
const hostFile = ${JSON.stringify(hostFile)};
const hostSocket = ${JSON.stringify(hostSocket)};
const hostPort = ${tcpServer.address().port};
assert.throws(() => readFileSync(hostFile), { code: 'ENOENT' });
assert.equal(process.env.SECRET_CANARY, undefined);
assert.equal(existsSync('/mnt/workspace/.env'), false);
assert.equal(existsSync('/mnt/workspace/config.json'), true);
assert.equal(existsSync('/mnt/workspace/production-api-key.json'), false);
assert.equal(existsSync('/mnt/workspace/nested/config/operator.json'), false);
assert.equal(existsSync('/mnt/workspace/auth.json'), false);
assert.equal(existsSync('/mnt/workspace/token.json'), false);
assert.equal(existsSync('/mnt/workspace/tokens.env'), false);
assert.equal(existsSync('/mnt/workspace/tokens.env.local'), false);
assert.equal(existsSync('/mnt/workspace/secrets.env.production'), false);
assert.equal(readFileSync('/mnt/workspace/tokens.env.example', 'utf8'), 'EXAMPLE_TOKEN_TEMPLATE=visible\\n');
assert.equal(existsSync('/mnt/workspace/.token'), false);
assert.equal(existsSync('/mnt/workspace/.auth'), false);
assert.equal(existsSync('/mnt/workspace/.credentials'), false);
assert.equal(existsSync('/mnt/workspace/.secrets'), false);
assert.equal(existsSync('/mnt/workspace/api-key.json'), false);
assert.equal(existsSync('/mnt/workspace/access-token.json'), false);
assert.equal(existsSync('/mnt/workspace/refresh_token.yaml'), false);
assert.equal(existsSync('/mnt/workspace/client-secret.ts'), false);
assert.equal(existsSync('/mnt/workspace/src/client-secret.ts'), false);
assert.equal(existsSync('/mnt/workspace/src/github-access-token.ts'), false);
assert.equal(existsSync('/mnt/workspace/src/apiKey.ts'), false);
assert.equal(existsSync('/mnt/workspace/src/apiKeys.js'), false);
assert.equal(existsSync('/mnt/workspace/src/productionApiKey.ts'), false);
assert.equal(existsSync('/mnt/workspace/src/productionPrivateKey.ts'), false);
assert.equal(existsSync('/mnt/workspace/src/productionToken.ts'), false);
assert.equal(existsSync('/mnt/workspace/src/token.ts'), false);
assert.equal(existsSync('/mnt/workspace/src/auth.rs'), false);
assert.equal(existsSync('/mnt/workspace/src/credentials.py'), false);
assert.equal(existsSync('/mnt/workspace/src/secrets.js'), false);
assert.equal(existsSync('/mnt/workspace/ops/production-auth.json'), false);
assert.equal(existsSync('/mnt/workspace/token.production.env'), false);
assert.equal(existsSync('/mnt/workspace/credentials.prod.toml'), false);
assert.equal(existsSync('/mnt/workspace/secrets-production.yaml'), false);
assert.equal(existsSync('/mnt/workspace/token.uat.json'), false);
assert.equal(existsSync('/mnt/workspace/credentials.preprod.toml'), false);
assert.equal(existsSync('/mnt/workspace/secrets-sandbox.yaml'), false);
assert.equal(existsSync('/mnt/workspace/ops/secrets-production'), false);
assert.equal(existsSync('/mnt/workspace/ops/credentials.prod'), false);
assert.equal(existsSync('/mnt/workspace/ops/token.uat'), false);
assert.equal(existsSync('/mnt/workspace/ops/credentials.sandbox'), false);
assert.equal(readFileSync('/mnt/workspace/web/src/designTokens.ts', 'utf8'), 'export const designTokens = {};\\n');
assert.equal(readFileSync('/mnt/workspace/src/cancellationToken.ts', 'utf8'), 'export const cancellationToken = {};\\n');
assert.equal(readFileSync('/mnt/workspace/scripts/check-browser-token-persistence.sh', 'utf8'), '#!/bin/sh\\nexit 0\\n');
assert.equal(readFileSync('/mnt/workspace/scripts/check-secret-scanning.sh', 'utf8'), '#!/bin/sh\\nexit 0\\n');
assert.equal(readFileSync('/mnt/workspace/scripts/check-web-auth-credentials-differential.sh', 'utf8'), '#!/bin/sh\\nexit 0\\n');
assert.equal(readFileSync('/mnt/workspace/release-notes/20261013-validation-snapshot-credential-filter.md', 'utf8'), 'Validation snapshots filter secrets safely.\\n');
assert.equal(readFileSync('/mnt/workspace/release-notes/20261013-validation-snapshot-credentials.md', 'utf8'), 'Credential matching avoids checker files.\\n');
assert.match(readFileSync('/mnt/workspace/crates/slskr/src/private_gateway_owners/peer_authentication.rs', 'utf8'), /peer_authentication/u);
assert.equal(readFileSync('/mnt/workspace/crates/slskr/data/peer-controller-auth-policy.json', 'utf8'), '{"policy":"source metadata"}\\n');
assert.equal(existsSync('/mnt/workspace/production-token.json'), false);
assert.equal(existsSync('/mnt/workspace/github-secrets.yaml'), false);
assert.equal(existsSync('/mnt/workspace/acme-credentials.toml'), false);
assert.equal(existsSync('/mnt/workspace/githubAccessToken.js'), false);
assert.equal(existsSync('/mnt/workspace/productionAPIKey.ts'), false);
assert.equal(existsSync('/mnt/workspace/api.key.json'), false);
assert.equal(existsSync('/mnt/workspace/production.private.key.json'), false);
assert.equal(existsSync('/mnt/workspace/github.access.token.ts'), false);
assert.equal(readFileSync('/mnt/workspace/src/mytoken.ts', 'utf8'), 'export const mytoken = "ordinary source";');
assert.equal(readFileSync('/mnt/workspace/src/myToken.ts', 'utf8'), 'export const myToken = "ordinary source";');
assert.equal(existsSync('/mnt/workspace/ops/production-secrets/value.json'), false);
assert.equal(existsSync('/mnt/workspace/ops/github-tokens/value.json'), false);
assert.match(readFileSync('/mnt/workspace/auth-service/src/index.js', 'utf8'), /service/u);
assert.match(readFileSync('/mnt/workspace/token-parser/src/index.js', 'utf8'), /parser/u);
assert.match(readFileSync('/mnt/workspace/secrets-manager/src/index.js', 'utf8'), /manager/u);
assert.equal(readFileSync('/mnt/workspace/src/production-secrets/schema.ts', 'utf8'), 'export const schema = "source asset";');
assert.equal(existsSync('/mnt/workspace/dashboard/src/pages/apiKeys.tsx'), false);
assert.equal(existsSync('/mnt/workspace/dashboard/src/pages/ApiKeys.jsx'), false);
assert.equal(existsSync('/mnt/workspace/web/src/lib/ApiKeys.tsx'), false);
assert.equal(existsSync('/mnt/workspace/packages/app/api-key.js'), false);
assert.equal(existsSync('/mnt/workspace/ops/secrets/production.ts'), false);
assert.equal(existsSync('/mnt/workspace/ops/acme-client-secret.env'), false);
assert.equal(existsSync('/mnt/workspace/.private-key.ts'), false);
assert.equal(existsSync('/mnt/workspace/nested/credentials/TokenStore.ts'), false);
assert.equal(existsSync('/mnt/workspace/nested/credentials/private-key'), false);
assert.equal(readFileSync('/mnt/workspace/packages/auth/package.json', 'utf8'), '{"name":"fixture-auth-package","type":"module"}\\n');
assert.match(readFileSync('/mnt/workspace/packages/auth/scripts/setup.sh', 'utf8'), /auth package asset/u);
assert.match(readFileSync('/mnt/workspace/src/tokens/index.ts', 'utf8'), /token directory source/u);
assert.equal(readFileSync('/mnt/workspace/src/tokens/schema.json', 'utf8'), '{"schema":"token asset"}\\n');
assert.equal(readFileSync('/mnt/workspace/src/tokens/fixtures/sample.json', 'utf8'), '{"fixture":"token asset"}\\n');
assert.match(readFileSync('/mnt/workspace/src/tokens/templates/config.hbs', 'utf8'), /token template asset/u);
assert.equal(existsSync('/mnt/workspace/credentials'), false);
assert.equal(readFileSync('/mnt/workspace/dashboard/src/pages/ApiKeys.tsx', 'utf8'), 'export default function ApiKeys() { return null; }\\n');
assert.equal(readFileSync('/mnt/workspace/web/src/lib/token.js', 'utf8'), 'export const token = "source code";\\n');
assert.equal(readFileSync('/mnt/workspace/client-go/auth/client.go', 'utf8'), 'package auth\\nfunc Client() {}\\n');
assert.equal(readFileSync('/mnt/workspace/client-python/auth/__init__.py', 'utf8'), 'def login(): return None\\n');
assert.equal(existsSync('/mnt/workspace/client-go/auth/api-key.go'), false);
assert.equal(existsSync('/mnt/workspace/client-python/auth/client-secret.py'), false);
assert.equal(readFileSync('/mnt/workspace/vendor/mainline/src/rpc/server/tokens.rs', 'utf8'), 'pub fn tokens() {}\\n');
assert.equal(existsSync('/mnt/workspace/nested/.env.local'), false);
assert.equal(existsSync('/mnt/workspace/nested/config/secrets.json'), false);
assert.equal(existsSync('/etc/os-release'), false);
const originalCheckout = ${JSON.stringify(source)};
assert.throws(() => readFileSync(path.join(originalCheckout, 'auth.json')), { code: 'ENOENT' });
assert.throws(() => writeFileSync(hostFile, 'escaped'));
assert.equal(readFileSync('/run/validation-engine-sandbox', 'utf8'), process.env.VALIDATION_OUTER_SANDBOX_TOKEN);
assert.equal(fixtureDependency, 'sibling dependency resolved');
const connectionResults = await Promise.all([
  new Promise((resolve) => { const socket = net.connect(hostPort, '127.0.0.1'); socket.once('connect', () => { socket.destroy(); resolve('connected'); }); socket.once('error', () => resolve('blocked')); socket.setTimeout(1000, () => { socket.destroy(); resolve('blocked'); }); }),
  new Promise((resolve) => { const socket = net.createConnection(hostSocket); socket.once('connect', () => { socket.destroy(); resolve('connected'); }); socket.once('error', () => resolve('blocked')); socket.setTimeout(1000, () => { socket.destroy(); resolve('blocked'); }); }),
]);
assert.deepEqual(connectionResults, ['blocked', 'blocked']);
assert.equal(readFileSync(path.join(process.env.PLAYWRIGHT_BROWSERS_PATH, 'browser-canary.txt'), 'utf8'), 'read-only browser');
assert.throws(() => writeFileSync(path.join(process.env.PLAYWRIGHT_BROWSERS_PATH, 'browser-canary.txt'), 'changed'));
writeFileSync('/mnt/workspace/launcher-write-canary.txt', 'candidate only');
assert.equal(readFileSync('/mnt/workspace/node_modules/marker.txt', 'utf8'), 'read-only dependency');
assert.throws(() => writeFileSync('/mnt/workspace/node_modules/marker.txt', 'changed'));
`
    );
    execFileSync('git', ['init', '--quiet', '--initial-branch=main'], {
      cwd: source,
    });
    execFileSync('git', ['config', 'user.name', 'Fixture'], { cwd: source });
    execFileSync('git', ['config', 'user.email', 'fixture@example.invalid'], {
      cwd: source,
    });
    execFileSync('git', ['add', '--all'], { cwd: source });
    execFileSync('git', ['commit', '--quiet', '-m', 'Fixture'], {
      cwd: source,
    });
    mkdirSync(path.join(source, 'nested/config'), { recursive: true });
    writeFileSync(
      path.join(source, 'nested/config/operator.json'),
      '{"private":true}\n'
    );
    const result = spawnSync(
      process.execPath,
      [
        launcher,
        source,
        '--playwright-cache',
        browserCache,
        '--',
        process.execPath,
        'bin/run-local-validation.mjs',
      ],
      {
        encoding: 'utf8',
        env: { ...process.env, SECRET_CANARY: 'must-not-be-inherited' },
        timeout: 30_000,
      }
    );
    assert.equal(result.error, undefined, result.error?.message);
    assert.equal(
      result.status,
      0,
      `${result.stdout ?? ''}${result.stderr ?? ''}`
    );
    assert.equal(readFileSync(hostFile, 'utf8'), 'host canary stays unchanged');
    assert.equal(existsSync(candidateWrite), false);

    rmSync(path.join(source, 'node_modules'), { recursive: true, force: true });
    symlinkSync(outsideDependencies, path.join(source, 'node_modules'), 'dir');
    const linkedDependencyResult = spawnSync(
      process.execPath,
      [launcher, source, '--', process.execPath, '-e', 'process.exit(99)'],
      { encoding: 'utf8', timeout: 30_000 }
    );
    assert.equal(linkedDependencyResult.error, undefined);
    assert.equal(linkedDependencyResult.status, 1);
    assert.match(
      linkedDependencyResult.stderr,
      /Installed dependency path must be a real directory/u
    );
  }
);

test('sandbox masks candidate checkouts outside the standard host paths', () => {
  assert.ok(hostPathsToHide('/projects/QuestarrNG').includes('/projects'));
  assert.ok(hostPathsToHide('/QuestarrNG').includes('/QuestarrNG'));
  assert.equal(
    hostPathsToHide('/home/keith/QuestarrNG').includes('/home/keith'),
    false
  );
  assert.throws(() => hostPathsToHide('/'), /cannot be the filesystem root/u);
});
