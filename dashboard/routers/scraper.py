from __future__ import annotations

from datetime import datetime, timedelta

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from data_stub import get_pipeline_points, get_run_history, get_stage_breakdown

router = APIRouter(prefix="/scraper", tags=["scraper"])
templates = Jinja2Templates(directory="templates")


@router.get("/{niche}", response_class=HTMLResponse)
def scraper_detail(request: Request, niche: str):
    logs = [
        f"{(datetime.now() - timedelta(minutes=i)).strftime('%H:%M:%S')} INFO {niche} index={67300 - i * 12} scrape heartbeat"
        for i in range(50)
    ]
    return templates.TemplateResponse(
        "scraper_detail.html",
        {
            "request": request,
            "niche": niche,
            "points": get_pipeline_points(),
            "stages": get_stage_breakdown(),
            "logs": list(reversed(logs)),
            "history": get_run_history(),
        },
    )
