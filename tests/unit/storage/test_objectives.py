import json
from pathlib import Path

import pytest

from wellness_tracker.models.objectives import (
    NutritionTargets,
    TrainingTarget,
    WeeklyObjectives,
    WeightGoal,
)
from wellness_tracker.storage import objectives as obj_storage


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
def patch_objectives_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(obj_storage.settings, "objectives_dir", tmp_path)


class TestSaveObjectives:
    def test_saves_to_correct_path(self, valid_objectives: WeeklyObjectives) -> None:
        path, version = obj_storage.save_objectives(valid_objectives)
        assert path == obj_storage.settings.objectives_dir / "week_2026-06-23_v1.json"
        assert version == "v1"
        assert path.exists()

    def test_second_save_increments_version(
        self, valid_objectives: WeeklyObjectives
    ) -> None:
        obj_storage.save_objectives(valid_objectives)
        path, version = obj_storage.save_objectives(valid_objectives)
        assert version == "v2"
        assert path == obj_storage.settings.objectives_dir / "week_2026-06-23_v2.json"

    def test_saved_file_is_valid_json(self, valid_objectives: WeeklyObjectives) -> None:
        path, _ = obj_storage.save_objectives(valid_objectives)
        data = json.loads(path.read_text())
        assert data["week_starting"] == "2026-06-23"

    def test_round_trip(self, valid_objectives: WeeklyObjectives) -> None:
        path, _ = obj_storage.save_objectives(valid_objectives)
        loaded = WeeklyObjectives.model_validate(json.loads(path.read_text()))
        assert loaded == valid_objectives


class TestGetCurrentVersion:
    def test_returns_latest_version(self, valid_objectives: WeeklyObjectives) -> None:
        obj_storage.save_objectives(valid_objectives)
        obj_storage.save_objectives(valid_objectives)
        assert obj_storage.get_current_version("2026-06-23") == "v2"

    def test_raises_when_no_versions(self) -> None:
        with pytest.raises(FileNotFoundError):
            obj_storage.get_current_version("2026-01-01")


class TestLoadObjectives:
    def test_loads_correctly(self, valid_objectives: WeeklyObjectives) -> None:
        obj_storage.save_objectives(valid_objectives)
        loaded = obj_storage.load_objectives("2026-06-23")
        assert loaded == valid_objectives

    def test_loads_specific_version(self, valid_objectives: WeeklyObjectives) -> None:
        obj_storage.save_objectives(valid_objectives)
        updated = valid_objectives.model_copy(
            update={"constraints": ["travel this week"]}
        )
        obj_storage.save_objectives(updated)

        first = obj_storage.load_objectives("2026-06-23", version="v1")
        second = obj_storage.load_objectives("2026-06-23", version="v2")
        assert first.constraints == []
        assert second.constraints == ["travel this week"]

    def test_raises_when_file_not_found(self) -> None:
        with pytest.raises(FileNotFoundError):
            obj_storage.load_objectives("2026-01-01")


class TestLoadCurrentObjectives:
    def test_returns_most_recent(self, valid_objectives: WeeklyObjectives) -> None:
        earlier = valid_objectives.model_copy(update={"week_starting": "2026-06-16"})
        obj_storage.save_objectives(earlier)
        obj_storage.save_objectives(valid_objectives)
        current, version = obj_storage.load_current_objectives()
        assert current.week_starting == "2026-06-23"
        assert version == "v1"

    def test_returns_latest_version_for_most_recent_week(
        self, valid_objectives: WeeklyObjectives
    ) -> None:
        obj_storage.save_objectives(valid_objectives)
        obj_storage.save_objectives(valid_objectives)
        current, version = obj_storage.load_current_objectives()
        assert current.week_starting == "2026-06-23"
        assert version == "v2"

    def test_raises_when_no_objectives(self) -> None:
        with pytest.raises(FileNotFoundError):
            obj_storage.load_current_objectives()
