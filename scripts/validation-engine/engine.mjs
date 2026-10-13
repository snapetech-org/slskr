#!/usr/bin/env node
// Copyright (c) slskR contributors. All rights reserved.
import { createHash, randomUUID } from 'node:crypto';
import { Buffer } from 'node:buffer';
import { spawn, spawnSync } from 'node:child_process';
import process from 'node:process';
import { clearTimeout, setTimeout } from 'node:timers';
import {
  accessSync,
  chmodSync,
  closeSync,
  constants,
  existsSync,
  lstatSync,
  mkdtempSync,
  mkdirSync,
  openSync,
  readFileSync,
  realpathSync,
  readlinkSync,
  readdirSync,
  rmSync,
  unlinkSync,
  writeFileSync,
  writeSync,
  fsyncSync,
} from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { requireTrustedLocalTestSandbox } from './trusted-sandbox.mjs';

export const ENGINE_VERSION = 1;
const SYSTEM_TEMP_DIR = os.tmpdir();
const ENGINE_DIR = path.dirname(fileURLToPath(import.meta.url));
const DEFAULT_ROOT = path.resolve(ENGINE_DIR, '..', '..');
const MAX_BUFFER = 8 * 1024 * 1024;
const MAX_LOG_BYTES = 16 * 1024 * 1024;
const LOG_TRUNCATION_MARKER = Buffer.from('\n[validation log truncated after 16 MiB]\n');
const PROGRESS_INTERVAL_MS = 60_000;
const IGNORED_DIRS = new Set([
  '.git',
  '.next',
  '.turbo',
  'node_modules',
  'obj',
  'dist',
  'target',
  'coverage',
  '_output',
  '_tests',
  'TestResults',
]);
const INHERITED_ENVIRONMENT_KEYS = new Set([
  'ASDF_DATA_DIR', 'ASDF_DIR', 'COMSPEC', 'LANG', 'LC_ALL', 'LC_CTYPE',
  'MISE_DATA_DIR', 'MISE_HOME', 'NVM_DIR', 'PATH', 'PATHEXT',
  'PYENV_ROOT', 'RUSTUP_HOME', 'VOLTA_HOME', 'SYSTEMROOT', 'TZ', 'WINDIR',
]);
const APPROVED_TASK_PASS_ENVIRONMENT = new Map([
  ['rust-workspace-tests', new Set(['OPENSSL_SRC_PERL'])],
]);
const CONTENT_MATCHERS = Object.freeze({
  rustInlineTestModule: (contents) => /#\s*\[\s*cfg\s*\(\s*test\s*\)\s*\]/.test(contents),
});

function sumCapturedCounts(output, pattern) {
  let total = 0;
  for (const match of output.matchAll(pattern)) total += Number(match[1]);
  return total;
}

const CASE_COUNT_PARSERS = Object.freeze({
  tapSummary: (output) => sumCapturedCounts(output, /(?:ℹ|#)\s*pass\s+(\d+)/g),
  cargoTestSummary: (output) => sumCapturedCounts(output, /test result: ok\.\s+(\d+) passed\b/g),
  sdkNativeSummary: (output) => sumCapturedCounts(output, /NATIVE_TESTS_PASSED=(\d+)/g),
  pythonUnittestSummary: (output) => sumCapturedCounts(output, /Ran\s+(\d+) tests?\b/g),
  vitestSummary: (output) => sumCapturedCounts(output, /Tests\s+(\d+)\s+passed\b/g),
  playwrightSummary: (output) => sumCapturedCounts(output, /(?:^|\n)\s*(\d+) passed(?:\s|$)/g),
  passLines: (output) => output.split(/\r?\n/).filter((line) => line.trim() === 'PASS').length,
});

export function parseCaseCount(parserName, output) {
  const parser = CASE_COUNT_PARSERS[parserName];
  if (!parser) fail('Unknown native test summary parser: ' + parserName);
  return parser(output);
}

const VERSION_BOUNDARIES = new Set(['digit', 'space-or-end']);

function asciiDigit(character) {
  if (character === undefined) return false;
  const code = character.charCodeAt(0);
  return code >= 48 && code <= 57;
}

export function matchesVersionCheck(versionLine, check) {
  if (!versionLine.startsWith(check.prefix)) return false;
  const next = versionLine[check.prefix.length];
  if (check.boundary === 'digit') return asciiDigit(next);
  return check.boundary === 'space-or-end' &&
    (next === undefined || next === ' ' || next === '\t');
}

function fail(message) {
  throw new Error(message);
}

function formatElapsed(milliseconds) {
  const seconds = Math.floor(milliseconds / 1000);
  return `${Math.floor(seconds / 60)}m${String(seconds % 60).padStart(2, '0')}s`;
}

export function formatValidationProgress(repository, tasks, results, currentTask = null, elapsedMs = 0) {
  const receipts = tasks.map((task) => results.get(task.id)).filter(Boolean);
  const passed = receipts.filter((receipt) => receipt.status === 'passed').length;
  const failed = receipts.filter((receipt) => ['failed', 'incomplete'].includes(receipt.status)).length;
  const blocked = receipts.filter((receipt) => ['blocked', 'not-run'].includes(receipt.status)).length;
  const completed = passed + failed;
  const pending = Math.max(0, tasks.length - completed - blocked);
  const active = currentTask
    ? `; running ${currentTask.name ?? currentTask.id} (${formatElapsed(elapsedMs)})`
    : '';
  return `[validation] ${repository}: ${completed}/${tasks.length} selected tasks complete (${passed} passed, ${failed} failed, ${blocked} blocked, ${pending} pending)${active}`;
}

export function acquireRunLock(root, repository) {
  const workspaceKey = hash(path.resolve(root)).slice(0, 16);
  const lockPath = path.join(os.tmpdir(), repository + '-validation-' + workspaceKey + '.lock');
  const lock = { pid: process.pid, startedAt: new Date().toISOString(), workspaceKey };
  const contents = JSON.stringify(lock) + '\n';
  let descriptor;
  try {
    descriptor = openSync(lockPath, 'wx', 0o600);
  } catch (error) {
    if (error.code !== 'EEXIST') throw error;
    let existing;
    try {
      existing = JSON.parse(readFileSync(lockPath, 'utf8'));
    } catch {
      fail('A validation lock exists but cannot be read safely: ' + lockPath);
    }
    let alive = false;
    if (Number.isInteger(existing.pid) && existing.pid > 0) {
      try {
        process.kill(existing.pid, 0);
        alive = true;
      } catch (probeError) {
        alive = probeError.code === 'EPERM';
      }
    }
    fail(alive
      ? 'Another validation engine run is active for this workspace (pid ' + existing.pid + ').'
      : 'A stale validation lock exists for this workspace. Confirm its process is gone, then remove ' + lockPath + '.');
  }
  writeFileSync(descriptor, contents, { encoding: 'utf8' });
  closeSync(descriptor);
  return { lockPath, contents };
}

export function releaseRunLock(lock) {
  try {
    if (readFileSync(lock.lockPath, 'utf8') === lock.contents) unlinkSync(lock.lockPath);
  } catch (error) {
    if (error.code !== 'ENOENT') throw error;
  }
}

function hash(value) {
  return createHash('sha256').update(value).digest('hex');
}

function stable(value) {
  if (Array.isArray(value)) return '[' + value.map(stable).join(',') + ']';
  if (value && typeof value === 'object') {
    return '{' + Object.keys(value).sort().map((key) =>
      JSON.stringify(key) + ':' + stable(value[key])
    ).join(',') + '}';
  }
  return JSON.stringify(value);
}

function git(root, args) {
  const result = spawnSync('git', args, {
    cwd: root,
    encoding: 'buffer',
    maxBuffer: 128 * 1024 * 1024,
  });
  if (result.error || result.status !== 0) {
    fail('Unable to bind validation to Git source: ' +
      (result.error?.message ?? result.stderr?.toString('utf8').trim() ?? 'git failed'));
  }
  return result.stdout;
}

function gitText(root, args) {
  return git(root, args).toString('utf8').trim();
}

function segmentMatches(pattern, value) {
  let previous = new Uint8Array(value.length + 1);
  previous[0] = 1;
  for (const token of pattern) {
    const current = new Uint8Array(value.length + 1);
    if (token === '*') {
      current[0] = previous[0];
      for (let index = 1; index <= value.length; index += 1) {
        current[index] = previous[index] || current[index - 1] ? 1 : 0;
      }
    } else {
      for (let index = 1; index <= value.length; index += 1) {
        current[index] = previous[index - 1] && (token === '?' || token === value[index - 1]) ? 1 : 0;
      }
    }
    previous = current;
  }
  return previous[value.length] === 1;
}

export function globMatches(glob, filename) {
  if (typeof glob !== 'string' || glob.length === 0 || glob.length > 512 ||
      glob.startsWith('/') || glob.includes('\\') || glob.split('/').includes('..') ||
      typeof filename !== 'string' || filename.length > 4096 ||
      filename.startsWith('/') || filename.includes('\\')) {
    fail('Inventory glob and paths must be bounded relative POSIX paths.');
  }
  const patterns = glob.split('/');
  const segments = filename.split('/');
  let previous = new Uint8Array(segments.length + 1);
  previous[0] = 1;
  for (const pattern of patterns) {
    const current = new Uint8Array(segments.length + 1);
    if (pattern === '**') {
      current[0] = previous[0];
      for (let index = 1; index <= segments.length; index += 1) {
        current[index] = previous[index] || current[index - 1] ? 1 : 0;
      }
    } else {
      for (let index = 1; index <= segments.length; index += 1) {
        current[index] = previous[index - 1] && segmentMatches(pattern, segments[index - 1]) ? 1 : 0;
      }
    }
    previous = current;
  }
  return previous[segments.length] === 1;
}

function walk(root, relative = '') {
  const directory = path.join(root, relative);
  const entries = readdirSync(directory, { withFileTypes: true });
  const files = [];
  for (const entry of entries) {
    const child = relative ? relative + '/' + entry.name : entry.name;
    if (entry.isSymbolicLink()) {
      files.push({ path: child, symlink: true });
    } else if (entry.isDirectory()) {
      if (!IGNORED_DIRS.has(entry.name)) files.push(...walk(root, child));
    } else if (entry.isFile()) {
      files.push({ path: child, symlink: false });
    }
  }
  return files;
}

// Configured source inputs and discovered tests are text. Git may check them
// out with CRLF on Windows; untracked files keep byte-exact hashing below.
function fileDigest(root, relative, normalizeLineEndings = false) {
  const filePath = path.join(root, relative);
  const info = lstatSync(filePath);
  if (info.isSymbolicLink() || !info.isFile()) {
    fail('Validation inventory contains a non-regular file: ' + relative);
  }
  const contents = readFileSync(filePath);
  return normalizeLineEndings
    ? hash(contents.toString('utf8').replace(/\r\n/g, '\n'))
    : hash(contents);
}

export function discoverInventory(root, rules) {
  const files = walk(root);
  const entriesByPath = new Map();
  const laneCounts = {};
  for (const rule of rules) {
    let matches = files.filter(({ path: name }) => globMatches(rule.glob, name));
    if (rule.contentMatcher) {
      const contentMatcher = CONTENT_MATCHERS[rule.contentMatcher];
      if (!contentMatcher) fail('Unknown inventory content matcher: ' + rule.contentMatcher);
      matches = matches.filter(({ path: name }) => contentMatcher(readFileSync(
        path.join(root, name), 'utf8'
      )));
    }
    if (rule.required !== false && matches.length === 0) {
      fail('Required test inventory is empty: ' + rule.id);
    }
    laneCounts[rule.id] = matches.length;
    for (const match of matches) {
      if (match.symlink) fail('Symlink in test discovery scope: ' + match.path);
      if (entriesByPath.has(match.path)) {
        fail('Test file has duplicate ownership: ' + match.path);
      }
      entriesByPath.set(match.path, {
        file: match.path,
        framework: rule.framework,
        owner: rule.owner,
        lane: rule.id,
        sha256: fileDigest(root, match.path, true),
      });
    }
  }
  return {
    entries: [...entriesByPath.values()].sort((left, right) =>
      left.file.localeCompare(right.file)
    ),
    laneCounts,
  };
}

function untrackedDigests(root) {
  const raw = git(root, ['ls-files', '--others', '--exclude-standard', '-z']);
  const paths = raw.toString('utf8').split('\0').filter(Boolean).sort();
  return paths.map((relative) => {
    const fullPath = path.join(root, relative);
    const info = lstatSync(fullPath);
    if (info.isSymbolicLink()) {
      return { file: relative, sha256: hash('symlink:' + readlinkSync(fullPath)) };
    }
    if (!info.isFile()) return { file: relative, sha256: 'not-regular' };
    return { file: relative, sha256: fileDigest(root, relative) };
  });
}

export function captureCandidate(root, inputs, inventory) {
  const commit = gitText(root, ['rev-parse', 'HEAD']);
  const tree = gitText(root, ['rev-parse', 'HEAD^{tree}']);
  const diffSha256 = hash(git(root, ['diff', '--binary', 'HEAD']));
  const untracked = untrackedDigests(root);
  const inputDigests = inputs.map((relative) => ({
    file: relative,
    sha256: fileDigest(root, relative, true),
  }));
  const inventorySha256 = hash(stable(inventory.entries));
  const sourceSha256 = hash(stable({
    commit,
    tree,
    diffSha256,
    untracked,
    inputDigests,
    inventorySha256,
  }));
  const status = gitText(root, ['status', '--porcelain=v1', '--untracked-files=all']);
  return {
    commit,
    tree,
    sourceSha256,
    inventorySha256,
    inputDigests,
    dirty: status.length > 0,
    untrackedCount: untracked.length,
  };
}

function commandAvailable(command) {
  const executable = (file) => {
    try {
      accessSync(file, constants.X_OK);
      return true;
    } catch {
      return false;
    }
  };
  if (path.isAbsolute(command)) {
    return executable(command);
  }
  const candidates = (process.env.PATH ?? '').split(path.delimiter);
  return candidates.some((directory) => {
    const file = path.join(directory, command);
    return executable(file) || (process.platform === 'win32' &&
      ['.exe', '.cmd', '.bat'].some((extension) => executable(file + extension)));
  });
}

function sanitizedEnvironment(additional = {}, inherited = process.env) {
  const values = new Map();
  for (const [key, value] of Object.entries(inherited)) {
    const normalized = key.toUpperCase();
    if (!INHERITED_ENVIRONMENT_KEYS.has(normalized) || typeof value !== 'string') continue;
    if (!values.has(normalized) || key === normalized) values.set(normalized, value);
  }
  const env = Object.fromEntries(values);
  for (const [key, value] of Object.entries(additional)) {
    if (typeof value === 'string') env[key] = value;
  }
  return env;
}

function privateEnvironment(additional, environmentRoot, cargoHome, inherited = process.env) {
  const env = sanitizedEnvironment(additional, inherited);
  if (!env.RUSTUP_HOME) {
    const inheritedHome = inherited.HOME ?? inherited.USERPROFILE;
    if (typeof inheritedHome === 'string' && inheritedHome) {
      env.RUSTUP_HOME = path.join(inheritedHome, '.rustup');
    }
  }
  const directories = {
    HOME: path.join(environmentRoot, 'home'),
    USERPROFILE: path.join(environmentRoot, 'home'),
    TMPDIR: path.join(environmentRoot, 'tmp'),
    TMP: path.join(environmentRoot, 'tmp'),
    TEMP: path.join(environmentRoot, 'tmp'),
    XDG_CONFIG_HOME: path.join(environmentRoot, 'xdg-config'),
    XDG_CACHE_HOME: path.join(environmentRoot, 'xdg-cache'),
    APPDATA: path.join(environmentRoot, 'AppData', 'Roaming'),
    LOCALAPPDATA: path.join(environmentRoot, 'AppData', 'Local'),
    CARGO_HOME: cargoHome,
    GOPATH: path.join(environmentRoot, 'go'),
    GOMODCACHE: path.join(environmentRoot, 'go', 'pkg', 'mod'),
    GOCACHE: path.join(environmentRoot, 'go-cache'),
  };
  for (const directory of new Set(Object.values(directories))) {
    mkdirSync(directory, { recursive: true, mode: 0o700 });
  }
  Object.assign(env, directories, {
    CI: 'true',
    NO_COLOR: '1',
    CARGO_TERM_COLOR: 'never',
    PYTHONNOUSERSITE: '1',
  });
  return env;
}

export function isolatedRuntimeEnvironment(runtime, environmentRoot, inherited = process.env) {
  return privateEnvironment(
    runtime?.env ?? {},
    environmentRoot,
    path.join(environmentRoot, 'cargo-home'),
    inherited,
  );
}

function isGoRuntimeCommand(command) {
  const executableName = path.basename(command)
    .replace(/\.(?:bat|cmd|exe)$/iu, '')
    .toLowerCase();
  return executableName === 'go';
}

export function runtimeProbeCommands(runtime) {
  const commands = [];
  if (isGoRuntimeCommand(runtime.command)) commands.push(['telemetry', 'off']);
  commands.push(runtime.args ?? ['--version']);
  return commands;
}

function inspectRuntime(root, runtime) {
  const available = commandAvailable(runtime.command);
  if (!available) return { ...runtime, available, version: null, exitCode: null };
  const probeRoot = mkdtempSync(path.join(SYSTEM_TEMP_DIR, 'slskr-runtime-probe-'));
  let result;
  try {
    const env = isolatedRuntimeEnvironment(runtime, probeRoot);
    const commands = runtimeProbeCommands(runtime);
    const disablesGoTelemetry = isGoRuntimeCommand(runtime.command);
    for (const [index, args] of commands.entries()) {
      result = spawnSync(runtime.command, args, {
        cwd: root,
        encoding: 'utf8',
        timeout: 10_000,
        maxBuffer: 1024 * 1024,
        env,
      });
      if (disablesGoTelemetry && index === 0 &&
          (result?.error !== undefined || result?.status !== 0)) {
        const detail = (result.stderr ?? '').trim();
        fail('Could not disable Go telemetry in the isolated runtime probe.' +
          (result.error ? ' ' + result.error.message : detail ? ' ' + detail : ''));
      }
    }
  } finally {
    rmSync(probeRoot, { recursive: true, force: true });
  }
  const version = (result.stdout ?? '') + (result.stderr ?? '');
  const versionLine = version.trim().split(/\r?\n/, 1)[0] ?? '';
  const versionCompatible = !runtime.versionCheck ||
    matchesVersionCheck(versionLine, runtime.versionCheck);
  return {
    ...runtime,
    available: !result.error && result.status === 0,
    version: versionLine,
    versionCompatible,
    required: runtime.required !== false,
    exitCode: result.status,
    error: result.error?.message,
  };
}

function validateConfig(config) {
  if (!config || typeof config.repository !== 'string' || !config.repository) {
    fail('Validation config must declare a repository identifier.');
  }
  if (!Array.isArray(config.inventory) || !Array.isArray(config.tasks)) {
    fail('Validation config must declare inventory rules and native tasks.');
  }
  const ids = new Set();
  for (const task of config.tasks) {
    if (!/^[a-z0-9][a-z0-9-]*$/.test(task.id) || ids.has(task.id)) {
      fail('Task IDs must be unique lowercase identifiers: ' + task.id);
    }
    ids.add(task.id);
    if (!Array.isArray(task.command) || task.command.length === 0) {
      fail('Task must use a registered native command array: ' + task.id);
    }
    if (task.kind === 'test' &&
        (!Object.hasOwn(CASE_COUNT_PARSERS, task.caseParser) || task.minimumCases < 1)) {
      fail('Test tasks must require active-case evidence: ' + task.id);
    }
    if (!Array.isArray(task.passEnv ?? [])) {
      fail('Explicitly inherited environment variables must be listed by task: ' + task.id);
    }
    if ((task.passEnv ?? []).some((name) => typeof name !== 'string' ||
        !APPROVED_TASK_PASS_ENVIRONMENT.get(task.id)?.has(name))) {
      fail('Task requests an unapproved inherited environment variable: ' + task.id);
    }
    if (!Array.isArray(task.requiredCommands ?? []) ||
        (task.requiredCommands ?? []).some((command) => typeof command !== 'string' || !command)) {
      fail('Task prerequisites must be declared as executable names: ' + task.id);
    }
  }
  const laneIds = new Set(config.inventory.map((rule) => rule.id));
  const ownedLanes = new Set();
  for (const task of config.tasks) {
    for (const lane of task.inventoryLanes ?? []) {
      if (!laneIds.has(lane)) fail('Task references an unknown inventory lane: ' + task.id + '/' + lane);
      ownedLanes.add(lane);
    }
  }
  for (const rule of config.inventory) {
    if (rule.required !== false && !ownedLanes.has(rule.id)) {
      fail('Required test inventory has no registered native task: ' + rule.id);
    }
  }
  if (!Array.isArray(config.requiredCommands ?? [])) {
    fail('Required commands must be declared as an array.');
  }
  for (const runtime of config.runtimes ?? []) {
    if (!runtime || typeof runtime.command !== 'string' || !runtime.command ||
        !Array.isArray(runtime.args ?? [])) {
      fail('Runtime declarations require an executable and an argument array.');
    }
    if (runtime.versionCheck &&
        (typeof runtime.versionCheck.prefix !== 'string' || !runtime.versionCheck.prefix ||
         runtime.versionCheck.prefix.length > 128 ||
         !VERSION_BOUNDARIES.has(runtime.versionCheck.boundary))) {
      fail('Runtime version checks require a prefix and a supported boundary.');
    }
  }
  for (const task of config.tasks) {
    if (!Array.isArray(task.runtimes ?? [])) {
      fail('Task runtime declarations must be an array: ' + task.id);
    }
    for (const runtime of task.runtimes ?? []) {
      if (!runtime || typeof runtime.command !== 'string' || !runtime.command ||
          !Array.isArray(runtime.args ?? [])) {
        fail('Task runtime declarations require an executable and an argument array: ' + task.id);
      }
      if (runtime.versionCheck &&
          (typeof runtime.versionCheck.prefix !== 'string' || !runtime.versionCheck.prefix ||
           runtime.versionCheck.prefix.length > 128 ||
           !VERSION_BOUNDARIES.has(runtime.versionCheck.boundary))) {
        fail('Task runtime version checks require a prefix and a supported boundary: ' + task.id);
      }
    }
  }
  for (const task of config.tasks) {
    for (const dependency of task.dependsOn ?? []) {
      if (!ids.has(dependency)) fail('Unknown task dependency: ' + dependency);
    }
  }
  const visiting = new Set();
  const visited = new Set();
  const visit = (id) => {
    if (visiting.has(id)) fail('Validation task dependency cycle includes: ' + id);
    if (visited.has(id)) return;
    visiting.add(id);
    const task = config.tasks.find((item) => item.id === id);
    for (const dependency of task.dependsOn ?? []) visit(dependency);
    visiting.delete(id);
    visited.add(id);
  };
  for (const task of config.tasks) visit(task.id);
}

export function createPlan(root, config, options = {}) {
  validateConfig(config);
  const inventory = discoverInventory(root, config.inventory);
  const candidate = captureCandidate(root, config.inputs ?? [], inventory);
  const inventoryLaneDigests = Object.fromEntries(config.inventory.map((rule) => [
    rule.id,
    hash(stable(inventory.entries.filter((entry) => entry.lane === rule.id))),
  ]));
  const selectedIds = new Set();
  const addTaskAndDependencies = (id) => {
    const task = config.tasks.find((item) => item.id === id);
    if (!task) fail('Unknown validation task: ' + id);
    if (selectedIds.has(id)) return;
    selectedIds.add(id);
    for (const dependency of task.dependsOn ?? []) addTaskAndDependencies(dependency);
  };
  if (options.task) addTaskAndDependencies(options.task);
  else if (options.testsOnly) {
    for (const task of config.tasks) {
      if (task.kind === 'test' && task.defaultSelected !== false) addTaskAndDependencies(task.id);
    }
  } else {
    for (const task of config.tasks) {
      if (task.defaultSelected !== false) addTaskAndDependencies(task.id);
    }
  }
  if (options.testsOnly && selectedIds.size === 0) fail('No test tasks are registered.');
  const taskById = new Map(config.tasks.map((task) => [task.id, task]));
  const orderedIds = [];
  const orderedSeen = new Set();
  const orderTask = (id) => {
    if (orderedSeen.has(id)) return;
    orderedSeen.add(id);
    for (const dependency of taskById.get(id).dependsOn ?? []) {
      if (selectedIds.has(dependency)) orderTask(dependency);
    }
    orderedIds.push(id);
  };
  for (const task of config.tasks) if (selectedIds.has(task.id)) orderTask(task.id);
  const selectedTasks = orderedIds.map((id) => taskById.get(id));
  const prerequisites = [...new Set([
    ...(config.requiredCommands ?? []),
    ...selectedTasks.flatMap((task) => [task.command[0], ...(task.requiredCommands ?? [])]),
  ])]
    .map((command) => ({ command, available: commandAvailable(command) }));
  const runtimeMap = new Map();
  for (const runtime of [
    ...(config.runtimes ?? []),
    ...selectedTasks.flatMap((task) => task.runtimes ?? []),
  ]) {
    runtimeMap.set(stable({ command: runtime.command, args: runtime.args ?? [], env: runtime.env ?? {} }), runtime);
  }
  const runtimes = [...runtimeMap.values()].map((runtime) => inspectRuntime(root, runtime));
  const executionContext = {
    executor: process.env.GITHUB_ACTIONS === 'true' ? 'github-actions' : 'local',
    platform: process.platform,
    architecture: process.arch,
    nodeVersion: process.version,
    nodeId: process.env.VALIDATION_NODE_ID ?? null,
    runner: process.env.GITHUB_ACTIONS === 'true' ? {
      name: process.env.RUNNER_NAME ?? null,
      os: process.env.RUNNER_OS ?? process.platform,
      architecture: process.env.RUNNER_ARCH ?? process.arch,
    } : null,
    github: process.env.GITHUB_ACTIONS === 'true' ? {
      workflow: process.env.GITHUB_WORKFLOW ?? null,
      job: process.env.GITHUB_JOB ?? null,
      runId: process.env.GITHUB_RUN_ID ?? null,
      runAttempt: process.env.GITHUB_RUN_ATTEMPT ?? null,
      eventName: process.env.GITHUB_EVENT_NAME ?? null,
      sha: process.env.GITHUB_SHA ?? null,
    } : null,
  };
  const plan = {
    schemaVersion: ENGINE_VERSION,
    repository: config.repository,
    selection: options.task ? 'task:' + options.task : options.testsOnly ? 'tests-only' : 'full',
    candidate,
    inventory: inventory.entries,
    inventoryCounts: inventory.laneCounts,
    inventoryLaneDigests,
    prerequisites,
    runtimes,
    executionContext,
    tasks: [...selectedTasks, ...config.tasks.filter((task) => !selectedIds.has(task.id))].map((task) => ({
      id: task.id,
      name: task.name,
      stage: task.stage,
      kind: task.kind,
      required: task.required !== false,
      selected: selectedIds.has(task.id),
      exclusionReason: task.exclusionReason ?? null,
      dependsOn: task.dependsOn ?? [],
      requiredCommands: task.requiredCommands ?? [],
      timeoutSeconds: task.timeoutSeconds ?? 3600,
      command: task.command,
      cwd: task.cwd ?? '.',
      caseParser: task.caseParser ?? null,
      minimumCases: task.minimumCases ?? null,
      envKeys: [...new Set([
        ...Object.keys(task.env ?? {}),
        ...(task.passEnv ?? []),
      ])].sort(),
      inventoryLanes: task.inventoryLanes ?? [],
    })),
  };
  plan.planSha256 = hash(stable(plan));
  return plan;
}

export function isolatedTaskEnvironment(task, runRoot, inherited = process.env) {
  if (typeof task?.id !== 'string' || !/^[a-z0-9][a-z0-9-]*$/.test(task.id)) {
    fail('Validation task ID must be a safe lowercase identifier.');
  }
  const environmentRoot = path.join(runRoot, `${task.id}-environment`);
  const env = privateEnvironment(
    task.env ?? {},
    environmentRoot,
    path.join(runRoot, 'cargo-home'),
    inherited,
  );
  const approvedPassEnv = APPROVED_TASK_PASS_ENVIRONMENT.get(task.id) ?? new Set();
  const passEnv = task.passEnv ?? [];
  if (!Array.isArray(passEnv) || passEnv.some((name) =>
    typeof name !== 'string' || !approvedPassEnv.has(name))) {
    fail('Task requests an unapproved inherited environment variable: ' + task.id);
  }
  for (const name of passEnv) {
    const match = Object.entries(inherited).find(([key]) => key.toUpperCase() === name.toUpperCase());
    if (match && typeof match[1] === 'string') env[name] = match[1];
  }
  if (task.kind === 'test') env.NODE_ENV = 'test';
  return env;
}

function terminate(child) {
  if (child.pid && process.platform !== 'win32') {
    try {
      process.kill(-child.pid, 'SIGTERM');
      return;
    } catch {
      // The process group may exit between the child status check and this signal.
    }
  }
  child.kill('SIGTERM');
}

export async function runCommand(task, root, logPath) {
  const startedAt = new Date().toISOString();
  const started = Date.now();
  const command = task.command[0];
  const args = task.command.slice(1);
  const cwd = path.resolve(root, task.cwd ?? '.');
  if (cwd !== root && !cwd.startsWith(root + path.sep)) {
    fail('Task working directory escapes the repository: ' + task.id);
  }
  const timeout = task.timeoutSeconds ?? 3600;
  let stdout = '';
  let stderr = '';
  let outputBytes = 0;
  let timedOut = false;
  const logDescriptor = openSync(logPath, 'wx', 0o600);
  const logContentLimit = MAX_LOG_BYTES - LOG_TRUNCATION_MARKER.length;
  let logBytesWritten = 0;
  let logTruncated = false;
  let child;
  const append = (chunk, target) => {
    outputBytes += chunk.length;
    target.value += chunk.toString('utf8');
    if (target.value.length > MAX_BUFFER) target.value = target.value.slice(-MAX_BUFFER);
  };
  const persist = (chunk) => {
    const length = Math.min(chunk.length, logContentLimit - logBytesWritten);
    let offset = 0;
    while (offset < length) {
      offset += writeSync(logDescriptor, chunk, offset, length - offset);
    }
    logBytesWritten += length;
    if (length < chunk.length) logTruncated = true;
  };
  const out = { value: stdout };
  const err = { value: stderr };
  let exit;
  try {
    child = spawn(command, args, {
      cwd,
      env: isolatedTaskEnvironment(task, path.dirname(logPath)),
      stdio: ['ignore', 'pipe', 'pipe'],
      detached: process.platform !== 'win32',
      windowsHide: true,
    });
    child.stdout.on('data', (chunk) => {
      append(chunk, out);
      persist(chunk);
    });
    child.stderr.on('data', (chunk) => {
      append(chunk, err);
      persist(chunk);
    });
    const timer = setTimeout(() => {
      timedOut = true;
      terminate(child);
      setTimeout(() => {
        if (child.exitCode === null && child.signalCode === null) {
          if (child.pid && process.platform !== 'win32') {
            try {
              process.kill(-child.pid, 'SIGKILL');
            } catch {
              // The process group may exit between the child status check and this signal.
            }
          } else {
            child.kill('SIGKILL');
          }
        }
      }, 2000).unref();
    }, timeout * 1000);
    let spawnError = null;
    exit = await new Promise((resolve) => {
      child.once('error', (error) => {
        spawnError = error;
      });
      child.once('close', (code, signal) => resolve({ code, signal, error: spawnError }));
    }).finally(() => clearTimeout(timer));
  } finally {
    if (logTruncated) writeSync(logDescriptor, LOG_TRUNCATION_MARKER);
    fsyncSync(logDescriptor);
    closeSync(logDescriptor);
  }
  stdout = out.value;
  stderr = err.value;
  const combined = stdout + (stdout && stderr ? '\n' : '') + stderr;
  const logBuffer = readFileSync(logPath);
  const activeCases = task.caseParser ? parseCaseCount(task.caseParser, combined) : null;
  const status = timedOut || exit.error || exit.code !== 0
    ? 'failed'
    : task.kind === 'test' && activeCases < task.minimumCases
      ? 'incomplete'
      : 'passed';
  return {
    taskId: task.id,
    status,
    startedAt,
    durationMs: Date.now() - started,
    exitCode: exit.code,
    signal: exit.signal,
    error: exit.error?.message,
    timedOut,
    outputBytes,
    logSha256: hash(logBuffer),
    logFile: path.basename(logPath),
    activeCases,
    envKeys: [...new Set([
      ...Object.keys(task.env ?? {}),
      ...(task.passEnv ?? []),
    ])].sort(),
    required: task.required !== false,
  };
}

export async function executePlan(root, config, plan, options = {}) {
  const { planSha256, ...planBody } = plan;
  if (plan.repository !== config.repository || !planSha256 || hash(stable(planBody)) !== planSha256) {
    fail('Validation plan digest does not match its contents.');
  }
  const runnerTemp = process.env.RUNNER_TEMP;
  const temporaryRoot = typeof runnerTemp === 'string' && path.isAbsolute(runnerTemp)
    ? runnerTemp
    : os.tmpdir();
  const runRoot = options.runRoot ?? mkdtempSync(path.join(temporaryRoot, config.repository + '-validation-'));
  mkdirSync(runRoot, { recursive: true, mode: 0o700 });
  chmodSync(runRoot, 0o700);
  const runId = randomUUID();
  const startedAt = new Date().toISOString();
  const receiptById = new Map();
  const selectedIds = new Set(plan.tasks.filter((task) => task.selected).map((task) => task.id));
  for (const task of plan.tasks) {
    if (!task.selected) {
      receiptById.set(task.id, {
        taskId: task.id,
        status: 'excluded',
        reason: task.exclusionReason ?? plan.selection,
        required: task.required,
      });
    }
  }
  const missing = [
    ...plan.prerequisites.filter((item) => !item.available),
    ...(plan.runtimes ?? []).filter((item) => item.required !== false &&
      (!item.available || !item.versionCompatible)),
    ...(plan.executionContext?.executor === 'github-actions' &&
      plan.executionContext.github?.sha !== plan.candidate.commit
      ? [{ command: 'GITHUB_SHA', available: false, expected: plan.candidate.commit,
        actual: plan.executionContext.github?.sha ?? null }]
      : []),
  ];
  if (missing.length > 0) {
    const receipt = {
      schemaVersion: ENGINE_VERSION,
      runId,
      startedAt,
      completedAt: new Date().toISOString(),
      planSha256: plan.planSha256,
      candidate: plan.candidate,
      executionContext: plan.executionContext,
      status: 'incomplete',
      prerequisites: missing,
      tasks: plan.tasks.map((task) => task.selected ? ({
        taskId: task.id,
        status: 'not-run',
        reason: 'required command is unavailable',
        required: task.required,
      }) : receiptById.get(task.id)),
      totals: { planned: selectedIds.size, executed: 0, passed: 0, failed: 0, blocked: 0, excluded: plan.tasks.length - selectedIds.size, activeCases: 0 },
    };
    writeFileSync(path.join(runRoot, 'receipt.json'), JSON.stringify(receipt, null, 2), { mode: 0o600 });
    return { receipt, runRoot, exitCode: 1 };
  }

  let sourceChanged = false;
  const selectedTasks = plan.tasks.filter((item) => item.selected);
  let lastProgressSummary = null;
  const reportProgress = (currentTask = null, taskStartedAt = 0) => {
    if (typeof options.onProgress !== 'function') return;
    const summary = formatValidationProgress(
      config.repository,
      selectedTasks,
      receiptById,
      currentTask,
      currentTask ? Date.now() - taskStartedAt : 0,
    );
    if (summary === lastProgressSummary) return;
    lastProgressSummary = summary;
    options.onProgress(summary);
  };
  for (const task of selectedTasks) {
    const dependencyReceipts = (task.dependsOn ?? []).map((id) => receiptById.get(id));
    const failedDependency = dependencyReceipts.find((item) => item?.status !== 'passed');
    if (failedDependency) {
      receiptById.set(task.id, {
        taskId: task.id,
        status: 'blocked',
        reason: 'dependency did not pass',
        required: task.required !== false,
      });
      reportProgress();
      continue;
    }
    if (captureCandidate(root, config.inputs ?? [], {
      entries: plan.inventory,
    }).sourceSha256 !== plan.candidate.sourceSha256) {
      sourceChanged = true;
      receiptById.set(task.id, {
        taskId: task.id,
        status: 'blocked',
        reason: 'candidate source changed after planning',
        required: task.required !== false,
      });
      reportProgress();
      break;
    }
    const configuredTask = config.tasks.find((item) => item.id === task.id);
    if (!configuredTask) fail('Selected task is missing from the registered configuration: ' + task.id);
    const taskStartedAt = Date.now();
    reportProgress(task, taskStartedAt);
    const heartbeat = setInterval(() => reportProgress(task, taskStartedAt), PROGRESS_INTERVAL_MS);
    heartbeat.unref();
    let taskReceipt;
    try {
      taskReceipt = await runCommand(
        configuredTask,
        root,
        path.join(runRoot, task.id + '.log'),
      );
    } finally {
      clearInterval(heartbeat);
    }
    taskReceipt.inventory = (configuredTask.inventoryLanes ?? []).map((lane) => ({
      lane,
      discoveredFiles: plan.inventoryCounts[lane] ?? 0,
      inventorySha256: plan.inventoryLaneDigests[lane],
    }));
    receiptById.set(task.id, taskReceipt);
    reportProgress();
    if (captureCandidate(root, config.inputs ?? [], {
      entries: plan.inventory,
    }).sourceSha256 !== plan.candidate.sourceSha256) {
      sourceChanged = true;
      break;
    }
  }
  for (const task of plan.tasks) {
    if (!receiptById.has(task.id)) {
      receiptById.set(task.id, {
        taskId: task.id,
        status: sourceChanged ? 'blocked' : 'excluded',
        reason: sourceChanged ? 'candidate source changed during execution' : 'not selected',
        required: task.required,
      });
    }
  }
  const tasks = plan.tasks.map((task) => receiptById.get(task.id));
  const totals = {
    planned: selectedIds.size,
    executed: tasks.filter((task) => task.startedAt).length,
    passed: tasks.filter((task) => task.status === 'passed').length,
    failed: tasks.filter((task) => task.status === 'failed' || task.status === 'incomplete').length,
    blocked: tasks.filter((task) => task.status === 'blocked').length,
    excluded: tasks.filter((task) => task.status === 'excluded').length,
    activeCases: tasks.reduce((sum, task) => sum + (task.activeCases ?? 0), 0),
  };
  const status = sourceChanged || missing.length > 0 ||
    plan.tasks.some((task) => task.selected && task.required !== false && receiptById.get(task.id)?.status !== 'passed')
    ? 'failed'
    : 'passed';
  const receipt = {
    schemaVersion: ENGINE_VERSION,
    repository: config.repository,
    selection: plan.selection,
    runId,
    startedAt,
    completedAt: new Date().toISOString(),
    planSha256: plan.planSha256,
    candidate: plan.candidate,
    inventoryCounts: plan.inventoryCounts,
    inventoryLaneDigests: plan.inventoryLaneDigests,
    executionContext: plan.executionContext,
    status,
    prerequisites: plan.prerequisites,
    runtimes: plan.runtimes,
    tasks,
    totals,
  };
  reportProgress();
  writeFileSync(path.join(runRoot, 'receipt.json'), JSON.stringify(receipt, null, 2), { mode: 0o600 });
  return { receipt, runRoot, exitCode: status === 'passed' ? 0 : 1 };
}

function help(config) {
  return [
    config.repository + ' validation engine',
    '',
    'Usage:',
    '  node scripts/validate-development.mjs --help',
    '  node scripts/validate-development.mjs --plan [--json]',
    '  node scripts/validate-development.mjs --tests-only',
    '  node scripts/validate-development.mjs',
    '',
    'The plan is read-only. Native test commands and assertions remain authoritative.',
    'Every run binds the current Git source snapshot, executes without test-result reuse,',
    'and writes attempt evidence under the operating system temporary directory.',
  ].join('\n');
}

export async function main(argv = process.argv.slice(2), root = DEFAULT_ROOT, config) {
  const loaded = config ?? (await import(pathToFileURL(path.join(ENGINE_DIR, 'config.mjs')).href)).validation;
  const args = [...argv];
  if (args.includes('--help')) {
    process.stdout.write(help(loaded) + '\n');
    return 0;
  }
  const planIndex = args.indexOf('--plan');
  const json = args.includes('--json');
  const testsOnly = args.includes('--tests-only');
  let taskId;
  const taskIndex = args.indexOf('--task');
  if (taskIndex >= 0) {
    taskId = args[taskIndex + 1];
    if (!taskId) fail('--task requires a registered task ID.');
  }
  const known = new Set(['--plan', '--json', '--tests-only', '--task']);
  for (let index = 0; index < args.length; index += 1) {
    if (!known.has(args[index])) fail('Unknown option: ' + args[index]);
    if (args[index] === '--task') index += 1;
  }
  const plan = createPlan(root, loaded, { testsOnly, task: taskId });
  if (planIndex >= 0) {
    process.stdout.write(json
      ? JSON.stringify(plan, null, 2) + '\n'
      : loaded.repository + ': ' + plan.inventory.length + ' test files; ' +
        plan.tasks.length + ' planned tasks; ' +
        plan.prerequisites.filter((item) => item.available).length + '/' +
        plan.prerequisites.length + ' command prerequisites available.\n');
    return 0;
  }
  if (plan.tasks.some((task) => task.selected && task.kind === 'test')) {
    requireTrustedLocalTestSandbox();
  }
  const lock = acquireRunLock(root, loaded.repository);
  let result;
  try {
    result = await executePlan(root, loaded, plan, {
      onProgress: (summary) => process.stderr.write(summary + '\n'),
    });
  } finally {
    releaseRunLock(lock);
  }
  const receiptExport = process.env.VALIDATION_RECEIPT_EXPORT;
  if (receiptExport) {
    const target = path.resolve(receiptExport);
    const exportRoots = [os.tmpdir(), process.env.RUNNER_TEMP]
      .filter(Boolean)
      .map((directory) => path.resolve(directory));
    if (!exportRoots.some((directory) => target.startsWith(directory + path.sep))) {
      fail('Validation receipts may only be exported beneath the system or runner temporary directory.');
    }
    mkdirSync(path.dirname(target), { recursive: true, mode: 0o700 });
    const actualParent = realpathSync(path.dirname(target));
    const realRoots = exportRoots.filter((directory) => existsSync(directory)).map((directory) => realpathSync(directory));
    if (!realRoots.some((directory) => actualParent === directory || actualParent.startsWith(directory + path.sep))) {
      fail('Validation receipt export resolves outside the system or runner temporary directory.');
    }
    try {
      if (lstatSync(target).isSymbolicLink()) fail('Validation receipt export cannot replace a symbolic link.');
    } catch (error) {
      if (error.code !== 'ENOENT') throw error;
    }
    writeFileSync(target, JSON.stringify(result.receipt, null, 2), { mode: 0o600 });
  }
  process.stdout.write(JSON.stringify({
    repository: loaded.repository,
    status: result.receipt.status,
    planSha256: result.receipt.planSha256,
    totals: result.receipt.totals,
    evidenceDirectory: result.runRoot,
  }, null, 2) + '\n');
  return result.exitCode;
}

if (process.argv[1] && import.meta.url === pathToFileURL(path.resolve(process.argv[1])).href) {
  main().then((code) => {
    process.exitCode = code;
  }).catch((error) => {
    process.stderr.write(String(error?.stack ?? error) + '\n');
    process.exitCode = 1;
  });
}
