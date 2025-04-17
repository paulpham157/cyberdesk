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

```bash
az aks get-credentials --resource-group rg-p-scu-kubevirt --name aks-p-scu-kubevirt
```

### 3. Deploy KubeVirt

Apply the KubeVirt operator:

```bash
kubectl apply -f ../kubevirt/kubevirt-operator.yaml
```

Apply the KubeVirt custom resource:

```bash
kubectl apply -f ../kubevirt/kubevirt-cr.yaml
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

**Important:** After building and pushing, you **must update** the `image:` field in `../infra/kubevirt/cyberdesk-operator.yaml` to reference the **specific tag** you just used (e.g., `image: cyberdesk-operator:v0.1.0` or `image: your-registry.io/cyberdesk-operator:v0.1.0`).

```bash
# Navigate back to the infra directory
cd ../../infra
```

#### 4.2 Deploy the Operator and Core Resources

This single manifest contains the Namespace, ServiceAccount, RBAC rules, the Deployment for the operator, the ConfigMap for the VM template, and the trigger CRD (`StartCyberdeskOperator`).

Make sure the `image:` tag in this file matches the image you built and pushed in the previous step.

```bash
kubectl apply -f ./kubevirt/cyberdesk-operator.yaml
```

Verify the operator deployment starts:

```bash
kubectl get deployment -n cyberdesk-system cyberdesk-operator
# Wait for AVAILABLE replicas to be 1
kubectl get pods -n cyberdesk-system -l app=cyberdesk-operator
```

#### 4.3 Trigger Operator Setup

Apply the `StartCyberdeskOperator` custom resource. This signals the running operator to perform its initial setup, primarily creating the `Cyberdesk` CRD.

```bash
kubectl apply -f ./kubevirt/start-cyberdesk-operator-cr.yaml
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
kubectl apply -f ./kubevirt/cyberdesk-cr.yaml
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
kubectl delete -f ./kubevirt/start-cyberdesk-operator-cr.yaml
```

3. Delete the Cyberdesk operator deployment and its associated resources (Namespace, RBAC, Deployment, ConfigMap, Trigger CRD):

```bash
kubectl delete -f ./kubevirt/cyberdesk-operator.yaml
```

4. Delete the dynamically created Cyberdesk CRD:

```bash
kubectl delete crd cyberdesks.cyberdesk.io
```

5. Delete KubeVirt resources:

```bash
kubectl delete -f ./kubevirt/kubevirt-cr.yaml
kubectl delete -f ./kubevirt/kubevirt-operator.yaml
```

6. Destroy the infrastructure:

```bash
cd ./terraform
terraform destroy -auto-approve
```

## Gut Check (Optional)

First, ensure you're in the `/infra` directory:

```bash
cd /path/to/project/infra
```

Use these steps to manually verify that VMs can be provisioned and accessed correctly.

### 1. Manage the Virtual Machine

Start, stop, or check your virtual machine:

```bash
# Start VM
virtctl start testvm

# Stop VM
virtctl stop testvm
```

### 2. SSH Into the Virtual Machine

Apply the LoadBalancer External Service
```bash
kubectl apply -f ./kubevirt/testvm-service.yaml
```

Get the external IP of the LoadBalancer service (this may take a minute to provision):

```bash
kubectl get svc testvm-service
```

SSH into the VM using the private key:

**MacOS/Linux:**
```bash
ssh -i ~/.ssh/cyberdesk_mvp_3_id_rsa kubevirt-admin@EXTERNAL-IP
```

**Windows PowerShell:**
```powershell
ssh -i "$env:USERPROFILE\.ssh\cyberdesk_mvp_3_id_rsa" kubevirt-admin@EXTERNAL-IP
```

Note: Replace `EXTERNAL-IP` with the external IP address shown in the output of the `kubectl get svc` command.

### 3. Cleaning Up After Gut Check

To delete the test virtual machine and service after verification:

```bash
# Delete the VM service
kubectl delete svc testvm-service

# Delete the VM
kubectl delete vm testvm
```

Delete user-data.yaml and user-data-base64.txt:

```bash
rm ./kubevirt/user-data.yaml
rm ./kubevirt/user-data-base64.txt
```