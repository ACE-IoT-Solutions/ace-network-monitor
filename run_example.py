#!/usr/bin/env python3
"""Example script to demonstrate the connection logger functionality.

This script generates sample monitoring data and demonstrates usage.
"""

import time
from datetime import datetime

from config import Config
from database import Database
from monitor import PingMonitor


def generate_sample_data(num_checks: int = 10):
    """Generate sample monitoring data for demonstration.

    Args:
        num_checks: Number of checks to perform.
    """
    print(f"Generating {num_checks} sample checks...")
    print("This will take approximately", num_checks * 5, "seconds")
    print()

    config = Config()
    db = Database(config.database_path)
    monitor = PingMonitor(config, db)

    for i in range(num_checks):
        print(f"Check {i + 1}/{num_checks}:")
        monitor.check_all_hosts()
        print()

        if i < num_checks - 1:
            print(f"Waiting {config.monitoring_interval} seconds...")
            time.sleep(config.monitoring_interval)

    print("Sample data generation complete!")
    print()
    print("You can now:")
    print("  1. View status: python main.py status")
    print("  2. Launch dashboard: python main.py dashboard")
    print()


def show_quick_demo():
    """Show a quick demo with 3 checks."""
    generate_sample_data(3)


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--full":
        # Full demo with 10 checks
        generate_sample_data(10)
    else:
        # Quick demo with 3 checks
        show_quick_demo()
