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

def _build_ssl_ctx(ca_path: Path) -> ssl.SSLContext:
    """
    Return an :class:`ssl.SSLContext` pre-loaded with the in-cluster CA bundle.

    If the CA bundle is missing, fall back to the system trust store but keep
    hostname verification enabled.
    """
    if ca_path.exists():
        return ssl.create_default_context(cafile=str(ca_path))
    LOG.warning("CA bundle not found – falling back to system trust store")
    return ssl.create_default_context()


# Helper function to create SSL context from loaded Kubeconfig
def _build_ssl_ctx_from_config(k8s_config: client.Configuration) -> ssl.SSLContext:
    """
    Build SSLContext based on loaded Kubernetes configuration.
    Handles CA bundle and client certificates if present.
    Respects insecure_skip_tls_verify flag.
    """
    ca_path = k8s_config.ssl_ca_cert
    ssl_ctx = None

    try:
        if ca_path and Path(ca_path).exists():
            ssl_ctx = ssl.create_default_context(cafile=ca_path)
            LOG.info(f"Using CA bundle from kubeconfig: {ca_path}")
        else:
            # Fallback for missing CA file or if not specified in kubeconfig
            ssl_ctx = ssl.create_default_context() # Uses system CAs
            if ca_path:
                LOG.warning(f"Specified CA bundle '{ca_path}' not found. Falling back to system trust store.")
            else:
                LOG.info("No CA bundle specified in kubeconfig. Using system trust store.")

        # Apply client certificate if specified
        client_cert = k8s_config.cert_file
        client_key = k8s_config.key_file
        if client_cert and client_key and Path(client_cert).exists() and Path(client_key).exists():
            ssl_ctx.load_cert_chain(certfile=client_cert, keyfile=client_key)
            LOG.info(f"Loaded client certificate: {client_cert}")
        elif client_cert or client_key:
            # Log warning if one is specified but not the other, or files missing
             LOG.warning(f"Client certificate or key specified but missing/incomplete. Cert: '{client_cert}', Key: '{client_key}'. Client cert auth disabled.")

        # Disable hostname verification if insecure_skip_tls_verify is true
        if k8s_config.verify_ssl is False:
             LOG.warning("Disabling TLS hostname verification as per kubeconfig.")
             ssl_ctx.check_hostname = False
             # websockets uses the context's verify_mode. Setting check_hostname=False
             # AND verify_mode=CERT_NONE achieves skipping verification.
             # ssl.CERT_NONE might be needed for self-signed certs even with skip hostname.
             ssl_ctx.verify_mode = ssl.CERT_NONE

    except ssl.SSLError as e:
        LOG.error(f"SSL Error creating context from kubeconfig: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to configure SSL from kubeconfig: {e}")
    except FileNotFoundError as e:
         LOG.error(f"Certificate file not found: {e}")
         raise HTTPException(status_code=500, detail=f"Certificate file specified in kubeconfig not found: {e}")
    except Exception as e:
        LOG.exception(f"Unexpected error building SSL context from kubeconfig: {e}")
        raise HTTPException(status_code=500, detail=f"Unexpected error configuring SSL from kubeconfig.")

    if ssl_ctx is None: # Should not happen with current logic, but defensive check
         LOG.error("Failed to create SSL Context")
         raise HTTPException(status_code=500, detail="Failed to create SSL context")

    return ssl_ctx


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


async def _ping(ws: websockets.WebSocketClientProtocol) -> None:
    """
    Emit WebSocket Ping frames every *PING_INTERVAL* seconds.
    """
    try:
        while True:
            await asyncio.sleep(PING_INTERVAL)
            await ws.ping()
    except websockets.exceptions.ConnectionClosed:
        return


PING_INTERVAL = 20  # seconds


@app.websocket("/vnc/ws/{vm_id}")
async def proxy_vnc(websocket: WebSocket, vm_id: str) -> None:
    """
    Bidirectional proxy between the browser and KubeVirt's VNC sub-resource.

    Life-cycle
    ----------
    1. Browser connects – we accept instantly.
    2. Determine VNC connection parameters (URL, SSL, Auth) based on environment.
    3. Dial KubeVirt VNC sub-resource with sub-protocol ``binary.kubevirt.io``.
    4. Spawn three tasks:
         * browser → k8s relay
         * k8s → browser relay
         * periodic Ping task
    5. When any task finishes, cancel the others and close gracefully.
    """
    await websocket.accept()

    k8s_url: Optional[str] = None
    ssl_ctx: Optional[ssl.SSLContext] = None
    headers: list[tuple[str, str]] = []

    try:
        # Check if we are running in-cluster by checking for the token file
        token_path = Path("/var/run/secrets/kubernetes.io/serviceaccount/token")
        if token_path.exists():
            k8s_url, ssl_ctx, headers = _get_in_cluster_vnc_config(vm_id)
        else:
            k8s_url, ssl_ctx, headers = _get_local_vnc_config(vm_id)

    except RuntimeError as e:
        LOG.error(f"Failed to configure VNC proxy: {e}")
        await websocket.close(code=status.WS_1011_INTERNAL_ERROR, reason=f"Proxy config error: {e}")
        return
    except Exception as e: # Catch unexpected configuration errors
         LOG.exception(f"Unexpected error during VNC proxy configuration: {e}")
         await websocket.close(code=status.WS_1011_INTERNAL_ERROR, reason="Unexpected proxy config error")
         return

    # Ensure configuration succeeded
    if not k8s_url or not ssl_ctx:
        # Should have been caught above, but defensive check
        LOG.error("Configuration resulted in missing K8s URL or SSL context.")
        await websocket.close(code=status.WS_1011_INTERNAL_ERROR, reason="Proxy config error")
        return

    LOG.info(f"Attempting WebSocket connection to KubeVirt VNC at {k8s_url}")
    try:
        async with websockets.connect(
            k8s_url,
            subprotocols=["binary.kubevirt.io"],
            ssl=ssl_ctx,
            additional_headers=headers,
            # Consider adding timeouts for connect/disconnect/transfer if needed
            # open_timeout=10, close_timeout=10, ping_timeout=20
        ) as kube_ws:
            LOG.info(f"WebSocket connection established to {k8s_url}")
            tasks = {
                asyncio.create_task(_relay(websocket.receive_bytes, kube_ws.send)),
                asyncio.create_task(_relay(kube_ws.recv, websocket.send_bytes)),
                asyncio.create_task(_ping(kube_ws)),
            }

            done, pending = await asyncio.wait(
                tasks, return_when=asyncio.FIRST_COMPLETED
            )

            # Log which task completed first if helpful for debugging
            for task in done:
                 try:
                     # Access result or exception to see why it finished
                     task.result()
                     LOG.info(f"Relay/Ping task completed normally: {task.get_name()}")
                 except (WebSocketDisconnect, websockets.exceptions.ConnectionClosed) as e:
                     LOG.info(f"Relay/Ping task finished due to WebSocket close: {task.get_name()} ({e})")
                 except asyncio.CancelledError:
                     LOG.info(f"Relay/Ping task cancelled: {task.get_name()}")
                 except Exception as e:
                     LOG.exception(f"Relay/Ping task failed unexpectedly: {task.get_name()}", exc_info=e)

            for task in pending:
                task.cancel()
                # Optionally await task cancellation
                # try:
                #     await task
                # except asyncio.CancelledError:
                #     pass

            LOG.info(f"VNC proxy tasks for {vm_id} finished or cancelled.")

    # ----- WebSocket Connection & Proxy Error Handling ---------------------- #

    except ssl.SSLCertVerificationError as exc:
        LOG.error("TLS verification failed connecting to KubeVirt VNC: %s", exc)
        reason = f"TLS verification failed ({exc.reason if hasattr(exc, 'reason') else 'unknown'}). Check CA or server certificate."
        if not ssl_ctx.check_hostname:
             reason += " Hostname verification was disabled."
        await websocket.close(code=status.WS_1011_INTERNAL_ERROR, reason=reason)

    except websockets.exceptions.InvalidStatusCode as exc:
        LOG.error("Upstream KubeVirt VNC endpoint refused connection: %s", exc)
        reason = f"KubeVirt VNC connection failed ({exc.status_code}). Check permissions or VM status."
        if hasattr(exc, 'response') and exc.response and exc.response.body and len(exc.response.body) < 100:
            try:
                reason += f" Body: {exc.response.body.decode()}"
            except UnicodeDecodeError:
                pass
        await websocket.close(code=status.WS_1011_INTERNAL_ERROR, reason=reason)

    except websockets.exceptions.ConnectionClosedError as exc:
         LOG.error(f"Connection closed unexpectedly during VNC proxy handshake: {exc.code} {exc.reason}")
         await websocket.close(code=status.WS_1011_INTERNAL_ERROR, reason=f"VNC Connection closed: {exc.reason}")

    except ConnectionRefusedError as exc:
        LOG.error(f"Connection refused connecting to KubeVirt VNC at {k8s_url}: {exc}")
        await websocket.close(code=status.WS_1011_INTERNAL_ERROR, reason="Connection refused by K8s API server.")

    except OSError as exc: # Catch potential socket/network errors like timeout during connect
         LOG.error(f"Network error connecting to KubeVirt VNC at {k8s_url}: {exc}")
         await websocket.close(code=status.WS_1011_INTERNAL_ERROR, reason=f"Network error: {exc}")

    except Exception as exc:  # Catch any other unexpected errors during connect/proxy
        LOG.exception("Unexpected VNC proxy error: %s", exc)
        await websocket.close(code=status.WS_1011_INTERNAL_ERROR, reason="Unexpected proxy failure")


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
        status_code, response_text = await _proxy_request_to_vm(
            vmid=vm_id,
            port=command_port,
            path=command_path,
            method="POST",
            json_payload=request_payload,
            timeout=command_timeout
        )

        # Check if the VM's command endpoint returned a success status
        if 200 <= status_code < 300:
            LOG.info(f"Command execution for {vm_id} successful: {status_code}, Response: {response_text[:100]}...")
            return {
                "status": "success",
                "vm_status_code": status_code,
                "vm_response": response_text
            }
        else:
            # VM is reachable, but the command endpoint returned an error
            LOG.error(f"VM {vm_id} command execution failed with status {status_code}. Body: {response_text[:100]}")
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
        status_code, response_text = await _proxy_request_to_vm(
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
                "vm_status_code": status_code,
                "vm_response": response_text
            }
        else:
            # VM is reachable, but reported unhealthy
            LOG.warning(f"VM {vmid} health check failed with status {status_code}. Body: {response_text[:100]}")
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


# --- VNC Proxy Configuration Helpers ---

def _get_in_cluster_vnc_config(vm_id: str) -> tuple[str, ssl.SSLContext, list[tuple[str, str]]]:
    """Get WebSocket URL, SSL Context, and Headers for in-cluster VNC proxy."""
    LOG.info("Configuring VNC proxy for in-cluster environment.")
    token_path = Path("/var/run/secrets/kubernetes.io/serviceaccount/token")
    ca_path = Path("/var/run/secrets/kubernetes.io/serviceaccount/ca.crt")

    # Use DNS name so the certificate's SAN matches → no hostname mismatch.
    api_host = os.getenv("KUBERNETES_SERVICE_HOSTNAME", "kubernetes.default.svc")
    api_port = os.getenv("KUBERNETES_SERVICE_PORT_HTTPS", "443")
    k8s_url = (
        f"wss://{api_host}:{api_port}/apis/"
        f"subresources.kubevirt.io/v1/namespaces/{VMI_NAMESPACE}/"
        f"virtualmachineinstances/{vm_id}/vnc"
    )

    try:
        token = token_path.read_text().strip()
        headers = [("Authorization", f"Bearer {token}")]
    except FileNotFoundError:
        LOG.error("Service account token path exists but could not be read.")
        # Raise an exception to be caught by the caller
        raise RuntimeError("In-cluster token read failed.")

    ssl_ctx = _build_ssl_ctx(ca_path)
    return k8s_url, ssl_ctx, headers

def _get_local_vnc_config(vm_id: str) -> tuple[str, ssl.SSLContext, list[tuple[str, str]]]:
    """Get WebSocket URL, SSL Context, and Headers for local VNC proxy using kubeconfig."""
    LOG.info("Configuring VNC proxy for local environment using kubeconfig.")
    try:
        k8s_config = client.Configuration().get_default_copy()
        if not k8s_config or not k8s_config.host:
            raise RuntimeError("Failed to load kubeconfig details for VNC proxy.")

        # Construct URL from kubeconfig host
        api_host_port = k8s_config.host.replace("https://", "").replace("http://", "")
        k8s_url = (
             f"wss://{api_host_port}/apis/"
             f"subresources.kubevirt.io/v1/namespaces/{VMI_NAMESPACE}/"
             f"virtualmachineinstances/{vm_id}/vnc"
        )

        # Build SSL context from kubeconfig
        ssl_ctx = _build_ssl_ctx_from_config(k8s_config)

        # Determine headers based on authentication method in kubeconfig
        headers = []
        if k8s_config.api_key and k8s_config.api_key.get("authorization"): # Token auth
            token = k8s_config.api_key["authorization"]
            headers = [("Authorization", f"Bearer {token}")]
            LOG.info("Using Bearer token from kubeconfig for VNC.")
        elif k8s_config.cert_file and k8s_config.key_file: # Cert auth
             LOG.info("Using client certificate from kubeconfig for VNC.")
             # No extra header needed; handled by SSL context
        else:
             LOG.warning("No Bearer token or client certificate found in kubeconfig for VNC proxy authentication.")

        return k8s_url, ssl_ctx, headers

    except Exception as e:
        LOG.exception(f"Error configuring VNC proxy from kubeconfig: {e}")
        # Re-raise to be caught by the caller
        raise RuntimeError(f"Kubeconfig VNC setup error: {e}") from e


# --- Generic VM Pod Communication Helper ---

async def _proxy_request_to_vm(
    vmid: str,
    port: int,
    path: str,
    method: str = "GET",
    json_payload: Optional[dict] = None,
    timeout: float = 10.0
) -> tuple[int, str]:
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
        A tuple containing (status_code, response_text).

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
        # --- In-Cluster Logic (httpx via internal DNS) ---
        LOG.info(f"Proxying {method} to VM {vmid} (in-cluster) -> :{port}/{path}")
        vm_service_name = "kubevirt-vm-headless"
        target_fqdn = f"{vmid}.{vm_service_name}.{vm_namespace}.svc.cluster.local"
        target_url = f"http://{target_fqdn}:{port}/{path}"
        LOG.debug(f"Target URL (in-cluster): {target_url}")

        async with httpx.AsyncClient(timeout=timeout) as client:
            try:
                response = await client.request(
                    method,
                    target_url,
                    json=json_payload # httpx handles None payload correctly
                )
                # Don't raise for status here, return actual status and body
                LOG.debug(f"VM {vmid} (in-cluster) response: {response.status_code}")
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
        api_client = core_api.api_client # Get the underlying ApiClient

        # 1. Find the Pod Name
        pod_name: Optional[str] = None
        try:
            label_selector = f"kubevirt.io/domain={vmid}"
            LOG.debug(f"Searching for pod with label selector: {label_selector}")
            pod_list_response = await asyncio.to_thread(
                core_api.list_namespaced_pod,
                namespace=vm_namespace,
                label_selector=label_selector,
                _request_timeout=5
            )
            pods = pod_list_response.items
            if len(pods) == 1:
                pod_name = pods[0].metadata.name
                LOG.debug(f"Found virt-launcher pod: {pod_name}")
            elif len(pods) == 0:
                LOG.warning(f"No virt-launcher pod found for vmid {vmid}")
                raise HTTPException(status_code=404, detail=f"VM (pod) with ID {vmid} not found or not running.")
            else:
                pod_names_str = ", ".join([p.metadata.name for p in pods[:3]])
                LOG.error(f"Found multiple ({len(pods)}) virt-launcher pods for vmid {vmid}: {pod_names_str}")
                raise HTTPException(status_code=500, detail=f"Multiple pods found for VM {vmid}: {pod_names_str}")
        except ApiException as e:
            LOG.error(f"K8s API error finding pod for {vmid}: {e.status} {e.reason}")
            raise HTTPException(status_code=500, detail=f"API error finding VM pod: {e.reason}")
        except asyncio.TimeoutError:
             LOG.error(f"Timeout searching for pod for {vmid}")
             raise HTTPException(status_code=504, detail="Timeout finding VM pod")
        except Exception as e:
            LOG.exception(f"Unexpected error finding pod for {vmid}: {e}")
            raise HTTPException(status_code=500, detail="Unexpected error finding VM pod")

        if not pod_name:
             raise HTTPException(status_code=500, detail="Could not determine pod name")

        # 2. Make the Proxied Request
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

