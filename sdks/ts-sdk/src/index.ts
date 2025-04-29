/// <reference lib="dom" />

import { createClient, type Client, type Options as ClientOptions } from '@hey-api/client-fetch';
import * as apiMethods from './client/sdk.gen'; // Import the generated methods
// Re-export all types from types.gen for user convenience
export * from './client/types.gen';

// Import the specific data types used by the SDK methods
import { 
    type GetV1DesktopIdData, 
    type PostV1DesktopData,
    type PostV1DesktopIdStopData,
    type PostV1DesktopIdComputerActionData,
    type PostV1DesktopIdBashActionData
    // Add other necessary *Data types if more methods are added
} from './client/types.gen';

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

// Helper type: Defines the options expected from the SDK user for a given method.
// It omits properties that are handled internally by the createCyberdeskClient wrapper.
// It focuses on the known structure of the *Data types (body, path, query).
// We make headers optional here to allow overrides, even if the main type omits it.
type SdkMethodOptions<TData> = Omit<TData, 'headers' | 'url'> & { 
    headers?: Record<string, string>; // Make headers optional for potential overrides
    // We don't include 'client' here as it's purely internal
};

// Define the type for the SDK object returned by the factory function.
// Use Omit on the generated method's parameters directly, excluding headers/client/url.
// Use the specific *Data types for clarity.
// The input type for the user is essentially the *Data type minus headers/url
export type CyberdeskSdk = {
    getDesktopInfo: (opts: Omit<GetV1DesktopIdData, 'headers' | 'url'>) => ReturnType<typeof apiMethods.getV1DesktopId>;
    launchDesktop: (opts: Omit<PostV1DesktopData, 'headers' | 'url'>) => ReturnType<typeof apiMethods.postV1Desktop>;
    terminateDesktop: (opts: Omit<PostV1DesktopIdStopData, 'headers' | 'url'>) => ReturnType<typeof apiMethods.postV1DesktopIdStop>;
    executeActionOnDesktop: (opts: Omit<PostV1DesktopIdComputerActionData, 'headers' | 'url'>) => ReturnType<typeof apiMethods.postV1DesktopIdComputerAction>;
    bashCommandOnDesktop: (opts: Omit<PostV1DesktopIdBashActionData, 'headers' | 'url'>) => ReturnType<typeof apiMethods.postV1DesktopIdBashAction>;
    // Add other methods exported from sdk.gen.ts here following the same pattern
};

const DEFAULT_BASE_URL = 'https://api.cyberdesk.io'; // Replace if needed

/**
 * Creates a Cyberdesk SDK instance configured with your API key.
 *
 * @param options - Configuration options including the API key.
 * @returns An SDK instance with methods ready to be called.
 */

export function createCyberdeskClient(options: CyberdeskClientOptions): CyberdeskSdk {
    const { apiKey, baseUrl = DEFAULT_BASE_URL, fetch: customFetch, clientOptions = {} } = options;

    if (!apiKey) {
        throw new Error('Cyberdesk SDK requires an `apiKey` to be provided.');
    }

    // Ensure baseUrl is string | undefined before use
    const finalBaseUrl: string | undefined = baseUrl;

    // Prepare headers, merging defaults with any provided in clientOptions
    const mergedHeaders = {
        'x-api-key': apiKey,
        'Content-Type': 'application/json',
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
        getDesktopInfo: (opts) => apiMethods.getV1DesktopId({
            ...(opts as GetV1DesktopIdData), // Cast opts to allow potential headers
            client: configuredClient,
            // Merge client headers with potentially provided headers from opts
            headers: { ...mergedHeaders, ...(opts as GetV1DesktopIdData).headers }
        }),
        launchDesktop: (opts) => apiMethods.postV1Desktop({
            ...(opts as PostV1DesktopData),
            client: configuredClient,
            headers: { ...mergedHeaders, ...(opts as PostV1DesktopData).headers }
        }),
        terminateDesktop: (opts) => apiMethods.postV1DesktopIdStop({
            ...(opts as PostV1DesktopIdStopData),
            path: { ...(opts as PostV1DesktopIdStopData).path, id: (opts as PostV1DesktopIdStopData).path.id },
            client: configuredClient,
            headers: { ...mergedHeaders, ...(opts as PostV1DesktopIdStopData).headers }
        }),
        executeActionOnDesktop: (opts) => apiMethods.postV1DesktopIdComputerAction({
            ...(opts as PostV1DesktopIdComputerActionData),
            client: configuredClient,
            headers: { ...mergedHeaders, ...(opts as PostV1DesktopIdComputerActionData).headers }
        }),
        bashCommandOnDesktop: (opts) => apiMethods.postV1DesktopIdBashAction({
            ...(opts as PostV1DesktopIdBashActionData),
            client: configuredClient,
            headers: { ...mergedHeaders, ...(opts as PostV1DesktopIdBashActionData).headers }
        }),
        // Add bindings for other generated methods here following the same pattern
    };
}

// Optional: Export the raw client creation function if users need advanced customization
export { createClient };
// Optional: Export the underlying api methods if needed, though usually accessed via the sdk instance
export * as rawApiMethods from './client/sdk.gen'; 