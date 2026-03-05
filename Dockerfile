# Connexify License Server – Cloud Run container
FROM python:3.12-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Cloud Run will set PORT env var (default 8080)
ENV PORT=8080
EXPOSE 8080

# Run with uvicorn – workers=1 keeps in-memory state consistent
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT} --workers 1"]
