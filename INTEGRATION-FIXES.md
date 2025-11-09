# Frontend Integration Fixes

## Issues Fixed

### 1. Root Path Serving JSON Instead of Frontend

**Problem:** Visiting `http://localhost:8506/` returned JSON:
```json
{"name":"ACE Connection Logger API","version":"0.2.0","status":"running"}
```

**Cause:** The `@app.get("/")` route was defined before the catch-all route in `api.py`, so it matched first.

**Fix:** Removed the explicit root route from `api.py:121-128`. Now the catch-all route serves the Vue.js frontend at `/`.

### 2. Misleading Startup Messages

**Problem:** Container logs said to run frontend separately even when it's already integrated.

**Cause:** `main.py` always displayed "Run 'cd frontend && npm run dev'" message.

**Fix:** Updated `main.py` to check if frontend is built and display appropriate message:
- ✅ If `frontend/dist/` exists: "Dashboard available at http://host:port/"
- ❌ If not built: Instructions to run dev server or build

## Current Routing

After fixes, the routing hierarchy is:

```
Priority 1: /api/*              → REST API endpoints
Priority 2: /docs, /redoc       → API documentation
Priority 3: /health             → Health check
Priority 4: /assets/*           → Static assets (CSS, JS)
Priority 5: /*                  → Vue.js SPA (catch-all)
```

## How It Works Now

### Production Mode (Built Frontend)
```bash
# Build frontend
cd frontend && npm run build && cd ..

# Start server
uv run python main.py monitor

# Output:
# Starting integrated monitoring + API server on localhost:8506...
# API documentation available at http://localhost:8506/docs
# Dashboard available at http://localhost:8506/
# (Frontend is built and integrated)
```

Visit `http://localhost:8506/` → Vue.js Dashboard ✅

### Development Mode (No Built Frontend)
```bash
# Start API server
uv run python main.py monitor

# Output:
# Starting integrated monitoring + API server on localhost:8506...
# API documentation available at http://localhost:8506/docs
# Frontend not built. For development, run in separate terminal:
#   cd frontend && npm run dev
# Or build for production:
#   cd frontend && npm run build

# In separate terminal:
cd frontend && npm run dev
```

Visit `http://localhost:5173/` → Vue.js Dashboard with hot-reload ✅

### Docker (Always Built)
```bash
docker-compose up -d
```

Visit `http://localhost:8506/` → Vue.js Dashboard ✅

The Dockerfile multi-stage build ensures frontend is always built in the container.

## Files Changed

1. **api.py** - Removed explicit `@app.get("/")` route
2. **main.py** - Smart detection of built frontend with appropriate messages
3. **frontend/dist/** - Rebuilt with updated configuration

## Testing

```bash
# Test that API loads correctly
uv run python -c "from api import app; print('✓ API loads')"

# Test that catch-all route exists
uv run python -c "from api import app; routes = [r.path for r in app.routes]; print('✓ Catch-all exists' if any('{full_path' in str(r.path) for r in app.routes) else '✗ Missing')"

# Test that frontend is built
test -f frontend/dist/index.html && echo "✓ Frontend built" || echo "✗ Frontend not built"

# Test integrated deployment
./test-integrated-deployment.sh
```

## URL Reference

| URL | What You Get | When Available |
|-----|-------------|----------------|
| `http://localhost:8506/` | Vue.js Dashboard | After `npm run build` or in Docker |
| `http://localhost:8506/docs` | API Documentation | Always |
| `http://localhost:8506/api/status` | System Status JSON | Always |
| `http://localhost:8506/health` | Health Check | Always |
| `http://localhost:5173/` | Vue.js Dashboard (dev) | When running `npm run dev` |

## Container Behavior

When you run the Docker container:

1. ✅ Dockerfile builds frontend during image creation
2. ✅ FastAPI serves frontend at root path `/`
3. ✅ Single port (8506) serves everything
4. ✅ No separate frontend service needed

The container logs will show:
```
Starting integrated monitoring + API server on 0.0.0.0:8506...
API documentation available at http://0.0.0.0:8506/docs
Dashboard available at http://0.0.0.0:8506/
(Frontend is built and integrated)
```
