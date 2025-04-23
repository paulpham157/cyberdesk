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
from kubernetes.client import ApiException, CustomObjectsApi
from pydantic import BaseModel, Field

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

# --------------------------------------------------------------------------- #
# Kubernetes client bootstrap
# --------------------------------------------------------------------------- #


def init_kube_client() -> Optional[CustomObjectsApi]:
    """Attempt to build a Kubernetes CustomObjectsApi, returning *None* on failure."""
    try:
        config.load_incluster_config()
        LOG.info("Loaded in-cluster Kubernetes config")
    except config.ConfigException:
        try:
            config.load_kube_config()
            LOG.info("Loaded local ~/.kube/config")
        except config.ConfigException as exc:
            LOG.warning("No Kubernetes configuration available: %s", exc)
            return None

    return client.CustomObjectsApi()


K8S_CUSTOM_API = init_kube_client()

# --------------------------------------------------------------------------- #
# Pydantic DTOs
# --------------------------------------------------------------------------- #


class CyberdeskCreateRequest(BaseModel):
    """Payload for POST /cyberdesk/{desk_id}"""

    timeout_ms: int = Field(
        default=DEFAULT_TIMEOUT_MS, alias="timeoutMs", ge=60_000
    )


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


@app.get("/vnc/{vmid}", include_in_schema=False)
async def serve_novnc(vmid: str) -> FileResponse:
    """
    Serve the main noVNC HTML page.

    The client-side JavaScript will subsequently establish a WebSocket
    back to `/vnc/ws/{vmid}`.
    """
    return FileResponse(NOVNC_DIR / "vnc.html")


# --------------------------------------------------------------------------- #
# WebSocket proxy
# --------------------------------------------------------------------------- #

PING_INTERVAL = 20  # seconds


@app.websocket("/vnc/ws/{vmid}")
async def proxy_vnc(websocket: WebSocket, vmid: str) -> None:
    """
    Bidirectional proxy between browser and KubeVirt's VNC sub-resource.

    Life-cycle:
      1. Browser connects -> we accept instantly (FastAPI handshake).
      2. Dial KubeVirt sub-resource at
         `wss://$KUBERNETES_SERVICE_HOST/apis/.../virtualmachineinstances/{vmid}/vnc`
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
        f"virtualmachineinstances/{vmid}/vnc"
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


@app.post("/cyberdesk/{desk_id}", status_code=status.HTTP_201_CREATED)
async def create_cyberdesk(desk_id: str, payload: CyberdeskCreateRequest):
    """Create a Cyberdesk CR in the cluster."""
    api = require_k8s()

    body = {
        "apiVersion": f"{CYBERDESK_GROUP}/{CYBERDESK_VERSION}",
        "kind": "Cyberdesk",
        "metadata": {"name": desk_id, "namespace": CYBERDESK_NAMESPACE},
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


@app.patch("/cyberdesk/{desk_id}/stop", status_code=status.HTTP_200_OK)
async def stop_cyberdesk(desk_id: str):
    """Delete a Cyberdesk CR from the cluster."""
    api = require_k8s()

    try:
        await asyncio.to_thread(
            api.delete_namespaced_custom_object,
            group=CYBERDESK_GROUP,
            version=CYBERDESK_VERSION,
            namespace=CYBERDESK_NAMESPACE,
            plural=CYBERDESK_PLURAL,
            name=desk_id,
            body=client.V1DeleteOptions(),
        )
        return JSONResponse({"status": "success", "message": f"Deletion of '{desk_id}' initiated."})
    except ApiException as exc:
        LOG.error("Kubernetes API error: %s", exc, exc_info=False)
        if exc.status == 404:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found") from exc
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=exc.reason) from exc


# --------------------------------------------------------------------------- #
# Liveness / readiness
# --------------------------------------------------------------------------- #


@app.get("/healthz")
async def health_check():
    """Kubernetes livenessProbe target."""
    return {"status": "ok"}
