<p align="center">
  <img src="assets/cyberdesk-logo-with-text.png" alt="Cyberdesk Logo with Text" width="500" />
</p>

<p align="center">
  <!-- NPM Version -->
  <a href="https://www.npmjs.com/package/cyberdesk">
    <img src="https://img.shields.io/npm/v/cyberdesk?color=cb3837&logo=npm" alt="NPM Version" />
  </a>
  <!-- NPM Downloads -->
  <a href="https://www.npmjs.com/package/cyberdesk">
    <img src="https://img.shields.io/npm/dw/cyberdesk?color=cb3837&logo=npm" alt="NPM Downloads" />
  </a>
  <!-- PyPI Version -->
  <a href="https://pypi.org/project/cyberdesk/">
    <img src="https://img.shields.io/pypi/v/cyberdesk?color=3776ab&logo=pypi" alt="PyPI Version" />
  </a>
  <!-- PyPI Downloads -->
  <a href="https://pypi.org/project/cyberdesk/">
    <img src="https://img.shields.io/pypi/dw/cyberdesk?color=3776ab&logo=pypi" alt="PyPI Downloads" />
  </a>
</p>
<p align="center">
  <!-- Discord -->
  <a href="https://discord.gg/ws5ddx5yZ8">
    <img src="https://img.shields.io/discord/1228348939648004096?label=discord&logo=discord&color=5865F2" alt="Discord" />
  </a>
  <!-- License -->
  <a href="LICENSE">
    <img src="https://img.shields.io/badge/license-Apache%202.0-blue.svg" alt="License: Apache 2.0" />
  </a>
  <!-- GitHub Stars (optional) -->
  <a href="https://github.com/cyberdesk-hq/cyberdesk">
    <img src="https://img.shields.io/github/stars/cyberdesk-hq/cyberdesk?style=social" alt="GitHub Stars" />
  </a>
</p>

<div align="center">
  <img src="assets/QuickDemo.gif" alt="Cyberdesk Demo GIF" style="max-width:100%; height:auto; margin-top: 16px;" />
  <div><i>A computer-use agent operating on a Cyberdesk Virtual Machine based on a user prompt</i></div>
</div>

<br>
Cyberdesk is a comprehensive platform that provides a suite of tools and services for managing virtual desktops, APIs, documentation, and more. With these tools you can setup a computer use agent like the one shown above in as little as an hour. This repository contains various components of the Cyberdesk project, including the API, documentation, web application, operator, and SDK.
<br>

# Getting Started

To quickly get started with building your own computer-use agents using Cyberdesk's infra, head on over to [docs.cyberdesk.io](https://docs.cyberdesk.io/docs/quickstart). To mess around with the interactive demo checkout out [cyberdesk.io](https://www.cyberdesk.io).

If you'd like to run the actual project locally, proceed with the rest of this README (work in progress, contact a team member for a personal 1-1 walkthrough of how to self host the project).

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

This project is licensed under the [Apache License 2.0](LICENSE) file in the root directory.
