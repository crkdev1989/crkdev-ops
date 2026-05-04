from __future__ import annotations

from datetime import datetime, timedelta
from random import Random

from config import REVENUE_GOAL, REVENUE_WEEKS

_rng = Random(42)
NICHES = ["chiro", "medspa", "pi_lawyers"]


def get_niche_statuses() -> list[dict]:
    now = datetime.now()
    # STUB: realistic fake niche status payload
    return [
        {
            "name": "chiro",
            "total_records": 126_450,
            "last_scrape": (now - timedelta(minutes=5)).isoformat(timespec="seconds"),
            "status": "running",
            "records_today": 8450,
            "email_hit_rate": 62.3,
            "dedup_rate": 18.1,
            "email_breakdown": {"direct": 51, "generic": 11, "none": 38},
            "records_per_min": 112,
            "remaining_records": 1540,
            "elapsed_minutes": 74,
        },
        {
            "name": "medspa",
            "total_records": 98_201,
            "last_scrape": (now - timedelta(minutes=22)).isoformat(timespec="seconds"),
            "status": "idle",
            "records_today": 3210,
            "email_hit_rate": 58.6,
            "dedup_rate": 20.2,
            "email_breakdown": {"direct": 47, "generic": 12, "none": 41},
            "records_per_min": 0,
            "remaining_records": 0,
            "elapsed_minutes": 0,
        },
        {
            "name": "pi_lawyers",
            "total_records": 143_903,
            "last_scrape": (now - timedelta(minutes=16)).isoformat(timespec="seconds"),
            "status": "hung",
            "records_today": 6770,
            "email_hit_rate": 55.2,
            "dedup_rate": 15.7,
            "email_breakdown": {"direct": 44, "generic": 11, "none": 45},
            "records_per_min": 18,
            "remaining_records": 2100,
            "elapsed_minutes": 96,
        },
    ]


def get_storage_monitor() -> dict:
    # STUB: fake storage usage values
    return {
        "total_gb": 2000,
        "used_gb": 1286,
        "free_gb": 714,
        "per_niche_gb": {"chiro": 322, "medspa": 281, "pi_lawyers": 409},
    }


def get_machine_health() -> dict:
    # STUB: fake health telemetry
    return {
        "k6": {"cpu": 36, "ram": 54, "disk": 68, "status": "healthy"},
        "pi": {"cpu": 29, "ram": 43, "disk": 41, "status": "healthy"},
        "hetzner": {"cpu": 71, "ram": 64, "disk": 52, "status": "idle"},
    }


def get_hetzner_enrichment_status() -> dict:
    # STUB: fake enrichment status
    return {"email_hit_rate": 61.8, "queue_depth": 382, "last_run": "2026-05-04T13:48:00"}


def get_sales_snapshot() -> dict:
    # STUB: fake Gumroad totals
    return {"today": 74.0, "week": 512.0, "month": 1830.0, "sales_count": 27}


def get_pipeline_points() -> list[int]:
    # STUB: random walk for 60-minute chart
    points = []
    value = 70
    for _ in range(60):
        value = max(10, min(170, value + _rng.randint(-12, 12)))
        points.append(value)
    return points


def get_stage_breakdown() -> list[dict]:
    # STUB: stage statuses
    return [
        {"name": "scrape", "status": "running"},
        {"name": "enrich", "status": "idle"},
        {"name": "clean", "status": "idle"},
        {"name": "package", "status": "idle"},
    ]


def get_run_history() -> list[dict]:
    # STUB: fake run history
    now = datetime.now()
    rows = []
    for i in range(10):
        rows.append(
            {
                "date": (now - timedelta(days=i)).strftime("%Y-%m-%d"),
                "records": 10_000 + i * 137,
                "duration": f"{70 + i}m",
                "status": "success" if i % 4 else "partial",
            }
        )
    return rows


def default_revenue_state() -> dict:
    weekly_target = round(REVENUE_GOAL / REVENUE_WEEKS, 2)
    # STUB: initial revenue state
    return {
        "earned_total": 940.0,
        "goal": REVENUE_GOAL,
        "weeks_total": REVENUE_WEEKS,
        "weeks_elapsed": 8,
        "weekly_target": weekly_target,
    }
