import { z } from "@hono/zod-openapi";

const errorSchema = z.object({
  status: z.literal("error").openapi({ example: "error" }),
  error: z.string().openapi({
     description: "Error message detailing what went wrong",
     example: "Instance not found or unauthorized"
  })
});

export const openApiErrorResponses = {
  400: {
    description:
      "The server cannot or will not process the request due to something that is perceived to be a client error (e.g., malformed request syntax, invalid request message framing, or deceptive request routing).",
    content: {
      "application/json": {
        schema: errorSchema,
      },
    },
  },
  401: {
    description: `Although the HTTP standard specifies "unauthorized", semantically this response means "unauthenticated". That is, the client must authenticate itself to get the requested response.`,
    content: {
      "application/json": {
        schema: errorSchema,
      },
    },
  },
  403: {
    description:
      "The client does not have access rights to the content; that is, it is unauthorized, so the server is refusing to give the requested resource. Unlike 401 Unauthorized, the client's identity is known to the server.",
    content: {
      "application/json": {
        schema: errorSchema,
      },
    },
  },
  404: {
    description:
      "The server cannot find the requested resource. In the browser, this means the URL is not recognized. In an API, this can also mean that the endpoint is valid but the resource itself does not exist. Servers may also send this response instead of 403 Forbidden to hide the existence of a resource from an unauthorized client. This response code is probably the most well known due to its frequent occurrence on the web.",
    content: {
      "application/json": {
        schema: errorSchema,
      },
    },
  },
  409: {
    description:
      "This response is sent when a request conflicts with the current state of the server.",
    content: {
      "application/json": {
        schema: errorSchema,
      },
    },
  },
  429: {
    description: `The user has sent too many requests in a given amount of time ("rate limiting")`,
    content: {
      "application/json": {
        schema: errorSchema,
      },
    },
  },
  500: {
    description:
      "The server has encountered a situation it does not know how to handle.",
    content: {
      "application/json": {
        schema: errorSchema,
      },
    },
  },
  502: {
    description:
      "The server, while acting as a gateway or proxy, received an invalid response from the upstream server.",
    content: {
      "application/json": {
        schema: errorSchema,
      },
    },
  },
};
