# cyberdesk

[![npm version](https://badge.fury.io/js/cyberdesk.svg)](https://badge.fury.io/js/cyberdesk)

The official TypeScript SDK for Cyberdesk.

## Installation

```bash
npm install cyberdesk
# or
yarn add cyberdesk
# or
pnpm add cyberdesk
```

## Usage

First, configure the client, for example, by setting default headers for authentication. You only need to do this once.

```typescript
import { client, setConfig } from 'cyberdesk/client'; // Import client and setConfig

// Configure the client (e.g., with an API Key)
// Adjust based on your actual authentication method
setConfig({
  headers: {
    'Authorization': `Bearer YOUR_API_KEY`
  }
});
```

Then, import and call the specific API functions you need:

```typescript
import {
  postV1Desktop,
  postV1DesktopIdComputerAction,
  type PostV1DesktopData,
  type PostV1DesktopIdComputerActionData
} from 'cyberdesk';

async function createAndInteract() {
  try {
    // 1. Create a new desktop
    console.log('Creating desktop...');
    const createResponse = await postV1Desktop({
      // Pass request body parameters inside the 'data' object
      data: {
         timeoutMs: 10000 
      }
      // Headers like Authorization should be set globally via setConfig (see above)
    });

    if (!createResponse.data) {
       throw new Error('Failed to create desktop: ' + (createResponse.error?.message || 'Unknown error'));
    }

    const desktopId = createResponse.data.id; // Assuming the response has an ID
    console.log(`Desktop created with ID: ${desktopId}`);

    // 2. Perform an action (e.g., a mouse click)
    console.log(`Performing action on desktop ${desktopId}...`);
    const actionData: PostV1DesktopIdComputerActionData['data'] = {
        type: 'click_mouse', // Example action type
        x: 100,
        y: 150
    };
    
    const actionResponse = await postV1DesktopIdComputerAction({
      path: { id: desktopId }, // Provide path parameters
      data: actionData // Provide request body data
    });

    if (actionResponse.error) {
      throw new Error(`Action failed: ${actionResponse.error.message}`);
    }

    console.log('Action successful:', actionResponse.data);

  } catch (error) {
    console.error('Error using Cyberdesk SDK:', error);
  }
}

createAndInteract();
```

## License

[MIT](LICENSE) 