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
  BashActionSchema,
} from "../schema/desktop.js";
import { GatewayExecuteCommandRequestSchema, GatewayExecuteCommandResponseSchema } from "../schema/gateway.js";
import { db } from "../db/index.js";
import {
  addDbInstance,
  getDbInstanceDetails,
  updateDbInstanceStatus,
} from "../db/dbActions.js";
import {
  ApiError,
  NotFoundError,
  ConflictError,
  BadRequestError,
  GatewayError,
  ActionExecutionError,
  honoErrorHandler,
  UnauthorizedError,
  InternalServerError,
} from "../lib/errors.js";

// Type definitions
type EnvVars = {
  UNKEY_API_ID: string;
  SUPABASE_URL: string;
  SUPABASE_ANON_KEY: string;
  SUPABASE_CONNECTION_STRING?: string;
  WEB_URL: string;
  GATEWAY_URL: string;
};

// Use the schema type for computer actions
type ComputerAction = z.infer<typeof ComputerActionSchema>;
// Use the schema type for desktop creation parameters
type CreateDesktopParams = z.infer<typeof CreateDesktopParamsSchema>;
type BashAction = z.infer<typeof BashActionSchema>;

// Create Hono instance
const desktop = new OpenAPIHono<{
  Variables: {
    unkey: UnkeyContext;
    userId: string;
  };
}>();

// Register the global error handler
desktop.onError(honoErrorHandler);

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
    throw new UnauthorizedError("Invalid API key");
  }

  const userId = result.ownerId;
  if (!userId) {
    throw new UnauthorizedError("No user associated with this key");
  }

  c.set("userId", userId);

  await next();
});

// Route for getting a desktop instance's details
desktop.openapi(getDesktop, async (c) => {
  const userId = c.get("userId");
  const id = c.req.param("id");

  const instanceDetails = await getDbInstanceDetails(db, id, userId);
  
  return c.json({
      id: instanceDetails.id,
      status: instanceDetails.status,
      created_at: (instanceDetails.createdAt || new Date(0)).toISOString(),
      timeout_at: instanceDetails.timeoutAt.toISOString(),
      stream_url: instanceDetails.streamUrl
  }, 200);
});

// Route for creating a new desktop instance
desktop.openapi(createDesktop, async (c) => {
  const { GATEWAY_URL } = env<EnvVars>(c);
  const userId = c.get("userId");
  let createDesktopParams: CreateDesktopParams;

  try {
    const body = await c.req.json().catch(() => ({}));
    createDesktopParams = CreateDesktopParamsSchema.parse(body);

    const newInstance = await addDbInstance(db, userId, createDesktopParams.timeout_ms);

    try {
      const provisioningUrl = `${GATEWAY_URL}/cyberdesk/${newInstance.id}`;
      const response = await axios.post(provisioningUrl, {
        timeoutMs: createDesktopParams.timeout_ms
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
      console.error('Error calling provisioning service during creation:', provisioningError);
      await updateDbInstanceStatus(db, newInstance.id, userId, InstanceStatus.Error).catch(console.error);
      if (axios.isAxiosError(provisioningError)) {
         throw new GatewayError(`Failed to provision via Gateway: ${provisioningError.response?.statusText || provisioningError.message}`);
      } else {
         throw new GatewayError('Failed to initiate provisioning of Cyberdesk resource via Gateway for instance ' + newInstance.id);
      }
    }
  } catch (error) {
    if (error instanceof z.ZodError) {
      throw error;
    } else if (error instanceof ApiError) {
        throw error;
    } else {
        console.error('Unexpected error during desktop creation:', error);
        throw new InternalServerError("Failed to create desktop instance due to an unexpected error.");
    }
  }
});

// Route for stopping a desktop instance
desktop.openapi(stopDesktop, async (c) => {
  const userId = c.get("userId");
  const id = c.req.param("id");
  const { GATEWAY_URL } = env<EnvVars>(c);

  const updatedInstance = await updateDbInstanceStatus(db, id, userId, InstanceStatus.Terminated);

  try {
    const provisioningUrl = `${GATEWAY_URL}/cyberdesk/${id}/stop`;
    await axios.post(provisioningUrl);
    console.log('Stopping request successful via Gateway for instance:', id);
  } catch (provisioningError) {
    console.error('Error calling provisioning service during stop:', provisioningError);
  }

  return c.json(
    {
      status: updatedInstance.status,
    },
    200
  );
});

async function executeComputerAction(
  id: string,
  userId: string,
  action: ComputerAction,
  GATEWAY_URL: string
): Promise<string> {
  const instance = await getDbInstanceDetails(db, id, userId);
  if (!instance) {
    throw new NotFoundError("Instance not found or unauthorized");
  }
  if (instance.status !== 'running') {
    throw new ConflictError(`Instance is not running (status: ${instance.status}). Cannot perform action.`);
  }

  let command: string;
  const displayPrefix = "export DISPLAY=:99;";

  switch (action.type) {
    case "click_mouse": {
      const { x, y, button = "left", num_of_clicks = 1, click_type = "click" } = action;
      const buttonMap: { [key: string]: number } = { left: 1, middle: 2, right: 3 };
      const btn = buttonMap[button] || 1;
      let moveCmd = "";
      if (x !== undefined && y !== undefined) {
        moveCmd = `xdotool mousemove ${x} ${y} && `;
      }
      let clickCmd: string;
      if (click_type === "click") {
        clickCmd = `xdotool click --repeat ${num_of_clicks} ${btn}`;
      } else if (click_type === "down") {
        clickCmd = `xdotool mousedown ${btn}`;
      } else { // up
        clickCmd = `xdotool mouseup ${btn}`;
      }
      command = `${displayPrefix} ${moveCmd}${clickCmd}`;
      break;
    }
    case "scroll": {
      const { direction, amount } = action;
      const directionMap: { [key: string]: number } = { up: 4, down: 5, left: 6, right: 7 };
      const btn = directionMap[direction];
      // Ensure amount is a reasonable positive integer
      const repeatCount = Math.max(1, Math.min(Math.floor(amount), 500)); // Cap repeat at 500 for sanity
      const delayMs = 25; // Reduce delay for faster scrolling
      command = `${displayPrefix} xdotool click --repeat ${repeatCount} --delay ${delayMs} ${btn}`;
      break;
    }
    case "move_mouse": {
      command = `${displayPrefix} xdotool mousemove ${action.x} ${action.y}`;
      break;
    }
    case "drag_mouse": {
      const { start, end } = action;
      command = `${displayPrefix} xdotool mousemove ${start.x} ${start.y} mousedown 1 mousemove ${end.x} ${end.y} mouseup 1`;
      break;
    }
    case "type": {
      const escapedText = action.text.replace(/'/g, "'\''");
      command = `${displayPrefix} xdotool type --clearmodifiers --delay 50 '${escapedText}'`;
      break;
    }
    case "press_keys": {
      const { keys, key_action_type = "press" } = action;
      const keyString = Array.isArray(keys) ? keys.join('+') : keys;
      let keyCmd: string;
      if (key_action_type === "down") {
        keyCmd = `keydown`;
      } else if (key_action_type === "up") {
        keyCmd = `keyup`;
      } else { // press
        keyCmd = `key`;
      }
      command = `${displayPrefix} xdotool ${keyCmd} --clearmodifiers ${keyString}`;
      break;
    }
    case "wait": {
      const seconds = Math.max(0, action.ms / 1000);
      command = `sleep ${seconds}`;
      break;
    }
    case "screenshot": {
      command = `${displayPrefix} scrot -q 100 /tmp/screen.jpg && base64 /tmp/screen.jpg && rm /tmp/screen.jpg`;
      break;
    }
    case "get_cursor_position": {
      command = `${displayPrefix} xdotool getmouselocation --shell`;
      break;
    }
    default:
      throw new BadRequestError(`Unsupported action type: ${(action as any).type}`);
  }

  console.log(`Executing command for instance ${id}: ${command}`);

  const provisioningUrl = `${GATEWAY_URL}/cyberdesk/${id}/execute-command`;
  const requestBody = GatewayExecuteCommandRequestSchema.parse({ command });
  try {
    const response = await axios.post<z.infer<typeof GatewayExecuteCommandResponseSchema>>(
        provisioningUrl,
        requestBody
    );

    const parsedResponse = GatewayExecuteCommandResponseSchema.parse(response.data);

    console.log(`Command execution response for instance ${id}:`, parsedResponse);

    if (parsedResponse.vm_response.return_code !== 0) {
      throw new ActionExecutionError(
          `Command failed with code ${parsedResponse.vm_response.return_code}`,
          parsedResponse.vm_response.stderr || 'No stderr output'
      );
    }

    return parsedResponse.vm_response.stdout.trim();

  } catch (error: any) {
    console.error(`Error executing command for instance ${id}:`, error);
    if (error instanceof z.ZodError) {
        throw new GatewayError(`Invalid response structure from gateway: ${error.errors.map(e => e.message).join(', ')}`);
    } else if (axios.isAxiosError(error)) {
        const gatewayMessage = error.response?.data?.message || error.message || "Failed to execute command via gateway";
        throw new GatewayError(`Action execution failed via gateway: ${gatewayMessage}`);
    } else if (error instanceof ApiError) {
        throw error;
    } else {
        throw new InternalServerError(`Unexpected error during action execution: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }
}

/**
 * Executes a raw bash command on the target instance via the gateway.
 * @param id Instance ID
 * @param userId User ID for authorization
 * @param command The bash command string to execute
 * @param GATEWAY_URL Gateway URL
 * @returns Promise<string> Resolves with stdout on success
 * @throws Error on command failure or communication issues
 */
async function executeBashCommand(
    id: string,
    userId: string,
    command: string,
    GATEWAY_URL: string
  ): Promise<string> {
    const instance = await getDbInstanceDetails(db, id, userId);
    if (!instance) {
      throw new NotFoundError("Instance not found or unauthorized");
    }
    if (instance.status !== 'running') {
      throw new ConflictError(`Instance is not running (status: ${instance.status}). Cannot execute command.`);
    }
  
    console.log(`Executing bash command for instance ${id}: ${command}`);
  
    const provisioningUrl = `${GATEWAY_URL}/cyberdesk/${id}/execute-command`;
    const requestBody = GatewayExecuteCommandRequestSchema.parse({ command });
    try {
      const response = await axios.post<z.infer<typeof GatewayExecuteCommandResponseSchema>>(
        provisioningUrl,
        requestBody
      );
  
      const parsedResponse = GatewayExecuteCommandResponseSchema.parse(response.data);
  
      console.log(`Bash command execution response for instance ${id}:`, parsedResponse);
  
      return parsedResponse.vm_response.stdout.trim() || parsedResponse.vm_response.stderr.trim();
  
    } catch (error: any) {
      console.error(`Error executing bash command for instance ${id}:`, error);
       if (error instanceof z.ZodError) {
            throw new GatewayError(`Invalid response structure from gateway: ${error.errors.map(e => e.message).join(', ')}`);
        } else if (axios.isAxiosError(error)) {
          const gatewayMessage = error.response?.data?.message || error.message || "Failed to execute command via gateway";
          throw new GatewayError(`Bash command execution failed via gateway: ${gatewayMessage}`);
      } else if (error instanceof ApiError) {
        throw error;
    } else {
          throw new InternalServerError(`Unexpected error during bash command execution: ${error instanceof Error ? error.message : 'Unknown error'}`);
      }
    }
  }

// Route for performing a computer action on a desktop
desktop.openapi(computerAction, async (c) => {
  const userId = c.get("userId");
  const id = c.req.param("id");
  const { GATEWAY_URL } = env<EnvVars>(c);
  let action: ComputerAction;

  try {
      const body = await c.req.json().catch(() => ({}));
      action = ComputerActionSchema.parse(body);
  } catch (parseError: any) {
      if (parseError instanceof z.ZodError) {
          throw parseError;
      }
      throw new BadRequestError(`Invalid request body: ${parseError?.message || 'Unknown parsing error'}`);
  }

  const resultString = await executeComputerAction(id, userId, action, GATEWAY_URL);

  if (action.type === "screenshot") {
    return c.json({ base64_image: resultString, }, 200);
  } else if (action.type === "get_cursor_position") {
      return c.json({ output: resultString, }, 200);
  } else {
    return c.json({ output: resultString, }, 200);
  }
});


// Route for executing a bash command on a desktop
desktop.openapi(bashAction, async (c) => {
  const userId = c.get("userId");
  const id = c.req.param("id");
  const { GATEWAY_URL } = env<EnvVars>(c);
  let bashAction: BashAction;

  try {
      const body = await c.req.json().catch(() => ({}));
      bashAction = BashActionSchema.parse(body);
  } catch (parseError: any) {
       if (parseError instanceof z.ZodError) {
           throw parseError;
       }
       throw new BadRequestError(`Invalid request body: ${parseError?.message || 'Unknown parsing error'}`);
  }

  const resultString = await executeBashCommand(id, userId, bashAction.command, GATEWAY_URL);

  return c.json({ status: "success", output: resultString, }, 200);
});

export default desktop;
