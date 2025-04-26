/// <reference lib="dom" />

import { createClient, type Client, type Options as ClientOptions } from '@hey-api/client-fetch';
import * as apiMethods from './client/sdk.gen'; // Import the generated methods
// Re-export all types from types.gen for user convenience
export * from './client/types.gen';

// Define a type for the fetch function to avoid global dependency issues
type FetchFn = (input: RequestInfo | URL, init?: RequestInit) => Promise<Response>;

/**
 * Configuration options for the Cyberdesk SDK client.
 */
export interface CyberdeskClientOptions {
    /** Your Cyberdesk API Key */
    apiKey: string;
    /** Optional: Override the base URL for the API. Defaults to Cyberdesk production API. */
    baseUrl?: string;
    /** Optional: Provide a custom fetch implementation. */
    fetch?: FetchFn;
    /** Optional: Provide additional default options for the underlying client (e.g., timeout, keepalive). */
    // Using Partial<ClientOptions> allows any subset of options but is less strict than Omit.
    clientOptions?: Partial<ClientOptions>;
}

// Define the type for the SDK object returned by the factory function.
// This maps the original method names to their corresponding function types
// from the generated sdk.gen module.
export type CyberdeskSdk = {
    getV1DesktopId: typeof apiMethods.getV1DesktopId;
    postV1Desktop: typeof apiMethods.postV1Desktop;
    postV1DesktopIdStop: typeof apiMethods.postV1DesktopIdStop;
    postV1DesktopIdComputerAction: typeof apiMethods.postV1DesktopIdComputerAction;
    postV1DesktopIdBashAction: typeof apiMethods.postV1DesktopIdBashAction;
    // Add other methods exported from sdk.gen.ts here if they exist
};

const DEFAULT_BASE_URL = 'https://api.cyberdesk.io'; // Replace if needed

/**
 * Creates a Cyberdesk SDK instance configured with your API key.
 *
 * @param options - Configuration options including the API key.
 * @returns An SDK instance with methods ready to be called.
 */
export function createCyberdeskSdk(options: CyberdeskClientOptions): CyberdeskSdk {
    const { apiKey, baseUrl = DEFAULT_BASE_URL, fetch: customFetch, clientOptions = {} } = options;

    if (!apiKey) {
        throw new Error('Cyberdesk SDK requires an `apiKey` to be provided.');
    }

    // Ensure baseUrl is string | undefined before use
    const finalBaseUrl: string | undefined = baseUrl;

    // Prepare headers, merging defaults with any provided in clientOptions
    const mergedHeaders = {
        'x-api-key': apiKey,
        ...(clientOptions.headers || {}),
    };

    // Construct the final options for createClient explicitly
    const finalClientOptions = {
        // Set base URL
        baseUrl: finalBaseUrl,
        // Set merged headers
        headers: mergedHeaders,
        // Conditionally add fetch
        ...(customFetch && { fetch: customFetch }),
        // TODO: Manually add other relevant clientOptions properties here if needed
        // Example: ...(clientOptions.timeout && { timeout: clientOptions.timeout })
    };

    // Pass the inferred options object directly
    const configuredClient: Client = createClient(finalClientOptions);

    // Return an object where each method is pre-configured with the client instance
    return {
        getV1DesktopId: (opts) => apiMethods.getV1DesktopId({ ...opts, client: configuredClient }),
        postV1Desktop: (opts) => apiMethods.postV1Desktop({ ...opts, client: configuredClient }),
        postV1DesktopIdStop: (opts) => apiMethods.postV1DesktopIdStop({ ...opts, client: configuredClient }),
        postV1DesktopIdComputerAction: (opts) => apiMethods.postV1DesktopIdComputerAction({ ...opts, client: configuredClient }),
        postV1DesktopIdBashAction: (opts) => apiMethods.postV1DesktopIdBashAction({ ...opts, client: configuredClient }),
        // Add bindings for other generated methods here following the same pattern
    };
}

// Optional: Export the raw client creation function if users need advanced customization
export { createClient };
// Optional: Export the underlying api methods if needed, though usually accessed via the sdk instance
export * as rawApiMethods from './client/sdk.gen'; 