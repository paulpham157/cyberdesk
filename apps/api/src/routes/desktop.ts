import { OpenAPIHono } from "@hono/zod-openapi";
import { env } from 'hono/adapter';
import { unkey, type UnkeyContext } from "@unkey/hono";
import { z } from "@hono/zod-openapi";

import {
  bashAction,
  computerAction,
  createDesktop,
  stopDesktop,
  ComputerActionSchema,
  CreateDesktopParamsSchema
} from "../schema/desktop.js";
import { db } from "../database.js";
import { 
  addDbDesktopInstance, 
  killDbDesktopInstance,
  getDbDesktopInstance
} from "../db/dbHelpers.js";

// Type definitions
type EnvVars = {
  UNKEY_API_ID: string;
  SUPABASE_URL: string;
  SUPABASE_ANON_KEY: string;
  SUPABASE_CONNECTION_STRING?: string;
  WEB_URL: string;
};

// Use the schema type for computer actions
type ComputerAction = z.infer<typeof ComputerActionSchema>;
// Use the schema type for desktop creation parameters
type CreateDesktopParams = z.infer<typeof CreateDesktopParamsSchema>;

// Create Hono instance
const desktop = new OpenAPIHono<{
  Variables: { 
    unkey: UnkeyContext;
    userId: string;
  };
}>();

// Helper functions
const handleApiError = (c: any, error: any, message: string) => {
  console.error(`Error: ${message}:`, error);
  return c.json(
    {
      message,
      docs: "https://docs.cyberdesk.io/docs/api-reference/",
    },
    500
  );
};

const unauthorizedResponse = (c: any) => {
  return c.json(
    {
      message: "unauthorized",
      docs: "https://docs.cyberdesk.io/docs/api-reference/",
    },
    401
  );
};

// API key verification middleware
desktop.use("*", async (c, next) => {
  const { UNKEY_API_ID } = env<EnvVars>(c);
  
  const handler = unkey({
    apiId: UNKEY_API_ID,
    getKey: (c) => c.req.header("x-api-key"),
  });
  
  await handler(c, next);
});

// Authentication and database connection middleware
desktop.use("*", async (c, next) => {
  const result = c.get("unkey");
  if (!result?.valid) {
    return unauthorizedResponse(c);
  }

  const userId = result.ownerId;
  if (!userId) {
    return c.json(
      {
        message: "no user associated with this key",
        docs: "https://docs.cyberdesk.io/docs/api-reference/",
      },
      401
    );
  }
  
  c.set("userId", userId);
  
  await next();
});

// Route for creating a new desktop instance
desktop.openapi(createDesktop, async (c) => {
  const userId = c.get("userId");
  
  try {
    // Get timeout from request body if provided
    const body = await c.req.json().catch(() => ({}));
    const params = CreateDesktopParamsSchema.parse(body);
    
    // Create a new desktop instance, setting timeoutMs

    return c.json(
      {
        id: "123",
        instance_status: "pending"
      },
      200
    );
  } catch (error) {
    return handleApiError(c, error, "Failed to create desktop instance");
  }
});

// Route for stopping a desktop instance
desktop.openapi(stopDesktop, async (c) => {
  const userId = c.get("userId");
  const id = c.req.param("id");
  
  try {
    // Get the DB instance of this id
    const dbInstance = await getDbDesktopInstance(db, id);

    // Stop the Cyberdesk instance

    const success = true;

    if (!success) {
      return c.json(
        {
          message: "Failed to stop desktop instance, or the instance has already timed out.",
          docs: "https://docs.cyberdesk.io/docs/api-reference/",
        },
        500
      );
    }
    
    // Mark the Cyberdesk instance as ended in the database
    await killDbDesktopInstance(db, id);

    return c.json(
      {
        status: "stopped",
      },
      200
    );
  } catch (error) {
    return handleApiError(c, error, "Failed to stop desktop instance");
  }
});

// Helper function to handle computer actions
/**
 * Fixes keyboard key names to ensure compatibility with xdotool
 * @param key The key or keys to fix
 * @returns The fixed key or keys
 */
function fixKeyboardKeys(key: string | string[]): string | string[] {
  if (typeof key === 'string') {
    const lowerKey = key.toLowerCase();
    if (lowerKey.includes('return')) {
      return "enter";
    }
    return key;
  } else if (Array.isArray(key)) {
    // Handle arrays of keys, replacing any keys containing "return" with "enter"
    const fixedKeys = key.map(k => {
      const lowerK = k.toLowerCase();
      if (lowerK.includes('return')) {
        return "enter";
      }
      return k;
    });
    return fixedKeys;
  }
  
  // Fallback for any unexpected type
  return key;
}

async function executeComputerAction(id: string, action: ComputerAction) {
  // TODO: Implement this
}

// Route for performing a computer action on a desktop
desktop.openapi(computerAction, async (c) => {
  const id = c.req.param("id");
  const action = await c.req.json() as ComputerAction;
  
  try {
    // Get the DB instance of this id
    const dbInstance = await getDbDesktopInstance(db, id);

    // Execute the appropriate action
    try {
      const result = await executeComputerAction(dbInstance.id, action);
      
      // If it's a screenshot action, return the image data
      if (action.type === "screenshot" && result) {
        return c.json(
          {
            status: "success",
            image: result,
          },
          200
        );
      }
      
      return c.json(
        {
          status: "success",
        },
        200
      );
    } catch (actionError) {
      return c.json(
        {
          message: "Unsupported action type",
          docs: "https://docs.cyberdesk.io/docs/api-reference/",
        },
        400
      );
    }
  } catch (error) {
    return handleApiError(c, error, `Failed to execute ${action.type} action`);
  }
});

// Route for executing a bash command on a desktop
desktop.openapi(bashAction, async (c) => {
  const id = c.req.param("id");
  const { command } = await c.req.json();
  
  try {
    // Get the DB instance of this id
    const dbInstance = await getDbDesktopInstance(db, id);

    // Execute the bash command

    return c.json(
      {
        status: "success",
        output: "Hello, world!"
      },
      200
    );
  } catch (error) {
    return handleApiError(c, error, "Failed to execute bash command");
  }
});

export { desktop };
