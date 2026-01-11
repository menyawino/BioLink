import { serve } from '@hono/node-server';
import { Hono } from 'hono';
import { cors } from 'hono/cors';
import { logger } from 'hono/logger';
import { config } from 'dotenv';

import { testConnection } from './db/connection.js';
import patients from './routes/patients.js';
import analytics from './routes/analytics.js';
import cohort from './routes/cohort.js';
import charts from './routes/charts.js';
import chat from './routes/chat.js';

config();

const app = new Hono();

// Middleware
app.use('*', cors({
  origin: ['http://localhost:5173', 'http://localhost:3000', 'http://127.0.0.1:5173'],
  allowMethods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
  allowHeaders: ['Content-Type', 'Authorization'],
  exposeHeaders: ['Content-Length'],
  maxAge: 86400,
  credentials: true
}));

app.use('*', logger());

// Health check
app.get('/', (c) => {
  return c.json({
    status: 'ok',
    name: 'BioLink API',
    version: '1.0.0',
    timestamp: new Date().toISOString()
  });
});

app.get('/health', async (c) => {
  const dbConnected = await testConnection();
  return c.json({
    status: dbConnected ? 'healthy' : 'unhealthy',
    database: dbConnected ? 'connected' : 'disconnected',
    timestamp: new Date().toISOString()
  });
});

// API Routes
app.route('/api/patients', patients);
app.route('/api/analytics', analytics);
app.route('/api/cohort', cohort);
app.route('/api/charts', charts);
app.route('/api/chat', chat);

// Error handling
app.onError((err, c) => {
  console.error('Server error:', err);
  return c.json({
    success: false,
    error: 'Internal server error',
    message: process.env.NODE_ENV === 'development' ? err.message : undefined
  }, 500);
});

app.notFound((c) => {
  return c.json({
    success: false,
    error: 'Not found'
  }, 404);
});

// Start server
const port = parseInt(process.env.PORT || '3001');

console.log(`
╔═══════════════════════════════════════════╗
║           BioLink API Server              ║
╠═══════════════════════════════════════════╣
║  Starting on port ${port}                    ║
║  Environment: ${process.env.NODE_ENV || 'development'}              ║
╚═══════════════════════════════════════════╝
`);

serve({
  fetch: app.fetch,
  port
});

console.log(`🚀 Server running at http://localhost:${port}`);
