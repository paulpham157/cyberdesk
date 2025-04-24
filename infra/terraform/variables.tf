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

variable "aks_default_node_pool_vm_size" {
  description = "The VM size for the default AKS node pool."
  type        = string
  default     = "Standard_D8ds_v5" # Keeping the original as default
}

variable "aks_default_node_pool_min_count" {
  description = "The minimum number of nodes for the default AKS node pool autoscaler."
  type        = number
  default     = 1
}

variable "aks_default_node_pool_max_count" {
  description = "The maximum number of nodes for the default AKS node pool autoscaler."
  type        = number
  default     = 2
}