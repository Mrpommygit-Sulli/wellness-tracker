import pytest

from wellness_tracker.models.envelope import DailyEnvelope, WhoopDayContext
from wellness_tracker.models.objectives import (
    NutritionTargets,
    TrainingTarget,
    WeeklyObjectives,
    WeightGoal,
)


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


class TestDailyEnvelope:
    def test_defaults_applied(self, valid_objectives: WeeklyObjectives) -> None:
        env = DailyEnvelope(date="2026-06-28", weekly_objectives=valid_objectives)
        assert env.status == "in_progress"
        assert env.envelope_id.startswith("env_")
        assert env.date == "2026-06-28"
        assert env.weekly_objectives == valid_objectives

    def test_envelope_id_includes_date(
        self, valid_objectives: WeeklyObjectives
    ) -> None:
        env = DailyEnvelope(date="2026-06-28", weekly_objectives=valid_objectives)
        assert "2026-06-28" in env.envelope_id

    def test_explicit_envelope_id_preserved(
        self, valid_objectives: WeeklyObjectives
    ) -> None:
        env = DailyEnvelope(
            envelope_id="env_custom_id",
            date="2026-06-28",
            weekly_objectives=valid_objectives,
        )
        assert env.envelope_id == "env_custom_id"

    def test_accepts_whoop_day_context(
        self, valid_objectives: WeeklyObjectives
    ) -> None:
        env = DailyEnvelope(date="2026-06-28", weekly_objectives=valid_objectives)
        assert env.whoop is None
        env.whoop = WhoopDayContext(strain_target=14.2)
        assert env.whoop.strain_target == 14.2
