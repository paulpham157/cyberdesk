import { pgTable, serial, text, index, varchar, uuid, timestamp, pgSchema, jsonb, boolean, pgEnum } from "drizzle-orm/pg-core";
import { sql } from "drizzle-orm";

// Define the auth schema and users table
const authSchema = pgSchema('auth');

const users = authSchema.table('users', {
  id: uuid('id').primaryKey(),
  // You can add other fields from auth.users if needed
});

// Define the profiles table
export const profiles = pgTable("profiles", {
  id: uuid("id").primaryKey().references(() => users.id, { onDelete: 'cascade' }),
  unkeyKeyId: varchar("unkey_key_id", { length: 255 }),
  stripeCustomerId: varchar("stripe_customer_id", { length: 255 }),
  stripeSubscriptionId: varchar("stripe_subscription_id", { length: 255 }),
  currentPeriodEnd: timestamp("current_period_end"),
  subscriptionStatus: varchar("subscription_status", { length: 50 }),
  planId: varchar("plan_id", { length: 100 }),
  cancelAtPeriodEnd: boolean("cancel_at_period_end").default(false),
  createdAt: timestamp("created_at").defaultNow(),
  updatedAt: timestamp("updated_at").defaultNow(),
});

// Define the status enum type
export const instanceStatusEnum = pgEnum('instance_status', ['pending', 'running', 'terminated', 'error']);

// Define the desktop_instances table
export const desktopInstances = pgTable("desktop_instances", {
  id: uuid("id").primaryKey().defaultRandom(),
  remoteId: varchar("remote_id", { length: 255 }).notNull(),
  userId: uuid("user_id").notNull().references(() => users.id, { onDelete: 'cascade' }), // Required field
  streamUrl: varchar("stream_url", { length: 1024 }).notNull().default("https://placeholder-stream-url.cyberdesk.io"), // Default value for existing records
  createdAt: timestamp("created_at").defaultNow(),
  endedAt: timestamp("ended_at"), // Optional field (nullable by default)
});

// Define the cyberdesk_instances table (MVP 3)
export const cyberdeskInstances = pgTable("cyberdesk_instances", {
  id: uuid("id").primaryKey().defaultRandom(),
  userId: uuid("user_id").notNull().references(() => users.id, { onDelete: 'cascade' }), // Required field
  createdAt: timestamp("created_at").defaultNow(),
  updatedAt: timestamp("updated_at"),
  status: instanceStatusEnum("status").notNull().default("pending"),
  timeoutAt: timestamp("timeout_at").notNull().default(sql`NOW() + interval '24 hours'`), // Set default to 24 hours from now
  streamUrl: varchar("stream_url", { length: 1024 })
});
