# CLAUDE.md — Wellness Tracker

## Project Purpose

A personal wellness tracking system that accepts plain text inputs throughout
the day — training sessions, meals, Whoop data — and processes them through a
multi-agent pipeline to build a structured daily diary entry. At the end of the
week, daily entries are synthesised into a weekly progress report tracking
training objectives and calorie deficit against targets.

This project is also a learning vehicle for agentic AI patterns implemented in
Python. Every architectural decision reflects a deliberate pattern choice, not
just the simplest path to working code.

---

## Architecture Overview

### Entry Points

Five CLI commands via `main.py`:

```
python main.py --set-objectives     # Set weekly goals (run once Monday)
python main.py --whoop "<text>"     # Log morning Whoop strain target
python main.py --log "<text>"       # Log a training session or meal
python main.py --close "<text>"     # End of day close with confirmed totals
python main.py --report             # Generate weekly progress report
```

### Request Flow

```
CLI (main.py)
    │
    ▼
Orchestrator (orchestrator.py)
    │   Loads weekly objectives
    │   Loads or creates today's envelope
    │   Runs input guardrails
    │   Routes to agent sequence
    │   Runs output + policy guardrails after each agent
    │   Writes audit records
    │   Triggers HITL when required
    │   Persists envelope to disk
    │
    ├── Agent Layer (src/wellness_tracker/agents/)
    │   Eight specialised agents, each with one responsibility
    │   All extend BaseAgent
    │   All called via agent.run(payload) → AgentOutput
    │
    ├── Guardrail Layer (src/wellness_tracker/guardrails/)
    │   Standalone deterministic functions
    │   Run by orchestrator before and after each agent
    │   Never contain LLM calls
    │
    ├── HITL Layer (src/wellness_tracker/hitl.py)
    │   Terminal-based escalation and decision capture
    │   Builds handoff package from guardrail results
    │   Records decision and context in audit trail
    │
    └── Storage Layer (data/)
        JSON files — one per day for diary entries
        JSONL files — one per day for audit trail (append-only, hash-chained)
```

---

## Agentic Patterns

This project implements six agentic patterns. Every implementation decision
should preserve these patterns — do not shortcut them.

**Specialised Agents**
Each agent has one responsibility, one input contract, one output contract.
Agents do not call other agents. Agents do not fetch their own data.

**Federated Agents**
Agents share a context envelope (DailyEnvelope). Each agent receives a scoped
payload extracted from the envelope by the orchestrator. Each agent appends its
output to the envelope. The envelope is the single source of truth.

**Least-Privilege**
No agent receives the full envelope. The orchestrator extracts only the fields
each agent needs. Agents have no file system or API access beyond the LLM call.

**Deterministic Guardrails**
All safety and business rules are Python functions, not prompt instructions.
Four types: input, output, policy, dependency. All return a GuardrailResult
with rule name, version, result, reason, and action. All results are recorded
in the audit trail.

**Human-in-the-Loop**
Escalations surface in the terminal as structured handoff packages. The user
selects from bounded decision options. The decision and the full context the
user saw are recorded in the audit trail before the workflow resumes.

**Audit-Grade Accountability**
Every significant event writes one record to a JSONL audit file. Records are
hash-chained — each record contains the hash of the previous record. Chain
integrity can be verified via `python main.py --verify-audit <date>`.

---

## Agent Inventory

| # | Agent | Input | Output |
|---|-------|-------|--------|
| 1 | ClassificationAgent | Raw text | Input type + segments |
| 2 | WhoopBriefAgent | Whoop text | Strain target |
| 3 | TrainingExtractionAgent | Training text segment | Structured session |
| 4 | NutritionExtractionAgent | Nutrition text segment | Meals + calories |
| 5 | DailyAccumulatorAgent | Envelope + new output | Updated daily totals |
| 6 | EndOfDayReconciliationAgent | Close text + envelope | Confirmed totals + narrative |
| 7 | ValidationAgent | Complete day envelope | Flags + validation status |
| 8 | WeeklyReportAgent | All daily entries | Weekly report |

---

## Orchestrator Routing

```python
ROUTING_MAP = {
    "whoop_brief":      [WhoopBriefAgent, DailyAccumulatorAgent],
    "training_session": [ClassificationAgent, TrainingExtractionAgent,
                         DailyAccumulatorAgent, ValidationAgent],
    "meal":             [ClassificationAgent, NutritionExtractionAgent,
                         DailyAccumulatorAgent],
    "mixed":            [ClassificationAgent, TrainingExtractionAgent,
                         NutritionExtractionAgent, DailyAccumulatorAgent,
                         ValidationAgent],
    "end_of_day_close": [ClassificationAgent, EndOfDayReconciliationAgent,
                         ValidationAgent, DailyAccumulatorAgent],
    "weekly_report":    [WeeklyReportAgent],
}
```

---

## Data Model Summary

### DailyEnvelope
The shared context object. One per day. Persisted to `data/diary/YYYY-MM-DD.json`
after every agent run.

Key sections:
- `envelope_id`, `date`, `status` (in_progress | finalised)
- `weekly_objectives` — loaded at start of day, referenced throughout
- `whoop` — strain target and actuals
- `training_sessions` — list, grows during day
- `meals` — list, grows during day
- `daily_totals` — recalculated after every accumulator run
- `agent_outputs` — append-only record of every agent invocation
- `flags` — raised by validation and guardrails
- `escalations` — HITL events and decisions
- `audit_trail` — append-only, hash-chained

### WeeklyObjectives
Set once on Monday. Loaded by orchestrator for every subsequent input that week.
Stored in `data/objectives/week_YYYY-MM-DD.json`.

Key sections:
- `weight_goal` — direction, target weekly deficit kcal, current weight
- `training_targets` — per activity: sessions, min duration
- `nutrition_targets` — daily calorie target, daily protein target
- `constraints` — free text list (injury notes, travel days)

---

## Technical Stack

| Concern | Decision |
|---------|----------|
| Language | Python 3.12 |
| Package manager | UV |
| Package layout | src layout — `src/wellness_tracker/` |
| LLM SDK | anthropic (official Python SDK) |
| LLM Model | claude-haiku-3-5 (configurable via .env) |
| Data validation | Pydantic v2 |
| Configuration | python-dotenv, .env file |
| Storage | JSON files (diary), JSONL files (audit) |
| Testing | pytest |
| Linting | Ruff |
| Type checking | mypy (pragmatic — typed where it matters) |
| Version control | Git |
| Pre-commit hooks | pre-commit (Ruff + mypy) |
| IDE | PyCharm |

---

## Project Structure

```
wellness_tracker/
├── CLAUDE.md                          # This file
├── pyproject.toml                     # UV project config, dependencies
├── .env                               # API keys — gitignored
├── .env.example                       # Template — committed to git
├── .pre-commit-config.yaml            # Ruff + mypy hooks
├── .gitignore
│
├── docs/
│   └── requirements/                  # One file per slice, named by outcome
│       ├── 001_PROJECT_FOUNDATIONS.md
│       ├── 002_WEEKLY_OBJECTIVES.md
│       ├── 003_WHOOP_DAILY_BRIEF.md
│       ├── 004_TRAINING_SESSION_LOGGING.md
│       ├── 005_MEAL_LOGGING.md
│       ├── 006_MIXED_INPUT_HANDLING.md
│       ├── 007_GUARDRAILS_LAYER.md
│       ├── 008_END_OF_DAY_CLOSE.md
│       ├── 009_VALIDATION_AGENT.md
│       ├── 010_HITL_ESCALATION.md
│       ├── 011_AUDIT_TRAIL.md
│       └── 012_WEEKLY_REPORT.md
│
├── src/
│   └── wellness_tracker/
│       ├── __init__.py
│       ├── main.py                    # CLI entry point
│       ├── config.py                  # Loads .env, exposes settings
│       ├── orchestrator.py            # Routing, sequencing, envelope mgmt
│       ├── hitl.py                    # Escalation and decision capture
│       ├── audit.py                   # Append-only JSONL audit writer
│       │
│       ├── models/
│       │   ├── __init__.py
│       │   ├── envelope.py            # DailyEnvelope and sub-models
│       │   ├── objectives.py          # WeeklyObjectives model
│       │   ├── audit.py               # AuditRecord model
│       │   └── outputs.py             # All agent output contracts
│       │
│       ├── agents/
│       │   ├── __init__.py
│       │   ├── base.py                # BaseAgent — all agents extend this
│       │   ├── classification.py
│       │   ├── whoop_brief.py
│       │   ├── training_extraction.py
│       │   ├── nutrition_extraction.py
│       │   ├── accumulator.py
│       │   ├── end_of_day.py
│       │   ├── validation.py
│       │   └── weekly_report.py
│       │
│       └── guardrails/
│           ├── __init__.py
│           ├── input.py
│           ├── output.py
│           ├── policy.py
│           ├── dependency.py
│           └── runner.py              # Runs guardrails, returns results
│
├── tests/
│   ├── conftest.py                    # Shared pytest config and fixtures
│   ├── fixtures/
│   │   ├── __init__.py
│   │   ├── objectives.py              # Sample WeeklyObjectives builders
│   │   ├── envelopes.py               # Sample DailyEnvelope builders
│   │   └── llm_responses.py           # Canned LLM response strings
│   ├── unit/
│   │   ├── models/
│   │   └── guardrails/
│   ├── integration/
│   └── e2e/
│
└── data/                              # Gitignored — runtime data
    ├── objectives/                    # week_YYYY-MM-DD.json
    ├── diary/                         # YYYY-MM-DD.json
    ├── reports/                       # week_YYYY-MM-DD_report.json
    └── audit/                         # YYYY-MM-DD_audit.jsonl
```

---

## Key Conventions

**Agent output contracts**
Every agent returns a typed Pydantic model. Raw LLM output is always parsed
and validated before being written to the envelope. If parsing fails, the
guardrail layer rejects the output — the envelope is never updated with
unvalidated data.

**Guardrail results**
Every guardrail function returns a `GuardrailResult` with:
- `passed: bool`
- `rule_name: str`
- `rule_version: str`
- `reason: str | None`
- `action: Literal["proceed", "note", "escalate", "reject"]`

**Audit records**
Every audit record contains:
- `sequence_number`, `timestamp`, `event_type`
- `actor` (agent ID + version, or "human" + reviewer ID)
- `payload` (what was recorded)
- `previous_hash`, `record_hash`

**Envelope persistence**
The envelope is written to disk after every agent run — not just at end of day.
If the process is interrupted, the envelope reflects the last completed agent.

**Testing LLM calls**
Unit and integration tests never call the real LLM. All LLM calls are mocked
via `unittest.mock.patch`. Canned responses live in `tests/fixtures/llm_responses.py`.
E2E tests call the real API and are gated behind `@pytest.mark.e2e`.

**mypy pragmatic mode**
All models, guardrail functions, and orchestrator logic are fully typed.
Agent output parsing may use `Any` where Pydantic handles runtime validation.
`# type: ignore` comments must include a reason.

---

## Build Slice Plan

| Slice | Description | Requirements File |
|-------|-------------|-------------------|
| 1 | Project Foundation | 001_PROJECT_FOUNDATIONS.md |
| 2 | Weekly Objectives | 002_WEEKLY_OBJECTIVES.md |
| 3 | Whoop Daily Brief | 003_WHOOP_DAILY_BRIEF.md |
| 4 | Training Session Logging | 004_TRAINING_SESSION_LOGGING.md |
| 5 | Meal Logging | 005_MEAL_LOGGING.md |
| 6 | Mixed Input Handling | 006_MIXED_INPUT_HANDLING.md |
| 7 | Guardrails Layer | 007_GUARDRAILS_LAYER.md |
| 8 | End of Day Close | 008_END_OF_DAY_CLOSE.md |
| 9 | Validation Agent | 009_VALIDATION_AGENT.md |
| 10 | HITL Escalation | 010_HITL_ESCALATION.md |
| 11 | Audit Trail | 011_AUDIT_TRAIL.md |
| 12 | Weekly Report | 012_WEEKLY_REPORT.md |

Slice requirement documents live in `docs/requirements/`.
Each document is named after the outcome it delivers.

---

## Running the Project

```bash
# Initialise with UV
uv sync

# Set up pre-commit hooks
uv run pre-commit install

# Run all unit and integration tests
uv run pytest tests/unit tests/integration

# Run E2E tests (requires ANTHROPIC_API_KEY in .env)
uv run pytest tests/e2e --run-e2e

# Verify audit trail integrity for a specific date
uv run python -m wellness_tracker.main --verify-audit 2026-06-27
```
