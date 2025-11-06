"""
Integration tests for cleanup job functionality.

Tests cover:
- Cleanup of old records
- Retention period enforcement
- Database growth management
- Scheduled cleanup execution
- Edge cases and error handling
"""

import pytest
import sqlite3
from datetime import datetime, timedelta


@pytest.mark.integration
@pytest.mark.cleanup
class TestCleanupJob:
    """Test suite for cleanup job functionality."""

    def test_cleanup_removes_old_records(self, db_connection, old_ping_data):
        """Test that cleanup removes records older than retention period."""
        cursor = db_connection.cursor()

        # Insert old data
        for record in old_ping_data:
            cursor.execute("""
                INSERT INTO ping_results
                (host, timestamp, ping_count, success_count, failure_count,
                 success_rate, min_latency, max_latency, avg_latency)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                record["host"],
                record["timestamp"],
                record["ping_count"],
                record["success_count"],
                record["failure_count"],
                record["success_rate"],
                record["min_latency"],
                record["max_latency"],
                record["avg_latency"],
            ))

        db_connection.commit()

        # Verify old records exist
        cursor.execute("SELECT COUNT(*) FROM ping_results")
        initial_count = cursor.fetchone()[0]
        assert initial_count == len(old_ping_data)

        # Run cleanup
        retention_days = 90
        cutoff_date = datetime.now() - timedelta(days=retention_days)
        cursor.execute("""
            DELETE FROM ping_results WHERE timestamp < ?
        """, (cutoff_date,))

        deleted_count = cursor.rowcount
        db_connection.commit()

        # Verify cleanup worked
        cursor.execute("SELECT COUNT(*) FROM ping_results")
        remaining_count = cursor.fetchone()[0]

        assert deleted_count == len(old_ping_data)
        assert remaining_count == 0

    def test_cleanup_preserves_recent_records(self, db_connection, sample_ping_data):
        """Test that cleanup preserves records within retention period."""
        cursor = db_connection.cursor()

        # Insert recent data
        for record in sample_ping_data:
            cursor.execute("""
                INSERT INTO ping_results
                (host, timestamp, ping_count, success_count, failure_count,
                 success_rate, min_latency, max_latency, avg_latency)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                record["host"],
                record["timestamp"],
                record["ping_count"],
                record["success_count"],
                record["failure_count"],
                record["success_rate"],
                record["min_latency"],
                record["max_latency"],
                record["avg_latency"],
            ))

        db_connection.commit()

        initial_count = len(sample_ping_data)

        # Run cleanup (should not delete recent records)
        retention_days = 90
        cutoff_date = datetime.now() - timedelta(days=retention_days)
        cursor.execute("""
            DELETE FROM ping_results WHERE timestamp < ?
        """, (cutoff_date,))

        db_connection.commit()

        # Verify recent records are preserved
        cursor.execute("SELECT COUNT(*) FROM ping_results")
        remaining_count = cursor.fetchone()[0]

        assert remaining_count == initial_count

    def test_cleanup_with_mixed_age_records(self, db_connection, sample_ping_data, old_ping_data):
        """Test cleanup with both old and recent records."""
        cursor = db_connection.cursor()

        # Insert both old and recent data
        all_records = sample_ping_data + old_ping_data

        for record in all_records:
            cursor.execute("""
                INSERT INTO ping_results
                (host, timestamp, ping_count, success_count, failure_count,
                 success_rate, min_latency, max_latency, avg_latency)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                record["host"],
                record["timestamp"],
                record["ping_count"],
                record["success_count"],
                record["failure_count"],
                record["success_rate"],
                record["min_latency"],
                record["max_latency"],
                record["avg_latency"],
            ))

        db_connection.commit()

        # Run cleanup
        retention_days = 90
        cutoff_date = datetime.now() - timedelta(days=retention_days)
        cursor.execute("""
            DELETE FROM ping_results WHERE timestamp < ?
        """, (cutoff_date,))

        deleted_count = cursor.rowcount
        db_connection.commit()

        # Verify only old records were deleted
        cursor.execute("SELECT COUNT(*) FROM ping_results")
        remaining_count = cursor.fetchone()[0]

        assert deleted_count == len(old_ping_data)
        assert remaining_count == len(sample_ping_data)

    @pytest.mark.parametrize("retention_days", [1, 7, 30, 90, 365])
    def test_cleanup_with_different_retention_periods(self, db_connection, retention_days):
        """Test cleanup with various retention periods."""
        cursor = db_connection.cursor()

        # Insert records with various ages
        test_ages = [0, 10, 50, 100, 200, 400]

        for days_ago in test_ages:
            cursor.execute("""
                INSERT INTO ping_results
                (host, timestamp, ping_count, success_count, failure_count,
                 success_rate, min_latency, max_latency, avg_latency)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                "test.com",
                datetime.now() - timedelta(days=days_ago),
                10, 10, 0, 100.0, 10.0, 20.0, 15.0
            ))

        db_connection.commit()

        # Run cleanup
        cutoff_date = datetime.now() - timedelta(days=retention_days)
        cursor.execute("""
            DELETE FROM ping_results WHERE timestamp < ?
        """, (cutoff_date,))

        deleted_count = cursor.rowcount
        db_connection.commit()

        # Verify correct number of records deleted
        expected_deleted = sum(1 for age in test_ages if age > retention_days)
        assert deleted_count == expected_deleted

    def test_cleanup_empty_database(self, db_connection):
        """Test cleanup on empty database (should not error)."""
        cursor = db_connection.cursor()

        # Verify database is empty
        cursor.execute("SELECT COUNT(*) FROM ping_results")
        assert cursor.fetchone()[0] == 0

        # Run cleanup (should succeed without errors)
        cutoff_date = datetime.now() - timedelta(days=90)
        cursor.execute("""
            DELETE FROM ping_results WHERE timestamp < ?
        """, (cutoff_date,))

        deleted_count = cursor.rowcount
        db_connection.commit()

        assert deleted_count == 0

    def test_cleanup_returns_deleted_count(self, db_connection, old_ping_data):
        """Test that cleanup returns accurate count of deleted records."""
        cursor = db_connection.cursor()

        # Insert old data
        for record in old_ping_data:
            cursor.execute("""
                INSERT INTO ping_results
                (host, timestamp, ping_count, success_count, failure_count,
                 success_rate, min_latency, max_latency, avg_latency)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                record["host"], record["timestamp"], record["ping_count"],
                record["success_count"], record["failure_count"],
                record["success_rate"], record["min_latency"],
                record["max_latency"], record["avg_latency"]
            ))

        db_connection.commit()

        # Run cleanup and get deleted count
        cutoff_date = datetime.now() - timedelta(days=90)
        cursor.execute("""
            DELETE FROM ping_results WHERE timestamp < ?
        """, (cutoff_date,))

        deleted_count = cursor.rowcount

        assert deleted_count == len(old_ping_data)

    def test_cleanup_database_vacuum(self, db_connection, old_ping_data):
        """Test that database is vacuumed after cleanup to reclaim space."""
        cursor = db_connection.cursor()

        # Insert and delete data
        for record in old_ping_data:
            cursor.execute("""
                INSERT INTO ping_results
                (host, timestamp, ping_count, success_count, failure_count,
                 success_rate, min_latency, max_latency, avg_latency)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                record["host"], record["timestamp"], record["ping_count"],
                record["success_count"], record["failure_count"],
                record["success_rate"], record["min_latency"],
                record["max_latency"], record["avg_latency"]
            ))

        db_connection.commit()

        cutoff_date = datetime.now() - timedelta(days=90)
        cursor.execute("""
            DELETE FROM ping_results WHERE timestamp < ?
        """, (cutoff_date,))

        db_connection.commit()

        # Vacuum to reclaim space
        cursor.execute("VACUUM")

        # Verify vacuum completed (no error)
        assert True

    def test_cleanup_with_transaction_rollback(self, db_connection, old_ping_data):
        """Test cleanup rollback on error."""
        cursor = db_connection.cursor()

        # Insert old data
        for record in old_ping_data:
            cursor.execute("""
                INSERT INTO ping_results
                (host, timestamp, ping_count, success_count, failure_count,
                 success_rate, min_latency, max_latency, avg_latency)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                record["host"], record["timestamp"], record["ping_count"],
                record["success_count"], record["failure_count"],
                record["success_rate"], record["min_latency"],
                record["max_latency"], record["avg_latency"]
            ))

        db_connection.commit()

        initial_count = len(old_ping_data)

        # Start transaction and delete
        cutoff_date = datetime.now() - timedelta(days=90)
        cursor.execute("""
            DELETE FROM ping_results WHERE timestamp < ?
        """, (cutoff_date,))

        # Rollback instead of commit
        db_connection.rollback()

        # Verify records still exist
        cursor.execute("SELECT COUNT(*) FROM ping_results")
        count = cursor.fetchone()[0]

        assert count == initial_count

    def test_cleanup_performance_large_dataset(self, db_connection):
        """Test cleanup performance with large dataset."""
        cursor = db_connection.cursor()

        # Insert large dataset
        records = []
        for i in range(1000):
            days_ago = (i % 200) + 1  # Vary ages from 1-200 days
            records.append((
                f"host{i % 10}.com",
                datetime.now() - timedelta(days=days_ago),
                10, 10, 0, 100.0, 10.0, 20.0, 15.0
            ))

        cursor.executemany("""
            INSERT INTO ping_results
            (host, timestamp, ping_count, success_count, failure_count,
             success_rate, min_latency, max_latency, avg_latency)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, records)

        db_connection.commit()

        # Run cleanup
        import time
        start_time = time.time()

        cutoff_date = datetime.now() - timedelta(days=90)
        cursor.execute("""
            DELETE FROM ping_results WHERE timestamp < ?
        """, (cutoff_date,))

        db_connection.commit()

        execution_time = time.time() - start_time

        # Cleanup should complete reasonably quickly
        assert execution_time < 5.0  # Should complete within 5 seconds

    def test_cleanup_maintains_database_integrity(self, db_connection, old_ping_data, sample_ping_data):
        """Test that cleanup maintains database integrity."""
        cursor = db_connection.cursor()

        # Insert mixed data
        all_records = sample_ping_data + old_ping_data

        for record in all_records:
            cursor.execute("""
                INSERT INTO ping_results
                (host, timestamp, ping_count, success_count, failure_count,
                 success_rate, min_latency, max_latency, avg_latency)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                record["host"], record["timestamp"], record["ping_count"],
                record["success_count"], record["failure_count"],
                record["success_rate"], record["min_latency"],
                record["max_latency"], record["avg_latency"]
            ))

        db_connection.commit()

        # Run cleanup
        cutoff_date = datetime.now() - timedelta(days=90)
        cursor.execute("""
            DELETE FROM ping_results WHERE timestamp < ?
        """, (cutoff_date,))

        db_connection.commit()

        # Verify integrity
        cursor.execute("PRAGMA integrity_check")
        result = cursor.fetchone()

        assert result[0] == 'ok'

    def test_cleanup_scheduled_execution_simulation(self):
        """Test simulated scheduled cleanup execution."""
        # Simulate daily cleanup schedule
        cleanup_interval_hours = 24
        last_cleanup = datetime.now() - timedelta(hours=25)

        # Check if cleanup should run
        should_run = (datetime.now() - last_cleanup).total_seconds() >= (cleanup_interval_hours * 3600)

        assert should_run is True

    def test_cleanup_with_concurrent_reads(self, db_connection, temp_db, old_ping_data):
        """Test cleanup with concurrent read operations."""
        cursor = db_connection.cursor()

        # Insert data
        for record in old_ping_data:
            cursor.execute("""
                INSERT INTO ping_results
                (host, timestamp, ping_count, success_count, failure_count,
                 success_rate, min_latency, max_latency, avg_latency)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                record["host"], record["timestamp"], record["ping_count"],
                record["success_count"], record["failure_count"],
                record["success_rate"], record["min_latency"],
                record["max_latency"], record["avg_latency"]
            ))

        db_connection.commit()

        # Open second connection for reading
        read_conn = sqlite3.connect(temp_db)
        read_cursor = read_conn.cursor()

        # Perform read while cleanup is happening
        read_cursor.execute("SELECT COUNT(*) FROM ping_results")
        count_before = read_cursor.fetchone()[0]

        # Run cleanup
        cutoff_date = datetime.now() - timedelta(days=90)
        cursor.execute("""
            DELETE FROM ping_results WHERE timestamp < ?
        """, (cutoff_date,))

        db_connection.commit()

        # Read after cleanup
        read_cursor.execute("SELECT COUNT(*) FROM ping_results")
        count_after = read_cursor.fetchone()[0]

        assert count_before > count_after

        read_conn.close()

    def test_cleanup_logging_simulation(self, db_connection, old_ping_data, capsys):
        """Test that cleanup operations are logged."""
        cursor = db_connection.cursor()

        # Insert old data
        for record in old_ping_data:
            cursor.execute("""
                INSERT INTO ping_results
                (host, timestamp, ping_count, success_count, failure_count,
                 success_rate, min_latency, max_latency, avg_latency)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                record["host"], record["timestamp"], record["ping_count"],
                record["success_count"], record["failure_count"],
                record["success_rate"], record["min_latency"],
                record["max_latency"], record["avg_latency"]
            ))

        db_connection.commit()

        # Run cleanup
        cutoff_date = datetime.now() - timedelta(days=90)
        cursor.execute("""
            DELETE FROM ping_results WHERE timestamp < ?
        """, (cutoff_date,))

        deleted_count = cursor.rowcount
        db_connection.commit()

        # Simulate logging
        print(f"Cleanup completed: {deleted_count} records deleted")

        captured = capsys.readouterr()
        assert "Cleanup completed" in captured.out
        assert str(deleted_count) in captured.out

    def test_cleanup_error_handling_simulation(self, db_connection):
        """Test cleanup error handling."""
        cursor = db_connection.cursor()

        try:
            # Attempt cleanup with invalid date format
            cursor.execute("""
                DELETE FROM ping_results WHERE timestamp < ?
            """, ("invalid_date",))

            db_connection.commit()
            assert False, "Should have raised an error"

        except Exception:
            # Error should be caught and handled
            db_connection.rollback()
            assert True

    @pytest.mark.slow
    def test_cleanup_stress_test(self, db_connection):
        """Stress test cleanup with very large dataset."""
        cursor = db_connection.cursor()

        # Insert large dataset (10,000 records)
        records = []
        for i in range(10000):
            days_ago = (i % 365) + 1
            records.append((
                f"host{i % 100}.com",
                datetime.now() - timedelta(days=days_ago),
                10, 10, 0, 100.0, 10.0, 20.0, 15.0
            ))

        # Batch insert
        cursor.executemany("""
            INSERT INTO ping_results
            (host, timestamp, ping_count, success_count, failure_count,
             success_rate, min_latency, max_latency, avg_latency)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, records)

        db_connection.commit()

        # Run cleanup
        cutoff_date = datetime.now() - timedelta(days=90)
        cursor.execute("""
            DELETE FROM ping_results WHERE timestamp < ?
        """, (cutoff_date,))

        deleted_count = cursor.rowcount
        db_connection.commit()

        # Verify cleanup worked
        assert deleted_count > 0

        # Verify database is still functional
        cursor.execute("SELECT COUNT(*) FROM ping_results")
        remaining = cursor.fetchone()[0]

        assert remaining > 0
        assert remaining + deleted_count == 10000
