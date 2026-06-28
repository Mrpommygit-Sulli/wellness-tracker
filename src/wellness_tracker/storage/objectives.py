import json
from pathlib import Path

from wellness_tracker.config import settings
from wellness_tracker.models.objectives import WeeklyObjectives


def save_objectives(objectives: WeeklyObjectives) -> Path:
    path = settings.objectives_dir / f"week_{objectives.week_starting}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(objectives.model_dump_json(indent=2))
    return path


def load_objectives(week_starting: str) -> WeeklyObjectives:
    path = settings.objectives_dir / f"week_{week_starting}.json"
    if not path.exists():
        raise FileNotFoundError(f"No objectives file found for week {week_starting}")
    return WeeklyObjectives.model_validate(json.loads(path.read_text()))


def load_current_objectives() -> WeeklyObjectives:
    files = sorted(settings.objectives_dir.glob("week_*.json"))
    if not files:
        raise FileNotFoundError(
            "No weekly objectives have been set. Run --set-objectives first."
        )
    return WeeklyObjectives.model_validate(json.loads(files[-1].read_text()))
