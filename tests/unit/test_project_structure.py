from pathlib import Path

ROOT = Path(__file__).parent.parent.parent


def test_required_paths_exist() -> None:
    required = [
        "src/wellness_tracker/__init__.py",
        "src/wellness_tracker/config.py",
        "tests/unit/__init__.py",
        "tests/integration/__init__.py",
        "tests/e2e/__init__.py",
        "tests/fixtures/__init__.py",
        "tests/conftest.py",
        "CLAUDE.md",
        "pyproject.toml",
        ".env.example",
        ".pre-commit-config.yaml",
        ".gitignore",
    ]
    for path in required:
        assert (ROOT / path).exists(), f"Missing required path: {path}"
