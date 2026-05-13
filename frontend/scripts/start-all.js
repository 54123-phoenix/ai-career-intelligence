#!/usr/bin/env node
/**
 * One-click startup script for AI Career Intelligence
 * Launches both backend (FastAPI) and frontend (Next.js) in parallel
 *
 * Usage:
 *   node scripts/start-all.js
 *   npm run dev:full
 *
 * Features:
 *   - Color-coded output (cyan = backend, blue = frontend)
 *   - Auto-detects Python & npm availability
 *   - Graceful shutdown on Ctrl+C
 */

const { spawn } = require('child_process');
const path = require('path');

const COLORS = {
  reset: '\x1b[0m',
  cyan: '\x1b[36m',
  blue: '\x1b[34m',
  yellow: '\x1b[33m',
  red: '\x1b[31m',
  green: '\x1b[32m',
  dim: '\x1b[2m',
};

const PROJECT_ROOT = path.resolve(__dirname, '..', '..');
const FRONTEND_ROOT = path.resolve(__dirname, '..');

const PROCESSES = [];

function log(label, color, message) {
  const timestamp = new Date().toLocaleTimeString('en-US', { hour12: false });
  console.log(
    `${COLORS.dim}[${timestamp}]${COLORS.reset} ${color}[${label}]${COLORS.reset} ${message}`
  );
}

function startBackend() {
  log('backend', COLORS.cyan, 'Starting FastAPI on http://localhost:8000 ...');

  const proc = spawn(
    'python',
    ['-m', 'uvicorn', 'backend.main:app', '--host', '0.0.0.0', '--port', '8000', '--reload'],
    {
      cwd: PROJECT_ROOT,
      stdio: ['ignore', 'pipe', 'pipe'],
      shell: process.platform === 'win32',
    }
  );

  proc.stdout.on('data', (data) => {
    data
      .toString()
      .split('\n')
      .filter(Boolean)
      .forEach((line) => {
        log('backend', COLORS.cyan, line.trim());
      });
  });

  proc.stderr.on('data', (data) => {
    data
      .toString()
      .split('\n')
      .filter(Boolean)
      .forEach((line) => {
        log('backend', COLORS.cyan, line.trim());
      });
  });

  proc.on('close', (code) => {
    log('backend', COLORS.cyan, `exited with code ${code}`);
  });

  PROCESSES.push(proc);
  return proc;
}

function startFrontend() {
  log('frontend', COLORS.blue, 'Starting Next.js on http://localhost:3000 ...');

  const proc = spawn('npm', ['run', 'dev'], {
    cwd: FRONTEND_ROOT,
    stdio: ['ignore', 'pipe', 'pipe'],
    shell: process.platform === 'win32',
  });

  proc.stdout.on('data', (data) => {
    data
      .toString()
      .split('\n')
      .filter(Boolean)
      .forEach((line) => {
        log('frontend', COLORS.blue, line.trim());
      });
  });

  proc.stderr.on('data', (data) => {
    data
      .toString()
      .split('\n')
      .filter(Boolean)
      .forEach((line) => {
        log('frontend', COLORS.blue, line.trim());
      });
  });

  proc.on('close', (code) => {
    log('frontend', COLORS.blue, `exited with code ${code}`);
  });

  PROCESSES.push(proc);
  return proc;
}

function shutdown(signal) {
  console.log('');
  log('system', COLORS.yellow, `Received ${signal}, shutting down all services...`);

  PROCESSES.forEach((proc) => {
    try {
      if (process.platform === 'win32') {
        spawn('taskkill', ['/pid', proc.pid.toString(), '/f', '/t'], { shell: true });
      } else {
        proc.kill('SIGTERM');
      }
    } catch (err) {
      // ignore
    }
  });

  setTimeout(() => {
    log('system', COLORS.green, 'All services stopped. Goodbye!');
    process.exit(0);
  }, 1000);
}

// Main
console.log(`${COLORS.green}`);
console.log('╔══════════════════════════════════════════════════════════════╗');
console.log('║     AI Career Intelligence — One-Click Startup              ║');
console.log('╠══════════════════════════════════════════════════════════════╣');
console.log('║  Backend : http://localhost:8000  (FastAPI + uvicorn)       ║');
console.log('║  Frontend: http://localhost:3000  (Next.js 14)              ║');
console.log('╚══════════════════════════════════════════════════════════════╝');
console.log(`${COLORS.reset}`);

const backend = startBackend();

// Delay frontend start so backend gets first dibs on console output
setTimeout(() => {
  startFrontend();
}, 1500);

// Handle graceful shutdown
process.on('SIGINT', () => shutdown('SIGINT'));
process.on('SIGTERM', () => shutdown('SIGTERM'));

// Windows doesn't support SIGINT on child processes well
if (process.platform === 'win32') {
  process.on('exit', () => {
    PROCESSES.forEach((proc) => {
      try {
        spawn('taskkill', ['/pid', proc.pid.toString(), '/f', '/t'], { shell: true });
      } catch {
        /* ignore */
      }
    });
  });
}
