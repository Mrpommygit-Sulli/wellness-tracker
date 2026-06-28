# 001 — Project Foundations

## Overview

Establishes the complete project skeleton. No agents, no LLM calls, no models,
no business logic. By the end of this slice the project structure exists, all
tooling is configured and passing, and configuration loads correctly from a
`.env` file.

Every subsequent slice builds on this foundation without modifying it.

---

## Objectives

1. Project initialised with UV, Python 3.12, src layout
2. All development tooling configured and passing (Ruff, mypy, pre-commit)
3. Configuration loads from `.env` file
4. Git repository initialised with pre-commit hooks active

---

## What This Slice Does NOT Include

- No Pydantic models
- No agents
- No LLM calls
- No orchestrator
- No guardrails
- No CLI commands beyond confirming config loads
- No file I/O

---

## Deliverables

### Project Initialisation

```
UV project initialised at wellness_tracker/
Python 3.12 specified in pyproject.toml
src layout: src/wellness_tracker/
```

### pyproject.toml

Runtime dependencies:
```
anthropic
pydantic>=2.0
python-dotenv
```

Dev dependencies:
```
pytest
pytest-mock
mypy
ruff
pre-commit
```

### .env.example

```
ANTHROPIC_API_KEY=your_key_here
ANTHROPIC_MODEL=claude-haiku-3-5
LOG_LEVEL=INFO
DATA_DIR=data
```

### .pre-commit-config.yaml

Two hooks:
- Ruff: lint and format check on every commit
- mypy: type check on every commit

### .gitignore

Must exclude:
- `.env`
- `.venv`
- `data/`
- `__pycache__`
- `.mypy_cache`
- `.ruff_cache`
- `*.pyc`
- `.pytest_cache`

---

## Configuration Module

**File:** `src/wellness_tracker/config.py`

Loads `.env` and exposes a `Settings` object used throughout the project.

```
Settings:
    anthropic_api_key: str       # Required — fail fast if missing
    anthropic_model: str         # Default: "claude-haiku-3-5"
    log_level: str               # Default: "INFO"
    data_dir: Path               # Default: Path("data")
    objectives_dir: Path         # Derived: data_dir / "objectives"
    diary_dir: Path              # Derived: data_dir / "diary"
    reports_dir: Path            # Derived: data_dir / "reports"
    audit_dir: Path              # Derived: data_dir / "audit"
```

Fail fast behaviour: if `ANTHROPIC_API_KEY` is not set, raise a clear error
on import — do not allow the application to start without it.

---

## Directory Structure Delivered by This Slice

```
wellness_tracker/
├── CLAUDE.md
├── pyproject.toml
├── .env                               # Gitignored
├── .env.example                       # Committed
├── .pre-commit-config.yaml
├── .gitignore
│
├── docs/
│   └── requirements/
│       └── 001_PROJECT_FOUNDATIONS.md
│
├── src/
│   └── wellness_tracker/
│       ├── __init__.py
│       └── config.py
│
├── tests/
│   ├── conftest.py
│   ├── fixtures/
│   │   └── __init__.py
│   ├── unit/
│   │   └── __init__.py
│   ├── integration/
│   │   └── __init__.py
│   └── e2e/
│       └── __init__.py
│
└── data/                              # Gitignored
    ├── objectives/
    ├── diary/
    ├── reports/
    └── audit/
```

---

## Functional Tests

### Scenario 1.1 — Project Structure Exists

**Given** the project has been initialised with UV
**When** the directory structure is inspected
**Then** the following paths exist:
- `src/wellness_tracker/__init__.py`
- `src/wellness_tracker/config.py`
- `tests/unit/__init__.py`
- `tests/integration/__init__.py`
- `tests/e2e/__init__.py`
- `tests/fixtures/__init__.py`
- `tests/conftest.py`
- `CLAUDE.md`
- `pyproject.toml`
- `.env.example`
- `.pre-commit-config.yaml`
- `.gitignore`

---

### Scenario 1.2 — Configuration Loads from .env

**Given** a `.env` file exists with `ANTHROPIC_API_KEY=test_key_123`
**When** `Settings` is imported from `config.py`
**Then**
- `settings.anthropic_api_key == "test_key_123"`
- `settings.anthropic_model == "claude-haiku-3-5"`
- `settings.data_dir == Path("data")`
- `settings.diary_dir == Path("data/diary")`
- `settings.audit_dir == Path("data/audit")`

---

### Scenario 1.3 — Configuration Fails Fast Without API Key

**Given** no `ANTHROPIC_API_KEY` is set in the environment
**When** `Settings` is imported
**Then** a `ValueError` or `EnvironmentError` is raised with a message
containing "ANTHROPIC_API_KEY"

---

### Scenario 1.4 — Ruff Passes on All Source Files

**Given** the project source files in `src/`
**When** `uv run ruff check src/` is executed
**Then** exit code is 0 with no errors reported

---

### Scenario 1.5 — mypy Passes on All Source Files

**Given** the project source files in `src/`
**When** `uv run mypy src/` is executed
**Then** exit code is 0 with no errors reported

---

### Scenario 1.6 — Pre-commit Hooks Pass on Clean Commit

**Given** pre-commit is installed and hooks are active
**When** a `git commit` is made with clean, correctly typed source files
**Then** both Ruff and mypy hooks pass and the commit succeeds

---

## Test File Locations

```
tests/
  unit/
    test_project_structure.py    # Scenario 1.1
    test_config.py               # Scenarios 1.2, 1.3
```

Scenarios 1.4, 1.5, 1.6 are verified manually during setup and recorded
in the slice completion checklist.

---

## Slice Completion Checklist

Before marking Slice 1 complete and beginning Slice 2:

Verified: 2026-06-28

- [x] `uv sync` completes without error
- [x] `uv run pytest tests/unit` — all tests pass (3 passed)
- [x] `uv run ruff check src/` — exit code 0
- [x] `uv run mypy src/` — exit code 0
- [x] `git commit` triggers pre-commit hooks and they pass
- [x] `.env` is not committed to git
- [x] `data/` directory is not committed to git
- [x] Scenarios 1.1 through 1.3 have passing unit tests
- [x] CLAUDE.md is committed to the repository
