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

# Template search paths (first wins)
VM_TEMPLATE_PATHS = (
    Path("/app/kubevirt-vm-cr.yaml"),                                      # prod: mounted ConfigMap
    Path(__file__).parent.parent / "tests" / "test-vm-template.yaml",  # dev / unit‑tests
)
USER_DATA_TEMPLATE_PATH = Path(__file__).parent.parent / "tests" / "test-user-data.yaml"

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
    COMPLETED = "completed"
    ERROR = "error"


# Static mapping between the two state machines -----------------------------
VMI_PHASE_TO_SUPABASE_STATUS: Dict[KubeVirtVMIPhase, SupabaseInstanceStatus] = {
    KubeVirtVMIPhase.PENDING: SupabaseInstanceStatus.PENDING,
    KubeVirtVMIPhase.SCHEDULING: SupabaseInstanceStatus.PENDING,
    KubeVirtVMIPhase.SCHEDULED: SupabaseInstanceStatus.PENDING,
    KubeVirtVMIPhase.RUNNING: SupabaseInstanceStatus.RUNNING,
    KubeVirtVMIPhase.SUCCEEDED: SupabaseInstanceStatus.COMPLETED,
    KubeVirtVMIPhase.FAILED: SupabaseInstanceStatus.ERROR,
    KubeVirtVMIPhase.UNKNOWN: SupabaseInstanceStatus.ERROR,
}

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
# Templating helpers ---------------------------------------------------------
# ---------------------------------------------------------------------------

def _load_first_existing(path_candidates: tuple[Path, ...]) -> str:
    """Return content of the first existing file from *path_candidates*."""
    for path in path_candidates:
        try:
            if path.exists():
                content = path.read_text()
                logger.info("Loaded template from %s", path)
                return content
        except Exception as exc:  # noqa: BLE001 — continue to next candidate
            logger.warning("Reading %s failed: %s", path, exc)
    raise kopf.PermanentError("No template file found in provided paths")


USER_DATA_TEMPLATE: str = os.getenv("USER_DATA_TEMPLATE") or _load_first_existing((USER_DATA_TEMPLATE_PATH,))
VM_TEMPLATE_RAW: str = _load_first_existing(VM_TEMPLATE_PATHS)

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
# Kubernetes helpers ---------------------------------------------------------
# ---------------------------------------------------------------------------

def create_cloudinit_secret(vm_name: str, namespace: str) -> None:
    """Create or ensure a cloud‑init secret containing *USER_DATA_TEMPLATE*."""
    secret_name = f"cloud-init-{vm_name}"

    secret_body = kubernetes.client.V1Secret(
        metadata=kubernetes.client.V1ObjectMeta(name=secret_name, namespace=namespace, labels={"managed-by": MANAGED_BY}),
        type="Opaque",
        string_data={"userdata": USER_DATA_TEMPLATE},
    )

    try:
        CORE_V1_API.create_namespaced_secret(namespace=namespace, body=secret_body)
        logger.info("Created cloud‑init secret %s in %s", secret_name, namespace)
    except kubernetes.client.rest.ApiException as exc:
        if exc.status == 409:  # already exists
            logger.debug("Secret %s already exists", secret_name)
        else:
            raise


# ---------------------------------------------------------------------------
# VM template rendering ------------------------------------------------------
# ---------------------------------------------------------------------------

def render_vm_manifest(vm_name: str) -> dict:
    """Return a KubeVirt VM manifest for *vm_name* based on ``VM_TEMPLATE_RAW``."""
    rendered_yaml = string.Template(VM_TEMPLATE_RAW).substitute(
        vm_name=vm_name,
        cyberdesk_name=vm_name,
        managed_by=MANAGED_BY,
    )
    return yaml.safe_load(rendered_yaml)

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

@kopf.on.startup()
def configure_kopf(settings: OperatorSettings, **_: Dict[str, object]) -> None:
    """Tune watch timeouts to avoid idle disconnects seen in some clusters."""
    settings.watching.server_timeout = 210  # seconds
    logger.info("Kopf watch server_timeout set to %s", settings.watching.server_timeout)


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


@kopf.on.create(CYBERDESK_GROUP, CYBERDESK_VERSION, CYBERDESK_PLURAL)
def cyberdesk_create(spec: dict, meta: dict, status: dict, **_: Dict[str, object]):  # noqa: WPS231 — complex but explicit
    """Reconcile a new *Cyberdesk* → create VM & cloud‑init secret."""
    vm_name = meta["name"]
    timeout_ms = spec.get("timeoutMs", 3_600_000)  # default: 1h

    # Idempotency: bail if VM exists already
    try:
        CUSTOM_OBJECTS_API.get_namespaced_custom_object(
            KUBEVIRT_GROUP, KUBEVIRT_VERSION, KUBEVIRT_NAMESPACE, KUBEVIRT_VM_PLURAL, vm_name
        )
        logger.info("VM %s already exists — skipping creation", vm_name)
        return {"virtualMachineRef": vm_name}
    except kubernetes.client.rest.ApiException as exc:
        if exc.status != 404:
            raise kopf.TemporaryError("VM existence check failed", delay=10) from exc

    # Ensure cloud‑init secret exists before creating the VM -----------------
    create_cloudinit_secret(vm_name, KUBEVIRT_NAMESPACE)

    vm_manifest = render_vm_manifest(vm_name)
    CUSTOM_OBJECTS_API.create_namespaced_custom_object(
        KUBEVIRT_GROUP, KUBEVIRT_VERSION, KUBEVIRT_NAMESPACE, KUBEVIRT_VM_PLURAL, vm_manifest
    )

    now = datetime.now(UTC)
    expiry = now + timedelta(milliseconds=timeout_ms)
    logger.info("VM %s created, expires at %s", vm_name, expiry.isoformat())

    return {"virtualMachineRef": vm_name, "startTime": now.isoformat(), "expiryTime": expiry.isoformat()}


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