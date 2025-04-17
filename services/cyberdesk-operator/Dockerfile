FROM python:3.12

WORKDIR /app

# Copy requirements first for layer caching
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY handlers/controller.py /app/

CMD kopf run /app/controller.py --liveness=http://0.0.0.0:8080/healthz --all-namespaces