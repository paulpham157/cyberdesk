/**
 * Utility functions for bash command execution with Cyberdesk API
 */

import client from '@/lib/cyberdeskClient';

/**
 * Get the base API URL based on environment
 */
const getApiBaseUrl = () => {
  return process.env.NODE_ENV === 'production' 
    ? 'https://api.cyberdesk.io/v1' 
    : 'http://localhost:3001/v1';
};

/**
 * Execute a bash command
 * @param command The command to execute
 * @param desktopId The ID of the desktop instance
 * @returns The command output as a string
 */
export async function executeBashCommand(
  command: string, 
  desktopId: string
): Promise<string> {
  try {
    // Call the client method
    const result = await client.bashCommandOnDesktop({
        path: { id: desktopId },
        body: { command },
        // No headers needed here as per previous request
    } as any); // Use 'as any' if type definition still mandates headers

    // Check status code from the nested response object
    if (result.response.status !== 200) {
      let errorDetails = `Failed with status: ${result.response.status}`;
      try {
        const errorBody = await result.response.json(); 
        errorDetails = errorBody.message || errorBody.error || JSON.stringify(errorBody);
      } catch (e) { /* Failed to parse body */ }
      throw new Error(`Failed to execute bash command: ${errorDetails}`);
    }

    const data = result.data;
    // Assuming the client response data has an optional output property
    return data?.output || '';
  } catch (error) {
    console.error(`Error executing bash command "${command}":`, error);
    return 'Error executing bash command' + "\n" + (error as Error).message;
  }
}
