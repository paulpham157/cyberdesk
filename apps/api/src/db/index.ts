import { drizzle } from "drizzle-orm/postgres-js";
import postgres from "postgres";
import type { PostgresJsDatabase } from "drizzle-orm/postgres-js";
import * as dotenv from 'dotenv';

// Ensure environment variables are loaded
dotenv.config();

import { schema } from "../index.js";

function connectDatabase(env: { SUPABASE_CONNECTION_STRING: string }): PostgresJsDatabase<typeof schema> {
  // Create a Postgres client for Drizzle
  const connectionString = env.SUPABASE_CONNECTION_STRING;
  
  const client = postgres(connectionString);
  
  // Return a Drizzle instance with the schema
  return drizzle(client, { schema });
}

// Use the connection string directly from process.env
const connectionString = process.env.SUPABASE_CONNECTION_STRING || "";

let db: PostgresJsDatabase<typeof schema>;
try {
  db = connectDatabase({
    SUPABASE_CONNECTION_STRING: connectionString,
  });
} catch (error) {
  console.error("Failed to connect to database:", error);
  throw error;
}

export { db };
