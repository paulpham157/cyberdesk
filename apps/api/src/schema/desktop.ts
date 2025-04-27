import { createRoute, z } from "@hono/zod-openapi";

import { openApiErrorResponses } from "./errors.js";
import { InstanceStatus, instanceStatusEnum } from "../db/schema.js";

// Header schema for API key authentication
const HeadersSchema = z.object({
  "x-api-key": z.string().openapi({
    description: "API key for authentication",
    example: "api_12345",
  }),
});

// Common schema for action oriented API responses
const ActionResponseSchema = z.object({
  output: z.string().optional().openapi({
      description: "Raw string output from the executed command (if any)",
      example: "X=500 Y=300",
  }),
  error: z.string().optional().openapi({
    description: "Error message if the operation failed (also indicated by non-2xx HTTP status)",
    example: "Command failed with code 1: xdotool: command not found",
  }),
  base64_image: z.string().optional().openapi({
    description: "Base64 encoded image data (only returned for screenshot actions)",
    example: "iVBORw0KGgoAAAANSUhEUgAA...",
  })
});

// Point schema for coordinates
const PointSchema = z.object({
  x: z.number().int().openapi({
    description: "X coordinate on the screen",
    example: 500,
  }),
  y: z.number().int().openapi({
    description: "Y coordinate on the screen",
    example: 300,
  }),
});

// Schema for desktop creation parameters
export const CreateDesktopParamsSchema = z.object({
  timeoutMs: z.number().int().optional().openapi({
    description: "Timeout in milliseconds for the desktop session",
    example: 3600000,
  }),
});

// Schema for the response of the create desktop endpoint
export const CreateDesktopResponseSchema = z.object({
    id: z.string().openapi({
      description: "Unique identifier for the desktop instance",
      example: "desktop_12345",
    }),
    status: z.enum(instanceStatusEnum.enumValues).openapi({
        description: "Initial status of the desktop instance after creation request",
        example: InstanceStatus.Pending,
      }),
  });

// Schema for the response of the stop desktop endpoint
export const StopDesktopResponseSchema = z.object({
  status: z.enum(instanceStatusEnum.enumValues).openapi({
    description: "Status of the desktop instance after stopping",
    example: InstanceStatus.Terminated,
  }),
});

// Computer action schema with discriminated union
export const ComputerActionSchema = z.discriminatedUnion("type", [
  z.object({
    type: z.literal("click_mouse").openapi({
      description: "Perform a mouse action: click, press (down), or release (up). Defaults to a single left click at the current position.",
      example: "click_mouse",
    }),
    x: z.number().int().optional().openapi({
      description: "X coordinate for the action (optional, uses current position if omitted)",
      example: 500,
    }),
    y: z.number().int().optional().openapi({
      description: "Y coordinate for the action (optional, uses current position if omitted)",
      example: 300,
    }),
    button: z.enum(["left", "right", "middle"]).optional().openapi({
      description: "Mouse button to use (optional, defaults to 'left')",
      example: "left",
    }),
    num_of_clicks: z.number().int().min(0).optional().openapi({
      description: "Number of clicks to perform (optional, defaults to 1, only applicable for 'click' type)",
      example: 1,
    }),
    click_type: z.enum(["click", "down", "up"]).optional().openapi({
      description: "Type of mouse action (optional, defaults to 'click')",
      example: "click",
    }),
  }).openapi({ title: "Click Mouse Action" }),
  z.object({
    type: z.literal("scroll").openapi({
      description: "Scroll the mouse wheel in the specified direction",
      example: "scroll",
    }),
    direction: z.enum(["up", "down", "left", "right"]).openapi({
      description: "Direction to scroll",
      example: "down",
    }),
    amount: z.number().int().openapi({
      description: "Amount to scroll in pixels",
      example: 100,
    }),
  }).openapi({ title: "Scroll Action" }),
  z.object({
    type: z.literal("move_mouse").openapi({
      description: "Move the mouse cursor to the specified coordinates",
      example: "move_mouse",
    }),
    x: z.number().int().openapi({
      description: "X coordinate to move to",
      example: 500,
    }),
    y: z.number().int().openapi({
      description: "Y coordinate to move to",
      example: 300,
    }),
  }).openapi({ title: "Move Mouse Action" }),
  z.object({
    type: z.literal("drag_mouse").openapi({
      description: "Drag the mouse from start to end coordinates",
      example: "drag_mouse",
    }),
    start: PointSchema.openapi({
      description: "Starting coordinates for the drag operation",
      example: { x: 100, y: 100 },
    }),
    end: PointSchema.openapi({
      description: "Ending coordinates for the drag operation",
      example: { x: 300, y: 300 },
    }),
  }).openapi({ title: "Drag Mouse Action" }),
  z.object({
    type: z.literal("type").openapi({
      description: "Type text at the current cursor position",
      example: "type",
    }),
    text: z.string().openapi({
      description: "Text to type",
      example: "Hello, World!",
    }),
  }).openapi({ title: "Type Text Action" }),
  z.object({
    type: z.literal("press_keys").openapi({
      description: "Press, hold down, or release one or more keyboard keys. Defaults to a single press and release.",
      example: "press_keys",
    }),
    keys: z.union([
      z.string().openapi({
        description: "Single key to press",
        example: "Enter",
      }),
      z.array(z.string()).openapi({
        description: "Multiple keys to press simultaneously",
        example: ["Control", "c"],
      })
    ]),
    key_action_type: z.enum(["press", "down", "up"]).optional().openapi({
        description: "Type of key action (optional, defaults to 'press' which is a down and up action)",
        example: "press",
      }),
  }).openapi({ title: "Press Keys Action" }),
  z.object({
    type: z.literal("wait").openapi({
      description: "Wait for the specified number of milliseconds",
      example: "wait",
    }),
    ms: z.number().int().openapi({
      description: "Time to wait in milliseconds",
      example: 1000,
    }),
  }).openapi({ title: "Wait Action" }),
  z.object({
    type: z.literal("screenshot").openapi({
      description: "Take a screenshot of the desktop",
      example: "screenshot",
    }),
  }).openapi({ title: "Screenshot Action" }),
  z.object({
    type: z.literal("get_cursor_position").openapi({
      description: "Get the current mouse cursor position",
      example: "get_cursor_position",
    }),
  }).openapi({ title: "Get Cursor Position Action" }),
]);

// Schema for Bash Action parameters
export const BashActionSchema = z.object({
  command: z.string().openapi({
    description: "Bash command to execute",
    example: "echo 'Hello, World!'",
  }),
});

// Create Desktop Route
export const createDesktop = createRoute({
  method: "post",
  path: "/desktop",
  tags: ["Desktop"],
  summary: "Create a new virtual desktop instance",
  description: "Creates a new virtual desktop instance and returns its ID and stream URL",
  request: {
    headers: HeadersSchema,
    body: {
      content: {
        "application/json": {
          schema: CreateDesktopParamsSchema,
        },
      },
    },
  },
  responses: {
    200: {
      content: {
        "application/json": {
          schema: CreateDesktopResponseSchema,
        },
      },
      description: "Desktop creation initiated successfully",
    },
    ...openApiErrorResponses,
  },
});

// Stop Desktop Route
export const stopDesktop = createRoute({
  method: "post",
  path: "/desktop/:id/stop",
  tags: ["Desktop"],
  summary: "Stop a running desktop instance",
  description: "Stops a running desktop instance and cleans up resources",
  request: {
    headers: HeadersSchema,
    params: z.object({
      id: z.string().openapi({
        description: "Desktop instance ID to stop",
        example: "desktop_12345",
      }),
    }),
  },
  responses: {
    200: {
      content: {
        "application/json": {
          schema: StopDesktopResponseSchema,
        },
      },
      description: "Desktop stopped successfully",
    },
    ...openApiErrorResponses,
  }, 
});

// Get Desktop Route Response Schema
const GetDesktopResponseSchema = z.object({
  id: z.string().uuid().openapi({
    description: "Unique identifier for the desktop instance",
    example: "a1b2c3d4-e5f6-7890-1234-567890abcdef",
  }),
  status: z.enum(instanceStatusEnum.enumValues).openapi({
    description: "Current status of the desktop instance",
    example: "running",
  }),
  createdAt: z.string().datetime().openapi({
    description: "Timestamp when the instance was created",
    example: "2023-10-27T10:00:00Z",
  }),
  timeoutAt: z.string().datetime().openapi({
    description: "Timestamp when the instance will automatically time out",
    example: "2023-10-28T10:00:00Z",
  }),
});

// Get Desktop Route
export const getDesktop = createRoute({
  method: "get",
  path: "/desktop/:id",
  tags: ["Desktop"],
  summary: "Get details of a specific desktop instance",
  description: "Returns the ID, status, creation timestamp, and timeout timestamp for a given desktop instance.",
  request: {
    headers: HeadersSchema,
    params: z.object({
      id: z.string().uuid().openapi({
        description: "The UUID of the desktop instance to retrieve",
        example: "a1b2c3d4-e5f6-7890-1234-567890abcdef",
      }),
    }),
  },
  responses: {
    200: {
      content: {
        "application/json": {
          schema: GetDesktopResponseSchema,
        },
      },
      description: "Desktop instance details retrieved successfully",
    },
    ...openApiErrorResponses,
  },
});

// Computer Action Route
export const computerAction = createRoute({
  method: "post",
  path: "/desktop/:id/computer-action",
  tags: ["Desktop"],
  summary: "Perform an action on the desktop",
  description: "Executes a computer action such as mouse clicks, keyboard input, or screenshots on the desktop",
  request: {
    headers: HeadersSchema,
    params: z.object({
      id: z.string().openapi({
        description: "Desktop instance ID to perform the action on",
        example: "desktop_12345",
      }),
    }),
    body: {
      content: {
        "application/json": {
          schema: ComputerActionSchema,
        },
      },
    },
  },
  responses: {
    200: {
      content: {
        "application/json": {
          schema: ActionResponseSchema,
        },
      },
      description: "Action executed successfully. Response may contain output or image data depending on the action.",
    },
    ...openApiErrorResponses,
  },
});

// Bash Action Route
export const bashAction = createRoute({
  method: "post",
  path: "/desktop/:id/bash-action",
  tags: ["Desktop"],
  summary: "Execute a bash command on the desktop",
  description: "Runs a bash command on the desktop and returns the command output",
  request: {
    headers: HeadersSchema,
    params: z.object({
      id: z.string().openapi({
        description: "Desktop instance ID to run the command on",
        example: "desktop_12345",
      }),
    }),
    body: {
      content: {
        "application/json": {
          schema: BashActionSchema,
        },
      },
    },
  },
  responses: {
    200: {
      content: {
        "application/json": {
          schema: ActionResponseSchema,
        },
      },
      description: "Command executed successfully. Response contains command output.",
    },
    ...openApiErrorResponses,
  },
});
