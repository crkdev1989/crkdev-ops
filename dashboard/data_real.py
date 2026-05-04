from __future__ import annotations

import json
import os
import shutil
from datetime import datetime, timedelta
from pathlib import Path

import psutil

from config import CHECKPOINTS_PATH, PASSPORT_MOUNT, SCRAPE_HUNG_THRESHOLD_MINUTES

TOTAL_EXPECTED_ROWS = {
    "chiro": 150000,
}

CHECKPOINT_DIR_MAP = {
    "chiro": "chiro_national",
}

CHIRO_PROGRESS_HISTORY_PATH = Path("/opt/crkdev/crkdev-ops/dashboard/chiro_progress_history.json")
CHIRO_JSONL_PATH = Path("/mnt/passport/scraper-runs/chiro_national_gmaps.jsonl")
CHIRO_DATASET_DIR = Path("/mnt/passport/scraper-runs/chiro_national")


def _parse_iso(ts: str) -> datetime | None:
    try:
        return datetime.fromisoformat(ts)
    except (TypeError, ValueError):
        return None


def _read_history() -> list[dict]:
    if not CHIRO_PROGRESS_HISTORY_PATH.exists():
        return []
    try:
        payload = json.loads(CHIRO_PROGRESS_HISTORY_PATH.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []
    if not isinstance(payload, list):
        return []
    return [p for p in payload if isinstance(p, dict)]


def _write_history(entries: list[dict]) -> None:
    try:
        CHIRO_PROGRESS_HISTORY_PATH.parent.mkdir(parents=True, exist_ok=True)
        CHIRO_PROGRESS_HISTORY_PATH.write_text(
            json.dumps(entries, indent=2), encoding="utf-8"
        )
    except OSError:
        return


def _append_history(rows_processed: int) -> tuple[list[dict], str]:
    entries = _read_history()
    now = datetime.now().replace(microsecond=0).isoformat()
    entries.append({"timestamp": now, "rows_processed": rows_processed})
    entries = entries[-2000:]
    _write_history(entries)
    return entries, now


def _human_elapsed(start: datetime, end: datetime) -> str:
    diff = max(timedelta(0), end - start)
    days = diff.days
    hours, rem = divmod(diff.seconds, 3600)
    minutes, _ = divmod(rem, 60)
    parts = []
    if days:
        parts.append(f"{days}d")
    if days or hours:
        parts.append(f"{hours}h")
    parts.append(f"{minutes}m")
    return " ".join(parts)


def _calc_rpm_eta(entries: list[dict], rows_processed: int, remaining_rows: int) -> tuple[float | None, int | None]:
    if len(entries) < 2:
        return None, None
    now = _parse_iso(entries[-1].get("timestamp"))
    if now is None:
        return None, None
    target = now - timedelta(minutes=10)
    candidates: list[tuple[float, int]] = []
    for e in entries[:-1]:
        ts = _parse_iso(e.get("timestamp"))
        if ts is None:
            continue
        candidates.append((abs((ts - target).total_seconds()), int(e.get("rows_processed", 0))))
    if not candidates:
        return None, None
    _, baseline_rows = min(candidates, key=lambda x: x[0])
    delta_rows = rows_processed - baseline_rows
    rpm = round(delta_rows / 10.0, 2)
    if rpm <= 0:
        return rpm, None
    eta = int(remaining_rows / rpm) if remaining_rows > 0 else 0
    return rpm, eta


def _status_from_checkpoint(checkpoint_file: Path, remaining_rows: int) -> tuple[str, str | None]:
    if not checkpoint_file.exists():
        return "error", None
    modified_at = datetime.fromtimestamp(checkpoint_file.stat().st_mtime).replace(microsecond=0)
    age = datetime.now() - modified_at
    if remaining_rows == 0:
        return "idle", modified_at.isoformat()
    if age > timedelta(minutes=SCRAPE_HUNG_THRESHOLD_MINUTES):
        return "hung", modified_at.isoformat()
    return "running", modified_at.isoformat()


def read_checkpoint(niche: str) -> dict:
    checkpoint_dir = CHECKPOINT_DIR_MAP.get(niche, niche)
    checkpoint_file = (
        Path(CHECKPOINTS_PATH) / checkpoint_dir / "gmaps_lookup_checkpoint.json"
    )
    expected_rows = TOTAL_EXPECTED_ROWS.get(niche, 0)

    if not checkpoint_file.exists():
        return {
            "niche": niche,
            "exists": False,
            "checkpoint_file": str(checkpoint_file),
            "job_id": "",
            "last_index": 0,
            "rows_processed": 0,
            "rows_updated": 0,
            "rows_skipped_no_result": 0,
            "rows_failed": 0,
            "total_expected_rows": expected_rows,
            "remaining_rows": expected_rows,
            "progress_pct": 0.0,
            "rpm": None,
            "eta_minutes": None,
            "elapsed_human": None,
            "status": "error",
            "last_scrape": None,
        }

    raw = json.loads(checkpoint_file.read_text(encoding="utf-8"))
    rows_processed = int(raw.get("rows_processed", 0))
    remaining_rows = max(0, expected_rows - rows_processed) if expected_rows else 0
    progress_pct = (rows_processed / expected_rows * 100) if expected_rows else 0.0
    history_entries, _ = _append_history(rows_processed)
    rpm, eta_minutes = _calc_rpm_eta(history_entries, rows_processed, remaining_rows)
    start_dt = _parse_iso(history_entries[0].get("timestamp")) if history_entries else None
    elapsed_human = _human_elapsed(start_dt, datetime.now()) if start_dt else None
    status, last_scrape = _status_from_checkpoint(checkpoint_file, remaining_rows)

    return {
        "niche": niche,
        "exists": True,
        "checkpoint_file": str(checkpoint_file),
        "job_id": raw.get("job_id", ""),
        "last_index": int(raw.get("last_index", 0)),
        "rows_processed": rows_processed,
        "rows_updated": int(raw.get("rows_updated", 0)),
        "rows_skipped_no_result": int(raw.get("rows_skipped_no_result", 0)),
        "rows_failed": int(raw.get("rows_failed", 0)),
        "total_expected_rows": expected_rows,
        "remaining_rows": remaining_rows,
        "progress_pct": round(progress_pct, 2),
        "rpm": rpm,
        "eta_minutes": eta_minutes,
        "elapsed_human": elapsed_human,
        "status": status,
        "last_scrape": last_scrape,
    }


def get_chiro_storage() -> dict:
    total, used, free = shutil.disk_usage(PASSPORT_MOUNT)

    def _dir_size(path: Path) -> int:
        if not path.exists():
            return 0
        if path.is_file():
            return path.stat().st_size
        total_size = 0
        for root, _, files in os.walk(path):
            for name in files:
                file_path = Path(root) / name
                try:
                    total_size += os.path.getsize(file_path)
                except OSError:
                    continue
        return total_size

    dataset_size_bytes = _dir_size(CHIRO_DATASET_DIR)
    return {
        "total_gb": round(total / (1024**3), 2),
        "used_gb": round(used / (1024**3), 2),
        "free_gb": round(free / (1024**3), 2),
        "chiro_dataset_gb": round(dataset_size_bytes / (1024**3), 2),
    }


def get_k6_machine_health() -> dict:
    disk = psutil.disk_usage("/")
    return {
        "cpu": round(psutil.cpu_percent(interval=0.25), 1),
        "ram": round(psutil.virtual_memory().percent, 1),
        "disk": round(disk.percent, 1),
        "status": "healthy",
    }


def get_chiro_quality_metrics() -> dict:
    if not CHIRO_JSONL_PATH.exists():
        return {
            "email_hit_rate": None,
            "direct_pct": None,
            "generic_pct": None,
            "none_pct": None,
        }
    generic_prefixes = {
        "info",
        "contact",
        "sales",
        "hello",
        "support",
        "admin",
        "office",
        "team",
    }
    total = 0
    with_email = 0
    direct = 0
    generic = 0
    none = 0
    with CHIRO_JSONL_PATH.open("r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except ValueError:
                continue
            total += 1
            email = str(row.get("email", "")).strip().lower()
            if not email:
                none += 1
                continue
            with_email += 1
            local = email.split("@", 1)[0]
            if local in generic_prefixes:
                generic += 1
            else:
                direct += 1
    if total == 0:
        return {
            "email_hit_rate": None,
            "direct_pct": None,
            "generic_pct": None,
            "none_pct": None,
        }
    return {
        "email_hit_rate": round(with_email / total * 100, 2),
        "direct_pct": round(direct / total * 100, 2),
        "generic_pct": round(generic / total * 100, 2),
        "none_pct": round(none / total * 100, 2),
    }
