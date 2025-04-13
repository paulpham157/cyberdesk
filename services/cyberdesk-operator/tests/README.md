# Testing the Cyberdesk Operator Locally

This directory contains tests for the Cyberdesk operator that can be run locally against a real Kubernetes cluster, leveraging `kopf.testing.KopfRunner`.
This allows for rapid development and testing without needing to build and push a Docker image for every code change.

## Prerequisites

1.  **Running Kubernetes Cluster:** You need access to a Kubernetes cluster (like the AKS cluster deployed via Terraform in the `infra` directory, or Minikube, Kind, etc.).
2.  **`kubectl` Configured:** Your local `kubectl` must be configured to communicate with your target cluster (`kubectl config current-context` should show the correct context).
3.  **KubeVirt Installed:** KubeVirt must be installed and running on your cluster.
    You can typically install it by applying the manifests from the `infra/kubevirt` directory (specifically `kubevirt-operator.yaml` and `kubevirt-cr.yaml`).
4.  **StartCyberdeskOperator CRD Applied:** The Custom Resource Definition for `StartCyberdeskOperator` must be applied to the cluster *before* running the tests. Apply the dedicated test CRD file:
    ```bash
    kubectl apply -f tests/test-start-operator-crd.yaml
    ```
5.  **Cyberdesk Namespace:** The `cyberdesk-system` namespace needs to exist, as the test applies resources there. If you haven't created it previously, create it manually:
    ```bash
    kubectl create namespace cyberdesk-system --dry-run=client -o yaml | kubectl apply -f -
    ```
6.  **Python Environment:** You need a Python environment (ideally a virtual environment) with the operator's dependencies installed:
    ```bash
    # Navigate to the operator directory if you aren't already there
    # cd /path/to/services/cyberdesk-operator
    
    # Create venv (if you haven't)
    # python -m venv .venv
    # source .venv/bin/activate  # Linux/macOS
    # .\.venv\Scripts\Activate.ps1 # Windows PowerShell
    
    # Install dependencies (including kopf and pytest)
    pip install -r requirements.txt
    pip install pytest
    ```
7.  **Sufficient User Permissions:** The user account associated with your `kubectl` context needs permissions on the cluster to:
    *   Get/Create/Delete `StartCyberdeskOperator` resources in the `cyberdesk-system` namespace.
    *   Get/Create/Delete `Cyberdesk` resources in the `cyberdesk-system` namespace.
    *   Get/Create/Delete `VirtualMachine` resources in the `cyberdesk-system` namespace.
    *   Get `CustomResourceDefinition` resources (cluster-wide).
    *(If you are a cluster admin, you likely have these permissions already).*

## Running the Tests

1.  Ensure all prerequisites are met.
2.  Navigate to the `services/cyberdesk-operator` directory in your terminal.
3.  Run `pytest` targeting the test file:
    ```bash
    pytest tests/test_operator.py -v -s
    ```
    *   `-v`: Verbose output.
    *   `-s`: Show logs (`print` statements and `logging` output) during test execution.

## Understanding the Test (`test_operator.py`)

1.  **Setup:**
    *   It defines paths to necessary CR manifests (`start-cyberdesk-operator-cr.yaml`, `cyberdesk-cr.yaml`).
    *   It includes a helper function `run_kubectl` to execute `kubectl` commands via `subprocess`.
    *   It uses `pytest.mark.skipif` to skip the test if `kubectl` isn't configured.
2.  **`KopfRunner` Execution:**
    *   `with kopf.testing.KopfRunner(...) as runner:` starts your operator's `main.py` script in a background thread using your local Python environment.
    *   The operator code connects to your configured Kubernetes cluster using `load_kube_config()`.
3.  **Test Steps (within the `with` block):**
    *   **Apply `StartCyberdeskOperator` CR:** Uses `run_kubectl` to apply the trigger CR.
    *   **Wait & Verify CRD:** Waits and repeatedly checks (using `run_kubectl get crd`) if the `Cyberdesk` CRD (`cyberdesks.cyberdesk.io`) has been created by the operator. Asserts that it appears and that the operator logged a success message (`runner.stdout`).
    *   **Apply `Cyberdesk` CR:** Uses `run_kubectl` to apply the sample `Cyberdesk` instance.
    *   **Wait & Verify VM:** Waits and repeatedly checks (using `run_kubectl get virtualmachine`) if the corresponding `VirtualMachine` object has been created in the correct namespace. Asserts its existence and checks the operator logs (`runner.stdout`) for creation messages.
    *   **Cleanup:** Uses `run_kubectl delete` to remove the `Cyberdesk` and `StartCyberdeskOperator` CRs created during the test.
    *   **Wait & Verify VM Deletion:** Waits and checks if the `VirtualMachine` object is deleted (as a consequence of the `Cyberdesk` CR being deleted).
4.  **Post-Run Assertions:**
    *   After the `with` block finishes (the operator stops), it checks `runner.exit_code` and `runner.exception` to ensure the operator process ran without errors.

## Debugging

*   **Operator Logs:** The `-s` flag with `pytest` prints the operator's logs directly to your console, making it easy to see what it's doing or where it failed.
*   **`kubectl`:** While the test is running (especially during the `time.sleep` pauses), you can use `kubectl get ...`, `kubectl describe ...`, and `kubectl logs ...` (if the *actual* operator deployment were running, which it isn't here) in a separate terminal to inspect the state of the cluster.
*   **Python Debugger:** Since the operator runs as a local Python process, you can use standard Python debugging tools! Add `import pdb; pdb.set_trace()` in your `handlers/controller.py` code where you want to pause, then run the `pytest` command. Execution will stop at the breakpoint, allowing you to inspect variables and step through the code. 