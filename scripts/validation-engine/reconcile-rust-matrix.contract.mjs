// Copyright (c) slskR contributors. All rights reserved.
import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import { mkdirSync, mkdtempSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import path from 'node:path';
import { test } from 'node:test';
import { fileURLToPath } from 'node:url';
import { reconcileRustReceipts } from './reconcile-rust-matrix.mjs';

const reconciler = fileURLToPath(new URL('./reconcile-rust-matrix.mjs', import.meta.url));

const sha = 'a'.repeat(40);
const nodes = [
  ['linux-x64', 'Linux', 'X64'],
  ['linux-aarch64', 'Linux', 'ARM64'],
  ['macos-x64', 'macOS', 'X64'],
  ['macos-arm64', 'macOS', 'ARM64'],
  ['windows-x64', 'Windows', 'X64'],
];

function receipt(id, os, arch, overrides = {}) {
  const inventoryCounts = { 'rust-inline-tests': 24, 'rust-integration-tests': 19 };
  const inventoryLaneDigests = {
    'rust-inline-tests': '1'.repeat(64),
    'rust-integration-tests': '2'.repeat(64),
  };
  const task = {
    taskId: 'rust-workspace-tests',
    status: 'passed',
    activeCases: 125,
    inventory: Object.entries(inventoryCounts).map(([lane, discoveredFiles]) => ({
      lane,
      discoveredFiles,
      inventorySha256: inventoryLaneDigests[lane],
    })),
  };
  return {
    schemaVersion: 1,
    repository: 'slskr',
    selection: 'task:rust-workspace-tests',
    status: 'passed',
    candidate: {
      commit: sha,
      tree: 'b'.repeat(40),
      sourceSha256: 'c'.repeat(64),
      inventorySha256: 'd'.repeat(64),
      inputDigests: [{ file: 'Cargo.lock', sha256: 'e'.repeat(64) }],
    },
    executionContext: {
      executor: 'github-actions',
      nodeId: id,
      runner: { name: 'GitHub Actions 1', os, architecture: arch },
      github: { runId: '1234', runAttempt: '2', sha },
    },
    inventoryCounts,
    inventoryLaneDigests,
    totals: { activeCases: task.activeCases },
    tasks: [task],
    completedAt: '2026-10-11T00:00:00.000Z',
    ...overrides,
  };
}

function receipts() {
  return nodes.map(([id, os, arch]) => receipt(id, os, arch));
}

const identity = { runId: '1234', runAttempt: '2', sha };

test('reconciles all five passing native Rust runner receipts from one source snapshot', () => {
  const result = reconcileRustReceipts({ receipts: receipts(), ...identity });
  assert.equal(result.status, 'passed');
  assert.equal(result.nodes.length, 5);
  assert.equal(result.totalCases, 625);
  assert.deepEqual(result.nodes.map((node) => node.id), nodes.map(([id]) => id));
});

test('accepts passing receipts from earlier attempts of the same immutable workflow run', () => {
  const items = receipts();
  items[0].executionContext.github.runAttempt = '1';
  items[4].executionContext.github.runAttempt = '3';
  const result = reconcileRustReceipts({ receipts: items, ...identity, runAttempt: '3' });
  assert.equal(result.status, 'passed');
  assert.equal(result.nodes.length, 5);
});

test('selects the newest receipt per runner when reruns leave older failed artifacts', () => {
  const current = receipts();
  const stale = structuredClone(current[0]);
  stale.executionContext.github.runAttempt = '1';
  stale.status = 'failed';
  stale.tasks[0].status = 'failed';
  const result = reconcileRustReceipts({
    receipts: [stale, ...current],
    ...identity,
  });
  assert.equal(result.status, 'passed');
  assert.equal(result.nodes.length, 5);
});

test('a failed newest receipt supersedes an older passing receipt', () => {
  const current = receipts();
  const stale = structuredClone(current[0]);
  stale.executionContext.github.runAttempt = '1';
  current[0].tasks[0].status = 'failed';
  current[0].status = 'failed';
  assert.throws(
    () => reconcileRustReceipts({ receipts: [...current, stale], ...identity }),
    /passing Rust tests/u,
  );
});

test('reconciles recursively downloaded artifacts from multiple run attempts', () => {
  const directory = mkdtempSync(path.join(tmpdir(), 'rust-receipt-artifacts-'));
  try {
    const older = receipt('linux-x64', 'Linux', 'X64');
    older.executionContext.github.runAttempt = '1';
    older.status = 'failed';
    older.tasks[0].status = 'failed';
    const artifacts = [older, ...receipts()];
    for (const item of artifacts) {
      const attempt = item.executionContext.github.runAttempt;
      const node = item.executionContext.nodeId;
      const artifactDirectory = path.join(directory, `validation-rust-${node}-attempt-${attempt}`);
      mkdirSync(artifactDirectory, { recursive: true });
      writeFileSync(path.join(artifactDirectory, `rust-${node}.json`), JSON.stringify(item));
    }
    const result = spawnSync(
      process.execPath,
      [reconciler, '--receipts', directory],
      {
        encoding: 'utf8',
        env: {
          ...process.env,
          GITHUB_RUN_ID: identity.runId,
          GITHUB_RUN_ATTEMPT: identity.runAttempt,
          GITHUB_SHA: identity.sha,
        },
      }
    );
    assert.equal(result.error, undefined, result.error?.message);
    assert.equal(result.status, 0, result.stderr);
    const summary = JSON.parse(result.stdout);
    assert.equal(summary.status, 'passed');
    assert.equal(summary.nodes.length, 5);
  } finally {
    rmSync(directory, { recursive: true, force: true });
  }
});

test('rejects duplicate receipts from the same runner and attempt', () => {
  const items = receipts();
  assert.throws(
    () => reconcileRustReceipts({ receipts: [...items, structuredClone(items[0])], ...identity }),
    /Duplicate Rust test receipt/u,
  );
});

test('rejects missing, duplicate, and unknown runner receipts', () => {
  assert.throws(
    () => reconcileRustReceipts({ receipts: receipts().slice(1), ...identity }),
    /at least one Rust workspace test receipt/u,
  );
  const duplicate = receipts();
  duplicate[4] = structuredClone(duplicate[1]);
  assert.throws(() => reconcileRustReceipts({ receipts: duplicate, ...identity }), /Duplicate Rust/u);
  const unknown = receipts();
  unknown[4].executionContext.nodeId = 'linux-musl-x64';
  assert.throws(() => reconcileRustReceipts({ receipts: unknown, ...identity }), /does not identify/u);
});

test('rejects unsuccessful tasks and zero-case successes', () => {
  const failed = receipts();
  failed[0].tasks[0].status = 'failed';
  assert.throws(() => reconcileRustReceipts({ receipts: failed, ...identity }), /passing Rust tests/);
  const empty = receipts();
  empty[0].tasks[0].activeCases = 0;
  empty[0].totals.activeCases = 0;
  assert.throws(() => reconcileRustReceipts({ receipts: empty, ...identity }), /positive native case count/);
});

test('rejects runner identity mismatches and inconsistent node claims', () => {
  const wrongOs = receipts();
  wrongOs[0].executionContext.runner.os = 'Windows';
  assert.throws(() => reconcileRustReceipts({ receipts: wrongOs, ...identity }), /runner identity/u);
  const wrongNode = receipts();
  wrongNode[0].executionContext.nodeId = 'linux-aarch64';
  assert.throws(() => reconcileRustReceipts({ receipts: wrongNode, ...identity }), /configured GitHub runner identity/u);
});

test('rejects receipts from another run, future or invalid attempts, or a different commit', () => {
  for (const change of [
    (items) => { items[0].executionContext.github.runId = '9999'; },
    (items) => { items[0].executionContext.github.runAttempt = '3'; },
    (items) => { items[0].executionContext.github.runAttempt = 'not-an-attempt'; },
    (items) => { items[0].candidate.commit = 'f'.repeat(40); },
  ]) {
    const items = receipts();
    change(items);
    assert.throws(() => reconcileRustReceipts({ receipts: items, ...identity }), /different workflow run|future or invalid attempt|different commit/);
  }
  assert.throws(
    () => reconcileRustReceipts({ receipts: receipts(), ...identity, runAttempt: 'invalid' }),
    /run ID, attempt, and full source commit/,
  );
});

test('rejects source, inventory and task-attestation drift', () => {
  const source = receipts();
  source[0].candidate.sourceSha256 = '9'.repeat(64);
  assert.throws(() => reconcileRustReceipts({ receipts: source, ...identity }), /different source snapshots/);
  const inventory = receipts();
  inventory[0].inventoryLaneDigests['rust-inline-tests'] = '8'.repeat(64);
  inventory[0].tasks[0].inventory[0].inventorySha256 = '8'.repeat(64);
  assert.throws(() => reconcileRustReceipts({ receipts: inventory, ...identity }), /different test inventories/);
  const attestation = receipts();
  attestation[0].tasks[0].inventory.pop();
  assert.throws(() => reconcileRustReceipts({ receipts: attestation, ...identity }), /does not attest/);
});
