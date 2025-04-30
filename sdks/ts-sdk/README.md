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

First, create a Cyberdesk client instance with your API key:

```typescript
import { createCyberdeskClient } from 'cyberdesk';

const cyberdesk = createCyberdeskClient({
  apiKey: 'YOUR_API_KEY',
  // Optionally, you can override the baseUrl or provide a custom fetch implementation
});
```

### Launch a Desktop

```typescript
const launchResult = await cyberdesk.launchDesktop({
  body: { timeout_ms: 10000 } // Optional: set a timeout for the desktop session
});

if (launchResult.error) {
  throw new Error('Failed to launch desktop: ' + launchResult.error.error);
}

const desktopId = launchResult.id;
console.log('Launched desktop with ID:', desktopId);
```

### Get Desktop Info

```typescript
const info = await cyberdesk.getDesktop({
  path: { id: desktopId }
});

if ('error' in info) {
  throw new Error('Failed to get desktop info: ' + info.error);
}

console.log('Desktop info:', info);
```

### Perform a Computer Action (e.g., Mouse Click)

```typescript
const actionResult = await cyberdesk.executeComputerAction({
  path: { id: desktopId },
  body: {
    type: 'click_mouse',
    x: 100,
    y: 150
  }
});

if (actionResult.error) {
  throw new Error('Action failed: ' + actionResult.error);
}

console.log('Action result:', actionResult);
```

### Run a Bash Command

```typescript
const bashResult = await cyberdesk.executeBashAction({
  path: { id: desktopId },
  body: {
    command: 'echo Hello, world!'
  }
});

if (bashResult.error) {
  throw new Error('Bash command failed: ' + bashResult.error);
}

console.log('Bash output:', bashResult.output);
```

## TypeScript Support

All request parameter types and the `CyberdeskSDK` type are exported for convenience:

```typescript
import type { LaunchDesktopParams, CyberdeskSDK } from 'cyberdesk';
```

## License

[MIT](LICENSE) 