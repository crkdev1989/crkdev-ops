from __future__ import annotations

from datetime import datetime, timedelta
from random import Random

from config import REVENUE_GOAL, REVENUE_WEEKS
from data_real import (
    format_last_scrape_display,
    get_chiro_quality_metrics,
    get_k6_machine_health,
    get_storage_monitor as build_storage_monitor,
    read_avvo_checkpoints,
    read_checkpoint,
    read_medspa_checkpoint,
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

    medspa = read_medspa_checkpoint()
    mq = medspa["quality"]
    mcounts = mq["email_breakdown_counts"]

    avvo = read_avvo_checkpoints()
    pq = avvo["quality"]
    pcounts = pq["email_breakdown_counts"]

    return [
        {
            "name": "chiro",
            "total_records": chiro_expected,
            "last_scrape": chiro_checkpoint.get("last_scrape") or now.isoformat(timespec="seconds"),
            "last_scrape_display": format_last_scrape_display(
                chiro_checkpoint.get("last_scrape") or now.isoformat(timespec="seconds")
            ),
            "status": chiro_checkpoint.get("status", "error"),
            "records_today": chiro_processed,
            "email_hit_rate": chiro_quality["email_hit_rate"],
            "dedup_rate": None,
            "dedup_na": False,
            "email_breakdown": {
                "direct": chiro_quality["direct_pct"],
                "generic": chiro_quality["generic_pct"],
                "none": chiro_quality["none_pct"],
            },
            "email_breakdown_suffix": "%",
            "records_per_min": chiro_checkpoint.get("rpm"),
            "remaining_records": chiro_remaining,
            "elapsed_minutes": elapsed_minutes,
            "elapsed_human": elapsed_human,
            "eta_minutes": chiro_checkpoint.get("eta_minutes"),
            "checkpoint": chiro_checkpoint,
        },
        {
            "name": "medspa",
            "total_records": mq["total_records"],
            "last_scrape": medspa.get("last_scrape") or now.isoformat(timespec="seconds"),
            "last_scrape_display": format_last_scrape_display(medspa.get("last_scrape")),
            "status": medspa.get("status", "idle"),
            "records_today": medspa.get("records_count", 0),
            "email_hit_rate": mq["email_hit_rate"],
            "dedup_rate": mq["dedup_rate"],
            "dedup_na": mq["dedup_na"],
            "email_breakdown": {
                "direct": mcounts["direct"],
                "generic": mcounts["generic"],
                "none": mcounts["none"],
            },
            "email_breakdown_suffix": "",
            "records_per_min": None,
            "remaining_records": medspa.get("remaining_records", 0),
            "elapsed_minutes": 0,
            "checkpoint": medspa,
        },
        {
            "name": "pi_lawyers",
            "total_records": pq["total_records"],
            "last_scrape": avvo.get("last_scrape") or now.isoformat(timespec="seconds"),
            "last_scrape_display": format_last_scrape_display(avvo.get("last_scrape")),
            "status": "idle",
            "records_today": avvo.get("total_records_summed", 0),
            "email_hit_rate": pq["email_hit_rate"],
            "dedup_rate": None,
            "dedup_na": pq["dedup_na"],
            "email_breakdown": {
                "direct": pcounts["direct"],
                "generic": pcounts["generic"],
                "none": pcounts["none"],
            },
            "email_breakdown_suffix": "",
            "records_per_min": None,
            "remaining_records": 0,
            "elapsed_minutes": 0,
            "checkpoint": avvo,
        },
    ]


def get_storage_monitor() -> dict:
    return build_storage_monitor()


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
