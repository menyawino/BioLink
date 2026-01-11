import { spawn } from 'child_process';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const rootDir = join(__dirname, '..');

console.log('\x1b[34m%s\x1b[0m', '🚀 Starting BioLink Application...\n');

// Track running processes
const processes = [];

// Function to start PostgreSQL
function startDatabase() {
  return new Promise((resolve) => {
    console.log('\x1b[32m%s\x1b[0m', '📊 Starting PostgreSQL...');
    
    const db = spawn('mamba', [
      'run', '-n', 'gcloud',
      'pg_ctl', '-D', join(rootDir, 'backend/pgdata'),
      '-l', join(rootDir, 'backend/pgdata/logfile'),
      'start'
    ], { shell: true });

    db.stdout.on('data', (data) => {
      console.log(`[DB] ${data}`);
    });

    db.stderr.on('data', (data) => {
      console.log(`[DB] ${data}`);
    });

    // Wait a bit for DB to start
    setTimeout(() => {
      console.log('\x1b[32m%s\x1b[0m', '✓ PostgreSQL started\n');
      resolve();
    }, 3000);
  });
}

// Function to start backend
function startBackend() {
  console.log('\x1b[32m%s\x1b[0m', '⚙️  Starting Backend Server...');
  
  const backend = spawn('npm', ['run', 'dev'], {
    cwd: join(rootDir, 'backend'),
    shell: true,
    stdio: 'inherit'
  });

  processes.push(backend);
  
  return new Promise((resolve) => {
    setTimeout(() => {
      console.log('\x1b[32m%s\x1b[0m', '✓ Backend started at http://localhost:3001\n');
      resolve();
    }, 2000);
  });
}

// Function to start frontend
function startFrontend() {
  console.log('\x1b[32m%s\x1b[0m', '🎨 Starting Frontend Server...');
  
  const frontend = spawn('npm', ['run', 'dev'], {
    cwd: rootDir,
    shell: true,
    stdio: 'inherit'
  });

  processes.push(frontend);
  
  console.log('\x1b[32m%s\x1b[0m', '✓ Frontend started at http://localhost:3000\n');
}

// Cleanup function
function cleanup() {
  console.log('\n\x1b[31m%s\x1b[0m', '🛑 Shutting down services...');
  
  processes.forEach(proc => {
    try {
      proc.kill();
    } catch (e) {
      // Ignore errors
    }
  });
  
  // Stop database
  spawn('mamba', [
    'run', '-n', 'gcloud',
    'pg_ctl', '-D', join(rootDir, 'backend/pgdata'),
    'stop'
  ], { shell: true });
  
  process.exit(0);
}

// Handle shutdown signals
process.on('SIGINT', cleanup);
process.on('SIGTERM', cleanup);

// Start all services
async function start() {
  try {
    await startDatabase();
    await startBackend();
    await startFrontend();
    
    console.log('\x1b[34m%s\x1b[0m', '\n✨ All services running!');
    console.log('\x1b[36m%s\x1b[0m', '   Frontend:  http://localhost:3000');
    console.log('\x1b[36m%s\x1b[0m', '   Backend:   http://localhost:3001');
    console.log('\x1b[33m%s\x1b[0m', '\n   Press Ctrl+C to stop all services\n');
  } catch (error) {
    console.error('\x1b[31m%s\x1b[0m', '❌ Error starting services:', error);
    cleanup();
  }
}

start();
