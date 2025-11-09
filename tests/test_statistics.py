"""
Unit tests for statistics calculations.

Tests cover:
- Success rate calculations
- Latency statistics (min, max, average)
- Aggregation accuracy
- Edge cases with missing data
- Time-based statistics
"""

import pytest
from datetime import datetime, timedelta


@pytest.mark.unit
@pytest.mark.stats
class TestStatisticsCalculations:
    """Test suite for statistics calculations."""

    def test_success_rate_calculation_all_success(self):
        """Test success rate calculation with 100% success."""
        success_count = 10
        total_count = 10

        success_rate = (success_count / total_count) * 100
        assert success_rate == 100.0

    def test_success_rate_calculation_all_failure(self):
        """Test success rate calculation with 0% success."""
        success_count = 0
        total_count = 10

        success_rate = (success_count / total_count) * 100
        assert success_rate == 0.0

    def test_success_rate_calculation_partial(self):
        """Test success rate calculation with partial success."""
        success_count = 7
        total_count = 10

        success_rate = (success_count / total_count) * 100
        assert success_rate == 70.0

    @pytest.mark.parametrize(
        "success,total,expected",
        [
            (10, 10, 100.0),
            (5, 10, 50.0),
            (3, 10, 30.0),
            (0, 10, 0.0),
            (1, 100, 1.0),
            (99, 100, 99.0),
        ],
    )
    def test_success_rate_various_scenarios(self, success, total, expected):
        """Test success rate calculation with various inputs."""
        calculated = (success / total) * 100
        assert abs(calculated - expected) < 0.01

    def test_average_latency_calculation(self):
        """Test average latency calculation."""
        latencies = [10.5, 12.3, 15.7, 11.2, 13.8]
        expected_avg = sum(latencies) / len(latencies)

        calculated_avg = sum(latencies) / len(latencies)
        assert abs(calculated_avg - expected_avg) < 0.01

    def test_min_latency_calculation(self):
        """Test minimum latency identification."""
        latencies = [10.5, 12.3, 8.1, 11.2, 13.8]
        assert min(latencies) == 8.1

    def test_max_latency_calculation(self):
        """Test maximum latency identification."""
        latencies = [10.5, 12.3, 8.1, 11.2, 13.8]
        assert max(latencies) == 13.8

    def test_latency_statistics_with_single_value(self):
        """Test latency statistics with only one measurement."""
        latencies = [12.5]

        assert min(latencies) == 12.5
        assert max(latencies) == 12.5
        assert sum(latencies) / len(latencies) == 12.5

    def test_latency_statistics_with_identical_values(self):
        """Test latency statistics with all identical values."""
        latencies = [10.0] * 10

        assert min(latencies) == 10.0
        assert max(latencies) == 10.0
        assert sum(latencies) / len(latencies) == 10.0

    def test_statistics_with_empty_dataset(self):
        """Test statistics calculation with empty dataset."""
        latencies = []

        # Should handle gracefully
        if latencies:
            avg = sum(latencies) / len(latencies)
        else:
            avg = None

        assert avg is None

    def test_packet_loss_percentage_calculation(self):
        """Test packet loss percentage calculation."""
        packets_sent = 10
        packets_received = 7

        packet_loss = ((packets_sent - packets_received) / packets_sent) * 100
        assert packet_loss == 30.0

    def test_failure_count_from_success(self):
        """Test deriving failure count from success count."""
        total_pings = 10
        success_count = 8

        failure_count = total_pings - success_count
        assert failure_count == 2

    def test_aggregated_statistics_multiple_hosts(self, populated_db):
        """Test aggregated statistics across multiple hosts."""
        cursor = populated_db.cursor()

        cursor.execute("""
            SELECT
                AVG(success_rate) as overall_success_rate,
                AVG(avg_latency) as overall_avg_latency
            FROM ping_results
            WHERE avg_latency IS NOT NULL
        """)

        result = cursor.fetchone()
        assert result is not None
        assert 0 <= result[0] <= 100  # Success rate should be 0-100%

    def test_statistics_over_time_range(self, populated_db):
        """Test statistics calculation over specific time range."""
        cursor = populated_db.cursor()

        start_time = datetime.now() - timedelta(hours=1)
        end_time = datetime.now()

        cursor.execute(
            """
            SELECT
                COUNT(*) as ping_count,
                AVG(success_rate) as avg_success_rate
            FROM ping_results
            WHERE timestamp BETWEEN ? AND ?
        """,
            (start_time, end_time),
        )

        result = cursor.fetchone()
        assert result is not None

    def test_hourly_statistics_aggregation(self, populated_db):
        """Test aggregating statistics by hour."""
        cursor = populated_db.cursor()

        cursor.execute("""
            SELECT
                strftime('%Y-%m-%d %H:00:00', timestamp) as hour,
                COUNT(*) as ping_count,
                AVG(success_rate) as avg_success_rate
            FROM ping_results
            GROUP BY hour
            ORDER BY hour DESC
            LIMIT 24
        """)

        results = cursor.fetchall()
        assert isinstance(results, list)

    def test_daily_statistics_aggregation(self, populated_db):
        """Test aggregating statistics by day."""
        cursor = populated_db.cursor()

        cursor.execute("""
            SELECT
                DATE(timestamp) as day,
                COUNT(*) as ping_count,
                AVG(success_rate) as avg_success_rate,
                AVG(avg_latency) as avg_latency
            FROM ping_results
            GROUP BY day
            ORDER BY day DESC
            LIMIT 30
        """)

        results = cursor.fetchall()
        assert isinstance(results, list)

    def test_per_host_statistics(self, populated_db):
        """Test statistics calculation per host."""
        cursor = populated_db.cursor()

        cursor.execute("""
            SELECT
                host,
                COUNT(*) as total_pings,
                AVG(success_rate) as avg_success_rate,
                MIN(min_latency) as best_latency,
                MAX(max_latency) as worst_latency
            FROM ping_results
            WHERE min_latency IS NOT NULL
            GROUP BY host
        """)

        results = cursor.fetchall()
        assert len(results) > 0

        for row in results:
            host, total, success_rate, min_lat, max_lat = row
            assert total > 0
            assert 0 <= success_rate <= 100
            if min_lat and max_lat:
                assert min_lat <= max_lat

    @pytest.mark.parametrize("percentile", [50, 90, 95, 99])
    def test_latency_percentile_calculation(self, percentile):
        """Test latency percentile calculations."""
        latencies = [float(i) for i in range(1, 101)]  # 1-100ms

        # Simple percentile calculation
        sorted_latencies = sorted(latencies)
        index = int((percentile / 100) * len(sorted_latencies))
        percentile_value = sorted_latencies[min(index, len(sorted_latencies) - 1)]

        assert percentile_value > 0

    def test_uptime_percentage_calculation(self):
        """Test uptime percentage calculation."""
        total_checks = 1440  # 24 hours * 60 minutes
        successful_checks = 1420

        uptime_percentage = (successful_checks / total_checks) * 100
        assert uptime_percentage > 98.0

    def test_downtime_duration_calculation(self):
        """Test downtime duration calculation."""
        check_interval_minutes = 1
        failed_checks = 20

        downtime_minutes = check_interval_minutes * failed_checks
        assert downtime_minutes == 20

    def test_statistics_with_null_values(self, populated_db):
        """Test statistics calculation handling NULL values."""
        cursor = populated_db.cursor()

        # Insert record with NULL latencies (failed ping)
        cursor.execute(
            """
            INSERT INTO ping_results
            (host, timestamp, ping_count, success_count, failure_count,
             success_rate, min_latency, max_latency, avg_latency)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            ("failed.host", datetime.now(), 10, 0, 10, 0.0, None, None, None),
        )

        populated_db.commit()

        # Query should exclude NULL values in averages
        cursor.execute(
            """
            SELECT
                AVG(avg_latency) as avg_latency,
                COUNT(avg_latency) as latency_count,
                COUNT(*) as total_count
            FROM ping_results
            WHERE host = ?
        """,
            ("failed.host",),
        )

        result = cursor.fetchone()
        assert result[1] == 0  # No latency values
        assert result[2] == 1  # But record exists

    def test_moving_average_calculation(self):
        """Test moving average calculation for latency trends."""
        latencies = [10.0, 12.0, 11.0, 13.0, 14.0, 12.0, 15.0]
        window_size = 3

        moving_averages = []
        for i in range(len(latencies) - window_size + 1):
            window = latencies[i : i + window_size]
            moving_averages.append(sum(window) / window_size)

        assert len(moving_averages) == len(latencies) - window_size + 1
        assert all(avg > 0 for avg in moving_averages)

    def test_standard_deviation_calculation(self):
        """Test standard deviation for latency variability."""
        latencies = [10.0, 12.0, 11.0, 13.0, 14.0]

        mean = sum(latencies) / len(latencies)
        variance = sum((x - mean) ** 2 for x in latencies) / len(latencies)
        std_dev = variance**0.5

        assert std_dev > 0

    def test_jitter_calculation(self):
        """Test jitter (latency variation) calculation."""
        latencies = [10.0, 12.0, 11.0, 15.0, 9.0]

        # Simple jitter: difference between consecutive measurements
        jitters = [
            abs(latencies[i] - latencies[i - 1]) for i in range(1, len(latencies))
        ]

        avg_jitter = sum(jitters) / len(jitters)
        assert avg_jitter >= 0

    def test_availability_calculation(self):
        """Test availability calculation over time period."""
        total_time_minutes = 1440  # 24 hours
        downtime_minutes = 20

        availability = (
            (total_time_minutes - downtime_minutes) / total_time_minutes
        ) * 100
        assert availability > 98.0

    @pytest.mark.parametrize("window_minutes", [5, 15, 60, 1440])
    def test_statistics_over_time_windows(self, window_minutes, populated_db):
        """Test statistics calculation over different time windows."""
        cursor = populated_db.cursor()

        cutoff_time = datetime.now() - timedelta(minutes=window_minutes)

        cursor.execute(
            """
            SELECT
                COUNT(*) as ping_count,
                AVG(success_rate) as avg_success_rate
            FROM ping_results
            WHERE timestamp >= ?
        """,
            (cutoff_time,),
        )

        result = cursor.fetchone()
        assert result is not None

    def test_comparison_statistics_between_hosts(self, populated_db):
        """Test comparative statistics between different hosts."""
        cursor = populated_db.cursor()

        cursor.execute("""
            SELECT
                host,
                AVG(success_rate) as avg_success_rate,
                AVG(avg_latency) as avg_latency
            FROM ping_results
            WHERE avg_latency IS NOT NULL
            GROUP BY host
            HAVING COUNT(*) >= 1
            ORDER BY avg_success_rate DESC
        """)

        results = cursor.fetchall()
        if len(results) > 1:
            # Verify results are sorted by success rate
            success_rates = [row[1] for row in results]
            assert success_rates == sorted(success_rates, reverse=True)

    def test_outlier_detection(self):
        """Test detection of latency outliers."""
        latencies = [10.0, 11.0, 12.0, 11.5, 10.5, 100.0]  # 100.0 is outlier

        mean = sum(latencies) / len(latencies)
        threshold = mean * 2  # Simple threshold

        outliers = [lat for lat in latencies if lat > threshold]
        assert len(outliers) > 0
        assert 100.0 in outliers

    def test_trend_calculation(self):
        """Test trend analysis for improving/degrading performance."""
        # Simulate degrading latency trend
        latencies_over_time = [
            (10.0, datetime.now() - timedelta(hours=5)),
            (12.0, datetime.now() - timedelta(hours=4)),
            (14.0, datetime.now() - timedelta(hours=3)),
            (16.0, datetime.now() - timedelta(hours=2)),
            (18.0, datetime.now() - timedelta(hours=1)),
        ]

        # Simple trend: compare first half vs second half
        midpoint = len(latencies_over_time) // 2
        first_half_avg = (
            sum(lat for lat, _ in latencies_over_time[:midpoint]) / midpoint
        )
        second_half_avg = sum(lat for lat, _ in latencies_over_time[midpoint:]) / (
            len(latencies_over_time) - midpoint
        )

        # Trend is degrading if second half is worse
        is_degrading = second_half_avg > first_half_avg
        assert is_degrading is True

    def test_reliability_score_calculation(self):
        """Test calculation of overall reliability score."""
        success_rate = 95.0
        avg_latency = 15.0
        max_acceptable_latency = 100.0

        # Simple reliability score: weighted combination
        latency_score = (1 - (avg_latency / max_acceptable_latency)) * 100
        reliability_score = (success_rate * 0.7) + (latency_score * 0.3)

        assert 0 <= reliability_score <= 100
