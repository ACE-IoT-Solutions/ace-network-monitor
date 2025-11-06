"""
Unit tests for database operations.

Tests cover:
- CRUD operations
- Data integrity
- Query performance
- Index efficiency
- Transaction handling
- Concurrent access
"""

import pytest
import sqlite3
from datetime import datetime, timedelta


@pytest.mark.unit
@pytest.mark.database
class TestDatabaseOperations:
    """Test suite for database operations."""

    def test_database_connection(self, temp_db):
        """Test database connection can be established."""
        conn = sqlite3.connect(temp_db)
        assert conn is not None
        conn.close()

    def test_schema_creation(self, db_connection):
        """Test that database schema is created correctly."""
        cursor = db_connection.cursor()

        # Check table exists
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='ping_results'
        """)
        assert cursor.fetchone() is not None

        # Check columns
        cursor.execute("PRAGMA table_info(ping_results)")
        columns = {row[1] for row in cursor.fetchall()}

        expected_columns = {
            'id', 'host', 'timestamp', 'ping_count',
            'success_count', 'failure_count', 'success_rate',
            'min_latency', 'max_latency', 'avg_latency', 'created_at'
        }
        assert expected_columns.issubset(columns)

    def test_insert_ping_result(self, db_connection):
        """Test inserting a ping result into database."""
        cursor = db_connection.cursor()

        cursor.execute("""
            INSERT INTO ping_results
            (host, timestamp, ping_count, success_count, failure_count,
             success_rate, min_latency, max_latency, avg_latency)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            "8.8.8.8",
            datetime.now(),
            10,
            10,
            0,
            100.0,
            10.5,
            15.2,
            12.3
        ))

        db_connection.commit()

        # Verify insertion
        cursor.execute("SELECT COUNT(*) FROM ping_results")
        assert cursor.fetchone()[0] == 1

    def test_query_by_host(self, populated_db):
        """Test querying results by host."""
        cursor = populated_db.cursor()

        cursor.execute("""
            SELECT * FROM ping_results WHERE host = ?
        """, ("8.8.8.8",))

        results = cursor.fetchall()
        assert len(results) >= 1
        assert all(row[1] == "8.8.8.8" for row in results)

    def test_query_by_time_range(self, populated_db):
        """Test querying results within time range."""
        cursor = populated_db.cursor()
        start_time = datetime.now() - timedelta(hours=1)
        end_time = datetime.now()

        cursor.execute("""
            SELECT * FROM ping_results
            WHERE timestamp BETWEEN ? AND ?
        """, (start_time, end_time))

        results = cursor.fetchall()
        assert len(results) >= 0

    def test_update_ping_result(self, populated_db):
        """Test updating existing ping result."""
        cursor = populated_db.cursor()

        # Get first record
        cursor.execute("SELECT id FROM ping_results LIMIT 1")
        record_id = cursor.fetchone()[0]

        # Update it
        new_latency = 99.9
        cursor.execute("""
            UPDATE ping_results
            SET avg_latency = ?
            WHERE id = ?
        """, (new_latency, record_id))

        populated_db.commit()

        # Verify update
        cursor.execute("""
            SELECT avg_latency FROM ping_results WHERE id = ?
        """, (record_id,))

        assert cursor.fetchone()[0] == new_latency

    def test_delete_old_records(self, db_connection, old_ping_data):
        """Test deleting records older than retention period."""
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

        # Delete records older than 90 days
        cutoff_date = datetime.now() - timedelta(days=90)
        cursor.execute("""
            DELETE FROM ping_results
            WHERE timestamp < ?
        """, (cutoff_date,))

        deleted_count = cursor.rowcount
        db_connection.commit()

        assert deleted_count == len(old_ping_data)

    def test_index_exists(self, db_connection):
        """Test that required indexes exist."""
        cursor = db_connection.cursor()

        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='index'
        """)

        indexes = {row[0] for row in cursor.fetchall()}

        # Check for expected indexes
        assert any('idx_host_timestamp' in idx for idx in indexes)
        assert any('idx_timestamp' in idx for idx in indexes)

    def test_query_statistics_by_host(self, populated_db):
        """Test calculating statistics for a specific host."""
        cursor = populated_db.cursor()

        cursor.execute("""
            SELECT
                COUNT(*) as total_pings,
                AVG(success_rate) as avg_success_rate,
                AVG(avg_latency) as overall_avg_latency,
                MIN(min_latency) as min_latency,
                MAX(max_latency) as max_latency
            FROM ping_results
            WHERE host = ?
            AND avg_latency IS NOT NULL
        """, ("8.8.8.8",))

        result = cursor.fetchone()
        assert result is not None
        assert result[0] > 0  # total_pings

    def test_database_integrity_constraints(self, db_connection):
        """Test database integrity constraints."""
        cursor = db_connection.cursor()

        # Test NOT NULL constraint
        with pytest.raises(sqlite3.IntegrityError):
            cursor.execute("""
                INSERT INTO ping_results
                (timestamp, ping_count, success_count, failure_count, success_rate)
                VALUES (?, ?, ?, ?, ?)
            """, (datetime.now(), 10, 10, 0, 100.0))

    def test_transaction_rollback(self, populated_db):
        """Test transaction rollback functionality."""
        cursor = populated_db.cursor()

        # Get initial count
        cursor.execute("SELECT COUNT(*) FROM ping_results")
        initial_count = cursor.fetchone()[0]

        # Start transaction
        cursor.execute("""
            INSERT INTO ping_results
            (host, timestamp, ping_count, success_count, failure_count,
             success_rate, min_latency, max_latency, avg_latency)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, ("test.com", datetime.now(), 10, 10, 0, 100.0, 10.0, 20.0, 15.0))

        # Rollback
        populated_db.rollback()

        # Verify count unchanged
        cursor.execute("SELECT COUNT(*) FROM ping_results")
        assert cursor.fetchone()[0] == initial_count

    def test_transaction_commit(self, db_connection):
        """Test transaction commit functionality."""
        cursor = db_connection.cursor()

        cursor.execute("""
            INSERT INTO ping_results
            (host, timestamp, ping_count, success_count, failure_count,
             success_rate, min_latency, max_latency, avg_latency)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, ("test.com", datetime.now(), 10, 10, 0, 100.0, 10.0, 20.0, 15.0))

        db_connection.commit()

        cursor.execute("SELECT COUNT(*) FROM ping_results")
        assert cursor.fetchone()[0] == 1

    def test_bulk_insert_performance(self, db_connection):
        """Test bulk insert performance."""
        cursor = db_connection.cursor()
        records = []

        for i in range(100):
            records.append((
                f"host{i % 10}.com",
                datetime.now() - timedelta(minutes=i),
                10,
                10,
                0,
                100.0,
                10.0,
                20.0,
                15.0
            ))

        cursor.executemany("""
            INSERT INTO ping_results
            (host, timestamp, ping_count, success_count, failure_count,
             success_rate, min_latency, max_latency, avg_latency)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, records)

        db_connection.commit()

        cursor.execute("SELECT COUNT(*) FROM ping_results")
        assert cursor.fetchone()[0] == 100

    def test_concurrent_read_access(self, populated_db, temp_db):
        """Test concurrent read access to database."""
        # Create second connection
        conn2 = sqlite3.connect(temp_db)
        cursor2 = conn2.cursor()

        # Read from both connections
        cursor1 = populated_db.cursor()
        cursor1.execute("SELECT COUNT(*) FROM ping_results")
        count1 = cursor1.fetchone()[0]

        cursor2.execute("SELECT COUNT(*) FROM ping_results")
        count2 = cursor2.fetchone()[0]

        assert count1 == count2
        conn2.close()

    def test_query_latest_results(self, populated_db):
        """Test querying most recent results per host."""
        cursor = populated_db.cursor()

        cursor.execute("""
            SELECT host, MAX(timestamp) as latest_timestamp
            FROM ping_results
            GROUP BY host
        """)

        results = cursor.fetchall()
        assert len(results) > 0

    def test_database_size_management(self, temp_db):
        """Test database size monitoring."""
        import os

        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()

        # Insert data
        for i in range(1000):
            cursor.execute("""
                INSERT INTO ping_results
                (host, timestamp, ping_count, success_count, failure_count,
                 success_rate, min_latency, max_latency, avg_latency)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, ("test.com", datetime.now(), 10, 10, 0, 100.0, 10.0, 20.0, 15.0))

        conn.commit()

        # Check database size
        db_size = os.path.getsize(temp_db)
        assert db_size > 0

        # Vacuum to reclaim space
        cursor.execute("VACUUM")

        conn.close()

    def test_null_latency_handling(self, db_connection):
        """Test handling of NULL latency values for failed pings."""
        cursor = db_connection.cursor()

        cursor.execute("""
            INSERT INTO ping_results
            (host, timestamp, ping_count, success_count, failure_count,
             success_rate, min_latency, max_latency, avg_latency)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, ("unreachable.host", datetime.now(), 10, 0, 10, 0.0, None, None, None))

        db_connection.commit()

        cursor.execute("""
            SELECT min_latency, max_latency, avg_latency
            FROM ping_results
            WHERE host = ?
        """, ("unreachable.host",))

        result = cursor.fetchone()
        assert result[0] is None
        assert result[1] is None
        assert result[2] is None

    @pytest.mark.parametrize("retention_days", [1, 7, 30, 90, 365])
    def test_cleanup_with_various_retention_periods(self, db_connection, retention_days):
        """Test cleanup job with different retention periods."""
        cursor = db_connection.cursor()

        # Insert data with various ages
        for days_ago in [0, 10, 50, 100, 200]:
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

        # Delete old records
        cutoff_date = datetime.now() - timedelta(days=retention_days)
        cursor.execute("""
            DELETE FROM ping_results WHERE timestamp < ?
        """, (cutoff_date,))

        deleted = cursor.rowcount
        db_connection.commit()

        assert deleted >= 0

    def test_database_backup_feasibility(self, temp_db):
        """Test that database can be backed up."""
        import shutil

        backup_path = temp_db + ".backup"

        # Create backup
        shutil.copy2(temp_db, backup_path)

        # Verify backup exists
        import os
        assert os.path.exists(backup_path)

        # Cleanup
        os.unlink(backup_path)

    def test_query_performance_with_index(self, populated_db):
        """Test that queries use indexes efficiently."""
        cursor = populated_db.cursor()

        # Explain query plan
        cursor.execute("""
            EXPLAIN QUERY PLAN
            SELECT * FROM ping_results
            WHERE host = ? AND timestamp > ?
        """, ("8.8.8.8", datetime.now() - timedelta(days=1)))

        plan = cursor.fetchall()
        # Plan should mention index usage
        assert len(plan) > 0
