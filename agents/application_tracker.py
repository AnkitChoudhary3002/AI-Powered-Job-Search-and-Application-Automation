
import json

from pathlib import Path
from datetime import datetime, timezone, timedelta

BASE_DIR = Path(__file__).resolve().parent.parent
HISTORY_PATH = BASE_DIR / "outputs" / "application_history.json"

COOLDOWN_DAYS = 7


def load_history():
    if not HISTORY_PATH.exists():
        return {}

    with open(HISTORY_PATH, "r", encoding="utf-8") as file:
        return json.load(file)


def can_apply(company):
    history = load_history()
    company_key = company.strip().lower()

    if company_key not in history:
        return True

    last_applied = datetime.fromisoformat(
        history[company_key]["applied_at"]
    )

    elapsed = datetime.now(timezone.utc) - last_applied

    return elapsed >= timedelta(days=COOLDOWN_DAYS)


def record_application(company, job_title, apply_url):
    HISTORY_PATH.parent.mkdir(parents=True, exist_ok=True)

    history = load_history()
    company_key = company.strip().lower()

    history[company_key] = {
        "company": company,
        "job_title": job_title,
        "apply_url": apply_url,
        "applied_at": datetime.now(timezone.utc).isoformat()
    }

    with open(HISTORY_PATH, "w", encoding="utf-8") as file:
        json.dump(history, file, indent=4, ensure_ascii=False)
