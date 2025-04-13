# Cyberdesk Operator: Troubleshooting Guide

This document provides detailed information about the Cyberdesk Operator implementation, focusing on key aspects that are important for troubleshooting and maintenance.

## Idempotency

The Cyberdesk Operator ensures that all operations are idempotent, meaning that they can be safely retried without causing duplicate or inconsistent states.

### How Idempotency is Implemented

1. **Resource Version Tracking**: 
   - The operator tracks which resource versions it has already processed using annotations on the Cyberdesk resources.
   - Each handler adds its identifier and the resource version it processed to these annotations.
   - Before processing a resource, handlers check if they've already processed the current resource version.

2. **Existence Checks**: 
   - Before creating resources, the operator checks if they already exist.
   - For example, before creating a VM, the operator checks if a VM with the same name already exists.

3. **Annotation-Based Tracking**:
   - Two key annotations track handler processing:
     - `cyberdesk.io/processed-by`: Lists handlers that have processed this resource
     - `cyberdesk.io/processed-versions`: Lists handler:resourceVersion pairs that have been processed

4. **Helper Functions**:
   - `is_handler_already_processed()`: Checks if a handler has already processed a resource version
   - `mark_handler_processed()`: Marks a resource as processed by a handler

### Troubleshooting Idempotency Issues

If you suspect that the operator is not correctly handling idempotency:

1. Check the annotations on the Cyberdesk resource:
   ```bash
   kubectl get cyberdesks <name> -o jsonpath='{.metadata.annotations}'
   ```

2. Verify the logs to see if handlers are skipping already processed resources:
   ```bash
   kubectl logs -n cyberdesk-system -l app=cyberdesk-operator | grep "already processed"
   ```

3. If resources are being created multiple times, check if the annotations are being properly updated.

## Leader Election

To ensure that only one instance of the operator processes resources in a multi-replica deployment, the operator uses Kopf's built-in leader election mechanism.

### How Leader Election is Configured

1. **Kopf Peering Resource**:
   - The operator uses a Kubernetes custom resource called a "Peering" for leader election.
   - The peering resource name is set via the `KOPF_PEERING` environment variable (defaults to "cyberdesk-operator").

2. **Leader ID**:
   - Each operator instance has a unique leader ID, by default using the Pod name.
   - If POD_NAME is not available, it falls back to using the hostname.

3. **Priority**:
   - All instances have the same priority (0) by default.
   - The instance with the lowest priority number becomes the leader.

4. **Startup Configuration**:
   - Leader election is configured in `main.py` through the `kopf.run()` parameters:
     - `peering`: Name of the peering resource
     - `id`: Unique ID for this operator instance
     - `priority`: Priority in leader election

### Failover Process

1. Kopf periodically updates a heartbeat in the peering resource.
2. If the leader fails to update its heartbeat, Kopf automatically promotes another instance to leader.
3. The new leader will resume processing events.
4. During failover, there might be a brief period (typically less than 30 seconds) where no instance is processing events.

### Troubleshooting Leader Election

1. Check the current leader:
   ```bash
   kubectl get kopfpeering cyberdesk-operator -o yaml
   ```

2. Check operator logs to see leader election activity:
   ```bash
   kubectl logs -n cyberdesk-system -l app=cyberdesk-operator | grep "leader"
   ```

3. If no instance becomes the leader, ensure the operator has permissions to create and update the peering resource.

## Secrets Management

The Cyberdesk Operator handles secrets differently in development and production environments.

### Development Environment

In the development environment:

1. **Dotenv**:
   - The operator uses `python-dotenv` to load environment variables from a `.env` file.
   - This is only intended for local development and testing.

2. **Local Configuration**:
   - Secrets such as API keys or credentials should be stored in a `.env` file that is not committed to version control.
   - The `.env.example` file provides a template for required variables.

### Production Environment

In the production environment:

1. **Kubernetes Secrets**:
   - All secrets are stored as Kubernetes Secret resources.
   - Secrets are mounted as either:
     - Environment variables using `envFrom` in the Deployment spec
     - Volume mounts for sensitive files (like certificates)

2. **No Dotenv Usage**:
   - The `python-dotenv` library is still imported but has no effect if `.env` is not present.
   - All configuration comes from the container environment or mounted files.

3. **Secret References**:
   - The operator's Deployment manifest references Kubernetes Secrets for sensitive data.
   - Example:
     ```yaml
     envFrom:
     - secretRef:
         name: cyberdesk-operator-secrets
     ```

### Secrets Used by the Operator

The operator may use the following types of secrets:

1. **API Credentials**: For accessing external services (if applicable)
2. **TLS Certificates**: For secure communication (if applicable)
3. **SSH Keys**: For VM access (if applicable)

### Troubleshooting Secrets Issues

1. Check if the required secrets exist:
   ```bash
   kubectl get secrets -n cyberdesk-system
   ```

2. Verify the operator has permissions to access secrets:
   ```bash
   kubectl auth can-i get secrets -n cyberdesk-system --as=system:serviceaccount:cyberdesk-system:cyberdesk-operator
   ```

3. Check if secrets are correctly mounted:
   ```bash
   kubectl exec -n cyberdesk-system deploy/cyberdesk-operator -- env | grep SENSITIVE_VAR
   ```

## Monitoring and Metrics

The operator exposes Prometheus metrics on port 8081:

1. **Available Metrics**:
   - `cyberdesk_vm_created_total`: Counter of VMs created
   - `cyberdesk_vm_deleted_total`: Counter of VMs deleted
   - `cyberdesk_vm_timeout_total`: Counter of VMs that timed out
   - `cyberdesk_active_vm_count`: Gauge showing current active VMs
   - `cyberdesk_operation_duration_seconds`: Histogram of operation durations

2. **Accessing Metrics**:
   ```bash
   kubectl port-forward -n cyberdesk-system deploy/cyberdesk-operator 8081:8081
   curl localhost:8081
   ``` 