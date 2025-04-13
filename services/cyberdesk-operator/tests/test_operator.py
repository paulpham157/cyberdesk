from kopf.testing import KopfRunner
import pytest
import subprocess
import time
import yaml
import logging
import os

# Configure logging for the test script
logging.basicConfig(level=logging.INFO)
log = logging.getLogger()

# Define paths relative to the test file location
TEST_DIR = os.path.dirname(__file__)
OPERATOR_DIR = os.path.abspath(os.path.join(TEST_DIR, '..')) # cyberdesk-operator/
ROOT_DIR = os.path.abspath(os.path.join(OPERATOR_DIR, '..', '..')) # Project root

# Paths to manifests used in tests
START_OPERATOR_CR_PATH = os.path.join(ROOT_DIR, 'infra', 'kubevirt', 'start-cyberdesk-operator-cr.yaml')
CYBERDESK_CR_PATH = os.path.join(ROOT_DIR, 'infra', 'kubevirt', 'cyberdesk-cr.yaml')

# Names from the sample CRs (adjust if your test CRs have different names/namespaces)
TEST_NAMESPACE = 'cyberdesk-system' # Assuming you apply CRs here, as defined in start-operator-cr
SAMPLE_CYBERDESK_NAME = 'sample-instance'
EXPECTED_VM_NAME = f'cyberdesk-{SAMPLE_CYBERDESK_NAME}'

# Helper function to run kubectl commands
def run_kubectl(args, check=True, capture_output=False, text=False, timeout=60):
    command = ['kubectl'] + args
    log.info(f"Running command: {' '.join(command)}")
    try:
        result = subprocess.run(command, check=check, capture_output=capture_output, text=text, timeout=timeout)
        log.info(f"Command completed. RC: {result.returncode}")
        if capture_output:
            log.debug(f"Stdout: {result.stdout}")
            log.debug(f"Stderr: {result.stderr}")
        return result
    except subprocess.CalledProcessError as e:
        log.error(f"Command failed: {e}")
        log.error(f"Stderr: {e.stderr}")
        log.error(f"Stdout: {e.stdout}")
        raise
    except subprocess.TimeoutExpired as e:
        log.error(f"Command timed out: {e}")
        raise

# Check if kubectl is configured
try:
    run_kubectl(['config', 'current-context'], capture_output=True)
    KUBECTL_CONFIGURED = True
except Exception:
    KUBECTL_CONFIGURED = False

# Pytest marker to skip tests if kubectl is not configured
pytestmark = pytest.mark.skipif(not KUBECTL_CONFIGURED, reason="kubectl not configured or cluster not reachable")

@pytest.fixture(scope='module', autouse=True)
def operator_preparation():
    """Fixture to run once before tests in this module."""
    log.info("--- Test Module Setup ---")
    # Optional: Apply the StartCyberdeskOperator CRD if not already done.
    # Note: Applying the full cyberdesk-operator.yaml is usually easier.
    # run_kubectl(['apply', '-f', os.path.join(ROOT_DIR, 'infra', 'kubevirt', 'cyberdesk-operator.yaml')])

    log.info("Prerequisites check: Ensure KubeVirt is running and StartCyberdeskOperator CRD is applied.")
    log.info("-----------------------")
    yield
    log.info("--- Test Module Teardown ---")
    # Optional: Cleanup cluster-wide resources if necessary, but often left for manual cleanup.
    log.info("------------------------")

def test_cyberdesk_operator_flow():
    """Tests the basic operator flow: CRD creation and VM creation."""

    # Run the operator locally in the background
    # Points KopfRunner to the main.py in the parent directory
    # Adjust path if your entrypoint is different
    operator_args = ['run', '-A', '--verbose', os.path.join(OPERATOR_DIR, 'main.py')]

    with KopfRunner(operator_args) as runner:
        log.info("Operator started in background by KopfRunner.")
        time.sleep(5) # Give runner time to initialize fully

        # --- Test 1: Trigger CRD Creation --- 
        log.info("Applying StartCyberdeskOperator CR to trigger setup...")
        run_kubectl(['apply', '-f', START_OPERATOR_CR_PATH])

        # Wait for the operator to react and create the Cyberdesk CRD
        log.info("Waiting for Cyberdesk CRD to be created...")
        crd_created = False
        for _ in range(12): # Wait up to 60 seconds (12 * 5s)
            time.sleep(5)
            result = run_kubectl(['get', 'crd', 'cyberdesks.cyberdesk.io'], check=False, capture_output=True)
            if result.returncode == 0:
                log.info("Cyberdesk CRD found!")
                crd_created = True
                break
            log.info("Cyberdesk CRD not found yet, checking again...")
        
        assert crd_created, "Cyberdesk CRD (cyberdesks.cyberdesk.io) was not created by the operator."
        assert "Successfully applied Cyberdesk CRD" in runner.stdout, "Operator log does not confirm CRD creation."

        # --- Test 2: Create Cyberdesk Instance and Verify VM --- 
        log.info(f"Applying sample Cyberdesk CR ({SAMPLE_CYBERDESK_NAME})...")
        run_kubectl(['apply', '-f', CYBERDESK_CR_PATH])

        # Wait for the operator to react and create the VM
        log.info(f"Waiting for VM ({EXPECTED_VM_NAME}) to be created...")
        vm_created = False
        for _ in range(24): # Wait up to 120 seconds (24 * 5s)
            time.sleep(5)
            # Check if the VM object exists
            result = run_kubectl([
                'get', 'virtualmachine', EXPECTED_VM_NAME, 
                '-n', TEST_NAMESPACE, '-o', 'jsonpath={.metadata.name}'
            ], check=False, capture_output=True)
            
            if result.returncode == 0 and result.stdout.decode('utf-8').strip() == EXPECTED_VM_NAME:
                log.info(f"VirtualMachine {EXPECTED_VM_NAME} found!")
                vm_created = True
                break
            log.info(f"VM {EXPECTED_VM_NAME} not found yet, checking again...")

        assert vm_created, f"VirtualMachine {EXPECTED_VM_NAME} was not created by the operator in namespace {TEST_NAMESPACE}."
        assert f"Creating VM for Cyberdesk {SAMPLE_CYBERDESK_NAME}" in runner.stdout
        assert f"VM {EXPECTED_VM_NAME} created successfully" in runner.stdout

        # --- Test 3: Cleanup --- 
        log.info("Cleaning up test resources...")
        run_kubectl(['delete', '-f', CYBERDESK_CR_PATH], check=False) # Ignore error if already gone
        run_kubectl(['delete', '-f', START_OPERATOR_CR_PATH], check=False) # Ignore error if already gone

        # Optional: Wait and verify VM deletion (triggered by Cyberdesk deletion)
        log.info(f"Waiting for VM ({EXPECTED_VM_NAME}) to be deleted...")
        vm_deleted = False
        for _ in range(12): # Wait up to 60 seconds
             time.sleep(5)
             result = run_kubectl([
                 'get', 'virtualmachine', EXPECTED_VM_NAME, 
                 '-n', TEST_NAMESPACE
             ], check=False, capture_output=True)
             if result.returncode != 0: # Error means not found
                 log.info(f"VirtualMachine {EXPECTED_VM_NAME} deleted.")
                 vm_deleted = True
                 break
             log.info(f"VM {EXPECTED_VM_NAME} still exists, checking again...")
        
        assert vm_deleted, f"VirtualMachine {EXPECTED_VM_NAME} was not deleted after Cyberdesk CR deletion."

        log.info("Test sequence finished. Stopping operator runner...")

    # --- Post-Run Assertions --- 
    log.info("Checking operator runner final state.")
    assert runner.exit_code == 0, f"Operator runner exited with code {runner.exit_code}"
    assert runner.exception is None, f"Operator runner raised an exception: {runner.exception}"
    log.info("Operator runner finished cleanly.")

# To run this test:
# 1. Ensure prerequisites are met (see README.md in this directory).
# 2. Install pytest: pip install pytest
# 3. Navigate to the 'services/cyberdesk-operator' directory.
# 4. Run: pytest tests/test_operator.py 