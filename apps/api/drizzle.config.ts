import { defineConfig } from "drizzle-kit";

export default defineConfig({
  schema: "./src/db/supabase.ts",
  schemaFilter: ["public"],
  out: "./drizzle/migrations",
  dialect: "postgresql",
  dbCredentials: {
    url: process.env.SUPABASE_CONNECTION_STRING!,
  },
});
