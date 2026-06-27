import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

_api_key_raw = os.getenv("ANTHROPIC_API_KEY")
if not _api_key_raw:
    raise ValueError(
        "ANTHROPIC_API_KEY is not set. "
        "Add it to your .env file before starting the application."
    )
_api_key: str = _api_key_raw

_data_dir = Path(os.getenv("DATA_DIR", "data"))


class Settings:
    anthropic_api_key: str = _api_key
    anthropic_model: str = os.environ.get("ANTHROPIC_MODEL", "claude-haiku-3-5")
    log_level: str = os.environ.get("LOG_LEVEL", "INFO")
    data_dir: Path = _data_dir
    objectives_dir: Path = _data_dir / "objectives"
    diary_dir: Path = _data_dir / "diary"
    reports_dir: Path = _data_dir / "reports"
    audit_dir: Path = _data_dir / "audit"


settings = Settings()
