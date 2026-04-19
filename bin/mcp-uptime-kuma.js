#!/usr/bin/env node
import { spawn } from 'child_process';
import { fileURLToPath } from 'url';
import { dirname, resolve } from 'path';

const __dirname = dirname(fileURLToPath(import.meta.url));

const proc = spawn('uv', ['run', 'mcp-uptime-kuma'], {
  stdio: 'inherit',
  env: process.env,
  cwd: resolve(__dirname, '..'),
});

proc.on('exit', (code) => process.exit(code ?? 1));
proc.on('error', (err) => {
  process.stderr.write(`Failed to start mcp-uptime-kuma: ${err.message}\n`);
  process.exit(1);
});
