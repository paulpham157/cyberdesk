FROM python:3.9-slim

WORKDIR /app

# Copy requirements first for layer caching
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Create non-root user
RUN groupadd -r cyberdesk && \
    useradd --no-log-init -r -g cyberdesk cyberdesk

# Copy the application code
COPY handlers/ /app/handlers/
COPY main.py /app/

# Set proper permissions
RUN chown -R cyberdesk:cyberdesk /app && \
    chmod +x /app/main.py && \
    adduser --disabled-password --gecos "" cyberdesk && \
    # Make directories for kopf persistence
    mkdir -p /tmp/kopf && \
    chown -R cyberdesk:cyberdesk /tmp/kopf

# Switch to non-root user
USER cyberdesk

# Expose health check and metrics ports
EXPOSE 8080
EXPOSE 8081

# Environment variables
ENV PYTHONUNBUFFERED=1 \
    KOPF_LIVENESS_ENDPOINT="http://0.0.0.0:8080/healthz" \
    METRICS_PORT="8081" \
    LOG_LEVEL="INFO" \
    KOPF_PEERING="cyberdesk-operator"

# Set security options
ENV PYTHONHASHSEED=random \
    PYTHONDONTWRITEBYTECODE=1

# Run kopf as the entrypoint with proper arguments for leader election
# TODO: Fix this. This is supposed to run operator.py, not main.py
ENTRYPOINT ["kopf", "run"]
CMD ["--all-namespaces", "--liveness=http://0.0.0.0:8080/healthz", "--peering=cyberdesk-operator", "main.py"] 