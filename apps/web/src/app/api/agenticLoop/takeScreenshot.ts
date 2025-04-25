export default async function takeScreenshot(instanceId: string) {
  // Check if we're in production mode first
  const isProd = process.env.NODE_ENV === 'production';
  const CYBERDESK_API_KEY = process.env.CYBERDESK_API_KEY;

  if (!CYBERDESK_API_KEY) {
    throw new Error("Missing CYBERDESK_API_KEY environment variable");
  }

  // Use production URL in prod mode, localhost:3001 otherwise
  const baseUrl = isProd ? 'https://api.cyberdesk.io' : 'http://localhost:3001';

  try {
    // Start the conversation with the user's prompt
    const response = await fetch(`${baseUrl}/v1/desktop/${instanceId}/computer-action`, {
      method: "POST",
      headers: {
        "x-api-key": CYBERDESK_API_KEY
      },
      body: JSON.stringify({
        type: "screenshot"
      })
    });

    const data = await response.json();

    return data.image;
  } catch (error) {
    console.error(error);
    return error;
  }
}