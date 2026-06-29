import json
from pathlib import Path

import pytest

from wellness_tracker.models.envelope import DailyEnvelope, WhoopDayContext
from wellness_tracker.models.objectives import (
    NutritionTargets,
    TrainingTarget,
    WeeklyObjectives,
    WeightGoal,
)
from wellness_tracker.storage import diary as diary_storage


@pytest.fixture
def valid_objectives() -> WeeklyObjectives:
    return WeeklyObjectives(
        week_starting="2026-06-23",
        weight_goal=WeightGoal(
            direction="lose",
            target_weekly_deficit_kcal=2800,
            current_weight_kg=82.0,
        ),
        training_targets={
            "running": TrainingTarget(sessions=3, min_duration_minutes=40)
        },
        nutrition_targets=NutritionTargets(
            daily_calorie_target=1900, daily_protein_target_g=140
        ),
    )


@pytest.fixture(autouse=True)
def patch_diary_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(diary_storage.settings, "diary_dir", tmp_path)


class TestSaveEnvelope:
    def test_saves_to_correct_path(self, valid_objectives: WeeklyObjectives) -> None:
        envelope = DailyEnvelope(
            date="2026-06-27",
            weekly_objectives=valid_objectives,
            whoop=WhoopDayContext(strain_target=14.2),
        )
        path = diary_storage.save_envelope(envelope)
        assert path == diary_storage.settings.diary_dir / "2026-06-27.json"
        assert path.exists()

    def test_saved_file_is_valid_json(self, valid_objectives: WeeklyObjectives) -> None:
        envelope = DailyEnvelope(date="2026-06-27", weekly_objectives=valid_objectives)
        path = diary_storage.save_envelope(envelope)
        data = json.loads(path.read_text())
        assert data["date"] == "2026-06-27"
        assert data["status"] == "in_progress"


class TestLoadEnvelope:
    def test_loads_existing_envelope(self, valid_objectives: WeeklyObjectives) -> None:
        envelope = DailyEnvelope(
            date="2026-06-27",
            weekly_objectives=valid_objectives,
            whoop=WhoopDayContext(strain_target=14.2),
        )
        diary_storage.save_envelope(envelope)
        loaded = diary_storage.load_envelope("2026-06-27")
        assert loaded.envelope_id == envelope.envelope_id
        assert loaded.whoop is not None
        assert loaded.whoop.strain_target == 14.2

    def test_raises_when_file_not_found(self) -> None:
        with pytest.raises(FileNotFoundError):
            diary_storage.load_envelope("2026-01-01")
