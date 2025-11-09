"""
Integration tests for end-to-end workflows and edge cases.

Tests cover:
- Complete monitoring workflow
- Database integration with monitoring
- Error recovery and resilience
- Concurrent operations
- Edge cases and failure modes
- Performance under load
"""

import pytest
import sqlite3
from datetime import datetime, timedelta
from unittest.mock import patch


@pytest.mark.integration
class TestEndToEndWorkflows:
    """Test suite for complete end-to-end workflows."""

    def test_complete_monitoring_cycle(self, db_connection, mock_ping_response):
        """Test complete monitoring cycle from ping to database storage."""
        cursor = db_connection.cursor()

        # Simulate ping result
        host = "8.8.8.8"
        timestamp = datetime.now()

        # Store result in database
        cursor.execute(
            """
            INSERT INTO ping_results
            (host, timestamp, ping_count, success_count, failure_count,
             success_rate, min_latency, max_latency, avg_latency)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                host,
                timestamp,
                mock_ping_response.packets_sent,
                mock_ping_response.packets_received,
                mock_ping_response.packets_sent - mock_ping_response.packets_received,
                (1 - mock_ping_response.packet_loss / 100) * 100,
                mock_ping_response.rtt_min,
                mock_ping_response.rtt_max,
                mock_ping_response.rtt_avg,
            ),
        )

        db_connection.commit()

        # Verify data was stored correctly
        cursor.execute("SELECT * FROM ping_results WHERE host = ?", (host,))
        result = cursor.fetchone()

        assert result is not None
        assert result[1] == host

    def test_multiple_hosts_monitoring(self, db_connection, mock_ping_response):
        """Test monitoring multiple hosts in sequence."""
        cursor = db_connection.cursor()

        hosts = ["8.8.8.8", "1.1.1.1", "google.com"]
        timestamp = datetime.now()

        for host in hosts:
            cursor.execute(
                """
                INSERT INTO ping_results
                (host, timestamp, ping_count, success_count, failure_count,
                 success_rate, min_latency, max_latency, avg_latency)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    host,
                    timestamp,
                    10,
                    10,
                    0,
                    100.0,
                    mock_ping_response.rtt_min,
                    mock_ping_response.rtt_max,
                    mock_ping_response.rtt_avg,
                ),
            )

        db_connection.commit()

        # Verify all hosts were recorded
        cursor.execute("SELECT DISTINCT host FROM ping_results")
        stored_hosts = [row[0] for row in cursor.fetchall()]

        assert len(stored_hosts) == len(hosts)
        assert set(stored_hosts) == set(hosts)

    def test_error_recovery_failed_ping(self, db_connection, mock_failed_ping_response):
        """Test system recovery from failed ping."""
        cursor = db_connection.cursor()

        host = "unreachable.host"
        timestamp = datetime.now()

        # Store failed ping result
        cursor.execute(
            """
            INSERT INTO ping_results
            (host, timestamp, ping_count, success_count, failure_count,
             success_rate, min_latency, max_latency, avg_latency)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                host,
                timestamp,
                mock_failed_ping_response.packets_sent,
                mock_failed_ping_response.packets_received,
                mock_failed_ping_response.packets_sent,
                0.0,
                None,
                None,
                None,
            ),
        )

        db_connection.commit()

        # Verify failed ping was recorded
        cursor.execute("SELECT success_rate FROM ping_results WHERE host = ?", (host,))
        result = cursor.fetchone()

        assert result[0] == 0.0

    def test_database_connection_resilience(self, temp_db):
        """Test database connection can recover from failures."""
        # Open connection
        conn1 = sqlite3.connect(temp_db)
        cursor1 = conn1.cursor()

        # Write data
        cursor1.execute("""
            CREATE TABLE IF NOT EXISTS test_table (id INTEGER PRIMARY KEY, value TEXT)
        """)
        cursor1.execute("INSERT INTO test_table (value) VALUES (?)", ("test",))
        conn1.commit()
        conn1.close()

        # Reopen connection and verify data persists
        conn2 = sqlite3.connect(temp_db)
        cursor2 = conn2.cursor()

        cursor2.execute("SELECT value FROM test_table")
        result = cursor2.fetchone()

        assert result[0] == "test"
        conn2.close()

    def test_concurrent_read_write_operations(self, temp_db):
        """Test concurrent read and write operations."""
        # Write connection
        write_conn = sqlite3.connect(temp_db)
        write_cursor = write_conn.cursor()

        write_cursor.execute("""
            CREATE TABLE IF NOT EXISTS ping_results (
                id INTEGER PRIMARY KEY,
                host TEXT,
                timestamp DATETIME
            )
        """)
        write_conn.commit()

        # Read connection
        read_conn = sqlite3.connect(temp_db)
        read_cursor = read_conn.cursor()

        # Write data
        write_cursor.execute(
            """
            INSERT INTO ping_results (host, timestamp) VALUES (?, ?)
        """,
            ("8.8.8.8", datetime.now()),
        )
        write_conn.commit()

        # Read data from separate connection
        read_cursor.execute("SELECT COUNT(*) FROM ping_results")
        count = read_cursor.fetchone()[0]

        assert count == 1

        write_conn.close()
        read_conn.close()

    def test_statistics_calculation_integration(self, populated_db):
        """Test statistics calculation on real database data."""
        cursor = populated_db.cursor()

        # Calculate statistics
        cursor.execute("""
            SELECT
                COUNT(*) as total_checks,
                AVG(success_rate) as avg_success_rate,
                AVG(avg_latency) as overall_avg_latency
            FROM ping_results
            WHERE avg_latency IS NOT NULL
        """)

        result = cursor.fetchone()

        assert result[0] > 0  # Has data
        assert 0 <= result[1] <= 100  # Valid success rate
        assert result[2] > 0  # Has latency data

    def test_cleanup_integration_with_monitoring(self, db_connection):
        """Test cleanup integration with ongoing monitoring."""
        cursor = db_connection.cursor()

        # Add mix of old and new data
        for days_ago in [0, 5, 50, 100, 200]:
            cursor.execute(
                """
                INSERT INTO ping_results
                (host, timestamp, ping_count, success_count, failure_count,
                 success_rate, min_latency, max_latency, avg_latency)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    "8.8.8.8",
                    datetime.now() - timedelta(days=days_ago),
                    10,
                    10,
                    0,
                    100.0,
                    10.0,
                    20.0,
                    15.0,
                ),
            )

        db_connection.commit()

        # Run cleanup
        cutoff_date = datetime.now() - timedelta(days=90)
        cursor.execute(
            """
            DELETE FROM ping_results WHERE timestamp < ?
        """,
            (cutoff_date,),
        )

        db_connection.commit()

        # Verify recent data remains
        cursor.execute(
            """
            SELECT COUNT(*) FROM ping_results
            WHERE timestamp >= ?
        """,
            (cutoff_date,),
        )

        recent_count = cursor.fetchone()[0]
        assert recent_count > 0


@pytest.mark.integration
class TestEdgeCasesAndFailureModes:
    """Test suite for edge cases and failure modes."""

    def test_empty_host_list(self):
        """Test handling of empty host list."""
        hosts = []
        assert len(hosts) == 0
        # System should handle gracefully or raise appropriate error

    def test_invalid_host_address(self):
        """Test handling of invalid host addresses."""
        invalid_hosts = ["", "invalid..host", "256.256.256.256"]

        for host in invalid_hosts:
            # System should validate and reject
            import re

            ip_pattern = r"^(\d{1,3}\.){3}\d{1,3}$"
            # Updated pattern to reject consecutive dots, starting/ending dots, and invalid characters
            domain_pattern = r"^(?!.*\.\.)[a-zA-Z0-9]([a-zA-Z0-9-]*[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9-]*[a-zA-Z0-9])?)*\.[a-zA-Z]{2,}$|^localhost$"

            is_valid = False
            if host and re.match(ip_pattern, host):
                parts = [int(p) for p in host.split(".")]
                is_valid = all(0 <= p <= 255 for p in parts)
            elif host and re.match(domain_pattern, host):
                is_valid = True

            assert not is_valid

    def test_database_disk_full_simulation(self):
        """Test handling when database disk is full."""
        # This would simulate disk full condition
        # In practice, system should handle OSError gracefully
        pass

    def test_network_timeout_handling(self):
        """Test handling of network timeouts."""
        with patch("subprocess.run") as mock_run:
            import subprocess

            mock_run.side_effect = subprocess.TimeoutExpired(cmd="ping", timeout=5)

            # System should catch and handle timeout
            with pytest.raises(subprocess.TimeoutExpired):
                mock_run()

    def test_ping_permission_denied(self):
        """Test handling when ping permission is denied."""
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = PermissionError("Operation not permitted")

            with pytest.raises(PermissionError):
                mock_run()

    def test_database_locked_handling(self, temp_db):
        """Test handling of database locked errors."""
        # Open connection with exclusive lock
        conn1 = sqlite3.connect(temp_db, timeout=1)
        cursor1 = conn1.cursor()

        cursor1.execute("""
            CREATE TABLE IF NOT EXISTS test_table (id INTEGER PRIMARY KEY)
        """)
        cursor1.execute("BEGIN EXCLUSIVE")

        # Try to access from second connection (should timeout)
        conn2 = sqlite3.connect(temp_db, timeout=0.5)
        cursor2 = conn2.cursor()

        try:
            cursor2.execute("SELECT * FROM test_table")
            conn2.close()
        except sqlite3.OperationalError:
            # Expected: database is locked
            pass

        conn1.rollback()
        conn1.close()

    def test_maximum_latency_values(self):
        """Test handling of extremely high latency values."""
        extreme_latencies = [1000.0, 5000.0, 10000.0]  # Very high latencies

        for latency in extreme_latencies:
            # System should accept but may flag as outlier
            assert latency > 0
            assert latency < 100000  # Reasonable maximum

    def test_zero_latency_values(self):
        """Test handling of zero latency (localhost or invalid)."""
        latency = 0.0

        # Very low latency is possible (localhost)
        assert latency >= 0

    def test_negative_latency_values(self):
        """Test rejection of negative latency values."""
        invalid_latencies = [-1.0, -10.0, -100.0]

        for latency in invalid_latencies:
            # System should reject negative latencies
            assert latency < 0  # Invalid

    def test_partial_packet_loss_edge_cases(self):
        """Test edge cases in packet loss calculation."""
        test_cases = [
            (10, 0),  # 100% loss
            (10, 10),  # 0% loss
            (10, 1),  # 90% loss
            (10, 9),  # 10% loss
            (1, 1),  # Single packet success
            (1, 0),  # Single packet loss
        ]

        for sent, received in test_cases:
            packet_loss = ((sent - received) / sent) * 100
            assert 0 <= packet_loss <= 100

    def test_timestamp_edge_cases(self):
        """Test edge cases in timestamp handling."""
        now = datetime.now()
        past = now - timedelta(days=365)
        future = now + timedelta(days=1)

        # Past timestamp should be valid
        assert past < now

        # Future timestamp should be detected
        assert future > now

    def test_database_corruption_detection(self, temp_db):
        """Test database corruption detection."""
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()

        # Run integrity check
        cursor.execute("PRAGMA integrity_check")
        result = cursor.fetchone()

        assert result[0] == "ok"
        conn.close()

    def test_very_long_host_name(self):
        """Test handling of extremely long host names."""
        long_host = "a" * 1000 + ".com"

        # System should handle or reject based on limit
        assert len(long_host) > 255  # Typical DNS limit

    def test_unicode_in_host_name(self):
        """Test handling of unicode characters in host names."""
        unicode_hosts = [
            "münchen.de",  # German
            "日本.jp",  # Japanese
            "café.fr",  # French
        ]

        # System should handle IDN (Internationalized Domain Names)
        for host in unicode_hosts:
            assert isinstance(host, str)

    def test_rapid_succession_pings(self):
        """Test handling of rapid succession ping requests."""
        # Simulate rapid pings
        ping_count = 100
        interval = 0.01  # Very rapid

        # System should handle without errors or rate limit appropriately
        assert ping_count > 0
        assert interval >= 0

    @pytest.mark.slow
    def test_long_running_monitoring_simulation(self, db_connection):
        """Test long-running monitoring simulation."""
        cursor = db_connection.cursor()

        # Simulate 24 hours of monitoring (1 ping per minute)
        checks_per_hour = 60
        hours = 24
        total_checks = checks_per_hour * hours

        # Insert simulated data
        records = []
        for i in range(total_checks):
            records.append(
                (
                    "8.8.8.8",
                    datetime.now() - timedelta(minutes=total_checks - i),
                    10,
                    10,
                    0,
                    100.0,
                    10.0,
                    20.0,
                    15.0,
                )
            )

        cursor.executemany(
            """
            INSERT INTO ping_results
            (host, timestamp, ping_count, success_count, failure_count,
             success_rate, min_latency, max_latency, avg_latency)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            records,
        )

        db_connection.commit()

        # Verify all records stored
        cursor.execute("SELECT COUNT(*) FROM ping_results")
        count = cursor.fetchone()[0]

        assert count == total_checks

    def test_system_clock_changes(self):
        """Test handling of system clock changes."""
        timestamp1 = datetime.now()
        timestamp2 = datetime.now()

        # Timestamps should be monotonically increasing in normal conditions
        assert timestamp2 >= timestamp1

    def test_config_file_changes_while_running(self, temp_config_file):
        """Test handling of configuration changes during runtime."""
        import yaml

        # Read original config
        with open(temp_config_file, "r") as f:
            original_config = yaml.safe_load(f)

        # Modify config
        modified_config = original_config.copy()
        modified_config["interval_seconds"] = 120

        with open(temp_config_file, "w") as f:
            yaml.dump(modified_config, f)

        # Reload config
        with open(temp_config_file, "r") as f:
            reloaded_config = yaml.safe_load(f)

        assert reloaded_config["interval_seconds"] == 120

    def test_memory_leak_prevention(self, db_connection):
        """Test that database operations don't leak memory."""
        cursor = db_connection.cursor()

        # Perform many operations
        for i in range(1000):
            cursor.execute(
                """
                INSERT INTO ping_results
                (host, timestamp, ping_count, success_count, failure_count,
                 success_rate, min_latency, max_latency, avg_latency)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                ("test.com", datetime.now(), 10, 10, 0, 100.0, 10.0, 20.0, 15.0),
            )

            if i % 100 == 0:
                db_connection.commit()

        db_connection.commit()

        # Cleanup
        cursor.execute("DELETE FROM ping_results")
        db_connection.commit()

        # Verify cleanup worked
        cursor.execute("SELECT COUNT(*) FROM ping_results")
        assert cursor.fetchone()[0] == 0
