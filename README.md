# ace-connection-logger

Network connectivity monitoring tool with ping statistics and interactive dashboard.

## Features

- **Continuous Monitoring**: Ping configurable hosts at regular intervals (default: once per minute)
- **Detailed Statistics**: Track success rates, min/max/average latency for each host
- **SQLite Database**: Efficiently stores historical ping data with automatic cleanup
- **Interactive Dashboard**: Modern Vue.js dashboard with real-time visualizations
- **REST API**: FastAPI backend with comprehensive API documentation
- **Outage Tracking**: Detailed event log of network outages with duration and recovery metrics
- **Flexible Configuration**: YAML-based configuration for hosts and settings
- **Automatic Cleanup**: Removes records older than 90 days (configurable)
- **CLI Interface**: Easy-to-use command-line interface with multiple commands

## Installation

### Option 1: Docker (Recommended for Production)

The easiest way to run ACE Connection Logger is with Docker:

```bash
# Using Docker Compose
docker-compose up -d

# Access the dashboard at http://localhost:8506
```

See [DOCKER.md](DOCKER.md) for detailed Docker deployment instructions.

### Option 2: Local Development

This project uses `uv` for dependency management. Make sure you have `uv` installed:

```bash
# Install dependencies
uv sync

# Activate the virtual environment
source .venv/bin/activate  # On Unix/macOS
# or
.venv\Scripts\activate  # On Windows
```

## Quick Start

1. **Initialize Configuration**:
   ```bash
   python main.py init-config
   ```
   This creates a `config.yaml` file with default settings.

2. **Edit Configuration**:
   Edit `config.yaml` to add your hosts:
   ```yaml
   monitoring:
     interval_seconds: 60  # Check every minute
     ping_count: 5         # 5 pings per check
     timeout_seconds: 2    # 2 second timeout

   hosts:
     - name: Google DNS
       address: 8.8.8.8
     - name: Cloudflare DNS
       address: 1.1.1.1
     - name: Local Gateway
       address: 192.168.1.1
   ```

3. **Start Monitoring with API Server**:
   ```bash
   python main.py monitor
   ```
   This automatically:
   - Starts continuous monitoring in the background
   - Launches the FastAPI server
   - API documentation available at http://localhost:8506/docs

4. **Access the Dashboard**:

   **For Development** (with hot-reload):
   ```bash
   # In a separate terminal
   cd frontend
   npm install  # First time only
   npm run dev
   ```
   Then open http://localhost:5173 in your browser.

   **For Production** (integrated with API):
   ```bash
   # Build the frontend first
   cd frontend && npm run build && cd ..

   # Start the monitor (serves built frontend + API)
   python main.py monitor
   ```
   Then open http://localhost:8506 in your browser.

   **Note**: The Docker container automatically builds and serves the frontend - no separate commands needed!

## CLI Commands

### `init-config`
Create a default configuration file:
```bash
python main.py init-config
python main.py init-config --config /path/to/config.yaml
```

### `monitor`
Start continuous monitoring with integrated API server (recommended):
```bash
# Default: Monitoring + API server together
python main.py monitor

# Custom API port
python main.py monitor --api-port 8080

# Monitoring only, no API server
python main.py monitor --no-dashboard

# Custom config
python main.py monitor --config /path/to/config.yaml
```

**Note:** By default, `monitor` now launches both the monitoring engine and the API server in one command. The monitoring runs in the background while the API server runs in the main thread. Start the Vue.js frontend separately with `cd frontend && npm run dev`. Press Ctrl+C to stop monitoring and API server.

### `check`
Perform a single check of all hosts:
```bash
python main.py check
python main.py check --config /path/to/config.yaml
```

### `status`
Show current status of all monitored hosts:
```bash
python main.py status
python main.py status --config /path/to/config.yaml
```

### `events`
Show outage event log with detailed information:
```bash
# Show all outage events
python main.py events

# Show only active (ongoing) outages
python main.py events --active

# Filter by host address
python main.py events --host 8.8.8.8

# Show events from last 7 days
python main.py events --days 7

# Limit number of events displayed
python main.py events --limit 20

# Combine filters
python main.py events --days 7 --limit 10 --host 192.168.1.1
```

**Note:** Events are created whenever a host becomes unreachable (success_rate == 0%) and are closed when the host recovers. Each event includes start time, end time, duration, number of failed checks, and recovery success rate.

### `api`
Launch the FastAPI server standalone (without monitoring):
```bash
# Standalone API server (no monitoring)
python main.py api
python main.py api --port 8080
python main.py api --host 0.0.0.0 --port 8080
```

**Note:** You typically want to use `monitor` (which includes the API server) instead of running `api` separately. Use this command only if you want to run monitoring separately or if the monitoring is already running in another process.

### `cleanup`
Run cleanup job once to remove old records:
```bash
python main.py cleanup
python main.py cleanup --config /path/to/config.yaml
```

### `cleanup-continuous`
Run cleanup job continuously (default: every 24 hours):
```bash
python main.py cleanup-continuous
python main.py cleanup-continuous --interval 12  # Run every 12 hours
```

## Configuration

The `config.yaml` file supports the following options:

```yaml
monitoring:
  interval_seconds: 60      # How often to check hosts (seconds)
  ping_count: 5            # Number of pings per check
  timeout_seconds: 2       # Timeout for each ping

hosts:
  - name: Host Name        # Human-readable name
    address: 8.8.8.8       # IP address or hostname

database:
  path: connection_logs.db # SQLite database file path
  retention_days: 90       # Keep records for this many days

dashboard:
  port: 8501              # Dashboard port
  host: localhost         # Dashboard host
```

## Dashboard Features

The Vue.js dashboard provides:

- **Real-time Status Overview**: Current status of all monitored hosts with color-coded health indicators
- **Active Outages Alert**: Highlighted section showing ongoing outages with duration and failed check counts
- **Performance Trends**: Interactive Chart.js visualizations with dual-axis charts
  - Average, min, and max latency over time
  - Success rate percentage overlay
  - Configurable time ranges (1 hour, 6 hours, 24 hours, 7 days)
  - Host selector for detailed analysis
- **Recent Outage Events**: Complete event log showing resolved outages with duration and recovery metrics
- **Auto-refresh**: Automatic data updates every 30 seconds
- **Responsive Design**: Modern, clean interface that works on desktop and mobile

## API Features

The FastAPI backend provides a comprehensive REST API:

- **Interactive Documentation**: Swagger UI at `/docs` and ReDoc at `/redoc`
- **11 API Endpoints**: Complete access to all monitoring data
  - `/api/status` - System status and monitoring configuration
  - `/api/ping-results/latest` - Latest results for all hosts
  - `/api/ping-results` - Historical ping results with filtering
  - `/api/statistics/{host_address}` - Aggregated statistics per host
  - `/api/outages` - Outage event log with filters
  - `/api/outages/active` - Currently active outages
  - `/api/outages/statistics/{host_address}` - Outage statistics per host
  - `/api/hosts` - List of all monitored hosts
  - `/api/hosts/{host_address}/active-outage` - Check for active outage
  - `/health` - Health check endpoint
- **CORS Support**: Cross-origin requests enabled for frontend integration
- **Type-safe**: Pydantic models for request/response validation

## Database Schema

The SQLite database stores ping results and outage events with the following schemas:

### Ping Results Table
```sql
CREATE TABLE ping_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    host_name TEXT NOT NULL,
    host_address TEXT NOT NULL,
    timestamp DATETIME NOT NULL,
    success_count INTEGER NOT NULL,
    failure_count INTEGER NOT NULL,
    success_rate REAL NOT NULL,
    min_latency REAL,
    max_latency REAL,
    avg_latency REAL,
    UNIQUE(host_address, timestamp)
);
```

Indexes are created on `timestamp`, `host_address`, and `(host_address, timestamp)` for efficient queries.

### Outage Events Table
```sql
CREATE TABLE outage_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    host_name TEXT NOT NULL,
    host_address TEXT NOT NULL,
    event_type TEXT NOT NULL,
    start_time DATETIME NOT NULL,
    end_time DATETIME,
    duration_seconds INTEGER,
    checks_failed INTEGER NOT NULL DEFAULT 0,
    checks_during_outage INTEGER NOT NULL DEFAULT 0,
    recovery_success_rate REAL,
    notes TEXT
);
```

Indexes are created on `host_address`, `start_time`, `end_time`, and `(host_address, start_time)` for efficient event queries. The `event_type` field is set to 'outage_start' when created and remains until the outage is resolved.

## Architecture

The project is organized into modular components:

### Backend (Python)
- **`config.py`**: Configuration management with YAML support
- **`database.py`**: SQLite database layer with efficient queries and outage event tracking
- **`monitor.py`**: Ping monitoring logic with cross-platform support and outage detection
- **`cleanup.py`**: Automatic cleanup of old records
- **`api.py`**: FastAPI REST API with 11 endpoints and Pydantic models
- **`main.py`**: CLI interface using Click

### Frontend (Vue.js)
- **`frontend/src/App.vue`**: Main application component with dashboard layout
- **`frontend/src/components/HostCard.vue`**: Host status display with color-coded indicators
- **`frontend/src/components/OutageCard.vue`**: Outage event display component
- **`frontend/src/components/LatencyChart.vue`**: Chart.js integration for performance visualization
- **`frontend/src/services/api.js`**: Axios-based API service layer

### Data Flow
1. **Monitoring**: `monitor.py` performs periodic pings and stores results in SQLite
2. **Event Tracking**: Automatic outage event creation and management
3. **API Layer**: FastAPI serves data through REST endpoints
4. **Frontend**: Vue.js fetches data and updates dashboard in real-time
5. **Cleanup**: Automated removal of old records based on retention policy

## Production Deployment

For production use, consider:

1. **Run as a Service**: Use systemd (Linux) or similar to run monitoring and API as background services
2. **Separate Processes**: Run monitor (with API), cleanup, and frontend as separate services
3. **Network Access**: Ensure the monitoring process has ICMP (ping) permissions
4. **Frontend Deployment**: Build Vue.js frontend for production and serve with nginx
5. **API Security**: Use a reverse proxy (nginx) for the API with HTTPS and rate limiting
6. **Monitoring Multiple Instances**: Each instance can use its own database or share one

### Example systemd service file for monitoring + API

`/etc/systemd/system/ace-monitor.service`:

```ini
[Unit]
Description=ACE Connection Logger Monitor and API
After=network.target

[Service]
Type=simple
User=your-user
WorkingDirectory=/path/to/ace-connection-logger
ExecStart=/path/to/.venv/bin/python main.py monitor
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### Frontend production build

```bash
cd frontend
npm run build

# Serve the dist/ folder with nginx or any static file server
```

### Nginx configuration example

```nginx
# API proxy
location /api/ {
    proxy_pass http://localhost:8501;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
}

# Serve Vue.js frontend
location / {
    root /path/to/ace-connection-logger/frontend/dist;
    try_files $uri $uri/ /index.html;
}
```

## Error Handling

The application includes comprehensive error handling:

- Failed pings are recorded with 0% success rate
- Database errors are logged and monitoring continues
- Network timeouts are handled gracefully
- Configuration errors fall back to defaults

## Development

To contribute or modify:

```bash
# Install dev dependencies
uv sync --group dev

# Run linting
ruff check .

# Run formatting
ruff format .

# Run tests
pytest
```

## License

See LICENSE file for details.

## Support

For issues, questions, or contributions, please open an issue on the project repository.
