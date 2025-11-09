"""
Unit tests for outage tracking functionality.

Tests cover:
- Creating outage events
- Updating active outages
- Closing outages on recovery
- Closing outages for removed hosts
- Querying outage statistics
"""

import pytest
from datetime import datetime, timedelta
from database import Database


@pytest.fixture
def db_with_outages(temp_db):
    """Create a database with sample outage events."""
    db = Database(temp_db)

    # Create some test hosts with various outage states
    now = datetime.now()

    # Host 1: Active outage
    db.create_outage_event(
        host_name="Test Host 1",
        host_address="192.168.1.1",
        start_time=now - timedelta(minutes=30),
        notes="Test active outage",
    )

    # Host 2: Closed outage
    event_id = db.create_outage_event(
        host_name="Test Host 2",
        host_address="192.168.1.2",
        start_time=now - timedelta(hours=2),
        notes="Test closed outage",
    )
    db.close_outage_event(
        event_id,
        end_time=now - timedelta(hours=1),
        recovery_success_rate=100.0,
        notes="Recovered successfully",
    )

    # Host 3: Another active outage (this will be for a removed host)
    db.create_outage_event(
        host_name="Test Host 3",
        host_address="192.168.1.3",
        start_time=now - timedelta(minutes=15),
        notes="Test outage for removed host",
    )

    # Host 4: Active outage (will remain active)
    db.create_outage_event(
        host_name="Test Host 4",
        host_address="192.168.1.4",
        start_time=now - timedelta(minutes=5),
        notes="Another active outage",
    )

    return db


@pytest.mark.unit
@pytest.mark.database
class TestOutageTracking:
    """Test suite for outage tracking operations."""

    def test_create_outage_event(self, temp_db):
        """Test creating a new outage event."""
        db = Database(temp_db)
        now = datetime.now()

        event_id = db.create_outage_event(
            host_name="Test Host",
            host_address="10.0.0.1",
            start_time=now,
            notes="Test outage",
        )

        assert event_id is not None
        assert event_id > 0

        # Verify the outage was created
        active_outage = db.get_active_outage("10.0.0.1")
        assert active_outage is not None
        assert active_outage.host_name == "Test Host"
        assert active_outage.host_address == "10.0.0.1"
        assert active_outage.checks_failed == 1
        assert active_outage.end_time is None

    def test_get_active_outage(self, db_with_outages):
        """Test retrieving active outage for a host."""
        # Host with active outage
        outage = db_with_outages.get_active_outage("192.168.1.1")
        assert outage is not None
        assert outage.host_address == "192.168.1.1"
        assert outage.end_time is None

        # Host with no active outage (was closed)
        outage = db_with_outages.get_active_outage("192.168.1.2")
        assert outage is None

        # Host that doesn't exist
        outage = db_with_outages.get_active_outage("192.168.1.99")
        assert outage is None

    def test_update_outage_event(self, db_with_outages):
        """Test updating an ongoing outage event."""
        outage = db_with_outages.get_active_outage("192.168.1.1")
        assert outage is not None

        # Update the outage
        db_with_outages.update_outage_event(
            outage.id, checks_failed=5, checks_during_outage=5
        )

        # Verify update
        updated_outage = db_with_outages.get_active_outage("192.168.1.1")
        assert updated_outage.checks_failed == 5
        assert updated_outage.checks_during_outage == 5

    def test_close_outage_event(self, db_with_outages):
        """Test closing an outage event when host recovers."""
        outage = db_with_outages.get_active_outage("192.168.1.1")
        assert outage is not None

        end_time = datetime.now()
        db_with_outages.close_outage_event(
            outage.id,
            end_time=end_time,
            recovery_success_rate=95.0,
            notes="Host recovered",
        )

        # Verify outage is no longer active
        active_outage = db_with_outages.get_active_outage("192.168.1.1")
        assert active_outage is None

        # Verify the outage was properly closed
        all_outages = db_with_outages.get_outage_events(host_address="192.168.1.1")
        assert len(all_outages) == 1
        closed_outage = all_outages[0]
        assert closed_outage.end_time is not None
        assert closed_outage.recovery_success_rate == 95.0
        assert closed_outage.duration_seconds is not None
        assert closed_outage.duration_seconds > 0

    def test_close_outages_for_removed_hosts_empty_list(self, db_with_outages):
        """Test that providing an empty list doesn't close any outages."""
        # Get count of active outages before
        all_outages = db_with_outages.get_outage_events(active_only=True)
        initial_count = len(all_outages)
        assert initial_count == 3  # We created 3 active outages

        # Call with empty list - should not close any outages
        closed_count = db_with_outages.close_outages_for_removed_hosts([])
        assert closed_count == 0

        # Verify no outages were closed
        all_outages = db_with_outages.get_outage_events(active_only=True)
        assert len(all_outages) == initial_count

    def test_close_outages_for_removed_hosts_single_host(self, db_with_outages):
        """Test closing outages when only one host remains active."""
        # Keep only host 192.168.1.1 active
        active_hosts = ["192.168.1.1"]

        # Close outages for removed hosts
        closed_count = db_with_outages.close_outages_for_removed_hosts(active_hosts)

        # Should have closed 2 outages (192.168.1.3 and 192.168.1.4)
        assert closed_count == 2

        # Verify only host 1 has active outage
        outage_1 = db_with_outages.get_active_outage("192.168.1.1")
        assert outage_1 is not None

        outage_3 = db_with_outages.get_active_outage("192.168.1.3")
        assert outage_3 is None

        outage_4 = db_with_outages.get_active_outage("192.168.1.4")
        assert outage_4 is None

    def test_close_outages_for_removed_hosts_multiple_hosts(self, db_with_outages):
        """Test closing outages when some hosts are removed."""
        # Keep hosts 1 and 4 active, remove 3
        active_hosts = ["192.168.1.1", "192.168.1.4"]

        closed_count = db_with_outages.close_outages_for_removed_hosts(active_hosts)

        # Should have closed 1 outage (192.168.1.3)
        assert closed_count == 1

        # Verify correct outages remain active
        outage_1 = db_with_outages.get_active_outage("192.168.1.1")
        assert outage_1 is not None

        outage_3 = db_with_outages.get_active_outage("192.168.1.3")
        assert outage_3 is None

        outage_4 = db_with_outages.get_active_outage("192.168.1.4")
        assert outage_4 is not None

    def test_close_outages_for_removed_hosts_all_active(self, db_with_outages):
        """Test that no outages are closed when all hosts remain active."""
        # All hosts remain active
        active_hosts = ["192.168.1.1", "192.168.1.3", "192.168.1.4"]

        closed_count = db_with_outages.close_outages_for_removed_hosts(active_hosts)

        # Should have closed 0 outages
        assert closed_count == 0

        # Verify all outages remain active
        for host in active_hosts:
            outage = db_with_outages.get_active_outage(host)
            assert outage is not None

    def test_closed_outages_have_proper_notes(self, db_with_outages):
        """Test that closed outages for removed hosts have proper notes."""
        active_hosts = ["192.168.1.1"]

        db_with_outages.close_outages_for_removed_hosts(active_hosts)

        # Check that closed outages have the removal note
        all_outages = db_with_outages.get_outage_events(host_address="192.168.1.3")
        assert len(all_outages) == 1

        closed_outage = all_outages[0]
        assert closed_outage.end_time is not None
        assert closed_outage.notes is not None
        assert "removed from monitoring configuration" in closed_outage.notes

    def test_closed_outages_have_duration(self, db_with_outages):
        """Test that closed outages have calculated duration."""
        active_hosts = ["192.168.1.1"]

        db_with_outages.close_outages_for_removed_hosts(active_hosts)

        # Check that closed outages have duration calculated
        all_outages = db_with_outages.get_outage_events(host_address="192.168.1.3")
        assert len(all_outages) == 1

        closed_outage = all_outages[0]
        assert closed_outage.duration_seconds is not None
        assert closed_outage.duration_seconds > 0
        # Duration should be approximately 15 minutes (900 seconds)
        # Allow some tolerance for test execution time
        assert 800 < closed_outage.duration_seconds < 1000

    def test_multiple_calls_dont_reclose_outages(self, db_with_outages):
        """Test that calling close multiple times doesn't affect already closed outages."""
        active_hosts = ["192.168.1.1"]

        # First call should close 2 outages
        closed_count_1 = db_with_outages.close_outages_for_removed_hosts(active_hosts)
        assert closed_count_1 == 2

        # Second call should close 0 outages (already closed)
        closed_count_2 = db_with_outages.close_outages_for_removed_hosts(active_hosts)
        assert closed_count_2 == 0

    def test_outage_event_type_after_closure(self, db_with_outages):
        """Test that event_type changes to 'outage_end' after closure."""
        active_hosts = ["192.168.1.1"]

        db_with_outages.close_outages_for_removed_hosts(active_hosts)

        # Check event_type
        all_outages = db_with_outages.get_outage_events(host_address="192.168.1.3")
        assert len(all_outages) == 1

        closed_outage = all_outages[0]
        assert closed_outage.event_type == "outage_end"

    def test_no_recovery_success_rate_for_removed_hosts(self, db_with_outages):
        """Test that recovery_success_rate is None for hosts closed due to removal."""
        active_hosts = ["192.168.1.1"]

        db_with_outages.close_outages_for_removed_hosts(active_hosts)

        all_outages = db_with_outages.get_outage_events(host_address="192.168.1.3")
        closed_outage = all_outages[0]

        # Recovery success rate should be None since host was removed, not recovered
        assert closed_outage.recovery_success_rate is None
