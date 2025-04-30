/// <reference lib="dom" />

import { createClient, type Client, type Options as ClientOptions } from '@hey-api/client-fetch';
import * as apiMethods from './client/sdk.gen';
import { 
    type GetV1DesktopIdData, 
    type PostV1DesktopData,
    type PostV1DesktopIdStopData,
    type PostV1DesktopIdComputerActionData,
    type PostV1DesktopIdBashActionData
} from './client/types.gen';

const DEFAULT_BASE_URL = 'https://api.cyberdesk.io';

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

// Named parameter types for SDK methods
export type GetDesktopParams = Omit<GetV1DesktopIdData, 'headers' | 'url'>;
export type LaunchDesktopParams = Omit<PostV1DesktopData, 'headers' | 'url'>;
export type TerminateDesktopParams = Omit<PostV1DesktopIdStopData, 'headers' | 'url'>;
export type ExecuteComputerActionParams = Omit<PostV1DesktopIdComputerActionData, 'headers' | 'url'>;
export type ExecuteBashActionParams = Omit<PostV1DesktopIdBashActionData, 'headers' | 'url'>;

export type CyberdeskSDK = {
    getDesktop: (opts: GetDesktopParams) => ReturnType<typeof apiMethods.getV1DesktopId>;
    launchDesktop: (opts: LaunchDesktopParams) => ReturnType<typeof apiMethods.postV1Desktop>;
    terminateDesktop: (opts: TerminateDesktopParams) => ReturnType<typeof apiMethods.postV1DesktopIdStop>;
    executeComputerAction: (opts: ExecuteComputerActionParams) => ReturnType<typeof apiMethods.postV1DesktopIdComputerAction>;
    executeBashAction: (opts: ExecuteBashActionParams) => ReturnType<typeof apiMethods.postV1DesktopIdBashAction>;
};

/**
 * Creates a Cyberdesk SDK instance configured with your API key.
 *
 * @param options - Configuration options including the API key.
 * @returns An SDK instance with methods ready to be called.
 */

export function createCyberdeskClient(options: CyberdeskClientOptions): CyberdeskSDK {
    const { apiKey, baseUrl = DEFAULT_BASE_URL, fetch: customFetch, clientOptions = {} } = options;

    if (!apiKey) {
        throw new Error('Cyberdesk SDK requires an `apiKey` to be provided.');
    }

    const finalBaseUrl: string | undefined = baseUrl;

    const mergedHeaders = {
        'x-api-key': apiKey,
        'Content-Type': 'application/json',
        ...(clientOptions.headers || {}),
    };

    const finalClientOptions = {
        baseUrl: finalBaseUrl,
        headers: mergedHeaders,
        ...(customFetch && { fetch: customFetch })
    };

    const configuredClient: Client = createClient(finalClientOptions);

    // Return an object where each method is pre-configured with the client instance
    return {
        getDesktop: (opts) => apiMethods.getV1DesktopId({
            ...(opts as GetV1DesktopIdData), // Cast opts to allow potential headers
            client: configuredClient,
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
        executeComputerAction: (opts) => apiMethods.postV1DesktopIdComputerAction({
            ...(opts as PostV1DesktopIdComputerActionData),
            client: configuredClient,
            headers: { ...mergedHeaders, ...(opts as PostV1DesktopIdComputerActionData).headers }
        }),
        executeBashAction: (opts) => apiMethods.postV1DesktopIdBashAction({
            ...(opts as PostV1DesktopIdBashActionData),
            client: configuredClient,
            headers: { ...mergedHeaders, ...(opts as PostV1DesktopIdBashActionData).headers }
        }),
    };
}