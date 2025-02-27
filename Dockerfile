FROM --platform=linux/amd64 python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Make sure persona.jsonl is explicitly copied
COPY persona.jsonl /app/persona.jsonl

# Create a non-root user
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

# Expose the port
EXPOSE 9350

# Run the application with explicit Python path
CMD ["/usr/local/bin/python", "-m", "uvicorn", "app:app", "--host", "0.0.0.0", "--port", "9350"]
