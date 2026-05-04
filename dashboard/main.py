from __future__ import annotations

import json
from datetime import datetime

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from config import BASE_DIR, DASHBOARD_PORT, PIPELINE_SCHEDULE, REVENUE_GOAL, REVENUE_WEEKS, STATE_FILES
from data_stub import (
    NICHES,
    default_revenue_state,
    get_hetzner_enrichment_status,
    get_machine_health,
    get_niche_statuses,
    get_sales_snapshot,
    get_storage_monitor,
)
from routers.api import router as api_router
from routers.scraper import router as scraper_router

app = FastAPI(title="CRK Dev Ops Dashboard")
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")
app.include_router(api_router)
app.include_router(scraper_router)


def _seed_state_files():
    defaults = {
        "queue": {"items": ["medspa", "pi_lawyers"]},
        "warmup": {
            "accounts": [
                {"account": "outreach.crkdev.com", "days_warmed": 24, "daily_volume": 35, "status": "healthy"},
                {"account": "craig@crkdev.com", "days_warmed": 18, "daily_volume": 28, "status": "ramping"},
            ]
        },
        "outreach": {
            "targets": [
                {"company": "HydraFacial", "sent_date": "2026-05-01", "follow_up_due": "2026-05-05", "status": "sent"},
                {"company": "InMode", "sent_date": "2026-04-29", "follow_up_due": "2026-05-04", "status": "followed up"},
                {"company": "Merz", "sent_date": "2026-04-27", "follow_up_due": "2026-05-02", "status": "replied"},
            ]
        },
        "listings": {
            "chiro": {"Gumroad": True, "Datarade": False, "Fiverr": True, "Instantly": False, "Apollo": True},
            "medspa": {"Gumroad": True, "Datarade": True, "Fiverr": False, "Instantly": False, "Apollo": False},
            "pi_lawyers": {"Gumroad": True, "Datarade": False, "Fiverr": False, "Instantly": True, "Apollo": True},
        },
        "revenue": default_revenue_state(),
    }
    for key, path in STATE_FILES.items():
        if not path.exists():
            path.write_text(json.dumps(defaults[key], indent=2), encoding="utf-8")


def _load_state(key: str):
    path = STATE_FILES[key]
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _dashboard_payload():
    niches = get_niche_statuses()
    active = [n for n in niches if n["status"] == "running"]
    queue_state = _load_state("queue")
    warmup = _load_state("warmup")
    outreach = _load_state("outreach")
    listings = _load_state("listings")
    revenue = _load_state("revenue") or default_revenue_state()
    total_earned = float(revenue.get("earned_total", 0))
    goal = float(revenue.get("goal", REVENUE_GOAL))
    weeks_total = int(revenue.get("weeks_total", REVENUE_WEEKS))
    weeks_elapsed = int(revenue.get("weeks_elapsed", 1))
    weeks_remaining = max(0, weeks_total - weeks_elapsed)
    pace_required = (goal - total_earned) / max(1, weeks_remaining) if weeks_remaining else 0
    current_pace = total_earned / max(1, weeks_elapsed)
    pace_state = "ahead" if current_pace > goal / weeks_total else "on track"
    if current_pace < (goal / weeks_total) * 0.95:
        pace_state = "behind"
    return {
        "niches": niches,
        "active_scrapes": active,
        "storage": get_storage_monitor(),
        "machines": get_machine_health(),
        "hetzner": get_hetzner_enrichment_status(),
        "sales": get_sales_snapshot(),
        "queue": queue_state.get("items", []),
        "warmup": warmup.get("accounts", []),
        "outreach": outreach.get("targets", []),
        "listings": listings,
        "platforms": ["Gumroad", "Datarade", "Fiverr", "Instantly", "Apollo"],
        "pipeline": PIPELINE_SCHEDULE,
        "revenue": revenue,
        "revenue_progress_pct": min(100.0, (total_earned / max(1, goal)) * 100),
        "pace_required": round(pace_required, 2),
        "pace_state": pace_state,
        "weeks_remaining": weeks_remaining,
        "now": datetime.now(),
        "niche_names": NICHES,
    }


@app.on_event("startup")
def startup():
    _seed_state_files()


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, **_dashboard_payload()})


@app.get("/partials/dashboard", response_class=HTMLResponse)
def dashboard_partial(request: Request):
    return templates.TemplateResponse("_dashboard_content.html", {"request": request, **_dashboard_payload()})


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=DASHBOARD_PORT, reload=False)
