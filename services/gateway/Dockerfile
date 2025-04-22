FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app code + noVNC client
COPY main.py .
COPY noVNC/ ./noVNC/

# Expose HTTP port
EXPOSE 80

# Launch with Uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80"]
