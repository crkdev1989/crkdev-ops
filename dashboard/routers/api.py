from __future__ import annotations

import json
import subprocess
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, HTTPException

from config import STATE_FILES, TMUX_SESSIONS
from data_stub import get_niche_statuses

router = APIRouter(prefix="/api", tags=["api"])


def _read_json(path: Path, default: dict | list):
    if not path.exists():
        path.write_text(json.dumps(default, indent=2), encoding="utf-8")
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict | list):
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


@router.get("/status")
def status():
    statuses = get_niche_statuses()
    return {
        "niches": statuses,
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "hung_flags": {n["name"]: n["status"] == "hung" for n in statuses},
    }


@router.post("/restart/{niche}")
def restart_scraper(niche: str):
    session = niche if niche in TMUX_SESSIONS else TMUX_SESSIONS[0]
    stop_cmd = ["tmux", "send-keys", "-t", session, "C-c", "Enter"]
    start_cmd = ["tmux", "send-keys", "-t", session, f"spectral run {niche}", "Enter"]
    try:
        subprocess.run(stop_cmd, check=True, timeout=5)
        subprocess.run(["sleep", "2"], check=False, timeout=3)
        subprocess.run(start_cmd, check=True, timeout=5)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Restart failed: {exc}") from exc
    return {"ok": True, "message": f"{niche} restart command dispatched", "session": session}


@router.post("/listings/toggle")
def toggle_listing(payload: dict):
    listings = _read_json(STATE_FILES["listings"], {})
    niche = payload.get("niche")
    platform = payload.get("platform")
    checked = bool(payload.get("checked", False))
    if not niche or not platform:
        raise HTTPException(status_code=400, detail="niche and platform required")
    listings.setdefault(niche, {})
    listings[niche][platform] = checked
    _write_json(STATE_FILES["listings"], listings)
    return {"ok": True}


@router.post("/queue/add")
def queue_add(payload: dict):
    queue = _read_json(STATE_FILES["queue"], {"items": []})
    niche = payload.get("niche")
    if not niche:
        raise HTTPException(status_code=400, detail="niche required")
    if niche not in queue["items"]:
        queue["items"].append(niche)
    _write_json(STATE_FILES["queue"], queue)
    return {"ok": True, "queue": queue["items"]}


@router.post("/queue/remove")
def queue_remove(payload: dict):
    queue = _read_json(STATE_FILES["queue"], {"items": []})
    niche = payload.get("niche")
    queue["items"] = [n for n in queue["items"] if n != niche]
    _write_json(STATE_FILES["queue"], queue)
    return {"ok": True, "queue": queue["items"]}


@router.post("/warmup/update")
def update_warmup(payload: dict):
    warmup = _read_json(STATE_FILES["warmup"], {"accounts": []})
    account = payload.get("account")
    if not account:
        raise HTTPException(status_code=400, detail="account required")
    for row in warmup["accounts"]:
        if row["account"] == account:
            row.update(payload)
            break
    else:
        warmup["accounts"].append(payload)
    _write_json(STATE_FILES["warmup"], warmup)
    return {"ok": True}


@router.post("/outreach/add")
def outreach_add(payload: dict):
    outreach = _read_json(STATE_FILES["outreach"], {"targets": []})
    required = ["company", "sent_date", "follow_up_due", "status"]
    if any(not payload.get(k) for k in required):
        raise HTTPException(status_code=400, detail="Missing required fields")
    outreach["targets"].append(payload)
    _write_json(STATE_FILES["outreach"], outreach)
    return {"ok": True}


@router.post("/outreach/update")
def outreach_update(payload: dict):
    outreach = _read_json(STATE_FILES["outreach"], {"targets": []})
    company = payload.get("company")
    for row in outreach["targets"]:
        if row["company"] == company:
            row.update(payload)
            _write_json(STATE_FILES["outreach"], outreach)
            return {"ok": True}
    raise HTTPException(status_code=404, detail="Target not found")


@router.post("/revenue/update")
def revenue_update(payload: dict):
    revenue = _read_json(STATE_FILES["revenue"], {})
    revenue.update(payload)
    _write_json(STATE_FILES["revenue"], revenue)
    return {"ok": True, "revenue": revenue}
