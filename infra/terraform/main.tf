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
  }
}

#############################
# Providers Configuration
#############################

provider "azurerm" {
  features {}
  subscription_id = var.subscription_id
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

# Create a Network Security Group for the AKS subnet.
resource "azurerm_network_security_group" "aks_nsg" {
  name                = "nsg-aks-subnet"
  location            = azurerm_resource_group.rg.location
  resource_group_name = azurerm_resource_group.rg.name
}

# Add a rule to allow outbound internet traffic.
resource "azurerm_network_security_rule" "allow_outbound" {
  name                        = "AllowOutboundInternet"
  priority                    = 100 # Lower number = higher priority
  direction                   = "Outbound"
  access                      = "Allow"
  protocol                    = "*" # Allows TCP, UDP, ICMP etc.
  source_port_range           = "*"
  destination_port_range      = "*"
  source_address_prefix       = "VirtualNetwork" # Traffic originating from within the VNet
  destination_address_prefix  = "Internet"       # Destination is the public internet
  resource_group_name         = azurerm_resource_group.rg.name
  network_security_group_name = azurerm_network_security_group.aks_nsg.name
}

# Add a rule to allow inbound HTTP traffic from specific sources.
resource "azurerm_network_security_rule" "allow_inbound_http" {
  name                        = "AllowInboundHttpFromTrusted"
  priority                    = 110 # Needs a different priority than the outbound rule
  direction                   = "Inbound"
  access                      = "Allow"
  protocol                    = "Tcp"
  source_port_range           = "*"
  destination_port_range      = "80" # Allow traffic to port 80
  source_address_prefixes     = concat(var.developer_api_ips, var.developer_vpn_ips) # Allow traffic from Developer API and Developer VPN
  destination_address_prefix  = "*"       # Allow traffic to any destination within the NSG scope (our subnet)
  resource_group_name         = azurerm_resource_group.rg.name
  network_security_group_name = azurerm_network_security_group.aks_nsg.name
}

# Add a rule to allow inbound HTTPS traffic from specific sources.
resource "azurerm_network_security_rule" "allow_inbound_https" {
  name                        = "AllowInboundHttpsFromTrusted"
  priority                    = 120 # Needs a different priority than the other rules
  direction                   = "Inbound"
  access                      = "Allow"
  protocol                    = "Tcp"
  source_port_range           = "*"
  destination_port_range      = "443" # Allow traffic to port 443
  source_address_prefixes     = concat(var.developer_api_ips, var.developer_vpn_ips) # Allow traffic from Developer API and Developer VPN
  destination_address_prefix  = "*"       # Allow traffic to any destination within the NSG scope (our subnet)
  resource_group_name         = azurerm_resource_group.rg.name
  network_security_group_name = azurerm_network_security_group.aks_nsg.name
}

# Associate the NSG with the AKS subnet.
resource "azurerm_subnet_network_security_group_association" "aks_nsg_assoc" {
  subnet_id                 = azurerm_subnet.aks.id
  network_security_group_id = azurerm_network_security_group.aks_nsg.id
}

# Provision an AKS cluster with networking pointing to the subnet.
resource "azurerm_kubernetes_cluster" "aks" {
  name                = var.aks_cluster_name
  location            = azurerm_resource_group.rg.location
  resource_group_name = azurerm_resource_group.rg.name
  dns_prefix          = var.aks_cluster_name

  default_node_pool {
    name                = "default"
    node_count          = 1 # Note: node_count is often managed by autoscaler if enabled. Consider removing if not needed or set to min_count.
    vm_size             = var.aks_default_node_pool_vm_size
    temporary_name_for_rotation = "tempnodepool"
    auto_scaling_enabled = true
    min_count           = var.aks_default_node_pool_min_count
    max_count           = var.aks_default_node_pool_max_count
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
}

# Grant the AKS managed identity "Network Contributor" role on the subnet.
resource "azurerm_role_assignment" "aks_subnet_role" {
  scope                = azurerm_subnet.aks.id
  role_definition_name = "Network Contributor"
  principal_id         = azurerm_kubernetes_cluster.aks.identity[0].principal_id
}

# Grant the AKS managed identity permissions to manage route tables if using Azure CNI
# Required for Azure CNI with network policies or custom routes
resource "azurerm_role_assignment" "aks_routetable_role" {
  scope                = azurerm_resource_group.rg.id # Assign at the resource group level
  role_definition_name = "Network Contributor"        # Or a more specific custom role if needed
  principal_id         = azurerm_kubernetes_cluster.aks.identity[0].principal_id
  # Depends on the VNet being created first
  depends_on = [azurerm_virtual_network.vnet]
}