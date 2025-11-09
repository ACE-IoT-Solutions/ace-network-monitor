"""FastAPI backend for network monitoring dashboard."""

import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

from config import Config
from database import Database, PingResult, OutageEvent


# Pydantic models for API responses
class PingResultResponse(BaseModel):
    host_name: str
    host_address: str
    timestamp: datetime
    success_count: int
    failure_count: int
    success_rate: float
    min_latency: Optional[float]
    max_latency: Optional[float]
    avg_latency: Optional[float]

    class Config:
        from_attributes = True


class OutageEventResponse(BaseModel):
    id: Optional[int]
    host_name: str
    host_address: str
    event_type: str
    start_time: datetime
    end_time: Optional[datetime]
    duration_seconds: Optional[int]
    checks_failed: int
    checks_during_outage: int
    recovery_success_rate: Optional[float]
    notes: Optional[str]

    class Config:
        from_attributes = True


class HostStatistics(BaseModel):
    avg_success_rate: float
    min_success_rate: float
    max_success_rate: float
    overall_avg_latency: float
    overall_min_latency: float
    overall_max_latency: float
    total_checks: int


class OutageStatistics(BaseModel):
    total_outages: int
    active_outages: int
    avg_duration_seconds: float
    max_duration_seconds: int
    total_downtime_seconds: int


class HostInfo(BaseModel):
    name: str
    address: str


class SystemStatus(BaseModel):
    hosts: List[HostInfo]
    total_hosts: int
    monitoring_interval: int
    database_path: str


# Initialize FastAPI app
app = FastAPI(
    title="ACE Connection Logger API",
    description="Network connectivity monitoring API with outage tracking",
    version="0.2.0"
)

# CORS middleware for Vue.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global config and database
config: Optional[Config] = None
db: Optional[Database] = None


def get_db() -> Database:
    """Get database instance."""
    global db, config
    if db is None:
        if config is None:
            config = Config()
        db = Database(config.database_path)
    return db


def get_config() -> Config:
    """Get config instance."""
    global config
    if config is None:
        config = Config()
    return config


# API Endpoints

@app.get("/api/status")
async def get_status() -> SystemStatus:
    """Get system status and configuration."""
    cfg = get_config()
    return SystemStatus(
        hosts=[HostInfo(name=h["name"], address=h["address"]) for h in cfg.hosts],
        total_hosts=len(cfg.hosts),
        monitoring_interval=cfg.monitoring_interval,
        database_path=cfg.database_path
    )


@app.get("/api/ping-results/latest", response_model=List[PingResultResponse])
async def get_latest_results():
    """Get latest ping result for each host."""
    database = get_db()
    results = database.get_latest_results()
    return [PingResultResponse.from_orm(r) for r in results]


@app.get("/api/ping-results", response_model=List[PingResultResponse])
async def get_ping_results(
    host_address: Optional[str] = None,
    hours: Optional[int] = 24,
    limit: Optional[int] = 1000
):
    """Get ping results with optional filtering."""
    database = get_db()

    start_time = None
    if hours:
        start_time = datetime.now() - timedelta(hours=hours)

    results = database.get_results(
        host_address=host_address,
        start_time=start_time,
        limit=limit
    )
    return [PingResultResponse.from_orm(r) for r in results]


@app.get("/api/statistics/{host_address}", response_model=HostStatistics)
async def get_host_statistics(
    host_address: str,
    hours: Optional[int] = 24
):
    """Get statistics for a specific host."""
    database = get_db()

    start_time = None
    if hours:
        start_time = datetime.now() - timedelta(hours=hours)

    stats = database.get_statistics(host_address, start_time=start_time)
    return HostStatistics(**stats)


@app.get("/api/outages", response_model=List[OutageEventResponse])
async def get_outage_events(
    host_address: Optional[str] = None,
    active_only: bool = False,
    days: Optional[int] = None,
    limit: int = 50
):
    """Get outage events with optional filtering."""
    database = get_db()

    start_time = None
    if days:
        start_time = datetime.now() - timedelta(days=days)

    events = database.get_outage_events(
        host_address=host_address,
        start_time=start_time,
        active_only=active_only,
        limit=limit
    )
    return [OutageEventResponse.from_orm(e) for e in events]


@app.get("/api/outages/active", response_model=List[OutageEventResponse])
async def get_active_outages():
    """Get all currently active outages."""
    database = get_db()
    events = database.get_outage_events(active_only=True)
    return [OutageEventResponse.from_orm(e) for e in events]


@app.get("/api/outages/statistics/{host_address}", response_model=OutageStatistics)
async def get_outage_statistics(
    host_address: str,
    days: Optional[int] = None
):
    """Get outage statistics for a specific host."""
    database = get_db()

    start_time = None
    if days:
        start_time = datetime.now() - timedelta(days=days)

    stats = database.get_outage_statistics(host_address, start_time=start_time)
    return OutageStatistics(**stats)


@app.get("/api/hosts")
async def get_hosts():
    """Get list of all monitored hosts."""
    cfg = get_config()
    return [HostInfo(name=h["name"], address=h["address"]) for h in cfg.hosts]


@app.get("/api/hosts/{host_address}/active-outage")
async def get_host_active_outage(host_address: str):
    """Get active outage for a specific host."""
    database = get_db()
    outage = database.get_active_outage(host_address)
    if outage:
        return OutageEventResponse.from_orm(outage)
    return None


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    try:
        database = get_db()
        # Simple query to verify database is accessible
        database.get_host_addresses()
        return {"status": "healthy", "timestamp": datetime.now().isoformat()}
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Database error: {str(e)}")


# Serve static files (built Vue.js frontend)
# This should be mounted AFTER all API routes
frontend_dist = Path(__file__).parent / "frontend" / "dist"
if frontend_dist.exists():
    # Mount static assets (js, css, etc)
    app.mount("/assets", StaticFiles(directory=str(frontend_dist / "assets")), name="assets")

    # Catch-all route for Vue.js SPA routing
    # This must be the LAST route defined
    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        """Serve Vue.js SPA for all non-API routes."""
        # Don't serve for API routes
        if full_path.startswith("api/"):
            raise HTTPException(status_code=404, detail="Not found")

        # Serve index.html for all other routes (SPA routing)
        index_file = frontend_dist / "index.html"
        if index_file.exists():
            return FileResponse(index_file)

        raise HTTPException(status_code=404, detail="Frontend not built. Run: cd frontend && npm run build")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
