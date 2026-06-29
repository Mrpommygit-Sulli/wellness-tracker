import os

import pytest

# Ensure config.py can be imported in unit/integration tests without a real .env file.
# E2E tests that need a real API key are gated behind @pytest.mark.e2e.
os.environ.setdefault("ANTHROPIC_API_KEY", "test-key-for-unit-tests")


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--run-e2e",
        action="store_true",
        default=False,
        help="Run tests marked e2e (requires a real ANTHROPIC_API_KEY)",
    )


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line("markers", "e2e: real-LLM end-to-end test")


def pytest_collection_modifyitems(
    config: pytest.Config, items: list[pytest.Item]
) -> None:
    if config.getoption("--run-e2e"):
        return
    skip_e2e = pytest.mark.skip(reason="need --run-e2e option to run")
    for item in items:
        if "e2e" in item.keywords:
            item.add_marker(skip_e2e)
