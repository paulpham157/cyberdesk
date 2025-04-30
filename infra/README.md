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

## 1. Infrastructure: Deploy AKS with Terraform

```bash
cd ./terraform
terraform init
terraform apply -var-file=dev.tfvars -auto-approve # or prod.tfvars
```

---

## 2. Configure kubectl Access

```bash
az aks get-credentials --resource-group <your-rg> --name <your-aks>
```

---

## 3. Deploy KubeVirt Operator and CR

```bash
kubectl apply -f ./kubernetes/kubevirt-operator.yaml
kubectl apply -f ./kubernetes/kubevirt-cr.yaml
```

---

## 4. Deploy Containerized Data Importer (CDI)

CDI is required for KubeVirt features like cloning PVCs and importing disk images. This is the recommended way to create VM root disks with specific sizes.

```bash
kubectl apply -f ./kubernetes/cdi-operator.yaml
kubectl apply -f ./kubernetes/cdi-cr.yaml

# Wait for CDI pods to be ready (optional check)
kubectl wait --for=condition=Ready pod -l app.kubernetes.io/component=cdi-operator -n cdi --timeout=300s
kubectl wait --for=condition=Ready pod -l cdi.kubevirt.io -n cdi --timeout=300s
```

---

## 5. Apply Azure Disk Snapshot Class (REQUIRED for KubeVirt Snapshots)

```bash
kubectl apply -f ./kubernetes/azure-snapshot-class.yaml
```

This enables snapshotting for Azure disks and is required for KubeVirt VM snapshots and cloning.

---

## 6. Create the Golden VM and Snapshot (REQUIRED for Cyberdesk Operator)

> **Note:** The golden VM manifest is gitignored. Ask a team member for `golden-vm-deploy.yaml`.

1. **Apply the Golden VM:**
   ```bash
   kubectl apply -f ./kubernetes/golden-vm-deploy.yaml
   ```
2. **Wait for the VM to fully boot and complete cloud-init.**
   - Check with:
     ```bash
     kubectl get vmi -n kubevirt
     # Wait for the VM to be Running and cloud-init to finish
     ```
3. **Stop the Golden VM:**
   ```bash
   virtctl stop golden-vm -n kubevirt
   # Wait for the VM to be fully stopped
   ```
4. **Create the Golden Snapshot:**
   ```bash
   kubectl apply -f ./kubernetes/golden-vm-snapshot-request.yaml
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

---

## 8. Deploy the Default Backend and Catch-All Ingress

1. **Apply the default-backend DaemonSet and Service:**
   (See `default-backend.yaml` in this repo or request from a team member)
   ```bash
   kubectl apply -f ./kubernetes/default-backend.yaml
   ```
2. **Apply a catch-all Ingress to route unmatched traffic to the default backend:**
   (See `default-backend-ingress.yaml` or request from a team member)
   ```bash
   kubectl apply -f ./kubernetes/default-backend-ingress.yaml
   ```
3. **Verify Azure Load Balancer health probes are healthy for all nodes** (in Azure Portal).

---

## 9. Install cert-manager (YAML, NOT Helm)

```bash
kubectl apply --validate=false -f https://github.com/cert-manager/cert-manager/releases/download/v1.14.1/cert-manager.yaml
```
- Wait for all pods in `cert-manager` namespace to be Running.

---

## 10. Apply ClusterIssuer for Let's Encrypt

1. **Edit and apply `cluster-issuer.yaml`:**
   (Ask a team member for this file if not present)
   ```bash
   kubectl apply -f ./kubernetes/cluster-issuer.yaml
   ```
2. **Verify the ClusterIssuer is READY:**
   ```bash
   kubectl get clusterissuer
   ```

---

## 11. Build and Push Operator and Gateway Images

If you have made changes to the operator or gateway code, you need to rebuild and push the images with a **unique, specific tag** (e.g., using Semantic Versioning like `v1.2.3` or a Git commit SHA like `a1b2c3d4`). **Avoid using the `:latest` tag**.

### Cyberdesk Operator

**Bash:**
```bash
# Navigate to the operator directory
cd ../services/cyberdesk-operator
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

## 12. Deploy Cyberdesk Operator and Gateway

1. **Apply the Supabase Secret:**
   (Ask a team member for `cyberdesk-secret.yaml`)
   ```bash
   kubectl apply -f ./kubernetes/cyberdesk-secret.yaml
   ```
2. **Deploy the Cyberdesk Operator:**
   ```bash
   kubectl apply -f ./kubernetes/cyberdesk-operator.yaml
   ```
3. **Deploy the Gateway:**
   ```bash
   kubectl apply -f ./kubernetes/gateway-deploy.yaml
   ```
4. **Trigger Operator Setup:**
   ```bash
   kubectl apply -f ./kubernetes/start-cyberdesk-operator-cr.yaml
   ```

---

## 13. Verify Everything

- Check pod status in all namespaces:
  ```bash
  kubectl get pods -A
  ```
- Check Ingress and certificate status:
  ```bash
  kubectl get ingress -A
  kubectl get certificate -A
  kubectl describe certificate <name> -n <namespace>
  ```
- Test your domain over HTTPS.

---

**For any files marked as gitignored, ask a team member for the latest version.**

---