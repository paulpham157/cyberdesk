import { OpenAPIHono, z } from "@hono/zod-openapi";
import type { UnkeyContext } from "@unkey/hono";
import type { Ratelimit } from "@unkey/ratelimit";
import type { Context as GenericContext, MiddlewareHandler } from "hono";
import type { ZodError } from "zod";

import type { Cache } from "./cache.js";

export type HonoEnv = {
  Bindings: {
    SUPABASE_CONNECTION_STRING: string;

    // Unkey credentials
    UNKEY_ROOT_KEY: string;
    UNKEY_API_ID: string;

    GATEWAY_EXTERNAL_IP: string;
  };
  Variables: {
    cache: Cache
    unkey: UnkeyContext;
    ratelimit: Ratelimit;
  };
};

export function parseZodErrorMessage(err: z.ZodError): string {
  try {
    const arr = JSON.parse(err.message) as Array<{
      message: string;
      path: Array<string>;
    }>;
    const { path, message } = arr[0];
    return `${path.join(".")}: ${message}`;
  } catch {
    return err.message;
  }
}
export function handleZodError(
  result:
    | {
        success: true;
        data: any;
      }
    | {
        success: false;
        error: ZodError;
      },
  c: Context
) {
  if (!result.success) {
    return c.json(
      {
        error: parseZodErrorMessage(result.error),
      },
      { status: 400 }
    );
  }
}

export function newApp() {
  const app = new OpenAPIHono<HonoEnv>({
    defaultHook: handleZodError,
  });

  app.onError((err: Error, c: Context) => {
    console.error(err);
    return c.json(
      {
        error: err.message,
      },
      { status: 500 }
    );
  });

  app.doc("/openapi.json", {
    openapi: "3.1.0",
    info: {
      title: "API Reference",
      version: "1.1.0",
      description: "API for Cyberdesk, to create, control, and manage virtual desktop instances.",
    },
    servers: [
      {
        url: "https://api.cyberdesk.io",
        description: "Production server"
      }
    ],
  });

  app.openAPIRegistry.registerComponent("securitySchemes", "apiKeyAuth", {
    type: "apiKey",
    in: "header",
    name: "x-api-key"
  });

  return app;
}

export type App = ReturnType<typeof newApp>;
export type Context = GenericContext<HonoEnv>;
export type Middleware = MiddlewareHandler<HonoEnv>;
