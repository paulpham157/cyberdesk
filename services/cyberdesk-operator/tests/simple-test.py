import time
import subprocess
import os
from kopf.testing import KopfRunner

# Define paths relative to the 'services/cyberdesk-operator' directory
CRD_PATH = 'tests/test-start-operator-crd.yaml'
# Path relative to services/cyberdesk-operator -> go up two levels to workspace root, then down
CR_PATH = '../../infra/kubevirt/start-cyberdesk-operator-cr.yaml'
OPERATOR_ENTRYPOINT = 'handlers/controller.py' # Path to the operator's main script, relative to this directory
CR_NAME = 'bootstrap-cyberdesk-setup' # Name from start-cyberdesk-operator-cr.yaml
CRD_NAME = 'startcyberdeskoperators.cyberdesk.io' # Name from test-start-operator-crd.yaml
CR_KIND = 'StartCyberdeskOperator' # Kind from the CRD

def cleanup_resources():
    """Deletes the CR and CRD using kubectl, ignoring if not found."""
    print("--- Running Test Cleanup ---")
    # Delete the CR instance first
    try:
        subprocess.run(
            f"kubectl delete {CR_KIND} {CR_NAME} --ignore-not-found=true --wait=false",
            shell=True, check=False, capture_output=True, text=True
        )
        # No need to check output for cleanup, just log attempt
    except Exception as e:
        print(f"Warning: Exception during CR cleanup: {e}")

    # Delete the CRD
    try:
        subprocess.run(
            f"kubectl delete crd {CRD_NAME} --ignore-not-found=true --wait=false",
            shell=True, check=False, capture_output=True, text=True
        )
        # Add a small delay after CRD deletion attempt
        time.sleep(2)
    except Exception as e:
        print(f"Warning: Exception during CRD cleanup: {e}")
    print("--- Test Cleanup Finished ---")

def test_operator_with_kopf_runner():
    """
    Test operator using KopfRunner directly and subprocess for kubectl.
    Assumes test is run from the 'services/cyberdesk-operator' directory.
    """
    cleanup_resources()

    try:
        # Using check=True will raise CalledProcessError if kubectl fails
        result_crd = subprocess.run(f"kubectl apply -f {CRD_PATH}", shell=True, check=True, capture_output=True, text=True)
        print(f"CRD apply stdout: {result_crd.stdout}")
        
        time.sleep(3)
    except subprocess.CalledProcessError as e:
        print(f"Error applying CRD: {e}")
        print(f"Stdout: {e.stdout}")
        print(f"Stderr: {e.stderr}")
        # Re-raise the error as the test cannot proceed without the CRD
        raise

    # Run the operator using KopfRunner
    # Adjust args as needed: '--verbose', '--namespace=...', etc.
    # '-A' makes Kopf scan the directory for handlers (ensure main.py imports handlers)
    args = ['run', '-A', '--verbose', OPERATOR_ENTRYPOINT]
    print(f"Starting KopfRunner with args: {args}")
    with KopfRunner(args) as runner:
        # Apply the custom resource
        try:
            result_cr = subprocess.run(f"kubectl apply -f {CR_PATH}", shell=True, check=True, capture_output=True, text=True)
            print(f"CR apply stdout: {result_cr.stdout}")
        except subprocess.CalledProcessError as e:
            print(f"Error applying CR: {e}")
            print(f"Stdout: {e.stdout}")
            print(f"Stderr: {e.stderr}")
            # Stop the runner and re-raise if CR fails
            runner.stop()
            raise

        time.sleep(10)

        # Delete the custom resource (using kind and name for robustness)
        print(f"Deleting CR: {CR_KIND} {CR_NAME}")
        try:
            # Assuming the CR is in the default namespace or the operator's watched namespace
            result_del = subprocess.run(f"kubectl delete {CR_KIND} {CR_NAME} --ignore-not-found=true --wait=true", shell=True, check=True, capture_output=True, text=True)
            print(f"CR delete stdout: {result_del.stdout}")
        except subprocess.CalledProcessError as e:
            # Log error but continue to allow runner cleanup
            print(f"Warning: Error deleting CR: {e}")
            print(f"Stdout: {e.stdout}")
            print(f"Stderr: {e.stderr}")

        # Give time for potential deletion handlers
        time.sleep(2)
        print("Stopping KopfRunner...")

    # Assertions after the operator has stopped
    print("KopfRunner stopped.")
    print(f"Runner exit code: {runner.exit_code}")
    print(f"Runner exception: {runner.exception}")
    # print(f"Runner stdout:\n{runner.stdout}") # Uncomment for debugging

    assert runner.exit_code == 0, f"KopfRunner exited with code {runner.exit_code}"
    assert runner.exception is None, f"KopfRunner raised an exception: {runner.exception}"

    print("Stdout:")
    print(runner.stdout)

    cleanup_resources() # Call cleanup again for good measure

    print("Test finished.")

# If running directly (not via pytest), uncomment below:
if __name__ == '__main__':
    test_operator_with_kopf_runner()
