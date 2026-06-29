# 003 — Whoop Daily Brief

## Overview

Delivers the ability to log a morning Whoop strain target via `--whoop`.
Introduces the first agent (WhoopBriefAgent), the first LLM call, the first
envelope written to disk, and a minimal orchestrator that routes the
whoop_brief input type through the agent and persists the result.

This slice establishes the pattern that all subsequent agent slices follow:
YAML prompt → BaseAgent → LLM call → typed output → envelope → disk.

By the end of this slice, a user can log their daily Whoop strain target and
have it persisted as part of a daily envelope ready for subsequent inputs.

---

## Objectives

1. `BaseAgent` defined — all agents extend this
2. `WhoopBriefAgent` implemented with YAML prompt
3. `WhoopBriefOutput` Pydantic model defined
4. `WhoopDayContext` model added to `DailyEnvelope`
5. `DailyEnvelope` extended with `whoop` field
6. Minimal orchestrator routes `whoop_brief` through agent and persists envelope
7. `--whoop` CLI command processes plain text and prints summary
8. Daily envelope written to `data/diary/YYYY-MM-DD.json`
9. Unit tests cover agent output parsing and envelope extension
10. Integration test covers full `--whoop` pipeline with mocked LLM

---

## What This Slice Does NOT Include

- No accumulator agent
- No audit trail (added in Slice 11)
- No guardrails (added in Slice 7)
- No HITL
- No other agents or input types
- No training or nutrition data

---

## New Models Introduced

### File: `src/wellness_tracker/models/envelope.py`

Extend the existing `DailyEnvelope` stub with two additions:

#### WhoopDayContext (new model)

| Field | Type | Validation |
|-------|------|------------|
| strain_target | float | 0.0–21.0 inclusive |
| strain_accumulated | float | 0.0–21.0 inclusive, default 0.0 |
| strain_actual | float \| None | 0.0–21.0 inclusive if provided |
| weight_kg | float \| None | > 0 and < 300 if provided |

#### DailyEnvelope (extend existing stub)

Add one field to the existing four-field stub:

| Field | Type | Default |
|-------|------|---------|
| whoop | WhoopDayContext \| None | None |

---

## New Agent Output Model

### File: `src/wellness_tracker/models/outputs.py`

Replace the placeholder `AgentOutput` base with the first real output contract:

#### WhoopBriefOutput

| Field | Type | Validation |
|-------|------|------------|
| agent_id | str | Always "whoop_brief_agent" |
| version | str | Matches version in YAML prompt file |
| status | Literal["success", "partial", "unable_to_determine"] | Required |
| strain_target | float \| None | 0.0–21.0 if provided |
| confidence | float | 0.0–1.0 inclusive |
| notes | str \| None | Optional |
| requires_human_review | bool | Default False |

---

## New Files Introduced

### File: `src/wellness_tracker/agents/base.py`

BaseAgent is the foundation all agents extend. Responsibilities:
- Load YAML prompt file via `importlib.resources`
- Expose `agent_id`, `version`, `system_prompt`, `max_tokens`
- Provide `_call_llm(user_message: str) -> str` — calls Anthropic API
- Provide `_parse_json(raw: str) -> dict` — strips markdown fences,
  parses JSON, retries once on failure
- Define abstract `run(payload: dict) -> Any` — implemented by each agent

```python
# Conceptual structure — not prescriptive implementation

class BaseAgent:
    agent_id: str
    version: str
    system_prompt: str
    max_tokens: int

    def __init__(self, prompt_filename: str) -> None:
        # Load YAML via importlib.resources
        # Set agent_id, version, system_prompt, max_tokens

    def _call_llm(self, user_message: str) -> str:
        # Call Anthropic API with system_prompt + user_message
        # Return raw response text

    def _parse_json(self, raw: str) -> dict:
        # Strip markdown code fences if present (```json ... ```)
        # Parse JSON
        # On JSONDecodeError: retry _call_llm once with correction prompt
        # On second failure: raise ValueError with raw response included

    def run(self, payload: dict) -> Any:
        raise NotImplementedError
```

---

### File: `src/wellness_tracker/agents/whoop_brief.py`

Single-responsibility agent. Extracts strain target from plain text.

```python
# Conceptual structure

class WhoopBriefAgent(BaseAgent):
    def __init__(self) -> None:
        super().__init__("whoop_brief_agent.yaml")

    def run(self, payload: dict) -> WhoopBriefOutput:
        # Build user message from payload["raw_text"]
        # Call _call_llm
        # Parse JSON response via _parse_json
        # Validate and return WhoopBriefOutput
        # On parse failure: return WhoopBriefOutput with
        #   status="unable_to_determine", confidence=0.0
```

---

### File: `src/wellness_tracker/prompts/whoop_brief_agent.yaml`

```yaml
agent_id: whoop_brief_agent
version: "1.0.0"
max_tokens: 256

system_prompt: |
  You are a Whoop data extraction agent. Your sole responsibility is to
  extract the daily strain target from a plain text Whoop brief.

  You must always respond with valid JSON matching this exact structure:
  {
    "strain_target": <float between 0.0 and 21.0 or null if not found>,
    "confidence": <float between 0.0 and 1.0>,
    "notes": <string or null>
  }

  Rules:
  - Extract only the strain target value
  - If no strain target is mentioned set strain_target to null
    and confidence to 0.0
  - Respond with JSON only — no explanation, no markdown code fences,
    no preamble
  - Never invent a strain target that was not explicitly stated
```

---

### File: `src/wellness_tracker/orchestrator.py`

Minimal orchestrator — handles only `whoop_brief` in this slice.
Extended in every subsequent slice.

Responsibilities in this slice:
- Load current weekly objectives (fail with clear message if none set)
- Load today's envelope from disk if it exists, create new one if not
- Route `whoop_brief` input to `WhoopBriefAgent`
- Apply agent output to envelope (`envelope.whoop = WhoopDayContext(...)`)
- Persist envelope to `data/diary/YYYY-MM-DD.json`
- Return summary dict for CLI to display

```python
# Conceptual structure

class Orchestrator:
    def process(
        self,
        input_type: str,
        raw_text: str
    ) -> dict:
        objectives = load_current_objectives()  # raises if none set
        envelope = self._load_or_create_envelope(objectives)

        if input_type == "whoop_brief":
            return self._handle_whoop_brief(raw_text, envelope)

        raise NotImplementedError(f"Input type {input_type} not yet implemented")

    def _handle_whoop_brief(
        self,
        raw_text: str,
        envelope: DailyEnvelope
    ) -> dict:
        agent = WhoopBriefAgent()
        output = agent.run({"raw_text": raw_text})

        if output.status == "success" and output.strain_target is not None:
            envelope.whoop = WhoopDayContext(
                strain_target=output.strain_target
            )

        self._save_envelope(envelope)
        return {"status": output.status, "output": output}

    def _load_or_create_envelope(
        self,
        objectives: WeeklyObjectives
    ) -> DailyEnvelope:
        # Load from data/diary/YYYY-MM-DD.json if exists
        # Create new DailyEnvelope if not

    def _save_envelope(self, envelope: DailyEnvelope) -> None:
        # Write to data/diary/YYYY-MM-DD.json
        # Create directory if not exists
```

---

### File: `src/wellness_tracker/storage/diary.py`

Two functions:

```
save_envelope(envelope: DailyEnvelope) -> Path
    Writes to data/diary/{date}.json
    Creates directory if it does not exist
    Returns path written to

load_envelope(date: str) -> DailyEnvelope
    Reads from data/diary/{date}.json
    Raises FileNotFoundError if not found
    Raises ValidationError if content is invalid
```

---

## CLI Command

**File:** `src/wellness_tracker/main.py`

Add `--whoop` argument to the existing argument parser:

```
--whoop "<text>"    Log morning Whoop brief
```

On success, print:

```
✓ Whoop brief logged
  Strain target: 14.2
  Envelope saved: data/diary/2026-06-27.json
```

On failure (unable_to_determine):

```
⚠ Could not extract strain target from input
  Try again with clearer text e.g.
  "Whoop strain target 14.2 today"
```

On missing objectives:

```
✗ No weekly objectives found
  Run --set-objectives before logging daily data
```

---

## Directory Additions This Slice

```
src/
  wellness_tracker/
    agents/
      __init__.py
      base.py                    # BaseAgent
      whoop_brief.py             # WhoopBriefAgent
    prompts/
      __init__.py
      whoop_brief_agent.yaml     # Prompt + version
    storage/
      diary.py                   # save_envelope, load_envelope
    orchestrator.py              # Minimal orchestrator

tests/
  unit/
    agents/
      __init__.py
      test_whoop_brief_agent.py  # Unit tests — mocked LLM
    models/
      test_whoop_output.py       # WhoopBriefOutput validation
      test_whoop_context.py      # WhoopDayContext validation
  integration/
    test_whoop_pipeline.py       # Full pipeline — mocked LLM
  e2e/
    test_whoop_e2e.py            # Real LLM — gated behind --run-e2e
  fixtures/
    llm_responses.py             # Add WHOOP_BRIEF_SUCCESS_RESPONSE
                                 #     WHOOP_BRIEF_NO_TARGET_RESPONSE
                                 #     WHOOP_BRIEF_MALFORMED_RESPONSE
```

---

## Test Fixtures Required

### `tests/fixtures/llm_responses.py`

```python
WHOOP_BRIEF_SUCCESS_RESPONSE = '''
{
  "strain_target": 14.2,
  "confidence": 0.96,
  "notes": null
}
'''

WHOOP_BRIEF_NO_TARGET_RESPONSE = '''
{
  "strain_target": null,
  "confidence": 0.0,
  "notes": "No strain target found in input"
}
'''

WHOOP_BRIEF_MALFORMED_RESPONSE = '''
Here is the extracted data: strain target is 14.2
'''
```

---

## Functional Tests

### Scenario 3.1 — WhoopBriefOutput Valid Response Accepted

**Given** valid LLM response data:
```python
{
    "agent_id": "whoop_brief_agent",
    "version": "1.0.0",
    "status": "success",
    "strain_target": 14.2,
    "confidence": 0.96,
    "notes": None,
    "requires_human_review": False
}
```
**When** `WhoopBriefOutput.model_validate(data)` is called
**Then** the model is created without error and all fields are correct

---

### Scenario 3.2 — WhoopBriefOutput Strain Boundary Validation

**Given** a `WhoopBriefOutput` with `strain_target = 21.1`
**When** `WhoopBriefOutput.model_validate(data)` is called
**Then** a `ValidationError` is raised referencing `strain_target`

**Given** a `WhoopBriefOutput` with `strain_target = -0.1`
**When** `WhoopBriefOutput.model_validate(data)` is called
**Then** a `ValidationError` is raised referencing `strain_target`

**Given** a `WhoopBriefOutput` with `strain_target = 0.0`
**When** `WhoopBriefOutput.model_validate(data)` is called
**Then** the model is created without error

**Given** a `WhoopBriefOutput` with `strain_target = 21.0`
**When** `WhoopBriefOutput.model_validate(data)` is called
**Then** the model is created without error

---

### Scenario 3.3 — WhoopDayContext Strain Boundary Validation

**Given** a `WhoopDayContext` with `strain_target = 21.1`
**When** `WhoopDayContext.model_validate(data)` is called
**Then** a `ValidationError` is raised referencing `strain_target`

**Given** a `WhoopDayContext` with `strain_target = 14.2`
**When** `WhoopDayContext.model_validate(data)` is called
**Then** the model is created without error with `strain_accumulated == 0.0`

---

### Scenario 3.4 — DailyEnvelope Accepts WhoopDayContext

**Given** a valid `DailyEnvelope` with `whoop = None`
**When** a `WhoopDayContext` is assigned to `envelope.whoop`
**Then** `envelope.whoop.strain_target` reflects the assigned value

---

### Scenario 3.5 — WhoopBriefAgent Extracts Strain Target

**Given** the LLM returns `WHOOP_BRIEF_SUCCESS_RESPONSE`
**When** `WhoopBriefAgent().run({"raw_text": "Whoop strain target 14.2 today"})` is called
**Then**
- `output.status == "success"`
- `output.strain_target == 14.2`
- `output.confidence >= 0.8`
- `output.requires_human_review == False`

---

### Scenario 3.6 — WhoopBriefAgent Handles Missing Strain Target

**Given** the LLM returns `WHOOP_BRIEF_NO_TARGET_RESPONSE`
**When** `WhoopBriefAgent().run({"raw_text": "Feeling good today"})` is called
**Then**
- `output.status == "unable_to_determine"`
- `output.strain_target is None`
- `output.confidence == 0.0`

---

### Scenario 3.7 — WhoopBriefAgent Handles Malformed LLM Response

**Given** the LLM returns `WHOOP_BRIEF_MALFORMED_RESPONSE` on both
the initial call and the retry
**When** `WhoopBriefAgent().run({"raw_text": "..."})` is called
**Then**
- `output.status == "unable_to_determine"`
- `output.strain_target is None`
- `output.confidence == 0.0`
- No exception is raised — failure is handled gracefully

---

### Scenario 3.8 — Prompt Loads Correctly via importlib.resources

**Given** the package is installed
**When** `WhoopBriefAgent()` is instantiated
**Then**
- `agent.agent_id == "whoop_brief_agent"`
- `agent.version == "1.0.0"`
- `agent.system_prompt` is a non-empty string
- `agent.max_tokens == 256`

---

### Scenario 3.9 — Envelope Saved to Correct Path

**Given** a successful `--whoop` run on date `2026-06-27`
**When** the orchestrator completes
**Then**
- File `data/diary/2026-06-27.json` exists
- File contains valid JSON
- JSON deserialises to a valid `DailyEnvelope`
- `envelope.whoop.strain_target == 14.2`
- `envelope.status == "in_progress"`

---

### Scenario 3.10 — Envelope Loads Existing File if Present

**Given** a `data/diary/2026-06-27.json` file already exists
**When** `--whoop` is run again on the same date
**Then**
- The existing envelope is loaded rather than a new one created
- The `whoop` field is updated with the new strain target
- The `envelope_id` is unchanged from the original

---

### Scenario 3.11 — Missing Objectives Produces Clear Error

**Given** no objectives file exists in `data/objectives/`
**When** `--whoop` is run
**Then**
- The process exits without writing any files
- The terminal displays a message containing "No weekly objectives found"
- The terminal displays instructions to run `--set-objectives` first

---

### Scenario 3.12 — Full Pipeline Integration Test

**Given** weekly objectives exist
**And** the LLM is mocked to return `WHOOP_BRIEF_SUCCESS_RESPONSE`
**When** the orchestrator processes `input_type="whoop_brief"` with
`raw_text="Whoop strain target 14.2 today"`
**Then**
- `WhoopBriefAgent.run()` is called exactly once
- The envelope has `whoop.strain_target == 14.2`
- The envelope is persisted to disk
- The returned summary contains `status == "success"`

---

### Scenario 3.13 — E2E Test with Real LLM (gated)

**Given** a real `ANTHROPIC_API_KEY` in `.env`
**When** `--whoop "Whoop recommends strain target 14.2 today, recovery 73%"`
is run via the CLI
**Then**
- The extracted `strain_target` is approximately 14.2 (within 0.5)
- The envelope is written to disk
- The terminal summary shows the strain target and file path

---

## Slice Completion Checklist

Before marking Slice 3 complete and beginning Slice 4:

- [ ] `uv run pytest tests/unit/ -v` — all tests pass
- [ ] `uv run pytest tests/integration/ -v` — all tests pass
- [ ] `uv run ruff check src/` — exit code 0
- [ ] `ANTHROPIC_API_KEY=test uv run mypy src/` — exit code 0
- [ ] `uv run pre-commit run --all-files` — all hooks pass
- [ ] Scenarios 3.1 through 3.12 have passing tests
- [ ] `uv run python -m wellness_tracker.main --whoop "strain target 14.2"` runs and prints summary
- [ ] `data/diary/YYYY-MM-DD.json` is written and human readable
- [ ] `data/` remains gitignored — no diary files committed
- [ ] `git commit -m "slice 3: whoop daily brief"`
- [ ] `git push`

---

## Notes for Implementation

**importlib.resources usage**
```python
from importlib.resources import files
import yaml

def _load_prompt(self, filename: str) -> dict:
    text = (
        files("wellness_tracker.prompts")
        .joinpath(filename)
        .read_text(encoding="utf-8")
    )
    return yaml.safe_load(text)
```

**Stripping markdown fences from LLM response**
Claude sometimes wraps JSON in ```json ... ``` even when instructed not to.
Strip defensively:
```python
def _parse_json(self, raw: str) -> dict:
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        lines = cleaned.split("\n")
        cleaned = "\n".join(lines[1:-1])
    return json.loads(cleaned)
```

**pyproject.toml package-data**
Ensure this is present so YAML files are included in the installed package:
```toml
[tool.setuptools.package-data]
"wellness_tracker.prompts" = ["*.yaml"]
```

**Retry prompt**
When the first LLM response fails to parse, send a correction message:
```
Your previous response was not valid JSON. 
Please respond with only a JSON object matching the required structure.
No explanation, no markdown, just the JSON.
```

**Envelope date**
Use `datetime.date.today().isoformat()` for the diary filename and
envelope date field. This ensures the file is always named for the
current date regardless of when the process runs.

**save_envelope path**
```python
from wellness_tracker.config import settings

def save_envelope(envelope: DailyEnvelope) -> Path:
    path = settings.diary_dir / f"{envelope.date}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(envelope.model_dump_json(indent=2))
    return path
```
