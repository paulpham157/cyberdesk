import { type Context, type Next } from 'hono';
import { HTTPException } from 'hono/http-exception';
import { ZodError } from 'zod';
import type { ContentfulStatusCode } from 'hono/utils/http-status';

// Base API Error class
export class ApiError extends Error {
  public readonly statusCode: number;

  constructor(message: string, statusCode: number) {
    super(message);
    this.statusCode = statusCode;
    this.name = this.constructor.name; // Set the error name to the class name
    Error.captureStackTrace(this, this.constructor); // Capture stack trace
  }
}

// Specific Error Types
export class BadRequestError extends ApiError {
  constructor(message = 'Bad Request') {
    super(message, 400);
  }
}

export class UnauthorizedError extends ApiError {
  constructor(message = 'Unauthorized') {
    super(message, 401);
  }
}

export class NotFoundError extends ApiError {
  constructor(message = 'Not Found') {
    super(message, 404);
  }
}

export class ConflictError extends ApiError {
  constructor(message = 'Conflict') {
    super(message, 409);
  }
}

export class GatewayError extends ApiError {
  constructor(message = 'Bad Gateway') {
    super(message, 502);
  }
}

export class InternalServerError extends ApiError {
    constructor(message = 'Internal Server Error') {
      super(message, 500);
    }
}

// Specific error for when a command fails *inside* the CyberDesk instance
// We might still want to return a 200 OK with an error status for this scenario.
export class ActionExecutionError extends Error {
    public readonly details?: string; // e.g., stderr output

    constructor(message: string, details?: string) {
        super(message);
        this.details = details;
        this.name = this.constructor.name;
        Error.captureStackTrace(this, this.constructor);
    }
}


// Hono Error Handler Middleware
export const honoErrorHandler = (err: Error, c: Context) => {
  console.error("Error caught by middleware:", err); // Log the full error

  // Handle Zod validation errors specifically
  if (err instanceof ZodError) {
    const validationErrors = err.errors.map(e => `${e.path.join('.')}: ${e.message}`).join(', ');
    return c.json(
      {
        status: "error",
        error: `Validation failed: ${validationErrors}`,
        docs: "https://docs.cyberdesk.io/docs/api-reference/",
      },
      400 // Bad Request for validation errors
    );
  }

  // Handle our custom ApiError instances
  if (err instanceof ApiError) {
    return c.json(
      {
        status: "error",
        error: err.message,
        docs: "https://docs.cyberdesk.io/docs/api-reference/",
      },
      err.statusCode as ContentfulStatusCode
    );
  }

   // Handle Hono's built-in HTTPException
   if (err instanceof HTTPException) {
    return c.json(
        {
          status: "error",
          error: err.message,
          docs: "https://docs.cyberdesk.io/docs/api-reference/",
        },
        err.status as ContentfulStatusCode
      );
  }

  // Handle ActionExecutionError specifically (return 200 OK with error status)
  if (err instanceof ActionExecutionError) {
      return c.json(
          {
              status: "error",
              error: err.message,
              details: err.details, // Optionally include details like stderr
          },
          200 // Special case: Action failed but API communication was successful
      );
  }


  // Fallback for unexpected errors
  return c.json(
    {
      status: "error",
      error: "An unexpected internal server error occurred.",
      docs: "https://docs.cyberdesk.io/docs/api-reference/",
    },
    500 as const
  );
}; 