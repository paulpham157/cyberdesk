import { createCyberdeskClient } from "cyberdesk";

const client = createCyberdeskClient({
    apiKey: process.env.CYBERDESK_API_KEY || '',
    baseUrl: process.env.CYBERDESK_API_BASE_URL || 'https://api.cyberdesk.io'
});

export default client;