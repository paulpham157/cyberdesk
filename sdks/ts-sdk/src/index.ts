/// <reference lib="dom" />

import { createClient, type Client, type Options as ClientOptions } from '@hey-api/client-fetch';
import * as apiMethods from './client/sdk.gen';
import { 
    GetV1DesktopByIdData,
    PostV1DesktopData,
    PostV1DesktopByIdStopData,
    PostV1DesktopByIdComputerActionData,
    PostV1DesktopByIdBashActionData
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
export type GetDesktopParams = Omit<GetV1DesktopByIdData, 'headers' | 'url'>;
export type LaunchDesktopParams = Omit<PostV1DesktopData, 'headers' | 'url'>;
export type TerminateDesktopParams = Omit<PostV1DesktopByIdStopData, 'headers' | 'url'>;
export type ExecuteComputerActionParams = Omit<PostV1DesktopByIdComputerActionData, 'headers' | 'url'>;
export type ExecuteBashActionParams = Omit<PostV1DesktopByIdBashActionData, 'headers' | 'url'>;

export type CyberdeskSDK = {
    getDesktop: (opts: GetDesktopParams) => ReturnType<typeof apiMethods.getV1DesktopById>;
    launchDesktop: (opts: LaunchDesktopParams) => ReturnType<typeof apiMethods.postV1Desktop>;
    terminateDesktop: (opts: TerminateDesktopParams) => ReturnType<typeof apiMethods.postV1DesktopByIdStop>;
    executeComputerAction: (opts: ExecuteComputerActionParams) => ReturnType<typeof apiMethods.postV1DesktopByIdComputerAction>;
    executeBashAction: (opts: ExecuteBashActionParams) => ReturnType<typeof apiMethods.postV1DesktopByIdBashAction>;
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
        getDesktop: (opts) => apiMethods.getV1DesktopById({
            ...(opts as GetV1DesktopByIdData), // Cast opts to allow potential headers
            client: configuredClient,
            headers: { ...mergedHeaders, ...(opts as GetV1DesktopByIdData).headers }
        }),
        launchDesktop: (opts) => apiMethods.postV1Desktop({
            ...(opts as PostV1DesktopData),
            client: configuredClient,
            headers: { ...mergedHeaders, ...(opts as PostV1DesktopData).headers }
        }),
        terminateDesktop: (opts) => apiMethods.postV1DesktopByIdStop({
            ...(opts as PostV1DesktopByIdStopData),
            path: { ...(opts as PostV1DesktopByIdStopData).path, id: (opts as PostV1DesktopByIdStopData).path.id },
            client: configuredClient,
            headers: { ...mergedHeaders, ...(opts as PostV1DesktopByIdStopData).headers }
        }),
        executeComputerAction: (opts) => apiMethods.postV1DesktopByIdComputerAction({
            ...(opts as PostV1DesktopByIdComputerActionData),
            client: configuredClient,
            headers: { ...mergedHeaders, ...(opts as PostV1DesktopByIdComputerActionData).headers }
        }),
        executeBashAction: (opts) => apiMethods.postV1DesktopByIdBashAction({
            ...(opts as PostV1DesktopByIdBashActionData),
            client: configuredClient,
            headers: { ...mergedHeaders, ...(opts as PostV1DesktopByIdBashActionData).headers }
        }),
    };
}