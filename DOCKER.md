# Docker Deployment Guide

This guide explains how to build and run ACE Connection Logger as a Docker container with the Vue.js frontend integrated into the FastAPI backend.

## Quick Start with Docker Compose

The easiest way to run the application is with Docker Compose:

```bash
# Build and start the container
docker-compose up -d

# View logs
docker-compose logs -f

# Stop the container
docker-compose down
```

The application will be available at:
- **Dashboard**: http://localhost:8506
- **API Documentation**: http://localhost:8506/docs

## Manual Docker Build

### Build the Image

```bash
docker build -t ace-connection-logger:latest .
```

The build process:
1. **Stage 1**: Builds the Vue.js frontend using Node.js 20
2. **Stage 2**: Creates Python runtime and copies built frontend

### Run the Container

```bash
docker run -d \
  --name ace-connection-logger \
  -p 8506:8506 \
  -v $(pwd)/data:/data \
  -v $(pwd)/config.yaml:/app/config.yaml:ro \
  ace-connection-logger:latest
```

### Environment Variables

You can customize the container with these environment variables:

- `API_HOST`: API server host (default: `0.0.0.0`)
- `API_PORT`: API server port (default: `8506`)
- `DATABASE_PATH`: Path to SQLite database (default: `/data/connection_logs.db`)

Example with custom port:

```bash
docker run -d \
  --name ace-connection-logger \
  -p 9000:9000 \
  -e API_PORT=9000 \
  -v $(pwd)/data:/data \
  ace-connection-logger:latest
```

## Architecture

The Docker container runs a **single service** that provides:

1. **Network Monitoring**: Periodic ping checks in background thread
2. **FastAPI Backend**: REST API with 11 endpoints
3. **Static Frontend**: Built Vue.js dashboard served by FastAPI

This eliminates the need for separate frontend and backend containers.

## Volume Mounts

### Database Persistence

Mount a volume for the database to persist data:

```bash
-v $(pwd)/data:/data
```

The database will be stored at `/data/connection_logs.db` inside the container.

### Custom Configuration

Mount your custom `config.yaml`:

```bash
-v $(pwd)/config.yaml:/app/config.yaml:ro
```

Example `config.yaml`:

```yaml
monitoring:
  interval_seconds: 60
  ping_count: 5
  timeout_seconds: 2

hosts:
  - name: Google DNS
    address: 8.8.8.8
  - name: Cloudflare DNS
    address: 1.1.1.1

database:
  path: /data/connection_logs.db
  retention_days: 90

dashboard:
  port: 8506
  host: 0.0.0.0
```

## Health Check

The container includes a health check that runs every 30 seconds:

```bash
# Check container health
docker ps

# View health check logs
docker inspect --format='{{json .State.Health}}' ace-connection-logger | jq
```

## Docker Compose Configuration

The included `docker-compose.yml` provides:

- Automatic container restart
- Database persistence
- Health checks
- Port mapping
- Custom network

### Start with Docker Compose

```bash
# Start in foreground
docker-compose up

# Start in background
docker-compose up -d

# View logs
docker-compose logs -f

# Stop and remove containers
docker-compose down

# Stop and remove containers + volumes
docker-compose down -v
```

## Production Deployment

### 1. Build for Production

```bash
docker build -t ace-connection-logger:v0.2.0 .
```

### 2. Push to Registry (optional)

```bash
# Tag for your registry
docker tag ace-connection-logger:v0.2.0 your-registry/ace-connection-logger:v0.2.0

# Push to registry
docker push your-registry/ace-connection-logger:v0.2.0
```

### 3. Run in Production

```bash
docker run -d \
  --name ace-connection-logger \
  --restart unless-stopped \
  -p 8506:8506 \
  -v /var/lib/ace-connection-logger/data:/data \
  -v /etc/ace-connection-logger/config.yaml:/app/config.yaml:ro \
  ace-connection-logger:v0.2.0
```

### 4. Behind Nginx Reverse Proxy

```nginx
server {
    listen 80;
    server_name monitoring.example.com;

    location / {
        proxy_pass http://localhost:8506;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## Troubleshooting

### View Container Logs

```bash
docker logs -f ace-connection-logger
```

### Execute Commands Inside Container

```bash
# Check status
docker exec ace-connection-logger python main.py status

# View events
docker exec ace-connection-logger python main.py events --limit 10

# Interactive shell
docker exec -it ace-connection-logger /bin/bash
```

### Database Access

```bash
# Copy database from container
docker cp ace-connection-logger:/data/connection_logs.db ./connection_logs.db

# Inspect database
sqlite3 ./connection_logs.db "SELECT * FROM ping_results ORDER BY timestamp DESC LIMIT 10;"
```

### Rebuild After Changes

```bash
# Rebuild and restart
docker-compose up -d --build

# Or manually
docker build -t ace-connection-logger:latest .
docker stop ace-connection-logger
docker rm ace-connection-logger
docker run -d --name ace-connection-logger -p 8506:8506 -v $(pwd)/data:/data ace-connection-logger:latest
```

## Image Size Optimization

The multi-stage build keeps the final image size small:

- **Stage 1 (builder)**: ~1.5GB (Node.js + build artifacts)
- **Stage 2 (final)**: ~200-300MB (Python slim + app only)

Only the final stage is included in the image.

## Security Considerations

1. **Don't run as root**: Consider adding a non-root user in Dockerfile
2. **Limit CORS**: Update `api.py` to restrict allowed origins in production
3. **Use secrets**: Don't hardcode sensitive data in config files
4. **Network isolation**: Use Docker networks to isolate containers
5. **Regular updates**: Keep base images updated for security patches

## Development vs Production

### Development (separate services)

```bash
# Terminal 1: API server
uv run python main.py monitor

# Terminal 2: Frontend dev server
cd frontend && npm run dev
```

### Production (single container)

```bash
# Single container serves both
docker-compose up -d
```

The frontend is built at container build time and served as static files by FastAPI.
