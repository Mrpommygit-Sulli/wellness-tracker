from unittest.mock import patch

from tests.fixtures.llm_responses import (
    WHOOP_BRIEF_MALFORMED_RESPONSE,
    WHOOP_BRIEF_NO_TARGET_RESPONSE,
    WHOOP_BRIEF_SUCCESS_RESPONSE,
)
from wellness_tracker.agents.whoop_brief import WhoopBriefAgent


class TestWhoopBriefAgentPromptLoading:
    def test_loads_prompt_via_importlib_resources(self) -> None:
        with patch("wellness_tracker.agents.base.Anthropic"):
            agent = WhoopBriefAgent()
        assert agent.agent_id == "whoop_brief_agent"
        assert agent.version == "1.0.0"
        assert isinstance(agent.system_prompt, str)
        assert len(agent.system_prompt) > 0
        assert agent.max_tokens == 256


class TestWhoopBriefAgentRun:
    @patch("wellness_tracker.agents.base.Anthropic")
    def test_extracts_strain_target(self, mock_anthropic: object) -> None:
        agent = WhoopBriefAgent()
        with patch.object(
            agent, "_call_llm", return_value=WHOOP_BRIEF_SUCCESS_RESPONSE
        ):
            output = agent.run({"raw_text": "Whoop strain target 14.2 today"})

        assert output.status == "success"
        assert output.strain_target == 14.2
        assert output.confidence >= 0.8
        assert output.requires_human_review is False

    @patch("wellness_tracker.agents.base.Anthropic")
    def test_handles_missing_strain_target(self, mock_anthropic: object) -> None:
        agent = WhoopBriefAgent()
        with patch.object(
            agent, "_call_llm", return_value=WHOOP_BRIEF_NO_TARGET_RESPONSE
        ):
            output = agent.run({"raw_text": "Feeling good today"})

        assert output.status == "unable_to_determine"
        assert output.strain_target is None
        assert output.confidence == 0.0

    @patch("wellness_tracker.agents.base.Anthropic")
    def test_handles_malformed_response(self, mock_anthropic: object) -> None:
        agent = WhoopBriefAgent()
        with patch.object(
            agent, "_call_llm", return_value=WHOOP_BRIEF_MALFORMED_RESPONSE
        ):
            output = agent.run({"raw_text": "..."})

        assert output.status == "unable_to_determine"
        assert output.strain_target is None
        assert output.confidence == 0.0
