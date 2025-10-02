FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend
COPY . .

EXPOSE 8000
# Run server with SSL
CMD ["uvicorn", "backend:app", "--host", "0.0.0.0", "--port", "8000", "--ssl-keyfile", "/certs/localhost+2-key.pem", "--ssl-certfile", "/certs/localhost+2.pem"]
