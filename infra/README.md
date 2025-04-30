# Cyberdesk AKS/KubeVirt Deployment Guide

This guide walks you through deploying Cyberdesk on Azure Kubernetes Service (AKS) with KubeVirt, including all required infrastructure, snapshotting, ingress, and certificate management. **Follow the steps in order for a successful deployment.**

---

## Prerequisites
- [Terraform](https://www.terraform.io/downloads.html)
- [Azure CLI](https://docs.microsoft.com/en-us/cli/azure/install-azure-cli)
- [kubectl](https://kubernetes.io/docs/tasks/tools/)
- [kubelogin](https://github.com/Azure/kubelogin)
- [virtctl](https://kubevirt.io/user-guide/operations/virtctl_client_tool/)
- Azure subscription with permissions

---

## 1. Authenticate and Set Up Terraform Workspaces

### 1.1 Authenticate with Azure
Before running any Terraform commands, authenticate with Azure CLI:
```bash
az login
az account set --subscription <your-subscription-id>
```
Replace `<your-subscription-id>` with the correct Azure subscription for your environment (this may be auto-set if you're using the Azure CLI to login).

### 1.2 Initialize Terraform
Navigate to the terraform directory and initialize:
```bash
cd ./terraform
terraform init
```

### 1.3 Using Workspaces for Dev and Prod
Terraform workspaces allow you to manage separate state for different environments (e.g., dev and prod).

#### **Create and Use the Dev Workspace**
```bash
# Create the dev workspace if it doesn't exist
terraform workspace new dev
# Switch to the dev workspace
terraform workspace select dev
# Apply the dev configuration
terraform apply -var-file="dev.tfvars" -auto-approve
```

#### **Create and Use the Prod Workspace**
```bash
# Create the prod workspace if it doesn't exist
terraform workspace new prod
# Switch to the prod workspace
terraform workspace select prod
# Apply the prod configuration
terraform apply -var-file="prod.tfvars" -auto-approve
```

- Always make sure you are in the correct workspace before running `plan` or `apply`.
- Each workspace maintains its own state, so dev and prod resources are managed separately.

---

## 2. Configure kubectl Access

After deploying your environment, configure kubectl access to your AKS cluster. You will need the resource group name and AKS cluster name, which are defined in your tfvars file for the environment you just deployed (either dev.tfvars or prod.tfvars).

- For **dev**:
  - Use the values of `resource_group_name` and `aks_cluster_name` from `dev.tfvars`.
- For **prod**:
  - Use the values of `resource_group_name` and `aks_cluster_name` from `prod.tfvars`.

Example:
```bash
az aks get-credentials --resource-group <resource_group_name_from_tfvars> --name <aks_cluster_name_from_tfvars>
```
Replace the placeholders with the actual values from your tfvars file.

---

## 3. Deploy KubeVirt Operator and CR

Note: From now on, you'll want to navigate to the correct folders to apply the correct YAMLs. For the most part, you'll be in the `infra/kubernetes` folder.

```bash
kubectl apply -f kubevirt-operator.yaml
kubectl apply -f kubevirt-cr.yaml
```

---

## 4. Deploy Containerized Data Importer (CDI)

CDI is required for KubeVirt features like cloning PVCs and importing disk images. This is the recommended way to create VM root disks with specific sizes.

```bash
kubectl apply -f cdi-operator.yaml
kubectl apply -f cdi-cr.yaml

# Wait for CDI pods to be ready (optional check)
kubectl wait --for=condition=Ready pod -l cdi.kubevirt.io -n cdi --timeout=300s
```

---

## 5. Apply Azure Disk Snapshot Class (REQUIRED for KubeVirt Snapshots)

```bash
kubectl apply -f azure-snapshot-class.yaml
```

This enables snapshotting for Azure disks and is required for KubeVirt VM snapshots and cloning.

---

## 6. Create the Golden VM and Snapshot (REQUIRED for Cyberdesk Operator)

> **Note:** The golden VM manifest is gitignored. Reference Notion or ask a team member for `golden-vm-deploy.yaml`

1. **Apply the Golden VM:**
   ```bash
   kubectl apply -f golden-vm-deploy.yaml
   ```
2. **Wait for the VM to fully boot and complete cloud-init.**
   - Check with:
     ```bash
     # Wait for the VM to be Running
     kubectl get vmi -n kubevirt
     
     # Access the VM console (to login, reference the golden-vm-deploy.yaml file to see the credentials)
     virtctl console golden-vm -n kubevirt

     # Inside the VM, if there doesn't seem to be any cloud-init logs, run this and see if "status:done" is printed
     cloud-init status
     ```
     - Once done, exit the VM console with ctrl / cmd + ]
3. **Stop the Golden VM:**
   ```bash
   virtctl stop golden-vm -n kubevirt
   # Wait for the VM to be fully stopped
   kubectl get vm golden-vm -n kubevirt
   ```
4. **Create the Golden Snapshot:**
   ```bash
   kubectl apply -f golden-vm-snapshot-request.yaml
   ```
   - Wait for the snapshot to be ready:
     ```bash
     kubectl get vmsnapshot -n kubevirt
     ```

---

## 7. Install ingress-nginx (YAML, NOT Helm)

```bash
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.10.1/deploy/static/provider/cloud/deploy.yaml
```
- Wait for all pods in `ingress-nginx` namespace to be Running.

```bash
kubectl get pods -n ingress-nginx
```

---

## 8. Deploy the Default Backend and Catch-All Ingress

1. **Apply the default-backend DaemonSet, Service, and catch-all Ingress:**
   (See `default-backend.yaml` in this repo or request from a team member)
   This ensures that Azure Load Balancer health probes are healthy for all nodes, and that unmatched traffic is routed to the default backend. If you don't do this, the Gateway will not be accessible via https.
   ```bash
   kubectl apply -f default-backend.yaml
   ```
2. **Optional: Verify Azure Load Balancer health probes are healthy for all nodes** (in Azure Portal).
   - They probably are, but if you're having trouble connecting to the Gateway, check this.

---

## 9. Install cert-manager (YAML, NOT Helm)

```bash
kubectl apply --validate=false -f https://github.com/cert-manager/cert-manager/releases/download/v1.14.1/cert-manager.yaml
```
- Wait for all pods in `cert-manager` namespace to be Running.

```bash
kubectl get pods -n cert-manager
```

---

## 10. Build and Push Operator and Gateway Images

If you have made changes to the operator or gateway code, you need to rebuild and push the images with a **unique, specific tag** (e.g., using Semantic Versioning like `v1.2.3` or a Git commit SHA like `a1b2c3d4`). **Avoid using the `:latest` tag**.

### Cyberdesk Operator

**Bash:**
```bash
# Navigate to the operator directory
cd ../../services/cyberdesk-operator
# Build the docker image with a specific tag (ensure Docker daemon is running)
docker build -t cyberdesk/cyberdesk-operator:NEW_VERSION_TAG_HERE .
# Push the image to Docker Hub
docker push cyberdesk/cyberdesk-operator:NEW_VERSION_TAG_HERE
```
**PowerShell:**
```powershell
cd ../services/cyberdesk-operator
docker build -t "cyberdesk/cyberdesk-operator:NEW_VERSION_TAG_HERE" .
docker push cyberdesk/cyberdesk-operator:NEW_VERSION_TAG_HERE
```
**Important:** After building and pushing, you **must update** the `image:` field in `infra/kubernetes/cyberdesk-operator.yaml` to reference the **specific tag** you just used.

### Gateway

**Bash:**
```bash
cd ../services/gateway
docker build -t cyberdesk/gateway:NEW_GATEWAY_TAG_HERE .
docker push cyberdesk/gateway:NEW_GATEWAY_TAG_HERE
```
**PowerShell:**
```powershell
cd ../services/gateway
docker build -t "cyberdesk/gateway:NEW_GATEWAY_TAG_HERE" .
docker push cyberdesk/gateway:NEW_GATEWAY_TAG_HERE
```
**Important:** After building and pushing, you **must update** the `image:` field in `infra/kubernetes/gateway-deploy.yaml` to reference the **specific tag** you just used.

---

## 11. Deploy Cyberdesk Operator and Gateway

1. **Apply the Supabase Secret:**
   (Ask a team member for `cyberdesk-secret.yaml`)
   ```bash
   kubectl apply -f cyberdesk-secret.yaml
   ```
2. **Deploy the Cyberdesk Operator:**
   ```bash
   kubectl apply -f cyberdesk-operator.yaml
   ```
3. **Deploy the Gateway:**
   ```bash
   kubectl apply -f gateway-deploy.yaml
   ```
4. **Trigger Operator Setup:**
   ```bash
   kubectl apply -f start-cyberdesk-operator-cr.yaml
   ```

---

## 12. Apply the ClusterIssuer and Gateway Ingress

Before applying your Ingress resources, you must first create the ClusterIssuer, which is defined in a separate file (`cluster-issuer.yaml`). This ClusterIssuer is required for cert-manager to issue certificates for your Ingress resources.

- **Step 1: Apply the ClusterIssuer**

  ```bash
  kubectl apply -f cluster-issuer.yaml
  ```

- **Step 2: Apply the Gateway Ingress**

  For **dev** (in your dev cluster):

  ```bash
  kubectl apply -f gateway-ingress-dev.yaml
  ```

  For **prod** (in your prod cluster):

  ```bash
  kubectl apply -f gateway-ingress-prod.yaml
  ```

Wait for the Ingress to be assigned an external IP:

```bash
kubectl get ingress -n cyberdesk-system
```

---

## 13. Set Up DNS for Gateway

Once your Ingress has an external IP, set up your DNS records (Cyberdesk manages it in Cloudflare, see credentials in Notion):

- For **dev**:  
  Create an A record for `dev-gateway.cyberdesk.io` pointing to your dev cluster's Ingress external IP. Disable proxy on the record, if it's enabled.
- For **prod**:  
  Create an A record for `gateway.cyberdesk.io` pointing to your prod cluster's Ingress external IP. Disable proxy on the record, if it's enabled.

Update your DNS provider with the correct IP.

Your DNS is ready when nslookup returns the correct IP (should be relatively quick).

```bash
nslookup gateway.cyberdesk.io (or dev-gateway.cyberdesk.io)
```
---

## 14. Verify Ingress and Certificate

Check that your Ingress and certificate resources are created and progressing:

```bash
kubectl get ingress -n cyberdesk-system
kubectl get clusterissuer
kubectl get certificate -n cyberdesk-system
kubectl describe certificate <name> -n cyberdesk-system
```

- The certificate may take a few minutes to become `READY` after DNS is set up.
- If it does not, check DNS, Ingress, and cert-manager logs for troubleshooting.

---

## 15. Initiate Virtual Machine Warm Pool

Before starting the warm pool, you must update `warm-pool.yaml` to reference the correct snapshot name for the golden VM's root disk.

1. **Get the name of the new root disk snapshot:**
   ```bash
   kubectl get volumesnapshots -n kubevirt
   ```
   - Look for the snapshot associated with your golden VM (it will look like `vmsnapshot-<uuid>-volume-rootdisk`).

2. **Edit `warm-pool.yaml`:**
   - Update the `snapshot: name:` field to match the name you found above.
   - Check the YAML to see if the desired amount of replicas are set. In dev, usually 1 is enough. In prod, this should probably be much, much higher.
3. **Apply the warm pool:**
   ```bash
   kubectl apply -f warm-pool.yaml
   ```

## 16. Verify Everything

- Check pod status in all namespaces:
  ```bash
  kubectl get pods -A
  ```
- Check if the warm pool is running:
  ```bash
  kubectl get vms -n kubevirt # should see 1 or more warm pool VMs starting up and eventually running
  ```
- Check if the Gateway is accessible:
  ```bash
  curl -k https://gateway.cyberdesk.io/healthz # (or dev-gateway.cyberdesk.io if you're in dev)
  ```

## 17. Delete the Golden VM
Since we've snapshotted it, we can delete it now. 
```bash
kubectl delete vm golden-vm -n kubevirt
```

## 18. Local Development
- Head to /apps/api, and make sure your .env contains the correct values, but most importantly, make sure the `GATEWAY_URL` is set to the correct URL (dev-gateway.cyberdesk.io or gateway.cyberdesk.io). Note: if set to dev-gateway.cyberdesk.io, stream URL's returned from the Gateway service will be overridden to use the dev-gateway.cyberdesk.io domain.
- Run `npm run dev` to start the API.
- Head to /apps/web, and make sure your .env contains the correct values, but most importantly, make sure the `CYBERDESK_API_BASE_URL` is set to http://localhost:3001 (or whatever port your API is running on).
- Run `npm run dev` to start the web app.

You're now set to start developing! Make sure you branch off from `dev` and create a new branch for your work.

## 19. Deploying to Prod
- Make a PR to merge your changes into `dev`.
- Once approved, merge your PR into `dev`.
- Carefully plan how you will bring the changes you made into the production cluster. Make sure to switch kubeconfig to prod before you start, using `az aks get-credentials --resource-group <resource-group-name> --name <aks-cluster-name>`.
- Make final tests in the dev cluster to ensure everything is working as expected.
- Once you're ready, make a PR to merge your changes into `prod`.
- Once approved, merge your PR into `prod`.
- Apply the changes to the production cluster using kubectl (for example, if the Gateway has a new image, you can do kubectl rollout restart deployment gateway -n cyberdesk-system).
- Make sure corresponding changes to the developer API / web app / docs are also being pushed to live via Vercel / Fly.io.
TODO: Figure out how to orchestrate this better. Right now, there is discrepency between when cluster changes are pushed vs when the developer API / web app are pushed to live (since we have so many different hosting environments).