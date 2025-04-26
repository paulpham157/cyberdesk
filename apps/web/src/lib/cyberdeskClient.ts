import {createCyberdeskClient} from "../../../../sdks/ts-sdk/src/index";

const client = createCyberdeskClient({
    apiKey: process.env.CYBERDESK_API_KEY || '',
});

client.getV1DesktopId({
    path: {
        id: '123'
    }
});

export default client;