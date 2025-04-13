#!/usr/bin/env python3

import kopf
import logging
import os
import sys
import socket
from datetime import datetime
from dotenv import load_dotenv

# Import our handlers
from handlers.controller import *

# Load environment variables from .env file (for local development)
load_dotenv()

# Configure logging with more details
def configure_logging():
    """Configure logging with hostname and pod name for better traceability"""
    log_level = os.environ.get("LOG_LEVEL", "INFO")
    log_format = '%(asctime)s [%(levelname)s] [%(name)s] [%(hostname)s] [%(pod_name)s] %(message)s'
    
    # Add hostname to log format
    hostname = socket.gethostname()
    pod_name = os.environ.get("POD_NAME", "unknown")
    
    logging.basicConfig(
        level=getattr(logging, log_level),
        format=log_format,
        stream=sys.stdout
    )
    
    # Add custom fields to the log record
    old_factory = logging.getLogRecordFactory()
    def record_factory(*args, **kwargs):
        record = old_factory(*args, **kwargs)
        record.hostname = hostname
        record.pod_name = pod_name
        return record
    logging.setLogRecordFactory(record_factory)
    
    logging.info(f"Logging configured at {log_level} level")

if __name__ == "__main__":
    # Configure logging
    configure_logging()
    
    # Get the namespace for logging purposes
    namespace = os.environ.get("KOPF_NAMESPACE", "cyberdesk-system")
    
    # Log startup message
    logging.info(f"Cyberdesk Operator starting in namespace {namespace}")
    logging.info("Watching for Cyberdesk resources across all namespaces")
    
    # Configure leader election
    leader_id = os.environ.get("POD_NAME", socket.gethostname())
    logging.info(f"Configuring leader election with leader ID: {leader_id}")
    
    # Start the operator - This is only used when running locally for development
    # In production, kopf is run using the CLI directly
    # Uses leader election to ensure high availability in multi-replica deployments
    kopf.run(
        standalone=True,  # Run as a standalone process
        clusterwide=True,  # Watch cluster-wide resources across all namespaces
        peering_name=os.environ.get("KOPF_PEERING", "cyberdesk-operator"),  # Name of the peering resource
        identity=leader_id,  # Unique ID for this operator instance
        priority=0,  # Priority in leader election (lower value = higher priority)
    ) 