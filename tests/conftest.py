import os

# Ensure config.py can be imported in unit/integration tests without a real .env file.
# E2E tests that need a real API key are gated behind @pytest.mark.e2e.
os.environ.setdefault("ANTHROPIC_API_KEY", "test-key-for-unit-tests")
