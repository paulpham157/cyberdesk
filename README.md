# Cyberdesk

Cyberdesk is a comprehensive platform that provides a suite of tools and services for managing virtual desktops, APIs, documentation, and more. This repository contains various components of the Cyberdesk project, including the API, documentation, web application, operator, and SDK.

## Prerequisites

Before running the project, ensure you have the following prerequisites installed:

- Node.js (v14 or higher)
- npm or yarn
- Docker
- Kubernetes
- Supabase account
- Unkey account

## Installation

To install the project, follow these steps:

1. Clone the repository:

```bash
git clone https://github.com/cyberdesk-hq/cyberdesk.git
cd cyberdesk
```

2. Install dependencies for each component:

```bash
# Install dependencies for the API
cd apps/api
npm install

# Install dependencies for the documentation
cd ../docs
npm install

# Install dependencies for the web application
cd ../web
npm install

# Install dependencies for the operator
cd ../../services/cyberdesk-operator
pip install -r requirements.txt

# Install dependencies for the SDK
cd ../../sdks/ts-sdk
npm install
```

## Usage

To run the project, follow these steps:

1. Start the API:

```bash
cd apps/api
npm run dev
```

2. Start the documentation:

```bash
cd ../docs
npm run dev
```

3. Start the web application:

```bash
cd ../web
npm run dev
```

4. Run the operator locally:

```bash
cd ../../services/cyberdesk-operator
docker build -t cyberdesk/cyberdesk-operator:local .
docker run --rm -it -v "${env:USERPROFILE}\.kube:/root/.kube:ro" --env-file ./.env cyberdesk/cyberdesk-operator:local
```

5. Use the SDK:

Refer to the [SDK README](sdks/ts-sdk/README.md) for usage examples and instructions.

## Links to Existing README Files

For more detailed information about each component, refer to the existing `README.md` files:

- [API README](apps/api/README.md)
- [Documentation README](apps/docs/README.md)
- [Web Application README](apps/web/README.md)
- [Operator README](services/cyberdesk-operator/README.md)
- [SDK README](sdks/ts-sdk/README.md)

## Contributing

We welcome contributions to the Cyberdesk project. Please refer to the [implementation guidelines](services/cyberdesk-operator/checklist.md) for more information on how to contribute.

## License

This project is licensed under the [LICENSE.md](apps/web/LICENSE.md) file in the `apps/web` directory.
