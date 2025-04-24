"""
cyberdesk_api.py

FastAPI micro-gateway that:

1. Serves the noVNC static front-end.
2. Proxies a browser WebSocket to the KubeVirt VNC sub-resource.
3. Creates / deletes *Cyberdesk* custom resources via the Kubernetes API.
4. Proxies terminal commands to the desired VM, via the execDaemon.

Designed to run either:

* Inside a Kubernetes cluster (uses ServiceAccount & in-cluster DNS), **or**
* Locally, picking up ~/.kube/config for dev workflows.
"""

from __future__ import annotations

import asyncio
import logging
import os
import ssl
from pathlib import Path
from typing import Callable, Awaitable, Optional
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

class CommandExecuteResponse(BaseModel):
    """Response for POST /cyberdesk/{vm_id}/execute-command"""
    status: str
    vm_status_code: int
    vm_response: str # Or consider Union[str, dict, list] if VM response can vary

class HealthCheckResponse(BaseModel):
    """Response for GET /healthz"""
    status: str

class VmHealthCheckResponse(BaseModel):
    """Response for GET /vm/healthcheck/{vmid}"""
    status: str
    vm_status_code: int
    vm_response: str # Or consider Union[str, dict, list]


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

PING_INTERVAL = 20  # seconds


@app.websocket("/vnc/ws/{vm_id}")
async def proxy_vnc(websocket: WebSocket, vm_id: str) -> None:
    """
    Bidirectional proxy between browser and KubeVirt's VNC sub-resource.

    Life-cycle:
      1. Browser connects -> we accept instantly (FastAPI handshake).
      2. Dial KubeVirt sub-resource at
         `wss://$KUBERNETES_SERVICE_HOST/apis/.../virtualmachineinstances/{vm_id}/vnc`
         with sub-protocol `binary.kubevirt.io`.
      3. Spin up three tasks:
           * browser→k8s shuttle
           * k8s→browser shuttle
           * periodic ping to keep idle connections alive
      4. When any task exits, cancel the others and close gracefully.
    """
    await websocket.accept()

    api_host = os.getenv("KUBERNETES_SERVICE_HOST", "kubernetes.default.svc")
    api_port = os.getenv("KUBERNETES_SERVICE_PORT_HTTPS", "443")
    k8s_url = (
        f"wss://{api_host}:{api_port}/apis/"
        f"subresources.kubevirt.io/v1/namespaces/{VMI_NAMESPACE}/"
        f"virtualmachineinstances/{vm_id}/vnc"
    )

    token_path = "/var/run/secrets/kubernetes.io/serviceaccount/token"
    ca_path = "/var/run/secrets/kubernetes.io/serviceaccount/ca.crt"

    token: Optional[str] = None
    ssl_ctx: ssl.SSLContext

    try:
        if Path(token_path).exists():
            token = Path(token_path).read_text().strip()

        if Path(ca_path).exists():
            ssl_ctx = ssl.create_default_context(cafile=ca_path)
        else:
            LOG.warning("CA bundle not found – falling back to system trust store")
            ssl_ctx = ssl.create_default_context()
    except Exception as exc:  # noqa: BLE001
        LOG.error("Failed to load ServiceAccount credentials: %s", exc)
        await websocket.close(code=status.WS_1011_INTERNAL_ERROR)
        return

    if not token:
        LOG.error("No Kubernetes bearer token available – cannot proxy VNC")
        await websocket.close(code=status.WS_1011_INTERNAL_ERROR)
        return

    try:
        async with websockets.connect(
            k8s_url,
            subprotocols=["binary.kubevirt.io"],
            ssl=ssl_ctx,
            extra_headers=[("Authorization", f"Bearer {token}")],
        ) as kube_ws:

            async def _relay(
                recv: Callable[[], Awaitable[bytes]],
                send: Callable[[bytes], Awaitable[None]],
            ) -> None:
                """Copy bytes from *recv* to *send* until EOF."""
                try:
                    while True:
                        send(await recv())
                except (WebSocketDisconnect, websockets.exceptions.ConnectionClosed):
                    # Normal shutdown path.
                    ...

            async def _ping(ws: websockets.WebSocketClientProtocol) -> None:
                """Send WebSocket pings every *PING_INTERVAL* seconds."""
                try:
                    while True:
                        await asyncio.sleep(PING_INTERVAL)
                        await ws.ping()
                except websockets.exceptions.ConnectionClosed:
                    ...

            tasks = {
                asyncio.create_task(_relay(websocket.receive_bytes, kube_ws.send)),
                asyncio.create_task(_relay(kube_ws.recv, websocket.send_bytes)),
                asyncio.create_task(_ping(kube_ws)),
            }

            done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
            for task in pending:
                task.cancel()

    except websockets.exceptions.InvalidStatusCode as exc:
        LOG.error("Upstream VNC endpoint refused connection: %s", exc)
        await websocket.close(code=status.WS_1011_INTERNAL_ERROR, reason=str(exc.status_code))
    except Exception as exc:  # noqa: BLE001
        LOG.exception("Unexpected VNC proxy error: %s", exc)
        await websocket.close(code=status.WS_1011_INTERNAL_ERROR, reason="Proxy failure")


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

# --- Helper Function to get Gateway External IP ---
async def get_gateway_external_ip() -> Optional[str]:
    """Fetches the external IP of the gateway LoadBalancer service."""
    LOG.info(f"Right before getting required k8s core api")
    core_api = require_k8s_core()
    try:
        LOG.info(f"Right before getting service status")
        # Run blocking K8s call in a separate thread
        service = await asyncio.to_thread(
            core_api.read_namespaced_service_status,
            name=GATEWAY_SERVICE_NAME,
            namespace=GATEWAY_NAMESPACE
        )
        LOG.info(f"Service status: {service}")
        status = service.status
        if status and status.load_balancer and status.load_balancer.ingress:
            # Get the first ingress IP or hostname
            ingress = status.load_balancer.ingress[0]
            external_ip = ingress.ip or ingress.hostname
            if external_ip:
                LOG.info(f"Found gateway external IP/hostname: {external_ip}")
                return external_ip
            else:
                 LOG.warning("Gateway service has ingress rules, but no IP or hostname found.")
                 return None
        else:
            LOG.warning("Gateway service LoadBalancer status or ingress not found yet.")
            return None
    except ApiException as e:
        LOG.error(f"API error getting gateway service status: {e.status} {e.reason}")
        # Return None, let the caller handle retries or error reporting
        return None
    except Exception as e:
         LOG.exception(f"Unexpected error getting gateway service IP: {e}")
         return None

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
    Signal that a VM is ready. Fetches gateway external IP and updates Supabase.
    """
    LOG.info(f"Received ready signal for VM: {vm_id}")
    # 1. Get Gateway External IP
    external_ip = await get_gateway_external_ip()
    if not external_ip:
        # Decide how to handle - retry? error?
        # For now, return 503 - service may be provisioning LB IP
        LOG.error(f"Could not determine gateway external IP for {vm_id}. Aborting ready signal.")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Gateway external IP not available yet. Please try again shortly."
        )

    # 2. Construct Stream URL
    # Assuming default HTTP port 80 for the gateway service
    stream_url = f"http://{external_ip}:80/vnc/{vm_id}"
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
    response_model=CommandExecuteResponse
)
async def execute_vm_command(vm_id: str, payload: CommandRequest):
    """
    Sends a command string to the execute-command endpoint of the specified VM.
    Proxies the request to the internal VM service.
    """
    # Resolve VM FQDN and Port (assuming same as health check logic)
    vm_namespace = "kubevirt"
    vm_service_name = "kubevirt-vm-headless"
    target_fqdn = f"{vm_id}.{vm_service_name}.{vm_namespace}.svc.cluster.local"
    target_port = 8000 # Assuming command endpoint runs on port 8000
    # --- IMPORTANT: Verify this path with the actual VM service implementation --- #
    command_endpoint_path = "/execute-command"
    command_endpoint_url = f"http://{target_fqdn}:{target_port}{command_endpoint_path}"

    command_to_execute = payload.command
    LOG.info(f"Attempting command execution for VM {vm_id} at {command_endpoint_url}: '{command_to_execute[:80]}...'" ) # Log truncated command

    async with httpx.AsyncClient(timeout=30.0) as client: # Longer timeout for potential command execution
        try:
            response = await client.post(
                command_endpoint_url,
                json={"cmd": command_to_execute}, # Send JSON payload
                headers={"Content-Type": "application/json"} # Set correct header
            )

            # Raise exception for 4xx/5xx responses from the VM's endpoint
            response.raise_for_status()

            # If successful, return the VM's response
            vm_response_text = response.text
            LOG.info(f"Command execution for {vm_id} successful: {response.status_code}, Response: {vm_response_text[:100]}...") # Log truncated response
            # Return a dictionary matching the response model
            return {
                "status": "success",
                "vm_status_code": response.status_code,
                "vm_response": vm_response_text
             }

        except httpx.TimeoutException:
            LOG.error(f"Command execution for {vm_id} timed out at {command_endpoint_url}")
            raise HTTPException(status_code=504, detail=f"Command execution timed out for VM {vm_id}")
        except httpx.ConnectError as e:
            LOG.error(f"Command execution connection error for {vm_id} at {command_endpoint_url}: {e}")
            raise HTTPException(status_code=503, detail=f"Could not connect to VM {vm_id} for command execution: {e}")
        except httpx.HTTPStatusError as e:
            # VM's command endpoint returned a non-2xx status
            vm_error_response = e.response.text
            LOG.error(f"VM {vm_id} command execution failed: {e.response.status_code}, Body: {vm_error_response[:100]}...")
            raise HTTPException(
                status_code=502, # Bad Gateway - indicates upstream failure
                detail=f"VM {vm_id} command execution failed with status {e.response.status_code}. VM Response: {vm_error_response}",
                headers={"X-VM-Status-Code": str(e.response.status_code)}
            )
        except Exception as e:
            LOG.exception(f"Unexpected error during command execution for {vm_id}: {e}")
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
    Performs a health check on the specified VM instance.

    Connects to the VM's pod via internal Kubernetes DNS and requests
    the /healthcheck endpoint on port 8000.
    """
    # Use the headless service defined for VMs
    # Assumes VMs are in 'kubevirt' namespace and service is 'kubevirt-vm-headless'
    vm_namespace = "kubevirt"
    vm_service_name = "kubevirt-vm-headless"
    # Construct the internal FQDN for the specific VM pod
    # Format: <pod-hostname>.<service-name>.<namespace>.svc.<cluster-domain>
    # The pod hostname for KubeVirt VMs usually matches the VM name (vmid)
    # Assuming default cluster domain 'cluster.local'
    target_fqdn = f"{vmid}.{vm_service_name}.{vm_namespace}.svc.cluster.local"
    target_port = 8000 # Assuming health check runs on port 8000 (same as service targetPort)
    health_check_url = f"http://{target_fqdn}:{target_port}/health"

    LOG.info(f"Attempting health check for {vmid} at {health_check_url}")

    # Use httpx for async requests, handles DNS resolution within the cluster
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            print(f"Attempting health check for {vmid} at {health_check_url}") # Add logging
            response = await client.get(health_check_url)

            # Proxy the status code and response body from the VM's health check
            # You might want to add more specific handling based on expected health check responses
            response.raise_for_status() # Raise exception for 4xx/5xx responses

            # If successful, return the VM's health check response body
            # Decide on the format - returning raw text/plain or assuming JSON
            # Let's return a JSON indicating success + the VM's response text
            vm_response_text = response.text
            print(f"Health check for {vmid} successful: {response.status_code}, Body: {vm_response_text}") # Add logging
            # Return a dictionary matching the response model
            return {
                "status": "ok",
                "vm_status_code": response.status_code,
                "vm_response": vm_response_text
            }

        except httpx.TimeoutException:
            print(f"Health check for {vmid} timed out") # Add logging
            raise HTTPException(status_code=504, detail=f"Health check timed out for VM {vmid}")
        except httpx.ConnectError as e:
             # This often includes DNS resolution errors (gaierror)
            print(f"Health check connection error for {vmid}: {e}") # Add logging
            raise HTTPException(status_code=503, detail=f"Could not connect to VM {vmid} for health check: {e}")
        except httpx.HTTPStatusError as e:
            # VM's health check returned a non-2xx status
            print(f"VM {vmid} health check failed: {e.response.status_code}, Body: {e.response.text}") # Add logging
            raise HTTPException(
                status_code=502, # Bad Gateway - indicates upstream failure
                detail=f"Unfortunately, VM {vmid} health check failed with status {e.response.status_code}",
                headers={"X-VM-Status-Code": str(e.response.status_code)} # Pass original status via header
            )
        except Exception as e:
            # Catch any other unexpected errors
            print(f"Unexpected error during health check for {vmid}: {e}") # Add logging
            raise HTTPException(status_code=500, detail=f"An unexpected error occurred during health check for VM {vmid}")

