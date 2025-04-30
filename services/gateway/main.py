"""
cyberdesk_api.py

FastAPI micro-gateway that:

1. Serves the noVNC static front-end.
2. Proxies a browser WebSocket to a websockify instance (port 5901) in the VM pod.
3. Creates / deletes *Cyberdesk* custom resources via the Kubernetes API.
4. Proxies terminal commands to the desired VM, via the execDaemon.

Designed to run either:

* Inside a Kubernetes cluster (uses ServiceAccount & in-cluster DNS), **or**
* Locally, picking up ~/.kube/config for dev workflows. Requires manual port-forwarding for VNC.
"""

from __future__ import annotations

import asyncio
import logging
import os
import ssl
from pathlib import Path
from typing import Callable, Awaitable, Optional, List, Any
import httpx
import websockets
from fastapi import (
    FastAPI,
    WebSocket,
    WebSocketDisconnect,
    HTTPException,
    status,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from kubernetes import client, config
from kubernetes.client import ApiException, CustomObjectsApi, CoreV1Api
from pydantic import BaseModel, Field
from supabase import create_client, Client
from dotenv import load_dotenv
import json
import socket

# --------------------------------------------------------------------------- #
# Logging
# --------------------------------------------------------------------------- #

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s │ %(levelname)-8s │ %(name)s │ %(message)s",
)
LOG = logging.getLogger("cyberdesk")

# --------------------------------------------------------------------------- #
# Constants & Helpers
# --------------------------------------------------------------------------- #

HOURS = 60 * 60 * 1000  # milliseconds per hour
DEFAULT_TIMEOUT_MS: int = 24 * HOURS

CYBERDESK_GROUP = "cyberdesk.io"
CYBERDESK_VERSION = "v1alpha1"
CYBERDESK_PLURAL = "cyberdesks"
CYBERDESK_NAMESPACE = "cyberdesk-system"

VMI_NAMESPACE = "kubevirt"
GATEWAY_SERVICE_NAME = "gateway"
GATEWAY_NAMESPACE = CYBERDESK_NAMESPACE # Namespace where gateway service runs

# Add KubeVirt constants
KUBEVIRT_GROUP = "kubevirt.io"
KUBEVIRT_VERSION = "v1"
KUBEVIRT_VMI_PLURAL = "virtualmachineinstances"

# --------------------------------------------------------------------------- #
# Kubernetes client bootstrap
# --------------------------------------------------------------------------- #


def init_kube_clients() -> tuple[Optional[CustomObjectsApi], Optional[CoreV1Api]]:
    """Attempt to build a Kubernetes CustomObjectsApi, returning *None* on failure."""
    try:
        config.load_incluster_config()
        LOG.info("Loaded in-cluster Kubernetes config")
        return client.CustomObjectsApi(), client.CoreV1Api()
    except config.ConfigException:
        try:
            config.load_kube_config()
            LOG.info("Loaded local ~/.kube/config")
            return client.CustomObjectsApi(), client.CoreV1Api()
        except config.ConfigException as exc:
            LOG.warning("No Kubernetes configuration available: %s", exc)
            return None, None


K8S_CUSTOM_API, K8S_CORE_V1_API = init_kube_clients()

# --------------------------------------------------------------------------- #
# Supabase Client Setup
# --------------------------------------------------------------------------- #
# Get the directory where main.py is located
script_dir = Path(__file__).resolve().parent
# Construct the path to the .env file in that same directory
dotenv_path = script_dir / ".env"

# Load using that specific path
load_dotenv(dotenv_path=dotenv_path, override=True)

SUPABASE_URL: Optional[str] = os.environ.get("SUPABASE_URL")
SUPABASE_KEY: Optional[str] = os.environ.get("SUPABASE_KEY")
SUPABASE_CLIENT: Optional[Client] = None

if SUPABASE_URL and SUPABASE_KEY:
    try:
        SUPABASE_CLIENT = create_client(SUPABASE_URL, SUPABASE_KEY)
        LOG.info("Successfully initialized Supabase client.")
    except Exception as e:
        LOG.critical(f"Failed to initialize Supabase client: {e}")
        # Depending on requirements, you might want to prevent startup
        # raise RuntimeError(f"Failed to initialize Supabase client: {e}")
else:
    LOG.warning("SUPABASE_URL or SUPABASE_KEY environment variables not set. Supabase integration disabled.")


# --------------------------------------------------------------------------- #
# Pydantic DTOs
# --------------------------------------------------------------------------- #


class CyberdeskCreateRequest(BaseModel):
    """Payload for POST /cyberdesk/{vm_id}"""

    timeout_ms: int = Field(
        default=DEFAULT_TIMEOUT_MS, alias="timeoutMs", ge=60_000
    )

class CommandRequest(BaseModel):
    """Payload for POST /cyberdesk/{vm_id}/execute-command"""
    command: str

# --- Response Models ---

class CyberdeskCreateResponse(BaseModel):
    """Response for POST /cyberdesk/{vm_id}"""
    id: str

class StatusMessageResponse(BaseModel):
    """Generic response model for status and message."""
    status: str
    message: str

class CyberdeskReadyResponse(StatusMessageResponse):
    """Response for POST /cyberdesk/{vm_id}/ready"""
    stream_url: str

class VMCommandExecutionResponse(BaseModel):
    """Schema for the response received *from* the VM's /execute-command endpoint."""
    args: List[str]
    return_code: int
    stdout: str
    stderr: str
    duration_s: float

class GatewayCommandResponse(BaseModel):
    """Response for POST /cyberdesk/{vm_id}/execute-command"""
    status: str
    vm_status_code: int
    vm_response: VMCommandExecutionResponse

class HealthCheckResponse(BaseModel):
    """Response for GET /healthz"""
    status: str

class VmHealthCheckResponse(BaseModel):
    """Response for GET /vm/healthcheck/{vmid}"""
    status: str  # Status reported by the VM's health endpoint
    vm_status_code: int # The HTTP status code received from the VM


# --------------------------------------------------------------------------- #
# FastAPI application
# --------------------------------------------------------------------------- #

app = FastAPI(title="Cyberdesk API Gateway", version="1.0")

# Optional: allow the browser UI to be hosted from another domain.
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CYBERDESK_CORS_ALLOW_ORIGINS", "*").split(","),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static noVNC artefacts live relative to this file.
BASE_DIR = Path(__file__).resolve().parent
NOVNC_DIR = BASE_DIR / "noVNC"
app.mount("/static", StaticFiles(directory=NOVNC_DIR), name="static")


# --------------------------------------------------------------------------- #
# Routes – HTML / root
# --------------------------------------------------------------------------- #


@app.get("/vnc/{vm_id}", include_in_schema=False)
async def serve_novnc(vm_id: str) -> FileResponse:
    """
    Serve the main noVNC HTML page.

    The client-side JavaScript will subsequently establish a WebSocket
    back to `/vnc/ws/{vm_id}`.
    """
    return FileResponse(NOVNC_DIR / "vnc.html")


# --------------------------------------------------------------------------- #
# WebSocket proxy
# --------------------------------------------------------------------------- #

async def _relay(
    recv: Callable[[], Awaitable[bytes]],
    send: Callable[[bytes], Awaitable[None]],
) -> None:
    """
    Copy bytes from *recv* to *send* until EOF or a normal WebSocket shutdown.
    """
    try:
        while True:
            await send(await recv())
    except (WebSocketDisconnect, websockets.exceptions.ConnectionClosed):
        # A graceful close on either side ends the task.
        return


@app.websocket("/vnc/ws/{vm_id}")
async def proxy_vnc(websocket: WebSocket, vm_id: str) -> None:
    """Proxy WebSocket to the target VMI's VNC port.

    Connects via VMI IP if running in-cluster.
    Connects via host.docker.internal:5901 if running locally
    (requires manual `kubectl port-forward pod/<vmi-pod> 5901:5901`).
    """
    await websocket.accept()
    LOG.info("VNC WebSocket opened for instance ID: %s", vm_id)

    target_uri: Optional[str] = None
    target_port = 5901 # Standard VNC port

    try:
        # --- Step 1: Determine Environment ---
        token_path = Path("/var/run/secrets/kubernetes.io/serviceaccount/token")
        in_cluster = token_path.exists()
        LOG.info(f"Running in-cluster: {in_cluster}")

        # --- Step 2: Get CR & VMI for validation (and IP if in-cluster) ---
        k8s_custom = require_k8s() # Ensure K8S client is available
        vm_name: Optional[str] = None
        vmi_ip: Optional[str] = None

        try:
            cr = k8s_custom.get_namespaced_custom_object(
                group=CYBERDESK_GROUP,
                version=CYBERDESK_VERSION,
                namespace=CYBERDESK_NAMESPACE,
                plural=CYBERDESK_PLURAL,
                name=vm_id,
            )
            vm_name = cr.get("status", {}).get("cyberdesk_create", {}).get("virtualMachineRef")
            if not vm_name:
                raise ValueError(f"virtualMachineRef not found in status for Cyberdesk {vm_id}")
            LOG.info("Found virtualMachineRef '%s' for instance %s", vm_name, vm_id)

        except ApiException as e:
            if e.status == 404:
                raise ValueError(f"Cyberdesk CR '{vm_id}' not found.") from e
            else:
                raise ValueError(f"API Error fetching Cyberdesk CR '{vm_id}': {e.reason}") from e
        except ValueError as e:
            LOG.error(str(e))
            await websocket.close(code=1011, reason=str(e))
            return

        try:
            vmi = k8s_custom.get_namespaced_custom_object(
                group=KUBEVIRT_GROUP,
                version=KUBEVIRT_VERSION,
                namespace=VMI_NAMESPACE,
                plural=KUBEVIRT_VMI_PLURAL,
                name=vm_name,
            )
            interfaces = vmi.get('status', {}).get('interfaces', [])
            vmi_ip = interfaces[0].get('ipAddress') if interfaces else None
            vmi_phase = vmi.get('status', {}).get('phase')

            if vmi_phase != 'Running':
                raise ValueError(f"Target VMI '{vm_name}' is not Running (phase: {vmi_phase}).")
            if in_cluster and not vmi_ip:
                # Only strictly need IP if in-cluster
                raise ValueError(f"Target VMI '{vm_name}' is Running but has no IP address (needed for in-cluster connection)." )
            LOG.info("Target VMI '%s' is Running. IP: %s", vm_name, vmi_ip if vmi_ip else "N/A (local)")

        except ApiException as e:
            if e.status == 404:
                 raise ValueError(f"VMI '{vm_name}' not found.") from e
            else:
                 raise ValueError(f"API Error fetching VMI '{vm_name}': {e.reason}") from e
        except ValueError as e:
            LOG.error(str(e))
            await websocket.close(code=1011, reason=str(e))
            return

        # --- Step 3: Determine Target URI based on environment ---
        if in_cluster:
            if not vmi_ip: # Should have been caught above, but defensive check
                 raise ValueError("Logic error: In-cluster but VMI IP is missing.")
            target_uri = f"ws://{vmi_ip}:{target_port}"
            LOG.info("Connecting via VMI IP (in-cluster): %s", target_uri)
        else:
            # Assume manual port-forward `kubectl port-forward pod/<vmi-pod> 5901:5901` is running
            target_uri = f"ws://host.docker.internal:{target_port}"
            LOG.info("Connecting via Docker host (local): %s (Requires manual port-forward)", target_uri)

        # --- Step 4: Establish connection and relay ---
        LOG.info("Attempting WebSocket connection to VMI VNC at %s", target_uri)
        async with websockets.connect(target_uri, ping_interval=None, open_timeout=10) as vmi_ws:
            LOG.info("Successfully connected to VMI VNC at %s", target_uri)

            # Start two tasks to relay messages in both directions
            consumer_task = asyncio.create_task(
                _relay(websocket.receive_bytes, vmi_ws.send)
            )
            producer_task = asyncio.create_task(
                _relay(vmi_ws.recv, websocket.send_bytes) # type: ignore[arg-type] -- websockets.recv() returns Data
            )

            # Wait for either task to complete (or raise an exception)
            done, pending = await asyncio.wait(
                [consumer_task, producer_task],
                return_when=asyncio.FIRST_COMPLETED,
            )

            # Cancel pending tasks to clean up resources
            for task in pending:
                task.cancel()

            # Raise exceptions if any task failed
            for task in done:
                if task.exception():
                    raise task.exception()

    except (websockets.exceptions.ConnectionClosedError, websockets.exceptions.ConnectionClosedOK) as e:
        LOG.info("VNC WebSocket connection closed cleanly: %s", e)
    except WebSocketDisconnect as e:
        LOG.info("Browser WebSocket disconnected: %s", e.code)
    except Exception as e:
        LOG.error("VNC proxy error: %s", e, exc_info=True)
        # Attempt to close the browser WebSocket with an error code
        try:
            await websocket.close(code=1011, reason=f"Proxy error: {e}")
        except RuntimeError: # Handle cases where socket might already be closed
            pass
    finally:
        LOG.info("VNC WebSocket closed for instance ID: %s", vm_id)


# --------------------------------------------------------------------------- #
# Cyberdesk custom-resource endpoints
# --------------------------------------------------------------------------- #


def require_k8s() -> CustomObjectsApi:
    """Return a live CustomObjectsApi or raise 503 HTTPException."""
    if K8S_CUSTOM_API is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Kubernetes client not configured.",
        )
    return K8S_CUSTOM_API

def require_k8s_core() -> CoreV1Api:
    """Return a live CoreV1Api or raise 503 HTTPException."""
    if K8S_CORE_V1_API is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Kubernetes CoreV1Api client not configured.",
        )
    return K8S_CORE_V1_API

def require_supabase() -> Client:
    """Return a live Supabase client or raise 503 HTTPException."""
    
    if SUPABASE_CLIENT is None:
         raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Supabase client not configured (missing SUPABASE_URL/KEY env vars?).",
        )
    return SUPABASE_CLIENT

# --- Helper Function to Update Supabase ---
async def update_supabase_instance(vm_id: str, stream_url: str):
    """Updates the Supabase instance entry with stream URL and status."""
    supabase_client = require_supabase()
    try:
        # Run blocking Supabase call in a separate thread
        # Assign the entire response object
        response = await asyncio.to_thread(
            lambda: supabase_client.table("cyberdesk_instances")
            .update({"status": "running", "stream_url": stream_url})
            .eq("id", vm_id)
            .execute()
        )
        # Log the actual response structure for clarity (can be removed later)
        LOG.info(f"Supabase raw response object for {vm_id}: {response}")

        # Access the data list via response.data
        updated_data = response.data
        # Access count via response.count (though not strictly needed for the check here)
        # updated_count = response.count

        LOG.info(f"Supabase update response for {vm_id}: data={updated_data}, count={getattr(response, 'count', 'N/A')}")

        # Check if the update was successful using the actual data list
        if isinstance(updated_data, list) and len(updated_data) > 0 and updated_data[0]:
            LOG.info(f"Successfully updated Supabase for instance {vm_id}")
            return True
        else:
            # This might happen if the row doesn't exist or based on Supabase return preferences
            LOG.warning(f"Supabase update for instance {vm_id} completed, but response data indicates no rows updated or an unexpected format: {updated_data}")
            return False
    except Exception as e:
        LOG.exception(f"Error updating Supabase for instance {vm_id}: {e}")
        return False

@app.post(
    "/cyberdesk/{vm_id}",
    status_code=status.HTTP_201_CREATED,
    response_model=CyberdeskCreateResponse
)
async def create_cyberdesk(vm_id: str, payload: CyberdeskCreateRequest):
    """Create a Cyberdesk CR in the cluster."""
    api = require_k8s()

    body = {
        "apiVersion": f"{CYBERDESK_GROUP}/{CYBERDESK_VERSION}",
        "kind": "Cyberdesk",
        "metadata": {"name": vm_id, "namespace": CYBERDESK_NAMESPACE},
        "spec": {"timeoutMs": payload.timeout_ms},
    }

    try:
        resp = await asyncio.to_thread(
            api.create_namespaced_custom_object,
            group=CYBERDESK_GROUP,
            version=CYBERDESK_VERSION,
            namespace=CYBERDESK_NAMESPACE,
            plural=CYBERDESK_PLURAL,
            body=body,
        )
        return {"id": resp["metadata"]["name"]}
    except ApiException as exc:
        LOG.error("Kubernetes API error: %s", exc, exc_info=False)
        if exc.status == 409:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Already exists") from exc
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=exc.reason) from exc


@app.post(
    "/cyberdesk/{vm_id}/stop",
    status_code=status.HTTP_200_OK,
    response_model=StatusMessageResponse
)
async def stop_cyberdesk(vm_id: str):
    """Delete a Cyberdesk CR from the cluster."""
    api = require_k8s()

    try:
        await asyncio.to_thread(
            api.delete_namespaced_custom_object,
            group=CYBERDESK_GROUP,
            version=CYBERDESK_VERSION,
            namespace=CYBERDESK_NAMESPACE,
            plural=CYBERDESK_PLURAL,
            name=vm_id,
            body=client.V1DeleteOptions(),
        )
        # Return a dictionary matching the response model
        return {"status": "success", "message": f"Deletion of '{vm_id}' initiated."}
    except ApiException as exc:
        LOG.error("Kubernetes API error: %s", exc, exc_info=False)
        if exc.status == 404:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found") from exc
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=exc.reason) from exc

# --- NEW Endpoint ---
@app.post(
    "/cyberdesk/{vm_id}/ready",
    status_code=status.HTTP_200_OK,
    response_model=CyberdeskReadyResponse
)
async def cyberdesk_ready(vm_id: str):
    """
    Signal that a VM is ready. Updates Supabase with the stream URL.
    """
    LOG.info(f"Received ready signal for VM: {vm_id}")
    # 2. Construct Stream URL
    # Assuming default HTTP port 80 for the gateway service
    stream_url = f"https://gateway.cyberdesk.io/vnc/{vm_id}"
    LOG.info(f"Constructed stream URL for {vm_id}: {stream_url}")

    # 3. Update Supabase
    success = await update_supabase_instance(vm_id, stream_url)

    if success:
        LOG.info(f"Successfully processed ready signal for {vm_id}")
        # Return a dictionary matching the response model
        return {"status": "success", "message": f"Instance {vm_id} marked as running.", "stream_url": stream_url}
    else:
        LOG.error(f"Failed to update Supabase for {vm_id} after getting IP.")
        # Indicate failure - maybe the instance ID was wrong or DB issue
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update instance status in database for {vm_id}."
        )

@app.post(
    "/cyberdesk/{vm_id}/execute-command",
    response_model=GatewayCommandResponse
)
async def execute_vm_command(vm_id: str, payload: CommandRequest):
    """
    Sends a command string to the execute-command endpoint of the specified VM
    using the proxy helper.
    """
    command_port = 8000
    command_path = "execute-command" # Path on the VM service
    command_timeout = 30.0 # Longer timeout for potential command execution

    command_to_execute = payload.command
    # IMPORTANT: Ensure the receiving service expects this JSON structure
    request_payload = {"cmd": command_to_execute}

    LOG.info(f"Attempting command execution for VM {vm_id}: '{command_to_execute[:80]}...'")

    try:
        status_code, response_json = await _proxy_request_to_vm(
            vmid=vm_id,
            port=command_port,
            path=command_path,
            method="POST",
            json_payload=request_payload,
            timeout=command_timeout
        )

        # Check if the VM's command endpoint returned a success status
        if 200 <= status_code < 300:
            LOG.info(f"Command execution for {vm_id} successful: {status_code}, Response: { response_json}")
            return {
                "status": "success",
                "vm_status_code": status_code,
                "vm_response": {
                    "args": response_json["args"],
                    "return_code": response_json["return_code"],
                    "stdout": response_json["stdout"],
                    "stderr": response_json["stderr"],
                    "duration_s": response_json["duration_s"]
                }
            }
        else:
            # VM is reachable, but the command endpoint returned an error
            LOG.error(f"VM {vm_id} command execution failed with status {status_code}.")
            raise HTTPException(
                status_code=502, # Bad Gateway, as the upstream VM endpoint failed
                detail=f"VM {vm_id} command execution failed: {status_code}",
                headers={"X-VM-Status-Code": str(status_code)}
            )

    except HTTPException as e:
         # Re-raise known HTTP exceptions from the proxy helper
         LOG.error(f"Command execution failed for {vm_id} due to proxy error: {e.status_code} - {e.detail}")
         raise e
    except Exception as e:
        # Catch any other unexpected errors during the process
        LOG.exception(f"Unexpected error during command execution processing for {vm_id}: {e}")
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred during command execution for VM {vm_id}")


# --------------------------------------------------------------------------- #
# Liveness / readiness
# --------------------------------------------------------------------------- #


@app.get("/healthz", response_model=HealthCheckResponse)
async def health_check():
    """Kubernetes livenessProbe target."""
    return {"status": "ok"}

@app.get("/vm/healthcheck/{vmid}", response_model=VmHealthCheckResponse)
async def vm_health_check(vmid: str):
    """
    Performs a health check on the specified VM instance using the proxy helper.
    """
    health_port = 8000
    health_path = "health"

    try:
        status_code, response_json = await _proxy_request_to_vm(
            vmid=vmid,
            port=health_port,
            path=health_path,
            method="GET",
            timeout=10.0
        )

        # Check if the VM's health endpoint returned a success status
        if 200 <= status_code < 300:
            LOG.info(f"Health check for {vmid} successful: {status_code}")
            return {
                "status": "ok",
                "vm_status_code": status_code
            }
        else:
            # VM is reachable, but reported unhealthy
            LOG.warning(f"VM {vmid} health check failed with status {status_code}")
            raise HTTPException(
                status_code=502, # Bad Gateway, as the upstream VM is unhealthy
                detail=f"VM {vmid} health check reported failure: {status_code}",
                headers={"X-VM-Status-Code": str(status_code)}
            )

    except HTTPException as e:
         # Re-raise known HTTP exceptions from the proxy helper
         # (e.g., 404 if pod not found, 503 if connection failed, 504 timeout)
         LOG.error(f"Health check failed for {vmid} due to proxy error: {e.status_code} - {e.detail}")
         raise e
    except Exception as e:
        # Catch any other unexpected errors during the process
        LOG.exception(f"Unexpected error during health check processing for {vmid}: {e}")
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred during health check for VM {vmid}")

# --- Generic VM Pod Communication Helper ---

async def _proxy_request_to_vm(
    vmid: str,
    port: int,
    path: str,
    method: str = "GET",
    json_payload: Optional[dict] = None,
    timeout: float = 10.0
) -> tuple[int, Any]:
    """
    Sends an HTTP request to a specific port/path on the VM pod.

    Handles routing via internal DNS (in-cluster) or K8s API proxy (local).
    Finds the correct virt-launcher pod name when running locally.

    Args:
        vmid: The target Virtual Machine ID.
        port: The target port on the VM pod.
        path: The target URL path on the VM pod (e.g., "health", "execute-command").
        method: HTTP method ("GET", "POST", etc.).
        json_payload: Optional dictionary to send as JSON body (for POST/PUT).
        timeout: Request timeout in seconds.

    Returns:
        A tuple containing (status_code, response_body). The response_body
        will be a parsed JSON object (dict/list) if possible, otherwise raw text.

    Raises:
        HTTPException: If the request fails due to connection errors, timeouts,
                       API errors, non-2xx VM responses, or pod lookup issues.
    """
    vm_namespace = "kubevirt"
    path = path.lstrip('/') # Ensure path doesn't start with /

    # Check if running in-cluster
    token_path = Path("/var/run/secrets/kubernetes.io/serviceaccount/token")
    in_cluster = token_path.exists()

    if in_cluster:
        # --- In-Cluster Logic (Get VMI IP) ---
        LOG.info(f"Proxying {method} to VM {vmid} (in-cluster) via IP lookup -> :{port}/{path}")
        k8s_custom = require_k8s()
        vm_name: Optional[str] = None
        vmi_ip: Optional[str] = None
        target_url: Optional[str] = None

        try:
            # 1. Get CR to find VM name
            try:
                cr = k8s_custom.get_namespaced_custom_object(
                    group=CYBERDESK_GROUP,
                    version=CYBERDESK_VERSION,
                    namespace=CYBERDESK_NAMESPACE,
                    plural=CYBERDESK_PLURAL,
                    name=vmid, # vmid is the instance ID here
                )
                vm_name = cr.get("status", {}).get("cyberdesk_create", {}).get("virtualMachineRef")
                if not vm_name:
                    raise ValueError(f"virtualMachineRef not found in status for Cyberdesk {vmid}")
                LOG.debug(f"Found virtualMachineRef '{vm_name}' for instance {vmid}")
            except ApiException as e:
                if e.status == 404:
                    raise ValueError(f"Cyberdesk CR '{vmid}' not found.") from e
                else:
                    raise ValueError(f"API Error fetching Cyberdesk CR '{vmid}': {e.reason}") from e

            # 2. Get VMI to find IP address
            try:
                vmi = k8s_custom.get_namespaced_custom_object(
                    group=KUBEVIRT_GROUP,
                    version=KUBEVIRT_VERSION,
                    namespace=vm_namespace, # Defined earlier in function
                    plural=KUBEVIRT_VMI_PLURAL,
                    name=vm_name,
                )
                interfaces = vmi.get('status', {}).get('interfaces', [])
                vmi_ip = interfaces[0].get('ipAddress') if interfaces else None
                vmi_phase = vmi.get('status', {}).get('phase')

                if vmi_phase != 'Running':
                     raise ValueError(f"Target VMI '{vm_name}' is not Running (phase: {vmi_phase}).")
                if not vmi_ip:
                     raise ValueError(f"Target VMI '{vm_name}' is Running but has no IP address.")
                LOG.debug(f"Found target VMI IP '{vmi_ip}' for VM '{vm_name}'")
            except ApiException as e:
                if e.status == 404:
                     raise ValueError(f"VMI '{vm_name}' not found.") from e
                else:
                     raise ValueError(f"API Error fetching VMI '{vm_name}': {e.reason}") from e

            # 3. Construct Target URL
            target_url = f"http://{vmi_ip}:{port}/{path}"
            LOG.debug(f"Target URL (in-cluster, via IP): {target_url}")

        except ValueError as e:
             # Handle all lookup errors gracefully
             LOG.error(f"Failed lookup for VM {vmid} proxy target: {e}")
             raise HTTPException(status_code=404, detail=f"Target VM or its resources not found/ready: {e}")

        # --- Make Request using IP-based URL ---
        async with httpx.AsyncClient(timeout=timeout) as client:
            try:
                response = await client.request(
                    method,
                    target_url,
                    json=json_payload # httpx handles None payload correctly
                )
                response.raise_for_status() # Raise exception for 4xx/5xx responses

                # Attempt to parse response as JSON
                try:
                    json_response = response.json()
                    LOG.debug(f"Successfully parsed JSON response from {target_url}")
                    return response.status_code, json_response
                except Exception as json_exc: # Catches JSONDecodeError and others
                    LOG.warning(f"Failed to parse response from {target_url} as JSON: {json_exc}. Returning raw text.")
                    return response.status_code, response.text
            except httpx.TimeoutException:
                LOG.error(f"Timeout connecting to VM {vmid} (in-cluster) at {target_url}")
                raise HTTPException(status_code=504, detail=f"Request timed out connecting to VM {vmid}")
            except httpx.ConnectError as e:
                LOG.error(f"Connection error to VM {vmid} (in-cluster) at {target_url}: {e}")
                raise HTTPException(status_code=503, detail=f"Could not connect to VM {vmid} (DNS issue?): {e}")
            except Exception as e:
                LOG.exception(f"Unexpected error during httpx request to VM {vmid} (in-cluster): {e}")
                raise HTTPException(status_code=500, detail=f"Unexpected error connecting to VM {vmid}")

    else:
        # --- Local Logic (Kubernetes API Proxy) ---
        LOG.info(f"Proxying {method} to VM {vmid} (local) via K8s API -> :{port}/{path}")
        core_api = require_k8s_core() # Ensures K8s client is loaded
        k8s_custom = require_k8s()   # Need custom objects API as well
        api_client = core_api.api_client # Get the underlying ApiClient

        # 1. Find the VM Name from CR
        vm_name: Optional[str] = None
        try:
            cr = k8s_custom.get_namespaced_custom_object(
                group=CYBERDESK_GROUP,
                version=CYBERDESK_VERSION,
                namespace=CYBERDESK_NAMESPACE,
                plural=CYBERDESK_PLURAL,
                name=vmid,
            )
            vm_name = cr.get("status", {}).get("cyberdesk_create", {}).get("virtualMachineRef")
            if not vm_name:
                raise ValueError(f"virtualMachineRef not found in status for Cyberdesk {vmid}")
            LOG.debug(f"Found virtualMachineRef '{vm_name}' for instance {vmid}")
        except ApiException as e:
            if e.status == 404:
                raise HTTPException(status_code=404, detail=f"Cyberdesk CR '{vmid}' not found.") from e
            else:
                raise HTTPException(status_code=500, detail=f"API Error fetching Cyberdesk CR '{vmid}': {e.reason}") from e
        except ValueError as e:
            LOG.error(str(e))
            raise HTTPException(status_code=404, detail=str(e))

        # 2. Find the Pod Name using the VM Name by checking annotations
        pod_name: Optional[str] = None
        running_pod_found = False
        try:
            LOG.debug(f"Listing pods in namespace '{vm_namespace}' to find one for VM '{vm_name}'.")
            # List all pods in the namespace - might need adjustment if too many pods
            pod_list_response = await asyncio.to_thread(
                core_api.list_namespaced_pod,
                namespace=vm_namespace,
                _request_timeout=10 # Increase timeout slightly for list operation
            )
            pods = pod_list_response.items
            LOG.debug(f"Found {len(pods)} pods in namespace. Iterating to find match.")

            for pod in pods:
                annotations = pod.metadata.annotations
                pod_domain = annotations.get("kubevirt.io/domain")
                
                # Check if annotation matches the target VM name
                if pod_domain == vm_name:
                    pod_name = pod.metadata.name
                    pod_phase = pod.status.phase
                    LOG.debug(f"Found candidate pod '{pod_name}' with matching domain annotation. Phase: {pod_phase}")
                    if pod_phase == "Running":
                        LOG.info(f"Found running virt-launcher pod '{pod_name}' for VM '{vm_name}'.")
                        running_pod_found = True
                        break # Found the running pod we need
                    else:
                        # Found a pod, but it's not running. Keep looking in case
                        # there's an older non-running one and a newer running one somehow.
                         LOG.warning(f"Found pod {pod_name} for VM {vm_name}, but phase is {pod_phase}. Continuing search.")
                         pod_name = None # Reset pod_name if not running
                
            if not running_pod_found:
                 # If loop finishes and we didn't find a running pod
                 if pod_name:
                      # We found a pod but it wasn't running
                      raise HTTPException(status_code=503, detail=f"VM pod {pod_name} for {vm_name} found but not in Running phase.")
                 else:
                      # We didn't find any pod with the matching annotation
                      LOG.warning(f"No virt-launcher pod found with annotation kubevirt.io/domain={vm_name}")
                      raise HTTPException(status_code=404, detail=f"VM pod for {vm_name} not found.")

        except ApiException as e:
            LOG.error(f"K8s API error listing pods for {vm_name}: {e.status} {e.reason}")
            raise HTTPException(status_code=500, detail=f"API error listing pods for VM {vm_name}: {e.reason}")

        if not pod_name:
             # Should be caught above, but defensive check
             raise HTTPException(status_code=500, detail="Could not determine pod name")

        # 3. Make the Proxied Request (using the found pod_name)
        api_proxy_path = f"/api/v1/namespaces/{vm_namespace}/pods/{pod_name}:{port}/proxy/{path}"
        LOG.debug(f"Attempting {method} via K8s API proxy path: {api_proxy_path}")

        try:
            # Prepare arguments for call_api
            call_api_args = {
                'resource_path': api_proxy_path,
                'method': method,
                'auth_settings': ['BearerToken'],
                'response_type': 'str', # Expect text back
                '_request_timeout': timeout
            }
            header_params = {}
            # Set body and Content-Type for methods that have payloads
            if json_payload is not None and method in ["POST", "PUT", "PATCH"]:
                call_api_args['body'] = json_payload
                header_params['Content-Type'] = api_client.select_header_content_type(['application/json'])
                call_api_args['header_params'] = header_params

            # Run synchronous call_api in thread
            response_data = await asyncio.to_thread(
                api_client.call_api,
                **call_api_args
            )

            # response_data = (data, status_code, headers)
            status_code = response_data[1]
            response_text = response_data[0]
            LOG.debug(f"K8s API proxy request to VM {vmid} completed with status: {status_code}")
            LOG.debug(f"Response data: {response_data}...")
            # Attempt to parse response as JSON, fall back to text
            try:
                corrected_json_string = response_text.replace("'", '"') # Basic, might break
                json_response = json.loads(corrected_json_string)
                LOG.debug(f"Successfully parsed JSON response from K8s proxy for {vmid}")
                return status_code, json_response
            except json.JSONDecodeError:
                LOG.warning(f"Failed to parse response from K8s proxy for {vmid} as JSON. Returning raw text. {response_text[:100]}...")
                return status_code, response_text

        except ApiException as e:
            LOG.error(f"K8s API error during proxy request to {vmid}: {e.status} {e.reason} - Body: {e.body}")
            # Map common K8s API errors during proxying
            if e.status == 404:
                 detail = f"Proxy path not found on pod '{pod_name}' (or pod disappeared)."
                 http_status = 502 # Treat as bad gateway, pod endpoint issue
            elif e.status == 503 or e.status == 504:
                detail = f"Could not connect to Pod '{pod_name}' via K8s API proxy: {e.reason}"
                http_status = 503
            elif e.status == 401 or e.status == 403:
                detail = f"Permission denied accessing K8s pod proxy: {e.reason}"
                http_status = 500
            else:
                 detail = f"Kubernetes API error during proxy: {e.reason}"
                 http_status = 500
            raise HTTPException(status_code=http_status, detail=detail)
        except asyncio.TimeoutError:
             LOG.error(f"Timeout during K8s API proxy request to {vmid}")
             raise HTTPException(status_code=504, detail=f"Request via K8s API timed out for VM {vmid}")
        except Exception as e:
            LOG.exception(f"Unexpected error during K8s API proxy request to {vmid}: {e}")
            raise HTTPException(status_code=500, detail=f"Unexpected error during proxy request to VM {vmid}")

