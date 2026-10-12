// Copyright (c) slskR contributors. All rights reserved.
import assert from 'node:assert/strict';
import {
  mkdtempSync,
  mkdirSync,
  readFileSync,
  rmSync,
  statSync,
  symlinkSync,
  unlinkSync,
  writeFileSync,
} from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { spawnSync } from 'node:child_process';
import process from 'node:process';
import { after, test } from 'node:test';
import {
  captureCandidate,
  acquireRunLock,
  createPlan,
  discoverInventory,
  executePlan,
  formatValidationProgress,
  globMatches,
  matchesVersionCheck,
  main as runEngine,
  parseCaseCount,
  releaseRunLock,
} from './engine.mjs';

const temporaryRoots = [];
const GITHUB_CONTEXT_KEYS = [
  'GITHUB_ACTIONS', 'GITHUB_RUN_ID', 'GITHUB_RUN_ATTEMPT', 'GITHUB_SHA',
  'GITHUB_WORKFLOW', 'GITHUB_JOB', 'GITHUB_EVENT_NAME', 'VALIDATION_NODE_ID',
];
const inheritedGithubContext = new Map(GITHUB_CONTEXT_KEYS.map((key) => [key, process.env[key]]));
for (const key of GITHUB_CONTEXT_KEYS) delete process.env[key];

function makeRoot(files = {}) {
  const root = mkdtempSync(path.join(os.tmpdir(), 'slskr-validation-contract-'));
  temporaryRoots.push(root);
  for (const [relative, contents] of Object.entries(files)) {
    const fullPath = path.join(root, relative);
    mkdirSync(path.dirname(fullPath), { recursive: true });
    writeFileSync(fullPath, contents);
  }
  const git = (args) => {
    const result = spawnSync('git', args, { cwd: root, encoding: 'utf8' });
    assert.equal(result.status, 0, result.stderr);
    return result.stdout.trim();
  };
  git(['init', '--quiet']);
  git(['config', 'user.email', 'validation-test@example.invalid']);
  git(['config', 'user.name', 'Validation Engine Test']);
  git(['add', '--all']);
  git(['commit', '--quiet', '-m', 'fixture baseline']);
  return root;
}

function baseConfig(overrides = {}) {
  return {
    repository: 'fixture',
    inputs: ['package.json'],
    requiredCommands: [],
    inventory: [{
      id: 'unit',
      glob: 'tests/**/*.test.mjs',
      framework: 'node:test',
      owner: 'unit',
    }],
    tasks: [{
      id: 'unit-tests',
      name: 'Unit tests',
      stage: 'repository',
      kind: 'test',
      command: [process.execPath, '--test', 'tests/example.test.mjs'],
      caseParser: 'tapSummary',
      minimumCases: 1,
      inventoryLanes: ['unit'],
      timeoutSeconds: 10,
    }],
    ...overrides,
  };
}

function fixture() {
  const root = makeRoot({
    'package.json': '{"name":"validation-fixture"}\n',
    'tests/example.test.mjs': "import test from 'node:test';\ntest('fixture passes', () => {});\n",
  });
  return { root, config: baseConfig() };
}

after(() => {
  for (const [key, value] of inheritedGithubContext) {
    if (value === undefined) delete process.env[key];
    else process.env[key] = value;
  }
  for (const root of temporaryRoots) rmSync(root, { recursive: true, force: true });
});

test('glob matching covers root and nested files without crossing sibling names', () => {
  assert.equal(globMatches('src/**/*.test.*', 'src/a.test.js'), true);
  assert.equal(globMatches('src/**/*.test.*', 'src/components/a.test.jsx'), true);
  assert.equal(globMatches('src/**/*.test.*', 'src-other/a.test.js'), false);
  assert.equal(globMatches('**/*.spec.ts', 'a.spec.ts'), true);
  assert.equal(globMatches('crates/**/src/**/*.rs', 'crates/app/src/lib.rs'), true);
  assert.equal(globMatches('tests/*.test.mjs', 'tests/nested/example.test.mjs'), false);
  assert.throws(() => globMatches('../**/*.js', 'src/example.js'), /bounded relative POSIX paths/);
});

test('fixed native summary parsers count cases without config-supplied regular expressions', () => {
  assert.equal(parseCaseCount('tapSummary', 'ℹ tests 12\nℹ pass 12\n'), 12);
  assert.equal(parseCaseCount('cargoTestSummary', 'test result: ok. 47 passed; 0 failed; 2 ignored;'), 47);
  assert.equal(parseCaseCount('sdkNativeSummary', 'NATIVE_TESTS_PASSED=5\n'), 5);
  assert.equal(parseCaseCount('pythonUnittestSummary', 'Ran 8 tests in 0.2s\n'), 8);
  assert.equal(parseCaseCount('vitestSummary', 'Tests 31 passed | 2 skipped'), 31);
  assert.equal(parseCaseCount('playwrightSummary', '3 passed (4.2s)\n'), 3);
  assert.equal(parseCaseCount('passLines', 'PASS\nPASS\nPASS\n'), 3);
  assert.throws(() => parseCaseCount('custom', '1 passed'), /Unknown native test summary parser/);
});

test('live progress summary distinguishes completed, blocked, pending, and active tasks', () => {
  const tasks = [
    { id: 'passed', name: 'Passed task' },
    { id: 'blocked', name: 'Blocked task' },
    { id: 'running', name: 'Long task' },
  ];
  const results = new Map([
    ['passed', { status: 'passed', startedAt: '2026-10-12T00:00:00.000Z' }],
    ['blocked', { status: 'blocked' }],
  ]);
  assert.equal(
    formatValidationProgress('sample', tasks, results, tasks[2], 65_000),
    '[validation] sample: 1/3 selected tasks complete (1 passed, 0 failed, 1 blocked, 1 pending); running Long task (1m05s)',
  );
});

test('runtime compatibility checks use bounded prefix and character rules', () => {
  assert.equal(matchesVersionCheck('v22.19.0', { prefix: 'v22.', boundary: 'digit' }), true);
  assert.equal(matchesVersionCheck('v220.19.0', { prefix: 'v22.', boundary: 'digit' }), false);
  assert.equal(matchesVersionCheck('v22.preview', { prefix: 'v22.', boundary: 'digit' }), false);
  assert.equal(matchesVersionCheck('rustc 1.94.0 (hash)', {
    prefix: 'rustc 1.94.0', boundary: 'space-or-end',
  }), true);
  assert.equal(matchesVersionCheck('rustc 1.94.01', {
    prefix: 'rustc 1.94.0', boundary: 'space-or-end',
  }), false);
});

test('inventory records scoped file digests and rejects empty or duplicate ownership', () => {
  const { root, config } = fixture();
  const inventory = discoverInventory(root, config.inventory);
  assert.deepEqual(inventory.laneCounts, { unit: 1 });
  assert.equal(inventory.entries[0].file, 'tests/example.test.mjs');
  assert.match(inventory.entries[0].sha256, /^[a-f0-9]{64}$/);
  assert.throws(() => discoverInventory(root, [
    ...config.inventory,
    { ...config.inventory[0], id: 'duplicate-owner', owner: 'other' },
  ]), /duplicate ownership/);
  assert.throws(() => discoverInventory(root, [{
    ...config.inventory[0],
    glob: 'tests/missing/**/*.test.mjs',
  }]), /inventory is empty/);
});

test('tracked source-input and inventory digests ignore CRLF checkout conversion', () => {
  const { root, config } = fixture();
  const inventory = discoverInventory(root, config.inventory);
  const original = captureCandidate(root, config.inputs, inventory);
  for (const relative of ['package.json', 'tests/example.test.mjs']) {
    const fullPath = path.join(root, relative);
    const normalized = readFileSync(fullPath, 'utf8').replace(/\r?\n/g, '\n');
    writeFileSync(fullPath, normalized.replace(/\n/g, '\r\n'));
  }

  const windowsCheckoutInventory = discoverInventory(root, config.inventory);
  const windowsCheckout = captureCandidate(root, config.inputs, windowsCheckoutInventory);
  assert.equal(windowsCheckout.inventorySha256, original.inventorySha256);
  assert.deepEqual(windowsCheckout.inputDigests, original.inputDigests);
});

test('inventory content filters keep inline Rust test modules in the native lane', () => {
  const root = makeRoot({
    'Cargo.toml': '[workspace]\nmembers = []\n',
    'crates/app/src/lib.rs': '#[cfg(test)]\nmod tests {}\n',
    'crates/app/src/main.rs': 'fn main() {}\n',
  });
  const inventory = discoverInventory(root, [{
    id: 'rust-inline',
    glob: 'crates/**/src/**/*.rs',
    contentMatcher: 'rustInlineTestModule',
    framework: 'cargo-test',
    owner: 'rust-workspace',
  }]);
  assert.deepEqual(inventory.laneCounts, { 'rust-inline': 1 });
  assert.equal(inventory.entries[0].file, 'crates/app/src/lib.rs');
});

test('inventory Rust matcher accepts spacing and rejects ordinary source', () => {
  const root = makeRoot({
    'crates/app/src/lib.rs': '#  [ cfg ( test ) ]\nmod tests {}\n',
    'crates/app/src/main.rs': 'fn main() {}\n',
  });
  const inventory = discoverInventory(root, [{
    id: 'rust-inline',
    glob: 'crates/**/src/**/*.rs',
    contentMatcher: 'rustInlineTestModule',
    framework: 'cargo-test',
    owner: 'rust-workspace',
  }]);
  assert.deepEqual(inventory.laneCounts, { 'rust-inline': 1 });
});

test('inventory rejects content matchers that are not registered by the engine', () => {
  const { root } = fixture();
  assert.throws(() => discoverInventory(root, [{
    id: 'custom',
    glob: 'tests/**/*.test.mjs',
    contentMatcher: 'repository-supplied-regex',
    framework: 'node:test',
    owner: 'unit',
  }]), /Unknown inventory content matcher/);
});

test('inventory rejects symbolic links in native test discovery scopes', () => {
  const root = makeRoot({ 'package.json': '{}\n' });
  mkdirSync(path.join(root, 'tests'), { recursive: true });
  writeFileSync(path.join(root, 'outside.test.mjs'), '');
  symlinkSync('../outside.test.mjs', path.join(root, 'tests', 'linked.test.mjs'));
  assert.throws(() => discoverInventory(root, baseConfig().inventory), /Symlink in test discovery scope/);
});

test('plan binds the candidate and closes test selection over its dependencies', () => {
  const { root, config } = fixture();
  config.tasks.unshift({
    id: 'prepare',
    name: 'Prepare',
    stage: 'prepare',
    kind: 'setup',
    command: [process.execPath, '-e', 'process.exit(0)'],
  });
  config.tasks[1].requiredCommands = ['python3.12'];
  config.tasks[1].dependsOn = ['prepare'];
  config.tasks.push({
    id: 'optional-browser',
    name: 'Optional browser suite',
    stage: 'browser',
    kind: 'test',
    command: [process.execPath, '-e', 'process.exit(0)'],
    caseParser: 'tapSummary',
    minimumCases: 1,
    defaultSelected: false,
  });
  const plan = createPlan(root, config, { testsOnly: true });
  assert.deepEqual(plan.tasks.filter((task) => task.selected).map((task) => task.id), [
    'prepare',
    'unit-tests',
  ]);
  assert.equal(plan.inventoryCounts.unit, 1);
  assert.deepEqual(plan.tasks[1].requiredCommands, ['python3.12']);
  assert.equal(plan.prerequisites.some((item) => item.command === 'python3.12'), true);
  assert.equal(plan.candidate.commit.length, 40);
  assert.match(plan.candidate.sourceSha256, /^[a-f0-9]{64}$/);
  assert.equal(plan.runtimes.length, 0);
  assert.match(plan.inventoryLaneDigests.unit, /^[a-f0-9]{64}$/);
});

test('test tasks reject unregistered case parsers', () => {
  const { root, config } = fixture();
  config.tasks[0].caseParser = 'repository-supplied-regex';
  assert.throws(() => createPlan(root, config), /active-case evidence/);
});

test('executor rejects a plan whose task contract was changed after hashing', async () => {
  const { root, config } = fixture();
  const plan = createPlan(root, config);
  plan.tasks[0].command = [process.execPath, '-e', 'process.exit(0)'];
  await assert.rejects(executePlan(root, config, plan), /plan digest/);
});

test('native execution records passing case counts, source identity and private evidence', async () => {
  const { root, config } = fixture();
  const plan = createPlan(root, config);
  const runRoot = mkdtempSync(path.join(os.tmpdir(), 'slskr-validation-receipt-'));
  temporaryRoots.push(runRoot);
  const result = await executePlan(root, config, plan, { runRoot });
  assert.equal(result.exitCode, 0, JSON.stringify(result.receipt, null, 2) +
    '\\n' + readFileSync(path.join(runRoot, 'unit-tests.log'), 'utf8'));
  assert.equal(result.receipt.status, 'passed');
  assert.equal(result.receipt.totals.executed, 1);
  assert.equal(result.receipt.totals.activeCases, 1);
  assert.deepEqual(result.receipt.tasks[0].inventory.map((item) => item.discoveredFiles), [1]);
  assert.equal(statSync(runRoot).mode & 0o777, 0o700);
  const log = path.join(runRoot, result.receipt.tasks[0].logFile);
  assert.equal(statSync(log).mode & 0o777, 0o600);
  assert.match(readFileSync(path.join(runRoot, 'receipt.json'), 'utf8'), /"status": "passed"/);
});

test('native execution can count individual pass events without summing their labels', async () => {
  const { root, config } = fixture();
  config.tasks[0].command = [process.execPath, '-e', 'console.log("PASS\\nPASS\\nPASS")'];
  config.tasks[0].caseParser = 'passLines';
  const plan = createPlan(root, config);
  assert.equal(plan.tasks[0].caseParser, 'passLines');
  const result = await executePlan(root, config, plan);
  assert.equal(result.receipt.status, 'passed');
  assert.equal(result.receipt.totals.activeCases, 3);
});

test('execution fails closed when a test reports zero active cases', async () => {
  const { root, config } = fixture();
  config.tasks[0].command = [process.execPath, '-e', 'console.log("suite completed")'];
  const plan = createPlan(root, config);
  const result = await executePlan(root, config, plan);
  assert.equal(result.receipt.tasks[0].status, 'incomplete');
  assert.equal(result.receipt.status, 'failed');
  assert.equal(result.receipt.totals.activeCases, 0);
});

test('execution blocks later tasks when a command changes the planned source', async () => {
  const { root, config } = fixture();
  config.tasks.push({
    id: 'after-tests',
    name: 'Must not run after drift',
    stage: 'repository',
    kind: 'check',
    command: [process.execPath, '-e', 'process.exit(0)'],
  });
  config.tasks[0].command = [
    process.execPath,
    '-e',
    "require('node:fs').writeFileSync('package.json', '{\\\"changed\\\":true}\\n')",
  ];
  const plan = createPlan(root, config);
  const result = await executePlan(root, config, plan);
  assert.equal(result.receipt.status, 'failed');
  assert.equal(result.receipt.tasks[0].status, 'incomplete');
  assert.match(result.receipt.tasks[1].reason, /candidate source changed/);
  assert.equal(result.receipt.totals.blocked, 1);
});

test('execution records timeouts and does not accept failed native commands', async () => {
  const { root, config } = fixture();
  config.tasks[0].command = [process.execPath, '-e', 'setInterval(() => {}, 1000)'];
  config.tasks[0].timeoutSeconds = 0.1;
  const plan = createPlan(root, config);
  const result = await executePlan(root, config, plan);
  assert.equal(result.receipt.tasks[0].status, 'failed');
  assert.equal(result.receipt.tasks[0].timedOut, true);
  assert.equal(result.receipt.status, 'failed');
});

test('workspace run lock rejects overlap and releases only its own lock file', () => {
  const { root } = fixture();
  const first = acquireRunLock(root, 'slskr');
  try {
    assert.equal(statSync(first.lockPath).mode & 0o777, 0o600);
    assert.throws(() => acquireRunLock(root, 'slskr'), /Another validation engine run is active/);
  } finally {
    releaseRunLock(first);
  }
  const second = acquireRunLock(root, 'slskr');
  releaseRunLock(second);
  assert.throws(() => readFileSync(first.lockPath, 'utf8'), { code: 'ENOENT' });
});

test('workspace run lock refuses to overwrite a stale lock without confirmation', () => {
  const { root } = fixture();
  const first = acquireRunLock(root, 'slskr');
  releaseRunLock(first);
  writeFileSync(first.lockPath, JSON.stringify({ pid: -1 }), { mode: 0o600 });
  try {
    assert.throws(() => acquireRunLock(root, 'slskr'), /A stale validation lock exists/);
  } finally {
    unlinkSync(first.lockPath);
  }
});

test('exports a private receipt only to a location beneath the system temporary directory', async () => {
  const { root, config } = fixture();
  const exportDirectory = mkdtempSync(path.join(os.tmpdir(), 'slskr-export-contract-'));
  temporaryRoots.push(exportDirectory);
  const exportPath = path.join(exportDirectory, 'receipt.json');
  const previous = process.env.VALIDATION_RECEIPT_EXPORT;
  process.env.VALIDATION_RECEIPT_EXPORT = exportPath;
  try {
    assert.equal(await runEngine(['--task', 'unit-tests'], root, config), 0);
    assert.equal(JSON.parse(readFileSync(exportPath, 'utf8')).status, 'passed');
    assert.equal(statSync(exportPath).mode & 0o777, 0o600);
  } finally {
    if (previous === undefined) delete process.env.VALIDATION_RECEIPT_EXPORT;
    else process.env.VALIDATION_RECEIPT_EXPORT = previous;
  }
});

test('child environments hide sensitive values unless a task explicitly needs them', async () => {
  const key = 'VALIDATION_ENGINE_TEST_SECRET';
  const previous = process.env[key];
  process.env[key] = 'do-not-log-me';
  try {
    const { root, config } = fixture();
    config.tasks[0].kind = 'check';
    config.tasks[0].command = [
      process.execPath,
      '-e',
      `process.stdout.write(process.env.${key} ?? '')`,
    ];
    let result = await executePlan(root, config, createPlan(root, config));
    let log = path.join(result.runRoot, result.receipt.tasks[0].logFile);
    assert.equal(readFileSync(log, 'utf8'), '');

    config.tasks[0].passEnv = [key];
    result = await executePlan(root, config, createPlan(root, config));
    log = path.join(result.runRoot, result.receipt.tasks[0].logFile);
    assert.equal(readFileSync(log, 'utf8'), 'do-not-log-me');
    assert.deepEqual(result.receipt.tasks[0].envKeys, [key]);
  } finally {
    if (previous === undefined) delete process.env[key];
    else process.env[key] = previous;
  }
});

test('plan and executor reject dependency cycles and report missing tools', async () => {
  const { root, config } = fixture();
  config.tasks[0].dependsOn = ['other'];
  config.tasks.push({
    id: 'other',
    name: 'Other',
    stage: 'repository',
    kind: 'check',
    command: [process.execPath, '-e', 'process.exit(0)'],
    dependsOn: ['unit-tests'],
  });
  assert.throws(() => createPlan(root, config), /dependency cycle/);

  const missingRoot = makeRoot({ 'package.json': '{}\n' });
  const missingConfig = baseConfig({
    inventory: [],
    tasks: [{
      id: 'check',
      name: 'Check',
      stage: 'repository',
      kind: 'check',
      command: [process.execPath, '-e', 'throw new Error("must not execute")'],
    }],
    requiredCommands: ['command-that-is-not-installed-validation-test'],
  });
  const plan = createPlan(missingRoot, missingConfig);
  const result = await executePlan(missingRoot, missingConfig, plan);
  assert.equal(result.receipt.status, 'incomplete');
  assert.equal(result.receipt.totals.executed, 0);
  assert.equal(result.receipt.prerequisites.some((item) => !item.available), true);
});

test('candidate digests change after tracked source edits', () => {
  const { root, config } = fixture();
  const before = captureCandidate(root, config.inputs, discoverInventory(root, config.inventory));
  writeFileSync(path.join(root, 'package.json'), '{"edited":true}\n');
  const afterEdit = captureCandidate(root, config.inputs, discoverInventory(root, config.inventory));
  assert.notEqual(before.sourceSha256, afterEdit.sourceSha256);
});

test('hosted execution rejects a workflow SHA that does not match its source snapshot', async () => {
  const previous = new Map(GITHUB_CONTEXT_KEYS.map((key) => [key, process.env[key]]));
  process.env.GITHUB_ACTIONS = 'true';
  process.env.GITHUB_RUN_ID = 'validation-contract-run';
  process.env.GITHUB_RUN_ATTEMPT = '1';
  process.env.GITHUB_SHA = '0'.repeat(40);
  try {
    const { root, config } = fixture();
    const result = await executePlan(root, config, createPlan(root, config));
    assert.equal(result.exitCode, 1);
    assert.equal(result.receipt.status, 'incomplete');
    assert.equal(result.receipt.totals.executed, 0);
    assert.equal(result.receipt.prerequisites.some((item) => item.command === 'GITHUB_SHA'), true);
  } finally {
    for (const [key, value] of previous) {
      if (value === undefined) delete process.env[key];
      else process.env[key] = value;
    }
  }
});
