from pathlib import Path

K6_SPECTRAL_PATH = "/opt/crkdev/spectral"
CHECKPOINTS_PATH = "/opt/crkdev/spectral/checkpoints"
PI_TAILSCALE_IP = "100.76.151.115"
HETZNER_TAILSCALE_IP = "100.92.177.81"
DASHBOARD_PORT = 3000
SCRAPE_HUNG_THRESHOLD_MINUTES = 10
SCRAPE_LOG_PATTERN = "{K6_SPECTRAL_PATH}/logs/{niche}/*.log"
TMUX_SESSIONS = ["chiro"]
PASSPORT_MOUNT = "/mnt/passport"
DISCORD_LOG_PATH = "/opt/crkdev/spectral/logs/discord.log"
GUMROAD_API_KEY = ""
REVENUE_GOAL = 3425
REVENUE_WEEKS = 30

BASE_DIR = Path(__file__).resolve().parent
STATE_FILES = {
    "queue": BASE_DIR / "queue.json",
    "warmup": BASE_DIR / "warmup.json",
    "outreach": BASE_DIR / "outreach.json",
    "listings": BASE_DIR / "listings.json",
    "revenue": BASE_DIR / "revenue.json",
}

PIPELINE_SCHEDULE = {
    "chiro": {"next_run": "2026-05-05T02:00:00", "last_run": "2026-05-04T02:01:00"},
    "medspa": {"next_run": "2026-05-06T02:00:00", "last_run": "2026-05-03T02:00:00"},
    "pi_lawyers": {"next_run": "2026-05-07T02:00:00", "last_run": "2026-05-02T02:00:00"},
}
