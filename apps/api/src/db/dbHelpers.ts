import { eq, and, sql } from "drizzle-orm";
import type { PostgresJsDatabase } from "drizzle-orm/postgres-js";
import { schema } from "./index.js";
import { instanceStatusEnum } from "./supabase.js";

/**
 * Creates a new Cyberdesk instance for a user.
 * @param db Drizzle database instance
 * @param userId The user ID to create the instance for
 * @param timeoutMs Optional timeout in milliseconds. Defaults to 24 hours.
 * @returns The newly created Cyberdesk instance details (id, status)
 */
export async function addDbInstance(
  db: PostgresJsDatabase<typeof schema>,
  userId: string,
  timeoutMs?: number
) {
  const timeoutInterval = timeoutMs ? `${timeoutMs} milliseconds` : '24 hours';

  const [newInstance] = await db
    .insert(schema.cyberdeskInstances)
    .values({
      userId,
      status: 'pending',
      timeoutAt: sql`NOW() + interval '${sql.raw(timeoutInterval)}'`,
    })
    .returning({
      id: schema.cyberdeskInstances.id,
      status: schema.cyberdeskInstances.status,
    });

  return newInstance;
}

/**
 * Updates the status of a specific Cyberdesk instance, verifying ownership.
 * @param db Drizzle database instance
 * @param id The UUID of the Cyberdesk instance to update
 * @param userId The user ID making the request (for authorization)
 * @param status The new status to set
 * @returns The updated instance details or null if not found or not authorized
 */
export async function updateDbInstanceStatus(
  db: PostgresJsDatabase<typeof schema>,
  id: string,
  userId: string,
  status: typeof instanceStatusEnum.enumValues[number]
) {
  const [updatedInstance] = await db
    .update(schema.cyberdeskInstances)
    .set({
      status: status,
      updatedAt: new Date(),
    })
    .where(
      and(
        eq(schema.cyberdeskInstances.id, id),
        eq(schema.cyberdeskInstances.userId, userId)
      )
    )
    .returning({
      id: schema.cyberdeskInstances.id,
      status: schema.cyberdeskInstances.status,
    });

  return updatedInstance || null;
}

/**
 * Gets specific details (id, status, createdAt, timeoutAt) for a Cyberdesk instance by ID, verifying ownership.
 * @param db Drizzle database instance
 * @param id The UUID of the Cyberdesk instance to get details for
 * @param userId The user ID making the request (for authorization)
 * @returns The instance details or null if not found or not authorized
 */
export async function getDbInstanceDetails(
  db: PostgresJsDatabase<typeof schema>,
  id: string,
  userId: string
) {
  const [result] = await db
    .select({
      id: schema.cyberdeskInstances.id,
      status: schema.cyberdeskInstances.status,
      createdAt: schema.cyberdeskInstances.createdAt,
      timeoutAt: schema.cyberdeskInstances.timeoutAt,
    })
    .from(schema.cyberdeskInstances)
    .where(
      and(
        eq(schema.cyberdeskInstances.id, id),
        eq(schema.cyberdeskInstances.userId, userId)
      )
    )
    .limit(1);

  return result || null;
}
