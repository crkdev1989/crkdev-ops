from __future__ import annotations

import json
from pathlib import Path

from config import CHECKPOINTS_PATH

TOTAL_EXPECTED_ROWS = {
    "chiro": 150000,
}

CHECKPOINT_DIR_MAP = {
    "chiro": "chiro_national",
}


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
        }

    raw = json.loads(checkpoint_file.read_text(encoding="utf-8"))
    rows_processed = int(raw.get("rows_processed", 0))
    remaining_rows = max(0, expected_rows - rows_processed) if expected_rows else 0
    progress_pct = (rows_processed / expected_rows * 100) if expected_rows else 0.0

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
    }
