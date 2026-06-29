import json
from importlib.resources import files
from typing import Any

import yaml
from anthropic import Anthropic

from wellness_tracker.config import settings

_RETRY_MESSAGE = (
    "Your previous response was not valid JSON. "
    "Please respond with only a JSON object matching the required structure. "
    "No explanation, no markdown, just the JSON."
)


class BaseAgent:
    agent_id: str
    version: str
    system_prompt: str
    max_tokens: int

    def __init__(self, prompt_filename: str) -> None:
        prompt_data = self._load_prompt(prompt_filename)
        self.agent_id = prompt_data["agent_id"]
        self.version = prompt_data["version"]
        self.system_prompt = prompt_data["system_prompt"]
        self.max_tokens = prompt_data["max_tokens"]
        self._client = Anthropic(api_key=settings.anthropic_api_key)

    @staticmethod
    def _load_prompt(filename: str) -> dict[str, Any]:
        text = (
            files("wellness_tracker.prompts")
            .joinpath(filename)
            .read_text(encoding="utf-8")
        )
        data: dict[str, Any] = yaml.safe_load(text)
        return data

    def _call_llm(self, user_message: str) -> str:
        response = self._client.messages.create(
            model=settings.anthropic_model,
            max_tokens=self.max_tokens,
            system=self.system_prompt,
            messages=[{"role": "user", "content": user_message}],
        )
        return "".join(block.text for block in response.content if block.type == "text")

    def _parse_json(self, raw: str) -> dict[str, Any]:
        try:
            return self._strip_and_parse(raw)
        except json.JSONDecodeError:
            retry_raw = self._call_llm(_RETRY_MESSAGE)
            try:
                return self._strip_and_parse(retry_raw)
            except json.JSONDecodeError as exc:
                raise ValueError(
                    f"LLM response could not be parsed as JSON: {retry_raw!r}"
                ) from exc

    @staticmethod
    def _strip_and_parse(raw: str) -> dict[str, Any]:
        cleaned = raw.strip()
        if cleaned.startswith("```"):
            lines = cleaned.split("\n")
            cleaned = "\n".join(lines[1:-1])
        data: dict[str, Any] = json.loads(cleaned)
        return data

    def run(self, payload: dict[str, Any]) -> Any:
        raise NotImplementedError
