"""Streamlit dashboard for visualizing network connectivity monitoring data."""

from datetime import datetime, timedelta
from typing import Optional

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from config import Config
from database import Database


def create_status_indicator(success_rate: float) -> str:
    """Create a colored status indicator based on success rate.

    Args:
        success_rate: Success rate percentage (0-100).

    Returns:
        HTML string with colored status indicator.
    """
    if success_rate >= 95:
        color = "#28a745"  # Green
        status = "Healthy"
    elif success_rate >= 80:
        color = "#ffc107"  # Yellow
        status = "Degraded"
    else:
        color = "#dc3545"  # Red
        status = "Down"

    return f'<span style="color: {color}; font-weight: bold;">{status}</span>'


def format_latency(latency: Optional[float]) -> str:
    """Format latency value for display.

    Args:
        latency: Latency in milliseconds or None.

    Returns:
        Formatted latency string.
    """
    if latency is None:
        return "N/A"
    return f"{latency:.2f} ms"


def main():
    """Main dashboard application."""
    st.set_page_config(
        page_title="Network Connectivity Monitor",
        page_icon=":signal_strength:",
        layout="wide",
    )

    st.title("Network Connectivity Monitor")

    # Load configuration and database
    config = Config()
    db = Database(config.database_path)

    # Sidebar for filters
    st.sidebar.header("Filters")

    # Time range selector
    time_range = st.sidebar.selectbox(
        "Time Range",
        [
            "Last Hour",
            "Last 6 Hours",
            "Last 24 Hours",
            "Last 7 Days",
            "Last 30 Days",
            "All Time",
        ],
        index=2,  # Default to Last 24 Hours
    )

    # Calculate time range
    now = datetime.now()
    if time_range == "Last Hour":
        start_time = now - timedelta(hours=1)
    elif time_range == "Last 6 Hours":
        start_time = now - timedelta(hours=6)
    elif time_range == "Last 24 Hours":
        start_time = now - timedelta(days=1)
    elif time_range == "Last 7 Days":
        start_time = now - timedelta(days=7)
    elif time_range == "Last 30 Days":
        start_time = now - timedelta(days=30)
    else:  # All Time
        start_time = None

    # Host Status Overview
    st.header("Current Status")

    latest_results = db.get_latest_results()

    if not latest_results:
        st.warning("No data available. Start monitoring to see results.")
        return

    # Create status cards
    cols = st.columns(len(latest_results))

    for idx, result in enumerate(latest_results):
        with cols[idx]:
            st.subheader(result.host_name)
            st.markdown(
                create_status_indicator(result.success_rate), unsafe_allow_html=True
            )
            st.metric("Success Rate", f"{result.success_rate:.1f}%")
            st.metric("Avg Latency", format_latency(result.avg_latency))
            st.caption(f"Last check: {result.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")

    # Detailed Statistics
    st.header("Historical Data")

    # Host selector for detailed view
    host_options = {
        f"{result.host_name} ({result.host_address})": result.host_address
        for result in latest_results
    }
    selected_host_display = st.selectbox("Select Host", list(host_options.keys()))
    selected_host = host_options[selected_host_display]

    # Get historical data for selected host
    results = db.get_results(
        host_address=selected_host, start_time=start_time, end_time=now
    )

    if not results:
        st.warning(f"No data available for {selected_host_display} in selected time range.")
        return

    # Convert to DataFrame for easier plotting
    df = pd.DataFrame(
        [
            {
                "timestamp": r.timestamp,
                "success_rate": r.success_rate,
                "avg_latency": r.avg_latency,
                "min_latency": r.min_latency,
                "max_latency": r.max_latency,
            }
            for r in results
        ]
    )

    # Sort by timestamp
    df = df.sort_values("timestamp")

    # Create two columns for charts
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Success Rate Over Time")

        # Success rate chart
        fig_success = go.Figure()

        fig_success.add_trace(
            go.Scatter(
                x=df["timestamp"],
                y=df["success_rate"],
                mode="lines+markers",
                name="Success Rate",
                line=dict(color="#007bff", width=2),
                marker=dict(size=6),
            )
        )

        # Add threshold lines
        fig_success.add_hline(
            y=95, line_dash="dash", line_color="green", annotation_text="Healthy (95%)"
        )
        fig_success.add_hline(
            y=80,
            line_dash="dash",
            line_color="orange",
            annotation_text="Degraded (80%)",
        )

        fig_success.update_layout(
            yaxis_title="Success Rate (%)",
            xaxis_title="Time",
            hovermode="x unified",
            yaxis=dict(range=[0, 105]),
        )

        st.plotly_chart(fig_success, use_container_width=True)

    with col2:
        st.subheader("Latency Over Time")

        # Latency chart
        fig_latency = go.Figure()

        # Filter out None values for latency
        df_latency = df[df["avg_latency"].notna()].copy()

        if not df_latency.empty:
            fig_latency.add_trace(
                go.Scatter(
                    x=df_latency["timestamp"],
                    y=df_latency["avg_latency"],
                    mode="lines+markers",
                    name="Avg Latency",
                    line=dict(color="#28a745", width=2),
                    marker=dict(size=6),
                )
            )

            # Add min/max range
            fig_latency.add_trace(
                go.Scatter(
                    x=df_latency["timestamp"],
                    y=df_latency["max_latency"],
                    mode="lines",
                    name="Max Latency",
                    line=dict(color="rgba(40, 167, 69, 0.3)", width=0),
                    showlegend=False,
                )
            )

            fig_latency.add_trace(
                go.Scatter(
                    x=df_latency["timestamp"],
                    y=df_latency["min_latency"],
                    mode="lines",
                    name="Min Latency",
                    line=dict(color="rgba(40, 167, 69, 0.3)", width=0),
                    fill="tonexty",
                    fillcolor="rgba(40, 167, 69, 0.2)",
                    showlegend=False,
                )
            )

            fig_latency.update_layout(
                yaxis_title="Latency (ms)",
                xaxis_title="Time",
                hovermode="x unified",
            )

            st.plotly_chart(fig_latency, use_container_width=True)
        else:
            st.info("No latency data available (all pings failed).")

    # Statistics Summary
    st.header("Statistics Summary")

    stats = db.get_statistics(selected_host, start_time=start_time, end_time=now)

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Average Success Rate", f"{stats['avg_success_rate']:.1f}%")
        st.caption(f"Min: {stats['min_success_rate']:.1f}%")
        st.caption(f"Max: {stats['max_success_rate']:.1f}%")

    with col2:
        st.metric(
            "Average Latency",
            format_latency(stats["overall_avg_latency"]),
        )

    with col3:
        st.metric(
            "Min Latency",
            format_latency(stats["overall_min_latency"]),
        )

    with col4:
        st.metric(
            "Max Latency",
            format_latency(stats["overall_max_latency"]),
        )

    st.caption(f"Total checks: {stats['total_checks']}")

    # Outage Events Section
    st.header("Outage Events")

    # Get outage statistics
    outage_stats = db.get_outage_statistics(selected_host, start_time=start_time, end_time=now)

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Outages", outage_stats["total_outages"])

    with col2:
        st.metric("Active Outages", outage_stats["active_outages"])

    with col3:
        avg_duration = outage_stats["avg_duration_seconds"]
        if avg_duration > 0:
            if avg_duration >= 3600:
                duration_str = f"{avg_duration / 3600:.1f}h"
            elif avg_duration >= 60:
                duration_str = f"{avg_duration / 60:.1f}m"
            else:
                duration_str = f"{avg_duration:.0f}s"
        else:
            duration_str = "N/A"
        st.metric("Avg Outage Duration", duration_str)

    with col4:
        total_downtime = outage_stats["total_downtime_seconds"]
        if total_downtime > 0:
            if total_downtime >= 3600:
                downtime_str = f"{total_downtime / 3600:.1f}h"
            elif total_downtime >= 60:
                downtime_str = f"{total_downtime / 60:.1f}m"
            else:
                downtime_str = f"{total_downtime:.0f}s"
        else:
            downtime_str = "0s"
        st.metric("Total Downtime", downtime_str)

    # Show recent outage events
    st.subheader("Recent Outage Events")

    outage_events = db.get_outage_events(
        host_address=selected_host,
        start_time=start_time,
        end_time=now,
        limit=20
    )

    if outage_events:
        # Create DataFrame for outage events
        outage_data = []
        for event in outage_events:
            duration_str = "Ongoing"
            if event.duration_seconds:
                if event.duration_seconds >= 3600:
                    duration_str = f"{event.duration_seconds / 3600:.1f}h"
                elif event.duration_seconds >= 60:
                    duration_str = f"{event.duration_seconds / 60:.1f}m"
                else:
                    duration_str = f"{event.duration_seconds}s"

            outage_data.append({
                "Start Time": event.start_time.strftime("%Y-%m-%d %H:%M:%S"),
                "End Time": event.end_time.strftime("%Y-%m-%d %H:%M:%S") if event.end_time else "Ongoing",
                "Duration": duration_str,
                "Failed Checks": event.checks_failed,
                "Total Checks": event.checks_during_outage,
                "Recovery Rate": f"{event.recovery_success_rate:.1f}%" if event.recovery_success_rate else "N/A",
                "Status": "🟢 Resolved" if event.end_time else "🔴 Active"
            })

        outage_df = pd.DataFrame(outage_data)
        st.dataframe(outage_df, use_container_width=True, hide_index=True)
    else:
        st.info("No outage events in selected time range")

    # Success Rate Distribution
    st.subheader("Success Rate Distribution")

    # Create histogram of success rates
    fig_hist = px.histogram(
        df,
        x="success_rate",
        nbins=20,
        labels={"success_rate": "Success Rate (%)", "count": "Number of Checks"},
        color_discrete_sequence=["#007bff"],
    )

    fig_hist.update_layout(showlegend=False)

    st.plotly_chart(fig_hist, use_container_width=True)

    # Recent Data Table
    st.header("Recent Check Results")

    # Show last 20 results
    recent_df = df.tail(20).copy()
    recent_df = recent_df.sort_values("timestamp", ascending=False)

    # Format for display
    display_df = recent_df[
        ["timestamp", "success_rate", "avg_latency", "min_latency", "max_latency"]
    ].copy()

    display_df.columns = [
        "Timestamp",
        "Success Rate (%)",
        "Avg Latency (ms)",
        "Min Latency (ms)",
        "Max Latency (ms)",
    ]

    # Format numeric columns
    for col in display_df.columns[1:]:
        display_df[col] = display_df[col].apply(
            lambda x: f"{x:.2f}" if pd.notna(x) else "N/A"
        )

    st.dataframe(display_df, use_container_width=True, hide_index=True)

    # Auto-refresh option
    st.sidebar.header("Auto-refresh")
    auto_refresh = st.sidebar.checkbox("Enable auto-refresh", value=False)

    if auto_refresh:
        refresh_interval = st.sidebar.slider(
            "Refresh interval (seconds)", min_value=10, max_value=300, value=60
        )
        st.sidebar.info(f"Dashboard will refresh every {refresh_interval} seconds")
        # Use st.rerun with a timer
        import time

        time.sleep(refresh_interval)
        st.rerun()


if __name__ == "__main__":
    main()
