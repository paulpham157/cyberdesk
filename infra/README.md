# KubeVirt on AKS Deployment

This directory contains Terraform configurations to deploy a Kubernetes cluster on Azure Kubernetes Service (AKS),
and then directions to manually deploy KubeVirt and the Cyberdesk Operator to the cluster.

## Prerequisites

- [Terraform](https://www.terraform.io/downloads.html) installed
- [Azure CLI](https://docs.microsoft.com/en-us/cli/azure/install-azure-cli) installed
- Azure subscription with appropriate permissions
- [kubectl](https://kubernetes.io/docs/tasks/tools/) installed
- [kubelogin](https://github.com/Azure/kubelogin) installed (for Azure AKS authentication)
- [virtctl](https://kubevirt.io/user-guide/operations/virtctl_client_tool/) KubeVirt client utility installed

## Deployment Steps

### 1. Infrastructure Deployment with Terraform

First, navigate to the terraform directory:

```bash
cd ./terraform
```

Initialize and apply the Terraform configuration:

```bash
terraform init
terraform validate
terraform plan
terraform apply -auto-approve
```

### 2. Configure Kubernetes Access

Once the AKS cluster is deployed, configure your local kubectl to access it:

Production:
```bash
az aks get-credentials --resource-group rg-p-scu-kubevirt --name aks-p-scu-kubevirt
```

Development:
```bash
az aks get-credentials --resource-group rg-d-scu-kubevirt --name aks-d-scu-kubevirt
```

### 3. Deploy KubeVirt

Apply the KubeVirt operator:

```bash
kubectl apply -f ../kubernetes/kubevirt-operator.yaml
```

Apply the KubeVirt custom resource:

```bash
kubectl apply -f ../kubernetes/kubevirt-cr.yaml
```

### 3.5 Deploy Containerized Data Importer (CDI)

CDI is required to use KubeVirt features like cloning PersistentVolumeClaims (PVCs) or importing disk images into PVCs. This is the recommended way to create VM root disks with specific sizes.

```bash
kubectl apply -f ../kubernetes/cdi-operator.yaml
kubectl apply -f ../kubernetes/cdi-cr.yaml

# Wait for CDI pods to be ready (optional check)
kubectl wait --for=condition=Ready pod -l app.kubernetes.io/component=cdi-operator -n cdi --timeout=300s
kubectl wait --for=condition=Ready pod -l cdi.kubevirt.io -n cdi --timeout=300s
```

### 4. Deploy the Cyberdesk Operator

#### 4.1 Build and Push the Operator Image (If necessary)

If you have made changes to the operator code, you need to rebuild and push the image with a **unique, specific tag** (e.g., using Semantic Versioning like `v1.2.3` or a Git commit SHA like `a1b2c3d4`). **Avoid using the `:latest` tag**, as it can lead to unpredictable behavior with Kubernetes image caching (`imagePullPolicy: IfNotPresent`).

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
# Navigate to the operator directory
cd ../services/cyberdesk-operator

# Build the docker image with a specific tag (ensure Docker daemon is running)
docker build -t "cyberdesk/cyberdesk-operator:NEW_VERSION_TAG_HERE" .

# Push the image to Docker Hub
docker push cyberdesk/cyberdesk-operator:NEW_VERSION_TAG_HERE

```

**Important:** After building and pushing, you **must update** the `image:` field in `../infra/kubernetes/cyberdesk-operator.yaml` to reference the **specific tag** you just used (e.g., `image: cyberdesk-operator:v0.1.0` or `image: your-registry.io/cyberdesk-operator:v0.1.0`).

```bash
# Navigate back to the infra directory
cd ../../infra
```

#### 4.2 Apply the Supabase Secret (Manual Step)

Before deploying the operator, you **must** apply the Kubernetes Secret containing the Supabase credentials. This secret is intentionally kept in a separate file (`infra/kubernetes/cyberdesk-secret.yaml`) and excluded via `.gitignore` to prevent committing sensitive data to version control. Ask a team member for the file.

**1. Edit the Secret File:**
   Create / open `infra/kubernetes/cyberdesk-secret.yaml` and replace the placeholder values `<your-supabase-url>` and `<your-supabase-key>` with your actual Supabase credentials.

**2. Apply the Secret (and the relevant Namespace):**
```bash
kubectl apply -f ./kubernetes/cyberdesk-secret.yaml
```

This command creates the `supabase-credentials` Secret object in the `cyberdesk-system` namespace, which the operator deployment requires.

#### 4.3 Deploy the Operator and Core Resources

Now that the secret exists in the cluster, deploy the main operator manifest. This single manifest contains the Namespace, ServiceAccount, RBAC rules, the Deployment for the operator, the ConfigMap for the VM template, and the trigger CRD (`StartCyberdeskOperator`).

Make sure the `image:` tag in this file matches the image you built and pushed (if applicable).

```bash
kubectl apply -f ./kubernetes/cyberdesk-operator.yaml
```

Verify the operator deployment starts:

```bash
kubectl get deployment -n cyberdesk-system cyberdesk-operator
# Wait for AVAILABLE replicas to be 1
kubectl get pods -n cyberdesk-system -l app=cyberdesk-operator
```

#### 4.4 Trigger Operator Setup

Apply the `StartCyberdeskOperator` custom resource. This signals the running operator to perform its initial setup, primarily creating the `Cyberdesk` CRD.

```bash
kubectl apply -f ./kubernetes/start-cyberdesk-operator-cr.yaml
```

## Verification

To verify your deployment, you can check the status of KubeVirt components:

```bash
kubectl get pods -n kubevirt
```

You can also verify that the Cyberdesk CRD is ready:

```bash
kubectl api-resources | grep cyberdesk
```

Check that the operator pod is running:

```bash
kubectl get pods -n cyberdesk-system -l app=cyberdesk-operator
```

Verify that the `Cyberdesk` CRD was created by the operator (this might take a few moments after applying the trigger CR):

```bash
kubectl get crd cyberdesks.cyberdesk.io
```

You can also check the operator logs to confirm it processed the trigger and created the CRD:

```bash
kubectl logs -n cyberdesk-system -l app=cyberdesk-operator -f
```

## Testing the Cyberdesk Operator

Ensure the operator setup has completed (check `kubectl get crd cyberdesks.cyberdesk.io`) before creating instances.

Create a sample Cyberdesk resource:

```bash
kubectl apply -f ./kubernetes/cyberdesk-cr.yaml
kubectl get cyberdesks
```

Check the status of the created Cyberdesk:

```bash
kubectl describe cyberdesk sample-instance
```

Verify that a VM was created for this Cyberdesk:

```bash
kubectl get virtualmachines | grep cyberdesk-sample-instance
```

## Cleanup

To delete all resources created by this deployment:

1. Delete any active Cyberdesk instances:

```bash
kubectl delete cyberdesks --all --all-namespaces
```

2. Delete the operator trigger instance:

```bash
kubectl delete -f ./kubernetes/start-cyberdesk-operator-cr.yaml
```

3. Delete the Cyberdesk operator deployment and its associated resources (Namespace, RBAC, Deployment, ConfigMap, Trigger CRD):

```bash
kubectl delete -f ./kubernetes/cyberdesk-operator.yaml
```

4. Delete the Supabase Secret:

```bash
# Note: If you applied the secret manually, delete it manually too.
kubectl delete secret supabase-credentials -n cyberdesk-system
# Alternatively, if you applied it from the file:
# kubectl delete -f ./kubernetes/cyberdesk-secret.yaml 
```

5. Delete the dynamically created Cyberdesk CRD:

```bash
kubectl delete crd cyberdesks.cyberdesk.io
```

6. Delete KubeVirt resources:

```bash
kubectl delete -f ./kubernetes/kubevirt-cr.yaml
kubectl delete -f ./kubernetes/kubevirt-operator.yaml
```

7. Destroy the infrastructure:

```bash
cd ./terraform
terraform destroy -auto-approve
```