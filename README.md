# KubeVirt on AKS Deployment

This repository contains Terraform configurations and Kubernetes manifests to deploy KubeVirt on Azure Kubernetes Service (AKS).

## Prerequisites

- [Terraform](https://www.terraform.io/downloads.html) installed
- [Azure CLI](https://docs.microsoft.com/en-us/cli/azure/install-azure-cli) installed
- Azure subscription with appropriate permissions
- [kubectl](https://kubernetes.io/docs/tasks/tools/) installed
- [kubelogin](https://github.com/Azure/kubelogin) installed (for Azure AKS authentication)
- [virtctl](https://kubevirt.io/user-guide/operations/virtctl_client_tool/) KubeVirt client utility installed

## Deployment Steps

### 1. Infrastructure Deployment with Terraform

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
kubectl apply -f kubevirt/kubevirt-operator.yaml
```

Apply the KubeVirt custom resource:

```bash
kubectl apply -f kubevirt/kubevirt-cr.yaml
```

### 4. Prepare SSH Keys and VM User Data

Change to the Kubevirt directory:

```bash
cd ./kubevirt
```

1. Generate an SSH key pair (if you don't already have one):

   **MacOS/Linux:**
   ```bash
   mkdir -p ~/.ssh
   ssh-keygen -t rsa -b 4096 -f ~/.ssh/cyberdesk_mvp_3_id_rsa
   ```

   **Windows PowerShell:**
   ```powershell
   # Ensure .ssh directory exists
   if (-not (Test-Path -Path "$env:USERPROFILE\.ssh")) {
       New-Item -ItemType Directory -Path "$env:USERPROFILE\.ssh"
   }
   ssh-keygen -t rsa -b 4096 -f "$env:USERPROFILE\.ssh\cyberdesk_mvp_3_id_rsa"
   ```

2. Create a user-data.yaml file from the template and add your public key (make sure user-data.yaml has the "SSH_PUBLIC_KEY_HERE" placeholder for the replacement to properly work):

   **MacOS/Linux:**
   ```bash
   cp ./user-data.template.yaml ./user-data.yaml
   # Replace the placeholder with your public key
   PUBLIC_KEY=$(cat ~/.ssh/cyberdesk_mvp_3_id_rsa.pub)
   sed -i "s|SSH_PUBLIC_KEY_HERE|$PUBLIC_KEY|g" ./user-data.yaml
   ```

   **Windows PowerShell:**
   ```powershell
   Copy-Item -Path ./user-data.template.yaml -Destination ./user-data.yaml
   # Replace the placeholder with your public key
   $PUBLIC_KEY=Get-Content -Raw "$env:USERPROFILE\.ssh\cyberdesk_mvp_3_id_rsa.pub"
   (Get-Content ./user-data.yaml) -replace 'SSH_PUBLIC_KEY_HERE', $PUBLIC_KEY | Set-Content ./user-data.yaml
   ```

3. Convert the user data to base64 and save it to a file:

   **MacOS/Linux:**
   ```bash
   cat ./user-data.yaml | base64 -w 0 > ./user-data-base64.txt
   ```
   
   **Windows PowerShell:**
   ```powershell
   [Convert]::ToBase64String([System.Text.Encoding]::UTF8.GetBytes((Get-Content -Raw ./user-data.yaml))) | Out-File -NoNewline ./user-data-base64.txt
   ```

4. Deploy the VM with the user data injected at runtime (without modifying the original file):

   **MacOS/Linux:**
   ```bash
   # Read the base64 encoded user data
   USER_DATA_BASE64=$(cat ./user-data-base64.txt)
   
   # Apply the VM definition with the base64 user data injected at runtime
   cat ./vm.yaml | sed "s|\${user_data_base64}|$USER_DATA_BASE64|g" | kubectl apply -f -
   ```
   
   **Windows PowerShell:**
   ```powershell
   # Read the base64 encoded user data
   $USER_DATA_BASE64=Get-Content -Raw ./user-data-base64.txt
   
   # Apply the VM definition with the base64 user data injected at runtime
   Get-Content ./vm.yaml | ForEach-Object { $_ -replace '\$\{user_data_base64\}', $USER_DATA_BASE64 } | kubectl apply -f -
   ```

### 5. Register the CyberdeskInstance Custom Resource Definition

Apply the CyberdeskInstance CRD to your cluster:

```bash
kubectl apply -f ./cyberdesk-instance-crd.yaml
```

Verify that the CRD was registered successfully:

```bash
kubectl get crd cyberdeskinstances.cyberdesk.io
```

## Verification

To verify your deployment, you can check the status of KubeVirt components:

```bash
kubectl get pods -n kubevirt
```

You can also verify that the CyberdeskInstance CRD is ready:

```bash
kubectl api-resources | grep cyberdesk
```

## Initial Testing (Optional)

You can test the CRD by creating a sample CyberdeskInstance:

```bash
kubectl apply -f kubevirt/cyberdesk-instance-cr.yaml
kubectl get cyberdeskinstances
```

## Cleanup

To delete all resources created by this deployment:

```bash
terraform destroy -auto-approve
```

## Gut Check (Optional)

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
kubectl apply -f ./testvm-service.yaml
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
rm ./user-data.yaml
rm ./user-data-base64.txt
```
