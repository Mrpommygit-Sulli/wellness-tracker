import pytest
from pydantic import ValidationError

from wellness_tracker.models.outputs import WhoopBriefOutput


class TestWhoopBriefOutput:
    def test_valid_response_accepted(self) -> None:
        data = {
            "agent_id": "whoop_brief_agent",
            "version": "1.0.0",
            "status": "success",
            "strain_target": 14.2,
            "confidence": 0.96,
            "notes": None,
            "requires_human_review": False,
        }
        output = WhoopBriefOutput.model_validate(data)
        assert output.agent_id == "whoop_brief_agent"
        assert output.version == "1.0.0"
        assert output.status == "success"
        assert output.strain_target == 14.2
        assert output.confidence == 0.96
        assert output.notes is None
        assert output.requires_human_review is False

    def test_strain_target_above_max_rejected(self) -> None:
        with pytest.raises(ValidationError, match="strain_target"):
            WhoopBriefOutput(
                version="1.0.0", status="success", strain_target=21.1, confidence=0.9
            )

    def test_strain_target_below_min_rejected(self) -> None:
        with pytest.raises(ValidationError, match="strain_target"):
            WhoopBriefOutput(
                version="1.0.0", status="success", strain_target=-0.1, confidence=0.9
            )

    def test_strain_target_zero_accepted(self) -> None:
        output = WhoopBriefOutput(
            version="1.0.0", status="success", strain_target=0.0, confidence=0.9
        )
        assert output.strain_target == 0.0

    def test_strain_target_max_accepted(self) -> None:
        output = WhoopBriefOutput(
            version="1.0.0", status="success", strain_target=21.0, confidence=0.9
        )
        assert output.strain_target == 21.0
