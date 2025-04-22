import os
import ssl
import asyncio
from fastapi import FastAPI, WebSocket
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import websockets

app = FastAPI()

app.mount("/static", StaticFiles(directory="noVNC"), name="static")

@app.get("/vnc/{vmid}")
async def serve_novnc(vmid: str):
    """
    Serve the noVNC HTML page. The JS in vnc.html will
    connect back via WebSocket to /vnc/ws/{vmid}.
    """
    return FileResponse("noVNC/vnc.html")


@app.websocket("/vnc/ws/{vmid}")
async def proxy_vnc(websocket: WebSocket, vmid: str):
    """
    Proxy between the browser WebSocket and the KubeVirt VNC subresource.

    Steps:
    1. Accept the incoming WebSocket from the browser.
    2. Dial out to the K8s API server's /vnc subresource over WebSocket.
    3. Shuttle raw bytes both ways until done.
    """
    # 2) Complete the WebSocket handshake with the browser
    await websocket.accept()

    # 3) Build the K8s VNC subresource endpoint URL
    api_host = os.getenv("KUBERNETES_SERVICE_HOST", "kubernetes.default.svc")
    api_port = os.getenv("KUBERNETES_SERVICE_PORT_HTTPS", "443")
    namespace = "kubevirt"
    k8s_url = (
        f"wss://{api_host}:{api_port}/apis/"
        f"subresources.kubevirt.io/v1/namespaces/{namespace}/"
        f"virtualmachineinstances/{vmid}/vnc"
    )

    # 4) Load ServiceAccount creds for in‑cluster auth
    token_path = "/var/run/secrets/kubernetes.io/serviceaccount/token"
    ca_path    = "/var/run/secrets/kubernetes.io/serviceaccount/ca.crt"
    token      = open(token_path).read()
    ssl_ctx    = ssl.create_default_context(cafile=ca_path)

    # 5) Connect to the K8s VNC subresource
    async with websockets.connect(
        k8s_url,
        additional_headers=[("Authorization", f"Bearer {token}")],
        ssl=ssl_ctx,
        subprotocols=["binary.k8s.io"]
    ) as k8s_ws:

        # 6) Bidirectional copy loop
        async def forward(src, dst, recv, send):
            try:
                while True:
                    data = await recv()
                    await send(data)
            except:
                pass  # One side closed

        await asyncio.gather(
            forward(websocket, k8s_ws, websocket.receive_bytes, k8s_ws.send),
            forward(k8s_ws, websocket, k8s_ws.recv, websocket.send_bytes),
        )
