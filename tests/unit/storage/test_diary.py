import json
from pathlib import Path

import pytest

from wellness_tracker.models.envelope import DailyEnvelope, WhoopDayContext
from wellness_tracker.storage import diary as diary_storage


@pytest.fixture(autouse=True)
def patch_diary_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(diary_storage.settings, "diary_dir", tmp_path)


class TestSaveEnvelope:
    def test_saves_to_correct_path(self) -> None:
        envelope = DailyEnvelope(
            date="2026-06-27",
            week_starting="2026-06-23",
            objectives_version="v1",
            whoop=WhoopDayContext(strain_target=14.2),
        )
        path = diary_storage.save_envelope(envelope)
        assert path == diary_storage.settings.diary_dir / "2026-06-27.json"
        assert path.exists()

    def test_saved_file_is_valid_json(self) -> None:
        envelope = DailyEnvelope(
            date="2026-06-27", week_starting="2026-06-23", objectives_version="v1"
        )
        path = diary_storage.save_envelope(envelope)
        data = json.loads(path.read_text())
        assert data["date"] == "2026-06-27"
        assert data["status"] == "in_progress"
        assert data["week_starting"] == "2026-06-23"
        assert data["objectives_version"] == "v1"


class TestLoadEnvelope:
    def test_loads_existing_envelope(self) -> None:
        envelope = DailyEnvelope(
            date="2026-06-27",
            week_starting="2026-06-23",
            objectives_version="v1",
            whoop=WhoopDayContext(strain_target=14.2),
        )
        diary_storage.save_envelope(envelope)
        loaded = diary_storage.load_envelope("2026-06-27")
        assert loaded.envelope_id == envelope.envelope_id
        assert loaded.whoop is not None
        assert loaded.whoop.strain_target == 14.2

    def test_raises_when_file_not_found(self) -> None:
        with pytest.raises(FileNotFoundError):
            diary_storage.load_envelope("2026-01-01")
