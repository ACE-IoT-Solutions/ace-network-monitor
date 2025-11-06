"""Network connectivity monitoring tool with ping statistics and dashboard."""

import subprocess
import sys

import click

from cleanup import CleanupJob
from config import Config
from database import Database
from monitor import PingMonitor


@click.group()
@click.version_option(version="0.1.0")
def cli():
    """Network Connectivity Monitor - Track network reliability with ping statistics."""
    pass


@cli.command()
@click.option(
    "--config",
    "-c",
    type=click.Path(),
    help="Path to configuration file",
)
@click.option(
    "--dashboard/--no-dashboard",
    default=True,
    help="Launch dashboard alongside monitoring (default: enabled)",
)
@click.option(
    "--dashboard-port",
    type=int,
    help="Port to run dashboard on (overrides config)",
)
@click.option(
    "--dashboard-host",
    type=str,
    help="Host to run dashboard on (overrides config)",
)
def monitor(config, dashboard, dashboard_port, dashboard_host):
    """Start continuous monitoring of configured hosts.

    By default, launches the dashboard alongside monitoring in an integrated mode.
    Use --no-dashboard to run monitoring only without the dashboard.
    """
    import threading
    import time

    cfg = Config(config)
    db = Database(cfg.database_path)
    mon = PingMonitor(cfg, db)

    if dashboard:
        # Start monitoring in background thread
        monitor_thread = threading.Thread(
            target=mon.run_continuous,
            daemon=True,
            name="MonitorThread"
        )
        monitor_thread.start()

        # Give monitoring a moment to start and do initial check
        time.sleep(2)

        # Launch dashboard in main thread (Streamlit expects this)
        dashboard_port_val = dashboard_port if dashboard_port else cfg.dashboard_port
        dashboard_host_val = dashboard_host if dashboard_host else cfg.dashboard_host

        cmd = [
            "streamlit",
            "run",
            "dashboard.py",
            "--server.port",
            str(dashboard_port_val),
            "--server.address",
            dashboard_host_val,
        ]

        click.echo(f"Starting integrated monitoring + dashboard on {dashboard_host_val}:{dashboard_port_val}...")
        click.echo("Press Ctrl+C to stop both monitoring and dashboard")

        try:
            subprocess.run(cmd)
        except KeyboardInterrupt:
            click.echo("\nMonitoring and dashboard stopped")
    else:
        # Run monitoring only (original behavior)
        mon.run_continuous()


@cli.command()
@click.option(
    "--config",
    "-c",
    type=click.Path(),
    help="Path to configuration file",
)
def check(config):
    """Perform a single check of all configured hosts."""
    cfg = Config(config)
    db = Database(cfg.database_path)
    mon = PingMonitor(cfg, db)

    results = mon.check_all_hosts()

    click.echo("\nSummary:")
    for result in results:
        status = (
            click.style("UP", fg="green")
            if result.success_rate >= 80
            else click.style("DOWN", fg="red")
        )
        click.echo(
            f"  {result.host_name} ({result.host_address}): {status} - "
            f"{result.success_rate:.1f}% success"
        )


@cli.command()
@click.option(
    "--config",
    "-c",
    type=click.Path(),
    help="Path to configuration file",
)
@click.option(
    "--port",
    "-p",
    type=int,
    help="Port to run dashboard on (overrides config)",
)
@click.option(
    "--host",
    "-h",
    type=str,
    help="Host to run dashboard on (overrides config)",
)
def dashboard(config, port, host):
    """Launch the Streamlit dashboard."""
    cfg = Config(config)

    # Use command line options if provided, otherwise use config
    dashboard_port = port if port else cfg.dashboard_port
    dashboard_host = host if host else cfg.dashboard_host

    # Build streamlit command
    cmd = [
        "streamlit",
        "run",
        "dashboard.py",
        "--server.port",
        str(dashboard_port),
        "--server.address",
        dashboard_host,
    ]

    click.echo(f"Starting dashboard on {dashboard_host}:{dashboard_port}...")
    click.echo("Press Ctrl+C to stop")

    try:
        subprocess.run(cmd)
    except KeyboardInterrupt:
        click.echo("\nDashboard stopped")


@cli.command()
@click.option(
    "--config",
    "-c",
    type=click.Path(),
    help="Path to configuration file",
)
def cleanup(config):
    """Run cleanup job to remove old records."""
    cfg = Config(config)
    db = Database(cfg.database_path)
    job = CleanupJob(cfg, db)

    deleted = job.run_cleanup()

    click.echo(f"Cleanup complete. {deleted} record(s) deleted.")


@cli.command()
@click.option(
    "--config",
    "-c",
    type=click.Path(),
    help="Path to configuration file",
)
@click.option(
    "--interval",
    "-i",
    type=int,
    default=24,
    help="Hours between cleanup runs (default: 24)",
)
def cleanup_continuous(config, interval):
    """Run cleanup job continuously."""
    cfg = Config(config)
    db = Database(cfg.database_path)
    job = CleanupJob(cfg, db)

    job.run_continuous(interval)


@cli.command()
@click.option(
    "--config",
    "-c",
    type=click.Path(),
    default="config.yaml",
    help="Path where config file will be created",
)
def init_config(config):
    """Create a default configuration file."""
    cfg = Config(config)
    cfg.save_default()

    click.echo(f"Default configuration saved to: {config}")
    click.echo("Edit this file to customize your monitoring settings.")


@cli.command()
@click.option(
    "--config",
    "-c",
    type=click.Path(),
    help="Path to configuration file",
)
def status(config):
    """Show current status of all monitored hosts."""
    cfg = Config(config)
    db = Database(cfg.database_path)

    latest_results = db.get_latest_results()

    if not latest_results:
        click.echo("No data available. Run monitoring to collect data.")
        return

    click.echo("\nCurrent Host Status:")
    click.echo("=" * 80)

    for result in latest_results:
        status_color = (
            "green" if result.success_rate >= 95 else "yellow" if result.success_rate >= 80 else "red"
        )

        click.echo(
            f"\n{click.style(result.host_name, bold=True)} ({result.host_address})"
        )
        click.echo(f"  Status: {click.style('●', fg=status_color)} {result.success_rate:.1f}% success")
        click.echo(
            f"  Latency: {result.avg_latency:.2f}ms (min: {result.min_latency:.2f}ms, max: {result.max_latency:.2f}ms)"
            if result.avg_latency
            else "  Latency: N/A (all pings failed)"
        )
        click.echo(f"  Last check: {result.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")


@cli.command()
@click.option(
    "--config",
    "-c",
    type=click.Path(),
    help="Path to configuration file",
)
@click.option(
    "--host",
    "-h",
    help="Filter events by host address",
)
@click.option(
    "--active",
    "-a",
    is_flag=True,
    help="Show only active (ongoing) outages",
)
@click.option(
    "--limit",
    "-l",
    type=int,
    default=50,
    help="Maximum number of events to display",
)
@click.option(
    "--days",
    "-d",
    type=int,
    help="Show events from last N days",
)
def events(config, host, active, limit, days):
    """Show outage event log with detailed information."""
    from datetime import datetime, timedelta

    cfg = Config(config)
    db = Database(cfg.database_path)

    # Calculate time range if days specified
    start_time = None
    if days:
        start_time = datetime.now() - timedelta(days=days)

    # Get outage events
    outage_events = db.get_outage_events(
        host_address=host,
        start_time=start_time,
        active_only=active,
        limit=limit
    )

    if not outage_events:
        click.echo("No outage events found.")
        return

    click.echo("\n" + "=" * 100)
    click.echo(f"{'OUTAGE EVENT LOG':^100}")
    click.echo("=" * 100)

    if active:
        click.echo(f"\n{click.style('Showing ACTIVE outages only', fg='red', bold=True)}")
    if days:
        click.echo(f"Time range: Last {days} days")
    if host:
        click.echo(f"Filtered by host: {host}")

    click.echo(f"\nTotal events: {len(outage_events)}")
    click.echo("-" * 100)

    for event in outage_events:
        # Format duration
        if event.duration_seconds:
            hours = event.duration_seconds // 3600
            minutes = (event.duration_seconds % 3600) // 60
            seconds = event.duration_seconds % 60

            if hours > 0:
                duration_str = f"{hours}h {minutes}m {seconds}s"
            elif minutes > 0:
                duration_str = f"{minutes}m {seconds}s"
            else:
                duration_str = f"{seconds}s"
        else:
            duration_str = click.style("ONGOING", fg="red", bold=True)

        # Status indicator
        if event.end_time:
            status = click.style("🟢 RESOLVED", fg="green")
        else:
            status = click.style("🔴 ACTIVE", fg="red", bold=True)

        # Event header
        click.echo(f"\n{status} | Event ID: {event.id}")
        click.echo(f"Host: {click.style(event.host_name, bold=True)} ({event.host_address})")
        click.echo(f"Started: {event.start_time.strftime('%Y-%m-%d %H:%M:%S')}")

        if event.end_time:
            click.echo(f"Ended:   {event.end_time.strftime('%Y-%m-%d %H:%M:%S')}")
            click.echo(f"Duration: {duration_str}")
            click.echo(f"Recovery success rate: {event.recovery_success_rate:.1f}%")
        else:
            # Calculate ongoing duration
            ongoing_duration = (datetime.now() - event.start_time).total_seconds()
            ongoing_hours = int(ongoing_duration // 3600)
            ongoing_minutes = int((ongoing_duration % 3600) // 60)
            if ongoing_hours > 0:
                ongoing_str = f"{ongoing_hours}h {ongoing_minutes}m"
            else:
                ongoing_str = f"{ongoing_minutes}m"
            click.echo(f"Duration: {duration_str} ({ongoing_str} so far)")

        click.echo(f"Failed checks: {event.checks_failed} / {event.checks_during_outage}")

        if event.notes:
            click.echo(f"Notes: {event.notes}")

        click.echo("-" * 100)

    # Show outage statistics summary
    click.echo("\n" + "=" * 100)
    click.echo("STATISTICS SUMMARY")
    click.echo("=" * 100)

    # Get statistics for each host
    hosts = set(event.host_address for event in outage_events)

    for host_addr in hosts:
        stats = db.get_outage_statistics(host_addr, start_time=start_time)

        # Find host name
        host_name = next((e.host_name for e in outage_events if e.host_address == host_addr), host_addr)

        click.echo(f"\n{click.style(host_name, bold=True)} ({host_addr}):")
        click.echo(f"  Total outages: {stats['total_outages']}")
        click.echo(f"  Active outages: {stats['active_outages']}")

        if stats['avg_duration_seconds'] > 0:
            avg_mins = stats['avg_duration_seconds'] / 60
            click.echo(f"  Average outage duration: {avg_mins:.1f} minutes")

        if stats['total_downtime_seconds'] > 0:
            total_hours = stats['total_downtime_seconds'] / 3600
            click.echo(f"  Total downtime: {total_hours:.2f} hours")

    click.echo("\n" + "=" * 100)


def main():
    """Main entry point."""
    cli()


if __name__ == "__main__":
    main()
