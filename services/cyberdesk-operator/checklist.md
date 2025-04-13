# Cyberdesk Operator Implementation Checklist

## Overview

The Cyberdesk Operator is a Kubernetes Custom Resource Operator that monitors and manages Cyberdesk resources in a Kubernetes cluster. It's responsible for automatically provisioning and lifecycle management of KubeVirt VirtualMachine resources based on Cyberdesk Custom Resource definitions. The operator handles VM creation, status tracking, timeout enforcement, and cleanup of resources, providing an abstraction layer that simplifies VM provisioning for users while ensuring proper resource management within the cluster.

## Project Setup

- [x] Create basic project structure
- [x] Set up Python virtual environment
- [x] Create requirements.txt with kopf and kubernetes dependencies
- [x] Create a Dockerfile for the operator
- [x] Create a deployment manifest for Kubernetes

## Core Operator Logic

- [x] Create handlers/controller.py for main operator logic
- [x] Implement Kopf watches for Cyberdesk creation
- [x] Implement Kopf watches for VirtualMachineInstance updates
- [x] Implement VM creation logic when a new Cyberdesk is created
- [x] Implement listener for VMI status updates, to perform various actions
- [x] Implement Kopf watches for Cyberdesk deletion, triggering the deletion of the underlaying VirtualMachineInstance
- [x] Implement timeout mechanism based on timeoutMs, shutting down the underlaying VirtualMachineInstance if it's running longer than the timeout
- [x] Ensure event handler idempotency for all handlers by checking the current resource state (using resourceVersion or status fields) to guarantee that duplicate events don't trigger duplicate operations.

## Leader Election and High Availability
- [x] Configure leader election in your operator to designate one active replica for processing state-changing events, while others are available for failover.
- [x] Document the expected behavior and failover process to ensure consistent operation in a multi-replica environment.

## Secrets 
- [x] In production, create Kubernetes Secret resources and inject them into your Pods via environment variables or volumes.
- [x] Use python-dotenv only for local development; in production rely entirely on Kubernetes-managed secrets.

## Error Handling and Lifecycle Management

- [x] Ensure proper error handling and retries
- [x] Add graceful cleanup logic for terminated instances
- [x] Implement VM deletion on Cyberdesk deletion
- [x] Add finalizers to ensure clean resource deletion

## Documentation

- [x] Add README.md with operator overview and K8s installation instructions.
- [x] Document troubleshooting steps, including:
  - [x] How idempotency is ensured
  - [x] How leader election is configured and behaves
  - [x] How secrets are managed in different environments

## CI/CD Pipeline

- [x] Add workflow for building and pushing Docker image

## Security

- [x] Ensure secure container settings (non-root user, readonly filesystem where possible)
- [x] Review RBAC policies for accessing secrets and managing resources

## Monitoring & Observability

- [x] Set up logging and metrics (consider integrating with Prometheus and Grafana)
- [x] Document key operational alerts and troubleshooting tips
