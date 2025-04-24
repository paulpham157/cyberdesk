import { eq, and, isNull } from "drizzle-orm";
import type { PostgresJsDatabase } from "drizzle-orm/postgres-js";
import { schema } from "./index.js";

/**
 * Creates a new desktop instance for a user
 * @param db Drizzle database instance
 * @param userId The user ID to create the desktop instance for
 * @param remoteId The remote ID of the desktop instance
 * @param streamUrl The original stream URL
 * @returns The created desktop instance
 */
export async function addDbDesktopInstance(
  db: PostgresJsDatabase<typeof schema>,
  userId: string,
  remoteId: string,
  streamUrl: string
) {
  const [newInstance] = await db
    .insert(schema.desktopInstances)
    .values({
      userId,
      remoteId,
      streamUrl,
    })
    .returning();

  return newInstance;
}

/**
 * Marks a desktop instance as ended by setting the endedAt timestamp
 * @param db Drizzle database instance
 * @param id The database ID of the desktop instance to end
 * @returns The updated desktop instance or null if not found
 */
export async function killDbDesktopInstance(
  db: PostgresJsDatabase<typeof schema>,
  id: string
) {
  const [updatedInstance] = await db
    .update(schema.desktopInstances)
    .set({
      endedAt: new Date(),
    })
    .where(eq(schema.desktopInstances.id, id))
    .returning();

  return updatedInstance || null;
}

/**
 * Gets all active desktop instances for a user (where endedAt is null)
 * @param db Drizzle database instance
 * @param userId The user ID to get desktop instances for
 * @returns Array of active desktop instances
 */
export async function getActiveDbDesktopInstances(
  db: PostgresJsDatabase<typeof schema>,
  userId: string
) {
  return db
    .select()
    .from(schema.desktopInstances)
    .where(
      and(
        eq(schema.desktopInstances.userId, userId),
        isNull(schema.desktopInstances.endedAt)
      )
    );
}

/**
 * Gets a specific desktop instance by ID
 * @param db Drizzle database instance
 * @param id The database ID of the desktop instance to get
 * @returns The desktop instance or null if not found
 */
export async function getDbDesktopInstance(
  db: PostgresJsDatabase<typeof schema>,
  id: string
) {
  const [instance] = await db
    .select()
    .from(schema.desktopInstances)
    .where(eq(schema.desktopInstances.id, id))
    .limit(1);

  return instance || null;
}
