"""
Unit tests for get_all_monitored_hosts functionality.

Tests cover:
- Getting list of all hosts with data
- Host name and address retrieval
- Handling multiple hosts
- Handling removed hosts
"""

import pytest
from datetime import datetime, timedelta
from database import Database


@pytest.mark.unit
@pytest.mark.database
class TestMonitoredHosts:
    """Test suite for monitored hosts retrieval."""

    def test_get_all_monitored_hosts_empty_database(self, temp_db):
        """Test getting hosts from an empty database."""
        db = Database(temp_db)
        hosts = db.get_all_monitored_hosts()
        assert hosts == []

    def test_get_all_monitored_hosts_single_host(self, temp_db):
        """Test getting hosts with a single monitored host."""
        db = Database(temp_db)
        now = datetime.now()

        # Insert some results for one host
        with db._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO ping_results
                (host_name, host_address, timestamp, success_count, failure_count,
                 success_rate, min_latency, max_latency, avg_latency)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                ("Google DNS", "8.8.8.8", now, 10, 0, 100.0, 10.5, 15.2, 12.3),
            )

        hosts = db.get_all_monitored_hosts()
        assert len(hosts) == 1
        assert hosts[0]["name"] == "Google DNS"
        assert hosts[0]["address"] == "8.8.8.8"

    def test_get_all_monitored_hosts_multiple_hosts(self, temp_db):
        """Test getting hosts with multiple monitored hosts."""
        db = Database(temp_db)
        now = datetime.now()

        # Insert results for multiple hosts
        test_hosts = [
            ("Google DNS", "8.8.8.8"),
            ("Cloudflare DNS", "1.1.1.1"),
            ("Local Gateway", "192.168.1.1"),
        ]

        with db._get_connection() as conn:
            cursor = conn.cursor()
            for name, address in test_hosts:
                cursor.execute(
                    """
                    INSERT INTO ping_results
                    (host_name, host_address, timestamp, success_count, failure_count,
                     success_rate, min_latency, max_latency, avg_latency)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (name, address, now, 10, 0, 100.0, 10.5, 15.2, 12.3),
                )

        hosts = db.get_all_monitored_hosts()
        assert len(hosts) == 3

        # Check all hosts are present
        addresses = {h["address"] for h in hosts}
        assert addresses == {"8.8.8.8", "1.1.1.1", "192.168.1.1"}

    def test_get_all_monitored_hosts_uses_latest_name(self, temp_db):
        """Test that the method returns the most recent host_name for each address."""
        db = Database(temp_db)
        now = datetime.now()

        # Insert results with changing host names
        with db._get_connection() as conn:
            cursor = conn.cursor()

            # Old name
            cursor.execute(
                """
                INSERT INTO ping_results
                (host_name, host_address, timestamp, success_count, failure_count,
                 success_rate, min_latency, max_latency, avg_latency)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                ("Old Name", "8.8.8.8", now - timedelta(days=1), 10, 0, 100.0, 10.5, 15.2, 12.3),
            )

            # New name (more recent)
            cursor.execute(
                """
                INSERT INTO ping_results
                (host_name, host_address, timestamp, success_count, failure_count,
                 success_rate, min_latency, max_latency, avg_latency)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                ("Google DNS", "8.8.8.8", now, 10, 0, 100.0, 10.5, 15.2, 12.3),
            )

        hosts = db.get_all_monitored_hosts()
        assert len(hosts) == 1
        assert hosts[0]["name"] == "Google DNS"  # Should use the latest name
        assert hosts[0]["address"] == "8.8.8.8"

    def test_get_all_monitored_hosts_sorted_by_name(self, temp_db):
        """Test that hosts are sorted alphabetically by name."""
        db = Database(temp_db)
        now = datetime.now()

        # Insert hosts in non-alphabetical order
        test_hosts = [
            ("Zebra Host", "10.0.0.3"),
            ("Alpha Host", "10.0.0.1"),
            ("Beta Host", "10.0.0.2"),
        ]

        with db._get_connection() as conn:
            cursor = conn.cursor()
            for name, address in test_hosts:
                cursor.execute(
                    """
                    INSERT INTO ping_results
                    (host_name, host_address, timestamp, success_count, failure_count,
                     success_rate, min_latency, max_latency, avg_latency)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (name, address, now, 10, 0, 100.0, 10.5, 15.2, 12.3),
                )

        hosts = db.get_all_monitored_hosts()
        names = [h["name"] for h in hosts]

        # Should be sorted alphabetically
        assert names == ["Alpha Host", "Beta Host", "Zebra Host"]

    def test_get_all_monitored_hosts_includes_historical(self, temp_db):
        """Test that method includes hosts that might have been removed from config."""
        db = Database(temp_db)
        now = datetime.now()

        # Insert results for a host that might no longer be in config
        with db._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO ping_results
                (host_name, host_address, timestamp, success_count, failure_count,
                 success_rate, min_latency, max_latency, avg_latency)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                ("Old Server", "192.168.1.100", now - timedelta(days=30), 10, 0, 100.0, 10.5, 15.2, 12.3),
            )

        hosts = db.get_all_monitored_hosts()
        assert len(hosts) == 1
        assert hosts[0]["name"] == "Old Server"
        assert hosts[0]["address"] == "192.168.1.100"

    def test_get_all_monitored_hosts_dict_format(self, temp_db):
        """Test that hosts are returned as dicts with correct keys."""
        db = Database(temp_db)
        now = datetime.now()

        with db._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO ping_results
                (host_name, host_address, timestamp, success_count, failure_count,
                 success_rate, min_latency, max_latency, avg_latency)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                ("Test Host", "10.0.0.1", now, 10, 0, 100.0, 10.5, 15.2, 12.3),
            )

        hosts = db.get_all_monitored_hosts()
        assert len(hosts) == 1

        host = hosts[0]
        assert isinstance(host, dict)
        assert "name" in host
        assert "address" in host
        assert len(host) == 2  # Should only have these two keys
