# ace-connection-logger

Network connectivity monitoring tool with ping statistics and interactive dashboard.

## Features

- **Continuous Monitoring**: Ping configurable hosts at regular intervals (default: once per minute)
- **Detailed Statistics**: Track success rates, min/max/average latency for each host
- **SQLite Database**: Efficiently stores historical ping data with automatic cleanup
- **Interactive Dashboard**: Beautiful Streamlit dashboard with real-time visualizations
- **Flexible Configuration**: YAML-based configuration for hosts and settings
- **Automatic Cleanup**: Removes records older than 90 days (configurable)
- **CLI Interface**: Easy-to-use command-line interface with multiple commands

## Installation

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

3. **Start Monitoring**:
   ```bash
   python main.py monitor
   ```

4. **Launch Dashboard** (in a separate terminal):
   ```bash
   python main.py dashboard
   ```
   Then open http://localhost:8501 in your browser.

## CLI Commands

### `init-config`
Create a default configuration file:
```bash
python main.py init-config
python main.py init-config --config /path/to/config.yaml
```

### `monitor`
Start continuous monitoring (runs indefinitely):
```bash
python main.py monitor
python main.py monitor --config /path/to/config.yaml
```

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

### `dashboard`
Launch the interactive Streamlit dashboard:
```bash
python main.py dashboard
python main.py dashboard --port 8080
python main.py dashboard --host 0.0.0.0 --port 8080
```

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

The Streamlit dashboard provides:

- **Real-time Status Overview**: Current status of all monitored hosts
- **Historical Graphs**:
  - Success rate over time with threshold indicators
  - Latency trends with min/max ranges
- **Time Range Filters**: View data from last hour to all time
- **Statistics Summary**: Aggregated statistics for selected time ranges
- **Success Rate Distribution**: Histogram showing reliability patterns
- **Recent Results Table**: Detailed view of recent checks
- **Auto-refresh**: Optional automatic dashboard updates

## Database Schema

The SQLite database stores ping results with the following schema:

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

## Architecture

The project is organized into modular components:

- **`config.py`**: Configuration management with YAML support
- **`database.py`**: SQLite database layer with efficient queries
- **`monitor.py`**: Ping monitoring logic with cross-platform support
- **`cleanup.py`**: Automatic cleanup of old records
- **`dashboard.py`**: Streamlit dashboard with interactive visualizations
- **`main.py`**: CLI interface using Click

## Production Deployment

For production use, consider:

1. **Run as a Service**: Use systemd (Linux) or similar to run monitoring as a background service
2. **Separate Processes**: Run monitor, cleanup, and dashboard as separate services
3. **Network Access**: Ensure the monitoring process has ICMP (ping) permissions
4. **Dashboard Security**: Use a reverse proxy (nginx) for the dashboard with authentication
5. **Monitoring Multiple Instances**: Each instance can use its own database or share one

Example systemd service file (`/etc/systemd/system/ace-monitor.service`):

```ini
[Unit]
Description=ACE Connection Logger Monitor
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
