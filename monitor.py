"""Ping monitoring module for network connectivity checks."""

import platform
import re
import subprocess
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List

from config import Config
from database import Database, PingResult


@dataclass
class PingStats:
    """Statistics from a ping operation."""

    success_count: int
    failure_count: int
    min_latency: Optional[float]
    max_latency: Optional[float]
    avg_latency: Optional[float]

    @property
    def success_rate(self) -> float:
        """Calculate success rate as percentage.

        Returns:
            Success rate between 0.0 and 100.0.
        """
        total = self.success_count + self.failure_count
        if total == 0:
            return 0.0
        return (self.success_count / total) * 100.0


class PingMonitor:
    """Monitors network connectivity using ICMP ping."""

    def __init__(self, config: Config, database: Database):
        """Initialize ping monitor.

        Args:
            config: Configuration object.
            database: Database object for storing results.
        """
        self.config = config
        self.database = database
        self.is_windows = platform.system().lower() == "windows"

    def ping_host(self, host_address: str, count: int, timeout: int) -> PingStats:
        """Ping a host and collect statistics.

        Args:
            host_address: IP address or hostname to ping.
            count: Number of ping packets to send.
            timeout: Timeout in seconds for each ping.

        Returns:
            PingStats object with results.
        """
        try:
            # Build ping command based on OS
            if self.is_windows:
                cmd = [
                    "ping",
                    "-n",
                    str(count),
                    "-w",
                    str(timeout * 1000),  # Windows uses milliseconds
                    host_address,
                ]
            else:
                # Unix-like systems (Linux, macOS)
                cmd = [
                    "ping",
                    "-c",
                    str(count),
                    "-W",
                    str(timeout),
                    host_address,
                ]

            # Execute ping command
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout * count + 5,  # Add buffer for command execution
            )

            # Parse output
            return self._parse_ping_output(result.stdout, result.returncode, count)

        except subprocess.TimeoutExpired:
            # All pings timed out
            return PingStats(
                success_count=0,
                failure_count=count,
                min_latency=None,
                max_latency=None,
                avg_latency=None,
            )
        except Exception as e:
            print(f"Error pinging {host_address}: {e}")
            return PingStats(
                success_count=0,
                failure_count=count,
                min_latency=None,
                max_latency=None,
                avg_latency=None,
            )

    def _parse_ping_output(
        self, output: str, return_code: int, expected_count: int
    ) -> PingStats:
        """Parse ping command output to extract statistics.

        Args:
            output: Raw output from ping command.
            return_code: Return code from ping command.
            expected_count: Expected number of pings sent.

        Returns:
            PingStats object with parsed results.
        """
        # Initialize counters
        success_count = 0
        failure_count = 0
        latencies: list[float] = []

        if self.is_windows:
            # Parse Windows ping output
            # Look for "Reply from" lines with time
            reply_pattern = re.compile(r"Reply from .+ time[=<](\d+)ms", re.IGNORECASE)
            for match in reply_pattern.finditer(output):
                success_count += 1
                latency = float(match.group(1))
                latencies.append(latency)

            # Look for failure indicators
            failure_patterns = [
                r"Request timed out",
                r"Destination host unreachable",
                r"could not find host",
            ]
            for pattern in failure_patterns:
                failure_count += len(re.findall(pattern, output, re.IGNORECASE))

        else:
            # Parse Unix ping output
            # Try to extract packet loss statistics first
            loss_pattern = re.compile(
                r"(\d+) packets transmitted, (\d+)(?:\s+packets)?\s+received",
                re.IGNORECASE,
            )
            loss_match = loss_pattern.search(output)
            if loss_match:
                transmitted = int(loss_match.group(1))
                received = int(loss_match.group(2))
                success_count = received
                failure_count = transmitted - received

            # Extract latency statistics
            # macOS format: round-trip min/avg/max/stddev = 7.270/8.087/8.904/0.817 ms
            mac_stats_pattern = re.compile(
                r"round-trip\s+min/avg/max/stddev\s*=\s*(\d+\.?\d*)/(\d+\.?\d*)/(\d+\.?\d*)",
                re.IGNORECASE,
            )
            mac_match = mac_stats_pattern.search(output)
            if mac_match:
                min_latency = float(mac_match.group(1))
                avg_latency = float(mac_match.group(2))
                max_latency = float(mac_match.group(3))
                # Store parsed values directly
                latencies = [min_latency, avg_latency, max_latency]
            else:
                # Linux format: time=7.27 ms
                time_pattern = re.compile(r"time[=<](\d+\.?\d*)\s*ms", re.IGNORECASE)
                for match in time_pattern.finditer(output):
                    latency = float(match.group(1))
                    latencies.append(latency)

        # If we couldn't parse packet counts, use expected count
        if success_count + failure_count == 0:
            if return_code == 0:
                # Command succeeded but no replies parsed
                success_count = expected_count
            else:
                # Command failed
                failure_count = expected_count

        # Calculate statistics
        if latencies:
            # Check if we already parsed min/avg/max from macOS output
            if len(latencies) == 3 and not self.is_windows:
                # macOS pre-calculated stats: [min, avg, max]
                min_latency = latencies[0]
                avg_latency = latencies[1]
                max_latency = latencies[2]
            else:
                # Calculate from individual measurements
                min_latency = min(latencies)
                max_latency = max(latencies)
                avg_latency = sum(latencies) / len(latencies)
        else:
            min_latency = None
            max_latency = None
            avg_latency = None

        return PingStats(
            success_count=success_count,
            failure_count=failure_count,
            min_latency=min_latency,
            max_latency=max_latency,
            avg_latency=avg_latency,
        )

    def check_host(self, host_name: str, host_address: str) -> PingResult:
        """Perform a ping check on a host and store the result.

        Args:
            host_name: Human-readable name for the host.
            host_address: IP address or hostname to ping.

        Returns:
            PingResult object with check results.
        """
        timestamp = datetime.now()

        # Perform ping
        stats = self.ping_host(
            host_address,
            self.config.ping_count,
            self.config.ping_timeout,
        )

        # Create result object
        result = PingResult(
            host_name=host_name,
            host_address=host_address,
            timestamp=timestamp,
            success_count=stats.success_count,
            failure_count=stats.failure_count,
            success_rate=stats.success_rate,
            min_latency=stats.min_latency,
            max_latency=stats.max_latency,
            avg_latency=stats.avg_latency,
        )

        return result

    def check_all_hosts(self) -> List[PingResult]:
        """Check all configured hosts and track outage events.

        Returns:
            List of PingResult objects for all hosts.
        """
        results = []

        # Close any active outages for hosts that are no longer in the config
        active_addresses = [host["address"] for host in self.config.hosts]
        self.database.close_outages_for_removed_hosts(active_addresses)

        for host in self.config.hosts:
            host_name = host["name"]
            host_address = host["address"]

            print(f"Checking {host_name} ({host_address})...")

            result = self.check_host(host_name, host_address)
            results.append(result)

            # Store result in database
            try:
                self.database.insert_result(result)

                # Track outage events
                self._track_outage_event(result)

                print(
                    f"  Success rate: {result.success_rate:.1f}%, "
                    f"Avg latency: {result.avg_latency:.1f}ms"
                    if result.avg_latency
                    else f"  Success rate: {result.success_rate:.1f}%, No responses"
                )
            except Exception as e:
                print(f"  Error storing result: {e}")

        return results

    def _track_outage_event(self, result: PingResult) -> None:
        """Track outage events based on ping results.

        Args:
            result: PingResult to analyze for outage tracking.
        """
        # Check if host is currently down (0% success rate)
        is_down = result.success_rate == 0.0

        # Check for active outage
        active_outage = self.database.get_active_outage(result.host_address)

        if is_down:
            # Host is down
            if active_outage:
                # Ongoing outage - update counters
                active_outage.checks_failed += 1
                active_outage.checks_during_outage += 1
                self.database.update_outage_event(
                    active_outage.id,
                    checks_failed=active_outage.checks_failed,
                    checks_during_outage=active_outage.checks_during_outage,
                )
                print(
                    f"  ⚠️  Outage continues ({active_outage.checks_failed} failed checks)"
                )
            else:
                # New outage detected
                event_id = self.database.create_outage_event(
                    result.host_name,
                    result.host_address,
                    result.timestamp,
                    notes=f"Outage detected at {result.timestamp.strftime('%Y-%m-%d %H:%M:%S')}",
                )
                print(f"  🔴 OUTAGE STARTED (Event ID: {event_id})")
        else:
            # Host is up (at least partially)
            if active_outage:
                # Host recovered from outage
                self.database.close_outage_event(
                    active_outage.id,
                    result.timestamp,
                    result.success_rate,
                    notes=f"Recovered at {result.timestamp.strftime('%Y-%m-%d %H:%M:%S')} with {result.success_rate:.1f}% success rate",
                )

                # Calculate and display outage duration
                duration = (result.timestamp - active_outage.start_time).total_seconds()
                minutes = int(duration // 60)
                seconds = int(duration % 60)

                if minutes > 0:
                    duration_str = f"{minutes}m {seconds}s"
                else:
                    duration_str = f"{seconds}s"

                print(
                    f"  🟢 RECOVERED from outage (Duration: {duration_str}, {active_outage.checks_failed} failed checks)"
                )
            # else: Host is up and no active outage - normal operation

    def run_continuous(self) -> None:
        """Run monitoring continuously at configured interval.

        This method runs indefinitely, checking all hosts at the configured interval.
        Use Ctrl+C to stop.
        """
        import schedule
        import time

        # Schedule the monitoring job
        schedule.every(self.config.monitoring_interval).seconds.do(self.check_all_hosts)

        print(
            f"Starting continuous monitoring (interval: {self.config.monitoring_interval}s)"
        )
        print("Press Ctrl+C to stop")

        # Run initial check immediately
        self.check_all_hosts()

        # Run scheduled jobs
        try:
            while True:
                schedule.run_pending()
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nMonitoring stopped")
