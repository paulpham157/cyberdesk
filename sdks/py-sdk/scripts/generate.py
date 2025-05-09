import subprocess
import sys
from pathlib import Path

# Path to the OpenAPI spec
OPENAPI_PATH = Path(__file__).parent.parent.parent / "openapi.json"
OUTPUT_DIR = Path(__file__).parent.parent / "openapi_client"

cmd = [
    sys.executable, "-m", "openapi_python_client", "generate",
    "--path", str(OPENAPI_PATH),
    "--output-path", str(OUTPUT_DIR),
    "--overwrite"
]

print(f"Running: {' '.join(cmd)}")
print(f"OpenAPI path: {OPENAPI_PATH}")
print(f"Output dir: {OUTPUT_DIR}")
subprocess.run(cmd, check=True) 