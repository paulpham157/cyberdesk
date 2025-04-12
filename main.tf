#########################################
# main.tf
#########################################

terraform {
  required_version = ">= 1.11.3"

  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 4.26.0"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.36.0"
    }
    helm = {
      source  = "hashicorp/helm"
      version = "~> 2.11.0"
    }
    kubectl = {
      source  = "gavinbunney/kubectl"
      version = "~> 1.19.0"
    }
  }
}

#############################
# Providers Configuration
#############################

provider "azurerm" {
  features {}
  subscription_id = var.subscription_id
}

provider "kubernetes" {
  host                   = azurerm_kubernetes_cluster.aks.kube_config.0.host
  client_certificate     = base64decode(azurerm_kubernetes_cluster.aks.kube_config.0.client_certificate)
  client_key             = base64decode(azurerm_kubernetes_cluster.aks.kube_config.0.client_key)
  cluster_ca_certificate = base64decode(azurerm_kubernetes_cluster.aks.kube_config.0.cluster_ca_certificate)
}

provider "helm" {
  kubernetes {
    host                   = azurerm_kubernetes_cluster.aks.kube_config.0.host
    client_certificate     = base64decode(azurerm_kubernetes_cluster.aks.kube_config.0.client_certificate)
    client_key             = base64decode(azurerm_kubernetes_cluster.aks.kube_config.0.client_key)
    cluster_ca_certificate = base64decode(azurerm_kubernetes_cluster.aks.kube_config.0.cluster_ca_certificate)
  }
}

provider "kubectl" {
  host                   = azurerm_kubernetes_cluster.aks.kube_config.0.host
  client_certificate     = base64decode(azurerm_kubernetes_cluster.aks.kube_config.0.client_certificate)
  client_key             = base64decode(azurerm_kubernetes_cluster.aks.kube_config.0.client_key)
  cluster_ca_certificate = base64decode(azurerm_kubernetes_cluster.aks.kube_config.0.cluster_ca_certificate)
  load_config_file       = false
}

#############################
# Networking & IAM Setup
#############################

# Create a resource group.
resource "azurerm_resource_group" "rg" {
  name     = var.resource_group_name
  location = var.location
}

# Create a Virtual Network.
resource "azurerm_virtual_network" "vnet" {
  name                = "vnet-kubevirt-demo"
  address_space       = ["10.0.0.0/16"]
  location            = azurerm_resource_group.rg.location
  resource_group_name = azurerm_resource_group.rg.name
}

# Create a subnet for the AKS cluster.
resource "azurerm_subnet" "aks" {
  name                 = "subnet-aks"
  resource_group_name  = azurerm_resource_group.rg.name
  virtual_network_name = azurerm_virtual_network.vnet.name
  address_prefixes     = ["10.0.1.0/24"]
}

# Create a Log Analytics workspace for monitoring
resource "azurerm_log_analytics_workspace" "law" {
  name                = "law-${var.aks_cluster_name}"
  location            = azurerm_resource_group.rg.location
  resource_group_name = azurerm_resource_group.rg.name
  sku                 = "PerGB2018"
  retention_in_days   = 30
}

# Provision an AKS cluster with networking pointing to the subnet.
resource "azurerm_kubernetes_cluster" "aks" {
  name                = var.aks_cluster_name
  location            = azurerm_resource_group.rg.location
  resource_group_name = azurerm_resource_group.rg.name
  dns_prefix          = var.aks_cluster_name

  default_node_pool {
    name                = "default"
    node_count          = 1
    vm_size             = "Standard_D8ds_v5"
    auto_scaling_enabled = true
    min_count           = 1
    max_count           = 2
    vnet_subnet_id      = azurerm_subnet.aks.id
  }

  identity {
    type = "SystemAssigned"
  }

  network_profile {
    network_plugin     = "azure"
    network_policy     = "azure"
    service_cidr       = "10.2.0.0/16"
    dns_service_ip     = "10.2.0.10"
  }

  oms_agent {
    log_analytics_workspace_id = azurerm_log_analytics_workspace.law.id
  }
}

# Grant the AKS managed identity "Network Contributor" role on the subnet.
resource "azurerm_role_assignment" "aks_subnet_role" {
  scope                = azurerm_subnet.aks.id
  role_definition_name = "Network Contributor"
  principal_id         = azurerm_kubernetes_cluster.aks.identity[0].principal_id
}

#############################
# Kubeconfig Output for Local Use
#############################

# This writes out the cluster's kubeconfig to a local file.
resource "local_file" "kubeconfig" {
  content  = azurerm_kubernetes_cluster.aks.kube_config_raw
  filename = "${path.module}/kubeconfig.yaml"
}

#############################
# Deploy KubeVirt via Kubernetes Manifests
#############################

# Apply the KubeVirt operator
resource "kubectl_manifest" "kubevirt_operator" {
  yaml_body = file("${path.module}/kubevirt/kubevirt-operator.yaml")
}

# Apply the KubeVirt CR
resource "kubernetes_manifest" "kubevirt_cr" {
  manifest = yamldecode(file("${path.module}/kubevirt/kubevirt-cr.yaml"))

  depends_on = [kubectl_manifest.kubevirt_operator]
}

#############################
# VirtualMachine Resource via Kubernetes Manifest
#############################

# Prepare cloud-init and base64 encoding using local values.
locals {
  # The cloud-init configuration to set up the VM.
  user_data = <<EOF
#cloud-config
users:
  - name: ${var.username}
    lock_passwd: false
    passwd: ${var.password}
    shell: /bin/bash
ssh_pwauth: true
EOF

  # Base64-encode the cloud-init script.
  user_data_base64 = base64encode(local.user_data)
  
  # Prepare the VM manifest with the replaced cloud-init data
  vm_yaml = replace(file("${path.module}/kubevirt/vm.yaml"), "${user_data_base64}", local.user_data_base64)
}

# Manage the KubeVirt VirtualMachine resource using kubectl_manifest
resource "kubectl_manifest" "vm_manifest" {
  yaml_body = local.vm_yaml

  depends_on = [kubectl_manifest.kubevirt_cr]
}