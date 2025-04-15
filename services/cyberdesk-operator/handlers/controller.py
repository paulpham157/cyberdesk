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

# --- Dummy DB Functions (Add these near the top or where appropriate) ---
_dummy_db = {} # Simple in-memory dictionary for demonstration

def getInstanceStatusById(instance_id: str) -> str | None:
    """Dummy function to get instance status from a 'DB'."""
    logging.debug(f"DB Query: Get status for instance '{instance_id}'")
    status = _dummy_db.get(instance_id)
    logging.debug(f"DB Result: Status for '{instance_id}' is '{status}'")
    return status

def updateInstanceStatus(instance_id: str, status: str):
    """Dummy function to update instance status in a 'DB'."""
    logging.info(f"DB Update: Setting status for instance '{instance_id}' to '{status}'")
    _dummy_db[instance_id] = status
    # In a real scenario, handle DB errors, transactions etc.
# --- End Dummy DB Functions ---

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
                                "x-kubernetes-preserve-unknown-fields": True
                            }
                        }
                    }
                },
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
        logging.error(f"Failed to apply Cyberdesk CRD: {e.status} {e.reason}")
        # If the error is temporary (like 429), retry later.
        if e.status == 429:
             logging.warning(f"API server returned 429 (Too Many Requests), will retry CRD creation. Message: {e.body}")
             raise kopf.TemporaryError(f"API server busy, retrying CRD creation: {e.reason}", delay=10) # Retry after 10s
        else:
             # For other API errors (e.g., 403 Forbidden, 409 Conflict), treat as permanent for this resource.
             raise kopf.PermanentError(f"Failed to apply Cyberdesk CRD: {e.status} {e.reason}")
    except Exception as e:
         # Catch unexpected errors during CRD creation
         logging.exception(f"Unexpected error applying Cyberdesk CRD: {e}") # Use logging.exception to include traceback
         raise kopf.PermanentError(f"Unexpected error applying Cyberdesk CRD: {e}")

@kopf.on.create(CYBERDESK_GROUP, CYBERDESK_VERSION, CYBERDESK_PLURAL)
def create_vm_from_cyberdesk(spec, meta, status, **kwargs):
    """
    Handle creation of a new Cyberdesk resource.
    Creates a corresponding KubeVirt VirtualMachine resource using desired state reconciliation.
    """
    start_time = time.time()
    cyberdesk_name = meta.get('name')
    namespace = meta.get('namespace') # Namespace where Cyberdesk CR lives

    # Added checks for essential metadata
    if not cyberdesk_name:
        logging.error("Cyberdesk resource is missing name in metadata.")
        raise kopf.PermanentError("Missing name in metadata")
    if not namespace:
        logging.error(f"Cyberdesk resource '{cyberdesk_name}' is missing namespace in metadata.")
        raise kopf.PermanentError(f"Missing namespace in metadata for '{cyberdesk_name}'")

    logging.info(f"Reconciling VM for Cyberdesk {cyberdesk_name} in namespace {namespace}") # Log Cyberdesk namespace

    # Extract necessary info from the Cyberdesk spec
    timeout_ms = spec.get('timeoutMs', 3600000)  # Default to 1 hour

    # Check if VM already exists (Desired State Check)
    # Assume VM lives in KUBEVIRT_NAMESPACE (often 'kubevirt' or dedicated ns)
    vm_namespace = KUBEVIRT_NAMESPACE # Define where VMs should live
    try:
        existing_vm = custom_objects_api.get_namespaced_custom_object(
            group=KUBEVIRT_GROUP,
            version=KUBEVIRT_VERSION,
            namespace=vm_namespace, # Check in the VM namespace
            plural=KUBEVIRT_VM_PLURAL,
            name=cyberdesk_name
        )
        # VM already exists, ensure status reflects this
        logging.info(f"VM {cyberdesk_name} already exists in {vm_namespace} for Cyberdesk {cyberdesk_name}. Ensuring status is up-to-date.")

        # Fetch current Cyberdesk status if needed, or return existing status
        current_status = status # Use the status passed by Kopf initially
        if not current_status or current_status.get('virtualMachineRef') != cyberdesk_name:
             # If Kopf's status is empty or incorrect, build a basic one
             return {
                 'virtualMachineRef': cyberdesk_name,
                 # Consider fetching start/expiry time from existing_vm annotations/labels if needed
             }
        else:
             # Status already seems correct, just return it
             # Removed call to mark_handler_processed
             return current_status # Return Kopf's view of the status


    except kubernetes.client.rest.ApiException as e:
        if e.status != 404:
            # Unexpected error, let Kopf handle the retry
            logging.error(f"Error checking if VM {cyberdesk_name} exists in {vm_namespace}: {e}")
            raise kopf.TemporaryError(f"Failed to check VM existence: {e}", delay=10)
        # If status is 404, VM does not exist, proceed with creation.
        logging.info(f"VM {cyberdesk_name} does not exist in {vm_namespace}. Proceeding with creation.")


    # Load and render the VM template
    template = load_vm_template()
    template = string.Template(template)
    rendered_template = template.substitute(
        vm_name=cyberdesk_name,
        cyberdesk_name=cyberdesk_name, # Pass Cyberdesk name for labels/annotations in template
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
        # Create the VM in the designated KUBEVIRT_NAMESPACE
        custom_objects_api.create_namespaced_custom_object(
            group=KUBEVIRT_GROUP,
            version=KUBEVIRT_VERSION,
            namespace=vm_namespace, # Create in the VM namespace
            plural=KUBEVIRT_VM_PLURAL,
            body=vm_manifest
        )

        # Get the current time and calculate expiry
        now = datetime.now()
        expiry = now + timedelta(milliseconds=timeout_ms)

        logging.info(f"VM {cyberdesk_name} created successfully in namespace {vm_namespace}, will expire at {expiry.isoformat()}") # Log correct namespace

        # Removed fetching Cyberdesk and marking handler processed

        # Update the Cyberdesk status (which lives in 'namespace')
        return {
            'virtualMachineRef': cyberdesk_name, # Refers to the VM name
            'startTime': now.isoformat(),
            'expiryTime': expiry.isoformat()
        }
    except kubernetes.client.rest.ApiException as e:
         logging.error(f"Failed to create VM {cyberdesk_name} in namespace {vm_namespace}: {e.status} {e.reason}")
         # Check for common specific errors if needed (e.g., 409 Conflict if race condition)
         # Update DB "instance" to be in "error" state.
         raise kopf.TemporaryError(f"Failed to create VM: {e.reason}")
    except Exception as e:
        logging.error(f"Unexpected error creating VM {cyberdesk_name} in namespace {vm_namespace}: {e}")
        # Update DB "instance" to be in "error" state.
        raise kopf.TemporaryError(f"Unexpected error creating VM: {e}")


@kopf.on.field(KUBEVIRT_GROUP, KUBEVIRT_VERSION, KUBEVIRT_VMI_PLURAL, field='status.phase')
def react_to_vmi_phase_change(old, new, meta, status, logger, **kwargs):
    """
    Watch for VirtualMachineInstance phase changes.
    Update the corresponding instance status in the DB if it doesn't match.
    Only triggered when `status.phase` changes.
    """
    # --- Input Validation and Extraction ---
    vmi_name = meta.get('name', 'unknown-vmi')
    namespace = meta.get('namespace') # Namespace where VMI lives (e.g., KUBEVIRT_NAMESPACE)
    if not namespace:
        # This shouldn't happen for namespaced resources, but safeguard anyway
        logger.error(f"VMI update event for '{vmi_name}' is missing namespace in metadata.")
        return # Cannot proceed

    # Check if this VMI is managed by our operator via labels
    labels = meta.get('labels', {})
    if labels.get('app') != 'cyberdesk':
        # Not managed by us, ignore.
        # logger.debug(f"Ignoring VMI {vmi_name} phase change in {namespace}: Not labeled 'app=cyberdesk'.")
        return

    cyberdesk_name = labels.get('cyberdesk-instance')
    if not cyberdesk_name:
        logger.warning(f"VMI {vmi_name} in {namespace} is labeled 'app=cyberdesk' but missing 'cyberdesk-instance' label. Cannot link to DB.")
        return # Cannot link to DB instance without the ID

    old_phase = old # The old value of status.phase
    new_phase = new # The new value of status.phase

    logger.debug(f"Reacting to VMI phase change: {vmi_name} (Cyberdesk: {cyberdesk_name}) in {namespace}. Old phase: '{old_phase}', New phase: '{new_phase}'.")

    # --- Core Logic: Update DB on Meaningful Phase Change ---
    # The handler only runs if the phase changes, so we primarily care about the new phase.
    if new_phase is not None:
        logger.info(f"Phase changed for VMI {vmi_name} (Cyberdesk: {cyberdesk_name}) from '{old_phase}' to '{new_phase}'. Checking DB.")

        try:
            # Get the status currently recorded in our dummy DB
            current_db_status = getInstanceStatusById(cyberdesk_name)

            # Update DB only if its state doesn't already match the new VMI phase
            if current_db_status != new_phase:
                logger.info(f"DB status ('{current_db_status}') differs from new VMI phase ('{new_phase}') for {cyberdesk_name}. Updating DB.")
                updateInstanceStatus(cyberdesk_name, new_phase)
                # Potentially add further actions here based on the new_phase
                # e.g., if new_phase == 'Running', notify user?
                # e.g., if new_phase == 'Failed', log details from VMI conditions?
                if new_phase in ['Failed', 'Error']: # KubeVirt might use 'Error' too
                     # Access the full status object passed by Kopf
                     vmi_conditions = status.get('conditions', [])
                     logger.error(f"VMI {vmi_name} (Cyberdesk: {cyberdesk_name}) entered phase '{new_phase}'. Conditions: {vmi_conditions}")

            else:
                # DB already reflects the current VMI phase
                logger.info(f"DB status ('{current_db_status}') already matches new VMI phase ('{new_phase}') for {cyberdesk_name}. No DB update needed.")

        except Exception as e:
            # Catch potential errors during DB interaction (even dummy ones)
            logger.error(f"Error interacting with dummy DB for instance {cyberdesk_name} during VMI update processing: {e}")
            # Retry the handler later in case the DB issue is transient
            raise kopf.TemporaryError(f"DB interaction failed for {cyberdesk_name}: {e}", delay=30)

    else:
        # This case might occur if the phase field is explicitly set to null or removed.
        logger.warning(f"VMI {vmi_name} (Cyberdesk: {cyberdesk_name}) phase changed, but the new phase is None. Old phase was '{old_phase}'.")

    # No return value needed as we are not patching the Cyberdesk status here.
    # Kopf handles checkpointing automatically unless errors are raised.


@kopf.on.delete(CYBERDESK_GROUP, CYBERDESK_VERSION, CYBERDESK_PLURAL)
def delete_vm_for_cyberdesk(spec, meta, status, **kwargs):
    """
    Handle deletion of a Cyberdesk resource.
    Deletes the corresponding KubeVirt VirtualMachine, or returns to warm pool.
    """

    start_time = time.time()
    cyberdesk_name = meta.get('name')
    namespace = meta.get('namespace') # Namespace where Cyberdesk CR lives
    vm_namespace = KUBEVIRT_NAMESPACE # Namespace where VM/VMI should live

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

    # Access the nested status correctly
    create_status = status.get('create_vm_from_cyberdesk', {}) if status else {}
    vm_name = create_status.get('virtualMachineRef')
    # vm_name = status.get('virtualMachineRef') if status else None # Old incorrect line

    if not vm_name:
        logging.info(f"No VM reference found in status.create_vm_from_cyberdesk for Cyberdesk {cyberdesk_name} in namespace {namespace}, nothing to delete.")
        return

    try:
        # First check if VM exists in the correct namespace
        try:
            custom_objects_api.get_namespaced_custom_object(
                group=KUBEVIRT_GROUP,
                version=KUBEVIRT_VERSION,
                namespace=vm_namespace, # Use VM namespace
                plural=KUBEVIRT_VM_PLURAL,
                name=vm_name
            )
        except kubernetes.client.rest.ApiException as e:
            if e.status == 404:
                logging.info(f"VM {vm_name} in namespace {vm_namespace} already deleted")
                return
        except Exception as e:
            logging.error(f"Unexpected error checking if VM {vm_name} in namespace {vm_namespace} exists: {e}")
            raise kopf.TemporaryError(f"Unexpected error checking VM existence: {e}", delay=15)


        # TODO: Possibly return to warm pool. Reboot and set as "warm_pool" status.

        # Proceed with full deletion in the correct namespace
        custom_objects_api.delete_namespaced_custom_object(
            group=KUBEVIRT_GROUP,
            version=KUBEVIRT_VERSION,
            namespace=vm_namespace, # Use VM namespace
            plural=KUBEVIRT_VM_PLURAL,
            name=vm_name
        )

        # TODO: Update DB "instance" to be completed.

        logging.info(f"Successfully deleted VM {vm_name} in namespace {vm_namespace}")
    except kubernetes.client.rest.ApiException as e:
        if e.status == 404:
            logging.info(f"VM {vm_name} in namespace {vm_namespace} already deleted")
        else:
            logging.error(f"Failed to delete VM {vm_name} in namespace {vm_namespace}: {e}")
            # Use TemporaryError to retry if deletion fails transiently
            raise kopf.TemporaryError(f"Failed to delete VM {vm_name} in {vm_namespace}: {e.reason}", delay=15)
    except Exception as e: # Catch unexpected errors during deletion logic
        logging.exception(f"Unexpected error during deletion handling for Cyberdesk {cyberdesk_name}: {e}")
        raise kopf.TemporaryError(f"Unexpected error during deletion for {cyberdesk_name}: {e}", delay=30)


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
            
        # Access the nested status correctly
        create_status = status.get('create_vm_from_cyberdesk', {})
        expiry_time_str = create_status.get('expiryTime')
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

                # TODO: Update DB "instance" to be completed in some way.
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