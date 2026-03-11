FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for layer caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port (Render sets PORT)
EXPOSE 8000

# Run migrations/seed then start server
CMD ["sh", "-c", "python seed_rules.py 2>/dev/null || true && uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"]
