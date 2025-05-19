import { newApp } from "./lib/hono.js";
import desktop from "./routes/desktop.js";
import { serve } from "@hono/node-server";
import * as dotenv from 'dotenv'
import posthogClient from './lib/posthog.js';
export * as schema from "./db/schema.js"

// Load environment variables from .env.local file
dotenv.config()

const app = newApp();

// app.use(initCache());
// app.use(initRatelimiter());

app.route("/v1/", desktop);

// Use PORT environment variable with fallback to 3000 for local development
const port = process.env.PORT ? parseInt(process.env.PORT) : 3000;

const server = serve(
  {
    fetch: app.fetch,
    port: port
  },
  (info) => {
    console.log(`Server is running on port ${info.port}`);
  }
);

// Graceful shutdown logic
async function gracefulShutdown(signal: string) {
  console.log(`Received ${signal}. Shutting down gracefully...`);

  // 1. Stop the HTTP server from accepting new connections
  // The `serve` function from `@hono/node-server` returns a Node.js http.Server instance.
  // We need to ensure it has a `close` method.
  if (server && typeof (server as any).close === 'function') {
    (server as any).close((err?: Error) => { // Added optional err parameter
      if (err) {
        console.error('Error during server shutdown:', err);
        // process.exit(1); // Optionally exit with error, but PostHog shutdown should still be attempted
      }
      console.log('HTTP server closed.');
    });
  } else {
    console.warn('Server instance does not have a close method or is undefined.');
  }
  
  // 2. Shutdown PostHog client
  try {
    console.log('Flushing PostHog events...');
    await posthogClient.shutdown();
    console.log('PostHog client shutdown successfully.');
  } catch (error) {
    console.error('Error shutting down PostHog client:', error);
  }

  // Add any other cleanup tasks here (e.g., closing database connections)

  console.log('Graceful shutdown process complete. Exiting process.');
  process.exit(0); // Exit successfully
}

process.on('SIGINT', () => gracefulShutdown('SIGINT'));
process.on('SIGTERM', () => gracefulShutdown('SIGTERM'));
