import pytest
from pydantic import ValidationError

from wellness_tracker.models.objectives import (
    NutritionTargets,
    TrainingTarget,
    WeeklyObjectives,
    WeightGoal,
)

VALID_OBJECTIVES_DATA = {
    "week_starting": "2026-06-23",
    "weight_goal": {
        "direction": "lose",
        "target_weekly_deficit_kcal": 2800,
        "current_weight_kg": 82.0,
    },
    "training_targets": {"running": {"sessions": 3, "min_duration_minutes": 40}},
    "nutrition_targets": {
        "daily_calorie_target": 1900,
        "daily_protein_target_g": 140,
    },
    "constraints": ["left knee — avoid high impact if pain above 3/10"],
}


class TestWeeklyObjectivesValid:
    def test_valid_objectives_accepted(self) -> None:
        obj = WeeklyObjectives.model_validate(VALID_OBJECTIVES_DATA)
        assert obj.week_starting == "2026-06-23"
        assert obj.weight_goal.direction == "lose"
        assert obj.weight_goal.target_weekly_deficit_kcal == 2800
        assert obj.weight_goal.current_weight_kg == 82.0
        assert obj.training_targets["running"].sessions == 3
        assert obj.nutrition_targets.daily_calorie_target == 1900
        assert obj.constraints == ["left knee — avoid high impact if pain above 3/10"]


class TestNutritionTargets:
    def test_calorie_below_minimum_rejected(self) -> None:
        with pytest.raises(ValidationError, match="daily_calorie_target"):
            NutritionTargets.model_validate(
                {"daily_calorie_target": 500, "daily_protein_target_g": 140}
            )

    def test_calorie_above_maximum_rejected(self) -> None:
        with pytest.raises(ValidationError, match="daily_calorie_target"):
            NutritionTargets.model_validate(
                {"daily_calorie_target": 5001, "daily_protein_target_g": 140}
            )

    def test_calorie_at_minimum_accepted(self) -> None:
        n = NutritionTargets.model_validate(
            {"daily_calorie_target": 1000, "daily_protein_target_g": 0}
        )
        assert n.daily_calorie_target == 1000

    def test_calorie_at_maximum_accepted(self) -> None:
        n = NutritionTargets.model_validate(
            {"daily_calorie_target": 5000, "daily_protein_target_g": 0}
        )
        assert n.daily_calorie_target == 5000


class TestTrainingTarget:
    def test_sessions_zero_rejected(self) -> None:
        with pytest.raises(ValidationError, match="sessions"):
            TrainingTarget.model_validate({"sessions": 0, "min_duration_minutes": 40})

    def test_sessions_fifteen_rejected(self) -> None:
        with pytest.raises(ValidationError, match="sessions"):
            TrainingTarget.model_validate({"sessions": 15, "min_duration_minutes": 40})

    def test_sessions_one_accepted(self) -> None:
        t = TrainingTarget.model_validate({"sessions": 1, "min_duration_minutes": 40})
        assert t.sessions == 1

    def test_sessions_fourteen_accepted(self) -> None:
        t = TrainingTarget.model_validate({"sessions": 14, "min_duration_minutes": 40})
        assert t.sessions == 14


class TestWeightGoal:
    def test_deficit_required_when_losing(self) -> None:
        with pytest.raises(ValidationError, match="target_weekly_deficit_kcal"):
            WeightGoal.model_validate({"direction": "lose", "current_weight_kg": 82.0})

    def test_weight_zero_rejected(self) -> None:
        with pytest.raises(ValidationError, match="current_weight_kg"):
            WeightGoal.model_validate({"direction": "maintain", "current_weight_kg": 0})

    def test_weight_three_hundred_rejected(self) -> None:
        with pytest.raises(ValidationError, match="current_weight_kg"):
            WeightGoal.model_validate(
                {"direction": "maintain", "current_weight_kg": 300}
            )


class TestWeeklyObjectivesValidation:
    def test_empty_training_targets_rejected(self) -> None:
        data = {**VALID_OBJECTIVES_DATA, "training_targets": {}}
        with pytest.raises(ValidationError, match="training_targets"):
            WeeklyObjectives.model_validate(data)

    def test_constraints_default_to_empty_list(self) -> None:
        data = {k: v for k, v in VALID_OBJECTIVES_DATA.items() if k != "constraints"}
        obj = WeeklyObjectives.model_validate(data)
        assert obj.constraints == []
