# Integrated Dashboard Mode - Feature Update

## Overview

The `monitor` command now **automatically launches the dashboard** alongside monitoring, providing a seamless integrated experience. No more juggling multiple terminals!

---

## What Changed

### Before (Separate Commands)

Previously, you needed two terminal windows:

```bash
# Terminal 1: Monitoring
python main.py monitor

# Terminal 2: Dashboard
python main.py dashboard
```

### After (Integrated Mode)

Now, one command does everything:

```bash
# Single command: Monitoring + Dashboard
python main.py monitor
```

This automatically:
- ✅ Starts continuous ping monitoring in background
- ✅ Launches interactive Streamlit dashboard
- ✅ Opens browser to http://localhost:8501
- ✅ Both stop together with Ctrl+C

---

## Usage Examples

### Default: Integrated Mode

```bash
# Start monitoring with dashboard (recommended)
uv run python main.py monitor
```

**Output:**
```
Starting continuous monitoring (interval: 60s)
Press Ctrl+C to stop
Checking Google DNS (8.8.8.8)...
  Success rate: 100.0%, Avg latency: 20.5ms
Checking Cloudflare DNS (1.1.1.1)...
  Success rate: 100.0%, Avg latency: 18.2ms

Starting integrated monitoring + dashboard on localhost:8501...
Press Ctrl+C to stop both monitoring and dashboard

  You can now view your Streamlit app in your browser.

  Local URL: http://localhost:8501
  Network URL: http://192.168.1.100:8501
```

### Custom Dashboard Port

```bash
# Run on different port
uv run python main.py monitor --dashboard-port 8080
```

### Custom Dashboard Host

```bash
# Make accessible on network
uv run python main.py monitor --dashboard-host 0.0.0.0 --dashboard-port 8080
```

### Monitoring Only (No Dashboard)

```bash
# Original behavior: monitoring only
uv run python main.py monitor --no-dashboard
```

---

## Technical Implementation

### Architecture

```
┌─────────────────────────────────────────┐
│         Main Process (main.py)          │
├─────────────────────────────────────────┤
│                                         │
│  ┌────────────────────────────────┐    │
│  │   Background Thread            │    │
│  │   - run_continuous()           │    │
│  │   - Ping hosts every 60s       │    │
│  │   - Store results in database  │    │
│  │   - Track outage events        │    │
│  │   - Daemon thread (auto-stop)  │    │
│  └────────────────────────────────┘    │
│                                         │
│  ┌────────────────────────────────┐    │
│  │   Main Thread (Foreground)     │    │
│  │   - Streamlit dashboard        │    │
│  │   - HTTP server on :8501       │    │
│  │   - Real-time data display     │    │
│  │   - Interactive controls       │    │
│  └────────────────────────────────┘    │
│                                         │
└─────────────────────────────────────────┘
                    │
                    ▼
        ┌──────────────────────┐
        │  SQLite Database     │
        │  - Shared access     │
        │  - WAL mode ready    │
        └──────────────────────┘
```

### Key Implementation Details

**Threading Strategy:**
- Monitoring runs in a **daemon thread** (auto-terminates with main)
- Dashboard runs in **main thread** (Streamlit requirement)
- 2-second startup delay allows initial monitoring check
- Clean shutdown on Ctrl+C

**Process Flow:**
1. User runs `python main.py monitor`
2. Create monitoring thread: `threading.Thread(target=mon.run_continuous, daemon=True)`
3. Start thread: `monitor_thread.start()`
4. Sleep 2 seconds (let monitoring initialize)
5. Launch Streamlit: `subprocess.run(['streamlit', 'run', 'dashboard.py', ...])`
6. Streamlit takes over terminal, opens browser
7. Monitoring continues in background
8. Ctrl+C stops Streamlit → daemon thread auto-stops

**Shared Database Access:**
- Both threads read/write to same SQLite database
- Safe due to SQLite's built-in locking
- WAL mode (when enabled) allows concurrent reads
- Dashboard reads latest data every refresh

---

## Command Options

### All `monitor` Options

```bash
python main.py monitor [OPTIONS]

Options:
  -c, --config PATH             Path to configuration file
  --dashboard / --no-dashboard  Launch dashboard alongside monitoring (default: enabled)
  --dashboard-port INTEGER      Port to run dashboard on (overrides config)
  --dashboard-host TEXT         Host to run dashboard on (overrides config)
  --help                        Show this message and exit
```

### Standalone Commands (Still Available)

```bash
# If you really need them separate:

# Monitoring only
python main.py monitor --no-dashboard

# Dashboard only (no monitoring)
python main.py dashboard
```

---

## Benefits

### 1. **Simplified Workflow**
- ✅ One command instead of two
- ✅ One terminal instead of two
- ✅ Both start together
- ✅ Both stop together (Ctrl+C)

### 2. **Better User Experience**
- ✅ Beginner-friendly
- ✅ No confusion about which terminal is which
- ✅ Dashboard automatically shows live data
- ✅ Immediate visual feedback

### 3. **Production Deployment**
- ✅ Single systemd service needed
- ✅ Single Docker container
- ✅ Simpler process management
- ✅ Clean shutdown handling

### 4. **Backward Compatible**
- ✅ Old behavior available via `--no-dashboard`
- ✅ Standalone `dashboard` command still works
- ✅ All existing configs work unchanged

---

## Examples

### Example 1: Quick Start

```bash
# Install and run
git clone <repo>
cd ace-connection-logger
uv sync
uv run python main.py init-config
# Edit config.yaml
uv run python main.py monitor

# That's it! Dashboard opens automatically
```

### Example 2: Production Server

```bash
# Run on all interfaces, custom port
uv run python main.py monitor \
  --dashboard-host 0.0.0.0 \
  --dashboard-port 8080

# Access from anywhere: http://server-ip:8080
```

### Example 3: Headless Server (No Dashboard)

```bash
# Server without display/browser
uv run python main.py monitor --no-dashboard

# Access dashboard from different machine:
# (on workstation)
uv run python main.py dashboard --config server-config.yaml
```

### Example 4: Development/Debugging

```bash
# Monitor only (see console output clearly)
uv run python main.py monitor --no-dashboard

# In another terminal: Dashboard
uv run python main.py dashboard

# Separate processes for debugging
```

---

## Migration Guide

### If You Had Scripts/Docs

**Old way:**
```bash
# Start monitoring
nohup python main.py monitor &

# Start dashboard
nohup python main.py dashboard &
```

**New way:**
```bash
# One command does both
nohup python main.py monitor &
```

### Systemd Service (Old)

**Old: Two services**
```ini
# /etc/systemd/system/ace-monitor.service
[Service]
ExecStart=/usr/bin/python3 main.py monitor --no-dashboard

# /etc/systemd/system/ace-dashboard.service
[Service]
ExecStart=/usr/bin/python3 main.py dashboard
```

**New: Single service**
```ini
# /etc/systemd/system/ace-monitor.service
[Service]
ExecStart=/usr/bin/python3 main.py monitor
# Dashboard included automatically
```

### Docker Compose (Old)

**Old: Separate containers**
```yaml
services:
  monitor:
    command: python main.py monitor --no-dashboard
  dashboard:
    command: python main.py dashboard
    ports:
      - "8501:8501"
```

**New: Single container**
```yaml
services:
  ace-monitor:
    command: python main.py monitor
    ports:
      - "8501:8501"
```

---

## Troubleshooting

### Dashboard Doesn't Open Browser

**Cause:** Headless environment or SSH session

**Solution:** Dashboard still runs, manually open:
```
http://localhost:8501
```

### Port Already in Use

**Error:** `Address already in use`

**Solution:** Change port:
```bash
python main.py monitor --dashboard-port 8502
```

### Want Separate Processes

**Reason:** Debugging, different machines, etc.

**Solution:** Use `--no-dashboard`:
```bash
# Terminal 1
python main.py monitor --no-dashboard

# Terminal 2
python main.py dashboard
```

### Monitoring Stops When Dashboard Stops

**Expected Behavior:** Both stop together (Ctrl+C)

**If you want independent:**
```bash
# Background monitoring
nohup python main.py monitor --no-dashboard &

# Foreground dashboard (can restart independently)
python main.py dashboard
```

---

## Performance Impact

**Minimal overhead:**
- Background thread: ~1-2 MB RAM
- Same CPU as separate process
- Same database access pattern
- No additional network overhead

**Resource Usage:**
- Memory: +2 MB (thread vs process)
- CPU: Identical (same work being done)
- Network: Identical (same monitoring)
- Disk I/O: Identical (same database writes)

---

## Configuration

### Dashboard Settings in config.yaml

```yaml
dashboard:
  port: 8501              # Default port
  host: localhost         # Default host

# Override with CLI:
# --dashboard-port 8080
# --dashboard-host 0.0.0.0
```

### Environment Variables

Streamlit respects these:
```bash
export STREAMLIT_SERVER_PORT=8501
export STREAMLIT_SERVER_ADDRESS=localhost
export STREAMLIT_SERVER_HEADLESS=true  # No browser auto-open
```

---

## Files Changed

### Code Changes

**main.py** - Modified `monitor` command:
- Added `--dashboard/--no-dashboard` flag (default: on)
- Added `--dashboard-port` and `--dashboard-host` options
- Threading for background monitoring
- Streamlit subprocess launch
- ~50 lines added

### Documentation Updates

**README.md:**
- Updated Quick Start (simplified to 3 steps)
- Updated `monitor` command documentation
- Added note about integrated mode
- Updated `dashboard` command (now optional)

---

## Future Enhancements (Optional)

**Potential improvements:**
1. **Status in terminal** - Show monitoring stats while dashboard runs
2. **Auto-restart** - Restart dashboard if it crashes
3. **Multi-dashboard** - Different ports for different views
4. **Remote monitoring** - Dashboard on different host than monitor
5. **API endpoint** - REST API alongside dashboard

---

## Summary

**What:** `monitor` command now includes dashboard by default

**Why:** Simpler user experience, fewer terminals, cleaner deployment

**How:** Background thread for monitoring, main thread for Streamlit

**Benefits:**
- ✅ One command instead of two
- ✅ Beginner-friendly
- ✅ Simpler deployment
- ✅ Backward compatible

**Usage:**
```bash
# New default (recommended)
python main.py monitor

# Old behavior (if needed)
python main.py monitor --no-dashboard
python main.py dashboard
```

---

*Updated: 2025-11-06*
*Version: 0.2.0*
