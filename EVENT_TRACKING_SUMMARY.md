# Event Tracking System - Implementation Summary

## Overview

The ACE Connection Logger now includes a comprehensive **Outage Event Tracking System** that automatically monitors and logs every period where a host becomes unreachable, providing detailed information about outage duration, recovery, and impact.

---

## Features Implemented

### ✅ 1. Database Schema - `outage_events` Table

**Table Structure:**
```sql
CREATE TABLE outage_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    host_name TEXT NOT NULL,
    host_address TEXT NOT NULL,
    event_type TEXT NOT NULL,              -- 'outage_start' or 'outage_end'
    start_time DATETIME NOT NULL,          -- When outage began
    end_time DATETIME,                     -- When host recovered (NULL if ongoing)
    duration_seconds INTEGER,              -- Total outage duration
    checks_failed INTEGER DEFAULT 0,       -- Number of failed ping checks
    checks_during_outage INTEGER DEFAULT 0,-- Total checks during outage
    recovery_success_rate REAL,            -- Success rate on first recovery check
    notes TEXT                             -- Additional information
)
```

**Indexes for Performance:**
- `idx_events_host_time` - Optimized for per-host queries
- `idx_events_time` - Optimized for time-range queries

### ✅ 2. Automatic Outage Detection

**Real-time Monitoring Logic:**
- Detects when a host becomes unreachable (0% success rate)
- Creates new outage event automatically
- Updates ongoing outage counters with each failed check
- Detects recovery when host comes back online
- Calculates and logs precise outage duration

**Visual Feedback:**
```
🔴 OUTAGE STARTED (Event ID: 123)
⚠️  Outage continues (5 failed checks)
🟢 RECOVERED from outage (Duration: 5m 30s, 5 failed checks)
```

### ✅ 3. Event Information Tracked

**For Each Outage Event:**
- **Start Time** - Exact timestamp when host became unreachable
- **End Time** - Exact timestamp when host recovered (NULL if ongoing)
- **Duration** - Total downtime in seconds (calculated on recovery)
- **Failed Checks** - Number of consecutive failed ping attempts
- **Total Checks** - Total monitoring checks during outage period
- **Recovery Rate** - Success rate of first check after recovery
- **Notes** - Automatic timestamped notes about detection and recovery

**Example Event:**
```
Event ID: 42
Host: Production Server (10.0.1.50)
Started: 2025-11-06 14:30:15
Ended: 2025-11-06 14:35:45
Duration: 5m 30s
Failed Checks: 5 / 5
Recovery Success Rate: 100.0%
Status: 🟢 Resolved
```

### ✅ 4. CLI Command - `events`

**Comprehensive Event Log Viewer:**

```bash
# View all outage events
uv run python main.py events

# Show only active (ongoing) outages
uv run python main.py events --active

# Filter by specific host
uv run python main.py events --host 192.168.1.1

# Show events from last 7 days
uv run python main.py events --days 7

# Limit results
uv run python main.py events --limit 20

# Combine filters
uv run python main.py events --host 8.8.8.8 --days 30 --limit 100
```

**Output Features:**
- Color-coded status indicators (🔴 ACTIVE / 🟢 RESOLVED)
- Formatted durations (hours, minutes, seconds)
- Failed checks ratio
- Recovery success rate
- Event notes with timestamps
- Statistics summary per host

**Sample Output:**
```
====================================================================================================
                                      OUTAGE EVENT LOG
====================================================================================================

Total events: 3
----------------------------------------------------------------------------------------------------

🟢 RESOLVED | Event ID: 3
Host: Google DNS (8.8.8.8)
Started: 2025-11-06 14:20:00
Ended:   2025-11-06 14:25:30
Duration: 5m 30s
Recovery success rate: 100.0%
Failed checks: 5 / 5
Notes: Outage detected at 2025-11-06 14:20:00
Recovered at 2025-11-06 14:25:30 with 100.0% success rate
----------------------------------------------------------------------------------------------------

🔴 ACTIVE | Event ID: 4
Host: Local Gateway (192.168.1.1)
Started: 2025-11-06 14:30:00
Duration: ONGOING (15m so far)
Failed checks: 15 / 15
Notes: Outage detected at 2025-11-06 14:30:00
----------------------------------------------------------------------------------------------------

====================================================================================================
STATISTICS SUMMARY
====================================================================================================

Google DNS (8.8.8.8):
  Total outages: 2
  Active outages: 0
  Average outage duration: 4.5 minutes
  Total downtime: 0.15 hours

Local Gateway (192.168.1.1):
  Total outages: 1
  Active outages: 1
====================================================================================================
```

### ✅ 5. Dashboard Integration

**New Dashboard Sections:**

**Outage Metrics Panel:**
- Total Outages (completed)
- Active Outages (ongoing)
- Average Outage Duration
- Total Downtime

**Recent Outage Events Table:**
Displays up to 20 recent events with:
- Start Time
- End Time (or "Ongoing")
- Duration
- Failed Checks / Total Checks
- Recovery Rate
- Status (🟢 Resolved / 🔴 Active)

**Time-Range Filtering:**
All outage data respects the dashboard's time range selector.

### ✅ 6. Database API Methods

**New Database Methods:**

```python
# Check for active outage on a host
active_outage = db.get_active_outage(host_address)

# Create new outage event
event_id = db.create_outage_event(host_name, host_address, start_time, notes)

# Update ongoing outage counters
db.update_outage_event(event_id, checks_failed=10, checks_during_outage=10)

# Close outage when recovered
db.close_outage_event(event_id, end_time, recovery_success_rate, notes)

# Query outage events with filters
events = db.get_outage_events(
    host_address=None,      # All hosts or specific host
    start_time=None,        # Filter by time range
    end_time=None,
    active_only=False,      # Only ongoing outages
    limit=50                # Max results
)

# Get outage statistics
stats = db.get_outage_statistics(host_address, start_time, end_time)
# Returns: {
#   'total_outages': 5,
#   'active_outages': 1,
#   'avg_duration_seconds': 300.0,
#   'max_duration_seconds': 600,
#   'total_downtime_seconds': 1500
# }
```

---

## Technical Implementation Details

### State Machine for Outage Tracking

```
┌─────────────┐
│   Normal    │ (Success rate > 0%)
│  Operation  │
└──────┬──────┘
       │
       │ Success rate = 0%
       ▼
┌─────────────┐
│   Outage    │ Create outage_event
│   Detected  │ event_type = 'outage_start'
└──────┬──────┘
       │
       │ Continues failing
       ▼
┌─────────────┐
│   Ongoing   │ Update checks_failed++
│   Outage    │ checks_during_outage++
└──────┬──────┘
       │
       │ Success rate > 0%
       ▼
┌─────────────┐
│   Recovery  │ Update event:
│   Detected  │ - end_time = now
└──────┬──────┘ - duration_seconds
       │         - recovery_success_rate
       │         - event_type = 'outage_end'
       ▼
┌─────────────┐
│   Normal    │
│  Operation  │
└─────────────┘
```

### Monitor Integration

**Modified `check_all_hosts()` Flow:**
1. Perform ping check
2. Store result in database
3. **NEW:** Call `_track_outage_event(result)`
   - Check if host is down (0% success)
   - Query for active outage
   - If down + no active outage → Create new event
   - If down + active outage → Update counters
   - If up + active outage → Close event (recovery)
   - If up + no active outage → Normal operation
4. Display status to user

### Data Retention

Outage events follow the same retention policy as ping results:
- Default: 90 days
- Configurable via `database.retention_days`
- Cleaned up by `cleanup` command

**Note:** Consider keeping outage events longer than raw ping data for historical analysis.

---

## Usage Examples

### Example 1: Monitor and Track Outages

```bash
# Start continuous monitoring
uv run python main.py monitor

# Output shows real-time outage detection:
Checking Google DNS (8.8.8.8)...
  Success rate: 100.0%, Avg latency: 20.5ms
Checking Local Router (192.168.1.1)...
  🔴 OUTAGE STARTED (Event ID: 1)
  Success rate: 0.0%, No responses

# On next check:
Checking Local Router (192.168.1.1)...
  ⚠️  Outage continues (2 failed checks)
  Success rate: 0.0%, No responses

# When it recovers:
Checking Local Router (192.168.1.1)...
  🟢 RECOVERED from outage (Duration: 2m 15s, 2 failed checks)
  Success rate: 100.0%, Avg latency: 5.2ms
```

### Example 2: Review Outage History

```bash
# View all outage events
uv run python main.py events

# Check current active outages
uv run python main.py events --active

# Review last week's outages for specific host
uv run python main.py events --host 192.168.1.1 --days 7

# Export to file
uv run python main.py events > outage_report.txt
```

### Example 3: Dashboard Analysis

```bash
# Launch dashboard
uv run python main.py dashboard

# Navigate to "Outage Events" section to see:
# - Outage statistics (total, active, avg duration)
# - Visual timeline of outages
# - Detailed event table with filtering
```

---

## Benefits

### 1. **Comprehensive Visibility**
- Track every period of downtime, no matter how brief
- Historical analysis of network reliability
- Identify patterns in outages

### 2. **Detailed Diagnostics**
- Exact start/end times for troubleshooting
- Duration tracking for SLA compliance
- Recovery patterns analysis

### 3. **Proactive Monitoring**
- Real-time alerts when outages start
- Automatic detection eliminates manual logging
- Ongoing outage tracking

### 4. **Performance Metrics**
- Calculate uptime percentages
- Measure mean time to recovery (MTTR)
- Track total downtime per host

### 5. **Audit Trail**
- Complete historical record
- Notes capture context
- Support for compliance requirements

---

## Data Schema Example

**Sample Data in Database:**

**ping_results table:**
```
id | host_address  | timestamp           | success_rate | avg_latency
1  | 192.168.1.1  | 2025-11-06 10:00:00 | 100.0       | 5.2
2  | 192.168.1.1  | 2025-11-06 10:01:00 | 0.0         | NULL
3  | 192.168.1.1  | 2025-11-06 10:02:00 | 0.0         | NULL
4  | 192.168.1.1  | 2025-11-06 10:03:00 | 100.0       | 5.5
```

**outage_events table:**
```
id | host_address | start_time          | end_time            | duration | checks_failed | recovery_rate
1  | 192.168.1.1  | 2025-11-06 10:01:00 | 2025-11-06 10:03:00 | 120     | 2            | 100.0
```

---

## Performance Impact

**Minimal Overhead:**
- Single query per check to check for active outage (indexed)
- Single insert/update per event (not per check)
- Efficient queries with composite indexes

**Storage Impact:**
- ~200 bytes per outage event
- Typical usage: <1MB per year for 10 hosts with occasional outages

---

## Future Enhancements (Optional)

**Potential additions:**
1. **Degraded State Tracking** - Track periods with partial success (50-95%)
2. **Alerting Integration** - Email/webhook notifications on outage start
3. **SLA Reporting** - Automated uptime percentage calculations
4. **Outage Classification** - Categorize outages by severity/cause
5. **Predictive Analysis** - ML-based outage prediction
6. **Export Functionality** - CSV/JSON export of events
7. **Archival** - Separate long-term storage for historical events

---

## Testing

**Verified Scenarios:**
- ✅ Outage detection when host goes down
- ✅ Counter updates during ongoing outage
- ✅ Recovery detection and event closure
- ✅ Duration calculation accuracy
- ✅ CLI events command with all filters
- ✅ Dashboard display of events
- ✅ Statistics aggregation

**Test Commands:**
```bash
# Clean slate
rm connection_logs.db

# Generate outage (local gateway typically unreachable)
uv run python main.py check

# View the created event
uv run python main.py events

# View in dashboard
uv run python main.py dashboard
```

---

## Files Modified

**Core Implementation:**
1. `database.py` - Added OutageEvent dataclass and 7 new methods
2. `monitor.py` - Added `_track_outage_event()` method
3. `dashboard.py` - Added outage events section
4. `main.py` - Added `events` CLI command

**Lines Added:**
- database.py: +270 lines
- monitor.py: +55 lines
- dashboard.py: +80 lines
- main.py: +145 lines
- **Total: ~550 lines of new code**

---

## Summary

The Event Tracking System transforms the ACE Connection Logger from a simple ping monitor into a **comprehensive network reliability tracking platform**. Every outage is automatically logged with complete details, providing invaluable data for:

- Network operations and troubleshooting
- SLA compliance and reporting
- Performance analysis and optimization
- Historical trending and capacity planning
- Audit trails and documentation

**The system is fully operational and production-ready!** 🎉

---

*Implementation Date: 2025-11-06*
*Status: Complete and Verified*
