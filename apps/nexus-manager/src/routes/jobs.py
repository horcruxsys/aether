"""Ingestion job tracking routes."""

from fastapi import APIRouter
from typing import List
from pydantic import BaseModel
from datetime import datetime

router = APIRouter()

class IngestionJob(BaseModel):
    job_id: str
    source_urn: str
    status: str  # RUNNING, COMPLETED, FAILED
    processed_count: int
    pii_masked_count: int
    timestamp: str

class JobsListResponse(BaseModel):
    active_jobs: List[IngestionJob]
    total_processed: int

# In-memory job tracking (will be injected/shared with main.py)
_active_jobs: dict = {}

def get_active_jobs() -> dict:
    """Get the active jobs dictionary (will be shared from main.py)."""
    from main import _active_jobs as main_jobs
    return main_jobs

@router.get("/internal/jobs", response_model=JobsListResponse)
async def list_jobs():
    """List all active ingestion jobs."""
    try:
        jobs_dict = get_active_jobs()

        active = [
            IngestionJob(
                job_id=job_id,
                source_urn=job.get("source_urn", "unknown"),
                status=job.get("status", "RUNNING"),
                processed_count=job.get("processed_count", 0),
                pii_masked_count=job.get("pii_masked_count", 0),
                timestamp=job.get("timestamp", datetime.utcnow().isoformat())
            )
            for job_id, job in jobs_dict.items()
        ]

        total = sum(j.processed_count for j in active)

        return JobsListResponse(
            active_jobs=active,
            total_processed=total
        )
    except Exception as e:
        print(f"[Jobs Routes] Error listing jobs: {e}")
        return JobsListResponse(
            active_jobs=[],
            total_processed=0
        )
