"use server";

import client from "@/utils/playground/cyberdesk-client";

export const getDesktopURL = async (id?: string) => {
  if (!id) throw new Error("Sandbox ID required for getDesktopURL");
  try {
    const response = await client.getDesktop({
      path: {
        id,
      },
    });
    
    const streamUrl = response.data?.stream_url;

    return { streamUrl, id };
  } catch (error) {
    console.error("Error in getDesktopURL:", error);
    throw error;
  }
};

export const startDesktop = async () => {
  try {
    const response = await client.launchDesktop({
      body: {
        timeout_ms: 86400000,
      }
    });
    if (!response.data || !response.data.id) {
      throw new Error("Failed to start desktop: No ID returned from API");
    }
    return response.data;
  } catch (error) {
    console.error("Error in startDesktop:", error);
    throw error;
  }
};

export const killDesktop = async (id?: string) => {
  if (!id) throw new Error("Sandbox ID required for killDesktop");
  try {
    const response = await client.terminateDesktop({
      path: {
        id,
      },
    });
    if (!response.data) {
      throw new Error("Failed to kill desktop: No data returned from API");
    }
    return response.data;
  } catch (error) {
    console.error("Error in killDesktop:", error);
    throw error;
  }
};
