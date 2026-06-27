import importlib
import sys
from pathlib import Path
from unittest.mock import patch


def _reload_config(env: dict[str, str]):
    """Reload config module with a controlled environment."""
    for mod in list(sys.modules):
        if "wellness_tracker.config" in mod or mod == "wellness_tracker.config":
            del sys.modules[mod]
    with patch.dict("os.environ", env, clear=True):
        import wellness_tracker.config as cfg

        importlib.reload(cfg)
        return cfg


def test_settings_loads_from_env(tmp_path: Path, monkeypatch: object) -> None:
    env = {
        "ANTHROPIC_API_KEY": "test_key_123",
        "ANTHROPIC_MODEL": "claude-haiku-3-5",
        "LOG_LEVEL": "INFO",
        "DATA_DIR": "data",
    }
    cfg = _reload_config(env)
    assert cfg.settings.anthropic_api_key == "test_key_123"
    assert cfg.settings.anthropic_model == "claude-haiku-3-5"
    assert cfg.settings.data_dir == Path("data")
    assert cfg.settings.diary_dir == Path("data/diary")
    assert cfg.settings.audit_dir == Path("data/audit")


def test_settings_fails_without_api_key() -> None:
    import pytest

    for mod in list(sys.modules):
        if "wellness_tracker.config" in mod or mod == "wellness_tracker.config":
            del sys.modules[mod]

    with patch.dict("os.environ", {}, clear=True):
        with pytest.raises((ValueError, EnvironmentError), match="ANTHROPIC_API_KEY"):
            import wellness_tracker.config  # noqa: F401
