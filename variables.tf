variable "subscription_id" {
  description = "The Azure Subscription ID where resources will be created."
  type        = string
}

variable "resource_group_name" {
  description = "The name of the resource group in which to create resources."
  type        = string
}

variable "location" {
  description = "Azure region for the resources."
  type        = string
}

variable "aks_cluster_name" {
  description = "The name to use for the AKS cluster."
  type        = string
}

variable "username" {
  description = "Username for the VM's cloud-init configuration"
  type        = string
}

variable "password" {
  description = "Password for the VM (should be provided via environment variable or secure secret management)"
  type        = string
  sensitive   = true
} 