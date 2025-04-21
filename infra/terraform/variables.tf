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