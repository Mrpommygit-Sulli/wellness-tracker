import json
from pathlib import Path

from wellness_tracker.config import settings
from wellness_tracker.models.envelope import DailyEnvelope


def save_envelope(envelope: DailyEnvelope) -> Path:
    path = settings.diary_dir / f"{envelope.date}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(envelope.model_dump_json(indent=2))
    return path


def load_envelope(date: str) -> DailyEnvelope:
    path = settings.diary_dir / f"{date}.json"
    if not path.exists():
        raise FileNotFoundError(f"No diary envelope found for date {date}")
    return DailyEnvelope.model_validate(json.loads(path.read_text()))
