# Cyberdesk API Gateway

This FastAPI application acts as a micro-gateway for the Cyberdesk system. Its primary responsibilities include:

1.  **Serving the noVNC UI:** Provides the static web files for the browser-based VNC client.
2.  **Proxying VNC WebSockets:** Securely proxies WebSocket connections from the browser's noVNC client to the KubeVirt VNC sub-resource endpoint for a specific Virtual Machine Instance (VMI).
3.  **Managing Cyberdesk CRs:** Handles API requests to create and delete `Cyberdesk` custom resources within the Kubernetes cluster.
4.  **(Future)** Proxying terminal commands via execDaemon.

## Running Locally (Development)

These instructions explain how to run the gateway service locally on your machine (e.g., Windows) for development purposes, connecting to a Kubernetes cluster (like AKS, Minikube, k3d, or Docker Desktop's built-in cluster).

### Prerequisites

1.  **Docker Desktop:** You need Docker installed and running to build and run the container image. Download and install it from [docker.com](https://www.docker.com/products/docker-desktop/).
2.  **Kubernetes Cluster Access:** You need `kubectl` configured to talk to your Kubernetes cluster.
    *   **AKS Example:** If using Azure Kubernetes Service (AKS) like the main Cyberdesk deployment, you can fetch credentials using the Azure CLI:
        ```bash
        # Login to Azure first if needed: az login
        az aks get-credentials --resource-group rg-p-scu-kubevirt --name aks-p-scu-kubevirt
        ```
        *(Replace the resource group and cluster name if you have a different setup).*
    *   **Other Clusters:** Ensure your `~/.kube/config` (or `${env:USERPROFILE}\.kube\config` on Windows) is correctly set up for `kubectl` to access your cluster.

### Steps

1.  **Build the Docker Image:**
    Navigate to the `services/gateway` directory in your terminal and run:
    ```bash
    docker build -t cyberdesk/gateway:local .
    ```
    *(You can change the tag `:local` if you prefer).*

2.  **Adjust Kubeconfig Server Address (If Necessary):**
    The gateway running inside Docker needs to reach your Kubernetes API server. If your `kubeconfig` file (`${env:USERPROFILE}\.kube\config`) has `server:` entries pointing to `https://localhost:...` or `https://127.0.0.1:...`, the container won't be able to connect.
    *   **Edit the file:** Change `localhost` or `127.0.0.1` to `host.docker.internal`.
    *   **Example (before):** `server: https://localhost:6443`
    *   **Example (after):** `server: https://host.docker.internal:6443`
    *   *(This special DNS name is provided by Docker Desktop).*

3.  **Run the Docker Container:**
    Open your terminal and run the appropriate command for your shell:

    *   **PowerShell (Windows):**
        ```powershell
        docker run --rm -it `
          -v "${env:USERPROFILE}\.kube:/root/.kube:ro" `
          --env-file ./.env `
          -p 3001:80 `
          cyberdesk/gateway:local
        ```
        *(Note: We use `${env:USERPROFILE}\.kube` to correctly locate your kubeconfig folder on Windows.)*

    *   **Bash (Linux/macOS/WSL):**
        ```bash
        docker run --rm -it \
          -v ~/.kube:/root/.kube:ro \
          --env-file ./.env \
          -p 3001:80 \
          cyberdesk/gateway:local
        ```
        *(Note: We use `~/.kube` for the standard kubeconfig location on Unix-like systems.)*

    **Command Breakdown:**
    *   `--rm`: Automatically removes the container when it exits.
    *   `-it`: Runs interactively so you can see logs and stop with Ctrl+C.
    *   `-v ...:/root/.kube:ro`: **Crucial!** Mounts your host's `.kube` directory (containing the `config` file) into the container at `/root/.kube`. We use the appropriate path for PowerShell or Bash. `:ro` makes it read-only inside the container for safety.
    *   `-p 3001:80`: Maps port 3001 on your host machine to port 80 inside the container (where Uvicorn runs by default). You can change `3001` if needed.
    *   `cyberdesk/gateway:local`: The image name and tag you built.

4.  **Access the Service:**
    The gateway should now be running and accessible at `http://localhost:3001` on your host machine. You can test endpoints like `http://localhost:3001/healthz`.

5.  **For the noVNC stream, you need to run the following command:**
    ```bash
    kubectl get pods -n kubevirt

    # Find the pod with id 'virt-launcher-<vm-id>-<pod-id>'

    kubectl port-forward <pod-id> 5901:5901 -n kubevirt
    ```

    This will forward port 5901 on your host machine to port 5901 on the pod that runs the Kubevirt VM. This allows you to connect to the VM's desktop environment via the noVNC stream via the URL: `http://localhost:3001/vnc/<vm-id>`.
