"""
cyberdesk_operator.py
---------------------
Kopf‑based Kubernetes operator that provisions and manages KubeVirt VMs for a custom
`Cyberdesk` CRD.  Supabase is used as an external source of truth for instance state.

Key responsibilities
~~~~~~~~~~~~~~~~~~~~
* Bootstrap the operator (load configuration, create Cyberdesk CRD if required).
* Translate `Cyberdesk` resources into KubeVirt `VirtualMachine` objects and their
  accompanying cloud‑init secrets.
* Keep Supabase in sync with KubeVirt `VirtualMachineInstance` phase changes.
* Tear everything down again when a `Cyberdesk` CR is deleted or expires.

This single file keeps a clear top‑down structure:
    1. Standard‑library / third‑party imports
    2. Global configuration & logging
    3. Constants & enums
    4. Supabase and Kubernetes client bootstrap
    5. Utility helpers (template loading, DB helpers, etc.)
    6. Kopf event‑handlers (startup, create/update/delete, timers)

All helpers are deliberately *side‑effect free* (raise on error, return data), making
unit‑testing straightforward.
"""
from __future__ import annotations

import logging
import os
import string
import time
from datetime import UTC, datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Dict, Optional

import kopf
import kubernetes
import yaml
from dotenv import load_dotenv
from kopf import OperatorSettings
from kubernetes.client import (  # noqa: WPS433 — explicit import list for type checking
    CoreV1Api,
    CustomObjectsApi,
    ApiextensionsV1Api,
    ApiException,
)
from supabase import Client, create_client

# ---------------------------------------------------------------------------
# Logging & basic config -----------------------------------------------------
# ---------------------------------------------------------------------------
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)

# Ensure ENV is loaded *early* so everything that relies on os.getenv works.
load_dotenv()

# ---------------------------------------------------------------------------
# Constants -----------------------------------------------------------------
# ---------------------------------------------------------------------------
CYBERDESK_GROUP = "cyberdesk.io"
CYBERDESK_VERSION = "v1alpha1"
CYBERDESK_PLURAL = "cyberdesks"
START_OPERATOR_PLURAL = "startcyberdeskoperators"

KUBEVIRT_GROUP = "kubevirt.io"
KUBEVIRT_VERSION = "v1"
KUBEVIRT_NAMESPACE = os.getenv("KUBEVIRT_NAMESPACE", "kubevirt")
KUBEVIRT_VM_PLURAL = "virtualmachines"
KUBEVIRT_VMI_PLURAL = "virtualmachineinstances"

MANAGED_BY = "cyberdesk-operator"
CYBERDESK_NAMESPACE = os.getenv("CYBERDESK_NAMESPACE", "cyberdesk-system")

# ---------------------------------------------------------------------------
# Enums ----------------------------------------------------------------------
# ---------------------------------------------------------------------------
class KubeVirtVMIPhase(str, Enum):
    """Supported phases as emitted by KubeVirt."""

    PENDING = "Pending"
    SCHEDULING = "Scheduling"
    SCHEDULED = "Scheduled"
    RUNNING = "Running"
    SUCCEEDED = "Succeeded"
    FAILED = "Failed"
    UNKNOWN = "Unknown"


class SupabaseInstanceStatus(str, Enum):
    """Canonical states stored in Supabase."""

    PENDING = "pending"
    RUNNING = "running"
    TERMINATED = "terminated"
    ERROR = "error"


# Static mapping between the two state machines -----------------------------
VMI_PHASE_TO_SUPABASE_STATUS: Dict[KubeVirtVMIPhase, SupabaseInstanceStatus] = {
    KubeVirtVMIPhase.PENDING: SupabaseInstanceStatus.PENDING,
    KubeVirtVMIPhase.SCHEDULING: SupabaseInstanceStatus.PENDING,
    KubeVirtVMIPhase.SCHEDULED: SupabaseInstanceStatus.PENDING,
    KubeVirtVMIPhase.RUNNING: SupabaseInstanceStatus.PENDING, # We now only denote running after cloud init is done
    KubeVirtVMIPhase.SUCCEEDED: SupabaseInstanceStatus.TERMINATED,
    KubeVirtVMIPhase.FAILED: SupabaseInstanceStatus.ERROR,
    KubeVirtVMIPhase.UNKNOWN: SupabaseInstanceStatus.ERROR,
}

CLONE_GROUP = "clone.kubevirt.io"
CLONE_VERSION = "v1beta1"
CLONE_PLURAL = "virtualmachineclones"
GOLDEN_SNAPSHOT_NAME = "snapshot-golden-vm" # Name of the golden snapshot source
SNAPSHOT_GROUP = "snapshot.kubevirt.io" # Correct API group for VirtualMachineSnapshot
SNAPSHOT_VERSION = "v1beta1" # Correct version for VirtualMachineSnapshot
SNAPSHOT_PLURAL = "virtualmachinesnapshots"

# ---------------------------------------------------------------------------
# Bootstrap helpers ----------------------------------------------------------
# ---------------------------------------------------------------------------

def _init_supabase() -> Client:
    """Create and return a Supabase client or raise ``kopf.PermanentError``."""
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")

    if not supabase_url or not supabase_key:
        msg = "SUPABASE_URL / SUPABASE_KEY env vars must be set"
        logger.critical(msg)
        raise kopf.PermanentError(msg)

    try:
        client = create_client(supabase_url, supabase_key)
        logger.info("Supabase client initialised")
        return client
    except Exception as exc:  # noqa: BLE001 — log real error and abort
        logger.critical("Failed to initialise Supabase: %s", exc)
        raise kopf.PermanentError("Supabase init failed") from exc


def _init_kubernetes_clients() -> tuple[CoreV1Api, CustomObjectsApi, ApiextensionsV1Api]:
    """Return (core_v1, custom_objects, apiext) after loading config."""
    try:
        kubernetes.config.load_kube_config()
        logger.info("Loaded kube‑config from local file")
    except kubernetes.config.config_exception.ConfigException:
        try:
            kubernetes.config.load_incluster_config()
            logger.info("Loaded in‑cluster kube‑config")
        except kubernetes.config.config_exception.ConfigException as exc:
            logger.critical("Failed to load Kubernetes configuration: %s", exc)
            raise kopf.PermanentError("Cannot load Kubernetes config") from exc

    return CoreV1Api(), CustomObjectsApi(), ApiextensionsV1Api()


SUPABASE: Client = _init_supabase()
CORE_V1_API, CUSTOM_OBJECTS_API, APIEXT_V1_API = _init_kubernetes_clients()

# ---------------------------------------------------------------------------
# Supabase helpers -----------------------------------------------------------
# ---------------------------------------------------------------------------

def get_instance_status(instance_id: str) -> Optional[str]:
    """Return the current status for *instance_id* or ``None`` if missing/error."""
    try:
        logger.debug("Supabase query: status for %s", instance_id)
        resp = SUPABASE.table("cyberdesk_instances").select("status").eq("id", instance_id).limit(1).execute()
        return (resp.data[0]["status"] if resp.data else None)
    except Exception as exc:  # noqa: BLE001
        logger.error("Supabase error: %s", exc)
        return None


def update_instance_status(instance_id: str, vmi_phase: str) -> None:
    """Translate *vmi_phase* → Supabase status and update row if needed."""
    try:
        phase_enum = KubeVirtVMIPhase(vmi_phase)
    except ValueError:
        logger.error("Unknown VMI phase '%s' → marking ERROR", vmi_phase)
        target = SupabaseInstanceStatus.ERROR
    else:
        target = VMI_PHASE_TO_SUPABASE_STATUS.get(phase_enum, SupabaseInstanceStatus.ERROR)

    try:
        SUPABASE.table("cyberdesk_instances").update({"status": target.value}).eq("id", instance_id).execute()
        logger.info("Supabase status for %s set to %s", instance_id, target.value)
    except Exception as exc:  # noqa: BLE001
        logger.error("Supabase update failed for %s: %s", instance_id, exc)

# ---------------------------------------------------------------------------
# Kubernetes Helpers (including Warm Pool) -----------------------------------
# ---------------------------------------------------------------------------

def get_free_vm_from_pool(namespace: str, logger: kopf.Logger) -> Optional[str]:
    """
    Find, claim, and return the name of an available warm VM, or None.

    A VM is considered available if it has the 'pool.kubevirt.io/warm=ready'
    label, is Running, and does not have 'pool.kubevirt.io/in-use=true'.

    If found, the VM is "plucked" by:
    1. Removing ownerReferences.
    2. Setting 'pool.kubevirt.io/in-use=true' and 'pool.kubevirt.io/warm=claimed'.
    """
    pool_label_selector = "pool.kubevirt.io/warm=ready"
    logger.debug(f"Searching for warm VMs in namespace '{namespace}' with label '{pool_label_selector}'")
    try:
        vms = CUSTOM_OBJECTS_API.list_namespaced_custom_object(
            KUBEVIRT_GROUP,
            KUBEVIRT_VERSION,
            namespace,
            KUBEVIRT_VM_PLURAL,
            label_selector=pool_label_selector,
        )
    except ApiException as e:
        logger.error(f"Error listing VMs for warm pool: {e.status} {e.reason}")
        # Treat as temporary, maybe API server issue
        raise kopf.TemporaryError("Failed to list VMs for warm pool.", delay=15) from e

    for vm in vms.get("items", []):
        meta = vm.get("metadata", {})
        status = vm.get("status", {})
        labels = meta.get("labels", {})

        vm_name = meta.get("name")
        if not vm_name:
            logger.warning("Found VM in pool list without a name, skipping.")
            continue

        # Check if already marked as in-use by the pool logic itself
        if labels.get("pool.kubevirt.io/in-use") == "true":
            logger.debug(f"Warm VM '{vm_name}' found but already marked in-use, skipping.")
            continue

        # Check if running (important!)
        if status.get("printableStatus") != "Running":
            logger.debug(f"Warm VM '{vm_name}' found but not Running (status: {status.get('printableStatus')}), skipping.")
            continue

        # --- Pluck the VM ---
        logger.info(f"Found available warm VM: '{vm_name}'. Attempting to pluck.")
        patch_body = {
            "metadata": {
                "ownerReferences": None,  # Detach from the pool controller
                "labels": {
                    **labels, # Keep existing labels
                    "pool.kubevirt.io/in-use": "true", # Mark as used
                    "pool.kubevirt.io/warm": "claimed", # Update pool status label
                    # Note: We will add cyberdesk-instance label in the main handler
                },
            }
        }
        try:
            CUSTOM_OBJECTS_API.patch_namespaced_custom_object(
                group=KUBEVIRT_GROUP,
                version=KUBEVIRT_VERSION,
                namespace=namespace,
                plural=KUBEVIRT_VM_PLURAL,
                name=vm_name,
                body=patch_body,
            )
            logger.info(f"Successfully plucked warm VM '{vm_name}'. Removed ownerReferences and added 'in-use' label.")
            return vm_name # Return the name of the plucked VM
        except ApiException as e:
            logger.error(f"Failed to patch (pluck) warm VM '{vm_name}': {e.status} {e.reason}")
            # If patching fails, maybe the VM was deleted concurrently? Or permissions issue.
            # Log error and continue searching, maybe another VM will work.
            # If it's a transient issue, the next reconciliation might succeed.
            continue # Try the next VM in the list

    logger.info("No available warm VMs found in the pool.")
    return None

# ---------------------------------------------------------------------------
# CRD definition -------------------------------------------------------------
# ---------------------------------------------------------------------------
CYBERDESK_CRD_MANIFEST: dict = {
    "apiVersion": "apiextensions.k8s.io/v1",
    "kind": "CustomResourceDefinition",
    "metadata": {"name": f"{CYBERDESK_PLURAL}.{CYBERDESK_GROUP}"},
    "spec": {
        "group": CYBERDESK_GROUP,
        "scope": "Namespaced",
        "names": {
            "plural": CYBERDESK_PLURAL,
            "singular": "cyberdesk",
            "kind": "Cyberdesk",
            "shortNames": ["cd", "cds"],
        },
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
                                        "minimum": 1000,
                                        "description": "Milliseconds until VM is terminated.",
                                    }
                                },
                                "required": ["timeoutMs"],
                            },
                            "status": {
                                "type": "object",
                                "x-kubernetes-preserve-unknown-fields": True,
                            },
                        },
                    }
                },
                "subresources": {"status": {}},
            }
        ],
    },
}

# ---------------------------------------------------------------------------
# Kopf handlers --------------------------------------------------------------
# ---------------------------------------------------------------------------

def ensure_golden_snapshot_exists():
    """Check if the required golden VirtualMachineSnapshot exists."""
    logger.info(f"Checking for golden snapshot: {GOLDEN_SNAPSHOT_NAME} in {KUBEVIRT_NAMESPACE}")
    try:
        CUSTOM_OBJECTS_API.get_namespaced_custom_object(
            group=SNAPSHOT_GROUP,
            version=SNAPSHOT_VERSION,
            namespace=KUBEVIRT_NAMESPACE,
            plural=SNAPSHOT_PLURAL,
            name=GOLDEN_SNAPSHOT_NAME,
        )
        logger.info(f"Golden snapshot '{GOLDEN_SNAPSHOT_NAME}' found.")
    except ApiException as e:
        if e.status == 404:
            msg = f"Required golden snapshot '{GOLDEN_SNAPSHOT_NAME}' not found in namespace '{KUBEVIRT_NAMESPACE}'."
            logger.critical(msg)
            raise kopf.PermanentError(msg)
        else:
            msg = f"Error checking for golden snapshot '{GOLDEN_SNAPSHOT_NAME}': {e.status} {e.reason}"
            logger.error(msg)
            # Treat other errors as temporary to allow retries after potential cluster issues
            raise kopf.TemporaryError(msg, delay=30) from e
    except Exception as e:
        msg = f"Unexpected error checking for golden snapshot '{GOLDEN_SNAPSHOT_NAME}': {e}"
        logger.error(msg)
        raise kopf.TemporaryError(msg, delay=30) from e


@kopf.on.startup()
def configure_kopf(settings: OperatorSettings, **_: Dict[str, object]) -> None:
    """Tune watch timeouts and ensure golden snapshot exists."""
    settings.watching.server_timeout = 210  # seconds
    logger.info("Kopf watch server_timeout set to %s", settings.watching.server_timeout)
    # Check for snapshot on startup - operator won't function without it.
    ensure_golden_snapshot_exists()


@kopf.on.create(CYBERDESK_GROUP, CYBERDESK_VERSION, START_OPERATOR_PLURAL)
def crd_bootstrap(spec: dict, meta: dict, **_: Dict[str, object]) -> None:
    """Ensure the Cyberdesk CRD exists once the *bootstrap* resource is created."""
    try:
        APIEXT_V1_API.create_custom_resource_definition(body=CYBERDESK_CRD_MANIFEST)
        logger.info("Cyberdesk CRD applied")
    except kubernetes.client.rest.ApiException as exc:
        if exc.status == 409:  # already present
            logger.debug("Cyberdesk CRD already present")
        elif exc.status == 429:
            raise kopf.TemporaryError("API busy, retrying", delay=10) from exc
        else:
            raise kopf.PermanentError(f"CRD creation failed: {exc.status} {exc.reason}") from exc


def _ensure_vm_patched_and_running(vm_name: str, namespace: str, logger: kopf.Logger) -> None:
    """Fetch the VM and apply the required patches (metadata, spec, runStrategy)."""
    logger.info(f"Ensuring VM '{vm_name}' is patched and set to run.")
    # Labels intended for the VMI must go into spec.template.metadata.labels
    # Labels only relevant to the VM object itself can stay at the top level.
    patch_body = {
        "metadata": {
            "labels": {
                # Optional: Keep labels specific to the VM object itself here if needed.
                # For instance, if you wanted to label the VM resource differently than the VMI.
                "managed-by": MANAGED_BY, # Can be useful on the VM too
            }
            # Add top-level annotations for the VM if needed
        },
        "spec": {
            "runStrategy": "Always", # Ensure VM is set to run
            "template": {
                "metadata": { # <--- Ensure metadata exists here
                    "labels": { # <--- Labels for the VMI go here
                        "app": "cyberdesk",
                        "cyberdesk-instance": vm_name,
                        "managed-by": MANAGED_BY, # Also label the VMI for consistency
                        "kubevirt.io/domain": vm_name, # This is often set here
                    }
                    # Add annotations for the VMI if needed
                },
                "spec": {
                    "hostname": vm_name,
                    "subdomain": "kubevirt-vm-headless"
                }
            }
        }
    }
    try:
        CUSTOM_OBJECTS_API.patch_namespaced_custom_object(
            group=KUBEVIRT_GROUP,
            version=KUBEVIRT_VERSION,
            namespace=namespace,
            plural=KUBEVIRT_VM_PLURAL,
            name=vm_name,
            body=patch_body
        )
        logger.info(f"Successfully patched VM '{vm_name}' metadata, spec, and runStrategy.")
    except ApiException as e:
        logger.error(f"Error patching VM '{vm_name}': {e.status} {e.reason}")
        # If patching fails, it's likely temporary or the VM was deleted.
        raise kopf.TemporaryError(f"Failed to patch VM {vm_name}", delay=10) from e


@kopf.on.create(CYBERDESK_GROUP, CYBERDESK_VERSION, CYBERDESK_PLURAL)
def cyberdesk_create(spec: dict, meta: dict, status: dict, logger: kopf.Logger, patch: kopf.Patch, body: dict, retry: int, **_: Dict[str, object]): # noqa: WPS211, WPS231
    """Reconcile a new Cyberdesk CR: Try warm pool first, then clone from golden snapshot."""
    instance_id = meta["name"] # Target VM name is the Cyberdesk CR name (consistent)
    namespace = KUBEVIRT_NAMESPACE # Target VM namespace
    timeout_ms = spec.get("timeoutMs", 3_600_000)  # default: 1h

    logger.info(f"Reconciling Cyberdesk CR '{instance_id}'")

    # --- Step 1: Try to get a VM from the warm pool ---
    plucked_vm_name = get_free_vm_from_pool(namespace, logger)

    if plucked_vm_name:
        logger.info(f"Using plucked warm VM '{plucked_vm_name}' for Cyberdesk '{instance_id}'.")

        # Patch the plucked VM with Cyberdesk-specific details
        # Note: We don't need to set runStrategy=Always as it's already running.
        # We DO need to set the instance label and hostname.
        vm_patch_body = {
            "metadata": {
                "labels": {
                    # Keep existing labels (like 'pool.kubevirt.io/in-use')
                    # Add/overwrite Cyberdesk specific labels
                    "app": "cyberdesk", # Standard label
                    "cyberdesk-instance": instance_id, # Link to this CR
                    "managed-by": MANAGED_BY, # Ensure operator management label
                }
            },
            "spec": {
                "template": {
                    "metadata": { # VMI metadata
                        "labels": {
                            # Keep existing labels if any? Maybe not necessary.
                            "app": "cyberdesk",
                            "cyberdesk-instance": instance_id,
                            "managed-by": MANAGED_BY,
                            "kubevirt.io/domain": instance_id, # Standard KubeVirt label for VMI domain
                        }
                    },
                    "spec": { # VMI spec
                        "hostname": instance_id,
                        "subdomain": "kubevirt-vm-headless" # Consistent with cloned VMs
                    }
                }
            }
        }
        try:
            # Fetch current labels first to merge correctly
            current_vm = CUSTOM_OBJECTS_API.get_namespaced_custom_object(
                KUBEVIRT_GROUP, KUBEVIRT_VERSION, namespace, KUBEVIRT_VM_PLURAL, plucked_vm_name
            )
            current_labels = current_vm.get("metadata", {}).get("labels", {})
            current_vmi_labels = current_vm.get("spec", {}).get("template", {}).get("metadata", {}).get("labels", {})

            vm_patch_body["metadata"]["labels"] = {**current_labels, **vm_patch_body["metadata"]["labels"]}
            vm_patch_body["spec"]["template"]["metadata"]["labels"] = {**current_vmi_labels, **vm_patch_body["spec"]["template"]["metadata"]["labels"]}


            CUSTOM_OBJECTS_API.patch_namespaced_custom_object(
                group=KUBEVIRT_GROUP,
                version=KUBEVIRT_VERSION,
                namespace=namespace,
                plural=KUBEVIRT_VM_PLURAL,
                name=plucked_vm_name,
                body=vm_patch_body
            )
            logger.info(f"Successfully patched plucked VM '{plucked_vm_name}' with labels and hostname for '{instance_id}'.")
        except ApiException as e:
            logger.error(f"Error patching plucked VM '{plucked_vm_name}': {e.status} {e.reason}")
            # This is potentially problematic. The VM is plucked but not configured.
            # Should we try to "unpluck" it? Or rely on retry?
            # Let's rely on Kopf's retry mechanism for now.
            raise kopf.TemporaryError(f"Failed to patch plucked VM {plucked_vm_name}", delay=10) from e

        # --- Update Status for Plucked VM ---
        now = datetime.now(UTC)
        expiry = now + timedelta(milliseconds=timeout_ms)
        logger.info(f"Cyberdesk '{instance_id}' reconciled using warm VM '{plucked_vm_name}', expires at {expiry.isoformat()}")

        if "cyberdesk_create" not in patch.status:
            patch.status["cyberdesk_create"] = {}
        patch.status["cyberdesk_create"]["virtualMachineRef"] = plucked_vm_name # Use the plucked VM name
        patch.status["cyberdesk_create"]["startTime"] = now.isoformat()
        patch.status["cyberdesk_create"]["expiryTime"] = expiry.isoformat()
        patch.status["cyberdesk_create"]["lastPhase"] = "Plucked" # Indicate it came from the pool

        # Clean up old top-level status fields if they still exist
        if "virtualMachineRef" in patch.status: del patch.status["virtualMachineRef"]
        if "startTime" in patch.status: del patch.status["startTime"]
        if "expiryTime" in patch.status: del patch.status["expiryTime"]

        return # Finished processing with a warm VM

    # --- Step 2: Fallback to Cloning if no warm VM was available ---
    logger.info(f"No warm VM available for '{instance_id}'. Falling back to cloning from snapshot.")

    # The rest of the function is the original cloning logic.
    # Important: The target VM name is 'instance_id' here too.
    vm_name = instance_id # Use the CR name as the target VM name for cloning
    clone_operation_name = f"clone-for-{vm_name}"
    max_clone_wait_retries = 20
    clone_wait_delay = 2 # seconds

    # --- Idempotency Check 1: Target VM Existence (Clone Path Only) ---
    # This check is now specific to the clone path. If a VM exists, it might be
    # from a previous failed/interrupted clone attempt for *this* CR.
    try:
        CUSTOM_OBJECTS_API.get_namespaced_custom_object(
            KUBEVIRT_GROUP, KUBEVIRT_VERSION, namespace, KUBEVIRT_VM_PLURAL, vm_name
        )
        # If the VM exists AND we are in the CLONE path, it means the warm pool
        # check failed, but a VM with the target name *already exists*.
        # This implies a previous clone attempt for this CR might have partially succeeded
        # or something else created a VM with this name.
        logger.warning(f"Target VM '{vm_name}' already exists, but was NOT plucked from pool. Proceeding with patch/run check as part of clone fallback recovery.")
        # Ensure the existing VM has the correct patches and is set to run
        # This re-uses the existing logic to bring a potentially orphaned VM into the desired state.
        _ensure_vm_patched_and_running(vm_name, namespace, logger)

        # Status handling similar to before, but assuming it relates to a CLONE attempt
        existing_status = body.get("status", {}).get("cyberdesk_create", {})
        if existing_status and "startTime" in existing_status and "expiryTime" in existing_status:
             logger.info(f"Restoring existing status for VM {vm_name} during clone fallback.")
             patch.status.update(existing_status) # Restore full existing status
        else:
            logger.warning(f"VM {vm_name} exists during clone fallback, but status is missing/incomplete. Creating/updating status.")
            now = datetime.now(UTC)
            expiry = now + timedelta(milliseconds=timeout_ms)
            patch.status["cyberdesk_create"] = {
                 "virtualMachineRef": vm_name,
                 "startTime": now.isoformat(),
                 "expiryTime": expiry.isoformat(),
                 "lastPhase": "Running" # Assume running after patch check
            }
        # Clean up old fields
        if "virtualMachineRef" in patch.status: del patch.status["virtualMachineRef"]
        if "startTime" in patch.status: del patch.status["startTime"]
        if "expiryTime" in patch.status: del patch.status["expiryTime"]

        return # Stop reconciliation for this CR (existing VM handled in clone path)

    except ApiException as e:
        if e.status != 404:
            logger.error(f"Error checking for existing VM '{vm_name}' in clone path: {e.status} {e.reason}")
            raise kopf.TemporaryError(f"VM check failed for {vm_name} (clone path)", delay=10) from e
        # VM Not found (expected case for cloning), proceed.
        logger.info(f"Target VM '{vm_name}' not found. Proceeding with clone operation.")

    # --- Define and Create/Get VirtualMachineClone (Clone Path Only) ---
    clone_body = {
        "apiVersion": f"{CLONE_GROUP}/{CLONE_VERSION}",
        "kind": "VirtualMachineClone",
        "metadata": {
            "name": clone_operation_name,
            "namespace": namespace,
             "labels": {"managed-by": MANAGED_BY, "cyberdesk-instance": vm_name}, # Add labels for tracking
        },
        "spec": {
            "source": {
                "apiGroup": SNAPSHOT_GROUP,
                "kind": "VirtualMachineSnapshot",
                "name": GOLDEN_SNAPSHOT_NAME,
            },
            "target": {
                "apiGroup": KUBEVIRT_GROUP,
                "kind": "VirtualMachine",
                "name": vm_name, # Target VM name
            },
        },
    }

    try:
        logger.info(f"Creating/getting VirtualMachineClone '{clone_operation_name}'")
        clone_obj = CUSTOM_OBJECTS_API.create_namespaced_custom_object(
            group=CLONE_GROUP,
            version=CLONE_VERSION,
            namespace=namespace,
            plural=CLONE_PLURAL,
            body=clone_body,
        )
        logger.info(f"VirtualMachineClone '{clone_operation_name}' created.")
    except ApiException as e:
        if e.status == 409: # Conflict - clone object already exists
             logger.info(f"VirtualMachineClone '{clone_operation_name}' already exists. Checking status.")
             try:
                 clone_obj = CUSTOM_OBJECTS_API.get_namespaced_custom_object(
                     group=CLONE_GROUP, version=CLONE_VERSION, namespace=namespace, plural=CLONE_PLURAL, name=clone_operation_name
                 )
             except ApiException as get_exc:
                 logger.error(f"Failed to get existing clone '{clone_operation_name}': {get_exc.status} {get_exc.reason}")
                 raise kopf.TemporaryError(f"Failed to get existing clone {clone_operation_name}", delay=10) from get_exc
        else:
            logger.error(f"Error creating VirtualMachineClone '{clone_operation_name}': {e.status} {e.reason}")
            raise kopf.TemporaryError(f"Clone creation failed for {vm_name}", delay=10) from e

    # --- Check Clone Status ---
    try:
        # Refresh clone object status
        current_clone_status = clone_obj.get("status", {})
        clone_phase = current_clone_status.get("phase")
        logger.info(f"Clone '{clone_operation_name}' phase: {clone_phase}")

        if clone_phase == "Succeeded":
            logger.info(f"Clone '{clone_operation_name}' succeeded.")
            # --- Ensure the newly created VM is patched and running ---
            _ensure_vm_patched_and_running(vm_name, namespace, logger)
        elif clone_phase == "Failed":
            logger.error(f"Clone '{clone_operation_name}' failed. Check clone object status for details.")
            # Clean up failed clone object? Maybe not, leave it for inspection.
            raise kopf.PermanentError(f"Clone {clone_operation_name} failed.")
        elif clone_phase == "Unknown":
                logger.warning(f"Clone '{clone_operation_name}' phase is Unknown. Retrying...")
                raise kopf.TemporaryError(f"Clone {clone_operation_name} phase Unknown.", delay=clone_wait_delay)
        else: # InProgress phases (SnapshotInProgress, CreatingTargetVM, RestoreInProgress)
            # Get potentially updated clone object for next status check
            # Place this *inside* the else block before raising TemporaryError
            try:
                    clone_obj = CUSTOM_OBJECTS_API.get_namespaced_custom_object(
                        group=CLONE_GROUP, version=CLONE_VERSION, namespace=namespace, plural=CLONE_PLURAL, name=clone_operation_name
                    )
            except ApiException as get_exc:
                    logger.warning(f"Failed to get clone '{clone_operation_name}' status during wait: {get_exc.reason}")
                    # Continue retry loop even if getting status fails temporarily
            raise kopf.TemporaryError(f"Clone {clone_operation_name} in progress ({clone_phase}). Waiting...", delay=clone_wait_delay)

    except kopf.TemporaryError:
            # Re-raise TemporaryError to trigger Kopf retry with delay
            if retry + 1 == max_clone_wait_retries:
                logger.error(f"Clone '{clone_operation_name}' did not succeed within the timeout.")
                # Potentially delete the clone object if it's stuck?
                try:
                    CUSTOM_OBJECTS_API.delete_namespaced_custom_object(CLONE_GROUP, CLONE_VERSION, namespace, CLONE_PLURAL, clone_operation_name)
                    logger.info(f"Deleted timed-out clone object '{clone_operation_name}'.")
                except ApiException as del_exc:
                    if del_exc.status != 404:
                        logger.warning(f"Failed to delete timed-out clone object '{clone_operation_name}': {del_exc.reason}")
                raise kopf.PermanentError(f"Clone {clone_operation_name} timed out.")
            raise # Re-raise the kopf.TemporaryError

    except ApiException as e:
            logger.error(f"API error checking clone '{clone_operation_name}' status: {e.reason}")
            raise kopf.TemporaryError(f"API error checking clone {clone_operation_name}", delay=clone_wait_delay) from e

    # --- Update Status --- ## VM exists, patched, and set to run
    # This part only runs if the VM was *just* created via the clone process
    # If the idempotency check handled an existing VM, the handler returned earlier.
    now = datetime.now(UTC)
    expiry = now + timedelta(milliseconds=timeout_ms)
    logger.info(f"Cyberdesk '{vm_name}' reconciled successfully (newly created), expires at {expiry.isoformat()}")

    # Use patch object provided by Kopf to update status safely
    # Ensure the 'cyberdesk_create' key exists if updating specific fields
    if "cyberdesk_create" not in patch.status:
         patch.status["cyberdesk_create"] = {}
    patch.status["cyberdesk_create"]["virtualMachineRef"] = vm_name
    patch.status["cyberdesk_create"]["startTime"] = now.isoformat()
    patch.status["cyberdesk_create"]["expiryTime"] = expiry.isoformat()
    patch.status["cyberdesk_create"]["lastPhase"] = "Created" # Changed from "Started" to reflect it was just created

    # Remove the old direct status fields if they exist from previous versions
    if "virtualMachineRef" in patch.status:
        del patch.status["virtualMachineRef"]
    if "startTime" in patch.status:
        del patch.status["startTime"]
    if "expiryTime" in patch.status:
        del patch.status["expiryTime"]


@kopf.on.field(KUBEVIRT_GROUP, KUBEVIRT_VERSION, KUBEVIRT_VMI_PLURAL, field="status.phase")
def vmi_phase_change(old: str | None, new: str | None, meta: dict, status: dict, **_: Dict[str, object]):
    """Sync Supabase when a VMI phase flips."""
    if new is None:
        return  # nothing to do
    if meta.get("labels", {}).get("app") != "cyberdesk":
        return  # not ours

    instance_id = meta["labels"].get("cyberdesk-instance")
    if not instance_id:
        logger.warning("VMI %s missing cyberdesk-instance label", meta.get("name"))
        return

    current_db = get_instance_status(instance_id)
    desired = VMI_PHASE_TO_SUPABASE_STATUS.get(KubeVirtVMIPhase(new), SupabaseInstanceStatus.ERROR).value

    if current_db != desired:
        update_instance_status(instance_id, new)


@kopf.on.delete(CYBERDESK_GROUP, CYBERDESK_VERSION, CYBERDESK_PLURAL)
def cyberdesk_delete(meta: dict, body: dict, **_: Dict[str, object]):
    """Tear down VM and its secret when *Cyberdesk* is deleted."""
    vm_name = body.get("status", {}).get("cyberdesk_create", {}).get("virtualMachineRef") or meta["name"]

    try:
        CUSTOM_OBJECTS_API.delete_namespaced_custom_object(
            KUBEVIRT_GROUP, KUBEVIRT_VERSION, KUBEVIRT_NAMESPACE, KUBEVIRT_VM_PLURAL, vm_name
        )
        CORE_V1_API.delete_namespaced_secret(f"cloud-init-{vm_name}", KUBEVIRT_NAMESPACE)
        logger.info("Deleted VM & secret for %s", vm_name)
    except kubernetes.client.rest.ApiException as exc:
        if exc.status not in (404, 410):
            raise kopf.TemporaryError("Cleanup failed, will retry", delay=15) from exc


@kopf.on.timer(CYBERDESK_GROUP, CYBERDESK_VERSION, CYBERDESK_PLURAL, interval=60)
def cyberdesk_timeout_check(body: dict, **_: Dict[str, object]):
    """Per‑resource timer: shut down VM once *expiryTime* passes."""
    expiry_str = body.get("status", {}).get("cyberdesk_create", {}).get("expiryTime")
    if not expiry_str:
        return

    if datetime.now(UTC) >= datetime.fromisoformat(expiry_str):
        logger.info("Cyberdesk %s expired — deleting", body["metadata"]["name"])
        CUSTOM_OBJECTS_API.delete_namespaced_custom_object(
            CYBERDESK_GROUP, CYBERDESK_VERSION, body["metadata"]["namespace"], CYBERDESK_PLURAL, body["metadata"]["name"]
        )