// Copyright (c) slskR contributors. All rights reserved.
import assert from 'node:assert/strict';
import { test } from 'node:test';
import { reconcileRustReceipts } from './reconcile-rust-matrix.mjs';

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

test('rejects missing, duplicate, and unknown runner receipts', () => {
  assert.throws(() => reconcileRustReceipts({ receipts: receipts().slice(1), ...identity }), /exactly one/);
  const duplicate = receipts();
  duplicate[4] = duplicate[0];
  assert.throws(() => reconcileRustReceipts({ receipts: duplicate, ...identity }), /Duplicate Rust/);
  const unknown = receipts();
  unknown[4].executionContext.nodeId = 'linux-musl-x64';
  assert.throws(() => reconcileRustReceipts({ receipts: unknown, ...identity }), /does not identify/);
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

test('rejects runner identity mismatches and duplicate runner claims', () => {
  const wrongOs = receipts();
  wrongOs[0].executionContext.runner.os = 'Windows';
  assert.throws(() => reconcileRustReceipts({ receipts: wrongOs, ...identity }), /runner identity/);
  const wrongNode = receipts();
  wrongNode[0].executionContext.nodeId = 'linux-aarch64';
  assert.throws(() => reconcileRustReceipts({ receipts: wrongNode, ...identity }), /Duplicate Rust/);
});

test('rejects receipts from another workflow run, attempt, or commit', () => {
  for (const change of [
    (items) => { items[0].executionContext.github.runId = '9999'; },
    (items) => { items[0].executionContext.github.runAttempt = '1'; },
    (items) => { items[0].candidate.commit = 'f'.repeat(40); },
  ]) {
    const items = receipts();
    change(items);
    assert.throws(() => reconcileRustReceipts({ receipts: items, ...identity }), /different workflow run, attempt, or commit/);
  }
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
