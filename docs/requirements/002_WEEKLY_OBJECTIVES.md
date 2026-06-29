# 002 — Weekly Objectives

## Overview

Delivers the ability to set and persist weekly objectives via `--set-objectives`.
Introduces the first Pydantic models — only those needed to represent and
validate weekly objectives. Introduces the minimal DailyEnvelope stub with only
the fields this slice requires. Subsequent slices extend both as needed.

By the end of this slice, a user can set their weekly goals and have them
persisted to disk and loaded back correctly.

---

## Objectives

1. `WeeklyObjectives` and its sub-models defined and validated
2. Minimal `DailyEnvelope` stub defined with only fields this slice needs
3. `--set-objectives` CLI command prompts for and persists weekly objectives
4. Weekly objectives can be loaded back from disk correctly
5. Unit tests cover all model validation rules
6. Unit tests cover persistence and loading

---

## What This Slice Does NOT Include

- No agents or LLM calls
- No orchestrator
- No guardrails
- No other models beyond those listed below
- No diary entry creation
- No audit trail

---

## New Models Introduced

### File: `src/wellness_tracker/models/objectives.py`

#### WeightGoal

| Field | Type | Validation |
|-------|------|------------|
| direction | Literal["lose", "maintain", "gain"] | Required |
| target_weekly_deficit_kcal | int | Required if direction is "lose"; must be > 0 |
| current_weight_kg | float | Must be > 0 and < 300 |

#### NutritionTargets

| Field | Type | Validation |
|-------|------|------------|
| daily_calorie_target | int | Must be >= 1000 and <= 5000 |
| daily_protein_target_g | int | Must be >= 0 and <= 500 |

#### TrainingTarget

| Field | Type | Validation |
|-------|------|------------|
| sessions | int | Must be >= 1 and <= 14 |
| min_duration_minutes | int | Must be >= 10 and <= 300 |

#### WeeklyObjectives

| Field | Type | Validation |
|-------|------|------------|
| week_starting | str | ISO date format YYYY-MM-DD |
| weight_goal | WeightGoal | Required |
| training_targets | dict[str, TrainingTarget] | At least one activity required |
| nutrition_targets | NutritionTargets | Required |
| constraints | list[str] | Optional, default empty list |

---

### File: `src/wellness_tracker/models/envelope.py`

Minimal stub — only fields needed by this slice. Extended in subsequent slices.

#### DailyEnvelope (stub)

| Field | Type | Default |
|-------|------|---------|
| envelope_id | str | Generated: `env_{date}_{uuid4_short}` |
| date | str | ISO date YYYY-MM-DD |
| status | Literal["in_progress", "finalised"] | "in_progress" |
| week_starting | str | Required |
| objectives_version | str | Required |

The envelope references the weekly objectives by `week_starting` and
`objectives_version` rather than embedding the full `WeeklyObjectives`
object. This keeps the envelope decoupled from the specific objectives
revision in force when the day started, even if objectives are later
revised mid-week.

---

## Persistence

### File: `src/wellness_tracker/storage/objectives.py`

Objectives are stored as versioned files, one per revision, so that any
`DailyEnvelope` created mid-week can keep referencing the exact objectives
revision that was in force when its day started — even if objectives are
later revised. Filenames follow `week_{week_starting}_v{n}.json`, with `n`
starting at 1 and incrementing by 1 each time objectives are saved for that
week.

Four functions:

```
get_current_version(week_starting: str) -> str
    Scans data/objectives/ for files matching week_{week_starting}_v*.json
    Returns the highest version found, formatted as "v{n}"
    Raises FileNotFoundError if no versions exist for that week

save_objectives(objectives: WeeklyObjectives) -> tuple[Path, str]
    Determines the next version for objectives.week_starting
    (1 if none exist yet, otherwise current version + 1)
    Writes to data/objectives/week_{week_starting}_v{n}.json
    Returns (path written to, version string e.g. "v1")
    Creates the directory if it does not exist

load_objectives(week_starting: str, version: str | None = None) -> WeeklyObjectives
    Reads from data/objectives/week_{week_starting}_{version}.json
    If version is None, uses get_current_version(week_starting)
    Raises FileNotFoundError if file does not exist
    Raises ValidationError if file content is invalid

load_current_objectives() -> tuple[WeeklyObjectives, str]
    Finds the most recent week_starting across all saved objectives
    Resolves its current version via get_current_version
    Returns (objectives, version string)
    Raises FileNotFoundError if no objectives have been set
```

---

## CLI Command

**File:** `src/wellness_tracker/main.py`

`--set-objectives` prompts the user interactively for:

```
Week starting (YYYY-MM-DD): 2026-06-23
Current weight (kg): 82.0
Weight goal (lose/maintain/gain): lose
Weekly calorie deficit target (kcal): 2800
Daily calorie target: 1900
Daily protein target (g): 140

Training targets (enter blank activity name to finish):
  Activity name: running
  Sessions per week: 3
  Min duration (minutes): 40
  Activity name: swimming
  Sessions per week: 2
  Min duration (minutes): 45
  Activity name:

Constraints (enter blank to finish):
  Constraint: left knee — avoid high impact if pain above 3/10
  Constraint:

Objectives saved to data/objectives/week_2026-06-23_v1.json (v1)
```

On completion, prints confirmation with the path written to and the version.

---

## Directory Additions This Slice

```
src/
  wellness_tracker/
    models/
      __init__.py
      objectives.py          # WeeklyObjectives and sub-models
      envelope.py            # DailyEnvelope stub
    storage/
      __init__.py
      objectives.py          # save_objectives, load_objectives

tests/
  unit/
    models/
      __init__.py
      test_objectives.py     # All model validation scenarios
      test_envelope.py       # DailyEnvelope stub scenarios
    storage/
      __init__.py
      test_objectives.py     # Persistence scenarios
```

---

## Functional Tests

### Scenario 2.1 — Valid WeeklyObjectives Accepted

**Given** valid weekly objectives data:
```python
{
    "week_starting": "2026-06-23",
    "weight_goal": {
        "direction": "lose",
        "target_weekly_deficit_kcal": 2800,
        "current_weight_kg": 82.0
    },
    "training_targets": {
        "running": {"sessions": 3, "min_duration_minutes": 40}
    },
    "nutrition_targets": {
        "daily_calorie_target": 1900,
        "daily_protein_target_g": 140
    },
    "constraints": ["left knee — avoid high impact if pain above 3/10"]
}
```
**When** `WeeklyObjectives.model_validate(data)` is called
**Then** the model is created without error and all fields are correct

---

### Scenario 2.2 — Invalid Calorie Target Rejected

**Given** `NutritionTargets` with `daily_calorie_target = 500`
**When** `NutritionTargets.model_validate(data)` is called
**Then** a `ValidationError` is raised referencing `daily_calorie_target`

**Given** `NutritionTargets` with `daily_calorie_target = 5001`
**When** `NutritionTargets.model_validate(data)` is called
**Then** a `ValidationError` is raised referencing `daily_calorie_target`

---

### Scenario 2.3 — TrainingTarget Session Boundary Validation

**Given** a `TrainingTarget` with `sessions = 0`
**When** `TrainingTarget.model_validate(data)` is called
**Then** a `ValidationError` is raised referencing `sessions`

**Given** a `TrainingTarget` with `sessions = 15`
**When** `TrainingTarget.model_validate(data)` is called
**Then** a `ValidationError` is raised referencing `sessions`

**Given** a `TrainingTarget` with `sessions = 1`
**When** `TrainingTarget.model_validate(data)` is called
**Then** the model is created without error

**Given** a `TrainingTarget` with `sessions = 14`
**When** `TrainingTarget.model_validate(data)` is called
**Then** the model is created without error

---

### Scenario 2.4 — WeeklyObjectives Requires At Least One Training Target

**Given** `WeeklyObjectives` with `training_targets = {}`
**When** `WeeklyObjectives.model_validate(data)` is called
**Then** a `ValidationError` is raised referencing `training_targets`

---

### Scenario 2.5 — WeightGoal Deficit Required When Losing

**Given** a `WeightGoal` with `direction = "lose"` and no
`target_weekly_deficit_kcal`
**When** `WeightGoal.model_validate(data)` is called
**Then** a `ValidationError` is raised referencing `target_weekly_deficit_kcal`

---

### Scenario 2.6 — WeightGoal Current Weight Boundary Validation

**Given** a `WeightGoal` with `current_weight_kg = 0`
**When** `WeightGoal.model_validate(data)` is called
**Then** a `ValidationError` is raised referencing `current_weight_kg`

**Given** a `WeightGoal` with `current_weight_kg = 300`
**When** `WeightGoal.model_validate(data)` is called
**Then** a `ValidationError` is raised referencing `current_weight_kg`

---

### Scenario 2.7 — DailyEnvelope Stub Created with Defaults

**Given** a `week_starting` and `objectives_version` and today's date
**When** a `DailyEnvelope` is created
**Then**
- `envelope.status == "in_progress"`
- `envelope.week_starting` matches the value passed in
- `envelope.objectives_version` matches the value passed in
- `envelope.envelope_id` starts with `"env_"`
- `envelope.date` matches today's date

---

### Scenario 2.8 — Objectives Saved to Correct Versioned Path

**Given** a valid `WeeklyObjectives` with `week_starting = "2026-06-23"`
**When** `save_objectives(objectives)` is called for the first time that week
**Then**
- The returned tuple is `(path, "v1")`
- The file `data/objectives/week_2026-06-23_v1.json` exists
- The file contains valid JSON
- The JSON round-trips back to an identical `WeeklyObjectives` instance

**Given** objectives have already been saved once for `"2026-06-23"`
**When** `save_objectives(objectives)` is called again
**Then**
- The returned version is `"v2"`
- The file `data/objectives/week_2026-06-23_v2.json` exists
- The original `week_2026-06-23_v1.json` is left untouched

---

### Scenario 2.9 — Objectives Loaded Back Correctly

**Given** a `WeeklyObjectives` instance that has been saved to disk
**When** `load_objectives("2026-06-23")` is called with no version
**Then**
- The returned `WeeklyObjectives` instance matches the most recently saved
  version
- All nested models are correctly deserialised
- All field values are identical to what was saved

**Given** multiple versions exist for `"2026-06-23"`
**When** `load_objectives("2026-06-23", version="v1")` is called
**Then** the first saved revision is returned, not the latest

---

### Scenario 2.10 — Load Raises Error When File Not Found

**Given** no objectives file exists for `"2026-01-01"`
**When** `load_objectives("2026-01-01")` is called
**Then** a `FileNotFoundError` is raised

---

### Scenario 2.11 — Load Current Objectives Returns Most Recent Week and Version

**Given** objectives files exist for `"2026-06-16"` and `"2026-06-23"`
**When** `load_current_objectives()` is called
**Then** the objectives for `"2026-06-23"` are returned, paired with its
current version string

**Given** `"2026-06-23"` has two saved versions, `v1` and `v2`
**When** `load_current_objectives()` is called
**Then** the returned version is `"v2"` and the objectives reflect that
revision

---

### Scenario 2.12 — Load Current Raises Error When No Objectives Set

**Given** no objectives files exist in `data/objectives/`
**When** `load_current_objectives()` is called
**Then** a `FileNotFoundError` is raised with a message indicating no
objectives have been set

---

### Scenario 2.13 — Constraints Default to Empty List

**Given** `WeeklyObjectives` data with no `constraints` field
**When** `WeeklyObjectives.model_validate(data)` is called
**Then** `objectives.constraints == []`

---

### Scenario 2.14 — get_current_version Resolves Latest Revision

**Given** objectives have been saved twice for `"2026-06-23"`
**When** `get_current_version("2026-06-23")` is called
**Then** `"v2"` is returned

**Given** no objectives exist for `"2026-01-01"`
**When** `get_current_version("2026-01-01")` is called
**Then** a `FileNotFoundError` is raised

---

## Slice Completion Checklist

Before marking Slice 2 complete and beginning Slice 3:

Verified: 2026-06-28

- [x] `uv run pytest tests/unit` — all tests pass (27 passed)
- [x] `uv run ruff check src/` — exit code 0
- [x] `uv run mypy src/` — exit code 0
- [ ] `git commit` triggers pre-commit hooks and they pass
- [x] Scenarios 2.1 through 2.14 have passing unit tests
- [ ] `python main.py --set-objectives` runs interactively and saves correctly
- [ ] Saved objectives file is valid JSON and human readable
- [x] `data/` remains gitignored — no objectives files committed

---

## Notes for Implementation

**week_starting format**
Store as an ISO date string `YYYY-MM-DD`. Use `datetime.date.fromisoformat()`
for validation in a `field_validator`. Do not use a `date` type directly —
JSON serialisation of `date` requires extra configuration in Pydantic v2.

**envelope_id generation**
Use `uuid.uuid4().hex[:8]` for the short suffix.
Format: `env_{date}_{suffix}` e.g. `env_2026-06-27_a3f8c291`
Generate in a `model_post_init` or via `default_factory`.

**save_objectives**
Use `model.model_dump_json(indent=2)` for human-readable output.
Create parent directories with `Path.mkdir(parents=True, exist_ok=True)`.
Determine the next version by calling `get_current_version` and incrementing,
falling back to `"v1"` if no version exists yet (i.e. `get_current_version`
raises `FileNotFoundError`).

**get_current_version**
Filenames follow `week_{week_starting}_v{n}.json`. Glob for
`week_{week_starting}_v*.json`, parse the integer after `v`, and return the
max formatted as `"v{n}"`.

**load_current_objectives**
Filenames sort lexicographically by `week_starting` since ISO date format
sorts correctly as a string. Determine the most recent `week_starting` across
all saved files, then resolve its current version via `get_current_version`
before loading.
