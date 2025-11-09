"""
Pytest configuration and fixtures for ACE Connection Logger tests.

This module provides reusable fixtures for testing all components of the system.
"""

import os
import sqlite3
import tempfile
from datetime import datetime, timedelta
from typing import Generator, List
from unittest.mock import MagicMock, Mock

import pytest
import yaml


@pytest.fixture
def temp_db() -> Generator[str, None, None]:
    """
    Create a temporary SQLite database for testing.

    Yields:
        Path to temporary database file
    """
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    yield db_path

    # Cleanup
    try:
        os.unlink(db_path)
    except OSError:
        pass


@pytest.fixture
def db_connection(temp_db: str) -> Generator[sqlite3.Connection, None, None]:
    """
    Create a database connection with schema initialized.

    Args:
        temp_db: Path to temporary database

    Yields:
        SQLite connection object
    """
    conn = sqlite3.connect(temp_db)

    # Initialize schema
    conn.execute("""
        CREATE TABLE IF NOT EXISTS ping_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            host TEXT NOT NULL,
            timestamp DATETIME NOT NULL,
            ping_count INTEGER NOT NULL,
            success_count INTEGER NOT NULL,
            failure_count INTEGER NOT NULL,
            success_rate REAL NOT NULL,
            min_latency REAL,
            max_latency REAL,
            avg_latency REAL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_host_timestamp
        ON ping_results(host, timestamp)
    """)

    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_timestamp
        ON ping_results(timestamp)
    """)

    conn.commit()

    yield conn

    conn.close()


@pytest.fixture
def sample_ping_data() -> List[dict]:
    """
    Generate sample ping result data for testing.

    Returns:
        List of ping result dictionaries
    """
    now = datetime.now()
    return [
        {
            "host": "8.8.8.8",
            "timestamp": now - timedelta(minutes=5),
            "ping_count": 10,
            "success_count": 10,
            "failure_count": 0,
            "success_rate": 100.0,
            "min_latency": 10.5,
            "max_latency": 15.2,
            "avg_latency": 12.3,
        },
        {
            "host": "1.1.1.1",
            "timestamp": now - timedelta(minutes=4),
            "ping_count": 10,
            "success_count": 9,
            "failure_count": 1,
            "success_rate": 90.0,
            "min_latency": 8.1,
            "max_latency": 12.5,
            "avg_latency": 10.2,
        },
        {
            "host": "8.8.8.8",
            "timestamp": now - timedelta(minutes=3),
            "ping_count": 10,
            "success_count": 0,
            "failure_count": 10,
            "success_rate": 0.0,
            "min_latency": None,
            "max_latency": None,
            "avg_latency": None,
        },
    ]


@pytest.fixture
def old_ping_data() -> List[dict]:
    """
    Generate old ping result data for cleanup testing.

    Returns:
        List of ping results older than 90 days
    """
    old_date = datetime.now() - timedelta(days=95)
    return [
        {
            "host": "8.8.8.8",
            "timestamp": old_date,
            "ping_count": 10,
            "success_count": 10,
            "failure_count": 0,
            "success_rate": 100.0,
            "min_latency": 10.5,
            "max_latency": 15.2,
            "avg_latency": 12.3,
        },
        {
            "host": "1.1.1.1",
            "timestamp": old_date - timedelta(days=10),
            "ping_count": 10,
            "success_count": 8,
            "failure_count": 2,
            "success_rate": 80.0,
            "min_latency": 20.1,
            "max_latency": 30.5,
            "avg_latency": 25.2,
        },
    ]


@pytest.fixture
def temp_config_file() -> Generator[str, None, None]:
    """
    Create a temporary configuration file for testing.

    Yields:
        Path to temporary config file
    """
    config = {
        "hosts": ["8.8.8.8", "1.1.1.1", "google.com"],
        "ping_count": 10,
        "interval_seconds": 60,
        "timeout_seconds": 5,
        "retention_days": 90,
        "database_path": "test_pings.db",
        "dashboard": {
            "port": 8501,
            "title": "Test Connection Monitor",
        },
    }

    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        yaml.dump(config, f)
        config_path = f.name

    yield config_path

    # Cleanup
    try:
        os.unlink(config_path)
    except OSError:
        pass


@pytest.fixture
def invalid_config_file() -> Generator[str, None, None]:
    """
    Create an invalid configuration file for negative testing.

    Yields:
        Path to invalid config file
    """
    config = {
        "hosts": [],  # Invalid: empty host list
        "ping_count": -5,  # Invalid: negative count
        "interval_seconds": 0,  # Invalid: zero interval
    }

    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        yaml.dump(config, f)
        config_path = f.name

    yield config_path

    try:
        os.unlink(config_path)
    except OSError:
        pass


@pytest.fixture
def mock_ping_response():
    """
    Create a mock ping response for testing without network access.

    Returns:
        Mock ping response object
    """
    mock = Mock()
    mock.success = True
    mock.packet_loss = 0.0
    mock.rtt_min = 10.5
    mock.rtt_max = 15.2
    mock.rtt_avg = 12.3
    mock.packets_sent = 10
    mock.packets_received = 10
    return mock


@pytest.fixture
def mock_failed_ping_response():
    """
    Create a mock failed ping response for testing failure scenarios.

    Returns:
        Mock failed ping response
    """
    mock = Mock()
    mock.success = False
    mock.packet_loss = 100.0
    mock.rtt_min = None
    mock.rtt_max = None
    mock.rtt_avg = None
    mock.packets_sent = 10
    mock.packets_received = 0
    return mock


@pytest.fixture
def mock_partial_ping_response():
    """
    Create a mock partial success ping response.

    Returns:
        Mock partial success ping response
    """
    mock = Mock()
    mock.success = True
    mock.packet_loss = 30.0
    mock.rtt_min = 8.1
    mock.rtt_max = 25.5
    mock.rtt_avg = 15.2
    mock.packets_sent = 10
    mock.packets_received = 7
    return mock


@pytest.fixture
def populated_db(db_connection: sqlite3.Connection, sample_ping_data: List[dict]):
    """
    Create a database populated with sample data.

    Args:
        db_connection: Database connection
        sample_ping_data: Sample data to insert

    Returns:
        Populated database connection
    """
    cursor = db_connection.cursor()

    for record in sample_ping_data:
        cursor.execute(
            """
            INSERT INTO ping_results
            (host, timestamp, ping_count, success_count, failure_count,
             success_rate, min_latency, max_latency, avg_latency)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                record["host"],
                record["timestamp"],
                record["ping_count"],
                record["success_count"],
                record["failure_count"],
                record["success_rate"],
                record["min_latency"],
                record["max_latency"],
                record["avg_latency"],
            ),
        )

    db_connection.commit()
    return db_connection


@pytest.fixture
def mock_streamlit():
    """
    Mock Streamlit components for dashboard testing.

    Returns:
        Mock streamlit module
    """
    mock_st = MagicMock()
    mock_st.title = Mock()
    mock_st.header = Mock()
    mock_st.subheader = Mock()
    mock_st.write = Mock()
    mock_st.dataframe = Mock()
    mock_st.line_chart = Mock()
    mock_st.metric = Mock()
    mock_st.selectbox = Mock(return_value="8.8.8.8")
    mock_st.multiselect = Mock(return_value=["8.8.8.8", "1.1.1.1"])
    mock_st.date_input = Mock(return_value=datetime.now())
    mock_st.sidebar = MagicMock()
    return mock_st


@pytest.fixture(autouse=True)
def reset_environment():
    """
    Reset environment variables before each test.
    """
    original_env = os.environ.copy()
    yield
    os.environ.clear()
    os.environ.update(original_env)


@pytest.fixture
def capture_logs(caplog):
    """
    Enhanced log capturing with specific level control.

    Args:
        caplog: Pytest's log capture fixture

    Returns:
        Configured caplog fixture
    """
    caplog.set_level("INFO")
    return caplog
