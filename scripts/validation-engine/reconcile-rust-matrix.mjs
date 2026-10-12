#!/usr/bin/env node
// Copyright (c) slskR contributors. All rights reserved.
import { readFileSync, readdirSync } from 'node:fs';
import path from 'node:path';
import process from 'node:process';
import { pathToFileURL } from 'node:url';

const EXPECTED_NODES = [
  { id: 'linux-x64', os: 'Linux', arch: 'X64' },
  { id: 'linux-aarch64', os: 'Linux', arch: 'ARM64' },
  { id: 'macos-x64', os: 'macOS', arch: 'X64' },
  { id: 'macos-arm64', os: 'macOS', arch: 'ARM64' },
  { id: 'windows-x64', os: 'Windows', arch: 'X64' },
];
const TEST_TASK = 'rust-workspace-tests';
const REQUIRED_LANES = ['rust-inline-tests', 'rust-integration-tests'];

function fail(message) {
  throw new Error(message);
}

function sourceIdentity(candidate) {
  return JSON.stringify({
    commit: candidate?.commit,
    tree: candidate?.tree,
    sourceSha256: candidate?.sourceSha256,
    inventorySha256: candidate?.inventorySha256,
    inputDigests: candidate?.inputDigests,
  });
}

export function reconcileRustReceipts({ receipts, runId, runAttempt, sha }) {
  if (!runId || !runAttempt || !/^[a-f0-9]{40}$/.test(sha ?? '')) {
    fail('A GitHub run ID, attempt, and full source commit are required.');
  }
  if (!Array.isArray(receipts) || receipts.length !== EXPECTED_NODES.length) {
    fail('Expected exactly one Rust workspace test receipt from each configured native runner.');
  }

  const byNode = new Map();
  for (const receipt of receipts) {
    const nodeId = receipt.executionContext?.nodeId;
    if (!EXPECTED_NODES.some((node) => node.id === nodeId)) {
      fail('A Rust receipt does not identify a configured native runner.');
    }
    if (byNode.has(nodeId)) fail('Duplicate Rust test receipt for ' + nodeId + '.');
    byNode.set(nodeId, receipt);
  }
  if (EXPECTED_NODES.some((node) => !byNode.has(node.id))) {
    fail('A required Rust native runner receipt is missing.');
  }

  let sharedSource;
  let sharedInventory;
  let totalCases = 0;
  const nodes = [];
  for (const expected of EXPECTED_NODES) {
    const receipt = byNode.get(expected.id);
    const task = (receipt.tasks ?? []).find((item) => item.taskId === TEST_TASK);
    const context = receipt.executionContext;
    const github = context?.github;
    if (receipt.schemaVersion !== 1 || receipt.repository !== 'slskr' ||
        !['task:' + TEST_TASK, 'tests-only'].includes(receipt.selection) || receipt.status !== 'passed' ||
        task?.status !== 'passed' || !Number.isInteger(task.activeCases) || task.activeCases < 1 ||
        !Number.isInteger(receipt.totals?.activeCases) || receipt.totals.activeCases < task.activeCases) {
      fail(expected.id + ' did not report passing Rust tests with a positive native case count.');
    }
    if (context.executor !== 'github-actions' || context.nodeId !== expected.id ||
        context.runner?.os !== expected.os || context.runner?.architecture !== expected.arch) {
      fail(expected.id + ' receipt does not match the configured GitHub runner identity.');
    }
    if (String(github?.runId) !== String(runId) || String(github?.runAttempt) !== String(runAttempt) ||
        github?.sha !== sha || receipt.candidate?.commit !== sha) {
      fail(expected.id + ' receipt belongs to a different workflow run, attempt, or commit.');
    }
    const candidate = receipt.candidate;
    if (!/^[a-f0-9]{40}$/.test(candidate?.tree ?? '') ||
        !/^[a-f0-9]{64}$/.test(candidate?.sourceSha256 ?? '') ||
        !/^[a-f0-9]{64}$/.test(candidate?.inventorySha256 ?? '') ||
        !Array.isArray(candidate?.inputDigests)) {
      fail(expected.id + ' receipt has an invalid source snapshot identity.');
    }
    const source = sourceIdentity(candidate);
    if (sharedSource !== undefined && source !== sharedSource) {
      fail('Rust runner receipts were produced from different source snapshots.');
    }
    sharedSource ??= source;

    const counts = receipt.inventoryCounts;
    const digests = receipt.inventoryLaneDigests;
    const inventory = JSON.stringify({ counts, digests });
    if (REQUIRED_LANES.some((lane) => !Number.isInteger(counts?.[lane]) || counts[lane] < 1 ||
        !/^[a-f0-9]{64}$/.test(digests?.[lane] ?? ''))) {
      fail(expected.id + ' receipt is missing a required Rust source inventory lane.');
    }
    if (sharedInventory !== undefined && inventory !== sharedInventory) {
      fail('Rust runner receipts were produced from different test inventories.');
    }
    sharedInventory ??= inventory;

    const taskInventory = new Map((task.inventory ?? []).map((item) => [item.lane, item]));
    if (taskInventory.size !== REQUIRED_LANES.length || REQUIRED_LANES.some((lane) => {
      const item = taskInventory.get(lane);
      return !item || item.discoveredFiles !== counts[lane] || item.discoveredFiles < 1 ||
        item.inventorySha256 !== digests[lane];
    })) {
      fail(expected.id + ' task receipt does not attest both configured Rust test source lanes.');
    }
    totalCases += task.activeCases;
    nodes.push({
      id: expected.id,
      runner: context.runner.name,
      os: context.runner.os,
      arch: context.runner.architecture,
      activeCases: task.activeCases,
      completedAt: receipt.completedAt,
    });
  }
  if (totalCases < EXPECTED_NODES.length) fail('The Rust matrix recorded no active test cases.');
  return {
    schemaVersion: 1,
    repository: 'slskr',
    runId: String(runId),
    runAttempt: String(runAttempt),
    sha,
    status: 'passed',
    totalCases,
    nodes,
  };
}

function parseArgs(argv) {
  const options = {};
  for (let index = 0; index < argv.length; index += 1) {
    const key = argv[index];
    if (!key.startsWith('--')) fail('Unexpected argument: ' + key);
    const value = argv[index + 1];
    if (!value || value.startsWith('--')) fail('Missing value for ' + key + '.');
    options[key.slice(2)] = value;
    index += 1;
  }
  return options;
}

export function main(argv = process.argv.slice(2)) {
  const options = parseArgs(argv);
  if (!options.receipts) fail('Pass --receipts <directory>.');
  const directory = path.resolve(options.receipts);
  const receipts = readdirSync(directory)
    .filter((name) => /^rust-[a-z0-9-]+\.json$/.test(name))
    .map((name) => JSON.parse(readFileSync(path.join(directory, name), 'utf8')));
  const summary = reconcileRustReceipts({
    receipts,
    runId: options['run-id'] ?? process.env.GITHUB_RUN_ID,
    runAttempt: options['run-attempt'] ?? process.env.GITHUB_RUN_ATTEMPT,
    sha: options.sha ?? process.env.GITHUB_SHA,
  });
  process.stdout.write(JSON.stringify(summary, null, 2) + '\n');
  return 0;
}

if (process.argv[1] && import.meta.url === pathToFileURL(path.resolve(process.argv[1])).href) {
  try {
    process.exitCode = main();
  } catch (error) {
    process.stderr.write(String(error?.stack ?? error) + '\n');
    process.exitCode = 1;
  }
}
