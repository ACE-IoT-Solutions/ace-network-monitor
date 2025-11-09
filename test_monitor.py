"""Tests for the monitoring module."""

import pytest
from datetime import datetime

from config import Config
from database import Database, PingResult
from monitor import PingStats


def test_ping_stats_success_rate():
    """Test success rate calculation."""
    stats = PingStats(
        success_count=8,
        failure_count=2,
        min_latency=5.0,
        max_latency=15.0,
        avg_latency=10.0,
    )
    assert stats.success_rate == 80.0


def test_ping_stats_zero_success():
    """Test success rate with all failures."""
    stats = PingStats(
        success_count=0,
        failure_count=5,
        min_latency=None,
        max_latency=None,
        avg_latency=None,
    )
    assert stats.success_rate == 0.0


def test_ping_stats_full_success():
    """Test success rate with 100% success."""
    stats = PingStats(
        success_count=5,
        failure_count=0,
        min_latency=5.0,
        max_latency=15.0,
        avg_latency=10.0,
    )
    assert stats.success_rate == 100.0


def test_config_defaults():
    """Test default configuration values."""
    config = Config()
    assert config.monitoring_interval == 60
    assert config.ping_count == 5
    assert config.ping_timeout == 2
    assert len(config.hosts) > 0
    assert config.retention_days == 90


def test_database_insert_and_retrieve(tmp_path):
    """Test database insert and retrieve operations."""
    db_path = tmp_path / "test.db"
    db = Database(str(db_path))

    # Create test result
    result = PingResult(
        host_name="Test Host",
        host_address="192.168.1.1",
        timestamp=datetime.now(),
        success_count=5,
        failure_count=0,
        success_rate=100.0,
        min_latency=5.0,
        max_latency=15.0,
        avg_latency=10.0,
    )

    # Insert result
    db.insert_result(result)

    # Retrieve results
    results = db.get_results(host_address="192.168.1.1")

    assert len(results) == 1
    assert results[0].host_name == "Test Host"
    assert results[0].success_rate == 100.0
    assert results[0].avg_latency == 10.0


def test_database_statistics(tmp_path):
    """Test database statistics calculation."""
    db_path = tmp_path / "test.db"
    db = Database(str(db_path))

    # Insert multiple results
    for i in range(5):
        result = PingResult(
            host_name="Test Host",
            host_address="192.168.1.1",
            timestamp=datetime.now(),
            success_count=4,
            failure_count=1,
            success_rate=80.0,
            min_latency=5.0 + i,
            max_latency=15.0 + i,
            avg_latency=10.0 + i,
        )
        db.insert_result(result)

    # Get statistics
    stats = db.get_statistics("192.168.1.1")

    assert stats["total_checks"] == 5
    assert stats["avg_success_rate"] == 80.0
    assert stats["overall_min_latency"] == 5.0
    assert stats["overall_max_latency"] == 19.0


if __name__ == "__main__":
    pytest.main([__file__])
