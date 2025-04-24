import { createCache, type Cache as C} from "@unkey/cache";
import { MemoryStore } from "@unkey/cache/stores";

import type { Context, Middleware } from "./hono.js";
import type { Next } from "hono";

export type CacheNamespaces = {
  // Define new namespaces here as needed
}

export type Cache = C<CacheNamespaces>

const persistentMap = new Map();

export function initCache(): Middleware {
  return async (c: Context, next: Next) => {
    const memory = new MemoryStore({ persistentMap: new Map() });

    const cache = createCache<CacheNamespaces>({
      // Add new namespaces as needed
    });
    c.set("cache", cache);
    return next();
  };
}
