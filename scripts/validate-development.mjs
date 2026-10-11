#!/usr/bin/env node
// Copyright (c) slskR contributors. All rights reserved.
import process from 'node:process';
import { pathToFileURL } from 'node:url';
import path from 'node:path';
import { main } from './validation-engine/engine.mjs';

if (process.argv[1] && import.meta.url === pathToFileURL(path.resolve(process.argv[1])).href) {
  main().then((code) => {
    process.exitCode = code;
  }).catch((error) => {
    process.stderr.write(String(error?.stack ?? error) + '\n');
    process.exitCode = 1;
  });
}
