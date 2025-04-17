# Cyberdesk Operator

A Kubernetes operator for managing Cyberdesk resources, built using Python and the Kopf (Kubernetes Operator Python Framework) framework.

## Overview

The Cyberdesk Operator watches for Cyberdesk custom resources and automatically provisions and manages KubeVirt VirtualMachine resources based on them. It handles:

- Creating VMs when new Cyberdesk resources are created
- Tracking VM status and updating the Cyberdesk status
- Enforcing timeouts to shutdown VMs that run longer than allowed
- Cleaning up resources when Cyberdesk instances are deleted

## Prerequisites

- Kubernetes cluster with KubeVirt installed
- Python 3.9+
- pip
- kubectl

## Installation

### 1. Create Dedicated Namespace

Create a dedicated namespace for the operator:

```bash
kubectl apply -f infra/kubevirt/cyberdesk-namespace.yaml
```

### 2. Use existing CRD

The Cyberdesk CRD is already defined in:
```
infra/kubevirt/cyberdesk-crd.yaml
```

### 3. Create RBAC resources

```bash
kubectl apply -f infra/kubevirt/cyberdesk-rbac.yaml
```

### 4. Deploy the operator

```bash
kubectl apply -f infra/kubevirt/cyberdesk-deployment.yaml
```

## Local Development Setup

To run the operator locally for development (e.g., using `kopf run`), you need to provide the Supabase credentials via environment variables.

1.  **Create a Virtual Environment (Recommended):**
    ```bash
    # Navigate to this directory (services/cyberdesk-operator)
    python -m venv .venv
    source .venv/bin/activate  # On Windows: .venv\Scripts\activate
    ```

2.  **Install Dependencies:** Ensure you have the necessary Python packages installed (including `python-dotenv`):
    ```bash
    pip install -r requirements.txt
    ```

3.  **Create a `.env` file:** Copy the example file:
    ```bash
    cp .env.example .env
    ```

4.  **Edit `.env`:** Open the newly created `.env` file and replace the placeholder values for `SUPABASE_URL` and `SUPABASE_KEY` with your actual Supabase credentials. You might also adjust `KOPF_NAMESPACE` if needed for local testing against a specific namespace.

5.  **Run with Kopf:** You can now run the operator locally. It will load the credentials from your `.env` file.
    ```bash
    # Make sure your virtual environment is active
    # Example using kopf run:
    kopf run ./handlers/controller.py --standalone --verbose
    ```
    *(Remember to configure your local `kubectl` context to point to the desired cluster if interacting with Kubernetes resources during local runs)*

## Building the Container

```bash
docker build -t cyberdesk-operator:latest .
```

## Usage

Create a Cyberdesk resource:

```bash
kubectl apply -f infra/kubevirt/cyberdesk-cr.yaml
```

Check the status:

```bash
kubectl get cyberdesks
```

## VM Template Customization

The operator uses a template file to create VMs, which is stored as a ConfigMap in the `cyberdesk-system` namespace. The template file is defined in the deployment YAML in `infra/kubevirt/cyberdesk-deployment.yaml`.

The template uses the following variables that will be substituted at runtime:
- `${vm_name}`: The name of the VM (prefixed with "cyberdesk-")
- `${namespace}`: The namespace where the VM will be created
- `${cyberdesk_name}`: The name of the Cyberdesk resource
- `${managed_by}`: The name of the operator/system managing this VM
- `${user_data_base64}`: Base64-encoded cloud-init user data (used for VM customization)

To modify the template, you can:
1. Edit the ConfigMap directly:
   ```bash
   kubectl edit configmap -n cyberdesk-system cyberdesk-vm-template
   ```

2. Or update the template in `infra/kubevirt/cyberdesk-deployment.yaml` and reapply:
   ```bash
   kubectl apply -f infra/kubevirt/cyberdesk-deployment.yaml
   ```

## Key Features

- **VM Lifecycle Management**: Automatically creates and manages VMs from Cyberdesks
- **Status Tracking**: Updates Cyberdesk status based on underlying VM status
- **Timeout Enforcement**: Automatically shuts down VMs that exceed their specified timeout
- **Resource Cleanup**: Ensures all resources are properly cleaned up on deletion
- **Template-based VM Creation**: Uses a template file for VM specifications, making it easy to customize

## Architecture

The operator uses a watch-based approach through Kopf to:
1. Watch for Cyberdesk resource changes
2. Watch for VirtualMachineInstance updates
3. Run periodic checks for timeout enforcement

All handler logic is implemented in `handlers/controller.py`.

## Troubleshooting

- **Idempotency**: All handlers are designed to be idempotent by checking the current state of resources before making changes.
- **Leader Election**: Kopf provides built-in leader election to ensure only one operator instance handles state-changing events in a multi-replica deployment.
- **Secrets Management**: In production, secrets are managed through Kubernetes Secret resources. For local development, a .env file can be used with python-dotenv.

## Checking Logs

```bash
kubectl logs -n cyberdesk-system -l app=cyberdesk-operator -f
``` 