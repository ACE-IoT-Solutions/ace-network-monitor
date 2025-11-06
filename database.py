"""Database layer for storing and retrieving ping results."""

import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Generator


@dataclass
class PingResult:
    """Represents a single ping check result."""

    host_name: str
    host_address: str
    timestamp: datetime
    success_count: int
    failure_count: int
    success_rate: float
    min_latency: float | None
    max_latency: float | None
    avg_latency: float | None


@dataclass
class OutageEvent:
    """Represents an outage/recovery event for a host."""

    id: int | None
    host_name: str
    host_address: str
    event_type: str  # 'outage_start', 'outage_end', 'degraded'
    start_time: datetime
    end_time: datetime | None
    duration_seconds: int | None
    checks_failed: int
    checks_during_outage: int
    recovery_success_rate: float | None
    notes: str | None


class Database:
    """Database manager for ping results."""

    def __init__(self, db_path: str):
        """Initialize database connection.

        Args:
            db_path: Path to SQLite database file.
        """
        self.db_path = Path(db_path)
        self._init_database()

    @contextmanager
    def _get_connection(self) -> Generator[sqlite3.Connection, None, None]:
        """Context manager for database connections.

        Yields:
            SQLite connection object.
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def _init_database(self) -> None:
        """Initialize database schema if it doesn't exist."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS ping_results (
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
                )
                """
            )

            # Create outage events table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS outage_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    host_name TEXT NOT NULL,
                    host_address TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    start_time DATETIME NOT NULL,
                    end_time DATETIME,
                    duration_seconds INTEGER,
                    checks_failed INTEGER DEFAULT 0,
                    checks_during_outage INTEGER DEFAULT 0,
                    recovery_success_rate REAL,
                    notes TEXT
                )
                """
            )

            # Create indexes for efficient queries
            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_timestamp
                ON ping_results(timestamp)
                """
            )
            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_host_address
                ON ping_results(host_address)
                """
            )
            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_host_timestamp
                ON ping_results(host_address, timestamp)
                """
            )
            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_events_host_time
                ON outage_events(host_address, start_time DESC)
                """
            )
            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_events_time
                ON outage_events(start_time DESC)
                """
            )

    def insert_result(self, result: PingResult) -> None:
        """Insert a ping result into the database.

        Args:
            result: PingResult object to store.
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT OR REPLACE INTO ping_results
                (host_name, host_address, timestamp, success_count,
                 failure_count, success_rate, min_latency, max_latency, avg_latency)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    result.host_name,
                    result.host_address,
                    result.timestamp,
                    result.success_count,
                    result.failure_count,
                    result.success_rate,
                    result.min_latency,
                    result.max_latency,
                    result.avg_latency,
                ),
            )

    def get_results(
        self,
        host_address: str | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        limit: int | None = None,
    ) -> list[PingResult]:
        """Retrieve ping results from the database.

        Args:
            host_address: Filter by host address. If None, returns all hosts.
            start_time: Filter results after this time. If None, no start limit.
            end_time: Filter results before this time. If None, no end limit.
            limit: Maximum number of results to return. If None, returns all.

        Returns:
            List of PingResult objects.
        """
        query = "SELECT * FROM ping_results WHERE 1=1"
        params: list[str | datetime | int] = []

        if host_address:
            query += " AND host_address = ?"
            params.append(host_address)

        if start_time:
            query += " AND timestamp >= ?"
            params.append(start_time)

        if end_time:
            query += " AND timestamp <= ?"
            params.append(end_time)

        query += " ORDER BY timestamp DESC"

        if limit:
            query += " LIMIT ?"
            params.append(limit)

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()

        return [
            PingResult(
                host_name=row["host_name"],
                host_address=row["host_address"],
                timestamp=datetime.fromisoformat(row["timestamp"]),
                success_count=row["success_count"],
                failure_count=row["failure_count"],
                success_rate=row["success_rate"],
                min_latency=row["min_latency"],
                max_latency=row["max_latency"],
                avg_latency=row["avg_latency"],
            )
            for row in rows
        ]

    def get_latest_results(self) -> list[PingResult]:
        """Get the most recent result for each host.

        Returns:
            List of PingResult objects, one per host.
        """
        query = """
            SELECT pr1.*
            FROM ping_results pr1
            INNER JOIN (
                SELECT host_address, MAX(timestamp) as max_timestamp
                FROM ping_results
                GROUP BY host_address
            ) pr2
            ON pr1.host_address = pr2.host_address
            AND pr1.timestamp = pr2.max_timestamp
            ORDER BY pr1.host_name
        """

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query)
            rows = cursor.fetchall()

        return [
            PingResult(
                host_name=row["host_name"],
                host_address=row["host_address"],
                timestamp=datetime.fromisoformat(row["timestamp"]),
                success_count=row["success_count"],
                failure_count=row["failure_count"],
                success_rate=row["success_rate"],
                min_latency=row["min_latency"],
                max_latency=row["max_latency"],
                avg_latency=row["avg_latency"],
            )
            for row in rows
        ]

    def get_statistics(
        self,
        host_address: str,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
    ) -> dict[str, float]:
        """Calculate aggregate statistics for a host.

        Args:
            host_address: Host address to calculate statistics for.
            start_time: Filter results after this time. If None, no start limit.
            end_time: Filter results before this time. If None, no end limit.

        Returns:
            Dictionary with aggregate statistics.
        """
        query = """
            SELECT
                AVG(success_rate) as avg_success_rate,
                MIN(success_rate) as min_success_rate,
                MAX(success_rate) as max_success_rate,
                AVG(avg_latency) as overall_avg_latency,
                MIN(min_latency) as overall_min_latency,
                MAX(max_latency) as overall_max_latency,
                COUNT(*) as total_checks
            FROM ping_results
            WHERE host_address = ?
        """
        params: list[str | datetime] = [host_address]

        if start_time:
            query += " AND timestamp >= ?"
            params.append(start_time)

        if end_time:
            query += " AND timestamp <= ?"
            params.append(end_time)

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            row = cursor.fetchone()

        if row and row["total_checks"] > 0:
            return {
                "avg_success_rate": row["avg_success_rate"] or 0.0,
                "min_success_rate": row["min_success_rate"] or 0.0,
                "max_success_rate": row["max_success_rate"] or 0.0,
                "overall_avg_latency": row["overall_avg_latency"] or 0.0,
                "overall_min_latency": row["overall_min_latency"] or 0.0,
                "overall_max_latency": row["overall_max_latency"] or 0.0,
                "total_checks": row["total_checks"],
            }
        else:
            return {
                "avg_success_rate": 0.0,
                "min_success_rate": 0.0,
                "max_success_rate": 0.0,
                "overall_avg_latency": 0.0,
                "overall_min_latency": 0.0,
                "overall_max_latency": 0.0,
                "total_checks": 0,
            }

    def cleanup_old_records(self, retention_days: int) -> int:
        """Delete records older than specified retention period.

        Args:
            retention_days: Number of days to retain records.

        Returns:
            Number of records deleted.
        """
        cutoff_date = datetime.now() - timedelta(days=retention_days)

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "DELETE FROM ping_results WHERE timestamp < ?",
                (cutoff_date,),
            )
            deleted_count = cursor.rowcount

        return deleted_count

    def get_host_addresses(self) -> list[str]:
        """Get list of all unique host addresses in the database.

        Returns:
            List of host addresses.
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT DISTINCT host_address FROM ping_results ORDER BY host_address"
            )
            rows = cursor.fetchall()

        return [row["host_address"] for row in rows]

    def get_active_outage(self, host_address: str) -> OutageEvent | None:
        """Get the current active outage for a host (if any).

        Args:
            host_address: Host address to check.

        Returns:
            OutageEvent if there's an active outage, None otherwise.
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT * FROM outage_events
                WHERE host_address = ?
                AND end_time IS NULL
                ORDER BY start_time DESC
                LIMIT 1
                """,
                (host_address,),
            )
            row = cursor.fetchone()

        if row:
            return OutageEvent(
                id=row["id"],
                host_name=row["host_name"],
                host_address=row["host_address"],
                event_type=row["event_type"],
                start_time=datetime.fromisoformat(row["start_time"]),
                end_time=None,
                duration_seconds=row["duration_seconds"],
                checks_failed=row["checks_failed"],
                checks_during_outage=row["checks_during_outage"],
                recovery_success_rate=row["recovery_success_rate"],
                notes=row["notes"],
            )
        return None

    def create_outage_event(
        self, host_name: str, host_address: str, start_time: datetime, notes: str | None = None
    ) -> int:
        """Create a new outage event.

        Args:
            host_name: Human-readable host name.
            host_address: Host address.
            start_time: When the outage started.
            notes: Optional notes about the outage.

        Returns:
            ID of the created event.
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO outage_events
                (host_name, host_address, event_type, start_time, checks_failed, checks_during_outage, notes)
                VALUES (?, ?, 'outage_start', ?, 1, 1, ?)
                """,
                (host_name, host_address, start_time, notes),
            )
            return cursor.lastrowid

    def update_outage_event(
        self,
        event_id: int,
        checks_failed: int | None = None,
        checks_during_outage: int | None = None,
    ) -> None:
        """Update an ongoing outage event with new check data.

        Args:
            event_id: ID of the event to update.
            checks_failed: Total number of failed checks.
            checks_during_outage: Total number of checks during outage.
        """
        updates = []
        params = []

        if checks_failed is not None:
            updates.append("checks_failed = ?")
            params.append(checks_failed)

        if checks_during_outage is not None:
            updates.append("checks_during_outage = ?")
            params.append(checks_during_outage)

        if updates:
            params.append(event_id)
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    f"UPDATE outage_events SET {', '.join(updates)} WHERE id = ?",
                    params,
                )

    def close_outage_event(
        self,
        event_id: int,
        end_time: datetime,
        recovery_success_rate: float,
        notes: str | None = None,
    ) -> None:
        """Close an outage event when the host recovers.

        Args:
            event_id: ID of the event to close.
            end_time: When the host recovered.
            recovery_success_rate: Success rate on first check after recovery.
            notes: Optional notes about the recovery.
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            # Get the start time to calculate duration
            cursor.execute(
                "SELECT start_time, notes FROM outage_events WHERE id = ?",
                (event_id,),
            )
            row = cursor.fetchone()
            if row:
                start_time = datetime.fromisoformat(row["start_time"])
                duration = int((end_time - start_time).total_seconds())

                # Combine existing notes with new notes if provided
                existing_notes = row["notes"]
                if notes:
                    combined_notes = f"{existing_notes}\n{notes}" if existing_notes else notes
                else:
                    combined_notes = existing_notes

                cursor.execute(
                    """
                    UPDATE outage_events
                    SET end_time = ?,
                        duration_seconds = ?,
                        recovery_success_rate = ?,
                        event_type = 'outage_end',
                        notes = ?
                    WHERE id = ?
                    """,
                    (end_time, duration, recovery_success_rate, combined_notes, event_id),
                )

    def get_outage_events(
        self,
        host_address: str | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        active_only: bool = False,
        limit: int | None = None,
    ) -> list[OutageEvent]:
        """Retrieve outage events from the database.

        Args:
            host_address: Filter by host address. If None, returns all hosts.
            start_time: Filter events after this time. If None, no start limit.
            end_time: Filter events before this time. If None, no end limit.
            active_only: If True, only return active (ongoing) outages.
            limit: Maximum number of results to return. If None, returns all.

        Returns:
            List of OutageEvent objects.
        """
        query = "SELECT * FROM outage_events WHERE 1=1"
        params: list[str | datetime | int] = []

        if host_address:
            query += " AND host_address = ?"
            params.append(host_address)

        if start_time:
            query += " AND start_time >= ?"
            params.append(start_time)

        if end_time:
            query += " AND start_time <= ?"
            params.append(end_time)

        if active_only:
            query += " AND end_time IS NULL"

        query += " ORDER BY start_time DESC"

        if limit:
            query += " LIMIT ?"
            params.append(limit)

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()

        return [
            OutageEvent(
                id=row["id"],
                host_name=row["host_name"],
                host_address=row["host_address"],
                event_type=row["event_type"],
                start_time=datetime.fromisoformat(row["start_time"]),
                end_time=datetime.fromisoformat(row["end_time"]) if row["end_time"] else None,
                duration_seconds=row["duration_seconds"],
                checks_failed=row["checks_failed"],
                checks_during_outage=row["checks_during_outage"],
                recovery_success_rate=row["recovery_success_rate"],
                notes=row["notes"],
            )
            for row in rows
        ]

    def get_outage_statistics(
        self,
        host_address: str,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
    ) -> dict[str, int | float]:
        """Calculate outage statistics for a host.

        Args:
            host_address: Host address to calculate statistics for.
            start_time: Filter events after this time. If None, no start limit.
            end_time: Filter events before this time. If None, no end limit.

        Returns:
            Dictionary with outage statistics.
        """
        query = """
            SELECT
                COUNT(*) as total_outages,
                SUM(CASE WHEN end_time IS NULL THEN 1 ELSE 0 END) as active_outages,
                AVG(duration_seconds) as avg_duration_seconds,
                MAX(duration_seconds) as max_duration_seconds,
                SUM(duration_seconds) as total_downtime_seconds
            FROM outage_events
            WHERE host_address = ?
            AND end_time IS NOT NULL
        """
        params: list[str | datetime] = [host_address]

        if start_time:
            query += " AND start_time >= ?"
            params.append(start_time)

        if end_time:
            query += " AND start_time <= ?"
            params.append(end_time)

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            row = cursor.fetchone()

        if row and row["total_outages"]:
            return {
                "total_outages": row["total_outages"] or 0,
                "active_outages": row["active_outages"] or 0,
                "avg_duration_seconds": row["avg_duration_seconds"] or 0.0,
                "max_duration_seconds": row["max_duration_seconds"] or 0,
                "total_downtime_seconds": row["total_downtime_seconds"] or 0,
            }
        else:
            return {
                "total_outages": 0,
                "active_outages": 0,
                "avg_duration_seconds": 0.0,
                "max_duration_seconds": 0,
                "total_downtime_seconds": 0,
            }
