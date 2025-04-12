# Cyberdesk Architecture

## System Overview

This document outlines the architecture for a scalable cloud desktop platform that allows users to create and interact with isolated virtual machine environments. The system is designed to support thousands of concurrent VMs while maintaining security, performance, and ease of use.

## Architecture Components

```
┌───────────────┐     ┌───────────────┐     ┌─────────────────────────────────────────┐
│   Frontend    │     │ API Backend   │     │          Kubernetes Cluster             │
│  (Next.js on  │───▶│  (Node.js      │───▶│┌───────────┐┌──────────┐┌─────────────┐ │
│    Vercel)    │     │   on          │     ││  Gateway  ││ Instance ││  Kubevirt   │ │
└───────────────┘     │   Fly.io)     │     ││  Service  ││ Operator ││    VMs      │ │
                      └───────────────┘     │└───────────┘└──────────┘└─────────────┘ │
                                            └─────────────────────────────────────────┘
```

### 1. Frontend (Next.js on Vercel)
- Landing page
- Docs
- User authentication and account management
- Desktop creation and management interface
- Playground

### 2. API Backend (Node.js on Fly.io)
- RESTful API for desktop management and control (makes calls to Gateway Service)
- API key auth provided by Unkey
- Billing with Stripe
- Usage tracking and limit enforcing
- Event logging and analytics with Posthog

### 3. Kubernetes Cluster (AKS with Kubevirt)

- **Gateway Service**
  - Single entry point into the cluster
  - CRUD endpoints for CyberdeskInstance K8s resources
  - Endpoint to route commands to running VMs
  - Exposed for public access from the FastAPI backend, via K8s External Service

- **Instance Operator**
  - Listens to changes to CyberdeskInstances and does all relevant business logic to create the underlying VirtualMachineInstance using Kubevirt
  - Enforce timeout and compute hour credits
  - Apply snapshots, etc
  
- **Kubevirt VMs**
  - Isolated sandbox environments
  - Each running the custom execD service, which accepts requests from Gateway Service
  - Network isolation via Kubernetes networking

## Other Key Components

### 1. execD Service (Inside Each VM)

#### Implementation
- Custom lightweight HTTP service
- Written in Node.js
- Runs on private-internal-ip:port inside each VM, only Gateway Service can access
- Starts automatically when VM boots

#### Features
- Command execution
- File system operations

### 2. CyberdeskInstance K8s Custom Resource Definition

#### Implementation
- YAML file that defines a desktop instance and it's parameters
- Instances of this custom resource are listened to by Instance Operator

### 3. JS / Python SDKs

#### Implementation
- Automatically generated from OpenAPI spec

### 4. Supabase Database
- Handles all database functionalities, authentication

## Scaling Considerations

### Horizontal Scaling
- Frontend: Automatic scaling via Vercel
- API Backend: Auto-scaling on Fly.io
- Gateway Service: Kubernetes HPA up to 20+ pods
- Kubernetes Cluster: Multiple node pools, auto-scaling

