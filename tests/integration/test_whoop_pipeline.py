import json
from pathlib import Path
from unittest.mock import patch

import pytest

from tests.fixtures.llm_responses import WHOOP_BRIEF_SUCCESS_RESPONSE
from wellness_tracker.models.objectives import (
    NutritionTargets,
    TrainingTarget,
    WeeklyObjectives,
    WeightGoal,
)
from wellness_tracker.orchestrator import Orchestrator
from wellness_tracker.storage import diary as diary_storage
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
def patch_dirs(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(obj_storage.settings, "objectives_dir", tmp_path / "objectives")
    monkeypatch.setattr(diary_storage.settings, "diary_dir", tmp_path / "diary")


class TestWhoopPipeline:
    @patch("wellness_tracker.agents.base.Anthropic")
    def test_full_pipeline_success(
        self,
        mock_anthropic: object,
        valid_objectives: WeeklyObjectives,
    ) -> None:
        obj_storage.save_objectives(valid_objectives)

        from wellness_tracker.agents.whoop_brief import WhoopBriefAgent

        original_run = WhoopBriefAgent.run
        with (
            patch(
                "wellness_tracker.agents.whoop_brief.WhoopBriefAgent._call_llm",
                return_value=WHOOP_BRIEF_SUCCESS_RESPONSE,
            ),
            patch.object(
                WhoopBriefAgent, "run", autospec=True, side_effect=original_run
            ) as mock_run,
        ):
            result = Orchestrator().process(
                "whoop_brief", "Whoop strain target 14.2 today"
            )

        assert mock_run.call_count == 1
        assert result["status"] == "success"
        assert result["output"].strain_target == 14.2

        saved_path = result["path"]
        assert saved_path.exists()
        data = json.loads(saved_path.read_text())
        assert data["whoop"]["strain_target"] == 14.2

    def test_missing_objectives_raises(self) -> None:
        with pytest.raises(FileNotFoundError):
            Orchestrator().process("whoop_brief", "Whoop strain target 14.2 today")

    @patch("wellness_tracker.agents.base.Anthropic")
    def test_existing_envelope_reused_on_second_run(
        self,
        mock_anthropic: object,
        valid_objectives: WeeklyObjectives,
    ) -> None:
        obj_storage.save_objectives(valid_objectives)

        with patch(
            "wellness_tracker.agents.whoop_brief.WhoopBriefAgent._call_llm",
            return_value=WHOOP_BRIEF_SUCCESS_RESPONSE,
        ):
            first_result = Orchestrator().process(
                "whoop_brief", "Whoop strain target 14.2 today"
            )
            second_result = Orchestrator().process(
                "whoop_brief", "Whoop strain target 14.2 today"
            )

        assert first_result["output"] and second_result["path"] == first_result["path"]
        first_envelope_id = json.loads(first_result["path"].read_text())["envelope_id"]
        second_envelope_id = json.loads(second_result["path"].read_text())[
            "envelope_id"
        ]
        assert first_envelope_id == second_envelope_id
