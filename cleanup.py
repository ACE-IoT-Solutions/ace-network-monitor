"""Cleanup job for removing old records from the database."""

from config import Config
from database import Database


class CleanupJob:
    """Manages cleanup of old database records."""

    def __init__(self, config: Config, database: Database):
        """Initialize cleanup job.

        Args:
            config: Configuration object.
            database: Database object.
        """
        self.config = config
        self.database = database

    def run_cleanup(self) -> int:
        """Run cleanup job to remove old records.

        Returns:
            Number of records deleted.
        """
        retention_days = self.config.retention_days

        print(f"Running cleanup job (retention: {retention_days} days)...")

        deleted_count = self.database.cleanup_old_records(retention_days)

        if deleted_count > 0:
            print(f"Deleted {deleted_count} old record(s)")
        else:
            print("No old records to delete")

        return deleted_count

    def run_continuous(self, interval_hours: int = 24) -> None:
        """Run cleanup job continuously at specified interval.

        Args:
            interval_hours: Hours between cleanup runs (default: 24).

        This method runs indefinitely, performing cleanup at the specified interval.
        Use Ctrl+C to stop.
        """
        import schedule
        import time

        # Schedule the cleanup job
        schedule.every(interval_hours).hours.do(self.run_cleanup)

        print(
            f"Starting continuous cleanup (interval: {interval_hours} hours, "
            f"retention: {self.config.retention_days} days)"
        )
        print("Press Ctrl+C to stop")

        # Run initial cleanup immediately
        self.run_cleanup()

        # Run scheduled jobs
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
        except KeyboardInterrupt:
            print("\nCleanup job stopped")


def main():
    """Main entry point for running cleanup as standalone script."""
    config = Config()
    db = Database(config.database_path)
    cleanup = CleanupJob(config, db)

    # Run cleanup once
    cleanup.run_cleanup()


if __name__ == "__main__":
    main()
