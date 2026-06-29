# Wellness Tracker

A personal wellness tracking system that processes plain text inputs 
— training sessions, meals, and Whoop data — through a multi-agent 
AI pipeline to build a structured daily diary and weekly progress report.

## Purpose

This project serves two purposes:
- A practical personal tool for tracking training and nutrition
- A learning vehicle for agentic AI patterns in Python

## Tech Stack

- Python 3.12
- Anthropic Claude API
- Pydantic v2
- UV package manager

## Setup

```bash
uv sync
cp .env.example .env
# Add your ANTHROPIC_API_KEY to .env
uv run pre-commit install
```

## Usage

```bash
uv run python -m wellness_tracker.main --set-objectives
uv run python -m wellness_tracker.main --whoop "<text>"
uv run python -m wellness_tracker.main --log "<text>"
uv run python -m wellness_tracker.main --close "<text>"
uv run python -m wellness_tracker.main --report
```

## Project Status

In development — building slice by slice.
