from pathlib import Path

import pytest

from wellness_tracker.models.objectives import (
    NutritionTargets,
    TrainingTarget,
    WeeklyObjectives,
    WeightGoal,
)
from wellness_tracker.orchestrator import Orchestrator
from wellness_tracker.storage import diary as diary_storage
from wellness_tracker.storage import objectives as obj_storage


@pytest.mark.e2e
def test_whoop_e2e_extracts_strain_target(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(obj_storage.settings, "objectives_dir", tmp_path / "objectives")
    monkeypatch.setattr(diary_storage.settings, "diary_dir", tmp_path / "diary")

    objectives = WeeklyObjectives(
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
    obj_storage.save_objectives(objectives)

    result = Orchestrator().process(
        "whoop_brief", "Whoop recommends strain target 14.2 today, recovery 73%"
    )

    assert result["status"] == "success"
    assert abs(result["output"].strain_target - 14.2) < 0.5
    assert result["path"].exists()
