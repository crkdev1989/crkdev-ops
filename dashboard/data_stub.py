from __future__ import annotations

from datetime import datetime, timedelta
from random import Random

from config import REVENUE_GOAL, REVENUE_WEEKS
from data_real import (
    get_chiro_quality_metrics,
    get_chiro_storage,
    get_k6_machine_health,
    read_checkpoint,
)

_rng = Random(42)
NICHES = ["chiro", "medspa", "pi_lawyers"]


def get_niche_statuses() -> list[dict]:
    now = datetime.now()
    chiro_checkpoint = read_checkpoint("chiro")
    chiro_quality = get_chiro_quality_metrics()
    chiro_processed = chiro_checkpoint.get("rows_processed", 0)
    chiro_expected = chiro_checkpoint.get("total_expected_rows", 150000) or 150000
    chiro_remaining = max(0, chiro_expected - chiro_processed)
    elapsed_human = chiro_checkpoint.get("elapsed_human")
    elapsed_minutes = 0
    if isinstance(elapsed_human, str):
        chunks = elapsed_human.split()
        for chunk in chunks:
            if chunk.endswith("d"):
                elapsed_minutes += int(chunk[:-1]) * 24 * 60
            elif chunk.endswith("h"):
                elapsed_minutes += int(chunk[:-1]) * 60
            elif chunk.endswith("m"):
                elapsed_minutes += int(chunk[:-1])
    return [
        {
            "name": "chiro",
            "total_records": chiro_expected,
            "last_scrape": chiro_checkpoint.get("last_scrape") or now.isoformat(timespec="seconds"),
            "status": chiro_checkpoint.get("status", "error"),
            "records_today": chiro_processed,
            "email_hit_rate": chiro_quality["email_hit_rate"],
            "dedup_rate": None,
            "email_breakdown": {
                "direct": chiro_quality["direct_pct"],
                "generic": chiro_quality["generic_pct"],
                "none": chiro_quality["none_pct"],
            },
            "records_per_min": chiro_checkpoint.get("rpm"),
            "remaining_records": chiro_remaining,
            "elapsed_minutes": elapsed_minutes,
            "elapsed_human": elapsed_human,
            "eta_minutes": chiro_checkpoint.get("eta_minutes"),
            "checkpoint": chiro_checkpoint,
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
    chiro_storage = get_chiro_storage()
    return {
        "total_gb": chiro_storage["total_gb"],
        "used_gb": chiro_storage["used_gb"],
        "free_gb": chiro_storage["free_gb"],
        "per_niche_gb": {"chiro": chiro_storage["chiro_dataset_gb"], "medspa": 281, "pi_lawyers": 409},
    }


def get_machine_health() -> dict:
    k6_health = get_k6_machine_health()
    return {
        "k6": k6_health,
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
