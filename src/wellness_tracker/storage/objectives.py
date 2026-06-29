import json
import re
from pathlib import Path

from wellness_tracker.config import settings
from wellness_tracker.models.objectives import WeeklyObjectives

_FILENAME_RE = re.compile(
    r"^week_(?P<week_starting>\d{4}-\d{2}-\d{2})_v(?P<version>\d+)\.json$"
)


def _path_for(week_starting: str, version: str) -> Path:
    return settings.objectives_dir / f"week_{week_starting}_{version}.json"


def get_current_version(week_starting: str) -> str:
    versions = [
        int(match.group("version"))
        for f in settings.objectives_dir.glob(f"week_{week_starting}_v*.json")
        if (match := _FILENAME_RE.match(f.name)) is not None
    ]
    if not versions:
        raise FileNotFoundError(f"No objectives file found for week {week_starting}")
    return f"v{max(versions)}"


def save_objectives(objectives: WeeklyObjectives) -> tuple[Path, str]:
    settings.objectives_dir.mkdir(parents=True, exist_ok=True)
    try:
        next_version = int(get_current_version(objectives.week_starting)[1:]) + 1
    except FileNotFoundError:
        next_version = 1
    version = f"v{next_version}"
    path = _path_for(objectives.week_starting, version)
    path.write_text(objectives.model_dump_json(indent=2))
    return path, version


def load_objectives(week_starting: str, version: str | None = None) -> WeeklyObjectives:
    if version is None:
        version = get_current_version(week_starting)
    path = _path_for(week_starting, version)
    if not path.exists():
        raise FileNotFoundError(
            f"No objectives file found for week {week_starting} {version}"
        )
    return WeeklyObjectives.model_validate(json.loads(path.read_text()))


def load_current_objectives() -> tuple[WeeklyObjectives, str]:
    week_startings = {
        match.group("week_starting")
        for f in settings.objectives_dir.glob("week_*_v*.json")
        if (match := _FILENAME_RE.match(f.name)) is not None
    }
    if not week_startings:
        raise FileNotFoundError(
            "No weekly objectives have been set. Run --set-objectives first."
        )
    week_starting = max(week_startings)
    version = get_current_version(week_starting)
    objectives = load_objectives(week_starting, version)
    return objectives, version
