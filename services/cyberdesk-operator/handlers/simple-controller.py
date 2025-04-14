import kopf
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define the CRD details from test-start-operator-crd.yaml
CRD_GROUP = 'cyberdesk.io'
CRD_VERSION = 'v1alpha1'
CRD_PLURAL = 'startcyberdeskoperators'

@kopf.on.create(CRD_GROUP, CRD_VERSION, CRD_PLURAL)
def handle_create(spec, name, meta, logger, **kwargs):
    """
    Handle the creation of a StartCyberdeskOperator resource.
    """
    logger.info(f"StartCyberdeskOperator '{name}' created. Spec: {spec}")
    # Add more logic here as needed
    pass

# Add other handlers (update, delete, field changes, etc.) here later
