#!/usr/bin/env python3
"""Test script to validate outage event recording."""

import time
from datetime import datetime
from config import Config
from database import Database
from monitor import PingMonitor

def main():
    """Test outage event recording with various scenarios."""

    print("=" * 80)
    print("EVENT RECORDING TEST")
    print("=" * 80)
    print()

    # Initialize
    cfg = Config()
    db = Database(cfg.database_path)
    monitor = PingMonitor(cfg, db)

    print("📋 Current Event Recording Logic:")
    print("   - Event STARTS when: success_rate == 0.0% (all pings fail)")
    print("   - Event CONTINUES while: success_rate == 0.0%")
    print("   - Event ENDS when: success_rate > 0.0% (any ping succeeds)")
    print("   - Minimum duration: NONE (even 1 failed check creates event)")
    print()

    # Test 1: Check current active outages
    print("🔍 Test 1: Check for Active Outages")
    print("-" * 80)
    latest_results = db.get_latest_results()

    for result in latest_results:
        active = db.get_active_outage(result.host_address)
        if active:
            duration = (datetime.now() - active.start_time).total_seconds()
            print(f"   🔴 ACTIVE OUTAGE: {result.host_name} ({result.host_address})")
            print(f"      Started: {active.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"      Duration: {int(duration)}s ({active.checks_failed} failed checks)")
        else:
            if result.success_rate == 0.0:
                print(f"   ⚠️  DOWN but no event: {result.host_name} ({result.host_address})")
            else:
                print(f"   ✅ UP: {result.host_name} ({result.host_address}) - {result.success_rate:.1f}%")
    print()

    # Test 2: Perform a fresh check to see event creation/update
    print("🔄 Test 2: Perform Fresh Check (watch for event creation/updates)")
    print("-" * 80)
    results = monitor.check_all_hosts()
    print()

    # Test 3: Show all events in database
    print("📊 Test 3: All Events in Database")
    print("-" * 80)
    all_events = db.get_outage_events(limit=10)

    if not all_events:
        print("   No events recorded yet")
    else:
        for event in all_events:
            status = "🔴 ACTIVE" if event.end_time is None else "🟢 RESOLVED"
            duration = "ongoing" if event.duration_seconds is None else f"{event.duration_seconds}s"

            print(f"   {status} Event #{event.id}")
            print(f"      Host: {event.host_name} ({event.host_address})")
            print(f"      Start: {event.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
            if event.end_time:
                print(f"      End: {event.end_time.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"      Duration: {duration}")
            print(f"      Failed checks: {event.checks_failed}/{event.checks_during_outage}")
            print()

    # Test 4: Event statistics
    print("📈 Test 4: Event Statistics by Host")
    print("-" * 80)

    for result in latest_results:
        stats = db.get_outage_statistics(result.host_address)

        print(f"   {result.host_name} ({result.host_address}):")
        print(f"      Total outages: {stats['total_outages']}")
        print(f"      Active outages: {stats['active_outages']}")

        if stats['avg_duration_seconds'] > 0:
            avg_min = stats['avg_duration_seconds'] / 60
            print(f"      Average duration: {avg_min:.1f} minutes")

        if stats['total_downtime_seconds'] > 0:
            total_min = stats['total_downtime_seconds'] / 60
            print(f"      Total downtime: {total_min:.1f} minutes")
        print()

    # Test 5: Explanation of minimum downtime
    print("❓ Test 5: Minimum Downtime to Create Event")
    print("-" * 80)
    print("   Answer: ZERO - Any failed check creates an event immediately!")
    print()
    print("   Why this design?")
    print("   ✓ Captures all downtime periods, even brief ones")
    print("   ✓ Provides complete audit trail")
    print("   ✓ Useful for debugging intermittent issues")
    print("   ✓ Can filter by duration later if needed")
    print()
    print("   Example scenarios:")
    print("   - Single check fails (60s with default interval) → Event created")
    print("   - 2 checks fail (120s) → Event continues, checks_failed = 2")
    print("   - Next check succeeds → Event closed, duration = ~120s")
    print()
    print("   Note: Check interval is configured in config.yaml")
    print(f"   Current interval: {cfg.monitoring_interval} seconds")
    print()

    # Test 6: Simulate brief outage detection
    print("💡 Test 6: Simulating Outage Detection Logic")
    print("-" * 80)
    print("   Scenario: Host goes down for 2 checks, then recovers")
    print()
    print("   Check 1: success_rate = 0.0%")
    print("      → 🔴 Event created (Event ID: X)")
    print("      → checks_failed = 1, checks_during_outage = 1")
    print()
    print("   Check 2: success_rate = 0.0% (still down)")
    print("      → ⚠️  Event updated")
    print("      → checks_failed = 2, checks_during_outage = 2")
    print()
    print("   Check 3: success_rate = 100.0% (recovered)")
    print("      → 🟢 Event closed")
    print("      → duration_seconds = ~120 (2 × 60s interval)")
    print("      → recovery_success_rate = 100.0%")
    print()

    print("=" * 80)
    print("TEST COMPLETE")
    print("=" * 80)
    print()
    print("💡 Tip: Run 'uv run python main.py events' to see formatted event log")
    print("💡 Tip: Use 'uv run python main.py events --active' to see only ongoing outages")
    print()

if __name__ == "__main__":
    main()
