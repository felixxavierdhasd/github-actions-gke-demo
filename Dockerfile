FROM python:3.11-slim

WORKDIR /app

# Install system dependencies needed for bcrypt
RUN apt-get update && apt-get install -y \
    build-essential \
    libssl-dev \
    python3-dev \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy .env and app code
COPY .env .
COPY . .

# Expose port
EXPOSE 8001

# Run the FastAPI app
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]
