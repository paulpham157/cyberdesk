import { OpenAPIHono } from "@hono/zod-openapi";
import { env } from 'hono/adapter';
import { unkey, type UnkeyContext } from "@unkey/hono";
import { z } from "@hono/zod-openapi";
import axios from "axios";
import { profiles, cyberdeskInstances, InstanceStatus } from "../db/schema.js";
import {
  bashAction,
  computerAction,
  createDesktop,
  stopDesktop,
  ComputerActionSchema,
  CreateDesktopParamsSchema,
  getDesktop,
} from "../schema/desktop.js";
import { db } from "../db/index.js";
import {
  addDbInstance,
  getDbInstanceDetails,
  updateDbInstanceStatus,
} from "../db/dbActions.js";

// Type definitions
type EnvVars = {
  UNKEY_API_ID: string;
  SUPABASE_URL: string;
  SUPABASE_ANON_KEY: string;
  SUPABASE_CONNECTION_STRING?: string;
  WEB_URL: string;
  GATEWAY_EXTERNAL_IP: string;
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

// Route for getting a desktop instance's details
desktop.openapi(getDesktop, async (c) => {
  const userId = c.get("userId");
  const id = c.req.param("id");

  try {
    // Fetch the instance details using the helper function (now includes userId)
    const instanceDetails = await getDbInstanceDetails(db, id, userId);

    if (!instanceDetails) {
      return c.json(
        {
          message: "Desktop instance not found or unauthorized",
          docs: "https://docs.cyberdesk.io/docs/api-reference/",
        },
        404
      );
    }

    // Return the found instance details
    return c.json(instanceDetails, 200);
  } catch (error) {
    return handleApiError(c, error, "Failed to retrieve desktop instance details");
  }
});

// Route for creating a new desktop instance
desktop.openapi(createDesktop, async (c) => {
  const { GATEWAY_EXTERNAL_IP } = env<EnvVars>(c);
  const userId = c.get("userId");

  try {
    // Get timeout from request body if provided
    const body = await c.req.json().catch(() => ({}));
    const params = CreateDesktopParamsSchema.parse(body);

    // Create a new desktop instance using the helper
    const newInstance = await addDbInstance(db, userId, params.timeoutMs);

    try {
      const provisioningUrl = `http://${GATEWAY_EXTERNAL_IP}/cyberdesk/${newInstance.id}`;
      const response = await axios.post(provisioningUrl, {
        timeoutMs: params.timeoutMs
      });
      console.log('Provisioning request successful:', response.data);

      return c.json(
        {
          id: newInstance.id,
          status: newInstance.status,
        },
        200
      );
    } catch (provisioningError) {
      console.error('Error calling provisioning service:', provisioningError);
      await updateDbInstanceStatus(db, newInstance.id, userId, InstanceStatus.Error);
      throw new Error('Failed to initiate provisioning of Cyberdesk resource via Gateway for instance ' + newInstance.id);
    }
  } catch (error) {
    return handleApiError(c, error, "Failed to create desktop instance");
  }
});

// Route for stopping a desktop instance
desktop.openapi(stopDesktop, async (c) => {
  const userId = c.get("userId");
  const id = c.req.param("id");
  const { GATEWAY_EXTERNAL_IP } = env<EnvVars>(c);
  try {
    // Stop the Cyberdesk instance (update status to terminated)
    const updatedInstance = await updateDbInstanceStatus(db, id, userId, InstanceStatus.Terminated);

    if (!updatedInstance) {
      return c.json(
        {
          message: "Failed to stop desktop instance. It might not exist, already be stopped/terminated, or you may not be authorized.",
          docs: "https://docs.cyberdesk.io/docs/api-reference/",
        },
        404
      );
    }

    try {
      const provisioningUrl = `http://${GATEWAY_EXTERNAL_IP}/cyberdesk/${id}/stop`;
      const response = await axios.post(provisioningUrl);
      console.log('Stopping request successful:', response.data);
    } catch (provisioningError) {
      console.error('Error calling provisioning service:', provisioningError);
      throw new Error('Failed to stop Cyberdesk resource via Gateway for instance ' + id);
    }

    return c.json(
      {
        status: updatedInstance.status,
      },
      200
    );
  } catch (error) {
    return handleApiError(c, error, "Failed to stop desktop instance");
  }
});

async function executeComputerAction(id: string, userId: string, action: ComputerAction) {
  // Get instance details (includes auth check)
  const instance = await getDbInstanceDetails(db, id, userId);
  if (!instance) {
    throw new Error("Instance not found or unauthorized");
  }
  if (instance.status !== 'running') {
    throw new Error(`Instance is not running (status: ${instance.status}). Cannot perform action.`);
  }

  // TODO: Implement actual action execution based on instance details (e.g., using streamUrl or remoteId if added)


  return { status: "success" };
}

// Route for performing a computer action on a desktop
desktop.openapi(computerAction, async (c) => {
  const userId = c.get("userId");
  const id = c.req.param("id");
  const action = await c.req.json() as ComputerAction;

  // Execute the appropriate action
  try {
    const result = await executeComputerAction(id, userId, action);

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
})


// Route for executing a bash command on a desktop
desktop.openapi(bashAction, async (c) => {
  const userId = c.get("userId");
  const id = c.req.param("id");
  const { command } = await c.req.json();

  try {
    // Get the DB instance of this id
    const dbInstance = await getDbInstanceDetails(db, id, userId);

    // TODO: Execute the bash command

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

export default desktop;
