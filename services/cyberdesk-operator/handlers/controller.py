import kopf
import kubernetes
import logging
import os
import yaml
import string
import time
from datetime import datetime, timedelta
from typing import Dict, Any
from pathlib import Path

# Configure the Kubernetes client
# Prioritize kubeconfig for local development, then fall back to incluster config
try:
    kubernetes.config.load_kube_config()
    logging.info("Loaded Kubernetes configuration from kubeconfig.")
except kubernetes.config.config_exception.ConfigException:
    try:
        kubernetes.config.load_incluster_config()
        logging.info("Loaded Kubernetes configuration from in-cluster config.")
    except kubernetes.config.config_exception.ConfigException as e:
        logging.critical(f"Could not load Kubernetes configuration from kubeconfig or in-cluster config: {e}")
        raise kopf.PermanentError("Failed to load Kubernetes configuration.")

# Define API clients
core_v1_api = kubernetes.client.CoreV1Api()
custom_objects_api = kubernetes.client.CustomObjectsApi()
apiextensions_v1_api = kubernetes.client.ApiextensionsV1Api()

# Resource definitions
CYBERDESK_GROUP = "cyberdesk.io"
CYBERDESK_VERSION = "v1alpha1"
CYBERDESK_PLURAL = "cyberdesks"

KUBEVIRT_GROUP = "kubevirt.io"
KUBEVIRT_VERSION = "v1"
KUBEVIRT_NAMESPACE = "kubevirt"
KUBEVIRT_VM_PLURAL = "virtualmachines"
KUBEVIRT_VMI_PLURAL = "virtualmachineinstances"

# Trigger Resource Definition
START_OPERATOR_PLURAL = "startcyberdeskoperators"

# Constants
MANAGED_BY = "cyberdesk-operator"
CYBERDESK_NAMESPACE = "cyberdesk-system"

# Helper function for idempotency checks
def is_handler_already_processed(meta, handler_id, resource_version=None):
    """
    Check if a handler has already processed this resource version.
    This helps ensure idempotency by avoiding duplicate operations.
    
    Args:
        meta: Resource metadata
        handler_id: String identifier for the handler
        resource_version: Optional specific resource version to check
        
    Returns:
        bool: True if already processed, False otherwise
    """
    annotations = meta.get('annotations', {})
    processed_by = annotations.get(f'{CYBERDESK_GROUP}/processed-by', '')
    processed_versions = annotations.get(f'{CYBERDESK_GROUP}/processed-versions', '')
    
    # If no resource version specified, check if handler is in the processed-by list
    if not resource_version:
        return handler_id in processed_by.split(',') if processed_by else False
    
    # If resource version specified, check if handler+version is in the processed-versions list
    handler_version = f"{handler_id}:{resource_version}"
    return handler_version in processed_versions.split(',') if processed_versions else False

def mark_handler_processed(api_instance, resource, handler_id, resource_version=None):
    """
    Mark that a handler has processed this resource version.
    
    Args:
        api_instance: Kubernetes API instance
        resource: Resource dict with metadata
        handler_id: String identifier for the handler
        resource_version: Optional specific resource version that was processed
    """
    meta = resource.get('metadata', {})
    if not meta:
        logging.warning(f"Resource missing metadata, cannot mark handler {handler_id}. Resource: {resource}")
        return

    annotations = meta.get('annotations', {})
    original_annotations = meta.get('annotations', {}).copy()

    # Mark the handler as having processed this resource
    processed_by = annotations.get(f'{CYBERDESK_GROUP}/processed-by', '')
    handlers = processed_by.split(',') if processed_by else []
    if handler_id not in handlers:
        handlers.append(handler_id)
        annotations[f'{CYBERDESK_GROUP}/processed-by'] = ','.join(handlers)
    
    # If resource version provided, mark the handler+version as processed
    if resource_version:
        processed_versions = annotations.get(f'{CYBERDESK_GROUP}/processed-versions', '')
        handler_versions = processed_versions.split(',') if processed_versions else []
        handler_version = f"{handler_id}:{resource_version}"
        if handler_version not in handler_versions:
            handler_versions.append(handler_version)
            annotations[f'{CYBERDESK_GROUP}/processed-versions'] = ','.join(handler_versions)
    
    # Only patch if annotations actually changed
    if annotations != original_annotations:
        # Apply the annotation update
        api_version = resource.get('apiVersion')
        kind = resource.get('kind')
        if not api_version or not kind:
            logging.warning(f"Resource missing apiVersion or kind, cannot patch handler {handler_id}. Resource: {resource}")
            return

        try:
            group, version = api_version.split('/')
        except ValueError:
            logging.warning(f"Invalid apiVersion format '{api_version}', cannot patch handler {handler_id}. Resource: {resource}")
            return
            
        plural = kind.lower() + 's'  # Simple pluralization

        namespace = meta.get('namespace')
        name = meta.get('name')
        if not namespace or not name:
            logging.warning(f"Resource missing namespace or name in metadata, cannot patch handler {handler_id}. Metadata: {meta}")
            return

        try:
            api_instance.patch_namespaced_custom_object(
                group=group,
                version=version,
                namespace=namespace,
                plural=plural,
                name=name,
                body={"metadata": {"annotations": annotations}}
            )
        except Exception as e:
            logging.warning(f"Failed to mark handler {handler_id} as processed for {name} in {namespace}: {e}")

# Path to VM template
# Check different locations based on running environment (container vs dev)
VM_TEMPLATE_PATHS = [
    '/app/kubevirt-vm-cr.yaml',  # Mounted in container via ConfigMap
    os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'tests', 'test-kubevirt-vm-cr.yaml')), # For local testing via KopfRunner
]

def load_vm_template():
    """Load VM template from file"""
    template_found = False
    template_content = None
    
    for template_path in VM_TEMPLATE_PATHS:
        try:
            if os.path.exists(template_path):
                with open(template_path, 'r') as f:
                    template_content = f.read()
                    template_found = True
                    logging.info(f"Loaded VM template from {template_path}")
                    break
        except Exception as e:
            logging.warning(f"Failed to read template from {template_path}: {e}")
    
    if not template_found:
        logging.critical("VM template file not found, exiting")
        raise kopf.PermanentError("VM template file not found, exiting")
    
    return template_content

# Define the Cyberdesk CRD manifest in code
CYBERDESK_CRD_MANIFEST = {
    "apiVersion": "apiextensions.k8s.io/v1",
    "kind": "CustomResourceDefinition",
    "metadata": {"name": f"{CYBERDESK_PLURAL}.{CYBERDESK_GROUP}"},
    "spec": {
        "group": CYBERDESK_GROUP,
        "names": {
            "kind": "Cyberdesk",
            "plural": CYBERDESK_PLURAL,
            "singular": "cyberdesk",
            "shortNames": ["cd", "cds"]
        },
        "scope": "Namespaced",
        "versions": [
            {
                "name": CYBERDESK_VERSION,
                "served": True,
                "storage": True,
                "schema": {
                    "openAPIV3Schema": {
                        "type": "object",
                        "properties": {
                            "spec": {
                                "type": "object",
                                "properties": {
                                    "timeoutMs": {
                                        "type": "integer",
                                        "description": "Timeout in milliseconds after which the instance will be terminated",
                                        "minimum": 1000
                                    }
                                },
                                "required": ["timeoutMs"]
                            },
                            "status": {
                                "type": "object",
                                "properties": {
                                    "virtualMachineRef": {"type": "string", "description": "Name of the associated KubeVirt VirtualMachine"},
                                    "startTime": {"type": "string", "format": "date-time", "description": "Time when the instance was started"},
                                    "expiryTime": {"type": "string", "format": "date-time", "description": "Time when the instance will expire based on timeout"},
                                    "message": {"type": "string", "description": "Informational message about the VM state"}
                                }
                            }
                        }
                    }
                },
                "additionalPrinterColumns": [
                    {"name": "VMI", "type": "string", "jsonPath": ".status.virtualMachineRef"},
                    {"name": "Timeout(ms)", "type": "integer", "jsonPath": ".spec.timeoutMs"},
                    {"name": "Expiry", "type": "date", "jsonPath": ".status.expiryTime"},
                    {"name": "Age", "type": "date", "jsonPath": ".metadata.creationTimestamp"}
                ],
                "subresources": {"status": {}}
            }
        ]
    }
}

@kopf.on.create(CYBERDESK_GROUP, CYBERDESK_VERSION, START_OPERATOR_PLURAL)
def setup_cyberdesk_operator(spec, meta, **kwargs):
    """
    On creation of the StartCyberdeskOperator resource, triggers installation of other
    crucial Cyberdesk Operator resources, and allows for future configuration of the operator from
    the StartCyberdeskOperator resource (none as of now).
    """
    trigger_name = meta.get('name')
    namespace = meta.get('namespace')

    logging.info(f"Received trigger {trigger_name} in {namespace}. Applying Cyberdesk CRD.")

    # Apply the Cyberdesk CRD
    try:
        apiextensions_v1_api.create_custom_resource_definition(body=CYBERDESK_CRD_MANIFEST)
        logging.info(f"Successfully applied Cyberdesk CRD.")
    except kubernetes.client.rest.ApiException as e:
        logging.error(f"Failed to apply Cyberdesk CRD: {e}")
        raise kopf.PermanentError(f"Failed to apply Cyberdesk CRD: {e}")

@kopf.on.create(CYBERDESK_GROUP, CYBERDESK_VERSION, CYBERDESK_PLURAL)
def create_vm_from_cyberdesk(spec, meta, status, **kwargs):
    """
    Handle creation of a new Cyberdesk resource.
    Creates a corresponding KubeVirt VirtualMachine resource.
    """
    start_time = time.time()
    cyberdesk_name = meta.get('name')
    namespace = meta.get('namespace')
    resource_version = meta.get('resourceVersion')
    handler_id = 'create_vm'
    
    # Added checks for essential metadata
    if not cyberdesk_name:
        logging.error("Cyberdesk resource is missing name in metadata.")
        raise kopf.PermanentError("Missing name in metadata")
    if not namespace:
        logging.error(f"Cyberdesk resource '{cyberdesk_name}' is missing namespace in metadata.")
        raise kopf.PermanentError(f"Missing namespace in metadata for '{cyberdesk_name}'")
    
    # Check if we've already processed this resource version
    if is_handler_already_processed(meta, handler_id, resource_version):
        logging.info(f"Skipping VM creation for Cyberdesk {cyberdesk_name} as it was already processed")
        return
    
    logging.info(f"Creating VM for Cyberdesk {cyberdesk_name} in namespace {namespace}")
    
    # Extract necessary info from the Cyberdesk spec
    timeout_ms = spec.get('timeoutMs', 3600000)  # Default to 1 hour
    
    # Check if VM already exists to ensure idempotency
    try:
        custom_objects_api.get_namespaced_custom_object(
            group=KUBEVIRT_GROUP,
            version=KUBEVIRT_VERSION,
            namespace=KUBEVIRT_NAMESPACE,
            plural=KUBEVIRT_VM_PLURAL,
            name=cyberdesk_name
        )
        # VM already exists, mark as processed and return current status
        logging.info(f"VM {cyberdesk_name} already exists for Cyberdesk with name: {cyberdesk_name}")
        
        # Get the current Cyberdesk to access its status
        try:
            cyberdesk = custom_objects_api.get_namespaced_custom_object(
                group=CYBERDESK_GROUP,
                version=CYBERDESK_VERSION,
                namespace=namespace,
                plural=CYBERDESK_PLURAL,
                name=cyberdesk_name
            )
        except kubernetes.client.rest.ApiException as e:
            logging.error(f"Failed to fetch existing Cyberdesk {cyberdesk_name}: {e}")
            raise kopf.TemporaryError(f"Failed to fetch Cyberdesk: {e}")

        # Mark as processed
        mark_handler_processed(custom_objects_api, cyberdesk, handler_id, resource_version)
        
        # Return current status if it exists
        current_status = cyberdesk.get('status')
        if current_status:
            return current_status
        
        # Otherwise return a basic status
        return {
            'virtualMachineRef': cyberdesk_name,
            'message': 'VM already exists'
        }
        
    except kubernetes.client.rest.ApiException as e:
        if e.status != 404:
            # Unexpected error, let Kopf handle the retry
            logging.error(f"Error checking if VM {cyberdesk_name} exists: {e}")
            raise kopf.TemporaryError(f"Failed to check VM existence: {e}", delay=10)
    
    # Load and render the VM template
    template = load_vm_template()
    template = string.Template(template)
    rendered_template = template.substitute(
        vm_name=cyberdesk_name,
        cyberdesk_name=cyberdesk_name,
        managed_by=MANAGED_BY,
        user_data_base64="",  # Empty by default, would be populated in a real scenario
    )
    
    # Parse the YAML into a dictionary
    vm_manifest = yaml.safe_load(rendered_template)

    # TODO: Check warm pool for available VM that matches the spec and is ready.
    # If found, update DB "instance" with this available VM and return normally
    # If not found, proceed with creation.
    
    # Create a new VM
    try:
        custom_objects_api.create_namespaced_custom_object(
            group=KUBEVIRT_GROUP,
            version=KUBEVIRT_VERSION,
            namespace=KUBEVIRT_NAMESPACE,
            plural=KUBEVIRT_VM_PLURAL,
            body=vm_manifest
        )
        
        # Get the current time and calculate expiry
        now = datetime.now()
        expiry = now + timedelta(milliseconds=timeout_ms)
        
        logging.info(f"VM {cyberdesk_name} created successfully in namespace {namespace}, will expire at {expiry.isoformat()}")
        
        # Get the updated Cyberdesk to mark it as processed
        try:
            cyberdesk = custom_objects_api.get_namespaced_custom_object(
                group=CYBERDESK_GROUP,
                version=CYBERDESK_VERSION,
                namespace=namespace,
                plural=CYBERDESK_PLURAL,
                name=cyberdesk_name
            )
        except kubernetes.client.rest.ApiException as e:
            logging.error(f"Failed to fetch Cyberdesk {cyberdesk_name} after VM creation: {e}")
            # Continue without marking processed, might lead to reprocessing but better than failing
            cyberdesk = None

        if cyberdesk:
            mark_handler_processed(custom_objects_api, cyberdesk, handler_id, resource_version)
        
        # Update the Cyberdesk status
        return {
            'virtualMachineRef': cyberdesk_name,
            'startTime': now.isoformat(),
            'expiryTime': expiry.isoformat(),
            'message': 'VM created successfully and is starting'
        }
    except Exception as e:
        logging.error(f"Failed to create VM for Cyberdesk {cyberdesk_name} in namespace {namespace}: {e}")
        raise kopf.PermanentError(f"Failed to create VM: {e}")


@kopf.on.update(KUBEVIRT_GROUP, KUBEVIRT_VERSION, KUBEVIRT_VMI_PLURAL)
def react_to_vmi_updates(spec, meta, status, old, new, **kwargs):
    """
    Watch for VirtualMachineInstance updates and performs various actions:
    - Updates DB "instance" status with VMI status (use dummy DB for now)
    - Tracks error states and reports them
    """
    # Check if this VMI is related to a Cyberdesk
    labels = meta.get('labels', {})
    if labels.get('app') != 'cyberdesk':
        return
        
    cyberdesk_name = labels.get('cyberdesk-instance')
    if not cyberdesk_name:
        # Log a warning if the label is missing, but don't stop processing
        logging.warning(f"VMI {meta.get('name', 'unknown')} is missing 'cyberdesk-instance' label.")
        return # Exit if the crucial label is missing
    
    namespace = meta.get('namespace')
    vmi_name = meta.get('name', 'unknown') # Added default for logging
    if not namespace:
        logging.error(f"VMI '{vmi_name}' is missing namespace in metadata.")
        # Cannot proceed without namespace
        return

    # Get the current VMI status
    vmi_status = status.get('phase', 'Unknown')
    
    logging.info(f"Updating DB instance with name = {cyberdesk_name} in namespace {namespace} based on VMI {vmi_name} status: {vmi_status}")
    
    # Get the resource version to ensure idempotency
    resource_version = meta.get('resourceVersion')
    
    # Ensure idempotency (passing meta, which is now handled safely)
    # Need to pass the VMI object itself to mark_handler_processed, not just meta
    vmi_object = new # Use the 'new' object state passed by Kopf for patching
    if is_handler_already_processed(meta, 'react_to_vmi_updates', resource_version):
        logging.info(f"Skipping VMI update for {cyberdesk_name} (VMI: {vmi_name}) as it was already processed")
        return
    
    # Update DB "instance" status with VMI status (use dummy DB for now)
    # TODO: Implement actual DB update
    logging.info(f"Updated DB status for Cyberdesk {cyberdesk_name} in namespace {namespace} with VMI status: {vmi_status}")
    
    # Mark the handler as processed using the VMI object
    mark_handler_processed(custom_objects_api, vmi_object, 'react_to_vmi_updates', resource_version)

    # Track error states and report them
    if vmi_status in ['Failed', 'Unknown']:
        logging.error(f"VMI {vmi_name} in namespace {namespace} is in error state: {vmi_status}")
        # TODO: Implement actual error reporting

    # Probably more to do here.



@kopf.on.delete(CYBERDESK_GROUP, CYBERDESK_VERSION, CYBERDESK_PLURAL)
def delete_vm_for_cyberdesk(spec, meta, status, **kwargs):
    """
    Handle deletion of a Cyberdesk resource.
    Deletes the corresponding KubeVirt VirtualMachine, or returns to warm pool.
    """
    start_time = time.time()
    cyberdesk_name = meta.get('name')
    namespace = meta.get('namespace')

    # Added checks for essential metadata
    if not cyberdesk_name:
        logging.warning("Handling deletion for Cyberdesk resource missing name in metadata.")
        # Cannot proceed without a name
        return 
    if not namespace:
        logging.warning(f"Handling deletion for Cyberdesk resource '{cyberdesk_name}' missing namespace in metadata.")
        # Cannot proceed without namespace
        return

    logging.info(f"Handling deletion of Cyberdesk {cyberdesk_name} in namespace {namespace}")
    
    vm_name = status.get('virtualMachineRef') if status else None
    if not vm_name:
        logging.info(f"No VM reference found in status for Cyberdesk {cyberdesk_name} in namespace {namespace}, nothing to delete.")
        return
        
    try:
        # First check if VM exists
        custom_objects_api.get_namespaced_custom_object(
            group=KUBEVIRT_GROUP,
            version=KUBEVIRT_VERSION,
            namespace=namespace,
            plural=KUBEVIRT_VM_PLURAL,
            name=vm_name    
        )

        # TODO: Possibly return to warm pool. Reboot and set as "warm_pool" status.
        
        # Proceed with full deletion
        custom_objects_api.delete_namespaced_custom_object(
            group=KUBEVIRT_GROUP,
            version=KUBEVIRT_VERSION,
            namespace=namespace,
            plural=KUBEVIRT_VM_PLURAL,
            name=vm_name
        )

        # TODO: Update DB "instance" to be completed.
        
        logging.info(f"Successfully deleted VM {vm_name} in namespace {namespace}")
        
        # Cleanup any other resources associated with this VM
        try:
            # Check for any associated VMIs and delete them
            vmi_list = custom_objects_api.list_namespaced_custom_object(
                group=KUBEVIRT_GROUP,
                version=KUBEVIRT_VERSION,
                namespace=namespace,
                plural=KUBEVIRT_VMI_PLURAL,
                label_selector=f"app=cyberdesk,cyberdesk-instance={cyberdesk_name}"
            )
            
            for vmi in vmi_list.get('items', []):
                vmi_meta = vmi.get('metadata', {})
                vmi_name = vmi_meta.get('name')
                if not vmi_name:
                    logging.warning(f"Found associated VMI for {cyberdesk_name} but it is missing a name.")
                    continue # Skip this VMI

                try:
                    custom_objects_api.delete_namespaced_custom_object(
                        group=KUBEVIRT_GROUP,
                        version=KUBEVIRT_VERSION,
                        namespace=namespace,
                        plural=KUBEVIRT_VMI_PLURAL,
                        name=vmi_name
                    )
                    logging.info(f"Deleted associated VMI {vmi_name} in namespace {namespace}")
                except kubernetes.client.rest.ApiException as e:
                    if e.status != 404:
                        logging.warning(f"Failed to delete associated VMI {vmi_name}: {e}")
        
        except Exception as e:
            logging.warning(f"Error while cleaning up resources for {cyberdesk_name}: {e}")

    except kubernetes.client.rest.ApiException as e:
        if e.status == 404:
            logging.info(f"VM {vm_name} in namespace {namespace} already deleted")
        else:
            logging.error(f"Failed to delete VM {vm_name} in namespace {namespace}: {e}")
            raise kopf.PermanentError(f"Failed to delete VM: {e}")


# Cluster-wide timer to check Cyberdesks that have exceeded their timeout.
@kopf.on.timer(CYBERDESK_GROUP, CYBERDESK_VERSION, CYBERDESK_PLURAL, interval=60.0)  # Runs every 60 seconds for the operator process
def check_all_cyberdesk_timeouts(**kwargs):
    """
    Periodically check all Cyberdesks across the cluster for VMs that have exceeded their timeout.
    Shuts down the VM if it has exceeded the timeout.
    Notifies the DB "instance" that the instance timed out.
    """
    logging.debug("Starting cluster-wide check for Cyberdesk timeouts...")
    
    try:
        # List all Cyberdesk resources across all namespaces
        cyberdesks = custom_objects_api.list_cluster_custom_object(
            group=CYBERDESK_GROUP,
            version=CYBERDESK_VERSION,
            plural=CYBERDESK_PLURAL
        )
    except kubernetes.client.rest.ApiException as e:
        logging.error(f"Failed to list Cyberdesk resources: {e}")
        # Optional: Raise TemporaryError if listing fails often
        # raise kopf.TemporaryError(f"Failed to list Cyberdesks: {e}", delay=30)
        return
    except Exception as e:
        logging.error(f"Unexpected error listing Cyberdesk resources: {e}")
        return

    now = datetime.now()
    
    for cyberdesk in cyberdesks.get('items', []):
        meta = cyberdesk.get('metadata', {})
        status = cyberdesk.get('status', {})
        
        cyberdesk_name = meta.get('name')
        namespace = meta.get('namespace')
        
        if not cyberdesk_name or not namespace:
            logging.warning(f"Skipping Cyberdesk resource with missing name or namespace in metadata: {meta}")
            continue
            
        expiry_time_str = status.get('expiryTime')
        if not expiry_time_str:
            # Skip resources without an expiry time set in their status
            continue

        # Parse the expiry time
        try:
            expiry_time = datetime.fromisoformat(expiry_time_str)
        except (ValueError, TypeError) as e:
            logging.error(f"Invalid or missing expiry time format for Cyberdesk {cyberdesk_name} in namespace {namespace}: {expiry_time_str}. Error: {e}")
            continue # Skip this resource

        # Check if the Cyberdesk has exceeded its timeout
        if now > expiry_time:
            logging.info(f"Cyberdesk {cyberdesk_name} in namespace {namespace} has exceeded its timeout ({expiry_time_str})")
            
            # Simply delete the Cyberdesk resource, which will trigger the delete_vm_for_cyberdesk handler.
            # Add try-except around deletion for robustness
            try:
                custom_objects_api.delete_namespaced_custom_object(
                    group=CYBERDESK_GROUP,
                    version=CYBERDESK_VERSION,
                    namespace=namespace,
                    plural=CYBERDESK_PLURAL,
                    name=cyberdesk_name
                )
            except kubernetes.client.rest.ApiException as e:
                if e.status == 404:
                    logging.info(f"Cyberdesk {cyberdesk_name} in namespace {namespace} already deleted.")
                else:
                    logging.error(f"Failed to delete timed-out Cyberdesk {cyberdesk_name} in {namespace}: {e}")
            except Exception as e:
                logging.error(f"Unexpected error deleting timed-out Cyberdesk {cyberdesk_name} in {namespace}: {e}")

        # End of check for 'if now > expiry_time:'
    # End of loop 'for cyberdesk in cyberdesks.get('items', []):'
    logging.debug("Finished cluster-wide check for Cyberdesk timeouts.")